from __future__ import annotations
import hashlib
import json
from pathlib import Path
from cad_primitives import geometry_fingerprint, require_cadquery, shape_bbox, union_all

SECTIONED_STEP_NAME = "v229_3_2_sectioned_review_assembly.step"

def localized_shape(shape):
    bbox = shape_bbox(shape)
    return shape.translate((-bbox["xmin"], -bbox["ymin"], -bbox["zmin"]))

def compound_fingerprint(shapes):
    cq = require_cadquery()
    assembly = cq.Assembly(name="fingerprint_source")
    for index, shape in enumerate(shapes):
        assembly.add(shape, name=f"part_{index:05d}")
    return geometry_fingerprint(assembly.toCompound())

def export_verification_component_steps(assembly_id, component_shapes, output_dir):
    cq = require_cadquery()
    destination = Path(output_dir) / Path(assembly_id).stem
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for component_id, shape in sorted(component_shapes.items()):
        safe_name = component_id.replace("::", "__").replace("/", "_")
        path = destination / f"{safe_name}.step"
        cq.exporters.export(shape, str(path))
        rows.append({
            "assembly_id": assembly_id, "component_id": component_id,
            "filename": path.relative_to(Path(output_dir)).as_posix(),
            "source_fingerprint": geometry_fingerprint(shape),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return rows

def export_step_assemblies(parts, expected_component_sets, sectioned_review_parts, output_dir, verification_dir):
    cq = require_cadquery()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows, component_rows = [], []
    for filename, expected_ids in sorted(expected_component_sets.items()):
        if filename == SECTIONED_STEP_NAME:
            component_shapes = dict(sectioned_review_parts)
        else:
            missing = [part_id for part_id in expected_ids if part_id not in parts]
            if missing:
                raise KeyError(f"{filename} missing built parts: {missing[:10]}")
            component_shapes = {part_id: parts[part_id] for part_id in expected_ids}
        if not component_shapes:
            raise RuntimeError(f"empty STEP assembly: {filename}")
        assembly = cq.Assembly(name=Path(filename).stem)
        for component_id, shape in sorted(component_shapes.items()):
            assembly.add(shape, name=component_id)
        path = destination / filename
        cq.exporters.export(assembly.toCompound(), str(path))
        source_fingerprint = geometry_fingerprint(assembly.toCompound())
        component_set_hash = hashlib.sha256(
            "\n".join(sorted(component_shapes)).encode("utf-8")
        ).hexdigest()
        rows.append({
            "filename": filename, "component_count": len(component_shapes),
            "component_ids": sorted(component_shapes),
            "component_set_hash": component_set_hash,
            "source_aggregate_fingerprint": source_fingerprint,
            "sectioned_source": filename == SECTIONED_STEP_NAME,
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
        component_rows.extend(
            export_verification_component_steps(filename, component_shapes, verification_dir)
        )
    return rows, component_rows

def export_print_stls(parts, print_manifest, output_dir):
    cq = require_cadquery()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in print_manifest["parts"]:
        part_id = item["part_id"]
        if part_id not in parts:
            raise KeyError(f"print target not built: {part_id}")
        source_shape = localized_shape(parts[part_id])
        path = destination / f"{part_id}.stl"
        cq.exporters.export(source_shape, str(path), tolerance=0.05, angularTolerance=0.1)
        rows.append({
            "part_id": part_id, "filename": path.name, "source_solid_id": part_id,
            "geometry_equivalence_group": item.get("geometry_equivalence_group", ""),
            "source_fingerprint": geometry_fingerprint(source_shape),
            "size_bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return rows
