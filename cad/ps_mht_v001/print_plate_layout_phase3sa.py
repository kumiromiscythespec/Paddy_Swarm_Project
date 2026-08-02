"""Individual Bambu Lab A1 plates for Phase 3S-A calibration."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.coupons.panel_capture_ring_coupon_phase3sa import (
    build_panel_capture_ring_coupon_phase3sa,
)
from ps_mht_v001.coupons.sector_panel_print_coupon_phase3sa import (
    build_sector_panel_print_coupon_phase3sa,
)
from ps_mht_v001.coupons.sector_seam_pair_coupon_phase3sa import (
    build_sector_seam_pair_coupon_phase3sa,
)
from ps_mht_v001.parameters import (
    phase3sa_seam_clearance_candidates,
    phase3sa_short_panel_height,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    build_temporary_panel_capture_ring_phase3sa,
)


STATUS = "PHASE3SA_FOUR_INDIVIDUAL_A1_PLATES_NO_GIANT_LAYOUT"
PART_SPACING_MM = 15.0
SELECTED_PRECALIBRATION_CANDIDATE_MM = 0.6


def _normalize(model: cq.Workplane) -> cq.Workplane:
    box = model.val().BoundingBox()
    return model.translate((-box.xmin, -box.ymin, -box.zmin))


def build_plate_01_sector_seam_coupons_phase3sa() -> cq.Workplane:
    coupons = [
        _normalize(build_sector_seam_pair_coupon_phase3sa(clearance))
        for clearance in phase3sa_seam_clearance_candidates
    ]
    first_box = coupons[0].val().BoundingBox()
    second_box = coupons[1].val().BoundingBox()
    placed = [
        coupons[0],
        coupons[1].translate(
            (first_box.xlen + PART_SPACING_MM, 0.0, 0.0)
        ),
        coupons[2].translate(
            (
                0.0,
                max(first_box.ylen, second_box.ylen) + PART_SPACING_MM,
                0.0,
            )
        ),
    ]
    shapes: list[cq.Shape] = []
    for model in placed:
        shapes.extend(model.solids().vals())
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(shapes)]
    )


def build_plate_02_panel_capture_coupon_phase3sa() -> cq.Workplane:
    ring = build_temporary_panel_capture_ring_phase3sa()
    coupon = build_panel_capture_ring_coupon_phase3sa()
    box = coupon.val().BoundingBox()
    centered_coupon = coupon.translate(
        (-box.center.x, -box.center.y, -box.zmin)
    )
    shapes = [ring.val(), *centered_coupon.solids().vals()]
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(shapes)]
    )


def build_plate_03_sector_panel_single_phase3sa() -> cq.Workplane:
    return _normalize(
        build_sector_panel_print_coupon_phase3sa(
            SELECTED_PRECALIBRATION_CANDIDATE_MM
        )
    )


def build_plate_04_three_sector_short_parts_phase3sa() -> cq.Workplane:
    source = orient_sector_for_print_phase3sa(
        build_blank_sector_panel_calibration_reference_phase3sa(
            SELECTED_PRECALIBRATION_CANDIDATE_MM,
            phase3sa_short_panel_height,
        )
    )
    source = _normalize(source)
    box = source.val().BoundingBox()
    panels = [
        source.translate(
            (0.0, index * (box.ylen + PART_SPACING_MM), 0.0)
        )
        for index in range(3)
    ]
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [panel.val() for panel in panels]
            )
        ]
    )


def phase3sa_individual_plates(
) -> tuple[tuple[str, cq.Workplane, int], ...]:
    return (
        (
            "plate_01_sector_seam_coupons_phase3sa",
            build_plate_01_sector_seam_coupons_phase3sa(),
            6,
        ),
        (
            "plate_02_panel_capture_coupon_phase3sa",
            build_plate_02_panel_capture_coupon_phase3sa(),
            3,
        ),
        (
            "plate_03_sector_panel_single_phase3sa",
            build_plate_03_sector_panel_single_phase3sa(),
            1,
        ),
        (
            "plate_04_three_sector_short_parts_phase3sa",
            build_plate_04_three_sector_short_parts_phase3sa(),
            3,
        ),
    )
