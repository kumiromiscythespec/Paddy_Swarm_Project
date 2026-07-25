from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Callable


SLIDE_CLEARANCE_CANDIDATES_MM = (0.20, 0.30, 0.40, 0.50)
SADDLE_CLEARANCE_CANDIDATES_MM = (0.20, 0.30, 0.40, 0.50)
PIN_BORE_CANDIDATES_MM = (6.10, 6.20, 6.30, 6.40)
THUMB_LATCH_THICKNESS_CANDIDATES_MM = (1.20, 1.60, 2.00, 2.40)
THUMB_LATCH_GAP_CANDIDATES_MM = (0.20, 0.30, 0.40, 0.50)
PART_NUMBERS = (
    "COUPON-01",
    "COUPON-02",
    "COUPON-03",
    "COUPON-04",
    "COUPON-05",
)
COMMON_MARKING_HANDLER = "COMMON_ENGRAVED_PART_NUMBER_V1"
PART_NUMBER_AUTHORITY = "SOURCE_DEFINED_COUPON_ID"
PART_NUMBER_FORMAT_AUTHORITY = (
    "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/"
    "coupon_geometry.py::PART_NUMBERS"
)


@dataclass(frozen=True)
class CouponSpec:
    coupon_id: str
    part_number: str
    filename: str
    purpose: str
    variants: str
    classification: str
    marking_surface: str
    marking_center_mm: tuple[float, float, float]
    marking_size_mm: float
    print_orientation: str = (
        "XY base face on build plate; marked +Z face upward"
    )


@dataclass(frozen=True)
class PartNumberMarkingEvidence:
    coupon_id: str
    part_number: str
    geometry_part_number: str
    physical_marking: str
    marking_surface: str
    marking_surface_class: str
    print_orientation: str
    support_removal_exposure: bool
    common_marking_handler: str
    common_marking_handler_invoked: bool
    marking_verified: bool
    glyph_solid_count: int
    intersecting_glyph_solid_count: int
    floating_part_number_solid_count: int
    engraved_volume_mm3: float


@dataclass(frozen=True)
class CouponGeometry:
    shape: object
    marking: PartNumberMarkingEvidence

    def BoundingBox(self):
        return self.shape.BoundingBox()


COUPON_SPECS = (
    CouponSpec(
        "COUPON-01",
        "COUPON-01",
        "coupon_01_tslot_saddle_fit.stl",
        "20x20 T-slot envelope saddle fit",
        "clearance 0.20|0.30|0.40|0.50 mm",
        "FIT TEST ONLY; NOT LOAD TEST; NOT FULL ROVER PART",
        "top face of non-functional rear identification band",
        (63.0, 42.0, 2.0),
        4.0,
    ),
    CouponSpec(
        "COUPON-02",
        "COUPON-02",
        "coupon_02_slide_fit.stl",
        "slide tongue / receiver resistance",
        "clearance 0.20|0.30|0.40|0.50 mm",
        "FIT TEST ONLY; NOT LOAD TEST; NOT FULL ROVER PART",
        "top face of non-functional rear identification band",
        (63.0, 54.0, 3.0),
        4.0,
    ),
    CouponSpec(
        "COUPON-03",
        "COUPON-03",
        "coupon_03_pin_alignment.stl",
        "positive-stop pin alignment and 6 mm-class bore fit",
        "bore 6.10|6.20|6.30|6.40 mm",
        "FIT TEST ONLY; NOT LOAD TEST; NOT FULL ROVER PART",
        "top face of non-functional gauge identification band",
        (50.0, 78.0, 3.0),
        4.0,
    ),
    CouponSpec(
        "COUPON-04",
        "COUPON-04",
        "coupon_04_thumb_latch_secondary.stl",
        "secondary latch feel comparison",
        (
            "thickness 1.20|1.60|2.00|2.40 mm; "
            "gap 0.20|0.30|0.40|0.50 mm"
        ),
        "FIT TEST ONLY; SECONDARY ONLY; NOT LOAD TEST",
        "top face of non-functional receiver identification band",
        (63.0, 76.0, 1.0),
        4.0,
    ),
    CouponSpec(
        "COUPON-05",
        "COUPON-05",
        "coupon_05_marking_readability.stl",
        "embossed assembly marking readability",
        "orientation, connection, and operation labels",
        "FIT TEST ONLY; NOT LOAD TEST; NOT FULL ROVER PART",
        "top face of non-functional rear identification band",
        (77.0, 98.0, 2.0),
        4.0,
    ),
)
SPEC_BY_ID = {spec.coupon_id: spec for spec in COUPON_SPECS}


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("CADQUERY_ENVIRONMENT_REQUIRED") from exc
    return cq


def _box(cq, dx, dy, dz, x=0.0, y=0.0, z=0.0):
    return (
        cq.Workplane("XY")
        .box(dx, dy, dz, centered=(False, False, False))
        .translate((x, y, z))
        .val()
    )


def _raised_text(
    cq,
    text: str,
    x: float,
    y: float,
    z: float,
    *,
    size: float = 4.0,
    depth: float = 0.55,
) -> list:
    return (
        cq.Workplane("XY")
        .workplane(offset=z)
        .center(x, y)
        .text(
            text,
            size,
            depth,
            combine=False,
            halign="center",
            valign="center",
        )
        .vals()
    )


def _text_solids(
    cq,
    text: str,
    x: float,
    y: float,
    surface_z: float,
    *,
    size: float,
    depth: float,
) -> list:
    overlap = 0.05
    return (
        cq.Workplane("XY")
        .workplane(offset=surface_z - depth)
        .center(x, y)
        .text(
            text,
            size,
            depth + overlap,
            combine=False,
            halign="center",
            valign="center",
        )
        .vals()
    )


def _engraved_text(
    cq,
    target,
    text: str,
    x: float,
    y: float,
    surface_z: float,
    *,
    size: float,
    depth: float = 0.55,
):
    text_solids = _text_solids(
        cq,
        text,
        x,
        y,
        surface_z,
        size=size,
        depth=depth,
    )
    if not text_solids:
        raise RuntimeError("PRINTED_PART_NUMBER_TEXT_SOLID_MISSING")
    return target.cut(*text_solids), text_solids


def apply_part_number_marking(
    cq,
    target,
    spec: CouponSpec,
) -> tuple[object, PartNumberMarkingEvidence]:
    """Engrave one source-authoritative part number and prove it is not floating."""

    if not spec.part_number.strip():
        raise RuntimeError("PRINTED_PART_NUMBER_MISSING")
    x, y, surface_z = spec.marking_center_mm
    before_volume = float(target.Volume())
    marked, text_solids = _engraved_text(
        cq,
        target,
        spec.part_number,
        x,
        y,
        surface_z,
        size=spec.marking_size_mm,
        depth=0.60,
    )
    intersections = [
        float(target.intersect(glyph).Volume()) for glyph in text_solids
    ]
    intersecting_count = sum(volume > 1.0e-6 for volume in intersections)
    engraved_volume = before_volume - float(marked.Volume())
    verified = (
        intersecting_count == len(text_solids)
        and engraved_volume > 1.0e-4
    )
    if not verified:
        raise RuntimeError(
            f"PRINTED_PART_NUMBER_GEOMETRY_MISMATCH:{spec.part_number}"
        )
    evidence = PartNumberMarkingEvidence(
        coupon_id=spec.coupon_id,
        part_number=spec.part_number,
        geometry_part_number=spec.part_number,
        physical_marking="ENGRAVED",
        marking_surface=spec.marking_surface,
        marking_surface_class="NON_FUNCTIONAL_PRINTABLE_EXTERIOR",
        print_orientation=spec.print_orientation,
        support_removal_exposure=False,
        common_marking_handler=COMMON_MARKING_HANDLER,
        common_marking_handler_invoked=True,
        marking_verified=True,
        glyph_solid_count=len(text_solids),
        intersecting_glyph_solid_count=intersecting_count,
        floating_part_number_solid_count=0,
        engraved_volume_mm3=round(engraved_volume, 6),
    )
    return marked, evidence


def _compound(cq, shapes: list):
    flattened = []
    for shape in shapes:
        if isinstance(shape, (list, tuple)):
            flattened.extend(shape)
        else:
            flattened.append(shape)
    return cq.Compound.makeCompound(flattened)


def filename_matches_part_number(filename: str, part_number: str) -> bool:
    filename_token = re.sub(r"[^a-z0-9]", "", Path(filename).stem.lower())
    part_number_token = re.sub(r"[^a-z0-9]", "", part_number.lower())
    return bool(part_number_token) and filename_token.startswith(
        part_number_token
    )


def build_coupon_01_tslot_saddle_fit():
    cq = _cq()
    spec = SPEC_BY_ID["COUPON-01"]
    base = _box(cq, 126, 48, 2)
    shapes = []
    for index, clearance in enumerate(SADDLE_CLEARANCE_CANDIDATES_MM):
        inner = 20.0 + 2.0 * clearance
        x = 2.0 + index * 31.0
        outer = _box(cq, inner + 6.0, 24.0, 12.0, x, 0.0, 2.0)
        channel = _box(
            cq,
            inner,
            20.5,
            10.2,
            x + 3.0,
            -0.1,
            4.0,
        )
        shapes.append(outer.cut(channel))
        base, _ = _engraved_text(
            cq,
            base,
            f"{clearance:.2f}",
            x + (inner + 6.0) / 2.0,
            29.0,
            2.0,
            size=3.5,
        )
    base, _ = _engraved_text(
        cq,
        base,
        "FIT TEST ONLY",
        63.0,
        35.0,
        2.0,
        size=4.0,
    )
    base, marking = apply_part_number_marking(cq, base, spec)
    return CouponGeometry(_compound(cq, [base, *shapes]), marking)


def build_coupon_02_slide_fit():
    cq = _cq()
    spec = SPEC_BY_ID["COUPON-02"]
    identification_band = _box(cq, 126, 20, 3, 0, 39, 0)
    shapes = []
    tongue_width = 12.0
    for index, clearance in enumerate(SLIDE_CLEARANCE_CANDIDATES_MM):
        x = 2.0 + index * 31.0
        inner = tongue_width + 2.0 * clearance
        outer = _box(cq, inner + 6.0, 18.0, 10.0, x, 21.0, 0.0)
        channel = _box(
            cq,
            inner,
            18.2,
            6.2,
            x + 3.0,
            20.9,
            4.0,
        )
        shapes.append(outer.cut(channel))
        tongue_x = x + 3.0 + clearance
        shapes.append(_box(cq, tongue_width, 16.0, 4.0, tongue_x, 0, 0))
        shapes.append(_box(cq, 0.6, 24.0, 1.0, tongue_x + 5.7, 15.5, 0))
        identification_band, _ = _engraved_text(
            cq,
            identification_band,
            f"{clearance:.2f}",
            x + (inner + 6.0) / 2.0,
            42.0,
            3.0,
            size=3.2,
        )
    identification_band, _ = _engraved_text(
        cq,
        identification_band,
        "FIT TEST ONLY",
        63.0,
        48.0,
        3.0,
        size=3.8,
    )
    identification_band, marking = apply_part_number_marking(
        cq, identification_band, spec
    )
    return CouponGeometry(
        _compound(cq, [identification_band, *shapes]), marking
    )


def build_coupon_03_pin_alignment():
    cq = _cq()
    spec = SPEC_BY_ID["COUPON-03"]
    base = _box(cq, 52, 38, 3)
    left_wall = _box(cq, 7, 25, 18, 0, 13, 3)
    right_wall = _box(cq, 7, 25, 18, 45, 13, 3)
    receiver = base.fuse(left_wall, right_wall)
    receiver_bore = cq.Solid.makeCylinder(
        3.10,
        54.0,
        cq.Vector(-1.0, 28.0, 13.0),
        cq.Vector(1.0, 0.0, 0.0),
    )
    receiver = receiver.cut(receiver_bore)
    tongue = _box(cq, 36, 28, 8, 62, 6, 0)
    tongue_bore = cq.Solid.makeCylinder(
        3.05,
        38.0,
        cq.Vector(61.0, 21.0, 4.0),
        cq.Vector(1.0, 0.0, 0.0),
    )
    tongue = tongue.cut(tongue_bore)
    stop = _box(cq, 36, 3, 12, 62, 31, 0)
    gauge = _box(cq, 100, 38, 3, 0, 44, 0)
    for index, diameter in enumerate(PIN_BORE_CANDIDATES_MM):
        hole = cq.Solid.makeCylinder(
            diameter / 2.0,
            3.4,
            cq.Vector(14.0 + index * 24.0, 52.0, -0.1),
            cq.Vector(0.0, 0.0, 1.0),
        )
        gauge = gauge.cut(hole)
        gauge, _ = _engraved_text(
            cq,
            gauge,
            f"{diameter:.2f}",
            14.0 + index * 24.0,
            63.0,
            3.0,
            size=3.0,
        )
    gauge, _ = _engraved_text(
        cq,
        gauge,
        "FIT TEST ONLY",
        50.0,
        71.0,
        3.0,
        size=4.0,
    )
    gauge, marking = apply_part_number_marking(cq, gauge, spec)
    return CouponGeometry(
        _compound(cq, [receiver, tongue.fuse(stop), gauge]), marking
    )


def build_coupon_04_thumb_latch_secondary():
    cq = _cq()
    spec = SPEC_BY_ID["COUPON-04"]
    shapes = [_box(cq, 126, 10, 4)]
    receivers = []
    identification_band = _box(cq, 126, 27, 1, 0, 53, 0)
    for index, (thickness, gap) in enumerate(
        zip(
            THUMB_LATCH_THICKNESS_CANDIDATES_MM,
            THUMB_LATCH_GAP_CANDIDATES_MM,
        )
    ):
        x = 4.0 + index * 31.0
        arm = _box(cq, 17.0, 38.0, thickness, x, 8.0, 0)
        hook = _box(cq, 23.0, 5.0, thickness + 2.0, x - 3.0, 43.0, 0)
        receiver_y = 48.0 + gap
        receiver = _box(cq, 23.0, 5.0, 6.0, x - 3.0, receiver_y, 0)
        shapes.append(arm.fuse(hook))
        receivers.append(receiver)
        identification_band, _ = _engraved_text(
            cq,
            identification_band,
            f"{thickness:.1f}/{gap:.1f}",
            x + 8.5,
            57.5,
            1.0,
            size=3.0,
        )
    identification_band = identification_band.fuse(*receivers)
    identification_band, _ = _engraved_text(
        cq,
        identification_band,
        "SECONDARY ONLY",
        63.0,
        64.0,
        1.0,
        size=4.0,
    )
    identification_band, _ = _engraved_text(
        cq,
        identification_band,
        "FIT TEST ONLY",
        63.0,
        70.0,
        1.0,
        size=3.8,
    )
    identification_band, marking = apply_part_number_marking(
        cq, identification_band, spec
    )
    return CouponGeometry(
        _compound(cq, [*shapes, identification_band]), marking
    )


def build_coupon_05_marking_readability():
    cq = _cq()
    spec = SPEC_BY_ID["COUPON-05"]
    base = _box(cq, 154, 104, 2)
    rows = (
        ("FRONT   REAR", 78.0, 11.0, 8.0),
        ("LEFT   RIGHT", 78.0, 25.0, 8.0),
        ("TOP   BOTTOM", 78.0, 39.0, 8.0),
        ("A1 A2   B1 B2   F1 F2   L1 L2", 78.0, 53.0, 6.0),
        ("1 INSERT   2 SLIDE", 78.0, 66.0, 6.2),
        ("3 LOCK   4 VERIFY", 78.0, 77.0, 6.2),
        ("FIT TEST ONLY", 78.0, 87.0, 5.0),
    )
    for text, x, y, size in rows:
        base = base.fuse(
            *_raised_text(cq, text, x, y, 1.95, size=size, depth=0.60)
        )
    base, marking = apply_part_number_marking(cq, base, spec)
    return CouponGeometry(base, marking)


_BUILDERS: tuple[Callable[[], CouponGeometry], ...] = (
    build_coupon_01_tslot_saddle_fit,
    build_coupon_02_slide_fit,
    build_coupon_03_pin_alignment,
    build_coupon_04_thumb_latch_secondary,
    build_coupon_05_marking_readability,
)
COUPON_BUILDERS: tuple[tuple[str, str, Callable], ...] = tuple(
    (spec.coupon_id, spec.filename, builder)
    for spec, builder in zip(COUPON_SPECS, _BUILDERS)
)
COUPON_EXPORT_ARTIFACTS = (
    *(spec.filename for spec in COUPON_SPECS),
    "coupon_manifest.csv",
    "printed_part_number_audit.json",
    "printed_part_number_geometry_report.txt",
    "coupon_marking_map.csv",
)


def _canonical_json(data: object) -> str:
    return json.dumps(
        data,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": "),
    ) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def coupon_manifest_rows() -> list[dict[str, object]]:
    return [
        {
            "coupon_id": spec.coupon_id,
            "part_number": spec.part_number,
            "filename": spec.filename,
            "purpose": spec.purpose,
            "variants": spec.variants,
            "classification": spec.classification,
            "printer": "Bambu Lab A1; 100% scale; no support preferred",
            "physical_marking": "ENGRAVED",
            "marking_surface": spec.marking_surface,
            "marking_verified": "true",
        }
        for spec in COUPON_SPECS
    ]


def printed_part_manifest_records() -> list[dict[str, object]]:
    return [
        {
            "coupon_id": spec.coupon_id,
            "part_number": spec.part_number,
            "part_number_authority": PART_NUMBER_AUTHORITY,
            "part_number_format_authority": PART_NUMBER_FORMAT_AUTHORITY,
            "revision": None,
            "revision_status": "NOT_DEFINED_FOR_SOURCE_COUPON_ID",
            "filename": spec.filename,
            "physical_marking": "ENGRAVED",
            "geometry_part_number": spec.part_number,
            "marking_surface": spec.marking_surface,
            "marking_surface_class": "NON_FUNCTIONAL_PRINTABLE_EXTERIOR",
            "marking_verified": True,
            "print_orientation": spec.print_orientation,
            "support_removal_exposure": False,
            "common_marking_handler": COMMON_MARKING_HANDLER,
            "common_marking_handler_invoked": True,
            "floating_part_number_solid_count": 0,
            "contains_fit_test_only": True,
            "contains_secondary_only": spec.coupon_id == "COUPON-04",
            "contains_candidate_values": True,
        }
        for spec in COUPON_SPECS
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_coupons(output_directory: Path) -> list[dict[str, object]]:
    cq = _cq()
    output = output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    audit_records = []
    for coupon_id, filename, builder in COUPON_BUILDERS:
        geometry = builder()
        evidence = geometry.marking
        if (
            evidence.coupon_id != coupon_id
            or evidence.part_number != coupon_id
            or not evidence.marking_verified
            or not evidence.common_marking_handler_invoked
            or evidence.floating_part_number_solid_count != 0
        ):
            raise RuntimeError(
                f"PRINTED_PART_NUMBER_GEOMETRY_MISMATCH:{coupon_id}"
            )
        stl_path = output / filename
        cq.exporters.export(
            geometry.shape,
            str(stl_path),
            tolerance=0.01,
            angularTolerance=0.1,
        )
        box = geometry.shape.BoundingBox()
        record = {
            **asdict(evidence),
            "filename": filename,
            "geometry_marking_connected": True,
            "contains_fit_test_only": True,
            "contains_secondary_only": coupon_id == "COUPON-04",
            "contains_candidate_values": True,
            "filename_part_number_match": filename_matches_part_number(
                filename, evidence.part_number
            ),
            "stl_sha256": _sha256(stl_path),
            "stl_size_bytes": stl_path.stat().st_size,
            "stl_solid_count": len(geometry.shape.Solids()),
            "bounding_box_mm": {
                "x": round(float(box.xlen), 6),
                "y": round(float(box.ylen), 6),
                "z": round(float(box.zlen), 6),
            },
        }
        audit_records.append(record)

    rows = coupon_manifest_rows()
    _write_csv(output / "coupon_manifest.csv", rows)
    audit = {
        "schema": "PS_PRINTED_PART_NUMBER_AUDIT_V0_1",
        "part_number_authority": PART_NUMBER_AUTHORITY,
        "part_number_format_authority": PART_NUMBER_FORMAT_AUTHORITY,
        "revision_status": "NOT_DEFINED_FOR_SOURCE_COUPON_ID",
        "exported_coupon_count": len(audit_records),
        "part_number_count": len(
            [row for row in audit_records if row["part_number"].strip()]
        ),
        "unique_part_number_count": len(
            {row["part_number"] for row in audit_records}
        ),
        "physically_marked_part_count": len(
            [row for row in audit_records if row["marking_verified"]]
        ),
        "floating_part_number_solid_count": sum(
            int(row["floating_part_number_solid_count"])
            for row in audit_records
        ),
        "records": audit_records,
    }
    (output / "printed_part_number_audit.json").write_text(
        _canonical_json(audit), encoding="utf-8", newline="\n"
    )
    report_lines = [
        "PRINTED PART NUMBER GEOMETRY REPORT",
        f"handler={COMMON_MARKING_HANDLER}",
        f"part_number_authority={PART_NUMBER_AUTHORITY}",
        "revision_status=NOT_DEFINED_FOR_SOURCE_COUPON_ID",
        "",
    ]
    for record in audit_records:
        report_lines.extend(
            [
                f"{record['coupon_id']} / {record['part_number']}",
                f"  filename={record['filename']}",
                f"  physical_marking={record['physical_marking']}",
                f"  marking_surface={record['marking_surface']}",
                f"  print_orientation={record['print_orientation']}",
                f"  glyph_solids={record['glyph_solid_count']}",
                (
                    "  intersecting_glyph_solids="
                    f"{record['intersecting_glyph_solid_count']}"
                ),
                (
                    "  floating_part_number_solids="
                    f"{record['floating_part_number_solid_count']}"
                ),
                f"  engraved_volume_mm3={record['engraved_volume_mm3']}",
                f"  marking_verified={str(record['marking_verified']).lower()}",
                "",
            ]
        )
    (output / "printed_part_number_geometry_report.txt").write_text(
        "\n".join(report_lines), encoding="utf-8", newline="\n"
    )
    map_rows = [
        {
            "coupon_id": row["coupon_id"],
            "part_number": row["part_number"],
            "filename": row["filename"],
            "physical_marking": row["physical_marking"],
            "marking_surface": row["marking_surface"],
            "print_orientation": row["print_orientation"],
            "marking_verified": str(row["marking_verified"]).lower(),
        }
        for row in audit_records
    ]
    _write_csv(output / "coupon_marking_map.csv", map_rows)
    return rows


def replay_coupon_exports(reference_directory: Path) -> dict[str, object]:
    reference = reference_directory.resolve()
    with tempfile.TemporaryDirectory(
        prefix="paddy_coupon_marking_replay_"
    ) as temporary:
        replay = Path(temporary).resolve()
        export_coupons(replay)
        rows = []
        for filename in COUPON_EXPORT_ARTIFACTS:
            first_path = reference / filename
            replay_path = replay / filename
            first_hash = _sha256(first_path)
            replay_hash = _sha256(replay_path)
            rows.append(
                {
                    "filename": filename,
                    "first_sha256": first_hash,
                    "replay_sha256": replay_hash,
                    "match": first_hash == replay_hash,
                }
            )
    return {
        "status": "PASS" if all(row["match"] for row in rows) else "FAIL",
        "files": rows,
    }
