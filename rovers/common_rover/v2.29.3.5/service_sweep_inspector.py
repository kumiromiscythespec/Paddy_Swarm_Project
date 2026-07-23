from __future__ import annotations
from cad_primitives import cylinder_along_axis, safe_boolean, shape_volume

def _scaled(vector, factor):
    return tuple(float(value) * float(factor) for value in vector)

def inspect_service_sweeps(assembly, boolean_tolerance_mm3=0.001):
    solids = assembly["solids"]
    rows = []
    for instance in assembly["fastener_instances"]:
        axis = instance["axis_direction_xyz"]
        origin = instance["axis_origin_xyz"]
        host_ids = {instance["parent_component"], instance["child_component"]}
        sweep_specs = [
            ("BOLT_INSERTION", instance["clearance_hole_candidate_mm"], instance["insertion_path"]["length_mm"]),
            ("DRIVER_INSERTION", instance["tool_envelope"]["diameter_mm"], instance["tool_envelope"]["axial_clearance_mm"]),
            ("WRENCH_ENVELOPE", instance["tool_envelope"]["diameter_mm"], instance["tool_envelope"]["axial_clearance_mm"]),
            ("FASTENER_REMOVAL", instance["clearance_hole_candidate_mm"], instance["removal_path"]["length_mm"]),
        ]
        for sweep_type, diameter, length in sweep_specs:
            sweep = cylinder_along_axis(origin, axis, float(diameter), float(length))
            obstructions = []
            for part_id, solid in solids.items():
                if part_id in host_ids:
                    continue
                common = safe_boolean(sweep, solid, "intersect", f"service:{instance['fastener_instance_id']}:{sweep_type}:{part_id}")
                volume = shape_volume(common)
                if volume > boolean_tolerance_mm3:
                    obstructions.append({"part_id": part_id, "intersection_volume_mm3": volume})
            rows.append({
                "sweep_id": f"{instance['fastener_instance_id']}::{sweep_type}",
                "fastener_instance_id": instance["fastener_instance_id"],
                "sweep_type": sweep_type, "sampled_position_count": 1,
                "sweep_solid_generated": True, "obstructions": obstructions,
                "status": "FAIL_HARD_OBSTRUCTION" if obstructions else "PASS",
            })
    rows.extend([
        {
            "sweep_id": f"RAIL::{name}", "fastener_instance_id": "",
            "sweep_type": name, "sampled_position_count": 0,
            "sweep_solid_generated": False, "obstructions": [],
            "status": "CONDITIONAL_HOLD_UNDEFINED_TRANSLATION_DIRECTION",
        }
        for name in ("RAIL_REMOVAL", "ADJACENT_BRACKET_REMOVAL", "LOWER_ADAPTER_ACCESS")
    ])
    obstruction_count = sum(row["status"] == "FAIL_HARD_OBSTRUCTION" for row in rows)
    return {
        "rows": rows, "service_sweep_obstruction_count": obstruction_count,
        "bolt_insertion_result": _aggregate(rows, "BOLT_INSERTION"),
        "tool_access_result": _aggregate(rows, "DRIVER_INSERTION", "WRENCH_ENVELOPE"),
        "removal_path_result": _aggregate(rows, "FASTENER_REMOVAL", "RAIL_REMOVAL"),
        "status": "FAIL" if obstruction_count else "CONDITIONAL_HOLD" if any("CONDITIONAL" in row["status"] for row in rows) else "PASS",
    }

def _aggregate(rows, *types):
    selected = [row["status"] for row in rows if row["sweep_type"] in types]
    if any(status == "FAIL_HARD_OBSTRUCTION" for status in selected):
        return "FAIL"
    if any("CONDITIONAL" in status for status in selected):
        return "CONDITIONAL_HOLD"
    return "PASS" if selected and all(status == "PASS" for status in selected) else "NOT_RUN"

def validate_service_sweep_claim(record):
    errors = []
    if record.get("status") == "PASS":
        if not record.get("rows"):
            errors.append("PASS without sweep records")
        if any(not row.get("sweep_solid_generated") for row in record.get("rows", [])):
            errors.append("PASS with unexecuted sweep")
        if record.get("service_sweep_obstruction_count"):
            errors.append("hard service obstruction cannot be a hold/PASS")
    return errors
