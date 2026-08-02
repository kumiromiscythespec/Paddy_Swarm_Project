"""Phase 2 replaceable 3 mm TPU/EPDM cord-ring reference."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    gasket_cord_diameter,
    gasket_groove_depth,
    interface_spigot_outer_diameter,
)


def gasket_major_radius() -> float:
    """Major radius that seats a 3 mm cord in the radial spigot groove."""

    spigot_outer_radius = 0.5 * interface_spigot_outer_diameter
    groove_bottom_radius = spigot_outer_radius - gasket_groove_depth
    return groove_bottom_radius + 0.5 * gasket_cord_diameter


def build_module_gasket() -> cq.Workplane:
    """Build the non-pressurized radial cord-ring reference."""

    torus = cq.Solid.makeTorus(
        gasket_major_radius(),
        0.5 * gasket_cord_diameter,
    )
    return cq.Workplane("XY").newObject([torus])
