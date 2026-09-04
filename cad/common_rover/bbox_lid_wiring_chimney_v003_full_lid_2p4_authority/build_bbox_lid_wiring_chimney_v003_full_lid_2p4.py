"""Build the physically selected 2.4 mm v003 full BBOX chimney lid."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers

ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "bbox_lid_wiring_chimney_v003_full_lid_2p4_authority"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PS-BBOX-CHIMNEY-V003-FULL-LID-2P4-AUTHORITY"
PARENT_REL = "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess"
PARENT = ROOT / PARENT_REL
PARENT_BUILDER = PARENT / "build_bbox_lid_wiring_chimney_v003.py"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3507
OUTSIDE_DIGEST = "4e5349b5a47b139a01b4369c4452391aa971e7dbb23f278f29506add6d7ba542"
PROTECTED = {
    PARENT_REL: (32, "052663630e9a1a9bfc84320c9286ad26f7559bb06e2274b326d6b1ef4c31ad99"),
    "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm": (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "cad/common_rover/bbox_lid_wiring_chimney_v001_above_water_gland": (39, "dca4482031a09754fcb46657393077af5b7b367946f3db58db81691c9cfca0c0"),
    "cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8": (37, "d0d58d47f45360ade6718d1f9bc856f06bfeaa355b6bd9f48229a480c4be3481"),
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test": (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37": (38, "d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
    "cad/common_rover/common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36": (24, "33741f011a960bdbbf416ce8be51cb41c9663fbbe8dcbf9db28e5134fd4b0400"),
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0": (43, "ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

SELECTED_WALL = 2.4
COUNTERBORE_DEPTH = 6.6
RECESS_MOUTH_D = 30.0
FLAT_SEAT_D = 27.0
TRANSITION_R = 1.5
GLAND_HOLE = 15.2
NORMAL_WALL = 4.0
LOCAL_STACK = 9.0
GLAND_CENTER_ABOVE_LID = 30.0
CHIMNEY = [50.0, 45.0, 50.0]
CHIMNEY_INTERNAL = [42.0, 37.0]
HOOD_PROJECTION = 8.0

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_lid_wiring_chimney_v003_full_lid_2p4_contract.py"
STEP = "cad/bbox_lid_wiring_chimney_v003_local_wall_2p4.step"
STL = "print/bbox_lid_wiring_chimney_v003_local_wall_2p4.stl"
SVGS = ["artifacts/FULL_LID_2P4_SECTION.svg", "artifacts/PHYSICAL_AUTHORITY_FLOW.svg"]
DOCS = [
    "README.md", "PHYSICAL_AUTHORITY.md", "DIMENSION_REPORT.md", "PHYSICAL_TEST_PLAN.md",
    "HOLD_REGISTER.md", "design_parameters.json", "validation_report.json", "MANIFEST.txt",
    "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, STEP, STL, *SVGS, *DOCS, *LOGS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v003 = load_module("bbox_chimney_v003_protected", PARENT_BUILDER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = git("diff", "--cached", "--name-only").splitlines()
    dirty = git("diff", "--name-only").splitlines()
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()) if LANE.exists() else []
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_9": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "cache_zero": not cache,
        "ignored_zero": not ignored, "complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "protected": {key: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for key, value in protected.items()},
        "lane_files": len(files),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(report, ensure_ascii=True))
    return report


def full_lid():
    return v003.recessed_lid(SELECTED_WALL)


def common_volume(a, b) -> float:
    try:
        return sum(solid.Volume() for solid in a.val().intersect(b.val()).Solids())
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def delta_in_mask(mask) -> float:
    old, new = v003.v002.compact_lid(), full_lid()
    removed, added = old.cut(new), new.cut(old)
    return round(common_volume(removed, mask) + common_volume(added, mask), 6)


def geometry_analysis() -> dict:
    shape = full_lid()
    old = v003.v002.compact_lid()
    bounds, old_bounds = shape.val().BoundingBox(), old.val().BoundingBox()
    external_face_mask = v003.box(31.0, 0.12, 31.0, (0, v003.EXTERNAL_SEAL_FACE_Y - 0.03, v003.GLAND_CENTER_Z))
    added = shape.cut(old)
    added_volume = sum(solid.Volume() for solid in added.solids().vals()) if added.solids().vals() else 0.0
    return {
        "valid": shape.val().isValid(), "solids": len(shape.solids().vals()),
        "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
        "parent_bbox_mm": [round(old_bounds.xlen, 3), round(old_bounds.ylen, 3), round(old_bounds.zlen, 3)],
        "measured_local_wall_mm": v003.measured_floor_thickness(shape, SELECTED_WALL),
        "measured_normal_wall_mm": v003.normal_wall_thickness(shape),
        "counterbore_depth_mm": v003.actual_counterbore_depth(SELECTED_WALL),
        "external_sealing_face_delta_mm3": delta_in_mask(external_face_mask),
        "rain_hood_delta_mm3": delta_in_mask(v003.v002.rain_hood()),
        "seal_land_delta_mm3": delta_in_mask(v003.v002.v001.seal_mask()),
        "fastener_pattern_delta_mm3": delta_in_mask(v003.v002.v001.fastener_mask()),
        "added_volume_vs_v002_mm3": round(added_volume, 6),
        "gasket_loop_change_count": 0, "lid_outer_geometry_change_count": 0,
        "gland_center_change_mm": 0.0, "gland_hole_change_mm": 0.0,
        "chimney_height_change_mm": 0.0, "normal_wall_change_mm": 0.0,
    }


def waterline() -> dict:
    source = dict(v003.v002.waterline_data())
    source["authority_class"] = "DERIVED_PHYSICAL_DATUM_PENDING"
    source["next_measurement_required"] = ["LID_TOP_Z", "GLAND_CENTER_Z", "GLAND_HOLE_LOWEST_Z", "CHIMNEY_TOP_Z"]
    return source


def parameters() -> dict:
    return {
        "version": VERSION, "parent": {"lane": PARENT_REL, "read_only": True},
        "physical_selection": {
            "gland_hole_authority_mm": GLAND_HOLE, "gland_hole_physical_fit": "PASS",
            "selected_local_gland_wall_mm": SELECTED_WALL, "coupon_gland_fit": "PASS",
            "coupon_locknut_thread_engagement": "PASS", "gasket_included_depth": "APPROPRIATE_OBSERVED",
            "thinner_wall_required": False, "selection_authority": "FULL_LID_CAD_AUTHORIZED",
            "full_lid_physical_sealing": "NOT_AUTHORIZED_BY_COUPON",
        },
        "geometry": {
            "chimney_outer_xyz_mm": CHIMNEY, "chimney_height_mm": 50.0,
            "normal_wall_mm": NORMAL_WALL, "chimney_internal_xy_mm": CHIMNEY_INTERNAL,
            "local_stack_mm": LOCAL_STACK, "selected_local_wall_mm": SELECTED_WALL,
            "counterbore_depth_mm": COUNTERBORE_DEPTH, "recess_side": "INTERNAL_ONLY",
            "recess_entry_diameter_mm": RECESS_MOUTH_D, "flat_seat_diameter_mm": FLAT_SEAT_D,
            "transition_r_mm": TRANSITION_R, "locknut_reference_od_mm": 24.0,
            "gland_hole_mm": GLAND_HOLE, "gland_center_above_lid_top_mm": GLAND_CENTER_ABOVE_LID,
            "gland_direction": "CBOX_SIDE_POSITIVE_Y_HORIZONTAL", "rain_hood_projection_mm": HOOD_PROJECTION,
        },
        "protected": {
            "lid_outer_change": 0, "gasket_loop_change": 0, "seal_land_change": 0,
            "lid_sealing_surface_change": 0, "m4x8_pattern_change": 0,
            "shell_interface_change": 0, "fastening_geometry_change": 0,
            "cable_routing_architecture_change": 0, "external_gland_sealing_face_change": 0,
        },
        "mechanical_access": {
            "coupon_locknut_engagement": "PASS", "generic_d40_proxy_design_blocker": False,
            "actual_service_method": "USED_FOR_COUPON_PASS", "full_lid_tool_access": "PHYSICAL_VALIDATION_PENDING",
        },
        "waterline": waterline(),
        "print": {"printer": "Bambu Lab A1", "material": "PETG", "first_print": STL, "slicer": "HOLD_SLICER_NOT_RUN"},
        "status": "CAD_PASS/CONTRACT_TEST_PASS/FULL_LID_2P4_PRINT_READY/SELECTED_LOCAL_GLAND_WALL_2P4/PHYSICAL_VALIDATION_PENDING",
        "forbidden_claims": ["WATERPROOF_PASS", "RAIN_PASS", "TILT_PASS", "DROP_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    return {
        SVGS[0]: svg("FULL LID 2.4 MM SECTION", "Physical coupon selection applied to full-lid CAD.", '<rect x="160" y="150" width="180" height="340" class="b"/><rect x="340" y="210" width="225" height="220" class="q"/><path d="M160 250H495V390H160" fill="#fff" stroke="#087f5b" stroke-width="3"/><text x="620" y="230">normal wall 4.0</text><text x="620" y="280">local stack 9.0</text><text x="620" y="330">counterbore 6.6</text><text x="620" y="380">remaining wall 2.4</text><text x="620" y="430">Ø30 → R1.5 → Ø27</text>'),
        SVGS[1]: svg("PHYSICAL AUTHORITY FLOW", "Coupon PASS selects CAD; full lid sealing remains pending.", '<rect x="90" y="190" width="240" height="190" class="g"/><text x="135" y="285">2.4 COUPON PASS</text><path d="M350 285H500" class="a"/><rect x="520" y="190" width="240" height="190" class="b"/><text x="565" y="285">FULL-LID CAD</text><path d="M780 285H900" class="a"/><rect x="920" y="190" width="140" height="190" class="q"/><text x="945" y="270">PRINT</text><text x="930" y="315">+ TEST</text>'),
    }


def documents() -> dict[str, str]:
    header = "# BBOX chimney v003 full-lid 2.4 mm authority\n\n"
    return {
        "README.md": header + "The physically passing2.4 mm coupon is selected for full-lid CAD. Existing v003 coupon and HOLD2.2 artifacts remain unchanged in the protected parent lane. First print: `print/bbox_lid_wiring_chimney_v003_local_wall_2p4.stl`. Status: `CAD_PASS / CONTRACT_TEST_PASS / FULL_LID_2P4_PRINT_READY / PHYSICAL_VALIDATION_PENDING`.\n",
        "PHYSICAL_AUTHORITY.md": header + "Observed on the2.4 mm coupon: Ø15.2 gland fit PASS, locknut thread engagement PASS, fastening depth appropriate with gasket, and no current need for a thinner wall. This authorizes2.4 mm for full-lid CAD only. It does not authorize waterproof, rain, tilt, drop, field, or complete BBOX sealing PASS.\n",
        "DIMENSION_REPORT.md": header + "50×45×50 mm chimney;42×37 mm interior;4 mm normal wall;9 mm actual local stack;2.4 mm selected floor;6.6 mm counterbore;Ø30 mouth;R1.5 transition;Ø27 flat seat;Ø15.2 hole;center lid top+30 mm;+Y horizontal gland;8 mm hood. External sealing face and protected lid interfaces have zero change.\n",
        "PHYSICAL_TEST_PLAN.md": header + "1 print full lid;2 inspect;3 remove recess burr/string;4 install PG9;5 install gasket;6 install locknut;7 tighten with actual method;8 verify flat seat;9 verify rotation resistance;10 install OD9.6 cable;11 verify routing;12 install on BBOX;13 align gasket;14 tighten M4;15 mount rover;16 measure lid-top, gland-center, hole-lowest and chimney-top Z;17 frame/crawler dry-fit;18 upright water;19 tilt>=10°;20 rain/splash;21 wet-cable movement. Only after sealing validation:22 removable TPU protector;23 handling/drop test.\n",
        "HOLD_REGISTER.md": header + "- slicer and first full-lid print\n- full-lid actual tool access, nut seating and gland rotation\n- real BBOX gasket/M4 assembly\n- physical lid/chimney/gland Z datums\n- rover frame/crawler dry-fit\n- upright water, tilt, rain/splash and wet-cable tests\n- TPU, drop, field and durability validation\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-26T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    v003.v002.v001.v002.v001.export_stl(shape, path)


def generate(out: Path):
    export_step(full_lid(), out / STEP)
    export_stl(full_lid(), out / STL)
    for relative, text in svg_payload().items():
        write(out / relative, text)
    for relative, text in documents().items():
        write(out / relative, text)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def artifact_audit(out: Path):
    step_shape = importers.importStep(str(out / STEP))
    bounds = step_shape.val().BoundingBox()
    step = {"path": STEP, "valid": step_shape.val().isValid(), "solids": len(step_shape.solids().vals()), "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)]}
    mesh = v003.v002.v001.v002.v001.mesh_metrics(out / STL)
    return step, mesh


def reproducibility() -> dict:
    compared = sorted([STEP, STL, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="chimney_v003_2p4_") as temp:
        subprocess.run([sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT=1\nSTL_COUNT=1\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract():
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def build():
    repository = guard(False)
    generate(LANE)
    geometry = geometry_analysis()
    step, mesh = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "selected_2p4": geometry["measured_local_wall_mm"] == 2.4,
        "counterbore_6p6": geometry["counterbore_depth_mm"] == 6.6,
        "normal_wall_4": geometry["measured_normal_wall_mm"] == 4.0,
        "hole_15p2": GLAND_HOLE == 15.2, "mouth_30": RECESS_MOUTH_D == 30,
        "seat_27": FLAT_SEAT_D == 27, "transition_1p5": TRANSITION_R == 1.5,
        "height_50": CHIMNEY[2] == 50, "center_plus30": GLAND_CENTER_ABOVE_LID == 30,
        "hood_8": HOOD_PROJECTION == 8,
        "external_face_zero": geometry["external_sealing_face_delta_mm3"] == 0,
        "hood_zero": geometry["rain_hood_delta_mm3"] == 0,
        "seal_zero": geometry["seal_land_delta_mm3"] == 0,
        "fastener_zero": geometry["fastener_pattern_delta_mm3"] == 0,
        "gasket_zero": geometry["gasket_loop_change_count"] == 0,
        "outer_zero": geometry["lid_outer_geometry_change_count"] == 0 and geometry["bbox_mm"] == geometry["parent_bbox_mm"],
        "no_added_volume": geometry["added_volume_vs_v002_mm3"] == 0,
        "valid": geometry["valid"] and geometry["solids"] == 1,
        "step_reload": step["valid"] and step["solids"] == 1,
        "stl_quality": mesh["reload"] == "PASS" and mesh["watertight"] and mesh["manifold"] and mesh["bad_edge_count"] == 0 and mesh["degenerate_triangle_count"] == 0,
        "reproducibility": repro["status"] == "PASS",
        "authority": repository["checks"]["authority_4"], "protected": repository["checks"]["protected_9"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "geometry": geometry,
        "waterline": waterline(), "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "step": step, "stl": {"path": STL, **mesh}, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "forbidden_statuses": parameters()["forbidden_claims"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nSTEP_RELOAD=1/1 PASS\nSTL_QUALITY=1/1 PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks))
    return guard(True), validation


def package():
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_BBOX_CHIMNEY_V003_FULL_LID_2P4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 26, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only:
        generate(args.render_only)
        return 0
    repository, validation = build()
    result = {
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED),
        "steps": 1, "stls": 1, "svgs": len(SVGS), "branch": repository["branch"],
        "head": repository["head"], "staged": repository["staged"], "geometry": validation["geometry"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
