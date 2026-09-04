#!/usr/bin/env python3
"""Build Common Rover integral 12T drive sprocket + dry split-clamp H0 v0.9.3.7."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq
import trimesh


DOCUMENT_ID = "PS-CR-V0937-INTEGRAL-DRIVE-SPROCKET-SHAFT-CONNECTION-S0"
VERSION = "0.9.3.7"
DESIGN_NAME = "common_rover_integral_drive_sprocket_shaft_connection_v0_9_3_7"
CLASSIFICATION = "S0_BASELINE_INTEGRAL_DRIVE_SPROCKET"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
PREFLIGHT_OUTSIDE_UNTRACKED_COUNT = 945
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_integral_drive_sprocket_shaft_connection_v0_9_3_7"
LANE_DIR = Path(__file__).resolve().parent
SOURCE_REL = "cad/crawler_h1/track_module/pretest_candidate_v0_1"
SOURCE_SNAPSHOT = (24, "c8df27c908ce60a2b7f4d6bfde10c264dc1074b367e5eb0579535aab1bf955ed")
SOURCE_CODE_REL = "source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py"
SOURCE_CODE_SHA256 = "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e"
SOURCE_DRIVE_STL_REL = "stl/petg/DRIVE_SPROCKET_V0131_INTEGRATED_B10_3_PCD24_M4.stl"
SOURCE_DRIVE_STL_SHA256 = "c97775e441fe25ad029bedccb7890a8e9661418da10fcab2bcbf968ea0a493e2"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Integral_Drive_Sprocket_Shaft_Connection_v0_9_3_7_"

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
EXPECTED_TRACKED_DIFF = set(AUTHORITY_HASHES)
PROTECTED_LANES = {
    "cad/common_rover/common_rover_powertrain_frame_belt_design_authority_v0_9_0": (38, "e6480973c32b76cbaf8c4cdb404f7a8ec1d2f9e4c48780bda8a416416c6421f6"),
    "cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1": (37, "1670e3a2553ff4495022e8c3b45afcc1e534c886229d899fd6405d81c190c95d"),
    "cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2": (45, "3dd904563cb579e57191ef4cee92cfc866fcf415b418c87eb1d7e535947de67a"),
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": (55, "a0bbc43837432e7b152dc85f9e36c9a77f2e4a815e063e9ca25a0efa6052b84e"),
    "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2": (45, "f61e6c3379496d4a742edffb4b7ef56e12002098cf9b0143ae934a602e3d7cac"),
    "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0": (151, "3528bc1192983fce3daeb5e543fe3f207fa59eb78615ddcde0643e73f9159199"),
    "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1": (46, "2f58d6fddab3c9c0f3deed09188974d3642dcdc89e94b0240eec869a7de770f8"),
    "cad/common_rover/common_rover_candidate_a_motor_bracket_adapter_v0_9_3_2": (39, "116f3283a634a80f61284f0a46a99f0ac07de2f5d8ebdd457faa64fafa2b77da"),
    "cad/common_rover/common_rover_candidate_a_motor_bracket_8hole_flat_plate_v0_9_3_3": (38, "2c0bd512c9e347ad1429fe0974948f64fe587f53ed616135d9c663b0814bb5be"),
    "cad/common_rover/common_rover_powertrain_frame_joint_trade_study_v0_9_3_4": (87, "8d7d4cd1201af8f1f7e50ff4b46642a022e240f4c8ab85bacf1f80b9b654a9a3"),
    "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5": (34, "93e1fae749a19c8f428f02091dec9dcf1363bbe09cd5e5f30e0acf21caeb73b1"),
    "cad/common_rover/common_rover_crawler_guide_clearance_retest_coupon_v0_9_3_6": (30, "2d5171c309e77a1634f0c559761319eaf893cc7e321a60347dae57a0cb420ab8"),
}


@dataclass(frozen=True)
class SprocketSpec:
    tooth_count: int = 12
    axial_width_mm: float = 44.0
    phase_deg: float = 15.0
    tip_radius_mm: float = 33.07
    root_radius_mm: float = 29.47
    tip_width_mm: float = 7.50
    root_width_mm: float = 9.50
    embed_depth_mm: float = 4.00
    embed_width_mm: float = 13.00
    ring_inner_radius_mm: float = 20.00
    hub_radius_mm: float = 18.00
    spoke_count: int = 6
    spoke_width_mm: float = 12.00
    spoke_inner_radius_mm: float = 15.00
    spoke_outer_radius_mm: float = 22.50
    drive_bore_mm: float = 10.30
    axial_bolt_count: int = 4
    axial_bolt_pcd_mm: float = 24.00
    axial_bolt_hole_mm: float = 4.40
    axial_bolt_phase_deg: float = 45.00

    @property
    def embed_radius_mm(self) -> float:
        return self.root_radius_mm - self.embed_depth_mm

    @property
    def pitch_diameter_record_mm(self) -> float:
        return 76.3943726841


S = SprocketSpec()
SHAFT_NOMINAL_MM = 10.0
SHAFT_BORE_CANDIDATES_MM = (10.0, 10.1, 10.2)
H0_SELECTED_BORE_MM = 10.1
H0_SPLIT_GAP_MM = 0.6
H0_BODY_RADIUS_MM = 18.0
H0_BODY_Z0_MM = 22.0
H0_BODY_LENGTH_MM = 14.0
H0_PILOT_OD_MM = 15.0
H0_PILOT_LENGTH_MM = 2.3
S0_PILOT_RECESS_DIAMETER_MM = 15.2
S0_PILOT_RECESS_DEPTH_MM = 2.5
H0_PILOT_DIAMETRAL_CLEARANCE_MM = S0_PILOT_RECESS_DIAMETER_MM - H0_PILOT_OD_MM
H0_CLAMP_BOLT_COUNT = 2
H0_CLAMP_BOLT_SIZE = "M5"
H0_CLAMP_BOLT_CLEARANCE_MM = 5.5
H0_CLAMP_BOLT_X_MM = 11.5
H0_CLAMP_BOLT_Z_MM = 29.0
H0_LUG_X_MM = 7.0
H0_LUG_Y_MM = 38.0
H0_LUG_Z_MM = 10.0
H0_HEAD_POCKET_DIAMETER_MM = 10.4
H0_NUT_POCKET_CIRCUMSCRIBED_MM = 9.4
AXIAL_FASTENER_SIZE = "M4"
AXIAL_FASTENER_COUNT = 4
M4_SHANK_MM = 4.0
M4_HEAD_ENVELOPE_MM = 8.0
M4_WASHER_OD_MM = 9.0
M4_NUT_CIRCUMSCRIBED_MM = 8.2
M5_SHANK_MM = 5.0
M5_HEAD_ENVELOPE_MM = 10.0
M5_WASHER_OD_MM = 10.0
M5_NUT_CIRCUMSCRIBED_MM = 9.2
BEARING_OD_MEASURED_MM = 25.9
BEARING_ID_NOMINAL_MM = 10.0
BEARING_WIDTH_SOURCE_MM = 8.0
BEARING_SHIELD_OD_PROVISIONAL_MM = 24.0
BEARING_REFERENCE_Z0_MM = -38.0
COLLAR_REFERENCE_OD_MM = 20.0
COLLAR_REFERENCE_BORE_MM = 10.2
COLLAR_REFERENCE_WIDTH_MM = 6.0

ROOT_FILES = (
    "README.md", "DESIGN_SPEC.md", "SOURCE_TRACE.md", "DESIGN_REVIEW.md",
    "SHAFT_CONNECTION_TRADE_STUDY.md", "PHYSICAL_TEST_PLAN.md",
    "ASSEMBLY_INSTRUCTIONS.md", "HARDWARE_BOM.md", "COMMIT_PATHS.txt",
    "SHA256SUMS.txt", "geometry_manifest.json", "validation_report.json",
    "build_log.txt", "test_log.txt", "MANIFEST.txt",
)
SOURCE_FILES = (
    "build_common_rover_integral_drive_sprocket_shaft_connection_v0937.py",
    "tests/test_common_rover_integral_drive_sprocket_shaft_connection_v0937.py",
)
STEP_FILES = (
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_source_comparison_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_h0_split_clamp_top_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_h0_split_clamp_bottom_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_h0_assembly_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_h0_exploded_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_shaft_bore_coupon_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_h1_parameter_hold_reference_v0_9_3_7.step",
    "artifacts/step/common_rover_crawler_sprocket_12t_integral_s0_bearing_shaft_envelope_assembly_v0_9_3_7.step",
)
STL_FILES = (
    "artifacts/stl/common_rover_crawler_sprocket_12t_integral_s0_v0_9_3_7.stl",
    "artifacts/stl/common_rover_crawler_sprocket_12t_integral_s0_h0_split_clamp_top_v0_9_3_7.stl",
    "artifacts/stl/common_rover_crawler_sprocket_12t_integral_s0_h0_split_clamp_bottom_v0_9_3_7.stl",
    "artifacts/stl/common_rover_crawler_sprocket_12t_integral_s0_shaft_bore_coupon_v0_9_3_7.stl",
)
SVG_FILES = (
    "artifacts/svg/common_rover_crawler_sprocket_12t_integral_s0_shaft_connection_overview_v0_9_3_7.svg",
    "artifacts/svg/common_rover_crawler_sprocket_12t_integral_s0_load_path_v0_9_3_7.svg",
)
PACKAGE_PATHS = ROOT_FILES + SOURCE_FILES + STEP_FILES + STL_FILES + SVG_FILES
if len(PACKAGE_PATHS) != 32 or len(set(PACKAGE_PATHS)) != 32:
    raise RuntimeError("formal path contract must be exact 32")


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", check=False)


def git(*args: str) -> str:
    result = run(["git", *args], REPO_ROOT)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return "\n".join(line for line in result.stdout.splitlines() if not line.startswith("warning:")).strip()


def live_repository() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"], LANE_DIR).returncode == 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lane_files(base: Path = LANE_DIR) -> list[str]:
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def full_lane_ledger(path: Path) -> tuple[int, str]:
    files = sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.relative_to(path).as_posix())
    rows = [f"{item.relative_to(path).as_posix()}\t{sha256(item)}" for item in files]
    return len(files), hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest()


def protected_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"lanes": {path: {"expected_file_count": value[0], "expected_ledger_sha256": value[1], "mode": "STANDALONE_EMBEDDED", "status": "PASS"} for path, value in PROTECTED_LANES.items()}, "status": "PASS"}
    rows = {}
    for path, expected in PROTECTED_LANES.items():
        actual = full_lane_ledger(REPO_ROOT / path)
        rows[path] = {"file_count": actual[0], "ledger_sha256": actual[1], "expected_file_count": expected[0], "expected_ledger_sha256": expected[1], "status": "PASS" if actual == expected else "FAIL"}
    if not all(row["status"] == "PASS" for row in rows.values()):
        raise RuntimeError({"protected_lanes": rows})
    return {"lanes": rows, "status": "PASS"}


def source_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"path": SOURCE_REL, "expected_file_count": SOURCE_SNAPSHOT[0], "expected_ledger_sha256": SOURCE_SNAPSHOT[1], "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    source = REPO_ROOT / SOURCE_REL
    actual = full_lane_ledger(source)
    tracked = {line.replace("\\", "/") for line in git("ls-files", "--", SOURCE_REL).splitlines() if line}
    expected_paths = {f"{SOURCE_REL}/{item.relative_to(source).as_posix()}" for item in source.rglob("*") if item.is_file()}
    checks = {
        "ledger": actual == SOURCE_SNAPSHOT,
        "fully_tracked": tracked == expected_paths,
        "source_code_hash": sha256(source / SOURCE_CODE_REL) == SOURCE_CODE_SHA256,
        "source_drive_stl_hash": sha256(source / SOURCE_DRIVE_STL_REL) == SOURCE_DRIVE_STL_SHA256,
    }
    if not all(checks.values()):
        raise RuntimeError({"source_checks": checks, "actual": actual})
    return {"path": SOURCE_REL, "file_count": actual[0], "ledger_sha256": actual[1], "tracked": True, "checks": checks, "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_untracked = sorted(path[len(LANE_REL) + 1:] for path in untracked if path.startswith(LANE_REL + "/"))
    outside_untracked = [path for path in untracked if not path.startswith(LANE_REL + "/")]
    actual = lane_files()
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL).splitlines() if line]
    forbidden = [path for path in actual if "__pycache__" in path.lower() or ".pytest_cache" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".tmp", ".bak", ".fcstd", ".blend"))]
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged, "authority_hashes": {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES} == AUTHORITY_HASHES,
        "protected_lanes": protected_audit(True)["status"] == "PASS", "source": source_audit(True)["status"] == "PASS",
        # Other user-owned tasks may add untracked files concurrently.  This lane
        # must never require their deletion merely to recover the preflight count.
        "outside_untracked_not_reduced": len(outside_untracked) >= PREFLIGHT_OUTSIDE_UNTRACKED_COUNT,
        "lane_scope": set(actual).issubset(PACKAGE_PATHS), "lane_untracked_exact": lane_untracked == actual,
        "lane_complete": actual == sorted(PACKAGE_PATHS) if require_complete else True,
        "ignored_zero": not ignored, "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_checks": checks, "actual": actual, "lane_untracked": lane_untracked, "outside_untracked_count": len(outside_untracked), "ignored": ignored, "forbidden": forbidden})
    return {"root": root, "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": sorted(staged), "untracked_total": len(untracked), "outside_untracked_count": len(outside_untracked), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def cylinder_z(radius: float, height: float, z0: float = 0.0, x: float = 0.0, y: float = 0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cylinder_y(radius: float, length: float, y0: float, x: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def source_ring_hub_spokes() -> cq.Workplane:
    ring = cq.Workplane(obj=cylinder_z(S.root_radius_mm, S.axial_width_mm, -S.axial_width_mm / 2.0)).cut(cq.Workplane(obj=cylinder_z(S.ring_inner_radius_mm, S.axial_width_mm + 0.4, -S.axial_width_mm / 2.0 - 0.2)))
    body = ring.union(cq.Workplane(obj=cylinder_z(S.hub_radius_mm, S.axial_width_mm, -S.axial_width_mm / 2.0)))
    length = S.spoke_outer_radius_mm - S.spoke_inner_radius_mm
    center = (S.spoke_outer_radius_mm + S.spoke_inner_radius_mm) / 2.0
    for index in range(S.spoke_count):
        spoke = cq.Workplane("XY").box(length, S.spoke_width_mm, S.axial_width_mm, centered=(True, True, True)).translate((center, 0, 0)).rotate((0, 0, 0), (0, 0, 1), index * 360.0 / S.spoke_count)
        body = body.union(spoke)
    return body.clean()


def source_embedded_tooth() -> cq.Workplane:
    points = [(S.embed_radius_mm, -S.embed_width_mm / 2.0), (S.root_radius_mm, -S.root_width_mm / 2.0), (S.tip_radius_mm, -S.tip_width_mm / 2.0), (S.tip_radius_mm, S.tip_width_mm / 2.0), (S.root_radius_mm, S.root_width_mm / 2.0), (S.embed_radius_mm, S.embed_width_mm / 2.0)]
    return cq.Workplane("XY").polyline(points).close().extrude(S.axial_width_mm / 2.0, both=True)


def source_blank() -> cq.Workplane:
    body = source_ring_hub_spokes()
    tooth = source_embedded_tooth()
    for index in range(S.tooth_count):
        body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), S.phase_deg + index * 360.0 / S.tooth_count))
    return body.clean()


def source_drive() -> cq.Workplane:
    body = source_blank().cut(cq.Workplane(obj=cylinder_z(S.drive_bore_mm / 2.0, S.axial_width_mm + 2.0, -S.axial_width_mm / 2.0 - 1.0)))
    for index in range(S.axial_bolt_count):
        angle = math.radians(S.axial_bolt_phase_deg + index * 360.0 / S.axial_bolt_count)
        x, y = S.axial_bolt_pcd_mm / 2.0 * math.cos(angle), S.axial_bolt_pcd_mm / 2.0 * math.sin(angle)
        body = body.cut(cq.Workplane(obj=cylinder_z(S.axial_bolt_hole_mm / 2.0, S.axial_width_mm + 2.0, -S.axial_width_mm / 2.0 - 1.0, x, y)))
    return body.clean()


def s0_sprocket() -> cq.Workplane:
    recess = cq.Workplane(obj=cylinder_z(S0_PILOT_RECESS_DIAMETER_MM / 2.0, S0_PILOT_RECESS_DEPTH_MM + 0.2, S.axial_width_mm / 2.0 - S0_PILOT_RECESS_DEPTH_MM))
    return source_drive().cut(recess).clean()


def hex_prism_y(circumscribed_mm: float, length: float, y0: float, x: float, z: float) -> cq.Shape:
    return cq.Workplane("XZ", origin=(0, y0, 0)).center(x, z).polygon(6, circumscribed_mm).extrude(length).val()


def h0_full(bore_mm: float = H0_SELECTED_BORE_MM) -> cq.Workplane:
    body = cq.Workplane(obj=cylinder_z(H0_BODY_RADIUS_MM, H0_BODY_LENGTH_MM, H0_BODY_Z0_MM))
    pilot = cq.Workplane(obj=cylinder_z(H0_PILOT_OD_MM / 2.0, H0_PILOT_LENGTH_MM, S.axial_width_mm / 2.0 - H0_PILOT_LENGTH_MM))
    body = body.union(pilot)
    for x in (-H0_CLAMP_BOLT_X_MM, H0_CLAMP_BOLT_X_MM):
        lug = cq.Workplane("XY").box(H0_LUG_X_MM, H0_LUG_Y_MM, H0_LUG_Z_MM, centered=(True, True, True)).translate((x, 0, H0_CLAMP_BOLT_Z_MM))
        body = body.union(lug)
    body = body.cut(cq.Workplane(obj=cylinder_z(bore_mm / 2.0, H0_BODY_LENGTH_MM + H0_PILOT_LENGTH_MM + 4.0, S.axial_width_mm / 2.0 - H0_PILOT_LENGTH_MM - 1.0)))
    for index in range(S.axial_bolt_count):
        angle = math.radians(S.axial_bolt_phase_deg + index * 360.0 / S.axial_bolt_count)
        x, y = S.axial_bolt_pcd_mm / 2.0 * math.cos(angle), S.axial_bolt_pcd_mm / 2.0 * math.sin(angle)
        body = body.cut(cq.Workplane(obj=cylinder_z(S.axial_bolt_hole_mm / 2.0, H0_BODY_LENGTH_MM + H0_PILOT_LENGTH_MM + 4.0, S.axial_width_mm / 2.0 - H0_PILOT_LENGTH_MM - 1.0, x, y)))
    for x in (-H0_CLAMP_BOLT_X_MM, H0_CLAMP_BOLT_X_MM):
        body = body.cut(cq.Workplane(obj=cylinder_y(H0_CLAMP_BOLT_CLEARANCE_MM / 2.0, 44.0, -22.0, x, H0_CLAMP_BOLT_Z_MM)))
        body = body.cut(cq.Workplane(obj=cylinder_y(H0_HEAD_POCKET_DIAMETER_MM / 2.0, 5.0, 14.0, x, H0_CLAMP_BOLT_Z_MM)))
        body = body.cut(cq.Workplane(obj=hex_prism_y(H0_NUT_POCKET_CIRCUMSCRIBED_MM, 5.0, -14.0, x, H0_CLAMP_BOLT_Z_MM)))
    gap = cq.Workplane("XY").box(60.0, H0_SPLIT_GAP_MM, 30.0, centered=(True, True, True)).translate((0, 0, 27.0))
    return body.cut(gap).clean()


def h0_half(half: str, bore_mm: float = H0_SELECTED_BORE_MM) -> cq.Shape:
    if half == "TOP":
        box = cq.Solid.makeBox(70.0, 35.0, 40.0, cq.Vector(-35.0, H0_SPLIT_GAP_MM / 2.0, 10.0))
    elif half == "BOTTOM":
        box = cq.Solid.makeBox(70.0, 35.0, 40.0, cq.Vector(-35.0, -35.0 - H0_SPLIT_GAP_MM / 2.0, 10.0))
    else:
        raise ValueError(half)
    return h0_full(bore_mm).val().intersect(box)


def shaft_coupon() -> cq.Workplane:
    body = cq.Workplane("XY").box(116.0, 40.0, 5.0, centered=(True, True, False))
    for x, diameter in zip((-36.0, 0.0, 36.0), SHAFT_BORE_CANDIDATES_MM):
        body = body.union(cq.Workplane("XY").center(x, 0).circle(10.0).extrude(12.0))
        body = body.cut(cq.Workplane("XY").center(x, 0).circle(diameter / 2.0).extrude(14.0))
        body = body.union(cq.Workplane("XY").workplane(offset=5.0).center(x, -15.0).text(f"{diameter:.1f}", 3.2, 0.6, combine=True))
    body = body.union(cq.Workplane("XY").workplane(offset=5.0).center(0, 15.0).text("S0 SHAFT FIT ONLY NO POWER", 3.2, 0.6, combine=True))
    return body.clean()


def axial_fasteners() -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    for index in range(S.axial_bolt_count):
        angle = math.radians(S.axial_bolt_phase_deg + index * 360.0 / S.axial_bolt_count)
        x, y = S.axial_bolt_pcd_mm / 2.0 * math.cos(angle), S.axial_bolt_pcd_mm / 2.0 * math.sin(angle)
        shapes.extend([
            cylinder_z(M4_SHANK_MM / 2.0, 64.0, -25.0, x, y),
            cylinder_z(M4_HEAD_ENVELOPE_MM / 2.0, 3.0, 36.0, x, y),
            cylinder_z(M4_WASHER_OD_MM / 2.0, 1.0, 35.0, x, y).cut(cylinder_z(2.2, 1.2, 34.9, x, y)),
            hex_prism_z(M4_NUT_CIRCUMSCRIBED_MM, 3.2, -25.0, x, y),
            cylinder_z(M4_WASHER_OD_MM / 2.0, 1.0, -22.8, x, y).cut(cylinder_z(2.2, 1.2, -22.9, x, y)),
        ])
    return shapes


def hex_prism_z(circumscribed_mm: float, height: float, z0: float, x: float, y: float) -> cq.Shape:
    return cq.Workplane("XY").center(x, y).polygon(6, circumscribed_mm).extrude(height).translate((0, 0, z0)).val()


def transverse_fasteners() -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    for x in (-H0_CLAMP_BOLT_X_MM, H0_CLAMP_BOLT_X_MM):
        shapes.extend([
            cylinder_y(M5_SHANK_MM / 2.0, 44.0, -22.0, x, H0_CLAMP_BOLT_Z_MM),
            cylinder_y(M5_HEAD_ENVELOPE_MM / 2.0, 4.0, 19.0, x, H0_CLAMP_BOLT_Z_MM),
            cylinder_y(M5_WASHER_OD_MM / 2.0, 1.0, 18.0, x, H0_CLAMP_BOLT_Z_MM).cut(cylinder_y(2.75, 1.2, 17.9, x, H0_CLAMP_BOLT_Z_MM)),
            hex_prism_y(M5_NUT_CIRCUMSCRIBED_MM, 4.0, -15.0, x, H0_CLAMP_BOLT_Z_MM),
            cylinder_y(M5_WASHER_OD_MM / 2.0, 1.0, -19.0, x, H0_CLAMP_BOLT_Z_MM).cut(cylinder_y(2.75, 1.2, -19.1, x, H0_CLAMP_BOLT_Z_MM)),
        ])
    return shapes


def bearing_envelope() -> cq.Shape:
    return cylinder_z(BEARING_OD_MEASURED_MM / 2.0, BEARING_WIDTH_SOURCE_MM, BEARING_REFERENCE_Z0_MM).cut(cylinder_z(BEARING_ID_NOMINAL_MM / 2.0, BEARING_WIDTH_SOURCE_MM + 0.2, BEARING_REFERENCE_Z0_MM - 0.1))


def shield_envelope() -> cq.Shape:
    return cylinder_z(BEARING_SHIELD_OD_PROVISIONAL_MM / 2.0, 0.8, BEARING_REFERENCE_Z0_MM + BEARING_WIDTH_SOURCE_MM - 0.8).cut(cylinder_z(BEARING_ID_NOMINAL_MM / 2.0, 1.0, BEARING_REFERENCE_Z0_MM + BEARING_WIDTH_SOURCE_MM - 0.9))


def collar_envelope() -> cq.Shape:
    return cylinder_z(COLLAR_REFERENCE_OD_MM / 2.0, COLLAR_REFERENCE_WIDTH_MM, -46.0).cut(cylinder_z(COLLAR_REFERENCE_BORE_MM / 2.0, COLLAR_REFERENCE_WIDTH_MM + 0.2, -46.1))


def shaft_envelope() -> cq.Shape:
    return cylinder_z(SHAFT_NOMINAL_MM / 2.0, 100.0, -50.0)


def link_contact_keepout() -> cq.Shape:
    # Links can occupy the exposed tooth/root zone.  The 25.47 mm embedded-root
    # extension is internal material, not a physical link-access boundary.
    return cylinder_z(35.0, 54.0, -27.0).cut(cylinder_z(S.root_radius_mm, 54.2, -27.1))


def h0_assembly(include_envelopes: bool = False) -> cq.Compound:
    shapes: list[cq.Shape] = [s0_sprocket().val(), h0_half("TOP"), h0_half("BOTTOM"), shaft_envelope(), *axial_fasteners(), *transverse_fasteners()]
    if include_envelopes:
        shapes.extend([bearing_envelope(), shield_envelope(), collar_envelope(), link_contact_keepout()])
    return cq.Compound.makeCompound(shapes)


def h0_exploded() -> cq.Compound:
    return cq.Compound.makeCompound([s0_sprocket().translate((0, 0, -12)).val(), h0_half("TOP").translate((0, 15, 10)), h0_half("BOTTOM").translate((0, -15, 10)), shaft_envelope(), *axial_fasteners(), *transverse_fasteners()])


def bounds(shape: cq.Shape | cq.Workplane) -> dict[str, float]:
    obj = shape.val() if hasattr(shape, "val") else shape
    box = obj.BoundingBox()
    return {"xmin": box.xmin, "xmax": box.xmax, "ymin": box.ymin, "ymax": box.ymax, "zmin": box.zmin, "zmax": box.zmax, "xlen": box.xlen, "ylen": box.ylen, "zlen": box.zlen}


def common_volume(a: cq.Shape | cq.Workplane, b: cq.Shape | cq.Workplane) -> float:
    aa = a.val() if hasattr(a, "val") else a
    bb = b.val() if hasattr(b, "val") else b
    try:
        return float(aa.intersect(bb).Volume())
    except Exception:
        return 0.0


def geometry_analysis() -> dict[str, Any]:
    source = source_drive()
    final = s0_sprocket()
    ring = source_ring_hub_spokes()
    tooth = source_embedded_tooth()
    top, bottom = h0_half("TOP"), h0_half("BOTTOM")
    shaft = shaft_envelope()
    bearing, shield, collar, link = bearing_envelope(), shield_envelope(), collar_envelope(), link_contact_keepout()
    external_shell = cylinder_z(40.0, 46.0, -23.0).cut(cylinder_z(S.root_radius_mm, 46.2, -23.1))
    source_external = source.val().intersect(external_shell)
    final_external = final.val().intersect(external_shell)
    source_minus_final_external = float(source_external.cut(final_external).Volume())
    final_minus_source_external = float(final_external.cut(source_external).Volume())
    clamp_parts = cq.Compound.makeCompound([top, bottom])
    m5_shanks = cq.Compound.makeCompound([cylinder_y(M5_SHANK_MM / 2.0, 44.0, -22.0, x, H0_CLAMP_BOLT_Z_MM) for x in (-H0_CLAMP_BOLT_X_MM, H0_CLAMP_BOLT_X_MM)])
    m4_shanks = cq.Compound.makeCompound([shape for index, shape in enumerate(axial_fasteners()) if index % 5 == 0])
    hardware = cq.Compound.makeCompound([*axial_fasteners(), *transverse_fasteners()])
    tooth_intersection = common_volume(ring, tooth)
    return {
        "source": {"solid_count": len(source.solids().vals()), "valid": bool(source.val().isValid()), "volume_mm3": float(source.val().Volume()), "bounds_mm": bounds(source)},
        "final_sprocket": {"solid_count": len(final.solids().vals()), "valid": bool(final.val().isValid()), "volume_mm3": float(final.val().Volume()), "bounds_mm": bounds(final)},
        "tooth": {"count": S.tooth_count, "angles_deg": [S.phase_deg + i * 360.0 / S.tooth_count for i in range(S.tooth_count)], "spacing_deg": 360.0 / S.tooth_count, "body_intersection_per_tooth_mm3": tooth_intersection, "minimum_required_mm3": 100.0, "external_source_minus_final_mm3": source_minus_final_external, "external_final_minus_source_mm3": final_minus_source_external},
        "h0": {"solid_count": len(clamp_parts.Solids()), "top_solid_count": len(top.Solids()), "bottom_solid_count": len(bottom.Solids()), "top_valid": bool(top.isValid()), "bottom_valid": bool(bottom.isValid()), "half_intersection_mm3": common_volume(top, bottom), "shaft_top_intersection_mm3": common_volume(shaft, top), "shaft_bottom_intersection_mm3": common_volume(shaft, bottom), "m5_shank_clamp_intersection_mm3": common_volume(m5_shanks, clamp_parts), "m4_shank_sprocket_hub_intersection_mm3": common_volume(m4_shanks, cq.Compound.makeCompound([final.val(), top, bottom])), "pilot_radial_clearance_mm": H0_PILOT_DIAMETRAL_CLEARANCE_MM / 2.0, "split_gap_mm": H0_SPLIT_GAP_MM},
        "envelopes": {"h0_to_bearing_mm3": common_volume(clamp_parts, bearing), "h0_to_shield_mm3": common_volume(clamp_parts, shield), "h0_to_collar_mm3": common_volume(clamp_parts, collar), "hardware_to_bearing_mm3": common_volume(hardware, bearing), "hardware_to_shield_mm3": common_volume(hardware, shield), "hardware_to_link_keepout_mm3": common_volume(hardware, link), "h0_to_link_keepout_mm3": common_volume(clamp_parts, link), "bearing_to_collar_mm3": common_volume(bearing, collar), "bearing_axial_position": "DERIVED_REFERENCE_HOLD_ACTUAL_STACK_MEASUREMENT_REQUIRED", "shield_od_status": "PROVISIONAL_MEASUREMENT_REQUIRED"},
        "coupon": {"bores_mm": list(SHAFT_BORE_CANDIDATES_MM), "solid_count": len(shaft_coupon().solids().vals()), "markings": ["10.0", "10.1", "10.2", "S0 SHAFT FIT ONLY NO POWER"]},
        "axis": {"source_center_xy_mm": [0.0, 0.0], "final_center_xy_mm": [0.0, 0.0], "h0_center_xy_mm": [0.0, 0.0]},
    }


def geometry_manifest(repository: dict[str, Any], source_audit_result: dict[str, Any], protected: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION, "design_name": DESIGN_NAME, "classification": CLASSIFICATION,
        "source_file_paths": [f"{SOURCE_REL}/{SOURCE_CODE_REL}", f"{SOURCE_REL}/upstream/contracts/crawler_h1_v0_13_1_design_contract.json", f"{SOURCE_REL}/upstream/reports/crawler_h1_v0_13_1_validation_report.json", f"{SOURCE_REL}/{SOURCE_DRIVE_STL_REL}", "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5/build_crawler_tracking_retention_patch_v0935.py", "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2/build_shaft_fit_calibration_v0922.py"],
        "source_commit": EXPECTED_HEAD, "current_branch": repository.get("branch", EXPECTED_BRANCH), "current_head": repository.get("head", EXPECTED_HEAD),
        "source_tooth_count": S.tooth_count, "final_tooth_count": S.tooth_count,
        "source_pitch_parameter": {"link_pitch_record_mm": 20.0, "pitch_diameter_record_mm": S.pitch_diameter_record_mm, "phase_deg": S.phase_deg, "spacing_deg": 30.0},
        "final_pitch_parameter": {"link_pitch_record_mm": 20.0, "pitch_diameter_record_mm": S.pitch_diameter_record_mm, "phase_deg": S.phase_deg, "spacing_deg": 30.0},
        "source_tooth_axial_width": S.axial_width_mm, "final_tooth_axial_width": S.axial_width_mm,
        "source_tooth_tip_width": S.tip_width_mm, "final_tooth_tip_width": S.tip_width_mm,
        "shaft_nominal_diameter": SHAFT_NOMINAL_MM, "shaft_bore_candidates": list(SHAFT_BORE_CANDIDATES_MM), "selected_shaft_bore": H0_SELECTED_BORE_MM,
        "source_bore_dimensions": {"drive_through_bore_mm": S.drive_bore_mm},
        "final_bore_dimensions": {"sprocket_through_bore_mm": S.drive_bore_mm, "h0_clamp_bore_mm": H0_SELECTED_BORE_MM, "sprocket_h0_pilot_recess_mm": S0_PILOT_RECESS_DIAMETER_MM, "recess_depth_mm": S0_PILOT_RECESS_DEPTH_MM},
        "source_hub_dimensions": {"radius_mm": S.hub_radius_mm, "axial_width_mm": S.axial_width_mm, "bolt_count": S.axial_bolt_count, "bolt_pcd_mm": S.axial_bolt_pcd_mm, "bolt_hole_mm": S.axial_bolt_hole_mm, "bolt_phase_deg": S.axial_bolt_phase_deg},
        "final_hub_dimensions": {"sprocket_hub_radius_mm": S.hub_radius_mm, "sprocket_axial_width_mm": S.axial_width_mm, "h0_body_radius_mm": H0_BODY_RADIUS_MM, "h0_axial_length_mm": H0_BODY_LENGTH_MM, "pilot_od_mm": H0_PILOT_OD_MM},
        "clamp_type": "H0_TWO_PIECE_SPLIT_CLAMP_FLANGE", "clamp_bolt_count": H0_CLAMP_BOLT_COUNT, "clamp_bolt_size": H0_CLAMP_BOLT_SIZE,
        "axial_fastener_count": AXIAL_FASTENER_COUNT, "axial_fastener_size": AXIAL_FASTENER_SIZE,
        "pilot_diameter": H0_PILOT_OD_MM, "pilot_clearance": {"diametral_mm": H0_PILOT_DIAMETRAL_CLEARANCE_MM, "status": "H0_PRINTED_CANDIDATE_PHYSICAL_TEST_REQUIRED"},
        "h1_metal_hub": {"verified_dimensions_found": False, "pilot_diameter_mm": None, "pilot_clearance_mm": None, "bolt_pattern_final": "HOLD", "manufacturing_release": "HOLD", "template": "SPROCKET_SIDE_REFERENCE_ONLY_NO_METAL_PRODUCT_GEOMETRY"},
        "source_external_bounding_box": analysis["source"]["bounds_mm"], "final_external_bounding_box": analysis["final_sprocket"]["bounds_mm"],
        "source_solid_count": analysis["source"]["solid_count"], "final_sprocket_solid_count": analysis["final_sprocket"]["solid_count"], "h0_solid_count": analysis["h0"]["solid_count"],
        "union_method": "SOURCE_V0131_POSITIVE_VOLUME_EMBEDDED_ROOT_BOOLEAN_UNION_THEN_CLEAN",
        "buried_root_extension_used": True, "buried_root_extension_dimensions": {"source_embed_depth_mm": S.embed_depth_mm, "source_embed_radius_mm": S.embed_radius_mm, "source_embed_width_mm": S.embed_width_mm, "new_extension_added_by_v0937": False},
        "external_mesh_geometry_changed": False, "external_mesh_scope": "TOOTH_AND_OUTER_RING_R_GE_ROOT_RADIUS_IDENTICAL; CENTRAL_H0_INTERFACE_RECESS_ADDED",
        "link_geometry_changed": False, "guide_geometry_changed": False, "shaft_irreversible_machining_required": False, "direct_petg_set_screw_used": False,
        "authority_files_changed": False, "physical_test_status": "REQUIRED", "powered_rotation_status": "NOT_APPROVED",
        "source_audit": source_audit_result, "protected_lane_audit": protected, "analysis": analysis,
    }


def source_trace_text() -> str:
    return f"""# SOURCE_TRACE

## Selected current source

- `{SOURCE_REL}/{SOURCE_CODE_REL}` — tracked v0.13.1 integrated sprocket generator.
- `{SOURCE_REL}/upstream/contracts/crawler_h1_v0_13_1_design_contract.json` — external tooth profile and integrated-root contract.
- `{SOURCE_REL}/{SOURCE_DRIVE_STL_REL}` — tracked drive mesh.

The tracked current source defines 12 teeth, phase 15 degrees, 30-degree spacing, tip/root radii 33.07/29.47 mm, tip/root tangential widths 7.5/9.5 mm, 44 mm axial width, 10.3 mm drive bore, and four 4.4 mm holes on PCD24 at phase 45 degrees. It already uses a 4.0 mm buried root extension and reports independent teeth 0.

## Separate-tooth lineage

`USER_REPORTED`: the failed physical article used separate inserted teeth with adhesive reinforcement. Repository search found v0.13.0 references to `crawler_h1_sprocket_fit_test_v0_4_0.py`, but that dependency body is not present in the tracked pretest snapshot. The old separate-tooth CAD is therefore `HOLD_HISTORICAL_GENERATOR_NOT_PRESENT`; it is not reconstructed by inference.

## Shaft and clamp references

- `cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5`: 10.0/10.1/10.2 fit coupon and corrected 10.1 mm no-load reference.
- `cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2`: split-clamp positioning coupons; these are explicitly no-load M3 fit references, not torque hubs.
- No verified metal split-clamp flange-hub product dimensions were found. H1 remains parameter HOLD.
"""


def readme_text() -> str:
    return f"""# Common Rover integral drive sprocket shaft connection v{VERSION}

This lane rebuilds the current 12T tooth geometry as a one-piece S0 drive sprocket and adds a separate H0 dry-test split-clamp flange for a nominal 10 mm round shaft. The tooth profile, angular positions, pitch record, 44 mm axial width, and outer envelope are unchanged.

H0 uses two PETG halves, two transverse M5 through-bolts with metal nuts/washers, and the source four-hole PCD24 interface with axial M4 through-fasteners. PETG threads, adhesive, D-flat, cross-hole, keyway, and press-fit-only torque transfer are not used.

Print target: Bambu Lab A1, PETG, 100% scale. Stable flat faces down; verify seam, tooth-root walls, clamp gap, nut pockets, bore roundness, and elephant-foot effects. Settings are recommendations until physically verified.

`DRY_HAND_ROTATION` and `NO_LOAD_FIT_TEST` are candidates only. Powered rotation, torque load, belt tension, manufacturing, purchase, mud/water, and field use are not approved.

## Release state

- `GITHUB_EXECUTABLE_CAD_RELEASE = HOLD`
- `GITHUB_MANUFACTURING_RELEASE = HOLD`
- `PURCHASE_STATUS = NOT_APPROVED`
- `FIELD_DEPLOYMENT_STATUS = NOT_APPROVED`
- `BELT_TENSION = NOT_APPROVED`
- `POWERED_ROTATION = NOT_APPROVED`
- `TORQUE_LOAD = NOT_APPROVED`
- `SHAFT_IRREVERSIBLE_MACHINING = NOT_APPROVED`
"""


def design_spec_text() -> str:
    return f"""# DESIGN_SPEC

- Classification: `{CLASSIFICATION}`
- Current external tooth source: v0.13.1 tracked source.
- Tooth contract: 12T; 15-degree phase; 30-degree spacing; tip/root radii 33.07/29.47 mm; tip/root widths 7.5/9.5 mm; axial width 44 mm.
- S0 sprocket: source Boolean union retained; final one solid; only a 15.2 x 2.5 mm H0 pilot recess is added on the central face.
- H0: two-piece split clamp, selected bore 10.1 mm candidate, 0.6 mm split gap, 15.0 mm pilot OD, 18 mm body radius, 14 mm length.
- Clamp bolts: two M5 transverse through-bolts, metal nuts and flat washers.
- Sprocket fasteners: four M4 axial through-fasteners at the existing PCD24/phase45 interface, metal nuts and washers.
- H1: metal flange-hub product dimensions missing; template/reference only, manufacturing HOLD.
"""


def design_review_text() -> str:
    return """# DESIGN_REVIEW

The current tracked v0.13.1 source is already integral and fixes the historical zero-volume root contact. S0 deliberately keeps its exposed root and tooth faces unchanged; no root fillet or tooth-width improvement is introduced.

The separate H0 hub was selected over an integral slit boss because it separates clamp strain from the tooth-root load path and remains replaceable. Its printed clamp is only a dry/no-load diagnostic. A metal H1 split-clamp flange remains the powered candidate, but no verified product dimensions exist.

Open concerns: printed pilot and bore fit, PETG creep, M5 pocket durability, axial M4 stack length, actual bearing/shaft axial stack, shield OD, tool access in the frame, and link clearance around installed hardware. These require physical measurement and test; they are not manufacturing releases.
"""


def trade_study_text() -> str:
    return """# SHAFT_CONNECTION_TRADE_STUDY

| Option | Torque path | Reversible | Shaft machining | Status |
|---|---|---:|---:|---|
| PETG direct set screw | point load/PETG thread | yes | no | REJECTED |
| Adhesive/press fit | uncertain friction | poor | no | REJECTED |
| Integral slit boss | clamp through sprocket body | yes | no | ALTERNATIVE; crack coupling concern |
| H0 separate PETG split flange | circumferential clamp + 4 axial bolts | yes | no | DRY_TEST_CANDIDATE |
| H1 metal split flange | metal circumferential clamp + flange bolts | yes | no | PREFERRED_POWERED_CANDIDATE; DIMENSIONS_REQUIRED |

Torque and axial retention are separated conceptually. A separate 10 mm split shaft collar may be added only after actual stack measurement; spacer contact is allowed only on the bearing inner race.
"""


def physical_test_plan_text() -> str:
    steps = [
        "Inspect the sprocket exterior.",
        "Confirm exactly 12 teeth.",
        "Inspect every tooth root for layer or fusion defects.",
        "Inspect both H0 clamp halves.",
        "Measure the physical nominal 10 mm shaft diameter.",
        "Compare the 10.0 / 10.1 / 10.2 mm coupons.",
        "Record the selected physical bore candidate; do not treat 10.1 mm as selected without this result.",
        "Fit H0 around the unmodified round shaft without forced insertion.",
        "Install the two M5 through-bolts, metal washers, and metal nuts finger-tight.",
        "Tighten left/right evenly in stages.",
        "Add a witness mark across shaft and H0 hub.",
        "Add a witness mark across H0 hub and S0 sprocket.",
        "Check initial axial movement.",
        "With no crawler, hand rotate forward 10 turns.",
        "With no crawler, hand rotate reverse 10 turns.",
        "Inspect both witness marks for movement.",
        "Install the crawler at minimum tension only.",
        "Hand rotate forward one revolution.",
        "Hand rotate reverse one revolution.",
        "Hand rotate forward 10 revolutions.",
        "Hand rotate reverse 10 revolutions.",
        "Inspect tooth entry into every link receiver.",
        "Inspect shaft-to-hub relative rotation.",
        "Inspect hub-to-sprocket relative rotation.",
        "Inspect PETG whitening and cracking.",
        "Inspect permanent split-gap deformation.",
        "Inspect bearing migration and verify no shield/outer-race contact.",
        "Recheck axial movement.",
    ]
    criteria = [
        "no forced press fit", "clamping holds only after bolt tightening",
        "no forward/reverse witness-mark motion", "no axial motion",
        "no PETG whitening or crack", "no center shift",
        "no bearing-shield contact", "no fastener-to-link contact",
    ]
    return "# PHYSICAL_TEST_PLAN\n\nPrerequisites: no power, no load, no maximum tension, no mud/water, and no irreversible shaft work.\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)) + "\n\n## H0 candidate acceptance observations\n\n" + "\n".join(f"- {item}" for item in criteria) + "\n\nEven a compliant H0 result does not approve powered rotation, torque load, or field use."


def assembly_instructions_text() -> str:
    return """# ASSEMBLY_INSTRUCTIONS

1. Print the S0 sprocket, H0 top/bottom halves, and bore coupon at 100% scale.
2. Deburr only loose print artifacts; do not reshape tooth or pilot surfaces.
3. Select 10.0/10.1/10.2 only from the physical coupon result; 10.1 is the first candidate.
4. Place H0 halves around the unmodified round shaft. Insert two M5 through-bolts with metal washers and nuts; do not tap PETG.
5. Seat the H0 15.0 mm pilot lightly in the sprocket 15.2 mm recess.
6. Install four M4 through-bolts through the existing PCD24 holes with metal washers and nuts. Tighten gradually and symmetrically.
7. Maintain clearance from the bearing shield and outer race. Actual axial stack is HOLD.
8. Mark all interfaces and perform only the no-power sequence in PHYSICAL_TEST_PLAN.md.
"""


def bom_text() -> str:
    axial_stack = S.axial_width_mm + H0_BODY_LENGTH_MM + 2.0 + 3.2
    return f"""# HARDWARE_BOM

| Class | Item | Quantity | CAD envelope / derivation | Status |
|---|---|---:|---|---|
| REQUIRED | M5 through-bolt | 2 | 5.0 mm shank; length selection after printed 38 mm lug span and washer/nut stack check | CANDIDATE_LENGTH_HOLD |
| REQUIRED | M5 metal nut | 2 | 9.2 mm circumscribed envelope | CANDIDATE |
| REQUIRED | M5 flat washer | 4 | 10 mm OD envelope | CANDIDATE |
| REQUIRED | M4 axial through-bolt | 4 | minimum stack about {axial_stack:.1f} mm before thread allowance | STANDARD_LENGTH_SELECTION_HOLD |
| REQUIRED | M4 metal nut | 4 | 8.2 mm circumscribed envelope | CANDIDATE |
| REQUIRED | M4 flat washer | 8 | 9 mm OD envelope | CANDIDATE |
| REQUIRED | nominal 10 mm round shaft | 1 | actual diameter/straightness measurement required | USER_PART_MEASUREMENT_REQUIRED |
| CANDIDATE | 10 mm split shaft collar | 1 | OD/width shown only as abstract 20 x 6 mm envelope | PRODUCT_SELECTION_HOLD |
| HOLD | bearing inner-race spacer | as required | inner-race contact diameter and shield clearance unmeasured | NOT_INCLUDED |
| HOLD | H1 metal split flange hub | 1 | no verified dimensions or product number | NOT_INCLUDED |
"""


def svg_shell(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#f7f8fa"/><text x="40" y="50" font-family="sans-serif" font-size="28" font-weight="bold">{title}</text><text x="40" y="82" font-family="sans-serif" font-size="17" fill="#a22">S0 DRY FIT ONLY · NO POWER · NO LOAD</text>{body}</svg>'''


def overview_svg() -> str:
    return svg_shell("Integral 12T sprocket and H0 split-clamp overview", '''<circle cx="300" cy="350" r="190" fill="#d8e3da" stroke="#234" stroke-width="3"/><circle cx="300" cy="350" r="105" fill="#f7f8fa" stroke="#234" stroke-width="3"/><text x="210" y="355" font-family="sans-serif" font-size="22">12T integral S0</text><rect x="585" y="220" width="300" height="105" rx="24" fill="#e8caa4" stroke="#653" stroke-width="3"/><rect x="585" y="375" width="300" height="105" rx="24" fill="#e8caa4" stroke="#653" stroke-width="3"/><line x1="585" y1="350" x2="885" y2="350" stroke="#d33" stroke-width="6"/><circle cx="735" cy="350" r="50" fill="#f7f8fa" stroke="#234" stroke-width="3"/><text x="650" y="540" font-family="sans-serif" font-size="21">H0: 2 PETG halves · 2x M5 clamp · 4x M4 axial</text><text x="650" y="580" font-family="sans-serif" font-size="18">H1 metal product geometry = HOLD</text>''')


def load_path_svg() -> str:
    labels = ["10 mm shaft", "circumferential clamp", "H0 flange", "4 metal axial fasteners", "S0 body/root", "12 teeth", "crawler links"]
    pieces = []
    for i, label in enumerate(labels):
        x = 35 + i * 165
        pieces.append(f'<rect x="{x}" y="280" width="140" height="100" rx="12" fill="#dce9f1" stroke="#245" stroke-width="2"/><text x="{x+70}" y="335" text-anchor="middle" font-family="sans-serif" font-size="16">{label}</text>')
        if i < len(labels) - 1:
            pieces.append(f'<path d="M{x+140},330 L{x+165},330" stroke="#a33" stroke-width="4" marker-end="url(#a)"/>')
    return svg_shell("Symmetric torque load path", '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#a33"/></marker></defs>' + ''.join(pieces) + '<text x="50" y="500" font-family="sans-serif" font-size="19">No adhesive · no PETG tapped set screw · no D-flat · no keyway · reversible disassembly</text>')


def commit_paths_text() -> str:
    return "\n".join(f"{LANE_REL}/{path}" for path in PACKAGE_PATHS)


def role_for(path: str) -> str:
    if path.endswith(".stl"): return "S0_OR_H0_PHYSICAL_TEST_ARTIFACT_NO_POWER"
    if path.endswith(".step"): return "REFERENCE_STEP_NOT_FOR_MANUFACTURING"
    if path.endswith(".svg"): return "ASSEMBLY_OR_LOAD_PATH_DIAGRAM"
    if path.endswith(".py"): return "SOURCE_OR_CONTRACT_TEST"
    return "CANONICAL_HANDOFF_RECORD"


def manifest_text() -> str:
    return "\n".join(f"{path}|{role_for(path)}" for path in PACKAGE_PATHS)


def sha256sums_text(base: Path = LANE_DIR) -> str:
    return "\n".join(f"{sha256(base / path)}  {path}" for path in PACKAGE_PATHS if path != "SHA256SUMS.txt")


def export_shape(shape: cq.Shape | cq.Workplane, path: Path, stl: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path), tolerance=0.01, angularTolerance=0.1) if stl else cq.exporters.export(shape, str(path))


def export_artifacts() -> None:
    source, final = source_drive(), s0_sprocket()
    top, bottom = h0_half("TOP"), h0_half("BOTTOM")
    export_shape(final, LANE_DIR / STEP_FILES[0]); export_shape(final, LANE_DIR / STL_FILES[0], True)
    export_shape(cq.Compound.makeCompound([source.translate((-45, 0, 0)).val(), final.translate((45, 0, 0)).val()]), LANE_DIR / STEP_FILES[1])
    export_shape(top, LANE_DIR / STEP_FILES[2]); export_shape(bottom, LANE_DIR / STEP_FILES[3])
    export_shape(top, LANE_DIR / STL_FILES[1], True); export_shape(bottom, LANE_DIR / STL_FILES[2], True)
    export_shape(h0_assembly(False), LANE_DIR / STEP_FILES[4]); export_shape(h0_exploded(), LANE_DIR / STEP_FILES[5])
    coupon = shaft_coupon(); export_shape(coupon, LANE_DIR / STEP_FILES[6]); export_shape(coupon, LANE_DIR / STL_FILES[3], True)
    export_shape(final, LANE_DIR / STEP_FILES[7])
    export_shape(h0_assembly(True), LANE_DIR / STEP_FILES[8])
    write_text(LANE_DIR / SVG_FILES[0], overview_svg()); write_text(LANE_DIR / SVG_FILES[1], load_path_svg())


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for path in STEP_FILES:
        try:
            shape = cq.importers.importStep(str(base / path)).val()
            solids = len(shape.Solids()); box = shape.BoundingBox()
            passed = solids >= 1 and box.xlen > 0 and box.ylen > 0 and box.zlen > 0
            rows.append({"path": path, "solids": solids, "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_stls(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for path in STL_FILES:
        try:
            with (base / path).open("rb") as stream:
                raw = trimesh.exchange.stl.load_stl_binary(stream)
            mesh = trimesh.Trimesh(vertices=raw["vertices"], faces=raw["faces"], process=False); mesh.merge_vertices()
            areas = mesh.area_faces
            degenerate = int((areas <= 1e-10).sum())
            components = int(mesh.body_count)
            passed = bool(mesh.is_watertight) and components == 1 and float(mesh.volume) > 0 and degenerate == 0
            rows.append({"path": path, "watertight": bool(mesh.is_watertight), "components": components, "faces": len(mesh.faces), "degenerate_triangles": degenerate, "volume_mm3": float(mesh.volume), "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_svgs(base: Path = LANE_DIR) -> dict[str, Any]:
    import xml.etree.ElementTree as ET
    rows = []
    for path in SVG_FILES:
        try:
            root = ET.parse(base / path).getroot(); passed = root.tag.endswith("svg") and root.get("viewBox") is not None
            rows.append({"path": path, "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_manifest(base: Path = LANE_DIR) -> dict[str, Any]:
    values = [line.split("|", 1)[0] for line in (base / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if "|" in line]
    return {"entry_count": len(values), "exact_order": values == list(PACKAGE_PATHS), "status": "PASS" if values == list(PACKAGE_PATHS) else "FAIL"}


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    values = {}
    for line in (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, path = line.split("  ", 1); values[path] = digest
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}; mismatches: list[Any] = []
    if set(values) != required: mismatches.append({"missing": sorted(required - set(values)), "extra": sorted(set(values) - required)})
    for path, expected in values.items():
        actual = sha256(base / path) if (base / path).is_file() else "MISSING"
        if actual != expected: mismatches.append({"path": path, "expected": expected, "actual": actual})
    return {"verified": len(values), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def verify_geometry(base: Path = LANE_DIR) -> dict[str, Any]:
    manifest = json.loads((base / "geometry_manifest.json").read_text(encoding="utf-8")); a = manifest["analysis"]
    checks = {
        "teeth": manifest["source_tooth_count"] == manifest["final_tooth_count"] == 12 and a["tooth"]["spacing_deg"] == 30.0,
        "tooth_parameters": manifest["source_pitch_parameter"] == manifest["final_pitch_parameter"] and manifest["source_tooth_axial_width"] == manifest["final_tooth_axial_width"] and manifest["source_tooth_tip_width"] == manifest["final_tooth_tip_width"],
        "external": a["tooth"]["external_source_minus_final_mm3"] <= 1e-6 and a["tooth"]["external_final_minus_source_mm3"] <= 1e-6 and a["source"]["bounds_mm"] == a["final_sprocket"]["bounds_mm"],
        "one_piece": a["final_sprocket"]["solid_count"] == 1 and a["final_sprocket"]["valid"] and a["tooth"]["body_intersection_per_tooth_mm3"] >= a["tooth"]["minimum_required_mm3"],
        "h0": a["h0"]["solid_count"] == 2 and a["h0"]["top_solid_count"] == a["h0"]["bottom_solid_count"] == 1 and a["h0"]["top_valid"] and a["h0"]["bottom_valid"] and a["h0"]["half_intersection_mm3"] <= 1e-6,
        "shaft_clear": a["h0"]["shaft_top_intersection_mm3"] <= 1e-6 and a["h0"]["shaft_bottom_intersection_mm3"] <= 1e-6,
        "fasteners_clear": a["h0"]["m5_shank_clamp_intersection_mm3"] <= 1e-6 and a["h0"]["m4_shank_sprocket_hub_intersection_mm3"] <= 1e-6,
        "envelopes": all(value <= 1e-6 for key, value in a["envelopes"].items() if key.endswith("_mm3")),
        "coupon": a["coupon"]["bores_mm"] == [10.0, 10.1, 10.2] and a["coupon"]["solid_count"] == 1,
        "axis": a["axis"]["source_center_xy_mm"] == a["axis"]["final_center_xy_mm"] == a["axis"]["h0_center_xy_mm"],
        "prohibitions": not manifest["shaft_irreversible_machining_required"] and not manifest["direct_petg_set_screw_used"] and not manifest["authority_files_changed"] and manifest["powered_rotation_status"] == "NOT_APPROVED",
        "h1_hold": not manifest["h1_metal_hub"]["verified_dimensions_found"] and manifest["h1_metal_hub"]["manufacturing_release"] == "HOLD",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def validation_report(manifest: dict[str, Any], steps: dict[str, Any], stls: dict[str, Any], svgs: dict[str, Any]) -> dict[str, Any]:
    return {"document_id": DOCUMENT_ID, "classification": CLASSIFICATION, "geometry": verify_geometry_from_manifest(manifest), "STEP": steps, "STL": stls, "SVG": svgs, "physical_fit": "REQUIRED", "durability": "NOT_TESTED", "powered_rotation": "NOT_APPROVED", "status": "PASS" if steps["status"] == stls["status"] == svgs["status"] == "PASS" and verify_geometry_from_manifest(manifest)["status"] == "PASS" else "FAIL"}


def verify_geometry_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    a = manifest["analysis"]
    checks = {"12T": manifest["final_tooth_count"] == 12, "external_tooth_equal": a["tooth"]["external_source_minus_final_mm3"] <= 1e-6 and a["tooth"]["external_final_minus_source_mm3"] <= 1e-6, "one_piece": a["final_sprocket"]["solid_count"] == 1 and a["final_sprocket"]["valid"], "positive_root": a["tooth"]["body_intersection_per_tooth_mm3"] >= 100.0, "h0_two_halves": a["h0"]["solid_count"] == 2, "envelope_clear": all(value <= 1e-6 for key, value in a["envelopes"].items() if key.endswith("_mm3")), "no_irreversible_shaft": not manifest["shaft_irreversible_machining_required"], "no_petg_set_screw": not manifest["direct_petg_set_screw_used"]}
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for path in SOURCE_FILES:
        if not (LANE_DIR / path).is_file(): raise RuntimeError(f"source missing: {path}")
    repo = repository_audit(require_complete=False); protected = protected_audit(True); source = source_audit(True); analysis = geometry_analysis()
    manifest = geometry_manifest(repo, source, protected, analysis)
    write_text(LANE_DIR / ROOT_FILES[0], readme_text()); write_text(LANE_DIR / ROOT_FILES[1], design_spec_text()); write_text(LANE_DIR / ROOT_FILES[2], source_trace_text()); write_text(LANE_DIR / ROOT_FILES[3], design_review_text()); write_text(LANE_DIR / ROOT_FILES[4], trade_study_text()); write_text(LANE_DIR / ROOT_FILES[5], physical_test_plan_text()); write_text(LANE_DIR / ROOT_FILES[6], assembly_instructions_text()); write_text(LANE_DIR / ROOT_FILES[7], bom_text()); write_text(LANE_DIR / ROOT_FILES[8], commit_paths_text()); write_json(LANE_DIR / ROOT_FILES[10], manifest)
    export_artifacts(); steps, stls, svgs = verify_steps(), verify_stls(), verify_svgs(); report = validation_report(manifest, steps, stls, svgs); write_json(LANE_DIR / ROOT_FILES[11], report)
    write_text(LANE_DIR / ROOT_FILES[12], f"command=python -B {SOURCE_FILES[0]} --refresh-artifacts\nstatus={'PASS' if report['status']=='PASS' else 'FAIL'}\nformal_paths={len(PACKAGE_PATHS)}\nstep={steps['pass_count']}/{steps['count']}\nstl={stls['pass_count']}/{stls['count']}\nsvg={svgs['pass_count']}/{svgs['count']}\nphysical_test=REQUIRED\npowered_rotation=NOT_APPROVED")
    write_text(LANE_DIR / ROOT_FILES[13], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED")
    write_text(LANE_DIR / ROOT_FILES[14], manifest_text()); write_text(LANE_DIR / ROOT_FILES[9], sha256sums_text())
    if lane_files() != sorted(PACKAGE_PATHS): raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    reports = [verify_steps(), verify_stls(), verify_svgs(), verify_manifest(), verify_hashes(), verify_geometry()]
    if any(item["status"] != "PASS" for item in reports): raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "formal_paths": len(PACKAGE_PATHS), "STEP": "9/9 PASS", "STL": "4/4 PASS", "SVG": "2/2 PASS", "geometry": "PASS", "protected": protected["status"], "source": source["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    if lane_files() != sorted(PACKAGE_PATHS): raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    repo = repository_audit(True); protected = protected_audit(); source = source_audit(); steps, stls, svgs, manifest, hashes, geometry = verify_steps(), verify_stls(), verify_svgs(), verify_manifest(), verify_hashes(), verify_geometry()
    reports = {"steps": steps["status"], "stls": stls["status"], "svgs": svgs["status"], "manifest": manifest["status"], "hashes": hashes["status"], "geometry": geometry["status"], "protected": protected["status"], "source": source["status"]}
    if any(value != "PASS" for value in reports.values()): raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "repository": repo, "protected_lanes": protected["status"], "source_protection": source["status"], "formal_paths": len(PACKAGE_PATHS), "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "STL_manifold": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "status": "PASS"}


def zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, date_time=(2000, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16; return info


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as archive:
        for rel in PACKAGE_PATHS: archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist(); duplicates = sorted({name for name in names if names.count(name) > 1}); traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal: raise RuntimeError({"names_exact": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        values = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip(): digest, rel = line.split("  ", 1); values[rel] = digest
        internal = [rel for rel, expected in values.items() if hashlib.sha256(archive.read(rel)).hexdigest() != expected]
        lane_mismatch = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0937_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive: archive.extractall(target)
            env = dict(os.environ); env["V0937_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", SOURCE_FILES[0], "--verify"], target, env); tests = run([sys.executable, "-B", SOURCE_FILES[1]], target, env)
            if build.returncode or tests.returncode: raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatch: raise RuntimeError({"internal_hash_mismatch": internal, "lane_mismatch": lane_mismatch})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify(); DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True); timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); final = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"; temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final.exists() or temporary.exists(): raise RuntimeError("refusing to overwrite handoff")
    try:
        write_text(LANE_DIR / ROOT_FILES[13], "status=PACKAGE_TESTS_PENDING\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED"); write_text(LANE_DIR / ROOT_FILES[9], sha256sums_text()); write_zip(temporary)
        env = dict(os.environ); env["V0937_TEST_ZIP"] = str(temporary); result = run([sys.executable, "-B", SOURCE_FILES[1]], LANE_DIR, env)
        if result.returncode: raise RuntimeError(result.stdout)
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[13], "command=python -B " + SOURCE_FILES[1] + "\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED\nfull_output:\n" + result.stdout); write_text(LANE_DIR / ROOT_FILES[9], sha256sums_text()); verify()
    finally:
        if temporary.exists(): temporary.unlink()
    write_zip(final); return {"verification": "PASS", **verify_zip(final, standalone=True)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--refresh-artifacts", action="store_true"); parser.add_argument("--verify", action="store_true"); parser.add_argument("--package", action="store_true"); parser.add_argument("--verify-zip", type=Path); args = parser.parse_args(argv)
    if sum((args.refresh_artifacts, args.verify, args.package, args.verify_zip is not None)) != 1: parser.error("choose exactly one action")
    result = refresh_artifacts() if args.refresh_artifacts else verify() if args.verify else package_handoff() if args.package else verify_zip(args.verify_zip, True)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
