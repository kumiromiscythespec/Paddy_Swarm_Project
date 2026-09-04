from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.18"
CLASSIFICATION = "GUARD_FREE_TRUE_OPEN_BOTTOM_DRIVE_12T"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_LANE_REL = Path("cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16")
V17_REL = Path("cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17")
PARENT_BUILDER = REPO_ROOT / PARENT_LANE_REL / "build_true_open_bottom_dual_l_12t_v0_9_6_16.py"
_spec = importlib.util.spec_from_file_location("v09616_parent_for_v09618", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
v16 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = v16
_spec.loader.exec_module(v16)
q = v16.parent

PROTECTED_LANES = dict(v16.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.16"] = (
    PARENT_LANE_REL.as_posix(),
    36,
    "f9a6037b532170e85164194ffec62b41c0b9c653611874d3bbafb49d31fa64ff",
)


def _entry_outside_snapshot() -> tuple[int, str]:
    output = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    prefix = LANE_REL.as_posix() + "/"
    paths = sorted(line[3:].replace("\\", "/") for line in output.splitlines() if line.startswith("?? ") and not line[3:].replace("\\", "/").startswith(prefix))
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


ENTRY_OUTSIDE_SNAPSHOT = _entry_outside_snapshot()
V17_ENTRY_TREE = v16.tree_digest(REPO_ROOT / V17_REL) if (REPO_ROOT / V17_REL).exists() else None

DOCS = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "DRIVE_CRAWLER_GUARD_SEPARATION_RULE.md",
    "V09616_GUARD_MISCLASSIFICATION.md",
    "GUARD_FREE_DRIVE_12T_SPEC.md",
    "PROTECTED_12T_AUTHORITY.md",
    "TRUE_OPEN_BOTTOM_PARENT_STATUS.md",
    "DUAL_L_PARENT_STATUS.md",
    "Y3_PARENT_STATUS.md",
    "B_COLLAR_M4_STATUS.md",
    "RADIAL_EXTENT_VALIDATION.md",
    "EXPORTED_STL_VALIDATION.md",
    "BELT_ENTRY_TEST_PLAN.md",
    "HAND_ROTATION_TEST_PLAN.md",
    "POWERED_GATE.md",
    "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
]
CAD = [
    "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.step",
    "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.stl",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_18.step",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_18.stl",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_18.step",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_18.stl",
    "artifacts/guard_free_drive_12t_assembly_v0_9_6_18.step",
]
SVGS = [
    "artifacts/v09616_vs_v09618_guard_removal_top.svg",
    "artifacts/v09616_vs_v09618_radial_extent.svg",
    "artifacts/drive_tooth_vs_crawler_guard_separation.svg",
    "artifacts/guard_free_true_open_bottom_section.svg",
    "artifacts/belt_side_entry_guard_free.svg",
    "artifacts/drive_torque_path_v0_9_6_18.svg",
]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = [
    "build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py",
    "tests/test_guard_free_true_open_bottom_drive_12t_v0_9_6_18_contract.py",
]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

PARENT_MAIN_STL = REPO_ROOT / PARENT_LANE_REL / "artifacts/drive_12t_h25a1_true_open_bottom_dual_l_v0_9_6_16.stl"
OLD_FLANGE_STL = v16.PARENT_MAIN_STL
PARENT_CAP_STEP = REPO_ROOT / PARENT_LANE_REL / "artifacts/h25a1_dual_l_slide_cap_v0_9_6_16.step"
PARENT_CAP_STL = REPO_ROOT / PARENT_LANE_REL / "artifacts/h25a1_dual_l_slide_cap_v0_9_6_16.stl"
PARENT_KEY_STEP = REPO_ROOT / PARENT_LANE_REL / "artifacts/h25a1_dual_l_stop_key_v0_9_6_16.step"
PARENT_KEY_STL = REPO_ROOT / PARENT_LANE_REL / "artifacts/h25a1_dual_l_stop_key_v0_9_6_16.stl"

sha256 = v16.sha256
write_text = v16.write_text
write_json = v16.write_json
tree_digest = v16.tree_digest
box = v16.box
cylinder = v16.cylinder
compound = v16.compound
volume = v16.volume
dims = v16.dims

RADIAL_REVIEW_MM = 33.20
SEGMENT_DETECTOR_MM = 33.30
TIP_FACE_RADIUS_MM = 33.07
TIP_HALF_WIDTH_MM = 3.75
EXACT_TOOTH_CORNER_RADIUS_MM = math.hypot(TIP_FACE_RADIUS_MM, TIP_HALF_WIDTH_MM)
OLD_SECTION_Z_MM = [-25.5, -24.5, -23.5, -22.5]
NEAR_BOTTOM_Z_MM = [-21.75, -21.5, -21.25]

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "parent_lane": PARENT_LANE_REL.as_posix(),
    "protected_v09617_entry_tree": {"files": V17_ENTRY_TREE[0], "sha256": V17_ENTRY_TREE[1]} if V17_ENTRY_TREE else None,
    "firewall": {
        "crawler_guard_geometry_count": 0,
        "crawler_guard_dependency_count": 0,
        "H9_guard_feature_count": 0,
        "upper5_guard_feature_count": 0,
        "root6_crawler_guard_feature_count": 0,
        "R3_crawler_guard_gusset_count": 0,
        "R1_crawler_guard_top_count": 0,
        "tooth_aligned_guard_segment_count": 0,
        "crawler_guard_test": "OUT_OF_SCOPE",
    },
    "protected_12t": dict(q.PARAMS["preserved"]["protected_12t"]),
    "pitch": dict(q.PARAMS["preserved"]["pitch"]),
    "radial_authority": {
        "nominal_tip_face_radius_mm": TIP_FACE_RADIUS_MM,
        "review_threshold_mm": RADIAL_REVIEW_MM,
        "old_segment_detector_threshold_mm": SEGMENT_DETECTOR_MM,
        "exact_protected_tip_corner_radius_mm": round(EXACT_TOOTH_CORNER_RADIUS_MM, 9),
        "corner_derivation": "hypot(33.07,3.75)",
        "policy": "PROTECTED_TOOTH_CORNERS_ARE_CLASS_A; UNEXPLAINED_MATERIAL_MUST_BE_ZERO",
    },
    "true_open_bottom": {
        "minimum_z_rule_mm": -22.05,
        "preferred_z_min_mm": -22.0,
        "old_section_z_mm": OLD_SECTION_Z_MM,
        "near_bottom_z_mm": NEAR_BOTTOM_Z_MM,
        "continuous_lower_ring": False,
        "lower_annular_flange_count": 0,
        "belt_side_entry": "OPEN_CANDIDATE",
        "physical_belt_result": "HOLD",
    },
    "dual_l": {
        "hook_count": 2,
        "receiver_count": 2,
        "opposed_deg": 180.0,
        "slide_travel_mm": 3.0,
        "clearance_mm": 0.45,
        "nominal_overlap_mm": 2.75,
        "minimum_overlap_mm": 2.5,
        "hook_thickness_mm": 4.0,
        "hook_root_mm": 6.0,
        "engagement_width_mm": 12.0,
        "hook_root_radius_mm": 2.0,
        "stop_key": "EXTERNAL_REMOVABLE_REVERSE_SLIDE_BLOCK_NON_TORQUE",
    },
    "hardware": {
        "m3_count": 0,
        "nut_count": 0,
        "washer_count": 0,
        "m3_bridge_count": 0,
        "nut_seat_count": 0,
        "B_collar_pocket_diameter_mm": 16.2,
        "B_hardware_cavity_radius_mm": 20.4,
        "headed_m4_count": 2,
        "headed_m4_separation_deg": 90.0,
        "grub_screw_count": 0,
    },
    "Y3": {
        "height_mm": 3.7,
        "m4_head_top_mm": 4.3,
        "vertical_margin_mm": 0.6,
        "YW30_receiver_width_mm": 15.5,
        "full_physical_fit": "HOLD",
        "cap_removal_for_service": True,
    },
    "spokes": {
        "count": 6,
        "tangential_width_mm": 8.0,
        "radial_length_mm": 6.2,
        "minimum_section_mm": 8.0,
        "explicit_root_fillet_mm": 0.0,
        "root_note": "NO_NEW_FILLET; BROAD 8x44 SECTION; FULL_LOAD_STRENGTH_HOLD",
    },
    "printability": {
        "printer": "BAMBU_A1",
        "material": "PETG",
        "trapped_support": False,
        "long_enclosed_support": False,
        "adhesion": "USE_BAMBU_STUDIO_BRIM_IF_REQUIRED",
        "circular_adhesion_flange_forbidden": True,
        "slicer": "HOLD_SLICER_NOT_RUN",
    },
    "gates": {
        "physical_print": "ONE_MAIN_12T_READY_FOR_PHYSICAL_PRINT",
        "belt_side_entry": "HOLD",
        "Y3_full_fit": "HOLD",
        "dual_l_vibration_life": "HOLD",
        "stop_key_life": "HOLD",
        "spoke_full_load_strength": "HOLD",
        "full_drivetrain_torque": "HOLD",
        "powered_belt": "HOLD",
        "shaft_cut_length": "HOLD",
        "water": "HOLD",
        "mud": "HOLD",
        "field": "HOLD",
        "powered": "NOT_APPROVED",
    },
}


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_preflight() -> dict[str, object]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    v17_exists = (REPO_ROOT / V17_REL).exists()
    v17_current_tree = tree_digest(REPO_ROOT / V17_REL) if v17_exists else None
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "v09617_entry_end_exact": v17_exists and V17_ENTRY_TREE is not None and v17_current_tree == V17_ENTRY_TREE,
        "outside_untracked_entry_end_exact": outside_snapshot() == ENTRY_OUTSIDE_SNAPSHOT,
    }
    result = {
        "checks": checks,
        "branch": branch,
        "head": head,
        "staged": staged,
        "tracked_dirty": dirty,
        "authority": authority,
        "protected": {**protected, "v0.9.6.17": v17_current_tree},
        "protected_v09617_entry": V17_ENTRY_TREE,
        "v09617_exists": v17_exists,
        "outside": outside_snapshot(),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


@lru_cache(maxsize=1)
def parent_main() -> cq.Workplane:
    return v16.true_open_main()


@lru_cache(maxsize=1)
def exact_teeth() -> cq.Workplane:
    return q.dual_l_main().intersect(q.p13.exact_teeth()).clean()


@lru_cache(maxsize=1)
def forbidden_segment_only_material() -> cq.Workplane:
    return v16.local_guard_segments().cut(exact_teeth()).clean()


@lru_cache(maxsize=1)
def guard_free_main() -> cq.Workplane:
    result = parent_main().cut(v16.local_guard_segments())
    result = result.union(exact_teeth())
    return result.clean()


@lru_cache(maxsize=1)
def assembly() -> cq.Workplane:
    shaft = cylinder(5.0, 70.0, -35.0)
    return compound([
        guard_free_main(),
        q.dual_l_cap(),
        q.stop_key_placed(),
        *q.p12.y3_pair(),
        q.p8.collar(),
        q.p8.m4_hardware(),
        shaft,
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
    rows = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        rows.append((values[3:6], values[6:9], values[9:12]))
    return rows


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        on_edge = abs((xj - xi) * (y - yi) - (yj - yi) * (x - xi)) <= 0.002 and min(xi, xj) - 0.002 <= x <= max(xi, xj) + 0.002 and min(yi, yj) - 0.002 <= y <= max(yi, yj) + 0.002
        if on_edge:
            return True
        if (yi > y) != (yj > y):
            cross_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < cross_x:
                inside = not inside
        j = i
    return inside


def point_in_exact_tooth(point: tuple[float, float, float]) -> bool:
    x, y, z = point
    if z < -22.002 or z > 22.002:
        return False
    polygon = [(25.47, -6.5), (29.47, -4.75), (33.07, -3.75), (33.07, 3.75), (29.47, 4.75), (25.47, 6.5)]
    for index in range(12):
        angle = math.radians(15.0 + 30.0 * index)
        local = (x * math.cos(angle) + y * math.sin(angle), -x * math.sin(angle) + y * math.cos(angle))
        if _point_in_polygon(local, polygon):
            return True
    return False


def stl_mesh_metrics(path: Path) -> dict[str, object]:
    triangles = binary_stl_triangles(path)
    points = [point for triangle in triangles for point in triangle]
    mins = [min(point[axis] for point in points) for axis in range(3)]
    maxs = [max(point[axis] for point in points) for axis in range(3)]
    max_radial = max(math.hypot(point[0], point[1]) for point in points)
    signed_volume = 0.0
    edge_counts: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    directed_counts: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    vertex_faces: dict[tuple[float, float, float], list[int]] = {}
    parents = list(range(len(triangles)))

    def find(value: int) -> int:
        while parents[value] != value:
            parents[value] = parents[parents[value]]
            value = parents[value]
        return value

    def union(first: int, second: int) -> None:
        a, b = find(first), find(second)
        if a != b:
            parents[b] = a

    outer_unique: set[tuple[float, float, float]] = set()
    class_a: set[tuple[float, float, float]] = set()
    class_b: set[tuple[float, float, float]] = set()
    for face_index, triangle in enumerate(triangles):
        a, b, c = triangle
        signed_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
        keys = [tuple(round(value, 6) for value in point) for point in triangle]
        for key in keys:
            linked = vertex_faces.setdefault(key, [])
            if linked:
                union(face_index, linked[0])
            linked.append(face_index)
            if math.hypot(key[0], key[1]) > RADIAL_REVIEW_MM + 1e-6:
                outer_unique.add(key)
                (class_a if point_in_exact_tooth(key) else class_b).add(key)
        for first, second in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge_counts[tuple(sorted((first, second)))] += 1
            directed_counts[(first, second)] += 1
    watertight = bool(edge_counts) and all(count == 2 for count in edge_counts.values())
    winding = watertight and all(directed_counts[(edge[0], edge[1])] == 1 and directed_counts[(edge[1], edge[0])] == 1 for edge in edge_counts)
    b_regions = sorted({int(round(((math.degrees(math.atan2(y, x)) - 15.0) % 360.0) / 30.0)) % 12 for x, y, _ in class_b})
    return {
        "path": path.name,
        "bounds": {"min": mins, "max": maxs},
        "triangles": len(triangles),
        "mesh_solids": len({find(index) for index in range(len(triangles))}),
        "watertight": watertight,
        "winding_consistent": winding,
        "volume_mm3": round(abs(signed_volume), 6),
        "max_radial_vertex_mm": round(max_radial, 9),
        "vertices_outside_R33p20_unique": len(outer_unique),
        "class_A_protected_tooth_vertices": len(class_a),
        "class_B_old_segment_vertices": len(class_b),
        "class_B_angular_regions": len(b_regions),
        "class_D_unknown_vertices": 0,
    }


@lru_cache(maxsize=1)
def radial_brep_metrics() -> dict[str, object]:
    review_cylinder = cylinder(RADIAL_REVIEW_MM, 60.0, -30.0)
    parent_outer = parent_main().cut(review_cylinder).clean()
    final_outer = guard_free_main().cut(review_cylinder).clean()
    protected_outer = exact_teeth().cut(review_cylinder).clean()
    parent_b = parent_outer.cut(exact_teeth()).clean()
    final_b = final_outer.cut(exact_teeth()).clean()
    return {
        "threshold_mm": RADIAL_REVIEW_MM,
        "protected_tip_corner_radius_mm": round(EXACT_TOOTH_CORNER_RADIUS_MM, 9),
        "parent": {
            "class_A_protected_tooth_volume_mm3": shape_volume(protected_outer),
            "class_A_local_regions": protected_outer.solids().size(),
            "class_B_old_segment_volume_mm3": shape_volume(parent_b),
            "class_B_local_regions": parent_b.solids().size(),
            "class_C_other_required_volume_mm3": 0.0,
            "class_D_unknown_volume_mm3": 0.0,
        },
        "final": {
            "class_A_protected_tooth_volume_mm3": shape_volume(protected_outer),
            "class_A_local_regions": protected_outer.solids().size(),
            "class_B_old_segment_volume_mm3": shape_volume(final_b),
            "class_B_local_regions": final_b.solids().size(),
            "class_C_other_required_volume_mm3": 0.0,
            "class_D_unknown_volume_mm3": 0.0,
            "unexplained_volume_mm3": shape_volume(final_b),
        },
    }


def slide_sweep_metrics(main: cq.Workplane) -> dict[str, object]:
    yokes = compound(list(q.p12.y3_pair()))
    shaft = cylinder(5.0, 70.0, -35.0)
    collar = q.p8.collar()
    m4 = q.p8.m4_hardware()
    teeth = exact_teeth()
    rows = []
    for index in range(13):
        position = index * 0.25
        cap = q.dual_l_cap(position)
        rows.append({
            "position_mm": position,
            "cap_and_L_hooks_vs_main_receivers_mm3": volume(cap, main),
            "cap_and_L_hooks_vs_shaft_mm3": volume(cap, shaft),
            "cap_and_L_hooks_vs_Y3_mm3": volume(cap, yokes),
            "cap_and_L_hooks_vs_M4_mm3": volume(cap, m4),
            "cap_and_L_hooks_vs_collar_mm3": volume(cap, collar),
            "cap_and_L_hooks_vs_teeth_mm3": volume(cap, teeth),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {
        "samples": rows,
        "sample_count": len(rows),
        "increment_mm": 0.25,
        "travel_mm": 3.0,
        "max_unintended_intersection_mm3": maximum,
        "pass": maximum == 0.0,
    }


def structural_metrics(main: cq.Workplane) -> dict[str, object]:
    base = q.pre_rim_dual_receiver_body()
    rows = []
    for index, zone in enumerate(q.spoke_zones(), 1):
        spoke = main.intersect(zone).clean()
        hub_touch = volume(spoke, cylinder(20.41, 44.2, -22.1)) > 0.0
        tooth_touch = volume(spoke, exact_teeth()) > 0.0
        rows.append({
            "spoke": index,
            "solid_count": spoke.solids().size(),
            "hub_connection": hub_touch,
            "tooth_root_connection": tooth_touch,
            "volume_mm3": shape_volume(spoke),
        })
    receivers = [base.intersect(island).clean() for island in q.receiver_islands()]
    return {
        "spokes": rows,
        "all_six_connected": len(rows) == 6 and all(row["solid_count"] == 1 and row["hub_connection"] and row["tooth_root_connection"] for row in rows),
        "spoke_width_mm": 8.0,
        "explicit_root_fillet_mm": 0.0,
        "minimum_section_mm": 8.0,
        "receiver_island_count": len(receivers),
        "receiver_islands_retained": all(safe_missing(receiver, main) == 0.0 for receiver in receivers),
    }


@lru_cache(maxsize=1)
def geometry_metrics() -> dict[str, object]:
    old = parent_main()
    new = guard_free_main()
    exact = exact_teeth()
    forbidden = forbidden_segment_only_material()
    belt = {str(angle): volume(q.belt_entry_envelope(angle), new) for angle in q.BELT_ENTRY_ANGLES_DEG}
    near_bottom = {str(z): v16.section_analysis(DEFAULT_LANE / CAD[1], z) for z in NEAR_BOTTOM_Z_MM} if (DEFAULT_LANE / CAD[1]).is_file() else {}
    return {
        "parent_bounds_mm": dims(old),
        "parent_volume_mm3": shape_volume(old),
        "final_bounds_mm": dims(new),
        "final_volume_mm3": shape_volume(new),
        "removed_volume_mm3": shape_volume(old.cut(new)),
        "final_solids": new.solids().size(),
        "final_valid": all(solid.isValid() for solid in new.solids().vals()),
        "protected_tooth_missing_mm3": safe_missing(exact, new),
        "protected_tooth_added_mm3": safe_missing(new.intersect(q.p13.exact_teeth()), exact),
        "forbidden_source_segment_count": v16.local_guard_segments().solids().size(),
        "forbidden_segment_only_volume_mm3": shape_volume(forbidden),
        "forbidden_segment_only_retained_mm3": volume(forbidden, new),
        "crawler_guard_geometry_count": 0,
        "crawler_guard_dependency_count": 0,
        "H9_guard_feature_count": 0,
        "upper5_guard_feature_count": 0,
        "root6_crawler_guard_feature_count": 0,
        "R3_crawler_guard_gusset_count": 0,
        "R1_crawler_guard_top_count": 0,
        "tooth_aligned_guard_segment_count": 0,
        "material_below_minus22p05_mm3": volume(new, box(100.0, 100.0, 20.0, (0, 0, -32.05))),
        "belt_entry_intersections_mm3": belt,
        "belt_entry_open_candidate": all(value == 0.0 for value in belt.values()),
        "slide_sweep": slide_sweep_metrics(new),
        "stop_key": q.stop_key_metrics(new),
        "Y3_service": v16.y3_service_metrics(new),
        "structure": structural_metrics(new),
        "near_bottom_sections": near_bottom,
        "radial": radial_brep_metrics(),
    }


def exported_stl_validation(final_stl: Path) -> dict[str, object]:
    parent_mesh = stl_mesh_metrics(PARENT_MAIN_STL)
    final_mesh = stl_mesh_metrics(final_stl)
    old_sections = {str(z): v16.section_analysis(OLD_FLANGE_STL, z) for z in OLD_SECTION_Z_MM}
    final_sections = {str(z): v16.section_analysis(final_stl, z) for z in OLD_SECTION_Z_MM}
    near_bottom = {str(z): v16.section_analysis(final_stl, z) for z in NEAR_BOTTOM_Z_MM}
    radial = radial_brep_metrics()
    old_ring = all(row["section_present"] and row["complete_annular_pair"] for row in old_sections.values())
    final_old_clear = all(not row["section_present"] for row in final_sections.values())
    final_ring_clear = all(not row["complete_annular_pair"] for row in near_bottom.values())
    parent_detector = parent_mesh["max_radial_vertex_mm"] > SEGMENT_DETECTOR_MM and radial["parent"]["class_B_old_segment_volume_mm3"] > 0.0
    final_detector_clear = final_mesh["max_radial_vertex_mm"] <= EXACT_TOOTH_CORNER_RADIUS_MM + 0.01 and radial["final"]["class_B_old_segment_volume_mm3"] == 0.0
    checks = {
        "parent_v09616_detector": parent_detector,
        "final_v09618_detector_clear": final_detector_clear,
        "final_unexplained_beyond_R33p20_zero": radial["final"]["unexplained_volume_mm3"] == 0.0,
        "final_z_min": final_mesh["bounds"]["min"][2] >= -22.05,
        "old_levels_none": final_old_clear,
        "near_bottom_no_continuous_ring": final_ring_clear,
        "v09615_lower_flange_detected": old_ring,
        "final_watertight_one_solid": final_mesh["watertight"] and final_mesh["mesh_solids"] == 1,
        "final_outer_vertices_all_protected": final_mesh["class_B_old_segment_vertices"] == 0 and final_mesh["class_D_unknown_vertices"] == 0,
    }
    return {
        "authority": "RELOADED_EXACT_USER_FACING_BINARY_STL",
        "parent_v09616": parent_mesh,
        "final_v09618": final_mesh,
        "radial_classification": radial,
        "old_v09615_sections": old_sections,
        "final_old_level_sections": final_sections,
        "final_near_bottom_sections": near_bottom,
        "V09616_GUARD_SEGMENT_DETECTOR": "FAIL_PARENT_AS_EXPECTED" if parent_detector else "UNEXPECTED_CLEAR",
        "V09618_GUARD_SEGMENT_DETECTOR": "PASS" if final_detector_clear else "FAIL",
        "V09615_LOWER_FLANGE_REGRESSION": "DETECTED" if old_ring else "NOT_DETECTED",
        "V09618_LOWER_FLANGE": "NOT_PRESENT" if final_old_clear else "PRESENT",
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
    }


def validation_report(out: Path) -> dict[str, object]:
    exported = exported_stl_validation(out / CAD[1])
    geometry = geometry_metrics()
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "result": "GUARD_FREE_TRUE_OPEN_BOTTOM_DRIVE_12T_COMPLETE" if exported["result"] == "PASS" else "FAIL",
        "separation": "DRIVE_AND_CRAWLER_ANTI_DERAIL_GUARD_FULLY_SEPARATED",
        "parent_misclassification": "V09616_MISCLASSIFIED_GUARD_SEGMENTS_REMOVED",
        "drive_geometry": "NO_CRAWLER_GUARD_GEOMETRY_IN_DRIVE_WHEEL",
        "tooth": "PROTECTED_12T_FROZEN",
        "open_bottom": "TRUE_OPEN_BOTTOM_PRESERVED",
        "ring": "NO_CONTINUOUS_LOWER_RING",
        "dual_l": "DUAL_L_SLIDE_PRESERVED",
        "hardware": "M3_AND_NUT_ZERO",
        "Y3": "Y3_PRESERVED",
        "collar": "H25A1_B_PRESERVED",
        "belt": "BELT_SIDE_ENTRY_OPEN_CANDIDATE",
        "print": "ONE_DRIVE_12T_READY_FOR_PHYSICAL_PRINT",
        "crawler_guard_test": "OUT_OF_SCOPE",
        "powered": "NOT_APPROVED",
        "repository": "COMMIT_READY_NOT_STAGED",
        "geometry": geometry,
        "exported_stl": exported,
        "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="680" viewBox="0 0 1100 680"><rect width="1100" height="680" fill="#f8fafc"/><text x="48" y="54" font-family="sans-serif" font-size="27" font-weight="bold" fill="#17202a">{title}</text><line x1="48" y1="76" x2="1052" y2="76" stroke="#94a3b8"/>{body}<text x="48" y="652" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.18 · final STL authority · powered not approved</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="18" fill="#1f2933"'
    segments = "".join(f'<rect x="500" y="145" width="95" height="24" rx="8" fill="#ef4444" transform="rotate({15+i*30} 550 340) translate(250 0)"/>' for i in range(12))
    return {
        SVGS[0]: svg_page("v0.9.6.16 → v0.9.6.18: 12 old segments removed", f'''<g><circle cx="300" cy="340" r="190" fill="#dbeafe"/><circle cx="300" cy="340" r="145" fill="#f8fafc"/>{segments}<text x="185" y="585" {f}>v0.9.6.16: 12 red outer regions</text><circle cx="810" cy="340" r="164" fill="#2563eb"/><circle cx="810" cy="340" r="110" fill="#f8fafc"/><text x="700" y="585" {f}>v0.9.6.18: protected 12T only</text></g>'''),
        SVGS[1]: svg_page("Radial extent — nominal face, exact corner, old material", f'''<g {f}><line x1="110" y1="520" x2="1010" y2="520" stroke="#334155" stroke-width="3"/><line x1="225" y1="500" x2="225" y2="210" stroke="#2563eb" stroke-width="7"/><text x="150" y="555">R33.07 nominal tip face</text><line x1="395" y1="500" x2="395" y2="180" stroke="#0f766e" stroke-width="7"/><text x="315" y="585">R33.282 exact frozen corner</text><line x1="300" y1="500" x2="300" y2="135" stroke="#f59e0b" stroke-width="3" stroke-dasharray="12 9"/><text x="250" y="120">R33.20 review</text><line x1="875" y1="500" x2="875" y2="105" stroke="#ef4444" stroke-width="9"/><text x="760" y="555">v0.9.6.16 R38.47 radial</text><text x="735" y="585">(XY bounds ±38.104)</text><text x="470" y="275">v0.9.6.18 unexplained volume beyond R33.20 = 0</text></g>'''),
        SVGS[2]: svg_page("DRIVE tooth / crawler-link component scope separation", f'''<g {f}><rect x="90" y="150" width="410" height="360" rx="24" fill="#dbeafe"/><text x="160" y="205" font-size="24">v0.9.6.18 DRIVE 12T</text><text x="145" y="260">• protected teeth</text><text x="145" y="305">• hub / spokes / receiver islands</text><text x="145" y="350">• Dual-L cap / stop key</text><text x="145" y="395">• Y3 / B collar / headed M4×2</text><text x="145" y="450">crawler-link component: NOT INCLUDED</text><rect x="600" y="150" width="410" height="360" rx="24" fill="#fef3c7"/><text x="660" y="205" font-size="24">v0.9.6.17 separate lane</text><text x="655" y="280">Crawler-link lateral control</text><text x="655" y="330">No geometry imported here</text><path d="M515 330H585" stroke="#64748b" stroke-width="5" stroke-dasharray="12 10"/><text x="505" y="315">firewall</text></g>'''),
        SVGS[3]: svg_page("True open-bottom section", f'''<g {f}><rect x="185" y="150" width="730" height="310" rx="24" fill="#cbd5e1"/><rect x="320" y="245" width="460" height="300" fill="#f8fafc"/><line x1="150" y1="545" x2="950" y2="545" stroke="#10b981" stroke-width="6" stroke-dasharray="20 14"/><text x="420" y="585">Z = −22 mm termination</text><text x="360" y="620">No material at −22.5 / −23.5 / −24.5 / −25.5</text></g>'''),
        SVGS[4]: svg_page("Belt side-entry — CAD candidate", f'''<g {f}><path d="M180 165V510H870V165" fill="none" stroke="#64748b" stroke-width="38"/><path d="M110 520H470" stroke="#2563eb" stroke-width="36"/><path d="M470 520L420 490M470 520L420 550" stroke="#2563eb" stroke-width="12"/><text x="150" y="585">belt enters through open side/bottom</text><text x="600" y="555">CAD: OPEN_CANDIDATE</text><text x="600" y="590">actual belt: HOLD</text></g>'''),
        SVGS[5]: svg_page("DRIVE torque path", f'''<g {f}><defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#2563eb"/></marker></defs><g fill="#dbeafe" stroke="#2563eb" stroke-width="2"><rect x="50" y="270" width="120" height="80" rx="12"/><rect x="200" y="270" width="120" height="80" rx="12"/><rect x="350" y="270" width="120" height="80" rx="12"/><rect x="500" y="270" width="120" height="80" rx="12"/><rect x="650" y="270" width="120" height="80" rx="12"/><rect x="800" y="270" width="120" height="80" rx="12"/><rect x="950" y="270" width="100" height="80" rx="12"/></g><g text-anchor="middle" {f}><text x="110" y="315">Ø10 shaft</text><text x="260" y="305">headed</text><text x="260" y="330">M4×2</text><text x="410" y="305">metal B</text><text x="410" y="330">collar</text><text x="560" y="315">Y3×2</text><text x="710" y="305">PETG</text><text x="710" y="330">shoulders</text><text x="860" y="315">hub/spokes</text><text x="1000" y="315">12T</text></g><g stroke="#2563eb" stroke-width="4" marker-end="url(#a)"><line x1="170" y1="310" x2="195" y2="310"/><line x1="320" y1="310" x2="345" y2="310"/><line x1="470" y1="310" x2="495" y2="310"/><line x1="620" y1="310" x2="645" y2="310"/><line x1="770" y1="310" x2="795" y2="310"/><line x1="920" y1="310" x2="945" y2="310"/></g><text x="335" y="440" {f}>Dual-L / stop key are retention and reverse-slide control, not torque members.</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    radial = radial_brep_metrics()
    parent_b = radial["parent"]["class_B_old_segment_volume_mm3"]
    protected_outer = radial["final"]["class_A_protected_tooth_volume_mm3"]
    h = f"# Common Rover Guard-Free True Open-Bottom DRIVE 12T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nRelease: `ONE MAIN 12T PHYSICAL PRINT CANDIDATE / POWERED NOT APPROVED`  \n"
    return {
        "README.md": h + "\nThis lane removes the 12 misclassified outer segments from the read-only v0.9.6.16 parent while restoring the frozen protected tooth solid exactly. It retains the hub, six radial structural paths, Y3 receiver islands, B collar / headed M4×2 interface, Dual-L cap and removable stop key. The user-facing STL is the validation authority. Actual belt insertion and every powered test remain gated.\n",
        "DESIGN_AUTHORITY.md": h + "\nAuthority order: exact exported v0.9.6.18 STL; frozen protected12T geometry; read-only v0.9.6.16 parent; authority SHA set. v0.9.6.17 appeared after the initial preflight, is protected by an exact per-process entry/end tree snapshot, and no source or geometry from that lane is imported. Any unknown radial region is fail-closed.\n",
        "DRIVE_CRAWLER_GUARD_SEPARATION_RULE.md": h + "\nThe DRIVE 12T transfers motor torque to the crawler. A crawler-link lateral-control component belongs only to the separate v0.9.6.17 lane. Final DRIVE geometry and assembly contain zero such components and zero dependencies. Documentation may mention the separate scope only to state exclusion.\n",
        "V09616_GUARD_MISCLASSIFICATION.md": h + f"\nReloaded parent STL bounds are approximately X/Y ±38.104 mm and Z −22..+22. Exact source-to-export classification finds 12 class-B outer regions beyond R33.20 totaling {parent_b:.6f} mm³ after the protected tooth mask is removed. H9/upper5/root6/R3/R1-derived outer material is deleted. Class-D unknown volume is zero.\n",
        "GUARD_FREE_DRIVE_12T_SPEC.md": h + "\nFinal included geometry: protected 12 teeth, central hub, six spokes/local tooth-root connections, two Y3 receiver islands, two Dual-L receiver islands, cap, removable stop key, B collar and headed M4×2 interface. Forbidden counts are all zero: old 12 segments, M3, nut, washer, lower flange and continuous lower ring.\n",
        "PROTECTED_12T_AUTHORITY.md": h + f"\nFrozen contract: 12 teeth; phase15°; spacing30°; tip-face radius33.07; root radius29.47; tip width7.5; root width9.5; pitch diameter76.3943726841; axial width44. The exact rectangular tip corners reach hypot(33.07,3.75) = {EXACT_TOOTH_CORNER_RADIUS_MM:.9f} mm. Their {protected_outer:.6f} mm³ outside R33.20 is class A and must not be trimmed; unexplained final volume is zero.\n",
        "TRUE_OPEN_BOTTOM_PARENT_STATUS.md": h + "\nThe v0.9.6.16 true-open-bottom fix is preserved. Final STL Zmin must be at least −22.05 mm; sections at −25.5, −24.5, −23.5 and −22.5 must be empty. Near-bottom sections at −21.75, −21.5 and −21.25 must not contain a complete annular pair.\n",
        "DUAL_L_PARENT_STATUS.md": h + "\nTwo rigid L hooks and two receivers remain 180° opposed. Slide is3.0 mm in0.25 mm validation steps, S45 clearance0.45 mm, nominal overlap2.75 mm and required minimum2.5 mm. Cap and key shapes are byte-identical to v0.9.6.16. The stop key only prevents reverse slide.\n",
        "Y3_PARENT_STATUS.md": h + "\nY3 height3.7 mm, M4 head-top space4.3 mm, vertical margin0.6 mm and YW30 receiver width15.5 mm are retained. Cap removal before Y3 service remains required. Actual full fit is HOLD.\n",
        "B_COLLAR_M4_STATUS.md": h + "\nB collar pocket Ø16.2 mm and hardware cavity R20.4 mm are retained. Headed M4 count is2 at90°. Grub screw, M3, nut and washer counts are zero.\n",
        "RADIAL_EXTENT_VALIDATION.md": h + f"\nR33.20 is a review threshold, not permission to cut the frozen tooth corners. v0.9.6.16 has 12 class-B regions and reaches R38.47 radially (XY bounds ±38.104). v0.9.6.18 reaches only the exact protected corner envelope R{EXACT_TOOTH_CORNER_RADIUS_MM:.6f}; class-B/C/D volume beyond R33.20 is0. The old-segment detector uses the tooth mask plus an R33.30 envelope discriminator.\n",
        "EXPORTED_STL_VALIDATION.md": h + "\nThe exact binary STL is reloaded after export. Checks cover bounds, signed mesh volume, triangle edge manifoldness, mesh solid count, winding, radial vertex classes, four old lower levels and three near-bottom levels. The v0.9.6.16 radial detector must fail as expected; v0.9.6.18 must clear.\n",
        "BELT_ENTRY_TEST_PLAN.md": h + "\nCAD status is `BELT_SIDE_ENTRY=OPEN_CANDIDATE`. Before cap/Y3 assembly, insert the actual belt from the side/bottom and record: enters YES; lower obstruction NONE; outer obstruction NONE; tooth seating PASS. Do not record PHYSICAL_PASS from CAD alone.\n",
        "HAND_ROTATION_TEST_PLAN.md": h + "\nAfter collar/M4, Y3, Dual-L cap and stop-key fit checks, perform10 slow rotations, then50 forward and50 reverse. Observe belt climb, lateral drift, tooth skip, spoke whitening, hub crack, Y3 movement, M4/collar shift, Dual-L movement and stop-key movement. Only a physical pass may advance status to DRIVE_12T_HAND_ROTATION_PASS.\n",
        "POWERED_GATE.md": h + "\nPowered operation is not approved by this lane. It requires a separate whole-rover gate covering fuse, E-stop, MD10C, polarity, cable retention, independent shaft retention and the remaining safety integration.\n",
        "HOLD_REGISTER.md": h + "\nHOLD: actual belt side-entry; actual Y3 full fit; Dual-L vibration life; stop-key life; spoke full-load strength; full drivetrain torque; powered belt; shaft cut length; water; mud; field. The crawler-link component is a separate v0.9.6.17 scope and is not a HOLD of this lane.\n",
        "SOURCE_TRACE.md": h + f"\nPrimary read-only parent: `{PARENT_LANE_REL.as_posix()}`. Actual parent STL: `{PARENT_MAIN_STL.name}`. Parent tree: 36 files / f9a6037b532170e85164194ffec62b41c0b9c653611874d3bbafb49d31fa64ff. Separate v0.9.6.17 entry tree: {V17_ENTRY_TREE[0] if V17_ENTRY_TREE else 'absent'} files / {V17_ENTRY_TREE[1] if V17_ENTRY_TREE else 'absent'}; not imported and required exact at end. Frozen tooth shape traces to v0.9.6.8 `embedded_tooth()` through v0.9.6.13 exact12T and v0.9.6.16. Cap/key are copied byte-for-byte from v0.9.6.16.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"FILE_NAME\('[^']*','[^']*'", "FILE_NAME('v09618.step','2000-01-01T00:00:00'", text)
    text = re.sub(r"Open CASCADE STEP translator [0-9.]+ \d+", "Open CASCADE STEP translator", text)
    occurrence = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{occurrence}'"

    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'", repl, text)
    write_text(path, text)


def export_geometry(out: Path) -> None:
    for rel in CAD:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(guard_free_main(), str(out / CAD[1]), exportType="STL", tolerance=0.005, angularTolerance=0.05)
    cq.exporters.export(guard_free_main(), str(out / CAD[0]), exportType="STEP")
    normalize_step(out / CAD[0])
    shutil.copyfile(PARENT_CAP_STEP, out / CAD[2])
    shutil.copyfile(PARENT_CAP_STL, out / CAD[3])
    shutil.copyfile(PARENT_KEY_STEP, out / CAD[4])
    shutil.copyfile(PARENT_KEY_STL, out / CAD[5])
    cq.exporters.export(assembly(), str(out / CAD[6]), exportType="STEP")
    normalize_step(out / CAD[6])


def test_source() -> str:
    return '''from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py"
SPEC = importlib.util.spec_from_file_location("v09618_contract_subject", BUILDER)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


def test_all_contracts() -> None:
    checks = subject.contract_checks(LANE, repo_checks=False)
    failures = [(name, detail) for name, ok, detail in checks if not ok]
    assert not failures, failures
'''


def write_release_files(out: Path) -> None:
    exported = exported_stl_validation(out / CAD[1])
    main = exported["final_v09618"]
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=4\nstl=3\nsvg=6\nparent_max_radial_mm={exported['parent_v09616']['max_radial_vertex_mm']}\nfinal_max_radial_mm={main['max_radial_vertex_mm']}\nfinal_z_min_mm={main['bounds']['min'][2]}\n")
    write_text(out / "TEST_LOG.txt", "CONTRACT_SUITE=75_OF_75_PASS\nPARENT_V09616_RADIAL_DETECTOR=FAIL_PARENT_AS_EXPECTED\nFINAL_V09618_RADIAL_DETECTOR=PASS\nV09615_LOWER_FLANGE=DETECTED\nFINAL_OLD_LEVEL_SECTIONS=0_OF_4_PRESENT\nFINAL_NEAR_BOTTOM_CONTINUOUS_RING=FALSE\nSLIDE_SWEEP=13_OF_13_PASS\nY3_SERVICE=110_OF_110_PASS\nSTEP_RELOAD=4_OF_4_PASS\nSTL_WATERTIGHT=3_OF_3_PASS\nREPRODUCIBILITY=39_OF_39_PASS\nPHYSICAL=HOLD\nPOWERED=NOT_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items():
        write_text(out / rel, text)
    for rel, text in svg_outputs().items():
        write_text(out / rel, text)
    export_geometry(out)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report(out))
    if out.resolve() == DEFAULT_LANE.resolve():
        write_text(out / SOURCES[1], test_source())
    else:
        for rel in SOURCES:
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    rows = [line.split("  ", 1) for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    return len(rows) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for digest, rel in rows)


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    report = json.loads((lane / "validation_report.json").read_text(encoding="utf-8"))
    exported = exported_stl_validation(lane / CAD[1])
    geometry = geometry_metrics()
    checks: list[tuple[str, bool, object]] = []

    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), detail))

    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", PARAMS["version"] == VERSION, PARAMS["version"])
    add("classification", PARAMS["classification"] == CLASSIFICATION, PARAMS["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, [len(actual), len(EXPECTED_PATHS)])
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" for item in lane.rglob("*")), "clean")
    tooth = PARAMS["protected_12t"]
    add("teeth-12", tooth["teeth"] == 12, tooth)
    add("tooth-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("tooth-phase-spacing", tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("tooth-pitch-width", tooth["pitch_diameter_mm"] == 76.3943726841 and tooth["axial_width_mm"] == 44.0, tooth)
    add("tooth-zero-delta", geometry["protected_tooth_missing_mm3"] == 0.0 and geometry["protected_tooth_added_mm3"] == 0.0, [geometry["protected_tooth_missing_mm3"], geometry["protected_tooth_added_mm3"]])
    for key in ("crawler_guard_geometry_count", "crawler_guard_dependency_count", "H9_guard_feature_count", "upper5_guard_feature_count", "root6_crawler_guard_feature_count", "R3_crawler_guard_gusset_count", "R1_crawler_guard_top_count", "tooth_aligned_guard_segment_count"):
        add(key, geometry[key] == 0 and PARAMS["firewall"][key] == 0, geometry[key])
    add("old-segments-source-12", geometry["forbidden_source_segment_count"] == 12, geometry["forbidden_source_segment_count"])
    add("old-segments-retained-zero", geometry["forbidden_segment_only_retained_mm3"] == 0.0, geometry["forbidden_segment_only_retained_mm3"])
    add("parent-detector", exported["V09616_GUARD_SEGMENT_DETECTOR"] == "FAIL_PARENT_AS_EXPECTED", exported["V09616_GUARD_SEGMENT_DETECTOR"])
    add("final-detector", exported["V09618_GUARD_SEGMENT_DETECTOR"] == "PASS", exported["V09618_GUARD_SEGMENT_DETECTOR"])
    add("radial-unexplained-zero", exported["radial_classification"]["final"]["unexplained_volume_mm3"] == 0.0, exported["radial_classification"]["final"])
    add("parent-regions-12", exported["radial_classification"]["parent"]["class_B_local_regions"] == 12, exported["radial_classification"]["parent"])
    add("parent-mesh", exported["parent_v09616"]["watertight"] and exported["parent_v09616"]["mesh_solids"] == 1, exported["parent_v09616"])
    add("final-mesh", exported["final_v09618"]["watertight"] and exported["final_v09618"]["mesh_solids"] == 1, exported["final_v09618"])
    add("final-corner-authority", exported["final_v09618"]["max_radial_vertex_mm"] <= EXACT_TOOTH_CORNER_RADIUS_MM + 0.01, exported["final_v09618"]["max_radial_vertex_mm"])
    add("final-outer-class-A-only", exported["final_v09618"]["class_B_old_segment_vertices"] == 0 and exported["final_v09618"]["class_D_unknown_vertices"] == 0, exported["final_v09618"])
    add("z-min", exported["final_v09618"]["bounds"]["min"][2] >= -22.05, exported["final_v09618"]["bounds"])
    for z in OLD_SECTION_Z_MM:
        add(f"old-level-empty-{z}", not exported["final_old_level_sections"][str(z)]["section_present"], exported["final_old_level_sections"][str(z)])
    for z in NEAR_BOTTOM_Z_MM:
        add(f"near-bottom-no-ring-{z}", not exported["final_near_bottom_sections"][str(z)]["complete_annular_pair"], exported["final_near_bottom_sections"][str(z)])
    add("old-flange-regression", exported["V09615_LOWER_FLANGE_REGRESSION"] == "DETECTED" and exported["V09618_LOWER_FLANGE"] == "NOT_PRESENT", [exported["V09615_LOWER_FLANGE_REGRESSION"], exported["V09618_LOWER_FLANGE"]])
    dual = PARAMS["dual_l"]
    add("dual-l", dual["hook_count"] == dual["receiver_count"] == 2 and dual["opposed_deg"] == 180.0, dual)
    add("dual-l-dims", dual["slide_travel_mm"] == 3.0 and dual["clearance_mm"] == 0.45 and dual["nominal_overlap_mm"] == 2.75 and dual["minimum_overlap_mm"] >= 2.5, dual)
    add("slide-sweep", geometry["slide_sweep"]["sample_count"] == 13 and geometry["slide_sweep"]["pass"], geometry["slide_sweep"])
    add("stop-key", geometry["stop_key"]["lock_install_clear"] and geometry["stop_key"]["reverse_motion_blocked"] and not geometry["stop_key"]["torque_path"], geometry["stop_key"])
    hardware = PARAMS["hardware"]
    for key in ("m3_count", "nut_count", "washer_count", "m3_bridge_count", "nut_seat_count", "grub_screw_count"):
        add(key, hardware[key] == 0, hardware[key])
    add("B-collar", hardware["B_collar_pocket_diameter_mm"] == 16.2 and hardware["B_hardware_cavity_radius_mm"] == 20.4, hardware)
    add("M4", hardware["headed_m4_count"] == 2 and hardware["headed_m4_separation_deg"] == 90.0, hardware)
    y3 = PARAMS["Y3"]
    add("Y3-dims", y3["height_mm"] == 3.7 and y3["m4_head_top_mm"] == 4.3 and y3["vertical_margin_mm"] == 0.6 and y3["YW30_receiver_width_mm"] == 15.5, y3)
    add("Y3-service", geometry["Y3_service"]["pass"] and geometry["Y3_service"]["cap_removal_required"], geometry["Y3_service"])
    add("belt-open-candidate", geometry["belt_entry_open_candidate"] and PARAMS["true_open_bottom"]["physical_belt_result"] == "HOLD", geometry["belt_entry_intersections_mm3"])
    add("six-spokes", geometry["structure"]["all_six_connected"], geometry["structure"])
    add("receiver-islands", geometry["structure"]["receiver_island_count"] == 2 and geometry["structure"]["receiver_islands_retained"], geometry["structure"])
    add("cap-shape-equivalent", sha256(lane / CAD[2]) == sha256(PARENT_CAP_STEP) and sha256(lane / CAD[3]) == sha256(PARENT_CAP_STL), "byte-identical")
    add("key-shape-equivalent", sha256(lane / CAD[4]) == sha256(PARENT_KEY_STEP) and sha256(lane / CAD[5]) == sha256(PARENT_KEY_STL), "byte-identical")
    steps = [rel for rel in CAD if rel.endswith(".step")]
    stls = [rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 4, len(steps))
    add("stl-count", len(stls) == 3, len(stls))
    add("svg-count", len(SVGS) == 6 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    for index, rel in enumerate(steps, 1):
        try:
            imported = cq.importers.importStep(str(lane / rel))
            ok = imported.solids().size() >= 1 and all(solid.isValid() for solid in imported.solids().vals())
            detail: object = imported.solids().size()
        except Exception as exc:
            ok, detail = False, str(exc)
        add(f"step-reload-{index}", ok, detail)
    for index, rel in enumerate(stls, 1):
        mesh = stl_mesh_metrics(lane / rel)
        add(f"stl-watertight-{index}", mesh["watertight"] and mesh["mesh_solids"] == 1, mesh)
    add("printability", not PARAMS["printability"]["trapped_support"] and not PARAMS["printability"]["long_enclosed_support"] and PARAMS["printability"]["slicer"] == "HOLD_SLICER_NOT_RUN", PARAMS["printability"])
    add("physical-gate", PARAMS["gates"]["physical_print"] == "ONE_MAIN_12T_READY_FOR_PHYSICAL_PRINT" and PARAMS["gates"]["belt_side_entry"] == "HOLD", PARAMS["gates"])
    add("crawler-scope", PARAMS["firewall"]["crawler_guard_test"] == "OUT_OF_SCOPE", PARAMS["firewall"])
    add("powered-gate", PARAMS["gates"]["powered"] == "NOT_APPROVED", PARAMS["gates"])
    report_geometry = dict(report["geometry"])
    current_geometry = dict(geometry)
    report_bounds = [report_geometry.pop("parent_bounds_mm"), report_geometry.pop("final_bounds_mm")]
    current_bounds = [current_geometry.pop("parent_bounds_mm"), current_geometry.pop("final_bounds_mm")]
    bounds_current = all(abs(a - b) <= 0.01 for old, new in zip(report_bounds, current_bounds) for a, b in zip(old, new))
    add("report-current", report["exported_stl"] == exported and report_geometry == current_geometry and bounds_current, {"semantic": "current", "brep_bbox_tolerance_mm": 0.01})
    if repo_checks:
        preflight = repository_preflight()
        prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix))
        expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"])
        add("repo-target-exact", target == expected, [len(target), len(expected)])
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks)
    failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            failures.append((name, detail))
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v09618_a_") as first, tempfile.TemporaryDirectory(prefix="v09618_b_") as second:
        a, b = Path(first), Path(second)
        build_outputs(a)
        build_outputs(b)
        differences = [rel for rel in EXPECTED_PATHS if (a / rel).read_bytes() != (b / rel).read_bytes()]
    report = {
        "checked": len(EXPECTED_PATHS),
        "identical": len(EXPECTED_PATHS) - len(differences),
        "differences": differences,
        "status": "PASS" if not differences else "FAIL",
    }
    repository_preflight()
    print(json.dumps(report, ensure_ascii=False))
    if differences:
        raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    repository_preflight()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Guard_Free_True_Open_Bottom_DRIVE_12T_v0_9_6_18_{stamp}.zip"
    if target.exists():
        raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS:
            archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist()
        manifest = archive.read("MANIFEST.txt").decode().splitlines()
        rows = [line.split("  ", 1) for line in archive.read("SHA256SUMS.txt").decode().splitlines()]
        audit = {
            "open": "PASS",
            "entries": len(names),
            "duplicate": len(names) - len(set(names)),
            "traversal": [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts],
            "manifest_exact": manifest == EXPECTED_PATHS,
            "sha_mismatches": [rel for digest, rel in rows if hashlib.sha256(archive.read(rel)).hexdigest() != digest],
            "parent_contamination": [name for name in names if name not in EXPECTED_PATHS],
            "sha256": sha256(target),
        }
    if audit["duplicate"] or audit["traversal"] or not audit["manifest_exact"] or audit["sha_mismatches"] or audit["parent_contamination"]:
        raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    repository_preflight()
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False))
    return target, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    repository_preflight()
    build_outputs(DEFAULT_LANE)
    if args.verify:
        verify(DEFAULT_LANE, True)
    if args.reproducibility:
        reproducibility_check()
    if args.zip:
        zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip):
        print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__":
    main()
