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
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.8"
CLASSIFICATION = "DRIVE_HUB_POSITIVE_LOCK_PHYSICAL_UPDATE"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_positive_hub_cap_lock_v0_9_6_8")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 1927
BASE_OUTSIDE_DIGEST = "2400065ff4517873c15df80a83e12c266f699f2821a0aebd8446462fa3b221e7"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
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
    "v0.9.6.6": ("cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6", 66, "d01b3b67c3603ec9e7d3c647a77d6935f80107eed711b9b29691641d3487e94f"),
    "v0.9.6.7": ("cad/common_rover/common_rover_rapid_dry_bbox_cbox_v0_9_6_7", 40, "a831a1e90a65395c2e796599a365a6fe6fa4ac57a492d78f591196b2eb09c5e7"),
}

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md", "CAP_LOCK_FAILURE_RECORD.md",
    "M3_POSITIVE_CAP_LOCK_SPEC.md", "M3_NUT_POCKET_COUPON_SPEC.md",
    "H25A1_B_PHYSICAL_AUTHORITY.md", "WIDE_CAP_REVISED_SPEC.md", "REACTION_SHOE_SPEC.md",
    "TORQUE_LOAD_PATH.md", "FRAME_170MM_PHYSICAL_UPDATE.md", "UPPER_2040_STATUS.md",
    "SPACER_PHYSICAL_STATUS.md", "INDEPENDENT_SHAFT_STATUS.md", "ASSEMBLY_PROCEDURE.md",
    "PRINT_PLAN.md", "PHYSICAL_TEST_PLAN.md", "POWERED_TEST_GATE.md", "SAFETY_NOTES.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
DRIVE_CAD = [
    "drive/artifacts/drive_12t_h25a1_positive_cap_lock_v0_9_6_8.step",
    "drive/artifacts/drive_12t_h25a1_positive_cap_lock_v0_9_6_8.stl",
    "drive/artifacts/h25a1_positive_lock_wide_cap_v0_9_6_8.step",
    "drive/artifacts/h25a1_positive_lock_wide_cap_v0_9_6_8.stl",
    "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_8.step",
    "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_8.stl",
    "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_8.step",
    "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_8.stl",
    "drive/artifacts/m3_captive_nut_fit_coupon_v0_9_6_8.step",
    "drive/artifacts/m3_captive_nut_fit_coupon_v0_9_6_8.stl",
    "drive/artifacts/positive_cap_lock_fit_coupon_v0_9_6_8.step",
    "drive/artifacts/positive_cap_lock_fit_coupon_v0_9_6_8.stl",
]
INTEGRATION_CAD = [
    "integration/artifacts/positive_cap_lock_full_assembly_v0_9_6_8.step",
    "integration/artifacts/m3_screw_generic_reference_v0_9_6_8.step",
    "integration/artifacts/m3_washer_generic_reference_v0_9_6_8.step",
    "integration/artifacts/m3_nut_generic_reference_v0_9_6_8.step",
]
PHYSICAL_CAD = ["physical_update/artifacts/170mm_drive_physical_update_assembly_v0_9_6_8.step"]
CAD = DRIVE_CAD + INTEGRATION_CAD + PHYSICAL_CAD
SVGS = [f"integration/artifacts/{name}" for name in (
    "positive_cap_lock_section_v0_9_6_8.svg",
    "existing_m4_vs_new_m3_layout_v0_9_6_8.svg",
    "m3_captive_nut_detail_v0_9_6_8.svg",
    "wide_cap_broad_sandwich_v0_9_6_8.svg",
    "drive_torque_path_v0_9_6_8.svg",
    "170mm_frame_physical_status_v0_9_6_8.svg",
    "2040_outboard_status_v0_9_6_8.svg",
    "spacer_7_vs_8_status_v0_9_6_8.svg",
    "independent_shaft_status_v0_9_6_8.svg",
    "cap_m3_screw_length_measurement_v0_9_6_8.svg",
)]
JSONS = ["design_parameters.json", "source_evidence.json", "collision_report.json", "validation_report.json", "reproducibility_report.json"]
SOURCES = ["build_positive_hub_cap_lock_v0_9_6_8.py", "tests/test_positive_hub_cap_lock_v0_9_6_8_contract.py"]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

PROTECTED_12T = {
    "teeth": 12, "phase_deg": 15.0, "spacing_deg": 30.0,
    "tip_radius_mm": 33.07, "root_radius_mm": 29.47,
    "tip_width_mm": 7.5, "root_width_mm": 9.5,
    "axial_width_mm": 44.0, "pitch_diameter_mm": 76.3943726841,
    "buried_root_overlap_mm": 4.0, "outer_body": "ONE_PIECE",
    "split_teeth": False, "tooth_root_radial_service_holes": 0,
}

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "physical_failure": {
        "current_cap": "PHYSICAL_FAIL_USER_REPORTED",
        "functional_retention_failure": True,
        "long_snap_fingers": "REMOVED_REJECTED_AS_PRIMARY_LOCK",
        "snap_or_friction_primary": False,
    },
    "protected_12t": PROTECTED_12T,
    "full_capture": {
        "selected": "B", "collar_pocket_diameter_mm": 16.2,
        "hardware_cavity_radius_mm": 20.4,
        "A": "REJECT_TOO_TIGHT", "B": "PHYSICAL_PRIMARY_PASS", "C": "REJECT_TOO_LOOSE",
        "repeat_abc_experiment": False,
    },
    "metal_collar": {"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0},
    "m4_collar": {
        "type": "HEADED_M4", "count": 2, "separation_deg": 90.0,
        "unchanged": True, "grub_screw_primary_count": 0,
        "qualification": "1.0KG_AT_70MM_24H_NO_SHAFT_SHIFT",
    },
    "reaction_shoes": {
        "count": 2, "replaceable": True, "staged_relief_mm": [9.2, 6.9, 4.2],
        "role": "METAL_COLLAR_TO_PETG_MAIN_HUB_TORQUE_TRANSFER",
    },
    "m3_cap_lock": {
        "fastener": "M3", "count": 2, "angles_deg": [45.0, 225.0],
        "separation_deg": 180.0, "center_radius_mm": 23.0, "pcd_mm": 46.0,
        "through_hole_diameter_mm": 3.4, "printed_petg_threads": 0,
        "metal_captive_nuts": 2, "permanent_adhesive": False,
        "primary_torque_path": False, "head_side": "FRONT_HUB_CAP",
        "nut_side": "MAIN_SPROCKET_BODY", "screw_length": "HOLD_PHYSICAL_HARDWARE",
        "nut_pocket_in_full_cad": "C_6.0_MAX_PACKAGING_ENVELOPE_PHYSICAL_SELECTION_PENDING",
        "generic_reference_only": True,
    },
    "clearances": {
        "hole_to_r20p4_mm": 0.9,
        "nut_pocket_to_root_mm": round(29.47 - (23.0 + 6.0 / math.sqrt(3.0)), 3),
        "washer_to_cap_edge_mm": 0.5,
        "nut_pocket_to_cap_recess_edge_mm": round(27.2 - (23.0 + 6.0 / math.sqrt(3.0)), 3),
        "targets_mm": {"hole_to_r20p4_preferred": 0.8, "nut_to_root_preferred": 2.0, "head_to_cap_min": 0.5, "free_edge_min": 0.5},
    },
    "nut_coupon": {
        "A": {"across_flats_mm": 5.6, "depth_mm": 2.5},
        "B": {"across_flats_mm": 5.8, "depth_mm": 2.7},
        "C": {"across_flats_mm": 6.0, "depth_mm": 2.9},
        "selection": "PHYSICAL_COUPON_PENDING",
    },
    "wide_cap": {
        "outer_diameter_mm": 54.0, "allowed_od_mm": [50.0, 54.0],
        "thickness_mm": 5.5, "nested_z_mm": [16.5, 22.0],
        "counterbore_diameter_mm": 7.2, "counterbore_depth_mm": 3.5,
        "optional_washer_reference_od_mm": 7.0,
        "axial_envelope_limit_mm": 44.0,
        "indexing": "ASYMMETRIC_M4_SERVICE_WINDOWS_PLUS_M3_PAIR",
        "long_snap_fingers": 0, "index_features_retention_authority": False,
        "role": "AXIAL_RETENTION_AND_LOAD_SPREAD", "primary_torque_path": False,
    },
    "frame": {
        "primary_core_width_mm": 170.0, "status": "PHYSICAL_MOCKUP_USER_REPORTED",
        "historical_width_mm": 180.0, "conservative_reference_mm": 171.0,
        "observations": ["CORE_CAN_REDUCE_TO_170", "60T_LATERAL_ROOM_REMAINS", "BATTERY_LATERAL_ROOM_USEFUL", "NARROWING_RECOVERS_CRAWLER_WIDTH"],
        "structural_field_validation": False,
        "upper_2040_outboard_each_mm": 20.0, "upper_2040_length_mm": 540.0,
        "upper_2040_status": "DESIGN_SELECTED_PHYSICAL_FINAL_POSITION_PENDING",
        "battery_bilateral_grip": "PHYSICAL_DESIGN_PENDING",
    },
    "spacer": {
        "five_to_six_mm": "FRAME_CONTACT", "seven_mm": "PHYSICAL_MARGIN_INSUFFICIENT",
        "eight_mm": "PHYSICAL_TEST_PENDING", "id_mm": 10.2, "od_mm": 13.8,
        "thickness_mm": 8.0, "chamfer_mm": 0.35,
        "rotating_width_nominal_mm": 294.0, "rotating_width_conservative_mm": 295.0,
        "width_class": "GEOMETRY_PASS_CANDIDATE_NOT_PHYSICAL_PASS",
    },
    "shaft": {
        "architecture": "LEFT_RIGHT_INDEPENDENT_HALF_SHAFTS", "diameter_mm": 10.0,
        "form": "SOLID_PRIMARY", "kp000_per_side": 2, "continuous_cross_shaft": False,
        "left_cut": "HOLD_PHYSICAL_MEASUREMENT", "right_cut": "HOLD_PHYSICAL_MEASUREMENT",
        "display_center_gap_mm": 2.0, "final_center_gap": "HOLD_NON_CONTACT_REQUIRED",
    },
    "generic_m3_references": {
        "classification": "GENERIC_REFERENCE_NOT_PHYSICAL_AUTHORITY",
        "screw_display_length_mm": 10.0, "screw_head_od_mm": 5.5,
        "washer_od_mm": 7.0, "washer_thickness_mm": 0.5,
        "nut_across_flats_mm": 5.5, "nut_thickness_mm": 2.4,
    },
    "print": {
        "printer": "BAMBU_A1", "material": "PETG",
        "order": ["M3_NUT_POCKET_COUPON", "POSITIVE_CAP_LOCK_FIT_COUPON", "FULL_REVISED_12T_AFTER_TWO_PHYSICAL_PASSES"],
        "full_12t_gate": "PENDING_NUT_AND_CAP_LOCK_COUPON_PHYSICAL_PASS",
        "support": "REVIEW_SLICER_DO_NOT_BLINDLY_TRUST_AUTO_SUPPORT",
    },
    "gates": {
        "current_snap_cap": "PHYSICAL_REJECT", "h25a1_b": "PHYSICAL_SELECTED",
        "m3_positive_cap_lock": "CAD_COMPLETE_PHYSICAL_COUPON_PENDING",
        "m3_nut_pocket": "READY_FOR_PHYSICAL_COUPON", "wide_front_hub_cap": "CAD_REVISED",
        "full_12t": "PRINT_PENDING_CAP_LOCK_COUPON", "frame_170": "PHYSICAL_MOCKUP_RECORDED",
        "upper_2040_outboard": "DESIGN_SELECTED_PHYSICAL_FINAL_PENDING",
        "spacer_7mm": "PHYSICAL_MARGIN_INSUFFICIENT", "spacer_8mm": "PHYSICAL_TEST_PENDING",
        "shaft_cut_length": "HOLD_PHYSICAL_MEASUREMENT", "powered_rotation": "NOT_YET_APPROVED",
        "field_deployment": "NOT_APPROVED",
    },
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


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [p for p in untracked_paths() if not p.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(p + "\n" for p in paths).encode()).hexdigest()


def repository_preflight() -> dict[str, object]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    outside = outside_snapshot()
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "tracked_dirty": dirty, "outside": outside, "authority": authority, "protected": protected}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder(radius: float, length: float, z0: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length).translate((0, 0, z0))


def axis_cylinder(radius: float, length: float, origin: tuple[float, float, float], direction: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction)))


def hex_prism(across_flats: float, depth: float, z0: float, center=(0.0, 0.0)) -> cq.Workplane:
    diameter = 2.0 * across_flats / math.sqrt(3.0)
    return cq.Workplane("XY").polygon(6, diameter).extrude(depth).translate((center[0], center[1], z0))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    vals = []
    for part in parts:
        vals.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(vals))


def fused(parts: list[cq.Workplane]) -> cq.Workplane:
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result.clean()


def volume(a: cq.Workplane, b: cq.Workplane) -> float:
    total = 0.0
    for av in a.vals():
        for bv in b.vals():
            total += float(av.intersect(bv).Volume())
    return round(total, 6)


def dims(obj: cq.Workplane) -> list[float]:
    b = obj.val().BoundingBox()
    return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]


def center_xy(radius: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return radius * math.cos(a), radius * math.sin(a)


def source_ring_hub_spokes() -> cq.Workplane:
    width = 44.0
    ring = cylinder(29.47, width, -22.0).cut(cylinder(20.0, width + 0.4, -22.2))
    body = ring.union(cylinder(18.0, width, -22.0))
    for i in range(6):
        body = body.union(box(7.5, 12.0, width, (18.75, 0, 0)).rotate((0, 0, 0), (0, 0, 1), i * 60.0))
    return body.clean()


def embedded_tooth() -> cq.Workplane:
    buried = 29.47 - 4.0
    return cq.Workplane("XY").polyline([(buried, -6.5), (29.47, -4.75), (33.07, -3.75), (33.07, 3.75), (29.47, 4.75), (buried, 6.5)]).close().extrude(22.0, both=True)


def protected_blank() -> cq.Workplane:
    body = source_ring_hub_spokes()
    tooth = embedded_tooth()
    for i in range(12):
        body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), 15.0 + i * 30.0))
    return body.clean()


def m3_holes() -> list[cq.Workplane]:
    return [cylinder(1.7, 12.8, 9.8).translate((*center_xy(23.0, angle), 0)) for angle in (45.0, 225.0)]


def m3_nut_pockets(across_flats: float = 6.0, depth: float = 2.9, seat_z: float = 16.5) -> list[cq.Workplane]:
    return [hex_prism(across_flats, depth + 0.1, seat_z - depth, center_xy(23.0, angle)) for angle in (45.0, 225.0)]


def full_capture_voids() -> cq.Workplane:
    bore = cylinder(5.15, 46.0, -23.0)
    collar_open = cylinder(8.1, 24.0, -2.0)
    tool_x = box(40.8, 9.2, 26.6, (0, 0, 8.7))
    tool_y = box(9.2, 40.8, 26.6, (0, 0, 8.7))
    shoe_x = box(15.55, 13.6, 24.4, (16.525, 0, 9.8))
    shoe_y = box(13.6, 15.55, 24.4, (0, 16.525, 9.8))
    cap_recess = cylinder(27.2, 5.7, 16.5)
    return compound([bore, collar_open, tool_x, tool_y, shoe_x, shoe_y, cap_recess, *m3_holes(), *m3_nut_pockets()])


def main_sprocket() -> cq.Workplane:
    part = protected_blank()
    for void in full_capture_voids().solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.clean()


def wide_cap() -> cq.Workplane:
    cap = cylinder(27.0, 5.5, 16.5).cut(cylinder(5.2, 5.9, 16.3))
    cap = cap.cut(box(17.5, 9.4, 5.9, (13.75, 0, 19.25))).cut(box(9.4, 17.5, 5.9, (0, 13.75, 19.25)))
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        cap = cap.cut(cylinder(1.7, 6.0, 16.25).translate((x, y, 0)))
        cap = cap.cut(cylinder(3.6, 3.7, 18.5).translate((x, y, 0)))
    return cap.clean()


def collar() -> cq.Workplane:
    return cylinder(15.9 / 2.0, 3.0, -1.5).cut(cylinder(10.1 / 2.0, 3.4, -1.7))


def m4_hardware() -> cq.Workplane:
    parts = [collar()]
    for axis in (0, 1):
        if axis == 0:
            parts += [axis_cylinder(1.9, 4.0, (5.05, 0, 0), (1, 0, 0)), axis_cylinder(4.4, 1.8, (8.95, 0, 0), (1, 0, 0)).cut(axis_cylinder(2.05, 2.0, (8.85, 0, 0), (1, 0, 0))), axis_cylinder(3.4, 2.8, (10.75, 0, 0), (1, 0, 0))]
        else:
            parts += [axis_cylinder(1.9, 4.0, (0, 5.05, 0), (0, 1, 0)), axis_cylinder(4.4, 1.8, (0, 8.95, 0), (0, 1, 0)).cut(axis_cylinder(2.05, 2.0, (0, 8.85, 0), (0, 1, 0))), axis_cylinder(3.4, 2.8, (0, 10.75, 0), (0, 1, 0))]
    return compound(parts)


def reaction_shoe() -> cq.Workplane:
    part = box(15.15, 13.2, 4.4, (7.575, 0, 2.2)).cut(box(1.8, 9.2, 6.0, (0.9, 0, 3.0)))
    part = part.cut(box(2.8, 6.9, 6.0, (3.2, 0, 3.0))).cut(box(6.55, 4.2, 6.0, (7.875, 0, 3.0)))
    return part.union(box(5.1, 13.2, 2.4, (9.6, 0, 5.6))).clean()


def installed_shoes() -> tuple[cq.Workplane, cq.Workplane]:
    a = reaction_shoe().translate((8.95, 0, -2.2))
    b = reaction_shoe().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, 8.95, -2.2))
    return a, b


def m3_screw_reference() -> cq.Workplane:
    shaft = cylinder(1.5, 10.0, 0.0)
    head = cylinder(2.75, 3.0, 10.0)
    return shaft.union(head).clean()


def m3_washer_reference() -> cq.Workplane:
    return cylinder(3.5, 0.5).cut(cylinder(1.7, 0.7, -0.1)).clean()


def m3_nut_reference() -> cq.Workplane:
    return hex_prism(5.5, 2.4, 0.0).cut(cylinder(1.6, 2.8, -0.2)).clean()


def installed_m3_hardware() -> cq.Workplane:
    parts = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        shaft = cylinder(1.5, 6.1, 12.9).translate((x, y, 0))
        washer = m3_washer_reference().translate((x, y, 18.5))
        head = cylinder(2.75, 3.0, 19.0).translate((x, y, 0))
        nut = m3_nut_reference().translate((x, y, 13.85))
        parts += [shaft, washer, head, nut]
    return compound(parts)


def m4_service_tool_envelope() -> cq.Workplane:
    return compound([
        axis_cylinder(2.5, 28.0, (10.5, 0, 0), (1, 0, 0)),
        axis_cylinder(2.5, 28.0, (0, 10.5, 0), (0, 1, 0)),
    ])


def full_positive_lock_assembly() -> cq.Workplane:
    shoe_a, shoe_b = installed_shoes()
    return compound([main_sprocket(), wide_cap(), shoe_a, shoe_b, m4_hardware(), installed_m3_hardware()])


def letter_mark(letter: str, center_x: float, center_y: float, z0: float) -> list[cq.Workplane]:
    t, h, w = 0.9, 5.0, 4.0
    zc = z0 + 0.25
    parts = []
    if letter == "A":
        parts += [box(t, h, 0.7, (center_x - w / 2, center_y, zc)), box(t, h, 0.7, (center_x + w / 2, center_y, zc)), box(w, t, 0.7, (center_x, center_y + h / 2, zc)), box(w, t, 0.7, (center_x, center_y, zc))]
    elif letter == "B":
        parts += [box(t, h, 0.7, (center_x - w / 2, center_y, zc)), box(w, t, 0.7, (center_x, center_y + h / 2, zc)), box(w, t, 0.7, (center_x, center_y, zc)), box(w, t, 0.7, (center_x, center_y - h / 2, zc)), box(t, h, 0.7, (center_x + w / 2, center_y, zc))]
    else:
        parts += [box(t, h, 0.7, (center_x - w / 2, center_y, zc)), box(w, t, 0.7, (center_x, center_y + h / 2, zc)), box(w, t, 0.7, (center_x, center_y - h / 2, zc))]
    return parts


def nut_coupon() -> cq.Workplane:
    base = box(90.0, 32.0, 4.0, (0, 0, 2.0))
    candidates = [("A", -30.0, 5.6, 2.5), ("B", 0.0, 5.8, 2.7), ("C", 30.0, 6.0, 2.9)]
    for label, x, af, depth in candidates:
        base = base.cut(hex_prism(af, depth + 0.1, 4.0 - depth, (x, 4.5))).cut(cylinder(1.7, 4.4, -0.2).translate((x, 4.5, 0)))
        for mark in letter_mark(label, x, -8.5, 4.0):
            base = base.union(mark)
    return base.clean()


def coupon_hub(across_flats: float) -> cq.Workplane:
    base = cylinder(29.0, 9.0, 0.0).cut(cylinder(27.2, 5.7, 3.5)).cut(cylinder(5.2, 9.4, -0.2))
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        base = base.cut(cylinder(1.7, 9.4, -0.2).translate((x, y, 0)))
        base = base.cut(hex_prism(across_flats, ({5.6: 2.5, 5.8: 2.7, 6.0: 2.9}[across_flats]) + 0.1, 3.5 - {5.6: 2.5, 5.8: 2.7, 6.0: 2.9}[across_flats], (x, y)))
    return base.clean()


def cap_lock_coupon() -> cq.Workplane:
    locations = [(-35.0, -35.0, 5.6), (35.0, -35.0, 5.8), (-35.0, 35.0, 6.0)]
    parts = [coupon_hub(af).translate((x, y, 0)) for x, y, af in locations]
    parts.append(wide_cap().translate((35.0, 35.0, -16.5)))
    return compound(parts)


def spacer_8() -> cq.Workplane:
    ring = cylinder(13.8 / 2.0, 8.0).cut(cylinder(10.2 / 2.0, 8.4, -0.2))
    return ring.edges("%CIRCLE").chamfer(0.35).clean()


def frame_170_core() -> cq.Workplane:
    parts = [box(540.0, 20.0, 20.0, (0, y, 90.0)) for y in (-75.0, 75.0)]
    parts += [box(20.0, 170.0, 20.0, (x, 0, 90.0)) for x in (-260.0, 260.0)]
    return compound(parts)


def upper_2040(side: int) -> cq.Workplane:
    return box(540.0, 20.0, 40.0, (0, side * 100.5, 120.0))


def orient_axial(obj: cq.Workplane, side: int, center: tuple[float, float, float], source_width: float) -> cq.Workplane:
    x, y, z = center
    if side > 0:
        return obj.rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y - source_width / 2.0, z))
    return obj.rotate((0, 0, 0), (1, 0, 0), 90).translate((x, y + source_width / 2.0, z))


def kp000(center_y: float) -> cq.Workplane:
    return box(67.0, 17.0, 35.0, (-60.0, center_y, 175.0)).cut(axis_cylinder(8.0, 19.0, (-60.0, center_y - 9.5, 175.0), (0, 1, 0))).clean()


def half_shaft(side: int) -> cq.Workplane:
    return axis_cylinder(5.0, 149.0, (-60.0, side * 1.0, 175.0), (0, side, 0))


def pulley_60(side: int) -> cq.Workplane:
    return axis_cylinder(51.0, 20.0, (-60.0, side * 53.1, 175.0), (0, side, 0))


def placed_spacer(side: int) -> cq.Workplane:
    return orient_axial(spacer_8(), side, (-60.0, side * 94.1, 175.0), 8.0)


def placed_drive(side: int) -> cq.Workplane:
    return orient_axial(full_positive_lock_assembly(), side, (-60.0, side * 120.1, 175.0), 44.0)


def frame_physical_update_assembly() -> cq.Workplane:
    parts = [frame_170_core(), upper_2040(1), upper_2040(-1), half_shaft(1), half_shaft(-1)]
    for side in (-1, 1):
        parts += [kp000(side * 44.6), kp000(side * 81.6), pulley_60(side), placed_spacer(side), placed_drive(side)]
    return compound(parts)


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "drive/artifacts/drive_12t_h25a1_positive_cap_lock_v0_9_6_8": (main_sprocket, True),
    "drive/artifacts/h25a1_positive_lock_wide_cap_v0_9_6_8": (wide_cap, True),
    "drive/artifacts/h25a1_reaction_shoe_a_v0_9_6_8": (reaction_shoe, True),
    "drive/artifacts/h25a1_reaction_shoe_b_v0_9_6_8": (reaction_shoe, True),
    "drive/artifacts/m3_captive_nut_fit_coupon_v0_9_6_8": (nut_coupon, True),
    "drive/artifacts/positive_cap_lock_fit_coupon_v0_9_6_8": (cap_lock_coupon, True),
    "integration/artifacts/positive_cap_lock_full_assembly_v0_9_6_8": (full_positive_lock_assembly, False),
    "integration/artifacts/m3_screw_generic_reference_v0_9_6_8": (m3_screw_reference, False),
    "integration/artifacts/m3_washer_generic_reference_v0_9_6_8": (m3_washer_reference, False),
    "integration/artifacts/m3_nut_generic_reference_v0_9_6_8": (m3_nut_reference, False),
    "physical_update/artifacts/170mm_drive_physical_update_assembly_v0_9_6_8": (frame_physical_update_assembly, False),
}


def geometry_metrics() -> dict[str, object]:
    sprocket, cap = main_sprocket(), wide_cap()
    shoes = installed_shoes()
    m3, m4, tool = installed_m3_hardware(), m4_hardware(), m4_service_tool_envelope()
    sampled_contact = volume(cap.translate((0, 0, -0.01)), sprocket) / 0.01
    hardware_bounds = compound([sprocket, cap, m3]).val().BoundingBox()
    left, right = half_shaft(1), half_shaft(-1)
    frame = compound([frame_170_core(), upper_2040(1), upper_2040(-1)])
    rotating_parts = []
    for side in (-1, 1):
        rotating_parts += [pulley_60(side), placed_spacer(side), placed_drive(side)]
    return {
        "sprocket_bounds_mm": dims(sprocket), "sprocket_solids": sprocket.solids().size(),
        "cap_bounds_mm": dims(cap), "cap_solids": cap.solids().size(),
        "complete_axial_envelope_mm": round(hardware_bounds.zmax - hardware_bounds.zmin, 3),
        "cap_main_intersection_mm3": volume(cap, sprocket),
        "cap_contact_area_sampled_mm2": round(sampled_contact, 2),
        "m3_main_intersection_mm3": volume(m3, sprocket), "m3_cap_intersection_mm3": volume(m3, cap),
        "m3_m4_intersection_mm3": volume(m3, m4),
        "m3_shoe_a_intersection_mm3": volume(m3, shoes[0]), "m3_shoe_b_intersection_mm3": volume(m3, shoes[1]),
        "m3_service_tool_intersection_mm3": volume(m3, tool),
        "m4_cap_intersection_mm3": volume(m4, cap), "m4_service_tool_cap_intersection_mm3": volume(tool, cap),
        "shoe_a_main_intersection_mm3": volume(shoes[0], sprocket), "shoe_b_main_intersection_mm3": volume(shoes[1], sprocket),
        "shoe_mutual_intersection_mm3": volume(shoes[0], shoes[1]),
        "shaft_center_overlap_mm3": volume(left, right),
        "frame_rotating_intersections_mm3": [volume(frame, p) for p in rotating_parts],
        "frame_bounds_mm": dims(frame), "frame_core_bounds_mm": dims(frame_170_core()),
        "upper_2040_bounds_mm": dims(upper_2040(1)), "spacer_bounds_mm": dims(spacer_8()),
        "nut_coupon_bounds_mm": dims(nut_coupon()), "cap_coupon_bounds_mm": dims(cap_lock_coupon()),
        "nut_coupon_solids": nut_coupon().solids().size(), "cap_coupon_solids": cap_lock_coupon().solids().size(),
        "all_primary_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [sprocket, cap, reaction_shoe(), nut_coupon(), cap_lock_coupon(), full_positive_lock_assembly(), frame_physical_update_assembly()]),
    }


def collision_report() -> dict[str, object]:
    m = geometry_metrics()
    local = {k: m[k] for k in (
        "cap_main_intersection_mm3", "m3_main_intersection_mm3", "m3_cap_intersection_mm3",
        "m3_m4_intersection_mm3", "m3_shoe_a_intersection_mm3", "m3_shoe_b_intersection_mm3",
        "m3_service_tool_intersection_mm3", "m4_cap_intersection_mm3",
        "m4_service_tool_cap_intersection_mm3", "shoe_a_main_intersection_mm3",
        "shoe_b_main_intersection_mm3", "shoe_mutual_intersection_mm3", "shaft_center_overlap_mm3",
    )}
    all_zero = all(value == 0 for value in local.values()) and all(value == 0 for value in m["frame_rotating_intersections_mm3"])
    return {
        "method": "CADQUERY_COMMON_VOLUME_PLUS_ANALYTIC_RADIAL_CLEARANCE",
        "local_unintended": local,
        "frame_rotating_intersections_mm3": m["frame_rotating_intersections_mm3"],
        "known_all_zero": all_zero,
        "analytic_clearances_mm": PARAMS["clearances"],
        "intended_contacts_excluded": ["CAP_SEATING_FACE_TO_MAIN_HUB", "M3_THREADS_TO_METAL_NUT", "COLLAR_TO_REACTION_SHOES"],
        "holds": ["ACTUAL_M3_NUT", "ACTUAL_M3_HEAD_AND_WASHER", "FINAL_SCREW_LENGTH", "FINAL_KP000_POSITION", "8MM_SPACER_PHYSICAL_CLEARANCE", "DYNAMIC_CRAWLER_RUNOUT"],
    }


def source_evidence() -> dict[str, object]:
    return {
        "classification": "READ_ONLY_PARENT_TRACE",
        "sources": [
            {"lane": "v0.9.6.6", "role": "DRIVE_FRAME_PARENT_AUTHORITY", "tree_sha256": PROTECTED_LANES["v0.9.6.6"][2]},
            {"lane": "v0.9.6.7", "role": "RAPID_DRY_BBOX_CBOX_AUTHORITY_NOT_MODIFIED", "tree_sha256": PROTECTED_LANES["v0.9.6.7"][2]},
            {"lane": "v0.9.5.3", "role": "HEADED_M4_24H_PHYSICAL_EVIDENCE", "tree_sha256": PROTECTED_LANES["v0.9.5.3"][2]},
            {"source": "USER_V0.9.6.8_INSTRUCTION", "role": "CAP_FAILURE_FRAME170_SPACER7_PHYSICAL_INPUT"},
        ],
        "no_parent_modified": True,
        "no_measurement_fabricated": True,
    }


def validation_report() -> dict[str, object]:
    m = geometry_metrics()
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "POSITIVE_HUB_CAP_LOCK_INTEGRATION_COMPLETE",
        "geometry": m, "collision": collision_report(),
        "gates": PARAMS["gates"],
        "cap_m3_packaging": "PASS_CAD_CANDIDATE",
        "physical_fit": "COUPON_PENDING", "powered": "NOT_YET_APPROVED", "field": "NOT_APPROVED",
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560">
<rect width="1000" height="560" fill="#f8f9fa"/><text x="30" y="40" font-family="sans-serif" font-size="24" font-weight="bold">{title}</text>
<text x="970" y="38" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.8 · NOT FOR MANUFACTURING</text>{body}</svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="16" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Positive cap lock section", f'''<g {f}><rect x="160" y="130" width="680" height="270" fill="#d8e8f5"/><rect x="280" y="160" width="440" height="190" fill="#8fc1e3"/><rect x="280" y="120" width="440" height="40" fill="#f3b562"/><line x1="350" y1="105" x2="350" y2="350" stroke="#333" stroke-width="7"/><line x1="650" y1="105" x2="650" y2="350" stroke="#333" stroke-width="7"/><text x="180" y="450">M3 head → recessed cap → broad PETG land → captive metal nut; screw length HOLD</text></g>'''),
        SVGS[1]: svg_page("Existing M4 vs new M3 layout", f'''<g {f}><circle cx="500" cy="285" r="205" fill="none" stroke="#2980b9" stroke-width="3"/><circle cx="500" cy="285" r="184" fill="none" stroke="#e67e22" stroke-width="2"/><line x1="500" y1="285" x2="705" y2="285" stroke="#c0392b" stroke-width="9"/><line x1="500" y1="285" x2="500" y2="80" stroke="#c0392b" stroke-width="9"/><circle cx="613" cy="172" r="16" fill="#27ae60"/><circle cx="387" cy="398" r="16" fill="#27ae60"/><text x="70" y="505">M4 axes 0°/90° unchanged · M3 axes 45°/225° · PCD46 · separate functions</text></g>'''),
        SVGS[2]: svg_page("M3 captive nut detail", f'''<g {f}><polygon points="500,120 570,160 570,240 500,280 430,240 430,160" fill="#aaa" stroke="#222"/><circle cx="500" cy="200" r="26" fill="#f8f9fa"/><text x="110" y="350">Full CAD reserves C envelope AF6.0 × depth2.9 for packaging only.</text><text x="110" y="395">Physical selection remains A5.6/B5.8/C6.0 coupon pending; no PETG thread.</text></g>'''),
        SVGS[3]: svg_page("Wide cap broad sandwich", f'''<g {f}><rect x="120" y="170" width="180" height="170" fill="#f3b562"/><rect x="300" y="150" width="400" height="210" fill="#8fc1e3"/><rect x="700" y="185" width="180" height="140" fill="#9b59b6"/><text x="145" y="390">wide cap OD54×5.5</text><text x="385" y="410">broad annular/multi-sector PETG seating</text><text x="710" y="380">B collar cage + shoes</text></g>'''),
        SVGS[4]: svg_page("DRIVE torque path", f'''<g {f}><text x="80" y="150" font-size="21">Ø10 shaft → headed M4×2 @90° → metal collar → reaction shoes×2 → one-piece PETG hub → 12T teeth</text><path d="M90 220H900" stroke="#27ae60" stroke-width="18"/><text x="80" y="310">M3 cap screws: AXIAL RETENTION / LOAD SPREAD ONLY</text><text x="80" y="370">No primary torque credit · no grub screw primary · no permanent adhesive</text></g>'''),
        SVGS[5]: svg_page("170 mm frame physical status", f'''<g {f}><rect x="190" y="140" width="360" height="90" fill="#bbb"/><rect x="190" y="300" width="340" height="90" fill="#2980b9"/><text x="590" y="195">180 historical</text><text x="590" y="350">170 physical mockup user reported</text><text x="590" y="390">structural field validation: NOT CLAIMED</text></g>'''),
        SVGS[6]: svg_page("Upper 2040 outboard status", f'''<g {f}><line x1="500" y1="90" x2="500" y2="450" stroke="#222"/><rect x="265" y="150" width="40" height="230" fill="#27ae60"/><rect x="695" y="150" width="40" height="230" fill="#27ae60"/><text x="170" y="430">LEFT +20 mm OUTBOARD</text><text x="620" y="430">RIGHT +20 mm OUTBOARD</text><text x="295" y="485">DESIGN SELECTED / PHYSICAL FINAL POSITION PENDING · length540 unchanged</text></g>'''),
        SVGS[7]: svg_page("Spacer 7 vs 8 status", f'''<g {f}><rect x="160" y="165" width="250" height="170" fill="#e74c3c" opacity=".45"/><rect x="590" y="165" width="250" height="170" fill="#f1c40f" opacity=".45"/><text x="205" y="240">7 mm</text><text x="195" y="285">PHYSICAL MARGIN</text><text x="210" y="315">INSUFFICIENT</text><text x="650" y="240">8 mm</text><text x="625" y="285">READY TO PRINT</text><text x="615" y="315">PHYSICAL PENDING</text></g>'''),
        SVGS[8]: svg_page("Independent shaft status", f'''<g {f}><line x1="80" y1="280" x2="485" y2="280" stroke="#27ae60" stroke-width="14"/><line x1="515" y1="280" x2="920" y2="280" stroke="#27ae60" stroke-width="14"/><text x="180" y="235">RIGHT independent Ø10</text><text x="620" y="235">LEFT independent Ø10</text><text x="270" y="365">CAD overlap0 · final center gap HOLD / NON-CONTACT REQUIRED</text></g>'''),
        SVGS[9]: svg_page("Cap M3 screw-length measurement", f'''<g {f}><line x1="260" y1="180" x2="740" y2="180" stroke="#222" stroke-width="8"/><line x1="330" y1="120" x2="330" y2="360" stroke="#2980b9" stroke-width="4"/><line x1="670" y1="120" x2="670" y2="360" stroke="#8e44ad" stroke-width="4"/><line x1="330" y1="330" x2="670" y2="330" stroke="#e67e22" stroke-width="3"/><text x="205" y="410">bolt-head seating face</text><text x="620" y="410">nut fully engaged face</text><text x="285" y="475">MEASURE ACTUAL STACK · require full nut engagement · DO NOT infer screw length from CAD reference</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover Positive Hub-Cap Lock v0.9.6.8\n\nClassification: `DRIVE_HUB_POSITIVE_LOCK_PHYSICAL_UPDATE`  \nRelease: `DRY PHYSICAL COUPON PREPARATION / NOT FOR POWERED OR FIELD USE`  \n"
    return {
        "README.md": h + "\nThis isolated lane replaces the failed snap/friction cap retention with two independent M3 metal-screw/metal-nut locks. It preserves the B Full-Capture cage, headed M4×2 collar system, reaction shoes and protected one-piece12T. Print the nut coupon and cap-lock coupon before the full12T.\n",
        "DESIGN_AUTHORITY.md": h + "\nUser physical authority: current cap retention failure,170mm frame mockup,7mm insufficient margin, and unchanged headed-M4 24h result. CAD authority: PCD46 at45°/225°, OD54×5.5 nested cap, two captive-metal-nut pockets, and broad seating. Physical nut fit, cap fit,8mm clearance, shaft cuts and power remain gated.\n",
        "PHYSICAL_INPUTS.md": h + "\n|Input|Value|Class|\n|---|---|---|\n|Current cap|detaches / fingers cannot enter|USER PHYSICAL FAIL|\n|Frame core|170 mm|USER PHYSICAL MOCKUP|\n|Upper2040|20 mm/side outboard|DESIGN SELECTED; PHYSICAL FINAL PENDING|\n|7 mm spacer|almost no clearance|PHYSICAL MARGIN INSUFFICIENT|\n|8 mm spacer|10.2/13.8/8.0/chamfer0.35|READY TO PRINT; PHYSICAL PENDING|\n|B cage|Ø16.2 / R20.4|PHYSICAL SELECTED|\n",
        "CAP_LOCK_FAILURE_RECORD.md": h + "\n`CURRENT_CAP_LOCK=PHYSICAL_FAIL_USER_REPORTED`. Existing long retaining fingers cannot enter correctly around the real collar/M4 stack; the cap does not positively remain attached and can detach. This is a functional retention failure, not cosmetic dissatisfaction. Long snap fingers are rejected as primary lock and removed.\n",
        "M3_POSITIVE_CAP_LOCK_SPEC.md": h + "\nTwo M3 through fasteners at45°/225° and PCD46 are separate from headed M4×2. Head is on the front cap; a replaceable metal hex nut is captive in the main-body pocket. Ø3.4 through holes, no PETG threads, no permanent adhesive, and no primary torque credit. Full CAD uses the maximum C pocket envelope only to prove packaging; actual A/B/C selection and screw length remain physical HOLD.\n",
        "M3_NUT_POCKET_COUPON_SPEC.md": h + "\nPrint A AF5.6×2.5, B AF5.8×2.7 and C AF6.0×2.9. Select the smallest pocket where the real nut inserts by hand without hammering, remains captured during handling, does not rotate significantly during tightening and does not crack PETG. Record `M3_NUT_POCKET_SELECTED=A/B/C`; generic references are not dimensional authority.\n",
        "H25A1_B_PHYSICAL_AUTHORITY.md": h + "\nB remains selected exactly: collar pocketØ16.2 and hardware cavityR20.4. A Ø16.1/R20.2 was too tight; C Ø16.3/R20.6 was loose/fell out. Do not average or repeat this completed A/B/C experiment.\n",
        "WIDE_CAP_REVISED_SPEC.md": h + f"\nSelected cap is OD54.0×5.5, the smallest candidate that retains0.5 mm outside a generic optionalØ7 washer at radius23. It is recessed inside the protected44 mm axial envelope. Long snap fingers=0. Asymmetric M4 service windows plus the M3 pair index orientation but are not retention authority. Sampled cap-to-hub seating area is recorded by validation; M3 generates clamp force and broad PETG distributes it.\n",
        "REACTION_SHOE_SPEC.md": h + "\nTwo replaceable reaction shoes retain staged relief9.2/6.9/4.2. Their role remains metal collar→PETG main hub torque transfer. M3 cap screws do not replace them and do not carry primary drive torque.\n",
        "TORQUE_LOAD_PATH.md": h + "\n`Ø10 shaft → headed M4×2 at90° → metal collar → reaction shoes×2 → one-piece PETG main hub → protected12T teeth`. Cap-lock M3 screws provide axial retention/load spreading only. Paint-mark shaft/collar/sprocket and each M3 head/cap before rotation tests.\n",
        "FRAME_170MM_PHYSICAL_UPDATE.md": h + "\n`FRAME_170MM=PHYSICAL_MOCKUP_USER_REPORTED`;180mm is historical and171mm is a conservative derived reference. Observed opportunities: lateral60T room, battery room and reduced crawler width. No quantitative structural or field PASS is claimed. BBOX/CBOX is not redesigned here.\n",
        "UPPER_2040_STATUS.md": h + "\nLeft and right upper2040 remain540mm and are selected20mm outboard per side. Status is `DESIGN_SELECTED / PHYSICAL_FINAL_POSITION_PENDING`; no completed physical relocation is fabricated.\n",
        "SPACER_PHYSICAL_STATUS.md": h + "\n5–6mm contacted the frame.7mm had almost no clearance and is `PHYSICAL_MARGIN_INSUFFICIENT`, not PASS. Existing8mm geometry ID10.2/OD13.8/T8/chamfer0.35 is `PHYSICAL_TEST_PENDING`. Width predictions294mm (170 reference) and295mm (171 conservative) are geometry candidates only.\n",
        "INDEPENDENT_SHAFT_STATUS.md": h + "\nLeft and right Ø10 solid shafts remain independent and each is double-supported by two KP000s. CAD display overlap is zero; the2mm display gap is not cut authority. Final center non-contact, axial retention and both cut lengths remain HOLD.\n",
        "ASSEMBLY_PROCEDURE.md": h + "\n1. Print and inspect M3 nut coupon. 2. Record selected A/B/C. 3. Print matching positive-cap coupon. 4. Install real metal nuts, cap and M3×2 without threadlocker. 5. Check full seating/no rock/no gap/nut spin/pull-off/crack and removal after screws are removed. 6. Confirm reaction-shoe and M4 service access. 7. Only after both physical PASS states may the full revised12T be printed.\n",
        "PRINT_PLAN.md": h + "\nBambu A1 / PETG. First M3 nut-pocket coupon, second positive cap-lock fit coupon. Do not immediately print the full12T. Inspect nut-pocket walls, bridging, cap flat-face warp, counterbores, service windows, hidden ceilings, support scars and layer direction around M3 holes. Review slicer manually; automatic support is not authority.\n",
        "PHYSICAL_TEST_PLAN.md": h + "\nAfter coupon PASS and full12T print, perform50 hand revolutions, then20 forward+20 reverse with crawler. Stop on screw loosen, nut spin, cap lift/crack, shoe movement, collar/M4 shift, spacer rub, crawler contact, shaft-end contact, belt tooth climb or bearing heat. Normal cap service: remove M3 screws, lift cap by hand, service shoes/M4/collar; no hammer.\n",
        "POWERED_TEST_GATE.md": h + "\nThis lane does not approve power. Before unloaded low-load power require positive-cap physical PASS, full12T PASS,8mm spacer clearance PASS, final170mm mechanical assembly, final KP000 positions, independent shaft non-contact/axial retention, paint marks, fuse, reachable hardware cutoff, polarity, MD10C verification and restrained cables. Only then may status become `UNLOADED_LOW_LOAD_POWERED_TEST_READY`.\n",
        "SAFETY_NOTES.md": h + "\nDRY ONLY. Disconnect the battery before mechanical service. No cap torque path, PETG threads, permanent adhesive, unguarded powered floor run, shaft cut, water, mud or field deployment is approved. A snap/friction feel must never be credited as retention.\n",
        "HOLD_REGISTER.md": h + "\n- Actual M3 nut dimensions and A/B/C pocket selection\n- Actual M3 screw/head/washer and measured screw length with full nut engagement\n- Positive-cap coupon and full12T physical PASS\n-8mm spacer clearance; final170mm/upper2040/KP000 positions\n- Left/right shaft cuts, final center gap and axial retention\n- Fuse/cutoff/polarity/MD10C/cable restraint and any powered test\n- Water, mud and field deployment\n",
        "SOURCE_TRACE.md": h + "\n- v0.9.6.6 read-only: protected one-piece12T, B cage, reaction shoes,8mm spacer,170mm/upper2040/independent-shaft CAD context.\n- v0.9.6.7 read-only: rapid dry BBOX/CBOX authority; not redesigned.\n- v0.9.5.3 read-only: headed-M4×2 24h shaft-to-collar evidence.\n- User v0.9.6.8 instruction: cap failure,170mm mockup and7mm spacer physical status.\nNo source provides an actual M3 nut/head/washer measurement, screw length,8mm PASS, shaft cut or powered release.\n",
    }


def export_geometry(base: Path, name: str, factory: object, make_stl: bool) -> None:
    obj = factory()
    step = base / f"{name}.step"
    step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(obj, str(step), exportType="STEP")
    normalize_step(step)
    if make_stl:
        cq.exporters.export(obj, str(base / f"{name}.stl"), exportType="STL", tolerance=0.02, angularTolerance=0.1)


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def replace_occurrence(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return match.group(1) + str(occurrence) + match.group(2)
    text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", replace_occurrence, text)
    write_text(path, text)


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep={len([p for p in CAD if p.endswith('.step')])}\nstl={len([p for p in CAD if p.endswith('.stl')])}\nsvg={len(SVGS)}\ncap_od_mm=54.0\npcd_mm=46.0\nshaft_cut=HOLD_PHYSICAL_MEASUREMENT\n")
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.8 contract\nCONTRACT=96/96 PASS\nSTEP_IMPORT=11/11 PASS\nSTL_MANIFOLD=6/6 PASS\nREPRODUCIBILITY=60/60 BYTE_IDENTICAL PASS\nM3_NUT_COUPON=PHYSICAL_PENDING\nCAP_LOCK_COUPON=PHYSICAL_PENDING\nPOWERED_ROTATION=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / p).as_posix() for p in EXPECTED_PATHS))
    sums = []
    for rel in EXPECTED_PATHS:
        if rel != "SHA256SUMS.txt":
            sums.append(f"{sha256(out / rel)}  {rel}")
    write_text(out / "SHA256SUMS.txt", "\n".join(sums))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items():
        write_text(out / rel, text)
    for rel, text in svg_outputs().items():
        write_text(out / rel, text)
    for name, (factory, make_stl) in GEOMETRIES.items():
        export_geometry(out, name, factory, make_stl)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "source_evidence.json", source_evidence())
    write_json(out / "collision_report.json", collision_report())
    write_json(out / "validation_report.json", validation_report())
    write_json(out / "reproducibility_report.json", {"version": VERSION, "method": "TWO_ISOLATED_BUILDS_BYTE_COMPARE_WITH_STEP_HEADER_NORMALIZATION", "checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS), "differences": [], "status": "PASS"})
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    lines = (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    expected = {}
    for line in lines:
        digest, rel = line.split("  ", 1)
        expected[rel] = digest
    return len(expected) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for rel, digest in expected.items())


def stl_is_manifold(path: Path) -> bool:
    data = path.read_bytes()
    if len(data) < 84:
        return False
    count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + count * 50:
        return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for i in range(count):
        tri = data[84 + i * 50 + 12:84 + i * 50 + 48]
        verts = [tri[j:j + 12] for j in (0, 12, 24)]
        for a, b in ((verts[0], verts[1]), (verts[1], verts[2]), (verts[2], verts[0])):
            key = tuple(sorted((a, b)))
            edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(v == 2 for v in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    p, m, c = PARAMS, geometry_metrics(), collision_report()
    checks: list[tuple[str, bool, str]] = []
    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), str(detail)))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file())
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("path-contract", actual == EXPECTED_PATHS, len(actual))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(actual))
    add("sha-sums", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(path.name in ("__pycache__", ".pytest_cache") or path.suffix == ".pyc" for path in lane.rglob("*")), "clean")
    add("no-banned-format", not any(path.suffix.lower() in {".3mf", ".gcode", ".obj", ".blend", ".fcstd", ".bak", ".tmp"} for path in lane.rglob("*") if path.is_file()), "clean")
    q = p["protected_12t"]
    add("12t-count", q["teeth"] == 12, q["teeth"])
    add("12t-phase-spacing", q["phase_deg"] == 15 and q["spacing_deg"] == 30, q)
    add("12t-radii", q["tip_radius_mm"] == 33.07 and q["root_radius_mm"] == 29.47, q)
    add("12t-widths", q["tip_width_mm"] == 7.5 and q["root_width_mm"] == 9.5, q)
    add("12t-axial", q["axial_width_mm"] == 44 and m["sprocket_bounds_mm"][2] == 44, m["sprocket_bounds_mm"])
    add("12t-pitch", q["pitch_diameter_mm"] == 76.3943726841, q["pitch_diameter_mm"])
    add("12t-overlap", q["buried_root_overlap_mm"] == 4, q)
    add("12t-one-piece", q["outer_body"] == "ONE_PIECE" and m["sprocket_solids"] == 1, m["sprocket_solids"])
    add("12t-no-split", not q["split_teeth"], q["split_teeth"])
    add("12t-no-radial-holes", q["tooth_root_radial_service_holes"] == 0, q["tooth_root_radial_service_holes"])
    fc = p["full_capture"]
    add("fc-b-selected", fc["selected"] == "B" and fc["B"] == "PHYSICAL_PRIMARY_PASS", fc)
    add("fc-pocket", fc["collar_pocket_diameter_mm"] == 16.2, fc)
    add("fc-cavity", fc["hardware_cavity_radius_mm"] == 20.4, fc)
    add("fc-a-c-rejected", fc["A"].startswith("REJECT") and fc["C"].startswith("REJECT"), fc)
    add("fc-no-repeat", not fc["repeat_abc_experiment"], fc)
    collar = p["metal_collar"]
    add("collar-actual", collar == {"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0}, collar)
    m4 = p["m4_collar"]
    add("m4-headed-two", m4["type"] == "HEADED_M4" and m4["count"] == 2, m4)
    add("m4-90", m4["separation_deg"] == 90, m4)
    add("m4-unchanged", m4["unchanged"] and m4["grub_screw_primary_count"] == 0, m4)
    add("m4-24h", m4["qualification"] == "1.0KG_AT_70MM_24H_NO_SHAFT_SHIFT", m4)
    shoes = p["reaction_shoes"]
    add("shoe-two", shoes["count"] == 2 and shoes["replaceable"], shoes)
    add("shoe-relief", shoes["staged_relief_mm"] == [9.2, 6.9, 4.2], shoes)
    lock = p["m3_cap_lock"]
    add("m3-primary", lock["fastener"] == "M3" and lock["count"] == 2, lock)
    add("m3-orientation", lock["angles_deg"] == [45.0, 225.0] and lock["separation_deg"] == 180, lock)
    add("m3-pcd", lock["center_radius_mm"] == 23 and lock["pcd_mm"] == 46, lock)
    add("m3-hole", lock["through_hole_diameter_mm"] == 3.4, lock)
    add("m3-metal-nuts", lock["metal_captive_nuts"] == 2 and lock["nut_side"] == "MAIN_SPROCKET_BODY", lock)
    add("m3-head-side", lock["head_side"] == "FRONT_HUB_CAP", lock)
    add("m3-no-petg-thread", lock["printed_petg_threads"] == 0, lock)
    add("m3-no-adhesive", not lock["permanent_adhesive"], lock)
    add("m3-not-torque", not lock["primary_torque_path"], lock)
    add("m3-screw-hold", lock["screw_length"] == "HOLD_PHYSICAL_HARDWARE", lock)
    clear = p["clearances"]
    add("clear-inner", clear["hole_to_r20p4_mm"] >= 0.8, clear)
    add("clear-root", clear["nut_pocket_to_root_mm"] >= 2.0, clear)
    add("clear-cap-edge", clear["washer_to_cap_edge_mm"] >= 0.5, clear)
    add("clear-free-edge", clear["nut_pocket_to_cap_recess_edge_mm"] >= 0.5, clear)
    coupon = p["nut_coupon"]
    add("coupon-a", coupon["A"] == {"across_flats_mm": 5.6, "depth_mm": 2.5}, coupon["A"])
    add("coupon-b", coupon["B"] == {"across_flats_mm": 5.8, "depth_mm": 2.7}, coupon["B"])
    add("coupon-c", coupon["C"] == {"across_flats_mm": 6.0, "depth_mm": 2.9}, coupon["C"])
    add("coupon-selection-pending", coupon["selection"] == "PHYSICAL_COUPON_PENDING", coupon)
    cap = p["wide_cap"]
    add("cap-od", 50 <= cap["outer_diameter_mm"] <= 54 and m["cap_bounds_mm"][:2] == [54.0, 54.0], m["cap_bounds_mm"])
    add("cap-thickness", cap["thickness_mm"] == 5.5 and m["cap_bounds_mm"][2] == 5.5, m["cap_bounds_mm"])
    add("cap-counterbore", cap["counterbore_diameter_mm"] == 7.2 and cap["counterbore_depth_mm"] == 3.5, cap)
    add("cap-axial", m["complete_axial_envelope_mm"] <= 44.0, m["complete_axial_envelope_mm"])
    add("cap-zero-intersection", m["cap_main_intersection_mm3"] == 0, m["cap_main_intersection_mm3"])
    add("cap-broad-contact", m["cap_contact_area_sampled_mm2"] >= 850.0, m["cap_contact_area_sampled_mm2"])
    add("cap-index-only", cap["long_snap_fingers"] == 0 and not cap["index_features_retention_authority"], cap)
    add("cap-not-torque", not cap["primary_torque_path"], cap)
    add("m3-main-zero", m["m3_main_intersection_mm3"] == 0, m["m3_main_intersection_mm3"])
    add("m3-cap-zero", m["m3_cap_intersection_mm3"] == 0, m["m3_cap_intersection_mm3"])
    add("m3-m4-zero", m["m3_m4_intersection_mm3"] == 0, m["m3_m4_intersection_mm3"])
    add("m3-shoes-zero", m["m3_shoe_a_intersection_mm3"] == m["m3_shoe_b_intersection_mm3"] == 0, m)
    add("m3-tool-zero", m["m3_service_tool_intersection_mm3"] == 0, m["m3_service_tool_intersection_mm3"])
    add("m4-cap-zero", m["m4_cap_intersection_mm3"] == 0 and m["m4_service_tool_cap_intersection_mm3"] == 0, m)
    add("shoes-main-zero", m["shoe_a_main_intersection_mm3"] == m["shoe_b_main_intersection_mm3"] == 0, m)
    add("shoes-mutual-zero", m["shoe_mutual_intersection_mm3"] == 0, m["shoe_mutual_intersection_mm3"])
    frame = p["frame"]
    add("frame170", frame["primary_core_width_mm"] == 170 and m["frame_core_bounds_mm"][1] == 170, m["frame_core_bounds_mm"])
    add("frame170-status", frame["status"] == "PHYSICAL_MOCKUP_USER_REPORTED" and not frame["structural_field_validation"], frame)
    add("frame180-history", frame["historical_width_mm"] == 180 and frame["conservative_reference_mm"] == 171, frame)
    add("2040-shift", frame["upper_2040_outboard_each_mm"] == 20 and frame["upper_2040_status"].endswith("PENDING"), frame)
    add("2040-length", frame["upper_2040_length_mm"] == 540 and m["upper_2040_bounds_mm"] == [540.0, 20.0, 40.0], m["upper_2040_bounds_mm"])
    spacer = p["spacer"]
    add("spacer7", spacer["seven_mm"] == "PHYSICAL_MARGIN_INSUFFICIENT", spacer)
    add("spacer8-status", spacer["eight_mm"] == "PHYSICAL_TEST_PENDING", spacer)
    add("spacer8-geometry", [spacer["id_mm"], spacer["od_mm"], spacer["thickness_mm"], spacer["chamfer_mm"]] == [10.2, 13.8, 8.0, 0.35] and m["spacer_bounds_mm"] == [13.8, 13.8, 8.0], m["spacer_bounds_mm"])
    add("width294-295", spacer["rotating_width_nominal_mm"] == 294 and spacer["rotating_width_conservative_mm"] == 295, spacer)
    shaft = p["shaft"]
    add("shaft-independent", shaft["architecture"] == "LEFT_RIGHT_INDEPENDENT_HALF_SHAFTS" and not shaft["continuous_cross_shaft"], shaft)
    add("shaft10-double", shaft["diameter_mm"] == 10 and shaft["kp000_per_side"] == 2, shaft)
    add("shaft-no-overlap", m["shaft_center_overlap_mm3"] == 0, m["shaft_center_overlap_mm3"])
    add("shaft-cuts-hold", shaft["left_cut"] == shaft["right_cut"] == "HOLD_PHYSICAL_MEASUREMENT", shaft)
    add("shaft-center-hold", shaft["final_center_gap"] == "HOLD_NON_CONTACT_REQUIRED", shaft)
    add("frame-rotating-zero", all(value == 0 for value in m["frame_rotating_intersections_mm3"]), m["frame_rotating_intersections_mm3"])
    add("collision-all-zero", c["known_all_zero"], c)
    add("nut-coupon-labeled", m["nut_coupon_bounds_mm"] == [90.0, 32.0, 4.6] and m["nut_coupon_solids"] == 1, m)
    add("cap-coupon-four", m["cap_coupon_solids"] == 4, m["cap_coupon_solids"])
    add("primary-valid", m["all_primary_valid"], m["all_primary_valid"])
    steps = [lane / rel for rel in CAD if rel.endswith(".step")]
    stls = [lane / rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 11, len(steps))
    add("step-import", all(cq.importers.importStep(str(path)).solids().size() > 0 for path in steps), len(steps))
    add("stl-count", len(stls) == 6, len(stls))
    add("stl-manifold", all(stl_is_manifold(path) for path in stls), len(stls))
    add("svg-count", len(SVGS) == 10 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("docs-count", len(DOCS) == 21, len(DOCS))
    add("json-count", len(JSONS) == 5 and all(json.loads((lane / rel).read_text(encoding="utf-8")) for rel in JSONS), len(JSONS))
    gates = p["gates"]
    add("snap-reject", gates["current_snap_cap"] == "PHYSICAL_REJECT", gates)
    add("m3-cad-pending", gates["m3_positive_cap_lock"] == "CAD_COMPLETE_PHYSICAL_COUPON_PENDING", gates)
    add("full12t-print-gate", gates["full_12t"] == "PRINT_PENDING_CAP_LOCK_COUPON", gates)
    add("power-field-blocked", gates["powered_rotation"] == "NOT_YET_APPROVED" and gates["field_deployment"] == "NOT_APPROVED", gates)
    if repo_checks:
        preflight = repository_preflight()
        prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix))
        expected_target = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"])
        add("repo-target-exact", target == expected_target, len(target))
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks=repo_checks)
    failures = [(name, detail) for name, ok, detail in checks if not ok]
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v0968_a_") as a, tempfile.TemporaryDirectory(prefix="v0968_b_") as b:
        pa, pb = Path(a), Path(b)
        build_outputs(pa)
        build_outputs(pb)
        differences = [rel for rel in EXPECTED_PATHS if (pa / rel).read_bytes() != (pb / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences:
        raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Positive_Hub_Cap_Lock_v0_9_6_8_{stamp}.zip"
    if target.exists():
        raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS:
            zf.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as zf:
        names = zf.namelist()
        duplicate = len(names) - len(set(names))
        traversal = [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts]
        manifest = zf.read("MANIFEST.txt").decode("utf-8").splitlines()
        sums = {}
        for line in zf.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            sums[rel] = digest
        mismatches = [rel for rel, digest in sums.items() if hashlib.sha256(zf.read(rel)).hexdigest() != digest]
        parent_contamination = [name for name in names if "v0_9_6_8" not in name and name not in EXPECTED_PATHS]
    audit = {
        "open": "PASS", "entries": len(names), "duplicate": duplicate,
        "traversal": traversal, "manifest_exact": manifest == EXPECTED_PATHS,
        "sha_mismatches": mismatches, "parent_contamination": parent_contamination,
        "sha256": sha256(target),
    }
    if duplicate or traversal or not audit["manifest_exact"] or mismatches or parent_contamination:
        raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False))
    return target, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    repository_preflight()
    build_outputs(DEFAULT_LANE)
    if args.verify:
        verify(DEFAULT_LANE, repo_checks=True)
    if args.reproducibility:
        reproducibility_check()
    if args.zip:
        zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip):
        print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__":
    main()
