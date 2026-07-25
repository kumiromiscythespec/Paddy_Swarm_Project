from __future__ import annotations

from pathlib import Path


SOURCE_BASE_HEAD = "e6ba477e7f0e14674d4266b0bc91cd86cd6ec8b8"
CAD_BASE_HEAD = "242737507c1f94811ff309b36905525057761c45"
CANONICAL_INVENTORY_ALGORITHM = (
    "SHA256_OF_UTF8_BYTEWISE_SORTED_POSIX_PATH_RECORDS_V1"
)
CANONICAL_INVENTORY_SHA256 = (
    "741f6a2be192db200ba55e5388ca14d09020ff6f4f9de844f2353bd5ef382ad9"
)
EXPECTED_TRACKED_STL_COUNT = 181
EXPECTED_TRACKED_STEP_STP_COUNT = 109

LANE_RELATIVE = Path(
    "cad/common_rover/"
    "v2_29_3_9_1_real_profile_input_registration_v0_1"
)
AUDIT_LANE_RELATIVE = Path(
    "cad/common_rover/"
    "v2_29_3_9_1_production_intent_input_audit_v0_1"
)

PURCHASE_EVIDENCE_CLASSIFICATION = "USER_SUPPLIED_ORDER_EVIDENCE"
CONFIRMED_CLASSIFICATION = "CONFIRMED_BY_USER_ORDER_EVIDENCE"
DESIGN_AUTHORITY_STATUS = "NOT_ESTABLISHED"

REQUIRED_PROFILE_FIELDS = (
    "profile_id",
    "manufacturer",
    "ordered_product_name",
    "ordered_part_number",
    "base_profile_identifier_candidate",
    "nominal_outer_section_mm",
    "ordered_length_mm",
    "ordered_quantity",
    "listing_slot_description",
    "listed_finish_or_color",
    "purchase_evidence_source",
    "purchase_evidence_classification",
    "design_authority_status",
    "arrival_status",
    "measurement_status",
    "intended_role_status",
    "fit_validation_status",
    "production_geometry_gate",
)

UNCONFIRMED_PRODUCTION_FIELDS = (
    "measured_outer_dimensions",
    "actual_slot_opening_width",
    "actual_slot_depth",
    "internal_cavity_dimensions",
    "center_bore",
    "external_corner_radius",
    "extrusion_tolerance",
    "straightness",
    "twist",
    "actual_mass_per_metre",
    "compatible_t_nut_model",
    "compatible_bracket_model",
    "compatible_bolt_length",
    "tightening_torque",
    "corrosion_suitability_in_paddy_field",
    "structural_role",
    "load_capacity_for_rover",
    "printed_part_fit_clearance",
)

SUPPLIER_DOCUMENT_REQUIREMENTS = (
    "MISUMI official product page",
    "downloadable CAD or controlled drawing",
    "section drawing revision",
    "tolerance specification",
    "material specification",
    "surface treatment specification",
    "compatible accessory list",
    "T-nut part number",
    "corner bracket part number",
    "bolt specification",
)

EXTERNAL_ARTIFACT_NAMES = (
    "supplier_profile_registry.json",
    "supplier_profile_registration_audit.json",
    "profile_role_candidate_matrix.csv",
    "incoming_profile_inspection_template.csv",
    "incoming_profile_inspection_instructions.md",
    "required_supplier_documents.csv",
    "unresolved_profile_inputs.md",
    "production_audit_profile_update.json",
    "baseline_cad_output_diff_report.json",
    "untracked_cad_output_scan.json",
    "repository_bytecode_audit.json",
    "unit_test_results.json",
    "unit_test_results.txt",
)

PROHIBITED_REPOSITORY_SUFFIXES = {
    ".stl",
    ".step",
    ".stp",
    ".svg",
    ".zip",
    ".pyc",
    ".pyo",
}


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for path in (candidate, *candidate.parents):
        if (path / ".git").exists():
            return path
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


def ensure_external_output(
    path: Path,
    repository: Path,
    *,
    allowed_names: set[str] | None = None,
) -> None:
    resolved = path.resolve()
    root = repository.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("PROFILE_ARTIFACT_MUST_BE_OUTSIDE_REPOSITORY")
    if (
        allowed_names is not None
        and resolved.name not in allowed_names
    ):
        raise ValueError(f"UNAPPROVED_PROFILE_ARTIFACT:{resolved.name}")
    if resolved.suffix.lower() in {".stl", ".step", ".stp"}:
        raise ValueError("PRODUCTION_CAD_OUTPUT_FORBIDDEN")

