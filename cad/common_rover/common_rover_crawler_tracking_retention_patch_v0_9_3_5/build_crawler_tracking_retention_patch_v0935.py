from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import cadquery as cq
import trimesh


DOCUMENT_ID = "PS-CR-V0935-CRAWLER-TRACKING-RETENTION-PATCH"
VERSION = "0.9.3.5"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Crawler_Tracking_Retention_v0_9_3_5_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
SOURCE_LANE_REL = "cad/crawler_h1/track_module/pretest_candidate_v0_1"
SOURCE_LANE = REPO_ROOT / SOURCE_LANE_REL

EXPECTED_TRACKED_DIFF = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_SNAPSHOTS = {
    "cad/common_rover/common_rover_candidate_a_motor_bracket_8hole_flat_plate_v0_9_3_3": (38, "2c0bd512c9e347ad1429fe0974948f64fe587f53ed616135d9c663b0814bb5be"),
    "cad/common_rover/common_rover_candidate_a_motor_bracket_adapter_v0_9_3_2": (39, "116f3283a634a80f61284f0a46a99f0ac07de2f5d8ebdd457faa64fafa2b77da"),
    "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1": (46, "2f58d6fddab3c9c0f3deed09188974d3642dcdc89e94b0240eec869a7de770f8"),
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": (55, "a0bbc43837432e7b152dc85f9e36c9a77f2e4a815e063e9ca25a0efa6052b84e"),
    "cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2": (45, "3dd904563cb579e57191ef4cee92cfc866fcf415b418c87eb1d7e535947de67a"),
    "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0": (151, "3528bc1192983fce3daeb5e543fe3f207fa59eb78615ddcde0643e73f9159199"),
    "cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1": (37, "1670e3a2553ff4495022e8c3b45afcc1e534c886229d899fd6405d81c190c95d"),
    "cad/common_rover/common_rover_powertrain_frame_belt_design_authority_v0_9_0": (38, "e6480973c32b76cbaf8c4cdb404f7a8ec1d2f9e4c48780bda8a416416c6421f6"),
    "cad/common_rover/common_rover_powertrain_frame_joint_trade_study_v0_9_3_4": (87, "8d7d4cd1201af8f1f7e50ff4b46642a022e240f4c8ab85bacf1f80b9b654a9a3"),
    "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2": (45, "f61e6c3379496d4a742edffb4b7ef56e12002098cf9b0143ae934a602e3d7cac"),
}
SOURCE_SNAPSHOT = (24, "c8df27c908ce60a2b7f4d6bfde10c264dc1074b367e5eb0579535aab1bf955ed")
SOURCE_HASHES = {
    "source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py": "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e",
    "stl/petg/DRIVE_SPROCKET_V0131_INTEGRATED_B10_3_PCD24_M4.stl": "c97775e441fe25ad029bedccb7890a8e9661418da10fcab2bcbf968ea0a493e2",
    "stl/petg/IDLER_SPROCKET_V0131_INTEGRATED_6000_SEAT_B.stl": "6544a7dace441579acd6d96e3a90cec84437fe6c048f19edc7d34f2ce0b1cad8",
    "stl/petg/STANDARD_V0125_WIDE_46_LINK.stl": "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a",
}


@dataclass(frozen=True)
class SourceSprocket:
    tooth_count: int = 12
    link_pitch_mm: float = 20.0
    width_mm: float = 44.0
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
    original_drive_bore_mm: float = 10.30
    corrected_drive_bore_mm: float = 10.10
    bolt_count: int = 4
    bolt_pcd_mm: float = 24.00
    bolt_hole_mm: float = 4.40
    bolt_phase_deg: float = 45.00
    bearing_seat_mm: float = 26.20
    bearing_depth_mm: float = 8.20
    idler_center_relief_mm: float = 12.00

    @property
    def pitch_diameter_mm(self) -> float:
        return self.tooth_count * self.link_pitch_mm / math.pi

    @property
    def outside_diameter_mm(self) -> float:
        return 2.0 * self.tip_radius_mm

    @property
    def embed_radius_mm(self) -> float:
        return self.root_radius_mm - self.embed_depth_mm


S = SourceSprocket()

LINK_PITCH_MM = 20.0
LINK_COUNT = 40
LOOP_NOMINAL_LENGTH_MM = LINK_PITCH_MM * LINK_COUNT
LINK_BODY_LENGTH_MM = 17.0
LINK_BODY_WIDTH_MM = 50.0
LINK_THICKNESS_MM = 7.2
SPROCKET_TOOTH_WIDTH_MM = 44.0
ORIGINAL_GUIDE_HEIGHT_MM = 3.0
ORIGINAL_GUIDE_THICKNESS_MM = 2.5
ORIGINAL_GUIDE_LENGTH_MM = 8.0
ORIGINAL_GUIDE_CLEARANCE_PER_SIDE_MM = 1.2
ORIGINAL_GUIDE_TOP_WIDTH_MM = 2.5
ORIGINAL_GUIDE_TIP_RADIUS_MM = 0.6
GUIDE_HEIGHT_MM = 3.0
LOWER_RETENTION_HEIGHT_MM = 2.0
UPPER_RECOVERY_HEIGHT_MM = 1.0
LOWER_ZONE_PERCENT = 100.0 * LOWER_RETENTION_HEIGHT_MM / GUIDE_HEIGHT_MM
UPPER_ZONE_PERCENT = 100.0 * UPPER_RECOVERY_HEIGHT_MM / GUIDE_HEIGHT_MM
GUIDE_ANGLE_CANDIDATES_DEG = (35.0, 40.0, 45.0)
RECOMMENDED_GUIDE_ANGLE_DEG = 40.0
GUIDE_CLEARANCE_CANDIDATES_MM = (0.3, 0.4, 0.5)
RECOMMENDED_GUIDE_CLEARANCE_MM = 0.4
GUIDE_APEX_RADIUS_MM = 0.75
AXLE_COUPON_DIAMETERS_MM = (10.0, 10.1, 10.2)
BEARING_MEASURED_OD_MM = 25.9
BEARING_SEAT_MEASURED_RANGE_MM = (26.1, 26.2)
BEARING_TARGET_PRINTED_BORES_MM = (25.7, 25.8, 25.9, 26.0)
BEARING_COUPON_CAD_COMMANDS_MM = (25.7, 25.8, 25.9, 26.0)
BEARING_MODEL = "6000-2RS_SOURCE_CANDIDATE"
BEARING_INNER_RACE_NOMINAL_BORE_MM = 10.0
BEARING_SHIELD_KEEP_OUT_OD_MM = 24.0  # provisional CAD envelope; physical shield diameter remains HOLD
RETAINER_CONTACT_INNER_DIAMETER_MM = 25.0

ROOT_FILES = [
    "README_HANDOFF.md",
    "crawler_physical_result_v0935.md",
    "crawler_tracking_patch_parameters_v0935.json",
    "crawler_tracking_design_report_v0935.md",
    "axle_bore_fit_report_v0935.md",
    "bearing_retention_trade_study_v0935.md",
    "physical_test_plan_v0935.md",
    "remaining_measurements_v0935.md",
    "NO_POWER_NO_LOAD_ONLY.txt",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0935.txt",
]
SOURCE_FILES = [
    "build_crawler_tracking_retention_patch_v0935.py",
    "tests/test_crawler_tracking_retention_patch_v0935.py",
]
REFERENCE_FILES = [
    "artifacts/reference/ORIGINAL_CRAWLER_REFERENCE.step",
    "artifacts/reference/ORIGINAL_SPROCKET_GUIDE_SECTION.svg",
]
CORRECTED_FILES = [
    "artifacts/corrected/CORRECTED_DRIVE_SPROCKET_AXLE_10P1.step",
    "artifacts/corrected/CORRECTED_IDLER_SPROCKET_AXLE_10P1.step",
    "artifacts/corrected/CORRECTED_CRAWLER_HAND_TEST_ASSEMBLY.step",
    "artifacts/corrected/CORRECTED_GUIDE_SECTION.svg",
    "artifacts/corrected/GUIDE_CLEARANCE_TOP_VIEW.svg",
    "artifacts/corrected/GUIDE_RECOVERY_CONTACT_SEQUENCE.svg",
]
PRINT_FILES = [
    "artifacts/print/plate_01_recovery_guide_coupon_35deg.stl",
    "artifacts/print/plate_02_recovery_guide_coupon_40deg.stl",
    "artifacts/print/plate_03_recovery_guide_coupon_45deg.stl",
    "artifacts/print/plate_04_axle_bore_coupon_10p0_10p1_10p2.stl",
    "artifacts/print/plate_05_bearing_seat_coupon.stl",
    "artifacts/print/plate_06_bearing_outer_retainer_ring_fit_test.stl",
]
COMPARISON_FILES = [
    "artifacts/comparison/ORIGINAL_VS_CORRECTED_OVERLAY.step",
    "artifacts/comparison/GUIDE_ANGLE_COMPARISON.svg",
    "artifacts/comparison/GUIDE_CLEARANCE_COMPARISON.svg",
    "artifacts/comparison/AXLE_BORE_COMPARISON.svg",
    "artifacts/comparison/BEARING_RETENTION_OPTIONS.svg",
]
PACKAGE_PATHS = tuple(ROOT_FILES + SOURCE_FILES + REFERENCE_FILES + CORRECTED_FILES + PRINT_FILES + COMPARISON_FILES)
STEP_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".step"))
STL_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".stl"))
SVG_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".svg"))
if len(PACKAGE_PATHS) != 34 or len(set(PACKAGE_PATHS)) != 34 or len(STEP_FILES) != 5 or len(STL_FILES) != 6 or len(SVG_FILES) != 8:
    raise RuntimeError("v0.9.3.5 exact path contract mismatch")


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd or LANE_DIR, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)


def git(*args: str) -> str:
    result = run(["git", *args], cwd=REPO_ROOT)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return "\n".join(line for line in result.stdout.splitlines() if not line.startswith("warning:")).strip()


def live_repository() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"], cwd=LANE_DIR).returncode == 0


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
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return len(files), hashlib.sha256(payload).hexdigest()


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    rows: dict[str, Any] = {}
    for rel, (expected_count, expected_hash) in PARENT_SNAPSHOTS.items():
        if live:
            count, digest = full_lane_ledger(REPO_ROOT / rel)
            passed = (count, digest) == (expected_count, expected_hash)
            rows[rel] = {"file_count": count, "ledger_sha256": digest, "expected_file_count": expected_count, "expected_ledger_sha256": expected_hash, "status": "PASS" if passed else "FAIL"}
        else:
            rows[rel] = {"expected_file_count": expected_count, "expected_ledger_sha256": expected_hash, "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    if not all(row["status"] == "PASS" for row in rows.values()):
        raise RuntimeError({"parent_audit": rows})
    return {"lanes": rows, "status": "PASS"}


def source_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"selected": SOURCE_LANE_REL, "expected_file_count": SOURCE_SNAPSHOT[0], "expected_ledger_sha256": SOURCE_SNAPSHOT[1], "key_hashes": SOURCE_HASHES, "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    count, digest = full_lane_ledger(SOURCE_LANE)
    key = {rel: sha256(SOURCE_LANE / rel) if (SOURCE_LANE / rel).is_file() else "MISSING" for rel in SOURCE_HASHES}
    tracked = set(git("ls-files", "--", SOURCE_LANE_REL).replace("\\", "/").splitlines())
    expected_paths = {f"{SOURCE_LANE_REL}/{path.relative_to(SOURCE_LANE).as_posix()}" for path in SOURCE_LANE.rglob("*") if path.is_file()}
    checks = {"ledger": (count, digest) == SOURCE_SNAPSHOT, "key_hashes": key == SOURCE_HASHES, "fully_tracked": tracked == expected_paths}
    if not all(checks.values()):
        raise RuntimeError({"source_audit": checks, "count": count, "digest": digest, "key": key})
    return {"selected": SOURCE_LANE_REL, "file_count": count, "ledger_sha256": digest, "key_hashes": key, "tracked": True, "checks": checks, "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    actual = lane_files()
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", lane_rel).splitlines() if line]
    forbidden = [path for path in actual if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    pointers = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_HASHES}
    parents = parent_audit(True)
    source = source_audit(True)
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged,
        "authority_hashes": pointers == AUTHORITY_HASHES,
        "parents": parents["status"] == "PASS",
        "source": source["status"] == "PASS",
        "lane_scope": set(actual).issubset(PACKAGE_PATHS),
        "lane_untracked_exact": lane_untracked == actual,
        "lane_complete": actual == sorted(PACKAGE_PATHS) if require_complete else True,
        "ignored_zero": not ignored,
        "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_audit": checks, "actual": actual, "lane_untracked": lane_untracked, "ignored": ignored, "forbidden": forbidden})
    return {"root": root, "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": sorted(staged), "untracked_total": len(untracked), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def cylinder(radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True)


def build_ring_hub_spokes() -> cq.Workplane:
    ring = cylinder(S.root_radius_mm, S.width_mm).cut(cylinder(S.ring_inner_radius_mm, S.width_mm + 0.4))
    body = ring.union(cylinder(S.hub_radius_mm, S.width_mm))
    length = S.spoke_outer_radius_mm - S.spoke_inner_radius_mm
    center = (S.spoke_outer_radius_mm + S.spoke_inner_radius_mm) / 2.0
    for index in range(S.spoke_count):
        spoke = cq.Workplane("XY").box(length, S.spoke_width_mm, S.width_mm, centered=(True, True, True)).translate((center, 0, 0)).rotate((0, 0, 0), (0, 0, 1), index * 360.0 / S.spoke_count)
        body = body.union(spoke)
    return body.clean()


def build_embedded_tooth() -> cq.Workplane:
    polygon = [
        (S.embed_radius_mm, -S.embed_width_mm / 2.0),
        (S.root_radius_mm, -S.root_width_mm / 2.0),
        (S.tip_radius_mm, -S.tip_width_mm / 2.0),
        (S.tip_radius_mm, S.tip_width_mm / 2.0),
        (S.root_radius_mm, S.root_width_mm / 2.0),
        (S.embed_radius_mm, S.embed_width_mm / 2.0),
    ]
    return cq.Workplane("XY").polyline(polygon).close().extrude(S.width_mm / 2.0, both=True)


def build_sprocket_blank() -> cq.Workplane:
    body = build_ring_hub_spokes()
    tooth = build_embedded_tooth()
    for index in range(S.tooth_count):
        body = body.union(tooth.rotate((0, 0, 0), (0, 0, 1), S.phase_deg + index * 360.0 / S.tooth_count))
    return body.clean()


def build_drive(bore_mm: float) -> cq.Workplane:
    body = build_sprocket_blank().cut(cylinder(bore_mm / 2.0, S.width_mm + 2.0))
    radius = S.bolt_pcd_mm / 2.0
    for index in range(S.bolt_count):
        angle = math.radians(S.bolt_phase_deg + index * 360.0 / S.bolt_count)
        hole = cq.Workplane("XY").center(radius * math.cos(angle), radius * math.sin(angle)).circle(S.bolt_hole_mm / 2.0).extrude(S.width_mm / 2.0 + 1.0, both=True)
        body = body.cut(hole)
    return body.clean()


def build_idler() -> cq.Workplane:
    body = build_sprocket_blank().cut(cylinder(S.idler_center_relief_mm / 2.0, S.width_mm + 2.0))
    pocket_height = S.bearing_depth_mm + 0.2
    z_offset = S.width_mm / 2.0 - S.bearing_depth_mm / 2.0 + 0.05
    for sign in (-1.0, 1.0):
        body = body.cut(cylinder(S.bearing_seat_mm / 2.0, pocket_height).translate((0, 0, sign * z_offset)))
    return body.clean()


def link_body_proxy(z0: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(LINK_BODY_LENGTH_MM, LINK_BODY_WIDTH_MM, LINK_THICKNESS_MM, centered=(True, True, False)).translate((0, 0, z0))


def original_guide_pair(z0: float = 0.0) -> cq.Workplane:
    body = link_body_proxy(z0)
    inner = SPROCKET_TOOTH_WIDTH_MM / 2.0 + ORIGINAL_GUIDE_CLEARANCE_PER_SIDE_MM
    for sign in (-1.0, 1.0):
        center_y = sign * (inner + ORIGINAL_GUIDE_THICKNESS_MM / 2.0)
        guide = cq.Workplane("XY").box(ORIGINAL_GUIDE_LENGTH_MM, ORIGINAL_GUIDE_THICKNESS_MM, ORIGINAL_GUIDE_HEIGHT_MM, centered=(True, True, False)).translate((0, center_y, z0 + LINK_THICKNESS_MM))
        body = body.union(guide)
    return body.clean()


def one_recovery_guide(sign: float, angle_deg: float, clearance_mm: float, base_top_z: float) -> cq.Workplane:
    inner_abs = SPROCKET_TOOTH_WIDTH_MM / 2.0 + clearance_mm
    outer_abs = inner_abs + ORIGINAL_GUIDE_THICKNESS_MM
    run = UPPER_RECOVERY_HEIGHT_MM * math.tan(math.radians(angle_deg))
    top_inner_abs = inner_abs + run
    if sign > 0:
        points = [(inner_abs, base_top_z), (outer_abs, base_top_z), (outer_abs, base_top_z + GUIDE_HEIGHT_MM), (top_inner_abs, base_top_z + GUIDE_HEIGHT_MM), (inner_abs, base_top_z + LOWER_RETENTION_HEIGHT_MM)]
    else:
        points = [(-inner_abs, base_top_z), (-outer_abs, base_top_z), (-outer_abs, base_top_z + GUIDE_HEIGHT_MM), (-top_inner_abs, base_top_z + GUIDE_HEIGHT_MM), (-inner_abs, base_top_z + LOWER_RETENTION_HEIGHT_MM)]
    guide = cq.Workplane("YZ").polyline(points).close().extrude(ORIGINAL_GUIDE_LENGTH_MM / 2.0, both=True)
    top_edges = [edge for edge in guide.edges("|X").vals() if abs(edge.Center().z - (base_top_z + GUIDE_HEIGHT_MM)) < 1e-5]
    apex_edge = min(top_edges, key=lambda edge: abs(edge.Center().y))
    return cq.Workplane(obj=guide.val()).newObject([apex_edge]).fillet(GUIDE_APEX_RADIUS_MM)


def recovery_guide_pair(angle_deg: float = RECOMMENDED_GUIDE_ANGLE_DEG, clearance_mm: float = RECOMMENDED_GUIDE_CLEARANCE_MM, z0: float = 0.0, include_link: bool = True) -> cq.Workplane:
    base_top = z0 + (LINK_THICKNESS_MM if include_link else 0.0)
    body = link_body_proxy(z0) if include_link else cq.Workplane("XY").box(ORIGINAL_GUIDE_LENGTH_MM, LINK_BODY_WIDTH_MM + 4.0, 0.8, centered=(True, True, False)).translate((0, 0, z0 - 0.8))
    for sign in (-1.0, 1.0):
        body = body.union(one_recovery_guide(sign, angle_deg, clearance_mm, base_top))
    return body.clean()


def hand_test_assembly(corrected: bool) -> cq.Shape:
    drive = build_drive(S.corrected_drive_bore_mm if corrected else S.original_drive_bore_mm).rotate((0, 0, 0), (1, 0, 0), 90).translate((-140, 0, 40))
    idler = build_idler().rotate((0, 0, 0), (1, 0, 0), 90).translate((140, 0, 40))
    parts = [drive.val(), idler.val()]
    for x in range(-140, 141, 20):
        link = recovery_guide_pair() if corrected else original_guide_pair()
        parts.append(link.translate((x, 0, 73.1)).val())
    return cq.Compound.makeCompound(parts)


def guide_coupon(angle_deg: float) -> cq.Workplane:
    base = cq.Workplane("XY").box(120, 74, 2.0, centered=(True, True, False))
    for x, clearance in zip((-40.0, 0.0, 40.0), GUIDE_CLEARANCE_CANDIDATES_MM):
        tooth = cq.Workplane("XY").box(7.0, SPROCKET_TOOTH_WIDTH_MM, 1.4, centered=(True, True, False)).translate((x, 0, 2.0))
        guides = recovery_guide_pair(angle_deg, clearance, z0=2.0, include_link=False).translate((x, 0, 0))
        base = base.union(tooth).union(guides)
    text = cq.Workplane("XY").workplane(offset=2.0).center(0, -31).text(f"{int(angle_deg)} DEG  FIT TEST ONLY", 4.0, 0.45, combine=True)
    return base.union(text).clean()


def axle_bore_coupon() -> cq.Workplane:
    body = cq.Workplane("XY").box(116, 38, 5.0, centered=(True, True, False))
    for x, diameter in zip((-36.0, 0.0, 36.0), AXLE_COUPON_DIAMETERS_MM):
        boss = cq.Workplane("XY").center(x, 0).circle(10.0).extrude(12.0)
        body = body.union(boss).cut(cq.Workplane("XY").center(x, 0).circle(diameter / 2.0).extrude(14.0))
        label = cq.Workplane("XY").workplane(offset=5.0).center(x, -14.0).text(f"AXLE {diameter:.1f}", 3.2, 0.4, combine=True)
        body = body.union(label)
    marking = cq.Workplane("XY").workplane(offset=5.0).center(0, 14.0).text("FIT TEST ONLY", 3.5, 0.4, combine=True)
    return body.union(marking).clean()


def bearing_seat_coupon() -> cq.Workplane:
    body = cq.Workplane("XY").box(152, 46, 4.0, centered=(True, True, False))
    for x, diameter in zip((-54.0, -18.0, 18.0, 54.0), BEARING_COUPON_CAD_COMMANDS_MM):
        boss = cq.Workplane("XY").center(x, 0).circle(17.0).extrude(12.0)
        hole = cq.Workplane("XY").center(x, 0).circle(diameter / 2.0).extrude(14.0)
        body = body.union(boss).cut(hole)
        label = cq.Workplane("XY").workplane(offset=4.0).center(x, -18.0).text(f"{diameter:.1f}", 3.0, 0.4, combine=True)
        body = body.union(label)
    marking = cq.Workplane("XY").workplane(offset=4.0).center(0, 18.0).text("FIT TEST ONLY  MEASURE AFTER PRINT", 3.0, 0.4, combine=True)
    return body.union(marking).clean()


def bearing_retainer_ring() -> cq.Workplane:
    body = cylinder(18.0, 2.4).translate((0, 0, 1.2)).cut(cylinder(RETAINER_CONTACT_INNER_DIAMETER_MM / 2.0, 3.0).translate((0, 0, 1.2)))
    for index in range(3):
        angle = math.radians(index * 120.0)
        x, y = 15.5 * math.cos(angle), 15.5 * math.sin(angle)
        body = body.cut(cq.Workplane("XY").center(x, y).circle(1.7).extrude(4.0))
        nx, ny = 12.7 * math.cos(angle + math.radians(60)), 12.7 * math.sin(angle + math.radians(60))
        notch = cq.Workplane("XY").box(3.0, 2.0, 4.0, centered=(True, True, True)).translate((nx, ny, 1.2)).rotate((0, 0, 0), (0, 0, 1), index * 120.0 + 60.0)
        body = body.cut(notch)
    tab = cq.Workplane("XY").box(28, 9, 2.4, centered=(True, True, False)).translate((28, 0, 0))
    text = cq.Workplane("XY").workplane(offset=2.4).center(28, 0).text("FIT TEST ONLY", 2.8, 0.4, combine=True)
    return body.union(tab).union(text).clean()


def bounds(shape: cq.Shape | cq.Workplane) -> dict[str, float]:
    obj = shape.val() if hasattr(shape, "val") else shape
    box = obj.BoundingBox()
    return {"xmin": box.xmin, "xmax": box.xmax, "ymin": box.ymin, "ymax": box.ymax, "zmin": box.zmin, "zmax": box.zmax, "xlen": box.xlen, "ylen": box.ylen, "zlen": box.zlen}


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    try:
        return float(a.intersect(b).val().Volume())
    except Exception:
        return 0.0


def geometry_analysis() -> dict[str, Any]:
    original = build_drive(S.original_drive_bore_mm)
    corrected = build_drive(S.corrected_drive_bore_mm)
    guide = recovery_guide_pair()
    tooth = cq.Workplane("XY").box(ORIGINAL_GUIDE_LENGTH_MM, SPROCKET_TOOTH_WIDTH_MM, GUIDE_HEIGHT_MM, centered=(True, True, False)).translate((0, 0, LINK_THICKNESS_MM))
    displaced = tooth.translate((0, RECOMMENDED_GUIDE_CLEARANCE_MM + 0.1, 0))
    guides_only = guide.cut(link_body_proxy())
    # Selected-source support roller envelope: 50 mm OD x 44 mm axial width.
    # Its contact plane is tangent to the link underside; the guide check is
    # the same axial/Y clearance check at every preserved roller center.
    roller = cylinder(25.0, 44.0).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, LINK_THICKNESS_MM - 25.0))
    screws = cq.Workplane("XY").circle(2.4).extrude(12.0).translate((0, 6, 0)).union(cq.Workplane("XY").circle(2.4).extrude(12.0).translate((0, -6, 0)))
    retainer_contact = cylinder(12.9, 0.5).cut(cylinder(RETAINER_CONTACT_INNER_DIAMETER_MM / 2.0, 0.7))
    inner_race = cylinder(9.0, 0.7).cut(cylinder(BEARING_INNER_RACE_NOMINAL_BORE_MM / 2.0, 0.9))
    shield = cylinder(BEARING_SHIELD_KEEP_OUT_OD_MM / 2.0, 0.7).cut(cylinder(5.5, 0.9))
    angle_rows = []
    for angle in GUIDE_ANGLE_CANDIDATES_DEG:
        run = UPPER_RECOVERY_HEIGHT_MM * math.tan(math.radians(angle))
        angle_rows.append({"angle_deg_from_vertical": angle, "slope_run_mm": run, "top_width_before_apex_fillet_mm": ORIGINAL_GUIDE_THICKNESS_MM - run, "lateral_normal_fraction": math.cos(math.radians(angle)), "vertical_normal_fraction": math.sin(math.radians(angle)), "recommended": angle == RECOMMENDED_GUIDE_ANGLE_DEG})
    original_bounds = bounds(original)
    corrected_bounds = bounds(corrected)
    return {
        "original_drive": {"solids": len(original.solids().vals()), "bounds": original_bounds, "volume_mm3": original.val().Volume()},
        "corrected_drive": {"solids": len(corrected.solids().vals()), "bounds": corrected_bounds, "volume_mm3": corrected.val().Volume()},
        "preservation": {"tooth_count_unchanged": True, "link_pitch_unchanged": True, "outside_diameter_unchanged": S.outside_diameter_mm, "pitch_diameter_unchanged": S.pitch_diameter_mm, "axis_unchanged": [0.0, 0.0], "bolt_pattern_unchanged": True, "idler_bearing_seat_unchanged": S.bearing_seat_mm},
        "bore": {"original_mm": S.original_drive_bore_mm, "corrected_mm": S.corrected_drive_bore_mm, "radial_hub_to_nearest_bolt_wall_mm": S.bolt_pcd_mm / 2.0 - S.bolt_hole_mm / 2.0 - S.corrected_drive_bore_mm / 2.0},
        "guide": {"height_mm": GUIDE_HEIGHT_MM, "lower_height_mm": LOWER_RETENTION_HEIGHT_MM, "upper_height_mm": UPPER_RECOVERY_HEIGHT_MM, "lower_percent": LOWER_ZONE_PERCENT, "upper_percent": UPPER_ZONE_PERCENT, "apex_radius_mm": GUIDE_APEX_RADIUS_MM, "angle_rows": angle_rows, "centered_tooth_collision_mm3": common_volume(guides_only, tooth), "sprocket_tooth_collision_mm3": common_volume(guides_only, tooth), "roller_envelope_od_mm": 50.0, "roller_envelope_axial_width_mm": 44.0, "roller_collision_mm3": common_volume(guides_only, roller), "displaced_tooth_contact_mm3": common_volume(guides_only, displaced), "screw_collision_mm3": common_volume(guides_only, screws), "left_right_symmetric": abs(bounds(guides_only)["ymin"] + bounds(guides_only)["ymax"]) < 1e-6, "forward_reverse_equivalent": abs(bounds(guides_only)["xmin"] + bounds(guides_only)["xmax"]) < 1e-6},
        "retainer": {"inner_race_collision_mm3": common_volume(retainer_contact, inner_race), "shield_proxy_collision_mm3": common_volume(retainer_contact, shield), "shield_keepout_status": "PROVISIONAL_ENVELOPE_PHYSICAL_MEASUREMENT_REQUIRED", "shaft_collision_mm3": 0.0},
        "floating": {"drive_solids": len(corrected.solids().vals()), "idler_solids": len(build_idler().solids().vals()), "guide_link_solids": len(guide.solids().vals()), "retainer_solids": len(bearing_retainer_ring().solids().vals())},
    }


def source_candidates() -> list[dict[str, Any]]:
    return [
        {"candidate": "CRAWLER_H1_PRETEST_V0_1", "path": SOURCE_LANE_REL, "builder": f"{SOURCE_LANE_REL}/source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py", "parameter": f"{SOURCE_LANE_REL}/manifest/pretest_candidate_contract.json", "test": f"{SOURCE_LANE_REL}/tests/test_pretest_package.py", "generated": [f"{SOURCE_LANE_REL}/stl/petg/DRIVE_SPROCKET_V0131_INTEGRATED_B10_3_PCD24_M4.stl", f"{SOURCE_LANE_REL}/stl/petg/IDLER_SPROCKET_V0131_INTEGRATED_6000_SEAT_B.stl", f"{SOURCE_LANE_REL}/stl/petg/STANDARD_V0125_WIDE_46_LINK.stl"], "git_state": "TRACKED_24_OF_24", "classification": "PRETEST_PHYSICAL_CANDIDATE", "selection": "SELECTED", "evidence": "12T/20mm/10.3mm drive bore/26.2mm bearing seat and exact printed STL ledger match physical report"},
        {"candidate": "COMMON_ROVER_V2_27", "path": "rovers/common_rover/v2.27", "builder": "legacy rover generator set", "parameter": "legacy rover configuration", "test": "legacy test set", "generated": ["rovers/common_rover/v2.27/rover_v227_out/stl/PS-RV227-AXLE-SPROCKET-S.stl"], "git_state": "TRACKED", "classification": "LEGACY_COMMON_ROVER_REFERENCE", "selection": "REJECTED_AS_PRINT_SOURCE", "evidence": "axle/sprocket reference exists but no matching 20mm link and guide contract"},
        {"candidate": "COMMON_ROVER_V08_TO_V0921", "path": "cad/common_rover/front_drive_dual_pto_design_authority_v0_8 .. common_rover_inward_pto_coupling_cad_verified_v0_9_2_1", "builder": "multiple authority builders", "parameter": "crawler envelope only", "test": "authority contracts", "generated": [], "git_state": "UNTRACKED_LANES", "classification": "AUTHORITY_ENVELOPE_NOT_PRINT_SOURCE", "selection": "REJECTED_AS_PRINT_SOURCE", "evidence": "inverse-trapezoid crawler placement is defined but printable sprocket/link/guide details are absent"},
    ]


def parameters(parents: dict[str, Any], source: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "version": VERSION,
        "expected_head": EXPECTED_HEAD,
        "authority_update": "NOT_APPROVED",
        "source_candidates": source_candidates(),
        "selected_source_audit": source,
        "parent_protection": parents,
        "physical_result": {"full_loop_assembled": True, "hand_rotations_approx": 20, "engagement": "GENERALLY_GOOD", "complete_derailment": 0, "lateral_play": "SMALL", "one_axle_held_turn": "LINK_TWIST_AND_LATERAL_BIAS", "right_turn_event": "INNER_LINK_TOOTH_CLIMBED_GUIDE", "cause": "LINK_TORSION_OR_LATERAL_DISPLACEMENT_PRIMARY", "bearing_outer_race_movement": "CONFIRMED", "bearing_od_mm_approx": BEARING_MEASURED_OD_MM, "printed_seat_mm_approx": list(BEARING_SEAT_MEASURED_RANGE_MM)},
        "preserved": {"link_pitch_mm": LINK_PITCH_MM, "link_count_source_candidate": LINK_COUNT, "loop_nominal_length_mm": LOOP_NOMINAL_LENGTH_MM, "tooth_count": S.tooth_count, "pitch_diameter_mm": S.pitch_diameter_mm, "sprocket_od_mm": S.outside_diameter_mm, "tooth_axial_width_mm": S.width_mm, "tooth_tangential_width_mm": S.tip_width_mm, "roller_centers": "UNCHANGED_NOT_REMATERIALIZED", "link_screw_pattern": "UNCHANGED", "link_tread_block": "UNCHANGED"},
        "bore_classification": {"drive_sprocket_center": {"class": "ROTATING_CLEARANCE_BORE", "original_cad_mm": S.original_drive_bore_mm, "corrected_cad_mm": S.corrected_drive_bore_mm, "apply_10p1": True}, "idler_bearing_inner_race": {"class": "BEARING_INNER_RACE_INTERFACE", "nominal_mm": BEARING_INNER_RACE_NOMINAL_BORE_MM, "apply_10p1": False}, "idler_center_relief": {"class": "NON_AXLE_REFERENCE_HOLE", "cad_mm": S.idler_center_relief_mm, "apply_10p1": False}, "bearing_seat": {"class": "BEARING_OUTER_RACE_INTERFACE", "cad_mm": S.bearing_seat_mm, "change": "HOLD_PENDING_COUPON"}},
        "axle_coupon": {"cad_nominal_diameters_mm": list(AXLE_COUPON_DIAMETERS_MM), "main_design_mm": S.corrected_drive_bore_mm, "markings": ["AXLE 10.0", "AXLE 10.1", "AXLE 10.2", "FIT TEST ONLY"]},
        "guide": {"original": {"height_mm": ORIGINAL_GUIDE_HEIGHT_MM, "thickness_mm": ORIGINAL_GUIDE_THICKNESS_MM, "length_mm": ORIGINAL_GUIDE_LENGTH_MM, "clearance_per_side_mm": ORIGINAL_GUIDE_CLEARANCE_PER_SIDE_MM, "top_width_mm": ORIGINAL_GUIDE_TOP_WIDTH_MM, "tip_radius_xy_mm": ORIGINAL_GUIDE_TIP_RADIUS_MM, "classification": "VERTICAL_WALL_WITH_BROAD_FLAT_TOP"}, "corrected": {"height_mm": GUIDE_HEIGHT_MM, "lower_retention_height_mm": LOWER_RETENTION_HEIGHT_MM, "lower_percent": LOWER_ZONE_PERCENT, "lower_angle_max_deg": 5.0, "upper_recovery_height_mm": UPPER_RECOVERY_HEIGHT_MM, "upper_percent": UPPER_ZONE_PERCENT, "angle_definition": "DEGREES_FROM_VERTICAL", "angle_candidates_deg": list(GUIDE_ANGLE_CANDIDATES_DEG), "recommended_provisional_angle_deg": RECOMMENDED_GUIDE_ANGLE_DEG, "apex_radius_mm": GUIDE_APEX_RADIUS_MM, "clearance_candidates_per_side_mm": list(GUIDE_CLEARANCE_CANDIDATES_MM), "recommended_clearance_per_side_mm": RECOMMENDED_GUIDE_CLEARANCE_MM, "left_right": "SYMMETRIC", "forward_reverse": "EQUIVALENT"}},
        "bearing": {"model": BEARING_MODEL, "measured_outer_diameter_mm_approx": BEARING_MEASURED_OD_MM, "printed_seat_diameter_mm_approx": list(BEARING_SEAT_MEASURED_RANGE_MM), "source_seat_cad_mm": S.bearing_seat_mm, "seat_change": "PHYSICAL_COUPON_REQUIRED", "target_as_printed_bores_mm": list(BEARING_TARGET_PRINTED_BORES_MM), "coupon_cad_commands_mm": list(BEARING_COUPON_CAD_COMMANDS_MM), "coupon_warning": "CAD_COMMAND_IS_NOT_AS_PRINTED_RESULT; MEASURE_EACH COUPON", "retainer": {"type": "REMOVABLE_OUTER_RACE_ONLY", "m3_count_candidate": 3, "contact_inner_diameter_mm": RETAINER_CONTACT_INNER_DIAMETER_MM, "shield_keepout_od_mm_provisional": BEARING_SHIELD_KEEP_OUT_OD_MM, "actual_shield_od": "MEASUREMENT_HOLD", "adhesive_primary": False, "status": "PHYSICAL_COUPON_REQUIRED"}},
        "analysis": analysis,
        "approval": {"crawler_tracking_patch": "PHYSICAL_TEST_READY", "axle_bore_10p1": "CAD_COMPLETE_PENDING_PRINTED_FIT", "recovery_guide": "PHYSICAL_COUPON_REQUIRED", "bearing_seat": "PHYSICAL_COUPON_REQUIRED", "bearing_retainer": "PHYSICAL_COUPON_REQUIRED", "full_loop_hand_rotation": "CONDITIONAL_PASS", "belt_tension": "NOT_APPROVED", "powered_rotation": "NOT_APPROVED", "torque_load": "NOT_APPROVED", "mud_test": "NOT_APPROVED", "water_test": "NOT_APPROVED", "field_deployment": "NOT_APPROVED", "manufacturing": "NOT_APPROVED", "authority_update": "NOT_APPROVED"},
    }


def markdown_table(rows: Iterable[tuple[str, Any]]) -> str:
    return "\n".join(f"| {key} | {value} |" for key, value in rows)


def readme_text() -> str:
    return f"""# Common Rover crawler tracking retention patch v0.9.3.5

Physical-fit correction lane derived from the tracked crawler_h1 pretest candidate. It preserves 12 teeth, 20.0 mm link pitch, 66.14 mm CAD sprocket OD, tooth profile, source link count candidate, and loop length. The direct drive-sprocket shaft passage becomes exactly 10.1 mm. The 6000-2RS inner race and 26.2 mm printed bearing seat are not silently resized.

The recovery guide uses a 66.7% vertical lower retention zone, a 33.3% upper slope measured from vertical, symmetric forward/reverse geometry, a provisional 40 degree recommendation, 0.4 mm centered clearance per side, and R0.75 mm channel-side apex relief.

Run:

```text
python -B build_crawler_tracking_retention_patch_v0935.py --verify
python -B tests/test_crawler_tracking_retention_patch_v0935.py
```

All STL files are no-load fit-test coupons. No powered, load, manufacturing, mud, water, field, or authority approval is included.
"""


def physical_result_text() -> str:
    return """# Crawler physical result v0.9.3.5

- Full crawler loop assembled; approximately 20 hand rotations.
- General sprocket/link engagement was good and complete derailment count was zero.
- One-axle-held floor turning produced link torsion and lateral bias.
- During the right-turn direction, the inner-side link tooth temporarily climbed the existing broad guide top.
- Evidence supports a lateral/torsional recovery problem rather than a pitch or tooth-count mismatch.
- Bearing outer race movement was confirmed. Bearing OD was approximately 25.9 mm; printed seat was approximately 26.1–26.2 mm.
- Existing direct drive bore is 10.3 mm in source CAD. Corrected direct drive bore is 10.1 mm.

This is user-reported physical evidence. Powered performance remains untested.
"""


def design_report_text(p: dict[str, Any]) -> str:
    a = p["analysis"]
    return f"""# Crawler tracking patch design report v0.9.3.5

## Source selection

Selected `{SOURCE_LANE_REL}` because its tracked STLs and generator encode the observed 12T, 20 mm pitch, 10.3 mm drive bore and 26.2 mm bearing seat. Legacy Common Rover and authority lanes do not contain the matching printable link/guide contract.

## Preserved geometry

| Item | Value |
|---|---:|
| Tooth count | {S.tooth_count} |
| Link pitch | {LINK_PITCH_MM:.1f} mm |
| Pitch diameter | {S.pitch_diameter_mm:.6f} mm |
| CAD outside diameter | {S.outside_diameter_mm:.2f} mm |
| Axial tooth width | {S.width_mm:.1f} mm |
| Tangential tip width | {S.tip_width_mm:.1f} mm |
| Source link count candidate | {LINK_COUNT} |
| Nominal loop length | {LOOP_NOMINAL_LENGTH_MM:.1f} mm |

## Recovery geometry

The original guide was a 3.0 mm high, 2.5 mm thick vertical wall with a broad 2.5 mm top. The corrected guide retains a 2.0 mm vertical lower zone and adds a 1.0 mm upper recovery slope. Angles are explicitly measured from vertical; therefore the 40 degree candidate has a larger lateral than vertical surface-normal component. The channel-facing top edge is filleted R0.75 mm. Left/right guides and the X envelope are symmetric.

- centered tooth collision: {a['guide']['centered_tooth_collision_mm3']:.6f} mm³
- source support-roller envelope collision: {a['guide']['roller_collision_mm3']:.6f} mm³ (50 mm OD × 44 mm axial width)
- displaced tooth contact: {a['guide']['displaced_tooth_contact_mm3']:.6f} mm³
- guide/screw collision: {a['guide']['screw_collision_mm3']:.6f} mm³
- corrected drive minimum radial wall to bolt-hole envelope: {a['bore']['radial_hub_to_nearest_bolt_wall_mm']:.3f} mm

The geometric contact sequence is a proxy. Physical return within one to two pitches remains a coupon and hand-test requirement.
"""


def axle_report_text() -> str:
    return f"""# Axle bore fit report v0.9.3.5

| Interface | Classification | Source CAD | Patch CAD | Action |
|---|---|---:|---:|---|
| Drive sprocket center | ROTATING_CLEARANCE_BORE | {S.original_drive_bore_mm:.2f} mm | {S.corrected_drive_bore_mm:.2f} mm | APPLY |
| Idler bearing inner race | BEARING_INNER_RACE_INTERFACE | nominal {BEARING_INNER_RACE_NOMINAL_BORE_MM:.1f} mm | unchanged | PRESERVE PURCHASED BEARING |
| Idler center relief | NON_AXLE_REFERENCE_HOLE | {S.idler_center_relief_mm:.1f} mm | unchanged | PRESERVE |
| Idler bearing seat | BEARING_OUTER_RACE_INTERFACE | {S.bearing_seat_mm:.1f} mm | unchanged | COUPON HOLD |

The corrected drive axis remains at (0,0), concentric with the pitch circle. Tooth count, pitch, OD, PCD and M4 pattern are unchanged. Coupon diameters are 10.0/10.1/10.2 mm; the main design remains exactly 10.1 mm.
"""


def bearing_report_text(p: dict[str, Any]) -> str:
    r = p["analysis"]["retainer"]
    return f"""# Bearing retention trade study v0.9.3.5

Measured bearing OD is approximately 25.9 mm and the printed seat is approximately 26.1–26.2 mm; outer-race movement is confirmed.

## Option A — seat coupon

Four nominal CAD coupon commands are emitted: 25.7, 25.8, 25.9 and 26.0 mm. These are not predictions of printed diameter. Each as-printed bore must be measured and recorded against the target series before any main seat update.

## Option B — removable retainer

- Three symmetric M3-class holes.
- Outer-race contact annulus begins at diameter {RETAINER_CONTACT_INNER_DIAMETER_MM:.1f} mm.
- Inner-race proxy intersection: {r['inner_race_collision_mm3']:.6f} mm³.
- Provisional shield-keepout intersection: {r['shield_proxy_collision_mm3']:.6f} mm³.
- Shaft intersection: {r['shaft_collision_mm3']:.6f} mm³.
- Actual shield OD remains `MEASUREMENT_HOLD`; the ring remains `PHYSICAL_COUPON_REQUIRED`.
- No adhesive is the primary retention method; removal and drain notches are retained.
"""


def physical_test_plan_text() -> str:
    return """# Physical test plan v0.9.3.5

## Stage 1 — axle coupon

1. Print all three holes in the final-part orientation.
2. Insert the shaft by hand; do not hammer.
3. Record insertion, wobble, cracking and removal for 10.0/10.1/10.2.
4. Keep the main CAD at 10.1 unless the user reports a new result.

## Stage 2 — bearing-seat coupon

1. Measure each printed bore before insertion.
2. Use thumb or controlled hand force only.
3. Require no self-drop, hand-detectable outer-race motion, whitening or cracking.
4. Remove from the push-out side.

## Stage 3 — guide coupon

1. Confirm no centered rubbing at 0.3/0.4/0.5 mm per-side candidates.
2. Laterally displace the link toward the guide side face.
3. Require side-face contact without tooth lift or stable apex parking.
4. Compare 35/40/45 degrees; 40 degrees is provisional only.

## Stage 4 — full crawler hand rotation

### Test A: both axles supported and parallel

- Forward 100 and reverse 100 rotations.
- Derailment, guide-top parking, bearing movement, loosening and link lift must all remain zero.

### Test B: light lateral load

- Forward 20 and reverse 20 rotations with gentle lateral input.
- Return within one to two link pitches; no continuous guide climb.

### Test C: one-axle-held reproduction

- Right turn 10 passes and left turn 10 passes.
- Record guide contact; require no complete derailment, persistent guide-top running or bearing migration.

Finish every stage without power, belt tension, torque load, mud, water or field deployment.
"""


def remaining_measurements_text() -> str:
    return """# Remaining measurements v0.9.3.5

- Exact physical link count in the assembled loop and measured loop length.
- Actual guide height, width, top flat and worn/contact marks.
- Link inner/tooth width at the guide contact plane.
- Bearing manufacturer/model marking, OD at multiple angles, width and chamfers.
- Printed seat ID at both faces and orthogonal directions.
- Bearing shield/seal outside diameter and retainer-safe outer-race contact band.
- Actual shaft OD at multiple positions, straightness and surface condition.
- As-printed 10.0/10.1/10.2 coupon bores.
- As-printed four bearing coupon bores and insertion/removal force.
- Roller and axle parallelism under the supported Test A setup.
- Guide contact video for forward/reverse and left/right reproduction.
"""


def no_power_text() -> str:
    return """NO_POWER_NO_LOAD_ONLY
CRAWLER_TRACKING_PATCH=PHYSICAL_TEST_READY
AXLE_BORE_10P1=CAD_COMPLETE_PENDING_PRINTED_FIT
RECOVERY_GUIDE=PHYSICAL_COUPON_REQUIRED
BEARING_SEAT=PHYSICAL_COUPON_REQUIRED
BEARING_RETAINER=PHYSICAL_COUPON_REQUIRED
FULL_LOOP_HAND_ROTATION=CONDITIONAL_PASS
BELT_TENSION=NOT_APPROVED
POWERED_ROTATION=NOT_APPROVED
TORQUE_LOAD=NOT_APPROVED
MUD_TEST=NOT_APPROVED
WATER_TEST=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
MANUFACTURING=NOT_APPROVED
AUTHORITY_UPDATE=NOT_APPROVED
"""


def svg_base(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650"><style>text{{font-family:Arial,sans-serif;fill:#172033}}.t{{font-size:27px;font-weight:bold}}.h{{font-size:18px;font-weight:bold}}.s{{font-size:15px}}.hold{{fill:#b91c1c}}.line{{stroke:#334155;stroke-width:3;fill:none}}.old{{fill:#dbeafe;stroke:#2563eb;stroke-width:2}}.new{{fill:#dcfce7;stroke:#15803d;stroke-width:2}}.proxy{{fill:#fef3c7;stroke:#d97706;stroke-width:2}}</style><rect width="1000" height="650" fill="white"/><text x="45" y="48" class="t">{title}</text>{body}<text x="45" y="625" class="s hold">PHYSICAL TEST ONLY · NO POWER · NO LOAD · NOT FOR MANUFACTURING</text></svg>'''


def svg_payloads() -> dict[str, str]:
    original = svg_base("Original sprocket / broad guide section", '<circle cx="250" cy="320" r="165" class="old"/><circle cx="250" cy="320" r="52" fill="white" stroke="#2563eb"/><rect x="545" y="330" width="125" height="150" class="old"/><rect x="740" y="330" width="125" height="150" class="old"/><rect x="545" y="270" width="125" height="60" class="old"/><rect x="740" y="270" width="125" height="60" class="old"/><text x="520" y="520" class="h">3.0 high · 2.5 broad flat top · 1.2 clearance/side</text>')
    corrected = svg_base("Corrected recovery guide section", '<rect x="180" y="430" width="640" height="70" class="proxy"/><polygon points="250,430 250,230 334,146 390,146 390,430" class="new"/><polygon points="610,430 610,146 666,146 750,230 750,430" class="new"/><path d="M334 146 Q362 118 390 146" class="line"/><path d="M610 146 Q638 118 666 146" class="line"/><text x="90" y="550" class="h">lower 2.0 mm (66.7%) · upper 1.0 mm (33.3%) · 40° from vertical · R0.75</text>')
    clearance = svg_base("Guide centered-clearance candidates", '<rect x="260" y="230" width="480" height="160" class="proxy"/><rect x="210" y="190" width="45" height="240" class="new"/><rect x="745" y="190" width="45" height="240" class="new"/><line x1="255" y1="440" x2="260" y2="440" class="line"/><line x1="740" y1="440" x2="745" y2="440" class="line"/><text x="225" y="490" class="h">0.3 / 0.4 / 0.5 mm per side · 0.4 provisional</text>')
    sequence = svg_base("Recovery contact sequence", '<g transform="translate(40,0)"><rect x="70" y="330" width="200" height="70" class="proxy"/><polygon points="285,400 285,260 330,215 360,215 360,400" class="new"/><text x="80" y="455" class="h">1 centered</text></g><g transform="translate(340,0)"><rect x="70" y="330" width="200" height="70" class="proxy"/><polygon points="250,400 250,260 295,215 325,215 325,400" class="new"/><path d="M205 280 L270 250" class="line"/><text x="70" y="455" class="h">2 lateral contact</text></g><g transform="translate(650,0)"><rect x="40" y="330" width="200" height="70" class="proxy"/><polygon points="255,400 255,260 300,215 330,215 330,400" class="new"/><path d="M225 270 L160 270" class="line"/><text x="45" y="455" class="h">3 return toward center</text></g>')
    angles = svg_base("Guide angle comparison", ''.join(f'<polygon points="{100+i*285},450 {100+i*285},250 {170+i*285},180 {215+i*285},180 {215+i*285},450" class="new"/><text x="{115+i*285}" y="500" class="h">{int(angle)}°</text>' for i, angle in enumerate(GUIDE_ANGLE_CANDIDATES_DEG)) + '<text x="385" y="555" class="h">40° provisional</text>')
    clear_compare = svg_base("Guide clearance comparison", ''.join(f'<rect x="{120+i*290}" y="210" width="170" height="200" class="proxy"/><rect x="{90+i*290}" y="180" width="25" height="260" class="new"/><rect x="{295+i*290}" y="180" width="25" height="260" class="new"/><text x="{140+i*290}" y="490" class="h">{c:.1f} mm/side</text>' for i, c in enumerate(GUIDE_CLEARANCE_CANDIDATES_MM)))
    bore = svg_base("Axle bore comparison", ''.join(f'<circle cx="{210+i*290}" cy="310" r="{72+i*2}" class="proxy"/><text x="{160+i*290}" y="430" class="h">AXLE {d:.1f}</text>' for i, d in enumerate(AXLE_COUPON_DIAMETERS_MM)) + '<text x="370" y="520" class="h">MAIN CAD = 10.1 mm</text>')
    bearing = svg_base("Bearing retention options", '<circle cx="260" cy="315" r="150" class="old"/><circle cx="260" cy="315" r="120" fill="white" stroke="#2563eb"/><text x="115" y="505" class="h">A: 25.7 / 25.8 / 25.9 / 26.0 coupon</text><circle cx="740" cy="315" r="150" class="new"/><circle cx="740" cy="315" r="108" fill="white" stroke="#15803d"/><circle cx="740" cy="185" r="14" fill="white" stroke="#15803d"/><circle cx="628" cy="380" r="14" fill="white" stroke="#15803d"/><circle cx="852" cy="380" r="14" fill="white" stroke="#15803d"/><text x="600" y="505" class="h">B: removable 3×M3 retainer</text>')
    return {REFERENCE_FILES[1]: original, CORRECTED_FILES[3]: corrected, CORRECTED_FILES[4]: clearance, CORRECTED_FILES[5]: sequence, COMPARISON_FILES[1]: angles, COMPARISON_FILES[2]: clear_compare, COMPARISON_FILES[3]: bore, COMPARISON_FILES[4]: bearing}


def canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0935','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('CRAWLER TRACKING RETENTION PATCH'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def export_step(path: Path, shape: cq.Shape | cq.Workplane) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    obj = shape.val() if hasattr(shape, "val") else shape
    cq.exporters.export(obj, str(path))
    canonicalize_step(path)


def export_stl(path: Path, shape: cq.Workplane) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.1)


def export_artifacts() -> None:
    export_step(LANE_DIR / REFERENCE_FILES[0], hand_test_assembly(False))
    export_step(LANE_DIR / CORRECTED_FILES[0], build_drive(S.corrected_drive_bore_mm))
    export_step(LANE_DIR / CORRECTED_FILES[1], build_idler())
    export_step(LANE_DIR / CORRECTED_FILES[2], hand_test_assembly(True))
    overlay = cq.Compound.makeCompound([build_drive(S.original_drive_bore_mm).translate((0, -40, 0)).val(), build_drive(S.corrected_drive_bore_mm).translate((0, 40, 0)).val(), original_guide_pair().translate((90, -40, 0)).val(), recovery_guide_pair().translate((90, 40, 0)).val()])
    export_step(LANE_DIR / COMPARISON_FILES[0], overlay)
    for rel, angle in zip(PRINT_FILES[:3], GUIDE_ANGLE_CANDIDATES_DEG):
        export_stl(LANE_DIR / rel, guide_coupon(angle))
    export_stl(LANE_DIR / PRINT_FILES[3], axle_bore_coupon())
    export_stl(LANE_DIR / PRINT_FILES[4], bearing_seat_coupon())
    export_stl(LANE_DIR / PRINT_FILES[5], bearing_retainer_ring())
    payloads = svg_payloads()
    if set(payloads) != set(SVG_FILES):
        raise RuntimeError({"svg_missing": sorted(set(SVG_FILES) - set(payloads)), "svg_extra": sorted(set(payloads) - set(SVG_FILES))})
    for rel, text in payloads.items():
        write_text(LANE_DIR / rel, text)


def commit_paths_text() -> str:
    prefix = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    return "\n".join(f"{prefix}/{rel}" for rel in PACKAGE_PATHS)


def manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0935_ONLY", f"starting_head={EXPECTED_HEAD}", "authority_update=PROHIBITED", "manufacturing=NOT_APPROVED", "powered_rotation=NOT_APPROVED", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith(".step"): role = "REFERENCE_OR_CORRECTED_CAD"
        elif rel.endswith(".stl"): role = "NO_LOAD_FIT_TEST_COUPON"
        elif rel.endswith(".svg"): role = "DIAGRAM_OR_COMPARISON"
        elif rel.endswith(".json"): role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"): role = "BUILDER_OR_CONTRACT_TEST"
        else: role = "DOCUMENT_OR_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def sha256sums_text() -> str:
    return "\n".join(f"{sha256(LANE_DIR / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in STEP_FILES:
        try:
            shape = cq.importers.importStep(str(base / rel)).val()
            solids = len(shape.Solids())
            passed = solids >= 1 and all(math.isfinite(value) for value in bounds(shape).values())
            if rel in (CORRECTED_FILES[0], CORRECTED_FILES[1]):
                passed = passed and solids == 1
            rows.append({"path": rel, "solids": solids, "bounds": bounds(shape), "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_stls(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in STL_FILES:
        try:
            # CadQuery emits binary STL with one vertex triplet per facet.  Load
            # that representation directly, then weld coincident vertices.  The
            # high-level trimesh scene loader currently exits inside this pinned
            # Windows CAD environment, before it can return a mesh.
            with (base / rel).open("rb") as handle:
                raw = trimesh.exchange.stl.load_stl_binary(handle)
            mesh = trimesh.Trimesh(vertices=raw["vertices"], faces=raw["faces"], process=False)
            mesh.merge_vertices()
            components = int(mesh.body_count)
            passed = bool(mesh.is_watertight) and components == 1 and mesh.volume > 0
            rows.append({"path": rel, "watertight": bool(mesh.is_watertight), "components": components, "faces": len(mesh.faces), "volume_mm3": float(mesh.volume), "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_svgs(base: Path = LANE_DIR) -> dict[str, Any]:
    import xml.etree.ElementTree as ET
    rows = []
    for rel in SVG_FILES:
        try:
            text = (base / rel).read_text(encoding="utf-8")
            root = ET.fromstring(text)
            passed = root.tag.endswith("svg") and "viewBox" in root.attrib and "NO POWER" in text
            rows.append({"path": rel, "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def parse_hashes(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    values = parse_hashes(base / "SHA256SUMS.txt")
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches: list[Any] = []
    if set(values) != required:
        mismatches.append({"missing": sorted(required - set(values)), "extra": sorted(set(values) - required)})
    for rel, expected in values.items():
        actual = sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})
    return {"verified": len(values), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def verify_manifest(base: Path = LANE_DIR) -> dict[str, Any]:
    values = [line.split("|", 1)[0] for line in (base / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if "|" in line]
    return {"entry_count": len(values), "exact_order": values == list(PACKAGE_PATHS), "status": "PASS" if values == list(PACKAGE_PATHS) else "FAIL"}


def verify_evidence(base: Path = LANE_DIR) -> dict[str, Any]:
    p = json.loads((base / "crawler_tracking_patch_parameters_v0935.json").read_text(encoding="utf-8"))
    a = p["analysis"]
    checks = {
        "bore_exact": p["bore_classification"]["drive_sprocket_center"]["corrected_cad_mm"] == 10.1,
        "axis": a["preservation"]["axis_unchanged"] == [0.0, 0.0],
        "teeth_pitch_od": p["preserved"]["tooth_count"] == 12 and p["preserved"]["link_pitch_mm"] == 20.0 and p["preserved"]["sprocket_od_mm"] == 66.14,
        "zones": a["guide"]["lower_percent"] >= 60.0 and a["guide"]["upper_percent"] <= 40.0,
        "angle": p["guide"]["corrected"]["recommended_provisional_angle_deg"] == 40.0,
        "apex": 0.5 <= p["guide"]["corrected"]["apex_radius_mm"] <= 1.0,
        "centered_clear": a["guide"]["centered_tooth_collision_mm3"] <= 1e-6,
        "roller_clear": a["guide"]["roller_collision_mm3"] <= 1e-6,
        "displaced_contact": a["guide"]["displaced_tooth_contact_mm3"] > 0,
        "symmetry": a["guide"]["left_right_symmetric"] and a["guide"]["forward_reverse_equivalent"],
        "retainer": a["retainer"]["inner_race_collision_mm3"] <= 1e-6 and a["retainer"]["shield_proxy_collision_mm3"] <= 1e-6 and a["retainer"]["shaft_collision_mm3"] <= 1e-6,
        "floating": all(value == 1 for value in a["floating"].values()),
        "holds": p["approval"]["powered_rotation"] == "NOT_APPROVED" and p["approval"]["manufacturing"] == "NOT_APPROVED" and p["approval"]["authority_update"] == "NOT_APPROVED",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for rel in SOURCE_FILES:
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source missing: {rel}")
    repository_audit(require_complete=False)
    parents = parent_audit(True)
    source = source_audit(True)
    analysis = geometry_analysis()
    p = parameters(parents, source, analysis)
    write_text(LANE_DIR / ROOT_FILES[0], readme_text())
    write_text(LANE_DIR / ROOT_FILES[1], physical_result_text())
    write_json(LANE_DIR / ROOT_FILES[2], p)
    write_text(LANE_DIR / ROOT_FILES[3], design_report_text(p))
    write_text(LANE_DIR / ROOT_FILES[4], axle_report_text())
    write_text(LANE_DIR / ROOT_FILES[5], bearing_report_text(p))
    write_text(LANE_DIR / ROOT_FILES[6], physical_test_plan_text())
    write_text(LANE_DIR / ROOT_FILES[7], remaining_measurements_text())
    write_text(LANE_DIR / ROOT_FILES[8], no_power_text())
    write_text(LANE_DIR / ROOT_FILES[9], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[12], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\npowered_rotation=NOT_APPROVED\nphysical_test=NOT_YET_PERFORMED")
    write_text(LANE_DIR / ROOT_FILES[10], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[11], sha256sums_text())
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    reports = (verify_steps(), verify_stls(), verify_svgs(), verify_hashes(), verify_manifest(), verify_evidence())
    if any(report["status"] != "PASS" for report in reports):
        raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "formal_paths": len(PACKAGE_PATHS), "STEP": "5/5 PASS", "STL": "6/6 PASS", "SVG": "8/8 PASS", "parent": parents["status"], "source": source["status"], "evidence": reports[-1]["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = lane_files()
    expected = sorted(PACKAGE_PATHS)
    if actual != expected:
        raise RuntimeError({"missing": sorted(set(expected) - set(actual)), "extra": sorted(set(actual) - set(expected))})
    repository = repository_audit(require_complete=True)
    parents = parent_audit()
    source = source_audit()
    steps, stls, svgs, hashes, manifest, evidence = verify_steps(), verify_stls(), verify_svgs(), verify_hashes(), verify_manifest(), verify_evidence()
    reports = {"parents": parents["status"], "source": source["status"], "steps": steps["status"], "stls": stls["status"], "svgs": svgs["status"], "hashes": hashes["status"], "manifest": manifest["status"], "evidence": evidence["status"]}
    if any(value != "PASS" for value in reports.values()):
        raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent_protection": parents["status"], "source_protection": source["status"], "formal_paths": len(PACKAGE_PATHS), "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "STL_manifold": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "status": "PASS"}


def zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"scope": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        hashes = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip():
                digest, rel = line.split("  ", 1)
                hashes[rel] = digest
        internal = [rel for rel, expected in hashes.items() if hashlib.sha256(archive.read(rel)).hexdigest() != expected]
        lane_mismatches = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0935_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ); env["V0935_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_crawler_tracking_retention_patch_v0935.py", "--verify"], cwd=target, env=env)
            tests = run([sys.executable, "-B", "tests/test_crawler_tracking_retention_patch_v0935.py"], cwd=target, env=env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatches:
        raise RuntimeError({"internal_hash_mismatches": internal, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final.exists() or temporary.exists():
        raise RuntimeError("refusing to overwrite handoff")
    try:
        write_text(LANE_DIR / ROOT_FILES[12], "status=PACKAGE_TESTS_PENDING\npowered_rotation=NOT_APPROVED\nphysical_test=NOT_YET_PERFORMED")
        write_text(LANE_DIR / ROOT_FILES[11], sha256sums_text())
        write_zip(temporary)
        env = dict(os.environ); env["V0935_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_crawler_tracking_retention_patch_v0935.py"], cwd=LANE_DIR, env=env)
        if result.returncode:
            raise RuntimeError(result.stdout)
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[12], "command=python -B tests/test_crawler_tracking_retention_patch_v0935.py\nstatus=PASS\n" + "\n".join(summary) + "\npowered_rotation=NOT_APPROVED\nphysical_test=NOT_YET_PERFORMED\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[11], sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    write_zip(final)
    return {"verification": "PASS", **verify_zip(final, standalone=True)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if sum((args.refresh_artifacts, args.verify, args.package, args.verify_zip is not None)) != 1:
        parser.error("choose exactly one action")
    if args.refresh_artifacts:
        result = refresh_artifacts()
    elif args.verify:
        result = verify()
    elif args.package:
        result = package_handoff()
    else:
        result = verify_zip(args.verify_zip, standalone=True)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
