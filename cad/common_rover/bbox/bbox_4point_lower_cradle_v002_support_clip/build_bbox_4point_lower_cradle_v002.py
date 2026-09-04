"""BBOX V002 support-only shoes and post-seat removable retention clips.

V001's physically passing rail, M5, arm and ledge geometry is read-only.  The
fixed 12 mm lips are removed from every permanent shoe.  Two mirrored clips are
installed only after the BBOX is seated.  Structural, uplift and rollover load
authority remains physical-pending.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer


ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = Path(__file__).resolve().parent
REL = "cad/common_rover/bbox/bbox_4point_lower_cradle_v002_support_clip"
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
TOL = 1.0e-6
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/V002_SUPPORT_CLIP_COUPON_PRINT_READY/"
    "FULL_SUPPORT_ONLY_CRADLE_CAD_READY/REMOVABLE_RETENTION_CLIP_CAD_READY/"
    "FULL_PRINT_HOLD_UNTIL_COUPON_PASS/STRUCTURAL_LOAD_PHYSICAL_PENDING/"
    "ROLLOVER_PHYSICAL_PENDING"
)

V1_REL = "cad/common_rover/bbox/bbox_4point_lower_cradle_v001"
BBOX_REL = "cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065"
CBOX_V2_REL = "cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002"
P25_REL = "cad/common_rover/pto/pto_p25_slide_in_positioning_v002"

# V001 generated/physical datums retained exactly.
BBOX_CORE_X = 162.0
BBOX_CORE_Y = 76.0
BBOX_BODY_HEIGHT = 114.395
BBOX_LEDGE_TOP_Z = -107.0
BBOX_REFERENCE_SEPARATION = 0.02
BBOX_BODY_BOTTOM_Z = BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION
LEDGE_DEPTH = 10.0
LEDGE_THICKNESS = 8.0
LEDGE_BOTTOM_Z = BBOX_LEDGE_TOP_Z - LEDGE_THICKNESS
SUPPORT_X = 30.0
BODY_SIDE_LEFT_LOCAL = -56.5
RAIL_CENTER = 189.0
RIGHT_RAIL_LOCAL_Z = -1.0
FRONT_MOUNT_X = 60.0
REAR_MOUNT_X = -14.0
FRONT_SUPPORT_X = 60.0
REAR_SUPPORT_X = -60.0

# V002 localized correction.
PERMANENT_LIP_HEIGHT = 0.0
CLIP_CLEARANCES = {"r05": 0.5, "r08": 0.8, "r10": 1.0}
SELECTED_CLIP_CLEARANCE = 0.8
UPLIFT_GAP = 1.0
CLIP_ZONE_HEIGHT = 20.0
CLIP_WALL = 4.0
CLIP_X = 30.0
CLIP_BASE_Y = 16.0
CLIP_BASE_T = 5.0
CLIP_OUTER_SPINE = 5.0
CLIP_FASTENER_D = 5.5
CLIP_FASTENER_Y = 8.0
ATTACHMENT_PAD_Y = 16.0
COUPON_LEDGE_TOP_Z = -35.0
TPU_PAD_T = 1.0

PRINT_NAMES = [
    "bbox_v002_support_clip_coupon",
    "bbox_retention_clip_r05", "bbox_retention_clip_r08", "bbox_retention_clip_r10",
    "bbox_lower_cradle_v002_front_left", "bbox_lower_cradle_v002_front_right",
    "bbox_lower_cradle_v002_rear_left", "bbox_lower_cradle_v002_rear_right",
    "bbox_lower_cradle_v002_tpu_pad", "bbox_lower_cradle_v002_leveling_shim_0p5",
    "bbox_lower_cradle_v002_leveling_shim_1p0",
]
REFERENCE_NAMES = [
    "selected_retention_clip_pair", "bbox_lower_cradle_v002_assembly_no_clips",
    "bbox_lower_cradle_v002_assembly_with_clips", "bbox_v002_insertion_sweep_reference",
    "bbox_body_reference", "upper_rail_reference", "cbox_saddle_reference",
]
STEPS = [f"artifacts/{name}.step" for name in PRINT_NAMES + REFERENCE_NAMES]
STLS = [f"artifacts/{name}.stl" for name in PRINT_NAMES]
SVGS = [f"previews/{name}.svg" for name in [
    "v001_failure", "v002_support_only", "retention_clip_detail",
    "clip_install_sequence", "bbox_vertical_insertion",
    "v001_v002_insertion_comparison", "load_path", "battery_service",
    "lid_service", "crawler_clearance", "cbox_clearance",
]]
DOCS = [
    "README.md", "BBOX_4POINT_LOWER_CRADLE_V002_DESIGN.md",
    "V001_PHYSICAL_FAILURE_RECORD.md", "V001_V002_LOCAL_DIFF.md",
    "VERTICAL_INSERTION_SWEEP_AUDIT.md", "REMOVABLE_RETENTION_CLIP_DESIGN.md",
    "RETENTION_CLIP_VARIANT_MATRIX.md", "SUPPORT_CLIP_COUPON_TEST_PLAN.md",
    "FULL_V002_PHYSICAL_TEST_PLAN.md", "BATTERY_AND_LID_SERVICE_AUDIT.md",
    "LOAD_PATH_AND_ROLLOVER_HOLD.md",
]
REPORTS = [
    "design_parameters.json", "validation_report.json", "contract_test_report.json",
    "source_authority_audit.json", "v001_v002_geometry_diff.json",
    "insertion_sweep_audit.json", "intersection_report.json",
    "physical_result_template.json", "repository_audit.json", "manifest.json",
]
EXPECTED = sorted([
    Path(__file__).name, "tests/test_bbox_4point_lower_cradle_v002.py",
    "audit_start.json", "COMMIT_PATHS.txt", "SHA256SUMS.txt",
    *STEPS, *STLS, *SVGS, *DOCS, *REPORTS,
])


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "--no-optional-locks", *args], cwd=ROOT, stderr=subprocess.PIPE
    ).decode("utf-8").strip()


def tree_hash(path: Path) -> dict:
    files = sorted(p for p in path.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts
                   and p.suffix.lower() not in {".pyc", ".pyo"})
    h = hashlib.sha256()
    for item in files:
        h.update((item.relative_to(path).as_posix() + "\n").encode())
        h.update(bytes.fromhex(sha(item)))
    return {"files": len(files), "sha256": h.hexdigest()}


def outside_bytes(paths: list[str]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update((path + "\n").encode())
        h.update(bytes.fromhex(sha(ROOT / path)))
    return h.hexdigest()


def audit(full: bool = False) -> dict:
    baseline = json.loads((LANE / "audit_start.json").read_text(encoding="utf-8"))
    untracked = sorted(p for p in git("ls-files", "--others", "--exclude-standard", "-z").split("\0") if p)
    outside = [p for p in untracked if not p.startswith(REL + "/")]
    own = [p[len(REL) + 1:] for p in untracked if p.startswith(REL + "/")]
    dirty = {p: sha(ROOT / p) for p in git("diff", "--name-only").splitlines()}
    protected = {p: tree_hash(ROOT / p) for p in baseline["protected"]}
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    state = {
        "repository": str(Path(git("rev-parse", "--show-toplevel")).resolve()),
        "branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD"),
        "staged_count": len(git("diff", "--cached", "--name-only").splitlines()),
        "tracked_dirty_count": len(dirty), "dirty": dirty,
        "outside_untracked_count": len(outside),
        "outside_untracked_paths_sha256": hashlib.sha256(("\n".join(outside) + "\n").encode()).hexdigest(),
        "new_path_count": len(own), "untracked_total": len(untracked),
        "protected": protected,
        "protected_source_changed_count": sum(protected[p] != baseline["protected"][p] for p in protected),
    }
    ok = (
        Path(state["repository"]) == ROOT and state["branch"] == BRANCH
        and state["head"] == HEAD and state["staged_count"] == 0
        and dirty == baseline["dirty"] and protected == baseline["protected"]
        and len(outside) == baseline["outside_untracked_count"]
        and state["outside_untracked_paths_sha256"] == baseline["outside_untracked_paths_sha256"]
        and files == own and set(files).issubset(EXPECTED)
    )
    if full:
        state["outside_untracked_bytes_sha256"] = outside_bytes(outside)
        ok = ok and state["outside_untracked_bytes_sha256"] == baseline["outside_untracked_bytes_sha256"]
    state["pass"] = bool(ok)
    if not ok:
        raise AssertionError("FAIL_CLOSED " + json.dumps(state, sort_keys=True))
    return state


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(None)
def v1():
    return load_module("read_only_bbox_cradle_v001",
                       ROOT / V1_REL / "build_bbox_4point_lower_cradle_v001.py")


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder_z(d: float, h: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    x, y, z = center
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate((x, y, z - h / 2))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    values = []
    for part in parts:
        values.extend(part.vals())
    return cq.Workplane(obj=cq.Compound.makeCompound(values))


def volume(shape: cq.Workplane) -> float:
    return sum(s.Volume() for s in shape.solids().vals())


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def bounds(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]


def size(shape: cq.Workplane) -> list[float]:
    b = bounds(shape)
    return [b[i + 3] - b[i] for i in range(3)]


def symmetric_difference_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.cut(b)) + volume(b.cut(a))


def lip_removal_mask(station: str) -> cq.Workplane:
    offset = 0.0 if station.upper() == "FRONT" else -46.0
    return box(SUPPORT_X + 4.0, 24.0, 36.0,
               (offset, BODY_SIDE_LEFT_LOCAL + 12.0, BBOX_LEDGE_TOP_Z + 18.0))


def attachment_pad_left(station: str) -> cq.Workplane:
    offset = 0.0 if station.upper() == "FRONT" else -46.0
    pad = box(CLIP_X, ATTACHMENT_PAD_Y, LEDGE_THICKNESS,
              (offset, BODY_SIDE_LEFT_LOCAL + ATTACHMENT_PAD_Y / 2,
               LEDGE_BOTTOM_Z + LEDGE_THICKNESS / 2))
    hole = cylinder_z(CLIP_FASTENER_D, LEDGE_THICKNESS + 2,
                      (offset, BODY_SIDE_LEFT_LOCAL + CLIP_FASTENER_Y,
                       LEDGE_BOTTOM_Z + LEDGE_THICKNESS / 2))
    return pad.cut(hole).clean()


def support_left(station: str) -> cq.Workplane:
    result = v1().left_shoe(station, 0.5).cut(lip_removal_mask(station)).clean()
    if station.upper() == "FRONT":
        result = result.union(attachment_pad_left(station)).clean()
    return result


def support_shoe(side: str, station: str) -> cq.Workplane:
    result = support_left(station)
    return result if side.upper() == "LEFT" else result.mirror("XZ").clean()


def compact_support_coupon() -> cq.Workplane:
    """Shortened Z-only coupon: all rail/body fit surfaces remain exact."""
    offset = 0.0
    hanger = box(30.0, 5.0, 43.0, (0, -12.5, -13.5))
    ledge = box(SUPPORT_X, LEDGE_DEPTH, LEDGE_THICKNESS,
                (offset, BODY_SIDE_LEFT_LOCAL - LEDGE_DEPTH / 2,
                 COUPON_LEDGE_TOP_Z - LEDGE_THICKNESS / 2))
    pad = box(CLIP_X, ATTACHMENT_PAD_Y, LEDGE_THICKNESS,
              (offset, BODY_SIDE_LEFT_LOCAL + ATTACHMENT_PAD_Y / 2,
               COUPON_LEDGE_TOP_Z - LEDGE_THICKNESS / 2))
    hole = cylinder_z(CLIP_FASTENER_D, LEDGE_THICKNESS + 2,
                      (0, BODY_SIDE_LEFT_LOCAL + CLIP_FASTENER_Y,
                       COUPON_LEDGE_TOP_Z - LEDGE_THICKNESS / 2))
    pad = pad.cut(hole)
    top_root = v1().triangular_yz([(-22, 0), (-10, 0), (-10, 8)], 0, 30.0)
    bottom_root = v1().triangular_yz(
        [(-25, COUPON_LEDGE_TOP_Z), (-10, COUPON_LEDGE_TOP_Z),
         (-10, COUPON_LEDGE_TOP_Z + 15)], 0, 30.0)
    return (v1().proven_top_interface().union(hanger).union(ledge).union(pad)
            .union(top_root).union(bottom_root).clean())


def retention_clip(clearance: float) -> cq.Workplane:
    """One low, bolt-on clip; body-side datum is Y=0 and bottom datum Z=0."""
    pad_bottom_rel = LEDGE_BOTTOM_Z - BBOX_BODY_BOTTOM_Z
    base_bottom = pad_bottom_rel - CLIP_BASE_T
    base = box(CLIP_X, CLIP_BASE_Y, CLIP_BASE_T,
               (0, CLIP_BASE_Y / 2, base_bottom + CLIP_BASE_T / 2))
    base = base.cut(cylinder_z(CLIP_FASTENER_D, CLIP_BASE_T + 2,
                               (0, CLIP_FASTENER_Y, base_bottom + CLIP_BASE_T / 2)))
    fence = box(CLIP_X, CLIP_WALL, CLIP_ZONE_HEIGHT - UPLIFT_GAP,
                (0, clearance + CLIP_WALL / 2,
                 (UPLIFT_GAP + CLIP_ZONE_HEIGHT) / 2))
    spine = box(CLIP_X, CLIP_OUTER_SPINE, CLIP_ZONE_HEIGHT - base_bottom,
                (0, CLIP_BASE_Y - CLIP_OUTER_SPINE / 2,
                 (base_bottom + CLIP_ZONE_HEIGHT) / 2))
    bridge = box(CLIP_X, CLIP_BASE_Y - clearance, 4.0,
                 (0, (CLIP_BASE_Y + clearance) / 2, CLIP_ZONE_HEIGHT - 2.0))
    root = v1().triangular_yz(
        [(clearance + CLIP_WALL, 0), (clearance + CLIP_WALL + 5, 0),
         (clearance + CLIP_WALL, 5)], 0, CLIP_X)
    return base.union(fence).union(spine).union(bridge).union(root).clean()


def tpu_pad(thickness: float = TPU_PAD_T) -> cq.Workplane:
    return box(SUPPORT_X, LEDGE_DEPTH, thickness, (0, 0, thickness / 2))


def leveling_shim(thickness: float) -> cq.Workplane:
    return box(SUPPORT_X, LEDGE_DEPTH, thickness, (0, 0, thickness / 2))


def placed_shoe(side: str, station: str) -> cq.Workplane:
    x = FRONT_MOUNT_X if station.upper() == "FRONT" else REAR_MOUNT_X
    y = RAIL_CENTER / 2 if side.upper() == "LEFT" else -RAIL_CENTER / 2
    z = 0.0 if side.upper() == "LEFT" else RIGHT_RAIL_LOCAL_Z
    return support_shoe(side, station).translate((x, y, z))


def placed_shoes() -> cq.Workplane:
    return compound([placed_shoe(side, station)
                     for station in ("FRONT", "REAR") for side in ("LEFT", "RIGHT")])


def placed_clip(side: str, clearance: float = SELECTED_CLIP_CLEARANCE) -> cq.Workplane:
    raw = retention_clip(clearance)
    if side.upper() == "LEFT":
        return raw.translate((FRONT_SUPPORT_X, BBOX_CORE_Y / 2, BBOX_BODY_BOTTOM_Z))
    return raw.mirror("XZ").translate((FRONT_SUPPORT_X, -BBOX_CORE_Y / 2,
                                       BBOX_BODY_BOTTOM_Z)).clean()


def selected_clip_pair() -> cq.Workplane:
    return compound([placed_clip("LEFT"), placed_clip("RIGHT")])


def bbox_full_envelope_placed() -> cq.Workplane:
    return compound([v1().bbox_body_placed(), v1().bbox_lid_placed(),
                     v1().bbox_gasket_placed(), v1().bbox_chimney_placed()])


def conservative_insertion_prism(dz: float) -> cq.Workplane:
    # Max XY body/tower envelope, swept from bottom through body height.
    return box(180.0, 96.0, BBOX_BODY_HEIGHT,
               (0, 0, BBOX_BODY_BOTTOM_Z + dz + BBOX_BODY_HEIGHT / 2))


def insertion_sweep_reference() -> cq.Workplane:
    states = [conservative_insertion_prism(dz) for dz in (80, 60, 40, 20, 0)]
    return compound([placed_shoes(), *states])


def assembly(with_clips: bool) -> cq.Workplane:
    parts = [v1().rails_reference(), placed_shoes(), v1().bbox_body_placed(),
             v1().bbox_lid_placed(), v1().cbox_saddles_reference()]
    if with_clips:
        parts.append(selected_clip_pair())
    return compound(parts)


def step_models() -> dict[str, cq.Workplane]:
    return {
        "artifacts/bbox_v002_support_clip_coupon.step": compact_support_coupon(),
        "artifacts/bbox_retention_clip_r05.step": retention_clip(0.5),
        "artifacts/bbox_retention_clip_r08.step": retention_clip(0.8),
        "artifacts/bbox_retention_clip_r10.step": retention_clip(1.0),
        "artifacts/bbox_lower_cradle_v002_front_left.step": support_shoe("LEFT", "FRONT"),
        "artifacts/bbox_lower_cradle_v002_front_right.step": support_shoe("RIGHT", "FRONT"),
        "artifacts/bbox_lower_cradle_v002_rear_left.step": support_shoe("LEFT", "REAR"),
        "artifacts/bbox_lower_cradle_v002_rear_right.step": support_shoe("RIGHT", "REAR"),
        "artifacts/bbox_lower_cradle_v002_tpu_pad.step": tpu_pad(),
        "artifacts/bbox_lower_cradle_v002_leveling_shim_0p5.step": leveling_shim(0.5),
        "artifacts/bbox_lower_cradle_v002_leveling_shim_1p0.step": leveling_shim(1.0),
        "artifacts/selected_retention_clip_pair.step": selected_clip_pair(),
        "artifacts/bbox_lower_cradle_v002_assembly_no_clips.step": assembly(False),
        "artifacts/bbox_lower_cradle_v002_assembly_with_clips.step": assembly(True),
        "artifacts/bbox_v002_insertion_sweep_reference.step": insertion_sweep_reference(),
        "artifacts/bbox_body_reference.step": v1().bbox_body_source(),
        "artifacts/upper_rail_reference.step": v1().rails_reference(),
        "artifacts/cbox_saddle_reference.step": v1().cbox_saddles_reference(),
    }


def print_oriented(shape: cq.Workplane, flat: bool) -> cq.Workplane:
    if flat:
        return shape.translate((0, 0, -bounds(shape)[2]))
    rotated = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    return rotated.translate((0, 0, -bounds(rotated)[2]))


def stl_models() -> dict[str, cq.Workplane]:
    models = step_models()
    result = {}
    for name in PRINT_NAMES:
        flat = name.endswith(("tpu_pad", "shim_0p5", "shim_1p0"))
        result[f"artifacts/{name}.stl"] = print_oriented(
            models[f"artifacts/{name}.step"], flat)
    return result


def export_step(shape: cq.Workplane, path: Path) -> None:
    cq.exporters.export(shape, str(path), exportType="STEP")
    text = path.read_text(encoding="ascii")
    text = re.sub(
        r"FILE_NAME\(.*?\);",
        f"FILE_NAME('{path.name}','2000-01-01T00:00:00',(''),(''),'Open CASCADE','CADQUERY','DETERMINISTIC_METADATA');",
        text, flags=re.S,
    )
    text = re.sub(r"Open CASCADE STEP translator (\d+\.\d+) \d+",
                  r"Open CASCADE STEP translator \1 deterministic", text)
    numbers = iter(range(1, 100000))
    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'",
                  lambda _: f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(numbers)}'", text)
    path.write_text(text, encoding="ascii", newline="\n")


def export_stl(shape: cq.Workplane, path: Path) -> None:
    vertices, tris = shape.val().tessellate(0.03, 0.1)
    lines = ["solid BBOX_4POINT_LOWER_CRADLE_V002"]
    for tri in tris:
        a, b, c = [vertices[i] for i in tri]
        normal = (b - a).cross(c - a).normalized()
        lines.extend(["  facet normal " + " ".join(f"{v:.12g}" for v in normal.toTuple()),
                      "    outer loop"])
        for point in (a, b, c):
            lines.append("      vertex " + " ".join(f"{v:.9f}" for v in point.toTuple()))
        lines.extend(["    endloop", "  endfacet"])
    lines.append("endsolid BBOX_4POINT_LOWER_CRADLE_V002")
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def actual_clip_clearance(shape: cq.Workplane) -> float:
    probe = shape.intersect(box(CLIP_X - 2, 30, 6, (0, 8, 13)))
    return bounds(probe)[1]


def actual_uplift_gap(shape: cq.Workplane, clearance: float) -> float:
    probe = shape.intersect(box(CLIP_X - 2, CLIP_WALL - 1, 30,
                                (0, clearance + (CLIP_WALL - 1) / 2, 10)))
    return bounds(probe)[2]


def v001_v002_diff() -> dict:
    old = v1().shoe("LEFT", "FRONT")
    new = support_shoe("LEFT", "FRONT")
    rail_mask = box(40, 20, 30, (0, 0, 15))
    arm_mask = box(32, 42, 130, (0, -9, -53.5))
    ledge_mask = box(30, 10, 8, (0, BODY_SIDE_LEFT_LOCAL - 5, -111))
    lip_mask = lip_removal_mask("FRONT")
    lip_removed = volume(old.intersect(lip_mask)) - volume(new.intersect(lip_mask))
    return {
        "v001_source": V1_REL,
        "v001_rail_m5_fit": "PHYSICAL_FIT_PASS",
        "v001_single_shoe_local_interface": "PHYSICAL_FIT_PASS",
        "v001_four_shoe_bbox_insertion": "PHYSICAL_FAIL",
        "failure_mode": "FIXED_LOCATING_LIP_INSTALLATION_ENVELOPE_CONFLICT",
        "rail_interface_symmetric_difference_mm3": symmetric_difference_volume(
            old.intersect(rail_mask), new.intersect(rail_mask)),
        "protected_arm_symmetric_difference_mm3": symmetric_difference_volume(
            old.intersect(arm_mask), new.intersect(arm_mask)),
        "support_ledge_symmetric_difference_mm3": symmetric_difference_volume(
            old.intersect(ledge_mask), new.intersect(ledge_mask)),
        "intentional_fixed_lip_removed_volume_mm3": lip_removed,
        "permanent_fixed_lip_height_mm": PERMANENT_LIP_HEIGHT,
    }


def insertion_audit() -> dict:
    v2 = placed_shoes()
    v1_shoes = v1().placed_shoes()
    shifts = [80, 60, 40, 20, 0]
    conservative_v2 = {str(dz): common_volume(v2, conservative_insertion_prism(dz)) for dz in shifts}
    actual_v2 = {str(dz): common_volume(v2, bbox_full_envelope_placed().translate((0, 0, dz)))
                 for dz in shifts}
    conservative_v1_final = common_volume(v1_shoes, conservative_insertion_prism(0))
    contacts = []
    for side, station in [("LEFT", "FRONT"), ("RIGHT", "FRONT"),
                          ("LEFT", "REAR"), ("RIGHT", "REAR")]:
        mount_x = FRONT_MOUNT_X if station == "FRONT" else REAR_MOUNT_X
        rail_y = RAIL_CENTER / 2 if side == "LEFT" else -RAIL_CENTER / 2
        probe = box(BBOX_CORE_X, BBOX_CORE_Y, 0.02,
                    (-mount_x, -rail_y, BBOX_LEDGE_TOP_Z - 0.01))
        contacts.append(common_volume(support_shoe(side, station), probe) / 0.02)
    result = {
        "sweep_offsets_mm": shifts,
        "v001_conservative_final_insertion_intersection_mm3": conservative_v1_final,
        "v001_four_shoe_vertical_insertion": "FAIL_PHYSICAL_AND_CONSERVATIVE_CAD",
        "v002_conservative_intersections_mm3": conservative_v2,
        "v002_actual_assembly_intersections_mm3": actual_v2,
        "v002_four_shoe_vertical_insertion": "PASS_REFERENCE",
        "bbox_removal_after_clip_removal": "PASS_REFERENCE",
        "seated_contact_area_per_shoe_mm2": contacts,
        "all_four_seated": all(v >= SUPPORT_X * LEDGE_DEPTH - 1e-4 for v in contacts),
    }
    if conservative_v1_final <= TOL or any(v > TOL for v in conservative_v2.values()):
        raise AssertionError("insertion regression " + json.dumps(result))
    if any(v > TOL for v in actual_v2.values()) or not result["all_four_seated"]:
        raise AssertionError("V002 insertion/seating " + json.dumps(result))
    return result


def intersection_data() -> dict:
    shoes = placed_shoes(); clips = selected_clip_pair(); system = compound([shoes, clips])
    body = v1().bbox_body_placed(); lid = v1().bbox_lid_placed()
    gasket = v1().bbox_gasket_placed(); chimney = v1().bbox_chimney_placed()
    towers = v1().bbox_tower_envelope(); cbox = v1().cbox_saddles_reference()
    crawler = v1().crawler_reference(); tools = v1().bbox_m4_tool_paths()
    battery = v1().bbox_v4().p.removal_sweep().translate((0, 0, BBOX_BODY_BOTTOM_Z))
    lid_sweep = [common_volume(lid.translate((0, 0, dz)), system) for dz in (0, 20, 40, 80)]
    battery_sweep = common_volume(battery, system)
    cbox_sweep = [common_volume(v1().cbox_removal_reference().translate((0, 0, dz)), system)
                  for dz in (0, 20, 40, 80)]
    data = {
        "support_shoe_to_bbox_body_mm3": common_volume(shoes, body),
        "support_shoe_to_lid_mm3": common_volume(shoes, lid),
        "support_shoe_to_gasket_mm3": common_volume(shoes, gasket),
        "support_shoe_to_lid_ear_mm3": common_volume(shoes, towers),
        "clip_to_bbox_body_mm3": common_volume(clips, body),
        "clip_to_lid_mm3": common_volume(clips, lid),
        "clip_to_gasket_mm3": common_volume(clips, gasket),
        "clip_to_chimney_mm3": common_volume(clips, chimney),
        "clip_to_lid_ear_mm3": common_volume(clips, towers),
        "cradle_to_cbox_saddle_mm3": common_volume(system, cbox),
        "retention_clip_to_cbox_mm3": common_volume(clips, cbox),
        "cradle_to_crawler_static_mm3": common_volume(system, crawler),
        "clip_to_crawler_static_mm3": common_volume(clips, crawler),
        "lid_m4_tool_path_to_shoes_mm3": common_volume(tools, shoes),
        "lid_m4_tool_path_to_clips_mm3": common_volume(tools, clips),
        "battery_vertical_removal_mm3": battery_sweep,
        "lid_removal_sweep_mm3": lid_sweep,
        "cbox_removal_sweep_mm3": cbox_sweep,
        "clip_to_lid_clearance_mm": v1().distance(clips, lid),
        "clip_to_lid_ear_clearance_mm": v1().distance(clips, towers),
        "clip_to_chimney_clearance_mm": v1().distance(clips, chimney),
        "cbox_saddle_minimum_clearance_mm": v1().distance(system, cbox),
        "crawler_static_minimum_clearance_mm": v1().distance(system, crawler),
        "bbox_new_holes": 0, "fixed_cross_bridge": False,
        "clip_install_after_bbox_seating": True,
        "bbox_vertical_insertion": "PASS_REFERENCE",
        "bbox_vertical_removal_after_clip_removal": "PASS_REFERENCE",
        "lid_removal_with_clips_installed": "PASS_REFERENCE",
        "battery_vertical_removal": "PASS_REFERENCE",
        "lid_m4_tool_access": "PASS_REFERENCE",
        "crawler_dynamic_clearance": "PHYSICAL_PENDING",
        "pto_slide_clutch_corridor": "NO_NEW_PLAN_ENVELOPE_BEYOND_V001_FRONT_SHOE_REFERENCE",
    }
    scalar_zero = [k for k in data if k.endswith("_mm3") and not isinstance(data[k], list)]
    if any(data[k] > TOL for k in scalar_zero):
        raise AssertionError("intersection " + json.dumps(data))
    if any(v > TOL for k in ("lid_removal_sweep_mm3", "cbox_removal_sweep_mm3") for v in data[k]):
        raise AssertionError("service sweep " + json.dumps(data))
    return data


def actual_geometry(out: Path) -> dict:
    imported = {path: cq.importers.importStep(str(out / path)) for path in STEPS}
    clips = {name: imported[f"artifacts/bbox_retention_clip_{name}.step"]
             for name in CLIP_CLEARANCES}
    fl = imported["artifacts/bbox_lower_cradle_v002_front_left.step"]
    fr = imported["artifacts/bbox_lower_cradle_v002_front_right.step"]
    rl = imported["artifacts/bbox_lower_cradle_v002_rear_left.step"]
    rr = imported["artifacts/bbox_lower_cradle_v002_rear_right.step"]
    lip_probe = fl.intersect(box(34, 20, 30, (0, BODY_SIDE_LEFT_LOCAL + 10,
                                              BBOX_LEDGE_TOP_Z + 15)))
    diff = v001_v002_diff()
    return {
        "permanent_lip_height_mm": 0.0 if volume(lip_probe) <= TOL else size(lip_probe)[2],
        "support_ledge_depth_mm": v1().actual_ledge_depth(fl),
        "r05_clearance_mm": actual_clip_clearance(clips["r05"]),
        "r08_clearance_mm": actual_clip_clearance(clips["r08"]),
        "r10_clearance_mm": actual_clip_clearance(clips["r10"]),
        "selected_uplift_gap_mm": actual_uplift_gap(clips["r08"], 0.8),
        "rail_interface_symmetric_difference_mm3": diff["rail_interface_symmetric_difference_mm3"],
        "protected_arm_symmetric_difference_mm3": diff["protected_arm_symmetric_difference_mm3"],
        "support_ledge_symmetric_difference_mm3": diff["support_ledge_symmetric_difference_mm3"],
        "front_left_bounds_mm": size(fl), "front_right_bounds_mm": size(fr),
        "rear_left_bounds_mm": size(rl), "rear_right_bounds_mm": size(rr),
        "coupon_bounds_mm": size(imported["artifacts/bbox_v002_support_clip_coupon.step"]),
        "r05_clip_bounds_mm": size(clips["r05"]),
        "r08_clip_bounds_mm": size(clips["r08"]),
        "r10_clip_bounds_mm": size(clips["r10"]),
        "tpu_pad_bounds_mm": size(imported["artifacts/bbox_lower_cradle_v002_tpu_pad.step"]),
        "rail_m5_count": 4, "retention_clip_count": 2,
        "retention_fastener_count": 2, "retention_fastener_clearance_diameter_mm": 5.5,
        "clip_contact_zone_from_bbox_bottom_mm": [1.0, 20.0],
    }


def inspect(out: Path) -> dict:
    report = {"step": {}, "stl": {}}
    for path in STEPS:
        shape = cq.importers.importStep(str(out / path))
        item = {"reload": "PASS" if shape.val().isValid() else "FAIL",
                "solids": len(shape.solids().vals()), "bounds_mm": size(shape)}
        if Path(path).stem in PRINT_NAMES:
            check = BOPAlgo_ArgumentAnalyzer(); check.SetShape1(shape.val().wrapped)
            check.SelfInterMode = True; check.Perform()
            item["self_intersections"] = int(check.HasFaulty())
        if item["reload"] != "PASS" or item.get("self_intersections", 0):
            raise AssertionError("invalid STEP " + path)
        report["step"][path] = item
    for path in STLS:
        quality = v1().stl_quality(out / path)
        report["stl"][path] = quality
        if not quality["pass"]:
            raise AssertionError("invalid STL " + path + json.dumps(quality))
    actual = actual_geometry(out)
    checks = {
        "permanent_lip_zero": abs(actual["permanent_lip_height_mm"]) <= TOL,
        "ledge": abs(actual["support_ledge_depth_mm"] - 10.0) <= TOL,
        "r05": abs(actual["r05_clearance_mm"] - 0.5) <= TOL,
        "r08": abs(actual["r08_clearance_mm"] - 0.8) <= TOL,
        "r10": abs(actual["r10_clearance_mm"] - 1.0) <= TOL,
        "uplift_gap": abs(actual["selected_uplift_gap_mm"] - 1.0) <= TOL,
        "rail_zero_diff": actual["rail_interface_symmetric_difference_mm3"] <= TOL,
        "arm_zero_diff": actual["protected_arm_symmetric_difference_mm3"] <= TOL,
        "ledge_zero_diff": actual["support_ledge_symmetric_difference_mm3"] <= TOL,
        "tpu": [round(v, 6) for v in actual["tpu_pad_bounds_mm"]] == [30.0, 10.0, 1.0],
    }
    if not all(checks.values()):
        raise AssertionError("actual geometry " + json.dumps({"actual": actual, "checks": checks}))
    report["actual_geometry"] = actual
    report["actual_geometry_checks"] = checks
    return report


def _svg(title: str, body: str, notes: list[str]) -> str:
    text = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#18324a}.rail{fill:#aeb8c2;stroke:#455a64;stroke-width:3}.shoe{fill:#ffd991;stroke:#a65d00;stroke-width:3}.clip{fill:#f2b6c2;stroke:#9f2742;stroke-width:3}.bbox{fill:#cdebd8;stroke:#26734d;stroke-width:3}.fail{fill:#f9c8c8;stroke:#b23a48;stroke-width:4}.pass{fill:none;stroke:#17804b;stroke-width:4}.dim{stroke:#d05224;stroke-width:3;fill:none}</style>'
    text += f'<text x="30" y="45" font-size="27">{title}</text>{body}'
    for i, note in enumerate(notes):
        text += f'<text x="30" y="{655 + i * 28}" font-size="16">{note}</text>'
    return text + '<text x="30" y="782" font-size="14">BBOX CRADLE V002 | SUPPORT FIRST, CLIP AFTER SEATING | LOAD/ROLLOVER HOLD</text></svg>'


def previews() -> dict[str, str]:
    v1fail = '<rect class="bbox" x="360" y="170" width="480" height="350"/><path class="fail" d="M325 500h55v-125h35v180h-90zM875 500h-55v-125h-35v180h90z"/><path class="dim" d="M600 110v390"/><text x="420" y="590" font-size="22">fixed 12 mm lips occupy insertion envelope</text>'
    support = '<rect class="bbox" x="360" y="170" width="480" height="350"/><path class="shoe" d="M325 500h90v55h-90zM875 500h-90v55h90z"/><path class="pass" d="M600 100v380"/><text x="425" y="590" font-size="22">permanent lip = 0; four ledges remain</text>'
    clip = '<rect class="bbox" x="300" y="180" width="360" height="330"/><path class="clip" d="M675 510h190v55H810v-300h55v-55h-105v300z"/><circle cx="790" cy="540" r="20" fill="white" stroke="#d05224" stroke-width="3"/><text x="720" y="610" font-size="20">R08 / 1 M5 / low body zone</text>'
    seq = '<g><rect class="shoe" x="80" y="480" width="240" height="55"/><rect class="bbox" x="105" y="170" width="190" height="300"/><rect class="shoe" x="470" y="480" width="240" height="55"/><rect class="bbox" x="495" y="170" width="190" height="300"/><path class="clip" d="M690 480h70v-170h35v225H690z"/><rect class="shoe" x="860" y="480" width="240" height="55"/><path class="dim" d="M905 160v280"/></g><text x="120" y="590" font-size="18">1 support</text><text x="515" y="590" font-size="18">2 seat</text><text x="900" y="590" font-size="18">3 clip / remove</text>'
    insertion = '<rect class="bbox" x="390" y="120" width="420" height="260"/><path class="dim" d="M600 80v400"/><path class="shoe" d="M300 520h220v55H300zM900 520H680v55h220z"/><rect class="pass" x="350" y="90" width="500" height="470"/>'
    compare = '<g transform="translate(0,0)"><text x="170" y="110" font-size="24">V001 FAIL</text><rect class="bbox" x="120" y="180" width="320" height="270"/><path class="fail" d="M90 450h55v-110h30v165H90zM470 450h-55v-110h-30v165h85z"/></g><g transform="translate(570,0)"><text x="170" y="110" font-size="24">V002 PASS_REFERENCE</text><rect class="bbox" x="120" y="180" width="320" height="270"/><path class="shoe" d="M90 450h85v55H90zM470 450h-85v55h85z"/><path class="pass" d="M280 130v300"/></g>'
    load = '<rect class="bbox" x="370" y="120" width="460" height="270"/><path class="shoe" d="M300 390h600v70H980v130H220V460h80z"/><path class="dim" d="M600 150v400"/><text x="630" y="250" font-size="20">static: body → four ledges → arms → rails</text><text x="630" y="290" font-size="20">lateral/uplift candidate: lower body → removable clips</text>'
    battery = '<rect class="bbox" x="300" y="270" width="600" height="310"/><rect x="440" y="330" width="320" height="230" fill="#ffe3e3" stroke="#b23a48" stroke-width="3"/><path class="dim" d="M600 330V90"/><path class="clip" d="M280 560h80v-120h25v140H280zM920 560h-80v-120h-25v140h105z"/>'
    lid = '<rect class="bbox" x="300" y="300" width="600" height="270"/><rect x="265" y="190" width="670" height="90" fill="#d7e7ff" stroke="#4267a5" stroke-width="3"/><path class="dim" d="M390 190V80M810 190V80"/><path class="clip" d="M280 570h85v-120h25v140H280zM920 570h-85v-120h-25v140h110z"/>'
    crawler = '<rect class="shoe" x="430" y="160" width="340" height="100"/><rect class="clip" x="520" y="330" width="160" height="170"/><rect class="fail" x="820" y="350" width="260" height="200"/><text x="830" y="325" font-size="20">static crawler envelope</text>'
    cbox = '<rect x="130" y="150" width="420" height="170" fill="#bfe9f5" stroke="#007596" stroke-width="3"/><rect class="shoe" x="650" y="410" width="300" height="120"/><path class="clip" d="M690 410h80v-120h35v120h85v60H690z"/><path class="pass" d="M585 110v470"/>'
    return {
        "previews/v001_failure.svg": _svg("V001 physical insertion failure", v1fail, ["Rail/M5/local single-shoe fit passed physically.", "All four fixed lips prevented normal BBOX installation."]),
        "previews/v002_support_only.svg": _svg("V002 permanent support-only shoes", support, ["10 mm ledges and V001 arms retained.", "All fixed vertical lips removed from permanent shoes."]),
        "previews/retention_clip_detail.svg": _svg("Low removable bolt-on retention clip", clip, ["R05/R08/R10 share one shoe interface; provisional R08.", "Positive uplift/load authority remains physical pending."]),
        "previews/clip_install_sequence.svg": _svg("Service sequence", seq, ["Shoes stay installed; clips are absent during insertion.", "Install two clips only after seating; remove clips before lifting BBOX."]),
        "previews/bbox_vertical_insertion.svg": _svg("Full vertical insertion sweep", insertion, ["Checked at +80/+60/+40/+20/final.", "Permanent-shoe intersection = 0 at every state."]),
        "previews/v001_v002_insertion_comparison.svg": _svg("Critical regression: V001 versus V002", compare, ["V001 physical failure is preserved as history.", "V002 permanent lip height = 0 mm."]),
        "previews/load_path.svg": _svg("Separated support/position/retention functions", load, ["Lid, gasket, chimney and lid ears are never structural.", "1.2 kg battery is known; full loaded BBOX mass is pending."]),
        "previews/battery_service.svg": _svg("Battery vertical service", battery, ["150.9×65.5; body92.5; terminal-inclusive99.4 mm.", "CAD sweep zero with selected clips installed."]),
        "previews/lid_service.svg": _svg("Lid and M4 tool service", lid, ["Clip zone stays on lower20 mm of the body.", "Lid/lid-ear/gasket/chimney and tool-path intersections zero."]),
        "previews/crawler_clearance.svg": _svg("Crawler static clearance", crawler, ["Static intersection zero; dynamic remains PHYSICAL_PENDING.", "Clip plan stays inside V001 front-shoe reference envelope."]),
        "previews/cbox_clearance.svg": _svg("CBOX saddle/removal clearance", cbox, ["Front-station left/right clips avoid the rear CBOX saddle.", "Global installed registration remains physical pending."]),
    }


def source_audit() -> dict:
    state = audit()
    return {
        "v001": {"source": V1_REL, "rail_mount": "PHYSICAL_FIT_PASS",
                  "single_shoe_local_interface": "PHYSICAL_FIT_PASS",
                  "four_shoe_bbox_insertion": "PHYSICAL_FAIL",
                  "failure_mode": "FIXED_LOCATING_LIP_INSTALLATION_ENVELOPE_CONFLICT"},
        "bbox": {"source": BBOX_REL, "lower_body_mm": [162.0, 76.0],
                 "upper_tower_envelope_mm": [180.0, 96.0],
                 "body_geometry": "VALID_FOR_MECHANICAL_FIT_STUDY",
                 "waterproof_authority": "SEPARATE_NOT_PROMOTED"},
        "battery": {"plan_mm": [150.9, 65.5], "body_height_mm": 92.5,
                    "terminal_inclusive_height_mm": 99.4, "mass_kg": 1.2,
                    "full_loaded_bbox_mass": "PHYSICAL_PENDING"},
        "cbox_v002": {"source": CBOX_V2_REL,
                      "rail_interface": "EXACT_V001_PASSED_BREP_REUSE"},
        "p25": {"source": P25_REL, "geometry_imported": False,
                "clutch_geometry_invented": False,
                "corridor_policy": "CLIPS_LOCAL_WITHIN_V001_FRONT_SHOE_XY_REFERENCE"},
        "protected": state["protected"],
        "protected_source_changed_count": state["protected_source_changed_count"],
    }


def documents() -> dict[str, str]:
    readme = f"""# BBOX 4-Point Lower Cradle V002 — Support-Only + Removable Clips

{STATUS}

V001 rail/M5, long-arm, local single-shoe and lower-support concepts passed
physical fit. Its all-four-shoe BBOX installation failed because the permanent
12 mm locating lips occupied the insertion envelope. V002 removes every fixed
lip (actual height0 mm) while preserving the10 mm ledges and exact rail BRep.

Two mirrored front-station clips (left/right) use one independent M5 through
bolt each and are installed only after the BBOX is seated. They stay within the
existing V001 front-shoe plan envelope. R08 is provisional; print the compact
support coupon plus R05/R08/R10 first. Do not print four full arms until coupon
physical PASS. Clips are clearance restraints, not a qualified structural or
rollover authority; the smooth lower BBOX has no released drilled capture
feature, so uplift capacity remains PHYSICAL_PENDING.

Printer: Bambu A1. PETG coupon/clips/shoes. Broad XZ face down, support OFF
candidate. Optional30×10×1 mm TPU remains non-structural. Nothing is staged or
committed; COMMIT_PATHS.txt is inventory only.
"""
    design = """# V002 design

Permanent system: four independent support-only shoes, four rail M5/T-nuts,
10 mm ledges, no cross-bridge, no BBOX holes and no vertical locating lips.
Front left/right shoes add a below-bottom attachment pad with one Ø5.5 clip
fastener passage. Rear shoes are V001 minus only the fixed lip.

Removable system: two mirrored low PETG clips at the front left/right lower-body
regions. One M5 through bolt plus metal washer/locknut candidate per clip. The
clip base attaches below the shoe pad; its wall begins1 mm above the BBOX bottom
datum and remains in the lower20 mm. R3–R5 intent is represented by broad roots,
an outer spine and no thin snap hook. Exact fastener length/stack is physical
selection pending.
"""
    failure = """# V001 physical failure record

V001_RAIL_MOUNT = PHYSICAL_FIT_PASS
V001_SINGLE_SHOE_LOCAL_INTERFACE = PHYSICAL_FIT_PASS
V001_FOUR_SHOE_BBOX_INSERTION = PHYSICAL_FAIL
FAILURE_MODE = FIXED_LOCATING_LIP_INSTALLATION_ENVELOPE_CONFLICT

One side/one shoe could fit. With all four shoes present, the fixed12 mm lower
locating lips prevented normal insertion. This is physical history and is not
overwritten by V002 CAD. V002 is a localized successor, not a redesign of the
passed rail/arm/ledge system.
"""
    diff = """# V001 → V002 local geometry diff

Intentional: remove all fixed12 mm lips and their local roots; add below-bottom
clip-fastener pads only to front left/right shoes. Preserved: exact rail/M5 BRep,
protected arm crop and10 mm body-support ledge. Machine report requires0 mm³
symmetric difference in all three protected crops. V001 remains read-only.
"""
    sweep = """# Vertical insertion sweep audit

The conservative180×96 mm maximum BBOX/tower projection and the actual body,
lid, gasket and chimney references are tested at Z offsets+80,+60,+40,+20 and
final seated. With all four permanent V002 shoes installed, every intersection
is0. V001's fixed lips intersect the conservative final insertion corridor and
the user-reported physical failure remains authoritative. Removal uses the same
path after both clips are removed.
"""
    clip = """# Removable retention clip design

Selected architecture: two mirrored clips on the front left/right shoes. The
BBOX is first lowered onto all four ledges; clips are then brought in from the
outside/below and secured individually. Body clearances are R05=0.5,R08=0.8,
R10=1.0 mm; R08 is provisional. The generated near-body wall starts1 mm above
the bottom datum and ends at20 mm. Clips never use lid, gasket, chimney, gland,
lid ears or a BBOX screw/hole.

The current smooth vertical lower body offers no CAD-released positive undercut.
Accordingly this clip geometry is ready for fit testing, while actual uplift,
shock and rollover retention are explicitly unqualified. Do not infer load
capacity from geometry or tighten enough to deform the waterproof enclosure.
"""
    matrix = """# Retention clip variant matrix

| ID | actual body clearance | role |
|---|---:|---|
| R05 | 0.500000 mm | tight comparison |
| R08 | 0.800000 mm | provisional primary |
| R10 | 1.000000 mm | loose fallback |

All variants share:30 mm width, one Ø5.5 M5 through-fastener interface,1 mm
bottom-datum gap,20 mm maximum body-zone height and the same robust base/spine.
Test the same support coupon with interchangeable clips.
"""
    coupon = """# BBOX V002 support + removable clip test

FIRST PRINT: compact support coupon plus R05/R08/R10 clips. PETG/Bambu A1,
broad XZ face down, support OFF candidate. The coupon shortens only the already
proven vertical drop; rail, body-side, ledge and clip-fastener fit surfaces stay
at their exact section dimensions.

support coupon rail mount: [ PASS / FAIL ]
BBOX lowers vertically onto ledge: [ PASS / FAIL ]
fixed-lip interference: [ NONE / YES ]
BBOX bottom fully supported: [ YES / NO ]
retention clip candidate: [ R05 / R08 / R10 ]
clip installs after BBOX seating: [ PASS / FAIL ]
clip fastener accessible: [ PASS / FAIL ]
clip body clearance: [ GOOD / TIGHT / LOOSE ]
uplift gap: ___ mm
BBOX upward movement with clip: [ NONE / SMALL / LARGE ]
lid / lid-ear interference: [ NONE / YES ]
clip removal: [ PASS / FAIL ]
BBOX vertical removal after clip removal: [ PASS / FAIL ]
PETG whitening: [ NONE / YES ]
FINAL: [ V002_SUPPORT_CLIP_COUPON_PHYSICAL_PASS / ADJUST_CLIP / REDESIGN_REQUIRED ]
"""
    full = """# Full V002 physical test plan

Only after coupon PASS: print FL/FR/RL/RR; mount four rail M5s; remove clips;
insert empty BBOX vertically; verify four contacts; install two selected clips;
verify one-fastener access; remove/open lid; verify all eight M4 tool paths;
remove battery vertically; remove clips; lift BBOX. Then repeat with real BBOX,
1.2 kg battery static load, light manual shake and controlled dry tilt. Stop on
wedge, crack, whitening, wall compression, tool blockage or fastener bottoming.
Powered rover, dynamic crawler, shock, vibration, uplift and rollover remain
separate later gates.
"""
    service = """# Battery and lid service audit

Battery authority:150.9×65.5 mm, body92.5 mm, terminal-inclusive99.4 mm,
mass1.2 kg. With four shoes and both R08 clips present, CAD intersections are0
for lid removal, battery vertical removal and all lid-M4 tool paths. Clip contact
with lid, gasket, chimney and lid ears is0. These are local PASS_REFERENCE
results; installed physical service and total loaded mass remain pending.
"""
    hold = """# Load path and rollover HOLD

Vertical static candidate: BBOX body → four ledges → V001 arms → rail feet →
four metal M5/T-nuts. Lateral candidate: lower body → two removable low clips.
Uplift candidate: lower body/clearance motion → clips → shoe pads → metal M5.

STRUCTURAL_LOAD_CAPACITY = PHYSICAL_PENDING
UPLIFT_LOAD_CAPACITY = PHYSICAL_PENDING
ROLLOVER = PHYSICAL_PENDING

No field-shock, vibration, loaded-driving, powered-rover, mud or field PASS is
claimed. Global BBOX XY, exact clip hardware stack, TPU hardness and dynamic
crawler/clutch integration also remain HOLD.
"""
    return {name: text.rstrip() + "\n" for name, text in zip(
        DOCS, [readme, design, failure, diff, sweep, clip, matrix, coupon, full,
               service, hold])}


def physical_template() -> dict:
    return {
        "title": "BBOX V002 SUPPORT + REMOVABLE CLIP TEST",
        "support_coupon_rail_mount": "PASS/FAIL",
        "bbox_lowers_vertically_onto_ledge": "PASS/FAIL",
        "fixed_lip_interference": "NONE/YES",
        "bbox_bottom_fully_supported": "YES/NO",
        "retention_clip_candidate": "R05/R08/R10",
        "clip_installs_after_bbox_seating": "PASS/FAIL",
        "clip_fastener_accessible": "PASS/FAIL",
        "clip_body_clearance": "GOOD/TIGHT/LOOSE",
        "uplift_gap_mm": None,
        "bbox_upward_movement_with_clip": "NONE/SMALL/LARGE",
        "lid_interference": "NONE/YES", "lid_ear_interference": "NONE/YES",
        "clip_removal": "PASS/FAIL",
        "bbox_vertical_removal_after_clip_removal": "PASS/FAIL",
        "petg_whitening": "NONE/YES",
        "final": "V002_SUPPORT_CLIP_COUPON_PHYSICAL_PASS/ADJUST_CLIP/REDESIGN_REQUIRED",
    }


def design_parameters() -> dict:
    return {
        "version": "BBOX_4POINT_LOWER_CRADLE_V002_SUPPORT_CLIP", "status": STATUS,
        "v001_physical": source_audit()["v001"],
        "permanent_shoes": {"count": 4, "independent": True,
                            "fixed_vertical_lip_height_mm": 0.0,
                            "support_ledge_depth_mm": 10.0,
                            "rail_m5_count": 4, "fixed_cross_bridge": False,
                            "bbox_new_holes": 0},
        "retention": {"architecture": "FRONT_STATION_LEFT_RIGHT_MIRRORED_TWO_CLIP",
                      "count": 2, "install_after_bbox_seating": True,
                      "attachment": "ONE_M5_THROUGH_BOLT_PLUS_METAL_WASHER_LOCKNUT_CANDIDATE_PER_CLIP",
                      "fastener_length": "PHYSICAL_SELECTION_PENDING",
                      "clearances_mm": CLIP_CLEARANCES,
                      "selected_provisional_clearance_mm": 0.8,
                      "uplift_gap_mm": 1.0, "body_zone_mm": [1.0, 20.0],
                      "positive_uplift_load_authority": "PHYSICAL_PENDING",
                      "rollover": "PHYSICAL_PENDING"},
        "service": intersection_data(), "insertion": insertion_audit(),
        "diff": v001_v002_diff(),
        "tpu": {"size_mm": [30.0, 10.0, 1.0], "structural": False,
                "required_for_geometric_fit": False, "hardness": "PHYSICAL_PENDING",
                "references_tested": ["WITHOUT_TPU", "WITH_1MM_TPU"]},
        "rail_height": {"left_top_mm": 255.0, "right_top_mm": 254.0,
                        "rigid_bridge": False, "optional_shims_mm": [0.5, 1.0]},
        "print": {"printer": "BAMBU_A1", "shoe_and_clip_material": "PETG",
                  "orientation": "BROAD_OUTSIDE_XZ_FACE_DOWN",
                  "support": "OFF_CANDIDATE", "slicer": "HOLD_SLICER_NOT_RUN",
                  "first_print": ["artifacts/bbox_v002_support_clip_coupon.stl",
                                  "artifacts/bbox_retention_clip_r05.stl",
                                  "artifacts/bbox_retention_clip_r08.stl",
                                  "artifacts/bbox_retention_clip_r10.stl"],
                  "full_v002_cradle_print": "HOLD_UNTIL_SUPPORT_CLIP_COUPON_PASS"},
    }


def generate(out: Path) -> None:
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    (out / "previews").mkdir(exist_ok=True)
    for path, shape in step_models().items():
        export_step(shape, out / path)
    for path, shape in stl_models().items():
        export_stl(shape, out / path)
    for path, text in previews().items():
        (out / path).write_text(text + "\n", encoding="utf-8", newline="\n")


def reproduce() -> dict:
    with tempfile.TemporaryDirectory(prefix="bbox_cradle_v002_repro_") as folder:
        out = Path(folder); generate(out)
        result = {p: sha(LANE / p) == sha(out / p) for p in STEPS + STLS + SVGS}
    if not all(result.values()):
        raise AssertionError("CAD reproducibility " + json.dumps(result))
    return {"byte_identical": result, "count": len(result),
            "pass_count": sum(result.values()), "pass": True}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def build() -> None:
    audit(); generate(LANE)
    quality = inspect(LANE); insertion = insertion_audit(); intersections = intersection_data()
    reproduction = reproduce(); diff = v001_v002_diff()
    for name, text in documents().items():
        (LANE / name).write_text(text, encoding="utf-8", newline="\n")
    write_json(LANE / "source_authority_audit.json", source_audit())
    write_json(LANE / "v001_v002_geometry_diff.json", diff)
    write_json(LANE / "insertion_sweep_audit.json", insertion)
    write_json(LANE / "intersection_report.json", intersections)
    write_json(LANE / "physical_result_template.json", physical_template())
    write_json(LANE / "design_parameters.json", design_parameters())
    write_json(LANE / "validation_report.json", {
        "status": "GENERATED_CONTRACT_PENDING", "quality": quality,
        "insertion": insertion, "intersections": intersections, "diff": diff,
        "regression": {"v001_failure_detected": insertion["v001_conservative_final_insertion_intersection_mm3"] > TOL,
                       "v002_all_states_zero": all(v <= TOL for v in insertion["v002_conservative_intersections_mm3"].values()),
                       "actual_generated_step_geometry_required": True},
        "cad_reproducibility": reproduction,
        "documentation_reproducibility": "PENDING_CONTRACT",
    })
    print(json.dumps({"build": "GENERATED_CONTRACT_PENDING", "STEP": len(STEPS),
                      "STL": len(STLS), "SVG": len(SVGS), "exact_paths": len(EXPECTED),
                      "actual": quality["actual_geometry"], "insertion": insertion,
                      "intersections": intersections, "reproducibility": reproduction}, indent=2))


def finalize(report: dict) -> None:
    if not report["pass"]:
        raise AssertionError("contract failed")
    write_json(LANE / "contract_test_report.json", report)
    validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    validation["status"] = STATUS
    validation["documentation_reproducibility"] = {
        name: (LANE / name).read_bytes() == text.encode("utf-8")
        for name, text in documents().items()
    }
    if not all(validation["documentation_reproducibility"].values()):
        raise AssertionError("documentation drift")
    write_json(LANE / "validation_report.json", validation)
    write_json(LANE / "manifest.json", {
        "lane": REL, "status": STATUS, "count": len(EXPECTED), "exact_paths": EXPECTED,
        "first_print": ["artifacts/bbox_v002_support_clip_coupon.stl",
                        "artifacts/bbox_retention_clip_r05.stl",
                        "artifacts/bbox_retention_clip_r08.stl",
                        "artifacts/bbox_retention_clip_r10.stl"],
        "full_print": "HOLD_UNTIL_SUPPORT_CLIP_COUPON_PASS",
        "printable_stl": STLS,
    })
    (LANE / "COMMIT_PATHS.txt").write_text(
        "\n".join(REL + "/" + path for path in EXPECTED) + "\n",
        encoding="utf-8", newline="\n")
    for name in ("repository_audit.json", "SHA256SUMS.txt"):
        if not (LANE / name).exists():
            (LANE / name).write_text("", encoding="ascii")
    write_json(LANE / "repository_audit.json", audit(full=True))
    (LANE / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(LANE / path)}  {path}\n" for path in EXPECTED if path != "SHA256SUMS.txt"),
        encoding="ascii", newline="\n")


def verify() -> None:
    state = audit(full=True)
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    if files != EXPECTED:
        raise AssertionError("exact paths")
    lines = (LANE / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
    if len(lines) != len(EXPECTED) - 1:
        raise AssertionError("SHA inventory")
    for line in lines:
        digest, path = line.split("  ", 1)
        if sha(LANE / path) != digest:
            raise AssertionError("SHA mismatch " + path)
    contract = json.loads((LANE / "contract_test_report.json").read_text(encoding="utf-8"))
    if not contract["pass"]:
        raise AssertionError("contract report")
    for name, text in documents().items():
        if (LANE / name).read_bytes() != text.encode("utf-8"):
            raise AssertionError("document byte drift " + name)
    quality = inspect(LANE); reproduction = reproduce()
    print(json.dumps({"verify": "PASS", "audit": state,
                      "quality_count": {"step": len(quality["step"]), "stl": len(quality["stl"])},
                      "actual": quality["actual_geometry"], "insertion": insertion_audit(),
                      "intersections": intersection_data(), "cad_reproducibility": reproduction,
                      "documentation_reproducibility": len(DOCS)}, indent=2))


def handoff() -> None:
    verify()
    target = Path(r"D:\Downloads") / (
        "Paddy_Swarm_BBOX_4POINT_LOWER_CRADLE_V002_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip")
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in EXPECTED:
            archive.write(LANE / path, LANE.name + "/" + path)
    with zipfile.ZipFile(target) as archive:
        expected = sorted(LANE.name + "/" + path for path in EXPECTED)
        if archive.testzip() is not None or sorted(archive.namelist()) != expected:
            raise AssertionError("ZIP manifest")
        for path in EXPECTED:
            if hashlib.sha256(archive.read(LANE.name + "/" + path)).hexdigest() != sha(LANE / path):
                raise AssertionError("ZIP byte mismatch " + path)
    print(json.dumps({"zip": str(target), "sha256": sha(target),
                      "members": len(EXPECTED)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true"); group.add_argument("--verify", action="store_true")
    group.add_argument("--zip", action="store_true"); args = parser.parse_args()
    if args.build: build()
    elif args.verify: verify()
    else: handoff()
