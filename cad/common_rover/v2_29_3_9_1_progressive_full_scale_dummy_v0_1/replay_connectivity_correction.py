from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from final_gate_contract import (
    compare_connectivity_core_outputs,
    compare_existing_stls,
)
from generate_connectivity_correction import generate
from part_number_registry import ALL_PARTS


def replay(
    baseline_artifact: Path,
    *,
    reference_artifact: Path | None = None,
) -> dict:
    baseline = baseline_artifact.resolve()
    with tempfile.TemporaryDirectory(
        prefix="pfd_connectivity_core_first_"
    ) as first_temporary, tempfile.TemporaryDirectory(
        prefix="pfd_connectivity_core_second_"
    ) as second_temporary:
        first = Path(first_temporary) / "artifact"
        second = Path(second_temporary) / "artifact"
        generate(first, baseline)
        generate(second, baseline)
        report = compare_connectivity_core_outputs(first, second)
        report["baseline_artifact"] = str(baseline)
        report["first_generator"] = (
            "generate_connectivity_correction.generate"
        )
        report["second_generator"] = (
            "generate_connectivity_correction.generate"
        )
        if reference_artifact is not None:
            identity = compare_existing_stls(
                reference_artifact,
                first,
                tuple(part.filename for part in ALL_PARTS),
            )
            report["existing_33_stl_identity"] = identity
            if identity["EXISTING_33_STL_BYTE_IDENTITY"] != "PASS":
                report["blockers"] = sorted(
                    set(report["blockers"] + identity["blockers"])
                )
                report["CONNECTIVITY_CORE_DETERMINISTIC_REPLAY"] = "FAIL"
        return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-artifact-dir",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--reference-artifact-dir",
        type=Path,
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = replay(
        args.baseline_artifact_dir,
        reference_artifact=args.reference_artifact_dir,
    )
    text = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "CONNECTIVITY_CORE_DETERMINISTIC_REPLAY": report[
                    "CONNECTIVITY_CORE_DETERMINISTIC_REPLAY"
                ],
                "CONNECTIVITY_CORE_OUTPUT_COUNT": report[
                    "CONNECTIVITY_CORE_OUTPUT_COUNT"
                ],
                "DETERMINISTIC_CORE_FILE_SET_MATCH": report[
                    "DETERMINISTIC_CORE_FILE_SET_MATCH"
                ],
                "DETERMINISTIC_MISMATCH_COUNT": report[
                    "DETERMINISTIC_MISMATCH_COUNT"
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        end="",
    )
    return (
        0
        if report["CONNECTIVITY_CORE_DETERMINISTIC_REPLAY"] == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
