"""Phase 3H-A horizontal full-ring joint calibration geometry.

The production clearance is deliberately not selected here.  Every public
candidate builder requires an explicit radial-per-side clearance.
"""

from __future__ import annotations

from math import isclose

import cadquery as cq

from ps_mht_v001.parameters import (
    horizontal_joint_clearance_candidates,
    horizontal_joint_hard_stop_width,
    horizontal_joint_lower_physical_print_height,
    horizontal_joint_nominal_inner_diameter,
    horizontal_joint_nominal_outer_diameter,
    horizontal_joint_lead_chamfer,
    horizontal_joint_skirt_overlap_length,
    horizontal_joint_skirt_root_radius,
    horizontal_joint_skirt_thickness,
    horizontal_joint_stop_collar_outer_diameter,
    horizontal_joint_upper_physical_print_height,
)


STATUS = "PHASE3HA_CLEARANCE_SELECTION_PENDING"
JOINT_AXIS = "ASSEMBLY_Z"
PRINT_ORIENTATION_LOWER = "FULL_CIRCUMFERENCE_ON_BED"
PRINT_ORIENTATION_UPPER = "SKIRT_UP_FULL_CIRCUMFERENCE_ON_BED"
PORT_COUNT = 0
BUFFER_TRAY_COUNT = 0
SMALL_PART_COUNT = 0
SEALANT_COUNT = 0
DRIP_EDGE_ANGLE_DEG = 45.0


def validate_horizontal_joint_clearance_phase3ha(clearance: float) -> float:
    """Accept only the three audit-authorized radial-per-side candidates."""

    value = float(clearance)
    for candidate in horizontal_joint_clearance_candidates:
        if isclose(value, candidate, abs_tol=1.0e-9):
            return candidate
    raise ValueError(
        "Phase 3H-A clearance must be explicitly set to 0.3, 0.5, or "
        f"0.7 mm/side; got {value!r}"
    )


def clearance_token_phase3ha(clearance: float) -> str:
    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    return f"c{int(round(value * 100)):03d}"


def build_lower_full_ring_phase3ha() -> cq.Workplane:
    """Build the 40 mm lower ring and its continuous 4 mm stop land."""

    outer_radius = 0.5 * horizontal_joint_nominal_outer_diameter
    inner_radius = 0.5 * horizontal_joint_nominal_inner_diameter
    collar_radius = 0.5 * horizontal_joint_stop_collar_outer_diameter
    body_height = (
        horizontal_joint_lower_physical_print_height
        - horizontal_joint_hard_stop_width
    )
    body = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(body_height)
    )
    stop_land = (
        cq.Workplane("XY")
        .workplane(offset=body_height)
        .circle(collar_radius)
        .circle(inner_radius)
        .extrude(horizontal_joint_hard_stop_width)
    )
    return body.union(stop_land)


def _upper_radial_section_phase3ha(
    clearance: float,
    angle_degrees: float = 360.0,
) -> cq.Workplane:
    """Build the real skirt/root/stop/body section around assembly Z."""

    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    body_inner = 0.5 * horizontal_joint_nominal_inner_diameter
    body_outer = 0.5 * horizontal_joint_nominal_outer_diameter
    collar_outer = 0.5 * horizontal_joint_stop_collar_outer_diameter
    skirt_outer = body_inner - value
    skirt_inner = skirt_outer - horizontal_joint_skirt_thickness
    root_r = horizontal_joint_skirt_root_radius
    overlap = horizontal_joint_skirt_overlap_length
    stop_h = horizontal_joint_hard_stop_width

    # The 1 mm lead occupies the final axial millimetre.  Its radial relief is
    # 0.2 mm; together with the 0.2 mm, 45-degree inner drip edge this leaves
    # the authorized 2.4 mm minimum at the very tip of the 2.8 mm skirt.
    lead_radial = 0.2
    drip_radial = 0.2
    lead_axial = horizontal_joint_lead_chamfer

    tip_outer = cq.Solid.makeCone(
        skirt_outer - lead_radial,
        skirt_outer,
        lead_axial,
        cq.Vector(0.0, 0.0, -overlap),
    )
    tip_inner_chamfer = cq.Solid.makeCone(
        skirt_inner + drip_radial,
        skirt_inner,
        drip_radial,
        cq.Vector(0.0, 0.0, -overlap),
    )
    tip_inner_straight = cq.Solid.makeCylinder(
        skirt_inner,
        lead_axial - drip_radial,
        cq.Vector(0.0, 0.0, -overlap + drip_radial),
    )
    tip_inner = tip_inner_chamfer.fuse(tip_inner_straight)
    tip = cq.Workplane("XY").newObject([tip_outer.cut(tip_inner)])
    straight_skirt = (
        cq.Workplane("XY")
        .workplane(offset=-overlap + lead_axial)
        .circle(skirt_outer)
        .circle(skirt_inner)
        .extrude(overlap - lead_axial)
    )
    stop_collar = (
        cq.Workplane("XY")
        .circle(collar_outer)
        .circle(skirt_inner)
        .extrude(stop_h)
    )
    body = (
        cq.Workplane("XY")
        .workplane(offset=stop_h)
        .circle(body_outer)
        .circle(body_inner)
        .extrude(40.0 - stop_h)
    )
    model = tip.union(straight_skirt).union(stop_collar).union(body)

    # Round the continuous inner root where the skirt/collar transitions to
    # the nominal 194 mm body bore.  Selecting by measured circle is stable
    # across all three candidate clearances.
    root_edges = [
        edge
        for edge in model.edges("%CIRCLE").vals()
        if abs(edge.Center().z - stop_h) < 1.0e-7
        and abs(edge.BoundingBox().xlen - 2.0 * skirt_inner) < 1.0e-6
    ]
    if len(root_edges) != 1:
        raise RuntimeError("unable to identify the continuous skirt root edge")
    model = model.newObject(root_edges).fillet(root_r)

    if angle_degrees < 360.0:
        if abs(angle_degrees - 90.0) > 1.0e-9:
            raise ValueError("Phase 3H-A currently authorizes only a 90 degree arc")
        cutter = (
            cq.Workplane("XY")
            .box(110.0, 110.0, 100.0, centered=(False, False, False))
            .translate((0.0, 0.0, -20.0))
        )
        model = model.intersect(cutter)
    return model


def build_upper_full_ring_assembly_phase3ha(clearance: float) -> cq.Workplane:
    """Build the upper ring in assembly coordinates (skirt below Z=0)."""

    return _upper_radial_section_phase3ha(clearance)


def build_upper_arc_assembly_phase3ha(
    clearance: float,
    angle_degrees: float = 90.0,
) -> cq.Workplane:
    """Build a partial ring with the identical revolved functional section."""

    if not 0.0 < angle_degrees < 360.0:
        raise ValueError("arc angle must be greater than 0 and less than 360")
    return _upper_radial_section_phase3ha(clearance, angle_degrees)


def build_upper_full_ring_print_phase3ha(clearance: float) -> cq.Workplane:
    """Return the upper ring already oriented skirt-up for slicing."""

    model = build_upper_full_ring_assembly_phase3ha(clearance)
    return model.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0).translate(
        (0.0, 0.0, 40.0)
    )


def full_ring_joint_assembly_parts_phase3ha(
    clearance: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    """Return lower and upper parts in the nominal fully seated assembly."""

    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    lower = build_lower_full_ring_phase3ha()
    upper = build_upper_full_ring_assembly_phase3ha(value).translate(
        (0.0, 0.0, horizontal_joint_lower_physical_print_height)
    )
    return lower, upper


def build_full_ring_joint_pair_phase3ha(clearance: float) -> cq.Workplane:
    """Return a two-solid assembly reference; no default clearance is allowed."""

    lower, upper = full_ring_joint_assembly_parts_phase3ha(clearance)
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([lower.val(), upper.val()])]
    )


def horizontal_joint_requirements_phase3ha(clearance: float) -> dict[str, object]:
    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    return {
        "status": STATUS,
        "clearance_mm_per_side": value,
        "joint_axis": JOINT_AXIS,
        "nominal_outer_diameter_mm": horizontal_joint_nominal_outer_diameter,
        "nominal_inner_diameter_mm": horizontal_joint_nominal_inner_diameter,
        "structural_wall_mm": 0.5
        * (
            horizontal_joint_nominal_outer_diameter
            - horizontal_joint_nominal_inner_diameter
        ),
        "skirt_overlap_mm": horizontal_joint_skirt_overlap_length,
        "skirt_nominal_thickness_mm": horizontal_joint_skirt_thickness,
        "skirt_minimum_tip_thickness_mm": horizontal_joint_skirt_thickness
        - 0.4,
        "skirt_root_radius_mm": horizontal_joint_skirt_root_radius,
        "lead_chamfer_axial_length_mm": horizontal_joint_lead_chamfer,
        "inner_drip_edge_angle_deg": DRIP_EDGE_ANGLE_DEG,
        "hard_stop_width_mm": horizontal_joint_hard_stop_width,
        "upper_physical_print_height_mm": horizontal_joint_upper_physical_print_height,
        "lower_physical_print_height_mm": horizontal_joint_lower_physical_print_height,
        "full_circumference": True,
        "closed_cavity": False,
        "cleaning_brush_access": True,
        "direct_outside_to_inside_sightline": False,
        "port_count": PORT_COUNT,
        "buffer_tray_count": BUFFER_TRAY_COUNT,
        "small_part_count": SMALL_PART_COUNT,
        "sealant_count": SEALANT_COUNT,
    }
