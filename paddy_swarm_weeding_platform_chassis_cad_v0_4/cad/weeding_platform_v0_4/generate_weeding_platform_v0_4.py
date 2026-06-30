from pathlib import Path
import math, zipfile, csv, textwrap, os
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix

ROOT = Path('/mnt/data/paddy_swarm_weeding_platform_chassis_cad_v0_4')
STL = ROOT/'stl'/'weeding_platform_v0_4'
CAD = ROOT/'cad'/'weeding_platform_v0_4'
DOCS = ROOT/'docs'
PN = DOCS/'print_notes'
for p in [STL, CAD, DOCS, PN]: p.mkdir(parents=True, exist_ok=True)

# ---------- primitive helpers ----------
def box(name, size, center):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    m.metadata['name'] = name
    return m

def cyl(name, radius, depth, center, axis='z', sections=48):
    m = trimesh.creation.cylinder(radius=radius, height=depth, sections=sections)
    if axis == 'x':
        m.apply_transform(rotation_matrix(math.radians(90), [0,1,0]))
    elif axis == 'y':
        m.apply_transform(rotation_matrix(math.radians(90), [1,0,0]))
    m.apply_translation(center)
    m.metadata['name'] = name
    return m

def cone(name, r1, r2, depth, center, axis='z', sections=48):
    m = trimesh.creation.cone(radius1=r1, radius2=r2, height=depth, sections=sections)
    if axis == 'x':
        m.apply_transform(rotation_matrix(math.radians(90), [0,1,0]))
    elif axis == 'y':
        m.apply_transform(rotation_matrix(math.radians(90), [1,0,0]))
    m.apply_translation(center)
    m.metadata['name'] = name
    return m

def wedge(name, length, width_bottom, width_top, height, center):
    # trapezoid prism, x length, y width, z height, centered at center
    L=length/2; wb=width_bottom/2; wt=width_top/2; h=height
    verts=np.array([
        [-L,-wb,0],[L,-wb,0],[L,wb,0],[-L,wb,0],
        [-L,-wt,h],[L,-wt,h],[L,wt,h],[-L,wt,h]
    ],float)
    faces=np.array([[0,1,2],[0,2,3],[4,7,6],[4,6,5],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]])
    m=trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.apply_translation([center[0],center[1],center[2]-h/2])
    m.metadata['name']=name
    return m

def rounded_float_segment(name, length, width, height, center):
    # simplified pontoon: box + half-round caps approximated by cylinders at ends
    parts=[]
    parts.append(box(name+'_mid', [length-width, width, height], center))
    for x in [center[0]-(length-width)/2, center[0]+(length-width)/2]:
        cap = cyl(name+'_cap', width/2, height, [x, center[1], center[2]], axis='z', sections=32)
        # scale z? cylinder vertical, not ideal but rounded top. use as volume. 
        parts.append(cap)
    return trimesh.util.concatenate(parts)

def concat(parts): return trimesh.util.concatenate(parts)
def export(mesh, filename): mesh.export(STL/filename)

# ---------- dimensions (mm) ----------
# Goal: 30cm row-aware, 15cm water + soft mud test, low functional body.
BASE_L=540
BASE_W=220
FRAME_Z=58
WHEEL_R=48
WHEEL_W=28
WHEEL_X=205
WHEEL_Y=118  # centerline; outside tire width about 264 mm. float width removable.
WHEEL_Z=54

# ---------- part 001: base chassis ----------
parts=[]
# low rectangular central frame, keeps belly corridor open
parts += [box('left_longitudinal_rail', [520, 16, 26], [0,-78,56]), box('right_longitudinal_rail', [520,16,26], [0,78,56])]
parts += [box('left_inner_rail', [430, 10, 18], [0,-36,82]), box('right_inner_rail', [430,10,18], [0,36,82])]
for x in [-250,-150,0,150,250]:
    parts.append(box('cross_member', [16, 185, 24], [x,0,56]))
# belly weeding rails leave lower center open
parts += [box('belly_left_slide_rail', [360, 10, 16], [0,-30,28]), box('belly_right_slide_rail', [360,10,16], [0,30,28])]
# low battery/dry cassette floor
parts.append(box('low_center_battery_tray_interface', [300, 82, 8], [15,0,20]))
# four motor pockets / brackets inside wheel positions
for x in [-WHEEL_X,WHEEL_X]:
    for y in [-WHEEL_Y,WHEEL_Y]:
        parts.append(box('motor_pocket', [62,30,38], [x, y*0.82, 57]))
        parts.append(cyl('axle_passage_gauge', 7, 50, [x,y,54], axis='y', sections=24))
# front/rear option receiver sockets, no modules included
for x,label in [(-292,'front_option_receiver'),(292,'rear_option_receiver')]:
    parts.append(box(label+'_crossbar', [24,172,24], [x,0,58]))
    for y in [-64,64]:
        parts.append(box(label+'_socket', [44,22,30], [x,y,58]))
# standoff bosses for cover / dry cassette
for x in [-160,-55,55,160]:
    for y in [-62,62]:
        parts.append(cyl('m3_cover_mount_boss', 6, 10, [x,y,96], sections=24))
# small rope handle holes represented by loops
for x in [-282,282]:
    parts.append(box('recovery_rope_bridge', [10,70,18], [x,0,95]))
chassis=concat(parts)
export(chassis, 'PSR-WP-101-R00_base_chassis_four_wheel_weeding_ready.stl')

# ---------- part 002: low water-shedding protective cover ----------
parts=[]
parts.append(wedge('low_protective_cover_main', 410, 205, 145, 52, [0,0,127]))
parts.append(box('charge_scute_flat_area', [72,60,4], [-35,0,154]))
parts.append(box('solar_perovskite_ready_flat_area', [135,86,3], [95,0,151]))
# side drip lips and vents (as raised guards, no holes)
parts += [box('left_drip_lip', [420,8,10], [0,-108,112]), box('right_drip_lip', [420,8,10], [0,108,112])]
parts += [box('front_splash_deflector', [18,178,24], [-214,0,105]), box('rear_splash_deflector', [18,178,24], [214,0,105])]
cover=concat(parts)
export(cover, 'PSR-WP-102-R00_low_protective_cover_charge_solar_ready.stl')

# ---------- part 003: inner dry cassette dummy ----------
parts=[]
parts.append(box('inner_dry_cassette_body', [240,80,55], [10,0,74]))
parts.append(box('removable_cassette_lid', [260,94,8], [10,0,107]))
for x in [-98,118]:
    for y in [-36,36]: parts.append(cyl('lid_screw_boss_gauge', 5, 7, [x,y,114], sections=20))
parts.append(box('cable_gland_high_side_gauge', [22,18,18], [150,50,82]))
export(concat(parts), 'PSR-PWR-101-R00_inner_dry_cassette_dummy.stl')

# ---------- part 004: side float pair removable ----------
parts=[]
for y, side in [(-142,'left'),(142,'right')]:
    parts.append(rounded_float_segment(f'{side}_pontoon_float_body', 470, 42, 58, [0,y,48]))
    parts.append(wedge(f'{side}_float_water_shed_top', 470, 42, 20, 20, [0,y,88]))
    # removable mount ears to chassis ledges
    for x in [-170,0,170]:
        parts.append(box(f'{side}_float_mount_tab', [38,10,16], [x, y*0.90, 68]))
    # water line marker strips at 150 mm visual reference (relative to ground dummy)
    parts.append(box(f'{side}_waterline_15cm_marker', [420,3,4], [0, y + (24 if y>0 else -24), 104]))
export(concat(parts), 'PSR-FLT-101-R00_removable_side_float_pair_15cm_water.stl')

# ---------- part 005: wheel dummy one piece ----------
parts=[]
parts.append(cyl('tpu_tire_outer', WHEEL_R, WHEEL_W, [0,0,0], axis='x', sections=64))
parts.append(cyl('petg_hub_core', 28, WHEEL_W+8, [0,0,0], axis='x', sections=48))
for i in range(16):
    a=2*math.pi*i/16
    y=math.cos(a)*WHEEL_R; z=math.sin(a)*WHEEL_R
    tread=box('low_damage_tpu_lug', [WHEEL_W+8, 7, 10], [0,y,z])
    tread.apply_transform(rotation_matrix(-a, [1,0,0], point=[0,0,0]))
    parts.append(tread)
for i in range(6):
    a=2*math.pi*i/6
    spoke=box('hub_spoke_gauge', [WHEEL_W+10, 6, 32], [0, math.cos(a)*18, math.sin(a)*18])
    spoke.apply_transform(rotation_matrix(-a, [1,0,0], point=[0,0,0]))
    parts.append(spoke)
wheel=concat(parts)
export(wheel, 'PSR-WH-101-R00_tpu_low_damage_lug_wheel_dummy.stl')

# ---------- part 006: belly weeding carrier ----------
parts=[]
# slide frame and float skids. Under-belly only; front/rear modules excluded.
parts += [box('weeding_carrier_left_slide', [360,10,16], [0,-30,15]), box('weeding_carrier_right_slide', [360,10,16], [0,30,15])]
parts += [box('front_carrier_cross', [12,82,16], [-185,0,15]), box('rear_carrier_cross', [12,82,16], [185,0,15])]
# skid runners that prevent over-digging in mud
for y in [-52,52]:
    parts.append(wedge('mud_float_skid', 330, 18, 12, 16, [0,y,0]))
# height adjust gauge towers
for x in [-150,150]:
    for y in [-43,43]: parts.append(box('height_adjust_post_gauge', [12,10,45], [x,y,30]))
export(concat(parts), 'PSR-WD-101-R00_belly_weeding_module_carrier.stl')

# ---------- part 007: weeding stirrer drum and tine assembly ----------
parts=[]
parts.append(cyl('weeding_stirrer_axle', 8, 150, [0,0,0], axis='y', sections=32))
# small drums
for x in [-120,-80,-40,0,40,80,120]:
    parts.append(cyl('stirrer_disk', 18, 6, [x,0,0], axis='x', sections=32))
    for angle in [40,160,280]:
        a=math.radians(angle)
        # tine is angled sweep, not blade; designed as flexible TPU/PETG experimental part
        tine=box('flex_weeding_tine', [6,5,54], [x, math.cos(a)*25, math.sin(a)*25])
        tine.apply_transform(rotation_matrix(-a, [1,0,0], point=[x,0,0]))
        # rotate around z a little to suggest sweep
        tine.apply_transform(rotation_matrix(math.radians(12 if x%80==0 else -12), [0,0,1], point=[x,0,0]))
        parts.append(tine)
# optional guard comb
parts.append(box('stirrer_guard_bar_front', [300,8,8], [0,-72,8]))
parts.append(box('stirrer_guard_bar_rear', [300,8,8], [0,72,8]))
export(concat(parts), 'PSR-WD-102-R00_belly_weeding_stirrer_tine_unit.stl')

# ---------- part 008: under-belly weeding complete module (carrier + stirrer) ----------
carrier = trimesh.load(STL/'PSR-WD-101-R00_belly_weeding_module_carrier.stl')
stir = trimesh.load(STL/'PSR-WD-102-R00_belly_weeding_stirrer_tine_unit.stl')
stir2=stir.copy(); stir2.apply_translation([0,0,22])
export(concat([carrier, stir2]), 'PSR-WD-103-R00_belly_weeding_module_complete_reference.stl')

# ---------- assembly: base chassis + weeding complete, no direct seeding/high-cut ----------
parts=[]
parts += [chassis, cover]
parts.append(trimesh.load(STL/'PSR-PWR-101-R00_inner_dry_cassette_dummy.stl'))
parts.append(trimesh.load(STL/'PSR-FLT-101-R00_removable_side_float_pair_15cm_water.stl'))
# wheels
wheelmesh = trimesh.load(STL/'PSR-WH-101-R00_tpu_low_damage_lug_wheel_dummy.stl')
for x in [-WHEEL_X,WHEEL_X]:
    for y in [-WHEEL_Y,WHEEL_Y]:
        w=wheelmesh.copy(); w.apply_translation([x,y,WHEEL_Z]); parts.append(w)
# belly module under chassis
wm=trimesh.load(STL/'PSR-WD-103-R00_belly_weeding_module_complete_reference.stl')
wm.apply_translation([0,0,8]); parts.append(wm)
assembly=concat(parts)
export(assembly, 'PSR-ASM-103-R00_base_chassis_weeding_complete_reference_assembly.stl')

# ---------- exact-ish CAD render png using matplotlib ----------
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    mesh=assembly
    # decimate only if huge
    fig=plt.figure(figsize=(12,8), dpi=180)
    ax=fig.add_subplot(111, projection='3d')
    faces=mesh.faces
    verts=mesh.vertices
    # sample not too much
    if len(faces)>12000:
        idx=np.linspace(0,len(faces)-1,12000).astype(int)
        faces=faces[idx]
    tris=verts[faces]
    coll=Poly3DCollection(tris, linewidths=0.02, alpha=0.95)
    coll.set_facecolor((0.18,0.20,0.18,1))
    coll.set_edgecolor((0.05,0.05,0.05,0.12))
    ax.add_collection3d(coll)
    bounds=mesh.bounds
    max_range=(bounds[1]-bounds[0]).max()/2
    mid=bounds.mean(axis=0)
    ax.set_xlim(mid[0]-max_range, mid[0]+max_range)
    ax.set_ylim(mid[1]-max_range, mid[1]+max_range)
    ax.set_zlim(max(0,mid[2]-max_range*0.45), mid[2]+max_range*0.85)
    ax.view_init(elev=24, azim=-45)
    ax.set_title('Paddy Swarm Base Chassis + Belly Weeding Module v0.4\nCAD/STL reference assembly: 4 wheels, removable side floats, 15cm water/mud test concept', fontsize=12)
    ax.set_xlabel('Length X mm'); ax.set_ylabel('Width Y mm'); ax.set_zlabel('Height Z mm')
    ax.grid(False)
    ax.set_box_aspect((1.5,1,0.55))
    plt.tight_layout()
    fig.savefig(ROOT/'paddy_swarm_weeding_platform_v0_4_cad_render.png', bbox_inches='tight')
    plt.close(fig)
except Exception as e:
    (ROOT/'render_error.txt').write_text(str(e))

# ---------- docs ----------
readme = '''# Paddy Swarm Weeding Platform Chassis CAD v0.4

This pack updates the Paddy Swarm work-platform CAD toward a **base chassis + under-belly weeding machine** configuration.

This version intentionally does **not** include the removable direct-seeding / germinated-seed module or the high-cut harvest module. Front and rear option receiver interfaces remain as blank sockets so future modules can be attached without rebuilding the base chassis.

## Design target

- Four-wheel base chassis
- Under-belly weeding module for weeding season
- Removable left/right side floats for shallow-water and mud tests
- Approximately 15 cm water-condition concept, with soft mud sink-in considered
- Low water-shedding protective cover, not a turtle-shaped decorative body
- Charge Scute / top charge area retained
- Solar / perovskite-ready flat area retained, but no solar panel included
- Inner dry cassette retained as second protection layer

## Important safety note

These STL files are Grade 0 / early mechanical test geometry. They are not waterproof-certified and are not validated for real paddy-field operation. Do not mount electronics or batteries for water tests until dry-cassette and leakage tests are completed.

## Print order

1. `PSR-WP-101-R00_base_chassis_four_wheel_weeding_ready.stl`
2. `PSR-WD-101-R00_belly_weeding_module_carrier.stl`
3. `PSR-WD-102-R00_belly_weeding_stirrer_tine_unit.stl`
4. `PSR-FLT-101-R00_removable_side_float_pair_15cm_water.stl`
5. `PSR-WH-101-R00_tpu_low_damage_lug_wheel_dummy.stl`
6. `PSR-WP-102-R00_low_protective_cover_charge_solar_ready.stl`

`PSR-ASM-103` is a reference assembly and is not intended to be printed as one piece.
'''
(ROOT/'README_weeding_platform_v0_4.md').write_text(readme, encoding='utf-8')

(DOCS/'weeding_platform_chassis_v0_4.md').write_text('''# Paddy Swarm Weeding Platform Chassis v0.4

## What changed from v0.3

v0.3 tried to represent a generic work platform with direct seeding, belly weeding, and high-cut harvesting examples. In this v0.4 CAD pack, the design is narrowed to the **weeding-season complete configuration**:

- Base chassis
- Four wheels
- Removable side floats
- Low protective cover
- Inner dry cassette
- Under-belly weeding module

The following are **not included as physical modules** in this pack:

- Germinated-seed direct-seeding module
- High-cut harvest arm

Only the blank front/rear receiver sockets remain.

## Field assumptions

- Water depth target for concept review: around 15 cm
- Soft mud sink-in is expected
- Wheels may partly sink; side floats help maintain buoyancy and side protection
- Under-belly weeding module should disturb weeds and surface mud, but not dig aggressively
- 180-degree rotation in crop lanes remains discouraged; Reverse-First Navigation is still assumed

## Mechanical philosophy

The rover is a paddy-field work platform, not a turtle-shaped vehicle. The cover is low and functional. The shell-like cover is used for water-shedding and protection only.

The side floats are removable because they may not be needed for every test, and the user should be able to compare:

- base chassis without floats
- base chassis with floats
- float size variations
- float position variations

## Weeding module concept

The under-belly weeding module is represented by:

- slide-in carrier frame
- height-adjustment posts
- mud float skids
- stirrer axle
- flexible tine array
- guard bars

The module is intended for print-fit and clearance testing first. Rotation, PTO, motor coupling, sealing, and weed effectiveness require separate experiments.
''', encoding='utf-8')

(DOCS/'repo_push_weeding_platform_v0_4.md').write_text('''# Push Paddy Swarm Weeding Platform v0.4 to GitHub

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_weeding_platform_chassis_cad_v0_4.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add weeding platform base chassis CAD v0.4"
git push
```
''', encoding='utf-8')

(PN/'PSR-WP-WD-R00.md').write_text('''# Print notes: PSR-WP / PSR-WD v0.4

## First print material

- PLA for fit and clearance checks
- PETG for side floats, protective cover, chassis outdoor handling
- TPU for experimental wheels and flexible tines after geometry is confirmed

## Do not print first

- Do not start with the reference assembly.
- Do not mount electronics in water tests.
- Do not treat FDM parts as waterproof without leak testing.

## Weeding-module caution

The stirrer tine geometry is a fit-test dummy. Field use requires guarded drive shafts, waterproof motor protection, emergency stop, and low-speed tests in non-crop mud first.
''', encoding='utf-8')

manifest_rows = [
 ['part_id','filename','category','recommended_material','print_first','notes'],
 ['PSR-WP-101','PSR-WP-101-R00_base_chassis_four_wheel_weeding_ready.stl','base chassis','PLA then PETG','yes','Four-wheel frame with blank front/rear option sockets and belly rails'],
 ['PSR-WP-102','PSR-WP-102-R00_low_protective_cover_charge_solar_ready.stl','protective cover','PLA then PETG','yes','Low water-shedding cover; Charge Scute and solar/perovskite-ready area retained'],
 ['PSR-PWR-101','PSR-PWR-101-R00_inner_dry_cassette_dummy.stl','power protection','PLA','yes','Dry cassette size and clearance dummy only'],
 ['PSR-FLT-101','PSR-FLT-101-R00_removable_side_float_pair_15cm_water.stl','float','PLA then PETG','yes','Removable side floats for 15cm water and mud sink-in concept tests'],
 ['PSR-WH-101','PSR-WH-101-R00_tpu_low_damage_lug_wheel_dummy.stl','wheel','TPU/PETG split later','yes','Single wheel dummy; duplicate four times for layout check'],
 ['PSR-WD-101','PSR-WD-101-R00_belly_weeding_module_carrier.stl','weeding module','PLA then PETG','yes','Slide-in carrier with mud skids and height adjustment gauge'],
 ['PSR-WD-102','PSR-WD-102-R00_belly_weeding_stirrer_tine_unit.stl','weeding module','PLA then TPU/PETG','yes','Experimental stirrer/tine geometry dummy'],
 ['PSR-WD-103','PSR-WD-103-R00_belly_weeding_module_complete_reference.stl','weeding module assembly','PLA','no','Reference only; carrier plus stirrer'],
 ['PSR-ASM-103','PSR-ASM-103-R00_base_chassis_weeding_complete_reference_assembly.stl','reference assembly','none','no','Do not print as one piece; visual and clearance reference only'],
]
with open(ROOT/'print_manifest_weeding_platform_v0_4.csv','w',newline='',encoding='utf-8') as f:
    csv.writer(f).writerows(manifest_rows)

kit_rows = [
 ['kit_id','kit_name','includes','purpose'],
 ['PSR-KIT-WD0','Weeding Platform Fit Kit v0.4','PSR-WP-101; PSR-WD-101; PSR-WD-102; PSR-FLT-101; PSR-WH-101','Fit, clearance, float, and under-belly weeding layout checks'],
 ['PSR-KIT-WD1','Weeding Season Reference Assembly v0.4','PSR-ASM-103','Visual/reference assembly only; not one-piece print'],
 ['PSR-KIT-PWR0','Dry Cassette Check Kit v0.4','PSR-PWR-101; PSR-WP-102','Check protective cover and inner dry cassette space'],
]
with open(ROOT/'kit_index_weeding_platform_v0_4.csv','w',newline='',encoding='utf-8') as f:
    csv.writer(f).writerows(kit_rows)

# copy generator itself into CAD dir
this = Path(__file__)
(CAD/'generate_weeding_platform_v0_4.py').write_text(this.read_text(encoding='utf-8'), encoding='utf-8')

# zip it
zip_path = Path('/mnt/data/paddy_swarm_weeding_platform_chassis_cad_v0_4.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(ROOT.parent))
print('Created', zip_path)
print('Files:', len(list(ROOT.rglob('*'))))
