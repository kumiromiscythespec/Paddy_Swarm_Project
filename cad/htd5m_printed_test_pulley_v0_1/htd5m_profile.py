"""Nominal HTD 5M groove geometry used by the calibration coupons.

The pitch and pitch-line differential follow ISO 13050:2022.  The nominal
groove data are the H5M values from Table 14.  ISO notes that the tabulated
profiles approximate the true generated profile over a tooth-count range;
these coupons therefore remain CALIBRATION_PENDING until checked with the
actual belt.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, pi, sin, sqrt

import cadquery as cq

from parameters import HTD_PITCH_MM, PITCH_LINE_DIFFERENTIAL_MM


@dataclass(frozen=True)
class H5MGrooveProfile:
    tooth_count_min: int
    tooth_count_max: int
    groove_depth_mm: float
    center_offset_mm: float
    main_radius_mm: float
    flank_angle_deg: float
    tip_radius_mm: float

    @property
    def main_center_depth_mm(self) -> float:
        """Radial depth of each paired main-arc center below the OD tangent."""

        return self.groove_depth_mm - sqrt(
            self.main_radius_mm**2 - self.center_offset_mm**2
        )


ISO_H5M_PROFILES: tuple[H5MGrooveProfile, ...] = (
    H5MGrooveProfile(
        tooth_count_min=17,
        tooth_count_max=25,
        groove_depth_mm=2.009,
        center_offset_mm=0.320,
        main_radius_mm=1.270,
        flank_angle_deg=6.0,
        tip_radius_mm=0.508,
    ),
    H5MGrooveProfile(
        tooth_count_min=26,
        tooth_count_max=80,
        groove_depth_mm=2.052,
        center_offset_mm=0.081,
        main_radius_mm=1.438,
        flank_angle_deg=2.0,
        tip_radius_mm=0.488,
    ),
)


def profile_for_tooth_count(tooth_count: int) -> H5MGrooveProfile:
    for profile in ISO_H5M_PROFILES:
        if profile.tooth_count_min <= tooth_count <= profile.tooth_count_max:
            return profile
    raise ValueError(f"No ISO H5M profile band configured for {tooth_count} teeth")


def pitch_diameter_mm(tooth_count: int) -> float:
    return tooth_count * HTD_PITCH_MM / pi


def outside_diameter_mm(tooth_count: int) -> float:
    return pitch_diameter_mm(tooth_count) - 2.0 * PITCH_LINE_DIFFERENTIAL_MM


def pitch_angle_deg(tooth_count: int) -> float:
    return 360.0 / tooth_count


def station_angles_deg(tooth_count: int, station_count: int = 6) -> tuple[float, ...]:
    if station_count % 2:
        raise ValueError("This coupon construction expects an even station count")
    half_step = (station_count - 1) / 2.0
    angle = pitch_angle_deg(tooth_count)
    return tuple((index - half_step) * angle for index in range(station_count))


def coupon_span_angle_deg(tooth_count: int, station_count: int = 6) -> float:
    return station_count * pitch_angle_deg(tooth_count)


def _short_arc_midpoint(
    center: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    """Return a point halfway along the shorter circular arc."""

    cx, cy = center
    radius = sqrt((start[0] - cx) ** 2 + (start[1] - cy) ** 2)
    start_angle = atan2(start[1] - cy, start[0] - cx)
    end_angle = atan2(end[1] - cy, end[0] - cx)
    delta = (end_angle - start_angle + pi) % (2.0 * pi) - pi
    mid_angle = start_angle + 0.5 * delta
    return (cx + radius * cos(mid_angle), cy + radius * sin(mid_angle))


def groove_profile_points(
    tooth_count: int, clearance_mm: float
) -> dict[str, tuple[float, float] | float]:
    """Return the paired-arc groove cutter geometry in an OD-tangent frame.

    ``x=0`` is the nominal outside-diameter tangent; negative x points into the
    pulley.  Clearance is applied as a normal offset by increasing the main
    contact-arc and transition-fillet radii while retaining groove station and
    pitch geometry.
    """

    nominal = profile_for_tooth_count(tooth_count)
    main_radius = nominal.main_radius_mm + clearance_mm
    tip_radius = nominal.tip_radius_mm + clearance_mm
    center_depth = nominal.main_center_depth_mm
    center_offset = nominal.center_offset_mm

    bottom_x = -center_depth - sqrt(main_radius**2 - center_offset**2)
    bottom = (bottom_x, 0.0)

    main_center_right = (-center_depth, -center_offset)
    fillet_center_x = -tip_radius
    center_delta_x = fillet_center_x - main_center_right[0]
    center_distance = main_radius + tip_radius
    fillet_center_y = (
        -center_offset + sqrt(center_distance**2 - center_delta_x**2)
    )
    fillet_center_right = (fillet_center_x, fillet_center_y)

    vector_x = fillet_center_right[0] - main_center_right[0]
    vector_y = fillet_center_right[1] - main_center_right[1]
    tangent_scale = main_radius / center_distance
    main_tangent_right = (
        main_center_right[0] + tangent_scale * vector_x,
        main_center_right[1] + tangent_scale * vector_y,
    )
    od_tangent_right = (0.0, fillet_center_y)

    def mirror(point: tuple[float, float]) -> tuple[float, float]:
        return (point[0], -point[1])

    main_center_left = mirror(main_center_right)
    fillet_center_left = mirror(fillet_center_right)
    main_tangent_left = mirror(main_tangent_right)
    od_tangent_left = mirror(od_tangent_right)

    return {
        "bottom": bottom,
        "main_center_left": main_center_left,
        "main_center_right": main_center_right,
        "fillet_center_left": fillet_center_left,
        "fillet_center_right": fillet_center_right,
        "main_tangent_left": main_tangent_left,
        "main_tangent_right": main_tangent_right,
        "od_tangent_left": od_tangent_left,
        "od_tangent_right": od_tangent_right,
        "main_radius_mm": main_radius,
        "tip_radius_mm": tip_radius,
        "bottom_depth_mm": -bottom_x,
    }


def make_groove_cutter(
    tooth_count: int,
    clearance_mm: float,
    face_width_mm: float,
    station_angle_deg: float,
) -> cq.Workplane:
    """Make one exact paired-circular-arc groove cutter."""

    points = groove_profile_points(tooth_count, clearance_mm)
    bottom = points["bottom"]
    left_tangent = points["main_tangent_left"]
    right_tangent = points["main_tangent_right"]
    od_left = points["od_tangent_left"]
    od_right = points["od_tangent_right"]

    left_fillet_mid = _short_arc_midpoint(
        points["fillet_center_left"], od_left, left_tangent
    )
    left_main_mid = _short_arc_midpoint(
        points["main_center_left"], left_tangent, bottom
    )
    right_main_mid = _short_arc_midpoint(
        points["main_center_right"], bottom, right_tangent
    )
    right_fillet_mid = _short_arc_midpoint(
        points["fillet_center_right"], right_tangent, od_right
    )

    outside_overcut = 2.0
    wire = (
        cq.Workplane("XY")
        .moveTo(outside_overcut, od_left[1])
        .lineTo(*od_left)
        .threePointArc(left_fillet_mid, left_tangent)
        .threePointArc(left_main_mid, bottom)
        .threePointArc(right_main_mid, right_tangent)
        .threePointArc(right_fillet_mid, od_right)
        .lineTo(outside_overcut, od_right[1])
        .close()
    )
    cutter = wire.extrude(face_width_mm)
    outside_radius = outside_diameter_mm(tooth_count) / 2.0
    return cutter.translate((outside_radius, 0.0, 0.0)).rotate(
        (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), station_angle_deg
    )


def describe_profile(tooth_count: int) -> dict[str, float | int]:
    profile = profile_for_tooth_count(tooth_count)
    return {
        "tooth_count": tooth_count,
        "pitch_mm": HTD_PITCH_MM,
        "pitch_diameter_mm": pitch_diameter_mm(tooth_count),
        "outside_diameter_mm": outside_diameter_mm(tooth_count),
        "pitch_angle_deg": pitch_angle_deg(tooth_count),
        "groove_depth_mm": profile.groove_depth_mm,
        "center_offset_mm": profile.center_offset_mm,
        "main_radius_mm": profile.main_radius_mm,
        "flank_angle_deg": profile.flank_angle_deg,
        "tip_radius_mm": profile.tip_radius_mm,
        "coupon_span_angle_deg": coupon_span_angle_deg(tooth_count),
        "arc_pitch_check_mm": (
            pitch_diameter_mm(tooth_count)
            * pi
            * pitch_angle_deg(tooth_count)
            / 360.0
        ),
    }
