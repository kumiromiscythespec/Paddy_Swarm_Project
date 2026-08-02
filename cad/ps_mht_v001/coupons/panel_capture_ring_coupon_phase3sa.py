"""Reduced real-profile panel-end and temporary-ring capture coupon."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    build_temporary_panel_capture_ring_phase3sa,
)


STATUS = "PHASE3SA_CAPTURE_FIT_COUPON_CALIBRATION_PENDING"
COUPON_SOLID_COUNT = 2
PART_SPACING_MM = 15.0


def build_panel_capture_ring_coupon_phase3sa() -> cq.Workplane:
    panel = build_blank_sector_panel_calibration_reference_phase3sa(
        0.6,
        20.0,
    )
    panel_crop = panel.intersect(
        cq.Workplane("XY")
        .box(80.0, 80.0, 22.0)
        .translate((70.0, 0.0, 10.0))
    )
    ring = build_temporary_panel_capture_ring_phase3sa()
    ring_crop = ring.intersect(
        cq.Workplane("XY")
        .box(80.0, 80.0, 20.0)
        .translate((100.0, 0.0, 10.0))
    )

    panel_box = panel_crop.val().BoundingBox()
    ring_box = ring_crop.val().BoundingBox()
    panel_crop = panel_crop.translate(
        (-panel_box.xmin, -panel_box.ymin, -panel_box.zmin)
    )
    ring_crop = ring_crop.translate(
        (
            panel_box.xlen + PART_SPACING_MM - ring_box.xmin,
            -ring_box.ymin,
            -ring_box.zmin,
        )
    )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([panel_crop.val(), ring_crop.val()])]
    )
