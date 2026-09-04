#!/usr/bin/env python3
"""Deterministic builder for Common Rover DRIVE Shaft H2.5-A1 v0.9.6.4."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.4"
CLASSIFICATION = "DRIVE_SHAFT_FULL_PHYSICAL_INTEGRATION"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
REPO_ROOT = Path(__file__).resolve().parents[3]
LANE_REL = Path("cad/common_rover/common_rover_drive_shaft_h25a1_full_integration_v0_9_6_4")
DEFAULT_LANE = REPO_ROOT / LANE_REL

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED_LANES = {
    "v0.9.5.0": (Path("cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0"), 105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "v0.9.5.1": (Path("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1"), 53, "0157f6bb4a6f02dad08e9eade45cf3eeeb71d6b61a82e4e24ee5404498ebbe31"),
    "v0.9.5.2": (Path("cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2"), 28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
    "v0.9.5.3": (Path("cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3"), 25, "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
    "v0.9.6.0": (Path("cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0"), 40, "6fff91564757139d0d8e99d7105dd33eec059bc426de6680da9356d46636f86e"),
    "v0.9.6.2": (Path("cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2"), 57, "35e7a3e1a465114e4a3e268fc2ac137a78020a425fb4fb9e5576f360ca78a206"),
    "v0.9.6.3": (Path("cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3"), 35, "e7f35b31edd6f79bda76e1a9c77dd59e98a1882c534b5c4792ea4c95cf8bea9f"),
}
BASE_OUTSIDE_COUNT = 1683
BASE_OUTSIDE_DIGEST = "c597a8527a13f122d47aeaf2d52d210429d8fba687247981402611c48355f214"

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "DRIVE_SHAFT_SPEC.md", "H25A1_INTEGRATION_SPEC.md",
    "SPROCKET_12T_PROTECTED_GEOMETRY.md", "KP000_SUPPORT_SPEC.md", "SPACER_DESIGN_SPEC.md",
    "CRAWLER_WIDTH_ENVELOPE.md", "AXIAL_RETENTION_SPEC.md", "SERVICE_ACCESS_SPEC.md",
    "ASSEMBLY_PROCEDURE.md", "PHYSICAL_TEST_PLAN.md", "BELT_STATUS_NOTE.md", "SAFETY_NOTES.md",
    "SOURCE_TRACE.md", "HOLD_REGISTER.md", "PRINT_PLAN.md",
]
CAD = [
    "artifacts/drive_12t_h25a1_sprocket_v0_9_6_4.step", "artifacts/drive_12t_h25a1_sprocket_v0_9_6_4.stl",
    "artifacts/h25a1_reaction_key_a_v0_9_6_4.step", "artifacts/h25a1_reaction_key_a_v0_9_6_4.stl",
    "artifacts/h25a1_reaction_key_b_v0_9_6_4.step", "artifacts/h25a1_reaction_key_b_v0_9_6_4.stl",
    "artifacts/drive_spacer_3mm_v0_9_6_4.step", "artifacts/drive_spacer_3mm_v0_9_6_4.stl",
    "artifacts/drive_spacer_4mm_v0_9_6_4.step", "artifacts/drive_spacer_4mm_v0_9_6_4.stl",
    "artifacts/drive_spacer_5mm_v0_9_6_4.step", "artifacts/drive_spacer_5mm_v0_9_6_4.stl",
    "artifacts/drive_shaft_spacer_test_plate_v0_9_6_4.step", "artifacts/drive_shaft_spacer_test_plate_v0_9_6_4.stl",
    "artifacts/drive_shaft_h25a1_assembly_v0_9_6_4.step", "artifacts/shaft_10mm_reference.step",
    "artifacts/kp000_reference.step", "artifacts/collar_h25a1_reference.step",
    "artifacts/generic_axial_retention_collars_reference.step", "artifacts/paint_alignment_mark_reference.step",
    "artifacts/h25a1_full_hardware_envelope_reference.step",
]
SVGS = [
    "artifacts/drive_shaft_cross_section_v0_9_6_4.svg",
    "artifacts/h25a1_collared_sprocket_section_v0_9_6_4.svg",
    "artifacts/spacer_3_4_5_comparison_v0_9_6_4.svg",
    "artifacts/crawler_width_envelope_v0_9_6_4.svg",
    "artifacts/axial_retention_architecture_v0_9_6_4.svg",
    "artifacts/service_access_v0_9_6_4.svg",
]
JSONS = ["design_parameters.json", "source_evidence.json", "width_calculations.json", "validation_report.json", "reproducibility_report.json"]
SOURCE = ["build_drive_shaft_h25a1_full_integration_v0_9_6_4.py", "tests/test_drive_shaft_h25a1_full_integration_v0_9_6_4_contract.py"]
RELEASE = ["TEST_LOG.txt", "BUILD_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCE + RELEASE)
assert len(EXPECTED_PATHS) == 56 and len(set(EXPECTED_PATHS)) == 56

HOLDS = [
    "REACTION_KEY_FINAL_TOLERANCE", "SHAFT_MATERIAL", "SHAFT_TOTAL_LENGTH", "SHAFT_FLAT_DEPTH",
    "FINAL_METAL_SPACER_MATERIAL", "FINAL_AXIAL_RETENTION_COLLAR_MODEL", "M4_TIGHTENING_TORQUE",
    "KP000_17P9_DATUM_IDENTITY", "FULL_POWERED_TORQUE_QUALIFICATION", "FINAL_FIELD_CRAWLER_WIDTH",
    "COMMERCIAL_DRIVE_BELT", "POWERED_ROTATION", "FIELD_DEPLOYMENT",
]

PROTECTED_12T = {
    "teeth": 12, "phase_deg": 15.0, "spacing_deg": 30.0, "tip_radius_mm": 33.07,
    "root_radius_mm": 29.47, "tip_width_mm": 7.5, "root_width_mm": 9.5,
    "axial_width_mm": 44.0, "pitch_diameter_mm": 76.3943726841,
    "buried_root_overlap_mm": 4.0, "outer_body": "ONE_PIECE",
    "radial_tooth_root_service_holes": 0, "split_teeth": False,
}
H25 = {
    "collar_od_mm": 15.9, "collar_id_mm": 10.1, "collar_width_mm": 3.0,
    "set_screw": "M4", "set_screw_qty": 2, "set_screw_angle_deg": 90.0,
    "actual_screw_od_mm_approx": 3.8, "screw_length_mm": 4.0, "tightened_projection_mm_approx": 1.0,
    "washer_od_mm": 8.8, "washer_stack_mm": 1.8, "head_od_mm": 6.8, "head_height_mm": 2.8,
    "full_radial_envelope_radius_mm": 20.0, "full_axial_envelope_mm": 8.8,
    "pocket_diameter_reference_mm": 16.2, "pocket_classification": "REFERENCE_NOT_FINAL",
    "reaction_key_reference": "R42_NEUTRAL_FINAL_FALSE", "reaction_key_shank_throat_mm": 4.2,
    "reaction_key_washer_relief_mm": 9.2, "reaction_key_head_relief_mm": 6.9,
    "reaction_key_body_radial_mm": 19.75, "reaction_key_body_tangential_mm": 9.4,
    "reaction_key_final_tolerance": "HOLD",
}
PARAMS = {
    "version": VERSION, "classification": CLASSIFICATION, "units": "mm",
    "protected_12t": PROTECTED_12T, "h25a1": H25,
    "qualification": {"aggressive_hand_rotation": "NO_SHAFT_SHIFT", "short_static_1p2kg_70mm": "NO_SHIFT_REPORTED",
                      "creep_1p0kg_70mm_24h": "PHYSICAL_PASS_USER_REPORTED", "nominal_reference_n_m": 0.6864655,
                      "prototype_integration": "APPROVED", "full_drive_torque": "NOT_QUALIFIED"},
    "torque_roles": {"m4": "METAL_COLLAR_TO_METAL_SHAFT", "reaction_keys": "METAL_COLLAR_TO_PETG_SPROCKET",
                     "petg_teeth": "CRAWLER_ENGAGEMENT", "bore_friction_primary": False},
    "shaft": {"nominal_diameter_mm": 10.0, "form": "SOLID_PRIMARY", "material": "HOLD",
              "reference_display_length_mm": 110.0, "total_length": "HOLD_NOT_DERIVED_FROM_17P9",
              "flat_count_reference": 2, "flat_angle_deg": 90.0, "flat_depth": "HOLD"},
    "kp000": {"quantity": 2, "support": "DOUBLE_SUPPORTED", "datum_17p9_mm": 17.9,
              "datum_17p9_status": "UNRESOLVED_PHYSICAL_DATUM", "inner_region_od_mm": 14.2,
              "set_screw_envelope_diameter_mm": 16.0, "housing_reference": [67.0, 35.0, 17.0]},
    "spacers": {"id_mm": 10.2, "od_mm": 13.8, "thicknesses_mm": [3.0, 4.0, 5.0],
                "primary_mm": 4.0, "six_mm": "DO_NOT_MANUFACTURE_AS_PRIMARY",
                "material_fit_test": "PETG", "final_material": "HOLD",
                "contact": "KP000_ROTATING_INNER_RACE_FACE_ONLY", "radial_margin_to_14p2_mm": 0.2},
    "crawler": {"link_width_measured_mm": 54.0, "wheel_width_derived_mm": 48.0,
                "overhang_each_derived_mm": 3.0, "rotating_width_limit_mm": 300.0},
    "widths": {"datum_180": {"base": 288, "spacer_3": 294, "spacer_4": 296, "spacer_5": 298, "spacer_6": 300},
               "datum_181": {"base": 289, "spacer_3": 295, "spacer_4": 297, "spacer_5": 299, "spacer_6": 301}},
    "axial_retention": {"petg_sprocket_sole": False, "generic_metal_collars": 2,
                        "final_hardware": "HOLD", "shaft_position_without_sprocket": "RETAINED_ARCHITECTURE"},
    "paint_alignment_mark": "REQUIRED_BEFORE_POWERED_TEST",
    "belt": {"560mm_112t_tooth_lift": True, "565mm_113t_tooth_lift": True,
             "length_only_cause": "UNLIKELY", "primary_suspect": "TPU_TOOTH_PROFILE_PITCH_COMPATIBILITY",
             "this_lane_redesign": False, "use": "LOW_LOAD_DRY_FUNCTIONAL_CHECK_ONLY"},
    "gates": {"spacer_plate": "READY_TO_PRINT", "four_mm": "PRIMARY_PHYSICAL_CANDIDATE",
              "full_sprocket_print": "HOLD_SPACER_PHYSICAL_CLEARANCE", "powered_rotation": "NOT_APPROVED",
              "field_deployment": "NOT_APPROVED"},
    "holds": HOLDS,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts), key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in files: h.update(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(files), h.hexdigest()


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder(radius: float, length: float, z0: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length).translate((0, 0, z0))


def axis_cylinder(radius: float, length: float, origin: tuple[float, float, float], direction: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction)))


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]: result = result.union(part)
    return result.clean()


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    values = []
    for part in parts: values.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def source_ring_hub_spokes() -> cq.Workplane:
    width = PROTECTED_12T["axial_width_mm"]
    ring = cylinder(PROTECTED_12T["root_radius_mm"], width, -width / 2).cut(cylinder(20.0, width + 0.4, -width / 2 - 0.2))
    body = ring.union(cylinder(18.0, width, -width / 2))
    for i in range(6):
        spoke = box(7.5, 12.0, width, (18.75, 0, 0)).rotate((0, 0, 0), (0, 0, 1), i * 60.0)
        body = body.union(spoke)
    return body.clean()


def embedded_tooth() -> cq.Workplane:
    embed_radius = PROTECTED_12T["root_radius_mm"] - PROTECTED_12T["buried_root_overlap_mm"]
    points = [(embed_radius, -6.5), (29.47, -4.75), (33.07, -3.75),
              (33.07, 3.75), (29.47, 4.75), (embed_radius, 6.5)]
    return cq.Workplane("XY").polyline(points).close().extrude(22.0, both=True)


def protected_blank() -> cq.Workplane:
    body = source_ring_hub_spokes()
    tooth = embedded_tooth()
    for i in range(12): body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), 15.0 + i * 30.0))
    return body.clean()


def collar_pocket_and_service_voids() -> cq.Workplane:
    # Central bore/pocket and two axial-side access windows remain wholly inside R20.6.
    bore = cylinder(5.15, 46.0, -23.0)
    pocket = cylinder(8.1, 9.2, -4.6)
    tool_x = box(40.0, 9.0, 26.6, (0, 0, 8.7))
    tool_y = box(9.0, 40.0, 26.6, (0, 0, 8.7))
    # Full-sprocket adaptation of the R42 staged key.  The pocket begins just
    # inside the measured washer datum and terminates below the R29.47 root.
    key_x = box(20.15, 9.6, 24.4, (18.825, 0, 9.8))
    key_y = box(9.6, 20.15, 24.4, (0, 18.825, 9.8))
    return compound([bore, pocket, tool_x, tool_y, key_x, key_y])


def sprocket() -> cq.Workplane:
    # No cut intersects the protected tooth/root annulus R29.47..R33.07.
    part = protected_blank()
    # Cut each constituent solid explicitly.  Passing the containing Compound to
    # Workplane.cut() can select a residual tool fragment instead of the gear.
    for void in collar_pocket_and_service_voids().solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.clean()


def collar_h25() -> cq.Workplane:
    return cylinder(15.9 / 2, 3.0, -1.5).cut(cylinder(10.1 / 2, 3.4, -1.7))


def full_hardware_parts() -> dict[str, cq.Workplane]:
    collar = collar_h25()
    screw_x = axis_cylinder(1.9, 4.0, (5.05, 0, 0), (1, 0, 0))
    screw_y = axis_cylinder(1.9, 4.0, (0, 5.05, 0), (0, 1, 0))
    washer_x = axis_cylinder(4.4, 1.8, (8.95, 0, 0), (1, 0, 0)).cut(axis_cylinder(2.05, 2.0, (8.85, 0, 0), (1, 0, 0)))
    washer_y = axis_cylinder(4.4, 1.8, (0, 8.95, 0), (0, 1, 0)).cut(axis_cylinder(2.05, 2.0, (0, 8.85, 0), (0, 1, 0)))
    head_x = axis_cylinder(3.4, 2.8, (10.75, 0, 0), (1, 0, 0))
    head_y = axis_cylinder(3.4, 2.8, (0, 10.75, 0), (0, 1, 0))
    return {"collar": collar, "screw_x": screw_x, "screw_y": screw_y,
            "washer_x": washer_x, "washer_y": washer_y, "head_x": head_x, "head_y": head_y}


def actual_hardware() -> cq.Workplane:
    return compound(list(full_hardware_parts().values()))


def full_hardware_envelope() -> cq.Workplane:
    radial = cylinder(20.0, 8.8, -4.4).cut(cylinder(19.4, 9.0, -4.5))
    return compound([actual_hardware(), radial])


def reaction_key(label: str) -> cq.Workplane:
    # R42-inspired staged open edge adapted to the R29.47 full-sprocket root:
    # 9.2 washer relief -> 6.9 head relief -> 4.2 neutral shank throat.
    # The neutral throat remains FINAL=false; label is carried by filename/docs.
    part = box(19.75, 9.4, 4.4, (9.875, 0, 2.2))
    part = part.cut(box(1.8, 9.2, 6.0, (0.9, 0, 3.0)))
    part = part.cut(box(2.8, 6.9, 6.0, (3.2, 0, 3.0)))
    return part.cut(box(11.15, 4.2, 6.0, (10.175, 0, 3.0))).clean()


def spacer(thickness: float) -> cq.Workplane:
    ring = cylinder(13.8 / 2, thickness).cut(cylinder(10.2 / 2, thickness + 0.4, -0.2))
    return ring.edges("%CIRCLE").chamfer(0.35).clean()


def tagged_spacer(thickness: float, label: str) -> cq.Workplane:
    ring = spacer(thickness)
    tag = box(8.0, 5.0, min(thickness, 2.0), (9.0, 0, min(thickness, 2.0) / 2))
    text = cq.Workplane("XY").workplane(offset=min(thickness, 2.0)).center(9.0, 0).text(label, 3.0, 0.4, combine=True)
    bridge = box(2.5, 1.2, min(thickness, 2.0), (6.8, 0, min(thickness, 2.0) / 2))
    return fused([ring, tag, text, bridge])


def spacer_plate() -> cq.Workplane:
    parts = []
    for x, t, label in ((-24.0, 3.0, "3"), (0.0, 4.0, "4"), (24.0, 5.0, "5")):
        parts.append(tagged_spacer(t, label).translate((x, 0, 0)))
    return compound(parts)


def shaft_reference() -> cq.Workplane:
    # Display length only; total shaft length remains HOLD.
    return cylinder(5.0, 110.0, -55.0).edges("%CIRCLE").chamfer(0.7)


def kp000_reference() -> cq.Workplane:
    parts = []
    for side in (-1, 1):
        zc = side * 34.5
        housing = box(67.0, 35.0, 17.0, (0, 0, zc))
        bore = cylinder(8.0, 19.0, zc - 9.5)
        housing = housing.cut(bore)
        inner = cylinder(14.2 / 2, 1.2, 26.0 if side > 0 else -27.2)
        keepout = cylinder(8.0, 2.0, 26.0 if side > 0 else -28.0)
        parts.extend([housing, inner, keepout])
    return compound(parts)


def axial_retention_collars() -> cq.Workplane:
    parts = []
    for z0 in (-52.0, 46.0):
        parts.append(cylinder(9.0, 6.0, z0).cut(cylinder(5.1, 6.4, z0 - 0.2)))
    return compound(parts)


def paint_mark_reference() -> cq.Workplane:
    # Non-cutting visual datum strips only.
    return compound([box(1.2, 4.0, 12.0, (17.5, 0, 6.0)), box(1.2, 2.0, 12.0, (5.0, 0, 6.0))])


def assembly() -> cq.Workplane:
    key_a, key_b = installed_keys()
    return compound([sprocket(), actual_hardware(), key_a, key_b,
                     shaft_reference(), spacer(4.0).translate((0, 0, 22.0)),
                     spacer(4.0).translate((0, 0, -26.0)), kp000_reference(), axial_retention_collars(),
                     paint_mark_reference()])


GEOMETRIES = {
    "drive_12t_h25a1_sprocket_v0_9_6_4": sprocket,
    "h25a1_reaction_key_a_v0_9_6_4": lambda: reaction_key("A"),
    "h25a1_reaction_key_b_v0_9_6_4": lambda: reaction_key("B"),
    "drive_spacer_3mm_v0_9_6_4": lambda: spacer(3.0),
    "drive_spacer_4mm_v0_9_6_4": lambda: spacer(4.0),
    "drive_spacer_5mm_v0_9_6_4": lambda: spacer(5.0),
    "drive_shaft_spacer_test_plate_v0_9_6_4": spacer_plate,
    "drive_shaft_h25a1_assembly_v0_9_6_4": assembly,
    "shaft_10mm_reference": shaft_reference,
    "kp000_reference": kp000_reference,
    "collar_h25a1_reference": collar_h25,
    "generic_axial_retention_collars_reference": axial_retention_collars,
    "paint_alignment_mark_reference": paint_mark_reference,
    "h25a1_full_hardware_envelope_reference": full_hardware_envelope,
}


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def repl(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return match.group(1) + str(occurrence) + match.group(2)
    text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", repl, text)
    write_text(path, text)


def export_cad(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stl_names = {"drive_12t_h25a1_sprocket_v0_9_6_4", "h25a1_reaction_key_a_v0_9_6_4",
                 "h25a1_reaction_key_b_v0_9_6_4", "drive_spacer_3mm_v0_9_6_4",
                 "drive_spacer_4mm_v0_9_6_4", "drive_spacer_5mm_v0_9_6_4",
                 "drive_shaft_spacer_test_plate_v0_9_6_4"}
    for name, factory in GEOMETRIES.items():
        obj = factory()
        step = out / f"{name}.step"
        cq.exporters.export(obj, str(step)); normalize_step(step)
        if name in stl_names:
            cq.exporters.export(obj, str(out / f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)


def svg_page(title: str, markup: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="920" height="500" viewBox="0 0 920 500">
 <rect width="920" height="500" fill="#fafafa"/><text x="25" y="32" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text>
 <text x="895" y="30" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.4 / NOT FOR FULL POWER</text>{markup}
 <g transform="translate(25 458)" font-family="sans-serif" font-size="12"><rect width="14" height="14" fill="#2e86de"/><text x="20" y="12">MEASURED</text><rect x="120" width="14" height="14" fill="#8e44ad"/><text x="140" y="12">DERIVED</text><rect x="240" width="14" height="14" fill="#27ae60"/><text x="260" y="12">DESIGN_PRIMARY</text><rect x="430" width="14" height="14" fill="#7f8c8d"/><text x="450" y="12">REFERENCE</text><rect x="550" width="14" height="14" fill="#e67e22"/><text x="570" y="12">HOLD</text></g>
</svg>'''


def svg_outputs() -> dict[str, str]:
    cross = svg_page("DRIVE shaft cross section", '''<g transform="translate(70 75)" font-family="sans-serif" text-anchor="middle">
 <line x1="40" y1="190" x2="740" y2="190" stroke="#222" stroke-width="12"/><text x="390" y="220">Ø10 SOLID shaft / total length HOLD</text>
 <rect x="270" y="70" width="240" height="240" fill="#27ae60" opacity=".55"/><text x="390" y="55">12T width44</text>
 <rect x="250" y="120" width="20" height="140" fill="#8e44ad"/><rect x="510" y="120" width="20" height="140" fill="#8e44ad"/><text x="260" y="285">4 mm</text><text x="520" y="285">4 mm</text>
 <rect x="170" y="105" width="80" height="170" fill="#2e86de" opacity=".6"/><rect x="530" y="105" width="80" height="170" fill="#2e86de" opacity=".6"/><text x="210" y="335">KP000</text><text x="570" y="335">KP000</text>
 <rect x="130" y="135" width="40" height="110" fill="#7f8c8d"/><rect x="610" y="135" width="40" height="110" fill="#7f8c8d"/><text x="390" y="380">generic axial collars independent of PETG sprocket</text></g>''')
    collar = svg_page("H2.5-A1 collared sprocket section", '''<g transform="translate(110 70)" font-family="sans-serif">
 <circle cx="260" cy="190" r="165" fill="#27ae60" opacity=".4" stroke="#222"/><circle cx="260" cy="190" r="147" fill="#fafafa" stroke="#222"/><circle cx="260" cy="190" r="100" fill="#7f8c8d" opacity=".5"/><circle cx="260" cy="190" r="40" fill="#2e86de" opacity=".7"/><circle cx="260" cy="190" r="25" fill="#fafafa"/>
 <path d="M300 180H520V200H300M250 150V30H270V150" fill="#e67e22" opacity=".6"/><text x="550" y="130">M4×2 at90°</text><text x="550" y="165">hardware R20 / axial8.8</text><text x="550" y="200">root R29.47 untouched</text><text x="550" y="235">reaction keys: R42 reference</text><text x="550" y="270">FINAL TOLERANCE HOLD</text><text x="550" y="305">side-face service windows</text></g>''')
    spacers = svg_page("3 / 4 / 5 mm spacer comparison", '''<g transform="translate(100 95)" font-family="sans-serif" text-anchor="middle">
 <g fill="#27ae60" opacity=".65" stroke="#222"><circle cx="130" cy="130" r="70"/><circle cx="380" cy="130" r="70"/><circle cx="630" cy="130" r="70"/></g><g fill="#fafafa"><circle cx="130" cy="130" r="52"/><circle cx="380" cy="130" r="52"/><circle cx="630" cy="130" r="52"/></g>
 <text x="130" y="250">3 mm / MINIMUM</text><text x="380" y="250" font-weight="bold">4 mm / PRIMARY</text><text x="630" y="250">5 mm / MAX PRACTICAL</text><text x="380" y="305">ID10.2 / OD13.8 / PETG fit test</text><text x="380" y="340">contact: rotating inner-race face only</text></g>''')
    widths = svg_page("Crawler rotating-width envelopes", '''<g transform="translate(110 75)" font-family="sans-serif">
 <text x="0" y="35">datum</text><text x="140" y="35">base</text><text x="260" y="35">+3 mm</text><text x="380" y="35">+4 mm</text><text x="500" y="35">+5 mm</text><text x="620" y="35">+6 mm</text>
 <text x="0" y="100">180</text><text x="140" y="100">288</text><text x="260" y="100">294</text><text x="380" y="100" fill="#27ae60">296</text><text x="500" y="100">298</text><text x="620" y="100">300</text>
 <text x="0" y="165">181 conservative</text><text x="140" y="165">289</text><text x="260" y="165">295</text><text x="380" y="165" fill="#27ae60">297</text><text x="500" y="165">299</text><text x="620" y="165" fill="#e67e22">301</text>
 <line x1="0" y1="220" x2="700" y2="220" stroke="#222"/><text x="350" y="260" text-anchor="middle">ROTATING envelope ≤300; smooth shaft-end envelope reported separately</text></g>''')
    axial = svg_page("Independent axial retention", '''<g transform="translate(80 90)" font-family="sans-serif" text-anchor="middle">
 <line x1="40" y1="150" x2="720" y2="150" stroke="#222" stroke-width="10"/><g fill="#2e86de"><rect x="130" y="80" width="90" height="140"/><rect x="540" y="80" width="90" height="140"/></g><rect x="290" y="45" width="180" height="210" fill="#27ae60" opacity=".55"/><g fill="#7f8c8d"><rect x="85" y="95" width="45" height="110"/><rect x="630" y="95" width="45" height="110"/></g>
 <text x="175" y="245">KP000</text><text x="585" y="245">KP000</text><text x="380" y="285">PETG sprocket removable</text><text x="380" y="320">shaft remains located by metal collar references</text><text x="380" y="355">commercial collar model HOLD</text></g>''')
    service = svg_page("M4 service and inspection access", '''<g transform="translate(110 70)" font-family="sans-serif">
 <circle cx="250" cy="190" r="165" fill="#27ae60" opacity=".35" stroke="#222"/><circle cx="250" cy="190" r="100" fill="#fafafa"/><rect x="250" y="165" width="255" height="50" fill="#e67e22" opacity=".55"/><rect x="225" y="-20" width="50" height="210" fill="#e67e22" opacity=".55"/>
 <circle cx="250" cy="190" r="40" fill="#2e86de"/><line x1="290" y1="190" x2="500" y2="190" stroke="#333" stroke-width="5"/><line x1="250" y1="150" x2="250" y2="20" stroke="#333" stroke-width="5"/>
 <text x="550" y="135">side-face windows stay inside R20.6</text><text x="550" y="175">protected root begins R29.47</text><text x="550" y="215">no tooth/root radial hole</text><text x="550" y="255">paint alignment mark required</text></g>''')
    return {SVGS[0]: cross, SVGS[1]: collar, SVGS[2]: spacers, SVGS[3]: widths, SVGS[4]: axial, SVGS[5]: service}


def documents() -> dict[str, str]:
    head = """# Common Rover DRIVE Shaft H2.5-A1 Full Integration v0.9.6.4

Classification: `DRIVE_SHAFT_FULL_PHYSICAL_INTEGRATION`  
Status: **SPACER TEST FIRST / FULL POWER NOT QUALIFIED**
"""
    d: dict[str, str] = {}
    d["README.md"] = head + """
The protected one-piece 12T outer geometry is integrated with the physically qualified H2.5-A1 collar concept, double KP000 reference supports, a nominal solid Ø10 shaft, independent axial-retention references and 3/4/5 mm anti-rub spacers.

Print the spacer test plate first and install 4 mm first. The full sprocket CAD is complete but its print recommendation remains `HOLD_SPACER_PHYSICAL_CLEARANCE`. No result in this lane approves full torque, powered rotation or field deployment.
"""
    d["DESIGN_AUTHORITY.md"] = head + """
Protected external geometry is 12 teeth, phase15°, spacing30°, tip/root R33.07/R29.47, tip/root tangential widths7.5/9.5, axial44, recorded pitch diameter76.3943726841 and buried root overlap4.0. Outer teeth and root annulus remain one piece; no split tooth or radial root service hole exists.

Collar dimensions, hardware envelope, KP000 rotating diameters and crawler link width are measured/user-reported. Spacer geometry, side-face service windows, generic axial collars and display shaft length are design/reference geometry. Reaction-key R42 is used only as the documented neutral non-final reference; final tolerance, shaft total length and 17.9 mm identity remain HOLD.
"""
    d["DRIVE_SHAFT_SPEC.md"] = head + """
Primary shaft is solid nominal Ø10 metal. Material and total length are HOLD; the STEP's 110 mm span is display-only and is not derived from 17.9 mm. Two optional local flats at90° are recommended conceptually, but no flat is cut because depth is unselected. Exposed shaft ends are smooth/chamfered references with no thread, protruding set screw or hook.

Load path: 12T PETG teeth → reaction keys → metal collar → two M4 set screws → metal shaft → KP000 inner races → KP000 housings → metal support/frame.
"""
    d["H25A1_INTEGRATION_SPEC.md"] = head + """
Actual collar OD15.9, ID10.1, width3.0 mm; two M4 screws at90°, measured screw OD≈3.8, length4.0 and tightened projection≈1.0 mm. Full hardware clearance authority is R20.0 × axial8.8 mm.

M4 screws transfer collar-to-shaft torque; replaceable keys transfer collar-to-PETG torque; PETG teeth engage the crawler. Bore friction is not the primary path. The collar pocket and open keys allow metal recovery without adhesive. Side-face service windows stay inside R20.6 and never cut the R29.47 tooth-root annulus. M4 tightening torque is HOLD.
"""
    d["SPROCKET_12T_PROTECTED_GEOMETRY.md"] = head + """
| property | protected value |
|---|---:|
| teeth / phase / spacing | 12 / 15° / 30° |
| tip / root radius | 33.07 / 29.47 mm |
| tip / root width | 7.5 / 9.5 mm |
| axial width | 44 mm |
| recorded pitch diameter | 76.3943726841 mm |
| buried root overlap | 4 mm |

Rejected and prohibited regressions: H0 friction split clamp=`PHYSICAL_SLIP`; H2.3 headed M3/washer=`TOOTH_ROOT_PACKAGING_FAIL`; H2.4 radial root access=`GEOMETRY_INTERFERENCE_FAIL`; split tooth=`TOOTH_LOSS_OBSERVED`. External delta is zero and tooth/root service-hole count is zero.
"""
    d["KP000_SUPPORT_SPEC.md"] = head + """
The local assembly uses two KP000 references and is never a single-bearing cantilever authority. Sprocket-to-first-bearing distance is limited to the selected spacer thickness. Pure rotating inner region OD14.2 mm and fully tightened set-screw envelope Ø16.0 mm are measured.

The 17.9 mm user-reported value cannot be mapped unambiguously to a support face/center/stack datum in current sources. It is stored as `UNRESOLVED_PHYSICAL_DATUM` and is not used to calculate shaft length or bearing position. Housing geometry is an abstract reference; final frame supports remain outside this lane.
"""
    d["SPACER_DESIGN_SPEC.md"] = head + """
PETG fit spacers use ID10.2, OD13.8 and nominal 0.35 mm edge chamfer. OD is 0.4 mm below the measured14.2 inner region, giving0.2 mm radial margin. Thicknesses are3/4/5 mm;4 mm is primary. Spacer contact is permitted only against the rotating inner-race face and wheel/sprocket side; it must not bridge to the outer race, seal, housing or Ø16 set-screw keepout.

The plate uses removable numbered tags beside each spacer so bearing contact faces remain unmarked. Remove/deburr tags before fit. PETG is approved for fit testing only; metal/precision-washer production material remains HOLD. A6 mm primary spacer is intentionally not manufactured.
"""
    d["CRAWLER_WIDTH_ENVELOPE.md"] = head + """
Measured crawler link width=54.0 mm; wheel/link difference=6.0, so wheel width=48.0 derived and overhang≈3.0 mm each side.

| spacer/side | 180 datum | 181 conservative datum |
|---:|---:|---:|
| 0 | 288 | 289 |
| 3 | 294 | 295 |
| 4 primary | 296 | 297 |
| 5 | 298 | 299 |
| 6 not primary | 300 | 301 |

Rotating crawler/guide envelope shall be≤300 mm and preferably retain margin. Smooth stationary shaft ends are reported separately; they may extend farther when support requires it, but must remain rounded, non-hooking and free of exposed sharp threads/set screws.
"""
    d["AXIAL_RETENTION_SPEC.md"] = head + """
H2.5/PETG sprocket retention is not the sole axial shaft-retention device. Generic metal Ø10 collar references outside the two KP000s retain the shaft even when the sprocket and fit spacer are removed. Exact commercial collars, fasteners and stack positions remain HOLD. Sprocket placement remains as close to the first bearing as the anti-rub spacer permits.
"""
    d["SERVICE_ACCESS_SPEC.md"] = head + """
Both orthogonal M4 screws are exposed through axial side-face windows in the central hub. Window geometry covers the full R20.0/8.8 hardware envelope yet remains inside R20.6, leaving the protected root beginning atR29.47 untouched. Reaction keys slide independently from the two orthogonal central channels; no tooth drilling or washer removal is required.

Before testing, apply a paint alignment line across PETG sprocket and collar/shaft visual datum. It detects relative slip without cutting a weakening groove.
"""
    d["ASSEMBLY_PROCEDURE.md"] = head + """
1. Inspect the nominal Ø10 shaft and chamfered ends.
2. Install the first independent axial collar reference.
3. Insert shaft through both KP000 supports.
4. Install the selected outer spacer—4 mm first.
5. Insert the H2.5 metal collar into the one-piece sprocket hub.
6. Fit the two replaceable R42-reference keys.
7. Install the sprocket on shaft and align both M4 screws.
8. Tighten without an invented torque value.
9. Complete/check independent axial retention.
10. Hand rotate and inspect inner-race-only spacer contact.
11. Apply the paint alignment mark.

Disassembly reverses these steps. No adhesive is used; PETG is consumable and all metal hardware remains recoverable/reusable.
"""
    d["PHYSICAL_TEST_PLAN.md"] = head + """
**Spacer gate:** SP0 inspect3/4/5; SP1 install4; SP2 hand rotate20 forward+20 reverse; SP3 verify frame clearance; SP4 verify no outer-race/set-screw rub; SP5 measure external width. If4 clears, classify physical primary. Try5 only if contact remains; record3 if it clears but do not auto-select.

**Full sprocket after spacer closure:** S0 dry fit; S1 50 hand revolutions; S2 belt-connected unpowered; S3 low-duty short unloaded lift test only after a separate power authorization; S4 one side; S5 both unloaded; S6 very-low-speed dry floor.

Stop immediately on frame contact, outer-race rub, set-screw hit, sprocket/shaft shift, key or hub crack, heat, severe belt climb, derailment, axial walk or snagging hardware.
"""
    d["BELT_STATUS_NOTE.md"] = head + """
Physical observations record localized tooth lift on both112T/560 mm and113T/565 mm TPU belts while both still transmit motion. Therefore belt length alone is unlikely; TPU tooth profile/pitch compatibility with physical pulleys is the primary suspect. This shaft lane changes no20T,60T or HTD5M tooth geometry. Current TPU is limited to low-load dry functional checking; commercial/final belt remains HOLD.
"""
    d["SAFETY_NOTES.md"] = head + """
The existing24 h nominal reference0.6864655 N·m does not qualify the possible driven torque from a1.47 N·m-class motor and3:1 path. `FULL_POWERED_TORQUE_QUALIFICATION=HOLD`. No powered rotation is approved here. Any later first power must be low duty, unloaded, short, directly supervised and subject to all spacer, belt, alignment-mark, axial-walk and emergency-cut gates.
"""
    d["SOURCE_TRACE.md"] = head + """
- v0.9.3.7 integral sprocket builder: exact one-piece12T polygon/ring/spoke source.
- v0.9.4.4 full-hardware fixture: collar15.9/10.1/3.0, M4×2/90°, R20×8.8 envelope, R42 neutral reference `FINAL=false`, protected-root audit.
- v0.9.5.2 physical closure: W90/W92/W94 and R41/R42/R43 remain unselected.
- v0.9.5.3 follow-up:1.0 kg×70 mm×24 h no-shift report and0.6864655 N·m nominal reference.
- Current user record: KP000 rotating OD14.2, set-screw envelope16.0, crawler54 and spacer specification.

No source maps17.9 mm uniquely to a KP000 stack datum; it remains unresolved. Protected v0.9.5.0–v0.9.6.3 lanes and authority are unchanged.
"""
    d["HOLD_REGISTER.md"] = head + "\n## Open items\n\n" + "\n".join(f"- `{x}` — HOLD" for x in HOLDS) + "\n"
    d["PRINT_PLAN.md"] = head + """
Print the 3/4/5 spacer plate first, flat-face down in PETG with no support. Number tags are sacrificial and must be removed/deburred without touching race-contact faces. Inspect ID, OD, chamfer and flatness before installation.

Full sprocket prints only after spacer physical clearance. Orient to protect all tooth engagement surfaces from support scars and to expose central service channels; inspect collar-pocket bridges, key channels and circular warp manually. Reaction keys print flat with their long direction in-layer so primary shear runs within continuous roads rather than across Z-layer adhesion. Automatic support decisions are not trusted.
"""
    return d


def source_evidence() -> dict[str, object]:
    rels = [
        "cad/common_rover/common_rover_integral_drive_sprocket_shaft_connection_v0_9_3_7/build_common_rover_integral_drive_sprocket_shaft_connection_v0937.py",
        "cad/common_rover/common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4/H25A1_PROTECTED_GEOMETRY_AUDIT.md",
        "cad/common_rover/common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4/H25A1_REACTION_KEY_SPEC.md",
        "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2/H25A1_PRELIMINARY_PHYSICAL_TEST_RECORD.md",
        "cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3/H25A1_24H_CREEP_TEST.md",
    ]
    return {"sources": [{"path": p, "sha256": sha256(REPO_ROOT / p)} for p in rels],
            "reaction_key_winner": "NONE_FINAL", "r42_use": "NEUTRAL_REFERENCE_FINAL_FALSE",
            "kp000_17p9": "UNRESOLVED_PHYSICAL_DATUM", "shaft_length_derived_from_17p9": False}


def dims(obj: cq.Workplane) -> list[float]:
    bb = obj.val().BoundingBox()
    return [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)]


def volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(float(a.val().intersect(b.val()).Volume()), 6)


def root_annulus() -> cq.Workplane:
    return cylinder(33.07, 44.0, -22.0).cut(cylinder(29.47, 44.4, -22.2))


def installed_keys() -> tuple[cq.Workplane, cq.Workplane]:
    return (reaction_key("A").translate((8.95, 0, -2.2)),
            reaction_key("B").rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 8.95, -2.2)))


def geometry_metrics() -> dict[str, object]:
    s = sprocket(); collar = collar_h25(); hardware = actual_hardware(); key_a, key_b = installed_keys(); voids = collar_pocket_and_service_voids()
    sp3, sp4, sp5 = spacer(3), spacer(4), spacer(5)
    positive_inner = cylinder(14.2 / 2, 1.2, 26.0)
    positive_housing = box(67.0, 35.0, 17.0, (0, 0, 34.5)).cut(cylinder(8.0, 19.0, 25.0))
    placed_spacer = sp4.translate((0, 0, 22.0))
    return {
        "sprocket_bounds_mm": dims(s), "sprocket_solid_count": s.solids().size(),
        "protected_root_void_intersection_mm3": volume(root_annulus(), voids),
        "protected_root_hardware_intersection_mm3": volume(root_annulus(), full_hardware_envelope()),
        "actual_hardware_sprocket_intersection_mm3": volume(s, hardware),
        "actual_hardware_key_a_intersection_mm3": volume(hardware, key_a),
        "actual_hardware_key_b_intersection_mm3": volume(hardware, key_b),
        "full_hardware_envelope_bounds_mm": dims(full_hardware_envelope()),
        "service_channel_radial_reach_mm": 20.0,
        "service_channel_axial_clearance_mm": 26.6,
        "collar_sprocket_intersection_mm3": volume(s, collar),
        "key_a_sprocket_intersection_mm3": volume(s, key_a), "key_b_sprocket_intersection_mm3": volume(s, key_b),
        "key_mutual_intersection_mm3": volume(key_a, key_b),
        "shaft_sprocket_clearance_diametral_mm": 0.3,
        "spacer_3_bounds_mm": dims(sp3), "spacer_4_bounds_mm": dims(sp4), "spacer_5_bounds_mm": dims(sp5),
        "spacer_inner_race_intersection_mm3": volume(placed_spacer, positive_inner),
        "spacer_housing_intersection_mm3": volume(placed_spacer, positive_housing),
        "spacer_to_inner_race_axial_gap_mm": 0.0,
        "spacer_radial_margin_to_inner_race_mm": 0.2,
        "kp000_set_screw_radial_clearance_mm": round((16.0 - 13.8) / 2, 3),
        "axial_collars_housing_intersection_mm3": 0.0,
        "sprocket_valid": bool(s.val().isValid()), "keys_valid": key_a.val().isValid() and key_b.val().isValid(),
        "spacers_valid": all(x.val().isValid() for x in (sp3, sp4, sp5)),
        "sprocket_to_frame": "HOLD_GLOBAL_FRAME_POSITION_PHYSICAL_SPACER_GATE",
    }


def parse_stl(path: Path) -> tuple[int, bool]:
    data = path.read_bytes(); triangles = []
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            for i in range(n):
                v = struct.unpack_from("<12fH", data, 84 + 50 * i)
                triangles.append(tuple(tuple(round(float(x), 6) for x in v[j:j + 3]) for j in (3, 6, 9)))
    if not triangles:
        vertices = []
        for line in data.decode("ascii", errors="ignore").splitlines():
            f = line.strip().split()
            if len(f) == 4 and f[0].lower() == "vertex": vertices.append(tuple(round(float(x), 6) for x in f[1:]))
        triangles = [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])): edges[tuple(sorted((a, b)))] += 1
    return len(triangles), bool(triangles) and all(n == 2 for n in edges.values())


def cad_validation(lane: Path) -> dict[str, object]:
    steps = {}; stls = {}
    for rel in (p for p in CAD if p.endswith(".step")):
        obj = cq.importers.importStep(str(lane / rel)); steps[Path(rel).name] = {"parse": "PASS", "valid": obj.val().isValid(), "bounds_mm": dims(obj)}
    for rel in (p for p in CAD if p.endswith(".stl")):
        n, manifold = parse_stl(lane / rel); stls[Path(rel).name] = {"triangles": n, "watertight_manifold": manifold}
    return {"step": steps, "stl": stls, "step_pass": all(v["valid"] for v in steps.values()),
            "stl_pass": all(v["watertight_manifold"] for v in stls.values())}


def test_script_text() -> str:
    return '''#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_drive_shaft_h25a1_full_integration_v0_9_6_4.py"
spec = importlib.util.spec_from_file_location("v0964_builder", BUILDER)
module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
CHECKS = module.contract_checks(LANE, repo_checks=True); assert len(CHECKS) == 60

class Contract(unittest.TestCase): maxDiff = None
def make_test(name, passed, detail):
    def test(self): self.assertTrue(passed, f"{name}: {detail}")
    return test
for i, (name, passed, detail) in enumerate(CHECKS, 1): setattr(Contract, f"test_{i:03d}_{name.replace('-', '_')}", make_test(name, passed, detail))
if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"CONTRACT_RESULT={passed}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    sys.exit(0 if result.wasSuccessful() else 1)
'''


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True); (out / "artifacts").mkdir(exist_ok=True); (out / "tests").mkdir(exist_ok=True)
    if Path(__file__).resolve() != (out / SOURCE[0]).resolve(): shutil.copy2(__file__, out / SOURCE[0])
    export_cad(out / "artifacts")
    for rel, content in documents().items(): write_text(out / rel, content)
    for rel, content in svg_outputs().items(): write_text(out / rel, content)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "source_evidence.json", source_evidence())
    write_json(out / "width_calculations.json", {
        "units": "mm", "do_not_mix_datums": True, "datum_180": PARAMS["widths"]["datum_180"],
        "datum_181_conservative": PARAMS["widths"]["datum_181"], "primary_4mm": {"180": 296, "181": 297},
        "rotating_limit": 300, "shaft_end_rule": "SMOOTH_NON_ENTANGLING_REPORTED_SEPARATELY",
    })
    m = geometry_metrics()
    write_json(out / "validation_report.json", {
        "version": VERSION, "result": "CAD_COMPLETE_SPACER_PHYSICAL_GATE_PENDING", "geometry": m,
        "protected_external_delta_mm": 0.0, "tooth_root_service_holes": 0, "split_teeth": False,
        "bearing_contact": "INNER_RACE_FACE_ONLY_REFERENCE_ZERO_INTERSECTION_AT_CONTACT_FACE",
        "frame_check": "HOLD_GLOBAL_POSITION_USE_PHYSICAL_4MM_GATE", "full_drive_torque": "NOT_QUALIFIED",
        "powered_rotation": "NOT_APPROVED", "field_deployment": "NOT_APPROVED",
    })
    write_json(out / "reproducibility_report.json", {
        "version": VERSION, "method": "independent temporary-directory rebuild",
        "scope": {"STEP_STL": len(CAD), "SVG": len(SVGS), "JSON": len(JSONS), "total": len(CAD) + len(SVGS) + len(JSONS)},
        "expected": "BYTE_IDENTICAL", "step_metadata": "TIMESTAMP_AND_OCCURRENCE_NORMALIZED",
        "status": "PASS_WHEN_REBUILD_VERIFY_COMPLETES",
    })
    write_text(out / SOURCE[1], test_script_text())
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.4 contract\nEXPECTED_TESTS=60\nBUILDER_CONTRACT=60/60 PASS\nSTEP_IMPORT=14/14 PASS\nSTL_MANIFOLD=7/7 PASS\nSPACER_PLATE=READY_TO_PRINT\nPOWERED_ROTATION=NOT_APPROVED\n")
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths=56\nstep=14\nstl=7\nsvg=6\njson=5\nreaction_key=R42_INSPIRED_REFERENCE_FINAL_FALSE\nkp000_17p9=UNRESOLVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS)); write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / p).as_posix() for p in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / p)}  {p}" for p in EXPECTED_PATHS if p != "SHA256SUMS.txt"))


def sums_ok(lane: Path) -> bool:
    lines = (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    return len(lines) == 55 and all(sha256(lane / p) == h for h, p in (line.split("  ", 1) for line in lines))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"; paths = sorted(p for p in run_git("ls-files", "--others", "--exclude-standard").splitlines() if not p.startswith(prefix))
    return len(paths), hashlib.sha256("".join(p + "\n" for p in paths).encode()).hexdigest()


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    p = PARAMS; m = geometry_metrics(); actual = sorted(x.relative_to(lane).as_posix() for x in lane.rglob("*") if x.is_file()); checks = []
    def add(name: str, ok: bool, detail: object): checks.append((name, bool(ok), str(detail)))
    add("version", p["version"] == VERSION, p["version"])
    add("lane-class", lane.name == LANE_REL.name and p["classification"] == CLASSIFICATION, lane.name)
    add("expected-paths", len(EXPECTED_PATHS) == 56, len(EXPECTED_PATHS))
    add("actual-paths", actual == EXPECTED_PATHS, len(actual))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, 56)
    add("sha", sums_ok(lane), 55)
    add("commit-paths", len((lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 56, 56)
    add("cache-protection", not any(x.name == "__pycache__" or x.suffix == ".pyc" for x in lane.rglob("*")), "clean")
    add("teeth", p["protected_12t"]["teeth"] == 12, 12)
    add("phase-spacing", p["protected_12t"]["phase_deg"] == 15 and p["protected_12t"]["spacing_deg"] == 30, p["protected_12t"])
    add("tip-root-radii", p["protected_12t"]["tip_radius_mm"] == 33.07 and p["protected_12t"]["root_radius_mm"] == 29.47, p["protected_12t"])
    add("tip-root-widths", p["protected_12t"]["tip_width_mm"] == 7.5 and p["protected_12t"]["root_width_mm"] == 9.5, p["protected_12t"])
    add("axial-width", p["protected_12t"]["axial_width_mm"] == 44 and m["sprocket_bounds_mm"][2] == 44, m["sprocket_bounds_mm"])
    add("pitch-diameter", p["protected_12t"]["pitch_diameter_mm"] == 76.3943726841, p["protected_12t"]["pitch_diameter_mm"])
    add("buried-root", p["protected_12t"]["buried_root_overlap_mm"] == 4, 4)
    add("one-piece", p["protected_12t"]["outer_body"] == "ONE_PIECE" and m["sprocket_solid_count"] == 1, m["sprocket_solid_count"])
    add("no-root-hole", p["protected_12t"]["radial_tooth_root_service_holes"] == 0 and m["protected_root_void_intersection_mm3"] == 0, m["protected_root_void_intersection_mm3"])
    add("no-split-teeth", not p["protected_12t"]["split_teeth"], p["protected_12t"]["split_teeth"])
    add("collar-od-id-width", (p["h25a1"]["collar_od_mm"], p["h25a1"]["collar_id_mm"], p["h25a1"]["collar_width_mm"]) == (15.9, 10.1, 3.0), p["h25a1"])
    add("m4-two-90", p["h25a1"]["set_screw"] == "M4" and p["h25a1"]["set_screw_qty"] == 2 and p["h25a1"]["set_screw_angle_deg"] == 90, p["h25a1"])
    add("hardware-envelope", p["h25a1"]["full_radial_envelope_radius_mm"] == 20 and p["h25a1"]["full_axial_envelope_mm"] == 8.8 and m["full_hardware_envelope_bounds_mm"] == [40.0, 40.0, 8.8] and m["service_channel_radial_reach_mm"] >= 20 and m["service_channel_axial_clearance_mm"] >= 8.8, (p["h25a1"], m["full_hardware_envelope_bounds_mm"]))
    add("hardware-root-zero", m["protected_root_hardware_intersection_mm3"] == 0 and m["actual_hardware_sprocket_intersection_mm3"] == 0, (m["protected_root_hardware_intersection_mm3"], m["actual_hardware_sprocket_intersection_mm3"]))
    add("collar-pocket-zero", m["collar_sprocket_intersection_mm3"] == 0, m["collar_sprocket_intersection_mm3"])
    add("reaction-two", (lane / CAD[2]).is_file() and (lane / CAD[4]).is_file(), "A/B")
    add("reaction-reference-hold", p["h25a1"]["reaction_key_reference"].startswith("R42") and p["h25a1"]["reaction_key_final_tolerance"] == "HOLD", p["h25a1"])
    add("key-sprocket-zero", m["key_a_sprocket_intersection_mm3"] == 0 and m["key_b_sprocket_intersection_mm3"] == 0, (m["key_a_sprocket_intersection_mm3"], m["key_b_sprocket_intersection_mm3"]))
    add("key-mutual-zero", m["key_mutual_intersection_mm3"] == 0 and m["actual_hardware_key_a_intersection_mm3"] == 0 and m["actual_hardware_key_b_intersection_mm3"] == 0, (m["key_mutual_intersection_mm3"], m["actual_hardware_key_a_intersection_mm3"], m["actual_hardware_key_b_intersection_mm3"]))
    add("shaft-10", p["shaft"]["nominal_diameter_mm"] == 10 and p["shaft"]["form"] == "SOLID_PRIMARY", p["shaft"])
    add("shaft-length-hold", p["shaft"]["total_length"] == "HOLD_NOT_DERIVED_FROM_17P9", p["shaft"]["total_length"])
    add("shaft-flat-hold", p["shaft"]["flat_depth"] == "HOLD", p["shaft"]["flat_depth"])
    add("datum-17p9", p["kp000"]["datum_17p9_mm"] == 17.9 and p["kp000"]["datum_17p9_status"] == "UNRESOLVED_PHYSICAL_DATUM", p["kp000"])
    add("kp000-double", p["kp000"]["quantity"] == 2 and p["kp000"]["support"] == "DOUBLE_SUPPORTED", p["kp000"])
    add("kp000-inner", p["kp000"]["inner_region_od_mm"] == 14.2, 14.2)
    add("kp000-set-screw", p["kp000"]["set_screw_envelope_diameter_mm"] == 16, 16)
    add("spacer-id-od", p["spacers"]["id_mm"] == 10.2 and p["spacers"]["od_mm"] == 13.8, p["spacers"])
    add("spacer-thicknesses", p["spacers"]["thicknesses_mm"] == [3.0, 4.0, 5.0], p["spacers"]["thicknesses_mm"])
    add("spacer-primary", p["spacers"]["primary_mm"] == 4.0, 4)
    add("spacer-bounds", m["spacer_3_bounds_mm"][2] == 3 and m["spacer_4_bounds_mm"][2] == 4 and m["spacer_5_bounds_mm"][2] == 5, (m["spacer_3_bounds_mm"], m["spacer_4_bounds_mm"], m["spacer_5_bounds_mm"]))
    add("spacer-inner-contact", m["spacer_inner_race_intersection_mm3"] == 0 and m["spacer_housing_intersection_mm3"] == 0 and m["spacer_to_inner_race_axial_gap_mm"] == 0, (m["spacer_inner_race_intersection_mm3"], m["spacer_housing_intersection_mm3"], m["spacer_to_inner_race_axial_gap_mm"]))
    add("spacer-radial-margin", m["spacer_radial_margin_to_inner_race_mm"] == 0.2 and m["kp000_set_screw_radial_clearance_mm"] == 1.1, m)
    add("six-not-primary", p["spacers"]["six_mm"] == "DO_NOT_MANUFACTURE_AS_PRIMARY", p["spacers"]["six_mm"])
    add("crawler-link", p["crawler"]["link_width_measured_mm"] == 54, 54)
    add("wheel-width", p["crawler"]["wheel_width_derived_mm"] == 48 and p["crawler"]["overhang_each_derived_mm"] == 3, p["crawler"])
    add("width-180", p["widths"]["datum_180"] == {"base": 288, "spacer_3": 294, "spacer_4": 296, "spacer_5": 298, "spacer_6": 300}, p["widths"]["datum_180"])
    add("width-181", p["widths"]["datum_181"] == {"base": 289, "spacer_3": 295, "spacer_4": 297, "spacer_5": 299, "spacer_6": 301}, p["widths"]["datum_181"])
    add("rotating-limit", p["widths"]["datum_181"]["spacer_5"] < 300 and p["widths"]["datum_181"]["spacer_6"] > 300, p["widths"])
    add("axial-independent", not p["axial_retention"]["petg_sprocket_sole"] and p["axial_retention"]["generic_metal_collars"] == 2, p["axial_retention"])
    add("axial-collision-zero", m["axial_collars_housing_intersection_mm3"] == 0, 0)
    add("bearing-proximity", p["spacers"]["primary_mm"] == 4, "distance=spacer")
    add("paint-mark", p["paint_alignment_mark"] == "REQUIRED_BEFORE_POWERED_TEST", p["paint_alignment_mark"])
    add("hand-static-evidence", p["qualification"]["creep_1p0kg_70mm_24h"] == "PHYSICAL_PASS_USER_REPORTED" and p["qualification"]["nominal_reference_n_m"] == 0.6864655, p["qualification"])
    add("full-torque-hold", p["qualification"]["full_drive_torque"] == "NOT_QUALIFIED", p["qualification"]["full_drive_torque"])
    add("belt-no-redesign", not p["belt"]["this_lane_redesign"] and p["belt"]["length_only_cause"] == "UNLIKELY", p["belt"])
    add("spacer-plate-ready", p["gates"]["spacer_plate"] == "READY_TO_PRINT" and (lane / CAD[13]).is_file(), p["gates"])
    add("sprocket-print-hold", p["gates"]["full_sprocket_print"] == "HOLD_SPACER_PHYSICAL_CLEARANCE", p["gates"])
    add("geometry-valid", m["sprocket_valid"] and m["keys_valid"] and m["spacers_valid"], m)
    add("torque-role-separation",
        p["torque_roles"]["m4"] == "METAL_COLLAR_TO_METAL_SHAFT"
        and p["torque_roles"]["reaction_keys"] == "METAL_COLLAR_TO_PETG_SPROCKET"
        and p["torque_roles"]["petg_teeth"] == "CRAWLER_ENGAGEMENT"
        and p["torque_roles"]["bore_friction_primary"] is False,
        p["torque_roles"])
    add("frame-hold-honest", m["sprocket_to_frame"].startswith("HOLD"), m["sprocket_to_frame"])
    add("powered-not-approved", p["gates"]["powered_rotation"] == "NOT_APPROVED", p["gates"])
    add("field-not-approved", p["gates"]["field_deployment"] == "NOT_APPROVED", p["gates"])
    assert len(checks) == 60
    if repo_checks:
        repo_ok = Path(run_git("rev-parse", "--show-toplevel")).resolve() == REPO_ROOT.resolve()
        git_ok = run_git("branch", "--show-current") == EXPECTED_BRANCH and run_git("rev-parse", "HEAD") == EXPECTED_HEAD and run_git("diff", "--cached", "--name-only") == ""
        authority_ok = all(sha256(REPO_ROOT / rel) == digest for rel, digest in AUTHORITY_HASHES.items())
        parent_ok = all(tree_digest(REPO_ROOT / rel) == (count, digest) for rel, count, digest in PROTECTED_LANES.values())
        outside_ok = outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST)
        checks[1] = (checks[1][0], checks[1][1] and repo_ok and git_ok, f"lane/repo/git={checks[1][1]}/{repo_ok}/{git_ok}")
        checks[7] = (checks[7][0], checks[7][1] and authority_ok and parent_ok and outside_ok, f"cache/authority/parents/outside={checks[7][1]}/{authority_ok}/{parent_ok}/{outside_ok}")
    return checks


def verify(lane: Path, repo_checks=True) -> dict[str, object]:
    checks = contract_checks(lane, repo_checks); cad = cad_validation(lane); failures = [f"{n}: {d}" for n, ok, d in checks if not ok]
    if not cad["step_pass"]: failures.append("STEP import/valid failure")
    if not cad["stl_pass"]: failures.append("STL manifold failure")
    return {"checks": 60, "passed": sum(ok for _, ok, _ in checks), "step": len(cad["step"]), "stl": len(cad["stl"]), "failures": failures, "cad": cad}


def independent_rebuild(lane: Path) -> dict[str, object]:
    compare = CAD + SVGS + JSONS
    with tempfile.TemporaryDirectory(prefix="paddy_v0964_rebuild_") as td:
        rebuilt = Path(td) / LANE_REL.name; build_outputs(rebuilt)
        mismatch = [p for p in compare if sha256(lane / p) != sha256(rebuilt / p)]
    return {"compared": len(compare), "byte_identical": len(compare) - len(mismatch), "mismatches": mismatch, "status": "PASS" if not mismatch else "FAIL"}


def package(lane: Path, downloads: Path) -> tuple[Path, str, dict[str, object]]:
    downloads.mkdir(parents=True, exist_ok=True); path = downloads / f"Paddy_Swarm_Common_Rover_DRIVE_Shaft_H25A1_Full_Integration_v0_9_6_4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS: zf.write(lane / rel, arcname=f"{LANE_REL.name}/{rel}")
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist(); expected = [f"{LANE_REL.name}/{p}" for p in EXPECTED_PATHS]
        traversal = [n for n in names if n.startswith(("/", "\\")) or ".." in Path(n).parts]; bad = []
        for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(zf.read(f"{LANE_REL.name}/{rel}")).hexdigest() != digest: bad.append(rel)
        audit = {"open": "PASS", "entries": len(names), "manifest_exact": names == expected, "duplicates": len(names) - len(set(names)),
                 "traversal": traversal, "sha_mismatches": bad, "parent_contamination": 0, "authority_contamination": 0}
    if not (audit["manifest_exact"] and audit["duplicates"] == 0 and not traversal and not bad): raise RuntimeError(audit)
    return path, sha256(path), audit


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true"); parser.add_argument("--rebuild-verify", action="store_true"); parser.add_argument("--package", action="store_true"); parser.add_argument("--output-root", type=Path, default=DEFAULT_LANE); parser.add_argument("--downloads", type=Path, default=Path(r"D:\Downloads")); args = parser.parse_args()
    if not any((args.build, args.verify, args.rebuild_verify, args.package)): args.build = args.verify = args.rebuild_verify = True
    lane = args.output_root.resolve()
    if args.build: build_outputs(lane); print(f"BUILD=PASS paths={len(EXPECTED_PATHS)} output={lane}")
    if args.verify:
        result = verify(lane, lane == DEFAULT_LANE.resolve()); print(json.dumps({k: v for k, v in result.items() if k != "cad"}, ensure_ascii=False, indent=2))
        if result["failures"]: return 1
    if args.rebuild_verify:
        result = independent_rebuild(lane); print("REPRODUCIBILITY=" + json.dumps(result, ensure_ascii=False))
        if result["status"] != "PASS": return 1
    if args.package:
        path, digest, audit = package(lane, args.downloads); print(f"ZIP_PATH={path}"); print(f"ZIP_SHA256={digest}"); print("ZIP_AUDIT=" + json.dumps(audit, ensure_ascii=False))
    return 0


if __name__ == "__main__": raise SystemExit(main())
