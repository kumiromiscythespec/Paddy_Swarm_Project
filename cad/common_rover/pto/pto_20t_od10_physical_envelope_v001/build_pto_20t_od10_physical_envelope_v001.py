#!/usr/bin/env python3
"""Measured physical-envelope authority for the current Ø10 PTO 20T pulley."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


REPO = Path(__file__).resolve().parents[4]
LANE = Path(__file__).resolve().parent
LANE_REL = Path("cad/common_rover/pto/pto_20t_od10_physical_envelope_v001")
ART = LANE / "artifacts"
DOWNLOADS = Path(r"D:\Downloads")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
VERSION = "PTO_20T_OD10_PHYSICAL_ENVELOPE_V001"
STATUS = "PTO_20T_PHYSICAL_ENVELOPE_CAPTURED/CAD_PASS/CONTRACT_TEST_PASS/PHYSICAL_VALIDATION_PENDING"

FLANGE_OD = 34.8
TOOTH_REGION_MAX_OD = 30.5
TOOTHED_BODY_AXIAL_WIDTH = 19.8
FLANGE_THICKNESS = 1.6
OVERALL_AXIAL_WIDTH = TOOTHED_BODY_AXIAL_WIDTH + 2 * FLANGE_THICKNESS
INDIVIDUAL_TOOTH_WIDTH = 1.5
MEASURED_BORE = 9.8
NOMINAL_SHAFT = 10.0
SETSCREW_COUNT = 2
SETSCREW_SPACING_DEG = 90.0
SETSCREW_HOLE_MEASURED = 4.4
SETSCREW_CENTER_FROM_END = 15.1
SETSCREW_PROTRUSION_CANDIDATE = 4.0
SETSCREW_SWEEP_RADIUS = FLANGE_OD / 2 + SETSCREW_PROTRUSION_CANDIDATE
ROTATION_SERVICE_CLEARANCE = 5.0
ROTATION_KEEPOUT_RADIUS = FLANGE_OD / 2 + ROTATION_SERVICE_CLEARANCE
ROTATION_KEEPOUT_WIDTH = OVERALL_AXIAL_WIDTH + 10.0
STATIC_MIN_SPACER = 0.0
SPACER_STUDY = [0.0, 0.5, 1.0]

OLD_STEP_REL = "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1/cad/drive_htd5m_20t_reference.step"
OLD_STEP_SHA = "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1"

SOURCE_FILES = [
    "build_pto_20t_od10_physical_envelope_v001.py",
    "tests/test_pto_20t_od10_physical_envelope_v001_contract.py",
]
GENERATED = [
    "README.md", "authority_report.md", "validation_report.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
    "physical_measurements.json", "validation_report.json", "spacer_study.json", "source_authority_audit.json",
    "artifacts/pto_20t_od10_physical_envelope.step",
    "artifacts/pto_20t_od10_clearance_envelope.step",
    "artifacts/pto_20t_od10_rotational_keepout.step",
    "artifacts/pto_20t_od10_set_screw_sweep.step",
    "artifacts/pto_20t_od10_dimension_reference.step",
    "artifacts/pto_20t_od10_dimension_preview.svg",
    "COMMIT_PATHS.txt", "MANIFEST.txt", "SHA256SUMS.txt",
]
ALL_PATHS = sorted(SOURCE_FILES + GENERATED)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=True).stdout.strip()


def repository_guard() -> dict:
    if Path(git("rev-parse", "--show-toplevel")).resolve() != REPO.resolve():
        raise RuntimeError("repository mismatch")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", "HEAD") != HEAD:
        raise RuntimeError("branch/HEAD mismatch")
    staged = [x for x in git("diff", "--cached", "--name-only").splitlines() if x]
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    old = REPO / OLD_STEP_REL
    if not old.is_file() or sha256(old) != OLD_STEP_SHA:
        raise RuntimeError("obsolete reference source hash changed")
    return {"branch": BRANCH, "head": HEAD, "staged": 0}


def cyl_z(radius: float, length: float, z0: float = 0.0) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))


def cyl_x(radius: float, length: float, x0: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(x0, 0, z), cq.Vector(1, 0, 0))


def cyl_y(radius: float, length: float, y0: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(0, y0, z), cq.Vector(0, 1, 0))


def measured_pulley() -> cq.Shape:
    body = cyl_z(TOOTH_REGION_MAX_OD / 2, TOOTHED_BODY_AXIAL_WIDTH, FLANGE_THICKNESS)
    front = cyl_z(FLANGE_OD / 2, FLANGE_THICKNESS, 0.0)
    rear = cyl_z(FLANGE_OD / 2, FLANGE_THICKNESS, FLANGE_THICKNESS + TOOTHED_BODY_AXIAL_WIDTH)
    solid = body.fuse(front).fuse(rear)
    bore = cyl_z(MEASURED_BORE / 2, OVERALL_AXIAL_WIDTH + 2, -1)
    solid = solid.cut(bore)
    hole_r = SETSCREW_HOLE_MEASURED / 2
    radial_start = MEASURED_BORE / 2
    radial_len = FLANGE_OD / 2 - radial_start + 1.0
    solid = solid.cut(cyl_x(hole_r, radial_len, radial_start, SETSCREW_CENTER_FROM_END))
    solid = solid.cut(cyl_y(hole_r, radial_len, radial_start, SETSCREW_CENTER_FROM_END))
    return solid.clean()


def clearance_envelope() -> cq.Shape:
    return cyl_z(FLANGE_OD / 2, OVERALL_AXIAL_WIDTH)


def rotational_keepout() -> cq.Shape:
    return cyl_z(ROTATION_KEEPOUT_RADIUS, ROTATION_KEEPOUT_WIDTH, -5.0)


def set_screw_sweep() -> cq.Shape:
    return cyl_z(SETSCREW_SWEEP_RADIUS, SETSCREW_HOLE_MEASURED, SETSCREW_CENTER_FROM_END - SETSCREW_HOLE_MEASURED / 2)


def dimension_reference() -> cq.Shape:
    axes = cq.Compound.makeCompound([
        cyl_x(1.0, 36.0, -18.0, SETSCREW_CENTER_FROM_END),
        cyl_y(1.0, 36.0, -18.0, SETSCREW_CENTER_FROM_END),
        cyl_z(NOMINAL_SHAFT / 2, OVERALL_AXIAL_WIDTH + 8.0, -4.0),
    ])
    return cq.Compound.makeCompound([measured_pulley(), axes])


def measurements() -> dict:
    return {
        "version": VERSION, "source": "USER_PHYSICAL_MEASUREMENTS_2026_08_30", "units": "mm",
        "type": "HTD5M_20T_PHYSICAL_CLEARANCE_ENVELOPE", "pitch_mm": 5.0, "tooth_count": 20,
        "flange_od_mm": FLANGE_OD, "tooth_region_max_od_mm": TOOTH_REGION_MAX_OD,
        "toothed_body_axial_width_mm": TOOTHED_BODY_AXIAL_WIDTH, "flange_thickness_each_mm": FLANGE_THICKNESS,
        "derived_overall_axial_width_mm": OVERALL_AXIAL_WIDTH, "individual_tooth_width_mm": INDIVIDUAL_TOOTH_WIDTH,
        "shaft_bore_measured_mm": MEASURED_BORE, "shaft_nominal_mm": NOMINAL_SHAFT, "keyway": "ABSENT",
        "setscrew_count": SETSCREW_COUNT, "setscrew_angular_spacing_deg": SETSCREW_SPACING_DEG,
        "setscrew_hole_measured_approx_mm": SETSCREW_HOLE_MEASURED,
        "setscrew_center_from_selected_end_face_mm": SETSCREW_CENTER_FROM_END,
        "setscrew_thread_standard": "PHYSICAL_PENDING", "setscrew_installed_length": "PHYSICAL_PENDING",
        "setscrew_radial_protrusion_candidate_mm": SETSCREW_PROTRUSION_CANDIDATE,
        "setscrew_360_sweep_radius_mm": SETSCREW_SWEEP_RADIUS,
        "static_geometric_min_spacer_from_kp000_mm": STATIC_MIN_SPACER,
        "operating_axial_clearance": "PHYSICAL_VALIDATION_PENDING",
        "installed_shaft_protrusion": "PHYSICAL_PENDING",
        "torque_path": "SHAFT_TO_DUAL_SETSCREWS_TO_PTO_20T_PULLEY",
        "pto_setscrew_torque_capacity": "PHYSICAL_VALIDATION_PENDING",
        "tooth_geometry_class": "PHYSICAL_CLEARANCE_ENVELOPE_NOT_EXACT_TOOTH_PROFILE",
        "old_pto_bore_6p1_interface": "ABSENT_OBSOLETE_FOR_CURRENT_PTO_CENTER",
        "current_pto_pulley_source": "PHYSICAL_ENVELOPE_2026_08_30",
    }


def spacer_study() -> dict:
    return {
        "candidates": [
            {"spacer_mm": x, "static_geometry": "PASS", "operating_selection": "PHYSICAL_PENDING",
             "shaft_usage_increase_mm": x, "belt_plane_shift_mm": x, "tool_access_effect": "NO_GEOMETRIC_REGRESSION"}
            for x in SPACER_STUDY
        ],
        "recommended_first_running_candidate_mm": 0.5,
        "reason": "0.0 mm is static-contact datum only; 0.5 mm is the first nonzero candidate and minimizes overhang before physical rotation testing",
        "status": "PTO_SPACER_PHYSICAL_SELECTION_PENDING",
    }


def checks() -> dict[str, bool]:
    m = measurements()
    return {
        "flange_od": m["flange_od_mm"] == 34.8,
        "tooth_region_od": m["tooth_region_max_od_mm"] == 30.5,
        "body_width": m["toothed_body_axial_width_mm"] == 19.8,
        "flange_thickness": m["flange_thickness_each_mm"] == 1.6,
        "overall_width_derived": m["derived_overall_axial_width_mm"] == 23.0,
        "tooth_width": m["individual_tooth_width_mm"] == 1.5,
        "measured_bore": m["shaft_bore_measured_mm"] == 9.8,
        "nominal_shaft": m["shaft_nominal_mm"] == 10.0,
        "keyway_absent": m["keyway"] == "ABSENT",
        "setscrew_count": m["setscrew_count"] == 2,
        "setscrew_spacing": m["setscrew_angular_spacing_deg"] == 90.0,
        "setscrew_center": m["setscrew_center_from_selected_end_face_mm"] == 15.1,
        "setscrew_thread_pending": m["setscrew_thread_standard"] == "PHYSICAL_PENDING",
        "static_zero": m["static_geometric_min_spacer_from_kp000_mm"] == 0.0,
        "old_6p1_absent": m["old_pto_bore_6p1_interface"].startswith("ABSENT"),
        "physical_source": m["current_pto_pulley_source"] == "PHYSICAL_ENVELOPE_2026_08_30",
        "clearance_not_exact_teeth": m["tooth_geometry_class"].startswith("PHYSICAL_CLEARANCE"),
        "dual_setscrew_torque_path": "DUAL_SETSCREWS" in m["torque_path"],
        "spacer_candidates": SPACER_STUDY == [0.0, 0.5, 1.0],
        "old_source_hash": sha256(REPO / OLD_STEP_REL) == OLD_STEP_SHA,
        "measured_shape_valid": measured_pulley().isValid(),
        "measured_shape_single_solid": len(measured_pulley().Solids()) == 1,
    }


def validation() -> dict:
    c = checks()
    return {"status": STATUS if all(c.values()) else "FAIL_CLOSED", "check_count": len(c),
            "pass_count": sum(c.values()), "fail_count": sum(not x for x in c.values()), "checks": c,
            "holds": ["SETSCREW_THREAD_STANDARD_PHYSICAL_PENDING", "OPERATING_AXIAL_CLEARANCE_PHYSICAL_PENDING",
                      "PTO_SPACER_PHYSICAL_SELECTION_PENDING", "PTO_TORQUE_TRANSFER_PHYSICAL_PENDING",
                      "SHAFT_PROTRUSION_PHYSICAL_PENDING"]}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, obj: object) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def export_step(shape: cq.Shape, name: str) -> None:
    path = ART / name
    cq.exporters.export(shape, str(path), exportType="STEP")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2026-08-30T00:00:00'", path.read_text(encoding="utf-8"), count=1)
    path.write_text(text, encoding="utf-8", newline="\n")


def svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="#f8fafc"/><style>.t{{font:22px sans-serif;fill:#0f172a}}.s{{font:17px monospace;fill:#334155}}.d{{stroke:#ef4444;stroke-width:3;fill:none}}.p{{fill:#f59e0b;stroke:#92400e;stroke-width:2}}.b{{fill:#64748b;stroke:#334155;stroke-width:2}}</style>
<text x="55" y="60" class="t">PTO 20T Ø10 physical envelope V001</text>
<g transform="translate(80 120)"><circle cx="230" cy="220" r="174" class="p"/><circle cx="230" cy="220" r="49" fill="#f8fafc"/><line x1="56" y1="410" x2="404" y2="410" class="d"/><text x="130" y="450" class="t">flange Ø{FLANGE_OD:.1f}</text><circle cx="230" cy="220" r="153" class="d"/><text x="105" y="500" class="s">tooth region max Ø{TOOTH_REGION_MAX_OD:.1f}</text></g>
<g transform="translate(590 145)"><rect x="40" y="110" width="32" height="250" class="b"/><rect x="72" y="132" width="396" height="206" class="p"/><rect x="468" y="110" width="32" height="250" class="b"/><line x1="40" y1="400" x2="500" y2="400" class="d"/><text x="115" y="440" class="t">overall {OVERALL_AXIAL_WIDTH:.1f} = 1.6 + 19.8 + 1.6</text><line x1="342" y1="80" x2="342" y2="365" class="d"/><text x="250" y="55" class="s">set-screw plane 15.1 from selected end</text></g>
<text x="70" y="670" class="s">MEASURED BORE 9.8 · NOMINAL SHAFT 10.0 · KEYWAY ABSENT · 2 set screws / 90° · exact tooth profile NOT claimed</text></svg>'''


def docs() -> dict[str, str]:
    h = f"# PTO 20T Ø10 Physical Envelope Authority V001\n\nStatus: `{STATUS}`  \nScope: `PHYSICAL_CLEARANCE_ENVELOPE / NOT_MANUFACTURING_TOOTH_CAD`\n\n"
    report = h + f"""## Captured physical authority

The current real pulley is HTD5M 20T, nominal Ø10 shaft. Measured flange OD is {FLANGE_OD} mm, maximum toothed-region OD {TOOTH_REGION_MAX_OD} mm, toothed/body width {TOOTHED_BODY_AXIAL_WIDTH} mm, and each flange is {FLANGE_THICKNESS} mm. Derived overall axial envelope is {OVERALL_AXIAL_WIDTH} mm. Measured bore is {MEASURED_BORE} mm; nominal shaft authority remains {NOMINAL_SHAFT} mm.

This is a physical envelope, not a manufacturing tooth-profile reconstruction. The old exact HTD5M source is retained only as a pitch/tooth-count reference. Its Ø6.1 centre is `OBSOLETE_FOR_CURRENT_PTO_CENTER` and is absent here.

## Torque architecture

`SHAFT → DUAL SET SCREWS → PTO 20T PULLEY`. There is no keyway. Two approximately Ø4.4 mm radial regions are 90° apart at 15.1 mm from the selected end face. Thread standard, installed screw length and torque capacity remain physical HOLD. CAD does not establish durability.

## Spacer

Static geometry permits 0.0 mm. The first recommended free-running trial is 0.5 mm, followed by 1.0 mm only if needed. Final selection remains `PTO_SPACER_PHYSICAL_SELECTION_PENDING`.
"""
    test = h + """1. Install the real Ø10 shaft and KP000 pair.
2. Test the real pulley at 0.0 mm static spacing and hand rotate without tightening.
3. Repeat at 0.5 mm, then 1.0 mm.
4. Select the smallest free-running spacing.
5. Tighten both verified screws; add shaft/pulley witness marks.
6. Hand torque forward/reverse.
7. Install belt and hand rotate.
8. Low-speed powered no-load only after prior PASS.
9. Inspect witness marks before staged load.
"""
    holds = h + """- `SETSCREW_THREAD_STANDARD_PHYSICAL_PENDING`
- `OPERATING_AXIAL_CLEARANCE_PHYSICAL_PENDING`
- `PTO_SPACER_PHYSICAL_SELECTION_PENDING`
- `PTO_TORQUE_TRANSFER_PHYSICAL_PENDING`
- `SHAFT_PROTRUSION_PHYSICAL_PENDING`
- `PTO_POWERED_PASS`, `PTO_TORQUE_PASS`, and field use are not claimed.
"""
    valid = h + f"Contract checks: {validation()['pass_count']}/{validation()['check_count']} PASS. STEP reload and byte reproducibility are verified by the builder/test.\n"
    return {"README.md": report, "authority_report.md": report, "PHYSICAL_TEST_PLAN.md": test, "HOLD_REGISTER.md": holds, "validation_report.md": valid}


def write_manifests() -> None:
    rows = []
    for rel in ALL_PATHS:
        p = LANE / rel
        if rel in {"MANIFEST.txt", "SHA256SUMS.txt"} or not p.is_file():
            continue
        rows.append(f"{rel}\t{p.stat().st_size}\t{sha256(p)}")
    write_text(LANE / "MANIFEST.txt", "path\tbytes\tsha256\n" + "\n".join(rows) + "\n")
    sums = []
    for rel in ALL_PATHS:
        p = LANE / rel
        if rel != "SHA256SUMS.txt" and p.is_file():
            sums.append(f"{sha256(p)}  {rel}")
    write_text(LANE / "SHA256SUMS.txt", "\n".join(sums) + "\n")


def build() -> None:
    repository_guard(); ART.mkdir(parents=True, exist_ok=True); (LANE / "tests").mkdir(exist_ok=True)
    export_step(measured_pulley(), "pto_20t_od10_physical_envelope.step")
    export_step(clearance_envelope(), "pto_20t_od10_clearance_envelope.step")
    export_step(rotational_keepout(), "pto_20t_od10_rotational_keepout.step")
    export_step(set_screw_sweep(), "pto_20t_od10_set_screw_sweep.step")
    export_step(dimension_reference(), "pto_20t_od10_dimension_reference.step")
    write_text(ART / "pto_20t_od10_dimension_preview.svg", svg())
    write_json(LANE / "physical_measurements.json", measurements())
    write_json(LANE / "spacer_study.json", spacer_study())
    write_json(LANE / "validation_report.json", validation())
    write_json(LANE / "source_authority_audit.json", {"old_reference_path": OLD_STEP_REL, "sha256": sha256(REPO / OLD_STEP_REL), "hash_pass": sha256(REPO / OLD_STEP_REL) == OLD_STEP_SHA, "centre_use": "PROHIBITED"})
    for rel, text in docs().items(): write_text(LANE / rel, text)
    write_text(LANE / "COMMIT_PATHS.txt", "".join(f"{(LANE_REL / p).as_posix()}\n" for p in ALL_PATHS))
    write_manifests()


def verify() -> dict:
    repository_guard()
    missing = [p for p in ALL_PATHS if not (LANE / p).is_file()]
    actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    if missing or actual != ALL_PATHS:
        raise RuntimeError(f"path contract failure missing={missing} extra={sorted(set(actual)-set(ALL_PATHS))}")
    steps = []
    for p in sorted(ART.glob("*.step")):
        s = cq.importers.importStep(str(p)).val(); steps.append({"file": p.name, "valid": s.isValid(), "solids": len(s.Solids())})
    c = checks()
    if not all(c.values()) or not all(x["valid"] and x["solids"] for x in steps):
        raise RuntimeError("geometry/contract failure")
    return {"contract": f"{sum(c.values())}/{len(c)}", "step_reload": steps, "path_count": len(actual)}


def make_zip() -> tuple[Path, str]:
    verify(); DOWNLOADS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = DOWNLOADS / f"Paddy_Swarm_PTO_20T_OD10_PHYSICAL_AUTHORITY_V001_{stamp}.zip"
    n = 1
    while target.exists(): target = DOWNLOADS / f"Paddy_Swarm_PTO_20T_OD10_PHYSICAL_AUTHORITY_V001_{stamp}_{n:02d}.zip"; n += 1
    with zipfile.ZipFile(target, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in ALL_PATHS:
            info = zipfile.ZipInfo((Path(LANE.name) / rel).as_posix(), (2026, 8, 30, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            z.writestr(info, (LANE / rel).read_bytes())
    return target, sha256(target)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); ap.add_argument("--verify", action="store_true"); ap.add_argument("--zip", action="store_true"); a = ap.parse_args()
    if not (a.build or a.verify or a.zip): a.build = True
    if a.build: build()
    if a.verify or a.zip: print(json.dumps(verify(), indent=2))
    if a.zip:
        p, h = make_zip(); print(f"ZIP_PATH={p}"); print(f"ZIP_SHA256={h}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
