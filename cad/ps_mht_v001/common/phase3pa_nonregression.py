"""Phase 1 through Phase 3S-A.2 artifact non-regression audit."""

from __future__ import annotations

import json
from pathlib import Path

from ps_mht_v001.common.phase3sa2_nonregression import (
    audit_phase1_through_phase3sa1,
)
from ps_mht_v001.common.phase_baseline import file_sha256


PHASE3SA2_SHA256 = json.loads(
    Path(__file__).with_name(
        "phase3pa_phase3sa2_baseline.json"
    ).read_text(
        encoding="utf-8"
    )
)


def audit_phase1_through_phase3sa2(
    export_root: Path,
) -> dict[str, dict[str, object]]:
    report = audit_phase1_through_phase3sa1(export_root)
    actual = {
        relative: file_sha256(export_root / relative)
        for relative in PHASE3SA2_SHA256
    }
    report["phase3sa2"] = {
        "expected": PHASE3SA2_SHA256,
        "actual": actual,
        "unchanged": actual == PHASE3SA2_SHA256,
    }
    return report
