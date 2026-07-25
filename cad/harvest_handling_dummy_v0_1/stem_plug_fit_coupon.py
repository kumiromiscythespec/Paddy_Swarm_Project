"""HHD-STEM-PLUG-V001 five-hole fit coupon."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive, validate_stem_plug_interface
from .parameters import GAUGE


HOLE_DIAMETERS: tuple[float, ...] = (6.10, 6.20, 6.25, 6.30, 6.40)


@dataclass(frozen=True)
class StemPlugFitCouponParams:
    """Compact five-hole common-shank calibration plate."""

    width: float = 120.0
    length: float = 34.0
    thickness: float = 8.0
    hole_pitch: float = 22.0
    label_relief: float = GAUGE.label_height


def validate_params(params: StemPlugFitCouponParams) -> None:
    """Validate coupon wall and label parameters."""

    validate_stem_plug_interface()
    require_positive(
        width=params.width,
        length=params.length,
        thickness=params.thickness,
        hole_pitch=params.hole_pitch,
        label_relief=params.label_relief,
    )
    if params.hole_pitch - max(HOLE_DIAMETERS) < 4.0:
        raise ValueError("stem plug coupon leaves less than 2 mm between bores")


def build(
    params: StemPlugFitCouponParams = StemPlugFitCouponParams(),
) -> cq.Workplane:
    """Build the labeled five-hole PETG comparison coupon."""

    validate_params(params)
    part = cq.Workplane("XY").box(
        params.width,
        params.length,
        params.thickness,
        centered=(True, True, False),
    )
    station_x = tuple(
        (index - 2) * params.hole_pitch
        for index in range(len(HOLE_DIAMETERS))
    )
    for x, diameter in zip(station_x, HOLE_DIAMETERS):
        bore = (
            cq.Workplane("XY")
            .center(x, 4.0)
            .circle(0.5 * diameter)
            .extrude(params.thickness)
        )
        part = part.cut(bore)
    for x, label in zip(station_x, ("610", "620", "625", "630", "640")):
        text = (
            cq.Workplane("XY")
            .workplane(offset=params.thickness)
            .center(x, -11.0)
            .text(
                label,
                4.5,
                params.label_relief,
                combine=True,
                halign="center",
                valign="center",
            )
        )
        part = part.union(text)
    validate_print_bounds(part, "HU-H0-HHD-CPN-STEM-PLUG-FIT")
    return part
