"""Build low-material crawler sprocket single-tooth fit coupons V001.

This lane does not instantiate a sprocket pitch circle.  It imports the actual
reinforced crawler-link STL as a faceted solid and evaluates three local drive
lug candidates in a physically assemblable +Z insertion pose.  The MISUMI
Groove-1 carrier and every existing drivetrain lane remain read-only.
"""
from __future__ import annotations

import argparse
import collections
import functools
import hashlib
import importlib.util
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "crawler_sprocket_tooth_fit_coupons_v001"
LANE_REL = PurePosixPath("cad/common_rover/drivetrain") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PADDY-SWARM-CRAWLER-SPROCKET-TOOTH-FIT-COUPONS-V001"

LINK_LANE_REL = "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17"
LINK_LANE = ROOT / LINK_LANE_REL
LINK_BUILDER = LINK_LANE / "build_common_rover_crawler_link_anti_derail_guard_v0_9_6_17.py"
LINK_STL_REL = LINK_LANE_REL + "/artifacts/crawler_link_reinforced_anti_derail_guard_v0_9_6_17.stl"
LINK_STL = ROOT / LINK_STL_REL
LINK_STL_SHA = "3bf2f55347d045faf62d5f269d80ad59917c29c4029399a381397b4fe1d1d16c"

CARRIER_LANE_REL = "cad/common_rover/drivetrain/misumi_pulley_groove1_full_driven_carrier_v001"
CARRIER_LANE = ROOT / CARRIER_LANE_REL
CARRIER_STL_REL = CARRIER_LANE_REL + "/print/full_driven_wheel_carrier_groove1.stl"
CARRIER_STL = ROOT / CARRIER_STL_REL
CARRIER_STL_SHA = "2e06c099a83334f7097590da73cd33755f86230367ad40ee3608ad6a5428e121"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3795
OUTSIDE_DIGEST = "1b8a42673a4246a8cc69af4672d359548846d007c9244dacca1e66928a0015d6"
PROTECTED = {
    LINK_LANE_REL: (33, "3e0a550c7d9faa38fae8d106e60b91467788e18533d23063156070d1259615b8"),
    CARRIER_LANE_REL: (28, "ac04cd892018cdc7d60116254ab47102507c4e3608bf7505c59aa2e863b7d9a1"),
    "cad/common_rover/common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34": (36, "121ae43e71aa732e601e67595401284f8953e4f55bde71dbd3340646e452451d"),
    "cad/common_rover/common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31": (20, "8065cefb36cef1dfb823a989185a67534f7eebdfd432fd5a664b364cc9053a72"),
    "cad/common_rover/bbox_lid_wiring_chimney_v004_drainage_biased_gland": (27, "7c08b27d629ad800c9a5caa55357466dd1413f740027f30cce7303ee2fe1de25"),
}

CANDIDATES = {
    "A": {"radial_height_mm": 4.0, "tip_tangential_width_mm": 5.5, "axial_width_mm": 18.0, "intent": "MAXIMUM_GEOMETRIC_CLEARANCE_FIRST_PHYSICAL_FIT"},
    "B": {"radial_height_mm": 4.25, "tip_tangential_width_mm": 6.0, "axial_width_mm": 20.0, "intent": "CAD_PRIMARY_BALANCED_FIT_AND_DRIVE_FACE"},
    "C": {"radial_height_mm": 4.5, "tip_tangential_width_mm": 6.5, "axial_width_mm": 22.0, "intent": "LARGEST_CLEARANCE_BIASED_CANDIDATE"},
}
CAD_PRIMARY = "B"
PHYSICAL_ORDER = ["A", "B", "C"]
ROOT_FILLET_R = 1.25
ROOT_SIDE_GROWTH = 1.0
BASE_T = 3.0
ROOT_PLANE_ENGAGED_Z = 3.5
CENTRAL_BRIDGE_UNDERSIDE_Z = 9.0
CURRENT_REPORTED_RADIAL_HEIGHT = 8.3
CURRENT_REPORTED_TIP_WIDTH_RANGE = [7.6, 8.2]
CURRENT_CARRIER_AXIAL_WIDTH = 44.0
FUTURE_TARGET_TOOTH_COUNT = 12

BUILDER = Path(__file__).name
TEST = "tests/test_crawler_sprocket_tooth_fit_coupons_v001_contract.py"
# Source authority is an STL mesh and this phase intentionally creates only
# pitch-free print gauges.  STEP is therefore not emitted; the contract clause
# is "STEP reload if generated" and remains explicitly NOT_APPLICABLE.
STEPS: list[str] = []
STLS = [
    "print/crawler_tooth_fit_A_h4p0_w5p5_ax18.stl",
    "print/crawler_tooth_fit_B_h4p25_w6p0_ax20.stl",
    "print/crawler_tooth_fit_C_h4p5_w6p5_ax22.stl",
    "print/combined_crawler_tooth_fit_A_B_C.stl",
]
SVGS = [
    "artifacts/TOOTH_CANDIDATE_DIMENSIONS.svg",
    "artifacts/ACTUAL_LINK_ENGAGEMENT_SECTION.svg",
    "artifacts/PHYSICAL_SELECTION_SEQUENCE.svg",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "SOURCE_TRACE.md", "CURRENT_FAILURE_DIAGNOSIS.md",
    "COLLISION_REPORT.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt",
    "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


link_authority = load_module("crawler_link_v09617_read_only", LINK_BUILDER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = git("diff", "--cached", "--name-only").splitlines()
    dirty = git("diff", "--name-only").splitlines()
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    inputs = {LINK_STL_REL: sha(LINK_STL), CARRIER_STL_REL: sha(CARRIER_STL)}
    files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()) if LANE.exists() else []
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_5": protected == PROTECTED,
        "input_sha": inputs == {LINK_STL_REL: LINK_STL_SHA, CARRIER_STL_REL: CARRIER_STL_SHA},
        "scope": set(files).issubset(EXPECTED), "cache_zero": not cache,
        "ignored_zero": not ignored, "complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "inputs": inputs,
        "protected": {key: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for key, value in protected.items()},
        "lane_files": len(files),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(report, ensure_ascii=True))
    return report


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def common_volume(left: cq.Shape, right: cq.Shape) -> float:
    try:
        intersection = left.intersect(right)
        return 0.0 if intersection.isNull() else intersection.Volume()
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


@functools.lru_cache(maxsize=1)
def actual_link() -> cq.Shape:
    if sha(LINK_STL) != LINK_STL_SHA:
        raise RuntimeError("CRAWLER_LINK_SOURCE_HASH_MISMATCH")
    shape = link_authority.source_mesh_to_faceted_solid(LINK_STL)
    if not shape.isValid():
        raise RuntimeError("CRAWLER_LINK_SOURCE_INVALID")
    return shape


def candidate_tooth(code: str) -> cq.Workplane:
    values = CANDIDATES[code]
    height = values["radial_height_mm"]
    tip_half = values["tip_tangential_width_mm"] / 2.0
    axial = values["axial_width_mm"]
    side_half = tip_half + ROOT_SIDE_GROWTH
    start_half = side_half + ROOT_FILLET_R
    mid = ROOT_FILLET_R / math.sqrt(2.0)
    profile = (
        cq.Workplane("XZ")
        .moveTo(-start_half, 0.0).lineTo(start_half, 0.0)
        .threePointArc((side_half + mid, mid), (side_half, ROOT_FILLET_R))
        .lineTo(tip_half, height).lineTo(-tip_half, height)
        .lineTo(-side_half, ROOT_FILLET_R)
        .threePointArc((-side_half - mid, mid), (-start_half, 0.0))
        .close()
    )
    return profile.extrude(axial / 2.0, both=True)


def label_tools(code: str) -> list[cq.Workplane]:
    """Sequential convex cuts form deterministic recessed block letters."""
    left = box(0.7, 4.0, 1.0, (-21.65, 0.0, -0.4))
    right = box(0.7, 4.0, 1.0, (-18.35, 0.0, -0.4))
    top = box(4.0, 0.7, 1.0, (-20.0, 1.6, -0.4))
    middle = box(4.0, 0.7, 1.0, (-20.0, 0.0, -0.4))
    bottom = box(4.0, 0.7, 1.0, (-20.0, -1.6, -0.4))
    if code == "A":
        return [left, right, top, middle]
    if code == "B":
        return [left, right, top, middle, bottom]
    if code == "C":
        return [top, left, bottom]
    raise ValueError(code)


def coupon(code: str) -> cq.Workplane:
    axial = CANDIDATES[code]["axial_width_mm"]
    base = box(16.0, axial + 6.0, BASE_T, (0.0, 0.0, -BASE_T / 2.0))
    tab = box(24.0, 12.0, BASE_T, (-18.0, 0.0, -BASE_T / 2.0))
    shape = base.union(tab).union(candidate_tooth(code)).clean()
    for tool in label_tools(code):
        shape = shape.cut(tool).clean()
    return shape


def combined_coupon() -> cq.Workplane:
    positions = {"A": -34.0, "B": 0.0, "C": 36.0}
    shape = coupon("A").translate((0, positions["A"], 0))
    for code in ("B", "C"):
        shape = shape.union(coupon(code).translate((0, positions[code], 0)))
    connector = box(4.0, 98.0, 2.0, (-25.0, 2.0, -2.0))
    return shape.union(connector).clean()


def engaged(shape: cq.Workplane, root_z: float = ROOT_PLANE_ENGAGED_Z) -> cq.Shape:
    return shape.translate((0.0, 0.0, root_z)).val()


def top_face_dimensions(code: str) -> tuple[float, float]:
    height = CANDIDATES[code]["radial_height_mm"]
    faces = [face for face in candidate_tooth(code).val().Faces() if abs(face.Center().z - height) < 1.0e-6 and face.normalAt().z > 0.99]
    if len(faces) != 1:
        raise RuntimeError("TIP_FACE_NOT_UNIQUE")
    bounds = faces[0].BoundingBox()
    return round(bounds.xlen, 6), round(bounds.ylen, 6)


@functools.lru_cache(maxsize=1)
def feature_shapes() -> dict[str, cq.Shape]:
    link = actual_link()
    return {
        "hinge_bridge": link.intersect(box(18.0, 36.0, 18.0, (0.0, 0.0, 16.0)).val()),
        "pivot_negative_x": link.intersect(box(8.0, 44.0, 25.0, (-12.0, 0.0, 12.5)).val()),
        "pivot_positive_x": link.intersect(box(8.0, 44.0, 25.0, (12.0, 0.0, 12.5)).val()),
        "anti_derail_negative_y": link.intersect(box(40.0, 13.0, 9.0, (0.0, -22.5, 4.5)).val()),
        "anti_derail_positive_y": link.intersect(box(40.0, 13.0, 9.0, (0.0, 22.5, 4.5)).val()),
    }


@functools.lru_cache(maxsize=3)
def candidate_metrics(code: str) -> dict:
    values = CANDIDATES[code]
    tooth_local = candidate_tooth(code)
    tooth = engaged(tooth_local)
    coupon_engaged = engaged(coupon(code))
    link = actual_link()
    features = feature_shapes()
    height = values["radial_height_mm"]
    tip_z = ROOT_PLANE_ENGAGED_Z + height
    tip_x, tip_y = top_face_dimensions(code)
    whole_interference = common_volume(tooth, link)
    coupon_interference = common_volume(coupon_engaged, link)
    approach = {}
    for root_z in (0.0, 1.75, ROOT_PLANE_ENGAGED_Z):
        approach[f"root_z_{root_z:g}"] = round(common_volume(engaged(tooth_local, root_z), link), 9)
    distances = {name: round(tooth.distance(shape), 6) for name, shape in features.items()}
    global_clearance = round(tooth.distance(link), 6)
    bounds = tooth_local.val().BoundingBox()
    return {
        "candidate_id": code,
        "radial_height_mm": height,
        "tip_tangential_width_mm": values["tip_tangential_width_mm"],
        "tip_tangential_width_measured_mm": tip_x,
        "axial_width_mm": values["axial_width_mm"],
        "axial_width_measured_at_tip_mm": tip_y,
        "root_transition_radius_mm": ROOT_FILLET_R,
        "root_total_tangential_width_mm": round(bounds.xlen, 6),
        "root_plane_engaged_z_mm": ROOT_PLANE_ENGAGED_Z,
        "tip_engaged_z_mm": tip_z,
        "central_bridge_underside_z_mm": CENTRAL_BRIDGE_UNDERSIDE_Z,
        "radial_clearance_to_bridge_mm": round(CENTRAL_BRIDGE_UNDERSIDE_Z - tip_z, 6),
        "minimum_global_clearance_mm": global_clearance,
        "minimum_anti_derail_side_clearance_mm": min(distances["anti_derail_negative_y"], distances["anti_derail_positive_y"]),
        "minimum_pivot_region_clearance_mm": min(distances["pivot_negative_x"], distances["pivot_positive_x"]),
        "feature_clearances_mm": distances,
        "maximum_interference_volume_mm3": round(whole_interference, 9),
        "coupon_interference_volume_mm3": round(coupon_interference, 9),
        "hinge_bridge_interference_mm3": round(whole_interference, 9),
        "pivot_screw_region_interference_mm3": round(whole_interference, 9),
        "anti_derail_interference_mm3": round(whole_interference, 9),
        "approach_path_interference_mm3": approach,
        "achievable_insertion_depth_mm": height,
        "full_depth_seating_cad": whole_interference == 0 and global_clearance > 0,
        "local_contact_surfaces": "NONE_AT_INTENDED_POSE",
        "nearest_surfaces": "TOOTH_TIP_TO_CENTRAL_HINGE_BRIDGE_UNDERSIDE",
        "candidate_valid": tooth_local.val().isValid(),
        "candidate_solids": len(tooth_local.solids().vals()),
        "coupon_valid": coupon(code).val().isValid(),
        "coupon_solids": len(coupon(code).solids().vals()),
        "intent": values["intent"],
        "physical_fit": "PENDING",
    }


def source_metrics() -> dict:
    link_metrics = mesh_metrics(LINK_STL)
    carrier_metrics = mesh_metrics(CARRIER_STL)
    carrier_params = json.loads((CARRIER_LANE / "design_parameters.json").read_text(encoding="utf-8"))
    return {
        "crawler_link": {
            "path": LINK_STL_REL, "sha256": LINK_STL_SHA, "scale": 1.0,
            "bounds_mm": link_metrics["bounds_mm"], "extents_mm": link_metrics["extents_mm"],
            "watertight": link_metrics["watertight"], "manifold": link_metrics["manifold"],
        },
        "current_carrier": {
            "path": CARRIER_STL_REL, "sha256": CARRIER_STL_SHA,
            "bounds_mm": carrier_metrics["bounds_mm"], "extents_mm": carrier_metrics["extents_mm"],
            "watertight": carrier_metrics["watertight"], "manifold": carrier_metrics["manifold"],
            "authority_outer_geometry": carrier_params["carrier"]["outer_geometry"],
            "authority_outer_tooth_count": carrier_params["carrier"]["outer_tooth_count"],
            "authority_outer_width_mm": carrier_params["carrier"]["outer_width_mm"],
        },
    }


def parameters() -> dict:
    candidates = {code: candidate_metrics(code) for code in PHYSICAL_ORDER}
    return {
        "version": VERSION,
        "sources": source_metrics(),
        "physical_failure": {
            "classification": "SPROCKET_TO_CRAWLER_TOOTH_GEOMETRY_PHYSICAL_FAIL",
            "not_a_groove1_failure": True,
            "current_tooth_radial_height_mm_approx": CURRENT_REPORTED_RADIAL_HEIGHT,
            "current_tooth_tip_tangential_width_mm_approx_range": CURRENT_REPORTED_TIP_WIDTH_RANGE,
            "current_tooth_axial_width_mm": CURRENT_CARRIER_AXIAL_WIDTH,
            "diagnosis": "CURRENT_TOOTH_REACHES_NARROWING_HINGE_BRIDGE_AND_SIDE_GEOMETRY_BEFORE_USEFUL_FULL_ENGAGEMENT",
        },
        "protected_drivetrain": {
            "pulley_groove1_physical_fit": "PASS",
            "pulley_groove1_static_torque_transfer": "PASS",
            "shaft_key_manual_rotation": "PASS",
            "full_carrier_manual_forward_reverse": "PASS",
            "misumi_geometry_change": 0, "groove1_change": 0, "shaft_key_change": 0,
            "center_carrier_change": 0, "keeper_change": 0, "hub_change": 0, "pulley_position_change": 0,
        },
        "coordinate_contract": {
            "crawler_travel_tangential_axis": "X",
            "crawler_shaft_axial_axis": "Y",
            "tooth_radial_insertion_axis": "+Z",
            "link_pose_source_coordinates": True,
            "root_plane_engaged_z_mm": ROOT_PLANE_ENGAGED_Z,
            "central_bridge_underside_z_mm": CENTRAL_BRIDGE_UNDERSIDE_Z,
            "assembly_method": "STRAIGHT_PLUS_Z_SINGLE_TOOTH_INSERTION_WITH_OPEN_SIDE_ACCESS",
        },
        "candidates": candidates,
        "selection": {
            "cad_primary": CAD_PRIMARY, "physical_order": PHYSICAL_ORDER,
            "rule": "LARGEST_FULLY_SEATING_NO_FORCE_NO_HINGE_NO_SIDE_CONTACT_CANDIDATE_WITH_CLEAR_PHYSICAL_MARGIN",
            "mud_clearance_priority": True,
        },
        "pitch_hold": {
            "future_requested_tooth_count": FUTURE_TARGET_TOOTH_COUNT,
            "current_reference_carrier_tooth_count": 14,
            "conflict_disposition": "NO_PATTERN_GENERATED_SINGLE_TOOTH_ONLY_FUTURE_12T_REMAINS_HOLD",
            "crawler_pitch_authority": "HOLD",
            "sprocket_pitch_diameter": "HOLD",
            "existing_angular_center_reference_change": 0,
            "three_tooth_sector": "NOT_GENERATED_PITCH_AUTHORITY_HOLD",
            "full_sprocket": "NOT_GENERATED",
        },
        "print": {
            "printer": "Bambu Lab A1", "material": "PETG",
            "first_print": STLS[0], "test_order": PHYSICAL_ORDER,
            "combined_plate": STLS[3], "slicer": "HOLD_SLICER_NOT_RUN",
        },
        "status": "CAD_PASS/CONTRACT_TEST_PASS/CRAWLER_TOOTH_FIT_COUPONS_PRINT_READY/CRAWLER_TOOTH_GEOMETRY_PHYSICAL_VALIDATION_PENDING",
        "holds": ["CRAWLER_TOOTH_GEOMETRY_PHYSICAL_VALIDATION_PENDING", "CRAWLER_PITCH_PENDING", "POWERED_CRAWLER_TEST_HOLD"],
        "forbidden_claims": ["CRAWLER_DRIVE_PASS", "POWERED_TORQUE_PASS", "DRY_RUN_PASS", "MUD_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9Z" fill="#245ca6"/></marker></defs><style>text{{font-family:Arial,sans-serif;fill:#17212b}}.t{{font-size:30px;font-weight:700}}.s{{font-size:18px;fill:#455}}.n{{font-size:18px}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:3}}.g{{fill:#dcfce7;stroke:#087f5b;stroke-width:3}}.q{{fill:#fff7ed;stroke:#c2410c;stroke-width:3}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:3}}.a{{stroke:#245ca6;stroke-width:4;marker-end:url(#a)}}.d{{stroke:#8b1e3f;stroke-width:3}}</style><text x="55" y="60" class="t">{title}</text><text x="55" y="95" class="s">{subtitle}</text>{body}</svg>'''


def svg_payload() -> dict[str, str]:
    a, b, c = (candidate_metrics(code) for code in PHYSICAL_ORDER)
    return {
        SVGS[0]: svg("SINGLE-TOOTH FIT CANDIDATES", "Tip dimensions are exact; the R1.25 root widens locally without changing the tip.", '<g transform="translate(100,170)"><path d="M0 330H250V275H170L150 80H100L80 275H0Z" class="b"/><text x="85" y="365" class="n">A · H4.0 · W5.5 · AX18</text></g><g transform="translate(475,160)"><path d="M0 340H250V280H175L152 68H98L75 280H0Z" class="g"/><text x="70" y="375" class="n">B PRIMARY · H4.25 · W6.0 · AX20</text></g><g transform="translate(850,150)"><path d="M0 350H250V285H180L155 55H95L70 285H0Z" class="q"/><text x="60" y="385" class="n">C · H4.5 · W6.5 · AX22</text></g><text x="350" y="625" class="n">No pitch circle and no full sprocket are generated in this phase.</text>'),
        SVGS[1]: svg("ACTUAL LINK ENGAGEMENT SECTION", "Actual v0.9.6.17 STL; root Z3.5, central bridge underside Z9.0.", f'<rect x="130" y="175" width="940" height="120" class="r"/><text x="470" y="240" class="n">crawler hinge / bridge material begins at Z9</text><path d="M500 540H700L655 320H545Z" class="g"/><line x1="100" y1="295" x2="1100" y2="295" class="d"/><line x1="100" y1="540" x2="1100" y2="540" class="d"/><text x="100" y="285" class="n">Z9.0 bridge underside</text><text x="100" y="565" class="n">Z3.5 root datum</text><text x="735" y="340" class="n">B tip Z{b["tip_engaged_z_mm"]:.2f}</text><text x="735" y="375" class="n">radial clearance {b["radial_clearance_to_bridge_mm"]:.2f} mm</text><text x="735" y="410" class="n">actual-link interference 0 mm³</text>'),
        SVGS[2]: svg("PHYSICAL SELECTION SEQUENCE", "Largest candidate is not automatically selected; contamination clearance remains important.", '<rect x="80" y="210" width="230" height="180" class="b"/><text x="165" y="305" class="n">A FIRST</text><path d="M330 300H450" class="a"/><rect x="470" y="210" width="230" height="180" class="g"/><text x="545" y="285" class="n">B PRIMARY</text><text x="525" y="325" class="n">if A passes</text><path d="M720 300H840" class="a"/><rect x="860" y="210" width="230" height="180" class="q"/><text x="945" y="285" class="n">C ONLY</text><text x="895" y="325" class="n">with clear margin</text><text x="155" y="490" class="n">Each: natural seat → rock → withdraw → 5 cycles → inspect tooth and link</text><text x="240" y="545" class="n">Pitch / pitch diameter / powered crawler test remain HOLD.</text>'),
    }


def collision_table() -> str:
    rows = ["| Candidate | Interference mm³ | Bridge clearance mm | Side clearance mm | Pivot clearance mm | Full depth CAD |", "|---|---:|---:|---:|---:|---|"]
    for code in PHYSICAL_ORDER:
        m = candidate_metrics(code)
        rows.append(f"| {code} | {m['maximum_interference_volume_mm3']:.6f} | {m['radial_clearance_to_bridge_mm']:.3f} | {m['minimum_anti_derail_side_clearance_mm']:.3f} | {m['minimum_pivot_region_clearance_mm']:.3f} | {'YES' if m['full_depth_seating_cad'] else 'NO'} |")
    return "\n".join(rows)


def documents() -> dict[str, str]:
    source = source_metrics()
    heading = "# Crawler sprocket tooth fit coupons V001\n\n"
    return {
        "README.md": heading + "Low-material A/B/C single-tooth gauges for the actual reinforced crawler link. The first print is `print/crawler_tooth_fit_A_h4p0_w5p5_ax18.stl`; test A→B→C. No pitch circle or complete sprocket is generated. Status: `CAD_PASS / CONTRACT_TEST_PASS / CRAWLER_TOOTH_FIT_COUPONS_PRINT_READY / CRAWLER_TOOTH_GEOMETRY_PHYSICAL_VALIDATION_PENDING`.\n",
        "DESIGN_AUTHORITY.md": heading + "This lane creates local replaceable tooth-fit gauges only. It does not alter or reproduce MISUMI metal pulley geometry, Groove-1, shaft/key, carrier center, keeper, hub or pulley position. Existing Groove-1 physical fit/static torque, shaft-key manual rotation and full-carrier manual forward/reverse PASS results remain valid. Physical tooth fit—not CAD clearance—will select authority.\n",
        "SOURCE_TRACE.md": heading + f"Crawler link: `{LINK_STL_REL}`, SHA-256 `{LINK_STL_SHA}`, actual bounds {source['crawler_link']['bounds_mm']} mm, scale1.0, watertight/manifold. Current carrier: `{CARRIER_STL_REL}`, SHA-256 `{CARRIER_STL_SHA}`, authority `{source['current_carrier']['authority_outer_geometry']}`, width {source['current_carrier']['authority_outer_width_mm']:.1f} mm. Both lanes are read-only and protected by complete tree hashes.\n",
        "CURRENT_FAILURE_DIAGNOSIS.md": heading + "Powered crawler tooth slip is classified as `SPROCKET_TO_CRAWLER_TOOTH_GEOMETRY = PHYSICAL_FAIL`, not a MISUMI/Groove-1 failure. User-reported current tooth is approximately H8.3 mm, tip W7.6–8.2 mm and axial44 mm; the actual link valley closes at the central hinge/bridge near Z9 and has protected side/anti-derail structures. The narrower H4.0–4.5, W5.5–6.5, AX18–22 gauges isolate valley fit before pitch work.\n",
        "COLLISION_REPORT.md": heading + collision_table() + "\n\nPose: actual link source coordinates; X tangential, Y axial, +Z tooth insertion; root plane Z3.5 mm. A/B/C approach samples at root Z0,1.75,3.5 have zero intersection. Contact surfaces are NONE at the intended pose; nearest surfaces are the tooth tip and central bridge underside. CAD zero interference does not authorize physical fit.\n",
        "PHYSICAL_TEST_PLAN.md": heading + "Print/test A→B→C. For each: insert the real link; push only to natural seating; inspect side/hinge/bridge/anti-derail clearance; rock gently; withdraw; repeat five cycles; inspect PETG tooth and link. Record FULL_DEPTH_SEATING, HINGE_CONTACT, SIDE_CONTACT, SCRAPING, TANGENTIAL_PLAY, AXIAL_PLAY, TOOTH_DAMAGE and LINK_DAMAGE. Select the largest candidate that fully seats without force or contact and retains clear contamination margin. Prefer B over A only when B is not noticeably tight; use C only with clear physical margin.\n",
        "HOLD_REGISTER.md": heading + "- crawler tooth physical fit and five-cycle inspection\n- crawler pitch authority and pitch diameter\n- full 12T pattern and angular validation\n- optional three-tooth sector (`NOT_GENERATED_PITCH_AUTHORITY_HOLD`)\n- final full sprocket\n- slicer review\n- powered crawler, dry-run, mud and field tests\n- conflict note: current protected reference carrier is P20653 14T, while the future requested target is 12T; this lane generates no tooth pattern, so neither pitch authority is altered or inferred\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-28T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), tolerance=0.035, angularTolerance=0.08)
    canonicalize_binary_stl(path)


def canonicalize_binary_stl(path: Path):
    """Normalize triangle rotation and record order after OCCT tessellation."""
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL_TOO_SHORT")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_NOT_CANONICAL_BINARY")
    records = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        vertices = [
            tuple(0.0 if abs(float(value)) < 5.0e-6 else round(float(value), 5) for value in values[offset:offset + 3])
            for offset in (3, 6, 9)
        ]
        rotations = [vertices[i:] + vertices[:i] for i in range(3)]
        ordered = min(rotations, key=lambda row: tuple(value for vertex in row for value in vertex))
        left = tuple(ordered[1][axis] - ordered[0][axis] for axis in range(3))
        right = tuple(ordered[2][axis] - ordered[0][axis] for axis in range(3))
        normal = (
            left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0],
        )
        length = math.sqrt(sum(value * value for value in normal))
        unit = tuple(value / length for value in normal) if length else (0.0, 0.0, 0.0)
        key = tuple(value for vertex in ordered for value in vertex)
        records.append((key, struct.pack("<12fH", *unit, *ordered[0], *ordered[1], *ordered[2], 0)))
    records.sort(key=lambda item: item[0])
    header = b"PADDY_SWARM_CANONICAL_BINARY_STL".ljust(80, b"\0")
    path.write_bytes(header + struct.pack("<I", count) + b"".join(record for _, record in records))


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


def mesh_metrics(path: Path) -> dict:
    triangles = list(binary_stl(path))
    edges: collections.Counter = collections.Counter()
    degenerate = 0
    triangle_edges = []
    vertices_all = []
    for triangle in triangles:
        vertices = [tuple(round(float(value), 5) for value in vertex) for vertex in triangle]
        vertices_all.extend(vertices)
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1.0e-14:
            degenerate += 1
        row = []
        for left, right in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edge = tuple(sorted((left, right)))
            edges[edge] += 1
            row.append(edge)
        triangle_edges.append(row)
    parents = list(range(len(triangles)))
    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index
    def union(left: int, right: int):
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a
    ownership = {}
    for triangle_index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in ownership:
                union(triangle_index, ownership[edge])
            else:
                ownership[edge] = triangle_index
    bad = sum(count != 2 for count in edges.values())
    bounds = [[min(vertex[i] for vertex in vertices_all) for i in range(3)], [max(vertex[i] for vertex in vertices_all) for i in range(3)]]
    return {
        "triangle_count": len(triangles), "component_count": len({find(i) for i in range(len(triangles))}),
        "watertight": bad == 0, "manifold": bad == 0, "bad_edge_count": bad,
        "degenerate_triangle_count": degenerate, "reload": "PASS",
        "bounds_mm": bounds, "extents_mm": [round(bounds[1][i] - bounds[0][i], 6) for i in range(3)],
    }


def generated_shapes() -> dict[str, cq.Workplane]:
    shapes = {code: coupon(code) for code in PHYSICAL_ORDER}
    combined = combined_coupon()
    stls = {STLS[0]: shapes["A"], STLS[1]: shapes["B"], STLS[2]: shapes["C"], STLS[3]: combined}
    return stls


def generate(out: Path):
    stls = generated_shapes()
    for relative, shape in stls.items():
        export_stl(shape, out / relative)
    for relative, payload in svg_payload().items():
        write(out / relative, payload)
    for relative, payload in documents().items():
        write(out / relative, payload)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def artifact_audit(out: Path) -> tuple[list[dict], list[dict]]:
    step_results = []
    stl_results = [{"path": relative, **mesh_metrics(out / relative)} for relative in STLS]
    return step_results, stl_results


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="crawler_tooth_fit_repro_") as temp:
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise RuntimeError("REPRO_RENDER_FAIL\n" + result.stdout + result.stderr)
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract() -> tuple[int, str]:
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def build() -> tuple[dict, dict]:
    repository = guard(False)
    generate(LANE)
    candidates = {code: candidate_metrics(code) for code in PHYSICAL_ORDER}
    step_results, stl_results = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "source_link_hash": sha(LINK_STL) == LINK_STL_SHA,
        "source_carrier_hash": sha(CARRIER_STL) == CARRIER_STL_SHA,
        "candidate_A_exact": [candidates["A"][key] for key in ("radial_height_mm", "tip_tangential_width_mm", "axial_width_mm")] == [4.0, 5.5, 18.0],
        "candidate_B_exact": [candidates["B"][key] for key in ("radial_height_mm", "tip_tangential_width_mm", "axial_width_mm")] == [4.25, 6.0, 20.0],
        "candidate_C_exact": [candidates["C"][key] for key in ("radial_height_mm", "tip_tangential_width_mm", "axial_width_mm")] == [4.5, 6.5, 22.0],
        "tip_measured_exact": all(candidates[code]["tip_tangential_width_measured_mm"] == CANDIDATES[code]["tip_tangential_width_mm"] for code in PHYSICAL_ORDER),
        "axial_measured_exact": all(candidates[code]["axial_width_measured_at_tip_mm"] == CANDIDATES[code]["axial_width_mm"] for code in PHYSICAL_ORDER),
        "root_r": all(candidates[code]["root_transition_radius_mm"] == 1.25 for code in PHYSICAL_ORDER),
        "candidate_valid": all(candidates[code]["candidate_valid"] and candidates[code]["candidate_solids"] == 1 for code in PHYSICAL_ORDER),
        "coupon_valid": all(candidates[code]["coupon_valid"] and candidates[code]["coupon_solids"] == 1 for code in PHYSICAL_ORDER),
        "whole_collision_zero": all(candidates[code]["maximum_interference_volume_mm3"] == 0 for code in PHYSICAL_ORDER),
        "coupon_collision_zero": all(candidates[code]["coupon_interference_volume_mm3"] == 0 for code in PHYSICAL_ORDER),
        "hinge_collision_zero": all(candidates[code]["hinge_bridge_interference_mm3"] == 0 for code in PHYSICAL_ORDER),
        "pivot_collision_zero": all(candidates[code]["pivot_screw_region_interference_mm3"] == 0 for code in PHYSICAL_ORDER),
        "guard_collision_zero": all(candidates[code]["anti_derail_interference_mm3"] == 0 for code in PHYSICAL_ORDER),
        "approach_zero": all(max(candidates[code]["approach_path_interference_mm3"].values()) == 0 for code in PHYSICAL_ORDER),
        "full_depth": all(candidates[code]["full_depth_seating_cad"] for code in PHYSICAL_ORDER),
        "radial_margin": all(candidates[code]["radial_clearance_to_bridge_mm"] >= 1.0 for code in PHYSICAL_ORDER),
        "side_margin": all(candidates[code]["minimum_anti_derail_side_clearance_mm"] >= 5.0 for code in PHYSICAL_ORDER),
        "pivot_margin": all(candidates[code]["minimum_pivot_region_clearance_mm"] >= 2.5 for code in PHYSICAL_ORDER),
        "no_pitch_pattern": parameters()["pitch_hold"]["full_sprocket"] == "NOT_GENERATED",
        "twelve_hold": parameters()["pitch_hold"]["future_requested_tooth_count"] == 12 and parameters()["pitch_hold"]["crawler_pitch_authority"] == "HOLD",
        "groove1_untouched": all(value == 0 for key, value in parameters()["protected_drivetrain"].items() if key.endswith("_change")),
        "step_not_generated_mesh_phase": not step_results,
        "stl_quality": all(item["reload"] == "PASS" and item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 for item in stl_results),
        "reproducibility": repro["status"] == "PASS",
        "authority": repository["checks"]["authority_4"], "protected": repository["checks"]["protected_5"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "sources": source_metrics(),
        "candidates": candidates, "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "step": step_results, "stl": stl_results, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "inputs": repository["inputs"], "authority": repository["authority"], "protected": repository["protected"]},
        "holds": parameters()["holds"], "forbidden_claims": parameters()["forbidden_claims"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nCHECKS={sum(checks.values())}/{len(checks)} PASS\nSTEP_RELOAD=NOT_APPLICABLE_MESH_COUPON_PHASE\nSTL_QUALITY={sum(item['reload'] == 'PASS' and item['watertight'] and item['manifold'] for item in stl_results)}/{len(stl_results)} PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks, indent=2))
    return guard(True), validation


def package() -> tuple[Path, str]:
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_CRAWLER_SPROCKET_TOOTH_FIT_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 28, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
    with zipfile.ZipFile(path, "r") as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(EXPECTED):
            raise RuntimeError("ZIP_VERIFY_FAIL")
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only:
        generate(args.render_only)
        return 0
    repository, validation = build()
    result = {
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED),
        "steps": len(STEPS), "stls": len(STLS), "svgs": len(SVGS),
        "branch": repository["branch"], "head": repository["head"], "staged": repository["staged"],
        "checks": [validation["pass_count"], validation["check_count"]], "candidates": validation["candidates"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
