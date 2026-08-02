"""Phase 3S-A.1 plates with explicit selected seam clearance."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.coupons.panel_capture_ring_coupon_phase3sa1 import (
    build_panel_capture_ring_coupon_phase3sa1,
)
from ps_mht_v001.coupons.sector_panel_print_coupon_phase3sa import (
    build_sector_panel_print_coupon_phase3sa,
)
from ps_mht_v001.parameters import phase3sa_short_panel_height
from ps_mht_v001.print_plate_layout_phase3sa import (
    PART_SPACING_MM,
    build_plate_01_sector_seam_coupons_phase3sa,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    build_temporary_panel_capture_ring_phase3sa,
)


STATUS = "PHASE3SA1_NO_IMPLICIT_SELECTED_CLEARANCE"


def seam_clearance_token_phase3sa1(clearance: float) -> str:
    value = validate_seam_clearance_phase3sa(clearance)
    return f"c{int(round(value * 100)):03d}"


def _normalize(model: cq.Workplane) -> cq.Workplane:
    box = model.val().BoundingBox()
    return model.translate((-box.xmin, -box.ymin, -box.zmin))


def build_plate_01_sector_seam_coupons_phase3sa1() -> cq.Workplane:
    """Plate 01 contains all three candidates and needs no selection."""

    return build_plate_01_sector_seam_coupons_phase3sa()


def build_plate_02_panel_capture_coupon_phase3sa1(
    clearance: float,
) -> cq.Workplane:
    """Build Plate 02 only for an explicitly supplied candidate."""

    value = validate_seam_clearance_phase3sa(clearance)
    ring = build_temporary_panel_capture_ring_phase3sa()
    coupon = build_panel_capture_ring_coupon_phase3sa1(value)
    box = coupon.val().BoundingBox()
    centered_coupon = coupon.translate(
        (-box.center.x, -box.center.y, -box.zmin)
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [ring.val(), *centered_coupon.solids().vals()]
            )
        ]
    )


def build_plate_03_sector_panel_single_phase3sa1(
    clearance: float,
) -> cq.Workplane:
    """Build Plate 03 only for an explicitly supplied candidate."""

    value = validate_seam_clearance_phase3sa(clearance)
    return _normalize(build_sector_panel_print_coupon_phase3sa(value))


def build_plate_04_three_sector_short_parts_phase3sa1(
    clearance: float,
) -> cq.Workplane:
    """Build Plate 04 only for an explicitly supplied candidate."""

    value = validate_seam_clearance_phase3sa(clearance)
    source = orient_sector_for_print_phase3sa(
        build_blank_sector_panel_calibration_reference_phase3sa(
            value,
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


def selected_plate_file_names_phase3sa1(
    clearance: float,
) -> tuple[str, str, str]:
    token = seam_clearance_token_phase3sa1(clearance)
    return (
        f"plate_02_panel_capture_coupon_{token}_phase3sa1.stl",
        f"plate_03_sector_panel_single_{token}_phase3sa1.stl",
        f"plate_04_three_sector_short_parts_{token}_phase3sa1.stl",
    )


def selected_plates_phase3sa1(
    clearance: float,
) -> tuple[tuple[str, cq.Workplane, int], ...]:
    value = validate_seam_clearance_phase3sa(clearance)
    names = selected_plate_file_names_phase3sa1(value)
    return (
        (
            names[0][:-4],
            build_plate_02_panel_capture_coupon_phase3sa1(value),
            3,
        ),
        (
            names[1][:-4],
            build_plate_03_sector_panel_single_phase3sa1(value),
            1,
        ),
        (
            names[2][:-4],
            build_plate_04_three_sector_short_parts_phase3sa1(value),
            3,
        ),
    )
