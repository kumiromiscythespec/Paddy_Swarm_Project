"""Full-height single panel in its recommended Phase 3S-A print posture."""

from __future__ import annotations

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.parameters import phase3sa_panel_height
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_sector_panel_phase3sa,
)


STATUS = "PHASE3SA_SINGLE_PANEL_PRINT_GATE"
PRINT_QUANTITY_BEFORE_SHORT_ASSEMBLY = 1


def build_sector_panel_print_coupon_phase3sa(
    seam_clearance: float,
):
    panel = build_sector_panel_phase3sa(
        seam_clearance,
        phase3sa_panel_height,
    )
    return orient_sector_for_print_phase3sa(panel)
