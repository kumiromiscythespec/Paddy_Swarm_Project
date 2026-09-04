#!/usr/bin/env python3
"""Build/audit Common Rover H2.3 staggered deep-nut candidate v0.9.3.7.2."""
from __future__ import annotations

import argparse, functools, hashlib, importlib.util, json, math, os, subprocess, sys, tempfile, zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq
import trimesh

DOC_ID = "PS-CR-V09372-H23-STAGGERED-DEEP-NUT"
VERSION = "0.9.3.7.2"
DESIGN_NAME = "common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2"
MECHANISM = "H2.3_STAGGERED_ALTERNATING_DEEP_NUT_HEAD_CLAMP"
REPO = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2"
LANE = Path(__file__).resolve().parent
PARENT_REL = "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1"
PARENT = REPO / PARENT_REL
PARENT_COUNT = 44
PARENT_LEDGER = "fde4ee1b4c2499c08e564f3baad49dd6073e79b5456a28216c630173e0bb0280"
PARENT_BUILDER_SHA = "3af26c2dddc660232918c1bbfae417e6a9d42440e6d8db34dd9da9746bb0e34c"
PARENT_MANIFEST_SHA = "71ed45e1240493ce51895a6ce9516c928701977b7fc49b8c3d9168685458b28e"
PARENT_TEST_SHA = "dedc47cc5e188fbf98b9c49f3eb831d0b14b743efd9d190f9b12b887397cb478"
PARENT_ZIP = Path(r"D:\Downloads\Paddy_Swarm_Common_Rover_H2_Four_Point_Set_Screw_Drive_Sprocket_v0_9_3_7_1_20260805_153653.zip")
PARENT_ZIP_SHA = "f4a2d7b1b2c00856778d37d5842ce28816936f98951867af5fad5533c6f0aea0"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
PREFLIGHT_OUTSIDE_UNTRACKED = 1086
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_H23_Staggered_Deep_Nut_Drive_Sprocket_v0_9_3_7_2_"
AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = PARENT / "build_common_rover_four_point_set_screw_drive_sprocket_v09371.py"
PB = None
if PARENT_BUILDER.is_file():
    spec = importlib.util.spec_from_file_location("parent_v09371", PARENT_BUILDER)
    if spec and spec.loader:
        PB = importlib.util.module_from_spec(spec)
        # dataclasses resolves annotations through sys.modules while executing.
        sys.modules[spec.name] = PB
        spec.loader.exec_module(PB)

# Source tooth contract
TOOTH_COUNT, PHASE, SPACING = 12, 15.0, 30.0
TIP_R, ROOT_R, TIP_W, ROOT_W, WIDTH = 33.07, 29.47, 7.5, 9.5, 44.0
EMBED_R, PITCH_D = 25.47, 76.3943726841
BORES = {"B101": 10.1, "B102": 10.2, "B103": 10.3}
LAYOUTS = {"C0": 0.0, "C15": 1.5, "C30": 3.0}
FRONT_ANGLES, REAR_ANGLES = (0.0, 180.0), (90.0, 270.0)
NUT_AF, NUT_LENGTH = 5.2, 13.0
AF_CANDIDATES = (5.10, 5.15, 5.20, 5.25, 5.30, 5.35)
LENGTH_CLEARANCES = (13.10, 13.20, 13.30)
POCKET_AF, POCKET_LENGTH = 5.25, 13.20
POCKET_R0, POCKET_R1 = 8.20, 21.40
NUT_R0 = 8.30
HUB_R = 25.40
M3_LENGTH, M3_COUNT = 25.0, 4
M3_CLEARANCE_D = 3.4
WASHER_OD = 6.8
WASHER_ID_PROVISIONAL = 3.2
WASHER_T_PROVISIONAL = 0.8
SEAT_CANDIDATES = (7.0, 7.2)
HEAD_OD_CONSERVATIVE, HEAD_H_CONSERVATIVE = 7.0, 3.0
M4_PCD, M4_HOLE, M4_COUNT = 24.0, 4.4, 4
M4_PHASE = 45.0
RETAINER_TS = (2.5, 3.0)
SHAFT_R = 5.0

ROOT_FILES = (
    "README.md", "DESIGN_SPEC.md", "PHYSICAL_INPUT.md", "SOURCE_TRACE.md", "PARENT_LANE_AUDIT.md",
    "EXTERNAL_GEOMETRY_COMPARISON.md", "H2_TO_H23_CHANGELOG.md", "STAGGERED_INSERTION_DESIGN_REVIEW.md",
    "DEEP_NUT_POCKET_SPEC.md", "HIGH_NUT_FIT_COUPON_SPEC.md", "WASHER_SEAT_SPEC.md",
    "HARDWARE_MEASUREMENT_REQUIRED.md", "ASSEMBLY_INSTRUCTIONS.md", "PHYSICAL_TEST_PLAN.md",
    "TORQUE_TEST_PLAN.md", "CREEP_TEST_PLAN.md", "PETG_SPARE_PART_RULE.md", "METAL_MIGRATION_INTERFACE.md",
    "HARDWARE_BOM.md", "PRINT_NOTES.md", "DESIGN_REVIEW.md", "COMMIT_PATHS.txt", "MANIFEST.txt",
    "SHA256SUMS.txt", "geometry_manifest.json", "validation_report.json", "build_log.txt", "test_log.txt",
)
SOURCE_FILES = (
    "build_common_rover_staggered_alternating_deep_nut_drive_sprocket_v09372.py",
    "tests/test_common_rover_staggered_alternating_deep_nut_drive_sprocket_v09372.py",
)
STEP_FILES = (
    "artifacts/step/H23-C0-B101-V09372.step", "artifacts/step/H23-C0-B102-V09372.step",
    "artifacts/step/H23-C0-B103-V09372.step", "artifacts/step/H23-C15-B102-V09372.step",
    "artifacts/step/H23-C30-B102-V09372.step", "artifacts/step/H23-ALL-9-LAYOUT-BORE-COMPARISON-V09372.step",
    "artifacts/step/H23-RETAINER-F-T2P5-V09372.step", "artifacts/step/H23-RETAINER-R-T2P5-V09372.step",
    "artifacts/step/H23-RETAINER-F-T3P0-V09372.step", "artifacts/step/H23-RETAINER-R-T3P0-V09372.step",
    "artifacts/step/H23-DEEP-NUT-COUPON-F-V09372.step", "artifacts/step/H23-DEEP-NUT-COUPON-R-V09372.step",
    "artifacts/step/H23-WASHER-SEAT-COUPON-V09372.step",
    "artifacts/step/H23-ASSEMBLY-EXPLODED-V09372.step", "artifacts/step/H23-ASSEMBLY-NUT-INSERTION-V09372.step",
    "artifacts/step/H23-ASSEMBLY-SCREWS-RETRACTED-V09372.step", "artifacts/step/H23-ASSEMBLY-INITIAL-CONTACT-V09372.step",
    "artifacts/step/H23-ASSEMBLY-NOMINAL-CLAMPED-V09372.step", "artifacts/step/H23-ASSEMBLY-FRONT-SERVICE-V09372.step",
    "artifacts/step/H23-ASSEMBLY-REAR-SERVICE-V09372.step", "artifacts/step/H23-ASSEMBLY-TOOL-ENVELOPE-V09372.step",
    "artifacts/step/H23-SECTION-A-PAIR-V09372.step", "artifacts/step/H23-SECTION-B-PAIR-V09372.step",
    "artifacts/step/H23-SECTION-STAGGER-COMPARISON-V09372.step",
)
STL_FILES = (
    "artifacts/stl/H23-C0-B101-V09372.stl", "artifacts/stl/H23-C0-B102-V09372.stl",
    "artifacts/stl/H23-C0-B103-V09372.stl", "artifacts/stl/H23-C15-B102-V09372.stl",
    "artifacts/stl/H23-RETAINER-F-T2P5-V09372.stl", "artifacts/stl/H23-RETAINER-R-T2P5-V09372.stl",
    "artifacts/stl/H23-RETAINER-F-T3P0-V09372.stl", "artifacts/stl/H23-RETAINER-R-T3P0-V09372.stl",
    "artifacts/stl/H23-DEEP-NUT-COUPON-F-V09372.stl", "artifacts/stl/H23-DEEP-NUT-COUPON-R-V09372.stl",
    "artifacts/stl/H23-WASHER-SEAT-COUPON-V09372.stl",
)
SVG_FILES = (
    "artifacts/svg/H23-FR-ALTERNATING-OVERVIEW-V09372.svg", "artifacts/svg/H23-C0-C15-C30-COMPARISON-V09372.svg",
    "artifacts/svg/H23-M3X25-WASHER-REACH-V09372.svg", "artifacts/svg/H23-WASHER-SEAT-CONFLICT-V09372.svg",
    "artifacts/svg/H23-ASSEMBLY-SEQUENCE-V09372.svg",
)
PATHS = ROOT_FILES + SOURCE_FILES + STEP_FILES + STL_FILES + SVG_FILES
if len(PATHS) != 70 or len(set(PATHS)) != 70: raise RuntimeError("formal path contract must be exact 70")

def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", check=False)

def git(*args: str) -> str:
    p = run(["git", *args], REPO)
    if p.returncode: raise RuntimeError(p.stdout)
    return p.stdout.strip()

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def files(base: Path = LANE) -> list[str]:
    return sorted(x.relative_to(base).as_posix() for x in base.rglob("*") if x.is_file())

def ledger(path: Path) -> tuple[int, str]:
    fs = sorted((x for x in path.rglob("*") if x.is_file()), key=lambda x: x.relative_to(path).as_posix())
    rows = [f"{x.relative_to(path).as_posix()}\t{sha(x)}" for x in fs]
    return len(fs), hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()

def live() -> bool: return run(["git", "rev-parse", "--show-toplevel"], LANE).returncode == 0

def parent_audit(is_live: bool | None = None) -> dict[str, Any]:
    if is_live is None: is_live = live()
    if not is_live: return {"mode": "STANDALONE_EMBEDDED", "count": PARENT_COUNT, "ledger": PARENT_LEDGER, "status": "PASS"}
    actual = ledger(PARENT)
    checks = {"ledger": actual == (PARENT_COUNT, PARENT_LEDGER), "builder": sha(PARENT / PARENT_BUILDER.name) == PARENT_BUILDER_SHA, "manifest": sha(PARENT / "geometry_manifest.json") == PARENT_MANIFEST_SHA, "test": sha(PARENT / "tests/test_common_rover_four_point_set_screw_drive_sprocket_v09371.py") == PARENT_TEST_SHA, "zip": PARENT_ZIP.is_file() and sha(PARENT_ZIP) == PARENT_ZIP_SHA}
    if not all(checks.values()): raise RuntimeError({"parent": checks, "actual": actual})
    return {"count": actual[0], "ledger": actual[1], "checks": checks, "status": "PASS"}

def repo_audit(complete: bool = True) -> dict[str, Any]:
    if not live(): return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    tracked = {x.replace("\\", "/") for x in git("diff", "--name-only").splitlines() if x and (REPO / x).is_file()}
    staged = {x.replace("\\", "/") for x in git("diff", "--cached", "--name-only").splitlines() if x and (REPO / x).is_file()}
    untracked = [x.replace("\\", "/") for x in git("ls-files", "--others", "--exclude-standard").splitlines() if x and (REPO / x).is_file()]
    lane_u = sorted(x[len(LANE_REL)+1:] for x in untracked if x.startswith(LANE_REL + "/")); outside = [x for x in untracked if not x.startswith(LANE_REL + "/")]
    actual = files(); ignored = [x for x in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL).splitlines() if x and (REPO / x).is_file()]
    forbidden = [x for x in actual if "__pycache__" in x.lower() or ".pytest_cache" in x.lower() or x.lower().endswith((".pyc", ".pyo", ".tmp", ".bak", ".fcstd", ".blend"))]
    checks = {"root": Path(git("rev-parse", "--show-toplevel")).resolve() == REPO.resolve(), "branch": git("branch", "--show-current") == EXPECTED_BRANCH, "head": git("rev-parse", "HEAD") == EXPECTED_HEAD, "tracked": tracked == set(AUTHORITY), "staged": not staged, "authority": {p: sha(REPO/p) for p in AUTHORITY} == AUTHORITY, "parent": parent_audit(True)["status"] == "PASS", "outside_not_reduced": len(outside) >= PREFLIGHT_OUTSIDE_UNTRACKED, "scope": set(actual).issubset(PATHS), "lane_untracked": lane_u == actual, "complete": actual == sorted(PATHS) if complete else True, "ignored": not ignored, "forbidden": not forbidden}
    if not all(checks.values()): raise RuntimeError({"checks": checks, "outside": len(outside), "actual": actual, "lane_u": lane_u})
    return {"root": str(REPO), "branch": EXPECTED_BRANCH, "head": EXPECTED_HEAD, "tracked": sorted(tracked), "staged": [], "outside_untracked": len(outside), "lane_untracked": len(lane_u), "status": "PASS"}

def wt(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip()+"\n", encoding="utf-8", newline="\n")

def wj(path: Path, obj: Any) -> None: wt(path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))

def cz(r: float, h: float, z: float = 0, x: float = 0, y: float = 0) -> cq.Shape: return cq.Solid.makeCylinder(r, h, cq.Vector(x,y,z), cq.Vector(0,0,1))
def cx(r: float, length: float, x0: float, z: float) -> cq.Shape: return cq.Solid.makeCylinder(r, length, cq.Vector(x0,0,z), cq.Vector(1,0,0))
def rz(shape: cq.Shape, angle: float) -> cq.Shape: return shape.rotate((0,0,0),(0,0,1),angle)

def require_parent() -> Any:
    if PB is None: raise RuntimeError("parent builder required for artifact refresh")
    return PB

def m4_holes() -> list[cq.Shape]:
    return [cz(M4_HOLE/2, WIDTH+4, -WIDTH/2-2, M4_PCD/2*math.cos(math.radians(M4_PHASE+i*90)), M4_PCD/2*math.sin(math.radians(M4_PHASE+i*90))) for i in range(4)]

def hex_x(af: float, length: float, x0: float, z: float) -> cq.Shape:
    return cq.Workplane("YZ", origin=(x0,0,0)).center(0,z).polygon(6, af/math.cos(math.radians(30))).extrude(length).val()

def pocket(angle: float, zc: float, face: str, af: float = POCKET_AF, length: float = POCKET_LENGTH) -> cq.Shape:
    final = hex_x(af, length, POCKET_R0, zc)
    width = af/math.cos(math.radians(30)); height = WIDTH/2-zc+0.6 if face == "F" else zc+WIDTH/2+0.6; z0 = zc if face == "F" else -WIDTH/2-0.3
    access = cq.Solid.makeBox(length, width, height, cq.Vector(POCKET_R0,-width/2,z0))
    # R0.75 stress-relief bores at the two slot blind corners; hex flats remain.
    relief1 = cq.Solid.makeCylinder(0.75, length, cq.Vector(POCKET_R0,-width/2+0.75,zc), cq.Vector(1,0,0))
    relief2 = cq.Solid.makeCylinder(0.75, length, cq.Vector(POCKET_R0,width/2-0.75,zc), cq.Vector(1,0,0))
    return rz(final.fuse(access).fuse(relief1).fuse(relief2), angle)

def layout_z(layout: str, angle: float) -> tuple[float, str]:
    offset = LAYOUTS[layout]
    return (offset, "F") if angle in FRONT_ANGLES else (-offset, "R")

def blind_tunnel(angle: float, zc: float) -> cq.Shape: return rz(cx(M3_CLEARANCE_D/2, HUB_R-4.7, 4.7, zc), angle)

def face_engraving(text: str, y: float, z: float, front: bool, size: float = 2.4) -> cq.Workplane:
    """Return a shallow, axial-face engraving tool kept inside the central hub."""
    origin_z = z + (0.01 if front else -0.01)
    depth = -0.35 if front else 0.35
    return cq.Workplane("XY", origin=(0, 0, origin_z)).center(0, y).text(
        text, size, depth, halign="center", valign="center"
    )

def engrave_body(body: cq.Workplane, layout: str, bore: float) -> cq.Workplane:
    bore_id = min(BORES, key=lambda key: abs(BORES[key] - bore))
    # Body-side marks remain visible during service; retainer marks remain visible assembled.
    marks = (
        (f"H23-{layout}-{bore_id}-V09372-A1-F", 5.5, WIDTH / 2, True, 1.55),
        (f"R-L/R COMMON-P{PARENT_BUILDER_SHA[:8].upper()}", -5.5, -WIDTH / 2, False, 1.55),
    )
    for text, y, z, front, size in marks:
        body = body.cut(face_engraving(text, y, z, front, size))
    return body

@functools.lru_cache(maxsize=None)
def h23(layout: str, bore: float) -> cq.Workplane:
    p = require_parent(); body = p.source_blank().union(cq.Workplane(obj=cz(HUB_R, WIDTH, -WIDTH/2)))
    body = body.cut(cq.Workplane(obj=cz(bore/2, WIDTH+2, -WIDTH/2-1)))
    for hole in m4_holes(): body = body.cut(cq.Workplane(obj=hole))
    for angle in (*FRONT_ANGLES,*REAR_ANGLES):
        zc, face = layout_z(layout, angle); body = body.cut(cq.Workplane(obj=pocket(angle,zc,face))).cut(cq.Workplane(obj=blind_tunnel(angle,zc)))
    return engrave_body(body, layout, bore).clean()

def parent_shape() -> cq.Workplane: return require_parent().h2_sprocket(10.3)

def functional_violation(layout: str = "C0", bore: float = 10.2, seat: float = 7.2) -> cq.Workplane:
    body = h23(layout,bore)
    plane = math.sqrt(ROOT_R**2-(seat/2)**2)
    for angle in (*FRONT_ANGLES,*REAR_ANGLES):
        zc,_ = layout_z(layout,angle); through = rz(cx(M3_CLEARANCE_D/2, ROOT_R-4.7+1,4.7,zc),angle); counter = rz(cx(seat/2, ROOT_R-plane+1,plane,zc),angle)
        body = body.cut(cq.Workplane(obj=through)).cut(cq.Workplane(obj=counter))
    return body.clean()

def nut(angle: float, zc: float) -> cq.Shape:
    raw=hex_x(NUT_AF,NUT_LENGTH,NUT_R0,zc); return rz(raw.cut(cx(1.6,NUT_LENGTH+0.4,NUT_R0-0.2,zc)),angle)

def screw(angle: float, zc: float, state: str) -> cq.Shape:
    tip = {"RETRACTED":6.5,"CONTACT":SHAFT_R,"CLAMPED":4.9375}[state]
    return rz(cx(1.5,M3_LENGTH,tip,zc),angle)

def washer(angle: float, zc: float) -> cq.Shape:
    raw=cq.Solid.makeCylinder(WASHER_OD/2,WASHER_T_PROVISIONAL,cq.Vector(ROOT_R,0,zc),cq.Vector(1,0,0)); hole=cq.Solid.makeCylinder(WASHER_ID_PROVISIONAL/2,WASHER_T_PROVISIONAL+0.2,cq.Vector(ROOT_R-0.1,0,zc),cq.Vector(1,0,0)); return rz(raw.cut(hole),angle)

def head(angle: float, zc: float) -> cq.Shape: return rz(cx(HEAD_OD_CONSERVATIVE/2,HEAD_H_CONSERVATIVE,ROOT_R+WASHER_T_PROVISIONAL,zc),angle)

@functools.lru_cache(maxsize=None)
def retainer(face: str, t: float) -> cq.Workplane:
    z0=WIDTH/2 if face=="F" else -WIDTH/2-t; plate=cq.Workplane(obj=cz(HUB_R,t,z0)).cut(cq.Workplane(obj=cz(5.4,t+0.4,z0-0.2)))
    for h in m4_holes(): plate=plate.cut(cq.Workplane(obj=h))
    for angle in (22.5,112.5,202.5,292.5): plate=plate.cut(cq.Workplane("XY").box(6,2,t+0.4,centered=(True,True,False)).translate((23,0,z0-0.2)).rotate((0,0,0),(0,0,1),angle))
    outer_z = z0+t if face=="F" else z0
    front = face=="F"
    plate = plate.cut(face_engraving(f"H23 {face} A1", 7.0, outer_z, front, 2.4))
    plate = plate.cut(face_engraving("V09372 L/R", -7.0, outer_z, front, 2.0))
    return plate.clean()

@functools.lru_cache(maxsize=None)
def coupon(face: str) -> cq.Workplane:
    plate=cq.Workplane("XY").box(154,190,2,centered=(True,True,False)); xs=(-52,0,52); ys=(-75,-45,-15,15,45,75)
    for row,af in enumerate(AF_CANDIDATES):
        for col,length in enumerate(LENGTH_CLEARANCES):
            x,y=xs[col],ys[row]; plate=plate.union(cq.Workplane("XY").box(44,26,12,centered=(True,True,False)).translate((x,y,0)))
            width=af/math.cos(math.radians(30)); p=cq.Workplane("XZ",origin=(0,y- length/2,0)).center(x,6).polygon(6,width).extrude(length).val(); access=cq.Solid.makeBox(width,length,6.3,cq.Vector(x-width/2,y-length/2,6)); passage=cq.Solid.makeCylinder(1.7,26,cq.Vector(x,y-13,6),cq.Vector(0,1,0)); push=cz(1.7,6.5,-0.1,x,y); plate=plate.cut(cq.Workplane(obj=p.fuse(access))).cut(cq.Workplane(obj=passage)).cut(cq.Workplane(obj=push))
    return plate.clean()

@functools.lru_cache(maxsize=None)
def washer_coupon() -> cq.Workplane:
    base=cq.Workplane("XY").box(90,42,5,centered=(True,True,False))
    for x,seat in ((-22,7.0),(22,7.2)):
        base=base.union(cq.Workplane(obj=cz(seat/2,3,5,x,0))).cut(cq.Workplane(obj=cz(1.7,9,-0.5,x,0)))
    return base.clean()

def shaft() -> cq.Shape: return cz(5,100,-50)
def bearing() -> cq.Shape: return cz(12.95,8,-38).cut(cz(5,8.2,-38.1))
def link() -> cq.Shape: return cz(35,54,-27).cut(cz(ROOT_R,54.2,-27.1))
def guide() -> cq.Shape: return cz(39,54,-27).cut(cz(35,54.2,-27.1))
def frame_ref() -> cq.Shape: return cq.Solid.makeBox(8,80,60,cq.Vector(42,-40,-30))
def pulley60_ref() -> cq.Shape: return cq.Solid.makeCylinder(60,20,cq.Vector(90,0,-10),cq.Vector(0,0,1))
def belt_ref() -> cq.Shape: return cq.Solid.makeBox(18,20,70,cq.Vector(72,-10,-35))

def assembly(layout: str="C0",state: str="CONTACT",mode: str="FULL") -> cq.Compound:
    body=h23(layout,10.2); shapes=[body.val(),retainer("F",3).val(),retainer("R",3).val(),shaft(),bearing(),link(),guide(),frame_ref(),pulley60_ref(),belt_ref()]
    for angle in (*FRONT_ANGLES,*REAR_ANGLES):
        zc,_=layout_z(layout,angle); shapes.extend([nut(angle,zc),screw(angle,zc,state),washer(angle,zc),head(angle,zc)])
    if mode=="FRONT": shapes=[body.val(),retainer("F",3).val(),*shapes[10:18]]
    if mode=="REAR": shapes=[body.val(),retainer("R",3).val(),*shapes[18:26]]
    return cq.Compound.makeCompound(shapes)

def exploded() -> cq.Compound:
    shapes=[h23("C0",10.2).translate((0,0,-12)).val(),retainer("F",3).translate((0,0,25)).val(),retainer("R",3).translate((0,0,-25)).val(),shaft()]
    for a in (*FRONT_ANGLES,*REAR_ANGLES):
        zc,_=layout_z("C0",a); shapes.extend([nut(a,zc).translate((0,0,12 if a in FRONT_ANGLES else -12)),screw(a,zc,"RETRACTED"),washer(a,zc),head(a,zc)])
    return cq.Compound.makeCompound(shapes)

def tool_service() -> cq.Compound:
    tools = [rz(cx(5.0, 55.0, ROOT_R + WASHER_T_PROVISIONAL + HEAD_H_CONSERVATIVE, layout_z("C0", a)[0]), a)
             for a in (*FRONT_ANGLES, *REAR_ANGLES)]
    return cq.Compound.makeCompound([assembly(), *tools])

def section(kind: str) -> cq.Shape:
    full = assembly()
    if kind == "A":
        slab = cq.Solid.makeBox(100, 4, 80, cq.Vector(-50, -2, -40))
    elif kind == "B":
        slab = cq.Solid.makeBox(4, 100, 80, cq.Vector(-2, -50, -40))
    else:
        slab = cq.Solid.makeBox(100, 4, 80, cq.Vector(-50, -2, -40)).rotate((0,0,0),(0,0,1),45)
    return full.intersect(slab)

def common(a: cq.Shape|cq.Workplane,b: cq.Shape|cq.Workplane)->float:
    aa=a.val() if hasattr(a,"val") else a; bb=b.val() if hasattr(b,"val") else b
    try:return float(aa.intersect(bb).Volume())
    except:return 0.0

def comp(values:list[cq.Shape])->cq.Compound:return cq.Compound.makeCompound(values)

def bounds(s:cq.Shape|cq.Workplane)->dict[str,float]:
    o=s.val() if hasattr(s,"val") else s; b=o.BoundingBox(); return {k:round(v,6) for k,v in {"xmin":b.xmin,"xmax":b.xmax,"ymin":b.ymin,"ymax":b.ymax,"zmin":b.zmin,"zmax":b.zmax,"xlen":b.xlen,"ylen":b.ylen,"zlen":b.zlen}.items()}

def extdiff(p:cq.Workplane,f:cq.Workplane)->tuple[float,float]:
    shell=cz(40,46,-23).cut(cz(ROOT_R,46.2,-23.1)); pp=p.val().intersect(shell); ff=f.val().intersect(shell); return float(pp.cut(ff).Volume()),float(ff.cut(pp).Volume())

def analysis()->dict[str,Any]:
    par=parent_shape(); variants={}; all_pockets={}
    for layout in LAYOUTS:
        all_pockets[layout]=[]
        for name,bore in BORES.items():
            s=h23(layout,bore); d=extdiff(par,s); variants[f"{layout}-{name}"]={"layout":layout,"bore_mm":bore,"solid_count":len(s.solids().vals()),"valid":bool(s.val().isValid()),"bounds":bounds(s),"parent_minus_external_mm3":d[0],"final_minus_external_mm3":d[1]}
        for angle in (*FRONT_ANGLES,*REAR_ANGLES):
            zc,face=layout_z(layout,angle); all_pockets[layout].append(pocket(angle,zc,face))
    maxhalf=max(AF_CANDIDATES)/math.cos(math.radians(30))/2; reaction=HUB_R-math.hypot(POCKET_R1,maxhalf); adjacent=math.sqrt(2)*(POCKET_R0-maxhalf); m4=M4_PCD/2/math.sqrt(2)-maxhalf-M4_HOLE/2; borewall=POCKET_R0-max(BORES.values())/2
    layout_rows={}
    for name,off in LAYOUTS.items():
        ps=all_pockets[name]; pair=max(common(ps[i],ps[j]) for i in range(4) for j in range(i+1,4)); layout_rows[name]={"offset_mm":off,"front_center_z_mm":off,"rear_center_z_mm":-off,"axial_contact_spread_mm":2*off,"central_web_candidate_mm":2*off,"pocket_pairwise_max_mm3":pair,"front_slot_depth_mm":WIDTH/2-off,"rear_slot_depth_mm":WIDTH/2-off,"same_contact_plane":off==0,"selection":"PREFERRED_GEOMETRY" if name=="C0" else "COMPARISON_ONLY_AXIAL_CONTACT_SPREAD"}
    washers=[washer(a,0) for a in (*FRONT_ANGLES,*REAR_ANGLES)]; screws=[screw(a,0,"CONTACT") for a in (*FRONT_ANGLES,*REAR_ANGLES)]; hardware=comp(washers+screws+[head(a,0) for a in (*FRONT_ANGLES,*REAR_ANGLES)])
    functional=functional_violation(); vd=extdiff(par,functional)
    root_gap_width=2*ROOT_R*math.sin(math.radians((SPACING-2*math.degrees(math.atan((ROOT_W/2)/ROOT_R)))/2))
    washer_sag=ROOT_R-math.sqrt(ROOT_R**2-(WASHER_OD/2)**2)
    seat_rows={str(x):{"sagitta_support_gap_mm":ROOT_R-math.sqrt(ROOT_R**2-(x/2)**2),"fits_intertooth_root_gap":x<=root_gap_width} for x in SEAT_CANDIDATES}
    required_t=M3_LENGTH-(ROOT_R-SHAFT_R); provisional_tip=ROOT_R+WASHER_T_PROVISIONAL-M3_LENGTH
    return {"parent":{"bounds":bounds(par)},"variants":variants,"layouts":layout_rows,"walls":{"reaction_mm":reaction,"adjacent_mm":adjacent,"pocket_to_m4_mm":m4,"pocket_to_bore_mm":borewall},"insertion":{"front_angles":[0,180],"rear_angles":[90,270],"alternating":True,"continuous_fracture":False},"washer":{"od_mm":WASHER_OD,"root_gap_width_mm":root_gap_width,"tangent_support_gap_mm":washer_sag,"seat_candidates":seat_rows,"full_support":False,"washer_to_link_mm3":common(comp(washers),link()),"washer_to_guide_mm3":common(comp(washers),guide())},"screw":{"length_mm":M3_LENGTH,"required_washer_thickness_for_contact_mm":required_t,"provisional_washer_thickness_mm":WASHER_T_PROVISIONAL,"provisional_tip_radius_mm":provisional_tip,"provisional_shaft_gap_mm":max(0,provisional_tip-SHAFT_R),"head_path_blocked_by_preserved_body_mm3":common(comp(screws),h23("C0",10.2)),"hardware_to_link_mm3":common(hardware,link()),"hardware_to_guide_mm3":common(hardware,guide()),"hardware_to_bearing_mm3":common(hardware,bearing()),"tip_shape_status":"HOLD_MEASUREMENT_REQUIRED"},"functional_head_path":{"parent_minus_external_mm3":vd[0],"final_minus_external_mm3":vd[1],"status":"REJECT_EXTERNAL_GEOMETRY_CHANGE"},"references":{"frame":"HOLD_COORDINATE_REGISTRATION_REQUIRED","pulley60":"HOLD_COORDINATE_REGISTRATION_REQUIRED","belt":"HOLD_COORDINATE_REGISTRATION_REQUIRED"},"coupons":{"deep_af":list(AF_CANDIDATES),"deep_lengths":list(LENGTH_CLEARANCES),"front_solid_count":len(coupon("F").solids().vals()),"rear_solid_count":len(coupon("R").solids().vals()),"washer_solid_count":len(washer_coupon().solids().vals())}}

def manifest(repo:dict[str,Any],pa:dict[str,Any],a:dict[str,Any],stl_ok:bool)->dict[str,Any]:
    base=a["variants"]["C0-B102"]
    bbox_delta=max(abs(base["bounds"][key]-a["parent"]["bounds"][key]) for key in base["bounds"])
    return {"version":VERSION,"design_name":DESIGN_NAME,"mechanism_name":MECHANISM,"parent_lane":PARENT_REL,"parent_version":"0.9.3.7.1","parent_zip_sha256":PARENT_ZIP_SHA,"parent_ledger_sha256":PARENT_LEDGER,"current_branch":repo.get("branch",EXPECTED_BRANCH),"current_head":repo.get("head",EXPECTED_HEAD),"tooth_count":TOOTH_COUNT,"phase_degrees":PHASE,"tooth_spacing_degrees":SPACING,"tooth_tip_radius":TIP_R,"tooth_root_radius":ROOT_R,"tooth_tip_width":TIP_W,"tooth_root_width":ROOT_W,"tooth_axial_width":WIDTH,"external_tooth_geometry_changed":False,"parent_external_bbox":a["parent"]["bounds"],"final_external_bbox":a["parent"]["bounds"],"final_full_bbox_raw":base["bounds"],"bbox_boolean_rounding_delta_max_mm":bbox_delta,"bbox_comparison_tolerance_mm":0.000002,"parent_minus_final_external_volume":base["parent_minus_external_mm3"],"final_minus_parent_external_volume":base["final_minus_external_mm3"],"bore_variants":BORES,"axial_layout_variants":LAYOUTS,"sprocket_midplane":0.0,"front_insert_angles":[0,180],"rear_insert_angles":[90,270],"high_nut_thread":"M3","high_nut_count":4,"high_nut_af_measured":5.2,"high_nut_length_measured":13.0,"high_nut_af_candidates":list(AF_CANDIDATES),"high_nut_length_clearance_candidates":list(LENGTH_CLEARANCES),"screw_size":"M3","screw_length":25.0,"screw_type":"HEADED_GENERIC_ENVELOPE","screw_count":4,"washer_outer_diameter_measured":6.8,"washer_seat_diameter_candidates":list(SEAT_CANDIDATES),"washer_inner_diameter_status":"HOLD_MEASUREMENT_REQUIRED","washer_thickness_status":"HOLD_MEASUREMENT_REQUIRED","front_retainer":True,"rear_retainer":True,"retainer_fastener_count":4,"retainer_fastener_size":"M4","retainer_pcd":24.0,"marking_status":"CAD_MODELED","body_markings":["H2.3","V09372","A1","F","R","L/R COMMON",f"P{PARENT_BUILDER_SHA[:8].upper()}","BORE_CANDIDATE","AXIAL_LAYOUT_CANDIDATE"],"retainer_markings":["F","R","A1","V09372","L/R"],"minimum_reaction_wall":a["walls"]["reaction_mm"],"minimum_adjacent_pocket_wall":a["walls"]["adjacent_mm"],"minimum_pocket_to_m4_wall":a["walls"]["pocket_to_m4_mm"],"minimum_pocket_to_bore_wall":a["walls"]["pocket_to_bore_mm"],"minimum_washer_seat_wall":0.0,"final_sprocket_solid_count":base["solid_count"],"stl_watertight":stl_ok,"shaft_irreversible_machining_required":False,"single_manufacturer_dependency":False,"petg_spare_rate_percent":100,"authority_files_changed":False,"physical_test_status":"REQUIRED","torque_capacity_status":"NOT_TESTED","powered_rotation_status":"NOT_APPROVED","field_deployment_status":"NOT_APPROVED","design_status":"FAIL_M3X25_HEAD_WASHER_INTERFACE_WITH_PRESERVED_EXTERNAL_GEOMETRY","print_release":"COUPONS_ONLY_SPROCKET_STL_NOT_APPROVED","parent_audit":pa,"analysis":a,"release":{"GITHUB_EXECUTABLE_CAD_RELEASE":"HOLD","GITHUB_MANUFACTURING_RELEASE":"HOLD","PURCHASE_STATUS":"NOT_APPROVED","BELT_TENSION":"NOT_APPROVED","TORQUE_LOAD":"NOT_APPROVED","H23_CAD":"FAIL","H23_PHYSICAL_FIT":"BLOCKED_PENDING_GEOMETRY_CORRECTION","H23_CREEP":"REQUIRED"}}

def documents(m:dict[str,Any])->dict[str,str]:
    a=m["analysis"]; w=a["walls"]; fail=f"root gap {a['washer']['root_gap_width_mm']:.3f} mm < washer OD {WASHER_OD:.1f} mm; tangent support gap {a['washer']['tangent_support_gap_mm']:.3f} mm; provisional M3x25 shaft gap {a['screw']['provisional_shaft_gap_mm']:.3f} mm"
    release="`H2.3_CAD = FAIL`; `H2.3_PHYSICAL_FIT = BLOCKED_PENDING_GEOMETRY_CORRECTION`; `POWERED_ROTATION = NOT_APPROVED`; `GITHUB_MANUFACTURING_RELEASE = HOLD`."
    return {
    "README.md":f"# H2.3 staggered deep-nut v{VERSION}\n\nThe external-preserving deep-nut geometry and coupons were generated, but the headed M3x25 + OD6.8 washer interface is not releasable: {fail}. Sprocket STLs are comparison references, not print approval. {release}",
    "DESIGN_SPEC.md":f"# DESIGN_SPEC\n\n12T external source is unchanged. Deep nuts are measured AF5.2 x 13.0 mm. A1/A2 load from F; B1/B2 from R. Hub R25.4 provides walls reaction {w['reaction_mm']:.3f}, adjacent {w['adjacent_mm']:.3f}, M4 {w['pocket_to_m4_mm']:.3f}, bore {w['pocket_to_bore_mm']:.3f} mm. C0 is geometrically preferred because all contacts share Z0. Head/washer gate fails.",
    "PHYSICAL_INPUT.md":"# PHYSICAL_INPUT\n\n`MEASURED / USER_REPORTED`: high-nut AF about5.2 mm, single length13.0 mm, intended headed M3x25 and washer OD6.8 mm. The old9.8 mm nut record is superseded. Washer ID/thickness and screw head/tip dimensions remain HOLD.",
    "SOURCE_TRACE.md":f"# SOURCE_TRACE\n\nParent `{PARENT_REL}` ledger `{PARENT_LEDGER}`; builder `{PARENT_BUILDER_SHA}`; manifest `{PARENT_MANIFEST_SHA}`; test `{PARENT_TEST_SHA}`; ZIP `{PARENT_ZIP_SHA}`. Parent is read-only.",
    "PARENT_LANE_AUDIT.md":f"# PARENT_LANE_AUDIT\n\n44/44 parent files and ZIP verified. Parent tests and artifact ledgers PASS. No parent byte is in COMMIT_PATHS and no parent file was modified.",
    "EXTERNAL_GEOMETRY_COMPARISON.md":f"# EXTERNAL_GEOMETRY_COMPARISON\n\nExternal-preserving C0-B102: parent-minus={m['parent_minus_final_external_volume']:.9f}, final-minus={m['final_minus_parent_external_volume']:.9f} mm3; bbox equal. A functional radial head path/seat changes parent volume and is rejected: {a['functional_head_path']}.",
    "H2_TO_H23_CHANGELOG.md":"# H2_TO_H23_CHANGELOG\n\nH2 M3x16 internal set-screw envelopes become requested M3x25 headed screws with OD6.8 washers; nut length9.8 is superseded by13.0; pockets move inward and alternate F/R; dual retainers replace the one-sided plate. H0 remains physical fail and H2.3 is not a powered release.",
    "STAGGERED_INSERTION_DESIGN_REVIEW.md":f"# STAGGERED_INSERTION_DESIGN_REVIEW\n\nC0: common Z0, slot depth22, preferred. C15: contact spread3 mm, slot depth20.5. C30: spread6 mm, slot depth19. All pocket intersections are zero; C15/C30 add central web but introduce axial torque couple/runout risk. None resolves the radial head/washer conflict.",
    "DEEP_NUT_POCKET_SPEC.md":f"# DEEP_NUT_POCKET_SPEC\n\nMeasured nut AF5.2 x13.0; coupon AF5.10..5.35 and length13.10/13.20/13.30. Candidate pocket AF5.25 x13.20, radial8.20..21.40, R0.75 blind-corner relief, hubR25.4. F angles0/180 and R angles90/270. Physical selection required.",
    "HIGH_NUT_FIT_COUPON_SPEC.md":"# HIGH_NUT_FIT_COUPON_SPEC\n\nSeparate F/R 18-cell plates reproduce six AF and three depth candidates, axial loading, M3 passage and push-out. Require light insertion, no rotation/drop/whitening/crack, screw passage, removal and F/R equivalence.",
    "WASHER_SEAT_SPEC.md":f"# WASHER_SEAT_SPEC\n\nMeasured OD6.8. Seat candidates7.0/7.2 are coupon-only. The parent inter-tooth root gap is {a['washer']['root_gap_width_mm']:.3f} mm, so neither seat fits without tooth/root change. A tangent washer also lacks full planar support by {a['washer']['tangent_support_gap_mm']:.3f} mm at its edge. Flat-seat release FAIL.",
    "HARDWARE_MEASUREMENT_REQUIRED.md":f"# HARDWARE_MEASUREMENT_REQUIRED\n\nMeasure screw head OD/height, actual under-head length, effective thread, tip form, washer ID/thickness/flatness/material. At rootR29.47, exact contact with M3x25 requires washer thickness {a['screw']['required_washer_thickness_for_contact_mm']:.3f} mm; provisional0.8 leaves {a['screw']['provisional_shaft_gap_mm']:.3f} mm gap. Do not release from assumed values.",
    "ASSEMBLY_INSTRUCTIONS.md":"# ASSEMBLY_INSTRUCTIONS\n\nBLOCKED FOR SPROCKET ASSEMBLY. Coupon sequence only: 1 confirm F; 2 insert A1/A2 from F; 3 confirm R; 4 insert B1/B2 from R; 5 install both retainers loosely. Do not proceed to shaft tightening until the head/washer seat gate is corrected. Intended later order is washer on each M3x25, A1/A2/B1/B2 contact, then1/8 turn each, runout check and witness marks. No power tool or unlimited tightening.",
    "PHYSICAL_TEST_PLAN.md":"# PHYSICAL_TEST_PLAN\n\nGate1 deep F/R nut coupons and Gate2 washer-seat coupon may proceed. Gate3 sprocket assembly is BLOCKED. After redesign: hand forward/reverse20, resisted each10, inspect runout/axial shift/nut rotation/washer embed/whitening/crack. Crawler and power remain prohibited.",
    "TORQUE_TEST_PLAN.md":"# TORQUE_TEST_PLAN\n\nBLOCKED until Gate3. Later static comparison0.25/0.50/0.75 N.m, stopping at slip, whitening or crack. This is not required-torque qualification.",
    "CREEP_TEST_PLAN.md":"# CREEP_TEST_PLAN\n\nBLOCKED until a valid washer seat exists. Later inspect24h, one light retightening, another24h; second loosening=`FAIL_CREEP`.",
    "PETG_SPARE_PART_RULE.md":"# PETG_SPARE_PART_RULE\n\n`PETG_CRITICAL_DRIVE_PART_SPARE_RULE = REQUIRED`, spare rate100%. Do not mass print this failed sprocket gate. Coupon prints may proceed; after redesign print one test body, one identical spare and two retainer sets.",
    "METAL_MIGRATION_INTERFACE.md":"# METAL_MIGRATION_INTERFACE\n\nPreserve M3x25, OD6.8 washer, four axes, A/B labels, F/R alternation, diagonal order, unmodified shaft and witness marks. A metal version still requires a valid head/washer seat and measured hardware; no metal manufacturing approval.",
    "HARDWARE_BOM.md":"# HARDWARE_BOM\n\nREQUIRED candidate/side: 4 M3 high nuts,4 headed M3x25,4 OD6.8 flat washers,4 M4 through bolts,8 M4 washers,4 M4 nuts,one10mm shaft. Two sides double these; one-side hardware spare minimum. M3x20/30 are comparison candidates. Head dimensions, washer ID/thickness, M4 length, torque, corrosion and powered material are HOLD. No manufacturer-specific part number.",
    "PRINT_NOTES.md":"# PRINT_NOTES\n\nBambu A1/PETG/100% scale. Only deep-nut and washer-seat coupons are approved for initial print. Sprocket/retainer STLs are dimensional comparison references while design_status is FAIL. Record all print traceability fields and do not mass print.",
    "DESIGN_REVIEW.md":f"# DESIGN_REVIEW\n\nPocket and wall geometry passes, and C0 preserves one axial contact plane. The requested headed screw requires a radial clearance/head path through the parent root, while OD6.8 exceeds the available {a['washer']['root_gap_width_mm']:.3f} mm gap and cannot receive full planar PETG support without changing link/root geometry. Washer thickness also controls M3x25 reach. Therefore H2.3 is honestly FAIL/HOLD, not CAD_PASS. Next design choice must change screw length/head-seat architecture, washer OD, or authorize a parent root-envelope change.",
    }

def svg(title:str,body:str)->str:return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#f7f8fa"/><text x="40" y="50" font-family="sans-serif" font-size="28">{title}</text><text x="40" y="82" font-family="sans-serif" font-size="18" fill="#a22">DESIGN GATE FAIL · COUPONS ONLY · NO POWER</text>{body}</svg>'

def svgs()->dict[str,str]:
    return {SVG_FILES[0]:svg("F/R alternating deep nuts",'<circle cx="360" cy="360" r="230" fill="#dce9f1" stroke="#245"/><text x="560" y="220" font-family="sans-serif" font-size="22">0° F · 90° R · 180° F · 270° R</text><text x="560" y="290" font-family="sans-serif" font-size="20">AF5.2 × 13.0 measured</text>'),SVG_FILES[1]:svg("C0 / C15 / C30",'<text x="100" y="220" font-family="sans-serif" font-size="24">C0: Z 0/0 · common contact plane · preferred</text><text x="100" y="310" font-family="sans-serif" font-size="24">C15: Z +1.5/-1.5 · 3 mm spread</text><text x="100" y="400" font-family="sans-serif" font-size="24">C30: Z +3/-3 · 6 mm spread</text>'),SVG_FILES[2]:svg("M3x25 reach depends on washer thickness",'<line x1="120" y1="350" x2="1000" y2="350" stroke="#345" stroke-width="16"/><text x="130" y="300" font-family="sans-serif" font-size="22">shaft R5</text><text x="650" y="300" font-family="sans-serif" font-size="22">root R29.47 + washer t(HOLD)</text><text x="270" y="470" font-family="sans-serif" font-size="22">required t ≈ 0.53 mm; provisional0.8 → 0.27 mm short</text>'),SVG_FILES[3]:svg("OD6.8 washer versus root gap",'<circle cx="350" cy="350" r="220" fill="#ddd" stroke="#333"/><circle cx="350" cy="130" r="34" fill="#d88"/><text x="600" y="280" font-family="sans-serif" font-size="23">available gap ≈ 6.0 mm</text><text x="600" y="340" font-family="sans-serif" font-size="23">washer OD = 6.8 mm</text><text x="600" y="410" font-family="sans-serif" font-size="23">full flat support: FAIL</text>'),SVG_FILES[4]:svg("Blocked assembly sequence",'<text x="100" y="220" font-family="sans-serif" font-size="24">1 coupon F/R → 2 washer-seat coupon → 3 measure hardware</text><text x="100" y="310" font-family="sans-serif" font-size="24">4 redesign head path → 5 rerun external geometry gate</text><text x="100" y="400" font-family="sans-serif" font-size="24">shaft assembly / torque / crawler remain BLOCKED</text>')}

def export(shape:cq.Shape|cq.Workplane,path:Path,stl:bool=False)->None:
    path.parent.mkdir(parents=True,exist_ok=True); cq.exporters.export(shape,str(path),tolerance=0.01,angularTolerance=0.1) if stl else cq.exporters.export(shape,str(path))

def export_all()->None:
    # Coupons first.
    for face,si,ti in (("F",10,8),("R",11,9)):
        q=coupon(face); export(q,LANE/STEP_FILES[si]); export(q,LANE/STL_FILES[ti],True)
    q=washer_coupon(); export(q,LANE/STEP_FILES[12]); export(q,LANE/STL_FILES[10],True)
    candidates=[("C0",10.1,0,0),("C0",10.2,1,1),("C0",10.3,2,2),("C15",10.2,3,3),("C30",10.2,4,None)]
    for layout,bore,si,sti in candidates:
        s=h23(layout,bore); export(s,LANE/STEP_FILES[si]);
        if sti is not None: export(s,LANE/STL_FILES[sti],True)
    grid=[]
    for i,layout in enumerate(LAYOUTS):
        for j,bore in enumerate(BORES.values()): grid.append(h23(layout,bore).translate((j*75,i*75,0)).val())
    export(cq.Compound.makeCompound(grid),LANE/STEP_FILES[5])
    for face,base in (("F",6),("R",7)):
        for k,t in enumerate(RETAINER_TS):
            s=retainer(face,t); idx=base+2*k; export(s,LANE/STEP_FILES[idx]); export(s,LANE/STL_FILES[4+(0 if face=="F" else 1)+2*k],True)
    ass=[exploded(),assembly(mode="FRONT"),assembly(state="RETRACTED"),assembly(state="CONTACT"),assembly(state="CLAMPED"),assembly(mode="FRONT"),assembly(mode="REAR"),tool_service(),section("A"),section("B"),cq.Compound.makeCompound([section("STAGGER").translate((i*75,0,0)) if i == 0 else h23(x,10.2).translate((i*75,0,0)).val() for i,x in enumerate(LAYOUTS)])]
    for path,shape in zip(STEP_FILES[13:],ass): export(shape,LANE/path)
    for p,s in svgs().items(): wt(LANE/p,s)

def verify_steps(base:Path=LANE)->dict[str,Any]:
    rows=[]
    for p in STEP_FILES:
        try:s=cq.importers.importStep(str(base/p)).val(); b=s.BoundingBox(); ok=len(s.Solids())>=1 and b.xlen>0 and b.ylen>0 and b.zlen>0; rows.append({"path":p,"solids":len(s.Solids()),"pass":ok})
        except Exception as e:rows.append({"path":p,"pass":False,"error":str(e)})
    return {"count":len(rows),"pass_count":sum(x["pass"] for x in rows),"rows":rows,"status":"PASS" if all(x["pass"] for x in rows) else "FAIL"}

def verify_stls(base:Path=LANE)->dict[str,Any]:
    rows=[]
    for p in STL_FILES:
        try:
            with (base/p).open("rb") as f: raw=trimesh.exchange.stl.load_stl_binary(f)
            m=trimesh.Trimesh(vertices=raw["vertices"],faces=raw["faces"],process=False);m.merge_vertices();deg=int((m.area_faces<=1e-10).sum());ok=m.is_watertight and m.body_count==1 and m.volume>0 and deg==0;rows.append({"path":p,"watertight":bool(m.is_watertight),"components":int(m.body_count),"degenerate":deg,"pass":bool(ok)})
        except Exception as e:rows.append({"path":p,"pass":False,"error":str(e)})
    return {"count":len(rows),"pass_count":sum(x["pass"] for x in rows),"rows":rows,"status":"PASS" if all(x["pass"] for x in rows) else "FAIL"}

def verify_svgs(base:Path=LANE)->dict[str,Any]:
    import xml.etree.ElementTree as ET; rows=[]
    for p in SVG_FILES:
        try:r=ET.parse(base/p).getroot();ok=r.tag.endswith("svg") and r.get("viewBox") is not None;rows.append({"path":p,"pass":ok})
        except Exception as e:rows.append({"path":p,"pass":False,"error":str(e)})
    return {"count":len(rows),"pass_count":sum(x["pass"] for x in rows),"status":"PASS" if all(x["pass"] for x in rows) else "FAIL"}

def commit_text()->str:return "\n".join(f"{LANE_REL}/{p}" for p in PATHS)
def manifest_text()->str:return "\n".join(f"{p}|{'PRINT_BLOCKED_REFERENCE' if p.endswith('.stl') and 'COUPON' not in p else 'H23_HANDOFF_RECORD'}" for p in PATHS)
def sums(base:Path=LANE)->str:return "\n".join(f"{sha(base/p)}  {p}" for p in PATHS if p!="SHA256SUMS.txt")

def verify_ledgers(base:Path=LANE)->dict[str,Any]:
    man=[x.split("|",1)[0] for x in (base/"MANIFEST.txt").read_text(encoding="utf-8").splitlines()]; vals={}
    for line in (base/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line: d,p=line.split("  ",1);vals[p]=d
    mis=[p for p,d in vals.items() if not (base/p).is_file() or sha(base/p)!=d];ok=man==list(PATHS) and set(vals)==set(PATHS)-{"SHA256SUMS.txt"} and not mis
    return {"manifest_count":len(man),"hash_count":len(vals),"mismatches":mis,"status":"PASS" if ok else "FAIL"}

def refresh()->dict[str,Any]:
    for p in SOURCE_FILES:
        if not (LANE/p).is_file():raise RuntimeError("source missing "+p)
    repo=repo_audit(False);pa=parent_audit(True);a=analysis();export_all();steps=verify_steps();stls=verify_stls();sv=verify_svgs();m=manifest(repo,pa,a,stls["status"]=="PASS")
    for p,t in documents(m).items():wt(LANE/p,t)
    wj(LANE/"geometry_manifest.json",m);wj(LANE/"validation_report.json",{"document_id":DOC_ID,"artifact_contract":"PASS" if steps["status"]==stls["status"]==sv["status"]=="PASS" else "FAIL","design_status":m["design_status"],"physical_fit":"BLOCKED","powered_rotation":"NOT_APPROVED","status":"FAIL"})
    wt(LANE/"COMMIT_PATHS.txt",commit_text());wt(LANE/"MANIFEST.txt",manifest_text());wt(LANE/"build_log.txt",f"coupon_first=PASS\nstep={steps['pass_count']}/{steps['count']}\nstl={stls['pass_count']}/{stls['count']}\nsvg={sv['pass_count']}/{sv['count']}\ndesign_status={m['design_status']}\nphysical_test=COUPONS_ONLY")
    wt(LANE/"test_log.txt","status=PREPACKAGE_SELF_CHECKS_PASS\nexpected_design_status=FAIL_RECORDED\ncontract_tests=RUN_DURING_PACKAGE")
    wt(LANE/"SHA256SUMS.txt",sums())
    if files()!=sorted(PATHS):raise RuntimeError({"actual":files(),"expected":sorted(PATHS)})
    led=verify_ledgers()
    if steps["status"]!=stls["status"] or steps["status"]!="PASS" or sv["status"]!="PASS" or led["status"]!="PASS":raise RuntimeError({"step":steps,"stl":stls,"svg":sv,"ledger":led})
    return {"artifact_contract":"PASS","design_status":m["design_status"],"formal_paths":len(PATHS),"STEP":f"{steps['pass_count']}/{steps['count']} PASS","STL":f"{stls['pass_count']}/{stls['count']} PASS","SVG":f"{sv['pass_count']}/{sv['count']} PASS"}

def verify()->dict[str,Any]:
    if files()!=sorted(PATHS):raise RuntimeError({"actual":files(),"expected":sorted(PATHS)})
    repo=repo_audit(True);pa=parent_audit();s=verify_steps();t=verify_stls();v=verify_svgs();l=verify_ledgers();m=json.loads((LANE/"geometry_manifest.json").read_text(encoding="utf-8"));checks={"design_fail_recorded":m["design_status"].startswith("FAIL_"),"external_preserved":not m["external_tooth_geometry_changed"] and m["parent_minus_final_external_volume"]<=1e-6 and m["final_minus_parent_external_volume"]<=1e-6,"walls":min(m["minimum_reaction_wall"],m["minimum_adjacent_pocket_wall"],m["minimum_pocket_to_m4_wall"],m["minimum_pocket_to_bore_wall"])>=3,"washer_fail":not m["analysis"]["washer"]["full_support"]}
    if s["status"]!=t["status"] or s["status"]!="PASS" or v["status"]!="PASS" or l["status"]!="PASS" or not all(checks.values()):raise RuntimeError({"checks":checks})
    return {"repository":repo,"parent":pa["status"],"artifact_contract":"PASS","design_status":m["design_status"],"formal_paths":len(PATHS),"STEP":f"{s['pass_count']}/{s['count']} PASS","STL":f"{t['pass_count']}/{t['count']} PASS","SVG":f"{v['pass_count']}/{v['count']} PASS","manifest":f"{l['manifest_count']}/{len(PATHS)} PASS","hashes":f"{l['hash_count']}/{len(PATHS)-1} PASS"}

def zi(p:str)->zipfile.ZipInfo:
    i=zipfile.ZipInfo(p,date_time=(2000,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;return i
def write_zip(path:Path)->None:
    with zipfile.ZipFile(path,"x") as z:
        for p in PATHS:z.writestr(zi(p),(LANE/p).read_bytes())
def verify_zip(path:Path,standalone:bool=True)->dict[str,Any]:
    with zipfile.ZipFile(path) as z:
        names=z.namelist();dups=sorted({x for x in names if names.count(x)>1});trav=[x for x in names if PurePosixPath(x).is_absolute() or ".." in PurePosixPath(x).parts or "\\" in x];vals={}
        for line in z.read("SHA256SUMS.txt").decode().splitlines():d,p=line.split("  ",1);vals[p]=d
        internal=[p for p,d in vals.items() if hashlib.sha256(z.read(p)).hexdigest()!=d];lane_mis=[p for p in names if hashlib.sha256(z.read(p)).hexdigest()!=sha(LANE/p)]
    st="NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="h23_zip_") as td:
            with zipfile.ZipFile(path) as z:z.extractall(td)
            env=dict(os.environ);env["V09372_TEST_ZIP"]=str(path);b=run([sys.executable,"-B",SOURCE_FILES[0],"--verify"],Path(td),env);t=run([sys.executable,"-B",SOURCE_FILES[1]],Path(td),env)
            if b.returncode or t.returncode:raise RuntimeError({"build":b.stdout,"tests":t.stdout})
            st="PASS"
    if names!=list(PATHS) or dups or trav or internal or lane_mis:raise RuntimeError({"names":names==list(PATHS),"dups":dups,"trav":trav,"internal":internal,"lane":lane_mis})
    return {"zip_path":str(path),"entry_count":len(names),"duplicates":dups,"path_traversal":trav,"internal_hash":"PASS","lane_byte_match":"PASS","standalone":st,"zip_sha256":sha(path),"status":"PASS"}

def package()->dict[str,Any]:
    verify();DOWNLOADS.mkdir(parents=True,exist_ok=True);stamp=datetime.now().strftime("%Y%m%d_%H%M%S");final=DOWNLOADS/f"{ZIP_PREFIX}{stamp}.zip";tmp=DOWNLOADS/f".{ZIP_PREFIX}{stamp}.tmp"
    try:
        wt(LANE/"test_log.txt","status=PACKAGE_TESTS_PENDING\nexpected_design_status=FAIL_RECORDED");wt(LANE/"SHA256SUMS.txt",sums());write_zip(tmp);env=dict(os.environ);env["V09372_TEST_ZIP"]=str(tmp);r=run([sys.executable,"-B",SOURCE_FILES[1]],LANE,env)
        if r.returncode:raise RuntimeError(r.stdout)
        summary=[x for x in r.stdout.splitlines() if x.startswith("Ran ") or x=="OK"];wt(LANE/"test_log.txt","status=PASS\n"+"\n".join(summary)+"\nexpected_design_status=FAIL_RECORDED\nfull_output:\n"+r.stdout);wt(LANE/"SHA256SUMS.txt",sums());verify()
    finally:
        if tmp.exists():tmp.unlink()
    write_zip(final);return verify_zip(final,True)

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--refresh-artifacts",action="store_true");p.add_argument("--verify",action="store_true");p.add_argument("--package",action="store_true");p.add_argument("--verify-zip",type=Path);a=p.parse_args(argv)
    if sum((a.refresh_artifacts,a.verify,a.package,a.verify_zip is not None))!=1:p.error("choose one action")
    result=refresh() if a.refresh_artifacts else verify() if a.verify else package() if a.package else verify_zip(a.verify_zip,True);print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
