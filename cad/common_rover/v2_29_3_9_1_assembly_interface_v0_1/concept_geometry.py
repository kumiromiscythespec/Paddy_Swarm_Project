from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from authority_adapter import AuthorityContext


@dataclass(frozen=True)
class ConceptBox:
    component_id: str
    minimum_xyz_mm: tuple[float, float, float]
    maximum_xyz_mm: tuple[float, float, float]
    visual_class: str
    geometry_status: str


def authority_component_boxes(
    context: AuthorityContext,
) -> tuple[ConceptBox, ...]:
    result = []
    for component in context.parameters.components:
        if component.component_id.startswith("V22939-FPB-"):
            visual_class = "aluminum"
        elif component.component_id == "V22939-CBOX":
            visual_class = "cbox"
        elif component.component_id == "V22939-BBOX":
            visual_class = "bbox"
        else:
            visual_class = "battery"
        result.append(
            ConceptBox(
                component_id=component.component_id,
                minimum_xyz_mm=component.minimum,
                maximum_xyz_mm=component.maximum,
                visual_class=visual_class,
                geometry_status="AUTHORITY_ENVELOPE_ONLY",
            )
        )
    return tuple(result)


def schematic_components() -> tuple[dict, ...]:
    return (
        {
            "component_id": "PRINTED-CBOX-SADDLES-A1-A2",
            "visual_class": "printed",
            "geometry_status": "SCHEMATIC_NOT_TO_SCALE",
        },
        {
            "component_id": "PRINTED-BBOX-SADDLES-B1-B2",
            "visual_class": "printed",
            "geometry_status": "SCHEMATIC_NOT_TO_SCALE_HOLD",
        },
        {
            "component_id": "METAL-LOWER-FRAME-CRADLE",
            "visual_class": "metal",
            "geometry_status": "CONCEPT_ONLY_HOLD",
        },
        {
            "component_id": "INDEPENDENT-METAL-REAR-SUPPORT",
            "visual_class": "metal",
            "geometry_status": "CONCEPT_ONLY_HOLD",
        },
        {
            "component_id": "FLOAT-MODULES-LEFT-RIGHT",
            "visual_class": "float",
            "geometry_status": "SCHEMATIC_NOT_TO_SCALE",
        },
        {
            "component_id": "REMOVABLE-PINS-AND-R-PINS",
            "visual_class": "fastener",
            "geometry_status": "CANDIDATE_ONLY",
        },
    )


def top_rect(
    minimum: Iterable[float],
    maximum: Iterable[float],
) -> tuple[float, float, float, float]:
    low = tuple(minimum)
    high = tuple(maximum)

    def px(x: float) -> float:
        return 430.0 - 2.0 * x

    def py(y: float) -> float:
        return 390.0 - 1.15 * y

    x1, x2 = sorted((px(low[0]), px(high[0])))
    y1, y2 = sorted((py(low[1]), py(high[1])))
    return x1, y1, x2 - x1, y2 - y1


def side_rect(
    minimum: Iterable[float],
    maximum: Iterable[float],
) -> tuple[float, float, float, float]:
    low = tuple(minimum)
    high = tuple(maximum)

    def px(y: float) -> float:
        return 340.0 + 1.15 * y

    def py(z: float) -> float:
        return 610.0 - 2.7 * z

    x1, x2 = sorted((px(low[1]), px(high[1])))
    y1, y2 = sorted((py(low[2]), py(high[2])))
    return x1, y1, x2 - x1, y2 - y1
