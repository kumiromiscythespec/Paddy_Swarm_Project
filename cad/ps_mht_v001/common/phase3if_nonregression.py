"""Frozen Phase 3I-D and inherited artifact audit for Phase 3I-F."""

from pathlib import Path

from ps_mht_v001.common.phase3hb_nonregression import file_sha256
from ps_mht_v001.common.phase3id_nonregression import audit_phase3id_nonregression


PHASE3ID_SHA_LIST_SHA256 = "f52f611c2b0d639219de8389e4040cff101a7065c81ada39da2fd41d04fbf830"


def _phase3id_artifact_audit(repository_root: Path) -> dict[str, object]:
    sha_path = repository_root / "cad/ps_mht_v001/commit/phase3id_SHA256SUMS.txt"
    entries: dict[str, str] = {}
    for line in sha_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        entries[relative] = expected
    actual = {relative: file_sha256(repository_root / relative) for relative in entries}
    list_actual = file_sha256(sha_path)
    return {
        "status": "FROZEN_SUPERSEDED_CANDIDATE",
        "artifact_count_from_sha_list": len(entries),
        "official_artifact_count": len(entries) + 1,
        "expected": entries,
        "actual": actual,
        "sha_list_expected_sha256": PHASE3ID_SHA_LIST_SHA256,
        "sha_list_actual_sha256": list_actual,
        "unchanged": actual == entries and list_actual == PHASE3ID_SHA_LIST_SHA256,
    }


def audit_phase3if_nonregression(repository_root: Path, export_root: Path) -> dict[str, object]:
    inherited = audit_phase3id_nonregression(repository_root, export_root)
    phase3id = _phase3id_artifact_audit(repository_root)
    return {
        "phase3id_frozen_artifacts": phase3id,
        "phase3ic_frozen_artifacts": inherited["phase3ic_frozen_artifacts"],
        "phase3ib_frozen_artifacts": inherited["phase3ib_frozen_artifacts"],
        "phase3ia_artifacts": inherited["phase3ia_artifacts"],
        "phase3h_exports": inherited["phase3h_exports"],
        "phase3pa_netpot_calibration_exports": inherited["phase3pa_netpot_calibration_exports"],
        "authoritative_sources": inherited["authoritative_sources"],
        "linked_sump": inherited["linked_sump"],
        "all_unchanged": phase3id["unchanged"] and inherited["all_unchanged"],
    }
