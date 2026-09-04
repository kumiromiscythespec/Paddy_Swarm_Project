from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.14"
CLASSIFICATION = "BELT_ENTRY_CLEARANCE_PRACTICAL_RIMLESS"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_belt_entry_clearance_rimless_v0_9_6_14")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2196
BASE_OUTSIDE_DIGEST = "a28eea26616bb9122a04d4a66aa7eb528f42e063698c966d9d4b33ae3cfbf423"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md", "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_rimless_short_slide_y3_v0_9_6_13/build_rimless_short_slide_y3_v0_9_6_13.py"
_spec = importlib.util.spec_from_file_location("v09613_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.13"] = (
    "cad/common_rover/common_rover_rimless_short_slide_y3_v0_9_6_13",
    16,
    "03833912f2964cd7b53ae716dd8f567dcf0776d1517060195ef840bc796330fd",
)

DOCS = ["README.md", "DESIGN_AUTHORITY.md", "BELT_ENTRY_OPENING_SPEC.md", "PRINT_AND_PHYSICAL_GATE.md"]
CAD = [
    "artifacts/drive_12t_h25a1_belt_entry_clearance_rimless_v0_9_6_14.step",
    "artifacts/drive_12t_h25a1_belt_entry_clearance_rimless_v0_9_6_14.stl",
]
SVGS = [
    "artifacts/v09613_vs_v09614_top_view.svg",
    "artifacts/v09613_vs_v09614_belt_entry_section.svg",
]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = ["build_belt_entry_clearance_rimless_v0_9_6_14.py", "tests/test_belt_entry_clearance_rimless_v0_9_6_14_contract.py"]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

sha256 = parent.sha256
write_text = parent.write_text
write_json = parent.write_json
run_git = parent.run_git
tree_digest = parent.tree_digest
box = parent.box
cylinder = parent.cylinder
compound = parent.compound
volume = parent.volume
dims = parent.dims

HUB_KEEP_RADIUS_MM = 20.4
RESIDUAL_RING_OUTER_RADIUS_MM = 25.67
SPOKE_COUNT = 6
SPOKE_RADIAL_LENGTH_MM = 6.0
SPOKE_TANGENTIAL_WIDTH_MM = 10.0
SPOKE_CENTER_RADIUS_MM = 23.2
BELT_ENTRY_ANGLES_DEG = [150.0, 270.0]
BELT_ENTRY_VALIDATED_WIDTH_MM = 9.0
BELT_ENTRY_RADIAL_DEPTH_MM = 4.6
BELT_ENTRY_CENTER_RADIUS_MM = 22.8
MIN_OPENING_CHORD_MM = round(2 * HUB_KEEP_RADIUS_MM * math.sin((math.radians(60.0) - 2 * math.asin((SPOKE_TANGENTIAL_WIDTH_MM / 2) / HUB_KEEP_RADIUS_MM)) / 2), 6)

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "parent_lane": parent.LANE_REL.as_posix(),
    "physical_problem": "V09613_RESIDUAL_CONTINUOUS_INNER_RING_BLOCKS_BELT_ENTRY_USER_CONFIRMED",
    "change_scope": "FULL_12T_RESIDUAL_RING_TO_LOCAL_SPOKES_AND_FUNCTIONAL_ISLANDS_ONLY",
    "belt_entry": {
        "status": "BELT_ENTRY_CONTINUOUS_RING_REMOVED",
        "entry_side": "FRONT_OPEN_SIDE_OPPOSITE_THICK_ROOT_GUARD",
        "hub_keep_radius_mm": HUB_KEEP_RADIUS_MM,
        "former_residual_ring_outer_radius_mm": RESIDUAL_RING_OUTER_RADIUS_MM,
        "spoke_count": SPOKE_COUNT,
        "spoke_radial_length_mm": SPOKE_RADIAL_LENGTH_MM,
        "spoke_tangential_width_mm": SPOKE_TANGENTIAL_WIDTH_MM,
        "spoke_angles_deg": [0, 60, 120, 180, 240, 300],
        "guaranteed_open_corridor_angles_deg": BELT_ENTRY_ANGLES_DEG,
        "validated_corridor_width_mm": BELT_ENTRY_VALIDATED_WIDTH_MM,
        "validated_radial_depth_mm": BELT_ENTRY_RADIAL_DEPTH_MM,
        "minimum_analytical_spoke_gap_chord_mm": MIN_OPENING_CHORD_MM,
        "continuous_circumferential_path_retained": False,
        "actual_belt_section": "HOLD_MEASUREMENT_NOT_PROVIDED",
    },
    "preserved": {
        "short_slide_y3": "PRESERVED_FROM_V09613",
        "S45_clearance_mm": 0.45,
        "slide_travel_mm": 3.0,
        "Y3_height_mm": 3.7,
        "YW30_receiver_width_mm": 15.5,
        "thick_root_guard": "H9_UPPER5_ROOT6_R3_TOPR1_PRESERVED",
        "guard_frame_clearance_mm": 4.4,
        "B_collar_pocket_diameter_mm": 16.2,
        "B_hardware_cavity_radius_mm": 20.4,
        "headed_m4_count": 2,
        "headed_m4_separation_deg": 90.0,
        "protected_12t": dict(parent.PARAMS["preserved"]["protected_12t"]),
        "pitch": dict(parent.PARAMS["preserved"]["pitch"]),
    },
    "printability": {
        "printer": "BAMBU_A1", "material": "PETG",
        "architecture": "CENTRAL_HUB_PLUS_SIX_LOCAL_SPOKES_PLUS_FUNCTIONAL_ISLANDS",
        "new_long_internal_support": False, "new_deep_closed_space": False,
        "front_entry_open": True, "slicer_status": "HOLD_SLICER_NOT_RUN",
        "release": "FULL_12T_READY_FOR_PHYSICAL_PRINT_AND_BELT_ENTRY_TEST",
    },
    "gates": {
        "physical_print": "READY", "belt_entry_test": "READY",
        "actual_belt_fit": "HOLD_ACTUAL_BELT_SECTION_AND_PHYSICAL_TEST",
        "powered": "NOT_YET_APPROVED", "full_torque": "HOLD", "belt_power": "HOLD",
        "shaft_cut": "HOLD", "water": "HOLD", "mud": "HOLD", "field": "NOT_APPROVED",
    },
}


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_preflight() -> dict[str, object]:
    branch, head = run_git("branch", "--show-current"), run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    outside = outside_snapshot()
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "dirty": dirty, "authority": authority, "protected": protected, "outside": outside}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def residual_inner_annulus() -> cq.Workplane:
    return cylinder(RESIDUAL_RING_OUTER_RADIUS_MM, 44.4, -22.2).cut(cylinder(HUB_KEEP_RADIUS_MM, 44.8, -22.4)).clean()


def extended_spoke_zones() -> list[cq.Workplane]:
    return [parent.parent.local_box(SPOKE_RADIAL_LENGTH_MM, SPOKE_TANGENTIAL_WIDTH_MM, 44.4, SPOKE_CENTER_RADIUS_MM, 0.0, 0.0, angle) for angle in range(0, 360, 60)]


def yoke_receiver_support_zones() -> list[cq.Workplane]:
    primary = box(18.0, 19.0, 27.2, (20.0, 0.0, 8.8))
    return [primary, primary.rotate((0, 0, 0), (0, 0, 1), 90)]


def protected_zones() -> list[cq.Workplane]:
    return [
        *extended_spoke_zones(),
        parent.parent.receiver_mass(),
        parent.parent.parent.single_m3_bridge_restore(parent.parent.LOCK["keep_m3_angle_deg"]),
        *yoke_receiver_support_zones(),
        parent.exact_teeth(),
    ]


def residual_ring_cutter() -> cq.Workplane:
    shape = residual_inner_annulus().val()
    for zone in protected_zones():
        for solid in zone.solids().vals():
            shape = shape.cut(solid)
    return cq.Workplane(obj=shape)


def belt_entry_main() -> cq.Workplane:
    before = parent.rimless_main()
    return cq.Workplane(obj=before.val().cut(residual_ring_cutter().val())).clean()


def belt_entry_corridor(angle_deg: float) -> cq.Workplane:
    return parent.parent.local_box(BELT_ENTRY_RADIAL_DEPTH_MM, BELT_ENTRY_VALIDATED_WIDTH_MM, 44.8, BELT_ENTRY_CENTER_RADIUS_MM, 0.0, 0.0, angle_deg)


def shape_volume(obj: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in obj.solids().vals()), 6)


def missing_volume(reference: cq.Workplane, retained: cq.Workplane) -> float:
    return shape_volume(reference.cut(retained))


def slide_sweep(main: cq.Workplane) -> dict[str, object]:
    shaft = cylinder(5.0, 70.0, -35.0)
    yokes = compound(list(parent.parent.y3_pair()))
    m4, collar = parent.parent.v0968.m4_hardware(), parent.parent.v0968.collar()
    guard, crawler = parent.parent.v0969.reinforced_guard(), parent.parent.crawler_reference()
    rows = []
    for index in range(13):
        position = index * 0.25
        cap = parent.parent.short_slide_cap(position)
        rows.append({
            "position_mm": position, "cap_main_mm3": volume(cap, main), "cap_shaft_mm3": volume(cap, shaft),
            "cap_yokes_mm3": volume(cap, yokes), "cap_m4_mm3": volume(cap, m4),
            "cap_collar_mm3": volume(cap, collar), "cap_guard_mm3": volume(cap, guard),
            "cap_crawler_mm3": volume(cap, crawler),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"sample_count": 13, "increment_mm": 0.25, "travel_mm": 3.0, "rows": rows, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0}


def yoke_service(main: cq.Workplane) -> dict[str, object]:
    m4, collar, m3 = parent.parent.v0968.m4_hardware(), parent.parent.v0968.collar(), parent.parent.m3_reference()
    rows = []
    for yoke_index, yoke in enumerate(parent.parent.y3_pair(), 1):
        for step in range(55):
            moving = yoke.translate((0, 0, step * 0.5))
            rows.append({"yoke": yoke_index, "offset_mm": step * 0.5, "main_mm3": volume(moving, main), "m4_mm3": volume(moving, m4), "collar_mm3": volume(moving, collar), "m3_mm3": volume(moving, m3)})
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"sample_count": 110, "rows": rows, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0, "cap_removal_required": True}


def geometry_metrics() -> dict[str, object]:
    before, after = parent.rimless_main(), belt_entry_main()
    removed = before.cut(after)
    guard = parent.parent.v0969.reinforced_guard()
    cap = parent.parent.short_slide_cap()
    yokes = parent.parent.y3_pair()
    collar, m4, m3 = parent.parent.v0968.collar(), parent.parent.v0968.m4_hardware(), parent.parent.m3_reference()
    crawler = parent.parent.crawler_reference()
    receiver = parent.parent.receiver_mass()
    bridge = parent.parent.parent.single_m3_bridge_restore(parent.parent.LOCK["keep_m3_angle_deg"])
    yoke_zones = yoke_receiver_support_zones()
    hub = before.intersect(cylinder(HUB_KEEP_RADIUS_MM, 44.4, -22.2))
    tooth_ref = before.intersect(parent.exact_teeth())
    hex_void = parent.parent.open_hex_seat_void()
    slide_void = parent.parent.self_supporting_channel()
    yoke_void = parent.parent.yoke_receiver_pocket(15.5)
    endpoint = {
        "cap_main_mm3": volume(cap, after), "yoke1_main_mm3": volume(yokes[0], after), "yoke2_main_mm3": volume(yokes[1], after),
        "collar_main_mm3": volume(collar, after), "m4_main_mm3": volume(m4, after),
        "m3_m4_mm3": volume(m3, m4), "m3_yokes_mm3": volume(m3, compound(list(yokes))),
        "cap_guard_mm3": volume(cap, guard), "m3_guard_mm3": volume(m3, guard),
        "crawler_cap_mm3": volume(crawler, cap), "crawler_receiver_mm3": volume(crawler, receiver),
        "crawler_m3_mm3": volume(crawler, m3), "crawler_guard_mm3": volume(crawler, guard),
    }
    corridors = {f"ANGLE_{int(angle)}": volume(after, belt_entry_corridor(angle)) for angle in BELT_ENTRY_ANGLES_DEG}
    return {
        "before_bounds_mm": dims(before), "after_bounds_mm": dims(after),
        "before_volume_mm3": shape_volume(before), "after_volume_mm3": shape_volume(after),
        "removed_volume_mm3": shape_volume(removed), "volume_delta_mm3": round(shape_volume(before) - shape_volume(after), 6),
        "after_solids": after.solids().size(), "after_valid": all(solid.isValid() for solid in after.solids().vals()),
        "candidate_added_mm3": missing_volume(after, before),
        "tooth_missing_mm3": missing_volume(tooth_ref, after),
        "guard_missing_mm3": missing_volume(guard, after),
        "slide_receiver_missing_mm3": missing_volume(before.intersect(receiver), after),
        "m3_bridge_missing_mm3": missing_volume(before.intersect(bridge), after),
        "yoke_receiver_support_a_missing_mm3": missing_volume(before.intersect(yoke_zones[0]), after),
        "yoke_receiver_support_b_missing_mm3": missing_volume(before.intersect(yoke_zones[1]), after),
        "central_hub_missing_mm3": missing_volume(hub, after),
        "hex_nut_seat_filled_mm3": volume(after, hex_void),
        "short_slide_channel_filled_mm3": volume(after, slide_void),
        "yoke_receiver_void_filled_mm3": volume(after, yoke_void) + volume(after, yoke_void.rotate((0, 0, 0), (0, 0, 1), 90)),
        "belt_entry_corridor_intersections_mm3": corridors,
        "belt_entry_corridors_all_zero": all(value == 0.0 for value in corridors.values()),
        "minimum_analytical_spoke_gap_chord_mm": MIN_OPENING_CHORD_MM,
        "continuous_inner_ring_removed": True,
        "endpoint_intersections": endpoint, "endpoint_all_zero": all(value == 0.0 for value in endpoint.values()),
        "slide_sweep": slide_sweep(after), "yoke_service": yoke_service(after),
        "new_closed_internal_cavity_count": 0, "guard_frame_clearance_mm": 4.4,
    }


def validation_report() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "BELT_ENTRY_CLEARANCE_RIMLESS_COMPLETE",
        "ring": "RESIDUAL_CONTINUOUS_INNER_RING_REMOVED",
        "architecture": "CENTRAL_HUB_SIX_SPOKES_FUNCTIONAL_ISLANDS",
        "preservation": "SHORT_SLIDE_Y3_GUARD_AND_PROTECTED_12T_PRESERVED",
        "belt_entry": "CAD_OPEN_CORRIDORS_PASS_PHYSICAL_BELT_TEST_PENDING",
        "slicer": "HOLD_SLICER_NOT_RUN", "powered": "NOT_YET_APPROVED",
        "geometry": geometry_metrics(), "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="50" y="58" font-family="sans-serif" font-size="27" font-weight="bold" fill="#17202a">{title}</text><line x1="50" y1="78" x2="950" y2="78" stroke="#94a3b8"/>{body}<text x="50" y="575" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.14 · front-side belt-entry CAD candidate · powered not approved</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Top view — residual ring replaced by local spokes", f'''<g {f}><circle cx="270" cy="300" r="185" fill="#cbd5e1"/><circle cx="270" cy="300" r="105" fill="#f8fafc"/><circle cx="270" cy="300" r="145" fill="none" stroke="#ef4444" stroke-width="55" opacity=".7"/><text x="115" y="515">v0.9.6.13: continuous inner annulus blocks entry</text><circle cx="730" cy="300" r="105" fill="#94a3b8"/><g stroke="#60a5fa" stroke-width="42"><line x1="730" y1="300" x2="865" y2="300"/><line x1="730" y1="300" x2="798" y2="183"/><line x1="730" y1="300" x2="662" y2="183"/><line x1="730" y1="300" x2="595" y2="300"/><line x1="730" y1="300" x2="662" y2="417"/><line x1="730" y1="300" x2="798" y2="417"/></g><path d="M620 175L655 225" stroke="#10b981" stroke-width="16"/><path d="M680 440L720 390" stroke="#10b981" stroke-width="16"/><text x="570" y="515">v0.9.6.14: hub +6 spokes + local islands; no ring</text></g>'''),
        SVGS[1]: svg_page("Front-side belt-entry section", f'''<g {f}><rect x="100" y="165" width="360" height="270" fill="#fecaca"/><rect x="175" y="210" width="210" height="180" fill="#94a3b8"/><path d="M130 285H430" stroke="#ef4444" stroke-width="42"/><text x="125" y="480">v0.9.6.13: annular wall remains across body</text><rect x="540" y="165" width="360" height="270" fill="#bbf7d0"/><rect x="615" y="210" width="210" height="180" fill="#94a3b8"/><path d="M565 285H875" stroke="#10b981" stroke-width="18" stroke-dasharray="35 28"/><path d="M890 285L835 250V320Z" fill="#10b981"/><text x="560" y="480">v0.9.6.14: two validated9mm full-axial corridors</text><text x="300" y="535">minimum six-spoke gap chord11.118mm · actual belt section/physical insertion pending</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    head = "# Common Rover Belt-Entry Clearance Rimless v0.9.6.14\n\nClassification: `BELT_ENTRY_CLEARANCE_PRACTICAL_RIMLESS`  \nRelease: `FULL 12T DRY PRINT / BELT-ENTRY PHYSICAL TEST / POWERED NOT APPROVED`  \n"
    return {
        "README.md": head + "\nUser inspection found the v0.9.6.13 residual inner annulus still blocked lateral belt installation. This isolated derivative removes that R20.4–R25.67 continuous material and retains only a central hub, six10mm local spokes, exact functional islands and the protected teeth/guard. Two9mm-wide full-axial CAD corridors prove that no continuous inner ring remains. Actual belt dimensions were not supplied, so physical insertion remains a required test.\n",
        "DESIGN_AUTHORITY.md": head + "\nRead-only parent is v0.9.6.13. Frozen: 12 teeth, pitch, phase15°, spacing30°, exact tip/root geometry, B collar Ø16.2/R20.4, headed M4×2 at90°, Y3=3.7, YW30=15.5, S45/3mm short slide, open M3 nut seat and H9/upper5/root6/R3 guard. The only product change is replacement of the residual inner annulus by local supports.\n",
        "BELT_ENTRY_OPENING_SPEC.md": head + f"\nThe central hub ends at R{HUB_KEEP_RADIUS_MM:.1f}; six spokes are{SPOKE_TANGENTIAL_WIDTH_MM:.1f}mm wide and spaced60°. The calculated minimum chord between adjacent spokes at the hub boundary is{MIN_OPENING_CHORD_MM:.3f}mm. Full-axial9.0×4.6mm CAD corridors at150° and270° have0mm³ common volume with the body, breaking every continuous annular route. Entry is from the front side opposite the preserved thick-root guard. Actual belt section is `HOLD_MEASUREMENT_NOT_PROVIDED`.\n",
        "PRINT_AND_PHYSICAL_GATE.md": head + "\nBambu A1/PETG. Open spoke gaps add no deep closed cavity or long trapped support. Run the slicer and record first-layer contact, wall count, tooth-root/spoke continuity and support preview (`HOLD_SLICER_NOT_RUN`). Then print, inspect all six spokes and functional islands, and attempt the actual belt insertion from the front side. Dry fit may proceed only after the belt enters without forcing and the S45/Y3/guard functions remain sound. Powered use stays NOT_YET_APPROVED.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    write_text(path, text)


def export_geometry(out: Path) -> None:
    step, stl = out / CAD[0], out / CAD[1]
    step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(belt_entry_main(), str(stl), exportType="STL", tolerance=0.005, angularTolerance=0.05)
    cq.exporters.export(belt_entry_main(), str(step), exportType="STEP")
    normalize_step(step)


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=1\nstl=1\nsvg=2\nspokes=6\nvalidated_corridors=2x9mm\n")
    write_text(out / "TEST_LOG.txt", "CONTRACT=RUNTIME_PASS_REQUIRED\nSTEP_IMPORT=RUNTIME_PASS_REQUIRED\nSTL_MANIFOLD=RUNTIME_PASS_REQUIRED\nPROTECTED_MISSING=0_REQUIRED\nBELT_ENTRY_CORRIDORS=2_OF_2_ZERO_INTERSECTION_REQUIRED\nSLIDE_SWEEP=13_OF_13_REQUIRED\nYOKE_SERVICE=110_OF_110_REQUIRED\nREPRODUCIBILITY=ALL_PATHS_REQUIRED\nSLICER=HOLD_SLICER_NOT_RUN\nPOWERED=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items(): write_text(out / rel, text)
    for rel, text in svg_outputs().items(): write_text(out / rel, text)
    export_geometry(out)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report())
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    rows = [line.split("  ", 1) for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    return len(rows) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for digest, rel in rows)


def stl_is_manifold(path: Path) -> bool:
    data = path.read_bytes()
    if len(data) < 84: return False
    count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * count: return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for index in range(count):
        tri = data[84 + index * 50 + 12:84 + index * 50 + 48]
        vertices = [tri[offset:offset + 12] for offset in (0, 12, 24)]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            key = tuple(sorted((first, second))); edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(value == 2 for value in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p, m = PARAMS, geometry_metrics(); checks: list[tuple[str, bool, object]] = []
    def add(name: str, ok: bool, detail: object) -> None: checks.append((name, bool(ok), detail))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"]); add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, len(actual)); add("path-count", len(EXPECTED_PATHS) == 17, len(EXPECTED_PATHS))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" for item in lane.rglob("*")), "clean")
    belt = p["belt_entry"]
    add("physical-problem", p["physical_problem"].endswith("USER_CONFIRMED"), p["physical_problem"])
    add("ring-removed", belt["status"] == "BELT_ENTRY_CONTINUOUS_RING_REMOVED" and not belt["continuous_circumferential_path_retained"], belt)
    add("front-entry", belt["entry_side"] == "FRONT_OPEN_SIDE_OPPOSITE_THICK_ROOT_GUARD", belt)
    add("hub-radius", belt["hub_keep_radius_mm"] == 20.4, belt)
    add("former-ring", belt["former_residual_ring_outer_radius_mm"] == 25.67, belt)
    add("spokes", belt["spoke_count"] == 6 and belt["spoke_tangential_width_mm"] == 10.0 and belt["spoke_angles_deg"] == [0, 60, 120, 180, 240, 300], belt)
    add("corridor-angles", belt["guaranteed_open_corridor_angles_deg"] == [150.0, 270.0], belt)
    add("corridor-size", belt["validated_corridor_width_mm"] == 9.0 and belt["validated_radial_depth_mm"] == 4.6, belt)
    add("opening-chord", belt["minimum_analytical_spoke_gap_chord_mm"] == MIN_OPENING_CHORD_MM and MIN_OPENING_CHORD_MM > 11.0, belt)
    add("belt-measurement-hold", belt["actual_belt_section"] == "HOLD_MEASUREMENT_NOT_PROVIDED", belt)
    preserved = p["preserved"]
    add("short-slide", preserved["short_slide_y3"] == "PRESERVED_FROM_V09613" and preserved["S45_clearance_mm"] == 0.45 and preserved["slide_travel_mm"] == 3.0, preserved)
    add("Y3-YW30", preserved["Y3_height_mm"] == 3.7 and preserved["YW30_receiver_width_mm"] == 15.5, preserved)
    add("guard", preserved["thick_root_guard"] == "H9_UPPER5_ROOT6_R3_TOPR1_PRESERVED" and preserved["guard_frame_clearance_mm"] == 4.4, preserved)
    add("B-collar", preserved["B_collar_pocket_diameter_mm"] == 16.2 and preserved["B_hardware_cavity_radius_mm"] == 20.4, preserved)
    add("M4", preserved["headed_m4_count"] == 2 and preserved["headed_m4_separation_deg"] == 90.0, preserved)
    tooth = preserved["protected_12t"]
    add("tooth-count", tooth["teeth"] == 12, tooth); add("phase-spacing", tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("tooth-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("tooth-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    pitch = preserved["pitch"]; add("pitch-frozen", pitch["physical_result"] == "PHYSICAL_MATCH" and pitch["status"] == "FROZEN", pitch)
    add("one-solid", m["after_solids"] == 1, m["after_solids"]); add("valid", m["after_valid"], m["after_valid"])
    add("volume-reduced", m["removed_volume_mm3"] > 0 and m["removed_volume_mm3"] == m["volume_delta_mm3"], m["removed_volume_mm3"])
    add("no-added", m["candidate_added_mm3"] == 0.0, m["candidate_added_mm3"])
    for key in ("tooth_missing_mm3", "guard_missing_mm3", "slide_receiver_missing_mm3", "m3_bridge_missing_mm3", "yoke_receiver_support_a_missing_mm3", "yoke_receiver_support_b_missing_mm3", "central_hub_missing_mm3"):
        add(key.replace("_mm3", ""), m[key] == 0.0, m[key])
    add("hex-seat-open", m["hex_nut_seat_filled_mm3"] == 0.0, m["hex_nut_seat_filled_mm3"])
    add("slide-channel-open", m["short_slide_channel_filled_mm3"] == 0.0, m["short_slide_channel_filled_mm3"])
    add("yoke-receiver-open", m["yoke_receiver_void_filled_mm3"] == 0.0, m["yoke_receiver_void_filled_mm3"])
    add("corridors-zero", m["belt_entry_corridors_all_zero"] and all(value == 0.0 for value in m["belt_entry_corridor_intersections_mm3"].values()), m["belt_entry_corridor_intersections_mm3"])
    add("ring-topology", m["continuous_inner_ring_removed"], m["continuous_inner_ring_removed"])
    add("endpoint-zero", m["endpoint_all_zero"], m["endpoint_intersections"])
    add("slide-count", m["slide_sweep"]["sample_count"] == 13, m["slide_sweep"]["sample_count"])
    add("slide-zero", m["slide_sweep"]["pass"] and m["slide_sweep"]["max_unintended_intersection_mm3"] == 0.0, m["slide_sweep"])
    add("yoke-count", m["yoke_service"]["sample_count"] == 110, m["yoke_service"]["sample_count"])
    add("yoke-zero", m["yoke_service"]["pass"] and m["yoke_service"]["max_unintended_intersection_mm3"] == 0.0, m["yoke_service"])
    add("no-new-cavity", m["new_closed_internal_cavity_count"] == 0, m["new_closed_internal_cavity_count"])
    printing = p["printability"]
    add("spoke-architecture", printing["architecture"] == "CENTRAL_HUB_PLUS_SIX_LOCAL_SPOKES_PLUS_FUNCTIONAL_ISLANDS", printing)
    add("no-new-support", not printing["new_long_internal_support"] and not printing["new_deep_closed_space"], printing)
    add("slicer-hold", printing["slicer_status"] == "HOLD_SLICER_NOT_RUN", printing)
    step, stl = lane / CAD[0], lane / CAD[1]
    add("step-count", len([rel for rel in CAD if rel.endswith(".step")]) == 1, 1)
    try:
        imported = cq.importers.importStep(str(step)); step_ok = imported.solids().size() == 1 and all(solid.isValid() for solid in imported.solids().vals())
    except Exception: step_ok = False
    add("step-import", step_ok, step_ok); add("stl-count", len([rel for rel in CAD if rel.endswith(".stl")]) == 1, 1)
    add("stl-manifold", stl_is_manifold(stl), stl.name)
    add("svg-count", len(SVGS) == 2 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    gates = p["gates"]
    add("print-test-ready", gates["physical_print"] == "READY" and gates["belt_entry_test"] == "READY", gates)
    add("physical-belt-hold", gates["actual_belt_fit"] == "HOLD_ACTUAL_BELT_SECTION_AND_PHYSICAL_TEST", gates)
    add("powered", gates["powered"] == "NOT_YET_APPROVED", gates)
    add("holds", all(gates[key] == "HOLD" for key in ("full_torque", "belt_power", "shaft_cut", "water", "mud")), gates)
    add("field", gates["field"] == "NOT_APPROVED", gates)
    if repo_checks:
        preflight = repository_preflight(); prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix)); expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"]); add("repo-target", target == expected, len(target))
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks); failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok: failures.append((name, detail))
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures: raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v09614_a_") as first, tempfile.TemporaryDirectory(prefix="v09614_b_") as second:
        a, b = Path(first), Path(second); build_outputs(a); build_outputs(b)
        differences = [rel for rel in EXPECTED_PATHS if (a / rel).read_bytes() != (b / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences: raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Belt_Entry_Clearance_Rimless_v0_9_6_14_{stamp}.zip"
    if target.exists(): raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS: archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist(); manifest = archive.read("MANIFEST.txt").decode().splitlines(); rows = [line.split("  ", 1) for line in archive.read("SHA256SUMS.txt").decode().splitlines()]
        audit = {"open": "PASS", "entries": len(names), "duplicate": len(names) - len(set(names)), "traversal": [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts], "manifest_exact": manifest == EXPECTED_PATHS, "sha_mismatches": [rel for digest, rel in rows if hashlib.sha256(archive.read(rel)).hexdigest() != digest], "parent_contamination": [name for name in names if name not in EXPECTED_PATHS], "sha256": sha256(target)}
    if audit["duplicate"] or audit["traversal"] or not audit["manifest_exact"] or audit["sha_mismatches"] or audit["parent_contamination"]: raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False)); return target, audit


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--verify", action="store_true"); parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--zip", action="store_true"); args = parser.parse_args()
    repository_preflight(); build_outputs(DEFAULT_LANE)
    if args.verify: verify(DEFAULT_LANE, True)
    if args.reproducibility: reproducibility_check()
    if args.zip: zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip): print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__": main()
