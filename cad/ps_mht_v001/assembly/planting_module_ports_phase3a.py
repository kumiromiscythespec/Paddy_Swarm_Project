"""Phase 3A module reference with removable port components installed."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ps_mht_v001.parameters import plant_port_local_angles
from ps_mht_v001.tower_module.blank_port_cap import build_blank_port_cap
from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
)
from ps_mht_v001.tower_module.netpot_reference import build_netpot_reference
from ps_mht_v001.tower_module.planting_port import (
    build_planting_module_with_ports_phase3a,
    orient_local_to_port,
    port_center_heights,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.port_adapter_gasket import (
    build_port_adapter_gasket,
)
from ps_mht_v001.tower_module.port_adapter_retainer import (
    build_port_adapter_retainer,
)


@dataclass(frozen=True)
class PortAssemblyComponent:
    name: str
    model: cq.Workplane
    category: str
    printable: bool


def _place_outward_part(
    part: cq.Workplane,
    angle: float,
    center_z: float,
    local_z: float,
) -> cq.Workplane:
    return orient_local_to_port(
        part.translate((0.0, 0.0, local_z)),
        angle,
        center_z,
    )


def _place_netpot(
    angle: float,
    center_z: float,
    exploded_gap: float,
) -> cq.Workplane:
    flipped = build_netpot_reference().rotate(
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        180.0,
    )
    return _place_outward_part(
        flipped,
        angle,
        center_z,
        15.0 + 3.0 * exploded_gap,
    )


def port_assembly_components(
    exploded_gap: float = 0.0,
) -> tuple[PortAssemblyComponent, ...]:
    """Two planted ports plus one blank-cap port on the same module."""

    components: list[PortAssemblyComponent] = [
        PortAssemblyComponent(
            "module_three_port_phase3a",
            build_planting_module_with_ports_phase3a(),
            "PRINTED_PETG_DO_NOT_PRINT_UNTIL_CALIBRATION",
            True,
        )
    ]
    heights = port_center_heights("A")
    for index, (angle, center_z) in enumerate(
        zip(plant_port_local_angles, heights)
    ):
        common_z = 2.0 + exploded_gap
        components.extend(
            (
                PortAssemblyComponent(
                    f"port_gasket_{index + 1}",
                    _place_outward_part(
                        build_port_adapter_gasket(),
                        angle,
                        center_z,
                        11.5 + 0.5 * exploded_gap,
                    ),
                    "TPU_OR_EPDM_REFERENCE",
                    False,
                ),
                PortAssemblyComponent(
                    f"port_retainer_{index + 1}",
                    _place_outward_part(
                        build_port_adapter_retainer(),
                        angle,
                        center_z,
                        -4.0 - exploded_gap,
                    ),
                    "PRINTED_PETG",
                    True,
                ),
            )
        )
        if index < 2:
            components.extend(
                (
                    PortAssemblyComponent(
                        f"common_adapter_{index + 1}",
                        _place_outward_part(
                            build_planting_port_adapter(),
                            angle,
                            center_z,
                            common_z,
                        ),
                        "PRINTED_PETG",
                        True,
                    ),
                    PortAssemblyComponent(
                        f"netpot_adapter_{index + 1}",
                        _place_outward_part(
                            build_netpot_60_adapter(),
                            angle,
                            center_z,
                            4.0 + 2.0 * exploded_gap,
                        ),
                        "PRINTED_PETG",
                        True,
                    ),
                    PortAssemblyComponent(
                        f"netpot_reference_{index + 1}",
                        _place_netpot(
                            angle,
                            center_z,
                            exploded_gap,
                        ),
                        "REFERENCE_PURCHASED_PART",
                        False,
                    ),
                )
            )
        else:
            components.append(
                PortAssemblyComponent(
                    "blank_port_cap_3",
                    _place_outward_part(
                        build_blank_port_cap(),
                        angle,
                        center_z,
                        common_z,
                    ),
                    "PRINTED_PETG",
                    True,
                )
            )
    return tuple(components)


def build_planting_module_ports_reference() -> cq.Workplane:
    shapes = [component.model.val() for component in port_assembly_components()]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])

