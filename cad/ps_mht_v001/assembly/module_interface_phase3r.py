"""Phase 3R large-ring module-interface assembly references."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    phase3r_m4_pitch_radius,
    used_fastener_angles,
)
from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    build_module_alignment_ring_phase3r,
    build_module_alignment_socket_ring_phase3r,
)
from ps_mht_v001.tower_module.module_clamping_ring_phase3r import (
    build_module_clamping_ring_phase3r,
)
from ps_mht_v001.tower_module.module_gasket_ring_phase3r import (
    build_module_gasket_ring_phase3r,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r import (
    build_module_nut_retaining_plate_reference_phase3r,
    build_module_nut_ring_phase3r,
)


INTERFACE_REFERENCE_SOLID_COUNT = 9
LOAD_PATH = "BROAD_ANNULAR_CONTACT_NOT_M4_BOLTS_ALONE"


@dataclass(frozen=True)
class Phase3RInterfaceComponent:
    name: str
    model: cq.Workplane
    category: str


def build_m4_bolt_references_phase3r(
    z: float = -3.0,
    height: float = 30.0,
) -> tuple[cq.Workplane, ...]:
    bolts: list[cq.Workplane] = []
    for angle_deg in used_fastener_angles:
        angle = radians(angle_deg)
        x = phase3r_m4_pitch_radius * cos(angle)
        y = phase3r_m4_pitch_radius * sin(angle)
        bolts.append(
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(height)
            .translate((0.0, 0.0, z))
        )
    return tuple(bolts)


def interface_components_phase3r(
    socket_rotation_deg: float = 0.0,
) -> tuple[Phase3RInterfaceComponent, ...]:
    components = [
        Phase3RInterfaceComponent(
            "module_nut_ring",
            build_module_nut_ring_phase3r(),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RInterfaceComponent(
            "reference_metal_retaining_plate",
            build_module_nut_retaining_plate_reference_phase3r().translate(
                (0.0, 0.0, 7.0)
            ),
            "REFERENCE_METAL_PLATE",
        ),
        Phase3RInterfaceComponent(
            "male_wave_alignment_ring",
            build_module_alignment_ring_phase3r().translate(
                (0.0, 0.0, 8.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RInterfaceComponent(
            "female_wave_socket_ring",
            build_module_alignment_socket_ring_phase3r()
            .rotate(
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                socket_rotation_deg,
            )
            .translate((0.0, 0.0, 8.0)),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RInterfaceComponent(
            "module_gasket_ring",
            build_module_gasket_ring_phase3r().translate(
                (0.0, 0.0, 13.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RInterfaceComponent(
            "module_clamping_ring",
            build_module_clamping_ring_phase3r().translate(
                (0.0, 0.0, 19.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
    ]
    for index, bolt in enumerate(build_m4_bolt_references_phase3r(), start=1):
        components.append(
            Phase3RInterfaceComponent(
                f"m4_bolt_reference_{index}",
                bolt,
                "PURCHASED_M4_REFERENCE",
            )
        )
    return tuple(components)


def build_module_interface_phase3r(
    socket_rotation_deg: float = 0.0,
) -> cq.Workplane:
    components = interface_components_phase3r(socket_rotation_deg)
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [component.model.val() for component in components]
            )
        ]
    )
