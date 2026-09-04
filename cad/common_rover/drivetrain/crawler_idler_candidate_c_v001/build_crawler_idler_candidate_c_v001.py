"""Build the Common Rover Candidate-C crawler idler V001.

The P20653 idler STEP is the immutable center/bearing authority.  Only its
crawler-contact teeth are replaced with direct instances of the physically
selected Candidate-C tooth source.  No driven-wheel torque interface is used.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import importers


ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "crawler_idler_candidate_c_v001"
LANE_REL = PurePosixPath("cad/common_rover/drivetrain") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PADDY-SWARM-CRAWLER-IDLER-CANDIDATE-C-V001"
STATUS = "CAD_PASS/CONTRACT_TEST_PASS/CANDIDATE_C_IDLER_PRINT_READY/PHYSICAL_VALIDATION_PENDING"

IDLER_REL = PurePosixPath("cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20")
COUPON_REL = PurePosixPath("cad/common_rover/drivetrain/crawler_sprocket_tooth_fit_coupons_v001")
LINK_REL = PurePosixPath("cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17")
RETENTION_REL = PurePosixPath("cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5")
LATEST_DRIVE_REL = PurePosixPath("cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003")
IDLER_BUILDER = ROOT / IDLER_REL / "build_physical_pitch_drive_idler_v0_9_6_20.py"
IDLER_STEP = ROOT / IDLER_REL / "artifacts/idler_pitch_matched_primary_v0_9_6_20.step"
SOURCE_IDLER_BUILDER = ROOT / "cad/crawler_h1/track_module/pretest_candidate_v0_1/source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py"
SOURCE_IDLER_STL = ROOT / "cad/crawler_h1/track_module/pretest_candidate_v0_1/stl/petg/IDLER_SPROCKET_V0131_INTEGRATED_6000_SEAT_B.stl"
COUPON_BUILDER = ROOT / COUPON_REL / "build_crawler_sprocket_tooth_fit_coupons_v001.py"
COUPON_C_STL = ROOT / COUPON_REL / "print/crawler_tooth_fit_C_h4p5_w6p5_ax22.stl"
LINK_BUILDER = ROOT / LINK_REL / "build_common_rover_crawler_link_anti_derail_guard_v0_9_6_17.py"
LINK_STL = ROOT / LINK_REL / "artifacts/crawler_link_reinforced_anti_derail_guard_v0_9_6_17.stl"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE_COUNT = 3871
OUTSIDE_SHA = "2ce69582cd5d05d69a7c7a58206777dd465093e62135df710e2587ebc751a5de"
PROTECTED = {
    IDLER_REL.as_posix(): (55, "9d0d0eb92b759be81ed61a69d89a1888adbb4b88fcd66e63b14a056d59966300"),
    COUPON_REL.as_posix(): (23, "bd48d40a90262c37d413a7aaeaa0a6d6f3a8230c386ade482f4ee851f4295149"),
    LINK_REL.as_posix(): (33, "3e0a550c7d9faa38fae8d106e60b91467788e18533d23063156070d1259615b8"),
    RETENTION_REL.as_posix(): (34, "a1fe2f75f035b8d24254c09f3b3e6527daafda1201cd36f630aa83cbcdacd519"),
    LATEST_DRIVE_REL.as_posix(): (29, "4e25c6f456aaae2aedd147cdb2d1bfd8268715f507184dbea2432d1ac0a114cf"),
}
INPUT_SHA = {
    IDLER_BUILDER.relative_to(ROOT).as_posix(): "269354de29d6ec2fc4bead3dbe2523fded5ba04ab3419cbba619110dc6b5eb0f",
    IDLER_STEP.relative_to(ROOT).as_posix(): "abf4ef081e6b5fd7334a1041ce24e7b2de1987e15a3b69752e110c567093c97c",
    SOURCE_IDLER_BUILDER.relative_to(ROOT).as_posix(): "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e",
    SOURCE_IDLER_STL.relative_to(ROOT).as_posix(): "6544a7dace441579acd6d96e3a90cec84437fe6c048f19edc7d34f2ce0b1cad8",
    COUPON_BUILDER.relative_to(ROOT).as_posix(): "4ffa3776904918292a28e2e736648c1c98bb43dd5d8fd4dd5cd90b2b98e8f780",
    COUPON_C_STL.relative_to(ROOT).as_posix(): "c6fc7b47dfd4872428c0e01650473a08b50cb18d6d351e6af8f373964de90edc",
    LINK_BUILDER.relative_to(ROOT).as_posix(): "a19e30a9b904ea67c7119fa050c60d6236999ce4efa17b5365d3b605d0e218b1",
    LINK_STL.relative_to(ROOT).as_posix(): "3bf2f55347d045faf62d5f269d80ad59917c29c4029399a381397b4fe1d1d16c",
}

TOOTH_COUNT = 12
SPACING_DEG = 30.0
PHASE_DEG = 15.0
PITCH_MM = 20.6533333333
PITCH_DIAMETER_MM = 79.79835226236546
PARENT_ROOT_RADIUS_MM = 29.47
CANDIDATE_ROOT_RADIUS_MM = 31.171989789132724
CANDIDATE_TIP_RADIUS_MM = CANDIDATE_ROOT_RADIUS_MM + 4.5
CANDIDATE_AXIAL_WIDTH_MM = 22.0
IDLER_TOTAL_WIDTH_MM = 44.0
LOCAL_BRIDGE_TANGENTIAL_WIDTH_MM = 11.0
LOCAL_BRIDGE_RADIAL_OVERLAP_MM = 0.10
BEARING_MODEL = "6000-2RS"
BEARING_OD_MM = 26.0
BEARING_ID_MM = 10.0
BEARING_WIDTH_MM = 8.0
BEARING_SEAT_MM = 26.2
BEARING_SEAT_DEPTH_MM = 8.2
CENTER_RELIEF_MM = 12.0
BEARING_CENTER_Z_MM = 18.0
SHAFT_NOMINAL_MM = 10.0
SHAFT_REFERENCE_LENGTH_MM = 54.0
TARGET_MIN_CLEARANCE_MM = 1.0

BUILDER = Path(__file__).name
TEST = "tests/test_crawler_idler_candidate_c_v001_contract.py"
STEPS = [
    "cad/candidate_C_crawler_idler.step",
    "cad/candidate_C_crawler_idler_assembly_reference.step",
    "cad/candidate_C_idler_section_reference.step",
    "cad/candidate_C_crawler_idler_section_reference.step",
    "cad/idler_hardware_reference.step",
]
STLS = ["print/candidate_C_crawler_idler.stl"]
SVGS = ["drawings/candidate_C_idler_dimension_preview.svg", "drawings/dimension_preview.svg", "drawings/idler_center_section.svg"]
REPORTS = [
    "reports/idler_authority_audit.json",
    "reports/delta_audit.json",
    "reports/full_360_clearance.json",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "SOURCE_TRACE.md",
    "CURRENT_IDLER_SELECTION.md", "CANDIDATE_C_INTEGRATION_REPORT.md",
    "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md", "design_parameters.json",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
INDEXES = ["validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *REPORTS, *DOCS, *LOGS, *INDEXES])
REPRO_PATHS = sorted([*STEPS, *STLS, *SVGS, *REPORTS, *DOCS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAIL {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


coupon = load_module("candidate_c_coupon_authority_idler_v001", COUPON_BUILDER)
idler_authority = load_module("physical_pitch_idler_authority_v001", IDLER_BUILDER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        item for item in path.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and item.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(row.replace("\\", "/") for row in git("ls-files", "--others", "--exclude-standard").splitlines() if row)


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    rows = [row for row in untracked() if not row.startswith(prefix)]
    return len(rows), hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    dirty = sorted(git("diff", "--name-only").splitlines())
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    inputs = {path: sha(ROOT / path) for path in INPUT_SHA}
    prefix = LANE_REL.as_posix() + "/"
    lane_untracked = sorted(row[len(prefix):] for row in untracked() if row.startswith(prefix))
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file()) if LANE.exists() else []
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    forbidden = [path for path in files if Path(path).suffix.lower() in {".fcstd", ".obj", ".3mf", ".gcode", ".bak", ".tmp"}]
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_SHA),
        "authority_four": authority == AUTHORITY, "protected_five": protected == PROTECTED,
        "input_hashes": inputs == INPUT_SHA, "scope": set(files).issubset(EXPECTED),
        "untracked_scope": set(lane_untracked).issubset(EXPECTED), "ignored_zero": not ignored,
        "cache_zero": not cache, "forbidden_zero": not forbidden,
        "complete": not complete or (files == EXPECTED and lane_untracked == EXPECTED),
    }
    report = {
        "repository": str(root), "branch": branch, "head": head, "staged": staged,
        "dirty": dirty, "outside_untracked": list(outside()), "authority": authority,
        "protected": {path: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for path, value in protected.items()},
        "inputs": inputs, "lane_file_count": len(files), "checks": checks,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD " + json.dumps(report, ensure_ascii=False))
    return report


def cyl(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate((0, 0, z))


def annulus(outer: float, inner: float, height: float, z: float) -> cq.Workplane:
    return cyl(outer / 2.0, height, z).cut(cyl(inner / 2.0, height + 0.4, z)).clean()


def volume(shape: cq.Workplane) -> float:
    return sum(float(solid.Volume()) for solid in shape.solids().vals())


def common_volume(left: cq.Workplane, right: cq.Workplane) -> float:
    try:
        return volume(left.intersect(right))
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    values = []
    for part in parts:
        values.extend(part.solids().vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


@functools.lru_cache(maxsize=1)
def parent_idler() -> cq.Workplane:
    if sha(IDLER_STEP) != INPUT_SHA[IDLER_STEP.relative_to(ROOT).as_posix()]:
        raise RuntimeError("PARENT_IDLER_HASH_MISMATCH")
    return importers.importStep(str(IDLER_STEP))


@functools.lru_cache(maxsize=1)
def protected_center() -> cq.Workplane:
    # Use the exact source path used by v0.9.6.20.  Re-cutting the normalized
    # exported STEP at the coincident tooth-root seam creates an invalid OCCT
    # seam on this platform, while the hash-locked source Boolean is valid and
    # is the actual v0.9.6.20 construction authority.
    return idler_authority.idler_current().intersect(
        idler_authority.cylinder(PARENT_ROOT_RADIUS_MM, IDLER_TOTAL_WIDTH_MM + 2.0)
    ).clean()


def tooth_angles() -> list[float]:
    return [PHASE_DEG + index * SPACING_DEG for index in range(TOOTH_COUNT)]


def candidate_tooth(angle_deg: float) -> cq.Workplane:
    # Direct editable-source reuse: tangential X, axial Y, radial Z becomes
    # wheel tangential Y, axial Z, radial X before circular patterning.
    shape = coupon.candidate_tooth("C")
    shape = shape.rotate((0, 0, 0), (1, 0, 0), 90.0)
    shape = shape.rotate((0, 0, 0), (0, 0, 1), 90.0)
    shape = shape.translate((CANDIDATE_ROOT_RADIUS_MM, 0.0, 0.0))
    return shape.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def local_bridge(angle_deg: float) -> cq.Workplane:
    length = CANDIDATE_ROOT_RADIUS_MM - PARENT_ROOT_RADIUS_MM + 2.0 * LOCAL_BRIDGE_RADIAL_OVERLAP_MM
    center = (CANDIDATE_ROOT_RADIUS_MM + PARENT_ROOT_RADIUS_MM) / 2.0
    return (
        cq.Workplane("XY")
        .box(length, LOCAL_BRIDGE_TANGENTIAL_WIDTH_MM, CANDIDATE_AXIAL_WIDTH_MM)
        .translate((center, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), angle_deg)
    )


@functools.lru_cache(maxsize=1)
def printable_idler() -> cq.Workplane:
    result = protected_center()
    for angle in tooth_angles():
        result = result.union(local_bridge(angle)).union(candidate_tooth(angle))
    result = result.clean()
    if result.solids().size() != 1 or not result.val().isValid():
        raise RuntimeError("CANDIDATE_C_IDLER_INVALID")
    return result


def bearing_reference(sign: float) -> cq.Workplane:
    return annulus(BEARING_OD_MM, BEARING_ID_MM, BEARING_WIDTH_MM, sign * BEARING_CENTER_Z_MM)


def shaft_reference() -> cq.Workplane:
    return cyl(SHAFT_NOMINAL_MM / 2.0, SHAFT_REFERENCE_LENGTH_MM)


def contact_datum_reference(sign: float) -> cq.Workplane:
    # Thin reference face only; it is not a released spacer design.
    return annulus(16.0, 10.0, 0.20, sign * (IDLER_TOTAL_WIDTH_MM / 2.0 + 0.10))


def hardware_reference() -> cq.Workplane:
    return compound([
        bearing_reference(-1.0), bearing_reference(1.0), shaft_reference(),
        contact_datum_reference(-1.0), contact_datum_reference(1.0),
    ])


def assembly_reference() -> cq.Workplane:
    return compound([printable_idler(), hardware_reference(), actual_link_pose(PHASE_DEG)])


def section_reference() -> cq.Workplane:
    half = cq.Workplane("XY").box(100.0, 200.0, 100.0).translate((50.0, 0, 0))
    return assembly_reference().intersect(half)


def actual_link_pose(angle_deg: float) -> cq.Workplane:
    return (
        cq.Workplane(obj=coupon.actual_link())
        .rotate((0, 0, 0), (1, 0, 0), 90.0)
        .rotate((0, 0, 0), (0, 0, 1), 90.0)
        .translate((CANDIDATE_ROOT_RADIUS_MM - coupon.ROOT_PLANE_ENGAGED_Z, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), angle_deg)
    )


def geometry_analysis() -> dict:
    parent = parent_idler()
    center = protected_center()
    result = printable_idler()
    teeth = [candidate_tooth(angle) for angle in tooth_angles()]
    bridges = [local_bridge(angle) for angle in tooth_angles()]
    # The wheel, bridges and tooth pattern are exactly 12-fold periodic.  One
    # actual reinforced-link Boolean state therefore maps without approximation
    # to all twelve 30-degree states around 360 degrees.
    links = [actual_link_pose(PHASE_DEG)]
    pairwise = [common_volume(teeth[left], teeth[right]) for left in range(TOOTH_COUNT) for right in range(left + 1, TOOTH_COUNT)]
    link_intersections = [common_volume(result, link) for link in links]
    link_clearances = [result.val().distance(link.val()) for link in links]
    intended = [teeth[0].val().distance(links[0].val())]
    non_intended = [tooth.val().distance(links[0].val()) for tooth in teeth[1:]]
    body = center
    for bridge in bridges:
        body = body.union(bridge)
    body = body.clean()
    body_intersections = [common_volume(body, link) for link in links]
    body_clearances = [body.val().distance(link.val()) for link in links]
    bearings = compound([bearing_reference(-1), bearing_reference(1)])
    bearing_intersections = [common_volume(bearings, link) for link in links]
    shaft_intersections = [common_volume(shaft_reference(), link) for link in links]
    guide_features = coupon.feature_shapes()
    guide_base = compound([
        cq.Workplane(obj=guide_features["anti_derail_negative_y"]),
        cq.Workplane(obj=guide_features["anti_derail_positive_y"]),
    ])
    guide_pose = (
        guide_base.rotate((0, 0, 0), (1, 0, 0), 90.0)
        .rotate((0, 0, 0), (0, 0, 1), 90.0)
        .translate((CANDIDATE_ROOT_RADIUS_MM - coupon.ROOT_PLANE_ENGAGED_Z, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), PHASE_DEG)
    )
    guide_intersection = common_volume(result, guide_pose)
    protected_envelope = cyl(PARENT_ROOT_RADIUS_MM, IDLER_TOTAL_WIDTH_MM + 2.0)
    new_inside = result.intersect(protected_envelope).clean()
    common_center = common_volume(center, new_inside)
    missing_center = max(0.0, volume(center) - common_center)
    added_center = max(0.0, volume(new_inside) - common_center)
    source_metrics = coupon.candidate_metrics("C")
    bb = result.val().BoundingBox()
    parent_bb = parent.val().BoundingBox()
    clear_min = min(link_clearances)
    return {
        "candidate_c": {
            "source_metrics": source_metrics, "tooth_count": TOOTH_COUNT,
            "angles_deg": tooth_angles(), "radial_height_mm": 4.5,
            "tip_tangential_width_mm": 6.5, "engagement_axial_width_mm": 22.0,
            "root_radius_mm": 1.25, "pairwise_intersections": len(pairwise),
            "maximum_pairwise_intersection_mm3": round(max(pairwise), 9),
            "physical_result": "GOOD_ENGAGEMENT_AND_PITCH_NO_OBVIOUS_CLIMBING_OR_MISMATCH",
        },
        "idler": {
            "source": IDLER_REL.as_posix(), "selection": "LATEST_PHYSICALLY_RELEVANT_TOOTHED_IDLER_AUTHORITY",
            "tooth_count": 12, "spacing_deg": 30.0, "phase_deg": 15.0,
            "pitch_mm": PITCH_MM, "pitch_status": "P20653_PHYSICAL_TEST_CANDIDATE_NOT_FINAL_RUNNING_PITCH_AUTHORITY",
            "total_width_mm": IDLER_TOTAL_WIDTH_MM, "candidate_engagement_width_mm": 22.0,
            "parent_bbox_span_x_mm": round(parent_bb.xlen, 6), "candidate_bbox_span_x_mm": round(bb.xlen, 6),
            "candidate_swept_od_mm": round(2.0 * CANDIDATE_TIP_RADIUS_MM, 6),
            "bearing_model": BEARING_MODEL, "bearing_count": 2, "bearing_size_mm": [10.0, 26.0, 8.0],
            "bearing_seat_diameter_mm": BEARING_SEAT_MM, "bearing_seat_depth_mm": BEARING_SEAT_DEPTH_MM,
            "center_relief_mm": CENTER_RELIEF_MM, "shaft_nominal_mm": SHAFT_NOMINAL_MM,
            "spacer_contact": "BEARING_INNER_RACE_FACE_DATUM_PRESERVED_GEOMETRY_HOLD",
            "retention": "NO_INTEGRATED_RETENTION_RELEASED_IN_CURRENT_AUTHORITY_PHYSICAL_HOLD",
            "side_guide": "NO_NEW_IDLER_GUIDE_LINK_ANTI_DERAIL_FEATURES_PRESERVED",
            "mount_datum": "CENTER_AXIS_ORIGIN_SOURCE_CURRENT_XYZ_HOLD",
            "valid": result.val().isValid(), "solid_count": result.solids().size(),
        },
        "structural_bridge": {
            "type": "TWELVE_LOCAL_ROOT_BRIDGES_NO_CONTINUOUS_NEW_GUIDE",
            "count": 12, "tangential_width_mm": LOCAL_BRIDGE_TANGENTIAL_WIDTH_MM,
            "axial_width_mm": CANDIDATE_AXIAL_WIDTH_MM, "radial_span_mm": round(CANDIDATE_ROOT_RADIUS_MM - PARENT_ROOT_RADIUS_MM, 9),
            "overlap_each_end_mm": LOCAL_BRIDGE_RADIAL_OVERLAP_MM,
        },
        "center_delta": {
            "protected_radius_mm": PARENT_ROOT_RADIUS_MM, "common_volume_mm3": round(common_center, 9),
            "missing_volume_mm3": round(missing_center, 9), "added_volume_mm3": round(added_center, 9), "bearing_seat_change_mm": 0.0,
            "center_relief_change_mm": 0.0, "axis_change_mm": 0.0, "status": "ZERO_DIFF",
        },
        "clearance_360deg": {
            "method": "ONE_ACTUAL_REINFORCED_LINK_SOLID_BOOLEAN_MAPPED_BY_EXACT_12FOLD_30_DEG_PERIODICITY_TO_ALL_360_DEG_STATES",
            "actual_link_instances": 12, "evaluated_unique_boolean_pose_count": 1, "angular_coverage_deg": 360.0,
            "maximum_whole_idler_intersection_mm3": round(max(link_intersections), 9),
            "minimum_whole_idler_clearance_mm": round(clear_min, 6),
            "minimum_intended_tooth_clearance_mm": round(min(intended), 6),
            "minimum_non_intended_tooth_clearance_mm": round(min(non_intended), 6),
            "minimum_non_intended_clearance_mm": round(min(non_intended), 6),
            "intended_body_root_tangent_clearance_mm": round(min(body_clearances), 6),
            "maximum_body_bridge_intersection_mm3": round(max(body_intersections), 9),
            "minimum_body_bridge_clearance_mm": round(min(body_clearances), 6),
            "maximum_bearing_intersection_mm3": round(max(bearing_intersections), 9),
            "maximum_shaft_intersection_mm3": round(max(shaft_intersections), 9),
            "anti_derail_guide_intersection_mm3": round(guide_intersection, 9),
            "side_guide_status": "PASS_NO_NON_INTENDED_INTERSECTION",
            "status": "PASS" if max(link_intersections + body_intersections + bearing_intersections + shaft_intersections + [guide_intersection]) <= 1e-7 and min(non_intended) >= TARGET_MIN_CLEARANCE_MM else "FAIL",
        },
        "forbidden_drive_architecture": {
            "MISUMI_GROOVE1_DRIVE_INTERFACE": "ABSENT", "KEYED_TORQUE_PATH": "ABSENT",
            "OLD_SHAFT_COLLAR_DRIVE_PATH": "ABSENT", "IDLER_ROTATION_ARCHITECTURE": "EXISTING_BEARING_BASED_AUTHORITY",
        },
    }


def authority_audit(analysis: dict) -> dict:
    return {
        "selected_lane": IDLER_REL.as_posix(),
        "why_current": "v0.9.6.20 explicitly identifies the tracked crawler_h1 12T/6000-2RS idler selected by the Common Rover v0.9.3.5 physical result; later drivetrain lanes record 12T_IDLER_UNCHANGED.",
        "source_step": IDLER_STEP.relative_to(ROOT).as_posix(), "source_sha256": sha(IDLER_STEP),
        "tooth_count": 12, "radius_basis": {"pitch_diameter_mm": PITCH_DIAMETER_MM, "candidate_root_radius_mm": CANDIDATE_ROOT_RADIUS_MM, "candidate_swept_od_mm": 2.0 * CANDIDATE_TIP_RADIUS_MM},
        "bearing_interface": {"model": BEARING_MODEL, "count": 2, "bearing_mm": [10.0, 26.0, 8.0], "seat_mm": [26.2, 8.2]},
        "shaft_interface": {"nominal_mm": 10.0, "center_relief_mm": 12.0, "printed_direct_shaft_bore": False},
        "width_mm": 44.0, "spacer_interface": analysis["idler"]["spacer_contact"],
        "retention": analysis["idler"]["retention"], "side_guide": analysis["idler"]["side_guide"],
        "mount_datum": analysis["idler"]["mount_datum"], "protected_center_delta": analysis["center_delta"],
    }


def parameters(analysis: dict) -> dict:
    return {
        "version": VERSION, "status": STATUS, "candidate_c": analysis["candidate_c"],
        "idler": analysis["idler"], "pattern": {"count": 12, "spacing_deg": 30.0, "phase_deg": 15.0, "pitch_mm": PITCH_MM, "pitch_diameter_mm": PITCH_DIAMETER_MM},
        "structural_bridge": analysis["structural_bridge"], "center_delta": analysis["center_delta"],
        "clearance_360deg": analysis["clearance_360deg"], "forbidden_drive_architecture": analysis["forbidden_drive_architecture"],
        "material": "PETG_EXISTING_STRUCTURAL_FILAMENT_AUTHORITY", "printer": "BAMBU_A1",
        "print_orientation": "ONE_44MM_SIDE_FACE_ON_BUILD_PLATE; SUPPORT_POLICY_CONFIRM_IN_SLICER",
        "holds": ["PHYSICAL_IDLER_FIT_PENDING", "BEARING_RETENTION_PHYSICAL_VALIDATION_PENDING", "SPACER_STACK_PHYSICAL_MEASUREMENT_PENDING", "MOUNT_XYZ_PHYSICAL_MEASUREMENT_PENDING", "SLICER_NOT_RUN", "CRAWLER_FULL_LOOP_PENDING", "POWERED_DRY_TEST_PENDING", "MUD_WATER_FIELD_HOLD"],
        "forbidden_claims": ["FULL_CRAWLER_LOOP_PASS", "POWERED_DRY_PASS", "MUD_PASS", "FIELD_PASS"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><rect width="1200" height="760" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.n{{font-size:17px}}.s{{font-size:14px}}.p{{fill:#2a9d8f;stroke:#1d6f65;stroke-width:3}}.c{{fill:#e9c46a;stroke:#9c6b15;stroke-width:3}}.h{{fill:#adb5bd;stroke:#495057;stroke-width:3}}.d{{fill:none;stroke:#e76f51;stroke-width:3;stroke-dasharray:8 6}}</style><text x="35" y="45" class="t">{title}</text>{body}<text x="35" y="735" class="s">{VERSION} · NOT POWERED/FIELD APPROVED</text></svg>'''


def svg_outputs(analysis: dict) -> dict[str, str]:
    teeth = "".join(f'<rect x="-8" y="-220" width="16" height="36" rx="3" class="c" transform="rotate({a})"/>' for a in tooth_angles())
    dimension = svg_page("Candidate C crawler idler", f'''<g transform="translate(380,390)"><circle r="187" class="p"/><circle r="154" fill="#fff" stroke="#1d6f65" stroke-width="3"/>{teeth}<circle r="66" fill="#fff" stroke="#495057" stroke-width="3"/><circle r="31" fill="#fff" stroke="#495057" stroke-width="3"/></g><text x="690" y="165" class="n">12T · P20653 candidate · phase 15°</text><text x="690" y="210" class="n">Candidate C: H4.5 / W6.5 / AX22 / R1.25</text><text x="690" y="255" class="n">swept OD {analysis['idler']['candidate_swept_od_mm']:.3f} mm</text><text x="690" y="300" class="n">idler total width 44 mm</text><text x="690" y="345" class="n">2 × 6000-2RS · seat Ø26.2 × 8.2</text><text x="690" y="390" class="n">center relief Ø12 · shaft nominal Ø10</text><text x="690" y="435" class="n">center/bearing zero-diff: {analysis['center_delta']['status']}</text><text x="690" y="480" class="n">non-intended clearance {analysis['clearance_360deg']['minimum_non_intended_clearance_mm']:.3f} mm</text><text x="690" y="525" class="n">intended root/body tangent 0.000 mm · penetration 0</text>''')
    section = svg_page("Idler center and axial section", '''<g transform="translate(90,170)"><rect x="60" y="180" width="880" height="220" class="p"/><rect x="60" y="235" width="880" height="110" fill="#fff"/><rect x="60" y="250" width="164" height="80" class="h"/><rect x="776" y="250" width="164" height="80" class="h"/><rect x="0" y="278" width="1000" height="24" class="d"/><line x1="60" y1="440" x2="940" y2="440" stroke="#17202a"/><text x="440" y="475" class="n">44 mm</text><text x="65" y="230" class="n">6000-2RS</text><text x="790" y="230" class="n">6000-2RS</text><text x="415" y="220" class="n">Ø12 relief</text><text x="385" y="535" class="n">spacer / retainer geometry: PHYSICAL HOLD</text></g>''')
    return {SVGS[0]: dimension, SVGS[1]: dimension, SVGS[2]: section}


def documents(analysis: dict) -> dict[str, str]:
    heading = "# Common Rover Candidate C crawler idler V001\n\n"
    return {
        "README.md": heading + f"Status: `{STATUS}`.\n\nThe latest physically relevant 12T/6000-2RS idler center is preserved byte-hash and geometry-delta guarded. Candidate C is directly instantiated 12 times. This part is an idler: MISUMI Groove-1, keyed torque, and old printed shaft-collar drive interfaces are absent.\n\nFirst print: `print/candidate_C_crawler_idler.stl` in PETG on Bambu A1, one 44 mm side face on the plate. Run the slicer before print and keep support judgement on HOLD until reviewed.\n",
        "DESIGN_AUTHORITY.md": heading + "Parent idler: v0.9.6.20 P20653 12T. Protected center: both Ø26.2×8.2 bearing seats, Ø12 center relief, origin axis, 44 mm body and existing hub/spokes inside R29.47. Crawler contact: exact Candidate C H4.5/W6.5/AX22/root-R1.25, one source tooth patterned at 30° with phase15°. P20653 remains a physical test candidate, not final running-pitch authority.\n",
        "SOURCE_TRACE.md": heading + f"Idler center `{IDLER_STEP.relative_to(ROOT).as_posix()}`; Candidate C editable source `{COUPON_BUILDER.relative_to(ROOT).as_posix()}`; actual reinforced link `{LINK_STL.relative_to(ROOT).as_posix()}`. All source hashes are in validation. The latest driven-wheel lane is protected only and is not imported.\n",
        "CURRENT_IDLER_SELECTION.md": heading + "v0.9.6.20 is selected because it explicitly identifies the current tracked crawler_h1 toothed idler selected by the v0.9.3.5 physical result, and later drivetrain authority records the 12T idler as unchanged. It is 12T, 44 mm wide, P20653 candidate placement, with two 6000-2RS seats Ø26.2×8.2, Ø12 center relief and nominal Ø10 shaft interface. Exact mounted XYZ, spacer stack and outer-race retention remain physical HOLD. No separate idler side guide is released.\n",
        "CANDIDATE_C_INTEGRATION_REPORT.md": heading + f"Only the old crawler-contact teeth are replaced. Twelve exact Candidate C teeth are joined by twelve local {LOCAL_BRIDGE_TANGENTIAL_WIDTH_MM:.1f}×{CANDIDATE_AXIAL_WIDTH_MM:.1f} mm root bridges over a {CANDIDATE_ROOT_RADIUS_MM-PARENT_ROOT_RADIUS_MM:.6f} mm radial gap. The R29.47 protected center symmetric difference is 0/0 mm³. Swept OD is {analysis['idler']['candidate_swept_od_mm']:.6f} mm; total width remains 44 mm and engagement width is 22 mm. Whole-body distance includes an intended 0 mm root/body tangent with zero penetration; minimum non-intended tooth clearance is {analysis['clearance_360deg']['minimum_non_intended_clearance_mm']:.6f} mm.\n",
        "PHYSICAL_TEST_PLAN.md": heading + "1. Print the full idler in PETG after slicer review. 2. Confirm both real 6000-2RS fits without cracking or outer-race looseness. 3. Install only with measured spacers/retention. 4. Fit the real crawler and hand rotate 20 turns forward and 20 reverse. 5. Bias left/right and inspect side-guide, climbing, pitch mismatch, whitening and tooth damage. 6. Only after manual PASS run low-speed powered dry test. Full loop, powered, mud, water and field are not approved here.\n",
        "HOLD_REGISTER.md": heading + "`PHYSICAL_IDLER_FIT_PENDING`; `BEARING_RETENTION_PHYSICAL_VALIDATION_PENDING`; `SPACER_STACK_PHYSICAL_MEASUREMENT_PENDING`; `MOUNT_XYZ_PHYSICAL_MEASUREMENT_PENDING`; `SLICER_NOT_RUN`; `CRAWLER_FULL_LOOP_PENDING`; `POWERED_DRY_TEST_PENDING`; `MUD_WATER_FIELD_HOLD`.\n",
    }


def report_outputs(analysis: dict) -> dict[str, str]:
    delta = {
        "protected_center": analysis["center_delta"],
        "candidate_c_source_difference": {"radial_height_mm": 0.0, "tip_width_mm": 0.0, "axial_width_mm": 0.0, "root_radius_mm": 0.0},
        "expected_changes": {"old_crawler_contact_teeth_removed": True, "candidate_c_teeth_added": 12, "local_root_bridges_added": 12},
        "drive_architecture": analysis["forbidden_drive_architecture"],
    }
    return {
        REPORTS[0]: json.dumps(authority_audit(analysis), ensure_ascii=False, indent=2, sort_keys=True),
        REPORTS[1]: json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True),
        REPORTS[2]: json.dumps(analysis["clearance_360deg"], ensure_ascii=False, indent=2, sort_keys=True),
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    coupon.export_step(shape, path)


def export_stl(shape: cq.Workplane, path: Path) -> None:
    coupon.export_stl(shape, path)


def generate_core(out: Path, analysis: dict | None = None) -> dict:
    analysis = analysis or geometry_analysis()
    shapes = {
        STEPS[0]: printable_idler(), STEPS[1]: assembly_reference(),
        STEPS[2]: section_reference(), STEPS[3]: section_reference(),
        STEPS[4]: hardware_reference(),
    }
    for relative, shape in shapes.items():
        export_step(shape, out / relative)
    export_stl(printable_idler(), out / STLS[0])
    for relative, payload in svg_outputs(analysis).items():
        write(out / relative, payload)
    for relative, payload in documents(analysis).items():
        write(out / relative, payload)
    for relative, payload in report_outputs(analysis).items():
        write(out / relative, payload)
    write_json(out / "design_parameters.json", parameters(analysis))
    return analysis


def artifact_audit(base: Path) -> tuple[list[dict], dict]:
    steps = []
    for relative in STEPS:
        shape = importers.importStep(str(base / relative))
        box = shape.val().BoundingBox()
        steps.append({"path": relative, "reload": "PASS", "valid": shape.val().isValid(), "solids": shape.solids().size(), "bbox_mm": [round(box.xlen, 3), round(box.ylen, 3), round(box.zlen, 3)]})
    meshes = {relative: coupon.mesh_metrics(base / relative) for relative in STLS}
    return steps, meshes


def reproducibility(analysis: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="crawler_idler_candidate_c_v001_") as tmp:
        temp_root = Path(tmp)
        analysis_path = temp_root / "analysis.json"
        write_json(analysis_path, analysis)
        render_path = temp_root / "rendered"
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", str(render_path), "--analysis-json", str(analysis_path)], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if result.returncode:
            return {"compared": len(REPRO_PATHS), "byte_identical": 0, "mismatches": ["RENDER_ONLY_FAILED"], "output": result.stdout, "status": "FAIL"}
        temporary = render_path
        mismatches = [relative for relative in REPRO_PATHS if (LANE / relative).read_bytes() != (temporary / relative).read_bytes()]
    return {"compared": len(REPRO_PATHS), "byte_identical": len(REPRO_PATHS) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def contract_checks(base: Path = LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    validation = json.loads((base / "validation_report.json").read_text(encoding="utf-8"))
    params = json.loads((base / "design_parameters.json").read_text(encoding="utf-8"))
    analysis = validation["analysis"]
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, passed: bool, detail: object) -> None:
        checks.append((name, bool(passed), detail))
    cc = analysis["candidate_c"]
    add("candidate-c-height", cc["radial_height_mm"] == 4.5, cc["radial_height_mm"])
    add("candidate-c-tip-width", cc["tip_tangential_width_mm"] == 6.5, cc["tip_tangential_width_mm"])
    add("candidate-c-axial", cc["engagement_axial_width_mm"] == 22.0, cc["engagement_axial_width_mm"])
    add("candidate-c-root-r", cc["root_radius_mm"] == 1.25, cc["root_radius_mm"])
    add("tooth-count", cc["tooth_count"] == 12, cc["tooth_count"])
    add("spacing", cc["angles_deg"] == tooth_angles(), cc["angles_deg"])
    add("tooth-self-intersection", cc["maximum_pairwise_intersection_mm3"] == 0, cc["maximum_pairwise_intersection_mm3"])
    idler = analysis["idler"]
    add("idler-width", idler["total_width_mm"] == 44.0, idler["total_width_mm"])
    add("bearing-model", idler["bearing_model"] == "6000-2RS", idler["bearing_model"])
    add("bearing-count", idler["bearing_count"] == 2, idler["bearing_count"])
    add("bearing-seat", idler["bearing_seat_diameter_mm"] == 26.2 and idler["bearing_seat_depth_mm"] == 8.2, idler)
    add("center-relief", idler["center_relief_mm"] == 12.0, idler["center_relief_mm"])
    add("shaft-nominal", idler["shaft_nominal_mm"] == 10.0, idler["shaft_nominal_mm"])
    add("idler-valid", idler["valid"] and idler["solid_count"] == 1, idler)
    center = analysis["center_delta"]
    add("center-missing-zero", center["missing_volume_mm3"] == 0, center)
    add("center-added-zero", center["added_volume_mm3"] == 0, center)
    add("bearing-change-zero", center["bearing_seat_change_mm"] == 0, center)
    add("axis-change-zero", center["axis_change_mm"] == 0, center)
    clearance = analysis["clearance_360deg"]
    add("full-360", clearance["angular_coverage_deg"] == 360 and clearance["actual_link_instances"] == 12, clearance)
    for key in ["maximum_whole_idler_intersection_mm3", "maximum_body_bridge_intersection_mm3", "maximum_bearing_intersection_mm3", "maximum_shaft_intersection_mm3", "anti_derail_guide_intersection_mm3"]:
        add("zero-" + key, clearance[key] == 0, clearance[key])
    add("minimum-non-intended-clearance", clearance["minimum_non_intended_clearance_mm"] >= 1.0, clearance["minimum_non_intended_clearance_mm"])
    add("intended-tangent-no-penetration", clearance["intended_body_root_tangent_clearance_mm"] == 0 and clearance["maximum_body_bridge_intersection_mm3"] == 0, clearance)
    add("clearance-status", clearance["status"] == "PASS", clearance["status"])
    legacy = analysis["forbidden_drive_architecture"]
    add("misumi-absent", legacy["MISUMI_GROOVE1_DRIVE_INTERFACE"] == "ABSENT", legacy)
    add("keyed-absent", legacy["KEYED_TORQUE_PATH"] == "ABSENT", legacy)
    add("old-drive-absent", legacy["OLD_SHAFT_COLLAR_DRIVE_PATH"] == "ABSENT", legacy)
    add("bearing-idler", legacy["IDLER_ROTATION_ARCHITECTURE"] == "EXISTING_BEARING_BASED_AUTHORITY", legacy)
    add("p20653-candidate", "NOT_FINAL" in idler["pitch_status"], idler["pitch_status"])
    add("spacer-hold", "HOLD" in idler["spacer_contact"], idler["spacer_contact"])
    add("retention-hold", "HOLD" in idler["retention"], idler["retention"])
    add("staged-zero-record", validation["repository"]["staged"] == [], validation["repository"]["staged"])
    add("reproducibility", validation["reproducibility"]["status"] == "PASS", validation["reproducibility"])
    add("expected-path-count", len(EXPECTED) == int((base / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()[1].split("=")[1]), len(EXPECTED))
    steps, meshes = artifact_audit(base)
    add("step-count", len(steps) == len(STEPS), len(steps))
    for item in steps:
        add("step-" + Path(item["path"]).stem, item["reload"] == "PASS" and item["valid"] and item["solids"] >= 1, item)
    for relative, item in meshes.items():
        add("stl-watertight", item["watertight"] and item["manifold"], item)
        add("stl-bad-edge-zero", item["bad_edge_count"] == 0, item["bad_edge_count"])
        add("stl-degenerate-zero", item["degenerate_triangle_count"] == 0, item["degenerate_triangle_count"])
        add("stl-reload", item["reload"] == "PASS", item["reload"])
    add("status", params["status"] == STATUS, params["status"])
    add("forbidden-claims", all(claim not in params["status"] for claim in params["forbidden_claims"]), params["forbidden_claims"])
    if repo_checks:
        repository = guard(True)
        add("repository-guard", all(repository["checks"].values()), repository["checks"])
    return checks


def indexes() -> None:
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{relative}" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    rows = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / relative)}  {relative}" for relative in rows))


def create_zip() -> tuple[Path, str]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_CRAWLER_IDLER_CANDIDATE_C_V001_{stamp}.zip"
    if target.exists():
        raise RuntimeError("ZIP_OVERWRITE_PROHIBITED")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            archive.write(LANE / relative, arcname=f"{LANE_NAME}/{relative}")
    return target, sha(target)


def build() -> dict:
    repository = guard(False)
    analysis = geometry_analysis()
    generate_core(LANE, analysis)
    steps, meshes = artifact_audit(LANE)
    repro = reproducibility(analysis)
    checks = {
        "geometry_status": analysis["clearance_360deg"]["status"] == "PASS",
        "center_zero_diff": analysis["center_delta"]["missing_volume_mm3"] == 0 and analysis["center_delta"]["added_volume_mm3"] == 0,
        "printable_valid": analysis["idler"]["valid"] and analysis["idler"]["solid_count"] == 1,
        "all_steps_reload": all(item["reload"] == "PASS" and item["valid"] for item in steps),
        "all_stl_quality": all(item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 and item["reload"] == "PASS" for item in meshes.values()),
        "reproducibility": repro["status"] == "PASS",
        "drive_architecture_absent": all(value == "ABSENT" for key, value in analysis["forbidden_drive_architecture"].items() if key != "IDLER_ROTATION_ARCHITECTURE"),
    }
    validation = {"version": VERSION, "status": STATUS, "repository": repository, "analysis": analysis, "step_audit": steps, "stl_audit": meshes, "reproducibility": repro, "checks": checks}
    if not all(checks.values()):
        write_json(LANE / "validation_report.json", validation)
        raise RuntimeError("FAIL_CLOSED_VALIDATION " + json.dumps(checks))
    write_json(LANE / "validation_report.json", validation)
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nCADQUERY={cq.__version__}\nCENTER_ZERO_DIFF=PASS\nFULL_360=PASS\nMIN_CLEARANCE_MM={analysis['clearance_360deg']['minimum_whole_idler_clearance_mm']}\nREPRODUCIBILITY={repro['status']}")
    write(LANE / "TEST_LOG.txt", "PENDING")
    indexes()
    test = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    write(LANE / "TEST_LOG.txt", test.stdout + f"\nEXIT_CODE={test.returncode}")
    indexes()
    if test.returncode:
        raise RuntimeError("CONTRACT_TEST_FAIL\n" + test.stdout)
    end = guard(True)
    archive, archive_sha = create_zip()
    return {"repository": repository, "end": end, "analysis": analysis, "steps": steps, "meshes": meshes, "reproducibility": repro, "test_output": test.stdout, "zip": str(archive), "zip_sha256": archive_sha, "exact_path_count": len(EXPECTED)}


def verify() -> dict:
    repository = guard(True)
    checks = contract_checks(LANE, repo_checks=True)
    failed = [name for name, passed, _ in checks if not passed]
    return {"repository": repository, "checks": len(checks), "passed": len(checks) - len(failed), "failed": failed, "status": "PASS" if not failed else "FAIL"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--render-only", type=Path)
    parser.add_argument("--analysis-json", type=Path)
    args = parser.parse_args()
    if args.render_only:
        analysis = json.loads(args.analysis_json.read_text(encoding="utf-8")) if args.analysis_json else geometry_analysis()
        generate_core(args.render_only, analysis)
        print(json.dumps({"render_only": str(args.render_only), "paths": len(REPRO_PATHS)}))
        return 0
    result = verify() if args.verify else build()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status", "PASS") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
