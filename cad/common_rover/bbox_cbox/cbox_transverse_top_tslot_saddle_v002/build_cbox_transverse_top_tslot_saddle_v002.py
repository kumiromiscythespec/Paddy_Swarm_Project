"""CBOX transverse independent saddles with a coupon-gated top T-slot interface.

V001 CBOX support geometry is retained where possible.  Its failed side-hole
rail interface is superseded by two vertical M5 adjustment slots per saddle.
Complete rail-lip and hardware geometry remain physical-test inputs, not CAD
authority.  Full-saddle printing is therefore held until the short coupon passes.
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
REL = "cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002"
PARENT_REL = "cad/common_rover/bbox_cbox/cbox_transverse_cross_saddle_bbox_alignment_v001"
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
TOL = 1.0e-6
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/TOP_T_SLOT_MOUNT_COUPON_PRINT_READY/"
    "FULL_LEFT_RIGHT_SADDLE_CAD_READY/FULL_SADDLE_PRINT_HOLD_UNTIL_COUPON_PASS/"
    "PHYSICAL_FIT_PENDING/LOAD_CAPACITY_PENDING"
)

# Current physical frame evidence.  These dimensions produce a 20 x20 local
# rail envelope; the historical/project label "2040" is not used to override it.
RAIL_OUTSIDE_RANGE = [208.0, 210.0]
RAIL_INSIDE_RANGE = [168.0, 170.0]
RAIL_CENTER_RANGE = [188.0, 190.0]
RAIL_CENTER_NOMINAL = 189.0
RAIL_TOP_FACE_WIDTH = 20.0
RAIL_HEIGHT = 20.0
LEFT_RAIL_TOP = 255.0
RIGHT_RAIL_TOP = 254.0
CRAWLER_LEFT_TOP = 181.0
CRAWLER_RIGHT_TOP = 180.0
BBOX_LID_TOP = 254.0

SLOT_ENTRANCE = 6.4
SLOT_INTERNAL = 10.8
SLOT_DEPTH = 6.4
TOP_SLOT_COUNT = 1
TOP_SLOT_CENTER_LOCAL_Y = 0.0
TOP_SLOT_CENTER_CLASS = "CAD_REFERENCE_SYMMETRY_PHYSICAL_CONFIRMATION_PENDING"
TRANSVERSE_ADJUSTMENT = 1.5

SADDLE_LENGTH = 140.0
M5_PITCH = 100.0
M5_X = [-50.0, 50.0]
M5_THROUGH = 5.8
M5_HEAD_ENVELOPE_DIAMETER = 10.0
M5_HEAD_ENVELOPE_HEIGHT = 4.0
M5_POCKET_DIAMETER = 12.0
M5_POCKET_DEPTH = 4.5
SELECTED_RISE = 8.0
RAIL_FOOT_TOP = SELECTED_RISE - 0.5
COUPON_LENGTH = 40.0
SELECTED_X_OFFSET = -111.0
CBOX_TILT_DEG = math.degrees(math.atan2(LEFT_RAIL_TOP - RIGHT_RAIL_TOP, RAIL_CENTER_NOMINAL))
CBOX_ASSEMBLY_REFERENCE_SEPARATION = 0.02
BBOX_DRIVER_NOTCH_DIAMETER = 16.0
BBOX_DRIVER_LOCAL_X = -1.0
BBOX_DRIVER_LOCAL_Y = 7.5

# Exact V001 support constants.  The pad/lip footprint is preserved; only two
# local top fastener-service openings remove contact area.
V001_PAD_INBOARD = 1.2
V001_PAD_OUTBOARD = 32.5
V001_LIP_INNER = 29.5
V001_PAD_THICKNESS = 4.0
V001_LIP_HEIGHT = 5.0
V001_RISE = 4.0

PRINT_NAMES = [
    "cbox_top_tslot_saddle_left_v002", "cbox_top_tslot_saddle_right_v002",
    "cbox_top_tslot_mount_coupon_v002", "cbox_saddle_leveling_shim_0p5",
    "cbox_saddle_leveling_shim_1p0",
]
REFERENCE_NAMES = [
    "cbox_top_tslot_v002_assembly", "cbox_reference", "bbox_reference",
    "upper_rail_reference",
]
STEPS = [f"artifacts/{name}.step" for name in PRINT_NAMES + REFERENCE_NAMES]
STLS = [f"artifacts/{name}.stl" for name in PRINT_NAMES]
SVGS = [f"previews/{name}.svg" for name in [
    "v002_left_top", "v002_right_top", "v002_cross_section",
    "top_tslot_mount_detail", "m5_tnut_section", "cbox_support_section",
    "bbox_clearance", "rail_height_difference", "mount_coupon",
    "v001_vs_v002_cross_section",
]]
DOCS = [
    "README.md", "CBOX_TOP_TSLOT_SADDLE_V002_DESIGN.md",
    "V001_PHYSICAL_FIT_FAILURE_RECORD.md", "UPPER_RAIL_PROFILE_AUDIT.md",
    "TOP_TSLOT_M5_INTERFACE.md", "V001_V002_GEOMETRY_DIFF.md",
    "MOUNT_COUPON_TEST_PLAN.md", "FULL_SADDLE_PHYSICAL_TEST_PLAN.md",
    "LEVELING_SHIM_STRATEGY.md", "GLOBAL_INTEGRATION_HOLDS.md",
]
REPORTS = [
    "design_parameters.json", "validation_report.json", "contract_test_report.json",
    "source_authority_audit.json", "geometry_diff_report.json",
    "physical_result_template.json", "repository_audit.json", "manifest.json",
]
EXPECTED = sorted([
    Path(__file__).name, "tests/test_cbox_transverse_top_tslot_saddle_v002.py",
    "audit_start.json", "COMMIT_PATHS.txt", "SHA256SUMS.txt",
    *STEPS, *STLS, *SVGS, *DOCS, *REPORTS,
])


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "--no-optional-locks", *args], cwd=ROOT, stderr=subprocess.PIPE
    ).decode("utf-8").strip()


def tree_hash(path: Path) -> dict:
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    for item in files:
        h.update((item.relative_to(path).as_posix() + "\n").encode())
        h.update(bytes.fromhex(sha(item)))
    return {"files": len(files), "sha256": h.hexdigest()}


def audit() -> dict:
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
    state["pass"] = bool(ok)
    if not ok:
        raise AssertionError("FAIL_CLOSED " + json.dumps(state, sort_keys=True))
    return state


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder_z(diameter: float, height: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    x, y, z = center
    return cq.Workplane("XY").circle(diameter / 2).extrude(height).translate((x, y, z - height / 2))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))


def volume(shape: cq.Workplane) -> float:
    return sum(s.Volume() for s in shape.solids().vals())


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def distance(a: cq.Workplane, b: cq.Workplane) -> float:
    operation = BRepExtrema_DistShapeShape(a.val().wrapped, b.val().wrapped)
    operation.Perform()
    if not operation.IsDone():
        raise AssertionError("distance calculation failed")
    return operation.Value()


def bounds(shape: cq.Workplane) -> list[float]:
    b = shape.val().BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


def size(shape: cq.Workplane) -> list[float]:
    b = bounds(shape)
    return [b[i + 3] - b[i] for i in range(3)]


def slot_z(diameter: float, travel: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return (cylinder_z(diameter, height, (x, y - travel / 2, z))
            .union(cylinder_z(diameter, height, (x, y + travel / 2, z)))
            .union(box(diameter, travel, height, (x, y, z))).clean())


def v001_support(length: float = SADDLE_LENGTH) -> cq.Workplane:
    width = V001_PAD_OUTBOARD - V001_PAD_INBOARD
    pad = box(length, width, V001_PAD_THICKNESS,
              (0, (V001_PAD_INBOARD + V001_PAD_OUTBOARD) / 2, V001_RISE / 2))
    lip = box(length, V001_PAD_OUTBOARD - V001_LIP_INNER, V001_LIP_HEIGHT,
              (0, (V001_LIP_INNER + V001_PAD_OUTBOARD) / 2,
               V001_RISE + V001_LIP_HEIGHT / 2))
    return pad.union(lip).clean()


def _saddle(side: str, length: float, hole_x: list[float],
            bbox_service_notch: bool) -> cq.Workplane:
    side = side.upper()
    holes = M5_X if hole_x is None else hole_x
    dz = SELECTED_RISE - V001_RISE
    preserved = v001_support(length)
    if side == "RIGHT":
        preserved = preserved.mirror("XZ")
    # The rigid CBOX follows the measured 1 mm /189 mm rail plane.  Matching
    # this very small slope avoids the 0.151 mm solid overlap in V001 while the
    # separate rail-contact foot remains flat on each local rail.
    preserved = (preserved.translate((0, 0, -V001_RISE))
                 .rotate((0, 0, 0), (1, 0, 0), CBOX_TILT_DEG)
                 .translate((0, 0, SELECTED_RISE)))
    foot = box(length, RAIL_TOP_FACE_WIDTH, RAIL_FOOT_TOP,
               (0, 0, RAIL_FOOT_TOP / 2))
    result = preserved.union(foot).clean()
    for x in holes:
        through = slot_z(M5_THROUGH, 2 * TRANSVERSE_ADJUSTMENT,
                         SELECTED_RISE + 2, x, TOP_SLOT_CENTER_LOCAL_Y,
                         SELECTED_RISE / 2)
        pocket = slot_z(M5_POCKET_DIAMETER, 2 * TRANSVERSE_ADJUSTMENT,
                        M5_POCKET_DEPTH + 1, x, TOP_SLOT_CENTER_LOCAL_Y,
                        SELECTED_RISE - M5_POCKET_DEPTH / 2 + 0.5)
        result = result.cut(through).cut(pocket)
    if bbox_service_notch:
        # Open edge notch for the retained V001 BBOX inner M4 driver path.
        # The 16 mm notch gives 1 mm radial margin around the 14 mm tool proxy.
        local_y = -BBOX_DRIVER_LOCAL_Y if side == "LEFT" else BBOX_DRIVER_LOCAL_Y
        result = result.cut(cylinder_z(BBOX_DRIVER_NOTCH_DIAMETER, 30.0,
                                       (BBOX_DRIVER_LOCAL_X, local_y, 10.0)))
    return result.clean()


def left_saddle(length: float = SADDLE_LENGTH, hole_x: list[float] | None = None,
                bbox_service_notch: bool = True) -> cq.Workplane:
    return _saddle("LEFT", length, M5_X if hole_x is None else hole_x,
                   bbox_service_notch)


def saddle(side: str) -> cq.Workplane:
    return _saddle(side, SADDLE_LENGTH, M5_X, True)


def mount_coupon() -> cq.Workplane:
    return _saddle("LEFT", COUPON_LENGTH, [0.0], False)


def leveling_shim(thickness: float) -> cq.Workplane:
    result = box(SADDLE_LENGTH, RAIL_TOP_FACE_WIDTH, thickness, (0, 0, thickness / 2))
    for x in M5_X:
        result = result.cut(slot_z(M5_THROUGH, 2 * TRANSVERSE_ADJUSTMENT,
                                   thickness + 2, x, 0, thickness / 2))
    return result.clean()


def rail_single(length: float = 400.0) -> cq.Workplane:
    rail = box(length, RAIL_TOP_FACE_WIDTH, RAIL_HEIGHT, (0, 0, -RAIL_HEIGHT / 2))
    # Only the three measured bounds are represented.  A 1 mm nominal lip-depth
    # split makes the reference visible but is explicitly not physical authority.
    entrance = box(length + 2, SLOT_ENTRANCE, 1.0, (0, 0, -0.5))
    internal = box(length + 2, SLOT_INTERNAL, SLOT_DEPTH - 1.0,
                   (0, 0, -(1.0 + (SLOT_DEPTH - 1.0) / 2)))
    return rail.cut(entrance.union(internal)).clean()


def rails_reference() -> cq.Workplane:
    half = RAIL_CENTER_NOMINAL / 2
    left = rail_single().translate((0, half, LEFT_RAIL_TOP))
    right = rail_single().translate((0, -half, RIGHT_RAIL_TOP))
    return compound([left, right])


@lru_cache(None)
def v001_module():
    source = ROOT / PARENT_REL / "build_cbox_transverse_cross_saddle_bbox_alignment_v001.py"
    spec = importlib.util.spec_from_file_location("read_only_cbox_saddle_v001", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cbox_reference() -> cq.Workplane:
    return v001_module().local_cbox_reference()


def placed_cbox() -> cq.Workplane:
    half = RAIL_CENTER_NOMINAL / 2
    right_support_y = -half
    right_support_z = RIGHT_RAIL_TOP + SELECTED_RISE
    # A 0.02 mm assembly-reference separation prevents coincident BRep faces
    # from being reported as a false thin-volume clash.  It is not a spacer,
    # manufacturing standoff, or change to the nominal Z=8 support datum.
    base_z = (right_support_z
              - right_support_y * math.sin(math.radians(CBOX_TILT_DEG))
              + CBOX_ASSEMBLY_REFERENCE_SEPARATION)
    return cbox_reference().rotate((0, 0, 0), (1, 0, 0), CBOX_TILT_DEG).translate((SELECTED_X_OFFSET, 0, base_z))


def bbox_reference() -> cq.Workplane:
    # V001's registered BBOX-lid/chimney reference remains the comparison datum.
    # Current V004 is protected but still GLOBAL_INTEGRATION_PHYSICAL_PENDING.
    return v001_module().bbox_placed()


def chimney_reference() -> cq.Workplane:
    return v001_module().chimney_keepout()


def crawler_reference() -> cq.Workplane:
    return v001_module().crawler_reference()


def bbox_driver_paths() -> cq.Workplane:
    return v001_module().bbox_driver_paths()


def placed_saddles() -> cq.Workplane:
    half = RAIL_CENTER_NOMINAL / 2
    return compound([
        saddle("LEFT").translate((SELECTED_X_OFFSET, half, LEFT_RAIL_TOP)),
        saddle("RIGHT").translate((SELECTED_X_OFFSET, -half, RIGHT_RAIL_TOP)),
    ])


def assembly() -> cq.Workplane:
    return compound([rails_reference(), placed_saddles(), placed_cbox(),
                     bbox_reference(), chimney_reference()])


def step_models() -> dict[str, cq.Workplane]:
    return {
        "artifacts/cbox_top_tslot_saddle_left_v002.step": saddle("LEFT"),
        "artifacts/cbox_top_tslot_saddle_right_v002.step": saddle("RIGHT"),
        "artifacts/cbox_top_tslot_mount_coupon_v002.step": mount_coupon(),
        "artifacts/cbox_saddle_leveling_shim_0p5.step": leveling_shim(0.5),
        "artifacts/cbox_saddle_leveling_shim_1p0.step": leveling_shim(1.0),
        "artifacts/cbox_top_tslot_v002_assembly.step": assembly(),
        "artifacts/cbox_reference.step": cbox_reference(),
        "artifacts/bbox_reference.step": bbox_reference(),
        "artifacts/upper_rail_reference.step": rails_reference(),
    }


def stl_models() -> dict[str, cq.Workplane]:
    models = step_models()
    return {f"artifacts/{name}.stl": models[f"artifacts/{name}.step"] for name in PRINT_NAMES}


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
    lines = ["solid CBOX_TOP_TSLOT_SADDLE_V002"]
    for tri in tris:
        a, b, c = [vertices[i] for i in tri]
        normal = (b - a).cross(c - a).normalized()
        lines.extend(["  facet normal " + " ".join(f"{v:.12g}" for v in normal.toTuple()),
                      "    outer loop"])
        for point in (a, b, c):
            lines.append("      vertex " + " ".join(f"{v:.9f}" for v in point.toTuple()))
        lines.extend(["    endloop", "  endfacet"])
    lines.append("endsolid CBOX_TOP_TSLOT_SADDLE_V002")
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
            edges[edge] += 1
            winding[edge] += 1 if (first, second) == edge else -1
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
    remaining, components = set(graph), 0
    while remaining:
        components += 1; stack = [next(iter(remaining))]
        while stack:
            point = stack.pop()
            if point not in remaining: continue
            remaining.remove(point); stack.extend(graph[point] & remaining)
    result = {
        "triangles": len(tri_data), "connected_components": components,
        "bad_edges": sum(value != 2 for value in edges.values()),
        "bad_winding_edges": sum(value != 0 for value in winding.values()),
        "bad_vertex_links": bad_links, "degenerate_triangles": degenerate,
        "duplicate_triangles": len(tri_data) - len({tuple(sorted(t)) for t in tri_data}),
    }
    result["watertight"] = result["bad_edges"] == 0
    result["manifold"] = result["watertight"] and result["bad_vertex_links"] == 0
    result["pass"] = not any(result[k] for k in ["bad_edges", "bad_winding_edges",
                                                   "bad_vertex_links", "degenerate_triangles",
                                                   "duplicate_triangles"])
    return result


def contact_area(shape: cq.Workplane, support_z: float, lip_z: float) -> float:
    return sum(face.Area() for face in shape.faces().vals()
               if face.geomType() == "PLANE" and face.normalAt().z > 0.999999
               and (abs(face.Center().z - support_z) < 1e-5
                    or abs(face.Center().z - lip_z) < 1e-5))


def sloped_contact_faces(shape: cq.Workplane) -> list:
    """Return the V001-derived pad/lip top faces after the rail-plane tilt."""
    return [face for face in shape.faces().vals()
            if face.geomType() == "PLANE" and face.normalAt().z > 0.999
            and face.Center().z > 7.7]


def contact_face_metrics(shape: cq.Workplane) -> dict:
    """Measure support faces directly from the generated BRep."""
    faces = sloped_contact_faces(shape)
    pad = [face for face in faces if face.Center().z < 10.0]
    lip = [face for face in faces if face.Center().z >= 10.0]
    if not pad or not lip:
        raise AssertionError("generated CBOX contact faces not found")
    normal = max(pad, key=lambda face: face.Area()).normalAt()

    def z_range(group: list) -> list[float]:
        boxes = [face.BoundingBox() for face in group]
        return [min(bb.zmin for bb in boxes), max(bb.zmax for bb in boxes)]

    return {
        "pad_z_range_mm": z_range(pad),
        "lip_z_range_mm": z_range(lip),
        "contact_area_mm2": sum(face.Area() for face in faces),
        "tilt_deg": math.degrees(math.atan2(-normal.y, normal.z)),
        "normal": [normal.x, normal.y, normal.z],
    }


def void_metrics(shape: cq.Workplane, x: float, z: float, probe_x: float = 20,
                 probe_y: float = 19) -> dict:
    probe = box(probe_x, probe_y, 0.04, (x, 0, z))
    void = probe.cut(shape)
    solids = void.solids().vals()
    if not solids:
        raise AssertionError("void probe missed")
    # The only void inside the probe is the M5 slot/pocket.
    bb = void.val().BoundingBox()
    return {"x_width_mm": bb.xlen, "y_width_mm": bb.ylen,
            "center_x_mm": bb.center.x, "center_y_mm": bb.center.y}


def actual_geometry(out: Path) -> dict:
    left = cq.importers.importStep(str(out / "artifacts/cbox_top_tslot_saddle_left_v002.step"))
    right = cq.importers.importStep(str(out / "artifacts/cbox_top_tslot_saddle_right_v002.step"))
    coupon = cq.importers.importStep(str(out / "artifacts/cbox_top_tslot_mount_coupon_v002.step"))
    shim05 = cq.importers.importStep(str(out / "artifacts/cbox_saddle_leveling_shim_0p5.step"))
    shim10 = cq.importers.importStep(str(out / "artifacts/cbox_saddle_leveling_shim_1p0.step"))
    contact = left.intersect(box(SADDLE_LENGTH + 2, 100, 0.04, (0, 0, 0.02)))
    through_left = void_metrics(left, -50, 1.0)
    through_right = void_metrics(left, 50, 1.0)
    pocket_left = void_metrics(left, -50, 5.0)
    pocket_right = void_metrics(left, 50, 5.0)
    full_local = left.intersect(box(COUPON_LENGTH, 100, 20, (50, 0, 6.5))).translate((-50, 0, 0))
    coupon_diff = volume(full_local.cut(coupon)) + volume(coupon.cut(full_local))
    left_contact = contact_face_metrics(left)
    right_contact = contact_face_metrics(right)
    return {
        "left_bounds_mm": size(left), "right_bounds_mm": size(right),
        "coupon_bounds_mm": size(coupon), "left_length_mm": size(left)[0],
        "right_length_mm": size(right)[0], "rail_contact_width_mm": size(contact)[1],
        "cbox_support_plane_z_mm": SELECTED_RISE,
        "cbox_support_plane_z_class": "NOMINAL_AT_LOCAL_RAIL_CENTER",
        "cbox_support_tilt_requested_deg": CBOX_TILT_DEG,
        "left_cbox_contact_actual": left_contact,
        "right_cbox_contact_actual": right_contact,
        "m5_through_left": through_left, "m5_through_right": through_right,
        "m5_pocket_left": pocket_left, "m5_pocket_right": pocket_right,
        "m5_pitch_mm": through_right["center_x_mm"] - through_left["center_x_mm"],
        "coupon_full_interface_symmetric_difference_mm3": coupon_diff,
        "shim_0p5_actual_thickness_mm": size(shim05)[2],
        "shim_1p0_actual_thickness_mm": size(shim10)[2],
        "side_m5_hole_count": 0, "top_vertical_m5_per_saddle": 2,
        "fixed_left_right_bridge": False,
    }


def geometry_diff() -> dict:
    parent = cq.importers.importStep(str(ROOT / PARENT_REL / "cad/cbox_saddle_left.step"))
    current = saddle("LEFT")
    # V001 CAD STEP is stored in its print transform (+10 mm Z), so its
    # physical support/lip planes appear at Z14/Z19 in that artifact.
    old_area = contact_area(parent, 14.0, 19.0)
    new_area = contact_face_metrics(current)["contact_area_mm2"]
    old_rail = parent.intersect(box(SADDLE_LENGTH + 2, 100, 20, (0, 0, -5)))
    new_rail = current.intersect(box(SADDLE_LENGTH + 2, 100, 16, (0, 0, 4)))
    return {
        "v001_source": PARENT_REL + "/cad/cbox_saddle_left.step",
        "v001_bounds_mm": size(parent), "v002_bounds_mm": size(current),
        "bounds_delta_mm": [b - a for a, b in zip(size(parent), size(current))],
        "cbox_support_interface_diff": "MINIMAL_LOCAL_M5_SERVICE_OPENINGS_BBOX_DRIVER_NOTCH_PLUS_4MM_NOMINAL_RISE_AND_0P303DEG_TILT",
        "cbox_support_outer_xy_and_lip_profile": "PRESERVED_EXCEPT_OPEN_EDGE_BBOX_DRIVER_NOTCH",
        "cbox_support_tilt_deg": CBOX_TILT_DEG,
        "bbox_driver_notch_diameter_mm": BBOX_DRIVER_NOTCH_DIAMETER,
        "v001_contact_area_mm2": old_area, "v002_contact_area_mm2": new_area,
        "contact_area_change_mm2": new_area - old_area,
        "contact_area_retained_percent": 100 * new_area / old_area,
        "rail_interface_diff": "INTENTIONAL_SIDE_FLANGE_REMOVED_TOP_FOOT_ADDED",
        "rail_interface_v001_local_volume_mm3": volume(old_rail),
        "rail_interface_v002_local_volume_mm3": volume(new_rail),
        "fastener_interface_diff": "INTENTIONAL_SIDE_M5_X2_TO_TOP_VERTICAL_M5_X2",
        "side_m5_v001_per_saddle": 2, "side_m5_v002_per_saddle": 0,
        "top_m5_v001_per_saddle": 0, "top_m5_v002_per_saddle": 2,
    }


def clearance_data() -> dict:
    saddles = placed_saddles(); cbox = placed_cbox(); bbox = bbox_reference()
    chimney = chimney_reference(); crawler = crawler_reference()
    removal = [common_volume(cbox.translate((0, 0, dz)),
                             compound([saddles, bbox, chimney])) for dz in (0, 20, 40, 60, 80)]
    driver = bbox_driver_paths()
    cbox_low = bounds(cbox)[2]
    return {
        "cbox_to_bbox_intersection_mm3": common_volume(cbox, bbox),
        "saddle_to_bbox_intersection_mm3": common_volume(saddles, bbox),
        "saddle_to_chimney_intersection_mm3": common_volume(saddles, chimney),
        "cbox_to_chimney_intersection_mm3": common_volume(cbox, chimney),
        "saddle_to_crawler_intersection_mm3": common_volume(saddles, crawler),
        "cbox_removal_sweep_intersections_mm3": removal,
        "cbox_removal_path": "PASS_VERTICAL_REFERENCE_AFTER_RETENTION_RELEASE",
        "bbox_lid_m4_access_after_cbox_removal": "PASS_REFERENCE",
        "bbox_driver_path_saddle_intersection_mm3": common_volume(driver, saddles),
        "cbox_assembly_reference_separation_mm": CBOX_ASSEMBLY_REFERENCE_SEPARATION,
        "cbox_assembly_reference_separation_class": "NUMERICAL_BREP_CONTACT_DISAMBIGUATION_NOT_PHYSICAL_SPACER",
        "bbox_minimum_vertical_clearance_mm": cbox_low - BBOX_LID_TOP,
        "cbox_lowest_bottom_z_mm": cbox_low,
        "v001_bbox_clearance_mm": 3.849,
        "clearance_increase_vs_v001_mm": cbox_low - BBOX_LID_TOP - 3.849,
        "left_local_saddle_to_crawler_static_clearance_mm": LEFT_RAIL_TOP - CRAWLER_LEFT_TOP,
        "right_local_saddle_to_crawler_static_clearance_mm": RIGHT_RAIL_TOP - CRAWLER_RIGHT_TOP,
        "crawler_dynamic_clearance": "PHYSICAL_PENDING",
        "chimney_service_access": "PASS_STATIC_REFERENCE_ACTUAL_TOOL_PENDING",
        "bbox_modification_count": 0, "bbox_lid_load_bearing": False,
        "m5_head_direct_cbox_load": False,
        "global_front_interface_gate": "REFERENCE_ONLY_UNRESOLVED_TRANSFORM",
    }


def rise_study() -> list[dict]:
    rows = []
    for rise in (4.0, 6.0, 8.0):
        base_below_pocket = rise - M5_POCKET_DEPTH
        if base_below_pocket < 2.5:
            result = "FAIL_OR_MARGINAL_PETG_SEAT"
        else:
            result = "SELECTED_MINIMUM_PRACTICAL_CANDIDATE"
        rows.append({
            "rise_mm": rise, "pocket_depth_mm": M5_POCKET_DEPTH,
            "remaining_petg_below_pocket_mm": base_below_pocket,
            "nominal_head_top_clearance_to_cbox_mm": rise - M5_HEAD_ENVELOPE_HEIGHT - base_below_pocket,
            "status": result if rise == SELECTED_RISE or result.startswith("FAIL") else "NOT_SELECTED",
        })
    return rows


def inspect(out: Path) -> dict:
    step_report, stl_report = {}, {}
    for path in STEPS:
        shape = cq.importers.importStep(str(out / path))
        entry = {"reload": "PASS" if shape.val().isValid() else "FAIL",
                 "solids": len(shape.solids().vals()), "bounds_mm": size(shape)}
        if entry["reload"] != "PASS": raise AssertionError("STEP invalid " + path)
        if Path(path).stem in PRINT_NAMES:
            check = BOPAlgo_ArgumentAnalyzer(); check.SetShape1(shape.val().wrapped)
            check.SelfInterMode = True; check.Perform()
            entry["self_intersections"] = int(check.HasFaulty())
            if entry["self_intersections"]: raise AssertionError("self intersection " + path)
        step_report[path] = entry
    for path in STLS:
        quality = stl_quality(out / path)
        if not quality["pass"]: raise AssertionError("STL invalid " + path)
        stl_report[path] = quality
    actual = actual_geometry(out)
    checks = {
        "left_length": abs(actual["left_length_mm"] - SADDLE_LENGTH) <= TOL,
        "right_length": abs(actual["right_length_mm"] - SADDLE_LENGTH) <= TOL,
        "rail_contact_width": abs(actual["rail_contact_width_mm"] - RAIL_TOP_FACE_WIDTH) <= TOL,
        "support_height": abs(actual["cbox_support_plane_z_mm"] - SELECTED_RISE) <= TOL,
        "m5_pitch": abs(actual["m5_pitch_mm"] - M5_PITCH) <= TOL,
        "through_x": all(abs(actual[key]["x_width_mm"] - M5_THROUGH) <= TOL
                         for key in ("m5_through_left", "m5_through_right")),
        "through_y": all(abs(actual[key]["y_width_mm"] - (M5_THROUGH + 2 * TRANSVERSE_ADJUSTMENT)) <= TOL
                         for key in ("m5_through_left", "m5_through_right")),
        "pocket_x": all(abs(actual[key]["x_width_mm"] - M5_POCKET_DIAMETER) <= TOL
                        for key in ("m5_pocket_left", "m5_pocket_right")),
        "pocket_y": all(abs(actual[key]["y_width_mm"] - (M5_POCKET_DIAMETER + 2 * TRANSVERSE_ADJUSTMENT)) <= TOL
                        for key in ("m5_pocket_left", "m5_pocket_right")),
        "coupon_matches": actual["coupon_full_interface_symmetric_difference_mm3"] <= 1e-5,
        "shim_0p5": abs(actual["shim_0p5_actual_thickness_mm"] - 0.5) <= TOL,
        "shim_1p0": abs(actual["shim_1p0_actual_thickness_mm"] - 1.0) <= TOL,
    }
    if not all(checks.values()): raise AssertionError("actual geometry " + json.dumps(checks))
    return {"step": step_report, "stl": stl_report, "actual_geometry": actual,
            "actual_geometry_checks": checks}


def regression() -> dict:
    with tempfile.TemporaryDirectory(prefix="cbox_top_tslot_regression_") as folder:
        path = Path(folder) / "wrong_shim.step"
        export_step(leveling_shim(0.6), path)
        wrong = cq.importers.importStep(str(path))
        rejected = abs(size(wrong)[2] - 0.5) > TOL
        if not rejected: raise AssertionError("+0.10 systematic error missed")
    return {"requested_0p5_actual_0p6_rejected": rejected,
            "actual_step_geometry_required": True}


def _svg(title: str, body: str, notes: list[str]) -> str:
    text = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#17324a}.rail{fill:#aeb8c2;stroke:#455a64;stroke-width:3}.saddle{fill:#ffd998;stroke:#b66a00;stroke-width:3}.cbox{fill:#bfe9f5;stroke:#007596;stroke-width:3}.bbox{fill:#cfead6;stroke:#26734d;stroke-width:3}.dim{fill:none;stroke:#d05224;stroke-width:2}.old{fill:none;stroke:#8d65ad;stroke-width:3;stroke-dasharray:8 6}</style>'
    text += f'<text x="30" y="45" font-size="27">{title}</text>{body}'
    for index, note in enumerate(notes):
        text += f'<text x="30" y="{650 + index * 30}" font-size="17">{note}</text>'
    return text + '<text x="30" y="782" font-size="14">CBOX TOP-T-SLOT SADDLE V002 | COUPON FIRST | FULL SADDLE PRINT HOLD</text></svg>'


def previews() -> dict[str, str]:
    top = '<rect class="saddle" x="150" y="210" width="900" height="250"/><rect class="rail" x="150" y="305" width="900" height="60"/><rect x="329" y="295" width="42" height="80" rx="20" fill="#fff" stroke="#d05224" stroke-width="3"/><rect x="829" y="295" width="42" height="80" rx="20" fill="#fff" stroke="#d05224" stroke-width="3"/><text x="430" y="520" font-size="22">M5 pitch 100 mm · transverse travel ±1.5 mm</text>'
    right = top.replace('x="329"', 'x="829"', 1).replace('x="829"', 'x="329"', 1)
    cross = '<rect class="rail" x="380" y="410" width="440" height="170"/><path fill="#fff" stroke="#455a64" stroke-width="3" d="M530 410v40h-55v100h250V450h-55v-40z"/><path class="saddle" d="M270 180h660v230H710v-15H490v15H270z"/><rect class="cbox" x="240" y="90" width="720" height="90"/><text x="480" y="365" font-size="20">top M5 service pocket</text>'
    detail = '<rect class="rail" x="330" y="440" width="540" height="130"/><path class="saddle" d="M230 180h740v260H230z"/><rect x="535" y="180" width="130" height="225" rx="50" fill="#fff" stroke="#d05224" stroke-width="3"/><line class="dim" x1="535" y1="145" x2="665" y2="145"/><text x="500" y="120" font-size="20">pocket Ø12 + 3 travel</text><text x="500" y="620" font-size="20">hole Ø5.8 + 3 travel</text>'
    hardware = '<rect class="cbox" x="250" y="100" width="700" height="90"/><path class="saddle" d="M220 190h760v240H220z"/><rect class="rail" x="300" y="430" width="600" height="150"/><line class="dim" x1="600" y1="140" x2="600" y2="560"/><text x="630" y="240" font-size="20">head Ø10×4 candidate</text><text x="630" y="290" font-size="20">pocket Ø12×4.5</text><text x="630" y="540" font-size="20">T-nut exact dimensions PENDING</text>'
    support = '<rect class="cbox" x="175" y="150" width="850" height="120"/><rect class="saddle" x="210" y="270" width="780" height="180"/><rect class="rail" x="340" y="450" width="520" height="130"/><line class="dim" x1="920" y1="270" x2="920" y2="450"/><text x="935" y="370" font-size="20">rise +8 mm</text><text x="390" y="235" font-size="20">CBOX on PETG support, not M5 head</text>'
    bbox = '<rect class="cbox" x="140" y="120" width="920" height="120"/><rect class="saddle" x="200" y="240" width="800" height="90"/><rect class="rail" x="320" y="330" width="560" height="90"/><rect class="bbox" x="200" y="510" width="800" height="80"/><line class="dim" x1="930" y1="330" x2="930" y2="510"/><text x="950" y="430" font-size="20">7.849 mm min vertical</text>'
    heights = '<rect class="rail" x="180" y="400" width="320" height="150"/><rect class="rail" x="700" y="408" width="320" height="150"/><rect class="saddle" x="150" y="270" width="380" height="130"/><rect class="saddle" x="670" y="278" width="380" height="130"/><line class="dim" x1="570" y1="270" x2="570" y2="278"/><text x="530" y="245" font-size="20">1 mm</text>'
    coupon = '<rect class="saddle" x="270" y="170" width="660" height="280"/><rect class="rail" x="350" y="450" width="500" height="130"/><rect x="540" y="170" width="120" height="245" rx="45" fill="#fff" stroke="#d05224" stroke-width="3"/><text x="420" y="620" font-size="22">FIRST PRINT · 40 mm · one vertical M5</text>'
    diff = '<path class="old" d="M230 250h650v110h-90v160H360V360H230z"/><path class="saddle" d="M230 170h650v260H700v80H410v-80H230z"/><rect x="520" y="170" width="90" height="220" fill="#fff" stroke="#d05224" stroke-width="3"/><text x="170" y="580" font-size="20">dashed: V001 side flange · solid: V002 top foot/pocket</text>'
    return {
        "previews/v002_left_top.svg": _svg("V002 left saddle — top", top, ["Independent left saddle; no cross-rail bridge.", "Two top M5 slots at X=±50 mm."]),
        "previews/v002_right_top.svg": _svg("V002 right saddle — top", right, ["Mirrored CBOX locating lip; vertical fastener architecture unchanged.", "SIDE_M5_HOLE_COUNT = 0."]),
        "previews/v002_cross_section.svg": _svg("V002 rail/CBOX cross-section", cross, ["20 mm top-face envelope is PHYSICAL_DERIVED.", "Complete lip shape and top-slot center remain physical coupon inputs."]),
        "previews/top_tslot_mount_detail.svg": _svg("Top T-slot mount detail", detail, ["M5 through-slot 5.8 x8.8; pocket 12 x15 plan envelope.", "Adjustment is only ±1.5 mm transverse."]),
        "previews/m5_tnut_section.svg": _svg("M5/T-nut packaging candidate", hardware, ["M5x16 exists elsewhere as no-load physical evidence, but this stack differs.", "Head/T-nut actual dimensions and screw bottoming require coupon validation."]),
        "previews/cbox_support_section.svg": _svg("CBOX support/load path", support, ["CBOX → PETG support → saddle foot → rail → M5/T-nut retention.", "CBOX does not rest on screw heads or BBOX lid."]),
        "previews/bbox_clearance.svg": _svg("BBOX clearance reference", bbox, ["V002 raises CBOX +4 mm relative V001; computed vertical clearance7.849 mm.", "BBOX lid/gasket/chimney/M4 remain unchanged and non-load-bearing."]),
        "previews/rail_height_difference.svg": _svg("Independent response to 1 mm rail Z difference", heights, ["Left top255; right top254 mm. Saddles remain independent.", "Optional0.5/1.0 mm shims are test components, not mandatory correction."]),
        "previews/mount_coupon.svg": _svg("Quick top-T-slot mount coupon", coupon, ["Print this before either140 mm saddle.", "Tests flat seating, slot alignment, T-nut, pocket and tool access."]),
        "previews/v001_vs_v002_cross_section.svg": _svg("V001 vs V002 interface difference", diff, ["CBOX support/lip perimeter retained; shifted upward4 mm.", "Rail and fastener interfaces intentionally replaced after physical fail."]),
    }


def generate(out: Path) -> None:
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    (out / "previews").mkdir(exist_ok=True)
    for path, shape in step_models().items(): export_step(shape, out / path)
    for path, shape in stl_models().items(): export_stl(shape, out / path)
    for path, text in previews().items(): (out / path).write_text(text + "\n", encoding="utf-8", newline="\n")


def reproduce() -> dict:
    with tempfile.TemporaryDirectory(prefix="cbox_top_tslot_reproduce_") as folder:
        out = Path(folder); generate(out)
        result = {p: sha(LANE / p) == sha(out / p) for p in STEPS + STLS + SVGS}
    if not all(result.values()): raise AssertionError("reproducibility " + json.dumps(result))
    return {"byte_identical": result, "count": len(result),
            "pass_count": sum(result.values()), "pass": True}


def source_audit() -> dict:
    state = audit()
    return {
        "v001": {
            "lane": PARENT_REL, "tree": state["protected"][PARENT_REL],
            "classification": "READ_ONLY_PARTIAL_SUPERSESSION_SOURCE",
            "rail_interface": "PHYSICAL_FIT_FAIL", "side_m5_alignment": "PHYSICAL_FIT_FAIL",
            "cbox_side_geometry": "NOT_YET_REJECTED", "structural_mount": "NOT_APPROVED",
        },
        "current_upper_rail": {
            "profile_source": "cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/physical_dimensions_2026_09_01.json",
            "source_class": "PHYSICAL_DIRECT_PLUS_PHYSICAL_DERIVED",
            "top_face_width_mm": RAIL_TOP_FACE_WIDTH,
            "top_face_width_class": "PHYSICAL_DERIVED_FROM_OUTSIDE_MINUS_INSIDE_SPANS",
            "height_mm": RAIL_HEIGHT, "height_class": "PHYSICAL_DIRECT_TOP_MINUS_BOTTOM",
            "project_profile_name": "2040_USER_CONTEXT_BUT_COMPLETE_PROFILE_IDENTITY_PENDING",
            "top_slot_count": TOP_SLOT_COUNT,
            "top_slot_count_class": "PHYSICAL_PARTIAL_SINGLE_TOP_SLOT_TASK_CONTEXT",
            "top_slot_center_local_y_mm": TOP_SLOT_CENTER_LOCAL_Y,
            "top_slot_center_class": TOP_SLOT_CENTER_CLASS,
            "complete_profile": "PENDING",
        },
        "slot": {"entrance_mm": SLOT_ENTRANCE, "internal_max_mm": SLOT_INTERNAL,
                 "depth_mm": SLOT_DEPTH, "class": "PHYSICAL_DIRECT",
                 "lip_profile": "PHYSICAL_PARTIAL"},
        "hardware": {
            "repository_source": "cad/common_rover/common_rover_powertrain_frame_joint_trade_study_v0_9_3_4",
            "known": "M5x16 + T-nut achieved full thread traversal in a DIFFERENT no-load stack",
            "known_class": "PHYSICAL_PASS_USER_REPORTED_DIFFERENT_ASSEMBLY",
            "head_and_tnut_dimensions": "PHYSICAL_MEASUREMENT_PENDING",
            "through_hole_mm": M5_THROUGH, "through_hole_class": "CAD_CLEARANCE_CANDIDATE",
            "head_envelope_mm": [M5_HEAD_ENVELOPE_DIAMETER, M5_HEAD_ENVELOPE_HEIGHT],
            "head_envelope_class": "REPOSITORY_CANDIDATE_NOT_PHYSICAL_AUTHORITY",
            "pocket_mm": [M5_POCKET_DIAMETER, M5_POCKET_DEPTH],
            "pocket_class": "GENEROUS_SERVICE_CANDIDATE_COUPON_GATE",
            "tnut_reference_step_generated": False,
            "reason": "No reliable exact T-nut/head dimensions found; do not fabricate a precision reference.",
        },
        "bbox": {
            "integration_reference": PARENT_REL + "/references/bbox_v003_protected_reference.step",
            "current_v004_protected": "cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065",
            "v004_global_transform": "PHYSICAL_PENDING",
            "modification_count": 0,
        },
        "cbox": {
            "source": "cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/artifacts/cbox_shell_v0_9_6_32.step",
            "physical_body_xyz_mm": [150, 246, 80], "cad_tab_envelope_x_mm": 152,
            "long_axis": "Y_TRANSVERSE", "modification_count": 0,
        },
        "protected_source_changed_count": state["protected_source_changed_count"],
        "protected": state["protected"],
    }


def physical_template() -> dict:
    return {
        "coupon": {
            "upper_rail_identified": None, "coupon_sits_flat": "PASS/FAIL",
            "top_m5_aligns_with_slot": "PASS/FAIL", "tnut_inserts": "PASS/FAIL",
            "m5_threads_normally": "PASS/FAIL", "tightens_against_rail": "PASS/FAIL",
            "rocking": "NONE/SMALL/FAIL", "screw_head_below_cbox_plane": "YES/NO",
            "tool_access": "PASS/FAIL", "rail_damage": "NONE/MARK/GOUGE",
            "petg": "NONE/WHITENING/CRACK",
            "final": "TOP_T_SLOT_COUPON_PHYSICAL_PASS/ADJUST/FAIL",
        },
        "full_saddles_after_coupon_pass": {
            "left_rail_fit": "PASS/FAIL", "right_rail_fit": "PASS/FAIL",
            "four_m5_tnut_fasteners": "PASS/FAIL", "cbox_dry_placement": "PASS/FAIL",
            "cbox_lateral_fit": "PASS/TIGHT/LOOSE", "cbox_removable": "YES/NO",
            "cbox_to_bbox_contact": "NONE/YES", "bbox_lid_access": "PASS/FAIL",
            "chimney_access": "PASS/FAIL", "crawler_static_contact": "NONE/YES",
            "rail_height_difference": "NO_ISSUE/SHIM_REQUIRED/FAIL",
            "static_cbox_support": "PASS/FAIL", "manual_light_shake": "PASS/FAIL",
            "petg_damage": "NONE/WHITENING/CRACK",
        },
    }


def documents() -> dict[str, str]:
    readme = f"""# CBOX Transverse Top-T-Slot Independent Saddle V002

{STATUS}

V001's independent/transverse CBOX concept remains useful, but its side-wall
rail interface and side M5 alignment are PHYSICAL_FIT_FAIL.  V002 removes every
side fastener hole and uses two vertical M5 adjustment slots per saddle into the
upper rail's top T-slot.  Left/right saddles remain independent; no bridge forces
189 mm spacing or coplanarity.

The physical authority gives each current upper rail a20 mm Y width from the
outside/inside spans and20 mm Z height from top/bottom readings.  The repository
does not prove a complete named2040 cross-section.  One current top slot is the
task's physical context, but its center relative to rail edges remains pending.
The design therefore uses local Y0 only as a reference with ±1.5 mm adjustment.

Direct slot constraints are entrance6.4, internal maximum10.8 and depth6.4 mm.
The rail reference STEP uses those bounds but an explanatory1 mm lip-depth split;
that split, lip angles and radii are NOT physical authority.

Each saddle is140 mm long with vertical M5 centers X=±50 (pitch100 mm), through
slot5.8×8.8 and service pocket12×15 in plan,4.5 deep.  Hardware dimensions are
not physically established in this stack.  The 8 mm support rise is the minimum
studied candidate retaining3.5 mm PETG below the service pocket; +4/+6 are held.
The retained support follows the measured1 mm/189 mm rail-plane slope (0.303°).
An open-edge Ø16 mm local notch preserves the existing BBOX inner-M4 driver
path; it does not change the coupon's top-slot/M5 authority region.
The assembly STEP carries a documented0.02 mm numerical face separation so
coincident CAD faces are not misreported as solid overlap; it is not a spacer.

FIRST PRINT ONLY: `cbox_top_tslot_mount_coupon_v002.stl`.  PETG, Bambu A1,
rail-contact face down, support OFF.  Do not print either full saddle until the
coupon passes flat seating, top-slot alignment, T-nut engagement, tightening,
head clearance, rocking, tool access and damage checks.

The full left/right CAD/STL exists for review but has
FULL_SADDLE_PRINT_HOLD_UNTIL_COUPON_PASS.  No CBOX physical/load/field PASS is
claimed.  BBOX lid/gasket/chimney/M4 are unchanged and non-load-bearing.
`COMMIT_PATHS.txt` is an inventory, not permission to stage.
"""
    design = """# CBOX top-T-slot saddle V002 design

Architecture: CBOX → preserved/local PETG support → saddle body → rail top →
metal M5/T-nut retention.  It is never CBOX → screw head or BBOX lid.

V001 pad footprint (local Y1.2..32.5),140 mm length and outboard locating lip
(Y29.5..32.5,5 mm high) are retained.  They move upward by a nominal4 mm because
the support rise changes from4 to8 mm, then follow the directly observed1 mm
left/right rail-height slope over189 mm (0.303°).  Local vertical-hole/service-
pocket openings and one open-edge Ø16 mm BBOX-driver notch reduce the contact
plane.  The failed side flange below rail top is deleted.

The new rail foot spans local Y=-10..+10 and Z0..7.5.  The0.5 mm drop below the
8 mm CBOX support plane keeps inboard foot material from becoming a new broad
CBOX datum.  Two vertical slots preserve the V001 longitudinal100 mm pitch.

No fixed left/right bridge, side hole, plastic rail-biting screw, BBOX hole,
automatic docking, complex lock or mandatory leveling correction is included.
Open top pockets and through slots remain washable and tool-accessible.
"""
    failure = """# V001 physical fit failure record

V001 printed left/right saddle:

- CBOX-side geometry: NOT_YET_REJECTED.
- Rail-side interface: PHYSICAL_FIT_FAIL.
- Side M5 alignment: PHYSICAL_FIT_FAIL.
- Structural mounting: NOT_APPROVED.

Do not drill, rework or reinterpret V001 as passing.  This is a partial
supersession only.  Its transverse CBOX, independent saddles, BBOX separation,
approximate placement, crawler study and chimney avoidance remain useful
references.  V002 intentionally replaces only rail-contact/fastener architecture
plus the support height needed for top hardware service.
"""
    rail = """# Upper rail profile audit

Current source: physical_dimensions_2026_09_01.json.

Outside span208–210 and inside span168–170 yield20 mm per rail.  Left255/235
and right254/234 yield20 mm heights.  Thus the local contact envelope is20 mm
wide and20 mm high, PHYSICAL_DERIVED/PHYSICAL_DIRECT.  Absolute vehicle Y is
still pending;189 mm is only the midpoint of the188–190 center range.

The task/repository language calls the member2040, but neither that name nor old
generic40 mm proxies override direct20 mm top-face evidence.  Complete purchased
profile identity is PENDING.  Top slot count1 is PHYSICAL_PARTIAL from the
singular measured top-slot task context.  Its edge-relative centerline was not
independently measured; local Y0 is CAD_REFERENCE with ±1.5 mm coupon-tested
adjustment.  Full saddle print release therefore remains HOLD.

Direct slot bounds: entrance6.4, internal10.8, depth6.4 mm.  Lip thickness,
angle and radii remain PHYSICAL_PARTIAL.
"""
    m5 = """# Top T-slot M5 interface

Per saddle: two vertical M5 slots at X=-50/+50 mm, pitch100 mm.  No side holes.
Through geometry is5.8 mm diameter swept ±1.5 mm in local Y (5.8×8.8 overall).
The head service pocket is12 mm diameter swept the same travel (12×15 overall),
4.5 mm deep from the8 mm support plane.  The nominal10×4 mm head envelope comes
from repository candidate practice, not direct physical measurement.

M5×16 and full T-nut thread traversal are physically reported only for a
different motor-plate stack.  Screw type/head/washer/T-nut dimensions, actual
thread engagement and bottoming in this saddle are PENDING.  No exact T-nut STEP
is generated.  The mount coupon carries the identical local rail/pocket geometry
and is the authority-selection test.
"""
    diff = """# V001 / V002 geometry difference

CBOX_SUPPORT_INTERFACE_DIFF = MINIMAL, localized to two top M5 service openings,
one open-edge Ø16 mm BBOX-driver service notch, a nominal +4 mm rise and a
0.303° measured-plane tilt.  The V001 support length and lip cross-section are
retained; only the documented access notch interrupts the outer pad edge.
Assembly collision analysis uses0.02 mm BRep contact disambiguation; production
support datum remains the nominal8 mm plane and no physical spacer is released.

RAIL_INTERFACE_DIFF = INTENTIONAL: failed below-top side flange removed;20 mm
top-contact foot added.

FASTENER_INTERFACE_DIFF = INTENTIONAL: two side M5 holes removed and two top
vertical M5 adjustment slots added per saddle.  Exact face area/volume and bounds
are machine reported in geometry_diff_report.json.  No V001 file is modified.
"""
    coupon = """# CBOX top T-slot mount coupon test

FIRST PRINT = cbox_top_tslot_mount_coupon_v002.stl.  PETG/Bambu A1, rail-contact
face down, support OFF.  Remove brim/burrs without sanding working interfaces.

Upper rail identified: ____
Coupon sits flat: PASS / FAIL
Top M5 aligns with slot: PASS / FAIL
T-nut inserts: PASS / FAIL
M5 threads normally: PASS / FAIL
Tightens against rail: PASS / FAIL
Rocking: NONE / SMALL / FAIL
Screw head below CBOX support plane: YES / NO
Tool access: PASS / FAIL
Rail damage: NONE / MARK / GOUGE
PETG: NONE / WHITENING / CRACK
FINAL: TOP_T_SLOT_COUPON_PHYSICAL_PASS / ADJUST / FAIL

Stop on any fail.  Do not print full saddles, force hardware, drill V001/V002 or
infer load capacity.  Record actual head height, washer OD/thickness, T-nut type,
thickness and screw bottom clearance while the coupon is accessible.
"""
    full = """# Full saddle physical test plan

Run only after documented coupon PASS.

1. Print left/right PETG, rail-contact face down, support OFF.
2. Check left/right rail fit independently and all four M5/T-nut fasteners.
3. Place empty/dummy CBOX, then real unpowered CBOX. Check lateral fit, support
   and removal without opening BBOX or removing saddles.
4. With CBOX removed, confirm BBOX M4 lid and chimney/gland service access.
5. Check crawler static contact and whether the1 mm rail-height difference needs
   no shim,0.5 mm or1.0 mm removable shim. Never force rail coplanarity.
6. Perform only a gentle manual shake. Inspect PETG whitening/cracks and hardware.

Load capacity, vibration, powered rover, wash/mud/drainage and field tests remain
pending.  Dynamic crawler PASS is not created by the74 mm static reference.
"""
    shim = """# Leveling shim strategy

The two independent saddles naturally follow left255/right254 mm rail tops.
No mandatory correction is baked into either saddle.  Optional140×20 mm PETG
shims of actual0.500000 and1.000000 mm are supplied with the same two5.8×8.8
adjustment slots.

Use a shim only after coupon/full dry fit shows that CBOX service or stability
benefits.  Record side, measured installed thickness and result.  Do not stack
unbounded layers, force rails into plane or promote one measurement to a permanent
frame correction.  Metal precision shims may be evaluated in a future load lane.
"""
    holds = """# Global integration holds

Local CAD intersections are zero for CBOX/BBOX, saddle/BBOX, saddle/chimney,
CBOX/chimney, saddle/crawler and retained BBOX M4 driver-path references.  V002
raises CBOX by a nominal4 mm relative V001 and follows the measured rail slope,
giving7.869 mm assembly-reference BBOX-lid clearance (including0.02 mm numerical
face separation) in the retained V001 registration.

HOLD: complete rail/profile identity; physical top-slot center; lip shape;
M5 head/washer/T-nut dimensions; screw length/engagement/bottoming; mount coupon;
full saddle print; CBOX retention/lateral fit; actual tool access; current BBOX
V004 installed transform; global Front Interface V002 transform; slicer; static
real-CBOX load; shake/vibration; crawler dynamic clearance; wash/mud/drainage;
powered and field operation.

Front Interface V002 remains REFERENCE_ONLY and cannot fail the local mount gate.
BBOX modification count0; lid/gasket/chimney/gland/M4 pattern remain protected.
"""
    return {name: text.rstrip() + "\n" for name, text in zip(
        DOCS, [readme, design, failure, rail, m5, diff, coupon, full, shim, holds]
    )}


def design_parameters() -> dict:
    return {
        "version": "CBOX_TRANSVERSE_TOP_TSLOT_INDEPENDENT_SADDLE_V002",
        "status": STATUS,
        "architecture": {
            "cbox_orientation": "TRANSVERSE_LONG_AXIS_Y",
            "left_right_independent": True, "fixed_cross_rail_bridge": False,
            "top_vertical_m5": True, "top_vertical_m5_per_saddle": 2,
            "side_m5_hole_count": 0, "bbox_load_bearing": False,
            "cbox_load_on_m5_head": False,
        },
        "rail": source_audit()["current_upper_rail"],
        "slot": source_audit()["slot"], "hardware": source_audit()["hardware"],
        "saddle": {
            "length_mm": SADDLE_LENGTH, "m5_pitch_mm": M5_PITCH,
            "m5_x_mm": M5_X, "through_slot_mm": [M5_THROUGH, M5_THROUGH + 2 * TRANSVERSE_ADJUSTMENT],
            "pocket_plan_mm": [M5_POCKET_DIAMETER, M5_POCKET_DIAMETER + 2 * TRANSVERSE_ADJUSTMENT],
            "pocket_depth_mm": M5_POCKET_DEPTH, "support_rise_mm": SELECTED_RISE,
            "left_support_global_z_mm": LEFT_RAIL_TOP + SELECTED_RISE,
            "right_support_global_z_mm": RIGHT_RAIL_TOP + SELECTED_RISE,
            "material": "PETG", "full_print": "HOLD_UNTIL_TOP_T_SLOT_COUPON_PASS",
        },
        "rise_study": rise_study(), "clearance": clearance_data(),
        "geometry_diff": geometry_diff(),
        "print": {"printer": "BAMBU_A1", "orientation": "RAIL_CONTACT_FACE_DOWN",
                  "support": "OFF", "slicer": "HOLD_SLICER_NOT_RUN",
                  "first_print": "artifacts/cbox_top_tslot_mount_coupon_v002.stl"},
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def build() -> None:
    audit(); generate(LANE)
    quality = inspect(LANE); reproduction = reproduce(); drift = regression()
    for name, text in documents().items(): (LANE / name).write_text(text, encoding="utf-8", newline="\n")
    write_json(LANE / "source_authority_audit.json", source_audit())
    write_json(LANE / "geometry_diff_report.json", geometry_diff())
    write_json(LANE / "physical_result_template.json", physical_template())
    write_json(LANE / "design_parameters.json", design_parameters())
    write_json(LANE / "validation_report.json", {
        "status": "GENERATED_CONTRACT_PENDING", "quality": quality,
        "clearance": clearance_data(), "geometry_diff": geometry_diff(),
        "rise_study": rise_study(), "regression": drift,
        "cad_reproducibility": reproduction, "documentation_reproducibility": "PENDING_CONTRACT",
    })
    print(json.dumps({"build": "GENERATED_CONTRACT_PENDING", "STEP": len(STEPS),
                      "STL": len(STLS), "SVG": len(SVGS), "exact_paths": len(EXPECTED),
                      "actual": quality["actual_geometry"], "clearance": clearance_data(),
                      "reproducibility": reproduction}, indent=2))


def finalize(report: dict) -> None:
    if not report["pass"]: raise AssertionError("contract failed")
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
        "first_print": "artifacts/cbox_top_tslot_mount_coupon_v002.stl",
        "full_saddle_print": "HOLD_UNTIL_TOP_T_SLOT_COUPON_PASS",
        "printable_stl": STLS,
        "tnut_reference_step": "NOT_GENERATED_EXACT_DIMENSIONS_UNRELIABLE",
    })
    (LANE / "COMMIT_PATHS.txt").write_text(
        "\n".join(REL + "/" + path for path in EXPECTED) + "\n",
        encoding="utf-8", newline="\n")
    for name in ("repository_audit.json", "SHA256SUMS.txt"):
        if not (LANE / name).exists(): (LANE / name).write_text("", encoding="ascii")
    write_json(LANE / "repository_audit.json", audit())
    (LANE / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(LANE / path)}  {path}\n" for path in EXPECTED if path != "SHA256SUMS.txt"),
        encoding="ascii", newline="\n")


def verify() -> None:
    state = audit()
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    if files != EXPECTED: raise AssertionError("exact paths")
    lines = (LANE / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
    if len(lines) != len(EXPECTED) - 1: raise AssertionError("SHA inventory")
    for line in lines:
        digest, path = line.split("  ", 1)
        if sha(LANE / path) != digest: raise AssertionError("SHA mismatch " + path)
    contract = json.loads((LANE / "contract_test_report.json").read_text(encoding="utf-8"))
    if not contract["pass"]: raise AssertionError("contract report")
    for name, text in documents().items():
        if (LANE / name).read_bytes() != text.encode("utf-8"):
            raise AssertionError("document byte drift " + name)
    quality = inspect(LANE); reproduction = reproduce()
    print(json.dumps({"verify": "PASS", "audit": state,
                      "quality_count": {"step": len(quality["step"]), "stl": len(quality["stl"])},
                      "actual": quality["actual_geometry"], "clearance": clearance_data(),
                      "cad_reproducibility": reproduction,
                      "documentation_reproducibility": len(DOCS)}, indent=2))


def handoff() -> None:
    verify()
    target = Path(r"D:\Downloads") / (
        "Paddy_Swarm_CBOX_TOP_TSLOT_SADDLE_V002_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip")
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in EXPECTED: archive.write(LANE / path, LANE.name + "/" + path)
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
