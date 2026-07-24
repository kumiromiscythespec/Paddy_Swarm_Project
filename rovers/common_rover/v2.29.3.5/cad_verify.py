from __future__ import annotations
import hashlib
import math
import struct
from collections import Counter
from pathlib import Path
from cad_export import SECTIONED_STEP_NAME, localized_shape
from cad_primitives import geometry_fingerprint, require_cadquery

def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _triangle_area_squared(a, b, c):
    ab = tuple(b[index] - a[index] for index in range(3))
    ac = tuple(c[index] - a[index] for index in range(3))
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return sum(value * value for value in cross) / 4.0

def read_stl_metrics(path):
    data = Path(path).read_bytes()
    triangles = []
    encoding = "ASCII"
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            encoding = "BINARY"
            for index in range(count):
                values = struct.unpack_from("<12fH", data, 84 + index * 50)
                triangles.append((values[3:6], values[6:9], values[9:12]))
    if not triangles:
        text = data.decode("utf-8", errors="strict")
        vertices = []
        for line in text.splitlines():
            tokens = line.strip().split()
            if len(tokens) == 4 and tokens[0].lower() == "vertex":
                vertices.append(tuple(float(value) for value in tokens[1:]))
        if len(vertices) % 3 != 0:
            raise ValueError("ASCII STL vertex count is not divisible by three")
        triangles = [tuple(vertices[index:index + 3]) for index in range(0, len(vertices), 3)]
    if not triangles:
        raise ValueError(f"empty STL mesh: {path}")
    points = [point for triangle in triangles for point in triangle]
    xs, ys, zs = zip(*points)
    signed_volume = 0.0
    degenerate = 0
    edges = Counter()
    for a, b, c in triangles:
        if _triangle_area_squared(a, b, c) <= 1e-18:
            degenerate += 1
        signed_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
        rounded = [tuple(round(value, 7) for value in point) for point in (a, b, c)]
        for first, second in ((rounded[0], rounded[1]), (rounded[1], rounded[2]), (rounded[2], rounded[0])):
            edges[tuple(sorted((first, second)))] += 1
    watertight = bool(edges) and all(count == 2 for count in edges.values())
    return {
        "encoding": encoding, "triangle_count": len(triangles),
        "bbox": {"xmin": min(xs), "xmax": max(xs), "ymin": min(ys), "ymax": max(ys), "zmin": min(zs), "zmax": max(zs)},
        "mesh_volume_mm3_candidate": abs(signed_volume),
        "degenerate_triangle_count": degenerate,
        "watertight_candidate": watertight,
        "volume_comparison_reliable": watertight and degenerate == 0,
        "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
    }

def compare_bbox(source_bbox, imported_bbox, tolerance_mm):
    keys = ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
    deviations = {key: abs(float(source_bbox[key]) - float(imported_bbox[key])) for key in keys}
    return max(deviations.values()), all(value <= tolerance_mm for value in deviations.values())

def compare_volume(source_volume, imported_volume, relative_tolerance):
    denominator = max(abs(float(source_volume)), 1e-9)
    deviation = abs(float(source_volume) - float(imported_volume)) / denominator
    return deviation, deviation <= relative_tolerance

def verify_component_steps(verification_root, component_export_rows, bbox_tolerance_mm, volume_relative_tolerance):
    cq = require_cadquery()
    results = []
    for row in component_export_rows:
        path = Path(verification_root) / row["filename"]
        imported = cq.importers.importStep(str(path))
        imported_fp = geometry_fingerprint(imported)
        source_fp = row["source_fingerprint"]
        bbox_deviation, bbox_ok = compare_bbox(source_fp["bbox"], imported_fp["bbox"], bbox_tolerance_mm)
        volume_deviation, volume_ok = compare_volume(source_fp["volume_mm3"], imported_fp["volume_mm3"], volume_relative_tolerance)
        results.append({
            "assembly_id": row["assembly_id"], "component_id": row["component_id"],
            "filename": row["filename"], "bbox_max_deviation_mm": bbox_deviation,
            "bbox_match": bbox_ok, "volume_relative_deviation": volume_deviation,
            "volume_match": volume_ok, "source_face_count": source_fp["face_count"],
            "imported_face_count": imported_fp["face_count"], "source_edge_count": source_fp["edge_count"],
            "imported_edge_count": imported_fp["edge_count"], "imported_valid": True,
            "status": "PASS" if bbox_ok and volume_ok else "FAIL",
        })
    return results

def verify_assembly_steps(step_root, export_rows, bbox_tolerance_mm, volume_relative_tolerance):
    cq = require_cadquery()
    results = []
    for row in export_rows:
        path = Path(step_root) / row["filename"]
        imported = cq.importers.importStep(str(path))
        imported_fp = geometry_fingerprint(imported)
        source_fp = row["source_aggregate_fingerprint"]
        bbox_deviation, bbox_ok = compare_bbox(source_fp["bbox"], imported_fp["bbox"], bbox_tolerance_mm)
        volume_deviation, volume_ok = compare_volume(source_fp["volume_mm3"], imported_fp["volume_mm3"], volume_relative_tolerance)
        results.append({
            "filename": row["filename"], "expected_component_count": row["component_count"],
            "component_set_hash": row["component_set_hash"], "source_fingerprint": source_fp,
            "imported_fingerprint": imported_fp, "bbox_max_deviation_mm": bbox_deviation,
            "bbox_match": bbox_ok, "volume_relative_deviation": volume_deviation,
            "volume_match": volume_ok, "file_sha256": file_sha256(path),
            "status": "PASS" if bbox_ok and volume_ok else "FAIL",
        })
    return results

def verify_stl_source_matches(stl_root, stl_export_rows, parts, bbox_tolerance_mm, volume_relative_tolerance):
    results, hashes = [], {}
    for row in stl_export_rows:
        part_id = row["part_id"]
        source_fp = geometry_fingerprint(localized_shape(parts[part_id]))
        metrics = read_stl_metrics(Path(stl_root) / row["filename"])
        bbox_deviation, bbox_ok = compare_bbox(source_fp["bbox"], metrics["bbox"], bbox_tolerance_mm)
        volume_deviation, volume_ok = compare_volume(source_fp["volume_mm3"], metrics["mesh_volume_mm3_candidate"], volume_relative_tolerance)
        group = row.get("geometry_equivalence_group", "")
        prior = hashes.get(metrics["sha256"])
        duplicate_ok = not prior or bool(group) and prior["group"] == group
        hashes[metrics["sha256"]] = {"part_id": part_id, "group": group}
        hard_ok = bbox_ok and metrics["triangle_count"] > 0 and metrics["degenerate_triangle_count"] == 0 and duplicate_ok
        results.append({
            "part_id": part_id, "filename": row["filename"], "source_bbox": source_fp["bbox"],
            "mesh_bbox": metrics["bbox"], "bbox_max_deviation_mm": bbox_deviation,
            "bbox_match": bbox_ok, "source_volume_mm3": source_fp["volume_mm3"],
            "mesh_volume_mm3_candidate": metrics["mesh_volume_mm3_candidate"],
            "volume_relative_deviation": volume_deviation,
            "volume_match": volume_ok if metrics["volume_comparison_reliable"] else "MEASUREMENT_HOLD_PARSER_RELIABILITY",
            "triangle_count": metrics["triangle_count"], "degenerate_triangle_count": metrics["degenerate_triangle_count"],
            "watertight_candidate": metrics["watertight_candidate"], "sha256": metrics["sha256"],
            "geometry_equivalence_group": group, "duplicate_policy_pass": duplicate_ok,
            "status": "PASS" if hard_ok else "FAIL",
        })
    return results

def verify_exported_outputs(output_root, export_rows, component_rows, stl_rows, parts, params):
    root = Path(output_root)
    assembly = verify_assembly_steps(root / "step", export_rows, params["step_bbox_tolerance_mm"], params["step_volume_relative_tolerance"])
    components = verify_component_steps(root / "verification" / "component_steps", component_rows, params["step_bbox_tolerance_mm"], params["step_volume_relative_tolerance"])
    stls = verify_stl_source_matches(root / "stl", stl_rows, parts, params["stl_bbox_tolerance_mm"], params["stl_volume_relative_tolerance"])
    hashes = [item["file_sha256"] for item in assembly]
    sectioned = next(item for item in assembly if item["filename"] == SECTIONED_STEP_NAME)
    upper = next(item for item in assembly if item["filename"] == "v229_3_2_upper_assembly.step")
    sectioned_duplicate = (
        sectioned["file_sha256"] == upper["file_sha256"]
        or sectioned["imported_fingerprint"]["normalized_sha256"] == upper["imported_fingerprint"]["normalized_sha256"]
    )
    sectioned_geometry_difference = (
        sectioned["imported_fingerprint"]["bbox"] != upper["imported_fingerprint"]["bbox"]
        or sectioned["imported_fingerprint"]["volume_mm3"] != upper["imported_fingerprint"]["volume_mm3"]
    )
    sectioned_volume_reduction = (
        sectioned["imported_fingerprint"]["volume_mm3"]
        < upper["imported_fingerprint"]["volume_mm3"]
    )
    return {
        "assembly_steps": assembly, "component_steps": components, "stl_source_matches": stls,
        "distinct_step_count": len(set(hashes)), "duplicate_step_count": len(hashes) - len(set(hashes)),
        "sectioned_step_duplicate": sectioned_duplicate,
        "sectioned_geometry_difference": sectioned_geometry_difference,
        "sectioned_volume_reduction": sectioned_volume_reduction,
        "step_failure_count": (
            sum(item["status"] != "PASS" for item in assembly)
            + sum(item["status"] != "PASS" for item in components)
            + int(not sectioned_geometry_difference)
            + int(not sectioned_volume_reduction)
        ),
        "stl_failure_count": sum(item["status"] != "PASS" for item in stls),
    }
