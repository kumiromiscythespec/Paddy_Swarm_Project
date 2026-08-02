"""Measured flange versus existing ring, M4, tool and root-ring envelopes."""

from ps_mht_v001.audit.port_fastener_envelope_audit_phase3pa import (
    port_fastener_envelope_audit_phase3pa,
)
from ps_mht_v001.audit.port_function_ring_audit_phase3pa import (
    port_function_ring_audit_phase3pa,
)


def test_phase3pa_existing_m4_envelopes_are_reaudited() -> None:
    audit = port_fastener_envelope_audit_phase3pa()
    assert audit["flange_radius_mm"] == 54.0
    assert audit["existing_m4_axis_radius_mm"] == 50.0
    assert all(audit["intersects_measured_flange_projection"].values())


def test_phase3pa_installed_pot_blocks_tool_and_finger_access() -> None:
    audit = port_fastener_envelope_audit_phase3pa()
    assert audit["tool_access_with_pot_installed"] is False
    assert audit["finger_access_with_pot_installed"] is False
    assert audit["fastening_without_removing_pot"] is False
    assert audit["fastening_with_pot_removed"] is True


def test_phase3pa_existing_ring_is_not_forced_to_pass() -> None:
    audit = port_function_ring_audit_phase3pa()
    assert audit["status"] == "REDESIGN_REQUIRED"
    assert audit["m4_fastener"]["status"] == "FAIL_FASTENER_INTERFERENCE"
    assert audit["tool_envelope"]["status"] == "FAIL_TOOL_ENVELOPE"


def test_phase3pa_existing_ring_supports_flange_only_as_reference() -> None:
    seating = port_function_ring_audit_phase3pa()["flange_seating"]
    assert seating["flange_support_radial_width_mm"] == 12.0
    assert seating["ring_outside_flange_radial_width_mm"] == 4.0
    assert seating["continuous_support_interrupted_by_existing_m4_holes"]


def test_phase3pa_backing_and_root_ring_are_separately_audited() -> None:
    audit = port_function_ring_audit_phase3pa()
    assert audit["backing_ring"]["status"] == "PASS_AS_REFERENCE"
    assert audit["root_sleeve_ring"]["status"] == "REDESIGN_REQUIRED"
    assert audit["panel_opening"]["axis_angle_deg"] == 27.0
    assert audit["panel_opening"]["seated_pot_shell_intersection_volume_mm3"] > 0.0
    assert audit["panel_opening"]["status"] == (
        "REDESIGN_REQUIRED_SHELL_INTERFERENCE"
    )
    assert audit["maximum_diameter"]["status"] == "FAIL_MAXIMUM_DIAMETER"
