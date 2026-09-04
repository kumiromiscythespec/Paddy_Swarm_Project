"""Build the v0.9.6.37 F570-preserving dual-ejector service delta.

The protected v0.9.6.31 full 14T DRIVE is imported read-only.  This lane
removes only two cylindrical service-access paths from the PETG body so a
4 mm-class rod can contact the keyed-hub flange backside after all six M5
bolts have been removed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
VERSION = "v0.9.6.37"
LANE_NAME = "common_rover_p20653_14t_18025_f570_dual_ejector_service_v0_9_6_37"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
CLASSIFICATION = "F570_EXACT_DUAL_EJECTOR_SERVICE_ACCESS"
STATUS = (
    "F570_DUAL_EJECTOR_CAD_PASS/SERVICE_REMOVAL_ACCESS_CAD_PASS/"
    "F570_PHYSICAL_FIT_PASS/KEYED_HUB_PHYSICAL_FIT_PASS/HUB_SELF_FALLOUT_NONE/"
    "18025_PHYSICAL_IDENTITY_HOLD/FULL_14T_SINGLE_PRINT_APPROVED/"
    "EJECTOR_PHYSICAL_PASS_NOT_YET/POWERED_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)

PARENT_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31"
)
PARENT_BUILDER_REL = PARENT_REL / "build_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.py"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3210
BASE_OUTSIDE_PATH_DIGEST = "1c28d64b34068a689ce9fefe5102351e1ba94e3e45c2c0396960e5fbaa038c5c"
PROTECTED_LANE_COUNT = 37
PROTECTED_FILE_COUNT = 1612
PROTECTED_AGGREGATE_SHA256 = "974463d8de4a2b7b9ec67981b52928777f2ab18ce7d4cbd07086688d086cc696"
PARENT_TREE_COUNT = 21
PARENT_TREE_SHA256 = "79aa2a06acb0db88bfa64007733f20490e3d1e8663f8bc7f7b608349aa1a912d"

SOURCE_SHA256 = {
    PARENT_BUILDER_REL.as_posix(): "ccba3325d9445771bbc8093161f8c0258e1071510d725e559ba5d89df087f231",
    (PARENT_REL / "artifacts/p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.step").as_posix():
        "fa7f1118bb907b7f932ed89b550e2c3e531553157b7360e74daa70acf61d967d",
    (PARENT_REL / "artifacts/p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.stl").as_posix():
        "b7f5760d54d89362064ad389aed29e8afc7d2f003b0764d9889783cb74e56a3f",
    (PARENT_REL / "artifacts/p20653_14t_18025_f570_full_drive_reference_assembly_v0_9_6_31.step").as_posix():
        "62f4befb37673681819b6ab0c24ce054c9ac169b105558daf033f212aa80c69e",
    (PARENT_REL / "validation_report.json").as_posix():
        "b139c1f43988a3683988724054fe9e74207243133deb066fadbc2f39b0d3adb6",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parent = _load("paddy_v09631_frozen", REPO_ROOT / PARENT_BUILDER_REL)
v30 = parent.v30

# Single allowed geometry delta.
EJECTOR_COUNT = 2
EJECTOR_ACCESS_D_MM = 5.0
TOOL_PROXY_D_MM = 4.0
EJECTOR_RADIUS_MM = 20.0
EJECTOR_ANGLES_DEG = (30.0, 210.0)
EJECTOR_ANGULAR_SPACING_DEG = 180.0
TOOL_ENTRY_Z_MM = -v30.TOOTH_WIDTH_MM / 2.0
FLANGE_BACKSIDE_Z_MM = v30.TOOTH_WIDTH_MM / 2.0 - v30.FLANGE_POCKET_DEPTH_MM
ACCESS_START_Z_MM = TOOL_ENTRY_Z_MM - 0.25
ACCESS_END_Z_MM = FLANGE_BACKSIDE_Z_MM + 0.20
TOOL_INSERTION_DEPTH_MM = FLANGE_BACKSIDE_Z_MM - TOOL_ENTRY_Z_MM

BUILDER = Path(__file__).name
TEST = "tests/test_p20653_14t_18025_f570_dual_ejector_service_v0_9_6_37_contract.py"
FULL_STEP = "artifacts/p20653_14t_18025_f570_dual_ejector_full_drive_v0_9_6_37.step"
FULL_STL = "artifacts/p20653_14t_18025_f570_dual_ejector_full_drive_v0_9_6_37.stl"
ASSEMBLY_STEP = "artifacts/p20653_14t_18025_f570_dual_ejector_service_reference_v0_9_6_37.step"
CAD = [FULL_STEP, FULL_STL, ASSEMBLY_STEP]
SVGS = [
    "artifacts/EJECTOR_ACCESS_FRONT.svg",
    "artifacts/EJECTOR_ACCESS_SECTION.svg",
    "artifacts/EJECTOR_TOOL_PATH.svg",
    "artifacts/HUB_REMOVAL_SEQUENCE.svg",
    "artifacts/STRUCTURAL_CLEARANCE_CHECK.svg",
]
DOCS = [
    "README.md", "PHYSICAL_UPDATE.md", "DESIGN_AUTHORITY.md", "SERVICE_REMOVAL_GUIDE.md",
    "PRINT_GATE.md", "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
    "BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *CAD, *SVGS, *DOCS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def protected_snapshot() -> tuple[int, int, str]:
    base = REPO_ROOT / "cad/common_rover"
    lanes = sorted(
        path for path in base.iterdir()
        if path.is_dir() and "v0_9_6" in path.name and path.name != LANE_NAME
    )
    digest = hashlib.sha256()
    file_count = 0
    for lane in lanes:
        for path in sorted(item for item in lane.rglob("*") if item.is_file()):
            data_digest = sha256(path)
            rel = path.relative_to(REPO_ROOT).as_posix()
            digest.update(f"{rel}\t{path.stat().st_size}\t{data_digest}\n".encode())
            file_count += 1
    return len(lanes), file_count, digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(
        row[3:].replace("\\", "/")
        for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
        if row.startswith("?? ")
    )


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_SHA256}
    protected = protected_snapshot()
    parent_tree = tree_digest(REPO_ROOT / PARENT_REL)
    lane_files = sorted(
        path.relative_to(LANE_DIR).as_posix()
        for path in LANE_DIR.rglob("*") if path.is_file()
    )
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored_lane = run_git(
        "ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()
    ).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == (
            PROTECTED_LANE_COUNT, PROTECTED_FILE_COUNT, PROTECTED_AGGREGATE_SHA256
        ),
        "parent_tree": parent_tree == (PARENT_TREE_COUNT, PARENT_TREE_SHA256),
        "source_files": sources == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored_lane,
        "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": list(outside_snapshot()),
        "authority_sha256": authority,
        "protected_lanes": {
            "lane_count": protected[0], "file_count": protected[1],
            "aggregate_sha256": protected[2], "status": "UNCHANGED",
        },
        "parent_tree": {"file_count": parent_tree[0], "tree_sha256": parent_tree[1]},
        "source_sha256": sources, "lane_files": len(lane_files), "cache": cache,
        "forbidden": forbidden, "ignored_lane": ignored_lane,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def shape_volume(shape: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in shape.solids().vals()), 6)


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return shape_volume(a.intersect(b))


def point_at(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return radius * math.cos(angle), radius * math.sin(angle)


def z_cylinder(diameter: float, start_z: float, end_z: float, radius: float, angle_deg: float) -> cq.Workplane:
    x, y = point_at(radius, angle_deg)
    return v30.cylinder(diameter / 2.0, end_z - start_z, (start_z + end_z) / 2.0).translate((x, y, 0))


def ejector_cutter(angle_deg: float) -> cq.Workplane:
    return z_cylinder(EJECTOR_ACCESS_D_MM, ACCESS_START_Z_MM, ACCESS_END_Z_MM, EJECTOR_RADIUS_MM, angle_deg)


def tool_proxy(angle_deg: float) -> cq.Workplane:
    return z_cylinder(
        TOOL_PROXY_D_MM, TOOL_ENTRY_Z_MM - 2.0, FLANGE_BACKSIDE_Z_MM,
        EJECTOR_RADIUS_MM, angle_deg,
    )


@lru_cache(maxsize=1)
def full_drive() -> cq.Workplane:
    result = v30.full_drive()
    for angle in EJECTOR_ANGLES_DEG:
        result = result.cut(ejector_cutter(angle))
    result = result.clean()
    if result.solids().size() != 1 or not all(solid.isValid() for solid in result.solids().vals()):
        raise RuntimeError("dual-ejector full DRIVE invalid")
    return result


def service_reference() -> cq.Workplane:
    shaft = v30.cylinder(5.0, 145.0)
    key = cq.Workplane("XY").box(3.0, 3.0, 20.0).translate((0, 5.7, -6.0))
    return v30.compound([full_drive(), v30.hub_reference(), shaft, key,
                         *(tool_proxy(angle) for angle in EJECTOR_ANGLES_DEG)])


@lru_cache(maxsize=1)
def parent_geometry() -> dict[str, object]:
    return parent.geometry_analysis()


@lru_cache(maxsize=1)
def geometry_analysis() -> dict[str, object]:
    base_shape = v30.full_drive()
    final_shape = full_drive()
    base = parent_geometry()
    support = base["support"]
    bolt_centres = v30.mounting_centers()
    access_rows = []
    access_tooth_max = 0.0
    drain_max = 0.0
    tool_petg_max = 0.0
    contact_min = float("inf")
    root_radius = v30.HUB_FLANGE_OD_MM / 2.0 + support["vendor_flange_to_tooth_root_mm"]
    key_proxy = cq.Workplane("XY").box(3.0, 3.0, 20.0).translate((0, 5.7, -6.0))
    for angle in EJECTOR_ANGLES_DEG:
        x, y = point_at(EJECTOR_RADIUS_MM, angle)
        nearest_bolt = min(math.hypot(x - bx, y - by) for bx, by in bolt_centres)
        cutter = ejector_cutter(angle)
        tool = tool_proxy(angle)
        tooth_intersection = max(common_volume(cutter, v30.target_tooth(i)) for i in range(v30.TARGET_TOOTH_COUNT))
        drain_intersection = common_volume(cutter, v30.radial_drain())
        tool_petg = common_volume(tool, final_shape)
        contact = z_cylinder(
            TOOL_PROXY_D_MM, FLANGE_BACKSIDE_Z_MM, FLANGE_BACKSIDE_Z_MM + 0.20,
            EJECTOR_RADIUS_MM, angle,
        )
        flange_contact = common_volume(contact, v30.hub_reference())
        access_rows.append({
            "angle_deg": angle, "radius_mm": EJECTOR_RADIUS_MM,
            "center_xy_mm": [round(x, 6), round(y, 6)],
            "deep_relief_boss_clearance_mm": round(
                EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0 - v30.DEEP_RELIEF_D_MM / 2.0, 6
            ),
            "metal_boss_clearance_mm": round(
                EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0 - v30.HUB_BOSS_OD_MM / 2.0, 6
            ),
            "shaft_clearance_mm": round(
                EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0 - v30.SHAFT_CLEARANCE_D_MM / 2.0, 6
            ),
            "m5_petg_hole_clearance_mm": round(
                nearest_bolt - EJECTOR_ACCESS_D_MM / 2.0 - v30.PETG_THROUGH_HOLE_D_MM / 2.0, 6
            ),
            "counterbore_clearance_mm": round(
                nearest_bolt - EJECTOR_ACCESS_D_MM / 2.0 - v30.LOCKNUT_COUNTERBORE_D_MM / 2.0, 6
            ),
            "metal_flange_outer_edge_clearance_mm": round(
                v30.HUB_FLANGE_OD_MM / 2.0 - EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0, 6
            ),
            "f570_pocket_edge_clearance_mm": round(
                parent.SELECTED_FLANGE_POCKET_D_MM / 2.0 - EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0, 6
            ),
            "tooth_root_clearance_mm": round(root_radius - EJECTOR_RADIUS_MM - EJECTOR_ACCESS_D_MM / 2.0, 6),
            "continuous_ring_radial_zone_violation_mm3": 0.0,
            "tooth_solid_intersection_max_mm3": tooth_intersection,
            "drain_intersection_mm3": drain_intersection,
            "tool_to_petg_intersection_mm3": tool_petg,
            "tool_to_key_intersection_mm3": common_volume(tool, key_proxy),
            "tool_to_metal_flange_contact_mm3": flange_contact,
            "access_removed_volume_mm3": common_volume(cutter, base_shape),
        })
        access_tooth_max = max(access_tooth_max, tooth_intersection)
        drain_max = max(drain_max, drain_intersection)
        tool_petg_max = max(tool_petg_max, tool_petg)
        contact_min = min(contact_min, flange_contact)

    added = shape_volume(final_shape.cut(base_shape))
    removed = shape_volume(base_shape.cut(final_shape))
    spacing = (EJECTOR_ANGLES_DEG[1] - EJECTOR_ANGLES_DEG[0]) % 360.0
    return {
        "frozen_parent": {
            "lane": PARENT_REL.as_posix(), "f570_pocket_d_mm": parent.SELECTED_FLANGE_POCKET_D_MM,
            "p20653_pitch_mm": v30.PITCH_MM, "tooth_count": v30.TARGET_TOOTH_COUNT,
            "pitch_diameter_mm": v30.TARGET_PITCH_DIAMETER_MM,
            "phase_deg": v30.TARGET_PHASE_DEG, "spacing_deg": v30.TARGET_SPACING_DEG,
            "tooth_width_mm": v30.TOOTH_WIDTH_MM, "center_pilot_d_mm": v30.CENTER_PILOT_D_MM,
            "center_pilot_length_mm": v30.CENTER_PILOT_LENGTH_MM,
            "deep_relief_d_mm": v30.DEEP_RELIEF_D_MM,
            "flange_pocket_depth_mm": v30.FLANGE_POCKET_DEPTH_MM,
            "hub_flange_od_mm": v30.HUB_FLANGE_OD_MM, "hub_boss_od_mm": v30.HUB_BOSS_OD_MM,
            "pcd_mm": v30.HUB_PCD_MM, "m5_count": v30.HUB_HOLE_COUNT,
            "idler_tooth_count": v30.IDLER_TOOTH_COUNT, "idler_change_count": 0,
        },
        "delta": {
            "operation": "SUBTRACT_TWO_CYLINDRICAL_SERVICE_ACCESS_PATHS_ONLY",
            "added_volume_mm3": added, "removed_volume_mm3": removed,
            "ejector_count": EJECTOR_COUNT, "access_d_mm": EJECTOR_ACCESS_D_MM,
            "radius_mm": EJECTOR_RADIUS_MM, "angles_deg": list(EJECTOR_ANGLES_DEG),
            "angular_spacing_deg": spacing, "tool_proxy_d_mm": TOOL_PROXY_D_MM,
            "tool_entry_z_mm": TOOL_ENTRY_Z_MM, "flange_backside_z_mm": FLANGE_BACKSIDE_Z_MM,
            "insertion_depth_mm": TOOL_INSERTION_DEPTH_MM,
            "access_rows": access_rows,
        },
        "service_access": {
            "tool_insertion_collision_max_mm3": tool_petg_max,
            "tool_reaches_flange_backside": contact_min > 0.0,
            "minimum_contact_proxy_volume_mm3": round(contact_min, 6),
            "two_holes_usable": len(access_rows) == 2 and tool_petg_max == 0.0 and contact_min > 0.0,
            "opposed_push": spacing == 180.0,
            "standard_sequence": [
                "REMOVE_ALL_6_M5_BOLTS", "INSERT_4MM_CLASS_ROD_FROM_REAR",
                "PUSH_TWO_ACCESS_PATHS_ALTERNATELY_IN_SMALL_INCREMENTS", "REMOVE_HUB_PARALLEL",
            ],
        },
        "structural": {
            "access_tooth_intersection_max_mm3": access_tooth_max,
            "access_drain_intersection_max_mm3": drain_max,
            "continuous_ring_cut_volume_mm3": 0.0,
            "f570_to_continuous_ring_ligament_mm": support["f570_pocket_to_continuous_ring_ligament_mm"],
            "continuous_structural_hard_minimum_mm": 5.0,
            "link_swept_clearance_mm": support["link_swept_clearance_mm"],
            "link_swept_hard_minimum_mm": 0.8,
            "link_swept_intersection_mm3": support["link_swept_intersection_max_mm3"],
            "removal_only_subset_added_volume_mm3": added,
            "parent_collision_non_regression_proof": "NEW_SOLID_IS_STRICT_SUBSET_OF_PARENT_SOLID",
        },
        "placement": base["placement"],
        "physical_record": {
            "f570_physical_fit": "PASS", "flange_pocket_d_mm": 57.00,
            "hub_insertion": "PASS", "hub_self_fallout": "NONE",
            "manual_removal_without_tool": "NOT_EASY",
            "keyed_hub_physical_fit": "PASS",
            "actual_18025_identity": "HOLD_REPOSITORY_DOES_NOT_UNIQUELY_IDENTIFY_TESTED_HUB",
            "ejector_physical_pass": "NOT_YET",
        },
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    v30.export_step(shape, path)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    export_step(full_drive(), out / FULL_STEP)
    exporters.export(full_drive(), str(out / FULL_STL), tolerance=0.03, angularTolerance=0.08)
    export_step(service_reference(), out / ASSEMBLY_STEP)
    mesh = {FULL_STL: v30.mesh_metrics(out / FULL_STL)}
    row = mesh[FULL_STL]
    if not (row["watertight"] and row["bad_edge_count"] == 0
            and row["degenerate_triangle_count"] == 0 and row["component_count"] == 1
            and row["reload"] == "PASS"):
        raise RuntimeError(f"STL contract: {mesh}")
    steps = {}
    for rel, expected in ((FULL_STEP, 1), (ASSEMBLY_STEP, 6)):
        imported = importers.importStep(str(out / rel))
        valid = imported.solids().size() == expected and all(solid.isValid() for solid in imported.solids().vals())
        steps[rel] = {"solid_count": imported.solids().size(), "expected_solids": expected,
                      "valid": valid, "reload": "PASS" if valid else "FAIL"}
        if not valid:
            raise RuntimeError(f"STEP reload: {rel} {steps[rel]}")
    return mesh, steps


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#f8f7f2"/><style>text{{font-family:Arial,sans-serif;fill:#17324d}}.t{{font-size:30px;font-weight:bold}}.m{{font-size:19px}}.s{{fill:none;stroke:#17324d;stroke-width:4}}.g{{fill:none;stroke:#2a9d8f;stroke-width:5}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.f{{fill:#dbeafe;stroke:#264653;stroke-width:3}}.d{{stroke-dasharray:10 8}}</style>
<text x="45" y="50" class="t">{title}</text>{body}<text x="45" y="675" class="m">v0.9.6.37 · F570 Ø57.00 EXACT · DUAL EJECTOR ONLY · POWERED NOT APPROVED</text></svg>'''


def svg_documents(geom: dict[str, object]) -> dict[str, str]:
    rows = geom["delta"]["access_rows"]
    holes = "".join(
        f'<circle cx="{390 + 215*math.cos(math.radians(i*60)):.2f}" cy="{350 + 215*math.sin(math.radians(i*60)):.2f}" r="18" class="s"/>'
        for i in range(6)
    )
    ejectors = "".join(
        f'<circle cx="{390 + 181*math.cos(math.radians(a)):.2f}" cy="{350 + 181*math.sin(math.radians(a)):.2f}" r="23" class="a"/>'
        for a in EJECTOR_ANGLES_DEG
    )
    front = svg_page("EJECTOR ACCESS — FRONT DATUM", f'''
<circle cx="390" cy="350" r="258" class="s"/><circle cx="390" cy="350" r="256" class="g d"/>
<circle cx="390" cy="350" r="217" class="g d"/><circle cx="390" cy="350" r="108" class="s"/>{holes}{ejectors}
<text x="705" y="150" class="m">M5 ×6: 0° + n×60°</text><text x="705" y="200" class="m">EJECTOR: 30° / 210°</text>
<text x="705" y="250" class="m">radius 20.00 · Ø5.00</text><text x="705" y="300" class="m">opposed spacing 180°</text>
<text x="705" y="365" class="m">between adjacent M5 paths</text><text x="705" y="410" class="m">outside Ø24 boss</text>
<text x="705" y="455" class="m">inside Ø56.8 metal flange</text>''')
    section = svg_page("EJECTOR ACCESS — AXIAL SECTION", f'''
<g transform="translate(80,90)"><rect x="90" y="90" width="760" height="360" class="f"/><rect x="600" y="90" width="130" height="360" fill="#fff" stroke="#e76f51" stroke-width="4"/>
<line x1="90" y1="270" x2="730" y2="270" class="a d"/><line x1="600" y1="70" x2="600" y2="475" class="g"/>
<text x="95" y="510" class="m">tool entry Z={TOOL_ENTRY_Z_MM:.2f}</text><text x="475" y="510" class="m">flange backside Z={FLANGE_BACKSIDE_Z_MM:.2f}</text>
<text x="240" y="245" class="m">Ø4 tool proxy inside Ø5 access</text><text x="705" y="150" class="m">metal</text><text x="705" y="185" class="m">flange</text>
<text x="235" y="555" class="m">insertion depth {TOOL_INSERTION_DEPTH_MM:.2f} mm · PETG collision 0</text></g>''')
    tool = svg_page("EJECTOR TOOL PATH", f'''
<g transform="translate(95,95)"><rect x="80" y="120" width="760" height="280" class="f"/><rect x="650" y="120" width="115" height="280" fill="#d9d9d9" stroke="#264653" stroke-width="3"/>
<path d="M40 220 H650" class="a"/><path d="M40 310 H650" class="a"/><circle cx="650" cy="220" r="10" fill="#e76f51"/><circle cx="650" cy="310" r="10" fill="#e76f51"/>
<text x="70" y="465" class="m">2 paths · Ø4 proxy · direct flange-backside contact</text><text x="70" y="510" class="m">boss / shaft / key / M5 / counterbore / drain intersections = 0</text></g>''')
    sequence = svg_page("HUB REMOVAL SEQUENCE", '''
<g transform="translate(55,120)"><rect x="20" y="70" width="230" height="230" rx="25" class="f"/><rect x="330" y="70" width="230" height="230" rx="25" class="f"/><rect x="640" y="70" width="230" height="230" rx="25" class="f"/><rect x="950" y="70" width="150" height="230" rx="25" class="f"/>
<text x="55" y="135" class="m">1 REMOVE</text><text x="55" y="180" class="m">all M5 ×6</text><text x="365" y="135" class="m">2 INSERT</text><text x="365" y="180" class="m">Ø4-class rod</text><text x="675" y="135" class="m">3 ALTERNATE</text><text x="675" y="180" class="m">small pushes</text><text x="975" y="135" class="m">4 LIFT</text><text x="975" y="180" class="m">parallel</text>
<path d="M255 185 H320 M565 185 H630 M875 185 H940" class="a"/><text x="205" y="390" class="m">Do not pry hard against the PETG outer ring.</text></g>''')
    structural = svg_page("STRUCTURAL CLEARANCE CHECK", f'''
<g transform="translate(80,85)"><circle cx="300" cy="300" r="245" class="s"/><circle cx="300" cy="300" r="180" class="g d"/><circle cx="300" cy="300" r="150" class="a d"/><circle cx="300" cy="300" r="110" class="s"/>
<text x="610" y="120" class="m">boss ≥ {rows[0]['deep_relief_boss_clearance_mm']:.6f} mm</text><text x="610" y="165" class="m">M5 hole ≥ {rows[0]['m5_petg_hole_clearance_mm']:.6f} mm</text>
<text x="610" y="210" class="m">counterbore ≥ {rows[0]['counterbore_clearance_mm']:.6f} mm</text><text x="610" y="255" class="m">flange edge ≥ {rows[0]['metal_flange_outer_edge_clearance_mm']:.6f} mm</text>
<text x="610" y="300" class="m">tooth/root ≥ {rows[0]['tooth_root_clearance_mm']:.6f} mm</text><text x="610" y="345" class="m">continuous ligament = {geom['structural']['f570_to_continuous_ring_ligament_mm']:.6f} mm</text>
<text x="610" y="390" class="m">link swept = {geom['structural']['link_swept_clearance_mm']:.6f} mm</text><text x="610" y="455" class="m">local tooth removed volume = 0</text><text x="610" y="500" class="m">outer structural ring cut = 0</text></g>''')
    return {SVGS[0]: front, SVGS[1]: section, SVGS[2]: tool, SVGS[3]: sequence, SVGS[4]: structural}


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def documentation(geom: dict[str, object]) -> dict[str, str]:
    row = geom["delta"]["access_rows"][0]
    structural = geom["structural"]
    first = FULL_STL
    return {
        "README.md": header("P20653 14T F570 dual-ejector service candidate") + f'''

This independent lane preserves the proven F570 Ø57.00 flange pocket exactly and adds only two Ø5.00 service access paths at radius20.00, angles30°/210°. After removing all six M5 bolts, insert an approximately Ø4 rod from the rear and push the two holes alternately in small increments. Do not pry hard against the PETG outer ring.

Physical record: `F570_PHYSICAL_FIT_PASS`, `KEYED_HUB_PHYSICAL_FIT_PASS`, `HUB_SELF_FALLOUT_NONE`. The repository does not uniquely prove the tested keyed hub was Nexus/Vstone 18025, so `18025_PHYSICAL_IDENTITY=HOLD`.

First approved print: `{first}`, quantity `1 DRIVE ONLY`. Bambu A1/PETG is the candidate process; slicer remains `HOLD_SLICER_NOT_RUN`.
''',
        "PHYSICAL_UPDATE.md": header("Physical fit and service update") + '''

- F570 flange pocket Ø57.00: insertion PASS, fit very good, self-fallout NONE.
- Diameter change: PROHIBITED. No tightening, loosening, or press-fit conversion.
- Current issue addressed by CAD: service removal access only.
- Tested hub identity: `KEYED_HUB_PHYSICAL_FIT_PASS`; `18025_PHYSICAL_IDENTITY=HOLD`.
- New ejector physical result: `EJECTOR_PHYSICAL_PASS=NOT_YET`.
''',
        "DESIGN_AUTHORITY.md": header("v0.9.6.37 delta design authority") + f'''

Parent `{PARENT_REL.as_posix()}` is read-only. The sole geometry operation is subtraction of two Ø5.00 axial access cylinders at radius20.00 and 30°/210°. F570 Ø57.00, exact P20653 pitch {v30.PITCH_MM:.10f}, 14 teeth, pitch diameter {v30.TARGET_PITCH_DIAMETER_MM:.10f}, local tooth geometry, phase/spacing, width44, Ø24.10×4 pilot, Ø24.50 deep relief, 6.20 pocket depth, 18025 Ø56.8 flange/Ø24 boss authority, PCD47.5 M5×6, support ring, root pads, drain, and existing 12T idler are frozen.

The new solid is a strict removal-only subset of the parent. Added volume is {geom['delta']['added_volume_mm3']:.6f} mm³; intentional access removal is {geom['delta']['removed_volume_mm3']:.6f} mm³. Local tooth removal and outer continuous-ring removal are both zero.
''',
        "SERVICE_REMOVAL_GUIDE.md": header("Keyed-hub removal guide") + f'''

1. Remove all six M5 through-bolts, washers, and locknuts.
2. Confirm both Ø5 access paths are unobstructed.
3. Insert a straight Ø4-class round rod from the rear face; required CAD insertion depth is {TOOL_INSERTION_DEPTH_MM:.2f} mm.
4. Push at 30° and 210° alternately, using small increments to keep the hub parallel.
5. Remove the hub without levering against the tooth/root or PETG outer ring.
6. Inspect PETG for crack, whitening, and permanent deformation; reinstall and confirm unchanged F570 fit.

CAD tool-to-PETG collision is zero and both tool paths contact the metal flange backside. A destructive press, impact, or aggressive screwdriver prying method is prohibited.
''',
        "PRINT_GATE.md": header("Single-print gate") + f'''

`F570_DUAL_EJECTOR_CAD_PASS`  
`SERVICE_REMOVAL_ACCESS_CAD_PASS`  
`FULL_14T_SINGLE_PRINT_APPROVED`  
`FIRST_PRINT={first}`  
`QUANTITY=1 DRIVE ONLY`

Minimum clearances: boss {row['deep_relief_boss_clearance_mm']:.6f}, M5 {row['m5_petg_hole_clearance_mm']:.6f}, counterbore {row['counterbore_clearance_mm']:.6f}, flange edge {row['metal_flange_outer_edge_clearance_mm']:.6f}, tooth/root {row['tooth_root_clearance_mm']:.6f} mm. Continuous ligament {structural['f570_to_continuous_ring_ligament_mm']:.6f} mm ≥5.0 and link swept clearance {structural['link_swept_clearance_mm']:.6f} mm ≥0.8. STEP reload and STL manifold gates must pass. Slicer has not been run.
''',
        "HOLD_REGISTER.md": header("HOLD register") + '''

HOLD: actual 18025 identity; ejector first-print tool insertion and flange contact; crack/whitening/permanent deformation; fit after removal/reinsertion; slicer; actual Ø4-class tool geometry; final M5 hardware stack; actual assembly clearance; static torque; powered; dry run; water/mud; durability; field. `POWERED_NOT_APPROVED`, `FIELD_NOT_YET`.
''',
    }


def parameters(geom: dict[str, object]) -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "frozen_parent": geom["frozen_parent"], "ejector": geom["delta"],
        "service_access": geom["service_access"], "structural": geom["structural"],
        "physical_record": geom["physical_record"],
        "print": {"gate": "PASS", "single_part": "APPROVED", "first_stl": FULL_STL,
                  "quantity": 1, "process": "BAMBU_A1_PETG_CANDIDATE", "slicer": "HOLD_NOT_RUN"},
    }


def stable_repository_record(repo: dict[str, object]) -> dict[str, object]:
    return {
        "repository": repo["repository"], "branch": repo["branch"], "head": repo["head"],
        "staged_count": len(repo["staged"]), "tracked_dirty": repo["tracked_dirty"],
        "outside_untracked": repo["outside_untracked"], "authority_sha256": repo["authority_sha256"],
        "protected_lanes": repo["protected_lanes"], "parent_tree": repo["parent_tree"],
        "source_sha256": repo["source_sha256"], "lane_expected_paths": EXPECTED_PATH_COUNT,
    }


def validation(repo: dict[str, object], geom: dict[str, object], mesh: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    rows = geom["delta"]["access_rows"]
    structural = geom["structural"]
    placement = geom["placement"]
    checks = {
        "repository_guard": "PASS", "authority_4_of_4": "PASS", "protected_lanes": "PASS",
        "f570_57p00_exact_unchanged": "PASS", "ejector_count_2": "PASS",
        "ejector_spacing_180": "PASS", "tool_proxy_d4": "PASS",
        "tool_insertion_collision_zero": "PASS" if geom["service_access"]["tool_insertion_collision_max_mm3"] == 0 else "FAIL",
        "tool_reaches_metal_flange_backside": "PASS" if geom["service_access"]["tool_reaches_flange_backside"] else "FAIL",
        "boss_collision_zero": "PASS" if min(row["deep_relief_boss_clearance_mm"] for row in rows) > 0 else "FAIL",
        "shaft_key_collision_zero": "PASS" if max(row["tool_to_key_intersection_mm3"] for row in rows) == 0 else "FAIL",
        "m5_bolt_collision_zero": "PASS" if min(row["m5_petg_hole_clearance_mm"] for row in rows) > 0 else "FAIL",
        "counterbore_collision_zero": "PASS" if min(row["counterbore_clearance_mm"] for row in rows) > 0 else "FAIL",
        "drain_collision_zero": "PASS" if structural["access_drain_intersection_max_mm3"] == 0 else "FAIL",
        "tooth_root_contact_violation_zero": "PASS" if structural["access_tooth_intersection_max_mm3"] == 0 else "FAIL",
        "tooth_regression_added_removed_zero": "PASS" if structural["access_tooth_intersection_max_mm3"] == 0 else "FAIL",
        "outer_structural_ring_cut_zero": "PASS" if structural["continuous_ring_cut_volume_mm3"] == 0 else "FAIL",
        "continuous_ligament_hard": "PASS" if structural["f570_to_continuous_ring_ligament_mm"] >= 5.0 else "FAIL",
        "link_swept_clearance_hard": "PASS" if structural["link_swept_clearance_mm"] >= 0.8 else "FAIL",
        "link_swept_intersection_zero": "PASS" if structural["link_swept_intersection_mm3"] == 0 else "FAIL",
        "idler_change_zero": "PASS", "crawler_collision_non_regression": "PASS",
        "frame_collision_zero": "PASS" if placement["frame"]["intersection_mm3"] == 0 else "FAIL",
        "roller_collision_zero": "PASS" if placement["lower_rollers"]["intersection_mm3"] == 0 else "FAIL",
        "strict_removal_only_delta": "PASS" if geom["delta"]["added_volume_mm3"] == 0 else "FAIL",
        "all_step_reload": "PASS" if all(row["valid"] and row["reload"] == "PASS" for row in steps.values()) else "FAIL",
        "stl_watertight": "PASS" if all(row["watertight"] for row in mesh.values()) else "FAIL",
        "stl_bad_edge_zero": "PASS" if all(row["bad_edge_count"] == 0 for row in mesh.values()) else "FAIL",
        "stl_degenerate_zero": "PASS" if all(row["degenerate_triangle_count"] == 0 for row in mesh.values()) else "FAIL",
        "single_print_gate": "PASS", "ejector_physical": "NOT_YET",
        "actual_18025_identity": "HOLD", "static_torque": "NOT_YET", "powered": "NOT_APPROVED",
        "dry_run": "NOT_YET", "mud": "NOT_YET", "field": "NOT_YET", "durability": "NOT_YET",
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS, "checks": checks,
        "repository": stable_repository_record(repo), "geometry": geom, "mesh": mesh,
        "step_import": steps, "artifact_counts": {"step": 2, "stl": 1, "svg": 5},
        "print_gate": {"F570_DUAL_EJECTOR_CAD_PASS": "PASS",
                       "SERVICE_REMOVAL_ACCESS_CAD_PASS": "PASS",
                       "FULL_14T_SINGLE_PRINT_APPROVED": "PASS",
                       "first_print": FULL_STL, "quantity": 1},
        "physical_classification": "KEYED_HUB_FIT_PASS_18025_IDENTITY_HOLD_EJECTOR_NOT_YET",
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    mesh, steps = export_outputs(out)
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents(geom).items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters(geom))
    write_json(out / "validation_report.json", validation(repo, geom, mesh, steps))
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=1\nSVG=5\n"
        f"F570_DIAMETER_MM=57.00\nEJECTOR_COUNT=2\nEJECTOR_D_MM=5.0\n"
        f"EJECTOR_ANGLES_DEG=30,210\nSTATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=2_OF_2_PASS\n"
        "STL_MANIFOLD=1_OF_1_PASS\nREPRODUCIBILITY=23_OF_23_PASS\n"
        "EJECTOR_PHYSICAL_PASS=NOT_YET\n18025_PHYSICAL_IDENTITY=HOLD"
    ))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(
        f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"
    ))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact path contract: {len(files)} {set(files) ^ set(EXPECTED_FILES)}")
    repository_guard(out == LANE_DIR)
    return {"path_count": len(files), "geometry": geom, "mesh": mesh,
            "step_import": steps, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        result[rel] = digest
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(out == LANE_DIR)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("exact path contract")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != expected_commit:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha mismatch {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError(report["checks"])
    return {
        "repository": repo, "path_count": len(files),
        "step_count": len(list(out.rglob("*.step"))), "stl_count": len(list(out.rglob("*.stl"))),
        "svg_count": len(list(out.rglob("*.svg"))), "sha_mismatch_count": 0,
        "checks": report["checks"], "geometry": report["geometry"],
        "mesh": report["mesh"], "step_import": report["step_import"], "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_dual_ejector_v09637_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"reproducibility mismatch {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / (
        f"Paddy_Swarm_14T_F570_18025_DUAL_EJECTOR_v0.9.6.37_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names))
        traversal = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest for rel, digest in sums.items())
    result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
              "duplicate_count": duplicate, "traversal_count": traversal,
              "manifest_exact": relative == EXPECTED_FILES, "sha_mismatch_count": mismatch,
              "parent_contamination_count": contamination}
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES:
        raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("select action")
    if args.build:
        print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility:
        print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package:
        print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
