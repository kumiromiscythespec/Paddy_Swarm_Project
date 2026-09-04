"""BBOX four-point lower cradle with the proven CBOX V002 top-slot interface.

The current BBOX body is read-only.  This lane creates four independent PETG
shoes, three clearance coupons, an optional TPU pad and leveling shims.  Global
BBOX XY registration and structural/uplift qualification remain physical gates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

import cadquery as cq
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape


ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = Path(__file__).resolve().parent
REL = "cad/common_rover/bbox/bbox_4point_lower_cradle_v001"
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
TOL = 1.0e-6
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/BBOX_LOWER_CRADLE_COUPONS_PRINT_READY/"
    "FULL_4POINT_CRADLE_CAD_READY/FULL_CRADLE_PRINT_HOLD_UNTIL_COUPON_PASS/"
    "STRUCTURAL_LOAD_PHYSICAL_PENDING/UPLIFT_RETENTION_PENDING"
)

BBOX_REL = "cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065"
CBOX_V2_REL = "cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002"
CBOX_V1_REL = "cad/common_rover/bbox_cbox/cbox_transverse_cross_saddle_bbox_alignment_v001"
PHYSICAL_REL = "cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001"
TRANSFORM_REL = "cad/common_rover/physical_authority/common_rover_bbox_installed_transform_front_interface_audit_v001"

# Exact generated BBOX V004 body facts, independently checked again from STEP.
BBOX_CORE_X = 162.0
BBOX_CORE_Y = 76.0
BBOX_BODY_HEIGHT = 114.395
BBOX_WALL = 3.5
BBOX_FLOOR = 3.5
BBOX_BOTTOM_GLOBAL_Z = 148.0
BBOX_XY_CLASS = "LOCAL_CENTERED_FIT_REFERENCE_GLOBAL_XY_PHYSICAL_PENDING"

# Direct current-frame evidence.  Local assembly uses left rail top as Z0.
RAIL_CENTER = 189.0
RAIL_WIDTH = 20.0
RAIL_HEIGHT = 20.0
LEFT_RAIL_TOP_GLOBAL = 255.0
RIGHT_RAIL_TOP_GLOBAL = 254.0
RIGHT_RAIL_LOCAL_Z = -1.0
CRAWLER_LEFT_GLOBAL_Z = 181.0
CRAWLER_RIGHT_GLOBAL_Z = 180.0
BBOX_LEDGE_TOP_Z = BBOX_BOTTOM_GLOBAL_Z - LEFT_RAIL_TOP_GLOBAL  # -107
BBOX_REFERENCE_SEPARATION = 0.02

# Physically passing CBOX V002 coupon interface.  Keep these exact.
INTERFACE_X = 40.0
M5_THROUGH = 5.8
M5_TRANSVERSE_TRAVEL = 3.0
M5_POCKET_DIAMETER = 12.0
M5_POCKET_DEPTH = 4.5
M5_PER_SHOE = 1

# New BBOX lower-body interface candidates.
CLEARANCES = {"c03": 0.3, "c05": 0.5, "c08": 0.8}
SELECTED_CLEARANCE = 0.5
LEDGE_DEPTH = 10.0
LEDGE_THICKNESS = 8.0
LEDGE_BOTTOM_Z = BBOX_LEDGE_TOP_Z - LEDGE_THICKNESS
LIP_HEIGHT = 12.0
LIP_THICKNESS = 4.0
ROOT_RELIEF = 3.0
SUPPORT_X = 30.0
HANGER_X = 30.0
HANGER_Y = 5.0
TPU_PAD_T = 1.0

# Centered local-fit study only: rail-to-BBOX lateral registration is not global authority.
BODY_SIDE_FROM_LEFT_RAIL = BBOX_CORE_Y / 2 - RAIL_CENTER / 2  # -56.5
SUPPORT_Y_CENTER_LEFT = BODY_SIDE_FROM_LEFT_RAIL - LEDGE_DEPTH / 2  # -61.5
FRONT_MOUNT_X = 60.0
REAR_MOUNT_X = -14.0
FRONT_SUPPORT_OFFSET_X = 0.0
REAR_SUPPORT_OFFSET_X = -46.0
FRONT_SUPPORT_X = FRONT_MOUNT_X + FRONT_SUPPORT_OFFSET_X
REAR_SUPPORT_X = REAR_MOUNT_X + REAR_SUPPORT_OFFSET_X

PRINT_NAMES = [
    "bbox_lower_cradle_fit_coupon_c03", "bbox_lower_cradle_fit_coupon_c05",
    "bbox_lower_cradle_fit_coupon_c08", "bbox_lower_cradle_front_left",
    "bbox_lower_cradle_front_right", "bbox_lower_cradle_rear_left",
    "bbox_lower_cradle_rear_right", "bbox_lower_cradle_tpu_pad",
    "bbox_lower_cradle_leveling_shim_0p5", "bbox_lower_cradle_leveling_shim_1p0",
]
REFERENCE_NAMES = [
    "bbox_lower_cradle_assembly", "bbox_body_reference", "upper_rail_reference",
    "cbox_saddle_reference", "bbox_future_lower_retention_clip_keepout",
]
STEPS = [f"artifacts/{name}.step" for name in PRINT_NAMES + REFERENCE_NAMES]
STLS = [f"artifacts/{name}.stl" for name in PRINT_NAMES]
SVGS = [f"previews/{name}.svg" for name in [
    "cradle_top_view", "cradle_side_section", "cradle_front_section",
    "single_shoe_detail", "c03_c05_c08_comparison", "m5_tslot_mount",
    "bbox_load_path", "lid_isolation", "battery_removal_path",
    "cbox_interference_check", "crawler_clearance",
]]
DOCS = [
    "README.md", "BBOX_4POINT_LOWER_CRADLE_V001_DESIGN.md",
    "BBOX_MECHANICAL_MOUNT_PHILOSOPHY.md", "BBOX_BODY_INTERFACE_AUDIT.md",
    "CBOX_V002_TOP_TSLOT_REUSE.md", "CRADLE_CLEARANCE_VARIANT_MATRIX.md",
    "CRADLE_COUPON_TEST_PLAN.md", "FULL_CRADLE_PHYSICAL_TEST_PLAN.md",
    "BATTERY_SERVICE_AUDIT.md", "FUTURE_UPLIFT_RETENTION_PLAN.md",
    "GLOBAL_INTEGRATION_HOLDS.md",
]
REPORTS = [
    "design_parameters.json", "validation_report.json", "contract_test_report.json",
    "source_authority_audit.json", "bbox_body_geometry_audit.json",
    "intersection_report.json", "physical_result_template.json",
    "repository_audit.json", "manifest.json",
]
EXPECTED = sorted([
    Path(__file__).name, "tests/test_bbox_4point_lower_cradle_v001.py",
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
    spec.loader.exec_module(module)
    return module


@lru_cache(None)
def bbox_v4():
    return load_module("read_only_bbox_v004", ROOT / BBOX_REL / "build_bbox_v004_g065.py")


@lru_cache(None)
def cbox_v2():
    return load_module("read_only_cbox_v002", ROOT / CBOX_V2_REL / "build_cbox_transverse_top_tslot_saddle_v002.py")


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


def distance(a: cq.Workplane, b: cq.Workplane) -> float:
    op = BRepExtrema_DistShapeShape(a.val().wrapped, b.val().wrapped)
    op.Perform()
    if not op.IsDone():
        raise AssertionError("distance failed")
    return op.Value()


def bounds(shape: cq.Workplane) -> list[float]:
    bb = shape.val().BoundingBox()
    return [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]


def size(shape: cq.Workplane) -> list[float]:
    b = bounds(shape)
    return [b[i + 3] - b[i] for i in range(3)]


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for point in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


@lru_cache(None)
def proven_top_interface() -> cq.Workplane:
    """Exact rail-contact/M5 subset of the user-confirmed CBOX V002 coupon."""
    mask = box(INTERFACE_X, RAIL_WIDTH, 30.0, (0, 0, 15.0))
    return cbox_v2().mount_coupon().intersect(mask).clean()


def triangular_yz(points: list[tuple[float, float]], x_center: float, length: float) -> cq.Workplane:
    return (cq.Workplane("YZ").polyline(points).close().extrude(length / 2, both=True)
            .translate((x_center, 0, 0)))


def left_shoe(station: str, clearance: float) -> cq.Workplane:
    offset = FRONT_SUPPORT_OFFSET_X if station.upper() == "FRONT" else REAR_SUPPORT_OFFSET_X
    hanger = [
        (-HANGER_X / 2, -15), (HANGER_X / 2, -15),
        (HANGER_X / 2, -10), (-HANGER_X / 2, -10),
    ]
    pad = [
        (offset - SUPPORT_X / 2, SUPPORT_Y_CENTER_LEFT - LEDGE_DEPTH / 2),
        (offset + SUPPORT_X / 2, SUPPORT_Y_CENTER_LEFT - LEDGE_DEPTH / 2),
        (offset + SUPPORT_X / 2, SUPPORT_Y_CENTER_LEFT + LEDGE_DEPTH / 2),
        (offset - SUPPORT_X / 2, SUPPORT_Y_CENTER_LEFT + LEDGE_DEPTH / 2),
    ]
    plan = convex_hull(hanger + pad)
    ledge = (cq.Workplane("XY", origin=(0, 0, LEDGE_BOTTOM_Z))
             .polyline(plan).close().extrude(LEDGE_THICKNESS))
    hanger_solid = box(HANGER_X, HANGER_Y, 8.0 - LEDGE_BOTTOM_Z,
                       (0, -12.5, (8.0 + LEDGE_BOTTOM_Z) / 2))
    top_root = triangular_yz([(-22, 0), (-10, 0), (-10, 8)], 0, HANGER_X)
    bottom_root = triangular_yz(
        [(-25, BBOX_LEDGE_TOP_Z), (-10, BBOX_LEDGE_TOP_Z),
         (-10, BBOX_LEDGE_TOP_Z + 15)], 0, HANGER_X)
    near = BODY_SIDE_FROM_LEFT_RAIL + clearance
    lip = box(SUPPORT_X, LIP_THICKNESS, LIP_HEIGHT,
              (offset, near + LIP_THICKNESS / 2, BBOX_LEDGE_TOP_Z + LIP_HEIGHT / 2))
    lip_root = triangular_yz(
        [(near + LIP_THICKNESS, BBOX_LEDGE_TOP_Z),
         (near + LIP_THICKNESS + ROOT_RELIEF, BBOX_LEDGE_TOP_Z),
         (near + LIP_THICKNESS, BBOX_LEDGE_TOP_Z + ROOT_RELIEF)],
        offset, SUPPORT_X,
    )
    return (proven_top_interface().union(hanger_solid).union(top_root)
            .union(ledge).union(bottom_root).union(lip).union(lip_root).clean())


def shoe(side: str, station: str, clearance: float = SELECTED_CLEARANCE) -> cq.Workplane:
    result = left_shoe(station, clearance)
    return result if side.upper() == "LEFT" else result.mirror("XZ").clean()


def coupon(clearance: float) -> cq.Workplane:
    return shoe("LEFT", "FRONT", clearance)


def tpu_pad(thickness: float = TPU_PAD_T) -> cq.Workplane:
    return box(SUPPORT_X, LEDGE_DEPTH, thickness, (0, 0, thickness / 2))


def leveling_shim(thickness: float) -> cq.Workplane:
    return box(SUPPORT_X, LEDGE_DEPTH, thickness, (0, 0, thickness / 2))


def rails_reference() -> cq.Workplane:
    return cbox_v2().rails_reference().translate((0, 0, -LEFT_RAIL_TOP_GLOBAL))


def cbox_saddles_reference() -> cq.Workplane:
    return cbox_v2().placed_saddles().translate((0, 0, -LEFT_RAIL_TOP_GLOBAL))


def cbox_removal_reference() -> cq.Workplane:
    return cbox_v2().placed_cbox().translate((0, 0, -LEFT_RAIL_TOP_GLOBAL))


def crawler_reference() -> cq.Workplane:
    return cbox_v2().crawler_reference().translate((0, 0, -LEFT_RAIL_TOP_GLOBAL))


def bbox_body_source() -> cq.Workplane:
    return cq.importers.importStep(str(ROOT / BBOX_REL / "artifacts/compact_field_bbox_v004_g065_body.step"))


def bbox_lid_source() -> cq.Workplane:
    return cq.importers.importStep(str(ROOT / BBOX_REL / "artifacts/compact_field_bbox_v004_g065_lid.step"))


def bbox_body_placed() -> cq.Workplane:
    return bbox_body_source().translate((0, 0, BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION))


def bbox_lid_placed() -> cq.Workplane:
    return bbox_lid_source().translate((0, 0, BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION + BBOX_BODY_HEIGHT))


def bbox_gasket_placed() -> cq.Workplane:
    return bbox_v4().gasket().translate((0, 0, BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION))


def bbox_chimney_placed() -> cq.Workplane:
    return bbox_v4().chimney().translate(
        (0, 0, BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION + BBOX_BODY_HEIGHT))


def bbox_tower_envelope() -> cq.Workplane:
    z0 = BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION + BBOX_BODY_HEIGHT - 8.895
    return compound([cylinder_z(12.0, 8.895, (x, y, z0 + 8.895 / 2))
                     for x, y in bbox_v4().p.M4_POINTS])


def bbox_m4_tool_paths() -> cq.Workplane:
    return compound([cylinder_z(14.0, 180.0, (x, y, -10.0))
                     for x, y in bbox_v4().p.M4_POINTS])


def placed_shoe(side: str, station: str) -> cq.Workplane:
    x = FRONT_MOUNT_X if station.upper() == "FRONT" else REAR_MOUNT_X
    y = RAIL_CENTER / 2 if side.upper() == "LEFT" else -RAIL_CENTER / 2
    z = 0.0 if side.upper() == "LEFT" else RIGHT_RAIL_LOCAL_Z
    return shoe(side, station).translate((x, y, z))


def placed_shoes() -> cq.Workplane:
    return compound([placed_shoe(side, station)
                     for station in ("FRONT", "REAR") for side in ("LEFT", "RIGHT")])


def placed_right_leveling_shims() -> cq.Workplane:
    return compound([
        leveling_shim(1.0).translate((FRONT_SUPPORT_X, -BBOX_CORE_Y / 2 + LEDGE_DEPTH / 2,
                                     BBOX_LEDGE_TOP_Z - 1.0)),
        leveling_shim(1.0).translate((REAR_SUPPORT_X, -BBOX_CORE_Y / 2 + LEDGE_DEPTH / 2,
                                     BBOX_LEDGE_TOP_Z - 1.0)),
    ])


def future_retention_keepout() -> cq.Workplane:
    return compound([
        box(12, 40, 20, (BBOX_CORE_X / 2 + 6, 0, BBOX_LEDGE_TOP_Z + 14)),
        box(12, 40, 20, (-BBOX_CORE_X / 2 - 6, 0, BBOX_LEDGE_TOP_Z + 14)),
    ])


def assembly() -> cq.Workplane:
    return compound([rails_reference(), placed_shoes(), placed_right_leveling_shims(),
                     bbox_body_placed(), bbox_lid_placed(), cbox_saddles_reference(),
                     future_retention_keepout()])


def step_models() -> dict[str, cq.Workplane]:
    models = {
        "artifacts/bbox_lower_cradle_fit_coupon_c03.step": coupon(0.3),
        "artifacts/bbox_lower_cradle_fit_coupon_c05.step": coupon(0.5),
        "artifacts/bbox_lower_cradle_fit_coupon_c08.step": coupon(0.8),
        "artifacts/bbox_lower_cradle_front_left.step": shoe("LEFT", "FRONT"),
        "artifacts/bbox_lower_cradle_front_right.step": shoe("RIGHT", "FRONT"),
        "artifacts/bbox_lower_cradle_rear_left.step": shoe("LEFT", "REAR"),
        "artifacts/bbox_lower_cradle_rear_right.step": shoe("RIGHT", "REAR"),
        "artifacts/bbox_lower_cradle_tpu_pad.step": tpu_pad(),
        "artifacts/bbox_lower_cradle_leveling_shim_0p5.step": leveling_shim(0.5),
        "artifacts/bbox_lower_cradle_leveling_shim_1p0.step": leveling_shim(1.0),
        "artifacts/bbox_lower_cradle_assembly.step": assembly(),
        "artifacts/bbox_body_reference.step": bbox_body_source(),
        "artifacts/upper_rail_reference.step": rails_reference(),
        "artifacts/cbox_saddle_reference.step": cbox_saddles_reference(),
        "artifacts/bbox_future_lower_retention_clip_keepout.step": future_retention_keepout(),
    }
    return models


def print_oriented(shape: cq.Workplane, flat: bool) -> cq.Workplane:
    if flat:
        return shape
    rotated = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    return rotated.translate((0, 0, -bounds(rotated)[2]))


def stl_models() -> dict[str, cq.Workplane]:
    models = step_models()
    result = {}
    for name in PRINT_NAMES:
        flat = name.endswith(("tpu_pad", "shim_0p5", "shim_1p0"))
        result[f"artifacts/{name}.stl"] = print_oriented(models[f"artifacts/{name}.step"], flat)
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
    lines = ["solid BBOX_4POINT_LOWER_CRADLE_V001"]
    for tri in tris:
        a, b, c = [vertices[i] for i in tri]
        normal = (b - a).cross(c - a).normalized()
        lines.extend(["  facet normal " + " ".join(f"{v:.12g}" for v in normal.toTuple()),
                      "    outer loop"])
        for point in (a, b, c):
            lines.append("      vertex " + " ".join(f"{v:.9f}" for v in point.toTuple()))
        lines.extend(["    endloop", "  endfacet"])
    lines.append("endsolid BBOX_4POINT_LOWER_CRADLE_V001")
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def triangles(path: Path) -> list:
    vertices = [tuple(map(float, line.split()[1:]))
                for line in path.read_text(encoding="ascii").splitlines()
                if line.lstrip().startswith("vertex ")]
    if len(vertices) % 3:
        raise AssertionError("invalid STL")
    return [tuple(vertices[i:i + 3]) for i in range(0, len(vertices), 3)]


def stl_quality(path: Path) -> dict:
    tri_data = triangles(path)
    edges, winding = Counter(), Counter()
    links, graph = defaultdict(list), defaultdict(set)
    degenerate = 0
    for a, b, c in tri_data:
        cross = (cq.Vector(*b) - cq.Vector(*a)).cross(cq.Vector(*c) - cq.Vector(*a))
        degenerate += int(cross.Length < 1e-9 or len({a, b, c}) < 3)
        for first, second in ((a, b), (b, c), (c, a)):
            edge = tuple(sorted((first, second)))
            edges[edge] += 1; winding[edge] += 1 if (first, second) == edge else -1
            graph[first].add(second); graph[second].add(first)
        for first, second, third in ((a, b, c), (b, c, a), (c, a, b)):
            links[first].append((second, third))
    bad_links = 0
    for pairs in links.values():
        local = defaultdict(set)
        for first, second in pairs:
            local[first].add(second); local[second].add(first)
        seen, stack = set(), [next(iter(local))]
        while stack:
            point = stack.pop()
            if point in seen: continue
            seen.add(point); stack.extend(local[point] - seen)
        bad_links += int(len(seen) != len(local) or any(len(v) != 2 for v in local.values()))
    result = {
        "triangles": len(tri_data), "bad_edges": sum(v != 2 for v in edges.values()),
        "bad_winding_edges": sum(v != 0 for v in winding.values()),
        "bad_vertex_links": bad_links, "degenerate_triangles": degenerate,
        "duplicate_triangles": len(tri_data) - len({tuple(sorted(t)) for t in tri_data}),
    }
    result["watertight"] = result["bad_edges"] == 0
    result["manifold"] = result["watertight"] and result["bad_vertex_links"] == 0
    result["pass"] = not any(result[k] for k in ["bad_edges", "bad_winding_edges",
                                                   "bad_vertex_links", "degenerate_triangles",
                                                   "duplicate_triangles"])
    return result


def void_metrics(shape: cq.Workplane, z: float) -> dict:
    probe = box(20, 19, 0.04, (0, 0, z))
    void = probe.cut(shape)
    bb = void.val().BoundingBox()
    return {"x_width_mm": bb.xlen, "y_width_mm": bb.ylen,
            "center_x_mm": bb.center.x, "center_y_mm": bb.center.y}


def actual_clearance(shape: cq.Workplane) -> float:
    probe = shape.intersect(box(SUPPORT_X - 2, 12, 8,
                                (0, BODY_SIDE_FROM_LEFT_RAIL + 6, BBOX_LEDGE_TOP_Z + 6)))
    if not probe.solids().vals():
        raise AssertionError("lip probe missed")
    return bounds(probe)[1] - BODY_SIDE_FROM_LEFT_RAIL


def actual_ledge_depth(shape: cq.Workplane, support_offset: float = 0.0) -> float:
    probe = shape.intersect(box(1, 100, 0.04,
                                (support_offset, -35, BBOX_LEDGE_TOP_Z - 0.02)))
    return BODY_SIDE_FROM_LEFT_RAIL - bounds(probe)[1]


def actual_lip_height(shape: cq.Workplane, support_offset: float = 0.0) -> float:
    near = BODY_SIDE_FROM_LEFT_RAIL + SELECTED_CLEARANCE
    probe = shape.intersect(box(SUPPORT_X - 2, LIP_THICKNESS - 0.5, 40,
                                (support_offset, near + LIP_THICKNESS / 2,
                                 BBOX_LEDGE_TOP_Z + 5)))
    return bounds(probe)[5] - BBOX_LEDGE_TOP_Z


def bbox_body_audit() -> dict:
    body = bbox_body_source()
    lower = body.intersect(box(300, 300, 0.2, (0, 0, 0.1)))
    upper = body.intersect(box(300, 300, 9.395, (0, 0, 109.6975)))
    bottom_faces = [f for f in body.faces().vals() if f.geomType() == "PLANE"
                    and f.normalAt().z < -0.999 and abs(f.Center().z) < TOL]
    return {
        "source": BBOX_REL + "/artifacts/compact_field_bbox_v004_g065_body.step",
        "body_bounds_mm": size(body), "lower_body_core_footprint_mm": size(lower)[:2],
        "bottom_z_mm": bounds(body)[2], "bottom_face_area_mm2": sum(f.Area() for f in bottom_faces),
        "lower_corner_radius_mm": 0.0, "lower_taper": "NONE",
        "lower_chamfer": "NONE", "wall_mm": BBOX_WALL, "floor_mm": BBOX_FLOOR,
        "top_m4_tower_envelope_xy_mm": size(upper)[:2],
        "m4_tower_centers_mm": bbox_v4().p.M4_POINTS, "m4_tower_count": len(bbox_v4().p.M4_POINTS),
        "lower_footprint_class": "ACTUAL_GENERATED_STEP",
        "top_tower_class": "ACTUAL_GENERATED_STEP_SEPARATE_FROM_LOWER_FOOTPRINT",
        "body_geometry_reference": "VALID_FOR_MECHANICAL_FIT_STUDY",
        "waterproof_authority": "SEPARATE_NOT_PROMOTED",
        "small_g065_dummy_water": "PASS",
        "full_v004_60_min_water": "FAIL_UNRESOLVED_SLOW_INGRESS_USER_LATEST_RESULT",
    }


def actual_geometry(out: Path) -> dict:
    imported = {path: cq.importers.importStep(str(out / path)) for path in STEPS}
    c03 = imported["artifacts/bbox_lower_cradle_fit_coupon_c03.step"]
    c05 = imported["artifacts/bbox_lower_cradle_fit_coupon_c05.step"]
    c08 = imported["artifacts/bbox_lower_cradle_fit_coupon_c08.step"]
    fl = imported["artifacts/bbox_lower_cradle_front_left.step"]
    fr = imported["artifacts/bbox_lower_cradle_front_right.step"]
    rl = imported["artifacts/bbox_lower_cradle_rear_left.step"]
    rr = imported["artifacts/bbox_lower_cradle_rear_right.step"]
    interface = proven_top_interface()
    crop = fl.intersect(box(INTERFACE_X, RAIL_WIDTH, 30, (0, 0, 15)))
    interface_delta = volume(crop.cut(interface)) + volume(interface.cut(crop))
    contacts = []
    for side, station in [("LEFT", "FRONT"), ("RIGHT", "FRONT"),
                          ("LEFT", "REAR"), ("RIGHT", "REAR")]:
        mount_x = FRONT_MOUNT_X if station == "FRONT" else REAR_MOUNT_X
        rail_y = RAIL_CENTER / 2 if side == "LEFT" else -RAIL_CENTER / 2
        # Measure in each generated part's own STEP coordinates.  This avoids
        # confusing the physical -1 mm right-rail placement with part geometry.
        local_body_probe = box(BBOX_CORE_X, BBOX_CORE_Y, 0.02,
                               (-mount_x, -rail_y, BBOX_LEDGE_TOP_Z - 0.01))
        contacts.append(common_volume(shoe(side, station), local_body_probe) / 0.02)
    return {
        "clearance_c03_mm": actual_clearance(c03),
        "clearance_c05_mm": actual_clearance(c05),
        "clearance_c08_mm": actual_clearance(c08),
        "support_ledge_depth_mm": actual_ledge_depth(c05),
        "vertical_lip_height_mm": actual_lip_height(fl),
        "m5_through_actual": void_metrics(c05, 1.0),
        "m5_pocket_actual": void_metrics(c05, 5.0),
        "proven_interface_symmetric_difference_mm3": interface_delta,
        "shoe_contact_plane_local_z_mm": BBOX_LEDGE_TOP_Z,
        "contact_area_per_shoe_mm2": contacts,
        "total_contact_area_mm2": sum(contacts),
        "front_left_bounds_mm": size(fl), "front_right_bounds_mm": size(fr),
        "rear_left_bounds_mm": size(rl), "rear_right_bounds_mm": size(rr),
        "coupon_bounds_mm": size(c05),
        "tpu_pad_bounds_mm": size(imported["artifacts/bbox_lower_cradle_tpu_pad.step"]),
        "shim_0p5_bounds_mm": size(imported["artifacts/bbox_lower_cradle_leveling_shim_0p5.step"]),
        "shim_1p0_bounds_mm": size(imported["artifacts/bbox_lower_cradle_leveling_shim_1p0.step"]),
        "front_rear_support_center_spacing_mm": FRONT_SUPPORT_X - REAR_SUPPORT_X,
        "left_right_effective_support_spacing_mm": BBOX_CORE_Y - LEDGE_DEPTH,
        "front_rear_rail_fastener_spacing_mm": FRONT_MOUNT_X - REAR_MOUNT_X,
        "m5_per_shoe": M5_PER_SHOE, "total_m5": 4,
    }


def intersection_data() -> dict:
    cradle = placed_shoes(); body = bbox_body_placed(); lid = bbox_lid_placed()
    gasket = bbox_gasket_placed(); chimney = bbox_chimney_placed()
    towers = bbox_tower_envelope(); cbox_saddle = cbox_saddles_reference()
    crawler = crawler_reference(); cbox = cbox_removal_reference()
    lid_sweep = [common_volume(lid.translate((0, 0, dz)), cradle) for dz in (0, 20, 40, 80)]
    body_sweep = [common_volume(body.translate((0, 0, dz)), cradle) for dz in (0, 20, 40, 80, 120)]
    cbox_sweep = [common_volume(cbox.translate((0, 0, dz)), cradle) for dz in (0, 20, 40, 80)]
    battery = bbox_v4().p.removal_sweep().translate((0, 0, BBOX_LEDGE_TOP_Z + BBOX_REFERENCE_SEPARATION))
    return {
        "cradle_to_bbox_body_mm3": common_volume(cradle, body),
        "cradle_to_bbox_lid_mm3": common_volume(cradle, lid),
        "cradle_to_gasket_mm3": common_volume(cradle, gasket),
        "cradle_to_chimney_mm3": common_volume(cradle, chimney),
        "cradle_to_lid_m4_ears_mm3": common_volume(cradle, towers),
        "cradle_to_cbox_saddle_mm3": common_volume(cradle, cbox_saddle),
        "cradle_to_crawler_static_mm3": common_volume(cradle, crawler),
        "bbox_lid_m4_tool_path_mm3": common_volume(cradle, bbox_m4_tool_paths()),
        "battery_vertical_removal_to_cradle_mm3": common_volume(battery, cradle),
        "bbox_lid_removal_sweep_mm3": lid_sweep,
        "bbox_body_removal_sweep_mm3": body_sweep,
        "cbox_removal_sweep_mm3": cbox_sweep,
        "bbox_lid_minimum_clearance_mm": distance(cradle, lid),
        "bbox_lid_ear_minimum_clearance_mm": distance(cradle, towers),
        "chimney_minimum_clearance_mm": distance(cradle, chimney),
        "cbox_saddle_minimum_clearance_mm": distance(cradle, cbox_saddle),
        "crawler_static_minimum_clearance_mm": distance(cradle, crawler),
        "bbox_new_hole_count": 0, "fixed_left_right_bridge": False,
        "bbox_lid_is_structural_mount": False, "bbox_lid_m4_used_for_frame_mount": False,
        "bbox_modification_count": 0,
        "bbox_lid_removal": "PASS_REFERENCE", "battery_vertical_removal": "PASS_REFERENCE",
        "lid_m4_tool_access": "PASS_REFERENCE", "bbox_body_removal": "PASS_REFERENCE",
        "cbox_service_path": "PASS_LOCAL_REFERENCE",
        "crawler_dynamic_clearance": "PHYSICAL_PENDING",
        "global_bbox_xy_registration": "PHYSICAL_PENDING",
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
        report["stl"][path] = stl_quality(out / path)
        if not report["stl"][path]["pass"]:
            raise AssertionError("invalid STL " + path + json.dumps(report["stl"][path]))
    actual = actual_geometry(out)
    checks = {
        "c03": abs(actual["clearance_c03_mm"] - 0.3) <= TOL,
        "c05": abs(actual["clearance_c05_mm"] - 0.5) <= TOL,
        "c08": abs(actual["clearance_c08_mm"] - 0.8) <= TOL,
        "ledge": abs(actual["support_ledge_depth_mm"] - LEDGE_DEPTH) <= TOL,
        "lip": abs(actual["vertical_lip_height_mm"] - LIP_HEIGHT) <= TOL,
        "m5_through_x": abs(actual["m5_through_actual"]["x_width_mm"] - M5_THROUGH) <= TOL,
        "m5_through_y": abs(actual["m5_through_actual"]["y_width_mm"] - (M5_THROUGH + M5_TRANSVERSE_TRAVEL)) <= TOL,
        "m5_pocket_x": abs(actual["m5_pocket_actual"]["x_width_mm"] - M5_POCKET_DIAMETER) <= TOL,
        "m5_pocket_y": abs(actual["m5_pocket_actual"]["y_width_mm"] - (M5_POCKET_DIAMETER + M5_TRANSVERSE_TRAVEL)) <= TOL,
        "interface_zero_diff": actual["proven_interface_symmetric_difference_mm3"] <= TOL,
        "tpu": abs(actual["tpu_pad_bounds_mm"][2] - TPU_PAD_T) <= TOL,
        "shim05": abs(actual["shim_0p5_bounds_mm"][2] - 0.5) <= TOL,
        "shim10": abs(actual["shim_1p0_bounds_mm"][2] - 1.0) <= TOL,
        "contact_area": (all(v + 1e-4 >= SUPPORT_X * LEDGE_DEPTH
                             for v in actual["contact_area_per_shoe_mm2"])
                         and abs(actual["contact_area_per_shoe_mm2"][0]
                                 - actual["contact_area_per_shoe_mm2"][1]) <= 1e-4
                         and abs(actual["contact_area_per_shoe_mm2"][2]
                                 - actual["contact_area_per_shoe_mm2"][3]) <= 1e-4),
    }
    if not all(checks.values()):
        raise AssertionError("actual geometry " + json.dumps({"actual": actual, "checks": checks}))
    report["actual_geometry"] = actual; report["actual_geometry_checks"] = checks
    return report


def regression() -> dict:
    with tempfile.TemporaryDirectory(prefix="bbox_cradle_regression_") as folder:
        path = Path(folder) / "wrong_c06.step"
        export_step(coupon(0.6), path)
        wrong = cq.importers.importStep(str(path))
        rejected = abs(actual_clearance(wrong) - SELECTED_CLEARANCE) > TOL
        if not rejected:
            raise AssertionError("clearance offset regression missed")
    return {"requested_c05_actual_c06_rejected": rejected,
            "actual_step_geometry_required": True}


def _svg(title: str, body: str, notes: list[str]) -> str:
    text = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#18324a}.rail{fill:#aeb8c2;stroke:#455a64;stroke-width:3}.shoe{fill:#ffd991;stroke:#a65d00;stroke-width:3}.bbox{fill:#cdebd8;stroke:#26734d;stroke-width:3}.cbox{fill:#bfe9f5;stroke:#007596;stroke-width:3}.hold{fill:none;stroke:#b23a48;stroke-width:3;stroke-dasharray:8 6}.dim{stroke:#d05224;stroke-width:3;fill:none}</style>'
    text += f'<text x="30" y="45" font-size="27">{title}</text>{body}'
    for i, note in enumerate(notes):
        text += f'<text x="30" y="{655 + i * 28}" font-size="16">{note}</text>'
    return text + '<text x="30" y="782" font-size="14">BBOX 4-POINT LOWER CRADLE V001 | COUPON FIRST | UPLIFT/LOAD HOLD</text></svg>'


def previews() -> dict[str, str]:
    top = '<rect class="bbox" x="280" y="230" width="640" height="300"/><rect class="rail" x="180" y="160" width="840" height="55"/><rect class="rail" x="180" y="545" width="840" height="55"/><g class="shoe"><rect x="700" y="190" width="100" height="95"/><rect x="700" y="515" width="100" height="55"/><rect x="350" y="190" width="100" height="95"/><rect x="350" y="515" width="100" height="55"/></g>'
    side = '<rect class="rail" x="760" y="120" width="190" height="90"/><path class="shoe" d="M720 120h230v80H850v350H500v-75h280V120z"/><rect class="bbox" x="320" y="400" width="300" height="170"/><text x="510" y="620" font-size="20">body bottom supported; lid above remains isolated</text>'
    front = '<rect class="rail" x="160" y="140" width="170" height="90"/><rect class="rail" x="870" y="148" width="170" height="90"/><path class="shoe" d="M160 140h170v70H300v330H480v70H270V230H160z"/><path class="shoe" d="M1040 148H870v70h30v322H720v70h210V238h110z"/><rect class="bbox" x="450" y="390" width="300" height="220"/>'
    detail = '<path class="shoe" d="M760 120h220v80H870v340H520v-80h290V120z"/><rect class="bbox" x="350" y="390" width="300" height="210"/><line class="dim" x1="520" y1="430" x2="650" y2="430"/><text x="525" y="415" font-size="18">10 mm ledge</text><text x="665" y="500" font-size="18">12 mm lip · 0.5 gap</text>'
    variants = '<rect class="bbox" x="180" y="260" width="180" height="260"/><path class="shoe" d="M100 520h300v55H350v-180h30v-80h-30v80"/><rect class="bbox" x="510" y="260" width="180" height="260"/><path class="shoe" d="M430 520h300v55H680v-180h30v-80h-30v80"/><rect class="bbox" x="840" y="260" width="180" height="260"/><path class="shoe" d="M760 520h300v55H1010v-180h30v-80h-30v80"/><text x="220" y="620" font-size="20">C03</text><text x="550" y="620" font-size="20">C05</text><text x="880" y="620" font-size="20">C08</text>'
    m5 = '<rect class="shoe" x="250" y="160" width="700" height="170"/><rect class="rail" x="320" y="330" width="560" height="170"/><rect x="535" y="160" width="130" height="300" rx="45" fill="#fff" stroke="#d05224" stroke-width="3"/><text x="690" y="235" font-size="19">exact CBOX V002 coupon interface</text><text x="690" y="275" font-size="19">5.8×8.8 / pocket12×15×4.5</text>'
    load = '<rect class="bbox" x="400" y="100" width="400" height="230"/><path class="shoe" d="M380 330h440v70H900v130H300V400h80z"/><rect class="rail" x="180" y="530" width="840" height="75"/><path class="dim" d="M600 130v430"/><text x="625" y="230" font-size="20">BODY → ledge → hanger → rail → M5/T-nut</text>'
    isolation = '<rect class="bbox" x="280" y="240" width="640" height="270"/><rect class="hold" x="240" y="130" width="720" height="90"/><path class="shoe" d="M190 510h820v70H190z"/><text x="360" y="185" font-size="22">lid / gasket / chimney / M4: NO CONTACT</text>'
    battery = '<rect class="bbox" x="300" y="260" width="600" height="320"/><rect x="430" y="330" width="340" height="230" fill="#ffe3e3" stroke="#b23a48" stroke-width="3"/><path class="dim" d="M600 330V100"/><text x="625" y="150" font-size="20">vertical removal with lid removed</text>'
    cbox = '<rect class="cbox" x="180" y="120" width="500" height="150"/><rect class="shoe" x="700" y="400" width="250" height="110"/><path class="hold" d="M680 100v450"/><text x="250" y="320" font-size="20">rear rail foot shifted to keep 1 mm CAD reference gap</text>'
    crawler = '<rect class="rail" x="480" y="120" width="240" height="90"/><path class="shoe" d="M480 120h240v80H650v350H500z"/><rect class="hold" x="760" y="360" width="300" height="210"/><text x="770" y="335" font-size="20">crawler static envelope · dynamic pending</text>'
    return {
        "previews/cradle_top_view.svg": _svg("Four independent lower shoes — local fit top view", top, ["Support centers X=+60/-60; effective lateral support spacing66 mm.", "BBOX global XY registration remains physical pending."]),
        "previews/cradle_side_section.svg": _svg("Rail-to-lower-body side section", side, ["Direct body-bottom Z148 gives107 mm drop from left rail top255.", "V004 upper Z conflict is preserved; full print remains coupon-gated."]),
        "previews/cradle_front_section.svg": _svg("Independent left/right front section", front, ["No rigid cross-rail bridge; right1 mm difference uses optional shim study.", "Lower body only; lid/seal are never structural."]),
        "previews/single_shoe_detail.svg": _svg("Single shoe detail", detail, ["10 mm ledge,12 mm lip, C05 primary clearance.", "R3-class triangular root relief stays outside clearance datum."]),
        "previews/c03_c05_c08_comparison.svg": _svg("Fit-clearance candidates", variants, ["Actual STEP clearances0.3/0.5/0.8 mm.", "Print/test C03 → C05 → C08; do not print four sets."]),
        "previews/m5_tslot_mount.svg": _svg("Proven top-T-slot M5 interface", m5, ["One M5/T-nut per independent shoe; four total.", "Rail profile detail beyond direct slot measures remains partial."]),
        "previews/bbox_load_path.svg": _svg("Intended dry-fit load path", load, ["TPU is optional/non-structural; load capacity is not inferred from area.", "No lid, gasket or lid-M4 load path."]),
        "previews/lid_isolation.svg": _svg("Waterproof-system isolation", isolation, ["BBOX modification count0; lid service remains vertical.", "Full V004 slow-ingress failure is a separate waterproof gate."]),
        "previews/battery_removal_path.svg": _svg("Battery service path", battery, ["Known payload1.2 kg; full assembly mass pending.", "Cradle remains below body and outside internal removal sweep."]),
        "previews/cbox_interference_check.svg": _svg("CBOX V002 local reference", cbox, ["Cradle/CBOX saddle and removal-path intersections are zero.", "Global BBOX/CBOX registration is not promoted."]),
        "previews/crawler_clearance.svg": _svg("Crawler static clearance", crawler, ["Cradle stays inboard of the protected static crawler envelope.", "Powered/dynamic crawler clearance remains PHYSICAL_PENDING."]),
    }


def source_audit() -> dict:
    state = audit()
    return {
        "bbox": bbox_body_audit(),
        "battery": {"plan_mm": [150.9, 65.5], "body_height_mm": 92.5,
                    "terminal_inclusive_height_mm": 99.4, "mass_kg": 1.2,
                    "known_internal_payload_mass": "1.2_KG", "full_assembly_mass": "PHYSICAL_PENDING"},
        "cbox_v002_interface": {
            "source": CBOX_V2_REL + "/artifacts/cbox_top_tslot_mount_coupon_v002.step",
            "physical_result": "PHYSICAL_FIT_PASS_USER_REPORTED_THIS_TASK",
            "reused": "EXACT_BREP_SUBSET", "redesign": "NONE",
        },
        "rail": {"outside_span_mm": [208, 210], "inside_span_mm": [168, 170],
                 "center_spacing_mm": [188, 190], "local_center_reference_mm": 189,
                 "top_face_width_mm": 20, "top_face_width_class": "PHYSICAL_DERIVED",
                 "left_top_z_mm": 255, "right_top_z_mm": 254,
                 "slot_entrance_mm": 6.4, "slot_internal_max_mm": 10.8,
                 "slot_depth_mm": 6.4, "lip_profile": "PHYSICAL_PARTIAL"},
        "registration": {
            "bbox_xy": BBOX_XY_CLASS, "bbox_body_bottom_z_mm": 148,
            "body_bottom_z_class": "DIRECT_PHYSICAL_POINT_FEATURE_IDENTITY_PARTIAL",
            "v004_exact_top_vs_physical_z254": "UNRESOLVED_SPECIMEN_OR_FEATURE_CONFLICT",
            "local_fit_only": True,
        },
        "protected": state["protected"],
        "protected_source_changed_count": state["protected_source_changed_count"],
    }


def documents() -> dict[str, str]:
    readme = f"""# BBOX 4-Point Lower Cradle V001

{STATUS}

This isolated lane mounts the current BBOX lower body with four independent PETG
shoes.  It never uses the lid, gasket, chimney, gland or lid M4 ears as vehicle
structure.  Each shoe reuses the exact physically passing CBOX V002 rail-foot/
vertical-M5 interface and adds one open hanger, a10 mm lower ledge and12 mm body
lip.  C05 is provisional; C03/C05/C08 are physical fit coupons.

FIRST PRINT: `artifacts/bbox_lower_cradle_fit_coupon_c03.stl`, then C05 and C08
only if needed.  Bambu A1, PETG, broad outside XZ face down, support OFF.  The
full four shoes are CAD-ready but DO NOT PRINT until rail mount, BBOX lower-body
fit and zero lid/gasket contact pass physically.

The actual V004 lower core is162×76 mm at Z0 with a flat square-corner bottom;
the180×96 mm upper M4-tower envelope is separate.  Direct body-bottom Z148 gives
a107 mm left-rail drop for this local fit study.  Global X/Y and the conflicting
V004 top registration remain HOLD.  Optional1 mm right support shim illustrates,
but does not mandate, correction of the measured rail-height difference.

`COMMIT_PATHS.txt` is only an inventory.  Nothing is staged or committed.
"""
    design = """# BBOX 4-point lower cradle design

Four parts: FRONT_LEFT, FRONT_RIGHT, REAR_LEFT and REAR_RIGHT.  Each has one
40 mm proven top-T-slot foot, one M5, an open inboard hanger, a broad lower arm,
a30×10 mm body contact patch,12 mm locating lip and outside-datum R3-class
printable triangular root relief.  There is no plate or bridge between rails.

Local reference centers: body support X=+60/-60 mm, rail mounts X=+60/-14 mm.
The rear diagonal arm keeps the rail foot1 mm beyond the current CBOX V002 body
X envelope while retaining rear body support at X=-60.  Support center spacing
is120 mm longitudinal and66 mm lateral.  These are local-fit coordinates, not a
promotion of global vehicle X/Y authority.

The underside, hanger and through M5 pocket are open and washable.  TPU and
leveling shims are removable, non-structural test components.
"""
    philosophy = """# BBOX mechanical mount philosophy

BBOX_WATERPROOF_SYSTEM = lid/gasket/chimney/gland.
BBOX_VEHICLE_MOUNT_SYSTEM = independent lower cradle.

Load path candidate: BBOX body → PETG ledges → open hangers → upper rails →
metal M5/T-nuts → frame.  BBOX lid structural mount = FALSE; lid M4 frame use =
FALSE; BBOX modifications/new holes =0.  Contact area is geometry evidence only,
not load capacity.  Uplift, rollover, shock, vibration and loaded driving remain
physical gates.
"""
    body_audit = """# BBOX body interface audit

Actual V004 body STEP bounds are180×96×114.395 mm.  A0.2 mm bottom slice and the
bottom planar face both prove the lower core footprint162×76 mm.  Bottom Z=0,
wall/floor3.5 mm, lower corner radius0, taper NONE and chamfer NONE.  Upper-only
M4 towers expand the envelope to180×96 mm at eight centers; they are not the
lower footprint and are not cradle contacts.

Small G065 dummy WATER PASS remains separate.  Latest user result says the full
V004 60-minute test failed with unresolved slow ingress.  Body geometry remains
valid for this dry mechanical fit study; waterproof authority is not promoted.
"""
    reuse = """# CBOX V002 top-T-slot reuse

The user now reports the CBOX V002 coupon fits the actual rail, M5/T-nut works,
and its short and outer L-shaped regions fit.  V001's side-hole failure is not
reintroduced.  Each cradle shoe uses the exact BRep subset of the V002 coupon:
40×20 rail contact,5.8×8.8 through slot and12×15×4.5 service pocket.  Generated
STEP comparison requires symmetric-difference volume0.  One M5 per shoe, four
total.  Slot direct authority remains6.4/10.8/6.4 mm; detailed lip profile is
partial.
"""
    matrix = """# Cradle clearance variant matrix

| ID | requested/actual clearance | role |
|---|---:|---|
| C03 | 0.300000 mm | first/tightest physical test |
| C05 | 0.500000 mm | primary provisional full-shoe CAD |
| C08 | 0.800000 mm | loose fallback |

All coupons use the same rail/M5 interface,10 mm ledge,12 mm lip and optional
1 mm TPU pad geometry.  Select the tightest hand-inserting candidate without
scrape, forced PETG/body stress or unacceptable play.
"""
    coupon_plan = """# BBOX lower cradle coupon test

FIRST PRINT C03; test C05 then C08 only if required. PETG/Bambu A1, broad outside
XZ face down, support OFF.

Candidate: C03 / C05 / C08
Rail mounting: PASS / FAIL
M5/T-nut: PASS / FAIL
Coupon sits flat: PASS / SMALL ROCK / FAIL
Actual BBOX inserts: PASS / TIGHT / LOOSE / FAIL
Bottom fully supported: YES / NO
Side play: NONE / SMALL / LARGE
Vertical lip: NORMAL / TOO_TIGHT / NONE
Lid contact: NONE / YES
Lid M4 ear contact: NONE / YES
TPU pad: PASS / TOO_THICK / TOO_THIN / NOT_TESTED
BBOX removal: PASS / FAIL
PETG: NONE / WHITENING / CRACK
Selected clearance: 0.3 / 0.5 / 0.8 / NONE
FINAL: CRADLE_SHOE_COUPON_PHYSICAL_PASS / ADJUST / FAIL

Stop before full shoes unless rail mount, lower-body fit and zero lid/gasket
contact all PASS.
"""
    full_plan = """# Full cradle physical test plan

Only after coupon PASS: print four PETG shoes; install one M5/T-nut each; verify
FL/FR/RL/RR; all four supports; rocking/lateral motion; lid and battery removal;
all eight lid-M4 tool paths; CBOX/chimney/crawler static clearance; optional TPU
pads and0.5/1.0 shims.  Test empty BBOX, real BBOX, dry1.2 kg battery static,
then gentle manual shake. Stop on whitening, crack, rock, contact or fastener
bottoming. Uplift/rollover and load capacity are NOT QUALIFIED. Low-speed dry,
vibration, water/mud and field work require later authority.
"""
    battery = """# Battery service audit

Known battery authority:150.9×65.5 mm plan,92.5 mm body,99.4 mm terminal-inclusive,
1.2 kg. Full loaded BBOX mass is PHYSICAL_PENDING. The cradle remains below and
outside the protected internal battery/removal envelope. CAD intersection with
the vertical removal sweep is0; lid must be removed and internal restraint
released. CAD service PASS is not a physical loaded-removal PASS.
"""
    retention = """# Future uplift retention plan

The lower cradle provides support and candidate lateral location only. It does
not qualify upward/rollover retention. A non-printing STEP reserves front/rear
lower-body clip regions, separate from lid/gasket/M4. Future removable clips must
be non-destructive, body-only and serviceable. No strap over the lid and no final
clip are released here.

LATERAL_LOCATION = DESIGN_CANDIDATE
VERTICAL_UPLIFT_RETENTION = FUTURE_CLIP_REQUIRED
ROLLOVER_RETENTION = PENDING
"""
    holds = """# Global integration holds

HOLD: full four-shoe print until coupon physical PASS; global BBOX X/Y; exact
V004-to-as-built specimen identity; conflicting top Z254 feature; full assembly
mass; M5 stack/bottoming recheck; optional TPU hardness; shim need; final CBOX/
BBOX installed transforms; future clutch corridor; retention clip; static1.2 kg
test; shock, tilt, vibration, powered crawler, water/mud and field operation.

The local CAD has zero cradle intersections with body, lid, gasket, chimney,
M4 ears/tool paths, CBOX saddle/removal path and static crawler reference. These
do not close unresolved global registration, dynamic or load gates.
"""
    return {name: text.rstrip() + "\n" for name, text in zip(
        DOCS, [readme, design, philosophy, body_audit, reuse, matrix, coupon_plan,
               full_plan, battery, retention, holds])}


def physical_template() -> dict:
    return {
        "coupon": {"candidate": "C03/C05/C08", "rail_mounting": "PASS/FAIL",
                   "m5_tnut": "PASS/FAIL", "sits_flat": "PASS/SMALL_ROCK/FAIL",
                   "bbox_inserts": "PASS/TIGHT/LOOSE/FAIL", "bottom_supported": "YES/NO",
                   "side_play": "NONE/SMALL/LARGE", "vertical_lip": "NORMAL/TOO_TIGHT/NONE",
                   "lid_contact": "NONE/YES", "lid_m4_ear_contact": "NONE/YES",
                   "tpu_pad": "PASS/TOO_THICK/TOO_THIN/NOT_TESTED",
                   "bbox_removal": "PASS/FAIL", "petg": "NONE/WHITENING/CRACK",
                   "selected_clearance_mm": "0.3/0.5/0.8/NONE",
                   "final": "CRADLE_SHOE_COUPON_PHYSICAL_PASS/ADJUST/FAIL"},
        "full_after_coupon_pass": {
            "front_left": "PASS/FAIL", "front_right": "PASS/FAIL",
            "rear_left": "PASS/FAIL", "rear_right": "PASS/FAIL",
            "all_four_m5": "PASS/FAIL", "rests_on_all_four": "YES/NO",
            "rocking": "NONE/SMALL/FAIL", "lateral_movement": "NONE/SMALL/LARGE",
            "lid_removable": "YES/NO", "battery_vertical_removal": "YES/NO",
            "lid_m4_access": "PASS/FAIL", "cbox_interference": "NONE/YES",
            "chimney_interference": "NONE/YES", "crawler_static": "NONE/YES",
            "tpu_pads": "PASS/FAIL", "empty_bbox_static": "PASS/FAIL",
            "battery_1p2kg_static": "PASS/FAIL", "manual_light_shake": "PASS/FAIL",
            "petg": "NONE/WHITENING/CRACK", "uplift_rollover": "NOT_QUALIFIED"},
    }


def design_parameters() -> dict:
    return {
        "version": "BBOX_4POINT_LOWER_CRADLE_V001", "status": STATUS,
        "architecture": {"shoe_count": 4, "m5_per_shoe": 1, "total_m5": 4,
                         "independent_shoes": True, "fixed_left_right_bridge": False,
                         "bbox_lid_is_structural_mount": False,
                         "bbox_lid_m4_used_for_frame_mount": False,
                         "bbox_modification_count": 0, "new_bbox_holes": 0},
        "bbox": bbox_body_audit(), "source": source_audit(),
        "shoe": {"selected_clearance_mm": SELECTED_CLEARANCE,
                 "support_ledge_depth_mm": LEDGE_DEPTH, "support_x_mm": SUPPORT_X,
                 "vertical_lip_height_mm": LIP_HEIGHT, "lip_thickness_mm": LIP_THICKNESS,
                 "root_relief_mm": ROOT_RELIEF, "material": "PETG",
                 "contact_area_per_shoe_mm2": SUPPORT_X * LEDGE_DEPTH,
                 "total_contact_area_mm2": 4 * SUPPORT_X * LEDGE_DEPTH,
                 "full_print": "HOLD_UNTIL_COUPON_PHYSICAL_PASS"},
        "placement": {"class": BBOX_XY_CLASS, "body_bottom_global_z_mm": 148,
                      "left_rail_to_body_bottom_drop_mm": 107,
                      "front_support_x_mm": FRONT_SUPPORT_X,
                      "rear_support_x_mm": REAR_SUPPORT_X,
                      "front_rear_support_spacing_mm": 120,
                      "effective_left_right_support_spacing_mm": 66,
                      "rear_rail_mount_x_mm": REAR_MOUNT_X,
                      "rear_cbox_reference_gap_mm": 1.0},
        "clearance_candidates_mm": CLEARANCES,
        "tpu": {"thickness_mm": TPU_PAD_T, "structural": False,
                "material": "CURRENT_PRINTABLE_TPU_SPECIMEN",
                "shore_hardness": "PHYSICAL_PENDING"},
        "leveling": {"rail_difference_mm": 1.0, "mandatory": False,
                     "optional_shims_mm": [0.5, 1.0]},
        "intersections": intersection_data(),
        "print": {"printer": "BAMBU_A1", "shoe_material": "PETG",
                  "orientation": "BROAD_OUTSIDE_XZ_FACE_DOWN",
                  "support": "OFF_CANDIDATE", "slicer": "HOLD_SLICER_NOT_RUN",
                  "first_print": "artifacts/bbox_lower_cradle_fit_coupon_c03.stl"},
        "retention": {"lateral_location": "DESIGN_CANDIDATE",
                      "vertical_uplift": "FUTURE_CLIP_REQUIRED",
                      "rollover": "PENDING"},
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
    with tempfile.TemporaryDirectory(prefix="bbox_4point_cradle_repro_") as folder:
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
    quality = inspect(LANE); intersections = intersection_data(); reproduction = reproduce()
    if any(intersections[key] > TOL for key in [
        "cradle_to_bbox_body_mm3", "cradle_to_bbox_lid_mm3", "cradle_to_gasket_mm3",
        "cradle_to_chimney_mm3", "cradle_to_lid_m4_ears_mm3",
        "cradle_to_cbox_saddle_mm3", "cradle_to_crawler_static_mm3",
        "bbox_lid_m4_tool_path_mm3", "battery_vertical_removal_to_cradle_mm3"]):
        raise AssertionError("intersection contract " + json.dumps(intersections))
    if not all(v <= TOL for key in ["bbox_lid_removal_sweep_mm3", "bbox_body_removal_sweep_mm3",
                                     "cbox_removal_sweep_mm3"] for v in intersections[key]):
        raise AssertionError("service sweep contract " + json.dumps(intersections))
    for name, text in documents().items():
        (LANE / name).write_text(text, encoding="utf-8", newline="\n")
    write_json(LANE / "source_authority_audit.json", source_audit())
    write_json(LANE / "bbox_body_geometry_audit.json", bbox_body_audit())
    write_json(LANE / "intersection_report.json", intersections)
    write_json(LANE / "physical_result_template.json", physical_template())
    write_json(LANE / "design_parameters.json", design_parameters())
    write_json(LANE / "validation_report.json", {
        "status": "GENERATED_CONTRACT_PENDING", "quality": quality,
        "intersections": intersections, "bbox_body": bbox_body_audit(),
        "regression": regression(), "cad_reproducibility": reproduction,
        "documentation_reproducibility": "PENDING_CONTRACT",
    })
    print(json.dumps({"build": "GENERATED_CONTRACT_PENDING", "STEP": len(STEPS),
                      "STL": len(STLS), "SVG": len(SVGS), "exact_paths": len(EXPECTED),
                      "actual": quality["actual_geometry"], "intersections": intersections,
                      "reproducibility": reproduction}, indent=2))


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
        "first_print": "artifacts/bbox_lower_cradle_fit_coupon_c03.stl",
        "full_cradle_print": "HOLD_UNTIL_COUPON_PHYSICAL_PASS",
        "printable_stl": STLS, "future_retention_step": "REFERENCE_ONLY_NOT_PRINT_RELEASED",
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
    quality = inspect(LANE); reproduction = reproduce(); intersections = intersection_data()
    print(json.dumps({"verify": "PASS", "audit": state,
                      "quality_count": {"step": len(quality["step"]), "stl": len(quality["stl"])},
                      "actual": quality["actual_geometry"], "intersections": intersections,
                      "cad_reproducibility": reproduction,
                      "documentation_reproducibility": len(DOCS)}, indent=2))


def handoff() -> None:
    verify()
    target = Path(r"D:\Downloads") / (
        "Paddy_Swarm_BBOX_4POINT_LOWER_CRADLE_V001_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip")
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
