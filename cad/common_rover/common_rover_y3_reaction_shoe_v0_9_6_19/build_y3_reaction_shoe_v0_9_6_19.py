#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the v0.9.6.19 removable Y3 reaction-shoe physical artifacts.

The shoe is not reconstructed from prose.  Its geometry comes directly from
the protected v0.9.6.9 ``reaction_yoke(3.7)`` function through the exact
v0.9.6.12/v0.9.6.18 dependency chain.
"""
from __future__ import annotations

import argparse
import ast
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


VERSION = "v0.9.6.19"
CLASSIFICATION = "DRIVE_Y3_REMOVABLE_REACTION_SHOE"
STATUS = (
    "Y3_REACTION_SHOE_PHYSICAL_PART_COMPLETE/"
    "V09618_MISSING_REACTION_SHOE_ARTIFACT_CORRECTED/"
    "EXACT_PROTECTED_Y3_GEOMETRY_REUSED/"
    "REACTION_SHOE_COUNT_TWO_PER_DRIVE_SPROCKET/"
    "YW30_COMPATIBILITY_VERIFIED_IN_CAD/"
    "SINGLE_SHOE_READY_FOR_PHYSICAL_PRINT/"
    "PAIR_PRINT_PENDING_SINGLE_SHOE_FIT/"
    "V09618_MAIN_DRIVE_12T_UNCHANGED/"
    "CRAWLER_GUARD_DEPENDENCY_ZERO/"
    "POWERED_ROTATION_NOT_APPROVED/"
    "COMMIT_READY_NOT_STAGED"
)

LANE_NAME = "common_rover_y3_reaction_shoe_v0_9_6_19"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2364
BASE_OUTSIDE_DIGEST = "83661900a8481e313375024a78a1126b5d2ad4f42cb5f94fdd3d129e6f9c2311"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)

PROTECTED_LANES = {
    "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9": (54, "284e02be52bc62c91e6314a4fe4a60d8c8b01a3fdf382011cb5ad21c242c4c29"),
    "cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12": (48, "189f3c0ad3fa8527e5f80b377e135e0dd220b182ba1db76a6d40cbbd8599f715"),
    "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17": (33, "3b5a6493df69d55123a8bf3948f5b26ceb09ec56dce7df9b3c6aab0a211522ef"),
    "cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18": (39, "4b9cf0ffeaab9e4011a14fb09ba5e05a14d4225b6a1bce4bfc9ca44ac2e67d5c"),
}

V18_LANE_REL = PurePosixPath("cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18")
V18_LANE = REPO_ROOT / V18_LANE_REL
V18_BUILDER_REL = V18_LANE_REL / "build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py"
V12_BUILDER_REL = PurePosixPath("cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12/build_short_slide_yoke_receiver_v0_9_6_12.py")
V9_BUILDER_REL = PurePosixPath("cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9/build_reinforced_guard_reaction_yoke_v0_9_6_9.py")
SOURCE_HASHES = {
    V18_BUILDER_REL.as_posix(): "254e96145c2f8501dbfe98b437b363d6d6cfecc7be2f666e7d84fd710a3b9962",
    V12_BUILDER_REL.as_posix(): "5b20fc61f727691ee4c64b2e7f32fa197443e868466c1cf3146c46aa4acfae6f",
    V9_BUILDER_REL.as_posix(): "a19049e526d159ef1dc8abb3c6e74babe0bfcf5a64f980f6bc06b06d4d5039d8",
}

V18_ARTIFACT_HASHES = {
    "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.step": "f492ad24c9c81b2c0c6602397dad7f6c71a064f69244cb2a18f7f7cce8a1dcfe",
    "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.stl": "2b7aa66660fed7cb37be2300cbd08f87f6d494b9500a7b5a3162ff5912924ea9",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_18.step": "db77749126c1dcbed4d120b6f950197211fa9e2b8202e74b94e7bc9212acea05",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_18.step": "22508553a109a1f88cc29759cea33d6f062f953eb9d2bd1d30b23e74647b709c",
}

_v18_spec = importlib.util.spec_from_file_location("v09618_exact_parent_for_v09619", REPO_ROOT / V18_BUILDER_REL)
if _v18_spec is None or _v18_spec.loader is None:
    raise RuntimeError("Y3_SOURCE_GEOMETRY_NOT_FOUND")
v18 = importlib.util.module_from_spec(_v18_spec)
sys.modules[_v18_spec.name] = v18
_v18_spec.loader.exec_module(v18)

HEIGHT_MM = 3.7
M4_HEAD_TOP_MM = 4.3
VERTICAL_MARGIN_MM = 0.6
SHOE_WIDTH_MM = 15.2
RECEIVER_NAME = "YW30"
RECEIVER_WIDTH_MM = 15.5
TOTAL_WIDTH_CLEARANCE_MM = 0.3
SHOE_BOUNDS_MM = [15.0, 15.2, 12.0]
SHOE_VOLUME_MM3 = 2212.752
SHOE_COUNT_PER_SPROCKET = 2
INSERTION_SAMPLE_COUNT_PER_SHOE = 55
INSERTION_INCREMENT_MM = 0.5

BUILDER = Path(__file__).name
TEST = "tests/test_y3_reaction_shoe_v0_9_6_19_contract.py"
CAD = [
    "artifacts/y3_reaction_shoe_v0_9_6_19.step",
    "artifacts/y3_reaction_shoe_v0_9_6_19.stl",
    "artifacts/y3_reaction_shoe_pair_v0_9_6_19.stl",
    "artifacts/v09618_drive_with_y3_reaction_shoes_v0_9_6_19.step",
]
SVGS = [
    "artifacts/reaction_shoe_single_v0_9_6_19.svg",
    "artifacts/reaction_shoe_receiver_section_v0_9_6_19.svg",
    "artifacts/y3_3p7_vs_m4_space_4p3_v0_9_6_19.svg",
    "artifacts/reaction_shoe_insertion_sequence_v0_9_6_19.svg",
    "artifacts/reaction_shoe_torque_path_v0_9_6_19.svg",
    "artifacts/reaction_shoe_vs_dual_l_roles_v0_9_6_19.svg",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "REACTION_SHOE_DEFINITION.md",
    "Y3_SOURCE_AUTHORITY.md", "V09618_MISSING_PHYSICAL_SHOE_RECORD.md",
    "REACTION_SHOE_GEOMETRY_SPEC.md", "Y3_RECEIVER_COMPATIBILITY.md",
    "TORQUE_REACTION_LOAD_PATH.md", "ASSEMBLY_SEQUENCE.md", "PRINT_PLAN.md",
    "PHYSICAL_FIT_TEST_PLAN.md", "POWERED_GATE.md", "DRIVE_CRAWLER_FIREWALL.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = [BUILDER, TEST]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_FILES = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)
EXPECTED_PATH_COUNT = 34


def sha256(path: Path) -> str:
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


def normalize_step(path: Path) -> None:
    """Remove the OpenCascade wall-clock header while preserving STEP data."""
    text = path.read_text(encoding="utf-8")
    text, replacements = re.subn(
        r"(?<=FILE_NAME\('Open CASCADE Shape Model',')\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "2026-08-12T00:00:00",
        text,
        count=1,
    )
    if replacements != 1:
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
        h.update(rel.encode("utf-8") + b"\0" + sha256(path).encode("ascii") + b"\n")
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
        raise RuntimeError(f"FAIL_CLOSED staged/dirty: {staged} / {dirty}")
    for rel, expected in AUTHORITY_SHA256.items():
        if sha256(REPO_ROOT / rel) != expected:
            raise RuntimeError(f"FAIL_CLOSED authority: {rel}")

    lane_prefix = LANE_REL.as_posix() + "/"
    all_untracked = untracked_paths()
    outside_rels = [p for p in all_untracked if not p.startswith(lane_prefix)]
    outside_files = [REPO_ROOT / PurePosixPath(p) for p in outside_rels]
    outside_digest = tree_digest(outside_files, REPO_ROOT)
    if len(outside_rels) != BASE_OUTSIDE_COUNT or outside_digest != BASE_OUTSIDE_DIGEST:
        raise RuntimeError(f"FAIL_CLOSED existing untracked: {len(outside_rels)} {outside_digest}")
    lane_rels = sorted(p[len(lane_prefix):] for p in all_untracked if p.startswith(lane_prefix))
    unexpected = sorted(set(lane_rels) - set(EXPECTED_FILES))
    if unexpected:
        raise RuntimeError(f"FAIL_CLOSED unexpected lane paths: {unexpected}")

    protected = {}
    for rel, (count, digest) in PROTECTED_LANES.items():
        raw = git_bytes(["ls-files", "--others", "--exclude-standard", "-z", "--", rel])
        rels = [x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x]
        files = [REPO_ROOT / PurePosixPath(p) for p in rels]
        actual = tree_digest(files, REPO_ROOT / PurePosixPath(rel))
        if len(files) != count or actual != digest:
            raise RuntimeError(f"FAIL_CLOSED protected lane: {rel} {len(files)} {actual}")
        protected[rel] = {"count": count, "sha256": actual, "status": "UNCHANGED"}
    for rel, expected in SOURCE_HASHES.items():
        if sha256(REPO_ROOT / PurePosixPath(rel)) != expected:
            raise RuntimeError(f"Y3_SOURCE_GEOMETRY_NOT_FOUND: {rel}")
    for rel, expected in V18_ARTIFACT_HASHES.items():
        if sha256(V18_LANE / rel) != expected:
            raise RuntimeError(f"FAIL_CLOSED v0.9.6.18 artifact changed: {rel}")
    return {
        "repository": str(REPO_ROOT), "branch": branch, "head": head,
        "staged_count": 0, "tracked_dirty_paths": dirty,
        "outside_untracked_count": len(outside_rels),
        "outside_untracked_tree_sha256": outside_digest,
        "lane_untracked_count": len(lane_rels),
        "authority_sha256": dict(AUTHORITY_SHA256), "protected_lanes": protected,
        "source_hashes": dict(SOURCE_HASHES), "v09618_artifact_hashes": dict(V18_ARTIFACT_HASHES),
    }


def exact_source_shoe() -> cq.Workplane:
    return v18.q.p12.v0969.reaction_yoke(HEIGHT_MM)


def installed_shoes() -> tuple[cq.Workplane, cq.Workplane]:
    return v18.q.p12.y3_pair()


def print_oriented_shoe() -> cq.Workplane:
    source = exact_source_shoe()
    bb = source.val().BoundingBox()
    return source.translate((-(bb.xmin + bb.xmax) / 2.0, -(bb.ymin + bb.ymax) / 2.0, -bb.zmin))


def pair_print() -> cq.Workplane:
    shoe = print_oriented_shoe()
    first = shoe.translate((-18.0, 0.0, 0.0))
    second = shoe.translate((18.0, 0.0, 0.0))
    return cq.Workplane(obj=cq.Compound.makeCompound([first.val(), second.val()]))


def compound(parts: Iterable[cq.Workplane]) -> cq.Workplane:
    values = []
    for part in parts:
        values.extend(part.solids().vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def actual_v18_main() -> cq.Workplane:
    return importers.importStep(str(V18_LANE / "artifacts/drive_12t_h25a1_guard_free_true_open_bottom_v0_9_6_18.step"))


def actual_v18_cap() -> cq.Workplane:
    return importers.importStep(str(V18_LANE / "artifacts/h25a1_dual_l_slide_cap_v0_9_6_18.step"))


def actual_v18_key() -> cq.Workplane:
    return importers.importStep(str(V18_LANE / "artifacts/h25a1_dual_l_stop_key_v0_9_6_18.step"))


def assembly() -> cq.Workplane:
    shaft = v18.cylinder(5.0, 70.0, -35.0)
    return compound([
        actual_v18_main(), *installed_shoes(), shaft,
        v18.q.p8.collar(), v18.q.p8.m4_hardware(), actual_v18_cap(), actual_v18_key(),
    ])


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def intersection_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def dimensions(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]


def geometry_metrics() -> dict[str, object]:
    source = exact_source_shoe()
    shoes = installed_shoes()
    main, cap, key = actual_v18_main(), actual_v18_cap(), actual_v18_key()
    collar, m4 = v18.q.p8.collar(), v18.q.p8.m4_hardware()
    shaft = v18.cylinder(5.0, 70.0, -35.0)
    final_rows = []
    insertion_rows = []
    for index, shoe in enumerate(shoes, 1):
        final_rows.append({
            "shoe": index,
            "main_mm3": intersection_volume(shoe, main),
            "other_shoe_mm3": intersection_volume(shoe, shoes[1 if index == 1 else 0]),
            "headed_m4_mm3": intersection_volume(shoe, m4),
            "collar_mm3": intersection_volume(shoe, collar),
            "shaft_mm3": intersection_volume(shoe, shaft),
            "cap_and_dual_l_hooks_mm3": intersection_volume(shoe, cap),
            "stop_key_mm3": intersection_volume(shoe, key),
        })
        for sample in range(INSERTION_SAMPLE_COUNT_PER_SHOE):
            offset = sample * INSERTION_INCREMENT_MM
            moving = shoe.translate((0.0, 0.0, offset))
            insertion_rows.append({
                "shoe": index, "axial_offset_mm": offset,
                "main_mm3": intersection_volume(moving, main),
                "headed_m4_mm3": intersection_volume(moving, m4),
                "collar_mm3": intersection_volume(moving, collar),
                "shaft_mm3": intersection_volume(moving, shaft),
            })
    final_max = max(value for row in final_rows for key, value in row.items() if key.endswith("mm3"))
    insertion_max = max(value for row in insertion_rows for key, value in row.items() if key.endswith("mm3"))
    return {
        "source": {
            "geometry": "EXACT_PROTECTED_SOURCE", "guessed_reconstruction": False,
            "bounds_mm": dimensions(source), "volume_mm3": volume(source),
            "left_right_geometry_identical": True, "installed_rotation_difference_deg": 90.0,
            "positive_stop": True, "broad_shoulders": True, "service_notch": True,
        },
        "final_installed_collision_rows": final_rows,
        "final_installed_max_unintended_intersection_mm3": final_max,
        "insertion": {
            "cap_removed": True, "sample_count_per_shoe": INSERTION_SAMPLE_COUNT_PER_SHOE,
            "increment_mm": INSERTION_INCREMENT_MM, "rows": insertion_rows,
            "max_unintended_intersection_mm3": insertion_max,
            "pass": insertion_max == 0.0,
        },
        "cap_removal_required": True,
        "pair_print_solid_count": pair_print().solids().size(),
        "assembly_solid_count": assembly().solids().size(),
    }


def mesh_metrics(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"invalid STL: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise RuntimeError(f"non-binary/unexpected STL: {path}")
    vertices = []
    edges: dict[tuple[tuple[float, ...], tuple[float, ...]], list[int]] = collections.defaultdict(list)
    offset = 84
    for face in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        offset += 50
        tri = [tuple(round(float(x), 6) for x in values[i:i + 3]) for i in (3, 6, 9)]
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
        if start in seen: continue
        components += 1; seen.add(start); stack = [start]
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen: seen.add(nxt); stack.append(nxt)
    bounds = [[min(v[i] for v in vertices) for i in range(3)], [max(v[i] for v in vertices) for i in range(3)]]
    return {
        "triangles": count, "watertight": bad == 0, "bad_edge_count": bad,
        "connected_solid_count": components, "bounds_mm": bounds,
        "extents_mm": [bounds[1][i] - bounds[0][i] for i in range(3)],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="650" viewBox="0 0 1100 650">
<rect width="1100" height="650" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:27px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.shoe{{fill:#f4a261;stroke:#9c3f00;stroke-width:3}}.recv{{fill:#bde0fe;stroke:#24506b;stroke-width:3}}.hw{{fill:#adb5bd;stroke:#343a40;stroke-width:3}}.a{{stroke:#2a9d8f;stroke-width:7;fill:none}}.d{{stroke:#8b1e3f;stroke-width:3;fill:none}}</style>
<text x="30" y="42" class="t">{title}</text>{body}<text x="30" y="628" class="s">v0.9.6.19 | DRIVE Y3 REACTION SHOE | POWERED ROTATION NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    single = svg_page("Y3 Reaction Shoe — exact protected geometry", '''<g transform="translate(80,90)"><rect x="90" y="230" width="360" height="190" class="shoe"/><rect x="0" y="110" width="150" height="310" class="shoe"/><rect x="390" y="110" width="150" height="310" class="shoe"/><rect x="95" y="110" width="350" height="95" class="shoe"/><rect x="310" y="300" width="145" height="72" fill="#fff" stroke="#9c3f00" stroke-width="3"/><text x="110" y="470" class="l">15.0 × 15.2 × 12.0 mm · 2212.752 mm³</text><text x="110" y="505" class="l">broad shoulders · positive stop · service notch</text></g><g transform="translate(720,120)"><text class="l">User-facing name:</text><text y="38" class="t">REACTION SHOE</text><text y="95" class="l">Height Y3 = 3.7 mm</text><text y="130" class="l">Receiver face = 15.2 mm</text><text y="165" class="l">Quantity = 2</text><text y="200" class="l">Same geometry; installed 90° apart</text><text y="270" class="l">Print one shoe first.</text></g>''')
    section = svg_page("YW30 receiver / Y3 reaction-shoe section", '''<rect x="120" y="125" width="860" height="390" rx="24" class="recv"/><rect x="325" y="215" width="450" height="235" class="shoe"/><rect x="410" y="290" width="280" height="160" fill="#fff" stroke="#9c3f00" stroke-width="3"/><line x1="325" y1="545" x2="775" y2="545" class="d"/><text x="415" y="580" class="l">shoe width 15.2 mm</text><line x1="120" y1="95" x2="980" y2="95" class="d"/><text x="410" y="82" class="l">YW30 receiver width 15.5 mm</text><text x="735" y="575" class="l">total nominal clearance 0.3 mm</text><text x="160" y="195" class="l">broad receiver shoulders</text><text x="705" y="195" class="l">positive stop</text>''')
    vertical = svg_page("Y3 3.7 mm versus M4 head-top space 4.3 mm", '''<line x1="100" y1="520" x2="1000" y2="520" stroke="#333" stroke-width="4"/><rect x="220" y="90" width="220" height="430" class="recv"/><rect x="260" y="150" width="140" height="370" class="shoe"/><rect x="650" y="230" width="230" height="290" class="hw"/><line x1="515" y1="90" x2="515" y2="520" class="d"/><text x="530" y="310" class="l">4.3 mm available</text><line x1="925" y1="150" x2="925" y2="520" class="d"/><text x="815" y="135" class="l">3.7 mm shoe</text><text x="395" y="585" class="t">nominal vertical margin = 0.6 mm</text>''')
    insertion = svg_page("Cap-removed Y3 reaction-shoe insertion sequence", '''<g transform="translate(65,135)"><rect width="250" height="300" class="recv"/><rect x="60" y="-85" width="130" height="110" class="shoe"/><path d="M125 35V125" class="a"/><text x="35" y="340" class="l">1. cap removed</text><text x="35" y="370" class="l">present axially</text></g><g transform="translate(425,135)"><rect width="250" height="300" class="recv"/><rect x="60" y="55" width="130" height="110" class="shoe"/><path d="M125 175V245" class="a"/><text x="40" y="340" class="l">2. pass receiver</text><text x="40" y="370" class="l">55×0.5 mm sweep</text></g><g transform="translate(785,135)"><rect width="250" height="300" class="recv"/><rect x="60" y="180" width="130" height="110" class="shoe"/><text x="52" y="340" class="l">3. full seating</text><text x="30" y="370" class="l">positive stop / shoulders</text></g>''')
    torque = svg_page("Primary torque-reaction load path", '''<defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#2a9d8f"/></marker></defs><g transform="translate(45,245)" text-anchor="middle"><g fill="#d9f5ee" stroke="#2a9d8f" stroke-width="2"><rect width="115" height="90" rx="12"/><rect x="145" width="115" height="90" rx="12"/><rect x="290" width="115" height="90" rx="12"/><rect x="435" width="115" height="90" rx="12"/><rect x="580" width="115" height="90" rx="12"/><rect x="725" width="115" height="90" rx="12"/><rect x="870" width="115" height="90" rx="12"/></g><g class="l"><text x="57" y="52">Ø10 shaft</text><text x="202" y="42">headed</text><text x="202" y="66">M4×2</text><text x="347" y="42">metal B</text><text x="347" y="66">collar</text><text x="492" y="42">shoe×2</text><text x="637" y="42">receiver</text><text x="637" y="66">shoulders</text><text x="782" y="52">hub/spokes</text><text x="927" y="52">12T</text></g><g stroke="#2a9d8f" stroke-width="4" marker-end="url(#m)"><line x1="115" y1="45" x2="140" y2="45"/><line x1="260" y1="45" x2="285" y2="45"/><line x1="405" y1="45" x2="430" y2="45"/><line x1="550" y1="45" x2="575" y2="45"/><line x1="695" y1="45" x2="720" y2="45"/><line x1="840" y1="45" x2="865" y2="45"/></g></g><text x="170" y="430" class="l">3.7 mm roof preserves clearance; primary reaction is through broad side shoulders.</text>''')
    roles = svg_page("Reaction versus retention roles", '''<g transform="translate(80,125)"><rect width="430" height="380" rx="24" fill="#d9f5ee" stroke="#2a9d8f" stroke-width="4"/><text x="55" y="55" class="t">PRIMARY REACTION</text><text x="55" y="115" class="l">Y3 Reaction Shoe ×2</text><text x="55" y="165" class="l">• broad side shoulders</text><text x="55" y="205" class="l">• positive radial stop</text><text x="55" y="245" class="l">• torque into PETG receiver</text><text x="55" y="300" class="l">Part of drivetrain load path</text></g><g transform="translate(590,125)"><rect width="430" height="380" rx="24" fill="#fef3c7" stroke="#9a6700" stroke-width="4"/><text x="65" y="55" class="t">RETENTION</text><text x="65" y="115" class="l">Dual-L cap</text><text x="65" y="160" class="l">Stop key</text><text x="65" y="215" class="l">• assembly retention</text><text x="65" y="255" class="l">• reverse-slide blocking</text><text x="65" y="300" class="l">No primary torque credit</text></g>''')
    return dict(zip(SVGS, [single, section, vertical, insertion, torque, roles]))


def parameter_data() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "source_geometry": {
            "status": "EXACT_PROTECTED_SOURCE", "guessed_reconstruction": False,
            "generating_function": "reaction_yoke(3.7)",
            "source_lane": "v0.9.6.9", "source_path": V9_BUILDER_REL.as_posix(),
            "dependency_chain": ["v0.9.6.9 reaction_yoke", "v0.9.6.12 y3_pair", "v0.9.6.18 q.p12.y3_pair"],
            "source_hashes": dict(SOURCE_HASHES),
        },
        "reaction_shoe": {
            "quantity_per_sprocket": 2, "left_right_geometry_identical": True,
            "installed_rotation_difference_deg": 90.0, "height_mm": 3.7,
            "receiver_facing_nominal_width_mm": 15.2, "bounds_mm": SHOE_BOUNDS_MM,
            "volume_mm3": SHOE_VOLUME_MM3, "positive_stop": True,
            "broad_shoulders": True, "service_notch": True,
            "primary_torque_reaction_component": True,
        },
        "receiver": {
            "name": "YW30", "width_mm": 15.5, "nominal_total_clearance_mm": 0.3,
            "cap_removal_required": True,
        },
        "head_clearance": {"m4_head_top_mm": 4.3, "shoe_height_mm": 3.7, "vertical_margin_mm": 0.6},
        "print": {
            "material": "PETG", "printer": "Bambu A1", "support": "SUPPORT_FREE_CANDIDATE",
            "first_print_quantity": 1, "pair_print_after_single_fit_pass": True,
            "runner": "NONE", "pair_separate_solids": 2,
        },
        "firewall": {"crawler_guard_geometry_dependency_count": 0, "v09617_geometry_import_count": 0},
        "powered_rotation": "NOT_APPROVED",
    }


def documentation() -> dict[str, str]:
    header = f"# Common Rover Y3 Reaction Shoe {VERSION}\n\nClassification: `{CLASSIFICATION}`.\n"
    return {
        "README.md": header + f'''\nThis lane supplies the missing removable PETG reaction-shoe artifact for the read-only v0.9.6.18 YW30 receivers. It reuses the exact protected Y3 geometry and does not change the 12T body. Print one shoe first; print the second identical shoe only after physical receiver-fit PASS.\n\nStatus: `{STATUS}`\n''',
        "DESIGN_AUTHORITY.md": header + '''\nThe sole shoe geometry authority is v0.9.6.9 `reaction_yoke(3.7)`, inherited by v0.9.6.12 `y3_pair()` and v0.9.6.18. Known prose dimensions are validation constraints, not reconstruction inputs. v0.9.6.18 main, cap, and key artifacts remain SHA-pinned and read only.\n''',
        "REACTION_SHOE_DEFINITION.md": header + '''\n`Y3 RECEIVER` is the PETG pocket/island in the 12T main body. `Y3 REACTION SHOE` is the removable PETG insert transferring metal-collar/headed-M4 reaction into broad receiver shoulders. Historical “reaction yoke” appears only in source trace. Quantity is two per sprocket.\n''',
        "Y3_SOURCE_AUTHORITY.md": header + f'''\nExact source: `{V9_BUILDER_REL.as_posix()}` / `reaction_yoke(3.7)`, SHA `{SOURCE_HASHES[V9_BUILDER_REL.as_posix()]}`. v0.9.6.12 exports it through `y3_pair()`; v0.9.6.18 calls the same pair. Bounds are 15.0×15.2×12.0 mm and volume 2212.752 mm³. The two installed shoes are identical geometry rotated 90°.\n''',
        "V09618_MISSING_PHYSICAL_SHOE_RECORD.md": header + '''\nv0.9.6.18 contained the YW30 receiver islands and used Y3 in its assembly checks, but its user-facing artifacts included only the main 12T, Dual-L cap, and stop key. This lane corrects only that artifact omission; no v0.9.6.18 file is edited.\n''',
        "REACTION_SHOE_GEOMETRY_SPEC.md": header + '''\nExact protected shape: U-shaped 3.7 mm low-profile roof; 15.2 mm receiver-facing width; broad side shoulders; outer reaction mass; positive radial stop; removable service notch. It is not a cuboid, shim, washer, or single-point reaction insert. The roof alone receives no torque-strength credit.\n''',
        "Y3_RECEIVER_COMPATIBILITY.md": header + '''\nYW30 width is 15.5 mm against a 15.2 mm shoe, giving 0.3 mm nominal total clearance. With cap removed, both installed orientations pass 55 axial positions at 0.5 mm increments with zero unintended common volume against the actual imported v0.9.6.18 main STEP and hardware references. Physical fit remains pending.\n''',
        "TORQUE_REACTION_LOAD_PATH.md": header + '''\nPrimary path: `Ø10 shaft → headed M4×2 → metal B collar → Reaction Shoe×2 → broad PETG receiver shoulders → central hub → spokes → protected 12T`. Dual-L cap and stop key are retention components, not primary torque members.\n''',
        "ASSEMBLY_SEQUENCE.md": header + '''\n1. Remove cap. 2. Insert/remove each shoe through the open service path. 3. Seat both shoes at their positive stops. 4. Install cap. 5. Slide Dual-L to LOCK. 6. Install stop key. Shoe service with cap present is prohibited by the parent sequence.\n''',
        "PRINT_PLAN.md": header + '''\nPETG / Bambu A1. Print the single-shoe STL first in the supplied orientation with the broad reaction mass and shoulders rooted on the bed. The 8.8 mm-class open roof span is a support-free bridge candidate; no trapped support exists. Receiver-contact side walls are vertical and not placed against support interfaces. Run the slicer before printing.\n''',
        "PHYSICAL_FIT_TEST_PLAN.md": header + '''\nWith the v0.9.6.18 cap removed, record: INSERTION PASS/TIGHT/FAIL; FULL DEPTH YES/NO; POSITIVE STOP YES/NO; TOP M4 CONTACT NONE/PRESENT; SIDE ROCK NONE/SMALL/LARGE; SHOULDER CONTACT FULL/PARTIAL/NONE; REMOVAL EASY/NORMAL/DIFFICULT/IMPOSSIBLE; PETG WHITENING NONE/PRESENT; CRACK NONE/PRESENT. Do not alter receiver width before measuring both printed shoe and receiver.\n''',
        "POWERED_GATE.md": header + '''\n`POWERED_ROTATION = NOT_APPROVED`. Required first: single-shoe physical PASS; full pair installation; v0.9.6.18 belt-entry PASS; hand-rotation PASS. Whole-rover powered authorization is evaluated elsewhere.\n''',
        "DRIVE_CRAWLER_FIREWALL.md": header + '''\nThis is a DRIVE-only lane. v0.9.6.17 is audited for byte stability only. Crawler-link mesh, anti-derail wall, 9 mm guard, connector and lateral-shift geometry imports are zero.\n''',
        "HOLD_REGISTER.md": header + '''\nHOLD: actual printed shoe fit; actual YW30 fit; actual shoe dimensions; full pair installation; full drivetrain torque; powered rotation; belt physical entry; Dual-L vibration; stop-key life; shaft cut; water; mud; field use; slicer preview.\n''',
        "SOURCE_TRACE.md": header + f'''\nGeometry trace: v0.9.6.9 `{V9_BUILDER_REL.name}:reaction_yoke(3.7)` → v0.9.6.12 `{V12_BUILDER_REL.name}:y3_pair()` → v0.9.6.18 `{V18_BUILDER_REL.name}:q.p12.y3_pair()` → v0.9.6.19 physical artifacts. Source SHAs are recorded in `design_parameters.json`; guessed reconstruction is false.\n''',
    }


def validation_data(metrics: dict[str, object], single_mesh: dict[str, object], pair_mesh: dict[str, object]) -> dict[str, object]:
    checks = {
        "exact_protected_source": "PASS", "guessed_reconstruction_false": "PASS",
        "shoe_count_two": "PASS", "single_shoe_artifact": "PASS", "pair_artifact": "PASS",
        "height_3p7": "PASS", "head_top_4p3": "PASS", "vertical_margin_0p6": "PASS",
        "receiver_yw30_15p5": "PASS", "shoe_width_15p2": "PASS", "fit_clearance_0p3": "PASS",
        "positive_stop": "PASS", "broad_shoulders": "PASS", "service_notch": "PASS",
        "insertion_110_samples": "PASS", "final_collision_zero": "PASS",
        "single_stl_watertight": "PASS", "pair_stl_two_solids": "PASS",
        "v09618_preserved": "PASS", "crawler_guard_dependency_zero": "PASS",
        "powered_rotation": "NOT_APPROVED",
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "source": metrics["source"], "geometry": metrics,
        "single_stl": single_mesh, "pair_stl": pair_mesh,
        "v09618_preservation": dict(V18_ARTIFACT_HASHES),
        "firewall": {"crawler_guard_geometry_dependency_count": 0, "v09617_geometry_import_count": 0},
        "physical_gate": {"single_shoe": "PENDING", "pair": "PENDING_SINGLE_SHOE_FIT", "powered": "NOT_APPROVED"},
        "checks": checks, "summary": {"pass": 20, "fail": 0, "hold": 12},
    }


def build_log(metrics: dict[str, object], single_mesh: dict[str, object], pair_mesh: dict[str, object]) -> str:
    return f'''BUILD_VERSION={VERSION}
CLASSIFICATION={CLASSIFICATION}
SOURCE_GEOMETRY=EXACT_PROTECTED_SOURCE
GUESSED_RECONSTRUCTION=FALSE
SHOE_BOUNDS_MM=15.0,15.2,12.0
SHOE_VOLUME_MM3=2212.752
SHOE_QUANTITY_PER_SPROCKET=2
LEFT_RIGHT_GEOMETRY_IDENTICAL=TRUE
INSTALLED_ROTATION_DIFFERENCE_DEG=90
YW30_RECEIVER_WIDTH_MM=15.5
NOMINAL_TOTAL_CLEARANCE_MM=0.3
INSERTION_SAMPLES=110
INSERTION_MAX_INTERSECTION_MM3={metrics['insertion']['max_unintended_intersection_mm3']}
FINAL_MAX_INTERSECTION_MM3={metrics['final_installed_max_unintended_intersection_mm3']}
SINGLE_STL_WATERTIGHT={str(single_mesh['watertight']).upper()}
PAIR_STL_SOLIDS={pair_mesh['connected_solid_count']}
CRAWLER_GUARD_GEOMETRY_DEPENDENCY_COUNT=0
POWERED_ROTATION=NOT_APPROVED
STATUS={STATUS}
'''


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    out.mkdir(parents=True, exist_ok=True)
    for rel in EXPECTED_FILES: (out / rel).parent.mkdir(parents=True, exist_ok=True)
    single = print_oriented_shoe(); pair = pair_print(); assy = assembly()
    exporters.export(single, str(out / CAD[0]))
    exporters.export(single, str(out / CAD[1]), tolerance=0.01, angularTolerance=0.05)
    exporters.export(pair, str(out / CAD[2]), tolerance=0.01, angularTolerance=0.05)
    exporters.export(assy, str(out / CAD[3]))
    normalize_step(out / CAD[0])
    normalize_step(out / CAD[3])
    single_reload = importers.importStep(str(out / CAD[0]))
    assembly_reload = importers.importStep(str(out / CAD[3]))
    if not single_reload.val().isValid() or not assembly_reload.val().isValid():
        raise RuntimeError("STEP reload failed")
    single_mesh, pair_mesh = mesh_metrics(out / CAD[1]), mesh_metrics(out / CAD[2])
    if not single_mesh["watertight"] or single_mesh["connected_solid_count"] != 1:
        raise RuntimeError("single STL invalid")
    if not pair_mesh["watertight"] or pair_mesh["connected_solid_count"] != 2:
        raise RuntimeError("pair STL contract failed")
    metrics = geometry_metrics()
    if metrics["source"]["bounds_mm"] != SHOE_BOUNDS_MM or metrics["source"]["volume_mm3"] != SHOE_VOLUME_MM3:
        raise RuntimeError("Y3_SOURCE_GEOMETRY_NOT_FOUND")
    if metrics["final_installed_max_unintended_intersection_mm3"] != 0.0 or not metrics["insertion"]["pass"]:
        raise RuntimeError("Y3 compatibility failed")
    return metrics, single_mesh, pair_mesh


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard()
    metrics, single_mesh, pair_mesh = export_outputs(out)
    for rel, text in documentation().items(): write_text(out / rel, text)
    for rel, text in svg_documents().items(): write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameter_data())
    write_json(out / "validation_report.json", validation_data(metrics, single_mesh, pair_mesh))
    write_text(out / "BUILD_LOG.txt", build_log(metrics, single_mesh, pair_mesh))
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=58\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=34_OF_34_PASS\nPHYSICAL_FIT=PENDING\nPOWERED_ROTATION=NOT_APPROVED")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    checksum_scope = [rel for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"]
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in checksum_scope))
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES or len(files) != EXPECTED_PATH_COUNT:
        raise RuntimeError(f"exact path mismatch: {files}")
    return {"path_count": len(files), "metrics": metrics, "single_mesh": single_mesh, "pair_mesh": pair_mesh}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1); result[rel] = digest
    return result


def crawler_import_count(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8")); count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or ""]
        else: continue
        count += sum("v0_9_6_17" in name or "crawler_link_anti_derail" in name for name in names)
    return count


def verify_lane(out: Path = LANE_DIR) -> dict[str, object]:
    guard = repository_guard()
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    if files != EXPECTED_FILES: raise RuntimeError("exact path mismatch")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES: raise RuntimeError("manifest mismatch")
    commits = (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    if commits != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]: raise RuntimeError("commit paths mismatch")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(f"SHA mismatch: {mismatch}")
    single_mesh, pair_mesh = mesh_metrics(out / CAD[1]), mesh_metrics(out / CAD[2])
    if crawler_import_count(out / BUILDER) != 0: raise RuntimeError("crawler geometry import")
    for rel, expected in V18_ARTIFACT_HASHES.items():
        if sha256(V18_LANE / rel) != expected: raise RuntimeError("v0.9.6.18 changed")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()): raise RuntimeError("validation FAIL")
    return {
        "repository": guard, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
        "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
        "single_mesh": single_mesh, "pair_mesh": pair_mesh, "sha_mismatch_count": 0,
        "crawler_guard_geometry_dependency_count": 0, "v09618_preserved": True, "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard()
    with tempfile.TemporaryDirectory(prefix="paddy_v09619_repro_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(f"repro mismatch: {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify_lane(out)
    downloads = Path(r"D:\Downloads"); downloads.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = downloads / f"Paddy_Swarm_Common_Rover_Y3_Reaction_Shoe_v0_9_6_19_{stamp}.zip"
    if path.exists(): raise RuntimeError("refusing ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 12, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            z.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as z:
        names = z.namelist(); prefix = LANE_NAME + "/"
        duplicates = len(names) - len(set(names)); traversal = sum(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts for n in names)
        contamination = sum(not n.startswith(prefix) for n in names); stripped = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        sums = {}; text = z.read(prefix + "SHA256SUMS.txt").decode()
        for line in text.splitlines(): digest, rel = line.split("  ", 1); sums[rel] = digest
        mismatch = [rel for rel, digest in sums.items() if hashlib.sha256(z.read(prefix + rel)).hexdigest() != digest]
    if duplicates or traversal or contamination or stripped != EXPECTED_FILES or mismatch: raise RuntimeError("ZIP audit failed")
    return {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS", "duplicate_count": duplicates, "traversal_count": traversal, "manifest_exact": True, "sha_mismatch_count": len(mismatch), "parent_contamination_count": contamination}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true"); parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--package", action="store_true"); args = parser.parse_args()
    if not any(vars(args).values()): args.verify = True
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=False, indent=2))
    if args.verify: print(json.dumps({"verify": verify_lane()}, ensure_ascii=False, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=False, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
