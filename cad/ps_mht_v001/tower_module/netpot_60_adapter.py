"""Nominal-60 purchased net-pot insert for the generic port adapter."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_adapter_body_length,
    netpot_adapter_flange_diameter,
    netpot_body_top_outer_diameter,
    netpot_fit_clearance,
    port_adapter_inner_diameter,
    port_rain_return_lip_height,
)


MATERIAL = "PRINTED_PETG"
STATUS = "CALIBRATION_PENDING_NETPOT_MEASUREMENT"
OPERATION = "TOOL_FREE_GRAVITY_SEATED_REPLACEABLE_LINER"
REMOVAL = "MAY_WITHDRAW_WITH_PURCHASED_NETPOT"
ROTATION_POLICY = "FREE_ROTATION_FUNCTIONALLY_ACCEPTABLE"
RETENTION_POLICY = "NO_THIN_SNAP_TABS"


def netpot_adapter_body_outer_diameter(
    clearance: float = netpot_fit_clearance,
) -> float:
    return port_adapter_inner_diameter - 2.0 * clearance


def netpot_adapter_seat_diameter(
    clearance: float = netpot_fit_clearance,
) -> float:
    return netpot_body_top_outer_diameter + 2.0 * clearance


def build_netpot_60_adapter(
    clearance: float = netpot_fit_clearance,
) -> cq.Workplane:
    """Build the replaceable insert and net-pot flange load seat."""

    body_outer = netpot_adapter_body_outer_diameter(clearance)
    seat_diameter = netpot_adapter_seat_diameter(clearance)
    body = (
        cq.Workplane("XY")
        .circle(0.5 * body_outer)
        .circle(0.5 * seat_diameter)
        .extrude(netpot_adapter_body_length)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_adapter_flange_diameter)
        .circle(0.5 * seat_diameter)
        .extrude(3.0)
        .translate((0.0, 0.0, netpot_adapter_body_length - 0.5))
    )
    rain_return = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_adapter_flange_diameter)
        .circle(0.5 * netpot_adapter_flange_diameter - 2.0)
        .extrude(port_rain_return_lip_height)
        .translate((0.0, 0.0, netpot_adapter_body_length + 2.5))
    )
    return body.union(flange).union(rain_return)
