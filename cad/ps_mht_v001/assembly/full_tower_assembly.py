"""Phase 1 five-module tower and simplified frame assembly."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ps_mht_v001.frame.aluminum_base import build_base_parts
from ps_mht_v001.frame.rear_post import build_rear_post
from ps_mht_v001.parameters import (
    drain_base_height,
    irrigation_top_height,
    module_count,
    module_height,
    module_placements,
    tower_body_diameter,
    tower_nominal_height,
)
from ps_mht_v001.tower_module.planting_module import build_planting_module


@dataclass(frozen=True)
class AssemblyComponent:
    """Named assembly component with explicit status metadata."""

    name: str
    model: cq.Workplane
    category: str
    printable: bool
    status: str


def _reference_cylinder(height: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * tower_body_diameter)
        .extrude(height)
    )


def tower_components() -> tuple[AssemblyComponent, ...]:
    """Return drain/top envelopes and five independently placed modules."""

    components: list[AssemblyComponent] = [
        AssemblyComponent(
            "drain_base_phase1_envelope",
            _reference_cylinder(drain_base_height),
            "REFERENCE_ENVELOPE",
            False,
            "PHASE_4_PENDING",
        )
    ]
    for placement in module_placements():
        model = (
            build_planting_module()
            .rotate(
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                placement.rotation_deg,
            )
            .translate((0.0, 0.0, placement.z_bottom))
        )
        components.append(
            AssemblyComponent(
                f"module_{placement.module_number:02d}",
                model,
                "PRINTED_PETG",
                True,
                "PHASE_1_GENERATED",
            )
        )

    top_height = irrigation_top_height
    components.append(
        AssemblyComponent(
            "irrigation_top_phase1_envelope",
            _reference_cylinder(top_height).translate(
                (
                    0.0,
                    0.0,
                    drain_base_height + module_count * module_height,
                )
            ),
            "REFERENCE_ENVELOPE",
            False,
            "PHASE_5_PENDING",
        )
    )
    return tuple(components)


def frame_components() -> tuple[AssemblyComponent, ...]:
    """Return the purchased base pieces and rear post."""

    components = [
        AssemblyComponent(
            part.name,
            part.model,
            part.material,
            False,
            "PURCHASED_REFERENCE",
        )
        for part in build_base_parts()
    ]
    components.append(
        AssemblyComponent(
            "rear_post_2020_1250",
            build_rear_post(),
            "PURCHASED_2020_ALUMINIUM",
            False,
            "PURCHASED_REFERENCE",
        )
    )
    return tuple(components)


def _compound(components: tuple[AssemblyComponent, ...]) -> cq.Workplane:
    compound = cq.Compound.makeCompound(
        [component.model.val() for component in components]
    )
    return cq.Workplane("XY").newObject([compound])


def build_tower_only_model() -> cq.Workplane:
    """Build the seven-solid nominal 1090 mm tower reference."""

    return _compound(tower_components())


def build_frame_model() -> cq.Workplane:
    """Build the seven-solid purchased aluminium frame reference."""

    return _compound(frame_components())


def build_full_tower_model() -> cq.Workplane:
    """Build the 14-solid Phase 1 tower-plus-frame reference."""

    return _compound(frame_components() + tower_components())


def build_cq_assembly() -> cq.Assembly:
    """Build a named/colorized assembly for CQ-editor or notebook viewing."""

    assembly = cq.Assembly(name="PS-MHT-V001_PHASE1")
    colors = {
        "PRINTED_PETG": cq.Color(0.92, 0.94, 0.96, 1.0),
        "REFERENCE_ENVELOPE": cq.Color(0.3, 0.65, 0.9, 0.35),
        "PURCHASED_2020_ALUMINIUM": cq.Color(0.55, 0.58, 0.62, 1.0),
        "PURCHASED_ALUMINIUM_PLATE": cq.Color(0.68, 0.70, 0.73, 1.0),
    }
    for component in frame_components() + tower_components():
        assembly.add(
            component.model,
            name=component.name,
            color=colors.get(component.category, cq.Color(0.7, 0.7, 0.7)),
        )
    return assembly
