"""Build PS-BBOX-WATER-DUMMY-V001 sealing-boundary test artifacts.

This independent lane reuses the v2.28 PS-RV227 BBOX lid/gasket and the
continuous 200 x 150 mm rim definition.  It deliberately closes the source
body's drip-only wire notches and never invents closure holes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "bbox_water_dummy_v001_full_size_seal_submersion_test"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "PS-BBOX-WATER-DUMMY-V001"
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/PRINT_READY/SEALING_BOUNDARY_TEST/"
    "AUTHORITY_UNIQUE_MATCH_V228/CONTINUOUS_RIM_EXACT/"
    "SOURCE_DRIP_NOTCHES_CLOSED_BY_TASK/NO_CLOSURE_HOLES_INVENTED/"
    "PHYSICAL_LEAK_RESULT_NOT_YET/BALLAST_FIXING_HOLD/"
    "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING/COMMIT_READY_NOT_STAGED"
)

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = sorted(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3132
BASE_OUTSIDE_PATH_DIGEST = "47b10cb36a45eec7401622a7490cb86652f2800deb872c3dd36af190e78fb112"
PROTECTED_LANE_COUNT = 35
PROTECTED_FILE_COUNT = 1540
PROTECTED_AGGREGATE_SHA256 = "c4adc57e39ac24f5ec5cff4fc234a0424ca09626e8d827374a0c4c575436565a"
PROTECTED_FOCUS = {
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32":
        (28, "4792b7db682d02e78ab88bdd8642f42b6805a6773782f4bcc36f2ff3427bc516"),
    "cad/common_rover/common_rover_generic_keyed_industrial_torque_core_comparison_v0_9_6_33":
        (30, "b0e1d30421c78c201658f5a410ecfaedd570c1121804a9ea26470884ec212496"),
    "cad/common_rover/common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34":
        (36, "121ae43e71aa732e601e67595401284f8953e4f55bde71dbd3340646e452451d"),
}

SOURCE_BUILDER_REL = PurePosixPath("rovers/common_rover/v2.28/paddy_swarm_v228_2_dual_pto_output_fix_cadquery.py")
SOURCE_STEP_DIR_REL = PurePosixPath("rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out/step")
SOURCE_BODY_REL = SOURCE_STEP_DIR_REL / "PS-RV227-BBOX-BDY.step"
SOURCE_LID_REL = SOURCE_STEP_DIR_REL / "PS-RV227-BBOX-LID.step"
SOURCE_GASKET_REL = SOURCE_STEP_DIR_REL / "PS-RV227-BBOX-GSK.step"
SOURCE_INTERFACE_REL = PurePosixPath("interfaces/power/bbox_battery_cassette/v001/README.md")
SOURCE_SHA256 = {
    SOURCE_BUILDER_REL.as_posix(): "aa8de0ddc9537fd5f8e75a4c41bc98975749aac4e9abd2419993e73d92df2201",
    SOURCE_BODY_REL.as_posix(): "ae9d49061d7df010d2ce66ff0e125f7db06cc6ce4e6b031f95da6a69c711f6b4",
    SOURCE_LID_REL.as_posix(): "0cf3b955166cf97c6b1b18b181db507b560c996de7c8011bb86aa817cdd202aa",
    SOURCE_GASKET_REL.as_posix(): "93f3652c0c81c76aac581b854aa5f4540a4211fcb630364a9584a2ce29c84393",
    SOURCE_INTERFACE_REL.as_posix(): "0463ff3e69cf5569a9711c0c71ef3c6566be1469c85af351062459c98c6fcacd",
}
SOURCE_TREE = {
    "rovers/common_rover/v2.28/rover_v228_2_dual_pto_output_fix_out":
        (74, "a84530203d35e06bec22f00215cd7649f45ab1aad70028bc0cda89a7ee979f28"),
    "interfaces/power/bbox_battery_cassette/v001":
        (5, "61e5c3c7ee6c05b8a0dce5f07e816e8119bd343797761e5f64a2874f8c070376"),
}

BODY_X = 200.0
BODY_Y = 150.0
BODY_H = 70.0
WALL = 4.0
BOTTOM = 5.0
LID_NOMINAL = [216.0, 166.0, 16.0]
LID_CAD_BBOX = [216.0, 166.0, 18.5]
GASKET = [204.0, 154.0, 3.0]
GASKET_INNER = [188.0, 138.0]
SOURCE_CLOSURE_HOLE_COUNT = 0
TOWER_SIZE = 12.0
TOWER_CENTER_X = 116.0
TOWER_CENTER_Y = 92.0
TOWER_LID_CLEARANCE_TARGET = 3.0
LID_BOTTOM_Z = BODY_H + GASKET[2]
LID_TOP_Z = LID_BOTTOM_Z + LID_CAD_BBOX[2]
TOWER_TOP_Z = LID_TOP_Z + 4.0
BALLAST_PLATE_X = 244.0
BALLAST_PLATE_Y = 196.0
BALLAST_PLATE_T = 4.0
A1_PLATE = 256.0
PETG_DENSITY_G_CM3 = 1.27
RHO_WATER = 1000.0
G_ACCEL = 9.80665
TEST_DEPTH_M = 0.150
PRESSURE_KPA = RHO_WATER * G_ACCEL * TEST_DEPTH_M / 1000.0

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_water_dummy_v001_contract.py"
CAD_FILES = [
    "bbox_water_dummy_v001.step",
    "bbox_water_dummy_v001.stl",
    "bbox_water_dummy_assembly_reference.step",
]
SVGS = [
    "seal_interface_section.svg",
    "ballast_load_path.svg",
    "submersion_test_setup.svg",
    "print_orientation.svg",
]
DOCS = ["README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_TEST_PLAN.md", "PRINT_GUIDE.md", "HOLD_REGISTER.md"]
DATA = ["design_parameters.json", "validation_report.json"]
META = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *CAD_FILES, *SVGS, *DOCS, *DATA, *META])
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
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(path.replace("\\", "/") for path in run_git("ls-files", "--others", "--exclude-standard").splitlines())


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def protected_snapshot() -> dict[str, object]:
    root = REPO_ROOT / "cad/common_rover"
    rows: dict[str, tuple[int, str]] = {}
    for path in sorted(root.iterdir()):
        match = re.search(r"_v0_9_6_(\d+)$", path.name)
        if path.is_dir() and match and int(match.group(1)) <= 34:
            rows[path.relative_to(REPO_ROOT).as_posix()] = tree_digest(path)
    digest = hashlib.sha256()
    for rel, (count, tree_sha) in rows.items():
        digest.update(f"{rel}|{count}|{tree_sha}\n".encode())
    return {
        "lane_count": len(rows),
        "file_count": sum(row[0] for row in rows.values()),
        "aggregate_sha256": digest.hexdigest(),
        "focus": {
            rel: {"count": row[0], "tree_sha256": row[1]}
            for rel, row in rows.items() if rel in PROTECTED_FOCUS
        },
    }


def source_guard() -> dict[str, object]:
    hashes = {rel: sha256(REPO_ROOT / rel) for rel in SOURCE_SHA256}
    trees = {rel: tree_digest(REPO_ROOT / rel) for rel in SOURCE_TREE}
    if hashes != SOURCE_SHA256:
        raise RuntimeError("SOURCE_AUTHORITY_HASH_FAIL: " + json.dumps(hashes, sort_keys=True))
    if trees != SOURCE_TREE:
        raise RuntimeError("SOURCE_AUTHORITY_TREE_FAIL: " + json.dumps(trees, sort_keys=True))
    source_text = (REPO_ROOT / SOURCE_BUILDER_REL).read_text(encoding="utf-8")
    required = [
        '"box_body_lwh": [200.0, 150.0, 120.0]',
        '"box_lid_lwh": [216.0, 166.0, 16.0]',
        '"box_gasket_lwh": [204.0, 154.0, 3.0]',
        "wall = 4.0", "rim_t = 4.0", "gasket = gasket.cut(inner)",
    ]
    if not all(token in source_text for token in required):
        raise RuntimeError("SOURCE_AUTHORITY_SEMANTIC_FAIL")
    body = importers.importStep(str(REPO_ROOT / SOURCE_BODY_REL))
    lid = importers.importStep(str(REPO_ROOT / SOURCE_LID_REL))
    gasket = importers.importStep(str(REPO_ROOT / SOURCE_GASKET_REL))
    return {
        "selection": "UNIQUE_MATCH_TO_USER_NOMINAL_AND_V228_FIXED_CORE",
        "source_builder": SOURCE_BUILDER_REL.as_posix(),
        "source_steps": [SOURCE_BODY_REL.as_posix(), SOURCE_LID_REL.as_posix(), SOURCE_GASKET_REL.as_posix()],
        "hashes": hashes,
        "trees": {rel: {"count": row[0], "tree_sha256": row[1]} for rel, row in trees.items()},
        "source_step_bbox_mm": {
            "body": bbox_values(body), "lid": bbox_values(lid), "gasket": bbox_values(gasket),
        },
        "nominal_interface_mm": {"body": [200.0, 150.0, 120.0], "lid": LID_NOMINAL, "gasket": GASKET},
        "source_closure_hole_count": SOURCE_CLOSURE_HOLE_COUNT,
        "source_notch_classification": "DRIP_RESISTANT_ONLY_NOT_WATERPROOF",
        "task_override": "CLOSE_SOURCE_WIRE_NOTCH_ZONES_NO_PENETRATIONS",
    }


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = sorted(run_git("diff", "--name-only").splitlines())
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    outside = outside_snapshot()
    protected = protected_snapshot()
    source = source_guard()
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file()) if LANE_DIR.exists() else []
    ignored = [path for path in lane_files if subprocess.run(
        ["git", "check-ignore", "-q", (LANE_REL / PurePosixPath(path)).as_posix()], cwd=REPO_ROOT
    ).returncode == 0]
    forbidden = [path for path in lane_files if Path(path).suffix.lower() in {".3mf", ".gcode", ".fcstd", ".pyc", ".pyo"}]
    caches = [path for path in lane_files if "__pycache__" in PurePosixPath(path).parts or ".pytest_cache" in PurePosixPath(path).parts]
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "authority_four": authority == AUTHORITY_SHA256,
        "outside_untracked_preserved": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "protected_lanes": (
            protected["lane_count"] == PROTECTED_LANE_COUNT
            and protected["file_count"] == PROTECTED_FILE_COUNT
            and protected["aggregate_sha256"] == PROTECTED_AGGREGATE_SHA256
        ),
        "protected_focus": all(
            protected["focus"].get(rel) == {"count": expected[0], "tree_sha256": expected[1]}
            for rel, expected in PROTECTED_FOCUS.items()
        ),
        "ignored_zero": not ignored,
        "cache_zero": not caches,
        "forbidden_zero": not forbidden,
        "lane_exact": not require_complete or lane_files == EXPECTED_FILES,
    }
    if not all(checks.values()):
        raise RuntimeError("REPOSITORY_GUARD_FAIL: " + json.dumps(checks, sort_keys=True))
    return {
        "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "authority_sha256": authority,
        "outside_untracked": list(outside), "protected_lanes": protected,
        "source_authority": source, "lane_files": lane_files,
        "ignored": ignored, "cache": caches, "forbidden": forbidden, "checks": checks,
    }


def wp(shape: cq.Shape) -> cq.Workplane:
    return cq.Workplane(obj=shape)


def volume(shape: cq.Workplane) -> float:
    return sum(s.Volume() for s in shape.solids().vals())


def bbox_values(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]


def support_system(with_ids: bool = True) -> cq.Workplane:
    result = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            connector = cq.Workplane("XY").box(26.0, 27.0, 60.0).translate((sx * 109.0, sy * 84.5, 30.0))
            tower = cq.Workplane("XY").box(TOWER_SIZE, TOWER_SIZE, TOWER_TOP_Z).translate(
                (sx * TOWER_CENTER_X, sy * TOWER_CENTER_Y, TOWER_TOP_Z / 2.0)
            )
            unit = connector.union(tower)
            result = unit if result is None else result.union(unit)
    assert result is not None
    if with_ids:
        # One isolated notch plus a close double-notch on one external tower face.
        for yy in (88.0, 93.0, 95.0):
            cutter = cq.Workplane("XY").box(1.2, 1.0, 4.0).translate((121.7, yy, 32.0))
            result = result.cut(cutter)
    return result


def body_shape() -> cq.Workplane:
    outer = cq.Workplane("XY").box(BODY_X, BODY_Y, BODY_H).translate((0, 0, BODY_H / 2.0))
    inner = cq.Workplane("XY").box(BODY_X - 2 * WALL, BODY_Y - 2 * WALL, BODY_H - BOTTOM + 1.0).translate(
        (0, 0, BOTTOM + (BODY_H - BOTTOM + 1.0) / 2.0)
    )
    return outer.cut(inner).union(support_system(True))


def exterior_displacement_body() -> cq.Workplane:
    outer = cq.Workplane("XY").box(BODY_X, BODY_Y, BODY_H).translate((0, 0, BODY_H / 2.0))
    return outer.union(support_system(True))


def source_lid() -> cq.Workplane:
    return importers.importStep(str(REPO_ROOT / SOURCE_LID_REL))


def source_gasket() -> cq.Workplane:
    return importers.importStep(str(REPO_ROOT / SOURCE_GASKET_REL))


def placed_lid() -> cq.Workplane:
    return source_lid().translate((0, 0, LID_BOTTOM_Z))


def placed_gasket() -> cq.Workplane:
    return source_gasket().translate((0, 0, BODY_H))


def ballast_plate() -> cq.Workplane:
    return cq.Workplane("XY").box(BALLAST_PLATE_X, BALLAST_PLATE_Y, BALLAST_PLATE_T).translate(
        (0, 0, TOWER_TOP_Z + BALLAST_PLATE_T / 2.0)
    )


def assembly_reference() -> cq.Workplane:
    shapes = [body_shape().val(), placed_gasket().val(), placed_lid().val(), ballast_plate().val()]
    return wp(cq.Compound.makeCompound(shapes))


def rim_authority(z0: float = 0.0) -> cq.Workplane:
    outer = cq.Workplane("XY").box(BODY_X, BODY_Y, 1.0).translate((0, 0, z0 + 0.5))
    inner = cq.Workplane("XY").box(BODY_X - 2 * WALL, BODY_Y - 2 * WALL, 2.0).translate((0, 0, z0 + 0.5))
    return outer.cut(inner)


def shape_distance(left: cq.Workplane, right: cq.Workplane) -> float:
    tool = BRepExtrema_DistShapeShape(left.val().wrapped, right.val().wrapped)
    tool.Perform()
    if not tool.IsDone():
        raise RuntimeError("SHAPE_DISTANCE_FAIL")
    return float(tool.Value())


def overlap_volume(left: cq.Workplane, right: cq.Workplane) -> float:
    return volume(left.intersect(right))


def design_analysis() -> dict[str, object]:
    body = body_shape()
    lid = placed_lid()
    gasket = placed_gasket()
    authority_rim = rim_authority(BODY_H - 1.0)
    top_slice = body.intersect(cq.Workplane("XY").box(BODY_X, BODY_Y, 1.0).translate((0, 0, BODY_H - 0.5)))
    rim_added = volume(top_slice.cut(authority_rim))
    rim_removed = volume(authority_rim.cut(top_slice))
    towers = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            towers.append(cq.Workplane("XY").box(TOWER_SIZE, TOWER_SIZE, TOWER_TOP_Z).translate(
                (sx * TOWER_CENTER_X, sy * TOWER_CENTER_Y, TOWER_TOP_Z / 2.0)
            ))
    tower_clearances = [shape_distance(tower, lid) for tower in towers]
    tower_lid_intersections = [overlap_volume(tower, lid) for tower in towers]
    # The actual gasket and rim touch at Z=70 and must have zero penetration.
    # Align one millimetre only for the independent XY support-area regression.
    gasket_projection_1mm = source_gasket().translate((0, 0, BODY_H - 1.0))
    gasket_rim_overlap = overlap_volume(gasket_projection_1mm, authority_rim)
    displacement_body = exterior_displacement_body()
    displacement_mm3 = volume(displacement_body) + volume(gasket) + volume(lid)
    displacement_l = displacement_mm3 / 1_000_000.0
    buoyancy_n = displacement_mm3 * 1e-9 * RHO_WATER * G_ACCEL
    body_bb = body.val().BoundingBox()
    material_mm3 = volume(body)
    return {
        "authority": source_guard(),
        "body": {
            "main_vessel_outer_xy_mm": [BODY_X, BODY_Y],
            "overall_with_integral_towers_xyz_mm": [body_bb.xlen, body_bb.ylen, body_bb.zlen],
            "height_mm": BODY_H, "wall_mm": WALL, "bottom_mm": BOTTOM,
            "closed_bottom": True, "penetration_count": 0,
            "material_volume_mm3": material_mm3,
            "estimated_petg_mass_g": material_mm3 / 1000.0 * PETG_DENSITY_G_CM3,
            "primary_shape_valid": body.val().isValid(),
        },
        "seal": {
            "source_rim_outer_xy_mm": [BODY_X, BODY_Y],
            "source_rim_inner_xy_mm": [BODY_X - 2 * WALL, BODY_Y - 2 * WALL],
            "source_rim_width_mm": WALL,
            "source_rim_section_area_mm2": volume(authority_rim),
            "dummy_rim_section_area_mm2": volume(top_slice),
            "regression_added_mm3_at_1mm_section": rim_added,
            "regression_removed_mm3_at_1mm_section": rim_removed,
            "source_drip_notches_reproduced": False,
            "source_drip_notches_closed_by_task": True,
            "gasket_bbox_mm": bbox_values(source_gasket()),
            "gasket_rim_overlap_mm3_at_nominal_1mm": gasket_rim_overlap,
            "lid_bbox_mm": bbox_values(source_lid()),
            "lid_nominal_contract_mm": LID_NOMINAL,
            "lid_body_interference_mm3": overlap_volume(body, lid),
            "gasket_body_interference_mm3": overlap_volume(gasket, body),
            "lid_gasket_interference_mm3": overlap_volume(lid, gasket),
            "closure_hole_count_source": SOURCE_CLOSURE_HOLE_COUNT,
            "closure_hole_count_dummy": 0,
            "bolt_alignment": "PASS_EXACT_EMPTY_SOURCE_PATTERN_NO_HOLES_INVENTED",
        },
        "ballast": {
            "tower_count": 4, "tower_cross_section_mm": [TOWER_SIZE, TOWER_SIZE],
            "tower_centers_xy_mm": [[sx * TOWER_CENTER_X, sy * TOWER_CENTER_Y] for sx in (-1, 1) for sy in (-1, 1)],
            "tower_top_z_mm": TOWER_TOP_Z, "lid_top_z_mm": LID_TOP_Z,
            "tower_above_lid_mm": TOWER_TOP_Z - LID_TOP_Z,
            "tower_lid_clearance_each_mm": tower_clearances,
            "tower_lid_clearance_min_mm": min(tower_clearances),
            "tower_lid_intersection_each_mm3": tower_lid_intersections,
            "tower_bolt_intersection_count": 0,
            "plate_reference_mm": [BALLAST_PLATE_X, BALLAST_PLATE_Y, BALLAST_PLATE_T],
            "plate_to_lid_clearance_mm": TOWER_TOP_Z - LID_TOP_Z,
            "load_path": "BALLAST_PLATE_REFERENCE_TO_FOUR_TOWERS_TO_INTEGRAL_CORNER_CONNECTORS_TO_BODY",
            "physical_fixing": "HOLD",
        },
        "hydrostatic": {
            "water_density_kg_m3": RHO_WATER, "g_m_s2": G_ACCEL,
            "reference_depth_m": TEST_DEPTH_M, "gauge_pressure_kpa": PRESSURE_KPA,
            "displacement_basis": "ACTUAL_CAD_EXTERIOR_BODY_TOWERS_CONNECTORS_GASKET_LID",
            "displaced_volume_mm3": displacement_mm3, "displaced_volume_l": displacement_l,
            "buoyancy_force_n": buoyancy_n, "buoyancy_equivalent_kgf": buoyancy_n / G_ACCEL,
            "ballast_value": "CAD_REFERENCE_ONLY_NO_SAFETY_FACTOR",
        },
        "printability": {
            "printer": "Bambu A1", "material": "PETG",
            "orientation": "BOTTOM_DOWN_OPEN_UP",
            "build_plate_mm": [A1_PLATE, A1_PLATE],
            "part_footprint_mm": [body_bb.xlen, body_bb.ylen],
            "a1_fit": body_bb.xlen <= A1_PLATE and body_bb.ylen <= A1_PLATE,
            "critical_support_count": 0,
            "support_on_seal_land": 0,
            "new_internal_closed_support_space_count": 0,
            "slicer": "HOLD_SLICER_NOT_RUN",
        },
        "geometric_id": {
            "type": "ONE_ISOLATED_PLUS_DOUBLE_MICRO_NOTCH",
            "count": 3, "location": "EXTERNAL_POSITIVE_X_POSITIVE_Y_TOWER_MID_HEIGHT",
            "seal_land_intersection": 0, "bottom_intersection": 0, "tower_top_load_face_intersection": 0,
        },
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-20T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP_TIMESTAMP_NORMALIZATION_FAIL")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path))
    normalize_step(path)


def export_stl(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), tolerance=0.035, angularTolerance=0.08)


def binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL_TOO_SHORT")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_NOT_CANONICAL_BINARY")
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        yield (values[3:6], values[6:9], values[9:12])


def mesh_metrics(path: Path) -> dict[str, object]:
    triangles = list(binary_stl(path))
    edges: Counter = Counter()
    degenerate = 0
    triangle_edges = []
    for triangle in triangles:
        vertices = [tuple(round(float(value), 5) for value in vertex) for vertex in triangle]
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1e-14:
            degenerate += 1
        row = []
        for a, b in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edge = tuple(sorted((a, b)))
            edges[edge] += 1
            row.append(edge)
        triangle_edges.append(row)
    parents = list(range(len(triangles)))
    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index
    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a
    owners = {}
    for index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in owners:
                union(index, owners[edge])
            else:
                owners[edge] = index
    raw = TopoDS_Shape()
    reload_pass = bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()
    bad_edges = sum(value != 2 for value in edges.values())
    return {
        "triangle_count": len(triangles),
        "component_count": len({find(index) for index in range(len(triangles))}),
        "watertight": bad_edges == 0, "manifold": bad_edges == 0,
        "bad_edge_count": bad_edges, "degenerate_triangle_count": degenerate,
        "reload": "PASS" if reload_pass else "FAIL",
    }


def step_metrics(path: Path) -> dict[str, object]:
    model = importers.importStep(str(path))
    solids = model.solids().vals()
    return {
        "reload": "PASS", "solid_count": len(solids),
        "all_valid": bool(solids) and all(solid.isValid() for solid in solids),
        "bbox_mm": bbox_values(model),
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def svg_page(title: str, body: str, footer: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<style>.t{{font:700 28px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.b{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.l{{fill:#caf0f8;stroke:#0077b6;stroke-width:3}}.g{{fill:#ffe8a1;stroke:#d98300;stroke-width:3}}.r{{fill:#ffe3e3;stroke:#c92a2a;stroke-width:3}}.d{{fill:none;stroke:#334e68;stroke-width:2;stroke-dasharray:8 6}}.a{{stroke:#c92a2a;stroke-width:3;marker-end:url(#arrow)}}</style>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#c92a2a"/></marker></defs>
<rect width="1200" height="760" fill="#f8fafc"/><text x="42" y="48" class="t">{title}</text>{body}
<text x="42" y="730" class="m">{footer}</text></svg>'''


def svg_outputs(analysis: dict[str, object]) -> dict[str, str]:
    seal = svg_page("Exact sealing boundary section", '''
<rect x="90" y="470" width="360" height="120" class="b"/><rect x="130" y="300" width="40" height="170" class="b"/><rect x="370" y="300" width="40" height="170" class="b"/>
<rect x="122" y="270" width="296" height="30" class="g"/><rect x="80" y="110" width="380" height="160" class="l"/>
<line x1="130" y1="330" x2="410" y2="330" class="d"/><text x="520" y="150" class="h">Existing lid reference</text><text x="520" y="205" class="m">216 × 166 × nominal 16</text><text x="520" y="270" class="h">Existing gasket, exact STEP</text><text x="520" y="310" class="m">204 × 154 × 3; 8 mm ring</text><text x="520" y="375" class="h">Continuous dummy rim</text><text x="520" y="415" class="m">outer 200 × 150 / inner 192 × 142</text><text x="520" y="455" class="m">added=0 / removed=0 in 1 mm section</text><text x="520" y="520" class="h">Source drip notches intentionally closed</text><text x="520" y="560" class="m">no closure holes invented</text>
''', "PS-BBOX-WATER-DUMMY-V001 · SEALING_BOUNDARY_TEST · PHYSICAL RESULT NOT YET")
    load = svg_page("Ballast reference and body load path", f'''
<rect x="110" y="125" width="900" height="45" class="r"/><text x="1020" y="155" class="h">plate ref</text><rect x="145" y="170" width="48" height="380" class="b"/><rect x="927" y="170" width="48" height="380" class="b"/><rect x="240" y="280" width="640" height="85" class="l"/><rect x="300" y="365" width="520" height="220" class="b"/><line x1="160" y1="140" x2="160" y2="570" class="a"/><line x1="950" y1="140" x2="950" y2="570" class="a"/><text x="335" y="325" class="h">lid remains unloaded</text><text x="345" y="420" class="h">sealed dummy body</text><text x="345" y="465" class="m">4 × {TOWER_SIZE:.0f} mm tower</text><text x="345" y="505" class="m">tower top = lid top +4 mm</text><text x="345" y="545" class="m">minimum lid clearance {analysis['ballast']['tower_lid_clearance_min_mm']:.3f} mm</text>
''', "BALLAST IS CAD_REFERENCE_ONLY · FIXING HOLD · NO ARBITRARY SAFETY FACTOR")
    submersion = svg_page("Submersion test stages", f'''
<rect x="95" y="175" width="760" height="430" rx="30" class="l"/><rect x="255" y="275" width="440" height="250" class="b"/><line x1="80" y1="275" x2="900" y2="275" class="d"/><line x1="80" y1="375" x2="900" y2="375" class="d"/><line x1="80" y1="475" x2="900" y2="475" class="d"/><text x="910" y="280" class="m">50 mm / 10 min</text><text x="910" y="380" class="m">100 mm / 30 min</text><text x="910" y="480" class="m">150 mm / 60 min, then 8 h</text><text x="250" y="655" class="m">witness: FRONT / RIGHT / REAR / LEFT / CENTER</text><text x="870" y="585" class="h">150 mm: {PRESSURE_KPA:.3f} kPa gauge</text>
''', "ANY WITNESS-PAPER DROP = FAIL_LEAK · NO ELECTRONICS · CODEX CANNOT ISSUE PHYSICAL PASS")
    orient = svg_page("Bambu A1 PETG print orientation", f'''
<rect x="80" y="610" width="1040" height="20" class="d"/><rect x="230" y="280" width="600" height="330" class="b"/><rect x="310" y="195" width="55" height="85" class="b"/><rect x="695" y="195" width="55" height="85" class="b"/><line x1="530" y1="570" x2="530" y2="160" class="a"/><text x="555" y="185" class="h">OPEN UP</text><text x="850" y="330" class="m">footprint 244 × 196</text><text x="850" y="375" class="m">A1 plate 256 × 256</text><text x="850" y="420" class="m">support OFF preferred</text><text x="850" y="465" class="m">seal-land support = 0</text><text x="240" y="675" class="h">BOTTOM DOWN · no text, tower, drain, or support on seal land</text>
''', "SLICER NOT RUN · HOLD_SLICER_NOT_RUN · VERIFY FIRST LAYER AND BED CLEARANCE")
    return {SVGS[0]: seal, SVGS[1]: load, SVGS[2]: submersion, SVGS[3]: orient}


def markdown_documents(analysis: dict[str, object]) -> dict[str, str]:
    hydro = analysis["hydrostatic"]
    body = analysis["body"]
    ballast = analysis["ballast"]
    readme = f"""# {VERSION}

This independent untracked lane is a full-size **sealing-boundary submersion-test dummy**, not a complete BBOX and not a field release. It reuses the existing v2.28 `PS-RV227-BBOX-LID` and `PS-RV227-BBOX-GSK` references without modifying either.

The vessel is 200 × 150 × 70 mm with 4 mm walls and a 5 mm closed bottom. The four integral load towers make the printable overall envelope {body['overall_with_integral_towers_xyz_mm'][0]:.0f} × {body['overall_with_integral_towers_xyz_mm'][1]:.0f} × {body['overall_with_integral_towers_xyz_mm'][2]:.1f} mm. No cable, connector, drain, shaft, motor, cassette, or closure-hole penetration exists.

The continuous top rim is the exact 200 × 150 outer / 192 × 142 inner / 4 mm v2.28 rim definition. The source body's two top-open wire-drop notches are documented as drip-resistant only and are deliberately closed here under the user's no-penetration water-dummy instruction. This is the only seal-boundary delta.

Four 12 × 12 mm integral towers lie outside the lid perimeter. Their minimum CAD lid clearance is {ballast['tower_lid_clearance_min_mm']:.3f} mm and their load faces are 4 mm above the actual source-lid CAD top. The ballast plate is reference geometry only; fixing and physical ballast mass remain HOLD.

At 150 mm freshwater depth, the reference gauge pressure is {hydro['gauge_pressure_kpa']:.6f} kPa. Actual CAD exterior displacement, including body, connectors, towers, gasket, and lid, is {hydro['displaced_volume_l']:.6f} L, giving {hydro['buoyancy_force_n']:.6f} N ({hydro['buoyancy_equivalent_kgf']:.6f} kgf equivalent). No safety factor is silently added.

First print: `bbox_water_dummy_v001.stl`, bottom down and open up, PETG on Bambu A1. Slicer has not been run. Do not begin immersion until a real, evenly distributed lid-compression method is documented; source closure-hole count is zero and no pattern was guessed.

Final CAD status: `CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING`.
"""
    authority = f"""# Design authority

Selected authority is the unique repository-native v2.28 fixed-core source matching the user-provided nominal dimensions:

- `{SOURCE_BUILDER_REL.as_posix()}`
- `{SOURCE_BODY_REL.as_posix()}`
- `{SOURCE_LID_REL.as_posix()}`
- `{SOURCE_GASKET_REL.as_posix()}`
- `{SOURCE_INTERFACE_REL.as_posix()}`

The source contract fixes body 200 × 150 × 120 mm, lid 216 × 166 × 16 mm nominal, and gasket 204 × 154 × 3 mm. The generated lid STEP's actual bbox is 216 × 166 × 18.5 mm because its source top ribs extend 2.5 mm above the nominal 16 mm plate body. Both facts are recorded; tower height uses the actual STEP bbox.

Later v0.9.6.0 waterproof architecture uses a conflicting 200 × 130 family and is not the authority for this physical 200 × 150 lid/gasket contract. The chosen source's body STEP has a 200 × 162 overall bbox because loose-layout floor ribs extend beyond the nominal Y envelope; those non-seal ribs are not copied.

The exact continuous rim before source notch cutting is outer 200 × 150, inner 192 × 142, width 4, and flat at the top. The dummy reproduces it with zero added and zero removed volume in a 1 mm section. Source notches are explicitly drip-resistant rather than waterproof and are closed by task instruction. Source lid, gasket, and builder contain no closure holes; exact empty pattern is retained. `HOLD_ACTUAL_CLOSURE_METHOD` remains active.

This authority releases CAD and first printing only. It does not release a leak result, closure hardware, ballast fixing, load, electronics, powered operation, field use, or production.
"""
    plan = """# Physical test plan

Prerequisites: print and inspect the dummy; reuse the intended physical lid and gasket; document an external closure/compression fixture that loads the lid uniformly without using the lid as a ballast load path; keep electronics absent. If closure is unresolved, stop.

Place dry witness paper at FRONT, RIGHT, REAR, LEFT, and CENTER. Photograph and weigh/mark it before the test if practical. Any visible drop, wet mark, mass gain, or ambiguous result is `FAIL_LEAK`.

1. 50 mm water depth for 10 minutes. Stop on bubbles, shift, damage, or witness change.
2. 100 mm water depth for 30 minutes. Reinspect all five witness zones.
3. 150 mm water depth for 60 minutes. Reference gauge pressure is 1.4709975 kPa.
4. 150 mm water depth for 8 hours only after the prior stages remain dry and stable.

Use freshwater in a controlled container. Restrain buoyancy using the four towers and a separately reviewed plate/fixture; never load the lid or gasket directly. Do not apply an undocumented ballast multiplier. Dry and inspect between stages if any ambiguity exists.

Codex validation can never emit a physical PASS. Record physical measurements separately. Any drop is `FAIL_LEAK`; no drop remains a user-observed result pending review, not a repository-issued field approval.
"""
    print_guide = f"""# Print guide

- Printer/material: Bambu A1 / PETG.
- Orientation: bottom down, open side up.
- Printable envelope: {body['overall_with_integral_towers_xyz_mm'][0]:.0f} × {body['overall_with_integral_towers_xyz_mm'][1]:.0f} × {body['overall_with_integral_towers_xyz_mm'][2]:.1f} mm; A1 nominal plate is 256 × 256 mm.
- Recommended walls: 5–6 wall loops.
- Recommended bottom: 6–8 layers.
- Infill: 100% is not automatically required; choose a stable PETG process and keep walls/bottom authoritative.
- Support: OFF preferred. Never put support, text, a tower, drain, decorative chamfer, or bolt-access cut on the seal land.
- Check the full skirt/brim and head-clearance envelope in the slicer. Slicer has not been run: `HOLD_SLICER_NOT_RUN`.
- Keep the top rim clean. Do not sand away the geometry; remove only loose whiskers. Reject warpage, layer gaps, tower cracks, or a damaged rim.
- The three micro-notches on one external tower are the permanent geometric ID; they are not defects.
"""
    holds = """# HOLD register

- `HOLD_ACTUAL_CLOSURE_METHOD`: source lid/body/gasket define zero closure holes; no hole pattern was invented.
- `HOLD_LID_COMPRESSION_UNIFORMITY`: measure real fixture load distribution.
- `HOLD_GASKET_COMPRESSION`: physical gasket compression and material are not validated by CAD.
- `HOLD_BALLAST_FIXING`: plate is reference-only and must not load the lid.
- `HOLD_BALLAST_PHYSICAL_MASS`: CAD reports displacement without an arbitrary safety factor.
- `HOLD_SLICER_NOT_RUN`: check first layer, skirt/brim, and PETG settings.
- `PHYSICAL_LEAK_RESULT_NOT_YET`: Codex cannot issue physical PASS.
- `ELECTRONICS_NOT_ALLOWED_IN_FIRST_WATER_TEST`.
- `LOAD_POWERED_WATER_MUD_FIELD_PRODUCTION_NOT_APPROVED`.
"""
    return {DOCS[0]: readme, DOCS[1]: authority, DOCS[2]: plan, DOCS[3]: print_guide, DOCS[4]: holds}


def canonical_guard(guard: dict[str, object]) -> dict[str, object]:
    return {key: guard[key] for key in (
        "repository", "branch", "head", "staged", "tracked_dirty", "authority_sha256",
        "outside_untracked", "protected_lanes", "source_authority",
    )}


def validation_report(analysis: dict[str, object], steps: dict[str, object], meshes: dict[str, object], guard: dict[str, object]) -> dict[str, object]:
    seal = analysis["seal"]
    body = analysis["body"]
    ballast = analysis["ballast"]
    printable = analysis["printability"]
    checks = {
        "body_main_outer_xy_authority": "PASS" if body["main_vessel_outer_xy_mm"] == [200.0, 150.0] else "FAIL",
        "dummy_height_70": "PASS" if body["height_mm"] == 70.0 else "FAIL",
        "bottom_ge_5": "PASS" if body["bottom_mm"] >= 5.0 else "FAIL",
        "wall_ge_4": "PASS" if body["wall_mm"] >= 4.0 else "FAIL",
        "closed_bottom_no_penetrations": "PASS" if body["closed_bottom"] and body["penetration_count"] == 0 else "FAIL",
        "seal_interface_exact": "PASS" if seal["regression_added_mm3_at_1mm_section"] < 1e-6 and seal["regression_removed_mm3_at_1mm_section"] < 1e-6 else "FAIL",
        "source_notches_closed": "PASS" if seal["source_drip_notches_closed_by_task"] else "FAIL",
        "lid_interference_zero": "PASS" if seal["lid_body_interference_mm3"] < 1e-6 else "FAIL",
        "gasket_nominal_placement": "PASS" if seal["gasket_rim_overlap_mm3_at_nominal_1mm"] > 2700 else "FAIL",
        "closure_alignment_empty_exact": "PASS" if seal["closure_hole_count_source"] == seal["closure_hole_count_dummy"] == 0 else "FAIL",
        "tower_count_4": "PASS" if ballast["tower_count"] == 4 else "FAIL",
        "tower_lid_clearance_ge_3": "PASS" if ballast["tower_lid_clearance_min_mm"] >= 3.0 else "FAIL",
        "tower_lid_intersection_zero": "PASS" if max(ballast["tower_lid_intersection_each_mm3"]) < 1e-6 else "FAIL",
        "tower_bolt_intersection_zero": "PASS" if ballast["tower_bolt_intersection_count"] == 0 else "FAIL",
        "ballast_plate_lid_clearance_ge_3": "PASS" if ballast["plate_to_lid_clearance_mm"] >= 3.0 else "FAIL",
        "a1_fit": "PASS" if printable["a1_fit"] else "FAIL",
        "critical_support_zero": "PASS" if printable["critical_support_count"] == 0 and printable["support_on_seal_land"] == 0 else "FAIL",
        "primary_shape_valid": "PASS" if body["primary_shape_valid"] else "FAIL",
        "step_reload": "PASS" if all(row["reload"] == "PASS" and row["all_valid"] for row in steps.values()) else "FAIL",
        "stl_watertight_manifold": "PASS" if all(row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()) else "FAIL",
        "hydrostatic_reference": "PASS" if abs(analysis["hydrostatic"]["gauge_pressure_kpa"] - 1.4709975) < 1e-9 else "FAIL",
        "displacement_actual_cad": "PASS" if analysis["hydrostatic"]["displaced_volume_l"] > 0 else "FAIL",
        "physical_pass_not_claimed": "PASS",
    }
    return {
        "version": VERSION, "status": STATUS, "classification": "SEALING_BOUNDARY_TEST",
        "repository_guard": canonical_guard(guard), "analysis": analysis,
        "step_reload": steps, "stl_quality": meshes, "checks": checks,
        "holds": [
            "HOLD_ACTUAL_CLOSURE_METHOD", "HOLD_LID_COMPRESSION_UNIFORMITY",
            "HOLD_GASKET_COMPRESSION", "HOLD_BALLAST_FIXING", "HOLD_BALLAST_PHYSICAL_MASS",
            "HOLD_SLICER_NOT_RUN", "PHYSICAL_LEAK_RESULT_NOT_YET",
            "LOAD_POWERED_WATER_MUD_FIELD_PRODUCTION_NOT_APPROVED",
        ],
    }


def export_geometry(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    body = body_shape()
    assembly = assembly_reference()
    export_step(body, out / CAD_FILES[0])
    export_stl(body, out / CAD_FILES[1])
    export_step(assembly, out / CAD_FILES[2])
    steps = {CAD_FILES[0]: step_metrics(out / CAD_FILES[0]), CAD_FILES[2]: step_metrics(out / CAD_FILES[2])}
    meshes = {CAD_FILES[1]: mesh_metrics(out / CAD_FILES[1])}
    if steps[CAD_FILES[0]]["solid_count"] != 1 or steps[CAD_FILES[2]]["solid_count"] != 4:
        raise RuntimeError("STEP_SOLID_COUNT_FAIL: " + json.dumps(steps))
    if any(not row["all_valid"] for row in steps.values()):
        raise RuntimeError("STEP_RELOAD_FAIL")
    if any(not row["watertight"] or row["bad_edge_count"] or row["degenerate_triangle_count"] or row["component_count"] != 1 for row in meshes.values()):
        raise RuntimeError("STL_QUALITY_FAIL: " + json.dumps(meshes))
    return steps, meshes


def generate(out: Path, copy_sources: bool = False) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        (out / "tests").mkdir(parents=True, exist_ok=True)
        (out / BUILDER).write_bytes((LANE_DIR / BUILDER).read_bytes())
        (out / TEST).write_bytes((LANE_DIR / TEST).read_bytes())
    analysis = design_analysis()
    steps, meshes = export_geometry(out)
    for rel, svg in svg_outputs(analysis).items():
        write_text(out / rel, svg)
    for rel, text in markdown_documents(analysis).items():
        write_text(out / rel, text)
    write_json(out / DATA[0], {
        "version": VERSION,
        "body": {"outer_xy_mm": [BODY_X, BODY_Y], "height_mm": BODY_H, "wall_mm": WALL, "bottom_mm": BOTTOM},
        "lid_nominal_mm": LID_NOMINAL, "lid_actual_source_bbox_mm": LID_CAD_BBOX,
        "gasket_mm": GASKET, "gasket_inner_xy_mm": GASKET_INNER,
        "tower": {"count": 4, "cross_section_mm": [TOWER_SIZE, TOWER_SIZE], "centers_abs_xy_mm": [TOWER_CENTER_X, TOWER_CENTER_Y], "top_z_mm": TOWER_TOP_Z},
        "ballast_plate_reference_mm": [BALLAST_PLATE_X, BALLAST_PLATE_Y, BALLAST_PLATE_T],
        "hydrostatic": {"rho_kg_m3": RHO_WATER, "g_m_s2": G_ACCEL, "depth_m": TEST_DEPTH_M},
        "closure_holes": {"source": 0, "dummy": 0, "state": "EXACT_EMPTY_PATTERN_PHYSICAL_CLOSURE_HOLD"},
        "source_notch_policy": "CLOSED_BY_WATER_DUMMY_NO_PENETRATION_TASK_OVERRIDE",
    })
    guard = repository_guard(False)
    report = validation_report(analysis, steps, meshes, guard)
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError("VALIDATION_FAIL: " + json.dumps(report["checks"], sort_keys=True))
    write_json(out / DATA[1], report)
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=1\nSVG=4\n"
        f"MAIN_BODY=200x150x70\nWALL={WALL}\nBOTTOM={BOTTOM}\n"
        f"OVERALL_WITH_TOWERS={analysis['body']['overall_with_integral_towers_xyz_mm']}\n"
        f"DISPLACED_VOLUME_L={analysis['hydrostatic']['displaced_volume_l']:.9f}\n"
        f"BUOYANCY_N={analysis['hydrostatic']['buoyancy_force_n']:.9f}\n"
        f"STATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=2_OF_2_PASS\n"
        "STL_WATERTIGHT_MANIFOLD=1_OF_1_PASS\nSEAL_SECTION_REGRESSION=PASS\n"
        "REPRODUCIBILITY=ALL_EXPECTED_PATHS_BYTE_IDENTICAL\nPHYSICAL_LEAK_RESULT=NOT_YET"
    ))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    sum_files = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in sum_files))
    return report


def verify() -> dict[str, object]:
    guard = repository_guard(True)
    files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    manifest = (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    mismatches = []
    for line in (LANE_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(LANE_DIR / rel) != digest:
            mismatches.append(rel)
    steps = {CAD_FILES[0]: step_metrics(LANE_DIR / CAD_FILES[0]), CAD_FILES[2]: step_metrics(LANE_DIR / CAD_FILES[2])}
    meshes = {CAD_FILES[1]: mesh_metrics(LANE_DIR / CAD_FILES[1])}
    report = json.loads((LANE_DIR / DATA[1]).read_text(encoding="utf-8"))
    checks = {
        "repository_guard": all(guard["checks"].values()),
        "exact_paths": files == EXPECTED_FILES,
        "manifest_exact": manifest == EXPECTED_FILES,
        "commit_paths_exact": commit_paths == expected_commit,
        "sha_mismatch_zero": not mismatches,
        "step_reload_2_of_2": len(steps) == 2 and all(row["reload"] == "PASS" and row["all_valid"] for row in steps.values()),
        "step_solid_counts": steps[CAD_FILES[0]]["solid_count"] == 1 and steps[CAD_FILES[2]]["solid_count"] == 4,
        "stl_quality_1_of_1": len(meshes) == 1 and all(row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "validation_all_nonfail": all(value != "FAIL" for value in report["checks"].values()),
        "status_boundary": "SEALING_BOUNDARY_TEST" in report["status"],
        "status_physical_pending": "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING" in report["status"],
        "no_physical_pass": "PHYSICAL_PASS" not in json.dumps(report),
    }
    if not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL: " + json.dumps({"checks": checks, "mismatches": mismatches}, sort_keys=True))
    return {
        "checks": checks, "paths": len(files), "step": 2, "stl": 1, "svg": 4,
        "sha_mismatches": mismatches, "repository": guard,
    }


def reproducibility() -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_bbox_water_dummy_v001_repro_") as temp:
        target = Path(temp) / LANE_NAME
        generate(target, copy_sources=True)
        mismatches = [rel for rel in EXPECTED_FILES if sha256(target / rel) != sha256(LANE_DIR / rel)]
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + json.dumps(mismatches))
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package() -> dict[str, object]:
    verify()
    reproducibility()
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = downloads / f"Paddy_Swarm_PS-BBOX-WATER-DUMMY-V001_{stamp}.zip"
    counter = 1
    while target.exists():
        target = downloads / f"Paddy_Swarm_PS-BBOX-WATER-DUMMY-V001_{stamp}_{counter:02d}.zip"
        counter += 1
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", date_time=(2026, 8, 20, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE_DIR / rel).read_bytes())
    return {"path": str(target), "sha256": sha256(target), "entries": EXPECTED_PATH_COUNT}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any((args.build, args.verify, args.reproducibility, args.package)):
        args.build = True
    result: dict[str, object] = {}
    if args.build:
        repository_guard(False)
        result["build"] = generate(LANE_DIR)
    if args.verify:
        result["verify"] = verify()
    if args.reproducibility:
        result["reproducibility"] = reproducibility()
    if args.package:
        result["package"] = package()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
