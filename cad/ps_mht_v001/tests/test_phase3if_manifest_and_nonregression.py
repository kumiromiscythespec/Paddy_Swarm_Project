from pathlib import Path

from ps_mht_v001.common.phase3if_nonregression import audit_phase3if_nonregression
from ps_mht_v001.print_manifest_phase3if import build_print_manifest_phase3if


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "cad/ps_mht_v001"
NONREG = audit_phase3if_nonregression(ROOT, PACKAGE / "exports")
MANIFEST = build_print_manifest_phase3if()


def test_phase3if_phase3id_sha_unchanged():
    assert NONREG["phase3id_frozen_artifacts"]["unchanged"]


def test_phase3if_all_inherited_sha_unchanged():
    assert NONREG["all_unchanged"]


def test_phase3if_fit_coupon_prints_first():
    assert MANIFEST["plates"][0]["status"] == "READY_FIRST_LOW_COST_FIT_TEST"


def test_phase3if_puck_and_cap_held():
    assert MANIFEST["plates"][1]["print"] is False
    assert MANIFEST["plates"][2]["print"] is False


def test_phase3if_full_do_not_print():
    assert MANIFEST["plates"][3]["status"] == "SLICER_REVIEW_ONLY_DO_NOT_PRINT"


def test_phase3if_sixty_partial_excluded():
    assert MANIFEST["historical"]["phase3ie_60deg"] == "ABORTED_PARTIAL_SOURCE_NOT_FOR_ZIP"

