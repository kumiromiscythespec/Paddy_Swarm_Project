"""Phase 3S-A chord-down transform, envelope, and stability gates."""

from __future__ import annotations

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    COORDINATE_TRANSFORM,
    orient_sector_for_print_phase3sa,
    print_stability_metrics_phase3sa,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    phase3sa_max_print_overhang,
    phase3sa_panel_height,
    phase3sa_print_height_audit_limit,
    phase3sa_print_height_target,
    print_bed_x,
    print_bed_y,
    print_bed_z,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_sector_panel_phase3sa,
)


def _printed_panel():
    return orient_sector_for_print_phase3sa(
        build_sector_panel_phase3sa(0.6)
    )


def test_coordinate_transform_places_assembly_height_in_print_y() -> None:
    assert COORDINATE_TRANSFORM["assembly_Z"] == "print_Y"
    assert COORDINATE_TRANSFORM[
        "assembly_radial_outward_X"
    ] == "print_Z"
    metrics = measure_shape(_printed_panel())
    assert abs(metrics.size_y - phase3sa_panel_height) < 1.0e-6


def test_chord_rail_plane_lands_at_print_z_zero() -> None:
    box = _printed_panel().val().BoundingBox()
    assert abs(box.zmin) < 1.0e-6
    assert COORDINATE_TRANSFORM["panel_chord_plane"] == "print_Z=0"


def test_actual_print_height_meets_target_and_stop_limit() -> None:
    height = measure_shape(_printed_panel()).size_z
    assert height <= phase3sa_print_height_target
    assert height <= phase3sa_print_height_audit_limit


def test_full_height_panel_print_orientation_fits_a1() -> None:
    metrics = measure_shape(_printed_panel())
    assert metrics.size_x <= print_bed_x
    assert metrics.size_y <= print_bed_y
    assert metrics.size_z <= print_bed_z


def test_center_of_mass_projection_is_inside_support_polygon() -> None:
    metrics = print_stability_metrics_phase3sa(
        build_sector_panel_phase3sa(0.6)
    )
    assert metrics["center_projection_inside_support_polygon"]
    assert metrics["support_polygon_margin_mm"] > 0.0


def test_split_panel_stability_index_exceeds_old_vertical_coupon() -> None:
    metrics = print_stability_metrics_phase3sa(
        build_sector_panel_phase3sa(0.6)
    )
    old_coupon_tip_index = 100.0 / 70.0
    assert metrics["tip_stability_index"] > old_coupon_tip_index


def test_port_print_overhang_is_at_most_45_degrees() -> None:
    assert phase3sa_max_print_overhang <= 45.0
