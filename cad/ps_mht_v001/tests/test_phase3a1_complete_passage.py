"""Corrected common passage and complete one-axis assembly tests."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.complete_port_assembly_phase3a1 import (
    COMPLETE_ASSEMBLY_SOLID_COUNT,
    build_complete_port_assembly_phase3a1,
    complete_port_interference_report,
    netpot_bottom_z,
    passage_interference_report,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.tower_module.netpot_60_adapter import (
    OPERATION,
    REMOVAL,
    RETENTION_POLICY,
    ROTATION_POLICY,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_common_adapter_full_length_passage_probe,
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.port_adapter_retainer import STATUS


INTERFERENCE = complete_port_interference_report()


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_common_adapter_center_is_open_for_its_full_length() -> None:
    adapter = build_planting_port_adapter()
    probe = build_common_adapter_full_length_passage_probe()
    assert abs(probe.val().BoundingBox().xlen - 66.0) <= 1.0e-7
    assert _volume(adapter.intersect(probe)) <= 1.0e-8


def test_common_adapter_flange_has_actual_center_opening() -> None:
    adapter = build_planting_port_adapter()
    flange_probe = (
        build_common_adapter_full_length_passage_probe()
        .intersect(
            cq.Workplane("XY")
            .circle(30.0)
            .extrude(2.0)
            .translate((0.0, 0.0, 10.0))
        )
    )
    assert _volume(adapter.intersect(flange_probe)) <= 1.0e-8


def test_real_netpot_has_no_common_adapter_or_liner_interference() -> None:
    assert INTERFERENCE["netpot_to_common_adapter_mm3"] <= 1.0e-8
    assert INTERFERENCE["netpot_to_netpot_adapter_mm3"] <= 1.0e-8


def test_netpot_bottom_reaches_tower_internal_side() -> None:
    assert netpot_bottom_z() < 0.0
    assert netpot_bottom_z() <= -30.0


def test_netpot_liner_assembles_inside_common_adapter() -> None:
    assert INTERFERENCE["netpot_adapter_to_common_adapter_mm3"] <= 1.0e-8


def test_root_ring_reaches_common_adapter_inner_end_without_overlap() -> None:
    assert INTERFERENCE["root_ring_to_common_adapter_mm3"] <= 1.0e-8


def test_folded_root_sleeve_passes_ring_and_common_adapter() -> None:
    assert INTERFERENCE["collapsed_sleeve_to_root_ring_mm3"] <= 1.0e-8
    assert INTERFERENCE["collapsed_sleeve_to_common_adapter_mm3"] <= 1.0e-8


def test_root_stop_insert_can_transit_common_adapter() -> None:
    assert INTERFERENCE["root_stop_transit_to_common_adapter_mm3"] <= 1.0e-8


def test_complete_passage_probe_has_no_structural_closure() -> None:
    assert max(passage_interference_report().values()) <= 1.0e-8


def test_complete_port_assembly_has_expected_valid_solids() -> None:
    metrics = measure_shape(build_complete_port_assembly_phase3a1())
    assert metrics.solid_count == COMPLETE_ASSEMBLY_SOLID_COUNT
    assert metrics.all_solids_valid


def test_old_annular_retainer_is_explicitly_deprecated() -> None:
    assert STATUS == "DEPRECATED_NOT_EXTERNALLY_SERVICEABLE"


def test_netpot_adapter_is_tool_free_gravity_liner_without_snaps() -> None:
    assert OPERATION == "TOOL_FREE_GRAVITY_SEATED_REPLACEABLE_LINER"
    assert REMOVAL == "MAY_WITHDRAW_WITH_PURCHASED_NETPOT"
    assert ROTATION_POLICY == "FREE_ROTATION_FUNCTIONALLY_ACCEPTABLE"
    assert RETENTION_POLICY == "NO_THIN_SNAP_TABS"
