from ps_mht_v001.reference.direct_drop_references_phase3ie import drop_corridor_collision_audit_phase3ie
from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    LANDING_ANGLES_LOCAL_DEG,
    LANDING_EFFECTIVE_CAPTURE_WIDTH_MM,
    LANDING_RAMP_TANGENTIAL_WIDTH_MM,
    OVERFLOW_ANGLES_LOCAL_DEG,
    correct_wrong_alignment_audit_phase3ie,
    landing_zone_audit_phase3ie,
    rotation_rule_audit_phase3ie,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ie import actual_water_volume_audit_phase3ie


COLLISION = drop_corridor_collision_audit_phase3ie()


def test_phase3if_overflow_angles_preserved():
    assert OVERFLOW_ANGLES_LOCAL_DEG == (30.0, 150.0, 270.0)


def test_phase3if_landing_angles_corrected():
    assert LANDING_ANGLES_LOCAL_DEG == (60.0, 180.0, 300.0)


def test_phase3if_rotation_contract():
    assert rotation_rule_audit_phase3ie()["contract"] == "RELATIVE_ROTATION_MOD_120_EQUALS_30"


def test_phase3if_sixty_rejected():
    assert 60.0 in rotation_rule_audit_phase3ie()["rejected_relative_angles_deg"]


def test_phase3if_correct_alignment_is_30():
    audit = correct_wrong_alignment_audit_phase3ie()
    assert audit["correct_rotation_deg"] == 30.0
    assert audit["correct_all_three_aligned"]


def test_phase3if_wrong_zero_not_aligned():
    assert correct_wrong_alignment_audit_phase3ie()["wrong_aligned_count"] == 0


def test_phase3if_drop_corridors_clear_all_obstacles():
    assert COLLISION["all_unintended_intersections_zero"]


def test_phase3if_drop_corridor_central_hole_clear():
    assert COLLISION["central_hole_intersection_mm3"] == 0


def test_phase3if_main_ramp_width_and_capture_shoulders():
    assert 28.0 <= LANDING_RAMP_TANGENTIAL_WIDTH_MM <= 30.0
    assert LANDING_EFFECTIVE_CAPTURE_WIDTH_MM == 32.0


def test_phase3if_tolerance_capture_passes():
    audit = landing_zone_audit_phase3ie()
    assert audit["all_cases_contained"]
    assert audit["tangential_capture_margin_mm"] > 0


def test_phase3if_retained_water_volume():
    audit = actual_water_volume_audit_phase3ie()
    assert audit["within_target_range"]
    assert audit["water_surface_z_mm"] == 26.0

