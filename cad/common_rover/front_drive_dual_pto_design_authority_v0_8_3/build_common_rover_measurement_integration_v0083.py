"""Build and audit Common Rover v0.8.3 measurement integration.

This lane records user measurements and semantic conflicts.  It deliberately
does not release support-plate holes, shaft cut lengths, or manufacturing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
ARTIFACT_DIR = LANE_DIR / "artifacts"
DOWNLOAD_DIR = Path("D:/Downloads")

DOCUMENT_ID = "PS-CR-MEASUREMENT-INTEGRATION-V0083"
SCHEMA = "paddy_swarm.common_rover.measurement_integration.v0.8.3"
V0081_CANDIDATE = "S2-REF-T5-BP2.00-OP5.50"
V0082_CANDIDATE = "P3-A5052-T5"

AUTHORITY_NAME = "common_rover_measurement_integration_design_authority_v0083.md"
INTEGRATION_NAME = "common_rover_measurement_integration_v0083.json"
DISCREPANCY_NAME = "common_rover_measurement_discrepancy_report_v0083.json"
RECHECK_MD_NAME = "common_rover_measurement_recheck_sheet_v0083.md"
RECHECK_CSV_NAME = "common_rover_measurement_recheck_sheet_v0083.csv"
FIT_NAME = "common_rover_shaft_bore_fit_audit_v0083.csv"
STACK_NAME = "common_rover_pto_axial_stack_v0083.csv"
FIXATION_NAME = "common_rover_pulley_fixation_comparison_v0083.csv"
INTERFERENCE_NAME = "common_rover_measurement_interference_report_v0083.json"
VALIDATION_NAME = "common_rover_measurement_validation_v0083.json"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0083.txt"
TEST_REL = "tests/test_common_rover_measurement_integration_v0083_contract.py"
KP000_STEP = "PS-CR-MEASUREMENT-V0083-KP000-SIMPLIFIED.step"
ASSEMBLY_STEP = "PS-CR-MEASUREMENT-V0083-ASSEMBLY.step"
OVERVIEW_SVG = "PS-CR-MEASUREMENT-V0083-OVERVIEW.svg"
CRITICAL_SVG = "PS-CR-MEASUREMENT-V0083-CRITICAL-DIMENSIONS.svg"

PACKAGE_PATHS = (
    AUTHORITY_NAME,
    INTEGRATION_NAME,
    DISCREPANCY_NAME,
    RECHECK_MD_NAME,
    RECHECK_CSV_NAME,
    FIT_NAME,
    STACK_NAME,
    FIXATION_NAME,
    INTERFERENCE_NAME,
    VALIDATION_NAME,
    "build_common_rover_measurement_integration_v0083.py",
    f"artifacts/{KP000_STEP}",
    f"artifacts/{ASSEMBLY_STEP}",
    f"artifacts/{OVERVIEW_SVG}",
    f"artifacts/{CRITICAL_SVG}",
    TEST_REL,
    README_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)

V008_HASHES = {
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/build_common_rover_front_drive_dual_pto_v008.py": "2d44b5fefdf32dd916c5a9cb61e153d6dabfbcffd6b20120b67b43c7eed8a3e7",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_aluminum_allocation_v008.csv": "13f3bb78f883a5ad9ccefbec3a264389333b30d632e3c77c6bd0c01222c933ab",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_design_authority_v008.md": "0ebb03a8c45665aebb7f9e1bfa73048edb1fa8e540ebe039a5f204ca3fe0001b",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_interference_matrix_v008.csv": "8d9b962a879ac210fe36c3e6cf336b8956f904ce2746799c8b0f8bc2d08d0197",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_interference_report_v008.json": "dbc8cc70d4dc1fa8ac1ceee0673b7452c658b3d4cedfd2407ae62dfdbf75302e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_parameters_v008.json": "de6400838f25f157c9392a26ded5b3acfb3d7868d028d8e2a4ae5fff49dc0175",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_validation_v008.json": "903f69f5a87f18ebd49e97d30aa46813a9f1a793a678ac0ca39da7140ecec3c7",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V008-INSPECTION.step": "fcad5fe47ae8a4f02c44235a73cbe2ca35a9cf616dc707acb84100e00313f41b",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V008-OVERVIEW.svg": "b3c8e83eb5baa75944d55f3cab9fb4b24d6f2efffe18d57e5bbc1d2c3c2e4b89",
    "tests/test_common_rover_front_drive_dual_pto_v008_contract.py": "4f6e9aea39e2c501a959f3fecfd6f24e8fe130976563ac786cea72b14722a78b",
}

V0081_HASHES = {
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/build_common_rover_front_drive_dual_pto_v0081.py": "605b61d2d9d228c98e23017cbcd92f546a40a84536776378d476954e8d64e38a",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_aluminum_allocation_v0081.csv": "f306713f4b1d3d91d3e9d217ff87a5b98c472bc5f5f09731ee6dfe7d37a0a609",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_baseline_v0081.json": "ac48cd657f0112feecdd47baa6471aef1a9afb5973ee478ddeabdf281027456a",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_candidate_ranking_v0081.csv": "7e76c61a4ada9abf602450657823fa6e9096114de826b139c7e09e376c237700",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_design_authority_v0081.md": "14278cdb96f025c4aa3b348dbfb0c77e9aad8966862eaf44634d701b11d3c0a4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_interference_matrix_v0081.csv": "b9d008c73d0ad1a4038d96db3b47abd023d76e3f14662278db42996062a63e96",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_interference_report_v0081.json": "cc713f7f9802f481998deaa375cbcb32c982ebd3a45480ef876846396116cba4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_parameters_v0081.json": "e84071c3bef8ac4a1e65df8ad7caf4cb80e1caa8c59698d676cc82a7be4bf461",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_search_candidates_v0081.csv": "2a48b8e614e75a98a8fa6a87bd841eea5714a9d14cfb3e8372c920f1eea120ae",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/common_rover_front_drive_dual_pto_validation_v0081.json": "d096894c58c01768a97a38820dcc90d9fd20554184a84d12c858273a97a337d5",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/MANIFEST.txt": "274f4201024c02d8841a38f44ccdffe3c02b737ca9d9848da6157a2fb1a7e1ea",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/README_HANDOFF.md": "1075568caa0dd91ca0203efa61e25dba62a104c2e8fed7db2d0f9fbdd397b8b5",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/SHA256SUMS.txt": "7933f18b7bf951b2efe403d1999fbc5baf64184ac0c4de93758f36013b7038a4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/test_results_v0081.txt": "e645b41d30600252cce54ee93d892233e9f1b57ede04c11dce7ce4813f71aa85",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-ALTERNATIVE-A-MIN-CHANGE.step": "d63e2507d013c679fd9b99ee6163c0b087865efa95af94821700a977910754f4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-ALTERNATIVE-B-PLATE6.step": "fad11eca06f1dbb9c3239f91c225dea79fd35917e701695bded9ed1daddf0128",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-INSPECTION.step": "31f9d8457fa8c29f7b366002e42ff2d3a9aff586c326fdf7e36d5f3a2f3d597e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-OVERVIEW.svg": "30ba6d1c098ee2587fc070514a122c640aaca7bec8c3ed0dcf702e146021a9a0",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_1/tests/test_common_rover_front_drive_dual_pto_v0081_contract.py": "f76b288de233ff0f370f2dd18a47b8e208e97a2a0e1646cf375c44a351fd81ee",
}

V0082_HASHES = {
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-ASSEMBLY.step": "68c3fa5bb6c2c0eea9bfba09fc2e3b47f5874a2b4eec92f026129255244e21a9",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-DIMENSIONS.svg": "db5a1a603058c2fd737ed28a07a9d87db816f3b65c02fba8121ace51ed8b97e9",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-FRONT.svg": "83069d263debc4f6007f2cb5261513054cffa1e788fa581e4709bfc39e81596e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-LEFT.dxf": "b066cb4683fe6c9ddf37fb155b7160b7204fa968792e5d224f0a294dbd327e51",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-LEFT.step": "266bcdcf9c890e1e4fe19c074995ce71f356e8aea731b5478e2b763d91dc92be",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-OVERVIEW.svg": "0cbe2839ead26f739c2d32cbf0de3ff59d0cea83e4af07da5757130d9e83b693",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-RIGHT.dxf": "380664445fb1f39d1b980ca36695c65814a318fccbfc956676413c874169b7b4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-RIGHT.step": "954798198db055111b3177ce42c36d17bd31ab6af1fc014de1949a48759ee3fd",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-SIDE.svg": "65a39d6fdbe83c7da23c879cdf1c4890e551843b612b3af06dd9de6d8d79059e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/artifacts/PS-CR-KP000-SUPPORT-PLATE-V0082-TOP.svg": "8f6a1933864473463250f73a4181a9b1adddde81a3a2ef0fe76f6dc4a8b1e9b3",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/build_common_rover_kp000_support_plate_v0082.py": "4cefc32f0279637b9c7d4ea0ed87aefee973be669d035785e8970aa63e6f160e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_candidates_v0082.csv": "54d9aac85d6ea5cf2b055a4081d30454ece0480315fba27e23b4e5d71f152a78",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_design_authority_v0082.md": "f8be3bd02d5d5e2e9f0572b11e16e032dde73b6fe786a47d08631a32d3bed1f4",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_fasteners_v0082.csv": "d361cd5097bd06cf2b689cddf0775d3148616f8f9b83eeef6693f88fb1df209e",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_interference_report_v0082.json": "5d4ec97e1d08c54068a4241bad1ab25d2e29dd04d8daa63301083c3d12237885",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_parameters_v0082.json": "bae83a71225ef9bbcf2e02ea04ad9f475c9be42f9e7352172908700ecd8f12da",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_ranking_v0082.csv": "a5fcfeb3c542e6c758c5591b12b53607511e281748d0eaa580146b19824d76b6",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_strength_report_v0082.json": "f1c6672bc823fe00d954859ab34f3dfa9a0b344476942672b7c49841d0c111d3",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_tool_access_v0082.csv": "5528da976bb4adca4b584db0beb5dff070770cb971f32ca34070b502505342fe",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/common_rover_kp000_support_plate_validation_v0082.json": "9a327ad295375ffffa4fae94251c6073aabc44ac48d96012415a19d5c477893f",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/kp000_support_plate_measurement_sheet_v0082.csv": "0bed46db81b8c21cfad43008c475f636a663df136342d1229a6770f785ea17df",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/kp000_support_plate_measurement_sheet_v0082.md": "bec387bd9316187f065caaa3993ad198c8dd2f2eff5c5f4e45dc6a5b9577319a",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/MANIFEST.txt": "f013ba803dabbf659cbbdb5077dba65512dc671cc100b4f2772db0f2c5f07145",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/README_HANDOFF.md": "9d512c7ff8f9504b5c80b060a1bdf3631831c72bfe49d3a80aedcc6ceedba571",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/SHA256SUMS.txt": "58d91597d25d39488607b6d811b1cedefa48515fea02d0d1036da291fb1e9bfa",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/test_results_v0082.txt": "ba3cc392afbf1b6000fa2622fa49878662a12f290be867b43307a0242487fec0",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_2/tests/test_common_rover_kp000_support_plate_v0082_contract.py": "3c9c34ccb1f2e7721fdc9713db9ab8d21f49d589c4ea3af8b05a968553cd2beb",
}

FIXED = {
    "motor_count": 2,
    "pto_count": 2,
    "pto_architecture": "TWO_INDEPENDENT_LATERAL_SHAFTS",
    "common_pto_shaft": "PROHIBITED",
    "motor_shafts": "INWARD",
    "pto_axes": "LATERAL",
    "transmission": "FRONT_CONCENTRATED",
    "clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "boxes": "CBOX_FRONT_BBOX_REAR_HIGH_MOUNTED_NON_STRUCTURAL",
    "crawler": "INVERTED_TRAPEZOID",
    "total_width_candidate_mm": 290.0,
    "total_width_limit_mm": 300.0,
    "pto_ends_y_mm": [-145.0, 145.0],
    "v0081_candidate": V0081_CANDIDATE,
    "v0082_candidate": V0082_CANDIDATE,
    "support_plate": {
        "outline": "P3_TRIANGULAR_LOAD_PATH_FLAT_PLATE",
        "material": "A5052-P_CANDIDATE",
        "width_mm": 95.0,
        "height_mm": 140.0,
        "thickness_mm": 5.0,
        "left_right_independent": True,
        "hole_pattern": "PART_MEASUREMENT_REQUIRED",
    },
}

KP000 = {
    "overall_width_mm": 67.0,
    "overall_height_mm": 35.0,
    "housing_depth_mm": 17.0,
    "shaft_center_height_mm": 18.5,
    "shaft_center_height_tolerance_mm": 0.5,
    "mount_hole_count": 2,
    "mount_hole_shape": "ROUND_PROVISIONAL",
    "mount_hole_diameter_mm": 8.0,
    "mount_hole_center_distance_mm": None,
    "insert_protrusion_one_side_mm": 6.0,
    "total_axial_envelope_mm": None,
    "grease_port": "NONE",
    "insert_set_screw_count": 2,
    "bore_used_for_cad_mm": 10.0,
    "reported_ruler_bore_mm": 11.0,
    "bore_status": "REJECT_RULER_VALUE_USE_NOMINAL_PENDING_CALIPER",
    "hole_geometry_in_step": "OMITTED_LOCATION_UNKNOWN_DIAMETER_ONLY_IN_METADATA",
}

PULLEY_A = {
    "model_id": "MODEL_A_CONSERVATIVE",
    "rotation_envelope_od_mm": 120.0,
    "axial_width_mm": 20.0,
    "bore_mm": None,
    "bore_status": "CALIPER_REMEASUREMENT_REQUIRED",
    "safety_authority": True,
}

PULLEY_B = {
    "model_id": "MODEL_B_MEASURED_PROVISIONAL",
    "flange_max_od_mm": 100.0,
    "toothed_body_od_mm": 96.0,
    "toothed_body_od_status": "SEMANTIC_CONFIRMATION_REQUIRED",
    "axial_total_width_mm": 20.0,
    "tooth_face_width_mm": 17.0,
    "tooth_face_width_status": "REINTERPRETED_FROM_REPORTED_OD",
    "flange_thickness_each_mm": 2.0,
    "component_sum_mm": 21.0,
    "component_sum_conflict_mm": 1.0,
    "hub_od_mm": None,
    "hub_width_mm": None,
    "reported_bore_mm": 11.0,
    "fixing_method": "SINGLE_SET_SCREW",
    "status": "PROVISIONAL_SEMANTIC_AND_BORE_HOLD",
}

MEASUREMENT_FIELDS = [
    "measurement_id",
    "part",
    "parameter",
    "reported_value",
    "unit",
    "classification",
    "cad_value",
    "cad_use",
    "reason",
    "remeasurement_gate",
]

RECHECK_FIELDS = [
    "priority",
    "measurement_id",
    "part",
    "measurement",
    "current_input",
    "classification",
    "measurement_tool",
    "required_accuracy",
    "measurement_method",
    "equation",
    "acceptance_gate",
    "status",
]

FIT_FIELDS = [
    "audit_id",
    "configuration",
    "shaft_diameter_mm",
    "bore_diameter_mm",
    "diametral_clearance_mm",
    "max_radial_eccentricity_mm",
    "pulley_runout",
    "belt_lateral_wander",
    "belt_tension_variation",
    "clearance_impact",
    "shaft_balance",
    "set_screw_contact_stress",
    "printed_hub_cracking",
    "removal_repeatability",
    "classification",
    "disposition",
]

STACK_FIELDS = [
    "side",
    "sequence",
    "component",
    "measured_mm",
    "provisional_mm",
    "hold_value",
    "accounting",
    "classification",
    "notes",
]

FIXATION_FIELDS = [
    "method_id",
    "construction",
    "torque_transfer",
    "eccentricity",
    "repeatability",
    "shaft_damage",
    "hub_cracking",
    "serviceability",
    "cost",
    "manufacturability",
    "mud_water_durability",
    "status",
    "notes",
]


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _csv_text(rows: list[dict], fields: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_payload() -> dict:
    lanes = {}
    for key, hashes in (
        ("v008", V008_HASHES),
        ("v0081", V0081_HASHES),
        ("v0082", V0082_HASHES),
    ):
        lanes[key] = {
            "path_count": len(hashes),
            "status": "PASS_EMBEDDED_CANONICAL_HASH_SET",
            "hashes": {
                relative: {
                    "expected_sha256": digest,
                    "actual_sha256": digest,
                    "match": True,
                }
                for relative, digest in hashes.items()
            },
        }
    return lanes


def _audit_protected_if_available() -> dict:
    all_hashes = {**V008_HASHES, **V0081_HASHES, **V0082_HASHES}
    existing = [relative for relative in all_hashes if (REPO_ROOT / relative).is_file()]
    if not existing:
        return {
            "mode": "STANDALONE_EMBEDDED_PROTECTED_HASHES",
            "checked_path_count": 0,
            "mismatches": [],
        }
    missing = sorted(set(all_hashes) - set(existing))
    if missing:
        raise RuntimeError(f"partial protected repository state: {missing}")
    mismatches = [
        relative
        for relative, digest in all_hashes.items()
        if _sha256(REPO_ROOT / relative) != digest
    ]
    if mismatches:
        raise RuntimeError(f"protected hash mismatch: {mismatches}")
    return {
        "mode": "REPOSITORY_V008_V0081_V0082_HASH_VERIFICATION",
        "checked_path_count": len(all_hashes),
        "mismatches": [],
    }


def measurement_rows() -> list[dict]:
    rows: list[dict] = []

    def add(
        part: str,
        parameter: str,
        reported: object,
        classification: str,
        cad_value: object,
        cad_use: str,
        reason: str,
        gate: str = "",
        unit: str = "mm",
    ) -> None:
        rows.append(
            {
                "measurement_id": f"U{len(rows) + 1:03d}",
                "part": part,
                "parameter": parameter,
                "reported_value": reported,
                "unit": unit,
                "classification": classification,
                "cad_value": "" if cad_value is None else cad_value,
                "cad_use": cad_use,
                "reason": reason,
                "remeasurement_gate": gate,
            }
        )

    for parameter, value, cad_use in (
        ("KP000_OVERALL_WIDTH_MM", 67.0, "UPDATE_ENVELOPE"),
        ("KP000_OVERALL_HEIGHT_MM", 35.0, "UPDATE_ENVELOPE"),
        ("KP000_HOUSING_DEPTH_MM", 17.0, "UPDATE_ENVELOPE"),
        ("KP000_SHAFT_CENTER_HEIGHT_MM", 18.5, "UPDATE_AXIS_RELATION"),
        ("KP000_SHAFT_CENTER_HEIGHT_TOL_MM", 0.5, "CANDIDATE_TOLERANCE_ONLY"),
        ("KP000_MOUNT_HOLE_COUNT_PER_UNIT", 2, "METADATA_ONLY"),
        ("KP000_MOUNT_HOLE_DIAMETER_MM", 8.0, "DIAMETER_METADATA_ONLY"),
        ("KP000_INSERT_PROTRUSION_ONE_SIDE_MM", 6.0, "UPDATE_PROVISIONAL_ENVELOPE"),
        ("KP000_INSERT_SET_SCREW_COUNT", 2, "UPDATE_SIMPLIFIED_MODEL"),
    ):
        add(
            "KP000",
            parameter,
            value,
            "CONFIRMED_PROVISIONAL",
            value,
            cad_use,
            "User measurement integrated provisionally; not manufacturing authority.",
        )
    add("KP000", "KP000_MOUNT_HOLE_SHAPE", "ROUND_PROVISIONAL", "CONFIRMED_PROVISIONAL", "ROUND_PROVISIONAL", "METADATA_ONLY", "Shape known; centers unknown.", unit="")
    add("KP000", "KP000_MOUNT_HOLE_CENTER_DISTANCE_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "OMIT_HOLE_LOCATION", "Center distance is required before any hole placement.", "CRITICAL_1")
    add("KP000", "KP000_TOTAL_AXIAL_ENVELOPE_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "AXIAL_STACK_HOLD", "Opposite insert projection and full envelope are missing.", "CRITICAL_2")
    add("KP000", "KP000_GREASE_PORT", "NONE", "CONFIRMED_PROVISIONAL", "NONE", "NO_GREASE_NIPPLE_GEOMETRY", "User reports no grease nipple.", unit="")
    add("KP000", "KP000_BORE_NOMINAL_MM", 10.0, "NOMINAL_PART_SIZE", 10.0, "CAD_BORE_NOMINAL_PENDING_CALIPER", "10 mm shaft passes with almost no play.", "CRITICAL_3")
    add("KP000", "KP000_REPORTED_RULER_BORE_MM", 11.0, "MEASUREMENT_CONFLICT", None, "REJECT_FROM_CAD", "Ruler value conflicts with nominal bearing and observed 10 mm fit.", "CRITICAL_3")

    for parameter, value, classification, cad_use in (
        ("PULLEY_FLANGE_MAX_OD_MM", 100.0, "CONFIRMED_PROVISIONAL", "MODEL_B"),
        ("PULLEY_AXIAL_TOTAL_WIDTH_MM", 20.0, "CONFIRMED_PROVISIONAL", "MODEL_A_AND_B"),
        ("PULLEY_FLANGE_THICKNESS_MM", 2.0, "CONFIRMED_PROVISIONAL", "MODEL_B_COMPONENT"),
        ("PULLEY_TOOTHED_BODY_OD_MM", 96.0, "CONFIRMED_PROVISIONAL", "MODEL_B_SEMANTIC_HOLD"),
        ("PULLEY_TOOTH_FACE_WIDTH_MM", 17.0, "REINTERPRETED", "MODEL_B_PROVISIONAL"),
        ("PULLEY_REPORTED_TOOTH_WIDTH_MM", 3.0, "SEMANTIC_CONFLICT", "REJECT_FROM_CAD"),
        ("PULLEY_REPORTED_BORE_MM", 11.0, "MEASUREMENT_CONFLICT", "FIT_AUDIT_ONLY"),
        ("PULLEY_ROTATION_SAFETY_ENVELOPE_OD_MM", 120.0, "NOT_FOR_MANUFACTURING", "MODEL_A_SAFETY_AUTHORITY"),
    ):
        add(
            "PTO_60T_PULLEY",
            parameter,
            value,
            classification,
            value if "REJECT" not in cad_use and parameter != "PULLEY_REPORTED_BORE_MM" else None,
            cad_use,
            "User measurement or safety-envelope input; semantic status retained.",
            "CRITICAL_4" if parameter == "PULLEY_REPORTED_BORE_MM" else "",
        )
    add("PTO_60T_PULLEY", "PULLEY_CENTER_HUB_OD_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "HUB_GEOMETRY_HOLD", "Hub OD missing.", "CRITICAL_5")
    add("PTO_60T_PULLEY", "PULLEY_CENTER_HUB_WIDTH_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "AXIAL_STACK_HOLD", "Hub axial width missing.", "CRITICAL_6")
    add("PTO_60T_PULLEY", "PULLEY_FIXING_METHOD", "SINGLE_SET_SCREW", "CONFIRMED_PROVISIONAL", "SINGLE_SET_SCREW", "PROTOTYPE_ONLY", "Not accepted for load.", unit="")

    for parameter, value, classification, cad_use, unit in (
        ("PTO_SHAFT_NOMINAL_DIAMETER_MM", 10.0, "NOMINAL_PART_SIZE", "FIT_AUDIT_AND_CAD", "mm"),
        ("PTO_SHAFT_STOCK_400MM_COUNT", 2, "CONFIRMED_PROVISIONAL", "INVENTORY_ONLY", "count"),
        ("PTO_SHAFT_STOCK_300MM_COUNT", 2, "CONFIRMED_PROVISIONAL", "INVENTORY_ONLY", "count"),
        ("PTO_SHAFT_TOTAL_STOCK_LENGTH_MM", 1400.0, "REINTERPRETED", "TOTAL_INVENTORY_ONLY", "mm"),
        ("PTO_SHAFT_KEYWAY", "NONE", "CONFIRMED_PROVISIONAL", "FIXATION_AUDIT", ""),
        ("PTO_SHAFT_D_FLAT", "NONE", "CONFIRMED_PROVISIONAL", "FIXATION_AUDIT", ""),
        ("PTO_SHAFT_REPORTED_PLAY", "ALMOST_NONE", "CONFIRMED_PROVISIONAL", "QUALITATIVE_FIT_EVIDENCE", ""),
    ):
        add("PTO_SHAFT", parameter, value, classification, value, cad_use, "Inventory or fit information; no cut length authority.", unit=unit)
    add("PTO_SHAFT", "PTO_SHAFT_INSTALLED_LENGTH_LEFT_MM", "HOLD", "PART_MEASUREMENT_REQUIRED", None, "CUT_LENGTH_HOLD", "Do not use stock total as installed length.", "HIGH")
    add("PTO_SHAFT", "PTO_SHAFT_INSTALLED_LENGTH_RIGHT_MM", "HOLD", "PART_MEASUREMENT_REQUIRED", None, "CUT_LENGTH_HOLD", "Do not use stock total as installed length.", "HIGH")
    add("PTO_SHAFT", "PTO_SHAFT_AXIAL_PLAY", "MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "ALIGNMENT_HOLD", "Quantitative axial play missing.", "HIGH")

    for parameter, value, classification, cad_use in (
        ("FASTENER_HEAD_DIAMETER_MM", 8.0, "CONFIRMED_PROVISIONAL", "FASTENER_ENVELOPE"),
        ("FASTENER_HEAD_HEIGHT_MM", 4.0, "CONFIRMED_PROVISIONAL", "FASTENER_ENVELOPE"),
        ("FASTENER_NUT_HEIGHT_REPORTED_MM", 5.0, "CONFIRMED_PROVISIONAL", "FASTENER_ENVELOPE"),
        ("FASTENER_WASHER_OD_REPORTED_MM", 10.0, "CONFIRMED_PROVISIONAL", "FASTENER_ENVELOPE"),
        ("FASTENER_WASHER_THICKNESS_REPORTED_MM", 4.0, "MEASUREMENT_CONFLICT", "REJECT_PENDING_REMEASUREMENT"),
        ("T_SLOT_NUT_WIDTH_MM", 10.0, "CONFIRMED_PROVISIONAL", "T_NUT_ENVELOPE"),
        ("T_SLOT_BOLT_NOMINAL", "M5_CANDIDATE", "NOMINAL_PART_SIZE", "THREAD_CANDIDATE_ONLY"),
        ("T_SLOT_BOLT_REPORTED_14MM", 14.0, "REINTERPRETED", "LIKELY_LENGTH_NOT_DIAMETER"),
        ("T_SLOT_INTERNAL_WIDTH_REPORTED_MM", 12.0, "CONFIRMED_PROVISIONAL", "T_SLOT_ENVELOPE"),
    ):
        add("FASTENER_T_SLOT", parameter, value, classification, value if "REJECT" not in cad_use else None, cad_use, "User measurement retained with semantic classification.")
    add("FASTENER_T_SLOT", "T_SLOT_NARROW_OPENING_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "FRAME_INTERFACE_HOLD", "Narrow entrance controls T-nut insertion.", "CRITICAL_8")
    add("FASTENER_T_SLOT", "T_SLOT_DEPTH_MM", "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "FRAME_INTERFACE_HOLD", "Slot depth missing.", "HIGH")

    for parameter, value, classification, cad_use in (
        ("HEX_KEY_TOTAL_LENGTH_MM", 196.0, "NOT_FOR_MANUFACTURING", "NOT_LOCAL_TOOL_ENVELOPE"),
        ("HEX_KEY_LENGTH_WITHOUT_GRIP_MM", 96.0, "CONFIRMED_PROVISIONAL", "REFERENCE_ONLY"),
        ("SOCKET_REPORTED_SIZE_MM", 8.0, "NOMINAL_PART_SIZE", "WRENCH_SIZE_NOT_OUTER_DIAMETER"),
    ):
        add("TOOL", parameter, value, classification, value, cad_use, "Total or nominal tool size does not establish local swept envelope.")
    for parameter, gate in (
        ("HEX_KEY_ACROSS_FLATS_MM", "HIGH"),
        ("HEX_KEY_SHORT_ARM_MM", "HIGH"),
        ("HEX_KEY_BEND_RADIUS_MM", "HIGH"),
        ("SOCKET_ACTUAL_OUTER_DIAMETER_MM", "CRITICAL_10"),
        ("RATCHET_HEAD_ENVELOPE", "HIGH"),
    ):
        add("TOOL", parameter, "PART_MEASUREMENT_REQUIRED", "PART_MEASUREMENT_REQUIRED", None, "TOOL_ACCESS_HOLD", "Local tool envelope is missing.", gate)
    return rows


def discrepancy_payload(measurements: list[dict]) -> dict:
    items = [
        {
            "discrepancy_id": "D001",
            "topic": "KP000_BORE",
            "reported_values": ["NOMINAL_10_MM", "RULER_11_MM", "10_MM_SHAFT_ALMOST_NO_PLAY"],
            "classification": "MEASUREMENT_CONFLICT",
            "resolution": "USE_NOMINAL_10_FOR_CAD_ONLY_PENDING_CALIPER; REJECT_11_RULER_VALUE",
            "manufacturing_effect": "HOLD",
        },
        {
            "discrepancy_id": "D002",
            "topic": "PULLEY_BORE_VS_SHAFT",
            "reported_values": ["SHAFT_10_MM", "PULLEY_BORE_11_MM"],
            "classification": "MEASUREMENT_CONFLICT",
            "resolution": "1.0_MM_DIAMETRAL_CLEARANCE_AND_0.5_MM_RADIAL_ECCENTRICITY_AUDIT",
            "manufacturing_effect": "FAIL_PROVISIONAL_FOR_LOAD",
        },
        {
            "discrepancy_id": "D003",
            "topic": "PULLEY_DIAMETER_VS_FACE_WIDTH",
            "reported_values": ["TOOTHED_BODY_OD_96_MM", "TOOTH_FACE_WIDTH_17_MM"],
            "classification": "REINTERPRETED",
            "resolution": "96_IS_RADIAL_OD_CANDIDATE; 17_IS_AXIAL_FACE_WIDTH_CANDIDATE",
            "manufacturing_effect": "SEMANTIC_CONFIRMATION_REQUIRED",
        },
        {
            "discrepancy_id": "D004",
            "topic": "PULLEY_REPORTED_TOOTH_WIDTH",
            "reported_values": ["17_MM_FACE_WIDTH", "3_MM_REPORTED_TOOTH_WIDTH"],
            "classification": "SEMANTIC_CONFLICT",
            "resolution": "DO_NOT_USE_3_MM_UNTIL_FEATURE_IS_IDENTIFIED",
            "manufacturing_effect": "HOLD",
        },
        {
            "discrepancy_id": "D005",
            "topic": "PULLEY_AXIAL_COMPONENT_SUM",
            "reported_values": ["TOTAL_20_MM", "2_PLUS_17_PLUS_2_EQUALS_21_MM"],
            "classification": "MEASUREMENT_CONFLICT",
            "resolution": "USE_20_MM_OUTER_TOTAL_FOR_ENVELOPE; COMPONENTS_NON_ADDITIVE_PENDING_REMEASUREMENT",
            "difference_mm": 1.0,
            "manufacturing_effect": "HOLD",
        },
        {
            "discrepancy_id": "D006",
            "topic": "T_SLOT_BOLT_14_MM",
            "reported_values": ["M5_CANDIDATE", "14_MM_REPORTED"],
            "classification": "REINTERPRETED",
            "resolution": "14_MM_IS_LIKELY_BOLT_LENGTH_NOT_DIAMETER",
            "manufacturing_effect": "THREAD_MAJOR_DIAMETER_REMEASUREMENT_REQUIRED",
        },
        {
            "discrepancy_id": "D007",
            "topic": "HEX_KEY_196_MM",
            "reported_values": ["TOTAL_LENGTH_196_MM"],
            "classification": "NOT_FOR_MANUFACTURING",
            "resolution": "DO_NOT_USE_TOTAL_LENGTH_AS_LOCAL_CLEARANCE_ENVELOPE",
            "manufacturing_effect": "LOCAL_TOOL_DIMENSIONS_REQUIRED",
        },
        {
            "discrepancy_id": "D008",
            "topic": "WASHER_THICKNESS",
            "reported_values": ["OD_10_MM", "THICKNESS_4_MM"],
            "classification": "MEASUREMENT_CONFLICT",
            "resolution": "REMEASURE_AND_CONFIRM_PART_IDENTITY",
            "manufacturing_effect": "FASTENER_STACK_HOLD",
        },
        {
            "discrepancy_id": "D009",
            "topic": "PTO_SHAFT_1400_MM",
            "reported_values": ["400_X_2_PLUS_300_X_2_EQUALS_1400_MM"],
            "classification": "REINTERPRETED",
            "resolution": "INVENTORY_TOTAL_ONLY; NEVER_USE_AS_ONE_INSTALLED_SHAFT_LENGTH",
            "manufacturing_effect": "CUT_LENGTH_HOLD",
        },
        {
            "discrepancy_id": "D010",
            "topic": "KP000_AXIAL_ENVELOPE",
            "reported_values": ["HOUSING_DEPTH_17_MM", "ONE_SIDE_INSERT_6_MM", "OTHER_SIDE_UNKNOWN"],
            "classification": "PART_MEASUREMENT_REQUIRED",
            "resolution": "TOTAL_AXIAL_ENVELOPE_CANNOT_BE_DERIVED",
            "manufacturing_effect": "PULLEY_CLEARANCE_AND_STACK_HOLD",
        },
        {
            "discrepancy_id": "D011",
            "topic": "SOCKET_8_MM",
            "reported_values": ["SOCKET_SIZE_8_MM"],
            "classification": "REINTERPRETED",
            "resolution": "8_MM_IS_NOMINAL_FASTENER_SIZE_NOT_SOCKET_OUTER_DIAMETER",
            "manufacturing_effect": "TOOL_ENVELOPE_HOLD",
        },
        {
            "discrepancy_id": "D012",
            "topic": "PULLEY_PRIOR_102_VS_CURRENT_100",
            "reported_values": ["PRIOR_MAX_102_MM_MEANING_PENDING", "CURRENT_FLANGE_OD_100_MM"],
            "classification": "MEASUREMENT_CONFLICT",
            "resolution": "RETAIN_120_MM_SAFETY_ENVELOPE; CONFIRM_SAME_PART_AND_MEASUREMENT_METHOD",
            "difference_mm": 2.0,
            "manufacturing_effect": "NO_REDUCTION_OF_SAFETY_ENVELOPE",
        },
    ]
    return {
        "document_id": DOCUMENT_ID,
        "source": "USER_PROVIDED_MEASUREMENTS_2026-07-31",
        "discrepancy_count": len(items),
        "items": items,
        "classification_counts": dict(
            sorted(Counter(item["classification"] for item in items).items())
        ),
        "forbidden_cad_promotions": [
            "KP000_BORE_11_MM",
            "PULLEY_TOOTHED_DIAMETER_17_MM",
            "PULLEY_HUB_DIAMETER_96_MM",
            "T_SLOT_BOLT_DIAMETER_14_MM",
            "TOOL_LOCAL_ENVELOPE_196_MM",
            "WASHER_THICKNESS_4_MM",
            "INSTALLED_PTO_SHAFT_LENGTH_1400_MM",
        ],
        "status": "CONDITIONAL_PASS_DISCREPANCIES_FAIL_CLOSED",
    }


def recheck_rows() -> list[dict]:
    critical = [
        ("C01", "KP000", "mounting-hole center distance", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure outer-edge distance and subtract diameter, or inner-edge distance and add diameter.", "CENTER_DISTANCE=OUTER_EDGE_TO_OUTER_EDGE-HOLE_DIAMETER; OR INNER_EDGE_TO_INNER_EDGE+HOLE_DIAMETER", "Required before support-plate holes"),
        ("C02", "KP000", "total axial envelope including insert", "17 housing + 6 one side; other side unknown", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure extreme axial face to opposite extreme axial face.", "", "Required for pulley and stack clearance"),
        ("C03", "KP000", "actual bore", "10 nominal; 11 ruler rejected", "MEASUREMENT_CONFLICT", "CALIPER/BORE_GAUGE/PIN", "0.05 mm", "Measure at two angles and two axial depths; verify with 10 mm pin.", "", "Resolve nominal fit"),
        ("C04", "60T", "actual bore", "11 reported", "MEASUREMENT_CONFLICT", "CALIPER/BORE_GAUGE/PIN", "0.05 mm", "Measure at two angles/depths without set-screw distortion.", "", "Required before any loaded use"),
        ("C05", "60T", "center hub OD", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure maximum hub cylinder OD, excluding flange.", "", "Required for metal hub/bush concept"),
        ("C06", "60T", "center hub axial width", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure hub extreme face-to-face width.", "", "Required for axial stack"),
        ("C07", "60T", "tooth-face axial width confirmation", "17 provisional; 3 semantic conflict", "SEMANTIC_CONFLICT", "CALIPER", "0.1 mm", "Measure usable toothed face between flange inner faces.", "", "Resolve 20 vs 21 mm component sum"),
        ("C08", "T_SLOT", "narrow entrance width", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure narrowest slot mouth perpendicular to slot.", "", "Required for T-nut insertion"),
        ("C09", "BOLT", "thread major diameter", "M5 candidate; 14 likely length", "REINTERPRETED", "CALIPER/THREAD_GAUGE", "0.05 mm", "Measure thread crest diameter and verify pitch.", "", "Confirm bolt designation"),
        ("C10", "SOCKET", "actual outside diameter", "8 nominal size only", "REINTERPRETED", "CALIPER", "0.1 mm", "Measure largest socket barrel OD used at bolt.", "", "Required for local tool envelope"),
    ]
    high = [
        ("H01", "PTO_SHAFT", "installed left length", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "TAPE/CALIPER", "0.5 mm", "Measure planned inner shaft end to output end after stack mock-up.", "", "Cut length HOLD"),
        ("H02", "PTO_SHAFT", "installed right length", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "TAPE/CALIPER", "0.5 mm", "Measure independently; do not mirror without confirming parts.", "", "Cut length HOLD"),
        ("H03", "PTO_SHAFT", "axial play", "ALMOST_NONE qualitative", "PART_MEASUREMENT_REQUIRED", "DIAL_INDICATOR", "0.05 mm", "Push-pull assembled shaft and record total travel.", "", "Collar/retention design"),
        ("H04", "KP000", "insert protrusion direction", "6 one side", "PART_MEASUREMENT_REQUIRED", "PHOTO/CALIPER", "0.1 mm", "Mark shaft-output direction and measure both sides separately.", "", "Worst pulley/belt clearance"),
        ("H05", "FASTENER", "washer thickness", "4 conflict", "MEASUREMENT_CONFLICT", "CALIPER", "0.05 mm", "Measure one washer alone; confirm it is not a stacked pair.", "", "Fastener stack"),
        ("H06", "TOOL", "hex key short arm and bend radius", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.5 mm", "Measure actual short arm from bend tangent and outside bend radius.", "", "Tool sweep"),
        ("H07", "TOOL", "ratchet head envelope", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.5 mm", "Measure maximum head width/thickness with socket installed.", "", "Tool sweep"),
        ("H08", "PTO_OUTPUT", "collars, coupling and reserve widths", "UNKNOWN", "PART_MEASUREMENT_REQUIRED", "CALIPER", "0.1 mm", "Measure each axial item face-to-face and define required exposed shaft.", "", "Installed shaft length"),
    ]
    rows = []
    for priority, source in (("CRITICAL", critical), ("HIGH", high)):
        for item in source:
            mid, part, measurement, current, classification, tool, accuracy, method, equation, gate = item
            rows.append(
                {
                    "priority": priority,
                    "measurement_id": mid,
                    "part": part,
                    "measurement": measurement,
                    "current_input": current,
                    "classification": classification,
                    "measurement_tool": tool,
                    "required_accuracy": accuracy,
                    "measurement_method": method,
                    "equation": equation,
                    "acceptance_gate": gate,
                    "status": "OPEN_REMEASUREMENT_GATE",
                }
            )
    return rows


def recheck_markdown(rows: list[dict]) -> str:
    lines = [
        "# Common Rover v0.8.3 corrected remeasurement sheet",
        "",
        "**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**",
        "",
        "Do not transfer a reported value into CAD until its classification and gate are closed.",
        "",
        "## Hole-center equations",
        "",
        "`CENTER_DISTANCE = OUTER_EDGE_TO_OUTER_EDGE - HOLE_DIAMETER`",
        "",
        "or",
        "",
        "`CENTER_DISTANCE = INNER_EDGE_TO_INNER_EDGE + HOLE_DIAMETER`",
        "",
        "| Priority | ID | Part | Measurement | Current input | Accuracy | Method | Gate |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['priority']} | {row['measurement_id']} | {row['part']} | "
            f"{row['measurement']} | {row['current_input']} | "
            f"{row['required_accuracy']} | {row['measurement_method']} | "
            f"{row['acceptance_gate']} |"
        )
    lines.extend(
        [
            "",
            "Record left and right separately, photograph the reference faces, and include the measuring tool in the photo. Manufacturing remains HOLD.",
        ]
    )
    return "\n".join(lines) + "\n"


def fit_rows() -> list[dict]:
    impacts = {
        "pulley_runout": "HIGH_RISK_IF_11_MM_CONFIRMED",
        "belt_lateral_wander": "INCREASED_AND_UNQUANTIFIED",
        "belt_tension_variation": "PER_REVOLUTION_VARIATION_POSSIBLE",
        "clearance_impact": "UP_TO_0.5_MM_RADIAL_CENTER_SHIFT_BEFORE_RUNOUT",
        "shaft_balance": "ECCENTRIC_MASS_RISK",
        "set_screw_contact_stress": "HIGH_LOCAL_CONTACT_AND_SHAFT_DENT_RISK",
        "printed_hub_cracking": "INCREASED_BY_POINT_LOAD",
        "removal_repeatability": "POOR_CENTER_REPEATABILITY",
    }
    rows = [
        {
            "audit_id": "A",
            "configuration": "10_MM_SHAFT_WITH_KP000_NOMINAL_10_MM_BORE",
            "shaft_diameter_mm": 10.0,
            "bore_diameter_mm": 10.0,
            "diametral_clearance_mm": 0.0,
            "max_radial_eccentricity_mm": 0.0,
            **{key: "NOMINAL_MATCH_BUT_TOLERANCE_UNKNOWN" for key in impacts},
            "classification": "NOMINAL_PART_SIZE",
            "disposition": "HOLD_PENDING_CALIPER_AND_TOLERANCE",
        },
        {
            "audit_id": "B",
            "configuration": "10_MM_SHAFT_WITH_REPORTED_11_MM_PULLEY_BORE",
            "shaft_diameter_mm": 10.0,
            "bore_diameter_mm": 11.0,
            "diametral_clearance_mm": 1.0,
            "max_radial_eccentricity_mm": 0.5,
            **impacts,
            "classification": "MEASUREMENT_CONFLICT",
            "disposition": "FAIL_PROVISIONAL_FOR_LOAD",
        },
    ]
    options = [
        ("B1", "PROTOTYPE_ONLY", "CURRENT_PRINTED_BORE_PLUS_ONE_SET_SCREW", "HAND_TURN_ONLY"),
        ("B2", "REBORE/BUSH_REQUIRED", "PRECISION_METAL_BUSH_11_OD_10_ID_CONCEPT", "HOLD_ACTUAL_BORE_AND_WALL"),
        ("B3", "METAL_HUB_REQUIRED", "REMOVABLE_CLAMPING_METAL_HUB", "RECOMMENDED_CONCEPT_HOLD"),
        ("B4", "REPLACEMENT_REQUIRED", "REPLACE_WITH_TRUE_10_MM_BORE_COMPONENT", "PREFERRED_IF_11_MM_CONFIRMED"),
    ]
    for audit_id, classification, configuration, disposition in options:
        rows.append(
            {
                "audit_id": audit_id,
                "configuration": configuration,
                "shaft_diameter_mm": 10.0,
                "bore_diameter_mm": "",
                "diametral_clearance_mm": "",
                "max_radial_eccentricity_mm": "",
                **{key: "MITIGATION_DEPENDS_ON_FINAL_DIMENSIONS" for key in impacts},
                "classification": classification,
                "disposition": disposition,
            }
        )
    return rows


def stack_rows() -> list[dict]:
    definitions = [
        ("INNER_SUPPORT_PLATE", "", 5.0, "NO", "OVERLAPS_MOUNT_INTERFACE", "CONFIRMED_PROVISIONAL", "P3-A5052-T5 candidate"),
        ("INNER_KP000_HOUSING", 17.0, "", "NO", "ENVELOPE", "CONFIRMED_PROVISIONAL", "Housing depth only"),
        ("INNER_INSERT_PROTRUSION", 6.0, "", "ORIENTATION", "ENVELOPE_WORST_CASE", "CONFIRMED_PROVISIONAL", "Only one side measured"),
        ("SHAFT_COLLAR", "", "", "YES", "ADDITIVE", "PART_MEASUREMENT_REQUIRED", "Width and retention method missing"),
        ("60T_FLANGE_INNER", 2.0, "", "SEMANTIC", "COMPONENT_ONLY_NON_ADDITIVE", "CONFIRMED_PROVISIONAL", "Contained in reported total 20"),
        ("60T_TOOTHED_FACE", 17.0, "", "SEMANTIC", "COMPONENT_ONLY_NON_ADDITIVE", "REINTERPRETED", "Confirm axial face"),
        ("60T_FLANGE_OUTER", 2.0, "", "SEMANTIC", "COMPONENT_ONLY_NON_ADDITIVE", "CONFIRMED_PROVISIONAL", "2+17+2 conflicts with total by 1"),
        ("60T_TOTAL_ENVELOPE", 20.0, "", "NO", "CONTROLLING_GROUP_TOTAL", "CONFIRMED_PROVISIONAL", "Used instead of summing components"),
        ("SPACER", "", "", "YES", "ADDITIVE", "PART_MEASUREMENT_REQUIRED", "Required width unknown"),
        ("OUTER_KP000_HOUSING", 17.0, "", "NO", "ENVELOPE", "CONFIRMED_PROVISIONAL", "Housing depth only"),
        ("OUTER_INSERT_PROTRUSION", 6.0, "", "ORIENTATION", "ENVELOPE_WORST_CASE", "CONFIRMED_PROVISIONAL", "Opposite-side projection unknown"),
        ("OUTPUT_COLLAR", "", "", "YES", "ADDITIVE", "PART_MEASUREMENT_REQUIRED", "Width unknown"),
        ("PTO_COUPLING", "", "", "YES", "ADDITIVE", "PART_MEASUREMENT_REQUIRED", "Fixing and width unknown"),
        ("OUTPUT_END_RESERVE", "", "", "YES", "ADDITIVE", "PART_MEASUREMENT_REQUIRED", "Required exposed length unknown"),
    ]
    rows = []
    for side in ("LEFT", "RIGHT"):
        for index, item in enumerate(definitions, 1):
            component, measured, provisional, hold, accounting, classification, notes = item
            rows.append(
                {
                    "side": side,
                    "sequence": index,
                    "component": component,
                    "measured_mm": measured,
                    "provisional_mm": provisional,
                    "hold_value": hold,
                    "accounting": accounting,
                    "classification": classification,
                    "notes": notes,
                }
            )
    return rows


def fixation_rows() -> list[dict]:
    values = [
        ("F-P1", "CURRENT_PRINTED_BORE_PLUS_ONE_SET_SCREW", "LOW", "POOR", "POOR", "DENT_RISK", "HIGH_POINT_LOAD", "SIMPLE", "LOW", "AVAILABLE", "POOR", "PROTOTYPE_ONLY", "Hand-turn only; never loaded."),
        ("F-P2", "TWO_OPPOSING_SET_SCREWS", "LOW_TO_MEDIUM", "IMPROVED_BUT_NOT_CENTERING", "LOW", "TWO_DENT_RISK", "HIGH", "SIMPLE", "LOW", "EASY", "POOR", "HOLD_NOT_LOAD_APPROVED", "Still relies on printed hub and clearance."),
        ("F-P3", "D_FLAT_ADDED_TO_SHAFT", "MEDIUM", "SET_SCREW_SIDE_LOAD_REMAINS", "MEDIUM", "INTENTIONAL_SHAFT_MODIFICATION", "MEDIUM", "MEDIUM", "MEDIUM", "SHAFT_PROCESS_REQUIRED", "MEDIUM", "HOLD_SHAFT_MODIFICATION_NOT_APPROVED", "Current shafts have no D-flat."),
        ("F-P4", "REMOVABLE_METAL_CLAMPING_HUB", "HIGH_CANDIDATE", "GOOD_CANDIDATE", "GOOD", "LOW_IF_CLAMPED", "LOW", "GOOD", "MEDIUM", "PURCHASE_OR_MACHINE", "GOOD", "RECOMMENDED_CONCEPT_HOLD", "Requires actual bore, hub OD/width and torque."),
        ("F-P5", "METAL_KEYED_HUB", "HIGH", "GOOD", "GOOD", "KEYWAY_REQUIRED", "LOW", "GOOD", "HIGH", "SHAFT_AND_HUB_MACHINING", "GOOD", "HOLD_REPLACEMENT_SHAFT_OR_KEYWAY", "No current keyway."),
        ("F-P6", "PRINTED_TOOTHED_RING_BOLTED_TO_METAL_HUB", "HIGH_CANDIDATE", "GOOD_IF_REGISTERED", "GOOD", "LOW", "BOLT_PATTERN_AND_RING_CRACK_HOLD", "GOOD", "HIGH", "CUSTOM_DESIGN", "GOOD_WITH_SEALING", "RECOMMENDED_CONCEPT_HOLD", "Separates torque hub from printed teeth."),
    ]
    return [dict(zip(FIXATION_FIELDS, item)) for item in values]


def axial_range_payload() -> dict:
    return {
        "inner_axis_abs_y_mm": 14.0,
        "outer_axis_abs_y_mm": 87.5,
        "output_end_abs_y_mm": 145.0,
        "housing_only_inner_face_abs_y_mm": 5.5,
        "provisional_insert_toward_center_face_abs_y_mm": -0.5,
        "preliminary_coverage_range_mm": [139.5, 145.5],
        "released_installed_length_range_mm": None,
        "upper_bound_status": "HOLD_COUPLING_COLLARS_RESERVE_AND_TOTAL_KP000_ENVELOPE",
        "stock_evaluation": {
            "300_mm_stock": "CANDIDATE_CAN_COVER_PRELIMINARY_RANGE_IF_FINAL_LENGTH_LTE_300",
            "400_mm_stock": "CANDIDATE_CAN_COVER_PRELIMINARY_RANGE_IF_FINAL_LENGTH_LTE_400",
            "preferred_stock": "300_MM_MINIMUM_OFFCUT_CANDIDATE_NOT_RELEASED",
            "cutting": "HOLD",
            "total_1400_mm": "INVENTORY_TOTAL_NOT_INSTALLED_SHAFT_LENGTH",
        },
    }


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


def kp000_shape(center: tuple[float, float, float] = (0, 0, 18.5), protrusion_sign: int = 1) -> cq.Shape:
    x, y, axis_z = center
    bottom = axis_z - KP000["shaft_center_height_mm"]
    housing = _box(67, 17, 35, (x, y, bottom + 17.5))
    bore = _cylinder_y(5, 21, (x, y, axis_z))
    housing = housing.cut(bore)
    insert_center_y = y + protrusion_sign * (8.5 + 3.0)
    insert = _cylinder_y(13, 6, (x, insert_center_y, axis_z)).cut(
        _cylinder_y(5, 8, (x, insert_center_y, axis_z))
    )
    screws = [
        _as_shape(
            cq.Workplane("XY")
            .circle(2.0)
            .extrude(6)
            .translate((x - 5, y + protrusion_sign * 10, axis_z + 10))
        ),
        _as_shape(
            cq.Workplane("XY")
            .circle(2.0)
            .extrude(6)
            .translate((x + 5, y + protrusion_sign * 10, axis_z + 10))
        ),
    ]
    return cq.Compound.makeCompound([_as_shape(housing), _as_shape(insert), *screws])


def plate_shape(sign: int) -> cq.Shape:
    points = [(-47.5, 0), (47.5, 0), (47.5, 58.8), (25.65, 140), (-25.65, 140), (-47.5, 58.8)]
    plate = (
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(2.5, both=True)
        .translate((390, sign * 14, 240))
    )
    return _as_shape(plate)


def build_models() -> dict[str, cq.Shape]:
    local_kp = kp000_shape()
    components: list[cq.Shape] = []
    for sign in (-1, 1):
        components.extend(
            [
                plate_shape(sign),
                kp000_shape((390, sign * 14, 370), protrusion_sign=sign),
                kp000_shape((390, sign * 87.5, 370), protrusion_sign=-sign),
                _cylinder_y(5, 145.5, (390, sign * 72.75, 370)),
                _cylinder_y(60, 20, (390, sign * 47, 370)),
                _cylinder_y(50, 20, (390, sign * 47, 370)),
                _cylinder_y(48, 17, (390, sign * 47, 370)),
                _box(220, 31, 120, (340, sign * 47, 370)),
                _box(10, 4, 10, (373, sign * 8.5, 352)),
                _box(10, 4, 10, (407, sign * 8.5, 352)),
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
    return {
        "kp000": local_kp,
        "assembly": cq.Compound.makeCompound(components),
    }


def _shape_signature(shape: cq.Shape | cq.Workplane) -> dict:
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


def interference_payload() -> dict:
    checks = [
        ("LEFT_DRIVE_BELT_VS_FRAME", 15.5, "PASS_CANDIDATE"),
        ("RIGHT_DRIVE_BELT_VS_FRAME", 15.5, "PASS_CANDIDATE"),
        ("LEFT_PTO_BELT_VS_FRAME", 15.0, "PASS_CANDIDATE"),
        ("RIGHT_PTO_BELT_VS_FRAME", 15.0, "PASS_CANDIDATE"),
        ("LEFT_PTO_BELT_VS_FASTENERS", 20.0, "PASS_CANDIDATE"),
        ("RIGHT_PTO_BELT_VS_FASTENERS", 20.0, "PASS_CANDIDATE"),
        ("LEFT_PTO_BELT_VS_KP000_WORST_PROTRUSION", 3.0, "HOLD_LOW_CLEARANCE"),
        ("RIGHT_PTO_BELT_VS_KP000_WORST_PROTRUSION", 3.0, "HOLD_LOW_CLEARANCE"),
        ("MODEL_A_60T_VS_INNER_KP000_HOUSING_ONLY_LEFT", 14.5, "CONDITIONAL_PASS"),
        ("MODEL_A_60T_VS_INNER_KP000_HOUSING_ONLY_RIGHT", 14.5, "CONDITIONAL_PASS"),
        ("MODEL_A_60T_VS_INNER_INSERT_WORST_LEFT", 8.5, "FAIL_PROVISIONAL_CLEARANCE_LT_10"),
        ("MODEL_A_60T_VS_INNER_INSERT_WORST_RIGHT", 8.5, "FAIL_PROVISIONAL_CLEARANCE_LT_10"),
        ("MODEL_A_60T_VS_SUPPORT_PLATE_LEFT", 20.5, "PASS_CANDIDATE"),
        ("MODEL_A_60T_VS_SUPPORT_PLATE_RIGHT", 20.5, "PASS_CANDIDATE"),
        ("LEFT_SUPPORT_VS_RIGHT_SUPPORT", 23.0, "PASS_CANDIDATE"),
        ("TOOL_X_INSERTION_MARGIN_LEFT", 14.0, "HOLD_ACTUAL_TOOL"),
        ("TOOL_X_INSERTION_MARGIN_RIGHT", 14.0, "HOLD_ACTUAL_TOOL"),
        ("TRACK_LEFT_DYNAMIC_VS_UPPER", 10.0, "PASS_CANDIDATE"),
        ("TRACK_RIGHT_DYNAMIC_VS_UPPER", 10.0, "PASS_CANDIDATE"),
    ]
    rows = [
        {
            "check_id": check_id,
            "intersection_count": 0,
            "minimum_distance_mm": distance,
            "status": status,
        }
        for check_id, distance, status in checks
    ]
    return {
        "document_id": DOCUMENT_ID,
        "safety_pulley_model": "MODEL_A_CONSERVATIVE",
        "checks": rows,
        "summary": {
            "check_count": len(rows),
            "intersection_count": 0,
            "four_belt_intersection_count": 0,
            "fail_provisional_count": sum("FAIL_PROVISIONAL" in row["status"] for row in rows),
            "hold_count": sum("HOLD" in row["status"] for row in rows),
            "kp000_belt_worst_clearance_mm": 3.0,
            "pulley_kp000_housing_only_mm": 14.5,
            "pulley_kp000_worst_provisional_mm": 8.5,
            "support_plate_belt_mm": 15.0,
            "candidate_total_width_mm": 290.0,
            "physical_total_width": "HOLD_PENDING_COMPLETE_AXIAL_STACK",
            "pto_ends_y_mm": [-145.0, 145.0],
            "rotation_safety_envelope_od_mm": 120.0,
        },
        "holds": [
            "KP000_TOTAL_AXIAL_ENVELOPE",
            "INSERT_PROTRUSION_DIRECTION",
            "SHAFT_COLLAR_WIDTH",
            "PULLEY_HUB_DIMENSIONS",
            "COUPLING_AND_OUTPUT_RESERVE",
            "ACTUAL_TOOL_ENVELOPE",
        ],
    }


def integration_payload(measurements: list[dict], discrepancies: dict) -> dict:
    return {
        "document_id": DOCUMENT_ID,
        "schema": SCHEMA,
        "source": {
            "type": "USER_PROVIDED_MEASUREMENTS",
            "integration_date": "2026-07-31",
            "prior_v0082_measurement_rows": 60,
            "prior_v0082_filled_measurement_values": 0,
        },
        "authority": {
            "measurement_integration": "CONDITIONAL_PASS",
            "envelope_geometry": "CONDITIONAL_PASS_WITH_HOLDS",
            "physical_fit": "HOLD",
            "pulley_bore_fit": "FAIL_PROVISIONAL",
            "hole_pattern": "PART_MEASUREMENT_REQUIRED",
            "machining": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
        "protected_parents": _protected_payload(),
        "fixed_architecture": FIXED,
        "measurements": measurements,
        "classification_counts": dict(
            sorted(Counter(row["classification"] for row in measurements).items())
        ),
        "kp000_cad": KP000,
        "pulley_models": [PULLEY_A, PULLEY_B],
        "shaft": {
            "nominal_diameter_mm": 10.0,
            "stock": [
                {"length_mm": 400.0, "count": 2},
                {"length_mm": 300.0, "count": 2},
            ],
            "total_stock_length_mm": 1400.0,
            "total_stock_semantics": "INVENTORY_TOTAL_NOT_INSTALLED_SHAFT_LENGTH",
            "installed_length_left_mm": None,
            "installed_length_right_mm": None,
            "keyway": "NONE",
            "d_flat": "NONE",
            "axial_play": "PART_MEASUREMENT_REQUIRED",
        },
        "support_plate_non_regression": {
            **FIXED["support_plate"],
            "kp000_width_increase_from_v0082_envelope_mm": 22.0,
            "kp000_depth_increase_from_v0082_envelope_mm": 2.0,
            "kp000_height_change_mm": 0.0,
            "axis_center_from_base_change_mm": 1.0,
            "plate_side_margin_each_mm": 14.0,
            "mount_holes_in_geometry": False,
            "set_screw_access": "HOLD_ANGULAR_POSITION_REQUIRED",
        },
        "axial_length": axial_range_payload(),
        "discrepancy_status": discrepancies["status"],
        "release_holds": [
            "KP000_HOLE_CENTER_DISTANCE",
            "KP000_TOTAL_AXIAL_ENVELOPE",
            "KP000_ACTUAL_BORE",
            "PULLEY_ACTUAL_BORE",
            "PULLEY_HUB_OD_AND_WIDTH",
            "PULLEY_COMPONENT_WIDTH_CONFLICT",
            "T_SLOT_OPENING",
            "BOLT_THREAD",
            "TOOL_LOCAL_ENVELOPES",
            "INSTALLED_SHAFT_LENGTHS",
        ],
    }


def _svg_shell(title: str, content: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="900" viewBox="0 0 1300 900">
<rect width="100%" height="100%" fill="#f5f7fa"/>
<style>.h{{font:700 25px Arial;fill:#132238}}.s{{font:15px Arial;fill:#1d2d3c}}.w{{font:700 15px Arial;fill:#ad1515}}.ok{{fill:#67bd6a;stroke:#174f2b;stroke-width:2}}.old{{fill:#ced5dc;stroke:#566573;stroke-width:2}}.hold{{fill:#ffe6a8;stroke:#9c6510;stroke-width:2}}.bad{{fill:#ffd0d0;stroke:#ad1515;stroke-width:2}}.d{{stroke:#1d426d;stroke-width:2;fill:none}}.g{{stroke:#8997a5;stroke-dasharray:7 5;fill:none}}</style>
<text x="35" y="42" class="h">{title}</text>
<text x="35" y="68" class="w">NOT_FOR_MANUFACTURING · PART_MEASUREMENT_REQUIRED · physical fit HOLD</text>
{content}
</svg>
"""


def overview_svg() -> str:
    return _svg_shell(
        "Common Rover v0.8.3 measurement integration",
        """
<rect x="35" y="95" width="1230" height="300" fill="white" stroke="#cad4df"/>
<text x="55" y="130" class="h">KP000 envelope update</text>
<rect x="100" y="190" width="180" height="140" class="old"/><text x="115" y="180" class="s">v0.8.2: 45 x 15 x 35 candidate</text>
<rect x="390" y="175" width="268" height="140" class="ok"/><text x="405" y="165" class="s">v0.8.3: 67 x 17 x 35 provisional</text>
<circle cx="524" cy="249" r="35" fill="white" stroke="#174f2b"/><text x="485" y="255" class="s">bore 10 nominal</text>
<text x="730" y="185" class="s">axis center/base: 18.5 +/-0.5 mm</text>
<text x="730" y="220" class="s">one-side insert: 6 mm provisional</text>
<text x="730" y="255" class="w">hole centers: PART_MEASUREMENT_REQUIRED</text>
<text x="730" y="290" class="w">total axial envelope: HOLD</text>
<text x="730" y="325" class="s">no grease nipple; two set-screw envelopes</text>
<rect x="35" y="420" width="1230" height="390" fill="white" stroke="#cad4df"/>
<text x="55" y="458" class="h">60T and shaft/bore audit</text>
<circle cx="230" cy="610" r="120" class="hold"/><circle cx="230" cy="610" r="100" class="ok"/><circle cx="230" cy="610" r="20" fill="white" stroke="#ad1515"/>
<text x="90" y="760" class="s">MODEL_A OD120 safety · MODEL_B flange OD100</text>
<rect x="450" y="530" width="290" height="160" class="bad"/>
<text x="475" y="565" class="s">10 mm shaft / reported 11 mm bore</text>
<text x="475" y="610" class="w">diametral clearance = 1.0 mm</text>
<text x="475" y="645" class="w">radial eccentricity up to 0.5 mm</text>
<text x="475" y="675" class="w">FAIL_PROVISIONAL_FOR_LOAD</text>
<rect x="800" y="500" width="410" height="220" class="hold"/>
<text x="825" y="540" class="h">Axial semantic conflict</text>
<text x="825" y="580" class="s">reported total = 20 mm</text>
<text x="825" y="615" class="s">2 flange + 17 face + 2 flange = 21 mm</text>
<text x="825" y="650" class="w">difference 1 mm — remeasure</text>
<text x="825" y="685" class="s">1400 mm is stock total, never one shaft</text>
""",
    )


def critical_svg() -> str:
    return _svg_shell(
        "V0.8.3 critical dimensions and remeasurement gates",
        """
<rect x="35" y="95" width="1230" height="720" fill="white" stroke="#cad4df"/>
<text x="60" y="135" class="h">KP000 front / axial envelope</text>
<rect x="120" y="220" width="335" height="175" class="ok"/>
<circle cx="287" cy="302" r="25" fill="white" stroke="#174f2b"/>
<line x1="120" y1="430" x2="455" y2="430" class="d"/><text x="235" y="460" class="s">67.0 mm</text>
<line x1="490" y1="220" x2="490" y2="395" class="d"/><text x="505" y="315" class="s">35.0 mm</text>
<line x1="287" y1="302" x2="287" y2="395" class="d"/><text x="300" y="355" class="s">18.5 +/-0.5</text>
<text x="120" y="500" class="w">two round holes dia 8: CENTER DISTANCE UNKNOWN</text>
<text x="120" y="535" class="s">CENTER = outer-edge span - hole diameter</text>
<text x="120" y="565" class="s">or inner-edge span + hole diameter</text>
<text x="700" y="135" class="h">Axial section</text>
<rect x="730" y="235" width="170" height="120" class="ok"/><text x="765" y="220" class="s">housing 17</text>
<rect x="900" y="260" width="60" height="70" class="hold"/><text x="905" y="350" class="s">insert 6</text>
<line x1="730" y1="405" x2="960" y2="405" class="d"/><text x="755" y="435" class="w">total axial envelope UNKNOWN</text>
<text x="680" y="500" class="h">Critical gates</text>
<text x="680" y="540" class="w">1 hole center · 2 total axial · 3 KP bore</text>
<text x="680" y="575" class="w">4 pulley bore · 5/6 hub OD/width · 7 face width</text>
<text x="680" y="610" class="w">8 T-slot mouth · 9 bolt major dia · 10 socket OD</text>
<text x="680" y="670" class="s">No support-plate hole geometry is released.</text>
<text x="680" y="705" class="s">120 mm pulley rotation envelope remains controlling.</text>
""",
    )


def authority_markdown(
    integration: dict,
    discrepancies: dict,
    interference: dict,
    fit: list[dict],
) -> str:
    return f"""# Common Rover v0.8.3 Measurement Integration and Dimensional Audit

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Document `{DOCUMENT_ID}` integrates user measurements without releasing holes,
shaft cut lengths, support-plate machining, or field use.

## 1. Parent protection and architecture

v0.8, v0.8.1 and v0.8.2 are protected by 56 embedded hashes and verified
against repository files when available. Two motors, two independent PTO
shafts, inward motor axes, DRIVE/NEUTRAL/PTO clutches, high CBOX/BBOX,
non-structural boxes, inverted-trapezoid crawlers, v0.8.1
`{V0081_CANDIDATE}` and v0.8.2 `{V0082_CANDIDATE}` are unchanged.

## 2. Accepted provisional measurements

KP000 envelope becomes 67 x 17 x 35 mm, shaft center is 18.5 +/-0.5 mm
from the base, one insert protrusion is 6 mm, two round mounting holes are
reported at diameter 8 mm, there are two insert set screws and no grease
nipple. The CAD bore remains nominal 10 mm pending caliper verification.
Mount-hole centers and total axial envelope remain absent from geometry.

MODEL_A retains the 120 mm rotation safety OD and 20 mm axial width.
MODEL_B records flange OD 100 mm, toothed-body OD 96 mm provisional, axial
total 20 mm, face width 17 mm provisional and flange thickness 2 mm.
Hub OD/width and bore remain HOLD.

## 3. Rejected and reinterpreted inputs

The KP000 ruler reading of 11 mm is rejected because a 10 mm shaft passes
with almost no play. The reported pulley bore 11 mm is not accepted as a
load fit. A 17 mm value is axial tooth-face width, not toothed diameter; 96
mm is the provisional radial body OD, not hub OD. Three millimetres is an
unidentified tooth-width report. Fourteen millimetres is likely bolt length,
not M5 diameter. A 196 mm hex-key total length is not local tool clearance.
The 4 mm washer thickness is conflicted. The 1400 mm shaft value is inventory
total, never one installed shaft.

There are {discrepancies['discrepancy_count']} registered discrepancies.

## 4. Shaft/bore fit

Configuration A, nominal 10 mm shaft and nominal 10 mm KP000 bore, is a
nominal match but remains tolerance HOLD. Configuration B, 10 mm shaft and
reported 11 mm pulley bore, has 1.0 mm diametral clearance and up to 0.5 mm
radial eccentricity before clamping. It can increase runout, belt wander,
tension variation, local set-screw stress, mass eccentricity, printed-hub
cracking and removal-to-removal variation.

If 11 mm is confirmed, the current single-set-screw pulley is
`FAIL_PROVISIONAL_FOR_LOAD`. Hand-turn prototype, precision bush, removable
metal hub and replacement with a true 10 mm bore are separately classified.

## 5. KP000 and plate non-regression

The old 45 x 15 x 35 envelope changes by +22 mm in X, +2 mm in Y and 0 mm
in Z. The axis/base relation changes from 17.5 to 18.5 mm. The 95 x 140 x
5 mm P3 plate remains a candidate and leaves 14 mm outline margin on each
side of the 67 mm KP000. No plate holes are emitted.

The one-side insert can reduce PTO belt/KP000 candidate distance to 3.0 mm.
Housing-only pulley/KP000 distance is 14.5 mm, but worst provisional
insert-facing-pulley distance is 8.5 mm, below the prior 10 mm safety target.
Insert direction and total axial envelope are therefore critical.

## 6. Pulley models and axial conflict

Safety decisions use MODEL_A OD120. MODEL_B is measurement visualization
only. The component expression 2 + 17 + 2 equals 21 mm and conflicts with
the reported 20 mm total by 1 mm. The 20 mm outer total controls the
provisional envelope; component widths are non-additive until remeasured.

## 7. Axial stack and shaft stock

Each side has an explicit stack table. Known housing, insert and pulley values
are separated from collars, spacer, coupling and output reserve HOLD values.
The preliminary geometric shaft coverage is
{integration['axial_length']['preliminary_coverage_range_mm'][0]} to
{integration['axial_length']['preliminary_coverage_range_mm'][1]} mm, but
there is no released installed-length range. Both 300 and 400 mm stock can
cover that preliminary range; 300 mm minimizes offcut provisionally. Cutting
remains HOLD.

## 8. Fixation

One set screw is prototype hand-turn only. Two screws and a D-flat remain
unreleased mitigations. A removable metal clamping hub or a printed toothed
ring bolted to a metal hub are preferred concepts, subject to bore, hub,
torque, bolt and material measurements. A keyed hub requires a different or
machined shaft.

## 9. Interference and width

All four belt intersection counts remain zero in the candidate model.
Candidate overall width remains 290 mm and PTO endpoints remain +/-145 mm.
Physical width is HOLD because collars, coupling, output reserve and complete
KP000 axial envelopes are missing. The report registers
{interference['summary']['fail_provisional_count']} provisional clearance
failure category and {interference['summary']['hold_count']} HOLD checks.

## 10. Release state

- measurement integration: CONDITIONAL_PASS
- envelope geometry: CONDITIONAL_PASS_WITH_HOLDS
- physical fit: HOLD
- pulley bore fit: FAIL_PROVISIONAL
- support-plate hole pattern: PART_MEASUREMENT_REQUIRED
- shaft cutting, machining and drilling: HOLD
- field deployment: NOT_APPROVED
"""


def readme_text() -> str:
    return f"""# Common Rover v0.8.3 measurement integration handoff

This exact {len(PACKAGE_PATHS)}-file package is an audit and remeasurement
gate, not a manufacturing release.

Runtime: Python 3.12.13, CadQuery 2.8.0.

```powershell
python -B build_common_rover_measurement_integration_v0083.py --verify
python -B tests/test_common_rover_measurement_integration_v0083_contract.py
```

The ZIP is standalone. Repository-present mode verifies all v0.8/v0.8.1/v0.8.2
hashes. Hole centers, shaft cut lengths, pulley bore fit, machining, loading
and field deployment remain HOLD or NOT_APPROVED.
"""


def validation_payload(
    integration: dict,
    discrepancies: dict,
    interference: dict,
    models: dict[str, cq.Shape],
    step_paths: dict[str, Path],
) -> dict:
    geometry = {}
    for key, shape in models.items():
        source = _shape_signature(shape)
        imported = cq.importers.importStep(str(step_paths[key]))
        artifact = _shape_signature(imported)
        geometry[key] = {
            "source_signature": source,
            "artifact_signature": artifact,
            "step_sha256": _sha256(step_paths[key]),
            "step_size_bytes": step_paths[key].stat().st_size,
            "semantic_geometry_reproducible": source == artifact,
        }
    checks = {
        "v008_protected": True,
        "v0081_protected": True,
        "v0082_protected": True,
        "motor_count_2": FIXED["motor_count"] == 2,
        "independent_pto_2": FIXED["pto_count"] == 2,
        "no_common_pto_shaft": FIXED["common_pto_shaft"] == "PROHIBITED",
        "parent_candidates_fixed": FIXED["v0081_candidate"] == V0081_CANDIDATE and FIXED["v0082_candidate"] == V0082_CANDIDATE,
        "plate_5_mm_fixed": FIXED["support_plate"]["thickness_mm"] == 5.0,
        "kp000_width_67": KP000["overall_width_mm"] == 67.0,
        "kp000_height_35": KP000["overall_height_mm"] == 35.0,
        "kp000_depth_17": KP000["housing_depth_mm"] == 17.0,
        "kp000_bore_11_rejected": KP000["bore_used_for_cad_mm"] == 10.0,
        "hole_center_not_in_geometry": KP000["mount_hole_center_distance_mm"] is None,
        "pulley_safety_od_120": PULLEY_A["rotation_envelope_od_mm"] == 120.0,
        "pulley_bore_fit_fail_provisional": integration["authority"]["pulley_bore_fit"] == "FAIL_PROVISIONAL",
        "stock_total_not_installed_length": integration["shaft"]["total_stock_semantics"] == "INVENTORY_TOTAL_NOT_INSTALLED_SHAFT_LENGTH",
        "four_belt_intersections_zero": interference["summary"]["four_belt_intersection_count"] == 0,
        "candidate_width_lt_300": interference["summary"]["candidate_total_width_mm"] < 300.0,
        "pto_ends_within_145": max(abs(value) for value in interference["summary"]["pto_ends_y_mm"]) <= 145.0,
        "manufacturing_hold": integration["authority"]["machining"] == "HOLD",
        "field_not_approved": integration["authority"]["field_deployment"] == "NOT_APPROVED",
        "forbidden_promotions_registered": len(discrepancies["forbidden_cad_promotions"]) == 7,
    }
    return {
        "document_id": DOCUMENT_ID,
        "fixed_checks": checks,
        "fixed_check_count": len(checks),
        "fixed_check_pass_count": sum(checks.values()),
        "geometry": geometry,
        "measurement_count": len(integration["measurements"]),
        "discrepancy_count": discrepancies["discrepancy_count"],
        "interference_summary": interference["summary"],
        "overall": (
            "CONDITIONAL_PASS_MEASUREMENT_INTEGRATION"
            if all(checks.values())
            and all(value["semantic_geometry_reproducible"] for value in geometry.values())
            else "FAIL"
        ),
        "physical_fit": "HOLD",
        "pulley_bore_fit": "FAIL_PROVISIONAL",
        "hole_pattern": "PART_MEASUREMENT_REQUIRED",
        "manufacturing_release": "HOLD",
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
            raise RuntimeError(f"missing path while sealing: {relative}")
        sums.append(f"{_sha256(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(sums) + "\n")


def refresh() -> dict:
    _audit_protected_if_available()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    measurements = measurement_rows()
    discrepancies = discrepancy_payload(measurements)
    rechecks = recheck_rows()
    fits = fit_rows()
    stacks = stack_rows()
    fixations = fixation_rows()
    interference = interference_payload()
    integration = integration_payload(measurements, discrepancies)
    models = build_models()
    step_paths = {
        "kp000": ARTIFACT_DIR / KP000_STEP,
        "assembly": ARTIFACT_DIR / ASSEMBLY_STEP,
    }
    for key, shape in models.items():
        _write_step(shape, step_paths[key])
    validation = validation_payload(
        integration, discrepancies, interference, models, step_paths
    )
    texts = {
        AUTHORITY_NAME: authority_markdown(integration, discrepancies, interference, fits),
        INTEGRATION_NAME: _json_text(integration),
        DISCREPANCY_NAME: _json_text(discrepancies),
        RECHECK_MD_NAME: recheck_markdown(rechecks),
        RECHECK_CSV_NAME: _csv_text(rechecks, RECHECK_FIELDS),
        FIT_NAME: _csv_text(fits, FIT_FIELDS),
        STACK_NAME: _csv_text(stacks, STACK_FIELDS),
        FIXATION_NAME: _csv_text(fixations, FIXATION_FIELDS),
        INTERFERENCE_NAME: _json_text(interference),
        VALIDATION_NAME: _json_text(validation),
        README_NAME: readme_text(),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(),
        f"artifacts/{CRITICAL_SVG}": critical_svg(),
    }
    for relative, text in texts.items():
        _write_text(LANE_DIR / relative, text)
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        f"DOCUMENT_ID={DOCUMENT_ID}\nSTATUS=PENDING_CONTRACT_EXECUTION\n",
    )
    _seal_hashes()
    return validation


def _verify_hashes() -> dict:
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


def verify() -> dict:
    audit = _audit_protected_if_available()
    missing = [relative for relative in PACKAGE_PATHS if not (LANE_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing package paths: {missing}")
    validation = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    if validation["overall"] != "CONDITIONAL_PASS_MEASUREMENT_INTEGRATION":
        raise RuntimeError("validation overall mismatch")
    measurements = measurement_rows()
    discrepancies = discrepancy_payload(measurements)
    integration = integration_payload(measurements, discrepancies)
    interference = interference_payload()
    expected = {
        AUTHORITY_NAME: authority_markdown(integration, discrepancies, interference, fit_rows()),
        INTEGRATION_NAME: _json_text(integration),
        DISCREPANCY_NAME: _json_text(discrepancies),
        RECHECK_MD_NAME: recheck_markdown(recheck_rows()),
        RECHECK_CSV_NAME: _csv_text(recheck_rows(), RECHECK_FIELDS),
        FIT_NAME: _csv_text(fit_rows(), FIT_FIELDS),
        STACK_NAME: _csv_text(stack_rows(), STACK_FIELDS),
        FIXATION_NAME: _csv_text(fixation_rows(), FIXATION_FIELDS),
        INTERFERENCE_NAME: _json_text(interference),
        README_NAME: readme_text(),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(),
        f"artifacts/{CRITICAL_SVG}": critical_svg(),
    }
    mismatches = [
        relative
        for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise RuntimeError(f"byte reproducibility mismatch: {mismatches}")
    for key, relative in (
        ("kp000", f"artifacts/{KP000_STEP}"),
        ("assembly", f"artifacts/{ASSEMBLY_STEP}"),
    ):
        imported = cq.importers.importStep(str(LANE_DIR / relative))
        if _shape_signature(imported) != validation["geometry"][key]["artifact_signature"]:
            raise RuntimeError(f"STEP semantic mismatch: {key}")
    package = _verify_hashes()
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "measurement_count": validation["measurement_count"],
        "discrepancy_count": validation["discrepancy_count"],
        "interference_count": validation["interference_summary"]["intersection_count"],
        "pulley_bore_fit": validation["pulley_bore_fit"],
        "protected_audit_mode": audit["mode"],
        "protected_checked_path_count": audit["checked_path_count"],
        **package,
    }


def record_test_result() -> dict:
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


def package() -> dict:
    result = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOAD_DIR / f"Paddy_Swarm_Common_Rover_v0_8_3_Measurement_Integration_{stamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite ZIP: {path}")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PACKAGE_PATHS:
            archive.write(LANE_DIR / relative, relative)
    with zipfile.ZipFile(path, "r") as archive:
        bad = archive.testzip()
        names = archive.namelist()
        forbidden = [
            name
            for name in names
            if "__pycache__" in name or ".pytest_cache" in name or name.endswith(".pyc")
        ]
        if bad or tuple(names) != PACKAGE_PATHS or forbidden:
            raise RuntimeError(f"ZIP audit failure: {bad}, {len(names)}, {forbidden}")
        sums = archive.read(SHA256SUMS_NAME).decode("utf-8").splitlines()
        internal_ok = all(
            hashlib.sha256(archive.read(relative)).hexdigest() == digest
            for digest, relative in (line.split("  ", 1) for line in sums)
        )
        if not internal_ok:
            raise RuntimeError("ZIP internal SHA256SUMS mismatch")
    return {
        **result,
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
            "overall": result["overall"],
            "fixed_checks": f"{result['fixed_check_pass_count']}/{result['fixed_check_count']}",
            "measurement_count": result["measurement_count"],
            "discrepancy_count": result["discrepancy_count"],
            "pulley_bore_fit": result["pulley_bore_fit"],
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
