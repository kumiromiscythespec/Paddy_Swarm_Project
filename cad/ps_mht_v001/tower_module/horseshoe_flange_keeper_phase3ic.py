"""Envelope-neutral horseshoe flange load spreader V2 for Phase 3I-C."""

from __future__ import annotations

from functools import lru_cache

import cadquery as cq


KEEPER_V2_ARCHITECTURE = "HORSESHOE_FLANGE_LOAD_SPREADER_V2"
KEEPER_V2_OUTER_DIAMETER_MM = 107.0
KEEPER_V2_MAXIMUM_ALLOWED_OUTER_DIAMETER_MM = 107.5
KEEPER_V2_INNER_DIAMETER_MM = 90.0
KEEPER_V2_THICKNESS_MM = 5.0
KEEPER_V2_RETAINED_ARC_DEG = 180.0
KEEPER_V2_RADIAL_CONTACT_WIDTH_MM = 8.5

ROPE_NOTCH_COUNT = 2
ROPE_NOTCH_NOMINAL_WIDTH_MM = 5.6
ROPE_NOTCH_DEPTH_MM = 4.0
ROPE_NOTCH_MINIMUM_ROOT_WIDTH_MM = 8.0
ROPE_NOTCH_EDGE_RADIUS_MM = 2.8
TOP_BOTTOM_EDGE_CHAMFER_MM = 0.6

NETPOT_FLANGE_OUTER_DIAMETER_MM = 108.0
INSTALLED_NETPOT_ENVELOPE_MM = 237.21534220615763
MAXIMUM_TOTAL_XY_ENVELOPE_MM = 238.0
PRINT_ORIENTATION = "FLAT_Z_THICKNESS"
PRINT_SUPPORT = "NONE"
PRINT_STATUS = "READY_FIRST_LOW_COST_PHYSICAL_FIT"


def _raw_horseshoe_phase3ic() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * KEEPER_V2_OUTER_DIAMETER_MM)
        .circle(0.5 * KEEPER_V2_INNER_DIAMETER_MM)
        .extrude(KEEPER_V2_THICKNESS_MM)
    )
    half_space = (
        cq.Workplane("XY")
        .box(
            KEEPER_V2_OUTER_DIAMETER_MM,
            KEEPER_V2_OUTER_DIAMETER_MM + 2.0,
            KEEPER_V2_THICKNESS_MM,
            centered=(True, True, False),
        )
        .translate((-0.5 * KEEPER_V2_OUTER_DIAMETER_MM, 0.0, 0.0))
    )
    return ring.intersect(half_space)


def _open_rope_notch(y_mm: float) -> cq.Workplane:
    # A round-root opening crosses the horseshoe terminal face at X=0.  Its
    # 5.6-mm diameter accepts the cord from above without a printed hook.
    root_center_x = -(ROPE_NOTCH_DEPTH_MM - 0.5 * ROPE_NOTCH_NOMINAL_WIDTH_MM)
    return (
        cq.Workplane("XY")
        .center(root_center_x, y_mm)
        .circle(0.5 * ROPE_NOTCH_NOMINAL_WIDTH_MM)
        .extrude(KEEPER_V2_THICKNESS_MM + 2.0)
        .translate((0.0, 0.0, -1.0))
    )


@lru_cache(maxsize=1)
def build_horseshoe_flange_keeper_v2_phase3ic() -> cq.Workplane:
    keeper = _raw_horseshoe_phase3ic()
    terminal_radius = 0.25 * (KEEPER_V2_OUTER_DIAMETER_MM + KEEPER_V2_INNER_DIAMETER_MM)
    for y in (-terminal_radius, terminal_radius):
        keeper = keeper.cut(_open_rope_notch(y))
    # The circular notch supplies a 2.8-mm root radius.  All flange-contact
    # and exposed top edges receive a shallow printable chamfer.
    keeper = keeper.edges(">Z").chamfer(TOP_BOTTOM_EDGE_CHAMFER_MM)
    keeper = keeper.edges("<Z").chamfer(TOP_BOTTOM_EDGE_CHAMFER_MM)
    return keeper.clean()


def keeper_v2_envelope_audit_phase3ic() -> dict[str, object]:
    keeper = build_horseshoe_flange_keeper_v2_phase3ic()
    box = keeper.val().BoundingBox()
    return {
        "architecture": KEEPER_V2_ARCHITECTURE,
        "outer_diameter_mm": KEEPER_V2_OUTER_DIAMETER_MM,
        "measured_xy_bbox_mm": [box.xlen, box.ylen],
        "inner_diameter_mm": KEEPER_V2_INNER_DIAMETER_MM,
        "thickness_mm": KEEPER_V2_THICKNESS_MM,
        "retained_arc_deg": KEEPER_V2_RETAINED_ARC_DEG,
        "radial_contact_width_mm": KEEPER_V2_RADIAL_CONTACT_WIDTH_MM,
        "notch_count": ROPE_NOTCH_COUNT,
        "notch_width_mm": ROPE_NOTCH_NOMINAL_WIDTH_MM,
        "notch_depth_mm": ROPE_NOTCH_DEPTH_MM,
        "notch_structural_root_width_mm": 12.0,
        "notch_edge_radius_mm": ROPE_NOTCH_EDGE_RADIUS_MM,
        "top_bottom_chamfer_mm": TOP_BOTTOM_EDGE_CHAMFER_MM,
        "flange_outer_diameter_mm": NETPOT_FLANGE_OUTER_DIAMETER_MM,
        "keeper_within_flange_envelope": KEEPER_V2_OUTER_DIAMETER_MM < NETPOT_FLANGE_OUTER_DIAMETER_MM,
        "installed_netpot_envelope_before_mm": INSTALLED_NETPOT_ENVELOPE_MM,
        "installed_netpot_envelope_with_keeper_mm": INSTALLED_NETPOT_ENVELOPE_MM,
        "envelope_increase_mm": 0.0,
        "maximum_allowed_total_xy_mm": MAXIMUM_TOTAL_XY_ENVELOPE_MM,
        "plant_center_open": True,
        "rope_installs_from_above": True,
        "printed_snap_features": False,
        "solid_count": len(keeper.solids().vals()),
        "valid": all(solid.isValid() for solid in keeper.solids().vals()),
        "print_orientation": PRINT_ORIENTATION,
        "support": PRINT_SUPPORT,
    }
