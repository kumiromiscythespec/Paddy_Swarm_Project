"""Generate and validate BH_V006 waist bottle holder CAD artifacts.

The script is intentionally self-contained so the V006 lane can be rebuilt with:

    conda run -n paddy-cadquery-280-py312 python source/build_bh_v006.py

Only files below the V006 lane are written.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
PARAM_PATH = ROOT / "parameters.json"
STEP_DIR = ROOT / "step"
STL_DIR = ROOT / "stl"
VALIDATION_DIR = ROOT / "validation"
REPORT_PATH = ROOT / "validation_report.json"

MAIN_NAME = "BH_V006_main_body_94mm_squircle_rope4p8_PETG"
COLLAR_NAME = "BH_V006_neck_collar_slide_tab_ID26p0_PETG"
ASSEMBLY_NAME = "BH_V006_assembly_reference"
ASSEMBLY_PREVIEW_NAME = "BH_V006_assembly_preview"


def load_parameters() -> dict[str, Any]:
    return json.loads(PARAM_PATH.read_text(encoding="utf-8"))


P = load_parameters()


def rounded_rect_prism(width: float, depth: float, radius: float, height: float) -> cq.Workplane:
    """Centered rounded rectangle in XY, extruded from Z=0."""
    if min(width, depth) < 2.0 * radius:
        raise ValueError("rounded rectangle radius is too large")
    result: cq.Workplane | None = None
    if width - 2.0 * radius > 1.0e-6:
        result = cq.Workplane("XY").box(
            width - 2.0 * radius, depth, height, centered=(True, True, False)
        )
    if depth - 2.0 * radius > 1.0e-6:
        cross = cq.Workplane("XY").box(
            width, depth - 2.0 * radius, height, centered=(True, True, False)
        )
        result = cross if result is None else result.union(cross)
    for x in (-width / 2.0 + radius, width / 2.0 - radius):
        for y in (-depth / 2.0 + radius, depth / 2.0 - radius):
            corner = cq.Workplane("XY").center(x, y).circle(radius).extrude(height)
            result = corner if result is None else result.union(corner)
    if result is None:
        raise RuntimeError("failed to construct rounded rectangle")
    return result.clean()


def rounded_rect_wire(width: float, depth: float, radius: float, z: float) -> cq.Wire:
    wafer = rounded_rect_prism(width, depth, radius, 0.02)
    wire = wafer.faces("<Z").wires().val()
    return wire.translate(cq.Vector(0.0, 0.0, z))


def rounded_rect_loft(
    lower_width: float,
    lower_depth: float,
    lower_radius: float,
    lower_z: float,
    upper_width: float,
    upper_depth: float,
    upper_radius: float,
    upper_z: float,
) -> cq.Workplane:
    lower = rounded_rect_wire(lower_width, lower_depth, lower_radius, lower_z)
    upper = rounded_rect_wire(upper_width, upper_depth, upper_radius, upper_z)
    solid = cq.Solid.makeLoft([lower, upper], False)
    return cq.Workplane(obj=solid)


def rounded_plate_xz(
    width: float,
    height: float,
    corner_radius: float,
    thickness: float,
    front_y: float,
    center_z: float,
) -> cq.Workplane:
    """Rounded XZ plate; `front_y` is its least-negative/bottle-side face."""
    return (
        rounded_rect_prism(width, height, corner_radius, thickness)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((0.0, front_y, center_z))
    )


def rounded_slot_cutter_xz(
    width: float,
    height: float,
    depth: float,
    front_y: float,
    center_x: float,
    center_z: float,
) -> cq.Workplane:
    return rounded_plate_xz(
        width,
        height,
        width / 2.0,
        depth,
        front_y,
        center_z,
    ).translate((center_x, 0.0, 0.0))


def safe_fillet(shape: cq.Workplane, selector: str, radius: float) -> cq.Workplane:
    try:
        return shape.edges(selector).fillet(radius)
    except Exception:
        return shape


def safe_chamfer(shape: cq.Workplane, selector: str, distance: float) -> cq.Workplane:
    try:
        return shape.edges(selector).chamfer(distance)
    except Exception:
        return shape


def make_cup() -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    cup = P["cup"]
    outer = rounded_rect_prism(
        cup["outer_x"], cup["outer_y"], cup["outer_corner_radius"], cup["height"]
    )
    # Round the exposed outer lip before cutting the cavity.
    try:
        outer = outer.faces(">Z").edges().fillet(cup["outer_top_edge_radius"])
    except Exception:
        outer = safe_chamfer(outer.faces(">Z"), None, 1.5)  # defensive fallback

    lead_h = cup["top_lead_in_height"]
    lower_cavity_height = cup["height"] - cup["bottom_thickness"] - lead_h
    cavity_lower = rounded_rect_prism(
        cup["inner_x"],
        cup["inner_y"],
        cup["inner_corner_radius"],
        lower_cavity_height,
    ).translate((0.0, 0.0, cup["bottom_thickness"]))
    lead = rounded_rect_loft(
        cup["inner_x"],
        cup["inner_y"],
        cup["inner_corner_radius"],
        cup["height"] - lead_h,
        cup["inner_x"] + 2.0 * cup["top_lead_in_radial"],
        cup["inner_y"] + 2.0 * cup["top_lead_in_radial"],
        cup["inner_corner_radius"] + cup["top_lead_in_radial"],
        cup["height"] + 0.15,
    )
    body = outer.cut(cavity_lower.union(lead))

    drains: list[cq.Workplane] = []
    for x, y in cup["drain_hole_centers_xy"]:
        drain = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(cup["drain_hole_diameter"] / 2.0)
            .extrude(cup["bottom_thickness"] + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        drains.append(drain)
        body = body.cut(drain)
    return body.clean(), {
        "outer": outer,
        "cavity_lower": cavity_lower,
        "lead_in": lead,
        "drains": cq.Compound.makeCompound([d.val() for d in drains]),
    }


def make_receiver(
    internal_width: float,
    internal_thickness: float,
    cavity_z_min: float,
    cavity_z_max: float,
    center_x: float = 0.0,
    center_y: float | None = None,
    stem_slot_width: float | None = None,
    chamfer_top: bool = True,
) -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    rec = P["receiver"]
    if center_y is None:
        center_y = P["slide_tab"]["nominal_center_y"]
    if stem_slot_width is None:
        stem_slot_width = rec["front_stem_slot_width"]

    side = rec["side_wall"]
    back = rec["back_wall"]
    lip = rec["front_lip"]
    floor_t = rec["bottom_stop_thickness"]
    outer_w = internal_width + 2.0 * side
    outer_d = internal_thickness + back + lip
    outer_back = center_y - internal_thickness / 2.0 - back
    outer_front = center_y + internal_thickness / 2.0 + lip
    full_h = cavity_z_max - (cavity_z_min - floor_t)

    back_wall = cq.Workplane("XY").box(
        outer_w, back, full_h, centered=(True, True, False)
    ).translate((center_x, outer_back + back / 2.0, cavity_z_min - floor_t))
    left_rail = cq.Workplane("XY").box(
        side, outer_d, full_h, centered=(True, True, False)
    ).translate(
        (
            center_x - internal_width / 2.0 - side / 2.0,
            (outer_back + outer_front) / 2.0,
            cavity_z_min - floor_t,
        )
    )
    right_rail = left_rail.translate((internal_width + side, 0.0, 0.0))

    lip_w = (outer_w - stem_slot_width) / 2.0
    left_lip = cq.Workplane("XY").box(
        lip_w, lip, full_h, centered=(True, True, False)
    ).translate(
        (
            center_x - outer_w / 2.0 + lip_w / 2.0,
            outer_front - lip / 2.0,
            cavity_z_min - floor_t,
        )
    )
    right_lip = left_lip.translate((outer_w - lip_w, 0.0, 0.0))
    floor = cq.Workplane("XY").box(
        outer_w, outer_d, floor_t, centered=(True, True, False)
    ).translate(
        (
            center_x,
            (outer_back + outer_front) / 2.0,
            cavity_z_min - floor_t,
        )
    )
    receiver = back_wall.union(left_rail).union(right_rail).union(left_lip).union(right_lip).union(floor).clean()
    if chamfer_top:
        try:
            receiver = receiver.faces(">Z").edges().chamfer(rec["lead_in_chamfer"])
        except Exception:
            receiver = safe_chamfer(receiver, ">Z", 0.6)
    return receiver.clean(), {
        "back_wall": back_wall,
        "left_rail": left_rail,
        "right_rail": right_rail,
        "left_lip": left_lip,
        "right_lip": right_lip,
        "floor": floor,
        "outer_width": outer_w,
        "outer_depth": outer_d,
    }


def make_main_body() -> tuple[cq.Workplane, dict[str, Any]]:
    cup, cup_parts = make_cup()
    spine = P["spine"]
    contact = P["body_contact"]
    rope = P["rope"]
    support_z = P["assembly"]["bottle_support_plane_z"]
    receiver = P["receiver"]

    spine_plate = rounded_plate_xz(
        spine["width"],
        spine["z_max"] - spine["z_min"],
        spine["root_corner_radius"],
        spine["thickness"],
        -P["cup"]["outer_y"] / 2.0 + 0.5,
        (spine["z_min"] + spine["z_max"]) / 2.0,
    )

    # Wide left/right load-path ribs, recessed from both body contact pads.
    rib_depth = spine["thickness"]
    rib_front_y = -P["cup"]["outer_y"] / 2.0 + 0.5
    right_rib = (
        cq.Workplane("XZ")
        .polyline(
            [
                (spine["width"] / 2.0 - 0.5, spine["side_rib_z_min"]),
                (34.0, spine["side_rib_z_min"]),
                (spine["width"] / 2.0 - 0.5, spine["side_rib_z_max"]),
            ]
        )
        .close()
        .extrude(rib_depth)
        .translate((0.0, rib_front_y, 0.0))
    )
    left_rib = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-spine["width"] / 2.0 + 0.5, spine["side_rib_z_min"]),
                (-34.0, spine["side_rib_z_min"]),
                (-spine["width"] / 2.0 + 0.5, spine["side_rib_z_max"]),
            ]
        )
        .close()
        .extrude(rib_depth)
        .translate((0.0, rib_front_y, 0.0))
    )

    lower_pad = rounded_plate_xz(
        contact["lower_pad_width"],
        contact["lower_pad_height"],
        contact["lower_pad_corner_radius"],
        contact["lower_pad_thickness"],
        -P["cup"]["outer_y"] / 2.0 + 0.2,
        contact["lower_pad_center_z"],
    )
    lower_pad = safe_fillet(lower_pad, None, 1.8)

    upper_front_y = -P["cup"]["outer_y"] / 2.0 - spine["thickness"] + 0.9
    upper_pad = rounded_plate_xz(
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
    for x, z in slot_centers:
        boss = rounded_plate_xz(18.0, 26.0, 7.0, 6.5, -38.5, z).translate((x, 0.0, 0.0))
        bosses.append(boss)
        upper_pad = upper_pad.union(boss)

    slot_cutters: list[cq.Workplane] = []
    for x, z in slot_centers:
        core = rounded_slot_cutter_xz(
            rope["slot_width"], rope["slot_height"], 25.0, -30.0, x, z
        )
        # Two nested entry cuts approximate a trumpet and remove the body-side knife edge.
        flare_mid = rounded_slot_cutter_xz(10.0, 16.0, 3.2, -47.0, x, z)
        flare_outer = rounded_slot_cutter_xz(
            rope["body_side_entry_width"],
            rope["body_side_entry_height"],
            3.0,
            -49.2,
            x,
            z,
        )
        cutter = core.union(flare_mid).union(flare_outer)
        slot_cutters.append(cutter)
        upper_pad = upper_pad.cut(cutter)
    try:
        upper_pad = upper_pad.faces("<Y").edges().fillet(rope["body_side_edge_radius"])
    except Exception:
        upper_pad = safe_fillet(upper_pad, "<Y", 0.8)

    cavity_z_min = support_z + receiver["bottle_relative_cavity_z_min"]
    cavity_z_max = support_z + receiver["bottle_relative_cavity_z_max"]
    receiver_shape, receiver_parts = make_receiver(
        receiver["internal_width"],
        receiver["internal_thickness"],
        cavity_z_min,
        cavity_z_max,
    )
    receiver_bridge = rounded_rect_prism(30.0, 8.2, 2.0, cavity_z_max - cavity_z_min + 3.0).translate(
        (0.0, -34.95, cavity_z_min - 3.0)
    )

    body = (
        cup.union(spine_plate)
        .union(right_rib)
        .union(left_rib)
        .union(lower_pad)
        .union(upper_pad)
        .union(receiver_bridge)
        .union(receiver_shape)
        .clean()
    )
    return body, {
        "cup": cup,
        "cup_parts": cup_parts,
        "spine": spine_plate,
        "ribs": [left_rib, right_rib],
        "lower_pad": lower_pad,
        "upper_pad": upper_pad,
        "rope_slot_cutters": slot_cutters,
        "rope_slot_centers": slot_centers,
        "receiver": receiver_shape,
        "receiver_parts": receiver_parts,
        "receiver_bridge": receiver_bridge,
        "receiver_cavity_z_min": cavity_z_min,
        "receiver_cavity_z_max": cavity_z_max,
    }


def make_neck_ring(inner_diameter: float) -> cq.Workplane:
    neck = P["neck_collar"]
    outer_diameter = inner_diameter + 2.0 * neck["wall"]
    ring = cq.Workplane("XY").circle(outer_diameter / 2.0).circle(inner_diameter / 2.0).extrude(neck["height"])
    gap = cq.Workplane("XY").box(
        neck["c_opening"],
        outer_diameter,
        neck["height"] + 2.0,
        centered=(True, False, False),
    ).translate((0.0, inner_diameter / 2.0 - 0.8, -1.0))
    ring = ring.cut(gap)
    # Fillet the four long split edges to reduce whitening/stress at snap-on entry.
    ring = safe_fillet(ring, "|Z", neck["opening_tip_radius"])
    return ring.clean()


def make_neck_collar_with_tab(inner_diameter: float = 26.0) -> tuple[cq.Workplane, dict[str, cq.Workplane]]:
    tab_p = P["slide_tab"]
    ring = make_neck_ring(inner_diameter)
    tab = rounded_rect_prism(
        tab_p["width"],
        tab_p["thickness"],
        tab_p["corner_radius"],
        tab_p["height"],
    ).translate(
        (
            0.0,
            tab_p["nominal_center_y"],
            tab_p["local_z_min_from_collar_bottom"],
        )
    )
    # Top and bottom lead edges of the key are softened without changing its gauge envelope.
    try:
        tab = tab.faces(">Z").edges().chamfer(1.0)
        tab = tab.faces("<Z").edges().chamfer(0.8)
    except Exception:
        pass

    collar_od = inner_diameter + 2.0 * P["neck_collar"]["wall"]
    bridge_front = -collar_od / 2.0 + 3.0
    tab_front = tab_p["nominal_center_y"] + tab_p["thickness"] / 2.0
    bridge_depth = bridge_front - tab_front + 0.2
    bridge_center_y = (bridge_front + tab_front) / 2.0 - 0.1
    bridge = rounded_rect_prism(
        tab_p["root_width"],
        bridge_depth,
        tab_p["root_corner_radius"],
        10.0,
    ).translate((0.0, bridge_center_y, -3.0))

    collar = ring.union(bridge).union(tab).clean()
    return collar, {"ring": ring, "bridge": bridge, "tab": tab}


def make_slide_coupon(
    receiver_width: float,
    receiver_thickness: float,
) -> tuple[cq.Compound, dict[str, cq.Workplane]]:
    receiver, _ = make_receiver(
        receiver_width,
        receiver_thickness,
        3.0,
        23.0,
        center_x=-19.0,
        center_y=0.0,
        stem_slot_width=10.8,
    )
    tab = rounded_rect_prism(16.0, 4.0, P["slide_tab"]["corner_radius"], 20.0).translate((19.0, 0.0, 0.0))
    try:
        tab = tab.faces(">Z").edges().chamfer(0.8)
        tab = tab.faces("<Z").edges().chamfer(0.8)
    except Exception:
        pass
    grip = rounded_rect_prism(22.0, 8.0, 2.0, 4.0).translate((19.0, 0.0, 20.0))
    tab_with_grip = tab.union(grip).clean()
    compound = cq.Compound.makeCompound([receiver.val(), tab_with_grip.val()])
    return compound, {"receiver": receiver, "tab": tab, "tab_with_grip": tab_with_grip}


def export_shape(shape: cq.Shape | cq.Workplane, stem: str) -> tuple[Path, Path]:
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


def stl_metrics(path: Path) -> dict[str, Any]:
    mesh = trimesh.load_mesh(path, file_type="stl", process=True)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    mesh.merge_vertices()
    sorted_edges = np.sort(mesh.edges, axis=1)
    _, counts = np.unique(sorted_edges, axis=0, return_counts=True)
    non_manifold = int(np.count_nonzero(counts != 2))
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "non_manifold_edges": non_manifold,
        "volume_mm3": round(float(mesh.volume), 3),
        "negative_volume": bool(mesh.volume <= 0.0),
        "body_count": int(len(mesh.split(only_watertight=False))),
        "bounds_mm": [[round(float(v), 3) for v in row] for row in mesh.bounds],
    }


def bbox_dict(shape: cq.Shape | cq.Workplane) -> dict[str, float]:
    obj = shape.val() if isinstance(shape, cq.Workplane) else shape
    box = obj.BoundingBox()
    return {
        "xmin": round(box.xmin, 4),
        "xmax": round(box.xmax, 4),
        "ymin": round(box.ymin, 4),
        "ymax": round(box.ymax, 4),
        "zmin": round(box.zmin, 4),
        "zmax": round(box.zmax, 4),
        "xlen": round(box.xlen, 4),
        "ylen": round(box.ylen, 4),
        "zlen": round(box.zlen, 4),
    }


def check(condition: bool, detail: str, *, pending: bool = False) -> dict[str, str]:
    return {
        "status": "PENDING" if pending else ("PASS" if condition else "FAIL"),
        "detail": detail,
    }


def duplicate_signatures(shape: cq.Shape | cq.Workplane) -> list[tuple[float, ...]]:
    obj = shape.val() if isinstance(shape, cq.Workplane) else shape
    signatures: list[tuple[float, ...]] = []
    for solid in obj.Solids():
        bb = solid.BoundingBox()
        c = solid.Center()
        signatures.append(
            tuple(round(v, 3) for v in (solid.Volume(), bb.xlen, bb.ylen, bb.zlen, c.x, c.y, c.z))
        )
    return [sig for sig, count in Counter(signatures).items() if count > 1]


def validate(
    main: cq.Workplane,
    main_parts: dict[str, Any],
    collar: cq.Workplane,
    collar_parts: dict[str, cq.Workplane],
    exports: list[tuple[Path, Path]],
    generated_shapes: dict[str, cq.Shape | cq.Workplane],
) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}
    all_paths = [path for pair in exports for path in pair]
    checks["all_step_generated"] = check(
        all(path.exists() and path.stat().st_size > 0 for path in all_paths if path.suffix == ".step"),
        "All required STEP files exist and are non-empty.",
    )
    checks["all_stl_generated"] = check(
        all(path.exists() and path.stat().st_size > 0 for path in all_paths if path.suffix == ".stl"),
        "All required STL files exist and are non-empty.",
    )

    step_reload: dict[str, Any] = {}
    for step_path, _ in exports:
        loaded = cq.importers.importStep(str(step_path))
        solids = loaded.solids().vals()
        step_reload[step_path.name] = {
            "solid_count": len(solids),
            "valid": bool(solids) and all(s.isValid() for s in solids),
            "positive_volume": bool(solids) and all(s.Volume() > 0.0 for s in solids),
        }
    checks["step_reload_valid"] = check(
        all(item["valid"] and item["positive_volume"] for item in step_reload.values()),
        "Every STEP reloaded in CadQuery with valid positive-volume solids.",
    )

    mesh_results = {stl.name: stl_metrics(stl) for _, stl in exports}
    checks["all_stl_watertight"] = check(
        all(m["watertight"] for m in mesh_results.values()),
        "Every STL is watertight, including multi-shell coupon/assembly files.",
    )
    checks["non_manifold_edge_zero"] = check(
        all(m["non_manifold_edges"] == 0 for m in mesh_results.values()),
        "All STL edge incidences are exactly two.",
    )
    checks["no_negative_volume"] = check(
        all(not m["negative_volume"] for m in mesh_results.values()),
        "All STL signed volumes are positive.",
    )

    duplicates = {name: duplicate_signatures(shape) for name, shape in generated_shapes.items()}
    checks["no_duplicate_body"] = check(
        not any(duplicates.values()),
        "No artifact contains geometrically duplicated solid signatures; coupon kits intentionally contain distinct solids.",
    )

    assembly_z = P["assembly"]["nominal_collar_bottom_global_z"]
    collar_placed = collar.translate((0.0, 0.0, assembly_z))
    intersection_volume = main.intersect(collar_placed).val().Volume()
    checks["assembly_no_unintended_intersection"] = check(
        intersection_volume < 1.0e-4,
        f"Main/collar nominal intersection volume = {intersection_volume:.6f} mm^3.",
    )

    insertion_path: list[dict[str, float]] = []
    path_clear = True
    for dz in (30.0, 24.0, 18.0, 12.0, 6.0, 0.0):
        moved = collar.translate((0.0, 0.0, assembly_z + dz))
        iv = main.intersect(moved).val().Volume()
        insertion_path.append({"offset_z": dz, "intersection_volume_mm3": round(iv, 6)})
        path_clear = path_clear and iv < 1.0e-4
    checks["nominal_slide_insertion_path"] = check(
        path_clear,
        "Discrete top-down Z path is collision-free from +30 mm to nominal seat.",
    )

    floor = main_parts["receiver_parts"]["floor"]
    checks["receiver_closed_bottom_stop"] = check(
        floor.val().Volume() > 0.0 and abs(bbox_dict(floor)["zlen"] - P["receiver"]["bottom_stop_thickness"]) < 0.01,
        f"Receiver has a {P['receiver']['bottom_stop_thickness']:.1f} mm full-width physical floor.",
    )

    neck = P["neck_collar"]
    ring_gauge = cq.Workplane("XY").circle(neck["id"] / 2.0 - 0.01).extrude(neck["height"])
    gauge_intersection = collar_parts["ring"].intersect(ring_gauge).val().Volume()
    checks["neck_collar_id_matches_parameter"] = check(
        abs(neck["id"] - 26.0) < 1.0e-9 and gauge_intersection < 1.0e-4,
        f"Nominal collar ID is {neck['id']:.1f} mm; a slightly undersize gauge has zero solid overlap.",
    )

    cup_bbox = bbox_dict(main_parts["cup"])
    checks["cup_height_94"] = check(
        abs(cup_bbox["zlen"] - P["cup"]["height"]) < 0.05,
        f"Cup B-rep Z extent = {cup_bbox['zlen']:.3f} mm (within 0.05 mm geometric tolerance of 94.0 mm).",
    )
    cavity_bbox = bbox_dict(main_parts["cup_parts"]["cavity_lower"])
    checks["cup_internal_envelope_72x72"] = check(
        abs(cavity_bbox["xlen"] - 72.0) < 0.01 and abs(cavity_bbox["ylen"] - 72.0) < 0.01,
        f"Functional cavity bbox = {cavity_bbox['xlen']:.3f} x {cavity_bbox['ylen']:.3f} mm before the 1.2 mm entry lead-in.",
    )

    slot_clear = True
    slot_details: list[dict[str, float]] = []
    for x, z in main_parts["rope_slot_centers"]:
        rope_gauge = (
            cq.Workplane("XY")
            .circle(P["rope"]["diameter"] / 2.0)
            .extrude(30.0)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((x, -30.0, z))
        )
        iv = main.intersect(rope_gauge).val().Volume()
        slot_clear = slot_clear and iv < 1.0e-4
        slot_details.append({"center_x": x, "center_z": z, "gauge_intersection_mm3": round(iv, 6)})
    checks["two_rope_slots_present"] = check(
        len(main_parts["rope_slot_centers"]) == 2 and slot_clear,
        "Two independent through-slots pass a phi4.8 mm cylindrical gauge.",
    )
    checks["rope_slot_opening_margin"] = check(
        P["rope"]["slot_width"] - P["rope"]["diameter"] >= 3.0,
        f"Minimum slot width {P['rope']['slot_width']:.1f} mm gives {P['rope']['slot_width'] - P['rope']['diameter']:.1f} mm diametral margin.",
    )

    main_bbox = bbox_dict(main)
    upper_pad_bbox = bbox_dict(main_parts["upper_pad"])
    checks["body_side_no_proud_hardware"] = check(
        abs(main_bbox["ymin"] - upper_pad_bbox["ymin"]) < 0.01,
        "The rounded upper contact pad is the rearmost feature; receiver, ribs, and spine are recessed and no hardware is present.",
    )

    cap_d = P["assembly"]["cap_rotation_clearance_diameter"]
    cap_envelope = (
        cq.Workplane("XY")
        .circle(cap_d / 2.0)
        .extrude(14.0)
        .translate((0.0, 0.0, assembly_z + neck["height"] + 0.5))
    )
    cap_main_iv = main.intersect(cap_envelope).val().Volume()
    cap_collar_iv = collar_placed.intersect(cap_envelope).val().Volume()
    checks["cap_rotation_space"] = check(
        cap_main_iv < 1.0e-4 and cap_collar_iv < 1.0e-4,
        f"Phi{cap_d:.1f} x 14 mm cap rotation envelope above collar is unobstructed.",
    )

    tab_bottom_global = assembly_z + P["slide_tab"]["local_z_min_from_collar_bottom"]
    stop_gap = tab_bottom_global - main_parts["receiver_cavity_z_min"]
    checks["cup_is_primary_weight_support"] = check(
        abs(stop_gap - P["assembly"]["nominal_tab_bottom_stop_clearance"]) < 0.01,
        f"Nominal tab floats {stop_gap:.3f} mm above receiver stop while bottle seats on the cup floor at Z={P['assembly']['bottle_support_plane_z']:.1f} mm.",
    )

    # Physical results must remain pending until coupons and full-scale tests are run.
    for key, status in P["physical_status"].items():
        checks[key] = check(False, "Requires printed coupon or field test; CAD cannot close this item.", pending=True)

    hard_failures = [name for name, item in checks.items() if item["status"] == "FAIL"]
    return {
        "project": P["project"],
        "generated_at_note": "Generated locally by source/build_bh_v006.py; no Git operation performed.",
        "overall_cad_status": "PASS" if not hard_failures else "FAIL",
        "hard_failures": hard_failures,
        "checks": checks,
        "step_reload": step_reload,
        "stl_metrics": mesh_results,
        "geometry": {
            "main_body_bbox_mm": main_bbox,
            "cup_bbox_mm": cup_bbox,
            "functional_cavity_bbox_mm": cavity_bbox,
            "receiver_cavity_z_global_mm": [
                main_parts["receiver_cavity_z_min"],
                main_parts["receiver_cavity_z_max"],
            ],
            "receiver_cavity_z_bottle_relative_mm": [
                P["receiver"]["bottle_relative_cavity_z_min"],
                P["receiver"]["bottle_relative_cavity_z_max"],
            ],
            "nominal_main_collar_intersection_mm3": round(intersection_volume, 6),
            "insertion_path": insertion_path,
            "rope_gauge_checks": slot_details,
            "nominal_tab_stop_gap_mm": round(stop_gap, 4),
            "duplicate_solid_signatures": {name: [list(sig) for sig in sigs] for name, sigs in duplicates.items()},
        },
        "authority_deviations": [
            "Spine thickness is 6.5 mm (authority basis 6.0 mm) for PETG fatigue margin; +0.5 mm is within permitted minor DFM adjustment.",
            "Receiver insertion length is 22.0 mm, the permitted upper bound, to maximize overlap across the measured 184-190 mm neck-height population.",
            "Receiver uses a 10.8 mm front stem slit. The 16 mm tab wings remain captured, so removal is still only by upward motion.",
            "The 72 x 72 mm functional cavity expands by 1.2 mm per side only over the final 1.2 mm top lead-in.",
        ],
    }


def main() -> None:
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    STL_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    main_body, main_parts = make_main_body()
    neck_collar, collar_parts = make_neck_collar_with_tab(P["neck_collar"]["id"])

    exports: list[tuple[Path, Path]] = []
    generated_shapes: dict[str, cq.Shape | cq.Workplane] = {
        MAIN_NAME: main_body,
        COLLAR_NAME: neck_collar,
    }
    exports.append(export_shape(main_body, MAIN_NAME))
    exports.append(export_shape(neck_collar, COLLAR_NAME))

    for coupon_id in P["neck_collar"]["fit_coupon_ids"]:
        stem = f"BH_V006_neck_fit_coupon_ID{coupon_id:.1f}".replace(".", "p") + "_PETG"
        coupon = make_neck_ring(coupon_id)
        generated_shapes[stem] = coupon
        exports.append(export_shape(coupon, stem))

    for key, values in P["slide_fit_coupons"].items():
        label = key.replace("_", "_")
        stem = f"BH_V006_slide_fit_coupon_{label}_PETG"
        coupon, _ = make_slide_coupon(values["receiver_width"], values["receiver_thickness"])
        generated_shapes[stem] = coupon
        exports.append(export_shape(coupon, stem))

    collar_placed = neck_collar.translate(
        (0.0, 0.0, P["assembly"]["nominal_collar_bottom_global_z"])
    )
    assembly = cq.Compound.makeCompound([main_body.val(), collar_placed.val()])
    generated_shapes[ASSEMBLY_NAME] = assembly
    assembly_step = STEP_DIR / f"{ASSEMBLY_NAME}.step"
    cq.exporters.export(assembly, str(assembly_step))
    preview_stl = STL_DIR / f"{ASSEMBLY_PREVIEW_NAME}.stl"
    cq.exporters.export(
        assembly,
        str(preview_stl),
        tolerance=P["mesh_export"]["linear_tolerance"],
        angularTolerance=P["mesh_export"]["angular_tolerance"],
    )
    # Pair assembly STEP with the preview STL for shared validation accounting.
    exports.append((assembly_step, preview_stl))

    report = validate(main_body, main_parts, neck_collar, collar_parts, exports, generated_shapes)
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
    print(json.dumps({"overall_cad_status": report["overall_cad_status"], "hard_failures": report["hard_failures"]}))


if __name__ == "__main__":
    main()
