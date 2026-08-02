"""Phase 1 through Phase 3R.1 artifact non-regression audit."""

from __future__ import annotations

import json
from pathlib import Path

from ps_mht_v001.common.phase_baseline import (
    audit_baseline_hashes,
    file_sha256,
)


PHASE3R1_SHA256 = json.loads(
    Path(__file__).with_name("phase3r1_baseline.json").read_text(
        encoding="utf-8"
    )
)


def audit_phase1_through_phase3r1(
    export_root: Path,
) -> dict[str, dict[str, object]]:
    report = audit_baseline_hashes(export_root)
    actual = {
        relative: file_sha256(export_root / relative)
        for relative in PHASE3R1_SHA256
    }
    report["phase3r1"] = {
        "expected": PHASE3R1_SHA256,
        "actual": actual,
        "unchanged": actual == PHASE3R1_SHA256,
    }
    return report


def phase3r2_generated_artifacts(export_root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(export_root).as_posix()
            for path in export_root.rglob("*")
            if path.is_file() and "phase3r2" in path.name.lower()
        )
    )
