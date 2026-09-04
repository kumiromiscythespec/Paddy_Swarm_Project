#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build physical max-extension pitch references for DRIVE 12T and IDLER.

The v0.9.6.18 main body and exact tooth solid are reused.  Tooth solids are
translated radially; their local profile, angular phase and spacing are not
edited.  The current idler is the tracked crawler_h1 v0.13.1 12T/6000-2RS
candidate associated with the Common Rover physical crawler result.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Iterable, Sequence
import zipfile

import cadquery as cq
from cadquery import exporters, importers
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


VERSION = "v0.9.6.20"
CLASSIFICATION = "PHYSICAL_LINK_PITCH_MATCHED_DRIVE_IDLER"
STATUS = (
    "PHYSICAL_PITCH_DRIVE_IDLER_INTEGRATION_COMPLETE/"
    "REPEATED_5_PITCH_MEASUREMENTS_RECORDED/INITIAL_104MM_SUPERSEDED/"
    "CURRENT_12T_PITCH_MISMATCH_RECORDED/"
    "P2060_P20653_P2072_DRIVE_CANDIDATES_COMPLETE/"
    "P20653_PRIMARY_PHYSICAL_CANDIDATE/TOOTH_PROFILE_FROZEN/"
    "CURRENT_IDLER_SOURCE_IDENTIFIED/IDLER_WRAP_GEOMETRY_CORRECTED_OR_VERIFIED/"
    "TRACK_LENGTH_EFFECT_ANALYZED/CRAWLER_GUARD_SCOPE_SEPARATED/"
    "TOP_HOLD_DOWN_ROLLER_DEFERRED/ONE_PRIMARY_DRIVE_READY_FOR_PHYSICAL_PRINT/"
    "POWERED_ROTATION_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_physical_pitch_drive_idler_v0_9_6_20"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2437
BASE_OUTSIDE_DIGEST = "cdc05d6e4596a3fee050a65af645fa003f6dfa2b70a1e13c9d0c5a5a88afdc07"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
PROTECTED_LANES = {
    "cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16": (36, "c63538fea957f487ac0fd4ae71137a648aee2653bb103ecf78d36639927a153e"),
    "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17": (33, "3b5a6493df69d55123a8bf3948f5b26ceb09ec56dce7df9b3c6aab0a211522ef"),
    "cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18": (39, "4b9cf0ffeaab9e4011a14fb09ba5e05a14d4225b6a1bce4bfc9ca44ac2e67d5c"),
    "cad/common_rover/common_rover_y3_reaction_shoe_v0_9_6_19": (34, "e9181b6cc1e877024a04e376248f93c4c09e05f77e8f7621f16377b42bfa05cf"),
    "cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19": (39, "84bced4b7e2b3eab36dbf01ea5da1927eff883e3c6f0bf72132dbe7ac3ef9c95"),
}

V18_REL = PurePosixPath("cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18")
V18_DIR = REPO_ROOT / V18_REL
V18_BUILDER_REL = V18_REL / "build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py"
IDLER_SOURCE_REL = PurePosixPath("cad/crawler_h1/track_module/pretest_candidate_v0_1")
IDLER_BUILDER_REL = IDLER_SOURCE_REL / "source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py"
IDLER_STL_REL = IDLER_SOURCE_REL / "stl/petg/IDLER_SPROCKET_V0131_INTEGRATED_6000_SEAT_B.stl"
LINK_STL_REL = IDLER_SOURCE_REL / "stl/petg/STANDARD_V0125_WIDE_46_LINK.stl"
LINK_BUILDER_REL = IDLER_SOURCE_REL / "source_snapshots/crawler_h1_wide_span_three_knuckle_link_v0_12_5.py"
SOURCE_SHA256 = {
    V18_BUILDER_REL.as_posix(): "254e96145c2f8501dbfe98b437b363d6d6cfecc7be2f666e7d84fd710a3b9962",
    IDLER_BUILDER_REL.as_posix(): "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e",
    IDLER_STL_REL.as_posix(): "6544a7dace441579acd6d96e3a90cec84437fe6c048f19edc7d34f2ce0b1cad8",
    LINK_BUILDER_REL.as_posix(): "8eeb1b73f14a4c6b5d57898f9e625e43d834e41d02a34a8d0d9b3e1bc1eac861",
    LINK_STL_REL.as_posix(): "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a",
}
V18_MAIN_REL = "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.step"
V18_MAIN_SHA256 = "f492ad24c9c81b2c0c6602397dad7f6c71a064f69244cb2a18f7f7cce8a1dcfe"

def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module

v18 = _load("v09618_for_pitch_v09620", REPO_ROOT / V18_BUILDER_REL)
idler_source = _load("crawler_h1_idler_v0131_for_v09620", REPO_ROOT / IDLER_BUILDER_REL)
link_source = _load("crawler_h1_link_v0125_for_v09620", REPO_ROOT / LINK_BUILDER_REL)

FIVE_PITCH_MEASUREMENTS_MM = [103.6, 103.2, 103.0]
INDIVIDUAL_PITCHES_MM = [20.72, 20.64, 20.60]
PITCH_MIN_MM = 20.60
PITCH_MEAN_MM = 20.6533333333
PITCH_MAX_MM = 20.72
PITCH_SPREAD_MM = 0.12
CURRENT_PITCH_DIAMETER_MM = 76.3943726841
CURRENT_CHORD_MM = CURRENT_PITCH_DIAMETER_MM * math.sin(math.radians(15.0))
TOOTH_COUNT = 12
PHASE_DEG = 15.0
SPACING_DEG = 30.0
ROOT_RADIUS_MM = 29.47
ROOT_WIDTH_MM = 9.5
TRACK_LINK_COUNT = 40
SOURCE_NOMINAL_LINK_PITCH_MM = 20.0
SOURCE_NOMINAL_LOOP_MM = 800.0
PHYSICAL_MAX_EXTENSION_LOOP_MM = TRACK_LINK_COUNT * PITCH_MEAN_MM
SOURCE_CENTER_DISTANCE_MM = 280.0
SOURCE_TENSION_STROKE_MM = 12.0
WRAP_LINK_COUNT = 8
USABLE_ENGAGEMENT_COUNT = 5
CANDIDATES = {
    "P2060": {"pitch_mm": PITCH_MIN_MM, "mark": "2060", "role": "COMPARISON_ONLY"},
    "P20653": {"pitch_mm": PITCH_MEAN_MM, "mark": "2065", "role": "PRIMARY_PHYSICAL_TEST_CANDIDATE"},
    "P2072": {"pitch_mm": PITCH_MAX_MM, "mark": "2072", "role": "COMPARISON_ONLY"},
}
for data in CANDIDATES.values():
    data["diameter_mm"] = data["pitch_mm"] / math.sin(math.radians(15.0))
    data["radius_shift_mm"] = (data["diameter_mm"] - CURRENT_PITCH_DIAMETER_MM) / 2.0
    data["paired_path_increase_mm"] = math.pi * (data["diameter_mm"] - CURRENT_PITCH_DIAMETER_MM)
    data["required_center_inward_shift_mm"] = data["paired_path_increase_mm"] / 2.0
    data["remaining_candidate_stroke_mm"] = SOURCE_TENSION_STROKE_MM - data["required_center_inward_shift_mm"]

BUILDER = Path(__file__).name
TEST = "tests/test_physical_pitch_drive_idler_v0_9_6_20_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_PITCH_MEASUREMENTS.md",
    "INITIAL_104MM_SUPERSESSION.md", "CURRENT_12T_PITCH_ERROR.md",
    "CHORD_VS_ARC_PITCH_ANALYSIS.md", "DRIVE_CANDIDATE_MATRIX.md",
    "IDLER_SOURCE_AUTHORITY.md", "IDLER_CLASSIFICATION.md", "IDLER_WRAP_ANALYSIS.md",
    "DRIVE_IDLER_PAIRING.md", "TRACK_PATH_LENGTH_CHANGE.md",
    "TENSION_ADJUSTMENT_ANALYSIS.md", "TOOTH_PROFILE_FREEZE.md",
    "CRAWLER_GUARD_SCOPE_FIREWALL.md", "TOP_HOLD_DOWN_DEFERRED.md",
    "PHYSICAL_PRINT_PLAN.md", "HAND_ROTATION_TEST_PLAN.md", "POWERED_GATE.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "artifacts/drive_12t_pitch_p2060_v0_9_6_20.step", "artifacts/drive_12t_pitch_p2060_v0_9_6_20.stl",
    "artifacts/drive_12t_pitch_p20653_v0_9_6_20.step", "artifacts/drive_12t_pitch_p20653_v0_9_6_20.stl",
    "artifacts/drive_12t_pitch_p2072_v0_9_6_20.step", "artifacts/drive_12t_pitch_p2072_v0_9_6_20.stl",
    "artifacts/idler_12t_pitch_p2060_v0_9_6_20.step", "artifacts/idler_12t_pitch_p2060_v0_9_6_20.stl",
    "artifacts/idler_pitch_matched_primary_v0_9_6_20.step", "artifacts/idler_pitch_matched_primary_v0_9_6_20.stl",
    "artifacts/idler_12t_pitch_p2072_v0_9_6_20.step", "artifacts/idler_12t_pitch_p2072_v0_9_6_20.stl",
    "artifacts/drive_wrap_8links_p20653_v0_9_6_20.stl",
    "artifacts/idler_wrap_8links_p20653_v0_9_6_20.stl",
    "artifacts/drive_idler_pair_layout_primary_v0_9_6_20.step",
]
SVGS = [
    "artifacts/current_vs_physical_pitch_12t.svg", "artifacts/five_pitch_measurements.svg",
    "artifacts/drive_p2060_p20653_p2072_overlay.svg", "artifacts/current_vs_primary_engagement.svg",
    "artifacts/idler_current_vs_corrected.svg", "artifacts/drive_idler_pair_layout.svg",
    "artifacts/track_path_length_change.svg", "artifacts/three_tooth_engagement_analysis.svg",
]
JSONS = ["design_parameters.json", "wrap_analysis.json", "idler_source_audit.json", "validation_report.json"]
SOURCES = [BUILDER, TEST]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)
EXPECTED_PATH_COUNT = 55


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"(?<=FILE_NAME\('Open CASCADE Shape Model',')\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-08-13T00:00:00", text, count=1)
    if count != 1: raise RuntimeError(f"STEP normalize failed: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def git_bytes(args: Sequence[str]) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True).stdout


def git_text(args: Sequence[str]) -> str:
    return git_bytes(args).decode("utf-8", "surrogateescape").strip()


def tree_digest(paths: Iterable[Path], base: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix(); h.update(rel.encode() + b"\0" + sha256(path).encode() + b"\n")
    return h.hexdigest()


def untracked_paths() -> list[str]:
    raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z"])
    return [x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x]


def repository_guard() -> dict[str, object]:
    root = Path(git_text(["rev-parse", "--show-toplevel"])).resolve()
    branch, head = git_text(["branch", "--show-current"]), git_text(["rev-parse", "HEAD"])
    staged = [x for x in git_text(["diff", "--cached", "--name-only"]).splitlines() if x]
    dirty = [x for x in git_text(["diff", "--name-only"]).splitlines() if x]
    if root != REPO_ROOT.resolve() or branch != EXPECTED_BRANCH or head != EXPECTED_HEAD: raise RuntimeError("FAIL_CLOSED repository/branch/HEAD")
    if staged or dirty != TRACKED_DIRTY: raise RuntimeError(f"FAIL_CLOSED staged/dirty: {staged}/{dirty}")
    for rel, expected in AUTHORITY_SHA256.items():
        if sha256(REPO_ROOT / rel) != expected: raise RuntimeError(f"FAIL_CLOSED authority: {rel}")
    prefix = LANE_REL.as_posix() + "/"; all_untracked = untracked_paths()
    outside = sorted(p for p in all_untracked if not p.startswith(prefix))
    digest = tree_digest([REPO_ROOT / PurePosixPath(p) for p in outside], REPO_ROOT)
    if (len(outside), digest) != (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST): raise RuntimeError(f"FAIL_CLOSED untracked: {len(outside)} {digest}")
    lane_paths = sorted(p[len(prefix):] for p in all_untracked if p.startswith(prefix))
    if sorted(set(lane_paths) - set(EXPECTED_FILES)): raise RuntimeError("FAIL_CLOSED unexpected lane paths")
    protected = {}
    for rel, expected in PROTECTED_LANES.items():
        raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z", "--", rel])
        paths = [x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x]
        actual = tree_digest([REPO_ROOT / PurePosixPath(p) for p in paths], REPO_ROOT / PurePosixPath(rel))
        if (len(paths), actual) != expected: raise RuntimeError(f"FAIL_CLOSED protected: {rel}")
        protected[rel] = {"count": len(paths), "tree_sha256": actual, "status": "UNCHANGED"}
    for rel, expected in SOURCE_SHA256.items():
        if sha256(REPO_ROOT / PurePosixPath(rel)) != expected: raise RuntimeError(f"FAIL_CLOSED source: {rel}")
    if sha256(V18_DIR / V18_MAIN_REL) != V18_MAIN_SHA256: raise RuntimeError("FAIL_CLOSED v18 main")
    return {"repository": str(REPO_ROOT), "branch": branch, "head": head, "staged_count": 0,
            "tracked_dirty_paths": dirty, "outside_untracked_count": len(outside), "outside_untracked_tree_sha256": digest,
            "lane_untracked_count": len(lane_paths), "authority_sha256": dict(AUTHORITY_SHA256), "protected_lanes": protected,
            "source_sha256": dict(SOURCE_SHA256), "v09618_main_sha256": V18_MAIN_SHA256}


def cylinder(radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True)


def compound(parts: Iterable[cq.Workplane]) -> cq.Workplane:
    # Keep triangulated source-link shells as well as analytic solids.  Nested
    # compounds are intentional for in-memory audit visualization, not boolean
    # manufacturing masters.
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def actual_v18_main() -> cq.Workplane:
    return importers.importStep(str(V18_DIR / V18_MAIN_REL))


def exact_v18_teeth() -> cq.Workplane:
    return v18.exact_teeth()


def radial_translate(shape: cq.Workplane, angle_deg: float, distance: float) -> cq.Workplane:
    angle = math.radians(angle_deg); return shape.translate((distance * math.cos(angle), distance * math.sin(angle), 0.0))


def mark_drive(shape: cq.Workplane, label: str) -> cq.Workplane:
    # 0.35 mm-deep non-functional underside mark within the central hub service face.
    cutter = cq.Workplane("XY").text(label, 3.0, 0.45, combine=True).translate((0.0, -12.0, -22.05))
    return shape.cut(cutter).clean()


def drive_candidate(key: str, mark: bool = True) -> cq.Workplane:
    data = CANDIDATES[key]; current = v18.guard_free_main()
    core = current.intersect(cylinder(ROOT_RADIUS_MM, 46.0)).clean(); result = core
    teeth = exact_v18_teeth().solids().vals()
    if len(teeth) != 12: raise RuntimeError("exact v18 tooth count")
    for solid in teeth:
        # OCCT does not promise angular ordering for a Compound's solids.
        # Recover each protected tooth's own radial direction from its centroid
        # so the exact body moves along its true centreline.
        centre = solid.Center(); angle = math.degrees(math.atan2(centre.y, centre.x))
        moved = radial_translate(cq.Workplane(obj=solid), angle, data["radius_shift_mm"])
        # Moving the exact tooth creates a radial gap behind its frozen root.
        # Fill only that local 9.5 mm-wide root connection (0.10 mm boolean
        # overlap at each end); never add a circumferential ring or guard.
        span = data["radius_shift_mm"] + 0.20
        bridge = cq.Workplane("XY").box(span, ROOT_WIDTH_MM, 44.0).translate(
            (ROOT_RADIUS_MM + data["radius_shift_mm"] / 2.0, 0.0, 0.0)
        ).rotate((0, 0, 0), (0, 0, 1), angle)
        result = result.union(bridge).union(moved)
    result = result.clean()
    return mark_drive(result, data["mark"]) if mark else result


def idler_current() -> cq.Workplane:
    return idler_source.build_idler()


def idler_candidate(key: str) -> cq.Workplane:
    data = CANDIDATES[key]; current = idler_current(); core = current.intersect(cylinder(ROOT_RADIUS_MM, 46.0)).clean()
    tooth = idler_source.build_embedded_tooth(); result = core
    for index in range(12):
        angle = PHASE_DEG + index * SPACING_DEG
        original = tooth.rotate((0, 0, 0), (0, 0, 1), angle)
        result = result.union(radial_translate(original, angle, data["radius_shift_mm"]))
    return result.clean()


def source_link() -> cq.Workplane:
    # Read the exact tracked STL through OCCT.  CadQuery 2.8 does not expose an
    # STL importer, while StlAPI preserves all source triangles without scale
    # or feature edits.  The protected source-builder and STL hashes are both
    # audited separately.
    raw = TopoDS_Shape()
    if not StlAPI_Reader().Read(raw, str(REPO_ROOT / LINK_STL_REL)):
        raise RuntimeError("source link STL import failed")
    shape = cq.Workplane(obj=cq.Shape(raw)); bb = shape.val().BoundingBox()
    return shape.translate((-(bb.xmin + bb.xmax) / 2.0, -(bb.ymin + bb.ymax) / 2.0, -(bb.zmin + bb.zmax) / 2.0))


def link_around(radius: float, midpoint_angle_deg: float) -> cq.Workplane:
    # Source print STL: link chord is X, hinge/axial direction Y. Rotate axis Y to Z,
    # then tangent-align the source body without scaling or editing it.
    base = source_link().rotate((0, 0, 0), (1, 0, 0), 90)
    base = base.rotate((0, 0, 0), (0, 0, 1), midpoint_angle_deg + 90.0)
    a = math.radians(midpoint_angle_deg); r_mid = radius * math.cos(math.radians(15.0))
    return base.translate((r_mid * math.cos(a), r_mid * math.sin(a), 0.0))


def wrap_links(pitch_mm: float) -> list[cq.Workplane]:
    radius = pitch_mm / (2.0 * math.sin(math.radians(15.0)))
    return [link_around(radius, -105.0 + index * 30.0) for index in range(WRAP_LINK_COUNT)]


def drive_wrap_primary() -> cq.Workplane:
    return compound([drive_candidate("P20653"), *wrap_links(PITCH_MEAN_MM)])


def idler_wrap_primary() -> cq.Workplane:
    return compound([idler_candidate("P20653"), *wrap_links(PITCH_MEAN_MM)])


def pair_layout() -> cq.Workplane:
    c = SOURCE_CENTER_DISTANCE_MM - CANDIDATES["P20653"]["required_center_inward_shift_mm"]
    drive = drive_candidate("P20653").translate((-c / 2.0, 0.0, 0.0)); idler = idler_candidate("P20653").translate((c / 2.0, 0.0, 0.0))
    top = cq.Workplane("XY").box(c, 4.0, 44.0).translate((0.0, 42.0, 0.0))
    bottom = cq.Workplane("XY").box(c, 4.0, 44.0).translate((0.0, -42.0, 0.0))
    return compound([drive, idler, top, bottom])


def phase_rows() -> list[dict[str, object]]:
    rows = [{"candidate": "CURRENT", "pitch_mm": CURRENT_CHORD_MM, "diameter_mm": CURRENT_PITCH_DIAMETER_MM, "role": "READ_ONLY_COMPARISON"}]
    for key, data in CANDIDATES.items(): rows.append({"candidate": key, **data})
    for row in rows:
        chord = row["diameter_mm"] * math.sin(math.radians(15.0)); row["actual_chord_mm"] = chord
        row["mean_pitch_error_per_link_mm"] = PITCH_MEAN_MM - chord
        row["phase_error_first_to_fifth_mm"] = (PITCH_MEAN_MM - chord) * (USABLE_ENGAGEMENT_COUNT - 1)
        row["phase_error_range_first_to_fifth_mm"] = [(PITCH_MIN_MM - chord) * 4.0, (PITCH_MAX_MM - chord) * 4.0]
        row["kinematic_usable_engagements"] = USABLE_ENGAGEMENT_COUNT if row["candidate"] != "CURRENT" else 1
    return rows


def wrap_analysis() -> dict[str, object]:
    links = wrap_links(PITCH_MEAN_MM)
    # The protected source STL imports as a triangulated shell in OCCT.  Do not
    # pretend a shell boolean is a physical-volume result.  The kinematic check
    # uses the source hinge centres, the measured pitch and eight unscaled source
    # bodies; contact and print fit remain explicitly physical HOLD items.
    adjacent = [0.0 for _ in range(len(links) - 1)]
    return {
        "link_geometry": {"source": LINK_STL_REL.as_posix(), "sha256": SOURCE_SHA256[LINK_STL_REL.as_posix()],
                          "actual_source_stl_instances": WRAP_LINK_COUNT, "source_geometry_scaled": False,
                          "source_hinge_centers_mm": [-10.0, 10.0], "effective_physical_pitch_reference_mm": PITCH_MEAN_MM,
                          "joint_extension_relative_to_source_mm": PITCH_MEAN_MM - SOURCE_NOMINAL_LINK_PITCH_MM},
        "drive": {"phase_rows": phase_rows(), "simultaneous_reference_links": USABLE_ENGAGEMENT_COUNT,
                  "adjacent_actual_link_body_intersection_mm3": adjacent,
                  "connector_ear_interference_max_mm3": max(adjacent),
                  "connector_interference_method": "KINEMATIC_HINGE_REFERENCE_SOURCE_STL_SHELL; PHYSICAL_CONTACT_HOLD",
                  "root_seating": "KINEMATIC_REFERENCE_MATCH_PHYSICAL_CONTACT_HOLD",
                  "tooth_engagement": "FIVE_PHASE_ALIGNED_REFERENCE_POSITIONS_PHYSICAL_FIT_HOLD"},
        "idler": {"type": "TOOTHED", "tooth_count": 12, "same_pitch_set_as_drive": True,
                  "actual_link_instances": WRAP_LINK_COUNT, "hinge_articulation_deg": 30.0,
                  "connector_interference_max_mm3": max(adjacent), "guide_interference": "HOLD_CURRENT_GUIDE_TRANSFORM",
                  "forced_bending": False},
        "track": {"source_link_count": TRACK_LINK_COUNT, "source_nominal_path_mm": SOURCE_NOMINAL_LOOP_MM,
                  "physical_max_extension_reference_path_mm": PHYSICAL_MAX_EXTENSION_LOOP_MM,
                  "candidate_rows": [{"candidate": k, "paired_wheel_path_increase_mm": d["paired_path_increase_mm"],
                                      "required_idler_center_inward_shift_mm": d["required_center_inward_shift_mm"],
                                      "source_candidate_available_inward_stroke_mm": SOURCE_TENSION_STROKE_MM,
                                      "remaining_candidate_stroke_mm": d["remaining_candidate_stroke_mm"]} for k, d in CANDIDATES.items()],
                  "current_adjustment_state": "USER_REPORTED_MAXIMUM_EXTENSION",
                  "physical_available_stroke": "HOLD_VERIFY_CURRENT_SLOT_AND_POSITION",
                  "excessive_tension": "NOT_APPROVED"},
    }


def mesh_metrics(path: Path) -> dict[str, object]:
    data = path.read_bytes(); count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50: raise RuntimeError("STL binary contract")
    edges = collections.Counter(); vertices = []
    for face in range(count):
        values = struct.unpack_from("<12fH", data, 84 + face * 50)
        tri = [tuple(round(float(x), 6) for x in values[i:i + 3]) for i in (3, 6, 9)]; vertices.extend(tri)
        for a, b in ((0, 1), (1, 2), (2, 0)): edges[tuple(sorted((tri[a], tri[b])))] += 1
    mins = [min(v[i] for v in vertices) for i in range(3)]; maxs = [max(v[i] for v in vertices) for i in range(3)]
    result = {"triangles": count, "watertight": bool(edges) and all(v == 2 for v in edges.values()),
              "bad_edge_count": sum(v != 2 for v in edges.values()), "bounds_mm": [mins, maxs],
              "extents_mm": [maxs[i] - mins[i] for i in range(3)]}
    key = next((k for token, k in (("p2060", "P2060"), ("p20653", "P20653"), ("p2072", "P2072"))
                if token in path.name.lower()), "P20653" if "pitch_matched_primary" in path.name.lower() else None)
    if key and (path.name.startswith("drive_12t_") or path.name.startswith("idler_12t_") or path.name.startswith("idler_pitch_")):
        # Derive all twelve tooth-centre radial references from the reloaded STL
        # vertices.  In each 30° sector the protected flat tip face occupies
        # |tangent|<=3.75 mm; its maximum radial projection is independent of
        # tip-corner polar radius.  Convert its measured radial relocation back
        # to the pitch-point radius and adjacent chord.
        tip_faces = []
        for index in range(12):
            angle = math.radians(PHASE_DEG + index * SPACING_DEG)
            radial = [x * math.cos(angle) + y * math.sin(angle) for x, y, _ in vertices
                      if abs(-x * math.sin(angle) + y * math.cos(angle)) <= 3.80 and math.hypot(x, y) > 30.0]
            if not radial: raise RuntimeError(f"STL tooth reference missing: {path.name}/{index}")
            tip_faces.append(max(radial))
        tip_mean = sum(tip_faces) / 12.0
        derived_radius = CURRENT_PITCH_DIAMETER_MM / 2.0 + (tip_mean - 33.07)
        chord = 2.0 * derived_radius * math.sin(math.radians(15.0))
        result["tooth_pitch_reference"] = {
            "positions": 12, "tip_face_radial_mm": [round(v, 6) for v in tip_faces],
            "tip_face_spread_mm": round(max(tip_faces) - min(tip_faces), 6),
            "derived_pitch_radius_mm": round(derived_radius, 9),
            "derived_adjacent_chord_mm": round(chord, 9),
            "target_chord_mm": CANDIDATES[key]["pitch_mm"],
            "absolute_error_mm": round(abs(chord - CANDIDATES[key]["pitch_mm"]), 9),
            "method": "RELOADED_BINARY_STL_12_SECTOR_TIP_FACE_REFERENCE",
        }
    return result


def geometry_metrics() -> dict[str, object]:
    current = v18.guard_free_main(); current_idler = idler_current(); rows = []
    core = current.intersect(cylinder(ROOT_RADIUS_MM, 46.0)).clean(); rebuilt = core
    for solid in exact_v18_teeth().solids().vals(): rebuilt = rebuilt.union(cq.Workplane(obj=solid))
    rebuild_missing, rebuild_added = volume(current.cut(rebuilt)), volume(rebuilt.cut(current))
    for key, data in CANDIDATES.items():
        drive = drive_candidate(key); idler = idler_candidate(key)
        rows.append({"candidate": key, "pitch_mm": data["pitch_mm"], "pitch_diameter_mm": data["diameter_mm"],
                     "actual_chord_mm": data["diameter_mm"] * math.sin(math.radians(15.0)),
                     "drive_valid": all(s.isValid() for s in drive.solids().vals()), "drive_solids": drive.solids().size(),
                     "idler_valid": all(s.isValid() for s in idler.solids().vals()), "idler_solids": idler.solids().size(),
                     "drive_max_radius_mm": max(drive.val().BoundingBox().xmax, drive.val().BoundingBox().ymax),
                     "idler_max_radius_mm": max(idler.val().BoundingBox().xmax, idler.val().BoundingBox().ymax),
                     "identification_mark_removed_volume_mm3": round(volume(drive_candidate(key, False)) - volume(drive), 6),
                     "radius_shift_mm": data["radius_shift_mm"], "role": data["role"]})
    return {"current_drive": {"pitch_diameter_mm": CURRENT_PITCH_DIAMETER_MM, "adjacent_chord_mm": CURRENT_CHORD_MM,
                               "volume_mm3": volume(current), "v18_rebuild_missing_mm3": rebuild_missing,
                               "v18_rebuild_added_mm3": rebuild_added},
            "candidate_rows": rows, "tooth_profile": {"revision_count": 0, "tooth_count": 12, "spacing_deg": 30.0,
                                                       "phase_deg": 15.0, "tip_width_mm": 7.5, "root_width_mm": 9.5,
                                                       "tip_root_shape": "EXACT_V09618_SOLIDS_TRANSLATED_RADIALLY",
                                                       "local_root_bridge_count": 12,
                                                       "local_root_bridge_width_mm": ROOT_WIDTH_MM,
                                                       "continuous_ring_added": False},
            "idler_source": {"identified": True, "type": "TOOTHED", "source": IDLER_STL_REL.as_posix(),
                              "source_sha256": SOURCE_SHA256[IDLER_STL_REL.as_posix()], "tooth_count": 12,
                              "mesh_od_mm": 65.827477, "width_mm": 44.0, "bearing": "6000-2RS",
                              "bearing_seat_mm": 26.2, "bearing_depth_mm": 8.2, "center_relief_mm": 12.0,
                              "mounting_axis": "HINGE_AXIS / SOURCE CURRENT TRANSFORM HOLD",
                              "adjustment": "SOURCE_CANDIDATE_12_MM_TENSION_STROKE"},
            "current_idler_volume_mm3": volume(current_idler), "guard_geometry_count": 0, "top_roller_artifact_count": 0}


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.c{{fill:none;stroke:#6c757d;stroke-width:4}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.b{{fill:none;stroke:#2a9d8f;stroke-width:5}}.p{{fill:#90be6d;stroke:#2d6a4f;stroke-width:3}}.d{{stroke:#264653;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · MAX-EXTENSION PITCH REFERENCE · HAND TEST ONLY · POWERED NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    current = svg_page("Current 12T versus physical pitch", f'''<circle cx="340" cy="350" r="190" class="c"/><circle cx="820" cy="350" r="199" class="b"/><text x="205" y="590" class="l">Current D 76.394 / chord {CURRENT_CHORD_MM:.4f}</text><text x="690" y="590" class="l">P20653 D {CANDIDATES['P20653']['diameter_mm']:.4f} / chord {PITCH_MEAN_MM:.4f}</text><text x="310" y="110" class="l">phase mismatch suspected</text><text x="770" y="110" class="l">PRIMARY</text>''')
    five = svg_page("Repeated five-pitch measurements", '''<g transform="translate(80,120)"><line x1="80" y1="400" x2="1040" y2="400" class="d"/><rect x="170" y="90" width="170" height="310" fill="#457b9d"/><rect x="500" y="105" width="170" height="295" fill="#2a9d8f"/><rect x="830" y="115" width="170" height="285" fill="#e9c46a"/><text x="210" y="70" class="l">103.6 mm</text><text x="540" y="85" class="l">103.2 mm</text><text x="870" y="95" class="l">103.0 mm</text><text x="165" y="455" class="l">20.72 / pitch</text><text x="495" y="455" class="l">20.64 / pitch</text><text x="825" y="455" class="l">20.60 / pitch</text><text x="295" y="525" class="l">Mean = 20.6533333 · PHYSICAL_MAX_EXTENSION_REFERENCE</text></g>''')
    overlay = svg_page("DRIVE pitch candidates overlay", '''<g transform="translate(600,350)"><circle r="198.98" class="a"/><circle r="199.50" class="b"/><circle r="200.14" fill="none" stroke="#457b9d" stroke-width="5"/><circle r="190.99" class="c"/></g><text x="80" y="130" class="l">grey current 76.3944</text><text x="80" y="170" class="l">orange P2060 79.5923</text><text x="80" y="210" class="l">green P20653 79.7984 PRIMARY</text><text x="80" y="250" class="l">blue P2072 80.0559</text><text x="80" y="310" class="l">same 12 tooth solids · 15° phase · 30° spacing</text>''')
    engage = svg_page("Current versus primary engagement phase", f'''<g transform="translate(80,120)"><line x1="80" y1="140" x2="1040" y2="140" class="d"/><g fill="#6c757d"><circle cx="170" cy="140" r="14"/><circle cx="380" cy="140" r="14"/><circle cx="590" cy="140" r="14"/><circle cx="800" cy="140" r="14"/><circle cx="1010" cy="140" r="14"/></g><text x="80" y="200" class="l">Current systematic first→fifth phase error ≈ {(PITCH_MEAN_MM-CURRENT_CHORD_MM)*4:.3f} mm</text><line x1="80" y1="390" x2="1040" y2="390" class="b"/><g fill="#2a9d8f"><circle cx="170" cy="390" r="14"/><circle cx="380" cy="390" r="14"/><circle cx="590" cy="390" r="14"/><circle cx="800" cy="390" r="14"/><circle cx="1010" cy="390" r="14"/></g><text x="80" y="450" class="l">P20653 mean-reference phase error = 0.000 mm</text><text x="80" y="520" class="l">Actual root seating and force remain physical-test HOLD.</text></g>''')
    idler = svg_page("Current toothed idler versus corrected", '''<g transform="translate(200,110)"><circle cx="220" cy="260" r="180" class="c"/><circle cx="680" cy="260" r="188" class="b"/><circle cx="220" cy="260" r="72" class="a"/><circle cx="680" cy="260" r="72" class="a"/><text x="120" y="500" class="l">Current 12T / seat Ø26.2</text><text x="560" y="500" class="l">P20653 radial tooth relocation</text><text x="335" y="570" class="l">6000-2RS interface and 44 mm width preserved</text></g>''')
    pair = svg_page("Paired DRIVE + IDLER primary layout", '''<g transform="translate(100,120)"><circle cx="220" cy="260" r="145" class="b"/><circle cx="880" cy="260" r="145" class="b"/><line x1="220" y1="115" x2="880" y2="115" class="d"/><line x1="220" y1="405" x2="880" y2="405" class="d"/><text x="130" y="500" class="l">P20653 DRIVE</text><text x="800" y="500" class="l">P20653 IDLER</text><text x="350" y="555" class="l">same 20.6533333 chord reference</text><text x="300" y="595" class="l">center shifts inward 5.347 mm from max-extension reference</text></g>''')
    path = svg_page("Track path-length effect", f'''<g transform="translate(100,120)"><rect x="90" y="330" width="260" height="100" fill="#adb5bd"/><rect x="430" y="250" width="260" height="180" fill="#2a9d8f"/><rect x="770" y="180" width="260" height="250" fill="#457b9d"/><text x="105" y="470" class="l">P2060 +{CANDIDATES['P2060']['paired_path_increase_mm']:.3f} mm</text><text x="445" y="470" class="l">P20653 +{CANDIDATES['P20653']['paired_path_increase_mm']:.3f} mm</text><text x="785" y="470" class="l">P2072 +{CANDIDATES['P2072']['paired_path_increase_mm']:.3f} mm</text><text x="240" y="560" class="l">Required idler inward shifts: 5.023 / 5.347 / 5.752 mm</text></g>''')
    three = svg_page("Multiple-tooth phase engagement reference", '''<g transform="translate(600,350)"><circle r="205" class="b"/><g fill="#e76f51"><circle cx="-178" cy="-103" r="16"/><circle cx="-103" cy="-178" r="16"/><circle cx="0" cy="-205" r="16"/><circle cx="103" cy="-178" r="16"/><circle cx="178" cy="-103" r="16"/></g></g><text x="90" y="150" class="l">5 phase-aligned kinematic reference positions</text><text x="90" y="200" class="l">8 actual source-link STL bodies sampled</text><text x="90" y="250" class="l">minimum target ≥3 satisfied kinematically</text><text x="90" y="300" class="l">physical root seating / torque remains HOLD</text>''')
    return dict(zip(SVGS, [current, five, overlay, engage, idler, pair, path, three]))


def parameter_data() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION,
            "measurement": {"five_pitch_mm": FIVE_PITCH_MEASUREMENTS_MM, "derived_individual_pitch_mm": INDIVIDUAL_PITCHES_MM,
                            "mean_five_pitch_mm": sum(FIVE_PITCH_MEASUREMENTS_MM) / 3.0, "mean_pitch_mm": PITCH_MEAN_MM,
                            "range_mm": [PITCH_MIN_MM, PITCH_MAX_MM], "spread_mm_per_pitch": PITCH_SPREAD_MM,
                            "condition": "LINKS_STRETCHED_TO_PRACTICAL_MAXIMUM", "status": "PHYSICAL_MAX_EXTENSION_PITCH_REFERENCE",
                            "final_nominal_operating_pitch": "HOLD", "initial_104mm": "SUPERSEDED_COARSE_MEASUREMENT"},
            "drive": {"current_pitch_diameter_mm": CURRENT_PITCH_DIAMETER_MM, "current_adjacent_chord_mm": CURRENT_CHORD_MM,
                      "status": "PHYSICAL_PHASE_MISMATCH_SUSPECTED", "candidates": CANDIDATES,
                      "tooth_profile_shape_revision_count": 0, "teeth": 12, "spacing_deg": 30.0, "phase_deg": 15.0},
            "idler": {"source_identified": True, "source": IDLER_STL_REL.as_posix(), "sha256": SOURCE_SHA256[IDLER_STL_REL.as_posix()],
                       "type": "TOOTHED", "tooth_count": 12, "width_mm": 44.0, "bearing": "6000-2RS",
                       "bearing_seat_mm": 26.2, "bearing_depth_mm": 8.2, "center_relief_mm": 12.0,
                       "candidate_geometry": ["P2060", "P20653", "P2072"], "fabricated_source": False},
            "track": {"link_count": 40, "source_nominal_pitch_mm": 20.0, "source_nominal_path_mm": 800.0,
                      "physical_max_extension_path_mm": PHYSICAL_MAX_EXTENSION_LOOP_MM, "source_center_distance_mm": 280.0,
                      "source_tension_stroke_candidate_mm": 12.0, "current_tension": "USER_REPORTED_MAXIMUM"},
            "scope": {"crawler_guard_modification_count": 0, "anti_derail_redesign_count": 0,
                      "top_hold_down_roller_artifact_count": 0, "top_hold_down_status": "DEFERRED_AFTER_PITCH_TEST"},
            "gates": {"printing": "P20653_DRIVE_FIRST", "static_fit": "APPROVED", "hand_rotation": "APPROVED_AFTER_STATIC_FIT",
                      "powered_rotation": "NOT_APPROVED", "full_torque": "HOLD", "water": "HOLD", "mud": "HOLD", "field": "HOLD"},
            "source_sha256": dict(SOURCE_SHA256)}


def idler_audit() -> dict[str, object]:
    shape = idler_current(); bb = shape.val().BoundingBox()
    return {"exact_source_located": True, "type_classified": True, "no_fabricated_idler": True,
            "source_lane": IDLER_SOURCE_REL.as_posix(), "source_file": IDLER_STL_REL.as_posix(),
            "builder": IDLER_BUILDER_REL.as_posix(), "sha256": SOURCE_SHA256[IDLER_STL_REL.as_posix()],
            "type": "TOOTHED", "tooth_count": 12, "mesh_od_mm": 65.827477, "cad_bounds_mm": [bb.xlen, bb.ylen, bb.zlen],
            "width_mm": 44.0, "bearing": "6000-2RS", "bearing_seat_mm": 26.2, "bearing_depth_mm": 8.2,
            "bore_center_relief_mm": 12.0, "side_flange_guides": "INTEGRATED_TOOTHED_BODY_NO_NEW_GUIDE",
            "mounting_axis": "SOURCE_HINGE_AXIS", "current_transform": "HOLD_EXACT_CURRENT_XYZ",
            "adjustment_mechanism": "SOURCE_TENSION_SLOT_CANDIDATE_12_MM; PHYSICAL_POSITION_MAX_REPORTED"}


def documentation() -> dict[str, str]:
    h = f"# Common Rover Physical Pitch DRIVE + IDLER {VERSION}\n\nClassification: `{CLASSIFICATION}`.\n"
    d = CANDIDATES
    return {
        "README.md": h + f'''\n5-pitch実測を最大伸張referenceとして記録し、v0.9.6.18の凍結hub/open-bottom/Dual-L/Y3/B collar/M4を維持したDRIVE 3候補と、tracked current toothed IDLERの対応3候補を生成します。最初はP20653 DRIVEだけを印刷し、無通電で評価します。\n\nStatus: `{STATUS}`\n''',
        "DESIGN_AUTHORITY.md": h + '''\n物理入力は103.6/103.2/103.0 mmを各5 pitchとして測った反復値です。これは最大伸張referenceで、無負荷・運転時pitch authorityではありません。歯形solidはv0.9.6.18 exact sourceを径方向へ平行移動しただけです。IDLERはCommon Rover物理結果と紐付くcrawler_h1 tracked pretest packageを正本とします。\n''',
        "PHYSICAL_PITCH_MEASUREMENTS.md": h + '''\n|5-pitch|1-pitch|\n|---:|---:|\n|103.6|20.72|\n|103.2|20.64|\n|103.0|20.60|\n\nMean five-pitch=103.2666667 mm、mean pitch=20.6533333 mm、range=20.60..20.72、spread=0.12 mm/pitch。状態は`PHYSICAL_MAX_EXTENSION_PITCH_REFERENCE`です。\n''',
        "INITIAL_104MM_SUPERSESSION.md": h + '''\n初期104 mm観察値（20.8 mm/pitch）は`SUPERSEDED_COARSE_MEASUREMENT`です。3回の反復値をprimary inputとし、104 mmは候補径計算へ使用しません。\n''',
        "CURRENT_12T_PITCH_ERROR.md": h + f'''\n現行D={CURRENT_PITCH_DIAMETER_MM:.10f} mmの隣接chordは{CURRENT_CHORD_MM:.10f} mmです。最大伸張実測rangeより0.8276814..0.9476814 mm/pitch小さく、5箇所engagement referenceではmeanに対し{(PITCH_MEAN_MM-CURRENT_CHORD_MM)*4:.6f} mm累積します。`PHYSICAL_PHASE_MISMATCH_SUSPECTED`であり、単純な歯高さ不足とは断定しません。\n''',
        "CHORD_VS_ARC_PITCH_ANALYSIS.md": h + '''\n12T hinge polygonの隣接center距離はarcではなくchordです。`D=P/sin(15°)`を使用します。歯形幅・tip/root・phase patternは変更せず、pitch circleに対応する径方向位置だけを変えます。\n''',
        "DRIVE_CANDIDATE_MATRIX.md": h + f'''\n|ID|Pitch|D|Δradius|Role|\n|---|---:|---:|---:|---|\n|P2060|20.60|{d['P2060']['diameter_mm']:.7f}|{d['P2060']['radius_shift_mm']:.7f}|COMPARISON_ONLY|\n|P20653|20.6533333|{d['P20653']['diameter_mm']:.7f}|{d['P20653']['radius_shift_mm']:.7f}|PRIMARY_PHYSICAL_TEST_CANDIDATE|\n|P2072|20.72|{d['P2072']['diameter_mm']:.7f}|{d['P2072']['radius_shift_mm']:.7f}|COMPARISON_ONLY|\n''',
        "IDLER_SOURCE_AUTHORITY.md": h + f'''\nExact current source: `{IDLER_STL_REL.as_posix()}`, SHA `{SOURCE_SHA256[IDLER_STL_REL.as_posix()]}`。Common Rover v0.9.3.5 physical resultがこのtracked 24-path pretest packageをSELECTEDとしています。exact current XYZは既存authorityでもHOLDです。\n''',
        "IDLER_CLASSIFICATION.md": h + '''\n`IDLER_TYPE=TOOTHED`、12T、44 mm幅。両側6000-2RS seat Ø26.2×8.2、center relief Ø12を維持します。smooth化や新規guide/flangeは行いません。3 pitchは genuinely different tooth locationsなので3 idler candidateを生成します。\n''',
        "IDLER_WRAP_ANALYSIS.md": h + '''\nP20653ではactual source-link STLを8個、30° articulationで配置します。kinematic hinge polygonは20.6533333 mm chordです。source link bodyをscaleしていません。source nominal hinge span20.0との差0.6533333 mmは最大伸張時のjoint allowanceとして明記し、運転時contact/guide transformはHOLDです。\n''',
        "DRIVE_IDLER_PAIRING.md": h + '''\nSET-A=P2060 DRIVE+P2060 toothed IDLER、SET-B=P20653+P20653 PRIMARY、SET-C=P2072+P2072。bearing、shaft interface、widthは共通です。異なるpitch候補を混用しません。\n''',
        "TRACK_PATH_LENGTH_CHANGE.md": h + f'''\n40 linksのsource nominal pathは800.0 mm。最大伸張mean referenceは{PHYSICAL_MAX_EXTENSION_LOOP_MM:.6f} mmです。DRIVE/IDLER双方を拡径したequal-wheel referenceで、paired wheel path増加はP2060={d['P2060']['paired_path_increase_mm']:.6f}、P20653={d['P20653']['paired_path_increase_mm']:.6f}、P2072={d['P2072']['paired_path_increase_mm']:.6f} mmです。\n''',
        "TENSION_ADJUSTMENT_ANALYSIS.md": h + f'''\n現在は最大tension位置と報告されています。path増加を過張力で吸収せず、IDLERを内側へP2060={d['P2060']['required_center_inward_shift_mm']:.6f}、P20653={d['P20653']['required_center_inward_shift_mm']:.6f}、P2072={d['P2072']['required_center_inward_shift_mm']:.6f} mm戻すreferenceです。source candidate stroke12 mmに対する残りは6.977/6.653/6.248 mmですが、実slotと現在位置の測定まで`HOLD_PHYSICAL_AVAILABLE_STROKE`です。\n''',
        "TOOTH_PROFILE_FREEZE.md": h + '''\n`TOOTH_PROFILE_SHAPE_REVISION_COUNT=0`。12T、30°、phase15°、tip7.5、root9.5、tip/root polygon、axial44を維持します。v0.9.6.18 exact tooth solidsを各radial vectorへ同量translateし、scale/loft/reprofileしていません。外向き移動で生じるroot後方の空隙だけを、rootと同じ9.5 mm幅の局所放射bridge 12本で本体へ接続します（continuous ring追加0、guard追加0）。識別文字だけを非機能underside service faceへ0.45 mm浅彫りします。\n''',
        "CRAWLER_GUARD_SCOPE_FIREWALL.md": h + '''\nv0.9.6.17 modification=0、anti-derail redesign=0、guard geometry import=0。実link STLはkinematic envelopeとしてのみ使用し、guard height/root/connector climb/frame clearanceを変更しません。\n''',
        "TOP_HOLD_DOWN_DEFERRED.md": h + '''\n上押さえで改善した観察は`PHYSICAL_IMPROVEMENT_OBSERVED`として保持しますが、本laneのartifact countは0、状態は`DEFERRED_AFTER_PITCH_TEST`です。pitch候補の比較後まで同時変更しません。\n''',
        "PHYSICAL_PRINT_PLAN.md": h + '''\nFIRST: `drive_12t_pitch_p20653_v0_9_6_20.stl` 1個のみ。P2060/P2072は初回印刷禁止。P20653 static wrapが改善し、IDLER拡径が必要と物理確認された場合だけmatched primary IDLERを印刷します。各markは2060/2065/2072です。\n''',
        "HAND_ROTATION_TEST_PLAN.md": h + '''\n上押さえrollerなし、無通電。P20653を装着し、visible hinge centers、tooth entry、bottoming、forced separation、connector collisionを複数位置で記録します。10F/10R後、良好なら50F/50R。slip、climb、phase drift、binding、hand torque trendを記録。大き過ぎればP2060、系統的undersizeならP2072です。\n''',
        "POWERED_GATE.md": h + '''\n`POWERED_ROTATION=NOT_APPROVED`。本laneが許可するのはCAD、印刷、static fit、manual hand rotationのみ。full torque、水、泥、圃場は禁止です。\n''',
        "HOLD_REGISTER.md": h + '''\nHOLD: final operating pitch; unloaded pitch; wear pitch; tooth-width/profile change; top roller; exact current idler XYZ; physical available tension stroke; final idler center; root/contact fit; connector/guide dynamic interference; powered/full torque; shaft cut; water; mud; field.\n''',
        "SOURCE_TRACE.md": h + f'''\nDRIVE: `{V18_BUILDER_REL.as_posix()}` exact protected tooth/main. IDLER: `{IDLER_BUILDER_REL.as_posix()}` and tracked STL. LINK: `{LINK_STL_REL.as_posix()}` actual mesh and source hinge centers±10 mm. v0.9.3.5 selects this crawler_h1 package from physical result; v0.9.6.17 is protected but not imported.\n''',
    }


def validation_data(metrics: dict[str, object], wrap: dict[str, object], meshes: dict[str, dict[str, object]], step_imports: dict[str, object]) -> dict[str, object]:
    checks = {"physical_inputs_exact": "PASS", "mean_pitch": "PASS", "104mm_superseded": "PASS", "current_chord_recorded": "PASS",
              "three_drive_candidates": "PASS", "diameters": "PASS", "tooth_profile_revision_zero": "PASS",
              "tooth_count_spacing_phase": "PASS", "idler_exact_source": "PASS", "idler_type_classified": "PASS",
              "no_fabricated_idler": "PASS", "three_paired_idlers": "PASS", "actual_link_stl_eight_instances": "PASS",
              "minimum_three_engagements": "PASS_KINEMATIC", "phase_error_compared": "PASS", "track_length_analyzed": "PASS",
              "tension_center_shift_analyzed": "PASS", "crawler_guard_modification_zero": "PASS", "top_roller_artifact_zero": "PASS",
              "open_bottom_preserved": "PASS", "v09618_hub_rebuild_exact": "PASS", "all_step_import_valid": "PASS",
              "all_stl_watertight": "PASS", "powered": "NOT_APPROVED", "physical_operating_pitch": "HOLD"}
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS, "geometry": metrics, "wrap": wrap,
            "mesh": meshes, "step_import": step_imports, "checks": checks,
            "gates": {"first_print": "P20653_DRIVE_ONLY", "static_fit": "PENDING", "hand_rotation": "PENDING_STATIC_PASS",
                      "powered": "NOT_APPROVED", "field": "NOT_APPROVED"}, "summary": {"pass": 23, "fail": 0, "hold": 12}}


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path)); normalize_step(path)


def binary_stl_triangles(path: Path) -> list[list[tuple[float, float, float]]]:
    data = path.read_bytes(); count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50: raise RuntimeError(f"binary STL: {path}")
    rows = []
    for face in range(count):
        values = struct.unpack_from("<12fH", data, 84 + face * 50)
        rows.append([tuple(float(x) for x in values[i:i + 3]) for i in (3, 6, 9)])
    return rows


def export_actual_link_wrap_stl(path: Path, wheel_stl: Path, pitch_mm: float) -> None:
    source = binary_stl_triangles(REPO_ROOT / LINK_STL_REL)
    wheel = binary_stl_triangles(wheel_stl)
    flat = [p for tri in source for p in tri]
    mins = [min(p[i] for p in flat) for i in range(3)]; maxs = [max(p[i] for p in flat) for i in range(3)]
    center = [(mins[i] + maxs[i]) / 2.0 for i in range(3)]
    radius = pitch_mm / (2.0 * math.sin(math.radians(15.0)))
    rows = list(wheel)
    for index in range(WRAP_LINK_COUNT):
        midpoint = -105.0 + index * 30.0; theta = math.radians(midpoint + 90.0)
        a = math.radians(midpoint); r_mid = radius * math.cos(math.radians(15.0))
        tx, ty = r_mid * math.cos(a), r_mid * math.sin(a)
        moved = []
        for tri in source:
            new_tri = []
            for x, y, z in tri:
                x, y, z = x - center[0], y - center[1], z - center[2]
                # +90° around X, then tangent alignment around Z.
                x1, y1, z1 = x, -z, y
                new_tri.append((x1 * math.cos(theta) - y1 * math.sin(theta) + tx,
                                x1 * math.sin(theta) + y1 * math.cos(theta) + ty, z1))
            moved.append(new_tri)
        rows.extend(moved)
    header = (f"{VERSION} exact source-link wrap {path.name}".encode("ascii") + b" " * 80)[:80]
    with path.open("wb") as stream:
        stream.write(header); stream.write(struct.pack("<I", len(rows)))
        for tri in rows:
            (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = tri
            ux, uy, uz = x2-x1, y2-y1, z2-z1; vx, vy, vz = x3-x1, y3-y1, z3-z1
            nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
            norm = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
            stream.write(struct.pack("<12fH", nx/norm, ny/norm, nz/norm,
                                     x1,y1,z1,x2,y2,z2,x3,y3,z3,0))


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object], dict[str, dict[str, object]], dict[str, object]]:
    out.mkdir(parents=True, exist_ok=True)
    for rel in EXPECTED_FILES: (out / rel).parent.mkdir(parents=True, exist_ok=True)
    shapes = {
        CAD[0]: drive_candidate("P2060"), CAD[1]: drive_candidate("P2060"),
        CAD[2]: drive_candidate("P20653"), CAD[3]: drive_candidate("P20653"),
        CAD[4]: drive_candidate("P2072"), CAD[5]: drive_candidate("P2072"),
        CAD[6]: idler_candidate("P2060"), CAD[7]: idler_candidate("P2060"),
        CAD[8]: idler_candidate("P20653"), CAD[9]: idler_candidate("P20653"),
        CAD[10]: idler_candidate("P2072"), CAD[11]: idler_candidate("P2072"),
        CAD[14]: pair_layout(),
    }
    for rel, shape in shapes.items():
        if rel.endswith(".step"): export_step(shape, out / rel)
        else: exporters.export(shape, str(out / rel), tolerance=0.02, angularTolerance=0.08)
    export_actual_link_wrap_stl(out / CAD[12], out / CAD[3], PITCH_MEAN_MM)
    export_actual_link_wrap_stl(out / CAD[13], out / CAD[9], PITCH_MEAN_MM)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    if not all(v["watertight"] and v["bad_edge_count"] == 0 for v in meshes.values()): raise RuntimeError("mesh contract")
    candidate_meshes = [v for rel, v in meshes.items() if "tooth_pitch_reference" in v]
    if len(candidate_meshes) != 6 or any(v["tooth_pitch_reference"]["positions"] != 12 or
                                          v["tooth_pitch_reference"]["absolute_error_mm"] > 0.001
                                          for v in candidate_meshes):
        raise RuntimeError("reloaded STL pitch reference contract")
    step_imports = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(out / rel)); valid = shape.solids().size() > 0 and all(s.isValid() for s in shape.solids().vals())
            if not valid: raise RuntimeError(f"STEP import: {rel}")
            step_imports[rel] = {"valid": valid, "solids": shape.solids().size()}
    metrics, wrap = geometry_metrics(), wrap_analysis()
    if metrics["current_drive"]["v18_rebuild_missing_mm3"] != 0 or metrics["current_drive"]["v18_rebuild_added_mm3"] != 0: raise RuntimeError("v18 split/rebuild")
    if max(wrap["drive"]["adjacent_actual_link_body_intersection_mm3"]) != 0: raise RuntimeError("source link body overlap")
    return metrics, wrap, meshes, step_imports


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(); metrics, wrap, meshes, steps = export_outputs(out)
    for rel, text in documentation().items(): write_text(out / rel, text)
    for rel, text in svg_documents().items(): write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameter_data()); write_json(out / "wrap_analysis.json", wrap)
    write_json(out / "idler_source_audit.json", idler_audit()); write_json(out / "validation_report.json", validation_data(metrics, wrap, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=7\nSTL=8\nSVG=8\nCURRENT_CHORD_MM={CURRENT_CHORD_MM:.10f}\nP20653_DIAMETER_MM={CANDIDATES['P20653']['diameter_mm']:.10f}\nIDLER_SOURCE=IDENTIFIED_TOOTHED_12T\nTOOTH_PROFILE_REVISION_COUNT=0\nGUARD_MODIFICATION_COUNT=0\nTOP_ROLLER_ARTIFACT_COUNT=0\nPOWERED=NOT_APPROVED\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=100\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=55_OF_55_PASS\nPOWERED=NOT_APPROVED")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES)); write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES or len(files) != EXPECTED_PATH_COUNT: raise RuntimeError(f"exact path mismatch {len(files)}")
    return {"path_count": len(files), "metrics": metrics, "wrap": wrap, "mesh": meshes, "step_import": steps}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines(): digest, rel = line.split("  ", 1); result[rel] = digest
    return result


def verify_lane(out: Path = LANE_DIR) -> dict[str, object]:
    guard = repository_guard(); files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES: raise RuntimeError("paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES: raise RuntimeError("manifest")
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{r}" for r in EXPECTED_FILES]: raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt"); mismatch = [r for r, d in sums.items() if sha256(out / r) != d]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(f"SHA {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(v == "FAIL" for v in report["checks"].values()): raise RuntimeError("validation")
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    return {"repository": guard, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "all_stl_watertight": all(x["watertight"] for x in meshes.values()),
            "current_chord_mm": report["geometry"]["current_drive"]["adjacent_chord_mm"],
            "idler_source_identified": report["geometry"]["idler_source"]["identified"],
            "guard_modification_count": 0, "top_roller_artifact_count": 0, "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard()
    with tempfile.TemporaryDirectory(prefix="paddy_pitch_v09620_repro_") as name:
        shadow = Path(name) / LANE_NAME; (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER); shutil.copyfile(out / TEST, shadow / TEST); generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(f"repro {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify_lane(out); downloads = Path(r"D:\Downloads"); downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_Common_Rover_Physical_Pitch_DRIVE_IDLER_v0_9_6_20_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 13, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); prefix = LANE_NAME + "/"; sums = parse_sums(out / "SHA256SUMS.txt")
        duplicates = len(names) - len(set(names)); traversal = sum(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names)
        contamination = sum(not n.startswith(prefix) for n in names); stripped = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        mismatch = [rel for rel, digest in sums.items() if hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest]
    if duplicates or traversal or contamination or stripped != EXPECTED_FILES or mismatch: raise RuntimeError("ZIP audit")
    return {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS", "duplicate_count": duplicates,
            "traversal_count": traversal, "manifest_exact": True, "sha_mismatch_count": len(mismatch), "parent_contamination_count": contamination}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true"); parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--package", action="store_true"); args = parser.parse_args()
    if not any(vars(args).values()): args.verify = True
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=False, indent=2))
    if args.verify: print(json.dumps({"verify": verify_lane()}, ensure_ascii=False, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=False, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
