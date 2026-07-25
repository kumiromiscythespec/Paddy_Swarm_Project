from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_contract import (
    BASE_HEAD,
    EXPECTED_TRACKED_STEP_STP_COUNT,
    EXPECTED_TRACKED_STL_COUNT,
    repository_root,
)
from canonical_inventory import (
    build_inventory,
    validate_inventory_bundle,
    write_inventory_bundle,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repository_root(args.repository_root)
    output = args.output_dir.resolve()
    if output == root or root in output.parents:
        raise ValueError("INVENTORY_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    inventory = build_inventory(root, base_head=BASE_HEAD)
    if inventory["TRACKED_STL_COUNT"] != EXPECTED_TRACKED_STL_COUNT:
        raise ValueError("BASELINE_TRACKED_STL_COUNT_MISMATCH")
    if (
        inventory["TRACKED_STEP_STP_COUNT"]
        != EXPECTED_TRACKED_STEP_STP_COUNT
    ):
        raise ValueError("BASELINE_TRACKED_STEP_STP_COUNT_MISMATCH")
    write_inventory_bundle(inventory, output)
    validation = validate_inventory_bundle(
        output / "baseline_tracked_cad_inventory.json",
        output / "baseline_tracked_cad_inventory.csv",
        output / "baseline_tracked_cad_inventory.sha256",
    )
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
