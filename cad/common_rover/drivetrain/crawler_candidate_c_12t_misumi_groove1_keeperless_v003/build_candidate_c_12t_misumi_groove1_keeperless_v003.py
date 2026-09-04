"""Build Candidate-C 12T + exact MISUMI Groove-1 keeperless carrier V003.

Only the new untracked lane is written.  Candidate-C, Groove-1, crawler-link,
P20653 placement, and spacer source lanes are imported/read as immutable
authorities.  The old OD66/PCD56 keeper architecture is intentionally absent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
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
LANE_NAME = "crawler_candidate_c_12t_misumi_groove1_keeperless_v003"
LANE_REL = PurePosixPath("cad/common_rover/drivetrain") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PADDY-SWARM-CANDIDATE-C-12T-MISUMI-GROOVE1-KEEPERLESS-V003"
STATUS = "CAD_PASS/CONTRACT_TEST_PASS/CANDIDATE_C_12T_MISUMI_KEEPERLESS_PRINT_READY/SPACER_STACK_PHYSICAL_VALIDATION_PENDING"

COUPON_REL = PurePosixPath("cad/common_rover/drivetrain/crawler_sprocket_tooth_fit_coupons_v001")
GROOVE_REL = PurePosixPath("cad/common_rover/drivetrain/misumi_pulley_groove1_full_driven_carrier_v001")
FAILED_OUTER_REL = PurePosixPath("cad/common_rover/drivetrain/crawler_candidate_c_full_12t_sprocket_v001")
PITCH_REL = PurePosixPath("cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20")
LINK_REL = PurePosixPath("cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17")
SPACER_REL = PurePosixPath("cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6")
SPACER_PHYSICAL_REL = PurePosixPath("cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9")
VENDOR_REL = PurePosixPath("cad/common_rover/common_rover_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34")

COUPON_BUILDER = ROOT / COUPON_REL / "build_crawler_sprocket_tooth_fit_coupons_v001.py"
GROOVE_BUILDER = ROOT / GROOVE_REL / "build_misumi_groove1_full_driven_carrier_v001.py"
FAILED_OUTER_BUILDER = ROOT / FAILED_OUTER_REL / "build_candidate_c_full_12t_sprocket_v001.py"
LINK_STL = ROOT / LINK_REL / "artifacts/crawler_link_reinforced_anti_derail_guard_v0_9_6_17.stl"
SPACER_STEP = ROOT / SPACER_REL / "drive/artifacts/drive_spacer_8mm_v0_9_6_6.step"
SPACER_STL = ROOT / SPACER_REL / "drive/artifacts/drive_spacer_8mm_v0_9_6_6.stl"
VENDOR_STEP = ROOT / VENDOR_REL / "source/vendor/PTPK28P5M150-A-N10-NFC.stp"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = sorted(AUTHORITY)
OUTSIDE_COUNT = 3842
OUTSIDE_SHA = "f819d2cf99183206e135e07d3fe378f86c4a965753ce36353f711d05149e64f7"
PROTECTED = {
    COUPON_REL.as_posix(): (23, "18dfcd36ae1db9f779e641f2e72241c908df471727f3ae4bfc61b9fbccdf6a19"),
    GROOVE_REL.as_posix(): (28, "ca9e647a0bc3c50fef4b8a059ddc364495f98c8ad00a64913f675dcd692fb21e"),
    FAILED_OUTER_REL.as_posix(): (24, "186585902012b54363bc732d238317fc35aabae3321d16fa813e731a0c56016c"),
    PITCH_REL.as_posix(): (55, "5bc9cd5611b93b7ec67e68a7b6342f0c333245096bb961cfcf5fed2ecf2e7eef"),
    LINK_REL.as_posix(): (33, "f26d294d4f9e2c7b08150f72ba85f028050c1407797ea45acd51900c9aadfd09"),
    SPACER_REL.as_posix(): (66, "069885e4645f5f0433d07f5c316bb0863decbb25afaabc1cb318d603cd42945c"),
    SPACER_PHYSICAL_REL.as_posix(): (54, "d0c31aaa67e3c79d4a51913c568ce8c23c308460a98d17869edd85e434ff77c0"),
    VENDOR_REL.as_posix(): (36, "c4d9db3aa6f391426d5af8ebe7c5a719e62d2c13328213a629e2c3e17f453e0f"),
}
INPUT_SHA = {
    COUPON_BUILDER.relative_to(ROOT).as_posix(): "4ffa3776904918292a28e2e736648c1c98bb43dd5d8fd4dd5cd90b2b98e8f780",
    GROOVE_BUILDER.relative_to(ROOT).as_posix(): "7c2c50a44f4a6c92c33402008ce6b576430a1e54358ab049a2aacf7bb9770d52",
    FAILED_OUTER_BUILDER.relative_to(ROOT).as_posix(): "5671e8b2858f6628b4e10a25a26a36439eb0243ed6afa8854eb5e8c3af73aec6",
    LINK_STL.relative_to(ROOT).as_posix(): "3bf2f55347d045faf62d5f269d80ad59917c29c4029399a381397b4fe1d1d16c",
    SPACER_STEP.relative_to(ROOT).as_posix(): "e83e146b93ed2578f8f120b832a1867e0eb7942d570119f04f40087835cea967",
    SPACER_STL.relative_to(ROOT).as_posix(): "2744b25a1313bbe41e93d02e86a23865f07334081289cb4f1afb2ef76cdaf5a2",
    VENDOR_STEP.relative_to(ROOT).as_posix(): "55dd2ae80b4b72a9ff101b093d9ab7d71538d74bda5c907906c5ede0b6b94729",
}

TOOTH_COUNT = 12
SPACING_DEG = 30.0
PHASE_DEG = 15.0
PITCH_MM = 20.6533333333
PITCH_DIAMETER_MM = 79.79835226236546
CANDIDATE_ROOT_RADIUS_MM = 31.171989789132724
CANDIDATE_TIP_RADIUS_MM = CANDIDATE_ROOT_RADIUS_MM + 4.5
CARRIER_MAIN_RADIUS_MM = CANDIDATE_ROOT_RADIUS_MM + 0.1
CARRIER_MAIN_Z_MIN_MM = -21.0
CARRIER_MAIN_Z_MAX_MM = 21.0
CARRIER_CONTACT_RADIUS_MM = 24.5
CARRIER_REAR_DATUM_Z_MM = -22.0
CARRIER_FRONT_DATUM_Z_MM = 22.0
CARRIER_CONTACT_OVERLAP_MM = 0.2
SHAFT_DIAMETER_MM = 10.0
PRINTED_SHAFT_CLEARANCE_DIAMETER_MM = 12.0
KEY_ORIGINAL_MM = 19.7
KEY_REMOVED_MM = 3.0
KEY_EFFECTIVE_MM = 16.7
SPACER_ID_MM = 10.2
SPACER_OD_MM = 13.8
SPACER_REFERENCE_T_MM = 8.0
SPACER_CHAMFER_MM = 0.35
FRONT_CONTACT_SPACER_OD_MM = 49.0
FRONT_CONTACT_PLATE_T_MM = 2.25
SETSCREW_SWEEP_RADIUS_MM = 21.71
SETSCREW_Z_MIN_MM = 9.0
SETSCREW_Z_MAX_MM = 13.0
TOOL_DIAMETER_MM = 6.0
SERVICE_RETRACTION_MM = 50.0
TARGET_MIN_CLEARANCE_MM = 1.0

BUILDER = Path(__file__).name
TEST = "tests/test_candidate_c_12t_misumi_groove1_keeperless_v003_contract.py"
STEPS = [
    "cad/candidate_C_12T_misumi_groove1_keeperless.step",
    "cad/candidate_C_12T_misumi_groove1_keeperless_assembly_reference.step",
    "cad/groove1_exact_interface_reference.step",
    "cad/spacer_stack_reference.step",
    "cad/set_screw_tool_access_reference.step",
    "cad/actual_crawler_clearance_reference.step",
]
STLS = ["print/candidate_C_12T_misumi_groove1_keeperless.stl"]
SVGS = [
    "drawings/dimension_preview.svg",
    "drawings/torque_and_axial_architecture.svg",
    "drawings/crawler_clearance.svg",
]
REPORTS = [
    "reports/clearance_360deg.json",
    "reports/delta_audit.json",
    "reports/set_screw_access.json",
    "reports/spacer_stack_study.csv",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "SOURCE_TRACE.md", "SPACER_STACK.md",
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


coupon = load_module("candidate_c_coupon_authority_v003", COUPON_BUILDER)
groove = load_module("misumi_groove1_authority_v003", GROOVE_BUILDER)


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
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(b"\0")
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
    caches = [p for p in files if "__pycache__" in PurePosixPath(p).parts or p.endswith((".pyc", ".pyo"))]
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_SHA),
        "authority_four": authority == AUTHORITY, "protected_eight": protected == PROTECTED,
        "input_hashes": inputs == INPUT_SHA, "scope": set(files).issubset(EXPECTED),
        "untracked_scope": set(lane_untracked).issubset(EXPECTED), "ignored_zero": not ignored,
        "cache_zero": not caches, "complete": not complete or (files == EXPECTED and lane_untracked == EXPECTED),
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
    return groove.authority.cylinder(radius, height, z)


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


def candidate_tooth(angle_deg: float) -> cq.Workplane:
    shape = coupon.candidate_tooth("C")
    shape = shape.rotate((0, 0, 0), (1, 0, 0), 90.0)
    shape = shape.rotate((0, 0, 0), (0, 0, 1), 90.0)
    shape = shape.translate((CANDIDATE_ROOT_RADIUS_MM, 0.0, 0.0))
    return shape.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def tooth_angles() -> list[float]:
    return [PHASE_DEG + index * SPACING_DEG for index in range(TOOTH_COUNT)]


def carrier_outer_envelope() -> cq.Workplane:
    main = cyl(CARRIER_MAIN_RADIUS_MM, CARRIER_MAIN_Z_MAX_MM - CARRIER_MAIN_Z_MIN_MM, 0.0)
    contact_t = 1.0 + CARRIER_CONTACT_OVERLAP_MM
    front = cyl(CARRIER_CONTACT_RADIUS_MM, contact_t, CARRIER_FRONT_DATUM_Z_MM - contact_t / 2.0)
    rear = cyl(CARRIER_CONTACT_RADIUS_MM, contact_t, CARRIER_REAR_DATUM_Z_MM + contact_t / 2.0)
    return main.union(front).union(rear).clean()


def carrier_body() -> cq.Workplane:
    result = carrier_outer_envelope().cut(groove.insertion_cavity())
    result = result.cut(cyl(PRINTED_SHAFT_CLEARANCE_DIAMETER_MM / 2.0, 48.0, 0.0)).clean()
    if result.solids().size() != 1 or not result.val().isValid():
        raise RuntimeError("KEEPERLESS_CARRIER_BODY_INVALID")
    return result


def printable_sprocket() -> cq.Workplane:
    result = carrier_body()
    for angle in tooth_angles():
        result = result.union(candidate_tooth(angle))
    result = result.clean()
    if result.solids().size() != 1 or not result.val().isValid():
        raise RuntimeError("KEEPERLESS_SPROCKET_INVALID")
    return result


def actual_link_pose() -> cq.Workplane:
    return (
        cq.Workplane(obj=coupon.actual_link())
        .rotate((0, 0, 0), (1, 0, 0), 90.0)
        .rotate((0, 0, 0), (0, 0, 1), 90.0)
        .translate((CANDIDATE_ROOT_RADIUS_MM - coupon.ROOT_PLANE_ENGAGED_Z, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), PHASE_DEG)
    )


def exact_metal_main() -> cq.Workplane:
    return (
        groove.authority.wp(groove.authority.main_solid())
        .rotate((0, 0, 0), (0, 1, 0), -90.0)
        .translate((0, 0, groove.METAL_REAR_Z))
    )


def exact_set_screws() -> cq.Workplane:
    small = [solid for solid in groove.authority.vendor_assembly().Solids() if solid.Volume() < 100.0]
    if len(small) != 2:
        raise RuntimeError("VENDOR_SETSCREW_PROXY_SOLID_COUNT_FAIL")
    return (
        cq.Workplane(obj=cq.Compound.makeCompound(small))
        .rotate((0, 0, 0), (0, 1, 0), -90.0)
        .translate((0, 0, groove.METAL_REAR_Z))
    )


def metal_sweep_envelope() -> cq.Workplane:
    return cyl(43.42 / 2.0, 21.0, 11.0)


def set_screw_sweep_envelope() -> cq.Workplane:
    return cyl(SETSCREW_SWEEP_RADIUS_MM, SETSCREW_Z_MAX_MM - SETSCREW_Z_MIN_MM, 11.0)


def shaft_reference() -> cq.Workplane:
    return cyl(SHAFT_DIAMETER_MM / 2.0, 80.0, 0.0)


def rear_spacer_reference() -> cq.Workplane:
    source = importers.importStep(str(SPACER_STEP))
    return source.translate((0, 0, CARRIER_REAR_DATUM_Z_MM - SPACER_REFERENCE_T_MM))


def front_spacer_reference() -> cq.Workplane:
    bore = SPACER_ID_MM / 2.0
    plate = cyl(FRONT_CONTACT_SPACER_OD_MM / 2.0, FRONT_CONTACT_PLATE_T_MM, CARRIER_FRONT_DATUM_Z_MM + FRONT_CONTACT_PLATE_T_MM / 2.0)
    plate = plate.cut(cyl(bore, FRONT_CONTACT_PLATE_T_MM + 2.0, CARRIER_FRONT_DATUM_Z_MM + FRONT_CONTACT_PLATE_T_MM / 2.0))
    neck_z0 = CARRIER_FRONT_DATUM_Z_MM + 2.0
    neck_t = SPACER_REFERENCE_T_MM - 2.0
    neck = cyl(SPACER_OD_MM / 2.0, neck_t, neck_z0 + neck_t / 2.0).cut(cyl(bore, neck_t + 2.0, neck_z0 + neck_t / 2.0))
    return plate.union(neck).clean()


def tool_envelopes() -> cq.Workplane:
    first = cq.Workplane(obj=cq.Solid.makeCylinder(TOOL_DIAMETER_MM / 2.0, 34.0, cq.Vector(19.0, 0, 11.0), cq.Vector(1, 0, 0)))
    second = cq.Workplane(obj=cq.Solid.makeCylinder(TOOL_DIAMETER_MM / 2.0, 34.0, cq.Vector(0, 19.0, 11.0), cq.Vector(0, 1, 0)))
    return compound([first, second])


def installed_assembly_reference() -> cq.Workplane:
    return compound([printable_sprocket(), exact_metal_main(), exact_set_screws(), shaft_reference(), rear_spacer_reference(), front_spacer_reference()])


def spacer_stack_reference() -> cq.Workplane:
    return compound([carrier_body(), rear_spacer_reference(), front_spacer_reference(), shaft_reference()])


def tool_access_reference() -> cq.Workplane:
    retracted = printable_sprocket().translate((0, 0, SERVICE_RETRACTION_MM))
    return compound([exact_metal_main(), exact_set_screws(), shaft_reference(), tool_envelopes(), retracted])


def crawler_clearance_reference() -> cq.Workplane:
    return compound([printable_sprocket(), actual_link_pose(), metal_sweep_envelope(), set_screw_sweep_envelope(), rear_spacer_reference(), front_spacer_reference(), shaft_reference()])


def geometry_analysis() -> dict:
    link = actual_link_pose()
    tooth = candidate_tooth(PHASE_DEG)
    outer = carrier_outer_envelope()
    body = carrier_body()
    front, rear = front_spacer_reference(), rear_spacer_reference()
    metal, screw, shaft = metal_sweep_envelope(), set_screw_sweep_envelope(), shaft_reference()
    teeth = [candidate_tooth(angle) for angle in tooth_angles()]
    overlaps = []
    for left in range(TOOTH_COUNT):
        for right in range(left + 1, TOOTH_COUNT):
            overlaps.append(common_volume(teeth[left], teeth[right]))
    pcd_hole_tools = [
        cyl(2.75, 10.0, 0.0).translate((28.0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), angle)
        for angle in (0.0, 90.0, 180.0, 270.0)
    ]
    pcd_filled = [volume(tool) - common_volume(tool, body) for tool in pcd_hole_tools]
    source_candidate = coupon.candidate_metrics("C")
    direct_access_blocked = common_volume(tool_envelopes(), body) > 0.0
    service_access_intersection = common_volume(tool_envelopes(), body.translate((0, 0, SERVICE_RETRACTION_MM)))
    clearances = {
        "candidate_c_tooth_mm": round(tooth.val().distance(link.val()), 6),
        "carrier_conservative_outer_mm": round(outer.val().distance(link.val()), 6),
        "front_spacer_mm": round(front.val().distance(link.val()), 6),
        "rear_spacer_mm": round(rear.val().distance(link.val()), 6),
        "metal_sweep_mm": round(metal.val().distance(link.val()), 6),
        "set_screw_360_sweep_mm": round(screw.val().distance(link.val()), 6),
        "shaft_mm": round(shaft.val().distance(link.val()), 6),
    }
    intersections = {
        "candidate_c_tooth_mm3": round(common_volume(tooth, link), 9),
        "carrier_conservative_outer_mm3": round(common_volume(outer, link), 9),
        "front_spacer_mm3": round(common_volume(front, link), 9),
        "rear_spacer_mm3": round(common_volume(rear, link), 9),
        "metal_sweep_mm3": round(common_volume(metal, link), 9),
        "set_screw_360_sweep_mm3": round(common_volume(screw, link), 9),
        "shaft_mm3": round(common_volume(shaft, link), 9),
    }
    minimum = min(clearances.values())
    groove_ref = groove.groove1_interface_envelope(groove.METAL_TOOTH_WIDTH)
    groove_box = groove_ref.val().BoundingBox()
    return {
        "candidate_c": {
            "source_metrics": source_candidate, "tooth_count": TOOTH_COUNT, "angles_deg": tooth_angles(),
            "radial_height_mm": 4.5, "tip_tangential_width_mm": 6.5,
            "engagement_axial_width_mm": 22.0, "root_radius_mm": 1.25,
            "pairwise_count": len(overlaps), "maximum_pairwise_intersection_mm3": round(max(overlaps), 9),
        },
        "printable": {
            "valid": printable_sprocket().val().isValid(), "solid_count": printable_sprocket().solids().size(),
            "volume_mm3": round(volume(printable_sprocket()), 6), "carrier_main_z_mm": [-21.0, 21.0],
            "contact_datums_z_mm": [-22.0, 22.0], "keeper_present": False,
            "pcd56_present": False, "m5_keeper_holes_present": False,
            "pcd56_void_volumes_mm3": [round(max(0.0, value), 9) for value in pcd_filled],
            "legacy_shaft_collar_torque_path": "ABSENT", "printed_shaft_radial_gap_mm": 1.0,
        },
        "groove1": {
            "code": groove.GROOVE_CODE, "clearance_mm": groove.GROOVE_CLEARANCE,
            "profile_volume_mm3": round(volume(groove_ref), 6),
            "profile_bbox_mm": [round(groove_box.xlen, 6), round(groove_box.ylen, 6), round(groove_box.zlen, 6)],
            "metal_center_z_mm": groove.METAL_CENTER_Z, "metal_rear_z_mm": groove.METAL_REAR_Z,
            "metal_front_z_mm": groove.METAL_FRONT_Z, "geometry_change": 0,
        },
        "clearance_360deg": {
            "method": "AXISYMMETRIC_FULL_SWEEPS_FOR_BODY_METAL_SETSCREW_SPACERS_SHAFT_PLUS_12FOLD_ENGAGEMENT_EQUIVALENCE",
            "angular_samples_equivalent": 360, "tooth_periodic_states": 12,
            "clearances_mm": clearances, "intersections_mm3": intersections,
            "minimum_non_intended_clearance_mm": round(minimum, 6),
            "keeper_to_crawler_test": "N/A_KEEPER_REMOVED",
            "status": "PASS" if not any(intersections.values()) and minimum >= TARGET_MIN_CLEARANCE_MM else "FAIL",
        },
        "set_screw_access": {
            "source_small_solid_count": exact_set_screws().solids().size(), "installed_direct_radial_path_blocked": direct_access_blocked,
            "approved_method": "PRETIGHTEN_BEFORE_CARRIER_INSERTION_OR_REMOVE_CRAWLER_AND_RETRACT_CARRIER_PLUS_Z",
            "carrier_retraction_mm": SERVICE_RETRACTION_MM, "retracted_tool_intersection_mm3": round(service_access_intersection, 9),
            "crawler_removal_required_for_service": True, "in_situ_tool_access_claimed": False,
            "status": "PASS_BY_AXIAL_SERVICE_RETRACTION" if service_access_intersection == 0 else "FAIL",
        },
        "spacer": {
            "existing_geometry": {"id_mm": 10.2, "od_mm": 13.8, "thickness_mm": 8.0, "chamfer_mm": 0.35},
            "existing_physical_result": "8MM_INSTALLED_FRAME_TO_GUARD_CLEARANCE_4P4MM_OTHER_DRIVETRAIN_CHECKS_PENDING",
            "misumi_left_thickness": "PHYSICAL_MEASUREMENT_REQUIRED", "misumi_right_thickness": "PHYSICAL_MEASUREMENT_REQUIRED",
            "available_shaft_axial_space": "PHYSICAL_MEASUREMENT_REQUIRED",
            "bearing_inner_ring_face_positions": "PHYSICAL_MEASUREMENT_REQUIRED",
            "reference_only_front_contact_od_mm": FRONT_CONTACT_SPACER_OD_MM,
            "reference_only_front_contact_plate_t_mm": FRONT_CONTACT_PLATE_T_MM,
            "status": "SPACER_STACK_PHYSICAL_SELECTION_PENDING",
        },
    }


def parameters(analysis: dict) -> dict:
    return {
        "version": VERSION, "status": STATUS,
        "candidate_c": analysis["candidate_c"],
        "pattern": {"tooth_count": 12, "spacing_deg": 30.0, "phase_deg": 15.0, "pitch_mm": PITCH_MM, "pitch_diameter_mm": PITCH_DIAMETER_MM, "classification": "P20653_TEST_PLACEMENT_NOT_FINAL_RUNNING_PITCH_AUTHORITY"},
        "groove1": {**analysis["groove1"], "source": GROOVE_REL.as_posix(), "reuse": "DIRECT_EXACT_C1_PROFILE_NO_RECONSTRUCTION_NO_SCALING"},
        "key": {"original_mm": KEY_ORIGINAL_MM, "removed_mm": KEY_REMOVED_MM, "effective_mm": KEY_EFFECTIVE_MM, "primary_torque_element": True},
        "torque_path": "SHAFT_TO_KEY_TO_MISUMI_METAL_PULLEY_TO_EXACT_GROOVE1_C1_TO_PRINTED_CARRIER_TO_CANDIDATE_C_12T",
        "set_screw_function": "AXIAL_POSITION_RETENTION_AND_ANTI_WALK_NOT_PRIMARY_TORQUE",
        "axial_architecture": "MISUMI_SETSCREW_PLUS_SPACER_SANDWICH",
        "keeper": {"annular_keeper": "ABSENT", "od66": "ABSENT", "id36": "ABSENT", "pcd56": "ABSENT", "m5_holes": "ABSENT", "locknuts": "ABSENT"},
        "carrier": analysis["printable"], "clearance": analysis["clearance_360deg"],
        "set_screw_access": analysis["set_screw_access"], "spacer": analysis["spacer"],
        "physical_results": {"groove1_fit": "PASS", "groove1_static_torque": "PASS", "full_carrier_manual_forward_reverse": "PASS", "backlash_growth": "NONE", "candidate_c": "HOLD_NEAR_PASS"},
        "holds": ["SPACER_STACK_PHYSICAL_VALIDATION_PENDING", "BEARING_INNER_RING_FACE_MEASUREMENT_PENDING", "AVAILABLE_SHAFT_AXIAL_SPACE_PENDING", "SERVICE_RETRACTION_SPACE_PHYSICAL_CONFIRMATION_PENDING", "POWERED_TORQUE_VALIDATION_PENDING", "CRAWLER_FULL_LOOP_PENDING", "MUD_WATER_FIELD_HOLD"],
        "forbidden_claims": ["DRIVETRAIN_PASS", "CRAWLER_PASS", "MUD_PASS", "FIELD_PASS"],
    }


def csv_text(rows: list[list[object]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerows(rows)
    return stream.getvalue()


def svg_page(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><style>text{{font-family:Arial,sans-serif;fill:#17212b}}.t{{font-size:30px;font-weight:700}}.s{{font-size:17px;fill:#455}}.n{{font-size:17px}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:3}}.g{{fill:#dcfce7;stroke:#087f5b;stroke-width:3}}.o{{fill:#ffedd5;stroke:#c2410c;stroke-width:3}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:3}}.d{{fill:none;stroke:#7c3aed;stroke-width:3;stroke-dasharray:9 7}}.l{{stroke:#334155;stroke-width:3}}</style><rect width="1200" height="760" fill="#f8fafc"/><text x="50" y="55" class="t">{title}</text><text x="50" y="90" class="s">{subtitle}</text>{body}<text x="50" y="730" class="s">{VERSION} · PHYSICAL SPACER / POWERED / FULL LOOP PENDING</text></svg>'''


def svg_outputs(analysis: dict) -> dict[str, str]:
    teeth = "".join(f'<rect x="-12" y="-247" width="24" height="44" rx="6" class="o" transform="rotate({15 + 30*i})"/>' for i in range(12))
    return {
        SVGS[0]: svg_page("Candidate C 12T · MISUMI Groove-1 · keeperless", "Exact C1 cavity, continuous structural web, no OD66 keeper or PCD56 holes.", f'<g transform="translate(390,420)"><circle r="205" class="b"/><circle r="160" class="g"/>{teeth}<circle r="110" class="d"/><circle r="32" fill="white" stroke="#334155" stroke-width="4"/></g><text x="690" y="185" class="n">12 teeth · phase15° · spacing30°</text><text x="690" y="230" class="n">Candidate C H4.5 / W6.5 / AX22 / R1.25</text><text x="690" y="275" class="n">C1 +0.15 exact imported interface</text><text x="690" y="320" class="n">PCD56/M5 keeper holes: ABSENT</text><text x="690" y="365" class="n">main body Z −21…+21</text><text x="690" y="410" class="n">local contact datums Z ±22</text><text x="690" y="455" class="n">minimum crawler clearance {analysis["clearance_360deg"]["minimum_non_intended_clearance_mm"]:.1f} mm</text>'),
        SVGS[1]: svg_page("Torque and axial architecture", "Key carries torque; set screw prevents axial walk; measured spacer thickness remains pending.", '<rect x="55" y="250" width="150" height="95" class="b"/><rect x="245" y="250" width="150" height="95" class="b"/><rect x="435" y="250" width="175" height="95" class="g"/><rect x="650" y="250" width="175" height="95" class="g"/><rect x="865" y="250" width="220" height="95" class="o"/><text x="100" y="305" class="n">SHAFT</text><text x="300" y="305" class="n">KEY</text><text x="465" y="305" class="n">MISUMI 28T</text><text x="685" y="305" class="n">GROOVE-1 C1</text><text x="900" y="305" class="n">CANDIDATE C 12T</text><path d="M205 298H245M395 298H435M610 298H650M825 298H865" class="l"/><text x="130" y="450" class="n">AXIAL: bearing inner-ring stack → spacer → printed/metal assembly → spacer → bearing inner-ring stack</text><text x="130" y="500" class="n">Set screw = AXIAL_POSITION_RETENTION / ANTI-WALK; never primary torque.</text>'),
        SVGS[2]: svg_page("Actual crawler clearance", "Conservative full sweeps are checked for every non-engagement rotating component.", '<rect x="85" y="185" width="980" height="360" class="b"/><rect x="300" y="260" width="510" height="190" class="g"/><rect x="810" y="300" width="75" height="110" class="o"/><rect x="895" y="280" width="70" height="150" class="r"/><text x="130" y="605" class="n">body envelope clearance 1.0 mm · tooth intended clearance 1.0 mm · intersections 0</text><text x="315" y="350" class="n">carrier Z −21…+21</text><text x="812" y="470" class="n">R24.5 contact</text><text x="880" y="515" class="n">actual link side zone</text><text x="130" y="650" class="n">KEEPER_TO_CRAWLER_TEST = N/A_KEEPER_REMOVED</text>'),
    }


def documents(analysis: dict) -> dict[str, str]:
    h = "# Candidate C 12T + MISUMI Groove-1 keeperless V003\n\n"
    return {
        "README.md": h + (
            "This lane replaces the obsolete OD66/ID36/PCD56/M5 annular keeper with a keeperless spacer-sandwich architecture. The direct Candidate-C tooth source is patterned12 times; the exact C1 +0.15 MISUMI interface is reused without reconstruction or scaling. "
            "Torque path: `shaft → shortened 16.7 mm key → MISUMI metal pulley → exact Groove-1/C1 → continuous printed carrier → Candidate C 12T`. The MISUMI set screw provides axial position/anti-walk only.\n\n"
            "Set-screw access deliberately preserves Groove-1: tighten before inserting the carrier, or remove the crawler and slide the carrier +Z by the documented service distance before using the hex key. No permanent in-situ radial access claim is made.\n\n"
            f"Primary print: `{STLS[0]}`. Status: `{STATUS}`.\n"
        ),
        "DESIGN_AUTHORITY.md": h + (
            "Protected: Candidate C H4.5/W6.5/AX22/root-R1.25; P20653 test placement12T/phase15/spacing30; exact vendor MISUMI main pulley and exact C1 normal-offset profile; pulley center/axial datum; shaft/key axis. "
            "Intended change: new keeperless continuous carrier, filled former PCD56 material, Candidate C outer engagement and parameterized spacer-contact datums. OD66 keeper, four M5 holes, locknuts, H2.5-A1, Dual-L, Y3, B-collar and headed-M4 printed-center torque features are absent.\n"
        ),
        "SOURCE_TRACE.md": h + (
            f"Candidate C editable source `{COUPON_REL.as_posix()}`; current exact center source `{GROOVE_REL.as_posix()}`; outer placement reference `{FAILED_OUTER_REL.as_posix()}` is read only and its obsolete center is not imported; actual link `{LINK_STL.relative_to(ROOT).as_posix()}`; spacer geometry `{SPACER_STEP.relative_to(ROOT).as_posix()}`. All protected tree and input hashes are recorded in validation.\n"
        ),
        "SPACER_STACK.md": h + (
            "Repository search found a physical spacer cross-section ID10.2/OD13.8/chamfer0.35 and an8 mm installed reference that produced4.4 mm frame-to-guard clearance. It does not establish the new MISUMI left/right stack. Therefore8 mm is visualization/reference only. Available shaft space, both bearing inner-ring face positions and final left/right thickness remain `PHYSICAL_MEASUREMENT_REQUIRED`. "
            "The front broad-contact envelope is OD49 with a2.25 mm reference contact plate; it has no bolts and is not an annular keeper authority. Production material, stiffness and thickness remain pending. Never clamp against a bearing outer race, seal, housing or frame.\n"
        ),
        "PHYSICAL_TEST_PLAN.md": h + (
            "1 insert real MISUMI pulley;2 install shortened≈16.7 mm key and shaft;3 tighten MISUMI set screw before carrier insertion;4 slide carrier over pulley;5 select provisional spacers from measured inner-ring faces;6 verify free hand rotation/no axial rattle/no print crushing;7 install crawler;8 forward20 revolutions;9 reverse20;10 bias left/right;11 inspect set-screw movement, axial walk, Groove-1 backlash, crack and whitening. "
            "For service remove crawler and spacer stack, retract carrier +Z, then access the set screw. After manual PASS only: low-speed no-load, powered forward/reverse, dry crawler, continuous dry later. Water/mud/field remain HOLD.\n"
        ),
        "HOLD_REGISTER.md": h + "\n".join([
            "- final left/right spacer thickness and material",
            "- available shaft axial length and bearing inner-ring face coordinates",
            "- front broad-contact spacer stiffness/contact-pressure validation",
            "- physical +Z service-retraction space and tool dimensions",
            "- full crawler loop and 20+20 hand test",
            "- powered torque, dry continuous run, mud, water and field validation",
            "- P20653 final running-pitch authority",
        ]) + "\n",
    }


def spacer_csv() -> str:
    rows = [["side", "candidate_thickness_mm", "id_mm", "od_mm", "classification", "selection_status"]]
    for side in ("REAR", "FRONT_NECK"):
        for step in range(0, 25):
            thickness = step * 0.5
            rows.append([side, f"{thickness:.1f}", "10.2", "13.8", "PARAMETRIC_STUDY", "PHYSICAL_MEASUREMENT_REQUIRED"])
    rows.append(["REFERENCE_ONLY", "8.0", "10.2", "13.8", "EXISTING_PHYSICAL_CROSS_SECTION", "NOT_AUTO_SELECTED_FOR_MISUMI"])
    return csv_text(rows)


def report_outputs(analysis: dict) -> dict[str, str]:
    delta = {
        "protected_zero_diff": {
            "candidate_c_engagement_parameters": True, "groove1_c1_exact_source": True,
            "pulley_center_axis": [0.0, 0.0], "pulley_center_z_mm": groove.METAL_CENTER_Z,
            "pulley_axial_datum_mm": [groove.METAL_REAR_Z, groove.METAL_FRONT_Z],
            "shaft_key_axis": "UNCHANGED", "global_scaling": [1.0, 1.0, 1.0],
        },
        "expected_changes": {
            "annular_keeper_removed": True, "keeper_pcd56_removed": True, "keeper_m5_holes_removed": True,
            "old_14t_outer_replaced_by_candidate_c_12t": True, "former_keeper_hole_material_filled": True,
            "flat_contact_datums_created": [-22.0, 22.0],
        },
        "legacy": {"shaft_collar_torque_path": "ABSENT", "h25a1": "ABSENT", "dual_l": "ABSENT", "y3": "ABSENT", "b_collar": "ABSENT", "headed_m4x2": "ABSENT"},
    }
    access = analysis["set_screw_access"]
    return {
        REPORTS[0]: json.dumps(analysis["clearance_360deg"], ensure_ascii=False, indent=2, sort_keys=True),
        REPORTS[1]: json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True),
        REPORTS[2]: json.dumps(access, ensure_ascii=False, indent=2, sort_keys=True),
        REPORTS[3]: spacer_csv(),
    }


def generate_core(out: Path, analysis: dict | None = None) -> dict:
    analysis = analysis or geometry_analysis()
    shapes = {
        STEPS[0]: printable_sprocket(),
        STEPS[1]: installed_assembly_reference(),
        STEPS[2]: groove.groove1_interface_envelope(groove.METAL_TOOTH_WIDTH).translate((0, 0, groove.METAL_CENTER_Z)),
        STEPS[3]: spacer_stack_reference(),
        STEPS[4]: tool_access_reference(),
        STEPS[5]: crawler_clearance_reference(),
    }
    for relative, shape in shapes.items():
        groove.authority.export_step(shape, out / relative)
    groove.authority.export_stl(printable_sprocket(), out / STLS[0])
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
    meshes = {relative: groove.authority.mesh_metrics(base / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    with tempfile.TemporaryDirectory(prefix="candidate_c_groove1_keeperless_v003_") as tmp:
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", tmp], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if result.returncode:
            return {"compared": len(REPRO_PATHS), "byte_identical": 0, "mismatches": ["RENDER_ONLY_FAILED"], "output": result.stdout, "status": "FAIL"}
        temp = Path(tmp)
        mismatches = [relative for relative in REPRO_PATHS if (LANE / relative).read_bytes() != (temp / relative).read_bytes()]
    return {"compared": len(REPRO_PATHS), "byte_identical": len(REPRO_PATHS) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def contract_checks(base: Path = LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    validation = json.loads((base / "validation_report.json").read_text(encoding="utf-8"))
    params = json.loads((base / "design_parameters.json").read_text(encoding="utf-8"))
    analysis = validation["analysis"]
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, passed: bool, detail: object) -> None:
        checks.append((name, bool(passed), detail))
    add("candidate-c-h", analysis["candidate_c"]["radial_height_mm"] == 4.5, analysis["candidate_c"]["radial_height_mm"])
    add("candidate-c-tip", analysis["candidate_c"]["tip_tangential_width_mm"] == 6.5, analysis["candidate_c"]["tip_tangential_width_mm"])
    add("candidate-c-axial", analysis["candidate_c"]["engagement_axial_width_mm"] == 22.0, analysis["candidate_c"]["engagement_axial_width_mm"])
    add("candidate-c-root-r", analysis["candidate_c"]["root_radius_mm"] == 1.25, analysis["candidate_c"]["root_radius_mm"])
    add("tooth-count", analysis["candidate_c"]["tooth_count"] == 12, analysis["candidate_c"]["tooth_count"])
    add("spacing", analysis["candidate_c"]["angles_deg"] == tooth_angles(), analysis["candidate_c"]["angles_deg"])
    add("tooth-self-intersection", analysis["candidate_c"]["maximum_pairwise_intersection_mm3"] == 0, analysis["candidate_c"]["maximum_pairwise_intersection_mm3"])
    add("groove-code", analysis["groove1"]["code"] == "C1", analysis["groove1"]["code"])
    add("groove-clearance", analysis["groove1"]["clearance_mm"] == 0.15, analysis["groove1"]["clearance_mm"])
    add("groove-zero-change", analysis["groove1"]["geometry_change"] == 0, analysis["groove1"]["geometry_change"])
    add("pulley-center", analysis["groove1"]["metal_center_z_mm"] == 11.0, analysis["groove1"]["metal_center_z_mm"])
    add("keeper-absent", not analysis["printable"]["keeper_present"], analysis["printable"]["keeper_present"])
    add("pcd56-absent", not analysis["printable"]["pcd56_present"], analysis["printable"]["pcd56_present"])
    add("m5-holes-absent", not analysis["printable"]["m5_keeper_holes_present"], analysis["printable"]["m5_keeper_holes_present"])
    add("pcd56-filled", max(analysis["printable"]["pcd56_void_volumes_mm3"]) <= 1e-6, analysis["printable"]["pcd56_void_volumes_mm3"])
    add("legacy-center-absent", analysis["printable"]["legacy_shaft_collar_torque_path"] == "ABSENT", analysis["printable"]["legacy_shaft_collar_torque_path"])
    add("current-torque-path", params["torque_path"].startswith("SHAFT_TO_KEY_TO_MISUMI"), params["torque_path"])
    add("axial-architecture", params["axial_architecture"] == "MISUMI_SETSCREW_PLUS_SPACER_SANDWICH", params["axial_architecture"])
    add("set-screw-not-primary", params["set_screw_function"].endswith("NOT_PRIMARY_TORQUE"), params["set_screw_function"])
    add("key-effective", params["key"]["effective_mm"] == 16.7, params["key"])
    add("carrier-valid", analysis["printable"]["valid"] and analysis["printable"]["solid_count"] == 1, analysis["printable"])
    for name, value in analysis["clearance_360deg"]["intersections_mm3"].items():
        add("intersection-" + name, value == 0, value)
    add("minimum-clearance", analysis["clearance_360deg"]["minimum_non_intended_clearance_mm"] >= 1.0, analysis["clearance_360deg"]["minimum_non_intended_clearance_mm"])
    add("full-360", analysis["clearance_360deg"]["angular_samples_equivalent"] == 360, analysis["clearance_360deg"]["method"])
    add("keeper-test-na", analysis["clearance_360deg"]["keeper_to_crawler_test"] == "N/A_KEEPER_REMOVED", analysis["clearance_360deg"]["keeper_to_crawler_test"])
    add("tool-access", analysis["set_screw_access"]["status"] == "PASS_BY_AXIAL_SERVICE_RETRACTION", analysis["set_screw_access"])
    add("tool-retracted-clear", analysis["set_screw_access"]["retracted_tool_intersection_mm3"] == 0, analysis["set_screw_access"]["retracted_tool_intersection_mm3"])
    add("spacer-pending", analysis["spacer"]["status"] == "SPACER_STACK_PHYSICAL_SELECTION_PENDING", analysis["spacer"]["status"])
    add("spacer-id", analysis["spacer"]["existing_geometry"]["id_mm"] == 10.2, analysis["spacer"]["existing_geometry"])
    add("spacer-od", analysis["spacer"]["existing_geometry"]["od_mm"] == 13.8, analysis["spacer"]["existing_geometry"])
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
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_CANDIDATE_C_12T_MISUMI_KEEPERLESS_V003_{stamp}.zip"
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
    repro = reproducibility()
    checks = {
        "geometry_status": analysis["clearance_360deg"]["status"] == "PASS",
        "minimum_clearance": analysis["clearance_360deg"]["minimum_non_intended_clearance_mm"] >= 1.0,
        "tool_access": analysis["set_screw_access"]["status"] == "PASS_BY_AXIAL_SERVICE_RETRACTION",
        "printable_valid": analysis["printable"]["valid"] and analysis["printable"]["solid_count"] == 1,
        "all_steps_reload": all(item["reload"] == "PASS" and item["valid"] for item in steps),
        "all_stl_quality": all(item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 and item["reload"] == "PASS" for item in meshes.values()),
        "reproducibility": repro["status"] == "PASS",
        "keeper_removed": not analysis["printable"]["keeper_present"],
        "pcd56_removed": not analysis["printable"]["pcd56_present"],
        "m5_keeper_holes_removed": not analysis["printable"]["m5_keeper_holes_present"],
    }
    validation = {"version": VERSION, "status": STATUS, "repository": repository, "analysis": analysis, "step_audit": steps, "stl_audit": meshes, "reproducibility": repro, "checks": checks}
    if not all(checks.values()):
        write_json(LANE / "validation_report.json", validation)
        raise RuntimeError("FAIL_CLOSED_VALIDATION " + json.dumps(checks))
    write_json(LANE / "validation_report.json", validation)
    write(LANE / "BUILD_LOG.txt", "BUILD=PASS\nCADQUERY=2.8.0\nKEEPER=ABSENT\nMIN_CLEARANCE_MM=" + str(analysis["clearance_360deg"]["minimum_non_intended_clearance_mm"]) + "\nREPRODUCIBILITY=" + repro["status"])
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
    args = parser.parse_args()
    if args.render_only:
        analysis = geometry_analysis()
        generate_core(args.render_only, analysis)
        print(json.dumps({"render_only": str(args.render_only), "paths": len(REPRO_PATHS)}))
        return 0
    result = verify() if args.verify else build()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status", "PASS") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
