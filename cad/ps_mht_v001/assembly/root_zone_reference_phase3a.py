"""Candidate A/B root-zone envelope comparison for Phase 3A."""

from __future__ import annotations

from functools import lru_cache
import cadquery as cq

from ps_mht_v001.parameters import (
    plant_port_local_angles,
    port_z_offset_pattern_candidate_a,
    port_z_offset_pattern_candidate_b,
)
from ps_mht_v001.tower_module.root_sleeve_reference import (
    build_expanded_root_sleeve,
    build_rear_drain_service_volume,
)


SELECTED_PATTERN = "A"


def build_root_zone_candidate(pattern: str) -> cq.Workplane:
    if pattern not in ("A", "B"):
        raise ValueError("pattern must be A or B")
    offsets = (
        port_z_offset_pattern_candidate_a
        if pattern == "A"
        else port_z_offset_pattern_candidate_b
    )
    shapes = [
        build_expanded_root_sleeve(angle)
        .translate((0.0, 0.0, offset))
        .val()
        for angle, offset in zip(plant_port_local_angles, offsets)
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


@lru_cache(maxsize=1)
def compare_root_zone_candidates() -> dict[str, dict[str, object]]:
    report: dict[str, dict[str, object]] = {}
    service = build_rear_drain_service_volume()
    for pattern in ("A", "B"):
        model = build_root_zone_candidate(pattern)
        solids = model.solids().vals()
        overlaps = [
            sum(
                s.Volume()
                for s in cq.Workplane("XY")
                .newObject([solids[first]])
                .intersect(cq.Workplane("XY").newObject([solids[second]]))
                .solids()
                .vals()
            )
            for first, second in ((0, 1), (0, 2), (1, 2))
        ]
        service_intersection = sum(
            s.Volume() for s in model.intersect(service).solids().vals()
        )
        report[pattern] = {
            "offsets_mm": (
                port_z_offset_pattern_candidate_a
                if pattern == "A"
                else port_z_offset_pattern_candidate_b
            ),
            "volumes_liter": tuple(
                solid.Volume() / 1_000_000.0 for solid in solids
            ),
            "pair_overlap_mm3": tuple(overlaps),
            "rear_service_intersection_mm3": service_intersection,
            "structure": (
                "equal-height continuous shell bands"
                if pattern == "A"
                else "two saddles approach interface bands by 15 mm"
            ),
            "appearance": (
                "level three-port datum"
                if pattern == "A"
                else "visibly staggered ports"
            ),
        }
    return report
