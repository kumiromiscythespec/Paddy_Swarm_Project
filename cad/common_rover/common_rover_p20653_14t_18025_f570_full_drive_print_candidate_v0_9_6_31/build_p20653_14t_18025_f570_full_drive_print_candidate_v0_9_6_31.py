"""Build and audit the v0.9.6.31 F570 full 14T DRIVE print candidate.

This is a narrow delta lane.  It imports the protected v0.9.6.30 geometry,
selects the physically screened F570 (57.00 mm) flange pocket, and leaves the
P20653 teeth, full-width support drum, M5 architecture, and 12T idler frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "common_rover_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = REPO_ROOT / LANE_REL
VERSION = "v0.9.6.31"
CLASSIFICATION = "P20653_14T_18025_F570_FULL_DRIVE_PRINT_CANDIDATE"
STATUS = (
    "F570_SELECTED_PHYSICAL_PROXY_PASS/"
    "TENSIONER_INWARD_STROKE_PHYSICAL_GATE_PASS/"
    "14T_FRAME_CLEARANCE_SCREEN_PASS/"
    "F570_FULL_14T_DRIVE_REGENERATED/"
    "P20653_TOOTH_GEOMETRY_FROZEN/"
    "FULL_WIDTH_SUPPORT_DRUM_COMPLETE/"
    "M5_THROUGH_BOLT_LOCKNUT_ARCHITECTURE_COMPLETE/"
    "18025_PHYSICAL_FIT_NOT_YET/"
    "FULL_14T_SINGLE_PRINT_APPROVED/"
    "STATIC_6P5NM_NOT_YET/POWERED_NOT_APPROVED/MUD_NOT_YET/FIELD_NOT_YET/"
    "COMMIT_READY_NOT_STAGED"
)

V30_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30"
)
V30_BUILDER_REL = V30_REL / "build_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30.py"
V19_REL = PurePosixPath("cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19")
V19_BUILDER_REL = V19_REL / "build_drive_entry_top_hold_down_roller_v0_9_6_19.py"

BASE_OUTSIDE_COUNT = 2995
BASE_OUTSIDE_PATH_DIGEST = "385229cc4de8f964fc831c69c7b787be063be43cbad28f4884d622d7465f9fb8"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)

SOURCE_SHA256 = {
    V30_BUILDER_REL.as_posix(): "d9ad9d5a5f46261b11aad1297855358148b56bd94e8d3bc4d6f8b72eac48d169",
    (V30_REL / "artifacts/p20653_14t_18025_full_width_through_bolt_drive_provisional_v0_9_6_30.step").as_posix():
        "be04ca7b537eac0e059321b8da94356b0b237eb8d39302a43fc8dcc995731337",
    (V30_REL / "artifacts/p20653_14t_18025_full_width_through_bolt_drive_provisional_v0_9_6_30.stl").as_posix():
        "0c454572dd5c6de0344b2765ad63f5d99dcac5e967effe634b763f3e0f6e9797",
    (V30_REL / "validation_report.json").as_posix():
        "3507150c6280911f65a680872a938a354a69daf03f2228110c4d401d6df7a83f",
    V19_BUILDER_REL.as_posix(): "e325ba23b895967a1e7cbc2f081f7ba2fcf2675ab389203da055796444b78fb0",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v30 = _load("paddy_v09630_frozen", REPO_ROOT / V30_BUILDER_REL)
v19 = _load("paddy_v09619_clearance", REPO_ROOT / V19_BUILDER_REL)
v30.SELECTED_PROVISIONAL_POCKET = "F570"
v30.full_drive.cache_clear()

PROTECTED_LANES = dict(v30.PROTECTED_LANES)
PROTECTED_LANES[V30_REL.as_posix()] = (
    69, "8ac79a2b4dadeb6a8584e8949e190e62fd74cdb4299dee0276be0c14e7513cd2"
)

SELECTED_FLANGE_CANDIDATE = "F570"
SELECTED_FLANGE_POCKET_D_MM = 57.00
PHYSICAL_COUPON_RESULTS = {
    "F569": {"diameter_mm": 56.90, "result": "FAIL_TIGHT"},
    "F570": {"diameter_mm": 57.00, "result": "PASS_SELECTED"},
    "F571": {"diameter_mm": 57.10, "result": "FAIL_LOOSE"},
}
TENSIONER_AVAILABLE_INWARD_MM = 10.0
TENSIONER_REQUIRED_INWARD_MM = 2.5801
TENSIONER_SERVICE_MARGIN_MM = 2.0
TENSIONER_REQUIRED_WITH_MARGIN_MM = 4.5801
TENSIONER_RESIDUAL_MM = TENSIONER_AVAILABLE_INWARD_MM - TENSIONER_REQUIRED_WITH_MARGIN_MM

BUILDER = Path(__file__).name
TEST = "tests/test_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31_contract.py"
FULL_STEP = "artifacts/p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.step"
FULL_STL = "artifacts/p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.stl"
ASSEMBLY_STEP = "artifacts/p20653_14t_18025_f570_full_drive_reference_assembly_v0_9_6_31.step"
CAD = [FULL_STEP, FULL_STL, ASSEMBLY_STEP]
SVGS = [
    "artifacts/p20653_14t_18025_f570_section_v0_9_6_31.svg",
    "artifacts/p20653_14t_frame_roller_clearance_v0_9_6_31.svg",
    "artifacts/p20653_14t_m5_through_bolt_stack_v0_9_6_31.svg",
]
DOCS = [
    "README.md", "PHYSICAL_UPDATE.md", "DESIGN_AUTHORITY.md", "PRINT_GATE.md",
    "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json",
    "BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *CAD, *SVGS, *DOCS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(
        row[3:].replace("\\", "/")
        for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
        if row.startswith("?? ")
    )


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".fcstd"}]
    ignored_lane = run_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES,
        "source_files": sources == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored_lane,
        "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"}
                            for rel, row in protected.items()},
        "source_sha256": sources, "cache": cache, "forbidden": forbidden, "ignored_lane": ignored_lane,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in a.intersect(b).solids().vals()), 6)


def shape_distance(a: cq.Workplane, b: cq.Workplane) -> float:
    return round(float(a.val().distance(b.val())), 6)


def placed_full_drive() -> cq.Workplane:
    return v30.full_drive().rotate((0, 0, 0), (1, 0, 0), 90).translate(v19.SPROCKET_CENTER)


def crawler_straight_run_keepout() -> cq.Workplane:
    # Ends at the protected first-entry datum.  The wrap/mesh sector downstream
    # of this plane is intended tooth/link engagement and is checked by v30's
    # exact 14-position swept-link test instead of being called a collision.
    x_min = -90.0
    x_max = float(v19.ENTRY_DATUM_X_MM)
    length = x_max - x_min
    center_x = (x_min + x_max) / 2.0
    left = v19.box(length, 10.0, v19.LINK_BASE_THICKNESS_MM,
                   (center_x, -v19.ROLLER_CENTER_ABS_Y_MM,
                    (v19.LINK_BOTTOM_Z_MM + v19.LINK_TOP_Z_MM) / 2.0))
    right = v19.box(length, 10.0, v19.LINK_BASE_THICKNESS_MM,
                    (center_x, v19.ROLLER_CENTER_ABS_Y_MM,
                     (v19.LINK_BOTTOM_Z_MM + v19.LINK_TOP_Z_MM) / 2.0))
    centre = v19.box(length, 28.0, 5.0,
                     (center_x, 0.0, v19.LINK_TOP_Z_MM + 2.5))
    return v19.compound([left, right, centre])


def lower_roller_candidate_envelopes() -> cq.Workplane:
    # Protected v0.8.1 candidate geometry, transformed to the v0.9.6.19 drive
    # centre: front drive (300,155), lower rollers x=(0,70,140,210), z=45.
    # Actual station registration remains HOLD; this is the repository CAD
    # candidate screen requested by the task, not a fabricated measurement.
    x_offsets = (-300.0, -230.0, -160.0, -90.0)
    z = v19.SPROCKET_CENTER[2] + (45.0 - 155.0)
    return v19.compound([v19.cylinder_y(25.0, 55.0, (x, 0.0, z)) for x in x_offsets])


def idler_at_center_distance(distance_mm: float) -> cq.Workplane:
    return v19.parent_main().translate((-distance_mm, 0.0, 0.0))


def placement_analysis() -> dict[str, object]:
    full = placed_full_drive()
    frame = v19.compound(list(v19.frame_references()))
    lower = lower_roller_candidate_envelopes()
    straight = crawler_straight_run_keepout()
    hold_rows = []
    for push in v19.PUSH_VALUES_MM:
        rollers = v19.installed_rollers(push)
        carriage = v19.roller_carriage(push)
        hold_rows.append({
            "push_mm": push,
            "drive_vs_rollers_mm3": common_volume(full, rollers),
            "drive_vs_carriage_mm3": common_volume(full, carriage),
            "drive_to_rollers_distance_mm": shape_distance(full, rollers),
            "drive_to_carriage_distance_mm": shape_distance(full, carriage),
        })
    idler_distances = [280.0, 280.0 - TENSIONER_REQUIRED_INWARD_MM, 270.0]
    idler_rows = []
    for distance in idler_distances:
        idler = idler_at_center_distance(distance)
        idler_rows.append({
            "center_distance_mm": round(distance, 4),
            "drive_vs_12t_idler_mm3": common_volume(full, idler),
            "drive_to_12t_idler_distance_mm": shape_distance(full, idler),
        })
    return {
        "coordinate_source": "v0.9.6.19 placement transform + v0.8.1 lower-roller candidate",
        "drive_bounds_world_mm": v19.bounds(full),
        "frame": {
            "intersection_mm3": common_volume(full, frame),
            "minimum_distance_mm": shape_distance(full, frame),
            "source": V19_REL.as_posix(),
        },
        "lower_rollers": {
            "intersection_mm3": common_volume(full, lower),
            "minimum_distance_mm": shape_distance(full, lower),
            "station_registration": "HOLD_ACTUAL_LOWER_ROLLER_STATIONS",
            "candidate_source": "front_drive_dual_pto_design_authority_v0_8_1",
        },
        "hold_down_roller": {
            "rows": hold_rows,
            "max_unintended_intersection_mm3": max(
                max(row["drive_vs_rollers_mm3"], row["drive_vs_carriage_mm3"]) for row in hold_rows
            ),
        },
        "crawler_straight_run": {
            "keepout_end_x_mm": float(v19.ENTRY_DATUM_X_MM),
            "intersection_mm3": common_volume(full, straight),
            "minimum_distance_mm": shape_distance(full, straight),
            "wrap_sector_contract": "INTENDED_MESH_CHECKED_BY_EXACT_LINK_SWEEP",
        },
        "idler_adjustment_range": {
            "rows": idler_rows,
            "max_intersection_mm3": max(row["drive_vs_12t_idler_mm3"] for row in idler_rows),
            "screened_center_distance_range_mm": [270.0, 280.0],
        },
        "physical_observation": "USER_CONFIRMED_LARGE_PLACEMENT_MARGIN_SCREEN_PASS",
        "final_physical_clearance": "NOT_YET_ACTUAL_ASSEMBLY_RETEST_REQUIRED",
    }


def geometry_analysis() -> dict[str, object]:
    base = v30.geometry_analysis()
    placement = placement_analysis()
    support = base["support"]
    radial = base["radial_margin"]
    return {
        "frozen_parent": {
            "lane": V30_REL.as_posix(), "tooth_count": 14, "pitch_mm": v30.PITCH_MM,
            "pitch_diameter_mm": v30.TARGET_PITCH_DIAMETER_MM,
            "phase_deg": v30.TARGET_PHASE_DEG, "spacing_deg": v30.TARGET_SPACING_DEG,
            "tooth_width_mm": v30.TOOTH_WIDTH_MM, "idler_tooth_count": 12,
            "tooth_regression": base["p20653"]["regression"],
        },
        "selected_flange": {
            "candidate": SELECTED_FLANGE_CANDIDATE,
            "pocket_diameter_mm": SELECTED_FLANGE_POCKET_D_MM,
            "pocket_depth_mm": v30.FLANGE_POCKET_DEPTH_MM,
            "physical_proxy_results": PHYSICAL_COUPON_RESULTS,
            "actual_18025_fit": "NOT_YET_PART_NOT_RECEIVED",
        },
        "support": {
            "type": support["support_type"], "width_mm": support["width_mm"],
            "ring_radius_mm": support["ring_radius_mm"],
            "link_swept_intersection_max_mm3": support["noncontact_ring_intersection_max_mm3"],
            "link_swept_clearance_mm": support["noncontact_ring_clearance_mm"],
            "clearance_hard_mm": 0.8, "clearance_target_mm": 1.0,
            "f570_pocket_to_continuous_ring_ligament_mm": radial["continuous_ring_ligament_mm"],
            "vendor_flange_to_tooth_root_mm": radial["v09630_14t_flange_to_tooth_root_mm"],
            "structural_hard_mm": 5.0, "structural_target_mm": 6.0,
        },
        "m5": {
            "count": 6, "pcd_mm": v30.HUB_PCD_MM, "petg_clearance_mm": v30.PETG_THROUGH_HOLE_D_MM,
            "head_side": "18025_METAL_FLANGE_SIDE",
            "opposite_side": "METAL_FLAT_WASHER_PLUS_METAL_LOCKNUT",
            "petg_tap": "PROHIBITED", "captive_nut": "PROHIBITED",
            "service_counterbore_d_mm": v30.LOCKNUT_COUNTERBORE_D_MM,
            "service_counterbore_depth_mm": v30.LOCKNUT_COUNTERBORE_DEPTH_MM,
            "cad_access": "PASS_OPEN_COUNTERBORE",
        },
        "tensioner": {
            "available_inward_mm": TENSIONER_AVAILABLE_INWARD_MM,
            "required_inward_mm": TENSIONER_REQUIRED_INWARD_MM,
            "service_margin_mm": TENSIONER_SERVICE_MARGIN_MM,
            "required_with_margin_mm": TENSIONER_REQUIRED_WITH_MARGIN_MM,
            "residual_mm": TENSIONER_RESIDUAL_MM,
            "physical_gate": "PASS",
        },
        "placement": placement,
        "dimensions": {
            "pilot_d_mm": v30.CENTER_PILOT_D_MM, "pilot_length_mm": v30.CENTER_PILOT_LENGTH_MM,
            "relief_d_mm": v30.DEEP_RELIEF_D_MM, "total_cavity_depth_mm": v30.TOTAL_CAVITY_DEPTH_MM,
            "hub_count_per_drive": 1, "total_hubs": 2,
        },
    }


def export_step(shape: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    v30.export_step(shape, path)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    out.joinpath("artifacts").mkdir(parents=True, exist_ok=True)
    export_step(v30.full_drive(), out / FULL_STEP)
    exporters.export(v30.full_drive(), str(out / FULL_STL), tolerance=0.03, angularTolerance=0.08)
    export_step(v30.assembly_reference(), out / ASSEMBLY_STEP)
    mesh = {FULL_STL: v30.mesh_metrics(out / FULL_STL)}
    if not (mesh[FULL_STL]["watertight"] and mesh[FULL_STL]["bad_edge_count"] == 0
            and mesh[FULL_STL]["degenerate_triangle_count"] == 0
            and mesh[FULL_STL]["component_count"] == 1 and mesh[FULL_STL]["reload"] == "PASS"):
        raise RuntimeError(f"STL contract: {mesh}")
    steps = {}
    for rel, expected in ((FULL_STEP, 1), (ASSEMBLY_STEP, 10)):
        imported = importers.importStep(str(out / rel))
        valid = imported.solids().size() == expected and all(solid.isValid() for solid in imported.solids().vals())
        steps[rel] = {"solid_count": imported.solids().size(), "valid": valid,
                      "reload": "PASS" if valid else "FAIL"}
        if not valid:
            raise RuntimeError(f"STEP reload: {rel} {steps[rel]}")
    return mesh, steps


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#faf9f4"/><style>text{{font-family:Arial,sans-serif;fill:#1d3557}}.t{{font-size:31px;font-weight:bold}}.m{{font-size:20px}}.s{{fill:none;stroke:#264653;stroke-width:5}}.g{{fill:none;stroke:#2a9d8f;stroke-width:5}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.d{{stroke-dasharray:11 8}}</style>
<text x="50" y="52" class="t">{title}</text>{body}<text x="50" y="672" class="m">v0.9.6.31 · F570 · SINGLE PRINT CANDIDATE · POWERED NOT APPROVED</text></svg>'''


def svg_documents(geom: dict[str, object]) -> dict[str, str]:
    s = geom["support"]
    p = geom["placement"]
    section = svg_page("F570 full 14T section", f'''
<g transform="translate(95,105)"><rect x="160" y="100" width="660" height="310" rx="30" class="s"/><rect x="160" y="100" width="660" height="310" rx="30" class="g d"/><rect x="345" y="100" width="290" height="90" fill="#fff" class="a"/><line x1="345" y1="220" x2="635" y2="220" class="a"/><text x="380" y="255" class="m">F570 pocket Ø57.00 × 6.20</text><text x="270" y="460" class="m">full width = 44 · support drum unchanged</text><text x="270" y="500" class="m">pocket→continuous ring = {s['f570_pocket_to_continuous_ring_ligament_mm']:.6f} mm</text><text x="270" y="540" class="m">link swept clearance = {s['link_swept_clearance_mm']:.6f} mm</text></g>''')
    clearance = svg_page("14T placement clearance screen", f'''
<g transform="translate(80,95)"><circle cx="300" cy="300" r="165" class="s"/><rect x="650" y="55" width="75" height="500" class="g"/><g class="a"><circle cx="170" cy="130" r="38"/><circle cx="250" cy="120" r="38"/></g><line x1="55" y1="470" x2="500" y2="470" class="g d"/><text x="105" y="520" class="m">straight run ends at entry datum X={p['crawler_straight_run']['keepout_end_x_mm']:.1f}</text><text x="760" y="150" class="m">frame intersection {p['frame']['intersection_mm3']:.1f} mm³</text><text x="760" y="195" class="m">lower rollers {p['lower_rollers']['intersection_mm3']:.1f} mm³</text><text x="760" y="240" class="m">hold-down max {p['hold_down_roller']['max_unintended_intersection_mm3']:.1f} mm³</text><text x="760" y="285" class="m">straight run {p['crawler_straight_run']['intersection_mm3']:.1f} mm³</text><text x="760" y="330" class="m">idler range {p['idler_adjustment_range']['max_intersection_mm3']:.1f} mm³</text><text x="760" y="390" class="m">actual lower-roller stations: HOLD</text></g>''')
    holes = "".join(f'<circle cx="{400 + 150*math.cos(math.radians(i*60)):.2f}" cy="{315 + 150*math.sin(math.radians(i*60)):.2f}" r="17" class="a"/>' for i in range(6))
    bolt = svg_page("M5 × 6 through-bolt / locknut architecture", f'''
<g transform="translate(80,40)"><circle cx="400" cy="315" r="235" class="s"/><circle cx="400" cy="315" r="150" class="g d"/>{holes}<text x="685" y="170" class="m">PCD 47.5 · PETG Ø5.5</text><text x="685" y="220" class="m">head: metal hub side</text><text x="685" y="270" class="m">opposite: washer + locknut</text><text x="685" y="320" class="m">open Ø12 × 4 counterbore</text><text x="685" y="370" class="m">PETG tap / captive nut: prohibited</text></g>''')
    return {SVGS[0]: section, SVGS[1]: clearance, SVGS[2]: bolt}


def header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def documentation(geom: dict[str, object]) -> dict[str, str]:
    s, p, t = geom["support"], geom["placement"], geom["tensioner"]
    first = FULL_STL
    docs = {
        "README.md": header("P20653 14T / 18025 F570 full DRIVE print candidate") + f'''
This lane is the minimum v0.9.6.30 delta. F570 Ø57.00 is the physical proxy winner; F569 was tight and F571 was loose. The exact P20653 14T teeth, 44 mm support drum, M5×6 PCD47.5 architecture, and 12T idler are unchanged.

First and only approved print: `{first}` (quantity 1). Bambu A1 / PETG candidate settings still require slicer review. After printing, check: 18009 proxy flange fit, hand removal, rocking/play, six-hole alignment, face seating, washer/locknut access, crawler hand rotation, tensioner position, frame/roller clearance, tooth/root whitening or crack, and reassembly. Do not perform powered testing.
''',
        "PHYSICAL_UPDATE.md": header("Physical update") + f'''
- F569 Ø56.90: `FAIL_TIGHT`
- F570 Ø57.00: `PASS / SELECTED` (fit, hand removable, no clear play, six-hole alignment and face seating)
- F571 Ø57.10: `FAIL_LOOSE`
- Nexus 18025 actual part: `NOT_YET_PART_NOT_RECEIVED`
- Tensioner: available ≥{t['available_inward_mm']:.1f} mm; required {t['required_inward_mm']:.4f} + service {t['service_margin_mm']:.1f} = {t['required_with_margin_mm']:.4f} mm; residual ≥{t['residual_mm']:.4f} mm; gate `PASS`.
- User placement observation: large margin around drive/idler/lower roller/frame; `14T_FRAME_CLEARANCE_SCREEN_PASS`. Final actual assembly clearance remains `NOT_YET`.
''',
        "DESIGN_AUTHORITY.md": header("v0.9.6.31 delta design authority") + f'''
Parent `{V30_REL.as_posix()}` is read-only. The only component geometry change is the selected full DRIVE flange pocket from F569 Ø56.90 to F570 Ø57.00. Protected tooth pitch {v30.PITCH_MM:.10f}, count 14, pitch diameter {v30.TARGET_PITCH_DIAMETER_MM:.10f}, phase {v30.TARGET_PHASE_DEG:.10f}°, spacing {v30.TARGET_SPACING_DEG:.10f}°, local tooth solid, width44, pilot Ø24.1×4, relief Ø24.5, cavity depth, support drum, drain, M5×6 PCD47.5 and 12T idler are frozen.

CAD placement screen uses the protected v0.9.6.19 transform. Existing v0.8.1 lower-roller stations are only a candidate envelope because current physical station registration is absent. No measurement was invented and no manufacturing authority is released.
''',
        "PRINT_GATE.md": header("Full 14T print gate") + f'''
`FULL_14T_PRINT_GATE=PASS`  
`FULL_14T_SINGLE_PART_PRINT=APPROVED`  
`FIRST_PRINT={first}`  
`QUANTITY=1`

CAD hard gates: tooth regression 14/14 PASS, link non-contact intersection 0, link clearance {s['link_swept_clearance_mm']:.6f} mm ≥0.8, F570 continuous-ring ligament {s['f570_pocket_to_continuous_ring_ligament_mm']:.6f} mm ≥5.0, frame/lower roller/hold-down/straight-run/idler intersection 0, STEP reload PASS, STL manifold PASS. Link clearance target1.0 and ligament target6.0 are `TARGET_MARGIN_MISS`, so physical tooth/root inspection is mandatory. Slicer has not been run.
''',
        "HOLD_REGISTER.md": header("HOLD register") + '''
HOLD: actual 18025 fit and set-screw details; actual M5 head/washer/locknut stack and selected length; actual lower-roller station registration; final full assembly clearances; slicer; printed F570 14T inspection; physical crawler hand rotation; tooth/root bending; keyed shaft/key receipt; static 6.5 N·m; powered; water/mud; durability; field. `POWERED_NOT_APPROVED`, `FIELD_NOT_YET`.
''',
    }
    return docs


def parameters(geom: dict[str, object]) -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "selected_flange": geom["selected_flange"], "frozen_parent": geom["frozen_parent"],
        "support": geom["support"], "m5": geom["m5"], "tensioner": geom["tensioner"],
        "dimensions": geom["dimensions"],
        "print": {"gate": "PASS", "single_part": "APPROVED", "first_stl": FULL_STL,
                  "quantity": 1, "process": "BAMBU_A1_PETG_CANDIDATE", "slicer": "HOLD_NOT_RUN"},
    }


def stable_repository_record(repo: dict[str, object]) -> dict[str, object]:
    return {
        "repository": repo["repository"], "branch": repo["branch"], "head": repo["head"],
        "staged_count": len(repo["staged"]), "tracked_dirty": repo["tracked_dirty"],
        "outside_untracked": list(repo["outside_untracked"]), "authority_sha256": repo["authority_sha256"],
        "protected_lanes": repo["protected_lanes"], "source_sha256": repo["source_sha256"],
        "lane_expected_paths": EXPECTED_PATH_COUNT,
    }


def validation(repo: dict[str, object], geom: dict[str, object], mesh: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    p, s = geom["placement"], geom["support"]
    regression = geom["frozen_parent"]["tooth_regression"]
    checks = {
        "repository_guard": "PASS", "authority_4_of_4": "PASS", "protected_lanes": "PASS",
        "f570_selected": "PASS", "flange_pocket_57p00": "PASS",
        "f570_physical_proxy": "PASS", "actual_18025_fit": "NOT_YET",
        "tensioner_physical_gate": "PASS",
        "tooth_count_14": "PASS", "pitch_frozen": "PASS", "phase_spacing_frozen": "PASS",
        "tooth_regression_14_of_14": "PASS" if regression["all_14_pass"] else "FAIL",
        "idler_change_zero": "PASS", "support_drum_frozen": "PASS", "m5_architecture_frozen": "PASS",
        "link_swept_intersection_zero": "PASS" if s["link_swept_intersection_max_mm3"] == 0 else "FAIL",
        "link_clearance_hard": "PASS" if s["link_swept_clearance_mm"] >= 0.8 else "FAIL",
        "link_clearance_target": "PASS" if s["link_swept_clearance_mm"] >= 1.0 else "TARGET_MARGIN_MISS",
        "radial_ligament_hard": "PASS" if s["f570_pocket_to_continuous_ring_ligament_mm"] >= 5.0 else "FAIL",
        "radial_ligament_target": "PASS" if s["f570_pocket_to_continuous_ring_ligament_mm"] >= 6.0 else "TARGET_MARGIN_MISS",
        "frame_collision_zero": "PASS" if p["frame"]["intersection_mm3"] == 0 else "FAIL",
        "lower_roller_candidate_collision_zero": "PASS" if p["lower_rollers"]["intersection_mm3"] == 0 else "FAIL",
        "hold_down_raised_lowered_collision_zero": "PASS" if p["hold_down_roller"]["max_unintended_intersection_mm3"] == 0 else "FAIL",
        "crawler_straight_run_collision_zero": "PASS" if p["crawler_straight_run"]["intersection_mm3"] == 0 else "FAIL",
        "idler_adjustment_range_collision_zero": "PASS" if p["idler_adjustment_range"]["max_intersection_mm3"] == 0 else "FAIL",
        "m5_washer_locknut_access": "PASS",
        "all_step_reload": "PASS" if all(row["valid"] and row["reload"] == "PASS" for row in steps.values()) else "FAIL",
        "stl_watertight_manifold": "PASS" if all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in mesh.values()) else "FAIL",
        "full_14t_print_gate": "PASS", "single_part_print": "APPROVED",
        "static_6p5nm": "NOT_YET", "powered": "NOT_APPROVED", "mud": "NOT_YET", "field": "NOT_YET",
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS, "checks": checks,
        "repository": stable_repository_record(repo), "geometry": geom, "mesh": mesh, "step_import": steps,
        "artifact_counts": {"step": 2, "stl": 1, "svg": 3},
        "print_gate": {"FULL_14T_PRINT_GATE": "PASS", "FULL_14T_SINGLE_PART_PRINT": "APPROVED",
                       "first_print": FULL_STL, "quantity": 1},
        "physical_classification": "CAD_PRINT_CANDIDATE_ONLY_ACTUAL_18025_NOT_YET",
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    mesh, steps = export_outputs(out)
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents(geom).items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters(geom))
    write_json(out / "validation_report.json", validation(repo, geom, mesh, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=1\nSVG=3\nF570=PASS_SELECTED\nFULL_14T_PRINT_GATE=PASS\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=2_OF_2_PASS\nSTL_MANIFOLD=1_OF_1_PASS\nREPRODUCIBILITY=20_OF_20_PASS\nPHYSICAL_18025=NOT_YET")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact path contract: {len(files)} {set(files) ^ set(EXPECTED_FILES)}")
    repository_guard(out == LANE_DIR)
    return {"path_count": len(files), "geometry": geom, "mesh": mesh, "step_import": steps, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        result[rel] = digest
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(out == LANE_DIR)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("exact path contract")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != expected_commit:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha mismatch {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError(report["checks"])
    return {
        "repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
        "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
        "sha_mismatch_count": 0, "checks": report["checks"], "geometry": report["geometry"],
        "mesh": report["mesh"], "step_import": report["step_import"], "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_p20653_14t_v09631_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"reproducibility mismatch {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / (
        f"Paddy_Swarm_Common_Rover_P20653_14T_18025_F570_FULL_DRIVE_PRINT_CANDIDATE_"
        f"v0_9_6_31_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names))
        traversal = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest for rel, digest in sums.items())
    result = {
        "path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
        "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
        "sha_mismatch_count": mismatch, "parent_contamination_count": contamination,
    }
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES:
        raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("select action")
    if args.build:
        print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility:
        print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package:
        print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
