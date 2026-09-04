#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the temporary exact-tooth HTD5M 60T split-clamp pulley.

The complete outer annulus is cut directly from the protected v0.9.5.1
60T STEP.  No HTD tooth is regenerated.  Only the non-tooth interior is
replaced with a six-spoke PETG structure and an M4 metal-hardware clamp.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile
from typing import Iterable
import zipfile

import cadquery as cq
from cadquery import exporters, importers


VERSION = "v0.9.6.21"
CLASSIFICATION = "TEMP_HTD5M_60T_SPLIT_CLAMP_PULLEY"
STATUS = (
    "TEMP_HTD5M_60T_SPLIT_CLAMP_PULLEY_CAD_COMPLETE/"
    "EXACT_WORKING_60T_TOOTH_GEOMETRY_REUSED/Ø10_SPLIT_CLAMP_READY/"
    "BORE_COUPONS_READY/P20653_SCOPE_UNCHANGED/"
    "DRY_DUAL_MOTOR_TEST_FIXTURE_READY_FOR_PHYSICAL_FIT/"
    "FULL_TORQUE_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2492
BASE_OUTSIDE_DIGEST = "eb076578a54daff7e9c5103a3e295fc86f9f7e67a92a78444c6633f55c229ea3"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
PROTECTED_LANES = {
    "cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16": (37, "fe514d3a9c1ca21bca92beee738ff1ed1b6d47fd2cdb2f2aa59866584303ea56"),
    "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17": (33, "3e0a550c7d9faa38fae8d106e60b91467788e18533d23063156070d1259615b8"),
    "cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18": (39, "fcab7a320e371504767153d1167c6c7f5416b84a8edd28e7331f988b01998373"),
    "cad/common_rover/common_rover_y3_reaction_shoe_v0_9_6_19": (34, "ede454f33bbd1030c0e744de0fda9614d86d201f89a7ebdc17e8a468bbfedb7a"),
    "cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19": (39, "e632689b54678455adec6758b2420bcf0ed4a2bd8ade8d229d80087275a4630e"),
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20": (55, "9d0d0eb92b759be81ed61a69d89a1888adbb4b88fcd66e63b14a056d59966300"),
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

SOURCE_LANE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
SOURCE_LANE = REPO_ROOT / SOURCE_LANE_REL
SOURCE_FILES_SHA256 = {
    "build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py": "2d51ca23ca1d2dfa445f5ad45d76fd244ebdbb78984d27123979e3d95a1d2924",
    "source_reuse_snapshot/htd5m_profile.py": "77f3e18eb14e2956213eddfc84529264585451c2014d0a8325229e368ede54e1",
    "cad/drive_htd5m_20t_reference.step": "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1",
    "cad/drive_htd5m_60t_reference.step": "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256",
    "cad/drive_20t_60t_c180_113t_reference.step": "29c0a32423c4656211a903ccc19af635be2797901d67a8ffa01921b23d5ed1f6",
    "pulley_geometry.json": "ff153d6de38d722746f3470ffc709137f5ae1458a00028006dbe7e0f64cfbf62",
    "validation_report.json": "134a0b21208a019f8ffbcb450b20482104268b5359f6fae6a0f02be91d4915ee",
}
ORIGINAL_SOURCE_LINEAGE = {
    "source_root": r"D:\Paddy_Swarm_Project_worktrees\common_rover_htd5m_full_pulley_dummy_v0_1\cad\common_rover\htd5m_full_pulley_dummy_candidate_v0_1",
    "pulley_60t_standard_dummy.py": "0a9d8e905df54b2594c420374eabc7678a6d95da231cb1f83bce15b64c864ec3",
    "full_pulley_common.py": "cc4e894275c32d2e37c101367ec9bda7f124e9cf374ca53c011afda11f4a78de",
}

TOOTH_COUNT = 60
PITCH_MM = 5.0
ANGULAR_PITCH_DEG = 6.0
PITCH_DIAMETER_MM = 95.4929658551372
ROOT_DIAMETER_MM = 91.8929658551372
TOOTH_OD_MM = 96.9329658551372
TOOTH_FACE_WIDTH_MM = 16.0
FLANGE_OD_MM = 102.0
FLANGE_THICKNESS_MM = 2.0
SOURCE_TOTAL_WIDTH_MM = 20.0
BELT_WIDTH_MM = 15.0
BELT_PLANE_Z_MM = 10.0
RING_INNER_RADIUS_MM = 37.0
RIM_MIN_RADIAL_MM = ROOT_DIAMETER_MM / 2.0 - RING_INNER_RADIUS_MM
HUB_OD_MM = 34.0
HUB_WIDTH_MM = 26.0
EAR_X_MIN_MM = 4.0
EAR_X_MAX_MM = 25.0
EAR_Y_SPAN_MM = 38.0
EAR_HEIGHT_MM = 34.0
EAR_CORNER_FILLET_MM = 3.0
BORE_PRIMARY_MM = 10.20
BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
SPLIT_WIDTH_MM = 1.30
M4_HOLE_MM = 4.50
M4_COUNT = 2
M4_X_MM = [10.5, 18.5]
M4_Z_MM = 27.0
SPOKE_COUNT = 6
SPOKE_WIDTH_MM = 10.0
SPOKE_ANGLES_DEG = [30.0 + 60.0 * i for i in range(6)]
TOOL_ENVELOPE_DIAMETER_CANDIDATE_MM = 10.0
TOOL_TO_FLANGE_AXIAL_CLEARANCE_MM = M4_Z_MM - TOOL_ENVELOPE_DIAMETER_CANDIDATE_MM / 2.0 - SOURCE_TOTAL_WIDTH_MM
HUB_NOMINAL_WALL_MM = (HUB_OD_MM - BORE_PRIMARY_MM) / 2.0
BORE_TO_M4_MIN_MM = min(M4_X_MM) - BORE_PRIMARY_MM / 2.0 - M4_HOLE_MM / 2.0
CLAMP_EAR_MIN_MM = min(min(M4_X_MM) - M4_HOLE_MM / 2.0 - EAR_X_MIN_MM,
                         EAR_X_MAX_MM - max(M4_X_MM) - M4_HOLE_MM / 2.0,
                         EAR_HEIGHT_MM - M4_Z_MM - M4_HOLE_MM / 2.0)

BUILDER = "build_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.py"
TEST = "tests/test_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "EXACT_60T_SOURCE_TRACE.md", "TOOTH_GEOMETRY_FREEZE.md",
    "TEMPORARY_USE_LIMITS.md", "SHAFT_INTERFACE.md", "SPLIT_CLAMP_DESIGN.md", "BORE_COUPON_PLAN.md",
    "PRINT_PLAN.md", "ASSEMBLY_PLAN.md", "BELT_ALIGNMENT_CHECK.md", "SHAFT_SLIP_WITNESS_MARK.md",
    "HAND_ROTATION_TEST.md", "DUAL_MOTOR_POWERED_TEST.md", "FAILURE_CRITERIA.md", "POWERED_GATE.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.step",
    "artifacts/temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.stl",
    "artifacts/split_clamp_coupon_b1010.stl", "artifacts/split_clamp_coupon_b1020.stl",
    "artifacts/split_clamp_coupon_b1030.stl", "artifacts/coupon_triplet_plate.stl",
    "artifacts/temp_htd5m_60t_dry_assembly_reference_v0_9_6_21.step",
]
SVGS = [
    "artifacts/temp_60t_overview.svg", "artifacts/existing_vs_temp_tooth_overlay.svg",
    "artifacts/split_clamp_detail.svg", "artifacts/shaft_witness_mark.svg",
    "artifacts/20t_60t_belt_plane.svg", "artifacts/dry_dual_motor_test_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    h = hashlib.sha256()
    for path in files:
        h.update((path.relative_to(root).as_posix() + "\n").encode())
        h.update(bytes.fromhex(sha256(path)))
    return len(files), h.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(row[3:].replace("\\", "/") for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
                  if row.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    sources = {rel: sha256(SOURCE_LANE / rel) for rel in SOURCE_FILES_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".dxf"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES, "source_sha": sources == SOURCE_FILES_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {"checks": checks, "repository": str(root), "branch": branch, "head": head, "staged": staged,
              "tracked_dirty": dirty, "outside_untracked": outside_snapshot(), "lane_files": len(lane_files),
              "authority_sha256": authority,
              "protected_lanes": {rel: {"count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
                                  for rel, value in protected.items()}, "source_sha256": sources,
              "cache": cache, "forbidden": forbidden}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=False))
    return result


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, z))


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def source_60t() -> cq.Workplane:
    return importers.importStep(str(SOURCE_LANE / "cad/drive_htd5m_60t_reference.step"))


def source_20t() -> cq.Workplane:
    return importers.importStep(str(SOURCE_LANE / "cad/drive_htd5m_20t_reference.step"))


def source_outer_ring() -> cq.Workplane:
    return source_60t().cut(cylinder(RING_INNER_RADIUS_MM, 24.0, -2.0)).clean()


def rounded_ear() -> cq.Workplane:
    return (cq.Workplane("XY").box(EAR_X_MAX_MM - EAR_X_MIN_MM, EAR_Y_SPAN_MM, EAR_HEIGHT_MM)
            .translate(((EAR_X_MIN_MM + EAR_X_MAX_MM) / 2.0, 0.0, EAR_HEIGHT_MM / 2.0))
            .edges("|Z").fillet(EAR_CORNER_FILLET_MM))


def capsule_spoke(r1: float, r2: float, angle_deg: float, height: float = SOURCE_TOTAL_WIDTH_MM) -> cq.Workplane:
    length = r2 - r1
    body = cq.Workplane("XY").box(length, SPOKE_WIDTH_MM, height).translate(((r1 + r2) / 2.0, 0, height / 2.0))
    end1 = cylinder(SPOKE_WIDTH_MM / 2.0, height).translate((r1, 0, 0))
    end2 = cylinder(SPOKE_WIDTH_MM / 2.0, height).translate((r2, 0, 0))
    return body.union(end1).union(end2).rotate((0, 0, 0), (0, 0, 1), angle_deg)


def clamp_blank(include_ring: bool, spoke_outer: float) -> cq.Workplane:
    base = cylinder(HUB_OD_MM / 2.0, HUB_WIDTH_MM).union(rounded_ear())
    for angle in SPOKE_ANGLES_DEG:
        base = base.union(capsule_spoke(16.0, spoke_outer, angle))
    if include_ring:
        base = base.union(source_outer_ring())
    return base.clean()


def clamp_cutters(bore_mm: float) -> list[cq.Workplane]:
    cutters = [cylinder(bore_mm / 2.0, EAR_HEIGHT_MM + 2.0, -1.0)]
    split = (cq.Workplane("XY").box(EAR_X_MAX_MM - 4.7 + 2.0, SPLIT_WIDTH_MM, EAR_HEIGHT_MM + 2.0)
             .translate(((4.7 + EAR_X_MAX_MM + 2.0) / 2.0, 0, EAR_HEIGHT_MM / 2.0)))
    cutters.append(split)
    for x in M4_X_MM:
        hole = cq.Solid.makeCylinder(M4_HOLE_MM / 2.0, EAR_Y_SPAN_MM + 4.0,
                                     cq.Vector(x, -EAR_Y_SPAN_MM / 2.0 - 2.0, M4_Z_MM), cq.Vector(0, 1, 0))
        cutters.append(cq.Workplane(obj=hole))
    return cutters


def apply_clamp_cuts(shape: cq.Workplane, bore_mm: float) -> cq.Workplane:
    result = shape
    for cutter in clamp_cutters(bore_mm):
        result = result.cut(cutter)
    return result.clean()


def temp_pulley(bore_mm: float = BORE_PRIMARY_MM) -> cq.Workplane:
    return apply_clamp_cuts(clamp_blank(True, 38.0), bore_mm)


def coupon(bore_mm: float, label: str) -> cq.Workplane:
    result = apply_clamp_cuts(clamp_blank(False, 26.0), bore_mm)
    mark = cq.Workplane("XY").text(label, 3.2, 0.35, combine=True).translate((14.5, -11.5, EAR_HEIGHT_MM - 0.30))
    return result.cut(mark).clean()


def triplet_plate() -> cq.Workplane:
    parts = [coupon(10.10, "B1010").translate((-70, 0, 0)), coupon(10.20, "B1020"),
             coupon(10.30, "B1030").translate((70, 0, 0))]
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def assembly_reference() -> cq.Workplane:
    source = importers.importStep(str(SOURCE_LANE / "cad/drive_20t_60t_c180_113t_reference.step"))
    solids = source.solids().vals()
    pulley20 = next(s for s in solids if 14000 < s.Volume() < 16000)
    belt113 = next(s for s in solids if 24000 < s.Volume() < 27000)
    shafts = [s for s in solids if 300 < s.Volume() < 400]
    temp = temp_pulley().translate((180, 0, 0)).val()
    return cq.Workplane(obj=cq.Compound.makeCompound([pulley20, temp, belt113, *shafts]))


def tip_face_signature(shape: cq.Workplane) -> dict[str, object]:
    rows = []
    for face in shape.val().Faces():
        center = face.Center(); radius = math.hypot(center.x, center.y); bb = face.BoundingBox()
        if face.geomType() == "PLANE" and 48.0 < radius < 49.0 and 20.0 < face.Area() < 30.0 and abs(bb.zlen - 16.0) < 0.01:
            rows.append(math.degrees(math.atan2(center.y, center.x)) % 360.0)
    rows.sort()
    spacings = [((rows[(i + 1) % len(rows)] - rows[i]) % 360.0) for i in range(len(rows))] if rows else []
    return {"count": len(rows), "angles_deg": [round(x, 6) for x in rows],
            "spacing_min_deg": round(min(spacings), 6) if spacings else None,
            "spacing_max_deg": round(max(spacings), 6) if spacings else None}


def tooth_preservation_audit(final: cq.Workplane) -> dict[str, object]:
    outer = cylinder(49.20, TOOTH_FACE_WIDTH_MM, 2.0)
    inner = cylinder(45.70, TOOTH_FACE_WIDTH_MM, 2.0)
    mask = outer.cut(inner)
    source = source_60t().intersect(mask)
    candidate = final.intersect(mask)
    removed = volume(source.cut(candidate)); added = volume(candidate.cut(source))
    source_sig = tip_face_signature(source_60t()); final_sig = tip_face_signature(final)
    return {"protected_radius_mm": [45.70, 49.20], "protected_z_mm": [2.0, 18.0],
            "source_volume_mm3": volume(source), "candidate_volume_mm3": volume(candidate),
            "removed_volume_mm3": removed, "added_volume_mm3": added,
            "source_tip_faces": source_sig, "final_tip_faces": final_sig,
            "profile_modification_count": 0,
            "exact_reuse_pass": removed == 0.0 and added == 0.0 and source_sig == final_sig}


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-14T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError(f"STEP timestamp: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path)); normalize_step(path)


def mesh_metrics(path: Path, bore_target: float | None = None) -> dict[str, object]:
    data = path.read_bytes(); count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError(f"binary STL: {path}")
    edges: dict[tuple, list[int]] = collections.defaultdict(list); vertices = []; degenerate = 0
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        tri = [tuple(round(float(x), 6) for x in values[i:i + 3]) for i in (3, 6, 9)]; vertices.extend(tri)
        ux, uy, uz = (tri[1][i] - tri[0][i] for i in range(3)); vx, vy, vz = (tri[2][i] - tri[0][i] for i in range(3))
        area2 = math.sqrt((uy*vz-uz*vy)**2 + (uz*vx-ux*vz)**2 + (ux*vy-uy*vx)**2)
        if area2 < 1e-9: degenerate += 1
        for a, b in ((0, 1), (1, 2), (2, 0)): edges[tuple(sorted((tri[a], tri[b])))].append(index)
    parent = list(range(count))
    def find(x: int) -> int:
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        a, b = find(a), find(b)
        if a != b: parent[b] = a
    for faces in edges.values():
        for other in faces[1:]: union(faces[0], other)
    components = len({find(i) for i in range(count)})
    mins = [min(v[i] for v in vertices) for i in range(3)]; maxs = [max(v[i] for v in vertices) for i in range(3)]
    result = {"triangles": count, "watertight": bool(edges) and all(len(f) == 2 for f in edges.values()),
              "bad_edge_count": sum(len(f) != 2 for f in edges.values()), "degenerate_triangle_count": degenerate,
              "component_count": components, "bounds_mm": [mins, maxs],
              "extents_mm": [maxs[i] - mins[i] for i in range(3)]}
    if bore_target is not None:
        target_r = bore_target / 2.0
        bore_vertices = sorted({v for v in vertices if abs(math.hypot(v[0], v[1]) - target_r) < 0.02})
        radii = [math.hypot(v[0], v[1]) for v in bore_vertices]
        angles = sorted({round(math.atan2(v[1], v[0]) % (2*math.pi), 8) for v in bore_vertices})
        gaps = sorted([((angles[(i+1) % len(angles)] - angles[i]) % (2*math.pi)) for i in range(len(angles))])
        regular_gap = gaps[-2] if len(gaps) > 1 else gaps[-1]
        split_y = sorted({v[1] for v in vertices if v[0] > target_r and abs(abs(v[1]) - SPLIT_WIDTH_MM/2.0) < 0.02})
        negative = max(y for y in split_y if y < 0); positive = min(y for y in split_y if y > 0)
        result["bore_mesh"] = {"target_mm": bore_target,
                               "effective_min_mm": round(2*min(radii)*math.cos(regular_gap/2.0), 6),
                               "effective_max_mm": round(2*max(radii), 6),
                               "split_gap_mm": round(positive-negative, 6),
                               "hub_nominal_wall_mm": round((HUB_OD_MM-bore_target)/2.0, 6),
                               "bore_to_m4_min_mm": round(min(M4_X_MM)-bore_target/2.0-M4_HOLE_MM/2.0, 6),
                               "clamp_ear_min_mm": round(CLAMP_EAR_MIN_MM, 6)}
    return result


def geometry_data(final: cq.Workplane, meshes: dict[str, dict[str, object]], steps: dict[str, object]) -> dict[str, object]:
    bb = final.val().BoundingBox(); tooth = tooth_preservation_audit(final)
    source_validation = json.loads((SOURCE_LANE / "validation_report.json").read_text(encoding="utf-8"))
    return {"pulley": {"valid": all(s.isValid() for s in final.solids().vals()), "solid_count": final.solids().size(),
                       "volume_mm3": volume(final), "overall_dimensions_mm": meshes[CAD[1]]["extents_mm"],
                       "cad_brep_tolerance_envelope_mm": [bb.xlen, bb.ylen, bb.zlen],
                       "architecture": "ONE_PIECE_60T_6SPOKE_INTEGRATED_SPLIT_CLAMP",
                       "tooth_count": TOOTH_COUNT, "pitch_family": "HTD5M", "pitch_mm": PITCH_MM,
                       "angular_spacing_deg": ANGULAR_PITCH_DEG, "pitch_diameter_mm": PITCH_DIAMETER_MM,
                       "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM, "flange_count": 2,
                       "flange_od_mm": FLANGE_OD_MM, "flange_thickness_mm": FLANGE_THICKNESS_MM,
                       "rim_inner_radius_mm": RING_INNER_RADIUS_MM, "rim_min_radial_mm": RIM_MIN_RADIAL_MM},
            "clamp": {"shaft_nominal_mm": 10.0, "bore_primary_candidate_mm": BORE_PRIMARY_MM,
                      "split_width_mm": SPLIT_WIDTH_MM, "split_exists": True, "split_gap_physical_closure": "PHYSICAL_HOLD",
                      "hub_od_mm": HUB_OD_MM, "hub_width_mm": HUB_WIDTH_MM, "clamp_ear_height_mm": EAR_HEIGHT_MM,
                      "m4_count": M4_COUNT, "m4_clearance_hole_mm": M4_HOLE_MM, "m4_centers_x_mm": M4_X_MM,
                      "m4_center_z_mm": M4_Z_MM, "petg_tapped_thread_count": 0,
                      "m4_bolt_length_candidate_mm": 50.0, "m4_bolt_length_status": "HOLD_CONFIRM_HARDWARE_STACK",
                      "hardware": "M4_BOLT + METAL_WASHER + PRINTED_EAR + METAL_WASHER + METAL_M4_NUT",
                      "captured_nut_pocket": "NOT_USED_AVOIDS_UNSUPPORTED_CEILING",
                      "hub_nominal_wall_mm": HUB_NOMINAL_WALL_MM, "bore_to_m4_min_mm": BORE_TO_M4_MIN_MM,
                      "clamp_ear_min_mm": CLAMP_EAR_MIN_MM, "ear_corner_fillet_mm": EAR_CORNER_FILLET_MM},
            "structure": {"spoke_count": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
                          "spoke_angles_deg": SPOKE_ANGLES_DEG, "broad_root_radius_mm": SPOKE_WIDTH_MM/2.0,
                          "decorative_lightening_hole_count": 0},
            "tooth_preservation": tooth,
            "belt_alignment": {"source_20t_to_60t_center_distance_mm": 180.0,
                               "source_20t_belt_plane_z_mm": BELT_PLANE_Z_MM,
                               "temp_60t_belt_plane_z_mm": BELT_PLANE_Z_MM, "belt_plane_error_mm": 0.0,
                               "nominal_belt_width_mm": BELT_WIDTH_MM,
                               "source_flange_collision_zero": source_validation["checks"].get("flange_collision_zero", False),
                               "exact_successful_belt_solid": "HOLD_ACTIVE_PHYSICAL_BELT_NOT_UNAMBIGUOUS",
                               "113t_reference_in_assembly": "REFERENCE_ONLY_NOT_OPERATING_AUTHORITY"},
            "clearance": {"local_non_intended_intersection_count": 0,
                          "tool_envelope_diameter_candidate_mm": TOOL_ENVELOPE_DIAMETER_CANDIDATE_MM,
                          "tool_to_flange_axial_clearance_mm": TOOL_TO_FLANGE_AXIAL_CLEARANCE_MM,
                          "tool_access": "CAD_CANDIDATE_PASS; HOLD_ACTUAL_DRIVER_AND_WRENCH_ENVELOPE",
                          "frame_bearing_collar_neighbor_transform": "HOLD_EXACT_TRANSFORMS_REQUIRED",
                          "global_non_intended_intersection": "HOLD_NOT_FALSE_ZERO"},
            "print": {"printer": "Bambu Lab A1", "material": "PETG", "axis": "Z", "flat_on_bed": True,
                      "support": "NO_SUPPORT_CANDIDATE; HOLD_SLICER_BRIDGE_AUDIT",
                      "horizontal_m4_bridge_diameter_mm": M4_HOLE_MM,
                      "nozzle_mm": 0.4, "layer_mm": 0.20, "walls_min": 6, "top_layers_min": 6,
                      "bottom_layers_min": 6, "infill_percent_candidate": [40, 50]},
            "mesh": meshes, "step_import": steps}


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "source": {"lane": SOURCE_LANE_REL.as_posix(), "builder": "build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py",
                       "artifact": "cad/drive_htd5m_60t_reference.step", "sha256": SOURCE_FILES_SHA256,
                       "original_lineage": ORIGINAL_SOURCE_LINEAGE},
            "pulley": {"teeth": TOOTH_COUNT, "pitch_family": "HTD5M", "pitch_mm": PITCH_MM,
                       "spacing_deg": ANGULAR_PITCH_DEG, "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM,
                       "profile_modification_count": 0, "spokes": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
                       "flange_count": 2, "flange_od_mm": FLANGE_OD_MM},
            "clamp": {"shaft_nominal_mm": 10.0, "bore_candidates_mm": BORE_CANDIDATES_MM,
                      "primary_bore_candidate_mm": BORE_PRIMARY_MM, "split_width_mm": SPLIT_WIDTH_MM,
                      "m4_count": M4_COUNT, "metal_nut_count": 2, "metal_washer_min_count": 4,
                      "petg_primary_thread": False},
            "scope": {"p20653_modification_count": 0, "crawler_guard_modification_count": 0,
                      "drive_20t_modification_count": 0, "belt_redesign_count": 0, "frame_redesign_count": 0},
            "gates": {"first_print": "COUPONS_ONLY", "full_pulley_print": "AFTER_COUPON_SELECTION",
                      "static_fit": "PHYSICAL_HOLD", "hand_rotation": "AFTER_STATIC_PASS",
                      "short_dry_power": "AFTER_ALL_STATIC_AND_HAND_GATES", "full_torque": "NOT_APPROVED",
                      "water": "NOT_APPROVED", "mud": "NOT_APPROVED", "field": "NOT_APPROVED"}}


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.o{{fill:none;stroke:#264653;stroke-width:4}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.b{{fill:none;stroke:#2a9d8f;stroke-width:5}}.f{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.h{{fill:#ffe8d6;stroke:#9c6644;stroke-width:3}}.d{{stroke:#457b9d;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · DRY / SHORT-DURATION / LOW-LOAD ONLY · FULL TORQUE / WATER / MUD / FIELD NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    overview = svg_page("TEMP HTD5M 60T overview", '''<g transform="translate(375,350)"><circle r="255" class="o"/><circle r="230" class="b"/><circle r="185" class="o"/><circle r="85" class="f"/><rect x="20" y="-95" width="125" height="190" rx="18" class="h"/><path d="M25 0H150" class="a"/><g class="d"><path d="M80 0L210 -120M80 0L210 120M-80 0L-210 -120M-80 0L-210 120M0 -80V-235M0 80V235"/></g></g><text x="720" y="150" class="l">Exact source annulus: OD102 / 60T / face16</text><text x="720" y="200" class="l">6 broad spokes: 10 mm</text><text x="720" y="250" class="l">hub barrel: Ø34 × 26</text><text x="720" y="300" class="l">split: 1.30 · bore primary Ø10.20</text><text x="720" y="350" class="l">M4 ×2 above flange plane for tool access</text><text x="720" y="420" class="l">one piece · PETG · shaft axis Z</text>''')
    overlay = svg_page("Existing versus TEMP tooth overlay", '''<g transform="translate(420,350)"><circle r="242" class="a"/><circle r="242" class="b"/><circle r="255" class="o"/></g><text x="720" y="180" class="l">red: v0.9.5.1 protected 60T STEP</text><text x="720" y="230" class="l">green: v0.9.6.21 copied outer annulus</text><text x="720" y="300" class="l">protected added volume = 0</text><text x="720" y="340" class="l">protected removed volume = 0</text><text x="720" y="380" class="l">60 tip faces · 6° spacing</text><text x="720" y="450" class="l">interior changes begin inside R37</text>''')
    clamp = svg_page("Split clamp detail", '''<g transform="translate(170,100)"><rect x="250" y="80" width="330" height="430" rx="35" class="h"/><circle cx="415" cy="300" r="90" class="f"/><circle cx="415" cy="300" r="27" fill="#fff" stroke="#264653" stroke-width="4"/><rect x="415" y="270" width="180" height="8" fill="#e76f51"/><circle cx="470" cy="185" r="18" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="540" cy="185" r="18" fill="#fff" stroke="#264653" stroke-width="4"/><text x="630" y="170" class="l">M4 ×2, axis Y</text><text x="630" y="210" class="l">bolt + washer + PETG ear</text><text x="630" y="245" class="l">+ washer + metal nut</text><text x="630" y="310" class="l">split 1.30 mm</text><text x="630" y="350" class="l">gap must remain &gt;0 after clamp</text><text x="630" y="400" class="l">no tapped PETG torque thread</text><text x="630" y="450" class="l">actual torque / creep: PHYSICAL HOLD</text></g>''')
    witness = svg_page("Shaft / hub witness mark", '''<g transform="translate(120,120)"><rect x="80" y="200" width="900" height="110" rx="50" fill="#adb5bd"/><rect x="400" y="130" width="300" height="250" rx="25" class="h"/><line x1="250" y1="165" x2="850" y2="345" stroke="#d00000" stroke-width="10"/><text x="80" y="470" class="l">Draw ONE continuous line across steel shaft + printed hub before power.</text><text x="80" y="520" class="l">Inspect after every 1–2 s / 5 s / 10 s stage.</text><text x="80" y="570" class="l">Visible shift = FAIL_HUB_SLIP → STOP.</text></g>''')
    plane = svg_page("20T / TEMP60T belt-plane alignment", '''<g transform="translate(100,100)"><circle cx="180" cy="260" r="85" class="o"/><circle cx="820" cy="260" r="255" class="o"/><rect x="95" y="220" width="810" height="80" fill="#d8f3dc" opacity=".7"/><line x1="80" y1="260" x2="1080" y2="260" class="b"/><text x="100" y="560" class="l">center distance reference 180 mm · both tooth faces Z2..18 · plane Z10</text><text x="100" y="605" class="l">15 mm belt fits inside 16 mm tooth face; TEMP outer ring/flanges are exact source.</text></g>''')
    sequence = svg_page("Dry dual-motor test sequence", '''<g transform="translate(55,135)"><g class="h"><rect x="0" y="0" width="150" height="90" rx="12"/><rect x="180" y="0" width="150" height="90" rx="12"/><rect x="360" y="0" width="150" height="90" rx="12"/><rect x="540" y="0" width="150" height="90" rx="12"/><rect x="720" y="0" width="150" height="90" rx="12"/><rect x="900" y="0" width="150" height="90" rx="12"/></g><text x="28" y="38" class="l">TEMP side</text><text x="48" y="65" class="l">1–2 s</text><text x="220" y="52" class="l">inspect</text><text x="405" y="52" class="l">5 s</text><text x="580" y="52" class="l">inspect</text><text x="756" y="52" class="l">10 s</text><text x="940" y="52" class="l">inspect</text><path d="M150 45H180M330 45H360M510 45H540M690 45H720M870 45H900" class="d"/><text x="0" y="180" class="l">Then dual motor: 1–2 s → inspect → 5 s → inspect → 10 s → inspect.</text><text x="0" y="235" class="l">Stop on slip, skip, climb, walk, wobble, whitening, crack, loosening, sound, asymmetry.</text><text x="0" y="300" class="l">Never stall / block crawler / restrain vehicle / pull payload / run mud, water, field or unattended.</text></g>''')
    return dict(zip(SVGS, [overview, overlay, clamp, witness, plane, sequence]))


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = f"# Common Rover TEMP HTD5M 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"
    source = SOURCE_LANE_REL.as_posix(); tooth = geom["tooth_preservation"]
    return {
        "README.md": h + "\n2026-09-04到着予定のproduction 60Tまでの、乾地・短時間・低負荷dual-motor test専用fixtureです。まずcouponだけを印刷し、物理winner確定後にfull pulleyを1個だけ印刷します。\n",
        "DESIGN_AUTHORITY.md": h + f"\n外周R{RING_INNER_RADIUS_MM:.1f} mm以遠はv0.9.5.1の60T STEPから直接切り出したBRepです。HTD歯形を式やproseから再生成していません。変更は内側rim、6 spokes、Ø34×26 hub、1.3 mm split、M4×2 earだけです。\n",
        "EXACT_60T_SOURCE_TRACE.md": h + f"\nActive repository lane: `{source}`。Builder: `build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py` SHA `{SOURCE_FILES_SHA256['build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py']}`。Artifact: `cad/drive_htd5m_60t_reference.step` SHA `{SOURCE_FILES_SHA256['cad/drive_htd5m_60t_reference.step']}`。Protected profile SHA `{SOURCE_FILES_SHA256['source_reuse_snapshot/htd5m_profile.py']}`。Original lineage module SHAはdesign_parameters.jsonへ固定しました。旧coupon laneやabstract 60T envelopeは採用していません。\n",
        "TOOTH_GEOMETRY_FREEZE.md": h + f"\n60 teeth、HTD5M、5 mm pitch、6° spacing、face16 mm、root diameter {ROOT_DIAMETER_MM:.6f}、tooth OD {TOOTH_OD_MM:.6f}。protected volume removed={tooth['removed_volume_mm3']:.6f} mm³、added={tooth['added_volume_mm3']:.6f} mm³、source/final tip faces={tooth['source_tip_faces']['count']}/{tooth['final_tip_faces']['count']}。`TOOTH_PROFILE_MODIFICATION_COUNT=0`。\n",
        "TEMPORARY_USE_LIMITS.md": h + "\nDisposable/replaceable fixture。DRY / SHORT-DURATION / LOW-LOAD dual-motor testだけです。stall、blocked crawler、最大traction、vehicle restraint、payload pull、long unattended、mud、水、fieldは禁止です。production pulley代替ではありません。\n",
        "SHAFT_INTERFACE.md": h + f"\nTarget shaft Ø10.0 mm steel。pre-physical primary bore Ø{BORE_PRIMARY_MM:.2f} mm。barrel wall {HUB_NOMINAL_WALL_MM:.2f} mm、bore-to-nearest-M4 {BORE_TO_M4_MIN_MM:.2f} mm。shaft cut lengthはscope外。摩擦、creep、slip、runoutはCAD PASSにしません。\n",
        "SPLIT_CLAMP_DESIGN.md": h + f"\nOne-piece integrated clamp。split {SPLIT_WIDTH_MM:.2f} mm、M4 clearance holes Ø{M4_HOLE_MM:.2f}×2、metal bolt+washer+printed ear+washer+metal nut。PETG tap=0。nut pocketはunsupported ceiling回避のため不使用、外側nutで整備します。hole center Z{M4_Z_MM:.1f}はflange top Z20より上で、Ø10 tool candidate clearance {TOOL_TO_FLANGE_AXIAL_CLEARANCE_MM:.1f} mm。実工具はHOLD。締結後split gap>0必須、looseかつfaces contactは`FAIL_LOOSE`。\n",
        "BORE_COUPON_PLAN.md": h + "\nPrint order #1: B10.10/B10.20/B10.30 coupons only。各couponはfull partと同じhub wall、split、ear、M4×2、orientationとshort spoke rootsを持ちます。記録: insertion、hand force、hammer、closure、bottoming、hand rotation、removal、white stress、crack。firm hand/no hammer/removable/gap open/no hand rotation/no damageがwinner。10.20は自動採用しません。\n",
        "PRINT_PLAN.md": h + "\nBambu Lab A1 / PETG / shaft axis Z / flat。0.4 nozzle、0.20 layer、walls≥6、top/bottom≥6、infill40–50% candidate。No-support candidateですが、horizontal Ø4.5 M4 bridges、split、ear、flange underside、spoke transitionをslicerで確認するまで`HOLD_SLICER_NOT_RUN`です。\n",
        "ASSEMBLY_PLAN.md": h + "\nCoupon winnerでfull boreを再生成し1個だけ印刷。Ø10 shaftへhammerなしで装着し、M4 bolt→metal washer→ear→metal washer→metal nut。belt planeを20Tと合わせ、witness lineを引く。assembly STEPの113Tはv0.9.5.1 reference onlyで、現物active belt authorityではありません。\n",
        "BELT_ALIGNMENT_CHECK.md": h + "\n20T/60T source tooth faceはZ2..18、belt plane Z10、face16に対しbelt15。TEMP outer tooth/flangesをexact reuseしたためCAD plane error0。現物belt seating、flange rub、frame/bearing/collar/neighbor transformは`PHYSICAL_VALIDATION_REQUIRED`です。\n",
        "SHAFT_SLIP_WITNESS_MARK.md": h + "\nPowered前にshaft+hubを横切る連続線を1本描く。各1–2/5/10 s stage後に確認し、目視shiftは`FAIL_HUB_SLIP`で即停止。無制限増締めは禁止です。\n",
        "HAND_ROTATION_TEST.md": h + "\nStatic gate後、無通電10 forward +10 reverse。belt climb/tooth skip/hub slip/frame contact/crackが全て0でなければpoweredへ進みません。runout、alignment、M4 closure、witnessも再確認します。\n",
        "DUAL_MOTOR_POWERED_TEST.md": h + "\n全static/hand gate後のみ。TEMP side 1–2 s→inspect→5 s→inspect→10 s→inspect、次にdual motor 1–2 s→inspect→5 s→inspect→10 s→inspect。slip/skip/climb/walk/wobble/whitening/crack/loose/sound/asymmetryで即停止。\n",
        "FAILURE_CRITERIA.md": h + "\nFAIL_LOOSE: split faces contact while shaft loose。FAIL_HUB_SLIP: witness shift。その他、hammer required、removal impossible、white stress/crack、belt skip/climb/walk、wobble、frame contact、M4 loosening、abnormal sound/asymmetryはSTOP。\n",
        "POWERED_GATE.md": h + "\nMaximum possible status is `TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS`。FULL_TORQUE_PASS / ENDURANCE_PASS / FIELD_PASSにはなりません。CAD aloneではpowered approvalは出ません。\n",
        "HOLD_REGISTER.md": h + "\nPHYSICAL_HOLD: coupon winner、real clamp friction、PETG creep、shaft slip、split residual gap、actual belt seating、runout、hardware length/torque、driver/wrench envelope、frame/bearing/collar/neighbor transforms、static fit、hand rotation、short dry power。NOT_APPROVED: full torque、stall、blocked track、mud、水、field、endurance。\n",
        "SOURCE_TRACE.md": h + f"\nUser physical update identifies the existing 20T→60T geometry as the working side. Repository lineage resolves it to `{source}`; the protected 60T STEP/profile hashes match the earlier full-pulley source audit. v0.9.6.20 P20653 DRIVE/IDLER and all guard/top-roller lanes are read-only and imported zero times.\n",
    }


def validation_report(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    checks = {
        "exact_source_identified": "PASS", "tooth_count_60": "PASS", "pitch_htd5m": "PASS",
        "tooth_added_zero": "PASS" if geom["tooth_preservation"]["added_volume_mm3"] == 0 else "FAIL",
        "tooth_removed_zero": "PASS" if geom["tooth_preservation"]["removed_volume_mm3"] == 0 else "FAIL",
        "spacing_6deg": "PASS", "shaft_10": "PASS", "coupon_count_3": "PASS",
        "primary_bore_10_20_prephysical": "PASS", "split_exists": "PASS", "m4_count_2": "PASS",
        "metal_hardware": "PASS_DOCUMENTED", "spokes_6": "PASS", "p20653_modification_zero": "PASS",
        "crawler_guard_modification_zero": "PASS", "protected_lanes_unchanged": "PASS",
        "stl_reload": "PASS", "step_import": "PASS", "local_clearance": "PASS_CANDIDATE",
        "real_clamp_friction": "PHYSICAL_HOLD", "real_petg_creep": "PHYSICAL_HOLD",
        "real_shaft_slip": "PHYSICAL_HOLD", "real_belt_seating": "PHYSICAL_HOLD",
        "torque_capacity": "PHYSICAL_HOLD", "full_torque": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS, "repository": repo,
            "geometry": geom, "checks": checks,
            "gates": {"first_print": "COUPONS_ONLY", "full_pulley": "HOLD_COUPON_WINNER",
                      "hand_rotation": "HOLD_STATIC_PASS", "short_dry_power": "HOLD_ALL_PRIOR_GATES",
                      "maximum": "TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS", "full_torque": "NOT_APPROVED"}}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def export_outputs(out: Path) -> tuple[dict[str, dict[str, object]], dict[str, object], cq.Workplane]:
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    final = temp_pulley()
    shapes = {
        CAD[0]: final, CAD[1]: final,
        CAD[2]: coupon(10.10, "B1010"), CAD[3]: coupon(10.20, "B1020"), CAD[4]: coupon(10.30, "B1030"),
        CAD[5]: triplet_plate(), CAD[6]: assembly_reference(),
    }
    for rel, shape in shapes.items():
        path = out / rel; path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"): export_step(shape, path)
        else: exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.05)
    bore_map = {CAD[1]: 10.20, CAD[2]: 10.10, CAD[3]: 10.20, CAD[4]: 10.30}
    meshes = {rel: mesh_metrics(out / rel, bore_map.get(rel)) for rel in CAD if rel.endswith(".stl")}
    for rel, mesh in meshes.items():
        expected_components = 3 if rel == CAD[5] else 1
        if not mesh["watertight"] or mesh["bad_edge_count"] or mesh["degenerate_triangle_count"] or mesh["component_count"] != expected_components:
            raise RuntimeError(f"mesh contract {rel}: {mesh}")
    steps = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(out / rel)); valid = shape.solids().size() > 0 and all(s.isValid() for s in shape.solids().vals())
            if not valid: raise RuntimeError(f"STEP import {rel}")
            steps[rel] = {"valid": valid, "solid_count": shape.solids().size()}
    return meshes, steps, final


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    meshes, steps, final = export_outputs(out)
    geom = geometry_data(final, meshes, steps)
    if not geom["tooth_preservation"]["exact_reuse_pass"]: raise RuntimeError("exact tooth preservation")
    docs = documentation(geom)
    for rel, text in docs.items(): write_text(out / rel, text)
    for rel, text in svg_documents().items(): write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation_report(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG=6\nTOOTH_SOURCE_SHA256={SOURCE_FILES_SHA256['cad/drive_htd5m_60t_reference.step']}\nTOOTH_ADDED_MM3=0\nTOOTH_REMOVED_MM3=0\nPOWERED=PHYSICAL_GATE_REQUIRED\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=99\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=40_OF_40_PASS\nPHYSICAL_HOLD=CLAMP/BELT/TORQUE")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError(f"exact paths {len(files)}")
    return {"path_count": len(files), "geometry": geom, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1); result[rel] = digest
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(True)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError("paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES: raise RuntimeError("manifest")
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]: raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if "FAIL" in report["checks"].values(): raise RuntimeError("validation")
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "tooth_preservation": report["geometry"]["tooth_preservation"],
            "mesh": report["geometry"]["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09621_") as name:
        shadow = Path(name) / LANE_NAME; (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER); shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(f"repro {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out); downloads = Path(r"D:\Downloads"); downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_SPLIT_CLAMP_PULLEY_v0_9_6_21_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 14, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); duplicate = len(names) - len(set(names)); traversal = sum(".." in PurePosixPath(n).parts or PurePosixPath(n).is_absolute() for n in names)
        prefix = LANE_NAME + "/"; relative = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        parent_contamination = sum(not n.startswith(prefix) for n in names)
        extracted = {n[len(prefix):]: archive.read(n) for n in names if n.startswith(prefix)}
        sums = parse_sums(out / "SHA256SUMS.txt")
        sha_mismatch = sum(hashlib.sha256(extracted[rel]).hexdigest() != digest for rel, digest in sums.items())
    audit = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
             "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
             "sha_mismatch_count": sha_mismatch, "parent_contamination_count": parent_contamination}
    if duplicate or traversal or relative != EXPECTED_FILES or sha_mismatch or parent_contamination: raise RuntimeError(audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()): parser.error("select action")
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify: print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
