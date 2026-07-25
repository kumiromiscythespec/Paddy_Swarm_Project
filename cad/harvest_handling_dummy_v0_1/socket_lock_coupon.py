"""BASE-SOCKET-IF-V001 three-candidate retention coupon."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive, validate_base_socket_interface
from .parameters import BASE_SOCKET, GAUGE


@dataclass(frozen=True)
class SocketLockCouponParams:
    """Three receiver stations for 0.15/0.25/0.35 mm bead interference."""

    plate_width: float = 95.0
    plate_length: float = 42.0
    plate_thickness: float = 4.0
    boss_diameter: float = 23.0
    boss_height: float = 14.0
    station_pitch: float = 30.0
    label_relief: float = GAUGE.label_height


def candidate_receiver_diameters() -> tuple[float, ...]:
    """Return bores paired with one 13.45 mm standard bead."""

    standard_bead = BASE_SOCKET.receiver_diameter + BASE_SOCKET.snap_interference
    return tuple(
        standard_bead - candidate
        for candidate in BASE_SOCKET.snap_candidate_values
    )


def validate_params(params: SocketLockCouponParams) -> None:
    """Validate coupon dimensions and candidate order."""

    validate_base_socket_interface()
    require_positive(
        plate_width=params.plate_width,
        plate_length=params.plate_length,
        plate_thickness=params.plate_thickness,
        boss_diameter=params.boss_diameter,
        boss_height=params.boss_height,
        station_pitch=params.station_pitch,
        label_relief=params.label_relief,
    )
    if params.boss_height < BASE_SOCKET.insertion_depth:
        raise ValueError("socket coupon boss is shorter than insertion depth")
    if params.boss_diameter - max(candidate_receiver_diameters()) < 4.0:
        raise ValueError("socket coupon boss wall is below 2 mm radial")


def _octagon_corner_diameter(across_flats: float) -> float:
    """Convert regular-octagon across-flats to corner diameter."""

    return across_flats / math.cos(math.pi / 8.0)


def build(
    params: SocketLockCouponParams = SocketLockCouponParams(),
) -> cq.Workplane:
    """Build one flat, labeled, single-solid calibration coupon."""

    validate_params(params)
    part = cq.Workplane("XY").box(
        params.plate_width,
        params.plate_length,
        params.plate_thickness,
        centered=(True, True, False),
    )
    station_x = (-params.station_pitch, 0.0, params.station_pitch)
    station_y = 5.0
    total_height = params.plate_thickness + params.boss_height
    for x, receiver_diameter in zip(
        station_x,
        candidate_receiver_diameters(),
    ):
        boss = (
            cq.Workplane("XY")
            .center(x, station_y)
            .circle(0.5 * params.boss_diameter)
            .extrude(params.boss_height)
            .translate((0.0, 0.0, params.plate_thickness))
        )
        part = part.union(boss)
        bore = (
            cq.Workplane("XY")
            .center(x, station_y)
            .circle(0.5 * receiver_diameter)
            .extrude(BASE_SOCKET.insertion_depth + 0.05)
            .translate(
                (
                    0.0,
                    0.0,
                    total_height - BASE_SOCKET.insertion_depth,
                )
            )
        )
        index = (
            cq.Workplane("XY")
            .center(x, station_y)
            .polygon(
                8,
                _octagon_corner_diameter(BASE_SOCKET.receiver_index_af),
            )
            .extrude(BASE_SOCKET.index_depth + 0.05)
            .translate(
                (
                    0.0,
                    0.0,
                    total_height - BASE_SOCKET.index_depth,
                )
            )
        )
        push_out = (
            cq.Workplane("XY")
            .center(x, station_y)
            .circle(2.0)
            .extrude(total_height)
        )
        part = part.cut(bore).cut(index).cut(push_out)

    for x, label in zip(station_x, ("15", "25", "35")):
        text = (
            cq.Workplane("XY")
            .workplane(offset=params.plate_thickness)
            .center(x, -14.0)
            .text(
                label,
                GAUGE.label_font_size,
                params.label_relief,
                combine=True,
                halign="center",
                valign="center",
            )
        )
        part = part.union(text)

    validate_print_bounds(part, "HU-H0-HHD-CPN-SOCKET-LOCK")
    return part
