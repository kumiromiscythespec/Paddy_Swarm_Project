from __future__ import annotations
from cad_primitives import box_from_bounds, cylinder_along_axis, safe_boolean, union_all
from registry_loader import component_index

def overall_bounds(boxes):
    return (
        min(box[0] for box in boxes), max(box[1] for box in boxes),
        min(box[2] for box in boxes), max(box[3] for box in boxes),
        min(box[4] for box in boxes), max(box[5] for box in boxes),
    )

def build_containment_cavity(cover_component, containment):
    bounds = list(overall_bounds(cover_component["boxes"]))
    wall = float(containment["wall_thickness_mm"])
    inner = [
        bounds[0] + wall, bounds[1] - wall,
        bounds[2] + wall, bounds[3] - wall,
        bounds[4] + wall, bounds[5] - wall,
    ]
    direction = containment["removable_direction"].upper()
    margin = wall * 2.0
    index_map = {"X-": 0, "X+": 1, "Y-": 2, "Y+": 3, "Z-": 4, "Z+": 5}
    side = index_map.get(direction, 5)
    inner[side] = bounds[side] + (-margin if side % 2 == 0 else margin)
    return box_from_bounds(inner)

def build_mounting_flange(bounds, direction, wall):
    expanded = list(bounds)
    axis = {"X": 0, "Y": 1, "Z": 2}[direction[0].upper()]
    lower = axis * 2
    upper = lower + 1
    side = upper if direction.endswith("+") else lower
    opposite = lower if side == upper else upper
    plane = bounds[side]
    expanded[lower] -= wall
    expanded[upper] += wall
    expanded[side] = plane + (wall if side == upper else -wall)
    expanded[opposite] = plane
    aperture = list(expanded)
    for other_axis in range(3):
        if other_axis != axis:
            aperture[2 * other_axis] += wall * 1.5
            aperture[2 * other_axis + 1] -= wall * 1.5
    aperture[lower] -= wall
    aperture[upper] += wall
    return safe_boolean(
        box_from_bounds(expanded),
        box_from_bounds(aperture),
        "cut",
        "mounting_flange",
    )

def build_cover_wall(part_id, params, registries):
    components = component_index(registries)
    component = components.get(part_id)
    containment = next(
        (item for item in registries["containments"] if item["cover_component"] == part_id),
        None,
    )
    if component is None or containment is None:
        raise KeyError(part_id)
    bounds = overall_bounds(component["boxes"])
    outer = box_from_bounds(bounds)
    cavity = build_containment_cavity(component, containment)
    wall = safe_boolean(outer, cavity, "cut", f"{part_id}:cavity")
    thickness = float(containment["wall_thickness_mm"])
    flange = build_mounting_flange(bounds, containment["removable_direction"], thickness)
    with_flange = safe_boolean(wall, flange, "union", f"{part_id}:flange")
    boss_shapes = []
    for instance in registries["fasteners"]["instances"]:
        if part_id not in {instance["parent_component"], instance["child_component"]}:
            continue
        boss_diameter = float(instance["clearance_hole_candidate_mm"]) + 2.0 * thickness
        boss_length = max(thickness * 2.0, float(instance["grip_length_candidate_mm"]) / 3.0)
        boss_shapes.append(
            cylinder_along_axis(
                instance["axis_origin_xyz"],
                instance["axis_direction_xyz"],
                boss_diameter,
                boss_length,
            )
        )
    bossed = safe_boolean(with_flange, union_all(boss_shapes), "union", f"{part_id}:bosses") if boss_shapes else with_flange
    return {
        "outer": outer,
        "cavity": cavity,
        "wall": wall,
        "flange": flange,
        "solid": bossed,
        "boss_count": len(boss_shapes),
        "removable_direction": containment["removable_direction"],
    }

def build_all_covers(params, registries):
    return {
        containment["cover_component"]: build_cover_wall(containment["cover_component"], params, registries)
        for containment in registries["containments"]
    }
