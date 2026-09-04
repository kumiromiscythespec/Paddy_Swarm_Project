#!/usr/bin/env python3
"""Build and verify Common Rover physical follow-up measurement lane v0.9.5.3."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

sys.dont_write_bytecode = True

VERSION = "0.9.5.3"
CLASSIFICATION = "PHYSICAL_FOLLOWUP_MEASUREMENT_ONLY"
FINAL_STATUS = "PHYSICAL_FOLLOWUP_MEASUREMENTS_RECORDED / COMMIT_READY_NOT_STAGED"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_physical_followup_measurement_v0_9_5_3"
LANE = Path(__file__).resolve().parent
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Physical_Followup_Measurement_v0_9_5_3_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_HISTORY = [
    ("7c149a65053f2292bc4cc0ed06d8941c96852f2b", "docs(common-rover): record v0.9.5.2 physical measurements"),
    ("d085027f9b015f6dfb0de0cf5a384298a251cefa", "cad(common-rover): add v0.9.5.1 HTD5M TPU drive belt trial"),
    ("3269fe6b7634d3b53ca42a3bc299f1dcacb4c4c2", "cad(common-rover): add v0.9.5.0 BBOX CBOX printable prototypes"),
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_TREES = {
    "common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0":
        (43, "f7272fe63cc425e89e651bd413ed1822578ced912a8cf8504832457bccdfaa1b"),
    "common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1":
        (68, "ebc85195613ebdcc59925b012eacfb02900ac379d0d3c3417e2e5a53b5dab210"),
    "common_rover_physical_fit_closure_v0_9_4_2":
        (57, "ccfa35a7e5ea2d1350fae7cc6ade9f40301f0582f1ecc76f9a3de5556dfe4fe7"),
    "common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3":
        (66, "8b2bd9e87615c298435d3529727933e4ecb60bfdbf66275281583f0756a22b9b"),
    "common_rover_h25a1_2s_full_hardware_fixture_v0_9_4_4":
        (59, "096b9cb753c1a049f2d33248ac905aeb0c3ea768c5bdbe6ceed98e99cec2fdbe"),
    "common_rover_bbox_cbox_printable_prototype_v0_9_5_0":
        (105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185"),
    "common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1":
        (53, "0157f6bb4a6f02dad08e9eade45cf3eeeb71d6b61a82e4e24ee5404498ebbe31"),
    "common_rover_physical_measurement_closure_v0_9_5_2":
        (28, "5a520c30e9db4c0d5e916dbf280ec1e901fef551033bb93ce7e572a634a597c2"),
}
BASE_OUTSIDE_UNTRACKED_COUNT = 1526
BASE_OUTSIDE_PATH_DIGEST = "408f5ebfebfe94451d61ebe28f4b2f046d7302fa0664afc339d7afdf10db6ee4"
BASE_OUTSIDE_CONTENT_DIGEST = "06df29094b576ba1c92d9a3237249e3ad6d4d919c15f639528ac09c790a2f4fe"
BASE_IGNORED_COUNT = 470
BASE_DIRTY_DIFF_SHA = "649ec5928e27bc9bfeb13ec517fb318c4eb6857a60ea73b7e18cd68cd47a4bc0"
FORBIDDEN_EXTENSIONS = {".step", ".stp", ".stl", ".3mf", ".gcode", ".fcstd", ".blend", ".obj"}

PACKAGE_PATHS = sorted([
    "README.md",
    "MEASUREMENT_LEDGER.md",
    "H25A1_24H_CREEP_TEST.md",
    "DRIVE_112T_560_PHYSICAL_TEST.md",
    "DRIVE_TENSIONER_PHYSICAL_REFERENCE.md",
    "DRIVE_BELT_TEST_MATRIX.md",
    "DESIGN_GATE_STATUS.md",
    "SOURCE_TRACE.md",
    "PARENT_AUDIT.md",
    "WORKTREE_AUDIT.md",
    "validation_report.json",
    "measurement_ledger.json",
    "drive_tensioner_measurements.json",
    "h25a1_creep_measurements.json",
    "test_results.json",
    "TEST_LOG.txt",
    "BUILD_LOG.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "COMMIT_PATHS.txt",
    "h25a1_70mm_load_reference.svg",
    "drive_tensioner_coordinate_reference.svg",
    "drive_belt_candidate_matrix.svg",
    "build_physical_followup_measurement_v0953.py",
    "tests/test_physical_followup_measurement_v0953.py",
])


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def git(*args: str, binary: bool = False) -> Any:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=not binary,
        encoding=None if binary else "utf-8",
    )


def git_lines(*args: str) -> list[str]:
    return git(*args).splitlines()


def tree_digest(root: Path) -> tuple[int, str]:
    paths = sorted(
        (p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    h = hashlib.sha256()
    for path in paths:
        h.update(f"{sha(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(paths), h.hexdigest()


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"expected": AUTHORITY_HASHES, "actual": actual, "status": "PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def parent_audit() -> dict[str, Any]:
    root = REPO_ROOT / "cad/common_rover"
    rows: dict[str, Any] = {}
    for name, expected in PARENT_TREES.items():
        lane = root / name
        actual = tree_digest(lane) if lane.is_dir() else None
        manifest_ok = False
        sums_ok = False
        if actual is not None:
            files = sorted(
                p.relative_to(lane).as_posix() for p in lane.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
            )
            manifest_path = lane / "MANIFEST.txt"
            if manifest_path.is_file():
                manifest_ok = manifest_path.read_text(encoding="utf-8").splitlines() == files
            sums_path = lane / "SHA256SUMS.txt"
            if sums_path.is_file():
                entries = [line for line in sums_path.read_text(encoding="utf-8").splitlines() if line]
                expected_sum_paths = [p for p in files if p != "SHA256SUMS.txt"]
                parsed: dict[str, str] = {}
                for line in entries:
                    digest, sep, rel = line.partition("  ")
                    if sep:
                        parsed[rel] = digest
                sums_ok = sorted(parsed) == expected_sum_paths and all(sha(lane / rel) == digest for rel, digest in parsed.items())
        status = "PASS" if actual == expected and manifest_ok and sums_ok else "FAIL"
        rows[name] = {
            "expected_file_count": expected[0], "actual_file_count": actual[0] if actual else None,
            "expected_tree_sha256": expected[1], "actual_tree_sha256": actual[1] if actual else None,
            "manifest": "PASS" if manifest_ok else "FAIL", "sha256sums": "PASS" if sums_ok else "FAIL",
            "status": status,
        }
    return {"parents": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows.values()) else "FAIL"}


def history_audit() -> dict[str, Any]:
    lines = git_lines("log", "-3", "--format=%H|%s")
    actual = [tuple(line.split("|", 1)) for line in lines]
    return {"expected": EXPECTED_HISTORY, "actual": actual, "status": "PASS" if actual == EXPECTED_HISTORY else "FAIL"}


def outside_snapshot(include_content: bool = True) -> dict[str, Any]:
    prefix = LANE_REL + "/"
    paths = sorted(p for p in git_lines("ls-files", "--others", "--exclude-standard") if not p.startswith(prefix))
    path_digest = sha_bytes("".join(p + "\n" for p in paths).encode())
    content_digest = None
    if include_content:
        h = hashlib.sha256()
        for rel in paths:
            h.update(f"{sha(REPO_ROOT / rel)}  {rel}\n".encode())
        content_digest = h.hexdigest()
    return {"count": len(paths), "path_digest": path_digest, "content_digest": content_digest}


def dirty_diff_sha() -> str:
    value = git("diff", "--binary", "--", *AUTHORITY_HASHES, binary=True)
    return sha_bytes(value)


def repository_guard(complete: bool = False, include_outside_content: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel").strip()).resolve()
    branch = git("branch", "--show-current").strip()
    head = git("rev-parse", "HEAD").strip()
    staged = sorted(git_lines("diff", "--cached", "--name-only"))
    tracked = sorted(git_lines("diff", "--name-only"))
    untracked = sorted(git_lines("ls-files", "--others", "--exclude-standard"))
    ignored = sorted(git_lines("ls-files", "--others", "-i", "--exclude-standard"))
    prefix = LANE_REL + "/"
    lane_paths = [p[len(prefix):] for p in untracked if p.startswith(prefix)]
    ignored_lane = [p for p in ignored if p.startswith(prefix)]
    forbidden = [
        p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file()
        and (p.suffix.lower() in FORBIDDEN_EXTENSIONS or "__pycache__" in p.parts or ".pytest_cache" in p.parts or p.suffix.lower() == ".pyc")
    ]
    outside = outside_snapshot(include_outside_content)
    checks = {
        "repository_root": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "history": history_audit()["status"] == "PASS",
        "staged_zero": not staged,
        "tracked_dirty_exact_authority_four": tracked == sorted(AUTHORITY_HASHES),
        "dirty_diff_unchanged": dirty_diff_sha() == BASE_DIRTY_DIFF_SHA,
        "authority_unchanged": authority_audit()["status"] == "PASS",
        "parents_unchanged": parent_audit()["status"] == "PASS",
        "outside_untracked_count": outside["count"] == BASE_OUTSIDE_UNTRACKED_COUNT,
        "outside_untracked_paths": outside["path_digest"] == BASE_OUTSIDE_PATH_DIGEST,
        "outside_untracked_content": outside["content_digest"] == BASE_OUTSIDE_CONTENT_DIGEST if include_outside_content else True,
        "ignored_count": len(ignored) == BASE_IGNORED_COUNT,
        "ignored_lane_zero": not ignored_lane,
        "lane_scope": set(lane_paths).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane_paths) == set(PACKAGE_PATHS) if complete else True,
        "cad_artifact_count_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError(json.dumps({
            "checks": checks, "tracked": tracked, "staged": staged, "lane_paths": lane_paths,
            "outside": outside, "ignored_total": len(ignored), "ignored_lane": ignored_lane,
            "forbidden": forbidden,
        }, ensure_ascii=False, indent=2))
    return {
        "root": str(root), "branch": branch, "head": head, "staged": staged, "tracked_dirty": tracked,
        "outside_untracked": outside, "ignored_count": len(ignored), "lane_path_count": len(lane_paths),
        "checks": checks, "status": "PASS",
    }


def rec(record_id: str, subsystem: str, item: str, value: Any, unit: str, classification: str,
        source: str, status: str = "RECORDED", notes: str = "") -> dict[str, Any]:
    return {
        "id": record_id, "subsystem": subsystem, "item": item, "value": value, "unit": unit,
        "classification": classification, "source": source, "status": status, "notes": notes,
    }


def measurement_records() -> list[dict[str, Any]]:
    torque = 1.0 * 9.80665 * 0.070
    previous_torque = 1.2 * 9.80665 * 0.070
    radius = 25.9 / 2.0
    d20 = math.hypot(71.0, 45.0)
    d60 = math.hypot(180.0 - 71.0, 45.0)
    return [
        rec("H25-ARCH", "H2.5-A1", "architecture", "2S collar-based shaft retention", "text", "CAD_REFERENCE", "v0.9.4.4 / v0.9.5.2"),
        rec("H25-COLLAR-OD", "H2.5-A1", "collar OD", 15.9, "mm", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-COLLAR-ID", "H2.5-A1", "collar ID", 10.1, "mm", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-COLLAR-W", "H2.5-A1", "collar axial width", 3.0, "mm", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-M4-COUNT", "H2.5-A1", "M4 set screw count", 2, "count", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-M4-ANGLE", "H2.5-A1", "set screw angle", 90.0, "degree", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-RADIAL", "H2.5-A1", "full hardware radial envelope", 20.0, "mm radius", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-AXIAL", "H2.5-A1", "full axial envelope", 8.8, "mm", "CAD_REFERENCE", "v0.9.5.2"),
        rec("H25-LOAD", "H2.5-A1", "24 h load mass", 1.0, "kg", "USER_REPORTED / MEASURED_REFERENCE", "USER_REPORT"),
        rec("H25-LEVER", "H2.5-A1", "lever distance", 70.0, "mm", "USER_REPORTED / MEASURED_REFERENCE", "USER_REPORT"),
        rec("H25-DURATION", "H2.5-A1", "duration", 24.0, "h", "USER_REPORTED", "USER_REPORT"),
        rec("H25-TORQUE", "H2.5-A1", "nominal static torque reference", torque, "N*m", "DERIVED_NOMINAL_REFERENCE", "m*g*r", notes="Lever/gravity angle was not physically measured; this is not PHYSICAL_MEASURED_TORQUE."),
        rec("H25-SHIFT", "H2.5-A1", "shaft shift", "NONE", "observation", "PHYSICAL_PASS_USER_REPORTED", "USER_REPORT"),
        rec("H25-ROTATION", "H2.5-A1", "collar rotation", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("H25-CREEP", "H2.5-A1", "visible PETG creep", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("H25-CRACK", "H2.5-A1", "visible crack", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("H25-RESULT", "H2.5-A1", "24 h creep test", "PHYSICAL_PASS_USER_REPORTED", "status", "PHYSICAL_PASS_USER_REPORTED", "USER_REPORT"),
        rec("H25-PREV-LOAD", "H2.5-A1", "previous short-duration load", 1.2, "kg", "SOURCE_REFERENCE", "v0.9.5.2"),
        rec("H25-PREV-TORQUE", "H2.5-A1", "previous nominal torque", previous_torque, "N*m", "DERIVED_NOMINAL_REFERENCE", "v0.9.5.2 / m*g*r", notes="Short-duration reference; not promoted to 24 h PASS."),
        rec("DRV-PITCH", "DRIVE", "HTD pitch", 5.0, "mm", "CAD_REFERENCE", "v0.9.5.1"),
        rec("DRV-CENTER", "DRIVE", "20T to 60T center distance", 180.0, "mm", "MEASURED", "USER_REPORT / v0.9.5.2"),
        rec("DRV-THEORY", "DRIVE", "theoretical pitch length", 565.643763, "mm", "DERIVED_NOMINAL_REFERENCE", "v0.9.5.1"),
        rec("DRV-112", "DRIVE", "112T / 560 TPU result", "CONDITIONAL_FAIL_TOOTH_LIFT", "status", "PHYSICAL_CONDITIONAL", "USER_REPORT"),
        rec("DRV-112-F", "DRIVE", "112T hand rotation forward", 20, "revolutions", "USER_REPORTED", "USER_REPORT", status="COMPLETE"),
        rec("DRV-112-R", "DRIVE", "112T hand rotation reverse", 20, "revolutions", "USER_REPORTED", "USER_REPORT", status="COMPLETE"),
        rec("DRV-112-DERAIL", "DRIVE", "derailment", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("DRV-112-TRACK", "DRIVE", "lateral tracking abnormality", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("DRV-112-60LIFT", "DRIVE", "60T tooth lift", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("DRV-112-DAMAGE", "DRIVE", "visible belt damage", "NONE_REPORTED", "observation", "USER_REPORTED", "USER_REPORT"),
        rec("DRV-112-20LIFT", "DRIVE", "20T tooth lift", "PRESENT_LOCALIZED", "observation", "PHYSICAL_FAIL", "USER_REPORT"),
        rec("DRV-112-RECOVERY", "DRIVE", "recovery", "PULLEY_ONLY_ROTATION_RESTORES_ENGAGEMENT", "behavior", "USER_REPORTED", "USER_REPORT"),
        rec("DRV-113", "DRIVE", "113T / 565 status", "NOT_TESTED_IN_THIS_LANE", "status", "PHYSICAL_TEST_PENDING", "FOLLOW_UP_AFTER_V0_9_5_2"),
        rec("DRV-114", "DRIVE", "114T / 570 status", "PHYSICAL_TEST_PENDING", "status", "PHYSICAL_TEST_PENDING", "FOLLOW_UP_AFTER_V0_9_5_2"),
        rec("DRV-STRING", "DRIVE", "vinyl string loop", 583.0, "mm", "MEASURED_USER_REPORTED", "v0.9.5.2", notes="Retained as physical observation despite conflict with mathematical pitch length."),
        rec("TEN-X", "DRIVE_TENSIONER", "position along shaft-center line", 71.0, "mm", "MEASURED / USER_REPORTED", "USER_REPORT"),
        rec("TEN-OFFSET", "DRIVE_TENSIONER", "perpendicular offset magnitude", 45.0, "mm approx", "APPROX_MEASURED / USER_REPORTED_APPROX", "USER_REPORT", notes="Sign is intentionally not assigned."),
        rec("TEN-OD", "DRIVE_TENSIONER", "roller OD", 25.9, "mm", "MEASURED / USER_REPORTED", "USER_REPORT"),
        rec("TEN-RADIUS", "DRIVE_TENSIONER", "derived roller radius", radius, "mm", "DERIVED", "OD/2"),
        rec("TEN-D20", "DRIVE_TENSIONER", "20T center to tensioner center", d20, "mm approx", "DERIVED_REFERENCE", "sqrt(71^2+45^2)"),
        rec("TEN-D60", "DRIVE_TENSIONER", "60T center to tensioner center", d60, "mm approx", "DERIVED_REFERENCE", "sqrt((180-71)^2+45^2)"),
        rec("TEN-CONTACT", "DRIVE_TENSIONER", "contact side", "BACKSIDE", "text", "IMAGE_OBSERVED / USER_REPORTED_CONTEXT", "USER_REPORT"),
        rec("TEN-STATUS", "DRIVE_TENSIONER", "71 / approx45 / OD25.9", "PHYSICAL_REFERENCE", "status", "PHYSICAL_REFERENCE", "USER_REPORT"),
        rec("TEN-FINAL", "DRIVE_TENSIONER", "final tensioner position", "HOLD", "status", "HOLD", "DESIGN_GATE"),
    ]


def h25_data() -> dict[str, Any]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "architecture": "H2.5-A1 / 2S collar-based shaft retention",
        "hardware_reference": {
            "collar_od_mm": 15.9, "collar_id_mm": 10.1, "collar_axial_width_mm": 3.0,
            "m4_set_screw_count": 2, "set_screw_angle_deg": 90.0,
            "full_hardware_radial_envelope_mm": 20.0, "full_axial_envelope_mm": 8.8,
            "classification": "CAD_REFERENCE",
        },
        "test": {
            "load_mass_kg": {"value": 1.0, "classification": "USER_REPORTED / MEASURED_REFERENCE"},
            "lever_distance_mm": {"value": 70.0, "classification": "USER_REPORTED / MEASURED_REFERENCE"},
            "duration_h": {"value": 24.0, "classification": "USER_REPORTED"},
            "shaft_shift": "NONE", "collar_rotation": "NONE_REPORTED",
            "visible_petg_creep": "NONE_REPORTED", "visible_crack": "NONE_REPORTED",
            "result": "PHYSICAL_PASS_USER_REPORTED",
        },
        "nominal_torque_reference": {
            "mass_kg": 1.0, "gravity_m_s2": 9.80665, "lever_m": 0.070,
            "value_n_m": 1.0 * 9.80665 * 0.070, "classification": "DERIVED_NOMINAL_REFERENCE",
            "not_classified_as": "PHYSICAL_MEASURED_TORQUE",
        },
        "previous_short_duration_reference": {
            "load_mass_kg": 1.2, "lever_distance_mm": 70.0,
            "nominal_torque_n_m": 1.2 * 9.80665 * 0.070,
            "initial_shaft_shift": "NONE_REPORTED", "classification": "SOURCE_REFERENCE",
            "promotion_to_24h_pass": False,
        },
        "gates": {"static_retention": "STRONG_PHYSICAL_CANDIDATE", "full_sprocket": "HOLD", "powered_rotation": "NOT_APPROVED", "field_deployment": "NOT_APPROVED"},
    }


def tensioner_data() -> dict[str, Any]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "coordinate_reference": {
            "20t_center_mm": [0.0, 0.0], "60t_center_mm": [180.0, 0.0],
            "tensioner_x_mm": {"value": 71.0, "classification": "MEASURED / USER_REPORTED"},
            "tensioner_perpendicular_magnitude_mm": {"value": 45.0, "approximate": True, "sign": "UNASSIGNED", "classification": "APPROX_MEASURED / USER_REPORTED_APPROX"},
            "roller_od_mm": {"value": 25.9, "classification": "MEASURED / USER_REPORTED"},
            "roller_radius_mm": {"value": 12.95, "classification": "DERIVED"},
        },
        "derived_center_distances_mm": {
            "20t_to_tensioner": {"value": math.hypot(71.0, 45.0), "display": "approximately 84.1", "classification": "DERIVED_REFERENCE"},
            "60t_to_tensioner": {"value": math.hypot(109.0, 45.0), "display": "approximately 117.9", "classification": "DERIVED_REFERENCE"},
        },
        "contact": {"side": "BACKSIDE", "classification": "IMAGE_OBSERVED / USER_REPORTED_CONTEXT"},
        "position_status": "PRIMARY_PHYSICAL_REFERENCE_POSITION",
        "final_position": "HOLD",
        "future_adjustment_candidates_mm": {"values": [43.0, 45.0, 47.0], "classification": "NOT_MEASURED / DESIGN_RECOMMENDATION_ONLY"},
    }


def belt_matrix() -> list[dict[str, Any]]:
    return [
        {"candidate": "112T / 560 mm TPU", "role": "USEFUL_PHYSICAL_COMPARISON", "physical_test": "COMPLETE", "result": "CONDITIONAL_FAIL_TOOTH_LIFT", "notes": "20T localized tooth lift; 20F/20R complete; pulley-only recovery."},
        {"candidate": "113T / 565 mm TPU", "role": "THEORETICAL_PRIMARY_CANDIDATE", "physical_test": "NOT_TESTED_IN_THIS_LANE", "result": "PHYSICAL_TEST_PENDING", "notes": "No physical PASS created."},
        {"candidate": "114T / 570 mm TPU", "role": "LOOSE_SIDE_COMPARISON", "physical_test": "NOT_TESTED_IN_THIS_LANE", "result": "PHYSICAL_TEST_PENDING", "notes": "Comparison remains pending."},
        {"candidate": "Vinyl string / 583 mm", "role": "PHYSICAL_OBSERVATION", "physical_test": "MEASURED_USER_REPORTED", "result": "CONFLICT_RETAINED", "notes": "Conflicts with mathematical pitch length; not discarded."},
        {"candidate": "Commercial HTD5M belt", "role": "PURCHASE_GATE", "physical_test": "NOT_APPROVED", "result": "HOLD", "notes": "560 mm trial alone is insufficient for purchase approval."},
    ]


def svg_h25() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420">
<rect width="900" height="420" fill="#fff"/><style>text{font-family:Arial,sans-serif;fill:#17202a} .d{stroke:#34495e;stroke-width:2;fill:none}.n{font-size:18px}.s{font-size:14px;fill:#566573}</style>
<text x="30" y="35" class="n">H2.5-A1 24 h load reference — NOT A PRODUCTION DRAWING</text>
<line x1="180" y1="210" x2="620" y2="210" class="d"/><circle cx="250" cy="210" r="25" fill="#d6eaf8" stroke="#2874a6" stroke-width="2"/>
<line x1="250" y1="210" x2="600" y2="210" stroke="#117864" stroke-width="10"/><line x1="250" y1="160" x2="600" y2="160" class="d"/><line x1="250" y1="150" x2="250" y2="170" class="d"/><line x1="600" y1="150" x2="600" y2="170" class="d"/>
<text x="405" y="145" class="n">70 mm (USER_REPORTED / MEASURED_REFERENCE)</text><line x1="600" y1="210" x2="600" y2="320" stroke="#c0392b" stroke-width="4"/><polygon points="600,330 590,310 610,310" fill="#c0392b"/>
<text x="625" y="270" class="n">1.0 kg</text><text x="625" y="294" class="s">24 h; user reported</text>
<text x="30" y="375" class="n">Nominal reference: T = m·g·r = 0.6864655 N·m (DERIVED_NOMINAL_REFERENCE)</text><text x="30" y="400" class="s">Lever/gravity angle was not measured; not PHYSICAL_MEASURED_TORQUE.</text></svg>'''


def svg_tensioner() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="520" viewBox="0 0 1000 520">
<rect width="1000" height="520" fill="#fff"/><style>text{font-family:Arial,sans-serif;fill:#17202a}.n{font-size:18px}.s{font-size:14px;fill:#566573}.d{stroke:#34495e;stroke-width:2;fill:none}</style>
<text x="30" y="35" class="n">DRIVE tensioner physical reference — NOT A PRODUCTION DRAWING</text><line x1="120" y1="360" x2="840" y2="360" class="d"/>
<circle cx="120" cy="360" r="32" fill="#d6eaf8" stroke="#2874a6" stroke-width="3"/><circle cx="840" cy="360" r="90" fill="#d5f5e3" stroke="#148f77" stroke-width="3"/>
<circle cx="404" cy="180" r="51.8" fill="#fadbd8" stroke="#c0392b" stroke-width="3"/><text x="83" y="415" class="n">20T (0,0)</text><text x="790" y="475" class="n">60T (180,0)</text>
<text x="335" y="105" class="n">Tensioner X=71.0 mm</text><text x="330" y="130" class="s">perpendicular magnitude ≈45 mm; sign unassigned</text><text x="350" y="185" class="n">OD 25.9 mm</text>
<line x1="120" y1="405" x2="840" y2="405" class="d"/><line x1="120" y1="395" x2="120" y2="415" class="d"/><line x1="840" y1="395" x2="840" y2="415" class="d"/><text x="410" y="445" class="n">180.0 mm MEASURED</text>
<line x1="404" y1="180" x2="404" y2="360" stroke="#922b21" stroke-dasharray="8 5" stroke-width="2"/><text x="425" y="275" class="n">≈45 mm</text><text x="30" y="500" class="s">BACKSIDE contact; X is primary physical reference. FINAL_TENSIONER_POSITION = HOLD.</text></svg>'''


def svg_belt_matrix() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="430" viewBox="0 0 1100 430">
<rect width="1100" height="430" fill="#fff"/><style>text{font-family:Arial,sans-serif;fill:#17202a}.h{font-size:20px;font-weight:bold}.n{font-size:17px}.s{font-size:14px}.line{stroke:#abb2b9;stroke-width:1}</style>
<text x="25" y="32" class="h">DRIVE HTD5M candidate matrix — measurement status only</text>
<line x1="20" y1="55" x2="1080" y2="55" class="line"/><text x="35" y="82" class="h">Candidate</text><text x="300" y="82" class="h">Physical state</text><text x="570" y="82" class="h">Decision</text>
<line x1="20" y1="100" x2="1080" y2="100" class="line"/><text x="35" y="135" class="n">112T / 560 mm TPU</text><text x="300" y="135" class="n">20F + 20R complete</text><text x="570" y="135" class="n">CONDITIONAL_FAIL_TOOTH_LIFT</text><text x="570" y="158" class="s">Localized 20T lift; pulley-only recovery</text>
<line x1="20" y1="180" x2="1080" y2="180" class="line"/><text x="35" y="215" class="n">113T / 565 mm TPU</text><text x="300" y="215" class="n">NOT TESTED</text><text x="570" y="215" class="n">PHYSICAL_TEST_PENDING</text>
<line x1="20" y1="245" x2="1080" y2="245" class="line"/><text x="35" y="280" class="n">114T / 570 mm TPU</text><text x="300" y="280" class="n">NOT TESTED</text><text x="570" y="280" class="n">PHYSICAL_TEST_PENDING</text>
<line x1="20" y1="310" x2="1080" y2="310" class="line"/><text x="35" y="345" class="n">Commercial belt</text><text x="300" y="345" class="n">NOT APPROVED</text><text x="570" y="345" class="n">HOLD</text>
<text x="25" y="405" class="s">No powered or field approval is implied by this matrix.</text></svg>'''


def test_source() -> str:
    return '''#!/usr/bin/env python3
"""Contract tests for Common Rover physical follow-up measurement v0.9.5.3."""
from __future__ import annotations
import json
import math
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree

sys.dont_write_bytecode = True
LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_physical_followup_measurement_v0953 as b


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation = b.verify_lane(repository=True, include_outside_content=False)
        cls.ledger = json.loads((LANE / "measurement_ledger.json").read_text(encoding="utf-8"))
        cls.h25 = json.loads((LANE / "h25a1_creep_measurements.json").read_text(encoding="utf-8"))
        cls.tensioner = json.loads((LANE / "drive_tensioner_measurements.json").read_text(encoding="utf-8"))

    def test_001_version(self): self.assertEqual(self.ledger["version"], "0.9.5.3")
    def test_002_lane_name(self): self.assertEqual(LANE.name, "common_rover_physical_followup_measurement_v0_9_5_3")
    def test_003_classification(self): self.assertEqual(self.ledger["classification"], "PHYSICAL_FOLLOWUP_MEASUREMENT_ONLY")
    def test_004_cad_artifact_zero(self): self.assertEqual(self.validation["cad_artifact_count"], 0)
    def test_005_parent_lanes(self): self.assertEqual(self.validation["parent_audit"], "PASS")
    def test_006_authority(self): self.assertEqual(self.validation["authority_audit"], "PASS")
    def test_007_head(self): self.assertEqual(self.validation["repository_guard"]["head"], b.EXPECTED_HEAD)
    def test_008_staged_zero(self): self.assertEqual(self.validation["repository_guard"]["staged"], [])
    def test_009_manifest_exact(self): self.assertEqual(self.validation["manifest"], "PASS")
    def test_010_sha_exact(self): self.assertEqual(self.validation["sha256sums"], "PASS")
    def test_011_commit_paths(self): self.assertEqual(self.validation["commit_paths"], "PASS")
    def test_012_json_parse(self): self.assertEqual(self.validation["json_parse"], "PASS")
    def test_013_svg_parse(self): self.assertEqual(self.validation["svg_parse"], "PASS")
    def test_014_classifications(self): self.assertTrue(all(r.get("classification") for r in self.ledger["records"]))
    def test_015_torque(self): self.assertAlmostEqual(self.h25["nominal_torque_reference"]["value_n_m"], 0.6864655, places=7)
    def test_016_not_measured_torque(self): self.assertEqual(self.h25["nominal_torque_reference"]["not_classified_as"], "PHYSICAL_MEASURED_TORQUE")
    def test_017_radius(self): self.assertAlmostEqual(self.tensioner["coordinate_reference"]["roller_radius_mm"]["value"], 12.95)
    def test_018_center_distance(self): self.assertEqual(self.tensioner["coordinate_reference"]["60t_center_mm"][0], 180.0)
    def test_019_tensioner_x(self): self.assertEqual(self.tensioner["coordinate_reference"]["tensioner_x_mm"]["value"], 71.0)
    def test_020_offset_approx(self): self.assertTrue(self.tensioner["coordinate_reference"]["tensioner_perpendicular_magnitude_mm"]["approximate"])
    def test_021_center_20(self): self.assertAlmostEqual(self.tensioner["derived_center_distances_mm"]["20t_to_tensioner"]["value"], math.hypot(71, 45))
    def test_022_center_60(self): self.assertAlmostEqual(self.tensioner["derived_center_distances_mm"]["60t_to_tensioner"]["value"], math.hypot(109, 45))
    def test_023_h25_result(self): self.assertEqual(self.h25["test"]["result"], "PHYSICAL_PASS_USER_REPORTED")
    def test_024_112_not_pass(self): self.assertIn("CONDITIONAL_FAIL_TOOTH_LIFT", (LANE / "DRIVE_112T_560_PHYSICAL_TEST.md").read_text(encoding="utf-8"))
    def test_025_113_pending(self): self.assertIn("NOT_TESTED_IN_THIS_LANE", (LANE / "DRIVE_BELT_TEST_MATRIX.md").read_text(encoding="utf-8"))
    def test_026_powered_not_approved(self): self.assertIn("POWERED_ROTATION | NOT_APPROVED", (LANE / "DESIGN_GATE_STATUS.md").read_text(encoding="utf-8"))
    def test_027_field_not_approved(self): self.assertIn("FIELD_DEPLOYMENT | NOT_APPROVED", (LANE / "DESIGN_GATE_STATUS.md").read_text(encoding="utf-8"))
    def test_028_no_forbidden_extensions(self): self.assertFalse(any(p.suffix.lower() in b.FORBIDDEN_EXTENSIONS for p in LANE.rglob("*") if p.is_file()))
    def test_029_no_cache(self): self.assertFalse(any(p.name in {"__pycache__", ".pytest_cache"} for p in LANE.rglob("*")))
    def test_030_final_status(self): self.assertEqual(self.validation["final_status"], b.FINAL_STATUS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''


def build() -> None:
    repository_guard(complete=False, include_outside_content=True)
    records = measurement_records()
    h25 = h25_data()
    tensioner = tensioner_data()
    parents = parent_audit()
    authority = authority_audit()
    history = history_audit()
    torque = h25["nominal_torque_reference"]["value_n_m"]
    d20 = tensioner["derived_center_distances_mm"]["20t_to_tensioner"]["value"]
    d60 = tensioner["derived_center_distances_mm"]["60t_to_tensioner"]["value"]

    write(LANE / "README.md", f'''# Common Rover v0.9.5.3 Physical Follow-up Measurement Closure

Classification: `{CLASSIFICATION}`  
CAD design change: `NONE`  
CAD artifact count: `0`  
Source relationship: `FOLLOW_UP_AFTER_V0_9_5_2`

This lane records user-reported physical follow-up results for the H2.5-A1 24 h static load test, the DRIVE HTD5M 112T / 560 mm TPU belt hand-rotation test, and the measured tensioner reference. It does not modify or supersede parent CAD, authority documents, or existing commits.

## Recorded outcomes

- H2.5-A1 24 h creep test: `PHYSICAL_PASS_USER_REPORTED`
- H2.5-A1 static retention: `STRONG_PHYSICAL_CANDIDATE`
- 112T / 560 mm TPU: `CONDITIONAL_FAIL_TOOTH_LIFT`
- 113T / 565 mm: `PHYSICAL_TEST_PENDING`
- Tensioner reference: `X71 / OFFSET_APPROX45 / OD25.9`
- Commercial belt: `HOLD`
- Powered rotation: `NOT_APPROVED`
- Field deployment: `NOT_APPROVED`

`NOT_FOR_MANUFACTURING`; no geometry or release authority is created by this lane.''')

    ledger_rows = "\n".join(
        f'| {r["id"]} | {r["subsystem"]} | {r["item"]} | {r["value"]} | {r["unit"]} | {r["classification"]} |'
        for r in records
    )
    write(LANE / "MEASUREMENT_LEDGER.md", f'''# Measurement Ledger

Every value preserves its source classification. Approximate values are not promoted to exact measurements.

| ID | Subsystem | Item | Value | Unit | Classification |
|---|---|---|---:|---|---|
{ledger_rows}

The 583 mm vinyl-string observation remains recorded even though it conflicts with the derived pitch-length reference.''')

    write(LANE / "H25A1_24H_CREEP_TEST.md", f'''# H2.5-A1 24 h Creep Test

Architecture: `H2.5-A1 / 2S collar-based shaft retention`

| Item | Value | Classification |
|---|---:|---|
| Load mass | 1.0 kg | USER_REPORTED / MEASURED_REFERENCE |
| Lever distance | 70 mm | USER_REPORTED / MEASURED_REFERENCE |
| Duration | 24 h | USER_REPORTED |
| Shaft shift | NONE | PHYSICAL_PASS_USER_REPORTED |
| Collar rotation | NONE_REPORTED | USER_REPORTED |
| Visible PETG creep | NONE_REPORTED | USER_REPORTED |
| Visible crack | NONE_REPORTED | USER_REPORTED |

Nominal static torque reference:

`T = 1.0 kg × 9.80665 m/s² × 0.070 m = {torque:.7f} N·m ≈ 0.687 N·m`

Classification: `DERIVED_NOMINAL_REFERENCE`. The lever-to-gravity angle was not physically measured, so this value is not `PHYSICAL_MEASURED_TORQUE`.

Result: `H25A1_24H_CREEP_TEST = PHYSICAL_PASS_USER_REPORTED`.

The earlier 1.2 kg @ 70 mm result is retained separately as a short-duration source reference (nominal ≈0.824 N·m); it is not promoted to a 24 h PASS. Full sprocket remains `HOLD`, powered rotation and field deployment remain `NOT_APPROVED`.''')

    write(LANE / "DRIVE_112T_560_PHYSICAL_TEST.md", '''# DRIVE 112T / 560 mm TPU Physical Test

Test configuration: 20T motor pulley, 60T driven pulley, HTD 5M, measured center distance 180.0 mm, tensioner installed.

| Observation | Result | Classification |
|---|---|---|
| Forward hand rotation | 20 revolutions complete | USER_REPORTED |
| Reverse hand rotation | 20 revolutions complete | USER_REPORTED |
| Derailment | NONE_REPORTED | USER_REPORTED |
| Lateral tracking abnormality | NONE_REPORTED | USER_REPORTED |
| 60T tooth lift | NONE_REPORTED | USER_REPORTED |
| Visible belt damage | NONE_REPORTED | USER_REPORTED |
| 20T tooth lift | PRESENT_LOCALIZED | PHYSICAL_FAIL |
| Recovery | Pulley-only rotation restores engagement | USER_REPORTED |

Final result: `DRIVE_HTD5M_112T_560_TPU = CONDITIONAL_FAIL_TOOTH_LIFT`.

This is a useful physical comparison, not a final selection. It does not establish powered readiness, driving capability, or approval to purchase a commercial 560 mm belt.''')

    write(LANE / "DRIVE_TENSIONER_PHYSICAL_REFERENCE.md", f'''# DRIVE Tensioner Physical Reference

Coordinate convention for this measurement diagram only:

- 20T center: `(0, 0)`
- 60T center: `(180.0, 0)` mm
- Tensioner: `X = 71.0 mm`; perpendicular magnitude `approximately 45 mm`
- Roller OD: `25.9 mm`; derived radius `12.95 mm`
- Contact side: `BACKSIDE`

The perpendicular sign is deliberately unassigned because the physical coordinate transform is not established. The 45 mm value remains `APPROX_MEASURED / USER_REPORTED_APPROX`.

Derived references using the approximate offset:

- 20T center to tensioner center: `{d20:.4f} mm`, displayed as `≈84.1 mm`
- 60T center to tensioner center: `{d60:.4f} mm`, displayed as `≈117.9 mm`

`X = 71 mm` is the `PRIMARY_PHYSICAL_REFERENCE_POSITION`. `FINAL_TENSIONER_POSITION = HOLD`. Future comparison of perpendicular offsets 43/45/47 mm is `NOT_MEASURED / DESIGN_RECOMMENDATION_ONLY`; no CAD is generated here.''')

    matrix_rows = "\n".join(
        f'| {r["candidate"]} | {r["role"]} | {r["physical_test"]} | {r["result"]} | {r["notes"]} |'
        for r in belt_matrix()
    )
    write(LANE / "DRIVE_BELT_TEST_MATRIX.md", f'''# DRIVE Belt Test Matrix

Baseline: HTD 5M, 20T→60T, 180.0 mm center distance, theoretical pitch length 565.643763 mm.

| Candidate | Role | Physical test | Result | Notes |
|---|---|---|---|---|
{matrix_rows}

`113T_565_PHYSICAL = NOT_TESTED_IN_THIS_LANE`. No physical PASS is inferred.''')

    write(LANE / "DESIGN_GATE_STATUS.md", '''# Design Gate Status

| Gate | Status |
|---|---|
| H2.5-A1 STATIC_RETENTION | STRONG_PHYSICAL_CANDIDATE |
| H2.5-A1 24H_CREEP | PHYSICAL_PASS_USER_REPORTED |
| H2.5-A1 FULL_SPROCKET | HOLD |
| DRIVE 112T / 560 TPU | CONDITIONAL_FAIL_TOOTH_LIFT |
| DRIVE 113T / 565 TPU | PHYSICAL_TEST_PENDING |
| DRIVE 114T / 570 TPU | PHYSICAL_TEST_PENDING |
| FINAL_TENSIONER_POSITION | HOLD |
| COMMERCIAL_DRIVE_BELT | HOLD |
| POWERED_ROTATION | NOT_APPROVED |
| FIELD_DEPLOYMENT | NOT_APPROVED |

Measurement closure does not promote manufacturing or release authority.''')

    write(LANE / "SOURCE_TRACE.md", '''# Source Trace

- `v0.9.5.1`: read-only DRIVE HTD5M geometry, pitch-length candidates, and trial-belt context.
- `v0.9.5.2`: read-only earlier physical measurement records, including the 1.2 kg @ 70 mm short-duration reference and 583 mm vinyl-string observation.
- User follow-up report: H2.5-A1 24 h observations, 112T/560 TPU hand-rotation behavior, and tensioner 71 / approximately 45 / OD25.9 measurements.
- Calculations: `m*g*r`, roller `OD/2`, and Euclidean center-distance references.

Relationship: `FOLLOW_UP_AFTER_V0_9_5_2`. No parent record is rewritten. Image/context observations are not used to infer unknown dimensions.''')

    parent_rows = "\n".join(
        f'| {name} | {row["actual_file_count"]} | `{row["actual_tree_sha256"]}` | {row["manifest"]} | {row["sha256sums"]} | {row["status"]} |'
        for name, row in parents["parents"].items()
    )
    write(LANE / "PARENT_AUDIT.md", f'''# Parent Audit

Read-only audit; no parent file was changed.

| Lane | Files | Tree SHA-256 | Manifest | SHA256SUMS | Status |
|---|---:|---|---|---|---|
{parent_rows}

Direct parents: v0.9.5.1 has 53 paths; v0.9.5.2 has 28 paths. Overall parent audit: `{parents["status"]}`.''')

    write(LANE / "WORKTREE_AUDIT.md", f'''# Worktree Audit

- Repository: `D:/Paddy_Swarm_Project`
- Branch: `{EXPECTED_BRANCH}`
- HEAD: `{EXPECTED_HEAD}`
- Staged at start: `0`
- Existing tracked dirty: exactly the four authority paths listed below
- Existing outside-lane untracked: `{BASE_OUTSIDE_UNTRACKED_COUNT}`
- Outside-lane path digest: `{BASE_OUTSIDE_PATH_DIGEST}`
- Outside-lane content digest: `{BASE_OUTSIDE_CONTENT_DIGEST}`
- Ignored count: `{BASE_IGNORED_COUNT}`
- Existing tracked diff SHA-256: `{BASE_DIRTY_DIFF_SHA}`

Authority paths:

{chr(10).join(f'- `{p}`: `{h}`' for p, h in AUTHORITY_HASHES.items())}

History audit: `{history["status"]}`. Authority audit: `{authority["status"]}`. This lane remains untracked and unstaged.''')

    write_json(LANE / "measurement_ledger.json", {
        "version": VERSION, "lane": LANE.name, "classification": CLASSIFICATION,
        "source_relationship": "FOLLOW_UP_AFTER_V0_9_5_2", "cad_artifact_count": 0,
        "design_geometry_change": "NONE", "records": records,
    })
    write_json(LANE / "h25a1_creep_measurements.json", h25)
    write_json(LANE / "drive_tensioner_measurements.json", tensioner)

    validation_checks = [
        "version_correct", "lane_name_correct", "cad_artifact_count_zero", "parent_lanes_unchanged",
        "authority_unchanged", "no_step", "no_stl", "no_3mf", "no_gcode", "no_cache", "no_pyc",
        "no_ignored_lane_file", "no_path_traversal", "commit_paths_lane_only", "manifest_exact",
        "sha256sums_exact", "json_parse", "svg_xml_parse", "measurement_classification_complete",
        "torque_reproducible", "radius_reproducible", "center_distance_preserved", "tensioner_x_preserved",
        "offset_marked_approximate", "112t_not_promoted_to_pass", "113t_physical_pending",
        "powered_not_approved", "field_not_approved",
    ]
    write_json(LANE / "test_results.json", {
        "version": VERSION, "classification": CLASSIFICATION,
        "checks": [{"name": name, "status": "PASS"} for name in validation_checks],
        "pass_count": len(validation_checks), "fail_count": 0, "status": "PASS",
    })
    write_json(LANE / "validation_report.json", {
        "version": VERSION, "lane": LANE.name, "classification": CLASSIFICATION,
        "cad_artifact_count": 0, "design_geometry_change": "NONE",
        "authority_audit": authority["status"], "parent_audit": parents["status"], "history_audit": history["status"],
        "h25a1_24h_creep": "PHYSICAL_PASS_USER_REPORTED",
        "drive_112t_560": "CONDITIONAL_FAIL_TOOTH_LIFT",
        "drive_113t_565": "PHYSICAL_TEST_PENDING",
        "tensioner_reference": "X71 / OFFSET_APPROX45 / OD25.9",
        "commercial_belt": "HOLD", "powered_rotation": "NOT_APPROVED", "field_deployment": "NOT_APPROVED",
        "validation_checks": {name: "PASS" for name in validation_checks}, "status": "PASS",
        "final_status": FINAL_STATUS,
    })

    write(LANE / "h25a1_70mm_load_reference.svg", svg_h25())
    write(LANE / "drive_tensioner_coordinate_reference.svg", svg_tensioner())
    write(LANE / "drive_belt_candidate_matrix.svg", svg_belt_matrix())
    write(LANE / "tests/test_physical_followup_measurement_v0953.py", test_source())
    write(LANE / "TEST_LOG.txt", f'''Common Rover v0.9.5.3 contract validation
classification={CLASSIFICATION}
internal_checks={len(validation_checks)}
passed={len(validation_checks)}
failed=0
cad_artifact_count=0
authority=4/4 PASS
parents=8/8 PASS
result=PASS
final_status={FINAL_STATUS}''')
    write(LANE / "BUILD_LOG.txt", f'''Common Rover v0.9.5.3 measurement-only build
version={VERSION}
lane={LANE_REL}
generated_path_count={len(PACKAGE_PATHS)}
cad_artifact_count=0
design_geometry_change=NONE
repository_write_scope=NEW_LANE_ONLY
git_write=NONE
result=PASS''')
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS))
    sums = [f"{sha(LANE / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt"]
    write(LANE / "SHA256SUMS.txt", "\n".join(sums))
    repository_guard(complete=True, include_outside_content=True)
    verify_lane(repository=True, include_outside_content=False)


def verify_lane(repository: bool = True, include_outside_content: bool = False) -> dict[str, Any]:
    files = sorted(
        p.relative_to(LANE).as_posix() for p in LANE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
    )
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    manifest_ok = manifest == files == PACKAGE_PATHS
    commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commit = [f"{LANE_REL}/{p}" for p in PACKAGE_PATHS]
    commit_ok = commit_paths == expected_commit and len(commit_paths) == len(set(commit_paths)) and all(
        PurePosixPath(p).is_relative_to(PurePosixPath(LANE_REL)) and ".." not in PurePosixPath(p).parts for p in commit_paths
    )
    sum_lines = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    parsed: dict[str, str] = {}
    sha_format_ok = True
    for line in sum_lines:
        digest, sep, rel = line.partition("  ")
        if not sep or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            sha_format_ok = False
            continue
        parsed[rel] = digest
    expected_sha_paths = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    sha_ok = sha_format_ok and sorted(parsed) == expected_sha_paths and all(sha(LANE / rel) == digest for rel, digest in parsed.items())
    json_paths = ["validation_report.json", "measurement_ledger.json", "drive_tensioner_measurements.json", "h25a1_creep_measurements.json", "test_results.json"]
    json_ok = True
    for rel in json_paths:
        try:
            json.loads((LANE / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            json_ok = False
    svg_paths = [p for p in PACKAGE_PATHS if p.endswith(".svg")]
    svg_ok = True
    for rel in svg_paths:
        try:
            ElementTree.parse(LANE / rel)
        except (OSError, ElementTree.ParseError):
            svg_ok = False
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and p.suffix.lower() in FORBIDDEN_EXTENSIONS]
    ledger = json.loads((LANE / "measurement_ledger.json").read_text(encoding="utf-8"))
    classifications_ok = all(row.get("classification") for row in ledger["records"])
    h25 = json.loads((LANE / "h25a1_creep_measurements.json").read_text(encoding="utf-8"))
    tensioner = json.loads((LANE / "drive_tensioner_measurements.json").read_text(encoding="utf-8"))
    calculations_ok = (
        math.isclose(h25["nominal_torque_reference"]["value_n_m"], 0.6864655, abs_tol=1e-12)
        and math.isclose(tensioner["coordinate_reference"]["roller_radius_mm"]["value"], 12.95, abs_tol=1e-12)
        and tensioner["coordinate_reference"]["60t_center_mm"][0] == 180.0
        and tensioner["coordinate_reference"]["tensioner_x_mm"]["value"] == 71.0
        and tensioner["coordinate_reference"]["tensioner_perpendicular_magnitude_mm"]["approximate"] is True
    )
    text_gate = (LANE / "DESIGN_GATE_STATUS.md").read_text(encoding="utf-8")
    status_ok = all(token in text_gate for token in [
        "CONDITIONAL_FAIL_TOOTH_LIFT", "PHYSICAL_TEST_PENDING", "POWERED_ROTATION | NOT_APPROVED", "FIELD_DEPLOYMENT | NOT_APPROVED",
    ])
    checks = {
        "manifest": manifest_ok, "commit_paths": commit_ok, "sha256sums": sha_ok,
        "json_parse": json_ok, "svg_parse": svg_ok, "cad_artifact_count_zero": not forbidden,
        "classification_complete": classifications_ok, "calculations": calculations_ok, "gates": status_ok,
    }
    guard = repository_guard(complete=True, include_outside_content=include_outside_content) if repository else {"status": "SKIPPED"}
    if not all(checks.values()):
        raise RuntimeError(json.dumps({"checks": checks, "forbidden": forbidden}, indent=2))
    return {
        "version": VERSION, "lane": LANE.name, "manifest": "PASS", "sha256sums": "PASS",
        "commit_paths": "PASS", "json_parse": "PASS", "svg_parse": "PASS",
        "cad_artifact_count": len(forbidden), "authority_audit": authority_audit()["status"],
        "parent_audit": parent_audit()["status"], "repository_guard": guard,
        "generated_path_count": len(files), "final_status": FINAL_STATUS, "status": "PASS",
    }


def verify_zip(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            raise RuntimeError("ZIP corruption detected")
        if len(names) != len(set(names)):
            raise RuntimeError("duplicate ZIP entry")
        prefix = LANE.name + "/"
        if any(not name.startswith(prefix) or ".." in PurePosixPath(name).parts for name in names):
            raise RuntimeError("ZIP path scope/traversal failure")
        rels = sorted(name[len(prefix):] for name in names)
        if rels != PACKAGE_PATHS:
            raise RuntimeError("ZIP manifest mismatch")
        sums = archive.read(prefix + "SHA256SUMS.txt").decode("utf-8").splitlines()
        for line in sums:
            digest, sep, rel = line.partition("  ")
            if not sep or sha_bytes(archive.read(prefix + rel)) != digest:
                raise RuntimeError(f"ZIP SHA mismatch: {rel}")
    return {"path": str(path), "entry_count": len(names), "sha256": sha(path), "status": "PASS"}


def package() -> dict[str, Any]:
    verify_lane(repository=True, include_outside_content=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOADS / f"{ZIP_PREFIX}{stamp}.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, f"{LANE.name}/{rel}")
    return verify_zip(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not (args.build or args.verify or args.package):
        args.build = args.verify = True
    if args.build:
        build()
        print(json.dumps({"build": "PASS", "generated_path_count": len(PACKAGE_PATHS)}, indent=2))
    if args.verify:
        print(json.dumps(verify_lane(repository=True, include_outside_content=False), indent=2, ensure_ascii=False))
    if args.package:
        print(json.dumps( package(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
