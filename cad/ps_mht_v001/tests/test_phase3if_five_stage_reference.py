from ps_mht_v001.reference.dry_core_frame_references_phase3if import (
    STAGE_ABSOLUTE_ROTATIONS_DEG,
    build_all_interstage_drop_corridors_phase3if,
    build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if,
    five_stage_dry_core_collision_audit_phase3if,
    five_stage_reference_metadata_phase3if,
)


AUDIT = five_stage_dry_core_collision_audit_phase3if()
META = five_stage_reference_metadata_phase3if()


def test_phase3if_five_stage_rotations():
    assert STAGE_ABSOLUTE_ROTATIONS_DEG == (0.0, 30.0, 60.0, 90.0, 120.0)


def test_phase3if_twelve_drop_corridors():
    assert len(build_all_interstage_drop_corridors_phase3if().solids().vals()) == 12


def test_phase3if_stage_contacts_have_zero_intersection_volume():
    assert AUDIT["stage_pair_intersections_mm3"] == [0, 0, 0, 0]


def test_phase3if_frame_intersections_all_zero():
    assert AUDIT["all_unintended_intersections_zero"]


def test_phase3if_mast_corridor_clear():
    assert AUDIT["intersections_mm3"]["drop_corridors_vs_central_mast"] == 0


def test_phase3if_mast_pot_and_root_clear():
    assert AUDIT["intersections_mm3"]["central_mast_vs_netpots"] == 0
    assert AUDIT["intersections_mm3"]["central_mast_vs_root_assumed_region"] == 0


def test_phase3if_puck_and_cap_stay_dry():
    assert AUDIT["intersections_mm3"]["bottom_puck_vs_water"] == 0
    assert AUDIT["intersections_mm3"]["top_cap_vs_water"] == 0


def test_phase3if_rear_post_and_brackets_clear_pots():
    assert AUDIT["intersections_mm3"]["rear_post_vs_netpots"] == 0
    assert AUDIT["intersections_mm3"]["lower_bracket_vs_netpots"] == 0
    assert AUDIT["intersections_mm3"]["upper_bracket_vs_netpots"] == 0


def test_phase3if_tolerance_frame_margin():
    assert AUDIT["minimum_tolerance_radial_margin_to_frame_mm"] == 18.0


def test_phase3if_upward_disassembly_requires_removals():
    assert AUDIT["upward_disassembly"] == "PASS_AFTER_REMOVING_TOP_BRACKET_AND_TOP_CAP"


def test_phase3if_reference_contains_five_stages():
    assert META["stage_count"] == 5
    assert len(build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if().solids().vals()) == META["solid_count"]


def test_phase3if_port_absolute_angles():
    assert META["plant_port_absolute_angles_deg"][3] == [90.0, 210.0, 330.0]

