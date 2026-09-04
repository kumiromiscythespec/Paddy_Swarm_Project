"""Reference-only assembly and water-volume models for Phase 3I-A."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    OVERFLOW_WEIR_WIDTH_MM,
    SELECTED_OPERATING_DEPTH_MM,
    STACKING_SEAT_Z_MM,
    build_installed_netpot_reference_phase3ia,
    build_integrated_stage_full_phase3ia,
    build_water_volume_phase3ia,
)


ASSEMBLY_REFERENCE_ONLY = True
ASSEMBLY_REFERENCE_SOLID_COUNT = 9
WATER_VOLUME_REFERENCE_SOLID_COUNT = 4
LEGACY_REAR_FRAME_DIRECTION = "+Y"
PHASE3IA_REAR_SERVICE_DIRECTION = "-X"
LEGACY_TO_PHASE3IA_FRAME_ROTATION_DEG = 90.0


def _annular_floor_reference(z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(100.0)
        .circle(50.0)
        .extrude(4.0)
        .translate((0.0, 0.0, z))
    )


def build_integrated_stage_assembly_reference_phase3ia() -> cq.Workplane:
    shapes: list[cq.Shape] = [build_integrated_stage_full_phase3ia().val()]
    for angle in (0.0, 120.0, 240.0):
        shapes.append(build_installed_netpot_reference_phase3ia(angle).val())
    shapes.append(build_water_volume_phase3ia(SELECTED_OPERATING_DEPTH_MM).val())
    overflow_path = (
        cq.Workplane("XY")
        .box(8.0, OVERFLOW_WEIR_WIDTH_MM, 24.0, centered=(True, True, False))
        .translate((-108.0, 0.0, 4.0))
    )
    shapes.append(overflow_path.val())
    shapes.append(_annular_floor_reference(STACKING_SEAT_Z_MM).val())
    shapes.append(_annular_floor_reference(-STACKING_SEAT_Z_MM).val())
    rear_post = (
        cq.Workplane("XY")
        .box(20.0, 20.0, 498.0, centered=(True, True, False))
        .translate((-150.0, 0.0, -164.0))
    )
    shapes.append(rear_post.val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def build_integrated_stage_water_volume_reference_phase3ia() -> cq.Workplane:
    depths = (18.0, 19.0, 20.0, SELECTED_OPERATING_DEPTH_MM)
    offsets = (-360.0, -120.0, 120.0, 360.0)
    shapes = [
        build_water_volume_phase3ia(depth).translate((offset, 0.0, 0.0)).val()
        for depth, offset in zip(depths, offsets)
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def assembly_reference_metadata_phase3ia() -> dict[str, object]:
    return {
        "reference_only": True,
        "solid_count": ASSEMBLY_REFERENCE_SOLID_COUNT,
        "contains": [
            "ONE_INTEGRATED_STAGE",
            "THREE_MEASURED_NETPOT_ENVELOPES",
            "SELECTED_NORMAL_WATER_VOLUME",
            "OPEN_OVERFLOW_PATH",
            "UPPER_AND_LOWER_STACKING_DATUMS",
            "REAR_2020_POST",
        ],
        "coordinate_conversion": {
            "legacy_rear_frame_direction": LEGACY_REAR_FRAME_DIRECTION,
            "phase3ia_rear_service_direction": PHASE3IA_REAR_SERVICE_DIRECTION,
            "rotation_about_z_deg": LEGACY_TO_PHASE3IA_FRAME_ROTATION_DEG,
        },
    }
