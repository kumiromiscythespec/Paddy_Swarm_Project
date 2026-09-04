"""Frozen Phase 3I-B plus inherited Phase 3I-A/3H/3P-A/linked SHA audit."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase3hb_nonregression import file_sha256
from ps_mht_v001.common.phase3ib_nonregression import audit_phase3ib_nonregression


PHASE3IB_SHA_LIST_SHA256 = "093917ea7e66de86ce1ac437352596a80c39edd97ec6426a7d79b519858de495"


def _phase3ib_artifact_audit(repository_root: Path) -> dict[str, object]:
    sha_path = repository_root / "cad/ps_mht_v001/commit/phase3ib_SHA256SUMS.txt"
    entries: dict[str, str] = {}
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        entries[relative] = expected
    actual = {relative: file_sha256(repository_root / relative) for relative in entries}
    list_actual = file_sha256(sha_path)
    return {
        "status": "HISTORICAL_FAILED_BASELINE_FROZEN",
        "artifact_count_from_sha_list": len(entries),
        "sha_list_file_count": 1,
        "official_artifact_count": len(entries) + 1,
        "expected": entries,
        "actual": actual,
        "sha_list_expected_sha256": PHASE3IB_SHA_LIST_SHA256,
        "sha_list_actual_sha256": list_actual,
        "unchanged": actual == entries and list_actual == PHASE3IB_SHA_LIST_SHA256,
    }


def audit_phase3ic_nonregression(repository_root: Path, export_root: Path) -> dict[str, object]:
    inherited = audit_phase3ib_nonregression(repository_root, export_root)
    phase3ib = _phase3ib_artifact_audit(repository_root)
    return {
        "phase3ib_frozen_artifacts": phase3ib,
        "phase3ia_artifacts": inherited["phase3ia_artifacts"],
        "phase3h_exports": inherited["phase3h_exports"],
        "phase3pa_netpot_calibration_exports": inherited["phase3pa_netpot_calibration_exports"],
        "authoritative_sources": inherited["authoritative_sources"],
        "linked_sump": inherited["linked_sump"],
        "all_unchanged": phase3ib["unchanged"] and inherited["all_unchanged"],
    }

