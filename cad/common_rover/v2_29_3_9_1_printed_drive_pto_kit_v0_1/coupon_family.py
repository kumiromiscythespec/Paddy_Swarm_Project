from __future__ import annotations

from dataclasses import dataclass
import math

from drive_pto_contract import (
    B10_BORE_COMPENSATION_MM,
    BELT_WIDTH_MM,
    D6_BORE_COMPENSATION_MM,
    MEASUREMENT_STATUS,
    TOOTH_COMPENSATION_MM,
    TPU_THICKNESS_CANDIDATES_MM,
)
from geometry_common import (
    BuiltPart,
    box_xyz,
    cylinder_z,
    engrave_part_number,
)
from htd5m_profile import external_toothed_blank, pulley_radii_mm
from part_number_registry import PART_BY_KEY


VARIANTS = ("A", "B", "C")


def _d_bore_tool(
    diameter_mm: float,
    flat_depth_mm: float,
    height_mm: float,
    *,
    x: float,
):
    radius = diameter_mm / 2.0
    round_tool = cylinder_z(radius, height_mm + 2.0, x=x, z=-1.0)
    flat_x = x + radius - flat_depth_mm
    minimum_x = x - radius - 1.0
    clip = box_xyz(
        flat_x - minimum_x,
        diameter_mm + 2.0,
        height_mm + 2.0,
        x=(minimum_x + flat_x) / 2.0,
        z=-1.0,
    )
    return round_tool.intersect(clip)


def build_bore_coupon(
    key: str,
    *,
    nominal_mm: float,
    compensation_mm: float,
    d_shaft: bool,
) -> BuiltPart:
    spec = PART_BY_KEY[key]
    plate = box_xyz(58.0, 32.0, 6.0, z=0.0)
    hole_x = 17.0
    diameter = nominal_mm + compensation_mm
    tool = (
        _d_bore_tool(diameter, 0.60, 6.0, x=hole_x)
        if d_shaft
        else cylinder_z(diameter / 2.0, 8.0, x=hole_x, z=-1.0)
    )
    shape = plate.cut(tool)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-11.0, 6.0), (-11.0, -6.0)),
        surface_z=6.0,
        size_mm=2.5,
        metadata={
            "coupon_type": "D6_BORE" if d_shaft else "B10_BORE",
            "nominal_mm": nominal_mm,
            "compensation_mm": compensation_mm,
            "candidate_diameter_mm": diameter,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": 3.0,
            "print_orientation": "PLATE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_tooth_coupon(
    key: str,
    *,
    teeth: int,
    tooth_width_compensation_mm: float,
) -> BuiltPart:
    spec = PART_BY_KEY[key]
    height = 5.0
    shape = external_toothed_blank(
        teeth,
        height,
        tooth_width_compensation_mm=tooth_width_compensation_mm,
    )
    radius = pulley_radii_mm(teeth)["tip_radius_mm"]
    marking_y = 5.5 if teeth == 20 else 17.0
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, marking_y), (0.0, -marking_y)),
        surface_z=height,
        size_mm=2.3 if teeth == 20 else 2.7,
        metadata={
            "coupon_type": f"{teeth}T_TOOTH_ENGAGEMENT",
            "teeth": teeth,
            "tooth_width_compensation_mm": tooth_width_compensation_mm,
            "commercial_belt_fit": True,
            "printed_tpu_belt_fit": True,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": 3.0,
            "print_orientation": "LARGE FLAT FACE DOWN",
            "support": "OFF",
            "trapped_support": False,
            "outside_radius_mm": radius,
        },
    )


def build_fit_coupon(key: str, *, printed_belt: bool) -> BuiltPart:
    spec = PART_BY_KEY[key]
    height = 7.0
    shape = external_toothed_blank(20, height)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 6.0), (0.0, -6.0)),
        surface_z=height,
        size_mm=2.1,
        metadata={
            "coupon_type": (
                "PRINTED_TPU_BELT_FIT"
                if printed_belt
                else "COMMERCIAL_450_5M_15_BELT_FIT"
            ),
            "teeth": 20,
            "belt_width_mm": BELT_WIDTH_MM,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": 3.0,
            "print_orientation": "LARGE FLAT FACE DOWN",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_pcd24_coupon() -> BuiltPart:
    spec = PART_BY_KEY["pcd24_hub_coupon"]
    shape = box_xyz(54.0, 54.0, 6.0)
    tools = [cylinder_z(5.1, 8.0, z=-1.0)]
    for index in range(4):
        angle = index * math.pi / 2.0
        tools.append(
            cylinder_z(
                2.15,
                8.0,
                x=12.0 * math.cos(angle),
                y=12.0 * math.sin(angle),
                z=-1.0,
            )
        )
    shape = shape.cut(*tools)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 20.0), (0.0, -20.0)),
        surface_z=6.0,
        size_mm=2.7,
        metadata={
            "coupon_type": "PCD24_4XM4_HUB",
            "pcd_mm": 24.0,
            "hole_diameter_mm": 4.3,
            "center_bore_mm": 10.2,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": 4.0,
            "print_orientation": "PLATE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_clamp_insert_coupon() -> BuiltPart:
    spec = PART_BY_KEY["clamp_insert_coupon"]
    shape = box_xyz(68.0, 30.0, 9.0)
    shape = shape.cut(
        cylinder_z(1.7, 11.0, x=20.0, z=-1.0),
        cylinder_z(2.25, 11.0, x=8.0, z=-1.0),
    )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-16.0, 6.0), (-16.0, -6.0)),
        surface_z=9.0,
        size_mm=2.4,
        metadata={
            "coupon_type": "CLAMP_BOLT_AND_HEAT_SET_INSERT",
            "through_hole_mm": 3.4,
            "insert_pilot_candidate_mm": 4.5,
            "petg_thread_is_primary": False,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": 4.0,
            "print_orientation": "PLATE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_tpu_thickness_coupon() -> BuiltPart:
    spec = PART_BY_KEY["tpu_thickness_coupon"]
    shapes = []
    for index, thickness in enumerate(TPU_THICKNESS_CANDIDATES_MM):
        shapes.append(
            box_xyz(
                30.0,
                15.0,
                thickness,
                x=(index - 1) * 30.0,
                z=0.0,
            )
        )
    bridge = box_xyz(90.0, 3.0, min(TPU_THICKNESS_CANDIDATES_MM))
    shape = shapes[0].fuse(*shapes[1:], bridge)
    label = box_xyz(40.0, 10.0, 3.0, y=10.0)
    shape = shape.fuse(label)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 8.0), (0.0, 12.0)),
        surface_z=3.0,
        size_mm=2.0,
        metadata={
            "coupon_type": "TPU_BACKING_THICKNESS",
            "candidate_thicknesses_mm": TPU_THICKNESS_CANDIDATES_MM,
            "measurement_result": MEASUREMENT_STATUS,
            "minimum_wall_mm": min(TPU_THICKNESS_CANDIDATES_MM),
            "print_orientation": "STRIPS FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_all_coupons() -> list[BuiltPart]:
    parts: list[BuiltPart] = []
    for variant, compensation in zip(VARIANTS, D6_BORE_COMPENSATION_MM):
        parts.append(
            build_bore_coupon(
                f"d6_{variant.lower()}",
                nominal_mm=6.0,
                compensation_mm=compensation,
                d_shaft=True,
            )
        )
    for variant, compensation in zip(VARIANTS, B10_BORE_COMPENSATION_MM):
        parts.append(
            build_bore_coupon(
                f"b10_{variant.lower()}",
                nominal_mm=10.0,
                compensation_mm=compensation,
                d_shaft=False,
            )
        )
    for teeth, prefix in ((20, "t20"), (60, "t60")):
        for variant, compensation in zip(VARIANTS, TOOTH_COMPENSATION_MM):
            parts.append(
                build_tooth_coupon(
                    f"{prefix}_{variant.lower()}",
                    teeth=teeth,
                    tooth_width_compensation_mm=compensation,
                )
            )
    parts.extend(
        (
            build_fit_coupon("commercial_belt_fit", printed_belt=False),
            build_fit_coupon("printed_belt_fit", printed_belt=True),
            build_pcd24_coupon(),
            build_clamp_insert_coupon(),
            build_tpu_thickness_coupon(),
        )
    )
    return parts


def coupon_manifest_rows() -> list[dict[str, object]]:
    rows = []
    for variant, value in zip(VARIANTS, D6_BORE_COMPENSATION_MM):
        spec = PART_BY_KEY[f"d6_{variant.lower()}"]
        rows.append(
            {
                "part_number": spec.part_number,
                "coupon_type": "D6_BORE",
                "variant": variant,
                "candidate_value_mm": 6.0 + value,
                "measurement_result": MEASUREMENT_STATUS,
                "filename": spec.filename,
            }
        )
    for variant, value in zip(VARIANTS, B10_BORE_COMPENSATION_MM):
        spec = PART_BY_KEY[f"b10_{variant.lower()}"]
        rows.append(
            {
                "part_number": spec.part_number,
                "coupon_type": "B10_BORE",
                "variant": variant,
                "candidate_value_mm": 10.0 + value,
                "measurement_result": MEASUREMENT_STATUS,
                "filename": spec.filename,
            }
        )
    for teeth, prefix in ((20, "t20"), (60, "t60")):
        for variant, value in zip(VARIANTS, TOOTH_COMPENSATION_MM):
            spec = PART_BY_KEY[f"{prefix}_{variant.lower()}"]
            rows.append(
                {
                    "part_number": spec.part_number,
                    "coupon_type": f"{teeth}T_TOOTH_ENGAGEMENT",
                    "variant": variant,
                    "candidate_value_mm": value,
                    "measurement_result": MEASUREMENT_STATUS,
                    "filename": spec.filename,
                }
            )
    for key, coupon_type in (
        ("commercial_belt_fit", "COMMERCIAL_450_5M_15_BELT_FIT"),
        ("printed_belt_fit", "PRINTED_TPU_BELT_FIT"),
        ("pcd24_hub_coupon", "PCD24_4XM4_HUB"),
        ("clamp_insert_coupon", "CLAMP_BOLT_INSERT"),
        ("tpu_thickness_coupon", "TPU_THICKNESS"),
    ):
        spec = PART_BY_KEY[key]
        rows.append(
            {
                "part_number": spec.part_number,
                "coupon_type": coupon_type,
                "variant": "MULTI" if key == "tpu_thickness_coupon" else "A",
                "candidate_value_mm": "SEE_GEOMETRY_METADATA",
                "measurement_result": MEASUREMENT_STATUS,
                "filename": spec.filename,
            }
        )
    joiner = PART_BY_KEY["joiner_fit"]
    rows.append(
        {
            "part_number": joiner.part_number,
            "coupon_type": "TPU_BELT_JOINER",
            "variant": "A",
            "candidate_value_mm": "SEE_GEOMETRY_METADATA",
            "measurement_result": MEASUREMENT_STATUS,
            "filename": joiner.filename,
        }
    )
    return rows
