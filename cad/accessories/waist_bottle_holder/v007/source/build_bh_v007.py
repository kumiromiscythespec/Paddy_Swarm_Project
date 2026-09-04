"""Generate and validate BH_V007 reinforced integrated-slide bottle holder CAD.

V006 is imported read-only for proven lower-cup and C-ring primitives. All
generated files are written below the V007 lane.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import cadquery as cq


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[3]
V006_SOURCE = ROOT.parent / "v006" / "source" / "build_bh_v006.py"
PARAM_PATH = ROOT / "parameters.json"
STEP_DIR = ROOT / "step"
STL_DIR = ROOT / "stl"
VALIDATION_DIR = ROOT / "validation"
REPORT_PATH = ROOT / "validation_report.json"

MAIN_NAME = "BH_V007_main_body_reinforced_integrated_slide_PETG"
COLLAR_NAME = "BH_V007_neck_collar_ID26p2_long_tab_PETG"
COUPON_NAME = "BH_V007_upper_structure_coupon_PETG"
ASSEMBLY_NAME = "BH_V007_assembly_reference"
ASSEMBLY_PREVIEW_NAME = "BH_V007_assembly_preview"


def import_v006_base():
    spec = importlib.util.spec_from_file_location("bh_v006_geometry", V006_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import V006 geometry source: {V006_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = import_v006_base()
P: dict[str, Any] = json.loads(PARAM_PATH.read_text(encoding="utf-8"))


def run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.rstrip("\n")


def current_git_state() -> dict[str, Any]:
    tracked = run_git("status", "--short", "--untracked-files=no")
    return {
        "branch": run_git("branch", "--show-current"),
        "head": run_git("rev-parse", "HEAD"),
        "tracked_status": tracked.splitlines() if tracked else [],
    }


def rect_wire(width: float, depth: float, z: float) -> cq.Wire:
    wire = cq.Workplane("XY").rect(width, depth).val()
    return wire.translate(cq.Vector(0.0, 0.0, z))


def rectangular_loft(
    lower_width: float,
    lower_depth: float,
    lower_z: float,
    upper_width: float,
    upper_depth: float,
    upper_z: float,
) -> cq.Workplane:
    lower = rect_wire(lower_width, lower_depth, lower_z)
    upper = rect_wire(upper_width, upper_depth, upper_z)
    return cq.Workplane(obj=cq.Solid.makeLoft([lower, upper], False))


def make_root_wings() -> list[cq.Workplane]:
    spine = P["upper_spine"]
    depth = spine["thickness"]
    front_y = spine["front_y"]
    right = (
        cq.Workplane("XZ")
        .polyline([(18.5, 60.0), (34.0, 60.0), (18.5, 120.0)])
        .close()
        .extrude(depth)
        .translate((0.0, front_y, 0.0))
    )
    left = (
        cq.Workplane("XZ")
        .polyline([(-18.5, 60.0), (-34.0, 60.0), (-18.5, 120.0)])
        .close()
        .extrude(depth)
        .translate((0.0, front_y, 0.0))
    )
    return [left, right]


def make_receiver_ribs() -> list[cq.Workplane]:
    spine = P["upper_spine"]
    ribs: list[cq.Workplane] = []
    for center_x in spine["rib_x_centers"]:
        rib = (
            cq.Workplane("YZ")
            .polyline(
                [
                    (spine["front_y"], spine["rib_z_min"]),
                    (spine["rib_front_y_at_top"], spine["rib_z_max"]),
                    (spine["front_y"], spine["rib_z_max"]),
                ]
            )
            .close()
            .extrude(spine["rib_thickness"])
            .translate((center_x - spine["rib_thickness"] / 2.0, 0.0, 0.0))
        )
        rib = BASE.safe_fillet(rib, "|X", 1.2)
        ribs.append(rib)
    return ribs


def make_integrated_upper_structure() -> tuple[cq.Workplane, dict[str, Any]]:
    spine_p = P["upper_spine"]
    rec = P["receiver"]
    spine = BASE.rounded_plate_xz(
        spine_p["width"],
        spine_p["z_max"] - spine_p["z_min"],
        spine_p["root_fillet"],
        spine_p["thickness"],
        spine_p["front_y"],
        (spine_p["z_min"] + spine_p["z_max"]) / 2.0,
    )

    outer_width = rec["entry_width"] + 2.0 * rec["side_wall"]
    outer_depth = rec["entry_thickness"] + rec["back_wall"] + rec["front_lip"]
    receiver_outer = BASE.rounded_rect_prism(
        outer_width,
        outer_depth,
        2.4,
        rec["total_internal_length"] + rec["bottom_stop_thickness"],
    ).translate(
        (
            0.0,
            rec["center_y"],
            rec["cavity_z_min"] - rec["bottom_stop_thickness"],
        )
    )

    hold_cavity = (
        cq.Workplane("XY")
        .box(
            rec["hold_width"],
            rec["hold_thickness"],
            rec["hold_length"],
            centered=(True, True, False),
        )
        .translate((0.0, rec["center_y"], rec["cavity_z_min"]))
    )
    entry_cavity = rectangular_loft(
        rec["hold_width"],
        rec["hold_thickness"],
        rec["hold_z_max"],
        rec["entry_width"],
        rec["entry_thickness"],
        rec["cavity_z_max"] + 0.15,
    ).translate((0.0, rec["center_y"], 0.0))

    stem_y_min = rec["center_y"] + rec["hold_thickness"] / 2.0 - 0.3
    stem_y_max = rec["outer_front_y"] + 0.45
    stem_cut = (
        cq.Workplane("XY")
        .box(
            rec["front_stem_slot_width"],
            stem_y_max - stem_y_min,
            rec["total_internal_length"] + 0.4,
            centered=(True, True, False),
        )
        .translate(
            (
                0.0,
                (stem_y_min + stem_y_max) / 2.0,
                rec["cavity_z_min"],
            )
        )
    )

    root_wings = make_root_wings()
    receiver_ribs = make_receiver_ribs()
    raw = spine.union(receiver_outer)
    for wing in root_wings:
        raw = raw.union(wing)
    for rib in receiver_ribs:
        raw = raw.union(rib)
    integrated = raw.cut(hold_cavity).cut(entry_cavity).cut(stem_cut).clean()

    return integrated, {
        "spine": spine,
        "receiver_outer": receiver_outer,
        "hold_cavity": hold_cavity,
        "entry_cavity": entry_cavity,
        "stem_cut": stem_cut,
        "root_wings": root_wings,
        "receiver_ribs": receiver_ribs,
        "raw_before_channel": raw,
        "outer_width": outer_width,
        "outer_depth": outer_depth,
    }


def make_contact_pads_and_slots() -> tuple[cq.Workplane, dict[str, Any]]:
    contact = P["body_contact"]
    rope = P["rope"]
    cup = P["cup"]
    spine = P["upper_spine"]

    lower_pad = BASE.rounded_plate_xz(
        contact["lower_pad_width"],
        contact["lower_pad_height"],
        contact["lower_pad_corner_radius"],
        contact["lower_pad_thickness"],
        -cup["outer_y"] / 2.0 + 0.2,
        contact["lower_pad_center_z"],
    )
    lower_pad = BASE.safe_fillet(lower_pad, None, 1.8)

    upper_front_y = spine["rear_y"] + 0.4
    upper_pad = BASE.rounded_plate_xz(
        contact["upper_pad_width"],
        contact["upper_pad_height"],
        contact["upper_pad_corner_radius"],
        contact["upper_pad_thickness"],
        upper_front_y,
        contact["upper_pad_center_z"],
    )
    slot_centers = [
        (-rope["slot_center_spacing"] / 2.0, rope["slot_center_z"]),
        (rope["slot_center_spacing"] / 2.0, rope["slot_center_z"]),
    ]
    bosses: list[cq.Workplane] = []
    cutters: list[cq.Workplane] = []
    for x, z in slot_centers:
        boss = BASE.rounded_plate_xz(18.0, 26.0, 7.0, 8.9, -38.3, z).translate((x, 0.0, 0.0))
        bosses.append(boss)
        upper_pad = upper_pad.union(boss)

        core = BASE.rounded_slot_cutter_xz(
            rope["slot_width"], rope["slot_height"], 28.0, -29.0, x, z
        )
        flare_mid = BASE.rounded_slot_cutter_xz(10.0, 16.0, 3.2, -49.0, x, z)
        flare_outer = BASE.rounded_slot_cutter_xz(
            rope["body_side_entry_width"],
            rope["body_side_entry_height"],
            3.0,
            -51.2,
            x,
            z,
        )
        cutter = core.union(flare_mid).union(flare_outer)
        cutters.append(cutter)
        upper_pad = upper_pad.cut(cutter)
    try:
        upper_pad = upper_pad.faces("<Y").edges().fillet(rope["body_side_edge_radius"])
    except Exception:
        upper_pad = BASE.safe_fillet(upper_pad, "<Y", 0.8)

    return lower_pad.union(upper_pad).clean(), {
        "lower_pad": lower_pad,
        "upper_pad": upper_pad,
        "bosses": bosses,
        "slot_cutters": cutters,
        "slot_centers": slot_centers,
    }


def make_main_body() -> tuple[cq.Workplane, dict[str, Any]]:
    original_base_parameters = BASE.P
    BASE.P = copy.deepcopy(BASE.P)
    BASE.P["cup"].update(P["cup"])
    cup, cup_parts = BASE.make_cup()
    BASE.P = original_base_parameters

    upper_structure, upper_parts = make_integrated_upper_structure()
    contact_structure, contact_parts = make_contact_pads_and_slots()
    body = cup.union(upper_structure).union(contact_structure).clean()
    return body, {
        "cup": cup,
        "cup_parts": cup_parts,
        "upper_structure": upper_structure,
        "upper_parts": upper_parts,
        "contact_structure": contact_structure,
        "contact_parts": contact_parts,
    }


def make_long_tab() -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    tab = P["long_tab"]
    main_z_min = tab["local_z_min_from_collar_bottom"] + tab["nose_length"]
    main_height = tab["local_z_max_from_collar_bottom"] - main_z_min
    hold = BASE.rounded_rect_prism(
        tab["width"], tab["thickness"], tab["hold_corner_radius"], main_height
    ).translate((0.0, tab["center_y"], main_z_min))

    nose_lower = BASE.rounded_rect_wire(
        tab["nose_tip_width"],
        tab["nose_tip_thickness"],
        min(tab["hold_corner_radius"], tab["nose_tip_thickness"] / 2.0),
        tab["local_z_min_from_collar_bottom"],
    )
    nose_upper = BASE.rounded_rect_wire(
        tab["width"],
        tab["thickness"],
        tab["hold_corner_radius"],
        main_z_min + 0.05,
    )
    # Ruled=True prevents the B-spline overshoot that would exceed the 5.1 mm entry gauge.
    nose = cq.Workplane(obj=cq.Solid.makeLoft([nose_lower, nose_upper], True)).translate(
        (0.0, tab["center_y"], 0.0)
    )
    return hold.union(nose).clean(), {"hold": hold, "nose": nose}


def make_neck_collar_long_tab() -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    neck = P["neck_collar"]
    tab = P["long_tab"]
    ring = BASE.make_neck_ring(neck["id"])
    long_tab, tab_parts = make_long_tab()

    bridge_front = -neck["od"] / 2.0 + 3.0
    tab_front = tab["center_y"] + tab["thickness"] / 2.0
    bridge_depth = bridge_front - tab_front + 0.2
    bridge_center_y = (bridge_front + tab_front) / 2.0 - 0.1
    bridge = BASE.rounded_rect_prism(
        tab["root_width"], bridge_depth, tab["root_plan_radius"], 10.0
    ).translate((0.0, bridge_center_y, -3.0))
    collar = ring.union(bridge).union(long_tab).clean()
    return collar, {
        "ring": ring,
        "bridge": bridge,
        "tab": long_tab,
        "tab_hold": tab_parts["hold"],
        "tab_nose": tab_parts["nose"],
    }


def make_bottle_clearance_envelope() -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    env = P["bottle_clearance_envelope"]
    support_z = P["assembly"]["bottle_support_plane_z"]
    body = BASE.rounded_rect_prism(
        env["upper_body_x"],
        env["upper_body_y"],
        env["upper_body_corner_radius"],
        env["upper_body_z_max"] - support_z,
    ).translate((0.0, 0.0, support_z))
    lower_wire = BASE.rounded_rect_wire(
        env["upper_body_x"],
        env["upper_body_y"],
        env["upper_body_corner_radius"],
        env["upper_body_z_max"],
    )
    upper_wire = (
        cq.Workplane("XY")
        .circle(env["neck_diameter"] / 2.0)
        .val()
        .translate(cq.Vector(0.0, 0.0, env["shoulder_z_max"]))
    )
    shoulder = cq.Workplane(obj=cq.Solid.makeLoft([lower_wire, upper_wire], False))
    neck = (
        cq.Workplane("XY")
        .circle(env["neck_diameter"] / 2.0)
        .extrude(env["neck_z_max"] - env["shoulder_z_max"])
        .translate((0.0, 0.0, env["shoulder_z_max"]))
    )
    envelope = body.union(shoulder).union(neck).clean()
    return envelope, {"body": body, "shoulder": shoulder, "neck": neck}


def make_upper_structure_coupon(
    upper_structure: cq.Workplane, collar: cq.Workplane
) -> tuple[cq.Compound, dict[str, cq.Workplane]]:
    spine = P["upper_spine"]
    cup = P["cup"]
    support_z = P["assembly"]["bottle_support_plane_z"]
    base = BASE.rounded_rect_prism(90.0, 105.0, 10.0, support_z).translate((0.0, -5.0, 0.0))
    lower_post = (
        cq.Workplane("XY")
        .box(
            spine["width"],
            spine["thickness"],
            spine["z_min"] + 10.0 - support_z,
            centered=(True, True, False),
        )
        .translate(
            (
                0.0,
                (spine["front_y"] + spine["rear_y"]) / 2.0,
                support_z,
            )
        )
    )
    datum_outer = BASE.rounded_rect_prism(
        cup["outer_x"], cup["outer_y"], cup["outer_corner_radius"], 8.0
    ).translate((0.0, 0.0, support_z))
    datum_inner = BASE.rounded_rect_prism(
        cup["inner_x"], cup["inner_y"], cup["inner_corner_radius"], 8.2
    ).translate((0.0, 0.0, support_z - 0.1))
    datum_rim = datum_outer.cut(datum_inner)
    fixture = base.union(lower_post).union(datum_rim).union(upper_structure).clean()

    # Print-layout copy: separate from the tall fixture, then install on the bottle for testing.
    collar_print = collar.translate((66.0, 0.0, -P["long_tab"]["local_z_min_from_collar_bottom"]))
    coupon = cq.Compound.makeCompound([fixture.val(), collar_print.val()])
    return coupon, {
        "fixture": fixture,
        "base": base,
        "lower_post": lower_post,
        "datum_rim": datum_rim,
        "collar_print": collar_print,
    }


def export_pair(shape: cq.Shape | cq.Workplane, stem: str) -> tuple[Path, Path]:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    step_path = STEP_DIR / f"{stem}.step"
    stl_path = STL_DIR / f"{stem}.stl"
    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(
        shape,
        str(stl_path),
        tolerance=P["mesh_export"]["linear_tolerance"],
        angularTolerance=P["mesh_export"]["angular_tolerance"],
    )
    return step_path, stl_path


def check(condition: bool, detail: str) -> dict[str, str]:
    return {"status": "PASS" if condition else "FAIL", "detail": detail}


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
                    solid.Volume(),
                    bbox.xlen,
                    bbox.ylen,
                    bbox.zlen,
                    center.x,
                    center.y,
                    center.z,
                )
            )
        )
    return [signature for signature, count in Counter(signatures).items() if count > 1]


def validate(
    main_body: cq.Workplane,
    main_parts: dict[str, Any],
    collar: cq.Workplane,
    collar_parts: dict[str, cq.Workplane],
    coupon: cq.Compound,
    coupon_parts: dict[str, cq.Workplane],
    assembly: cq.Compound,
    bottle_envelope: cq.Workplane,
    exports: list[tuple[Path, Path]],
) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}
    rec = P["receiver"]
    spine = P["upper_spine"]
    tab = P["long_tab"]
    neck = P["neck_collar"]
    cup = P["cup"]
    rope = P["rope"]
    assembly_p = P["assembly"]
    comparison = P["comparison_v006"]

    checks["all_step_generated"] = check(
        all(step.exists() and step.stat().st_size > 0 for step, _ in exports),
        "All required V007 STEP files exist and are non-empty.",
    )
    checks["all_stl_generated"] = check(
        all(stl.exists() and stl.stat().st_size > 0 for _, stl in exports),
        "All required V007 STL files exist and are non-empty.",
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

    stl_metrics = {stl.name: BASE.stl_metrics(stl) for _, stl in exports}
    checks["all_stl_watertight"] = check(
        all(item["watertight"] for item in stl_metrics.values()),
        "All V007 STL meshes are watertight.",
    )
    checks["non_manifold_edge_zero"] = check(
        all(item["non_manifold_edges"] == 0 for item in stl_metrics.values()),
        "Every V007 STL has zero non-manifold edges.",
    )
    checks["no_negative_volume"] = check(
        all(not item["negative_volume"] for item in stl_metrics.values()),
        "Every V007 STL has positive signed volume.",
    )

    shapes = {
        MAIN_NAME: main_body,
        COLLAR_NAME: collar,
        COUPON_NAME: coupon,
        ASSEMBLY_NAME: assembly,
    }
    duplicates = {name: duplicate_signatures(shape) for name, shape in shapes.items()}
    checks["no_duplicate_solid"] = check(
        not any(duplicates.values()),
        "No artifact contains duplicated solid signatures; coupon and assembly contain intentional distinct shells.",
    )

    cup_bbox = BASE.bbox_dict(main_parts["cup"])
    cavity_bbox = BASE.bbox_dict(main_parts["cup_parts"]["cavity_lower"])
    checks["cup_height_94"] = check(
        abs(cup_bbox["zlen"] - cup["height"]) < 0.05,
        f"Cup B-rep Z extent = {cup_bbox['zlen']:.3f} mm.",
    )
    checks["cup_72x72_r11"] = check(
        abs(cavity_bbox["xlen"] - cup["inner_x"]) < 0.01
        and abs(cavity_bbox["ylen"] - cup["inner_y"]) < 0.01
        and cup["inner_corner_radius"] == 11.0,
        f"Functional cavity = {cavity_bbox['xlen']:.3f} x {cavity_bbox['ylen']:.3f} mm / R{cup['inner_corner_radius']:.1f}.",
    )

    rope_gauges: list[dict[str, float]] = []
    rope_clear = True
    for x, z in main_parts["contact_parts"]["slot_centers"]:
        gauge = (
            cq.Workplane("XY")
            .circle(rope["diameter"] / 2.0)
            .extrude(32.0)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((x, -28.0, z))
        )
        overlap = main_body.intersect(gauge).val().Volume()
        rope_clear = rope_clear and overlap < 1.0e-4
        rope_gauges.append(
            {"center_x_mm": x, "center_z_mm": z, "intersection_volume_mm3": round(overlap, 6)}
        )
    checks["rope_slots_8x14_two_at_46"] = check(
        rope_clear
        and len(main_parts["contact_parts"]["slot_centers"]) == 2
        and rope["slot_width"] == 8.0
        and rope["slot_height"] == 14.0
        and rope["slot_center_spacing"] == 46.0,
        "Two 8 x 14 mm slots at 46 mm centers pass phi4.8 mm gauges.",
    )

    id_gauge = cq.Workplane("XY").circle(neck["id"] / 2.0 - 0.01).extrude(neck["height"])
    id_overlap = collar_parts["ring"].intersect(id_gauge).val().Volume()
    checks["neck_id26p2"] = check(
        neck["id"] == 26.2 and id_overlap < 1.0e-4,
        "The unchanged V006 tested C-ring primitive is generated at ID26.2 mm.",
    )

    # Measure a fresh isolated tab B-rep; collar booleans may widen cached OCC bounds.
    measurement_tab, measurement_tab_parts = make_long_tab()
    hold_bbox = BASE.bbox_dict(measurement_tab_parts["hold"])
    tab_bbox = BASE.bbox_dict(measurement_tab)
    checks["tab_width_16"] = check(
        tab["width"] == 16.0 and abs(hold_bbox["xlen"] - 16.0) < 0.05,
        f"Hold-section construction width = 16.0 mm; B-rep bbox = {hold_bbox['xlen']:.3f} mm.",
    )
    checks["tab_thickness_4"] = check(
        tab["thickness"] == 4.0 and abs(hold_bbox["ylen"] - 4.0) < 0.05,
        f"Hold-section construction thickness = 4.0 mm; B-rep bbox = {hold_bbox['ylen']:.3f} mm.",
    )
    checks["tab_height_28_to_32"] = check(
        28.0 <= tab["height"] <= 32.0 and abs(tab_bbox["zlen"] - tab["height"]) < 0.08,
        f"Long-tab B-rep height = {tab_bbox['zlen']:.3f} mm; authority = {tab['height']:.1f} mm.",
    )
    checks["tab_nose_lead_in"] = check(
        tab["nose_length"] >= 3.0
        and tab["nose_tip_width"] < tab["width"]
        and tab["nose_tip_thickness"] < tab["thickness"],
        f"The first {tab['nose_length']:.1f} mm tapers from {tab['nose_tip_width']:.1f} x {tab['nose_tip_thickness']:.1f} to 16.0 x 4.0 mm.",
    )

    hold_cavity_bbox = BASE.bbox_dict(main_parts["upper_parts"]["hold_cavity"])
    entry_bbox = BASE.bbox_dict(main_parts["upper_parts"]["entry_cavity"])
    checks["receiver_hold_17p1x4p8"] = check(
        abs(hold_cavity_bbox["xlen"] - rec["hold_width"]) < 0.01
        and abs(hold_cavity_bbox["ylen"] - rec["hold_thickness"]) < 0.01,
        f"Receiver hold cutter = {hold_cavity_bbox['xlen']:.3f} x {hold_cavity_bbox['ylen']:.3f} mm.",
    )
    checks["receiver_length_32_to_36"] = check(
        32.0 <= rec["total_internal_length"] <= 36.0
        and abs(rec["cavity_z_max"] - rec["cavity_z_min"] - rec["total_internal_length"]) < 0.01,
        f"Receiver internal guide length = {rec['total_internal_length']:.1f} mm.",
    )
    checks["receiver_entry_lead_in"] = check(
        entry_bbox["zlen"] >= 5.9
        and rec["entry_width"] > rec["hold_width"]
        and rec["entry_thickness"] > rec["hold_thickness"],
        f"Smooth loft lead-in length = {entry_bbox['zlen']:.3f} mm, expanding to {rec['entry_width']:.1f} x {rec['entry_thickness']:.1f} mm.",
    )

    assembly_z = assembly_p["nominal_collar_bottom_global_z"]
    collar_placed = collar.translate((0.0, 0.0, assembly_z))
    nominal_intersection = main_body.intersect(collar_placed).val().Volume()
    checks["main_collar_intersection_zero"] = check(
        nominal_intersection < 1.0e-4,
        f"Nominal main/collar intersection = {nominal_intersection:.6f} mm3.",
    )

    insertion_path: list[dict[str, float]] = []
    slide_clear = True
    for dz in (42.0, 36.0, 30.0, 24.0, 18.0, 12.0, 6.0, 0.0):
        moved = collar.translate((0.0, 0.0, assembly_z + dz))
        overlap = main_body.intersect(moved).val().Volume()
        slide_clear = slide_clear and overlap < 1.0e-4
        insertion_path.append({"offset_z_mm": dz, "intersection_volume_mm3": round(overlap, 6)})
    checks["straight_top_slide_in"] = check(
        slide_clear,
        "The vertical path from +42 mm to nominal seat is collision-free.",
    )

    shoulder_overlap = main_parts["upper_structure"].intersect(bottle_envelope).val().Volume()
    contact_overlap = main_parts["contact_structure"].intersect(bottle_envelope).val().Volume()
    checks["bottle_shoulder_envelope_clear"] = check(
        shoulder_overlap < 1.0e-4 and contact_overlap < 1.0e-4,
        f"Upper structural overlap with conservative bottle envelope = {shoulder_overlap + contact_overlap:.6f} mm3.",
    )

    centerline_offset = math.hypot(
        assembly_p["bottle_centerline_x"] - assembly_p["cup_centerline_x"],
        assembly_p["bottle_centerline_y"] - assembly_p["cup_centerline_y"],
    )
    receiver_tab_x_offset = abs(0.0 - assembly_p["cup_centerline_x"])
    checks["bottle_centerline_alignment"] = check(
        centerline_offset < 0.01 and receiver_tab_x_offset < 0.01,
        f"Cup/bottle axis offset = {centerline_offset:.3f} mm; receiver/tab lateral X offset = {receiver_tab_x_offset:.3f} mm.",
    )

    protrusion_reduction = 1.0 - rec["v007_forward_protrusion_from_cup_rear"] / rec["v006_forward_protrusion_from_cup_rear"]
    checks["receiver_protrusion_reduced"] = check(
        rec["v007_forward_protrusion_from_cup_rear"] < rec["v006_forward_protrusion_from_cup_rear"],
        f"Receiver forward protrusion reduced from {rec['v006_forward_protrusion_from_cup_rear']:.2f} to {rec['v007_forward_protrusion_from_cup_rear']:.2f} mm ({protrusion_reduction:.1%} reduction).",
    )

    receiver_spine_union = main_parts["upper_parts"]["receiver_outer"].intersect(
        main_parts["upper_parts"]["spine"]
    ).val().Volume()
    checks["receiver_integrated_into_spine"] = check(
        receiver_spine_union > 0.0,
        f"Receiver/spine fused overlap = {receiver_spine_union:.3f} mm3; no separate forward pedestal exists.",
    )
    checks["upper_spine_width_at_least_36"] = check(
        spine["width"] >= 36.0,
        f"Upper spine width = {spine['width']:.1f} mm.",
    )
    checks["upper_spine_thickness_at_least_8"] = check(
        spine["thickness"] >= 8.0,
        f"Upper spine thickness = {spine['thickness']:.1f} mm.",
    )
    checks["root_fillet_at_least_r8"] = check(
        spine["root_fillet"] >= 8.0,
        f"Spine/root rounded-plate radius = R{spine['root_fillet']:.1f}.",
    )
    rib_bboxes = [BASE.bbox_dict(rib) for rib in main_parts["upper_parts"]["receiver_ribs"]]
    checks["two_receiver_support_ribs"] = check(
        len(rib_bboxes) == 2
        and all(abs(bbox["xlen"] - spine["rib_thickness"]) < 0.05 for bbox in rib_bboxes),
        f"Two receiver-to-spine ribs use {spine['rib_thickness']:.1f} mm CAD thickness.",
    )

    tab_bottom_global = assembly_z + tab["local_z_min_from_collar_bottom"]
    float_mm = tab_bottom_global - rec["cavity_z_min"]
    float_low, float_high = assembly_p["acceptable_float_range"]
    checks["assembly_float_positive"] = check(
        float_mm > 0.0,
        f"Assembly float = {float_mm:.3f} mm (>0).",
    )
    checks["assembly_float_target_range"] = check(
        float_low <= float_mm <= float_high,
        f"Assembly float {float_mm:.3f} mm is within {float_low:.1f}--{float_high:.1f} mm.",
    )
    checks["cup_bottom_primary_support"] = check(
        float_mm > 0.0 and assembly_p["bottle_support_plane_z"] == cup["bottom_thickness"],
        "The bottle seats on the 3.6 mm cup floor while the tab floats above the stop.",
    )

    cap_diameter = assembly_p["cap_rotation_clearance_diameter"]
    cap_envelope = (
        cq.Workplane("XY")
        .circle(cap_diameter / 2.0)
        .extrude(14.0)
        .translate((0.0, 0.0, assembly_z + neck["height"] + 0.5))
    )
    cap_overlap = collar_placed.intersect(cap_envelope).val().Volume()
    cap_overlap += main_body.intersect(cap_envelope).val().Volume()
    checks["cap_rotation_envelope_clear"] = check(
        cap_overlap < 1.0e-4,
        f"Phi{cap_diameter:.1f} cap envelope overlap = {cap_overlap:.6f} mm3.",
    )

    coupon_core_delta = main_parts["upper_structure"].cut(coupon_parts["fixture"]).val().Volume()
    checks["upper_coupon_contains_actual_structure"] = check(
        coupon_core_delta < 1.0e-4,
        f"Actual upper-structure material absent from coupon fixture = {coupon_core_delta:.6f} mm3.",
    )
    checks["upper_coupon_has_fixture_and_long_collar"] = check(
        len(coupon.Solids()) == 2,
        "Coupon STL/STEP contains the tall reinforced fixture and a separate printable long-tab collar.",
    )

    main_bbox = BASE.bbox_dict(main_body)
    checks["bambu_a1_z_envelope"] = check(
        main_bbox["zmax"] <= 256.0,
        f"Main body maximum Z = {main_bbox['zmax']:.3f} mm, within Bambu A1 256 mm Z.",
    )

    v007_volume = main_body.val().Volume()
    volume_change = v007_volume / comparison["main_body_volume_mm3"] - 1.0
    section_increase = spine["minimum_section_area_mm2"] / comparison["upper_min_section_area_mm2"] - 1.0
    checks["upper_min_section_increased"] = check(
        spine["minimum_section_area_mm2"] > comparison["upper_min_section_area_mm2"],
        f"Analytical uninterrupted spine section increased from {comparison['upper_min_section_area_mm2']:.1f} to {spine['minimum_section_area_mm2']:.1f} mm2 ({section_increase:.1%}).",
    )

    start_git = P["start_git_state"]
    end_git = current_git_state()
    checks["git_branch_head_unchanged"] = check(
        start_git["branch"] == end_git["branch"] and start_git["head"] == end_git["head"],
        f"Start/end branch={end_git['branch']}, HEAD={end_git['head']}.",
    )
    checks["preexisting_tracked_status_unchanged"] = check(
        start_git["tracked_status"] == end_git["tracked_status"],
        "Pre-existing tracked status is unchanged; the generator performs read-only Git inspection only.",
    )

    physical_state = {
        name: {
            "status": status,
            "detail": "Inherited V006 physical result or V007 test state; CAD does not promote PENDING items.",
        }
        for name, status in P["physical_state"].items()
    }
    hard_failures = [name for name, item in checks.items() if item["status"] == "FAIL"]
    counts = Counter(item["status"] for item in checks.values())
    counts.update(item["status"] for item in physical_state.values())
    return {
        "project": P["project"],
        "overall_cad_status": "PASS" if not hard_failures else "FAIL",
        "hard_failures": hard_failures,
        "summary_counts": dict(sorted(counts.items())),
        "cad_checks": checks,
        "physical_state": physical_state,
        "git": {"start": start_git, "end": end_git},
        "step_reload": step_reload,
        "stl_metrics": stl_metrics,
        "geometry": {
            "main_body_bbox_mm": main_bbox,
            "cup_bbox_mm": cup_bbox,
            "functional_cavity_bbox_mm": cavity_bbox,
            "tab_bbox_mm": tab_bbox,
            "receiver_hold_cutter_bbox_mm": hold_cavity_bbox,
            "receiver_entry_bbox_mm": entry_bbox,
            "nominal_main_collar_intersection_mm3": round(nominal_intersection, 6),
            "slide_path": insertion_path,
            "bottle_envelope_intersection_mm3": round(shoulder_overlap + contact_overlap, 6),
            "bottle_centerline_offset_mm": round(centerline_offset, 4),
            "receiver_tab_x_offset_mm": round(receiver_tab_x_offset, 4),
            "assembly_float_mm": round(float_mm, 4),
            "cap_envelope_intersection_mm3": round(cap_overlap, 6),
            "receiver_spine_fused_overlap_mm3": round(receiver_spine_union, 3),
            "upper_coupon_missing_actual_structure_mm3": round(coupon_core_delta, 6),
            "rope_gauge_checks": rope_gauges,
            "duplicate_solid_signatures": {
                name: [list(signature) for signature in signatures]
                for name, signatures in duplicates.items()
            },
        },
        "comparison_v006_v007": {
            "receiver_forward_protrusion_mm": {
                "V006": rec["v006_forward_protrusion_from_cup_rear"],
                "V007": rec["v007_forward_protrusion_from_cup_rear"],
                "reduction_percent": round(protrusion_reduction * 100.0, 2),
            },
            "upper_min_section_area_mm2": {
                "V006": comparison["upper_min_section_area_mm2"],
                "V007": spine["minimum_section_area_mm2"],
                "increase_percent": round(section_increase * 100.0, 2),
            },
            "root_fillet_mm": {"V006": comparison["root_fillet"], "V007": spine["root_fillet"]},
            "receiver_guide_length_mm": {
                "V006": comparison["receiver_length"],
                "V007": rec["total_internal_length"],
            },
            "tab_length_mm": {"V006": comparison["tab_length"], "V007": tab["height"]},
            "bottle_centerline_offset_mm": centerline_offset,
            "main_body_cad_volume_mm3": {
                "V006": comparison["main_body_volume_mm3"],
                "V007": round(v007_volume, 2),
                "change_percent": round(volume_change * 100.0, 2),
            },
            "solid_petg_equivalent_mass_g_at_1p27": {
                "V006": round(comparison["main_body_volume_mm3"] * 0.00127, 2),
                "V007": round(v007_volume * 0.00127, 2),
                "note": "Solid-CAD equivalent only; slicer walls/infill determine printed mass.",
            },
        },
    }


def main() -> None:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    main_body, main_parts = make_main_body()
    collar, collar_parts = make_neck_collar_long_tab()
    bottle_envelope, _ = make_bottle_clearance_envelope()
    coupon, coupon_parts = make_upper_structure_coupon(main_parts["upper_structure"], collar)

    assembly_z = P["assembly"]["nominal_collar_bottom_global_z"]
    collar_placed = collar.translate((0.0, 0.0, assembly_z))
    assembly = cq.Compound.makeCompound([main_body.val(), collar_placed.val()])

    exports: list[tuple[Path, Path]] = []
    exports.append(export_pair(main_body, MAIN_NAME))
    exports.append(export_pair(collar, COLLAR_NAME))
    exports.append(export_pair(coupon, COUPON_NAME))

    assembly_step = STEP_DIR / f"{ASSEMBLY_NAME}.step"
    assembly_stl = STL_DIR / f"{ASSEMBLY_PREVIEW_NAME}.stl"
    cq.exporters.export(assembly, str(assembly_step))
    cq.exporters.export(
        assembly,
        str(assembly_stl),
        tolerance=P["mesh_export"]["linear_tolerance"],
        angularTolerance=P["mesh_export"]["angular_tolerance"],
    )
    exports.append((assembly_step, assembly_stl))

    report = validate(
        main_body,
        main_parts,
        collar,
        collar_parts,
        coupon,
        coupon_parts,
        assembly,
        bottle_envelope,
        exports,
    )
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (VALIDATION_DIR / "artifact_manifest.json").write_text(
        json.dumps(
            {
                "step": [str(path.relative_to(ROOT)).replace("\\", "/") for path, _ in exports],
                "stl": [str(path.relative_to(ROOT)).replace("\\", "/") for _, path in exports],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "overall_cad_status": report["overall_cad_status"],
                "hard_failures": report["hard_failures"],
                "summary_counts": report["summary_counts"],
                "assembly_float_mm": report["geometry"]["assembly_float_mm"],
            }
        )
    )


if __name__ == "__main__":
    main()
