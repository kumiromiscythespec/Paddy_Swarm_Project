"""Production-candidate Phase 3R.1 interface using one uniform nut clearance."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ps_mht_v001.assembly.module_interface_phase3r import (
    build_m4_bolt_references_phase3r,
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
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r1 import (
    build_module_nut_ring_phase3r1,
    production_pocket_clearances_phase3r1,
)


INTERFACE_REFERENCE_SOLID_COUNT = 9
ASSEMBLY_POLICY = "UNIFORM_NUT_CLEARANCE_ONLY_NO_CALIBRATION_COUPON"


@dataclass(frozen=True)
class Phase3R1InterfaceComponent:
    name: str
    model: cq.Workplane
    category: str
    nut_pocket_clearances: tuple[float, ...] = ()


def interface_components_phase3r1(
    nut_pocket_clearance: float,
    socket_rotation_deg: float = 0.0,
) -> tuple[Phase3R1InterfaceComponent, ...]:
    uniform = production_pocket_clearances_phase3r1(
        nut_pocket_clearance
    )
    components = [
        Phase3R1InterfaceComponent(
            "module_nut_ring_phase3r1",
            build_module_nut_ring_phase3r1(nut_pocket_clearance),
            "PRINTED_PETG_PRODUCTION_CANDIDATE",
            uniform,
        ),
        Phase3R1InterfaceComponent(
            "reference_metal_retaining_plate",
            build_module_nut_retaining_plate_reference_phase3r().translate(
                (0.0, 0.0, 7.0)
            ),
            "REFERENCE_METAL_PLATE",
        ),
        Phase3R1InterfaceComponent(
            "male_wave_alignment_ring",
            build_module_alignment_ring_phase3r().translate(
                (0.0, 0.0, 8.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3R1InterfaceComponent(
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
        Phase3R1InterfaceComponent(
            "module_gasket_ring",
            build_module_gasket_ring_phase3r().translate(
                (0.0, 0.0, 13.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3R1InterfaceComponent(
            "module_clamping_ring",
            build_module_clamping_ring_phase3r().translate(
                (0.0, 0.0, 19.0)
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
    ]
    for index, bolt in enumerate(build_m4_bolt_references_phase3r(), start=1):
        components.append(
            Phase3R1InterfaceComponent(
                f"m4_bolt_reference_{index}",
                bolt,
                "PURCHASED_M4_REFERENCE",
            )
        )
    return tuple(components)


def build_module_interface_phase3r1(
    nut_pocket_clearance: float,
    socket_rotation_deg: float = 0.0,
) -> cq.Workplane:
    components = interface_components_phase3r1(
        nut_pocket_clearance,
        socket_rotation_deg,
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [component.model.val() for component in components]
            )
        ]
    )
