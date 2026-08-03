"""Phase 3H-B wrappers that reuse Phase 3H-A authoritative geometry."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    horizontal_joint_lower_physical_print_height,
    phase3ha_m4_clearance_hole,
)
from ps_mht_v001.phase3hb_state import FULL_RING_CLEARANCE_MM
from ps_mht_v001.test_fixtures.horizontal_joint_compression_fixture_phase3ha import (
    build_horizontal_joint_compression_ring_phase3ha,
    m4_axis_points_phase3ha,
)
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    build_lower_full_ring_phase3ha,
    build_upper_full_ring_print_phase3ha,
    full_ring_joint_assembly_parts_phase3ha,
    horizontal_joint_requirements_phase3ha,
)


SOURCE_GEOMETRY_AUTHORITY = "PHASE3HA_IMPORTED_NOT_COPIED"
REFERENCE_ONLY = True
M4_ENVELOPE_COUNT = 3


def build_full_ring_lower_c050_phase3hb() -> cq.Workplane:
    """Reuse the Phase 3H-A lower full ring without geometric modification."""

    return build_lower_full_ring_phase3ha()


def build_full_ring_upper_c050_print_phase3hb() -> cq.Workplane:
    """Reuse the Phase 3H-A c050 upper ring in its authorized print posture."""

    return build_upper_full_ring_print_phase3ha(FULL_RING_CLEARANCE_MM)


def build_full_ring_pair_c050_reference_phase3hb() -> cq.Workplane:
    """Return seated rings plus three existing M4-axis envelope references."""

    lower, upper = full_ring_joint_assembly_parts_phase3ha(
        FULL_RING_CLEARANCE_MM
    )
    shapes: list[cq.Shape] = [lower.val(), upper.val()]
    for x_value, y_value in m4_axis_points_phase3ha():
        envelope = cq.Solid.makeCylinder(
            0.5 * phase3ha_m4_clearance_hole,
            2.0 * horizontal_joint_lower_physical_print_height,
            cq.Vector(x_value, y_value, 0.0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        shapes.append(envelope)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def build_compression_ring_reference_phase3hb() -> cq.Workplane:
    """Reuse the unchanged Phase 3H-A common compression ring."""

    return build_horizontal_joint_compression_ring_phase3ha()


def phase3hb_geometry_requirements() -> dict[str, object]:
    source = horizontal_joint_requirements_phase3ha(FULL_RING_CLEARANCE_MM)
    lower = build_full_ring_lower_c050_phase3hb().val().BoundingBox()
    upper = build_full_ring_upper_c050_print_phase3hb().val().BoundingBox()
    pair = build_full_ring_pair_c050_reference_phase3hb().val().BoundingBox()
    lower_inner_radius = 0.5 * source["nominal_inner_diameter_mm"]
    candidates = {
        token: {
            "radial_clearance_mm_per_side": clearance,
            "skirt_outer_radius_mm": lower_inner_radius - clearance,
            "skirt_outer_diameter_mm": 2.0 * (lower_inner_radius - clearance),
            "relative_fit": relation,
        }
        for token, clearance, relation in (
            ("c030", 0.30, "TIGHTEST_OF_THREE"),
            ("c050", 0.50, "MIDDLE_SELECTED_ARC_CANDIDATE"),
            ("c070", 0.70, "LOOSEST_OF_THREE"),
        )
    }
    return {
        "source_geometry_authority": SOURCE_GEOMETRY_AUTHORITY,
        "clearance_mm_per_side": FULL_RING_CLEARANCE_MM,
        "candidate_dimensions": candidates,
        "greater_candidate_number_means": "GREATER_CLEARANCE_SMALLER_SKIRT_OD_LOOSER_FIT",
        "lower_print_envelope_mm": [lower.xlen, lower.ylen, lower.zlen],
        "upper_print_envelope_mm": [upper.xlen, upper.ylen, upper.zlen],
        "pair_reference_envelope_mm": [pair.xlen, pair.ylen, pair.zlen],
        "assembled_height_mm": pair.zlen,
        "skirt_overlap_mm": source["skirt_overlap_mm"],
        "hard_stop_width_mm": source["hard_stop_width_mm"],
        "m4_envelope_count": M4_ENVELOPE_COUNT,
        "hole_1_feature_added": False,
    }
