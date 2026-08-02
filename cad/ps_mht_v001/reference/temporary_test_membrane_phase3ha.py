"""Non-printable temporary membrane reference for Phase 3H-A leak tests."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    horizontal_joint_nominal_outer_diameter,
    phase3ha_test_membrane_status,
)


MATERIAL = "PURCHASED_PE_OR_SILICONE_SHEET"
PRINT_STATUS = "REFERENCE_ONLY_DO_NOT_PRINT"
THICKNESS_REFERENCE_MM = 0.5


def build_temporary_test_membrane_reference_phase3ha() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * horizontal_joint_nominal_outer_diameter)
        .extrude(THICKNESS_REFERENCE_MM)
    )


def temporary_test_membrane_requirements_phase3ha() -> dict[str, object]:
    return {
        "status": phase3ha_test_membrane_status,
        "material": MATERIAL,
        "print_status": PRINT_STATUS,
        "diameter_reference_mm": horizontal_joint_nominal_outer_diameter,
        "thickness_reference_mm": THICKNESS_REFERENCE_MM,
        "joint_leak_and_membrane_leak_must_be_distinguished": True,
        "printed_bottom_wall_used": False,
    }
