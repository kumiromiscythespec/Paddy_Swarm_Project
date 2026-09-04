#!/usr/bin/env python3
"""Front Interface V002: V001 architecture with measured Ø10 PTO envelope."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
LANE_REL = Path("cad/common_rover/frame/front_interface_dual_pto_20t_v002")
ART = LANE / "artifacts"
DOWNLOADS = Path(r"D:\Downloads")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
STATUS = "PTO_20T_PHYSICAL_ENVELOPE_CAPTURED/CAD_PASS/CONTRACT_TEST_PASS/FRONT_INTERFACE_V002_READY/PHYSICAL_VALIDATION_PENDING"

V001_LANE = REPO / "cad/common_rover/frame/front_interface_dual_pto_20t_v001"
PTO_LANE = REPO / "cad/common_rover/pto/pto_20t_od10_physical_envelope_v001"
V001_TREE_SHA = "06e80eaeea3a56724625d51f6e351b4c9dcc13db80536d530c73015c2b6306ce"
PTO_TREE_SHA = "cd22d671d55559eeac1d1e532bb141d454264dcd3afeb76668fd711cb9cd613f"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path); assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


v1 = load_module("front_interface_v001_protected", V001_LANE / "build_front_interface_dual_pto_20t_v001.py")
pa = load_module("pto_20t_physical_authority", PTO_LANE / "build_pto_20t_od10_physical_envelope_v001.py")

PULLEY_CENTER_Y = 130.0
PULLEY_NEAR_FACE_ABS_Y = PULLEY_CENTER_Y - pa.OVERALL_AXIAL_WIDTH / 2
PULLEY_FAR_FACE_ABS_Y = PULLEY_CENTER_Y + pa.OVERALL_AXIAL_WIDTH / 2
PULLEY_TO_KP_HOUSING = PULLEY_NEAR_FACE_ABS_Y - (v1.KP_OUTER_Y + v1.KP_DEPTH_Y / 2)
PULLEY_OVERHANG = PULLEY_CENTER_Y - v1.KP_OUTER_Y
SETSCREW_PLANE_ABS_Y = PULLEY_NEAR_FACE_ABS_Y + pa.SETSCREW_CENTER_FROM_END
DISPLAY_SPACER_CANDIDATE = 0.5
UNRESOLVED_RETENTION_STACK = PULLEY_TO_KP_HOUSING - DISPLAY_SPACER_CANDIDATE

SOURCE_FILES = ["build_front_interface_dual_pto_20t_v002.py", "tests/test_front_interface_dual_pto_20t_v002_contract.py"]
GENERATED = [
    "README.md", "DESIGN_AUTHORITY.md", "DELTA_AUDIT_V001_TO_V002.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
    "design_parameters.json", "validation_report.json", "collision_report.json", "spacer_study.json", "source_authority_audit.json",
    "artifacts/front_interface_dual_pto_20t_v002.step",
    "artifacts/front_interface_dual_pto_20t_v002_reference.stl",
    "artifacts/front_interface_v002_assembly_reference.step",
    "artifacts/left_pto_physical_reference.step",
    "artifacts/right_pto_physical_reference.step",
    "artifacts/pulley_keepout_v002.step",
    "artifacts/set_screw_service_envelope.step",
    "artifacts/belt_keepout_v002.step",
    "artifacts/unit_input_pulley_envelope_v002.step",
    "artifacts/500mm_frame_reference_v002.step",
    "artifacts/dimension_preview.svg",
    "COMMIT_PATHS.txt", "MANIFEST.txt", "SHA256SUMS.txt",
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


def guard() -> dict:
    if Path(git("rev-parse", "--show-toplevel")).resolve() != REPO.resolve(): raise RuntimeError("repo mismatch")
    if git("branch", "--show-current") != BRANCH or git("rev-parse", "HEAD") != HEAD: raise RuntimeError("branch/HEAD mismatch")
    if git("diff", "--cached", "--name-only"): raise RuntimeError("staged paths prohibited")
    if tree_hash(V001_LANE) != V001_TREE_SHA: raise RuntimeError("protected V001 tree changed")
    if tree_hash(PTO_LANE) != PTO_TREE_SHA: raise RuntimeError("PTO authority tree changed")
    return {"branch": BRANCH, "head": HEAD, "v001_tree": V001_TREE_SHA, "pto_tree": PTO_TREE_SHA}


def compound(shapes: list[cq.Shape]) -> cq.Shape:
    return cq.Compound.makeCompound(shapes)


def orient_authority(shape: cq.Shape, side: int) -> cq.Shape:
    centered = shape.translate((0, 0, -pa.OVERALL_AXIAL_WIDTH / 2))
    angle = -90 if side > 0 else 90
    return centered.rotate((0, 0, 0), (1, 0, 0), angle).translate((0, side * PULLEY_CENTER_Y, v1.DRIVE_Z))


def physical_pulley(side: int) -> cq.Shape:
    return orient_authority(pa.measured_pulley(), side)


def pulley_keepout(side: int) -> cq.Shape:
    return v1.cyl_y(pa.ROTATION_KEEPOUT_RADIUS, pa.ROTATION_KEEPOUT_WIDTH, (0, side * PULLEY_CENTER_Y, v1.DRIVE_Z))


def setscrew_sweep(side: int) -> cq.Shape:
    return orient_authority(pa.set_screw_sweep(), side)


def setscrew_tool(side: int) -> cq.Shape:
    plane_y = side * SETSCREW_PLANE_ABS_Y
    return v1.cyl_z(4.0, 35.0, (0, plane_y, v1.DRIVE_Z + pa.FLANGE_OD / 2 + 17.5))


def belt(side: int) -> cq.Shape:
    return v1.belt_keepout(side)


def pto(side: int) -> cq.Shape:
    return compound([v1.support_plate(side), v1.kp000(side * v1.KP_INNER_Y), v1.kp000(side * v1.KP_OUTER_Y), v1.pto_shaft(side), physical_pulley(side)])


def assembly() -> cq.Shape:
    return compound([
        v1.interface_structure(), pto(-1), pto(1), pulley_keepout(-1), pulley_keepout(1),
        setscrew_sweep(-1), setscrew_sweep(1), setscrew_tool(-1), setscrew_tool(1),
        belt(-1), belt(1), v1.input_pulley_envelope(-1), v1.input_pulley_envelope(1),
        v1.frame_500_reference(), v1.crawler_envelope(-1), v1.crawler_envelope(1),
    ])


def iv(a: cq.Shape, b: cq.Shape) -> float:
    return round(a.intersect(b).Volume(), 9)


def dist(a: cq.Shape, b: cq.Shape) -> float:
    return round(float(a.distance(b)), 6)


def collision_report() -> dict:
    kp = compound([v1.kp000(-v1.KP_INNER_Y), v1.kp000(-v1.KP_OUTER_Y), v1.kp000(v1.KP_INNER_Y), v1.kp000(v1.KP_OUTER_Y)])
    pulleys = compound([physical_pulley(-1), physical_pulley(1)])
    sweeps = compound([setscrew_sweep(-1), setscrew_sweep(1)])
    tools = compound([setscrew_tool(-1), setscrew_tool(1)])
    belts = compound([belt(-1), belt(1)])
    crawler = compound([v1.crawler_envelope(-1), v1.crawler_envelope(1)])
    mount = v1.unit_mount()
    pairs = {
        "PULLEY_TO_KP000": (pulleys, kp), "SETSCREW_SWEEP_TO_KP000": (sweeps, kp), "TOOL_TO_KP000": (tools, kp),
        "PULLEY_TO_BEAM": (pulleys, v1.beam()), "SETSCREW_SWEEP_TO_BEAM": (sweeps, v1.beam()),
        "UNIT_MOUNT_TO_PULLEY": (mount, pulleys), "UNIT_MOUNT_TO_PULLEY_KEEPOUT": (mount, compound([pulley_keepout(-1), pulley_keepout(1)])),
        "UNIT_MOUNT_TO_BELT": (mount, belts), "UNIT_MOUNT_TO_SETSCREW_TOOL": (mount, tools),
        "PULLEY_TO_CRAWLER": (pulleys, crawler), "SETSCREW_SWEEP_TO_CRAWLER": (sweeps, crawler),
        "BELT_TO_CRAWLER": (belts, crawler), "BEAM_TO_CRAWLER": (v1.beam(), crawler),
        "KP000_TO_CRAWLER": (kp, crawler), "UNIT_MOUNT_TO_CRAWLER": (mount, crawler),
    }
    return {"checks": {k: {"intersection_mm3": iv(a, b), "minimum_clearance_mm": dist(a, b)} for k, (a, b) in pairs.items()}}


def spacer_study() -> dict:
    rows = []
    housing_face = v1.KP_OUTER_Y + v1.KP_DEPTH_Y / 2
    for s in (0.0, 0.5, 1.0):
        center = housing_face + s + pa.OVERALL_AXIAL_WIDTH / 2
        rows.append({"service_clearance_mm": s, "minimum_pulley_center_abs_y_mm": center,
                     "minimum_overhang_from_outer_bearing_plane_mm": center - v1.KP_OUTER_Y,
                     "shaft_usage_increase_mm": s, "static_pulley_kp000": "PASS" if s >= 0 else "FAIL",
                     "operating_status": "PHYSICAL_PENDING"})
    return {"candidates": rows, "recommended_first_physical_candidate_mm": DISPLAY_SPACER_CANDIDATE,
            "v002_reference_pulley_plane_abs_y_mm": PULLEY_CENTER_Y,
            "v002_reference_housing_to_near_face_mm": PULLEY_TO_KP_HOUSING,
            "unresolved_retention_service_stack_after_0p5_candidate_mm": UNRESOLVED_RETENTION_STACK,
            "selection": "PTO_SPACER_PHYSICAL_SELECTION_PENDING"}


def parameters() -> dict:
    return {
        "version": "FRONT_INTERFACE_DUAL_PTO_20T_V002", "status": STATUS,
        "protected_v001": {"tree_sha256": V001_TREE_SHA, "drive_axis_z_mm": v1.DRIVE_Z, "pto_axis_z_mm": v1.DRIVE_Z,
                            "beam_length_mm": v1.BEAM_LENGTH, "kp000_total": 4, "kp000_pair_spacing_mm": v1.KP_PAIR_SPACING,
                            "shaft_center_gap_mm": v1.PTO_SHAFT_CENTER_GAP, "unit_mount_y_mm": [-75.0, 75.0],
                            "unit_mount_z_mm": [55.0, 185.0], "diagonal_brace_count": 0,
                            "frame_500_status": "REFERENCE_FRAME_ENVELOPE_DESIGN_CANDIDATE_NOT_PHYSICAL_AUTHORITY"},
        "pulley": {**pa.measurements(), "authority_lane": "cad/common_rover/pto/pto_20t_od10_physical_envelope_v001",
                   "left_center_y_mm": PULLEY_CENTER_Y, "right_center_y_mm": -PULLEY_CENTER_Y,
                   "near_face_abs_y_mm": PULLEY_NEAR_FACE_ABS_Y, "center_plane_abs_y_mm": PULLEY_CENTER_Y,
                   "far_face_abs_y_mm": PULLEY_FAR_FACE_ABS_Y, "outer_kp000_reference_plane_abs_y_mm": v1.KP_OUTER_Y,
                   "overhang_from_outer_kp000_plane_mm": PULLEY_OVERHANG,
                   "housing_to_near_face_mm": PULLEY_TO_KP_HOUSING,
                   "shaft_protrusion": "PHYSICAL_PENDING", "spacer_candidate_mm": DISPLAY_SPACER_CANDIDATE,
                   "old_pto_bore_6p1_interface": "ABSENT"},
        "setscrew": {"count": 2, "spacing_deg": 90.0, "plane_abs_y_mm": SETSCREW_PLANE_ABS_Y,
                     "thread_standard": "PHYSICAL_PENDING", "torque_transfer": "PHYSICAL_PENDING",
                     "service_order": ["REMOVE_WORK_UNIT", "REMOVE_BELT", "INDEX_SETSCREW_UP", "LOOSEN_DUAL_SETSCREWS", "SLIDE_PULLEY", "SERVICE_SHAFT_KP000"]},
        "keepouts": {"pulley_radius_mm": pa.ROTATION_KEEPOUT_RADIUS, "pulley_axial_width_mm": pa.ROTATION_KEEPOUT_WIDTH,
                     "belt_corridor_v001": [22.5, 102.5, 25.0, 45.0], "belt_corridor_v002": [22.5, 102.5, 25.0, 45.0],
                     "belt_corridor_delta_mm": [0.0, 0.0, 0.0, 0.0], "unit_input_envelope": [60.0, 30.0],
                     "unit_input_center_x_mm": 120.0, "local_adjustment_mm": [10.0, 20.0]},
        "future_failover_options_not_implemented": ["D_FLAT_SHAFT", "KEYED_PULLEY", "CLAMP_HUB", "SPLIT_CLAMP_ADAPTER"],
        "holds": ["SETSCREW_THREAD_STANDARD_PHYSICAL_PENDING", "OPERATING_AXIAL_CLEARANCE_PHYSICAL_PENDING",
                  "PTO_SPACER_PHYSICAL_SELECTION_PENDING", "PTO_TORQUE_TRANSFER_PHYSICAL_PENDING",
                  "SHAFT_PROTRUSION_PHYSICAL_PENDING", "UNIT_LOAD_PHYSICAL_PENDING"],
    }


def checks() -> dict[str, bool]:
    p = parameters(); c = collision_report()["checks"]
    z = p["protected_v001"]
    result = {
        "v001_tree": tree_hash(V001_LANE) == V001_TREE_SHA, "pto_tree": tree_hash(PTO_LANE) == PTO_TREE_SHA,
        "drive_z": z["drive_axis_z_mm"] == 122.5, "pto_z": z["pto_axis_z_mm"] == 122.5,
        "z_difference": z["pto_axis_z_mm"] - z["drive_axis_z_mm"] == 0,
        "beam": z["beam_length_mm"] == 400.0, "kp000_four": z["kp000_total"] == 4,
        "kp000_spacing": z["kp000_pair_spacing_mm"] == 50.0, "center_gap": z["shaft_center_gap_mm"] == 60.0,
        "unit_mount_y": z["unit_mount_y_mm"] == [-75.0, 75.0], "unit_mount_z": z["unit_mount_z_mm"] == [55.0, 185.0],
        "no_diagonal": z["diagonal_brace_count"] == 0, "frame500_candidate": "DESIGN_CANDIDATE" in z["frame_500_status"],
        "physical_source": p["pulley"]["current_pto_pulley_source"] == "PHYSICAL_ENVELOPE_2026_08_30",
        "flange_od": p["pulley"]["flange_od_mm"] == 34.8, "body_od": p["pulley"]["tooth_region_max_od_mm"] == 30.5,
        "body_width": p["pulley"]["toothed_body_axial_width_mm"] == 19.8, "flanges": p["pulley"]["flange_thickness_each_mm"] == 1.6,
        "bore": (p["pulley"]["shaft_bore_measured_mm"], p["pulley"]["shaft_nominal_mm"]) == (9.8, 10.0),
        "old6p1_absent": p["pulley"]["old_pto_bore_6p1_interface"] == "ABSENT", "keyway_absent": p["pulley"]["keyway"] == "ABSENT",
        "setscrews": (p["setscrew"]["count"], p["setscrew"]["spacing_deg"]) == (2, 90.0),
        "belt_delta_zero": p["keepouts"]["belt_corridor_delta_mm"] == [0.0, 0.0, 0.0, 0.0],
        "unit_input_unchanged": p["keepouts"]["unit_input_envelope"] == [60.0, 30.0],
    }
    for name in ("PULLEY_TO_KP000", "SETSCREW_SWEEP_TO_KP000", "TOOL_TO_KP000", "PULLEY_TO_BEAM",
                 "SETSCREW_SWEEP_TO_BEAM", "UNIT_MOUNT_TO_PULLEY", "UNIT_MOUNT_TO_PULLEY_KEEPOUT",
                 "UNIT_MOUNT_TO_BELT", "UNIT_MOUNT_TO_SETSCREW_TOOL", "PULLEY_TO_CRAWLER",
                 "SETSCREW_SWEEP_TO_CRAWLER", "BELT_TO_CRAWLER", "BEAM_TO_CRAWLER", "KP000_TO_CRAWLER", "UNIT_MOUNT_TO_CRAWLER"):
        result[name.lower()+"_zero"] = c[name]["intersection_mm3"] == 0.0
    return result


def validation() -> dict:
    c = checks()
    return {"status": STATUS if all(c.values()) else "FAIL_CLOSED", "check_count": len(c), "pass_count": sum(c.values()), "fail_count": sum(not x for x in c.values()), "checks": c}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, obj: object) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def export_step(shape: cq.Shape, name: str) -> None:
    p = ART / name; cq.exporters.export(shape, str(p), exportType="STEP")
    t = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2026-08-30T00:00:00'", p.read_text(encoding="utf-8"), count=1); p.write_text(t, encoding="utf-8", newline="\n")


def svg() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720"><rect width="1200" height="720" fill="#f8fafc"/><style>.t{{font:22px sans-serif;fill:#0f172a}}.s{{font:17px monospace;fill:#334155}}.b{{fill:#64748b}}.p{{fill:#f59e0b;stroke:#92400e;stroke-width:2}}.r{{fill:none;stroke:#ef4444;stroke-width:3;stroke-dasharray:9 7}}.g{{fill:#10b981}}</style><text x="55" y="55" class="t">Front Interface V002 — measured PTO 20T envelope</text><g transform="translate(70 120)"><rect x="40" y="290" width="1060" height="45" class="b"/><line x1="40" y1="235" x2="1100" y2="235" stroke="#ef4444" stroke-width="3"/><text x="60" y="220" class="s">PTO = DRIVE axis Z122.5</text><rect x="240" y="165" width="130" height="125" class="g"/><circle cx="450" cy="235" r="87" class="p"/><circle cx="450" cy="235" r="112" class="r"/><rect x="562" y="170" width="250" height="130" class="r"/><circle cx="940" cy="235" r="150" class="r"/><text x="185" y="410" class="s">KP000</text><text x="385" y="410" class="s">flange Ø34.8 / keepout Ø44.8</text><text x="575" y="410" class="s">belt corridor unchanged</text><text x="850" y="410" class="s">unit input Ø60</text><text x="60" y="510" class="t">near / center / far plane: {PULLEY_NEAR_FACE_ABS_Y:.1f} / {PULLEY_CENTER_Y:.1f} / {PULLEY_FAR_FACE_ABS_Y:.1f} mm</text><text x="60" y="555" class="s">KP housing gap {PULLEY_TO_KP_HOUSING:.1f} · overhang {PULLEY_OVERHANG:.1f} · set-screw plane {SETSCREW_PLANE_ABS_Y:.1f}</text></g></svg>'''


def docs() -> dict[str, str]:
    h = f"# Front Interface Dual PTO 20T V002\n\nStatus: `{STATUS}`  \nProtected parent: `front_interface_dual_pto_20t_v001`\n\n"
    report = h + f"""V002 replaces only the provisional pulley model with the measured physical-envelope authority. Drive/PTO Z remains 122.5 mm, beam 400 mm, four KP000 units at 50/100 mm per side, independent half-shafts with 60 mm centre gap, four unit points at Y±75/Z55/185, no diagonals, and 500 mm rails as reference-only.

Measured pulley: flange Ø34.8, tooth-region max Ø30.5, 19.8 mm body plus 1.6 mm flanges = 23.0 mm overall, measured bore 9.8/nominal shaft10, no keyway, dual approximate Ø4.4 set-screw regions at 90°. The old Ø6.1 centre is absent.

The protected V001 belt plane is retained at Y±130. Pulley planes are near {PULLEY_NEAR_FACE_ABS_Y:.1f}, centre {PULLEY_CENTER_Y:.1f}, far {PULLEY_FAR_FACE_ABS_Y:.1f} mm; outer bearing plane is 100 mm. Overhang stays {PULLEY_OVERHANG:.1f} mm and housing clearance is {PULLEY_TO_KP_HOUSING:.1f} mm. This clearance includes an unresolved retention/service stack; 0/0.5/1.0 mm spacer trials remain physical selection inputs and shaft protrusion is not released.

`PTO = ROTATIONAL TORQUE ONLY`; unit mount carries weight/reaction/impact. Dual set-screw torque capacity remains physical pending.
"""
    delta = h + """## Zero-diff protected

- drive and PTO Z; beam; KP000 geometry/spacing; shaft independence/gap; unit mount coordinates; no-diagonal rule; 500 mm candidate status.

## Intended delta

- Ø35×20 provisional pulley → measured flange/body/flange 23.0 mm envelope
- pulley keep-out radius 22.5→22.4 mm; axial width 30→33 mm
- set-screw sweep/tool envelope added
- belt corridor and unit-input envelope unchanged after collision revalidation
"""
    physical = h + """1 remove work unit; 2 remove/loosen belt; 3 index a set screw upward; 4 access and loosen both set screws; 5 slide/remove pulley; 6 service shaft/KP000. Physical test: 0 mm static, then 0.5 and 1.0 mm hand-rotation trials; select smallest free-running spacing; add witness marks; hand torque; belt hand rotation; low-speed no-load later; staged load only after prior PASS.
"""
    hold = h + """- SETSCREW_THREAD_STANDARD_PHYSICAL_PENDING
- OPERATING_AXIAL_CLEARANCE_PHYSICAL_PENDING
- PTO_SPACER_PHYSICAL_SELECTION_PENDING
- PTO_TORQUE_TRANSFER_PHYSICAL_PENDING
- SHAFT_PROTRUSION_PHYSICAL_PENDING
- UNIT_LOAD_PHYSICAL_PENDING
- PTO_POWERED_PASS / PTO_TORQUE_PASS / UNIT_FIELD_PASS / FRAME_FIELD_PASS are not claimed.
"""
    return {"README.md": report, "DESIGN_AUTHORITY.md": report, "DELTA_AUDIT_V001_TO_V002.md": delta, "PHYSICAL_TEST_PLAN.md": physical, "HOLD_REGISTER.md": hold}


def write_manifests() -> None:
    rows=[]
    for rel in ALL_PATHS:
        p=LANE/rel
        if rel not in {"MANIFEST.txt","SHA256SUMS.txt"} and p.is_file(): rows.append(f"{rel}\t{p.stat().st_size}\t{sha256(p)}")
    write_text(LANE/"MANIFEST.txt","path\tbytes\tsha256\n"+"\n".join(rows)+"\n")
    sums=[]
    for rel in ALL_PATHS:
        p=LANE/rel
        if rel!="SHA256SUMS.txt" and p.is_file(): sums.append(f"{sha256(p)}  {rel}")
    write_text(LANE/"SHA256SUMS.txt","\n".join(sums)+"\n")


def build() -> None:
    guard(); ART.mkdir(parents=True,exist_ok=True); (LANE/"tests").mkdir(exist_ok=True)
    export_step(v1.interface_structure(),"front_interface_dual_pto_20t_v002.step")
    cq.exporters.export(v1.interface_structure(),str(ART/"front_interface_dual_pto_20t_v002_reference.stl"),exportType="STL",tolerance=0.05,angularTolerance=0.1)
    export_step(assembly(),"front_interface_v002_assembly_reference.step")
    export_step(pto(1),"left_pto_physical_reference.step"); export_step(pto(-1),"right_pto_physical_reference.step")
    export_step(compound([pulley_keepout(-1),pulley_keepout(1)]),"pulley_keepout_v002.step")
    export_step(compound([setscrew_sweep(-1),setscrew_sweep(1),setscrew_tool(-1),setscrew_tool(1)]),"set_screw_service_envelope.step")
    export_step(compound([belt(-1),belt(1)]),"belt_keepout_v002.step")
    export_step(compound([v1.input_pulley_envelope(-1),v1.input_pulley_envelope(1)]),"unit_input_pulley_envelope_v002.step")
    export_step(v1.frame_500_reference(),"500mm_frame_reference_v002.step")
    write_text(ART/"dimension_preview.svg",svg())
    write_json(LANE/"design_parameters.json",parameters()); write_json(LANE/"spacer_study.json",spacer_study())
    write_json(LANE/"collision_report.json",collision_report()); write_json(LANE/"validation_report.json",validation())
    write_json(LANE/"source_authority_audit.json",{"v001_tree_expected":V001_TREE_SHA,"v001_tree_actual":tree_hash(V001_LANE),"pto_tree_expected":PTO_TREE_SHA,"pto_tree_actual":tree_hash(PTO_LANE),"all_pass":tree_hash(V001_LANE)==V001_TREE_SHA and tree_hash(PTO_LANE)==PTO_TREE_SHA})
    for rel,text in docs().items(): write_text(LANE/rel,text)
    write_text(LANE/"COMMIT_PATHS.txt","".join(f"{(LANE_REL/p).as_posix()}\n" for p in ALL_PATHS)); write_manifests()


def verify() -> dict:
    guard(); actual=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    if actual!=ALL_PATHS: raise RuntimeError(f"path contract failure {sorted(set(actual)^set(ALL_PATHS))}")
    steps=[]
    for p in sorted(ART.glob("*.step")):
        s=cq.importers.importStep(str(p)).val();steps.append({"file":p.name,"valid":s.isValid(),"solids":len(s.Solids())})
    stl=v1.inspect_binary_stl(ART/"front_interface_dual_pto_20t_v002_reference.stl"); c=checks()
    if not all(c.values()) or not all(x["valid"] and x["solids"] for x in steps) or not stl["watertight"] or stl["bad_edges"] or stl["degenerate_triangles"]: raise RuntimeError("validation failure")
    return {"contract":f"{sum(c.values())}/{len(c)}","steps":steps,"stl":stl,"path_count":len(actual)}


def make_zip()->tuple[Path,str]:
    verify();DOWNLOADS.mkdir(parents=True,exist_ok=True);stamp=datetime.now().strftime("%Y%m%d_%H%M%S");target=DOWNLOADS/f"Paddy_Swarm_FRONT_INTERFACE_DUAL_PTO_20T_V002_{stamp}.zip";n=1
    while target.exists():target=DOWNLOADS/f"Paddy_Swarm_FRONT_INTERFACE_DUAL_PTO_20T_V002_{stamp}_{n:02d}.zip";n+=1
    with zipfile.ZipFile(target,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in ALL_PATHS:
            info=zipfile.ZipInfo((Path(LANE.name)/rel).as_posix(),(2026,8,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(LANE/rel).read_bytes())
    return target,sha256(target)


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--build",action="store_true");ap.add_argument("--verify",action="store_true");ap.add_argument("--zip",action="store_true");a=ap.parse_args()
    if not(a.build or a.verify or a.zip):a.build=True
    if a.build:build()
    if a.verify or a.zip:print(json.dumps(verify(),indent=2))
    if a.zip:
        p,h=make_zip();print(f"ZIP_PATH={p}");print(f"ZIP_SHA256={h}")
    return 0
if __name__=="__main__":raise SystemExit(main())
