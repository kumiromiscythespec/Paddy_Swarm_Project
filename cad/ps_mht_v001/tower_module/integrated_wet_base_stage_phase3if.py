"""Phase 3I-F full module: the 30-degree direct-drop module has no frame boss."""

from __future__ import annotations

from functools import lru_cache

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ie import (
    actual_water_volume_audit_phase3ie,
    build_integrated_stage_full_direct_drop_phase3ie,
    geometry_audit_phase3ie,
    maximum_xy_diameter_phase3ie,
)


PHASE3IF_ARCHITECTURE = "THIRTY_DEGREE_DIRECT_DROP_WITH_NON_ROTATING_DRY_CORE_FRAME"
LEGACY_LOCAL_MINUS_X_FIXING_INTERFACE = "SUPERSEDED_BY_NON_ROTATING_DRY_CORE_FRAME"
MODULE_FRAME_BOSS_ADDED = False
FULL_PRINT_STATUS = "SLICER_REVIEW_ONLY_DO_NOT_PRINT"


@lru_cache(maxsize=1)
def build_integrated_stage_full_direct_drop_phase3if() -> cq.Workplane:
    return build_integrated_stage_full_direct_drop_phase3ie()


def geometry_audit_phase3if() -> dict[str, object]:
    full = build_integrated_stage_full_direct_drop_phase3if()
    inherited = geometry_audit_phase3ie()
    return {
        "architecture": PHASE3IF_ARCHITECTURE,
        "phase3ie_30deg_geometry_reused": True,
        "legacy_local_minus_x_fixing_interface": LEGACY_LOCAL_MINUS_X_FIXING_INTERFACE,
        "module_frame_boss_added": MODULE_FRAME_BOSS_ADDED,
        "solid_count": len(full.solids().vals()),
        "valid": full.val().isValid(),
        "maximum_xy_diameter_mm": maximum_xy_diameter_phase3ie(full),
        "maximum_allowed_xy_mm": 238.0,
        "phase3ie_geometry": inherited,
        "actual_water_volume": actual_water_volume_audit_phase3ie(),
        "wet_wall_penetration_added": False,
        "print_status": FULL_PRINT_STATUS,
    }
