"""Large flat-print Phase 3R module indexing rings."""

from __future__ import annotations

from math import cos, pi, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    large_ring_selected_clearance,
    phase3r_min_root_thickness,
    wave_amplitude,
    wave_lobe_count,
    wave_ring_base_radius,
    wave_ring_height,
    wave_ring_inner_diameter,
    wide_key_arc_width,
    wide_key_count,
    wide_key_height,
)


STATUS = "PHASE3R_SELECTED_CONTINUOUS_WAVE_RING"
PRINT_ORIENTATION = "FLAT_ON_LARGEST_ANNULAR_FACE"
DESIGN_TYPE = "SIX_LOBE_CONTINUOUS_WAVE_RING"
SAMPLE_COUNT = 360


def _wave_points(
    radial_offset: float = 0.0,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(SAMPLE_COUNT):
        angle = 2.0 * pi * index / SAMPLE_COUNT
        radius = (
            wave_ring_base_radius
            + radial_offset
            + wave_amplitude * cos(wave_lobe_count * angle)
        )
        points.append((radius * cos(angle), radius * sin(angle)))
    return points


def _wave_prism(
    radial_offset: float,
    height: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .polyline(_wave_points(radial_offset))
        .close()
        .extrude(height)
    )


def build_module_alignment_ring_phase3r() -> cq.Workplane:
    """Male continuous six-lobe ring; no isolated key projections."""

    inner_void = (
        cq.Workplane("XY")
        .circle(0.5 * wave_ring_inner_diameter)
        .extrude(wave_ring_height + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    return _wave_prism(0.0, wave_ring_height).cut(inner_void)


def build_module_alignment_socket_ring_phase3r(
    clearance: float = large_ring_selected_clearance,
) -> cq.Workplane:
    """Female ring with a smooth matching six-lobe inner boundary."""

    outer_radius = wave_ring_base_radius + wave_amplitude + 8.0
    outer = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .extrude(wave_ring_height)
    )
    inner = (
        _wave_prism(clearance, wave_ring_height + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    return outer.cut(inner)


def alignment_interference_volume(
    rotation_deg: float,
    clearance: float = large_ring_selected_clearance,
) -> float:
    male = build_module_alignment_ring_phase3r()
    socket = build_module_alignment_socket_ring_phase3r(clearance).rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        rotation_deg,
    )
    return sum(solid.Volume() for solid in male.intersect(socket).solids().vals())


def minimum_wave_curvature_radius() -> float:
    """Analytic minimum plan-view radius of the selected smooth wave."""

    minimum = float("inf")
    for index in range(3600):
        angle = 2.0 * pi * index / 3600.0
        cosine = cos(wave_lobe_count * angle)
        sine = sin(wave_lobe_count * angle)
        radius = wave_ring_base_radius + wave_amplitude * cosine
        first = -wave_amplitude * wave_lobe_count * sine
        second = -wave_amplitude * wave_lobe_count**2 * cosine
        numerator = abs(
            radius**2 + 2.0 * first**2 - radius * second
        )
        curvature = numerator / (radius**2 + first**2) ** 1.5
        if curvature > 1.0e-12:
            minimum = min(minimum, 1.0 / curvature)
    return minimum


def build_wide_three_key_candidate_phase3r() -> cq.Workplane:
    """Comparison-only broad three-rib candidate with a continuous base."""

    inner_radius = 0.5 * wave_ring_inner_diameter
    base_outer_radius = wave_ring_base_radius - wave_amplitude
    ring = (
        cq.Workplane("XY")
        .circle(base_outer_radius)
        .circle(inner_radius)
        .extrude(phase3r_min_root_thickness)
    )
    for index in range(wide_key_count):
        rib = (
            cq.Workplane("XY")
            .box(
                2.0 * wave_amplitude + 0.8,
                wide_key_arc_width,
                phase3r_min_root_thickness,
                centered=(True, True, False),
            )
            .translate(
                (
                    base_outer_radius + wave_amplitude - 0.4,
                    0.0,
                    0.0,
                )
            )
            .rotate(
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                index * 360.0 / wide_key_count,
            )
        )
        ring = ring.union(rib)
    # The comparison preserves the requested 2–3 mm key-height datum without
    # making it a thin vertical cantilever.
    assert 2.0 <= wide_key_height <= 3.0
    return ring
