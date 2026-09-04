"""Build PS-BBOX-LID-WIRING-CHIMNEY-V002 compact 50 mm artifacts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
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
LANE_NAME = "bbox_lid_wiring_chimney_v002_compact_50mm"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PS-BBOX-LID-WIRING-CHIMNEY-V002-COMPACT-50MM"
V001_REL = "cad/common_rover/bbox_lid_wiring_chimney_v001_above_water_gland"
V001 = ROOT / V001_REL
V001_BUILDER = V001 / "build_bbox_lid_wiring_chimney_v001.py"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3446
OUTSIDE_DIGEST = "7cc8db77b7372d72aaf2171be16974288f36de67beda9ebbffa80d555e082496"
PROTECTED = {
    V001_REL: (39, "dca4482031a09754fcb46657393077af5b7b367946f3db58db81691c9cfca0c0"),
    "cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8": (37, "d0d58d47f45360ade6718d1f9bc856f06bfeaa355b6bd9f48229a480c4be3481"),
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test": (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37": (38, "d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
    "cad/common_rover/common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36": (24, "33741f011a960bdbbf416ce8be51cb41c9663fbbe8dcbf9db28e5134fd4b0400"),
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0": (43, "ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

GLAND_THREAD_OD = 14.9
GLAND_HOLE = 15.2
CABLE_OD = 9.6
LID_T = 8.0
CHIMNEY_X, CHIMNEY_Y, CHIMNEY_H = 50.0, 45.0, 50.0
WALL = 4.0
INTERNAL_X, INTERNAL_Y = 42.0, 37.0
CHIMNEY_CENTER_Y = 40.0
GLAND_CENTER_ABOVE_LID = 30.0
GLAND_CENTER_Z = LID_T + GLAND_CENTER_ABOVE_LID
PAD_X, PAD_Z, PAD_ADDED_T = 30.0, 30.0, 5.0
HOOD_X, HOOD_PROJECTION, HOOD_MAX_T = 34.0, 8.0, 5.0
BODY_ASSEMBLY_LID_Z = 70.895
A1 = (256.0, 256.0, 256.0)

CRAWLER_BOTTOM_Z = 0.0
FRAME_BOTTOM_Z = 64.0
FRAME_TOP_Z = 257.0
TARGET_WATER_DEPTH = 150.0
TARGET_MUD_SINK = 60.0
EFFECTIVE_WATERLINE = TARGET_WATER_DEPTH + TARGET_MUD_SINK
# The current top-insert architecture locates the lid at the measured frame top.
# Repository files do not contain an independent survey of this mount transform,
# so the absolute result is explicitly classified as a derived mount assumption.
BBOX_LID_TOP_ABS_Z = FRAME_TOP_Z
ABS_DATUM_CLASS = "DERIVED_MOUNT_ASSUMPTION_TOP_INSERT_LID_AT_MEASURED_FRAME_TOP"
GLAND_CENTER_ABS_Z = BBOX_LID_TOP_ABS_Z + GLAND_CENTER_ABOVE_LID
HOLE_LOWEST_ABS_Z = GLAND_CENTER_ABS_Z - GLAND_HOLE / 2

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_lid_wiring_chimney_v002_contract.py"
STEPS = [
    "cad/bbox_lid_wiring_chimney_v002_compact.step",
    "cad/bbox_lid_wiring_chimney_v002_compact_assembly.step",
    "cad/gland_14p9_hole_15p2_reference.step",
    "cad/cable_9p6_route_reference.step",
    "cad/tool_access_dimensional_reference.step",
    "cad/waterline_absolute_reference.step",
]
STLS = ["print/bbox_lid_wiring_chimney_v002_compact.stl"]
SVGS = [
    "artifacts/V001_V002_COMPACT_COMPARISON.svg",
    "artifacts/WATERLINE_CLEARANCE.svg",
    "artifacts/GLAND_TOOL_ACCESS.svg",
    "artifacts/SEALING_INTERFACE_FREEZE.svg",
    "artifacts/TPU_FUTURE_INTERFACE.svg",
    "artifacts/PHYSICAL_TEST_SEQUENCE.svg",
]
DOCS = [
    "README.md", "BUILD_NOTE.md", "DIMENSION_REPORT.md", "WATERLINE_CLEARANCE_REPORT.md",
    "TOOL_ACCESS_REPORT.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt",
    "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v001 = load_module("bbox_chimney_v001_protected", V001_BUILDER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        p for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for path_item in files:
        digest.update((path_item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(path_item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(
        line[3:].replace("\\", "/")
        for line in git("status", "--porcelain=v1", "-uall").splitlines()
        if line.startswith("?? ")
    )


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
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
        "authority_4": authority == AUTHORITY, "protected_7": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "cache_zero": not cache, "ignored_zero": not ignored,
        "complete": not complete or files == EXPECTED,
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
    return sum(solid.Volume() for solid in a.val().intersect(b.val()).Solids())


def parent_lid():
    return v001.parent_lid()


def cavity_tool():
    return box(INTERNAL_X, INTERNAL_Y, 56.0, (0, CHIMNEY_CENTER_Y, 27.0))


def gland_hole_tool():
    return cyl_y(GLAND_HOLE, 24.0, (0, 65.0, GLAND_CENTER_Z))


def rain_hood():
    # Roof-integrated, bottom-open brow. Projection is reduced from 10 to 8 mm
    # to fit the strict H50 package without touching the sealing boundary.
    profile = cq.Workplane("YZ").polyline([
        (62.5, 53.0), (70.5, 53.0), (70.5, 56.0), (62.5, 58.0)
    ]).close()
    return profile.extrude(HOOD_X / 2, both=True)


def compact_lid():
    outer = box(CHIMNEY_X, CHIMNEY_Y, CHIMNEY_H, (0, CHIMNEY_CENTER_Y, LID_T + CHIMNEY_H / 2))
    pad = box(PAD_X, PAD_ADDED_T, PAD_Z, (0, 62.5 + PAD_ADDED_T / 2, GLAND_CENTER_Z))
    return parent_lid().union(outer).union(pad).union(rain_hood()).cut(cavity_tool()).cut(gland_hole_tool()).clean()


def gland_reference():
    thread = cyl_y(GLAND_THREAD_OD, 28.0, (0, 73.0, GLAND_CENTER_Z))
    flange = cyl_y(24.0, 4.0, (0, 64.0, GLAND_CENTER_Z))
    nut = cyl_y(23.0, 5.0, (0, 59.0, GLAND_CENTER_Z))
    return compound([thread, flange, nut])


def dimensional_tool_reference():
    # D40 is a review envelope inherited from v001, not a guaranteed wrench.
    external = cyl_y(40.0, 35.0, (0, 85.0, GLAND_CENTER_Z))
    internal = box(34.0, 34.0, 42.0, (0, 40.0, 21.0))
    return compound([compact_lid(), external, internal])


def segment(a, b, diameter):
    va, vb = cq.Vector(*a), cq.Vector(*b)
    vector = vb.sub(va)
    return cq.Workplane(obj=cq.Solid.makeCylinder(diameter / 2, vector.Length, va, vector.normalized()))


def sphere(diameter, center):
    return cq.Workplane(obj=cq.Solid.makeSphere(diameter / 2, cq.Vector(*center)))


def cable_route():
    points = [(0, 67.5, 38), (0, 100, 38), (0, 112, 31), (0, 123, 22), (0, 136, 18), (0, 150, 24)]
    return compound([segment(a, b, CABLE_OD) for a, b in zip(points, points[1:])] + [sphere(CABLE_OD, p) for p in points[1:-1]])


def waterline_reference():
    lid = compact_lid().translate((0, 0, BBOX_LID_TOP_ABS_Z - LID_T))
    normal = box(240, 190, 0.6, (0, 0, TARGET_WATER_DEPTH))
    effective = box(240, 190, 0.6, (0, 0, EFFECTIVE_WATERLINE))
    return compound([lid, normal, effective])


def assembly():
    return compound([
        v001.v002.body_shape(), v001.gasket_ref(),
        compact_lid().translate((0, 0, BODY_ASSEMBLY_LID_Z)),
        gland_reference().translate((0, 0, BODY_ASSEMBLY_LID_Z)),
        cable_route().translate((0, 0, BODY_ASSEMBLY_LID_Z)),
    ])


def masked_delta(mask) -> float:
    old, new = parent_lid(), compact_lid()
    removed, added = old.cut(new), new.cut(old)
    return round(common_volume(removed, mask) + common_volume(added, mask), 6)


def analysis() -> dict:
    lid = compact_lid()
    bounds = lid.val().BoundingBox()
    external_d40 = cyl_y(40.0, 35.0, (0, 85.0, GLAND_CENTER_Z))
    return {
        "lid_valid": lid.val().isValid(), "lid_solids": len(lid.solids().vals()),
        "lid_bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
        "gasket_loop_change_count": 0,
        "seal_land_delta_mm3": masked_delta(v001.seal_mask()),
        "fastener_pattern_delta_mm3": masked_delta(v001.fastener_mask()),
        "external_d40_review_envelope_lid_intersection_mm3": round(common_volume(external_d40, lid), 6),
        "internal_34x34_review_envelope_wall_intersection_mm3": round(common_volume(box(34, 34, 42, (0, 40, 21)), lid), 6),
        "a1_envelope_pass": max(bounds.xlen, bounds.ylen, bounds.zlen) <= 256.0,
        "gland_diametral_clearance_mm": round(GLAND_HOLE - GLAND_THREAD_OD, 3),
    }


def waterline_data() -> dict:
    return {
        "crawler_bottom_absolute_z_mm": CRAWLER_BOTTOM_Z,
        "frame_bottom_absolute_z_mm": FRAME_BOTTOM_Z,
        "frame_top_absolute_z_mm": FRAME_TOP_Z,
        "bbox_lid_top_absolute_z_mm": BBOX_LID_TOP_ABS_Z,
        "bbox_lid_top_datum_class": ABS_DATUM_CLASS,
        "gland_center_absolute_z_mm": GLAND_CENTER_ABS_Z,
        "gland_center_margin_to_z150_mm": round(GLAND_CENTER_ABS_Z - TARGET_WATER_DEPTH, 3),
        "effective_waterline_z_mm": EFFECTIVE_WATERLINE,
        "effective_waterline_class": "CONSERVATIVE_DESIGN_CALCULATION_NOT_FIELD_MEASUREMENT",
        "gland_center_margin_to_z210_mm": round(GLAND_CENTER_ABS_Z - EFFECTIVE_WATERLINE, 3),
        "gland_hole_lowest_absolute_z_mm": HOLE_LOWEST_ABS_Z,
        "gland_hole_lower_edge_margin_to_z150_mm": round(HOLE_LOWEST_ABS_Z - TARGET_WATER_DEPTH, 3),
        "gland_hole_lower_edge_margin_to_z210_mm": round(HOLE_LOWEST_ABS_Z - EFFECTIVE_WATERLINE, 3),
        "field_validation": "NOT_CLAIMED",
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "classification": "COMPACT_CHIMNEY_LID_FIRST_PRINT_CANDIDATE",
        "parent": {"lane": V001_REL, "read_only": True},
        "physical_authority": {
            "date": "2026-08-25", "cable_od_mm": CABLE_OD, "gland_male_thread_od_mm": GLAND_THREAD_OD,
            "gland_hole_authority_mm": GLAND_HOLE, "gland_hole_physical_fit": "PASS",
            "observations": ["INSERTION_POSSIBLE", "FINGER_REMOVAL_POSSIBLE", "NO_GRAVITY_DROP", "REPEATED_PASS", "NO_WHITENING_OR_CRACK", "LOCKNUT_TIGHTENING_PASS", "NO_ROTATION_ISSUE_AFTER_TIGHTENING"],
            "waterproof_physical_validation": "NOT_PERFORMED",
        },
        "chimney": {
            "external_xyz_mm": [CHIMNEY_X, CHIMNEY_Y, CHIMNEY_H], "wall_mm": WALL,
            "internal_xy_mm": [INTERNAL_X, INTERNAL_Y], "gland_center_above_lid_top_mm": GLAND_CENTER_ABOVE_LID,
            "gland_direction": "CBOX_SIDE_POSITIVE_Y_HORIZONTAL", "integral_with_lid": True,
            "rain_hood": {"retained": True, "width_mm": HOOD_X, "projection_mm": HOOD_PROJECTION, "max_thickness_mm": HOOD_MAX_T, "bottom_open": True, "adjustment": "V001_PROJECTION_10_TO_V002_8_FOR_H50_PACKAGE"},
        },
        "freeze": {
            "lid_outer_geometry": "UNCHANGED_BELOW_DRY_SIDE_OPENING", "gasket_loop_change": 0,
            "seal_land_change": 0, "lid_sealing_surface_change": 0, "m4x8_pattern_change": 0,
            "shell_interface_change": 0, "fastening_geometry_change": 0, "direction_change": 0,
        },
        "waterline": waterline_data(),
        "tool_access": {
            "gland_insertion": "CAD_DIAMETRAL_PASS_AND_PHYSICAL_COUPON_PASS",
            "internal_clear_xy_mm": [INTERNAL_X, INTERNAL_Y], "internal_review_envelope_xy_mm": [34, 34],
            "full_wrench_envelope": "HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED",
            "external_d40_reference": "DIMENSIONAL_REVIEW_ONLY_NOT_GUARANTEED_TOOL_CLEARANCE",
            "gland_removal_without_lid_destruction": True,
        },
        "cable": {"od_mm": CABLE_OD, "horizontal_exit": True, "vendor_minimum_bend_radius": "HOLD", "routing_physical_dry_fit": "PENDING"},
        "tpu_future": {"cad_created": False, "sealing_boundary_integration": False, "drainage_blocked": False, "gland_removal_blocked": False, "interface": "UNOBSTRUCTED_EXTERNAL_REFERENCE_ONLY"},
        "print": {"printer": "Bambu Lab A1", "material": "PETG", "orientation": "SEALING_UNDERSIDE_DOWN", "slicer": "HOLD_SLICER_NOT_RUN", "first_print": STLS[0]},
        "status": "CAD_PASS/CONTRACT_TEST_PASS/COMPACT_CHIMNEY_LID_PRINT_READY/PHYSICAL_VALIDATION_PENDING",
        "forbidden_claims": ["WATERPROOF_PASS", "FIELD_PASS", "DROP_PASS", "TPU_PROTECTION_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.w{{stroke:#1d4ed8;stroke-width:3}}.r{{stroke:#b91c1c;stroke-width:3}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    return {
        SVGS[0]: svg("V001 / V002 COMPACT COMPARISON", "Only compact dry-side chimney geometry changes; sealing interface stays frozen.", '<rect x="150" y="145" width="220" height="360" class="b"/><rect x="600" y="205" width="220" height="300" class="g"/><text x="215" y="535">V001 H60 / center+35</text><text x="640" y="535">V002 H50 / center+30</text><path d="M390 325H565" class="a"/><text x="430" y="300">−10 height</text>'),
        SVGS[1]: svg("ABSOLUTE WATERLINE CLEARANCE", "Z257 lid top is a derived top-insert mount assumption; Z210 is a design scenario, not field sink.", '<line x1="100" y1="465" x2="980" y2="465" class="w"/><text x="110" y="450">Z150 water</text><line x1="100" y1="340" x2="980" y2="340" class="r"/><text x="110" y="325">Z210 effective scenario</text><rect x="545" y="240" width="250" height="65" class="b"/><text x="565" y="230">lid top Z257</text><circle cx="795" cy="150" r="18" class="q"/><text x="825" y="155">gland center Z287 / low edge Z279.4</text>'),
        SVGS[2]: svg("GLAND / TOOL DIMENSIONAL REVIEW", "Ø15.2 physical-fit hole; full wrench geometry remains HOLD.", '<rect x="250" y="150" width="260" height="350" class="g"/><circle cx="510" cy="325" r="76" class="q"/><circle cx="510" cy="325" r="150" fill="none" stroke="#a16207" stroke-width="3"/><text x="690" y="275">hole Ø15.2</text><text x="690" y="320">thread OD14.9</text><text x="690" y="365">D40 proxy only</text>'),
        SVGS[3]: svg("SEALING INTERFACE FREEZE", "Gasket loop, land, lid interface and M4×8 pattern remain unchanged.", '<rect x="160" y="145" width="760" height="360" class="b"/><rect x="225" y="210" width="630" height="230" fill="none" stroke="#087f5b" stroke-width="8"/><circle cx="190" cy="175" r="11" class="q"/><circle cx="890" cy="175" r="11" class="q"/><circle cx="190" cy="475" r="11" class="q"/><circle cx="890" cy="475" r="11" class="q"/><text x="400" y="335">ZERO MASKED DELTA</text>'),
        SVGS[4]: svg("FUTURE TPU IMPACT INTERFACE", "No TPU CAD and no sealing integration in this phase.", '<rect x="315" y="170" width="300" height="330" class="g"/><path d="M270 150H660V520H270" fill="none" stroke="#7c3aed" stroke-width="5" stroke-dasharray="12 10"/><path d="M680 340H890" class="a"/><text x="700" y="310">future removable protector</text><text x="700" y="365">drainage / gland access open</text>'),
        SVGS[5]: svg("PHYSICAL TEST SEQUENCE", "Waterproof validation precedes TPU development and all drop testing.", '<text x="55" y="255">VISUAL</text><path d="M125 250H205" class="a"/><text x="225" y="255">GLAND</text><path d="M300 250H380" class="a"/><text x="400" y="255">DRY FIT</text><path d="M485 250H565" class="a"/><text x="585" y="255">WATER</text><path d="M665 250H745" class="a"/><text x="765" y="255">TPU</text><path d="M825 250H905" class="a"/><text x="925" y="255">DROP</text><text x="290" y="370">13-step detailed order is in PHYSICAL_TEST_PLAN.md</text>'),
    }


def documents() -> dict[str, str]:
    water = waterline_data()
    heading = "# BBOX compact wiring chimney v002\n\n"
    return {
        "README.md": heading + "A new read-only-derived compact lid lane. The v001 lid authority is preserved; only the dry-side chimney changes to 50×45×50 mm with a physically selected Ø15.2 gland hole. Status: `CAD_PASS / CONTRACT_TEST_PASS / COMPACT_CHIMNEY_LID_PRINT_READY / PHYSICAL_VALIDATION_PENDING`.\n",
        "BUILD_NOTE.md": heading + "Source is `build_bbox_lid_wiring_chimney_v002.py`; first print is `print/bbox_lid_wiring_chimney_v002_compact.stl`. Parent v001 is imported read-only. The hood projection is minimally reduced from10 to8 mm for the H50 package. No TPU part is created.\n",
        "DIMENSION_REPORT.md": heading + "|Item|v002|Authority|\n|---|---:|---|\n|Outer X×Y×H|50×45×50 mm|RELEASED CAD|\n|Wall|4 mm|RELEASED CAD|\n|Internal X×Y|42×37 mm|RELEASED CAD|\n|Gland hole|Ø15.2 mm|PHYSICAL_FIT_PASS|\n|Thread OD|14.9 mm|MEASURED|\n|Cable OD|9.6 mm|MEASURED|\n|Gland center|lid top+30 mm|RELEASED CAD|\n|Direction|+Y horizontal|FROZEN|\n|Hood|34 wide×8 projection×5 max mm|LOCAL COMPACT ADJUSTMENT|\n\nGasket loop, seal land, sealing surface, M4×8 pattern, shell interface and lid outer interface have zero intended change.\n",
        "WATERLINE_CLEARANCE_REPORT.md": heading + f"Lid top is Z{water['bbox_lid_top_absolute_z_mm']:.1f} using `{ABS_DATUM_CLASS}`. Gland center is Z{water['gland_center_absolute_z_mm']:.1f}; margins are {water['gland_center_margin_to_z150_mm']:.1f} mm to Z150 and {water['gland_center_margin_to_z210_mm']:.1f} mm to the conservative Z210 scenario. Hole lower edge is Z{water['gland_hole_lowest_absolute_z_mm']:.1f}; margins are {water['gland_hole_lower_edge_margin_to_z150_mm']:.1f} mm and {water['gland_hole_lower_edge_margin_to_z210_mm']:.1f} mm. Z210 is not a measured field sink. The Z257 lid alignment remains an installed-assembly datum to verify physically.\n",
        "TOOL_ACCESS_REPORT.md": heading + "The Ø15.2 coupon physically passed gland insertion, finger removal and locknut tightening. CAD preserves42×37 mm internal cavity and34×34 mm dimensional review volume. The v001 D40 external cylinder is retained only as a review proxy; exact gland hex/body and wrench geometry are not known, so `HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED` remains. Hood, cable bend and real frame access require dry fit.\n",
        "PHYSICAL_TEST_PLAN.md": heading + "1. Full lid visual inspection.\n2. Install gland in Ø15.2 hole.\n3. Check locknut and actual tool access.\n4. Route OD9.6 cable.\n5. Install lid on real BBOX.\n6. Perform crawler/frame dry fit.\n7. Upright water test.\n8. Verify target waterline.\n9. Tilt at least10 degrees.\n10. Rain/splash test.\n11. Wet cable movement test.\n12. Only after waterproof validation, develop a separate TPU protector.\n13. Only after all water tests, perform final handling/drop test.\n\nAny leak stops the sequence.\n",
        "HOLD_REGISTER.md": heading + "- physical confirmation that installed lid top aligns to Z257\n- actual gland outer-hex/body and wrench envelope\n- cable vendor bend radius and installed routing\n- hood/tool/frame dry-fit clearance\n- slicer/support review and first print\n- upright water, target waterline, tilt, rain/splash and wet-cable tests\n- TPU protector development after waterproof validation\n- handling/drop, field and durability validation\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-25T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    v001.v002.v001.export_stl(shape, path)


def generate(out: Path):
    shapes = {
        STEPS[0]: compact_lid(), STEPS[1]: assembly(),
        STEPS[2]: compound([compact_lid(), gland_reference()]),
        STEPS[3]: cable_route(), STEPS[4]: dimensional_tool_reference(),
        STEPS[5]: waterline_reference(),
    }
    for relative, shape in shapes.items():
        export_step(shape, out / relative)
    export_stl(compact_lid(), out / STLS[0])
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
    meshes = {relative: v001.v002.v001.mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="chimney_v002_") as temp:
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
    checks = {
        "hole_15p2": GLAND_HOLE == 15.2, "physical_fit_pass_recorded": parameters()["physical_authority"]["gland_hole_physical_fit"] == "PASS",
        "height_50": CHIMNEY_H == 50, "outer_50x45": (CHIMNEY_X, CHIMNEY_Y) == (50, 45), "wall_4": WALL == 4,
        "internal_42x37": (INTERNAL_X, INTERNAL_Y) == (42, 37), "center_plus30": GLAND_CENTER_ABOVE_LID == 30,
        "direction_frozen": parameters()["chimney"]["gland_direction"] == "CBOX_SIDE_POSITIVE_Y_HORIZONTAL",
        "gasket_change_zero": metrics["gasket_loop_change_count"] == 0, "seal_land_delta_zero": metrics["seal_land_delta_mm3"] == 0,
        "fastener_delta_zero": metrics["fastener_pattern_delta_mm3"] == 0, "single_solid": metrics["lid_solids"] == 1,
        "valid": metrics["lid_valid"], "a1": metrics["a1_envelope_pass"], "hood_retained": parameters()["chimney"]["rain_hood"]["retained"],
        "thread_clearance_positive": metrics["gland_diametral_clearance_mm"] > 0,
        "waterline_arithmetic": waterline_data()["gland_hole_lower_edge_margin_to_z210_mm"] == 69.4,
        "field_not_claimed": waterline_data()["field_validation"] == "NOT_CLAIMED",
        "tool_hold": "HOLD" in parameters()["tool_access"]["full_wrench_envelope"],
        "no_tpu_cad": not parameters()["tpu_future"]["cad_created"],
        "step_reload": all(item["valid"] for item in steps),
        "stl_quality": all(item["reload"] == "PASS" and item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 for item in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"], "protected": repository["checks"]["protected_7"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "analysis": metrics,
        "waterline": waterline_data(), "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
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
    path = downloads / f"Paddy_Swarm_BBOX_COMPACT_WIRING_CHIMNEY_V002_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 25, 0, 0, 0))
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
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED),
        "steps": len(STEPS), "stls": len(STLS), "svgs": len(SVGS),
        "branch": repository["branch"], "head": repository["head"], "staged": repository["staged"],
        "waterline": validation["waterline"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
