from __future__ import annotations
import hashlib
import json
from pathlib import Path
from software_renderer import CAMERA_AUTHORITY, REQUIRED_VIEWS, render_shape_to_png

SECTION_VIEW_NAMES = ("section_longitudinal", "section_fastener", "mount_detail")

def render_settings(params, kind="standard", test_mode=False):
    renderer = params["renderer"]
    resolution = (
        renderer["test_resolution"] if test_mode
        else renderer["section_resolution"] if kind == "section"
        else renderer["detail_resolution"] if kind == "detail"
        else renderer["standard_resolution"]
    )
    return {
        "resolution": list(resolution),
        "background_rgb": list(renderer["background_rgb"]),
        "ambient": renderer["ambient"], "directional": renderer["directional"],
        "frame_margin_fraction": renderer["frame_margin_fraction"],
        "tessellation_tolerance_mm": renderer["tessellation_tolerance_mm"],
        "angular_tolerance": renderer["angular_tolerance"],
        "formal_review": not test_mode,
    }

def render_actual_solid_views(
    actual_shape, part_id, revision, output_dir, params,
    source_measurements, assembly_transform=None, test_mode=False,
):
    if actual_shape is None:
        raise ValueError("actual shape required")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows, buffers = [], {}
    settings = render_settings(params, "standard", test_mode)
    for view_name in REQUIRED_VIEWS:
        path = destination / f"{part_id}_{revision}_{view_name}.png"
        row, pixels = render_shape_to_png(
            actual_shape, path, part_id, revision, view_name, settings,
            assembly_transform=assembly_transform,
            annotations=source_measurements,
        )
        rows.append(row); buffers[view_name] = pixels
    return rows, buffers

def render_actual_section_views(
    section_shapes, part_id, revision, output_dir, params,
    source_measurements, section_metadata, test_mode=False,
):
    if set(section_shapes) != set(SECTION_VIEW_NAMES):
        raise ValueError(f"three distinct section solids required: {SECTION_VIEW_NAMES}")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows, buffers = [], {}
    for view_name in SECTION_VIEW_NAMES:
        shape = section_shapes[view_name]
        if shape is None:
            raise ValueError(f"{view_name} section result unavailable; source solid reuse forbidden")
        kind = "detail" if view_name == "mount_detail" else "section"
        settings = render_settings(params, kind, test_mode)
        camera_view = "iso" if view_name == "mount_detail" else "front"
        path = destination / f"{part_id}_{revision}_{view_name}.png"
        row, pixels = render_shape_to_png(
            shape, path, part_id, revision, camera_view, settings,
            annotations={
                **source_measurements,
                "section_view": view_name,
                "section_plane": section_metadata[view_name]["plane"],
                "keep_side": section_metadata[view_name]["keep_side"],
                "annotation_text": (
                    f"{source_measurements.get('annotation_text', 'ACTUAL SECTION')} "
                    f"PLANE {section_metadata[view_name]['plane']} "
                    f"KEEP {section_metadata[view_name]['keep_side']}"
                ),
            },
        )
        row.update({
            "view": view_name, "camera_view": camera_view,
            "section_plane": section_metadata[view_name]["plane"],
            "keep_side": section_metadata[view_name]["keep_side"],
            "section_solid_evidence": True,
        })
        rows.append(row); buffers[view_name] = pixels
    return rows, buffers

def image_manifest_sha256(rows):
    payload = [
        {
            "part_id": row["part_id"], "revision": row["revision"],
            "view": row["view"], "file_sha256": row["file_sha256"],
            "pixel_sha256": row["pixel_sha256"],
            "source_solid_fingerprint": row["source_solid_fingerprint"],
        }
        for row in sorted(rows, key=lambda value: value["view"])
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
