"""Non-rotating dry-core frame references and printable centering parts."""

from __future__ import annotations

from math import hypot

import cadquery as cq


FRAME_ARCHITECTURE = "NON_ROTATING_DRY_CORE_FRAME_INTERFACE"
CENTRAL_DRY_OPENING_DIAMETER_MM = 100.0
MAXIMUM_DRY_CORE_FRAME_RADIUS_MM = 49.0
MAST_CANDIDATES = (
    "2020_ALUMINUM_EXTRUSION",
    "ROUND_METAL_TUBE_OD20",
    "ROUND_METAL_TUBE_OD25",
    "ROUND_METAL_TUBE_OD30",
    "THREADED_ROD_REFERENCE_ONLY",
)
REFERENCE_MAST_TYPE = "2020_ALUMINUM_EXTRUSION_NOMINAL_20X20_UNMEASURED"
SELECTED_MAST_TYPE = None
REFERENCE_MAST_NOMINAL_WIDTH_MM = 20.0
REFERENCE_MAST_DIAGONAL_MM = 2.0 ** 0.5 * REFERENCE_MAST_NOMINAL_WIDTH_MM
MAST_PHYSICAL_MEASUREMENT = "PENDING"

BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM = (98.0, 98.5, 99.0)
SELECTED_BOTTOM_PUCK_OUTER_DIAMETER_MM = None
REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM = 98.0
REFERENCE_MAST_CLEARANCE_MM = 21.0
SELECTED_MAST_CLEARANCE_MM = None
BOTTOM_PUCK_THICKNESS_MM = 10.0
TOP_CAP_THICKNESS_MM = 10.0
M5_CLEARANCE_DIAMETER_MM = 5.5

REAR_POST_CENTER_X_MM = -150.0
REAR_POST_SIZE_MM = 20.0
BRACKET_SPAN_MM = 170.0
BRACKET_WIDTH_MM = 30.0
BRACKET_THICKNESS_MM = 4.0
BRACKET_STRUCTURE = "METAL_FLAT_PLATE_REFERENCE_M5_TNUT_FASTENERS"


def _validate_puck_dimensions(outer_diameter_mm: float, mast_clearance_mm: float) -> None:
    if outer_diameter_mm not in BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM:
        raise ValueError("outer_diameter_mm must explicitly be 98.0, 98.5, or 99.0")
    if mast_clearance_mm <= REFERENCE_MAST_NOMINAL_WIDTH_MM:
        raise ValueError("mast clearance must exceed the nominal reference mast width")


def _square_mast_hole(size_mm: float, height_mm: float) -> cq.Workplane:
    return cq.Workplane("XY").rect(size_mm, size_mm).extrude(height_mm)


def _m5_base_holes(height_mm: float) -> cq.Workplane:
    holes: list[cq.Shape] = []
    for x in (-35.0, 35.0):
        holes.extend(
            cq.Workplane("XY").center(x, 0.0).circle(0.5 * M5_CLEARANCE_DIAMETER_MM).extrude(height_mm).solids().vals()
        )
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(holes)])


def build_bottom_centering_puck_phase3if(
    outer_diameter_mm: float,
    mast_clearance_mm: float,
) -> cq.Workplane:
    _validate_puck_dimensions(outer_diameter_mm, mast_clearance_mm)
    puck = cq.Workplane("XY").circle(0.5 * outer_diameter_mm).extrude(BOTTOM_PUCK_THICKNESS_MM)
    puck = puck.cut(_square_mast_hole(mast_clearance_mm, BOTTOM_PUCK_THICKNESS_MM))
    puck = puck.cut(_m5_base_holes(BOTTOM_PUCK_THICKNESS_MM)).clean()
    if len(puck.solids().vals()) != 1:
        raise RuntimeError("bottom puck must be one printable solid")
    return puck


def build_bottom_centering_puck_fit_coupons_phase3if() -> cq.Workplane:
    placements = ((-57.0, -35.0), (57.0, -35.0), (0.0, 64.0))
    solids: list[cq.Shape] = []
    for diameter, (x, y) in zip(BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM, placements):
        coupon = build_bottom_centering_puck_phase3if(diameter, REFERENCE_MAST_CLEARANCE_MM)
        solids.extend(coupon.translate((x, y, 0.0)).solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def build_removable_top_centering_cap_phase3if(
    outer_diameter_mm: float,
    mast_clearance_mm: float,
) -> cq.Workplane:
    _validate_puck_dimensions(outer_diameter_mm, mast_clearance_mm)
    cap = cq.Workplane("XY").circle(0.5 * outer_diameter_mm).extrude(TOP_CAP_THICKNESS_MM)
    cap = cap.cut(_square_mast_hole(mast_clearance_mm, TOP_CAP_THICKNESS_MM))
    # M5 through holes accept a removable metal clamp bar; no printed thread.
    cap = cap.cut(_m5_base_holes(TOP_CAP_THICKNESS_MM)).clean()
    if len(cap.solids().vals()) != 1:
        raise RuntimeError("top cap must be one removable solid")
    return cap


def build_central_mast_reference_phase3if(height_mm: float = 870.0, bottom_z_mm: float = -10.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(REFERENCE_MAST_NOMINAL_WIDTH_MM, REFERENCE_MAST_NOMINAL_WIDTH_MM, height_mm, centered=(True, True, False))
        .translate((0.0, 0.0, bottom_z_mm))
    )


def build_rear_2020_post_reference_phase3if(height_mm: float = 870.0, bottom_z_mm: float = -10.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(REAR_POST_SIZE_MM, REAR_POST_SIZE_MM, height_mm, centered=(True, True, False))
        .translate((REAR_POST_CENTER_X_MM, 0.0, bottom_z_mm))
    )


def build_rear_post_to_central_mast_bracket_reference_phase3if(z_mm: float) -> cq.Workplane:
    # Reference metal plate, not an STL and not a claim that PETG carries the
    # tower.  It overlaps both nominal 2020 sections for M5/T-nut fastening.
    return (
        cq.Workplane("XY")
        .box(BRACKET_SPAN_MM, BRACKET_WIDTH_MM, BRACKET_THICKNESS_MM, centered=(True, True, False))
        .translate((-75.0, 0.0, z_mm))
    )


def build_dry_core_frame_architecture_reference_phase3if() -> cq.Workplane:
    models = [
        build_central_mast_reference_phase3if(200.0, -10.0),
        build_rear_2020_post_reference_phase3if(200.0, -10.0),
        build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM),
        build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM).translate((0, 0, 160.0)),
        build_rear_post_to_central_mast_bracket_reference_phase3if(-8.0),
        build_rear_post_to_central_mast_bracket_reference_phase3if(174.0),
    ]
    solids: list[cq.Shape] = []
    for model in models:
        solids.extend(model.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def dry_core_component_audit_phase3if() -> dict[str, object]:
    coupons = build_bottom_centering_puck_fit_coupons_phase3if()
    coupon_box = coupons.val().BoundingBox()
    puck = build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    cap = build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    return {
        "architecture": FRAME_ARCHITECTURE,
        "central_opening_diameter_mm": CENTRAL_DRY_OPENING_DIAMETER_MM,
        "maximum_installed_frame_radius_mm": MAXIMUM_DRY_CORE_FRAME_RADIUS_MM,
        "mast_candidates": list(MAST_CANDIDATES),
        "selected_mast_type": SELECTED_MAST_TYPE,
        "reference_mast_type": REFERENCE_MAST_TYPE,
        "mast_physical_measurement": MAST_PHYSICAL_MEASUREMENT,
        "reference_mast_nominal_width_mm": REFERENCE_MAST_NOMINAL_WIDTH_MM,
        "reference_mast_diagonal_mm": REFERENCE_MAST_DIAGONAL_MM,
        "selected_puck_outer_diameter_mm": SELECTED_BOTTOM_PUCK_OUTER_DIAMETER_MM,
        "puck_outer_diameter_candidates_mm": list(BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM),
        "installed_reference_puck_outer_diameter_mm": REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM,
        "installed_reference_puck_is_production_selection": False,
        "selected_mast_clearance_mm": SELECTED_MAST_CLEARANCE_MM,
        "reference_mast_clearance_mm": REFERENCE_MAST_CLEARANCE_MM,
        "puck_solid_count": len(puck.solids().vals()),
        "top_cap_solid_count": len(cap.solids().vals()),
        "fit_coupon_solid_count": len(coupons.solids().vals()),
        "fit_coupon_bbox_mm": [coupon_box.xlen, coupon_box.ylen, coupon_box.zlen],
        "fit_coupon_a1_pass": coupon_box.xlen <= 245 and coupon_box.ylen <= 245 and coupon_box.zlen <= 240,
        "coupon_only_candidates_over_49mm_radius": [98.5, 99.0],
        "installed_candidate_within_49mm_radius": 0.5 * REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM <= MAXIMUM_DRY_CORE_FRAME_RADIUS_MM,
        "vertical_load_path": "MODULE_STACK_TO_BASE_NOT_SUSPENDED_FROM_MAST",
        "mast_loads": ["LATERAL_RESTRAINT", "TILT_RESTRAINT", "LIGHT_TOP_PRELOAD", "SEPARATION_RESTRAINT"],
        "petg_primary_bending_member": False,
        "bracket_primary_structure": BRACKET_STRUCTURE,
        "tool_removable": True,
        "printed_threads": False,
        "watertight_part": False,
    }
