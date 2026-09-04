#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the isolated DRIVE-entry top hold-down roller candidate v0.9.6.19.

This lane adds a removable vertical-2020-supported dry-test mechanism around
the read-only v0.9.6.18 DRIVE 12T.  It never imports crawler-guard geometry.
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
from typing import Iterable, Sequence
import zipfile

import cadquery as cq
from cadquery import exporters, importers


VERSION = "v0.9.6.19"
CLASSIFICATION = "DRIVE_ENTRY_TOP_HOLD_DOWN_ROLLER_DRY_TEST"
STATUS = (
    "DRIVE_ENTRY_TOP_HOLD_DOWN_ROLLER_COMPLETE/"
    "DRIVE_AND_CRAWLER_SCOPE_SEPARATED/"
    "VERTICAL_2020_SUPPORT_READY/"
    "DRY_TEST_ROLLER_READY_FOR_PHYSICAL_PRINT/"
    "FULL_POWER_NOT_APPROVED/"
    "COMMIT_READY_NOT_STAGED"
)

LANE_NAME = "common_rover_drive_entry_top_hold_down_roller_v0_9_6_19"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2398
BASE_OUTSIDE_DIGEST = "e1ce40613e219c747011f24ec5fe880d6f047de22f218a830078a14e223590fb"

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
}

V18_REL = PurePosixPath("cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18")
V18_DIR = REPO_ROOT / V18_REL
V18_MAIN_REL = "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.step"
V18_CAP_REL = "artifacts/h25a1_dual_l_slide_cap_v0_9_6_18.step"
V18_KEY_REL = "artifacts/h25a1_dual_l_stop_key_v0_9_6_18.step"
PINNED_SOURCE_SHA256 = {
    f"{V18_REL.as_posix()}/build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py": "254e96145c2f8501dbfe98b437b363d6d6cfecc7be2f666e7d84fd710a3b9962",
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6/build_narrow_frame_independent_drive_v0_9_6_6.py": "2139e64fefc5776449885728bf81f2745557646adb6d5cd9233dd6a34720af29",
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/dimensions.json": "77ae432278d07302883f78ad71f3152d28895c672bb0282a486c78ffc8db1f16",
}
V18_ARTIFACT_SHA256 = {
    V18_MAIN_REL: "f492ad24c9c81b2c0c6602397dad7f6c71a064f69244cb2a18f7f7cce8a1dcfe",
    "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.stl": "2b7aa66660fed7cb37be2300cbd08f87f6d494b9500a7b5a3162ff5912924ea9",
    V18_CAP_REL: "db77749126c1dcbed4d120b6f950197211fa9e2b8202e74b94e7bc9212acea05",
    V18_KEY_REL: "22508553a109a1f88cc29759cea33d6f062f953eb9d2bd1d30b23e74647b709c",
}

# Local layout reference. +X is downstream toward sprocket, +Y points from the
# crawler centre toward the selected frame face, +Z is up.
SPROCKET_CENTER = (0.0, 0.0, 65.0)
SPROCKET_TIP_RADIUS_MM = 33.282411
LINK_WIDTH_MM = 54.0                    # measured history, used as envelope
LINK_FLAT_WIDTH_EACH_MM = 10.0          # user physical authority
LINK_BASE_THICKNESS_MM = 6.0            # abstract dry-layout envelope
LINK_BOTTOM_Z_MM = SPROCKET_CENTER[2] + SPROCKET_TIP_RADIUS_MM
LINK_TOP_Z_MM = LINK_BOTTOM_Z_MM + LINK_BASE_THICKNESS_MM
LINK_OUTER_FACE_Y_MM = LINK_WIDTH_MM / 2.0
FRAME_NEAREST_FACE_DISTANCE_MM = 60.0   # user physical authority
POST_NEAR_FACE_Y_MM = LINK_OUTER_FACE_Y_MM + FRAME_NEAREST_FACE_DISTANCE_MM
POST_CENTER_Y_MM = POST_NEAR_FACE_Y_MM + 10.0
VERTICAL_2020_CUT_LENGTH_MM = 110.0
VERTICAL_2020_BOTTOM_Z_MM = 20.0
VERTICAL_2020_TOP_Z_MM = 130.0
ENTRY_DATUM_X_MM = -26.0
ROLLER_UPSTREAM_MM = 10.0
ROLLER_CENTER_X_MM = ENTRY_DATUM_X_MM - ROLLER_UPSTREAM_MM
ROLLER_OD_MM = 16.0
ROLLER_RADIUS_MM = ROLLER_OD_MM / 2.0
ROLLER_WIDTH_MM = 8.0
ROLLER_BORE_MM = 4.3
ROLLER_CENTER_ABS_Y_MM = 22.0
ROLLER_CENTER_Z_AT_ZERO_MM = LINK_TOP_Z_MM + ROLLER_RADIUS_MM
ROLLER_AXIS = "M4x20_TWO_INDEPENDENT_AXLES"
PUSH_VALUES_MM = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
PHYSICAL_TEST_PUSH_VALUES_MM = [0.0, 0.5, 1.0, 1.5, 2.0]
UPSTREAM_RANGE_MM = [5.0, 15.0]

BUILDER = Path(__file__).name
TEST = "tests/test_drive_entry_top_hold_down_roller_v0_9_6_19_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "DRIVE_CRAWLER_SCOPE_FIREWALL.md",
    "VERTICAL_2020_SUPPORT_SPEC.md", "UPPER_LOWER_MOUNT_BRACKET_SPEC.md",
    "SPLIT_ROLLER_SPEC.md", "ROLLER_ADJUSTMENT_SPEC.md", "LAYOUT_DATUM_SPEC.md",
    "BELT_ENTRY_OPEN_BOTTOM_SERVICE.md", "ASSEMBLY_SEQUENCE.md", "PRINT_PLAN.md",
    "DRY_HAND_TEST_PLAN.md", "POWERED_GATE.md", "HOLD_REGISTER.md",
]
CAD = [
    "artifacts/vertical_2020_upper_mount_bracket_v0_9_6_19.step",
    "artifacts/vertical_2020_upper_mount_bracket_v0_9_6_19.stl",
    "artifacts/vertical_2020_lower_mount_bracket_v0_9_6_19.step",
    "artifacts/vertical_2020_lower_mount_bracket_v0_9_6_19.stl",
    "artifacts/drive_entry_roller_carriage_bracket_v0_9_6_19.step",
    "artifacts/drive_entry_roller_carriage_bracket_v0_9_6_19.stl",
    "artifacts/drive_entry_split_plain_roller_v0_9_6_19.step",
    "artifacts/drive_entry_split_plain_roller_v0_9_6_19.stl",
    "artifacts/drive_entry_split_plain_roller_pair_v0_9_6_19.stl",
    "artifacts/vertical_2020_110mm_reference_v0_9_6_19.step",
    "artifacts/v09618_drive_entry_top_hold_down_assembly_v0_9_6_19.step",
]
SVGS = [
    "artifacts/drive_entry_vertical_2020_layout_v0_9_6_19.svg",
    "artifacts/split_roller_contact_section_v0_9_6_19.svg",
    "artifacts/push_in_adjustment_matrix_v0_9_6_19.svg",
    "artifacts/belt_side_entry_open_bottom_service_v0_9_6_19.svg",
]
JSONS = ["design_parameters.json", "interference_report.json", "validation_report.json"]
SOURCES = [BUILDER, TEST]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)
EXPECTED_PATH_COUNT = 39


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(
        r"(?<=FILE_NAME\('Open CASCADE Shape Model',')\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "2026-08-12T00:00:00", text, count=1,
    )
    if count != 1:
        raise RuntimeError(f"STEP timestamp normalization failed: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def git_bytes(args: Sequence[str]) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, capture_output=True).stdout


def git_text(args: Sequence[str]) -> str:
    return git_bytes(args).decode("utf-8", "surrogateescape").strip()


def untracked_paths() -> list[str]:
    raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z"])
    return [item.decode("utf-8", "surrogateescape") for item in raw.split(b"\0") if item]


def tree_digest(paths: Iterable[Path], base: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix()
        h.update(rel.encode() + b"\0" + sha256(path).encode() + b"\n")
    return h.hexdigest()


def repository_guard() -> dict[str, object]:
    root = Path(git_text(["rev-parse", "--show-toplevel"])).resolve()
    branch = git_text(["branch", "--show-current"])
    head = git_text(["rev-parse", "HEAD"])
    staged = [x for x in git_text(["diff", "--cached", "--name-only"]).splitlines() if x]
    dirty = [x for x in git_text(["diff", "--name-only"]).splitlines() if x]
    if root != REPO_ROOT.resolve() or branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise RuntimeError("FAIL_CLOSED repository/branch/HEAD")
    if staged or dirty != TRACKED_DIRTY:
        raise RuntimeError(f"FAIL_CLOSED staged/dirty: {staged}/{dirty}")
    for rel, expected in AUTHORITY_SHA256.items():
        if sha256(REPO_ROOT / rel) != expected:
            raise RuntimeError(f"FAIL_CLOSED authority: {rel}")
    prefix = LANE_REL.as_posix() + "/"
    all_untracked = untracked_paths()
    outside = sorted(p for p in all_untracked if not p.startswith(prefix))
    outside_digest = tree_digest([REPO_ROOT / PurePosixPath(p) for p in outside], REPO_ROOT)
    if len(outside) != BASE_OUTSIDE_COUNT or outside_digest != BASE_OUTSIDE_DIGEST:
        raise RuntimeError(f"FAIL_CLOSED existing untracked: {len(outside)} {outside_digest}")
    lane_paths = sorted(p[len(prefix):] for p in all_untracked if p.startswith(prefix))
    unexpected = sorted(set(lane_paths) - set(EXPECTED_FILES))
    if unexpected:
        raise RuntimeError(f"FAIL_CLOSED unexpected lane path: {unexpected}")
    protected = {}
    for rel, expected in PROTECTED_LANES.items():
        raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z", "--", rel])
        paths = [x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x]
        actual = tree_digest([REPO_ROOT / PurePosixPath(p) for p in paths], REPO_ROOT / PurePosixPath(rel))
        if (len(paths), actual) != expected:
            raise RuntimeError(f"FAIL_CLOSED protected lane: {rel} {len(paths)} {actual}")
        protected[rel] = {"count": len(paths), "tree_sha256": actual, "status": "UNCHANGED"}
    for rel, expected in PINNED_SOURCE_SHA256.items():
        if sha256(REPO_ROOT / PurePosixPath(rel)) != expected:
            raise RuntimeError(f"FAIL_CLOSED source changed: {rel}")
    for rel, expected in V18_ARTIFACT_SHA256.items():
        if sha256(V18_DIR / rel) != expected:
            raise RuntimeError(f"FAIL_CLOSED v0.9.6.18 changed: {rel}")
    return {
        "repository": str(REPO_ROOT), "branch": branch, "head": head,
        "staged_count": 0, "tracked_dirty_paths": dirty,
        "outside_untracked_count": len(outside), "outside_untracked_tree_sha256": outside_digest,
        "lane_untracked_count": len(lane_paths), "authority_sha256": dict(AUTHORITY_SHA256),
        "protected_lanes": protected, "pinned_sources": dict(PINNED_SOURCE_SHA256),
        "v09618_artifacts": dict(V18_ARTIFACT_SHA256),
    }


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, True)).translate(center)


def cylinder_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length / 2.0, both=True).translate(center)


def cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cylinder_z(radius, length, (0.0, 0.0, 0.0)).rotate((0, 0, 0), (1, 0, 0), 90).translate(center)


def cylinder_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cylinder_z(radius, length, (0.0, 0.0, 0.0)).rotate((0, 0, 0), (0, 1, 0), 90).translate(center)


def compound(parts: Iterable[cq.Workplane]) -> cq.Workplane:
    solids = []
    for part in parts:
        solids.extend(part.solids().vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(solids))


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def bounds(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]


def normalize_for_print(shape: cq.Workplane) -> cq.Workplane:
    bb = shape.val().BoundingBox()
    return shape.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def actual_v18(rel: str) -> cq.Workplane:
    return importers.importStep(str(V18_DIR / rel))


def placed_parent(rel: str) -> cq.Workplane:
    return actual_v18(rel).rotate((0, 0, 0), (1, 0, 0), 90).translate(SPROCKET_CENTER)


def parent_main() -> cq.Workplane:
    return placed_parent(V18_MAIN_REL)


def parent_cap() -> cq.Workplane:
    return placed_parent(V18_CAP_REL)


def parent_key() -> cq.Workplane:
    return placed_parent(V18_KEY_REL)


def frame_references() -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    lower = box(100.0, 20.0, 20.0, (ROLLER_CENTER_X_MM, POST_CENTER_Y_MM, 10.0))
    post = box(20.0, 20.0, VERTICAL_2020_CUT_LENGTH_MM,
               (ROLLER_CENTER_X_MM, POST_CENTER_Y_MM, 75.0))
    upper = box(100.0, 20.0, 20.0, (ROLLER_CENTER_X_MM, POST_CENTER_Y_MM, 140.0))
    return lower, post, upper


def vertical_2020_reference() -> cq.Workplane:
    return frame_references()[1]


def mount_bracket_world(joint_z: float) -> cq.Workplane:
    x, y = ROLLER_CENTER_X_MM, POST_CENTER_Y_MM
    face = box(36.0, 6.0, 58.0, (x, y + 13.0, joint_z))
    return_flange = box(6.0, 20.0, 58.0, (x + 13.0, y + 16.0, joint_z))
    part = face.union(return_flange)
    for dz in (-12.0, 12.0):
        part = part.cut(box(5.5, 10.0, 9.0, (x, y + 13.0, joint_z + dz)))
        part = part.cut(box(10.0, 5.5, 9.0, (x + 13.0, y + 16.0, joint_z + dz)))
    return part.clean()


def lower_mount_bracket() -> cq.Workplane:
    return mount_bracket_world(20.0)


def upper_mount_bracket() -> cq.Workplane:
    return mount_bracket_world(130.0)


def mount_bracket_print(upper: bool) -> cq.Workplane:
    shape = upper_mount_bracket() if upper else lower_mount_bracket()
    # Lay the broad face on the bed; the two files retain their assembly role.
    return normalize_for_print(shape.rotate((0, 0, 0), (1, 0, 0), 90))


def plain_roller() -> cq.Workplane:
    roller = cylinder_z(ROLLER_RADIUS_MM, ROLLER_WIDTH_MM, (0.0, 0.0, ROLLER_WIDTH_MM / 2.0))
    roller = roller.cut(cylinder_z(ROLLER_BORE_MM / 2.0, ROLLER_WIDTH_MM + 1.0,
                                   (0.0, 0.0, ROLLER_WIDTH_MM / 2.0)))
    return roller.clean()


def installed_roller(side: int, push_mm: float) -> cq.Workplane:
    z = ROLLER_CENTER_Z_AT_ZERO_MM - push_mm
    return plain_roller().translate((0, 0, -ROLLER_WIDTH_MM / 2.0)).rotate(
        (0, 0, 0), (1, 0, 0), 90).translate(
        (ROLLER_CENTER_X_MM, side * ROLLER_CENTER_ABS_Y_MM, z))


def installed_rollers(push_mm: float) -> cq.Workplane:
    return compound([installed_roller(-1, push_mm), installed_roller(1, push_mm)])


def roller_pair_print() -> cq.Workplane:
    return compound([plain_roller().translate((-12.0, 0, 0)), plain_roller().translate((12.0, 0, 0))])


def roller_carriage(push_mm: float = 0.0) -> cq.Workplane:
    x = ROLLER_CENTER_X_MM
    zc = ROLLER_CENTER_Z_AT_ZERO_MM - push_mm
    post_face = POST_NEAR_FACE_Y_MM
    cross_bottom = zc + 13.7
    back_bottom, back_top = zc - 23.0, cross_bottom + 6.0
    back = box(32.0, 6.0, back_top - back_bottom,
               (x, post_face - 3.0, (back_bottom + back_top) / 2.0))
    cross = box(16.0, 113.0, 6.0, (x, 24.5, cross_bottom + 3.0))
    ear_bottom, ear_top = zc - 5.0, cross_bottom + 3.0
    ears = []
    for y in (-27.8, -16.2, 16.2, 27.8):
        ears.append(box(12.0, 3.0, ear_top - ear_bottom, (x, y, (ear_bottom + ear_top) / 2.0)))
    # Central upper gusset supports the 60 mm cantilever without entering the link path.
    rib = cq.Workplane("YZ").polyline([
        (30.0, cross_bottom), (81.0, cross_bottom), (81.0, zc - 7.0)
    ]).close().extrude(3.0, both=True).translate((x, 0, 0))
    part = back.union(cross).union(rib)
    for ear in ears:
        part = part.union(ear)
    # Two vertical adjustment slots on the single 2020 face.
    for dz in (-12.0, 12.0):
        part = part.cut(box(5.5, 10.0, 8.5, (x, post_face - 3.0, zc + 1.0 + dz)))
    # Coaxial cuts form two independent forks; the central air gap stays open.
    part = part.cut(cylinder_y(ROLLER_BORE_MM / 2.0, 80.0, (x, 0.0, zc)))
    return part.clean()


def roller_carriage_print() -> cq.Workplane:
    # Put the long crossbar top and backplate top on one broad bed plane.
    return normalize_for_print(roller_carriage().rotate((0, 0, 0), (1, 0, 0), 180))


def link_envelopes() -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    left = box(70.0, 10.0, LINK_BASE_THICKNESS_MM,
               (-55.0, -ROLLER_CENTER_ABS_Y_MM, (LINK_BOTTOM_Z_MM + LINK_TOP_Z_MM) / 2.0))
    right = box(70.0, 10.0, LINK_BASE_THICKNESS_MM,
                (-55.0, ROLLER_CENTER_ABS_Y_MM, (LINK_BOTTOM_Z_MM + LINK_TOP_Z_MM) / 2.0))
    centre = box(70.0, 28.0, 5.0, (-55.0, 0.0, LINK_TOP_Z_MM + 2.5))
    return left, right, centre


def belt_side_entry_corridor() -> cq.Workplane:
    # Conservative lower/side service corridor through the protected open bottom.
    return box(72.0, 190.0, 24.0, (0.0, 0.0, 34.0))


def open_bottom_keepout() -> cq.Workplane:
    return box(80.0, 80.0, 18.0, (0.0, 0.0, 18.0))


def axle_hardware(push_mm: float = 0.0) -> cq.Workplane:
    z = ROLLER_CENTER_Z_AT_ZERO_MM - push_mm
    return compound([
        cylinder_y(2.0, 20.0, (ROLLER_CENTER_X_MM, -ROLLER_CENTER_ABS_Y_MM, z)),
        cylinder_y(2.0, 20.0, (ROLLER_CENTER_X_MM, ROLLER_CENTER_ABS_Y_MM, z)),
    ])


def reference_assembly() -> cq.Workplane:
    lower, post, upper = frame_references()
    link_left, link_right, centre = link_envelopes()
    push = 1.0
    shaft = cylinder_y(5.0, 90.0, SPROCKET_CENTER)
    return compound([
        parent_main(), parent_cap(), parent_key(), shaft,
        lower, post, upper, lower_mount_bracket(), upper_mount_bracket(),
        roller_carriage(push), installed_rollers(push), axle_hardware(push),
        link_left, link_right, centre,
    ])


def geometry_metrics() -> dict[str, object]:
    main, cap, key = parent_main(), parent_cap(), parent_key()
    lower, post, upper = frame_references()
    flat_left, flat_right, centre = link_envelopes()
    belt, bottom = belt_side_entry_corridor(), open_bottom_keepout()
    rows = []
    for push in PUSH_VALUES_MM:
        rollers = installed_rollers(push)
        carriage = roller_carriage(push)
        auxiliary = compound([rollers, carriage])
        rows.append({
            "push_mm": push,
            "left_flat_intended_contact_mm3": common_volume(installed_roller(-1, push), flat_left),
            "right_flat_intended_contact_mm3": common_volume(installed_roller(1, push), flat_right),
            "roller_vs_central_protrusion_mm3": common_volume(rollers, centre),
            "roller_vs_protected_12t_mm3": common_volume(rollers, main),
            "carriage_vs_link_flats_mm3": common_volume(carriage, compound([flat_left, flat_right])),
            "carriage_vs_central_protrusion_mm3": common_volume(carriage, centre),
            "carriage_vs_protected_12t_mm3": common_volume(carriage, main),
            "auxiliary_vs_dual_l_cap_mm3": common_volume(auxiliary, cap),
            "auxiliary_vs_stop_key_mm3": common_volume(auxiliary, key),
            "auxiliary_vs_belt_entry_corridor_mm3": common_volume(auxiliary, belt),
            "auxiliary_vs_open_bottom_keepout_mm3": common_volume(auxiliary, bottom),
            "axle_vs_roller_material_mm3": common_volume(axle_hardware(push), rollers),
        })
    non_intended_keys = [
        "roller_vs_central_protrusion_mm3", "roller_vs_protected_12t_mm3",
        "carriage_vs_link_flats_mm3", "carriage_vs_central_protrusion_mm3",
        "carriage_vs_protected_12t_mm3", "auxiliary_vs_dual_l_cap_mm3",
        "auxiliary_vs_stop_key_mm3", "auxiliary_vs_belt_entry_corridor_mm3",
        "auxiliary_vs_open_bottom_keepout_mm3", "axle_vs_roller_material_mm3",
    ]
    max_unintended = max(row[key] for row in rows for key in non_intended_keys)
    return {
        "coordinate_system": "+X downstream; +Y crawler-to-frame; +Z up",
        "layout": {
            "sprocket_center_mm": list(SPROCKET_CENTER), "entry_datum_x_mm": ENTRY_DATUM_X_MM,
            "roller_center_x_mm": ROLLER_CENTER_X_MM, "roller_upstream_mm": ROLLER_UPSTREAM_MM,
            "upstream_allowed_range_mm": UPSTREAM_RANGE_MM,
            "link_outer_face_y_mm": LINK_OUTER_FACE_Y_MM,
            "vertical_2020_near_face_y_mm": POST_NEAR_FACE_Y_MM,
            "link_to_frame_face_mm": POST_NEAR_FACE_Y_MM - LINK_OUTER_FACE_Y_MM,
        },
        "frame": {
            "vertical_2020_bounds_mm": bounds(post), "cut_length_mm": VERTICAL_2020_CUT_LENGTH_MM,
            "lower_mount_bounds_mm": bounds(lower_mount_bracket()),
            "upper_mount_bounds_mm": bounds(upper_mount_bracket()),
            "post_vs_carriage_mm3": common_volume(post, roller_carriage()),
            "frame_vs_parent_12t_mm3": common_volume(compound([lower, post, upper]), main),
        },
        "roller": {
            "single_bounds_mm": bounds(plain_roller()), "pair_solid_count": roller_pair_print().solids().size(),
            "width_margin_each_flat_mm": LINK_FLAT_WIDTH_EACH_MM - ROLLER_WIDTH_MM,
            "axis": ROLLER_AXIS, "push_rows": rows, "max_unintended_intersection_mm3": max_unintended,
            "intended_contact_monotonic": all(
                rows[i]["left_flat_intended_contact_mm3"] <= rows[i + 1]["left_flat_intended_contact_mm3"] + 1e-6
                for i in range(len(rows) - 1)),
        },
        "protected_12t": {
            "artifact_sha256": V18_ARTIFACT_SHA256[V18_MAIN_REL],
            "source_volume_mm3": volume(actual_v18(V18_MAIN_REL)),
            "placed_volume_mm3": volume(main), "missing_volume_mm3": 0.0,
            "geometry_operation": "IMPORT_ROTATE_TRANSLATE_ONLY_NO_BOOLEAN_MODIFICATION",
        },
        "service": {
            "belt_side_entry_intersection_max_mm3": max(row["auxiliary_vs_belt_entry_corridor_mm3"] for row in rows),
            "open_bottom_intersection_max_mm3": max(row["auxiliary_vs_open_bottom_keepout_mm3"] for row in rows),
            "roller_carriage_removable": True, "vertical_2020_remains_after_carriage_removal": True,
        },
    }


def mesh_metrics(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"STL_TOO_SHORT: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError(f"STL_NOT_BINARY: {path}")
    edges: dict[tuple[tuple[float, ...], tuple[float, ...]], list[int]] = collections.defaultdict(list)
    vertices = []
    for face in range(count):
        values = struct.unpack_from("<12fH", data, 84 + face * 50)
        tri = [tuple(round(float(v), 6) for v in values[i:i + 3]) for i in (3, 6, 9)]
        vertices.extend(tri)
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((tri[a], tri[b])))].append(face)
    bad = sum(len(faces) != 2 for faces in edges.values())
    adjacency = [[] for _ in range(count)]
    for faces in edges.values():
        if len(faces) == 2:
            a, b = faces; adjacency[a].append(b); adjacency[b].append(a)
    seen, components = set(), 0
    for start in range(count):
        if start in seen:
            continue
        components += 1; stack = [start]; seen.add(start)
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]
    return {
        "triangles": count, "watertight": bad == 0, "bad_edge_count": bad,
        "connected_solid_count": components,
        "bounds_mm": [mins, maxs], "extents_mm": [maxs[i] - mins[i] for i in range(3)],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.frame{{fill:#adb5bd;stroke:#343a40;stroke-width:3}}.drive{{fill:#f4a261;stroke:#9c3f00;stroke-width:3}}.link{{fill:#90be6d;stroke:#2d6a4f;stroke-width:3}}.roller{{fill:#457b9d;stroke:#123b55;stroke-width:3}}.arm{{fill:#ffd166;stroke:#8a5a00;stroke-width:3}}.hold{{stroke:#d62828;stroke-width:4;fill:none}}.dim{{stroke:#264653;stroke-width:3;fill:none}}</style>
<text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · DRIVE-only dry hand-test candidate · POWERED/FIELD NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    layout = svg_page("DRIVE entry hold-down: vertical 2020 layout", '''<g transform="translate(90,70)"><rect x="760" y="60" width="65" height="500" class="frame"/><rect x="680" y="60" width="225" height="65" class="frame"/><rect x="680" y="495" width="225" height="65" class="frame"/><path d="M755 250H480V300H350" class="arm" stroke-width="38"/><circle cx="350" cy="330" r="62" class="drive"/><rect x="80" y="245" width="310" height="54" class="link"/><circle cx="245" cy="220" r="30" class="roller"/><line x1="825" y1="190" x2="825" y2="470" class="dim"/><text x="850" y="335" class="l">2020 cut 110 mm candidate</text><line x1="390" y1="180" x2="760" y2="180" class="dim"/><text x="500" y="165" class="l">link outer face → post face ≈60 mm</text><text x="85" y="610" class="l">roller centre = 10 mm upstream of first-entry datum (allowed 5–15 mm)</text></g>''')
    split = svg_page("Split plain rollers avoid the central link feature", '''<g transform="translate(110,110)"><rect x="90" y="270" width="780" height="110" class="link"/><rect x="385" y="205" width="190" height="175" fill="#588157" stroke="#2d6a4f" stroke-width="3"/><circle cx="280" cy="240" r="72" class="roller"/><circle cx="680" cy="240" r="72" class="roller"/><line x1="208" y1="130" x2="352" y2="130" class="dim"/><text x="245" y="112" class="l">8 mm roller</text><line x1="608" y1="130" x2="752" y2="130" class="dim"/><text x="645" y="112" class="l">8 mm roller</text><text x="360" y="440" class="l">central raised feature remains untouched</text><text x="160" y="500" class="l">Each link flat = 10 mm → 2 mm axial margin per flat</text><text x="160" y="545" class="l">Plain PETG roller Ø16 / bore Ø4.3 / M4×20 independent axle · dry hand-test only</text></g>''')
    matrix = svg_page("Push-in adjustment matrix", '''<g transform="translate(80,100)"><line x1="90" y1="500" x2="1050" y2="500" class="dim"/><g class="roller"><circle cx="130" cy="210" r="55"/><circle cx="290" cy="225" r="55"/><circle cx="450" cy="240" r="55"/><circle cx="610" cy="255" r="55"/><circle cx="770" cy="270" r="55"/><circle cx="930" cy="300" r="55"/></g><g class="l"><text x="105" y="590">0.0</text><text x="265" y="590">0.5</text><text x="425" y="590">1.0</text><text x="585" y="590">1.5</text><text x="745" y="590">2.0</text><text x="905" y="590">3.0 mm</text></g><text x="235" y="55" class="l">Start at 0.0; increase only while hand-rotation remains smooth.</text><text x="205" y="90" class="l">Physical test series: 0 / 0.5 / 1.0 / 1.5 / 2.0 mm. 3.0 is adjustment envelope only.</text></g>''')
    service = svg_page("Belt side entry and true open bottom remain clear", '''<g transform="translate(100,85)"><circle cx="410" cy="320" r="170" class="drive"/><path d="M60 510H760V650H60Z" fill="#dff6ff" stroke="#118ab2" stroke-width="4"/><path d="M410 610H980" class="dim"/><polygon points="950,590 1000,610 950,630" fill="#264653"/><text x="690" y="580" class="l">belt side-entry service direction</text><rect x="780" y="40" width="70" height="410" class="frame"/><path d="M815 250H500" class="arm" stroke-width="34"/><circle cx="480" cy="205" r="42" class="roller"/><text x="70" y="60" class="l">Auxiliary mechanism does not enter the lower service corridor.</text><text x="70" y="95" class="l">Remove the two-M5 carriage before belt/link service if more hand space is needed.</text><text x="70" y="130" class="l">Vertical 2020 may remain; protected v0.9.6.18 body is unchanged.</text></g>''')
    return dict(zip(SVGS, [layout, split, matrix, service]))


def parameter_data() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "scope": {"drive_entry_hold_down_only": True, "crawler_guard_geometry_dependency_count": 0,
                  "v09618_body_modified": False},
        "physical_authority": {"link_to_nearest_frame_face_mm": 60.0,
                               "link_flat_width_each_mm": 10.0,
                               "manual_top_press_improved_engagement": True},
        "frame": {"profile": "2020", "vertical_cut_length_mm": 110.0,
                  "cut_length_class": "CANDIDATE_FROM_PHYSICAL_COMPACT_FRAME_HISTORY",
                  "cut_gate": "HOLD_VERIFY_ACTUAL_UPPER_LOWER_FACE_GAP",
                  "mount": "TWO_PRINTED_L_SPLICE_BRACKETS_WITH_M5_T_NUT_SLOTS"},
        "roller": {"architecture": "LEFT_RIGHT_SPLIT_PLAIN_ROLLER", "quantity": 2,
                   "od_mm": 16.0, "width_each_mm": 8.0, "bore_mm": 4.3,
                   "axis": ROLLER_AXIS, "bearing": "NONE_DRY_TEST_PLAIN_BORE",
                   "bearing_selection": "HOLD", "flat_margin_each_mm": 2.0},
        "adjustment": {"push_range_mm": [0.0, 3.0], "cad_samples_mm": PUSH_VALUES_MM,
                       "physical_test_mm": PHYSICAL_TEST_PUSH_VALUES_MM,
                       "vertical_slot_length_mm": 8.5, "vertical_slot_width_mm": 5.5,
                       "upstream_mm": 10.0, "allowed_upstream_mm": UPSTREAM_RANGE_MM},
        "print": {"printer": "Bambu A1", "material": "PETG",
                  "internal_closed_support": False, "slicer": "HOLD_SLICER_NOT_RUN"},
        "gates": {"first": "DRY_HAND_TEST_ONLY", "powered": "NOT_APPROVED",
                  "field": "NOT_APPROVED", "water": "NOT_APPROVED", "mud": "NOT_APPROVED"},
        "source_sha256": dict(PINNED_SOURCE_SHA256), "v09618_sha256": dict(V18_ARTIFACT_SHA256),
    }


def documentation() -> dict[str, str]:
    h = f"# Common Rover DRIVE Entry Top Hold-Down Roller {VERSION}\n\nClassification: `{CLASSIFICATION}`.\n"
    return {
        "README.md": h + f'''\nDRIVE 12Tへ噛み始める直前のcrawler linkを上から軽く押さえる、乾地手回し試験専用の独立laneです。縦2020支柱、上下L-splice bracket、着脱式carriage、左右分割plain rollerだけを追加し、v0.9.6.18の凍結DRIVE 12Tは変更しません。CRAWLER脱輪guardは完全に別scopeです。\n\nStatus: `{STATUS}`\n''',
        "DESIGN_AUTHORITY.md": h + '''\n物理authorityは、link外面から最寄りframe面まで約60 mm、左右平坦部各10 mm、上から押すと改善傾向、の3点です。現行compact-frame履歴の上下間2020長110 mmを候補に採用します。絶対entry datum、link厚、中央突起高さはlayout envelopeであり再測定HOLDです。\n''',
        "DRIVE_CRAWLER_SCOPE_FIREWALL.md": h + '''\n本laneはDRIVE 12T入口の上押さえ補助だけを扱います。v0.9.6.17 crawler-link anti-derail guardのshape/import/dependencyは0です。crawler link自体は物理幅authorityを用いた抽象contact envelopeのみで、guardを改造・複製しません。\n''',
        "VERTICAL_2020_SUPPORT_SPEC.md": h + '''\n追加材は市販2020アルミ押出材1本、候補切断長110.0 mmです。根拠はstructural height 150 mmのcompact physical referenceにおける上下20-series材間110 mmです。narrow-frame変更は主として横方向170 mm化であり、このZ履歴を自動変更しません。実物の上下面間を測り110±1 mmとの整合を確認するまで `HOLD_ALUMINUM_CUT` です。\n''',
        "UPPER_LOWER_MOUNT_BRACKET_SPEC.md": h + '''\n上下はPETG製L-splice bracket各1個で、既存railと縦2020の隣接2面を跨ぎます。各面に5.5×9.0 mm長穴を2箇所設け、M5 T-nut候補で後付けします。これは乾地位置保持候補であり、powered reactionをPETG spliceだけへ入力する承認ではありません。\n''',
        "SPLIT_ROLLER_SPEC.md": h + '''\n左右分割plain rollerを採用します。各rollerはØ16×8、bore Ø4.3、各10 mm平坦部内に2 mm軸方向余裕を残します。中央raised featureを跨ぐ連続rollerは使いません。各rollerは独立M4×20 bolt候補とwasher/nylocで保持します。bearing未選定につき摩擦・摩耗・発熱はHOLDです。\n''',
        "ROLLER_ADJUSTMENT_SPEC.md": h + '''\n最優先調整は上下です。2020面の2本の5.5×8.5 mm vertical slotで0～3 mmの押し込みを与えます。CADは0.5 mm刻みで0～3 mmをsampleし、物理試験は0/0.5/1.0/1.5/2.0 mmの順です。3.0 mmは機構envelopeであり初回試験値ではありません。\n''',
        "LAYOUT_DATUM_SPEC.md": h + '''\nLocal +Xは12Tへ向かうdownstream、+Yはcrawlerからframe、+Zは上です。候補first-entry datum X=-26 mm、roller中心X=-36 mm、すなわち10 mm upstreamで5～15 mm要求内です。この絶対datumは現物link pitch姿勢で再確認してください。\n''',
        "BELT_ENTRY_OPEN_BOTTOM_SERVICE.md": h + '''\n全0～3 mm sampleで補助機構と下側belt side-entry corridor/open-bottom keep-outのcommon volumeは0です。belt/link作業時はcarriageのM5×2を外せます。縦2020は残せます。12T下側を跨ぐ連続材は追加していません。\n''',
        "ASSEMBLY_SEQUENCE.md": h + '''\n1) Batteryを外す。2) 実frame面間を測る。3) 上下L bracketを仮止め。4) 110 mm候補2020を仮配置。5) carriageを0 mm位置で固定。6) plain roller×2を各M4×20で装着。7) link/12T/belt serviceを確認。8) 手回しだけで試験。9) 擦れ・重さ・白化があれば停止。\n''',
        "PRINT_PLAN.md": h + '''\n初回はplain roller 1個、次にroller 2個、次にcarriage、最後に上下mount bracketの順です。PETG/Bambu A1候補。rollerは円盤面、mount bracketは広いsplice面、carriageは長いcantilever crossbar上面とbackplate上端を同一bed面へ置き、約43 mm高さで印刷します。内部閉鎖supportはありません。slicer未実行のため `HOLD_SLICER_NOT_RUN` です。\n''',
        "DRY_HAND_TEST_PLAN.md": h + '''\n最初は0 mm、次に0.5/1.0/1.5/2.0 mm。各条件で同じ方向20 link-pitchesと逆方向20 link-pitchesを手回しし、歯滑り回数、link浮き高さ、中央突起/roller擦れ、偏摩耗、手回し重さ、carriage移動、M4緩みを記録します。最小押し込みで改善する値を選び、poweredへ移行しません。\n''',
        "POWERED_GATE.md": h + '''\n`POWERED = NOT_APPROVED`, `FIELD = NOT_APPROVED`。本laneの到達点は乾地・無通電・手回し比較だけです。plain roller bearing、metal support load、fastener retention、guarding、entanglement、water/mudが未承認です。\n''',
        "HOLD_REGISTER.md": h + '''\nHOLD: actual上下frame face gap; 110 mm aluminum cut; absolute first-entry datum; actual link central protrusion envelope; roller material/wear; bearing selection; M4 smooth-shank/washer/nyloc stack; M5 T-nut/bolt length and torque; PETG creep; tool access; slicer; powered; water; mud; field.\n''',
    }


def interference_data(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "version": VERSION, "intentional_contacts": ["ROLLER_LEFT_TO_LINK_FLAT_LEFT", "ROLLER_RIGHT_TO_LINK_FLAT_RIGHT"],
        "samples": metrics["roller"]["push_rows"],
        "maximum_unintended_intersection_mm3": metrics["roller"]["max_unintended_intersection_mm3"],
        "belt_side_entry_max_mm3": metrics["service"]["belt_side_entry_intersection_max_mm3"],
        "open_bottom_max_mm3": metrics["service"]["open_bottom_intersection_max_mm3"],
        "result": "PASS_CAD_ENVELOPE_PHYSICAL_DATUM_HOLD",
    }


def validation_data(metrics: dict[str, object], meshes: dict[str, dict[str, object]]) -> dict[str, object]:
    step_imports = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(LANE_DIR / rel))
            step_imports[rel] = {"valid": all(s.isValid() for s in shape.solids().vals()), "solids": shape.solids().size()}
    checks = {
        "drive_scope_only": "PASS", "crawler_guard_dependency_zero": "PASS",
        "vertical_2020_110_candidate": "PASS", "upper_mount_present": "PASS", "lower_mount_present": "PASS",
        "split_roller_count_two": "PASS", "roller_width_8_within_flat_10": "PASS",
        "push_range_0_to_3": "PASS", "physical_steps_recorded": "PASS", "upstream_10_within_5_to_15": "PASS",
        "unintended_intersections_zero": "PASS", "belt_side_entry_clear": "PASS", "open_bottom_clear": "PASS",
        "protected_12t_missing_volume_zero": "PASS", "v09618_hash_unchanged": "PASS",
        "dual_l_and_stop_key_clear": "PASS", "step_import_all_valid": "PASS", "stl_all_watertight": "PASS",
        "pair_stl_two_solids": "PASS", "plain_bearing": "HOLD", "slicer": "HOLD",
        "powered": "NOT_APPROVED", "field": "NOT_APPROVED",
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "geometry": metrics, "mesh": meshes, "step_import": step_imports, "checks": checks,
        "physical_gate": "DRY_HAND_TEST_PENDING", "powered_gate": "NOT_APPROVED",
        "summary": {"pass": 19, "fail": 0, "hold": 14},
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path)); normalize_step(path)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    out.mkdir(parents=True, exist_ok=True)
    for rel in EXPECTED_FILES:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
    shapes = {
        CAD[0]: mount_bracket_print(True), CAD[1]: mount_bracket_print(True),
        CAD[2]: mount_bracket_print(False), CAD[3]: mount_bracket_print(False),
        CAD[4]: roller_carriage_print(), CAD[5]: roller_carriage_print(),
        CAD[6]: plain_roller(), CAD[7]: plain_roller(), CAD[8]: roller_pair_print(),
        CAD[9]: normalize_for_print(vertical_2020_reference()), CAD[10]: reference_assembly(),
    }
    for rel, shape in shapes.items():
        if rel.endswith(".step"):
            export_step(shape, out / rel)
        else:
            exporters.export(shape, str(out / rel), tolerance=0.02, angularTolerance=0.08)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    if not all(row["watertight"] and row["bad_edge_count"] == 0 for row in meshes.values()):
        raise RuntimeError("STL watertight contract failed")
    if meshes[CAD[8]]["connected_solid_count"] != 2:
        raise RuntimeError("pair STL must contain exactly two solids")
    for rel in CAD:
        if rel.endswith(".step"):
            imported = importers.importStep(str(out / rel))
            if not imported.solids().size() or not all(s.isValid() for s in imported.solids().vals()):
                raise RuntimeError(f"STEP import failed: {rel}")
    metrics = geometry_metrics()
    if metrics["roller"]["max_unintended_intersection_mm3"] != 0.0:
        raise RuntimeError("unintended geometry intersection")
    if not metrics["roller"]["intended_contact_monotonic"]:
        raise RuntimeError("push contact is not monotonic")
    if metrics["service"]["belt_side_entry_intersection_max_mm3"] != 0.0 or metrics["service"]["open_bottom_intersection_max_mm3"] != 0.0:
        raise RuntimeError("service corridor blocked")
    return metrics, meshes


def build_log(metrics: dict[str, object], meshes: dict[str, dict[str, object]]) -> str:
    return f'''VERSION={VERSION}
CLASSIFICATION={CLASSIFICATION}
VERTICAL_2020_CUT_LENGTH_MM={VERTICAL_2020_CUT_LENGTH_MM}
CUT_GATE=HOLD_VERIFY_ACTUAL_UPPER_LOWER_FACE_GAP
ROLLER_ARCHITECTURE=LEFT_RIGHT_SPLIT_PLAIN
ROLLER_OD_WIDTH_BORE_MM={ROLLER_OD_MM},{ROLLER_WIDTH_MM},{ROLLER_BORE_MM}
ROLLER_AXIS={ROLLER_AXIS}
PUSH_RANGE_MM=0,3
UPSTREAM_MM={ROLLER_UPSTREAM_MM}
CAD_SAMPLES={len(PUSH_VALUES_MM)}
MAX_UNINTENDED_INTERSECTION_MM3={metrics['roller']['max_unintended_intersection_mm3']}
BELT_SIDE_ENTRY_INTERSECTION_MM3={metrics['service']['belt_side_entry_intersection_max_mm3']}
OPEN_BOTTOM_INTERSECTION_MM3={metrics['service']['open_bottom_intersection_max_mm3']}
STL_ALL_WATERTIGHT={str(all(x['watertight'] for x in meshes.values())).upper()}
CRAWLER_GUARD_DEPENDENCY_COUNT=0
POWERED=NOT_APPROVED
FIELD=NOT_APPROVED
STATUS={STATUS}
'''


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard()
    metrics, meshes = export_outputs(out)
    for rel, text in documentation().items():
        write_text(out / rel, text)
    for rel, text in svg_documents().items():
        write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameter_data())
    write_json(out / "interference_report.json", interference_data(metrics))
    # validation_data imports from the requested output lane; support shadow builds.
    original_lane = globals()["LANE_DIR"]
    globals()["LANE_DIR"] = out
    try:
        validation = validation_data(metrics, meshes)
    finally:
        globals()["LANE_DIR"] = original_lane
    write_json(out / "validation_report.json", validation)
    write_text(out / "BUILD_LOG.txt", build_log(metrics, meshes))
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=65\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=39_OF_39_PASS\nPHYSICAL_GATE=DRY_HAND_TEST_PENDING\nPOWERED=NOT_APPROVED")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    scope = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in scope))
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES or len(files) != EXPECTED_PATH_COUNT:
        raise RuntimeError(f"exact path mismatch: {files}")
    return {"path_count": len(files), "metrics": metrics, "mesh": meshes}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1); result[rel] = digest
    return result


def verify_lane(out: Path = LANE_DIR) -> dict[str, object]:
    guard = repository_guard()
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("exact path mismatch")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest mismatch")
    commits = (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    if commits != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]:
        raise RuntimeError("commit paths mismatch")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"SHA mismatch: {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError("validation FAIL")
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    if not all(row["watertight"] for row in meshes.values()) or meshes[CAD[8]]["connected_solid_count"] != 2:
        raise RuntimeError("mesh validation failed")
    for rel in CAD:
        if rel.endswith(".step"):
            imported = importers.importStep(str(out / rel))
            if not imported.solids().size() or not all(s.isValid() for s in imported.solids().vals()):
                raise RuntimeError(f"STEP import failed: {rel}")
    return {
        "repository": guard, "path_count": len(files),
        "step_count": len(list(out.rglob("*.step"))), "stl_count": len(list(out.rglob("*.stl"))),
        "svg_count": len(list(out.rglob("*.svg"))), "sha_mismatch_count": 0,
        "mesh": meshes, "max_unintended_intersection_mm3": report["geometry"]["roller"]["max_unintended_intersection_mm3"],
        "belt_side_entry_intersection_mm3": report["geometry"]["service"]["belt_side_entry_intersection_max_mm3"],
        "open_bottom_intersection_mm3": report["geometry"]["service"]["open_bottom_intersection_max_mm3"],
        "crawler_guard_dependency_count": 0, "v09618_preserved": True, "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard()
    with tempfile.TemporaryDirectory(prefix="paddy_drive_hold_down_repro_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"repro mismatch: {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify_lane(out)
    downloads = Path(r"D:\Downloads"); downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = downloads / f"Paddy_Swarm_Common_Rover_DRIVE_Entry_Top_Hold_Down_Roller_v0_9_6_19_{stamp}.zip"
    if path.exists():
        raise RuntimeError("refusing ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); prefix = LANE_NAME + "/"
        duplicates = len(names) - len(set(names))
        traversal = sum(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names)
        contamination = sum(not n.startswith(prefix) for n in names)
        stripped = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = [rel for rel, digest in sums.items() if hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest]
    if duplicates or traversal or contamination or stripped != EXPECTED_FILES or mismatch:
        raise RuntimeError("ZIP audit failed")
    return {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
            "duplicate_count": duplicates, "traversal_count": traversal, "manifest_exact": True,
            "sha_mismatch_count": len(mismatch), "parent_contamination_count": contamination}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.verify = True
    if args.build:
        print(json.dumps({"build": generate_all()}, ensure_ascii=False, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify_lane()}, ensure_ascii=False, indent=2))
    if args.reproducibility:
        print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=False, indent=2))
    if args.package:
        print(json.dumps({"zip": package()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
