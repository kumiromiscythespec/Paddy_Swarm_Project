from __future__ import annotations

from copy import deepcopy
from typing import Any

from profile_input_contract import (
    CONFIRMED_CLASSIFICATION,
    DESIGN_AUTHORITY_STATUS,
    PURCHASE_EVIDENCE_CLASSIFICATION,
    REQUIRED_PROFILE_FIELDS,
    UNCONFIRMED_PRODUCTION_FIELDS,
)


PROFILE_RECORDS = (
    {
        "profile_id": "PROFILE-01",
        "manufacturer": "MISUMI",
        "ordered_product_name": (
            "ミスミ MISUMI アルミフレーム 5シリーズ "
            "正方形 20×20mm 1列溝 4面溝 400mm 4本入"
        ),
        "ordered_part_number": "NFS5-2020-400",
        "base_profile_identifier_candidate": "NFS5-2020",
        "nominal_outer_section_mm": [20, 20],
        "ordered_length_mm": 400,
        "ordered_quantity": 4,
        "listing_slot_description": "1列溝・4面溝",
        "listed_finish_or_color": None,
        "purchase_evidence_source": {
            "source_class": "USER_SUPPLIED_ORDER_HISTORY_AND_LISTING",
            "listing_reference": "https://www.amazon.co.jp/dp/B0DKF1VYM3",
            "web_lookup_performed": False,
        },
        "purchase_evidence_classification": (
            PURCHASE_EVIDENCE_CLASSIFICATION
        ),
        "design_authority_status": DESIGN_AUTHORITY_STATUS,
        "arrival_status": "PENDING",
        "measurement_status": "INCOMPLETE",
        "intended_role_status": "CANDIDATE_ONLY",
        "fit_validation_status": "HOLD",
        "production_geometry_gate": "HOLD",
    },
    {
        "profile_id": "PROFILE-02",
        "manufacturer": "MISUMI",
        "ordered_product_name": (
            "ミスミ MISUMI アルミフレーム 5シリーズ "
            "長方形 20×40mm 2列溝 4面溝 400mm 4本入 "
            "NFSB5-2040-400 ブラック"
        ),
        "ordered_part_number": "NFSB5-2040-400",
        "base_profile_identifier_candidate": "NFSB5-2040",
        "nominal_outer_section_mm": [20, 40],
        "ordered_length_mm": 400,
        "ordered_quantity": 4,
        "listing_slot_description": "2列溝・4面溝",
        "listed_finish_or_color": "ブラック",
        "purchase_evidence_source": {
            "source_class": "USER_SUPPLIED_ORDER_HISTORY_AND_LISTING",
            "listing_reference": "https://www.amazon.co.jp/dp/B0FLNBX1Y9",
            "web_lookup_performed": False,
        },
        "purchase_evidence_classification": (
            PURCHASE_EVIDENCE_CLASSIFICATION
        ),
        "design_authority_status": DESIGN_AUTHORITY_STATUS,
        "arrival_status": "PENDING",
        "measurement_status": "INCOMPLETE",
        "intended_role_status": "CANDIDATE_ONLY",
        "fit_validation_status": "HOLD",
        "production_geometry_gate": "HOLD",
    },
)


def build_registry() -> dict[str, Any]:
    records = deepcopy(list(PROFILE_RECORDS))
    confirmed_fields = [
        "manufacturer",
        "ordered_product_name",
        "ordered_part_number",
        "nominal_outer_section_mm",
        "ordered_length_mm",
        "ordered_quantity",
        "listing_slot_description",
    ]
    for record in records:
        record["field_classification"] = {
            field: CONFIRMED_CLASSIFICATION
            for field in confirmed_fields
        }
        if record["listed_finish_or_color"] is not None:
            record["field_classification"][
                "listed_finish_or_color"
            ] = CONFIRMED_CLASSIFICATION
        record["unconfirmed_production_inputs"] = {
            field: {
                "value": None,
                "status": "UNCONFIRMED_HOLD",
                "generic_5_series_inference_allowed": False,
            }
            for field in UNCONFIRMED_PRODUCTION_FIELDS
        }
    return {
        "schema": "PS_REAL_ALUMINUM_PROFILE_REGISTRY_V0_1",
        "registration_status": "PASS_WITH_HOLD",
        "profile_count": len(records),
        "profiles": records,
        "purchase_evidence_is_geometry_authority": False,
        "official_supplier_authority_registered": False,
        "personal_order_data_stored": False,
    }


def validate_registry(registry: dict[str, Any]) -> None:
    records = registry.get("profiles", [])
    if len(records) != 2:
        raise ValueError("EXACTLY_TWO_PROFILE_RECORDS_REQUIRED")
    by_id = {record.get("profile_id"): record for record in records}
    if set(by_id) != {"PROFILE-01", "PROFILE-02"}:
        raise ValueError("PROFILE_IDENTIFIERS_MUST_REMAIN_DISTINCT")
    if (
        by_id["PROFILE-01"]["nominal_outer_section_mm"]
        == by_id["PROFILE-02"]["nominal_outer_section_mm"]
    ):
        raise ValueError("PROFILES_MUST_NOT_BE_TREATED_AS_SAME_SECTION")
    if by_id["PROFILE-01"]["nominal_outer_section_mm"] != [20, 20]:
        raise ValueError("PROFILE_01_NOMINAL_SECTION_MISMATCH")
    if by_id["PROFILE-02"]["nominal_outer_section_mm"] != [20, 40]:
        raise ValueError("PROFILE_02_MUST_REMAIN_20X40")
    part_numbers = set()
    for record in records:
        missing = [
            field
            for field in REQUIRED_PROFILE_FIELDS
            if field not in record
        ]
        if missing:
            raise ValueError(
                "PROFILE_REQUIRED_FIELDS_MISSING:" + ",".join(missing)
            )
        part_number = record["ordered_part_number"]
        if part_number in part_numbers:
            raise ValueError("ORDERED_PART_NUMBER_DUPLICATE")
        part_numbers.add(part_number)
        if (
            record["purchase_evidence_classification"]
            != PURCHASE_EVIDENCE_CLASSIFICATION
        ):
            raise ValueError("PURCHASE_EVIDENCE_CLASSIFICATION_INVALID")
        if record["design_authority_status"] != "NOT_ESTABLISHED":
            raise ValueError("LISTING_PROMOTED_TO_GEOMETRY_AUTHORITY")
        if record["arrival_status"] == "PENDING" and (
            record["measurement_status"] == "COMPLETE"
        ):
            raise ValueError("MEASUREMENT_COMPLETE_BEFORE_ARRIVAL")
        if record["intended_role_status"] != "CANDIDATE_ONLY":
            raise ValueError("ROLE_CANDIDATE_IMPROPERLY_PROMOTED")
        if record["production_geometry_gate"] != "HOLD":
            raise ValueError("PROFILE_REGISTRATION_RELEASED_GEOMETRY")
        for field, item in record[
            "unconfirmed_production_inputs"
        ].items():
            if item["value"] is not None:
                raise ValueError(
                    f"UNCONFIRMED_PROFILE_VALUE_POPULATED:{field}"
                )
            if item["generic_5_series_inference_allowed"] is not False:
                raise ValueError("GENERIC_5_SERIES_INFERENCE_ENABLED")
    if registry.get("purchase_evidence_is_geometry_authority") is not False:
        raise ValueError("PURCHASE_EVIDENCE_MISCLASSIFIED_AS_AUTHORITY")
    if registry.get("personal_order_data_stored") is not False:
        raise ValueError("PERSONAL_ORDER_DATA_STORAGE_FORBIDDEN")


def reject_generic_profile_fill(
    values: dict[str, Any],
    *,
    generic_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if generic_defaults:
        raise ValueError("GENERIC_5_SERIES_VALUE_INFERENCE_FORBIDDEN")
    result = deepcopy(values)
    for field in UNCONFIRMED_PRODUCTION_FIELDS:
        value = result.get(field)
        if value == 0:
            raise ValueError(f"UNMEASURED_VALUE_ZERO_FILLED:{field}")
    return result


def register_accessory(
    accessory_type: str,
    part_number: str | None,
    *,
    evidence_classification: str,
) -> dict[str, str]:
    if evidence_classification in {
        "INFERRED_FROM_ORDERED_PART_NUMBER",
        "INFERRED_FROM_PRODUCT_NAME",
        "GENERIC_5_SERIES_ASSUMPTION",
    }:
        raise ValueError(
            f"ACCESSORY_INFERENCE_FORBIDDEN:{accessory_type}"
        )
    if not part_number:
        raise ValueError(f"ACCESSORY_PART_NUMBER_REQUIRED:{accessory_type}")
    if evidence_classification != "OFFICIAL_SUPPLIER_AUTHORITY":
        raise ValueError("ACCESSORY_REQUIRES_OFFICIAL_SUPPLIER_AUTHORITY")
    return {
        "accessory_type": accessory_type,
        "part_number": part_number,
        "status": "CONFIRMED_BY_OFFICIAL_SUPPLIER_AUTHORITY",
    }
