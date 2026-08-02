"""One-axis Phase 3R split planting-port assembly."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    plant_port_angle,
    port_function_ring_fastener_pitch,
    port_shell_coupon_height,
)
from ps_mht_v001.tower_module.netpot_seat_ring_phase3r import (
    build_netpot_seat_ring_phase3r,
    build_siawadeky_netpot_reference_phase3r,
)
from ps_mht_v001.tower_module.port_backing_ring_phase3r import (
    build_port_backing_metal_washer_reference_phase3r,
    build_port_backing_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    build_port_function_ring_phase3r,
)
from ps_mht_v001.tower_module.port_gasket_ring_phase3r import (
    build_port_gasket_ring_phase3r,
)
from ps_mht_v001.tower_module.root_sleeve_ring_phase3r import (
    build_root_mesh_bag_reference_phase3r,
    build_root_sleeve_ring_phase3r,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r import (
    build_self_supporting_port_shell_coupon_phase3r,
)


PORT_Z = 0.5 * port_shell_coupon_height
PORT_AXIS_TILT_FROM_Z = 90.0 - plant_port_angle


@dataclass(frozen=True)
class Phase3RPortComponent:
    name: str
    model: cq.Workplane
    category: str


def orient_flat_part_to_port_axis(
    model: cq.Workplane,
    radial_position: float,
    exploded_offset: float = 0.0,
) -> cq.Workplane:
    return (
        model.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            PORT_AXIS_TILT_FROM_Z,
        )
        .translate(
            (
                radial_position
                + exploded_offset,
                0.0,
                PORT_Z,
            )
        )
    )


def _m4_port_bolt(side: int) -> cq.Workplane:
    return orient_flat_part_to_port_axis(
        cq.Workplane("XY")
        .center(0.0, side * port_function_ring_fastener_pitch)
        .circle(0.5 * m4_clearance_diameter)
        .extrude(28.0),
        84.0,
    )


def port_components_phase3r(
    exploded_gap: float = 0.0,
) -> tuple[Phase3RPortComponent, ...]:
    netpot = (
        build_siawadeky_netpot_reference_phase3r()
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
    )
    components = [
        Phase3RPortComponent(
            "self_supporting_tower_shell",
            build_self_supporting_port_shell_coupon_phase3r(),
            "PRINTED_SHELL_COUPON",
        ),
        Phase3RPortComponent(
            "port_backing_c_ring",
            orient_flat_part_to_port_axis(
                build_port_backing_ring_phase3r(),
                88.0,
                -3.0 * exploded_gap,
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RPortComponent(
            "port_metal_washer_references",
            orient_flat_part_to_port_axis(
                build_port_backing_metal_washer_reference_phase3r(),
                94.0,
                -2.0 * exploded_gap,
            ),
            "PURCHASED_METAL_REFERENCE",
        ),
        Phase3RPortComponent(
            "port_gasket_ring",
            orient_flat_part_to_port_axis(
                build_port_gasket_ring_phase3r(),
                94.0,
                -exploded_gap,
            ),
            "TPU_OR_EPDM",
        ),
        Phase3RPortComponent(
            "port_function_ring",
            orient_flat_part_to_port_axis(
                build_port_function_ring_phase3r(),
                96.0,
                0.0,
            ),
            "PRINTED_PETG_FLAT_CIRCULAR_DATUM",
        ),
        Phase3RPortComponent(
            "replaceable_netpot_seat_ring",
            orient_flat_part_to_port_axis(
                build_netpot_seat_ring_phase3r(),
                104.0,
                exploded_gap,
            ),
            "PRINTED_PETG_PRELIMINARY_LINER",
        ),
        Phase3RPortComponent(
            "siawadeky_netpot_reference",
            orient_flat_part_to_port_axis(
                netpot,
                116.0,
                2.0 * exploded_gap,
            ),
            "PURCHASED_PART_REFERENCE",
        ),
        Phase3RPortComponent(
            "root_sleeve_foldover_ring",
            orient_flat_part_to_port_axis(
                build_root_sleeve_ring_phase3r(),
                84.0,
                -4.0 * exploded_gap,
            ),
            "PRINTED_PETG_LARGE_RING",
        ),
        Phase3RPortComponent(
            "root_mesh_bag_reference",
            orient_flat_part_to_port_axis(
                build_root_mesh_bag_reference_phase3r(),
                84.0,
                -5.0 * exploded_gap,
            ),
            "PURCHASED_PP_OR_PE_REFERENCE",
        ),
    ]
    for side in (-1, 1):
        components.append(
            Phase3RPortComponent(
                f"m4_bolt_reference_{side:+d}",
                _m4_port_bolt(side),
                "PURCHASED_M4_REFERENCE",
            )
        )
    return tuple(components)


def build_planting_port_phase3r(
    exploded_gap: float = 0.0,
) -> cq.Workplane:
    components = port_components_phase3r(exploded_gap)
    shapes: list[cq.Shape] = []
    for component in components:
        shapes.extend(component.model.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
