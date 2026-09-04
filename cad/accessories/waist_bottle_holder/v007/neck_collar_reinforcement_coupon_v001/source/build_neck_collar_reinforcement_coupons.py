"""Build BH_V007 neck-collar reinforcement coupons N-A, N-B and N-C.

The V007 production lane is imported read-only.  Only this coupon-study lane is
written.  The proven V007 16 x 4 x 30 mm long-tab B-rep is reused verbatim.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import cadquery as cq

sys.dont_write_bytecode = True


LANE = Path(__file__).resolve().parents[1]
V007_ROOT = LANE.parent
REPO_ROOT = V007_ROOT.parents[3]
V007_SOURCE = V007_ROOT / "source" / "build_bh_v007.py"
PARAM_PATH = LANE / "parameters.json"
STEP_DIR = LANE / "step"
STL_DIR = LANE / "stl"
VALIDATION_DIR = LANE / "validation"
REPORT_PATH = LANE / "validation_report.json"
MANIFEST_PATH = VALIDATION_DIR / "artifact_manifest.json"

COMPARISON_STEP_NAME = "BH_V007_neck_collar_reinforcement_comparison_NA_NB_NC"
PREVIEW_STL_NAME = "BH_V007_neck_collar_reinforcement_3up_print_preview"
FILE_STEMS = {
    "N-A": "BH_V007_NA_neck_collar_coupon_ID26p2_G18_T4p0_H9_PETG",
    "N-B": "BH_V007_NB_neck_collar_coupon_ID26p2_G20_T4p0_H9_PETG",
    "N-C": "BH_V007_NC_neck_collar_coupon_ID26p2_G20_T3p5_H9_PETG",
}


def import_v007():
    spec = importlib.util.spec_from_file_location("bh_v007_reference", V007_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import V007 source: {V007_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V007 = import_v007()
BASE = V007.BASE
P: dict[str, Any] = json.loads(PARAM_PATH.read_text(encoding="utf-8"))


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.rstrip("\n")


def current_git_state() -> dict[str, Any]:
    tracked = run_git("status", "--short", "--untracked-files=no")
    return {
        "branch": run_git("branch", "--show-current"),
        "head": run_git("rev-parse", "HEAD"),
        "tracked_status": tracked.splitlines() if tracked else [],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def check(condition: bool, detail: str) -> dict[str, str]:
    return {"status": "PASS" if condition else "FAIL", "detail": detail}


def make_c_ring(opening: float, thickness: float, height: float) -> cq.Workplane:
    inner_radius = P["fixed_authority"]["neck_id"] / 2.0
    outer_radius = inner_radius + thickness
    ring = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
    )
    gap = (
        cq.Workplane("XY")
        .box(opening, 2.0 * outer_radius + 4.0, height + 2.0, centered=(True, False, False))
        .translate((0.0, 0.0, -1.0))
    )
    ring = ring.cut(gap)
    # The straight section between the two tangent blends retains the exact clear gap.
    ring = BASE.safe_fillet(ring, "|Z", P["reinforcement"]["opening_tip_radius"])
    return ring.clean()


def make_gusset_rail(x_center: float) -> cq.Workplane:
    r = P["reinforcement"]
    y_len = r["gusset_y_max"] - r["gusset_y_min"]
    z_len = r["gusset_z_max"] - r["gusset_z_min"]
    y_center = (r["gusset_y_min"] + r["gusset_y_max"]) / 2.0
    z_center = (r["gusset_z_min"] + r["gusset_z_max"]) / 2.0
    rail = (
        cq.Workplane("YZ")
        .center(y_center, z_center)
        .rect(y_len, z_len)
        .extrude(r["gusset_thickness"])
        .translate((x_center - r["gusset_thickness"] / 2.0, 0.0, 0.0))
    )
    return BASE.safe_fillet(rail, "|X", r["gusset_end_radius"]).clean()


def make_root_system(height: float) -> tuple[cq.Workplane, dict[str, Any]]:
    r = P["reinforcement"]
    saddle = BASE.rounded_rect_prism(
        r["root_saddle_width"],
        r["root_saddle_depth"],
        r["root_saddle_plan_radius"],
        height,
    ).translate((0.0, r["root_saddle_center_y"], 0.0))

    bridge_depth = r["bridge_y_max"] - r["bridge_y_min"]
    bridge_height = r["bridge_z_max"] - r["bridge_z_min"]
    bridge = (
        cq.Workplane("XY")
        .box(
            r["bridge_width"],
            bridge_depth,
            bridge_height,
            centered=(True, True, False),
        )
        .translate(
            (
                0.0,
                (r["bridge_y_min"] + r["bridge_y_max"]) / 2.0,
                r["bridge_z_min"],
            )
        )
    )
    gussets = [make_gusset_rail(x) for x in r["gusset_x_centers"]]
    root = saddle.union(bridge)
    for gusset in gussets:
        root = root.union(gusset)

    # Preserve the full phi26.2 neck bore even where the broad saddle wraps the ring.
    neck_id = P["fixed_authority"]["neck_id"]
    id_cutter = (
        cq.Workplane("XY")
        .circle(neck_id / 2.0)
        .extrude(30.0)
        .translate((0.0, 0.0, -10.0))
    )
    root = root.cut(id_cutter).clean()
    return root, {"saddle": saddle, "bridge": bridge, "gussets": gussets}


def make_candidate(candidate_id: str) -> tuple[cq.Workplane, dict[str, Any]]:
    cp = P["candidates"][candidate_id]
    ring = make_c_ring(
        cp["construction_gap_before_tip_blend"],
        cp["radial_ring_thickness"],
        cp["collar_height"],
    )
    root, root_parts = make_root_system(cp["collar_height"])
    tab, tab_parts = V007.make_long_tab()
    collar = ring.union(root).union(tab).clean()
    return collar, {
        "ring": ring,
        "root": root,
        "root_parts": root_parts,
        "tab": tab,
        "tab_parts": tab_parts,
    }


def first_material_x(shape: cq.Workplane, y: float, z: float, x_max: float) -> float:
    solid = shape.val()
    step = 0.05
    low = 0.0
    high = step
    while high <= x_max:
        if solid.isInside(cq.Vector(high, y, z), 1.0e-7):
            break
        low = high
        high += step
    else:
        raise RuntimeError(f"No ring material found at y={y:.3f}, z={z:.3f}")
    for _ in range(30):
        mid = (low + high) / 2.0
        if solid.isInside(cq.Vector(mid, y, z), 1.0e-7):
            high = mid
        else:
            low = mid
    return high


def measure_finished_opening(
    ring: cq.Workplane, opening_hint: float, thickness: float, height: float
) -> dict[str, Any]:
    ri = P["fixed_authority"]["neck_id"] / 2.0
    ro = ri + thickness
    inner_y = math.sqrt(max(0.0, ri * ri - (opening_hint / 2.0) ** 2))
    outer_y = math.sqrt(max(0.0, ro * ro - (opening_hint / 2.0) ** 2))
    mid_y = (inner_y + outer_y) / 2.0
    sample_y = [mid_y - 0.25, mid_y, mid_y + 0.25]
    gaps = [
        2.0 * first_material_x(ring, y, height / 2.0, ro + 1.0) for y in sample_y
    ]
    return {
        "minimum_clear_gap_mm": round(min(gaps), 4),
        "sample_gaps_mm": [round(value, 4) for value in gaps],
        "sample_y_mm": [round(value, 4) for value in sample_y],
        "method": "B-rep point-in-solid boundary search at three finished mid-height tip stations",
    }


def cross_section_area_y(shape: cq.Workplane, y: float, slice_thickness: float = 0.08) -> float:
    cutter = (
        cq.Workplane("XY")
        .box(100.0, slice_thickness, 100.0, centered=(True, True, True))
        .translate((0.0, y, 0.0))
    )
    return shape.intersect(cutter).val().Volume() / slice_thickness


def minimum_throat_section(shape: cq.Workplane) -> dict[str, Any]:
    stations = [-37.0, -35.0, -33.0, -31.0, -29.0]
    samples = [cross_section_area_y(shape, y) for y in stations]
    return {
        "minimum_area_mm2": round(min(samples), 3),
        "station_y_mm": stations[samples.index(min(samples))],
        "samples_mm2": [round(value, 3) for value in samples],
        "method": "0.08 mm transverse B-rep slice across the constant root-throat span",
    }


def bbox_dict(shape: cq.Shape | cq.Workplane) -> dict[str, float]:
    return BASE.bbox_dict(shape)


def duplicate_signatures(shape: cq.Shape | cq.Workplane) -> list[tuple[float, ...]]:
    obj = shape.val() if isinstance(shape, cq.Workplane) else shape
    signatures: list[tuple[float, ...]] = []
    for solid in obj.Solids():
        bbox = solid.BoundingBox()
        center = solid.Center()
        signatures.append(
            tuple(
                round(value, 3)
                for value in (
                    solid.Volume(), bbox.xlen, bbox.ylen, bbox.zlen,
                    center.x, center.y, center.z,
                )
            )
        )
    return [signature for signature, count in Counter(signatures).items() if count > 1]


def binary_stl_metrics(path: Path) -> dict[str, Any]:
    """Inspect an OpenCascade binary STL without trimesh/runtime DLL dependencies."""
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError(f"STL is too short: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if len(data) != expected_size:
        raise RuntimeError(
            f"Unexpected binary STL size for {path.name}: {len(data)} != {expected_size}"
        )
    edges: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    signed_volume = 0.0
    bounds_min = [float("inf"), float("inf"), float("inf")]
    bounds_max = [float("-inf"), float("-inf"), float("-inf")]
    scale = 100000
    offset = 84
    for _ in range(triangle_count):
        values = struct.unpack_from("<12fH", data, offset)
        vertices = [values[3:6], values[6:9], values[9:12]]
        for vertex in vertices:
            for axis in range(3):
                bounds_min[axis] = min(bounds_min[axis], vertex[axis])
                bounds_max[axis] = max(bounds_max[axis], vertex[axis])
        quantized = [tuple(round(component * scale) for component in vertex) for vertex in vertices]
        for index in range(3):
            a = quantized[index]
            b = quantized[(index + 1) % 3]
            edges[tuple(sorted((a, b)))] += 1
        a, b, c = vertices
        cross_x = b[1] * c[2] - b[2] * c[1]
        cross_y = b[2] * c[0] - b[0] * c[2]
        cross_z = b[0] * c[1] - b[1] * c[0]
        signed_volume += (a[0] * cross_x + a[1] * cross_y + a[2] * cross_z) / 6.0
        offset += 50
    boundary_edges = sum(1 for count in edges.values() if count == 1)
    non_manifold_edges = sum(1 for count in edges.values() if count > 2)
    return {
        "triangle_count": triangle_count,
        "watertight": boundary_edges == 0 and non_manifold_edges == 0,
        "boundary_edges": boundary_edges,
        "non_manifold_edges": non_manifold_edges,
        "signed_volume_mm3": round(signed_volume, 3),
        "negative_volume": signed_volume < 0.0,
        "mesh_bbox_mm": {
            "xmin": round(bounds_min[0], 4), "xmax": round(bounds_max[0], 4),
            "ymin": round(bounds_min[1], 4), "ymax": round(bounds_max[1], 4),
            "zmin": round(bounds_min[2], 4), "zmax": round(bounds_max[2], 4),
            "xlen": round(bounds_max[0] - bounds_min[0], 4),
            "ylen": round(bounds_max[1] - bounds_min[1], 4),
            "zlen": round(bounds_max[2] - bounds_min[2], 4),
        },
    }


def export_pair(
    shape: cq.Shape | cq.Workplane, step_stem: str, stl_stem: str | None = None
) -> tuple[Path, Path]:
    step_path = STEP_DIR / f"{step_stem}.step"
    stl_path = STL_DIR / f"{stl_stem or step_stem}.stl"
    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(
        shape,
        str(stl_path),
        tolerance=P["mesh_export"]["linear_tolerance"],
        angularTolerance=P["mesh_export"]["angular_tolerance"],
    )
    return step_path, stl_path


def validate(
    candidates: dict[str, cq.Workplane],
    parts: dict[str, dict[str, Any]],
    comparison: cq.Compound,
    exports: list[tuple[Path, Path]],
) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}
    fixed = P["fixed_authority"]
    reinforcement = P["reinforcement"]
    baseline_p = P["comparison_baseline_v007"]

    checks["required_exports_exist"] = check(
        all(a.exists() and a.stat().st_size > 0 and b.exists() and b.stat().st_size > 0 for a, b in exports),
        "Three candidate pairs, one comparison STEP and one 3-up preview STL exist and are non-empty.",
    )

    step_reload: dict[str, Any] = {}
    for step_path, _ in exports:
        loaded = cq.importers.importStep(str(step_path))
        solids = loaded.solids().vals()
        step_reload[step_path.name] = {
            "solid_count": len(solids),
            "valid": bool(solids) and all(solid.isValid() for solid in solids),
            "positive_volume": bool(solids) and all(solid.Volume() > 0.0 for solid in solids),
        }
    checks["step_reload_valid"] = check(
        all(item["valid"] and item["positive_volume"] for item in step_reload.values()),
        "Every STEP reloads with valid positive-volume solids.",
    )

    stl_metrics = {stl.name: binary_stl_metrics(stl) for _, stl in exports}
    checks["all_stl_watertight"] = check(
        all(item["watertight"] for item in stl_metrics.values()),
        "All STL meshes are watertight.",
    )
    checks["non_manifold_edges_zero"] = check(
        all(item["non_manifold_edges"] == 0 for item in stl_metrics.values()),
        "All STL meshes have zero non-manifold edges.",
    )
    checks["positive_stl_volume"] = check(
        all(not item["negative_volume"] for item in stl_metrics.values()),
        "All STL meshes have positive signed volume.",
    )

    candidate_solids = {name: len(shape.solids().vals()) for name, shape in candidates.items()}
    checks["one_solid_per_candidate"] = check(
        all(count == 1 for count in candidate_solids.values()),
        f"Candidate solid counts = {candidate_solids}.",
    )
    comparison_solid_count = len(comparison.Solids())
    checks["comparison_has_three_solids"] = check(
        comparison_solid_count == 3,
        f"Comparison layout contains {comparison_solid_count} distinct candidate solids.",
    )
    duplicates = duplicate_signatures(comparison)
    checks["no_duplicate_solids"] = check(
        not duplicates,
        "Comparison contains no duplicated solid signature.",
    )

    opening_results: dict[str, Any] = {}
    id_overlaps: dict[str, float] = {}
    ring_bboxes: dict[str, Any] = {}
    for name, shape in candidates.items():
        cp = P["candidates"][name]
        opening_results[name] = measure_finished_opening(
            parts[name]["ring"],
            cp["opening_clear"],
            cp["radial_ring_thickness"],
            cp["collar_height"],
        )
        gauge = (
            cq.Workplane("XY")
            .circle(fixed["neck_id"] / 2.0 - 0.01)
            .extrude(cp["collar_height"])
        )
        id_overlaps[name] = shape.intersect(gauge).val().Volume()
        ring_bboxes[name] = bbox_dict(parts[name]["ring"])

    checks["neck_id26p2_preserved"] = check(
        all(value < 1.0e-5 for value in id_overlaps.values()),
        f"Phi26.18 go-gauge intersection volumes = { {k: round(v, 7) for k, v in id_overlaps.items()} } mm3.",
    )
    checks["finished_opening_targets"] = check(
        all(
            abs(opening_results[name]["minimum_clear_gap_mm"] - P["candidates"][name]["opening_clear"]) <= 0.03
            for name in candidates
        ),
        "Finished B-rep minimum gaps: "
        + ", ".join(f"{name}={opening_results[name]['minimum_clear_gap_mm']:.3f} mm" for name in candidates),
    )
    checks["ring_thickness_targets"] = check(
        all(
            abs(
                ring_bboxes[name]["xlen"]
                - (fixed["neck_id"] + 2.0 * P["candidates"][name]["radial_ring_thickness"])
            ) < 0.03
            for name in candidates
        ),
        "Nominal arm thicknesses are N-A/N-B=4.0 mm and N-C=3.5 mm; B-rep outer X spans match.",
    )
    checks["collar_height_9"] = check(
        all(abs(ring_bboxes[name]["zlen"] - 9.0) < 0.03 for name in candidates),
        "All isolated ring B-reps are 9.0 mm high.",
    )
    checks["tip_radius_at_least_1p5"] = check(
        reinforcement["opening_tip_radius"] >= 1.5,
        f"Free split-tip vertical edges use R{reinforcement['opening_tip_radius']:.1f} blends.",
    )

    gusset_bboxes = {
        name: [bbox_dict(g) for g in parts[name]["root_parts"]["gussets"]]
        for name in candidates
    }
    checks["root_saddle_r8"] = check(
        7.0 <= reinforcement["root_saddle_plan_radius"] <= 8.0,
        f"Broad rear saddle plan radius = R{reinforcement['root_saddle_plan_radius']:.1f}.",
    )
    checks["two_4x14_gussets"] = check(
        all(len(items) == 2 for items in gusset_bboxes.values())
        and all(
            abs(item["xlen"] - 4.0) < 0.03 and abs(item["zlen"] - 14.0) < 0.03
            for items in gusset_bboxes.values() for item in items
        ),
        "Each candidate has two rounded gusset rails, 4.0 mm thick x 14.0 mm high.",
    )

    reference_tab, reference_tab_parts = V007.make_long_tab()
    tab_differences: dict[str, float] = {}
    for name in candidates:
        tab = parts[name]["tab"]
        delta = tab.cut(reference_tab).val().Volume() + reference_tab.cut(tab).val().Volume()
        tab_differences[name] = delta
    hold_bbox = bbox_dict(reference_tab_parts["hold"])
    tab_bbox = bbox_dict(reference_tab)
    checks["v007_tab_brep_identical"] = check(
        all(value < 1.0e-6 for value in tab_differences.values()),
        f"Symmetric tab B-rep differences = { {k: round(v, 8) for k, v in tab_differences.items()} } mm3.",
    )
    checks["tab_16x4x30"] = check(
        abs(hold_bbox["xlen"] - 16.0) < 0.03
        and abs(hold_bbox["ylen"] - 4.0) < 0.03
        and abs(tab_bbox["zlen"] - 30.0) < 0.05,
        f"Reused V007 tab B-rep = {hold_bbox['xlen']:.3f} x {hold_bbox['ylen']:.3f} x {tab_bbox['zlen']:.3f} mm.",
    )
    checks["receiver_authority_17p1x4p8"] = check(
        fixed["receiver_hold_width"] == 17.1 and fixed["receiver_hold_thickness"] == 4.8,
        "Receiver hold authority remains 17.1 x 4.8 mm and is not regenerated.",
    )
    root_bbox = bbox_dict(parts["N-B"]["root"])
    checks["root_passes_front_stem_slot"] = check(
        reinforcement["bridge_width"] <= fixed["receiver_front_stem_slot_width"]
        and max(abs(x) + reinforcement["gusset_thickness"] / 2.0 for x in reinforcement["gusset_x_centers"])
        <= fixed["receiver_front_stem_slot_width"] / 2.0,
        f"Root/gusset X envelope is 10.0 mm within the {fixed['receiver_front_stem_slot_width']:.1f} mm front stem slot.",
    )

    old_collar, old_parts = V007.make_neck_collar_long_tab()
    old_opening = measure_finished_opening(
        old_parts["ring"], baseline_p["opening_clear"], baseline_p["radial_ring_thickness"], baseline_p["collar_height"]
    )
    old_section = minimum_throat_section(old_parts["bridge"])
    root_sections = {name: minimum_throat_section(parts[name]["root"]) for name in candidates}
    root_section_increase = {
        name: (item["minimum_area_mm2"] / old_section["minimum_area_mm2"] - 1.0) * 100.0
        for name, item in root_sections.items()
    }
    checks["root_section_increased"] = check(
        all(value >= 25.0 for value in root_section_increase.values()),
        "Minimum constant-throat section rises from "
        f"{old_section['minimum_area_mm2']:.2f} mm2 to "
        + ", ".join(f"{name}={root_sections[name]['minimum_area_mm2']:.2f} mm2 ({root_section_increase[name]:.1f}%)" for name in candidates),
    )

    main_body, _ = V007.make_main_body()
    nominal_z = V007.P["assembly"]["nominal_collar_bottom_global_z"]
    slide_offsets = (42.0, 36.0, 30.0, 24.0, 18.0, 12.0, 6.0, 0.0)
    slide_paths: dict[str, list[dict[str, float]]] = {}
    for name, shape in candidates.items():
        samples = []
        for dz in slide_offsets:
            moved = shape.translate((0.0, 0.0, nominal_z + dz))
            overlap = main_body.intersect(moved).val().Volume()
            samples.append({"offset_z_mm": dz, "intersection_volume_mm3": round(overlap, 7)})
        slide_paths[name] = samples
    checks["straight_slide_path_clear"] = check(
        all(item["intersection_volume_mm3"] < 1.0e-5 for items in slide_paths.values() for item in items),
        "All three coupons are collision-free through the eight-station V007 straight slide path.",
    )

    neck_diameter = fixed["neck_id"]
    deflection: dict[str, Any] = {
        "existing_V007": {
            "opening_mm": old_opening["minimum_clear_gap_mm"],
            "total_required_gap_expansion_mm": round(neck_diameter - old_opening["minimum_clear_gap_mm"], 4),
            "symmetric_tip_deflection_mm_each": round((neck_diameter - old_opening["minimum_clear_gap_mm"]) / 2.0, 4),
        }
    }
    for name in candidates:
        gap = opening_results[name]["minimum_clear_gap_mm"]
        deflection[name] = {
            "opening_mm": gap,
            "total_required_gap_expansion_mm": round(neck_diameter - gap, 4),
            "symmetric_tip_deflection_mm_each": round((neck_diameter - gap) / 2.0, 4),
            "reduction_vs_existing_percent": round(
                (1.0 - (neck_diameter - gap) / (neck_diameter - old_opening["minimum_clear_gap_mm"])) * 100.0,
                2,
            ),
        }
    checks["deflection_reduced_vs_existing"] = check(
        all(deflection[name]["total_required_gap_expansion_mm"] < deflection["existing_V007"]["total_required_gap_expansion_mm"] for name in candidates),
        "Required total gap expansion reduces from "
        f"{deflection['existing_V007']['total_required_gap_expansion_mm']:.2f} mm to "
        + ", ".join(f"{name}={deflection[name]['total_required_gap_expansion_mm']:.2f} mm" for name in candidates),
    )

    volumes: dict[str, Any] = {
        "existing_V007": {
            "collar_total_mm3": round(old_collar.val().Volume(), 2),
            "bridge_only_mm3": round(old_parts["bridge"].val().Volume(), 2),
        }
    }
    for name, shape in candidates.items():
        volumes[name] = {
            "collar_total_mm3": round(shape.val().Volume(), 2),
            "root_saddle_bridge_gussets_mm3": round(parts[name]["root"].val().Volume(), 2),
            "total_change_vs_existing_percent": round(
                (shape.val().Volume() / old_collar.val().Volume() - 1.0) * 100.0, 2
            ),
        }
    checks["positive_material_volumes"] = check(
        all(volumes[name]["collar_total_mm3"] > 0.0 and volumes[name]["root_saddle_bridge_gussets_mm3"] > 0.0 for name in candidates),
        "All total and reinforcement-only CAD volumes are positive.",
    )

    comparison_bbox = bbox_dict(comparison)
    comparison_print_bbox = stl_metrics[f"{PREVIEW_STL_NAME}.stl"]["mesh_bbox_mm"]
    checks["bambu_a1_3up_envelope"] = check(
        comparison_print_bbox["xlen"] <= 256.0
        and comparison_print_bbox["ylen"] <= 256.0
        and comparison_print_bbox["zlen"] <= 256.0
        and comparison_print_bbox["zmin"] >= -0.01,
        f"3-up mesh envelope = {comparison_print_bbox['xlen']:.1f} x {comparison_print_bbox['ylen']:.1f} x {comparison_print_bbox['zlen']:.1f} mm with Zmin={comparison_print_bbox['zmin']:.3f} mm.",
    )

    protected_hashes = {
        rel: sha256(V007_ROOT / rel) for rel in P["protected_v007_files_sha256"]
    }
    protected_unchanged = {
        rel: protected_hashes[rel] == expected
        for rel, expected in P["protected_v007_files_sha256"].items()
    }
    checks["production_v007_files_unchanged"] = check(
        all(protected_unchanged.values()),
        f"Protected V007 source/parameters/main/collar hashes unchanged = {protected_unchanged}.",
    )

    start_git = P["start_git_state"]
    end_git = current_git_state()
    checks["git_branch_head_unchanged"] = check(
        start_git["branch"] == end_git["branch"] and start_git["head"] == end_git["head"],
        f"Start/end branch={end_git['branch']}, HEAD={end_git['head']}.",
    )
    checks["preexisting_tracked_status_unchanged"] = check(
        start_git["tracked_status"] == end_git["tracked_status"],
        "Pre-existing tracked status is unchanged; no Git mutation was performed.",
    )

    hard_failures = [name for name, item in checks.items() if item["status"] == "FAIL"]
    physical_state = {
        name: {
            "status": status,
            "detail": (
                "Known broken original V007 collar root; retained as comparison evidence."
                if status == "FAIL"
                else "Physical print/fit/durability result is not promoted by CAD validation."
            ),
        }
        for name, status in P["physical_state"].items()
    }
    cad_counts = Counter(item["status"] for item in checks.values())
    combined_counts = cad_counts.copy()
    combined_counts.update(item["status"] for item in physical_state.values())

    return {
        "project": P["project"],
        "overall_cad_status": "PASS" if not hard_failures else "FAIL",
        "hard_failures": hard_failures,
        "cad_summary_counts": dict(sorted(cad_counts.items())),
        "summary_counts_including_physical": dict(sorted(combined_counts.items())),
        "cad_checks": checks,
        "physical_state": physical_state,
        "production_authority": {
            "status": P["scope"]["production_authority"],
            "production_update": P["scope"]["production_update"],
            "first_print_recommendation": P["scope"]["first_print_recommendation"],
        },
        "git": {"start": start_git, "end": end_git},
        "protected_v007_sha256": {
            rel: {"expected": P["protected_v007_files_sha256"][rel], "actual": value, "unchanged": protected_unchanged[rel]}
            for rel, value in protected_hashes.items()
        },
        "step_reload": step_reload,
        "stl_metrics": stl_metrics,
        "geometry": {
            "candidate_solid_counts": candidate_solids,
            "comparison_solid_count": comparison_solid_count,
            "comparison_bbox_mm": comparison_bbox,
            "comparison_print_mesh_bbox_mm": comparison_print_bbox,
            "finished_opening_measurements": opening_results,
            "neck_id_gauge_intersection_mm3": {k: round(v, 7) for k, v in id_overlaps.items()},
            "ring_bboxes_mm": ring_bboxes,
            "root_system_bbox_mm": root_bbox,
            "tab_bbox_mm": tab_bbox,
            "tab_hold_bbox_mm": hold_bbox,
            "tab_symmetric_difference_mm3": {k: round(v, 8) for k, v in tab_differences.items()},
            "slide_path": slide_paths,
            "duplicate_solid_signatures": [list(item) for item in duplicates],
        },
        "comparison_existing_v007_to_candidates": {
            "opening_clear_mm": {
                "existing_V007": old_opening["minimum_clear_gap_mm"],
                **{name: opening_results[name]["minimum_clear_gap_mm"] for name in candidates},
            },
            "minimum_root_throat_section": {
                "existing_V007": old_section,
                **root_sections,
                "increase_vs_existing_percent": {k: round(v, 2) for k, v in root_section_increase.items()},
            },
            "material_volume": volumes,
            "theoretical_opening_deflection": deflection,
            "note": "Deflection is the diametral gap expansion needed to pass phi26.2; symmetric tip values divide that expansion equally between both arms.",
        },
    }


def write_manifest(exports: list[tuple[Path, Path]]) -> None:
    artifacts = [path for pair in exports for path in pair]
    artifacts.extend(
        [
            LANE / "parameters.json",
            LANE / "README.md",
            LANE / "docs" / "GEOMETRY_COMPARISON.md",
            LANE / "docs" / "BH_V007_neck_collar_coupon_visual_review.png",
            LANE / "source" / "build_neck_collar_reinforcement_coupons.py",
            LANE / "source" / "render_coupon_preview.py",
            REPORT_PATH,
            VALIDATION_DIR / "README.md",
        ]
    )
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "lane": str(LANE.relative_to(REPO_ROOT)).replace("\\", "/"),
                "production_v007_updated": False,
                "artifacts": [
                    {
                        "path": str(path.relative_to(LANE)).replace("\\", "/"),
                        "exists": path.exists(),
                        "size_bytes": path.stat().st_size if path.exists() else None,
                    }
                    for path in artifacts
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    candidates: dict[str, cq.Workplane] = {}
    parts: dict[str, dict[str, Any]] = {}
    exports: list[tuple[Path, Path]] = []
    for name in ("N-A", "N-B", "N-C"):
        candidates[name], parts[name] = make_candidate(name)
        exports.append(export_pair(candidates[name], FILE_STEMS[name]))

    print_lift = -V007.P["long_tab"]["local_z_min_from_collar_bottom"]
    placements = {"N-A": -60.0, "N-B": 0.0, "N-C": 60.0}
    comparison = cq.Compound.makeCompound(
        [
            candidates[name].translate((x, 0.0, print_lift)).val()
            for name, x in placements.items()
        ]
    )
    exports.append(export_pair(comparison, COMPARISON_STEP_NAME, PREVIEW_STL_NAME))

    report = validate(candidates, parts, comparison, exports)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(exports)
    print(
        json.dumps(
            {
                "overall_cad_status": report["overall_cad_status"],
                "hard_failures": report["hard_failures"],
                "cad_summary_counts": report["cad_summary_counts"],
                "summary_counts_including_physical": report["summary_counts_including_physical"],
                "first_print_recommendation": report["production_authority"]["first_print_recommendation"],
            }
        )
    )


if __name__ == "__main__":
    main()
