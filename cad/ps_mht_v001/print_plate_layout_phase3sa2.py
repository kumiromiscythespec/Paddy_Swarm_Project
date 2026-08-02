"""Bambu Lab A1 plates for Phase 3S-A.2 full-length seam tests."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.coupons.full_length_seam_pair_phase3sa2 import (
    PART_SPACING_MM,
    build_full_length_seam_pair_phase3sa2,
    full_length_seam_print_pieces_phase3sa2,
)
from ps_mht_v001.tower_module.full_length_seam_capture_fixture_phase3sa2 import (
    build_full_length_seam_capture_fixture_phase3sa2,
)


STATUS = "PHASE3SA2_THREE_REQUIRED_A1_PLATES"


def _normalize(model: cq.Workplane) -> cq.Workplane:
    box = model.val().BoundingBox()
    return model.translate((-box.xmin, -box.ymin, -box.zmin))


def build_plate_01_full_length_seam_c040_phase3sa2() -> cq.Workplane:
    return build_full_length_seam_pair_phase3sa2(0.4)


def build_plate_02_full_length_seam_c060_phase3sa2() -> cq.Workplane:
    return build_full_length_seam_pair_phase3sa2(0.6)


def build_plate_03_full_length_seam_capture_fixtures_phase3sa2(
) -> cq.Workplane:
    first = _normalize(build_full_length_seam_capture_fixture_phase3sa2())
    box = first.val().BoundingBox()
    second = first.translate((0.0, box.ylen + PART_SPACING_MM, 0.0))
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([first.val(), second.val()])]
    )


def build_optional_combined_c040_c060_plate_phase3sa2() -> cq.Workplane:
    """Place all four specimens in one row while retaining 15 mm gaps."""

    pieces = [
        *full_length_seam_print_pieces_phase3sa2(0.4),
        *full_length_seam_print_pieces_phase3sa2(0.6),
    ]
    placed: list[cq.Workplane] = []
    next_x = 0.0
    for piece in pieces:
        normalized = _normalize(piece)
        box = normalized.val().BoundingBox()
        placed.append(normalized.translate((next_x, 0.0, 0.0)))
        next_x += box.xlen + PART_SPACING_MM
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [piece.val() for piece in placed]
            )
        ]
    )


def phase3sa2_required_plates(
) -> tuple[tuple[str, cq.Workplane, int], ...]:
    return (
        (
            "plate_01_full_length_seam_c040_phase3sa2",
            build_plate_01_full_length_seam_c040_phase3sa2(),
            2,
        ),
        (
            "plate_02_full_length_seam_c060_phase3sa2",
            build_plate_02_full_length_seam_c060_phase3sa2(),
            2,
        ),
        (
            "plate_03_full_length_seam_capture_fixtures_phase3sa2",
            build_plate_03_full_length_seam_capture_fixtures_phase3sa2(),
            2,
        ),
    )
