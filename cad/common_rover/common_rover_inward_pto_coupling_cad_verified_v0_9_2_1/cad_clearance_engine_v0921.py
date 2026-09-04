#!/usr/bin/env python3
"""Actual CadQuery/OCP clearance calculations for Common Rover v0.9.2.1."""

from __future__ import annotations

import math
from typing import Any, Iterable

import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape


CAD_NUMERICAL_DISTANCE_TOLERANCE_MM = 0.05
CAD_INTERSECTION_VOLUME_TOLERANCE_MM3 = 0.01
FULL_SWEEP_SAMPLE_INTERVAL_MM = 0.5


def compute_intersection_shape(shape_a: cq.Shape, shape_b: cq.Shape) -> cq.Shape:
    """Return the actual Boolean common shape; errors propagate."""
    return shape_a.intersect(shape_b)


def compute_intersection_volume(shape_a: cq.Shape, shape_b: cq.Shape) -> float:
    """Return actual Boolean common volume in mm³; errors propagate."""
    common = compute_intersection_shape(shape_a, shape_b)
    return float(common.Volume())


def compute_intersection_solid_count(
    shape_a: cq.Shape,
    shape_b: cq.Shape,
) -> int:
    """Return solid count in the actual Boolean common shape."""
    common = compute_intersection_shape(shape_a, shape_b)
    return len(common.Solids())


def compute_minimum_distance(shape_a: cq.Shape, shape_b: cq.Shape) -> float:
    """Return exact-kernel minimum distance using OCP BRepExtrema."""
    solver = BRepExtrema_DistShapeShape(shape_a.wrapped, shape_b.wrapped)
    solver.Perform()
    if not solver.IsDone() or solver.NbSolution() < 1:
        raise RuntimeError("OCP distance solver returned no solution")
    distance = float(solver.Value())
    if not math.isfinite(distance):
        raise RuntimeError(f"non-finite OCP distance: {distance}")
    return distance


def compute_nearest_points(
    shape_a: cq.Shape,
    shape_b: cq.Shape,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return one stable nearest-point pair from OCP BRepExtrema."""
    solver = BRepExtrema_DistShapeShape(shape_a.wrapped, shape_b.wrapped)
    solver.Perform()
    if not solver.IsDone() or solver.NbSolution() < 1:
        raise RuntimeError("OCP nearest-point solver returned no solution")
    point_a = solver.PointOnShape1(1)
    point_b = solver.PointOnShape2(1)
    return (
        (float(point_a.X()), float(point_a.Y()), float(point_a.Z())),
        (float(point_b.X()), float(point_b.Y()), float(point_b.Z())),
    )


def classify_contact(
    intersection_volume_mm3: float,
    minimum_distance_mm: float,
    *,
    distance_tolerance_mm: float = CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
    volume_tolerance_mm3: float = CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
) -> str:
    if intersection_volume_mm3 > volume_tolerance_mm3:
        return "INTERSECT"
    if minimum_distance_mm <= distance_tolerance_mm:
        return "CONTACT"
    return "CLEAR"


def evaluate_required_clearance(
    classification: str,
    minimum_distance_mm: float,
    required_clearance_mm: float,
    *,
    distance_tolerance_mm: float = CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
) -> str:
    if classification == "INTERSECT":
        return "FAIL"
    return (
        "PASS"
        if minimum_distance_mm + distance_tolerance_mm >= required_clearance_mm
        else "FAIL"
    )


def _rounded_point(point: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 6) for value in point)


def build_pair_result(
    pair_id: str,
    shape_a_name: str,
    shape_a: cq.Shape,
    shape_b_name: str,
    shape_b: cq.Shape,
    coupling_state: str,
    required_clearance_mm: float,
    note: str,
    *,
    distance_tolerance_mm: float = CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
    volume_tolerance_mm3: float = CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
    sample_position_mm: float | None = None,
) -> dict[str, Any]:
    """Calculate one pair. Errors are returned as ERROR, never PASS."""
    base: dict[str, Any] = {
        "pair_id": pair_id,
        "shape_a_name": shape_a_name,
        "shape_b_name": shape_b_name,
        "coupling_state": coupling_state,
        "sample_position_mm": sample_position_mm,
        "numerical_distance_tolerance_mm": distance_tolerance_mm,
        "intersection_volume_tolerance_mm3": volume_tolerance_mm3,
        "required_clearance_mm": required_clearance_mm,
        "note": note,
        "calculation_api": (
            "CadQuery.Shape.intersect+Volume;"
            "OCP.BRepExtrema_DistShapeShape"
        ),
    }
    try:
        volume = compute_intersection_volume(shape_a, shape_b)
        solid_count = compute_intersection_solid_count(shape_a, shape_b)
        distance = compute_minimum_distance(shape_a, shape_b)
        nearest_a, nearest_b = compute_nearest_points(shape_a, shape_b)
        classification = classify_contact(
            volume,
            distance,
            distance_tolerance_mm=distance_tolerance_mm,
            volume_tolerance_mm3=volume_tolerance_mm3,
        )
        result = evaluate_required_clearance(
            classification,
            distance,
            required_clearance_mm,
            distance_tolerance_mm=distance_tolerance_mm,
        )
        return {
            **base,
            "intersection_volume_mm3": round(volume, 9),
            "intersection_solid_count": solid_count,
            "minimum_distance_mm": round(distance, 9),
            "nearest_point_a_x": _rounded_point(nearest_a)[0],
            "nearest_point_a_y": _rounded_point(nearest_a)[1],
            "nearest_point_a_z": _rounded_point(nearest_a)[2],
            "nearest_point_b_x": _rounded_point(nearest_b)[0],
            "nearest_point_b_y": _rounded_point(nearest_b)[1],
            "nearest_point_b_z": _rounded_point(nearest_b)[2],
            "classification": classification,
            "result": result,
            "error": "",
        }
    except Exception as exc:
        return {
            **base,
            "intersection_volume_mm3": None,
            "intersection_solid_count": None,
            "minimum_distance_mm": None,
            "nearest_point_a_x": None,
            "nearest_point_a_y": None,
            "nearest_point_a_z": None,
            "nearest_point_b_x": None,
            "nearest_point_b_y": None,
            "nearest_point_b_z": None,
            "classification": "ERROR",
            "result": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _box(
    x_size: float,
    y_size: float,
    z_size: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .box(x_size, y_size, z_size)
        .translate(cq.Vector(*center))
        .val()
    )


def _cylinder_y(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    x, y, z = center
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(x, y - length / 2.0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def _annulus_y(
    outer_radius: float,
    inner_radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    return _cylinder_y(outer_radius, length, center).cut(
        _cylinder_y(inner_radius, length + 2.0, center)
    )


def run_canary_tests() -> list[dict[str, Any]]:
    """Run known-geometry tests of the actual clearance engine."""
    cube_a = _box(10.0, 10.0, 10.0, (0.0, 0.0, 0.0))
    cases: list[dict[str, Any]] = []

    overlap = build_pair_result(
        "CANARY_OVERLAP",
        "CUBE_A",
        cube_a,
        "CUBE_B_OVERLAP",
        _box(10.0, 10.0, 10.0, (5.0, 0.0, 0.0)),
        "CANARY",
        0.0,
        "10mm cubes overlap by 5mm",
    )
    overlap["expected"] = "INTERSECT"
    overlap["canary_pass"] = (
        overlap["classification"] == "INTERSECT"
        and float(overlap["intersection_volume_mm3"] or 0.0) > 0.0
    )
    cases.append(overlap)

    touch = build_pair_result(
        "CANARY_TOUCH",
        "CUBE_A",
        cube_a,
        "CUBE_B_TOUCH",
        _box(10.0, 10.0, 10.0, (10.0, 0.0, 0.0)),
        "CANARY",
        0.0,
        "10mm cubes share one face",
    )
    touch["expected"] = "CONTACT"
    touch["canary_pass"] = (
        touch["classification"] == "CONTACT"
        and touch["minimum_distance_mm"] is not None
        and float(touch["minimum_distance_mm"]) <= 0.05
    )
    cases.append(touch)

    for gap in (5.0, 10.0):
        row = build_pair_result(
            f"CANARY_GAP_{int(gap)}",
            "CUBE_A",
            cube_a,
            f"CUBE_B_GAP_{int(gap)}",
            _box(10.0, 10.0, 10.0, (10.0 + gap, 0.0, 0.0)),
            "CANARY",
            gap,
            f"known cube gap {gap:g}mm",
        )
        row["expected"] = "CLEAR"
        row["canary_pass"] = (
            row["classification"] == "CLEAR"
            and abs(float(row["minimum_distance_mm"]) - gap) <= 1.0e-6
            and row["result"] == "PASS"
        )
        cases.append(row)

    shaft = _cylinder_y(5.0, 20.0, (0.0, 0.0, 0.0))
    coupling_annulus = _annulus_y(10.0, 6.0, 20.0, (0.0, 0.0, 0.0))
    coaxial = build_pair_result(
        "CANARY_CYLINDER_SHAFT",
        "SHAFT_OD10",
        shaft,
        "COUPLING_ANNULUS_OD20_BORE12",
        coupling_annulus,
        "CANARY",
        1.0,
        "coaxial shaft-to-bore radial clearance",
    )
    coaxial["expected"] = "CLEAR"
    coaxial["canary_pass"] = (
        coaxial["classification"] == "CLEAR"
        and abs(float(coaxial["minimum_distance_mm"]) - 1.0) <= 1.0e-6
        and float(coaxial["intersection_volume_mm3"]) <= 0.01
        and coaxial["result"] == "PASS"
    )
    cases.append(coaxial)

    obstacle = _box(2.0, 2.0, 2.0, (0.0, 5.0, 0.0))
    sweep_samples = []
    for index in range(21):
        travel = index * FULL_SWEEP_SAMPLE_INTERVAL_MM
        mover = _box(2.0, 2.0, 2.0, (0.0, travel, 0.0))
        sweep_samples.append(build_pair_result(
            f"CANARY_SWEEP_{index:02d}",
            "SWEEP_MOVER",
            mover,
            "SWEEP_OBSTACLE",
            obstacle,
            "FULL_SWEEP",
            0.0,
            "0.5mm sampled collision canary",
            sample_position_mm=travel,
        ))
    first_collision = next(
        (
            row for row in sweep_samples
            if row["classification"] == "INTERSECT"
        ),
        None,
    )
    sweep = {
        "pair_id": "CANARY_SWEEP_COLLISION",
        "shape_a_name": "SWEEP_MOVER",
        "shape_b_name": "SWEEP_OBSTACLE",
        "coupling_state": "FULL_SWEEP",
        "sample_position_mm": (
            first_collision["sample_position_mm"] if first_collision else None
        ),
        "intersection_volume_mm3": (
            max(float(row["intersection_volume_mm3"] or 0.0) for row in sweep_samples)
        ),
        "intersection_solid_count": (
            max(int(row["intersection_solid_count"] or 0) for row in sweep_samples)
        ),
        "minimum_distance_mm": min(
            float(row["minimum_distance_mm"])
            for row in sweep_samples
            if row["minimum_distance_mm"] is not None
        ),
        "nearest_point_a_x": first_collision["nearest_point_a_x"] if first_collision else None,
        "nearest_point_a_y": first_collision["nearest_point_a_y"] if first_collision else None,
        "nearest_point_a_z": first_collision["nearest_point_a_z"] if first_collision else None,
        "nearest_point_b_x": first_collision["nearest_point_b_x"] if first_collision else None,
        "nearest_point_b_y": first_collision["nearest_point_b_y"] if first_collision else None,
        "nearest_point_b_z": first_collision["nearest_point_b_z"] if first_collision else None,
        "numerical_distance_tolerance_mm": CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
        "intersection_volume_tolerance_mm3": CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
        "required_clearance_mm": 0.0,
        "classification": "INTERSECT" if first_collision else "ERROR",
        "result": "PASS" if first_collision else "ERROR",
        "note": "sampled at 0.5mm; collision must be detected",
        "calculation_api": "CadQuery actual sampled shapes",
        "error": "" if first_collision else "collision not detected",
        "expected": "INTERSECT_DURING_SWEEP",
        "canary_pass": first_collision is not None,
    }
    cases.append(sweep)
    return cases


def summarize_pair_results(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    valid_distance = [
        row for row in rows
        if row.get("minimum_distance_mm") is not None
    ]
    valid_volume = [
        row for row in rows
        if row.get("intersection_volume_mm3") is not None
    ]
    minimum = min(
        valid_distance,
        key=lambda row: float(row["minimum_distance_mm"]),
        default=None,
    )
    maximum = max(
        valid_volume,
        key=lambda row: float(row["intersection_volume_mm3"]),
        default=None,
    )
    return {
        "total_pairs_tested": len(rows),
        "total_states": len({row["coupling_state"] for row in rows}),
        "total_intersect": sum(row["classification"] == "INTERSECT" for row in rows),
        "total_contact": sum(row["classification"] == "CONTACT" for row in rows),
        "total_clear": sum(row["classification"] == "CLEAR" for row in rows),
        "total_pass": sum(row["result"] == "PASS" for row in rows),
        "total_fail": sum(row["result"] == "FAIL" for row in rows),
        "total_error": sum(row["result"] == "ERROR" for row in rows),
        "minimum_clearance_overall_mm": (
            minimum["minimum_distance_mm"] if minimum else None
        ),
        "minimum_clearance_pair": minimum["pair_id"] if minimum else None,
        "minimum_clearance_state": minimum["coupling_state"] if minimum else None,
        "minimum_clearance_position_mm": (
            minimum.get("sample_position_mm") if minimum else None
        ),
        "maximum_intersection_volume_mm3": (
            maximum["intersection_volume_mm3"] if maximum else None
        ),
        "worst_intersection_pair": maximum["pair_id"] if maximum else None,
    }
