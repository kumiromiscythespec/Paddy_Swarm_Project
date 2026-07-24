from __future__ import annotations
import hashlib
import importlib
import json
import math

def require_cadquery():
    spec = importlib.util.find_spec("cadquery")
    if spec is None:
        raise RuntimeError("CadQuery is required for solid execution; installation is intentionally not attempted")
    return importlib.import_module("cadquery")

def normalize_axis(direction):
    if isinstance(direction, str):
        token = direction.upper().strip()
        sign = -1.0 if token.endswith("-") else 1.0
        token = token[0]
        mapping = {"X": (sign, 0.0, 0.0), "Y": (0.0, sign, 0.0), "Z": (0.0, 0.0, sign)}
        if token not in mapping:
            raise ValueError(f"unsupported axis {direction}")
        return mapping[token]
    values = tuple(float(value) for value in direction)
    length = math.sqrt(sum(value * value for value in values))
    if length <= 0.0:
        raise ValueError("zero-length axis")
    return tuple(value / length for value in values)

def box_from_bounds(bounds):
    cq = require_cadquery()
    xmin, xmax, ymin, ymax, zmin, zmax = (float(value) for value in bounds)
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
    if min(dimensions) <= 0.0:
        raise ValueError(f"non-positive bounds: {bounds}")
    center = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0)
    return cq.Workplane("XY").box(*dimensions, centered=(True, True, True)).translate(center)

def box_from_center(center, dimensions):
    cx, cy, cz = (float(value) for value in center)
    dx, dy, dz = (float(value) for value in dimensions)
    return box_from_bounds((cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2, cz - dz / 2, cz + dz / 2))

def union_all(shapes):
    sequence = [shape for shape in shapes if shape is not None]
    if not sequence:
        raise ValueError("cannot union an empty shape sequence")
    result = sequence[0]
    for shape in sequence[1:]:
        result = result.union(shape)
    return result.clean()

def boxes_to_solid(boxes):
    return union_all([box_from_bounds(bounds) for bounds in boxes])

def cylinder_along_axis(center, direction, diameter, length):
    cq = require_cadquery()
    axis = normalize_axis(direction)
    if diameter <= 0.0 or length <= 0.0:
        raise ValueError("cylinder dimensions must be positive")
    shape = cq.Workplane("XY").circle(float(diameter) / 2.0).extrude(float(length), both=True)
    target = cq.Vector(*axis)
    z_axis = cq.Vector(0, 0, 1)
    cross = z_axis.cross(target)
    angle = math.degrees(z_axis.getAngle(target))
    if cross.Length > 1e-9:
        shape = shape.rotate((0, 0, 0), cross.toTuple(), angle)
    elif axis[2] < 0:
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 180)
    return shape.translate(tuple(float(value) for value in center))

def safe_boolean(left, right, operation, context):
    try:
        if operation == "cut":
            result = left.cut(right)
        elif operation == "union":
            result = left.union(right)
        elif operation == "intersect":
            result = left.intersect(right)
        else:
            raise ValueError(f"unsupported boolean operation {operation}")
        return result.clean()
    except Exception as exc:
        raise RuntimeError(f"BOOLEAN_OPERATION_ERROR:{context}:{operation}:{exc}") from exc

def shape_value(shape):
    value = shape.val() if hasattr(shape, "val") else shape
    return value

def shape_volume(shape):
    value = shape_value(shape)
    return float(value.Volume())

def shape_bbox(shape):
    box = shape_value(shape).BoundingBox()
    return {
        "xmin": float(box.xmin), "xmax": float(box.xmax),
        "ymin": float(box.ymin), "ymax": float(box.ymax),
        "zmin": float(box.zmin), "zmax": float(box.zmax),
        "xlen": float(box.xlen), "ylen": float(box.ylen), "zlen": float(box.zlen),
    }

def is_valid_solid(shape):
    value = shape_value(shape)
    volume = shape_volume(shape)
    valid = bool(value.isValid()) if hasattr(value, "isValid") else volume > 0.0
    return valid and volume > 0.0 and min(shape_bbox(shape)[axis] for axis in ("xlen", "ylen", "zlen")) > 0.0

def geometry_fingerprint(shape):
    value = shape_value(shape)
    bbox = shape_bbox(shape)
    center = value.Center()
    record = {
        "volume_mm3": round(shape_volume(shape), 6),
        "bbox": {key: round(value, 6) for key, value in bbox.items()},
        "center_of_mass_candidate": [round(float(center.x), 6), round(float(center.y), 6), round(float(center.z), 6)],
        "face_count": len(value.Faces()),
        "edge_count": len(value.Edges()),
        "vertex_count": len(value.Vertices()),
    }
    record["normalized_sha256"] = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return record

def intersect_volume(left, right, tolerance=0.001):
    common = safe_boolean(left, right, "intersect", "collision")
    volume = shape_volume(common)
    return volume, volume > float(tolerance)
