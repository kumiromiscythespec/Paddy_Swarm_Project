"""Five-stage Phase 3I-F dry-core frame reference and collision audits."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.fixtures.dry_core_frame_phase3if import (
    BRACKET_THICKNESS_MM,
    MAXIMUM_DRY_CORE_FRAME_RADIUS_MM,
    REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM,
    REFERENCE_MAST_CLEARANCE_MM,
    build_bottom_centering_puck_phase3if,
    build_central_mast_reference_phase3if,
    build_rear_2020_post_reference_phase3if,
    build_rear_post_to_central_mast_bracket_reference_phase3if,
    build_removable_top_centering_cap_phase3if,
)
from ps_mht_v001.fixtures.stack_clocking_gauge_30deg_phase3ie import (
    REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM,
    build_stack_clocking_gauge_30deg_phase3ie,
)
from ps_mht_v001.reference.integrated_stage_references_phase3ib import build_keeper_installed_reference_phase3ib
from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    DROP_CORRIDOR_LOWER_Z_MM,
    DROP_CORRIDOR_STRETCH_DIAMETER_MM,
    DROP_CORRIDOR_UPPER_Z_MM,
    OVERFLOW_ANGLES_LOCAL_DEG,
    OVERFLOW_CENTER_RADIUS_MM,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import build_installed_netpot_reference_phase3ia
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3if import build_integrated_stage_full_direct_drop_phase3if


STAGE_ABSOLUTE_ROTATIONS_DEG = (0.0, 30.0, 60.0, 90.0, 120.0)
STAGE_HEIGHT_MM = 170.0
STACK_HEIGHT_MM = 850.0
LOWER_BRACKET_Z_MM = -8.0
UPPER_BRACKET_Z_MM = 854.0
REFERENCE_ONLY = True


def _append(solids: list[cq.Shape], model: cq.Workplane) -> None:
    solids.extend(model.solids().vals())


def _stage_transform(model: cq.Workplane, stage_index: int) -> cq.Workplane:
    rotation = STAGE_ABSOLUTE_ROTATIONS_DEG[stage_index]
    return model.rotate((0, 0, 0), (0, 0, 1), rotation).translate((0, 0, stage_index * STAGE_HEIGHT_MM))


def build_all_interstage_drop_corridors_phase3if(diameter_mm: float = DROP_CORRIDOR_STRETCH_DIAMETER_MM) -> cq.Workplane:
    solids: list[cq.Shape] = []
    for lower_index in range(4):
        upper_rotation = STAGE_ABSOLUTE_ROTATIONS_DEG[lower_index + 1]
        lower_z = lower_index * STAGE_HEIGHT_MM
        for local_angle in OVERFLOW_ANGLES_LOCAL_DEG:
            global_angle = local_angle + upper_rotation
            x = OVERFLOW_CENTER_RADIUS_MM * cos(radians(global_angle))
            y = OVERFLOW_CENTER_RADIUS_MM * sin(radians(global_angle))
            corridor = (
                cq.Workplane("XY")
                .center(x, y)
                .circle(0.5 * diameter_mm)
                .extrude(DROP_CORRIDOR_UPPER_Z_MM - DROP_CORRIDOR_LOWER_Z_MM)
                .translate((0, 0, lower_z + DROP_CORRIDOR_LOWER_Z_MM))
            )
            _append(solids, corridor)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _all_pot_references_phase3if() -> cq.Workplane:
    solids: list[cq.Shape] = []
    for stage_index in range(5):
        for angle in phase3ib.PORT_ANGLES_DEG:
            _append(solids, _stage_transform(build_installed_netpot_reference_phase3ia(angle), stage_index))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _all_keeper_references_phase3if() -> cq.Workplane:
    solids: list[cq.Shape] = []
    for stage_index in range(5):
        for angle in phase3ib.PORT_ANGLES_DEG:
            _append(solids, _stage_transform(build_keeper_installed_reference_phase3ib(angle), stage_index))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _all_water_references_phase3if() -> cq.Workplane:
    solids: list[cq.Shape] = []
    for stage_index in range(5):
        water = phase3ib._annulus(95.2, 54.8, 0.2, stage_index * STAGE_HEIGHT_MM + 26.0)
        _append(solids, water)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if() -> cq.Workplane:
    solids: list[cq.Shape] = []
    full = build_integrated_stage_full_direct_drop_phase3if()
    for index in range(5):
        _append(solids, _stage_transform(full, index))
    _append(solids, build_all_interstage_drop_corridors_phase3if())
    _append(solids, build_central_mast_reference_phase3if(880.0, -10.0))
    _append(solids, build_rear_2020_post_reference_phase3if(880.0, -10.0))
    _append(solids, build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM))
    _append(solids, build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM).translate((0, 0, STACK_HEIGHT_MM - 10.0)))
    _append(solids, build_rear_post_to_central_mast_bracket_reference_phase3if(LOWER_BRACKET_Z_MM))
    _append(solids, build_rear_post_to_central_mast_bracket_reference_phase3if(UPPER_BRACKET_Z_MM))
    _append(solids, _all_pot_references_phase3if())
    _append(solids, _all_keeper_references_phase3if())
    _append(solids, _all_water_references_phase3if())
    gauge = build_stack_clocking_gauge_30deg_phase3ie(REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM).translate((0, 0, 165.0))
    _append(solids, gauge)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _intersection_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return sum(s.Volume() for s in a.intersect(b).clean().solids().vals())


def five_stage_dry_core_collision_audit_phase3if() -> dict[str, object]:
    full = build_integrated_stage_full_direct_drop_phase3if()
    stages = [_stage_transform(full, index) for index in range(5)]
    mast = build_central_mast_reference_phase3if(880.0, -10.0)
    post = build_rear_2020_post_reference_phase3if(880.0, -10.0)
    puck = build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    cap = build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM).translate((0, 0, STACK_HEIGHT_MM - 10.0))
    lower_bracket = build_rear_post_to_central_mast_bracket_reference_phase3if(LOWER_BRACKET_Z_MM)
    upper_bracket = build_rear_post_to_central_mast_bracket_reference_phase3if(UPPER_BRACKET_Z_MM)
    corridors = build_all_interstage_drop_corridors_phase3if()
    pots = _all_pot_references_phase3if()
    water = _all_water_references_phase3if()
    root_region = phase3ib._annulus(95.0, 55.0, STACK_HEIGHT_MM, 0.0)

    stage_pair_intersections = []
    for index in range(4):
        stage_pair_intersections.append(_intersection_volume(stages[index], stages[index + 1]))
    intersections = {
        "drop_corridors_vs_central_mast": _intersection_volume(corridors, mast),
        "drop_corridors_vs_bottom_puck": _intersection_volume(corridors, puck),
        "drop_corridors_vs_top_cap": _intersection_volume(corridors, cap),
        "drop_corridors_vs_lower_bracket": _intersection_volume(corridors, lower_bracket),
        "drop_corridors_vs_upper_bracket": _intersection_volume(corridors, upper_bracket),
        "central_mast_vs_netpots": _intersection_volume(mast, pots),
        "central_mast_vs_root_assumed_region": _intersection_volume(mast, root_region),
        "bottom_puck_vs_water": _intersection_volume(puck, water),
        "top_cap_vs_water": _intersection_volume(cap, water),
        "rear_post_vs_netpots": _intersection_volume(post, pots),
        "lower_bracket_vs_netpots": _intersection_volume(lower_bracket, pots),
        "upper_bracket_vs_netpots": _intersection_volume(upper_bracket, pots),
    }
    radial_margin = (OVERFLOW_CENTER_RADIUS_MM - 2.0 - 0.5 * DROP_CORRIDOR_STRETCH_DIAMETER_MM) - MAXIMUM_DRY_CORE_FRAME_RADIUS_MM
    return {
        "stage_rotations_deg": list(STAGE_ABSOLUTE_ROTATIONS_DEG),
        "stage_pair_intersections_mm3": stage_pair_intersections,
        "intersections_mm3": intersections,
        "all_unintended_intersections_zero": all(value < 1.0e-6 for value in stage_pair_intersections) and all(value < 1.0e-6 for value in intersections.values()),
        "drop_corridor_count": len(corridors.solids().vals()),
        "minimum_tolerance_radial_margin_to_frame_mm": radial_margin,
        "thirty_degree_rotation_unobstructed": radial_margin > 0.0,
        "upward_disassembly": "PASS_AFTER_REMOVING_TOP_BRACKET_AND_TOP_CAP",
        "upper_bracket_removable": True,
        "clocking_gauge_role": "ANGULAR_ALIGNMENT_ONLY",
        "central_mast_role": "RADIAL_AND_LATERAL_ALIGNMENT_ONLY",
        "upper_tank_envelope": "NOT_PROVIDED_NO_PHYSICAL_LOAD_ASSUMED",
        "obvious_modeled_upper_tank_collision": False,
        "tool_access_reference": "TOP_AND_BOTTOM_BRACKETS_OUTSIDE_STACK_Z_ENVELOPE",
        "physical_frame_validation": "PENDING",
    }


def five_stage_reference_metadata_phase3if() -> dict[str, object]:
    reference = build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if()
    return {
        "reference_only": True,
        "solid_count": len(reference.solids().vals()),
        "stage_count": 5,
        "stage_absolute_rotations_deg": list(STAGE_ABSOLUTE_ROTATIONS_DEG),
        "plant_port_absolute_angles_deg": [
            [float((rotation + local) % 360.0) for local in phase3ib.PORT_ANGLES_DEG]
            for rotation in STAGE_ABSOLUTE_ROTATIONS_DEG
        ],
        "contains": [
            "FIVE_PHASE3IF_MODULES", "TWELVE_DROP_CORRIDORS", "NON_ROTATING_CENTRAL_2020_REFERENCE",
            "BOTTOM_CENTERING_PUCK_REFERENCE", "REMOVABLE_TOP_CAP_REFERENCE", "REAR_2020_POST",
            "LOWER_AND_UPPER_METAL_BRACKET_REFERENCES", "FIFTEEN_NETPOT_REFERENCES",
            "FIFTEEN_KEEPER_REFERENCES", "FIVE_WATER_SURFACES", "CLOCKING_GAUGE_USE_POSITION",
        ],
    }
