"""Phase 3H-B SHA, test-accounting, and no-Git tests (5)."""

import json
from pathlib import Path

from ps_mht_v001.common.phase3hb_nonregression import (
    audit_linked_sump_phase4tlsa,
    audit_phase3ha_exports,
)


PACKAGE_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"
PREVIEW_ROOT = EXPORT_ROOT / "preview"


def _report() -> dict[str, object]:
    return json.loads(
        (PREVIEW_ROOT / "phase3hb_validation_report.json").read_text(encoding="utf-8")
    )


def test_phase3hb_phase3ha_export_sha_is_unchanged() -> None:
    audit = audit_phase3ha_exports(EXPORT_ROOT)
    assert audit["unchanged"] and audit["artifact_count"] == 16


def test_phase3hb_linked_sump_sha_is_unchanged() -> None:
    audit = audit_linked_sump_phase4tlsa(REPOSITORY_ROOT)
    assert audit["unchanged"] and audit["artifact_count_in_manifest"] == 52


def test_phase3hb_report_records_all_existing_tests_passed() -> None:
    tests = _report()["automated_tests"]
    assert tests["existing_ps_mht"] == 334
    assert tests["linked_sump"] == 40
    assert tests["existing_all_passed"] is True


def test_phase3hb_report_records_exactly_32_new_tests_passed() -> None:
    tests = _report()["automated_tests"]
    assert tests["new_phase3hb"] == 32
    assert tests["total_passed"] == 406
    assert tests["all_passed"] is True


def test_phase3hb_report_records_no_git_mutation() -> None:
    git = _report()["git"]
    assert git["mutation_operations_performed"] is False
    assert git["prohibited_commands_executed"] == []
