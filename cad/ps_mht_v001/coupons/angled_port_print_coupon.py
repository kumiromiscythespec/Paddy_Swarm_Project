"""Vertical-print shell section containing the real 27-degree port root."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.planting_port import (
    build_planting_module_with_ports_phase3a,
)


COUPON_SOLID_COUNT = 1
STATUS = "DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE"
PRINT_ORIENTATION = "TOWER_AXIS_VERTICAL"
SUPPORT_EVALUATION = "CALIBRATION_PENDING"


def build_angled_port_print_coupon() -> cq.Workplane:
    """Cut a short actual shell/saddle/bore section around the 0-degree port."""

    cutter = (
        cq.Workplane("XY")
        .box(58.0, 104.0, 104.0, centered=(True, True, False))
        .translate((91.0, 0.0, 33.0))
    )
    return build_planting_module_with_ports_phase3a().intersect(cutter)
