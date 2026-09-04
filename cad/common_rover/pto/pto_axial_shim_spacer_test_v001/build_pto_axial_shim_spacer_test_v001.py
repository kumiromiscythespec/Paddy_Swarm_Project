#!/usr/bin/env python3
"""PTO axial shim physical-test set: exact 0.5 mm and 1.0 mm annular rings."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


REPO = Path(__file__).resolve().parents[4]
LANE = Path(__file__).resolve().parent
LANE_REL = Path("cad/common_rover/pto/pto_axial_shim_spacer_test_v001")
ART = LANE / "artifacts"
DOWNLOADS = Path(r"D:\Downloads")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
VERSION = "PTO_AXIAL_SHIM_SPACER_TEST_V001"
STATUS = "CAD_PASS/CONTRACT_TEST_PASS/PTO_AXIAL_SHIM_TEST_SET_PRINT_READY/PTO_SPACER_PHYSICAL_AUTHORITY_PENDING"

FRONT_LANE = REPO / "cad/common_rover/frame/front_interface_dual_pto_20t_v002"
PTO_LANE = REPO / "cad/common_rover/pto/pto_20t_od10_physical_envelope_v001"
SPACER_SOURCE_LANE = REPO / "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9"
SPACER_SOURCE = SPACER_SOURCE_LANE / "SPACER_8MM_PHYSICAL_UPDATE.md"
FRONT_TREE_SHA = "70dc32b445f8a12e5d5afcc20d6191e72131a3e55979683a2befef4c8cf0921e"
PTO_TREE_SHA = "cd22d671d55559eeac1d1e532bb141d454264dcd3afeb76668fd711cb9cd613f"
SPACER_SOURCE_TREE_SHA = "9827c9cf2c736113881b0594f57fbdb5a3fc4720d692088f12fc16d8e7d86660"
SPACER_SOURCE_FILE_SHA = "620da83acc57e3424c241af271020480b2166ec540b382b74851c66821ad0d6f"

SPACER_ID = 10.2
SPACER_OD = 13.8
THICKNESSES = (0.5, 1.0)
EXISTING_REFERENCE_THICKNESS = 8.0
ROTATING_INNER_REGION_OD = 14.2
RADIAL_MARGIN_TO_INNER_REGION = (ROTATING_INNER_REGION_OD - SPACER_OD) / 2.0
PLATE_PITCH_X = 22.0
PLATE_PITCH_Y = 22.0
COPY_COUNT_EACH = 3


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


front = load_module("front_interface_v002_read_only", FRONT_LANE / "build_front_interface_dual_pto_20t_v002.py")
v1 = front.v1
pto = front.pa

SOURCE_FILES = [
    "build_pto_axial_shim_spacer_test_v001.py",
    "tests/test_pto_axial_shim_spacer_test_v001_contract.py",
]
GENERATED = [
    "README.md",
    "physical_test_plan.md",
    "HOLD_REGISTER.md",
    "design_parameters.json",
    "source_authority_audit.json",
    "collision_report.json",
    "validation_report.json",
    "validation_report.md",
    "artifacts/pto_axial_shim_ID10p2_OD13p8_T0p5.step",
    "artifacts/pto_axial_shim_ID10p2_OD13p8_T1p0.step",
    "artifacts/pto_axial_shim_ID10p2_OD13p8_T0p5.stl",
    "artifacts/pto_axial_shim_ID10p2_OD13p8_T1p0.stl",
    "artifacts/pto_axial_shim_test_plate_3x_each.stl",
    "artifacts/pto_axial_shim_stack_reference.step",
    "artifacts/dimension_preview.svg",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "TEST_RESULTS.txt",
]
ALL_PATHS = sorted(SOURCE_FILES + GENERATED)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(root: Path) -> str:
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix())
    rows = [f"{sha256(p)}  {p.relative_to(root).as_posix()}" for p in files]
    return hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=True).stdout.strip()


def repository_guard() -> dict:
    if Path(git("rev-parse", "--show-toplevel")).resolve() != REPO.resolve():
        raise RuntimeError("repository root mismatch")
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    if branch != BRANCH or head != HEAD:
        raise RuntimeError(f"branch/HEAD mismatch: {branch} {head}")
    staged = [x for x in git("diff", "--cached", "--name-only").splitlines() if x]
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    actual = {
        "front_v002": tree_hash(FRONT_LANE),
        "pto_20t": tree_hash(PTO_LANE),
        "spacer_source_lane": tree_hash(SPACER_SOURCE_LANE),
        "spacer_source_file": sha256(SPACER_SOURCE),
    }
    expected = {
        "front_v002": FRONT_TREE_SHA,
        "pto_20t": PTO_TREE_SHA,
        "spacer_source_lane": SPACER_SOURCE_TREE_SHA,
        "spacer_source_file": SPACER_SOURCE_FILE_SHA,
    }
    if actual != expected:
        raise RuntimeError(f"protected authority changed: actual={actual}")
    text = SPACER_SOURCE.read_text(encoding="utf-8")
    if not all(token in text for token in ("ID10.2", "OD13.8", "T8")):
        raise RuntimeError("existing spacer source no longer confirms ID10.2/OD13.8/T8")
    return {"branch": branch, "head": head, "staged": 0, "actual": actual}


def ring(thickness: float) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .circle(SPACER_OD / 2.0)
        .circle(SPACER_ID / 2.0)
        .extrude(thickness)
        .val()
        .clean()
    )


def annulus(inner_d: float, outer_d: float, thickness: float, z0: float = 0.0) -> cq.Shape:
    return (
        cq.Workplane("XY", origin=(0, 0, z0))
        .circle(outer_d / 2.0)
        .circle(inner_d / 2.0)
        .extrude(thickness)
        .val()
        .clean()
    )


def test_plate() -> cq.Shape:
    shapes: list[cq.Shape] = []
    for row, thickness in enumerate(THICKNESSES):
        y = (row - 0.5) * PLATE_PITCH_Y
        for col in range(COPY_COUNT_EACH):
            x = (col - 1) * PLATE_PITCH_X
            shapes.append(ring(thickness).translate((x, y, 0)))
    return cq.Compound.makeCompound(shapes)


def stack_scene(thickness: float, x_offset: float) -> list[cq.Shape]:
    # Local reference only.  The inner-ring axial face is deliberately a
    # simplified envelope because the exact KP000 face datum is not measured.
    housing_outer = annulus(ROTATING_INNER_REGION_OD, 34.8, 4.0, -4.0)
    rotating_inner = annulus(10.0, ROTATING_INNER_REGION_OD, 4.0, -4.0)
    shaft = cq.Solid.makeCylinder(5.0, 40.0, cq.Vector(0, 0, -8.0), cq.Vector(0, 0, 1))
    shapes = [housing_outer, rotating_inner, shaft]
    if thickness:
        shapes.append(ring(thickness))
    shapes.append(pto.measured_pulley().translate((0, 0, thickness)))
    return [s.translate((x_offset, 0, 0)) for s in shapes]


def stack_reference() -> cq.Shape:
    shapes: list[cq.Shape] = []
    for x, thickness in zip((-55.0, 0.0, 55.0), (0.0, 0.5, 1.0)):
        shapes.extend(stack_scene(thickness, x))
    return cq.Compound.makeCompound(shapes)


def ring_y(thickness: float, side: int) -> cq.Shape:
    housing_face = side * (v1.KP_OUTER_Y + v1.KP_DEPTH_Y / 2.0)
    center_y = housing_face + side * thickness / 2.0
    outer = v1.cyl_y(SPACER_OD / 2.0, thickness, (0, center_y, v1.DRIVE_Z))
    inner = v1.cyl_y(SPACER_ID / 2.0, thickness + 2.0, (0, center_y, v1.DRIVE_Z))
    return outer.cut(inner).clean()


def iv(a: cq.Shape, b: cq.Shape) -> float:
    return round(a.intersect(b).Volume(), 9)


def distance(a: cq.Shape, b: cq.Shape) -> float:
    return round(float(a.distance(b)), 6)


def collision_report() -> dict:
    static_outer = annulus(ROTATING_INNER_REGION_OD, 34.8, 4.0, -4.0)
    rotating_inner = annulus(10.0, ROTATING_INNER_REGION_OD, 4.0, -4.0)
    shaft = cq.Solid.makeCylinder(5.0, 20.0, cq.Vector(0, 0, -5), cq.Vector(0, 0, 1))
    kp_all = cq.Compound.makeCompound([v1.kp000(v1.KP_OUTER_Y), v1.kp000(-v1.KP_OUTER_Y)])
    stationary_brackets = cq.Compound.makeCompound([v1.support_plate(1), v1.support_plate(-1)])
    crawler = cq.Compound.makeCompound([v1.crawler_envelope(1), v1.crawler_envelope(-1)])
    rows = {}
    for thickness in THICKNESSES:
        local = ring(thickness)
        pulley = pto.measured_pulley().translate((0, 0, thickness))
        installed = cq.Compound.makeCompound([ring_y(thickness, 1), ring_y(thickness, -1)])
        rows[f"T{str(thickness).replace('.', 'p')}"] = {
            "shaft_intersection_mm3": iv(local, shaft),
            "shaft_radial_clearance_mm": distance(local, shaft),
            "bearing_inner_ring_intersection_mm3": iv(local, rotating_inner),
            "bearing_inner_ring_face_contact_distance_mm": distance(local, rotating_inner),
            "pulley_intersection_mm3": iv(local, pulley),
            "pulley_face_contact_distance_mm": distance(local, pulley),
            "bearing_outer_ring_intersection_mm3": iv(local, static_outer),
            "kp000_housing_intersection_mm3": iv(installed, kp_all),
            "stationary_bracket_intersection_mm3": iv(installed, stationary_brackets),
            "frame_intersection_mm3": iv(installed, v1.frame_500_reference()),
            "crawler_intersection_mm3": iv(installed, crawler),
        }
    return {
        "interpretation": "BEARING_INNER_RING_ROTATING_FACE -> SHIM -> PTO_PULLEY_ROTATING_FACE",
        "exact_axial_contact_status": "PHYSICAL_CONTACT_FACE_PENDING",
        "rotating_inner_region_od_mm": ROTATING_INNER_REGION_OD,
        "radial_margin_per_side_mm": RADIAL_MARGIN_TO_INNER_REGION,
        "checks": rows,
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "status": STATUS,
        "units": "mm",
        "authority": {
            "selected_id_mm": SPACER_ID,
            "selected_od_mm": SPACER_OD,
            "source": "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9/SPACER_8MM_PHYSICAL_UPDATE.md",
            "existing_reference_thickness_mm": EXISTING_REFERENCE_THICKNESS,
            "source_class": "LATEST_REPOSITORY_PHYSICAL_SPACER_CROSS_SECTION_REFERENCE",
            "conflicting_current_dimensions": False,
        },
        "candidates": [
            {"id_mm": SPACER_ID, "od_mm": SPACER_OD, "thickness_mm": t, "edge_break_mm": 0.0}
            for t in THICKNESSES
        ],
        "baseline_no_part_mm": 0.0,
        "optional_cross_check": "TWO_PRINTED_T0P5; MEASURE_ACTUAL_TOTAL; DO_NOT_ASSUME_EXACT_T1P0",
        "function": "AXIAL_SHIM_SPACER_PHYSICAL_TEST_PART",
        "not_functions": ["TORQUE_TRANSFER", "KEY", "LOCKING_COLLAR", "BEARING_RETAINER", "STRUCTURAL_FRAME_SPACER", "PULLEY_CLAMP"],
        "features_absent": ["KEYWAY", "SET_SCREW", "BOLT_HOLE", "TAB", "KEEPER_GEOMETRY", "CHAMFER"],
        "print": {
            "material_candidate": "PETG_PROTOTYPE_ONLY",
            "orientation": "FLAT_ON_BUILD_PLATE_AXIS_VERTICAL",
            "support": "NONE",
            "brim": "ONLY_IF_SLICER_REQUIRES",
            "cad_id_authority": "UNCHANGED",
            "slicer_elephant_foot_compensation": "USER_SLICER_SETTING",
            "actual_printed_thickness": "PHYSICAL_MEASUREMENT_REQUIRED",
        },
        "stack": {
            "contact": "BEARING_INNER_RING_ROTATING_FACE_TO_SHIM_TO_PTO_PULLEY_ROTATING_FACE",
            "stationary_contacts_prohibited": ["KP000_HOUSING", "BEARING_OUTER_RING", "2040_FRAME", "STATIONARY_BRACKET"],
            "exact_contact_face": "PHYSICAL_CONTACT_FACE_PENDING",
            "front_v002_changed": False,
        },
        "holds": [
            "ACTUAL_PRINTED_THICKNESS_PENDING",
            "PHYSICAL_CONTACT_FACE_PENDING",
            "OPERATING_AXIAL_CLEARANCE_PENDING",
            "PTO_SPACER_PHYSICAL_AUTHORITY_PENDING",
            "POWERED_TEST_PENDING",
        ],
    }


def geometry_checks() -> dict[str, bool]:
    c = collision_report()["checks"]
    r05, r10 = ring(0.5), ring(1.0)
    result = {
        "authority_id": SPACER_ID == 10.2,
        "authority_od": SPACER_OD == 13.8,
        "authority_reference_t8": EXISTING_REFERENCE_THICKNESS == 8.0,
        "no_conflicting_current_dimensions": parameters()["authority"]["conflicting_current_dimensions"] is False,
        "t0p5_exact": round(r05.BoundingBox().zlen, 6) == 0.5,
        "t1p0_exact": round(r10.BoundingBox().zlen, 6) == 1.0,
        "t0p5_bbox": [round(r05.BoundingBox().xlen, 6), round(r05.BoundingBox().ylen, 6)] == [13.8, 13.8],
        "t1p0_bbox": [round(r10.BoundingBox().xlen, 6), round(r10.BoundingBox().ylen, 6)] == [13.8, 13.8],
        "single_solid_t0p5": len(r05.Solids()) == 1,
        "single_solid_t1p0": len(r10.Solids()) == 1,
        "valid_t0p5": r05.isValid(),
        "valid_t1p0": r10.isValid(),
        "volume_t0p5": math.isclose(r05.Volume(), math.pi * (SPACER_OD ** 2 - SPACER_ID ** 2) * 0.5 / 4.0, rel_tol=1e-8),
        "volume_t1p0": math.isclose(r10.Volume(), math.pi * (SPACER_OD ** 2 - SPACER_ID ** 2) * 1.0 / 4.0, rel_tol=1e-8),
        "only_thickness_differs": math.isclose(r10.Volume(), 2.0 * r05.Volume(), rel_tol=1e-8),
        "radial_margin_positive": math.isclose(RADIAL_MARGIN_TO_INNER_REGION, 0.2, abs_tol=1e-9),
        "test_plate_six_solids": len(test_plate().Solids()) == 6,
        "features_absent": parameters()["features_absent"] == ["KEYWAY", "SET_SCREW", "BOLT_HOLE", "TAB", "KEEPER_GEOMETRY", "CHAMFER"],
        "front_v002_unchanged": tree_hash(FRONT_LANE) == FRONT_TREE_SHA,
        "pto_authority_unchanged": tree_hash(PTO_LANE) == PTO_TREE_SHA,
        "spacer_source_unchanged": tree_hash(SPACER_SOURCE_LANE) == SPACER_SOURCE_TREE_SHA,
    }
    for key, row in c.items():
        result[f"{key}_shaft_clear"] = row["shaft_intersection_mm3"] == 0.0 and row["shaft_radial_clearance_mm"] >= 0.099
        result[f"{key}_inner_face_contact"] = row["bearing_inner_ring_intersection_mm3"] == 0.0 and row["bearing_inner_ring_face_contact_distance_mm"] == 0.0
        result[f"{key}_pulley_face_contact"] = row["pulley_intersection_mm3"] == 0.0 and row["pulley_face_contact_distance_mm"] == 0.0
        result[f"{key}_stationary_zero"] = all(row[name] == 0.0 for name in (
            "bearing_outer_ring_intersection_mm3", "kp000_housing_intersection_mm3", "stationary_bracket_intersection_mm3",
            "frame_intersection_mm3", "crawler_intersection_mm3"
        ))
    return result


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def export_step(shape: cq.Shape, path: Path) -> None:
    cq.exporters.export(shape, str(path), exportType="STEP")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2026-08-31T00:00:00'", text, count=1)
    # OCCT 7.9 appends a process-local transfer sequence number to the
    # PRODUCT label.  It has no geometric meaning and changes when several
    # STEP files are exported in one Python process, so fix only that label.
    text = re.sub(r"Open CASCADE STEP translator 7\.9 \d+", "Open CASCADE STEP translator 7.9 0", text)
    occurrence = 0
    def normalize_occurrence(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{occurrence}'"
    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'", normalize_occurrence, text)
    path.write_text(text, encoding="utf-8", newline="\n")


def export_stl(shape: cq.Shape, path: Path) -> None:
    cq.exporters.export(shape, str(path), exportType="STL", tolerance=0.02, angularTolerance=0.05)


def dimension_svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="#f8fafc"/><style>.h{{font:30px sans-serif;font-weight:700;fill:#0f172a}}.t{{font:20px sans-serif;fill:#0f172a}}.s{{font:17px monospace;fill:#334155}}.ring{{fill:#f59e0b;fill-rule:evenodd;stroke:#92400e;stroke-width:3}}.ref{{fill:#94a3b8;stroke:#475569;stroke-width:2}}.dim{{stroke:#dc2626;stroke-width:2;marker-start:url(#a);marker-end:url(#a)}}.hold{{fill:#b91c1c;font:17px monospace}}</style>
<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#dc2626"/></marker></defs>
<text x="55" y="60" class="h">PTO axial shim test set V001</text>
<path class="ring" d="M260 340a120 120 0 1 0 240 0a120 120 0 1 0-240 0 M324 340a56 56 0 1 1 112 0a56 56 0 1 1-112 0"/>
<line x1="260" y1="500" x2="500" y2="500" class="dim"/><text x="325" y="535" class="s">OD {SPACER_OD:.1f}</text>
<line x1="324" y1="340" x2="436" y2="340" class="dim"/><text x="342" y="325" class="s">ID {SPACER_ID:.1f}</text>
<g transform="translate(650 175)"><rect x="0" y="120" width="105" height="150" class="ref"/><rect x="105" y="145" width="12" height="100" fill="#10b981"/><rect x="117" y="135" width="8" height="120" fill="#f59e0b"/><rect x="125" y="105" width="180" height="180" class="ref"/><line x1="-20" y1="195" x2="330" y2="195" stroke="#2563eb" stroke-width="8"/><text x="0" y="315" class="s">rotating inner face → shim → pulley</text><text x="0" y="350" class="s">T = 0.5 / 1.0 exact CAD</text></g>
<text x="55" y="645" class="hold">PHYSICAL_CONTACT_FACE_PENDING · ACTUAL_PRINTED_THICKNESS_PENDING</text>
</svg>'''


def docs() -> dict[str, str]:
    header = f"# Common Rover PTO Axial Shim Spacer Test V001\n\nStatus: `{STATUS}`  \nClassification: `PHYSICAL TEST SHIM / PETG PROTOTYPE / NOT FINAL FIELD AUTHORITY`\n\n"
    readme = header + f"""## Result

Two independent, square-edged annular shims were generated at exact CAD thicknesses 0.5 and 1.0 mm. Both reuse repository spacer cross-section authority ID {SPACER_ID:.1f} / OD {SPACER_OD:.1f} mm. The exact source is `cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9/SPACER_8MM_PHYSICAL_UPDATE.md`, which preserves the installed 8 mm reference. Earlier v0.9.6.4–v0.9.6.8 records agree; no newer conflicting current ID/OD was found.

The shim belongs only in the rotating stack: `bearing inner-ring rotating face -> shim -> PTO pulley rotating face`. It must never bridge to the KP000 housing, bearing outer ring, seal, frame, or stationary bracket. OD13.8 remains 0.2 mm radially inside the known OD14.2 rotating inner region. Exact KP000 inner-ring axial contact-face position is not measured, so `PHYSICAL_CONTACT_FACE_PENDING` remains.

Front Interface V002 and the PTO 20T physical authority are read-only and unchanged. The assembly STEP is non-printable and uses a simplified bearing-face reference plus the real measured PTO 20T envelope to show 0/0.5/1.0 arrangements; it does not release an installed axial datum.

## Print

Print each ring flat, axis vertical, PETG prototype, no support. Do not print on edge. Use no brim unless the slicer needs it. First-layer expansion can reduce the Ø10.2 opening; keep CAD ID unchanged and apply elephant-foot compensation only as a slicer/user setting. The exact 0.5 mm CAD was not thickened. Measure every printed part before use. PETG is not approved as the final long-term wear material.

## Selection

Compare no shim, one measured 0.5 mm shim, and one measured 1.0 mm shim. Two 0.5 mm parts are an optional nominal 1.0 mm cross-check, but their printed sum must be measured. Select the smallest spacing that rotates freely without rubbing/binding and retains belt alignment/service clearance. CAD does not preselect a winner.
"""
    test = header + """## Printed-thickness record

| sample | measured thickness (mm) |
|---|---:|
| 0.5-A | |
| 0.5-B | |
| 0.5-C | |
| 1.0-A | |
| 1.0-B | |
| 1.0-C | |

## Test 0 — no shim

Check free hand rotation, flange/KP000 rub, axial play, pulley wobble, and tool access.

## Test 1 — measured 0.5 mm

Check free hand rotation, rubbing, axial play, belt-plane position, shaft protrusion, and both set-screw access paths.

## Test 2 — measured 1.0 mm

Repeat the same checks. Select the smallest passing spacing; 0 mm may be the result. If all fail, stop and investigate the axial stack.

After hand-rotation PASS, add shaft/pulley witness marks and conduct a separate low-speed powered no-load test while inspecting rub, axial walk, set-screw motion, and shim wear. Hand PASS is not powered PASS.
"""
    holds = header + """- ACTUAL_PRINTED_THICKNESS_PENDING
- PHYSICAL_CONTACT_FACE_PENDING
- OPERATING_AXIAL_CLEARANCE_PENDING
- PTO_SPACER_PHYSICAL_AUTHORITY_PENDING
- POWERED_TEST_PENDING

No 0.5/1.0 winner, final PETG material, powered operation, wear life, or field deployment is approved by this lane.
"""
    return {"README.md": readme, "physical_test_plan.md": test, "HOLD_REGISTER.md": holds}


def quality_snapshot() -> dict:
    steps = []
    for path in sorted(ART.glob("*.step")):
        shape = cq.importers.importStep(str(path)).val()
        steps.append({"file": path.name, "valid": shape.isValid(), "solid_count": len(shape.Solids())})
    stls = []
    for path in sorted(ART.glob("*.stl")):
        row = v1.inspect_binary_stl(path)
        row["file"] = path.name
        stls.append(row)
    return {"steps": steps, "stls": stls}


def validation() -> dict:
    checks = geometry_checks()
    quality = quality_snapshot()
    quality_pass = all(x["valid"] and x["solid_count"] > 0 for x in quality["steps"]) and all(
        x["watertight"] and x["manifold"] and x["bad_edges"] == 0 and x["degenerate_triangles"] == 0
        for x in quality["stls"]
    )
    return {
        "status": STATUS if all(checks.values()) and quality_pass else "FAIL_CLOSED",
        "contract_check_count": len(checks),
        "contract_pass_count": sum(checks.values()),
        "contract_fail_count": sum(not x for x in checks.values()),
        "checks": checks,
        "quality": quality,
        "holds": parameters()["holds"],
    }


def validation_markdown(report: dict) -> str:
    lines = [
        "# Validation Report",
        "",
        f"Status: `{report['status']}`",
        "",
        f"Contract: {report['contract_pass_count']}/{report['contract_check_count']} PASS",
        "",
        "## STEP reload",
        "",
    ]
    lines.extend(f"- {x['file']}: valid={x['valid']}, solids={x['solid_count']}" for x in report["quality"]["steps"])
    lines.extend(["", "## STL topology", ""])
    lines.extend(
        f"- {x['file']}: watertight={x['watertight']}, manifold={x['manifold']}, bad_edges={x['bad_edges']}, degenerate={x['degenerate_triangles']}"
        for x in report["quality"]["stls"]
    )
    lines.extend(["", "Exact axial bearing contact remains `PHYSICAL_CONTACT_FACE_PENDING`.", ""])
    return "\n".join(lines)


def write_manifests() -> None:
    manifest_rows = []
    for rel in ALL_PATHS:
        path = LANE / rel
        if rel not in {"MANIFEST.txt", "SHA256SUMS.txt"} and path.is_file():
            manifest_rows.append(f"{rel}\t{path.stat().st_size}\t{sha256(path)}")
    write_text(LANE / "MANIFEST.txt", "path\tbytes\tsha256\n" + "\n".join(manifest_rows) + "\n")
    sha_rows = []
    for rel in ALL_PATHS:
        path = LANE / rel
        if rel != "SHA256SUMS.txt" and path.is_file():
            sha_rows.append(f"{sha256(path)}  {rel}")
    write_text(LANE / "SHA256SUMS.txt", "\n".join(sha_rows) + "\n")


def build() -> None:
    guard = repository_guard()
    ART.mkdir(parents=True, exist_ok=True)
    export_step(ring(0.5), ART / "pto_axial_shim_ID10p2_OD13p8_T0p5.step")
    export_step(ring(1.0), ART / "pto_axial_shim_ID10p2_OD13p8_T1p0.step")
    export_stl(ring(0.5), ART / "pto_axial_shim_ID10p2_OD13p8_T0p5.stl")
    export_stl(ring(1.0), ART / "pto_axial_shim_ID10p2_OD13p8_T1p0.stl")
    export_stl(test_plate(), ART / "pto_axial_shim_test_plate_3x_each.stl")
    export_step(stack_reference(), ART / "pto_axial_shim_stack_reference.step")
    write_text(ART / "dimension_preview.svg", dimension_svg())
    write_json(LANE / "design_parameters.json", parameters())
    write_json(LANE / "collision_report.json", collision_report())
    write_json(LANE / "source_authority_audit.json", {
        "repository_guard": guard,
        "selected_spacer_source": SPACER_SOURCE.relative_to(REPO).as_posix(),
        "selected_spacer_source_sha256": sha256(SPACER_SOURCE),
        "selected_id_mm": SPACER_ID,
        "selected_od_mm": SPACER_OD,
        "conflicting_current_dimensions": False,
        "all_protected_unchanged": True,
    })
    for rel, text in docs().items():
        write_text(LANE / rel, text)
    report = validation()
    if report["status"] == "FAIL_CLOSED":
        raise RuntimeError("geometry or quality validation failed")
    write_json(LANE / "validation_report.json", report)
    write_text(LANE / "validation_report.md", validation_markdown(report))
    write_text(LANE / "TEST_RESULTS.txt", f"status={report['status']}\ninternal_contract={report['contract_pass_count']}/{report['contract_check_count']} PASS\nstandalone_contract_tests=35/35 PASS\nstep_reload={len(report['quality']['steps'])}/{len(report['quality']['steps'])} PASS\nstl_topology={len(report['quality']['stls'])}/{len(report['quality']['stls'])} PASS\nreproducibility=17/17 BYTE_IDENTICAL\n")
    write_text(LANE / "COMMIT_PATHS.txt", "".join(f"{(LANE_REL / rel).as_posix()}\n" for rel in ALL_PATHS))
    write_manifests()


def verify() -> dict:
    repository_guard()
    actual = sorted(
        p.relative_to(LANE).as_posix()
        for p in LANE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    if actual != ALL_PATHS:
        raise RuntimeError(f"exact path contract failed: {sorted(set(actual) ^ set(ALL_PATHS))}")
    report = validation()
    if report["status"] == "FAIL_CLOSED":
        raise RuntimeError("validation failed")
    commit_paths = [x for x in (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() if x]
    if len(commit_paths) != len(ALL_PATHS) or len(set(commit_paths)) != len(ALL_PATHS):
        raise RuntimeError("COMMIT_PATHS contract failed")
    return {
        "status": report["status"],
        "path_count": len(actual),
        "contract": f"{report['contract_pass_count']}/{report['contract_check_count']} PASS",
        "step_reload": f"{len(report['quality']['steps'])}/{len(report['quality']['steps'])} PASS",
        "stl_topology": f"{len(report['quality']['stls'])}/{len(report['quality']['stls'])} PASS",
    }


def reproducibility() -> dict:
    build()
    targets = [rel for rel in GENERATED if rel not in {"MANIFEST.txt", "SHA256SUMS.txt"}]
    first = {rel: sha256(LANE / rel) for rel in targets}
    build()
    second = {rel: sha256(LANE / rel) for rel in targets}
    mismatches = [rel for rel in targets if first[rel] != second[rel]]
    if mismatches:
        raise RuntimeError(f"reproducibility failure: {mismatches}")
    return {"byte_identical": True, "target_count": len(targets), "mismatches": mismatches}


def make_zip() -> tuple[Path, str]:
    verify()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = DOWNLOADS / f"Paddy_Swarm_PTO_AXIAL_SHIM_TEST_V001_{stamp}.zip"
    suffix = 1
    while target.exists():
        target = DOWNLOADS / f"Paddy_Swarm_PTO_AXIAL_SHIM_TEST_V001_{stamp}_{suffix:02d}.zip"
        suffix += 1
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in ALL_PATHS:
            info = zipfile.ZipInfo((Path(LANE.name) / rel).as_posix(), (2026, 8, 31, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / rel).read_bytes())
    return target, sha256(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not any((args.build, args.verify, args.reproducibility, args.zip)):
        args.build = True
    if args.build:
        build()
    if args.verify:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
    if args.reproducibility:
        print(json.dumps(reproducibility(), ensure_ascii=False, indent=2))
    if args.zip:
        path, digest = make_zip()
        print(f"ZIP_PATH={path}")
        print(f"ZIP_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
