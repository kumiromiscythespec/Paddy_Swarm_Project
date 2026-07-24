from __future__ import annotations

PROCESS_CLASSES = {
    "METAL_PART_CAD_VALIDATION", "PRINT_PART_CLOSED_LOOP",
    "PURCHASED_PART_ENVELOPE_VALIDATION",
    "REFERENCE_DATUM_VALIDATION",
    "NONPRINT_STRUCTURAL_INTERFACE_VALIDATION",
}

def classify_part_process(component):
    if component.get("part_id") == "V2292-FPB-RAIL-L":
        return {
            "part_id": component["part_id"],
            "part_process_class": "METAL_PART_CAD_VALIDATION",
            "print_target": False,
            "production_print_stl_status":
                "NOT_APPLICABLE_METAL_CANDIDATE",
            "visualization_stl_role":
                "VISUALIZATION_AND_GEOMETRY_COMPARISON_ONLY",
        }
    if component.get("part_id") == "V2292-MOTOR-COVER-L":
        return {
            "part_id": component["part_id"],
            "part_process_class": "PRINT_PART_CLOSED_LOOP",
            "print_target": True,
            "loop_status": "PLANNED_BLOCKED_BY_LOOP_001",
        }
    if component.get("classification") == "MECHANICAL_PLACEHOLDER":
        process = "PURCHASED_PART_ENVELOPE_VALIDATION"
    elif component.get("classification") == "STRUCTURAL":
        process = "NONPRINT_STRUCTURAL_INTERFACE_VALIDATION"
    else:
        process = "REFERENCE_DATUM_VALIDATION"
    return {
        "part_id": component.get("part_id"),
        "part_process_class": process,
        "print_target": bool(component.get("print_target")),
    }

def validate_process_claim(record):
    errors = []
    if (
        record.get("part_process_class") == "METAL_PART_CAD_VALIDATION"
        and record.get("production_print_stl_status")
        != "NOT_APPLICABLE_METAL_CANDIDATE"
    ):
        errors.append("metal candidate cannot receive production print STL approval")
    if (
        record.get("part_id") == "V2292-FPB-RAIL-L"
        and record.get("print_target") is not False
    ):
        errors.append("LOOP-001 rail is not a print target")
    return errors
