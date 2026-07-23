from __future__ import annotations
import math
from software_renderer import tessellate_shape

ORIENTATIONS = ("ORIGINAL", "ROTATE_X_90", "ROTATE_Y_90", "ROTATE_180")

def _rotate(point, orientation):
    x, y, z = (float(value) for value in point)
    if orientation == "ORIGINAL":
        return (x, y, z)
    if orientation == "ROTATE_X_90":
        return (x, -z, y)
    if orientation == "ROTATE_Y_90":
        return (z, y, -x)
    if orientation == "ROTATE_180":
        return (-x, -y, z)
    raise ValueError(orientation)

def _sub(a, b):
    return tuple(a[index] - b[index] for index in range(3))

def _cross(a, b):
    return (
        a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]
    )

def _triangle_metrics(triangle):
    cross = _cross(_sub(triangle[1], triangle[0]), _sub(triangle[2], triangle[0]))
    length = math.sqrt(sum(value*value for value in cross))
    normal = tuple(value / length for value in cross) if length > 1e-12 else (0.0, 0.0, 0.0)
    area = length / 2.0
    centroid = tuple(sum(point[index] for point in triangle) / 3.0 for index in range(3))
    return normal, area, centroid

def inspect_print_orientations(actual_shape, params, component):
    triangles = tessellate_shape(
        actual_shape, params["renderer"]["tessellation_tolerance_mm"],
        params["renderer"]["angular_tolerance"],
    )
    authority = params["printability"]
    rows = []
    threshold_cos = math.cos(math.radians(float(authority["overhang_support_angle_deg"])))
    for orientation in ORIENTATIONS:
        rotated = [tuple(_rotate(point, orientation) for point in triangle) for triangle in triangles]
        points = [point for triangle in rotated for point in triangle]
        mins = [min(point[index] for point in points) for index in range(3)]
        maxs = [max(point[index] for point in points) for index in range(3)]
        dimensions = [maxs[index] - mins[index] for index in range(3)]
        contact_area = 0.0; downward_area = 0.0; support_area = 0.0
        for triangle in rotated:
            normal, area, centroid = _triangle_metrics(triangle)
            if max(abs(point[2] - mins[2]) for point in triangle) <= authority["bed_plane_tolerance_mm"]:
                contact_area += area * abs(normal[2])
            if normal[2] < -1e-6:
                downward_area += area
            if normal[2] < -threshold_cos and centroid[2] > mins[2] + authority["bed_plane_tolerance_mm"]:
                support_area += area
        x_margin = authority["bambu_a1_safe_x_mm"] - dimensions[0]
        y_margin = authority["bambu_a1_safe_y_mm"] - dimensions[1]
        z_limit = authority["bambu_a1_z_mm"]
        hard_build_failure = x_margin < -1e-9 or y_margin < -1e-9 or (
            z_limit is not None and dimensions[2] > z_limit
        )
        severe_support = support_area > 0.35 * max(sum(_triangle_metrics(item)[1] for item in rotated), 1e-9)
        rows.append({
            "orientation": orientation, "build_bbox_mm": dimensions,
            "build_limit_margin_mm": [x_margin, y_margin, None if z_limit is None else z_limit - dimensions[2]],
            "bed_contact_area_mm2": contact_area, "maximum_z_mm": dimensions[2],
            "downward_overhang_area_mm2": downward_area,
            "support_risk_area_mm2": support_area,
            "overhang_proxy": "SEVERE_SUPPORT_RISK" if severe_support else "SUPPORT_RECOMMENDED" if support_area > 0 else "SAFE",
            "support_removal_proxy": "SUPPORT_TEST_REQUIRED" if support_area > 0 else "NO_SUPPORT_PROXY",
            "hole_axis_orientation": "OPENING_ID_ANALYSIS_REQUIRED",
            "layer_direction_vs_load": "STRUCTURAL_ANALYSIS_HOLD",
            "estimated_print_height_mm": dimensions[2],
            "confirmed_build_volume_failure": hard_build_failure,
            "z_authority_status": "CONFIRMED" if z_limit is not None else "MEASUREMENT_REQUIRED",
            "bed_contact_result": "PASS_PROXY" if contact_area > 0 else "PRINT_STABILITY_HOLD",
            "process_applicability": "PRINT_TARGET" if component.get("print_target") else "METAL_PART_PRINT_PROXY_ONLY",
        })
    viable = [row for row in rows if not row["confirmed_build_volume_failure"]]
    viable.sort(key=lambda row: (
        row["support_risk_area_mm2"], -row["bed_contact_area_mm2"], row["maximum_z_mm"], row["orientation"]
    ))
    selected = viable[0] if viable else None
    confirmed_failure_count = 0 if viable else 1
    holds = 0
    if selected:
        holds += int(selected["z_authority_status"] != "CONFIRMED")
        holds += int(selected["support_removal_proxy"] != "NO_SUPPORT_PROXY")
        holds += int(selected["bed_contact_result"] != "PASS_PROXY")
        holds += int(selected["layer_direction_vs_load"] != "PASS")
        holds += int(selected["process_applicability"] != "PRINT_TARGET")
    status = "FAIL" if confirmed_failure_count else "CONDITIONAL_HOLD" if holds else "PASS_PROXY"
    return {
        "orientation_rows": rows, "candidate_count": len(rows),
        "selected_orientation": selected["orientation"] if selected else None,
        "build_volume_authority": authority["authority"],
        "build_volume_result": "FAIL" if confirmed_failure_count else "CONDITIONAL_HOLD" if selected and selected["z_authority_status"] != "CONFIRMED" else "PASS",
        "overhang_proxy_result": selected["overhang_proxy"] if selected else "NOT_RUN",
        "support_removal_result": selected["support_removal_proxy"] if selected else "NOT_RUN",
        "bed_contact_result": selected["bed_contact_result"] if selected else "NOT_RUN",
        "confirmed_build_volume_failure_count": confirmed_failure_count,
        "print_support_hold_count": holds,
        "status": status,
        "claim": "PRINTABILITY_PROXY_NOT_MANUFACTURING_APPROVAL",
    }

def validate_printability_claim(record):
    errors = []
    if record.get("status") == "PASS_PROXY":
        if record.get("candidate_count", 0) < 4:
            errors.append("PASS_PROXY without orientation comparison")
        if "Z_MEASUREMENT_REQUIRED" in str(record.get("build_volume_authority")):
            errors.append("PASS_PROXY with missing confirmed Z authority")
        if record.get("overhang_proxy_result") in {None, "NOT_RUN"}:
            errors.append("PASS_PROXY without overhang inspection")
        if record.get("support_removal_result") not in {"NO_SUPPORT_PROXY", "PASS_PROXY"}:
            errors.append("PASS_PROXY with unresolved/trapped support")
        if record.get("bed_contact_result") != "PASS_PROXY":
            errors.append("PASS_PROXY without bed contact")
        if record.get("confirmed_build_volume_failure_count"):
            errors.append("PASS_PROXY outside confirmed build volume")
    return errors
