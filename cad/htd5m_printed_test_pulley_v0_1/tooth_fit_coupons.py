"""Curved six-groove HTD 5M belt-fit coupons."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from htd5m_profile import (
    coupon_span_angle_deg,
    make_groove_cutter,
    outside_diameter_mm,
    profile_for_tooth_count,
    station_angles_deg,
)
from parameters import (
    COUPON_BACKING_THICKNESS_MM,
    COUPON_ENGRAVING_DEPTH_MM,
    COUPON_TOOTH_COUNT,
    COUPONS,
    FONT_PATH,
    TOOTH_FACE_WIDTH_MM,
    CouponSpec,
)


def _point_on_radius(radius_mm: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = radians(angle_deg)
    return (radius_mm * cos(angle_rad), radius_mm * sin(angle_rad))


def _annular_sector(
    inner_radius_mm: float,
    outer_radius_mm: float,
    span_angle_deg: float,
    width_mm: float,
) -> cq.Workplane:
    half_angle = span_angle_deg / 2.0
    inner_start = _point_on_radius(inner_radius_mm, -half_angle)
    outer_start = _point_on_radius(outer_radius_mm, -half_angle)
    outer_mid = _point_on_radius(outer_radius_mm, 0.0)
    outer_end = _point_on_radius(outer_radius_mm, half_angle)
    inner_end = _point_on_radius(inner_radius_mm, half_angle)
    inner_mid = _point_on_radius(inner_radius_mm, 0.0)

    return (
        cq.Workplane("XY")
        .moveTo(*inner_start)
        .lineTo(*outer_start)
        .threePointArc(outer_mid, outer_end)
        .lineTo(*inner_end)
        .threePointArc(inner_mid, inner_start)
        .close()
        .extrude(width_mm)
    )


def _engrave_id(
    model: cq.Workplane,
    text: str,
    inner_radius_mm: float,
    top_z_mm: float,
) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY")
        .workplane(offset=top_z_mm - COUPON_ENGRAVING_DEPTH_MM)
        .text(
            text,
            fontsize=2.4,
            distance=COUPON_ENGRAVING_DEPTH_MM + 0.10,
            combine=True,
            clean=True,
            fontPath=str(FONT_PATH),
        )
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 90.0)
        .translate((inner_radius_mm + 1.6, 0.0, 0.0))
    )
    return model.cut(cutter)


def build_tooth_fit_coupon(spec: CouponSpec) -> cq.Workplane:
    """Build one calibration coupon; this is not a complete pulley."""

    profile = profile_for_tooth_count(spec.pulley_teeth)
    outer_radius = outside_diameter_mm(spec.pulley_teeth) / 2.0
    nominal_root_radius = outer_radius - profile.groove_depth_mm
    inner_radius = nominal_root_radius - COUPON_BACKING_THICKNESS_MM
    if inner_radius <= 0.0:
        raise ValueError(f"{spec.key}: backing thickness leaves no inner radius")

    coupon = _annular_sector(
        inner_radius,
        outer_radius,
        coupon_span_angle_deg(spec.pulley_teeth, COUPON_TOOTH_COUNT),
        TOOTH_FACE_WIDTH_MM,
    )
    for station_angle in station_angles_deg(spec.pulley_teeth, COUPON_TOOTH_COUNT):
        coupon = coupon.cut(
            make_groove_cutter(
                spec.pulley_teeth,
                spec.clearance_mm,
                TOOTH_FACE_WIDTH_MM,
                station_angle,
            )
        )

    coupon = _engrave_id(
        coupon, spec.id_text, inner_radius, TOOTH_FACE_WIDTH_MM
    )
    return coupon.clean()


def build_all_tooth_fit_coupons() -> dict[str, cq.Workplane]:
    return {spec.key: build_tooth_fit_coupon(spec) for spec in COUPONS}


if __name__ == "__main__":
    for name, model in build_all_tooth_fit_coupons().items():
        print(name, model.val().BoundingBox())
