"""Full 170 mm seam pairs for Phase 3S-A.2 force calibration."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    orient_sector_for_print_phase3sa,
)
from ps_mht_v001.parameters import (
    phase3sa2_effective_seam_length,
    phase3sa2_panel_remaining_width,
    phase3sa2_seam_clearance_candidates,
    phase3sa_seam_overlap,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    build_blank_sector_panel_calibration_reference_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)


STATUS = "PHASE3SA2_FULL_LENGTH_FORCE_CALIBRATION_ONLY"
PART_COUNT = 2
PART_SPACING_MM = 15.0
SHARED_SEAM_ANGLE_DEG = 60.0
RADIAL_CROP_MIN_MM = 30.0
RADIAL_CROP_MAX_MM = 116.0
SEAM_FEATURE_ALLOWANCE_MM = 15.0


def validate_phase3sa2_clearance(clearance: float) -> float:
    value = validate_seam_clearance_phase3sa(clearance)
    if value not in phase3sa2_seam_clearance_candidates:
        raise ValueError(
            "Phase 3S-A.2 only retests c040 and c060; "
            f"got {value:.1f} mm"
        )
    return value


def clearance_token_phase3sa2(clearance: float) -> str:
    value = validate_phase3sa2_clearance(clearance)
    return f"c{int(round(value * 100)):03d}"


def _shared_seam_point(
    radial: float,
    tangent: float,
) -> tuple[float, float]:
    angle = radians(SHARED_SEAM_ANGLE_DEG)
    return (
        radial * cos(angle) - tangent * sin(angle),
        radial * sin(angle) + tangent * cos(angle),
    )


def _crop_prism(
    tangent_min: float,
    tangent_max: float,
    height: float = phase3sa2_effective_seam_length,
) -> cq.Workplane:
    points = [
        _shared_seam_point(RADIAL_CROP_MIN_MM, tangent_min),
        _shared_seam_point(RADIAL_CROP_MAX_MM, tangent_min),
        _shared_seam_point(RADIAL_CROP_MAX_MM, tangent_max),
        _shared_seam_point(RADIAL_CROP_MIN_MM, tangent_max),
    ]
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height + 2.0)
        .translate((0.0, 0.0, -1.0))
    )


def seam_assembly_pieces_at_height_phase3sa2(
    seam_clearance: float,
    height: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    """Return nominally assembled cover and receiver at an explicit height."""

    clearance = validate_phase3sa2_clearance(seam_clearance)
    source = build_blank_sector_panel_calibration_reference_phase3sa(
        clearance,
        height,
    )
    adjacent = source.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        120.0,
    )
    cover = source.intersect(
        _crop_prism(
            -phase3sa2_panel_remaining_width,
            phase3sa_seam_overlap + 3.0,
            height,
        )
    )
    receiver = adjacent.intersect(
        _crop_prism(
            -3.0,
            phase3sa2_panel_remaining_width,
            height,
        )
    )
    return cover, receiver


def full_length_seam_assembly_pieces_phase3sa2(
    seam_clearance: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    """Return nominally assembled cover and receiver specimen solids."""

    return seam_assembly_pieces_at_height_phase3sa2(
        seam_clearance,
        phase3sa2_effective_seam_length,
    )


def full_length_seam_print_pieces_phase3sa2(
    seam_clearance: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    """Return both pieces independently in the real chord-rail-down posture."""

    cover, receiver_global = full_length_seam_assembly_pieces_phase3sa2(
        seam_clearance
    )
    receiver_local = receiver_global.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        -120.0,
    )
    return (
        orient_sector_for_print_phase3sa(cover),
        orient_sector_for_print_phase3sa(receiver_local),
    )


def _normalize(model: cq.Workplane) -> cq.Workplane:
    box = model.val().BoundingBox()
    return model.translate((-box.xmin, -box.ymin, -box.zmin))


def build_full_length_seam_pair_phase3sa2(
    seam_clearance: float,
) -> cq.Workplane:
    """Return the two full-length pieces spaced on one A1 plate."""

    cover, receiver = (
        full_length_seam_print_pieces_phase3sa2(seam_clearance)
    )
    cover = _normalize(cover)
    receiver = _normalize(receiver)
    cover_box = cover.val().BoundingBox()
    receiver_box = receiver.val().BoundingBox()
    receiver = receiver.translate(
        (
            cover_box.xlen + PART_SPACING_MM - receiver_box.xmin,
            -receiver_box.ymin,
            -receiver_box.zmin,
        )
    )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([cover.val(), receiver.val()])]
    )


def full_length_seam_requirements_phase3sa2(
    seam_clearance: float,
) -> dict[str, object]:
    return {
        "clearance_mm": validate_phase3sa2_clearance(seam_clearance),
        "effective_length_mm": phase3sa2_effective_seam_length,
        "panel_remaining_width_mm": phase3sa2_panel_remaining_width,
        "overlap_mm": phase3sa_seam_overlap,
        "actual_curvature": True,
        "actual_left_cover": True,
        "actual_right_receiver": True,
        "actual_contact_rail_section": True,
        "actual_top_bottom_datums": True,
        "small_snap_claw_gate": False,
    }
