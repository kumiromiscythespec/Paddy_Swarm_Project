"""Parametric stepped-candidate bore gauge bars."""

from __future__ import annotations

from string import ascii_uppercase

import cadquery as cq

from parameters import (
    BORE_GAUGES,
    FONT_PATH,
    GAUGE_ENGRAVING_DEPTH_MM,
    GAUGE_HOLE_ENTRY_CHAMFER_MM,
    GAUGE_OUTER_EDGE_CHAMFER_MM,
    BoreGaugeSpec,
)


def _text_cutter(
    text: str,
    size_mm: float,
    depth_mm: float,
    top_z_mm: float,
    x_mm: float,
    y_mm: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=top_z_mm - depth_mm)
        .text(
            text,
            fontsize=size_mm,
            distance=depth_mm + 0.10,
            combine=True,
            clean=True,
            fontPath=str(FONT_PATH),
        )
        .translate((x_mm, y_mm, 0.0))
    )


def build_bore_gauge(spec: BoreGaugeSpec) -> cq.Workplane:
    """Build one gauge with true circular bores and top-face engravings."""

    gauge = (
        cq.Workplane("XY")
        .box(spec.length_mm, spec.width_mm, spec.thickness_mm, centered=(True, True, False))
        .edges()
        .chamfer(GAUGE_OUTER_EDGE_CHAMFER_MM)
    )

    for center_x, diameter in zip(spec.hole_centers_x_mm, spec.candidates_mm):
        hole = (
            cq.Workplane("XY")
            .center(center_x, 0.0)
            .circle(diameter / 2.0)
            .extrude(spec.thickness_mm)
        )
        gauge = gauge.cut(hole)

    circular_edges = gauge.edges("%Circle")
    if circular_edges.size() != 2 * len(spec.candidates_mm):
        raise RuntimeError(
            f"{spec.key}: expected {2 * len(spec.candidates_mm)} circular bore edges "
            f"before entry chamfer, found {circular_edges.size()}"
        )
    gauge = circular_edges.chamfer(GAUGE_HOLE_ENTRY_CHAMFER_MM)

    for index, (center_x, diameter) in enumerate(
        zip(spec.hole_centers_x_mm, spec.candidates_mm)
    ):
        letter = ascii_uppercase[index]
        gauge = gauge.cut(
            _text_cutter(
                letter,
                spec.label_size_mm,
                GAUGE_ENGRAVING_DEPTH_MM,
                spec.thickness_mm,
                center_x,
                spec.label_offset_y_mm,
            )
        )
        gauge = gauge.cut(
            _text_cutter(
                f"{diameter:.2f}",
                spec.label_size_mm * 0.78,
                GAUGE_ENGRAVING_DEPTH_MM,
                spec.thickness_mm,
                center_x,
                -spec.label_offset_y_mm,
            )
        )

    return gauge.clean()


def build_all_bore_gauges() -> dict[str, cq.Workplane]:
    return {spec.key: build_bore_gauge(spec) for spec in BORE_GAUGES}


if __name__ == "__main__":
    for name, model in build_all_bore_gauges().items():
        print(name, model.val().BoundingBox())
