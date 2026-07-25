from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from drive_pto_contract import BELT_WIDTH_MM, PITCH_MM, pitch_diameter_mm
from geometry_common import (
    BuiltPart,
    box_xyz,
    cylinder_z,
    engrave_part_number,
    require_cadquery,
)
from htd5m_profile import external_toothed_blank, pulley_radii_mm
from part_number_registry import PART_BY_KEY, PULLEY_PARTS


BOTTOM_FLANGE_MM = 1.5
TOP_FLANGE_MM = 1.8
TOTAL_HEIGHT_MM = BOTTOM_FLANGE_MM + BELT_WIDTH_MM + TOP_FLANGE_MM
FLANGE_RADIAL_CLEARANCE_MM = 1.8
PCD24_DIAMETER_MM = 24.0
PCD_HOLE_DIAMETER_MM = 4.3
CLAMP_SLOT_MM = 1.2
CLAMP_BOLT_DIAMETER_MM = 3.4


@dataclass(frozen=True)
class PulleyConfig:
    key: str
    path_id: str
    teeth: int
    bore_type: str
    bore_nominal_mm: float
    bore_compensation_mm: float
    d_flat_depth_mm: float | None
    split_clamp: bool
    pcd24_4xm4: bool
    shaft_measurement_status: str


PULLEY_CONFIGS: tuple[PulleyConfig, ...] = (
    PulleyConfig("drive_l_20t_pulley", "DRIVE-L", 20, "D_SHAFT", 6.0, 0.0, 0.60, True, False, "JGB37-520_AUTHORITY"),
    PulleyConfig("drive_l_60t_pulley", "DRIVE-L", 60, "ROUND", 10.0, 0.0, None, False, True, "CALIBRATION_PENDING"),
    PulleyConfig("drive_r_20t_pulley", "DRIVE-R", 20, "D_SHAFT", 6.0, 0.0, 0.60, True, False, "JGB37-520_AUTHORITY"),
    PulleyConfig("drive_r_60t_pulley", "DRIVE-R", 60, "ROUND", 10.0, 0.0, None, False, True, "CALIBRATION_PENDING"),
    PulleyConfig("pto_a_20t_pulley", "PTO-A", 20, "ROUND", 10.0, 0.0, None, True, False, "CALIBRATION_PENDING"),
    PulleyConfig("pto_a_60t_pulley", "PTO-A", 60, "ROUND", 10.0, 0.0, None, True, True, "CALIBRATION_PENDING"),
    PulleyConfig("pto_b_20t_pulley", "PTO-B", 20, "ROUND", 10.0, 0.0, None, True, False, "CALIBRATION_PENDING"),
    PulleyConfig("pto_b_60t_pulley", "PTO-B", 60, "ROUND", 10.0, 0.0, None, True, True, "CALIBRATION_PENDING"),
)
CONFIG_BY_KEY = {config.key: config for config in PULLEY_CONFIGS}


def _bore_tool(config: PulleyConfig, height_mm: float):
    diameter = config.bore_nominal_mm + config.bore_compensation_mm
    radius = diameter / 2.0
    round_tool = cylinder_z(radius, height_mm + 2.0, z=-1.0)
    if config.bore_type != "D_SHAFT":
        return round_tool
    if config.d_flat_depth_mm is None:
        raise ValueError("D_FLAT_DEPTH_REQUIRED")
    flat_x = radius - config.d_flat_depth_mm
    minimum_x = -radius - 1.0
    clip_length = flat_x - minimum_x
    clip = box_xyz(
        clip_length,
        diameter + 2.0,
        height_mm + 2.0,
        x=(minimum_x + flat_x) / 2.0,
        z=-1.0,
    )
    return round_tool.intersect(clip)


def _cut_clamp(shape, config: PulleyConfig, tip_radius: float):
    if not config.split_clamp:
        return shape
    bore_radius = (
        config.bore_nominal_mm + config.bore_compensation_mm
    ) / 2.0
    slot_start = bore_radius - 0.25
    slot_end = tip_radius + FLANGE_RADIAL_CLEARANCE_MM + 1.0
    slot = box_xyz(
        slot_end - slot_start,
        CLAMP_SLOT_MM,
        TOTAL_HEIGHT_MM + 2.0,
        x=(slot_start + slot_end) / 2.0,
        z=-1.0,
    )
    cq = require_cadquery()
    bolt_x = bore_radius + 3.3
    bolt = cq.Solid.makeCylinder(
        CLAMP_BOLT_DIAMETER_MM / 2.0,
        2.0 * (tip_radius + 2.0),
        cq.Vector(bolt_x, -(tip_radius + 2.0), TOTAL_HEIGHT_MM / 2.0),
        cq.Vector(0.0, 1.0, 0.0),
    )
    return shape.cut(slot, bolt)


def _cut_pcd24(shape, config: PulleyConfig):
    if not config.pcd24_4xm4:
        return shape
    tools = []
    for index in range(4):
        angle = math.pi / 2.0 * index
        tools.append(
            cylinder_z(
                PCD_HOLE_DIAMETER_MM / 2.0,
                TOTAL_HEIGHT_MM + 2.0,
                x=PCD24_DIAMETER_MM / 2.0 * math.cos(angle),
                y=PCD24_DIAMETER_MM / 2.0 * math.sin(angle),
                z=-1.0,
            )
        )
    return shape.cut(*tools)


def build_pulley(config: PulleyConfig) -> BuiltPart:
    spec = PART_BY_KEY[config.key]
    radii = pulley_radii_mm(config.teeth)
    toothed = external_toothed_blank(
        config.teeth,
        BELT_WIDTH_MM,
        z_mm=BOTTOM_FLANGE_MM,
    )
    flange_radius = radii["tip_radius_mm"] + FLANGE_RADIAL_CLEARANCE_MM
    bottom_flange = cylinder_z(flange_radius, BOTTOM_FLANGE_MM)
    top_flange = cylinder_z(
        flange_radius,
        TOP_FLANGE_MM,
        z=BOTTOM_FLANGE_MM + BELT_WIDTH_MM,
    )
    hub_radius = 11.5 if config.bore_nominal_mm <= 6.0 else 14.0
    hub = cylinder_z(hub_radius, TOTAL_HEIGHT_MM)
    shape = toothed.fuse(bottom_flange, top_flange, hub)
    shape = shape.cut(_bore_tool(config, TOTAL_HEIGHT_MM))
    shape = _cut_clamp(shape, config, radii["tip_radius_mm"])
    shape = _cut_pcd24(shape, config)
    marking_y = 8.0 if config.teeth == 20 else 21.0
    metadata = {
        "profile": "HTD-5M",
        "path_id": config.path_id,
        "teeth": config.teeth,
        "pitch_mm": PITCH_MM,
        "pitch_diameter_mm": pitch_diameter_mm(config.teeth),
        "belt_width_mm": BELT_WIDTH_MM,
        "bore_type": config.bore_type,
        "bore_nominal_mm": config.bore_nominal_mm,
        "bore_compensation_mm": config.bore_compensation_mm,
        "d_flat_depth_mm": config.d_flat_depth_mm,
        "split_clamp": config.split_clamp,
        "set_screw_only": False,
        "metal_fastener_required": config.split_clamp or config.pcd24_4xm4,
        "pcd24_4xm4": config.pcd24_4xm4,
        "hub_pcd_mm": PCD24_DIAMETER_MM if config.pcd24_4xm4 else None,
        "hub_hole_diameter_mm": (
            PCD_HOLE_DIAMETER_MM if config.pcd24_4xm4 else None
        ),
        "shaft_measurement_status": config.shaft_measurement_status,
        "flange_radius_mm": flange_radius,
        "tooth_region_height_mm": BELT_WIDTH_MM,
        "minimum_wall_mm": min(
            hub_radius
            - (config.bore_nominal_mm + config.bore_compensation_mm) / 2.0,
            BOTTOM_FLANGE_MM,
        ),
        "print_orientation": "LARGE FLAT FLANGE DOWN",
        "support": "OFF",
        "trapped_support": False,
        "warping_relief": "RADIAL PCD HOLES AND THIN REMOVABLE-FLANGE OPTION",
        "safety": "LOW-LOAD TEST ONLY",
    }
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, marking_y), (0.0, -marking_y)),
        surface_z=TOTAL_HEIGHT_MM,
        size_mm=2.4 if config.teeth == 20 else 2.8,
        depth_mm=0.55,
        metadata=metadata,
    )


def build_all_pulleys() -> list[BuiltPart]:
    return [build_pulley(config) for config in PULLEY_CONFIGS]


def pulley_manifest_rows() -> list[dict[str, object]]:
    rows = []
    for config in PULLEY_CONFIGS:
        spec = PART_BY_KEY[config.key]
        rows.append(
            {
                "part_number": spec.part_number,
                "path_id": config.path_id,
                "teeth": config.teeth,
                "pitch_mm": PITCH_MM,
                "pitch_diameter_mm": f"{pitch_diameter_mm(config.teeth):.12f}",
                "belt_width_mm": BELT_WIDTH_MM,
                "bore_type": config.bore_type,
                "bore_nominal_mm": config.bore_nominal_mm,
                "bore_compensation_mm": config.bore_compensation_mm,
                "split_clamp": config.split_clamp,
                "pcd24_4xm4": config.pcd24_4xm4,
                "physical_marking": "ENGRAVED",
                "classification": spec.classification,
                "filename": spec.filename,
            }
        )
    return rows
