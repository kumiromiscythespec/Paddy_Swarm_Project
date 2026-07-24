from __future__ import annotations

import math
from typing import Iterable, Mapping

from authority_loader import Envelope
from solid_builders import require_cadquery


def _clean(value: float, tolerance: float = 1.0e-12) -> float:
    result = float(value)
    return 0.0 if abs(result) <= tolerance else result


def bounding_box(shape) -> dict[str, float]:
    box = shape.BoundingBox()
    return {
        "xmin": _clean(box.xmin),
        "xmax": _clean(box.xmax),
        "ymin": _clean(box.ymin),
        "ymax": _clean(box.ymax),
        "zmin": _clean(box.zmin),
        "zmax": _clean(box.zmax),
        "xlen": _clean(box.xlen),
        "ylen": _clean(box.ylen),
        "zlen": _clean(box.zlen),
    }


def inspect_solid(shape, envelope: Envelope, tolerance: float) -> dict:
    cq = require_cadquery()
    expected = {
        "xmin": envelope.minimum[0],
        "xmax": envelope.maximum[0],
        "ymin": envelope.minimum[1],
        "ymax": envelope.maximum[1],
        "zmin": envelope.minimum[2],
        "zmax": envelope.maximum[2],
        "xlen": envelope.dimensions[0],
        "ylen": envelope.dimensions[1],
        "zlen": envelope.dimensions[2],
    }
    shape_type = (
        None if shape is None else f"{type(shape).__module__}.{type(shape).__name__}"
    )
    base = {
        "component_id": envelope.component_id,
        "object_exists": shape is not None,
        "shape_type": shape_type,
        "cadquery_ocp_shape": False,
        "solid_count": None,
        "valid": None,
        "finite": None,
        "volume_mm3": None,
        "bounding_box_mm": None,
        "expected_bounding_box_mm": expected,
        "bounding_box_mismatch_fields": [],
    }
    if shape is None:
        return {**base, "blockers": ["OBJECT_MISSING"], "status": "FAIL"}
    shape_is_cadquery = isinstance(shape, cq.Shape) and hasattr(shape, "wrapped")
    base["cadquery_ocp_shape"] = shape_is_cadquery
    if not shape_is_cadquery:
        return {
            **base,
            "blockers": ["NOT_CADQUERY_OCP_SHAPE"],
            "status": "FAIL",
        }
    required_methods = ("BoundingBox", "Volume", "Solids", "isValid")
    missing_methods = tuple(
        method for method in required_methods if not callable(getattr(shape, method, None))
    )
    if missing_methods:
        return {
            **base,
            "blockers": [
                f"SHAPE_METHOD_MISSING:{method}" for method in missing_methods
            ],
            "status": "FAIL",
        }
    try:
        box = bounding_box(shape)
        volume = float(shape.Volume())
        solid_count = len(shape.Solids())
        valid = bool(shape.isValid())
    except Exception as exc:
        return {
            **base,
            "blockers": [f"SOLID_INSPECTION_FAILED:{type(exc).__name__}"],
            "status": "FAIL",
        }
    mismatches = [
        key
        for key in expected
        if not math.isclose(
            box[key], expected[key], abs_tol=tolerance, rel_tol=0.0
        )
    ]
    finite = all(math.isfinite(value) for value in (*box.values(), volume))
    blockers = []
    if solid_count != 1:
        blockers.append("SOLID_COUNT_NOT_ONE")
    if not valid:
        blockers.append("INVALID_SOLID")
    if not finite:
        blockers.append("NONFINITE_SOLID_RESULT")
    if volume <= 0.0:
        blockers.append("NONPOSITIVE_VOLUME")
    if mismatches:
        blockers.append("BOUNDING_BOX_MISMATCH")
    return {
        **base,
        "solid_count": solid_count,
        "valid": valid,
        "finite": finite,
        "volume_mm3": volume,
        "bounding_box_mm": box,
        "expected_bounding_box_mm": expected,
        "bounding_box_mismatch_fields": mismatches,
        "blockers": blockers,
        "status": "PASS" if not blockers else "FAIL",
    }


def classify_envelope_relation(
    first: Envelope,
    second: Envelope,
    tolerance: float,
) -> dict:
    overlaps = tuple(
        min(first.maximum[index], second.maximum[index])
        - max(first.minimum[index], second.minimum[index])
        for index in range(3)
    )
    if all(value > tolerance for value in overlaps):
        relation = "VOLUME_OVERLAP"
    elif any(value < -tolerance for value in overlaps):
        relation = "SEPARATED"
    elif (
        sum(abs(value) <= tolerance for value in overlaps) == 1
        and sum(value > tolerance for value in overlaps) == 2
    ):
        relation = "FACE_CONTACT"
    else:
        relation = "EDGE_OR_POINT_CONTACT"
    return {
        "first": first.component_id,
        "second": second.component_id,
        "axis_overlap_mm": overlaps,
        "relation": relation,
    }


def actual_intersection_volume(first_shape, second_shape) -> dict:
    try:
        volume = float(first_shape.intersect(second_shape).Volume())
    except Exception as exc:
        return {
            "intersection_operation_status": "FAIL",
            "intersection_error_type": type(exc).__name__,
            "actual_intersection_volume_mm3": None,
        }
    if not math.isfinite(volume):
        return {
            "intersection_operation_status": "FAIL",
            "intersection_error_type": "NONFINITE_INTERSECTION_VOLUME",
            "actual_intersection_volume_mm3": None,
        }
    if volume < 0.0:
        return {
            "intersection_operation_status": "FAIL",
            "intersection_error_type": "NEGATIVE_INTERSECTION_VOLUME",
            "actual_intersection_volume_mm3": volume,
        }
    return {
        "intersection_operation_status": "PASS",
        "intersection_error_type": None,
        "actual_intersection_volume_mm3": _clean(volume),
    }


def inspect_pair(
    first_envelope: Envelope,
    second_envelope: Envelope,
    first_shape,
    second_shape,
    linear_tolerance_mm: float,
    intersection_volume_tolerance_mm3: float,
    expected_relation: str,
) -> dict:
    relation = classify_envelope_relation(
        first_envelope, second_envelope, linear_tolerance_mm
    )
    operation = actual_intersection_volume(first_shape, second_shape)
    intersection_volume = operation["actual_intersection_volume_mm3"]
    failure_blocker = (
        "INTERSECTION_BOOLEAN_FAILED:"
        f"{first_envelope.component_id}:{second_envelope.component_id}"
    )
    if operation["intersection_operation_status"] != "PASS":
        relation.update(
            {
                **operation,
                "expected_relation": expected_relation,
                "unintended_volumetric_intersection": None,
                "blockers": [failure_blocker],
                "status": "FAIL",
            }
        )
        return relation
    unintended_intersection = (
        intersection_volume > intersection_volume_tolerance_mm3
    )
    pair_blockers = []
    if unintended_intersection and expected_relation != "VOLUME_OVERLAP":
        pair_blockers.append(
            "UNINTENDED_VOLUMETRIC_INTERSECTION:"
            f"{first_envelope.component_id}:{second_envelope.component_id}"
        )
    if relation["relation"] != expected_relation:
        pair_blockers.append(
            "PAIR_RELATION_MISMATCH:"
            f"{first_envelope.component_id}:{second_envelope.component_id}"
        )
    relation.update(
        {
            **operation,
            "expected_relation": expected_relation,
            "unintended_volumetric_intersection": unintended_intersection,
            "blockers": pair_blockers,
            "status": (
                "PASS"
                if relation["relation"] == expected_relation
                and not (
                    expected_relation != "VOLUME_OVERLAP"
                    and unintended_intersection
                )
                else "FAIL"
            ),
        }
    )
    return relation


def inspect_mirror(
    left: Envelope,
    right: Envelope,
    tolerance: float,
) -> dict:
    expected_right_min = (
        -left.maximum[0],
        left.minimum[1],
        left.minimum[2],
    )
    expected_right_max = (
        -left.minimum[0],
        left.maximum[1],
        left.maximum[2],
    )
    deviations = tuple(
        right.minimum[index] - expected_right_min[index]
        for index in range(3)
    ) + tuple(
        right.maximum[index] - expected_right_max[index]
        for index in range(3)
    )
    passed = all(abs(value) <= tolerance for value in deviations)
    return {
        "plane": "X=0",
        "left_component": left.component_id,
        "right_component": right.component_id,
        "expected_right_minimum": expected_right_min,
        "expected_right_maximum": expected_right_max,
        "actual_right_minimum": right.minimum,
        "actual_right_maximum": right.maximum,
        "deviations_mm": deviations,
        "status": "PASS" if passed else "FAIL",
    }


def union_bounds(envelopes: Iterable[Envelope]) -> dict[str, float]:
    values = tuple(envelopes)
    minimum = tuple(min(item.minimum[index] for item in values) for index in range(3))
    maximum = tuple(max(item.maximum[index] for item in values) for index in range(3))
    return {
        "xmin": minimum[0],
        "xmax": maximum[0],
        "ymin": minimum[1],
        "ymax": maximum[1],
        "zmin": minimum[2],
        "zmax": maximum[2],
        "xlen": maximum[0] - minimum[0],
        "ylen": maximum[1] - minimum[1],
        "zlen": maximum[2] - minimum[2],
    }


def inspect_all_solids(
    solids: Mapping[str, object],
    envelopes: Iterable[Envelope],
    tolerance: float,
) -> list[dict]:
    return [
        inspect_solid(solids.get(envelope.component_id), envelope, tolerance)
        for envelope in envelopes
    ]
