from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context


# Legacy Grade 0 evidence from the task and existing preserved float lane.
LEGACY_FLOAT_ONE_SIDE_NOMINAL_MM = 56.0
LEGACY_NOMINAL_TOTAL_REPORTED_MM = 290.0

# Explicit audit candidates, never authority claims.
PRINTED_BRACKET_THICKNESS_CANDIDATE_MM = 4.0
SLIDE_CLEARANCE_CANDIDATE_MM = 0.4
VISUAL_OVERLAP_CANDIDATE_MM = 8.0
MANUFACTURING_TOLERANCE_ALLOWANCE_MM = 0.6
INCLINATION_ALLOWANCE_MM = 2.0
PRINTED_WALL_ALLOWANCE_MM = 0.4


def build_float_width_audit() -> dict:
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    frame = float(authority["bare_frame_width_mm"])
    registered = float(authority["registered_width_mm"])
    hard = float(authority["hard_limit_width_mm"])
    side_allowance = (
        MANUFACTURING_TOLERANCE_ALLOWANCE_MM
        + INCLINATION_ALLOWANCE_MM
        + PRINTED_WALL_ALLOWANCE_MM
    )

    float_1_nominal = frame + 2.0 * (
        LEGACY_FLOAT_ONE_SIDE_NOMINAL_MM
        + PRINTED_BRACKET_THICKNESS_CANDIDATE_MM
        + SLIDE_CLEARANCE_CANDIDATE_MM
    )
    float_1_audited = float_1_nominal + 2.0 * side_allowance

    float_2_nominal = frame + 2.0 * (
        LEGACY_FLOAT_ONE_SIDE_NOMINAL_MM
        + PRINTED_BRACKET_THICKNESS_CANDIDATE_MM
        + SLIDE_CLEARANCE_CANDIDATE_MM
        - VISUAL_OVERLAP_CANDIDATE_MM
    )
    float_2_audited = float_2_nominal + 2.0 * side_allowance

    max_float_3_side = (
        (registered - frame) / 2.0
        - PRINTED_BRACKET_THICKNESS_CANDIDATE_MM
        - SLIDE_CLEARANCE_CANDIDATE_MM
        - side_allowance
    )

    return {
        "schema": "PS_FLOAT_WIDTH_AUDIT_V0_1",
        "authority": {
            "bare_frame_width_mm": frame,
            "registered_maximum_interface_width_mm": registered,
            "operational_hard_limit_mm": hard,
            "registered_is_hard_limit": False,
            "hard_limit_is_registered_width": False,
        },
        "legacy_evidence": {
            "one_side_nominal_width_mm": (
                LEGACY_FLOAT_ONE_SIDE_NOMINAL_MM
            ),
            "reported_nominal_total_mm": LEGACY_NOMINAL_TOTAL_REPORTED_MM,
            "reported_nominal_vs_registered_mm": (
                LEGACY_NOMINAL_TOTAL_REPORTED_MM - registered
            ),
            "reported_nominal_hard_limit_margin_mm": (
                hard - LEGACY_NOMINAL_TOTAL_REPORTED_MM
            ),
            "accepted_without_bracket_audit": False,
        },
        "audit_inputs_mm_per_side": {
            "printed_bracket_thickness_candidate": (
                PRINTED_BRACKET_THICKNESS_CANDIDATE_MM
            ),
            "slide_clearance_candidate": SLIDE_CLEARANCE_CANDIDATE_MM,
            "manufacturing_tolerance_allowance": (
                MANUFACTURING_TOLERANCE_ALLOWANCE_MM
            ),
            "inclination_allowance": INCLINATION_ALLOWANCE_MM,
            "printed_wall_allowance": PRINTED_WALL_ALLOWANCE_MM,
            "mud_clearance": "UNRESOLVED_HOLD",
        },
        "options": {
            "FLOAT-1": {
                "description": "Legacy float directly beside each rail",
                "nominal_assembled_width_mm": round(float_1_nominal, 3),
                "audited_width_mm": round(float_1_audited, 3),
                "registered_treatment": (
                    "EXCEEDS_REGISTERED_TARGET"
                    if float_1_audited > registered
                    else "WITHIN_REGISTERED_TARGET"
                ),
                "hard_limit_treatment": (
                    "FAIL_EXCEEDS_300"
                    if float_1_audited > hard
                    else "WITHIN_HARD_LIMIT"
                ),
                "status": "REJECT",
            },
            "FLOAT-2": {
                "description": (
                    "Legacy float upper region visually overlaps rail underside"
                ),
                "overlap_candidate_mm_per_side": (
                    VISUAL_OVERLAP_CANDIDATE_MM
                ),
                "nominal_assembled_width_mm": round(float_2_nominal, 3),
                "audited_width_mm": round(float_2_audited, 3),
                "registered_treatment": (
                    "HOLD_AUDITED_CASE_EXCEEDS_REGISTERED_TARGET"
                    if float_2_audited > registered
                    else "WITHIN_REGISTERED_TARGET"
                ),
                "hard_limit_treatment": (
                    "WITHIN_HARD_LIMIT_WITHOUT_OPERATIONAL_APPROVAL"
                    if float_2_audited <= hard
                    else "FAIL_EXCEEDS_300"
                ),
                "hard_limit_margin_mm": round(hard - float_2_audited, 3),
                "status": "SELECTED_VISUAL_DUMMY_ONLY",
            },
            "FLOAT-3": {
                "description": "New narrower current-rover float section",
                "maximum_one_side_width_for_registered_case_mm": round(
                    max_float_3_side, 3
                ),
                "geometry_authority": "NOT_ESTABLISHED",
                "status": "HOLD_REQUIRES_NEW_FLOAT_DESIGN",
            },
            "FLOAT-4": {
                "description": (
                    "Use preserved legacy float visually; operational width HOLD"
                ),
                "nominal_width_mm": LEGACY_NOMINAL_TOTAL_REPORTED_MM,
                "registered_treatment": "EXCEEDS_BY_4_MM",
                "hard_limit_treatment": "NOMINALLY_BELOW_BY_10_MM",
                "status": "VISUAL_ONLY_HOLD",
            },
        },
        "selected_option": "FLOAT-2_WITH_FLOAT-4_OPERATIONAL_HOLD",
        "recommendation": (
            "Use the legacy-compatible adapter/receiver kit and an 8 mm-per-side "
            "visual overlap to continue the assembly dummy. Do not approve an "
            "operational float until bracket, mud, tolerance, inclination, and "
            "wall measurements prove both width categories."
        ),
        "adapter_kit": "A_LEGACY_FLOAT_COMPATIBLE_ADAPTER_KIT",
        "FLOAT_FULL_SCALE_PRINT": "HOLD",
        "FLOAT_WIDTH_STATUS": "HOLD",
    }


def reject_unqualified_width(
    *,
    nominal_mm: float,
    bracket_audited: bool,
    registered_treated_as_hard: bool = False,
    hard_treated_as_registered: bool = False,
) -> None:
    if nominal_mm == LEGACY_NOMINAL_TOTAL_REPORTED_MM and not bracket_audited:
        raise ValueError("UNAUDITED_290_MM_NOMINAL_WIDTH")
    if registered_treated_as_hard:
        raise ValueError("REGISTERED_WIDTH_IS_NOT_HARD_LIMIT")
    if hard_treated_as_registered:
        raise ValueError("HARD_LIMIT_IS_NOT_REGISTERED_WIDTH")
    if nominal_mm > 300.0:
        raise ValueError("FLOAT_ASSEMBLY_EXCEEDS_HARD_LIMIT")
