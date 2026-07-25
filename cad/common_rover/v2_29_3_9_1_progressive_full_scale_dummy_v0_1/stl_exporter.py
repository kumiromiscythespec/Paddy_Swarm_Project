from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from pathlib import Path
import struct
from typing import Iterable

from part_number_registry import PrintedPart


def cq_module():
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("CADQUERY_ENVIRONMENT_REQUIRED") from exc
    return cq


def box(
    dx: float,
    dy: float,
    dz: float,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
):
    cq = cq_module()
    return (
        cq.Workplane("XY")
        .box(dx, dy, dz, centered=(False, False, False))
        .translate((x, y, z))
        .val()
    )


def cylinder_x(
    diameter: float,
    length: float,
    x: float,
    y: float,
    z: float,
):
    cq = cq_module()
    return cq.Solid.makeCylinder(
        diameter / 2.0,
        length,
        cq.Vector(x, y, z),
        cq.Vector(1.0, 0.0, 0.0),
    )


def cylinder_z(
    diameter: float,
    length: float,
    x: float,
    y: float,
    z: float,
):
    cq = cq_module()
    return cq.Solid.makeCylinder(
        diameter / 2.0,
        length,
        cq.Vector(x, y, z),
        cq.Vector(0.0, 0.0, 1.0),
    )


def fuse_all(shapes: Iterable):
    items = list(shapes)
    if not items:
        raise ValueError("NO_SHAPES_TO_FUSE")
    result = items[0]
    for shape in items[1:]:
        result = result.fuse(shape)
    return result


def hollow_cage(
    dimensions_xyz: tuple[float, float, float],
    *,
    beam: float = 4.0,
    open_bottom: bool = True,
):
    """Create a connected edge cage preserving the exact outer envelope."""

    xlen, ylen, zlen = dimensions_xyz
    shapes = []
    for x in (0.0, xlen - beam):
        for y in (0.0, ylen - beam):
            shapes.append(box(beam, beam, zlen, x, y, 0.0))
    for z in ((zlen - beam,) if open_bottom else (0.0, zlen - beam)):
        shapes.extend(
            (
                box(xlen, beam, beam, 0.0, 0.0, z),
                box(xlen, beam, beam, 0.0, ylen - beam, z),
                box(beam, ylen, beam, 0.0, 0.0, z),
                box(beam, ylen, beam, xlen - beam, 0.0, z),
            )
        )
    if open_bottom:
        # Small low braces connect the posts while leaving the bottom open.
        shapes.extend(
            (
                box(xlen, beam, beam, 0.0, 0.0, 0.0),
                box(xlen, beam, beam, 0.0, ylen - beam, 0.0),
            )
        )
    return fuse_all(shapes)


@dataclass(frozen=True)
class MarkingEvidence:
    part_number: str
    geometry_part_number: str
    required_lines: tuple[str, ...]
    marking_surface: str
    physical_marking: str
    marking_verified: bool
    glyph_solid_count: int
    intersecting_glyph_solid_count: int
    floating_text_solid_count: int
    engraved_volume_mm3: float


@dataclass(frozen=True)
class BuiltGeometry:
    shape: object
    marking: MarkingEvidence
    design_metadata: dict

    def BoundingBox(self):
        return self.shape.BoundingBox()


def validate_marking_evidence(evidence: MarkingEvidence) -> None:
    if not evidence.part_number.strip():
        raise ValueError("MISSING_PHYSICAL_PART_NUMBER")
    if evidence.part_number != evidence.geometry_part_number:
        raise ValueError("PART_NUMBER_GEOMETRY_MISMATCH")
    if evidence.physical_marking not in {"ENGRAVED", "EMBOSSED"}:
        raise ValueError("MARKING_ONLY_IN_METADATA")
    if (
        not evidence.marking_verified
        or evidence.floating_text_solid_count != 0
        or evidence.glyph_solid_count
        != evidence.intersecting_glyph_solid_count
    ):
        raise ValueError("FLOATING_ENGRAVED_OR_EMBOSSED_TEXT")


def add_recessed_top_id_panel(
    shape,
    *,
    x: float,
    y: float,
    z: float,
    width: float,
    depth: float,
    thickness: float = 2.0,
):
    """Fuse an ID panel below the outer datum so it is not a measurement face."""

    return shape.fuse(box(width, depth, thickness, x, y, z))


def _text_solids(
    text: str,
    x: float,
    y: float,
    surface_z: float,
    *,
    size: float,
    depth: float,
    rotation_degrees: float = 0.0,
):
    cq = cq_module()
    overlap = 0.05
    solids = (
        cq.Workplane("XY")
        .workplane(offset=surface_z - depth)
        .center(x, y)
        .text(
            text,
            size,
            depth + overlap,
            combine=False,
            halign="center",
            valign="center",
        )
        .vals()
    )
    if rotation_degrees:
        origin = cq.Vector(x, y, surface_z)
        axis = cq.Vector(x, y, surface_z + 1.0)
        solids = [
            glyph.rotate(origin, axis, rotation_degrees)
            for glyph in solids
        ]
    return solids


def engrave_top_markings(
    shape,
    part: PrintedPart,
    *,
    center_x: float,
    first_y: float,
    surface_z: float,
    line_spacing: float,
    sizes: tuple[float, float, float, float] = (3.0, 3.0, 3.0, 2.6),
    depth: float = 0.55,
    metadata: dict | None = None,
) -> BuiltGeometry:
    before = float(shape.Volume())
    target = shape
    glyph_count = 0
    intersecting = 0
    for index, (line, size) in enumerate(
        zip(part.required_marking_lines, sizes)
    ):
        solids = _text_solids(
            line,
            center_x,
            first_y + index * line_spacing,
            surface_z,
            size=size,
            depth=depth,
        )
        if not solids:
            raise RuntimeError(f"MARKING_TEXT_SOLID_MISSING:{part.key}:{line}")
        for glyph in solids:
            glyph_count += 1
            if float(target.intersect(glyph).Volume()) > 1.0e-7:
                intersecting += 1
        target = target.cut(*solids)
    engraved = before - float(target.Volume())
    verified = (
        glyph_count > 0
        and intersecting == glyph_count
        and engraved > 1.0e-5
    )
    if not verified:
        raise RuntimeError(f"FLOATING_OR_MISSING_MARKING:{part.key}")
    geometry = BuiltGeometry(
        target,
        MarkingEvidence(
            part_number=part.part_number,
            geometry_part_number=part.part_number,
            required_lines=part.required_marking_lines,
            marking_surface=part.marking_surface,
            physical_marking="ENGRAVED",
            marking_verified=True,
            glyph_solid_count=glyph_count,
            intersecting_glyph_solid_count=intersecting,
            floating_text_solid_count=0,
            engraved_volume_mm3=round(engraved, 6),
        ),
        metadata or {},
    )
    validate_marking_evidence(geometry.marking)
    return geometry


def engrave_rail_markings(
    shape,
    part: PrintedPart,
    *,
    x_positions: tuple[float, float, float, float],
    center_y: float,
    surface_z: float,
    sizes: tuple[float, float, float, float] = (2.4, 2.4, 2.4, 2.0),
    depth: float = 0.50,
    metadata: dict | None = None,
) -> BuiltGeometry:
    """Engrave four strings along the long Y axis of a 20 mm rail."""

    before = float(shape.Volume())
    target = shape
    glyph_count = 0
    intersecting = 0
    for line, x, size in zip(
        part.required_marking_lines, x_positions, sizes
    ):
        solids = _text_solids(
            line,
            x,
            center_y,
            surface_z,
            size=size,
            depth=depth,
            rotation_degrees=90.0,
        )
        if not solids:
            raise RuntimeError(f"MARKING_TEXT_SOLID_MISSING:{part.key}:{line}")
        for glyph in solids:
            glyph_count += 1
            if float(target.intersect(glyph).Volume()) > 1.0e-7:
                intersecting += 1
        target = target.cut(*solids)
    engraved = before - float(target.Volume())
    verified = (
        glyph_count > 0
        and intersecting == glyph_count
        and engraved > 1.0e-5
    )
    if not verified:
        raise RuntimeError(f"FLOATING_OR_MISSING_MARKING:{part.key}")
    geometry = BuiltGeometry(
        target,
        MarkingEvidence(
            part_number=part.part_number,
            geometry_part_number=part.part_number,
            required_lines=part.required_marking_lines,
            marking_surface=part.marking_surface,
            physical_marking="ENGRAVED",
            marking_verified=True,
            glyph_solid_count=glyph_count,
            intersecting_glyph_solid_count=intersecting,
            floating_text_solid_count=0,
            engraved_volume_mm3=round(engraved, 6),
        ),
        metadata or {},
    )
    validate_marking_evidence(geometry.marking)
    return geometry


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def export_stl(
    geometry: BuiltGeometry,
    path: Path,
    *,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> dict:
    cq = cq_module()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not geometry.shape.isValid():
        raise RuntimeError(f"INVALID_CAD_SHAPE:{path.name}")
    cq.exporters.export(
        geometry.shape,
        str(path),
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )
    mesh = audit_stl(path)
    box_ = geometry.shape.BoundingBox()
    return {
        "filename": path.name,
        "stl_sha256": sha256_file(path),
        "stl_size_bytes": path.stat().st_size,
        "cad_shape_valid": True,
        "cad_solid_count": len(geometry.shape.Solids()),
        "bounding_box_mm": {
            "x": round(float(box_.xlen), 6),
            "y": round(float(box_.ylen), 6),
            "z": round(float(box_.zlen), 6),
        },
        "marking": asdict(geometry.marking),
        "design_metadata": geometry.design_metadata,
        "mesh_audit": mesh,
    }


def _binary_stl_vertices(data: bytes) -> list[tuple[float, float, float]]:
    count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + count * 50
    if len(data) != expected:
        raise ValueError("INVALID_BINARY_STL_SIZE")
    vertices = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        vertices.extend(
            (
                (values[3], values[4], values[5]),
                (values[6], values[7], values[8]),
                (values[9], values[10], values[11]),
            )
        )
        offset += 50
    return vertices


def _ascii_stl_vertices(data: bytes) -> list[tuple[float, float, float]]:
    vertices = []
    for raw in data.decode("ascii", errors="strict").splitlines():
        line = raw.strip()
        if line.startswith("vertex "):
            fields = line.split()
            vertices.append(tuple(float(value) for value in fields[1:4]))
    if len(vertices) % 3:
        raise ValueError("INVALID_ASCII_STL_VERTEX_COUNT")
    return vertices


def audit_stl(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 84:
        vertices = _ascii_stl_vertices(data)
        encoding = "ASCII"
    else:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            vertices = _binary_stl_vertices(data)
            encoding = "BINARY"
        else:
            vertices = _ascii_stl_vertices(data)
            encoding = "ASCII"
    if not vertices:
        raise ValueError("EMPTY_STL")
    finite = all(math.isfinite(value) for vertex in vertices for value in vertex)
    if not finite:
        raise ValueError("NONFINITE_STL_VERTEX")
    zero_area = 0
    for index in range(0, len(vertices), 3):
        a, b, c = vertices[index : index + 3]
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        if sum(value * value for value in cross) <= 1.0e-18:
            zero_area += 1
    mins = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maxs = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    return {
        "status": "PASS" if zero_area == 0 else "FAIL",
        "encoding": encoding,
        "triangle_count": len(vertices) // 3,
        "finite_vertices": finite,
        "zero_area_triangle_count": zero_area,
        "bounds_mm": {
            "minimum": [round(value, 6) for value in mins],
            "maximum": [round(value, 6) for value in maxs],
        },
    }
