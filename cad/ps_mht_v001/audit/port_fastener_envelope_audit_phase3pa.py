"""M4, tool, finger and pot-removal envelope audit for the measured flange."""

from __future__ import annotations

from math import sqrt

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    m4_nut_across_flats,
    m4_star_knob_envelope_diameter,
    m4_washer_diameter,
    netpot_siawadeky_flange_outer_diameter,
    phase3pa_m4_finger_access_diameter,
    phase3pa_m4_tool_access_diameter,
    port_function_ring_fastener_pitch,
    port_function_ring_outer_diameter,
)


STATUS = "FAIL_FASTENER_INTERFERENCE"


def _radial_interval(center: float, diameter: float) -> tuple[float, float]:
    radius = 0.5 * diameter
    return center - radius, center + radius


def _overlaps_flange(interval: tuple[float, float]) -> bool:
    return interval[0] < 0.5 * netpot_siawadeky_flange_outer_diameter


def port_fastener_envelope_audit_phase3pa() -> dict[str, object]:
    pitch = port_function_ring_fastener_pitch
    nut_vertex_diameter = 2.0 * (
        m4_nut_across_flats / sqrt(3.0)
    )
    envelopes = {
        "m4_bolt_axis": _radial_interval(pitch, m4_clearance_diameter),
        "m4_flat_washer": _radial_interval(pitch, m4_washer_diameter),
        "m4_bolt_head_or_star_knob": _radial_interval(
            pitch,
            m4_star_knob_envelope_diameter,
        ),
        "m4_nut": _radial_interval(pitch, nut_vertex_diameter),
        "tool_access": _radial_interval(
            pitch,
            phase3pa_m4_tool_access_diameter,
        ),
        "finger_access": _radial_interval(
            pitch,
            phase3pa_m4_finger_access_diameter,
        ),
    }
    overlap = {
        name: _overlaps_flange(interval)
        for name, interval in envelopes.items()
    }
    return {
        "status": STATUS,
        "flange_radius_mm":
            0.5 * netpot_siawadeky_flange_outer_diameter,
        "existing_m4_axis_radius_mm": pitch,
        "ring_outer_radius_mm": 0.5 * port_function_ring_outer_diameter,
        "radial_intervals_mm": {
            name: {"minimum": value[0], "maximum": value[1]}
            for name, value in envelopes.items()
        },
        "intersects_measured_flange_projection": overlap,
        "cad_shape_intersection_free": False,
        "tool_access_with_pot_installed": False,
        "finger_access_with_pot_installed": False,
        "fastening_without_removing_pot": False,
        "fastening_with_pot_removed": True,
        "pot_removal_path_with_existing_head_installed": False,
        "service_classification": "POT_REMOVED_ONLY_REFERENCE",
        "conclusion": (
            "Existing M4 axes and all service envelopes lie inside the "
            "measured 54 mm flange radius. Geometry non-intersection alone "
            "cannot produce a service PASS."
        ),
    }
