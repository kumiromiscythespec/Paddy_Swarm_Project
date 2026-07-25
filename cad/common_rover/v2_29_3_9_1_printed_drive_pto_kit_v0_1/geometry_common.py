from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from part_number_registry import PartSpec


MARKING_HANDLER = "COMMON_ENGRAVED_PART_NUMBER_V1_GENERALIZED"
MARKING_PROVENANCE = (
    "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/"
    "coupon_geometry.py::COMMON_ENGRAVED_PART_NUMBER_V1"
)


def require_cadquery():
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("CADQUERY_2_8_ENVIRONMENT_REQUIRED") from exc
    return cq


@dataclass(frozen=True)
class MarkingEvidence:
    part_number: str
    geometry_part_number: str
    physical_marking: str
    handler: str
    provenance: str
    lines: tuple[str, ...]
    marking_verified: bool
    glyph_solid_count: int
    intersecting_glyph_solid_count: int
    floating_part_number_solid_count: int
    engraved_volume_mm3: float
    minimum_text_size_mm: float
    depth_mm: float


@dataclass(frozen=True)
class BuiltPart:
    spec: PartSpec
    shape: object
    marking: MarkingEvidence
    metadata: dict[str, Any]

    def record(self) -> dict[str, Any]:
        box = self.shape.BoundingBox()
        return {
            "key": self.spec.key,
            "part_number": self.spec.part_number,
            "title": self.spec.title,
            "family": self.spec.family,
            "filename": self.spec.filename,
            "material": self.spec.material,
            "classification": self.spec.classification,
            "print_target": self.spec.print_target,
            "volume_mm3": float(self.shape.Volume()),
            "solid_count": len(self.shape.Solids()),
            "valid": bool(self.shape.isValid()),
            "bounding_box_mm": {
                "x": float(box.xlen),
                "y": float(box.ylen),
                "z": float(box.zlen),
            },
            "marking": asdict(self.marking),
            "metadata": self.metadata,
        }


def box_xyz(
    x_length: float,
    y_length: float,
    z_length: float,
    *,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
):
    cq = require_cadquery()
    return (
        cq.Workplane("XY")
        .box(x_length, y_length, z_length, centered=(True, True, False))
        .translate((x, y, z))
        .val()
    )


def cylinder_z(
    radius: float,
    height: float,
    *,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
):
    cq = require_cadquery()
    return cq.Solid.makeCylinder(
        radius,
        height,
        cq.Vector(x, y, z),
        cq.Vector(0.0, 0.0, 1.0),
    )


def fuse_all(shapes: Iterable[object]):
    items = list(shapes)
    if not items:
        raise ValueError("NO_SHAPES_TO_FUSE")
    result = items[0]
    if len(items) > 1:
        result = result.fuse(*items[1:])
    return result


def _text_solids(
    text: str,
    center_x: float,
    center_y: float,
    surface_z: float,
    *,
    size_mm: float,
    depth_mm: float,
) -> list[object]:
    cq = require_cadquery()
    overlap_mm = 0.05
    return (
        cq.Workplane("XY")
        .workplane(offset=surface_z - depth_mm)
        .center(center_x, center_y)
        .text(
            text,
            size_mm,
            depth_mm + overlap_mm,
            combine=False,
            halign="center",
            valign="center",
        )
        .vals()
    )


def engrave_part_number(
    shape,
    spec: PartSpec,
    *,
    centers_xy: tuple[tuple[float, float], tuple[float, float]],
    surface_z: float,
    size_mm: float = 2.6,
    depth_mm: float = 0.55,
    metadata: dict[str, Any] | None = None,
) -> BuiltPart:
    """Engrave the full part number and prove every glyph intersects the body."""

    if size_mm < 2.0:
        raise ValueError("PART_NUMBER_TEXT_TOO_SMALL_FOR_0_4_NOZZLE")
    before = float(shape.Volume())
    target = shape
    glyph_count = 0
    intersecting_count = 0
    lines = spec.marking_lines
    for line, (center_x, center_y) in zip(lines, centers_xy):
        glyphs = _text_solids(
            line,
            center_x,
            center_y,
            surface_z,
            size_mm=size_mm,
            depth_mm=depth_mm,
        )
        if not glyphs:
            raise RuntimeError(f"MARKING_TEXT_SOLID_MISSING:{spec.part_number}")
        for glyph in glyphs:
            glyph_count += 1
            if float(shape.intersect(glyph).Volume()) > 1.0e-7:
                intersecting_count += 1
        target = target.cut(*glyphs)
    engraved = before - float(target.Volume())
    verified = (
        glyph_count > 0
        and intersecting_count == glyph_count
        and engraved > 1.0e-5
    )
    if not verified:
        raise RuntimeError(
            f"FLOATING_OR_UNREADABLE_PART_NUMBER:{spec.part_number}:"
            f"glyphs={glyph_count}:intersecting={intersecting_count}:"
            f"engraved={engraved}"
        )
    evidence = MarkingEvidence(
        part_number=spec.part_number,
        geometry_part_number=spec.part_number,
        physical_marking="ENGRAVED",
        handler=MARKING_HANDLER,
        provenance=MARKING_PROVENANCE,
        lines=lines,
        marking_verified=True,
        glyph_solid_count=glyph_count,
        intersecting_glyph_solid_count=intersecting_count,
        floating_part_number_solid_count=0,
        engraved_volume_mm3=round(engraved, 6),
        minimum_text_size_mm=size_mm,
        depth_mm=depth_mm,
    )
    return BuiltPart(spec, target, evidence, metadata or {})


def add_label_pad(
    shape,
    *,
    width_mm: float,
    depth_mm: float,
    bottom_z: float,
    thickness_mm: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
):
    pad = box_xyz(
        width_mm,
        depth_mm,
        thickness_mm,
        x=center_x,
        y=center_y,
        z=bottom_z,
    )
    return shape.fuse(pad)


def export_part(
    built: BuiltPart,
    stl_directory: Path,
    step_directory: Path,
) -> tuple[Path, Path]:
    cq = require_cadquery()
    stl_directory.mkdir(parents=True, exist_ok=True)
    step_directory.mkdir(parents=True, exist_ok=True)
    stl_path = stl_directory / built.spec.filename
    step_path = step_directory / built.spec.filename.replace(".stl", ".step")
    cq.exporters.export(
        built.shape,
        str(stl_path),
        tolerance=0.04,
        angularTolerance=0.08,
    )
    cq.exporters.export(built.shape, str(step_path))
    return stl_path, step_path
