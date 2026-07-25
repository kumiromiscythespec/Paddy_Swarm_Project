from __future__ import annotations

from copy import deepcopy
from typing import Any


SAMPLE_IDS = (
    "PROFILE-01-SAMPLE-A",
    "PROFILE-01-SAMPLE-B",
    "PROFILE-02-SAMPLE-A",
    "PROFILE-02-SAMPLE-B",
)

THREE_POSITION_ITEMS = {
    "actual_overall_width": ("mm", "DIRECT_CALIPER_MEASUREMENT"),
    "actual_overall_height": ("mm", "DIRECT_CALIPER_MEASUREMENT"),
    "slot_opening_width": ("mm", "DIRECT_CALIPER_MEASUREMENT"),
}

SINGLE_POSITION_ITEMS = {
    "actual_total_length": ("mm", "DIRECT_CALIPER_MEASUREMENT", "FULL_LENGTH"),
    "slot_internal_maximum_width": (
        "mm",
        "SUPPLIER_DRAWING_REQUIRED",
        "SECTION_REFERENCE",
    ),
    "slot_depth": ("mm", "DEPTH_GAUGE_MEASUREMENT", "END_A"),
    "center_bore_diameter": (
        "mm",
        "DIRECT_CALIPER_MEASUREMENT",
        "END_A",
    ),
    "external_corner_radius": (
        "mm",
        "NOT_MEASURABLE_WITH_AVAILABLE_TOOL",
        "END_A",
    ),
    "visible_internal_cavity_dimensions": (
        "mm",
        "SECTION_CUT_REQUIRED",
        "SECTION_REFERENCE",
    ),
    "straightness_over_400_mm": (
        "mm",
        "NOT_MEASURABLE_WITH_AVAILABLE_TOOL",
        "FULL_LENGTH",
    ),
    "twist_over_400_mm": (
        "degree",
        "NOT_MEASURABLE_WITH_AVAILABLE_TOOL",
        "FULL_LENGTH",
    ),
    "measured_mass": ("g", "MASS_MEASUREMENT", "WHOLE_SAMPLE"),
    "finish_condition": ("visual", "VISUAL_INSPECTION", "WHOLE_SAMPLE"),
    "shipping_damage": ("visual", "VISUAL_INSPECTION", "WHOLE_SAMPLE"),
    "burrs": ("visual", "VISUAL_INSPECTION", "END_A_AND_END_B"),
    "slot_contamination": (
        "visual",
        "VISUAL_INSPECTION",
        "ALL_SLOTS",
    ),
}


def _profile_id(sample_id: str) -> str:
    return "-".join(sample_id.split("-")[:2])


def _empty_row(
    *,
    sample_id: str,
    item: str,
    unit: str,
    method: str,
    position: str,
) -> dict[str, Any]:
    return {
        "profile_id": _profile_id(sample_id),
        "sample_id": sample_id,
        "measurement_item": item,
        "measurement_position": position,
        "required_method": method,
        "value": "",
        "unit": unit,
        "instrument": "",
        "instrument_resolution": "",
        "repetition_count": "",
        "operator_note": "",
        "acceptance_status": "NOT_MEASURED",
    }


def build_inspection_contract() -> dict[str, Any]:
    rows = []
    for sample_id in SAMPLE_IDS:
        for item, (unit, method) in THREE_POSITION_ITEMS.items():
            for position in ("END_A", "CENTER", "END_B"):
                rows.append(
                    _empty_row(
                        sample_id=sample_id,
                        item=item,
                        unit=unit,
                        method=method,
                        position=position,
                    )
                )
        for item, (unit, method, position) in (
            SINGLE_POSITION_ITEMS.items()
        ):
            rows.append(
                _empty_row(
                    sample_id=sample_id,
                    item=item,
                    unit=unit,
                    method=method,
                    position=position,
                )
            )
        for position in ("END_A", "END_B"):
            rows.append(
                _empty_row(
                    sample_id=sample_id,
                    item="end_face_condition",
                    unit="visual",
                    method="VISUAL_INSPECTION",
                    position=position,
                )
            )
    return {
        "schema": "PS_INCOMING_PROFILE_INSPECTION_CONTRACT_V0_1",
        "arrival_status": "PENDING",
        "measurement_status": "INCOMPLETE",
        "minimum_samples_per_profile": 2,
        "sample_ids": list(SAMPLE_IDS),
        "rows": rows,
        "photo_only_numeric_internal_geometry_allowed": False,
        "unavailable_tool_measurement_complete_allowed": False,
    }


def validate_inspection_contract(contract: dict[str, Any]) -> None:
    if set(contract.get("sample_ids", [])) != set(SAMPLE_IDS):
        raise ValueError("INSPECTION_SAMPLE_IDS_MISMATCH")
    profile_sample_counts = {
        profile: sum(sample.startswith(profile) for sample in SAMPLE_IDS)
        for profile in ("PROFILE-01", "PROFILE-02")
    }
    if any(count < 2 for count in profile_sample_counts.values()):
        raise ValueError("MINIMUM_TWO_SAMPLES_PER_PROFILE_REQUIRED")
    if (
        contract["arrival_status"] == "PENDING"
        and contract["measurement_status"] == "COMPLETE"
    ):
        raise ValueError("MEASUREMENT_COMPLETE_BEFORE_ARRIVAL")
    required_columns = {
        "value",
        "unit",
        "instrument",
        "instrument_resolution",
        "sample_id",
        "measurement_position",
        "repetition_count",
        "operator_note",
        "acceptance_status",
    }
    for row in contract.get("rows", []):
        if not required_columns.issubset(row):
            raise ValueError("INSPECTION_ROW_SCHEMA_INCOMPLETE")
        if row["acceptance_status"] == "NOT_MEASURED":
            if row["value"] not in {"", None}:
                raise ValueError("UNMEASURED_VALUE_MUST_REMAIN_EMPTY")
        if row["required_method"] in {
            "SUPPLIER_DRAWING_REQUIRED",
            "SECTION_CUT_REQUIRED",
            "NOT_MEASURABLE_WITH_AVAILABLE_TOOL",
        } and row["acceptance_status"] == "MEASURED_ACCEPTED":
            raise ValueError("UNAVAILABLE_METHOD_MARKED_MEASURED")
    if contract.get("photo_only_numeric_internal_geometry_allowed") is not False:
        raise ValueError("PHOTO_NUMERIC_INTERNAL_GEOMETRY_FORBIDDEN")


def record_measurement(
    row: dict[str, Any],
    *,
    value: float,
    instrument: str,
    instrument_resolution: float,
    repetition_count: int,
    arrival_status: str,
    source_classification: str = "ACTUAL_MEASUREMENT",
) -> dict[str, Any]:
    if arrival_status != "RECEIVED":
        raise ValueError("MEASUREMENT_BEFORE_ARRIVAL_FORBIDDEN")
    if source_classification in {
        "NOMINAL_VALUE_SUBSTITUTION",
        "GENERIC_PROFILE_ASSUMPTION",
        "PHOTO_ESTIMATE",
    }:
        raise ValueError("NON_MEASUREMENT_VALUE_SUBSTITUTION_FORBIDDEN")
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("MEASURED_VALUE_MUST_BE_POSITIVE")
    if row["required_method"] in {
        "SUPPLIER_DRAWING_REQUIRED",
        "SECTION_CUT_REQUIRED",
        "NOT_MEASURABLE_WITH_AVAILABLE_TOOL",
    }:
        raise ValueError("MEASUREMENT_METHOD_NOT_AVAILABLE")
    if not instrument or instrument_resolution <= 0 or repetition_count < 1:
        raise ValueError("MEASUREMENT_TRACEABILITY_INCOMPLETE")
    result = deepcopy(row)
    result.update(
        {
            "value": value,
            "instrument": instrument,
            "instrument_resolution": instrument_resolution,
            "repetition_count": repetition_count,
            "acceptance_status": "MEASURED_PENDING_ACCEPTANCE_LIMIT",
        }
    )
    return result
