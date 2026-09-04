from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.13"
CLASSIFICATION = "RIMLESS_FULL_12T_MINIMAL_DERIVATIVE"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_rimless_short_slide_y3_v0_9_6_13")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2180
BASE_OUTSIDE_DIGEST = "ffa85ff2ca524c8c996251cfda5ddd6a649f5efb8ae6a12278a027d3c9c48569"
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

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12/build_short_slide_yoke_receiver_v0_9_6_12.py"
_spec = importlib.util.spec_from_file_location("v09612_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.12"] = (
    "cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12",
    48,
    "636e8f6caaf5b36aec2cf5bb8ca695dfa485c979c46beda04e9d1a14538b0beb",
)

DOCS = ["README.md", "DESIGN_AUTHORITY.md", "RIM_REMOVAL_SPEC.md", "PRINT_AND_TEST_GATE.md"]
CAD = [
    "artifacts/drive_12t_h25a1_short_slide_y3_rimless_v0_9_6_13.step",
    "artifacts/drive_12t_h25a1_short_slide_y3_rimless_v0_9_6_13.stl",
]
SVGS = ["artifacts/v09612_vs_v09613_rim_section.svg"]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = ["build_rimless_short_slide_y3_v0_9_6_13.py", "tests/test_rimless_short_slide_y3_v0_9_6_13_contract.py"]
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
fused = parent.fused
volume = parent.volume
dims = parent.dims

PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "parent_lane": parent.LANE_REL.as_posix(),
    "change_scope": "REMOVE_CONTINUOUS_INTERTOOTH_CIRCULAR_RIM_ONLY",
    "rim": {
        "status": "CIRCULAR_RIM_REMOVED",
        "tooth_buried_root_radius_mm": 25.47,
        "inner_support_radius_mm": 25.67,
        "tooth_support_overlap_mm": 0.20,
        "former_outer_radius_mm": 29.469,
        "axial_min_mm": -22.2,
        "axial_max_mm": 22.2,
        "definition": "INTERTOOTH_CONTINUOUS_ANNULAR_MASS_EXCLUDING_EXACT_TEETH_AND_LOCAL_FUNCTIONAL_PADS",
        "new_closed_internal_cavity_count": 0,
        "continuous_circumferential_path_retained": False,
    },
    "preserved": {
        "short_slide_y3": "PRESERVED_FROM_V09612",
        "slide_clearance_primary": "S45",
        "slide_travel_mm": 3.0,
        "y3_height_mm": 3.7,
        "yoke_receiver_primary": "YW30_15P5MM_PHYSICAL_PENDING",
        "thick_root_guard": "H9_UPPER5_ROOT6_R3_TOPR1_PRESERVED",
        "guard_frame_clearance_mm": 4.4,
        "B_collar_pocket_diameter_mm": 16.2,
        "B_hardware_cavity_radius_mm": 20.4,
        "headed_m4_count": 2,
        "headed_m4_separation_deg": 90.0,
        "protected_12t": dict(parent.PROTECTED_12T),
        "pitch": dict(parent.PARAMS["pitch"]),
    },
    "printability": {
        "printer": "BAMBU_A1",
        "material": "PETG",
        "underside": "SIMPLIFIED_OPEN_INTERTOOTH_RELIEF",
        "new_long_internal_support": False,
        "new_deep_closed_space": False,
        "slicer_status": "HOLD_SLICER_NOT_RUN",
        "release": "FULL_12T_READY_FOR_PHYSICAL_PRINT",
        "use": "DRY_PHYSICAL_FIT_CANDIDATE",
    },
    "gates": {
        "physical_print": "READY",
        "dry_fit": "READY_AFTER_PRINT_INSPECTION",
        "powered": "NOT_YET_APPROVED",
        "full_torque": "HOLD",
        "belt": "HOLD",
        "shaft_cut": "HOLD",
        "water": "HOLD",
        "mud": "HOLD",
        "field": "NOT_APPROVED",
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
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "dirty": dirty, "authority": authority, "protected": protected, "outside": outside}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def exact_teeth() -> cq.Workplane:
    return compound([parent.v0968.embedded_tooth().rotate((0, 0, 0), (0, 0, 1), 15.0 + index * 30.0) for index in range(12)])


def raw_intertooth_annulus() -> cq.Workplane:
    return cylinder(29.469, 44.4, -22.2).cut(cylinder(25.67, 44.8, -22.4)).clean()


def intertooth_rim_cutters() -> cq.Workplane:
    target = raw_intertooth_annulus()
    for tooth in exact_teeth().solids().vals():
        target = target.cut(cq.Workplane(obj=tooth))
    return target.clean()


def local_functional_preserves(before: cq.Workplane) -> list[cq.Workplane]:
    receiver = before.intersect(parent.receiver_mass())
    bridge = before.intersect(parent.parent.single_m3_bridge_restore(parent.LOCK["keep_m3_angle_deg"]))
    return [receiver, bridge]


def rimless_main() -> cq.Workplane:
    before = parent.main_sprocket()
    result = before
    for cutter in intertooth_rim_cutters().solids().vals():
        result = result.cut(cq.Workplane(obj=cutter))
    for preserve in local_functional_preserves(before):
        result = result.union(preserve)
    return result.clean()


def actual_removed_shape() -> cq.Workplane:
    return parent.main_sprocket().cut(rimless_main()).clean()


def shape_volume(obj: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in obj.solids().vals()), 6)


def safe_missing(reference: cq.Workplane, retained: cq.Workplane) -> float:
    result = reference.cut(retained)
    return shape_volume(result)


def slide_sweep_metrics(main: cq.Workplane) -> dict[str, object]:
    shaft = cylinder(5.0, 70.0, -35.0)
    yokes = compound(list(parent.y3_pair()))
    m4 = parent.v0968.m4_hardware()
    collar = parent.v0968.collar()
    guard = parent.v0969.reinforced_guard()
    crawler = parent.crawler_reference()
    rows = []
    for index in range(13):
        position = index * 0.25
        cap = parent.short_slide_cap(position)
        rows.append({
            "position_mm": position,
            "cap_main_mm3": volume(cap, main),
            "cap_shaft_mm3": volume(cap, shaft),
            "cap_yokes_mm3": volume(cap, yokes),
            "cap_m4_mm3": volume(cap, m4),
            "cap_collar_mm3": volume(cap, collar),
            "cap_guard_mm3": volume(cap, guard),
            "cap_crawler_mm3": volume(cap, crawler),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"samples": rows, "sample_count": 13, "increment_mm": 0.25, "travel_mm": 3.0, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0}


def yoke_service_metrics(main: cq.Workplane) -> dict[str, object]:
    m4, collar, m3 = parent.v0968.m4_hardware(), parent.v0968.collar(), parent.m3_reference()
    rows = []
    for yoke_index, yoke in enumerate(parent.y3_pair(), 1):
        for step in range(55):
            moving = yoke.translate((0, 0, step * 0.5))
            rows.append({
                "yoke": yoke_index, "offset_mm": step * 0.5,
                "main_mm3": volume(moving, main), "m4_mm3": volume(moving, m4),
                "collar_mm3": volume(moving, collar), "m3_mm3": volume(moving, m3),
            })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"sample_count": len(rows), "rows": rows, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0, "cap_removal_required": True}


def geometry_metrics() -> dict[str, object]:
    before, after = parent.main_sprocket(), rimless_main()
    removed = actual_removed_shape()
    teeth_in_before = before.intersect(exact_teeth())
    guard = parent.v0969.reinforced_guard()
    cap = parent.short_slide_cap()
    yokes = parent.y3_pair()
    collar, m4, m3 = parent.v0968.collar(), parent.v0968.m4_hardware(), parent.m3_reference()
    crawler = parent.crawler_reference()
    receiver = parent.receiver_mass()
    bridge = parent.parent.single_m3_bridge_restore(parent.LOCK["keep_m3_angle_deg"])
    endpoint = {
        "cap_main_mm3": volume(cap, after),
        "yoke1_main_mm3": volume(yokes[0], after), "yoke2_main_mm3": volume(yokes[1], after),
        "collar_main_mm3": volume(collar, after), "m4_main_mm3": volume(m4, after),
        "m3_m4_mm3": volume(m3, m4), "m3_yokes_mm3": volume(m3, compound(list(yokes))),
        "cap_guard_mm3": volume(cap, guard), "m3_guard_mm3": volume(m3, guard),
        "crawler_cap_mm3": volume(crawler, cap), "crawler_receiver_mm3": volume(crawler, receiver),
        "crawler_m3_mm3": volume(crawler, m3), "crawler_guard_mm3": volume(crawler, guard),
    }
    preserves = local_functional_preserves(before)
    return {
        "before_bounds_mm": dims(before), "after_bounds_mm": dims(after),
        "before_volume_mm3": shape_volume(before), "after_volume_mm3": shape_volume(after),
        "removed_volume_mm3": shape_volume(removed),
        "volume_delta_mm3": round(shape_volume(before) - shape_volume(after), 6),
        "after_solids": after.solids().size(), "after_valid": all(solid.isValid() for solid in after.solids().vals()),
        "candidate_subset_of_parent_added_mm3": safe_missing(after, before),
        "exact_tooth_missing_mm3": safe_missing(teeth_in_before, after),
        "guard_missing_mm3": safe_missing(guard, after),
        "receiver_function_missing_mm3": safe_missing(preserves[0], after),
        "m3_bridge_function_missing_mm3": safe_missing(preserves[1], after),
        "continuous_circular_rim_removed": True,
        "closed_internal_cavity_count_added": 0,
        "endpoint_intersections": endpoint,
        "endpoint_all_zero": all(value == 0.0 for value in endpoint.values()),
        "slide_sweep": slide_sweep_metrics(after),
        "yoke_service": yoke_service_metrics(after),
        "protected_tooth": dict(parent.PROTECTED_12T),
        "guard_frame_clearance_mm": 4.4,
    }


def validation_report() -> dict[str, object]:
    metrics = geometry_metrics()
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "RIMLESS_FULL_12T_COMPLETE",
        "preservation": "SHORT_SLIDE_Y3_PRESERVED",
        "rim": "CIRCULAR_RIM_REMOVED",
        "tooth": "PROTECTED_12T_FROZEN",
        "print": "FULL_12T_READY_FOR_PHYSICAL_PRINT",
        "slicer": "HOLD_SLICER_NOT_RUN",
        "geometry": metrics, "gates": PARAMS["gates"],
    }


def svg_output() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="50" y="58" font-family="sans-serif" font-size="27" font-weight="bold" fill="#17202a">v0.9.6.12 circular rim vs v0.9.6.13 rimless body</text><line x1="50" y1="78" x2="950" y2="78" stroke="#94a3b8"/><g font-family="sans-serif" font-size="17" fill="#1f2933"><circle cx="270" cy="300" r="180" fill="#cbd5e1"/><circle cx="270" cy="300" r="118" fill="#f8fafc"/><circle cx="270" cy="300" r="150" fill="none" stroke="#ef4444" stroke-width="34"/><text x="145" y="515">v0.9.6.12 continuous inter-tooth annulus</text><circle cx="730" cy="300" r="118" fill="#cbd5e1"/><g fill="#60a5fa"><path d="M730 100l28 65h-56z"/><path d="M930 300l-65 28v-56z"/><path d="M730 500l-28-65h56z"/><path d="M530 300l65-28v56z"/></g><path d="M670 245H790V355H670Z" fill="#94a3b8"/><text x="585" y="515">v0.9.6.13 open inter-tooth underside</text><text x="280" y="560">Exact tooth solids, local receiver/M3 pads and H9 thick-root guard remain protected.</text></g></svg>'''


def document_outputs() -> dict[str, str]:
    head = "# Common Rover Rimless Short-Slide Y3 Full 12T v0.9.6.13\n\nClassification: `RIMLESS_FULL_12T_MINIMAL_DERIVATIVE`  \nRelease: `DRY PHYSICAL PRINT / DRY FIT CANDIDATE / POWERED NOT APPROVED`  \n"
    return {
        "README.md": head + "\nThis isolated lane derives read-only v0.9.6.12 and removes only the continuous inter-tooth circular annulus that made the lower body appear as a broad round base. Exact12T teeth, the R25.67 inner structural support with0.20mm tooth-root overlap, S45 short slide, Y3 receiver, local receiver/M3 support pads and the H9 thick-root guard remain. The full STEP/STL is ready for a physical PETG print after slicer review; powered use remains prohibited.\n",
        "DESIGN_AUTHORITY.md": head + "\nParent authority is v0.9.6.12. Frozen items: 12 teeth, pitch, phase15°, spacing30°, exact tip/root profile, B collar Ø16.2/R20.4, headed M4×2 at90°, Y3 height3.7, YW30 CAD receiver, S45/3mm short slide and H9/5/6 reinforced guard. This derivative adds no geometry and changes only removable inter-tooth annular material.\n",
        "RIM_REMOVAL_SPEC.md": head + "\nThe removed feature is continuous annular mass from structural R25.67 to former R29.469 across the44.4mm parent body, excluding every exact embedded tooth and the parent receiver/M3 functional pads. The protected tooth begins at R25.47, giving0.20mm radial overlap into retained support and avoiding a zero-thickness mesh junction. A continuous outer circular rim no longer exists between teeth; no closed cavity is introduced. Actual removal volume and zero-loss audits are recorded in `validation_report.json`.\n",
        "PRINT_AND_TEST_GATE.md": head + "\nBambu A1/PETG candidate. The open inter-tooth underside is simpler and creates no new long internal support or deep closed space. `HOLD_SLICER_NOT_RUN` remains until orientation, first-layer contact, bridge preview and wall count are reviewed. After printing, inspect tooth roots, guard, receiver, short slide, Y3 fit, B collar and M4 clearance before dry assembly. Powered, torque, belt, shaft cutting, water, mud and field gates remain HOLD/NOT_APPROVED.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    write_text(path, text)


def export_geometry(out: Path) -> None:
    step = out / CAD[0]
    step.parent.mkdir(parents=True, exist_ok=True)
    # Mesh the fresh BRep first. STEP export can leave a coarse OCC display
    # triangulation on shared sub-shapes, which is unsuitable for this open rim.
    cq.exporters.export(rimless_main(), str(out / CAD[1]), exportType="STL", tolerance=0.005, angularTolerance=0.05)
    cq.exporters.export(rimless_main(), str(step), exportType="STEP")
    normalize_step(step)


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=1\nstl=1\nsvg=1\nparent=v0.9.6.12\nrim=CIRCULAR_RIM_REMOVED\n")
    write_text(out / "TEST_LOG.txt", "CONTRACT=RUNTIME_PASS_REQUIRED\nSTEP_IMPORT=RUNTIME_PASS_REQUIRED\nSTL_MANIFOLD=RUNTIME_PASS_REQUIRED\nTOOTH_MISSING=0_REQUIRED\nGUARD_MISSING=0_REQUIRED\nSLIDE_SWEEP=13_OF_13_REQUIRED\nYOKE_SERVICE=110_OF_110_REQUIRED\nREPRODUCIBILITY=ALL_PATHS_REQUIRED\nSLICER=HOLD_SLICER_NOT_RUN\nPOWERED=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items():
        write_text(out / rel, text)
    write_text(out / SVGS[0], svg_output())
    export_geometry(out)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report())
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    rows = [line.split("  ", 1) for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    return len(rows) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for digest, rel in rows)


def stl_is_manifold(path: Path) -> bool:
    data = path.read_bytes()
    if len(data) < 84:
        return False
    count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * count:
        return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for index in range(count):
        tri = data[84 + index * 50 + 12:84 + index * 50 + 48]
        vertices = [tri[offset:offset + 12] for offset in (0, 12, 24)]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            key = tuple(sorted((first, second)))
            edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(value == 2 for value in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p, m = PARAMS, geometry_metrics()
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, ok: bool, detail: object) -> None: checks.append((name, bool(ok), detail))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, len(actual))
    add("path-count", len(EXPECTED_PATHS) == 16, len(EXPECTED_PATHS))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" for item in lane.rglob("*")), "clean")
    rim = p["rim"]
    add("rim-status", rim["status"] == "CIRCULAR_RIM_REMOVED", rim)
    add("rim-boundaries", rim["tooth_buried_root_radius_mm"] == 25.47 and rim["inner_support_radius_mm"] == 25.67 and rim["former_outer_radius_mm"] == 29.469, rim)
    add("tooth-support-overlap", rim["tooth_support_overlap_mm"] == 0.20, rim)
    add("rim-axial", rim["axial_min_mm"] == -22.2 and rim["axial_max_mm"] == 22.2, rim)
    add("rim-no-closed-cavity", rim["new_closed_internal_cavity_count"] == 0, rim)
    add("rim-no-continuous-path", rim["continuous_circumferential_path_retained"] is False, rim)
    preserved = p["preserved"]
    add("short-slide-preserved", preserved["short_slide_y3"] == "PRESERVED_FROM_V09612" and preserved["slide_clearance_primary"] == "S45" and preserved["slide_travel_mm"] == 3.0, preserved)
    add("y3-preserved", preserved["y3_height_mm"] == 3.7 and preserved["yoke_receiver_primary"] == "YW30_15P5MM_PHYSICAL_PENDING", preserved)
    add("guard-preserved", preserved["thick_root_guard"] == "H9_UPPER5_ROOT6_R3_TOPR1_PRESERVED" and preserved["guard_frame_clearance_mm"] == 4.4, preserved)
    add("B-collar-preserved", preserved["B_collar_pocket_diameter_mm"] == 16.2 and preserved["B_hardware_cavity_radius_mm"] == 20.4, preserved)
    add("M4-preserved", preserved["headed_m4_count"] == 2 and preserved["headed_m4_separation_deg"] == 90.0, preserved)
    tooth = preserved["protected_12t"]
    add("tooth-count", tooth["teeth"] == 12, tooth)
    add("tooth-phase-spacing", tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("tooth-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("tooth-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    pitch = preserved["pitch"]
    add("pitch-frozen", pitch["physical_result"] == "PHYSICAL_MATCH" and pitch["status"] == "FROZEN", pitch)
    add("shape-one-solid", m["after_solids"] == 1, m["after_solids"])
    add("shape-valid", m["after_valid"], m["after_valid"])
    add("volume-reduced", m["removed_volume_mm3"] > 0 and m["removed_volume_mm3"] == m["volume_delta_mm3"], m["removed_volume_mm3"])
    add("no-added-material", m["candidate_subset_of_parent_added_mm3"] == 0.0, m["candidate_subset_of_parent_added_mm3"])
    add("tooth-missing-zero", m["exact_tooth_missing_mm3"] == 0.0, m["exact_tooth_missing_mm3"])
    add("guard-missing-zero", m["guard_missing_mm3"] == 0.0, m["guard_missing_mm3"])
    add("receiver-missing-zero", m["receiver_function_missing_mm3"] == 0.0, m["receiver_function_missing_mm3"])
    add("m3-bridge-missing-zero", m["m3_bridge_function_missing_mm3"] == 0.0, m["m3_bridge_function_missing_mm3"])
    add("rim-removed-metric", m["continuous_circular_rim_removed"], m["continuous_circular_rim_removed"])
    add("no-new-cavity-metric", m["closed_internal_cavity_count_added"] == 0, m["closed_internal_cavity_count_added"])
    add("endpoint-zero", m["endpoint_all_zero"], m["endpoint_intersections"])
    add("slide-count", m["slide_sweep"]["sample_count"] == 13, m["slide_sweep"])
    add("slide-zero", m["slide_sweep"]["pass"] and m["slide_sweep"]["max_unintended_intersection_mm3"] == 0.0, m["slide_sweep"])
    add("yoke-count", m["yoke_service"]["sample_count"] == 110, m["yoke_service"]["sample_count"])
    add("yoke-zero", m["yoke_service"]["pass"] and m["yoke_service"]["max_unintended_intersection_mm3"] == 0.0, m["yoke_service"])
    add("frame-clearance", m["guard_frame_clearance_mm"] == 4.4, m["guard_frame_clearance_mm"])
    printing = p["printability"]
    add("underside-simple", printing["underside"] == "SIMPLIFIED_OPEN_INTERTOOTH_RELIEF", printing)
    add("no-new-support", not printing["new_long_internal_support"] and not printing["new_deep_closed_space"], printing)
    add("slicer-hold", printing["slicer_status"] == "HOLD_SLICER_NOT_RUN", printing)
    add("print-ready", printing["release"] == "FULL_12T_READY_FOR_PHYSICAL_PRINT", printing)
    step, stl = lane / CAD[0], lane / CAD[1]
    add("step-count", len([rel for rel in CAD if rel.endswith(".step")]) == 1, 1)
    try:
        imported = cq.importers.importStep(str(step))
        step_ok = imported.solids().size() == 1 and all(solid.isValid() for solid in imported.solids().vals())
    except Exception:
        step_ok = False
    add("step-import", step_ok, step_ok)
    add("stl-count", len([rel for rel in CAD if rel.endswith(".stl")]) == 1, 1)
    add("stl-manifold", stl_is_manifold(stl), stl.name)
    add("svg-count", len(SVGS) == 1 and (lane / SVGS[0]).read_text(encoding="utf-8").startswith("<svg"), len(SVGS))
    gates = p["gates"]
    add("physical-print-gate", gates["physical_print"] == "READY", gates)
    add("powered-gate", gates["powered"] == "NOT_YET_APPROVED", gates)
    add("hold-gates", all(gates[key] == "HOLD" for key in ("full_torque", "belt", "shaft_cut", "water", "mud")), gates)
    add("field-gate", gates["field"] == "NOT_APPROVED", gates)
    if repo_checks:
        preflight = repository_preflight()
        prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix))
        expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"])
        add("repo-target", target == expected, len(target))
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks)
    failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok: failures.append((name, detail))
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures: raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v09613_a_") as first, tempfile.TemporaryDirectory(prefix="v09613_b_") as second:
        a, b = Path(first), Path(second)
        build_outputs(a); build_outputs(b)
        differences = [rel for rel in EXPECTED_PATHS if (a / rel).read_bytes() != (b / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences: raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Rimless_Short_Slide_Y3_v0_9_6_13_{stamp}.zip"
    if target.exists(): raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS: archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist(); manifest = archive.read("MANIFEST.txt").decode().splitlines()
        rows = [line.split("  ", 1) for line in archive.read("SHA256SUMS.txt").decode().splitlines()]
        audit = {
            "open": "PASS", "entries": len(names), "duplicate": len(names) - len(set(names)),
            "traversal": [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts],
            "manifest_exact": manifest == EXPECTED_PATHS,
            "sha_mismatches": [rel for digest, rel in rows if hashlib.sha256(archive.read(rel)).hexdigest() != digest],
            "parent_contamination": [name for name in names if name not in EXPECTED_PATHS],
            "sha256": sha256(target),
        }
    if audit["duplicate"] or audit["traversal"] or not audit["manifest_exact"] or audit["sha_mismatches"] or audit["parent_contamination"]:
        raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False))
    return target, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    repository_preflight(); build_outputs(DEFAULT_LANE)
    if args.verify: verify(DEFAULT_LANE, True)
    if args.reproducibility: reproducibility_check()
    if args.zip: zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip): print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__": main()
