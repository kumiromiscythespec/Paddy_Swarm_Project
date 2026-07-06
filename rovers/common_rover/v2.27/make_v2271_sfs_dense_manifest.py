import csv
from pathlib import Path

out = Path("rover_v2271_sfs_out")
src = out / "print_manifest.csv"
dst = out / "print_manifest_generic_marked.csv"

with src.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

extra_fields = [
    "part_no", "part_code", "label", "label_text",
    "name", "part_name", "quantity", "count",
    "material_hint", "material_group", "is_tpu", "split_group",
    "plate_id", "plate_group", "module", "title",
    "stl", "stl_file", "stl_path", "file", "filename", "path", "file_path",
    "source_file", "source_path", "output_stl",
    "step", "step_file", "step_path",
    "bbox_x", "bbox_y", "bbox_z",
    "printable", "marked",
]

fields = list(rows[0].keys())
for f in extra_fields:
    if f not in fields:
        fields.append(f)

fixed = []
for r in rows:
    part_id = r.get("part_id", "").strip()
    plate = r.get("plate", "SFS-RIGID").strip() or "SFS-RIGID"
    qty = r.get("qty", "1").strip() or "1"
    material = r.get("material", "PETG").strip() or "PETG"
    desc = r.get("description", "").strip() or part_id

    stl_name = r.get("filename_stl", "").strip() or f"{part_id}.stl"
    step_name = r.get("filename_step", "").strip() or f"{part_id}.step"

    stl_path = f"stl/{stl_name}"
    step_path = f"step/{step_name}"

    r.update({
        "part_no": part_id,
        "part_code": part_id,
        "label": part_id,
        "label_text": part_id,
        "name": desc,
        "part_name": desc,
        "quantity": qty,
        "count": qty,
        "material_hint": material,
        "material_group": "HARD",
        "is_tpu": "0",
        "split_group": "HARD",
        "plate_id": plate,
        "plate_group": plate,
        "module": "v2271_summer_float_shell",
        "title": desc,
        "stl": stl_path,
        "stl_file": stl_path,
        "stl_path": stl_path,
        "file": stl_path,
        "filename": stl_name,
        "path": stl_path,
        "file_path": stl_path,
        "source_file": stl_path,
        "source_path": stl_path,
        "output_stl": stl_path,
        "step": step_path,
        "step_file": step_path,
        "step_path": step_path,
        "bbox_x": r.get("bbox_x_mm", ""),
        "bbox_y": r.get("bbox_y_mm", ""),
        "bbox_z": r.get("bbox_z_mm", ""),
        "printable": "1",
        "marked": "1",
    })
    fixed.append(r)

with dst.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(fixed)

print(f"Wrote {dst}")
