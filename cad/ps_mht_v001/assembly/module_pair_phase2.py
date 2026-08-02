"""Phase 2 two-module assemblies, hardware references, and keep-outs."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.common.fasteners import (
    build_m4_nut_cartridge,
    build_m4_nut_cartridge_retainer,
    build_m4_star_knob_reference,
)
from ps_mht_v001.parameters import (
    frame_post_offset,
    frame_profile_size,
    gasket_groove_width,
    interface_fastener_pitch_radius,
    interface_flange_height,
    main_irrigation_tube_od,
    m4_star_knob_envelope_height,
    module_height,
    plant_port_angle,
    plant_port_diameter,
    tower_body_diameter,
    tower_max_diameter,
    used_fastener_angles,
)
from ps_mht_v001.tower_module.module_gasket import build_module_gasket
from ps_mht_v001.tower_module.module_interface import (
    build_index_key_solid,
    build_m4_axis_probe,
    build_socket_key_groove_void,
    cartridge_placement,
    retainer_placement,
    station_point,
    build_planting_module_with_interface,
)


@dataclass(frozen=True)
class PairComponent:
    """One named solid in a module-pair reference assembly."""

    name: str
    model: cq.Workplane
    category: str
    printable: bool


def _compound(components: tuple[PairComponent, ...]) -> cq.Workplane:
    compound = cq.Compound.makeCompound(
        [component.model.val() for component in components]
    )
    return cq.Workplane("XY").newObject([compound])


def _knob_placement(angle_deg: float) -> cq.Workplane:
    knob_bottom_z = (
        module_height
        - interface_flange_height
        - m4_star_knob_envelope_height
        - 1.0
    )
    x, y = station_point(interface_fastener_pitch_radius, angle_deg)
    return build_m4_star_knob_reference().translate((x, y, knob_bottom_z))


def module_pair_components(
    upper_rotation_deg: float,
    exploded_gap: float = 0.0,
    include_hardware: bool = True,
) -> tuple[PairComponent, ...]:
    """Build two modules sharing one nominal Z=170 interface."""

    if upper_rotation_deg not in (0.0, 60.0):
        raise ValueError("upper module rotation must be 0 or 60 degrees")
    upper_z = module_height + exploded_gap
    lower = build_planting_module_with_interface()
    upper = (
        build_planting_module_with_interface()
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            upper_rotation_deg,
        )
        .translate((0.0, 0.0, upper_z))
    )
    components: list[PairComponent] = [
        PairComponent("module_lower", lower, "PRINTED_PETG", True),
        PairComponent("module_upper", upper, "PRINTED_PETG", True),
    ]
    if not include_hardware:
        return tuple(components)

    gasket_center_z = (
        module_height + 1.2 + 0.5 * gasket_groove_width + 0.5 * exploded_gap
    )
    components.append(
        PairComponent(
            "module_gasket",
            build_module_gasket().translate((0.0, 0.0, gasket_center_z)),
            "TPU_OR_EPDM_REFERENCE",
            False,
        )
    )
    for angle in used_fastener_angles:
        components.extend(
            (
                PairComponent(
                    f"m4_knob_{int(angle):03d}",
                    _knob_placement(angle),
                    "PURCHASED_M4_REFERENCE",
                    False,
                ),
                PairComponent(
                    f"m4_nut_cartridge_{int(angle):03d}",
                    cartridge_placement(
                        build_m4_nut_cartridge(),
                        angle,
                        z_offset=upper_z,
                    ),
                    "PRINTED_PETG",
                    True,
                ),
                PairComponent(
                    f"m4_cartridge_retainer_{int(angle):03d}",
                    retainer_placement(
                        build_m4_nut_cartridge_retainer(),
                        angle,
                        z_offset=upper_z,
                    ),
                    "PRINTED_PETG",
                    True,
                ),
            )
        )
    return tuple(components)


def build_module_pair(
    upper_rotation_deg: float,
    include_hardware: bool = True,
) -> cq.Workplane:
    """Return the assembled 0- or 60-degree module pair."""

    return _compound(
        module_pair_components(
            upper_rotation_deg,
            exploded_gap=0.0,
            include_hardware=include_hardware,
        )
    )


def build_exploded_interface() -> cq.Workplane:
    """Return a 25 mm separated 60-degree interface assembly."""

    return _compound(
        module_pair_components(
            60.0,
            exploded_gap=25.0,
            include_hardware=True,
        )
    )


@lru_cache(maxsize=8)
def module_pair_interference_volume(upper_rotation_deg: float) -> float:
    """Return module-to-module overlap volume, excluding the compressed gasket."""

    lower = build_planting_module_with_interface()
    upper = (
        build_planting_module_with_interface()
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            upper_rotation_deg,
        )
        .translate((0.0, 0.0, module_height))
    )
    intersection = lower.intersect(upper)
    return sum(solid.Volume() for solid in intersection.solids().vals())


def module_pair_interference_volume_at_lift(
    upper_rotation_deg: float,
    lift_mm: float,
) -> float:
    """Measure real module overlap after lifting the upper module."""

    lower = build_planting_module_with_interface()
    upper = (
        build_planting_module_with_interface()
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            upper_rotation_deg,
        )
        .translate((0.0, 0.0, module_height + lift_mm))
    )
    return sum(
        solid.Volume() for solid in lower.intersect(upper).solids().vals()
    )


def minimum_noninterfering_lift(
    upper_rotation_deg: float,
    increment_mm: float = 0.05,
    maximum_lift_mm: float = 10.0,
) -> float:
    """Return lift needed to clear one representative real key collision."""

    from math import ceil

    key = build_index_key_solid(0.0)
    upper = (
        build_planting_module_with_interface()
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            upper_rotation_deg,
        )
        .translate((0.0, 0.0, module_height))
    )
    collision = key.intersect(upper)
    solids = collision.solids().vals()
    if not solids:
        return 0.0
    key_top = key.val().BoundingBox().zmax
    upper_bottom = upper.val().BoundingBox().zmin
    lift = ceil((key_top - upper_bottom) / increment_mm) * increment_mm
    if lift > maximum_lift_mm:
        raise ValueError("module key did not clear within maximum_lift_mm")
    if sum(
        solid.Volume()
        for solid in key.intersect(
            upper.translate((0.0, 0.0, lift))
        ).solids().vals()
    ) > 1.0e-6:
        raise ValueError("computed key lift does not clear real geometry")
    return lift


@lru_cache(maxsize=8)
def key_alignment_intersection_volume(upper_rotation_deg: float) -> float:
    """Measure real lower-key overlap with the rotated upper socket grooves."""

    total = 0.0
    for lower_angle in range(0, 360, 60):
        key = build_index_key_solid(float(lower_angle))
        for upper_angle in range(0, 360, 60):
            groove = (
                build_socket_key_groove_void(float(upper_angle))
                .rotate(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0),
                    upper_rotation_deg,
                )
                .translate((0.0, 0.0, module_height))
            )
            total += sum(
                solid.Volume()
                for solid in key.intersect(groove).solids().vals()
            )
    return total


@lru_cache(maxsize=8)
def m4_axis_alignment_intersection_volume(
    upper_rotation_deg: float,
) -> float:
    """Measure overlap of real six-hole probes for a relative rotation."""

    total = 0.0
    for lower_angle in range(30, 360, 60):
        lower_probe = build_m4_axis_probe(
            float(lower_angle),
            z=module_height - 0.5,
            height=11.0,
        )
        for upper_angle in range(30, 360, 60):
            upper_probe = (
                build_m4_axis_probe(
                    float(upper_angle),
                    z=-0.5,
                    height=11.0,
                )
                .rotate(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0),
                    upper_rotation_deg,
                )
                .translate((0.0, 0.0, module_height))
            )
            total += sum(
                solid.Volume()
                for solid in lower_probe.intersect(upper_probe).solids().vals()
            )
    return total


def is_normal_assembly_rotation(rotation_deg: float) -> bool:
    """Only the intended alternating 0/60-degree rotations are normal."""

    return rotation_deg in (0.0, 60.0)


def build_interface_section() -> cq.Workplane:
    """Return a thin radial solid section through the assembled joint."""

    components = module_pair_components(
        0.0,
        exploded_gap=0.0,
        include_hardware=False,
    )
    cutter = (
        cq.Workplane("XY")
        .box(250.0, 1.0, 32.0, centered=(True, True, False))
        .translate((0.0, 0.0, module_height - 12.0))
    )
    section_shapes: list[cq.Shape] = []
    for component in components:
        section = component.model.intersect(cutter)
        section_shapes.extend(section.solids().vals())
    gasket = (
        build_module_gasket()
        .translate(
            (
                0.0,
                0.0,
                module_height + 1.2 + 0.5 * gasket_groove_width,
            )
        )
        .intersect(cutter)
    )
    section_shapes.extend(gasket.solids().vals())
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(section_shapes)]
    )


def _future_port_axis(angle_deg: float, z_center: float) -> cq.Workplane:
    """Build one φ60 angled REFERENCE_KEEP_OUT cylinder."""

    angle = radians(angle_deg)
    tilt = radians(plant_port_angle)
    direction = cq.Vector(
        cos(tilt) * cos(angle),
        cos(tilt) * sin(angle),
        sin(tilt),
    )
    start_radius = 0.42 * tower_body_diameter
    start = cq.Vector(
        start_radius * cos(angle),
        start_radius * sin(angle),
        z_center - 20.0 * sin(tilt),
    )
    solid = cq.Solid.makeCylinder(
        0.5 * plant_port_diameter,
        55.0,
        start,
        direction,
    )
    return cq.Workplane("XY").newObject([solid])


def keepout_components() -> tuple[PairComponent, ...]:
    """Return non-printable future-feature and service-zone references."""

    components: list[PairComponent] = [
        PairComponent(
            "tower_240mm_absolute_envelope",
            cq.Workplane("XY")
            .circle(0.5 * tower_max_diameter)
            .extrude(module_height),
            "REFERENCE_KEEP_OUT",
            False,
        ),
        PairComponent(
            "rear_post_keepout",
            cq.Workplane("XY")
            .box(
                frame_profile_size,
                frame_profile_size,
                360.0,
                centered=(True, True, False),
            )
            .translate((0.0, frame_post_offset, 0.0)),
            "REFERENCE_KEEP_OUT",
            False,
        ),
        PairComponent(
            "rear_drain_service_zone",
            cq.Workplane("XY")
            .box(34.0, 24.0, 150.0, centered=(True, True, False))
            .translate((0.0, 123.0, 10.0)),
            "REFERENCE_KEEP_OUT",
            False,
        ),
        PairComponent(
            "rear_clamp_service_zone",
            cq.Workplane("XY")
            .box(90.0, 22.0, 34.0, centered=(True, True, False))
            .translate((0.0, 126.0, 68.0)),
            "REFERENCE_KEEP_OUT",
            False,
        ),
        PairComponent(
            "main_irrigation_hose_zone",
            cq.Workplane("XY")
            .circle(0.5 * main_irrigation_tube_od)
            .extrude(360.0)
            .translate((28.0, 130.0, 0.0)),
            "REFERENCE_KEEP_OUT",
            False,
        ),
    ]
    for angle in range(0, 360, 60):
        components.append(
            PairComponent(
                f"future_port_axis_{angle:03d}",
                _future_port_axis(float(angle), 85.0),
                "REFERENCE_KEEP_OUT",
                False,
            )
        )
    return tuple(components)


def build_keepout_reference_model() -> cq.Workplane:
    """Return the disconnected non-printable keep-out reference."""

    return _compound(keepout_components())
