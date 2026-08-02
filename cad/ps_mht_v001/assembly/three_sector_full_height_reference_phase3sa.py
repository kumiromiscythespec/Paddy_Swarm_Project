"""Full-height three-identical-panel Phase 3S-A geometry reference."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.three_sector_short_assembly_phase3sa import (
    PANEL_BOTTOM_Z_MM,
)
from ps_mht_v001.parameters import (
    phase3sa_panel_height,
    phase3sa_sector_count,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_sector_panel_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    REFERENCE_EXTERNAL_BAND,
    build_external_band_reference_phase3sa,
    build_temporary_panel_capture_ring_phase3sa,
)


STATUS = "PHASE3SA_FULL_HEIGHT_REFERENCE_DO_NOT_PRINT_AS_ASSEMBLY"
ASSEMBLY_SOLID_COUNT = 6
FULL_FIVE_STAGE_TOWER_INCLUDED = False


def full_height_panel_models_phase3sa(
    seam_clearance: float,
) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    clearance = validate_seam_clearance_phase3sa(seam_clearance)
    source = build_sector_panel_phase3sa(
        clearance,
        phase3sa_panel_height,
    ).translate((0.0, 0.0, PANEL_BOTTOM_Z_MM))
    return tuple(
        source.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            index * 360.0 / phase3sa_sector_count,
        )
        for index in range(phase3sa_sector_count)
    )


def build_three_sector_full_height_reference_phase3sa(
    seam_clearance: float,
) -> cq.Workplane:
    panels = full_height_panel_models_phase3sa(seam_clearance)
    lower_ring = build_temporary_panel_capture_ring_phase3sa()
    top_reference_z = PANEL_BOTTOM_Z_MM + phase3sa_panel_height + 3.0
    upper_ring = (
        build_temporary_panel_capture_ring_phase3sa()
        .rotate(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            180.0,
        )
        .translate((0.0, 0.0, top_reference_z))
    )
    band = build_external_band_reference_phase3sa(
        PANEL_BOTTOM_Z_MM + 0.5 * phase3sa_panel_height
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [
                    *(panel.val() for panel in panels),
                    lower_ring.val(),
                    upper_ring.val(),
                    band.val(),
                ]
            )
        ]
    )


def full_height_reference_component_policy_phase3sa() -> dict[str, object]:
    return {
        "panel_source_count": 1,
        "panel_instance_count": 3,
        "panel_rotations_deg": (0.0, 120.0, 240.0),
        "port_centers_deg": (0.0, 120.0, 240.0),
        "seam_centers_deg": (60.0, 180.0, 300.0),
        "temporary_ring_count": 2,
        "external_band": REFERENCE_EXTERNAL_BAND,
        "full_five_stage_tower": False,
    }
