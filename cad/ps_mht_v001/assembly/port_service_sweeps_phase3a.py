"""External insertion/removal, finger, and M3-tool clearance envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import cadquery as cq

from ps_mht_v001.assembly.module_pair_phase2 import (
    keepout_components,
    module_pair_components,
)
from ps_mht_v001.parameters import (
    finger_access_diameter,
    m3_fastener_pitch_radius,
    m3_tool_access_diameter,
    main_irrigation_tube_od,
    netpot_flange_outer_diameter,
    plant_port_local_angles,
    port_receiver_length,
    port_service_sweep_length,
    root_sleeve_collapsed_diameter,
)
from ps_mht_v001.tower_module.planting_port import (
    orient_local_to_port,
    port_center_heights,
    rotated_port_angles,
)


@dataclass(frozen=True)
class ServiceSweep:
    name: str
    angle_deg: float
    model: cq.Workplane


SWEEP_DIAMETERS = {
    "netpot_insertion": netpot_flange_outer_diameter,
    "adapter_removal": 100.0,
    "blank_cap_removal": 100.0,
    "collapsed_root_sleeve": root_sleeve_collapsed_diameter,
    "finger_access": finger_access_diameter,
}


def _local_sweep(diameter: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * diameter)
        .extrude(port_service_sweep_length)
        .translate((0.0, 0.0, port_receiver_length + 4.0))
    )


def _local_m3_tool_sweep() -> cq.Workplane:
    shapes = []
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        shapes.append(
            (
                cq.Workplane("XY")
                .center(0.0, y)
                .circle(0.5 * m3_tool_access_diameter)
                .extrude(port_service_sweep_length)
                .translate((0.0, 0.0, port_receiver_length + 2.0))
                .val()
            )
        )
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


@lru_cache(maxsize=2)
def service_sweep_components(
    module_rotation_deg: float,
) -> tuple[ServiceSweep, ...]:
    """Return all six service envelopes for each of the three ports."""

    heights = port_center_heights("A")
    angles = rotated_port_angles(module_rotation_deg)
    components: list[ServiceSweep] = []
    for index, (angle, center_z) in enumerate(zip(angles, heights), start=1):
        for kind, diameter in SWEEP_DIAMETERS.items():
            components.append(
                ServiceSweep(
                    f"{kind}_{index}",
                    angle,
                    orient_local_to_port(
                        _local_sweep(diameter),
                        angle,
                        center_z,
                    ),
                )
            )
        components.append(
            ServiceSweep(
                f"m3_tool_access_{index}",
                angle,
                orient_local_to_port(
                    _local_m3_tool_sweep(),
                    angle,
                    center_z,
                ),
            )
        )
    return tuple(components)


def build_port_service_sweeps_phase3a() -> cq.Workplane:
    """Compound containing both odd (0°) and even (60°) service cases."""

    components = service_sweep_components(0.0) + service_sweep_components(60.0)
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([component.model.val() for component in components])]
    )


def _intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    first_box = first.val().BoundingBox()
    second_box = second.val().BoundingBox()
    separated = (
        first_box.xmax < second_box.xmin
        or second_box.xmax < first_box.xmin
        or first_box.ymax < second_box.ymin
        or second_box.ymax < first_box.ymin
        or first_box.zmax < second_box.zmin
        or second_box.zmax < first_box.zmin
    )
    if separated:
        return 0.0
    return sum(s.Volume() for s in first.intersect(second).solids().vals())


@lru_cache(maxsize=2)
def service_clearance_report(module_rotation_deg: float) -> dict[str, float]:
    """Measure unwanted sweep intersections against real/declared keep-outs."""

    components = service_sweep_components(module_rotation_deg)
    maximum_neighbor = 0.0
    for first_index, first in enumerate(components):
        first_port = first.name.rsplit("_", 1)[-1]
        for second in components[first_index + 1 :]:
            second_port = second.name.rsplit("_", 1)[-1]
            if first_port != second_port:
                maximum_neighbor = max(
                    maximum_neighbor,
                    _intersection_volume(first.model, second.model),
                )

    phase2_pair = module_pair_components(0.0)
    knobs = [
        component.model
        for component in phase2_pair
        if component.name.startswith("m4_knob_")
    ]
    keepouts = keepout_components()
    rear_post = next(
        component.model
        for component in keepouts
        if component.name == "rear_post_keepout"
    )
    # Phase 2's provisional external (28, 130) hose zone conflicts with an
    # even-module 60-degree net-pot extraction.  Phase 3A therefore reserves
    # the rear internal service corridor at (0, 60); the actual hose remains
    # Phase 5 CALIBRATION_PENDING.
    hose = (
        cq.Workplane("XY")
        .center(0.0, 60.0)
        .circle(0.5 * main_irrigation_tube_od)
        .extrude(360.0)
    )
    interface_bands = (
        cq.Workplane("XY")
        .circle(118.25)
        .circle(95.0)
        .extrude(14.0)
    ).union(
        cq.Workplane("XY")
        .circle(118.25)
        .circle(95.0)
        .extrude(20.0)
        .translate((0.0, 0.0, 158.0))
    )
    return {
        "neighbor_max_mm3": maximum_neighbor,
        "m4_knob_max_mm3": max(
            _intersection_volume(sweep.model, knob)
            for sweep in components
            for knob in knobs
        ),
        "rear_post_max_mm3": max(
            _intersection_volume(sweep.model, rear_post)
            for sweep in components
        ),
        "main_hose_max_mm3": max(
            _intersection_volume(sweep.model, hose)
            for sweep in components
        ),
        "module_interface_max_mm3": max(
            _intersection_volume(sweep.model, interface_bands)
            for sweep in components
        ),
    }
