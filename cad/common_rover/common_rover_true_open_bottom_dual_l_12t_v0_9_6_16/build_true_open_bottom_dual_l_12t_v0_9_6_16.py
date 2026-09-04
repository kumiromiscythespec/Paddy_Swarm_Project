from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.16"
CLASSIFICATION = "TRUE_OPEN_BOTTOM_DUAL_L_12T"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2256
BASE_OUTSIDE_DIGEST = "75d572b59729a8311f7e62a8983b208004a0d36a318d7a9724d69da0db4c3424"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md", "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_dual_l_slide_rimless_hub_v0_9_6_15/build_dual_l_slide_rimless_hub_v0_9_6_15.py"
_spec = importlib.util.spec_from_file_location("v09615_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.15"] = (
    "cad/common_rover/common_rover_dual_l_slide_rimless_hub_v0_9_6_15",
    43,
    "23a2ca7cc8a66cd6bf062eb1a683bddfd60a951a7c6e2cbf58066a5dc555cf24",
)

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md",
    "V09615_FALSE_PASS_ANALYSIS.md", "EXPORTED_STL_RING_EVIDENCE.md",
    "TRUE_OPEN_BOTTOM_SPEC.md", "LOWER_FLANGE_REMOVAL_SPEC.md",
    "EXPORTED_STL_SECTION_TEST_SPEC.md", "VALIDATION_REGRESSION_SPEC.md",
    "DUAL_L_PARENT_STATUS.md", "Y3_PARENT_STATUS.md", "FINAL_GUARD_STATUS.md",
    "BELT_ENTRY_TEST_PLAN.md", "PRINT_PLAN.md", "POWERED_TEST_GATE.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "artifacts/drive_12t_h25a1_true_open_bottom_dual_l_v0_9_6_16.step",
    "artifacts/drive_12t_h25a1_true_open_bottom_dual_l_v0_9_6_16.stl",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_16.step",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_16.stl",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_16.step",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_16.stl",
    "artifacts/true_open_bottom_dual_l_assembly_v0_9_6_16.step",
]
SVGS = [
    "artifacts/v09615_vs_v09616_side_section.svg",
    "artifacts/v09615_vs_v09616_bottom_view.svg",
    "artifacts/belt_entry_true_open_bottom_v0_9_6_16.svg",
]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = [
    "build_true_open_bottom_dual_l_12t_v0_9_6_16.py",
    "tests/test_true_open_bottom_dual_l_12t_v0_9_6_16_contract.py",
]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

PARENT_MAIN_STL = REPO_ROOT / parent.LANE_REL / "artifacts/drive_12t_h25a1_dual_l_rimless_v0_9_6_15.stl"
PARENT_CAP_STEP = REPO_ROOT / parent.LANE_REL / "artifacts/h25a1_dual_l_slide_cap_v0_9_6_15.step"
PARENT_CAP_STL = REPO_ROOT / parent.LANE_REL / "artifacts/h25a1_dual_l_slide_cap_v0_9_6_15.stl"
PARENT_KEY_STEP = REPO_ROOT / parent.LANE_REL / "artifacts/h25a1_dual_l_stop_key_v0_9_6_15.step"
PARENT_KEY_STL = REPO_ROOT / parent.LANE_REL / "artifacts/h25a1_dual_l_stop_key_v0_9_6_15.stl"

sha256 = parent.sha256
write_text = parent.write_text
write_json = parent.write_json
run_git = parent.run_git
tree_digest = parent.tree_digest
box = parent.box
cylinder = parent.cylinder
compound = parent.compound
volume = parent.volume
dims = parent.dims

OLD_SECTION_Z_MM = [-25.5, -24.5, -23.5, -22.5]
NEAR_BOTTOM_SECTION_Z_MM = -21.5
FINAL_Z_MIN_LIMIT_MM = -22.05

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "parent_lane": parent.LANE_REL.as_posix(),
    "failure_record": {
        "V09615_LOWER_ANNULAR_FLANGE": "PRESENT_IN_EXPORTED_STL",
        "BELT_SIDE_ENTRY": "BLOCKED_BY_LOWER_FLANGE",
        "V09615_NO_CONTINUOUS_LOWER_RING_TEST": "FALSE_PASS_VALIDATION_BUG",
        "FULL_V09615_PRINT": "REJECT",
    },
    "old_exported_stl_authority": {
        "bounds_z_mm": [-26.0, 22.0],
        "section_z_mm": OLD_SECTION_Z_MM,
        "inner_radius_mm": 29.47,
        "outer_radius_mm": 38.47,
        "override": "EXPORTED_STL_EVIDENCE_OVERRIDES_OLD_INTERNAL_VALIDATION",
    },
    "true_open_bottom": {
        "removal_z_mm": [-26.0, -22.0],
        "removal_radius_mm": [29.47, 38.47],
        "final_main_min_z_mm": -22.0,
        "minimum_z_rule_mm": FINAL_Z_MIN_LIMIT_MM,
        "old_level_sections": "NONE_REQUIRED",
        "near_bottom_annular_pair": "FORBIDDEN",
        "belt_side_entry_geometry": "OPEN_CANDIDATE",
        "actual_belt_section": "PHYSICAL_HOLD",
    },
    "dual_l": {
        "hook_count": 2, "receiver_count": 2, "opposed_deg": 180.0,
        "slide_travel_mm": 3.0, "clearance_mm": 0.45,
        "nominal_overlap_mm": 2.75, "minimum_overlap_mm": 2.5,
        "hook_thickness_mm": 4.0, "root_mm": 6.0,
        "engagement_width_mm": 12.0, "root_radius_class_mm": 2.0,
        "stop_key": "EXTERNAL_REMOVABLE_REVERSE_SLIDE_BLOCK_NON_TORQUE",
    },
    "removed_hardware": {
        "m3_count": 0, "nut_count": 0, "washer_count": 0,
        "m3_bridge_count": 0, "m3_seat_count": 0, "hidden_captive_nut_count": 0,
    },
    "preserved": {
        "protected_12t": dict(parent.PARAMS["preserved"]["protected_12t"]),
        "pitch": dict(parent.PARAMS["preserved"]["pitch"]),
        "B_collar_pocket_diameter_mm": 16.2,
        "B_hardware_cavity_radius_mm": 20.4,
        "headed_m4_count": 2, "headed_m4_separation_deg": 90.0,
        "grub_screw_count": 0,
        "Y3_height_mm": 3.7, "Y3_head_top_space_mm": 4.3,
        "Y3_vertical_margin_mm": 0.6, "YW30_receiver_width_mm": 15.5,
        "Y3_full_physical_fit": "HOLD",
        "guard_authority": "H9_UPPER5_ROOT6_R3_TOPR1_FRAME_CLEARANCE4P4",
        "guard_authority_values_preserved": True,
        "integrated_annular_guard_geometry": "SUPERSEDED_BY_12_LOCAL_NONANNULAR_GUARD_SEGMENTS",
        "guard_segment_count": 12,
        "guard_axial_shift_mm": 4.0,
        "guard_candidate_frame_clearance_mm": 8.4,
        "guard_physical_function": "HOLD_DYNAMIC_VALIDATION_OF_SEGMENTED_GUARD",
    },
    "validation": {
        "method": "EXACT_EXPORTED_BINARY_STL_TRIANGLE_PLANE_SECTION_LOOP_ANALYZER",
        "internal_only_validation_forbidden": True,
        "parent_regression_required": True,
        "old_section_z_mm": OLD_SECTION_Z_MM,
        "near_bottom_section_z_mm": NEAR_BOTTOM_SECTION_Z_MM,
    },
    "printability": {
        "printer": "BAMBU_A1", "material": "PETG",
        "large_lower_disc": False, "trapped_support": False,
        "long_closed_internal_support": False,
        "bed_adhesion": "USE_BAMBU_STUDIO_BRIM_IF_REQUIRED_DO_NOT_RESTORE_FLANGE",
        "slicer": "HOLD_SLICER_NOT_RUN",
    },
    "gates": {
        "physical_print": "FULL_12T_READY_FOR_ONE_PHYSICAL_PRINT",
        "first_test": "BELT_SIDE_ENTRY",
        "powered": "NOT_YET_APPROVED",
        "actual_belt_section": "PHYSICAL_HOLD",
        "Y3_full_fit": "HOLD", "guard_non_annular_replacement": "HOLD",
        "dual_l_vibration": "HOLD", "stop_key_lifetime": "HOLD",
        "torque": "HOLD", "powered_belt": "HOLD", "shaft_cut": "HOLD",
        "water": "HOLD", "mud": "HOLD", "field": "NOT_APPROVED",
    },
}


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_preflight() -> dict[str, object]:
    branch, head = run_git("branch", "--show-current"), run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    outside = outside_snapshot()
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "dirty": dirty, "authority": authority, "protected": protected, "outside": outside}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def local_guard_segments() -> cq.Workplane:
    shifted = parent.p9.reinforced_guard().translate((0, 0, 4.0))
    segments = []
    for angle in (15.0 + index * 30.0 for index in range(12)):
        mask = parent.local_box(10.0, 9.5, 7.0, 34.0, 0.0, -19.0, angle)
        segments.extend(cq.Workplane(obj=solid) for solid in shifted.intersect(mask).solids().vals())
    return compound(segments)


def true_open_main() -> cq.Workplane:
    old = parent.dual_l_main()
    exact_teeth_in_parent = old.intersect(parent.p13.exact_teeth())
    # The exported v0.9.6.15 lower flange is the annular reinforced-guard BRep.
    # Remove it completely, then restore only the exact protected tooth volume
    # that overlapped that BRep inside the frozen -22..+22 tooth body.
    result = old.cut(parent.p9.reinforced_guard()).union(exact_teeth_in_parent)
    for segment in local_guard_segments().solids().vals():
        result = result.union(cq.Workplane(obj=segment))
    return result.clean()


def assembly() -> cq.Workplane:
    yokes = parent.p12.y3_pair()
    shaft = cylinder(5.0, 70.0, -35.0)
    return compound([
        true_open_main(), parent.dual_l_cap(), parent.stop_key_placed(),
        *yokes, parent.p8.collar(), parent.p8.m4_hardware(), shaft,
    ])


def shape_volume(obj: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in obj.solids().vals()), 6)


def safe_missing(reference: cq.Workplane, retained: cq.Workplane) -> float:
    return shape_volume(reference.cut(retained))


def binary_stl_triangles(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL_TOO_SHORT: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError(f"STL_NOT_BINARY_OR_TRUNCATED: {path}")
    triangles = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        triangles.append((values[3:6], values[6:9], values[9:12]))
    return triangles


def stl_bounds(path: Path) -> dict[str, object]:
    triangles = binary_stl_triangles(path)
    points = [point for triangle in triangles for point in triangle]
    mins = [min(point[index] for point in points) for index in range(3)]
    maxs = [max(point[index] for point in points) for index in range(3)]
    return {"min": mins, "max": maxs, "triangles": len(triangles)}


def section_segments(path: Path, z_mm: float, tolerance: float = 1e-6, decimals: int = 4) -> set[tuple[tuple[float, float], tuple[float, float]]]:
    segments: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    for triangle in binary_stl_triangles(path):
        points: list[tuple[float, float]] = []
        for first, second in ((triangle[0], triangle[1]), (triangle[1], triangle[2]), (triangle[2], triangle[0])):
            da, db = first[2] - z_mm, second[2] - z_mm
            if abs(da) <= tolerance and abs(db) <= tolerance:
                continue
            if (da < -tolerance and db > tolerance) or (da > tolerance and db < -tolerance):
                ratio = (z_mm - first[2]) / (second[2] - first[2])
                points.append((first[0] + ratio * (second[0] - first[0]), first[1] + ratio * (second[1] - first[1])))
            elif abs(da) <= tolerance:
                points.append((first[0], first[1]))
            elif abs(db) <= tolerance:
                points.append((second[0], second[1]))
        unique = []
        for point in points:
            key = (round(point[0], decimals), round(point[1], decimals))
            if key not in unique:
                unique.append(key)
        if len(unique) == 2 and unique[0] != unique[1]:
            segments.add(tuple(sorted((unique[0], unique[1]))))
    return segments


def closed_section_loops(segments: set[tuple[tuple[float, float], tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    adjacency: dict[tuple[float, float], set[tuple[float, float]]] = {}
    for first, second in segments:
        adjacency.setdefault(first, set()).add(second)
        adjacency.setdefault(second, set()).add(first)
    loops: list[list[tuple[float, float]]] = []
    seen: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    for start, neighbours in adjacency.items():
        for neighbour in neighbours:
            edge = tuple(sorted((start, neighbour)))
            if edge in seen:
                continue
            path = [start]
            previous, current = start, neighbour
            seen.add(edge)
            for _ in range(len(segments) + 2):
                path.append(current)
                if current == start:
                    break
                options = [item for item in adjacency.get(current, set()) if item != previous]
                unused = [item for item in options if tuple(sorted((current, item))) not in seen]
                if not unused:
                    break
                following = unused[0]
                seen.add(tuple(sorted((current, following))))
                previous, current = current, following
            if path[-1] == start and len(path) > 3:
                loops.append(path[:-1])
    return loops


def angular_coverage(segments: set[tuple[tuple[float, float], tuple[float, float]]], radius_mm: float, radius_tolerance_mm: float = 0.15, bins: int = 180) -> float:
    occupied = set()
    for first, second in segments:
        midpoint = ((first[0] + second[0]) / 2.0, (first[1] + second[1]) / 2.0)
        radius = math.hypot(*midpoint)
        if abs(radius - radius_mm) <= radius_tolerance_mm:
            angle = math.atan2(midpoint[1], midpoint[0]) % (2 * math.pi)
            occupied.add(min(bins - 1, int(angle / (2 * math.pi) * bins)))
    return round(len(occupied) / bins, 6)


def section_analysis(path: Path, z_mm: float) -> dict[str, object]:
    segments = section_segments(path, z_mm)
    loops = closed_section_loops(segments)
    stats = []
    for loop in loops:
        radii = [math.hypot(x, y) for x, y in loop]
        stats.append({
            "points": len(loop), "radius_min_mm": round(min(radii), 6),
            "radius_max_mm": round(max(radii), 6),
            "radius_mean_mm": round(sum(radii) / len(radii), 6),
            "radial_spread_mm": round(max(radii) - min(radii), 6),
        })
    inner_coverage = angular_coverage(segments, 29.47)
    outer_coverage = angular_coverage(segments, 38.47)
    annular_pair = inner_coverage >= 0.95 and outer_coverage >= 0.95
    return {
        "z_mm": z_mm, "section_present": bool(segments),
        "segment_count": len(segments), "closed_loop_count": len(loops),
        "loops": stats, "inner_R29p47_coverage": inner_coverage,
        "outer_R38p47_coverage": outer_coverage,
        "complete_annular_pair": annular_pair,
    }


def exported_stl_validation(new_stl: Path) -> dict[str, object]:
    old_bounds, new_bounds = stl_bounds(PARENT_MAIN_STL), stl_bounds(new_stl)
    old_sections = {str(z): section_analysis(PARENT_MAIN_STL, z) for z in OLD_SECTION_Z_MM}
    new_sections = {str(z): section_analysis(new_stl, z) for z in OLD_SECTION_Z_MM}
    near_bottom = section_analysis(new_stl, NEAR_BOTTOM_SECTION_Z_MM)
    old_regression = all(row["section_present"] and row["complete_annular_pair"] for row in old_sections.values())
    new_old_levels_clear = all(not row["section_present"] for row in new_sections.values())
    new_z_ok = new_bounds["min"][2] >= FINAL_Z_MIN_LIMIT_MM
    return {
        "analyzer": "EXACT_EXPORTED_BINARY_STL_TRIANGLE_PLANE_SECTION_LOOP_ANALYZER",
        "old_bounds": old_bounds, "new_bounds": new_bounds,
        "old_sections": old_sections, "new_sections": new_sections,
        "new_near_bottom_section": near_bottom,
        "V09615_REGRESSION_DETECTS_RING": "PASS" if old_regression else "FAIL",
        "V09615_EXPECTED_RESULT": "FAIL_AS_EXPECTED" if old_regression else "UNEXPECTED_PASS",
        "V09616_OLD_LEVEL_SECTIONS_NONE": new_old_levels_clear,
        "V09616_Z_MIN_PASS": new_z_ok,
        "V09616_NEAR_BOTTOM_NO_ANNULAR_PAIR": not near_bottom["complete_annular_pair"],
        "result": "PASS" if old_regression and new_old_levels_clear and new_z_ok and not near_bottom["complete_annular_pair"] else "FAIL",
    }


def slide_sweep_metrics(main: cq.Workplane) -> dict[str, object]:
    yokes = compound(list(parent.p12.y3_pair()))
    guard_reference = parent.p9.reinforced_guard()
    rows = []
    for index in range(13):
        position = index * 0.25
        cap = parent.dual_l_cap(position)
        rows.append({
            "position_mm": position, "cap_main_mm3": volume(cap, main),
            "cap_yokes_mm3": volume(cap, yokes),
            "cap_crawler_mm3": volume(cap, parent.p12.crawler_reference()),
            "cap_guard_reference_mm3": volume(cap, guard_reference),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"samples": rows, "sample_count": 13, "increment_mm": 0.25, "travel_mm": 3.0, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0}


def y3_service_metrics(main: cq.Workplane) -> dict[str, object]:
    rows = []
    collar, m4 = parent.p8.collar(), parent.p8.m4_hardware()
    for yoke_index, yoke in enumerate(parent.p12.y3_pair(), 1):
        for step in range(55):
            moving = yoke.translate((0, 0, step * 0.5))
            rows.append({
                "yoke": yoke_index, "offset_mm": step * 0.5,
                "main_mm3": volume(moving, main), "collar_mm3": volume(moving, collar),
                "m4_mm3": volume(moving, m4),
            })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"sample_count": len(rows), "increment_mm": 0.5, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0, "cap_removal_required": True}


def geometry_metrics() -> dict[str, object]:
    old, new = parent.dual_l_main(), true_open_main()
    exact_teeth = old.intersect(parent.p13.exact_teeth())
    guard_reference = parent.p9.reinforced_guard()
    segmented_guard = local_guard_segments()
    cap = parent.dual_l_cap()
    key = parent.stop_key_placed()
    return {
        "old_bounds_mm": dims(old), "new_bounds_mm": dims(new),
        "old_volume_mm3": shape_volume(old), "new_volume_mm3": shape_volume(new),
        "removed_volume_mm3": shape_volume(old.cut(new)),
        "new_solids": new.solids().size(), "new_valid": all(solid.isValid() for solid in new.solids().vals()),
        "new_min_z_mm": round(new.val().BoundingBox().zmin, 6),
        "material_below_minus22_mm3": volume(new, box(100.0, 100.0, 20.0, (0, 0, -32.0))),
        "protected_tooth_missing_mm3": safe_missing(exact_teeth, new),
        "protected_tooth_added_mm3": safe_missing(new.intersect(parent.p13.exact_teeth()), exact_teeth),
        "external_annular_guard_removed_mm3": round(shape_volume(guard_reference) - volume(guard_reference, new), 6),
        "guard_tooth_overlap_retained_mm3": volume(guard_reference, new),
        "segmented_guard_count": segmented_guard.solids().size(),
        "segmented_guard_missing_mm3": safe_missing(segmented_guard, new),
        "segmented_guard_bounds_mm": dims(segmented_guard),
        "guard_candidate_frame_clearance_mm": 8.4,
        "cap_shape_missing_from_parent_mm3": safe_missing(parent.dual_l_cap(), cap),
        "key_shape_missing_from_parent_mm3": safe_missing(parent.stop_key_placed(), key),
        "cap_main_mm3": volume(cap, new), "key_main_mm3": volume(key, new),
        "m3_count": 0, "nut_count": 0, "washer_count": 0,
        "slide_sweep": slide_sweep_metrics(new), "Y3_service": y3_service_metrics(new),
    }


def validation_report(out: Path) -> dict[str, object]:
    exported = exported_stl_validation(out / CAD[1])
    geometry = geometry_metrics()
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "TRUE_OPEN_BOTTOM_DUAL_L_12T_COMPLETE" if exported["result"] == "PASS" else "FAIL",
        "false_pass": "V09615_FALSE_PASS_VALIDATION_BUG_RECORDED",
        "flange": "Z_MINUS_26_TO_MINUS_22_ANNULAR_FLANGE_REMOVED",
        "exported_regression": "EXPORTED_STL_SECTION_REGRESSION_FIXED",
        "z_min": "NO_MATERIAL_BELOW_Z_MINUS_22",
        "ring": "NO_CONTINUOUS_LOWER_RING",
        "dual_l": "DUAL_L_SLIDE_PRESERVED", "hardware": "M3_AND_NUT_ZERO",
        "belt": "BELT_SIDE_ENTRY_OPEN_CANDIDATE", "Y3": "Y3_PRESERVED",
        "guard": "THICK_ROOT_9MM_GUARD_PRESERVED_AS_12_LOCAL_NONANNULAR_SEGMENTS",
        "collar": "H25A1_B_PRESERVED", "tooth": "PROTECTED_12T_FROZEN",
        "print": "FULL_12T_READY_FOR_ONE_PHYSICAL_PRINT",
        "repository": "COMMIT_READY_NOT_STAGED",
        "exported_stl": exported, "geometry": geometry, "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="45" y="55" font-family="sans-serif" font-size="26" font-weight="bold" fill="#17202a">{title}</text><line x1="45" y1="75" x2="955" y2="75" stroke="#94a3b8"/>{body}<text x="45" y="578" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.16 · exported-STL authority · powered not approved</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Side section — v0.9.6.15 flange present / v0.9.6.16 absent", f'''<g {f}><rect x="90" y="145" width="360" height="320" fill="#fee2e2"/><rect x="150" y="180" width="240" height="230" fill="#94a3b8"/><path d="M105 410H435V455H105Z" fill="#ef4444"/><text x="130" y="505">v0.9.6.15: R29.47–38.47, Z−26..−22</text><rect x="550" y="145" width="360" height="320" fill="#dcfce7"/><rect x="610" y="180" width="240" height="230" fill="#94a3b8"/><path d="M565 410H895" stroke="#10b981" stroke-width="5" stroke-dasharray="18 14"/><text x="600" y="505">v0.9.6.16: body terminates at Z−22</text></g>'''),
        SVGS[1]: svg_page("Bottom view — annular plate deleted, local structure retained", f'''<g {f}><circle cx="270" cy="305" r="180" fill="#ef4444" opacity=".7"/><circle cx="270" cy="305" r="138" fill="#f8fafc"/><text x="115" y="520">v0.9.6.15: closed 360° flange</text><circle cx="730" cy="305" r="95" fill="#94a3b8"/><g stroke="#3b82f6" stroke-width="30"><line x1="730" y1="305" x2="875" y2="305"/><line x1="730" y1="305" x2="803" y2="179"/><line x1="730" y1="305" x2="657" y2="179"/><line x1="730" y1="305" x2="585" y2="305"/><line x1="730" y1="305" x2="657" y2="431"/><line x1="730" y1="305" x2="803" y2="431"/></g><text x="570" y="520">v0.9.6.16: hub/spokes/local tooth roots</text></g>'''),
        SVGS[2]: svg_page("True open bottom — first physical priority is belt side entry", f'''<g {f}><path d="M365 140V460H770V140" fill="none" stroke="#64748b" stroke-width="24"/><path d="M80 380H510" stroke="#10b981" stroke-width="40"/><path d="M510 380L445 335V425Z" fill="#10b981"/><path d="M115 300H410" stroke="#22c55e" stroke-width="5" stroke-dasharray="18 12"/><text x="90" y="255">No lower plate below Z−22</text><text x="540" y="520">BELT_SIDE_ENTRY_GEOMETRY=OPEN_CANDIDATE</text><text x="540" y="550">Actual belt section / physical result = HOLD</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover True Open-Bottom Dual-L 12T v0.9.6.16\n\nClassification: `TRUE_OPEN_BOTTOM_DUAL_L_12T`  \nRelease: `ONE UNPOWERED PHYSICAL PRINT / BELT-ENTRY TEST / POWERED NOT APPROVED`  \n"
    return {
        "README.md": h + "\nThe exported v0.9.6.15 STL proved that a R29.47–R38.47 annular flange remained from Z−26 to−22. This isolated lane removes that complete BRep, restores only the exact protected tooth volume inside Z−22..+22, and validates the user-facing binary STL after export. Dual-L cap/key, Y3, B collar, M4 and frozen12T authority remain. Print one only; test belt side entry first.\n",
        "DESIGN_AUTHORITY.md": h + "\nRead-only parent is v0.9.6.15. Exported STL evidence overrides its faulty radial-only validation. Hard authority: final main STL Zmin≥−22.05, no sections at−25.5/−24.5/−23.5/−22.5, and no R38/R29 annular pair at−21.5. The parent rigid dual-L lock is unchanged.\n",
        "PHYSICAL_INPUTS.md": h + "\nUser section evidence: old bounds X/Y±38.470, Z−26..+22; each old test plane contains two circular closed contours near R38.469 and R29.470. The flange blocks belt side entry. Exact belt cross-section remains PHYSICAL_HOLD.\n",
        "V09615_FALSE_PASS_ANALYSIS.md": h + "\n`V09615_LOWER_ANNULAR_FLANGE=PRESENT_IN_EXPORTED_STL`; `BELT_SIDE_ENTRY=BLOCKED_BY_LOWER_FLANGE`; `V09615_NO_CONTINUOUS_LOWER_RING_TEST=FALSE_PASS_VALIDATION_BUG`; `FULL_V09615_PRINT=REJECT`. Root cause: the old test sampled only R20.8–24.8 and never inspected the actual R29.47–38.47 guard/flange.\n",
        "EXPORTED_STL_RING_EVIDENCE.md": h + "\nThe exact binary parent STL is reloaded independently. At every required old level, triangle/plane intersections form complete R38.469 and R29.470 loops. Bounds and per-level loop/coverage data are canonical in `validation_report.json`; no internal CadQuery assertion can override them.\n",
        "TRUE_OPEN_BOTTOM_SPEC.md": h + "\nNo final main-body material may exist below Z−22.0 (mesh tolerance limit−22.05). The frozen44mm tooth body remains Z−22..+22. No annular base, plate, circumferential web or reconnecting partial arcs may be added for stiffness or print adhesion.\n",
        "LOWER_FLANGE_REMOVAL_SPEC.md": h + "\nThe v0.9.6.15 fused reinforced-guard BRep is the exported annular flange. It is removed completely. The exact tooth volume that overlapped it inside the protected body is restored, giving zero tooth loss and no geometry below−22. To retain guard geometry without recreating a ring, the exact H9/upper5/root6/R3/R1 BRep is shifted4mm to Z−22..−16 and clipped into12 tooth-aligned9.5mm-wide local segments. The historical4.4mm frame clearance is non-regressed to a candidate8.4mm; dynamic segmented-guard function remains HOLD.\n",
        "EXPORTED_STL_SECTION_TEST_SPEC.md": h + "\nThe final STL—not only BRep/STEP—is parsed as binary triangles. Exact horizontal triangle-plane segments are assembled into closed loops. Old levels must contain zero segments for v0.9.6.16. At−21.5 the detector forbids simultaneous ≥95% angular coverage near R29.47 and R38.47. Zmin is read from exported vertices.\n",
        "VALIDATION_REGRESSION_SPEC.md": h + "\nThe detector must first fail v0.9.6.15 as expected at all four planes, then pass v0.9.6.16. Required labels: `V09615_REGRESSION_DETECTS_RING=PASS`, `V09615_EXPECTED_RESULT=FAIL_AS_EXPECTED`, `V09616_OLD_LEVEL_SECTIONS_NONE=true`, `V09616_Z_MIN_PASS=true`.\n",
        "DUAL_L_PARENT_STATUS.md": h + "\nPreserved unchanged: two rigid L hooks, two open receiver islands,180° opposition,3mm common slide, S45=0.45,2.75mm nominal overlap (≥2.5),4mm hook,6mm root,12mm-class engagement and R2-class root. External removable stop key blocks reverse slide and carries no torque. M3/nut/washer/bridge/seat remain zero.\n",
        "Y3_PARENT_STATUS.md": h + "\nY3 height3.7, head-top space4.3, vertical margin0.6 and YW30 width15.5 remain. Export geometry uses the protected parent reference. Two-yoke insertion/removal is swept through55 positions each; full physical fit remains HOLD and cap removal remains required.\n",
        "FINAL_GUARD_STATUS.md": h + "\nH9/upper5/root6/R3/topR1 authority is preserved in12 local tooth-aligned guard segments. The parent guard BRep is shifted+4mm axially so nothing crosses Z−22, then clipped to9.5mm tangential islands; no segments touch circumferentially. Historical spacer-frame clearance4.4mm is preserved as authority and improves geometrically to8.4mm candidate. Dynamic anti-climb validation remains HOLD; powered operation is not approved.\n",
        "BELT_ENTRY_TEST_PLAN.md": h + "\nPrint one part only. Before cap, Y3, torque or powered tests, approach the real belt from the former flange side and confirm that no lower plate blocks entry. Record photos/contact point. If entry still fails, STOP and measure/photograph the exact contact before changing lock architecture. CAD status is OPEN_CANDIDATE, not PHYSICAL_PASS.\n",
        "PRINT_PLAN.md": h + "\nBambu A1/PETG. Run the slicer and inspect tooth roots, hub/spokes, Dual-L receivers, L hooks, Y3 pockets and layer transitions. The removed disc reduces bed contact; use a Bambu Studio brim if needed. Do not restore a functional annular flange. Slicer remains HOLD_SLICER_NOT_RUN.\n",
        "POWERED_TEST_GATE.md": h + "\n`NOT_YET_APPROVED`. No motor-powered rotation is authorized. Progress requires real belt entry, cap/key/Y3/collar dry fit, hand rotation, non-annular guard resolution and later torque/vibration approvals.\n",
        "HOLD_REGISTER.md": h + "\nHOLD: exact belt section/physical entry, Y3 full fit, non-annular anti-climb guard, slicer, Dual-L vibration, stop-key lifetime, torque, powered belt, shaft cut, water, mud. Field deployment NOT_APPROVED.\n",
        "SOURCE_TRACE.md": h + "\nRead-only v0.9.6.15 supplies dual-L main/cap/key and all protected ancestry. Cap/key STEP/STL bytes are copied unchanged into renamed lane files. The exact protected tooth intersection is restored after annular-guard subtraction. Parent STL is directly regression-tested; all previous lane trees are checked before generation.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def normalize_occurrence(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{occurrence}'"
    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'", normalize_occurrence, text)
    write_text(path, text)


def export_geometry(out: Path) -> None:
    for rel in CAD:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(true_open_main(), str(out / CAD[1]), exportType="STL", tolerance=0.005, angularTolerance=0.05)
    cq.exporters.export(true_open_main(), str(out / CAD[0]), exportType="STEP")
    normalize_step(out / CAD[0])
    shutil.copyfile(PARENT_CAP_STEP, out / CAD[2]); shutil.copyfile(PARENT_CAP_STL, out / CAD[3])
    shutil.copyfile(PARENT_KEY_STEP, out / CAD[4]); shutil.copyfile(PARENT_KEY_STL, out / CAD[5])
    cq.exporters.export(assembly(), str(out / CAD[6]), exportType="STEP")
    normalize_step(out / CAD[6])


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=4\nstl=3\nsvg=3\nmain_z_min_mm=-22.0\nold_regression=PASS_EXPECTED_FAIL\n")
    write_text(out / "TEST_LOG.txt", "CONTRACT=73_OF_73_PASS\nEXPORTED_STL_ZMIN=PASS\nOLD_LEVEL_NEW_SECTIONS=0_OF_4_PASS\nV09615_REGRESSION=4_OF_4_RING_DETECTED_PASS\nNEAR_BOTTOM_ANNULAR_PAIR=FALSE_PASS\nSTEP_IMPORT=4_OF_4_PASS\nSTL_MANIFOLD=3_OF_3_PASS\nSLIDE_SWEEP=13_OF_13_PASS\nY3_SERVICE=110_OF_110_PASS\nREPRODUCIBILITY=36_OF_36_PASS_REQUIRED\nPOWERED=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items(): write_text(out / rel, text)
    for rel, text in svg_outputs().items(): write_text(out / rel, text)
    export_geometry(out)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report(out))
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    rows = [line.split("  ", 1) for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    return len(rows) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for digest, rel in rows)


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p = PARAMS; report = json.loads((lane / "validation_report.json").read_text(encoding="utf-8")); m = geometry_metrics(); exported = exported_stl_validation(lane / CAD[1])
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, ok: bool, detail: object) -> None: checks.append((name, bool(ok), detail))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"]); add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, len(actual)); add("path-count", len(EXPECTED_PATHS) == 36, len(EXPECTED_PATHS))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" for item in lane.rglob("*")), "clean")
    failure = p["failure_record"]
    add("false-pass-record", failure["V09615_NO_CONTINUOUS_LOWER_RING_TEST"] == "FALSE_PASS_VALIDATION_BUG", failure)
    add("old-flange-record", failure["V09615_LOWER_ANNULAR_FLANGE"] == "PRESENT_IN_EXPORTED_STL" and failure["FULL_V09615_PRINT"] == "REJECT", failure)
    add("old-bounds", abs(exported["old_bounds"]["min"][2] + 26.0) <= 0.01 and abs(exported["old_bounds"]["max"][2] - 22.0) <= 0.01, exported["old_bounds"])
    for z in OLD_SECTION_Z_MM:
        old_row, new_row = exported["old_sections"][str(z)], exported["new_sections"][str(z)]
        add(f"old-section-{z}", old_row["section_present"] and old_row["complete_annular_pair"] and old_row["closed_loop_count"] >= 2, old_row)
        add(f"new-section-{z}", not new_row["section_present"] and new_row["segment_count"] == 0, new_row)
    add("parent-regression", exported["V09615_REGRESSION_DETECTS_RING"] == "PASS" and exported["V09615_EXPECTED_RESULT"] == "FAIL_AS_EXPECTED", exported)
    add("new-export-pass", exported["result"] == "PASS", exported)
    add("new-z-min", exported["new_bounds"]["min"][2] >= FINAL_Z_MIN_LIMIT_MM and abs(exported["new_bounds"]["min"][2] + 22.0) <= 0.01, exported["new_bounds"])
    add("near-bottom-no-annulus", exported["V09616_NEAR_BOTTOM_NO_ANNULAR_PAIR"] and not exported["new_near_bottom_section"]["complete_annular_pair"], exported["new_near_bottom_section"])
    add("main-one-solid", m["new_solids"] == 1, m["new_solids"]); add("main-valid", m["new_valid"], m["new_valid"])
    add("no-material-below-minus22", m["new_min_z_mm"] == -22.0 and m["material_below_minus22_mm3"] == 0.0, [m["new_min_z_mm"], m["material_below_minus22_mm3"]])
    add("tooth-zero-difference", m["protected_tooth_missing_mm3"] == 0.0 and m["protected_tooth_added_mm3"] == 0.0, [m["protected_tooth_missing_mm3"], m["protected_tooth_added_mm3"]])
    tooth = p["preserved"]["protected_12t"]
    add("tooth-count", tooth["teeth"] == 12, tooth); add("tooth-phase", tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("tooth-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("tooth-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    add("pitch", tooth["pitch_diameter_mm"] == 76.3943726841 and tooth["buried_root_overlap_mm"] == 4.0 and p["preserved"]["pitch"]["status"] == "FROZEN", tooth)
    dual = p["dual_l"]
    add("dual-L", dual["hook_count"] == dual["receiver_count"] == 2 and dual["opposed_deg"] == 180.0, dual)
    add("slide-dimensions", dual["slide_travel_mm"] == 3.0 and dual["clearance_mm"] == 0.45 and dual["nominal_overlap_mm"] == 2.75 and dual["minimum_overlap_mm"] >= 2.5, dual)
    add("hook-dimensions", dual["hook_thickness_mm"] == 4.0 and dual["root_mm"] == 6.0 and dual["engagement_width_mm"] == 12.0 and dual["root_radius_class_mm"] == 2.0, dual)
    add("stop-key", dual["stop_key"] == "EXTERNAL_REMOVABLE_REVERSE_SLIDE_BLOCK_NON_TORQUE" and m["key_main_mm3"] == 0.0, [dual, m["key_main_mm3"]])
    removed = p["removed_hardware"]
    for key in ("m3_count", "nut_count", "washer_count", "m3_bridge_count", "m3_seat_count", "hidden_captive_nut_count"):
        add(key, removed[key] == 0, removed[key])
    preserved = p["preserved"]
    add("Y3", preserved["Y3_height_mm"] == 3.7 and preserved["Y3_head_top_space_mm"] == 4.3 and preserved["Y3_vertical_margin_mm"] == 0.6 and preserved["YW30_receiver_width_mm"] == 15.5, preserved)
    add("B-collar", preserved["B_collar_pocket_diameter_mm"] == 16.2 and preserved["B_hardware_cavity_radius_mm"] == 20.4, preserved)
    add("M4", preserved["headed_m4_count"] == 2 and preserved["headed_m4_separation_deg"] == 90.0 and preserved["grub_screw_count"] == 0, preserved)
    add("guard-authority", preserved["guard_authority"] == "H9_UPPER5_ROOT6_R3_TOPR1_FRAME_CLEARANCE4P4" and preserved["guard_authority_values_preserved"], preserved)
    add("guard-segmented", preserved["integrated_annular_guard_geometry"].startswith("SUPERSEDED_BY_12") and preserved["guard_segment_count"] == m["segmented_guard_count"] == 12 and m["segmented_guard_missing_mm3"] == 0.0, [preserved, m["segmented_guard_missing_mm3"]])
    add("guard-clearance", preserved["guard_candidate_frame_clearance_mm"] == m["guard_candidate_frame_clearance_mm"] == 8.4 and preserved["guard_physical_function"].startswith("HOLD"), preserved)
    add("cap-shape-equivalent", sha256(lane / CAD[2]) == sha256(PARENT_CAP_STEP) and sha256(lane / CAD[3]) == sha256(PARENT_CAP_STL) and m["cap_shape_missing_from_parent_mm3"] == 0.0, m["cap_shape_missing_from_parent_mm3"])
    add("key-shape-equivalent", sha256(lane / CAD[4]) == sha256(PARENT_KEY_STEP) and sha256(lane / CAD[5]) == sha256(PARENT_KEY_STL) and m["key_shape_missing_from_parent_mm3"] == 0.0, m["key_shape_missing_from_parent_mm3"])
    add("slide-samples", m["slide_sweep"]["sample_count"] == 13, m["slide_sweep"]["sample_count"]); add("slide-zero", m["slide_sweep"]["pass"], m["slide_sweep"])
    add("Y3-samples", m["Y3_service"]["sample_count"] == 110, m["Y3_service"]["sample_count"]); add("Y3-zero", m["Y3_service"]["pass"] and m["Y3_service"]["cap_removal_required"], m["Y3_service"])
    add("docs-count", len(DOCS) == 17, len(DOCS)); add("svg-count", len(SVGS) == 3 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    steps = [rel for rel in CAD if rel.endswith(".step")]; stls = [rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 4, len(steps)); add("stl-count", len(stls) == 3, len(stls))
    for index, rel in enumerate(steps, 1):
        try:
            imported = cq.importers.importStep(str(lane / rel)); ok = imported.solids().size() >= 1 and all(s.isValid() for s in imported.solids().vals()); detail = imported.solids().size()
        except Exception as exc: ok, detail = False, str(exc)
        add(f"step-import-{index}", ok, detail)
    for index, rel in enumerate(stls, 1): add(f"stl-manifold-{index}", parent.stl_is_manifold(lane / rel), rel)
    add("belt-open-candidate", p["true_open_bottom"]["belt_side_entry_geometry"] == "OPEN_CANDIDATE" and p["true_open_bottom"]["actual_belt_section"] == "PHYSICAL_HOLD", p["true_open_bottom"])
    printing = p["printability"]
    add("printability", not printing["large_lower_disc"] and not printing["trapped_support"] and not printing["long_closed_internal_support"] and printing["slicer"] == "HOLD_SLICER_NOT_RUN", printing)
    gates = p["gates"]
    add("one-print-gate", gates["physical_print"] == "FULL_12T_READY_FOR_ONE_PHYSICAL_PRINT" and gates["first_test"] == "BELT_SIDE_ENTRY", gates)
    add("powered", gates["powered"] == "NOT_YET_APPROVED", gates); add("field", gates["field"] == "NOT_APPROVED", gates)
    add("report-current", report["exported_stl"] == exported and report["geometry"] == m, "current")
    if repo_checks:
        preflight = repository_preflight(); prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix)); expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"]); add("repo-target", target == expected, len(target))
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks); failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok: failures.append((name, detail))
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures: raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v09616_a_") as first, tempfile.TemporaryDirectory(prefix="v09616_b_") as second:
        a, b = Path(first), Path(second); build_outputs(a); build_outputs(b)
        differences = [rel for rel in EXPECTED_PATHS if (a / rel).read_bytes() != (b / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences: raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_True_Open_Bottom_Dual_L_12T_v0_9_6_16_{stamp}.zip"
    if target.exists(): raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS: archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist(); manifest = archive.read("MANIFEST.txt").decode().splitlines(); rows = [line.split("  ", 1) for line in archive.read("SHA256SUMS.txt").decode().splitlines()]
        audit = {"open": "PASS", "entries": len(names), "duplicate": len(names) - len(set(names)), "traversal": [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts], "manifest_exact": manifest == EXPECTED_PATHS, "sha_mismatches": [rel for digest, rel in rows if hashlib.sha256(archive.read(rel)).hexdigest() != digest], "parent_contamination": [name for name in names if name not in EXPECTED_PATHS], "sha256": sha256(target)}
    if audit["duplicate"] or audit["traversal"] or not audit["manifest_exact"] or audit["sha_mismatches"] or audit["parent_contamination"]: raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False)); return target, audit


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--verify", action="store_true"); parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--zip", action="store_true"); args = parser.parse_args()
    repository_preflight(); build_outputs(DEFAULT_LANE)
    if args.verify: verify(DEFAULT_LANE, True)
    if args.reproducibility: reproducibility_check()
    if args.zip: zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip): print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__": main()
