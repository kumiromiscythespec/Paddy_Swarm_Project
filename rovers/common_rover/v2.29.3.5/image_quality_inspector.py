from __future__ import annotations
import json
from pathlib import Path
from software_renderer import CAMERA_AUTHORITY, REQUIRED_VIEWS, camera_matrix, validate_png

def inspect_image_record(row, expected_part_id, expected_revision, expected_source_fingerprint):
    errors = []
    path = Path(row.get("filename", ""))
    if not path.is_file():
        errors.append("file missing")
        validation = {"status": "FAIL", "non_background_pixel_count": 0}
    else:
        validation = validate_png(path)
        if validation["status"] != "PASS":
            errors.append(f"invalid PNG: {validation.get('error','')}")
    if row.get("part_id") != expected_part_id:
        errors.append("wrong part ID")
    if row.get("revision") != expected_revision:
        errors.append("wrong revision")
    if not row.get("actual_solid_evidence") or row.get("input_kind") != "TRIANGULATED_SOLID":
        errors.append("not actual triangulated-solid evidence")
    if row.get("source_solid_fingerprint") != expected_source_fingerprint:
        errors.append("source fingerprint mismatch")
    view = row.get("view")
    camera_view = row.get("camera_view", view)
    if camera_view in CAMERA_AUTHORITY:
        expected_matrix = camera_matrix(camera_view)
        if row.get("camera") != expected_matrix:
            errors.append("camera authority violation")
        expected_axes = {
            "X": [expected_matrix["right"][0], expected_matrix["up"][0]],
            "Y": [expected_matrix["right"][1], expected_matrix["up"][1]],
            "Z": [expected_matrix["right"][2], expected_matrix["up"][2]],
        }
        if row.get("projected_axis_directions") != expected_axes:
            errors.append("projected axis authority violation")
    occupied = row.get("occupied_bbox", {})
    width = validation.get("width", row.get("width", 0))
    height = validation.get("height", row.get("height", 0))
    expected_resolution = row.get("render_settings", {}).get("resolution")
    if expected_resolution and [width, height] != list(expected_resolution):
        errors.append("PNG resolution differs from render authority")
    if occupied:
        if min(occupied.get("xmin", 0), occupied.get("ymin", 0)) <= 0 or occupied.get("xmax", width) >= width - 1 or occupied.get("ymax", height) >= height - 1:
            errors.append("image clipping")
        area = max(0, occupied.get("xmax", 0) - occupied.get("xmin", 0)) * max(0, occupied.get("ymax", 0) - occupied.get("ymin", 0))
        if width and height and area / (width * height) < 0.01:
            errors.append("occupied area too small")
    labels = " ".join(row.get("overlay_labels", []))
    if str(view).upper() not in labels and not str(view).startswith(("section_", "mount_")):
        errors.append("view label mismatch")
    if "X Y Z ACTUAL SOLID" not in labels:
        errors.append("axis or actual-solid label missing")
    if len(row.get("overlay_labels", [])) < 3 or "ACTUAL" not in str(row.get("overlay_labels", ["", "", ""])[2]).upper():
        errors.append("actual measurement annotation missing")
    return {
        "view": view, "status": "PASS" if not errors else "FAIL",
        "errors": errors, "png_validation": validation,
    }

def inspect_view_set(rows, expected_part_id, expected_revision, expected_source_fingerprint):
    directional = [row for row in rows if row.get("view") in REQUIRED_VIEWS]
    sections = [row for row in rows if row.get("view") not in REQUIRED_VIEWS]
    results = [
        inspect_image_record(row, expected_part_id, expected_revision, expected_source_fingerprint)
        for row in rows
    ]
    errors = []
    present = {row.get("view") for row in directional}
    if present != set(REQUIRED_VIEWS):
        errors.append(f"directional view set mismatch: {sorted(present)}")
    matrices = [json.dumps(row.get("camera"), sort_keys=True) for row in directional]
    if len(matrices) != len(set(matrices)):
        errors.append("duplicate camera matrix")
    pixel_hashes = [row.get("pixel_sha256") for row in directional]
    geometry_hashes = [row.get("geometry_pixel_sha256") for row in directional]
    if geometry_hashes and len(set(geometry_hashes)) == 1:
        errors.append("all directional images have identical geometry pixels")
    by_view = {row.get("view"): row for row in directional}
    for first, second in (("front", "rear"), ("left", "right"), ("top", "bottom")):
        if first in by_view and second in by_view and by_view[first].get("camera") == by_view[second].get("camera"):
            errors.append(f"{first}/{second} camera collision")
    if "iso" in by_view:
        for side in ("front", "rear", "left", "right", "top", "bottom"):
            if side in by_view and by_view["iso"].get("camera") == by_view[side].get("camera"):
                errors.append(f"iso camera equals {side}")
    normal_hashes = set(geometry_hashes)
    for row in sections:
        if row.get("geometry_pixel_sha256") in normal_hashes:
            errors.append(f"section image reused normal image: {row.get('view')}")
        if not row.get("section_solid_evidence"):
            errors.append(f"section evidence missing: {row.get('view')}")
    errors.extend(
        f"{result['view']}: {error}"
        for result in results for error in result["errors"]
    )
    return {
        "status": "PASS" if not errors else "FAIL",
        "image_results": results, "errors": errors,
        "directional_view_count": len(directional), "section_view_count": len(sections),
        "invalid_png_count": sum(result["png_validation"].get("status") != "PASS" for result in results),
        "camera_authority_failure_count": sum("camera" in error for error in errors),
        "image_duplicate_anomaly_count": sum("identical" in error or "reused" in error or "collision" in error for error in errors),
        "scope": "AUTOMATED_FILE_QUALITY_DIRECTION_AND_DIFFERENCE_ONLY",
        "content_review_claimed": False,
    }
