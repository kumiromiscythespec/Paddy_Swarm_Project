"""Reference-only assembly, purchased parts, cord, and real water for Phase 3I-B."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    C_KEEPER_THICKNESS_MM,
    OPERATING_WATER_DEPTH_CANDIDATES_MM,
    OVERFLOW_CREST_Z_MM,
    SELECTED_OPERATING_WATER_DEPTH_MM,
    SELECTED_OVERFLOW_WEIR_WIDTH_MM,
    build_actual_water_volume_phase3ib,
    build_c_shaped_flange_keeper_phase3ib,
    build_integrated_stage_full_phase3ib,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    build_installed_netpot_reference_phase3ia,
)


ASSEMBLY_REFERENCE_ONLY = True
WATER_REFERENCE_ONLY = True


def _orient_local_reference(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    from math import cos, radians, sin

    angle = radians(angle_deg)
    return (
        model.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 63.0)
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        .translate((83.4 * cos(angle), 83.4 * sin(angle), 85.0))
    )


def build_rope_reference_phase3ib(angle_deg: float) -> cq.Workplane:
    local = (
        cq.Workplane("XZ", origin=(-45.0, 0.0, 13.0))
        .circle(2.5)
        .extrude(36.0, both=True)
    )
    return _orient_local_reference(local, angle_deg)


def build_keeper_installed_reference_phase3ib(angle_deg: float) -> cq.Workplane:
    local = build_c_shaped_flange_keeper_phase3ib().translate((0.0, 0.0, 12.5))
    return _orient_local_reference(local, angle_deg)


def _append_solids(shapes: list[cq.Shape], model: cq.Workplane) -> None:
    shapes.extend(model.solids().vals())


def build_integrated_stage_assembly_reference_phase3ib() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    _append_solids(shapes, build_integrated_stage_full_phase3ib())
    for angle in (0.0, 120.0, 240.0):
        _append_solids(shapes, build_installed_netpot_reference_phase3ia(angle))
        _append_solids(shapes, build_rope_reference_phase3ib(angle))
        _append_solids(shapes, build_keeper_installed_reference_phase3ib(angle))
    _append_solids(shapes, build_actual_water_volume_phase3ib(SELECTED_OPERATING_WATER_DEPTH_MM))
    overflow_flow = (
        cq.Workplane("XY")
        .box(28.0, SELECTED_OVERFLOW_WEIR_WIDTH_MM - 4.0, 6.0, centered=(True, True, False))
        .translate((-112.0, 0.0, OVERFLOW_CREST_Z_MM))
    )
    _append_solids(shapes, overflow_flow)
    for z in (-170.0, 170.0):
        datum = cq.Workplane("XY").circle(100.0).circle(50.0).extrude(2.0).translate((0.0, 0.0, z))
        _append_solids(shapes, datum)
    rear_post = (
        cq.Workplane("XY")
        .box(20.0, 20.0, 510.0, centered=(True, True, False))
        .translate((-150.0, 0.0, -170.0))
    )
    _append_solids(shapes, rear_post)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def build_actual_water_volume_reference_phase3ib() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    for index, depth in enumerate(OPERATING_WATER_DEPTH_CANDIDATES_MM):
        water = build_actual_water_volume_phase3ib(depth).translate(((index - 1) * 240.0, 0.0, 0.0))
        _append_solids(shapes, water)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def assembly_reference_metadata_phase3ib() -> dict[str, object]:
    assembly = build_integrated_stage_assembly_reference_phase3ib()
    waters = build_actual_water_volume_reference_phase3ib()
    return {
        "reference_only": True,
        "assembly_solid_count": len(assembly.solids().vals()),
        "water_reference_solid_count": len(waters.solids().vals()),
        "contains": [
            "ONE_CORRECTED_MODULE",
            "THREE_MEASURED_NETPOT_REFERENCES",
            "THREE_5MM_VINYL_ROPE_REFERENCES",
            "THREE_OPTIONAL_C_KEEPER_REFERENCES",
            "SELECTED_ACTUAL_WATER_VOLUME",
            "OPEN_OVERFLOW_FLOW_REFERENCE",
            "UPPER_AND_LOWER_STAGE_DATUMS",
            "REAR_POST_REFERENCE",
        ],
    }

