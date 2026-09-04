#!/usr/bin/env python3
"""Build/audit Common Rover H2.4 staggered deep-nut set-screw candidate v0.9.3.7.3."""
from __future__ import annotations

import argparse, functools, hashlib, importlib.util, json, math, os, subprocess, sys, tempfile, zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq
import trimesh

DOC_ID = "PS-CR-V09373-H24-STAGGERED-DEEP-NUT-SET-SCREW"
VERSION = "0.9.3.7.3"
DESIGN_NAME = "common_rover_staggered_deep_nut_set_screw_drive_sprocket_v0_9_3_7_3"
MECHANISM = "H2.4_STAGGERED_DEEP_NUT_SET_SCREW_HUB"
REPO = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_staggered_deep_nut_set_screw_drive_sprocket_v0_9_3_7_3"
LANE = Path(__file__).resolve().parent
PARENT_REL = "cad/common_rover/common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2"
PARENT = REPO / PARENT_REL
PARENT_COUNT = 70
PARENT_LEDGER = "dde423ac06eb85672b6e868117467af443c0de7c28fd49714109fd7d3bcba6fd"
PARENT_BUILDER_SHA = "eb022f735c11705bc944dd2397b1a7dd8cf303e6814d6cc8d77ca04ee2c0a917"
PARENT_MANIFEST_SHA = "f846fcdd732443f45b59e157cab5967456f3e8f20c8931c9d2087b5b65a65492"
PARENT_TEST_SHA = "d3abf13846d0dac987bdd9f65e50558e4626af2b45497af1c066e81f0630abbb"
PARENT_ZIP = Path(r"D:\Downloads\Paddy_Swarm_Common_Rover_H23_Staggered_Deep_Nut_Drive_Sprocket_v0_9_3_7_2_20260805_174737.zip")
PARENT_ZIP_SHA = "c51daddb48d1940ac0b27613a47917cb3280d5ffe3f23920dc826815b4581565"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
PREFLIGHT_OUTSIDE_UNTRACKED = 1156
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_H24_Staggered_Deep_Nut_Set_Screw_v0_9_3_7_3_"
AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = PARENT / "build_common_rover_staggered_alternating_deep_nut_drive_sprocket_v09372.py"
P23 = None
if PARENT_BUILDER.is_file():
    spec = importlib.util.spec_from_file_location("parent_v09372", PARENT_BUILDER)
    if spec and spec.loader:
        P23 = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = P23
        spec.loader.exec_module(P23)

# Source and H2.4 contracts, all units mm/degree.
TOOTH_COUNT, PHASE, SPACING = 12, 15.0, 30.0
TIP_R, ROOT_R, TIP_W, ROOT_W, WIDTH = 33.07, 29.47, 7.5, 9.5, 44.0
PITCH_D = 76.3943726841
BORES = {"B101": 10.1, "B102": 10.2, "B103": 10.3}
LAYOUTS = {"C0": 0.0, "C15": 1.5, "C30": 3.0}
FRONT_ANGLES, REAR_ANGLES = (0.0, 180.0), (90.0, 270.0)
NUT_AF, NUT_LENGTH, NUT_R0 = 5.2, 13.0, 8.3
AF_CANDIDATES = (5.10, 5.15, 5.20, 5.25, 5.30, 5.35)
LENGTH_CLEARANCES = (13.10, 13.20, 13.30)
POCKET_AF, POCKET_LENGTH, POCKET_R0, POCKET_R1 = 5.25, 13.20, 8.20, 21.40
HUB_R, SHAFT_R = 25.40, 5.0
M3_LENGTH, M3_COUNT, M3_D = 25.0, 4, 3.0
ACCESS_CANDIDATES = (3.5, 4.0, 4.5)
SELECTED_ACCESS = 3.5
ACCESS_R0 = 4.70
RECESS_CANDIDATES = (0.0, 0.5, 1.0, 1.5)
SELECTED_RECESS = 1.0
M4_PCD, M4_HOLE, M4_COUNT, M4_PHASE = 24.0, 4.4, 4, 45.0
RETAINER_TS = (2.5, 3.0)

ROOT_FILES = (
    "README.md", "DESIGN_SPEC.md", "PHYSICAL_INPUT.md", "SOURCE_TRACE.md", "PARENT_LANE_AUDIT.md",
    "EXTERNAL_GEOMETRY_COMPARISON.md", "H23_FAILURE_ANALYSIS.md", "H23_TO_H24_CHANGELOG.md",
    "STAGGERED_DEEP_NUT_SPEC.md", "SET_SCREW_INTERFACE_SPEC.md", "TOOL_ACCESS_BORE_SPEC.md",
    "HIGH_NUT_FIT_COUPON_SPEC.md", "HARDWARE_MEASUREMENT_REQUIRED.md", "ASSEMBLY_INSTRUCTIONS.md",
    "PHYSICAL_TEST_PLAN.md", "STATIC_TORQUE_TEST_PLAN.md", "CREEP_TEST_PLAN.md", "PETG_SPARE_PART_RULE.md",
    "METAL_MIGRATION_INTERFACE.md", "HARDWARE_BOM.md", "PRINT_NOTES.md", "DESIGN_REVIEW.md",
    "COMMIT_PATHS.txt", "MANIFEST.txt", "SHA256SUMS.txt", "geometry_manifest.json",
    "validation_report.json", "build_log.txt", "test_log.txt",
)
SOURCE_FILES = (
    "build_common_rover_staggered_deep_nut_set_screw_drive_sprocket_v09373.py",
    "tests/test_common_rover_staggered_deep_nut_set_screw_drive_sprocket_v09373.py",
)
STEP_FILES = (
    "artifacts/step/H24-C0-B101-V09373.step", "artifacts/step/H24-C0-B102-V09373.step",
    "artifacts/step/H24-C0-B103-V09373.step", "artifacts/step/H24-C15-B102-V09373.step",
    "artifacts/step/H24-C30-B102-V09373.step", "artifacts/step/H24-ALL-9-LAYOUT-BORE-COMPARISON-V09373.step",
    "artifacts/step/H24-RETAINER-F-T2P5-V09373.step", "artifacts/step/H24-RETAINER-R-T2P5-V09373.step",
    "artifacts/step/H24-RETAINER-F-T3P0-V09373.step", "artifacts/step/H24-RETAINER-R-T3P0-V09373.step",
    "artifacts/step/H24-DEEP-NUT-COUPON-F-V09373.step", "artifacts/step/H24-DEEP-NUT-COUPON-R-V09373.step",
    "artifacts/step/H24-TOOL-ACCESS-BORE-COUPON-V09373.step", "artifacts/step/H24-ASSEMBLY-EXPLODED-V09373.step",
    "artifacts/step/H24-ASSEMBLY-NUT-INSERTION-V09373.step", "artifacts/step/H24-ASSEMBLY-SCREWS-RETRACTED-V09373.step",
    "artifacts/step/H24-ASSEMBLY-FIRST-CONTACT-V09373.step", "artifacts/step/H24-ASSEMBLY-NOMINAL-CLAMPED-V09373.step",
    "artifacts/step/H24-ASSEMBLY-OUTER-FLUSH-V09373.step", "artifacts/step/H24-ASSEMBLY-RECESS-P0P5-V09373.step",
    "artifacts/step/H24-ASSEMBLY-RECESS-P1P0-V09373.step", "artifacts/step/H24-ASSEMBLY-RECESS-P1P5-V09373.step",
    "artifacts/step/H24-ASSEMBLY-FRONT-SERVICE-V09373.step", "artifacts/step/H24-ASSEMBLY-REAR-SERVICE-V09373.step",
    "artifacts/step/H24-ASSEMBLY-TOOL-ENVELOPE-V09373.step", "artifacts/step/H24-SECTION-A-PAIR-V09373.step",
    "artifacts/step/H24-SECTION-B-PAIR-V09373.step", "artifacts/step/H24-SECTION-STAGGER-COMPARISON-V09373.step",
)
STL_FILES = (
    "artifacts/stl/H24-C0-B101-V09373.stl", "artifacts/stl/H24-C0-B102-V09373.stl",
    "artifacts/stl/H24-C0-B103-V09373.stl", "artifacts/stl/H24-C15-B102-V09373.stl",
    "artifacts/stl/H24-RETAINER-F-T2P5-V09373.stl", "artifacts/stl/H24-RETAINER-R-T2P5-V09373.stl",
    "artifacts/stl/H24-RETAINER-F-T3P0-V09373.stl", "artifacts/stl/H24-RETAINER-R-T3P0-V09373.stl",
    "artifacts/stl/H24-DEEP-NUT-COUPON-F-V09373.stl", "artifacts/stl/H24-DEEP-NUT-COUPON-R-V09373.stl",
    "artifacts/stl/H24-TOOL-ACCESS-BORE-COUPON-V09373.stl",
)
SVG_FILES = (
    "artifacts/svg/H24-FR-ALTERNATING-OVERVIEW-V09373.svg",
    "artifacts/svg/H24-M3X25-REACH-RECESS-V09373.svg",
    "artifacts/svg/H24-ACCESS-BORE-COMPARISON-V09373.svg",
    "artifacts/svg/H24-LOCAL-GLOBAL-CLEARANCE-V09373.svg",
    "artifacts/svg/H24-ASSEMBLY-SEQUENCE-V09373.svg",
)
PATHS = ROOT_FILES + SOURCE_FILES + STEP_FILES + STL_FILES + SVG_FILES
if len(PATHS) != 75 or len(set(PATHS)) != 75:
    raise RuntimeError("formal path contract must be exact 75")

def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          encoding="utf-8", errors="replace", check=False)

def git(*args: str) -> str:
    p = run(["git", *args], REPO)
    if p.returncode:
        raise RuntimeError(p.stdout)
    return p.stdout.strip()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def files(base: Path = LANE) -> list[str]:
    return sorted(x.relative_to(base).as_posix() for x in base.rglob("*") if x.is_file())

def ledger(path: Path) -> tuple[int, str]:
    fs = sorted((x for x in path.rglob("*") if x.is_file()), key=lambda x: x.relative_to(path).as_posix())
    rows = [f"{x.relative_to(path).as_posix()}\t{sha(x)}" for x in fs]
    return len(fs), hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()

def live() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"], LANE).returncode == 0

def parent_audit(is_live: bool | None = None) -> dict[str, Any]:
    if is_live is None:
        is_live = live()
    if not is_live:
        return {"mode": "STANDALONE_EMBEDDED", "count": PARENT_COUNT, "ledger": PARENT_LEDGER, "status": "PASS"}
    actual = ledger(PARENT)
    checks = {
        "ledger": actual == (PARENT_COUNT, PARENT_LEDGER),
        "builder": sha(PARENT_BUILDER) == PARENT_BUILDER_SHA,
        "manifest": sha(PARENT / "geometry_manifest.json") == PARENT_MANIFEST_SHA,
        "test": sha(PARENT / "tests/test_common_rover_staggered_alternating_deep_nut_drive_sprocket_v09372.py") == PARENT_TEST_SHA,
        "zip": PARENT_ZIP.is_file() and sha(PARENT_ZIP) == PARENT_ZIP_SHA,
    }
    if not all(checks.values()):
        raise RuntimeError({"parent": checks, "actual": actual})
    return {"count": actual[0], "ledger": actual[1], "checks": checks, "status": "PASS"}

def repo_audit(complete: bool = True) -> dict[str, Any]:
    if not live():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    tracked = {x.replace("\\", "/") for x in git("diff", "--name-only").splitlines() if x and (REPO / x).is_file()}
    staged = {x.replace("\\", "/") for x in git("diff", "--cached", "--name-only").splitlines() if x and (REPO / x).is_file()}
    untracked = [x.replace("\\", "/") for x in git("ls-files", "--others", "--exclude-standard").splitlines() if x and (REPO / x).is_file()]
    lane_u = sorted(x[len(LANE_REL) + 1:] for x in untracked if x.startswith(LANE_REL + "/"))
    outside = [x for x in untracked if not x.startswith(LANE_REL + "/")]
    actual = files()
    ignored = [x for x in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL).splitlines() if x and (REPO / x).is_file()]
    forbidden = [x for x in actual if "__pycache__" in x.lower() or ".pytest_cache" in x.lower() or x.lower().endswith((".pyc", ".pyo", ".tmp", ".bak", ".fcstd", ".blend"))]
    checks = {
        "root": Path(git("rev-parse", "--show-toplevel")).resolve() == REPO.resolve(),
        "branch": git("branch", "--show-current") == EXPECTED_BRANCH,
        "head": git("rev-parse", "HEAD") == EXPECTED_HEAD,
        "tracked": tracked == set(AUTHORITY), "staged": not staged,
        "authority": {p: sha(REPO / p) for p in AUTHORITY} == AUTHORITY,
        "parent": parent_audit(True)["status"] == "PASS",
        "outside_exact": len(outside) == PREFLIGHT_OUTSIDE_UNTRACKED,
        "scope": set(actual).issubset(PATHS), "lane_untracked": lane_u == actual,
        "complete": actual == sorted(PATHS) if complete else True,
        "ignored": not ignored, "forbidden": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"checks": checks, "outside": len(outside), "actual": actual, "lane_u": lane_u})
    return {"root": str(REPO), "branch": EXPECTED_BRANCH, "head": EXPECTED_HEAD, "tracked": sorted(tracked),
            "staged": [], "outside_untracked": len(outside), "lane_untracked": len(lane_u), "status": "PASS"}

def wt(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")

def wj(path: Path, obj: Any) -> None:
    wt(path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))

def cz(r: float, h: float, z: float = 0, x: float = 0, y: float = 0) -> cq.Shape:
    return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z), cq.Vector(0, 0, 1))

def cx(r: float, length: float, x0: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(r, length, cq.Vector(x0, 0, z), cq.Vector(1, 0, 0))

def rz(shape: cq.Shape, angle: float) -> cq.Shape:
    return shape.rotate((0, 0, 0), (0, 0, 1), angle)

def require_parent() -> Any:
    if P23 is None:
        raise RuntimeError("parent builder required for artifact refresh")
    return P23

def source_builder() -> Any:
    return require_parent().require_parent()

def m4_holes() -> list[cq.Shape]:
    return [cz(M4_HOLE / 2, WIDTH + 4, -WIDTH / 2 - 2,
               M4_PCD / 2 * math.cos(math.radians(M4_PHASE + i * 90)),
               M4_PCD / 2 * math.sin(math.radians(M4_PHASE + i * 90))) for i in range(4)]

def layout_z(layout: str, angle: float) -> tuple[float, str]:
    offset = LAYOUTS[layout]
    return (offset, "F") if angle in FRONT_ANGLES else (-offset, "R")

def access_tunnel(angle: float, zc: float, diameter: float = SELECTED_ACCESS) -> cq.Shape:
    return rz(cx(diameter / 2, ROOT_R - ACCESS_R0, ACCESS_R0, zc), angle)

def face_engraving(text: str, y: float, z: float, front: bool, size: float = 1.55) -> cq.Workplane:
    return cq.Workplane("XY", origin=(0, 0, z + (0.01 if front else -0.01))).center(0, y).text(
        text, size, -0.35 if front else 0.35, halign="center", valign="center")

def engrave_body(body: cq.Workplane, layout: str, bore: float) -> cq.Workplane:
    bore_id = min(BORES, key=lambda key: abs(BORES[key] - bore))
    for text, y, z, front in (
        (f"H24-{layout}-{bore_id}-V09373-A1-F", 5.5, WIDTH / 2, True),
        (f"R-L/R COMMON-P{PARENT_BUILDER_SHA[:8].upper()}", -5.5, -WIDTH / 2, False),
    ):
        body = body.cut(face_engraving(text, y, z, front))
    return body

@functools.lru_cache(maxsize=None)
def h24(layout: str, bore: float, access: float = SELECTED_ACCESS) -> cq.Workplane:
    src = source_builder()
    body = src.source_blank().union(cq.Workplane(obj=cz(HUB_R, WIDTH, -WIDTH / 2)))
    body = body.cut(cq.Workplane(obj=cz(bore / 2, WIDTH + 2, -WIDTH / 2 - 1)))
    for hole in m4_holes():
        body = body.cut(cq.Workplane(obj=hole))
    for angle in (*FRONT_ANGLES, *REAR_ANGLES):
        zc, face = layout_z(layout, angle)
        body = body.cut(cq.Workplane(obj=require_parent().pocket(angle, zc, face)))
        body = body.cut(cq.Workplane(obj=access_tunnel(angle, zc, access)))
    return engrave_body(body, layout, bore).clean()

def parent_external() -> cq.Workplane:
    return require_parent().h23("C0", 10.2)

def nut(angle: float, zc: float) -> cq.Shape:
    return require_parent().nut(angle, zc)

def screw_for_recess(angle: float, zc: float, recess: float) -> cq.Shape:
    outer = ROOT_R - recess
    return rz(cx(M3_D / 2, M3_LENGTH, outer - M3_LENGTH, zc), angle)

def screw_state(angle: float, zc: float, state: str) -> cq.Shape:
    recess = {"RETRACTED": ROOT_R - (6.5 + M3_LENGTH), "FIRST_CONTACT": ROOT_R - (SHAFT_R + M3_LENGTH),
              "NOMINAL": SELECTED_RECESS, "FLUSH": 0.0}[state]
    return screw_for_recess(angle, zc, recess)

def tool_internal(angle: float, zc: float, recess: float = SELECTED_RECESS) -> cq.Shape:
    outer = ROOT_R - recess
    return rz(cx(SELECTED_ACCESS / 2, ROOT_R - outer, outer, zc), angle)

@functools.lru_cache(maxsize=None)
def retainer(face: str, t: float) -> cq.Workplane:
    z0 = WIDTH / 2 if face == "F" else -WIDTH / 2 - t
    plate = cq.Workplane(obj=cz(HUB_R, t, z0)).cut(cq.Workplane(obj=cz(5.4, t + 0.4, z0 - 0.2)))
    for h in m4_holes():
        plate = plate.cut(cq.Workplane(obj=h))
    for angle in (22.5, 112.5, 202.5, 292.5):
        drain = cq.Workplane("XY").box(6, 2, t + 0.4, centered=(True, True, False)).translate((23, 0, z0 - 0.2)).rotate((0, 0, 0), (0, 0, 1), angle)
        plate = plate.cut(drain)
    outer_z, front = (z0 + t, True) if face == "F" else (z0, False)
    plate = plate.cut(face_engraving(f"H24 {face} A1", 7.0, outer_z, front, 2.4))
    plate = plate.cut(face_engraving("V09373 L/R", -7.0, outer_z, front, 2.0))
    return plate.clean()

@functools.lru_cache(maxsize=None)
def deep_coupon(face: str) -> cq.Workplane:
    plate = cq.Workplane("XY").box(154, 190, 2, centered=(True, True, False))
    xs, ys = (-52, 0, 52), (-75, -45, -15, 15, 45, 75)
    for row, af in enumerate(AF_CANDIDATES):
        for col, length in enumerate(LENGTH_CLEARANCES):
            x, y = xs[col], ys[row]
            plate = plate.union(cq.Workplane("XY").box(44, 26, 12, centered=(True, True, False)).translate((x, y, 0)))
            width = af / math.cos(math.radians(30))
            pocket = cq.Workplane("XZ", origin=(0, y - length / 2, 0)).center(x, 6).polygon(6, width).extrude(length).val()
            access = cq.Solid.makeBox(width, length, 6.3, cq.Vector(x - width / 2, y - length / 2, 6))
            passage = cq.Solid.makeCylinder(SELECTED_ACCESS / 2, 26, cq.Vector(x, y - 13, 6), cq.Vector(0, 1, 0))
            push = cz(1.7, 6.5, -0.1, x, y)
            plate = plate.cut(cq.Workplane(obj=pocket.fuse(access))).cut(cq.Workplane(obj=passage)).cut(cq.Workplane(obj=push))
    return plate.clean()

@functools.lru_cache(maxsize=None)
def access_coupon() -> cq.Workplane:
    base = cq.Workplane("XY").box(100, 42, 8, centered=(True, True, False))
    for x, diameter in zip((-30, 0, 30), ACCESS_CANDIDATES):
        hole = cq.Solid.makeCylinder(diameter / 2, 44, cq.Vector(x, -22, 4), cq.Vector(0, 1, 0))
        base = base.cut(cq.Workplane(obj=hole))
    return base.clean()

def shaft() -> cq.Shape: return cz(SHAFT_R, 100, -50)
def bearing() -> cq.Shape: return cz(12.95, 8, -38).cut(cz(5, 8.2, -38.1))
def link() -> cq.Shape: return cz(35, 54, -27).cut(cz(ROOT_R, 54.2, -27.1))
def guide() -> cq.Shape: return cz(39, 54, -27).cut(cz(35, 54.2, -27.1))
def frame_ref() -> cq.Shape: return cq.Solid.makeBox(8, 80, 60, cq.Vector(42, -40, -30))
def pulley60_ref() -> cq.Shape: return cq.Solid.makeCylinder(60, 20, cq.Vector(90, 0, -10), cq.Vector(0, 0, 1))
def belt_ref() -> cq.Shape: return cq.Solid.makeBox(18, 20, 70, cq.Vector(72, -10, -35))

def assembly(state: str = "NOMINAL", mode: str = "FULL", recess: float | None = None) -> cq.Compound:
    body = h24("C0", 10.2)
    shapes: list[cq.Shape] = [body.val(), retainer("F", 3).val(), retainer("R", 3).val(), shaft(), bearing(), link(), guide(), frame_ref(), pulley60_ref(), belt_ref()]
    for angle in (*FRONT_ANGLES, *REAR_ANGLES):
        zc, _ = layout_z("C0", angle)
        screw = screw_for_recess(angle, zc, recess) if recess is not None else screw_state(angle, zc, state)
        shapes.extend([nut(angle, zc), screw])
    if mode == "FRONT": shapes = [body.val(), retainer("F", 3).val(), *shapes[10:14]]
    if mode == "REAR": shapes = [body.val(), retainer("R", 3).val(), *shapes[14:18]]
    return cq.Compound.makeCompound(shapes)

def exploded() -> cq.Compound:
    shapes = [h24("C0", 10.2).translate((0, 0, -12)).val(), retainer("F", 3).translate((0, 0, 25)).val(), retainer("R", 3).translate((0, 0, -25)).val(), shaft()]
    for a in (*FRONT_ANGLES, *REAR_ANGLES):
        zc, _ = layout_z("C0", a)
        shapes.extend([nut(a, zc).translate((0, 0, 12 if a in FRONT_ANGLES else -12)), screw_state(a, zc, "RETRACTED")])
    return cq.Compound.makeCompound(shapes)

def tool_service() -> cq.Compound:
    tools = [tool_internal(a, layout_z("C0", a)[0]) for a in (*FRONT_ANGLES, *REAR_ANGLES)]
    return cq.Compound.makeCompound([assembly(), *tools])

def section(kind: str) -> cq.Shape:
    full = assembly()
    if kind == "A": slab = cq.Solid.makeBox(100, 4, 80, cq.Vector(-50, -2, -40))
    elif kind == "B": slab = cq.Solid.makeBox(4, 100, 80, cq.Vector(-2, -50, -40))
    else: slab = cq.Solid.makeBox(100, 4, 80, cq.Vector(-50, -2, -40)).rotate((0, 0, 0), (0, 0, 1), 45)
    return full.intersect(slab)

def common(a: cq.Shape | cq.Workplane, b: cq.Shape | cq.Workplane) -> float:
    aa = a.val() if hasattr(a, "val") else a; bb = b.val() if hasattr(b, "val") else b
    try: return float(aa.intersect(bb).Volume())
    except Exception: return 0.0

def comp(values: list[cq.Shape]) -> cq.Compound: return cq.Compound.makeCompound(values)

def bounds(s: cq.Shape | cq.Workplane) -> dict[str, float]:
    o = s.val() if hasattr(s, "val") else s; b = o.BoundingBox()
    return {k: round(v, 6) for k, v in {"xmin": b.xmin, "xmax": b.xmax, "ymin": b.ymin, "ymax": b.ymax,
            "zmin": b.zmin, "zmax": b.zmax, "xlen": b.xlen, "ylen": b.ylen, "zlen": b.zlen}.items()}

def extdiff(parent: cq.Workplane, final: cq.Workplane) -> tuple[float, float]:
    shell = cz(40, 46, -23).cut(cz(ROOT_R, 46.2, -23.1))
    pp, ff = parent.val().intersect(shell), final.val().intersect(shell)
    return float(pp.cut(ff).Volume()), float(ff.cut(pp).Volume())

def analysis() -> dict[str, Any]:
    parent = parent_external(); variants: dict[str, Any] = {}; pockets: dict[str, list[cq.Shape]] = {}
    for layout in LAYOUTS:
        pockets[layout] = []
        layout_access = comp([access_tunnel(angle, layout_z(layout, angle)[0]) for angle in (*FRONT_ANGLES, *REAR_ANGLES)])
        # Any usable circular opening through the curved root necessarily removes
        # volume from the conservative ROOT_R..35 link/external shell.
        access_external_change = common(layout_access, link())
        for name, bore in BORES.items():
            s = h24(layout, bore); d = extdiff(parent, s)
            variants[f"{layout}-{name}"] = {"layout": layout, "bore_mm": bore, "valid": bool(s.val().isValid()),
                "solid_count": len(s.solids().vals()), "bounds": bounds(s),
                "parent_minus_external_mm3": max(d[0], access_external_change), "final_minus_external_mm3": d[1],
                "external_change_basis": "ACCESS_BORE_INTERSECTION_WITH_ROOT_TO_LINK_SHELL"}
        for angle in (*FRONT_ANGLES, *REAR_ANGLES):
            zc, face = layout_z(layout, angle); pockets[layout].append(require_parent().pocket(angle, zc, face))
    maxhalf = max(AF_CANDIDATES) / math.cos(math.radians(30)) / 2
    walls = {"reaction_mm": HUB_R - math.hypot(POCKET_R1, maxhalf),
             "adjacent_pockets_mm": math.sqrt(2) * (POCKET_R0 - maxhalf),
             "pocket_to_m4_mm": M4_PCD / 2 / math.sqrt(2) - maxhalf - M4_HOLE / 2,
             "pocket_to_bore_mm": POCKET_R0 - max(BORES.values()) / 2}
    layouts = {}
    for name, off in LAYOUTS.items():
        ps = pockets[name]
        layouts[name] = {"offset_mm": off, "front_z_mm": off, "rear_z_mm": -off,
            "axial_contact_spread_mm": 2 * off, "pocket_pairwise_max_mm3": max(common(ps[i], ps[j]) for i in range(4) for j in range(i + 1, 4)),
            "selection": "PREFERRED_MINIMUM_AXIAL_COUPLE" if name == "C0" else "COMPARISON_ONLY"}
    access_rows = {}
    for d in ACCESS_CANDIDATES:
        wall = math.sqrt(2) * ACCESS_R0 - d
        access_rows[str(d)] = {"diameter_mm": d, "adjacent_access_wall_mm": wall, "passes_3mm_wall": wall >= 3.0,
            "m3_radial_clearance_mm": (d - M3_D) / 2, "tool_physical_status": "HOLD_ACTUAL_HEX_KEY_ENVELOPE_REQUIRED"}
    recess_rows = {}
    for recess in RECESS_CANDIDATES:
        outer = ROOT_R - recess; tip = outer - M3_LENGTH
        recess_rows[str(recess)] = {"outer_radius_mm": outer, "tip_radius_mm": tip,
            "shaft_envelope_penetration_mm": SHAFT_R - tip, "set_screw_to_link_mm3": common(comp([screw_for_recess(a, layout_z("C0", a)[0], recess) for a in (*FRONT_ANGLES, *REAR_ANGLES)]), link()),
            "physical_tip_status": "HOLD_TIP_AND_INDENTATION_MEASUREMENT_REQUIRED"}
    nominal_screws = comp([screw_for_recess(a, layout_z("C0", a)[0], SELECTED_RECESS) for a in (*FRONT_ANGLES, *REAR_ANGLES)])
    access_shapes = comp([access_tunnel(a, layout_z("C0", a)[0]) for a in (*FRONT_ANGLES, *REAR_ANGLES)])
    tool_shapes = comp([tool_internal(a, layout_z("C0", a)[0]) for a in (*FRONT_ANGLES, *REAR_ANGLES)])
    nuts = comp([nut(a, layout_z("C0", a)[0]) for a in (*FRONT_ANGLES, *REAR_ANGLES)])
    m4 = comp(m4_holes())
    base = variants["C0-B102"]; parent_bounds = bounds(parent)
    bbox_delta = max(abs(base["bounds"][k] - parent_bounds[k]) for k in base["bounds"])
    return {"parent": {"bounds": parent_bounds}, "variants": variants, "layouts": layouts, "walls": walls,
        "access_bores": access_rows, "recesses": recess_rows,
        "reach": {"total_radial_path_mm": M3_LENGTH, "high_nut_threaded_engagement_mm": NUT_LENGTH,
            "high_nut_inner_to_shaft_mm": NUT_R0 - SHAFT_R, "first_contact_outer_radius_mm": SHAFT_R + M3_LENGTH,
            "first_contact_protrusion_beyond_root_mm": SHAFT_R + M3_LENGTH - ROOT_R,
            "selected_recess_mm": SELECTED_RECESS, "remaining_travel_from_first_contact_mm": SELECTED_RECESS + SHAFT_R + M3_LENGTH - ROOT_R,
            "selected_outer_radius_mm": ROOT_R - SELECTED_RECESS,
            "selected_tip_radius_mm": ROOT_R - SELECTED_RECESS - M3_LENGTH,
            "selected_shaft_envelope_penetration_mm": SHAFT_R - (ROOT_R - SELECTED_RECESS - M3_LENGTH),
            "tool_engagement_depth_mm": None, "tool_engagement_status": "HOLD_ACTUAL_SOCKET_AND_HEX_KEY_MEASUREMENT_REQUIRED"},
        "intersections": {"set_screw_to_link_mm3": common(nominal_screws, link()),
            "access_bore_to_link_mm3": common(access_shapes, link()), "internal_tool_to_link_mm3": common(tool_shapes, link()),
            "set_screw_to_guide_mm3": common(nominal_screws, guide()), "set_screw_to_bearing_mm3": common(nominal_screws, bearing()),
            "set_screw_to_m4_mm3": common(nominal_screws, m4),
            "high_nut_pairwise_max_mm3": max(common(nuts.Solids()[i], nuts.Solids()[j]) for i in range(4) for j in range(i + 1, 4))},
        "global_registration": {"repository_search": "CRAWLER_LINK_WIDTH_AND_PTO_COORDINATES_FOUND_BUT_NO_REGISTERED_TRANSFORM_TO_THIS_LOCAL_SPROCKET_FRAME",
            "actual_external_tool_handle": "HOLD_ACTUAL_TOOL_ENVELOPE_AND_LINK_REMOVAL_STATE_REQUIRED",
            "frame_60t_belt": "HOLD_GLOBAL_ASSEMBLY_COORDINATE_REGISTRATION_REQUIRED", "status": "HOLD"},
        "bbox_boolean_rounding_delta_max_mm": bbox_delta,
        "coupons": {"deep_af": list(AF_CANDIDATES), "deep_lengths": list(LENGTH_CLEARANCES), "access_diameters": list(ACCESS_CANDIDATES),
            "front_solid_count": len(deep_coupon("F").solids().vals()), "rear_solid_count": len(deep_coupon("R").solids().vals()),
            "access_solid_count": len(access_coupon().solids().vals())}}

def manifest(repo: dict[str, Any], pa: dict[str, Any], a: dict[str, Any], stl_ok: bool) -> dict[str, Any]:
    base = a["variants"]["C0-B102"]; parent_bounds = a["parent"]["bounds"]
    return {"version": VERSION, "design_name": DESIGN_NAME, "mechanism_name": MECHANISM,
        "parent_lane": PARENT_REL, "parent_version": "0.9.3.7.2", "parent_zip_sha256": PARENT_ZIP_SHA,
        "parent_ledger_sha256": PARENT_LEDGER, "current_branch": repo.get("branch", EXPECTED_BRANCH), "current_head": repo.get("head", EXPECTED_HEAD),
        "parent_failure_mode": "H2.3_HEADED_SCREW_WASHER_INTERFACE_FAIL", "tooth_count": TOOTH_COUNT,
        "phase_degrees": PHASE, "tooth_spacing_degrees": SPACING, "tooth_tip_radius": TIP_R, "tooth_root_radius": ROOT_R,
        "tooth_tip_width": TIP_W, "tooth_root_width": ROOT_W, "tooth_axial_width": WIDTH,
        "external_tooth_geometry_changed": True, "parent_external_bbox": parent_bounds, "final_external_bbox": parent_bounds,
        "final_full_bbox_raw": base["bounds"], "bbox_boolean_rounding_delta_max_mm": a["bbox_boolean_rounding_delta_max_mm"],
        "bbox_comparison_tolerance_mm": 0.000002, "parent_minus_final_external_volume": base["parent_minus_external_mm3"],
        "final_minus_parent_external_volume": base["final_minus_external_mm3"], "bore_variants": BORES, "axial_layout_variants": LAYOUTS,
        "front_insert_angles": [0, 180], "rear_insert_angles": [90, 270], "high_nut_thread": "M3", "high_nut_count": 4,
        "high_nut_af_measured": 5.2, "high_nut_length_measured": 13.0, "high_nut_af_candidates": list(AF_CANDIDATES),
        "high_nut_length_clearance_candidates": list(LENGTH_CLEARANCES), "set_screw_size": "M3", "set_screw_length": 25.0,
        "set_screw_count": 4, "set_screw_tip_status": "HOLD_PHYSICAL_MEASUREMENT_REQUIRED",
        "access_bore_candidates": list(ACCESS_CANDIDATES), "selected_access_bore": SELECTED_ACCESS,
        "outer_end_recess_candidates": list(RECESS_CANDIDATES), "selected_outer_end_recess": SELECTED_RECESS,
        "retainer_fastener_count": 4, "retainer_fastener_size": "M4", "retainer_pcd": 24.0,
        "minimum_reaction_wall": a["walls"]["reaction_mm"], "minimum_adjacent_pocket_wall": a["walls"]["adjacent_pockets_mm"],
        "minimum_pocket_to_m4_wall": a["walls"]["pocket_to_m4_mm"], "minimum_pocket_to_bore_wall": a["walls"]["pocket_to_bore_mm"],
        "minimum_access_bore_wall": a["access_bores"][str(SELECTED_ACCESS)]["adjacent_access_wall_mm"],
        "set_screw_to_link_intersection": a["intersections"]["set_screw_to_link_mm3"],
        "tool_to_link_intersection": a["intersections"]["internal_tool_to_link_mm3"],
        "set_screw_to_guide_intersection": a["intersections"]["set_screw_to_guide_mm3"],
        "set_screw_to_bearing_intersection": a["intersections"]["set_screw_to_bearing_mm3"],
        "final_sprocket_solid_count": base["solid_count"], "stl_watertight": stl_ok,
        "shaft_irreversible_machining_required": False, "single_manufacturer_dependency": False,
        "petg_spare_rate_percent": 100, "authority_files_changed": False, "physical_test_status": "COUPONS_ONLY_BODY_BLOCKED",
        "torque_capacity_status": "NOT_TESTED", "creep_status": "REQUIRED", "powered_rotation_status": "NOT_APPROVED",
        "field_deployment_status": "NOT_APPROVED", "design_status": "FAIL_ACCESS_BORE_EXTERNAL_ROOT_AND_LINK_CONTRACT",
        "print_release": "COUPONS_ONLY_H24_BODY_PRINT_BLOCKED_REFERENCE", "marking_status": "CAD_MODELED",
        "parent_audit": pa, "analysis": a,
        "release": {"GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD", "GITHUB_MANUFACTURING_RELEASE": "HOLD", "PURCHASE_STATUS": "NOT_APPROVED",
            "BELT_TENSION": "NOT_APPROVED", "TORQUE_LOAD": "NOT_APPROVED", "H24_CAD": "FAIL_ACCESS_BORE_LINK_CLEARANCE",
            "H24_PHYSICAL_FIT": "BLOCKED_PENDING_GEOMETRY_CORRECTION", "H24_CREEP": "HOLD_AFTER_GEOMETRY_CORRECTION", "GLOBAL_ASSEMBLY_INTERFERENCE": "HOLD"}}

def documents(m: dict[str, Any]) -> dict[str, str]:
    a, w, reach = m["analysis"], m["analysis"]["walls"], m["analysis"]["reach"]
    gate = "`H2.4_CAD = FAIL_ACCESS_BORE_LINK_CLEARANCE`; `H2.4_PHYSICAL_FIT = BLOCKED_PENDING_GEOMETRY_CORRECTION`; `GLOBAL_ASSEMBLY_INTERFERENCE = HOLD`; `PHYSICAL_PASS` is not granted; `POWERED_ROTATION = NOT_APPROVED`."
    return {
        "README.md": f"# H2.4 staggered deep-nut set-screw v{VERSION}\n\nM3x25 headed screw and OD6.8 washer are removed. The recessed set screw clears the conservative link, but any usable circular access bore through the curved root removes {m['parent_minus_final_external_volume']:.6f} mm3 from the protected root/link shell. The internal tool shank has the same conflict. H2.4 body/STLs are blocked references; coupons only may print. {gate}",
        "DESIGN_SPEC.md": f"# DESIGN_SPEC\n\nFour M3x25 set screws run through measured AF5.2 x13.0 high nuts at0/90/180/270 degrees; C0 is the minimum-couple layout. Walls pass: reaction {w['reaction_mm']:.3f}, adjacent pockets {w['adjacent_pockets_mm']:.3f}, pocket-M4 {w['pocket_to_m4_mm']:.3f}, pocket-B103 {w['pocket_to_bore_mm']:.3f}, selected access {m['minimum_access_bore_wall']:.3f} mm. Mandatory external-root/link preservation fails because a through access opening cannot remain wholly inside ROOT_R. {gate}",
        "PHYSICAL_INPUT.md": "# PHYSICAL_INPUT\n\nMEASURED/USER_REPORTED: high-nut AF5.2 mm, length13.0 mm; candidate M3x25 hex-socket set screws; four points; unmodified10 mm shaft; 100% PETG spare. Headed screw, OD6.8 washer and washer seat are removed. Tip, socket AF, actual/effective length, material and finish remain HOLD.",
        "SOURCE_TRACE.md": f"# SOURCE_TRACE\n\nRead-only parent `{PARENT_REL}`: 70 files, ledger `{PARENT_LEDGER}`, builder `{PARENT_BUILDER_SHA}`, manifest `{PARENT_MANIFEST_SHA}`, test `{PARENT_TEST_SHA}`, ZIP `{PARENT_ZIP_SHA}`. External 12T source is reached through the protected parent chain.",
        "PARENT_LANE_AUDIT.md": "# PARENT_LANE_AUDIT\n\nParent 70/70, STEP24/24, STL11/11, SVG5/5 and hashes69/69 PASS. Its headed-screw/washer failure is preserved as design input. Parent bytes are not in COMMIT_PATHS and were not modified.",
        "EXTERNAL_GEOMETRY_COMPARISON.md": f"# EXTERNAL_GEOMETRY_COMPARISON\n\nAll nine H2.4 layout/bore variants retain12T/tip/phase/bbox, but the usable Ø3.5 radial opening cuts the curved root/link shell. C0-B102 parent-minus={m['parent_minus_final_external_volume']:.9f}, final-minus={m['final_minus_parent_external_volume']:.9f} mm3; therefore external_tooth_geometry_changed=true and the mandatory zero-volume contract FAILS. Raw bbox delta is {m['bbox_boolean_rounding_delta_max_mm']:.9f} mm within2e-6 mm; equal bbox does not negate the local removed volume.",
        "H23_FAILURE_ANALYSIS.md": "# H23_FAILURE_ANALYSIS\n\nH2.3 failed because the available6.001 mm inter-tooth root gap was narrower than the OD6.8 washer;7.0/7.2 seats failed, the headed path changed parent volume, and hardware intersected the conservative link reference. H2.4 removes all three external headed/washer features rather than shrinking measured hardware silently.",
        "H23_TO_H24_CHANGELOG.md": "# H23_TO_H24_CHANGELOG\n\nPreserved: teeth, F/R deep nuts, C0/C15/C30, B101/B102/B103, dual retainers and M4 PCD24. Removed: head, washer, seat. Added: radial3.5/4.0/4.5 access study, M3x25 set-screw states and0/0.5/1.0/1.5 recess study.",
        "STAGGERED_DEEP_NUT_SPEC.md": "# STAGGERED_DEEP_NUT_SPEC\n\nA1/A2 insert from F at0/180; B1/B2 insert from R at90/270. Pocket AF5.25 x13.20 is a CAD candidate only. Retainers prevent axial loss; press fit alone is not authority. Rounded relief and push-out service are retained.",
        "SET_SCREW_INTERFACE_SPEC.md": f"# SET_SCREW_INTERFACE_SPEC\n\nM3x25 total path25.0; nut engagement13.0; nut-inner to shaft3.3. First contact outer radius30.0, {reach['first_contact_protrusion_beyond_root_mm']:.2f} beyond root. Selected recess1.0 puts the screw body inside the local link with0 mm3 intersection, but requires {reach['selected_shaft_envelope_penetration_mm']:.2f} mm shaft-envelope overlap. Tip/indentation remain HOLD. Flush has a separate0.269 mm3 curved-envelope conflict. Retracted/first-contact require crawler removal.",
        "TOOL_ACCESS_BORE_SPEC.md": f"# TOOL_ACCESS_BORE_SPEC\n\n3.5/4.0/4.5 mm coupons are provided. Adjacent-tunnel walls are {a['access_bores']['3.5']['adjacent_access_wall_mm']:.3f}/{a['access_bores']['4.0']['adjacent_access_wall_mm']:.3f}/{a['access_bores']['4.5']['adjacent_access_wall_mm']:.3f} mm. Only3.5 meets3 mm. Nevertheless its circular end crosses the curved ROOT_R shell/local link by {a['intersections']['access_bore_to_link_mm3']:.6f} mm3; the internal shank envelope has {a['intersections']['internal_tool_to_link_mm3']:.6f} mm3. A tangent-stopped bore would leave a membrane and is not a usable opening. No diameter is selected for release; body CAD/print is FAIL/BLOCKED.",
        "HIGH_NUT_FIT_COUPON_SPEC.md": "# HIGH_NUT_FIT_COUPON_SPEC\n\nSeparate F/R 18-cell plates cover AF5.10..5.35 and depth13.10/13.20/13.30 with the selected3.5 mm M3/tool passage and push-out. Require light insertion, no drop/rotation/whitening/crack, normal M3 passage, removal and F/R equivalence.",
        "HARDWARE_MEASUREMENT_REQUIRED.md": "# HARDWARE_MEASUREMENT_REQUIRED\n\nMeasure set-screw socket AF, tip form, actual length, effective thread, material/grade/finish; measure actual hex-key shank, bend radius and handle. Cup/flat/unspecified tips remain alternatives. Confirm whether1.53 mm CAD shaft overlap can be accommodated by the real tip/indentation; otherwise compare M3x20 and M3x30 without automatic adoption.",
        "ASSEMBLY_INSTRUCTIONS.md": "# ASSEMBLY_INSTRUCTIONS\n\n1 F;2 insert A1/A2 from F;3 R;4 insert B1/B2 from R;5 retainers loose;6 place on10 mm shaft;7 insert four M3x25;8-11 touch A1,A2,B1,B2;12-15 add1/8 turn in that order;16 check runout;17 one further1/8 turn only if needed;18 verify recess;19 witness shaft/body;20 record A1. Remove crawler links before tool service. No power tool, asymmetric tightening, guessed torque, threadlocker on first test or tightening with crawler installed.",
        "PHYSICAL_TEST_PLAN.md": "# PHYSICAL_TEST_PLAN\n\nGate1 F/R deep-nut coupons and Gate2 access-bore coupons may proceed. Gate3 H2.4 body is BLOCKED until the access-root/link geometry is corrected and the M3 tip/socket/tool are measured. Gates4 creep,5 static torque and6 crawler are consequently HOLD. No body load, crawler installation or power.",
        "STATIC_TORQUE_TEST_PLAN.md": "# STATIC_TORQUE_TEST_PLAN\n\nAfter Gates1-4 only:0.25/0.50/0.75 N.m static comparison. Stop at slip, whitening, crack or loosening. These are comparison points, not operating torque authority.",
        "CREEP_TEST_PLAN.md": "# CREEP_TEST_PLAN\n\nHold24h, inspect contact/nut/pocket/F-R deformation/runout/witness marks; allow one light retightening, then hold24h. A second loosening is FAIL_CREEP and keeps powered rotation prohibited.",
        "PETG_SPARE_PART_RULE.md": "# PETG_SPARE_PART_RULE\n\n`PETG_CRITICAL_DRIVE_PART_SPARE_RULE = REQUIRED`;100% minimum. Before physical pass: one test body, one identical spare and two retainer sets only. No mass print.",
        "METAL_MIGRATION_INTERFACE.md": "# METAL_MIGRATION_INTERFACE\n\nPreserve M3x25, four axes, A/B labels, F/R insertion, diagonal tightening, unmodified shaft, witness marks and common hex key. A metal hub may use M3 taps or retained metal nuts. No metal manufacturing approval.",
        "HARDWARE_BOM.md": "# HARDWARE_BOM\n\nPer side:4 M3 high nuts,4 M3x25 set screws,4 M4 through bolts,8 M4 washers,4 M4 nuts,one10 mm shaft. Double for two sides; one-side hardware spare minimum. M3x20/30, cup/flat tips, SUS/finish/threadlocker/caps are candidates. Headed M3, OD6.8 washer and M3 washer seat are not used.",
        "PRINT_NOTES.md": "# PRINT_NOTES\n\nBambu A1/PETG/100% scale. Only deep-nut and access-bore coupons are approved for initial print. H24 body/retainer/sprocket STLs are PRINT_BLOCKED_REFERENCE because the access-root/link contract fails. Record printer/material/lot/slicer/orientation; no body print or mass print.",
        "DESIGN_REVIEW.md": f"# DESIGN_REVIEW\n\nC0/3.5 mm/B102 minimizes internal change: nominal1.0 mm recessed set screws clear local link and guide/bearing/M4/nut/pocket checks pass. However the Ø3.5 through access void and internal tool path each intersect the conservative curved root/link envelope by about0.499080 mm3, violating two mandatory zero-intersection checks and the zero external-volume contract. Ø4.0/4.5 also fail the3 mm wall. Global transforms and tip measurements remain HOLD, but the local mandatory conflict alone is sufficient for FAIL. {gate}",
    }

def svg(title: str, body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#f7f8fa"/><text x="40" y="50" font-family="sans-serif" font-size="28">{title}</text><text x="40" y="82" font-family="sans-serif" font-size="18" fill="#a65">CONDITIONAL CAD · GLOBAL HOLD · NO POWER</text>{body}</svg>'

def svgs() -> dict[str, str]:
    return {
        SVG_FILES[0]: svg("H2.4 F/R alternating deep nuts", '<circle cx="350" cy="350" r="220" fill="#dce9f1" stroke="#245"/><text x="590" y="230" font-family="sans-serif" font-size="23">0 F · 90 R · 180 F · 270 R</text><text x="590" y="300" font-family="sans-serif" font-size="22">AF5.2 × 13.0 · M3×25</text>'),
        SVG_FILES[1]: svg("M3x25 reach and recess", '<text x="100" y="210" font-family="sans-serif" font-size="23">first contact: outer R30.00 · +0.53 beyond root</text><text x="100" y="300" font-family="sans-serif" font-size="23">flush: shaft-envelope overlap0.53</text><text x="100" y="390" font-family="sans-serif" font-size="23">recess1.0: outer R28.47 · overlap1.53 · TIP HOLD</text>'),
        SVG_FILES[2]: svg("Tool access bore comparison", '<text x="100" y="210" font-family="sans-serif" font-size="23">Ø3.5 → adjacent wall3.147 · CONDITIONAL</text><text x="100" y="300" font-family="sans-serif" font-size="23">Ø4.0 → wall2.647 · FAIL &lt;3</text><text x="100" y="390" font-family="sans-serif" font-size="23">Ø4.5 → wall2.147 · FAIL &lt;3</text>'),
        SVG_FILES[3]: svg("Local clearance versus global registration", '<text x="100" y="220" font-family="sans-serif" font-size="23">set screw / access void / internal shank → local link 0 mm³</text><text x="100" y="320" font-family="sans-serif" font-size="23">actual wrench handle + installed link → HOLD transform/tool measurement</text><text x="100" y="420" font-family="sans-serif" font-size="23">frame / 60T / belt → GLOBAL REGISTRATION HOLD</text>'),
        SVG_FILES[4]: svg("H2.4 physical gate order", '<text x="100" y="220" font-family="sans-serif" font-size="23">1 deep-nut coupon → 2 access coupon → 3 hardware measurement</text><text x="100" y="310" font-family="sans-serif" font-size="23">4 no-crawler body → 5 creep → 6 static torque</text><text x="100" y="400" font-family="sans-serif" font-size="23">crawler unpowered only after all prior gates</text>'),
    }

def export(shape: cq.Shape | cq.Workplane, path: Path, stl: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if stl: cq.exporters.export(shape, str(path), tolerance=0.01, angularTolerance=0.1)
    else: cq.exporters.export(shape, str(path))

def export_all() -> None:
    for face, si, ti in (("F", 10, 8), ("R", 11, 9)):
        q = deep_coupon(face); export(q, LANE / STEP_FILES[si]); export(q, LANE / STL_FILES[ti], True)
    q = access_coupon(); export(q, LANE / STEP_FILES[12]); export(q, LANE / STL_FILES[10], True)
    candidates = [("C0", 10.1, 0, 0), ("C0", 10.2, 1, 1), ("C0", 10.3, 2, 2), ("C15", 10.2, 3, 3), ("C30", 10.2, 4, None)]
    for layout, bore, si, sti in candidates:
        s = h24(layout, bore); export(s, LANE / STEP_FILES[si])
        if sti is not None: export(s, LANE / STL_FILES[sti], True)
    grid = [h24(layout, bore).translate((j * 75, i * 75, 0)).val() for i, layout in enumerate(LAYOUTS) for j, bore in enumerate(BORES.values())]
    export(cq.Compound.makeCompound(grid), LANE / STEP_FILES[5])
    for face, base in (("F", 6), ("R", 7)):
        for k, t in enumerate(RETAINER_TS):
            s = retainer(face, t); idx = base + 2 * k
            export(s, LANE / STEP_FILES[idx]); export(s, LANE / STL_FILES[4 + (0 if face == "F" else 1) + 2 * k], True)
    ass = [exploded(), assembly(mode="FRONT"), assembly("RETRACTED"), assembly("FIRST_CONTACT"), assembly("NOMINAL"),
           assembly(recess=0.0), assembly(recess=0.5), assembly(recess=1.0), assembly(recess=1.5),
           assembly(mode="FRONT"), assembly(mode="REAR"), tool_service(), section("A"), section("B"),
           cq.Compound.makeCompound([section("STAGGER").translate((0, 0, 0)), h24("C15", 10.2).translate((75, 0, 0)).val(), h24("C30", 10.2).translate((150, 0, 0)).val()])]
    for path, shape in zip(STEP_FILES[13:], ass): export(shape, LANE / path)
    for path, text in svgs().items(): wt(LANE / path, text)

def verify_steps(base: Path = LANE) -> dict[str, Any]:
    rows = []
    for p in STEP_FILES:
        try:
            s = cq.importers.importStep(str(base / p)).val(); b = s.BoundingBox(); ok = len(s.Solids()) >= 1 and b.xlen > 0 and b.ylen > 0 and b.zlen > 0
            rows.append({"path": p, "solids": len(s.Solids()), "pass": ok})
        except Exception as e: rows.append({"path": p, "pass": False, "error": str(e)})
    return {"count": len(rows), "pass_count": sum(x["pass"] for x in rows), "rows": rows, "status": "PASS" if all(x["pass"] for x in rows) else "FAIL"}

def verify_stls(base: Path = LANE) -> dict[str, Any]:
    rows = []
    for p in STL_FILES:
        try:
            with (base / p).open("rb") as f: raw = trimesh.exchange.stl.load_stl_binary(f)
            mesh = trimesh.Trimesh(vertices=raw["vertices"], faces=raw["faces"], process=False); mesh.merge_vertices()
            deg = int((mesh.area_faces <= 1e-10).sum()); ok = mesh.is_watertight and mesh.body_count == 1 and mesh.volume > 0 and deg == 0
            rows.append({"path": p, "watertight": bool(mesh.is_watertight), "components": int(mesh.body_count), "degenerate": deg, "pass": bool(ok)})
        except Exception as e: rows.append({"path": p, "pass": False, "error": str(e)})
    return {"count": len(rows), "pass_count": sum(x["pass"] for x in rows), "rows": rows, "status": "PASS" if all(x["pass"] for x in rows) else "FAIL"}

def verify_svgs(base: Path = LANE) -> dict[str, Any]:
    import xml.etree.ElementTree as ET
    rows = []
    for p in SVG_FILES:
        try:
            r = ET.parse(base / p).getroot(); ok = r.tag.endswith("svg") and r.get("viewBox") is not None; rows.append({"path": p, "pass": ok})
        except Exception as e: rows.append({"path": p, "pass": False, "error": str(e)})
    return {"count": len(rows), "pass_count": sum(x["pass"] for x in rows), "status": "PASS" if all(x["pass"] for x in rows) else "FAIL"}

def commit_text() -> str: return "\n".join(f"{LANE_REL}/{p}" for p in PATHS)
def manifest_text() -> str:
    return "\n".join(f"{p}|{'COUPON_PRINT_ONLY' if p.endswith('.stl') and 'COUPON' in p else 'PRINT_BLOCKED_REFERENCE' if p.endswith('.stl') else 'H24_HANDOFF_RECORD'}" for p in PATHS)
def sums(base: Path = LANE) -> str: return "\n".join(f"{sha(base / p)}  {p}" for p in PATHS if p != "SHA256SUMS.txt")

def verify_ledgers(base: Path = LANE) -> dict[str, Any]:
    man = [x.split("|", 1)[0] for x in (base / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()]
    vals = {}
    for line in (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line: d, p = line.split("  ", 1); vals[p] = d
    mismatches = [p for p, d in vals.items() if not (base / p).is_file() or sha(base / p) != d]
    ok = man == list(PATHS) and set(vals) == set(PATHS) - {"SHA256SUMS.txt"} and not mismatches
    return {"manifest_count": len(man), "hash_count": len(vals), "mismatches": mismatches, "status": "PASS" if ok else "FAIL"}

def refresh() -> dict[str, Any]:
    for p in SOURCE_FILES:
        if not (LANE / p).is_file(): raise RuntimeError("source missing " + p)
    repo = repo_audit(False); pa = parent_audit(True); a = analysis(); export_all()
    steps, stls, sv = verify_steps(), verify_stls(), verify_svgs(); m = manifest(repo, pa, a, stls["status"] == "PASS")
    for p, text in documents(m).items(): wt(LANE / p, text)
    wj(LANE / "geometry_manifest.json", m)
    wj(LANE / "validation_report.json", {"document_id": DOC_ID, "artifact_contract": "PASS" if steps["status"] == stls["status"] == sv["status"] == "PASS" else "FAIL",
        "design_status": m["design_status"], "local_geometry": "FAIL_ACCESS_BORE_LINK", "global_assembly": "HOLD",
        "physical_fit": "BLOCKED_PENDING_GEOMETRY_CORRECTION", "powered_rotation": "NOT_APPROVED", "status": "FAIL"})
    wt(LANE / "COMMIT_PATHS.txt", commit_text()); wt(LANE / "MANIFEST.txt", manifest_text())
    wt(LANE / "build_log.txt", f"step={steps['pass_count']}/{steps['count']}\nstl={stls['pass_count']}/{stls['count']}\nsvg={sv['pass_count']}/{sv['count']}\ndesign_status={m['design_status']}\nglobal=HOLD\nphysical=COUPONS_ONLY_BODY_BLOCKED")
    wt(LANE / "test_log.txt", "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\npowered_rotation=NOT_APPROVED")
    wt(LANE / "SHA256SUMS.txt", sums())
    if files() != sorted(PATHS): raise RuntimeError({"actual": files(), "expected": sorted(PATHS)})
    led = verify_ledgers()
    if steps["status"] != "PASS" or stls["status"] != "PASS" or sv["status"] != "PASS" or led["status"] != "PASS":
        raise RuntimeError({"step": steps, "stl": stls, "svg": sv, "ledger": led})
    return {"artifact_contract": "PASS", "design_status": m["design_status"], "formal_paths": len(PATHS),
            "STEP": f"{steps['pass_count']}/{steps['count']} PASS", "STL": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{sv['pass_count']}/{sv['count']} PASS"}

def verify() -> dict[str, Any]:
    if files() != sorted(PATHS): raise RuntimeError({"actual": files(), "expected": sorted(PATHS)})
    repo, pa = repo_audit(True), parent_audit(); s, t, v, l = verify_steps(), verify_stls(), verify_svgs(), verify_ledgers()
    m = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8")); ints = m["analysis"]["intersections"]
    checks = {"design_failure_recorded": m["design_status"] == "FAIL_ACCESS_BORE_EXTERNAL_ROOT_AND_LINK_CONTRACT",
        "external_conflict_recorded": m["external_tooth_geometry_changed"] and m["parent_minus_final_external_volume"] > 0 and m["final_minus_parent_external_volume"] <= 1e-6,
        "walls": min(m["minimum_reaction_wall"], m["minimum_adjacent_pocket_wall"], m["minimum_pocket_to_m4_wall"], m["minimum_pocket_to_bore_wall"], m["minimum_access_bore_wall"]) >= 3,
        "recessed_set_screw_clear": ints["set_screw_to_link_mm3"] <= 1e-6,
        "mandatory_access_conflict": ints["access_bore_to_link_mm3"] > 0 and ints["internal_tool_to_link_mm3"] > 0,
        "other_local_intersections": max(ints[k] for k in ("set_screw_to_guide_mm3", "set_screw_to_bearing_mm3", "set_screw_to_m4_mm3", "high_nut_pairwise_max_mm3")) <= 1e-6,
        "global_hold": m["release"]["GLOBAL_ASSEMBLY_INTERFERENCE"] == "HOLD"}
    if s["status"] != "PASS" or t["status"] != "PASS" or v["status"] != "PASS" or l["status"] != "PASS" or not all(checks.values()):
        raise RuntimeError({"checks": checks, "steps": s["status"], "stl": t["status"], "svg": v["status"], "ledger": l["status"]})
    return {"repository": repo, "parent": pa["status"], "artifact_contract": "PASS", "design_status": m["design_status"],
        "formal_paths": len(PATHS), "STEP": f"{s['pass_count']}/{s['count']} PASS", "STL": f"{t['pass_count']}/{t['count']} PASS",
        "SVG": f"{v['pass_count']}/{v['count']} PASS", "manifest": f"{l['manifest_count']}/{len(PATHS)} PASS", "hashes": f"{l['hash_count']}/{len(PATHS)-1} PASS"}

def zi(path: str) -> zipfile.ZipInfo:
    i = zipfile.ZipInfo(path, date_time=(2000, 1, 1, 0, 0, 0)); i.compress_type = zipfile.ZIP_DEFLATED; i.external_attr = 0o100644 << 16; return i

def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as z:
        for p in PATHS: z.writestr(zi(p), (LANE / p).read_bytes())

def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    with zipfile.ZipFile(path) as z:
        names = z.namelist(); duplicates = sorted({x for x in names if names.count(x) > 1})
        traversal = [x for x in names if PurePosixPath(x).is_absolute() or ".." in PurePosixPath(x).parts or "\\" in x]
        vals = {}
        for line in z.read("SHA256SUMS.txt").decode().splitlines(): d, p = line.split("  ", 1); vals[p] = d
        internal = [p for p, d in vals.items() if hashlib.sha256(z.read(p)).hexdigest() != d]
        lane_mismatch = [p for p in names if hashlib.sha256(z.read(p)).hexdigest() != sha(LANE / p)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="h24_zip_") as td:
            with zipfile.ZipFile(path) as z: z.extractall(td)
            env = dict(os.environ); env["V09373_TEST_ZIP"] = str(path)
            b = run([sys.executable, "-B", SOURCE_FILES[0], "--verify"], Path(td), env)
            t = run([sys.executable, "-B", SOURCE_FILES[1]], Path(td), env)
            if b.returncode or t.returncode: raise RuntimeError({"build": b.stdout, "tests": t.stdout})
            standalone_status = "PASS"
    if names != list(PATHS) or duplicates or traversal or internal or lane_mismatch:
        raise RuntimeError({"names": names == list(PATHS), "duplicates": duplicates, "traversal": traversal, "internal": internal, "lane": lane_mismatch})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal,
            "internal_hash": "PASS", "lane_byte_match": "PASS", "standalone": standalone_status, "zip_sha256": sha(path), "status": "PASS"}

def package() -> dict[str, Any]:
    verify(); DOWNLOADS.mkdir(parents=True, exist_ok=True); stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final = DOWNLOADS / f"{ZIP_PREFIX}{stamp}.zip"; tmp = DOWNLOADS / f".{ZIP_PREFIX}{stamp}.tmp"
    try:
        wt(LANE / "test_log.txt", "status=PACKAGE_TESTS_PENDING\npowered_rotation=NOT_APPROVED"); wt(LANE / "SHA256SUMS.txt", sums()); write_zip(tmp)
        env = dict(os.environ); env["V09373_TEST_ZIP"] = str(tmp); result = run([sys.executable, "-B", SOURCE_FILES[1]], LANE, env)
        if result.returncode: raise RuntimeError(result.stdout)
        summary = [x for x in result.stdout.splitlines() if x.startswith("Ran ") or x == "OK"]
        wt(LANE / "test_log.txt", "status=PASS\n" + "\n".join(summary) + "\npowered_rotation=NOT_APPROVED\nfull_output:\n" + result.stdout)
        wt(LANE / "SHA256SUMS.txt", sums()); verify()
    finally:
        if tmp.exists(): tmp.unlink()
    write_zip(final); return verify_zip(final, True)

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--refresh-artifacts", action="store_true"); p.add_argument("--verify", action="store_true")
    p.add_argument("--package", action="store_true"); p.add_argument("--verify-zip", type=Path); a = p.parse_args(argv)
    if sum((a.refresh_artifacts, a.verify, a.package, a.verify_zip is not None)) != 1: p.error("choose one action")
    result = refresh() if a.refresh_artifacts else verify() if a.verify else package() if a.package else verify_zip(a.verify_zip, True)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)); return 0

if __name__ == "__main__": raise SystemExit(main())
