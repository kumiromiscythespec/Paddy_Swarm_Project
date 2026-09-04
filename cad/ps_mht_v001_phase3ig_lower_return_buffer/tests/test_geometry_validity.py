import pytest

from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import (
    DIAGNOSTIC_BUILDERS, build_inlet_diffuser_phase3ig, build_inlet_downcomer_phase3ig,
    build_lower_buffer_tank_phase3ig, build_terminal_collection_tray_phase3ig,
    geometry_audit_phase3ig,
)


@pytest.mark.parametrize("builder", [
    build_lower_buffer_tank_phase3ig, build_terminal_collection_tray_phase3ig,
    build_inlet_downcomer_phase3ig, build_inlet_diffuser_phase3ig,
])
def test_primary_part_is_one_valid_body(builder):
    model = builder()
    assert len(model.solids().vals()) == 1
    assert model.val().isValid()


@pytest.mark.parametrize("name,builder", DIAGNOSTIC_BUILDERS.items())
def test_diagnostic_has_only_valid_positive_solids(name, builder):
    solids = builder().solids().vals()
    assert solids, name
    assert all(s.isValid() and s.Volume() > 0 for s in solids)


def test_no_floating_solid_in_tank_or_tray():
    audit = geometry_audit_phase3ig()
    assert audit["parts"]["tank"]["solid_count"] == 1
    assert audit["parts"]["tray"]["solid_count"] == 1


def test_removable_parts_remain_separate_in_assembly_authority():
    audit = geometry_audit_phase3ig()
    assert audit["parts"]["downcomer"]["solid_count"] == 1
    assert audit["parts"]["diffuser"]["solid_count"] == 1
    assert any("DOWNCOMER_TO_DIFFUSER_CAPTURE_INTERFACE" in item for item in audit["intended_contacts"])
