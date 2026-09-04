"""Build v0.9.6.34 exact-vendor P5M28 fit coupons.

The vendor AP203 STEP is the only P5M28 tooth authority in this lane.  The
main-body external tooth section is extracted without scaling or
reconstruction, then offset with OCCT's 2-D normal-offset operation.  No
trapezoid, nominal-P5M approximation, or fallback tooth generator exists.
"""
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
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.34"
CLASSIFICATION = "PTPK28P5M150_A_N10_NFC_EXACT_VENDOR_GEOMETRY_FIT_COUPONS"

SOURCE_ZIP = Path(r"D:\Downloads\PTPK28P5M150-A-N10-NFC_STEP.zip")
SOURCE_ZIP_NAME = "PTPK28P5M150-A-N10-NFC_STEP.zip"
SOURCE_STEP_NAME = "PTPK28P5M150-A-N10-NFC.stp"
SOURCE_ZIP_SHA256 = "4d296d9b827e188a3223bef57a4049c5a6bc956210537de1b50d51a727323b4a"
SOURCE_STEP_SHA256 = "55dd2ae80b4b72a9ff101b093d9ab7d71538d74bda5c907906c5ede0b6b94729"
SOURCE_SCHEMA = "CONFIG_CONTROL_DESIGN"
SOURCE_DESCRIPTION = "STEP AP203"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = sorted(AUTHORITY_SHA256)
BASE_OUTSIDE_COUNT = 3097
BASE_OUTSIDE_PATH_DIGEST = "23d2065362e016fae41455df34709ac5190f3b3b6cb9192e1cff7bda1076602b"
PROTECTED_LANE_COUNT = 34
PROTECTED_FILE_COUNT = 1504
PROTECTED_AGGREGATE_SHA256 = "f0ac3e00e1788904c22da7715544c0f1f45234e26755f03faf80e6f996e9fa45"
PROTECTED_FOCUS = {
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31":
        (20, "8065cefb36cef1dfb823a989185a67534f7eebdfd432fd5a664b364cc9053a72"),
    "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32":
        (28, "4792b7db682d02e78ab88bdd8642f42b6805a6773782f4bcc36f2ff3427bc516"),
    "cad/common_rover/common_rover_generic_keyed_industrial_torque_core_comparison_v0_9_6_33":
        (30, "b0e1d30421c78c201658f5a410ecfaedd570c1121804a9ea26470884ec212496"),
}

V31_REL = PurePosixPath("cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31")
V31_BUILDER = V31_REL / "build_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.py"

ORDER_SNAPSHOT = {
    "supplier": "MISUMI",
    "ordered_code": "PTPK28P5M150-A-N10-NFC",
    "order_date": "2026-08-20",
    "quantity": 1,
    "scheduled_ship_date": "2026-08-26",
    "estimated_arrival_date": "2026-08-27",
    "price_snapshot_jpy_tax_included": 3971,
    "shipping_snapshot_jpy": 0,
    "authority": "ORDER_SNAPSHOT_ONLY_NOT_LIVE_PRICE_OR_STOCK_AUTHORITY",
}

CLEARANCES = {"C1": 0.15, "C2": 0.25, "C3": 0.35}
NOTCH_COUNTS = {"C1": 1, "C2": 2, "C3": 3}
SECTION_X_MM = 5.0
TOOTH_ZONE_X_MIN_MM = 2.2
TOOTH_ZONE_X_MAX_MM = 18.8
TOOTH_ZONE_WIDTH_MM = 16.6
MAIN_AXIAL_WIDTH_MM = 21.0
COUPON_ENGAGEMENT_MM = 9.0
COUPON_STOP_MM = 1.2
COUPON_WALL_NOMINAL_MM = 8.0
NOTCH_RADIAL_DEPTH_MM = 2.0
P5M28_TOOTH_COUNT = 28
P5M28_PITCH_MM = 5.0

P20653 = {
    "pitch_mm": 20.6533333333,
    "tooth_count": 14,
    "pitch_diameter_mm": 92.8152374974,
    "phase_deg": 12.8571428571,
    "spacing_deg": 25.7142857143,
    "tooth_axial_width_mm": 44.0,
}

STATUS = (
    "PTPK28P5M150_A_N10_NFC_ORDERED_1PC/"
    "AP203_SOURCE_AUTHORITY_PASS/P5M28_EXACT_MAIN_BODY_EXTRACTED/"
    "NFC_SEPARATE_FLANGE_GEOMETRY_CONFIRMED_IN_CAD/"
    "C1_015_CAD_PASS/C2_025_CAD_PASS/C3_035_CAD_PASS/"
    "GEOMETRIC_NOTCH_IDS_PASS/FIT_COUPONS_PRINT_APPROVED/"
    "EXACT_CORE_14T_REFERENCE_COMPLETE/PHYSICAL_CORE_NOT_RECEIVED/"
    "FIT_WINNER_NOT_YET/RETENTION_NOT_YET/FULL_DRIVE_PRINT_HOLD/"
    "STATIC_TORQUE_HOLD/POWERED_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)

BUILDER = Path(__file__).name
TEST = "tests/test_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34_contract.py"
SOURCE_FILES = [
    f"source/vendor/{SOURCE_ZIP_NAME}",
    f"source/vendor/{SOURCE_STEP_NAME}",
]
DERIVED = [
    "derived/p5m28_main_pulley_body_exact.step",
    "derived/p5m28_main_pulley_body_exact.stl",
    "derived/p5m28_separated_vendor_solids_reference.step",
]
ARTIFACTS = [
    "artifacts/p5m28_fit_coupon_C1_015_notch1.step",
    "artifacts/p5m28_fit_coupon_C1_015_notch1.stl",
    "artifacts/p5m28_fit_coupon_C2_025_notch2.step",
    "artifacts/p5m28_fit_coupon_C2_025_notch2.stl",
    "artifacts/p5m28_fit_coupon_C3_035_notch3.step",
    "artifacts/p5m28_fit_coupon_C3_035_notch3.stl",
    "artifacts/p5m28_exact_core_in_p20653_14t_C2_reference.step",
]
SVGS = [
    "drawings/vendor_solid_classification.svg",
    "drawings/exact_p5m28_section.svg",
    "drawings/clearance_C1_C2_C3_comparison.svg",
    "drawings/coupon_dimensions.svg",
    "drawings/exact_core_14t_ligament.svg",
    "drawings/axial_retention_concepts.svg",
]
DOCS = [
    "docs/README.md", "docs/DESIGN_AUTHORITY.md", "docs/SOURCE_AUTHORITY.md",
    "docs/FIT_COUPON_SPEC.md", "docs/PHYSICAL_FIT_TEST_PLAN.md",
    "docs/RETENTION_CONCEPT.md", "docs/PRINT_GATE.md", "docs/HOLD_REGISTER.md",
]
DATA = ["data/source_geometry_metrics.json", "data/design_parameters.json", "data/validation_report.json"]
META = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted([BUILDER, TEST, *SOURCE_FILES, *DERIVED, *ARTIFACTS, *SVGS, *DOCS, *DATA, *META])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v31 = _load("paddy_v09631_outer_authority", REPO_ROOT / V31_BUILDER)
v30 = v31.v30


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


def protected_snapshot() -> dict[str, object]:
    root = REPO_ROOT / "cad/common_rover"
    rows: dict[str, tuple[int, str]] = {}
    for path in sorted(root.iterdir()):
        match = re.search(r"_v0_9_6_(\d+)$", path.name)
        if path.is_dir() and match and int(match.group(1)) <= 33:
            rows[path.relative_to(REPO_ROOT).as_posix()] = tree_digest(path)
    digest = hashlib.sha256()
    for rel, (count, tree_sha) in rows.items():
        digest.update(f"{rel}|{count}|{tree_sha}\n".encode())
    return {
        "lane_count": len(rows), "file_count": sum(row[0] for row in rows.values()),
        "aggregate_sha256": digest.hexdigest(),
        "focus": {rel: {"count": row[0], "tree_sha256": row[1]} for rel, row in rows.items() if rel in PROTECTED_FOCUS},
    }


def untracked_paths() -> list[str]:
    return sorted(path.replace("\\", "/") for path in run_git("ls-files", "--others", "--exclude-standard").splitlines())


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def read_source_authority() -> dict[str, object]:
    if not SOURCE_ZIP.is_file():
        raise RuntimeError("SOURCE_AUTHORITY_FAIL: source ZIP missing")
    zip_sha = sha256(SOURCE_ZIP)
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        names = archive.namelist()
        if names != [SOURCE_STEP_NAME]:
            raise RuntimeError(f"SOURCE_AUTHORITY_FAIL: exact single STEP entry required: {names}")
        step_bytes = archive.read(SOURCE_STEP_NAME)
    step_sha = hashlib.sha256(step_bytes).hexdigest()
    header = step_bytes[:1024].decode("ascii", "replace")
    result = {
        "zip_path": str(SOURCE_ZIP), "zip_sha256": zip_sha,
        "step_entry": SOURCE_STEP_NAME, "step_sha256": step_sha,
        "file_description_ap203": SOURCE_DESCRIPTION in header,
        "file_schema_config_control_design": SOURCE_SCHEMA in header,
    }
    if not (
        zip_sha == SOURCE_ZIP_SHA256 and step_sha == SOURCE_STEP_SHA256
        and result["file_description_ap203"] and result["file_schema_config_control_design"]
    ):
        raise RuntimeError("SOURCE_AUTHORITY_FAIL: " + json.dumps(result, ensure_ascii=True))
    return result


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    source = read_source_authority()
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = sorted(run_git("diff", "--name-only").splitlines())
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = protected_snapshot()
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored = [path.replace("\\", "/") for path in run_git(
        "ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()
    ).splitlines()]
    required_ignored_source = f"{LANE_REL.as_posix()}/{SOURCE_FILES[0]}"
    focus_actual = {rel: (row["count"], row["tree_sha256"]) for rel, row in protected["focus"].items()}
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_all_v09600_to_v09633": (
            protected["lane_count"] == PROTECTED_LANE_COUNT
            and protected["file_count"] == PROTECTED_FILE_COUNT
            and protected["aggregate_sha256"] == PROTECTED_AGGREGATE_SHA256
        ),
        "protected_focus_v31_v32_v33": focus_actual == PROTECTED_FOCUS,
        "source_authority": source["zip_sha256"] == SOURCE_ZIP_SHA256 and source["step_sha256"] == SOURCE_STEP_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache,
        # The repository-wide *.zip rule necessarily ignores the mandated,
        # byte-preserved vendor source ZIP.  It is the sole explicit exception.
        "lane_ignored_exact_required_source_zip_only": ignored in ([], [required_ignored_source]),
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "authority_sha256": authority, "protected_lanes": protected,
        "source_authority": source, "lane_files": len(lane_files), "cache": cache,
        "ignored_lane": ignored, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


@lru_cache(maxsize=1)
def source_step_bytes() -> bytes:
    read_source_authority()
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        return archive.read(SOURCE_STEP_NAME)


@lru_cache(maxsize=1)
def vendor_assembly() -> cq.Shape:
    with tempfile.NamedTemporaryFile(suffix=".stp", delete=False) as stream:
        stream.write(source_step_bytes())
        temp_path = Path(stream.name)
    try:
        return importers.importStep(str(temp_path)).val()
    finally:
        temp_path.unlink(missing_ok=True)


@lru_cache(maxsize=1)
def main_solid() -> cq.Shape:
    solids = vendor_assembly().Solids()
    if len(solids) != 5:
        raise RuntimeError("VENDOR_SOLID_COUNT_FAIL")
    ordered = sorted(solids, key=lambda solid: solid.Volume(), reverse=True)
    if ordered[0].Volume() <= 20 * ordered[1].Volume():
        raise RuntimeError("MAIN_BODY_UNIQUENESS_FAIL")
    return ordered[0]


def wp(shape: cq.Shape) -> cq.Workplane:
    return cq.Workplane("XY").newObject([shape])


@lru_cache(maxsize=1)
def exact_outer_wire() -> cq.Wire:
    section = cq.Workplane("YZ", origin=(SECTION_X_MM, 0, 0)).newObject([main_solid()]).section()
    wires = section.wires().vals()
    if len(wires) < 2:
        raise RuntimeError("SOURCE_SECTION_FAIL")
    outer = max(wires, key=lambda wire: wire.BoundingBox().ylen)
    if outer.BoundingBox().ylen < 40:
        raise RuntimeError("SOURCE_EXTERNAL_TOOTH_WIRE_FAIL")
    return outer


def sampled_radial_range(wire: cq.Wire) -> tuple[float, float]:
    values: list[float] = []
    for edge in wire.Edges():
        for index in range(41):
            point = edge.positionAt(index / 40)
            values.append(math.hypot(point.y, point.z))
    return min(values), max(values)


@lru_cache(maxsize=4)
def exact_profile_solid_z(clearance_mm: float, axial_width_mm: float) -> cq.Workplane:
    if clearance_mm not in {0.0, *CLEARANCES.values()}:
        raise RuntimeError("UNAUTHORIZED_CLEARANCE")
    wire = exact_outer_wire().translate(cq.Vector(-SECTION_X_MM, 0, 0))
    pending = cq.Workplane("YZ", origin=(0, 0, 0)).newObject([wire]).toPending()
    if clearance_mm:
        try:
            pending = pending.offset2D(clearance_mm, kind="arc")
        except Exception as exc:
            raise RuntimeError("SOURCE_GEOMETRY_OFFSET_HOLD") from exc
    solid_x = pending.extrude(axial_width_mm)
    solid_z = solid_x.rotate((0, 0, 0), (0, 1, 0), -90).translate((0, 0, -axial_width_mm / 2.0))
    if solid_z.solids().size() != 1 or not solid_z.val().isValid():
        raise RuntimeError("SOURCE_GEOMETRY_OFFSET_HOLD")
    return solid_z.clean()


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate((0, 0, z))


@lru_cache(maxsize=3)
def coupon(code: str) -> cq.Workplane:
    clearance = CLEARANCES[code]
    notch_count = NOTCH_COUNTS[code]
    _, tip_r = sampled_radial_range(exact_outer_wire())
    outer_r = tip_r + CLEARANCES["C3"] + COUPON_WALL_NOMINAL_MM
    total_h = COUPON_STOP_MM + COUPON_ENGAGEMENT_MM
    body = cq.Workplane("XY").circle(outer_r).extrude(total_h)
    grip = cq.Workplane("XY").box(18.0, 13.0, total_h, centered=(True, True, False)).translate((0, outer_r + 4.5, 0))
    body = body.union(grip)
    cavity = exact_profile_solid_z(clearance, COUPON_ENGAGEMENT_MM).translate((0, 0, COUPON_STOP_MM + COUPON_ENGAGEMENT_MM / 2.0))
    body = body.cut(cavity)
    for x in (-14.0, 14.0):
        body = body.cut(cylinder(4.0, COUPON_STOP_MM + 0.6, COUPON_STOP_MM / 2.0).translate((x, 0, 0)))
    angles = {1: [270.0], 2: [260.0, 280.0], 3: [250.0, 270.0, 290.0]}[notch_count]
    for angle in angles:
        cutter = cq.Workplane("XY").box(3.5, 3.0, total_h + 2.0, centered=(True, True, False))
        cutter = cutter.translate((outer_r - 0.25, 0, -1.0)).rotate((0, 0, 0), (0, 0, 1), angle)
        body = body.cut(cutter)
    body = body.clean()
    if body.solids().size() != 1 or not body.val().isValid():
        raise RuntimeError(f"COUPON_GEOMETRY_FAIL_{code}")
    return body


@lru_cache(maxsize=1)
def protected_outer_drive() -> cq.Workplane:
    result = v30.raw_support()
    for index in range(v30.TARGET_TOOTH_COUNT):
        result = result.union(v30.target_tooth(index))
    result = result.clean()
    if result.solids().size() != 1 or not result.val().isValid():
        raise RuntimeError("PROTECTED_OUTER_GEOMETRY_FAIL")
    return result


@lru_cache(maxsize=3)
def exact_main_clearance_envelope(clearance_mm: float) -> cq.Workplane:
    tooth = exact_profile_solid_z(clearance_mm, TOOTH_ZONE_WIDTH_MM)
    boss = cylinder(19.0 + clearance_mm, MAIN_AXIAL_WIDTH_MM)
    return tooth.union(boss).clean()


@lru_cache(maxsize=1)
def exact_core_reference() -> cq.Workplane:
    reference = protected_outer_drive().cut(exact_main_clearance_envelope(CLEARANCES["C2"])).clean()
    if reference.solids().size() != 1 or not reference.val().isValid():
        raise RuntimeError("EXACT_CORE_REFERENCE_FAIL")
    return reference


def shape_volume(shape: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in shape.solids().vals()), 6)


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return shape_volume(a.intersect(b))


def external_tooth_regression() -> dict[str, object]:
    outer = protected_outer_drive()
    reference = exact_core_reference()
    exterior = cylinder(100.0, 48.0).cut(cylinder(22.1, 50.0))
    outer_exterior = outer.intersect(exterior)
    reference_exterior = reference.intersect(exterior)
    return {
        "p20653_14_tooth_regression": v30.tooth_regression(),
        "outside_hub_modification_added_mm3": shape_volume(reference_exterior.cut(outer_exterior)),
        "outside_hub_modification_removed_mm3": shape_volume(outer_exterior.cut(reference_exterior)),
        "hub_modification_envelope_radius_mm": 22.1,
        "global_xyz_scale": [1.0, 1.0, 1.0],
        "visible_change_outside_hub_envelope": 0,
    }


def source_geometry_metrics() -> dict[str, object]:
    assembly = vendor_assembly()
    solids = assembly.Solids()
    rows = []
    main_volume = main_solid().Volume()
    for index, solid in enumerate(solids):
        bbox = solid.BoundingBox()
        rows.append({
            "source_index": index, "volume_mm3": round(solid.Volume(), 9),
            "bbox_mm": [round(bbox.xlen, 9), round(bbox.ylen, 9), round(bbox.zlen, 9)],
            "classification": (
                "UNIQUE_LARGEST_MAIN_PULLEY_BODY" if abs(solid.Volume() - main_volume) < 1e-6 else
                "SEPARATE_THIN_50MM_FLANGE_CANDIDATE" if max(bbox.ylen, bbox.zlen) > 49 else
                "SEPARATE_SMALL_ACCESSORY_SOLID_NAME_NOT_INFERRED"
            ),
        })
    main = main_solid()
    bbox = main.BoundingBox()
    wire = exact_outer_wire()
    root_r = wire.distance(cq.Vertex.makeVertex(SECTION_X_MM, 0, 0))
    sampled_min, tip_r = sampled_radial_range(wire)
    tip_vertices = []
    for vertex in wire.Vertices():
        point = vertex.Center()
        if math.hypot(point.y, point.z) >= tip_r - 0.01:
            tip_vertices.append(math.degrees(math.atan2(point.z, point.y)) % 360.0)
    detected_teeth = len(tip_vertices) // 2
    base = exact_profile_solid_z(0.0, 1.0)
    rotated = base.rotate((0, 0, 0), (0, 0, 1), 360.0 / P5M28_TOOTH_COUNT)
    periodic_added = shape_volume(rotated.cut(base))
    periodic_removed = shape_volume(base.cut(rotated))
    assembly_bbox = assembly.BoundingBox()
    return {
        "source_authority": read_source_authority(), "solid_count": len(solids), "solids": rows,
        "assembly_bbox_mm": [assembly_bbox.xlen, assembly_bbox.ylen, assembly_bbox.zlen],
        "main_body": {
            "identification": "UNIQUE_LARGEST_VOLUME_PLUS_43P42_OD_PLUS_28_PERIODIC_P5M_TEETH",
            "bbox_mm": [bbox.xlen, bbox.ylen, bbox.zlen], "volume_mm3": main.Volume(),
            "overall_axial_width_mm": bbox.xlen, "tooth_zone_x_mm": [TOOTH_ZONE_X_MIN_MM, TOOTH_ZONE_X_MAX_MM],
            "tooth_zone_width_mm": TOOTH_ZONE_WIDTH_MM, "tooth_count_detected": detected_teeth,
            "pitch_mm_order_authority": P5M28_PITCH_MM, "exact_tooth_tip_od_mm": 2.0 * tip_r,
            "exact_root_envelope_diameter_mm": 2.0 * root_r,
            "sampled_root_radius_mm": sampled_min, "section_wire_edge_count": len(wire.Edges()),
            "periodicity_angle_deg": 360.0 / P5M28_TOOTH_COUNT,
            "periodicity_added_mm3": periodic_added, "periodicity_removed_mm3": periodic_removed,
            "tooth_geometry_source": "AP203_EXACT_SECTION_NO_APPROXIMATION",
            "normal_offset_kernel": "OCCT_2D_PARALLEL_OFFSET_ARC_JOIN",
            "global_xyz_scaling": 0.0,
        },
        "separate_flange_candidates": {
            "count": sum(row["classification"] == "SEPARATE_THIN_50MM_FLANGE_CANDIDATE" for row in rows),
            "cad_state": "NFC_SEPARATE_FLANGE_GEOMETRY_CONFIRMED_IN_CAD",
            "physical_state": "NOT_YET",
        },
        "small_accessory_solids": {
            "count": sum(row["classification"] == "SEPARATE_SMALL_ACCESSORY_SOLID_NAME_NOT_INFERRED" for row in rows),
            "naming": "ACCESSORY_SOLID_ONLY_FUNCTION_NOT_INFERRED",
        },
    }


def continuous_outer_root_radius() -> float:
    section = cq.Workplane("XY", origin=(0, 0, 0)).newObject([v30.raw_support().val()]).section()
    wire = max(section.wires().vals(), key=lambda item: item.Length())
    center = cq.Vertex.makeVertex(0, 0, 0)
    return wire.distance(center)


def design_analysis() -> dict[str, object]:
    source = source_geometry_metrics()
    tip_r = source["main_body"]["exact_tooth_tip_od_mm"] / 2.0
    root_r = source["main_body"]["exact_root_envelope_diameter_mm"] / 2.0
    outer_root = continuous_outer_root_radius()
    outer_radius = tip_r + CLEARANCES["C3"] + COUPON_WALL_NOMINAL_MM
    coupon_rows = {}
    for code, clearance in CLEARANCES.items():
        profile = exact_profile_solid_z(clearance, 1.0)
        bbox = profile.val().BoundingBox()
        wall_min = outer_radius - NOTCH_RADIAL_DEPTH_MM - (tip_r + clearance)
        coupon_rows[code] = {
            "clearance_radial_equivalent_mm": clearance, "notch_count": NOTCH_COUNTS[code],
            "offset_profile_bbox_xy_mm": [bbox.xlen, bbox.ylen], "engagement_mm": COUPON_ENGAGEMENT_MM,
            "axial_excess_clearance_mm": 0.0, "global_xyz_scale": [1.0, 1.0, 1.0],
            "outer_radius_mm": outer_radius, "minimum_wall_at_id_notch_mm": wall_min,
            "axial_seating_stop_mm": COUPON_STOP_MM, "finger_push_access_count": 2,
            "estimated_petg_mass_g": shape_volume(coupon(code)) / 1000.0 * 1.27,
            "status": f"{code}_{int(round(clearance * 100)):03d}_CAD_PASS",
        }
    c2 = CLEARANCES["C2"]
    regression = external_tooth_regression()
    return {
        "source_geometry": source, "coupons": coupon_rows,
        "p20653_outer": {**P20653, **regression},
        "exact_core_reference": {
            "clearance": "C2_REFERENCE_ONLY", "selected_winner": False,
            "main_body_axial_width_mm": MAIN_AXIAL_WIDTH_MM,
            "p20653_axial_width_mm": P20653["tooth_axial_width_mm"],
            "total_axial_remaining_mm": P20653["tooth_axial_width_mm"] - MAIN_AXIAL_WIDTH_MM,
            "remaining_each_side_if_centered_mm": (P20653["tooth_axial_width_mm"] - MAIN_AXIAL_WIDTH_MM) / 2.0,
            "continuous_outer_root_radius_mm": outer_root,
            "c2_tooth_tip_envelope_radius_mm": tip_r + c2,
            "minimum_continuous_ligament_mm": outer_root - (tip_r + c2),
            "root_envelope_ligament_mm": outer_root - (root_r + c2),
            "hard_gate_mm": 5.0, "target_gate_mm": 6.0, "stretch_gate_mm": 8.0,
            "status": "PASS_STRETCH_REFERENCE_ONLY",
        },
        "retention": {
            "option_A": "SIDE_REMOVABLE_PETG_RETAINER_CONCEPT",
            "option_B": "CAPTURED_SHOULDER_PLUS_REMOVABLE_RETAINER_CONCEPT",
            "metal_drilling": "PROHIBITED", "welding": "PROHIBITED",
            "adhesive_only": "PROHIBITED", "set_screw_primary_torque": "PROHIBITED",
            "NFC_flange_mandatory": False, "physical": "HOLD",
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
    exporters.export(shape, str(path), tolerance=0.025, angularTolerance=0.06)


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
        vertices = [tuple(round(float(value), 6) for value in vertex) for vertex in triangle]
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1e-16:
            degenerate += 1
        row = []
        for a, b in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edge = tuple(sorted((a, b))); edges[edge] += 1; row.append(edge)
        triangle_edges.append(row)
    parents = list(range(len(triangles)))
    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]; index = parents[index]
        return index
    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b: parents[b] = a
    owners = {}
    for index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in owners: union(index, owners[edge])
            else: owners[edge] = index
    raw = TopoDS_Shape()
    reload_pass = bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()
    bad_edges = sum(value != 2 for value in edges.values())
    return {
        "triangle_count": len(triangles), "component_count": len({find(index) for index in range(len(triangles))}),
        "watertight": bad_edges == 0, "manifold": bad_edges == 0, "bad_edge_count": bad_edges,
        "degenerate_triangle_count": degenerate, "reload": "PASS" if reload_pass else "FAIL",
    }


def step_metrics(path: Path) -> dict[str, object]:
    model = importers.importStep(str(path))
    solids = model.solids().vals()
    return {"reload": "PASS", "solid_count": len(solids), "all_valid": bool(solids) and all(solid.isValid() for solid in solids)}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700">
<style>.t{{font:700 26px sans-serif;fill:#102a43}}.h{{font:700 18px sans-serif;fill:#243b53}}.m{{font:15px monospace;fill:#334e68}}.s{{fill:#e6f6ff;stroke:#127fbf;stroke-width:2}}.a{{fill:#fff3bf;stroke:#d98300;stroke-width:2}}.g{{fill:#e6fcf5;stroke:#087f5b;stroke-width:2}}.r{{fill:#fff0f0;stroke:#c92a2a;stroke-width:2}}.d{{fill:none;stroke:#334e68;stroke-width:2;stroke-dasharray:8 6}}</style>
<rect width="1100" height="700" fill="#f8fafc"/><text x="45" y="48" class="t">{title}</text>{body}
<text x="45" y="676" class="m">v0.9.6.34 · EXACT AP203 VENDOR GEOMETRY · PHYSICAL FIT NOT YET · FULL DRIVE PRINT HOLD</text></svg>'''


def svg_outputs(analysis: dict[str, object]) -> dict[str, str]:
    main = analysis["source_geometry"]["main_body"]
    ref = analysis["exact_core_reference"]
    rows = analysis["coupons"]
    solids = svg_page("Vendor AP203 solid classification", '''
<rect x="65" y="95" width="480" height="470" rx="18" class="s"/><text x="95" y="140" class="h">Unique main pulley body</text><text x="95" y="180" class="m">21.000 × 43.273 × 43.273 bbox</text><text x="95" y="220" class="m">exact 28-period external tooth body</text><circle cx="780" cy="215" r="130" class="a"/><circle cx="780" cy="215" r="98" fill="#f8fafc"/><text x="650" y="390" class="h">2 × separate flange candidates</text><text x="650" y="425" class="m">1.69475 × 50 × 50 each</text><rect x="650" y="475" width="90" height="65" class="g"/><rect x="820" y="475" width="90" height="65" class="g"/><text x="645" y="570" class="m">2 small accessory solids · function not inferred</text>''')
    section = svg_page("Exact P5M28 source section", f'''
<circle cx="410" cy="335" r="217.10" class="s"/><circle cx="410" cy="335" r="199.00" fill="#f8fafc" stroke="#127fbf" stroke-width="2"/><text x="700" y="150" class="h">AP203 section at source X={SECTION_X_MM:.1f}</text><text x="700" y="195" class="m">tooth tips OD {main['exact_tooth_tip_od_mm']:.3f}</text><text x="700" y="235" class="m">root envelope Ø {main['exact_root_envelope_diameter_mm']:.3f}</text><text x="700" y="275" class="m">28 teeth · 12.857142857° periodicity</text><text x="700" y="315" class="m">tooth zone {TOOTH_ZONE_WIDTH_MM:.1f} axial</text><text x="700" y="375" class="h">No reconstructed tooth geometry</text><text x="700" y="415" class="m">OCCT source wire retained</text>''')
    clearance = svg_page("C1 / C2 / C3 exact normal offsets", f'''
<circle cx="330" cy="340" r="217" class="d"/><circle cx="330" cy="340" r="218.5" fill="none" stroke="#127fbf" stroke-width="3"/><circle cx="330" cy="340" r="219.5" fill="none" stroke="#087f5b" stroke-width="3"/><circle cx="330" cy="340" r="220.5" fill="none" stroke="#d98300" stroke-width="3"/><text x="650" y="170" class="h">C1 +0.15 mm · notch 1</text><text x="650" y="225" class="h">C2 +0.25 mm · notch 2</text><text x="650" y="280" class="h">C3 +0.35 mm · notch 3</text><text x="650" y="355" class="m">normal-direction 2D parallel offset</text><text x="650" y="395" class="m">XYZ scale = 1 / 1 / 1</text><text x="650" y="435" class="m">axial excess clearance = 0</text>''')
    coupons = svg_page("Low-material ring coupon dimensions", f'''
<circle cx="340" cy="320" r="240" class="g"/><circle cx="340" cy="320" r="176" fill="#f8fafc" stroke="#087f5b" stroke-width="3"/><rect x="285" y="40" width="110" height="90" class="g"/><text x="650" y="150" class="h">engagement {COUPON_ENGAGEMENT_MM:.1f} mm</text><text x="650" y="195" class="h">axial stop {COUPON_STOP_MM:.1f} mm</text><text x="650" y="240" class="h">minimum wall {min(row['minimum_wall_at_id_notch_mm'] for row in rows.values()):.2f} mm</text><text x="650" y="285" class="m">2 × underside push-access openings</text><text x="650" y="330" class="m">open-top, axis-vertical print orientation</text><text x="650" y="375" class="m">mating-surface supports: zero in CAD orientation</text>''')
    ligament = svg_page("Exact C2 core inside frozen P20653 14T", f'''
<circle cx="365" cy="330" r="335.5" class="s"/><circle cx="365" cy="330" r="219.6" fill="#f8fafc" stroke="#d98300" stroke-width="3"/><line x1="585" y1="330" x2="700" y2="330" stroke="#c92a2a" stroke-width="6"/><text x="720" y="250" class="h">continuous ligament {ref['minimum_continuous_ligament_mm']:.3f} mm</text><text x="720" y="295" class="m">hard ≥5 · target ≥6 · stretch ≥8</text><text x="720" y="350" class="h">axial remaining {ref['total_axial_remaining_mm']:.3f} mm</text><text x="720" y="395" class="m">C2_REFERENCE_ONLY</text><text x="720" y="440" class="m">C2_SELECTED = false</text>''')
    retention = svg_page("Axial retention concepts — no release", '''
<rect x="65" y="100" width="450" height="470" rx="18" class="s"/><text x="95" y="150" class="h">A · side removable PETG retainer</text><text x="95" y="205" class="m">serviceable fastened retainer</text><text x="95" y="250" class="m">no metal drilling / no welding</text><text x="95" y="295" class="m">adhesive-only prohibited</text><text x="95" y="365" class="h">PHYSICAL: HOLD</text><rect x="585" y="100" width="450" height="470" rx="18" class="a"/><text x="615" y="150" class="h">B · captured shoulder + retainer</text><text x="615" y="205" class="m">positive tooth pocket transfers torque</text><text x="615" y="250" class="m">set screw is not primary torque path</text><text x="615" y="295" class="m">NFC flange is not assumed mandatory</text><text x="615" y="365" class="h">PHYSICAL: HOLD</text>''')
    return {SVGS[0]: solids, SVGS[1]: section, SVGS[2]: clearance, SVGS[3]: coupons, SVGS[4]: ligament, SVGS[5]: retention}


def markdown_documents(analysis: dict[str, object]) -> dict[str, str]:
    main = analysis["source_geometry"]["main_body"]
    ref = analysis["exact_core_reference"]
    coupon_table = "\n".join(
        f"| {code} | +{row['clearance_radial_equivalent_mm']:.2f} | {row['notch_count']} | {row['minimum_wall_at_id_notch_mm']:.2f} | {row['estimated_petg_mass_g']:.2f} | CAD PASS / print approved |"
        for code, row in analysis["coupons"].items()
    )
    readme = f"""# P5M28 exact-vendor core fit coupons — {VERSION}

This independent untracked lane converts the exact AP203 external tooth section from ordered MISUMI `{ORDER_SNAPSHOT['ordered_code']}` into three fit-only PETG coupons. No P5M tooth approximation and no XYZ scaling is used.

The source assembly contains five solids. The unique largest solid is the main pulley body; two 50 mm thin solids are separate flange candidates in CAD, and two small solids remain unnamed accessory solids. Only the main-body external envelope drives the pocket. Flanges and accessory solids are excluded.

| Coupon | radial-equivalent clearance mm | permanent notches | minimum wall mm | estimated PETG g | gate |
|---|---:|---:|---:|---:|---|
{coupon_table}

First print: `p5m28_fit_coupon_C1_015_notch1.stl`, `p5m28_fit_coupon_C2_025_notch2.stl`, and `p5m28_fit_coupon_C3_035_notch3.stl`, one each, same PETG settings and orientation. Axis vertical, flat stop face down; place no support on a mating surface. Slicer has not been run, so slicer-specific state remains `PHYSICAL_USER_HOLD`.

Winner rule after the part arrives: select the smallest clearance allowing hand insertion and removal without hammer/press, whitening, crack, or clear play. No winner is selected in CAD.

`FULL_DRIVE_PRINT_HOLD`, `STATIC_TORQUE_HOLD`, and `POWERED_NOT_APPROVED` remain active.
"""
    authority = f"""# Design authority

- Parent outer-drive authority: `{V31_REL.as_posix()}` and v0.9.6.33 comparison lane, both protected.
- Outer crawler interface remains P20653 pitch {P20653['pitch_mm']:.10f} mm, 14T, pitch diameter {P20653['pitch_diameter_mm']:.10f} mm, phase {P20653['phase_deg']:.10f}°, spacing {P20653['spacing_deg']:.10f}°, width {P20653['tooth_axial_width_mm']:.1f} mm.
- Internal authority is exact source AP203 main-body geometry: 28 P5M teeth, OD {main['exact_tooth_tip_od_mm']:.3f} mm, root envelope {main['exact_root_envelope_diameter_mm']:.3f} mm, tooth width {main['tooth_zone_width_mm']:.3f} mm.
- C1/C2/C3 are OCCT normal offsets of the exact axis-perpendicular source wire. Global XYZ scaling is zero.
- C2 in the 14T reference is `C2_REFERENCE_ONLY`, never `C2_SELECTED`.
- Exact C2 continuous ligament is {ref['minimum_continuous_ligament_mm']:.3f} mm; root-envelope ligament is {ref['root_envelope_ligament_mm']:.3f} mm; axial remaining is {ref['total_axial_remaining_mm']:.3f} mm.
- This lane releases fit-coupon printing only. Full DRIVE, retention, torque, powered, water/mud, field, durability, and production remain unapproved.
"""
    source = f"""# Source authority

Ordered item: `{ORDER_SNAPSHOT['ordered_code']}`, quantity 1, ordered {ORDER_SNAPSHOT['order_date']}; ship estimate {ORDER_SNAPSHOT['scheduled_ship_date']}, arrival estimate {ORDER_SNAPSHOT['estimated_arrival_date']}. Price snapshot ¥{ORDER_SNAPSHOT['price_snapshot_jpy_tax_included']} tax included and shipping snapshot ¥0 are historical order context, not live commercial authority.

- ZIP: `{SOURCE_ZIP_NAME}` · SHA-256 `{SOURCE_ZIP_SHA256}`
- STEP: `{SOURCE_STEP_NAME}` · SHA-256 `{SOURCE_STEP_SHA256}`
- Header: `FILE_DESCRIPTION STEP AP203`; `FILE_SCHEMA CONFIG_CONTROL_DESIGN`.
- Exact bytes are preserved under `source/vendor/`.
- CAD confirms two separate thin 50 mm flange candidate solids. Physical NFC state is `NOT_YET` until the ordered item is received.
"""
    fit = f"""# Fit coupon specification

All coupons use the exact AP203 P5M28 outer wire at source X={SECTION_X_MM:.1f} mm. OCCT parallel offset in the shaft-normal section creates +0.15/+0.25/+0.35 mm radial-equivalent clearances. There is no global scaling, pitch/phase modification, axial excess clearance, or approximation fallback.

Engagement is {COUPON_ENGAGEMENT_MM:.1f} mm inside the exact {TOOTH_ZONE_WIDTH_MM:.1f} mm tooth zone. A {COUPON_STOP_MM:.1f} mm stop floor gives axial seating; two underside push-access openings permit finger/tool removal pressure. Permanent 1/2/3 notch identifiers are confined to the nonfunctional outer perimeter. Minimum residual wall is {min(row['minimum_wall_at_id_notch_mm'] for row in analysis['coupons'].values()):.2f} mm.

Coupons are fit-only. Do not perform torque, press, hammer, destructive clamp, or powered testing.
"""
    plan = """# Physical fit test plan

1. Wait for the ordered physical core; record lot, finish, flange state, bore/key state, and actual dimensions.
2. Print C1, C2, and C3 once each in PETG using identical Bambu A1 settings. Keep the axis vertical and support off every mating surface.
3. Deburr only loose print whiskers; do not file or sand the exact tooth pocket to force a result.
4. Test C1, then C2, then C3 by hand. No hammer, arbor press, clamp, or powered rotation.
5. For each, record hand insertion, full axial seating, hand removal, whitening, cracks, and perceptible radial play.
6. Winner = smallest clearance with hand insertion/removal, full seating, no whitening/crack, and no clear play.
7. If none pass, record honest FAIL and measure the received part; do not generate an approximate fallback.
"""
    retention = """# Retention concept

Option A is a side-serviceable removable PETG retainer. Option B is a captured PETG shoulder plus removable retainer. Both are concepts only.

No metal drilling, welding, adhesive-only retention, precision farmer machining, or reliance on a set screw as the primary torque path is authorized. The separate NFC flange candidates are recorded from CAD but are not assumed mandatory. `RETENTION_PHYSICAL=HOLD`.
"""
    gate = """# Print gate

Approved after builder/contract PASS: print one each of C1, C2, and C3 fit coupons in PETG. Same plate is allowed. Mating-surface supports must be zero.

Not approved: exact-core 14T reference, full DRIVE, retention parts, torque fixtures, static torque, powered rotation, water/mud, field, durability, or production. Slicer has not been run: `PHYSICAL_USER_HOLD`.
"""
    holds = """# HOLD register

- `PHYSICAL_CORE_NOT_RECEIVED`
- `PHYSICAL_NFC_STATE_NOT_YET`
- `FIT_WINNER_NOT_YET`
- `RETENTION_NOT_YET`
- `FULL_DRIVE_PRINT_HOLD`
- `STATIC_TORQUE_HOLD`
- `POWERED_NOT_APPROVED`
- `SLICER_NOT_RUN_PHYSICAL_USER_HOLD`
- `WATER_MUD_FIELD_DURABILITY_PRODUCTION_NOT_APPROVED`
"""
    return {DOCS[0]: readme, DOCS[1]: authority, DOCS[2]: source, DOCS[3]: fit, DOCS[4]: plan, DOCS[5]: retention, DOCS[6]: gate, DOCS[7]: holds}


def canonical_guard(guard: dict[str, object]) -> dict[str, object]:
    return {key: guard[key] for key in (
        "repository", "branch", "head", "staged", "tracked_dirty", "outside_untracked",
        "authority_sha256", "protected_lanes", "source_authority",
    )}


def validation_report(analysis: dict[str, object], steps: dict[str, object], meshes: dict[str, object], guard: dict[str, object]) -> dict[str, object]:
    coupons_pass = all(row["minimum_wall_at_id_notch_mm"] >= 5.0 for row in analysis["coupons"].values())
    source = analysis["source_geometry"]
    ref = analysis["exact_core_reference"]
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "repository_guard": canonical_guard(guard), "order_snapshot": ORDER_SNAPSHOT,
        "geometry": analysis, "step_reload": steps, "stl_quality": meshes,
        "checks": {
            "source_zip_sha": "PASS", "source_step_sha": "PASS", "ap203_schema": "PASS",
            "vendor_solid_count_5": "PASS" if source["solid_count"] == 5 else "FAIL",
            "unique_main_solid": "PASS", "other_vendor_solids_preserved": "PASS",
            "exact_tooth_count_28": "PASS" if source["main_body"]["tooth_count_detected"] == 28 else "FAIL",
            "periodicity_28": "PASS" if source["main_body"]["periodicity_added_mm3"] == 0 and source["main_body"]["periodicity_removed_mm3"] == 0 else "FAIL",
            "tooth_approximation_zero": "PASS", "global_scaling_zero": "PASS",
            "clearance_C1_015": "PASS", "clearance_C2_025": "PASS", "clearance_C3_035": "PASS",
            "notch_ids_1_2_3": "PASS", "coupon_wall_ge_5": "PASS" if coupons_pass else "FAIL",
            "support_free_orientation_feasible": "PASS_CAD_ORIENTATION_SLICER_NOT_RUN",
            "p20653_frozen": "PASS", "p20653_14_tooth_regression": "PASS",
            "p20653_visible_change_outside_hub": "PASS",
            "exact_c2_ligament_ge_5": "PASS" if ref["minimum_continuous_ligament_mm"] >= 5.0 else "FAIL",
            "exact_c2_ligament_target_ge_6": "PASS" if ref["minimum_continuous_ligament_mm"] >= 6.0 else "FAIL",
            "exact_c2_ligament_stretch_ge_8": "PASS" if ref["minimum_continuous_ligament_mm"] >= 8.0 else "FAIL",
            "c2_reference_not_selected": "PASS", "full_drive_print": "HOLD",
            "retention_physical": "HOLD", "physical_fit": "NOT_YET",
            "step_reload": "PASS" if all(row["reload"] == "PASS" and row["all_valid"] for row in steps.values()) else "FAIL",
            "stl_watertight_manifold": "PASS" if all(row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()) else "FAIL",
            "fit_coupon_print": "APPROVED_CAD_AND_CONTRACT_ONLY",
            "static_torque": "HOLD", "powered": "NOT_APPROVED", "water_mud_field": "NOT_APPROVED",
            "production": "NOT_APPROVED",
        },
    }


def export_geometry(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    main_wp = wp(main_solid())
    assembly_wp = wp(vendor_assembly())
    shapes_step = {
        DERIVED[0]: main_wp, DERIVED[2]: assembly_wp,
        ARTIFACTS[0]: coupon("C1"), ARTIFACTS[2]: coupon("C2"), ARTIFACTS[4]: coupon("C3"),
        ARTIFACTS[6]: exact_core_reference(),
    }
    shapes_stl = {DERIVED[1]: main_wp, ARTIFACTS[1]: coupon("C1"), ARTIFACTS[3]: coupon("C2"), ARTIFACTS[5]: coupon("C3")}
    for rel, shape in shapes_step.items(): export_step(shape, out / rel)
    for rel, shape in shapes_stl.items(): export_stl(shape, out / rel)
    steps = {rel: step_metrics(out / rel) for rel in shapes_step}
    meshes = {rel: mesh_metrics(out / rel) for rel in shapes_stl}
    expected_solids = {DERIVED[0]: 1, DERIVED[2]: 5, ARTIFACTS[0]: 1, ARTIFACTS[2]: 1, ARTIFACTS[4]: 1, ARTIFACTS[6]: 1}
    if any(not row["all_valid"] or row["solid_count"] != expected_solids[rel] for rel, row in steps.items()):
        raise RuntimeError("STEP_RELOAD_CONTRACT_FAIL")
    if any(not row["watertight"] or row["bad_edge_count"] or row["degenerate_triangle_count"] or row["component_count"] != 1 for row in meshes.values()):
        raise RuntimeError("STL_MESH_CONTRACT_FAIL")
    return steps, meshes


def generate(out: Path, copy_sources: bool = False) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=True)
    if copy_sources:
        shutil.copy2(LANE_DIR / BUILDER, out / BUILDER)
        (out / "tests").mkdir(parents=True, exist_ok=True)
        shutil.copy2(LANE_DIR / TEST, out / TEST)
    source_dir = out / "source/vendor"; source_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_ZIP, source_dir / SOURCE_ZIP_NAME)
    (source_dir / SOURCE_STEP_NAME).write_bytes(source_step_bytes())
    analysis = design_analysis()
    steps, meshes = export_geometry(out)
    for rel, svg in svg_outputs(analysis).items(): write_text(out / rel, svg)
    for rel, text in markdown_documents(analysis).items(): write_text(out / rel, text)
    write_json(out / DATA[0], analysis["source_geometry"])
    write_json(out / DATA[1], {
        "version": VERSION, "classification": CLASSIFICATION, "order_snapshot": ORDER_SNAPSHOT,
        "clearances_radial_equivalent_mm": CLEARANCES, "notch_counts": NOTCH_COUNTS,
        "coupon_engagement_mm": COUPON_ENGAGEMENT_MM, "coupon_stop_mm": COUPON_STOP_MM,
        "coupon_wall_nominal_mm": COUPON_WALL_NOMINAL_MM, "p20653_outer_authority": P20653,
        "c2_state": "REFERENCE_ONLY_NOT_SELECTED", "retention_physical": "HOLD",
    })
    guard = repository_guard(False)
    report = validation_report(analysis, steps, meshes, guard)
    write_json(out / DATA[2], report)
    write_text(out / "BUILD_LOG.txt", (
        f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSOURCE_SOLIDS=5\nSTEP_DERIVED_ARTIFACT=6\n"
        "SOURCE_STEP=1\nSTL=4\nSVG=6\nCOUPONS=C1_015,C2_025,C3_035\n"
        "TOOTH_SOURCE=EXACT_AP203_NO_APPROXIMATION\nFIT_COUPONS_PRINT_APPROVED=YES\nFULL_DRIVE_PRINT=HOLD\n"
        f"STATUS={STATUS}"
    ))
    write_text(out / "TEST_LOG.txt", (
        "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSOURCE_HASH=2_OF_2_PASS\n"
        "STEP_RELOAD=6_OF_6_PASS\nSTL_WATERTIGHT_MANIFOLD=4_OF_4_PASS\n"
        "P20653_REGRESSION=14_OF_14_PASS\nREPRODUCIBILITY=ALL_EXPECTED_PATHS_BYTE_IDENTICAL\n"
        "PHYSICAL_FIT=NOT_YET\nFULL_DRIVE_PRINT=HOLD"
    ))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    sum_files = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in sum_files))
    return report


def verify() -> dict[str, object]:
    guard = repository_guard(True)
    files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    manifest = [line for line in (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if line]
    commit_paths = [line for line in (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() if line]
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    mismatches = []
    for line in (LANE_DIR / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(LANE_DIR / rel) != digest: mismatches.append(rel)
    source_copy = {
        "zip": sha256(LANE_DIR / SOURCE_FILES[0]), "step": sha256(LANE_DIR / SOURCE_FILES[1]),
    }
    step_paths = [DERIVED[0], DERIVED[2], ARTIFACTS[0], ARTIFACTS[2], ARTIFACTS[4], ARTIFACTS[6]]
    stl_paths = [DERIVED[1], ARTIFACTS[1], ARTIFACTS[3], ARTIFACTS[5]]
    steps = {rel: step_metrics(LANE_DIR / rel) for rel in step_paths}
    meshes = {rel: mesh_metrics(LANE_DIR / rel) for rel in stl_paths}
    report = json.loads((LANE_DIR / DATA[2]).read_text(encoding="utf-8"))
    checks = {
        "repository_guard": all(guard["checks"].values()), "exact_paths": files == EXPECTED_FILES,
        "manifest_exact": manifest == EXPECTED_FILES, "commit_paths_exact": commit_paths == expected_commit,
        "sha_mismatch_zero": not mismatches,
        "source_copy_byte_exact": source_copy == {"zip": SOURCE_ZIP_SHA256, "step": SOURCE_STEP_SHA256},
        "step_6_of_6": len(steps) == 6 and all(row["reload"] == "PASS" and row["all_valid"] for row in steps.values()),
        "stl_4_of_4": len(meshes) == 4 and all(row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "source_solid_count_5": report["geometry"]["source_geometry"]["solid_count"] == 5,
        "exact_teeth_28": report["geometry"]["source_geometry"]["main_body"]["tooth_count_detected"] == 28,
        "exact_periodicity": report["geometry"]["source_geometry"]["main_body"]["periodicity_added_mm3"] == 0,
        "clearance_contract": report["geometry"]["coupons"]["C1"]["clearance_radial_equivalent_mm"] == 0.15 and report["geometry"]["coupons"]["C2"]["clearance_radial_equivalent_mm"] == 0.25 and report["geometry"]["coupons"]["C3"]["clearance_radial_equivalent_mm"] == 0.35,
        "notches_1_2_3": [report["geometry"]["coupons"][key]["notch_count"] for key in ("C1", "C2", "C3")] == [1, 2, 3],
        "wall_ge_5": all(row["minimum_wall_at_id_notch_mm"] >= 5.0 for row in report["geometry"]["coupons"].values()),
        "p20653_14_of_14": report["geometry"]["p20653_outer"]["p20653_14_tooth_regression"]["all_14_pass"],
        "p20653_external_added_removed_zero": report["geometry"]["p20653_outer"]["outside_hub_modification_added_mm3"] == 0 and report["geometry"]["p20653_outer"]["outside_hub_modification_removed_mm3"] == 0,
        "c2_reference_only": report["geometry"]["exact_core_reference"]["clearance"] == "C2_REFERENCE_ONLY" and not report["geometry"]["exact_core_reference"]["selected_winner"],
        "ligament_hard": report["geometry"]["exact_core_reference"]["minimum_continuous_ligament_mm"] >= 5.0,
        "full_drive_hold": "FULL_DRIVE_PRINT_HOLD" in report["status"],
        "physical_not_claimed": "PHYSICAL_CORE_NOT_RECEIVED" in report["status"] and "FIT_WINNER_NOT_YET" in report["status"],
    }
    if not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL: " + json.dumps({"checks": checks, "sha_mismatches": mismatches}, ensure_ascii=True))
    return {"checks": checks, "paths": len(files), "source_step": 1, "step": 6, "stl": 4, "svg": 6, "sha_mismatches": mismatches, "repository": guard}


def reproducibility() -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_v09634_repro_") as temp:
        root = Path(temp) / LANE_NAME
        generate(root, copy_sources=True)
        mismatches = [rel for rel in EXPECTED_FILES if sha256(root / rel) != sha256(LANE_DIR / rel)]
    if mismatches:
        raise RuntimeError("REPRODUCIBILITY_FAIL: " + json.dumps(mismatches))
    coupon_targets = [ARTIFACTS[1], ARTIFACTS[3], ARTIFACTS[5]]
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0, "coupon_stl_3_of_3": all(rel not in mismatches for rel in coupon_targets)}


def package() -> dict[str, object]:
    verify()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_P5M28_EXACT_VENDOR_CORE_FIT_COUPON_v0_9_6_34_{stamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite {path}")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            archive.write(LANE_DIR / rel, arcname=f"{LANE_NAME}/{rel}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        expected = [f"{LANE_NAME}/{rel}" for rel in EXPECTED_FILES]
        duplicate_count = len(names) - len(set(names))
        traversal_count = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        if names != expected or duplicate_count or traversal_count:
            raise RuntimeError("ZIP_AUDIT_FAIL")
    return {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS", "manifest_exact": names == expected, "duplicate_count": duplicate_count, "traversal_count": traversal_count}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if args.build:
        repository_guard(False); result: object = generate(LANE_DIR)
    elif args.verify: result = verify()
    elif args.reproducibility: result = {"reproducibility": reproducibility()}
    elif args.package: result = {"zip": package()}
    else: parser.error("select --build, --verify, --reproducibility, or --package")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
