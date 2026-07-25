#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crawler_h1 v0.13.1 integrated sprocket reinforcement."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence
import argparse
import hashlib
import json
import math
import shutil

try:
    import cadquery as cq
    from cadquery import exporters
except Exception:
    cq = None
    exporters = None

VERSION = "crawler-h1-v0.13.1-integrated-sprocket"
STATUS = "FIRST_ARTICLE_REQUIRED"


@dataclass(frozen=True)
class Spec:
    tooth_count: int = 12
    width_mm: float = 44.0
    phase_deg: float = 15.0

    tip_radius_mm: float = 33.07
    root_radius_mm: float = 29.47
    tip_width_mm: float = 7.50
    root_width_mm: float = 9.50

    embed_depth_mm: float = 4.00
    embed_width_mm: float = 13.00

    ring_inner_radius_mm: float = 20.00
    hub_radius_mm: float = 18.00
    spoke_count: int = 6
    spoke_width_mm: float = 12.00
    spoke_inner_radius_mm: float = 15.00
    spoke_outer_radius_mm: float = 22.50

    drive_bore_mm: float = 10.30
    bolt_count: int = 4
    bolt_pcd_mm: float = 24.00
    bolt_hole_mm: float = 4.40
    bolt_phase_deg: float = 45.00

    bearing_seat_mm: float = 26.20
    bearing_depth_mm: float = 8.20
    center_relief_mm: float = 12.00

    minimum_intersection_mm3: float = 100.0

    @property
    def embed_radius_mm(self):
        return self.root_radius_mm - self.embed_depth_mm

    @property
    def ring_thickness_mm(self):
        return self.root_radius_mm - self.ring_inner_radius_mm


S = Spec()


def require_cadquery():
    if cq is None or exporters is None:
        raise RuntimeError(
            "CadQuery unavailable; use --metadata-only."
        )


def cylinder(radius, height):
    require_cadquery()
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(height / 2.0, both=True)
    )


def solid_count(shape):
    try:
        return len(shape.solids().vals())
    except Exception:
        return None


def volume_of(shape):
    obj = shape.val() if hasattr(shape, "val") else shape
    try:
        return float(obj.Volume())
    except Exception:
        return None


def build_ring_hub_spokes():
    require_cadquery()

    ring = cylinder(
        S.root_radius_mm,
        S.width_mm,
    ).cut(
        cylinder(
            S.ring_inner_radius_mm,
            S.width_mm + 0.4,
        )
    )

    body = ring.union(
        cylinder(S.hub_radius_mm, S.width_mm)
    )

    spoke_length = (
        S.spoke_outer_radius_mm
        - S.spoke_inner_radius_mm
    )
    spoke_center = (
        S.spoke_outer_radius_mm
        + S.spoke_inner_radius_mm
    ) / 2.0

    for index in range(S.spoke_count):
        spoke = (
            cq.Workplane("XY")
            .box(
                spoke_length,
                S.spoke_width_mm,
                S.width_mm,
                centered=(True, True, True),
            )
            .translate((spoke_center, 0.0, 0.0))
            .rotate(
                (0, 0, 0),
                (0, 0, 1),
                index * 360.0 / S.spoke_count,
            )
        )
        body = body.union(spoke)

    return body.clean()


def build_embedded_tooth():
    require_cadquery()

    polygon = [
        (S.embed_radius_mm, -S.embed_width_mm / 2.0),
        (S.root_radius_mm, -S.root_width_mm / 2.0),
        (S.tip_radius_mm, -S.tip_width_mm / 2.0),
        (S.tip_radius_mm, S.tip_width_mm / 2.0),
        (S.root_radius_mm, S.root_width_mm / 2.0),
        (S.embed_radius_mm, S.embed_width_mm / 2.0),
    ]

    # Intentionally no pre-union fillet.
    return (
        cq.Workplane("XY")
        .polyline(polygon)
        .close()
        .extrude(S.width_mm / 2.0, both=True)
    )


def build_blank():
    require_cadquery()

    body = build_ring_hub_spokes()
    tooth = build_embedded_tooth()

    for index in range(S.tooth_count):
        body = body.union(
            tooth.rotate(
                (0, 0, 0),
                (0, 0, 1),
                S.phase_deg
                + index * 360.0 / S.tooth_count,
            )
        )

    return body.clean()


def build_drive():
    require_cadquery()

    body = build_blank().cut(
        cylinder(
            S.drive_bore_mm / 2.0,
            S.width_mm + 2.0,
        )
    )

    radius = S.bolt_pcd_mm / 2.0

    for index in range(S.bolt_count):
        angle = math.radians(
            S.bolt_phase_deg
            + index * 360.0 / S.bolt_count
        )
        x_value = radius * math.cos(angle)
        y_value = radius * math.sin(angle)

        hole = (
            cq.Workplane("XY")
            .center(x_value, y_value)
            .circle(S.bolt_hole_mm / 2.0)
            .extrude(
                S.width_mm / 2.0 + 1.0,
                both=True,
            )
        )
        body = body.cut(hole)

    return body.clean()


def build_idler():
    require_cadquery()

    body = build_blank().cut(
        cylinder(
            S.center_relief_mm / 2.0,
            S.width_mm + 2.0,
        )
    )

    pocket_height = S.bearing_depth_mm + 0.2
    z_offset = (
        S.width_mm / 2.0
        - S.bearing_depth_mm / 2.0
        + 0.05
    )

    for sign in (-1.0, 1.0):
        body = body.cut(
            cylinder(
                S.bearing_seat_mm / 2.0,
                pocket_height,
            ).translate(
                (0.0, 0.0, sign * z_offset)
            )
        )

    return body.clean()


def runtime_validation():
    require_cadquery()

    ring = build_ring_hub_spokes()
    tooth = build_embedded_tooth()
    intersection = volume_of(ring.intersect(tooth))

    drive = build_drive()
    idler = build_idler()

    return {
        "tooth_ring_intersection_mm3": intersection,
        "drive_solid_count": solid_count(drive),
        "idler_solid_count": solid_count(idler),
        "runtime_pass": (
            intersection is not None
            and intersection >= S.minimum_intersection_mm3
            and solid_count(drive) == 1
            and solid_count(idler) == 1
        ),
    }


def static_validation():
    checks = {
        "tooth_count": S.tooth_count == 12,
        "embed_depth": S.embed_depth_mm >= 4.0,
        "positive_overlap": (
            S.embed_radius_mm < S.root_radius_mm
        ),
        "wide_foot": (
            S.embed_width_mm > S.root_width_mm
        ),
        "ring_thickness": (
            S.ring_thickness_mm >= 9.0
        ),
        "spoke_width": S.spoke_width_mm >= 12.0,
        "tip_retained": S.tip_radius_mm == 33.07,
        "root_retained": S.root_radius_mm == 29.47,
    }

    failures = [
        key for key, value in checks.items()
        if not value
    ]

    return {
        "version": VERSION,
        "status": STATUS,
        "result": (
            "STATIC_PASS_WITH_WARNINGS"
            if not failures
            else "STATIC_FAIL"
        ),
        "cadquery_available": cq is not None,
        "specification": asdict(S),
        "checks": checks,
        "failures": len(failures),
        "warnings": 3,
    }


def place_on_bed(shape):
    bounds = shape.val().BoundingBox()
    return shape.translate(
        (0.0, 0.0, -bounds.zmin)
    )


def export_shape(shape, path):
    require_cadquery()
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path))


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)
    return digest.hexdigest()


def write_checksums(out):
    lines = []
    for path in sorted(out.rglob("*")):
        if (
            path.is_file()
            and path.name != "SHA256SUMS.txt"
        ):
            lines.append(
                f"{sha256_file(path)}  "
                f"{path.relative_to(out).as_posix()}"
            )

    (out / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    validation = static_validation()

    (args.out / "reports").mkdir(
        parents=True,
        exist_ok=True,
    )
    (args.out / "source").mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        args.out
        / "reports"
        / "validation_report.json"
    ).write_text(
        json.dumps(
            validation,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    source_path = Path(__file__).resolve()
    copy_path = (
        args.out
        / "source"
        / source_path.name
    ).resolve()

    if source_path != copy_path:
        shutil.copy2(
            source_path,
            copy_path,
        )

    if not args.metadata_only:
        runtime = runtime_validation()

        (
            args.out
            / "reports"
            / "geometry_runtime_validation.json"
        ).write_text(
            json.dumps(
                runtime,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        if runtime["runtime_pass"]:
            export_shape(
                place_on_bed(build_drive()),
                args.out
                / "stl/petg"
                / "DRIVE_SPROCKET_V0131_CADQUERY.stl",
            )
            export_shape(
                place_on_bed(build_idler()),
                args.out
                / "stl/petg"
                / "IDLER_SPROCKET_V0131_CADQUERY.stl",
            )
            export_shape(
                build_drive(),
                args.out
                / "step"
                / "DRIVE_SPROCKET_V0131.step",
            )
            export_shape(
                build_idler(),
                args.out
                / "step"
                / "IDLER_SPROCKET_V0131.step",
            )
        else:
            (
                args.out
                / "reports"
                / "GEOMETRY_HOLD_V0131.txt"
            ).write_text(
                "Runtime integration gate failed.\n",
                encoding="utf-8",
            )

    write_checksums(args.out)

    print(json.dumps({
        "version": VERSION,
        "validation": validation["result"],
        "failures": validation["failures"],
        "warnings": validation["warnings"],
        "cadquery_available": cq is not None,
        "first_print": (
            "DRIVE_SPROCKET_FIRST_ARTICLE_"
            "V0131_PETG.stl"
        ),
    }, ensure_ascii=False, indent=2))

    return 0 if validation["failures"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
