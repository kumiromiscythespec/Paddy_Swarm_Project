from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


BASE_HEAD = "242737507c1f94811ff309b36905525057761c45"
EXPECTED_TRACKED_STL_COUNT = 181
EXPECTED_TRACKED_STEP_STP_COUNT = 109
LANE_RELATIVE = Path(
    "cad/common_rover/"
    "v2_29_3_9_1_production_intent_input_audit_v0_1"
)
PROFILE_AUTHORITY = Path(
    "rovers/common_rover/v2.29.3.9.1/tslot_profile_authority.json"
)
FRAME_AUTHORITY = Path(
    "rovers/common_rover/v2.29.3.9.1/body_frame_authority.json"
)
WIDTH_AUTHORITY = Path(
    "rovers/common_rover/v2.29.3.9.1/operational_width_contract.json"
)
DUMMY_LANE = Path(
    "cad/common_rover/v2_29_3_9_1_progressive_full_scale_dummy_v0_1"
)
INTERFACE_LANE = Path(
    "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1"
)

REQUIRED_EXTERNAL_ARTIFACTS = (
    "production_input_audit.json",
    "real_profile_input_audit.json",
    "cbox_structural_input_audit.json",
    "bbox_structural_input_audit.json",
    "fastener_input_audit.json",
    "printed_part_manufacturing_input_audit.json",
    "float_production_width_audit.json",
    "ai10_production_input_audit.json",
    "production_part_number_proposal.md",
    "unresolved_production_inputs.md",
    "production_readiness_matrix.csv",
    "required_measurements_checklist.csv",
    "required_purchase_specifications.csv",
    "next_cad_lane_recommendation.md",
    "baseline_tracked_cad_inventory.json",
    "baseline_tracked_cad_inventory.csv",
    "baseline_tracked_cad_inventory.sha256",
    "baseline_cad_output_diff_report.json",
    "untracked_cad_output_scan.json",
    "repository_bytecode_audit.json",
)

DUMMY_DECLARATIONS = {
    "referenced_existing_dummy_stl_count": 33,
    "declaration_source": (
        "cad/common_rover/"
        "v2_29_3_9_1_progressive_full_scale_dummy_v0_1/"
        "final_gate_contract.py"
    ),
    "manufacturing_part": False,
    "real_rover_part": False,
    "structural_part": False,
    "actual_aluminum_profile_compatible": False,
    "geometry_reuse_automatically_approved": False,
    "production_part_number_reuse": "PROHIBITED",
    "remove_dummy_only_marking_to_promote": "PROHIBITED",
    "classification": (
        "DUMMY ONLY / NO LOAD / NOT STRUCTURAL / PROFILE-3 ONLY"
    ),
    "existing_dummy_source_modified": False,
}

PROFILE_REQUIRED_FIELDS = (
    "planned_manufacturer",
    "product_part_number",
    "nominal_outer_dimensions",
    "measured_outer_dimensions",
    "slot_opening_width",
    "slot_depth",
    "internal_cavity",
    "center_bore",
    "corner_radius",
    "extrusion_tolerance",
    "compatible_t_nut",
    "compatible_corner_bracket",
    "compatible_bolt_size",
    "surface_treatment",
    "mass_per_meter",
)

PRINTED_MANUFACTURING_FIELDS = (
    "material",
    "nozzle_diameter",
    "layer_height",
    "wall_count",
    "top_bottom_layers",
    "infill",
    "print_orientation",
    "support_policy",
    "dimensional_clearance",
    "shrinkage_allowance",
    "hole_compensation",
    "heat_set_insert_use",
    "metal_washer_requirement",
    "minimum_wall_thickness",
    "minimum_fillet",
    "layer_load_direction",
    "replaceable_wear_surface",
    "uv_exposure",
    "water_mud_exposure",
    "expected_service_temperature",
    "inspection_dimensions",
    "rejection_criteria",
)


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for path in (candidate, *candidate.parents):
        if (path / ".git").exists():
            return path
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


def _load_json(root: Path, relative: Path) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def field(
    name: str,
    classification: str,
    value: Any,
    *,
    unit: str | None = None,
    source: str,
    evidence: str,
    closure_action: str | None = None,
) -> dict[str, Any]:
    return {
        "field": name,
        "classification": classification,
        "value": value,
        "unit": unit,
        "source": source,
        "evidence": evidence,
        "closure_action": closure_action,
    }


def merge_profile_supplier_inputs(
    repository_values: dict[str, Any],
    supplied_values: dict[str, Any] | None = None,
    *,
    generic_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge explicit supplier inputs while rejecting inferred generic values."""
    if generic_defaults:
        raise ValueError("GENERIC_PROFILE_VALUE_INFERENCE_FORBIDDEN")
    result = deepcopy(repository_values)
    for key, value in (supplied_values or {}).items():
        if key not in PROFILE_REQUIRED_FIELDS:
            raise ValueError(f"UNKNOWN_PROFILE_INPUT:{key}")
        if value in (None, "", "UNKNOWN", "UNSELECTED"):
            raise ValueError(f"PROFILE_INPUT_NOT_EXPLICIT:{key}")
        result[key] = value
    return result


def build_real_profile_audit(root: Path) -> dict[str, Any]:
    profile = _load_json(root, PROFILE_AUTHORITY)
    frame = _load_json(root, FRAME_AUTHORITY)
    profile_source = PROFILE_AUTHORITY.as_posix()
    frame_source = FRAME_AUTHORITY.as_posix()
    nominal = [
        frame["section_mm"]["X_or_Y"],
        frame["section_mm"]["Z"],
    ]
    records = [
        field(
            "planned_manufacturer",
            "MISSING",
            None,
            source=profile_source,
            evidence=f'vendor={profile.get("vendor", "NOT_FOUND")}',
            closure_action="Select and record the extrusion manufacturer.",
        ),
        field(
            "product_part_number",
            "MISSING",
            None,
            source=profile_source,
            evidence="No supplier product part number is present.",
            closure_action="Record the manufacturer catalogue part number.",
        ),
        field(
            "nominal_outer_dimensions",
            "CONFIRMED_ENVELOPE_ONLY",
            nominal,
            unit="mm",
            source=frame_source,
            evidence=(
                f'profile_class={frame["profile_class"]}; section_mm='
                f'{frame["section_mm"]}'
            ),
            closure_action=(
                "Do not treat nominal envelope dimensions as measured supplier "
                "cross-section geometry."
            ),
        ),
    ]
    missing_measurements = {
        "measured_outer_dimensions": (
            "Measure X and Z across multiple cut samples."
        ),
        "slot_opening_width": "Measure every mating slot opening.",
        "slot_depth": "Measure slot depth on the selected supplier profile.",
        "internal_cavity": (
            "Obtain a controlled section drawing or measure the cut section."
        ),
        "center_bore": "Measure center bore diameter and form.",
        "corner_radius": "Measure external corner radius.",
        "extrusion_tolerance": (
            "Obtain supplier tolerance or establish an incoming-inspection range."
        ),
    }
    for name, action in missing_measurements.items():
        records.append(
            field(
                name,
                "MEASUREMENT_REQUIRED",
                None,
                unit="mm",
                source=profile_source,
                evidence=(
                    "Supplier-specific cross-section value is absent; "
                    "generic 20x20 values are forbidden."
                ),
                closure_action=action,
            )
        )
    purchase_missing = {
        "compatible_t_nut": (
            "Select and fit-check the supplier-specific T-nut."
        ),
        "compatible_corner_bracket": (
            "Select and load-justify a compatible metal corner bracket."
        ),
        "compatible_bolt_size": (
            "Confirm thread and engagement after the T-nut is selected."
        ),
        "surface_treatment": "Record alloy finish and surface treatment.",
        "mass_per_meter": "Record the supplier-controlled mass per metre.",
    }
    for name, action in purchase_missing.items():
        records.append(
            field(
                name,
                "MISSING",
                None,
                unit="kg/m" if name == "mass_per_meter" else None,
                source=profile_source,
                evidence="No selected supplier specification is present.",
                closure_action=action,
            )
        )
    return {
        "schema": "PS_REAL_PROFILE_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "profile_class": profile["profile_class"],
        "supplier_selected": False,
        "generic_20x20_value_inference_allowed": False,
        "records": records,
        "missing_fields": [
            item["field"]
            for item in records
            if item["classification"] in {"MISSING", "MEASUREMENT_REQUIRED"}
        ],
        "production_stl_gate": "HOLD",
    }


def build_cbox_structural_audit() -> dict[str, Any]:
    source = (
        DUMMY_LANE / "physical_connection_model.py"
    ).as_posix()
    requirements = {
        "actual_mounting_face": (
            "MISSING",
            None,
            "Dummy keyed-corner seats do not establish the real mounting face.",
            "Measure and define the real CBOX mounting datum and face.",
        ),
        "load_direction": (
            "MISSING",
            None,
            "No production load vector or duty cycle is established.",
            "Provide gravity, inertial, shock, and torque load vectors.",
        ),
        "center_of_gravity": (
            "MISSING",
            None,
            "No measured loaded CBOX mass properties are present.",
            "Measure loaded mass and COG in the rover coordinate system.",
        ),
        "saddle_contact_area": (
            "MISSING",
            None,
            "Dummy cage-corner clearance is not a structural contact patch.",
            "Define allowable faces, contact area, pressure, and pad material.",
        ),
        "clamp_position": (
            "MISSING",
            None,
            "The temporary visible dummy strap is not a production clamp.",
            "Define clamp locations, reaction loads, and access.",
        ),
        "removal_direction": (
            "CANDIDATE_DUMMY_ONLY",
            "+Z",
            "The dummy is lifted +Z after its temporary strap is removed.",
            "Verify the real loaded box extraction path and service clearance.",
        ),
        "cable_clearance": (
            "MISSING",
            None,
            "No production connector, bend-radius, or harness sweep is defined.",
            "Provide connector envelopes, bend radii, and service loops.",
        ),
        "water_drainage": (
            "MISSING",
            None,
            "No production saddle drainage geometry is established.",
            "Define drainage paths and a mud-cleaning inspection method.",
        ),
        "motor_pto_interference": (
            "MISSING",
            None,
            "Reserved zones exist, but real CBOX/clamp interference is unverified.",
            "Measure the operational motor/PTO sweep and clearance.",
        ),
    }
    records = [
        field(
            name,
            classification,
            value,
            source=source,
            evidence=evidence,
            closure_action=closure,
        )
        for name, (classification, value, evidence, closure) in requirements.items()
    ]
    return {
        "schema": "PS_CBOX_STRUCTURAL_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "dummy_geometry_structural_evidence": False,
        "records": records,
        "production_stl_gate": "HOLD",
    }


def build_bbox_structural_audit() -> dict[str, Any]:
    dummy_source = (
        DUMMY_LANE / "authority_adapter.py"
    ).as_posix()
    interface_source = (
        INTERFACE_LANE / "interface_model.py"
    ).as_posix()
    records = [
        field(
            "independent_structural_support",
            "REQUIREMENT_CONFIRMED_INPUT_MISSING",
            True,
            source=interface_source,
            evidence=(
                "BBOX must use an independent load path; current representation "
                "is visual dummy only."
            ),
            closure_action=(
                "Design and substantiate a metal load path independent of CBOX."
            ),
        ),
        field(
            "rear_frame_hardpoint",
            "MISSING",
            None,
            source=dummy_source,
            evidence="rear_bridge_hardpoints is explicitly unresolved.",
            closure_action="Measure and approve rear frame hardpoint locations.",
        ),
        field(
            "frame_section",
            "MISSING",
            None,
            source=dummy_source,
            evidence="cradle_section is explicitly unresolved.",
            closure_action="Select section, alloy, wall thickness, and finish.",
        ),
        field(
            "longitudinal_tie",
            "MISSING",
            None,
            source=dummy_source,
            evidence="frame_tie geometry and load capability are unresolved.",
            closure_action="Define longitudinal tie geometry and load cases.",
        ),
        field(
            "lateral_tie",
            "MISSING",
            None,
            source=dummy_source,
            evidence="No production lateral tie is established.",
            closure_action="Define lateral load restraint and hardpoints.",
        ),
        field(
            "clamp_method",
            "MISSING",
            None,
            source=dummy_source,
            evidence="clamp_geometry is explicitly unresolved.",
            closure_action="Select a metal clamp and calculate engagement.",
        ),
        field(
            "battery_load",
            "MISSING",
            None,
            source=interface_source,
            evidence="Battery envelope exists; loaded mass and dynamic loads do not.",
            closure_action="Measure battery/cassette mass, COG, shock, and restraint load.",
        ),
        field(
            "lift_removal_direction",
            "CANDIDATE_DUMMY_ONLY",
            "+Z",
            source=(
                DUMMY_LANE / "physical_connection_model.py"
            ).as_posix(),
            evidence="Dummy BBOX is lifted +Z after a temporary strap is removed.",
            closure_action="Verify production lifting clearance and human factors.",
        ),
        field(
            "implement_clearance",
            "MISSING",
            None,
            source=dummy_source,
            evidence="implement_clearance is explicitly unresolved.",
            closure_action="Measure the full implement motion envelope.",
        ),
        field(
            "mud_water_drainage",
            "MISSING",
            None,
            source=interface_source,
            evidence="Open drainage is a concept requirement, not production geometry.",
            closure_action="Define drainage, cleanout access, and rejection criteria.",
        ),
    ]
    return {
        "schema": "PS_BBOX_STRUCTURAL_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "bbox_cantilevered_from_cbox_allowed": False,
        "current_independent_support_is_structural": False,
        "records": records,
        "production_stl_gate": "HOLD",
    }


def build_fastener_audit() -> dict[str, Any]:
    source = (DUMMY_LANE / "assembly_bom.py").as_posix()
    candidate = "CANDIDATE_NOT_APPROVED"
    missing = "MISSING"
    specifications = {
        "bolt_diameter": (
            candidate,
            "M5",
            "M5 metal bolts are a structural candidate.",
            "Confirm against the selected profile/T-nut and joint analysis.",
        ),
        "bolt_length": (
            missing,
            None,
            "No grip stack or selected bolt length is present.",
            "Calculate each joint stack and available engagement.",
        ),
        "thread_pitch": (
            missing,
            None,
            "M5 candidate does not establish thread pitch.",
            "Record the purchased bolt and nut thread pitch.",
        ),
        "strength_class": (
            missing,
            None,
            "No strength class is approved.",
            "Select class from calculated load and environmental requirements.",
        ),
        "material": (
            missing,
            None,
            "No production fastener material is approved.",
            "Select material with galvanic/corrosion review.",
        ),
        "washer": (
            candidate,
            "M5 metal washer candidate",
            "OD, thickness, material, and corrosion remain unresolved.",
            "Select washer standard, size, material, and finish.",
        ),
        "nut_t_nut": (
            candidate,
            "Compatible T-nut for selected 20x20 profile",
            "Profile and supplier-specific compatibility are unresolved.",
            "Select and fit-test the exact T-nut SKU.",
        ),
        "removable_pin_diameter": (
            candidate,
            "6 mm-class",
            "Actual diameter, tolerance, grip, and material are unresolved.",
            "Select pin SKU and measure mating stack.",
        ),
        "r_pin_size": (
            candidate,
            "Compatible R-pin candidate",
            "Cross-hole and R-pin dimensions are unresolved.",
            "Select paired removable pin and R-pin specifications.",
        ),
        "thread_engagement": (
            missing,
            None,
            "No selected T-nut or joint stack exists.",
            "Calculate minimum/maximum engagement for every joint.",
        ),
        "tightening_torque": (
            missing,
            None,
            "No torque specification is approved.",
            "Set torque after material, finish, and locking method selection.",
        ),
        "anti_loosening_method": (
            missing,
            None,
            "No production vibration-retention method is approved.",
            "Select and validate locking method for field service.",
        ),
        "corrosion_protection": (
            missing,
            None,
            "No paddy-field corrosion system is approved.",
            "Specify coating/material and galvanic isolation.",
        ),
    }
    records = [
        field(
            name,
            classification,
            value,
            source=source,
            evidence=evidence,
            closure_action=closure,
        )
        for name, (classification, value, evidence, closure) in specifications.items()
    ]
    return {
        "schema": "PS_FASTENER_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "candidate_values_are_hole_geometry_authority": False,
        "purchase_status": "NOT_APPROVED",
        "records": records,
        "production_stl_gate": "HOLD",
    }


def build_printed_part_audit() -> dict[str, Any]:
    source = "docs/3d_print_pack_README.md"
    categories = (
        (
            "positioning_saddles_and_guides",
            "Printed geometry may position parts but is not an approved load path.",
        ),
        (
            "secondary_retention_and_covers",
            "Printed retention is secondary only; primary metal retention is required.",
        ),
        (
            "replaceable_wear_and_sacrificial_parts",
            "Wear surface definition and replacement criteria remain unresolved.",
        ),
        (
            "structural_or_primary_retention_parts",
            "PROHIBITED until a separately approved structural process exists.",
        ),
    )
    records = []
    for category, boundary in categories:
        inputs = []
        for name in PRINTED_MANUFACTURING_FIELDS:
            if name == "material":
                classification = "CANDIDATE_NOT_APPROVED"
                value = "PETG/ASA"
                evidence = (
                    "Repository workflow suggests PETG/ASA after fit revision; "
                    "this is not manufacturing approval."
                )
            elif (
                category == "structural_or_primary_retention_parts"
                and name == "layer_load_direction"
            ):
                classification = "NOT_APPLICABLE_PROHIBITED_CATEGORY"
                value = None
                evidence = boundary
            else:
                classification = "MISSING"
                value = None
                evidence = "No category-specific production value is approved."
            inputs.append(
                field(
                    name,
                    classification,
                    value,
                    source=source,
                    evidence=evidence,
                    closure_action=(
                        "Establish by controlled print process, measurement, and "
                        "acceptance testing before release."
                    ),
                )
            )
        records.append(
            {
                "category": category,
                "functional_boundary": boundary,
                "status": "INCOMPLETE",
                "inputs": inputs,
            }
        )
    return {
        "schema": "PS_PRINTED_PART_MANUFACTURING_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "petg_assumption_is_manufacturing_approval": False,
        "target_printer_reference": "Bambu Lab A1 (coupon context only)",
        "categories": records,
        "production_stl_gate": "HOLD",
    }


def build_float_width_audit(root: Path) -> dict[str, Any]:
    frame = _load_json(root, FRAME_AUTHORITY)
    width = _load_json(root, WIDTH_AUTHORITY)
    missing_terms = (
        "actual_float_outboard_projection_each_side_mm",
        "actual_bracket_outboard_offset_each_side_mm",
        "assembled_part_tolerance_each_side_mm",
        "operational_inclination_allowance_each_side_mm",
        "mud_clearance_each_side_mm",
    )
    return {
        "schema": "PS_FLOAT_PRODUCTION_WIDTH_AUDIT_V0_1",
        "status": "HOLD",
        "known_authority": {
            "bare_frame_width_mm": frame["bare_frame_union"]["width_mm"],
            "registered_interface_maximum_mm": width["candidate_target_max_mm"],
            "operational_hard_limit_mm": width["hard_limit_mm"],
            "registered_maximum_is_automatic_approval": False,
        },
        "assembled_maximum_formula": (
            "bare_frame_width_mm + left(actual float projection + bracket "
            "offset + tolerance + inclination + mud clearance) + "
            "right(actual float projection + bracket offset + tolerance + "
            "inclination + mud clearance)"
        ),
        "assembled_maximum_width_mm": None,
        "calculation_complete": False,
        "missing_inputs": list(missing_terms),
        "candidate_dummy_width_values_used": False,
        "registered_286_mm_exceedance_automatically_approved": False,
        "production_stl_gate": "HOLD",
    }


def build_ai10_audit() -> dict[str, Any]:
    source = (DUMMY_LANE / "physical_connection_model.py").as_posix()
    records = [
        field(
            "drive_pulley",
            "CANDIDATE_NOT_APPROVED",
            "Drive 20T dual-row pulley",
            source=source,
            evidence="Recorded as AI-10 candidate only.",
            closure_action="Select pulley profile, SKU, bore, keying, and material.",
        ),
        field(
            "pto_pulley",
            "CANDIDATE_NOT_APPROVED",
            "PTO 20T dual-row pulley",
            source=source,
            evidence="Recorded as AI-10 candidate only.",
            closure_action="Select pulley profile, SKU, bore, keying, and material.",
        ),
        field(
            "sync_ratio",
            "CANDIDATE_NOT_APPROVED",
            "20T:20T / 1:1",
            source=source,
            evidence="Recorded as sync-belt candidate only.",
            closure_action="Approve ratio after speed, torque, and safety analysis.",
        ),
        field(
            "pto_downstream_ratio",
            "CANDIDATE_NOT_APPROVED",
            "20T:60T",
            source=source,
            evidence="Recorded as downstream candidate only.",
            closure_action="Approve after spreader duty-cycle analysis.",
        ),
    ]
    missing = {
        "shaft_usable_length": "Measure usable shaft length and retention features.",
        "pulley_row_spacing": "Measure pulley rows, belt tracking, and axial tolerance.",
        "bearing_overhang": "Calculate bearing reactions and allowable overhang.",
        "belt_width": "Select belt standard and width from transmitted load.",
        "guard_clearance": "Define full guard envelope and service access.",
        "300_mm_width_interference": "Check the complete operational envelope.",
    }
    for name, closure in missing.items():
        records.append(
            field(
                name,
                "MEASUREMENT_OR_ENGINEERING_REQUIRED",
                None,
                unit="mm",
                source=source,
                evidence="AI-10 clearance is NOT_YET_AUDITED.",
                closure_action=closure,
            )
        )
    requirements = {
        "independent_pto_neutral_interlock": (
            "REQUIRED_NOT_DESIGNED",
            True,
            "Explicit safety requirement; implementation is absent.",
        ),
        "application_boundary": (
            "REQUIREMENT_CONFIRMED",
            "LOW-LOAD SPREADER ONLY",
            "Explicit AI-10 load-class boundary.",
        ),
        "torque_fuse": (
            "REQUIRED_NOT_SPECIFIED",
            True,
            "Required by production audit task; no specification is present.",
        ),
        "normally_closed_material_gate": (
            "REQUIRED_NOT_DESIGNED",
            True,
            "Required by production audit task; no implementation is present.",
        ),
    }
    for name, (classification, value, evidence) in requirements.items():
        records.append(
            field(
                name,
                classification,
                value,
                source=source,
                evidence=evidence,
                closure_action="Design, verify failure state, and approve before release.",
            )
        )
    return {
        "schema": "PS_AI10_PRODUCTION_INPUT_AUDIT_V0_1",
        "status": "INCOMPLETE",
        "manufacturing_geometry_created": False,
        "current_dummy_guarantees_axial_space": False,
        "records": records,
        "production_stl_gate": "HOLD",
    }


def validate_production_part_number(
    candidate: str,
    *,
    dummy_part_numbers: set[str],
) -> None:
    if candidate in dummy_part_numbers:
        raise ValueError("DUMMY_PART_NUMBER_PRODUCTION_REUSE_FORBIDDEN")
    if "DUMMY" in candidate.upper():
        raise ValueError("DUMMY_IDENTIFIER_NOT_A_PRODUCTION_PART_NUMBER")


def build_overall_audit(
    *,
    profile: dict[str, Any],
    cbox: dict[str, Any],
    bbox: dict[str, Any],
    fastener: dict[str, Any],
    printed: dict[str, Any],
    float_width: dict[str, Any],
    ai10: dict[str, Any],
) -> dict[str, Any]:
    statuses = {
        "REAL_PROFILE_INPUT_STATUS": profile["status"],
        "CBOX_STRUCTURAL_INPUT_STATUS": cbox["status"],
        "BBOX_STRUCTURAL_INPUT_STATUS": bbox["status"],
        "FASTENER_INPUT_STATUS": fastener["status"],
        "PRINTED_PART_INPUT_STATUS": printed["status"],
        "FLOAT_PRODUCTION_WIDTH_STATUS": float_width["status"],
        "AI10_PRODUCTION_INPUT_STATUS": ai10["status"],
        "PRODUCTION_PART_NUMBER_STATUS": "HOLD",
    }
    return {
        "schema": "PS_PRODUCTION_INTENT_INPUT_AUDIT_V0_1",
        "base_head": BASE_HEAD,
        "audit_status": "PASS_WITH_HOLD",
        "domain_statuses": statuses,
        "dummy_declarations": DUMMY_DECLARATIONS,
        "completion_gate": {
            "all_required_inputs_complete": False,
            "production_stl_generation": "HOLD",
            "dummy_stl_print": "NOT_SELECTED",
            "manufacturing_status": "NOT_APPROVED",
            "purchase_status": "NOT_APPROVED",
            "field_deployment_status": "NOT_APPROVED",
        },
        "prohibitions": [
            "NO_GENERIC_PROFILE_DIMENSION_INFERENCE",
            "NO_UNCONFIRMED_FASTENER_VALUE_TO_HOLE_GEOMETRY",
            "NO_DUMMY_PART_NUMBER_PRODUCTION_REUSE",
            "NO_DUMMY_MARKING_REMOVAL_AS_PRODUCTION_PROMOTION",
            "NO_PRODUCTION_STL_STEP_STP_GENERATION_IN_THIS_AUDIT",
        ],
    }
