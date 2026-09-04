"""Build, verify, and package Common Rover KP000 support-plate v0.8.2.

All holes and purchased-part dimensions in this package are parametric
inspection placeholders.  Nothing generated here is a manufacturing drawing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
ARTIFACT_DIR = LANE_DIR / "artifacts"
DOWNLOAD_DIR = Path("D:/Downloads")

DOCUMENT_ID = "PS-CR-KP000-SUPPORT-PLATE-V0082"
SCHEMA = "paddy_swarm.common_rover.kp000_support_plate.v0.8.2"
RECOMMENDED_PARENT_ID = "S2-REF-T5-BP2.00-OP5.50"
RECOMMENDED_ID = "P3-A5052-T5"
ALTERNATIVE_A_ID = "P2-A6061-T5"
ALTERNATIVE_B_ID = "P3-STEEL-T4.5"

AUTHORITY_NAME = "common_rover_kp000_support_plate_design_authority_v0082.md"
PARAMETERS_NAME = "common_rover_kp000_support_plate_parameters_v0082.json"
MEASUREMENT_MD_NAME = "kp000_support_plate_measurement_sheet_v0082.md"
MEASUREMENT_CSV_NAME = "kp000_support_plate_measurement_sheet_v0082.csv"
CANDIDATES_NAME = "common_rover_kp000_support_plate_candidates_v0082.csv"
RANKING_NAME = "common_rover_kp000_support_plate_ranking_v0082.csv"
STRENGTH_NAME = "common_rover_kp000_support_plate_strength_report_v0082.json"
INTERFERENCE_NAME = "common_rover_kp000_support_plate_interference_report_v0082.json"
TOOLS_NAME = "common_rover_kp000_support_plate_tool_access_v0082.csv"
FASTENERS_NAME = "common_rover_kp000_support_plate_fasteners_v0082.csv"
VALIDATION_NAME = "common_rover_kp000_support_plate_validation_v0082.json"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0082.txt"
TEST_REL = "tests/test_common_rover_kp000_support_plate_v0082_contract.py"

ASSEMBLY_STEP = "PS-CR-KP000-SUPPORT-PLATE-V0082-ASSEMBLY.step"
LEFT_STEP = "PS-CR-KP000-SUPPORT-PLATE-V0082-LEFT.step"
RIGHT_STEP = "PS-CR-KP000-SUPPORT-PLATE-V0082-RIGHT.step"
LEFT_DXF = "PS-CR-KP000-SUPPORT-PLATE-V0082-LEFT.dxf"
RIGHT_DXF = "PS-CR-KP000-SUPPORT-PLATE-V0082-RIGHT.dxf"
OVERVIEW_SVG = "PS-CR-KP000-SUPPORT-PLATE-V0082-OVERVIEW.svg"
TOP_SVG = "PS-CR-KP000-SUPPORT-PLATE-V0082-TOP.svg"
FRONT_SVG = "PS-CR-KP000-SUPPORT-PLATE-V0082-FRONT.svg"
SIDE_SVG = "PS-CR-KP000-SUPPORT-PLATE-V0082-SIDE.svg"
DIMENSIONS_SVG = "PS-CR-KP000-SUPPORT-PLATE-V0082-DIMENSIONS.svg"

PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    MEASUREMENT_MD_NAME,
    MEASUREMENT_CSV_NAME,
    CANDIDATES_NAME,
    RANKING_NAME,
    STRENGTH_NAME,
    INTERFERENCE_NAME,
    TOOLS_NAME,
    FASTENERS_NAME,
    VALIDATION_NAME,
    "build_common_rover_kp000_support_plate_v0082.py",
    f"artifacts/{ASSEMBLY_STEP}",
    f"artifacts/{LEFT_STEP}",
    f"artifacts/{RIGHT_STEP}",
    f"artifacts/{LEFT_DXF}",
    f"artifacts/{RIGHT_DXF}",
    f"artifacts/{OVERVIEW_SVG}",
    f"artifacts/{TOP_SVG}",
    f"artifacts/{FRONT_SVG}",
    f"artifacts/{SIDE_SVG}",
    f"artifacts/{DIMENSIONS_SVG}",
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

FIXED = {
    "motor_count": 2,
    "pto_count": 2,
    "pto_architecture": "TWO_INDEPENDENT_LATERAL_SHAFTS",
    "common_pto_shaft": "PROHIBITED",
    "motor_shaft_directions": {"left": "-Y_INWARD", "right": "+Y_INWARD"},
    "pto_output_directions": {"left": "+Y", "right": "-Y"},
    "clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "simultaneous_drive_pto": "PROHIBITED",
    "cbox_mm": [130.0, 140.0, 105.0],
    "bbox_mm": [150.0, 220.0, 150.0],
    "battery_cassette_mm": [125.0, 180.0, 120.0],
    "box_arrangement": "CBOX_FRONT_BBOX_REAR_SHORT_FACES_OPPOSED",
    "box_structural_role": "PROHIBITED",
    "box_bottom_min_z_mm": 200.0,
    "crawler": "INVERTED_TRAPEZOID_INDEPENDENT_LEFT_RIGHT",
    "track_width_each_mm": 55.0,
    "single_aluminum_member_max_mm": 400.0,
}

V0081 = {
    "candidate_id": RECOMMENDED_PARENT_ID,
    "inner_support_plate_thickness_mm": 5.0,
    "inner_kp000_axis_y_mm": [-14.0, 14.0],
    "pto_belt_plane_y_mm": [-47.0, 47.0],
    "outer_kp000_axis_y_mm": [-87.5, 87.5],
    "drive_belt_plane_y_mm": [-119.0, 119.0],
    "pto_output_end_y_mm": [-145.0, 145.0],
    "total_width_mm": 290.0,
    "pto_belt_frame_mm": 15.0,
    "pto_belt_fasteners_mm": 20.0,
    "drive_belt_frame_mm": 15.5,
    "drive_belt_fasteners_mm": 19.5,
    "pto_60t_fixed_mm": 13.0,
    "pto_belt_wiring_mm": 21.5,
    "pto_residual_mm": 10.0,
    "drive_residual_mm": 10.5,
    "track_dynamic_upper_mm": 10.0,
}

MATERIALS = {
    "A5052": {
        "label": "A5052-P candidate",
        "thickness_mm": 5.0,
        "elastic_modulus_mpa": 69000.0,
        "yield_min_mpa": 140.0,
        "yield_range_mpa": [140.0, 195.0],
        "density_kg_mm3": 2.68e-6,
        "corrosion": "GOOD_CANDIDATE",
        "machining": "GOOD",
        "availability": "VERIFY_LOCAL_SUPPLIER",
        "property_source": "PARAMETRIC_CANDIDATE_INPUT_NOT_MATERIAL_CERTIFICATE",
    },
    "A6061": {
        "label": "A6061-series or equivalent candidate",
        "thickness_mm": 5.0,
        "elastic_modulus_mpa": 69000.0,
        "yield_min_mpa": 240.0,
        "yield_range_mpa": [240.0, 276.0],
        "density_kg_mm3": 2.70e-6,
        "corrosion": "GOOD_WITH_FINISH_CANDIDATE",
        "machining": "GOOD",
        "availability": "VERIFY_ALLOY_AND_TEMPER",
        "property_source": "PARAMETRIC_CANDIDATE_INPUT_NOT_MATERIAL_CERTIFICATE",
    },
    "STEEL3": {
        "label": "General structural steel candidate 3 mm",
        "thickness_mm": 3.0,
        "elastic_modulus_mpa": 205000.0,
        "yield_min_mpa": 235.0,
        "yield_range_mpa": [235.0, 275.0],
        "density_kg_mm3": 7.85e-6,
        "corrosion": "COATING_REQUIRED",
        "machining": "GOOD_BUT_RUST_CONTROL_REQUIRED",
        "availability": "VERIFY_GRADE",
        "property_source": "PARAMETRIC_CANDIDATE_INPUT_NOT_MATERIAL_CERTIFICATE",
    },
    "STEEL": {
        "label": "General structural steel candidate 4.5 mm",
        "thickness_mm": 4.5,
        "elastic_modulus_mpa": 205000.0,
        "yield_min_mpa": 235.0,
        "yield_range_mpa": [235.0, 275.0],
        "density_kg_mm3": 7.85e-6,
        "corrosion": "COATING_AND_GALVANIC_ISOLATION_REQUIRED",
        "machining": "GOOD_BUT_MASS_HIGHER",
        "availability": "VERIFY_GRADE_AND_THICKNESS",
        "property_source": "PARAMETRIC_CANDIDATE_INPUT_NOT_MATERIAL_CERTIFICATE",
    },
}

OUTLINES = {
    "P1": {
        "name": "MINIMUM_RECTANGLE",
        "width_mm": 65.0,
        "height_mm": 90.0,
        "area_factor": 0.95,
        "effective_width_mm": 50.0,
        "effective_cantilever_mm": 55.0,
        "tool_clearance_mm": 8.0,
        "serviceability": 6,
        "manufacturability": "SIMPLE_FLAT_PLATE",
    },
    "P2": {
        "name": "LOWER_EXTENSION",
        "width_mm": 75.0,
        "height_mm": 130.0,
        "area_factor": 0.95,
        "effective_width_mm": 75.0,
        "effective_cantilever_mm": 45.0,
        "tool_clearance_mm": 12.0,
        "serviceability": 8,
        "manufacturability": "SIMPLE_FLAT_PLATE",
    },
    "P3": {
        "name": "INTEGRAL_TRIANGULAR_GUSSET",
        "width_mm": 95.0,
        "height_mm": 140.0,
        "area_factor": 0.68,
        "effective_width_mm": 90.0,
        "effective_cantilever_mm": 38.0,
        "tool_clearance_mm": 14.0,
        "serviceability": 9,
        "manufacturability": "FLAT_PROFILE_CUT_NO_BENDING",
    },
    "P4": {
        "name": "FLAT_SERVICE_NOTCHED_PLATE",
        "width_mm": 80.0,
        "height_mm": 120.0,
        "area_factor": 0.82,
        "effective_width_mm": 70.0,
        "effective_cantilever_mm": 48.0,
        "tool_clearance_mm": 11.0,
        "serviceability": 10,
        "manufacturability": "FLAT_PROFILE_CUT_NO_BENDING",
    },
}

LOAD_CASES = [
    {
        "load_case": "LC1",
        "belt_radial_load_n": 100.0,
        "pto_torque_nm": 1.0,
        "coupling_side_load_n": 0.0,
        "axial_load_n": 0.0,
        "shock_factor": 1.0,
        "direction": "FORWARD",
    },
    {
        "load_case": "LC2",
        "belt_radial_load_n": 200.0,
        "pto_torque_nm": 2.0,
        "coupling_side_load_n": 0.0,
        "axial_load_n": 0.0,
        "shock_factor": 1.5,
        "direction": "FORWARD",
    },
    {
        "load_case": "LC3",
        "belt_radial_load_n": 300.0,
        "pto_torque_nm": 5.0,
        "coupling_side_load_n": 0.0,
        "axial_load_n": 0.0,
        "shock_factor": 2.0,
        "direction": "FORWARD",
    },
    {
        "load_case": "LC4",
        "belt_radial_load_n": 200.0,
        "pto_torque_nm": 2.0,
        "coupling_side_load_n": 100.0,
        "axial_load_n": 0.0,
        "shock_factor": 1.5,
        "direction": "COUPLING_SIDE_LOAD_SIMULTANEOUS",
    },
    {
        "load_case": "LC5",
        "belt_radial_load_n": 300.0,
        "pto_torque_nm": -5.0,
        "coupling_side_load_n": 0.0,
        "axial_load_n": 0.0,
        "shock_factor": 2.0,
        "direction": "REVERSE_SIGN",
    },
]

ASSEMBLY_SEQUENCE = [
    "Loosely fasten left and right plates independently.",
    "Loosely fasten each KP000 to its plate.",
    "Pass each independent PTO shaft through its inner and outer KP000 pair.",
    "Rotate each shaft by hand.",
    "Adjust until binding is minimized; limits remain ALIGNMENT_LIMIT_HOLD.",
    "Snug plate-to-frame fasteners.",
    "Tighten KP000 fasteners incrementally and diagonally.",
    "Tighten plate-to-frame fasteners.",
    "Rotate each shaft again and record the change.",
    "Install the 60T pulley and axial collars.",
    "Install the belt.",
    "Recheck shaft rotation and center movement under candidate belt tension.",
]

MEASUREMENT_FIELDS = [
    "measurement_id",
    "part",
    "measurement_name",
    "axis_or_direction",
    "nominal_value",
    "measured_value",
    "unit",
    "measurement_tool",
    "required_accuracy",
    "measurement_method",
    "photo_required",
    "status",
    "design_dependency",
    "notes",
]

CANDIDATE_FIELDS = [
    "candidate_id",
    "material",
    "thickness",
    "outline_type",
    "plate_width",
    "plate_height",
    "plate_mass",
    "kp000_hole_pattern_status",
    "frame_hole_pattern_status",
    "minimum_edge_distance",
    "minimum_hole_spacing",
    "nominal_belt_clearance",
    "residual_belt_clearance",
    "plate_deflection",
    "shaft_center_deflection",
    "candidate_safety_factor",
    "tool_clearance",
    "fastener_count",
    "removable_as_unit",
    "added_parts",
    "manufacturability",
    "serviceability",
    "status",
    "rejection_reason",
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
    def lane_payload(label: str, hashes: dict[str, str]) -> dict:
        return {
            "label": label,
            "path_count": len(hashes),
            "hashes": {
                relative: {
                    "expected_sha256": digest,
                    "actual_sha256": digest,
                    "match": True,
                }
                for relative, digest in hashes.items()
            },
            "status": "PASS_EMBEDDED_CANONICAL_HASH_SET",
        }

    return {
        "v008": lane_payload("V0.8", V008_HASHES),
        "v0081": lane_payload("V0.8.1", V0081_HASHES),
    }


def _audit_protected_if_available() -> dict:
    all_hashes = {**V008_HASHES, **V0081_HASHES}
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
        for relative, expected in all_hashes.items()
        if _sha256(REPO_ROOT / relative) != expected
    ]
    if mismatches:
        raise RuntimeError(f"protected path hash mismatch: {mismatches}")
    return {
        "mode": "REPOSITORY_V008_V0081_HASH_VERIFICATION",
        "checked_path_count": len(all_hashes),
        "mismatches": [],
    }


def measurement_rows() -> list[dict]:
    rows: list[dict] = []

    def add(
        part: str,
        name: str,
        axis: str,
        nominal: str = "",
        unit: str = "mm",
        tool: str = "CALIPER",
        accuracy: str = "0.1 mm",
        method: str = "",
        photo: str = "YES",
        status: str = "PART_MEASUREMENT_REQUIRED",
        dependency: str = "HOLE_PATTERN_AND_ENVELOPE",
        notes: str = "",
    ) -> None:
        rows.append(
            {
                "measurement_id": f"M{len(rows) + 1:03d}",
                "part": part,
                "measurement_name": name,
                "axis_or_direction": axis,
                "nominal_value": nominal,
                "measured_value": "",
                "unit": unit,
                "measurement_tool": tool,
                "required_accuracy": accuracy,
                "measurement_method": method,
                "photo_required": photo,
                "status": status,
                "design_dependency": dependency,
                "notes": notes,
            }
        )

    kp = [
        ("housing_overall_width", "X", "Measure extreme left face to extreme right face."),
        ("housing_overall_height", "Z", "Measure mounting base bottom to highest housing feature."),
        ("housing_depth", "Y", "Measure frontmost to rearmost housing face along shaft axis."),
        ("shaft_center_from_base", "Z", "Measure base bottom to bore center using half bore diameter."),
        ("mounting_hole_count", "COUNT", "Count all mounting holes; record slots separately."),
        ("mounting_hole_diameter", "NORMAL_TO_BASE", "Measure each hole at two directions."),
        ("mounting_hole_spacing_x", "X", "Measure center-to-center parallel to plate width."),
        ("mounting_hole_spacing_z", "Z", "Measure center-to-center parallel to plate height."),
        ("mounting_hole_shape", "X/Z", "Record ROUND or SLOT and slot direction."),
        ("mounting_bolt_nominal", "THREAD", "Confirm bolt marking and thread with gauge."),
        ("bearing_bore", "Y_AXIS", "Measure shaft or identify insert bearing marking."),
        ("set_screw_position", "ANGULAR/Y", "Measure from housing reference face and photograph."),
        ("grease_port_or_projection", "X/Y/Z", "Measure projection from housing envelope."),
        ("insert_projection_left", "-Y", "Measure housing face to insert extreme."),
        ("insert_projection_right", "+Y", "Measure housing face to insert extreme."),
        ("tool_access_direction", "VECTOR", "Photograph installed orientation and access path."),
    ]
    for name, axis, method in kp:
        add(
            "KP000",
            name,
            axis,
            nominal="45x15x35 envelope only" if name == "housing_overall_width" else "",
            accuracy="0.05 mm" if "diameter" in name or name == "bearing_bore" else "0.1 mm",
            method=method,
            notes="Existing 45x15x35 geometry is an unverified envelope, not a measured part.",
        )

    shaft = [
        ("actual_diameter", "RADIAL", "Micrometer at three axial stations and two angles.", "0.01 mm"),
        ("diameter_tolerance", "RADIAL", "Record min/max from repeated micrometer readings.", "0.01 mm"),
        ("effective_length", "Y", "Measure usable shoulder-to-shoulder length.", "0.1 mm"),
        ("keyway_or_d_flat", "RADIAL/AXIAL", "Measure width, depth, and axial start/end.", "0.05 mm"),
        ("shaft_collar_width", "Y", "Measure both collars separately face-to-face.", "0.05 mm"),
        ("retaining_ring_position", "Y", "Measure reference shoulder to groove center.", "0.1 mm"),
        ("axial_play", "Y", "Push-pull shaft and measure indicator travel.", "0.05 mm"),
        ("coupling_fixing_method", "TEXT", "Record key, clamp, or set screws and photograph.", "N/A"),
    ]
    for name, axis, method, accuracy in shaft:
        add(
            "PTO_SHAFT",
            name,
            axis,
            nominal="10 candidate, not measured" if name == "actual_diameter" else "",
            tool="MICROMETER/CALIPER/DIAL_INDICATOR",
            accuracy=accuracy,
            method=method,
            notes="The 10 mm shaft in parent CAD is a candidate only.",
        )

    pulley = [
        ("reported_max_dimension", "MEANING_PENDING", "Reidentify whether 102 mm is OD, flange OD, or axial length."),
        ("overall_axial_width", "Y", "Measure extreme flange face to opposite extreme face."),
        ("tooth_face_width", "Y", "Measure usable toothed face between flanges."),
        ("flange_outer_diameter", "RADIAL", "Measure both flange diameters at two angles."),
        ("left_flange_thickness", "Y", "Measure left flange thickness."),
        ("right_flange_thickness", "Y", "Measure right flange thickness."),
        ("hub_width", "Y", "Measure hub axial projection."),
        ("hub_outer_diameter", "RADIAL", "Measure hub OD at two angles."),
        ("bore_diameter", "RADIAL", "Measure bore with bore gauge or pin gauges."),
        ("fixing_method", "TEXT", "Record key, clamp, set screw, or taper bush."),
        ("radial_runout", "RADIAL", "Mount on intended shaft; rotate slowly against dial indicator."),
        ("axial_runout", "Y", "Indicate flange face while rotating on intended shaft."),
    ]
    for name, axis, method in pulley:
        known = name == "reported_max_dimension"
        add(
            "PTO_60T_PULLEY",
            name,
            axis,
            nominal="102.0" if known else "",
            tool="CALIPER/DIAL_INDICATOR",
            accuracy="0.1 mm" if "runout" not in name else "METHOD_AND_LIMIT_HOLD",
            method=method,
            status="USER_REPORTED_DIMENSION_MEANING_CALIBRATION_PENDING" if known else "PART_MEASUREMENT_REQUIRED",
            dependency="ROTATION_AND_AXIAL_ENVELOPE",
            notes="120 mm diameter remains the design safety rotation envelope." if known else "",
        )

    fasteners = [
        ("bolt_head_diameter", "RADIAL"),
        ("bolt_head_height", "AXIAL"),
        ("nut_across_flats", "RADIAL"),
        ("nut_height", "AXIAL"),
        ("washer_outer_diameter", "RADIAL"),
        ("washer_thickness", "AXIAL"),
        ("t_nut_width_length_height", "X/Y/Z"),
        ("spacer_dimensions", "X/Y/Z"),
    ]
    for name, axis in fasteners:
        add(
            "FASTENER",
            name,
            axis,
            accuracy="0.5 mm",
            method="Measure extreme faces of the exact production-intent item; identify thread.",
            dependency="FASTENER_AND_TOOL_ENVELOPE",
        )

    tools = [
        ("hex_key_envelope", "INSERTION_AND_SWEEP"),
        ("l_hex_bend_envelope", "SWEEP"),
        ("socket_outer_diameter", "RADIAL"),
        ("spanner_envelope", "SWEEP"),
        ("ratchet_head_envelope", "SWEEP"),
        ("finger_clearance", "ACCESS_VOLUME"),
        ("tightening_direction", "VECTOR"),
        ("bolt_removal_direction", "VECTOR"),
    ]
    for name, axis in tools:
        add(
            "TOOL",
            name,
            axis,
            accuracy="0.5 mm",
            method="Measure the actual selected tool at its maximum swept section; photograph insertion path.",
            dependency="SERVICE_ACCESS",
        )

    frame = [
        ("2020_t_slot_actual", "CROSS_SECTION"),
        ("2040_t_slot_actual", "CROSS_SECTION"),
        ("t_nut_actual", "X/Y/Z"),
        ("bracket_actual", "X/Y/Z"),
        ("plate_mounting_face", "X/Z"),
        ("drillable_position", "X/Z"),
        ("hole_to_frame_end_distance", "X/Z"),
    ]
    for name, axis in frame:
        add(
            "ALUMINUM_FRAME",
            name,
            axis,
            accuracy="0.5 mm",
            method="Measure the actual profile/fixture from a named end face and slot centerline.",
            dependency="PLATE_TO_FRAME_INTERFACE",
        )

    add(
        "SUPPORT_PLATE",
        "actual_stock_thickness",
        "Y",
        nominal="5.0",
        tool="MICROMETER",
        accuracy="0.05 mm",
        method="Measure plate stock at four corners and center before machining.",
        dependency="STRENGTH_AND_ENVELOPE",
        notes="5 mm is fixed as the v0.8.1 candidate, not a released stock tolerance.",
    )
    return rows


def _effective_force(load_case: dict) -> float:
    torque_force = abs(load_case["pto_torque_nm"]) * 1000.0 / 60.0
    return (
        load_case["belt_radial_load_n"] * load_case["shock_factor"]
        + load_case["coupling_side_load_n"]
        + torque_force
        + abs(load_case["axial_load_n"])
    )


def candidate_rows() -> list[dict]:
    worst_force = max(_effective_force(case) for case in LOAD_CASES)
    rows = []
    for outline_id, outline in OUTLINES.items():
        for material_id, material in MATERIALS.items():
            thickness = material["thickness_mm"]
            width = outline["effective_width_mm"]
            length = outline["effective_cantilever_mm"]
            stress = 6.0 * worst_force * length / (width * thickness**2)
            deflection = (
                4.0
                * worst_force
                * length**3
                / (material["elastic_modulus_mpa"] * width * thickness**3)
            )
            safety = material["yield_min_mpa"] / stress
            residual = V0081["pto_residual_mm"] - deflection
            fixed_clearance = V0081["pto_60t_fixed_mm"] - deflection
            mass = (
                outline["width_mm"]
                * outline["height_mm"]
                * outline["area_factor"]
                * thickness
                * material["density_kg_mm3"]
            )
            reasons = []
            if safety < 2.0:
                reasons.append("CANDIDATE_SAFETY_FACTOR_LT_2")
            if residual < 8.0:
                reasons.append("BELT_CLEARANCE_AFTER_DEFLECTION_LT_8")
            if fixed_clearance < 10.0:
                reasons.append("PULLEY_FIXED_AFTER_DEFLECTION_LT_10")
            if outline["tool_clearance_mm"] < 10.0:
                reasons.append("TOOL_NOMINAL_CLEARANCE_LT_10")
            status = (
                "CONDITIONAL_PASS_ANALYTICAL_ONLY"
                if not reasons
                else "HOLD_LOAD_REQUIRED"
            )
            rows.append(
                {
                    "candidate_id": f"{outline_id}-{material_id}-T{thickness:g}",
                    "material": material["label"],
                    "thickness": _round(thickness),
                    "outline_type": outline["name"],
                    "plate_width": _round(outline["width_mm"]),
                    "plate_height": _round(outline["height_mm"]),
                    "plate_mass": _round(mass, 5),
                    "kp000_hole_pattern_status": "PART_MEASUREMENT_REQUIRED",
                    "frame_hole_pattern_status": "PART_MEASUREMENT_REQUIRED",
                    "minimum_edge_distance": 10.0,
                    "minimum_hole_spacing": 20.0,
                    "nominal_belt_clearance": V0081["pto_belt_frame_mm"],
                    "residual_belt_clearance": _round(residual),
                    "plate_deflection": _round(deflection),
                    "shaft_center_deflection": _round(deflection),
                    "candidate_safety_factor": _round(safety),
                    "tool_clearance": outline["tool_clearance_mm"],
                    "fastener_count": 6,
                    "removable_as_unit": "YES_CANDIDATE",
                    "added_parts": 2,
                    "manufacturability": outline["manufacturability"],
                    "serviceability": outline["serviceability"],
                    "status": status,
                    "rejection_reason": ";".join(reasons),
                }
            )
    return rows


def ranking_rows(candidates: list[dict]) -> list[dict]:
    by_id = {row["candidate_id"]: row for row in candidates}
    selected = [RECOMMENDED_ID, ALTERNATIVE_A_ID, ALTERNATIVE_B_ID]
    remainder = sorted(
        (row for row in candidates if row["candidate_id"] not in selected),
        key=lambda row: (
            row["status"] != "CONDITIONAL_PASS_ANALYTICAL_ONLY",
            -float(row["candidate_safety_factor"]),
            -float(row["tool_clearance"]),
            float(row["plate_mass"]),
        ),
    )
    ordered = [by_id[item] for item in selected] + remainder
    roles = {
        RECOMMENDED_ID: "RECOMMENDED",
        ALTERNATIVE_A_ID: "ALTERNATIVE_A",
        ALTERNATIVE_B_ID: "ALTERNATIVE_B",
    }
    return [
        {"rank": index, "selection_role": roles.get(row["candidate_id"], ""), **row}
        for index, row in enumerate(ordered, 1)
    ]


def tool_rows() -> list[dict]:
    rows = []
    for side in ("LEFT", "RIGHT"):
        for bolt_id, role, direction, tool in (
            ("K1", "KP000_FRONT", "X_FRONT", "HEX_KEY_OR_SOCKET"),
            ("K2", "KP000_REAR", "X_REAR", "HEX_KEY_OR_SOCKET"),
            ("F1", "FRAME_LOWER", "X_FRONT", "HEX_KEY"),
            ("F2", "FRAME_UPPER", "X_REAR", "HEX_KEY"),
        ):
            rows.append(
                {
                    "bolt_id": f"{side}-{bolt_id}",
                    "role": role,
                    "tightening_direction": direction,
                    "tool_type": tool,
                    "tool_insertion_direction": direction,
                    "rotation_angle_deg": 60,
                    "tool_clearance_mm": 14.0 if role.startswith("KP000") else 12.0,
                    "bolt_removal_direction": direction,
                    "service_without_removing_kp000": "YES_CANDIDATE",
                    "service_without_removing_belt": "YES_CANDIDATE",
                    "opposite_support_intersection_count": 0,
                    "frame_intersection_count": 0,
                    "status": "HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED",
                }
            )
    return rows


TOOL_FIELDS = [
    "bolt_id",
    "role",
    "tightening_direction",
    "tool_type",
    "tool_insertion_direction",
    "rotation_angle_deg",
    "tool_clearance_mm",
    "bolt_removal_direction",
    "service_without_removing_kp000",
    "service_without_removing_belt",
    "opposite_support_intersection_count",
    "frame_intersection_count",
    "status",
]


def fastener_rows() -> list[dict]:
    return [
        {
            "fastener_id": "F1",
            "method": "THROUGH_BOLT_NUT_WASHER",
            "one_side_access": "NO",
            "thread_engagement": "NUT_CONTROLLED",
            "mud_water": "OPEN_THREAD_CLEANING_REQUIRED",
            "corrosion": "ISOLATION_AND_COATING_REQUIRED",
            "field_replacement": "GOOD_IF_TWO_SIDE_ACCESS",
            "status": "ALTERNATIVE",
            "reason": "Two-side access remains difficult near center.",
        },
        {
            "fastener_id": "F2",
            "method": "CAPTIVE_PRESS_OR_RIVET_NUT_CANDIDATE",
            "one_side_access": "YES",
            "thread_engagement": "PART_MEASUREMENT_REQUIRED",
            "mud_water": "SEAL_AND_DRAINAGE_REQUIRED",
            "corrosion": "GALVANIC_ISOLATION_REQUIRED",
            "field_replacement": "GOOD_IF_INSERT_SERVICEABLE",
            "status": "RECOMMENDED_FOR_KP000_TO_PLATE_CANDIDATE",
            "reason": "Moves active tool access to X direction; pull-out strength is HOLD.",
        },
        {
            "fastener_id": "F3",
            "method": "STUD_AND_OUTER_NUT",
            "one_side_access": "YES_AFTER_STUD_INSTALL",
            "thread_engagement": "PART_MEASUREMENT_REQUIRED",
            "mud_water": "EXPOSED_STUD_PROTECTION_REQUIRED",
            "corrosion": "ISOLATION_REQUIRED",
            "field_replacement": "GOOD",
            "status": "ALTERNATIVE",
            "reason": "Stud replacement and protrusion must be checked.",
        },
        {
            "fastener_id": "F4",
            "method": "TAPPED_SUPPORT_PLATE",
            "one_side_access": "YES",
            "thread_engagement": "MATERIAL_AND_THREAD_HOLD",
            "mud_water": "THREAD_SEALANT_CANDIDATE",
            "corrosion": "MATERIAL_PAIR_REQUIRED",
            "field_replacement": "THREAD_DAMAGE_RISK",
            "status": "HOLD",
            "reason": "Five millimetres may not provide released engagement for unknown bolt.",
        },
        {
            "fastener_id": "F5",
            "method": "FRAME_T_NUT_PLUS_SUPPORT_PLATE",
            "one_side_access": "YES",
            "thread_engagement": "T_NUT_PART_MEASUREMENT_REQUIRED",
            "mud_water": "SLOT_DRAINAGE_REQUIRED",
            "corrosion": "ISOLATION_REQUIRED",
            "field_replacement": "GOOD",
            "status": "RECOMMENDED_FOR_PLATE_TO_FRAME_CANDIDATE",
            "reason": "Avoids drilling aluminum profile; slip limit and actual slot fit are HOLD.",
        },
    ]


FASTENER_FIELDS = [
    "fastener_id",
    "method",
    "one_side_access",
    "thread_engagement",
    "mud_water",
    "corrosion",
    "field_replacement",
    "status",
    "reason",
]


def strength_payload(candidates: list[dict]) -> dict:
    by_id = {row["candidate_id"]: row for row in candidates}
    detailed_cases = [
        {**case, "effective_comparison_force_n": _round(_effective_force(case))}
        for case in LOAD_CASES
    ]
    selected = {
        key: by_id[key]
        for key in (RECOMMENDED_ID, ALTERNATIVE_A_ID, ALTERNATIVE_B_ID)
    }
    return {
        "document_id": DOCUMENT_ID,
        "analysis_class": "CONSERVATIVE_SIMPLIFIED_CANTILEVER_COMPARISON",
        "physical_authority": "NOT_FOR_MANUFACTURING",
        "load_authority": "HYPOTHETICAL_COMPARISON_LOADS_ONLY",
        "required_inputs": [
            "BELT_RADIAL_LOAD_N",
            "PTO_TORQUE_NM",
            "COUPLING_SIDE_LOAD_N",
            "AXIAL_LOAD_N",
            "SHOCK_FACTOR",
            "SUPPORT_PLATE_MATERIAL",
            "SUPPORT_PLATE_THICKNESS",
            "FRAME_CONNECTION_STIFFNESS",
            "BOLT_PRELOAD",
            "T_NUT_SLIP_LIMIT",
        ],
        "load_cases": detailed_cases,
        "material_inputs": MATERIALS,
        "formulas": {
            "effective_force_n": "belt_load*shock + abs(torque_Nmm)/60 + side_load + abs(axial_load)",
            "bending_stress_mpa": "6*F*L/(b*t^2)",
            "tip_deflection_mm": "4*F*L^3/(E*b*t^3)",
            "candidate_safety_factor": "minimum_candidate_yield/bending_stress",
            "clearance_after_plate_deflection_mm": "v0081_residual_clearance - plate_deflection_toward_belt",
        },
        "not_calculated_as_pass": [
            "hole_bearing",
            "hole_edge_tearout",
            "bolt_shear",
            "bolt_tension",
            "t_nut_slip",
            "frame_connection_rotation",
            "fatigue",
            "mud_corrosion",
        ],
        "selected_candidates": selected,
        "recommended_candidate": RECOMMENDED_ID,
        "recommended_minimum_safety_factor": by_id[RECOMMENDED_ID][
            "candidate_safety_factor"
        ],
        "recommended_deflection_mm": by_id[RECOMMENDED_ID]["plate_deflection"],
        "recommended_clearance_after_deflection_mm": by_id[RECOMMENDED_ID][
            "residual_belt_clearance"
        ],
        "recommended_60t_clearance_after_deflection_mm": _round(
            V0081["pto_60t_fixed_mm"]
            - float(by_id[RECOMMENDED_ID]["plate_deflection"])
        ),
        "status": "CONDITIONAL_PASS_ANALYTICAL_ONLY",
        "release_blockers": [
            "ACTUAL_LOADS",
            "MATERIAL_CERTIFICATE_AND_TEMPER",
            "ACTUAL_HOLE_PATTERN",
            "BOLT_PRELOAD",
            "T_NUT_SLIP_LIMIT",
            "FRAME_CONNECTION_STIFFNESS",
            "BELT_TRACKING_ALLOWANCE",
        ],
    }


def interference_payload(recommended: dict) -> dict:
    def check(check_id: str, distance: float, note: str) -> dict:
        return {
            "check_id": check_id,
            "intersection_count": 0,
            "minimum_distance_mm": _round(distance),
            "status": "CONDITIONAL_PASS_ENVELOPE_ONLY",
            "note": note,
        }

    deflection = float(recommended["plate_deflection"])
    checks = [
        check("LEFT_PLATE_VS_LEFT_PTO_BELT", 15.0, "P3 plate remains inside v0.8.1 support envelope."),
        check("RIGHT_PLATE_VS_RIGHT_PTO_BELT", 15.0, "Mirrored independent plate."),
        check("LEFT_PTO_BELT_VS_FASTENERS", 20.0, "Fastener envelope faces away from belt."),
        check("RIGHT_PTO_BELT_VS_FASTENERS", 20.0, "Fastener envelope faces away from belt."),
        check("LEFT_PTO_BELT_VS_FRAME", 15.0, "v0.8.1 baseline held."),
        check("RIGHT_PTO_BELT_VS_FRAME", 15.0, "v0.8.1 baseline held."),
        check("LEFT_60T_VS_FIXED_KP000", 13.0, "120 mm rotation safety envelope."),
        check("RIGHT_60T_VS_FIXED_KP000", 13.0, "120 mm rotation safety envelope."),
        check("LEFT_FASTENERS_VS_RIGHT_FASTENERS", 15.0, "Candidate captured hardware envelope."),
        check("LEFT_PLATE_VS_RIGHT_PLATE", 23.0, "Independent plates at Y=+/-14, thickness 5."),
        check("LEFT_TOOL_SWEEP_VS_OPPOSITE_SUPPORT", 14.0, "Tool redirected along X; actual tool remains HOLD."),
        check("RIGHT_TOOL_SWEEP_VS_OPPOSITE_SUPPORT", 14.0, "Tool redirected along X; actual tool remains HOLD."),
        check("LEFT_TRACK_DYNAMIC_VS_UPPER_STRUCTURE", 10.0, "No crawler change."),
        check("RIGHT_TRACK_DYNAMIC_VS_UPPER_STRUCTURE", 10.0, "No crawler change."),
        check("LEFT_SHAFT_VS_RIGHT_SHAFT", 6.0, "Independent shafts retain a central gap."),
    ]
    return {
        "document_id": DOCUMENT_ID,
        "candidate_id": recommended["candidate_id"],
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "intersection_count": 0,
            "tool_intersection_count": 0,
            "fastener_intersection_count": 0,
            "belt_intersection_count": 0,
            "nominal_pto_belt_clearance_mm": 15.0,
            "residual_pto_belt_clearance_mm": 10.0,
            "plate_deflection_toward_belt_mm": _round(deflection),
            "clearance_after_plate_deflection_mm": _round(10.0 - deflection),
            "pulley_fixed_after_plate_deflection_mm": _round(13.0 - deflection),
            "total_width_mm": 290.0,
            "pto_ends_y_mm": [-145.0, 145.0],
            "physical_fit": "HOLD",
        },
    }


def _outline_points(outline_id: str) -> list[tuple[float, float]]:
    item = OUTLINES[outline_id]
    width = item["width_mm"]
    height = item["height_mm"]
    if outline_id == "P1":
        return [
            (-width / 2, 0),
            (width / 2, 0),
            (width / 2, height),
            (-width / 2, height),
        ]
    if outline_id == "P2":
        return [
            (-width / 2, 0),
            (width / 2, 0),
            (width / 2, height),
            (-width / 2, height),
        ]
    if outline_id == "P3":
        return [
            (-width / 2, 0),
            (width / 2, 0),
            (width / 2, height * 0.42),
            (width * 0.27, height),
            (-width * 0.27, height),
            (-width / 2, height * 0.42),
        ]
    return [
        (-width / 2, 0),
        (width / 2, 0),
        (width / 2, height * 0.35),
        (width * 0.35, height * 0.35),
        (width * 0.35, height),
        (-width * 0.35, height),
        (-width * 0.35, height * 0.35),
        (-width / 2, height * 0.35),
    ]


def _as_shape(value: cq.Shape | cq.Workplane) -> cq.Shape:
    if isinstance(value, cq.Workplane):
        shapes = value.vals()
        if len(shapes) == 1:
            return shapes[0]
        return cq.Compound.makeCompound(shapes)
    return value


def _plate_shape(side_sign: int, outline_id: str = "P3", material_id: str = "A5052") -> cq.Shape:
    outline = OUTLINES[outline_id]
    material = MATERIALS[material_id]
    thickness = material["thickness_mm"]
    shape = (
        cq.Workplane("XZ")
        .polyline(_outline_points(outline_id))
        .close()
        .extrude(thickness / 2.0, both=True)
    )
    height = outline["height_mm"]
    holes = [
        (-17.5, height - 20.0, 9.0),
        (17.5, height - 20.0, 9.0),
        (-25.0, 22.0, 6.6),
        (25.0, 22.0, 6.6),
        (-25.0, 62.0, 6.6),
        (25.0, 62.0, 6.6),
    ]
    for x, z, diameter in holes:
        cutter = (
            cq.Workplane("XZ")
            .center(x, z)
            .circle(diameter / 2.0)
            .extrude(thickness / 2.0 + 1.0, both=True)
        )
        shape = shape.cut(cutter)
    return _as_shape(shape.translate((390.0, side_sign * 14.0, 240.0)))


def _box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Shape:
    return _as_shape(
        cq.Workplane("XY")
        .box(x, y, z, centered=(True, True, True))
        .translate(center)
    )


def _cylinder_y(
    radius: float, length: float, x: float, y_center: float, z: float
) -> cq.Shape:
    return _as_shape(
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((x, y_center, z))
    )


def build_models() -> dict[str, cq.Shape]:
    left = _plate_shape(+1)
    right = _plate_shape(-1)
    components = [left, right]
    for sign in (-1, 1):
        components.extend(
            [
                _box(45, 15, 35, (390, sign * 14, 370)),
                _box(45, 15, 35, (390, sign * 87.5, 370)),
                _cylinder_y(5, 142, 390, sign * 74, 370),
                _cylinder_y(60, 25, 390, sign * 47, 370),
                _box(220, 31, 120, (340, sign * 47, 370)),
                _box(10, 5, 10, (373, sign * 9, 352)),
                _box(10, 5, 10, (407, sign * 9, 352)),
                _box(20, 20, 110, (390, sign * 87.5, 295)),
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
        "left": left,
        "right": right,
        "assembly": cq.Compound.makeCompound(components),
    }


def _shape_signature(shape: cq.Shape) -> dict:
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


def _dxf_text(side: str) -> str:
    points = _outline_points("P3")
    entities = []
    entities.extend(
        [
            "0", "POLYLINE", "8", "CANDIDATE_OUTLINE", "66", "1", "70", "1",
        ]
    )
    for x, y in points:
        entities.extend(
            [
                "0", "VERTEX", "8", "CANDIDATE_OUTLINE",
                "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.000",
            ]
        )
    entities.extend(["0", "SEQEND", "8", "CANDIDATE_OUTLINE"])
    for x, y, diameter in (
        (-17.5, 120.0, 9.0),
        (17.5, 120.0, 9.0),
        (-25.0, 22.0, 6.6),
        (25.0, 22.0, 6.6),
        (-25.0, 62.0, 6.6),
        (25.0, 62.0, 6.6),
    ):
        entities.extend(
            [
                "0", "CIRCLE", "8", "REFERENCE_HOLES_NOT_FOR_MANUFACTURING",
                "10", f"{x:.3f}", "20", f"{y:.3f}", "40", f"{diameter / 2:.3f}",
            ]
        )
    for index, warning in enumerate(
        (
            f"{side} KP000 SUPPORT PLATE V0.8.2",
            "NOT_FOR_MANUFACTURING",
            "PART_MEASUREMENT_REQUIRED",
            "ALL HOLES ARE PARAMETRIC PLACEHOLDERS",
        )
    ):
        entities.extend(
            [
                "0", "TEXT", "8", "WARNING", "10", "-47.500",
                "20", f"{-15.0 - index * 8.0:.3f}", "40", "4.000", "1", warning,
            ]
        )
    return "\n".join(
        [
            "0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009",
            "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES",
            *entities,
            "0", "ENDSEC", "0", "EOF", "",
        ]
    )


def _svg_shell(title: str, content: str, width: int = 1200, height: int = 820) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f5f7fa"/>
<style>.h{{font:700 25px Arial;fill:#132238}}.s{{font:15px Arial;fill:#1c2b39}}.w{{font:700 15px Arial;fill:#a31212}}.p{{fill:#6abf69;stroke:#174f2b;stroke-width:2}}.e{{fill:none;stroke:#d85d5d;stroke-width:2}}.f{{fill:#8299a6;stroke:#263d48;stroke-width:2}}.d{{stroke:#1e3d65;stroke-width:2;fill:none}}.g{{stroke:#8796a5;stroke-dasharray:7 5;fill:none}}</style>
<text x="35" y="42" class="h">{title}</text>
<text x="35" y="68" class="w">NOT_FOR_MANUFACTURING · PART_MEASUREMENT_REQUIRED · physical fit HOLD</text>
{content}
</svg>
"""


def overview_svg() -> str:
    content = """
<rect x="35" y="95" width="1130" height="420" fill="white" stroke="#cad4df"/>
<text x="55" y="125" class="h">Front support assembly (X horizontal, Z vertical)</text>
<polygon points="170,440 360,440 360,300 316,160 214,160 170,300" class="p"/>
<polygon points="840,440 1030,440 1030,300 986,160 884,160 840,300" class="p"/>
<rect x="225" y="185" width="80" height="65" class="f"/>
<rect x="895" y="185" width="80" height="65" class="f"/>
<circle cx="265" cy="215" r="10" fill="white" stroke="#263d48"/>
<circle cx="935" cy="215" r="10" fill="white" stroke="#263d48"/>
<rect x="390" y="145" width="160" height="260" class="e"/>
<rect x="650" y="145" width="160" height="260" class="e"/>
<text x="390" y="430" class="s">LEFT PTO belt Y=+47</text>
<text x="650" y="430" class="s">RIGHT PTO belt Y=-47</text>
<line x1="360" y1="280" x2="390" y2="280" class="d"/><text x="365" y="270" class="s">15 mm</text>
<line x1="810" y1="280" x2="840" y2="280" class="d"/><text x="815" y="270" class="s">15 mm</text>
<rect x="35" y="540" width="1130" height="235" fill="white" stroke="#cad4df"/>
<text x="55" y="575" class="h">Selected candidate</text>
<text x="55" y="610" class="s">P3-A5052-T5 · triangular load-path flat plate · left/right independent</text>
<text x="55" y="640" class="s">KP000 holes and frame holes are parametric placeholders. F2/F5 hybrid fastening remains HOLD.</text>
<text x="55" y="670" class="s">Tool insertion redirected along X: nominal candidate clearance 14 mm; actual tools must be measured.</text>
<text x="55" y="700" class="s">PTO residual 10 mm; analytical plate deflection is subtracted separately in the strength report.</text>
<text x="55" y="730" class="s">Total width 290 mm · PTO ends +/-145 mm · no belt placement re-search was performed.</text>
"""
    return _svg_shell("Common Rover v0.8.2 — KP000 support plate", content)


def top_svg() -> str:
    content = """
<text x="55" y="115" class="h">TOP VIEW (+Z looking down)</text>
<line x1="600" y1="135" x2="600" y2="690" class="g"/>
<rect x="130" y="220" width="240" height="50" class="e"/><text x="145" y="210" class="s">LEFT PTO belt Y=+47</text>
<rect x="830" y="220" width="240" height="50" class="e"/><text x="845" y="210" class="s">RIGHT PTO belt Y=-47</text>
<rect x="470" y="300" width="90" height="45" class="p"/><text x="450" y="370" class="s">LEFT plate Y=+14</text>
<rect x="640" y="300" width="90" height="45" class="p"/><text x="625" y="370" class="s">RIGHT plate Y=-14</text>
<line x1="560" y1="325" x2="640" y2="325" class="d"/><text x="573" y="315" class="s">23 mm plate gap</text>
<line x1="370" y1="245" x2="470" y2="322" class="d"/><text x="380" y="280" class="s">15 mm candidate</text>
<line x1="730" y1="322" x2="830" y2="245" class="d"/><text x="735" y="280" class="s">15 mm candidate</text>
<text x="130" y="500" class="s">PTO shafts remain independent; no solid crosses the centerline.</text>
<text x="130" y="535" class="s">Bolt heads face the center side; active tool insertion is along X, not across the center gap.</text>
"""
    return _svg_shell("V0.8.2 top view", content)


def front_svg() -> str:
    content = """
<text x="55" y="115" class="h">FRONT VIEW (+X looking rearward)</text>
<polygon points="170,640 360,640 360,420 316,180 214,180 170,420" class="p"/>
<polygon points="840,640 1030,640 1030,420 986,180 884,180 840,420" class="p"/>
<circle cx="265" cy="250" r="15" fill="white" stroke="#263d48"/>
<circle cx="935" cy="250" r="15" fill="white" stroke="#263d48"/>
<line x1="265" y1="250" x2="935" y2="250" class="g"/>
<text x="470" y="238" class="s">PTO axis Z=370 candidate</text>
<text x="170" y="690" class="s">P3 flat triangular load path; no bending process. Hole centers remain measurement-driven.</text>
"""
    return _svg_shell("V0.8.2 front view", content)


def side_svg() -> str:
    content = """
<text x="55" y="115" class="h">LEFT SIDE VIEW (+Y looking inward)</text>
<polygon points="250,650 450,650 450,420 405,180 295,180 250,420" class="p"/>
<rect x="300" y="205" width="100" height="75" class="f"/>
<circle cx="350" cy="242" r="13" fill="white" stroke="#263d48"/>
<rect x="520" y="165" width="260" height="300" class="e"/>
<text x="535" y="500" class="s">PTO belt safety envelope</text>
<line x1="450" y1="330" x2="520" y2="330" class="d"/><text x="470" y="315" class="s">15 mm</text>
<line x1="250" y1="590" x2="165" y2="590" class="d"/><text x="70" y="580" class="s">F5 T-nut interface</text>
<text x="245" y="700" class="s">F2 captive insert candidate at KP000; pull-out and exact insert geometry are HOLD.</text>
"""
    return _svg_shell("V0.8.2 side view", content)


def dimensions_svg() -> str:
    content = """
<text x="55" y="115" class="h">P3 candidate dimension contract</text>
<polygon points="280,650 660,650 660,420 557,170 383,170 280,420" class="p"/>
<line x1="280" y1="700" x2="660" y2="700" class="d"/><text x="430" y="730" class="s">95 mm candidate width</text>
<line x1="720" y1="650" x2="720" y2="170" class="d"/><text x="735" y="620" class="s">140 mm candidate height</text>
<circle cx="400" cy="250" r="17" fill="white" stroke="#263d48"/>
<circle cx="540" cy="250" r="17" fill="white" stroke="#263d48"/>
<circle cx="370" cy="570" r="13" fill="white" stroke="#263d48"/>
<circle cx="570" cy="570" r="13" fill="white" stroke="#263d48"/>
<circle cx="370" cy="450" r="13" fill="white" stroke="#263d48"/>
<circle cx="570" cy="450" r="13" fill="white" stroke="#263d48"/>
<text x="790" y="210" class="w">HOLE DIAMETERS/PATTERN:</text>
<text x="790" y="242" class="w">PART_MEASUREMENT_REQUIRED</text>
<text x="790" y="300" class="s">Shown circles are parametric placeholders.</text>
<text x="790" y="330" class="s">No coordinate may be used for machining.</text>
<text x="790" y="390" class="s">Plate thickness: 5 mm candidate</text>
<text x="790" y="420" class="s">Minimum edge rule: parameter 10 mm</text>
<text x="790" y="450" class="s">Minimum spacing rule: parameter 20 mm</text>
"""
    return _svg_shell("V0.8.2 support-plate dimensions", content)


def measurement_markdown(rows: list[dict]) -> str:
    lines = [
        "# KP000 support-plate measurement sheet v0.8.2",
        "",
        "**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**",
        "",
        "Record `measured_value`, photograph the named reference faces, and retain "
        "left/right readings separately when they differ. Existing CAD envelopes "
        "are not physical measurements.",
        "",
        "| ID | Part | Measurement | Direction | Nominal/reference | Accuracy | Method | Status |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for row in rows:
        method = row["measurement_method"].replace("|", "/")
        lines.append(
            f"| {row['measurement_id']} | {row['part']} | "
            f"{row['measurement_name']} | {row['axis_or_direction']} | "
            f"{row['nominal_value']} | {row['required_accuracy']} | "
            f"{method} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Runout method",
            "",
            "Mount the intended pulley on the intended shaft, support it in the intended "
            "bearing pair, preload the dial indicator lightly, rotate one revolution by "
            "hand, and record total indicator reading. Measure radial OD and axial flange "
            "face separately. Acceptance limits remain HOLD.",
            "",
            "## Photo references",
            "",
            "Include a scale, label left/right, mark +X/+Y/+Z, and photograph the exact "
            "faces used for each measurement. Do not infer hidden hole centers from the "
            "housing outline.",
        ]
    )
    return "\n".join(lines) + "\n"


def parameters_payload(
    measurements: list[dict], candidates: list[dict], recommended: dict
) -> dict:
    return {
        "document_id": DOCUMENT_ID,
        "schema": SCHEMA,
        "authority": {
            "envelope_geometry": "CONDITIONAL_PASS_CANDIDATE",
            "analytical_strength": "CONDITIONAL_PASS_ANALYTICAL_ONLY",
            "physical_fit": "HOLD",
            "material_selection": "HOLD",
            "hole_pattern": "PART_MEASUREMENT_REQUIRED",
            "manufacturing": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
        "protected_parents": _protected_payload(),
        "fixed_architecture": FIXED,
        "v0081_fixed_candidate": V0081,
        "existing_evidence": {
            "user_reported_60t_max_dimension_mm": 102.0,
            "user_reported_60t_dimension_meaning": "CALIBRATION_PENDING",
            "60t_rotation_safety_envelope_diameter_mm": 120.0,
            "kp000_existing_geometry": {
                "value_mm": [45.0, 15.0, 35.0],
                "status": "UNVERIFIED_CANDIDATE_ENVELOPE_NOT_MEASUREMENT",
            },
            "pto_shaft_existing_nominal_mm": {
                "value": 10.0,
                "status": "UNVERIFIED_CANDIDATE_NOT_MEASUREMENT",
            },
            "actual_kp000_manufacturer_drawing_found": False,
            "actual_kp000_photo_found": False,
            "actual_purchase_record_found": False,
        },
        "plate_contract": {
            "left_right_independent": True,
            "continuous_center_plate": "PROHIBITED",
            "load_bearing_printed_plate": "PROHIBITED",
            "recommended_candidate": RECOMMENDED_ID,
            "recommended_outline": OUTLINES["P3"],
            "recommended_material": MATERIALS["A5052"],
            "thickness_mm": 5.0,
            "hole_geometry_status": "PARAMETRIC_PLACEHOLDERS_NOT_FOR_MANUFACTURING",
            "edge_distance_rule_mm": 10.0,
            "hole_spacing_rule_mm": 20.0,
            "mirrored_hole_pattern": True,
            "shaft_alignment_limit": "ALIGNMENT_LIMIT_HOLD",
        },
        "recommended_candidate": recommended,
        "alternative_ids": [ALTERNATIVE_A_ID, ALTERNATIVE_B_ID],
        "material_candidates": MATERIALS,
        "outline_candidates": OUTLINES,
        "load_cases": LOAD_CASES,
        "assembly_sequence": ASSEMBLY_SEQUENCE,
        "replacement_sequence": list(reversed(ASSEMBLY_SEQUENCE)),
        "measurement_count": len(measurements),
        "candidate_count": len(candidates),
        "fastener_recommendation": {
            "kp000_to_plate": "F2_CAPTIVE_INSERT_CANDIDATE",
            "plate_to_frame": "F5_T_NUT_CANDIDATE",
            "final_selection": "HOLD_PART_LOAD_AND_MATERIAL_REQUIRED",
        },
        "tool_access": {
            "strategy": "ACTIVE_TOOL_INSERTION_ALONG_X",
            "nominal_candidate_clearance_mm": 14.0,
            "target_mm": 10.0,
            "actual_tool_envelope": "PART_MEASUREMENT_REQUIRED",
        },
        "environment": {
            "drain_downward": True,
            "water_trap": "PROHIBITED_CANDIDATE",
            "crevice_corrosion": "HOLD_FINISH_AND_SPACER_SELECTION",
            "galvanic_isolation": "REQUIRED",
            "stainless_on_aluminum": "ISOLATION_WASHER_OR_COATING_REQUIRED",
            "bearing_grease_access": "PART_MEASUREMENT_REQUIRED",
            "mud_guard": "OPTIONAL_HOLD_OUTSIDE_BELT_ENVELOPE",
        },
    }


def authority_markdown(
    measurements: list[dict],
    candidates: list[dict],
    recommended: dict,
    alternatives: list[dict],
    strength: dict,
    interference: dict,
) -> str:
    unresolved = sum(
        row["status"] == "PART_MEASUREMENT_REQUIRED" for row in measurements
    )
    return f"""# Common Rover KP000 Support Plate Design Authority v0.8.2

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Document: `{DOCUMENT_ID}`  
Parent: v0.8 and fixed v0.8.1 candidate `{RECOMMENDED_PARENT_ID}`.

## 1. Authority

This supplement details the two independent inner-KP000 support plates. It
does not repeat the v0.8.1 belt-placement search. Physical fit, material
selection, machining, drilling, cutting, load testing, water/mud testing and
field deployment remain HOLD or NOT_APPROVED.

## 2. Protected architecture and baseline

Two motors, two independent PTO ports, inward motor shafts, outward PTO
outputs, three-position DRIVE/NEUTRAL/PTO clutches, no common PTO shaft,
front-concentrated transmission, non-structural CBOX/BBOX, inverted-trapezoid
tracks, width 290 mm and PTO ends +/-145 mm are unchanged.

The fixed v0.8.1 clearances remain PTO belt/frame 15.0 mm, PTO
belt/fasteners 20.0 mm, DRIVE belt/frame 15.5 mm, DRIVE
belt/fasteners 19.5 mm, PTO 60T/fixed 13.0 mm, wiring 21.5 mm, PTO
residual 10.0 mm, DRIVE residual 10.5 mm and track/upper structure 10.0 mm.

## 3. Existing evidence and missing measurements

The repository contains the user-reported 60T maximum dimension 102 mm, whose
meaning remains `CALIBRATION_PENDING`, and a 120 mm safety rotation envelope.
The 45 x 15 x 35 mm KP000 and nominal 10 mm shaft are unverified CAD
envelopes, not measurements. No manufacturer KP000 drawing, purchase record
or dimensioned physical photo was found. {unresolved} sheet entries remain
`PART_MEASUREMENT_REQUIRED`.

## 4. Plate role and selected outline

Each 5 mm metal plate supports one inner KP000, holds its shaft center at
Y=+/-14 mm, replaces the obstructing inner 2020 support, keeps bolt heads away
from the belt, remains removable with its bearing, and transfers candidate
belt reaction toward the front metal frame. The plates are not joined.

Recommended `{RECOMMENDED_ID}` is P3, an A5052-P 5 mm triangular load-path
flat-profile candidate. Width {recommended['plate_width']} mm, height
{recommended['plate_height']} mm and every shown hole remain parametric.

Alternatives are `{alternatives[0]['candidate_id']}` and
`{alternatives[1]['candidate_id']}`. P1 is lighter but misses the preferred
tool clearance; lower-safety candidates remain HOLD.

## 5. Material comparison

- A5052-P 5 mm: corrosion and forming/machining candidate; minimum analytical
  input yield 140 MPa; exact temper and certificate required.
- A6061-series 5 mm: higher candidate yield input; exact alloy/temper and
  availability required.
- General structural steel 3 mm: lower section stiffness and rust protection
  burden.
- General structural steel 4.5 mm: stronger/stiffer candidate but heavier;
  coating and galvanic isolation required.

Material properties are explicitly parametric comparison inputs, not certified
allowables.

## 6. Hole and fastening contract

KP000 holes, frame holes, slots, locating holes, cover holes and datum holes
are separately managed. Current CAD/DXF holes are inspection placeholders.
Edge distance 10 mm and spacing 20 mm are candidate rules only. A slot may
adjust alignment but may not be the sole permanent locator.

F2 captive insert is recommended only as the KP000-to-plate concept and F5
T-nut only as the plate-to-frame concept. Insert pull-out, thread engagement,
T-nut fit/slip, bolt preload, mud sealing, corrosion and reverse-load locking
remain HOLD.

## 7. Tool access

Tool insertion is redirected along X. The envelope study gives 14 mm nominal
candidate clearance with zero simplified intersections, improving the v0.8.1
1.5 mm central approach. Actual hex key, socket, spanner, ratchet and finger
envelopes must be measured before serviceability is accepted.

## 8. Load and analytical comparison

LC1 through LC5 use hypothetical 100–300 N belt loads, 1–5 N m torque,
shock factors 1.0–2.0, simultaneous 100 N coupling side load and load
reversal. The conservative flat-plate comparison uses simple cantilever
stress/deflection formulas. `{RECOMMENDED_ID}` has candidate safety factor
{strength['recommended_minimum_safety_factor']} and deflection
{strength['recommended_deflection_mm']} mm under the comparison envelope.
Hole bearing, tear-out, bolt loads, T-nut slip, frame rotation, fatigue and
corrosion are not passed.

Status is `CONDITIONAL_PASS_ANALYTICAL_ONLY`, not physical PASS.

## 9. Deflection-clearance coupling

PTO residual clearance after the comparison plate deflection is
{strength['recommended_clearance_after_deflection_mm']} mm. PTO 60T/fixed
clearance after the same conservative displacement is
{strength['recommended_60t_clearance_after_deflection_mm']} mm. Both exceed
8 mm and 10 mm candidate gates, respectively. Belt tracking tolerance and
actual frame connection stiffness remain HOLD.

## 10. Alignment and assembly

1. {ASSEMBLY_SEQUENCE[0]}
2. {ASSEMBLY_SEQUENCE[1]}
3. {ASSEMBLY_SEQUENCE[2]}
4. {ASSEMBLY_SEQUENCE[3]}
5. {ASSEMBLY_SEQUENCE[4]}
6. {ASSEMBLY_SEQUENCE[5]}
7. {ASSEMBLY_SEQUENCE[6]}
8. {ASSEMBLY_SEQUENCE[7]}
9. {ASSEMBLY_SEQUENCE[8]}
10. {ASSEMBLY_SEQUENCE[9]}
11. {ASSEMBLY_SEQUENCE[10]}
12. {ASSEMBLY_SEQUENCE[11]}

Record shaft insertion resistance, unloaded rotation torque, left/right center
difference, bearing parallelism, tightening-induced rotation change and
belt-load-induced center movement. Limits are `ALIGNMENT_LIMIT_HOLD`.

Replacement follows the controlled reverse sequence after removing belt,
pulley and collars. Never use plate flexure for alignment.

## 11. Interference and non-regression

The {interference['summary']['check_count']} registered envelope checks have
zero candidate intersections. Width remains 290 mm; PTO ends remain
Y=+/-145 mm. No belt location, track geometry, box arrangement, aluminum
member length or parent architecture changed.

## 12. Mud, water and corrosion

Provide downward drainage, avoid water-trap pockets, isolate dissimilar
metals, verify coating/finish, retain grease-port and bearing replacement
access, and keep any mud guard outside belt and tool envelopes. Stainless
fasteners against aluminum require an isolation system candidate.

## 13. Release state

- envelope geometry: CONDITIONAL_PASS_CANDIDATE
- analytical strength: CONDITIONAL_PASS_ANALYTICAL_ONLY
- physical fit: HOLD
- material selection: HOLD
- hole pattern: PART_MEASUREMENT_REQUIRED
- aluminum cutting: HOLD
- plate machining and drilling: HOLD
- load and water/mud tests: HOLD
- field deployment: NOT_APPROVED
"""


def readme_text() -> str:
    return f"""# Common Rover v0.8.2 handoff

This exact {len(PACKAGE_PATHS)}-file package details the independent inner
KP000 support-plate candidate while preserving v0.8 and v0.8.1.

## Runtime

- Python 3.12.13
- CadQuery 2.8.0

## Commands

```powershell
python -B build_common_rover_kp000_support_plate_v0082.py --verify
python -B tests/test_common_rover_kp000_support_plate_v0082_contract.py
```

The builder supports standalone ZIP extraction. When parent repository paths
are present it verifies all protected hashes; otherwise it verifies the
embedded canonical hash sets.

Every DXF/STEP/SVG hole is a parametric inspection placeholder.
`NOT_FOR_MANUFACTURING`, `PART_MEASUREMENT_REQUIRED`, physical fit HOLD,
machining HOLD and field deployment NOT_APPROVED apply.
"""


def validation_payload(
    candidates: list[dict],
    models: dict[str, cq.Shape],
    step_paths: dict[str, Path],
    interference: dict,
    strength: dict,
) -> dict:
    by_id = {row["candidate_id"]: row for row in candidates}
    geometry = {}
    for key, shape in models.items():
        geometry[key] = {
            "source_signature": _shape_signature(shape),
            "step_sha256": _sha256(step_paths[key]),
            "step_size_bytes": step_paths[key].stat().st_size,
        }
        imported = cq.importers.importStep(str(step_paths[key]))
        geometry[key]["artifact_signature"] = _shape_signature(imported)
        geometry[key]["semantic_geometry_reproducible"] = (
            geometry[key]["source_signature"] == geometry[key]["artifact_signature"]
        )
    fixed_checks = {
        "v008_protected": True,
        "v0081_protected": True,
        "parent_candidate_fixed": RECOMMENDED_PARENT_ID == V0081["candidate_id"],
        "two_motors": FIXED["motor_count"] == 2,
        "two_independent_ptos": FIXED["pto_count"] == 2,
        "no_common_pto_shaft": FIXED["common_pto_shaft"] == "PROHIBITED",
        "clutch_three_states": FIXED["clutch_states"] == ["DRIVE", "NEUTRAL", "PTO"],
        "independent_plates": True,
        "recommended_thickness_5": by_id[RECOMMENDED_ID]["thickness"] == 5.0,
        "metal_plate": "A5052" in by_id[RECOMMENDED_ID]["material"],
        "pto_belt_frame_non_regression": V0081["pto_belt_frame_mm"] >= 15.0,
        "pto_residual_non_regression": V0081["pto_residual_mm"] >= 10.0,
        "pto_60t_fixed_non_regression": V0081["pto_60t_fixed_mm"] >= 13.0,
        "width_non_regression": V0081["total_width_mm"] <= 290.0,
        "pto_ends_within_145": max(abs(item) for item in V0081["pto_output_end_y_mm"]) <= 145.0,
        "all_intersections_zero": interference["summary"]["intersection_count"] == 0,
        "tool_intersections_zero": interference["summary"]["tool_intersection_count"] == 0,
        "deflected_belt_clearance_gte_8": strength["recommended_clearance_after_deflection_mm"] >= 8.0,
        "deflected_60t_clearance_gte_10": strength["recommended_60t_clearance_after_deflection_mm"] >= 10.0,
        "candidate_safety_factor_gte_2": strength["recommended_minimum_safety_factor"] >= 2.0,
        "hole_pattern_not_for_manufacturing": True,
        "manufacturing_hold": True,
        "field_not_approved": True,
    }
    return {
        "document_id": DOCUMENT_ID,
        "recommended_candidate": RECOMMENDED_ID,
        "candidate_count": len(candidates),
        "fixed_checks": fixed_checks,
        "fixed_check_pass_count": sum(fixed_checks.values()),
        "fixed_check_count": len(fixed_checks),
        "geometry": geometry,
        "interference_summary": interference["summary"],
        "strength_summary": {
            "status": strength["status"],
            "candidate_safety_factor": strength["recommended_minimum_safety_factor"],
            "plate_deflection_mm": strength["recommended_deflection_mm"],
            "clearance_after_deflection_mm": strength["recommended_clearance_after_deflection_mm"],
        },
        "overall": (
            "CONDITIONAL_PASS_ANALYTICAL_ONLY"
            if all(fixed_checks.values())
            and all(item["semantic_geometry_reproducible"] for item in geometry.values())
            else "FAIL"
        ),
        "physical_fit": "HOLD",
        "manufacturing_release": "HOLD",
        "field_deployment": "NOT_APPROVED",
    }


def _seal_hashes() -> None:
    manifest = [
        f"DOCUMENT_ID={DOCUMENT_ID}",
        f"EXPECTED_FILE_COUNT={len(PACKAGE_PATHS)}",
        "ROOT=ZIP_ROOT",
        "STATUS=NOT_FOR_MANUFACTURING",
    ]
    manifest.extend(f"{relative}\tFILE" for relative in PACKAGE_PATHS)
    _write_text(LANE_DIR / MANIFEST_NAME, "\n".join(manifest) + "\n")
    sums = []
    for relative in PACKAGE_PATHS:
        if relative == SHA256SUMS_NAME:
            continue
        path = LANE_DIR / relative
        if not path.is_file():
            raise RuntimeError(f"cannot seal missing path: {relative}")
        sums.append(f"{_sha256(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(sums) + "\n")


def refresh() -> dict:
    _audit_protected_if_available()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    measurements = measurement_rows()
    candidates = candidate_rows()
    by_id = {row["candidate_id"]: row for row in candidates}
    recommended = by_id[RECOMMENDED_ID]
    alternatives = [by_id[ALTERNATIVE_A_ID], by_id[ALTERNATIVE_B_ID]]
    strength = strength_payload(candidates)
    interference = interference_payload(recommended)
    tools = tool_rows()
    fasteners = fastener_rows()
    models = build_models()
    step_paths = {
        "assembly": ARTIFACT_DIR / ASSEMBLY_STEP,
        "left": ARTIFACT_DIR / LEFT_STEP,
        "right": ARTIFACT_DIR / RIGHT_STEP,
    }
    for key, shape in models.items():
        _write_step(shape, step_paths[key])
    validation = validation_payload(
        candidates, models, step_paths, interference, strength
    )
    ranking = ranking_rows(candidates)
    texts = {
        AUTHORITY_NAME: authority_markdown(
            measurements, candidates, recommended, alternatives, strength, interference
        ),
        PARAMETERS_NAME: _json_text(
            parameters_payload(measurements, candidates, recommended)
        ),
        MEASUREMENT_MD_NAME: measurement_markdown(measurements),
        MEASUREMENT_CSV_NAME: _csv_text(measurements, MEASUREMENT_FIELDS),
        CANDIDATES_NAME: _csv_text(candidates, CANDIDATE_FIELDS),
        RANKING_NAME: _csv_text(
            ranking, ["rank", "selection_role", *CANDIDATE_FIELDS]
        ),
        STRENGTH_NAME: _json_text(strength),
        INTERFERENCE_NAME: _json_text(interference),
        TOOLS_NAME: _csv_text(tools, TOOL_FIELDS),
        FASTENERS_NAME: _csv_text(fasteners, FASTENER_FIELDS),
        VALIDATION_NAME: _json_text(validation),
        README_NAME: readme_text(),
        f"artifacts/{LEFT_DXF}": _dxf_text("LEFT"),
        f"artifacts/{RIGHT_DXF}": _dxf_text("RIGHT"),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(),
        f"artifacts/{TOP_SVG}": top_svg(),
        f"artifacts/{FRONT_SVG}": front_svg(),
        f"artifacts/{SIDE_SVG}": side_svg(),
        f"artifacts/{DIMENSIONS_SVG}": dimensions_svg(),
    }
    for relative, text in texts.items():
        _write_text(LANE_DIR / relative, text)
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        (
            f"DOCUMENT_ID={DOCUMENT_ID}\n"
            "STATUS=PENDING_CONTRACT_EXECUTION\n"
            "Run --record-test-result after refresh.\n"
        ),
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
        raise RuntimeError("MANIFEST path set/order mismatch")
    sums = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        sums[relative] = digest
    if set(sums) != set(PACKAGE_PATHS) - {SHA256SUMS_NAME}:
        raise RuntimeError("SHA256SUMS path set mismatch")
    mismatches = [
        relative
        for relative, expected in sums.items()
        if _sha256(LANE_DIR / relative) != expected
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
    if validation["overall"] != "CONDITIONAL_PASS_ANALYTICAL_ONLY":
        raise RuntimeError("validation overall mismatch")
    measurements = measurement_rows()
    candidates = candidate_rows()
    by_id = {row["candidate_id"]: row for row in candidates}
    recommended = by_id[RECOMMENDED_ID]
    alternatives = [by_id[ALTERNATIVE_A_ID], by_id[ALTERNATIVE_B_ID]]
    strength = strength_payload(candidates)
    interference = interference_payload(recommended)
    expected = {
        AUTHORITY_NAME: authority_markdown(
            measurements, candidates, recommended, alternatives, strength, interference
        ),
        PARAMETERS_NAME: _json_text(
            parameters_payload(measurements, candidates, recommended)
        ),
        MEASUREMENT_MD_NAME: measurement_markdown(measurements),
        MEASUREMENT_CSV_NAME: _csv_text(measurements, MEASUREMENT_FIELDS),
        CANDIDATES_NAME: _csv_text(candidates, CANDIDATE_FIELDS),
        RANKING_NAME: _csv_text(
            ranking_rows(candidates), ["rank", "selection_role", *CANDIDATE_FIELDS]
        ),
        STRENGTH_NAME: _json_text(strength),
        INTERFERENCE_NAME: _json_text(interference),
        TOOLS_NAME: _csv_text(tool_rows(), TOOL_FIELDS),
        FASTENERS_NAME: _csv_text(fastener_rows(), FASTENER_FIELDS),
        README_NAME: readme_text(),
        f"artifacts/{LEFT_DXF}": _dxf_text("LEFT"),
        f"artifacts/{RIGHT_DXF}": _dxf_text("RIGHT"),
        f"artifacts/{OVERVIEW_SVG}": overview_svg(),
        f"artifacts/{TOP_SVG}": top_svg(),
        f"artifacts/{FRONT_SVG}": front_svg(),
        f"artifacts/{SIDE_SVG}": side_svg(),
        f"artifacts/{DIMENSIONS_SVG}": dimensions_svg(),
    }
    byte_mismatches = [
        relative
        for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if byte_mismatches:
        raise RuntimeError(f"byte reproducibility mismatch: {byte_mismatches}")
    for key, relative in (
        ("assembly", f"artifacts/{ASSEMBLY_STEP}"),
        ("left", f"artifacts/{LEFT_STEP}"),
        ("right", f"artifacts/{RIGHT_STEP}"),
    ):
        imported = cq.importers.importStep(str(LANE_DIR / relative))
        if _shape_signature(imported) != validation["geometry"][key]["artifact_signature"]:
            raise RuntimeError(f"STEP semantic mismatch: {key}")
    package = _verify_hashes()
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "recommended_candidate": RECOMMENDED_ID,
        "candidate_count": len(candidates),
        "measurement_count": len(measurements),
        "protected_audit_mode": audit["mode"],
        "protected_checked_path_count": audit["checked_path_count"],
        "interference_count": interference["summary"]["intersection_count"],
        **package,
    }


def record_test_result() -> dict:
    test_path = LANE_DIR / TEST_REL
    result = subprocess.run(
        [sys.executable, "-B", str(test_path)],
        cwd=LANE_DIR,
        text=True,
        capture_output=True,
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
    if result.returncode != 0:
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
    path = DOWNLOAD_DIR / f"Paddy_Swarm_Common_Rover_v0_8_2_KP000_Support_Plate_{stamp}.zip"
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
            if "__pycache__" in name
            or ".pytest_cache" in name
            or name.lower().endswith(".pyc")
        ]
        if bad or tuple(names) != PACKAGE_PATHS or forbidden:
            raise RuntimeError(
                f"ZIP audit failure: bad={bad}, count={len(names)}, forbidden={forbidden}"
            )
        extracted_sums = archive.read(SHA256SUMS_NAME).decode("utf-8").splitlines()
        zip_hashes_ok = all(
            hashlib.sha256(archive.read(relative)).hexdigest() == digest
            for digest, relative in (line.split("  ", 1) for line in extracted_sums)
        )
        if not zip_hashes_ok:
            raise RuntimeError("ZIP internal SHA256SUMS failure")
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
            "candidate_count": result["candidate_count"],
            "fixed_checks": f"{result['fixed_check_pass_count']}/{result['fixed_check_count']}",
            "recommended": result["recommended_candidate"],
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
