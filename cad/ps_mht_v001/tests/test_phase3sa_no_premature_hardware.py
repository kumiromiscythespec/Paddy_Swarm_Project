"""Phase 3S-A scope fences against premature production features."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.assembly.three_sector_full_height_reference_phase3sa import (
    FULL_FIVE_STAGE_TOWER_INCLUDED,
)
from ps_mht_v001.common.phase3sa_nonregression import (
    phase3r2_generated_artifacts,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    IMPLEMENTED_DRAIN_OR_IRRIGATION_FEATURES,
    IMPLEMENTED_HARDWARE,
    IMPLEMENTED_SMALL_PART_COUNT,
    REFERENCE_DRAIN_ZONE,
)


EXPORT_ROOT = Path(__file__).resolve().parents[1] / "exports"


def test_no_small_independent_parts_are_implemented() -> None:
    assert IMPLEMENTED_SMALL_PART_COUNT == 0


def test_no_final_m4_nut_or_stack_hardware_is_implemented() -> None:
    assert IMPLEMENTED_HARDWARE == ()


def test_no_drain_or_irrigation_rail_is_implemented() -> None:
    assert IMPLEMENTED_DRAIN_OR_IRRIGATION_FEATURES == ()
    assert REFERENCE_DRAIN_ZONE == "REFERENCE_ONLY_NO_GEOMETRY"


def test_no_five_stage_tower_is_generated() -> None:
    assert FULL_FIVE_STAGE_TOWER_INCLUDED is False


def test_phase3r2_remains_documentation_only() -> None:
    assert phase3r2_generated_artifacts(EXPORT_ROOT) == ()
