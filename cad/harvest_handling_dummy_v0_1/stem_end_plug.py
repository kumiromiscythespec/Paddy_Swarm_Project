"""Five HHD-STEM-PLUG-V001 commercial-rod adapter presets."""

from __future__ import annotations

from dataclasses import replace

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_non_negative, require_positive, validate_stem_plug_interface
from .parameters import STEM_PLUG_IF, StemPlugParams


PRESET_DATA: dict[str, tuple[str, float, bool]] = {
    "rod_od_2p0": ("HU-H0-HHD-PLG-ROD-2P0", 2.0, False),
    "rod_od_3p0": ("HU-H0-HHD-PLG-ROD-3P0", 3.0, False),
    "rod_od_4p0": ("HU-H0-HHD-PLG-ROD-4P0", 4.0, False),
    "rod_od_5p0": ("HU-H0-HHD-PLG-ROD-5P0", 5.0, False),
    "blank_custom": ("HU-H0-HHD-PLG-BLANK", 0.0, True),
}


def params_for_preset(name: str) -> StemPlugParams:
    """Return one fixed rod-diameter or drillable-blank preset."""

    try:
        part_id, diameter, blank = PRESET_DATA[name]
    except KeyError as exc:
        raise ValueError(f"unknown HHD stem plug preset: {name!r}") from exc
    return replace(
        StemPlugParams(),
        preset=name,
        part_id=part_id,
        material_side_od=diameter,
        blank_custom=blank,
    )


def validate_params(params: StemPlugParams) -> None:
    """Validate common interface and provisional material-side sleeve."""

    validate_stem_plug_interface()
    require_non_negative(
        material_side_od=params.material_side_od,
        material_clearance=params.material_clearance,
    )
    require_positive(
        material_insertion_depth=params.material_insertion_depth,
        material_sleeve_length=params.material_sleeve_length,
        material_sleeve_wall=params.material_sleeve_wall,
        sleeve_split_width=params.sleeve_split_width,
    )
    if params.preset not in PRESET_DATA:
        raise ValueError(f"unknown HHD stem plug preset: {params.preset!r}")
    if params.calibration_status != "CALIBRATION_PENDING":
        raise ValueError("stem material fit must remain CALIBRATION_PENDING")
    if params.blank_custom != PRESET_DATA[params.preset][2]:
        raise ValueError("blank_custom flag does not match preset")
    if not params.blank_custom and params.material_side_od <= 0.0:
        raise ValueError("rod preset requires a positive material diameter")
    if params.material_insertion_depth > params.material_sleeve_length:
        raise ValueError("rod insertion exceeds sleeve length")
    if params.material_sleeve_wall < 2.0:
        raise ValueError("rod sleeve radial wall must be at least 2 mm")


def material_sleeve_outer_diameter(params: StemPlugParams) -> float:
    """Return sleeve OD while preserving a 2 mm radial wall."""

    if params.blank_custom:
        return STEM_PLUG_IF.flange_diameter
    return params.material_side_od + 2.0 * params.material_sleeve_wall


def build(params: StemPlugParams = StemPlugParams()) -> cq.Workplane:
    """Build one split-sleeve rod adapter or solid drillable blank."""

    validate_params(params)
    common_shank = (
        cq.Workplane("XY")
        .circle(0.5 * STEM_PLUG_IF.shank_diameter)
        .extrude(STEM_PLUG_IF.shank_length)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * STEM_PLUG_IF.flange_diameter)
        .extrude(STEM_PLUG_IF.flange_thickness)
        .translate((0.0, 0.0, STEM_PLUG_IF.shank_length))
    )
    sleeve_bottom = STEM_PLUG_IF.shank_length + STEM_PLUG_IF.flange_thickness
    sleeve = (
        cq.Workplane("XY")
        .circle(0.5 * material_sleeve_outer_diameter(params))
        .extrude(params.material_sleeve_length)
        .translate((0.0, 0.0, sleeve_bottom))
    )
    part = common_shank.union(flange).union(sleeve)

    if not params.blank_custom:
        receiver_bottom = (
            sleeve_bottom
            + params.material_sleeve_length
            - params.material_insertion_depth
        )
        rod_receiver = (
            cq.Workplane("XY")
            .circle(
                0.5 * (params.material_side_od + params.material_clearance)
            )
            .extrude(params.material_insertion_depth + 0.1)
            .translate((0.0, 0.0, receiver_bottom))
        )
        split = (
            cq.Workplane("XY")
            .box(
                0.5 * material_sleeve_outer_diameter(params) + 1.0,
                params.sleeve_split_width,
                params.material_insertion_depth + 0.1,
                centered=(False, True, False),
            )
            .translate((0.0, 0.0, receiver_bottom))
        )
        part = part.cut(rod_receiver).cut(split)

    direction_notch = (
        cq.Workplane("XY")
        .center(0.5 * STEM_PLUG_IF.flange_diameter, 0.0)
        .circle(0.75)
        .extrude(STEM_PLUG_IF.flange_thickness + 0.2)
        .translate((0.0, 0.0, STEM_PLUG_IF.shank_length - 0.1))
    )
    part = part.cut(direction_notch)
    validate_print_bounds(part, params.part_id)
    return part
