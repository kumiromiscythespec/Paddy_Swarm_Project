"""Phase 3R.1 module envelope reference with the inward-fused frame."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import module_height, plant_port_local_angles
from ps_mht_v001.tower_module.port_backing_ring_phase3r import (
    build_port_backing_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    build_port_function_ring_phase3r,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    build_three_port_module_shell_phase3r1,
)


FULL_MODULE_REFERENCE_SOLID_COUNT = 7
PRINT_STATUS = "DO_NOT_PRINT_UNTIL_PHASE3R1_PHYSICAL_CALIBRATION"


def _orient_at_port(
    model: cq.Workplane,
    angle_deg: float,
    radial_position: float,
) -> cq.Workplane:
    angle = radians(angle_deg)
    return (
        model.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            63.0,
        )
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            angle_deg,
        )
        .translate(
            (
                radial_position * cos(angle),
                radial_position * sin(angle),
                0.5 * module_height,
            )
        )
    )


def build_full_module_reference_phase3r1() -> cq.Workplane:
    shapes: list[cq.Shape] = [build_three_port_module_shell_phase3r1().val()]
    for angle_deg in plant_port_local_angles:
        shapes.append(
            _orient_at_port(
                build_port_function_ring_phase3r(),
                angle_deg,
                85.4,
            ).val()
        )
        shapes.append(
            _orient_at_port(
                build_port_backing_ring_phase3r(),
                angle_deg,
                80.0,
            ).val()
        )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(shapes)]
    )
