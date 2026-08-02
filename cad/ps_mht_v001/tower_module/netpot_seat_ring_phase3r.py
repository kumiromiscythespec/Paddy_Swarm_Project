"""Replaceable preliminary Siawadeky net-pot liner/seat ring."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_seat_ring_flange_diameter,
    netpot_seat_ring_flange_thickness,
    netpot_seat_ring_height,
    netpot_seat_ring_outer_diameter,
    netpot_siawadeky_body_clearance_selected,
    netpot_siawadeky_body_diameter_preliminary,
    netpot_siawadeky_flange_diameter_assumed,
    netpot_siawadeky_height_assumed,
)


STATUS = "REFERENCE_PRELIMINARY_CALIBRATION_PENDING"
PRINT_ORIENTATION = "FLAT_ON_FLANGE_FACE"
OPERATION = "TOOL_FREE_REPLACEABLE_LINER_MAY_WITHDRAW_WITH_NETPOT"


def netpot_body_passage_diameter(
    clearance: float = netpot_siawadeky_body_clearance_selected,
) -> float:
    return netpot_siawadeky_body_diameter_preliminary + 2.0 * clearance


def build_netpot_seat_ring_phase3r(
    clearance: float = netpot_siawadeky_body_clearance_selected,
) -> cq.Workplane:
    passage = netpot_body_passage_diameter(clearance)
    body = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_seat_ring_outer_diameter)
        .circle(0.5 * passage)
        .extrude(netpot_seat_ring_height)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_seat_ring_flange_diameter)
        .circle(0.5 * passage)
        .extrude(netpot_seat_ring_flange_thickness)
        .translate((0.0, 0.0, netpot_seat_ring_height))
    )
    return body.union(flange)


def build_siawadeky_netpot_reference_phase3r() -> cq.Workplane:
    """Image-derived envelope; body and flange thickness remain assumptions."""

    body_top = netpot_siawadeky_body_diameter_preliminary
    body_bottom = 50.0
    body_height = netpot_siawadeky_height_assumed - 3.0
    body = (
        cq.Workplane("XY")
        .circle(0.5 * body_bottom)
        .workplane(offset=body_height)
        .circle(0.5 * body_top)
        .loft(combine=True)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_siawadeky_flange_diameter_assumed)
        .extrude(3.0)
        .translate((0.0, 0.0, body_height))
    )
    return body.union(flange)
