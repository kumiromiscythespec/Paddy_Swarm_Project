from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import geometry_audit_phase3ig


def _audit():
    return geometry_audit_phase3ig()


def test_actual_phase3if_components_have_zero_intersection():
    assert _audit()["all_inherited_actual_component_intersections_zero"]


def test_tank_and_downcomer_clear_measured_mast():
    values = _audit()["inherited_actual_component_intersections_mm3"]
    assert values["tank_vs_measured_mast_reference"] == 0
    assert values["downcomer_vs_measured_mast_reference"] == 0


def test_tray_clears_mast_puck_pots_and_keepers():
    values = _audit()["inherited_actual_component_intersections_mm3"]
    for key in ("tray_vs_measured_mast_reference", "tray_vs_actual_bottom_puck",
                "tray_vs_actual_netpots", "tray_vs_actual_retention_keepers"):
        assert values[key] == 0


def test_tank_clears_radial_legs():
    assert _audit()["intersections_mm3"]["tank_vs_radial_legs"] == 0


def test_tank_removal_path_is_clear_after_required_disassembly():
    assert _audit()["removal_path"]["path_clear_after_required_disassembly"]


def test_removal_sequence_does_not_claim_tray_can_stay_installed():
    removal = _audit()["removal_path"]
    assert "REMOVE_TRAY_AND_DOWNCOMER" in removal["required_sequence"]
    assert removal["positions"]["lifted_110mm_after_tray_removal"]["tray_mm3_if_tray_not_removed"] > 0


def test_diffuser_downcomer_interface_is_clear_and_removable():
    audit = _audit()
    assert audit["intersections_mm3"]["diffuser_vs_downcomer"] == 0
    assert any("0P3MM_RADIAL_CLEARANCE" in item for item in audit["intended_contacts"])


def test_printed_parts_are_not_primary_load_path():
    audit = _audit()
    assert not audit["printed_parts_primary_load_path"]
    assert "METAL" in audit["primary_load_path"]
