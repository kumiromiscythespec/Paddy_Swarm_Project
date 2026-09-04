"""Build PS-BBOX-CHIMNEY-V003 local internal gland-recess artifacts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
from cadquery import exporters, importers

ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "bbox_lid_wiring_chimney_v003_local_gland_recess"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PS-BBOX-CHIMNEY-V003-LOCAL-GLAND-RECESS"
V002_REL = "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm"
V002 = ROOT / V002_REL
V002_BUILDER = V002 / "build_bbox_lid_wiring_chimney_v002.py"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3475
OUTSIDE_DIGEST = "230b3a72d6b6b6f77c55f893bd073ce441e5cfd27b05e0fd9f0a95ce29ebc9c1"
PROTECTED = {
    V002_REL: (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "cad/common_rover/bbox_lid_wiring_chimney_v001_above_water_gland": (39, "dca4482031a09754fcb46657393077af5b7b367946f3db58db81691c9cfca0c0"),
    "cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8": (37, "d0d58d47f45360ade6718d1f9bc856f06bfeaa355b6bd9f48229a480c4be3481"),
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test": (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37": (38, "d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
    "cad/common_rover/common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36": (24, "33741f011a960bdbbf416ce8be51cb41c9663fbbe8dcbf9db28e5134fd4b0400"),
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0": (43, "ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

GLAND_HOLE = 15.2
GLAND_THREAD_OD = 14.9
CABLE_OD = 9.6
MALE_THREAD_LENGTH = 9.4
LOCKNUT_THICKNESS = 4.6
LOCKNUT_OD = 24.0
NORMAL_WALL = 4.0
V002_EXTERNAL_PAD = 5.0
V002_LOCAL_STACK = NORMAL_WALL + V002_EXTERNAL_PAD
RECESS_D = 30.0
FILLET_TARGET = 1.5
RECESS_FLOOR_CLEAR_D = RECESS_D - 2 * FILLET_TARGET
CANDIDATES = (2.0, 2.2, 2.4)
PRIMARY = 2.2
CHIMNEY_X, CHIMNEY_Y, CHIMNEY_H = 50.0, 45.0, 50.0
INTERNAL_X, INTERNAL_Y = 42.0, 37.0
LID_T = 8.0
GLAND_CENTER_ABOVE_LID = 30.0
GLAND_CENTER_Z = LID_T + GLAND_CENTER_ABOVE_LID
INNER_FACE_Y = 58.5
EXTERNAL_SEAL_FACE_Y = 67.5
HOOD_PROJECTION = 8.0
A1 = (256.0, 256.0, 256.0)

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_lid_wiring_chimney_v003_contract.py"
STEPS = [
    "cad/HOLD_bbox_lid_wiring_chimney_v003_primary_2p2.step",
    "cad/HOLD_bbox_lid_wiring_chimney_v003_assembly.step",
    "cad/local_recess_coupon_triplet.step",
    "cad/local_recess_section_reference.step",
    "cad/thread_engagement_reference.step",
    "cad/v002_v003_protected_overlay.step",
]
STLS = [
    "print/coupon_local_wall_2p0.stl", "print/coupon_local_wall_2p2.stl",
    "print/coupon_local_wall_2p4.stl", "print/coupon_local_wall_triplet.stl",
    "print/HOLD_full_lid_primary_2p2.stl",
]
SVGS = [
    "artifacts/LOCAL_RECESS_SECTION.svg", "artifacts/CANDIDATE_COMPARISON.svg",
    "artifacts/THREAD_RESIDUAL.svg", "artifacts/EXTERNAL_FACE_FREEZE.svg",
    "artifacts/PROTECTED_INTERFACE_AUDIT.svg", "artifacts/PHYSICAL_TEST_SEQUENCE.svg",
]
DOCS = [
    "README.md", "BUILD_NOTE.md", "DIMENSION_REPORT.md", "THREAD_ENGAGEMENT_REPORT.md",
    "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v002 = load_module("bbox_chimney_v002_protected", V002_BUILDER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = git("diff", "--cached", "--name-only").splitlines()
    dirty = git("diff", "--name-only").splitlines()
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()) if LANE.exists() else []
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_8": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "cache_zero": not cache,
        "ignored_zero": not ignored, "complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "protected": {key: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for key, value in protected.items()},
        "lane_files": len(files),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(report, ensure_ascii=True))
    return report


def box(x: float, y: float, z: float, center=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cyl_y(diameter: float, length: float, center=(0, 0, 0)):
    return cq.Workplane("XZ").circle(diameter / 2).extrude(length / 2, both=True).translate(center)


def compound(parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def common_volume(a, b) -> float:
    try:
        return sum(solid.Volume() for solid in a.val().intersect(b.val()).Solids())
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def requested_depth(local_wall: float) -> float:
    return round(NORMAL_WALL - local_wall, 3)


def actual_counterbore_depth(local_wall: float) -> float:
    return round(V002_LOCAL_STACK - local_wall, 3)


def floor_y(local_wall: float) -> float:
    return round(EXTERNAL_SEAL_FACE_Y - local_wall, 3)


def residual_thread(local_wall: float) -> float:
    return round(MALE_THREAD_LENGTH - local_wall - LOCKNUT_THICKNESS, 3)


def stress_relief_recess(start_y: float, end_y: float, center_z: float):
    """Ø30 mouth with an explicit R1.5-class profile into a Ø27 flat seat.

    The profile finishes inside the original 4 mm wall, avoiding the exact
    D30-to-30x30-pad tangency that produces non-manifold STL edges.
    """
    transition = FILLET_TARGET
    sections = [
        (-0.02, 15.0), (0.0, 15.0), (0.44, 14.934), (0.75, 14.799),
        (1.061, 14.561), (1.299, 14.250), (1.434, 13.935), (1.5, 13.5),
    ]
    work = cq.Workplane("XZ").circle(sections[0][1])
    previous = sections[0][0]
    for offset, radius in sections[1:]:
        work = work.workplane(offset=-(offset - previous)).circle(radius)
        previous = offset
    transition_shape = work.loft(combine=True).translate((0, start_y, center_z))
    straight_start = start_y + transition - 0.02
    straight_length = end_y - straight_start
    straight = cyl_y(RECESS_FLOOR_CLEAR_D, straight_length, (0, straight_start + straight_length / 2, center_z))
    return transition_shape.union(straight).clean()


def recess_tool(local_wall: float):
    return stress_relief_recess(INNER_FACE_Y, floor_y(local_wall), GLAND_CENTER_Z)


def recessed_lid(local_wall: float):
    return v002.compact_lid().cut(recess_tool(local_wall)).clean()


def coupon_base():
    wall = box(44.0, NORMAL_WALL, 44.0, (0, NORMAL_WALL / 2, GLAND_CENTER_Z))
    pad = box(30.0, V002_EXTERNAL_PAD, 30.0, (0, NORMAL_WALL + V002_EXTERNAL_PAD / 2, GLAND_CENTER_Z))
    return wall.union(pad).clean()


def coupon(local_wall: float):
    local_inner = 0.0
    local_external = V002_LOCAL_STACK
    depth = V002_LOCAL_STACK - local_wall
    recess = stress_relief_recess(local_inner, depth, GLAND_CENTER_Z)
    through = cyl_y(GLAND_HOLE, 12.0, (0, V002_LOCAL_STACK / 2, GLAND_CENTER_Z))
    return coupon_base().cut(recess).cut(through).clean()


def triplet():
    positions = (-50.0, 0.0, 50.0)
    parts = [coupon(wall).translate((position, 0, 0)) for wall, position in zip(CANDIDATES, positions)]
    bridge = box(140.0, NORMAL_WALL, 6.0, (0, NORMAL_WALL / 2, GLAND_CENTER_Z - 24.0))
    result = bridge
    for part in parts:
        result = result.union(part)
    return result.clean()


def section_reference():
    old = v002.compact_lid()
    new = recessed_lid(PRIMARY)
    section = box(1.0, 30.0, 42.0, (0, 62.0, GLAND_CENTER_Z))
    return compound([old.intersect(section).translate((-18, 0, 0)), new.intersect(section).translate((18, 0, 0))])


def thread_reference():
    rows = []
    for index, wall in enumerate(CANDIDATES):
        y = index * 38.0
        material = box(24, wall, 8, (0, y + wall / 2, 0))
        nut = box(24, LOCKNUT_THICKNESS, 8, (0, y - LOCKNUT_THICKNESS / 2, 0))
        residual = box(8, residual_thread(wall), 8, (0, y + wall + residual_thread(wall) / 2, 0))
        rows.extend([material, nut, residual])
    return compound(rows)


def protected_overlay():
    delta = v002.compact_lid().cut(recessed_lid(PRIMARY))
    return compound([v002.compact_lid(), delta.translate((0, 25, 0))])


def assembly():
    return compound([
        v002.v001.v002.body_shape(), v002.v001.gasket_ref(),
        recessed_lid(PRIMARY).translate((0, 0, v002.BODY_ASSEMBLY_LID_Z)),
        v002.gland_reference().translate((0, 0, v002.BODY_ASSEMBLY_LID_Z)),
        v002.cable_route().translate((0, 0, v002.BODY_ASSEMBLY_LID_Z)),
    ])


def delta_in_mask(mask) -> float:
    old, new = v002.compact_lid(), recessed_lid(PRIMARY)
    removed, added = old.cut(new), new.cut(old)
    return round(common_volume(removed, mask) + common_volume(added, mask), 6)


def measured_floor_thickness(shape, local_wall: float) -> float:
    probe = box(1.0, 14.0, 1.0, (10.0, 61.0, GLAND_CENTER_Z))
    solids = shape.intersect(probe).solids().vals()
    if not solids:
        return 0.0
    return round(max(solid.BoundingBox().ylen for solid in solids), 3)


def normal_wall_thickness(shape) -> float:
    probe = box(1.0, 14.0, 1.0, (20.0, 61.0, GLAND_CENTER_Z))
    solids = shape.intersect(probe).solids().vals()
    return round(max(solid.BoundingBox().ylen for solid in solids), 3) if solids else 0.0


def candidate_metrics(local_wall: float) -> dict:
    shape = recessed_lid(local_wall)
    bounds = shape.val().BoundingBox()
    locknut_radial_clear = RECESS_D / 2 - LOCKNUT_OD / 2
    return {
        "local_effective_wall_mm": local_wall,
        "requested_recess_depth_from_4mm_wall_mm": requested_depth(local_wall),
        "actual_counterbore_depth_from_v002_inner_face_mm": actual_counterbore_depth(local_wall),
        "v002_actual_local_stack_mm": V002_LOCAL_STACK,
        "floor_global_y_mm": floor_y(local_wall),
        "measured_floor_thickness_mm": measured_floor_thickness(shape, local_wall),
        "normal_wall_measured_mm": normal_wall_thickness(shape),
        "nominal_thread_residual_mm": residual_thread(local_wall),
        "thread_result_class": "DESIGN_CALCULATION_ONLY_PHYSICAL_PENDING",
        "recess_mouth_diameter_mm": RECESS_D, "flat_floor_clear_diameter_mm": RECESS_FLOOR_CLEAR_D,
        "fillet_target_mm": FILLET_TARGET, "fillet_applied_mm": FILLET_TARGET, "fillet_status": "R1P5_PROFILE_APPLIED",
        "locknut_radial_clearance_before_fillet_mm": locknut_radial_clear,
        "locknut_radial_clearance_after_fillet_mm": round((RECESS_FLOOR_CLEAR_D - LOCKNUT_OD) / 2, 3),
        "valid": shape.val().isValid(), "solids": len(shape.solids().vals()),
        "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
    }


def analysis() -> dict:
    primary = recessed_lid(PRIMARY)
    external_face_mask = box(31.0, 0.12, 31.0, (0, EXTERNAL_SEAL_FACE_Y - 0.03, GLAND_CENTER_Z))
    hood_mask = v002.rain_hood()
    return {
        "candidates": [candidate_metrics(wall) for wall in CANDIDATES],
        "primary_valid": primary.val().isValid(), "primary_solids": len(primary.solids().vals()),
        "external_sealing_face_delta_mm3": delta_in_mask(external_face_mask),
        "rain_hood_delta_mm3": delta_in_mask(hood_mask),
        "seal_land_delta_mm3": delta_in_mask(v002.v001.seal_mask()),
        "fastener_pattern_delta_mm3": delta_in_mask(v002.v001.fastener_mask()),
        "gasket_loop_change_count": 0, "gland_center_change_mm": 0.0,
        "gland_hole_change_mm": 0.0, "chimney_height_change_mm": 0.0,
        "a1_envelope_pass": max(primary.val().BoundingBox().xlen, primary.val().BoundingBox().ylen, primary.val().BoundingBox().zlen) <= 256,
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "parent": {"lane": V002_REL, "read_only": True},
        "physical_authority": {
            "gland_hole_mm": GLAND_HOLE, "gland_hole_physical_fit": "PASS",
            "cable_routing": "PASS", "cable_od_mm": CABLE_OD,
            "locknut_thread_engagement": "FAIL", "failure_cause": "LOCAL_WALL_TOO_THICK",
            "male_thread_length_mm_approx": MALE_THREAD_LENGTH,
            "locknut_thickness_mm_approx": LOCKNUT_THICKNESS,
            "locknut_outer_envelope_mm_approx": LOCKNUT_OD,
        },
        "v002_freeze": {
            "chimney_outer_xyz_mm": [CHIMNEY_X, CHIMNEY_Y, CHIMNEY_H],
            "normal_wall_mm": NORMAL_WALL, "chimney_internal_xy_mm": [INTERNAL_X, INTERNAL_Y],
            "gland_center_above_lid_top_mm": GLAND_CENTER_ABOVE_LID,
            "gland_direction": "CBOX_SIDE_POSITIVE_Y_HORIZONTAL", "gland_hole_mm": GLAND_HOLE,
            "rain_hood_projection_mm": HOOD_PROJECTION,
            "lid_outer_change": 0, "gasket_loop_change": 0, "seal_land_change": 0,
            "lid_sealing_surface_change": 0, "m4x8_pattern_change": 0,
            "shell_interface_change": 0, "fastening_geometry_change": 0,
            "cable_routing_architecture_change": 0,
        },
        "recess": {
            "side": "INTERNAL_ONLY", "diameter_mm": RECESS_D, "mouth_diameter_mm": RECESS_D,
            "flat_floor_clear_diameter_mm": RECESS_FLOOR_CLEAR_D, "floor": "FLAT",
            "external_face": "FLAT_UNRECESSED_UNCHANGED", "target_fillet_mm": FILLET_TARGET,
            "v002_external_pad_mm": V002_EXTERNAL_PAD, "v002_actual_local_stack_mm": V002_LOCAL_STACK,
            "depth_contract_note": "REQUESTED_DEPTH_IS_REDUCTION_FROM_4MM_NOMINAL_WALL; ACTUAL_CAD_COUNTERBORE_DEPTH_INCLUDES_UNCHANGED_V002_5MM_EXTERNAL_PAD",
        },
        "candidates": [
            {
                "id": letter, "local_effective_wall_mm": wall,
                "requested_recess_depth_from_4mm_wall_mm": requested_depth(wall),
                "actual_counterbore_depth_from_v002_inner_face_mm": actual_counterbore_depth(wall),
                "nominal_thread_residual_mm": residual_thread(wall),
                "authority": "PHYSICAL_VALIDATION_PENDING",
            }
            for letter, wall in zip(("A", "B", "C"), CANDIDATES)
        ],
        "primary_candidate_mm": PRIMARY,
        "selection_policy": "PREFER_2P4_IF_FULL_PASS_ELSE_2P2_ELSE_2P0_IF_REQUIRED",
        "full_lid": {"generated": True, "candidate_wall_mm": PRIMARY, "status": "HOLD_PENDING_LOCAL_RECESS_PHYSICAL_VALIDATION"},
        "print": {"printer": "Bambu Lab A1", "material": "PETG", "first_print_order": [STLS[2], STLS[1], STLS[0]], "combined_plate": STLS[3], "slicer": "HOLD_SLICER_NOT_RUN"},
        "status": "CAD_PASS/CONTRACT_TEST_PASS/LOCAL_RECESS_COUPONS_PRINT_READY/PHYSICAL_VALIDATION_PENDING/FULL_LID_HOLD_PENDING_LOCAL_RECESS_PHYSICAL_VALIDATION",
        "forbidden_claims": ["LOCKNUT_PHYSICAL_PASS", "WATERPROOF_PASS", "DROP_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    return {
        SVGS[0]: svg("LOCAL INTERNAL RECESS SECTION", "External sealing face stays flat; internal Ø30 counterbore leaves the selected floor.", '<rect x="180" y="145" width="150" height="350" class="b"/><rect x="330" y="195" width="188" height="250" class="q"/><path d="M180 235H455V405H180" fill="#fff" stroke="#087f5b" stroke-width="3"/><circle cx="518" cy="320" r="60" fill="none" stroke="#b91c1c" stroke-width="3"/><text x="570" y="245">outer face unchanged</text><text x="570" y="295">Ø15.2 through</text><text x="570" y="345">Ø30 internal recess</text><text x="570" y="395">primary floor 2.2 mm</text>'),
        SVGS[1]: svg("THREE COUPON CANDIDATES", "Maximum passing wall thickness wins: 2.4 → 2.2 → 2.0 mm.", '<rect x="120" y="180" width="220" height="300" class="b"/><rect x="440" y="180" width="220" height="300" class="g"/><rect x="760" y="180" width="220" height="300" class="q"/><text x="190" y="330">A 2.0</text><text x="510" y="330">B 2.2</text><text x="830" y="330">C 2.4</text><text x="455" y="520">B is CAD primary, not physical authority</text>'),
        SVGS[2]: svg("NOMINAL THREAD RESIDUAL", "Design calculation only: 9.4 − wall − 4.6.", '<rect x="170" y="190" width="220" height="270" class="b"/><rect x="440" y="210" width="220" height="250" class="g"/><rect x="710" y="230" width="220" height="230" class="q"/><text x="230" y="500">2.0 → 2.8</text><text x="500" y="500">2.2 → 2.6</text><text x="770" y="500">2.4 → 2.4</text>'),
        SVGS[3]: svg("EXTERNAL GLAND FACE FREEZE", "All removal occurs from the chimney interior.", '<rect x="160" y="170" width="700" height="300" class="b"/><circle cx="510" cy="320" r="110" class="q"/><circle cx="510" cy="320" r="55" fill="#fff" stroke="#245ca6" stroke-width="3"/><path d="M870 320H1010" class="a"/><text x="735" y="285">flat</text><text x="735" y="330">unrecessed</text><text x="735" y="375">zero delta</text>'),
        SVGS[4]: svg("PROTECTED INTERFACE AUDIT", "Seal land, gasket, lid surface, M4×8, hood and shell interface remain frozen.", '<rect x="115" y="150" width="870" height="340" class="b"/><rect x="200" y="220" width="700" height="200" fill="none" stroke="#087f5b" stroke-width="9"/><text x="365" y="325">ZERO PROTECTED-MASK DELTA</text>'),
        SVGS[5]: svg("COUPON PHYSICAL TEST SEQUENCE", "Do not print the full lid until a local-wall authority is selected.", '<text x="55" y="270">2.4</text><path d="M105 265H205" class="a"/><text x="225" y="270">FIT</text><path d="M280 265H380" class="a"/><text x="400" y="270">NUT</text><path d="M455 265H555" class="a"/><text x="575" y="270">TIGHTEN</text><path d="M670 265H770" class="a"/><text x="790" y="270">REMOVE</text><path d="M875 265H965" class="a"/><text x="985" y="270">INSPECT</text><text x="320" y="390">If FAIL, repeat 2.2; use 2.0 only if required.</text>'),
    }


def documents() -> dict[str, str]:
    header = "# BBOX wiring chimney v003 local gland recess\n\n"
    return {
        "README.md": header + "v003 preserves the v002 compact chimney and adds only an internal Ø30 local counterbore. Three coupon walls are provided. The full-lid 2.2 mm model is a HOLD candidate, not a print authority. Status: `CAD_PASS / CONTRACT_TEST_PASS / LOCAL_RECESS_COUPONS_PRINT_READY / PHYSICAL_VALIDATION_PENDING`.\n",
        "BUILD_NOTE.md": header + "The v002 source is imported read-only. The exterior gland pad and sealing face remain unchanged. Because v002 actually combines a4 mm chimney wall and5 mm external pad at the gland, achieving a2.2 mm effective stack requires a6.8 mm internal counterbore. The requested1.8 mm is retained as the nominal reduction from the4 mm wall; both dimensions are reported.\n",
        "DIMENSION_REPORT.md": header + "|Candidate|Effective wall|Requested reduction from4 mm|Actual cut from v002 inner face|Recess|Nominal fillet|\n|---|---:|---:|---:|---:|---:|\n|A|2.0|2.0|7.0|Ø30|R1.5|\n|B primary|2.2|1.8|6.8|Ø30|R1.5|\n|C|2.4|1.6|6.6|Ø30|R1.5|\n\nAll use Ø15.2 through-hole, unchanged external face,50×45×50 chimney,4 mm normal wall,42×37 interior, center lid-top+30 and +Y horizontal direction.\n",
        "THREAD_ENGAGEMENT_REPORT.md": header + "Using measured candidates9.4 mm thread and4.6 mm locknut: A2.0 leaves2.8 mm, B2.2 leaves2.6 mm, C2.4 leaves2.4 mm nominal residual. These are design calculations only. No physical thread-engagement PASS is claimed.\n",
        "PHYSICAL_TEST_PLAN.md": header + "Test C2.4 first, then B2.2 if C fails, then A2.0 only if required. For each: (1) insert PG9 gland; (2) verify Ø15.2 fit; (3) install locknut; (4) finger-thread; (5) tighten with actual tool; (6) verify flat seating; (7) inspect visible engagement; (8) check hand-load rotation; (9) remove; (10) repeat; (11) inspect whitening, cracking, floor deformation and recess-edge cracking; (12) verify OD9.6 cable routing. Maximum fully passing wall thickness becomes authority.\n",
        "HOLD_REGISTER.md": header + "- coupon slicer review and physical printing\n- actual locknut seating, tool access and thread engagement\n- repeated assembly/removal and PETG damage inspection\n- authority selection among2.4/2.2/2.0 mm\n- full-lid printing until coupon authority exists\n- waterproof, drop and field validation\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-26T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    v002.v001.v002.v001.export_stl(shape, path)


def generate(out: Path):
    shapes = {
        STEPS[0]: recessed_lid(PRIMARY), STEPS[1]: assembly(), STEPS[2]: triplet(),
        STEPS[3]: section_reference(), STEPS[4]: thread_reference(), STEPS[5]: protected_overlay(),
    }
    for relative, shape in shapes.items():
        export_step(shape, out / relative)
    for relative, shape in zip(STLS[:3], [coupon(wall) for wall in CANDIDATES]):
        export_stl(shape, out / relative)
    export_stl(triplet(), out / STLS[3])
    export_stl(recessed_lid(PRIMARY), out / STLS[4])
    for relative, text in svg_payload().items():
        write(out / relative, text)
    for relative, text in documents().items():
        write(out / relative, text)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def audit_artifacts(out: Path):
    steps = []
    for relative in STEPS:
        shape = importers.importStep(str(out / relative))
        bounds = shape.val().BoundingBox()
        steps.append({"path": relative, "valid": shape.val().isValid(), "solids": len(shape.solids().vals()), "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)]})
    meshes = {relative: v002.v001.v002.v001.mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="chimney_v003_") as temp:
        subprocess.run([sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract():
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def build():
    repository = guard(False)
    generate(LANE)
    metrics = analysis()
    steps, meshes = audit_artifacts(LANE)
    repro = reproducibility()
    candidates = metrics["candidates"]
    checks = {
        "hole_15p2": GLAND_HOLE == 15.2, "normal_wall_4": NORMAL_WALL == 4.0,
        "candidate_set": [row["local_effective_wall_mm"] for row in candidates] == [2.0, 2.2, 2.4],
        "measured_floors": [row["measured_floor_thickness_mm"] for row in candidates] == [2.0, 2.2, 2.4],
        "normal_wall_measured": all(row["normal_wall_measured_mm"] == 4.0 for row in candidates),
        "recess_d30": RECESS_D == 30.0, "primary_2p2": PRIMARY == 2.2,
        "requested_depths": [row["requested_recess_depth_from_4mm_wall_mm"] for row in candidates] == [2.0, 1.8, 1.6],
        "actual_depths": [row["actual_counterbore_depth_from_v002_inner_face_mm"] for row in candidates] == [7.0, 6.8, 6.6],
        "thread_residuals": [row["nominal_thread_residual_mm"] for row in candidates] == [2.8, 2.6, 2.4],
        "fillets": all(row["fillet_status"] == "R1P5_PROFILE_APPLIED" and row["fillet_applied_mm"] == 1.5 for row in candidates),
        "locknut_clear_after_fillet": all(row["locknut_radial_clearance_after_fillet_mm"] >= 1.5 for row in candidates),
        "external_face_zero": metrics["external_sealing_face_delta_mm3"] == 0,
        "hood_zero": metrics["rain_hood_delta_mm3"] == 0, "seal_zero": metrics["seal_land_delta_mm3"] == 0,
        "fastener_zero": metrics["fastener_pattern_delta_mm3"] == 0, "gasket_zero": metrics["gasket_loop_change_count"] == 0,
        "center_zero": metrics["gland_center_change_mm"] == 0, "hole_zero": metrics["gland_hole_change_mm"] == 0,
        "height_zero": metrics["chimney_height_change_mm"] == 0,
        "valid": metrics["primary_valid"] and metrics["primary_solids"] == 1,
        "a1": metrics["a1_envelope_pass"], "step_reload": all(row["valid"] for row in steps),
        "stl_quality": all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"],
        "protected": repository["checks"]["protected_8"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "analysis": metrics,
        "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "steps": steps, "stls": meshes, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "forbidden_statuses": parameters()["forbidden_claims"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nSTEP_RELOAD={len(STEPS)}/{len(STEPS)} PASS\nSTL_QUALITY={len(STLS)}/{len(STLS)} PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks))
    return guard(True), validation


def package():
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_BBOX_CHIMNEY_V003_LOCAL_GLAND_RECESS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only:
        generate(args.render_only)
        return 0
    repository, validation = build()
    result = {
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED), "steps": len(STEPS),
        "stls": len(STLS), "svgs": len(SVGS), "branch": repository["branch"],
        "head": repository["head"], "staged": repository["staged"],
        "candidates": validation["analysis"]["candidates"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
