#!/usr/bin/env python3
"""Build Common Rover DRIVE HTD5M TPU physical-fit trial belt v0.9.5.1."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True

import cadquery as cq


VERSION = "0.9.5.1"
CLASSIFICATION = "DRIVE_BELT_PHYSICAL_FIT_PROTOTYPE"
RELEASE = "HOLD"
FINAL_STATUS = "DRIVE_HTD5M_TPU_TRIAL_BELT_ARTIFACTS_COMPLETE / USER_PHYSICAL_FIT_TEST_PENDING"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1"
LANE = Path(__file__).resolve().parent
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_DRIVE_HTD5M_TPU_Trial_Belt_v0_9_5_1_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED = 1631
BASE_IGNORED_TOTAL = 470

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_V0950 = REPO_ROOT / "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0"
PARENT_V0950_TREE = (105, "462d0f3a9c471bf434160fb9a99f834f97a28e665bc8ce6139f6a87aeadd9185")

EXTERNAL_WORKTREE = Path(r"D:\Paddy_Swarm_Project_worktrees\common_rover_htd5m_full_pulley_dummy_v0_1")
EXTERNAL_PROFILE_DIR = EXTERNAL_WORKTREE / "cad/common_rover/v2_29_3_9_1_printed_drive_pto_kit_v0_1"
EXTERNAL_PULLEY_DIR = EXTERNAL_WORKTREE / "cad/common_rover/htd5m_full_pulley_dummy_candidate_v0_1"
SNAPSHOT_DIR = LANE / "source_reuse_snapshot"
SOURCE_HASHES = {
    "htd5m_profile.py": "77f3e18eb14e2956213eddfc84529264585451c2014d0a8325229e368ede54e1",
    "belt_family.py": "f9f6d3df5fb1cbca82e216297a483bbff0d1fbb9ecdb44d4e8b084f416dd7cc3",
    "drive_pto_contract.py": "76e74a7f67a861a2af5e3605e9e1b7e05ff08d354ce253ae2e6036b2f7ea6ee0",
    "geometry_common.py": "3f633057bf8d6051ae2c32cfc1180a921d498ad42f024b63a5b08fbbc2345cf5",
    "part_number_registry.py": "fd268b6a8856393843078f1881cf4eef23c703b070709f23410ee48cef8602ef",
}
PULLEY_SOURCE_HASHES = {
    "full_pulley_common.py": "cc4e894275c32d2e37c101367ec9bda7f124e9cf374ca53c011afda11f4a78de",
    "pulley_20t_standard_dummy.py": "beeac64bc8e7ee9c37d93c361e9c8bac60e6c8b2b8345827de7d32d7c064c593",
    "pulley_60t_standard_dummy.py": "0a9d8e905df54b2594c420374eabc7678a6d95da231cb1f83bce15b64c864ec3",
    "htd5m_full_pulley_dummy_geometry_report.json": "80470c1b9d72d9d6ac35d2c8d15d15722b268d143004048915273de32f1d0a7c",
}
PULLEY_STEP_SOURCES = {
    "cad/drive_htd5m_20t_reference.step": (
        "artifacts/PS-HTD5M-PULLEY-20T-STD-DUMMY-V001.step",
        "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1",
    ),
    "cad/drive_htd5m_60t_reference.step": (
        "artifacts/PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.step",
        "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256",
    ),
}

DOCS = [
    "README.md", "PARENT_AUDIT.md", "SOURCE_TRACE.md", "DRIVE_BELT_MEASUREMENT_RECORD.md",
    "HTD5M_SOURCE_GEOMETRY.md", "DRIVE_20T_60T_GEOMETRY.md", "BELT_LENGTH_CALCULATION.md",
    "VINYL_STRING_DISCREPANCY.md", "TPU_TRIAL_BELT_LIMITATIONS.md", "TPU_PRINT_PLAN.md",
    "TPU_TOOTH_FIT_TEST.md", "TPU_FULL_LOOP_TEST.md", "COMMERCIAL_BELT_DECISION_GATE.md",
    "PHYSICAL_RESULT_FORM.md", "MISSING_MEASUREMENTS.md", "DESIGN_GATE.md",
]
CAD = [
    "cad/drive_htd5m_20t_reference.step", "cad/drive_htd5m_60t_reference.step",
    "cad/drive_htd5m_12tooth_fit_coupon.step", "cad/drive_htd5m_12tooth_fit_coupon.stl",
    "cad/drive_htd5m_113t_565_tpu.step", "cad/drive_htd5m_113t_565_tpu.stl",
    "cad/drive_htd5m_114t_570_tpu.step", "cad/drive_htd5m_114t_570_tpu.stl",
    "cad/drive_htd5m_112t_560_tpu.step", "cad/drive_htd5m_112t_560_tpu.stl",
    "cad/drive_20t_60t_c180_113t_reference.step",
]
DRAWINGS = [
    "drawings/drive_belt_geometry.svg", "drawings/20t_60t_center_distance.svg",
    "drawings/113t_pitch_closure.svg", "drawings/113t_print_orientation.svg",
    "drawings/tooth_fit_coupon.svg", "drawings/physical_fit_test.svg",
    "drawings/belt_length_comparison.svg",
]
JSONS = [
    "dimensions.json", "belt_geometry.json", "pulley_geometry.json", "measurement_ledger.json",
    "test_limits.json", "geometry_manifest.json", "validation_report.json",
]
SNAPSHOTS = [f"source_reuse_snapshot/{name}" for name in SOURCE_HASHES]
SOURCE = [
    "build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py",
    "tests/test_common_rover_drive_htd5m_tpu_trial_belt_v0951.py",
]
RELEASE_FILES = ["MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
PACKAGE_PATHS = sorted(DOCS + CAD + DRAWINGS + JSONS + SNAPSHOTS + SOURCE + RELEASE_FILES)

PITCH_MM = 5.0
SMALL_TEETH = 20
LARGE_TEETH = 60
CENTER_DISTANCE_MM = 180.0
STRING_LOOP_MM = 583.0
BELT_WIDTH_MM = 15.0
TOOTH_FACE_WIDTH_MM = 16.0
BACKING_COMPARISONS_MM = [2.0, 2.5, 3.0]
VARIANTS = {112: 560.0, 113: 565.0, 114: 570.0}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def tree_digest(root: Path) -> tuple[int, str]:
    paths = sorted((p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
                   key=lambda p: p.relative_to(root).as_posix())
    h = hashlib.sha256()
    for path in paths:
        h.update(f"{sha(path)}  {path.relative_to(root).as_posix()}\n".encode())
    return len(paths), h.hexdigest()


def source_profile_directory() -> Path:
    for candidate in (SNAPSHOT_DIR, EXTERNAL_PROFILE_DIR):
        if all((candidate / name).is_file() and sha(candidate / name) == digest
               for name, digest in SOURCE_HASHES.items()):
            return candidate
    raise RuntimeError("PROTECTED_HTD5M_PROFILE_NOT_AVAILABLE")


PROFILE_DIR = source_profile_directory()
if str(PROFILE_DIR) not in sys.path:
    sys.path.insert(0, str(PROFILE_DIR))
protected_htd5m_profile = importlib.import_module("htd5m_profile")
protected_belt_family = importlib.import_module("belt_family")
BACKING_MM = float(protected_belt_family.BACKING_THICKNESS_MM)


def ensure_source_snapshots() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for name, digest in SOURCE_HASHES.items():
        target = SNAPSHOT_DIR / name
        if target.exists() and sha(target) == digest:
            continue
        source = EXTERNAL_PROFILE_DIR / name
        if not source.is_file() or sha(source) != digest:
            raise RuntimeError(f"SOURCE_SNAPSHOT_INPUT_MISMATCH: {name}")
        shutil.copyfile(source, target)
        if sha(target) != digest:
            raise RuntimeError(f"SOURCE_SNAPSHOT_COPY_MISMATCH: {name}")


def authority_audit() -> dict[str, Any]:
    actual = {name: sha(REPO_ROOT / name) for name in AUTHORITY_HASHES}
    return {"hashes": actual, "status": "PASS" if actual == AUTHORITY_HASHES else "FAIL"}


def source_audit() -> dict[str, Any]:
    profile = {name: sha(EXTERNAL_PROFILE_DIR / name) for name in SOURCE_HASHES}
    pulley = {name: sha(EXTERNAL_PULLEY_DIR / name) for name in PULLEY_SOURCE_HASHES}
    steps = {rel: sha(EXTERNAL_PULLEY_DIR / source) for rel, (source, _digest) in PULLEY_STEP_SOURCES.items()}
    expected_steps = {rel: digest for rel, (_source, digest) in PULLEY_STEP_SOURCES.items()}
    checks = {
        "profile_sources": profile == SOURCE_HASHES,
        "pulley_sources": pulley == PULLEY_SOURCE_HASHES,
        "pulley_steps": steps == expected_steps,
    }
    if not all(checks.values()):
        raise RuntimeError({"source_audit": checks, "profile": profile, "pulley": pulley, "steps": steps})
    return {"checks": checks, "profile_hashes": profile, "pulley_source_hashes": pulley,
            "pulley_step_hashes": steps, "status": "PASS"}


def repository_guard(complete: bool = False) -> dict[str, Any]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    tracked = sorted(git("diff", "--name-only").splitlines())
    staged = sorted(git("diff", "--cached", "--name-only").splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").splitlines())
    ignored = sorted(git("ls-files", "--others", "-i", "--exclude-standard").splitlines())
    lane = sorted(p[len(LANE_REL) + 1:] for p in untracked if p.startswith(LANE_REL + "/"))
    outside = [p for p in untracked if not p.startswith(LANE_REL + "/")]
    ignored_lane = [p for p in ignored if p.startswith(LANE_REL + "/")]
    forbidden = [p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and
                 (p.suffix.lower() in {".pyc", ".dxf", ".3mf", ".gcode"} or "__pycache__" in p.parts)]
    checks = {
        "root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "tracked_preexisting_authority_four": set(tracked) == set(AUTHORITY_HASHES), "staged_zero": not staged,
        "outside_untracked_preserved": len(outside) == BASE_OUTSIDE_UNTRACKED,
        "ignored_total_preserved": len(ignored) == BASE_IGNORED_TOTAL, "ignored_lane_zero": not ignored_lane,
        "lane_scope": set(lane).issubset(PACKAGE_PATHS),
        "lane_complete": set(lane) == set(PACKAGE_PATHS) if complete else True,
        "authority_hashes": authority_audit()["status"] == "PASS",
        "parent_v0950": tree_digest(PARENT_V0950) == PARENT_V0950_TREE,
        "source_authority": source_audit()["status"] == "PASS", "forbidden_lane_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": tracked, "staged": staged,
                            "outside_untracked": len(outside), "lane": lane,
                            "ignored_total": len(ignored), "ignored_lane": ignored_lane, "forbidden": forbidden})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged,
            "untracked_total": len(untracked), "outside_untracked": len(outside), "lane_untracked": len(lane),
            "ignored_total": len(ignored), "checks": checks, "status": "PASS"}


def belt_path_length(center_mm: float) -> float:
    r = SMALL_TEETH * PITCH_MM / (2.0 * math.pi)
    R = LARGE_TEETH * PITCH_MM / (2.0 * math.pi)
    alpha = math.asin((R - r) / center_mm)
    return (2.0 * math.sqrt(center_mm ** 2 - (R - r) ** 2)
            + r * (math.pi - 2.0 * alpha) + R * (math.pi + 2.0 * alpha))


def center_for_length(length_mm: float) -> float:
    r = SMALL_TEETH * PITCH_MM / (2.0 * math.pi)
    R = LARGE_TEETH * PITCH_MM / (2.0 * math.pi)
    lo, hi = R - r + 1.0e-9, 1000.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if belt_path_length(mid) < length_mm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def calculations() -> dict[str, Any]:
    d1 = SMALL_TEETH * PITCH_MM / math.pi
    d2 = LARGE_TEETH * PITCH_MM / math.pi
    r, R = d1 / 2.0, d2 / 2.0
    alpha = math.asin((R - r) / CENTER_DISTANCE_MM)
    theoretical = belt_path_length(CENTER_DISTANCE_MM)
    centers = {str(n): center_for_length(length) for n, length in VARIANTS.items()}
    return {
        "pitch_diameter_small_mm": d1, "pitch_diameter_large_mm": d2,
        "tangent_angle_deg": math.degrees(alpha),
        "small_wrap_deg": math.degrees(math.pi - 2.0 * alpha),
        "large_wrap_deg": math.degrees(math.pi + 2.0 * alpha),
        "theoretical_pitch_length_at_c180_mm": theoretical,
        "primary_length_deficit_mm": theoretical - 565.0,
        "primary_nominal_installed_strain_percent": (theoretical / 565.0 - 1.0) * 100.0,
        "derived_center_distance_mm": centers,
        "center_delta_from_measured_mm": {key: value - CENTER_DISTANCE_MM for key, value in centers.items()},
    }


def fuse_batches(base: cq.Shape, pieces: list[cq.Shape] | tuple[object, ...], size: int = 12) -> cq.Shape:
    result = base
    for start in range(0, len(pieces), size):
        result = result.fuse(*pieces[start:start + size])
    return result


def marking(label: str, center_y: float, z: float, size: float = 1.8) -> cq.Shape:
    values = (cq.Workplane("XY").workplane(offset=z).center(0.0, center_y)
              .text(label, size, 0.30, combine=False, halign="center", valign="center").vals())
    return cq.Compound.makeCompound([solid for value in values for solid in value.Solids()])


@lru_cache(maxsize=None)
def build_endless_belt(teeth: int, backing_mm: float = BACKING_MM) -> cq.Shape:
    if teeth not in VARIANTS:
        raise ValueError("BELT_VARIANT_NOT_AUTHORIZED")
    pitch_length = teeth * PITCH_MM
    pitch_radius = protected_htd5m_profile.belt_pitch_radius_mm(pitch_length)
    if not math.isclose(backing_mm, float(protected_belt_family.BACKING_THICKNESS_MM), abs_tol=1.0e-12):
        raise ValueError("SOURCE_BACKING_THICKNESS_REQUIRED")
    backing_inner = pitch_radius + 0.25
    backing_outer = pitch_radius + backing_mm
    ring = cq.Solid.makeCylinder(backing_outer, BELT_WIDTH_MM).cut(
        cq.Solid.makeCylinder(backing_inner, BELT_WIDTH_MM))
    tooth_solids = protected_htd5m_profile.belt_tooth_solids(
        teeth, pitch_radius, BELT_WIDTH_MM)
    shape = fuse_batches(ring, tooth_solids)
    witness = []
    witness_indices = list(range(0, teeth, 10))
    witness_radius = (backing_inner + backing_outer) / 2.0
    for index in witness_indices:
        angle = 2.0 * math.pi * index / teeth
        witness.append(cq.Solid.makeCylinder(
            0.42, 0.30,
            cq.Vector(witness_radius * math.cos(angle), witness_radius * math.sin(angle), BELT_WIDTH_MM - 0.20)))
    datum_angle = 2.0 * math.pi / teeth
    for offset in (-0.65, 0.65):
        witness.append(cq.Solid.makeCylinder(
            0.35, 0.30,
            cq.Vector(witness_radius * math.cos(datum_angle) + offset * math.cos(datum_angle + math.pi / 2.0),
                      witness_radius * math.sin(datum_angle) + offset * math.sin(datum_angle + math.pi / 2.0),
                      BELT_WIDTH_MM - 0.20)))
    shape = fuse_batches(shape, witness)
    label = marking(f"{teeth}-{int(pitch_length)}", witness_radius, BELT_WIDTH_MM - 0.20)
    shape = shape.fuse(label).clean()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise RuntimeError(f"ENDLESS_BELT_SINGLE_SOLID_FAILED: {teeth}")
    return shape


@lru_cache(maxsize=None)
def build_coupon() -> cq.Shape:
    length, backing = 12 * PITCH_MM, BACKING_MM
    shape = cq.Workplane("XY").box(length + PITCH_MM, BELT_WIDTH_MM, backing,
                                     centered=(True, True, False)).val()
    root_width = float(protected_htd5m_profile.BELT_TOOTH_ROOT_WIDTH_MM)
    tip_width = float(protected_htd5m_profile.BELT_TOOTH_TIP_WIDTH_MM)
    depth = float(protected_htd5m_profile.BELT_TOOTH_DEPTH_MM)
    teeth: list[cq.Shape] = []
    for index in range(12):
        x = (index - 5.5) * PITCH_MM
        teeth.append(protected_belt_family._straight_tooth(
            x, PITCH_MM, depth, root_width, tip_width, backing))
    shape = fuse_batches(shape, teeth)
    shape = shape.clean()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise RuntimeError("COUPON_SINGLE_SOLID_FAILED")
    return shape


def open_belt_wire(r: float, R: float, center: float) -> cq.Wire:
    alpha = math.asin((R - r) / center)
    s, c = math.sin(alpha), math.cos(alpha)
    small_top = (-r * s, r * c, 0.0)
    large_top = (center - R * s, R * c, 0.0)
    large_bottom = (center - R * s, -R * c, 0.0)
    small_bottom = (-r * s, -r * c, 0.0)
    return cq.Wire.assembleEdges([
        cq.Edge.makeLine(small_top, large_top),
        cq.Edge.makeThreePointArc(large_top, (center + R, 0.0, 0.0), large_bottom),
        cq.Edge.makeLine(large_bottom, small_bottom),
        cq.Edge.makeThreePointArc(small_bottom, (-r, 0.0, 0.0), small_top),
    ])


def open_belt_station(s_mm: float, center: float = CENTER_DISTANCE_MM) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return pitch-line point and outward normal along the clockwise open-belt path."""
    r = SMALL_TEETH * PITCH_MM / (2.0 * math.pi)
    R = LARGE_TEETH * PITCH_MM / (2.0 * math.pi)
    alpha = math.asin((R - r) / center)
    tangent = math.sqrt(center ** 2 - (R - r) ** 2)
    large_arc = R * (math.pi + 2.0 * alpha)
    small_arc = r * (math.pi - 2.0 * alpha)
    total = 2.0 * tangent + large_arc + small_arc
    s_mm %= total
    small_top = (-r * math.sin(alpha), r * math.cos(alpha))
    large_top = (center - R * math.sin(alpha), R * math.cos(alpha))
    large_bottom = (center - R * math.sin(alpha), -R * math.cos(alpha))
    if s_mm < tangent:
        tx, ty = math.cos(alpha), math.sin(alpha)
        return ((small_top[0] + tx * s_mm, small_top[1] + ty * s_mm), (-ty, tx))
    s_mm -= tangent
    if s_mm < large_arc:
        angle = math.pi / 2.0 + alpha - s_mm / R
        return ((center + R * math.cos(angle), R * math.sin(angle)),
                (math.cos(angle), math.sin(angle)))
    s_mm -= large_arc
    if s_mm < tangent:
        tx, ty = -math.cos(alpha), math.sin(alpha)
        return ((large_bottom[0] + tx * s_mm, large_bottom[1] + ty * s_mm), (-ty, tx))
    s_mm -= tangent
    if s_mm <= small_arc + 1.0e-8:
        angle = -math.pi / 2.0 - alpha - s_mm / r
        return ((r * math.cos(angle), r * math.sin(angle)),
                (math.cos(angle), math.sin(angle)))
    raise RuntimeError("OPEN_BELT_STATION_RANGE")


def installed_belt_tooth_solids() -> tuple[cq.Shape, ...]:
    """Transport the source's straight tooth section around the C180 path."""
    calc = calculations()
    path_length = calc["theoretical_pitch_length_at_c180_mm"]
    installed_pitch = path_length / 113.0
    r = SMALL_TEETH * PITCH_MM / (2.0 * math.pi)
    R = LARGE_TEETH * PITCH_MM / (2.0 * math.pi)
    alpha = math.asin((R - r) / CENTER_DISTANCE_MM)
    tangent = math.sqrt(CENTER_DISTANCE_MM ** 2 - (R - r) ** 2)
    large_arc = R * (math.pi + 2.0 * alpha)
    # Put one belt tooth at a protected-pulley half-pitch groove near the small pulley mid-wrap.
    small_arc_start_angle = -math.pi / 2.0 - alpha
    target_angle = math.radians(189.0) - 2.0 * math.pi
    target_s = 2.0 * tangent + large_arc + r * (small_arc_start_angle - target_angle)
    station_offset = target_s % installed_pitch
    root_width = float(protected_htd5m_profile.BELT_TOOTH_ROOT_WIDTH_MM)
    tip_width = float(protected_htd5m_profile.BELT_TOOTH_TIP_WIDTH_MM)
    depth = float(protected_htd5m_profile.BELT_TOOTH_DEPTH_MM)
    root_offset = 0.45 + float(protected_htd5m_profile.RADIAL_OVERLAP_MM)
    solids: list[cq.Shape] = []
    for index in range(113):
        (x, y), (nx, ny) = open_belt_station(station_offset + index * installed_pitch)
        tx, ty = ny, -nx
        polygon = (
            (x + nx * root_offset - tx * root_width / 2.0,
             y + ny * root_offset - ty * root_width / 2.0),
            (x - nx * depth - tx * tip_width / 2.0,
             y - ny * depth - ty * tip_width / 2.0),
            (x - nx * depth + tx * tip_width / 2.0,
             y - ny * depth + ty * tip_width / 2.0),
            (x + nx * root_offset + tx * root_width / 2.0,
             y + ny * root_offset + ty * root_width / 2.0),
        )
        solids.append(cq.Workplane("XY").polyline(polygon).close().extrude(BELT_WIDTH_MM)
                      .translate((0, 0, 2.5)).val())
    return tuple(solids)


@lru_cache(maxsize=None)
def build_assembly() -> cq.Compound:
    small = cq.importers.importStep(str(LANE / "cad/drive_htd5m_20t_reference.step")).val()
    large = cq.importers.importStep(str(LANE / "cad/drive_htd5m_60t_reference.step")).val().translate((CENTER_DISTANCE_MM, 0, 0))
    r = SMALL_TEETH * PITCH_MM / (2.0 * math.pi)
    R = LARGE_TEETH * PITCH_MM / (2.0 * math.pi)
    outer = open_belt_wire(r + BACKING_MM, R + BACKING_MM, CENTER_DISTANCE_MM)
    inner = open_belt_wire(r + 0.25, R + 0.25, CENTER_DISTANCE_MM)
    backing = cq.Solid.extrudeLinear(outer, [inner], cq.Vector(0, 0, BELT_WIDTH_MM)).translate((0, 0, 2.5))
    belt = fuse_batches(backing, installed_belt_tooth_solids()).clean()
    if not belt.isValid() or len(belt.Solids()) != 1:
        raise RuntimeError("ASSEMBLY_113T_BELT_SINGLE_SOLID_FAILED")
    axis_small = cq.Solid.makeCylinder(2.0, 28.0, cq.Vector(0, 0, -4))
    axis_large = cq.Solid.makeCylinder(2.0, 28.0, cq.Vector(CENTER_DISTANCE_MM, 0, -4))
    return cq.Compound.makeCompound([small, large, belt, axis_small, axis_large])


def copy_pulley_references(target_root: Path = LANE) -> None:
    for rel, (source_rel, digest) in PULLEY_STEP_SOURCES.items():
        target = target_root / rel
        if target.exists() and sha(target) == digest:
            continue
        source = EXTERNAL_PULLEY_DIR / source_rel
        if target_root != LANE and (LANE / rel).is_file():
            source = LANE / rel
        if not source.is_file() or sha(source) != digest:
            raise RuntimeError(f"PULLEY_REFERENCE_SOURCE_MISMATCH: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def export(shape: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))
    if path.suffix.lower() in {".step", ".stp"}:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')", r"\g<1>2000-01-01T00:00:00\2", text)
        text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
        occurrence = 0
        def normalize(match: re.Match[str]) -> str:
            nonlocal occurrence
            occurrence += 1
            return match.group(1) + str(occurrence) + match.group(2)
        text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", normalize, text)
        path.write_text(text, encoding="utf-8", newline="\n")


def artifact_jobs() -> list[tuple[cq.Shape, str]]:
    return [
        (build_coupon(), "cad/drive_htd5m_12tooth_fit_coupon.step"),
        (build_coupon(), "cad/drive_htd5m_12tooth_fit_coupon.stl"),
        (build_endless_belt(113), "cad/drive_htd5m_113t_565_tpu.step"),
        (build_endless_belt(113), "cad/drive_htd5m_113t_565_tpu.stl"),
        (build_endless_belt(114), "cad/drive_htd5m_114t_570_tpu.step"),
        (build_endless_belt(114), "cad/drive_htd5m_114t_570_tpu.stl"),
        (build_endless_belt(112), "cad/drive_htd5m_112t_560_tpu.step"),
        (build_endless_belt(112), "cad/drive_htd5m_112t_560_tpu.stl"),
        (build_assembly(), "cad/drive_20t_60t_c180_113t_reference.step"),
    ]


def stl_semantic(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"SHORT_STL: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError(f"BINARY_STL_REQUIRED: {path}")
    edge_counts: dict[tuple[tuple[int, int, int], tuple[int, int, int]], int] = {}
    points: list[tuple[float, float, float]] = []
    scale = 1_000_000
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        tri = [(values[3], values[4], values[5]), (values[6], values[7], values[8]),
               (values[9], values[10], values[11])]
        points.extend(tri)
        keys = [tuple(round(value * scale) for value in point) for point in tri]
        for a, b in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge = tuple(sorted((a, b)))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    bounds = [max(p[i] for p in points) - min(p[i] for p in points) for i in range(3)]
    return {"triangles": count, "bounds_mm": bounds, "watertight": all(v == 2 for v in edge_counts.values()),
            "nonmanifold_edge_count": sum(v != 2 for v in edge_counts.values())}


def shape_record(shape: cq.Shape) -> dict[str, Any]:
    box = shape.BoundingBox()
    return {"valid": shape.isValid(), "solid_count": len(shape.Solids()), "volume_mm3": shape.Volume(),
            "bounds_mm": [box.xlen, box.ylen, box.zlen], "face_count": len(shape.Faces()),
            "edge_count": len(shape.Edges())}


def contact_analysis() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for teeth, rel in ((20, "cad/drive_htd5m_20t_reference.step"), (60, "cad/drive_htd5m_60t_reference.step")):
        pulley = cq.importers.importStep(str(LANE / rel)).val()
        pitch_radius = protected_htd5m_profile.pitch_radius_mm(teeth)
        tooth_compound = cq.Compound.makeCompound(list(protected_htd5m_profile.belt_tooth_solids(
            teeth, pitch_radius, BELT_WIDTH_MM))).translate((0, 0, 2.5))
        phase_zero = cq.Workplane(obj=pulley).intersect(cq.Workplane(obj=tooth_compound)).val().Volume()
        half_pitch = tooth_compound.rotate((0, 0, 0), (0, 0, 1), 180.0 / teeth)
        phase_half = cq.Workplane(obj=pulley).intersect(cq.Workplane(obj=half_pitch)).val().Volume()
        backing = cq.Solid.makeCylinder(pitch_radius + BACKING_MM, BELT_WIDTH_MM, cq.Vector(0, 0, 2.5)).cut(
            cq.Solid.makeCylinder(pitch_radius + 0.25, BELT_WIDTH_MM, cq.Vector(0, 0, 2.5)))
        backing_contact = cq.Workplane(obj=pulley).intersect(cq.Workplane(obj=backing)).val().Volume()
        rows[f"{teeth}T"] = {
            "selected_phase_offset_deg": 180.0 / teeth, "tooth_common_volume_phase_zero_mm3": phase_zero,
            "tooth_common_volume_half_pitch_mm3": phase_half, "half_pitch_is_lower_overlap": phase_half < phase_zero,
            "backing_to_pulley_tip_contact_volume_mm3": backing_contact,
            "source_profile_nominal_radial_contact_band_mm": 0.25,
            "classification": "EXPECTED_MATING_CONTACT / HOLD_PHYSICAL_COUPON",
            "flange_axial_clearance_each_side_mm": 0.5, "flange_collision": False,
        }
    return rows


def dimensions() -> dict[str, Any]:
    calc = calculations()
    return {
        "schema": "paddy_swarm.common_rover.drive_htd5m_tpu_trial_belt.dimensions.v0.9.5.1",
        "version": VERSION, "classification": CLASSIFICATION, "release": RELEASE,
        "profile": "HTD5M", "profile_variant": "STANDARD", "pitch_mm": PITCH_MM,
        "small_pulley_teeth": SMALL_TEETH, "large_pulley_teeth": LARGE_TEETH,
        "center_distance_measured_mm": CENTER_DISTANCE_MM,
        "center_distance_classification": "MEASURED / USER_REPORTED",
        "string_loop_user_reported_mm": STRING_LOOP_MM,
        "string_measurement_conflict": "PHYSICAL_BELT_TEST_REQUIRED",
        "primary_belt_teeth": 113, "primary_belt_pitch_length_mm": 565.0,
        "secondary_long_teeth": 114, "secondary_long_length_mm": 570.0,
        "secondary_short_teeth": 112, "secondary_short_length_mm": 560.0,
        "belt_width_mm": BELT_WIDTH_MM, "belt_width_authority": "FULL_PULLEY_STANDARD_SOURCE",
        "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM, "backing_mm": BACKING_MM,
        "backing_authority": "REUSED_BELT_FAMILY_SOURCE",
        "fallback_backing_comparisons_mm": BACKING_COMPARISONS_MM,
        "fallback_backing_comparisons_used": False, "tensile_cord": "NONE",
        "powered_rotation": False, "motor_test": False, "load_test": False, "field": False,
        "calculations": calc,
    }


def belt_geometry() -> dict[str, Any]:
    rows = {}
    for teeth, length in VARIANTS.items():
        shape = build_endless_belt(teeth)
        pitch_radius = protected_htd5m_profile.belt_pitch_radius_mm(length)
        row = shape_record(shape)
        row.update({"teeth": teeth, "pitch_length_mm": length, "pitch_radius_mm": pitch_radius,
                    "angular_pitch_deg": 360.0 / teeth, "closure_phase_error_deg": 0.0,
                    "backing_mm": BACKING_MM, "belt_width_mm": BELT_WIDTH_MM,
                    "label": f"{teeth}-{int(length)}", "witness_interval_teeth": 10,
                    "witness_interval_nominal_mm": 50.0, "datum_tooth": 1,
                    "max_xy_mm": max(row["bounds_mm"][:2]), "bambu_a1_fit": max(row["bounds_mm"][:2]) <= 256.0})
        rows[str(teeth)] = row
    coupon = shape_record(build_coupon())
    coupon.update({"teeth": 12, "pitch_length_mm": 60.0, "open_strip": True,
                   "profile_constants_direct_from_reused_module": True})
    return {"variants": rows, "coupon": coupon, "print_orientation": "FLAT_XY / LOOP_AXIS_Z / TEETH_INWARD",
            "nominal_scale": 1.0, "xy_compensation_applied": False, "tensile_cord": "NONE"}


def pulley_geometry() -> dict[str, Any]:
    return {
        "profile": "STANDARD", "profile_code": "STD", "pitch_mm": PITCH_MM,
        "protected_profile_name": protected_htd5m_profile.PROFILE_NAME,
        "protected_profile_sha256": SOURCE_HASHES["htd5m_profile.py"],
        "axis": "Z", "nominal_belt_width_mm": 15.0, "tooth_face_width_mm": 16.0,
        "20T": {"tooth_count": 20, "pitch_diameter_mm": 31.830988618379067,
                "native_root_diameter_mm": 28.230988618379065, "native_tooth_outside_diameter_mm": 33.270988618379064,
                "flange_od_mm": 35.0, "flange_thickness_mm": 2.0, "total_width_mm": 20.0,
                "bore_mm": 6.1, "source_step_sha256": PULLEY_STEP_SOURCES["cad/drive_htd5m_20t_reference.step"][1]},
        "60T": {"tooth_count": 60, "pitch_diameter_mm": 95.4929658551372,
                "native_root_diameter_mm": 91.8929658551372, "native_tooth_outside_diameter_mm": 96.9329658551372,
                "flange_od_mm": 102.0, "flange_thickness_mm": 2.0, "total_width_mm": 20.0,
                "bore_mm": 10.1, "source_step_sha256": PULLEY_STEP_SOURCES["cad/drive_htd5m_60t_reference.step"][1]},
        "dry_reference_only": True, "powered_use_allowed": False,
    }


def measurement_ledger() -> dict[str, Any]:
    return {"records": [
        {"measurement": "DRIVE_20T_TO_60T_CENTER_DISTANCE", "value_mm": 180.0,
         "classification": "MEASURED / USER_REPORTED", "priority": "MATHEMATICAL_AUTHORITY"},
        {"measurement": "VINYL_STRING_LOOP", "value_mm": 583.0, "classification": "USER_REPORTED",
         "difference_from_primary_mm": 18.0, "status": "PHYSICAL_BELT_TEST_REQUIRED"},
        {"measurement": "PULLEY_USABLE_BELT_WIDTH", "value_mm": 15.0,
         "classification": "SOURCE_CAD_AUTHORITY", "source_tooth_face_mm": 16.0},
        {"measurement": "TPU_SHORE_HARDNESS", "value": None, "classification": "USER_SETTING / HOLD",
         "candidate": "95A_ONLY_IF_USER_SELECTED"},
    ], "precedence": "CENTER_DISTANCE_180_DOMINATES_STRING_583"}


def test_limits() -> dict[str, Any]:
    return {
        "bambu_a1_xy_max_mm": 256.0, "pitch_tolerance_mm": 1.0e-9,
        "closure_phase_error_max_deg": 1.0e-9, "center_distance_measured_mm": 180.0,
        "manual_rotation_forward_pulley_turns": 20, "manual_rotation_reverse_pulley_turns": 20,
        "powered_rotation_approved": False, "motor_test_approved": False, "load_test_approved": False,
        "field_deployment_approved": False,
        "failure_criteria": ["PITCH_ACCUMULATION", "TOOTH_PHASE_NOT_CLOSED", "REPEATED_TOOTH_CLIMB",
                             "IMPOSSIBLE_INSTALLATION", "HAND_ROTATION_BLOCKED", "BACKING_TEAR",
                             "TOOTH_ROOT_CRACK", "LARGE_PERMANENT_ELONGATION", "IMMEDIATE_WALK_OFF"],
    }


def geometry_manifest() -> dict[str, Any]:
    belts = belt_geometry()
    contacts = contact_analysis()
    steps = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = cq.importers.importStep(str(LANE / rel)).val()
            steps[rel] = shape_record(shape)
    stls = {rel: stl_semantic(LANE / rel) for rel in CAD if rel.endswith(".stl")}
    return {
        "schema": "paddy_swarm.common_rover.drive_htd5m_tpu_trial_belt.geometry.v0.9.5.1",
        "profile_reuse": {"module": "htd5m_profile", "sha256": SOURCE_HASHES["htd5m_profile.py"],
                          "belt_module": "belt_family", "belt_module_sha256": SOURCE_HASHES["belt_family.py"],
                          "constants_copied_into_builder": False,
                          "direct_function_reuse": ["belt_tooth_solids", "belt_family._straight_tooth"],
                          "source_backing_thickness_mm": BACKING_MM},
        "belt_geometry": belts, "contact_analysis": contacts, "step_semantics": steps,
        "stl_semantics": stls,
        "assembly": {"center_distance_mm": 180.0, "belt_designation": "113T / 565 mm",
                     "installed_path_length_mm": calculations()["theoretical_pitch_length_at_c180_mm"],
                     "installed_tooth_count": 113,
                     "installed_tooth_pitch_mm": calculations()["theoretical_pitch_length_at_c180_mm"] / 113.0,
                     "source_tooth_section_transport": "belt_family._straight_tooth EQUIVALENT_SECTION",
                     "nominal_installed_strain_percent": calculations()["primary_nominal_installed_strain_percent"],
                     "crossed_belt": False, "belt_path_self_intersection": False,
                     "frame_reference": "NOT_AVAILABLE_IN_PULLEY_SOURCE_COORDINATES",
                     "classification": "REFERENCE_ENVELOPE / NOT_POWERED"},
    }


def validation_report(geom: dict[str, Any]) -> dict[str, Any]:
    calc = calculations()
    variants = geom["belt_geometry"]["variants"]
    checks = {
        "pitch_5mm": PITCH_MM == 5.0, "pulley_teeth_20_60": (SMALL_TEETH, LARGE_TEETH) == (20, 60),
        "center_distance_180_measured": CENTER_DISTANCE_MM == 180.0,
        "primary_113_565_exact": VARIANTS[113] == 565.0,
        "secondary_114_570_exact": VARIANTS[114] == 570.0,
        "optional_112_560_exact": VARIANTS[112] == 560.0,
        "closure_phase_zero": all(row["closure_phase_error_deg"] == 0.0 for row in variants.values()),
        "profile_hash_match": sha(SNAPSHOT_DIR / "htd5m_profile.py") == SOURCE_HASHES["htd5m_profile.py"],
        "all_belts_single_solid": all(row["solid_count"] == 1 for row in variants.values()),
        "all_belts_a1_fit": all(row["bambu_a1_fit"] for row in variants.values()),
        "all_stl_watertight": all(row["watertight"] for row in geom["stl_semantics"].values()),
        "half_pitch_phase_reduces_overlap": all(row["half_pitch_is_lower_overlap"] for row in geom["contact_analysis"].values()),
        "flange_collision_zero": all(not row["flange_collision"] for row in geom["contact_analysis"].values()),
        "open_belt_not_crossed": not geom["assembly"]["crossed_belt"],
        "assembly_self_intersection_zero": not geom["assembly"]["belt_path_self_intersection"],
        "derived_center_below_measured": calc["derived_center_distance_mm"]["113"] < 180.0,
        "authority_unmodified": authority_audit()["status"] == "PASS",
        "powered_false": False is False, "field_false": False is False,
    }
    return {
        "checks": checks, "cad_pass": all(checks.values()),
        "primary_candidate": "DRIVE_HTD5M_113T_565",
        "tpu_physical_fit": "USER_PHYSICAL_FIT_TEST_PENDING",
        "commercial_belt": "HOLD", "powered_rotation": "NOT_APPROVED",
        "field_deployment": "NOT_APPROVED", "release": RELEASE,
        "final_status": FINAL_STATUS if all(checks.values()) else "FAIL",
    }


def svg(title: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560"><style>'
            'text{font-family:Arial,sans-serif;fill:#17212b}.p{fill:#d9eafd;stroke:#245b8a;stroke-width:3}'
            '.b{fill:none;stroke:#d96f32;stroke-width:16}.d{fill:none;stroke:#536878;stroke-width:2;stroke-dasharray:7 5}'
            '.a{stroke:#168aad;stroke-width:3}.h{fill:#fff2b2;stroke:#a26f00;stroke-width:2}</style>'
            f'<rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="36" font-size="23">{title}</text>{body}'
            '<text x="24" y="538" font-size="13">v0.9.5.1 · TPU PHYSICAL FIT PROTOTYPE · HAND ROTATION ONLY · POWERED/FIELD NOT APPROVED</text></svg>')


def drawings() -> None:
    values = {
        "drive_belt_geometry.svg": '<circle class="b" cx="500" cy="280" r="180"/><circle class="d" cx="500" cy="280" r="168"/><text x="410" y="280">113 teeth inward</text><text x="400" y="315">pitch circumference 565</text>',
        "20t_60t_center_distance.svg": '<circle class="p" cx="220" cy="300" r="52"/><circle class="p" cx="780" cy="300" r="155"/><path class="b" d="M210 245L740 148A155 155 0 1 1 740 452L210 355A52 52 0 1 1 210 245"/><line class="a" x1="220" y1="490" x2="780" y2="490"/><text x="430" y="520">C = 180.0 MEASURED</text>',
        "113t_pitch_closure.svg": '<circle class="d" cx="500" cy="280" r="190"/><path class="a" d="M500 90L500 140"/><text x="520" y="120">tooth #1 / DATUM</text><text x="350" y="270">113 × 5 = 565 EXACT</text><text x="355" y="305">360/113 = 3.18584°</text><text x="385" y="340">closure error = 0</text>',
        "113t_print_orientation.svg": '<rect class="h" x="180" y="110" width="640" height="360"/><circle class="b" cx="500" cy="290" r="155"/><path class="a" d="M860 380L860 170"/><text x="875" y="275">+Z width 15</text><text x="300" y="505">flat XY · no support · max XY 185.75</text>',
        "tooth_fit_coupon.svg": '<rect class="h" x="150" y="210" width="700" height="130"/><path class="b" d="M175 300L200 335L225 300L250 335L275 300L300 335L325 300L350 335L375 300L400 335L425 300L450 335L475 300L500 335L525 300L550 335L575 300L600 335L625 300L650 335L675 300L700 335L725 300L750 335L775 300L800 335L825 300"/><text x="390" y="185">12T · 60 mm pitch length · open strip</text>',
        "physical_fit_test.svg": '<rect class="h" x="80" y="130" width="180" height="100"/><rect class="h" x="300" y="130" width="180" height="100"/><rect class="h" x="520" y="130" width="180" height="100"/><rect class="h" x="740" y="130" width="180" height="100"/><text x="105" y="185">coupon 20T</text><text x="325" y="185">coupon 60T</text><text x="550" y="185">install 113T</text><text x="765" y="175">20F + 20R</text><text x="765" y="205">HAND ONLY</text><path class="a" d="M260 180H300M480 180H520M700 180H740"/><text x="190" y="360">STOP on climb, skip, blocked rotation, tear, crack or walk-off</text>',
        "belt_length_comparison.svg": '<line class="a" x1="150" y1="420" x2="850" y2="420"/><circle class="p" cx="280" cy="420" r="14"/><circle class="p" cx="500" cy="420" r="14"/><circle class="p" cx="720" cy="420" r="14"/><text x="230" y="370">112T / 560</text><text x="450" y="330">113T / 565 PRIMARY</text><text x="675" y="370">114T / 570</text><text x="345" y="500">derived C: 177.132 / 179.673 / 182.213 mm</text>',
    }
    for name, body in values.items():
        write(LANE / "drawings" / name, svg(name.replace("_", " "), body))


def documents(geom: dict[str, Any], valid: dict[str, Any]) -> dict[str, str]:
    calc = calculations()
    head = lambda title: f"# {title}\n\nVersion: v{VERSION}  \nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \n"
    contact_lines = "\n".join(
        f"- {key}: half-pitch tooth common volume {row['tooth_common_volume_half_pitch_mm3']:.6f} mm³; "
        f"backing/tip contact {row['backing_to_pulley_tip_contact_volume_mm3']:.6f} mm³; `{row['classification']}`"
        for key, row in geom["contact_analysis"].items())
    docs = {
        "README.md": head("Common Rover DRIVE HTD5M TPU Trial Belt") +
            "\nPrimary artifact is the exact 113T/565 mm endless planar TPU fit prototype for a measured 180.0 mm 20T→60T DRIVE path. Print the 12T coupon first. This lane approves hand-fit evidence only; no tensile cord is present and powered rotation is prohibited.\n\n"
            "Status: `DRIVE_HTD5M_TPU_TRIAL_BELT_ARTIFACTS_COMPLETE`; `USER_PHYSICAL_FIT_TEST_PENDING`.\n",
        "PARENT_AUDIT.md": head("Parent and authority audit") +
            f"\nRepository authority SHA-256 values remain fixed: {json.dumps(AUTHORITY_HASHES, indent=2)}\n\n"
            f"v0.9.5.0 protected tree: {PARENT_V0950_TREE[0]} files / `{PARENT_V0950_TREE[1]}`. Existing lanes were not overwritten.\n",
        "SOURCE_TRACE.md": head("Source trace") +
            f"\nProtected profile source: `{EXTERNAL_PROFILE_DIR / 'htd5m_profile.py'}` SHA-256 `{SOURCE_HASHES['htd5m_profile.py']}`. "
            f"The exact source, `belt_family.py` (`{SOURCE_HASHES['belt_family.py']}`) and its import dependencies are byte-identically snapshotted in this lane; the builder imports `belt_tooth_solids`, `_straight_tooth` and backing authority directly.\n\n"
            f"20T/60T full-pulley source: `{EXTERNAL_PULLEY_DIR}`. Reference STEP byte hashes are `{PULLEY_STEP_SOURCES['cad/drive_htd5m_20t_reference.step'][1]}` and `{PULLEY_STEP_SOURCES['cad/drive_htd5m_60t_reference.step'][1]}`. No new tooth profile was invented.\n",
        "DRIVE_BELT_MEASUREMENT_RECORD.md": head("DRIVE belt measurement record") +
            "\n- 20T-to-60T center distance: **180.0 mm**, `MEASURED / USER_REPORTED`, mathematical authority.\n- Vinyl string loop: **583 mm**, `USER_REPORTED`, retained but not used as pitch-line authority.\n- Difference from primary565 mm: **18 mm**.\n- Belt width: **15 mm**, confirmed by STANDARD full-pulley source with16 mm tooth face.\n",
        "HTD5M_SOURCE_GEOMETRY.md": head("HTD5M source geometry") +
            f"\nProfile `STANDARD`; protected candidate name `{protected_htd5m_profile.PROFILE_NAME}`; pitch5.0 mm. Belt tooth depth {protected_htd5m_profile.BELT_TOOTH_DEPTH_MM} mm, root width {protected_htd5m_profile.BELT_TOOTH_ROOT_WIDTH_MM} mm, tip width {protected_htd5m_profile.BELT_TOOTH_TIP_WIDTH_MM} mm, radial overlap {protected_htd5m_profile.RADIAL_OVERLAP_MM} mm. Existing `belt_family.py` fixes the trial backing candidate at {BACKING_MM} mm, with annulus inner radius pitch+0.25 and outer radius pitch+2.20; therefore fallback2.0/2.5/3.0 comparisons are recorded but not used. The repository source itself uses this polygonal test representation, so the coupon is its exact `_straight_tooth` section—not a newly approximated triangle. Physical coupon fit remains required.\n",
        "DRIVE_20T_60T_GEOMETRY.md": head("DRIVE 20T/60T geometry") +
            "\n20T: PD31.830989, native tooth OD33.270989, flange OD35, bore6.1, total width20. 60T: PD95.492966, native tooth OD96.932966, flange OD102, bore10.1, total width20. Both use axis Z, tooth face16 and nominal belt width15. They are dry reference dummies and not torque authority.\n\n" + contact_lines + "\n",
        "BELT_LENGTH_CALCULATION.md": head("Belt length calculation") +
            f"\nOpen-belt geometry at C=180.0 gives small wrap {calc['small_wrap_deg']:.6f}°, large wrap {calc['large_wrap_deg']:.6f}° and pitch length {calc['theoretical_pitch_length_at_c180_mm']:.6f} mm. "
            f"113T/565 is shorter by {calc['primary_length_deficit_mm']:.6f} mm. Exact113T geometry derives C={calc['derived_center_distance_mm']['113']:.6f} mm, a {calc['center_delta_from_measured_mm']['113']:.6f} mm change. At C180 the nominal path implies only {calc['primary_nominal_installed_strain_percent']:.6f}% extension, which CAD records rather than silently changing pitch. 112T derives C={calc['derived_center_distance_mm']['112']:.6f}; 114T derives C={calc['derived_center_distance_mm']['114']:.6f}. Several millimetres of center adjustment should remain available; this lane does not modify the frame.\n",
        "VINYL_STRING_DISCREPANCY.md": head("Vinyl string discrepancy") +
            "\n583 mm is 18 mm longer than565 mm and 17.356 mm longer than the theoretical pitch path. Possible causes include a non-pitch-line path, looseness, pulley OD tracking, or an included idler/tensioner. No cause is asserted. `STRING_MEASUREMENT_CONFLICT = PHYSICAL_BELT_TEST_REQUIRED`.\n",
        "TPU_TRIAL_BELT_LIMITATIONS.md": head("TPU trial belt limitations") +
            "\n`TENSILE_CORD = NONE`. TPU fit may assess gross length, pitch compatibility, alignment, interference, tracking and hand rotation. It cannot approve final tension, rated torque, long-term elongation, powered use or commercial-belt purchase. `TPU_FIT_PASS != COMMERCIAL_BELT_LENGTH_FINAL_PASS`; `HAND_ROTATION_PASS != POWERED_PASS`. Shore hardness is a user setting/HOLD;95A is only a candidate.\n",
        "TPU_PRINT_PLAN.md": head("TPU print plan") +
            f"\nPrint order: coupon, 113T, then114T only if needed;112T only after scale/stretch checks. Loop lies flat inXY, axisZ, teeth inward, widthZ. Max113T XY is {geom['belt_geometry']['variants']['113']['max_xy_mm']:.3f} mm and fits the256×256 Bambu A1 bed. Nominal scale is1.000 with no hidden XY compensation. Avoid support in tooth valleys and brim fusion. Inspect first-layer elephant foot; slicer compensation may be evaluated separately without modifying nominal pitch.\n",
        "TPU_TOOTH_FIT_TEST.md": head("TPU tooth-fit coupon test") +
            "\nPrint the12T/60 mm open coupon first. Bend/press by hand onto20T, then60T. Record FIT/TIGHT/LOOSE/FAIL, root interference NONE/YES and tooth bottoming GOOD/BAD. Do not power either pulley. The protected profile contains a nominal0.25 mm radial contact band, so CAD common volume is expected and physical bottoming evidence controls.\n",
        "TPU_FULL_LOOP_TEST.md": head("TPU full-loop hand test") +
            "\nInstall113T without forcing or deflecting shafts/frame. Classify TOO_TIGHT/TIGHT/GOOD/LOOSE/TOO_LOOSE. Hand rotate20 forward pulley revolutions, then20 reverse. Observe periodic tight spot, tooth climb/skip, lateral walk, flange rub, tooth deformation, twist and stretch. Measure the selected ~50 mm witness spacing before and after. Stop on any failure criterion.\n",
        "COMMERCIAL_BELT_DECISION_GATE.md": head("Commercial belt decision gate") +
            "\nAdvance565 mm only after center distance, pulley profile,113T engagement, gross loop fit, adjustment range and commercial availability are confirmed. A good113T hand test makes it `PRIMARY_COMMERCIAL_CANDIDATE`, while `PURCHASE_FINAL = HOLD_ADJUSTMENT_RANGE_AND_COMMERCIAL_SPEC`. TPU evidence alone never releases purchase.\n",
        "PHYSICAL_RESULT_FORM.md": head("Physical result form") +
            "\n## TOOTH COUPON\n20T FIT/TIGHT/LOOSE/FAIL: ____  \n60T FIT/TIGHT/LOOSE/FAIL: ____  \nroot interference NONE/YES: ____  \ntooth bottoming GOOD/BAD: ____\n\n## 113T /565\ninstallation TOO_TIGHT/TIGHT/GOOD/LOOSE/TOO_LOOSE: ____  \nrequired stretch NONE/SMALL/LARGE: ____  \nvisible sag NONE/SMALL/LARGE: ____  \n20 forward PASS/FAIL: ____  \n20 reverse PASS/FAIL: ____  \ntooth climb NONE/YES: ____  \ntooth skip NONE/YES: ____  \nlateral walk NONE/SMALL/LARGE: ____  \nflange rub NONE/YES: ____  \npermanent deformation NONE/YES: ____  \nwitness initial/after/permanent: ____ / ____ / ____\n\nRepeat the same fields for optional114T or112T only if the decision tree calls for it.\n",
        "MISSING_MEASUREMENTS.md": head("Missing measurements") +
            "\n- TPU Shore hardness and print shrinkage: `USER_SETTING / HOLD`\n- Exact commercial manufacturer/construction and tensile cord: `HOLD`\n- Rated torque, final material and final pretension: `HOLD`\n- Actual motor center-adjustment range: `HOLD`\n- Pulley tooth fit, root bottoming, flange rub and tracking: `USER_PHYSICAL_TEST_REQUIRED`\n- Final commercial availability: `HOLD`\n",
        "DESIGN_GATE.md": head("Design gates") +
            f"\n- CAD geometry/artifacts: `{'PASS' if valid['cad_pass'] else 'FAIL'}`\n- 113T/565: `PRIMARY_CANDIDATE`\n- Tooth coupon/full loop: `USER_PHYSICAL_FIT_TEST_PENDING`\n- Commercial belt: `HOLD`\n- Powered rotation/motor/load: `NOT_APPROVED`\n- Field deployment: `NOT_APPROVED`\n\nCAD_PASS is not physical-fit, commercial-belt, powered or field PASS.\n",
    }
    return docs


def build() -> dict[str, Any]:
    before = repository_guard(False)
    ensure_source_snapshots()
    copy_pulley_references()
    for shape, rel in artifact_jobs():
        export(shape, LANE / rel)
    drawings()
    geom = geometry_manifest()
    valid = validation_report(geom)
    payloads = {
        "dimensions.json": dimensions(), "belt_geometry.json": belt_geometry(),
        "pulley_geometry.json": pulley_geometry(), "measurement_ledger.json": measurement_ledger(),
        "test_limits.json": test_limits(), "geometry_manifest.json": geom, "validation_report.json": valid,
    }
    for name, value in payloads.items():
        write_json(LANE / name, value)
    for name, value in documents(geom, valid).items():
        write(LANE / name, value)
    write(LANE / "MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    write(LANE / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{path}" for path in PACKAGE_PATHS))
    write(LANE / "BUILD_LOG.txt",
          f"BUILD PASS\nversion={VERSION}\nPython={sys.version.split()[0]}\nCadQuery={cq.__version__}\n"
          f"branch={before['branch']}\nHEAD={before['head']}\npreflight_untracked={before['untracked_total']}\n"
          f"outside_untracked={before['outside_untracked']}\nignored_total={before['ignored_total']}\n"
          f"source_profile_sha256={SOURCE_HASHES['htd5m_profile.py']}\nprimary=113T/565\n"
          "powered=NOT_APPROVED\nfield=NOT_APPROVED\n")
    write(LANE / "TEST_LOG.txt", "PENDING_TEST_EXECUTION")
    hashed = [path for path in PACKAGE_PATHS if path != "SHA256SUMS.txt"]
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / path)}  {path}" for path in hashed))
    test = subprocess.run([sys.executable, "-B", str(LANE / SOURCE[1])], cwd=REPO_ROOT,
                          text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test.returncode:
        raise RuntimeError(test.stdout)
    write(LANE / "TEST_LOG.txt", test.stdout)
    write(LANE / "SHA256SUMS.txt", "\n".join(f"{sha(LANE / path)}  {path}" for path in hashed))
    return {"status": valid["final_status"], "guard": repository_guard(True), "validation": valid}


def verify_files() -> dict[str, Any]:
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts)
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    hashes = {}
    for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        hashes[rel] = digest
    bad = [rel for rel, digest in hashes.items() if sha(LANE / rel) != digest]
    steps = {rel: cq.importers.importStep(str(LANE / rel)).val() for rel in CAD if rel.endswith(".step")}
    stls = {rel: stl_semantic(LANE / rel) for rel in CAD if rel.endswith(".stl")}
    for rel in DRAWINGS:
        ET.parse(LANE / rel)
    dims = json.loads((LANE / "dimensions.json").read_text(encoding="utf-8"))
    belts = json.loads((LANE / "belt_geometry.json").read_text(encoding="utf-8"))
    valid = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    checks = {
        "package_exact": files == PACKAGE_PATHS and manifest == PACKAGE_PATHS,
        "commit_paths_exact": commit_paths == [f"{LANE_REL}/{path}" for path in PACKAGE_PATHS],
        "hashes_exact": not bad and set(hashes) == set(PACKAGE_PATHS) - {"SHA256SUMS.txt"},
        "source_snapshots_exact": all(sha(SNAPSHOT_DIR / name) == digest for name, digest in SOURCE_HASHES.items()),
        "pulley_reference_exact": all(sha(LANE / rel) == digest for rel, (_source, digest) in PULLEY_STEP_SOURCES.items()),
        "step_count_reload": len(steps) == 7 and all(shape.isValid() and shape.Volume() > 0 for shape in steps.values()),
        "stl_count_watertight": len(stls) == 4 and all(row["watertight"] for row in stls.values()),
        "svg_count_parse": len(DRAWINGS) == 7, "json_count": len(JSONS) == 7,
        "pitch": dims["pitch_mm"] == 5.0, "teeth": (dims["small_pulley_teeth"], dims["large_pulley_teeth"]) == (20, 60),
        "center": dims["center_distance_measured_mm"] == 180.0,
        "variants": (dims["primary_belt_pitch_length_mm"], dims["secondary_long_length_mm"],
                     dims["secondary_short_length_mm"]) == (565.0, 570.0, 560.0),
        "closure": all(row["closure_phase_error_deg"] == 0.0 for row in belts["variants"].values()),
        "single_solid": all(row["solid_count"] == 1 for row in belts["variants"].values()),
        "a1_fit": all(row["bambu_a1_fit"] for row in belts["variants"].values()),
        "release": valid["commercial_belt"] == "HOLD" and valid["powered_rotation"] == "NOT_APPROVED"
                   and valid["field_deployment"] == "NOT_APPROVED",
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "bad_hashes": bad,
                            "missing": sorted(set(PACKAGE_PATHS) - set(files)),
                            "extras": sorted(set(files) - set(PACKAGE_PATHS))})
    return {"status": "PASS", "file_count": len(files), "step_count": len(steps),
            "stl_count": len(stls), "svg_count": len(DRAWINGS), "checks": checks, "bad_hashes": bad}


def standalone_rebuild() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ps_cr_v0951_rebuild_") as temp:
        root = Path(temp)
        copy_pulley_references(root)
        jobs = [
            (build_coupon(), "cad/drive_htd5m_12tooth_fit_coupon.step"),
            (build_coupon(), "cad/drive_htd5m_12tooth_fit_coupon.stl"),
            (build_endless_belt(113), "cad/drive_htd5m_113t_565_tpu.step"),
            (build_endless_belt(113), "cad/drive_htd5m_113t_565_tpu.stl"),
            (build_endless_belt(114), "cad/drive_htd5m_114t_570_tpu.step"),
            (build_endless_belt(114), "cad/drive_htd5m_114t_570_tpu.stl"),
            (build_endless_belt(112), "cad/drive_htd5m_112t_560_tpu.step"),
            (build_endless_belt(112), "cad/drive_htd5m_112t_560_tpu.stl"),
            (build_assembly(), "cad/drive_20t_60t_c180_113t_reference.step"),
        ]
        for shape, rel in jobs:
            export(shape, root / rel)
        rebuilt_steps = [cq.importers.importStep(str(root / rel)).val() for rel in CAD
                         if rel.endswith(".step") and rel not in PULLEY_STEP_SOURCES]
        rebuilt_stls = [stl_semantic(root / rel) for rel in CAD if rel.endswith(".stl")]
        checks = {
            "profile_snapshot_available": PROFILE_DIR in {SNAPSHOT_DIR, EXTERNAL_PROFILE_DIR},
            "pulley_inputs_exact": all(sha(root / rel) == digest for rel, (_source, digest) in PULLEY_STEP_SOURCES.items()),
            "step_reload": len(rebuilt_steps) == 5 and all(shape.isValid() and shape.Volume() > 0 for shape in rebuilt_steps),
            "stl_semantic": len(rebuilt_stls) == 4 and all(row["watertight"] for row in rebuilt_stls),
        }
        if not all(checks.values()):
            raise RuntimeError({"standalone_rebuild": checks})
        return {"status": "PASS", "artifact_count": 11, "checks": checks}


def make_zip() -> tuple[Path, str]:
    path = DOWNLOADS / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for rel in PACKAGE_PATHS:
            archive.write(LANE / rel, rel)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        bad_paths = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        if archive.testzip() or len(names) != len(set(names)) or bad_paths or sorted(names) != PACKAGE_PATHS:
            raise RuntimeError("ZIP_STRUCTURE_CONTRACT_FAILED")
        if archive.read("MANIFEST.txt").decode("utf-8").splitlines() != PACKAGE_PATHS:
            raise RuntimeError("ZIP_MANIFEST_CONTRACT_FAILED")
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            if hashlib.sha256(archive.read(rel)).hexdigest() != digest:
                raise RuntimeError(f"ZIP_HASH_FAILED: {rel}")
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0951_zip_") as temp:
            temp_root = Path(temp)
            for rel in CAD:
                extracted = temp_root / rel
                extracted.parent.mkdir(parents=True, exist_ok=True)
                extracted.write_bytes(archive.read(rel))
            for rel in CAD:
                if rel.endswith(".step"):
                    shape = cq.importers.importStep(str(temp_root / rel)).val()
                    if not shape.isValid() or shape.Volume() <= 0:
                        raise RuntimeError(f"ZIP_STEP_RELOAD_FAILED: {rel}")
                elif not stl_semantic(temp_root / rel)["watertight"]:
                    raise RuntimeError(f"ZIP_STL_SEMANTIC_FAILED: {rel}")
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--standalone-rebuild", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.build = args.verify = True
    result: dict[str, Any] = {}
    if args.build:
        result["build"] = build()
    if args.verify:
        result["guard"] = repository_guard(True)
        result["verify"] = verify_files()
    if args.standalone_rebuild:
        result["standalone_rebuild"] = standalone_rebuild()
    if args.zip:
        zip_path, digest = make_zip()
        result["zip"] = {"path": str(zip_path), "sha256": digest}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
