"""Expanded/collapsed purchased flexible PP/PE root-sleeve envelopes."""

from __future__ import annotations

from functools import lru_cache
from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    plant_port_local_angles,
    rear_drain_service_inner_radius,
    rear_drain_service_wedge_angle,
    rear_drain_service_wedge_center,
    root_sleeve_bottom_z,
    root_sleeve_collapsed_diameter,
    root_sleeve_collapsed_length,
    root_sleeve_height,
    root_sleeve_inner_radius,
    root_sleeve_material_reference,
    root_sleeve_outer_radius,
    root_sleeve_sector_angle,
)
from ps_mht_v001.tower_module.planting_port import (
    orient_local_to_port,
    port_center_heights,
)


REFERENCE_STATUS = "REFERENCE_PURCHASED_PART"
MATERIAL = root_sleeve_material_reference
ROOT_REFERENCE_SOLID_COUNT = 3


def _wedge(
    start_deg: float,
    end_deg: float,
    radius: float,
    height: float,
    z: float,
) -> cq.Workplane:
    steps = max(3, int((end_deg - start_deg) / 3.0))
    points = [(0.0, 0.0)]
    points.extend(
        (
            radius
            * cos(radians(start_deg + (end_deg - start_deg) * i / steps)),
            radius
            * sin(radians(start_deg + (end_deg - start_deg) * i / steps)),
        )
        for i in range(steps + 1)
    )
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z))
    )


def build_rear_drain_service_volume() -> cq.Workplane:
    """Future rear drain-service region that flexible sleeves must avoid."""

    outer = _wedge(
        rear_drain_service_wedge_center
        - 0.5 * rear_drain_service_wedge_angle,
        rear_drain_service_wedge_center
        + 0.5 * rear_drain_service_wedge_angle,
        root_sleeve_outer_radius + 2.0,
        root_sleeve_height + 2.0,
        root_sleeve_bottom_z - 1.0,
    )
    inner = (
        cq.Workplane("XY")
        .circle(rear_drain_service_inner_radius)
        .extrude(root_sleeve_height + 4.0)
        .translate((0.0, 0.0, root_sleeve_bottom_z - 2.0))
    )
    return outer.cut(inner)


@lru_cache(maxsize=3)
def build_expanded_root_sleeve(angle_deg: float) -> cq.Workplane:
    """One 110-degree flexible sleeve envelope with rear service notch."""

    outer = _wedge(
        angle_deg - 0.5 * root_sleeve_sector_angle,
        angle_deg + 0.5 * root_sleeve_sector_angle,
        root_sleeve_outer_radius,
        root_sleeve_height,
        root_sleeve_bottom_z,
    )
    inner = (
        cq.Workplane("XY")
        .circle(root_sleeve_inner_radius)
        .extrude(root_sleeve_height + 2.0)
        .translate((0.0, 0.0, root_sleeve_bottom_z - 1.0))
    )
    sleeve = outer.cut(inner)
    return sleeve.cut(build_rear_drain_service_volume())


def build_expanded_root_sleeve_reference() -> cq.Workplane:
    shapes = [
        build_expanded_root_sleeve(angle).val()
        for angle in plant_port_local_angles
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def build_collapsed_root_sleeve(angle_deg: float, center_z: float) -> cq.Workplane:
    """Folded sleeve envelope small enough for the common receiver bore."""

    local = build_collapsed_root_sleeve_local().translate(
        (0.0, 0.0, 0.45 * root_sleeve_collapsed_length)
    )
    return orient_local_to_port(local, angle_deg, center_z)


def build_collapsed_root_sleeve_local() -> cq.Workplane:
    """Standalone folded-sleeve cylinder centered on its insertion axis."""

    return (
        cq.Workplane("XY")
        .circle(0.5 * root_sleeve_collapsed_diameter)
        .extrude(root_sleeve_collapsed_length)
        .translate((0.0, 0.0, -root_sleeve_collapsed_length))
    )


def build_collapsed_root_sleeve_reference() -> cq.Workplane:
    heights = port_center_heights("A")
    shapes = [
        build_collapsed_root_sleeve(angle, center_z).val()
        for angle, center_z in zip(plant_port_local_angles, heights)
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def expanded_root_volumes_liters() -> tuple[float, float, float]:
    return tuple(
        sum(s.Volume() for s in build_expanded_root_sleeve(angle).solids().vals())
        / 1_000_000.0
        for angle in plant_port_local_angles
    )


def expanded_root_overlap_volumes() -> tuple[float, float, float]:
    sleeves = [
        build_expanded_root_sleeve(angle)
        for angle in plant_port_local_angles
    ]
    return tuple(
        sum(
            s.Volume()
            for s in sleeves[first].intersect(sleeves[second]).solids().vals()
        )
        for first, second in ((0, 1), (0, 2), (1, 2))
    )
