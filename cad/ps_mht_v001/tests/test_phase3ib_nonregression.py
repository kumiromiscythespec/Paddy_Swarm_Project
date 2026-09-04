"""Phase 3I-B inherited SHA, source, and no-Git tests (7)."""

import json
from pathlib import Path

from ps_mht_v001.common.phase3ib_nonregression import audit_phase3ib_nonregression


PACKAGE_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def _audit() -> dict[str, object]:
    return audit_phase3ib_nonregression(REPOSITORY_ROOT, EXPORT_ROOT)


def test_phase3ib_phase3ia_all_36_artifacts_are_unchanged() -> None:
    audit = _audit()["phase3ia_artifacts"]
    assert audit["total_phase3ia_artifact_count"] == 36
    assert audit["unchanged"]


def test_phase3ib_phase3h_exports_are_unchanged() -> None:
    assert _audit()["phase3h_exports"]["unchanged"]


def test_phase3ib_phase3pa_netpot_exports_are_unchanged() -> None:
    assert _audit()["phase3pa_netpot_calibration_exports"]["unchanged"]


def test_phase3ib_linked_sump_artifacts_are_unchanged() -> None:
    assert _audit()["linked_sump"]["unchanged"]


def test_phase3ib_inherited_authoritative_sources_are_unchanged() -> None:
    assert _audit()["authoritative_sources"]["unchanged"]


def test_phase3ib_nonregression_aggregate_is_true() -> None:
    assert _audit()["all_unchanged"]


def test_phase3ib_report_records_no_git_mutation() -> None:
    report = json.loads((EXPORT_ROOT / "preview" / "phase3ib_validation_report.json").read_text(encoding="utf-8"))
    assert report["git"]["mutation_operations_performed"] is False
    assert report["git"]["prohibited_commands_executed"] == []

