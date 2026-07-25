"""Single-source design parameters for HHD-V001."""

from __future__ import annotations

from dataclasses import dataclass

from .cq_config import PRINT


@dataclass(frozen=True)
class RootBaseParams:
    """Four-module fixed-root base dimensions in mm."""

    assembled_width: float = 210.0
    assembled_length: float = 210.0
    module_width: float = 105.0
    module_length: float = 105.0
    module_thickness: float = 18.0
    socket_count_per_module: int = 6
    min_socket_spacing: float = 21.0
    target_layout_diameter: float = 145.0
    max_layout_diameter: float = 150.0
    min_socket_edge_margin: float = 8.0
    m4_clearance_diameter: float = 4.5
    m4_edge_offset: float = 6.0
    locating_key_hole_diameter: float = 5.8
    locating_key_depth: float = 3.0
    push_out_hole_diameter: float = 4.0
    petg_min_wall: float = PRINT.petg_min_wall_mm


@dataclass(frozen=True)
class RootMountParams:
    """Two-piece workbench mount dimensions in mm."""

    assembled_width: float = 210.0
    assembled_length: float = 210.0
    half_width: float = 105.0
    thickness: float = 6.0
    m6_clearance_diameter: float = 6.6
    m6_edge_offset: float = 15.0
    m4_clearance_diameter: float = 4.5
    locating_pin_diameter: float = 5.4
    locating_pin_height: float = 3.0
    seam_tongue_depth: float = 5.0
    seam_tongue_length: float = 28.0
    seam_clearance: float = 0.3
    petg_min_wall: float = PRINT.petg_min_wall_mm


@dataclass(frozen=True)
class BaseSocketInterface:
    """BASE-SOCKET-IF-V001 provisional connection in mm."""

    name: str = "BASE-SOCKET-IF-V001"
    shank_diameter: float = 12.8
    receiver_diameter: float = 13.2
    index_af: float = 16.0
    receiver_index_af: float = 16.4
    index_depth: float = 3.0
    insertion_depth: float = 12.0
    snap_interference: float = 0.25
    snap_candidate_values: tuple[float, ...] = (0.15, 0.25, 0.35)
    shank_split_width: float = 1.0
    calibration_status: str = "CALIBRATION_PENDING"


@dataclass(frozen=True)
class StemPlugInterface:
    """HHD-STEM-PLUG-V001 common plug-to-socket interface in mm."""

    name: str = "HHD-STEM-PLUG-V001"
    shank_diameter: float = 6.0
    shank_length: float = 18.0
    receiver_diameter: float = 6.25
    receiver_entry_chamfer: float = 0.6
    receiver_slot_width: float = 1.0
    flange_diameter: float = 10.0
    flange_thickness: float = 2.0
    calibration_status: str = "CALIBRATION_PENDING"


@dataclass(frozen=True)
class StemSocketParams:
    """One fixed-angle exchangeable stem socket in mm and degrees."""

    tilt_angle_deg: float = 0.0
    tilt_direction_deg: float = 0.0
    outer_tube_diameter: float = 12.0
    outer_axis_length: float = 28.0
    lower_solid_axis_length: float = 10.0
    standard_fillet: float = 1.0
    petg_min_wall: float = PRINT.petg_min_wall_mm


@dataclass(frozen=True)
class StemPlugParams:
    """One commercial-rod adapter preset in mm."""

    preset: str = "rod_od_4p0"
    part_id: str = "HU-H0-HHD-PLG-ROD-4P0"
    material_side_od: float = 4.0
    material_clearance: float = 0.20
    material_insertion_depth: float = 15.0
    material_sleeve_length: float = 18.0
    material_sleeve_wall: float = 2.0
    sleeve_split_width: float = 1.0
    blank_custom: bool = False
    calibration_status: str = "CALIBRATION_PENDING"


@dataclass(frozen=True)
class GaugeParams:
    """Flat gauge and record-plate minimum feature sizes."""

    plate_thickness: float = 3.0
    label_height: float = 0.6
    label_font_size: float = 6.0
    line_width: float = 1.2
    zip_tie_slot_width: float = 4.0
    zip_tie_slot_length: float = 12.0


ROOT_BASE = RootBaseParams()
ROOT_MOUNT = RootMountParams()
BASE_SOCKET = BaseSocketInterface()
STEM_PLUG_IF = StemPlugInterface()
GAUGE = GaugeParams()

ALLOWED_TILT_ANGLES: tuple[float, ...] = (0.0, 10.0, 20.0, 30.0)
ALLOWED_DIRECTIONS: tuple[float, ...] = (
    0.0,
    45.0,
    90.0,
    135.0,
    180.0,
    225.0,
    270.0,
    315.0,
)
HEIGHTS_MM: dict[str, float] = {
    "LOW": 650.0,
    "STANDARD": 750.0,
    "HIGH": 850.0,
}
