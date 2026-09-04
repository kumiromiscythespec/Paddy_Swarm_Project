"""Reference-only Phase 3I-E drop corridors and correct/wrong assemblies."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.fixtures.stack_clocking_gauge_30deg_phase3ie import (
    REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM,
    build_stack_clocking_gauge_30deg_phase3ie,
)
from ps_mht_v001.reference.integrated_stage_references_phase3ib import (
    build_keeper_installed_reference_phase3ib,
)
from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    DROP_CORRIDOR_STRETCH_DIAMETER_MM,
    build_drop_corridor_reference_phase3ie,
    correct_wrong_alignment_audit_phase3ie,
)
from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    RETENTION_LUG_SIDE_SIGNS,
    build_isolated_retention_lug_net_phase3ic,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    build_installed_netpot_reference_phase3ia,
    build_internal_rib_phase3ia,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ie import (
    build_integrated_stage_full_direct_drop_phase3ie,
)


REFERENCE_ONLY = True
CORRECT_ROTATION_DEG = 30.0
WRONG_ROTATION_DEG = 0.0
COLLISION_ROTATION_DEG = 60.0
UPPER_TRANSLATION_Z_MM = 170.0


def _append(solids: list[cq.Shape], model: cq.Workplane) -> None:
    solids.extend(model.solids().vals())


def _transform_upper(model: cq.Workplane, rotation_deg: float) -> cq.Workplane:
    return model.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), rotation_deg).translate((0.0, 0.0, UPPER_TRANSLATION_Z_MM))


def build_drop_corridor_reference_only_phase3ie() -> cq.Workplane:
    return build_drop_corridor_reference_phase3ie(DROP_CORRIDOR_STRETCH_DIAMETER_MM, CORRECT_ROTATION_DEG)


def build_two_stage_direct_drop_reference_phase3ie(rotation_deg: float) -> cq.Workplane:
    solids: list[cq.Shape] = []
    full = build_integrated_stage_full_direct_drop_phase3ie()
    _append(solids, full)
    _append(solids, _transform_upper(full, rotation_deg))
    _append(solids, build_drop_corridor_reference_phase3ie(DROP_CORRIDOR_STRETCH_DIAMETER_MM, rotation_deg))

    water_surface = phase3ib._annulus(95.2, 54.8, 0.2, 26.0)
    _append(solids, water_surface)
    for angle in phase3ib.PORT_ANGLES_DEG:
        _append(solids, build_installed_netpot_reference_phase3ia(angle))
        _append(solids, build_keeper_installed_reference_phase3ib(angle))
        _append(solids, _transform_upper(build_installed_netpot_reference_phase3ia(angle), rotation_deg))
        _append(solids, _transform_upper(build_keeper_installed_reference_phase3ib(angle), rotation_deg))

    rear_post = cq.Workplane("XY").box(20.0, 20.0, 340.0, centered=(True, True, False)).translate((-150.0, 0.0, 0.0))
    _append(solids, rear_post)
    gauge = build_stack_clocking_gauge_30deg_phase3ie(REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM).translate((0.0, 0.0, 165.0))
    _append(solids, gauge)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def build_two_stage_direct_drop_correct_30deg_reference_phase3ie() -> cq.Workplane:
    return build_two_stage_direct_drop_reference_phase3ie(CORRECT_ROTATION_DEG)


def build_two_stage_direct_drop_wrong_0deg_reference_phase3ie() -> cq.Workplane:
    return build_two_stage_direct_drop_reference_phase3ie(WRONG_ROTATION_DEG)


def build_two_stage_direct_drop_wrong_60deg_reference_phase3ie() -> cq.Workplane:
    return build_two_stage_direct_drop_reference_phase3ie(COLLISION_ROTATION_DEG)


def _compound(models: list[cq.Workplane]) -> cq.Workplane:
    solids: list[cq.Shape] = []
    for model in models:
        _append(solids, model)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def drop_corridor_collision_audit_phase3ie() -> dict[str, object]:
    corridors = build_drop_corridor_reference_only_phase3ie()
    pots = _compound([build_installed_netpot_reference_phase3ia(angle) for angle in phase3ib.PORT_ANGLES_DEG])
    cradles = _compound([phase3ib.build_floor_connected_cradle_phase3ib(angle) for angle in phase3ib.PORT_ANGLES_DEG])
    lugs = _compound([
        build_isolated_retention_lug_net_phase3ic(angle, sign)
        for angle in phase3ib.PORT_ANGLES_DEG for sign in RETENTION_LUG_SIDE_SIGNS
    ])
    keepers = _compound([build_keeper_installed_reference_phase3ib(angle) for angle in phase3ib.PORT_ANGLES_DEG])
    wicks = _compound([phase3ib.build_wick_open_channel_phase3ib(angle) for angle in phase3ib.PORT_ANGLES_DEG])
    dam = phase3ib.build_real_inner_dam_phase3ib()
    ribs = _compound([build_internal_rib_phase3ia(angle) for angle in phase3ib.PORT_ANGLES_DEG])
    central = cq.Workplane("XY").circle(50.0).extrude(144.0).translate((0.0, 0.0, 26.0))
    rear_frame = cq.Workplane("XY").box(20.0, 20.0, 144.0, centered=(True, True, False)).translate((-150.0, 0.0, 26.0))
    root_mesh = _compound([
        cq.Workplane("XY").center(75.0, 0.0).circle(22.0).extrude(90.0).translate((0.0, 0.0, 45.0)).rotate((0, 0, 0), (0, 0, 1), angle)
        for angle in phase3ib.PORT_ANGLES_DEG
    ])
    guides = phase3ib.build_stacking_guides_phase3ib()
    outer_wall = phase3ib._annulus(100.0, 95.2, 144.0, 26.0)
    features = {
        "lower_netpot_references": pots,
        "lower_cradles": cradles,
        "lower_retention_lugs": lugs,
        "lower_keeper_references": keepers,
        "lower_wick_paths": wicks,
        "lower_inner_dam": dam,
        "lower_vertical_ribs": ribs,
        "lower_central_dry_opening": central,
        "rear_2020_frame_reference": rear_frame,
        "root_holding_mesh_assumed_regions": root_mesh,
        "stacking_guides": guides,
        "outer_wall": outer_wall,
    }
    intersections = {}
    for name, feature in features.items():
        common = corridors.intersect(feature).clean()
        intersections[name] = sum(s.Volume() for s in common.solids().vals())
    return {
        "corridor_count": len(corridors.solids().vals()),
        "stretch_diameter_mm": DROP_CORRIDOR_STRETCH_DIAMETER_MM,
        "intersections_mm3": intersections,
        "all_unintended_intersections_zero": all(value < 1.0e-6 for value in intersections.values()),
        "central_hole_intersection_mm3": intersections["lower_central_dry_opening"],
    }


def correct_wrong_assembly_audit_phase3ie() -> dict[str, object]:
    alignment = correct_wrong_alignment_audit_phase3ie()
    correct = build_two_stage_direct_drop_correct_30deg_reference_phase3ie()
    wrong = build_two_stage_direct_drop_wrong_0deg_reference_phase3ie()
    collision = build_two_stage_direct_drop_wrong_60deg_reference_phase3ie()
    return {
        **alignment,
        "correct_reference_only": True,
        "wrong_reference_only": True,
        "collision_reference_only": True,
        "correct_reference_solid_count": len(correct.solids().vals()),
        "wrong_reference_solid_count": len(wrong.solids().vals()),
        "collision_reference_solid_count": len(collision.solids().vals()),
        "upper_translation_z_mm": UPPER_TRANSLATION_Z_MM,
        "stage_functional_xy_envelope_limit_mm": 238.0,
        "external_rear_post_excluded_from_functional_envelope": True,
    }
