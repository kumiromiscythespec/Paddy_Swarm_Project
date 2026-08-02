"""Permanent two-rail contact-area and load-path gates."""

from __future__ import annotations

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    phase3sa_panel_height,
    phase3sa_seam_rail_min_contact_area,
    phase3sa_seam_rail_target_contact_area,
    phase3sa_seam_rail_width,
    phase3sa_seam_root_radius,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_sector_panel_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    RAIL_COUNT,
    build_contact_rails_phase3sa,
    rail_contact_area_phase3sa,
)


def test_two_rails_are_continuous_for_full_panel_height() -> None:
    rails = build_contact_rails_phase3sa()
    metrics = measure_shape(rails)
    assert RAIL_COUNT == 2
    assert metrics.solid_count == 2
    assert abs(metrics.size_z - phase3sa_panel_height) < 1.0e-7


def test_each_rail_has_required_width_and_root_radius() -> None:
    assert 12.0 <= phase3sa_seam_rail_width <= 18.0
    assert phase3sa_seam_root_radius >= 3.0


def test_total_contact_area_exceeds_minimum_and_target() -> None:
    area = rail_contact_area_phase3sa()
    assert area >= phase3sa_seam_rail_min_contact_area
    assert area >= phase3sa_seam_rail_target_contact_area


def test_contact_area_target_margin_is_reportable() -> None:
    difference = (
        rail_contact_area_phase3sa()
        - phase3sa_seam_rail_target_contact_area
    )
    assert difference == 1100.0


def test_real_coplanar_bed_faces_equal_analytic_contact_area() -> None:
    printed = orient_sector_for_print_phase3sa(
        build_sector_panel_phase3sa(0.6)
    )
    contact_faces = [
        face for face in printed.faces("<Z").vals()
        if abs(face.BoundingBox().zmin) < 1.0e-6
        and abs(face.BoundingBox().zmax) < 1.0e-6
    ]
    actual = sum(face.Area() for face in contact_faces)
    assert abs(actual - rail_contact_area_phase3sa()) < 1.0e-5


def test_contact_area_is_more_than_old_integrated_coupon() -> None:
    old_contact_area_mm2 = 1856.0
    assert rail_contact_area_phase3sa() > old_contact_area_mm2
