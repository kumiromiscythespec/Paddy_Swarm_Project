"""Short three-panel Phase 3S-A seam and circularity calibration assembly."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    phase3sa_sector_count,
    phase3sa_short_panel_height,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    BLANK_REFERENCE_STATUS,
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    REFERENCE_EXTERNAL_BAND,
    RING_HEIGHT_MM,
    build_external_band_reference_phase3sa,
    build_temporary_panel_capture_ring_phase3sa,
)


STATUS = "PHASE3SA_SHORT_CALIBRATION_ASSEMBLY_NOT_PRODUCTION_MODULE"
ASSEMBLY_SOLID_COUNT = 6
PANEL_BOTTOM_Z_MM = 3.0
PANEL_ROLE = BLANK_REFERENCE_STATUS


@dataclass(frozen=True)
class ShortAssemblyComponentPhase3SA:
    name: str
    model: cq.Workplane
    category: str
    source_model: str


def short_panel_models_phase3sa(
    seam_clearance: float,
) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    clearance = validate_seam_clearance_phase3sa(seam_clearance)
    source = build_blank_sector_panel_calibration_reference_phase3sa(
        clearance,
        phase3sa_short_panel_height,
    ).translate((0.0, 0.0, PANEL_BOTTOM_Z_MM))
    return tuple(
        source.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            index * 360.0 / phase3sa_sector_count,
        )
        for index in range(phase3sa_sector_count)
    )


def short_assembly_components_phase3sa(
    seam_clearance: float,
) -> tuple[ShortAssemblyComponentPhase3SA, ...]:
    panels = short_panel_models_phase3sa(seam_clearance)
    lower_ring = build_temporary_panel_capture_ring_phase3sa()
    top_reference_z = (
        PANEL_BOTTOM_Z_MM
        + phase3sa_short_panel_height
        + 3.0
    )
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
        PANEL_BOTTOM_Z_MM + 0.5 * phase3sa_short_panel_height
    )
    components: list[ShortAssemblyComponentPhase3SA] = []
    for index, panel in enumerate(panels, start=1):
        components.append(
            ShortAssemblyComponentPhase3SA(
                f"blank_calibration_panel_{index}",
                panel,
                "PRINTED_PETG_COUPON_REFERENCE",
                "IDENTICAL_BLANK_PANEL_SOURCE",
            )
        )
    components.extend(
        (
            ShortAssemblyComponentPhase3SA(
                "temporary_lower_capture_ring",
                lower_ring,
                "PRINTED_PETG_TEMPORARY",
                "IDENTICAL_CAPTURE_RING_SOURCE",
            ),
            ShortAssemblyComponentPhase3SA(
                "temporary_upper_capture_ring",
                upper_ring,
                "PRINTED_PETG_TEMPORARY",
                "IDENTICAL_CAPTURE_RING_SOURCE",
            ),
            ShortAssemblyComponentPhase3SA(
                "reference_external_band",
                band,
                "PURCHASED_REFERENCE_NOT_PRINTED",
                REFERENCE_EXTERNAL_BAND,
            ),
        )
    )
    return tuple(components)


def build_three_sector_short_assembly_phase3sa(
    seam_clearance: float,
) -> cq.Workplane:
    components = short_assembly_components_phase3sa(seam_clearance)
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [component.model.val() for component in components]
            )
        ]
    )


def build_three_sector_short_exploded_phase3sa(
    seam_clearance: float,
) -> cq.Workplane:
    components = short_assembly_components_phase3sa(seam_clearance)
    shapes: list[cq.Shape] = []
    for index, component in enumerate(components[:3]):
        angle = radians(index * 120.0)
        shapes.append(
            component.model.translate(
                (30.0 * cos(angle), 30.0 * sin(angle), 0.0)
            ).val()
        )
    shapes.append(components[3].model.translate((0.0, 0.0, -20.0)).val())
    shapes.append(components[4].model.translate((0.0, 0.0, 20.0)).val())
    shapes.append(components[5].model.val())
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(shapes)]
    )
