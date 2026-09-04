"""P25 slide-in positioning gauge for a physically measured, partial 2040 slot.

The three measured slot constraints are authoritative.  The reference STEP is
deliberately not a generic 2040 reconstruction.  This lane is positioning-only;
it does not release a structural PTO spacer or fastener.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
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
REL = "cad/common_rover/pto/pto_p25_slide_in_positioning_v002"
PARENT_REL = "cad/common_rover/pto/pto_offset_spacer_test_v001"
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
TOL = 1.0e-6
STATUS = (
    "CAD_PASS/CONTRACT_TEST_PASS/2040_SLIDE_FIT_COUPONS_PRINT_READY/"
    "P25_SLIDE_B_PROVISIONAL_PRINT_READY/PHYSICAL_FIT_SELECTION_PENDING/"
    "STRUCTURAL_LOAD_AUTHORITY_PENDING"
)

SLOT = {
    "entrance_width_mm": 6.4,
    "maximum_internal_width_mm": 10.8,
    "surface_to_bottom_depth_mm": 6.4,
    "measurement_class": "PHYSICAL_DIRECT",
    "lip_profile": "PHYSICAL_PARTIAL",
}
VARIANTS = {
    "A": {"stem_width_mm": 5.6, "head_width_mm": 9.8, "depth_mm": 5.8},
    "B": {"stem_width_mm": 5.8, "head_width_mm": 10.0, "depth_mm": 5.9},
    "C": {"stem_width_mm": 6.0, "head_width_mm": 10.2, "depth_mm": 6.0},
}
HEAD_THICKNESS = 2.0
LEAD_IN = 0.4
COUPON_LENGTH = 20.0
COUPON_BODY_WIDTH = 14.0
COUPON_BODY_HEIGHT = 4.0
P25_LENGTH = 25.0
P25_BODY_WIDTH = 18.0
P25_BODY_HEIGHT = 8.0

PRINT_NAMES = [
    "2040_slide_fit_coupon_A",
    "2040_slide_fit_coupon_B",
    "2040_slide_fit_coupon_C",
    "p25_slide_in_positioning_block_B_provisional",
]
REFERENCE_NAMES = ["2040_physical_slot_reference", "p25_slide_reference_assembly"]
STEPS = [f"artifacts/{name}.step" for name in PRINT_NAMES + REFERENCE_NAMES]
STLS = [f"artifacts/{name}.stl" for name in PRINT_NAMES]
SVGS = [f"previews/{name}.svg" for name in [
    "slot_cross_section", "coupon_A_section", "coupon_B_section",
    "coupon_C_section", "coupon_comparison", "p25_slide_block",
    "p25_working_datum",
]]
DOCS = [
    "README.md", "P25_SLIDE_IN_V002_DESIGN.md",
    "2040_PHYSICAL_SLOT_MEASUREMENTS.md", "SLIDE_FIT_VARIANT_MATRIX.md",
    "PHYSICAL_TEST_PLAN.md", "PHYSICAL_RESULT_SHEET.md",
    "STRUCTURAL_LOAD_HOLD.md",
]
REPORTS = [
    "design_parameters.json", "validation_report.json",
    "contract_test_report.json", "source_authority_audit.json",
    "physical_result_template.json", "repository_audit.json", "manifest.json",
]
EXPECTED = sorted([
    Path(__file__).name, "tests/test_p25_slide_in_positioning_v002.py",
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
    for path_item in files:
        h.update((path_item.relative_to(path).as_posix() + "\n").encode())
        h.update(bytes.fromhex(sha(path_item)))
    return {"files": len(files), "sha256": h.hexdigest()}


def audit() -> dict:
    base = json.loads((LANE / "audit_start.json").read_text(encoding="utf-8"))
    raw = git("ls-files", "--others", "--exclude-standard", "-z")
    untracked = sorted(p for p in raw.split("\0") if p)
    outside = [p for p in untracked if not p.startswith(REL + "/")]
    own = [p[len(REL) + 1:] for p in untracked if p.startswith(REL + "/")]
    dirty = {p: sha(ROOT / p) for p in git("diff", "--name-only").splitlines()}
    protected = {p: tree_hash(ROOT / p) for p in base["protected"]}
    state = {
        "repository": str(Path(git("rev-parse", "--show-toplevel")).resolve()),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "staged_count": len(git("diff", "--cached", "--name-only").splitlines()),
        "tracked_dirty_count": len(dirty),
        "dirty": dirty,
        "protected": protected,
        "protected_source_changed_count": sum(
            protected[p] != base["protected"][p] for p in protected
        ),
        "outside_untracked_count": len(outside),
        "outside_untracked_paths_sha256": hashlib.sha256(
            ("\n".join(outside) + "\n").encode()
        ).hexdigest(),
        "new_path_count": len(own),
        "untracked_total": len(untracked),
    }
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    ok = (
        Path(state["repository"]) == ROOT
        and state["branch"] == BRANCH
        and state["head"] == HEAD
        and state["staged_count"] == 0
        and state["dirty"] == base["dirty"]
        and state["protected"] == base["protected"]
        and state["outside_untracked_count"] == base["outside_untracked_count"]
        and state["outside_untracked_paths_sha256"] == base["outside_untracked_paths_sha256"]
        and files == own
        and set(files).issubset(EXPECTED)
    )
    state["pass"] = bool(ok)
    if not ok:
        raise AssertionError("FAIL_CLOSED " + json.dumps(state, sort_keys=True))
    return state


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def volume(shape: cq.Workplane) -> float:
    return sum(s.Volume() for s in shape.solids().vals())


def bounds(shape: cq.Workplane) -> list[float]:
    b = shape.val().BoundingBox()
    return [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]


def size(shape: cq.Workplane) -> list[float]:
    b = bounds(shape)
    return [b[i + 3] - b[i] for i in range(3)]


def common(a: cq.Workplane, b: cq.Workplane) -> float:
    return volume(a.intersect(b))


def distance(a: cq.Workplane, b: cq.Workplane) -> float:
    operation = BRepExtrema_DistShapeShape(a.val().wrapped, b.val().wrapped)
    operation.Perform()
    if not operation.IsDone():
        raise AssertionError("distance calculation failed")
    return operation.Value()


def _bar(length: float, width: float, depth: float, x: float, y: float, angle: float = 0) -> cq.Workplane:
    return box(length, width, depth, (x, y, P25_BODY_HEIGHT - depth / 2)).rotate(
        (x, y, 0), (x, y, 1), angle
    )


def _letter(letter: str, x: float, y: float, z_top: float, scale: float = 1.0) -> cq.Workplane:
    depth = 0.6
    w = 0.55 * scale
    parts: list[cq.Workplane] = []

    def seg(x1: float, y1: float, x2: float, y2: float) -> None:
        length = math.hypot(x2 - x1, y2 - y1)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        part = box(length, w, depth, ((x1 + x2) / 2, (y1 + y2) / 2, z_top - depth / 2))
        parts.append(part.rotate(((x1 + x2) / 2, (y1 + y2) / 2, 0), ((x1 + x2) / 2, (y1 + y2) / 2, 1), angle))

    coords = {
        "top": (-2, 2.5, 2, 2.5), "mid": (-2, 0, 2, 0),
        "bot": (-2, -2.5, 2, -2.5), "left": (-2, -2.5, -2, 2.5),
        "ru": (2, 0, 2, 2.5), "rl": (2, -2.5, 2, 0),
    }
    if letter == "A":
        seg(x - 2 * scale, y - 2.5 * scale, x, y + 2.5 * scale)
        seg(x, y + 2.5 * scale, x + 2 * scale, y - 2.5 * scale)
        seg(x - 1.15 * scale, y, x + 1.15 * scale, y)
    else:
        mapping = {"B": ["top", "mid", "bot", "left", "ru", "rl"],
                   "C": ["top", "bot", "left"]}
        for name in mapping[letter]:
            x1, y1, x2, y2 = coords[name]
            seg(x + x1 * scale, y + y1 * scale, x + x2 * scale, y + y2 * scale)
    result = parts[0]
    for item in parts[1:]:
        result = result.union(item)
    return result


def _digit_segments(digit: str) -> list[str]:
    return {
        "2": ["top", "ru", "mid", "ll", "bot"],
        "5": ["top", "lu", "mid", "rl", "bot"],
    }[digit]


def _digit(digit: str, x: float, y: float, z_top: float) -> cq.Workplane:
    depth = 0.6
    parts: list[cq.Workplane] = []
    centers = {
        "top": (0, 2.4, 3.2, 0), "mid": (0, 0, 3.2, 0), "bot": (0, -2.4, 3.2, 0),
        "lu": (-1.6, 1.2, 2.4, 90), "ru": (1.6, 1.2, 2.4, 90),
        "ll": (-1.6, -1.2, 2.4, 90), "rl": (1.6, -1.2, 2.4, 90),
    }
    for name in _digit_segments(digit):
        dx, dy, length, angle = centers[name]
        p = box(length, 0.5, depth, (x + dx, y + dy, z_top - depth / 2))
        parts.append(p.rotate((x + dx, y + dy, 0), (x + dx, y + dy, 1), angle))
    result = parts[0]
    for item in parts[1:]:
        result = result.union(item)
    return result


def tongue(spec: dict, length: float) -> cq.Workplane:
    stem_h = spec["depth_mm"] - HEAD_THICKNESS
    main_length = length - LEAD_IN
    stem_main = box(main_length, spec["stem_width_mm"], stem_h,
                    (LEAD_IN + main_length / 2, 0, -stem_h / 2))
    head_main = box(main_length, spec["head_width_mm"], HEAD_THICKNESS,
                    (LEAD_IN + main_length / 2, 0, -stem_h - HEAD_THICKNESS / 2))

    # Only the insertion-end 0.4 mm is a lead-in.  Every fit surface after it
    # is prismatic and exactly equal to the requested fit dimensions.
    stem_lead = (cq.Workplane("YZ")
                 .center(0, -stem_h / 2)
                 .rect(spec["stem_width_mm"] - 0.6, stem_h)
                 .workplane(offset=LEAD_IN)
                 .rect(spec["stem_width_mm"], stem_h)
                 .loft(combine=True))
    head_lead = (cq.Workplane("YZ")
                 .center(0, -stem_h - HEAD_THICKNESS / 2)
                 .rect(spec["head_width_mm"] - 0.6, HEAD_THICKNESS)
                 .workplane(offset=LEAD_IN)
                 .rect(spec["head_width_mm"], HEAD_THICKNESS)
                 .loft(combine=True))
    return stem_main.union(head_main).union(stem_lead).union(head_lead).clean()


def coupon(letter: str) -> cq.Workplane:
    body = box(COUPON_LENGTH, COUPON_BODY_WIDTH, COUPON_BODY_HEIGHT,
               (COUPON_LENGTH / 2, 0, COUPON_BODY_HEIGHT / 2))
    result = body.union(tongue(VARIANTS[letter], COUPON_LENGTH)).clean()
    label = _letter(letter, COUPON_LENGTH / 2, 0, COUPON_BODY_HEIGHT)
    # Rebase label Z because the helper defaults to P25 height.
    label = label.translate((0, 0, COUPON_BODY_HEIGHT - P25_BODY_HEIGHT))
    return result.cut(label).clean()


def p25_block() -> cq.Workplane:
    body = box(P25_LENGTH, P25_BODY_WIDTH, P25_BODY_HEIGHT,
               (P25_LENGTH / 2, 0, P25_BODY_HEIGHT / 2))
    result = body.union(tongue(VARIANTS["B"], P25_LENGTH)).clean()
    # P25 is kept away from X end datums; the arrow points toward +X.
    text = _digit("2", 9.0, 2.2, P25_BODY_HEIGHT).union(
        _digit("5", 14.0, 2.2, P25_BODY_HEIGHT)
    )
    arrow = box(7.0, 0.5, 0.6, (12.5, -3.0, P25_BODY_HEIGHT - 0.3))
    arrow = arrow.union(box(2.3, 0.5, 0.6, (15.1, -2.2, P25_BODY_HEIGHT - 0.3)).rotate(
        (15.1, -2.2, 0), (15.1, -2.2, 1), 35
    )).union(box(2.3, 0.5, 0.6, (15.1, -3.8, P25_BODY_HEIGHT - 0.3)).rotate(
        (15.1, -3.8, 0), (15.1, -3.8, 1), -35
    ))
    return result.cut(text.union(arrow)).clean()


def slot_reference(length: float = 40.0) -> cq.Workplane:
    # Five separate constraint markers: internal side faces ±5.4, bottom -6.4,
    # and entrance side faces ±3.2.  Their unmeasured outward thicknesses are
    # display-only and never used as physical authority.
    internal = [
        box(length, 0.2, 6.4, (length / 2, 5.5, -3.2)),
        box(length, 0.2, 6.4, (length / 2, -5.5, -3.2)),
    ]
    bottom = box(length, 10.8, 0.2, (length / 2, 0, -6.5))
    entrance = [
        box(length, 0.2, 0.8, (length / 2, 3.3, -0.4)),
        box(length, 0.2, 0.8, (length / 2, -3.3, -0.4)),
    ]
    return cq.Workplane(obj=cq.Compound.makeCompound(
        [p.val() for p in [*internal, bottom, *entrance]]
    ))


def assembly_reference() -> cq.Workplane:
    block = p25_block().translate((7.5, 0, 0))
    refs = slot_reference(40.0)
    return cq.Workplane(obj=cq.Compound.makeCompound([refs.val(), block.val()]))


def print_oriented(shape: cq.Workplane) -> cq.Workplane:
    # Logical +X slide direction becomes print +Z.  The insertion-end face is
    # flat on the plate; stem/head width and slot depth are XY dimensions.
    rotated = shape.rotate((0, 0, 0), (0, 1, 0), -90)
    b = rotated.val().BoundingBox()
    return rotated.translate((-b.xmin, -b.ymin, -b.zmin))


def step_models() -> dict[str, cq.Workplane]:
    return {
        "artifacts/2040_slide_fit_coupon_A.step": coupon("A"),
        "artifacts/2040_slide_fit_coupon_B.step": coupon("B"),
        "artifacts/2040_slide_fit_coupon_C.step": coupon("C"),
        "artifacts/p25_slide_in_positioning_block_B_provisional.step": p25_block(),
        "artifacts/2040_physical_slot_reference.step": slot_reference(),
        "artifacts/p25_slide_reference_assembly.step": assembly_reference(),
    }


def stl_models() -> dict[str, cq.Workplane]:
    models = step_models()
    return {path.replace(".step", ".stl"): print_oriented(models[path])
            for path in [f"artifacts/{name}.step" for name in PRINT_NAMES]}


def export_step(shape: cq.Workplane, path: Path) -> None:
    cq.exporters.export(shape, str(path), exportType="STEP")
    text = path.read_text(encoding="ascii")
    text = re.sub(
        r"FILE_NAME\(.*?\);",
        f"FILE_NAME('{path.name}','2000-01-01T00:00:00',(''),(''),'Open CASCADE','CADQUERY','DETERMINISTIC_METADATA');",
        text,
        flags=re.S,
    )
    text = re.sub(r"Open CASCADE STEP translator (\d+\.\d+) \d+",
                  r"Open CASCADE STEP translator \1 deterministic", text)
    numbers = iter(range(1, 100000))
    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'",
                  lambda _: f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(numbers)}'", text)
    path.write_text(text, encoding="ascii", newline="\n")


def export_stl(shape: cq.Workplane, path: Path) -> None:
    vertices, triangles_data = shape.val().tessellate(0.02, 0.08)
    lines = ["solid P25_SLIDE_IN_POSITIONING_V002"]
    for tri in triangles_data:
        a, b, c = [vertices[i] for i in tri]
        n = (b - a).cross(c - a).normalized()
        lines.extend(["  facet normal " + " ".join(f"{v:.12g}" for v in n.toTuple()),
                      "    outer loop"])
        for point in (a, b, c):
            lines.append("      vertex " + " ".join(f"{v:.9f}" for v in point.toTuple()))
        lines.extend(["    endloop", "  endfacet"])
    lines.append("endsolid P25_SLIDE_IN_POSITIONING_V002")
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def triangles(path: Path) -> list:
    vertices = [tuple(map(float, line.split()[1:]))
                for line in path.read_text(encoding="ascii").splitlines()
                if line.lstrip().startswith("vertex ")]
    if len(vertices) % 3:
        raise AssertionError("invalid STL vertex count")
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
            graph[first].add(second)
            graph[second].add(first)
        for first, second, third in ((a, b, c), (b, c, a), (c, a, b)):
            links[first].append((second, third))
    bad_links = 0
    for pairs in links.values():
        local = defaultdict(set)
        for first, second in pairs:
            local[first].add(second)
            local[second].add(first)
        seen, stack = set(), [next(iter(local))]
        while stack:
            point = stack.pop()
            if point in seen:
                continue
            seen.add(point)
            stack.extend(local[point] - seen)
        bad_links += int(len(seen) != len(local) or any(len(v) != 2 for v in local.values()))
    remaining = set(graph)
    components = 0
    while remaining:
        components += 1
        stack = [next(iter(remaining))]
        while stack:
            point = stack.pop()
            if point not in remaining:
                continue
            remaining.remove(point)
            stack.extend(graph[point] & remaining)
    result = {
        "triangles": len(tri_data), "connected_components": components,
        "bad_edges": sum(value != 2 for value in edges.values()),
        "bad_winding_edges": sum(value != 0 for value in winding.values()),
        "bad_vertex_links": bad_links, "degenerate_triangles": degenerate,
        "duplicate_triangles": len(tri_data) - len({tuple(sorted(t)) for t in tri_data}),
    }
    result["watertight"] = result["bad_edges"] == 0
    result["manifold"] = result["watertight"] and result["bad_vertex_links"] == 0
    result["pass"] = not any(result[k] for k in [
        "bad_edges", "bad_winding_edges", "bad_vertex_links",
        "degenerate_triangles", "duplicate_triangles",
    ])
    return result


def _section_width(shape: cq.Workplane, x: float, z: float) -> float:
    probe = box(0.02, 40.0, 0.02, (x, 0, z))
    cut = shape.intersect(probe)
    if not cut.solids().vals():
        raise AssertionError("section probe missed solid")
    return size(cut)[1]


def actual_fit_geometry(shape: cq.Workplane, length: float, spec: dict) -> dict:
    stem_h = spec["depth_mm"] - HEAD_THICKNESS
    x = max(LEAD_IN + 1.0, length / 2)
    stem_width = _section_width(shape, x, -stem_h / 2)
    head_width = _section_width(shape, x, -stem_h - HEAD_THICKNESS / 2)
    b = bounds(shape)
    depth = -b[2]
    lead_stem = _section_width(shape, 0.01, -stem_h / 2)
    lead_head = _section_width(shape, 0.01, -stem_h - HEAD_THICKNESS / 2)
    return {
        "stem_width_mm": stem_width, "head_width_mm": head_width,
        "total_insertion_depth_mm": depth, "head_thickness_mm": HEAD_THICKNESS,
        "stem_height_mm": stem_h, "full_section_start_x_mm": LEAD_IN,
        "engagement_length_mm": length, "lead_in_length_mm": LEAD_IN,
        "lead_face_stem_width_mm": lead_stem, "lead_face_head_width_mm": lead_head,
    }


def require_fit(shape: cq.Workplane, length: float, spec: dict) -> dict:
    result = actual_fit_geometry(shape, length, spec)
    expected = [spec["stem_width_mm"], spec["head_width_mm"], spec["depth_mm"]]
    actual = [result["stem_width_mm"], result["head_width_mm"],
              result["total_insertion_depth_mm"]]
    if any(abs(a - e) > TOL for a, e in zip(actual, expected)):
        raise AssertionError(f"actual T geometry mismatch: actual={actual}, requested={expected}")
    return result


def actual_p25_working_dimension(shape: cq.Workplane) -> dict:
    # Intersect only the unmarked central datum patch Y±5, Z2..6.  The tongue,
    # top markings, and slot-fit changes cannot affect this measurement.
    patch = shape.intersect(box(P25_LENGTH + 2, 10, 4, (P25_LENGTH / 2, 0, 4)))
    faces = [face for face in patch.faces().vals()
             if face.geomType() == "PLANE" and abs(face.normalAt().x) > 0.999999
             and face.Area() > 39.999]
    if len(faces) != 2:
        raise AssertionError("two explicit P25 datum patches required")
    faces.sort(key=lambda face: face.Center().x)
    operation = BRepExtrema_DistShapeShape(faces[0].wrapped, faces[1].wrapped)
    operation.Perform()
    value = operation.Value()
    if abs(value - P25_LENGTH) > TOL:
        raise AssertionError(f"P25 datum mismatch: {value}")
    return {
        "working_dimension_mm": value,
        "datum_x_mm": [faces[0].Center().x, faces[1].Center().x],
        "measurement_patch_y_mm": [-5.0, 5.0],
        "measurement_patch_z_mm": [2.0, 6.0],
        "planar": True, "parallel": True,
    }


def clearances(letter: str) -> dict:
    spec = VARIANTS[letter]
    stem_side = (SLOT["entrance_width_mm"] - spec["stem_width_mm"]) / 2
    head_side = (SLOT["maximum_internal_width_mm"] - spec["head_width_mm"]) / 2
    bottom = SLOT["surface_to_bottom_depth_mm"] - spec["depth_mm"]
    capture = (spec["head_width_mm"] - spec["stem_width_mm"]) / 2
    return {
        "entrance_lateral_clearance_per_side_mm": stem_side,
        "internal_head_clearance_per_side_mm": head_side,
        "bottom_clearance_mm": bottom,
        "vertical_capture_overhang_per_side_mm": capture,
        "vertical_pull_through_possible_by_width": spec["head_width_mm"] <= SLOT["entrance_width_mm"],
    }


def inspect(out: Path) -> dict:
    step_report, stl_report, actual = {}, {}, {}
    for rel_path in STEPS:
        shape = cq.importers.importStep(str(out / rel_path))
        entry = {"reload": "PASS" if shape.val().isValid() else "FAIL",
                 "solids": len(shape.solids().vals()), "bounds_mm": size(shape)}
        if entry["reload"] != "PASS":
            raise AssertionError("invalid STEP " + rel_path)
        if Path(rel_path).stem in PRINT_NAMES:
            check = BOPAlgo_ArgumentAnalyzer()
            check.SetShape1(shape.val().wrapped)
            check.SelfInterMode = True
            check.Perform()
            entry["self_intersections"] = int(check.HasFaulty())
            if entry["self_intersections"]:
                raise AssertionError("self intersection " + rel_path)
        step_report[rel_path] = entry
    for rel_path in STLS:
        quality = stl_quality(out / rel_path)
        if not quality["pass"]:
            raise AssertionError("STL quality failure " + rel_path)
        quality["print_oriented_bounds_mm"] = [
            max(v[i] for tri in triangles(out / rel_path) for v in tri)
            - min(v[i] for tri in triangles(out / rel_path) for v in tri)
            for i in range(3)
        ]
        stl_report[rel_path] = quality
    for letter in VARIANTS:
        path = out / f"artifacts/2040_slide_fit_coupon_{letter}.step"
        shape = cq.importers.importStep(str(path))
        actual[letter] = require_fit(shape, COUPON_LENGTH, VARIANTS[letter])
    p25 = cq.importers.importStep(str(out / "artifacts/p25_slide_in_positioning_block_B_provisional.step"))
    actual["P25"] = {
        **require_fit(p25, P25_LENGTH, VARIANTS["B"]),
        **actual_p25_working_dimension(p25),
    }
    return {"step": step_report, "stl": stl_report, "actual_geometry": actual}


def regression() -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory(prefix="paddy_p25_slide_regression_") as folder:
        base = Path(folder)
        for letter, spec in VARIANTS.items():
            path = base / f"{letter}.step"
            export_step(coupon(letter), path)
            actual = require_fit(cq.importers.importStep(str(path)), COUPON_LENGTH, spec)
            wrong = dict(spec)
            wrong["stem_width_mm"] += 0.10
            wrong["head_width_mm"] += 0.10
            wrong["depth_mm"] += 0.10
            wrong_shape = box(COUPON_LENGTH, COUPON_BODY_WIDTH, COUPON_BODY_HEIGHT,
                              (COUPON_LENGTH / 2, 0, COUPON_BODY_HEIGHT / 2)).union(
                                  tongue(wrong, COUPON_LENGTH)).clean()
            wrong_path = base / f"{letter}_plus010.step"
            export_step(wrong_shape, wrong_path)
            rejected = False
            try:
                require_fit(cq.importers.importStep(str(wrong_path)), COUPON_LENGTH, spec)
            except AssertionError:
                rejected = True
            if not rejected:
                raise AssertionError("systematic +0.10 mm drift was not rejected")
            results.append({"candidate": letter, "actual": actual,
                            "systematic_plus_0p10_mm_rejected": rejected})
    return results


def _svg_shell(title: str, body: str, notes: list[str]) -> str:
    text = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
    text += '<rect width="1200" height="800" fill="#f7fafc"/><style>text{font-family:Arial,sans-serif;fill:#163247}.shape{fill:#d8e9f1;stroke:#176b87;stroke-width:3}.ref{fill:none;stroke:#65798a;stroke-width:3}.dim{stroke:#d3661f;stroke-width:2;fill:none}.hold{fill:#a24318}</style>'
    text += f'<text x="30" y="45" font-size="27">{title}</text>{body}'
    for index, line in enumerate(notes):
        text += f'<text x="30" y="{650 + 30 * index}" font-size="17">{line}</text>'
    return text + '<text x="30" y="782" font-size="14">P25 SLIDE-IN V002 | PETG POSITIONING GAUGE | STRUCTURAL LOAD AUTHORITY PENDING</text></svg>'


def _section_svg(letter: str) -> str:
    spec = VARIANTS[letter]
    stem = spec["stem_width_mm"] * 35
    head = spec["head_width_mm"] * 35
    depth = spec["depth_mm"] * 35
    stem_h = (spec["depth_mm"] - HEAD_THICKNESS) * 35
    cx, surface = 580, 250
    body = f'<line class="ref" x1="170" y1="{surface}" x2="990" y2="{surface}"/><rect class="shape" x="{cx-245}" y="110" width="490" height="140"/>'
    body += f'<rect class="shape" x="{cx-stem/2}" y="{surface}" width="{stem}" height="{stem_h}"/><rect class="shape" x="{cx-head/2}" y="{surface+stem_h}" width="{head}" height="70"/>'
    body += f'<path class="dim" d="M {cx-head/2} {surface+depth+35} H {cx+head/2}"/><text x="{cx-85}" y="{surface+depth+65}" font-size="18">head {spec["head_width_mm"]:.1f} mm</text>'
    return _svg_shell(f"Coupon {letter} — measured T-section", body, [
        f'Stem {spec["stem_width_mm"]:.1f}; head {spec["head_width_mm"]:.1f}; depth {spec["depth_mm"]:.1f} mm.',
        f'Nominal bottom clearance {clearances(letter)["bottom_clearance_mm"]:.1f} mm; lead-in is end-only 0.4 mm.',
        'Drawing is explanatory; generated STEP is measured by the contract.',
    ])


def previews() -> dict[str, str]:
    slot_body = '<line class="ref" x1="180" y1="220" x2="1020" y2="220"/><line class="ref" x1="468" y1="220" x2="468" y2="444"/><line class="ref" x1="846" y1="220" x2="846" y2="444"/><line class="ref" x1="580" y1="220" x2="580" y2="444"/><line class="ref" x1="734" y1="220" x2="734" y2="444"/><line class="ref" x1="468" y1="444" x2="846" y2="444"/>'
    slot_body += '<text x="575" y="200" font-size="18">entrance 6.4</text><text x="555" y="480" font-size="18">internal max 10.8</text><text x="855" y="345" font-size="18">depth 6.4</text>'
    comparison = '<line class="ref" x1="150" y1="250" x2="1050" y2="250"/>'
    for index, letter in enumerate(VARIANTS):
        spec = VARIANTS[letter]
        x = 300 + index * 300
        comparison += f'<rect class="shape" x="{x-90}" y="130" width="180" height="120"/><rect class="shape" x="{x-spec["stem_width_mm"]*12}" y="250" width="{spec["stem_width_mm"]*24}" height="{(spec["depth_mm"]-2)*24}"/><rect class="shape" x="{x-spec["head_width_mm"]*12}" y="{250+(spec["depth_mm"]-2)*24}" width="{spec["head_width_mm"]*24}" height="48"/><text x="{x-70}" y="500" font-size="22">{letter}: {spec["stem_width_mm"]:.1f}/{spec["head_width_mm"]:.1f}/{spec["depth_mm"]:.1f}</text>'
    block = '<rect class="shape" x="180" y="190" width="750" height="240"/><rect class="shape" x="180" y="430" width="750" height="100"/><path class="dim" d="M 180 580 H 930"/><text x="490" y="615" font-size="22">25.000000 mm</text><text x="370" y="320" font-size="26">P25 + slide arrow, top non-datum surface</text>'
    datum = '<rect class="shape" x="225" y="180" width="750" height="240"/><line class="dim" x1="225" y1="150" x2="225" y2="500"/><line class="dim" x1="975" y1="150" x2="975" y2="500"/><path class="dim" d="M 225 540 H 975"/><text x="500" y="580" font-size="24">25.000000 mm</text><rect x="225" y="250" width="18" height="100" fill="#f59e0b"/><rect x="957" y="250" width="18" height="100" fill="#f59e0b"/>'
    return {
        "previews/slot_cross_section.svg": _svg_shell("2040 measured-constraint reference", slot_body, [
            "S1/S2/S3 are PHYSICAL_DIRECT. Lip thickness, angle and radii are not reconstructed.",
            "2040_SLOT_LIP_PROFILE = PHYSICAL_PARTIAL / REFERENCE_APPROXIMATION.",
        ]),
        "previews/coupon_A_section.svg": _section_svg("A"),
        "previews/coupon_B_section.svg": _section_svg("B"),
        "previews/coupon_C_section.svg": _section_svg("C"),
        "previews/coupon_comparison.svg": _svg_shell("Slide-fit coupon comparison", comparison, [
            "A loose → B nominal → C tight. Select the tightest that hand-slides without damage.",
            "All have 2.0 mm head thickness and 2.1 mm capture overhang per side.",
        ]),
        "previews/p25_slide_block.svg": _svg_shell("P25 provisional B slide block", block, [
            "Logical +X is slide and 25 mm working direction; B tongue extends the full 25 mm.",
            "Positioning/assembly gauge only. It does not carry belt, bearing, torque or impact load.",
        ]),
        "previews/p25_working_datum.svg": _svg_shell("P25 independent working datum", datum, [
            "Orange patches: planar X=0 and X=25, Y=-5..+5, Z=2..6 mm.",
            "Text, lead-in and T-fit geometry are outside the measured patches.",
        ]),
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
    with tempfile.TemporaryDirectory(prefix="paddy_p25_slide_reproduce_") as folder:
        out = Path(folder)
        generate(out)
        results = {path: sha(LANE / path) == sha(out / path)
                   for path in STEPS + STLS + SVGS}
    if not all(results.values()):
        raise AssertionError("reproducibility failure " + json.dumps(results))
    return {"byte_identical": results, "count": len(results),
            "pass_count": sum(results.values()), "pass": True}


def source_audit() -> dict:
    state = audit()
    parent = state["protected"][PARENT_REL]
    return {
        "parent_lane": PARENT_REL,
        "parent_class": "READ_ONLY_PHYSICAL_PLACEMENT_REFERENCE",
        "parent_tree": parent,
        "p25_selection": "CURRENT_SELECTED_CANDIDATE",
        "p25_offset_mm": 25.0,
        "physical_observations": {
            "p25_20t_to_60t_spacing_mm_approx": 25.0,
            "p25_kp000_to_60t_edge_spacing_mm_approx": 9.0,
            "p20_20t_to_60t_spacing_mm_approx": 20.0,
            "p20_kp000_to_60t_edge_spacing_mm_approx": 4.0,
            "p25_additional_spacing_vs_p20_mm_approx": 5.0,
            "60t_rotating_max_mm": [100.1, 100.2],
            "pto_axis_from_local_member_end_mm": 34.0,
            "classification": "CURRENT_PHYSICAL_RESULT_NOT_STRUCTURAL_FIELD_AUTHORITY",
        },
        "protected_source_changed_count": state["protected_source_changed_count"],
        "protected": state["protected"],
    }


def variant_records() -> list[dict]:
    records = []
    for letter, spec in VARIANTS.items():
        records.append({
            "candidate": letter,
            **spec,
            "head_thickness_mm": HEAD_THICKNESS,
            "stem_height_mm": spec["depth_mm"] - HEAD_THICKNESS,
            "coupon_engagement_length_mm": COUPON_LENGTH,
            "lead_in_length_mm": LEAD_IN,
            **clearances(letter),
            "target": "HAND_SLIDE_NOT_PRESS_FIT",
            "physical_result": "PENDING",
        })
    return records


def geometry_metrics() -> dict:
    return {
        "slot": SLOT,
        "variants": variant_records(),
        "p25": {
            "working_dimension_mm": P25_LENGTH,
            "body_mm": [P25_LENGTH, P25_BODY_WIDTH, P25_BODY_HEIGHT],
            "tongue_variant": "B_PROVISIONAL",
            "tongue_engagement_length_mm": P25_LENGTH,
            "installed_bounds_mm": size(p25_block()),
            "print_oriented_bounds_mm": size(print_oriented(p25_block())),
            "working_dimension_independent_of_fit": True,
            "datum_patch": {"y_mm": [-5, 5], "z_mm": [2, 6]},
        },
        "coupons": {
            letter: {
                "installed_bounds_mm": size(coupon(letter)),
                "print_oriented_bounds_mm": size(print_oriented(coupon(letter))),
                "volume_mm3": volume(coupon(letter)),
            } for letter in VARIANTS
        },
        "print": {
            "material": "PETG", "printer": "BAMBU_A1",
            "orientation": "INSERTION_END_FLAT_ON_PLATE_LOGICAL_X_TO_PRINT_Z",
            "critical_dimensions": "XY", "support": "OFF",
            "slicer": "HOLD_SLICER_NOT_RUN",
            "first_layer_note": "Only the 0.4 mm insertion lead-in is first-layer-adjacent; full fit starts above it.",
        },
        "combined_plate_generated": False,
        "reason": "Individual exact coupons avoid accidental joining and keep selection unambiguous.",
    }


def physical_template() -> dict:
    fields = {
        "slides_in_from_extrusion_end": None,
        "hand_force": "LIGHT/MODERATE/TOO_TIGHT",
        "vertical_pull_out": "NONE/YES",
        "side_play": "NONE/SMALL/LARGE",
        "petg_damage": "NONE/WHITENING/SHAVING/CRACK",
        "aluminum_damage": "NONE/MARK/GOUGE",
        "slides_100_mm_if_available": "PASS/FAIL/NOT_AVAILABLE",
        "result": "PASS/FAIL/PENDING",
    }
    return {
        "physical_slot_mm": {"entrance": 6.4, "internal": 10.8, "depth": 6.4},
        "coupons": {letter: dict(fields) for letter in VARIANTS},
        "selected": "A/B/C/NONE/PENDING",
        "selection_rule": "TIGHTEST_THAT_HAND_SLIDES_WITHOUT_BINDING_OR_DAMAGE_AND_WITH_ACCEPTABLE_PLAY",
        "p25_after_selection": {
            "actual_working_length_mm": None, "slides_into_2040": "PENDING",
            "can_reach_kp000_position": "PENDING", "datum_repeatability_mm": None,
            "kp000_to_60t_mm": None, "20t_to_60t_mm": None,
            "removal": "PENDING", "tool_access": "PENDING",
            "structural_load": "NOT_TESTED",
        },
    }


def documents() -> dict[str, str]:
    rows = "|Coupon|Stem|Head|Depth|Stem H|Bottom|Entrance/side|Head/side|Capture/side|\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    for record in variant_records():
        rows += (f"|{record['candidate']}|{record['stem_width_mm']:.1f}|{record['head_width_mm']:.1f}|"
                 f"{record['depth_mm']:.1f}|{record['stem_height_mm']:.1f}|{record['bottom_clearance_mm']:.1f}|"
                 f"{record['entrance_lateral_clearance_per_side_mm']:.1f}|{record['internal_head_clearance_per_side_mm']:.1f}|"
                 f"{record['vertical_capture_overhang_per_side_mm']:.1f}|\n")
    readme = f"""# P25 Slide-In Positioning Block V002

{STATUS}

## Outcome

This lane converts the selected P25 placement distance into a removable,
end-inserted T-slot positioning interface.  The two explicit P25 datum patches
remain exactly 25.000000 mm apart and do not depend on tongue width.

The controlling physical inputs are the user's direct measurements: entrance
6.4 mm, maximum internal width 10.8 mm, and surface-to-bottom depth 6.4 mm.
The complete lip section is not known.  The reference STEP contains only five
constraint markers; its marker thickness is display-only.  It is not a generic
2040 authority or a manufactured rail reconstruction.

{rows}
Coupon B supplies the provisional full P25 tongue.  Print A, then B, then C as
needed, and select the tightest candidate that still inserts from the extrusion
end and slides smoothly by hand without PETG/aluminum damage.  Never hammer,
press, lever or use pliers.  Do not push a coupon vertically through the slot.

## Print

PETG / Bambu A1.  Each printable STL is already oriented with the flat insertion
end on the plate and logical +X toward print +Z.  Critical head/stem width and
slot depth therefore lie in XY.  The end-only 0.4 mm lead-in occupies the first
0.4 mm; all later fit sections are exact and untapered.  Support OFF.  The
coupon footprint is about 14 x 10 mm and height20 mm; P25 footprint is18 x13.9
mm and height25 mm.  Add brim only if the slicer/operator requires it; keep it
off the fit section after removal.  Slicer review remains HOLD_SLICER_NOT_RUN.

Labels A/B/C and the P25/slide-arrow marks are recessed only into non-fit top
surfaces.  No text or chamfer touches the designated P25 datum patches.

## Safety / scope

This PETG tongue is a positioning and assembly gauge.  It is not responsible
for belt tension, PTO torque, KP000 load, shock or field impact.  Structural
loads require future approved metal fasteners, T-nuts, frame and support.  No
plastic set screw, snap, wedge or cam lock is present.

If B wins, the provisional P25 block may proceed to the documented physical
position test.  If A or C wins, create a new corrected artifact later; do not
silently modify V002.  Parent V001 and all protected lanes are read-only.

Run with Python 3.12.13 / CadQuery 2.8.0:

```
python -B build_p25_slide_in_positioning_v002.py --build
python -B tests/test_p25_slide_in_positioning_v002.py
python -B build_p25_slide_in_positioning_v002.py --verify
python -B build_p25_slide_in_positioning_v002.py --zip
```

COMMIT_PATHS is an inventory, not permission to stage.  Git add/commit/push were
not performed.
"""
    design = """# P25 Slide-In V002 design authority

P25_PHYSICAL_LAYOUT_SELECTION = CURRENT_SELECTED_CANDIDATE.
P25_WORKING_DIMENSION = 25.000000 mm.
PRIMARY_FUNCTION = POSITIONING / ASSEMBLY GAUGE.
STRUCTURAL_LOAD_AUTHORITY = PENDING.

Logical +X is the slide and P25 measurement direction.  The body is25 x18 x8
mm.  Its central external datum patches are X=0 and X=25, Y=-5..+5, Z=2..6.
The generated/reloaded BRep faces are planar, parallel and measured directly.
The B tongue extends25 mm; changing it cannot move either datum.

The T-section has a2 mm head and a stem of depth-minus2.  Its 2.1 mm/side head
overhang captures behind the measured6.4 mm entrance while the head remains
inside the10.8 mm internal maximum.  Positive bottom clearance prevents tongue
bottom-loading.  The first0.4 mm narrows0.3 mm per side as an insertion lead-in;
the remaining engagement has no taper.

No root fillet projects into the partially measured lip corridor.  This is a
deliberate fail-closed choice: adding an unmeasured fillet could bind at the lip.
The full-width stem-to-body union is continuous and not a thin tab.  Future
physical lip measurements may justify a non-fit-side root radius in a new lane.

The provisional body has no load-rated clamp.  Positioning, repeatability and
anti-side-shift assistance are the only claimed functions.  It cannot carry
drive torque or belt/bearing/shock load.
"""
    measurements = """# 2040 physical slot measurements

|ID|Physical value|Class|
|---|---:|---|
|S1 entrance width|6.4 mm|PHYSICAL_DIRECT|
|S2 maximum internal slot width|10.8 mm|PHYSICAL_DIRECT|
|S3 outer surface to slot bottom|6.4 mm|PHYSICAL_DIRECT|

These values control this fit study and are not replaced by catalogue/generic
2040 values.  Slot lip thickness, angle, root radius, corner radii, surface
finish and longitudinal variation remain unmeasured.

2040_SLOT_LIP_PROFILE = PHYSICAL_PARTIAL.
UNMEASURED_LIP_GEOMETRY = REFERENCE_APPROXIMATION.

The reference STEP shows internal side constraints at Y=±5.4, entrance side
constraints at Y=±3.2, and bottom at Z=-6.4.  Thin marker solids have arbitrary
display thickness outside those faces.  They must not be interpreted as the
complete aluminum cross-section.  Coupons resolve the actual usable fit.
"""
    matrix = f"""# Slide-fit variant matrix

All dimensions in mm.  Coupons are20 mm long and use an end-only0.4 mm lead-in.

{rows}
The head is wider than the entrance in every candidate, so it cannot be pulled
vertically through the measured opening.  Positive clearances do not prove fit
because lip profile, extrusion variation and FDM process error are unresolved.

Selection: the tightest coupon that hand-slides without binding, PETG whitening,
shaving/cracking, or aluminum marking/gouging, and still has acceptable play.
Nominal order is A (loose), B, C (tight).  Coupon B is provisional only.
"""
    plan = """# Physical test plan

1. Disconnect power and remove drivetrain load. Inspect the 2040 slot end for
   burrs/damage; clean loose debris without altering the extrusion.
2. Caliper-check coupon fit surfaces away from the0.4 mm lead-in. Confirm label.
3. Start with Coupon A. Insert only from the extrusion end, by hand. Never use
   hammer, pliers, clamp force, or vertical snap-in.
4. Record hand force,100 mm travel if available, rocking/side play, and vertical
   capture. Stop immediately on binding, whitening, shaving, cracking, marking
   or gouging. Slide back out by hand.
5. Repeat B and C only when the previous step is non-damaging. Select the
   tightest smooth/removable result with acceptable lateral play.
6. If B wins, measure provisional P25 actual working length at three points,
   slide it to the KP000 position, record datum repeatability,20T-to-60T and
   KP000-to-60T clearances, removal and tool access.
7. If A or C wins, stop. Create a NEW corrected P25 artifact later. Do not cut,
   sand, heat-form or silently edit V002 to make it fit.

Structural load remains NOT TESTED.  Do not tension a belt, power the PTO, load
KP000, apply shock, or use this gauge as a final structural fastener.
"""
    sheet = """# 2040 SLIDE FIT PHYSICAL TEST — blank result sheet

Measured physical slot: entrance6.4 / internal10.8 / depth6.4 mm.
Date/operator/printer/material/settings: ____

"""
    for letter in VARIANTS:
        sheet += f"""## COUPON {letter}

Slides in from extrusion end: YES / NO
Hand force: LIGHT / MODERATE / TOO_TIGHT
Vertical pull-out: NONE / YES
Side play: NONE / SMALL / LARGE
PETG damage: NONE / WHITENING / SHAVING / CRACK
Aluminum damage: NONE / MARK / GOUGE
Slides 100 mm if available: PASS / FAIL / NOT_AVAILABLE
Result: PASS / FAIL

"""
    sheet += """## Selection

SELECTED: A / B / C / NONE
Reason: ____

## P25 after coupon selection

Actual working length readings: ____ / ____ / ____ mm
Slides into 2040: PASS / FAIL
Can reach KP000 position: PASS / FAIL
25 mm datum repeatability: ____ mm
KP000-to-60T: ____ mm
20T-to-60T: ____ mm
Removal: PASS / FAIL
Tool access: PASS / FAIL
Structural load: NOT TESTED
"""
    structural = """# Structural load HOLD

STRUCTURAL_LOAD_AUTHORITY = PENDING.

Allowed claims: repeatable25 mm positioning, end-slide fit exploration,
lateral location and manual removal after physical validation.

Not released: belt tension, PTO torque, KP000/bearing support, shock, field
impact, permanent retention, powered operation, frame drilling, aluminum
machining, shaft cutting, water/mud operation or field deployment.

Future structural architecture must use approved metal fasteners/T-nuts,
aluminum frame and support.  This lane intentionally contains no printed set
screw, snap detent, wedge lock or cam lock.  Coupon fit cannot promote load
capacity.  Slicer and physical fit remain pending.
"""
    return {name: text.rstrip() + "\n" for name, text in zip(
        DOCS, [readme, design, measurements, matrix, plan, sheet, structural]
    )}


def design_parameters() -> dict:
    return {
        "version": "P25_SLIDE_IN_POSITIONING_BLOCK_V002",
        "status": STATUS,
        "classification": {
            "p25_physical_layout_selection": "CURRENT_SELECTED_CANDIDATE",
            "primary_function": "POSITIONING_ASSEMBLY_GAUGE",
            "structural_load_authority": "PENDING",
        },
        "geometry": geometry_metrics(),
        "source": source_audit(),
        "physical_fit": "PENDING",
        "powered": "NOT_APPROVED",
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def build() -> None:
    audit()
    generate(LANE)
    quality = inspect(LANE)
    drift = regression()
    reproduction = reproduce()
    for name, text in documents().items():
        (LANE / name).write_text(text, encoding="utf-8", newline="\n")
    write_json(LANE / "design_parameters.json", design_parameters())
    write_json(LANE / "source_authority_audit.json", source_audit())
    write_json(LANE / "physical_result_template.json", physical_template())
    write_json(LANE / "validation_report.json", {
        "status": "GENERATED_CONTRACT_PENDING", "quality": quality,
        "systematic_drift_regression": drift, "reproducibility": reproduction,
        "geometry": geometry_metrics(), "slot_lip_profile": "PHYSICAL_PARTIAL",
        "structural_load_authority": "PENDING",
    })
    print(json.dumps({
        "build": "GENERATED_CONTRACT_PENDING", "STEP": len(STEPS),
        "STL": len(STLS), "SVG": len(SVGS), "exact_paths": len(EXPECTED),
        "actual_geometry": quality["actual_geometry"],
        "reproducibility": reproduction,
    }, indent=2))


def finalize(contract_report: dict) -> None:
    if not contract_report["pass"]:
        raise AssertionError("contract failed")
    write_json(LANE / "contract_test_report.json", contract_report)
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
        "lane": REL, "status": STATUS, "count": len(EXPECTED),
        "exact_paths": EXPECTED, "printable_stl": STLS,
        "logical_design_steps": [f"artifacts/{name}.step" for name in PRINT_NAMES],
        "reference_steps_not_printable": [f"artifacts/{name}.step" for name in REFERENCE_NAMES],
    })
    (LANE / "COMMIT_PATHS.txt").write_text(
        "\n".join(REL + "/" + path for path in EXPECTED) + "\n",
        encoding="utf-8", newline="\n",
    )
    for name in ("repository_audit.json", "SHA256SUMS.txt"):
        if not (LANE / name).exists():
            (LANE / name).write_text("", encoding="ascii")
    write_json(LANE / "repository_audit.json", audit())
    (LANE / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(LANE / path)}  {path}\n" for path in EXPECTED
                if path != "SHA256SUMS.txt"),
        encoding="ascii", newline="\n",
    )


def verify() -> None:
    state = audit()
    files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
    if files != EXPECTED:
        raise AssertionError("exact-path contract failure")
    lines = (LANE / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
    if len(lines) != len(EXPECTED) - 1:
        raise AssertionError("SHA inventory count")
    for line in lines:
        digest, path = line.split("  ", 1)
        if sha(LANE / path) != digest:
            raise AssertionError("SHA mismatch " + path)
    contract = json.loads((LANE / "contract_test_report.json").read_text(encoding="utf-8"))
    if not contract["pass"]:
        raise AssertionError("contract report not passed")
    for name, text in documents().items():
        if (LANE / name).read_bytes() != text.encode("utf-8"):
            raise AssertionError("documentation byte drift " + name)
    quality = inspect(LANE)
    reproduction = reproduce()
    print(json.dumps({
        "verify": "PASS", "audit": state,
        "quality_count": {"step": len(quality["step"]), "stl": len(quality["stl"])},
        "actual_geometry": quality["actual_geometry"],
        "geometry_svg_reproduction": reproduction,
        "documentation_reproduction": len(DOCS),
    }, indent=2))


def handoff() -> None:
    verify()
    target = Path(r"D:\Downloads") / (
        "Paddy_Swarm_P25_SLIDE_IN_POSITIONING_V002_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
    )
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in EXPECTED:
            archive.write(LANE / path, LANE.name + "/" + path)
    with zipfile.ZipFile(target) as archive:
        expected_names = sorted(LANE.name + "/" + path for path in EXPECTED)
        if archive.testzip() is not None or sorted(archive.namelist()) != expected_names:
            raise AssertionError("ZIP manifest failure")
        for path in EXPECTED:
            member = LANE.name + "/" + path
            if hashlib.sha256(archive.read(member)).hexdigest() != sha(LANE / path):
                raise AssertionError("ZIP byte mismatch " + path)
    print(json.dumps({"zip": str(target), "sha256": sha(target),
                      "members": len(EXPECTED)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if args.build:
        build()
    elif args.verify:
        verify()
    else:
        handoff()
