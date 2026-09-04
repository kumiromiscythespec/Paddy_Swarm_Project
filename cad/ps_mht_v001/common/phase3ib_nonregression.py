"""Phase 3I-A plus inherited Phase 3H/3P-A/linked SHA audit."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase3hb_nonregression import file_sha256
from ps_mht_v001.common.phase3ia_nonregression import audit_phase3ia_nonregression


PHASE3IA_SHA_LIST_SHA256 = "75e95607222458eedd2db234b5d0cbe9f56b54992a49e87d40d6922c2153b54e"


def _phase3ia_artifact_audit(repository_root: Path) -> dict[str, object]:
    sha_path = repository_root / "cad/ps_mht_v001/commit/phase3ia_SHA256SUMS.txt"
    entries: dict[str, str] = {}
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        entries[relative] = expected
    actual = {relative: file_sha256(repository_root / relative) for relative in entries}
    list_actual = file_sha256(sha_path)
    return {
        "artifact_count_from_sha_list": len(entries),
        "sha_list_file_count": 1,
        "total_phase3ia_artifact_count": len(entries) + 1,
        "expected": entries,
        "actual": actual,
        "sha_list_expected_sha256": PHASE3IA_SHA_LIST_SHA256,
        "sha_list_actual_sha256": list_actual,
        "unchanged": actual == entries and list_actual == PHASE3IA_SHA_LIST_SHA256,
    }


def audit_phase3ib_nonregression(repository_root: Path, export_root: Path) -> dict[str, object]:
    inherited = audit_phase3ia_nonregression(repository_root, export_root)
    phase3ia = _phase3ia_artifact_audit(repository_root)
    return {
        "phase3ia_artifacts": phase3ia,
        "phase3h_exports": inherited["phase3h_exports"],
        "phase3pa_netpot_calibration_exports": inherited["phase3pa_netpot_calibration_exports"],
        "authoritative_sources": inherited["authoritative_sources"],
        "linked_sump": inherited["linked_sump"],
        "all_unchanged": phase3ia["unchanged"] and inherited["all_unchanged"],
    }

