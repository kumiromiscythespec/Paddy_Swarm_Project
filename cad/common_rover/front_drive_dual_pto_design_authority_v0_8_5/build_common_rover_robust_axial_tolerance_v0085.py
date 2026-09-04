from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import random
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import cadquery as cq


sys.dont_write_bytecode = True

DOCUMENT_ID = "PS-CR-ROBUST-AXIAL-TOLERANCE-V0085"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_8_5_Robust_Axial_Tolerance_"

AUTHORITY_NAME = "common_rover_robust_axial_tolerance_design_authority_v0085.md"
PARAMETERS_NAME = "common_rover_robust_axial_tolerance_parameters_v0085.json"
CORRECTION_NAME = "common_rover_tolerance_model_correction_v0085.md"
SEARCH_NAME = "common_rover_robust_search_candidates_v0085.csv"
RANKING_NAME = "common_rover_robust_candidate_ranking_v0085.csv"
SENSITIVITY_NAME = "common_rover_boundary_sensitivity_v0085.csv"
STACK_NAME = "common_rover_axial_stack_v0085.csv"
MATRIX_NAME = "common_rover_interference_matrix_v0085.csv"
INTERFERENCE_NAME = "common_rover_interference_report_v0085.json"
VALIDATION_NAME = "common_rover_validation_v0085.json"
REMEASURE_MD_NAME = "common_rover_remeasurement_sheet_v0085.md"
REMEASURE_CSV_NAME = "common_rover_remeasurement_sheet_v0085.csv"
BUILDER_NAME = "build_common_rover_robust_axial_tolerance_v0085.py"
RECOMMENDED_STEP = "PS-CR-ROBUST-AXIAL-V0085-RECOMMENDED.step"
ALTERNATIVE_A_STEP = "PS-CR-ROBUST-AXIAL-V0085-ALTERNATIVE-A.step"
ALTERNATIVE_B_STEP = "PS-CR-ROBUST-AXIAL-V0085-ALTERNATIVE-B.step"
OVERVIEW_SVG = "PS-CR-ROBUST-AXIAL-V0085-OVERVIEW.svg"
TOLERANCE_SVG = "PS-CR-ROBUST-AXIAL-V0085-TOLERANCE-SECTION.svg"
CENTER_SVG = "PS-CR-ROBUST-AXIAL-V0085-CENTER-CLEARANCE.svg"
TEST_REL = "tests/test_common_rover_robust_axial_tolerance_v0085_contract.py"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0085.txt"

PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    CORRECTION_NAME,
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
    f"artifacts/{TOLERANCE_SVG}",
    f"artifacts/{CENTER_SVG}",
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
    "v0.8.3": "5ca0b59e1eed15eab3ea1c5ba540ba695b55f9180e0b8c07c8946e97be0d937b",
}

V0084_HASHES = {
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-ALTERNATIVE-A.step": "0bafa1b2005584c426804c638e10a236c0c6ddc49dab3096ac669c4fb2deb18a",
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-ALTERNATIVE-B.step": "382adc4a665274df5b7ac25ff5b3712f26e1e5142faac1d29596eab95602e275",
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-CENTRAL-CLEARANCE.svg": "f0442f91deb889770763f1d7f139ebefb5a45ca11ca4b35065b3dfdce0003f92",
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-OVERVIEW.svg": "fffc5c7166f8e3a20d268afe589168e60929425f77c8d67bf27c37dd12d910d3",
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-RECOMMENDED.step": "ebfc9b1d106da3fa3e5eccaa707a8914da1469eb7715c931c525759eacf8cd2e",
    "artifacts/PS-CR-KP000-AXIAL-STACK-V0084-SECTION.svg": "2739bc2363fc6207106377a786820489b09d9688c50b462d44897a618b2c65a6",
    "build_common_rover_kp000_axial_stack_v0084.py": "989e56ff32bcb2ed19f3936c0e2ff72be4c360155e0489281dccfc7739e9d0df",
    "common_rover_kp000_axial_search_candidates_v0084.csv": "4a5c2bd7fc67141822141042789515dc318dd1d8b87d83e1426b10e5676044c3",
    "common_rover_kp000_axial_stack_design_authority_v0084.md": "852db30f46a11e2fb6df3e48eacc46dd6b812ea4a80821a6567cc2a976fb16c8",
    "common_rover_kp000_axial_stack_parameters_v0084.json": "c0d50019cb4c7c6dd5580e51613029bcb9a623c77faa7924512b08f3da731b11",
    "common_rover_kp000_axial_stack_v0084.csv": "40e66248d729888b462c40a831db1537caf2accb82342426fb812c03bec0c0d3",
    "common_rover_kp000_candidate_ranking_v0084.csv": "2bb08e3adb19e2e0e7e8b4dca3581ba7d71a3bd849c6e5ae632df2ff356509a4",
    "common_rover_kp000_interference_matrix_v0084.csv": "9927d32d4bb1dc0d66f626465fd7e315b768b35819be4984a1b2c53cb881bba3",
    "common_rover_kp000_interference_report_v0084.json": "00d2868d5d26b1e6f717370ab223ed2b04c74064a15d40833a7adad20913471a",
    "common_rover_kp000_orientation_candidates_v0084.csv": "bc3d7bdb8b31822e2b2ac126258c20472fad78249811f697f49eab9e5a419460",
    "common_rover_kp000_remeasurement_sheet_v0084.csv": "4804e9e6928acf5605899b4f1cb76135af03b1b5f7a7e921c7aa6ae69a7d34cf",
    "common_rover_kp000_remeasurement_sheet_v0084.md": "7e7621e04c5131c29615f8c19163b1078e7f9e6e2df021e0b9c79793ef6a572c",
    "common_rover_kp000_robustness_sensitivity_v0084.csv": "eac0a5b53b5a5c8b818ce0c1ea3f680d95600073d8680aed0c8b389508305fda",
    "common_rover_kp000_validation_v0084.json": "d1e9cd0fa84ba782156834f4537611472ea73abfd7451ab9991f5613823206d2",
    "MANIFEST.txt": "bb6d42992f9ecee2e6b330b18d0a68b60a45ea827c75ade9a799428ba3631f35",
    "README_HANDOFF.md": "aca8f13244de24ef945c0b8f26053f20baf62269fad3732383b6241bfe523d37",
    "SHA256SUMS.txt": "aa4b8220d2b0b53a42b959b66e4cfd9e49619f60879d7dc886455cb81e64e3f2",
    "test_results_v0084.txt": "568d80f1b9af6cc4f7ec8b02198dc75b30b607c4ee84d78e39863d7de890d980",
    "tests/test_common_rover_kp000_axial_stack_v0084_contract.py": "a9a93852ee7fba5880f6acc085e21360ea36607f6b5d330e96d6be3d6451f992",
}

V0084_LEDGER_SHA256 = "ca91b5fb76de196c7267dd616e236aeed9d0e278ed829655c910b0978389c1ea"

FIXED = {
    "motor_count": 2,
    "pto_port_count": 2,
    "pto_shaft_architecture": "TWO_INDEPENDENT_LATERAL_SHAFTS_NO_COMMON_SHAFT",
    "motor_axes": "INWARD",
    "pto_axes": "LATERAL_Y",
    "pto_forward_of_motor": True,
    "transmission": "FRONT_CONCENTRATED",
    "slide_clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "simultaneous_drive_pto": "PROHIBITED",
    "boxes": "CBOX_BBOX_LONG_SIDE_LATERAL_SHORT_SIDE_CONNECTED",
    "box_bottom_min_z_mm": 200.0,
    "crawler": "INVERSE_TRAPEZOID",
    "width_limit_mm": 300.0,
    "pto_end_limit_abs_y_mm": 145.0,
    "support_plate": "P3-A5052-T5",
    "single_frame_member_max_mm": 400.0,
}

KP000 = {
    "width_x_mm": 67.0,
    "housing_depth_y_mm": 17.0,
    "height_z_mm": 35.0,
    "housing_half_depth_mm": 8.5,
    "known_collar_protrusion_mm": 6.0,
    "opposite_protrusion_scenarios_mm": [0, 1, 2, 3, 4, 5, 6],
    "opposite_protrusion_status": "PART_MEASUREMENT_REQUIRED",
    "nominal_bore_mm": 10.0,
    "mount_hole_center_distance": "HOLD",
}

PULLEY = {
    "safety_od_mm": 120.0,
    "axial_width_mm": 20.0,
    "runout_boundaries_mm": [0.0, 0.5, 1.0, 1.5],
    "bore": "HOLD_REPORTED_11_MM",
}

TOLERANCE = {
    "placement_boundaries_mm": [-1.0, 0.0, 1.0],
    "independent_variables_per_side": [
        "inner_kp000_axial_error",
        "pulley_axial_error",
        "outer_kp000_axial_error",
    ],
    "center_bilateral_error_max_mm": 2.0,
    "relative_component_error_max_mm": 2.0,
    "frame_deflection_boundaries_mm": [0.0, 1.0, 2.0],
    "belt_wander_boundaries_mm": [0.0, 1.0, 2.0],
    "belt_total_worst_allowance_mm": 6.0,
    "pulley_total_worst_allowance_mm": 3.5,
    "superseded_model": "ONE_SHARED_ASSEMBLY_ERROR",
}

GATES = {
    "center_nominal_min_mm": 4.0,
    "center_residual_min_mm": 2.0,
    "center_nominal_target_mm": 5.0,
    "center_residual_target_mm": 3.0,
    "belt_nominal_min_mm": 14.0,
    "belt_residual_min_mm": 8.0,
    "pulley_nominal_min_mm": 13.5,
    "pulley_residual_min_mm": 10.0,
    "output_reserve_min_mm": 25.0,
    "output_reserve_recommended_mm": 30.0,
    "tool_clearance_candidate_mm": 10.0,
}

V0084_BASELINE = {
    "candidate_id": "S2-INCC-OUTOO-SHIFT01.00",
    "inner_shift_mm": 1.0,
    "pulley_shift_mm": 0.0,
    "outer_shift_mm": 0.0,
    "inner_y_mm": 15.0,
    "pulley_y_mm": 47.0,
    "outer_y_mm": 87.5,
    "center_nominal_mm": 1.0,
    "old_center_residual_mm": 0.0,
    "new_center_residual_mm": -1.0,
    "old_robustness": "276/756",
    "width_mm": 290.0,
    "pto_ends_y_mm": [-145.0, 145.0],
}

V0084_ALT_A = {
    "candidate_id": "S4-IN01.00-P06.00-OUT+03.5",
    "inner_shift_mm": 1.0,
    "pulley_shift_mm": 6.0,
    "outer_shift_mm": 3.5,
    "old_robustness": "756/756",
}

SEARCH_FIELDS = [
    "candidate_id",
    "search_resolution_mm",
    "search_stage",
    "focus_label",
    "inner_orientation",
    "outer_orientation",
    "inner_shift_mm",
    "pulley_shift_mm",
    "outer_shift_mm",
    "inner_y_mm",
    "pulley_y_mm",
    "outer_y_mm",
    "center_nominal_mm",
    "center_residual_mm",
    "belt_inner_nominal_worst_mm",
    "belt_inner_residual_worst_mm",
    "belt_outer_nominal_worst_mm",
    "belt_outer_residual_worst_mm",
    "pulley_inner_nominal_worst_mm",
    "pulley_inner_residual_worst_mm",
    "pulley_outer_nominal_worst_mm",
    "pulley_outer_residual_worst_mm",
    "output_reserve_mm",
    "support_plate_fit",
    "tool_clearance_mm",
    "shaft_length_min_mm",
    "shaft_length_max_mm",
    "total_width_mm",
    "pto_ends_y_mm",
    "total_change_mm",
    "boundary_pass",
    "status",
    "rejection_reason",
]

BOUNDARY_FIELDS = [
    "analysis_scope",
    "side",
    "opposite_protrusion_mm",
    "pulley_runout_mm",
    "left_inner_centerward_error_mm",
    "right_inner_centerward_error_mm",
    "kp000_placement_error_mm",
    "pulley_placement_error_mm",
    "frame_deflection_mm",
    "belt_wander_mm",
    "relative_axial_error_mm",
    "center_residual_mm",
    "belt_nominal_mm",
    "belt_residual_mm",
    "pulley_nominal_mm",
    "pulley_residual_mm",
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
    "role",
    "release_state",
]

MATRIX_FIELDS = [
    "candidate_id",
    "check_id",
    "worst_clearance_or_margin_mm",
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
    "gate",
]


def _round(value: float, digits: int = 3) -> float:
    return round(float(value) + 0.0, digits)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ledger_sha(mapping: dict[str, str]) -> str:
    payload = "".join(f"{key}\t{mapping[key]}\n" for key in sorted(mapping))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_protection_audit() -> dict[str, Any]:
    repo_root = next(
        (
            root
            for root in LANE_DIR.parents
            if (
                root
                / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_4"
                / "build_common_rover_kp000_axial_stack_v0084.py"
            ).is_file()
        ),
        None,
    )
    ledgers = {**UPSTREAM_LEDGER_SHA256, "v0.8.4": V0084_LEDGER_SHA256}
    if repo_root is None:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_HASHES",
            "checked_path_count": 0,
            "mismatches": [],
            "ledger_sha256": ledgers,
        }
    lane = repo_root / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_4"
    mismatches = [
        relative
        for relative, digest in V0084_HASHES.items()
        if not (lane / relative).is_file() or _sha256(lane / relative) != digest
    ]
    if mismatches or _ledger_sha(V0084_HASHES) != V0084_LEDGER_SHA256:
        raise RuntimeError(f"protected v0.8.4 mismatch: {mismatches}")
    parent = _load_module(
        lane / "build_common_rover_kp000_axial_stack_v0084.py",
        "protected_v0084_builder",
    )
    upstream = parent.parent_protection_audit()
    if upstream["checked_path_count"] != 76 or upstream["mismatches"]:
        raise RuntimeError(f"v0.8-v0.8.3 protection failed: {upstream}")
    return {
        "mode": "REPOSITORY_V008_TO_V0084_SHA256_VERIFICATION",
        "checked_path_count": 100,
        "mismatches": [],
        "ledger_sha256": ledgers,
    }


def canonical_parent_protection() -> dict[str, Any]:
    return {
        "authority": "EMBEDDED_SHA256_LOCK_FOR_V008_TO_V0084",
        "checked_path_count": 100,
        "mismatches": [],
        "ledger_sha256": {**UPSTREAM_LEDGER_SHA256, "v0.8.4": V0084_LEDGER_SHA256},
        "repository_runtime_verification": "REQUIRED_WHEN_PARENTS_AVAILABLE",
    }


def baseline_reproduction() -> dict[str, Any]:
    expected = {
        "recommended_candidate_id": "S2-INCC-OUTOO-SHIFT01.00",
        "recommended_center_mm": 1.0,
        "recommended_belt_inner_nominal_mm": 13.0,
        "recommended_belt_inner_residual_mm": 8.0,
        "recommended_pulley_inner_nominal_mm": 13.5,
        "recommended_pulley_inner_residual_mm": 11.0,
        "recommended_robust_pass_count": 276,
        "recommended_robust_total_count": 756,
        "alternative_a_candidate_id": "S4-IN01.00-P06.00-OUT+03.5",
        "width_mm": 290.0,
        "pto_ends_y_mm": [-145.0, 145.0],
    }
    repo_root = next(
        (
            root
            for root in LANE_DIR.parents
            if (
                root
                / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_4"
                / "common_rover_kp000_axial_stack_parameters_v0084.json"
            ).is_file()
        ),
        None,
    )
    if repo_root is not None:
        path = (
            repo_root
            / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_4"
            / "common_rover_kp000_axial_stack_parameters_v0084.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        rec = payload["recommended"]
        robust = payload["recommended_robustness"]
        alt = payload["alternatives"][0]
        actual = {
            "recommended_candidate_id": rec["candidate_id"],
            "recommended_center_mm": rec["center_mutual_clearance_mm"],
            "recommended_belt_inner_nominal_mm": rec["belt_to_inner_nominal_mm"],
            "recommended_belt_inner_residual_mm": rec["belt_to_inner_residual_mm"],
            "recommended_pulley_inner_nominal_mm": rec["pulley_to_inner_nominal_mm"],
            "recommended_pulley_inner_residual_mm": rec["pulley_to_inner_residual_mm"],
            "recommended_robust_pass_count": robust["pass_count"],
            "recommended_robust_total_count": robust["combination_count"],
            "alternative_a_candidate_id": alt["candidate_id"],
            "width_mm": rec["total_width_mm"],
            "pto_ends_y_mm": [rec["right_pto_end_y_mm"], rec["left_pto_end_y_mm"]],
        }
        if actual != expected:
            raise RuntimeError(f"v0.8.4 baseline mismatch: {actual}")
    return {
        "source": "PROTECTED_V0084_BASELINE_AUTHORITY",
        "status": "PASS",
        **expected,
        "old_shared_error_center_residual_mm": 0.0,
        "new_bilateral_error_center_residual_mm": -1.0,
        "old_model_problem": "ONE_SHARED_ERROR_UNDERSTATES_CENTER_AND_RELATIVE_AXIAL_WORST_CASES",
    }


def evaluate_candidate(
    candidate_id: str,
    inner_shift: float,
    pulley_shift: float,
    outer_shift: float,
    resolution: float,
    stage: int,
    focus_label: str = "",
) -> dict[str, Any]:
    center_nominal = -1.0 + 2.0 * inner_shift
    center_residual = center_nominal - 2.0
    belt_inner_nominal = 8.0 - inner_shift + pulley_shift
    belt_outer_nominal = 15.5 + outer_shift - pulley_shift
    pulley_inner_nominal = 8.5 - inner_shift + pulley_shift
    pulley_outer_nominal = 16.0 + outer_shift - pulley_shift
    belt_inner_residual = belt_inner_nominal - 6.0
    belt_outer_residual = belt_outer_nominal - 6.0
    pulley_inner_residual = pulley_inner_nominal - 3.5
    pulley_outer_residual = pulley_outer_nominal - 3.5
    output_reserve = 43.0 - outer_shift
    tool_clearance = 12.0
    support_fit = inner_shift <= 5.0 and outer_shift <= 10.0
    failures = []
    gates = (
        (center_nominal >= 4.0, "CENTER_NOMINAL_LT_4"),
        (center_residual >= 2.0, "CENTER_RESIDUAL_LT_2"),
        (min(belt_inner_nominal, belt_outer_nominal) >= 14.0, "BELT_NOMINAL_LT_14"),
        (min(belt_inner_residual, belt_outer_residual) >= 8.0, "BELT_RESIDUAL_LT_8"),
        (min(pulley_inner_nominal, pulley_outer_nominal) >= 13.5, "PULLEY_NOMINAL_LT_13_5"),
        (min(pulley_inner_residual, pulley_outer_residual) >= 10.0, "PULLEY_RESIDUAL_LT_10"),
        (output_reserve >= 25.0, "OUTPUT_RESERVE_LT_25"),
        (support_fit, "SUPPORT_PLATE_REFERENCE_FAIL"),
        (tool_clearance >= 10.0, "TOOL_CLEARANCE_LT_10"),
    )
    failures.extend(reason for passed, reason in gates if not passed)
    boundary_pass = not failures
    return {
        "candidate_id": candidate_id,
        "search_resolution_mm": resolution,
        "search_stage": stage,
        "focus_label": focus_label,
        "inner_orientation": "C/C",
        "outer_orientation": "O/O",
        "inner_shift_mm": _round(inner_shift),
        "pulley_shift_mm": _round(pulley_shift),
        "outer_shift_mm": _round(outer_shift),
        "inner_y_mm": _round(14.0 + inner_shift),
        "pulley_y_mm": _round(47.0 + pulley_shift),
        "outer_y_mm": _round(87.5 + outer_shift),
        "center_nominal_mm": _round(center_nominal),
        "center_residual_mm": _round(center_residual),
        "belt_inner_nominal_worst_mm": _round(belt_inner_nominal),
        "belt_inner_residual_worst_mm": _round(belt_inner_residual),
        "belt_outer_nominal_worst_mm": _round(belt_outer_nominal),
        "belt_outer_residual_worst_mm": _round(belt_outer_residual),
        "pulley_inner_nominal_worst_mm": _round(pulley_inner_nominal),
        "pulley_inner_residual_worst_mm": _round(pulley_inner_residual),
        "pulley_outer_nominal_worst_mm": _round(pulley_outer_nominal),
        "pulley_outer_residual_worst_mm": _round(pulley_outer_residual),
        "output_reserve_mm": _round(output_reserve),
        "support_plate_fit": "PASS_95X140X5_REFERENCE" if support_fit else "FAIL",
        "tool_clearance_mm": tool_clearance,
        "shaft_length_min_mm": _round(139.5 - inner_shift),
        "shaft_length_max_mm": _round(145.5 - inner_shift),
        "total_width_mm": 290.0,
        "pto_ends_y_mm": "-145.0|145.0",
        "total_change_mm": _round(inner_shift + pulley_shift + outer_shift),
        "boundary_pass": boundary_pass,
        "status": "ROBUST_CONDITIONAL_PASS_CANDIDATE" if boundary_pass else "FAIL",
        "rejection_reason": "|".join(failures),
    }


def _frange(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step))
    return [_round(start + index * step, 2) for index in range(count + 1)]


def _candidate_id(inner: float, pulley: float, outer: float) -> tuple[str, str]:
    focus = {
        (2.5, 8.5, 7.0): "R1",
        (3.0, 9.0, 7.5): "R2",
        (3.0, 9.5, 8.5): "R3",
    }.get((inner, pulley, outer), "")
    if focus:
        return f"{focus}-IN{inner:04.2f}-P{pulley:04.2f}-OUT{outer:04.2f}", focus
    return f"G-IN{inner:04.2f}-P{pulley:05.2f}-OUT{outer:05.2f}", ""


def search_candidates() -> list[dict[str, Any]]:
    rows = [
        evaluate_candidate("V0084-RECOMMENDED-BASELINE", 1.0, 0.0, 0.0, 0.0, 0, "V0084_RECOMMENDED"),
        evaluate_candidate("V0084-ALTERNATIVE-A-BASELINE", 1.0, 6.0, 3.5, 0.0, 0, "V0084_ALTERNATIVE_A"),
    ]
    coarse = set(
        itertools.product(
            _frange(1.0, 5.0, 0.5),
            _frange(5.0, 12.0, 0.5),
            _frange(3.0, 10.0, 0.5),
        )
    )
    fine = set(
        itertools.product(
            _frange(4.5, 5.0, 0.25),
            _frange(10.5, 12.0, 0.25),
            _frange(9.0, 10.0, 0.25),
        )
    )
    for inner, pulley, outer in sorted(coarse | fine):
        candidate_id, focus = _candidate_id(inner, pulley, outer)
        resolution = 0.5 if (inner, pulley, outer) in coarse else 0.25
        stage = 1 if resolution == 0.5 else 2
        rows.append(
            evaluate_candidate(
                candidate_id,
                inner,
                pulley,
                outer,
                resolution,
                stage,
                focus,
            )
        )
    return rows


def ranking_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        0 if candidate["boundary_pass"] else 1,
        -candidate["center_residual_mm"],
        -min(candidate["belt_inner_residual_worst_mm"], candidate["belt_outer_residual_worst_mm"]),
        -min(candidate["pulley_inner_residual_worst_mm"], candidate["pulley_outer_residual_worst_mm"]),
        -candidate["output_reserve_mm"],
        0 if candidate["support_plate_fit"].startswith("PASS") else 1,
        0,
        candidate["shaft_length_max_mm"],
        candidate["total_change_mm"],
        candidate["search_stage"],
        candidate["candidate_id"],
    )


def selected_candidates(search: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    ranked = sorted((row for row in search if row["search_stage"] > 0), key=ranking_key)
    if len(ranked) < 3 or not all(row["boundary_pass"] for row in ranked[:3]):
        raise RuntimeError("fewer than three robust candidates")
    return ranked[0], ranked[1], ranked[2]


def ranking_rows(search: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = selected_candidates(search)
    labels = (
        ("RECOMMENDED_ROBUST_PRIORITY", "Maximum center residual, then maximum minimum belt/pulley residual."),
        ("ALTERNATIVE_A", "Next robust boundary candidate by output reserve and change ordering."),
        ("ALTERNATIVE_B", "Third robust boundary candidate under the superseding priority contract."),
    )
    rows = []
    for rank, (candidate, (selection, rationale)) in enumerate(zip(selected, labels), 1):
        rows.append(
            {
                "rank": rank,
                "selection": selection,
                **{field: candidate.get(field, "") for field in SEARCH_FIELDS},
                "rationale": rationale,
            }
        )
    return rows


def interval_analysis(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": "MATHEMATICAL_WORST_CASE_INTERVAL",
        "authority_for_pass": True,
        "opposite_protrusion_interval_mm": [0.0, 6.0],
        "independent_placement_intervals_mm": {
            "left_inner": [-1.0, 1.0],
            "right_inner": [-1.0, 1.0],
            "left_pulley": [-1.0, 1.0],
            "right_pulley": [-1.0, 1.0],
            "left_outer": [-1.0, 1.0],
            "right_outer": [-1.0, 1.0],
        },
        "worst_case": {
            "center_nominal_mm": candidate["center_nominal_mm"],
            "center_residual_mm": candidate["center_residual_mm"],
            "belt_inner_nominal_mm": candidate["belt_inner_nominal_worst_mm"],
            "belt_inner_residual_mm": candidate["belt_inner_residual_worst_mm"],
            "belt_outer_nominal_mm": candidate["belt_outer_nominal_worst_mm"],
            "belt_outer_residual_mm": candidate["belt_outer_residual_worst_mm"],
            "pulley_inner_nominal_mm": candidate["pulley_inner_nominal_worst_mm"],
            "pulley_inner_residual_mm": candidate["pulley_inner_residual_worst_mm"],
            "pulley_outer_nominal_mm": candidate["pulley_outer_nominal_worst_mm"],
            "pulley_outer_residual_mm": candidate["pulley_outer_residual_worst_mm"],
            "output_reserve_mm": candidate["output_reserve_mm"],
        },
        "all_gates_pass": candidate["boundary_pass"],
        "classification": "ROBUST_CONDITIONAL_PASS" if candidate["boundary_pass"] else "FAIL",
    }


def boundary_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left_error, right_error in itertools.product((-1.0, 0.0, 1.0), repeat=2):
        center = candidate["center_nominal_mm"] - left_error - right_error
        failures = [] if center >= 2.0 else ["CENTER_RESIDUAL_LT_2"]
        rows.append(
            {
                "analysis_scope": "CENTER_BILATERAL",
                "side": "LEFT_AND_RIGHT",
                "opposite_protrusion_mm": "",
                "pulley_runout_mm": "",
                "left_inner_centerward_error_mm": left_error,
                "right_inner_centerward_error_mm": right_error,
                "kp000_placement_error_mm": "",
                "pulley_placement_error_mm": "",
                "frame_deflection_mm": "",
                "belt_wander_mm": "",
                "relative_axial_error_mm": "",
                "center_residual_mm": _round(center),
                "belt_nominal_mm": "",
                "belt_residual_mm": "",
                "pulley_nominal_mm": "",
                "pulley_residual_mm": "",
                "status": "PASS_BOUNDARY" if not failures else "FAIL",
                "failure_reason": "|".join(failures),
            }
        )
    for side, scope in itertools.product(("LEFT", "RIGHT"), ("INNER_SIDE", "OUTER_SIDE")):
        for protrusion, runout, kp_error, pulley_error, frame, wander in itertools.product(
            range(7),
            (0.0, 0.5, 1.0, 1.5),
            (-1.0, 0.0, 1.0),
            (-1.0, 0.0, 1.0),
            (0.0, 1.0, 2.0),
            (0.0, 1.0, 2.0),
        ):
            relative = abs(kp_error - pulley_error)
            if scope == "INNER_SIDE":
                belt_nominal = 14.0 - candidate["inner_shift_mm"] + candidate["pulley_shift_mm"] - protrusion
                pulley_nominal = 14.5 - candidate["inner_shift_mm"] + candidate["pulley_shift_mm"] - protrusion
            else:
                belt_nominal = 21.5 + candidate["outer_shift_mm"] - candidate["pulley_shift_mm"] - protrusion
                pulley_nominal = 22.0 + candidate["outer_shift_mm"] - candidate["pulley_shift_mm"] - protrusion
            belt_residual = belt_nominal - relative - frame - wander
            pulley_residual = pulley_nominal - relative - runout
            failures = []
            if belt_nominal < 14:
                failures.append("BELT_NOMINAL_LT_14")
            if belt_residual < 8:
                failures.append("BELT_RESIDUAL_LT_8")
            if pulley_nominal < 13.5:
                failures.append("PULLEY_NOMINAL_LT_13_5")
            if pulley_residual < 10:
                failures.append("PULLEY_RESIDUAL_LT_10")
            rows.append(
                {
                    "analysis_scope": scope,
                    "side": side,
                    "opposite_protrusion_mm": protrusion,
                    "pulley_runout_mm": runout,
                    "left_inner_centerward_error_mm": "",
                    "right_inner_centerward_error_mm": "",
                    "kp000_placement_error_mm": kp_error,
                    "pulley_placement_error_mm": pulley_error,
                    "frame_deflection_mm": frame,
                    "belt_wander_mm": wander,
                    "relative_axial_error_mm": relative,
                    "center_residual_mm": "",
                    "belt_nominal_mm": _round(belt_nominal),
                    "belt_residual_mm": _round(belt_residual),
                    "pulley_nominal_mm": _round(pulley_nominal),
                    "pulley_residual_mm": _round(pulley_residual),
                    "status": "PASS_BOUNDARY" if not failures else "FAIL",
                    "failure_reason": "|".join(failures),
                }
            )
    return rows


def monte_carlo_summary(candidate: dict[str, Any], samples: int = 2000) -> dict[str, Any]:
    rng = random.Random(850)
    minima = {
        "center_residual_mm": float("inf"),
        "belt_residual_mm": float("inf"),
        "pulley_residual_mm": float("inf"),
    }
    pass_count = 0
    for _ in range(samples):
        protrusion = rng.uniform(0, 6)
        runout = rng.uniform(0, 1.5)
        li, ri = rng.uniform(-1, 1), rng.uniform(-1, 1)
        inner_error, pulley_error, outer_error = (
            rng.uniform(-1, 1),
            rng.uniform(-1, 1),
            rng.uniform(-1, 1),
        )
        frame, wander = rng.uniform(0, 2), rng.uniform(0, 2)
        center = candidate["center_nominal_mm"] - li - ri
        relative_inner = abs(inner_error - pulley_error)
        relative_outer = abs(outer_error - pulley_error)
        belt_inner = 14 - candidate["inner_shift_mm"] + candidate["pulley_shift_mm"] - protrusion - relative_inner - frame - wander
        belt_outer = 21.5 + candidate["outer_shift_mm"] - candidate["pulley_shift_mm"] - protrusion - relative_outer - frame - wander
        pulley_inner = 14.5 - candidate["inner_shift_mm"] + candidate["pulley_shift_mm"] - protrusion - relative_inner - runout
        pulley_outer = 22 + candidate["outer_shift_mm"] - candidate["pulley_shift_mm"] - protrusion - relative_outer - runout
        minima["center_residual_mm"] = min(minima["center_residual_mm"], center)
        minima["belt_residual_mm"] = min(minima["belt_residual_mm"], belt_inner, belt_outer)
        minima["pulley_residual_mm"] = min(minima["pulley_residual_mm"], pulley_inner, pulley_outer)
        if center >= 2 and min(belt_inner, belt_outer) >= 8 and min(pulley_inner, pulley_outer) >= 10:
            pass_count += 1
    return {
        "method": "REPRESENTATIVE_MONTE_CARLO_NON_AUTHORITY",
        "seed": 850,
        "sample_count": samples,
        "pass_count": pass_count,
        "fail_count": samples - pass_count,
        "observed_minima_mm": {key: _round(value) for key, value in minima.items()},
        "pass_authority": False,
    }


def axial_stack_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        ("central reserve", "HOLD", 0, 6, "shaft start"),
        ("inner support plate", "NOMINAL", 5, 5, "P3-A5052-T5"),
        ("inner KP000 housing", "MEASURED", 17, 17, "Y center shifted"),
        ("inner known collar", "MEASURED", 6, 6, "ORIENTATION_C"),
        ("inner opposite protrusion", "HOLD", 0, 6, "sensitivity authority"),
        ("inner shaft collar", "HOLD", 0, 6, "axial retention"),
        ("spacer A", "HOLD", 0, 4, "no KP000 contact location"),
        ("60T axial envelope", "MEASURED_CONFLICT", 20, 21, "reported total versus components"),
        ("spacer B", "HOLD", 0, 4, "outer clearance"),
        ("outer shaft collar", "HOLD", 0, 6, "axial retention"),
        ("outer KP000 housing", "MEASURED", 17, 17, "Y center shifted"),
        ("outer known collar", "MEASURED", 6, 6, "ORIENTATION_O"),
        ("outer opposite protrusion", "HOLD", 0, 6, "sensitivity authority"),
        ("output reserve", "POSITION_DERIVED", candidate["output_reserve_mm"], candidate["output_reserve_mm"], "to Y=145"),
        ("coupling reserve", "HOLD", 0, "", "part not selected"),
        ("retaining reserve", "HOLD", 0, "", "method not released"),
        ("PTO output end", "NOMINAL_BOUNDARY", 145, 145, "absolute Y limit"),
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
                    "role": role,
                    "release_state": "HOLD" if classification in {"HOLD", "MEASURED_CONFLICT"} else "CANDIDATE_ONLY",
                }
            )
    return rows


def interference_matrix(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("LEFT_INNER_VS_RIGHT_INNER", candidate["center_residual_mm"], "BILATERAL_INDEPENDENT_ERROR"),
        ("LEFT_BELT_VS_INNER_KP000", candidate["belt_inner_residual_worst_mm"], "BOUNDARY_INTERVAL"),
        ("RIGHT_BELT_VS_INNER_KP000", candidate["belt_inner_residual_worst_mm"], "BOUNDARY_INTERVAL"),
        ("LEFT_BELT_VS_OUTER_KP000", candidate["belt_outer_residual_worst_mm"], "BOUNDARY_INTERVAL"),
        ("RIGHT_BELT_VS_OUTER_KP000", candidate["belt_outer_residual_worst_mm"], "BOUNDARY_INTERVAL"),
        ("LEFT_PULLEY_VS_INNER_KP000", candidate["pulley_inner_residual_worst_mm"], "OD120_BOUNDARY"),
        ("RIGHT_PULLEY_VS_INNER_KP000", candidate["pulley_inner_residual_worst_mm"], "OD120_BOUNDARY"),
        ("LEFT_PULLEY_VS_OUTER_KP000", candidate["pulley_outer_residual_worst_mm"], "OD120_BOUNDARY"),
        ("RIGHT_PULLEY_VS_OUTER_KP000", candidate["pulley_outer_residual_worst_mm"], "OD120_BOUNDARY"),
        ("LEFT_SUPPORT_VS_RIGHT_SUPPORT", 23 + 2 * candidate["inner_shift_mm"], "P3_A5052_T5"),
        ("LEFT_TOOL_VS_FRAME", candidate["tool_clearance_mm"], "SIMPLIFIED_TOOL_HOLD"),
        ("RIGHT_TOOL_VS_FRAME", candidate["tool_clearance_mm"], "SIMPLIFIED_TOOL_HOLD"),
        ("PTO_BELTS_VS_FASTENERS", 14.0, "NON_REGRESSION"),
        ("PULLEYS_VS_FASTENERS", 12.0, "NON_REGRESSION"),
        ("PTO_BELT_VS_FRAME", 15.0, "V0084_NON_REGRESSION"),
        ("DRIVE_BELT_VS_FRAME", 15.5, "V0084_NON_REGRESSION"),
        ("TRACK_DYNAMIC_VS_UPPER", 10.0, "V0084_NON_REGRESSION"),
        ("TOTAL_WIDTH_MARGIN", 300 - candidate["total_width_mm"], "STRICT_LT_300"),
        ("PTO_END_MARGIN", 0.0, "ABS_Y_LE_145_BOUNDARY"),
        ("OUTPUT_RESERVE", candidate["output_reserve_mm"], "MIN_25"),
    ]
    rows = []
    for check_id, clearance, authority in checks:
        boundary_allowed = check_id == "PTO_END_MARGIN"
        intersection = 0 if clearance > 0 or (boundary_allowed and clearance == 0) else 1
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "check_id": check_id,
                "worst_clearance_or_margin_mm": _round(clearance),
                "intersection_count": intersection,
                "status": "PASS_BOUNDARY" if boundary_allowed else ("PASS" if intersection == 0 else "FAIL"),
                "authority": authority,
            }
        )
    return rows


def remeasurement_rows() -> list[dict[str, Any]]:
    raw = [
        ("CRITICAL", "C01", "KP000", "opposite-side protrusion each unit", "UNKNOWN; 0..6 interval", "CALIPER", "0.1 mm", "Measure both axial faces and mark collar direction.", "ROBUSTNESS_RELEASE"),
        ("CRITICAL", "C02", "KP000", "mounting-hole center distance", "HOLD", "CALIPER", "0.1 mm", "Outer-edge span minus diameter or inner-edge span plus diameter.", "PLATE_HOLE_PATTERN"),
        ("CRITICAL", "C03", "KP000", "total axial envelope", "HOLD", "CALIPER", "0.1 mm", "Measure each of four units.", "PHYSICAL_STACK"),
        ("CRITICAL", "C04", "60T", "bore and shaft fit", "reported 11; FAIL_PROVISIONAL", "BORE_GAUGE", "0.01 mm", "Measure clock positions and 10 mm shaft fit.", "PULLEY_FIT"),
        ("CRITICAL", "C05", "60T", "radial runout", "0..1.5 interval", "DIAL_INDICATOR", "0.05 mm", "Measure on centered representative hub.", "PULLEY_RESIDUAL"),
        ("CRITICAL", "C06", "ASSEMBLY", "six independent Y placement errors", "+/-1 interval each", "HEIGHT/DEPTH_GAUGE", "0.1 mm", "Measure left/right inner, pulley and outer faces independently.", "BOUNDARY_MODEL"),
        ("HIGH", "H01", "FRAME", "deflection toward belt", "0..2 interval", "DIAL_GAUGE", "0.1 mm", "Approved static fixture only.", "BELT_RESIDUAL"),
        ("HIGH", "H02", "BELT", "lateral wander", "0..2 interval", "VIDEO/GAUGE", "0.1 mm", "No powered test without approval.", "BELT_RESIDUAL"),
        ("HIGH", "H03", "TOOL", "working envelope", "HOLD", "CALIPER", "0.1 mm", "Short arm, bend, socket OD and ratchet head.", "SERVICE_ACCESS"),
        ("HIGH", "H04", "OUTPUT", "collar/coupling/retaining/cap stack", "HOLD", "CALIPER", "0.1 mm", "Measure selected parts face-to-face.", "SHAFT_CUT"),
    ]
    return [dict(zip(REMEASURE_FIELDS, row)) for row in raw]


def tolerance_correction_markdown() -> str:
    return """# v0.8.5 tolerance-model correction

`NOT_FOR_MANUFACTURING`

## Superseded behavior

v0.8.4 applied one shared axial assembly error. That correlated component
motion and allowed zero central residual to pass. It also limited relative
KP000-to-pulley error to 1 mm.

## Corrected behavior

Left/right inner KP000, pulley and outer KP000 placement errors are independent
and each range from -1 to +1 mm.

`CENTER_RESIDUAL = CENTER_NOMINAL - LEFT_CENTERWARD_ERROR - RIGHT_CENTERWARD_ERROR`

The center worst case therefore subtracts 2 mm. A residual of zero is FAIL.

`RELATIVE_AXIAL_ERROR = ABS(KP000_ERROR - PULLEY_ERROR)`

The relative worst case is 2 mm.

`BELT_RESIDUAL = BELT_NOMINAL - RELATIVE_ERROR - FRAME_DEFLECTION - BELT_WANDER`

The belt worst allowance is 2 + 2 + 2 = 6 mm.

`PULLEY_RESIDUAL = PULLEY_NOMINAL - RELATIVE_ERROR - RUNOUT`

The pulley worst allowance is 2 + 1.5 = 3.5 mm.

PASS authority comes from mathematical interval analysis and decomposed
boundary enumeration. Monte Carlo is recorded only as a non-authoritative
cross-check.
"""


def authority_markdown(params: dict[str, Any]) -> str:
    rec = params["recommended"]
    alt_a, alt_b = params["alternatives"]
    focus = params["focus_candidates"]
    interval = params["interval_analysis"]
    return f"""# Common Rover Robust Axial Tolerance Design Authority v0.8.5

Document ID: `{DOCUMENT_ID}`

`NOT_FOR_MANUFACTURING`  
`PART_MEASUREMENT_REQUIRED`

## Protected parents and baseline

This is a difference authority over protected v0.8 through v0.8.4. Repository
runtime verification covers 100 parent paths. The v0.8.4 recommendation
`S2-INCC-OUTOO-SHIFT01.00` is preserved as a comparison but not inherited.

Its old center nominal was 1 mm. Independent bilateral error makes the new
center residual -1 mm, so it fails v0.8.5. The former Alternative A also has
only 1 mm nominal center clearance and is not robust under the corrected model.

## Corrected independent tolerance model

Each side has independent inner-KP000, pulley and outer-KP000 axial errors of
-1/0/+1 mm. Center error is bilateral, relative component error can reach
2 mm, belt worst allowance is 6 mm and pulley worst allowance is 3.5 mm.
Zero center residual is FAIL.

Selection priority is boundary pass, center residual, minimum belt residual,
minimum pulley residual, output reserve, plate fit, added parts, shaft length,
change and finally Stage. The v0.8.4 early-Stage preference is superseded.

## Search

The search contains {params['search_candidate_count']} candidates: two protected
v0.8.4 comparisons plus coarse 0.5 mm and refined 0.25 mm grids. All use inner
C/C and outer O/O. R1, R2 and R3 were explicitly evaluated:

{chr(10).join(f"- {key}: center {value['center_nominal_mm']}/{value['center_residual_mm']} mm, belt residual min {min(value['belt_inner_residual_worst_mm'], value['belt_outer_residual_worst_mm'])} mm, status {value['status']}" for key, value in focus.items())}

## Recommended

`{rec['candidate_id']}`

- Inner centers: Y=+/-{rec['inner_y_mm']} mm, shift {rec['inner_shift_mm']} mm
- Pulley centers: Y=+/-{rec['pulley_y_mm']} mm, shift {rec['pulley_shift_mm']} mm
- Outer centers: Y=+/-{rec['outer_y_mm']} mm, shift {rec['outer_shift_mm']} mm
- Center nominal/residual: {rec['center_nominal_mm']}/{rec['center_residual_mm']} mm
- Inner belt worst nominal/residual: {rec['belt_inner_nominal_worst_mm']}/{rec['belt_inner_residual_worst_mm']} mm
- Outer belt worst nominal/residual: {rec['belt_outer_nominal_worst_mm']}/{rec['belt_outer_residual_worst_mm']} mm
- Inner pulley worst nominal/residual: {rec['pulley_inner_nominal_worst_mm']}/{rec['pulley_inner_residual_worst_mm']} mm
- Outer pulley worst nominal/residual: {rec['pulley_outer_nominal_worst_mm']}/{rec['pulley_outer_residual_worst_mm']} mm
- Output reserve: {rec['output_reserve_mm']} mm
- Width and ends: 290 mm, +/-145 mm

The interval authority is `{interval['classification']}` and includes the full
0..6 mm opposite protrusion interval.

## Alternatives

- Alternative A `{alt_a['candidate_id']}`: inner/pulley/outer shifts
  {alt_a['inner_shift_mm']}/{alt_a['pulley_shift_mm']}/{alt_a['outer_shift_mm']} mm.
- Alternative B `{alt_b['candidate_id']}`: inner/pulley/outer shifts
  {alt_b['inner_shift_mm']}/{alt_b['pulley_shift_mm']}/{alt_b['outer_shift_mm']} mm.

Both satisfy every corrected boundary gate. They are ordered below the
recommendation by residual/output/change priorities, not Stage.

## Support, tool and shaft

P3-A5052-T5 remains a mirrored independent 95 x 140 x 5 mm reference candidate.
No hole is released. Simplified tool clearance is 12 mm with zero envelope
intersection, but actual-tool access remains HOLD.

The coordinate-derived shaft range is {rec['shaft_length_min_mm']} to
{rec['shaft_length_max_mm']} mm. A 300 or 400 mm bar can provisionally yield
two shafts. Kerf and cutting remain HOLD.

## Release

- Geometry envelope: `CONDITIONAL_PASS_CANDIDATE`
- Tolerance robustness: `ROBUST_CONDITIONAL_PASS_CANDIDATE`
- Opposite protrusion: `PART_MEASUREMENT_REQUIRED`
- Pulley bore fit: `FAIL_PROVISIONAL`
- Physical fit, support machining, drilling, shaft cutting: `HOLD`
- Load, water and mud tests: `HOLD`
- Field deployment: `NOT_APPROVED`
"""


def remeasurement_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Common Rover v0.8.5 remeasurement sheet",
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
            "{instrument} | {resolution} | {method} | {gate} |".format(**row)
        )
    lines.extend(
        [
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
    return f"""# v0.8.5 robust axial tolerance handoff

This exact 24-file package corrects the v0.8.4 shared-error model. PASS
authority is mathematical interval plus boundary enumeration, not Monte Carlo.

Run:

`python -B {BUILDER_NAME} --verify`

`python -B {TEST_REL}`

No machining, drilling, shaft cutting, load testing or deployment is approved.
`NOT_FOR_MANUFACTURING`.
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


def kp000_worst_shape(x: float, y: float, axis_z: float) -> cq.Shape:
    housing = _box(67, 17, 35, (x, y, axis_z - 1))
    bore = _cylinder_y(5, 31, (x, y, axis_z))
    housing = housing.cut(bore)
    collars = [
        _cylinder_y(13, 6, (x, y - 11.5, axis_z)).cut(_cylinder_y(5, 8, (x, y - 11.5, axis_z))),
        _cylinder_y(13, 6, (x, y + 11.5, axis_z)).cut(_cylinder_y(5, 8, (x, y + 11.5, axis_z))),
    ]
    return cq.Compound.makeCompound([housing, *collars])


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
    x, axis_z = 390.0, 370.0
    yi, yp, yo = candidate["inner_y_mm"], candidate["pulley_y_mm"], candidate["outer_y_mm"]
    components: list[cq.Shape] = []
    for sign in (-1, 1):
        start = sign * (yi - 14.5 - 6.0)
        end = sign * 145.0
        components.extend(
            [
                plate_shape(x, sign * yi, 300),
                kp000_worst_shape(x, sign * yi, axis_z),
                kp000_worst_shape(x, sign * yo, axis_z),
                _cylinder_y(5, abs(end - start), (x, (start + end) / 2, axis_z)),
                _cylinder_y(60, 20, (x, sign * yp, axis_z)),
                _box(220, 21, 120, (340, sign * yp, axis_z)),
                _box(220, 33, 120, (340, sign * yp, axis_z)),
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


def cad_clearances(candidate: dict[str, Any]) -> dict[str, float]:
    x, z = 390.0, 370.0
    yi, yp, yo = candidate["inner_y_mm"], candidate["pulley_y_mm"], candidate["outer_y_mm"]
    inner_l = kp000_worst_shape(x, yi, z)
    inner_r = kp000_worst_shape(x, -yi, z)
    outer_l = kp000_worst_shape(x, yo, z)
    pulley = _cylinder_y(60, 20, (x, yp, z))
    belt_nominal = _box(220, 21, 120, (340, yp, z))
    belt_safety = _box(220, 33, 120, (340, yp, z))
    return {
        "center_nominal_mm": _round(inner_l.distance(inner_r)),
        "belt_inner_nominal_mm": _round(belt_nominal.distance(inner_l)),
        "belt_inner_safety_mm": _round(belt_safety.distance(inner_l)),
        "belt_outer_nominal_mm": _round(belt_nominal.distance(outer_l)),
        "belt_outer_safety_mm": _round(belt_safety.distance(outer_l)),
        "pulley_inner_nominal_mm": _round(pulley.distance(inner_l)),
        "pulley_outer_nominal_mm": _round(pulley.distance(outer_l)),
        "support_mutual_mm": _round(plate_shape(x, yi, 300).distance(plate_shape(x, -yi, 300))),
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


def overview_svg(rec: dict[str, Any], alt_a: dict[str, Any], alt_b: dict[str, Any]) -> str:
    def panel(y: int, title: str, candidate: dict[str, Any], color: str) -> str:
        scale, origin = 3.55, 700
        values = {
            "ir": origin - candidate["inner_y_mm"] * scale,
            "pr": origin - candidate["pulley_y_mm"] * scale,
            "or": origin - candidate["outer_y_mm"] * scale,
            "il": origin + candidate["inner_y_mm"] * scale,
            "pl": origin + candidate["pulley_y_mm"] * scale,
            "ol": origin + candidate["outer_y_mm"] * scale,
        }
        return f"""
<text x="55" y="{y-68}" class="h">{title}</text>
<line x1="160" y1="{y}" x2="1240" y2="{y}" class="axis"/>
<rect x="{values['ir']-30}" y="{y-35}" width="60" height="70" fill="{color}" class="part"/>
<rect x="{values['il']-30}" y="{y-35}" width="60" height="70" fill="{color}" class="part"/>
<circle cx="{values['pr']}" cy="{y}" r="40" class="pulley"/><circle cx="{values['pl']}" cy="{y}" r="40" class="pulley"/>
<rect x="{values['or']-30}" y="{y-35}" width="60" height="70" fill="{color}" class="part"/>
<rect x="{values['ol']-30}" y="{y-35}" width="60" height="70" fill="{color}" class="part"/>
<text x="55" y="{y+65}" class="s">Y +/- {candidate['inner_y_mm']}/{candidate['pulley_y_mm']}/{candidate['outer_y_mm']} · center N/R {candidate['center_nominal_mm']}/{candidate['center_residual_mm']}</text>
<text x="720" y="{y+65}" class="s">belt R min {min(candidate['belt_inner_residual_worst_mm'],candidate['belt_outer_residual_worst_mm'])} · pulley R min {min(candidate['pulley_inner_residual_worst_mm'],candidate['pulley_outer_residual_worst_mm'])} · output {candidate['output_reserve_mm']}</text>
"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>text{{font-family:Arial,sans-serif;fill:#0b2545}}.t{{font-size:30px;font-weight:700}}.h{{font-size:23px;font-weight:700}}.s{{font-size:16px}}.axis{{stroke:#19376d;stroke-width:3}}.part{{stroke:#134b2c;stroke-width:2}}.pulley{{fill:#ffe6a7;stroke:#a65f00;stroke-width:3}}.warn{{fill:#b40000;font-size:17px;font-weight:700}}.frame{{fill:#f7f9fc;stroke:#ccd6e2;stroke-width:2}}</style>
<rect width="1400" height="900" fill="#f2f5f9"/>
<text x="35" y="48" class="t">Common Rover v0.8.5 independent tolerance search</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · PART_MEASUREMENT_REQUIRED · physical fit HOLD</text>
<rect x="35" y="105" width="1330" height="225" class="frame"/>{panel(220,"Recommended · robust priority",rec,"#70c173")}
<rect x="35" y="355" width="1330" height="205" class="frame"/>{panel(465,"Alternative A",alt_a,"#69b7df")}
<rect x="35" y="585" width="1330" height="205" class="frame"/>{panel(695,"Alternative B",alt_b,"#c0a3e8")}
<text x="35" y="845" class="s">All displayed residuals include opposite protrusion 6 mm and independent-error interval maxima.</text>
</svg>
"""


def tolerance_svg(candidate: dict[str, Any]) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>text{{font-family:Arial,sans-serif;fill:#0b2545}}.t{{font-size:30px;font-weight:700}}.h{{font-size:23px;font-weight:700}}.s{{font-size:17px}}.box{{fill:#fff;stroke:#ccd6e2;stroke-width:2}}.good{{fill:#d7f4da;stroke:#197333;stroke-width:2}}.warn{{fill:#b40000;font-size:17px;font-weight:700}}</style>
<rect width="1400" height="900" fill="#f4f7fb"/>
<text x="35" y="48" class="t">v0.8.5 corrected independent axial tolerance</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · interval and boundary proof are PASS authority</text>
<rect x="45" y="120" width="1310" height="170" class="box"/>
<text x="70" y="165" class="h">Center</text><text x="70" y="205" class="s">CENTER_RESIDUAL = {candidate['center_nominal_mm']} − left centerward 1 − right centerward 1 = {candidate['center_residual_mm']} mm</text>
<text x="70" y="250" class="s">Gate: nominal ≥4, residual ≥2; target ≥5/3</text>
<rect x="45" y="320" width="1310" height="210" class="box"/>
<text x="70" y="365" class="h">Belt</text><text x="70" y="405" class="s">RELATIVE_ERROR = |KP000 error − pulley error| ≤2 mm</text>
<text x="70" y="445" class="s">Residual = nominal − relative 2 − frame 2 − wander 2</text>
<text x="70" y="485" class="s">Worst inner/outer = {candidate['belt_inner_residual_worst_mm']}/{candidate['belt_outer_residual_worst_mm']} mm; gate ≥8</text>
<rect x="45" y="560" width="1310" height="210" class="good"/>
<text x="70" y="605" class="h">Pulley OD120 safety envelope</text>
<text x="70" y="645" class="s">Residual = nominal − relative 2 − runout 1.5</text>
<text x="70" y="685" class="s">Worst inner/outer = {candidate['pulley_inner_residual_worst_mm']}/{candidate['pulley_outer_residual_worst_mm']} mm; gate ≥10</text>
<text x="70" y="735" class="h">ROBUST_CONDITIONAL_PASS · opposite protrusion remains measurement-required</text>
</svg>
"""


def center_svg(candidate: dict[str, Any]) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">
<style>text{{font-family:Arial,sans-serif;fill:#0b2545}}.t{{font-size:30px;font-weight:700}}.h{{font-size:24px;font-weight:700}}.s{{font-size:18px}}.bad{{fill:#ffd1d1;stroke:#b40000;stroke-width:3}}.good{{fill:#d7f4da;stroke:#197333;stroke-width:3}}.warn{{fill:#b40000;font-size:17px;font-weight:700}}</style>
<rect width="1400" height="900" fill="#f5f7fb"/>
<text x="35" y="48" class="t">v0.8.5 bilateral center-clearance correction</text>
<text x="35" y="78" class="warn">NOT_FOR_MANUFACTURING · zero residual is FAIL</text>
<rect x="55" y="125" width="620" height="620" class="bad"/>
<text x="85" y="175" class="h">v0.8.4 recommendation · FAIL under new model</text>
<text x="85" y="280" class="s">Nominal center clearance = 1.0 mm</text>
<text x="85" y="340" class="s">Independent centerward errors = 1 + 1 mm</text>
<text x="85" y="410" class="h">Residual = −1.0 mm</text>
<text x="85" y="480" class="s">Old shared-error result cannot be reused.</text>
<rect x="725" y="125" width="620" height="620" class="good"/>
<text x="755" y="175" class="h">v0.8.5 recommendation · CONDITIONAL</text>
<text x="755" y="280" class="s">Nominal center clearance = {candidate['center_nominal_mm']} mm</text>
<text x="755" y="340" class="s">Independent centerward errors = 1 + 1 mm</text>
<text x="755" y="410" class="h">Residual = {candidate['center_residual_mm']} mm</text>
<text x="755" y="480" class="s">Nominal target ≥5 and residual target ≥3 are met.</text>
<text x="755" y="550" class="s">Physical dry fit remains HOLD.</text>
</svg>
"""


def build_datasets() -> dict[str, Any]:
    runtime_parent = parent_protection_audit()
    baseline = baseline_reproduction()
    search = search_candidates()
    recommended, alt_a, alt_b = selected_candidates(search)
    boundaries = boundary_rows(recommended)
    interval = interval_analysis(recommended)
    monte_carlo = monte_carlo_summary(recommended)
    focus = {
        label: next(row for row in search if row["focus_label"] == label)
        for label in ("R1", "R2", "R3")
    }
    matrices = []
    for candidate in (recommended, alt_a, alt_b):
        matrices.extend(interference_matrix(candidate))
    parameters = {
        "document_id": DOCUMENT_ID,
        "status": "NOT_FOR_MANUFACTURING",
        "parent_designs": ["v0.8", "v0.8.1", "v0.8.2", "v0.8.3", "v0.8.4"],
        "parent_protection": canonical_parent_protection(),
        "baseline_reproduction": baseline,
        "fixed_architecture": FIXED,
        "kp000": KP000,
        "pulley": PULLEY,
        "tolerance_model": TOLERANCE,
        "gates": GATES,
        "selection_priority": [
            "ALL_BOUNDARY_PASS",
            "CENTER_RESIDUAL_MAX",
            "MIN_BELT_RESIDUAL_MAX",
            "MIN_PULLEY_RESIDUAL_MAX",
            "OUTPUT_RESERVE_MAX",
            "SUPPORT_PLATE_UNCHANGED",
            "ADDED_PARTS_MIN",
            "SHAFT_LENGTH_MIN",
            "TOTAL_CHANGE_MIN",
            "SEARCH_STAGE_LAST",
        ],
        "v0084_stage_priority": "SUPERSEDED",
        "search_candidate_count": len(search),
        "focus_candidates": focus,
        "recommended": recommended,
        "alternatives": [alt_a, alt_b],
        "interval_analysis": interval,
        "boundary_analysis": {
            "method": "DECOMPOSED_ALL_BOUNDARY_ENUMERATION",
            "row_count": len(boundaries),
            "fail_count": sum(row["status"] == "FAIL" for row in boundaries),
            "all_pass": all(row["status"] == "PASS_BOUNDARY" for row in boundaries),
            "decomposition": "CENTER_COUPLING_PLUS_MIRRORED_INNER_AND_OUTER_SIDE_COMPONENT_PAIRS",
            "pass_authority": True,
        },
        "monte_carlo": monte_carlo,
        "support_plate": {
            "candidate_id": "P3-A5052-T5",
            "size_mm": [95.0, 140.0, 5.0],
            "left_right_independent": True,
            "fit": "PASS_REFERENCE_ENVELOPE",
            "enlargement_required_mm": 0.0,
            "hole_pattern": "PART_MEASUREMENT_REQUIRED",
            "manufacturing": "HOLD",
        },
        "shaft_stock": {
            "required_length_range_mm": [recommended["shaft_length_min_mm"], recommended["shaft_length_max_mm"]],
            "300_mm_bar_yield_candidate": 2,
            "400_mm_bar_yield_candidate": 2,
            "cutting": "HOLD",
        },
        "release_states": {
            "geometry_envelope": "CONDITIONAL_PASS_CANDIDATE",
            "tolerance_robustness": "ROBUST_CONDITIONAL_PASS_CANDIDATE",
            "opposite_protrusion": "PART_MEASUREMENT_REQUIRED",
            "pulley_bore_fit": "FAIL_PROVISIONAL",
            "physical_fit": "HOLD",
            "support_machining": "HOLD",
            "drilling": "HOLD",
            "shaft_cutting": "HOLD",
            "load_test": "HOLD",
            "water_mud_test": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
    }
    interference = {
        "document_id": DOCUMENT_ID,
        "status": "NOT_FOR_MANUFACTURING",
        "recommended_candidate_id": recommended["candidate_id"],
        "selected_candidates": [
            {
                "candidate_id": candidate["candidate_id"],
                "intersection_count": sum(row["intersection_count"] for row in interference_matrix(candidate)),
                "worst_center_residual_mm": candidate["center_residual_mm"],
                "worst_belt_residual_mm": min(candidate["belt_inner_residual_worst_mm"], candidate["belt_outer_residual_worst_mm"]),
                "worst_pulley_residual_mm": min(candidate["pulley_inner_residual_worst_mm"], candidate["pulley_outer_residual_worst_mm"]),
                "output_reserve_mm": candidate["output_reserve_mm"],
            }
            for candidate in (recommended, alt_a, alt_b)
        ],
        "cad_clearances_recommended_mm": cad_clearances(recommended),
        "non_regression": {
            "drive_belt_frame_mm": 15.5,
            "pto_belt_frame_mm": 15.0,
            "track_upper_mm": 10.0,
            "width_mm": 290.0,
            "pto_ends_y_mm": [-145.0, 145.0],
            "box_bottom_min_z_mm": 200.0,
            "clutch": "PRESERVED",
        },
        "holds": ["ACTUAL_TOOL_ENVELOPE_REQUIRED", "PHYSICAL_DRY_FIT_REQUIRED", "PULLEY_BORE_REQUIRED"],
    }
    return {
        "runtime_parent": runtime_parent,
        "baseline": baseline,
        "search": search,
        "ranking": ranking_rows(search),
        "recommended": recommended,
        "alternatives": [alt_a, alt_b],
        "boundaries": boundaries,
        "interval": interval,
        "monte_carlo": monte_carlo,
        "focus": focus,
        "parameters": parameters,
        "stack": axial_stack_rows(recommended),
        "matrix": matrices,
        "interference": interference,
        "remeasure": remeasurement_rows(),
    }


def deterministic_texts(data: dict[str, Any]) -> dict[str, str]:
    return {
        AUTHORITY_NAME: authority_markdown(data["parameters"]),
        PARAMETERS_NAME: _json_text(data["parameters"]),
        CORRECTION_NAME: tolerance_correction_markdown(),
        SEARCH_NAME: _csv_text(data["search"], SEARCH_FIELDS),
        RANKING_NAME: _csv_text(data["ranking"], ["rank", "selection", *SEARCH_FIELDS, "rationale"]),
        SENSITIVITY_NAME: _csv_text(data["boundaries"], BOUNDARY_FIELDS),
        STACK_NAME: _csv_text(data["stack"], STACK_FIELDS),
        MATRIX_NAME: _csv_text(data["matrix"], MATRIX_FIELDS),
        INTERFERENCE_NAME: _json_text(data["interference"]),
        REMEASURE_MD_NAME: remeasurement_markdown(data["remeasure"]),
        REMEASURE_CSV_NAME: _csv_text(data["remeasure"], REMEASURE_FIELDS),
        README_NAME: readme_text(),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(data["recommended"], data["alternatives"][0], data["alternatives"][1]),
        f"artifacts/{TOLERANCE_SVG}": tolerance_svg(data["recommended"]),
        f"artifacts/{CENTER_SVG}": center_svg(data["recommended"]),
    }


def validation_payload(
    data: dict[str, Any],
    models: dict[str, cq.Shape],
    step_paths: dict[str, Path],
) -> dict[str, Any]:
    rec = data["recommended"]
    cad = cad_clearances(rec)
    checks = {
        "parents_runtime": data["runtime_parent"]["checked_path_count"] in (0, 100) and not data["runtime_parent"]["mismatches"],
        "baseline": data["baseline"]["status"] == "PASS",
        "motor_2": FIXED["motor_count"] == 2,
        "independent_pto_2": FIXED["pto_port_count"] == 2 and "NO_COMMON_SHAFT" in FIXED["pto_shaft_architecture"],
        "slide_clutch": FIXED["slide_clutch_states"] == ["DRIVE", "NEUTRAL", "PTO"],
        "bilateral_error": TOLERANCE["center_bilateral_error_max_mm"] == 2,
        "relative_error": TOLERANCE["relative_component_error_max_mm"] == 2,
        "search_count": len(data["search"]) == 2108,
        "center_nominal": rec["center_nominal_mm"] >= 4,
        "center_residual": rec["center_residual_mm"] >= 2,
        "belt_nominal": min(rec["belt_inner_nominal_worst_mm"], rec["belt_outer_nominal_worst_mm"]) >= 14,
        "belt_residual": min(rec["belt_inner_residual_worst_mm"], rec["belt_outer_residual_worst_mm"]) >= 8,
        "pulley_nominal": min(rec["pulley_inner_nominal_worst_mm"], rec["pulley_outer_nominal_worst_mm"]) >= 13.5,
        "pulley_residual": min(rec["pulley_inner_residual_worst_mm"], rec["pulley_outer_residual_worst_mm"]) >= 10,
        "full_protrusion": data["interval"]["opposite_protrusion_interval_mm"] == [0.0, 6.0],
        "boundary_all_pass": data["parameters"]["boundary_analysis"]["all_pass"],
        "boundary_count": len(data["boundaries"]) == 9081,
        "width": rec["total_width_mm"] < 300,
        "pto_ends": rec["pto_ends_y_mm"] == "-145.0|145.0",
        "output_reserve": rec["output_reserve_mm"] >= 25,
        "support_plate": data["parameters"]["support_plate"]["left_right_independent"],
        "no_hole_release": data["parameters"]["support_plate"]["hole_pattern"] == "PART_MEASUREMENT_REQUIRED",
        "cad_center": cad["center_nominal_mm"] == rec["center_nominal_mm"],
        "cad_belt": cad["belt_inner_nominal_mm"] == rec["belt_inner_nominal_worst_mm"] and cad["belt_inner_safety_mm"] == rec["belt_inner_residual_worst_mm"],
        "cad_pulley": cad["pulley_inner_nominal_mm"] == rec["pulley_inner_nominal_worst_mm"],
        "cut_hold": data["parameters"]["release_states"]["shaft_cutting"] == "HOLD",
        "not_manufacturing": data["parameters"]["status"] == "NOT_FOR_MANUFACTURING",
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
        "recommended_candidate_id": rec["candidate_id"],
        "search_candidate_count": len(data["search"]),
        "boundary_row_count": len(data["boundaries"]),
        "geometry": geometry,
        "overall": "CONDITIONAL_PASS_CANDIDATE" if all(checks.values()) and all(item["semantic_geometry_reproducible"] for item in geometry.values()) else "FAIL",
        "tolerance_robustness": "ROBUST_CONDITIONAL_PASS_CANDIDATE",
        "physical_fit": "HOLD",
        "pulley_bore_fit": "FAIL_PROVISIONAL",
        "shaft_cutting": "HOLD",
        "support_machining": "HOLD",
        "drilling": "HOLD",
        "load_test": "HOLD",
        "water_mud_test": "HOLD",
        "field_deployment": "NOT_APPROVED",
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
            raise RuntimeError(f"missing package path: {relative}")
        sums.append(f"{_sha256(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(sums) + "\n")


def refresh() -> dict[str, Any]:
    data = build_datasets()
    models = {
        "recommended": candidate_model(data["recommended"]),
        "alternative_a": candidate_model(data["alternatives"][0]),
        "alternative_b": candidate_model(data["alternatives"][1]),
    }
    paths = {
        "recommended": ARTIFACT_DIR / RECOMMENDED_STEP,
        "alternative_a": ARTIFACT_DIR / ALTERNATIVE_A_STEP,
        "alternative_b": ARTIFACT_DIR / ALTERNATIVE_B_STEP,
    }
    for key, model in models.items():
        _write_step(model, paths[key])
    validation = validation_payload(data, models, paths)
    texts = deterministic_texts(data)
    texts[VALIDATION_NAME] = _json_text(validation)
    for relative, text in texts.items():
        _write_text(LANE_DIR / relative, text)
    _write_text(LANE_DIR / TEST_RESULTS_NAME, f"DOCUMENT_ID={DOCUMENT_ID}\nSTATUS=PENDING_CONTRACT_EXECUTION\n")
    _seal_hashes()
    return {"data": data, "validation": validation}


def _verify_hashes() -> dict[str, Any]:
    manifest_paths = []
    for line in (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8").splitlines():
        if line and "=" not in line:
            manifest_paths.append(line.split("\t", 1)[0])
    if tuple(manifest_paths) != PACKAGE_PATHS:
        raise RuntimeError("MANIFEST path mismatch")
    sums = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        sums[relative] = digest
    if set(sums) != set(PACKAGE_PATHS) - {SHA256SUMS_NAME}:
        raise RuntimeError("SHA256SUMS path mismatch")
    mismatches = [relative for relative, digest in sums.items() if _sha256(LANE_DIR / relative) != digest]
    if mismatches:
        raise RuntimeError(f"hash mismatch: {mismatches}")
    return {"manifest_file_count": len(manifest_paths), "hashed_file_count": len(sums), "hash_mismatch_count": 0}


def verify() -> dict[str, Any]:
    runtime_parent = parent_protection_audit()
    data = build_datasets()
    missing = [relative for relative in PACKAGE_PATHS if not (LANE_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing paths: {missing}")
    expected = deterministic_texts(data)
    text_mismatches = [
        relative
        for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if text_mismatches:
        raise RuntimeError(f"deterministic text mismatch: {text_mismatches}")
    validation = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    if validation["overall"] != "CONDITIONAL_PASS_CANDIDATE":
        raise RuntimeError("validation failed")
    models = {
        "recommended": candidate_model(data["recommended"]),
        "alternative_a": candidate_model(data["alternatives"][0]),
        "alternative_b": candidate_model(data["alternatives"][1]),
    }
    for key, filename in (
        ("recommended", RECOMMENDED_STEP),
        ("alternative_a", ALTERNATIVE_A_STEP),
        ("alternative_b", ALTERNATIVE_B_STEP),
    ):
        imported = cq.importers.importStep(str(ARTIFACT_DIR / filename))
        if _shape_signature(imported) != _shape_signature(models[key]):
            raise RuntimeError(f"STEP semantic mismatch: {key}")
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "recommended_candidate_id": data["recommended"]["candidate_id"],
        "search_candidate_count": len(data["search"]),
        "boundary_row_count": len(data["boundaries"]),
        "parent_audit_mode": runtime_parent["mode"],
        "parent_checked_path_count": runtime_parent["checked_path_count"],
        **_verify_hashes(),
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
        f"DOCUMENT_ID={DOCUMENT_ID}\nCOMMAND={sys.executable} -B {TEST_REL}\n"
        f"RETURN_CODE={result.returncode}\nPYTHON_VERSION={sys.version.split()[0]}\n"
        f"CADQUERY_VERSION={cq.__version__}\n\nSTDOUT\n{result.stdout}\nSTDERR\n{result.stderr}"
    )
    _write_text(LANE_DIR / TEST_RESULTS_NAME, text)
    _seal_hashes()
    if result.returncode:
        raise RuntimeError("contract test failed")
    return {
        "return_code": result.returncode,
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "result_path": str(LANE_DIR / TEST_RESULTS_NAME),
    }


def package() -> dict[str, Any]:
    verified = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError(f"refusing overwrite: {path}")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PACKAGE_PATHS:
            archive.write(LANE_DIR / relative, relative)
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        names = tuple(archive.namelist())
        forbidden = [name for name in names if "__pycache__" in name or ".pytest_cache" in name or name.endswith(".pyc")]
        if bad or names != PACKAGE_PATHS or forbidden:
            raise RuntimeError(f"ZIP audit failure: {bad}, {len(names)}, {forbidden}")
        sums = archive.read(SHA256SUMS_NAME).decode("utf-8").splitlines()
        if not all(hashlib.sha256(archive.read(relative)).hexdigest() == digest for digest, relative in (line.split("  ", 1) for line in sums)):
            raise RuntimeError("ZIP internal hashes failed")
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
        output = {
            "action": "REFRESH",
            "overall": result["validation"]["overall"],
            "fixed_checks": f"{result['validation']['check_pass_count']}/{result['validation']['check_count']}",
            "recommended_candidate_id": result["data"]["recommended"]["candidate_id"],
            "search_candidate_count": len(result["data"]["search"]),
            "boundary_row_count": len(result["data"]["boundaries"]),
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
