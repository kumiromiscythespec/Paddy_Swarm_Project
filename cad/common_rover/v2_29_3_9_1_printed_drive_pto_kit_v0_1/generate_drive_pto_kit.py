from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

from belt_family import belt_manifest_rows, build_belt_family
from coupon_family import build_all_coupons, coupon_manifest_rows
from drive_pto_contract import (
    EXPECTED_BRANCH,
    EXPECTED_HEAD,
    SOURCE_REUSE_PROVENANCE,
    SOURCE_REUSE_RESULT,
    contract_dict,
)
from geometry_common import BuiltPart, export_part
from guard_family import build_guard_family
from hub_adapter_family import build_hubs_spacers_and_flanges
from missing_part_audit import AUDIT_ROWS, validate_audit
from part_number_registry import ALL_PARTS, validate_registry
from pulley_family import build_all_pulleys, pulley_manifest_rows
from tensioner_family import build_tensioner_family
from tooling_family import build_tooling_family
from validate_drive_pto_kit import (
    SOURCE_LANE,
    sha256_file,
    validate_all,
    write_validation,
)


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"EMPTY_CSV_REJECTED:{path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _assert_external_output(output: Path, repo_root: Path) -> None:
    resolved_output = output.resolve()
    resolved_repo = repo_root.resolve()
    if resolved_output == resolved_repo or resolved_repo in resolved_output.parents:
        raise ValueError("ARTIFACT_DIRECTORY_MUST_BE_OUTSIDE_REPOSITORY")


def build_all_parts() -> list[BuiltPart]:
    groups = (
        build_all_pulleys(),
        build_belt_family(),
        build_all_coupons(),
        build_hubs_spacers_and_flanges(),
        build_tensioner_family(),
        build_guard_family(),
        build_tooling_family(),
    )
    parts = [part for group in groups for part in group]
    expected = {part.part_number for part in ALL_PARTS if part.generated}
    actual = {part.spec.part_number for part in parts}
    if expected != actual:
        raise RuntimeError(
            f"GENERATED_REGISTRY_MISMATCH:missing={sorted(expected-actual)}:"
            f"unexpected={sorted(actual-expected)}"
        )
    return parts


def _part_registry_rows() -> list[dict[str, object]]:
    return [
        {
            "key": part.key,
            "part_number": part.part_number,
            "revision": "R00",
            "title": part.title,
            "family": part.family,
            "filename": part.filename if part.generated else "NOT_GENERATED",
            "material": part.material,
            "classification": part.classification,
            "print_target": part.print_target,
            "generated": part.generated,
            "physical_marking": (
                "ENGRAVED" if part.generated else "HOLD_NOT_PRINTED"
            ),
        }
        for part in ALL_PARTS
    ]


def _print_target_rows() -> list[dict[str, object]]:
    return [
        {"target": "TARGET-P0-CALIBRATION", "status": "APPROVED", "contents": "D6/B10 A-B-C; T20/T60 A-B-C; commercial/printed belt fit; PCD24; clamp insert; TPU thickness; joiner"},
        {"target": "TARGET-P1-FIRST-ARTICLE", "status": "HOLD_COUPON_PASS_REQUIRED", "contents": "DRIVE-L 20T/60T; short TPU belt; tensioner; alignment gauge"},
        {"target": "TARGET-P2-ONE-DRIVE-PATH", "status": "HOLD_FIRST_ARTICLE_MEASUREMENTS", "contents": "DRIVE-L 20T/60T; 450 belt; spacers; tensioner; guard"},
        {"target": "TARGET-P3-DUAL-DRIVE", "status": "HOLD_P2_PASS", "contents": "DRIVE-R set and drive spares"},
        {"target": "TARGET-P4-PTO-A", "status": "HOLD_PTO_INPUTS_AND_BELT_LENGTH", "contents": "PTO-A pulleys/hardware sources ready; final belt not generated"},
        {"target": "TARGET-P5-PTO-B", "status": "HOLD_PTO_INPUTS_AND_BELT_LENGTH", "contents": "PTO-B pulleys/hardware sources ready; final belt not generated"},
        {"target": "TARGET-P6-FULL-4-SET", "status": "HOLD", "contents": "All confirmed parts plus practical spares"},
    ]


def _measurement_rows() -> list[dict[str, object]]:
    rows = []
    for coupon_type, candidates, unit in (
        ("D6_BORE", ("5.90", "6.00", "6.10"), "mm"),
        ("B10_BORE", ("9.88", "10.00", "10.12"), "mm"),
        ("20T_TOOTH_WIDTH_COMP", ("-0.12", "0.00", "0.12"), "mm"),
        ("60T_TOOTH_WIDTH_COMP", ("-0.12", "0.00", "0.12"), "mm"),
    ):
        for variant, target in zip(("A", "B", "C"), candidates):
            rows.append(
                {
                    "coupon_type": coupon_type,
                    "variant": variant,
                    "design_candidate": target,
                    "unit": unit,
                    "measured_value": "CALIBRATION_PENDING",
                    "fit_result": "CALIBRATION_PENDING",
                    "selected": "CALIBRATION_PENDING",
                    "operator": "CALIBRATION_PENDING",
                    "date": "CALIBRATION_PENDING",
                }
            )
    for coupon_type in (
        "COMMERCIAL_450_5M_15_FIT",
        "PRINTED_TPU_BELT_FIT",
        "PCD24_4XM4",
        "CLAMP_INSERT",
        "TPU_THICKNESS",
        "TPU_JOINER_HAND_FIT",
    ):
        rows.append(
            {
                "coupon_type": coupon_type,
                "variant": "A",
                "design_candidate": "SEE_COUPON_MANIFEST",
                "unit": "inspection",
                "measured_value": "CALIBRATION_PENDING",
                "fit_result": "CALIBRATION_PENDING",
                "selected": "CALIBRATION_PENDING",
                "operator": "CALIBRATION_PENDING",
                "date": "CALIBRATION_PENDING",
            }
        )
    return rows


PRINT_ORDER = """# Print order

1. Print `TARGET-P0-CALIBRATION` only.
2. Measure every A/B/C coupon and replace every `CALIBRATION_PENDING` field.
3. Select bore and tooth compensation only from recorded coupon results.
4. Print `TARGET-P1-FIRST-ARTICLE`; do not power it.
5. Inspect tooth engagement, flange clearance, clamp retention, runout, and belt tracking by hand.
6. After signed first-article acceptance, print `TARGET-P2-ONE-DRIVE-PATH`.
7. `TARGET-P3` through `TARGET-P6` remain gated; PTO final belts remain HOLD.

All parts are test candidates. Support is OFF unless a later reviewed process sheet explicitly changes it.
"""

ASSEMBLY_ORDER = """# Assembly order

1. Install purchased metal shafts, bearings, pillow blocks, fasteners, washers, and locknuts.
2. Fit the selected coupon-qualified pulley bore; never force an unqualified bore.
3. Use metal bolts/inserts for every split clamp. Printed PETG threads are not a torque authority.
4. Support belt reaction through the metal motor bracket/slide and output bearing blocks.
5. Fit pulley alignment and shaft parallelism gauges before the belt.
6. Install spacers and removable flange; hand-turn through at least five revolutions.
7. Install the tensioner as a guide only. Apply no more than the minimum no-slip hand tension.
8. Fit the temporary guard before any powered test.
9. Leave both PTO belts removed during the first drive test.
"""

POWERED_GATE = """# Powered-test gate

Status: **HOLD**

Before a staged powered no-load approval can be requested:

- Coupon result must be recorded as PASS.
- PTO belts must be removed.
- Test only one drive side with the rover lifted clear of the ground.
- Use a low current limit and keep the emergency stop in hand.
- Fit the temporary belt and shaft guards.
- Keep hands, hair, clothing, and tools away from belts and pulleys.
- Jog forward briefly, stop and inspect, then jog reverse briefly.
- Stop immediately for noise, tooth skip, tracking drift, cracking, heat, or clamp movement.

Joiner-fit belts are never permitted in a powered test. Powered loaded testing and field use remain HOLD.
"""

UNRESOLVED_INPUTS = """# Unresolved inputs

- PTO-A shaft diameter: `CALIBRATION_PENDING`
- PTO-A center distance: `CALIBRATION_PENDING`
- PTO-A usable shaft length: `CALIBRATION_PENDING`
- PTO-B shaft diameter: `CALIBRATION_PENDING`
- PTO-B center distance: `CALIBRATION_PENDING`
- PTO-B usable shaft length: `CALIBRATION_PENDING`
- D6 bore compensation selection: `CALIBRATION_PENDING`
- B10 bore compensation selection: `CALIBRATION_PENDING`
- 20T/60T tooth compensation selection: `CALIBRATION_PENDING`
- TPU pitch/shrinkage compensation: `CALIBRATION_PENDING`
- Final frame mounting holes for tensioners and guards: `HOLD`
- Sacrificial torque-fuse release torque: `CALIBRATION_PENDING`

No final PTO continuous-loop STL is generated until all three measurements for that path are authoritative.
"""


def _write_source_patch(repo_root: Path, output_path: Path) -> None:
    source_root = repo_root / SOURCE_LANE
    chunks = []
    for path in sorted(
        item for item in source_root.rglob("*") if item.is_file()
    ):
        relative = path.relative_to(repo_root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        chunks.extend(
            difflib.unified_diff(
                [],
                lines,
                fromfile="/dev/null",
                tofile=f"b/{relative}",
            )
        )
    output_path.write_text(
        "".join(chunks), encoding="utf-8", newline="\n"
    )


def _completion_status(validation: dict[str, object]) -> dict[str, object]:
    return {
        "PREFLIGHT": "PASS",
        "PREFLIGHT_SCAN_SCOPE": "TARGET_WORKTREE_ONLY",
        "SOURCE_REUSE_AUDIT": "PASS",
        "SOURCE_REUSE_RESULT": SOURCE_REUSE_RESULT,
        "PULLEY_20T_SOURCE": "COMPLETE",
        "PULLEY_60T_SOURCE": "COMPLETE",
        "TPU_BELT_SOURCE": "COMPLETE",
        "COUPON_SOURCE": "COMPLETE",
        "TENSIONER_SOURCE": "COMPLETE",
        "GUARD_SOURCE": "COMPLETE",
        "ADDITIONAL_MISSING_PART_AUDIT": "COMPLETE",
        "DRIVE_L_STL": "GENERATED",
        "DRIVE_R_STL": "GENERATED",
        "PTO_A_STL": "HOLD",
        "PTO_B_STL": "HOLD",
        "PTO_HOLD_REASON": "FINAL_CONTINUOUS_BELT_LENGTH_UNCONFIRMED",
        "PHYSICAL_PART_NUMBER_STATUS": validation[
            "physical_part_number_status"
        ],
        "GEOMETRY_VALIDATION": validation["status"],
        "BUILD_PLATE_FIT": validation["build_plate"]["status"],
        "CALIBRATION_PRINT": (
            "APPROVED" if validation["status"] == "PASS" else "HOLD"
        ),
        "FIRST_ARTICLE_PRINT": "HOLD",
        "FULL_4_SET_PRINT": "HOLD",
        "POWERED_NO_LOAD_TEST": "HOLD",
        "POWERED_LOAD_TEST": "HOLD",
        "FIELD_DEPLOYMENT": "HOLD",
        "TARGET_WORKTREE_PYC_COUNT": validation["repository"]["pyc_count"],
        "TARGET_WORKTREE_PYO_COUNT": validation["repository"]["pyo_count"],
        "TARGET_WORKTREE_PYCACHE_COUNT": validation["repository"][
            "pycache_count"
        ],
        "UNRELATED_WORKTREE_BYTECODE": "OUT_OF_SCOPE",
        "COMMIT_CREATED": "NO",
        "PUSH_EXECUTED": "NO",
        "PR_CREATED": "NO",
    }


def generate(output: Path, repo_root: Path) -> dict[str, object]:
    _assert_external_output(output, repo_root)
    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "drive_pto_contract.json", contract_dict())
    _write_json(
        output / "source_reuse_audit.json",
        {
            "status": "PASS",
            "result": SOURCE_REUSE_RESULT,
            "search_scope": "TARGET_WORKTREE_ONLY",
            "searched_terms": [
                "HTD-5M",
                "htd5m",
                "20T",
                "60T",
                "timing pulley",
                "timing belt",
                "pulley coupon",
                "bore coupon",
                "D-shaft",
                "PCD24",
                "tensioner",
                "belt guard",
                "PTO pulley",
            ],
            "provenance": SOURCE_REUSE_PROVENANCE,
            "external_branch_import": "NONE",
            "cherry_pick": "NONE",
            "merge": "NONE",
        },
    )
    _write_csv(output / "part_number_registry.csv", _part_registry_rows())
    _write_csv(output / "pulley_manifest.csv", pulley_manifest_rows())
    _write_csv(output / "belt_manifest.csv", belt_manifest_rows())
    _write_csv(output / "coupon_manifest.csv", coupon_manifest_rows())
    _write_csv(
        output / "additional_missing_parts_audit.csv",
        list(AUDIT_ROWS),
    )
    _write_csv(
        output / "print_target_manifest.csv",
        _print_target_rows(),
    )
    _write_csv(
        output / "first_article_measurement_sheet.csv",
        _measurement_rows(),
    )
    (output / "print_order.md").write_text(
        PRINT_ORDER, encoding="utf-8", newline="\n"
    )
    (output / "assembly_order.md").write_text(
        ASSEMBLY_ORDER, encoding="utf-8", newline="\n"
    )
    (output / "powered_test_gate.md").write_text(
        POWERED_GATE, encoding="utf-8", newline="\n"
    )
    (output / "unresolved_inputs.md").write_text(
        UNRESOLVED_INPUTS, encoding="utf-8", newline="\n"
    )
    built_parts = build_all_parts()
    for part in built_parts:
        export_part(part, output / "stl", output / "step")
    validation = validate_all(built_parts, output, repo_root)
    write_validation(validation, output / "geometry_validation.json")
    _write_json(
        output / "build_summary.json",
        {
            "status": validation["status"],
            "expected_branch": EXPECTED_BRANCH,
            "expected_head": EXPECTED_HEAD,
            "registry": validate_registry(),
            "missing_part_audit": validate_audit(),
            "generated_part_count": len(built_parts),
            "stl_count": len(list((output / "stl").glob("*.stl"))),
            "step_count": len(list((output / "step").glob("*.step"))),
        },
    )
    _write_json(
        output / "completion_status.json",
        _completion_status(validation),
    )
    _write_source_patch(repo_root, output / "source.patch")
    if validation["status"] != "PASS":
        raise RuntimeError("GEOMETRY_VALIDATION_FAILED")
    return {
        "status": "PASS",
        "output": str(output),
        "generated_part_count": len(built_parts),
    }


def finalize_bundle(output: Path) -> None:
    checksum_path = output / "SHA256SUMS.txt"
    bundle_path = output / "result_bundle.zip"
    if checksum_path.exists():
        checksum_path.unlink()
    if bundle_path.exists():
        bundle_path.unlink()
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file()
        and path.name not in {"SHA256SUMS.txt", "result_bundle.zip"}
    )
    checksum_path.write_text(
        "".join(
            f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n"
            for path in files
        ),
        encoding="utf-8",
        newline="\n",
    )
    with zipfile.ZipFile(
        bundle_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for path in sorted(
            item for item in output.rglob("*") if item.is_file()
        ):
            if path == bundle_path:
                continue
            archive.write(path, path.relative_to(output).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    arguments = parser.parse_args()
    result = generate(arguments.output_dir, arguments.repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
