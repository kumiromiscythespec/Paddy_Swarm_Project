from __future__ import annotations
import math
from cad_primitives import shape_bbox

ACTIVE_PART_ID = "V2292-FPB-RAIL-L"

def _component_bbox(component):
    boxes = component["boxes"]
    return {
        "xmin": min(box[0] for box in boxes), "xmax": max(box[1] for box in boxes),
        "ymin": min(box[2] for box in boxes), "ymax": max(box[3] for box in boxes),
        "zmin": min(box[4] for box in boxes), "zmax": max(box[5] for box in boxes),
    }

def build_tolerance_registry(registries):
    component = next(item for item in registries["components"] if item["part_id"] == ACTIVE_PART_ID)
    bbox = _component_bbox(component)
    entries = []
    for axis, lower, upper in (
        ("X", "xmin", "xmax"), ("Y", "ymin", "ymax"), ("Z", "zmin", "zmax")
    ):
        entries.append({
            "inspection_id": f"BBOX_SIZE_{axis}", "design_parameter": f"outer_size_{axis.lower()}_mm",
            "design_value": bbox[upper] - bbox[lower],
            "tolerance_type": "TOLERANCE_MEASUREMENT_REQUIRED",
            "minimum": None, "maximum": None, "unit": "mm",
            "reason": "repository defines design extent but not acceptance tolerance",
            "provenance": "component_registry.json", "fixed_or_conditional": "CONDITIONAL",
        })
    for opening in registries["openings"]:
        if opening["host_component"] != ACTIVE_PART_ID:
            continue
        axis = opening["direction"][0].upper()
        axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
        diameter = min(
            float(value) for index, value in enumerate(opening["dimensions_mm"])
            if index != axis_index
        )
        for metric, value in (("CENTER", opening["center_xyz"]), ("DIAMETER", diameter)):
            entries.append({
                "inspection_id": f"{opening['opening_id']}_{metric}",
                "design_parameter": f"{opening['opening_id']}_{metric.lower()}",
                "design_value": value,
                "tolerance_type": "TOLERANCE_MEASUREMENT_REQUIRED",
                "minimum": None, "maximum": None, "unit": "mm",
                "reason": "registry candidate lacks manufacturing acceptance tolerance",
                "provenance": "opening_registry.json", "fixed_or_conditional": "CONDITIONAL",
            })
    return entries

def freeze_loop_001_specification(registries, revision="revA"):
    component = next(item for item in registries["components"] if item["part_id"] == ACTIVE_PART_ID)
    bbox = _component_bbox(component)
    openings = [item for item in registries["openings"] if item["host_component"] == ACTIVE_PART_ID]
    attachments = [
        item for item in registries["attachments"]
        if ACTIVE_PART_ID in {item["parent_component"], item["child_component"]}
    ]
    fasteners = [
        item for item in registries["fasteners"]["instances"]
        if ACTIVE_PART_ID in {item["parent_component"], item["child_component"]}
    ]
    sizes = {
        "X_mm": bbox["xmax"] - bbox["xmin"],
        "Y_mm": bbox["ymax"] - bbox["ymin"],
        "Z_mm": bbox["zmax"] - bbox["zmin"],
    }
    fixed_parameters = {
        "part_id": ACTIVE_PART_ID, "revision": revision,
        "classification": component["classification"], "role": component["role"],
        "outer_size_X_mm": sizes["X_mm"], "outer_size_Y_mm": sizes["Y_mm"],
        "outer_size_Z_mm": sizes["Z_mm"], "assembly_bbox_mm": bbox,
        "coordinate_system": {"X": "left_positive", "Y": "rear_positive", "Z": "up_positive"},
        "z_zero": "ALUMINUM_FRAME_TOP",
    }
    candidate_parameters = {
        "material_candidate": component["status"],
        "mounting_faces": sorted({
            item["parent_face_id"] if item["parent_component"] == ACTIVE_PART_ID else item["child_face_id"]
            for item in fasteners
        }),
        "fastener_groups": sorted({item["fastener_group_id"] for item in fasteners}),
        "hole_centers": {item["opening_id"]: item["center_xyz"] for item in openings},
        "hole_diameters": {
            item["opening_id"]: min(
                float(value) for index, value in enumerate(item["dimensions_mm"])
                if index != {"X": 0, "Y": 1, "Z": 2}[item["direction"][0].upper()]
            )
            for item in openings
        },
        "load_directions": sorted({load for item in attachments for load in item["load_types"]}),
        "print_orientations": ["ORIGINAL", "ROTATE_X_90", "ROTATE_Y_90", "ROTATE_180"],
    }
    undefined_parameters = {
        "actual_material": "MEASUREMENT_REQUIRED",
        "manufacturing_tolerance": "REPOSITORY_DEFINITION_MISSING",
        "lower_adapter_physical_interface": "MEASUREMENT_REQUIRED",
        "structural_allowable": "MEASUREMENT_REQUIRED",
        "bambu_a1_z_authority": "REPOSITORY_DEFINITION_MISSING",
        "physical_surface_finish": "MEASUREMENT_REQUIRED",
    }
    return {
        "schema": "PS_LOOP_PART_SPECIFICATION_V2",
        "loop_id": "LOOP-001", "part_id": ACTIVE_PART_ID, "revision": revision,
        "source_status": "IMPLEMENTED", "geometry_source": "component_registry.json",
        "outer_dimensions_mm": sizes, "assembly_transform": "IDENTITY_GLOBAL_REGISTRY_COORDINATES",
        "mounting_faces": candidate_parameters["mounting_faces"],
        "fastener_groups": candidate_parameters["fastener_groups"],
        "hole_centers": candidate_parameters["hole_centers"],
        "hole_diameters": candidate_parameters["hole_diameters"],
        "lower_adapter_interface": next((item for item in attachments if any("LOWER-ADAPTER" in part for part in (item["parent_component"], item["child_component"]))), None),
        "front_crossmember_interface": next((item for item in attachments if any("FPB-FRONT-XMEMBER" in part for part in (item["parent_component"], item["child_component"]))), None),
        "material_candidate": component["status"],
        "load_direction": candidate_parameters["load_directions"],
        "print_orientation_candidate": candidate_parameters["print_orientations"],
        "a1_build_limit_authority": {"X_mm": 232.0, "Y_mm": 232.0, "Z_mm": "MEASUREMENT_REQUIRED", "source": "repository dense-tool --safe"},
        "fixed_parameters": fixed_parameters,
        "candidate_parameters": candidate_parameters,
        "undefined_parameters": undefined_parameters,
        "acceptance_tolerances": build_tolerance_registry(registries),
        "revision_policy": "APPEND_ONLY; revB only after failed revA and minimal correction",
    }

def compare_measurement(inspection_id, design_value, measured_value, tolerance, measurement_method):
    if measurement_method in {"PARAMETER_COPY", "REGISTRY_COPY", "BBOX_SPECIFICATION_COPY"}:
        return {
            "inspection_item": inspection_id, "design_value": design_value,
            "measured_value": measured_value, "tolerance": tolerance,
            "deviation": None, "result": "FAIL",
            "measurement_method": measurement_method,
            "error": "measured value must come from final solid",
        }
    if isinstance(design_value, (list, tuple)):
        deviation = [float(measured_value[index]) - float(design_value[index]) for index in range(len(design_value))]
        magnitude = math.sqrt(sum(value * value for value in deviation))
    else:
        deviation = float(measured_value) - float(design_value)
        magnitude = abs(deviation)
    if tolerance.get("tolerance_type") == "TOLERANCE_MEASUREMENT_REQUIRED":
        result = "CONDITIONAL_HOLD"
    else:
        minimum = tolerance.get("minimum")
        maximum = tolerance.get("maximum")
        if minimum is None or maximum is None:
            result = "FAIL"
        else:
            result = "PASS" if float(minimum) <= float(measured_value) <= float(maximum) else "FAIL"
    return {
        "inspection_item": inspection_id, "design_value": design_value,
        "measured_value": measured_value, "tolerance": tolerance,
        "deviation": deviation, "deviation_magnitude": magnitude,
        "result": result, "measurement_method": measurement_method, "error": "",
    }

def inspect_actual_bbox(final_solid, specification, tolerance_registry):
    measured = shape_bbox(final_solid)
    expected = specification["outer_dimensions_mm"]
    tolerance_map = {item["inspection_id"]: item for item in tolerance_registry}
    rows = []
    for axis, measured_key in (("X", "xlen"), ("Y", "ylen"), ("Z", "zlen")):
        rows.append(compare_measurement(
            f"BBOX_SIZE_{axis}", expected[f"{axis}_mm"], measured[measured_key],
            tolerance_map[f"BBOX_SIZE_{axis}"], "FINAL_SOLID_BOUNDING_BOX",
        ))
    rows.extend([
        {
            "inspection_item": f"BBOX_{key.upper()}", "design_value": None,
            "measured_value": measured[key], "tolerance": None, "deviation": None,
            "result": "MEASURED", "measurement_method": "FINAL_SOLID_BOUNDING_BOX",
        }
        for key in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
    ])
    rows.extend([
        {
            "inspection_item": f"BBOX_CENTER_{axis}", "design_value": None,
            "measured_value": (measured[lower] + measured[upper]) / 2.0,
            "tolerance": None, "deviation": None, "result": "MEASURED",
            "measurement_method": "FINAL_SOLID_BOUNDING_BOX",
        }
        for axis, lower, upper in (
            ("X", "xmin", "xmax"), ("Y", "ymin", "ymax"), ("Z", "zmin", "zmax")
        )
    ])
    hard = sum(row["result"] == "FAIL" for row in rows)
    holds = sum(row["result"] == "CONDITIONAL_HOLD" for row in rows)
    return {
        "rows": rows, "inspection_count": len(rows),
        "hard_failure_count": hard, "hold_count": holds,
        "status": "FAIL" if hard else "CONDITIONAL_HOLD" if holds else "PASS",
    }

def validate_dimension_gate_claim(record):
    errors = []
    if record.get("status") == "PASS":
        rows = record.get("rows", [])
        bbox_rows = [row for row in rows if str(row.get("inspection_item", "")).startswith("BBOX_SIZE_")]
        if len(bbox_rows) != 3:
            errors.append("PASS without three actual bbox size inspections")
        if any(row.get("measurement_method") != "FINAL_SOLID_BOUNDING_BOX" for row in bbox_rows):
            errors.append("PASS bbox not measured from final solid")
        if any(not row.get("tolerance") for row in bbox_rows):
            errors.append("PASS with missing tolerance")
        if record.get("hard_failure_count"):
            errors.append("PASS with hard dimension failure")
        if record.get("hold_count"):
            errors.append("PASS with unresolved dimension hold")
    return errors
