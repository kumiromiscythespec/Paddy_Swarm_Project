"""Non-printable c040/c060 full-length seam assembly reference."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.coupons.full_length_seam_pair_phase3sa2 import (
    SHARED_SEAM_ANGLE_DEG,
    full_length_seam_assembly_pieces_phase3sa2,
)
from ps_mht_v001.parameters import (
    phase3sa2_effective_seam_length,
)
from ps_mht_v001.tower_module.full_length_seam_capture_fixture_phase3sa2 import (
    GROOVE_FLOOR_MM,
    build_full_length_seam_capture_fixture_phase3sa2,
)


STATUS = "PHASE3SA2_REFERENCE_ONLY_DO_NOT_PRINT_AS_ASSEMBLY"
ASSEMBLY_SOLID_COUNT = 8
CANDIDATE_REFERENCE_SPACING_MM = 280.0


def build_one_candidate_reference_phase3sa2(
    seam_clearance: float,
) -> cq.Workplane:
    pieces = [
        piece.translate((0.0, 0.0, GROOVE_FLOOR_MM))
        for piece in full_length_seam_assembly_pieces_phase3sa2(
            seam_clearance
        )
    ]
    lower = build_full_length_seam_capture_fixture_phase3sa2()
    angle = radians(SHARED_SEAM_ANGLE_DEG)
    upper = (
        build_full_length_seam_capture_fixture_phase3sa2()
        .rotate(
            (0.0, 0.0, 0.0),
            (cos(angle), sin(angle), 0.0),
            180.0,
        )
        .translate(
            (
                0.0,
                0.0,
                phase3sa2_effective_seam_length
                + 2.0 * GROOVE_FLOOR_MM,
            )
        )
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [pieces[0].val(), pieces[1].val(), lower.val(), upper.val()]
            )
        ]
    )


def build_full_length_seam_calibration_reference_phase3sa2() -> cq.Workplane:
    c040 = build_one_candidate_reference_phase3sa2(0.4)
    c060 = build_one_candidate_reference_phase3sa2(0.6).translate(
        (CANDIDATE_REFERENCE_SPACING_MM, 0.0, 0.0)
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [*c040.solids().vals(), *c060.solids().vals()]
            )
        ]
    )
