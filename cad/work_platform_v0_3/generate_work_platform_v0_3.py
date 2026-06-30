"""
Paddy Swarm Work Platform Chassis v0.3
Functional 4-wheel work rover CAD generator.

This CAD pack intentionally shifts the design goal away from a turtle-shaped body.
The vehicle is a work platform for:
- direct seeding / small transplanting front module
- under-belly weeding module
- high-cut harvest assist rear arm

Outputs simple STL concept/prototype parts for Grade 0 mechanical fit tests.
Not waterproof-certified; do not mount electronics or batteries for water tests.
"""
from pathlib import Path
import math
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix

OUT = Path(__file__).resolve().parents[2] / "stl" / "work_platform_v0_3"
OUT.mkdir(parents=True, exist_ok=True)


def box(name, size, center):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    m.metadata["name"] = name
    return m


def cyl(name, radius, depth, center, axis="z", sections=48):
    m = trimesh.creation.cylinder(radius=radius, height=depth, sections=sections)
    if axis == "x":
        m.apply_transform(rotation_matrix(math.radians(90), [0,1,0]))
    elif axis == "y":
        m.apply_transform(rotation_matrix(math.radians(90), [1,0,0]))
    m.apply_translation(center)
    m.metadata["name"] = name
    return m


def triangular_prism(name, length, width_bottom, width_top, height, center):
    # x length, y width, z height; trapezoid cross-section with water shedding slopes
    L = length/2; wb = width_bottom/2; wt = width_top/2; h = height
    z0 = 0; z1 = h
    verts = np.array([
        [-L,-wb,z0],[ L,-wb,z0],[ L, wb,z0],[-L, wb,z0],
        [-L,-wt,z1],[ L,-wt,z1],[ L, wt,z1],[-L, wt,z1],
    ], dtype=float)
    faces = np.array([
        [0,1,2],[0,2,3],
        [4,7,6],[4,6,5],
        [0,4,5],[0,5,1],
        [1,5,6],[1,6,2],
        [2,6,7],[2,7,3],
        [3,7,4],[3,4,0]
    ])
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.apply_translation([center[0], center[1], center[2]-h/2])
    m.metadata["name"] = name
    return m


def export(mesh, filename):
    mesh.export(OUT / filename)


def concat(parts):
    return trimesh.util.concatenate(parts)

# Common dimensions, mm
L = 520
body_w = 240
wheel_track_y = 330
wheel_x = 205
wheel_r = 55
wheel_w = 36
z_wheel = 58

# 001 Functional chassis frame: side rails, cross-members, belly corridor, attachment hardpoints
parts = []
# side longitudinal rails
parts += [box('left_side_rail', [500, 18, 28], [0, -105, 58]), box('right_side_rail', [500, 18, 28], [0, 105, 58])]
# upper central rails to hold dry cassette and protective cover
parts += [box('left_upper_inner_rail', [360, 12, 20], [0, -55, 92]), box('right_upper_inner_rail', [360, 12, 20], [0, 55, 92])]
# front/rear cross beams
for x in [-235, -170, 170, 235]:
    parts.append(box('cross_beam', [18, 230, 30], [x, 0, 60]))
# belly module rails, leave clear center 90 mm
parts += [box('belly_left_module_rail', [310, 10, 18], [0, -45, 32]), box('belly_right_module_rail', [310, 10, 18], [0, 45, 32])]
# low battery tray pad
parts.append(box('low_battery_floor', [260, 90, 8], [20, 0, 22]))
# mount bosses / standoff pads
for x in [-140, 0, 140]:
    for y in [-70,70]:
        parts.append(cyl('m3_mount_boss', 7, 12, [x,y,103], axis='z', sections=24))
# front/rear attachment receiver blocks
parts += [box('front_receiver_left', [54, 26, 34], [-276, -72, 58]), box('front_receiver_right', [54, 26, 34], [-276, 72, 58])]
parts += [box('rear_receiver_left', [54, 26, 34], [276, -72, 58]), box('rear_receiver_right', [54, 26, 34], [276, 72, 58])]
# side float rails / buoyancy mounting ledges
parts += [box('left_float_mount_ledge', [420, 32, 42], [0, -142, 44]), box('right_float_mount_ledge', [420, 32, 42], [0, 142, 44])]
chassis = concat(parts)
export(chassis, 'PSR-WP-001-R00_four_wheel_work_chassis_frame.stl')

# 002 Front quick attachment mount for direct seeding / planting / weeding
parts = []
parts += [box('front_mount_crossbar', [30, 220, 26], [-300, 0, 72])]
parts += [box('front_mount_lower_crossbar', [26, 220, 20], [-315, 0, 36])]
for y in [-82, 0, 82]:
    parts.append(box('vertical_socket', [26, 18, 64], [-300, y, 64]))
# quick pin towers
for y in [-95,95]:
    parts.append(cyl('pin_boss', 9, 24, [-327, y, 72], axis='x', sections=24))
export(concat(parts), 'PSR-WP-002-R00_front_quick_attachment_mount.stl')

# 003 Rear high-cut / harvest assist mount
parts = []
parts += [box('rear_mount_crossbar', [30, 220, 28], [300, 0, 76])]
parts += [box('rear_mount_lower_crossbar', [26, 220, 20], [315, 0, 38])]
for y in [-82, 0, 82]:
    parts.append(box('rear_vertical_socket', [26, 18, 70], [300, y, 70]))
for y in [-95,95]:
    parts.append(cyl('rear_pin_boss', 9, 24, [327, y, 76], axis='x', sections=24))
# vertical hinge ears for high-cut arm
for y in [-55,55]:
    parts.append(box('high_cut_hinge_ear', [16, 16, 80], [336, y, 96]))
export(concat(parts), 'PSR-WP-003-R00_rear_high_cut_arm_mount.stl')

# 004 Belly weeding module carrier / clearance gauge
parts = []
parts += [box('belly_module_frame_left', [280, 12, 18], [0, -38, 18]), box('belly_module_frame_right', [280, 12, 18], [0, 38, 18])]
parts += [box('belly_front_cross', [12, 88, 18], [-145, 0, 18]), box('belly_rear_cross', [12, 88, 18], [145, 0, 18])]
# stirrer axle dummy and tines
parts.append(cyl('stirrer_axle_dummy', 10, 130, [0,0,6], axis='y', sections=32))
for x in [-90,-60,-30,0,30,60,90]:
    for angle in [0,120,240]:
        rad=math.radians(angle)
        y=math.cos(rad)*28; z=6+math.sin(rad)*28
        tine=box('flex_tine_dummy', [8, 6, 50], [x, y, z])
        tine.apply_transform(rotation_matrix(rad, [1,0,0], point=[x,0,6]))
        parts.append(tine)
export(concat(parts), 'PSR-WP-004-R00_belly_weeding_module_carrier_dummy.stl')

# 005 Direct seeding / planting front module dummy
parts = []
parts += [box('module_back_plate', [18, 210, 70], [-335, 0, 82])]
parts += [box('seed_hopper_left', [70, 55, 75], [-385, -42, 132]), box('seed_hopper_right', [70, 55, 75], [-385, 42, 132])]
parts.append(cyl('metering_roller_dummy', 14, 150, [-385,0,84], axis='y', sections=32))
# opener shoes and drop tubes
for y in [-50,0,50]:
    parts.append(box('seed_drop_tube', [12, 10, 70], [-430, y, 55]))
    parts.append(box('shallow_opener_shoe', [65, 12, 14], [-455, y, 18]))
export(concat(parts), 'PSR-WP-005-R00_direct_seeding_planting_module_dummy.stl')

# 006 High-cut harvest assist rear arm dummy
parts = []
parts += [box('rear_arm_base_plate', [18, 210, 60], [335, 0, 84])]
# arms reaching rearward and upward, cutter bar at high position
for y in [-70,70]:
    parts.append(box('high_cut_arm_side', [190, 14, 18], [425, y, 145]))
    parts.append(box('arm_drop_link', [14, 14, 120], [515, y, 95]))
parts.append(box('high_cut_cutter_bar_dummy', [22, 210, 18], [520, 0, 55]))
parts.append(box('panicle_guide_bar', [18, 210, 16], [475, 0, 170]))
parts.append(box('grain_catch_tray_dummy', [95, 190, 24], [425, 0, 46]))
export(concat(parts), 'PSR-WP-006-R00_high_cut_harvest_arm_dummy.stl')

# 007 Low functional protective cover (not turtle-shaped body) with service flat, charge window, solar-ready area
parts = []
parts.append(triangular_prism('low_water_shedding_cover', 390, 220, 120, 58, [0,0,138]))
# charge scute / top charging window insert and solar pad outlines
parts.append(box('charge_scute_flat_window', [70, 64, 5], [-20, 0, 171]))
parts.append(box('solar_ready_flat_area_front', [120, 88, 4], [-115, 0, 166]))
parts.append(box('solar_ready_flat_area_rear', [120, 88, 4], [105, 0, 166]))
# water shedding lips
parts += [box('left_drip_lip', [400, 8, 10], [0,-116,122]), box('right_drip_lip', [400, 8, 10], [0,116,122])]
export(concat(parts), 'PSR-WP-007-R00_low_functional_protective_cover_charge_solar_ready.stl')

# 008 Side float pair, streamlined simple
parts=[]
for y, name in [(-150,'left'),(150,'right')]:
    parts.append(box(f'{name}_side_float_body', [420, 42, 54], [0,y,42]))
    parts.append(triangular_prism(f'{name}_side_float_top_shed', 420, 42, 22, 22, [0,y,80]))
export(concat(parts), 'PSR-WP-008-R00_side_float_pair_safety_path_width.stl')

# 009 TPU wheel dummy (one wheel) for four-wheel layout
parts=[]
parts.append(cyl('tpu_tire_outer', 55, 36, [0,0,0], axis='x', sections=64))
parts.append(cyl('petg_hub_dummy', 34, 42, [0,0,0], axis='x', sections=48))
# add tread bars around circumference
for i in range(16):
    a=2*math.pi*i/16
    y=math.cos(a)*54; z=math.sin(a)*54
    tread=box('tpu_lug', [42, 9, 12], [0,y,z])
    tread.apply_transform(rotation_matrix(-a, [1,0,0], point=[0,0,0]))
    parts.append(tread)
export(concat(parts), 'PSR-WH-010-R00_tpu_lug_wheel_dummy.stl')

# 010 Full assembly reference, includes four wheels and modules (not intended for printing as one piece)
parts=[]
parts.append(chassis)
# wheels
wheel = concat([cyl('wheel', 55, 36, [0,0,0], axis='x', sections=48)])
# use exported wheel mesh duplicate? create wheel with spokes/treads simplified by using parts from above
wheelmesh = trimesh.load(OUT / 'PSR-WH-010-R00_tpu_lug_wheel_dummy.stl')
for x in [-wheel_x, wheel_x]:
    for y in [-wheel_track_y/2, wheel_track_y/2]:
        w = wheelmesh.copy(); w.apply_translation([x,y,z_wheel]); parts.append(w)
# add cover, floats, mounts and simplified modules
for fn in ['PSR-WP-002-R00_front_quick_attachment_mount.stl','PSR-WP-003-R00_rear_high_cut_arm_mount.stl','PSR-WP-004-R00_belly_weeding_module_carrier_dummy.stl','PSR-WP-007-R00_low_functional_protective_cover_charge_solar_ready.stl','PSR-WP-008-R00_side_float_pair_safety_path_width.stl']:
    parts.append(trimesh.load(OUT / fn))
export(concat(parts), 'PSR-ASM-002-R00_four_wheel_work_platform_reference_assembly.stl')

print(f'Generated STL files in {OUT}')
