#!/usr/bin/env python3
"""Build Common Rover v0.9.4.3 service/drivetrain architecture references.

All geometry is non-manufacturing reference geometry.  Missing washer/head,
servo, and clutch measurements remain explicit HOLD values.
"""
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
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq


VERSION = "0.9.4.3"
CLASSIFICATION = "SERVICE_AND_DRIVETRAIN_ARCHITECTURE"
RELEASE = "HOLD"
FINAL_STATUS = "SERVICE_AND_DRIVETRAIN_ARCHITECTURE_COMPLETE / PHYSICAL_MEASUREMENTS_PENDING"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3"
LANE = Path(__file__).resolve().parent
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED = 1401
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Service_Servo_Clutch_H25A1_v0_9_4_3_"

P2_REL = "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2"
P1_REL = "cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1"
P0_REL = "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0"
P2, P1, P0 = (REPO_ROOT / p for p in (P2_REL, P1_REL, P0_REL))

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_CONTRACTS = {
    P2_REL: (57, {
        "MANIFEST.txt": "a983a48c6f9394a9f90b112b3f1f7e2f89dbdc70a34044e4d4711bf6cf6adf4a",
        "SHA256SUMS.txt": "e0033d12141e805b11ec53dbe5c2de5e65fecb46a1a87a1b9f30b9113cce82b1",
        "geometry_manifest.json": "c9a9ce48fba8318ff0d41155c2cb47ec5a5b6beb3d688385ef0ba8f9cd90408c",
        "validation_report.json": "37d2da249ab66238b4ecc715550a45d7ef7a6a427fc533cb09c75248031d1da8",
        "build_common_rover_physical_fit_closure_v0942.py": "3356276d37bee8f7e84c82c9ada8b128c45206148952a0c3137d526590259172",
        "tests/test_common_rover_physical_fit_closure_v0942.py": "a6f5a0adce49bc71797175f337fe964a7dae3a13f87c4a815cbb0692db8609f3",
    }),
    P1_REL: (68, {
        "MANIFEST.txt": "879697e31b9ab4595c2c13c17741ca46e6d14d6137de4d0cac91cc32b90397e5",
        "SHA256SUMS.txt": "9446ff0205256762757396be582c8cbb46b3c2131aa8d150903e8b1297ac26aa",
        "geometry_manifest.json": "99bf05d5c13cb958983f3c2c8c167f2bc7d62ec254d9fef19f3c811384355451",
        "validation_report.json": "9f79843e750884f96c9aa04dc123a87b8c6e006fa2c5f50be652abe453c74c53",
    }),
    P0_REL: (43, {
        "MANIFEST.txt": "fbb9d00eda9dda979e3dfcb4596d987260fc79dd6f0160cdf40512fbf438a984",
        "SHA256SUMS.txt": "0bfd7afed7b19543e811a1e08bb98aa8c8151a46465d3254702361ea50794fe5",
        "geometry_manifest.json": "06c2785bf772912a3019a59004586ddad136d3e58320682c376d93f9f1add198",
        "validation_report.json": "13cdca78fc4a12a29ba5128ecf366cb986fdf635b6f73751af1604fba314f5d5",
    }),
}

DOCS = [
    "README.md", "PARENT_AUDIT.md", "SOURCE_TRACE.md",
    "H25A1_FULL_HARDWARE_UPDATE.md", "H25A1_FULL_HARDWARE_MEASUREMENT_SHEET.md",
    "H25A1_FULL_HARDWARE_FIT_ARCHITECTURE.md", "H25A1_STATIC_FIXTURE_V2_SPEC.md",
    "BBOX_PITCH_AND_SLIDE_SERVICE.md", "BBOX_TOP_GUIDE_ARCHITECTURE.md",
    "BBOX_BOTTOM_GRIP_ARCHITECTURE.md", "BBOX_SERVICE_TEST_UPDATE.md",
    "SERVO_BRIDGE_ARCHITECTURE.md", "SERVO_MEASUREMENT_SHEET.md",
    "SLIDE_CLUTCH_ARCHITECTURE.md", "SLIDE_CLUTCH_MEASUREMENT_SHEET.md",
    "CLUTCH_FORCE_TEST_PLAN.md", "CLUTCH_POSITION_INTERLOCK.md",
    "FRAME_BRACE_ROLE_REPORT.md", "INTERFERENCE_REPORT.md", "SERVICEABILITY_REPORT.md",
    "MISSING_MEASUREMENTS.md", "DESIGN_GATE.md",
]
JSONS = [
    "dimensions.json", "interfaces.json", "hardware.json", "service_motions.json",
    "test_limits.json", "measurement_ledger.json", "geometry_manifest.json",
    "validation_report.json",
]
CAD = [
    "cad/frame_reference.step", "cad/bbox_pitch_slide_envelope.step",
    "cad/bbox_top_wear_pad_reference.step", "cad/bbox_bottom_grip_reference.step",
    "cad/h25a1_full_hardware_parametric_reference.step", "cad/servo_bridge_reference.step",
    "cad/servo_plate_generic_left.step", "cad/servo_plate_generic_right.step",
    "cad/slide_clutch_architecture.step", "cad/slide_clutch_carriage_reference.step",
    "cad/slide_shoe_reference.step", "cad/drive_stop_reference.step",
    "cad/neutral_stop_reference.step", "cad/pto_stop_reference.step",
    "cad/full_service_architecture.step", "cad/bbox_top_wear_pad_concept_coupon.stl",
    "cad/slide_shoe_concept_coupon.stl", "cad/bbox_pitch_angle_service_gauge.step",
    "cad/bbox_pitch_angle_service_gauge.stl",
]
DRAWINGS = [
    "drawings/bbox_pitch_slide_side.svg", "drawings/bbox_service_sequence.svg",
    "drawings/h25a1_full_hardware_section.svg", "drawings/h25a1_measurement_map.svg",
    "drawings/servo_bridge_top.svg", "drawings/servo_bridge_front.svg",
    "drawings/slide_clutch_positions.svg", "drawings/slide_clutch_guide_section.svg",
    "drawings/servo_linkage_concept.svg", "drawings/bbox_vs_clutch_service_clearance.svg",
]
SOURCE = ["build_common_rover_service_servo_clutch_v0943.py", "tests/test_common_rover_service_servo_clutch_v0943.py"]
RELEASE_FILES = ["MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
PACKAGE_PATHS = sorted(DOCS + JSONS + CAD + DRAWINGS + SOURCE + RELEASE_FILES)

FRAME = {
    "structural_height_mm": 150.0, "upper_outer_mm": [540.0, 181.0],
    "lower_outer_mm": [442.0, 181.0], "upper_clear_mm": [500.0, 100.0],
    "lower_clear_mm": [400.0, 140.0], "vertical_2020_mm": 110.0,
    "status": "REOPENED_PRIMARY_COMPACT_BASELINE", "frame_190": "ALTERNATIVE_HOLD",
}
BATTERY = {"x_mm": 150.9, "y_mm": 99.4, "z_mm": 92.5, "mass_kg": 1.2,
           "insertion_clear_height_mm": 108.0, "terminal_equipped_pass": "PHYSICAL_PASS_USER_REPORTED"}
BBOX = {
    "dummy_mm": [180.0, 114.0, 103.0], "test_heights_mm": [103.0, 105.0, 107.0],
    "service_motion": "BBOX_PITCH_AND_SLIDE_SERVICE_MOTION", "reference_pitch_deg": [0.0, 2.0, 4.0, 6.0],
    "final_pitch": "PHYSICAL_TEST_REQUIRED", "straight_x_only": False,
    "waterproof_lid_as_wear_surface": False, "top_guide": "REPLACEABLE_WEAR_PAD_ON_STRUCTURAL_SHOULDER",
    "bottom_grip": "RECESSED_BOTTOM_GRIP", "pull_lip_depth_class_mm": [15.0, 20.0],
    "pull_lip_dimension_classification": "REFERENCE_ONLY", "physical_dummy_results": "USER_TEST_PENDING",
}
H25 = {
    "collar": {"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0, "classification": "MEASURED"},
    "set_screws": {"quantity": 2, "nominal": "M4", "major_od_mm": 3.8, "length_mm": 4.0,
                   "projection_mm": 1.0, "angle_deg": 90.0, "pitch": None},
    "captive_washer_required": True,
    "unknowns": {"washer_max_od_mm": None, "washer_stack_thickness_mm": None,
                 "screw_head_max_od_mm": None, "head_height_mm": None,
                 "surface_to_radial_max_mm": None, "full_hardware_axial_width_mm": None},
    "existing_collar_coupons_mm": [16.0, 16.1, 16.2],
    "existing_shank_coupons_mm": [4.1, 4.2, 4.3],
    "existing_shank_classification": "SCREW_SHANK_CLEARANCE_COUPONS",
    "full_hardware_dimensions": "HOLD", "v2_print": "BLOCKED_MEASUREMENT_REQUIRED",
}
SPROCKET = {"teeth": 12, "phase_deg": 15.0, "spacing_deg": 30.0, "tip_radius_mm": 33.07,
            "root_radius_mm": 29.47, "tip_width_mm": 7.5, "root_width_mm": 9.5,
            "axial_width_mm": 44.0, "pitch_diameter_mm": 76.3943726841,
            "root_overlap_mm": 4.0, "external_geometry_delta_mm": 0.0, "radial_access_holes": False}
SERVO = {
    "count_candidate": 2, "bridge": "SERVO_BRIDGE_2020", "bridge_axis": "Y_TRANSVERSE",
    "bridge_x": "PARAMETRIC_ADJUSTABLE", "plate_adjustment_allowance_mm": [-15.0, 15.0],
    "load_path": "SERVO_METAL_PLATE_TNUT_2020_MAIN_FRAME", "petg_sole_reaction_mount": False,
    "generic_display_envelope": "PARAMETRIC_REFERENCE_NOT_COMPONENT_DIMENSION", "final_model": None,
}
CLUTCH = {
    "architecture": "FRAME_INTEGRATED_SLIDE_CLUTCH", "positions": ["DRIVE", "NEUTRAL", "PTO"],
    "simultaneous_drive_pto": "MECHANICALLY_PROHIBITED", "slide_axis": "Y",
    "axis_basis": "PARENT_V0941_PTO_AXIS_Y_AND_V08_INWARD_COAXIAL_SELECTOR",
    "x_axis_comparison": "NOT_SELECTED_FOR_PARENT_CONSISTENCY",
    "coordinate_and_stroke": "HOLD_PHYSICAL_MEASUREMENT", "display_state_offset_mm": 6.0,
    "guide": "TWO_TRANSVERSE_2020_CONTACT_LINES", "contact_lines": 2,
    "carriage": "METAL_PRIMARY_STRUCTURE", "shoes": "REPLACEABLE_POLYMER",
    "servo_continuous_belt_load_holding": False, "operating_reaction": "MECHANICAL_STOP_TO_FRAME",
    "linkage": "SERVO_HORN_ADJUSTABLE_ROD_CLEVIS_CARRIAGE",
    "sensor_reservation": "HALL_PLUS_MAGNET_DRIVE_NEUTRAL_PTO", "servo_torque": "HOLD_FORCE_STROKE_HORN",
}
PTO = {"architecture": "COMMON_PTO_HS_1TO1", "driver_teeth": 20, "driven_teeth": 20,
       "ratio": 1.0, "axis": "Y", "support": "KP000_DOUBLE_SUPPORT", "powered": False}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def box(x: float, y: float, z: float, cx: float = 0, cy: float = 0, cz: float = 0) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def cyl(radius: float, length: float, origin=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0)) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(*origin), cq.Vector(*direction)))


def compound(parts: list[Any]) -> cq.Compound:
    values: list[Any] = []
    for part in parts:
        if isinstance(part, cq.Workplane):
            values.extend(part.vals())
        elif isinstance(part, cq.Compound):
            values.extend(part.Solids())
        else:
            values.append(part)
    return cq.Compound.makeCompound(values)


def export(shape: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))
    if path.suffix.lower() in {".step", ".stp"}:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')", r"\g<1>2000-01-01T00:00:00\2", text)
        # OCCT's process-global product/assembly counters otherwise make two
        # equivalent exports byte-different.  Normalize only descriptive IDs;
        # entity references and geometry remain untouched.
        text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
        occurrence = 0
        def normalize_occurrence(match: re.Match[str]) -> str:
            nonlocal occurrence
            occurrence += 1
            return match.group(1) + str(occurrence) + match.group(2)
        text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", normalize_occurrence, text)
        path.write_text(text, encoding="utf-8", newline="\n")


def audit_dir(rel: str, expected_count: int, expected_hashes: dict[str, str]) -> dict[str, Any]:
    root = REPO_ROOT / rel
    files = [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    actual = {name: sha(root / name) for name in expected_hashes}
    return {"path": rel, "file_count": len(files), "hashes": actual,
            "status": "CAD_PASS" if len(files) == expected_count and actual == expected_hashes else "FAIL"}


def parent_audit() -> dict[str, Any]:
    rows = {rel: audit_dir(rel, count, hashes) for rel, (count, hashes) in PARENT_CONTRACTS.items()}
    return {"lanes": rows, "v0942_baseline_verify": "57_FILES_HASH_PASS_STANDALONE_11_PASS_CONTRACT_24_PASS",
            "status": "CAD_PASS" if all(r["status"] == "CAD_PASS" for r in rows.values()) else "FAIL"}


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"hashes": actual, "status": "CAD_PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    tracked = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").splitlines())
    lane = sorted(x[len(LANE_REL) + 1:] for x in untracked if x.startswith(LANE_REL + "/"))
    outside = [x for x in untracked if not x.startswith(LANE_REL + "/")]
    ignored_lane = git("ls-files", "--others", "-i", "--exclude-standard", "--", LANE_REL).splitlines()
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                 (p.suffix.lower() in {".pyc", ".dxf", ".3mf", ".gcode"} or "__pycache__" in p.parts)]
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "tracked_authority_set_preserved": set(tracked) == set(AUTHORITY_HASHES), "staged_zero": not staged,
        "outside_untracked_preserved": len(outside) == BASE_OUTSIDE_UNTRACKED,
        "lane_scope": set(lane).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane) == set(PACKAGE_PATHS) if complete else True,
        "authority_hashes": authority_audit()["status"] == "CAD_PASS",
        "parent_hashes": parent_audit()["status"] == "CAD_PASS", "ignored_in_lane_zero": not ignored_lane,
        "forbidden_in_lane_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"guard": checks, "tracked": tracked, "staged": staged,
                            "outside_untracked": len(outside), "lane": lane,
                            "ignored_lane": ignored_lane, "forbidden": forbidden})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged,
            "untracked_total": len(untracked), "outside_untracked": len(outside), "lane_untracked": len(lane),
            "checks": checks, "status": "CAD_PASS"}


def frame150() -> cq.Compound:
    parts: list[Any] = []
    for y in (-80.5, 80.5):
        parts += [box(442, 20, 40, 0, y, 88), box(540, 20, 20, 49, y, 208)]
    for x in (-211, 211):
        parts.append(box(20, 181, 20, x, 0, 78))
    for x in (-211, 309):
        parts.append(box(20, 181, 20, x, 0, 208))
    for x in (-211, 211):
        for y in (-80.5, 80.5):
            parts.append(box(20, 20, 110, x, y, 163))
    return compound(parts)


def bbox_pose(angle: float, dx: float, dz: float) -> cq.Workplane:
    body = box(180, 114, 103, -100, 0, 139.5)
    return body.rotate((-10, 0, 139.5), (-10, 1, 139.5), angle).translate((dx, 0, dz))


def bbox_sweep() -> cq.Compound:
    return compound([bbox_pose(0, 0, 0), bbox_pose(2, -25, 1), bbox_pose(4, -55, 2), bbox_pose(6, -90, 3)])


def wear_pad() -> cq.Workplane:
    return box(60, 16, 4, 0, 0, 2).cut(box(44, 8, 2, 0, 0, 3.5)).clean()


def bottom_grip() -> cq.Workplane:
    return box(70, 24, 18, 0, 0, 9).cut(box(48, 18, 11, 0, -5, 4)).clean()


def h25_full_hardware_reference() -> cq.Compound:
    collar = cq.Workplane("XY").circle(15.9 / 2).circle(10.1 / 2).extrude(3)
    screw_x = cyl(1.9, 4.0, (5.05, 0, 1.5), (1, 0, 0))
    screw_y = cyl(1.9, 4.0, (0, 5.05, 1.5), (0, 1, 0))
    # Thin cross markers are measurement datums, never washer/head envelopes.
    hold_x = compound([box(0.6, 24, 0.6, 12, 0, 1.5), box(8, 0.6, 0.6, 12, 0, 1.5)])
    hold_y = compound([box(24, 0.6, 0.6, 0, 12, 1.5), box(0.6, 8, 0.6, 0, 12, 1.5)])
    return compound([collar, screw_x, screw_y, hold_x, hold_y])


def servo_bridge() -> cq.Compound:
    bridge = box(20, 181, 20, 249, 0, 208)
    plates = [servo_plate(1), servo_plate(-1)]
    envelopes = [box(45, 30, 45, 249, sign * 43, 243.5) for sign in (1, -1)]
    return compound([bridge, *plates, *envelopes])


def servo_plate(sign: int) -> cq.Workplane:
    plate = box(70, 42, 3, 249, sign * 43, 219.5)
    for x in (229, 269):
        plate = plate.cut(box(20, 4, 5, x, sign * 43, 219.5))
    return plate.clean()


def slide_shoe() -> cq.Workplane:
    return box(26, 34, 7, 0, 0, 3.5).cut(box(20.6, 24, 5, 0, 0, 5.5)).clean()


def carriage() -> cq.Workplane:
    plate = box(80, 28, 5, 0, 0, 2.5)
    for x in (-30, 30):
        plate = plate.cut(cyl(3, 7, (x, 0, -1)))
    return plate.clean()


def state_stop(kind: str) -> cq.Compound:
    offset = {"DRIVE": -6.0, "NEUTRAL": 0.0, "PTO": 6.0}[kind]
    return compound([box(8, 3, 12, 279, 40 + offset, 228), box(8, 3, 12, 279, -40 - offset, 228)])


def slide_architecture() -> cq.Compound:
    existing_front_cross = box(20, 181, 20, 309, 0, 208)
    new_bridge = box(20, 181, 20, 249, 0, 208)
    parts: list[Any] = [existing_front_cross, new_bridge]
    for sign in (1, -1):
        y = sign * 40
        parts.append(carriage().translate((279, y, 222)))
        for x in (249, 309):
            parts.append(slide_shoe().translate((x, y, 218)))
        parts.append(cyl(2, 28, (249, sign * 52, 236), (0, -sign, 0)))
    parts += [state_stop("DRIVE"), state_stop("NEUTRAL"), state_stop("PTO")]
    for y in (-52, -46, -40, 40, 46, 52):
        parts.append(box(8, 4, 4, 289, y, 238))
    return compound(parts)


def pitch_gauge() -> cq.Compound:
    parts: list[Any] = [box(100, 42, 3, 0, 0, 1.5)]
    for index, angle in enumerate((0.0, 2.0, 4.0, 6.0)):
        bar = box(75, 4, 3, 5, -15 + index * 10, 5)
        parts.append(bar.rotate((-32.5, 0, 5), (-32.5, 1, 5), angle))
    return compound(parts)


def full_service() -> cq.Compound:
    cbox = box(180, 94, 45, 100, 0, 132.5)
    pto = [box(50, 30, 50, 215, sign * 52, 160) for sign in (1, -1)]
    belts = [box(60, 15, 70, 215, sign * 68, 150) for sign in (1, -1)]
    pads = [wear_pad().translate((-135, sign * 50, 194)) for sign in (1, -1)]
    grip = bottom_grip().translate((-170, 0, 80))
    return compound([frame150(), bbox_sweep(), cbox, servo_bridge(), slide_architecture(), *pto, *belts, *pads, grip])


def artifact_jobs() -> list[tuple[Any, str]]:
    return [
        (frame150(), CAD[0]), (bbox_sweep(), CAD[1]), (wear_pad(), CAD[2]), (bottom_grip(), CAD[3]),
        (h25_full_hardware_reference(), CAD[4]), (servo_bridge(), CAD[5]), (servo_plate(1), CAD[6]),
        (servo_plate(-1), CAD[7]), (slide_architecture(), CAD[8]), (carriage(), CAD[9]),
        (slide_shoe(), CAD[10]), (state_stop("DRIVE"), CAD[11]), (state_stop("NEUTRAL"), CAD[12]),
        (state_stop("PTO"), CAD[13]), (full_service(), CAD[14]), (wear_pad(), CAD[15]),
        (slide_shoe(), CAD[16]), (pitch_gauge(), CAD[17]), (pitch_gauge(), CAD[18]),
    ]


def common_volume(a: Any, b: Any) -> float:
    sa = a.val() if isinstance(a, cq.Workplane) else a
    sb = b.val() if isinstance(b, cq.Workplane) else b
    return float(sa.intersect(sb).Volume())


def collision_report() -> dict[str, Any]:
    corridor = box(380, 114, 112, -200, 0, 145)
    cbox = box(180, 94, 45, 100, 0, 132.5)
    bridge = box(20, 181, 20, 249, 0, 208)
    clutch = box(80, 130, 35, 279, 0, 228)
    pto = compound([box(50, 30, 50, 215, s * 52, 160) for s in (1, -1)])
    belt = compound([box(60, 15, 70, 215, s * 68, 150) for s in (1, -1)])
    pairs = [("BBOX_SWEEP_SERVO_BRIDGE", corridor, bridge), ("BBOX_SWEEP_CLUTCH", corridor, clutch),
             ("BBOX_SWEEP_CBOX", corridor, cbox), ("SERVO_BRIDGE_PTO", bridge, pto),
             ("SERVO_BRIDGE_BELT", bridge, belt), ("CLUTCH_CBOX", clutch, cbox)]
    rows = []
    for name, a, b in pairs:
        volume = common_volume(a, b)
        rows.append({"check": name, "common_volume_mm3": round(volume, 6), "status": "CAD_PASS" if volume < 1e-7 else "FAIL"})
    return {"method": "CADQUERY_ACTUAL_SHAPE_COMMON_VOLUME_ON_PARAMETRIC_RESERVED_ENVELOPES",
            "rows": rows, "all_zero": all(r["status"] == "CAD_PASS" for r in rows),
            "physical_transform_status": "HOLD_ACTUAL_SERVO_AND_CLUTCH_MEASUREMENTS"}


def source_trace() -> list[dict[str, str]]:
    paths = [
        f"{P2_REL}/dimensions.json", f"{P2_REL}/interfaces.json", f"{P1_REL}/interfaces.json",
        "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/build_common_rover_front_drive_dual_pto_v008.py",
        "cad/common_rover/common_rover_powertrain_frame_belt_design_authority_v0_9_0/common_rover_slide_clutch_contract_v090.md",
        "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0/candidate_slide_clutch_report_v0930.md",
        "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0/candidate_trade_matrix_v0930.csv",
    ]
    return [{"path": p, "sha256": sha(REPO_ROOT / p)} for p in paths]


def dimensions() -> dict[str, Any]:
    return {"version": VERSION, "classification": CLASSIFICATION, "frame": FRAME, "battery": BATTERY,
            "bbox": BBOX, "h25a1": H25, "protected_12t": SPROCKET, "servo": SERVO, "clutch": CLUTCH, "pto": PTO}


def interfaces() -> dict[str, Any]:
    return {
        "bbox": {"layout": "BBOX_REAR_CBOX_FRONT_X_SERIAL", "motion": BBOX["service_motion"],
                 "load_path": "FRAME_SUPPORT_TO_BBOX_STRUCTURAL_SHOULDER", "lid_wear_contact": False},
        "h25a1": {"insertion": "OPEN_TOP_OR_SIDE_SERVICE_CAPTURE_POCKET",
                  "torque_path": "SHAFT_SET_SCREWS_METAL_COLLAR_CONTROLLED_METAL_FEATURES_REPLACEABLE_REACTION_KEY_PETG_HUB_12T",
                  "washer_primary_torque_feature": False, "cover_primary_torque": False},
        "servo": {"count": 2, "support": SERVO["load_path"], "continuous_belt_reaction": False},
        "clutch": {"axis": "Y", "guide": CLUTCH["guide"], "positions": CLUTCH["positions"],
                    "operating_reaction": CLUTCH["operating_reaction"]},
        "pto": PTO,
    }


def hardware() -> dict[str, Any]:
    return {"h25a1_full_hardware_envelope": {**H25, "cad_marker_policy":
            "UNKNOWN_WASHER_HEAD_EXTENTS_ARE_DATUM_MARKERS_NOT_GUESSED_SOLIDS"},
            "servo": {"model": None, "body_xyz": None, "mount_holes": None, "output_center": None,
                      "horn_radius": None, "voltage": None, "rated_torque": None, "waterproof": None},
            "clutch": {"metal_carriage": True, "replaceable_shoes": True, "final_material": "HOLD",
                       "hall_sensor_model": None, "magnet_model": None}}


def service_motions() -> dict[str, Any]:
    return {"bbox": {"name": BBOX["service_motion"], "selected_x_direction": "-X_REFERENCE",
                     "sequence": ["SYSTEM_OFF", "DISCONNECT_CONNECTOR", "RELEASE_SAFETY_RETAINER",
                                  "RELEASE_PRIMARY_LOCK", "GRIP_BOTTOM", "LIFT_LOWER_SIDE",
                                  "APPROACH_TOP_GUIDE_TO_FRAME_UNDERSIDE", "APPLY_SMALL_PITCH",
                                  "SLIDE_SELECTED_X", "COMPLETE_REMOVAL"],
                     "reference_pitch_deg": BBOX["reference_pitch_deg"], "actual_pitch": "PHYSICAL_TEST_REQUIRED",
                     "test_grid": {str(h): ["STRAIGHT_X_REMOVAL", "PITCH_AND_SLIDE", "TOP_CONTACT",
                                                  "LOWER_GRIP_ACCESS", "SNAGGING", "FRAME_SCRATCH",
                                                  "REQUIRED_PITCH_APPROX", "SERVICE_EFFORT"] for h in (103, 105, 107)}},
            "clutch": {"axis": "Y", "sequence": ["DRIVE", "NEUTRAL", "PTO"],
                       "motor_state_for_shift": "OFF_ZERO_ROTATION", "powered_test": False}}


def test_limits() -> dict[str, Any]:
    return {"bbox_reference_pitch_deg": [0, 2, 4, 6], "bbox_physical_pass_required": True,
            "top_contact_allowed": ["NONE", "LIGHT_AT_REPLACEABLE_GUIDE_ONLY"],
            "clutch_force_test": ["BREAKAWAY", "AVERAGE", "APPROACH_DRIVE_STOP", "APPROACH_PTO_STOP"],
            "clutch_powered": False, "h25_static_torque_future_nm": [0.25, 0.50, 0.75],
            "h25_v2_test_blocked": True, "powered_rotation": False, "field": False}


def measurement_ledger() -> dict[str, Any]:
    measured = [
        ("FRAME_STRUCTURAL_HEIGHT", 150.0), ("BATTERY_INSERTION_CLEAR_HEIGHT", 108.0),
        ("BATTERY_BODY_XYZ", [150.9, 99.4, 92.5]), ("BATTERY_MASS", 1.2),
        ("COLLAR_OD", 15.9), ("COLLAR_ID", 10.1), ("COLLAR_WIDTH", 3.0),
        ("SET_SCREW_COUNT", 2), ("SET_SCREW_ANGLE", 90.0), ("SET_SCREW_LENGTH", 4.0),
        ("SET_SCREW_PROJECTION", 1.0),
    ]
    holds = ["WASHER_MAX_OD", "WASHER_STACK_THICKNESS", "SCREW_HEAD_MAX_OD", "SCREW_HEAD_HEIGHT",
             "FULL_HARDWARE_AXIAL_WIDTH", "CENTER_TO_RADIAL_MAX_ENVELOPE", "SERVO_BODY_XYZ",
             "SERVO_MOUNT_HOLES", "SERVO_OUTPUT_CENTER", "SERVO_HORN_RADIUS", "SERVO_VOLTAGE",
             "SERVO_RATED_TORQUE", "SERVO_WATERPROOF", "CLUTCH_DRIVE_COORDINATE",
             "CLUTCH_NEUTRAL_COORDINATE", "CLUTCH_PTO_COORDINATE", "CLUTCH_TOTAL_STROKE",
             "CLUTCH_MANUAL_LINEAR_FORCE"]
    rows = [{"id": f"M{i:03d}", "name": name, "value": value, "classification": "MEASURED"}
            for i, (name, value) in enumerate(measured, 1)]
    rows += [{"id": f"H{i:03d}", "name": name, "value": None, "classification": "HOLD_MEASUREMENT_REQUIRED"}
             for i, name in enumerate(holds, 1)]
    return {"schema": "paddy_swarm.common_rover.service_servo_clutch.measurements.v0.9.4.3", "rows": rows}


def stl_semantic(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"bad binary STL: {path}")
    mins, maxs, positive = [math.inf] * 3, [-math.inf] * 3, 0
    for i in range(count):
        vals = struct.unpack_from("<12f", data, 84 + 50 * i)
        pts = [vals[3:6], vals[6:9], vals[9:12]]
        a = [pts[1][j] - pts[0][j] for j in range(3)]
        b = [pts[2][j] - pts[0][j] for j in range(3)]
        cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        positive += sum(x * x for x in cross) > 1e-12
        for p in pts:
            for j in range(3):
                mins[j], maxs[j] = min(mins[j], p[j]), max(maxs[j], p[j])
    if positive != count:
        raise RuntimeError(f"degenerate STL: {path}")
    return {"triangles": count, "bounds_mm": [maxs[j] - mins[j] for j in range(3)]}


def geometry_manifest() -> dict[str, Any]:
    report = collision_report()
    return {"schema": "paddy_swarm.common_rover.service_servo_clutch.geometry.v0.9.4.3",
            "classification": CLASSIFICATION, "release": RELEASE, "cad_count": len(CAD),
            "step_count": len([p for p in CAD if p.endswith(".step")]),
            "stl_count": len([p for p in CAD if p.endswith(".stl")]),
            "step_contract": "RELOAD_VALID_AND_BYTE_REPRODUCIBLE_AFTER_TIMESTAMP_NORMALIZATION",
            "stl_contract": "BINARY_ALL_TRIANGLES_POSITIVE_AND_BYTE_REPRODUCIBLE",
            "full_hardware": {"known_solids": ["COLLAR", "M4_SET_SCREW_X", "M4_SET_SCREW_Y"],
                              "hold_datums": ["WASHER_HEAD_X", "WASHER_HEAD_Y"],
                              "final_v2_fixture_stl_generated": False},
            "slide_axis": {"selected": "Y", "basis": CLUTCH["axis_basis"], "final_coordinate": None},
            "interference": report, "protected_12t": SPROCKET,
            "parent_audit": parent_audit()}


def validation() -> dict[str, Any]:
    checks = {
        "FRAME_150_BASELINE": "CAD_PASS", "BBOX_PITCH_AND_SLIDE_ARCHITECTURE": "CAD_PASS_CANDIDATE",
        "BBOX_FINAL_HEIGHT": "USER_DUMMY_TEST_PENDING", "BBOX_TOP_GUIDE": "DESIGN_CANDIDATE",
        "H25A1_COLLAR_BODY_COUPONS": "USER_TEST_PENDING", "H25A1_SHANK_COUPONS": "USER_TEST_PENDING",
        "H25A1_FULL_HARDWARE_ENVELOPE": "HOLD_WASHER_HEAD_MEASUREMENTS",
        "H25A1_V2_FIXTURE": "BLOCKED_MEASUREMENT_REQUIRED", "SERVO_BRIDGE": "ARCHITECTURE_PASS_CANDIDATE",
        "SERVO_FINAL_MOUNT": "HOLD_SERVO_DIMENSIONS", "SLIDE_CLUTCH": "ARCHITECTURE_PASS_CANDIDATE",
        "CLUTCH_FINAL_CARRIAGE": "HOLD_STROKE_FORCE", "FRAME_BRACING": "OBSERVATION_ONLY_LOAD_VALIDATION_HOLD",
        "POWERED_ROTATION": "NOT_APPROVED", "FIELD": "NOT_APPROVED",
    }
    missing = [r["name"] for r in measurement_ledger()["rows"] if r["classification"].startswith("HOLD")]
    return {"version": VERSION, "classification": CLASSIFICATION, "release": RELEASE, "checks": checks,
            "missing_measurements": missing, "architecture_cad_complete": True,
            "manufacturing_inputs_complete": False, "powered_rotation_approved": False,
            "field_approved": False, "final_status": FINAL_STATUS}


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nStatus: `{FINAL_STATUS}`\n"


def documents(valid: dict[str, Any]) -> dict[str, str]:
    h = lambda title: header(title)
    d: dict[str, str] = {}
    d["README.md"] = h("Common Rover Service Motion / Servo / Slide Clutch / H2.5-A1") + "\nThis lane is a non-powered architecture and measurement handoff. It preserves v0.9.4.2, the protected 12T tooth form, the 150 mm compact frame candidate, BBOX-rear/CBOX-front serial service, and the 20:20 KP000-supported PTO. No manufacturing or field release is made.\n"
    d["PARENT_AUDIT.md"] = h("Parent audit") + "\n- v0.9.4.2: 57 files, protected hashes PASS, standalone rebuild 11/11 PASS, contract 24/24 PASS.\n- v0.9.4.1: 68 files, protected hashes PASS.\n- v0.9.4.0: 43 files, protected hashes PASS.\n- All three parent lanes are read-only and their current hashes are recorded in `geometry_manifest.json`.\n"
    trace = source_trace()
    d["SOURCE_TRACE.md"] = h("Source trace") + "\n" + "\n".join(f"- `{r['path']}` — `{r['sha256']}`" for r in trace) + "\n\nAxis finding: v0.9.4.1 records PTO axis Y; v0.8 uses inward Y-axis motor shafts and coaxial slider envelopes. v0.9.3.0 Candidate A's X-axis selector is retained only as a comparison. Parent-consistent recommendation: Y-axis slide; physical state coordinates remain HOLD.\n"
    d["H25A1_FULL_HARDWARE_UPDATE.md"] = h("H2.5-A1 full-hardware update") + "\nThe final fit object is collar + two 90° M4 set screws + captive/non-removable washer hardware + screw-head envelope. Existing 4.1/4.2/4.3 coupons remain screw-shank-only tests; 16.00/16.10/16.20 remain collar-body OD tests. Neither validates full hardware. Protected 12T external geometry delta remains 0 and no radial tooth/root holes are introduced.\n"
    d["H25A1_FULL_HARDWARE_MEASUREMENT_SHEET.md"] = h("H2.5-A1 full-hardware measurement sheet") + "\n|Item|Value|Class|\n|---|---:|---|\n|Collar OD|15.9 mm|MEASURED|\n|Collar ID|10.1 mm|MEASURED|\n|Collar width|3.0 mm|MEASURED|\n|Set screws|2 × M4, 90°|MEASURED/CONFIRMED|\n|Length / tightened projection|4.0 / 1.0 mm|MEASURED|\n|Washer maximum OD|______|REQUIRED|\n|Washer stack thickness|______|REQUIRED|\n|Screw-head maximum OD|______|REQUIRED|\n|Head height|______|REQUIRED|\n|Collar surface → highest installed point|______|REQUIRED|\n|Full-hardware axial width|______|REQUIRED|\n"
    d["H25A1_FULL_HARDWARE_FIT_ARCHITECTURE.md"] = h("H2.5-A1 full-hardware fit architecture") + "\nUse an open-top or central side-service capture pocket: full collar assembly enters axially/open-side, a replaceable dual reaction key receives controlled metal reaction features, and a removable cover closes the hub. Washer clearance is free; washers and cover bolts are not the primary torque path. The STEP contains exact known collar/screw solids and explicit HOLD datum markers—not guessed washer/head solids.\n"
    d["H25A1_STATIC_FIXTURE_V2_SPEC.md"] = h("H2.5-A1 static fixture V2 specification") + "\n`V2_FULL_HARDWARE_FIXTURE` must accept the collar, both screws, captive washers and heads without alteration. Final coupon/fixture pocket and STL are `BLOCKED_MEASUREMENT_REQUIRED`. After dimensional closure only: 0.25 → 0.50 → 0.75 N·m static inspection; powered rotation remains NOT_APPROVED.\n"
    d["BBOX_PITCH_AND_SLIDE_SERVICE.md"] = h("BBOX pitch-and-slide service") + "\nThe service architecture is no longer pure horizontal X removal. With system off: disconnect, release safety and primary locks, grip the lower recess, slightly lift the lower side, approach the replaceable top guide to the upper-frame underside, apply a small pitch, then slide −X reference and fully remove. CAD compares 0/2/4/6° only; the required angle is PHYSICAL_TEST_REQUIRED.\n"
    d["BBOX_TOP_GUIDE_ARCHITECTURE.md"] = h("BBOX replaceable top-guide architecture") + "\nLoad/service hierarchy: aluminum-frame underside → replaceable wear pad/top guide → BBOX structural shoulder → protected waterproof lid. Direct lid/frame sliding is REJECTED. PETG is a prototype coupon material; POM/UHMW-PE are later wear candidates. The pad is independently replaceable and cannot disturb gasket preload.\n"
    d["BBOX_BOTTOM_GRIP_ARCHITECTURE.md"] = h("BBOX bottom-grip architecture") + "\nUse a recessed rear-bottom pull lip referenced to the structural bottom/shoulder, not a thin waterproof wall. The 15–20 mm class is REFERENCE_ONLY. Muddy-glove access, snagging, box mass, edge radii and final depth remain physical-test inputs.\n"
    d["BBOX_SERVICE_TEST_UPDATE.md"] = h("BBOX service-test update") + "\nFor 103/105/107 mm, record straight-X removal, pitch-and-slide, top contact NONE/LIGHT/HARD, lower-grip GOOD/MARGINAL/BAD, snagging, frame scratch, approximate pitch, and LOW/MEDIUM/HIGH effort. Current dummy and coupon results remain USER_TEST_PENDING; do not infer PASS from CAD.\n"
    d["SERVO_BRIDGE_ARCHITECTURE.md"] = h("Servo Bridge architecture") + "\n`SERVO_BRIDGE_2020` is a transverse adjustable-X upper-frame member serving two independent generic servo mounting zones and restoring a Y brace. Metal adapter plates and T-nuts carry reaction into 2020; PETG is auxiliary only. The displayed servo boxes are packaging references, not servo dimensions. Final cut length and X are PHYSICAL_CHECK_REQUIRED.\n"
    d["SERVO_MEASUREMENT_SHEET.md"] = h("Servo measurement sheet") + "\nModel: ______  \nBody X/Y/Z: ______ / ______ / ______  \nMount-hole pattern: ______  \nOutput center and mount-face offset: ______  \nHorn radius: ______  \nVoltage: ______  \nRated torque: ______  \nWaterproof status: ______  \n\nFinal selection and mounting remain HOLD.\n"
    d["SLIDE_CLUTCH_ARCHITECTURE.md"] = h("Frame-integrated slide-clutch architecture") + "\nSelected architecture: Y-axis coaxial slide, consistent with parent v0.9.4.1 PTO axis Y and v0.8 inward selector source. Two transverse 2020 contact lines—adjustable Servo Bridge plus the existing front upper crossmember—support independent left/right metal carriages through replaceable polymer shoes. X-axis longitudinal-frame sliding remains a comparison, not the parent-consistent recommendation. Display state offsets are schematic; actual stroke is HOLD.\n"
    d["SLIDE_CLUTCH_MEASUREMENT_SHEET.md"] = h("Slide-clutch measurement sheet") + "\nSlide axis (confirm Y/X/other): ______  \nDRIVE coordinate: ______  \nNEUTRAL coordinate: ______  \nPTO coordinate: ______  \nDRIVE→NEUTRAL stroke: ______  \nNEUTRAL→PTO stroke: ______  \nTotal stroke: ______  \nPeak manual linear force: ______  \nOperating belt tension: ______  \nPulley/belt clearance envelope: ______\n"
    d["CLUTCH_FORCE_TEST_PLAN.md"] = h("Clutch force test plan") + "\nMotor OFF and zero rotation. Align a luggage scale/force gauge with the confirmed slide axis. Record breakaway force, average force, and forces approaching DRIVE and PTO stops in both directions. Do not energize. Servo torque selection remains HOLD until force × effective horn radius and a safety factor can be evaluated.\n"
    d["CLUTCH_POSITION_INTERLOCK.md"] = h("Clutch position and interlock") + "\nThe only sequence is DRIVE ↔ NEUTRAL ↔ PTO. A single carriage geometry cannot occupy both engagement ends. DRIVE and PTO have positive structural hard stops; NEUTRAL has a positive center definition/detent. Operating belt reaction terminates in frame/carriage stops, never continuous servo gear hold. Hall+magnet zones are reserved for all three positions; software alone is insufficient. SAFE_NEUTRAL_BIAS remains a comparison pending belt mechanics.\n"
    d["FRAME_BRACE_ROLE_REPORT.md"] = h("Frame brace role report") + "\nThe Servo Bridge restores an upper transverse load path where belt clearance may have removed an older Y crossmember, and provides a second local clutch guide line with the existing front crossmember. This improves architecture-level torsional continuity, but no section stress, joint slip, modal, or load test is available; structural PASS is not claimed.\n"
    cr = collision_report()
    d["INTERFERENCE_REPORT.md"] = h("Interference report") + "\nReference common-volume checks:\n" + "\n".join(f"- `{r['check']}`: {r['common_volume_mm3']:.6f} mm³ — `{r['status']}`" for r in cr["rows"]) + "\n\nThese are parametric reserved-envelope checks only. Actual servo, horn, bolt-tip, sensor, washer/head, clutch stroke, belt and linkage transforms remain HOLD.\n"
    d["SERVICEABILITY_REPORT.md"] = h("Serviceability report") + "\nBBOX rear/CBOX front X-serial layout remains. The architecture corridor places the front Servo Bridge/clutch reference outside the rear pitch-slide sweep and keeps the waterproof lid out of wear contact. Shoes, top pad, reaction key, linkage rod and servo plate are independently serviceable. Belt removal/tool envelopes require physical transforms.\n"
    d["MISSING_MEASUREMENTS.md"] = h("Missing measurements") + "\nPriority order:\n" + "\n".join(f"{i}. `{name}`" for i, name in enumerate(valid["missing_measurements"], 1)) + "\n\nThese do not block reference CAD, but block final full-hardware pocket, servo plate, carriage, stops, linkage, sensor and manufacturing release.\n"
    d["DESIGN_GATE.md"] = h("Design gate") + "\n" + "\n".join(f"- `{k}`: `{v}`" for k, v in valid["checks"].items()) + "\n\nSupport-plate machining, shaft cutting, drilling, powered rotation, load/water/mud tests and field deployment remain HOLD/NOT_APPROVED.\n"
    return d


def svg(title: str, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520"><style>text{{font-family:Arial;fill:#17212b}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.g{{fill:#d9eafd;stroke:#245b8a}}.h{{fill:#fde2e2;stroke:#a33}}.u{{fill:#fff2b2;stroke:#a26f00;stroke-dasharray:8 5}}.a{{fill:none;stroke:#168aad;stroke-width:4;marker-end:url(#m)}}.d{{stroke:#667;stroke-dasharray:7 5}}</style><defs><marker id="m" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#168aad"/></marker></defs><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="32" font-size="22">{title}</text>{body}<text x="24" y="500" font-size="13">v0.9.4.3 · REFERENCE ONLY · HOLD · NOT FOR MANUFACTURING</text></svg>'


def drawings() -> None:
    values = {
        "bbox_pitch_slide_side.svg": '<rect class="g" x="170" y="250" width="300" height="170"/><rect class="f" x="170" y="120" width="640" height="24"/><g transform="rotate(-6 470 250)"><rect class="h" x="470" y="250" width="250" height="145"/></g><path class="a" d="M470 330H130"/><text x="505" y="235">0/2/4/6° REFERENCE SWEEP</text><text x="500" y="170">replaceable pad; lid protected</text>',
        "bbox_service_sequence.svg": '<text x="70" y="95">OFF → DISCONNECT → SAFETY → LOCK → GRIP → LIFT → GUIDE → PITCH → −X SLIDE → REMOVE</text><path class="a" d="M80 130H900"/><rect class="g" x="100" y="190" width="150" height="150"/><rect class="h" x="420" y="180" width="150" height="150" transform="rotate(-4 495 255)"/><rect class="u" x="730" y="175" width="150" height="150"/><text x="115" y="365">SEATED</text><text x="435" y="365">PITCH</text><text x="750" y="365">REMOVED</text>',
        "h25a1_full_hardware_section.svg": '<circle class="g" cx="300" cy="270" r="80"/><circle class="f" cx="300" cy="270" r="51"/><path class="h" d="M380 252H520V288H380M282 190V70H318V190"/><circle class="u" cx="520" cy="270" r="55"/><circle class="u" cx="300" cy="70" r="55"/><text x="600" y="180">washer/head extents = HOLD</text><text x="600" y="220">datum markers ≠ envelope solids</text><text x="600" y="260">open-top / side service</text><text x="600" y="300">washer not torque dog</text>',
        "h25a1_measurement_map.svg": '<circle class="g" cx="330" cy="270" r="80"/><path class="h" d="M410 250H600V290H410M310 190V80H350V190"/><path class="d" d="M330 270H700M330 270V60"/><text x="705" y="275">radial max ______</text><text x="355" y="75">washer/head OD ______</text><text x="590" y="330">axial width / stack ______</text>',
        "servo_bridge_top.svg": '<rect class="f" x="110" y="100" width="780" height="300"/><rect class="g" x="450" y="100" width="30" height="300"/><rect class="g" x="700" y="100" width="30" height="300"/><rect class="h" x="390" y="140" width="150" height="75"/><rect class="h" x="390" y="285" width="150" height="75"/><text x="330" y="85">Servo Bridge X adjustable</text><text x="740" y="120">existing front crossmember</text><text x="560" y="470">two Y guide/contact lines</text>',
        "servo_bridge_front.svg": '<rect class="g" x="180" y="300" width="640" height="35"/><rect class="h" x="280" y="210" width="150" height="90"/><rect class="h" x="570" y="210" width="150" height="90"/><path class="a" d="M355 210V150M645 210V150"/><text x="310" y="130">generic servo envelopes</text><text x="300" y="370">metal plate → T-nut → 2020 → frame</text>',
        "slide_clutch_positions.svg": '<path class="d" d="M130 260H870"/><rect class="h" x="210" y="210" width="120" height="100"/><rect class="u" x="440" y="210" width="120" height="100"/><rect class="g" x="670" y="210" width="120" height="100"/><path class="a" d="M330 330H440M560 330H670"/><text x="230" y="190">DRIVE stop</text><text x="455" y="190">NEUTRAL</text><text x="700" y="190">PTO stop</text><text x="310" y="390">Y-axis schematic; actual stroke HOLD</text>',
        "slide_clutch_guide_section.svg": '<rect class="g" x="220" y="280" width="560" height="60"/><rect class="u" x="250" y="255" width="500" height="25"/><rect class="h" x="270" y="220" width="460" height="35"/><text x="300" y="195">metal carriage</text><text x="300" y="270">replaceable polymer shoe</text><text x="300" y="375">2020 frame surface; no loose T-nut bearing</text>',
        "servo_linkage_concept.svg": '<circle class="g" cx="220" cy="250" r="70"/><path class="a" d="M270 220L690 300"/><rect class="h" x="690" y="255" width="150" height="90"/><text x="130" y="360">servo horn</text><text x="360" y="200">adjustable rod + clevis</text><text x="700" y="380">carriage to hard stop</text>',
        "bbox_vs_clutch_service_clearance.svg": '<rect class="h" x="70" y="210" width="340" height="180"/><path class="a" d="M410 300H60"/><rect class="g" x="650" y="100" width="40" height="300"/><rect class="u" x="720" y="180" width="190" height="110"/><text x="100" y="190">BBOX rear service sweep</text><text x="630" y="85">servo bridge</text><text x="730" y="165">clutch / PTO reserved</text><text x="430" y="440">reference common volume = 0; actual transforms HOLD</text>',
    }
    for name, body in values.items():
        write(LANE / "drawings" / name, svg(name.replace("_", " "), body))


def build() -> dict[str, Any]:
    before = repository_guard(False)
    for shape, rel in artifact_jobs():
        export(shape, LANE / rel)
    drawings()
    valid = validation()
    payloads = {
        "dimensions.json": dimensions(), "interfaces.json": interfaces(), "hardware.json": hardware(),
        "service_motions.json": service_motions(), "test_limits.json": test_limits(),
        "measurement_ledger.json": measurement_ledger(), "geometry_manifest.json": geometry_manifest(),
        "validation_report.json": valid,
    }
    for name, value in payloads.items():
        write_json(LANE / name, value)
    for name, value in documents(valid).items():
        write(LANE / name, value)
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS))
    write(LANE / "BUILD_LOG.txt", f"BUILD PASS\nversion={VERSION}\nPython={sys.version.split()[0]}\nCadQuery={cq.__version__}\npreflight_untracked={before['untracked_total']}\noutside_untracked={before['outside_untracked']}\nparent_v0942=57_HASH_AND_24_TEST_PASS\nslide_axis=Y_PARENT_CONSISTENT\nphysical_release=HOLD")
    write(LANE / "TEST_LOG.txt", "PENDING_TEST_EXECUTION")
    hashed = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / p)}  {p}" for p in hashed))
    test = subprocess.run([sys.executable, "-B", str(LANE / SOURCE[1])], cwd=REPO_ROOT,
                          text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test.returncode:
        raise RuntimeError(test.stdout)
    write(LANE / "TEST_LOG.txt", test.stdout)
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / p)}  {p}" for p in hashed))
    return {"status": "CAD_PASS", "guard": repository_guard(True), "validation": valid}


def verify_files() -> dict[str, Any]:
    missing = [p for p in PACKAGE_PATHS if not (LANE / p).is_file()]
    extras = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                    "__pycache__" not in p.parts and p.relative_to(LANE).as_posix() not in PACKAGE_PATHS)
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    hashes: dict[str, str] = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        hashes[rel] = digest
    expected_hashed = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    bad_hashes = [p for p, value in hashes.items() if sha(LANE / p) != value]
    step_rows = {}
    for rel in [p for p in CAD if p.endswith(".step")]:
        shape = cq.importers.importStep(str(LANE / rel)).val()
        step_rows[rel] = {"valid": shape.isValid(), "volume_mm3": shape.Volume()}
    stl_rows = {rel: stl_semantic(LANE / rel) for rel in CAD if rel.endswith(".stl")}
    dim = json.loads((LANE / "dimensions.json").read_text(encoding="utf-8"))
    valid = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    geom = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
    checks = {
        "package": not missing and not extras and manifest == PACKAGE_PATHS,
        "hashes": not bad_hashes and set(hashes) == expected_hashed,
        "cad_counts": len(step_rows) == 16 and len(stl_rows) == 3,
        "step_reload": all(r["valid"] and r["volume_mm3"] > 0 for r in step_rows.values()),
        "frame": dim["frame"]["structural_height_mm"] == 150.0,
        "battery": dim["battery"] == BATTERY,
        "bbox": dim["bbox"]["service_motion"] == "BBOX_PITCH_AND_SLIDE_SERVICE_MOTION" and not dim["bbox"]["waterproof_lid_as_wear_surface"],
        "h25": dim["h25a1"]["captive_washer_required"] and dim["h25a1"]["full_hardware_dimensions"] == "HOLD",
        "sprocket": dim["protected_12t"] == SPROCKET,
        "servo": dim["servo"]["count_candidate"] == 2 and dim["servo"]["final_model"] is None,
        "clutch": dim["clutch"]["slide_axis"] == "Y" and dim["clutch"]["positions"] == ["DRIVE", "NEUTRAL", "PTO"] and not dim["clutch"]["servo_continuous_belt_load_holding"],
        "pto": dim["pto"]["driver_teeth"] == dim["pto"]["driven_teeth"] == 20 and dim["pto"]["ratio"] == 1.0,
        "interference": geom["interference"]["all_zero"],
        "release": not valid["powered_rotation_approved"] and not valid["field_approved"],
        "no_v2_fixture_stl": not any("fixture" in p.lower() and p.endswith(".stl") for p in PACKAGE_PATHS),
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "missing": missing, "extras": extras, "bad_hashes": bad_hashes})
    return {"status": "CAD_PASS", "file_count": len(PACKAGE_PATHS), "step_count": len(step_rows),
            "stl_count": len(stl_rows), "checks": checks, "bad_hashes": bad_hashes}


def standalone_rebuild() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ps_cr_v0943_a_") as a, tempfile.TemporaryDirectory(prefix="ps_cr_v0943_b_") as b:
        aa, bb = Path(a), Path(b)
        for shape, rel in artifact_jobs():
            export(shape, aa / rel)
        for shape, rel in artifact_jobs():
            export(shape, bb / rel)
        equal = {rel: sha(aa / rel) == sha(bb / rel) for rel in CAD}
        step_valid = {rel: cq.importers.importStep(str(aa / rel)).val().isValid() for rel in CAD if rel.endswith(".step")}
        stls = {rel: stl_semantic(aa / rel) for rel in CAD if rel.endswith(".stl")}
        checks = {"outputs": len(equal) == len(CAD), "byte_reproducible": all(equal.values()),
                  "step_reload": all(step_valid.values()), "stl_semantic": len(stls) == 3}
        if not all(checks.values()):
            raise RuntimeError({"checks": checks, "byte_equal": equal})
        return {"status": "CAD_PASS", "artifact_count": len(equal), "step_count": len(step_valid),
                "stl_count": len(stls), "checks": checks}


def make_zip() -> tuple[Path, str]:
    path = DOWNLOADS / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, rel)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        bad = [n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
        if archive.testzip() or len(names) != len(set(names)) or bad or sorted(names) != PACKAGE_PATHS:
            raise RuntimeError("ZIP contract failed")
        manifest = archive.read("MANIFEST.txt").decode("utf-8").splitlines()
        if manifest != PACKAGE_PATHS:
            raise RuntimeError("ZIP manifest mismatch")
        sums = archive.read("SHA256SUMS.txt").decode("utf-8").splitlines()
        for line in sums:
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(archive.read(rel)).hexdigest() != digest:
                raise RuntimeError(f"ZIP SHA mismatch: {rel}")
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--standalone-rebuild", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.build = args.verify = True
    result: dict[str, Any] = {}
    if args.build:
        result["build"] = build()
    if args.verify:
        result["guard"] = repository_guard(True)
        result["verify"] = verify_files()
    if args.standalone_rebuild:
        result["standalone_rebuild"] = standalone_rebuild()
    if args.zip:
        path, digest = make_zip()
        result["zip"] = {"path": str(path), "sha256": digest}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
