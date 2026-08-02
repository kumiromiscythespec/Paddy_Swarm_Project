"""Phase 3H-A arc-coupon and compression-fixture tests (6)."""

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.coupons.horizontal_joint_arc_coupon_phase3ha import (
    arc_coupon_requirements_phase3ha,
    build_horizontal_joint_arc_coupon_phase3ha,
    horizontal_joint_arc_parts_phase3ha,
)
from ps_mht_v001.test_fixtures.horizontal_joint_compression_fixture_phase3ha import (
    build_horizontal_joint_compression_ring_phase3ha,
    compression_fixture_requirements_phase3ha,
)
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    horizontal_joint_requirements_phase3ha,
)


def test_phase3ha_c030_c050_c070_are_distinct_dimple_identified_outputs() -> None:
    requirements = [
        arc_coupon_requirements_phase3ha(value) for value in (0.3, 0.5, 0.7)
    ]
    assert [item["file_token"] for item in requirements] == [
        "c030",
        "c050",
        "c070",
    ]
    assert [item["dimple_count"] for item in requirements] == [1, 2, 3]


def test_phase3ha_each_arc_part_is_one_valid_a1_solid() -> None:
    for clearance in (0.3, 0.5, 0.7):
        pair = measure_shape(build_horizontal_joint_arc_coupon_phase3ha(clearance))
        assert pair.solid_count == 2 and pair.all_solids_valid
        assert pair.size_x <= 245.0 and pair.size_y <= 245.0 and pair.size_z <= 240.0
        for part in horizontal_joint_arc_parts_phase3ha(clearance):
            metrics = measure_shape(part)
            assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3ha_compression_fixture_is_below_240_mm() -> None:
    metrics = measure_shape(build_horizontal_joint_compression_ring_phase3ha())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert max(metrics.size_x, metrics.size_y) <= 240.0


def test_phase3ha_m4_axes_remain_outside_root_and_body_envelopes() -> None:
    requirements = compression_fixture_requirements_phase3ha()
    assert requirements["m4_outside_root_envelope"] is True
    assert requirements["m4_outside_200mm_body"] is True


def test_phase3ha_has_no_small_joint_or_fixture_parts() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)["small_part_count"] == 0
    fixture = compression_fixture_requirements_phase3ha()
    assert fixture["small_nut_cartridge_count"] == 0
    assert fixture["small_gate_count"] == 0


def test_phase3ha_has_zero_planting_ports_and_buffer_trays() -> None:
    requirements = horizontal_joint_requirements_phase3ha(0.5)
    assert requirements["port_count"] == 0
    assert requirements["buffer_tray_count"] == 0
