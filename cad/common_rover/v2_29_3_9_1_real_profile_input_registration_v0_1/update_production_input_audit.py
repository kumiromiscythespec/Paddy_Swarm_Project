from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from incoming_inspection_contract import build_inspection_contract
from profile_input_contract import (
    CANONICAL_INVENTORY_ALGORITHM,
    CANONICAL_INVENTORY_SHA256,
    EXTERNAL_ARTIFACT_NAMES,
    SUPPLIER_DOCUMENT_REQUIREMENTS,
    UNCONFIRMED_PRODUCTION_FIELDS,
    ensure_external_output,
    repository_root,
)
from profile_role_candidate_matrix import build_role_matrix
from supplier_profile_registry import build_registry


def build_production_audit_update() -> dict[str, Any]:
    return {
        "schema": "PS_PRODUCTION_AUDIT_REAL_PROFILE_UPDATE_V0_1",
        "PROFILE_REGISTRATION": "PASS_WITH_HOLD",
        "PROFILE_01_ORDER_INPUT": "COMPLETE",
        "PROFILE_02_ORDER_INPUT": "COMPLETE",
        "REAL_PROFILE_MANUFACTURER_STATUS": "COMPLETE",
        "REAL_PROFILE_ORDERED_MODEL_STATUS": "COMPLETE",
        "REAL_PROFILE_NOMINAL_SECTION_STATUS": "COMPLETE",
        "REAL_PROFILE_LENGTH_QUANTITY_STATUS": "COMPLETE",
        "REAL_PROFILE_ARRIVAL_STATUS": "PENDING",
        "REAL_PROFILE_MEASUREMENT_STATUS": "INCOMPLETE",
        "REAL_PROFILE_SECTION_AUTHORITY_STATUS": "INCOMPLETE",
        "REAL_PROFILE_ACCESSORY_STATUS": "INCOMPLETE",
        "REAL_PROFILE_ROLE_ASSIGNMENT_STATUS": "HOLD",
        "REAL_PROFILE_FIT_VALIDATION_STATUS": "HOLD",
        "REAL_PROFILE_INPUT_STATUS": "INCOMPLETE",
        "PRODUCTION_INPUT_AUDIT": "PASS_WITH_HOLD",
        "PRODUCTION_STL_GENERATION": "HOLD",
        "PRINT_STAGE": "NOT_REACHED",
        "inherited_domain_gates": {
            "CBOX_STRUCTURAL_INPUT_STATUS": "INCOMPLETE",
            "BBOX_STRUCTURAL_INPUT_STATUS": "INCOMPLETE",
            "FASTENER_INPUT_STATUS": "INCOMPLETE",
            "PRINTED_PART_INPUT_STATUS": "INCOMPLETE",
            "FLOAT_PRODUCTION_WIDTH_STATUS": "HOLD",
            "AI10_PRODUCTION_INPUT_STATUS": "INCOMPLETE",
            "PRODUCTION_PART_NUMBER_STATUS": "HOLD",
            "MANUFACTURING_STATUS": "NOT_APPROVED",
            "PURCHASE_STATUS": "NOT_APPROVED",
            "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        },
        "purchase_information_is_design_authority": False,
        "amazon_listing_is_cross_section_authority": False,
        "web_lookup_performed": False,
    }


def approve_production_stl(
    update: dict[str, Any],
    *,
    registration_only: bool = True,
) -> None:
    del update
    if registration_only:
        raise ValueError(
            "PROFILE_REGISTRATION_CANNOT_APPROVE_PRODUCTION_STL"
        )
    raise ValueError("PRODUCTION_INPUT_COMPLETION_GATE_NOT_SATISFIED")


def validate_production_part_number(
    candidate: str,
    *,
    dummy_part_numbers: set[str],
) -> None:
    if candidate in dummy_part_numbers or "DUMMY" in candidate.upper():
        raise ValueError("DUMMY_PART_NUMBER_PRODUCTION_REUSE_FORBIDDEN")


def _registration_audit() -> dict[str, Any]:
    return {
        "schema": "PS_SUPPLIER_PROFILE_REGISTRATION_AUDIT_V0_1",
        "status": "PASS_WITH_HOLD",
        "registered_profile_count": 2,
        "order_evidence_complete_profile_ids": [
            "PROFILE-01",
            "PROFILE-02",
        ],
        "purchase_evidence_classification": (
            "USER_SUPPLIED_ORDER_EVIDENCE"
        ),
        "production_geometry_authority": "NOT_ESTABLISHED",
        "official_supplier_documents_registered": False,
        "arrival_status": "PENDING",
        "measurement_status": "INCOMPLETE",
        "candidate_roles_finalized": False,
        "production_geometry_gate": "HOLD",
        "personal_order_number_stored": False,
        "customer_name_stored": False,
        "shipping_address_stored": False,
        "payment_information_stored": False,
        "web_lookup_performed": False,
    }


def _instructions() -> str:
    return """# Incoming aluminum-profile inspection instructions

Status: **PENDING ARRIVAL / NOT MEASURED**

Keep PROFILE-01 and PROFILE-02 physically separated and label at least two
members from each ordered model:

- PROFILE-01-SAMPLE-A
- PROFILE-01-SAMPLE-B
- PROFILE-02-SAMPLE-A
- PROFILE-02-SAMPLE-B

Record overall width, overall height, and slot opening at END_A, CENTER, and
END_B. Every entry requires the actual value, unit, instrument, instrument
resolution, sample ID, position, repetition count, operator note, and
acceptance status.

Use direct calipers only on directly accessible geometry. Use a depth gauge
for slot depth and a scale for mass. Use visual inspection only for condition,
damage, burrs, and contamination. Do not turn photographs into numerical
internal dimensions.

Complex slot geometry, thin walls, and internal cavities require an official
supplier drawing or a separately authorized section cut. Straightness, twist,
and radius remain `NOT_MEASURABLE_WITH_AVAILABLE_TOOL` until an appropriate
instrument and procedure are registered.

Blank values mean `NOT_MEASURED`; never enter zero or a nominal/listing value
as a substitute. Acceptance limits remain HOLD until official tolerances and
the rover fit/structural requirements are approved.
"""


def _unresolved_markdown() -> str:
    lines = [
        "# Unresolved real-profile inputs",
        "",
        "Purchase registration does not establish production cross-section "
        "geometry.",
        "",
        "## Production geometry and accessories",
        "",
    ]
    lines.extend(
        f"- `{field}` — UNCONFIRMED / HOLD"
        for field in UNCONFIRMED_PRODUCTION_FIELDS
    )
    lines.extend(
        [
            "",
            "## Placement and role",
            "",
            "- final placement",
            "- PROFILE-02 40 mm direction and vertical/horizontal orientation",
            "- left/right symmetry",
            "- cut lengths and connection method",
            "- rover width and BBOX support height",
            "- PTO, motor-pod, and float interference",
            "",
            "No production STL/STEP/STP generation is authorized.",
        ]
    )
    return "\n".join(lines)


def _write_json(
    output: Path,
    name: str,
    payload: dict[str, Any],
    *,
    root: Path,
    generated_at: str,
) -> None:
    destination = output / name
    ensure_external_output(
        destination,
        root,
        allowed_names=set(EXTERNAL_ARTIFACT_NAMES),
    )
    result = dict(payload)
    result["generated_at_utc"] = generated_at
    destination.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_text(
    output: Path,
    name: str,
    content: str,
    *,
    root: Path,
) -> None:
    destination = output / name
    ensure_external_output(
        destination,
        root,
        allowed_names=set(EXTERNAL_ARTIFACT_NAMES),
    )
    destination.write_text(
        content.rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(
    output: Path,
    name: str,
    fieldnames: list[str],
    rows: Iterable[dict[str, Any]],
    *,
    root: Path,
) -> None:
    destination = output / name
    ensure_external_output(
        destination,
        root,
        allowed_names=set(EXTERNAL_ARTIFACT_NAMES),
    )
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def generate_artifacts(
    *,
    root: Path,
    output: Path,
    baseline_inventory: Path,
) -> dict[str, Any]:
    from validate_profile_registration import build_repository_gate_reports

    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError("PROFILE_ARTIFACT_MUST_BE_OUTSIDE_REPOSITORY")
    output.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    registry = build_registry()
    roles = build_role_matrix()
    inspection = build_inspection_contract()
    update = build_production_audit_update()
    gates = build_repository_gate_reports(root, baseline_inventory)

    _write_json(
        output,
        "supplier_profile_registry.json",
        registry,
        root=root,
        generated_at=generated_at,
    )
    _write_json(
        output,
        "supplier_profile_registration_audit.json",
        _registration_audit(),
        root=root,
        generated_at=generated_at,
    )
    _write_json(
        output,
        "production_audit_profile_update.json",
        update,
        root=root,
        generated_at=generated_at,
    )
    _write_json(
        output,
        "baseline_cad_output_diff_report.json",
        gates["cad_diff"],
        root=root,
        generated_at=generated_at,
    )
    _write_json(
        output,
        "untracked_cad_output_scan.json",
        gates["untracked_cad"],
        root=root,
        generated_at=generated_at,
    )
    _write_json(
        output,
        "repository_bytecode_audit.json",
        gates["bytecode"],
        root=root,
        generated_at=generated_at,
    )
    role_fields = list(roles["rows"][0])
    _write_csv(
        output,
        "profile_role_candidate_matrix.csv",
        role_fields,
        roles["rows"],
        root=root,
    )
    inspection_fields = list(inspection["rows"][0])
    _write_csv(
        output,
        "incoming_profile_inspection_template.csv",
        inspection_fields,
        inspection["rows"],
        root=root,
    )
    _write_csv(
        output,
        "required_supplier_documents.csv",
        [
            "requirement_id",
            "required_document_or_specification",
            "current_status",
            "authority_effect",
        ],
        [
            {
                "requirement_id": f"DOC-{index:02d}",
                "required_document_or_specification": requirement,
                "current_status": "NOT_REGISTERED",
                "authority_effect": "PRODUCTION_GEOMETRY_HOLD",
            }
            for index, requirement in enumerate(
                SUPPLIER_DOCUMENT_REQUIREMENTS,
                start=1,
            )
        ],
        root=root,
    )
    _write_text(
        output,
        "incoming_profile_inspection_instructions.md",
        _instructions(),
        root=root,
    )
    _write_text(
        output,
        "unresolved_profile_inputs.md",
        _unresolved_markdown(),
        root=root,
    )
    return {
        "PROFILE_REGISTRATION": "PASS_WITH_HOLD",
        "canonical_inventory_algorithm": CANONICAL_INVENTORY_ALGORITHM,
        "canonical_inventory_sha256": CANONICAL_INVENTORY_SHA256,
        "repository_gates": gates,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-inventory", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = generate_artifacts(
        root=repository_root(args.repository_root),
        output=args.output_dir,
        baseline_inventory=args.baseline_inventory,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
