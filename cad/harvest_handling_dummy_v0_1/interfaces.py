"""Validation for HHD-V001 interfaces; independent from CUT-DUMMY."""

from __future__ import annotations

import math

from .parameters import (
    ALLOWED_DIRECTIONS,
    ALLOWED_TILT_ANGLES,
    BASE_SOCKET,
    ROOT_BASE,
    ROOT_MOUNT,
    STEM_PLUG_IF,
    BaseSocketInterface,
    RootBaseParams,
    RootMountParams,
    StemPlugInterface,
    StemSocketParams,
)


def require_finite(**values: float) -> None:
    """Reject non-numeric, NaN, and infinite values."""

    for name, value in values.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")


def require_positive(**values: float) -> None:
    """Require finite values greater than zero."""

    require_finite(**values)
    for name, value in values.items():
        if value <= 0.0:
            raise ValueError(f"{name} must be positive, got {value!r}")


def require_non_negative(**values: float) -> None:
    """Require finite values greater than or equal to zero."""

    require_finite(**values)
    for name, value in values.items():
        if value < 0.0:
            raise ValueError(f"{name} must be non-negative, got {value!r}")


def validate_direction(direction_deg: float) -> None:
    """Require one of the eight fixed index directions."""

    require_finite(direction_deg=direction_deg)
    if direction_deg not in ALLOWED_DIRECTIONS:
        raise ValueError(
            f"direction must be one of {ALLOWED_DIRECTIONS}, got {direction_deg}"
        )


def validate_root_base(params: RootBaseParams = ROOT_BASE) -> None:
    """Validate the four-module base envelope and minimum features."""

    require_positive(
        assembled_width=params.assembled_width,
        assembled_length=params.assembled_length,
        module_width=params.module_width,
        module_length=params.module_length,
        module_thickness=params.module_thickness,
        min_socket_spacing=params.min_socket_spacing,
        target_layout_diameter=params.target_layout_diameter,
        max_layout_diameter=params.max_layout_diameter,
        min_socket_edge_margin=params.min_socket_edge_margin,
        m4_clearance_diameter=params.m4_clearance_diameter,
        locating_key_hole_diameter=params.locating_key_hole_diameter,
        locating_key_depth=params.locating_key_depth,
        push_out_hole_diameter=params.push_out_hole_diameter,
        petg_min_wall=params.petg_min_wall,
    )
    if params.petg_min_wall < 2.0:
        raise ValueError("PETG minimum wall must be at least 2.0 mm")
    if params.socket_count_per_module != 6:
        raise ValueError("each root module requires exactly 6 sockets")
    if params.assembled_width != 2.0 * params.module_width:
        raise ValueError("assembled width must equal two module widths")
    if params.assembled_length != 2.0 * params.module_length:
        raise ValueError("assembled length must equal two module lengths")
    if params.target_layout_diameter > params.max_layout_diameter:
        raise ValueError("target layout diameter exceeds maximum")
    if params.locating_key_depth >= params.module_thickness:
        raise ValueError("locating key depth exceeds base thickness")


def validate_root_mount(params: RootMountParams = ROOT_MOUNT) -> None:
    """Validate the two-piece workbench mount."""

    require_positive(
        assembled_width=params.assembled_width,
        assembled_length=params.assembled_length,
        half_width=params.half_width,
        thickness=params.thickness,
        m6_clearance_diameter=params.m6_clearance_diameter,
        m4_clearance_diameter=params.m4_clearance_diameter,
        locating_pin_diameter=params.locating_pin_diameter,
        locating_pin_height=params.locating_pin_height,
        seam_tongue_depth=params.seam_tongue_depth,
        seam_tongue_length=params.seam_tongue_length,
        seam_clearance=params.seam_clearance,
        petg_min_wall=params.petg_min_wall,
    )
    if params.petg_min_wall < 2.0:
        raise ValueError("PETG minimum wall must be at least 2.0 mm")
    if params.assembled_width != 2.0 * params.half_width:
        raise ValueError("mount width must equal two nominal half widths")


def validate_base_socket_interface(
    interface: BaseSocketInterface = BASE_SOCKET,
) -> None:
    """Validate provisional shank, receiver, index, and snap relations."""

    require_positive(
        shank_diameter=interface.shank_diameter,
        receiver_diameter=interface.receiver_diameter,
        index_af=interface.index_af,
        receiver_index_af=interface.receiver_index_af,
        index_depth=interface.index_depth,
        insertion_depth=interface.insertion_depth,
        snap_interference=interface.snap_interference,
        shank_split_width=interface.shank_split_width,
    )
    if interface.receiver_diameter <= interface.shank_diameter:
        raise ValueError("base receiver must be larger than socket shank")
    if interface.receiver_index_af <= interface.index_af:
        raise ValueError("base index receiver must be larger than index flange")
    if interface.insertion_depth < 12.0:
        raise ValueError("base socket insertion depth must be at least 12 mm")
    if interface.index_depth > interface.insertion_depth:
        raise ValueError("index depth cannot exceed insertion depth")
    if interface.snap_interference not in interface.snap_candidate_values:
        raise ValueError("snap interference must be one of the calibration candidates")
    if interface.calibration_status != "CALIBRATION_PENDING":
        raise ValueError("base socket interface must remain CALIBRATION_PENDING")


def validate_stem_plug_interface(
    interface: StemPlugInterface = STEM_PLUG_IF,
) -> None:
    """Validate the common 6 mm plug interface."""

    require_positive(
        shank_diameter=interface.shank_diameter,
        shank_length=interface.shank_length,
        receiver_diameter=interface.receiver_diameter,
        receiver_entry_chamfer=interface.receiver_entry_chamfer,
        receiver_slot_width=interface.receiver_slot_width,
        flange_diameter=interface.flange_diameter,
        flange_thickness=interface.flange_thickness,
    )
    if interface.receiver_diameter <= interface.shank_diameter:
        raise ValueError("stem receiver must be larger than 6 mm plug shank")
    if interface.shank_length < 18.0:
        raise ValueError("stem plug insertion depth must be at least 18 mm")
    if interface.calibration_status != "CALIBRATION_PENDING":
        raise ValueError("stem plug interface must remain CALIBRATION_PENDING")


def validate_stem_socket(params: StemSocketParams) -> None:
    """Validate a fixed-angle exchangeable socket."""

    require_non_negative(
        tilt_angle_deg=params.tilt_angle_deg,
        tilt_direction_deg=params.tilt_direction_deg,
    )
    require_positive(
        outer_tube_diameter=params.outer_tube_diameter,
        outer_axis_length=params.outer_axis_length,
        lower_solid_axis_length=params.lower_solid_axis_length,
        standard_fillet=params.standard_fillet,
        petg_min_wall=params.petg_min_wall,
    )
    if params.tilt_angle_deg not in ALLOWED_TILT_ANGLES:
        raise ValueError(f"unsupported tilt angle: {params.tilt_angle_deg}")
    validate_direction(params.tilt_direction_deg)
    if params.petg_min_wall < 2.0:
        raise ValueError("PETG minimum wall must be at least 2.0 mm")
    radial_wall = 0.5 * (
        params.outer_tube_diameter - STEM_PLUG_IF.receiver_diameter
    )
    if radial_wall < params.petg_min_wall:
        raise ValueError("stem socket radial wall is below PETG minimum")
    if params.outer_axis_length - params.lower_solid_axis_length < (
        STEM_PLUG_IF.shank_length
    ):
        raise ValueError("stem receiver insertion depth is insufficient")


def validate_all_interfaces() -> None:
    """Validate every standard interface at import time."""

    validate_root_base()
    validate_root_mount()
    validate_base_socket_interface()
    validate_stem_plug_interface()
    for angle in ALLOWED_TILT_ANGLES:
        validate_stem_socket(StemSocketParams(tilt_angle_deg=angle))


validate_all_interfaces()
