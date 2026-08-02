"""Calibration-only annular M4 ring with three identifiable clearances."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    module_nut_pocket_clearance_candidates,
    module_nut_ring_thickness,
    phase3r_m4_pitch_radius,
    used_fastener_angles,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r1 import (
    _build_ring_with_clearances_phase3r1,
)


STATUS = "PHASE3R1_CALIBRATION_COUPON_NOT_FOR_PRODUCTION_ASSEMBLY"
CALIBRATION_ONLY = True
NUT_POCKET_CLEARANCES = tuple(module_nut_pocket_clearance_candidates)
PHYSICAL_ID_SCHEME = "ONE_TWO_THREE_TOP_DIMPLING_BY_ASCENDING_CLEARANCE"
COUPON_SOLID_COUNT = 1
PRINT_ORIENTATION = "FLAT_POCKETS_AND_ID_DIMPLES_UP"


def _add_identification_dimples(ring: cq.Workplane) -> cq.Workplane:
    """Cut 1/2/3 shallow dots next to the 0.15/0.25/0.35 mm stations."""

    for station_index, angle_deg in enumerate(used_fastener_angles, start=1):
        for dot_index in range(station_index):
            marker_angle = radians(angle_deg + 12.0 + 3.0 * dot_index)
            x = phase3r_m4_pitch_radius * cos(marker_angle)
            y = phase3r_m4_pitch_radius * sin(marker_angle)
            dimple = (
                cq.Workplane("XY")
                .center(x, y)
                .circle(0.6)
                .extrude(1.0)
                .translate((0.0, 0.0, module_nut_ring_thickness - 0.5))
            )
            ring = ring.cut(dimple)
    return ring


def build_annular_nut_ring_coupon_phase3r1() -> cq.Workplane:
    ring = _build_ring_with_clearances_phase3r1(NUT_POCKET_CLEARANCES)
    return _add_identification_dimples(ring)
