"""Actual-curvature, two-piece Phase 3S-A seam calibration coupon."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.parameters import (
    phase3sa_seam_clearance_candidates,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)


STATUS = "PHASE3SA_SEAM_CALIBRATION_ONLY"
COUPON_HEIGHT_MM = 60.0
COUPON_PART_COUNT = 2
PART_SPACING_MM = 15.0
IDENTIFICATION = "ONE_TWO_THREE_LARGE_DIMPLES_FOR_C040_C060_C080"
TEST_PROTOCOL = (
    "HAND_ASSEMBLY_NO_IMPACT_10_CYCLES_WHITENING_PLAY_STEP_"
    "500ML_INWARD_DRIP_DIRECT_OUTFLOW_CLEANABILITY"
)


def _candidate_index(clearance: float) -> int:
    value = validate_seam_clearance_phase3sa(clearance)
    return phase3sa_seam_clearance_candidates.index(value) + 1


def _crop_shared_seam(
    model: cq.Workplane,
) -> cq.Workplane:
    crop = (
        cq.Workplane("XY")
        .box(70.0, 70.0, COUPON_HEIGHT_MM + 2.0)
        .translate((50.0, 86.6025403784, 0.5 * COUPON_HEIGHT_MM))
    )
    return model.intersect(crop)


def _add_large_dimples(
    cover_piece: cq.Workplane,
    count: int,
) -> cq.Workplane:
    result = cover_piece
    for index in range(count):
        dimple = (
            cq.Workplane("XY")
            .center(54.0 + 6.0 * index, 74.0)
            .circle(2.0)
            .extrude(2.0)
            .translate((0.0, 0.0, COUPON_HEIGHT_MM - 1.0))
        )
        result = result.cut(dimple)
    return result


def seam_pair_assembly_pieces_phase3sa(
    seam_clearance: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    index = _candidate_index(seam_clearance)
    first = build_blank_sector_panel_calibration_reference_phase3sa(
        seam_clearance,
        COUPON_HEIGHT_MM,
    )
    second = first.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 120.0)
    cover = _add_large_dimples(_crop_shared_seam(first), index)
    receiver = _crop_shared_seam(second)
    return cover, receiver


def build_sector_seam_pair_coupon_phase3sa(
    seam_clearance: float,
) -> cq.Workplane:
    """Return two separated pieces in their real chord-down print posture."""

    cover, receiver_global = seam_pair_assembly_pieces_phase3sa(
        seam_clearance
    )
    receiver_local = receiver_global.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        -120.0,
    )
    printed_cover = orient_sector_for_print_phase3sa(cover)
    printed_receiver = orient_sector_for_print_phase3sa(receiver_local)

    cover_box = printed_cover.val().BoundingBox()
    receiver_box = printed_receiver.val().BoundingBox()
    printed_cover = printed_cover.translate(
        (-cover_box.xmin, -cover_box.ymin, -cover_box.zmin)
    )
    printed_receiver = printed_receiver.translate(
        (
            cover_box.xlen + PART_SPACING_MM - receiver_box.xmin,
            -receiver_box.ymin,
            -receiver_box.zmin,
        )
    )
    return cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [printed_cover.val(), printed_receiver.val()]
            )
        ]
    )
