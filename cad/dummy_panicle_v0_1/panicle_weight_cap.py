"""DR-H03 PETG removable cap for the DR-H02 weight pocket."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from .cq_utils import (
    export_step as export_shape_step,
    export_stl as export_shape_stl,
    require_minimum,
    require_positive,
    validate_printable_shape,
)
from .interfaces import PANICLE_HEAD


@dataclass(frozen=True)
class PanicleWeightCapParams:
    """DR-H03 dimensions in mm.

    The 0.2 mm diametral retention-bead interference is a calibration
    candidate only.  It does not establish retention until a printed cap and
    hub have been measured and pull-tested.
    """

    pocket_diameter: float = 8.0
    plug_diameter: float = 7.8
    retention_bead_diameter: float = 8.2
    insertion_depth: float = 4.5
    bead_height: float = 0.8
    flange_diameter: float = 12.2
    flange_thickness: float = 1.5
    pry_notch_width: float = 2.0
    pry_notch_depth: float = 1.0
    min_wall: float = 1.5
    calibration_status: str = PANICLE_HEAD.calibration_status


def retention_interference(params: PanicleWeightCapParams) -> float:
    """Return nominal diametral bead interference with the hub pocket."""

    return params.retention_bead_diameter - params.pocket_diameter


def validate_params(params: PanicleWeightCapParams) -> None:
    """Validate cap fit candidates and conservative printable dimensions."""

    require_positive(
        pocket_diameter=params.pocket_diameter,
        plug_diameter=params.plug_diameter,
        retention_bead_diameter=params.retention_bead_diameter,
        insertion_depth=params.insertion_depth,
        bead_height=params.bead_height,
        flange_diameter=params.flange_diameter,
        flange_thickness=params.flange_thickness,
        pry_notch_width=params.pry_notch_width,
        pry_notch_depth=params.pry_notch_depth,
        min_wall=params.min_wall,
    )
    if params.calibration_status != "CALIBRATION_PENDING":
        raise ValueError("DR-H03 must remain CALIBRATION_PENDING before print testing")
    if params.plug_diameter >= params.pocket_diameter:
        raise ValueError("DR-H03 plug body requires diametral clearance")
    if retention_interference(params) <= 0.0:
        raise ValueError("DR-H03 retention bead requires positive candidate interference")
    if retention_interference(params) > 0.4:
        raise ValueError("DR-H03 candidate bead interference exceeds 0.4 mm")
    if params.bead_height >= params.insertion_depth:
        raise ValueError("DR-H03 bead height must be shorter than insertion depth")
    require_minimum(params.min_wall, 1.5, "DR-H03 minimum wall")
    radial_flange = 0.5 * (
        params.flange_diameter - params.retention_bead_diameter
    )
    require_minimum(radial_flange, params.min_wall, "DR-H03 flange radial margin")
    if params.pry_notch_depth >= radial_flange:
        raise ValueError("DR-H03 pry notch reaches the retention bead")
    require_minimum(
        params.flange_thickness,
        params.min_wall,
        "DR-H03 flange thickness",
    )


def build(
    params: PanicleWeightCapParams = PanicleWeightCapParams(),
) -> cq.Workplane:
    """Build the support-free DR-H03 pocket cap in print orientation."""

    validate_params(params)
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * params.flange_diameter)
        .extrude(params.flange_thickness)
    )
    plug_height = params.insertion_depth - params.bead_height
    plug = (
        cq.Workplane("XY")
        .circle(0.5 * params.plug_diameter)
        .extrude(plug_height)
        .translate((0.0, 0.0, params.flange_thickness))
    )
    bead = cq.Workplane("XY").workplane(
        offset=params.flange_thickness + plug_height
    ).circle(0.5 * params.plug_diameter).workplane(
        offset=0.5 * params.bead_height
    ).circle(
        0.5 * params.retention_bead_diameter
    ).workplane(
        offset=0.5 * params.bead_height
    ).circle(
        0.5 * params.plug_diameter
    ).loft(
        combine=True
    )
    cap = flange.union(plug).union(bead)

    notch = (
        cq.Workplane("XY")
        .box(
            params.pry_notch_depth + 0.2,
            params.pry_notch_width,
            params.flange_thickness + 0.2,
            centered=(False, True, False),
        )
        .translate(
            (
                0.5 * params.flange_diameter - params.pry_notch_depth,
                0.0,
                -0.1,
            )
        )
    )
    cap = cap.cut(notch)
    validate_printable_shape(cap, "DR-H03 panicle weight cap PETG")
    return cap


def export_step(params: PanicleWeightCapParams, output_path: str | Path) -> Path:
    """Build and export DR-H03 as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: PanicleWeightCapParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export DR-H03 as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
