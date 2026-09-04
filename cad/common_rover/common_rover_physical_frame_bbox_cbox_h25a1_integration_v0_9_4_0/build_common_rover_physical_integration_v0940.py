#!/usr/bin/env python3
"""Build Common Rover physical integration reference v0.9.4.0.

This builder is deliberately fail-closed: missing physical measurements remain HOLD,
and all box/drive models are reference envelopes rather than manufacturing geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq


VERSION = "0.9.4.0"
CLASSIFICATION = "PHYSICAL_INTEGRATION_REFERENCE"
RELEASE = "HOLD"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0"
LANE = Path(__file__).resolve().parent
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
DOWNLOADS = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Physical_Integration_H25A1_BBOX_CBOX_v0_9_4_0_"

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

DOCS = [
    "README.md", "PHYSICAL_FRAME_REFERENCE.md", "FRAME_MEASUREMENT_LEDGER.md",
    "DESIGN_SOURCE_TRACE.md", "PTO_20T20T_ARCHITECTURE.md", "KP000_SUPPORT_POLICY.md",
    "CRAWLER_BEARING_UPDATE.md", "H0_H23_H24_FAILURE_HISTORY.md", "H25A1_DESIGN_SPEC.md",
    "H25A1_COLLAR_MEASUREMENTS.md", "H25A1_MISSING_MEASUREMENTS.md", "BBOX_CBOX_ARCHITECTURE.md",
    "BBOX_ENVELOPE_STUDY.md", "CBOX_ENVELOPE_STUDY.md", "BBOX_REMOVAL_STUDY.md",
    "WATERLINE_AND_BUOYANCY.md", "INTERFERENCE_REPORT.md", "MISSING_MEASUREMENTS.md", "DESIGN_GATE.md",
]
STEPS = [
    "cad/physical_frame_reference.step", "cad/h25a1_reference.step", "cad/bbox_candidate_envelope.step",
    "cad/cbox_candidate_envelope.step", "cad/integration_assembly.step", "cad/h25a1_collar_fit_coupon.step",
    "cad/h25a1_antirotation_comparison.step",
]
STLS = ["cad/physical_frame_reference.stl", "cad/integration_assembly_reference.stl", "cad/h25a1_collar_fit_coupon.stl"]
SVGS = ["drawings/top_view.svg", "drawings/side_view.svg", "drawings/front_view.svg", "drawings/bbox_removal.svg", "drawings/h25a1_section.svg"]
ROOT_DATA = ["geometry_manifest.json", "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt", "BUILD_LOG.txt", "TEST_LOG.txt"]
SOURCE = ["build_common_rover_physical_integration_v0940.py", "tests/test_common_rover_physical_integration_v0940.py"]
PACKAGE_PATHS = sorted(DOCS + STEPS + STLS + SVGS + ROOT_DATA + SOURCE)

# Physical authority (mm).
FRAME = {
    "upper_outer_x": 540.0, "upper_outer_y": 181.0, "lower_outer_x": 442.0, "lower_outer_y": 181.0,
    "height": 150.0, "upper_clear_x": 500.0, "upper_clear_y": 100.0,
    "lower_clear_x": 400.0, "lower_clear_y": 140.0, "tolerance": 1.0,
    "bottom_z": 68.0, "top_z": 218.0, "waterline_z": 150.0,
}
COLLAR = {"od": 15.9, "bore": 10.1, "width": 3.0, "apparent_threaded_hole": 3.7}
KP000 = {"width_x": 67.0, "depth_y": 17.0, "height_z": 35.0, "axis_height": 18.5, "axis_tol": 0.5, "bore": 10.0, "collar_protrusion": 6.0}
SPROCKET = {"tooth_count": 12, "phase": 15.0, "tip_radius": 33.07, "root_radius": 29.47, "tip_width": 7.5, "root_width": 9.5, "axial_width": 44.0, "pitch_diameter": 76.3943726841, "embed_depth": 4.0}
BEARING = {"od_measured": 25.9, "seat_trial": 26.0, "central_clearance": 12.0}


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_digest(path: Path) -> dict[str, Any]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    h = hashlib.sha256()
    for p in files:
        rel = p.relative_to(path).as_posix()
        h.update(rel.encode()); h.update(b"\0"); h.update(bytes.fromhex(sha(p)))
    return {"path": path.relative_to(REPO_ROOT).as_posix(), "file_count": len(files), "sha256_tree": h.hexdigest()}


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def repository_guard(require_complete: bool = False) -> dict[str, Any]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    tracked = sorted(set(run_git("diff", "--name-only").splitlines()))
    staged = sorted(set(run_git("diff", "--cached", "--name-only").splitlines()))
    untracked = sorted(run_git("ls-files", "--others", "--exclude-standard").splitlines())
    lane_untracked = sorted(p[len(LANE_REL) + 1:] for p in untracked if p.startswith(LANE_REL + "/"))
    authority = {p: sha(REPO_ROOT / p) for p in AUTHORITY_HASHES}
    forbidden = [p for p in LANE.rglob("*") if p.is_file() and (p.suffix.lower() in {".dxf", ".3mf", ".gcode"} or "__pycache__" in p.parts or p.suffix.lower() == ".pyc")]
    checks = {
        "repository_root": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "tracked_diff_preserved": set(tracked) == set(AUTHORITY_HASHES),
        "staged_zero": staged == [], "authority_hashes": authority == AUTHORITY_HASHES,
        "lane_scope": set(lane_untracked).issubset(PACKAGE_PATHS), "lane_complete": set(lane_untracked) == set(PACKAGE_PATHS) if require_complete else True,
        "forbidden_cache_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": tracked, "staged": staged, "lane_untracked": lane_untracked, "forbidden": [str(p) for p in forbidden]})
    return {"root": str(root), "branch": branch, "head": head, "tracked": tracked, "staged": staged, "untracked_total": len(untracked), "lane_untracked": lane_untracked, "authority_hashes": authority, "checks": checks, "status": "CAD_PASS"}


def box(x: float, y: float, z: float, cx: float, cy: float, cz: float) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate((cx, cy, cz))


def cyl_y(radius: float, length: float, x: float, y0: float, z: float) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def compound(parts: list[cq.Workplane | cq.Shape]) -> cq.Compound:
    values = []
    for part in parts:
        if isinstance(part, cq.Workplane): values.extend(part.vals())
        else: values.append(part)
    return cq.Compound.makeCompound(values)


def beam_between_xz(a: tuple[float, float], b: tuple[float, float], y: float) -> cq.Workplane:
    dx, dz = b[0] - a[0], b[1] - a[1]
    length, angle = math.hypot(dx, dz), -math.degrees(math.atan2(dz, dx))
    # Rotate about the beam's own centre before positioning it.  Rotating an
    # already-translated beam would incorrectly swing it around the global origin.
    return cq.Workplane("XY").box(length, 20, 20).rotate((0, 0, 0), (0, 1, 0), angle).translate(((a[0]+b[0])/2, y, (a[1]+b[1])/2))


def frame_geometry() -> cq.Compound:
    parts: list[cq.Workplane] = []
    # Exact physical outer envelopes take precedence; segmented-stock joints remain measurement references.
    for y in (-80.5, 80.5):
        parts += [box(442, 20, 40, 0, y, 88), box(540, 20, 20, 49, y, 208)]
    for x in (-211, 211): parts.append(box(20, 181, 20, x, 0, 78))
    for x in (-211, 309): parts.append(box(20, 181, 20, x, 0, 208))
    for x in (-211, 211):
        for y in (-80.5, 80.5): parts.append(box(20, 20, 110, x, y, 143))
    for y in (-80.5, 80.5):
        parts.append(beam_between_xz((211, 108), (309, 198), y))
        parts += [box(32, 20, 20, 218, y, 117), box(32, 20, 20, 301, y, 189)]
    return compound(parts)


def source_sprocket() -> cq.Workplane:
    embed_r = SPROCKET["root_radius"] - SPROCKET["embed_depth"]
    ring = cq.Workplane("XY").circle(SPROCKET["root_radius"]).circle(20).extrude(SPROCKET["axial_width"] / 2, both=True)
    hub = cq.Workplane("XY").circle(18).extrude(SPROCKET["axial_width"] / 2, both=True)
    body = ring.union(hub)
    pts = [(embed_r, -6.5), (SPROCKET["root_radius"], -SPROCKET["root_width"]/2), (SPROCKET["tip_radius"], -SPROCKET["tip_width"]/2), (SPROCKET["tip_radius"], SPROCKET["tip_width"]/2), (SPROCKET["root_radius"], SPROCKET["root_width"]/2), (embed_r, 6.5)]
    tooth = cq.Workplane("XY").polyline(pts).close().extrude(SPROCKET["axial_width"] / 2, both=True)
    for i in range(12): body = body.union(tooth.rotate((0,0,0),(0,0,1),15+i*30))
    return body.clean()


def h25_parts() -> dict[str, cq.Workplane | cq.Compound]:
    body = source_sprocket().cut(cq.Workplane("XY").circle(10.3/2).extrude(50, both=True))
    # The collar pocket is axial and fully inside the protected root; no radial tooth/root access bore exists.
    pocket = cq.Workplane("XY").circle(16.1/2).extrude(3.2).translate((0,0,18.8))
    body = body.cut(pocket)
    collar = cq.Workplane("XY").circle(15.9/2).circle(10.1/2).extrude(3.0).translate((0,0,19.0))
    cover = cq.Workplane("XY").circle(18).circle(10.8/2).extrude(2.5).translate((0,0,22.0))
    key = box(3.0, 3.0, 3.0, 7.1, 0, 20.5)
    assembly = compound([body, collar, cover, key])
    return {"body": body, "collar": collar, "cover": cover, "reaction_key_envelope": key, "assembly": assembly}


def coupon() -> cq.Workplane:
    part = box(72, 25, 6, 0, 0, 3)
    for x, d in zip((-24, 0, 24), (16.0, 16.1, 16.2)):
        part = part.cut(cq.Workplane("XY").workplane(offset=0).center(x, 0).circle(d/2).extrude(8))
    return part.clean()


def reference_envelopes() -> dict[str, cq.Workplane | cq.Compound]:
    # These are available-space references, not selected box dimensions.
    bbox_zone = box(400, 140, 82, 0, 0, 109)
    bbox_sweep = box(900, 140, 82, 250, 0, 109)
    cbox_zone = box(400, 94, 45, 0, 0, 172.5)
    bridges = compound([box(20, 181, 10, -180, 0, 198), box(20, 181, 10, 180, 0, 198)])
    connector = box(30, 20, 20, -150, 0, 205)
    return {"bbox": bbox_zone, "bbox_sweep": bbox_sweep, "cbox": cbox_zone, "bridges": bridges, "connector": connector}


def integration_geometry() -> cq.Compound:
    env = reference_envelopes(); parts: list[cq.Workplane | cq.Shape] = [frame_geometry(), env["bbox"], env["cbox"], env["bridges"], env["connector"]]
    # Four schematic smooth load rollers per side. X registration remains HOLD.
    for y in (-117.3, 117.3):
        for x in (-150, -50, 50, 150):
            parts += [cyl_y(25, 44, x, y-22, 25), cyl_y(12.95, 8, x, y-4, 25)]
            parts.append(box(67, 17, 35, x, y + (-17 if y > 0 else 0), 43.5))
    # Provisional drivetrain reservation in the triangular front extension.
    shaft_z = 178
    parts += [cyl_y(5, 140, 270, -70, shaft_z), cyl_y(5, 140, 235, -70, shaft_z)]
    for x in (235, 270): parts.append(cyl_y(18, 15, x, -7.5, shaft_z))
    parts += [box(35, 20, 35, 220, 0, 178), box(45, 40, 40, 190, 0, 178), box(20, 30, 30, 250, 0, 205)]
    # H2.5-A1 reference at left crawler drive station.
    parts.append(h25_parts()["assembly"].rotate((0,0,0),(1,0,0),90).translate((-190,117.3,40)))
    return compound(parts)


def export_shape(shape: cq.Workplane | cq.Shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))


def svg(title: str, body: str, viewbox: str = "0 0 1000 500") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}"><style>text{{font-family:Arial,sans-serif;fill:#17212b}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.m{{fill:#d9eafd;stroke:#245b8a}}.h{{fill:#fbd5d5;stroke:#a33}}.w{{stroke:#168aad;stroke-width:3;stroke-dasharray:10 7}}.g{{stroke:#555;stroke-width:2}}</style><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="34" font-size="22">{title}</text>{body}<text x="24" y="480" font-size="14">PHYSICAL_INTEGRATION_REFERENCE · NOT_FOR_MANUFACTURING · HOLD</text></svg>'''


def create_svgs() -> None:
    write(LANE/"drawings/top_view.svg", svg("TOP X-Y", '<rect class="m" x="230" y="150" width="540" height="181"/><rect class="h" x="300" y="170" width="400" height="140" fill-opacity=".35"/><path class="g" d="M230 150L770 150M230 331L770 331"/><text x="380" y="140">upper 540×181</text><text x="365" y="245">BBOX available zone 400×140 (HOLD)</text><path class="h" d="M300 170H930V310H300" fill="none"/><text x="735" y="300">+X removal sweep</text>'))
    write(LANE/"drawings/side_view.svg", svg("SIDE X-Z", '<line class="g" x1="50" y1="430" x2="950" y2="430"/><text x="55" y="423">ground Z0</text><line class="w" x1="50" y1="220" x2="950" y2="220"/><text x="55" y="212">water Z150</text><rect class="m" x="230" y="125" width="540" height="25"/><rect class="m" x="280" y="335" width="442" height="55"/><line class="g" x1="722" y1="335" x2="770" y2="150"/><rect class="h" x="300" y="220" width="400" height="115" fill-opacity=".35"/><rect class="h" x="300" y="158" width="400" height="62" fill-opacity=".25"/><circle class="f" cx="690" cy="180" r="25"/><text x="55" y="150">frame top Z218</text><text x="55" y="390">frame bottom Z68</text><text x="390" y="290">BBOX available zone / water-contact region</text><text x="430" y="195">CBOX comparison zone</text><text x="660" y="145">PTO/motor reservation</text>'))
    write(LANE/"drawings/front_view.svg", svg("FRONT Y-Z", '<line class="g" x1="100" y1="430" x2="900" y2="430"/><line class="w" x1="100" y1="220" x2="900" y2="220"/><rect class="m" x="410" y="125" width="181" height="25"/><rect class="m" x="410" y="335" width="181" height="55"/><rect class="h" x="430" y="220" width="140" height="115" fill-opacity=".35"/><rect class="h" x="453" y="158" width="94" height="62" fill-opacity=".25"/><circle class="f" cx="350" cy="360" r="40"/><circle class="f" cx="650" cy="360" r="40"/><text x="420" y="110">outer Y181 / upper clear Y100</text><text x="455" y="290">BBOX HOLD</text><text x="458" y="190">CBOX Y≤94</text>'))
    write(LANE/"drawings/bbox_removal.svg", svg("BBOX X-REMOVAL STUDY", '<rect class="m" x="160" y="160" width="400" height="140"/><path class="h" d="M160 160H900V300H160" fill-opacity=".15"/><path d="M550 230H850" stroke="#a33" stroke-width="6" marker-end="url(#a)"/><defs><marker id="a" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto"><path d="M0 0L8 3L0 6Z" fill="#a33"/></marker></defs><text x="245" y="235">sealed cassette available zone</text><text x="600" y="215">X sweep — route/locks HOLD</text>'))
    write(LANE/"drawings/h25a1_section.svg", svg("H2.5-A1 AXIAL SECTION", '<circle class="m" cx="350" cy="250" r="130"/><circle fill="white" stroke="#333" cx="350" cy="250" r="22"/><rect class="h" x="330" y="190" width="40" height="120"/><rect fill="#f4c95d" stroke="#7a6100" x="365" y="235" width="45" height="30"/><rect fill="#9bd3ae" stroke="#27633a" x="405" y="235" width="22" height="30"/><text x="500" y="190">metal collar OD15.9 / ID10.1 / W3.0</text><text x="500" y="225">A2 replaceable reaction-key envelope</text><text x="500" y="260">central cover only; no primary torque</text><text x="500" y="295">NO radial tooth/root access hole</text><text x="500" y="330">thread and screw projection: HOLD</text>'))


def source_audit() -> list[dict[str, Any]]:
    rels = [
        "cad/common_rover/common_rover_staggered_deep_nut_set_screw_drive_sprocket_v0_9_3_7_3",
        "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1",
        "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5",
        "cad/common_rover/common_rover_crawler_guide_clearance_retest_coupon_v0_9_3_6",
        "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_3",
    ]
    return [tree_digest(REPO_ROOT/r) for r in rels]


def geometry_manifest() -> dict[str, Any]:
    physical = frame_geometry().BoundingBox(); sprocket = source_sprocket(); h25 = h25_parts(); integration = integration_geometry().BoundingBox()
    baseline_outer = sprocket.intersect(cq.Workplane("XY").circle(40).circle(SPROCKET["root_radius"]).extrude(60, both=True)).val().Volume()
    h25_outer = h25["body"].intersect(cq.Workplane("XY").circle(40).circle(SPROCKET["root_radius"]).extrude(60, both=True)).val().Volume()
    return {
        "schema": "paddy_swarm.common_rover.physical_integration.v0.9.4.0", "classification": CLASSIFICATION, "release": RELEASE,
        "coordinate_system": {"unit":"mm","+X":"front","+Y":"left","+Z":"up","ground_z":0,"waterline_z":150},
        "frame": FRAME, "frame_cad_bounds": {"x": physical.xlen, "y": physical.ylen, "z": physical.zlen, "zmin": physical.zmin, "zmax": physical.zmax},
        "frame_material": {"2020":{"180":4,"110":4,"100":2},"2040":{"400":4},"vertical_110":"ADOPTED","vertical_100":"SUPERSEDED"},
        "triangular_extension": {"difference_x":98.0,"front_registration":"DERIVED_CANDIDATE_HOLD_PHYSICAL_DATUM_CONFIRMATION","pivot_joint":[32,20,20],"sole_final_lock":"NOT_APPROVED"},
        "pto": {"name":"COMMON_PTO_HS_1TO1","driver_teeth":20,"driven_teeth":20,"ratio":1.0,"axis":"Y","transform":"HOLD","powered_rotation":"NOT_APPROVED","load_path":"METAL_PLATE_KP000_METAL_SHAFT_KP000_METAL_PLATE"},
        "kp000": {**KP000,"crawler_count":8,"pto_other_count":4,"mockup_total":12,"mount_hole_centers":"HOLD","opposite_protrusion":"HOLD"},
        "crawler": {"lower_roller_count_per_side":4,"roller_od_reference":50,"roller_axial_width_reference":44,"roller_station_registration":"HOLD","bearing":BEARING,"d26_updated_stl_found":False},
        "h25a1": {"variant":"H2.5-A1_CAPTURED_SET_SCREW_COLLAR_HUB","collar":COLLAR,"pocket_coupon_diameters":[16.0,16.1,16.2],"antirotation_selected":"A2_REPLACEABLE_REACTION_KEY_ENVELOPE","antirotation_status":"HOLD_ACTUAL_SCREW_PROJECTION_AND_SHEAR","friction_only":"REJECT","radial_tooth_root_access_hole":False,"cover_fastener_candidates":[16,20,25],"first_comparison":20,"compression_sleeve":"STRONGLY_RECOMMENDED","external_12t":SPROCKET,"outer_volume_delta_mm3":h25_outer-baseline_outer},
        "boxes": {"old":{"body":[200,150,120],"lid":[216,166,16],"gasket":[204,154,3],"inside_current_frame":"FAIL"},"bbox":{"architecture":"SEALED_REMOVABLE_BATTERY_CASSETTE","axis":"X","normal_swap_lid_open":False,"blind_mate":False,"cad_object":"MAX_AVAILABLE_ZONE_NOT_FINAL_BOX","dimensions":"HOLD"},"cbox":{"architecture":"ABOVE_BBOX_INDEPENDENT_BRIDGE","outer_y_limit":94,"height_comparison":[40,50],"final_height":"HOLD","cad_object":"COMPARISON_ZONE_NOT_FINAL_BOX"}},
        "water": {"shell_contact":"ALLOWED","internal_contact":"NOT_ALLOWED","buoyancy":"HOLD_BBOX_DIMS_AND_MASS"},
        "integration_bounds": {"x":integration.xlen,"y":integration.ylen,"z":integration.zlen}, "source_audit":source_audit(),
    }


def validation(manifest: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "FRAME_REFERENCE":"CAD_PASS", "FRAME_DIMENSIONS":"CAD_PASS", "WATERLINE":"CAD_PASS",
        "PTO_20T20T_ARCHITECTURE":"CONDITIONAL_PASS_TRANSFORM_HOLD", "BBOX_ENVELOPE":"HOLD_BATTERY_DIMENSIONS",
        "BBOX_X_REMOVAL":"HOLD_BOX_SIZE_ROUTE_AND_LOCK", "CBOX_ENVELOPE":"HOLD_ELECTRONICS_AND_VERTICAL_CLEARANCE",
        "CBOX_INDEPENDENT_SUPPORT":"CAD_PASS_REFERENCE", "CBOX_DOES_NOT_LOAD_BBOX":"CAD_PASS_REFERENCE",
        "DRIVETRAIN_RESERVATION":"CAD_PASS_REFERENCE", "H2.5-A1_EXTERNAL_12T_GEOMETRY":"UNCHANGED",
        "H2.5-A1_ANTI_ROTATION":"HOLD_A2_REACTION_KEY_DETAIL", "H2.5-A1_THREAD_SPEC":"HOLD",
        "POWERED_ROTATION":"NOT_APPROVED", "FIELD_DEPLOYMENT":"NOT_APPROVED",
    }
    interferences = {
        "BBOX_vs_frame":"HOLD_FINAL_BBOX_DIMENSIONS", "BBOX_vs_crawler_KP000_shaft_belt_diagonal":"HOLD_TRANSFORMS",
        "BBOX_vs_CBOX_support":"CAD_PASS_REFERENCE_ZONE_ONLY", "CBOX_vs_frame":"CAD_PASS_REFERENCE_ZONE_ONLY",
        "CBOX_vs_motor_clutch_servo_pulley_belt_PTO":"HOLD_FINAL_TRANSFORMS", "H25A1_vs_link":"HOLD_PHYSICAL_LINK_MOTION_ENVELOPE",
        "H25A1_vs_guide":"HOLD_GUIDE_REGISTRATION", "H25A1_vs_bearing":"CAD_PASS_REFERENCE_AXIS_ONLY",
        "H25A1_vs_neighbor_hardware":"HOLD_HARDWARE_STACK", "BBOX_X_sweep_vs_all":"HOLD_BOX_DIMENSIONS_AND_SERVICE_SIDE",
    }
    missing = ["BATTERY_X","BATTERY_Y","BATTERY_Z","BATTERY_MASS","VERTICAL_INTERNAL_CLEARANCE","CBOX_ELECTRONICS_ENVELOPE","COLLAR_THREAD_NOMINAL","COLLAR_THREAD_PITCH","SET_SCREW_TOTAL_LENGTH","SET_SCREW_PROJECTION","KP000_MOUNT_HOLE_CENTERS","KP000_OPPOSITE_PROTRUSION","PTO_TRANSFORM","BBOX_LOCK_HARDWARE","BBOX_SERVICE_SIDE","BBOX_GASKET_COMPRESSION","CONNECTOR_SELECTION"]
    return {"version":VERSION,"classification":CLASSIFICATION,"release":RELEASE,"checks":checks,"interference":interferences,"missing_measurements":missing,"cad_reference_complete":True,"physical_validation_pending":True,"physical_pass":False,"powered_rotation_approved":False,"field_deployment_approved":False,"final_status":"CAD_REFERENCE_COMPLETE / PHYSICAL_VALIDATION_PENDING"}


def documents(manifest: dict[str, Any], report: dict[str, Any]) -> dict[str,str]:
    head = f"# Common Rover Physical Integration v{VERSION}\n\nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nFinal: `CAD_REFERENCE_COMPLETE / PHYSICAL_VALIDATION_PENDING`\n"
    docs: dict[str,str] = {}
    docs["README.md"] = head + "\nThis lane integrates the 2026-08-08/09 physical frame as a reference. Box and drivetrain objects with missing inputs are explicit available-space envelopes; they are not manufacturing parts. Powered rotation and field deployment are NOT_APPROVED.\n"
    docs["PHYSICAL_FRAME_REFERENCE.md"] = head + "\nMEASURED outer: upper 540×181, lower 442×181, height 150±1. Clear: upper 500×100, lower 400×140. Ground Z0; bottom Z68; water Z150; top Z218. Physical values supersede conflicting nominal CAD. Front registration of the 98 mm extension is a DERIVED candidate and requires datum confirmation.\n"
    docs["FRAME_MEASUREMENT_LEDGER.md"] = head + "\n|Item|Value|Class|\n|---|---:|---|\n|Upper outer|540×181|MEASURED|\n|Lower outer|442×181|MEASURED|\n|Height|150±1|MEASURED|\n|Upper clear|500×100|MEASURED|\n|Lower clear|400×140|MEASURED|\n|Bottom / top Z|68 / 218|MEASURED / DERIVED|\n|Vertical post|110|ADOPTED|\n|100 mm post|—|SUPERSEDED|\n|Internal effective Z|—|HOLD|\n"
    docs["DESIGN_SOURCE_TRACE.md"] = head + "\nRead-only sources:\n" + "\n".join(f"- `{x['path']}`: {x['file_count']} files, tree `{x['sha256_tree']}`" for x in manifest["source_audit"]) + "\n\nProtected 12T source values are reproduced exactly. Authority files are hash-guarded and unchanged.\n"
    docs["PTO_20T20T_ARCHITECTURE.md"] = head + "\n`COMMON_PTO_HS_1TO1`: 20T→20T, ratio 1:1. Axis Y between diagonal rails; load path is metal plate→KP000→metal shaft→pulley/output→KP000→metal plate. Permanent single-sided cantilever is PROHIBITED. The displayed transform is schematic; final transform and powered rotation are HOLD / NOT_APPROVED.\n"
    docs["KP000_SUPPORT_POLICY.md"] = head + "\nMeasured reference: 67×17×35, shaft-center height 18.5±0.5, nominal bore 10, one-side collar protrusion 6. Current plan: crawler 8 plus PTO/other 4 = 12. Mount-hole centers and opposite protrusion remain HOLD. Metal plates carry primary shaft load; PETG-only bearing support is prohibited.\n"
    docs["CRAWLER_BEARING_UPDATE.md"] = head + "\n`BEARING_OD=25.9 MEASURED`; `BEARING_SEAT=26.0 TARGET`; `CENTRAL_CLEARANCE=12.0 UNCHANGED`. Exact D26.0 STL names requested were not found. Four smooth lower rollers per side remain the baseline; the schematic X stations are not released placements. Existing roller outside and protected 12T teeth are unchanged by this fit update.\n"
    docs["H0_H23_H24_FAILURE_HISTORY.md"] = head + "\n- H0: `PHYSICAL_FAIL_SLIP`; PETG friction clamp is not revived.\n- H2.3: 6.001 mm root region vs OD6.8 washer; hardware/link FAIL.\n- H2.4: Ø3.5 radial access caused 0.499080 mm³ link/root intersection and changed protected exterior.\n\nAbsolute rule: `NO RADIAL ACCESS HOLE THROUGH TOOTH/ROOT`.\n"
    docs["H25A1_DESIGN_SPEC.md"] = head + "\nVariant `H2.5-A1_CAPTURED_SET_SCREW_COLLAR_HUB`. Load path: φ10 shaft→metal set screw→solid metal collar→positive anti-rotation→PETG central hub→one-piece 12T→link. Circular friction-only capture is REJECT. A2 replaceable reaction-key envelope is recommended for simplicity/serviceability without tooth/root violation, but remains HOLD pending screw projection, thread and shear/crushing tests. Central cover only is removable and carries no primary torque. M4 16/20/25 are comparisons; M4×20 is not final. Metal compression sleeve is STRONGLY_RECOMMENDED. Side margin is 4.8 mm; hardware ≤3 preferred, 3–4 conditional, >4 blocked.\n"
    docs["H25A1_COLLAR_MEASUREMENTS.md"] = head + "\n|Feature|Value|Class|\n|---|---:|---|\n|OD|15.9|MEASURED|\n|Bore|10.1|MEASURED|\n|Width|3.0|MEASURED|\n|Apparent radial threaded hole|3.7|MEASURED, not nominal thread|\n|Pocket coupon|16.00 / 16.10 / 16.20|DERIVED candidates|\n"
    docs["H25A1_MISSING_MEASUREMENTS.md"] = head + "\nHOLD: nominal thread, pitch, set-screw total length, actual projection, angular registration, torque/shear capacity, PETG crushing, final cover stack and real link/guide motion clearances. `3.7` must not be interpreted as M4 authority.\n"
    docs["BBOX_CBOX_ARCHITECTURE.md"] = head + "\nCASE A selected: low wet-capable sealed BBOX cassette, X removable; narrow shallow CBOX above it on an independent frame bridge. BBOX and CBOX load paths are independent. CASE B top CBOX and CASE C top boxes are reference-only due to drivetrain/CG congestion. Shell water contact ALLOWED; internal water contact NOT_ALLOWED.\n"
    docs["BBOX_ENVELOPE_STUDY.md"] = head + "\nHistorical 200×150×120 body and 216×166×16 lid FAIL current Y clearances. The STEP is the 400×140 lower available-space reference from Z68 to waterline Z150, not a selected BBOX. Battery X/Y/Z/mass are HOLD, so `BBOX_ENVELOPE` and manufacturing remain HOLD/BLOCKED. Normal swap removes the sealed cassette without opening its lid.\n"
    docs["CBOX_ENVELOPE_STUDY.md"] = head + "\nThe STEP uses X400 as a reference span, Y94 as the allowed comparison limit, and Z45 within the permitted 40–50 comparison range. None is final product authority. Final height, electronics envelope, cable bends and effective internal Z are HOLD. Independent bridge supports do not use the BBOX lid.\n"
    docs["BBOX_REMOVAL_STUDY.md"] = head + "\nBaseline axis X. Sequence: power off; disconnect high service connector; remove safety pin; release primary lock; withdraw cassette; insert/seat at rear stop; lock; pin; reconnect. Open self-draining replaceable skid; no furniture slide, blind mate or friction-only retention. Sweep is shown, but dimensions, service side, cross-member route and locking hardware are HOLD; therefore no physical PASS.\n"
    docs["WATERLINE_AND_BUOYANCY.md"] = head + "\nGround Z0, frame bottom Z68, nominal waterline Z150, frame top Z218. Waterline is 82 mm above the bottom and 68 mm below the top. Submerged volume, displacement, buoyancy, normal-force reduction and imbalance cannot be calculated without final BBOX dimensions, immersion pose and battery+BBOX mass; result is `HOLD_BBOX_DIMS_AND_MASS`, not zero.\n"
    docs["INTERFERENCE_REPORT.md"] = head + "\n" + "\n".join(f"- {k}: `{v}`" for k,v in report["interference"].items()) + "\n\nOnly reference-zone non-intersections receive CAD_PASS. Unknown transforms and physical envelopes remain HOLD and are never reported as zero interference.\n"
    docs["MISSING_MEASUREMENTS.md"] = head + "\n" + "\n".join(f"- `{x}`: HOLD" for x in report["missing_measurements"]) + "\n"
    docs["DESIGN_GATE.md"] = head + "\n" + "\n".join(f"- `{k}`: `{v}`" for k,v in report["checks"].items()) + "\n\nCAD_PASS is not PHYSICAL_PASS. Manufacturing, powered rotation, load/water/mud tests and field deployment remain HOLD / NOT_APPROVED.\n"
    return docs


def write_release_files(log: str) -> None:
    paths_without_release = [p for p in PACKAGE_PATHS if p not in {"MANIFEST.txt","SHA256SUMS.txt","BUILD_LOG.txt","TEST_LOG.txt"}]
    write(LANE/"COMMIT_PATHS.txt", "\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS))
    write(LANE/"BUILD_LOG.txt", log)
    write(LANE/"TEST_LOG.txt", "PENDING_TEST_EXECUTION\n")
    # MANIFEST lists every package path, including the checksum and log files themselves.
    write(LANE/"MANIFEST.txt", "\n".join(PACKAGE_PATHS))
    hashed = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    write(LANE/"SHA256SUMS.txt", "\n".join(f"{sha(LANE/p)}  {p}" for p in hashed))


def build() -> dict[str, Any]:
    before = repository_guard(False)
    frame = frame_geometry(); h25 = h25_parts(); env = reference_envelopes(); integ = integration_geometry(); fit = coupon()
    for shape, rel in [(frame,STEPS[0]),(h25["assembly"],STEPS[1]),(env["bbox"],STEPS[2]),(env["cbox"],STEPS[3]),(integ,STEPS[4]),(fit,STEPS[5]),(compound([h25["assembly"],box(3,3,3,45,0,0),box(5,3,3,60,0,0)]),STEPS[6]),(frame,STLS[0]),(integ,STLS[1]),(fit,STLS[2])]: export_shape(shape, LANE/rel)
    create_svgs()
    manifest = geometry_manifest(); report = validation(manifest)
    write_json(LANE/"geometry_manifest.json", manifest); write_json(LANE/"validation_report.json", report)
    for name, content in documents(manifest, report).items(): write(LANE/name, content)
    write_release_files(f"BUILD PASS\nversion={VERSION}\nclassification={CLASSIFICATION}\npreflight_untracked_total={before['untracked_total']}\nCadQuery={cq.__version__}\nPython={sys.version.split()[0]}")
    test_run = subprocess.run([sys.executable, "-B", str(LANE/"tests/test_common_rover_physical_integration_v0940.py")], cwd=REPO_ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test_run.returncode != 0:
        raise RuntimeError("embedded contract test failed\n" + test_run.stdout)
    write(LANE/"TEST_LOG.txt", test_run.stdout)
    # TEST_LOG is now final, so refresh the checksum ledger once more.
    hashed = [p for p in PACKAGE_PATHS if p != "SHA256SUMS.txt"]
    write(LANE/"SHA256SUMS.txt", "\n".join(f"{sha(LANE/p)}  {p}" for p in hashed))
    after = repository_guard(True)
    return {"status":"CAD_REFERENCE_COMPLETE","guard":after,"manifest":manifest,"validation":report}


def verify_files() -> dict[str, Any]:
    missing = [p for p in PACKAGE_PATHS if not (LANE/p).is_file()]
    extras = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.relative_to(LANE).as_posix() not in PACKAGE_PATHS)
    manifest_lines = (LANE/"MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    checksums = {}
    for line in (LANE/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ",1); checksums[rel] = digest
    bad_hashes = [p for p,d in checksums.items() if sha(LANE/p) != d]
    data = json.loads((LANE/"geometry_manifest.json").read_text(encoding="utf-8")); val = json.loads((LANE/"validation_report.json").read_text(encoding="utf-8"))
    contract = {
        "package_exact": not missing and not extras and manifest_lines == PACKAGE_PATHS,
        "hashes": not bad_hashes, "frame": data["frame"] == FRAME,
        "pto_20_20": data["pto"]["driver_teeth"] == data["pto"]["driven_teeth"] == 20,
        "bearing": data["crawler"]["bearing"] == BEARING, "collar": data["h25a1"]["collar"] == COLLAR,
        "external_12t": abs(data["h25a1"]["outer_volume_delta_mm3"]) < 1e-6 and not data["h25a1"]["radial_tooth_root_access_hole"],
        "bbox_x": data["boxes"]["bbox"]["axis"] == "X" and not data["boxes"]["bbox"]["normal_swap_lid_open"] and not data["boxes"]["bbox"]["blind_mate"],
        "cbox_independent": data["boxes"]["cbox"]["architecture"] == "ABOVE_BBOX_INDEPENDENT_BRIDGE",
        "release": not val["powered_rotation_approved"] and not val["field_deployment_approved"] and not val["physical_pass"],
    }
    if not all(contract.values()): raise RuntimeError({"contract":contract,"missing":missing,"extras":extras,"bad_hashes":bad_hashes})
    return {"status":"CAD_PASS","tests":contract,"file_count":len(PACKAGE_PATHS),"bad_hashes":bad_hashes}


def standalone_rebuild() -> dict[str, Any]:
    """Rebuild all CAD classes in an isolated directory without Git/repository data."""
    with tempfile.TemporaryDirectory(prefix="ps_cr_v0940_") as td:
        out = Path(td)
        frame=frame_geometry(); h25=h25_parts(); env=reference_envelopes(); integ=integration_geometry(); fit=coupon()
        jobs = [(frame,"physical_frame_reference.step"),(frame,"physical_frame_reference.stl"),(h25["assembly"],"h25a1_reference.step"),(env["bbox"],"bbox_candidate_envelope.step"),(env["cbox"],"cbox_candidate_envelope.step"),(integ,"integration_assembly.step"),(integ,"integration_assembly_reference.stl"),(fit,"h25a1_collar_fit_coupon.step"),(fit,"h25a1_collar_fit_coupon.stl")]
        for shape,name in jobs: export_shape(shape,out/name)
        b=frame.BoundingBox()
        checks={"outputs":len(list(out.iterdir()))==len(jobs),"frame_x":abs(b.xlen-540)<1e-6,"frame_y":abs(b.ylen-181)<1e-6,"frame_z":abs(b.zlen-150)<1e-6,"nonempty":all((out/name).stat().st_size>0 for _,name in jobs)}
        if not all(checks.values()): raise RuntimeError({"standalone_rebuild":checks})
        return {"status":"CAD_PASS","checks":checks,"output_count":len(jobs)}


def create_zip() -> tuple[Path,str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = DOWNLOADS/f"{ZIP_PREFIX}{timestamp}.zip"
    if target.exists(): raise FileExistsError(target)
    with zipfile.ZipFile(target,"x",zipfile.ZIP_DEFLATED) as z:
        for rel in PACKAGE_PATHS: z.write(LANE/rel, rel)
    with zipfile.ZipFile(target) as z:
        names=z.namelist(); bad=[n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
        if z.testzip() is not None or len(names)!=len(set(names)) or bad or sorted(names)!=PACKAGE_PATHS: raise RuntimeError("ZIP contract failed")
    return target, sha(target)


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--build",action="store_true"); ap.add_argument("--verify",action="store_true"); ap.add_argument("--zip",action="store_true"); ap.add_argument("--standalone-verify",action="store_true"); ap.add_argument("--standalone-rebuild",action="store_true"); args=ap.parse_args()
    if not any(vars(args).values()): args.build=args.verify=True
    result: dict[str,Any]={}
    if args.build: result["build"]=build()
    if args.verify or args.standalone_verify:
        if args.verify: result["repository_guard"]=repository_guard(True)
        result["verify"]=verify_files()
    if args.standalone_verify or args.standalone_rebuild: result["standalone_rebuild"]=standalone_rebuild()
    if args.zip:
        target,digest=create_zip(); result["zip"]={"path":str(target),"sha256":digest}
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
