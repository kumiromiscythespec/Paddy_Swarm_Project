from __future__ import annotations
import math
from cad_primitives import shape_value

WALL_METHODS = {
    "DESIGN_OFFSET_CONFIRMED", "SECTION_SAMPLE_MEASURED",
    "RAY_SAMPLE_PROXY", "NOT_MEASURABLE",
}

def _dot(a, b):
    return sum(float(a[index]) * float(b[index]) for index in range(3))

def _normal_tuple(normal):
    return (float(normal.x), float(normal.y), float(normal.z))

def inspect_opposing_planar_thickness(final_solid):
    faces = []
    for index, face in enumerate(shape_value(final_solid).Faces()):
        try:
            if str(face.geomType()).upper() != "PLANE":
                continue
            center = face.Center()
            normal = _normal_tuple(face.normalAt())
            length = math.sqrt(_dot(normal, normal))
            normal = tuple(value / length for value in normal)
            faces.append({
                "face_index": index, "center": (float(center.x), float(center.y), float(center.z)),
                "normal": normal, "area_mm2": float(face.Area()),
            })
        except Exception:
            continue
    samples = []
    for first_index, first in enumerate(faces):
        for second in faces[first_index + 1:]:
            opposition = _dot(first["normal"], second["normal"])
            if opposition > -0.995:
                continue
            center_delta = tuple(second["center"][index] - first["center"][index] for index in range(3))
            distance = abs(_dot(center_delta, first["normal"]))
            tangential = math.sqrt(max(0.0, _dot(center_delta, center_delta) - distance * distance))
            if distance <= 1e-6:
                continue
            samples.append({
                "face_a": first["face_index"], "face_b": second["face_index"],
                "distance_mm": distance, "tangential_center_offset_mm": tangential,
                "minimum_face_area_mm2": min(first["area_mm2"], second["area_mm2"]),
                "normal_opposition": opposition,
            })
    samples.sort(key=lambda item: (item["distance_mm"], -item["minimum_face_area_mm2"]))
    if not samples:
        return {
            "method": "NOT_MEASURABLE", "status": "NOT_RUN",
            "major_plate_thickness_mm": None, "samples": [],
            "claim": "NO_MINIMUM_WALL_CLAIM",
        }
    major_candidates = [
        sample for sample in samples
        if sample["tangential_center_offset_mm"] <= max(0.5, sample["distance_mm"] * 0.1)
    ] or samples
    major = major_candidates[0]
    return {
        "method": "SECTION_SAMPLE_MEASURED",
        "specific_method": "OPPOSING_PLANAR_FACE_DISTANCE",
        "status": "PARTIAL_PROXY",
        "major_plate_thickness_mm": major["distance_mm"],
        "samples": samples,
        "claim": "MAJOR_RAIL_PLATE_SAMPLE_ONLY_NOT_GLOBAL_MINIMUM_WALL",
        "wall_analysis_partial_count": 1,
    }

def validate_wall_claim(record):
    errors = []
    if record.get("method") not in WALL_METHODS:
        errors.append("unrecognized wall inspection method")
    if record.get("claim") in {"ACTUAL_MINIMUM_WALL", "MINIMUM_WALL_PASS"} and record.get("method") != "DESIGN_OFFSET_CONFIRMED":
        errors.append("proxy/sample method cannot claim actual global minimum wall")
    if record.get("status") == "PASS" and record.get("method") in {"RAY_SAMPLE_PROXY", "NOT_MEASURABLE"}:
        errors.append("proxy/unmeasurable wall method cannot PASS")
    return errors
