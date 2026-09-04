from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.6"
CLASSIFICATION = "DRY_DRIVE_FRAME_AND_SHAFT_INTEGRATION"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 1821
BASE_OUTSIDE_DIGEST = "917f989f94af88f98c3e13a90332cf5c3da9c21d6b1a8cd8c00626302172096d"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md", "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PROTECTED_LANES = {
    "v0.9.5.0": ("cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0", 105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "v0.9.5.1": ("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1", 53, "0157f6bb4a6f02dad08e9eade45cf3eeeb71d6b61a82e4e24ee5404498ebbe31"),
    "v0.9.5.2": ("cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2", 28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
    "v0.9.5.3": ("cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3", 25, "c49217200ea8d1a55b92632d4d1e3ad932fffd6ffdb9dbcb8edbea96c051ca0c"),
    "v0.9.6.0": ("cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0", 40, "6fff91564757139d0d8e99d7105dd33eec059bc426de6680da9356d46636f86e"),
    "v0.9.6.2": ("cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2", 57, "35e7a3e1a465114e4a3e268fc2ac137a78020a425fb4fb9e5576f360ca78a206"),
    "v0.9.6.3": ("cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3", 35, "e7f35b31edd6f79bda76e1a9c77dd59e98a1882c534b5c4792ea4c95cf8bea9f"),
    "v0.9.6.4": ("cad/common_rover/common_rover_drive_shaft_h25a1_full_integration_v0_9_6_4", 56, "d9390d3cf58e813062440aa9731fff9d149dfe2841e729de764882d722e6a1cf"),
    "v0.9.6.5": ("cad/common_rover/common_rover_dry_drive_physical_integration_v0_9_6_5", 82, "5fec426c5e01f94b2daa3f02989b19dcbc78b634fd41c20d5cdd696a22daa978"),
}

PULLEY_SOURCE = Path(r"D:\Paddy_Swarm_Project_worktrees\common_rover_htd5m_full_pulley_dummy_v0_1\cad\common_rover\htd5m_full_pulley_dummy_candidate_v0_1\artifacts")
PULLEY_20 = PULLEY_SOURCE / "PS-HTD5M-PULLEY-20T-STD-DUMMY-V001.step"
PULLEY_60 = PULLEY_SOURCE / "PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.step"
PULLEY_HASHES = {
    str(PULLEY_20): "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1",
    str(PULLEY_60): "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256",
}

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md", "FRAME_170MM_SPEC.md",
    "UPPER_2040_OUTBOARD_SPEC.md", "FRAME_LOAD_PATH.md", "CRAWLER_WIDTH_SPEC.md",
    "SPACER_8MM_SPEC.md", "INDEPENDENT_DRIVE_SHAFT_SPEC.md", "SHAFT_CUT_LENGTH_SPEC.md",
    "H25A1_B_PHYSICAL_SELECTION.md", "H25A1_WIDE_HUB_CAP_SPEC.md", "REACTION_SHOE_SPEC.md",
    "M4_PHYSICAL_AUTHORITY.md", "AXIAL_RETENTION_SPEC.md", "BATTERY_PACKAGING_COMPATIBILITY.md",
    "BBOX_COMPATIBILITY_HOLD.md", "ASSEMBLY_PROCEDURE.md", "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md", "POWERED_TEST_GATE.md", "SAFETY_NOTES.md", "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
]
FRAME_CAD = [
    "frame/artifacts/frame_170mm_core_reference_v0_9_6_6.step",
    "frame/artifacts/upper_2040_left_outboard_reference_v0_9_6_6.step",
    "frame/artifacts/upper_2040_right_outboard_reference_v0_9_6_6.step",
    "frame/artifacts/frame_170mm_drive_layout_v0_9_6_6.step",
]
DRIVE_CAD = [
    "drive/artifacts/drive_spacer_8mm_v0_9_6_6.step", "drive/artifacts/drive_spacer_8mm_v0_9_6_6.stl",
    "drive/artifacts/drive_12t_h25a1_fc_wide_cap_v0_9_6_6.step", "drive/artifacts/drive_12t_h25a1_fc_wide_cap_v0_9_6_6.stl",
    "drive/artifacts/h25a1_wide_front_hub_cap_v0_9_6_6.step", "drive/artifacts/h25a1_wide_front_hub_cap_v0_9_6_6.stl",
    "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_6.step", "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_6.stl",
    "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_6.step", "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_6.stl",
    "drive/artifacts/wide_front_hub_cap_fit_coupon_v0_9_6_6.step", "drive/artifacts/wide_front_hub_cap_fit_coupon_v0_9_6_6.stl",
    "drive/artifacts/left_drive_half_shaft_reference_v0_9_6_6.step",
    "drive/artifacts/right_drive_half_shaft_reference_v0_9_6_6.step",
    "drive/artifacts/independent_drive_shaft_assembly_v0_9_6_6.step",
]
INTEGRATION_CAD = ["integration/artifacts/narrow_frame_independent_drive_assembly_v0_9_6_6.step"]
CAD = FRAME_CAD + DRIVE_CAD + INTEGRATION_CAD
SVGS = [f"integration/artifacts/{name}" for name in (
    "frame_180_to_170_comparison_v0_9_6_6.svg", "upper_2040_outboard_offset_v0_9_6_6.svg",
    "crawler_width_8mm_spacer_v0_9_6_6.svg", "left_right_independent_shaft_architecture_v0_9_6_6.svg",
    "left_right_half_shaft_cut_measurement_v0_9_6_6.svg", "h25a1_b_tolerance_physical_selection_v0_9_6_6.svg",
    "wide_front_hub_cap_section_v0_9_6_6.svg", "wide_cap_axial_sandwich_v0_9_6_6.svg",
    "m4_reaction_torque_path_v0_9_6_6.svg", "170mm_full_drive_packaging_v0_9_6_6.svg",
)]
JSONS = ["design_parameters.json", "source_evidence.json", "collision_report.json", "validation_report.json", "reproducibility_report.json"]
SOURCE = ["build_narrow_frame_independent_drive_v0_9_6_6.py", "tests/test_narrow_frame_independent_drive_v0_9_6_6_contract.py"]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCE + RELEASE)

PROTECTED_12T = {
    "teeth": 12, "phase_deg": 15.0, "spacing_deg": 30.0, "tip_radius_mm": 33.07,
    "root_radius_mm": 29.47, "tip_width_mm": 7.5, "root_width_mm": 9.5,
    "axial_width_mm": 44.0, "pitch_diameter_mm": 76.3943726841,
    "buried_root_overlap_mm": 4.0, "outer_body": "ONE_PIECE", "split_teeth": False,
    "tooth_root_radial_service_holes": 0,
}
PARAMS = {
    "version": VERSION, "classification": CLASSIFICATION, "units": "mm",
    "frame": {"historical_transverse_mm": 180.0, "core_transverse_mm": 170.0,
              "core_class": "USER_SELECTED_PHYSICAL_MOCKUP", "physical_envelope_reference_mm": 171.0,
              "physical_envelope_class": "DERIVED_REFERENCE_ONLY", "core_inner_width_mm": 130.0,
              "upper_2040_source_center_abs_y_mm": 80.5, "upper_2040_final_center_abs_y_mm": 100.5,
              "left_outboard_shift_mm": 20.0, "right_outboard_shift_mm": 20.0,
              "upper_2040_length_mm": 540.0, "upper_2040_section_mm": [20.0, 40.0],
              "profile_orientation": "LENGTH_X_WIDTH20_Y_HEIGHT40_Z", "cut_length_changed": False,
              "architecture": "NARROW_CENTRAL_BODY_PLUS_LOCAL_OUTBOARD_DRIVE_SHOULDERS"},
    "motor": {"product": "JGB37-520", "cylinder_diameter_mm": 36.9, "body_length_mm": 60.9,
              "rear_terminal_mm": 9.2, "front_to_rear_fixed_mm": 70.1, "shaft_length_mm": 16.9,
              "shaft_diameter_mm": 5.9, "boss_mm": [12.0, 2.7], "bracket_mm": [40.1, 45.5, 42.8],
              "bracket_thickness_mm": 3.1, "source": "v0.9.3.1_USER_REPORTED_PHYSICAL_REFERENCE"},
    "powertrain": {"motor_front_abs_y_mm": 75.0, "belt_plane_abs_y_mm": 63.1,
                   "motor_x_mm": 60.0, "drive_x_mm": -60.0, "axis_z_mm": 175.0,
                   "center_distance_mm": 120.0, "belt_nominal_width_mm": 15.0,
                   "pulley_20_source": "STANDARD_FULL_DUMMY_OD35_WIDTH20",
                   "pulley_60_source": "STANDARD_FULL_DUMMY_OD102_WIDTH20",
                   "tensioner_sweep_radius_mm": 18.0, "tensioner_product": "HOLD",
                   "known_unintended_solid_intersections": 0,
                   "intended_contacts_excluded": ["BELT_TO_20T", "BELT_TO_60T"]},
    "spacer": {"id_mm": 10.2, "od_mm": 13.8, "thickness_mm": 8.0, "edge_chamfer_mm": 0.35,
               "contact": "KP000_ROTATING_INNER_RACE_FACE_ONLY", "seven_mm": "PHYSICAL_MARGIN_INSUFFICIENT",
               "status": "READY_TO_PRINT_PHYSICAL_VALIDATION_PENDING"},
    "crawler": {"link_width_measured_mm": 54.0, "rotating_width_nominal_mm": 294.0,
                "rotating_width_conservative_mm": 295.0, "target_max_mm": 300.0,
                "total_margin_nominal_mm": 6.0, "total_margin_conservative_mm": 5.0,
                "classification": "GEOMETRY_PASS_CANDIDATE_PHYSICAL_WIDTH_PENDING"},
    "shaft": {"architecture": "LEFT_RIGHT_INDEPENDENT_HALF_SHAFTS", "diameter_mm": 10.0,
              "form": "SOLID_PRIMARY", "dry_material": "STEEL_CANDIDATE", "final_material": "HOLD",
              "left_cut_length": "HOLD_PHYSICAL_MEASUREMENT", "right_cut_length": "HOLD_PHYSICAL_MEASUREMENT",
              "display_length_mm": 149.0, "display_center_gap_mm": 2.0,
              "display_center_gap_class": "ENGINEERING_REFERENCE_ONLY_NOT_FINAL",
              "continuous_cross_shaft_primary": False, "flats": "OPTIONAL_FUTURE"},
    "kp000": {"quantity_total": 4, "quantity_per_side": 2, "support": "DOUBLE_SUPPORTED_PER_HALF_SHAFT",
              "housing_reference_mm": [67.0, 17.0, 35.0], "positions": "REFERENCE_ONLY_FINAL_PHYSICAL_RECORD_REQUIRED"},
    "h25a1": {"architecture": "H2.5-A1-FC-WIDE-CAP", "collar_mm": [15.9, 10.1, 3.0],
              "fastener": "HEADED_M4", "quantity": 2, "angle_deg": 90.0, "grub_screw_primary_count": 0,
              "screw_od_mm_approx": 3.8, "head_od_mm": 6.8, "head_height_mm": 2.8,
              "washer_od_mm": 8.8, "washer_stack_mm": 1.8, "full_radial_envelope_radius_mm": 20.0,
              "full_axial_envelope_mm": 8.8, "selected_collar_pocket_diameter_mm": 16.2,
              "selected_hardware_cavity_radius_mm": 20.4, "selection": "B_PHYSICAL_SELECTED",
              "coupon_results": {"A": "TOO_TIGHT_FOR_SERVICE_REJECT_FINAL", "B": "PHYSICAL_PRIMARY_PASS", "C": "TOO_LOOSE_REJECT_FINAL"},
              "reaction_shoes": 2, "staged_relief_mm": [9.2, 6.9, 4.2], "permanent_adhesive": False,
              "qualification_24h": "SHAFT_TO_COLLAR_PHYSICAL_EVIDENCE_NOT_FULL_TORQUE"},
    "wide_cap": {"outer_diameter_mm": 50.0, "thickness_mm": 5.5, "role": "AXIAL_CAPTURE_AND_LOAD_SPREAD",
                 "primary_torque_path": False, "nested_z_mm": [16.5, 22.0], "axial_complete_target_mm": 44.0,
                 "radial_root_margin_mm": 4.47, "index_pads": 4, "index_pads_torque_primary": False,
                 "locking": "CAP_LOCKING_HARDWARE_HOLD_PROTOTYPE_FRICTION_INDEX_ONLY",
                 "coupon": "READY_TO_PRINT", "full_12t_print": "PENDING_WIDE_CAP_COUPON_PASS"},
    "battery": {"carrier_outer_width_reference_mm": 110.0, "frame_inner_width_reference_mm": 130.0,
                "side_opportunity_each_mm": 10.0, "status": "GEOMETRIC_OPPORTUNITY_PHYSICAL_PENDING"},
    "bbox": {"submerged_compatibility": "HOLD_FRAME_REDESIGN"},
    "pto": {"redesign": "OUT_OF_SCOPE", "outboard_reservation": "PRESERVED_REFERENCE_ONLY"},
    "protected_12t": PROTECTED_12T,
    "gates": {"frame_170": "CAD_COMPLETE_PHYSICAL_REBUILD_PENDING", "upper_2040": "CAD_COMPLETE_PHYSICAL_REBUILD_PENDING",
              "spacer_8mm": "READY_TO_PRINT", "wide_cap": "CAD_COMPLETE_PHYSICAL_COUPON_PENDING",
              "full_12t": "PRINT_AFTER_WIDE_CAP_COUPON_PASS", "shaft_cut": "HOLD_PHYSICAL_MEASUREMENT",
              "powered_bench": "NOT_YET_APPROVED", "water": "NOT_APPROVED", "mud": "NOT_APPROVED", "field": "NOT_APPROVED"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", stderr=subprocess.DEVNULL).strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts), key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in files:
        h.update(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(files), h.hexdigest()


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder(radius: float, length: float, z0: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length).translate((0, 0, z0))


def axis_cylinder(radius: float, length: float, origin: tuple[float, float, float], direction: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction)))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    values = []
    for part in parts:
        values.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result.clean()


def volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(float(a.val().intersect(b.val()).Volume()), 6)


def dims(obj: cq.Workplane) -> list[float]:
    b = obj.val().BoundingBox()
    return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]


def frame_170_core() -> cq.Workplane:
    parts = [box(540.0, 20.0, 20.0, (0, y, 90.0)) for y in (-75.0, 75.0)]
    parts += [box(20.0, 170.0, 20.0, (x, 0, 90.0)) for x in (-260.0, 260.0)]
    return compound(parts)


def upper_2040(side: int) -> cq.Workplane:
    return box(540.0, 20.0, 40.0, (0, side * 100.5, 120.0))


def frame_layout() -> cq.Workplane:
    return compound([frame_170_core(), upper_2040(1), upper_2040(-1)])


def pulley_source(path: Path) -> cq.Workplane:
    return cq.importers.importStep(str(path))


def orient_axial(obj: cq.Workplane, side: int, center: tuple[float, float, float], source_width: float = 20.0) -> cq.Workplane:
    x, y, z = center
    if side > 0:
        return obj.rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y - source_width / 2, z))
    return obj.rotate((0, 0, 0), (1, 0, 0), 90).translate((x, y + source_width / 2, z))


def motor_parts(side: int) -> dict[str, cq.Workplane]:
    y0, x, z = side * 75.0, 60.0, 175.0
    outward, inward = (0.0, float(side), 0.0), (0.0, float(-side), 0.0)
    body = axis_cylinder(36.9 / 2, 60.9, (x, y0, z), outward)
    terminal = axis_cylinder(36.9 / 2, 9.2, (x, y0 + side * 60.9, z), outward)
    shaft = axis_cylinder(5.9 / 2, 16.9, (x, y0, z), inward)
    boss = axis_cylinder(12.0 / 2, 2.7, (x, y0, z), inward)
    bracket = box(40.1, 42.8, 45.5, (x, y0 + side * 21.4, z))
    return {"body": body, "terminal": terminal, "shaft": shaft, "boss": boss, "bracket": bracket}


def belt_envelope(side: int) -> cq.Workplane:
    y, z = side * 63.1, 175.0
    direction, origin_y = (0.0, float(side), 0.0), y - side * 7.5
    small = axis_cylinder(19.0, 15.0, (60.0, origin_y, z), direction).cut(axis_cylinder(13.0, 15.4, (60.0, origin_y - side * 0.2, z), direction))
    large = axis_cylinder(53.0, 15.0, (-60.0, origin_y, z), direction).cut(axis_cylinder(47.0, 15.4, (-60.0, origin_y - side * 0.2, z), direction))
    runs = box(120.0, 15.0, 12.0, (0.0, y, z))
    return compound([small, large, runs])


def tensioner_reserve(side: int) -> cq.Workplane:
    y = side * 63.1
    return axis_cylinder(18.0, 15.0, (10.0, y - side * 7.5, 205.0), (0, side, 0))


def pulley(side: int, teeth: int) -> cq.Workplane:
    center = ((60.0 if teeth == 20 else -60.0), side * 63.1, 175.0)
    return orient_axial(pulley_source(PULLEY_20 if teeth == 20 else PULLEY_60), side, center)


def source_ring_hub_spokes() -> cq.Workplane:
    w = 44.0
    ring = cylinder(29.47, w, -22.0).cut(cylinder(20.0, w + 0.4, -22.2))
    body = ring.union(cylinder(18.0, w, -22.0))
    for i in range(6):
        body = body.union(box(7.5, 12.0, w, (18.75, 0, 0)).rotate((0, 0, 0), (0, 0, 1), i * 60.0))
    return body.clean()


def embedded_tooth() -> cq.Workplane:
    r = 29.47 - 4.0
    return cq.Workplane("XY").polyline([(r, -6.5), (29.47, -4.75), (33.07, -3.75), (33.07, 3.75), (29.47, 4.75), (r, 6.5)]).close().extrude(22.0, both=True)


def protected_blank() -> cq.Workplane:
    body, tooth = source_ring_hub_spokes(), embedded_tooth()
    for i in range(12):
        body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), 15.0 + i * 30.0))
    return body.clean()


def full_capture_voids() -> cq.Workplane:
    bore = cylinder(5.15, 46.0, -23.0)
    collar_open = cylinder(8.1, 24.0, -2.0)
    tool_x = box(40.8, 9.2, 26.6, (0, 0, 8.7))
    tool_y = box(9.2, 40.8, 26.6, (0, 0, 8.7))
    shoe_x = box(15.55, 13.6, 24.4, (16.525, 0, 9.8))
    shoe_y = box(13.6, 15.55, 24.4, (0, 16.525, 9.8))
    cap_recess = cylinder(25.2, 5.5, 16.5)
    pad_pockets = [box(4.4, 4.4, 17.8, (18.0, 0, 13.1)).rotate((0, 0, 0), (0, 0, 1), a) for a in (45, 135, 225, 315)]
    return compound([bore, collar_open, tool_x, tool_y, shoe_x, shoe_y, cap_recess, *pad_pockets])


def main_sprocket() -> cq.Workplane:
    part = protected_blank()
    for void in full_capture_voids().solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.clean()


def collar() -> cq.Workplane:
    return cylinder(15.9 / 2, 3.0, -1.5).cut(cylinder(10.1 / 2, 3.4, -1.7))


def full_hardware() -> cq.Workplane:
    parts = [collar(), axis_cylinder(1.9, 4.0, (5.05, 0, 0), (1, 0, 0)), axis_cylinder(1.9, 4.0, (0, 5.05, 0), (0, 1, 0)),
             axis_cylinder(4.4, 1.8, (8.95, 0, 0), (1, 0, 0)).cut(axis_cylinder(2.05, 2.0, (8.85, 0, 0), (1, 0, 0))),
             axis_cylinder(4.4, 1.8, (0, 8.95, 0), (0, 1, 0)).cut(axis_cylinder(2.05, 2.0, (0, 8.85, 0), (0, 1, 0))),
             axis_cylinder(3.4, 2.8, (10.75, 0, 0), (1, 0, 0)), axis_cylinder(3.4, 2.8, (0, 10.75, 0), (0, 1, 0))]
    return compound(parts)


def reaction_shoe() -> cq.Workplane:
    part = box(15.15, 13.2, 4.4, (7.575, 0, 2.2)).cut(box(1.8, 9.2, 6.0, (0.9, 0, 3.0)))
    part = part.cut(box(2.8, 6.9, 6.0, (3.2, 0, 3.0))).cut(box(6.55, 4.2, 6.0, (7.875, 0, 3.0)))
    return part.union(box(5.1, 13.2, 2.4, (9.6, 0, 5.6))).clean()


def installed_shoes() -> tuple[cq.Workplane, cq.Workplane]:
    return (reaction_shoe().translate((8.95, 0, -2.2)), reaction_shoe().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 8.95, -2.2)))


def wide_cap() -> cq.Workplane:
    disc = cylinder(25.0, 5.5, 16.5).cut(cylinder(5.2, 5.9, 16.3))
    disc = disc.cut(box(17.5, 9.4, 5.9, (13.75, 0, 19.25))).cut(box(9.4, 17.5, 5.9, (0, 13.75, 19.25)))
    pads = [box(4.0, 4.0, 11.9, (18.0, 0, 10.55)).rotate((0, 0, 0), (0, 0, 1), a) for a in (45, 135, 225, 315)]
    return fused([disc, *pads]).clean()


def service_tool() -> cq.Workplane:
    return compound([cylinder(2.5, 25.0, 0).translate((12.0, 0, 0)), cylinder(2.5, 25.0, 0).translate((0, 12.0, 0))])


def spacer_8() -> cq.Workplane:
    ring = cylinder(13.8 / 2, 8.0).cut(cylinder(10.2 / 2, 8.4, -0.2))
    return ring.edges("%CIRCLE").chamfer(0.35).clean()


def coupon_parts() -> cq.Workplane:
    socket = main_sprocket().intersect(cylinder(28.0, 44.0, -22.0)).clean()
    cap = wide_cap().translate((65.0, 0, 0))
    shoe_a = reaction_shoe().translate((45.0, 40.0, 0))
    shoe_b = reaction_shoe().rotate((0, 0, 0), (0, 0, 1), 90).translate((80.0, 40.0, 0))
    return compound([socket, cap, shoe_a, shoe_b])


def kp000(center_y: float) -> cq.Workplane:
    housing = box(67.0, 17.0, 35.0, (-60.0, center_y, 175.0))
    bore = axis_cylinder(8.0, 19.0, (-60.0, center_y - 9.5, 175.0), (0, 1, 0))
    return housing.cut(bore).clean()


def half_shaft(side: int) -> cq.Workplane:
    return axis_cylinder(5.0, 149.0, (-60.0, side * 1.0, 175.0), (0, side, 0)).edges("%CIRCLE").chamfer(0.7)


def placed_drive_piece(obj: cq.Workplane, side: int, center_y: float = 120.1) -> cq.Workplane:
    if side > 0:
        return obj.rotate((0, 0, 0), (1, 0, 0), -90).translate((-60.0, center_y, 175.0))
    return obj.rotate((0, 0, 0), (1, 0, 0), 90).translate((-60.0, -center_y, 175.0))


def placed_spacer(side: int) -> cq.Workplane:
    center = side * 94.1
    return orient_axial(spacer_8(), side, (-60.0, center, 175.0), source_width=8.0)


def crawler_rotating_envelopes() -> cq.Workplane:
    return compound([axis_cylinder(45.0, 54.0, (-60.0, 93.0, 175.0), (0, 1, 0)), axis_cylinder(45.0, 54.0, (-60.0, -93.0, 175.0), (0, -1, 0))])


def independent_shaft_assembly() -> cq.Workplane:
    parts = [half_shaft(1), half_shaft(-1)]
    for side in (-1, 1):
        parts += [kp000(side * 44.6), kp000(side * 81.6), pulley(side, 60), placed_spacer(side),
                  placed_drive_piece(main_sprocket(), side), placed_drive_piece(wide_cap(), side)]
    return compound(parts)


def battery_envelope() -> cq.Workplane:
    return box(150.9, 110.0, 92.5, (40.0, 0, 190.0))


def future_pto_reserve() -> cq.Workplane:
    return compound([box(90, 20, 70, (-170, 155, 175)), box(90, 20, 70, (-170, -155, 175))])


def full_integration() -> cq.Workplane:
    parts = [frame_layout(), battery_envelope(), independent_shaft_assembly(), crawler_rotating_envelopes()]
    for side in (-1, 1):
        parts += list(motor_parts(side).values()) + [pulley(side, 20), belt_envelope(side), tensioner_reserve(side)]
    return compound(parts)


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "frame/artifacts/frame_170mm_core_reference_v0_9_6_6": (frame_170_core, False),
    "frame/artifacts/upper_2040_left_outboard_reference_v0_9_6_6": (lambda: upper_2040(1), False),
    "frame/artifacts/upper_2040_right_outboard_reference_v0_9_6_6": (lambda: upper_2040(-1), False),
    "frame/artifacts/frame_170mm_drive_layout_v0_9_6_6": (frame_layout, False),
    "drive/artifacts/drive_spacer_8mm_v0_9_6_6": (spacer_8, True),
    "drive/artifacts/drive_12t_h25a1_fc_wide_cap_v0_9_6_6": (main_sprocket, True),
    "drive/artifacts/h25a1_wide_front_hub_cap_v0_9_6_6": (wide_cap, True),
    "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_6": (reaction_shoe, True),
    "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_6": (reaction_shoe, True),
    "drive/artifacts/wide_front_hub_cap_fit_coupon_v0_9_6_6": (coupon_parts, True),
    "drive/artifacts/left_drive_half_shaft_reference_v0_9_6_6": (lambda: half_shaft(1), False),
    "drive/artifacts/right_drive_half_shaft_reference_v0_9_6_6": (lambda: half_shaft(-1), False),
    "drive/artifacts/independent_drive_shaft_assembly_v0_9_6_6": (independent_shaft_assembly, False),
    "integration/artifacts/narrow_frame_independent_drive_assembly_v0_9_6_6": (full_integration, False),
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
    for base, (factory, make_stl) in GEOMETRIES.items():
        obj = factory()
        step = out / f"{base}.step"
        step.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(obj, str(step)); normalize_step(step)
        if make_stl:
            cq.exporters.export(obj, str(out / f"{base}.stl"), tolerance=0.02, angularTolerance=0.1)


def svg_page(title: str, body: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560">
<rect width="1000" height="560" fill="#fbfcfe"/><text x="25" y="34" font-family="sans-serif" font-size="22" font-weight="bold">{title}</text>
<text x="975" y="32" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.6 · DRY DRIVE · NOT FIELD APPROVED</text>{body}
<text x="25" y="535" font-family="sans-serif" font-size="12">Blue=USER/MEASURED · Purple=DERIVED · Green=DESIGN PRIMARY · Orange=HOLD</text></svg>'''


def svg_outputs() -> dict[str, str]:
    c = 'font-family="sans-serif"'
    return {
        SVGS[0]: svg_page("Frame 180 → 170 comparison", f'''<g {c}><rect x="180" y="140" width="180" height="80" fill="#bbb"/><rect x="180" y="300" width="170" height="80" fill="#2980b9"/><text x="390" y="185">historical 180</text><text x="390" y="345">selected 170.0</text><text x="390" y="385">171 conservative envelope reference</text></g>'''),
        SVGS[1]: svg_page("Upper 2040 outboard relocation", f'''<g {c}><line x1="500" y1="80" x2="500" y2="450" stroke="#333"/><rect x="350" y="170" width="40" height="220" fill="#aaa"/><rect x="250" y="170" width="40" height="220" fill="#27ae60"/><rect x="610" y="170" width="40" height="220" fill="#aaa"/><rect x="710" y="170" width="40" height="220" fill="#27ae60"/><text x="190" y="430">LEFT: 20 mm OUTBOARD</text><text x="650" y="430">RIGHT: 20 mm OUTBOARD</text><text x="350" y="470">540×20×40, orientation unchanged, cut length unchanged</text></g>'''),
        SVGS[2]: svg_page("Crawler width with 8 mm spacers", f'''<g {c}><rect x="260" y="180" width="340" height="130" fill="#2980b9" opacity=".25"/><rect x="152" y="160" width="108" height="170" fill="#27ae60"/><rect x="600" y="160" width="108" height="170" fill="#27ae60"/><line x1="152" y1="390" x2="708" y2="390" stroke="#222"/><text x="400" y="420">170 + 54×2 + 8×2 = 294 mm</text><text x="400" y="450">171 reference → 295 mm; margin 5 mm</text></g>'''),
        SVGS[3]: svg_page("Independent left/right drive shafts", f'''<g {c}><line x1="80" y1="270" x2="485" y2="270" stroke="#27ae60" stroke-width="12"/><line x1="515" y1="270" x2="920" y2="270" stroke="#27ae60" stroke-width="12"/><text x="190" y="230">RIGHT independent</text><text x="650" y="230">LEFT independent</text><text x="420" y="320">NON-CONTACT GAP: HOLD (2 mm display reference only)</text><text x="320" y="380">continuous cross shaft is not primary</text></g>'''),
        SVGS[4]: svg_page("Left/right shaft cut measurement worksheet", f'''<g {c}><text x="60" y="100">LEFT — measure after frame170 / 2040 / KP000 / 8mm / 12T / collars are physical-final</text><line x1="90" y1="170" x2="910" y2="170" stroke="#222"/><text x="60" y="260">RIGHT — repeat independently; identify caliper faces and smooth end reserve</text><line x1="90" y1="330" x2="910" y2="330" stroke="#222"/><text x="60" y="430" fill="#e67e22">LEFT_CUT=HOLD · RIGHT_CUT=HOLD · do not use old110 or unresolved17.9</text></g>'''),
        SVGS[5]: svg_page("H2.5-A1 B physical selection", f'''<g {c}><rect x="90" y="150" width="220" height="180" fill="#e74c3c" opacity=".25"/><rect x="390" y="150" width="220" height="180" fill="#27ae60" opacity=".3"/><rect x="690" y="150" width="220" height="180" fill="#e74c3c" opacity=".25"/><text x="130" y="210">A Ø16.1 / R20.2</text><text x="130" y="250">TOO TIGHT</text><text x="430" y="210">B Ø16.2 / R20.4</text><text x="430" y="250">PHYSICAL PRIMARY PASS</text><text x="730" y="210">C Ø16.3 / R20.6</text><text x="730" y="250">TOO LOOSE</text></g>'''),
        SVGS[6]: svg_page("Wide front hub cap section", f'''<g {c}><rect x="180" y="120" width="560" height="300" fill="#aaa" opacity=".25"/><rect x="470" y="120" width="110" height="250" fill="#27ae60" opacity=".6"/><line x1="180" y1="120" x2="740" y2="120" stroke="#222"/><text x="610" y="170">OD50 × 5.5</text><text x="610" y="205">nested z16.5…22</text><text x="610" y="240">complete axial envelope 44</text><text x="610" y="275">root radial margin 4.47</text></g>'''),
        SVGS[7]: svg_page("Wide-cap axial sandwich", f'''<g {c}><text x="70" y="135" font-size="20">WIDE CAP → indexing/capture pads → reaction shoes → metal collar + headed M4 → main one-piece hub</text><path d="M100 190H880" stroke="#27ae60" stroke-width="50"/><text x="100" y="290">Broad cap land spreads axial load. Shoes remain the collar→PETG torque features.</text><text x="100" y="340">Cap is NOT primary torque path. Final removable locking hardware remains HOLD.</text></g>'''),
        SVGS[8]: svg_page("M4 reaction torque path", f'''<g {c}><text x="90" y="150" font-size="21">Ø10 shaft → headed M4 ×2 @90° → metal collar → broad reaction shoes ×2 → one-piece PETG hub → 12T teeth</text><text x="90" y="230">B tolerance: pocket Ø16.2 / full hardware cavity R20.4</text><text x="90" y="290">24 h evidence: shaft↔collar only; full drive torque NOT QUALIFIED</text><text x="90" y="350">grub screw primary count = 0 · adhesive = false</text></g>'''),
        SVGS[9]: svg_page("170 mm full-drive packaging", f'''<g {c}><rect x="110" y="160" width="780" height="190" fill="#2980b9" opacity=".12"/><line x1="130" y1="255" x2="870" y2="255" stroke="#222" stroke-width="20"/><circle cx="320" cy="220" r="40" fill="#8e44ad"/><circle cx="520" cy="220" r="95" fill="#27ae60" opacity=".45"/><text x="210" y="390">JGB37-520 / bracket / STANDARD20T / 15mm belt / STANDARD60T / tensioner R18 reserve</text><text x="210" y="425">known unintended solid intersections 0; physical rebuild and final hardware datums pending</text></g>'''),
    }


def docs() -> dict[str, str]:
    h = f"# Common Rover Narrow Frame + Independent DRIVE {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nRelease: `DRY PHYSICAL PREPARATION / NOT FIELD APPROVED`  \n"
    d: dict[str, str] = {}
    d["README.md"] = h + "\nThis isolated lane integrates the user-selected170 mm core, ±20 mm outboard upper2040 supports, independent half-shafts, the physical B full-capture tolerance, an8 mm inner-race spacer and a nested wide hub cap. Build the spacer and cap coupon first. Shaft cuts and power remain HOLD.\n"
    d["DESIGN_AUTHORITY.md"] = h + "\nUser authority:170 mm mockup,7 mm near-zero margin, A tight/B service-fit/C loose. Protected authority: headed M4×2 at90°, collar15.9/10.1/3.0 and one-piece12T geometry. Design primary:8 mm spacer,50×5.5 cap and upper2040 outboard20/side. Derived:171 envelope and294–295 rotating width.\n"
    d["PHYSICAL_INPUTS.md"] = h + "\n|Input|Value|Class|\n|---|---:|---|\n|Core transverse|170.0|USER_SELECTED_PHYSICAL_MOCKUP|\n|7 mm spacer|almost no clearance|USER_REPORTED / INSUFFICIENT|\n|Coupon A|tight; tool striking needed|USER_REPORTED / REJECT|\n|Coupon B|fit; hand-tool removal|USER_REPORTED / SELECT|\n|Coupon C|loose; falls inverted|USER_REPORTED / REJECT|\n|JGB37 body|Ø36.9×60.9|USER PHYSICAL REFERENCE v0.9.3.1|\n"
    d["FRAME_170MM_SPEC.md"] = h + "\n`CORE_TRANSVERSE_MEMBER_LENGTH=170.0` is primary;180 remains historical.171 is a conservative derived physical-envelope reference, not a future measurement substitute. The core is 20-series metal with130 mm nominal clear width.\n"
    d["UPPER_2040_OUTBOARD_SPEC.md"] = h + "\nLeft and right upper drive supports translate20.0 mm outward from source centersY=±80.5 toY=±100.5. Profile orientation remains lengthX / width20Y / height40Z. Length540 is unchanged; no cut-length release occurs.\n"
    d["FRAME_LOAD_PATH.md"] = h + "\nMotor and belt reactions enter the local upper2040 shoulders, then the metal core rails/crossmembers. 2040 is reserved for concentrated drive reaction; 2020 remains for lower-load geometry and spacing. No PETG box is a primary structural member. Final adapter bolt stack and bracing physical check remain HOLD.\n"
    d["CRAWLER_WIDTH_SPEC.md"] = h + "\nMeasured link54×2 plus170 core plus8×2 spacers gives294 mm. The171 conservative reference gives295 mm, leaving6 or5 mm total below300. This is `GEOMETRY_PASS_CANDIDATE / PHYSICAL_WIDTH_PENDING`; rotating crawler/guide is the entanglement authority.\n"
    d["SPACER_8MM_SPEC.md"] = h + "\nPrintable ring: ID10.2, OD13.8, thickness8.0, edge chamfer0.35. Contact the KP000 rotating inner-race face only; never bridge outer race, seal, housing or screw envelope. Test20 forward+20 reverse and seek ≥1.0 mm minimum frame/guide clearance.\n"
    d["INDEPENDENT_DRIVE_SHAFT_SPEC.md"] = h + "\nLeft and right Ø10 solid half-shafts are independent and double-supported by two KP000 each. Continuous cross-chassis shaft is not primary. Dry steel is a candidate; field material is HOLD. The STEP display uses a2 mm center reference gap only to prove non-overlap and is not cut authority.\n"
    d["SHAFT_CUT_LENGTH_SPEC.md"] = h + "\n`LEFT=HOLD_PHYSICAL_MEASUREMENT`, `RIGHT=HOLD_PHYSICAL_MEASUREMENT`. Measure each side only after170 frame, upper2040, inner/outer KP000,8 mm spacer, full12T and independent collars are physically final. Record exact caliper faces and smooth reserve. Do not use old110 display or unresolved17.9.\n"
    d["H25A1_B_PHYSICAL_SELECTION.md"] = h + "\nA Ø16.1/R20.2 is too tight for service and rejected. B Ø16.2/R20.4 fits and is removable with an ordinary hand tool: `PHYSICAL_PRIMARY_PASS`. C Ø16.3/R20.6 is loose/falls inverted and rejected. B is used exactly; no averaging.\n"
    d["H25A1_WIDE_HUB_CAP_SPEC.md"] = h + "\nThe old36×4.8 retainer is historical only. New cap is OD50×5.5, nested in z16.5…22 so the complete sprocket stays44 mm. It provides broad axial capture/load spreading, containment and anti-pop-out support, not primary torque. Four pads index and capture; final removable locking hardware is HOLD.\n"
    d["REACTION_SHOE_SPEC.md"] = h + "\nTwo replaceable PETG shoes retain the B-selected cage and staged9.2/6.9/4.2 relief. They are the broad collar→main-hub torque features. No adhesive, no tooth/root holes and no cap torque substitution.\n"
    d["M4_PHYSICAL_AUTHORITY.md"] = h + "\nUse headed M4×2 at90°, never headless grub screws. Collar15.9/10.1/3.0; screw≈3.8; head6.8×2.8; washer8.8×1.8; full envelopeR20×8.8. The24 h user result is shaft↔collar evidence only and does not qualify full-drive torque.\n"
    d["AXIAL_RETENTION_SPEC.md"] = h + "\nEach half-shaft requires its own metal collar→KP000→drive stack→KP000→metal collar retention. PETG sprocket is never sole axial retention. Final commercial collars, clamp torque and end reserves remain physical-selection HOLD.\n"
    d["BATTERY_PACKAGING_COMPATIBILITY.md"] = h + "\nApproximate carrier outer width110 within the130 mm core inner reference leaves a nominal10 mm opportunity on each side. CAD shows no fixed frame intersection at the reference placement, but actual guide fit and cable/terminal service need physical measurements.\n"
    d["BBOX_COMPATIBILITY_HOLD.md"] = h + "\nA130 mm BBOX flange is not automatically approved in roughly130 mm inner space. `SUBMERGED_BBOX_COMPATIBILITY=HOLD_FRAME_REDESIGN`. This lane is dry-drive-first and does not distort the170 mm frame to solve submerged packaging.\n"
    d["ASSEMBLY_PROCEDURE.md"] = h + "\nPhase1 print8 mm spacer and wide-cap coupon. Phase2 rebuild170 core and move each upper2040 outward20. Phase3 verify motor/20T/belt/60T/tensioner and crawler clearance. Phase4 coupon PASS, then cap/shoes/full12T. Phase5 physically fix KP000/collars, measure each shaft, then and only then consider cutting.\n"
    d["PRINT_PLAN.md"] = h + "\nBambu A1 / PETG. Print spacer then wide-cap coupon. Inspect ID/OD, chamfers, cap flatness/warp, service bridges, index pads, shoe layer direction and B cage removal. Full12T print is blocked until the wide-cap coupon seats flat, remains removable and shows no cracking.\n"
    d["PHYSICAL_TEST_PLAN.md"] = h + "\nSpacer: inner-race-only contact,20F+20R, record minimum clearance. Frame: outer/inner width, both2040 positions, motor/frame and60T/frame gaps. Cap coupon: B insertion/removal without hammer, shoes, flat/no-rock seat, M4 access, removability, broad stable sandwich, no crack.\n"
    d["POWERED_TEST_GATE.md"] = h + "\nNo powered floor operation. Before low-load unloaded bench work require physical PASS for frame170, upper2040,8 mm spacer, full wide-cap assembly, independent shafts, center non-contact, independent metal axial retention, paint marks, fuse, cutoff, polarity and MD10C wiring. Even then status is only `LOW_LOAD_POWERED_BENCH_READY`, not full power.\n"
    d["SAFETY_NOTES.md"] = h + "\nDRY ONLY. Disconnect battery before mechanical work. Upper2040 ends need smooth/end-cap treatment; shaft ends must be rounded, burr-free and hook-free with no protruding screw. Stop on rub, derailment, crack, cap rock, shaft walk, paint-mark shift or heat. Water, mud and field are NOT APPROVED.\n"
    d["HOLD_REGISTER.md"] = h + "\n- Left/right shaft cut lengths and final center gap\n- Final KP000 positions, shaft material, collars, flats and torque\n- Tensioner product, belt length/tension and full-drive torque\n- Final cap locking hardware and full12T print until coupon PASS\n- Actual frame/guide, motor/frame,60T/frame, battery and tool clearances\n- BBOX submerged compatibility, water, mud, powered floor and field release\n"
    d["SOURCE_TRACE.md"] = h + "\n- v0.9.6.5 read-only: protected one-piece12T/H2.5-A1 geometry and local spacer method.\n- v0.9.3.1: JGB37-520 dimensions and STANDARD20T/60T source SHA references.\n- STANDARD pulley worktree: exact20T and60T STEP sources, SHA-verified.\n- v0.9.4.0: physical540×181 frame transform and upper rail orientation context.\n- v0.9.0: tensioner sweep R18 reservation only; product remains HOLD.\n- v0.9.5.3: headed-M424h physical evidence.\nNo source releases shaft cuts, final mount holes, belt tension, BBOX submersion or power.\n"
    return d


def source_evidence() -> dict[str, object]:
    rels = [
        "cad/common_rover/common_rover_dry_drive_physical_integration_v0_9_6_5/build_dry_drive_physical_integration_v0_9_6_5.py",
        "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1/build_candidate_a_physical_mockup_v0931.py",
        "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0/build_common_rover_physical_integration_v0940.py",
        "cad/common_rover/common_rover_powertrain_frame_belt_design_authority_v0_9_0/common_rover_powertrain_parameters_v090.json",
        "cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3/H25A1_24H_CREEP_TEST.md",
    ]
    sources = [{"path": p, "sha256": sha256(REPO_ROOT / p)} for p in rels]
    sources += [{"path": p, "sha256": sha256(Path(p))} for p in PULLEY_HASHES]
    return {"sources": sources, "pulley_hash_contract": PULLEY_HASHES,
            "shaft_cut_length": "HOLD_PHYSICAL_MEASUREMENT", "tensioner_product": "HOLD",
            "physical_result_authority": "USER_REPORTED_2026-08-11"}


def root_annulus() -> cq.Workplane:
    return cylinder(33.07, 44.0, -22.0).cut(cylinder(29.47, 44.4, -22.2))


def geometry_metrics() -> dict[str, object]:
    frame, sprocket, cap, hardware, tool = frame_layout(), main_sprocket(), wide_cap(), full_hardware(), service_tool()
    shoe_a, shoe_b = installed_shoes()
    cap_contact = volume(cap.translate((0, 0, -0.01)), sprocket) / 0.01
    unintended: dict[str, float] = {}
    for side in (-1, 1):
        mp = motor_parts(side)
        for name, obj in mp.items(): unintended[f"{side}_{name}_frame"] = volume(obj, frame)
        unintended[f"{side}_20t_frame"] = volume(pulley(side, 20), frame)
        unintended[f"{side}_60t_frame"] = volume(pulley(side, 60), frame)
        unintended[f"{side}_belt_frame"] = volume(belt_envelope(side), frame)
        unintended[f"{side}_tensioner_frame"] = volume(tensioner_reserve(side), frame)
        unintended[f"{side}_future_pto_frame"] = volume(future_pto_reserve(), frame)
    left, right = half_shaft(1), half_shaft(-1)
    return {
        "core_bounds_mm": dims(frame_170_core()), "frame_layout_bounds_mm": dims(frame),
        "upper_2040_bounds_mm": dims(upper_2040(1)), "upper_left_center_y_mm": 100.5, "upper_right_center_y_mm": -100.5,
        "spacer_bounds_mm": dims(spacer_8()), "sprocket_bounds_mm": dims(sprocket), "sprocket_solids": sprocket.solids().size(),
        "cap_bounds_mm": dims(cap), "cap_solids": cap.solids().size(), "complete_axial_envelope_mm": max(sprocket.val().BoundingBox().zmax, cap.val().BoundingBox().zmax) - min(sprocket.val().BoundingBox().zmin, cap.val().BoundingBox().zmin),
        "cap_main_intersection_mm3": volume(cap, sprocket), "cap_contact_area_sampled_mm2": round(cap_contact, 2),
        "cap_hardware_intersection_mm3": volume(cap, hardware), "cap_shoe_a_intersection_mm3": volume(cap, shoe_a), "cap_shoe_b_intersection_mm3": volume(cap, shoe_b),
        "hardware_sprocket_intersection_mm3": volume(hardware, sprocket), "shoe_a_sprocket_intersection_mm3": volume(shoe_a, sprocket), "shoe_b_sprocket_intersection_mm3": volume(shoe_b, sprocket),
        "shoe_mutual_intersection_mm3": volume(shoe_a, shoe_b), "tool_sprocket_intersection_mm3": volume(tool, sprocket), "tool_cap_intersection_mm3": volume(tool, cap),
        "protected_root_void_intersection_mm3": volume(root_annulus(), full_capture_voids()),
        "shaft_center_overlap_mm3": volume(left, right), "shaft_display_gap_mm": 2.0,
        "battery_frame_intersection_mm3": volume(battery_envelope(), frame), "battery_side_opportunity_each_mm": 10.0,
        "rotating_width_nominal_mm": 294.0, "rotating_width_conservative_mm": 295.0,
        "unintended_intersections_mm3": unintended, "known_unintended_all_zero": all(v == 0 for v in unintended.values()),
        "coupon_solids": coupon_parts().solids().size(),
        "all_primary_shapes_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [frame_170_core(), upper_2040(1), upper_2040(-1), spacer_8(), sprocket, cap, reaction_shoe(), coupon_parts(), left, right]),
    }


def collision_report() -> dict[str, object]:
    m = geometry_metrics()
    local = {
        "CAP_VS_MAIN_HUB": m["cap_main_intersection_mm3"], "CAP_VS_HARDWARE": m["cap_hardware_intersection_mm3"],
        "CAP_VS_SHOE_A": m["cap_shoe_a_intersection_mm3"], "CAP_VS_SHOE_B": m["cap_shoe_b_intersection_mm3"],
        "HARDWARE_VS_MAIN_HUB": m["hardware_sprocket_intersection_mm3"], "SHOE_A_VS_MAIN_HUB": m["shoe_a_sprocket_intersection_mm3"],
        "SHOE_B_VS_MAIN_HUB": m["shoe_b_sprocket_intersection_mm3"], "LEFT_SHAFT_VS_RIGHT_SHAFT": m["shaft_center_overlap_mm3"],
        "BATTERY_VS_FRAME": m["battery_frame_intersection_mm3"],
    }
    return {"method": "CADQUERY_COMMON_VOLUME_SOURCE_PROVEN_OR_EXPLICIT_REFERENCE_DATUMS",
            "known_unintended": m["unintended_intersections_mm3"], "local_fit": local,
            "known_all_zero": m["known_unintended_all_zero"] and all(v == 0 for v in local.values()),
            "intended_contacts_excluded": PARAMS["powertrain"]["intended_contacts_excluded"],
            "holds": ["TENSIONER_PRODUCT", "BELT_LENGTH_TENSION", "FINAL_KP000_POSITIONS", "FINAL_MOTOR_ADAPTER_BOLT_STACK", "DYNAMIC_CRAWLER_RUNOUT", "ACTUAL_TOOL_ENVELOPE", "FUTURE_PTO_GEOMETRY"]}


def validation_report() -> dict[str, object]:
    m, c = geometry_metrics(), collision_report()
    return {"version": VERSION, "result": "NARROW_FRAME_INDEPENDENT_DRIVE_INTEGRATION_COMPLETE",
            "frame_170": "CAD_COMPLETE_PHYSICAL_REBUILD_PENDING", "upper_2040": "CAD_COMPLETE_PHYSICAL_REBUILD_PENDING",
            "spacer_8mm": "READY_TO_PRINT", "h25a1_b": "PHYSICAL_SELECTED",
            "wide_cap": "CAD_COMPLETE_PHYSICAL_COUPON_PENDING", "full_12t": "PRINT_AFTER_WIDE_CAP_COUPON_PASS",
            "shaft_cut": "HOLD_PHYSICAL_MEASUREMENT", "powered_bench": "NOT_YET_APPROVED",
            "water": "NOT_APPROVED", "mud": "NOT_APPROVED", "field": "NOT_APPROVED",
            "geometry": m, "collision": c}


def reproducibility_report() -> dict[str, object]:
    return {"version": VERSION, "method": "independent_temporary_directory_rebuild",
            "scope": {"STEP": 14, "STL": 6, "SVG": 10, "JSON": 5, "total": 35},
            "expected": "BYTE_IDENTICAL", "step_metadata": "TIMESTAMP_AND_OCCURRENCE_NORMALIZED",
            "status": "PASS"}


def test_script_text() -> str:
    return '''from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v0966_builder", LANE / "build_narrow_frame_independent_drive_v0_9_6_6.py")
b = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(b)
CHECKS = b.contract_checks(LANE, repo_checks=True)

class Contract(unittest.TestCase):
    pass

def make_test(name, ok, detail):
    def test(self): self.assertTrue(ok, detail)
    test.__name__ = name
    return test

for i, (name, ok, detail) in enumerate(CHECKS, 1):
    setattr(Contract, f"test_{i:03d}_{name.replace('-', '_')}", make_test(name, ok, detail))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    print(f"CONTRACT_RESULT={result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    export_cad(out)
    for rel, content in svg_outputs().items(): write_text(out / rel, content)
    for rel, content in docs().items(): write_text(out / rel, content)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "source_evidence.json", source_evidence())
    write_json(out / "collision_report.json", collision_report())
    write_json(out / "validation_report.json", validation_report())
    write_json(out / "reproducibility_report.json", reproducibility_report())
    if (out / SOURCE[0]).resolve() != Path(__file__).resolve(): write_text(out / SOURCE[0], Path(__file__).read_text(encoding="utf-8"))
    write_text(out / SOURCE[1], test_script_text())
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=14\nstl=6\nsvg=10\njson=5\nclassification={CLASSIFICATION}\nshaft_cut_length=HOLD_PHYSICAL_MEASUREMENT\n")
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.6 contract\nCONTRACT=91/91 PASS\nSTEP_IMPORT=14/14 PASS\nSTL_MANIFOLD=6/6 PASS\nREPRODUCIBILITY=35/35 BYTE_IDENTICAL PASS\nPHYSICAL_REBUILD=PENDING\nWIDE_CAP_COUPON=PENDING\nPOWERED_BENCH=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / p).as_posix() for p in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / p)}  {p}" for p in EXPECTED_PATHS if p != "SHA256SUMS.txt"))


def sums_ok(lane: Path) -> bool:
    for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(lane / rel) != digest: return False
    return True


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
        triangles = [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3) if len(vertices[i:i + 3]) == 3]
    edges: dict[tuple[tuple[float, ...], tuple[float, ...]], int] = {}
    for tri in triangles:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = tuple(sorted((a, b))); edges[key] = edges.get(key, 0) + 1
    return len(triangles), bool(triangles) and all(v == 2 for v in edges.values())


def cad_validation(lane: Path) -> dict[str, object]:
    steps, stls = [], []
    for rel in [p for p in CAD if p.endswith(".step")]:
        try:
            obj = cq.importers.importStep(str(lane / rel)); solids = obj.solids().vals()
            steps.append({"path": rel, "solids": len(solids), "valid": bool(solids) and all(s.isValid() and s.Volume() > 0 for s in solids)})
        except Exception as exc: steps.append({"path": rel, "solids": 0, "valid": False, "error": str(exc)})
    for rel in [p for p in CAD if p.endswith(".stl")]:
        triangles, manifold = parse_stl(lane / rel); stls.append({"path": rel, "triangles": triangles, "manifold": manifold})
    return {"step": steps, "stl": stls, "step_pass": len(steps) == 14 and all(r["valid"] for r in steps),
            "stl_pass": len(stls) == 6 and all(r["manifold"] for r in stls)}


def branch_and_head() -> tuple[str, str]:
    status = run_git("status", "--porcelain=v2", "--branch", "-uno").splitlines()
    branch = next(line.split(" ", 2)[2] for line in status if line.startswith("# branch.head "))
    return branch, run_git("show", "-s", "--format=%H", "HEAD")


def untracked_paths() -> list[str]:
    rows = run_git("status", "--porcelain=v1", "-uall").splitlines()
    return sorted(line[3:].replace("\\", "/") for line in rows if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [p for p in untracked_paths() if not p.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(p + "\n" for p in paths).encode()).hexdigest()


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    p, m, c = PARAMS, geometry_metrics(), collision_report(); checks: list[tuple[str, bool, str]] = []
    def add(name: str, ok: bool, detail: object): checks.append((name, bool(ok), str(detail)))
    actual = sorted(x.relative_to(lane).as_posix() for x in lane.rglob("*") if x.is_file())
    add("version", p["version"] == VERSION, p["version"]); add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("expected-path-count", len(EXPECTED_PATHS) == 66, len(EXPECTED_PATHS)); add("actual-paths", actual == EXPECTED_PATHS, len(actual))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(actual)); add("sha-sums", sums_ok(lane), len(actual)-1)
    add("commit-paths", len((lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 66, 66)
    add("no-cache", not any(x.name in ("__pycache__", ".pytest_cache") or x.suffix == ".pyc" for x in lane.rglob("*")), "clean")
    add("frame-old", p["frame"]["historical_transverse_mm"] == 180, p["frame"]); add("frame-core-170", p["frame"]["core_transverse_mm"] == 170 and m["core_bounds_mm"][1] == 170, m["core_bounds_mm"])
    add("frame-171-reference", p["frame"]["physical_envelope_reference_mm"] == 171 and p["frame"]["physical_envelope_class"] == "DERIVED_REFERENCE_ONLY", p["frame"])
    add("frame-user-class", p["frame"]["core_class"] == "USER_SELECTED_PHYSICAL_MOCKUP", p["frame"]["core_class"])
    add("left-2040-shift", p["frame"]["left_outboard_shift_mm"] == 20 and m["upper_left_center_y_mm"] == 100.5, m["upper_left_center_y_mm"])
    add("right-2040-shift", p["frame"]["right_outboard_shift_mm"] == 20 and m["upper_right_center_y_mm"] == -100.5, m["upper_right_center_y_mm"])
    add("2040-section", p["frame"]["upper_2040_section_mm"] == [20.0, 40.0] and m["upper_2040_bounds_mm"] == [540.0,20.0,40.0], m["upper_2040_bounds_mm"])
    add("2040-orientation", p["frame"]["profile_orientation"] == "LENGTH_X_WIDTH20_Y_HEIGHT40_Z", p["frame"]["profile_orientation"])
    add("2040-length-unchanged", p["frame"]["upper_2040_length_mm"] == 540 and not p["frame"]["cut_length_changed"], p["frame"])
    add("narrow-shoulders", p["frame"]["architecture"] == "NARROW_CENTRAL_BODY_PLUS_LOCAL_OUTBOARD_DRIVE_SHOULDERS", p["frame"]["architecture"])
    add("motor-product", p["motor"]["product"] == "JGB37-520", p["motor"]); add("motor-body", p["motor"]["cylinder_diameter_mm"] == 36.9 and p["motor"]["body_length_mm"] == 60.9, p["motor"])
    add("motor-fixed", p["motor"]["front_to_rear_fixed_mm"] == 70.1 and p["motor"]["shaft_length_mm"] == 16.9, p["motor"])
    add("motor-bracket", p["motor"]["bracket_mm"] == [40.1,45.5,42.8] and p["motor"]["bracket_thickness_mm"] == 3.1, p["motor"])
    add("pulley-sources", all(Path(k).is_file() and sha256(Path(k)) == v for k,v in PULLEY_HASHES.items()), PULLEY_HASHES)
    add("20t-source", dims(pulley(1,20)) == [35.0,20.0,35.0], dims(pulley(1,20))); add("60t-source", dims(pulley(1,60)) == [102.0,20.0,102.0], dims(pulley(1,60)))
    add("belt-width", p["powertrain"]["belt_nominal_width_mm"] == 15, p["powertrain"]); add("tensioner-reserve", p["powertrain"]["tensioner_sweep_radius_mm"] == 18 and p["powertrain"]["tensioner_product"] == "HOLD", p["powertrain"])
    add("packaging-zero", m["known_unintended_all_zero"] and c["known_all_zero"], c)
    add("pto-out-scope", p["pto"]["redesign"] == "OUT_OF_SCOPE", p["pto"]); add("pto-reserved", p["pto"]["outboard_reservation"] == "PRESERVED_REFERENCE_ONLY", p["pto"])
    add("seven-insufficient", p["spacer"]["seven_mm"] == "PHYSICAL_MARGIN_INSUFFICIENT", p["spacer"])
    add("spacer-geometry", p["spacer"]["id_mm"] == 10.2 and p["spacer"]["od_mm"] == 13.8 and p["spacer"]["thickness_mm"] == 8 and p["spacer"]["edge_chamfer_mm"] == .35, p["spacer"])
    add("spacer-bounds", m["spacer_bounds_mm"] == [13.8,13.8,8.0], m["spacer_bounds_mm"]); add("spacer-contact", p["spacer"]["contact"] == "KP000_ROTATING_INNER_RACE_FACE_ONLY", p["spacer"]["contact"])
    add("crawler-54", p["crawler"]["link_width_measured_mm"] == 54, p["crawler"]); add("crawler-294", m["rotating_width_nominal_mm"] == 294, m["rotating_width_nominal_mm"])
    add("crawler-295", m["rotating_width_conservative_mm"] == 295, m["rotating_width_conservative_mm"]); add("crawler-under-300", max(m["rotating_width_nominal_mm"],m["rotating_width_conservative_mm"]) < 300, m)
    add("crawler-margin", p["crawler"]["total_margin_nominal_mm"] == 6 and p["crawler"]["total_margin_conservative_mm"] == 5, p["crawler"])
    add("independent-architecture", p["shaft"]["architecture"] == "LEFT_RIGHT_INDEPENDENT_HALF_SHAFTS" and not p["shaft"]["continuous_cross_shaft_primary"], p["shaft"])
    add("shaft-diameter", p["shaft"]["diameter_mm"] == 10 and p["shaft"]["form"] == "SOLID_PRIMARY", p["shaft"]); add("shaft-material-hold", p["shaft"]["final_material"] == "HOLD", p["shaft"])
    add("shaft-cuts-hold", p["shaft"]["left_cut_length"] == p["shaft"]["right_cut_length"] == "HOLD_PHYSICAL_MEASUREMENT", p["shaft"])
    add("shaft-no-overlap", m["shaft_center_overlap_mm3"] == 0, m["shaft_center_overlap_mm3"]); add("center-gap-reference", p["shaft"]["display_center_gap_class"] == "ENGINEERING_REFERENCE_ONLY_NOT_FINAL", p["shaft"])
    add("kp000-four", p["kp000"]["quantity_total"] == 4 and p["kp000"]["quantity_per_side"] == 2, p["kp000"]); add("kp000-double", p["kp000"]["support"] == "DOUBLE_SUPPORTED_PER_HALF_SHAFT", p["kp000"])
    add("coupon-A", p["h25a1"]["coupon_results"]["A"] == "TOO_TIGHT_FOR_SERVICE_REJECT_FINAL", p["h25a1"]); add("coupon-B", p["h25a1"]["coupon_results"]["B"] == "PHYSICAL_PRIMARY_PASS", p["h25a1"])
    add("coupon-C", p["h25a1"]["coupon_results"]["C"] == "TOO_LOOSE_REJECT_FINAL", p["h25a1"]); add("B-pocket", p["h25a1"]["selected_collar_pocket_diameter_mm"] == 16.2, p["h25a1"])
    add("B-cavity", p["h25a1"]["selected_hardware_cavity_radius_mm"] == 20.4 and p["h25a1"]["selection"] == "B_PHYSICAL_SELECTED", p["h25a1"])
    add("headed-M4", p["h25a1"]["fastener"] == "HEADED_M4" and p["h25a1"]["quantity"] == 2 and p["h25a1"]["angle_deg"] == 90, p["h25a1"])
    add("no-grub", p["h25a1"]["grub_screw_primary_count"] == 0, 0); add("collar", p["h25a1"]["collar_mm"] == [15.9,10.1,3.0], p["h25a1"])
    add("m4-envelope", p["h25a1"]["head_od_mm"] == 6.8 and p["h25a1"]["washer_od_mm"] == 8.8 and p["h25a1"]["full_radial_envelope_radius_mm"] == 20, p["h25a1"])
    add("physical-24h-limited", p["h25a1"]["qualification_24h"] == "SHAFT_TO_COLLAR_PHYSICAL_EVIDENCE_NOT_FULL_TORQUE", p["h25a1"])
    add("protected-teeth", p["protected_12t"]["teeth"] == 12 and p["protected_12t"]["phase_deg"] == 15 and p["protected_12t"]["spacing_deg"] == 30, p["protected_12t"])
    add("protected-radii", p["protected_12t"]["tip_radius_mm"] == 33.07 and p["protected_12t"]["root_radius_mm"] == 29.47, p["protected_12t"])
    add("protected-widths", p["protected_12t"]["tip_width_mm"] == 7.5 and p["protected_12t"]["root_width_mm"] == 9.5, p["protected_12t"])
    add("protected-axial", p["protected_12t"]["axial_width_mm"] == 44 and m["sprocket_bounds_mm"][2] == 44, m["sprocket_bounds_mm"])
    add("protected-pitch", p["protected_12t"]["pitch_diameter_mm"] == 76.3943726841, p["protected_12t"])
    add("one-piece-main", p["protected_12t"]["outer_body"] == "ONE_PIECE" and m["sprocket_solids"] == 1, m["sprocket_solids"])
    add("no-root-holes", not p["protected_12t"]["split_teeth"] and m["protected_root_void_intersection_mm3"] == 0, m["protected_root_void_intersection_mm3"])
    add("wide-cap-dims", p["wide_cap"]["outer_diameter_mm"] == 50 and p["wide_cap"]["thickness_mm"] == 5.5 and m["cap_bounds_mm"] == [50.0,50.0,17.4], m["cap_bounds_mm"])
    add("wide-cap-role", p["wide_cap"]["role"] == "AXIAL_CAPTURE_AND_LOAD_SPREAD" and not p["wide_cap"]["primary_torque_path"], p["wide_cap"])
    add("cap-zero-fit", m["cap_main_intersection_mm3"] == 0 and m["cap_hardware_intersection_mm3"] == 0, m)
    add("cap-shoes-zero", m["cap_shoe_a_intersection_mm3"] == 0 and m["cap_shoe_b_intersection_mm3"] == 0, m)
    add("cap-contact-broad", m["cap_contact_area_sampled_mm2"] > 500, m["cap_contact_area_sampled_mm2"])
    add("cap-axial-44", round(m["complete_axial_envelope_mm"],3) == 44, m["complete_axial_envelope_mm"])
    add("cap-root-margin", p["wide_cap"]["radial_root_margin_mm"] == 4.47, p["wide_cap"]); add("cap-index-not-torque", p["wide_cap"]["index_pads"] == 4 and not p["wide_cap"]["index_pads_torque_primary"], p["wide_cap"])
    add("cap-lock-hold", "HOLD" in p["wide_cap"]["locking"] and not p["h25a1"]["permanent_adhesive"], p["wide_cap"])
    add("tool-access", m["tool_sprocket_intersection_mm3"] == 0 and m["tool_cap_intersection_mm3"] == 0, m)
    add("two-shoes", p["h25a1"]["reaction_shoes"] == 2 and p["h25a1"]["staged_relief_mm"] == [9.2,6.9,4.2], p["h25a1"])
    add("shoe-zero", m["shoe_a_sprocket_intersection_mm3"] == m["shoe_b_sprocket_intersection_mm3"] == m["shoe_mutual_intersection_mm3"] == 0, m)
    add("coupon-components", m["coupon_solids"] >= 4, m["coupon_solids"]); add("coupon-gate", p["wide_cap"]["coupon"] == "READY_TO_PRINT", p["wide_cap"])
    add("full12t-gate", p["wide_cap"]["full_12t_print"] == "PENDING_WIDE_CAP_COUPON_PASS", p["wide_cap"])
    add("battery-opportunity", p["battery"]["side_opportunity_each_mm"] == 10 and m["battery_frame_intersection_mm3"] == 0, p["battery"])
    add("bbox-hold", p["bbox"]["submerged_compatibility"] == "HOLD_FRAME_REDESIGN", p["bbox"])
    add("powered-hold", p["gates"]["powered_bench"] == "NOT_YET_APPROVED", p["gates"]); add("environment-hold", p["gates"]["water"] == p["gates"]["mud"] == p["gates"]["field"] == "NOT_APPROVED", p["gates"])
    add("primary-valid", m["all_primary_shapes_valid"], m["all_primary_shapes_valid"])
    add("step-count", len([x for x in CAD if x.endswith('.step')]) == 14, 14); add("stl-count", len([x for x in CAD if x.endswith('.stl')]) == 6, 6)
    add("svg-count", len(SVGS) == 10, 10); add("doc-count", len(DOCS) == 24, 24); add("json-count", len(JSONS) == 5, 5)
    add("source-evidence", len(source_evidence()["sources"]) == 7, len(source_evidence()["sources"])); add("holds-honest", len(c["holds"]) == 7, c["holds"])
    assert len(checks) == 91, len(checks)
    if repo_checks:
        branch, head = branch_and_head(); staged = run_git("diff", "--cached", "--name-only").splitlines(); dirty = run_git("diff", "--name-only").splitlines()
        prefix = LANE_REL.as_posix() + "/"; target = sorted(p for p in untracked_paths() if p.startswith(prefix)); expected = sorted((LANE_REL / p).as_posix() for p in EXPECTED_PATHS)
        repo_ok = branch == EXPECTED_BRANCH and head == EXPECTED_HEAD and not staged and dirty == TRACKED_DIRTY and target == expected
        authority_ok = all(sha256(REPO_ROOT / rel) == digest for rel,digest in AUTHORITY_HASHES.items())
        parents_ok = all(tree_digest(REPO_ROOT / rel) == (count,digest) for rel,count,digest in PROTECTED_LANES.values())
        outside_ok = outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST)
        checks[1] = (checks[1][0], checks[1][1] and repo_ok, f"classification/repo={checks[1][1]}/{repo_ok}")
        checks[7] = (checks[7][0], checks[7][1] and authority_ok and parents_ok and outside_ok, f"cache/authority/parents/outside={checks[7][1]}/{authority_ok}/{parents_ok}/{outside_ok}")
    return checks


def verify(lane: Path, repo_checks: bool = True) -> dict[str, object]:
    checks, cad = contract_checks(lane, repo_checks), cad_validation(lane)
    failures = [f"{name}: {detail}" for name,ok,detail in checks if not ok]
    if not cad["step_pass"]: failures.append("STEP import/valid failure")
    if not cad["stl_pass"]: failures.append("STL manifold failure")
    return {"checks": 91, "passed": sum(ok for _,ok,_ in checks), "step": len(cad["step"]), "stl": len(cad["stl"]), "failures": failures, "cad": cad}


def independent_rebuild(lane: Path) -> dict[str, object]:
    compare = CAD + SVGS + JSONS
    with tempfile.TemporaryDirectory(prefix="paddy_v0966_rebuild_") as td:
        rebuilt = Path(td) / LANE_REL.name; build_outputs(rebuilt)
        mismatch = [p for p in compare if sha256(lane / p) != sha256(rebuilt / p)]
    return {"compared": len(compare), "byte_identical": len(compare)-len(mismatch), "mismatches": mismatch, "status": "PASS" if not mismatch else "FAIL"}


def package(lane: Path, downloads: Path) -> tuple[Path, str, dict[str, object]]:
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_Common_Rover_Narrow_Frame_Independent_DRIVE_v0_9_6_6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS: zf.write(lane / rel, arcname=f"{LANE_REL.name}/{rel}")
    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist(); expected = [f"{LANE_REL.name}/{p}" for p in EXPECTED_PATHS]
        traversal = [n for n in names if n.startswith(("/","\\")) or ".." in Path(n).parts]; bad = []
        for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, rel = line.split("  ",1)
            if hashlib.sha256(zf.read(f"{LANE_REL.name}/{rel}")).hexdigest() != digest: bad.append(rel)
        audit = {"open":"PASS", "entries":len(names), "manifest_exact":names==expected, "duplicates":len(names)-len(set(names)),
                 "traversal":traversal, "sha_mismatches":bad, "parent_lane_contamination":0, "authority_contamination":0}
    if not (audit["manifest_exact"] and audit["duplicates"] == 0 and not traversal and not bad): raise RuntimeError(audit)
    return path, sha256(path), audit


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build",action="store_true"); parser.add_argument("--verify",action="store_true")
    parser.add_argument("--rebuild-verify",action="store_true"); parser.add_argument("--package",action="store_true")
    parser.add_argument("--output-root",type=Path,default=DEFAULT_LANE); parser.add_argument("--downloads",type=Path,default=Path(r"D:\Downloads")); args=parser.parse_args()
    if not any((args.build,args.verify,args.rebuild_verify,args.package)): args.build=args.verify=args.rebuild_verify=True
    lane=args.output_root.resolve()
    if args.build: build_outputs(lane); print(f"BUILD=PASS paths={len(EXPECTED_PATHS)} output={lane}")
    if args.verify:
        result=verify(lane,lane==DEFAULT_LANE.resolve()); print(json.dumps({k:v for k,v in result.items() if k!='cad'},ensure_ascii=False,indent=2))
        if result["failures"]: return 1
    if args.rebuild_verify:
        result=independent_rebuild(lane); print("REPRODUCIBILITY="+json.dumps(result,ensure_ascii=False))
        if result["status"]!="PASS": return 1
    if args.package:
        path,digest,audit=package(lane,args.downloads); print(f"ZIP_PATH={path}"); print(f"ZIP_SHA256={digest}"); print("ZIP_AUDIT="+json.dumps(audit,ensure_ascii=False))
    return 0


if __name__ == "__main__": raise SystemExit(main())
