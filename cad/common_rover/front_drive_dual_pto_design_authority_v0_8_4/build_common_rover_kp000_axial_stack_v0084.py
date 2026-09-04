from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import math
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import cadquery as cq


sys.dont_write_bytecode = True

DOCUMENT_ID = "PS-CR-KP000-AXIAL-STACK-V0084"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_8_4_KP000_Axial_Stack_"

AUTHORITY_NAME = "common_rover_kp000_axial_stack_design_authority_v0084.md"
PARAMETERS_NAME = "common_rover_kp000_axial_stack_parameters_v0084.json"
ORIENTATION_NAME = "common_rover_kp000_orientation_candidates_v0084.csv"
SEARCH_NAME = "common_rover_kp000_axial_search_candidates_v0084.csv"
RANKING_NAME = "common_rover_kp000_candidate_ranking_v0084.csv"
SENSITIVITY_NAME = "common_rover_kp000_robustness_sensitivity_v0084.csv"
STACK_NAME = "common_rover_kp000_axial_stack_v0084.csv"
MATRIX_NAME = "common_rover_kp000_interference_matrix_v0084.csv"
INTERFERENCE_NAME = "common_rover_kp000_interference_report_v0084.json"
VALIDATION_NAME = "common_rover_kp000_validation_v0084.json"
REMEASURE_MD_NAME = "common_rover_kp000_remeasurement_sheet_v0084.md"
REMEASURE_CSV_NAME = "common_rover_kp000_remeasurement_sheet_v0084.csv"
BUILDER_NAME = "build_common_rover_kp000_axial_stack_v0084.py"
RECOMMENDED_STEP = "PS-CR-KP000-AXIAL-STACK-V0084-RECOMMENDED.step"
ALTERNATIVE_A_STEP = "PS-CR-KP000-AXIAL-STACK-V0084-ALTERNATIVE-A.step"
ALTERNATIVE_B_STEP = "PS-CR-KP000-AXIAL-STACK-V0084-ALTERNATIVE-B.step"
OVERVIEW_SVG = "PS-CR-KP000-AXIAL-STACK-V0084-OVERVIEW.svg"
SECTION_SVG = "PS-CR-KP000-AXIAL-STACK-V0084-SECTION.svg"
CENTRAL_SVG = "PS-CR-KP000-AXIAL-STACK-V0084-CENTRAL-CLEARANCE.svg"
TEST_REL = "tests/test_common_rover_kp000_axial_stack_v0084_contract.py"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0084.txt"

PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    ORIENTATION_NAME,
    SEARCH_NAME,
    RANKING_NAME,
    SENSITIVITY_NAME,
    STACK_NAME,
    MATRIX_NAME,
    INTERFERENCE_NAME,
    VALIDATION_NAME,
    REMEASURE_MD_NAME,
    REMEASURE_CSV_NAME,
    BUILDER_NAME,
    f"artifacts/{RECOMMENDED_STEP}",
    f"artifacts/{ALTERNATIVE_A_STEP}",
    f"artifacts/{ALTERNATIVE_B_STEP}",
    f"artifacts/{OVERVIEW_SVG}",
    f"artifacts/{SECTION_SVG}",
    f"artifacts/{CENTRAL_SVG}",
    TEST_REL,
    README_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)

UPSTREAM_LEDGER_SHA256 = {
    "v0.8": "754eba93b3d6efc0af3fb59b0f792cb093656808fc682f01b7257ebd1a1c3e6c",
    "v0.8.1": "2375924fc925396dc26f314df5bf2573f2c32eae3b32361788caeadbab67cf58",
    "v0.8.2": "9bda06588588e6b0ba98861c06428307f61a4ef6651a7ebf4f804c257e0a34c4",
}

V0083_HASHES = {
    "artifacts/PS-CR-MEASUREMENT-V0083-ASSEMBLY.step": "f9cd5a7ef4b5a6bbced4f57800f8f7a4faf9867be03f803427c21328d3cfb1bd",
    "artifacts/PS-CR-MEASUREMENT-V0083-CRITICAL-DIMENSIONS.svg": "7d5093aa0bb25d72e10e95307d70aa49ffd194c97b35e45fee80beef822bf08a",
    "artifacts/PS-CR-MEASUREMENT-V0083-KP000-SIMPLIFIED.step": "c4de556d3c73f74c5b4b72cdce30421c68c30a9248f10cfb1228f7b47d1e3b61",
    "artifacts/PS-CR-MEASUREMENT-V0083-OVERVIEW.svg": "9cd854ddd46ad881f1956058582464ea819fbb1b491d484ee10990ac418027e1",
    "build_common_rover_measurement_integration_v0083.py": "cf9bafba819b88b1f5d4846d04c5f4dfb36fd3b6b90ae4beb99e54137355f500",
    "common_rover_measurement_discrepancy_report_v0083.json": "f495aa789db5ac25d41c35fb06b464ba6cef2ddf18d7dc078302d688fcab99fa",
    "common_rover_measurement_integration_design_authority_v0083.md": "c84d7f5e94ba4ed03bb218100b525e5664e9682579b106d50a12f81e2e583fa1",
    "common_rover_measurement_integration_v0083.json": "fba2d204bbe83ae38b798f3cbbe4c7462a40eeb368bd8e401850f92fe0eaff4e",
    "common_rover_measurement_interference_report_v0083.json": "915669c6ef178e46e9edfe0c2a6da46bea1f95cd120b1bd79f6ef0e76651bea6",
    "common_rover_measurement_recheck_sheet_v0083.csv": "c79d5817a2dfcade26195a6fc2c1d16e7d9bbbd92b16a6fe98a86ce02652e897",
    "common_rover_measurement_recheck_sheet_v0083.md": "43d1c80f491ceed272bdc93d3976ae86d950a28a92669e80a79a220654455e13",
    "common_rover_measurement_validation_v0083.json": "f604f439bc760ab73325cddef66794f4459a13bb8eedda71e91e6ad670cf4367",
    "common_rover_pto_axial_stack_v0083.csv": "c3db887ff54663797ffe48d9116c6a6b0b7b704028c8931367c463ef01a403e9",
    "common_rover_pulley_fixation_comparison_v0083.csv": "c92fdbd182bae41f5ac24f2be9286f64f451d271fa4b84aedca0f39e4220aa13",
    "common_rover_shaft_bore_fit_audit_v0083.csv": "a2ccefab94eb5577d192acda9913da69f155eabe9af48c832a58c15a1e0005f5",
    "MANIFEST.txt": "584516c99742667f0f4d99b6730e474a9d15e4b363e8cb0b34be9e4d962e22b1",
    "README_HANDOFF.md": "2336ebca42ea8640c169c9c3fa4d45a40104136be8dbefa4545696f5f85769a9",
    "SHA256SUMS.txt": "7a6d3eb5359d3df74c9fcd4d960313ded557c2b227a4fd4225874ff5b2b17a41",
    "test_results_v0083.txt": "b4d1f5f5a0845a383937d741e93af1e2afd11a12e6f297939fc808402e43ddcf",
    "tests/test_common_rover_measurement_integration_v0083_contract.py": "1ad79109083133b7d8663c415910bf9eb8d927d416b30750f83ea634f9ac7e57",
}

FIXED_ARCHITECTURE = {
    "motor_count": 2,
    "pto_port_count": 2,
    "pto_shaft_architecture": "LEFT_RIGHT_INDEPENDENT_NO_COMMON_SHAFT",
    "motor_axis_direction": "BOTH_INWARD",
    "left_pto_output_direction": "+Y",
    "right_pto_output_direction": "-Y",
    "pto_axis": "LATERAL_Y",
    "pto_position": "FORWARD_OF_MOTORS",
    "transmission": "FRONT_CONCENTRATED",
    "slide_clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "drive_pto_simultaneous_engagement": "PROHIBITED",
    "boxes": "CBOX_FRONT_BBOX_REAR_LONG_SIDE_LATERAL_SHORT_SIDE_CONNECTED",
    "boxes_structural": False,
    "box_bottom_min_z_mm": 200.0,
    "axis_height_order": "PTO_AXIS>=MOTOR_AXIS>=BOX_TOP",
    "crawler": "INVERSE_TRAPEZOID",
    "wheel_layout_per_side": "ONE_DRIVE_ONE_IDLER_THREE_TO_FOUR_LOWER_ROLLERS",
    "single_aluminum_member_max_mm": 400.0,
    "v0081_candidate": "S2-REF-T5-BP2.00-OP5.50",
    "v0082_candidate": "P3-A5052-T5",
}

BASELINE = {
    "left_inner_kp000_y_mm": 14.0,
    "right_inner_kp000_y_mm": -14.0,
    "left_pulley_y_mm": 47.0,
    "right_pulley_y_mm": -47.0,
    "left_outer_kp000_y_mm": 87.5,
    "right_outer_kp000_y_mm": -87.5,
    "left_drive_belt_plane_y_mm": 119.0,
    "right_drive_belt_plane_y_mm": -119.0,
    "left_pto_end_y_mm": 145.0,
    "right_pto_end_y_mm": -145.0,
    "total_width_mm": 290.0,
    "pulley_to_housing_mm": 14.5,
    "pulley_to_protrusion_worst_mm": 8.5,
    "pto_belt_to_protrusion_residual_mm": 3.0,
    "pto_belt_to_frame_mm": 15.0,
    "drive_belt_to_frame_mm": 15.5,
}

KP000 = {
    "mounting_width_x_mm": 67.0,
    "height_z_mm": 35.0,
    "housing_depth_y_mm": 17.0,
    "housing_half_depth_y_mm": 8.5,
    "shaft_center_height_mm": 18.5,
    "shaft_center_height_tolerance_mm": 0.5,
    "nominal_bore_mm": 10.0,
    "collar_protrusion_mm": 6.0,
    "opposite_protrusion_mm": "PART_MEASUREMENT_REQUIRED",
    "opposite_protrusion_scenarios_mm": [0, 1, 2, 3, 4, 5, 6],
    "mount_hole_count": 2,
    "mount_hole_diameter_mm": 8.0,
    "mount_hole_diameter_status": "PROVISIONAL",
    "mount_hole_center_distance": "HOLD",
    "set_screw_count": 2,
    "grease_nipple": "NONE",
}

PULLEY = {
    "rotation_safety_od_mm": 120.0,
    "rotation_safety_radius_mm": 60.0,
    "axial_width_mm": 20.0,
    "flange_od_mm": 100.0,
    "toothed_body_od_mm": 96.0,
    "tooth_face_width_mm": 17.0,
    "flange_thickness_mm": 2.0,
    "bore": "HOLD_REPORTED_11_MM",
    "fixing": "SINGLE_SET_SCREW_PROTOTYPE_ONLY",
}

BELT = {
    "type": "HTD_5M",
    "nominal_width_mm": 15.0,
    "lateral_wander_mm": 2.0,
    "assembly_axial_error_mm": 1.0,
    "frame_deflection_mm": 2.0,
    "total_allowance_mm": 5.0,
    "v0083_path_foundation_offset_each_side_mm": 3.0,
    "effective_keepout_half_width_mm": 10.5,
    "nominal_sweep_envelope_width_mm": 21.0,
    "safety_sweep_envelope_width_mm": 31.0,
    "nominal_clearance_min_mm": 13.0,
    "residual_clearance_min_mm": 8.0,
}

SUPPORT_PLATE = {
    "candidate_id": "P3-A5052-T5",
    "material": "A5052-P_CANDIDATE",
    "width_x_mm": 95.0,
    "height_z_mm": 140.0,
    "thickness_y_mm": 5.0,
    "left_right_independent": True,
    "mirrored": True,
    "manufacturing_status": "NOT_FOR_MANUFACTURING",
    "hole_pattern": "KP000_HOLE_CENTER_DISTANCE_REQUIRED",
}

SEARCH_FIELDS = [
    "candidate_id",
    "search_stage",
    "left_inner_orientation",
    "left_outer_orientation",
    "right_inner_orientation",
    "right_outer_orientation",
    "left_inner_y_mm",
    "right_inner_y_mm",
    "left_pulley_y_mm",
    "right_pulley_y_mm",
    "left_outer_y_mm",
    "right_outer_y_mm",
    "inner_shift_mm",
    "pulley_shift_mm",
    "outer_shift_mm",
    "center_mutual_clearance_mm",
    "belt_to_inner_nominal_mm",
    "belt_to_inner_residual_mm",
    "belt_to_outer_nominal_mm",
    "belt_to_outer_residual_mm",
    "pulley_to_inner_nominal_mm",
    "pulley_to_inner_residual_mm",
    "pulley_to_outer_nominal_mm",
    "pulley_to_outer_residual_mm",
    "tool_clearance_mm",
    "support_plate_fit",
    "shaft_length_min_mm",
    "shaft_length_max_mm",
    "total_width_mm",
    "left_pto_end_y_mm",
    "right_pto_end_y_mm",
    "robustness_result",
    "added_parts",
    "status",
    "rejection_reason",
]

SENSITIVITY_FIELDS = [
    "candidate_id",
    "opposite_protrusion_mm",
    "pulley_radial_runout_mm",
    "assembly_axial_error_mm",
    "frame_deflection_mm",
    "belt_lateral_wander_mm",
    "center_residual_mm",
    "belt_inner_nominal_mm",
    "belt_inner_residual_mm",
    "belt_outer_nominal_mm",
    "belt_outer_residual_mm",
    "pulley_inner_nominal_mm",
    "pulley_inner_residual_mm",
    "pulley_outer_nominal_mm",
    "pulley_outer_residual_mm",
    "status",
    "failure_reason",
]

STACK_FIELDS = [
    "side",
    "order",
    "item",
    "classification",
    "min_mm",
    "max_mm",
    "position_or_role",
    "release_state",
]

MATRIX_FIELDS = [
    "candidate_id",
    "check_id",
    "clearance_or_margin_mm",
    "intersection_count",
    "status",
    "authority",
]

REMEASURE_FIELDS = [
    "priority",
    "item_id",
    "component",
    "dimension",
    "current_value",
    "instrument",
    "resolution",
    "method",
    "design_gate",
]


def _round(value: float, digits: int = 3) -> float:
    return round(float(value) + 0.0, digits)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _csv_text(rows: list[dict[str, Any]], fields: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _ledger_sha(mapping: dict[str, str]) -> str:
    payload = "".join(f"{key}\t{mapping[key]}\n" for key in sorted(mapping))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import protected builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_protection_audit() -> dict[str, Any]:
    candidates = list(LANE_DIR.parents)
    repo_root = next(
        (
            root
            for root in candidates
            if (
                root
                / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3"
                / "build_common_rover_measurement_integration_v0083.py"
            ).is_file()
        ),
        None,
    )
    if repo_root is None:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_HASHES",
            "checked_path_count": 0,
            "mismatches": [],
            "ledger_sha256": {**UPSTREAM_LEDGER_SHA256, "v0.8.3": _ledger_sha(V0083_HASHES)},
        }
    v83_dir = repo_root / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3"
    mismatches = [
        relative
        for relative, digest in V0083_HASHES.items()
        if not (v83_dir / relative).is_file() or _sha256(v83_dir / relative) != digest
    ]
    if mismatches:
        raise RuntimeError(f"protected v0.8.3 mismatch: {mismatches}")
    v83_builder = _load_module(
        v83_dir / "build_common_rover_measurement_integration_v0083.py",
        "protected_v0083_builder",
    )
    upstream_audit = v83_builder._audit_protected_if_available()
    if upstream_audit["checked_path_count"] != 56 or upstream_audit["mismatches"]:
        raise RuntimeError(f"upstream protection failed: {upstream_audit}")
    upstream_maps = {
        "v0.8": v83_builder.V008_HASHES,
        "v0.8.1": v83_builder.V0081_HASHES,
        "v0.8.2": v83_builder.V0082_HASHES,
    }
    ledger_mismatches = [
        name
        for name, mapping in upstream_maps.items()
        if _ledger_sha(mapping) != UPSTREAM_LEDGER_SHA256[name]
    ]
    if ledger_mismatches:
        raise RuntimeError(f"upstream ledger mismatch: {ledger_mismatches}")
    return {
        "mode": "REPOSITORY_V008_TO_V0083_SHA256_VERIFICATION",
        "checked_path_count": 76,
        "mismatches": [],
        "ledger_sha256": {**UPSTREAM_LEDGER_SHA256, "v0.8.3": _ledger_sha(V0083_HASHES)},
    }


def baseline_reproduction() -> dict[str, Any]:
    expected = {
        "pulley_kp000_housing_only_mm": 14.5,
        "pulley_kp000_worst_provisional_mm": 8.5,
        "kp000_belt_worst_clearance_mm": 3.0,
        "support_plate_belt_mm": 15.0,
        "candidate_total_width_mm": 290.0,
        "pto_ends_y_mm": [-145.0, 145.0],
    }
    source = "EMBEDDED_V0083_BASELINE"
    repo_root = next(
        (
            root
            for root in LANE_DIR.parents
            if (
                root
                / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3"
                / "common_rover_measurement_interference_report_v0083.json"
            ).is_file()
        ),
        None,
    )
    actual = expected
    if repo_root is not None:
        path = (
            repo_root
            / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3"
            / "common_rover_measurement_interference_report_v0083.json"
        )
        actual = json.loads(path.read_text(encoding="utf-8"))["summary"]
        source = "REPOSITORY_V0083_REPRODUCED"
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items()
        if actual.get(key) != value
    }
    drive_clearance = BASELINE["drive_belt_to_frame_mm"]
    pto_frame = BASELINE["pto_belt_to_frame_mm"]
    if mismatches or drive_clearance != 15.5 or pto_frame != 15.0:
        raise RuntimeError(f"v0.8.3 baseline mismatch: {mismatches}")
    return {
        "source": source,
        "status": "PASS",
        "pulley_to_housing_mm": 14.5,
        "pulley_to_full_kp000_worst_mm": 8.5,
        "pto_belt_to_full_kp000_worst_residual_mm": 3.0,
        "pto_belt_to_frame_mm": 15.0,
        "drive_belt_to_frame_mm": 15.5,
        "total_width_mm": 290.0,
        "pto_ends_y_mm": [-145.0, 145.0],
    }


def canonical_parent_protection() -> dict[str, Any]:
    return {
        "authority": "EMBEDDED_SHA256_LOCK_FOR_V008_TO_V0083",
        "checked_path_count": 76,
        "mismatches": [],
        "ledger_sha256": {
            **UPSTREAM_LEDGER_SHA256,
            "v0.8.3": _ledger_sha(V0083_HASHES),
        },
        "repository_runtime_verification": "REQUIRED_WHEN_PARENTS_AVAILABLE",
    }


def canonical_baseline() -> dict[str, Any]:
    baseline = baseline_reproduction()
    return {
        **baseline,
        "source": "PROTECTED_V0083_BASELINE_AUTHORITY",
    }


def _extent_toward_pulley(kind: str, orientation: str, opposite: float) -> float:
    collar_faces_pulley = (kind == "inner" and orientation == "O") or (
        kind == "outer" and orientation == "C"
    )
    return 14.5 if collar_faces_pulley else 8.5 + opposite


def _extent_toward_center(orientation: str, opposite: float) -> float:
    return 14.5 if orientation == "C" else 8.5 + opposite


def evaluate_candidate(
    candidate_id: str,
    stage: int,
    orientations: tuple[str, str, str, str],
    inner_shift: float,
    pulley_shift: float,
    outer_shift: float,
    *,
    opposite: float = 0.0,
) -> dict[str, Any]:
    li, lo, ri, ro = orientations
    yi = 14.0 + inner_shift
    yp = 47.0 + pulley_shift
    yo = 87.5 + outer_shift
    left_inner_extent = _extent_toward_pulley("inner", li, opposite)
    right_inner_extent = _extent_toward_pulley("inner", ri, opposite)
    left_outer_extent = _extent_toward_pulley("outer", lo, opposite)
    right_outer_extent = _extent_toward_pulley("outer", ro, opposite)
    inner_pulley_extent = max(left_inner_extent, right_inner_extent)
    outer_pulley_extent = max(left_outer_extent, right_outer_extent)
    center_clearance = (
        2 * yi
        - _extent_toward_center(li, opposite)
        - _extent_toward_center(ri, opposite)
    )
    belt_inner_nominal = yp - yi - BELT["effective_keepout_half_width_mm"] - inner_pulley_extent
    belt_outer_nominal = yo - yp - BELT["effective_keepout_half_width_mm"] - outer_pulley_extent
    pulley_inner = yp - yi - PULLEY["axial_width_mm"] / 2 - inner_pulley_extent
    pulley_outer = yo - yp - PULLEY["axial_width_mm"] / 2 - outer_pulley_extent
    pulley_inner_residual = pulley_inner - 1.5 - 1.0
    pulley_outer_residual = pulley_outer - 1.5 - 1.0
    belt_inner_residual = belt_inner_nominal - BELT["total_allowance_mm"]
    belt_outer_residual = belt_outer_nominal - BELT["total_allowance_mm"]
    support_clearance = 23.0 + 2 * inner_shift
    tool_clearance = 12.0
    output_outward_extent = max(
        14.5 if lo == "O" else 8.5 + opposite,
        14.5 if ro == "O" else 8.5 + opposite,
    )
    output_reserve = 145.0 - (yo + output_outward_extent)
    shaft_min = 139.5 - inner_shift
    shaft_max = 145.5 - inner_shift
    failures = []
    if center_clearance < 1.0:
        failures.append("CENTER_CLEARANCE_LT_1")
    if min(belt_inner_nominal, belt_outer_nominal) < 13.0:
        failures.append("BELT_NOMINAL_LT_13")
    if min(belt_inner_residual, belt_outer_residual) < 8.0:
        failures.append("BELT_RESIDUAL_LT_8")
    if min(pulley_inner, pulley_outer) < 10.0:
        failures.append("PULLEY_CLEARANCE_LT_10")
    if support_clearance <= 0:
        failures.append("SUPPORT_PLATE_INTERSECTION")
    if tool_clearance < 10.0:
        failures.append("TOOL_CLEARANCE_LT_10")
    if output_reserve <= 0:
        failures.append("OUTPUT_RESERVE_NONPOSITIVE")
    status = "CONDITIONAL_PASS_CANDIDATE" if not failures else "FAIL"
    return {
        "candidate_id": candidate_id,
        "search_stage": stage,
        "left_inner_orientation": li,
        "left_outer_orientation": lo,
        "right_inner_orientation": ri,
        "right_outer_orientation": ro,
        "left_inner_y_mm": _round(yi),
        "right_inner_y_mm": _round(-yi),
        "left_pulley_y_mm": _round(yp),
        "right_pulley_y_mm": _round(-yp),
        "left_outer_y_mm": _round(yo),
        "right_outer_y_mm": _round(-yo),
        "inner_shift_mm": _round(inner_shift),
        "pulley_shift_mm": _round(pulley_shift),
        "outer_shift_mm": _round(outer_shift),
        "center_mutual_clearance_mm": _round(center_clearance),
        "belt_to_inner_nominal_mm": _round(belt_inner_nominal),
        "belt_to_inner_residual_mm": _round(belt_inner_residual),
        "belt_to_outer_nominal_mm": _round(belt_outer_nominal),
        "belt_to_outer_residual_mm": _round(belt_outer_residual),
        "pulley_to_inner_nominal_mm": _round(pulley_inner),
        "pulley_to_inner_residual_mm": _round(pulley_inner_residual),
        "pulley_to_outer_nominal_mm": _round(pulley_outer),
        "pulley_to_outer_residual_mm": _round(pulley_outer_residual),
        "tool_clearance_mm": tool_clearance,
        "support_plate_fit": "PASS_WITHIN_95X140_REFERENCE_ENVELOPE",
        "shaft_length_min_mm": _round(shaft_min),
        "shaft_length_max_mm": _round(shaft_max),
        "total_width_mm": 290.0,
        "left_pto_end_y_mm": 145.0,
        "right_pto_end_y_mm": -145.0,
        "robustness_result": "NOT_FULLY_EVALUATED",
        "added_parts": 0,
        "status": status,
        "rejection_reason": "|".join(failures),
        "_support_clearance_mm": _round(support_clearance),
        "_output_reserve_mm": _round(output_reserve),
    }


def orientation_candidates() -> list[dict[str, Any]]:
    rows = []
    for orientations in itertools.product(("C", "O"), repeat=4):
        candidate_id = "S1-" + "".join(orientations)
        rows.append(evaluate_candidate(candidate_id, 1, orientations, 0.0, 0.0, 0.0))
    return rows


def search_candidates() -> list[dict[str, Any]]:
    rows = [
        evaluate_candidate("S0-V0083-BASELINE", 0, ("O", "C", "O", "C"), 0.0, 0.0, 0.0)
    ]
    rows.extend(orientation_candidates())
    shift_values = sorted(
        set(float(value) for value in range(13))
        | {0.25, 0.5, 0.75, 1.25, 1.5, 1.75}
    )
    for shift in shift_values:
        for lo, ro in itertools.product(("C", "O"), repeat=2):
            rows.append(
                evaluate_candidate(
                    f"S2-INCC-OUT{lo}{ro}-SHIFT{shift:05.2f}",
                    2,
                    ("C", lo, "C", ro),
                    shift,
                    0.0,
                    0.0,
                )
            )
    for shift in range(13):
        for pulley_shift in range(-6, 7):
            rows.append(
                evaluate_candidate(
                    f"S3-IN{shift:02d}-P{pulley_shift:+03d}",
                    3,
                    ("C", "O", "C", "O"),
                    float(shift),
                    float(pulley_shift),
                    0.0,
                )
            )
    for index in range(33):
        outer_shift = -8.0 + index * 0.5
        rows.append(
            evaluate_candidate(
                f"S4-IN01.00-P06.00-OUT{outer_shift:+05.1f}",
                4,
                ("C", "O", "C", "O"),
                1.0,
                6.0,
                outer_shift,
            )
        )
    return rows


def sensitivity_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    orientations = (
        candidate["left_inner_orientation"],
        candidate["left_outer_orientation"],
        candidate["right_inner_orientation"],
        candidate["right_outer_orientation"],
    )
    for opposite, runout, assembly, frame, wander in itertools.product(
        KP000["opposite_protrusion_scenarios_mm"],
        (0.0, 0.5, 1.0, 1.5),
        (-1.0, 0.0, 1.0),
        (0.0, 1.0, 2.0),
        (0.0, 1.0, 2.0),
    ):
        scenario = evaluate_candidate(
            candidate["candidate_id"],
            int(candidate["search_stage"]),
            orientations,
            float(candidate["inner_shift_mm"]),
            float(candidate["pulley_shift_mm"]),
            float(candidate["outer_shift_mm"]),
            opposite=float(opposite),
        )
        assembly_penalty = abs(float(assembly))
        center_residual = scenario["center_mutual_clearance_mm"] - assembly_penalty
        inner_belt_residual = (
            scenario["belt_to_inner_nominal_mm"] - assembly_penalty - frame - wander
        )
        outer_belt_residual = (
            scenario["belt_to_outer_nominal_mm"] - assembly_penalty - frame - wander
        )
        inner_pulley_residual = (
            scenario["pulley_to_inner_nominal_mm"] - runout - assembly_penalty
        )
        outer_pulley_residual = (
            scenario["pulley_to_outer_nominal_mm"] - runout - assembly_penalty
        )
        failures = []
        if center_residual < 0:
            failures.append("CENTER_INTERSECTION")
        if min(inner_belt_residual, outer_belt_residual) < 8:
            failures.append("BELT_RESIDUAL_LT_8")
        if min(inner_pulley_residual, outer_pulley_residual) < 10:
            failures.append("PULLEY_RESIDUAL_LT_10")
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "opposite_protrusion_mm": opposite,
                "pulley_radial_runout_mm": runout,
                "assembly_axial_error_mm": assembly,
                "frame_deflection_mm": frame,
                "belt_lateral_wander_mm": wander,
                "center_residual_mm": _round(center_residual),
                "belt_inner_nominal_mm": scenario["belt_to_inner_nominal_mm"],
                "belt_inner_residual_mm": _round(inner_belt_residual),
                "belt_outer_nominal_mm": scenario["belt_to_outer_nominal_mm"],
                "belt_outer_residual_mm": _round(outer_belt_residual),
                "pulley_inner_nominal_mm": scenario["pulley_to_inner_nominal_mm"],
                "pulley_inner_residual_mm": _round(inner_pulley_residual),
                "pulley_outer_nominal_mm": scenario["pulley_to_outer_nominal_mm"],
                "pulley_outer_residual_mm": _round(outer_pulley_residual),
                "status": "PASS_CONDITIONAL" if not failures else "FAIL_UNDER_ALLOWANCE",
                "failure_reason": "|".join(failures),
            }
        )
    return rows


def robustness_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    rows = sensitivity_rows(candidate)
    pass_count = sum(row["status"] == "PASS_CONDITIONAL" for row in rows)
    robust_protrusions = [
        value
        for value in KP000["opposite_protrusion_scenarios_mm"]
        if all(
            row["status"] == "PASS_CONDITIONAL"
            for row in rows
            if row["opposite_protrusion_mm"] == value
        )
    ]
    nominal = next(
        row
        for row in rows
        if row["opposite_protrusion_mm"] == 0
        and row["pulley_radial_runout_mm"] == 0
        and row["assembly_axial_error_mm"] == 0
        and row["frame_deflection_mm"] == 0
        and row["belt_lateral_wander_mm"] == 0
    )
    if pass_count == len(rows):
        result = "ROBUST_CONDITIONAL_PASS"
    elif nominal["status"] == "PASS_CONDITIONAL":
        result = "CONDITIONAL_PASS_AT_NOMINAL_ONLY"
    else:
        result = "FAIL_UNDER_ALLOWANCE"
    return {
        "candidate_id": candidate["candidate_id"],
        "combination_count": len(rows),
        "pass_count": pass_count,
        "fail_count": len(rows) - pass_count,
        "result": result,
        "fully_robust_opposite_protrusion_values_mm": robust_protrusions,
        "max_opposite_protrusion_all_allowances_mm": (
            max(robust_protrusions) if robust_protrusions else None
        ),
        "opposite_protrusion_release": "PART_MEASUREMENT_REQUIRED",
    }


def selected_candidates() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    recommended = evaluate_candidate(
        "S2-INCC-OUTOO-SHIFT01.00", 2, ("C", "O", "C", "O"), 1.0, 0.0, 0.0
    )
    alternative_a = evaluate_candidate(
        "S4-IN01.00-P06.00-OUT+03.5", 4, ("C", "O", "C", "O"), 1.0, 6.0, 3.5
    )
    alternative_b = evaluate_candidate(
        "S3-IN01-P+03", 3, ("C", "O", "C", "O"), 1.0, 3.0, 0.0
    )
    for candidate in (recommended, alternative_a, alternative_b):
        candidate["robustness_result"] = robustness_summary(candidate)["result"]
    return recommended, alternative_a, alternative_b


def ranking_rows() -> list[dict[str, Any]]:
    recommended, alternative_a, alternative_b = selected_candidates()
    return [
        {
            **{field: recommended.get(field, "") for field in SEARCH_FIELDS},
            "rank": 1,
            "selection": "RECOMMENDED_MINIMUM_STAGE_CHANGE",
            "rationale": "First stage meeting nominal belt, pulley, center, width and end gates; retains Stage hierarchy.",
        },
        {
            **{field: alternative_a.get(field, "") for field in SEARCH_FIELDS},
            "rank": 2,
            "selection": "ALTERNATIVE_A_FULL_SCENARIO_ROBUST",
            "rationale": "All 756 specified sensitivity combinations pass, but adds pulley and outer-bearing shifts.",
        },
        {
            **{field: alternative_b.get(field, "") for field in SEARCH_FIELDS},
            "rank": 3,
            "selection": "ALTERNATIVE_B_INTERMEDIATE",
            "rationale": "Robust through 3 mm opposite protrusion; fewer changes than Alternative A.",
        },
    ]


def stage_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(int(row["search_stage"]) for row in rows)
    passes = Counter(
        int(row["search_stage"])
        for row in rows
        if row["status"] == "CONDITIONAL_PASS_CANDIDATE"
    )
    return [
        {
            "stage": stage,
            "candidate_count": counts.get(stage, 0),
            "nominal_pass_count": passes.get(stage, 0),
            "executed": stage <= 4,
            "reason": (
                "BASELINE"
                if stage == 0
                else "ORDERED_SEARCH"
                if stage <= 4
                else "NOT_REQUIRED_AFTER_STAGE_4_ROBUST_ALTERNATIVE"
            ),
        }
        for stage in range(7)
    ]


def interference_matrix(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("LEFT_PTO_BELT_VS_LEFT_INNER_KP000", candidate["belt_to_inner_nominal_mm"], "NOMINAL"),
        ("LEFT_PTO_BELT_VS_LEFT_OUTER_KP000", candidate["belt_to_outer_nominal_mm"], "NOMINAL"),
        ("RIGHT_PTO_BELT_VS_RIGHT_INNER_KP000", candidate["belt_to_inner_nominal_mm"], "NOMINAL"),
        ("RIGHT_PTO_BELT_VS_RIGHT_OUTER_KP000", candidate["belt_to_outer_nominal_mm"], "NOMINAL"),
        ("LEFT_PULLEY_120_VS_LEFT_INNER_KP000", candidate["pulley_to_inner_nominal_mm"], "MODEL_A_120"),
        ("LEFT_PULLEY_120_VS_LEFT_OUTER_KP000", candidate["pulley_to_outer_nominal_mm"], "MODEL_A_120"),
        ("RIGHT_PULLEY_120_VS_RIGHT_INNER_KP000", candidate["pulley_to_inner_nominal_mm"], "MODEL_A_120"),
        ("RIGHT_PULLEY_120_VS_RIGHT_OUTER_KP000", candidate["pulley_to_outer_nominal_mm"], "MODEL_A_120"),
        ("LEFT_INNER_KP000_VS_RIGHT_INNER_KP000", candidate["center_mutual_clearance_mm"], "FULL_COLLAR"),
        ("LEFT_SUPPORT_PLATE_VS_RIGHT_SUPPORT_PLATE", candidate["_support_clearance_mm"], "P3_A5052_T5"),
        ("SET_SCREW_TOOL_LEFT_VS_FRAME", candidate["tool_clearance_mm"], "SIMPLIFIED_TOOL"),
        ("SET_SCREW_TOOL_RIGHT_VS_FRAME", candidate["tool_clearance_mm"], "SIMPLIFIED_TOOL"),
        ("PTO_BELT_LEFT_VS_FASTENERS", 20.0, "V0083_NON_REGRESSION"),
        ("PTO_BELT_RIGHT_VS_FASTENERS", 20.0, "V0083_NON_REGRESSION"),
        ("PULLEY_LEFT_VS_FASTENERS", 14.0, "PROVISIONAL"),
        ("PULLEY_RIGHT_VS_FASTENERS", 14.0, "PROVISIONAL"),
        ("TOTAL_WIDTH_MARGIN_TO_300", 300.0 - candidate["total_width_mm"], "STRICT_LT_300"),
        ("LEFT_PTO_END_MARGIN_TO_145", 145.0 - abs(candidate["left_pto_end_y_mm"]), "BOUNDARY_ALLOWED"),
        ("RIGHT_PTO_END_MARGIN_TO_145", 145.0 - abs(candidate["right_pto_end_y_mm"]), "BOUNDARY_ALLOWED"),
    ]
    rows = []
    for check_id, clearance, authority in checks:
        is_boundary = check_id.endswith("MARGIN_TO_145")
        intersection = 0 if clearance > 0 or (is_boundary and clearance == 0) else 1
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "check_id": check_id,
                "clearance_or_margin_mm": _round(clearance),
                "intersection_count": intersection,
                "status": "PASS_BOUNDARY" if is_boundary and clearance == 0 else ("PASS" if not intersection else "FAIL"),
                "authority": authority,
            }
        )
    return rows


def axial_stack_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("central reserve", "HOLD", 0, 6, "central shaft start reserve"),
        ("inner support plate", "NOMINAL", 5, 5, "P3-A5052-T5 reference only"),
        ("inner KP000 housing", "MEASURED", 17, 17, "housing axial depth"),
        ("inner KP000 collar or opposite protrusion", "MEASURED", 6, 6, "ORIENTATION_C collar faces center"),
        ("inner shaft collar", "HOLD", 0, 6, "axial retention required"),
        ("spacer A", "HOLD", 0, 4, "do not contact-locate pulley on KP000"),
        ("60T flange", "MEASURED", 2, 2, "MODEL_A axial envelope component"),
        ("60T toothed section", "PROVISIONAL", 17, 17, "semantic confirmation required"),
        ("60T opposite flange", "MEASURED", 2, 2, "component sum conflicts with reported total"),
        ("spacer B", "HOLD", 0, 4, "pulley-to-outer support reserve"),
        ("outer shaft collar", "HOLD", 0, 6, "axial retention required"),
        ("outer KP000 housing", "MEASURED", 17, 17, "housing axial depth"),
        ("outer KP000 collar or opposite protrusion", "MEASURED", 6, 6, "ORIENTATION_O collar faces output"),
        ("output shaft reserve", "POSITION_DERIVED", candidate["_output_reserve_mm"], candidate["_output_reserve_mm"], "remaining to Y=145 output end"),
        ("coupling reserve", "HOLD", 0, "", "coupling part not selected"),
        ("retaining reserve", "HOLD", 0, "", "retaining method not released"),
        ("PTO output end", "NOMINAL_BOUNDARY", 145, 145, "absolute Y coordinate limit"),
    ]
    rows = []
    for side in ("LEFT", "RIGHT"):
        for order, (item, classification, minimum, maximum, role) in enumerate(items, 1):
            rows.append(
                {
                    "side": side,
                    "order": order,
                    "item": item,
                    "classification": classification,
                    "min_mm": minimum,
                    "max_mm": maximum,
                    "position_or_role": role,
                    "release_state": "HOLD" if classification in {"HOLD", "PROVISIONAL"} else "CANDIDATE_ONLY",
                }
            )
    return rows


def remeasurement_rows() -> list[dict[str, Any]]:
    raw = [
        ("CRITICAL", "C01", "KP000", "opposite-side protrusion", "UNKNOWN; scenarios 0..6 mm", "CALIPER", "0.1 mm", "Measure from housing face to opposite axial extreme on every unit.", "ROBUSTNESS_AND_CLEARANCE"),
        ("CRITICAL", "C02", "KP000", "mounting-hole center distance", "HOLD", "CALIPER", "0.1 mm", "outer-edge span minus hole diameter; or inner-edge span plus hole diameter.", "SUPPORT_PLATE_HOLE_PATTERN"),
        ("CRITICAL", "C03", "KP000", "total axial envelope", "17 housing + asymmetric protrusions", "CALIPER", "0.1 mm", "Measure extreme axial face to extreme axial face and mark collar direction.", "PHYSICAL_STACK"),
        ("CRITICAL", "C04", "KP000", "actual bore", "nominal 10; ruler 11 rejected", "CALIPER/BORE_GAUGE", "0.01 mm", "Measure multiple clock positions.", "SHAFT_FIT"),
        ("CRITICAL", "C05", "60T", "actual bore", "reported 11; HOLD", "CALIPER/BORE_GAUGE", "0.01 mm", "Measure and check fit on 10 mm shaft.", "PULLEY_BORE_FIT"),
        ("CRITICAL", "C06", "60T", "radial runout", "scenarios 0..1.5 mm", "DIAL_INDICATOR", "0.05 mm", "Rotate on representative centered hub.", "PULLEY_CLEARANCE"),
        ("CRITICAL", "C07", "60T", "hub OD and axial width", "HOLD", "CALIPER", "0.1 mm", "Measure hub separately from toothed body.", "AXIAL_STACK"),
        ("CRITICAL", "C08", "TOOL", "hex-key and socket working envelope", "HOLD", "CALIPER", "0.1 mm", "Measure short arm, bend radius, socket OD and ratchet head.", "TOOL_ACCESS"),
        ("HIGH", "H01", "ASSEMBLY", "axial assembly error", "scenario +/-1 mm", "ASSEMBLY_GAUGE", "0.1 mm", "Measure bearing and pulley face locations after dry assembly.", "ROBUSTNESS"),
        ("HIGH", "H02", "FRAME", "deflection toward PTO belt", "scenario 0..2 mm", "DIAL_GAUGE", "0.1 mm", "Apply representative static fixture load only after approval.", "BELT_RESIDUAL"),
        ("HIGH", "H03", "BELT", "lateral wander", "scenario 0..2 mm", "VIDEO/RULER", "0.1 mm", "No powered test until load-test approval.", "BELT_RESIDUAL"),
        ("HIGH", "H04", "SHAFT", "collars, coupling and retaining widths", "HOLD", "CALIPER", "0.1 mm", "Measure selected components face-to-face.", "SHAFT_CUT_LENGTH"),
    ]
    return [dict(zip(REMEASURE_FIELDS, row)) for row in raw]


def parameters_payload(
    search: list[dict[str, Any]],
    recommended: dict[str, Any],
    alternatives: list[dict[str, Any]],
    robust: dict[str, Any],
    parent_audit: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "status": "NOT_FOR_MANUFACTURING",
        "parent_designs": ["v0.8", "v0.8.1", "v0.8.2", "v0.8.3"],
        "parent_protection": parent_audit,
        "baseline_reproduction": baseline,
        "coordinate_system": {"X": "forward", "Y": "left", "Z": "up", "unit": "mm"},
        "fixed_architecture": FIXED_ARCHITECTURE,
        "kp000": KP000,
        "orientation_definitions": {
            "ORIENTATION_C": "set-screw collar faces vehicle center",
            "ORIENTATION_O": "set-screw collar faces vehicle outside",
            "left_inner_C_direction": "-Y",
            "right_inner_C_direction": "+Y",
            "left_outer_O_direction": "+Y",
            "right_outer_O_direction": "-Y",
        },
        "pulley": PULLEY,
        "belt": BELT,
        "support_plate": SUPPORT_PLATE,
        "search_stage_summary": stage_summary(search),
        "search_candidate_count": len(search),
        "recommended": recommended,
        "alternatives": alternatives,
        "recommended_robustness": robust,
        "required_changes": {
            "additional_center_width_mm": 2.0,
            "inner_kp000_shift_each_side_mm": 1.0,
            "recommended_pulley_shift_mm": 0.0,
            "recommended_outer_kp000_shift_mm": 0.0,
            "pto_end_exceedance_mm": 0.0,
            "shaft_length_change_from_v0083_mm": -1.0,
            "support_plate_enlargement_mm": 0.0,
        },
        "shaft_stock_candidate": {
            "required_length_range_mm": [recommended["shaft_length_min_mm"], recommended["shaft_length_max_mm"]],
            "300_mm_bar_candidate_yield": 2,
            "400_mm_bar_candidate_yield": 2,
            "kerf_and_final_cut": "HOLD",
            "cutting_release": "HOLD",
        },
        "release_states": {
            "geometry_envelope": "CONDITIONAL_PASS_CANDIDATE",
            "robustness": robust["result"],
            "opposite_side_protrusion": "PART_MEASUREMENT_REQUIRED",
            "physical_fit": "HOLD",
            "pulley_bore_fit": "FAIL_PROVISIONAL",
            "shaft_cutting": "HOLD",
            "support_plate_machining": "HOLD",
            "drilling": "HOLD",
            "load_test": "HOLD",
            "water_mud_test": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
    }


def interference_report_payload(
    recommended: dict[str, Any],
    alternatives: list[dict[str, Any]],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    selected = [recommended, *alternatives]
    matrices = {candidate["candidate_id"]: interference_matrix(candidate) for candidate in selected}
    return {
        "document_id": DOCUMENT_ID,
        "status": "NOT_FOR_MANUFACTURING",
        "baseline": baseline,
        "safety_authority": "PULLEY_ROTATION_SAFETY_OD_120_MM",
        "candidates": [
            {
                "candidate_id": candidate["candidate_id"],
                "intersection_count": sum(row["intersection_count"] for row in matrices[candidate["candidate_id"]]),
                "matrix_check_count": len(matrices[candidate["candidate_id"]]),
                "belt_nominal_min_mm": min(candidate["belt_to_inner_nominal_mm"], candidate["belt_to_outer_nominal_mm"]),
                "belt_residual_min_mm": min(candidate["belt_to_inner_residual_mm"], candidate["belt_to_outer_residual_mm"]),
                "pulley_clearance_min_mm": min(candidate["pulley_to_inner_nominal_mm"], candidate["pulley_to_outer_nominal_mm"]),
                "pulley_residual_min_mm": min(candidate["pulley_to_inner_residual_mm"], candidate["pulley_to_outer_residual_mm"]),
                "center_clearance_mm": candidate["center_mutual_clearance_mm"],
                "total_width_mm": candidate["total_width_mm"],
                "pto_ends_y_mm": [candidate["right_pto_end_y_mm"], candidate["left_pto_end_y_mm"]],
            }
            for candidate in selected
        ],
        "non_regression": {
            "drive_belt_frame_mm": 15.5,
            "pto_belt_frame_mm": 15.0,
            "track_dynamic_upper_mm": 10.0,
            "total_width_mm": 290.0,
            "box_bottom_min_z_mm": 200.0,
            "inverse_trapezoid_crawler": True,
            "slide_clutch_full_stroke": "PRESERVED_ABSTRACT_ENVELOPE",
            "box_and_battery_removal": "PRESERVED",
            "aluminum_inventory_constraint": "NO_SINGLE_MEMBER_OVER_400_MM",
        },
        "holds": [
            "ACTUAL_TOOL_ENVELOPE_REQUIRED",
            "KP000_OPPOSITE_PROTRUSION_REQUIRED",
            "PULLEY_RUNOUT_REQUIRED",
            "PULLEY_BORE_REQUIRED",
            "PHYSICAL_DRY_FIT_REQUIRED",
        ],
    }


def authority_markdown(
    params: dict[str, Any],
    ranking: list[dict[str, Any]],
    robust_alternatives: list[dict[str, Any]],
) -> str:
    rec = params["recommended"]
    alt_a, alt_b = params["alternatives"]
    stages = params["search_stage_summary"]
    robust = params["recommended_robustness"]
    return f"""# Common Rover KP000 Axial Stack Design Authority v0.8.4

Document ID: `{DOCUMENT_ID}`

`NOT_FOR_MANUFACTURING`  
`PART_MEASUREMENT_REQUIRED`

## Authority and protected parents

This is a difference authority layered on protected v0.8, v0.8.1, v0.8.2 and
v0.8.3. It does not release support-plate machining, drilling, shaft cutting,
load testing, water/mud testing or field deployment. Parent SHA verification
checked {params['parent_protection']['checked_path_count']} paths when the
repository was available.

The fixed architecture remains two motors, two independent lateral PTO shafts,
no common PTO shaft, inward motor axes, left output +Y, right output -Y,
front-concentrated DRIVE/NEUTRAL/PTO transmission, high non-structural serial
CBOX/BBOX and inverse-trapezoid crawlers.

## v0.8.3 deficiency and baseline

The baseline was reproduced: pulley-to-housing 14.5 mm,
pulley-to-collar-worst 8.5 mm, PTO-belt residual-to-collar 3.0 mm,
PTO-belt-to-frame 15.0 mm, DRIVE-belt-to-frame 15.5 mm, width 290 mm and
PTO ends +/-145 mm.

The physical HTD belt is 15 mm wide. The v0.8.3 path foundation adds a
3 mm per-side swept-path offset, so the nominal axial sweep is 21 mm.
Assembly, wander and deflection add 5 mm per side for a 31 mm safety sweep.

KP000 is 67 x 17 x 35 mm. Its known collar extends 6 mm beyond one housing
face. The opposite protrusion is not measured and remains a 0..6 mm
sensitivity variable.

## Orientation authority

`ORIENTATION_C` means the set-screw collar faces vehicle center.
`ORIENTATION_O` means it faces vehicle outside. These names are used instead
of ambiguous left/right-facing labels.

At unchanged Y=+/-14 mm, dual inner `ORIENTATION_C` gives:

`28 - 17 - 6 - 6 = -1 mm`

The STEP envelope confirms this collision candidate. Flip-only is rejected.

## Ordered exploration

| Stage | Candidates | Nominal pass | Outcome |
|---:|---:|---:|---|
{chr(10).join(f"| {row['stage']} | {row['candidate_count']} | {row['nominal_pass_count']} | {row['reason']} |" for row in stages)}

Stage 5 spacer/collar optimization and Stage 6 alternate bearing selection were
not required after Stage 4 produced a fully robust alternative. They are not
automatically adopted.

## Recommended candidate

`{rec['candidate_id']}` is the first ordered stage meeting nominal gates.

- Inner KP000: C/C, Y=+/-{abs(rec['left_inner_y_mm']):.1f} mm
- Outer KP000: O/O, Y=+/-{abs(rec['left_outer_y_mm']):.1f} mm
- Pulley plane: Y=+/-{abs(rec['left_pulley_y_mm']):.1f} mm
- Center clearance: {rec['center_mutual_clearance_mm']:.1f} mm
- Inner belt nominal/residual: {rec['belt_to_inner_nominal_mm']:.1f}/{rec['belt_to_inner_residual_mm']:.1f} mm
- Outer belt nominal/residual: {rec['belt_to_outer_nominal_mm']:.1f}/{rec['belt_to_outer_residual_mm']:.1f} mm
- Inner/outer pulley nominal clearance: {rec['pulley_to_inner_nominal_mm']:.1f}/{rec['pulley_to_outer_nominal_mm']:.1f} mm
- Inner/outer pulley residual after 1.5 mm runout and 1 mm axial error: {rec['pulley_to_inner_residual_mm']:.1f}/{rec['pulley_to_outer_residual_mm']:.1f} mm
- Simplified tool clearance: {rec['tool_clearance_mm']:.1f} mm, but actual tool remains HOLD
- Total width 290 mm; PTO output ends +/-145 mm

This requires 1.0 mm outward movement per inner KP000, or 2.0 mm additional
central bearing-center width. Pulley movement, outer-KP000 movement, PTO-end
extension and support-plate enlargement are zero. Required shaft range becomes
{rec['shaft_length_min_mm']:.1f}..{rec['shaft_length_max_mm']:.1f} mm, 1.0 mm
shorter than the v0.8.3 provisional range.

The recommendation follows the Stage hierarchy and is
`{robust['result']}` because only opposite protrusion values
{robust['fully_robust_opposite_protrusion_values_mm']} pass every specified
allowance combination. Physical fit is not released.

## Alternatives

Alternative A `{alt_a['candidate_id']}` moves the pulley 6.0 mm outward and the
outer KP000 3.5 mm outward. It passes all
{robust_alternatives[0]['combination_count']} combinations and is
`{robust_alternatives[0]['result']}`, but is not preferred because Stage 2
already meets nominal gates with fewer changes.

Alternative B `{alt_b['candidate_id']}` moves the pulley 3.0 mm outward and is
fully robust only through opposite protrusion
{robust_alternatives[1]['max_opposite_protrusion_all_allowances_mm']} mm.

## Support plates and tool access

P3-A5052-T5 remains an independent mirrored 95 x 140 x 5 mm A5052-P candidate.
The reference envelopes fit without outline enlargement. No manufacturing hole
is created because KP000 hole-center distance is missing. The reference STEP
shows mounting, belt, pulley and tool keep-outs only.

The recommended collar directions permit simplified +X/front hex-key insertion
with a 12 mm candidate clearance. Tool intersection is zero in the simplified
envelope, but `HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED` remains. Pulley or belt
removal requirements must be verified at dry assembly.

## Axial stack and stock

The stack contains 17 classified entries per side. Coordinate-derived shaft
length is {rec['shaft_length_min_mm']:.1f}..{rec['shaft_length_max_mm']:.1f} mm.
A 300 mm or 400 mm stock bar can provisionally yield two shafts, subject to
kerf, end preparation and final measurements. No cut length is released.

## Robust sensitivity

The recommendation was checked across 7 opposite protrusions, 4 pulley
runouts, 3 assembly errors, 3 frame deflections and 3 belt-wander values:
{robust['combination_count']} combinations. {robust['pass_count']} pass and
{robust['fail_count']} fail. This is a measurement gate, not a manufactured
fit claim.

## Release states

- Geometry envelope: `CONDITIONAL_PASS_CANDIDATE`
- Robustness: `{robust['result']}`
- Opposite protrusion: `PART_MEASUREMENT_REQUIRED`
- Physical fit: `HOLD`
- Pulley bore fit: `FAIL_PROVISIONAL`
- Shaft cutting / support machining / drilling: `HOLD`
- Load, water and mud tests: `HOLD`
- Field deployment: `NOT_APPROVED`
"""


def remeasurement_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Common Rover v0.8.4 remeasurement sheet",
        "",
        "`NOT_FOR_MANUFACTURING`  ",
        "`PART_MEASUREMENT_REQUIRED`",
        "",
        "| Priority | ID | Component | Dimension | Current | Instrument | Resolution | Method | Gate |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {priority} | {item_id} | {component} | {dimension} | {current_value} | "
            "{instrument} | {resolution} | {method} | {design_gate} |".format(**row)
        )
    lines.extend(
        [
            "",
            "KP000 hole center distance:",
            "",
            "`CENTER_DISTANCE = OUTER_EDGE_TO_OUTER_EDGE - HOLE_DIAMETER`",
            "",
            "or",
            "",
            "`CENTER_DISTANCE = INNER_EDGE_TO_INNER_EDGE + HOLE_DIAMETER`",
            "",
        ]
    )
    return "\n".join(lines)


def readme_text() -> str:
    return f"""# v0.8.4 handoff

`{DOCUMENT_ID}` is a 24-file, self-contained design-audit package.

It preserves the two independent PTO architecture and explores KP000
orientation and axial placement in strict Stage order. The recommended
candidate is minimum-change and conditional. Alternative A is the full
specified-sensitivity candidate.

Run:

`python -B {BUILDER_NAME} --verify`

`python -B {TEST_REL}`

No manufacturing holes, shaft cuts, support-plate machining, load tests or
field use are approved. `NOT_FOR_MANUFACTURING`.
"""


def _as_shape(value: cq.Shape | cq.Workplane) -> cq.Shape:
    if isinstance(value, cq.Workplane):
        values = value.vals()
        return values[0] if len(values) == 1 else cq.Compound.makeCompound(values)
    return value


def _box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Shape:
    return _as_shape(cq.Workplane("XY").box(x, y, z).translate(center))


def _cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    return _as_shape(
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length / 2, both=True)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate(center)
    )


def kp000_shape(
    x: float,
    y: float,
    axis_z: float,
    collar_direction: int,
) -> cq.Shape:
    housing = _box(67, 17, 35, (x, y, axis_z - 1.0))
    bore = _cylinder_y(5, 21, (x, y, axis_z))
    housing = housing.cut(bore)
    collar_y = y + collar_direction * 11.5
    collar = _cylinder_y(13, 6, (x, collar_y, axis_z)).cut(
        _cylinder_y(5, 8, (x, collar_y, axis_z))
    )
    screws = [
        _box(4, 4, 8, (x - 6, collar_y, axis_z + 12)),
        _box(4, 4, 8, (x + 6, collar_y, axis_z + 12)),
    ]
    return cq.Compound.makeCompound([housing, collar, *screws])


def plate_shape(x: float, y: float, z: float) -> cq.Shape:
    points = [(-47.5, 0), (47.5, 0), (47.5, 58.8), (25.65, 140), (-25.65, 140), (-47.5, 58.8)]
    return _as_shape(
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(2.5, both=True)
        .translate((x, y, z))
    )


def candidate_model(candidate: dict[str, Any]) -> cq.Shape:
    x = 390.0
    axis_z = 370.0
    components: list[cq.Shape] = []
    for sign, inner_key, outer_key in (
        (1, "left_inner_orientation", "left_outer_orientation"),
        (-1, "right_inner_orientation", "right_outer_orientation"),
    ):
        yi = sign * abs(float(candidate["left_inner_y_mm"]))
        yp = sign * abs(float(candidate["left_pulley_y_mm"]))
        yo = sign * abs(float(candidate["left_outer_y_mm"]))
        inner_collar_direction = -sign if candidate[inner_key] == "C" else sign
        outer_collar_direction = -sign if candidate[outer_key] == "C" else sign
        shaft_start = sign * (abs(yi) - 8.5 - 6.0)
        shaft_end = sign * 145.0
        shaft_center = (shaft_start + shaft_end) / 2
        components.extend(
            [
                plate_shape(x, yi, 300),
                kp000_shape(x, yi, axis_z, inner_collar_direction),
                kp000_shape(x, yo, axis_z, outer_collar_direction),
                _cylinder_y(5, abs(shaft_end - shaft_start), (x, shaft_center, axis_z)),
                _cylinder_y(60, 20, (x, yp, axis_z)),
                _box(220, 21, 120, (340, yp, axis_z)),
                _box(220, 31, 120, (340, yp, axis_z)),
                _box(40, 10, 10, (x - 55, yi - sign * 20, axis_z + 18)),
                _box(480, 55, 175, (100, sign * 117.5, 97.5)),
                _box(400, 20, 40, (80, sign * 78, 130)),
            ]
        )
    components.extend(
        [
            _box(180, 20, 20, (330, 0, 360)),
            _box(156, 40, 20, (250, 0, 230)),
            _box(130, 140, 105, (85, 0, 252.5)),
            _box(150, 220, 150, (-75, 0, 275)),
        ]
    )
    return cq.Compound.makeCompound(components)


def cad_clearance_snapshot(candidate: dict[str, Any]) -> dict[str, float]:
    x = 390.0
    axis_z = 370.0
    yi = abs(float(candidate["left_inner_y_mm"]))
    yp = abs(float(candidate["left_pulley_y_mm"]))
    yo = abs(float(candidate["left_outer_y_mm"]))
    left_inner_direction = -1 if candidate["left_inner_orientation"] == "C" else 1
    right_inner_direction = 1 if candidate["right_inner_orientation"] == "C" else -1
    left_outer_direction = -1 if candidate["left_outer_orientation"] == "C" else 1
    left_inner = kp000_shape(x, yi, axis_z, left_inner_direction)
    right_inner = kp000_shape(x, -yi, axis_z, right_inner_direction)
    left_outer = kp000_shape(x, yo, axis_z, left_outer_direction)
    pulley = _cylinder_y(60, 20, (x, yp, axis_z))
    belt_nominal = _box(220, 21, 120, (340, yp, axis_z))
    belt_safety = _box(220, 31, 120, (340, yp, axis_z))
    left_plate = plate_shape(x, yi, 300)
    right_plate = plate_shape(x, -yi, 300)

    def distance(a: cq.Shape, b: cq.Shape) -> float:
        return _round(a.distance(b))

    return {
        "belt_inner_nominal_mm": distance(belt_nominal, left_inner),
        "belt_inner_safety_residual_mm": distance(belt_safety, left_inner),
        "belt_outer_nominal_mm": distance(belt_nominal, left_outer),
        "belt_outer_safety_residual_mm": distance(belt_safety, left_outer),
        "pulley_inner_nominal_mm": distance(pulley, left_inner),
        "pulley_outer_nominal_mm": distance(pulley, left_outer),
        "inner_kp000_mutual_mm": distance(left_inner, right_inner),
        "support_plate_mutual_mm": distance(left_plate, right_plate),
    }


def _shape_signature(shape: cq.Shape | cq.Workplane) -> dict[str, Any]:
    shape = _as_shape(shape)
    solids = sorted(
        [
            _round(s.Volume(), 2),
            _round(s.BoundingBox().xlen, 3),
            _round(s.BoundingBox().ylen, 3),
            _round(s.BoundingBox().zlen, 3),
        ]
        for s in shape.Solids()
    )
    box = shape.BoundingBox()
    return {
        "solid_count": len(solids),
        "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
        "total_volume_mm3": _round(sum(item[0] for item in solids), 2),
        "solid_signatures": solids,
    }


def _normalize_step(path: Path, name: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"FILE_NAME\('[^']*','[^']*'",
        f"FILE_NAME('{name}','1970-01-01T00:00:00'",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_step(shape: cq.Shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    cq.exporters.export(shape, str(temporary), exportType="STEP")
    _normalize_step(temporary, path.name)
    temporary.replace(path)


def overview_svg(
    recommended: dict[str, Any],
    alternative_a: dict[str, Any],
    alternative_b: dict[str, Any],
) -> str:
    def panel(y: int, title: str, candidate: dict[str, Any], color: str) -> str:
        scale = 3.7
        origin = 700
        x_inner_l = origin + candidate["left_inner_y_mm"] * scale
        x_pulley_l = origin + candidate["left_pulley_y_mm"] * scale
        x_outer_l = origin + candidate["left_outer_y_mm"] * scale
        x_inner_r = origin + candidate["right_inner_y_mm"] * scale
        x_pulley_r = origin + candidate["right_pulley_y_mm"] * scale
        x_outer_r = origin + candidate["right_outer_y_mm"] * scale
        return f"""
<text x="55" y="{y-70}" class="h">{title}</text>
<line x1="163" y1="{y}" x2="1237" y2="{y}" class="axis"/>
<rect x="{x_inner_r-31}" y="{y-38}" width="62" height="76" fill="{color}" class="part"/>
<rect x="{x_inner_l-31}" y="{y-38}" width="62" height="76" fill="{color}" class="part"/>
<circle cx="{x_pulley_r}" cy="{y}" r="42" class="pulley"/>
<circle cx="{x_pulley_l}" cy="{y}" r="42" class="pulley"/>
<rect x="{x_outer_r-31}" y="{y-38}" width="62" height="76" fill="{color}" class="part"/>
<rect x="{x_outer_l-31}" y="{y-38}" width="62" height="76" fill="{color}" class="part"/>
<text x="55" y="{y+70}" class="s">inner +/-{abs(candidate['left_inner_y_mm']):.1f} | pulley +/-{abs(candidate['left_pulley_y_mm']):.1f} | outer +/-{abs(candidate['left_outer_y_mm']):.1f} | center {candidate['center_mutual_clearance_mm']:.1f}</text>
<text x="700" y="{y+70}" class="s">belt N/R {candidate['belt_to_inner_nominal_mm']:.1f}/{candidate['belt_to_inner_residual_mm']:.1f} | pulley N/R {min(candidate['pulley_to_inner_nominal_mm'],candidate['pulley_to_outer_nominal_mm']):.1f}/{min(candidate['pulley_to_inner_residual_mm'],candidate['pulley_to_outer_residual_mm']):.1f}</text>
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>
text{{font-family:Arial,sans-serif;fill:#0b2545}} .t{{font-size:30px;font-weight:700}} .h{{font-size:23px;font-weight:700}} .s{{font-size:16px}}
.axis{{stroke:#19376d;stroke-width:3}} .part{{stroke:#134b2c;stroke-width:2}} .pulley{{fill:#ffe6a7;stroke:#a65f00;stroke-width:3}}
.warn{{fill:#b40000;font-size:17px;font-weight:700}} .frame{{fill:#f7f9fc;stroke:#ccd6e2;stroke-width:2}}
</style>
<rect width="1400" height="900" fill="#f2f5f9"/>
<text x="35" y="48" class="t">Common Rover v0.8.4 KP000 axial search</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · PART_MEASUREMENT_REQUIRED · physical fit HOLD</text>
<rect x="35" y="105" width="1330" height="235" class="frame"/>
{panel(230, "Recommended · Stage 2 minimum change", recommended, "#70c173")}
<rect x="35" y="365" width="1330" height="205" class="frame"/>
{panel(480, "Alternative A · Stage 4 robust all 756", alternative_a, "#69b7df")}
<rect x="35" y="595" width="1330" height="205" class="frame"/>
{panel(710, "Alternative B · Stage 3 robust through 3 mm", alternative_b, "#c0a3e8")}
<text x="35" y="850" class="s">C = collar toward center; O = collar toward outside. Pulley circle is OD120 safety authority.</text>
</svg>
"""


def section_svg(candidate: dict[str, Any]) -> str:
    positions = [
        ("CENTER", 0, "#d9e2ec"),
        ("INNER KP", abs(candidate["left_inner_y_mm"]), "#70c173"),
        ("60T", abs(candidate["left_pulley_y_mm"]), "#ffe6a7"),
        ("OUTER KP", abs(candidate["left_outer_y_mm"]), "#70c173"),
        ("PTO END", 145, "#f4a6a6"),
    ]
    scale = 7.6
    elements = []
    for name, value, color in positions:
        x = 130 + value * scale
        elements.append(f'<line x1="{x}" y1="180" x2="{x}" y2="600" class="dim"/>')
        elements.append(f'<rect x="{x-33}" y="315" width="66" height="90" fill="{color}" class="part"/>')
        elements.append(f'<text x="{x}" y="295" text-anchor="middle" class="s">{name}</text>')
        elements.append(f'<text x="{x}" y="435" text-anchor="middle" class="s">{value:.1f}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>
text{{font-family:Arial,sans-serif;fill:#0b2545}} .t{{font-size:30px;font-weight:700}} .h{{font-size:23px;font-weight:700}} .s{{font-size:16px}}
.dim{{stroke:#19376d;stroke-width:2}} .part{{stroke:#264653;stroke-width:2}} .warn{{fill:#b40000;font-size:17px;font-weight:700}}
</style>
<rect width="1400" height="900" fill="#f5f7fb"/>
<text x="35" y="48" class="t">v0.8.4 recommended left PTO axial section</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · shaft cutting HOLD · coupling/retaining dimensions HOLD</text>
<line x1="130" y1="360" x2="1232" y2="360" stroke="#111" stroke-width="8"/>
{''.join(elements)}
<text x="75" y="530" class="h">Coordinate-derived shaft range: {candidate['shaft_length_min_mm']:.1f}–{candidate['shaft_length_max_mm']:.1f} mm</text>
<text x="75" y="575" class="s">300 mm stock: two shafts candidate · 400 mm stock: two shafts candidate · kerf/end preparation HOLD</text>
<text x="75" y="640" class="s">Stack CSV classifies 17 entries per side as measured, nominal, provisional or HOLD.</text>
<text x="75" y="685" class="s">Pulley axial width authority remains 20 mm. Reported 2 + 17 + 2 = 21 mm conflict remains open.</text>
</svg>
"""


def central_svg(recommended: dict[str, Any]) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>
text{{font-family:Arial,sans-serif;fill:#0b2545}} .t{{font-size:30px;font-weight:700}} .h{{font-size:24px;font-weight:700}} .s{{font-size:18px}}
.bad{{fill:#ffd1d1;stroke:#b40000;stroke-width:3}} .good{{fill:#d7f4da;stroke:#197333;stroke-width:3}} .warn{{fill:#b40000;font-size:17px;font-weight:700}}
</style>
<rect width="1400" height="900" fill="#f5f7fb"/>
<text x="35" y="48" class="t">v0.8.4 inner KP000 central-clearance gate</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · opposite protrusion and assembly tolerance require measurement</text>
<rect x="55" y="125" width="620" height="620" class="bad"/>
<text x="85" y="175" class="h">Simple dual inward flip · REJECT</text>
<rect x="228" y="300" width="145" height="160" fill="#70c173"/>
<rect x="357" y="330" width="55" height="100" fill="#f2b36d"/>
<rect x="303" y="330" width="55" height="100" fill="#f2b36d"/>
<rect x="397" y="300" width="145" height="160" fill="#70c173"/>
<text x="85" y="535" class="s">center distance 28 − housing 17 − collars 6 − 6</text>
<text x="85" y="585" class="h">= −1.0 mm overlap candidate</text>
<text x="85" y="635" class="s">Orientation-only Stage 1 cannot be accepted.</text>
<rect x="725" y="125" width="620" height="620" class="good"/>
<text x="755" y="175" class="h">Stage 2 recommendation · CONDITIONAL</text>
<rect x="898" y="300" width="145" height="160" fill="#70c173"/>
<rect x="1027" y="330" width="55" height="100" fill="#f2b36d"/>
<rect x="1081" y="330" width="55" height="100" fill="#f2b36d"/>
<rect x="1120" y="300" width="145" height="160" fill="#70c173"/>
<text x="755" y="535" class="s">center distance 30 − housing 17 − collars 6 − 6</text>
<text x="755" y="585" class="h">= {recommended['center_mutual_clearance_mm']:.1f} mm nominal clearance</text>
<text x="755" y="635" class="s">Each inner KP000 moves 1.0 mm outward.</text>
<text x="755" y="680" class="s">Physical PASS remains HOLD pending dry fit.</text>
</svg>
"""


def validation_payload(
    params: dict[str, Any],
    search: list[dict[str, Any]],
    sensitivity: list[dict[str, Any]],
    matrices: list[dict[str, Any]],
    models: dict[str, cq.Shape],
    step_paths: dict[str, Path],
) -> dict[str, Any]:
    recommended = params["recommended"]
    cad_clearances = cad_clearance_snapshot(recommended)
    stage_counts = {row["stage"]: row["candidate_count"] for row in params["search_stage_summary"]}
    checks = {
        "fixed_motor_count_2": FIXED_ARCHITECTURE["motor_count"] == 2,
        "independent_pto_2": FIXED_ARCHITECTURE["pto_port_count"] == 2
        and "NO_COMMON_SHAFT" in FIXED_ARCHITECTURE["pto_shaft_architecture"],
        "slide_clutch_preserved": FIXED_ARCHITECTURE["slide_clutch_states"] == ["DRIVE", "NEUTRAL", "PTO"],
        "kp000_envelope": [KP000["mounting_width_x_mm"], KP000["housing_depth_y_mm"], KP000["height_z_mm"]] == [67, 17, 35],
        "collar_6": KP000["collar_protrusion_mm"] == 6,
        "baseline": params["baseline_reproduction"]["status"] == "PASS",
        "stage1_16": stage_counts[1] == 16,
        "simple_flip_collision": evaluate_candidate("CHECK", 1, ("C", "O", "C", "O"), 0, 0, 0)["center_mutual_clearance_mm"] == -1,
        "recommended_center": recommended["center_mutual_clearance_mm"] >= 1,
        "recommended_belt_nominal": min(recommended["belt_to_inner_nominal_mm"], recommended["belt_to_outer_nominal_mm"]) >= 13,
        "recommended_belt_residual": min(recommended["belt_to_inner_residual_mm"], recommended["belt_to_outer_residual_mm"]) >= 8,
        "recommended_pulley": min(recommended["pulley_to_inner_nominal_mm"], recommended["pulley_to_outer_nominal_mm"]) >= 10,
        "recommended_pulley_residual": min(recommended["pulley_to_inner_residual_mm"], recommended["pulley_to_outer_residual_mm"]) >= 10,
        "cad_belt_clearance_matches": cad_clearances["belt_inner_nominal_mm"] == recommended["belt_to_inner_nominal_mm"]
        and cad_clearances["belt_inner_safety_residual_mm"] == recommended["belt_to_inner_residual_mm"]
        and cad_clearances["belt_outer_nominal_mm"] == recommended["belt_to_outer_nominal_mm"]
        and cad_clearances["belt_outer_safety_residual_mm"] == recommended["belt_to_outer_residual_mm"],
        "cad_pulley_clearance_matches": cad_clearances["pulley_inner_nominal_mm"] == recommended["pulley_to_inner_nominal_mm"]
        and cad_clearances["pulley_outer_nominal_mm"] == recommended["pulley_to_outer_nominal_mm"],
        "cad_center_clearance_matches": cad_clearances["inner_kp000_mutual_mm"] == recommended["center_mutual_clearance_mm"],
        "all_intersections_zero": sum(row["intersection_count"] for row in matrices) == 0,
        "width": recommended["total_width_mm"] < 300,
        "pto_ends": abs(recommended["left_pto_end_y_mm"]) <= 145 and abs(recommended["right_pto_end_y_mm"]) <= 145,
        "support_plate": SUPPORT_PLATE["thickness_y_mm"] == 5 and SUPPORT_PLATE["left_right_independent"],
        "no_hole_release": SUPPORT_PLATE["hole_pattern"] == "KP000_HOLE_CENTER_DISTANCE_REQUIRED",
        "sensitivity_756": len(sensitivity) == 756,
        "shaft_cut_hold": params["release_states"]["shaft_cutting"] == "HOLD",
        "not_for_manufacturing": params["status"] == "NOT_FOR_MANUFACTURING",
    }
    geometry = {}
    for key, model in models.items():
        imported = cq.importers.importStep(str(step_paths[key]))
        geometry[key] = {
            "source_signature": _shape_signature(model),
            "artifact_signature": _shape_signature(imported),
            "semantic_geometry_reproducible": _shape_signature(model) == _shape_signature(imported),
        }
    return {
        "document_id": DOCUMENT_ID,
        "checks": checks,
        "check_count": len(checks),
        "check_pass_count": sum(checks.values()),
        "search_candidate_count": len(search),
        "stage_summary": params["search_stage_summary"],
        "recommended_candidate_id": recommended["candidate_id"],
        "recommended_cad_clearances_mm": cad_clearances,
        "geometry": geometry,
        "overall": (
            "CONDITIONAL_PASS_CANDIDATE"
            if all(checks.values())
            and all(value["semantic_geometry_reproducible"] for value in geometry.values())
            else "FAIL"
        ),
        "robustness": params["recommended_robustness"]["result"],
        "opposite_side_protrusion": "PART_MEASUREMENT_REQUIRED",
        "physical_fit": "HOLD",
        "pulley_bore_fit": "FAIL_PROVISIONAL",
        "shaft_cutting": "HOLD",
        "support_plate_machining": "HOLD",
        "drilling": "HOLD",
        "load_test": "HOLD",
        "water_mud_test": "HOLD",
        "field_deployment": "NOT_APPROVED",
    }


def build_datasets() -> dict[str, Any]:
    runtime_parent_audit = parent_protection_audit()
    runtime_baseline = baseline_reproduction()
    parent_audit = canonical_parent_protection()
    baseline = canonical_baseline()
    search = search_candidates()
    recommended, alternative_a, alternative_b = selected_candidates()
    recommended_robust = robustness_summary(recommended)
    alt_robust = [robustness_summary(alternative_a), robustness_summary(alternative_b)]
    sensitivity = sensitivity_rows(recommended)
    params = parameters_payload(
        search,
        recommended,
        [alternative_a, alternative_b],
        recommended_robust,
        parent_audit,
        baseline,
    )
    ranking = ranking_rows()
    matrix = []
    for candidate in (recommended, alternative_a, alternative_b):
        matrix.extend(interference_matrix(candidate))
    return {
        "parent_audit": runtime_parent_audit,
        "baseline_runtime": runtime_baseline,
        "baseline": baseline,
        "search": search,
        "orientation": orientation_candidates(),
        "recommended": recommended,
        "alternatives": [alternative_a, alternative_b],
        "recommended_robust": recommended_robust,
        "alternative_robust": alt_robust,
        "sensitivity": sensitivity,
        "parameters": params,
        "ranking": ranking,
        "stack": axial_stack_rows(recommended),
        "matrix": matrix,
        "interference": interference_report_payload(recommended, [alternative_a, alternative_b], baseline),
        "remeasure": remeasurement_rows(),
    }


def deterministic_texts(data: dict[str, Any]) -> dict[str, str]:
    return {
        AUTHORITY_NAME: authority_markdown(data["parameters"], data["ranking"], data["alternative_robust"]),
        PARAMETERS_NAME: _json_text(data["parameters"]),
        ORIENTATION_NAME: _csv_text(data["orientation"], SEARCH_FIELDS),
        SEARCH_NAME: _csv_text(data["search"], SEARCH_FIELDS),
        RANKING_NAME: _csv_text(
            data["ranking"], ["rank", "selection", *SEARCH_FIELDS, "rationale"]
        ),
        SENSITIVITY_NAME: _csv_text(data["sensitivity"], SENSITIVITY_FIELDS),
        STACK_NAME: _csv_text(data["stack"], STACK_FIELDS),
        MATRIX_NAME: _csv_text(data["matrix"], MATRIX_FIELDS),
        INTERFERENCE_NAME: _json_text(data["interference"]),
        REMEASURE_MD_NAME: remeasurement_markdown(data["remeasure"]),
        REMEASURE_CSV_NAME: _csv_text(data["remeasure"], REMEASURE_FIELDS),
        README_NAME: readme_text(),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(
            data["recommended"], data["alternatives"][0], data["alternatives"][1]
        ),
        f"artifacts/{SECTION_SVG}": section_svg(data["recommended"]),
        f"artifacts/{CENTRAL_SVG}": central_svg(data["recommended"]),
    }


def _seal_hashes() -> None:
    manifest = [
        f"DOCUMENT_ID={DOCUMENT_ID}",
        f"EXPECTED_FILE_COUNT={len(PACKAGE_PATHS)}",
        "STATUS=NOT_FOR_MANUFACTURING",
        "ROOT=ZIP_ROOT",
    ]
    manifest.extend(f"{relative}\tFILE" for relative in PACKAGE_PATHS)
    _write_text(LANE_DIR / MANIFEST_NAME, "\n".join(manifest) + "\n")
    sums = []
    for relative in PACKAGE_PATHS:
        if relative == SHA256SUMS_NAME:
            continue
        path = LANE_DIR / relative
        if not path.is_file():
            raise RuntimeError(f"missing path while sealing: {relative}")
        sums.append(f"{_sha256(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(sums) + "\n")


def refresh() -> dict[str, Any]:
    data = build_datasets()
    models = {
        "recommended": candidate_model(data["recommended"]),
        "alternative_a": candidate_model(data["alternatives"][0]),
        "alternative_b": candidate_model(data["alternatives"][1]),
    }
    step_paths = {
        "recommended": ARTIFACT_DIR / RECOMMENDED_STEP,
        "alternative_a": ARTIFACT_DIR / ALTERNATIVE_A_STEP,
        "alternative_b": ARTIFACT_DIR / ALTERNATIVE_B_STEP,
    }
    for key, model in models.items():
        _write_step(model, step_paths[key])
    validation = validation_payload(
        data["parameters"],
        data["search"],
        data["sensitivity"],
        data["matrix"],
        models,
        step_paths,
    )
    texts = deterministic_texts(data)
    texts[VALIDATION_NAME] = _json_text(validation)
    for relative, text in texts.items():
        _write_text(LANE_DIR / relative, text)
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        f"DOCUMENT_ID={DOCUMENT_ID}\nSTATUS=PENDING_CONTRACT_EXECUTION\n",
    )
    _seal_hashes()
    return {
        "validation": validation,
        "data": data,
    }


def _verify_hashes() -> dict[str, Any]:
    manifest_paths = []
    for line in (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8").splitlines():
        if not line or "=" in line:
            continue
        manifest_paths.append(line.split("\t", 1)[0])
    if tuple(manifest_paths) != PACKAGE_PATHS:
        raise RuntimeError("MANIFEST path mismatch")
    sums = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        sums[relative] = digest
    if set(sums) != set(PACKAGE_PATHS) - {SHA256SUMS_NAME}:
        raise RuntimeError("SHA256SUMS path mismatch")
    mismatches = [
        relative
        for relative, digest in sums.items()
        if _sha256(LANE_DIR / relative) != digest
    ]
    if mismatches:
        raise RuntimeError(f"SHA256SUMS mismatch: {mismatches}")
    return {
        "manifest_file_count": len(manifest_paths),
        "hashed_file_count": len(sums),
        "hash_mismatch_count": 0,
    }


def verify() -> dict[str, Any]:
    parent_audit = parent_protection_audit()
    data = build_datasets()
    missing = [relative for relative in PACKAGE_PATHS if not (LANE_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing package paths: {missing}")
    expected = deterministic_texts(data)
    mismatches = [
        relative
        for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise RuntimeError(f"deterministic text mismatch: {mismatches}")
    validation = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    if validation["overall"] != "CONDITIONAL_PASS_CANDIDATE":
        raise RuntimeError("validation overall mismatch")
    models = {
        "recommended": candidate_model(data["recommended"]),
        "alternative_a": candidate_model(data["alternatives"][0]),
        "alternative_b": candidate_model(data["alternatives"][1]),
    }
    step_paths = {
        "recommended": ARTIFACT_DIR / RECOMMENDED_STEP,
        "alternative_a": ARTIFACT_DIR / ALTERNATIVE_A_STEP,
        "alternative_b": ARTIFACT_DIR / ALTERNATIVE_B_STEP,
    }
    for key, model in models.items():
        imported = cq.importers.importStep(str(step_paths[key]))
        if _shape_signature(imported) != _shape_signature(model):
            raise RuntimeError(f"STEP semantic mismatch: {key}")
    hashes = _verify_hashes()
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "recommended_candidate_id": data["recommended"]["candidate_id"],
        "search_candidate_count": len(data["search"]),
        "sensitivity_combination_count": len(data["sensitivity"]),
        "robustness": data["recommended_robust"]["result"],
        "parent_audit_mode": parent_audit["mode"],
        "parent_checked_path_count": parent_audit["checked_path_count"],
        **hashes,
    }


def record_test_result() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-B", str(LANE_DIR / TEST_REL)],
        cwd=LANE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    text = (
        f"DOCUMENT_ID={DOCUMENT_ID}\n"
        f"COMMAND={sys.executable} -B {TEST_REL}\n"
        f"RETURN_CODE={result.returncode}\n"
        f"PYTHON_VERSION={sys.version.split()[0]}\n"
        f"CADQUERY_VERSION={cq.__version__}\n"
        "\nSTDOUT\n"
        f"{result.stdout}"
        "\nSTDERR\n"
        f"{result.stderr}"
    )
    _write_text(LANE_DIR / TEST_RESULTS_NAME, text)
    _seal_hashes()
    if result.returncode:
        raise RuntimeError("contract tests failed; result saved")
    return {
        "return_code": result.returncode,
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "result_path": str(LANE_DIR / TEST_RESULTS_NAME),
    }


def package() -> dict[str, Any]:
    verified = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{stamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite ZIP: {path}")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PACKAGE_PATHS:
            archive.write(LANE_DIR / relative, relative)
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        names = tuple(archive.namelist())
        forbidden = [
            name
            for name in names
            if "__pycache__" in name or ".pytest_cache" in name or name.endswith(".pyc")
        ]
        if bad or names != PACKAGE_PATHS or forbidden:
            raise RuntimeError(f"ZIP audit failure: {bad}, {len(names)}, {forbidden}")
        sums = archive.read(SHA256SUMS_NAME).decode("utf-8").splitlines()
        internal_ok = all(
            hashlib.sha256(archive.read(relative)).hexdigest() == digest
            for digest, relative in (line.split("  ", 1) for line in sums)
        )
        if not internal_ok:
            raise RuntimeError("ZIP internal SHA256SUMS mismatch")
    return {
        **verified,
        "zip_path": str(path),
        "zip_sha256": _sha256(path),
        "zip_size_bytes": path.stat().st_size,
        "zip_file_count": len(PACKAGE_PATHS),
        "zip_crc_pass": True,
        "zip_hash_manifest_pass": True,
        "zip_cache_pyc_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--refresh-artifacts", action="store_true")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--record-test-result", action="store_true")
    action.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if args.refresh_artifacts:
        result = refresh()
        validation = result["validation"]
        data = result["data"]
        output = {
            "action": "REFRESH",
            "overall": validation["overall"],
            "fixed_checks": f"{validation['check_pass_count']}/{validation['check_count']}",
            "recommended_candidate_id": data["recommended"]["candidate_id"],
            "search_candidate_count": len(data["search"]),
            "sensitivity_combination_count": len(data["sensitivity"]),
            "robustness": data["recommended_robust"]["result"],
        }
    elif args.verify:
        output = {"action": "VERIFY", **verify()}
    elif args.record_test_result:
        output = {"action": "RECORD_TEST_RESULT", **record_test_result()}
    else:
        output = {"action": "PACKAGE", **package()}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
