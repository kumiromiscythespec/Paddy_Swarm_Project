#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crawler_h1 v0.13.0 track-undercarriage production generator.

Uses the physically accepted v0.12.5 WIDE-46 link and SPR-CB tooth geometry.
Adds:
- production link/LUG plates;
- φ10 mm drive-shaft sprocket with metal-hub bolt pattern;
- 6000-2RS idler sprocket;
- 6000-2RS support roller;
- single-track and dual-track production manifests.

The link tooth, hinge, guide and LUG interface are not modified.
Powered, load, soil, mud and water approval still require staged testing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence
import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import sys

try:
    import cadquery as cq
    from cadquery import exporters
except Exception:
    cq = None
    exporters = None


VERSION = "crawler-h1-v0.13.0-track-undercarriage-production"
PACKAGE_NAME = "crawler_h1_track_undercarriage_production_v0_13_0"
STATUS = "PRODUCTION_PREP_LINK_LUG_APPROVED_NEW_HUB_BEARING_INTERFACES_REQUIRE_FIRST_ARTICLE"


@dataclass(frozen=True)
class ProductionSpec:
    links_per_track: int = 40
    spare_links_per_track: int = 8
    link_pitch_mm: float = 20.0

    hinge_shaft_diameter_mm: float = 3.0
    hinge_shaft_length_mm: float = 50.5

    drive_shaft_nominal_mm: float = 10.0
    drive_bore_a_mm: float = 10.2
    drive_bore_b_mm: float = 10.3
    drive_bore_c_mm: float = 10.4

    drive_hub_radius_mm: float = 18.0
    drive_hub_bolt_count: int = 4
    drive_hub_pcd_mm: float = 24.0
    drive_hub_bolt_hole_mm: float = 4.4
    drive_hub_bolt_phase_deg: float = 45.0

    bearing_name: str = "6000-2RS"
    bearing_id_mm: float = 10.0
    bearing_od_mm: float = 26.0
    bearing_width_mm: float = 8.0
    bearing_seat_a_mm: float = 26.0
    bearing_seat_b_mm: float = 26.2
    bearing_seat_c_mm: float = 26.4
    bearing_seat_depth_mm: float = 8.2
    bearing_center_relief_mm: float = 12.0

    roller_od_mm: float = 50.0
    roller_width_mm: float = 44.0
    roller_edge_chamfer_mm: float = 0.8

    tension_stroke_mm: float = 12.0
    nominal_center_distance_mm: float = 280.0

    material_link: str = "PETG"
    material_lug: str = "TPU 95A"
    support: str = "OFF"
    nozzle_mm: float = 0.4
    layer_height_mm: float = 0.20


P = ProductionSpec()
_V125 = None
_SPR = None


def require_cadquery() -> None:
    if cq is None or exporters is None:
        raise RuntimeError(
            "CadQuery is not installed. Use --metadata-only or run in paddy-cad."
        )


def load_dependency(filename: str, module_name: str):
    path = Path(__file__).resolve().parent / "dependencies" / filename
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def v125():
    global _V125
    if _V125 is None:
        _V125 = load_dependency(
            "crawler_h1_wide_span_three_knuckle_link_v0_12_5.py",
            "crawler_h1_v0125_dep_for_v0130",
        )
    return _V125


def spr():
    global _SPR
    if _SPR is None:
        _SPR = load_dependency(
            "crawler_h1_sprocket_fit_test_v0_4_0.py",
            "crawler_h1_sprocket_v040_dep_for_v0130",
        )
    return _SPR


def lug_module():
    return v125().v120().lug_dep()


def make_compound(parts: Iterable[object]):
    require_cadquery()
    values = [part.val() if hasattr(part, "val") else part for part in parts]
    return cq.Compound.makeCompound(values)


def place_on_bed(shape):
    require_cadquery()
    obj = shape.val() if hasattr(shape, "val") else shape
    bb = obj.BoundingBox()
    return shape.translate((0.0, 0.0, -bb.zmin))


def centered_cylinder(diameter_mm: float, height_mm: float):
    require_cadquery()
    return (
        cq.Workplane("XY")
        .circle(diameter_mm / 2.0)
        .extrude(height_mm / 2.0, both=True)
    )


def build_link():
    require_cadquery()
    return v125().build_link(False)


def build_link_print():
    require_cadquery()
    return v125().build_link_print()


def build_lug():
    require_cadquery()
    lug = lug_module()
    return lug.build_lug(
        lug.DEFAULT,
        lug.STANDARD_CAPTURE,
        lug.STANDARD_HEAD,
    )


def build_lug_print():
    require_cadquery()
    return place_on_bed(build_lug())


def build_base_sprocket():
    require_cadquery()
    module = spr()
    return module.build_sprocket(module.DEFAULT, module.STANDARD_FIT)


def build_drive_sprocket(bore_mm: float = P.drive_bore_b_mm):
    require_cadquery()
    module = spr()
    width = module.DEFAULT.axial_width_mm

    body = build_base_sprocket().union(
        centered_cylinder(2.0 * P.drive_hub_radius_mm, width)
    )

    body = body.cut(centered_cylinder(bore_mm, width + 2.0))

    hole_radius = P.drive_hub_pcd_mm / 2.0
    for index in range(P.drive_hub_bolt_count):
        angle = math.radians(
            P.drive_hub_bolt_phase_deg
            + index * 360.0 / P.drive_hub_bolt_count
        )
        x = hole_radius * math.cos(angle)
        y = hole_radius * math.sin(angle)
        hole = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(P.drive_hub_bolt_hole_mm / 2.0)
            .extrude(width / 2.0 + 1.0, both=True)
        )
        body = body.cut(hole)

    return body.clean()


def build_idler_sprocket(
    seat_mm: float = P.bearing_seat_b_mm,
):
    require_cadquery()
    module = spr()
    width = module.DEFAULT.axial_width_mm

    body = build_base_sprocket().union(
        centered_cylinder(2.0 * P.drive_hub_radius_mm, width)
    )

    body = body.cut(
        centered_cylinder(P.bearing_center_relief_mm, width + 2.0)
    )

    pocket_h = P.bearing_seat_depth_mm + 0.2
    z_abs = width / 2.0 - P.bearing_seat_depth_mm / 2.0 + 0.05

    for sign in (-1.0, 1.0):
        pocket = centered_cylinder(seat_mm, pocket_h).translate(
            (0.0, 0.0, sign * z_abs)
        )
        body = body.cut(pocket)

    return body.clean()


def build_support_roller(
    seat_mm: float = P.bearing_seat_b_mm,
):
    require_cadquery()
    body = centered_cylinder(P.roller_od_mm, P.roller_width_mm)

    body = body.cut(
        centered_cylinder(
            P.bearing_center_relief_mm,
            P.roller_width_mm + 2.0,
        )
    )

    pocket_h = P.bearing_seat_depth_mm + 0.2
    z_abs = (
        P.roller_width_mm / 2.0
        - P.bearing_seat_depth_mm / 2.0
        + 0.05
    )

    for sign in (-1.0, 1.0):
        body = body.cut(
            centered_cylinder(seat_mm, pocket_h).translate(
                (0.0, 0.0, sign * z_abs)
            )
        )

    try:
        body = body.edges("|Z").chamfer(P.roller_edge_chamfer_mm)
    except Exception:
        pass

    return body.clean()


def arrange_grid(
    shape,
    columns: int,
    rows: int,
    step_x_mm: float,
    step_y_mm: float,
):
    require_cadquery()
    parts = []
    for row in range(rows):
        for column in range(columns):
            parts.append(
                shape.translate((
                    column * step_x_mm,
                    row * step_y_mm,
                    0.0,
                ))
            )
    compound = make_compound(parts)
    obj = compound
    bb = obj.BoundingBox()
    return cq.Workplane(obj=obj).translate((
        -(bb.xmin + bb.xmax) / 2.0,
        -(bb.ymin + bb.ymax) / 2.0,
        -bb.zmin,
    ))


def build_link_plate_12():
    return arrange_grid(build_link_print(), 4, 3, 38.0, 60.0)


def build_link_plate_24():
    return arrange_grid(build_link_print(), 6, 4, 38.0, 60.0)


def build_lug_plate_12():
    return arrange_grid(build_lug_print(), 4, 3, 22.0, 42.0)


def build_lug_plate_24():
    return arrange_grid(build_lug_print(), 6, 4, 22.0, 42.0)


def build_drive_bore_coupon():
    require_cadquery()
    parts = []
    for index, diameter in enumerate((
        P.drive_bore_a_mm,
        P.drive_bore_b_mm,
        P.drive_bore_c_mm,
    )):
        coupon = centered_cylinder(18.0, 8.0)
        coupon = coupon.cut(centered_cylinder(diameter, 10.0))
        parts.append(
            place_on_bed(coupon).translate(((index - 1) * 24.0, 0.0, 0.0))
        )
    return make_compound(parts)


def build_bearing_seat_coupon():
    require_cadquery()
    parts = []
    for index, diameter in enumerate((
        P.bearing_seat_a_mm,
        P.bearing_seat_b_mm,
        P.bearing_seat_c_mm,
    )):
        coupon = centered_cylinder(36.0, 10.0)
        pocket = centered_cylinder(diameter, 8.2).translate((0.0, 0.0, 1.0))
        coupon = coupon.cut(pocket)
        coupon = coupon.cut(centered_cylinder(12.0, 12.0))
        parts.append(
            place_on_bed(coupon).translate(((index - 1) * 44.0, 0.0, 0.0))
        )
    return make_compound(parts)


def build_single_track_hardpart_plate():
    require_cadquery()
    parts = [
        place_on_bed(build_drive_sprocket()).translate((-70, -40, 0)),
        place_on_bed(build_drive_sprocket()).translate((0, -40, 0)),
        place_on_bed(build_idler_sprocket()).translate((70, -40, 0)),
        place_on_bed(build_idler_sprocket()).translate((-70, 40, 0)),
    ]
    for index in range(4):
        x = -30 + (index % 2) * 60
        y = 20 + (index // 2) * 60
        parts.append(
            place_on_bed(build_support_roller()).translate((x, y, 0))
        )
    return make_compound(parts)


def build_dual_track_hardpart_plate():
    require_cadquery()
    parts = []
    # Split across logical rows; Bambu Studio may be used to rearrange if desired.
    for index in range(3):
        parts.append(
            place_on_bed(build_drive_sprocket()).translate(
                (-75 + index * 75, -75, 0)
            )
        )
        parts.append(
            place_on_bed(build_idler_sprocket()).translate(
                (-75 + index * 75, 0, 0)
            )
        )
    for index in range(8):
        col = index % 4
        row = index // 4
        parts.append(
            place_on_bed(build_support_roller()).translate(
                (-90 + col * 60, 75 + row * 55, 0)
            )
        )
    return make_compound(parts)


def theoretical_center_distance_mm() -> float:
    module = spr()
    pitch_diameter = module.DEFAULT.theoretical_pitch_diameter_mm
    loop_length = P.links_per_track * P.link_pitch_mm
    return (loop_length - math.pi * pitch_diameter) / 2.0


def static_validation() -> dict:
    module = spr()
    lug = lug_module()
    issues = []

    def add(level: str, code: str, detail: str):
        issues.append({"level": level, "code": code, "detail": detail})

    add(
        "PASS" if P.links_per_track == 40 else "FAIL",
        "LINKS_PER_TRACK",
        str(P.links_per_track),
    )
    add(
        "PASS" if P.spare_links_per_track == 8 else "FAIL",
        "SPARE_LINKS_PER_TRACK",
        str(P.spare_links_per_track),
    )
    add(
        "PASS" if abs(P.link_pitch_mm - 20.0) < 1e-9 else "FAIL",
        "LINK_PITCH",
        f"{P.link_pitch_mm:.3f} mm",
    )
    add(
        "PASS" if abs(P.hinge_shaft_length_mm - 50.5) < 1e-9 else "FAIL",
        "HINGE_SHAFT_LENGTH",
        f"{P.hinge_shaft_length_mm:.3f} mm",
    )
    add(
        "PASS" if abs(P.drive_shaft_nominal_mm - 10.0) < 1e-9 else "FAIL",
        "DRIVE_SHAFT_NOMINAL",
        f"φ{P.drive_shaft_nominal_mm:.3f} mm",
    )
    add(
        "PASS" if P.drive_bore_b_mm > P.drive_shaft_nominal_mm else "FAIL",
        "DRIVE_BORE_CLEARANCE",
        f"φ{P.drive_bore_b_mm:.3f} mm",
    )
    add(
        "PASS" if P.drive_hub_bolt_count == 4 else "FAIL",
        "METAL_HUB_BOLT_COUNT",
        str(P.drive_hub_bolt_count),
    )
    add(
        "PASS" if P.bearing_seat_b_mm >= P.bearing_od_mm else "FAIL",
        "BEARING_SEAT_CLEARANCE",
        f"φ{P.bearing_seat_b_mm:.3f} mm",
    )
    add(
        "PASS"
        if abs(module.STANDARD_FIT.tip_radius_mm - 33.07) < 1e-9
        else "FAIL",
        "SPR_CB_TIP_RADIUS_RETAINED",
        f"{module.STANDARD_FIT.tip_radius_mm:.3f} mm",
    )
    add(
        "PASS"
        if abs(module.STANDARD_FIT.root_radius_mm - 29.47) < 1e-9
        else "FAIL",
        "SPR_CB_ROOT_RADIUS_RETAINED",
        f"{module.STANDARD_FIT.root_radius_mm:.3f} mm",
    )
    add(
        "PASS"
        if lug.DEFAULT.lug_quantity == 40
        and lug.DEFAULT.lug_spare_quantity == 8
        else "FAIL",
        "LUG_QUANTITY_CONTRACT",
        f"{lug.DEFAULT.lug_quantity}+{lug.DEFAULT.lug_spare_quantity}",
    )
    add(
        "PASS" if P.tension_stroke_mm >= 10.0 else "FAIL",
        "TENSION_STROKE",
        f"{P.tension_stroke_mm:.3f} mm",
    )

    for code, detail in [
        (
            "DRIVE_HUB_FIRST_ARTICLE_REQUIRED",
            "The φ10.3 bore and PCD24 M4 pattern are new and require one physical hub-fit article.",
        ),
        (
            "BEARING_SEAT_FIRST_ARTICLE_REQUIRED",
            "The φ26.2 seat requires the 6000-2RS ABC coupon before production.",
        ),
        (
            "FRAME_INTERFACE_NOT_FINAL",
            "Drive bearing blocks, idler slider and roller axle lengths depend on the crawler_h1 frame.",
        ),
        (
            "POWERED_TEST_STAGED",
            "Production printing does not waive no-load, reverse, 15-minute and load tests.",
        ),
        (
            "CADQUERY_RUNTIME_NOT_RUN",
            "Boolean geometry and generated STL/STEP require paddy-cad.",
        ),
    ]:
        add("WARN", code, detail)

    failures = [x for x in issues if x["level"] == "FAIL"]
    warnings = [x for x in issues if x["level"] == "WARN"]

    return {
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": STATUS,
        "result": (
            "STATIC_PASS_WITH_WARNINGS"
            if not failures
            else "STATIC_FAIL"
        ),
        "cadquery_available": cq is not None,
        "production_spec": asdict(P),
        "derived": {
            "track_loop_length_mm": P.links_per_track * P.link_pitch_mm,
            "theoretical_center_distance_mm": theoretical_center_distance_mm(),
            "single_track_total_links": 48,
            "dual_track_total_links": 96,
            "single_track_starlocks_purchase": 110,
            "dual_track_starlocks_purchase": 220,
        },
        "issues": issues,
        "failures": len(failures),
        "warnings": len(warnings),
    }


def design_contract(validation: dict) -> dict:
    return {
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": STATUS,
        "verified_geometry": {
            "link": "STANDARD_V0125_WIDE_46_LINK",
            "sprocket_tooth": "SPR-CB 12T P20 W44",
            "hinge_shaft": "φ3 × 50.5 mm SUS304",
        },
        "single_track_lot": {
            "links": 48,
            "lugs": 48,
            "hinge_shafts": 48,
            "starlocks_purchase": 110,
            "drive_sprockets": 2,
            "idler_sprockets": 2,
            "support_rollers": 4,
        },
        "dual_track_lot": {
            "links": 96,
            "lugs": 96,
            "hinge_shafts": 96,
            "starlocks_purchase": 220,
            "drive_sprockets": 3,
            "idler_sprockets": 3,
            "support_rollers": 8,
        },
        "drive_sprocket": {
            "bore_fit_mm": [10.2, 10.3, 10.4],
            "standard_bore_mm": 10.3,
            "metal_hub_bolts": "4×M4, PCD24, phase45",
            "round_bore_alone_may_carry_torque": False,
        },
        "idler_and_roller": {
            "bearing": "6000-2RS 10×26×8",
            "seat_fit_mm": [26.0, 26.2, 26.4],
            "standard_seat_mm": 26.2,
        },
        "track_geometry": {
            "link_count": 40,
            "loop_length_mm": 800.0,
            "nominal_center_distance_mm": 280.0,
            "theoretical_center_distance_mm": theoretical_center_distance_mm(),
            "tensioner_stroke_mm": 12.0,
        },
        "validation_result": validation["result"],
    }


def export_shape(shape, path: Path) -> None:
    require_cadquery()
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path))


def export_geometry(out: Path, target: str) -> None:
    require_cadquery()

    if target in ("PARTS", "ALL"):
        export_shape(
            build_link_print(),
            out / "stl/petg/STANDARD_V0125_WIDE_46_LINK.stl",
        )
        export_shape(
            build_lug_print(),
            out / "stl/tpu/STANDARD_CAP_B_LUG_TPU.stl",
        )
        export_shape(
            place_on_bed(build_drive_sprocket()),
            out / "stl/petg/DRIVE_SPROCKET_B10_3_PCD24_M4.stl",
        )
        export_shape(
            place_on_bed(build_idler_sprocket()),
            out / "stl/petg/IDLER_SPROCKET_6000_SEAT_B.stl",
        )
        export_shape(
            place_on_bed(build_support_roller()),
            out / "stl/petg/SUPPORT_ROLLER_W44_OD50_6000.stl",
        )

    if target in ("PLATES", "ALL"):
        export_shape(build_link_plate_12(), out / "plates/LINK_12X_PETG.stl")
        export_shape(build_link_plate_24(), out / "plates/LINK_24X_PETG.stl")
        export_shape(build_lug_plate_12(), out / "plates/LUG_CAP_B_12X_TPU.stl")
        export_shape(build_lug_plate_24(), out / "plates/LUG_CAP_B_24X_TPU.stl")
        export_shape(
            build_drive_bore_coupon(),
            out / "plates/DRIVE_BORE_ABC_FIT_COUPON_PETG.stl",
        )
        export_shape(
            build_bearing_seat_coupon(),
            out / "plates/BEARING_6000_SEAT_ABC_FIT_COUPON_PETG.stl",
        )
        export_shape(
            build_single_track_hardpart_plate(),
            out / "plates/SINGLE_TRACK_SPROCKET_ROLLER_SET_PETG.stl",
        )
        export_shape(
            build_dual_track_hardpart_plate(),
            out / "plates/DUAL_TRACK_SPROCKET_ROLLER_SET_PETG.stl",
        )

    if target in ("REFERENCE", "ALL"):
        export_shape(
            build_drive_sprocket(),
            out / "step/DRIVE_SPROCKET_B10_3_PCD24_M4.step",
        )
        export_shape(
            build_idler_sprocket(),
            out / "step/IDLER_SPROCKET_6000_SEAT_B.step",
        )
        export_shape(
            build_support_roller(),
            out / "step/SUPPORT_ROLLER_W44_OD50_6000.step",
        )


def write_metadata(out: Path, validation: dict) -> None:
    (out / "contracts").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    (
        out / "contracts/crawler_h1_v0_13_0_design_contract.json"
    ).write_text(
        json.dumps(
            design_contract(validation),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (out / "reports/validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksums(out: Path) -> None:
    lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(
                f"{sha256_file(path)}  {path.relative_to(out).as_posix()}"
            )

    (out / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--target",
        choices=("PARTS", "PLATES", "REFERENCE", "ALL"),
        default="ALL",
    )
    parser.add_argument("--metadata-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validation = static_validation()
    write_metadata(args.out, validation)

    (args.out / "source").mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    dst = (args.out / "source" / src.name).resolve()
    if src != dst:
        shutil.copy2(src, dst)

    if not args.metadata_only:
        export_geometry(args.out, args.target)

    write_checksums(args.out)

    print(json.dumps({
        "version": VERSION,
        "validation": validation["result"],
        "failures": validation["failures"],
        "warnings": validation["warnings"],
        "cadquery_available": cq is not None,
        "single_track_links_lugs": 48,
        "dual_track_links_lugs": 96,
        "drive_bore_standard_mm": P.drive_bore_b_mm,
        "bearing_seat_standard_mm": P.bearing_seat_b_mm,
        "nominal_center_distance_mm": P.nominal_center_distance_mm,
        "first_new_interface_tests": [
            "DRIVE_BORE_ABC_FIT_COUPON_PETG.stl",
            "BEARING_6000_SEAT_ABC_FIT_COUPON_PETG.stl",
        ],
    }, ensure_ascii=False, indent=2))

    return 0 if validation["failures"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
