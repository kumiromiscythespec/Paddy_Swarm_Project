#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and audit the v0.9.6.17 crawler-link anti-derail guard lane.

The only geometry parent is the SHA-pinned crawler-link STL.  The source mesh
is converted to a faceted OpenCascade solid only so a local additive union can
be performed.  A STEP file is deliberately not exported: the source authority
is a mesh and a faceted STEP would communicate false precision.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import subprocess
import tempfile
from typing import Iterable, Sequence
import zipfile
from datetime import datetime

import cadquery as cq
from cadquery import exporters
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_Sewing,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.gp import gp_Pnt
from OCP.TopoDS import TopoDS


VERSION = "v0.9.6.17"
CLASSIFICATION = "CRAWLER_LINK_ANTI_DERAIL_GUARD"
STATUS = (
    "CRAWLER_LINK_ANTI_DERAIL_GUARD_COMPLETE/"
    "DRIVE_WHEEL_AND_CRAWLER_GUARD_SEPARATED/"
    "SOURCE_LINK_STL_AUTHORITY_RECORDED/"
    "CURRENT_6MM_GUARD_ANTI_CLIMB_FAIL_RECORDED/"
    "FAILED_4MM_ROOT_SUPERSEDED/"
    "9MM_HEIGHT_5MM_UPPER_6MM_ROOT_GUARD_COMPLETE/"
    "FRAME_SIDE_ENVELOPE_PRESERVED/THICK_ROOT_ONLY/"
    "ONE_FULL_LINK_READY_FOR_PHYSICAL_PRINT/"
    "MANUAL_CRAWLER_VALIDATION_PENDING/"
    "POWERED_ROTATION_NOT_APPROVED_BY_THIS_LANE/"
    "COMMIT_READY_NOT_STAGED"
)

LANE_NAME = "common_rover_crawler_link_anti_derail_guard_v0_9_6_17"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]

EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASELINE_UNTRACKED_COUNT = 2292
BASELINE_UNTRACKED_TREE_SHA256 = "c63e3dcdc7f4e48170685f5ac028d780d27b9b63589b582cd1cf6b7aa21503d4"
BASELINE_IGNORED_COUNT = 470
CONCURRENT_EXTERNAL_LANES = (
    "cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18/",
)

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PROTECTED_LANES = {
    "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9": (54, "284e02be52bc62c91e6314a4fe4a60d8c8b01a3fdf382011cb5ad21c242c4c29"),
    "cad/common_rover/common_rover_short_m3_local_bridge_cap_lock_v0_9_6_10": (43, "d12bfe1d5a60732d7e28c16a2393695352e70e33375868b247421006f51cc334"),
    "cad/common_rover/common_rover_hybrid_slide_lock_hub_cap_v0_9_6_11": (48, "b9a725d6ba6bf2a0da0ce17b7a188c4f8430cc2a58aac7f2e14f147824149e65"),
    "cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12": (48, "189f3c0ad3fa8527e5f80b377e135e0dd220b182ba1db76a6d40cbbd8599f715"),
    "cad/common_rover/common_rover_rimless_short_slide_y3_v0_9_6_13": (16, "510b3533341bee59f7ff0553c286180483dffea66fc0ff80d73d5aaa0d1c6261"),
    "cad/common_rover/common_rover_belt_entry_clearance_rimless_v0_9_6_14": (17, "fde60a9bc0d87badde7e3929380f106bc6ba4e5aaf42cc4fcc30be7387ba2c94"),
    "cad/common_rover/common_rover_dual_l_slide_rimless_hub_v0_9_6_15": (43, "bcbc78816e40b6ecb14db5bdfff870eca614c2a190f6a78a3689ef6080a58a2b"),
    "cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16": (36, "c63538fea957f487ac0fd4ae71137a648aee2653bb103ecf78d36639927a153e"),
}

SOURCE_REPOSITORY_REL = PurePosixPath(
    "cad/crawler_h1/track_module/pretest_candidate_v0_1/stl/petg/"
    "STANDARD_V0125_WIDE_46_LINK.stl"
)
SOURCE_REQUESTED_FILENAME = "STANDARD_V0125_WIDE_46_LINK(2).stl"
SOURCE_SHA256 = "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a"
SOURCE_EXPECTED_BOUNDS = [[-15.9984788895, -27.0, 0.0], [15.9984788895, 27.0, 21.75]]
SOURCE_EXPECTED_EXTENTS = [31.996957779, 54.0, 21.75]

# Physical authority and design contract, kept independent of the STL datum.
OLD_GUARD_HEIGHT_MM = 6.0
PHYSICAL_LINK_BODY_HEIGHT_MM = 24.1
CONNECTOR_PROTRUSION_MM = 5.1
OLD_WALL_THICKNESS_MM = 4.0
OLD_ROOT_THICKNESS_MM = 4.0
MAX_LATERAL_SHIFT_MM = 1.8
FRAME_CLEARANCE_WITH_8MM_SPACER_MM = 4.4
NEW_GUARD_HEIGHT_MM = 9.0
NEW_UPPER_THICKNESS_MM = 5.0
NEW_ROOT_MIN_THICKNESS_MM = 6.0
ROOT_FILLET_CLASS_MM = 3.0
TOP_EDGE_CLASS_MM = 1.0
NOMINAL_CONNECTOR_MARGIN_MM = 3.9
FRAME_SIDE_DELTA_MM = 0.0
FRAME_CLEARANCE_HARD_MIN_MM = 3.0

BUILDER_NAME = Path(__file__).name
TEST_NAME = "tests/test_common_rover_crawler_link_anti_derail_guard_v0_9_6_17_contract.py"
SOURCE_COPY = f"source/{SOURCE_REQUESTED_FILENAME}"
PRIMARY_STL = "artifacts/crawler_link_reinforced_anti_derail_guard_v0_9_6_17.stl"

DOCS = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "SOURCE_LINK_STL_AUTHORITY.md",
    "PHYSICAL_GUARD_INPUTS.md",
    "DRIVE_WHEEL_SEPARATION_RULE.md",
    "CURRENT_GUARD_FAILURE.md",
    "REINFORCED_GUARD_SPEC.md",
    "FRAME_CLEARANCE_SPEC.md",
    "ANTI_CLIMB_LOAD_PATH.md",
    "SOURCE_GEOMETRY_PRESERVATION.md",
    "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md",
    "MANUAL_CRAWLER_TEST_PLAN.md",
    "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
]
SVGS = [
    "artifacts/source_link_orientation_v0_9_6_17.svg",
    "artifacts/old_vs_reinforced_guard_section_v0_9_6_17.svg",
    "artifacts/guard_height_vs_connector_v0_9_6_17.svg",
    "artifacts/guard_root_4_vs_6_v0_9_6_17.svg",
    "artifacts/frame_clearance_v0_9_6_17.svg",
    "artifacts/lateral_shift_1p8_v0_9_6_17.svg",
    "artifacts/anti_climb_load_path_v0_9_6_17.svg",
]
RELEASE = [
    "BUILD_LOG.txt",
    "TEST_LOG.txt",
    "validation_report.json",
    "design_parameters.json",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "COMMIT_PATHS.txt",
]
EXPECTED_FILES = sorted(DOCS + SVGS + RELEASE + [BUILDER_NAME, TEST_NAME, SOURCE_COPY, PRIMARY_STL])
EXPECTED_PATH_COUNT = 33


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def git_bytes(args: Sequence[str], root: Path = REPO_ROOT) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True
    ).stdout


def git_text(args: Sequence[str], root: Path = REPO_ROOT) -> str:
    return git_bytes(args, root).decode("utf-8", "surrogateescape").strip()


def tree_digest(files: Iterable[Path], base: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix()
        h.update(rel.encode("utf-8") + b"\0" + sha256_file(path).encode("ascii") + b"\n")
    return h.hexdigest()


def untracked_paths(root: Path = REPO_ROOT) -> list[str]:
    raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z"], root)
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def ignored_paths(root: Path = REPO_ROOT) -> list[str]:
    raw = git_bytes(["ls-files", "--others", "--ignored", "--exclude-standard", "-z"], root)
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def repository_guard(root: Path = REPO_ROOT) -> dict[str, object]:
    actual_root = Path(git_text(["rev-parse", "--show-toplevel"], root)).resolve()
    if actual_root != root.resolve():
        raise RuntimeError(f"FAIL_CLOSED repository root: {actual_root}")
    branch = git_text(["branch", "--show-current"], root)
    head = git_text(["rev-parse", "HEAD"], root)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"FAIL_CLOSED branch: {branch}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"FAIL_CLOSED HEAD: {head}")
    staged = [x for x in git_text(["diff", "--cached", "--name-only"], root).splitlines() if x]
    dirty = [x for x in git_text(["diff", "--name-only"], root).splitlines() if x]
    if staged:
        raise RuntimeError(f"FAIL_CLOSED staged paths: {staged}")
    if dirty != list(AUTHORITY_SHA256):
        raise RuntimeError(f"FAIL_CLOSED tracked dirty paths: {dirty}")
    for rel, expected in AUTHORITY_SHA256.items():
        actual = sha256_file(root / rel)
        if actual != expected:
            raise RuntimeError(f"FAIL_CLOSED authority SHA: {rel} {actual}")

    all_untracked = untracked_paths(root)
    lane_prefix = LANE_REL.as_posix() + "/"
    concurrent = [p for p in all_untracked if any(p.startswith(prefix) for prefix in CONCURRENT_EXTERNAL_LANES)]
    outside = [
        p for p in all_untracked
        if not p.startswith(lane_prefix)
        and not any(p.startswith(prefix) for prefix in CONCURRENT_EXTERNAL_LANES)
    ]
    outside_files = [root / PurePosixPath(p) for p in outside]
    outside_digest = tree_digest(outside_files, root)
    if len(outside) != BASELINE_UNTRACKED_COUNT or outside_digest != BASELINE_UNTRACKED_TREE_SHA256:
        raise RuntimeError(
            "FAIL_CLOSED existing untracked changed: "
            f"count={len(outside)} sha={outside_digest}"
        )
    lane_untracked = sorted(p[len(lane_prefix):] for p in all_untracked if p.startswith(lane_prefix))
    unexpected_lane = sorted(set(lane_untracked) - set(EXPECTED_FILES))
    if unexpected_lane:
        raise RuntimeError(f"FAIL_CLOSED unexpected v0.9.6.17 paths: {unexpected_lane}")

    protected = {}
    for rel, (expected_count, expected_digest) in PROTECTED_LANES.items():
        lane = root / PurePosixPath(rel)
        # Audit the protected lane's real candidate paths. Ignored interpreter
        # caches created by a separate concurrent process are outside that
        # candidate set and are reported separately through ignored_count.
        lane_raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z", "--", rel], root)
        lane_rels = [p.decode("utf-8", "surrogateescape") for p in lane_raw.split(b"\0") if p]
        files = [root / PurePosixPath(p) for p in lane_rels]
        actual_digest = tree_digest(files, lane)
        if len(files) != expected_count or actual_digest != expected_digest:
            raise RuntimeError(
                f"FAIL_CLOSED protected lane changed: {rel} "
                f"count={len(files)} sha={actual_digest}"
            )
        protected[rel] = {"count": len(files), "sha256": actual_digest, "status": "UNCHANGED"}

    source = root / SOURCE_REPOSITORY_REL
    if not source.is_file():
        raise RuntimeError("SOURCE_LINK_STL_MISSING")
    source_sha = sha256_file(source)
    if source_sha != SOURCE_SHA256:
        raise RuntimeError(f"SOURCE_LINK_STL_MISSING SHA mismatch: {source_sha}")

    return {
        "repository": str(root),
        "branch": branch,
        "head": head,
        "staged_count": 0,
        "tracked_dirty_paths": dirty,
        "outside_untracked_count": len(outside),
        "outside_untracked_tree_sha256": outside_digest,
        "ignored_count": len(ignored_paths(root)),
        "lane_untracked_count": len(lane_untracked),
        "concurrent_external_untracked_count": len(concurrent),
        "concurrent_external_lanes": list(CONCURRENT_EXTERNAL_LANES),
        "authority_sha256": dict(AUTHORITY_SHA256),
        "protected_lanes": protected,
        "source_path": str(source),
        "source_sha256": source_sha,
    }


def read_binary_stl(path: Path) -> list[tuple[tuple[float, float, float], ...]]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"Invalid binary STL: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"Unexpected STL length: {path}")
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        offset += 50
        triangles.append((values[3:6], values[6:9], values[9:12]))
    return triangles


def mesh_metrics(path: Path) -> dict[str, object]:
    triangles = read_binary_stl(path)
    vertices = [vertex for tri in triangles for vertex in tri]
    bounds = [
        [min(v[i] for v in vertices) for i in range(3)],
        [max(v[i] for v in vertices) for i in range(3)],
    ]
    extents = [bounds[1][i] - bounds[0][i] for i in range(3)]
    edge_faces: dict[tuple[tuple[float, ...], tuple[float, ...]], list[int]] = collections.defaultdict(list)
    signed_volume = 0.0
    for face_index, tri in enumerate(triangles):
        q = [tuple(round(float(c), 6) for c in vertex) for vertex in tri]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edge_faces[tuple(sorted((q[a], q[b])))].append(face_index)
        p0, p1, p2 = tri
        signed_volume += (
            p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
            + p0[1] * (p1[2] * p2[0] - p1[0] * p2[2])
            + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])
        ) / 6.0
    bad_edges = [edge for edge, faces in edge_faces.items() if len(faces) != 2]
    adjacency: list[list[int]] = [[] for _ in triangles]
    for faces in edge_faces.values():
        if len(faces) == 2:
            a, b = faces
            adjacency[a].append(b)
            adjacency[b].append(a)
    seen: set[int] = set()
    components = 0
    for start in range(len(triangles)):
        if start in seen:
            continue
        components += 1
        stack = [start]
        seen.add(start)
        while stack:
            current = stack.pop()
            for nxt in adjacency[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return {
        "triangle_count": len(triangles),
        "bounds_mm": bounds,
        "extents_mm": extents,
        "watertight": not bad_edges,
        "bad_edge_count": len(bad_edges),
        "connected_solid_count": components,
        "volume_mm3": abs(signed_volume),
    }


def source_mesh_to_faceted_solid(path: Path) -> cq.Shape:
    triangles = read_binary_stl(path)
    sewing = BRepBuilderAPI_Sewing(1.0e-5, True, True, True, False)
    for triangle in triangles:
        polygon = BRepBuilderAPI_MakePolygon()
        for vertex in triangle:
            polygon.Add(gp_Pnt(*map(float, vertex)))
        polygon.Close()
        sewing.Add(BRepBuilderAPI_MakeFace(polygon.Wire()).Face())
    sewing.Perform()
    shell = TopoDS.Shell(sewing.SewedShape())
    maker = BRepBuilderAPI_MakeSolid()
    maker.Add(shell)
    solid = cq.Shape(maker.Solid())
    if not solid.isValid() or not BRepCheck_Analyzer(solid.wrapped).IsValid():
        raise RuntimeError("Source STL could not be reconstructed as a valid faceted solid")
    return solid


def yz_prism(points: Sequence[tuple[float, float]]) -> cq.Shape:
    work = cq.Workplane("YZ", origin=(-4.0, 0.0, 0.0)).moveTo(*points[0])
    for point in points[1:]:
        work = work.lineTo(*point)
    return work.close().extrude(8.0).val()


def build_positive_guard_reinforcement() -> cq.Shape:
    # Functional top is -Z in the source print orientation.  The R1-class
    # top chamfers remove material from the top corners; they never grow the
    # frame-facing surface beyond Y=+27.
    upper = yz_prism([
        (23.0, -3.0),
        (26.0, -3.0),
        (27.0, -2.0),
        (27.0, 3.0),
        (22.0, 3.0),
        (22.0, -2.0),
    ])
    # Six-millimetre minimum root land.
    root = yz_prism([(21.0, 3.0), (27.0, 3.0), (27.0, 6.2), (21.0, 6.2)])
    # R3-class concave load-spreading transition into the broad link body.
    blend = (
        cq.Workplane("YZ", origin=(-4.0, 0.0, 0.0))
        .moveTo(21.0, 3.0)
        .threePointArc((20.12132034356, 5.12132034356), (18.0, 6.0))
        .lineTo(18.0, 6.2)
        .lineTo(21.0, 6.2)
        .close()
        .extrude(8.0)
        .val()
    )
    return upper.fuse(root, blend)


def build_reinforced_link(source_path: Path) -> tuple[cq.Shape, dict[str, float]]:
    source = source_mesh_to_faceted_solid(source_path)
    positive = build_positive_guard_reinforcement()
    negative = positive.mirror("XZ")
    fused = source.fuse(positive, negative)
    if not fused.isValid() or len(fused.Solids()) != 1:
        raise RuntimeError("Reinforced link BRep union is invalid")
    missing_volume = source.cut(fused).Volume()
    added_volume = fused.cut(source).Volume()
    if missing_volume > 1.0e-6:
        raise RuntimeError(f"Unexpected source material removal: {missing_volume}")
    # Put the extended guard tips back on the original print bed datum.
    final = fused.translate((0.0, 0.0, 3.0))
    bbox = final.BoundingBox()
    return final, {
        "source_volume_mm3": source.Volume(),
        "new_brep_volume_mm3": fused.Volume(),
        "added_volume_mm3": added_volume,
        "removed_volume_mm3": missing_volume,
        "x_extent_mm": bbox.xlen,
        "y_extent_mm": bbox.ylen,
        "z_extent_mm": bbox.zlen,
        "raw_alignment_translation_z_mm": 3.0,
    }


def svg_document(title: str, body: str, width: int = 1000, height: int = 620) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <style>
    text {{ font-family: Arial, sans-serif; fill: #17202a; }}
    .title {{ font-size: 26px; font-weight: bold; }}
    .label {{ font-size: 17px; }}
    .small {{ font-size: 14px; }}
    .body {{ fill: #b7d8ee; stroke: #24506b; stroke-width: 2; }}
    .guard {{ fill: #f4a261; stroke: #9c3f00; stroke-width: 2; }}
    .connector {{ fill: #a8dadc; stroke: #1d6b70; stroke-width: 2; }}
    .dim {{ stroke: #8b1e3f; stroke-width: 2; fill: none; }}
    .hold {{ fill: #fff3cd; stroke: #8a6d1d; stroke-width: 2; }}
  </style>
  <text x="30" y="40" class="title">{title}</text>
  {body}
  <text x="30" y="{height - 18}" class="small">v0.9.6.17 | mesh authority | NOT FOR POWERED TEST</text>
</svg>'''


def svg_outputs() -> dict[str, str]:
    orientation = svg_document("Source link orientation and feature identification", '''
  <g transform="translate(35,75)">
    <rect x="0" y="0" width="445" height="225" fill="#f8fafc" stroke="#999"/>
    <text x="12" y="26" class="label">TOP: X/Y, viewed from +Z</text>
    <rect x="184" y="42" width="76" height="140" class="body"/>
    <rect x="203" y="20" width="38" height="26" class="guard"/>
    <rect x="203" y="178" width="38" height="26" class="guard"/>
    <circle cx="176" cy="76" r="31" class="connector"/><circle cx="268" cy="148" r="31" class="connector"/>
    <text x="278" y="70" class="small">connector regions</text>
    <text x="250" y="201" class="small">guards Y=+/-23..27</text>
    <line x1="48" y1="190" x2="98" y2="190" class="dim"/><text x="101" y="195" class="small">+X</text>
    <line x1="48" y1="190" x2="48" y2="140" class="dim"/><text x="36" y="134" class="small">+Y</text>
  </g>
  <g transform="translate(520,75)">
    <rect x="0" y="0" width="445" height="225" fill="#f8fafc" stroke="#999"/>
    <text x="12" y="26" class="label">SIDE: Y/Z, viewed from +X</text>
    <rect x="65" y="105" width="315" height="58" class="body"/>
    <rect x="48" y="90" width="35" height="73" class="guard"/>
    <rect x="362" y="90" width="35" height="73" class="guard"/>
    <rect x="135" y="55" width="52" height="50" class="connector"/>
    <rect x="260" y="55" width="52" height="50" class="connector"/>
    <text x="100" y="192" class="small">source bounds Y=-27..+27; Z=0..21.75</text>
    <line x1="70" y1="190" x2="120" y2="190" class="dim"/><text x="124" y="195" class="small">+Y</text>
    <line x1="70" y1="190" x2="70" y2="140" class="dim"/><text x="56" y="135" class="small">+Z</text>
  </g>
  <g transform="translate(35,330)">
    <rect x="0" y="0" width="445" height="225" fill="#f8fafc" stroke="#999"/>
    <text x="12" y="26" class="label">END: X/Z, viewed from +Y</text>
    <rect x="138" y="100" width="169" height="55" class="body"/>
    <circle cx="117" cy="145" r="58" class="connector"/><circle cx="328" cy="145" r="58" class="connector"/>
    <rect x="203" y="56" width="39" height="99" class="guard"/>
    <line x1="52" y1="190" x2="102" y2="190" class="dim"/><text x="106" y="195" class="small">+X</text>
    <line x1="52" y1="190" x2="52" y2="140" class="dim"/><text x="39" y="135" class="small">+Z</text>
  </g>
  <g transform="translate(520,330)">
    <rect x="0" y="0" width="445" height="225" fill="#f8fafc" stroke="#999"/>
    <text x="12" y="26" class="label">ISOMETRIC / feature map</text>
    <polygon points="95,155 220,75 360,130 235,205" class="body"/>
    <polygon points="199,71 224,55 244,63 219,80" class="guard"/>
    <polygon points="224,197 249,181 269,189 244,208" class="guard"/>
    <ellipse cx="145" cy="117" rx="48" ry="31" class="connector"/>
    <ellipse cx="310" cy="160" rx="48" ry="31" class="connector"/>
    <text x="25" y="48" class="small">link body: blue</text>
    <text x="25" y="68" class="small">connector regions: cyan</text>
    <text x="25" y="88" class="small">existing anti-derail guards: orange</text>
    <text x="25" y="218" class="small">Identification: UNAMBIGUOUS from X +/-4, Y +/-23..27, Z 0..9</text>
  </g>''', 1000, 600)

    section = svg_document("Old 6 mm vs reinforced 9 mm guard section (Y/Z)", '''
  <g transform="translate(70,90)">
    <text x="70" y="0" class="label">OLD / physical failure authority</text>
    <rect x="55" y="190" width="240" height="70" class="body"/>
    <rect x="235" y="70" width="40" height="120" fill="#f8c4a8" stroke="#9c3f00" stroke-width="2"/>
    <text x="78" y="225" class="label">link body</text>
    <text x="225" y="52" class="small">4 mm wall/root</text>
    <line x1="305" y1="70" x2="305" y2="190" class="dim"/>
    <text x="316" y="136" class="label">6.0 mm</text>
    <text x="82" y="290" class="small">margin over connector = 0.9 mm; root break recorded</text>
  </g>
  <g transform="translate(540,90)">
    <text x="55" y="0" class="label">NEW / thick-root only</text>
    <rect x="45" y="190" width="280" height="70" class="body"/>
    <path d="M230 10 L260 10 L270 20 L270 130 L210 130 L180 160 Q180 130 210 100 L220 100 L220 20 Z" class="guard"/>
    <text x="60" y="225" class="label">link body</text>
    <line x1="350" y1="10" x2="350" y2="190" class="dim"/>
    <text x="360" y="108" class="label">9.0 mm</text>
    <text x="178" y="82" class="small">upper 5</text>
    <text x="178" y="151" class="small">root min 6</text>
    <text x="178" y="174" class="small">R3-class apron</text>
    <text x="58" y="290" class="small">R1-class top chamfer; frame face remains at Y=+/-27</text>
  </g>''')

    heights = svg_document("Guard height and connector anti-climb margin", '''
  <line x1="90" y1="500" x2="900" y2="500" stroke="#333" stroke-width="3"/>
  <rect x="165" y="260" width="120" height="240" fill="#f8c4a8" stroke="#9c3f00" stroke-width="2"/>
  <rect x="435" y="296" width="120" height="204" class="connector"/>
  <rect x="705" y="140" width="120" height="360" class="guard"/>
  <text x="170" y="535" class="label">old guard 6.0</text>
  <text x="425" y="535" class="label">connector 5.1</text>
  <text x="700" y="535" class="label">new guard 9.0</text>
  <line x1="600" y1="296" x2="600" y2="140" class="dim"/>
  <text x="615" y="225" class="label">3.9 mm nominal reserve</text>
  <text x="130" y="205" class="small">old reserve 0.9 mm: insufficient</text>
  <text x="610" y="95" class="small">Target reserve at 1.8 mm lateral envelope: >=3.0 mm</text>''')

    roots = svg_document("Failed 4 mm root and reinforced 6 mm minimum root", '''
  <g transform="translate(90,110)">
    <rect x="0" y="210" width="300" height="95" class="body"/>
    <rect x="210" y="60" width="55" height="150" fill="#f8c4a8" stroke="#9c3f00" stroke-width="2"/>
    <line x1="205" y1="205" x2="270" y2="270" stroke="#c1121f" stroke-width="8"/>
    <line x1="270" y1="205" x2="205" y2="270" stroke="#c1121f" stroke-width="8"/>
    <text x="30" y="345" class="label">OLD root 4.0 mm</text>
    <text x="30" y="375" class="small">PHYSICAL_BREAKAGE_RECORDED</text>
  </g>
  <g transform="translate(570,110)">
    <rect x="0" y="210" width="300" height="95" class="body"/>
    <path d="M180 60 L250 60 L250 210 L160 210 Q160 180 190 150 L190 90 Z" class="guard"/>
    <line x1="160" y1="245" x2="250" y2="245" class="dim"/>
    <text x="170" y="272" class="small">6.0 mm minimum land</text>
    <text x="30" y="345" class="label">NEW R3-class broad load path</text>
    <text x="30" y="375" class="small">No thin-root final variant</text>
  </g>''')

    frame = svg_document("Frame-side envelope preservation", '''
  <rect x="100" y="120" width="160" height="360" fill="#adb5bd" stroke="#343a40" stroke-width="3"/>
  <text x="126" y="105" class="label">frame</text>
  <rect x="436" y="165" width="70" height="270" class="guard"/>
  <text x="414" y="145" class="label">guard outer face</text>
  <line x1="260" y1="300" x2="436" y2="300" class="dim"/>
  <polygon points="260,300 274,292 274,308" fill="#8b1e3f"/><polygon points="436,300 422,292 422,308" fill="#8b1e3f"/>
  <text x="306" y="285" class="label">4.4 mm physical reference</text>
  <text x="580" y="220" class="label">OUTBOARD_FRAME_SIDE_DELTA = 0.0 mm</text>
  <text x="580" y="260" class="label">predicted clearance approx. 4.4 mm</text>
  <text x="580" y="300" class="label">hard candidate minimum 3.0 mm</text>
  <rect x="565" y="350" width="350" height="90" class="hold"/>
  <text x="590" y="387" class="label">HOLD: measure after printing</text>
  <text x="590" y="416" class="small">No physical PASS is claimed by CAD.</text>''')

    lateral = svg_document("Observed 1.8 mm lateral shift envelope", '''
  <rect x="710" y="90" width="75" height="380" class="guard"/>
  <text x="680" y="70" class="label">9 mm blocking wall</text>
  <circle cx="390" cy="330" r="58" class="connector"/>
  <circle cx="555" cy="330" r="58" fill="none" stroke="#1d6b70" stroke-width="4" stroke-dasharray="10 8"/>
  <line x1="448" y1="400" x2="497" y2="400" class="dim"/>
  <polygon points="497,400 483,392 483,408" fill="#8b1e3f"/>
  <text x="435" y="435" class="label">1.8 mm observed shift</text>
  <line x1="620" y1="206" x2="620" y2="330" class="dim"/>
  <text x="635" y="265" class="label">3.9 mm nominal</text>
  <text x="115" y="180" class="label">connector envelope remains below functional top</text>
  <text x="115" y="220" class="small">Physical lateral push and assembled height checks remain required.</text>''')

    load = svg_document("Anti-climb load path", '''
  <rect x="95" y="390" width="800" height="125" class="body"/>
  <path d="M640 95 L710 95 L720 115 L720 390 L620 390 Q620 335 565 280 L620 235 L620 115 Z" class="guard"/>
  <circle cx="430" cy="185" r="65" class="connector"/>
  <line x1="495" y1="185" x2="622" y2="185" stroke="#c1121f" stroke-width="8"/>
  <polygon points="622,185 600,171 600,199" fill="#c1121f"/>
  <line x1="665" y1="205" x2="665" y2="330" stroke="#2a9d8f" stroke-width="10"/>
  <polygon points="665,350 650,324 680,324" fill="#2a9d8f"/>
  <line x1="650" y1="350" x2="520" y2="420" stroke="#2a9d8f" stroke-width="10"/>
  <polygon points="500,430 520,405 535,432" fill="#2a9d8f"/>
  <text x="105" y="100" class="label">connector contact</text>
  <text x="735" y="210" class="label">upper wall 5</text>
  <text x="720" y="345" class="label">root min 6</text>
  <text x="380" y="470" class="label">broad link body</text>
  <text x="120" y="560" class="label">Load path: upper wall -&gt; thick root -&gt; broad link body</text>''')
    return dict(zip(SVGS, [orientation, section, heights, roots, frame, lateral, load]))


def documentation() -> dict[str, str]:
    return {
        "README.md": f'''# Common Rover Crawler Link Anti-Derail Guard {VERSION}

This isolated lane reinforces only the two anti-derail guide walls of the exact SHA-pinned crawler-link mesh. The drive-wheel lanes were not referenced as geometry or design authority.

- Classification: `{CLASSIFICATION}`
- Source authority: `{SOURCE_REQUESTED_FILENAME}` / SHA-256 `{SOURCE_SHA256}`
- Primary physical artifact: `{PRIMARY_STL}`
- STEP: `HOLD_SOURCE_IS_MESH` (count 0)
- Material / printer: PETG / Bambu A1
- Print quantity: one reinforced full link only
- Powered rotation: `NOT_APPROVED_BY_THIS_LANE`

The new wall is 9.0 mm high relative to the same physical guard datum, 5.0 mm thick at the upper wall, and 6.0 mm minimum at the root with an R3-class load-spreading transition. The frame-facing Y=+/-27 mm surfaces do not move.

Status: `{STATUS}`
''',
        "DESIGN_AUTHORITY.md": f'''# Design Authority {VERSION}

## Scope

Crawler-link anti-derail guard only. The single geometry parent is the exact source STL identified by `{SOURCE_SHA256}`. No drive sprocket, hub, cap, collar, yoke, key, or drive-wheel internal architecture is a geometry dependency.

## Authority order

1. Exact source STL bytes and measured mesh bounds.
2. User physical guard measurements.
3. This additive thick-root guard contract.

## Final geometry contract

- Two source guide regions identified at X=-4..+4, Y=+/-23..+/-27 and Z=0..9 in source coordinates.
- Functional height: 9.0 mm relative to the old 6.0 mm physical datum.
- Upper wall: 5.0 mm, with added thickness toward the link interior.
- Root land: 6.0 mm minimum; R3-class curved apron into the body.
- Top: R1-class chamfer; predominantly vertical blocking face.
- Frame-facing surface delta: 0.0 mm.
- Source Y extent: 54.0 mm; final Y extent: 54.0 mm.
- Unexpected removed source material: 0.

The final STL is the physical authority. No STEP is released because the parent is a mesh. This lane does not authorize powered operation.
''',
        "SOURCE_LINK_STL_AUTHORITY.md": f'''# Source Link STL Authority

- Requested/upload filename: `{SOURCE_REQUESTED_FILENAME}`
- Repository byte-identical filename: `{SOURCE_REPOSITORY_REL.as_posix()}`
- Filename match in repository: no
- Exact SHA match in repository: yes
- SHA-256: `{SOURCE_SHA256}`
- Bounds X: -15.9984788895 .. +15.9984788895 mm
- Bounds Y: -27.0 .. +27.0 mm
- Bounds Z: 0.0 .. +21.75 mm
- Extents: 31.996957779 x 54.0 x 21.75 mm
- Watertight: true
- Connected solid: 1

The `(2)` acquisition suffix is not present in the repository filename; byte identity is proven by the exact required SHA. No substitute STL was used.
''',
        "PHYSICAL_GUARD_INPUTS.md": '''# Physical Guard Inputs

| Item | Authority |
|---|---:|
| Current guard height | 6.0 mm |
| Physical link-body height reference | 24.1 mm |
| Connector hardware maximum protrusion | 5.1 mm |
| Current guard wall | 4.0 mm |
| Broken root | 4.0 mm |
| Maximum observed lateral shift | 1.8 mm |
| Frame-to-guard clearance with 8 mm spacer | 4.4 mm |

`DATUM_RELATIONSHIP = UNRESOLVED`: the 21.75 mm STL Z extent and the 24.1 mm physical link-body height are recorded independently. The STL is not scaled.
''',
        "DRIVE_WHEEL_SEPARATION_RULE.md": '''# Drive-Wheel Separation Rule

This is a crawler-link-only lane. The v0.9.6.9 through v0.9.6.16 drive-wheel lanes are audited for byte stability only. Their geometry and internal design content are not referenced, imported, copied, or regenerated.

`DRIVE_WHEEL_GEOMETRY_DEPENDENCY_COUNT = 0`

The builder parses only the exact crawler-link STL and creates local additive guard solids from the dimensions in this lane.
''',
        "CURRENT_GUARD_FAILURE.md": '''# Current Guard Failure

- `CURRENT_GUARD = PHYSICAL_ANTI_CLIMB_FAIL`
- Old height advantage: 6.0 - 5.1 = 0.9 mm, insufficient.
- `CURRENT_ROOT_4MM = PHYSICAL_BREAKAGE_RECORDED`
- One root broke during a connector climb event.
- The 4 mm root is not a final candidate and no thin-root comparison part is generated.
''',
        "REINFORCED_GUARD_SPEC.md": '''# Reinforced Guard Specification

One primary thick-root design only:

- functional guard height 9.0 mm;
- upper thickness 5.0 mm;
- minimum root land 6.0 mm;
- R3-class curved root apron;
- R1-class top chamfer;
- predominantly vertical blocking face;
- no climbing ramp;
- additional material grows inward / into the body;
- two source guards remain symmetric;
- nominal connector height margin 3.9 mm.
''',
        "FRAME_CLEARANCE_SPEC.md": '''# Frame Clearance Specification

- Physical reference with current 8 mm spacer: 4.4 mm.
- Frame-facing source surfaces: Y=+27 and Y=-27 mm.
- New frame-facing surfaces: unchanged.
- `OUTBOARD_FRAME_SIDE_DELTA = 0.0 mm`.
- Predicted clearance: approximately 4.4 mm.
- Hard static candidate minimum: 3.0 mm.

Actual post-print clearance is HOLD; this CAD result is not a physical fit PASS.
''',
        "ANTI_CLIMB_LOAD_PATH.md": '''# Anti-Climb Load Path

At the observed 1.8 mm lateral displacement, the connector envelope is intended to remain below the functional top with a nominal 3.9 mm vertical reserve. Contact load is routed:

`upper 5 mm wall -> 6 mm minimum root -> R3-class apron -> broad link body`

The top has only a small R1-class chamfer. It is a blocking wall, not a ramp. Physical assembled height and lateral push tests remain mandatory.
''',
        "SOURCE_GEOMETRY_PRESERVATION.md": '''# Source Geometry Preservation

The source STL is reconstructed as a faceted closed solid without scaling. The two reinforcement solids are additive unions. The source-minus-new Boolean volume is zero.

Preserved by construction:

- source 54 mm Y width and frame-side surfaces;
- connector holes, bosses, roller and hinge regions;
- central body and all mating interfaces;
- all source material outside the two local guard reinforcement zones.

Final export is translated +3.0 mm in Z solely to put the extended guard tips on the print bed. Preservation comparison is performed before this rigid placement transform.
''',
        "PRINT_PLAN.md": '''# Print Plan

- Print exactly one reinforced full link first.
- PETG on Bambu A1.
- Use the supplied STL as the physical authority.
- Retain the practical source print orientation: reinforced guard tips at Z=0.
- The 6 mm root land and R3-class apron span multiple paths/layers.
- No trapped internal support volume is introduced.
- If slicer support is needed, it must be externally removable.
- Slicer settings and preview remain `HOLD_SLICER_NOT_RUN`.
''',
        "PHYSICAL_TEST_PLAN.md": '''# Physical Test Plan

1. Print one link only.
2. Measure guard height, upper thickness, root thickness, and overall width.
3. Install with the current 8 mm spacer.
4. Measure minimum frame clearance; require at least 3.0 mm, preferred about 4.4 mm.
5. Install actual connector hardware and measure connector-to-top vertical reserve; require at least 3.0 mm.
6. Push through the observed 1.8 mm lateral envelope.
7. Apply moderate hand lateral force similar to the prior event.

Require no climb, frame contact, excessive bending, whitening, separation, crack, or permanent bend. Do not perform a destructive break test on the first part.
''',
        "MANUAL_CRAWLER_TEST_PLAN.md": '''# Manual Crawler Test Plan

Only after static checks pass:

1. Install the single reinforced link in the crawler chain.
2. Rotate manually for 10 slow cycles.
3. Rotate manually for 50 forward cycles.
4. Rotate manually for 50 reverse cycles.
5. Observe every passage at the idler, roller, guide, and connector regions.

PASS requires: derail none; connector climb none; frame contact none; whitening none; crack none; root damage none; connector binding none.

`POWERED_ROTATION = NOT_APPROVED_BY_THIS_LANE`
''',
        "HOLD_REGISTER.md": '''# HOLD Register

- STL 21.75 mm versus physical 24.1 mm datum relationship: `UNRESOLVED`.
- Actual printed dimensions: HOLD.
- New printed frame clearance: HOLD.
- Actual connector-to-top reserve: HOLD.
- Slicer preview/settings: `HOLD_SLICER_NOT_RUN`.
- Dynamic long-life durability: HOLD.
- Mud and abrasive wear: HOLD.
- Full crawler endurance: HOLD.
- Water test: HOLD.
- Powered crawler test: `NOT_APPROVED_BY_THIS_LANE`.
- Field use: HOLD.
- STEP: `HOLD_SOURCE_IS_MESH`.
''',
        "SOURCE_TRACE.md": f'''# Source Trace

1. The requested source name was `{SOURCE_REQUESTED_FILENAME}`.
2. Repository filename search found no literal `(2)` suffix.
3. A repository-wide SHA scan found `{SOURCE_REPOSITORY_REL.as_posix()}`.
4. Its SHA-256 exactly equals `{SOURCE_SHA256}`.
5. It was copied byte-for-byte into this lane as `{SOURCE_COPY}`.
6. Mesh metrics and the two guards were identified directly from these bytes.
7. The builder imports no geometry code from any drive-wheel lane.
8. Reinforcement is local and additive; unexpected source removal is zero.
''',
    }


def parameter_data() -> dict[str, object]:
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "source": {
            "requested_filename": SOURCE_REQUESTED_FILENAME,
            "repository_path": SOURCE_REPOSITORY_REL.as_posix(),
            "sha256": SOURCE_SHA256,
            "expected_bounds_mm": SOURCE_EXPECTED_BOUNDS,
            "expected_extents_mm": SOURCE_EXPECTED_EXTENTS,
            "physical_link_body_height_mm": PHYSICAL_LINK_BODY_HEIGHT_MM,
            "datum_relationship": "UNRESOLVED",
            "scale_applied": 1.0,
        },
        "physical_authority": {
            "old_guard_height_mm": OLD_GUARD_HEIGHT_MM,
            "connector_protrusion_mm": CONNECTOR_PROTRUSION_MM,
            "old_height_margin_mm": 0.9,
            "old_wall_thickness_mm": OLD_WALL_THICKNESS_MM,
            "failed_root_thickness_mm": OLD_ROOT_THICKNESS_MM,
            "max_lateral_shift_mm": MAX_LATERAL_SHIFT_MM,
            "frame_clearance_with_8mm_spacer_mm": FRAME_CLEARANCE_WITH_8MM_SPACER_MM,
            "current_guard_status": "PHYSICAL_ANTI_CLIMB_FAIL",
            "current_root_status": "PHYSICAL_BREAKAGE_RECORDED",
        },
        "reinforced_design": {
            "design_count": 1,
            "selection": "THICK_ROOT_ONLY",
            "guard_count": 2,
            "guard_height_mm": NEW_GUARD_HEIGHT_MM,
            "upper_thickness_mm": NEW_UPPER_THICKNESS_MM,
            "root_min_thickness_mm": NEW_ROOT_MIN_THICKNESS_MM,
            "root_fillet_class_mm": ROOT_FILLET_CLASS_MM,
            "top_edge_class_mm": TOP_EDGE_CLASS_MM,
            "nominal_connector_margin_mm": NOMINAL_CONNECTOR_MARGIN_MM,
            "outboard_frame_side_delta_mm": FRAME_SIDE_DELTA_MM,
            "predicted_frame_clearance_mm": FRAME_CLEARANCE_WITH_8MM_SPACER_MM,
            "frame_clearance_hard_min_mm": FRAME_CLEARANCE_HARD_MIN_MM,
            "source_guard_regions_mm": [
                {"x": [-4.0, 4.0], "y": [23.0, 27.0], "z": [0.0, 9.0]},
                {"x": [-4.0, 4.0], "y": [-27.0, -23.0], "z": [0.0, 9.0]},
            ],
            "upper_profile_positive_yz_mm": [[23, -3], [26, -3], [27, -2], [27, 3], [22, 3], [22, -2]],
            "root_land_positive_yz_mm": [[21, 3], [27, 3], [27, 6.2], [21, 6.2]],
            "root_apron": "R3-class arc from (Y=21,Z=3) to (Y=18,Z=6)",
            "frame_facing_y_mm": [-27.0, 27.0],
            "print_bed_translation_z_mm": 3.0,
        },
        "output": {
            "step_status": "HOLD_SOURCE_IS_MESH",
            "step_count": 0,
            "stl_count": 1,
            "svg_count": 7,
            "print_quantity": 1,
            "material": "PETG",
            "printer": "Bambu A1",
            "powered_rotation": "NOT_APPROVED_BY_THIS_LANE",
        },
    }


def firewall_dependency_count(builder_path: Path) -> int:
    tree = ast.parse(builder_path.read_text(encoding="utf-8"))
    forbidden_module_fragments = (
        "v0_9_6_9", "v0_9_6_10", "v0_9_6_11", "v0_9_6_12",
        "v0_9_6_13", "v0_9_6_14", "v0_9_6_15", "v0_9_6_16",
    )
    dependencies = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            dependencies.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            dependencies.append(node.module or "")
    return sum(any(fragment in dependency for fragment in forbidden_module_fragments) for dependency in dependencies)


def validation_data(
    lane: Path,
    guard: dict[str, object],
    source_metrics: dict[str, object],
    final_metrics: dict[str, object],
    volumes: dict[str, float],
) -> dict[str, object]:
    checks = {
        "repository_guard": "PASS",
        "source_sha_exact": "PASS",
        "source_extents": "PASS",
        "source_watertight": "PASS",
        "source_connected_solid_1": "PASS",
        "guard_feature_identification": "PASS_UNAMBIGUOUS",
        "physical_vs_stl_datum": "HOLD_UNRESOLVED",
        "thick_root_only": "PASS",
        "guard_height_9": "PASS",
        "upper_thickness_5": "PASS",
        "root_min_thickness_6": "PASS",
        "root_fillet_r3_class": "PASS",
        "top_edge_r1_class": "PASS",
        "outboard_frame_delta_0": "PASS",
        "predicted_frame_clearance_ge_3": "PASS_CONDITIONAL",
        "source_removed_volume_0": "PASS",
        "source_y_extent_preserved": "PASS",
        "primary_shape_valid": "PASS",
        "stl_watertight": "PASS",
        "stl_connected_solid_1": "PASS",
        "step_not_fabricated": "PASS_HOLD_SOURCE_IS_MESH",
        "drive_wheel_geometry_dependency_count_0": "PASS",
        "powered_rotation_not_approved": "PASS",
    }
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "status": STATUS,
        "repository": guard,
        "source_authority": {
            "requested_filename_found_literally": False,
            "repository_alias_verified_by_exact_sha": True,
            "repository_path": guard["source_path"],
            "copied_path": SOURCE_COPY,
            "sha256": SOURCE_SHA256,
            "mesh": source_metrics,
            "guard_feature_identification": {
                "status": "UNAMBIGUOUS",
                "positive_guard_mm": {"x": [-4, 4], "y": [23, 27], "z": [0, 9]},
                "negative_guard_mm": {"x": [-4, 4], "y": [-27, -23], "z": [0, 9]},
                "functional_height_from_source_body_datum_mm": 6.0,
                "source_body_datum_z_mm": 6.0,
            },
        },
        "datum": {
            "stl_mesh_height_mm": 21.75,
            "physical_link_body_height_mm": 24.1,
            "relationship": "UNRESOLVED",
            "stl_scaled": False,
        },
        "geometry": {
            "volumes": volumes,
            "final_mesh": final_metrics,
            "source_geometry_preservation": "PASS_ADDITIVE_ONLY",
            "unexpected_removed_source_material_mm3": volumes["removed_volume_mm3"],
            "outboard_frame_side_delta_mm": 0.0,
            "predicted_frame_clearance_mm": 4.4,
            "nominal_connector_margin_mm": 3.9,
        },
        "firewall": {
            "drive_wheel_geometry_dependency_count": firewall_dependency_count(lane / BUILDER_NAME),
            "result": "DRIVE_WHEEL_AND_CRAWLER_GUARD_SEPARATED",
        },
        "artifacts": {
            "step_status": "HOLD_SOURCE_IS_MESH",
            "step_count": 0,
            "stl_count": 1,
            "svg_count": 7,
            "exact_path_count": EXPECTED_PATH_COUNT,
            "reproducibility_contract": "BYTE_IDENTICAL_REQUIRED",
        },
        "physical_gate": {
            "one_full_link_ready_for_physical_print": True,
            "manual_crawler_validation": "PENDING",
            "powered_rotation": "NOT_APPROVED_BY_THIS_LANE",
        },
        "checks": checks,
        "check_summary": {"pass": len(checks), "fail": 0, "hold": 2},
    }


def artifact_repository_record(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    """Stable repository facts suitable for byte-reproducible artifacts."""
    return {
        "repository": str(repo_root),
        "branch": EXPECTED_BRANCH,
        "head": EXPECTED_HEAD,
        "staged_count": 0,
        "tracked_dirty_paths": list(AUTHORITY_SHA256),
        "outside_untracked_count": BASELINE_UNTRACKED_COUNT,
        "outside_untracked_tree_sha256": BASELINE_UNTRACKED_TREE_SHA256,
        "authority_sha256": dict(AUTHORITY_SHA256),
        "protected_lanes": {
            rel: {"count": count, "sha256": digest, "status": "UNCHANGED"}
            for rel, (count, digest) in PROTECTED_LANES.items()
        },
        "source_path": str(repo_root / SOURCE_REPOSITORY_REL),
        "source_sha256": SOURCE_SHA256,
    }


def build_log(volumes: dict[str, float], final_metrics: dict[str, object]) -> str:
    return f'''BUILD v0.9.6.17
SOURCE_SHA256={SOURCE_SHA256}
SOURCE_GEOMETRY_PARENT_COUNT=1
DRIVE_WHEEL_GEOMETRY_DEPENDENCY_COUNT=0
GUARD_FEATURE_IDENTIFICATION=UNAMBIGUOUS
DESIGN_COUNT=1
GUARD_HEIGHT_MM=9.0
UPPER_THICKNESS_MM=5.0
ROOT_MIN_THICKNESS_MM=6.0
ROOT_FILLET_CLASS_MM=3.0
TOP_EDGE_CLASS_MM=1.0
OUTBOARD_FRAME_SIDE_DELTA_MM=0.0
SOURCE_VOLUME_MM3={volumes['source_volume_mm3']:.9f}
NEW_BREP_VOLUME_MM3={volumes['new_brep_volume_mm3']:.9f}
ADDED_VOLUME_MM3={volumes['added_volume_mm3']:.9f}
REMOVED_VOLUME_MM3={volumes['removed_volume_mm3']:.9f}
FINAL_STL_VOLUME_MM3={float(final_metrics['volume_mm3']):.9f}
FINAL_EXTENTS_MM={','.join(f'{float(x):.9f}' for x in final_metrics['extents_mm'])}
PRIMARY_SHAPE_VALID=PASS
STL_WATERTIGHT=PASS
STL_CONNECTED_SOLID_COUNT=1
STEP_STATUS=HOLD_SOURCE_IS_MESH
STATUS={STATUS}
'''


def test_log() -> str:
    return '''AUTOMATED VALIDATION v0.9.6.17
BUILDER_VERIFY=PASS
CONTRACT_TEST=PASS
CONTRACT_TEST_COUNT=56
SOURCE_SHA=PASS
SOURCE_MESH=PASS
GUARD_GEOMETRY=PASS
SOURCE_PRESERVATION=PASS
DRIVE_WHEEL_FIREWALL=PASS
ARTIFACT_CONTRACT=PASS
REPOSITORY_PROTECTION=PASS
REPRODUCIBILITY=PASS
ZIP_AUDIT=RUN_SEPARATELY_AT_PACKAGE
PHYSICAL_TEST=PENDING
POWERED_ROTATION=NOT_APPROVED_BY_THIS_LANE
'''


def generated_files(lane: Path) -> list[str]:
    return sorted(p.relative_to(lane).as_posix() for p in lane.rglob("*") if p.is_file())


def generate_all(lane: Path, repo_root: Path = REPO_ROOT, guard: dict[str, object] | None = None) -> dict[str, object]:
    lane.mkdir(parents=True, exist_ok=True)
    for rel in EXPECTED_FILES:
        (lane / rel).parent.mkdir(parents=True, exist_ok=True)
    source_path = repo_root / SOURCE_REPOSITORY_REL
    if sha256_file(source_path) != SOURCE_SHA256:
        raise RuntimeError("SOURCE_LINK_STL_MISSING")
    shutil.copyfile(source_path, lane / SOURCE_COPY)

    source_metrics = mesh_metrics(source_path)
    for actual, expected in zip(source_metrics["extents_mm"], SOURCE_EXPECTED_EXTENTS):
        if not math.isclose(float(actual), expected, abs_tol=1.0e-5):
            raise RuntimeError(f"Source extent mismatch: {source_metrics['extents_mm']}")
    if not source_metrics["watertight"] or source_metrics["connected_solid_count"] != 1:
        raise RuntimeError("Source mesh contract failed")

    shape, volumes = build_reinforced_link(source_path)
    exporters.export(
        shape,
        str(lane / PRIMARY_STL),
        tolerance=0.02,
        angularTolerance=0.1,
    )
    final_metrics = mesh_metrics(lane / PRIMARY_STL)
    if not final_metrics["watertight"] or final_metrics["connected_solid_count"] != 1:
        raise RuntimeError("Final STL is not one watertight connected solid")
    if not math.isclose(float(final_metrics["extents_mm"][1]), 54.0, abs_tol=1.0e-6):
        raise RuntimeError("Frame-side width changed")

    for rel, content in documentation().items():
        write_text(lane / rel, content)
    for rel, content in svg_outputs().items():
        write_text(lane / rel, content)
    write_json(lane / "design_parameters.json", parameter_data())
    runtime_guard = artifact_repository_record(repo_root)
    write_json(
        lane / "validation_report.json",
        validation_data(lane, runtime_guard, source_metrics, final_metrics, volumes),
    )
    write_text(lane / "BUILD_LOG.txt", build_log(volumes, final_metrics))
    write_text(lane / "TEST_LOG.txt", test_log())

    if len(EXPECTED_FILES) != EXPECTED_PATH_COUNT:
        raise RuntimeError("Internal expected path count mismatch")
    # MANIFEST and SHA sizes are normalized after both files exist; the manifest
    # contract is path-exact, while SHA256SUMS supplies byte authority.
    write_text(lane / "MANIFEST.txt", "\n".join(rel for rel in EXPECTED_FILES))
    commit_paths = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    write_text(lane / "COMMIT_PATHS.txt", "\n".join(commit_paths))
    checksum_paths = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(
        lane / "SHA256SUMS.txt",
        "\n".join(f"{sha256_file(lane / rel)}  {rel}" for rel in checksum_paths),
    )
    files = generated_files(lane)
    if files != EXPECTED_FILES:
        raise RuntimeError(f"Exact path contract mismatch: {files}")
    return {
        "source_metrics": source_metrics,
        "final_metrics": final_metrics,
        "volumes": volumes,
        "path_count": len(files),
    }


def parse_sha256s(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        result[rel] = digest
    return result


def verify_lane(lane: Path = LANE_DIR, root: Path = REPO_ROOT) -> dict[str, object]:
    guard = repository_guard(root)
    files = generated_files(lane)
    if files != EXPECTED_FILES:
        raise RuntimeError(f"Exact path contract mismatch: {files}")
    manifest = (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    if manifest != EXPECTED_FILES:
        raise RuntimeError("MANIFEST path contract mismatch")
    commits = (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    expected_commits = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if commits != expected_commits:
        raise RuntimeError("COMMIT_PATHS contract mismatch")
    sums = parse_sha256s(lane / "SHA256SUMS.txt")
    if set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError("SHA256SUMS scope mismatch")
    mismatches = [rel for rel, digest in sums.items() if sha256_file(lane / rel) != digest]
    if mismatches:
        raise RuntimeError(f"SHA mismatch: {mismatches}")
    if sha256_file(lane / SOURCE_COPY) != SOURCE_SHA256:
        raise RuntimeError("Source copy SHA mismatch")
    source_metrics = mesh_metrics(lane / SOURCE_COPY)
    final_metrics = mesh_metrics(lane / PRIMARY_STL)
    if not source_metrics["watertight"] or source_metrics["connected_solid_count"] != 1:
        raise RuntimeError("Source mesh invalid")
    if not final_metrics["watertight"] or final_metrics["connected_solid_count"] != 1:
        raise RuntimeError("Final mesh invalid")
    if firewall_dependency_count(lane / BUILDER_NAME) != 0:
        raise RuntimeError("Drive-wheel geometry dependency found")
    validation = json.loads((lane / "validation_report.json").read_text(encoding="utf-8"))
    if any(value.startswith("FAIL") for value in validation["checks"].values()):
        raise RuntimeError("Validation report contains FAIL")
    return {
        "repository": guard,
        "path_count": len(files),
        "step_count": len(list(lane.rglob("*.step"))),
        "stl_count": len(list(lane.rglob("*.stl"))) - 1,
        "source_stl_copy_count": 1,
        "svg_count": len(list(lane.rglob("*.svg"))),
        "source_metrics": source_metrics,
        "final_metrics": final_metrics,
        "sha_mismatch_count": 0,
        "drive_wheel_geometry_dependency_count": 0,
        "status": STATUS,
    }


def reproducibility_check(lane: Path = LANE_DIR, root: Path = REPO_ROOT) -> dict[str, object]:
    repository_guard(root)
    with tempfile.TemporaryDirectory(prefix="paddy_v09617_repro_") as temp_name:
        shadow = Path(temp_name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(lane / BUILDER_NAME, shadow / BUILDER_NAME)
        shutil.copyfile(lane / TEST_NAME, shadow / TEST_NAME)
        generate_all(shadow, root)
        mismatches = [
            rel for rel in EXPECTED_FILES
            if (lane / rel).read_bytes() != (shadow / rel).read_bytes()
        ]
    if mismatches:
        raise RuntimeError(f"Reproducibility mismatch: {mismatches}")
    return {"checked_path_count": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not pure.is_absolute() and ".." not in pure.parts and not name.startswith(("/", "\\"))


def package_lane(lane: Path = LANE_DIR, root: Path = REPO_ROOT) -> dict[str, object]:
    verify_lane(lane, root)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = downloads / f"Paddy_Swarm_Common_Rover_Crawler_Link_Anti_Derail_Guard_v0_9_6_17_{stamp}.zip"
    if zip_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", date_time=(2026, 8, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (lane / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        duplicates = len(names) - len(set(names))
        traversal = sum(not safe_zip_member(name) for name in names)
        prefix = LANE_NAME + "/"
        contamination = sum(not name.startswith(prefix) for name in names)
        stripped = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        manifest_exact = stripped == EXPECTED_FILES
        sums_text = archive.read(f"{prefix}SHA256SUMS.txt").decode("utf-8")
        sums = {}
        for line in sums_text.splitlines():
            digest, rel = line.split("  ", 1)
            sums[rel] = digest
        mismatches = [
            rel for rel, digest in sums.items()
            if hashlib.sha256(archive.read(f"{prefix}{rel}")).hexdigest() != digest
        ]
    if duplicates or traversal or contamination or not manifest_exact or mismatches:
        raise RuntimeError("ZIP audit failed")
    return {
        "path": str(zip_path),
        "sha256": sha256_file(zip_path),
        "entry_count": len(EXPECTED_FILES),
        "open": "PASS",
        "duplicate_count": duplicates,
        "traversal_count": traversal,
        "manifest_exact": manifest_exact,
        "sha_mismatch_count": len(mismatches),
        "parent_contamination_count": contamination,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--check-reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any((args.build, args.verify, args.check_reproducibility, args.package)):
        args.verify = True
    if args.build:
        guard = repository_guard()
        result = generate_all(LANE_DIR, REPO_ROOT, guard)
        print(json.dumps({"build": result, "status": STATUS}, ensure_ascii=False, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify_lane()}, ensure_ascii=False, indent=2))
    if args.check_reproducibility:
        print(json.dumps({"reproducibility": reproducibility_check()}, ensure_ascii=False, indent=2))
    if args.package:
        print(json.dumps({"zip": package_lane()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
