"""Phase 3I-C frozen artifact and no-Git regression tests (7)."""

import json
from pathlib import Path

from ps_mht_v001.common.phase3ic_nonregression import audit_phase3ic_nonregression


PACKAGE_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def _audit() -> dict[str, object]:
    return audit_phase3ic_nonregression(REPOSITORY_ROOT, EXPORT_ROOT)


def test_phase3ic_phase3ib_46_artifacts_are_frozen() -> None:
    audit = _audit()["phase3ib_frozen_artifacts"]
    assert audit["official_artifact_count"] == 46
    assert audit["unchanged"]


def test_phase3ic_phase3ia_artifacts_are_unchanged() -> None:
    assert _audit()["phase3ia_artifacts"]["unchanged"]


def test_phase3ic_phase3h_artifacts_are_unchanged() -> None:
    assert _audit()["phase3h_exports"]["unchanged"]


def test_phase3ic_phase3pa_artifacts_are_unchanged() -> None:
    assert _audit()["phase3pa_netpot_calibration_exports"]["unchanged"]


def test_phase3ic_linked_sump_artifacts_are_unchanged() -> None:
    assert _audit()["linked_sump"]["unchanged"]


def test_phase3ic_all_inherited_nonregression_is_true() -> None:
    assert _audit()["all_unchanged"]


def test_phase3ic_report_records_no_git_mutation() -> None:
    report = json.loads((EXPORT_ROOT / "preview" / "phase3ic_validation_report.json").read_text(encoding="utf-8"))
    assert report["git"]["mutation_operations_performed"] is False
    assert report["git"]["prohibited_commands_executed"] == []

