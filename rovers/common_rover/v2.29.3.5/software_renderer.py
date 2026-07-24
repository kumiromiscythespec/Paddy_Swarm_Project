from __future__ import annotations
import binascii
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path
from cad_primitives import geometry_fingerprint, shape_value

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CAMERA_AUTHORITY = {
    "front": {"eye_side": [0.0, -1.0, 0.0], "forward": [0.0, 1.0, 0.0], "up_hint": [0.0, 0.0, 1.0]},
    "rear": {"eye_side": [0.0, 1.0, 0.0], "forward": [0.0, -1.0, 0.0], "up_hint": [0.0, 0.0, 1.0]},
    "left": {"eye_side": [1.0, 0.0, 0.0], "forward": [-1.0, 0.0, 0.0], "up_hint": [0.0, 0.0, 1.0]},
    "right": {"eye_side": [-1.0, 0.0, 0.0], "forward": [1.0, 0.0, 0.0], "up_hint": [0.0, 0.0, 1.0]},
    "top": {"eye_side": [0.0, 0.0, 1.0], "forward": [0.0, 0.0, -1.0], "up_hint": [0.0, 1.0, 0.0]},
    "bottom": {"eye_side": [0.0, 0.0, -1.0], "forward": [0.0, 0.0, 1.0], "up_hint": [0.0, -1.0, 0.0]},
    "iso": {"eye_side": [1.0, -1.0, 1.0], "forward": [-1.0, 1.0, -1.0], "up_hint": [0.0, 0.0, 1.0]},
}
REQUIRED_VIEWS = tuple(CAMERA_AUTHORITY)
FONT = {
    "A":"011101000110001111111000110001","B":"111101000111110100011000111110",
    "C":"011111000010000100001000001111","D":"111101000110001100011000111110",
    "E":"111111000011110100001000011111","F":"111111000011110100001000010000",
    "G":"011111000010000101111000101111","H":"100011000111111100011000110001",
    "I":"111110010000100001000010011111","J":"001110001000010000101001001100",
    "K":"100011001011100100101000110001","L":"100001000010000100001000011111",
    "M":"100011101110101100011000110001","N":"100011100110101100111000110001",
    "O":"011101000110001100011000101110","P":"111101000110001111101000010000",
    "Q":"011101000110001101011001001101","R":"111101000110001111101001010001",
    "S":"011111000001110000011000111110","T":"111110010000100001000010000100",
    "U":"100011000110001100011000101110","V":"100011000110001100010101000100",
    "W":"100011000110001101011101110101","X":"100011000101010001000101010001",
    "Y":"100011000101010001000010000100","Z":"111110000100010001000100011111",
    "0":"011101000110011101011100101110","1":"001000110000100001000010001110",
    "2":"011101000100001001100100011111","3":"111100000100110000011000111110",
    "4":"000100011001010100101111100010","5":"111111000011110000011000111110",
    "6":"011101000010000111101000101110","7":"111110000100010001000100001000",
    "8":"011101000101110100011000101110","9":"011101000110001011110000101110",
    "-":"000000000000000111110000000000","_":"000000000000000000000000011111",
    ".":"000000000000000000000110001100",":":"000000110001100000001100011000",
    "/":"000010001000100010001000010000"," ":"000000000000000000000000000000",
}

def _dot(a, b):
    return sum(float(a[index]) * float(b[index]) for index in range(3))

def _sub(a, b):
    return tuple(float(a[index]) - float(b[index]) for index in range(3))

def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )

def _normalize(value):
    length = math.sqrt(_dot(value, value))
    if length <= 1e-12:
        raise ValueError("zero vector")
    return tuple(float(item) / length for item in value)

def camera_matrix(view_name):
    if view_name not in CAMERA_AUTHORITY:
        raise KeyError(view_name)
    authority = CAMERA_AUTHORITY[view_name]
    forward = _normalize(authority["forward"])
    right = _normalize(_cross(forward, authority["up_hint"]))
    up = _normalize(_cross(right, forward))
    return {
        "view": view_name, "right": list(right), "up": list(up),
        "forward": list(forward), "eye_side": authority["eye_side"],
        "matrix": [list(right), list(up), list(forward)],
    }

def _vertex_tuple(vertex):
    if hasattr(vertex, "toTuple"):
        values = vertex.toTuple()
    elif all(hasattr(vertex, name) for name in ("x", "y", "z")):
        values = (vertex.x, vertex.y, vertex.z)
    else:
        values = vertex
    return tuple(float(value) for value in values)

def tessellate_shape(actual_shape, tolerance=0.08, angular_tolerance=0.12):
    if actual_shape is None or isinstance(actual_shape, (dict, list, tuple)):
        raise TypeError("renderer requires an actual CadQuery/OCP shape, not bbox/specification data")
    value = shape_value(actual_shape)
    if not hasattr(value, "tessellate"):
        raise TypeError("actual shape has no tessellation API")
    vertices, indices = value.tessellate(float(tolerance), float(angular_tolerance))
    vertex_values = [_vertex_tuple(vertex) for vertex in vertices]
    triangles = []
    for item in indices:
        index_values = tuple(int(value) for value in item)
        if len(index_values) != 3:
            raise ValueError("tessellation emitted a non-triangle")
        triangle = tuple(vertex_values[index] for index in index_values)
        if len(set(triangle)) == 3:
            triangles.append(triangle)
    triangles.sort(key=lambda triangle: tuple(sorted(tuple(round(value, 9) for value in point) for point in triangle)))
    if not triangles:
        raise ValueError("shape tessellation produced no triangles")
    return triangles

def _project(point, matrix):
    return (
        _dot(point, matrix["right"]),
        _dot(point, matrix["up"]),
        _dot(point, matrix["forward"]),
    )

def _set_pixel(pixels, width, height, x, y, color):
    if 0 <= x < width and 0 <= y < height:
        offset = (y * width + x) * 3
        pixels[offset:offset + 3] = bytes(color)

def _draw_line(pixels, width, height, x0, y0, x1, y1, color):
    dx = abs(x1 - x0); sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0); sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        _set_pixel(pixels, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        twice = 2 * error
        if twice >= dy:
            error += dy; x0 += sx
        if twice <= dx:
            error += dx; y0 += sy

def _draw_text(pixels, width, height, x, y, text, color=(20, 32, 48), scale=2):
    cursor = x
    for character in str(text).upper():
        glyph = FONT.get(character, FONT[" "])
        for row in range(6):
            for column in range(5):
                if glyph[row * 5 + column] == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            _set_pixel(pixels, width, height, cursor + column * scale + sx, y + row * scale + sy, color)
        cursor += 6 * scale

def _triangle_normal(triangle):
    return _normalize(_cross(_sub(triangle[1], triangle[0]), _sub(triangle[2], triangle[0])))

def _edge_function(a, b, point):
    return (point[0] - a[0]) * (b[1] - a[1]) - (point[1] - a[1]) * (b[0] - a[0])

def render_triangles(
    triangles, view_name, width=256, height=256, background=(244, 246, 248),
    labels=None, frame_margin_fraction=0.08, ambient=0.28, directional=0.72,
):
    if width < 32 or height < 32:
        raise ValueError("render resolution too small")
    if not triangles:
        raise ValueError("no triangles")
    matrix = camera_matrix(view_name)
    projected = [[_project(point, matrix) for point in triangle] for triangle in triangles]
    planar = [point for triangle in projected for point in triangle]
    min_u = min(point[0] for point in planar); max_u = max(point[0] for point in planar)
    min_v = min(point[1] for point in planar); max_v = max(point[1] for point in planar)
    span_u = max(max_u - min_u, 1e-9); span_v = max(max_v - min_v, 1e-9)
    label_band = max(42, height // 8)
    margin_x = max(8, int(width * frame_margin_fraction))
    margin_y = max(8, int(height * frame_margin_fraction))
    usable_width = width - 2 * margin_x
    usable_height = height - label_band - 2 * margin_y
    scale = min(usable_width / span_u, usable_height / span_v)
    center_u = (min_u + max_u) / 2.0; center_v = (min_v + max_v) / 2.0

    def screen(point):
        return (
            width / 2.0 + (point[0] - center_u) * scale,
            label_band + usable_height / 2.0 - (point[1] - center_v) * scale,
            point[2],
        )

    pixels = bytearray(bytes(background) * width * height)
    zbuffer = [math.inf] * (width * height)
    visible_triangles = 0
    for triangle, camera_triangle in zip(triangles, projected):
        normal = _triangle_normal(triangle)
        facing = -_dot(normal, matrix["forward"])
        if facing <= 1e-10:
            continue
        points = [screen(point) for point in camera_triangle]
        area = _edge_function(points[0], points[1], points[2])
        if abs(area) <= 1e-12:
            continue
        xmin = max(0, int(math.floor(min(point[0] for point in points))))
        xmax = min(width - 1, int(math.ceil(max(point[0] for point in points))))
        ymin = max(label_band, int(math.floor(min(point[1] for point in points))))
        ymax = min(height - 1, int(math.ceil(max(point[1] for point in points))))
        intensity = max(0.0, min(1.0, ambient + directional * facing))
        color = (
            int(44 + 74 * intensity),
            int(88 + 105 * intensity),
            int(128 + 110 * intensity),
        )
        filled = False
        for y in range(ymin, ymax + 1):
            for x in range(xmin, xmax + 1):
                sample = (x + 0.5, y + 0.5)
                w0 = _edge_function(points[1], points[2], sample) / area
                w1 = _edge_function(points[2], points[0], sample) / area
                w2 = 1.0 - w0 - w1
                if min(w0, w1, w2) < -1e-9:
                    continue
                depth = w0 * points[0][2] + w1 * points[1][2] + w2 * points[2][2]
                offset = y * width + x
                if depth < zbuffer[offset]:
                    zbuffer[offset] = depth
                    pixel_offset = offset * 3
                    pixels[pixel_offset:pixel_offset + 3] = bytes(color)
                    filled = True
        visible_triangles += int(filled)
    background_bytes = bytes(background)
    mask = [
        bytes(pixels[index:index + 3]) != background_bytes
        for index in range(0, len(pixels), 3)
    ]
    if not any(mask):
        raise RuntimeError("render produced an empty image; check tessellation winding/camera")
    edge_count = 0
    for y in range(label_band + 1, height - 1):
        for x in range(1, width - 1):
            offset = y * width + x
            if not mask[offset]:
                continue
            if not all(mask[offset + delta] for delta in (-1, 1, -width, width)):
                _set_pixel(pixels, width, height, x, y, (18, 30, 44))
                edge_count += 1
    geometry_pixel_sha256 = hashlib.sha256(bytes(pixels)).hexdigest()
    labels = labels or {}
    title = f"{labels.get('part_id','TEST')} {labels.get('revision','TEST')} {view_name}"
    annotation = str(labels.get("annotations", {}).get("annotation_text", "SCALE FIT TO FRAME"))
    evidence_marker = str(labels.get("evidence_marker", "TRIANGULATED GEOMETRY"))
    _draw_text(pixels, width, height, 8, 8, title, scale=1 if width < 512 else 2)
    _draw_text(pixels, width, height, 8, 21 if width < 512 else 30, evidence_marker, scale=1 if width < 512 else 2)
    _draw_text(pixels, width, height, 8, 32 if width < 512 else 52, annotation, scale=1 if width < 512 else 2)
    axis_origin = (30, height - 30)
    axis_length = max(18, min(32, width // 10))
    axis_colors = {"X": (190, 40, 40), "Y": (40, 150, 70), "Z": (45, 85, 190)}
    projected_axes = {
        "X": (matrix["right"][0], matrix["up"][0]),
        "Y": (matrix["right"][1], matrix["up"][1]),
        "Z": (matrix["right"][2], matrix["up"][2]),
    }
    for axis_name, direction in projected_axes.items():
        endpoint = (
            int(round(axis_origin[0] + direction[0] * axis_length)),
            int(round(axis_origin[1] - direction[1] * axis_length)),
        )
        color = axis_colors[axis_name]
        if abs(direction[0]) + abs(direction[1]) <= 1e-9:
            _set_pixel(pixels, width, height, axis_origin[0], axis_origin[1], color)
            _set_pixel(pixels, width, height, axis_origin[0] + 1, axis_origin[1], color)
            endpoint = (axis_origin[0] + 3, axis_origin[1] + 3)
        else:
            _draw_line(
                pixels, width, height, axis_origin[0], axis_origin[1],
                endpoint[0], endpoint[1], color,
            )
        _draw_text(
            pixels, width, height, endpoint[0] + 2, endpoint[1] - 3,
            axis_name, color, 1,
        )
    final_mask = [
        bytes(pixels[index:index + 3]) != background_bytes
        for index in range(0, len(pixels), 3)
    ]
    object_points = [
        (index % width, index // width) for index, value in enumerate(final_mask)
        if value and index // width >= label_band
    ]
    occupied_bbox = {
        "xmin": min(point[0] for point in object_points),
        "xmax": max(point[0] for point in object_points),
        "ymin": min(point[1] for point in object_points),
        "ymax": max(point[1] for point in object_points),
    }
    luminance = [0] * 16
    for index in range(0, len(pixels), 3):
        value = int(0.2126 * pixels[index] + 0.7152 * pixels[index + 1] + 0.0722 * pixels[index + 2])
        luminance[min(15, value // 16)] += 1
    return {
        "pixels": bytes(pixels), "width": width, "height": height,
        "camera": matrix, "visible_triangle_count": visible_triangles,
        "model_units_per_pixel": 1.0 / scale,
        "projected_axis_directions": {
            "X": [matrix["right"][0], matrix["up"][0]],
            "Y": [matrix["right"][1], matrix["up"][1]],
            "Z": [matrix["right"][2], matrix["up"][2]],
        },
        "non_background_pixel_count": sum(final_mask),
        "object_non_background_pixel_count": len(object_points),
        "occupied_bbox": occupied_bbox, "edge_count_proxy": edge_count,
        "luminance_histogram": luminance,
        "pixel_sha256": hashlib.sha256(bytes(pixels)).hexdigest(),
        "geometry_pixel_sha256": geometry_pixel_sha256,
        "background_rgb": list(background), "input_kind": "TRIANGULATED_SOLID",
        "overlay_labels": [title, evidence_marker, annotation],
    }

def _png_chunk(name, payload):
    return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", binascii.crc32(name + payload) & 0xffffffff)

def encode_png_rgb(width, height, pixels):
    if len(pixels) != width * height * 3:
        raise ValueError("pixel buffer length mismatch")
    raw = b"".join(
        b"\x00" + pixels[row * width * 3:(row + 1) * width * 3]
        for row in range(height)
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return PNG_SIGNATURE + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", zlib.compress(raw, 9)) + _png_chunk(b"IEND", b"")

def write_png_rgb(path, width, height, pixels):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = encode_png_rgb(width, height, pixels)
    destination.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()

def read_png_rgb(path_or_bytes):
    data = Path(path_or_bytes).read_bytes() if isinstance(path_or_bytes, (str, Path)) else bytes(path_or_bytes)
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")
    offset = len(PNG_SIGNATURE); chunks = []; idat = bytearray()
    width = height = bit_depth = color_type = None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack_from(">I", data, offset)[0]
        name = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if binascii.crc32(name + payload) & 0xffffffff != expected_crc:
            raise ValueError(f"PNG CRC mismatch: {name!r}")
        chunks.append(name.decode("ascii"))
        if name == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", payload)
            if (bit_depth, color_type, compression, filter_method, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("unsupported PNG format")
        elif name == b"IDAT":
            idat.extend(payload)
        elif name == b"IEND":
            break
        offset += 12 + length
    if chunks[:1] != ["IHDR"] or "IDAT" not in chunks or chunks[-1:] != ["IEND"]:
        raise ValueError("required PNG chunks missing or out of order")
    raw = zlib.decompress(bytes(idat))
    row_size = width * 3
    expected_size = height * (row_size + 1)
    if len(raw) != expected_size:
        raise ValueError("PNG decompressed row count/size mismatch")
    pixels = bytearray()
    for row in range(height):
        start = row * (row_size + 1)
        if raw[start] != 0:
            raise ValueError("unsupported PNG filter")
        pixels.extend(raw[start + 1:start + 1 + row_size])
    return {
        "width": width, "height": height, "bit_depth": bit_depth,
        "color_type": color_type, "pixels": bytes(pixels), "chunks": chunks,
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "pixel_sha256": hashlib.sha256(bytes(pixels)).hexdigest(),
    }

def validate_png(path, background=(244, 246, 248)):
    try:
        decoded = read_png_rgb(path)
        background_bytes = bytes(background)
        non_background = sum(
            decoded["pixels"][index:index + 3] != background_bytes
            for index in range(0, len(decoded["pixels"]), 3)
        )
        return {
            "status": "PASS" if non_background > 0 else "FAIL",
            "width": decoded["width"], "height": decoded["height"],
            "color_type": decoded["color_type"],
            "non_background_pixel_count": non_background,
            "file_sha256": decoded["file_sha256"],
            "pixel_sha256": decoded["pixel_sha256"], "error": "",
        }
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc), "non_background_pixel_count": 0}

def render_shape_to_png(
    actual_shape, path, part_id, revision, view_name, settings,
    assembly_transform=None, annotations=None,
):
    triangles = tessellate_shape(
        actual_shape, settings["tessellation_tolerance_mm"], settings["angular_tolerance"]
    )
    width, height = settings["resolution"]
    result = render_triangles(
        triangles, view_name, width, height, tuple(settings["background_rgb"]),
        labels={
            "part_id": part_id, "revision": revision,
            "annotations": annotations or {},
            "evidence_marker": "X Y Z ACTUAL SOLID",
        },
        frame_margin_fraction=settings["frame_margin_fraction"],
        ambient=settings["ambient"], directional=settings["directional"],
    )
    file_hash = write_png_rgb(path, width, height, result["pixels"])
    solid_fingerprint = geometry_fingerprint(actual_shape)
    manifest = {
        key: value for key, value in result.items() if key != "pixels"
    }
    manifest.update({
        "part_id": part_id, "revision": revision, "view": view_name,
        "filename": str(path), "file_sha256": file_hash,
        "source_solid_fingerprint": solid_fingerprint,
        "assembly_transform": assembly_transform or "IDENTITY",
        "render_settings": settings, "actual_solid_evidence": True,
    })
    return manifest, result["pixels"]
