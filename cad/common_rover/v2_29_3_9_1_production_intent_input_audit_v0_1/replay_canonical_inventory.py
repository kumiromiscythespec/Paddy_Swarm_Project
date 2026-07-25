from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical_inventory import (
    replay_inventory,
    replay_text,
    validate_inventory_bundle,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    directory = args.artifact_dir.resolve()
    json_path = directory / "baseline_tracked_cad_inventory.json"
    csv_path = directory / "baseline_tracked_cad_inventory.csv"
    receipt_path = directory / "baseline_tracked_cad_inventory.sha256"
    validate_inventory_bundle(json_path, csv_path, receipt_path)
    inventory = json.loads(json_path.read_text(encoding="utf-8"))
    report = replay_inventory(
        inventory["records"],
        recorded_sha256=inventory["inventory_sha256"],
    )
    (directory / "canonical_inventory_hash_replay.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (directory / "canonical_inventory_hash_replay.txt").write_text(
        replay_text(report),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(
        report[key]
        for key in (
            "match",
            "shuffled_replay_match",
            "reversed_replay_match",
        )
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
