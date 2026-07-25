from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from audit_contract import (
    BASE_HEAD,
    EXPECTED_TRACKED_STEP_STP_COUNT,
    EXPECTED_TRACKED_STL_COUNT,
    REQUIRED_EXTERNAL_ARTIFACTS,
    build_ai10_audit,
    build_bbox_structural_audit,
    build_cbox_structural_audit,
    build_fastener_audit,
    build_float_width_audit,
    build_overall_audit,
    build_printed_part_audit,
    build_real_profile_audit,
    repository_root,
)
from canonical_inventory import ALGORITHM_IDENTIFIER
from repository_guard import (
    build_cad_diff_report,
    ensure_external_output,
    load_baseline_inventory,
    scan_repository_bytecode,
    scan_source_lane,
    scan_untracked_cad,
)


JSON_ARTIFACTS = {
    "production_input_audit.json",
    "real_profile_input_audit.json",
    "cbox_structural_input_audit.json",
    "bbox_structural_input_audit.json",
    "fastener_input_audit.json",
    "printed_part_manufacturing_input_audit.json",
    "float_production_width_audit.json",
    "ai10_production_input_audit.json",
    "baseline_cad_output_diff_report.json",
    "untracked_cad_output_scan.json",
    "repository_bytecode_audit.json",
    "canonical_inventory_hash_replay.json",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate source-only production-input audit artifacts."
    )
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-inventory", type=Path, required=True)
    return parser.parse_args(argv)


def _stamp(payload: dict[str, Any], generated_at: str) -> dict[str, Any]:
    result = dict(payload)
    result["generated_at_utc"] = generated_at
    return result


def _write_json(
    output: Path,
    name: str,
    payload: dict[str, Any],
    *,
    root: Path,
) -> None:
    destination = output / name
    ensure_external_output(
        destination,
        root,
        allowed_names=set(REQUIRED_EXTERNAL_ARTIFACTS),
    )
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
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
        allowed_names=set(REQUIRED_EXTERNAL_ARTIFACTS),
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
        allowed_names=set(REQUIRED_EXTERNAL_ARTIFACTS),
    )
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _all_records(
    domain: str,
    report: dict[str, Any],
) -> Iterable[tuple[str, dict[str, Any]]]:
    if "records" in report:
        for record in report["records"]:
            yield domain, record
    for category in report.get("categories", []):
        for record in category["inputs"]:
            copy = dict(record)
            copy["field"] = f'{category["category"]}.{record["field"]}'
            yield domain, copy


def _measurement_rows(
    reports: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows = []
    measurement_markers = {
        "MEASUREMENT_REQUIRED",
        "MEASUREMENT_OR_ENGINEERING_REQUIRED",
        "MISSING",
    }
    sequence = 1
    for domain, report in reports.items():
        for _, record in _all_records(domain, report):
            if record["classification"] not in measurement_markers:
                continue
            rows.append(
                {
                    "measurement_id": f"M-{sequence:03d}",
                    "domain": domain,
                    "field": record["field"],
                    "current_classification": record["classification"],
                    "required_action": record.get("closure_action") or "",
                    "unit": record.get("unit") or "",
                    "acceptance_source_required": (
                        "controlled measurement record or approved engineering input"
                    ),
                    "production_release_effect": "HOLD",
                }
            )
            sequence += 1
    for field_name in reports["float_width"]["missing_inputs"]:
        rows.append(
            {
                "measurement_id": f"M-{sequence:03d}",
                "domain": "float_width",
                "field": field_name,
                "current_classification": "MEASUREMENT_REQUIRED",
                "required_action": (
                    "Measure on the production-intent assembled float configuration."
                ),
                "unit": "mm",
                "acceptance_source_required": "controlled measurement record",
                "production_release_effect": "HOLD",
            }
        )
        sequence += 1
    return rows


def _purchase_rows() -> list[dict[str, str]]:
    specifications = (
        (
            "P-001",
            "real_profile",
            "20x20 T-slot extrusion",
            "manufacturer, product PN, section drawing, alloy, finish, "
            "tolerance, mass/m",
        ),
        (
            "P-002",
            "real_profile",
            "profile-compatible T-nut",
            "manufacturer, SKU, thread, fit range, proof/load rating, finish",
        ),
        (
            "P-003",
            "real_profile",
            "metal corner bracket",
            "manufacturer, SKU, thickness, alloy, load rating, finish",
        ),
        (
            "P-004",
            "fastener",
            "M5 bolt candidate",
            "length by joint, pitch, strength class, material, finish",
        ),
        (
            "P-005",
            "fastener",
            "M5 washer candidate",
            "standard, OD, thickness, material, finish",
        ),
        (
            "P-006",
            "fastener",
            "6 mm-class removable pin candidate",
            "actual diameter/tolerance, grip, material, cross-hole, retention",
        ),
        (
            "P-007",
            "fastener",
            "R-pin candidate",
            "wire size, envelope, compatible cross-hole, material, finish",
        ),
        (
            "P-008",
            "AI-10",
            "20T dual-row drive/PTO pulley candidates",
            "tooth profile, pitch, bore, keying, row spacing, material, SKU",
        ),
        (
            "P-009",
            "AI-10",
            "sync/downstream belt candidates",
            "profile, width, tooth count, length, tension, environmental rating",
        ),
        (
            "P-010",
            "printed_parts",
            "production print material",
            "grade, colour, batch traceability, moisture control, UV/water/"
            "temperature data",
        ),
    )
    return [
        {
            "purchase_id": identifier,
            "domain": domain,
            "item": item,
            "required_supplier_specification": requirement,
            "current_status": "NOT_APPROVED",
            "substitution_allowed_without_review": "NO",
        }
        for identifier, domain, item, requirement in specifications
    ]


def _readiness_rows(
    reports: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    definitions = (
        (
            "real_profile",
            "REAL_PROFILE_INPUT_STATUS",
            reports["profile"]["status"],
            "Supplier geometry and fit inputs incomplete.",
        ),
        (
            "cbox_structure",
            "CBOX_STRUCTURAL_INPUT_STATUS",
            reports["cbox"]["status"],
            "Loads, COG, contact, clamp, drainage, and interference incomplete.",
        ),
        (
            "bbox_structure",
            "BBOX_STRUCTURAL_INPUT_STATUS",
            reports["bbox"]["status"],
            "Independent load path geometry and loads incomplete.",
        ),
        (
            "fasteners",
            "FASTENER_INPUT_STATUS",
            reports["fastener"]["status"],
            "Candidates exist; purchasable specifications are incomplete.",
        ),
        (
            "printed_parts",
            "PRINTED_PART_INPUT_STATUS",
            reports["printed"]["status"],
            "Category-specific manufacturing and inspection inputs incomplete.",
        ),
        (
            "float_width",
            "FLOAT_PRODUCTION_WIDTH_STATUS",
            reports["float_width"]["status"],
            "Assembled maximum cannot be calculated from current actual inputs.",
        ),
        (
            "AI-10",
            "AI10_PRODUCTION_INPUT_STATUS",
            reports["ai10"]["status"],
            "Reservation and candidates only; manufacturing inputs incomplete.",
        ),
        (
            "part_numbering",
            "PRODUCTION_PART_NUMBER_STATUS",
            "HOLD",
            "New stage/category tokens require repository-wide ratification.",
        ),
    )
    return [
        {
            "domain": domain,
            "gate_name": gate,
            "status": status,
            "blocking_reason": reason,
            "production_stl_generation": "HOLD",
            "manufacturing_status": "NOT_APPROVED",
            "purchase_status": "NOT_APPROVED",
            "field_deployment_status": "NOT_APPROVED",
        }
        for domain, gate, status, reason in definitions
    ]


def _unresolved_markdown(
    reports: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# Unresolved production inputs",
        "",
        "All items below are release blockers. Candidate and dummy values are "
        "not manufacturing authority.",
        "",
    ]
    for domain, report in reports.items():
        unresolved = []
        for _, record in _all_records(domain, report):
            if record["classification"] not in {
                "CONFIRMED_ENVELOPE_ONLY",
                "REQUIREMENT_CONFIRMED",
            }:
                unresolved.append(record)
        if domain == "float_width":
            unresolved.extend(
                {
                    "field": item,
                    "classification": "MEASUREMENT_REQUIRED",
                    "closure_action": (
                        "Measure the production-intent assembled configuration."
                    ),
                }
                for item in report["missing_inputs"]
            )
        lines.extend((f"## {domain}", ""))
        for record in unresolved:
            lines.append(
                f'- `{record["field"]}` — {record["classification"]}: '
                f'{record.get("closure_action") or "controlled input required"}'
            )
        lines.append("")
    return "\n".join(lines)


PART_NUMBER_PROPOSAL = """# Production part-number proposal

Status: **HOLD — proposal only; no repository-wide rule is ratified here.**

The existing repository pattern is
`PS-[MACHINE]-[STAGE]-[CATEGORY]-[NUMBER]-[REV]`. Existing dummy identifiers
must never be promoted or copied into production simply by removing `DUMMY
ONLY`.

## Proposed decisions requiring ratification

- Reserve a new, non-dummy production-intent prototype stage token. `PI` is a
  candidate mnemonic only; it is not assigned by this audit and must first be
  checked for repository-wide uniqueness and format compatibility.
- Reuse an existing manufacturing-intent category only when its lifecycle and
  serial namespace are explicitly compatible. Otherwise allocate a new
  category token through the repository numbering authority.
- Assign left and right parts independent serial numbers. Do not encode the
  second hand only as an ungoverned filename suffix.
- Give every sacrificial or replaceable wear part its own governed serial and
  revision. A possible sacrificial category token must be proposed and
  ratified; this audit does not create one.
- Use `R00` only for the first controlled release after profile, structure,
  fastener, manufacturing, width, and inspection gates pass. Any geometry
  change affecting fit, load path, material, orientation, or acceptance
  criteria requires a governed revision decision.
- Physically mark the unique part number and revision on every future printed
  part. Missing, duplicate, or geometry-mismatched markings fail release.

No production part numbers are allocated by this report.
"""


NEXT_LANE = """# Next CAD lane recommendation

Status: **HOLD**

Do not start a production STL/STEP/STP generation lane. The next authorized
work should be an input-closure lane:

1. select and measure the actual extrusion and mating purchase parts;
2. capture CBOX/BBOX mass, COG, loads, hardpoints, clamps, service paths, and
   drainage;
3. select fasteners and approve joint calculations;
4. establish category-specific print process and inspection inputs;
5. measure the complete float assembly and prove both the 286 mm registered
   interface target and 300 mm hard limit;
6. close AI-10 shaft, pulley, belt, guard, interlock, torque-fuse, and
   normally-closed gate inputs;
7. ratify production-intent part-number rules.

Only after every completion gate is closed should a separately authorized,
parametric production-intent CAD lane begin.
"""


def generate(
    *,
    root: Path,
    output: Path,
    baseline_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    baseline_path = baseline_path.resolve()
    if baseline_path.parent != output:
        raise ValueError("SEALED_BASELINE_INVENTORY_MUST_RESIDE_IN_OUTPUT_DIR")
    for name in (
        "baseline_tracked_cad_inventory.json",
        "baseline_tracked_cad_inventory.csv",
        "baseline_tracked_cad_inventory.sha256",
        "canonical_inventory_hash_replay.json",
        "canonical_inventory_hash_replay.txt",
    ):
        if not (output / name).is_file():
            raise FileNotFoundError(f"SEALED_BASELINE_ARTIFACT_MISSING:{name}")
    output.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()

    baseline = load_baseline_inventory(baseline_path)
    if baseline["TRACKED_STL_COUNT"] != EXPECTED_TRACKED_STL_COUNT:
        raise ValueError("BASELINE_TRACKED_STL_COUNT_MISMATCH")
    if (
        baseline["TRACKED_STEP_STP_COUNT"]
        != EXPECTED_TRACKED_STEP_STP_COUNT
    ):
        raise ValueError("BASELINE_TRACKED_STEP_STP_COUNT_MISMATCH")
    if baseline["inventory_hash_algorithm"] != ALGORITHM_IDENTIFIER:
        raise ValueError("BASELINE_INVENTORY_ALGORITHM_MISMATCH")
    replay = json.loads(
        (output / "canonical_inventory_hash_replay.json").read_text(
            encoding="utf-8"
        )
    )
    if replay.get("algorithm_identifier") != ALGORITHM_IDENTIFIER:
        raise ValueError("CANONICAL_REPLAY_ALGORITHM_MISMATCH")
    if replay.get("recorded_sha256") != baseline["inventory_sha256"]:
        raise ValueError("CANONICAL_REPLAY_RECORDED_SHA_MISMATCH")
    for key in (
        "match",
        "shuffled_replay_match",
        "reversed_replay_match",
    ):
        if replay.get(key) is not True:
            raise ValueError(f"CANONICAL_REPLAY_FAILED:{key}")

    reports = {
        "profile": build_real_profile_audit(root),
        "cbox": build_cbox_structural_audit(),
        "bbox": build_bbox_structural_audit(),
        "fastener": build_fastener_audit(),
        "printed": build_printed_part_audit(),
        "float_width": build_float_width_audit(root),
        "ai10": build_ai10_audit(),
    }
    diff_report = build_cad_diff_report(root, baseline)
    untracked_report = scan_untracked_cad(root)
    bytecode_report = scan_repository_bytecode(root)
    source_report = scan_source_lane(root)

    overall = build_overall_audit(
        profile=reports["profile"],
        cbox=reports["cbox"],
        bbox=reports["bbox"],
        fastener=reports["fastener"],
        printed=reports["printed"],
        float_width=reports["float_width"],
        ai10=reports["ai10"],
    )
    overall["preflight"] = {
        "status": "PASS",
        "base_head": BASE_HEAD,
        "baseline_tracked_stl_count": baseline["TRACKED_STL_COUNT"],
        "baseline_tracked_step_stp_count": baseline[
            "TRACKED_STEP_STP_COUNT"
        ],
        "baseline_inventory_sha256": baseline["inventory_sha256"],
        "baseline_inventory_hash_algorithm": ALGORITHM_IDENTIFIER,
        "canonical_record_order": (
            "UTF8_BYTEWISE_ASCENDING_CANONICAL_POSIX_PATH"
        ),
        "json_csv_order_consistency": baseline[
            "_bundle_validation"
        ]["json_csv_order_consistency"],
        "inventory_receipt_consistency": baseline[
            "_bundle_validation"
        ]["receipt_consistency"],
        "reverse_order_replay": (
            "PASS" if replay["reversed_replay_match"] else "FAIL"
        ),
        "shuffled_order_replay": (
            "PASS" if replay["shuffled_replay_match"] else "FAIL"
        ),
    }
    overall["repository_output_gates"] = {
        **{
            key: diff_report[key]
            for key in (
                "BASELINE_TRACKED_CAD_INVENTORY_MATCH",
                "ADDED_TRACKED_CAD_OUTPUT_COUNT",
                "MODIFIED_TRACKED_CAD_OUTPUT_COUNT",
                "DELETED_TRACKED_CAD_OUTPUT_COUNT",
            )
        },
        "UNTRACKED_CAD_OUTPUT_COUNT": untracked_report[
            "UNTRACKED_CAD_OUTPUT_COUNT"
        ],
        "repository_bytecode_status": bytecode_report["status"],
        "source_lane_status": source_report["status"],
    }

    mapping = {
        "production_input_audit.json": overall,
        "real_profile_input_audit.json": reports["profile"],
        "cbox_structural_input_audit.json": reports["cbox"],
        "bbox_structural_input_audit.json": reports["bbox"],
        "fastener_input_audit.json": reports["fastener"],
        "printed_part_manufacturing_input_audit.json": reports["printed"],
        "float_production_width_audit.json": reports["float_width"],
        "ai10_production_input_audit.json": reports["ai10"],
        "baseline_cad_output_diff_report.json": diff_report,
        "untracked_cad_output_scan.json": untracked_report,
        "repository_bytecode_audit.json": bytecode_report,
    }
    for name, report in mapping.items():
        _write_json(
            output,
            name,
            _stamp(report, generated_at),
            root=root,
        )

    _write_text(
        output,
        "production_part_number_proposal.md",
        PART_NUMBER_PROPOSAL,
        root=root,
    )
    _write_text(
        output,
        "unresolved_production_inputs.md",
        _unresolved_markdown(reports),
        root=root,
    )
    _write_text(
        output,
        "next_cad_lane_recommendation.md",
        NEXT_LANE,
        root=root,
    )
    _write_csv(
        output,
        "production_readiness_matrix.csv",
        [
            "domain",
            "gate_name",
            "status",
            "blocking_reason",
            "production_stl_generation",
            "manufacturing_status",
            "purchase_status",
            "field_deployment_status",
        ],
        _readiness_rows(reports),
        root=root,
    )
    _write_csv(
        output,
        "required_measurements_checklist.csv",
        [
            "measurement_id",
            "domain",
            "field",
            "current_classification",
            "required_action",
            "unit",
            "acceptance_source_required",
            "production_release_effect",
        ],
        _measurement_rows(reports),
        root=root,
    )
    _write_csv(
        output,
        "required_purchase_specifications.csv",
        [
            "purchase_id",
            "domain",
            "item",
            "required_supplier_specification",
            "current_status",
            "substitution_allowed_without_review",
        ],
        _purchase_rows(),
        root=root,
    )
    return overall


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repository_root(args.repository_root)
    result = generate(
        root=root,
        output=args.output_dir,
        baseline_path=args.baseline_inventory,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
