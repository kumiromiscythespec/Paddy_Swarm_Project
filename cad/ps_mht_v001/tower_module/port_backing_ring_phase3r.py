"""Large internally serviced C-ring nut plate for a Phase 3R port."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    m4_nut_across_flats,
    m4_nut_thickness,
    module_nut_pocket_selected_clearance,
    port_backing_ring_inner_diameter,
    port_backing_ring_outer_diameter,
    port_backing_ring_thickness,
    port_function_ring_fastener_pitch,
)


STATUS = "PHASE3R_MODULE_DISASSEMBLY_SERVICE_RING"
PRINT_ORIENTATION = "FLAT_ON_CONTINUOUS_C_RING_FACE"
SERVICE_POLICY = "REPLACE_RING_WHEN_MODULE_IS_DISASSEMBLED"
NUT_POCKET_COUNT = 2


def build_port_backing_ring_phase3r() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * port_backing_ring_outer_diameter)
        .circle(0.5 * port_backing_ring_inner_diameter)
        .extrude(port_backing_ring_thickness)
    )
    # Broad -X drain/wash gap; this deliberately avoids a closed root shelf.
    drain_gap = (
        cq.Workplane("XY")
        .box(
            0.5 * port_backing_ring_outer_diameter + 4.0,
            30.0,
            port_backing_ring_thickness + 2.0,
            centered=(False, True, False),
        )
        .translate(
            (
                -0.5 * port_backing_ring_outer_diameter - 2.0,
                0.0,
                -1.0,
            )
        )
    )
    ring = ring.cut(drain_gap)
    nut_circumscribed = (
        m4_nut_across_flats / 0.8660254037844386
        + 2.0 * module_nut_pocket_selected_clearance
    )
    for y in (-port_function_ring_fastener_pitch, port_function_ring_fastener_pitch):
        through = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(port_backing_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        pocket = (
            cq.Workplane("XY")
            .center(0.0, y)
            .polygon(6, nut_circumscribed)
            .extrude(m4_nut_thickness + 0.8)
            .translate(
                (
                    0.0,
                    0.0,
                    port_backing_ring_thickness - m4_nut_thickness - 0.8,
                )
            )
        )
        ring = ring.cut(through).cut(pocket)
    return ring


def build_port_backing_metal_washer_reference_phase3r() -> cq.Workplane:
    washers: list[cq.Shape] = []
    for y in (-port_function_ring_fastener_pitch, port_function_ring_fastener_pitch):
        washer = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(6.0)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(1.0)
        )
        washers.append(washer.val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(washers)])


def build_backing_ring_root_passage_probe_phase3r() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(40.0)
        .extrude(port_backing_ring_thickness + 2.0)
        .translate((0.0, 0.0, -1.0))
    )


def build_backing_ring_drain_service_probe_phase3r() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(20.0, 20.0, port_backing_ring_thickness + 2.0)
        .translate((-50.0, 0.0, -1.0))
    )
