from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3if import (
    FULL_PRINT_STATUS,
    LEGACY_LOCAL_MINUS_X_FIXING_INTERFACE,
    MODULE_FRAME_BOSS_ADDED,
    build_integrated_stage_full_direct_drop_phase3if,
    geometry_audit_phase3if,
)


AUDIT = geometry_audit_phase3if()


def test_phase3if_full_one_solid():
    assert len(build_integrated_stage_full_direct_drop_phase3if().solids().vals()) == 1


def test_phase3if_full_valid():
    assert build_integrated_stage_full_direct_drop_phase3if().val().isValid()


def test_phase3if_full_xy_envelope():
    assert AUDIT["maximum_xy_diameter_mm"] <= 238.0


def test_phase3if_no_module_frame_boss():
    assert MODULE_FRAME_BOSS_ADDED is False


def test_phase3if_legacy_fixing_excluded():
    assert LEGACY_LOCAL_MINUS_X_FIXING_INTERFACE == "SUPERSEDED_BY_NON_ROTATING_DRY_CORE_FRAME"


def test_phase3if_no_wet_wall_penetration():
    assert AUDIT["wet_wall_penetration_added"] is False


def test_phase3if_water_volume_stays_above_minimum():
    assert AUDIT["actual_water_volume"]["actual_retained_volume_l"] >= 0.35


def test_phase3if_full_print_prohibited():
    assert FULL_PRINT_STATUS == "SLICER_REVIEW_ONLY_DO_NOT_PRINT"

