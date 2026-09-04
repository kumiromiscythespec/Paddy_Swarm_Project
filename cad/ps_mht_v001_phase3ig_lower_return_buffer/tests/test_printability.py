import pytest

from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import (
    A1_X_MM, A1_Y_MM, A1_Z_MM, DIAGNOSTIC_BUILDERS, printability_audit_phase3ig,
)


@pytest.mark.parametrize("name,builder", DIAGNOSTIC_BUILDERS.items())
def test_each_diagnostic_fits_a1(name, builder):
    b = builder().val().BoundingBox()
    assert b.xlen <= A1_X_MM and b.ylen <= A1_Y_MM and b.zlen <= A1_Z_MM, name


def test_no_inaccessible_support_cavity():
    a = printability_audit_phase3ig()
    assert not a["supports_trapped_inside_tank"]
    assert not a["unsupported_internal_roof_present"]


def test_bridges_are_flagged_for_slicer_review():
    assert len(printability_audit_phase3ig()["bridges_requiring_slicer_review"]) == 2


def test_no_long_external_nipple():
    assert not printability_audit_phase3ig()["long_external_nipple_present"]


def test_full_models_remain_hold():
    a = printability_audit_phase3ig()
    assert a["full_tank"].startswith("HOLD")
    assert a["full_tray"].startswith("HOLD")
    assert a["full_assembly"].startswith("HOLD")
    assert a["phase3if_full_stage"] == "DO_NOT_PRINT"

