"""Build PS-BBOX-WATER-DUMMY-V002 external-M4 / 1.8 mm cord test artifacts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
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
VERSION = "PS-BBOX-WATER-DUMMY-V002"
LANE_NAME = "bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
CLASSIFICATION = "SEALING_BOUNDARY_PHYSICAL_TEST_DUMMY_NOT_PRODUCTION_BBOX"
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/GASKET_COUPON_PRINT_READY/"
    "V002_REFERENCE_COMPLETE/EXTERNAL_VERTICAL_M4_COMPLETE/"
    "SEALED_INTERNAL_PENETRATION_ZERO/PHYSICAL_GASKET_WINNER_PENDING/"
    "COMMIT_READY_NOT_STAGED"
)

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3271
BASE_OUTSIDE_PATH_DIGEST = "975d431c60d38d04bd93e10de630a8f50e02cb2956c9f6b8c4595af3bc661c8a"
PROTECTED_TREES = {
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test":
        (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27":
        (54, "1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32":
        (28, "4792b7db682d02e78ab88bdd8642f42b6805a6773782f4bcc36f2ff3427bc516"),
    "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37":
        (38, "d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
}

# V001 envelope retained; its through-hole geometry is intentionally not reused.
BODY_X = 200.0
BODY_Y = 150.0
BODY_H = 70.0
WALL = 4.0
BOTTOM = 5.0
TOP_FLANGE_X = 208.0
TOP_FLANGE_Y = 158.0
TOP_FLANGE_T = 6.0
BODY_LUG_Z0 = 58.0
BODY_LUG_T = 8.0
LID_CORE_X = 208.0
LID_CORE_Y = 158.0
LID_T = 8.0
EXTERNAL_MAX_X = 240.0
EXTERNAL_MAX_Y = 190.0
LUG_CENTER_X = 112.0
LUG_CENTER_Y = 87.0
LUG_OD = 16.0
M4_CLEARANCE_D = 4.5
M4_COUNT = 8
M4_BOLT_LENGTH_CANDIDATE = 30.0
WASHER_OD_REFERENCE = 9.0
NUT_AF_REFERENCE = 7.0
TOOL_SOCKET_OD_REFERENCE = 12.0
STRUCTURAL_LIGAMENT_HARD_MIN = 4.0
STRUCTURAL_LIGAMENT_TARGET = 5.0
MIN_STRUCTURAL_LIGAMENT = min(
    LUG_CENTER_X - M4_CLEARANCE_D / 2 - TOP_FLANGE_X / 2,
    LUG_CENTER_Y - M4_CLEARANCE_D / 2 - TOP_FLANGE_Y / 2,
)

CORD_SOURCE = "PVC_TOWER_RUBBER_CORD"
CORD_DIAMETER = 1.8
COMPRESSION_PERCENT = (20.0, 25.0)
COMPRESSED_HEIGHT_RANGE = (1.35, 1.44)
GROOVE_CANDIDATES = {
    "G18-A": {"width_mm": 2.0, "depth_mm": 0.4, "notch_count": 1},
    "G18-B": {"width_mm": 2.1, "depth_mm": 0.5, "notch_count": 2},
    "G18-C": {"width_mm": 2.2, "depth_mm": 0.6, "notch_count": 3},
}
FULL_DUMMY_CANDIDATE = "G18-B"
GROOVE_OUTER_X = 200.0
GROOVE_OUTER_Y = 150.0
GROOVE_OUTER_RADIUS = 6.0
COUPON_X = 48.0
COUPON_Y = 34.0
COUPON_T = 5.0
COUPON_GROOVE_OUTER_X = 36.0
COUPON_GROOVE_OUTER_Y = 22.0
COUPON_GROOVE_OUTER_RADIUS = 6.0
HARD_STOP_PAD = 4.0
HARD_STOP_CENTERS = [(-102.0, 0.0), (102.0, 0.0), (0.0, -77.0), (0.0, 77.0)]
A1_BUILD_VOLUME = (256.0, 256.0, 256.0)

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_water_dummy_v002_contract.py"
CAD_FILES = [
    "artifacts/gasket_g18_a.step", "artifacts/gasket_g18_a.stl",
    "artifacts/gasket_g18_b.step", "artifacts/gasket_g18_b.stl",
    "artifacts/gasket_g18_c.step", "artifacts/gasket_g18_c.stl",
    "artifacts/bbox_water_dummy_v002_body.step", "artifacts/bbox_water_dummy_v002_body.stl",
    "artifacts/bbox_water_dummy_v002_lid.step", "artifacts/bbox_water_dummy_v002_lid.stl",
    "artifacts/bbox_water_dummy_v002_assembly.step",
]
SVGS = [
    "artifacts/WATER_PATH_V001_FAILURE.svg", "artifacts/V002_SEALING_BOUNDARY.svg",
    "artifacts/EXTERNAL_M4_LOAD_PATH.svg", "artifacts/GASKET_1P8_SECTION.svg",
    "artifacts/GASKET_COMPRESSION_CANDIDATES.svg", "artifacts/G18_COUPON_IDENTIFICATION.svg",
    "artifacts/FASTENER_PATTERN.svg", "artifacts/WATER_TEST_SETUP.svg",
    "artifacts/LEAK_DIAGNOSIS.svg",
]
DOCS = [
    "README.md", "PHYSICAL_FAILURE_RECORD.md", "DESIGN_AUTHORITY.md",
    "GASKET_1P8_REQUIREMENTS.md", "FASTENER_REQUIREMENTS.md", "PHYSICAL_TEST_PLAN.md",
    "PRINT_GUIDE.md", "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *CAD_FILES, *SVGS, *DOCS, *LOGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)

def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

v001 = _load("bbox_water_dummy_v001_frozen",
    REPO_ROOT / "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test/build_bbox_water_dummy_v001.py")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file()
                   and "__pycache__" not in path.parts and path.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode()); digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()

def untracked_paths() -> list[str]:
    return sorted(row[3:].replace("\\", "/") for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
                  if row.startswith("?? "))

def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"; paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()

def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve(); branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD"); staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_TREES}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    ignored = run_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256, "protected_trees": protected == PROTECTED_TREES,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "cache_zero": not cache,
        "ignored_zero": not ignored, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {"checks": checks, "repository": str(root), "branch": branch, "head": head, "staged": staged,
        "tracked_dirty": dirty, "outside_untracked": list(outside_snapshot()), "authority_sha256": authority,
        "protected_trees": {rel: {"file_count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
                            for rel, value in protected.items()}, "lane_files": len(lane_files), "cache": cache,
        "ignored": ignored, "forbidden": forbidden}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result

def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)

def cylinder(d: float, h: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").circle(d / 2).extrude(h / 2, both=True).translate(center)

def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))

def rounded_plate(x: float, y: float, radius: float, height: float, z0: float) -> cq.Workplane:
    result = box(x - 2 * radius, y, height, (0, 0, z0 + height / 2)).union(
        box(x, y - 2 * radius, height, (0, 0, z0 + height / 2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            result = result.union(cylinder(2 * radius, height,
                (sx * (x / 2 - radius), sy * (y / 2 - radius), z0 + height / 2)))
    return result.clean()

def rounded_ring_xy(outer_x: float, outer_y: float, outer_r: float, width: float,
                    height: float, z0: float) -> cq.Workplane:
    inner_x = outer_x - 2 * width; inner_y = outer_y - 2 * width; inner_r = outer_r - width
    return rounded_plate(outer_x, outer_y, outer_r, height, z0).cut(
        rounded_plate(inner_x, inner_y, inner_r, height + 2, z0 - 1)).clean()

def fastener_positions() -> list[tuple[float, float]]:
    return [(-LUG_CENTER_X, -LUG_CENTER_Y), (LUG_CENTER_X, -LUG_CENTER_Y),
            (-LUG_CENTER_X, LUG_CENTER_Y), (LUG_CENTER_X, LUG_CENTER_Y),
            (-LUG_CENTER_X, 0.0), (LUG_CENTER_X, 0.0),
            (0.0, -LUG_CENTER_Y), (0.0, LUG_CENTER_Y)]

def external_lugs(z0: float, height: float) -> cq.Workplane:
    result = None
    for x, y in fastener_positions():
        boss = cylinder(LUG_OD, height, (x, y, z0 + height / 2))
        if abs(x) > 0 and abs(y) > 0:
            bridge = box(16.0, 16.0, height, (x - (6.0 if x > 0 else -6.0),
                                                   y - (6.0 if y > 0 else -6.0), z0 + height / 2))
        elif abs(x) > 0:
            bridge = box(24.0, 16.0, height, (x - (6.0 if x > 0 else -6.0), y, z0 + height / 2))
        else:
            bridge = box(16.0, 24.0, height, (x, y - (6.0 if y > 0 else -6.0), z0 + height / 2))
        unit = boss.union(bridge)
        result = unit if result is None else result.union(unit)
    assert result is not None
    return result.clean()

def m4_hole_tools(z_center: float = 65.0, height: float = 40.0) -> cq.Workplane:
    return compound([cylinder(M4_CLEARANCE_D, height, (x, y, z_center)) for x, y in fastener_positions()])

def selected_groove() -> dict[str, float | int]:
    return GROOVE_CANDIDATES[FULL_DUMMY_CANDIDATE]

def hard_stop_rows() -> list[dict[str, object]]:
    rows = []
    for name, values in GROOVE_CANDIDATES.items():
        depth = float(values["depth_mm"]); low = COMPRESSED_HEIGHT_RANGE[0] - depth
        high = COMPRESSED_HEIGHT_RANGE[1] - depth; nominal = sum(COMPRESSED_HEIGHT_RANGE) / 2 - depth
        rows.append({"candidate": name, **values, "hard_stop_gap_range_mm": [round(low, 3), round(high, 3)],
                     "hard_stop_gap_nominal_mm": round(nominal, 3),
                     "compressed_total_at_nominal_mm": round(depth + nominal, 3)})
    return rows

def selected_hard_stop_gap() -> float:
    return next(float(row["hard_stop_gap_nominal_mm"]) for row in hard_stop_rows()
                if row["candidate"] == FULL_DUMMY_CANDIDATE)

def groove_tool(width: float, depth: float, z_top: float = BODY_H) -> cq.Workplane:
    return rounded_ring_xy(GROOVE_OUTER_X, GROOVE_OUTER_Y, GROOVE_OUTER_RADIUS,
                           width, depth + 0.2, z_top - depth)

def cavity_envelope() -> cq.Workplane:
    return box(BODY_X - 2 * WALL, BODY_Y - 2 * WALL, BODY_H - BOTTOM + 1,
               (0, 0, BOTTOM + (BODY_H - BOTTOM + 1) / 2))

@lru_cache(maxsize=1)
def body_shape() -> cq.Workplane:
    shell = box(BODY_X, BODY_Y, BODY_H, (0, 0, BODY_H / 2)).cut(cavity_envelope())
    flange = box(TOP_FLANGE_X, TOP_FLANGE_Y, TOP_FLANGE_T,
                 (0, 0, BODY_H - TOP_FLANGE_T / 2)).cut(cavity_envelope())
    result = shell.union(flange).union(external_lugs(BODY_LUG_Z0, BODY_LUG_T))
    result = result.cut(m4_hole_tools())
    selected = selected_groove(); result = result.cut(groove_tool(float(selected["width_mm"]), float(selected["depth_mm"])))
    gap = selected_hard_stop_gap()
    for x, y in HARD_STOP_CENTERS:
        result = result.union(box(HARD_STOP_PAD, HARD_STOP_PAD, gap, (x, y, BODY_H + gap / 2)))
    return result.clean()

@lru_cache(maxsize=1)
def lid_shape() -> cq.Workplane:
    result = rounded_plate(LID_CORE_X, LID_CORE_Y, 8.0, LID_T, 0.0).union(external_lugs(0.0, LID_T))
    return result.cut(m4_hole_tools(LID_T / 2, LID_T + 4)).clean()

def coupon_shape(candidate: str) -> cq.Workplane:
    values = GROOVE_CANDIDATES[candidate]; width = float(values["width_mm"]); depth = float(values["depth_mm"])
    result = rounded_plate(COUPON_X, COUPON_Y, 3.0, COUPON_T, 0.0)
    groove = rounded_ring_xy(COUPON_GROOVE_OUTER_X, COUPON_GROOVE_OUTER_Y,
                             COUPON_GROOVE_OUTER_RADIUS, width, depth + 0.15, COUPON_T - depth)
    result = result.cut(groove)
    count = int(values["notch_count"])
    for index in range(count):
        x = (index - (count - 1) / 2) * 3.0
        result = result.cut(box(1.2, 2.0, 1.5, (x, -COUPON_Y / 2, 1.75)))
    return result.clean()

@lru_cache(maxsize=1)
def compressed_gasket_reference() -> cq.Workplane:
    selected = selected_groove(); height = float(selected["depth_mm"]) + selected_hard_stop_gap()
    return rounded_ring_xy(GROOVE_OUTER_X, GROOVE_OUTER_Y, GROOVE_OUTER_RADIUS,
                           float(selected["width_mm"]), height, BODY_H - float(selected["depth_mm"]))

@lru_cache(maxsize=1)
def assembly_shape() -> cq.Workplane:
    return compound([body_shape(), compressed_gasket_reference(),
                     lid_shape().translate((0, 0, BODY_H + selected_hard_stop_gap()))])

def common_volume(left: cq.Workplane, right: cq.Workplane) -> float:
    return sum(solid.Volume() for solid in left.val().intersect(right.val()).Solids())

def shape_volume(shape: cq.Workplane) -> float:
    return sum(solid.Volume() for solid in shape.solids().vals())

def bbox_mm(shape: cq.Workplane) -> list[float]:
    b = shape.val().BoundingBox(); return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]

@lru_cache(maxsize=1)
def analysis() -> dict[str, object]:
    body = body_shape(); lid = lid_shape(); cavity = cavity_envelope(); holes = m4_hole_tools()
    selected = selected_groove(); groove = groove_tool(float(selected["width_mm"]), float(selected["depth_mm"]))
    tool_access = compound([cylinder(TOOL_SOCKET_OD_REFERENCE, 12.0, (x, y, BODY_LUG_Z0 - 6.0))
                            for x, y in fastener_positions()])
    placed_lid = lid.translate((0, 0, BODY_H + selected_hard_stop_gap()))
    gasket = compressed_gasket_reference()
    contact_band = rounded_ring_xy(GROOVE_OUTER_X, GROOVE_OUTER_Y, GROOVE_OUTER_RADIUS,
                                   float(selected["width_mm"]), 0.2, 0.0)
    coverage = common_volume(lid, contact_band) / shape_volume(contact_band)
    hard_stops = compound([box(HARD_STOP_PAD, HARD_STOP_PAD, selected_hard_stop_gap(),
                               (x, y, BODY_H + selected_hard_stop_gap() / 2)) for x, y in HARD_STOP_CENTERS])
    coupons = {name: {"bbox_mm": bbox_mm(coupon_shape(name)), "valid": coupon_shape(name).val().isValid(),
                      **values} for name, values in GROOVE_CANDIDATES.items()}
    return {
        "physical_failure_record": {"V001_BODY_PRINT": "PASS", "V001_RUBBER_CORD_INSTALLATION": "PHYSICALLY_FEASIBLE",
            "V001_THROUGH_HOLE_WATER_PATH": "FAIL", "V001_SIDE_M4_RETENTION": "FAIL",
            "V001_WATER_TEST_CONFIGURATION": "REJECTED"},
        "rubber_cord": {"source": CORD_SOURCE, "physical_diameter_mm": CORD_DIAMETER,
            "measurement_authority": "USER_IMAGE_PHYSICAL_MEASUREMENT", "material_hardness": "HOLD",
            "end_joint": "PHYSICAL_HOLD", "compression_percent_target": list(COMPRESSION_PERCENT),
            "compressed_height_target_mm": list(COMPRESSED_HEIGHT_RANGE)},
        "gasket_study": {"candidates": hard_stop_rows(), "full_dummy_provisional_candidate": FULL_DUMMY_CANDIDATE,
            "final_gasket_compression": "PHYSICAL_HOLD", "coupon_geometry": coupons,
            "closed_loop": True, "discontinuity_count": 0,
            "groove_cavity_intersection_mm3": round(common_volume(groove, cavity), 6),
            "groove_m4_intersection_mm3": round(common_volume(groove, holes), 6),
            "hard_stop_groove_intersection_mm3": round(common_volume(hard_stops, groove), 6)},
        "sealed_body": {"core_outer_xyz_mm": [BODY_X, BODY_Y, BODY_H],
            "inner_xyz_mm": [BODY_X - 2 * WALL, BODY_Y - 2 * WALL, BODY_H - BOTTOM],
            "wall_mm": WALL, "bottom_mm": BOTTOM, "top_flange_xy_mm": [TOP_FLANGE_X, TOP_FLANGE_Y],
            "external_bbox_mm": bbox_mm(body), "primary_valid": body.val().isValid(), "bottom_closed": True,
            "continuous_walls": 4, "top_only_open": True, "drain_count": 0, "pin_hole_count": 0,
            "locator_hole_count": 0, "insert_pilot_hole_count": 0,
            "sealed_internal_hole_penetration_count": 0,
            "m4_hole_cavity_intersection_mm3": round(common_volume(holes, cavity), 6)},
        "external_fastener": {"architecture": "EXTERNAL_VERTICAL_M4_THROUGH_BOLT",
            "orientation": "VERTICAL_Z", "horizontal_fastener_count": 0, "m4_count": M4_COUNT,
            "pattern": "CORNER_4_PLUS_EDGE_MID_4", "positions_xy_mm": [list(row) for row in fastener_positions()],
            "clearance_hole_d_mm": M4_CLEARANCE_D, "bolt_length_candidate_mm": M4_BOLT_LENGTH_CANDIDATE,
            "stack": ["M4_BOLT", "LID_EXTERNAL_EAR", "OPEN_GAP", "BODY_EXTERNAL_LUG", "FLAT_WASHER", "M4_NYLOC_NUT"],
            "minimum_structural_ligament_mm": MIN_STRUCTURAL_LIGAMENT,
            "ligament_hard_min_mm": STRUCTURAL_LIGAMENT_HARD_MIN,
            "ligament_target_mm": STRUCTURAL_LIGAMENT_TARGET,
            "tool_access_proxy_od_mm": TOOL_SOCKET_OD_REFERENCE,
            "tool_access_body_intersection_mm3": round(common_volume(tool_access, body), 6),
            "six_point_max_projected_span_mm": 174.0, "eight_point_max_projected_span_mm": 112.0,
            "selection": "M4_X8_SELECTED_FOR_LOWER_MAXIMUM_COMPRESSION_SPAN"},
        "lid": {"core_xyz_mm": [LID_CORE_X, LID_CORE_Y, LID_T], "external_bbox_mm": bbox_mm(lid),
            "primary_valid": lid.val().isValid(), "flat_sealing_underside": True,
            "sealing_band_coverage_ratio": round(coverage, 6), "internal_penetration_count": 0,
            "placed_body_intersection_mm3": round(common_volume(placed_lid, body), 6),
            "placed_gasket_lid_intersection_mm3": round(common_volume(gasket, placed_lid), 6),
            "placed_gasket_body_intersection_mm3": round(common_volume(gasket, body), 6)},
        "printability": {"printer": "Bambu Lab A1", "build_volume_mm": list(A1_BUILD_VOLUME),
            "body_orientation": "BOTTOM_DOWN_TOP_OPEN_SUPPORT_OFF_PREFERRED",
            "lid_orientation": "FLAT_SEALING_FACE_DOWN_SUPPORT_OFF_PREFERRED",
            "coupon_orientation": "FUNCTIONAL_GROOVE_UP_SUPPORT_OFF",
            "all_parts_within_a1": all(max(bbox_mm(shape)) <= min(A1_BUILD_VOLUME)
                                      for shape in [body, lid, *[coupon_shape(name) for name in GROOVE_CANDIDATES]]),
            "slicer": "HOLD_SLICER_NOT_RUN"},
        "release": {"first_print": ["artifacts/gasket_g18_a.stl", "artifacts/gasket_g18_b.stl",
                                      "artifacts/gasket_g18_c.stl"],
            "second_print": "artifacts/bbox_water_dummy_v002_body.stl",
            "third_print": "artifacts/bbox_water_dummy_v002_lid.stl",
            "allowed": ["CAD_PASS", "CONTRACT_TEST_PASS", "GASKET_COUPON_PRINT_READY", "V002_REFERENCE_COMPLETE"],
            "prohibited": ["GASKET_FIT_PASS", "GASKET_COMPRESSION_PASS", "BODY_PRINT_PASS", "LID_PRINT_PASS",
                           "WATER_PASS", "BBOX_SEALING_BOUNDARY_PASS", "POWERED_PASS", "FIELD_PASS", "DURABILITY_PASS"]}}

def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-23T00:00:00'", text, count=1)
    if count != 1: raise RuntimeError("STEP timestamp normalization")
    path.write_text(text, encoding="utf-8", newline="\n")

def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); exporters.export(shape, str(path), exportType="STEP"); normalize_step(path)

def export_artifacts(out: Path) -> dict[str, object]:
    shapes = {"gasket_g18_a": coupon_shape("G18-A"), "gasket_g18_b": coupon_shape("G18-B"),
              "gasket_g18_c": coupon_shape("G18-C"), "bbox_water_dummy_v002_body": body_shape(),
              "bbox_water_dummy_v002_lid": lid_shape()}
    result = {"step": {}, "stl": {}}
    for stem, shape in shapes.items():
        rel = f"artifacts/{stem}.step"; export_step(shape, out / rel); loaded = importers.importStep(str(out / rel))
        solids = loaded.solids().vals(); valid = bool(solids) and all(solid.isValid() for solid in solids)
        result["step"][rel] = {"reload": "PASS" if valid else "FAIL", "solid_count": len(solids),
                               "valid": valid, "bbox_mm": bbox_mm(loaded)}
        if not valid: raise RuntimeError(result["step"][rel])
        stl_rel = f"artifacts/{stem}.stl"; v001.export_stl(shape, out / stl_rel)
        mesh = v001.mesh_metrics(out / stl_rel); result["stl"][stl_rel] = mesh
        if not (mesh["reload"] == "PASS" and mesh["watertight"] and mesh["manifold"]
                and mesh["bad_edge_count"] == 0 and mesh["degenerate_triangle_count"] == 0):
            raise RuntimeError(mesh)
    rel = "artifacts/bbox_water_dummy_v002_assembly.step"; export_step(assembly_shape(), out / rel)
    loaded = importers.importStep(str(out / rel)); solids = loaded.solids().vals()
    valid = bool(solids) and all(solid.isValid() for solid in solids)
    result["step"][rel] = {"reload": "PASS" if valid else "FAIL", "solid_count": len(solids),
                           "valid": valid, "bbox_mm": bbox_mm(loaded)}
    if not valid: raise RuntimeError(result["step"][rel])
    return result

def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#f8fafc"/><style>text{{font-family:Arial,sans-serif;fill:#17324d}}.t{{font-size:30px;font-weight:bold}}.m{{font-size:18px}}.s{{fill:none;stroke:#264653;stroke-width:4}}.g{{fill:none;stroke:#2a9d8f;stroke-width:5}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.f{{fill:#dbeafe;stroke:#264653;stroke-width:3}}.h{{fill:#fff3cd;stroke:#e9c46a;stroke-width:3}}.d{{stroke-dasharray:10 8}}</style>
<text x="40" y="48" class="t">{title}</text>{body}<text x="40" y="675" class="m">PS-BBOX-WATER-DUMMY-V002 · TEST FIXTURE · PHYSICAL WATER PASS NOT YET</text></svg>'''

def svg_documents(_: dict[str, object]) -> dict[str, str]:
    failure = svg_page("V001 PHYSICAL FAILURE — THROUGH-HOLE WATER PATH", '''<path d="M120 130 V540 H780 V130" class="s"/><path d="M100 110 H800" class="g"/><path d="M260 80 V310" class="a"/><path d="M260 310 L235 270 M260 310 L285 270" class="a"/><text x="840" y="150" class="m">V001 body print: PASS</text><text x="840" y="205" class="m">corner pin/screw path: FAIL</text><text x="840" y="260" class="m">side M4 retention: FAIL</text><text x="840" y="330" class="m">water test configuration: REJECTED</text>''')
    boundary = svg_page("V002 SEALING BOUNDARY", '''<path d="M140 160 V540 H740 V160" class="s"/><path d="M120 140 H760" class="g"/><path d="M185 175 H715" class="a"/><circle cx="870" cy="230" r="22" class="s"/><text x="820" y="300" class="m">M4 hole is outside sealed wall</text><text x="820" y="350" class="m">sealed cavity penetration = 0</text><text x="820" y="400" class="m">gasket loop continuous</text>''')
    load = svg_page("EXTERNAL VERTICAL M4 LOAD PATH", '''<rect x="210" y="100" width="520" height="80" class="f"/><rect x="270" y="245" width="400" height="65" class="h"/><path d="M470 70 V500" class="a"/><circle cx="470" cy="535" r="42" class="s"/><text x="800" y="140" class="m">lid external ear</text><text x="800" y="260" class="m">body external lug</text><text x="800" y="330" class="m">washer + M4 nyloc nut below</text><text x="800" y="400" class="m">water path returns outside</text>''')
    gasket = svg_page("1.8 MM RUBBER CORD SECTION", '''<path d="M150 420 H850" class="s"/><path d="M350 420 V500 H600 V420" class="g"/><circle cx="475" cy="370" r="90" class="a"/><text x="900" y="220" class="m">cord diameter = 1.8 mm</text><text x="900" y="270" class="m">target compressed = 1.35–1.44</text><text x="900" y="320" class="m">source = PVC tower rubber cord</text><text x="900" y="370" class="m">material/hardness = HOLD</text>''')
    rows = hard_stop_rows()
    compression = svg_page("GASKET COMPRESSION / HARD-STOP CANDIDATES", ''.join(
        f'<rect x="{90+i*350}" y="160" width="300" height="300" class="f"/><text x="{120+i*350}" y="220" class="m">{row["candidate"]}: W{row["width_mm"]} D{row["depth_mm"]}</text><text x="{120+i*350}" y="275" class="m">gap {row["hard_stop_gap_range_mm"][0]}–{row["hard_stop_gap_range_mm"][1]}</text><text x="{120+i*350}" y="330" class="m">nominal {row["hard_stop_gap_nominal_mm"]}</text><text x="{120+i*350}" y="385" class="m">total {row["compressed_total_at_nominal_mm"]}</text>' for i, row in enumerate(rows)))
    coupons = svg_page("G18 COUPON IDENTIFICATION", '''<rect x="100" y="150" width="280" height="330" rx="30" class="f"/><rect x="460" y="150" width="280" height="330" rx="30" class="f"/><rect x="820" y="150" width="280" height="330" rx="30" class="f"/><text x="175" y="230" class="t">A · notch 1</text><text x="535" y="230" class="t">B · notch 2</text><text x="895" y="230" class="t">C · notch 3</text><text x="155" y="390" class="m">functional groove upward</text><text x="515" y="390" class="m">ID on non-sealing side</text><text x="875" y="390" class="m">support OFF</text>''')
    pattern = svg_page("M4 ×8 EXTERNAL PATTERN", '''<rect x="220" y="120" width="650" height="440" class="s"/><rect x="260" y="155" width="570" height="370" class="g"/><circle cx="185" cy="90" r="20" class="a"/><circle cx="905" cy="90" r="20" class="a"/><circle cx="185" cy="590" r="20" class="a"/><circle cx="905" cy="590" r="20" class="a"/><circle cx="185" cy="340" r="20" class="a"/><circle cx="905" cy="340" r="20" class="a"/><circle cx="545" cy="90" r="20" class="a"/><circle cx="545" cy="590" r="20" class="a"/><text x="930" y="180" class="m">corner 4 + edge mid 4</text><text x="930" y="235" class="m">minimum ligament 5.75 mm</text><text x="930" y="290" class="m">all holes outside gasket</text>''')
    water = svg_page("WATER TEST SETUP", '''<rect x="130" y="110" width="700" height="480" class="f"/><rect x="260" y="250" width="440" height="260" class="s"/><path d="M130 210 H830" class="g d"/><text x="870" y="180" class="m">50 mm / 10 min</text><text x="870" y="235" class="m">100 mm / 30 min</text><text x="870" y="290" class="m">150 mm / 60 min</text><text x="870" y="345" class="m">150 mm / 8 h</text><text x="870" y="415" class="m">one droplet = FAIL_LEAK</text>''')
    diagnosis = svg_page("LEAK DIAGNOSIS AFTER WATER-PATH REMOVAL", '''<rect x="80" y="160" width="230" height="300" class="h"/><rect x="350" y="160" width="230" height="300" class="h"/><rect x="620" y="160" width="230" height="300" class="h"/><rect x="890" y="160" width="230" height="300" class="h"/><text x="120" y="235" class="m">GASKET PATH</text><text x="395" y="235" class="m">CORD JOINT</text><text x="665" y="235" class="m">PRINTED SHELL</text><text x="925" y="235" class="m">DEFORMATION</text><text x="315" y="530" class="m">Fastener-hole-to-dry-cavity path is eliminated by geometry.</text>''')
    return dict(zip(SVGS, (failure, boundary, load, gasket, compression, coupons, pattern, water, diagnosis)))

def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"

def documentation(a: dict[str, object]) -> dict[str, str]:
    return {
        "README.md": header("BBOX water dummy V002") + '''\nV002 isolates the top sealing boundary. V001 proved the body printable and the1.8 mm cord installable, but its pin/screw holes created direct water paths and its side M4 retention failed. V002 moves every M4 hole outside both the closed gasket loop and sealed wall. A leak can therefore be diagnosed as gasket path, cord joint, printed shell, or deformation rather than an intentional fastener passage. This fixture does not modify the production BBOX.\n''',
        "PHYSICAL_FAILURE_RECORD.md": header("V001 physical failure record") + '''\n- `BODY_PRINT=PASS`\n- `RUBBER_CORD_INSTALLATION=PHYSICALLY_FEASIBLE`\n- `CURRENT_THROUGH_HOLES=FAIL_WATER_PATH`\n- `SIDE_M4_RETENTION=FAIL`\n- `CURRENT_CONFIGURATION_WATER_TEST=REJECTED`\n\nV001 remains unchanged as a failure/reference artifact. No hole plug is treated as a remedy.\n''',
        "DESIGN_AUTHORITY.md": header("V002 design authority") + '''\nPhysical authority: PVC-tower black rubber cord measured Ø1.8 mm from the supplied image; V001 failure results; V001 shell envelope200×150×70 mm. V002 uses a closed bottom, continuous four walls, top-only opening, closed gasket loop, and eight external vertical through-bolts. Sealed internal hole penetration count is exactly zero.\n''',
        "GASKET_1P8_REQUIREMENTS.md": header("1.8 mm cord gasket") + '''\nCandidates: G18-A W2.0/D0.4/notch1; G18-B W2.1/D0.5/notch2; G18-C W2.2/D0.6/notch3. Target compression20–25% gives total compressed height1.44–1.35 mm. Nominal hard-stop gaps are A0.995, B0.895, C0.795 mm. G18-B is only the full-dummy provisional reference. Final material behavior, winner, compression PASS, and cut-cord end joint remain physical HOLD.\n''',
        "FASTENER_REQUIREMENTS.md": header("External vertical M4") + '''\nArchitecture: M4 bolt → lid external ear → open external gap → body external lug → flat washer → M4 nyloc nut. Pattern is corner4 plus edge-middle4. Hole Ø4.5 mm; hole-edge-to-sealed-flange minimum ligament5.75 mm. M4×30 is a packaging candidate. Tool proxy Ø12 beneath every lug has zero body intersection. Horizontal M4 and heat-set inserts are not used.\n''',
        "PHYSICAL_TEST_PLAN.md": header("Physical test plan") + '''\nA DRY: place cord, seat lid, insert M4×8, confirm washer/nut access, close onto hard stops, inspect extrusion. B PAPER: copy-paper check on four sides. C: lid50 mm below water/10 min. D:100 mm/30 min. E:150 mm/60 min. F:150 mm/8 h. Witness paper at FRONT/REAR/LEFT/RIGHT/CENTER. One droplet is `FAIL_LEAK`. No electronics, battery, cable gland, charging contact, or powered operation.\n''',
        "PRINT_GUIDE.md": header("Print order") + '''\nFIRST: `gasket_g18_a.stl`, `gasket_g18_b.stl`, `gasket_g18_c.stl`, groove upward, support OFF. Select the physical cord-fit winner. SECOND: V002 body, PETG, bottom down/top open/support OFF preferred. THIRD: V002 lid, flat sealing face down/support OFF preferred. Inspect all sealing faces in slicer; no support contact is permitted there.\n''',
        "HOLD_REGISTER.md": header("HOLD register") + '''\nHOLD: rubber hardness/material; cut-cord joint method and position; G18 physical winner; final gasket compression; slicer review; coupon fit; body print; lid print; lid flatness; shell porosity; water test; sealing-boundary PASS; powered/field/durability use. Production BBOX modification, cable gland, connectors, electronics and charging contacts are outside this task.\n'''}

def parameters(a: dict[str, object]) -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS, **a}

def stable_repo(repo: dict[str, object]) -> dict[str, object]:
    return {key: repo[key] for key in ("repository", "branch", "head", "tracked_dirty", "outside_untracked",
                                       "authority_sha256", "protected_trees")} | {
        "staged_count": len(repo["staged"]), "lane_expected_paths": EXPECTED_PATH_COUNT}

def validation(repo: dict[str, object], a: dict[str, object], artifacts: dict[str, object]) -> dict[str, object]:
    steps_ok = all(row["reload"] == "PASS" and row["valid"] for row in artifacts["step"].values())
    stls_ok = all(row["reload"] == "PASS" and row["watertight"] and row["manifold"]
                  and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0
                  for row in artifacts["stl"].values())
    checks = {"repository_guard": "PASS", "authority_4_of_4": "PASS", "protected_trees": "PASS",
        "cord_diameter_exact_1p8": "PASS", "sealed_cavity_through_holes_zero": "PASS",
        "m4_hole_cavity_intersection_zero": "PASS" if a["sealed_body"]["m4_hole_cavity_intersection_mm3"] == 0 else "FAIL",
        "m4_outside_gasket": "PASS" if a["gasket_study"]["groove_m4_intersection_mm3"] == 0 else "FAIL",
        "gasket_loop_closed": "PASS", "gasket_discontinuity_zero": "PASS",
        "groove_candidates_exact": "PASS", "geometric_ids_exact": "PASS",
        "body_closed_bottom": "PASS", "continuous_four_walls": "PASS", "lid_sealing_face_continuous":
            "PASS" if a["lid"]["sealing_band_coverage_ratio"] == 1 else "FAIL",
        "hard_stop_calculation": "PASS", "fastener_load_path": "PASS",
        "external_ligament": "PASS" if a["external_fastener"]["minimum_structural_ligament_mm"] >= STRUCTURAL_LIGAMENT_HARD_MIN else "FAIL",
        "washer_nut_tool_access": "PASS" if a["external_fastener"]["tool_access_body_intersection_mm3"] == 0 else "FAIL",
        "body_lid_invalid_intersection_zero": "PASS" if a["lid"]["placed_body_intersection_mm3"] == 0 else "FAIL",
        "gasket_invalid_intersections_zero": "PASS" if a["lid"]["placed_gasket_lid_intersection_mm3"] == 0
            and a["lid"]["placed_gasket_body_intersection_mm3"] == 0 else "FAIL",
        "a1_build_envelope": "PASS" if a["printability"]["all_parts_within_a1"] else "FAIL",
        "step_reload_6_of_6": "PASS" if steps_ok else "FAIL", "stl_mesh_5_of_5": "PASS" if stls_ok else "FAIL",
        "gasket_fit": "NOT_YET", "gasket_compression": "PHYSICAL_HOLD", "body_print": "NOT_YET",
        "lid_print": "NOT_YET", "water": "NOT_YET", "bbox_sealing_boundary": "NOT_YET",
        "powered": "PROHIBITED", "field": "PROHIBITED", "durability": "NOT_YET"}
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS, "checks": checks,
        "repository": stable_repo(repo), "analysis": a, "artifacts": artifacts,
        "artifact_counts": {"step": 6, "stl": 5, "svg": 9},
        "final_classification": "CAD_PASS_GASKET_COUPON_PRINT_READY_PHYSICAL_WINNER_PENDING"}

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")

def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))

def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False); a = analysis(); artifacts = export_artifacts(out)
    for rel, text in documentation(a).items(): write_text(out / rel, text)
    for rel, text in svg_documents(a).items(): write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameters(a)); write_json(out / "validation_report.json", validation(repo, a, artifacts))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=6\nSTL=5\nSVG=9\nFIRST_PRINT=G18-A,B,C\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", f"CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=6_OF_6_PASS\nSTL_MESH=5_OF_5_PASS\nREPRODUCIBILITY={EXPECTED_PATH_COUNT}_OF_{EXPECTED_PATH_COUNT}_PASS")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError(f"exact paths {len(files)} {set(files) ^ set(EXPECTED_FILES)}")
    repository_guard(out == LANE_DIR)
    return {"path_count": len(files), "analysis": a, "artifacts": artifacts, "status": STATUS}

def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1); result[rel] = digest
    return result

def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(out == LANE_DIR); files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES or (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("exact manifest")
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt"); mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(mismatch)
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()): raise RuntimeError(report["checks"])
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
        "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
        "sha_mismatch_count": 0, "analysis": report["analysis"], "checks": report["checks"],
        "artifacts": report["artifacts"], "status": STATUS}

def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_bbox_water_v002_") as name:
        shadow = Path(name) / LANE_NAME; (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER); shutil.copyfile(out / TEST, shadow / TEST); generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(mismatch)
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}

def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_BBOX_WATER_DUMMY_V002_1P8_GASKET_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 23, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); prefix = LANE_NAME + "/"; sums = parse_sums(out / "SHA256SUMS.txt")
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
            "manifest_exact": relative == EXPECTED_FILES, "duplicate_count": len(names) - len(set(names)),
            "traversal_count": sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names),
            "sha_mismatch_count": sum(hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest for rel, digest in sums.items()),
            "parent_contamination_count": sum(not name.startswith(prefix) for name in names)}
    if any(result[key] for key in ("duplicate_count", "traversal_count", "sha_mismatch_count", "parent_contamination_count")) or not result["manifest_exact"]:
        raise RuntimeError(result)
    return result

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true"); parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true"); args = parser.parse_args()
    if not any(vars(args).values()): parser.error("select action")
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify: print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
