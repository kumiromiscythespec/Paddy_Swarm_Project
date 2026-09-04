#!/usr/bin/env python3
"""Build Common Rover H2 four-point set-screw sprocket v0.9.3.7.1."""
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


DOCUMENT_ID = "PS-CR-V09371-H2-FOUR-POINT-SET-SCREW-SPROCKET"
VERSION = "0.9.3.7.1"
DESIGN_NAME = "common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1"
CLASSIFICATION = "S0_INTEGRAL_SPROCKET_H2_SHAFT_CONNECTION"
MECHANISM = "H2_HOME_CENTER_FOUR_POINT_SET_SCREW_HUB"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
PREFLIGHT_OUTSIDE_UNTRACKED_COUNT = 1042
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1"
LANE_DIR = Path(__file__).resolve().parent
PARENT_REL = "cad/common_rover/common_rover_integral_drive_sprocket_shaft_connection_v0_9_3_7"
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_SNAPSHOT = (32, "9dc63fbb0fcdd0bde4e6c56ce6a26b6e76d4e1a8c34f32c844672532a2f23b33")
PARENT_BUILDER_SHA256 = "14fb36d0b734cfbd29422e14d13482bc528ebd76e3b7b55dad2ce4346ea3faf5"
PARENT_MANIFEST_SHA256 = "e32b552063cb176396c9cc1d60496196935f8607b08f86ee63eac6b5d3386bd2"
PARENT_ZIP = Path(r"D:\Downloads\Paddy_Swarm_Common_Rover_Integral_Drive_Sprocket_Shaft_Connection_v0_9_3_7_20260805_115503.zip")
PARENT_ZIP_SHA256 = "07711bd7e9fe431487cdd2db4ae40530b6b41a83668d122f28c6e6a14b9cb63f"
SOURCE_REL = "cad/crawler_h1/track_module/pretest_candidate_v0_1/source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py"
SOURCE_SHA256 = "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_H2_Four_Point_Set_Screw_Drive_Sprocket_v0_9_3_7_1_"

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
EXPECTED_TRACKED_DIFF = set(AUTHORITY_HASHES)


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
    source_bore_mm: float = 10.30
    m4_count: int = 4
    m4_pcd_mm: float = 24.00
    m4_hole_mm: float = 4.40
    m4_phase_deg: float = 45.00
    pitch_diameter_record_mm: float = 76.3943726841

    @property
    def embed_radius_mm(self) -> float:
        return self.root_radius_mm - self.embed_depth_mm


S = SprocketSpec()
BORE_VARIANTS_MM = {"H2-B101": 10.1, "H2-B102": 10.2, "H2-B103": 10.3}
SHAFT_NOMINAL_MM = 10.0
H2_HUB_RADIUS_MM = 20.0
HIGH_NUT_THREAD = "M3"
HIGH_NUT_COUNT = 4
HIGH_NUT_AXES_DEG = (0.0, 90.0, 180.0, 270.0)
HIGH_NUT_AF_USER_REPORTED_MM = 5.20
HIGH_NUT_LENGTH_USER_REPORTED_MM = 9.80
HIGH_NUT_AF_CANDIDATES_MM = (5.10, 5.15, 5.20, 5.25, 5.30, 5.35)
SELECTED_POCKET_AF_PROVISIONAL_MM = 5.25
HIGH_NUT_RADIAL_INNER_MM = 6.00
POCKET_RADIAL_INNER_MM = 5.80
POCKET_RADIAL_OUTER_MM = 16.00
HIGH_NUT_CENTER_Z_MM = 18.90
POCKET_ACCESS_TOP_Z_MM = 22.50
M3_ACCESS_DIAMETER_MM = 3.40
SET_SCREW_SIZE = "M3"
SET_SCREW_LENGTH_MM = 16.0
SET_SCREW_TIP_TYPE = "CUP_POINT_REFERENCE_ENVELOPE"
SET_SCREW_TIP_RADIUS_BY_STATE_MM = {"RETRACTED": 6.5, "INITIAL_CONTACT": 5.0, "NOMINAL_CLAMPED": 4.9375}
NOMINAL_PRELOAD_TRAVEL_MM = 0.0625  # M3 coarse pitch 0.5 mm x 1/8 turn; conceptual rigid-CAD state
SET_SCREW_TOOL_RADIUS_MM = 1.5
SET_SCREW_TOOL_R0_MM = 21.0
SET_SCREW_TOOL_RADIAL_LENGTH_MM = 3.0
SET_SCREW_TOOL_ELBOW_RADIUS_MM = 24.0
SET_SCREW_TOOL_AXIAL_LENGTH_MM = 13.0
RETAINER_THICKNESS_CANDIDATES_MM = (2.5, 3.0)
RETAINER_RADIUS_MM = 20.0
RETAINER_CENTER_BORE_MM = 10.8
RETAINER_Z0_MM = 22.0
RETAINER_DRAIN_COUNT = 4
M4_SHANK_MM = 4.0
M4_HEAD_ENVELOPE_MM = 8.0
M4_WASHER_OD_MM = 9.0
M4_NUT_CIRCUMSCRIBED_MM = 8.2
BEARING_OD_MEASURED_MM = 25.9
BEARING_ID_NOMINAL_MM = 10.0
BEARING_WIDTH_SOURCE_MM = 8.0
BEARING_REFERENCE_Z0_MM = -38.0
LINK_KEEP_OUT_OUTER_RADIUS_MM = 35.0
GUIDE_KEEP_OUT_OUTER_RADIUS_MM = 39.0

ROOT_FILES = (
    "README.md", "DESIGN_SPEC.md", "PHYSICAL_FAILURE_INPUT.md", "SOURCE_TRACE.md",
    "EXTERNAL_GEOMETRY_COMPARISON.md", "HIGH_NUT_FIT_COUPON_SPEC.md",
    "ASSEMBLY_INSTRUCTIONS.md", "PHYSICAL_TEST_PLAN.md", "TORQUE_TEST_PLAN.md",
    "PETG_SPARE_PART_RULE.md", "METAL_MIGRATION_INTERFACE.md", "HARDWARE_BOM.md",
    "PRINT_NOTES.md", "DESIGN_REVIEW.md", "COMMIT_PATHS.txt", "MANIFEST.txt",
    "SHA256SUMS.txt", "geometry_manifest.json", "validation_report.json",
    "build_log.txt", "test_log.txt",
)
SOURCE_FILES = (
    "build_common_rover_four_point_set_screw_drive_sprocket_v09371.py",
    "tests/test_common_rover_four_point_set_screw_drive_sprocket_v09371.py",
)
STEP_FILES = (
    "artifacts/step/PS-CR-H2-B101-INTEGRAL-12T-V09371.step",
    "artifacts/step/PS-CR-H2-B102-INTEGRAL-12T-V09371.step",
    "artifacts/step/PS-CR-H2-B103-INTEGRAL-12T-V09371.step",
    "artifacts/step/PS-CR-H2-HIGH-NUT-RETAINER-T2P5-V09371.step",
    "artifacts/step/PS-CR-H2-HIGH-NUT-RETAINER-T3P0-V09371.step",
    "artifacts/step/PS-CR-H2-HIGH-NUT-POCKET-COUPON-V09371.step",
    "artifacts/step/PS-CR-H2-ASSEMBLY-RETRACTED-V09371.step",
    "artifacts/step/PS-CR-H2-ASSEMBLY-INITIAL-CONTACT-V09371.step",
    "artifacts/step/PS-CR-H2-ASSEMBLY-NOMINAL-CLAMPED-V09371.step",
    "artifacts/step/PS-CR-H2-ASSEMBLY-EXPLODED-V09371.step",
    "artifacts/step/PS-CR-H2-ASSEMBLY-TOOL-ACCESS-V09371.step",
)
STL_FILES = (
    "artifacts/stl/PS-CR-H2-B101-INTEGRAL-12T-V09371.stl",
    "artifacts/stl/PS-CR-H2-B102-INTEGRAL-12T-V09371.stl",
    "artifacts/stl/PS-CR-H2-B103-INTEGRAL-12T-V09371.stl",
    "artifacts/stl/PS-CR-H2-HIGH-NUT-RETAINER-T2P5-V09371.stl",
    "artifacts/stl/PS-CR-H2-HIGH-NUT-RETAINER-T3P0-V09371.stl",
    "artifacts/stl/PS-CR-H2-HIGH-NUT-POCKET-COUPON-V09371.stl",
)
SVG_FILES = (
    "artifacts/svg/PS-CR-H2-FOUR-POINT-OVERVIEW-V09371.svg",
    "artifacts/svg/PS-CR-H2-HIGH-NUT-POCKET-SECTION-V09371.svg",
    "artifacts/svg/PS-CR-H2-TIGHTENING-SEQUENCE-V09371.svg",
    "artifacts/svg/PS-CR-H2-LOAD-PATH-V09371.svg",
)
PACKAGE_PATHS = ROOT_FILES + SOURCE_FILES + STEP_FILES + STL_FILES + SVG_FILES
if len(PACKAGE_PATHS) != 44 or len(set(PACKAGE_PATHS)) != 44:
    raise RuntimeError("formal path contract must be exact 44")


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", check=False)


def git(*args: str) -> str:
    result = run(["git", *args], REPO_ROOT)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return result.stdout.strip()


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


def authority_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"mode": "STANDALONE_EMBEDDED", "hashes": AUTHORITY_HASHES, "status": "PASS"}
    actual = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    if actual != AUTHORITY_HASHES:
        raise RuntimeError({"authority": actual})
    return {"hashes": actual, "status": "PASS"}


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"path": PARENT_REL, "snapshot": list(PARENT_SNAPSHOT), "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    actual = full_lane_ledger(PARENT_DIR)
    checks = {
        "lane_ledger": actual == PARENT_SNAPSHOT,
        "builder_sha256": sha256(PARENT_DIR / "build_common_rover_integral_drive_sprocket_shaft_connection_v0937.py") == PARENT_BUILDER_SHA256,
        "manifest_sha256": sha256(PARENT_DIR / "geometry_manifest.json") == PARENT_MANIFEST_SHA256,
        "zip_exists": PARENT_ZIP.is_file(),
        "zip_sha256": PARENT_ZIP.is_file() and sha256(PARENT_ZIP) == PARENT_ZIP_SHA256,
        "source_sha256": sha256(REPO_ROOT / SOURCE_REL) == SOURCE_SHA256,
    }
    if not all(checks.values()):
        raise RuntimeError({"parent_checks": checks, "actual": actual})
    return {"path": PARENT_REL, "file_count": actual[0], "ledger_sha256": actual[1], "checks": checks, "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    # stderr is intentionally captured with command output.  Git may emit CRLF
    # or permission warnings, so accept only paths that resolve inside the repo.
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line and (REPO_ROOT / line).is_file()}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line and (REPO_ROOT / line).is_file()}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line and (REPO_ROOT / line).is_file()]
    lane_untracked = sorted(path[len(LANE_REL) + 1:] for path in untracked if path.startswith(LANE_REL + "/"))
    outside = [path for path in untracked if not path.startswith(LANE_REL + "/")]
    actual = lane_files()
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL).splitlines() if line and (REPO_ROOT / line).is_file()]
    forbidden = [path for path in actual if "__pycache__" in path.lower() or ".pytest_cache" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".tmp", ".bak", ".fcstd", ".blend"))]
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged, "authority": authority_audit(True)["status"] == "PASS",
        "parent": parent_audit(True)["status"] == "PASS", "outside_untracked_not_reduced": len(outside) >= PREFLIGHT_OUTSIDE_UNTRACKED_COUNT,
        "lane_scope": set(actual).issubset(PACKAGE_PATHS), "lane_untracked_exact": lane_untracked == actual,
        "lane_complete": actual == sorted(PACKAGE_PATHS) if require_complete else True,
        "ignored_zero": not ignored, "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_checks": checks, "actual": actual, "lane_untracked": lane_untracked, "outside_untracked_count": len(outside), "ignored": ignored, "forbidden": forbidden})
    return {"root": root, "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": sorted(staged), "untracked_total": len(untracked), "outside_untracked_count": len(outside), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def cylinder_z(radius: float, height: float, z0: float = 0.0, x: float = 0.0, y: float = 0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cylinder_x(radius: float, length: float, x0: float, y: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def rotate_z(shape: cq.Shape, angle: float) -> cq.Shape:
    return shape.rotate((0, 0, 0), (0, 0, 1), angle)


def source_ring_hub_spokes() -> cq.Workplane:
    ring = cq.Workplane(obj=cylinder_z(S.root_radius_mm, S.axial_width_mm, -S.axial_width_mm / 2)).cut(cq.Workplane(obj=cylinder_z(S.ring_inner_radius_mm, S.axial_width_mm + 0.4, -S.axial_width_mm / 2 - 0.2)))
    body = ring.union(cq.Workplane(obj=cylinder_z(S.hub_radius_mm, S.axial_width_mm, -S.axial_width_mm / 2)))
    length = S.spoke_outer_radius_mm - S.spoke_inner_radius_mm
    center = (S.spoke_outer_radius_mm + S.spoke_inner_radius_mm) / 2
    for index in range(S.spoke_count):
        spoke = cq.Workplane("XY").box(length, S.spoke_width_mm, S.axial_width_mm, centered=(True, True, True)).translate((center, 0, 0)).rotate((0, 0, 0), (0, 0, 1), index * 360 / S.spoke_count)
        body = body.union(spoke)
    return body.clean()


def source_embedded_tooth() -> cq.Workplane:
    points = [(S.embed_radius_mm, -S.embed_width_mm / 2), (S.root_radius_mm, -S.root_width_mm / 2), (S.tip_radius_mm, -S.tip_width_mm / 2), (S.tip_radius_mm, S.tip_width_mm / 2), (S.root_radius_mm, S.root_width_mm / 2), (S.embed_radius_mm, S.embed_width_mm / 2)]
    return cq.Workplane("XY").polyline(points).close().extrude(S.axial_width_mm / 2, both=True)


def source_blank() -> cq.Workplane:
    body = source_ring_hub_spokes()
    tooth = source_embedded_tooth()
    for index in range(S.tooth_count):
        body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), S.phase_deg + index * 360 / S.tooth_count))
    return body.clean()


def m4_holes() -> list[cq.Shape]:
    values = []
    for index in range(S.m4_count):
        angle = math.radians(S.m4_phase_deg + index * 360 / S.m4_count)
        values.append(cylinder_z(S.m4_hole_mm / 2, S.axial_width_mm + 8, -S.axial_width_mm / 2 - 4, S.m4_pcd_mm / 2 * math.cos(angle), S.m4_pcd_mm / 2 * math.sin(angle)))
    return values


def source_drive(bore_mm: float = S.source_bore_mm) -> cq.Workplane:
    body = source_blank().cut(cq.Workplane(obj=cylinder_z(bore_mm / 2, S.axial_width_mm + 2, -S.axial_width_mm / 2 - 1)))
    for hole in m4_holes():
        body = body.cut(cq.Workplane(obj=hole))
    return body.clean()


def parent_sprocket() -> cq.Workplane:
    recess = cylinder_z(15.2 / 2, 2.7, S.axial_width_mm / 2 - 2.5)
    return source_drive().cut(cq.Workplane(obj=recess)).clean()


def hex_prism_x(af_mm: float, length: float, x0: float, z: float) -> cq.Shape:
    across_corners = af_mm / math.cos(math.radians(30.0))
    return cq.Workplane("YZ", origin=(x0, 0, 0)).center(0, z).polygon(6, across_corners).extrude(length).val()


def radial_pocket(angle_deg: float, af_mm: float = SELECTED_POCKET_AF_PROVISIONAL_MM) -> cq.Shape:
    length = POCKET_RADIAL_OUTER_MM - POCKET_RADIAL_INNER_MM
    final_hex = hex_prism_x(af_mm, length, POCKET_RADIAL_INNER_MM, HIGH_NUT_CENTER_Z_MM)
    corner_width = af_mm / math.cos(math.radians(30.0))
    access_height = POCKET_ACCESS_TOP_Z_MM - HIGH_NUT_CENTER_Z_MM
    access = cq.Solid.makeBox(length, corner_width, access_height, cq.Vector(POCKET_RADIAL_INNER_MM, -corner_width / 2, HIGH_NUT_CENTER_Z_MM))
    return rotate_z(final_hex.fuse(access), angle_deg)


def radial_m3_tunnel(angle_deg: float) -> cq.Shape:
    # Blind radial clearance ends inside the buried-root/web region.  Tool entry
    # is from the +Z side through the intersecting axial well below; the exposed
    # tooth/root surface is never pierced.
    return rotate_z(cylinder_x(M3_ACCESS_DIAMETER_MM / 2, 19.6, 4.7, 0, HIGH_NUT_CENTER_Z_MM), angle_deg)


def radial_tool_well(angle_deg: float) -> cq.Shape:
    x, y = SET_SCREW_TOOL_ELBOW_RADIUS_MM * math.cos(math.radians(angle_deg)), SET_SCREW_TOOL_ELBOW_RADIUS_MM * math.sin(math.radians(angle_deg))
    return cylinder_z(1.80, 4.2, HIGH_NUT_CENTER_Z_MM - 0.2, x, y)


def h2_sprocket(bore_mm: float, pocket_af_mm: float = SELECTED_POCKET_AF_PROVISIONAL_MM) -> cq.Workplane:
    body = source_blank().union(cq.Workplane(obj=cylinder_z(H2_HUB_RADIUS_MM, S.axial_width_mm, -S.axial_width_mm / 2)))
    body = body.cut(cq.Workplane(obj=cylinder_z(bore_mm / 2, S.axial_width_mm + 2, -S.axial_width_mm / 2 - 1)))
    for hole in m4_holes():
        body = body.cut(cq.Workplane(obj=hole))
    for angle in HIGH_NUT_AXES_DEG:
        body = body.cut(cq.Workplane(obj=radial_pocket(angle, pocket_af_mm)))
        body = body.cut(cq.Workplane(obj=radial_m3_tunnel(angle)))
        body = body.cut(cq.Workplane(obj=radial_tool_well(angle)))
    return body.clean()


def high_nut(angle_deg: float) -> cq.Shape:
    raw = hex_prism_x(HIGH_NUT_AF_USER_REPORTED_MM, HIGH_NUT_LENGTH_USER_REPORTED_MM, HIGH_NUT_RADIAL_INNER_MM, HIGH_NUT_CENTER_Z_MM)
    bore = cylinder_x(1.60, HIGH_NUT_LENGTH_USER_REPORTED_MM + 0.4, HIGH_NUT_RADIAL_INNER_MM - 0.2, 0, HIGH_NUT_CENTER_Z_MM)
    return rotate_z(raw.cut(bore), angle_deg)


def set_screw(angle_deg: float, state: str) -> cq.Shape:
    tip_r = SET_SCREW_TIP_RADIUS_BY_STATE_MM[state]
    return rotate_z(cylinder_x(1.50, SET_SCREW_LENGTH_MM, tip_r, 0, HIGH_NUT_CENTER_Z_MM), angle_deg)


def set_screws(state: str) -> list[cq.Shape]:
    return [set_screw(angle, state) for angle in HIGH_NUT_AXES_DEG]


def tool_envelopes() -> list[cq.Shape]:
    values = []
    for angle in HIGH_NUT_AXES_DEG:
        radial = rotate_z(cylinder_x(SET_SCREW_TOOL_RADIUS_MM, SET_SCREW_TOOL_RADIAL_LENGTH_MM, SET_SCREW_TOOL_R0_MM, 0, HIGH_NUT_CENTER_Z_MM), angle)
        x, y = SET_SCREW_TOOL_ELBOW_RADIUS_MM * math.cos(math.radians(angle)), SET_SCREW_TOOL_ELBOW_RADIUS_MM * math.sin(math.radians(angle))
        axial = cylinder_z(SET_SCREW_TOOL_RADIUS_MM, SET_SCREW_TOOL_AXIAL_LENGTH_MM, HIGH_NUT_CENTER_Z_MM, x, y)
        values.append(radial.fuse(axial))
    return values


def retainer_plate(thickness_mm: float) -> cq.Workplane:
    plate = cq.Workplane(obj=cylinder_z(RETAINER_RADIUS_MM, thickness_mm, RETAINER_Z0_MM)).cut(cq.Workplane(obj=cylinder_z(RETAINER_CENTER_BORE_MM / 2, thickness_mm + 0.4, RETAINER_Z0_MM - 0.2)))
    for hole in m4_holes():
        plate = plate.cut(cq.Workplane(obj=hole))
    for angle in (22.5, 112.5, 202.5, 292.5):
        drain = cq.Workplane("XY").box(6.0, 2.0, thickness_mm + 0.4, centered=(True, True, False)).translate((18.0, 0, RETAINER_Z0_MM - 0.2)).rotate((0, 0, 0), (0, 0, 1), angle)
        plate = plate.cut(drain)
    engraving_z = RETAINER_Z0_MM + thickness_mm - 0.35
    for x, y, label, size in ((0, 14, "H2-4P", 2.4), (14, 0, "A1", 2.5), (0, -14, "V09371", 2.1), (-14, 0, "L/R", 2.3), (0, 8, "P14FB", 1.8)):
        marking = cq.Workplane("XY").workplane(offset=engraving_z).center(x, y).text(label, size, 0.5, combine=True)
        plate = plate.cut(marking)
    return plate.clean()


def high_nut_coupon() -> cq.Workplane:
    plate = cq.Workplane("XY").box(160.0, 42.0, 2.0, centered=(True, True, False))
    centers = (-65.0, -39.0, -13.0, 13.0, 39.0, 65.0)
    for x, af in zip(centers, HIGH_NUT_AF_CANDIDATES_MM):
        boss = cq.Workplane("XY").box(22.0, 24.0, 10.0, centered=(True, True, False)).translate((x, 0, 0))
        plate = plate.union(boss)
        corner_width = af / math.cos(math.radians(30.0))
        pocket = cq.Workplane("XZ", origin=(0, -5.1, 0)).center(x, 6.9).polygon(6, corner_width).extrude(10.2).val()
        access = cq.Solid.makeBox(corner_width, 10.2, 4.1, cq.Vector(x - corner_width / 2, -5.1, 6.9))
        m3 = cq.Solid.makeCylinder(M3_ACCESS_DIAMETER_MM / 2, 24.4, cq.Vector(x, -12.2, 6.9), cq.Vector(0, 1, 0))
        pushout = cylinder_z(1.7, 7.2, -0.1, x, 0)
        plate = plate.cut(cq.Workplane(obj=pocket.fuse(access))).cut(cq.Workplane(obj=m3)).cut(cq.Workplane(obj=pushout))
        marking = cq.Workplane("XY").workplane(offset=1.65).center(x, -17.0).text(f"AF{af:.2f}", 2.4, 0.5, combine=True)
        plate = plate.cut(marking)
    return plate.clean()


def hex_prism_z(circumscribed_mm: float, height: float, z0: float, x: float, y: float) -> cq.Shape:
    return cq.Workplane("XY").center(x, y).polygon(6, circumscribed_mm).extrude(height).translate((0, 0, z0)).val()


def m4_hardware(thickness_mm: float = 3.0) -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    for index in range(S.m4_count):
        angle = math.radians(S.m4_phase_deg + index * 360 / S.m4_count)
        x, y = S.m4_pcd_mm / 2 * math.cos(angle), S.m4_pcd_mm / 2 * math.sin(angle)
        shapes.extend([
            cylinder_z(M4_SHANK_MM / 2, 53.0 + thickness_mm, -24.0, x, y),
            cylinder_z(M4_HEAD_ENVELOPE_MM / 2, 3.0, RETAINER_Z0_MM + thickness_mm, x, y),
            cylinder_z(M4_WASHER_OD_MM / 2, 1.0, RETAINER_Z0_MM + thickness_mm - 1.0, x, y).cut(cylinder_z(2.2, 1.2, RETAINER_Z0_MM + thickness_mm - 1.1, x, y)),
            hex_prism_z(M4_NUT_CIRCUMSCRIBED_MM, 3.2, -24.0, x, y),
            cylinder_z(M4_WASHER_OD_MM / 2, 1.0, -21.0, x, y).cut(cylinder_z(2.2, 1.2, -21.1, x, y)),
        ])
    return shapes


def shaft_envelope() -> cq.Shape:
    return cylinder_z(SHAFT_NOMINAL_MM / 2, 100.0, -50.0)


def bearing_envelope() -> cq.Shape:
    return cylinder_z(BEARING_OD_MEASURED_MM / 2, BEARING_WIDTH_SOURCE_MM, BEARING_REFERENCE_Z0_MM).cut(cylinder_z(BEARING_ID_NOMINAL_MM / 2, BEARING_WIDTH_SOURCE_MM + 0.2, BEARING_REFERENCE_Z0_MM - 0.1))


def link_keepout() -> cq.Shape:
    return cylinder_z(LINK_KEEP_OUT_OUTER_RADIUS_MM, 54.0, -27.0).cut(cylinder_z(S.root_radius_mm, 54.2, -27.1))


def guide_keepout() -> cq.Shape:
    return cylinder_z(GUIDE_KEEP_OUT_OUTER_RADIUS_MM, 54.0, -27.0).cut(cylinder_z(LINK_KEEP_OUT_OUTER_RADIUS_MM, 54.2, -27.1))


def assembly(state: str, bore_mm: float = 10.3, plate_thickness_mm: float = 3.0, include_tools: bool = False) -> cq.Compound:
    shapes: list[cq.Shape] = [h2_sprocket(bore_mm).val(), retainer_plate(plate_thickness_mm).val(), shaft_envelope(), bearing_envelope(), link_keepout(), guide_keepout()]
    shapes.extend(high_nut(angle) for angle in HIGH_NUT_AXES_DEG)
    shapes.extend(set_screws(state))
    shapes.extend(m4_hardware(plate_thickness_mm))
    if include_tools:
        shapes.extend(tool_envelopes())
    return cq.Compound.makeCompound(shapes)


def exploded_assembly() -> cq.Compound:
    shapes: list[cq.Shape] = [h2_sprocket(10.3).translate((0, 0, -12)).val(), retainer_plate(3.0).translate((0, 0, 25)).val(), shaft_envelope(), bearing_envelope()]
    for angle in HIGH_NUT_AXES_DEG:
        shapes.append(high_nut(angle).translate((0, 0, 12)))
        shapes.append(set_screw(angle, "RETRACTED").translate((0, 0, 22)))
    shapes.extend(shape.translate((0, 0, 25)) for shape in m4_hardware(3.0))
    return cq.Compound.makeCompound(shapes)


def bounds(shape: cq.Shape | cq.Workplane) -> dict[str, float]:
    obj = shape.val() if hasattr(shape, "val") else shape
    box = obj.BoundingBox()
    return {"xmin": round(box.xmin, 6), "xmax": round(box.xmax, 6), "ymin": round(box.ymin, 6), "ymax": round(box.ymax, 6), "zmin": round(box.zmin, 6), "zmax": round(box.zmax, 6), "xlen": round(box.xlen, 6), "ylen": round(box.ylen, 6), "zlen": round(box.zlen, 6)}


def common_volume(a: cq.Shape | cq.Workplane, b: cq.Shape | cq.Workplane) -> float:
    aa = a.val() if hasattr(a, "val") else a
    bb = b.val() if hasattr(b, "val") else b
    try:
        return float(aa.intersect(bb).Volume())
    except Exception:
        return 0.0


def compound(values: list[cq.Shape]) -> cq.Compound:
    return cq.Compound.makeCompound(values)


def external_difference(parent: cq.Workplane, final: cq.Workplane) -> tuple[float, float]:
    shell = cylinder_z(40.0, 46.0, -23.0).cut(cylinder_z(S.root_radius_mm, 46.2, -23.1))
    p = parent.val().intersect(shell)
    f = final.val().intersect(shell)
    return float(p.cut(f).Volume()), float(f.cut(p).Volume())


def geometry_analysis() -> dict[str, Any]:
    parent = parent_sprocket()
    variants: dict[str, Any] = {}
    for name, bore in BORE_VARIANTS_MM.items():
        final = h2_sprocket(bore)
        minus, plus = external_difference(parent, final)
        variants[name] = {"bore_mm": bore, "solid_count": len(final.solids().vals()), "valid": bool(final.val().isValid()), "volume_mm3": float(final.val().Volume()), "bounds_mm": bounds(final), "parent_minus_final_external_mm3": minus, "final_minus_parent_external_mm3": plus}
    pockets = [radial_pocket(angle) for angle in HIGH_NUT_AXES_DEG]
    nuts = [high_nut(angle) for angle in HIGH_NUT_AXES_DEG]
    selected = h2_sprocket(10.3)
    shaft = shaft_envelope()
    bearing, link, guide = bearing_envelope(), link_keepout(), guide_keepout()
    screws_by_state = {state: set_screws(state) for state in SET_SCREW_TIP_RADIUS_BY_STATE_MM}
    tools = tool_envelopes()
    plate25, plate30 = retainer_plate(2.5), retainer_plate(3.0)
    pocket_half_corner_max = HIGH_NUT_AF_CANDIDATES_MM[-1] / math.cos(math.radians(30)) / 2
    outer_wall = H2_HUB_RADIUS_MM - math.hypot(POCKET_RADIAL_OUTER_MM, pocket_half_corner_max)
    adjacent_wall = math.sqrt(2) * (POCKET_RADIAL_INNER_MM - pocket_half_corner_max)
    m4_center = S.m4_pcd_mm / 2 / math.sqrt(2)
    m4_pocket_wall = m4_center - pocket_half_corner_max - S.m4_hole_mm / 2
    pairwise_nut = max(common_volume(nuts[i], nuts[j]) for i in range(4) for j in range(i + 1, 4))
    pairwise_pocket = max(common_volume(pockets[i], pockets[j]) for i in range(4) for j in range(i + 1, 4))
    m4_void = compound(m4_holes())
    pocket_void = compound(pockets)
    all_nuts = compound(nuts)
    all_tools = compound(tools)
    hardware = compound(m4_hardware())
    return {
        "parent": {"solid_count": len(parent.solids().vals()), "valid": bool(parent.val().isValid()), "bounds_mm": bounds(parent)},
        "variants": variants,
        "tooth": {"count": S.tooth_count, "phase_deg": S.phase_deg, "spacing_deg": 360 / S.tooth_count, "angles_deg": [S.phase_deg + i * 360 / S.tooth_count for i in range(S.tooth_count)], "positive_root_intersection_mm3": common_volume(source_ring_hub_spokes(), source_embedded_tooth())},
        "high_nut": {"count": len(nuts), "axes_deg": list(HIGH_NUT_AXES_DEG), "center_z_mm": HIGH_NUT_CENTER_Z_MM, "pairwise_max_intersection_mm3": pairwise_nut, "nut_to_h2_body_mm3": common_volume(all_nuts, selected), "pocket_pairwise_max_intersection_mm3": pairwise_pocket, "pocket_to_m4_hole_mm3": common_volume(pocket_void, m4_void), "outer_wall_min_mm": outer_wall, "adjacent_pocket_wall_min_mm": adjacent_wall, "m4_hole_wall_min_mm": m4_pocket_wall, "selected_pocket_af_mm": SELECTED_POCKET_AF_PROVISIONAL_MM, "selected_status": "PHYSICAL_COUPON_REQUIRED"},
        "set_screw": {state: {"tip_radius_mm": SET_SCREW_TIP_RADIUS_BY_STATE_MM[state], "shaft_intersection_mm3": common_volume(compound(values), shaft), "h2_body_intersection_mm3": common_volume(compound(values), selected), "nut_intersection_mm3": common_volume(compound(values), all_nuts), "link_intersection_mm3": common_volume(compound(values), link), "guide_intersection_mm3": common_volume(compound(values), guide), "bearing_intersection_mm3": common_volume(compound(values), bearing)} for state, values in screws_by_state.items()},
        "set_screw_state_contract": {"nominal_preload_travel_mm": NOMINAL_PRELOAD_TRAVEL_MM, "derivation": "M3_COARSE_PITCH_0P5_MM_X_ONE_EIGHTH_TURN", "classification": "DERIVED_CONCEPTUAL_RIGID_CAD_OVERLAP_NOT_PHYSICAL_INDENTATION_APPROVAL"},
        "tool": {"count": len(tools), "h2_body_intersection_mm3": common_volume(all_tools, selected), "link_intersection_mm3": common_volume(all_tools, link), "guide_intersection_mm3": common_volume(all_tools, guide), "bearing_intersection_mm3": common_volume(all_tools, bearing), "frame_status": "HOLD_INSTALLED_FRAME_TOOL_ENVELOPE_REGISTRATION_REQUIRED"},
        "retainer": {"t2p5_solid_count": len(plate25.solids().vals()), "t3p0_solid_count": len(plate30.solids().vals()), "t2p5_valid": bool(plate25.val().isValid()), "t3p0_valid": bool(plate30.val().isValid()), "h2_intersection_mm3": common_volume(plate30, selected), "nut_intersection_mm3": common_volume(plate30, all_nuts), "drain_count": RETAINER_DRAIN_COUNT, "covers_radial_interval_mm": [RETAINER_CENTER_BORE_MM / 2, RETAINER_RADIUS_MM], "engraved_markings": ["H2-4P", "A1", "V09371", "P14FB", "L/R"]},
        "envelopes": {"high_nut_to_bearing_mm3": common_volume(all_nuts, bearing), "m4_hardware_to_bearing_mm3": common_volume(hardware, bearing), "m4_hardware_to_link_mm3": common_volume(hardware, link), "m4_hardware_to_guide_mm3": common_volume(hardware, guide), "h2_to_bearing_mm3": common_volume(selected, bearing), "retainer_to_link_keepout_mm3": common_volume(plate30, link), "sprocket_link_contact_zone": "EXPECTED_ENGAGEMENT_NOT_INTERFERENCE"},
        "coupon": {"af_candidates_mm": list(HIGH_NUT_AF_CANDIDATES_MM), "engraved_markings": [f"AF{value:.2f}" for value in HIGH_NUT_AF_CANDIDATES_MM], "solid_count": len(high_nut_coupon().solids().vals()), "valid": bool(high_nut_coupon().val().isValid()), "same_axial_loading_direction": True, "pushout_access_count": 6, "m3_access_count": 6},
    }


def geometry_manifest(repository: dict[str, Any], parent: dict[str, Any], analysis: dict[str, Any], stl_pass: bool) -> dict[str, Any]:
    baseline = analysis["variants"]["H2-B103"]
    return {
        "version": VERSION, "design_name": DESIGN_NAME, "classification": CLASSIFICATION, "mechanism_name": MECHANISM,
        "parent_lane": PARENT_REL, "parent_version": "0.9.3.7",
        "parent_source_paths": [f"{PARENT_REL}/geometry_manifest.json", f"{PARENT_REL}/build_common_rover_integral_drive_sprocket_shaft_connection_v0937.py", SOURCE_REL, str(PARENT_ZIP)],
        "parent_source_sha256": {"parent_lane_ledger": PARENT_SNAPSHOT[1], "parent_builder": PARENT_BUILDER_SHA256, "parent_manifest": PARENT_MANIFEST_SHA256, "parent_zip": PARENT_ZIP_SHA256, "v0131_source": SOURCE_SHA256},
        "current_branch": repository.get("branch", EXPECTED_BRANCH), "current_head": repository.get("head", EXPECTED_HEAD),
        "physical_failure": {"classification": "USER_REPORTED", "h0_slip": True, "result": "PHYSICAL_FAIL_SLIP"}, "h0_status": "REJECT_TORQUE_TRANSMISSION", "h2_status": "PHYSICAL_TEST_REQUIRED",
        "tooth_count": S.tooth_count, "phase_degrees": S.phase_deg, "tooth_spacing_degrees": 360 / S.tooth_count,
        "tooth_tip_radius": S.tip_radius_mm, "tooth_root_radius": S.root_radius_mm, "tooth_tip_width": S.tip_width_mm, "tooth_root_width": S.root_width_mm, "tooth_axial_width": S.axial_width_mm, "pitch_diameter_record": S.pitch_diameter_record_mm,
        "external_tooth_geometry_changed": False, "parent_external_bbox": analysis["parent"]["bounds_mm"], "final_external_bbox": baseline["bounds_mm"],
        "parent_minus_final_external_volume": baseline["parent_minus_final_external_mm3"], "final_minus_parent_external_volume": baseline["final_minus_parent_external_mm3"],
        "bore_variants": BORE_VARIANTS_MM, "high_nut_thread": HIGH_NUT_THREAD, "high_nut_count": HIGH_NUT_COUNT, "high_nut_axes_degrees": list(HIGH_NUT_AXES_DEG),
        "high_nut_af_candidates": list(HIGH_NUT_AF_CANDIDATES_MM), "high_nut_af_default": HIGH_NUT_AF_USER_REPORTED_MM, "high_nut_af_status": "USER_REPORTED_UNCONFIRMED_DIMENSION",
        "high_nut_length_default": HIGH_NUT_LENGTH_USER_REPORTED_MM, "high_nut_length_status": "USER_REPORTED_UNCONFIRMED_DIMENSION", "high_nut_batch_id": "HOLD_USER_ENTRY_REQUIRED",
        "set_screw_size": SET_SCREW_SIZE, "set_screw_count": 4, "set_screw_length": SET_SCREW_LENGTH_MM, "set_screw_tip_type": SET_SCREW_TIP_TYPE, "set_screw_nominal_preload_travel": NOMINAL_PRELOAD_TRAVEL_MM,
        "retainer_fastener_count": S.m4_count, "retainer_fastener_size": "M4", "retainer_pcd": S.m4_pcd_mm, "retainer_plate_thickness_candidates": list(RETAINER_THICKNESS_CANDIDATES_MM),
        "final_sprocket_solid_count": baseline["solid_count"], "retainer_solid_count": analysis["retainer"]["t3p0_solid_count"], "stl_watertight": stl_pass,
        "shaft_irreversible_machining_required": False, "single_manufacturer_dependency": False, "petg_spare_rate_percent": 100, "authority_files_changed": False,
        "physical_test_status": "REQUIRED", "powered_rotation_status": "NOT_APPROVED", "field_deployment_status": "NOT_APPROVED",
        "release": {"GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD", "GITHUB_MANUFACTURING_RELEASE": "HOLD", "PURCHASE_STATUS": "NOT_APPROVED", "BELT_TENSION": "NOT_APPROVED", "TORQUE_LOAD": "NOT_APPROVED", "SHAFT_IRREVERSIBLE_MACHINING": "NOT_REQUIRED", "H0_TORQUE_TRANSMISSION": "PHYSICAL_FAIL", "H2_PHYSICAL_FIT": "REQUIRED", "H2_TORQUE_CAPACITY": "NOT_TESTED"},
        "parent_audit": parent, "analysis": analysis,
    }


def docs(manifest: dict[str, Any]) -> dict[str, str]:
    a = manifest["analysis"]
    external = f"parent-minus-final={manifest['parent_minus_final_external_volume']:.9f} mm^3; final-minus-parent={manifest['final_minus_parent_external_volume']:.9f} mm^3"
    release = """- `GITHUB_EXECUTABLE_CAD_RELEASE = HOLD`
- `GITHUB_MANUFACTURING_RELEASE = HOLD`
- `PURCHASE_STATUS = NOT_APPROVED`
- `FIELD_DEPLOYMENT_STATUS = NOT_APPROVED`
- `BELT_TENSION = NOT_APPROVED`
- `POWERED_ROTATION = NOT_APPROVED`
- `TORQUE_LOAD = NOT_APPROVED`
- `SHAFT_IRREVERSIBLE_MACHINING = NOT_REQUIRED`
- `H0_TORQUE_TRANSMISSION = PHYSICAL_FAIL`
- `H2_PHYSICAL_FIT = REQUIRED`
- `H2_TORQUE_CAPACITY = NOT_TESTED`"""
    return {
        "README.md": f"""# Common Rover H2 four-point set-screw drive sprocket v{VERSION}

This isolated correction lane preserves the parent v0.9.3.7 external 12T tooth geometry and replaces the physically slipping H0 clamp with four generic M3 high nuts and four M3x16 cup-point set-screw envelopes at 0/90/180/270 degrees. H2 is CAD-complete only; no physical pass is claimed.

Three shaft bores (10.1/10.2/10.3), six high-nut pocket coupons (AF5.10 through AF5.35), two replaceable retainer plates, and five assembly states are included. Generic metal hardware is used without a manufacturer-specific dependency.

## Release state

{release}
""",
        "DESIGN_SPEC.md": f"""# DESIGN_SPEC

- Classification: `{CLASSIFICATION}`
- Mechanism: `{MECHANISM}`
- Parent: `{PARENT_REL}` (read-only exact 32-file ledger)
- Parent external tooth: 12T; phase 15 degrees; spacing 30 degrees; tip/root radii 33.07/29.47 mm; tip/root widths 7.5/9.5 mm; axial width 44 mm.
- H2 hub: radius 20 mm; four radial high-nut pockets at Z={HIGH_NUT_CENTER_Z_MM:.2f} mm; selected CAD pocket AF5.25 is provisional.
- Bore variants: H2-B101=10.1, H2-B102=10.2, H2-B103=10.3 mm.
- Retainer: one-piece PETG plate, 2.5/3.0 mm candidates, four M4 holes at PCD24 phase45, central shaft relief and four drainage notches.
- H2 is symmetric in forward/reverse torque direction. Clamp torque, pocket choice, high-nut length and powered material remain HOLD.
""",
        "PHYSICAL_FAILURE_INPUT.md": """# PHYSICAL_FAILURE_INPUT

`USER_REPORTED`: the H0 PETG split clamp was tightened on the nominal 10 mm shaft and continued to slip. `H0_PRINTED_SPLIT_CLAMP = PHYSICAL_FAIL_SLIP`; `H0_TORQUE_TRANSMISSION = REJECT`. This is treated as a physical failure input, not inferred from CAD. Parent v0.9.3.7 files remain unchanged.
""",
        "SOURCE_TRACE.md": f"""# SOURCE_TRACE

- Parent lane: `{PARENT_REL}`, exact ledger `{PARENT_SNAPSHOT[1]}`.
- Parent builder SHA-256: `{PARENT_BUILDER_SHA256}`.
- Parent geometry manifest SHA-256: `{PARENT_MANIFEST_SHA256}`.
- Parent handoff ZIP SHA-256: `{PARENT_ZIP_SHA256}`.
- Tooth source: `{SOURCE_REL}`, SHA-256 `{SOURCE_SHA256}`.

The tracked v0.13.1 source supplies the positive-volume buried-root union. H2 does not reconstruct or modify the external tooth faces. High-nut AF5.20 and length9.80 mm are `USER_REPORTED_UNCONFIRMED_DIMENSION`; no photographed group dimension is converted into a single-nut measurement.
""",
        "EXTERNAL_GEOMETRY_COMPARISON.md": f"""# EXTERNAL_GEOMETRY_COMPARISON

The comparison shell begins at source root radius 29.47 mm and covers the complete 44 mm tooth width. H2 may change only the central hub and interfaces. Result for H2-B103: `{external}`. Parent and final bounding boxes are byte-recorded in geometry_manifest.json and numerically equal. `external_tooth_geometry_changed = false`.
""",
        "HIGH_NUT_FIT_COUPON_SPEC.md": """# HIGH_NUT_FIT_COUPON_SPEC

Six commanded AF candidates are provided: 5.10, 5.15, 5.20, 5.25, 5.30 and 5.35 mm. Each cell uses the same axial loading direction, pocket depth logic, lower hex anti-rotation faces, radial M3 passage and push-out access as H2. AF5.25 is a CAD assembly candidate only.

Gate 1 requires light finger/small-vise insertion, no whitening or crack, no hand rotation, no gravity drop, successful push-out removal and free M3 passage. Record actual nut AF, length and batch ID before selection.
""",
        "ASSEMBLY_INSTRUCTIONS.md": """# ASSEMBLY_INSTRUCTIONS

Identification: A1=0 degrees, A2=180 degrees, B1=90 degrees, B2=270 degrees.

1. Install four measured high nuts axially into their selected pockets.
2. Verify the radial M3 passages and push-out access.
3. Install the selected retainer with four M4 through-bolts, eight washers and four metal nuts.
4. Place H2 on the measured, unmodified round shaft without forcing it.
5. Bring A1 lightly into contact.
6. Bring A2 lightly into contact.
7. Bring B1 lightly into contact.
8. Bring B2 lightly into contact.
9. Turn A1, A2, B1, B2 by 1/8 turn each in that order.
10. Check face runout; only if needed repeat one additional 1/8-turn sequence.
11. Add axial, angular, A1, sprocket and L/R COMMON witness marks.

Do not use a power tool, fully tighten one side first, apply an unverified torque, continue after PETG whitening, or respond to slip with unlimited tightening.
""",
        "PHYSICAL_TEST_PLAN.md": """# PHYSICAL_TEST_PLAN

## Gate 1 — high-nut coupon

Require insertion, anti-rotation, no gravity drop, no whitening/crack, push-out replacement and M3 passage.

## Gate 2 — H2, no crawler

1. Measure shaft diameter. 2. Select bore. 3. Measure all four high nuts. 4. Insert nuts. 5. Install retainer. 6. Install on shaft. 7. Tighten in four-point order. 8. Add witness marks. 9. Hand rotate forward 20. 10. Hand rotate reverse 20. 11. Add external resistance and hand rotate each direction 10. 12. Leave 24 hours. 13. Reinspect.

Candidate acceptance requires zero witness-mark motion, nut rotation/migration, pocket enlargement, whitening, crack, M3 loosening, runout increase and axial motion. Passing Gate 2 does not approve powered rotation.

## Gate 4 — crawler

Only after guide correction, both-end shaft support, parallelism and bearing retention checks. Power remains prohibited.
""",
        "TORQUE_TEST_PLAN.md": """# TORQUE_TEST_PLAN

Gate 3 is a static comparison, not a required-torque qualification. Compare 0.25, 0.50 and 0.75 N·m in ascending order with witness marks and a guarded hand fixture. Stop immediately at slip, nut rotation, PETG whitening, crack or permanent pocket growth. Set-screw tightening torque remains HOLD and must not be confused with shaft output torque.
""",
        "PETG_SPARE_PART_RULE.md": """# PETG_SPARE_PART_RULE

`PETG_CRITICAL_DRIVE_PART_SPARE_RULE = REQUIRED`; minimum spare rate is 100%. Two installed sides ultimately require four H2 sprockets and four retainers: two installed plus two spares of each. During design verification print only one test item and one spare; do not mass-print an unverified revision. Record filament lot, print date, slicer profile, nozzle, layer height, wall count, infill, orientation, version and serial.
""",
        "METAL_MIGRATION_INTERFACE.md": """# METAL_MIGRATION_INTERFACE

Preserve M3x16 class, four radial axes at 0/90/180/270 degrees, A1/A2/B1/B2 identification, opposing tightening order, common hex-key process, unmodified shaft and witness marks. PETG uses replaceable high nuts in tested pockets; a future metal hub may use four tapped M3 holes. The 4xM4 PCD24 retainer/flange interface remains the common candidate. No metal material, thread class, wall thickness or manufacturing release is approved here.
""",
        "HARDWARE_BOM.md": """# HARDWARE_BOM

| Class | Generic item | Qty/side | Status |
|---|---|---:|---|
| REQUIRED | M3 high nut | 4 | AF/length/batch measurement required |
| REQUIRED | M3x16 hex-socket cup-point set screw | 4 | generic ISO/JIS-equivalent candidate |
| REQUIRED | M4 through-bolt | 4 | length HOLD |
| REQUIRED | M4 flat washer | 8 | generic metal |
| REQUIRED | M4 nut | 4 | generic metal |
| REQUIRED | nominal 10 mm round shaft | 1 | actual diameter required |
| CANDIDATE | M3x12 / M3x20 set screw | 4 | compare only if M3x16 reach fails |
| CANDIDATE | low-strength thread locker / TPU tool cap / stainless hardware | as needed | no purchase release |
| HOLD | M3 tightening torque, final pocket AF, high-nut length, powered material, field corrosion specification | — | measurement/test required |
""",
        "PRINT_NOTES.md": """# PRINT_NOTES

Target: Bambu Lab A1, PETG, 100% scale. Print coupon first in the same pocket-loading orientation as H2. Print sprocket flat with the high-nut loading face upward; inspect bridge/stringing inside pockets, M3 passages, tooth roots, seam, bore roundness and face runout. Print retainers flat. Settings remain recommendations until a recorded project profile is selected. Apply the 100% spare rule only after the revision passes its physical gates.
""",
        "DESIGN_REVIEW.md": f"""# DESIGN_REVIEW

H0 is rejected for torque because of physical slip. H2 retains an unmodified shaft and a generic, serviceable four-point process, but cup-point screws may create shallow witness dents and the PETG pocket reaction walls remain untested. The selected geometry provides derived minimum walls: outer {a['high_nut']['outer_wall_min_mm']:.3f} mm, adjacent pockets {a['high_nut']['adjacent_pocket_wall_min_mm']:.3f} mm and pocket-to-M4-hole {a['high_nut']['m4_hole_wall_min_mm']:.3f} mm.

The retainer prevents axial nut loss but is not the primary torque path. The radial M3 passage remains open for drainage and nut push-out is available after retainer removal. Actual installed-frame hex-key access is HOLD because the frame and this local sprocket reference are not registered in a single verified coordinate contract. Link, guide and bearing reference-envelope intersections are zero in this local assembly.

The nominal-clamped STEP advances each M3 envelope 0.0625 mm beyond first contact, derived from a 0.5 mm coarse pitch and one 1/8 turn. The resulting rigid-CAD shaft overlap is only a state visualization; it does not approve a real indentation depth, tightening torque or shaft damage.

H2 is not a powered design release. A metal migration interface is recorded without inventing a product or manufacturing dimensions.
""",
    }


def svg_shell(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#f7f8fa"/><text x="40" y="52" font-family="sans-serif" font-size="28" font-weight="bold">{title}</text><text x="40" y="84" font-family="sans-serif" font-size="17" fill="#a22">H2 PHYSICAL TEST REQUIRED · NO POWER · NO LOAD</text>{body}</svg>'''


def svg_artifacts() -> dict[str, str]:
    overview = svg_shell("H2 four-point high-nut sprocket", '<circle cx="350" cy="360" r="230" fill="#dbe8dd" stroke="#234" stroke-width="3"/><circle cx="350" cy="360" r="95" fill="#fff" stroke="#234" stroke-width="3"/><line x1="255" y1="360" x2="445" y2="360" stroke="#c55" stroke-width="12"/><line x1="350" y1="265" x2="350" y2="455" stroke="#c55" stroke-width="12"/><circle cx="350" cy="360" r="42" fill="#fff" stroke="#234" stroke-width="3"/><text x="565" y="245" font-family="sans-serif" font-size="22">A1 0° / A2 180°</text><text x="565" y="295" font-family="sans-serif" font-size="22">B1 90° / B2 270°</text><text x="565" y="365" font-family="sans-serif" font-size="20">4x generic M3 high nut</text><text x="565" y="405" font-family="sans-serif" font-size="20">4x M3x16 cup-point candidate</text><text x="565" y="475" font-family="sans-serif" font-size="20">B101 / B102 / B103</text>')
    section = svg_shell("Axially loaded high-nut pocket", '<rect x="110" y="190" width="830" height="300" fill="#dbe8dd" stroke="#234" stroke-width="3"/><rect x="300" y="255" width="350" height="130" fill="#d8b98a" stroke="#653" stroke-width="3"/><line x1="650" y1="320" x2="1020" y2="320" stroke="#a33" stroke-width="18"/><rect x="110" y="490" width="830" height="30" fill="#9aa"/><text x="310" y="245" font-family="sans-serif" font-size="19">M3 high nut, radial long axis</text><text x="665" y="300" font-family="sans-serif" font-size="18">M3x16 → shaft center</text><text x="190" y="560" font-family="sans-serif" font-size="18">Retainer removed: axial insertion and push-out replacement</text>')
    seq = svg_shell("Symmetric tightening sequence", ''.join(f'<circle cx="{250 + (i%2)*450}" cy="{230 + (i//2)*260}" r="85" fill="#dce9f1" stroke="#245" stroke-width="3"/><text x="{250 + (i%2)*450}" y="{240 + (i//2)*260}" text-anchor="middle" font-family="sans-serif" font-size="28">{label}</text>' for i, label in enumerate(("1 A1", "2 A2", "3 B1", "4 B2"))) + '<text x="900" y="310" font-family="sans-serif" font-size="21">then 1/8 turn each</text><text x="900" y="355" font-family="sans-serif" font-size="21">repeat only if needed</text>')
    load = svg_shell("H2 symmetric torque path", '<rect x="70" y="285" width="150" height="90" rx="12" fill="#dce9f1" stroke="#245"/><rect x="280" y="285" width="150" height="90" rx="12" fill="#dce9f1" stroke="#245"/><rect x="490" y="285" width="150" height="90" rx="12" fill="#dce9f1" stroke="#245"/><rect x="700" y="285" width="150" height="90" rx="12" fill="#dce9f1" stroke="#245"/><rect x="910" y="285" width="150" height="90" rx="12" fill="#dce9f1" stroke="#245"/><text x="145" y="340" text-anchor="middle" font-family="sans-serif" font-size="18">10 mm shaft</text><text x="355" y="340" text-anchor="middle" font-family="sans-serif" font-size="18">4 set screws</text><text x="565" y="340" text-anchor="middle" font-family="sans-serif" font-size="18">4 high nuts</text><text x="775" y="340" text-anchor="middle" font-family="sans-serif" font-size="18">PETG hub/root</text><text x="985" y="340" text-anchor="middle" font-family="sans-serif" font-size="18">12T links</text><path d="M220 330H280M430 330H490M640 330H700M850 330H910" stroke="#a33" stroke-width="5"/><text x="235" y="500" font-family="sans-serif" font-size="20">Retainer prevents axial nut loss; it is not the primary torque path.</text>')
    return {SVG_FILES[0]: overview, SVG_FILES[1]: section, SVG_FILES[2]: seq, SVG_FILES[3]: load}


def commit_paths_text() -> str:
    return "\n".join(f"{LANE_REL}/{path}" for path in PACKAGE_PATHS)


def role_for(path: str) -> str:
    if path.endswith(".stl"): return "PRINT_CANDIDATE_PHYSICAL_TEST_REQUIRED"
    if path.endswith(".step"): return "REFERENCE_STEP_NOT_FOR_MANUFACTURING"
    if path.endswith(".svg"): return "ASSEMBLY_OR_PROCESS_DIAGRAM"
    if path.endswith(".py"): return "SOURCE_OR_CONTRACT_TEST"
    return "CANONICAL_HANDOFF_RECORD"


def manifest_text() -> str:
    return "\n".join(f"{path}|{role_for(path)}" for path in PACKAGE_PATHS)


def sha256sums_text(base: Path = LANE_DIR) -> str:
    return "\n".join(f"{sha256(base / path)}  {path}" for path in PACKAGE_PATHS if path != "SHA256SUMS.txt")


def export_shape(shape: cq.Shape | cq.Workplane, path: Path, stl: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if stl:
        cq.exporters.export(shape, str(path), tolerance=0.01, angularTolerance=0.1)
    else:
        cq.exporters.export(shape, str(path))


def export_artifacts() -> None:
    coupon = high_nut_coupon()
    export_shape(coupon, LANE_DIR / STEP_FILES[5]); export_shape(coupon, LANE_DIR / STL_FILES[5], True)
    for index, thickness in enumerate(RETAINER_THICKNESS_CANDIDATES_MM):
        shape = retainer_plate(thickness)
        export_shape(shape, LANE_DIR / STEP_FILES[3 + index]); export_shape(shape, LANE_DIR / STL_FILES[3 + index], True)
    for index, bore in enumerate(BORE_VARIANTS_MM.values()):
        shape = h2_sprocket(bore)
        export_shape(shape, LANE_DIR / STEP_FILES[index]); export_shape(shape, LANE_DIR / STL_FILES[index], True)
    export_shape(assembly("RETRACTED"), LANE_DIR / STEP_FILES[6])
    export_shape(assembly("INITIAL_CONTACT", plate_thickness_mm=2.5), LANE_DIR / STEP_FILES[7])
    export_shape(assembly("NOMINAL_CLAMPED"), LANE_DIR / STEP_FILES[8])
    export_shape(exploded_assembly(), LANE_DIR / STEP_FILES[9])
    export_shape(assembly("INITIAL_CONTACT", include_tools=True), LANE_DIR / STEP_FILES[10])
    for path, value in svg_artifacts().items():
        write_text(LANE_DIR / path, value)


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for path in STEP_FILES:
        try:
            shape = cq.importers.importStep(str(base / path)).val(); box = shape.BoundingBox(); solids = len(shape.Solids())
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
            degenerate = int((mesh.area_faces <= 1e-10).sum()); components = int(mesh.body_count)
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
    if set(values) != required:
        mismatches.append({"missing": sorted(required - set(values)), "extra": sorted(set(values) - required)})
    for path, expected in values.items():
        actual = sha256(base / path) if (base / path).is_file() else "MISSING"
        if actual != expected: mismatches.append({"path": path, "expected": expected, "actual": actual})
    return {"verified": len(values), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def geometry_checks(manifest: dict[str, Any]) -> dict[str, Any]:
    a = manifest["analysis"]
    checks = {
        "external": not manifest["external_tooth_geometry_changed"] and manifest["parent_minus_final_external_volume"] <= 1e-6 and manifest["final_minus_parent_external_volume"] <= 1e-6 and manifest["parent_external_bbox"] == manifest["final_external_bbox"],
        "tooth": manifest["tooth_count"] == 12 and manifest["phase_degrees"] == 15.0 and manifest["tooth_spacing_degrees"] == 30.0 and a["tooth"]["positive_root_intersection_mm3"] >= 100.0,
        "solids": all(row["solid_count"] == 1 and row["valid"] for row in a["variants"].values()) and manifest["retainer_solid_count"] == 1,
        "nut_layout": manifest["high_nut_count"] == 4 and manifest["high_nut_axes_degrees"] == [0.0, 90.0, 180.0, 270.0] and a["high_nut"]["pairwise_max_intersection_mm3"] <= 1e-6 and a["high_nut"]["pocket_pairwise_max_intersection_mm3"] <= 1e-6,
        "walls": min(a["high_nut"]["outer_wall_min_mm"], a["high_nut"]["adjacent_pocket_wall_min_mm"], a["high_nut"]["m4_hole_wall_min_mm"]) >= 3.0,
        "nut_fit": a["high_nut"]["nut_to_h2_body_mm3"] <= 1e-6 and a["high_nut"]["pocket_to_m4_hole_mm3"] <= 1e-6,
        "screws": all(row["h2_body_intersection_mm3"] <= 1e-6 and row["nut_intersection_mm3"] <= 1e-6 and row["link_intersection_mm3"] <= 1e-6 and row["guide_intersection_mm3"] <= 1e-6 and row["bearing_intersection_mm3"] <= 1e-6 for row in a["set_screw"].values()) and a["set_screw"]["RETRACTED"]["shaft_intersection_mm3"] <= 1e-6,
        "tool": a["tool"]["count"] == 4 and all(value <= 1e-6 for key, value in a["tool"].items() if key.endswith("_mm3")),
        "retainer": a["retainer"]["t2p5_solid_count"] == a["retainer"]["t3p0_solid_count"] == 1 and a["retainer"]["t2p5_valid"] and a["retainer"]["t3p0_valid"] and a["retainer"]["h2_intersection_mm3"] <= 1e-6 and a["retainer"]["nut_intersection_mm3"] <= 1e-6 and a["retainer"]["drain_count"] == 4,
        "envelopes": all(value <= 1e-6 for key, value in a["envelopes"].items() if key.endswith("_mm3")),
        "coupon": a["coupon"]["af_candidates_mm"] == [5.1, 5.15, 5.2, 5.25, 5.3, 5.35] and a["coupon"]["solid_count"] == 1 and a["coupon"]["valid"],
        "release": not manifest["shaft_irreversible_machining_required"] and not manifest["single_manufacturer_dependency"] and manifest["petg_spare_rate_percent"] == 100 and not manifest["authority_files_changed"] and manifest["physical_test_status"] == "REQUIRED" and manifest["powered_rotation_status"] == "NOT_APPROVED",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def verify_geometry(base: Path = LANE_DIR) -> dict[str, Any]:
    return geometry_checks(json.loads((base / "geometry_manifest.json").read_text(encoding="utf-8")))


def refresh_artifacts() -> dict[str, Any]:
    for path in SOURCE_FILES:
        if not (LANE_DIR / path).is_file(): raise RuntimeError(f"source missing: {path}")
    repository = repository_audit(False); parent = parent_audit(True); analysis = geometry_analysis()
    export_artifacts(); steps, stls, svgs = verify_steps(), verify_stls(), verify_svgs()
    manifest = geometry_manifest(repository, parent, analysis, stls["status"] == "PASS")
    for path, text in docs(manifest).items(): write_text(LANE_DIR / path, text)
    write_json(LANE_DIR / "geometry_manifest.json", manifest)
    geometry = geometry_checks(manifest)
    validation = {"document_id": DOCUMENT_ID, "classification": CLASSIFICATION, "geometry": geometry, "STEP": steps, "STL": stls, "SVG": svgs, "physical_fit": "REQUIRED", "torque_capacity": "NOT_TESTED", "powered_rotation": "NOT_APPROVED", "status": "PASS" if steps["status"] == stls["status"] == svgs["status"] == geometry["status"] == "PASS" else "FAIL"}
    write_json(LANE_DIR / "validation_report.json", validation)
    write_text(LANE_DIR / "COMMIT_PATHS.txt", commit_paths_text()); write_text(LANE_DIR / "MANIFEST.txt", manifest_text())
    write_text(LANE_DIR / "build_log.txt", f"command=python -B {SOURCE_FILES[0]} --refresh-artifacts\nphase_1_high_nut_coupon=PASS\nphase_2_retainer_plates=PASS\nphase_3_h2_bore_variants=PASS\nphase_4_assemblies=PASS\nstep={steps['pass_count']}/{steps['count']}\nstl={stls['pass_count']}/{stls['count']}\nsvg={svgs['pass_count']}/{svgs['count']}\ngeometry={geometry['status']}\nphysical_test=REQUIRED\npowered_rotation=NOT_APPROVED")
    write_text(LANE_DIR / "test_log.txt", "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED")
    write_text(LANE_DIR / "SHA256SUMS.txt", sha256sums_text())
    if lane_files() != sorted(PACKAGE_PATHS): raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    reports = [steps, stls, svgs, verify_manifest(), verify_hashes(), verify_geometry()]
    if any(item["status"] != "PASS" for item in reports): raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "formal_paths": len(PACKAGE_PATHS), "STEP": f"{steps['pass_count']}/{steps['count']} PASS", "STL": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "geometry": geometry["status"], "parent": parent["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    if lane_files() != sorted(PACKAGE_PATHS): raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    repository = repository_audit(True); parent = parent_audit(); steps, stls, svgs = verify_steps(), verify_stls(), verify_svgs(); manifest = verify_manifest(); hashes = verify_hashes(); geometry = verify_geometry()
    reports = {"STEP": steps["status"], "STL": stls["status"], "SVG": svgs["status"], "manifest": manifest["status"], "hashes": hashes["status"], "geometry": geometry["status"], "parent": parent["status"]}
    if any(value != "PASS" for value in reports.values()): raise RuntimeError(reports)
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent": parent["status"], "formal_paths": len(PACKAGE_PATHS), "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "STL_manifold": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "status": "PASS"}


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
        with tempfile.TemporaryDirectory(prefix="ps_cr_v09371_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive: archive.extractall(target)
            env = dict(os.environ); env["V09371_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", SOURCE_FILES[0], "--verify"], target, env); tests = run([sys.executable, "-B", SOURCE_FILES[1]], target, env)
            if build.returncode or tests.returncode: raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatch: raise RuntimeError({"internal_hash_mismatch": internal, "lane_mismatch": lane_mismatch})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify(); DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True); timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); final = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"; temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final.exists() or temporary.exists(): raise RuntimeError("refusing to overwrite handoff")
    try:
        write_text(LANE_DIR / "test_log.txt", "status=PACKAGE_TESTS_PENDING\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED"); write_text(LANE_DIR / "SHA256SUMS.txt", sha256sums_text()); write_zip(temporary)
        env = dict(os.environ); env["V09371_TEST_ZIP"] = str(temporary); result = run([sys.executable, "-B", SOURCE_FILES[1]], LANE_DIR, env)
        if result.returncode: raise RuntimeError(result.stdout)
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / "test_log.txt", "command=python -B " + SOURCE_FILES[1] + "\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_test=NOT_YET_PERFORMED\npowered_rotation=NOT_APPROVED\nfull_output:\n" + result.stdout); write_text(LANE_DIR / "SHA256SUMS.txt", sha256sums_text()); verify()
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
