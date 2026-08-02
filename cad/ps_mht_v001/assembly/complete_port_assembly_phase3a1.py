"""Corrected one-axis Phase 3A.1 planting-port assembly and passage audit."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_body_top_outer_diameter,
    netpot_flange_thickness,
    netpot_body_height,
    port_service_sweep_length,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    build_m3_port_bolt_axis_reference,
    build_m3_port_cartridge_removal_sweep,
    build_m3_port_nut_cartridge,
    build_m3_port_nut_cartridge_retainer,
    place_m3_port_cartridge_retainer,
    place_m3_port_nut_cartridge,
)
from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
)
from ps_mht_v001.tower_module.netpot_reference import build_netpot_reference
from ps_mht_v001.tower_module.planting_port import (
    build_planting_port_receiver,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.port_adapter_gasket import (
    build_port_adapter_gasket,
)
from ps_mht_v001.tower_module.root_sleeve_reference import (
    build_collapsed_root_sleeve_local,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
)
from ps_mht_v001.tower_module.root_stop_insert import build_root_stop_insert


COMPLETE_PASSAGE_DIAMETER = netpot_body_top_outer_diameter
COMMON_ADAPTER_Z = 2.5
GASKET_Z = 11.5
NETPOT_ADAPTER_Z = 11.0
NETPOT_FLANGE_TOP_Z = 24.5
ROOT_RING_INNER_END_DATUM_Z = COMMON_ADAPTER_Z
COLLAPSED_ROOT_TOP_Z = 8.0
ROOT_STOP_Z = -101.0
COMPLETE_ASSEMBLY_SOLID_COUNT = 14
ROOT_RING_RETENTION_METHOD = (
    "CAPTIVE_IN_FLEXIBLE_SLEEVE_FOLD_AT_ADAPTER_INNER_END"
)


@dataclass(frozen=True)
class CompletePortComponent:
    name: str
    model: cq.Workplane
    category: str
    contact_policy: str


@lru_cache(maxsize=1)
def _placed_netpot() -> cq.Workplane:
    return (
        build_netpot_reference()
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
        .translate((0.0, 0.0, NETPOT_FLANGE_TOP_Z))
    )


@lru_cache(maxsize=1)
def _placed_collapsed_root_sleeve() -> cq.Workplane:
    return build_collapsed_root_sleeve_local().translate(
        (0.0, 0.0, COLLAPSED_ROOT_TOP_Z)
    )


@lru_cache(maxsize=1)
def build_complete_port_passage_probe() -> cq.Workplane:
    """Continuous real-body envelope from net-pot entrance into tower."""

    return (
        cq.Workplane("XY")
        .circle(0.5 * COMPLETE_PASSAGE_DIAMETER)
        .extrude(65.0)
        .translate((0.0, 0.0, -40.0))
    )


@lru_cache(maxsize=1)
def build_netpot_removal_sweep_local() -> cq.Workplane:
    """Purchased flange envelope withdrawing outward from its seat."""

    from ps_mht_v001.parameters import netpot_flange_outer_diameter

    return (
        cq.Workplane("XY")
        .circle(0.5 * netpot_flange_outer_diameter)
        .extrude(port_service_sweep_length)
        .translate((0.0, 0.0, NETPOT_FLANGE_TOP_Z - netpot_flange_thickness))
    )


@lru_cache(maxsize=2)
def complete_port_components(
    exploded_gap: float = 0.0,
) -> tuple[CompletePortComponent, ...]:
    """Place every corrected component on one common local +Z port axis."""

    positive_gap = exploded_gap
    negative_gap = -exploded_gap
    components: list[CompletePortComponent] = [
        CompletePortComponent(
            "tower_receiver",
            build_planting_port_receiver(),
            "PRINTED_MODULE_FEATURE",
            "FIXED",
        ),
        CompletePortComponent(
            "port_adapter_gasket",
            build_port_adapter_gasket().translate(
                (0.0, 0.0, GASKET_Z + positive_gap)
            ),
            "TPU_OR_EPDM",
            "DESIGNED_COMPRESSION",
        ),
        CompletePortComponent(
            "common_planting_port_adapter",
            build_planting_port_adapter().translate(
                (0.0, 0.0, COMMON_ADAPTER_Z + 2.0 * positive_gap)
            ),
            "PRINTED_PETG",
            "CLEARANCE_FIT",
        ),
        CompletePortComponent(
            "netpot_60_adapter",
            build_netpot_60_adapter().translate(
                (0.0, 0.0, NETPOT_ADAPTER_Z + 3.0 * positive_gap)
            ),
            "PRINTED_PETG_TOOL_FREE_LINER",
            "GRAVITY_SEAT",
        ),
        CompletePortComponent(
            "purchased_netpot_reference",
            _placed_netpot().translate(
                (0.0, 0.0, 4.0 * positive_gap)
            ),
            "REFERENCE_PURCHASED_PART",
            "FLANGE_SEAT",
        ),
        CompletePortComponent(
            "root_sleeve_retaining_ring",
            build_root_sleeve_retaining_ring().translate(
                (
                    0.0,
                    0.0,
                    ROOT_RING_INNER_END_DATUM_Z + negative_gap,
                )
            ),
            "PRINTED_PETG",
            ROOT_RING_RETENTION_METHOD,
        ),
        CompletePortComponent(
            "collapsed_root_sleeve_reference",
            _placed_collapsed_root_sleeve().translate(
                (0.0, 0.0, 2.0 * negative_gap)
            ),
            "REFERENCE_PURCHASED_PP_OR_PE",
            "FOLDED_PASSAGE",
        ),
        CompletePortComponent(
            "root_stop_insert",
            build_root_stop_insert().translate(
                (0.0, 0.0, ROOT_STOP_Z + 3.0 * negative_gap)
            ),
            "PRINTED_PETG_OPTIONAL",
            "TOWER_INTERIOR_STOP",
        ),
    ]
    for side in (-1, 1):
        components.extend(
            (
                CompletePortComponent(
                    f"m3_bolt_axis_{side:+d}",
                    build_m3_port_bolt_axis_reference(side),
                    "PURCHASED_M3_REFERENCE",
                    "DESIGNED_AXIS_OVERLAP",
                ),
                CompletePortComponent(
                    f"m3_nut_cartridge_{side:+d}",
                    place_m3_port_nut_cartridge(
                        build_m3_port_nut_cartridge(),
                        side,
                    ).translate((0.0, side * positive_gap, 0.0)),
                    "PRINTED_PETG",
                    "CLEARANCE_FIT",
                ),
                CompletePortComponent(
                    f"m3_cartridge_retainer_{side:+d}",
                    place_m3_port_cartridge_retainer(
                        build_m3_port_nut_cartridge_retainer(),
                        side,
                    ).translate((0.0, side * 2.0 * positive_gap, 0.0)),
                    "PRINTED_PETG",
                    "M3_BOLT_CAPTURED",
                ),
            )
        )
    return tuple(components)


def _compound(components: tuple[CompletePortComponent, ...]) -> cq.Workplane:
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([component.model.val() for component in components])]
    )


@lru_cache(maxsize=1)
def build_complete_port_assembly_phase3a1() -> cq.Workplane:
    return _compound(complete_port_components())


@lru_cache(maxsize=1)
def build_complete_port_exploded_phase3a1() -> cq.Workplane:
    return _compound(complete_port_components(exploded_gap=8.0))


@lru_cache(maxsize=1)
def build_complete_port_section_phase3a1() -> cq.Workplane:
    """Return a thin axial section of the complete one-axis assembly."""

    section_cutter = (
        cq.Workplane("XY")
        .box(120.0, 1.0, 140.0, centered=(True, True, False))
        .translate((0.0, 0.0, -110.0))
    )
    section_solids: list[cq.Shape] = []
    for component in complete_port_components():
        section_solids.extend(
            component.model.intersect(section_cutter).solids().vals()
        )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(section_solids)]
    )


def _intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    first_box = first.val().BoundingBox()
    second_box = second.val().BoundingBox()
    if (
        first_box.xmax < second_box.xmin
        or second_box.xmax < first_box.xmin
        or first_box.ymax < second_box.ymin
        or second_box.ymax < first_box.ymin
        or first_box.zmax < second_box.zmin
        or second_box.zmax < first_box.zmin
    ):
        return 0.0
    return sum(s.Volume() for s in first.intersect(second).solids().vals())


@lru_cache(maxsize=1)
def complete_port_interference_report() -> dict[str, float]:
    """Return only prohibited intersection classes; all must be zero."""

    components = {
        component.name: component.model
        for component in complete_port_components()
    }
    common_adapter = components["common_planting_port_adapter"]
    netpot_adapter = components["netpot_60_adapter"]
    netpot = components["purchased_netpot_reference"]
    ring = components["root_sleeve_retaining_ring"]
    sleeve = components["collapsed_root_sleeve_reference"]
    receiver = components["tower_receiver"]
    netpot_sweep = build_netpot_removal_sweep_local()
    report = {
        "netpot_to_common_adapter_mm3":
            _intersection_volume(netpot, common_adapter),
        "netpot_to_netpot_adapter_mm3":
            _intersection_volume(netpot, netpot_adapter),
        "netpot_adapter_to_common_adapter_mm3":
            _intersection_volume(netpot_adapter, common_adapter),
        "root_ring_to_common_adapter_mm3":
            _intersection_volume(ring, common_adapter),
        "collapsed_sleeve_to_root_ring_mm3":
            _intersection_volume(sleeve, ring),
        "collapsed_sleeve_to_common_adapter_mm3":
            _intersection_volume(sleeve, common_adapter),
        "root_stop_transit_to_common_adapter_mm3":
            _intersection_volume(
                build_root_stop_insert().translate((0.0, 0.0, 4.0)),
                common_adapter,
            ),
    }
    for side in (-1, 1):
        cartridge = components[f"m3_nut_cartridge_{side:+d}"]
        report[f"cartridge_{side:+d}_to_netpot_sweep_mm3"] = (
            _intersection_volume(cartridge, netpot_sweep)
        )
        report[f"cartridge_{side:+d}_to_root_sleeve_mm3"] = (
            _intersection_volume(cartridge, sleeve)
        )
        report[f"cartridge_removal_{side:+d}_to_receiver_mm3"] = (
            _intersection_volume(
                build_m3_port_cartridge_removal_sweep(side),
                receiver,
            )
        )
    return report


@lru_cache(maxsize=1)
def passage_interference_report() -> dict[str, float]:
    """Check the φ60 complete probe against every structural passage part."""

    probe = build_complete_port_passage_probe()
    components = {
        component.name: component.model
        for component in complete_port_components()
    }
    return {
        name: _intersection_volume(probe, components[name])
        for name in (
            "tower_receiver",
            "common_planting_port_adapter",
            "netpot_60_adapter",
            "root_sleeve_retaining_ring",
        )
    }


def netpot_bottom_z() -> float:
    return (
        NETPOT_FLANGE_TOP_Z
        - netpot_flange_thickness
        - netpot_body_height
    )
