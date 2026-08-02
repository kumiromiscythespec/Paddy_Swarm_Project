"""Phase 1 planting-module outer shell.

Plant ports, drainage floor, fasteners, gasket groove, and keyed interfaces are
intentionally absent until their designated phases. The current open tube is a
manufacturable envelope and does not claim water-tight operation.
"""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    module_height,
    module_wall_thickness,
    phase1_datum_groove_bottom,
    phase1_datum_groove_depth,
    phase1_datum_groove_height,
    phase1_datum_groove_width,
    tower_body_diameter,
)


def build_planting_module() -> cq.Workplane:
    """Build the Phase 1 open cylindrical PETG shell as one solid."""

    outer_radius = 0.5 * tower_body_diameter
    inner_radius = outer_radius - module_wall_thickness
    shell = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(module_height)
    )

    # A shallow, non-through groove makes 0/60-degree assembly rotation visible.
    groove = (
        cq.Workplane("XY")
        .box(
            phase1_datum_groove_width,
            2.0 * phase1_datum_groove_depth,
            phase1_datum_groove_height,
            centered=(True, True, False),
        )
        .translate(
            (
                0.0,
                outer_radius,
                phase1_datum_groove_bottom,
            )
        )
    )
    return shell.cut(groove)


def minimum_wall_at_phase1_datum() -> float:
    """Return the remaining shell wall at the temporary orientation groove."""

    return module_wall_thickness - phase1_datum_groove_depth

