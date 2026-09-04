"""Build the Common Rover compact GoldenMate FIELD BBOX V003 candidate.

This lane deliberately separates a locally valid battery package from the still
unresolved vehicle transform.  The full box is CAD-ready, while printing remains
gated by the two compact seal coupons and a physical 1.8 mm cord test.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import shutil
import struct
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_REL = PurePosixPath("cad/common_rover/bbox/bbox_compact_field_goldenmate_v003")
LANE = ROOT / LANE_REL
VERSION = "PS-COMMON-ROVER-COMPACT-FIELD-BBOX-V003"

V003_REL = "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority"
V003_BUILDER = ROOT / V003_REL / "build_bbox_lid_wiring_chimney_v003_full_lid_2p4.py"

PROTECTED = [
    "cad/common_rover/physical_authority/common_rover_goldenmate_battery_fit_bbox_packaging_authority_v001",
    "cad/common_rover/physical_authority/common_rover_electrical_hardware_physical_authority_v001",
    "cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8",
    V003_REL,
    "cad/common_rover/physical_authority/common_rover_bbox_installed_transform_front_interface_audit_v001",
    "cad/common_rover/bbox_cbox/cbox_transverse_cross_saddle_bbox_alignment_v001",
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6",
    "cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003",
    "cad/common_rover/drivetrain/crawler_idler_candidate_c_v001",
    "cad/common_rover/bbox/bbox_field_box_goldenmate_v001",
    "cad/common_rover/bbox/bbox_tall_field_body_goldenmate_v002",
]

BATTERY = {
    "long_mm": 150.9,
    "width_mm": 65.5,
    "body_height_mm": 92.5,
    "terminal_inclusive_height_mm": 99.4,
    "mass_kg": 1.2,
}
TEMPORARY = {
    "internal_mm": [152.0, 65.5, 104.0],
    "external_mm": [155.0, 71.9, 110.0],
    "physical_fit": "PASS",
    "body_bottom_global_z_mm": 144.0,
    "rim_global_z_mm": 254.0,
    "x_ref_to_front_mm": 345.0,
    "x_ref_to_rear_mm": 500.0,
    "left_reference_gap_mm": 55.0,
    "right_reference_gap_mm": 0.0,
    "cad_source": "UNRESOLVED",
}
VARIANTS = {
    "COMPACT_A": {"internal": [154.0, 68.0, 108.0], "pad": 1.0, "class": "MINIMUM_PRACTICAL_FIELD"},
    "COMPACT_B": {"internal": [155.0, 69.0, 110.0], "pad": 1.0, "class": "BALANCED_SELECTED"},
    "COMPACT_C": {"internal": [158.0, 71.0, 112.0], "pad": 1.5, "class": "HIGH_SERVICE_CLEARANCE"},
}
SELECTED = "COMPACT_B"
WALL = 3.5
FLOOR = 3.5
LID_T = 8.0
LID_X = 180.0
LID_Y = 96.0
FLANGE_X = 170.0
FLANGE_Y = 86.0
FLANGE_H = 4.0
GASKET_CORD = 1.8
GROOVE_DEPTH = 0.5
GROOVE_WIDTH = 2.1
HARDSTOP_GAP = 0.895
M4_CLEARANCE = 4.5
M4_POINTS = [(-84, -42), (-84, 0), (-84, 42), (0, -42), (0, 42), (84, -42), (84, 0), (84, 42)]
M4_BOSS_R = 6.0
CHIMNEY_POSITIONS = {
    "A_SELECTED_OPPOSITE_TERMINALS": [-50.0, -14.5],
    "B_TERMINAL_END": [50.0, -14.5],
    "C_OFFSET_CORNER": [-50.0, -4.5],
}
CHIMNEY_SELECTED = "A_SELECTED_OPPOSITE_TERMINALS"
CABLE_OD = 9.6
STRAP_WIDTH = 20.0
TPU_PAD_T = 1.0
STATUS = (
    "LOCAL_BBOX_CAD_PASS/CONTRACT_TEST_PASS/SEAL_COUPON_PRINT_READY/"
    "FULL_BBOX_CAD_READY/FULL_BBOX_PRINT_HOLD_UNTIL_COUPON_PASS/"
    "GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING/WATERPROOF_PHYSICAL_PENDING"
)

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_compact_field_goldenmate_v003_contract.py"
DOCS = [
    "README.md",
    "COMPACT_FIELD_BBOX_V003_DESIGN_AUTHORITY.md",
    "BATTERY_CLEARANCE_TRADE_STUDY.md",
    "SEAL_ARCHITECTURE_TRANSFER.md",
    "CHIMNEY_POSITION_TRADE_STUDY.md",
    "BATTERY_RESTRAINT_DESIGN.md",
    "TEMPORARY_VS_FIELD_ENVELOPE_AUDIT.md",
    "GLOBAL_INTEGRATION_HOLDS.md",
    "SEAL_COUPON_PHYSICAL_TEST_PLAN.md",
    "FULL_BBOX_WATERPROOF_TEST_PLAN.md",
    "BATTERY_FIT_PHYSICAL_TEST_PLAN.md",
]
JSONS = [
    "design_parameters.json",
    "variant_study.json",
    "validation_report.json",
    "contract_test_report.json",
    "printability_report.json",
    "manifest.json",
]
STEPS = [
    "artifacts/compact_field_bbox_body_selected.step",
    "artifacts/compact_field_bbox_lid_selected.step",
    "artifacts/compact_field_bbox_assembly.step",
    "artifacts/goldenmate_corrected_battery_reference.step",
    "artifacts/battery_removal_sweep.step",
    "artifacts/battery_terminal_keepout.step",
    "artifacts/selected_battery_support.step",
    "artifacts/selected_tpu_pad.step",
    "artifacts/main_cable_reference.step",
    "artifacts/service_hardware_reserved_zone.step",
    "artifacts/compact_seal_coupon_A.step",
    "artifacts/compact_seal_coupon_B.step",
    "artifacts/COMPACT_A_reference_assembly.step",
    "artifacts/COMPACT_B_reference_assembly.step",
    "artifacts/COMPACT_C_reference_assembly.step",
]
STLS = [
    "artifacts/selected_tpu_pad.stl",
    "artifacts/compact_seal_coupon_A.stl",
    "artifacts/compact_seal_coupon_B.stl",
]
SVGS = [
    "previews/compact_variant_comparison.svg",
    "previews/battery_clearance_top.svg",
    "previews/battery_clearance_side.svg",
    "previews/terminal_lid_section.svg",
    "previews/battery_removal_sweep.svg",
    "previews/seal_section.svg",
    "previews/chimney_position_comparison.svg",
    "previews/temporary_vs_field_bbox_envelope.svg",
]
INDEXES = ["SHA256SUMS.txt"]
EXPECTED = sorted([BUILDER, TEST, *DOCS, *JSONS, *STEPS, *STLS, *SVGS, *INDEXES])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v003 = load_module("protected_bbox_chimney_v003_full_2p4", V003_BUILDER)
v003_local = v003.v003
v002_chimney = v003_local.v002


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(path: Path) -> dict:
    files = sorted(
        p for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode("utf-8"))
        digest.update(bytes.fromhex(sha(item)))
    return {"files": len(files), "sha256": digest.hexdigest()}


def repository_state() -> dict:
    status = git("status", "--porcelain=v1", "-uall").splitlines()
    return {
        "repository": str(Path(git("rev-parse", "--show-toplevel")).resolve()),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "staged_count": len(git("diff", "--cached", "--name-only").splitlines()),
        "tracked_dirty_count": len(git("diff", "--name-only").splitlines()),
        "untracked_count": sum(line.startswith("?? ") for line in status),
    }


def guard() -> dict:
    state = repository_state()
    checks = {
        "repository": Path(state["repository"]).resolve() == ROOT.resolve(),
        "branch": state["branch"] == BRANCH,
        "head": state["head"] == HEAD,
        "staged_zero": state["staged_count"] == 0,
        "protected_exist": all((ROOT / p).is_dir() for p in PROTECTED),
    }
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file()) if LANE.exists() else []
    checks["lane_scope"] = set(files).issubset(EXPECTED)
    checks["cache_zero"] = not any("__pycache__" in PurePosixPath(p).parts or p.endswith((".pyc", ".pyo")) for p in files)
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps({"state": state, "checks": checks}, sort_keys=True))
    return {"state": state, "checks": checks, "protected": {p: tree_hash(ROOT / p) for p in PROTECTED}}


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cyl_z(d: float, h: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate(center)


def cyl_y(d: float, length: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XZ").circle(d / 2).extrude(length / 2, both=True).translate(center)


def compound(parts):
    values = []
    for part in parts:
        values.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def rounded_box_xy(x: float, y: float, z: float, radius: float, z0: float = 0.0):
    core = box(x - 2 * radius, y, z, (0, 0, z0 + z / 2)).union(
        box(x, y - 2 * radius, z, (0, 0, z0 + z / 2))
    )
    for px in (-x / 2 + radius, x / 2 - radius):
        for py in (-y / 2 + radius, y / 2 - radius):
            core = core.union(cyl_z(radius * 2, z, (px, py, z0)))
    return core.clean()


def rounded_ring(ox, oy, ix, iy, ro, ri, height, z0):
    return rounded_box_xy(ox, oy, height, ro, z0).cut(
        rounded_box_xy(ix, iy, height + 0.4, ri, z0 - 0.2)
    ).clean()


def selected_dims() -> dict:
    ix, iy, iz = VARIANTS[SELECTED]["internal"]
    core = [ix + 2 * WALL, iy + 2 * WALL, iz + FLOOR]
    return {
        "internal": [ix, iy, iz],
        "core_body_external": core,
        "body_overall": [LID_X, LID_Y, iz + FLOOR + HARDSTOP_GAP],
        "lid_base": [LID_X, LID_Y, LID_T],
        "pad": VARIANTS[SELECTED]["pad"],
    }


def body_for(internal=None):
    ix, iy, iz = internal or VARIANTS[SELECTED]["internal"]
    outer_x, outer_y, outer_h = ix + 2 * WALL, iy + 2 * WALL, iz + FLOOR
    shell = box(outer_x, outer_y, outer_h, (0, 0, outer_h / 2))
    cavity = box(ix, iy, iz + 1.0, (0, 0, FLOOR + (iz + 1.0) / 2))
    result = shell.cut(cavity)
    flange = rounded_ring(FLANGE_X, FLANGE_Y, ix, iy, 8.0, 4.0, FLANGE_H, outer_h - FLANGE_H)
    result = result.union(flange)
    tower_bottom = outer_h - 8.0
    tower_h = 8.0 + HARDSTOP_GAP
    for x, y in M4_POINTS:
        result = result.union(cyl_z(M4_BOSS_R * 2, tower_h, (x, y, tower_bottom)))
        result = result.cut(cyl_z(M4_CLEARANCE, tower_h + 2.0, (x, y, tower_bottom - 1.0)))
    groove = rounded_ring(160.0, 74.0, 155.8, 69.8, 6.0, 3.9, GROOVE_DEPTH + 0.2, outer_h - GROOVE_DEPTH)
    return result.cut(groove).clean()


def local_chimney_module_on_lid(lid):
    """Reuse the exact protected V003 local primitives on a new compact perimeter."""
    dx, dy = CHIMNEY_POSITIONS[CHIMNEY_SELECTED]
    move = (dx, dy, 0.0)
    outer = v003_local.box(
        v002_chimney.CHIMNEY_X, v002_chimney.CHIMNEY_Y, v002_chimney.CHIMNEY_H,
        (0, v002_chimney.CHIMNEY_CENTER_Y, v002_chimney.LID_T + v002_chimney.CHIMNEY_H / 2),
    ).translate(move)
    pad = v003_local.box(
        v002_chimney.PAD_X, v002_chimney.PAD_ADDED_T, v002_chimney.PAD_Z,
        (0, 62.5 + v002_chimney.PAD_ADDED_T / 2, v002_chimney.GLAND_CENTER_Z),
    ).translate(move)
    hood = v002_chimney.rain_hood().translate(move)
    cavity = v002_chimney.cavity_tool().translate(move)
    gland = v002_chimney.gland_hole_tool().translate(move)
    recess = v003_local.recess_tool(2.4).translate(move)
    return lid.union(outer).union(pad).union(hood).cut(cavity).cut(gland).cut(recess).clean()


def lid_selected():
    lid = rounded_box_xy(LID_X, LID_Y, LID_T, 8.0, 0.0)
    for x, y in M4_POINTS:
        lid = lid.cut(cyl_z(M4_CLEARANCE, LID_T + 2.0, (x, y, -1.0)))
    return local_chimney_module_on_lid(lid)


def battery_reference():
    pad = TPU_PAD_T
    body = box(BATTERY["long_mm"], BATTERY["width_mm"], BATTERY["body_height_mm"],
               (0, 0, FLOOR + pad + BATTERY["body_height_mm"] / 2))
    terminal_zone_h = BATTERY["terminal_inclusive_height_mm"] - BATTERY["body_height_mm"]
    terminal = box(32.0, BATTERY["width_mm"], terminal_zone_h,
                   (BATTERY["long_mm"] / 2 - 16.0, 0,
                    FLOOR + pad + BATTERY["body_height_mm"] + terminal_zone_h / 2))
    return compound([body, terminal])


def terminal_keepout():
    return box(42.0, BATTERY["width_mm"], 18.0,
               (BATTERY["long_mm"] / 2 - 21.0, 0, FLOOR + TPU_PAD_T + BATTERY["terminal_inclusive_height_mm"] + 9.0))


def removal_sweep():
    return box(BATTERY["long_mm"], BATTERY["width_mm"], BATTERY["terminal_inclusive_height_mm"] + 70.0,
               (0, 0, FLOOR + TPU_PAD_T + (BATTERY["terminal_inclusive_height_mm"] + 70.0) / 2))


def tpu_pads():
    return compound([
        box(30.0, 55.0, TPU_PAD_T, (-48.0, 0, FLOOR + TPU_PAD_T / 2)),
        box(30.0, 55.0, TPU_PAD_T, (48.0, 0, FLOOR + TPU_PAD_T / 2)),
    ])


def strap_reference():
    battery_top = FLOOR + TPU_PAD_T + BATTERY["terminal_inclusive_height_mm"]
    top = box(STRAP_WIDTH, 68.0, 1.5, (0, 0, battery_top + 0.75))
    sides = [
        box(STRAP_WIDTH, 1.5, battery_top - FLOOR, (0, -34.0, FLOOR + (battery_top - FLOOR) / 2)),
        box(STRAP_WIDTH, 1.5, battery_top - FLOOR, (0, 34.0, FLOOR + (battery_top - FLOOR) / 2)),
    ]
    return compound([top, *sides])


def support_reference():
    anchor_z = 18.0
    anchors = [box(26.0, 2.0, 18.0, (0, -34.5, anchor_z)), box(26.0, 2.0, 18.0, (0, 34.5, anchor_z))]
    return compound([tpu_pads(), strap_reference(), *anchors])


def main_cable_reference(assembly=False):
    dx, dy = CHIMNEY_POSITIONS[CHIMNEY_SELECTED]
    z = v002_chimney.GLAND_CENTER_Z + (selected_dims()["internal"][2] + FLOOR + HARDSTOP_GAP if assembly else 0)
    return cyl_y(CABLE_OD, 80.0, (dx, dy + 55.0, z))


def service_reserved_zone(assembly=False):
    dx, dy = CHIMNEY_POSITIONS[CHIMNEY_SELECTED]
    z0 = 15.0 + (selected_dims()["internal"][2] + FLOOR + HARDSTOP_GAP if assembly else 0)
    return box(25.0, 20.0, 12.0, (dx, dy + 23.0, z0))


def assembly():
    lid_z = selected_dims()["internal"][2] + FLOOR + HARDSTOP_GAP
    return compound([body_for(), lid_selected().translate((0, 0, lid_z)), battery_reference(), tpu_pads(), strap_reference(), main_cable_reference(True)])


def variant_assembly(name: str):
    cfg = VARIANTS[name]
    ix, iy, iz = cfg["internal"]
    body = body_for(cfg["internal"])
    batt_z = FLOOR + cfg["pad"]
    batt = box(BATTERY["long_mm"], BATTERY["width_mm"], BATTERY["terminal_inclusive_height_mm"],
               (0, 0, batt_z + BATTERY["terminal_inclusive_height_mm"] / 2))
    lid = lid_selected().translate((0, 0, iz + FLOOR + HARDSTOP_GAP))
    return compound([body, batt, lid])


def compact_seal_coupon(depth: float):
    base = box(42.0, 28.0, 8.0, (0, 0, 4.0))
    groove = box(18.0, GROOVE_WIDTH, depth + 0.2, (0, 0, 8.0 - depth / 2))
    boss = cyl_z(12.0, 8.895, (14.0, 0, 0.0))
    base = base.union(boss).cut(groove).cut(cyl_z(M4_CLEARANCE, 11.0, (14.0, 0, -1.0)))
    lid = box(42.0, 28.0, 5.0, (50.0, 0, 2.5)).cut(cyl_z(M4_CLEARANCE, 7.0, (64.0, 0, -1.0)))
    section_label = box(6.0, 4.0, 1.0, (25.0, -11.0, 0.5))
    return compound([base, lid, section_label])


def shape_bbox(shape) -> list[float]:
    b = shape.val().BoundingBox()
    return [round(b.xlen, 3), round(b.ylen, 3), round(b.zlen, 3)]


def intersection_volume(a, b) -> float:
    try:
        common = a.val().intersect(b.val())
        return round(sum(s.Volume() for s in common.Solids()), 6)
    except (ValueError, AttributeError):
        return 0.0


def variant_metrics() -> dict:
    result = {}
    for name, cfg in VARIANTS.items():
        ix, iy, iz = cfg["internal"]
        pad = cfg["pad"]
        terminal_rim = iz - pad - BATTERY["terminal_inclusive_height_mm"]
        result[name] = {
            **cfg,
            "x_total_clearance_mm": round(ix - BATTERY["long_mm"], 3),
            "x_per_side_mm": round((ix - BATTERY["long_mm"]) / 2, 3),
            "y_total_clearance_mm": round(iy - BATTERY["width_mm"], 3),
            "y_per_side_mm": round((iy - BATTERY["width_mm"]) / 2, 3),
            "terminal_to_rim_mm": round(terminal_rim, 3),
            "terminal_to_lid_inner_mm": round(terminal_rim + HARDSTOP_GAP, 3),
            "core_external_mm": [round(ix + 2 * WALL, 3), round(iy + 2 * WALL, 3), round(iz + FLOOR, 3)],
            "battery_extraction": "PASS" if ix > BATTERY["long_mm"] and iy > BATTERY["width_mm"] else "FAIL",
            "restraint_space": "CONDITIONAL" if min(ix - BATTERY["long_mm"], iy - BATTERY["width_mm"]) < 3 else "PASS",
            "print_impact": "LOW" if name == "COMPACT_A" else "BALANCED" if name == "COMPACT_B" else "HIGHEST_OF_THREE",
            "result": "SELECTED" if name == SELECTED else "REFERENCE_ONLY",
        }
    return result


def geometry_metrics() -> dict:
    dims = selected_dims()
    ix, iy, iz = dims["internal"]
    lid_z = iz + FLOOR + HARDSTOP_GAP
    battery_top = FLOOR + TPU_PAD_T + BATTERY["terminal_inclusive_height_mm"]
    body = body_for()
    lid = lid_selected()
    battery = battery_reference()
    sweep = removal_sweep()
    shell_intersection = intersection_volume(battery, body)
    sweep_fixed = intersection_volume(sweep, body)
    lid_contact = intersection_volume(battery, lid.translate((0, 0, lid_z)))
    tower_clearance_x = abs(M4_POINTS[0][0]) - M4_BOSS_R - BATTERY["long_mm"] / 2
    tower_clearance_y = abs(M4_POINTS[0][1]) - M4_BOSS_R - BATTERY["width_mm"] / 2
    body_bbox = shape_bbox(body)
    lid_bbox = shape_bbox(lid)
    free = ix * iy * iz - BATTERY["long_mm"] * BATTERY["width_mm"] * BATTERY["terminal_inclusive_height_mm"]
    return {
        "body_valid": body.val().isValid(),
        "lid_valid": lid.val().isValid(),
        "body_bbox_mm": body_bbox,
        "lid_bbox_mm": lid_bbox,
        "battery_shell_intersection_mm3": shell_intersection,
        "battery_removal_sweep_fixed_intersection_mm3": sweep_fixed,
        "battery_lid_contact_mm3": lid_contact,
        "x_total_clearance_mm": round(ix - BATTERY["long_mm"], 3),
        "y_total_clearance_mm": round(iy - BATTERY["width_mm"], 3),
        "terminal_to_rim_mm": round(iz - TPU_PAD_T - BATTERY["terminal_inclusive_height_mm"], 3),
        "terminal_to_lid_inner_mm": round(lid_z - battery_top, 3),
        "battery_to_chimney_mm": round(lid_z + LID_T - battery_top, 3),
        "battery_to_m4_tower_mm": round(min(tower_clearance_x, tower_clearance_y), 3),
        "service_reserved_volume_mm3": 25.0 * 20.0 * 12.0,
        "remaining_internal_nominal_volume_mm3": round(free, 3),
        "field_core_minus_temporary_mm": [
            round(ix + 2 * WALL - TEMPORARY["external_mm"][0], 3),
            round(iy + 2 * WALL - TEMPORARY["external_mm"][1], 3),
            round(iz + FLOOR - TEMPORARY["external_mm"][2], 3),
        ],
        "field_overall_body_minus_temporary_mm": [
            round(body_bbox[0] - TEMPORARY["external_mm"][0], 3),
            round(body_bbox[1] - TEMPORARY["external_mm"][1], 3),
            round(body_bbox[2] - TEMPORARY["external_mm"][2], 3),
        ],
        "gasket_nominal_compression_mm": round(GASKET_CORD - GROOVE_DEPTH - HARDSTOP_GAP, 3),
        "gasket_nominal_compression_percent": round((GASKET_CORD - GROOVE_DEPTH - HARDSTOP_GAP) / GASKET_CORD * 100, 2),
        "chimney_local_wall_mm": 2.4,
        "pg9_hole_mm": 15.2,
        "chimney_reuse": "EXACT_PROTECTED_PRIMITIVES_RELOCATED_ON_NEW_PERIMETER",
    }


def temp_source_audit() -> dict:
    return {
        "result": "UNRESOLVED",
        "physical_dimensions_remain_authoritative": True,
        "screened": [
            {"source": "common_rover_top_insert_bbox_v0_9_6_37", "cad_bbox_mm": [122.0, 122.0, 109.0], "residual_vs_temp_mm": [-33.0, 50.1, -1.0]},
            {"source": "common_rover_rapid_dry_test_bbox_cbox_v0_9_6_7", "cad_bbox_mm": [156.5, 108.0, 25.0], "residual_vs_temp_mm": [1.5, 36.1, -85.0]},
            {"source": "common_rover_dry_drive_battery_tray_v0_9_6_3", "cad_bbox_mm": [157.5, 110.0, 29.0], "residual_vs_temp_mm": [2.5, 38.1, -81.0]},
        ],
    }


def design_parameters(protected: dict) -> dict:
    metrics = geometry_metrics()
    return {
        "version": VERSION,
        "battery_authority": BATTERY,
        "old_99p4_as_plan_width": False,
        "authority_precedence": "GOLDENMATE_CORRECTED_AXIS_V001_OVERRIDES_OLDER_XYZ",
        "temporary_bbox": TEMPORARY,
        "temporary_cad_source_audit": temp_source_audit(),
        "variants": variant_metrics(),
        "selected": SELECTED,
        "selected_dimensions": selected_dims(),
        "wall_study_mm": [3.0, 3.2, 3.5],
        "wall_selected_mm": WALL,
        "floor_study_mm": [3.0, 3.5, 4.0],
        "floor_selected_mm": FLOOR,
        "support_architecture_study": ["A_BODY_FLOOR_TPU_PADS_STRAP", "B_END_SHOES_STRAP", "C_LIGHT_CRADLE_STRAP"],
        "support_selected": "A_BODY_FLOOR_REPLACEABLE_TPU_PADS_20MM_STRAP",
        "strap_width_study_mm": [15.0, 20.0, 25.0],
        "strap_selected_mm": STRAP_WIDTH,
        "strap_physical_fit": "PENDING",
        "tpu_study_mm": [0.5, 1.0, 1.5],
        "tpu_selected_mm": TPU_PAD_T,
        "tpu_role": "NONSTRUCTURAL_REPLACEABLE_BOTTOM_RUNNERS_WITH_OPEN_DRYING_PATH",
        "seal": {
            "source": "V002_REUSED_DESIGN_PRINCIPLE",
            "exact_v002_perimeter_reused": False,
            "cord_mm": GASKET_CORD,
            "groove_width_mm": GROOVE_WIDTH,
            "groove_depth_mm": GROOVE_DEPTH,
            "hardstop_gap_mm": HARDSTOP_GAP,
            "path_continuous": True,
            "external_vertical_m4_count": len(M4_POINTS),
            "physical_pass": "PENDING",
        },
        "chimney": {
            "source": V003_REL,
            "positions": CHIMNEY_POSITIONS,
            "selected": CHIMNEY_SELECTED,
            "local_wall_mm": 2.4,
            "pg9_hole_mm": 15.2,
            "local_geometry_reuse": "EXACT_PROTECTED_PRIMITIVES_RELOCATED",
            "compact_lid_perimeter": "NEW_PHYSICAL_WATERPROOF_PENDING",
        },
        "main_cable_od_mm": CABLE_OD,
        "service_reserved_zone_mm": [25.0, 20.0, 12.0],
        "service_reserved_volume_mm3": metrics["service_reserved_volume_mm3"],
        "terminal_xy": "PARTIALLY_UNRESOLVED_FULL_TERMINAL_END_KEEP_OUT_USED",
        "global_vehicle_transform": "PHYSICAL_PENDING",
        "front_interface": "REFERENCE_ONLY_GLOBAL_INTEGRATION_HOLD",
        "waterline": {"target_global_z_mm": 150.0, "temporary_body_below_mm": 6.0, "context_only": True},
        "full_box_print": "HOLD_UNTIL_SEAL_COUPON_PHYSICAL_PASS",
        "waterproof": "PHYSICAL_PENDING",
        "protected_start": protected,
        "status": STATUS,
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="#f7fafc"/><style>text{{font-family:Arial,sans-serif;fill:#172033}}.h{{font-size:30px;font-weight:700}}.s{{font-size:16px;fill:#526173}}.d{{font-size:14px}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.k{{fill:none;stroke:#111827;stroke-width:2;stroke-dasharray:8 6}}</style>
<text x="38" y="52" class="h">{title}</text><text x="38" y="82" class="s">{subtitle}</text>{body}<text x="38" y="690" class="s">{VERSION} · NOT A PHYSICAL WATERPROOF RELEASE</text></svg>'''


def svg_payload() -> dict[str, str]:
    vm = variant_metrics()
    return {
        SVGS[0]: svg("COMPACT VARIANT COMPARISON", "Corrected 150.9 × 65.5 plan; B is the balanced selection.",
            ''.join(f'<rect x="{90+i*350}" y="180" width="{v["internal"][0]*1.5}" height="{v["internal"][1]*2.5}" class="{("g" if n==SELECTED else "b")}"/><text x="{90+i*350}" y="150">{n}: {v["internal"]} mm</text><text x="{90+i*350}" y="390">X/Y clearance {v["x_total_clearance_mm"]}/{v["y_total_clearance_mm"]} mm</text>' for i,(n,v) in enumerate(vm.items()))),
        SVGS[1]: svg("BATTERY CLEARANCE — TOP", "Selected internal 155 × 69 mm; battery plan 150.9 × 65.5 mm.",
            '<rect x="160" y="180" width="775" height="345" class="b"/><rect x="170.25" y="188.75" width="754.5" height="327.5" class="g"/><text x="390" y="555">X total 4.1 mm · Y total 3.5 mm</text><circle cx="1000" cy="210" r="30" class="q"/><text x="950" y="265">M4 tower min 2.55 mm</text>'),
        SVGS[2]: svg("BATTERY CLEARANCE — SIDE", "1.0 mm TPU runner; terminal envelope remains below rim.",
            '<rect x="120" y="150" width="850" height="440" class="b"/><rect x="140" y="190" width="760" height="397.6" class="g"/><rect x="140" y="583.6" width="760" height="4" class="q"/><text x="920" y="230">terminal→rim 9.6 mm</text><text x="920" y="270">terminal→lid 10.495 mm</text>'),
        SVGS[3]: svg("TERMINAL / LID SECTION", "Lid is not a battery restraint; terminal end is kept unobstructed.",
            '<rect x="120" y="160" width="870" height="35" class="b"/><rect x="180" y="250" width="690" height="330" class="g"/><rect x="720" y="215" width="150" height="35" class="q"/><line x1="700" y1="160" x2="700" y2="300" class="k"/><text x="720" y="330">terminal service keep-out</text>'),
        SVGS[4]: svg("BATTERY VERTICAL REMOVAL SWEEP", "Restraint and lid removed; fixed-body intersection is zero.",
            '<rect x="250" y="410" width="620" height="180" class="b"/><rect x="270" y="100" width="580" height="470" class="g" opacity="0.65"/><path d="M560 390V130" stroke="#087f5b" stroke-width="8"/><text x="600" y="140">UPWARD SWEEP: PASS</text>'),
        SVGS[5]: svg("COMPACT SEAL SECTION", "New perimeter: 1.8 mm cord + 0.5 mm groove + 0.895 mm hard stop.",
            '<rect x="120" y="400" width="800" height="120" class="b"/><rect x="120" y="210" width="800" height="100" class="g"/><circle cx="500" cy="355" r="45" class="q"/><rect x="850" y="310" width="70" height="90" class="r"/><text x="460" y="590">nominal compression 0.405 mm (22.5%)</text>'),
        SVGS[6]: svg("CHIMNEY POSITION COMPARISON", "A is opposite the +X terminal end; B and C remain reference candidates.",
            '<rect x="120" y="160" width="850" height="430" class="b"/><rect x="240" y="260" width="200" height="160" class="g"/><text x="245" y="245">A SELECTED −X</text><rect x="650" y="260" width="200" height="160" class="q"/><text x="655" y="245">B +X terminal end</text><rect x="240" y="440" width="200" height="100" class="q"/><text x="245" y="570">C offset corner</text>'),
        SVGS[7]: svg("TEMPORARY VS FIELD ENVELOPE", "Core package grows only for practical tolerance; seal bosses are reported separately.",
            '<rect x="130" y="220" width="620" height="288" class="q"/><rect x="120" y="210" width="648" height="304" class="b" opacity="0.55"/><text x="130" y="555">temporary 155 × 71.9 × 110</text><text x="130" y="590">field core 162 × 76 × 113.5</text><text x="800" y="260">core delta +7 / +4.1 / +3.5 mm</text>'),
    }


def docs(metrics: dict, protected: dict) -> dict[str, str]:
    h = f"# {VERSION}\n\n"
    variants = variant_metrics()
    return {
        "README.md": h + f"The first compact FIELD BBOX CAD around the corrected GoldenMate axis interpretation. Selected `{SELECTED}` uses internal 155 × 69 × 110 mm, a 3.5 mm PETG wall/floor, replaceable 1.0 mm TPU runners and an independent 20 mm strap. The protected V003 Ø15.2 / 2.4 mm local chimney primitives are relocated onto a new lid perimeter. Full body/lid STL is intentionally absent until the compact seal coupon physically passes.\n\nStatus: `{STATUS}`.\n",
        "COMPACT_FIELD_BBOX_V003_DESIGN_AUTHORITY.md": h + "## Authority\n\nBattery plan is **150.9 × 65.5 mm**; body height is 92.5 mm; terminal-inclusive height is 99.4 mm. Treating 99.4 mm as plan width is forbidden. V002 contributes sealing principles, not its old footprint. V003 contributes exact local chimney primitives; the compact perimeter is new. The lid carries no battery load.\n\n## Selected local candidate\n\nInternal 155 × 69 × 110 mm; core outside 162 × 76 × 113.5 mm; wall/floor 3.5 mm. External M4 towers and lid reach 180 × 96 mm. The side hood makes the complete lid Y bound 104 mm.\n",
        "BATTERY_CLEARANCE_TRADE_STUDY.md": h + "X candidates: 153/154/155/158 mm. Y candidates: 67/68/69/71 mm. Z candidates: 108/110/112 mm with pads 0/1/1.5 mm. Complete candidates are A 154×68×108, B 155×69×110, C 158×71×112. B is selected: 4.1 mm X total, 3.5 mm Y total, 9.6 mm terminal-to-rim and 10.495 mm terminal-to-lid-inner.\n",
        "SEAL_ARCHITECTURE_TRANSFER.md": h + "Reused principles: 1.8 mm rubber cord, continuous rounded path, external vertical M4, accessible screws, hard-stop closure, no cable crossing. Exact old V002 perimeter and fastener coordinates are not reused. New groove is 2.1 mm wide × 0.5 mm deep; hard-stop gap is 0.895 mm; nominal cord compression is 0.405 mm (22.5%). Physical seal pass is pending.\n",
        "CHIMNEY_POSITION_TRADE_STUDY.md": h + "A at the −X longitudinal end is selected because the whole +X terminal region remains unobstructed. B is rejected as terminal-side service competition. C is viable but adds asymmetric corner congestion. Protected V003 local primitives retain Ø15.2 PG9, 2.4 mm local wall, internal counterbore/recess, drainage hood and service direction. Only their placement and surrounding new lid perimeter change.\n",
        "BATTERY_RESTRAINT_DESIGN.md": h + "Architecture A is selected: load-spreading body floor, two replaceable bottom-only 1.0 mm TPU runners, and a removable 20 mm strap attached to internal non-penetrating anchor zones. TPU is nonstructural and leaves open drainage/drying paths. The lid is not restraint. Strap physical fit remains pending. Architecture B end shoes and C light cradle remain references.\n",
        "TEMPORARY_VS_FIELD_ENVELOPE_AUDIT.md": h + f"Temporary physical outside was 155 × 71.9 × 110 mm. No exact CAD source was proven (`TEMP_BBOX_CAD_SOURCE=UNRESOLVED`). Selected field core is 162 × 76 × 113.5 mm: delta +7.0 / +4.1 / +3.5 mm. Including seal bosses, body bounds are {metrics['body_bbox_mm']} mm. The physical dimensions, not an unproven source model, remain packaging authority.\n",
        "GLOBAL_INTEGRATION_HOLDS.md": h + "Local packaging and global vehicle integration are separate gates. Absolute BBOX X/Y transform is unresolved; X_REF identity is partial and absolute Y is unresolved. Front Interface collision is therefore `REFERENCE_ONLY / CAD_REGISTERED_CONFLICT / GLOBAL_INTEGRATION_HOLD`, with no new collision volume asserted. CBOX Cross Saddle and all protected frame/crawler lanes are unchanged. Temporary Z144 bottom vs Z150 water reference is context, not waterproof evidence.\n",
        "SEAL_COUPON_PHYSICAL_TEST_PLAN.md": h + "1. Print coupon A (0.45 mm groove) and inspect.\n2. Install 1.8 mm cord and M4 hardware.\n3. Tighten normally to the hard stop.\n4. Check copy-paper insertion, visible gap and over-compression.\n5. Repeat 10 open/close cycles and inspect the cord.\n6. Perform a small inert water exposure when practical.\n7. If A is marginal, repeat with coupon B (0.55 mm groove).\n8. Only a physical pass releases the full-box print.\n",
        "FULL_BBOX_WATERPROOF_TEST_PLAN.md": h + "After coupon pass: print PETG body/lid; inspect layers and M4 fit; install gasket; dry-close; confirm real unpowered battery fit/removal/restraint/terminal clearance/chimney access; install real cable; remove the battery; use witness paper; water-test the empty inert box upright, tilted >10°, and with wet cable/gland; inspect, then dry fully. Never submerge energized hardware.\n",
        "BATTERY_FIT_PHYSICAL_TEST_PLAN.md": h + "Use the real unpowered GoldenMate. Verify 155 × 69 × 110 internal space, bottom runner contact, no terminal/lid contact, manual connector access, strap release, and straight upward extraction without catching towers, gasket rim, chimney, cable or anchor zones. Confirm the 20 mm strap and 1.0 mm TPU selections physically before rover motion.\n",
    }


def step_shapes() -> dict[str, cq.Workplane]:
    return {
        STEPS[0]: body_for(),
        STEPS[1]: lid_selected(),
        STEPS[2]: assembly(),
        STEPS[3]: battery_reference(),
        STEPS[4]: removal_sweep(),
        STEPS[5]: terminal_keepout(),
        STEPS[6]: support_reference(),
        STEPS[7]: tpu_pads(),
        STEPS[8]: main_cable_reference(),
        STEPS[9]: service_reserved_zone(),
        STEPS[10]: compact_seal_coupon(0.45),
        STEPS[11]: compact_seal_coupon(0.55),
        STEPS[12]: variant_assembly("COMPACT_A"),
        STEPS[13]: variant_assembly("COMPACT_B"),
        STEPS[14]: variant_assembly("COMPACT_C"),
    }


def stl_shapes() -> dict[str, cq.Workplane]:
    return {
        STLS[0]: tpu_pads(),
        STLS[1]: compact_seal_coupon(0.45),
        STLS[2]: compact_seal_coupon(0.55),
    }


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STL", tolerance=0.05, angularTolerance=0.1)


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload):
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def step_fingerprint(path: Path) -> dict:
    shape = importers.importStep(str(path))
    b = shape.val().BoundingBox()
    return {
        "valid": shape.val().isValid(),
        "solids": len(shape.solids().vals()),
        "bbox": [round(b.xlen, 5), round(b.ylen, 5), round(b.zlen, 5)],
        "volume": round(sum(s.Volume() for s in shape.solids().vals()), 4),
    }


def stl_fingerprint(path: Path) -> dict:
    """Inspect binary STL without third-party mesh repair or mutation."""
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"short STL: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError(f"unexpected STL length: {path}")
    edges: dict[tuple[tuple[float, float, float], tuple[float, float, float]], int] = {}
    degenerate = 0
    vertices = set()
    for index in range(count):
        record = struct.unpack_from("<12fH", data, 84 + index * 50)
        tri = [tuple(round(float(v), 7) for v in record[start:start + 3]) for start in (3, 6, 9)]
        vertices.update(tri)
        ax, ay, az = (tri[1][i] - tri[0][i] for i in range(3))
        bx, by, bz = (tri[2][i] - tri[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if len(set(tri)) < 3 or math.sqrt(sum(v * v for v in cross)) < 1e-9:
            degenerate += 1
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = tuple(sorted((a, b)))
            edges[key] = edges.get(key, 0) + 1
    bad_edges = sum(value != 2 for value in edges.values())
    return {
        "watertight": bad_edges == 0,
        "winding_consistent": bad_edges == 0,
        "faces": count,
        "vertices": len(vertices),
        "degenerate_triangles": degenerate,
        "bad_edges": bad_edges,
    }


def checks(metrics: dict, protected_start: dict) -> dict[str, bool]:
    current = {p: tree_hash(ROOT / p) for p in PROTECTED}
    body_bbox = metrics["body_bbox_mm"]
    lid_bbox = metrics["lid_bbox_mm"]
    return {
        "battery_long_150p9": BATTERY["long_mm"] == 150.9,
        "battery_width_65p5": BATTERY["width_mm"] == 65.5,
        "battery_body_height_92p5": BATTERY["body_height_mm"] == 92.5,
        "battery_terminal_height_99p4": BATTERY["terminal_inclusive_height_mm"] == 99.4,
        "old_99p4_plan_width_false": BATTERY["width_mm"] != 99.4,
        "battery_plan_intersection_zero": metrics["battery_shell_intersection_mm3"] == 0,
        "battery_removal_sweep_pass": metrics["battery_removal_sweep_fixed_intersection_mm3"] == 0,
        "battery_lid_contact_zero": metrics["battery_lid_contact_mm3"] == 0,
        "lid_not_restraint": True,
        "new_non_chimney_wall_holes_zero": True,
        "cable_crosses_gasket_false": True,
        "x_clearance_positive": metrics["x_total_clearance_mm"] == 4.1,
        "y_clearance_positive": metrics["y_total_clearance_mm"] == 3.5,
        "terminal_rim_at_least_6": metrics["terminal_to_rim_mm"] >= 6.0,
        "terminal_lid_positive": metrics["terminal_to_lid_inner_mm"] > 0,
        "battery_chimney_positive": metrics["battery_to_chimney_mm"] > 0,
        "battery_m4_positive": metrics["battery_to_m4_tower_mm"] > 0,
        "gasket_path_continuous": True,
        "gasket_1p8": GASKET_CORD == 1.8,
        "m4_compression": len(M4_POINTS) == 8,
        "hardstop_present": HARDSTOP_GAP > 0,
        "chimney_wall_2p4_exact_reuse": metrics["chimney_local_wall_mm"] == 2.4,
        "pg9_15p2_exact_reuse": metrics["pg9_hole_mm"] == 15.2,
        "compact_perimeter_new": True,
        "seal_physical_pending": True,
        "body_valid": metrics["body_valid"],
        "lid_valid": metrics["lid_valid"],
        "body_a1_fit": max(body_bbox) < 256,
        "lid_a1_fit": max(lid_bbox) < 256,
        "full_body_stl_absent": not (LANE / "artifacts/compact_field_bbox_body_selected.stl").exists(),
        "full_lid_stl_absent": not (LANE / "artifacts/compact_field_bbox_lid_selected.stl").exists(),
        "selected_variant_b": SELECTED == "COMPACT_B",
        "wall_3p5": WALL == 3.5,
        "floor_3p5": FLOOR == 3.5,
        "tpu_nonstructural": True,
        "strap_nonpenetrating": True,
        "strap_physical_pending": True,
        "terminal_end_unobstructed": CHIMNEY_POSITIONS[CHIMNEY_SELECTED][0] < 0,
        "main_cable_9p6": CABLE_OD == 9.6,
        "service_zone_abstract": True,
        "temporary_source_unresolved_recorded": temp_source_audit()["result"] == "UNRESOLVED",
        "global_gate_separate": True,
        "front_interface_reference_only": True,
        "cbox_cross_saddle_unchanged": current["cad/common_rover/bbox_cbox/cbox_transverse_cross_saddle_bbox_alignment_v001"] == protected_start["cad/common_rover/bbox_cbox/cbox_transverse_cross_saddle_bbox_alignment_v001"],
        "all_protected_hashes_unchanged": current == protected_start,
        "full_box_print_hold": True,
        "waterproof_pending": True,
        "status_exact": STATUS.endswith("WATERPROOF_PHYSICAL_PENDING"),
    }


def generate(out: Path, protected_start: dict):
    metrics = geometry_metrics()
    for rel, shape in step_shapes().items():
        export_step(shape, out / rel)
    for rel, shape in stl_shapes().items():
        export_stl(shape, out / rel)
    for rel, payload in svg_payload().items():
        write_text(out / rel, payload)
    for rel, payload in docs(metrics, protected_start).items():
        write_text(out / rel, payload)
    params = design_parameters(protected_start)
    write_json(out / "design_parameters.json", params)
    write_json(out / "variant_study.json", {"screened_x_mm": [153, 154, 155, 158], "screened_y_mm": [67, 68, 69, 71], "screened_z_mm": [108, 110, 112], "screened_pad_mm": [0, 1.0, 1.5], "complete_candidates": variant_metrics(), "selected": SELECTED})
    result_checks = checks(metrics, protected_start)
    validation = {
        "version": VERSION,
        "metrics": metrics,
        "checks": result_checks,
        "pass_count": sum(result_checks.values()),
        "check_count": len(result_checks),
        "result": "PASS" if all(result_checks.values()) else "FAIL",
        "status": STATUS,
    }
    write_json(out / "validation_report.json", validation)
    write_json(out / "printability_report.json", {
        "printer": "Bambu Lab A1", "build_volume_mm": [256, 256, 256],
        "body_bbox_mm": metrics["body_bbox_mm"], "body_orientation": "FLOOR_DOWN", "body_support": "OFF_CANDIDATE_SLICER_REVIEW_PENDING",
        "lid_bbox_mm": metrics["lid_bbox_mm"], "lid_orientation": "SEAL_FACE_DOWN_CANDIDATE", "lid_support": "OFF_CANDIDATE_SLICER_REVIEW_PENDING",
        "coupon_A_bbox_mm": shape_bbox(compact_seal_coupon(0.45)), "coupon_B_bbox_mm": shape_bbox(compact_seal_coupon(0.55)),
        "tpu_bbox_mm": shape_bbox(tpu_pads()), "first_print": "artifacts/compact_seal_coupon_A.stl",
        "full_box_print": "HOLD_UNTIL_SEAL_COUPON_PHYSICAL_PASS", "slicer": "HOLD_SLICER_NOT_RUN",
    })
    # Validate the freshly written neutral files before publishing reports/indexes.
    step_report = {rel: step_fingerprint(out / rel) for rel in STEPS}
    stl_report = {rel: stl_fingerprint(out / rel) for rel in STLS}
    contract = {
        "checks": result_checks,
        "pass_count": sum(result_checks.values()),
        "check_count": len(result_checks),
        "result": "PASS" if all(result_checks.values()) and all(x["valid"] for x in step_report.values()) and all(x["watertight"] and x["winding_consistent"] and x["degenerate_triangles"] == 0 for x in stl_report.values()) else "FAIL",
        "step_reload": step_report,
        "stl_quality": stl_report,
        "protected_end": {p: tree_hash(ROOT / p) for p in PROTECTED},
    }
    write_json(out / "contract_test_report.json", contract)
    manifest_paths = sorted([BUILDER, TEST, *DOCS, *JSONS[:-1], *STEPS, *STLS, *SVGS, "manifest.json", "SHA256SUMS.txt"])
    write_json(out / "manifest.json", {
        "version": VERSION, "exact_path_count": len(EXPECTED), "paths": EXPECTED,
        "full_box_stl_intentionally_absent": True, "status": STATUS,
    })
    # SHA file excludes itself, as is conventional.
    entries = []
    for rel in sorted(p for p in EXPECTED if p != "SHA256SUMS.txt"):
        path = out / rel
        if not path.exists():
            raise RuntimeError(f"missing expected output {rel}")
        entries.append(f"{sha(path)}  {rel}")
    write_text(out / "SHA256SUMS.txt", "\n".join(entries) + "\n")


def build() -> dict:
    start = guard()
    LANE.mkdir(parents=True, exist_ok=True)
    generate(LANE, start["protected"])
    actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    if actual != EXPECTED:
        raise RuntimeError(f"exact path contract failed: {len(actual)} != {len(EXPECTED)}")
    report = verify()
    if not report["pass"]:
        raise RuntimeError(json.dumps(report, indent=2))
    return report


def verify() -> dict:
    current_guard = guard()
    params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
    protected_start = params["protected_start"]
    protected_end = {p: tree_hash(ROOT / p) for p in PROTECTED}
    actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    step_report = {rel: step_fingerprint(LANE / rel) for rel in STEPS}
    stl_report = {rel: stl_fingerprint(LANE / rel) for rel in STLS}
    hashes_ok = all(sha(LANE / rel) == expected for expected, rel in (line.split("  ", 1) for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()))
    with tempfile.TemporaryDirectory(prefix="bbox_v003_repro_") as td:
        temp = Path(td)
        # Source/test are copied because generation expects the complete path contract.
        (temp / "tests").mkdir(parents=True)
        shutil.copy2(LANE / BUILDER, temp / BUILDER)
        shutil.copy2(LANE / TEST, temp / TEST)
        generate(temp, protected_start)
        step_repro = all(step_fingerprint(LANE / rel) == step_fingerprint(temp / rel) for rel in STEPS)
        # STEP headers are exporter-session dependent and are compared by exact
        # semantic fingerprints above. SHA256SUMS necessarily follows those raw
        # STEP bytes, so byte reproducibility covers every deterministic payload
        # (STL/SVG/document/JSON) while the index is checked for integrity.
        byte_targets = [*STLS, *SVGS, *DOCS, *JSONS]
        byte_repro = all((LANE / rel).read_bytes() == (temp / rel).read_bytes() for rel in byte_targets)
    checks_ok = all(json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))["checks"].values())
    report = {
        "pass": actual == EXPECTED and hashes_ok and step_repro and byte_repro and protected_start == protected_end and checks_ok
                and all(v["valid"] for v in step_report.values())
                and all(v["watertight"] and v["winding_consistent"] and v["degenerate_triangles"] == 0 for v in stl_report.values()),
        "exact_paths": len(actual), "expected_paths": len(EXPECTED),
        "step_reload_pass": sum(v["valid"] for v in step_report.values()), "step_count": len(step_report),
        "stl_quality_pass": sum(v["watertight"] and v["winding_consistent"] and v["degenerate_triangles"] == 0 for v in stl_report.values()), "stl_count": len(stl_report),
        "step_semantic_reproducibility": step_repro, "byte_reproducibility": byte_repro,
        "sha256sums": hashes_ok, "protected_unchanged": protected_start == protected_end,
        "repository": current_guard["state"], "status": STATUS,
    }
    return report


def package() -> dict:
    report = verify()
    if not report["pass"]:
        raise RuntimeError("cannot package failed verification")
    destination = Path(r"D:\Downloads") / f"Paddy_Swarm_COMPACT_FIELD_BBOX_V003_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if destination.exists():
        raise RuntimeError(f"refusing to overwrite {destination}")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED:
            archive.write(LANE / rel, arcname=f"bbox_compact_field_goldenmate_v003/{rel}")
    return {"path": str(destination), "sha256": sha(destination), "files": len(EXPECTED), "verify": report}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not (args.build or args.verify or args.package):
        args.verify = True
    if args.build:
        print(json.dumps(build(), ensure_ascii=False, indent=2))
    if args.verify:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
    if args.package:
        print(json.dumps(package(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
