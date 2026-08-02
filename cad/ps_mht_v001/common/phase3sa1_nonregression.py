"""Phase 1 through Phase 3S-A artifact non-regression audit."""

from __future__ import annotations

import json
from pathlib import Path

from ps_mht_v001.common.phase3sa_nonregression import (
    audit_phase1_through_phase3r1,
)
from ps_mht_v001.common.phase_baseline import file_sha256


PHASE3SA_SHA256 = json.loads(
    Path(__file__).with_name("phase3sa_baseline.json").read_text(
        encoding="utf-8"
    )
)


def audit_phase1_through_phase3sa(
    export_root: Path,
) -> dict[str, dict[str, object]]:
    report = audit_phase1_through_phase3r1(export_root)
    actual = {
        relative: file_sha256(export_root / relative)
        for relative in PHASE3SA_SHA256
    }
    report["phase3sa"] = {
        "expected": PHASE3SA_SHA256,
        "actual": actual,
        "unchanged": actual == PHASE3SA_SHA256,
    }
    return report
