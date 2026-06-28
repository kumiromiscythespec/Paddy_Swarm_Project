import os, math, csv, zipfile, textwrap, json
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path('/mnt/data/paddy_swarm_3d_print_pack_v0_1')
STL = ROOT/'stl'
DOCS = ROOT/'docs'
NOTES = DOCS/'print_notes'
for p in [STL, DOCS, NOTES]:
    p.mkdir(parents=True, exist_ok=True)

# ---------- helpers ----------
def box(size, center=(0,0,0)):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    return m

def cyl(radius, height, center=(0,0,0), sections=48, axis='z'):
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis == 'x':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [0,1,0]))
    elif axis == 'y':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [1,0,0]))
    m.apply_translation(center)
    return m

def annulus(r_min, r_max, height, center=(0,0,0), sections=48, axis='z'):
    m = trimesh.creation.annulus(r_min=r_min, r_max=r_max, height=height, sections=sections)
    if axis == 'x':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [0,1,0]))
    elif axis == 'y':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [1,0,0]))
    m.apply_translation(center)
    return m

def rotate(mesh, angle_deg, axis, point=(0,0,0)):
    T = trimesh.transformations.rotation_matrix(math.radians(angle_deg), axis, point=point)
    mesh.apply_transform(T)
    return mesh

def combine(parts):
    mesh = trimesh.util.concatenate(parts)
    try:
        mesh.remove_unreferenced_vertices()
    except Exception:
        pass
    return mesh

def save(mesh, filename):
    mesh.export(STL/filename)
    return str(STL/filename)

parts_meta = []

def register(part_no, file, name, machine, material, infill, notes):
    parts_meta.append({
        'part_no': part_no,
        'file': file,
        'name': name,
        'machine': machine,
        'recommended_material': material,
        'infill': infill,
        'notes': notes,
    })

# ---------- PS-PR-A0-BMP-001-R00 bumper ----------
def make_bumper():
    # ladder-style bumper: no boolean cutouts, just rails and posts
    parts=[]
    w=260; rail_y=12; rail_z=12
    parts.append(box((w, rail_y, rail_z), (0,0, 18)))
    parts.append(box((w, rail_y, rail_z), (0,0,-18)))
    for x in [-125, -55, 55, 125]:
        parts.append(box((14, rail_y, 48), (x,0,0)))
    # rear mount lugs
    for x in [-95, 95]:
        parts.append(box((35, 30, 18), (x, 18, 0)))
        parts.append(annulus(2.2, 5.5, 8, (x, 36, 0), axis='y'))
    return combine(parts)

file='PS-PR-A0-BMP-001-R00_front_bumper.stl'
save(make_bumper(), file)
register('PS-PR-A0-BMP-001-R00', file, 'Front/rear ladder bumper, drill-to-fit mount lugs', 'Paddy Rover α-0', 'PETG / ASA', '35-50%', 'Concept R00. Mount holes are pilot annulus guides; drill/ream for final bolts.')

# ---------- Orange Pi / SBC mount ----------
def make_sbc_mount():
    parts=[box((95,70,4),(0,0,0))]
    # four standoff rings with M2.5/M3 clearance-like holes
    for x in [-37,37]:
        for y in [-25,25]:
            parts.append(annulus(1.8,5.0,10,(x,y,7)))
    # cable guard tabs
    parts.append(box((95,6,8),(0,38,6)))
    parts.append(box((95,6,8),(0,-38,6)))
    return combine(parts)
file='PS-PR-A0-SBC-001-R00_orange_pi_universal_mount.stl'
save(make_sbc_mount(), file)
register('PS-PR-A0-SBC-001-R00', file, 'Universal Orange Pi / small SBC mount plate with standoff rings', 'Paddy Rover α-0', 'PETG', '30-45%', 'Measure the exact board before use. Designed as universal drill-to-fit R00, not a certified Orange Pi One hole pattern.')

# ---------- Camera mount ----------
def make_camera_mount():
    parts=[]
    parts.append(box((70,45,5),(0,0,0))) # base
    parts.append(box((8,45,45),(-30,0,25)))
    parts.append(box((8,45,45),(30,0,25)))
    parts.append(box((60,8,12),(0,-22,10)))
    # front lens guard rectangular frame
    parts.append(box((60,6,8),(0,25,25)))
    parts.append(box((6,6,45),(-30,25,25)))
    parts.append(box((6,6,45),(30,25,25)))
    return combine(parts)
file='PS-PR-A0-CAM-001-R00_camera_cradle.stl'
save(make_camera_mount(), file)
register('PS-PR-A0-CAM-001-R00', file, 'Generic front camera cradle / protective frame', 'Paddy Rover α-0', 'PETG / ASA', '30-45%', 'Use foam tape or small screws. Final camera dimensions must be measured and adjusted.')

# ---------- Cable guide ----------
def make_cable_guide():
    parts=[]
    # series of C-like clips as separate pieces connected by spine
    parts.append(box((160,8,6),(0,0,0)))
    for x in [-60,-30,0,30,60]:
        parts.append(box((8,30,6),(x,12,0)))
        parts.append(box((8,30,6),(x,-12,0)))
        parts.append(box((8,6,16),(x,27,5)))
        parts.append(box((8,6,16),(x,-27,5)))
    return combine(parts)
file='PS-PR-A0-CBL-001-R00_cable_comb_guide.stl'
save(make_cable_guide(), file)
register('PS-PR-A0-CBL-001-R00', file, 'Cable comb guide for temporary harness routing', 'Paddy Rover α-0', 'PETG / TPU optional', '20-35%', 'Not waterproof by itself. Use inside covers or as a service loop guide.')

# ---------- Harvest V guide ----------
def make_v_guide():
    parts=[]
    # base plate
    parts.append(box((150,80,5),(0,0,0)))
    # two angled plates, rotated about z? Actually V in top view: panels vertical thin walls.
    left = box((120,4,70),(-35,0,38))
    rotate(left, -28, [0,0,1])
    right = box((120,4,70),(35,0,38))
    rotate(right, 28, [0,0,1])
    parts += [left,right]
    # rear narrow exit throat
    parts.append(box((18,20,65),(0,-45,36)))
    return combine(parts)
file='PS-HU-H0-GDE-001-R00_v_rice_stalk_guide.stl'
save(make_v_guide(), file)
register('PS-HU-H0-GDE-001-R00', file, 'V-shaped rice stalk guide for bench harvest test', 'Harvest Assist H0', 'PLA for desk / PETG for repeated test', '20-35%', 'First geometry check. Edges should be sanded smooth to avoid snagging leaves.')

# ---------- Harvest roller holder ----------
def make_roller_holder():
    parts=[]
    # base and two side pillars
    parts.append(box((110,40,8),(0,0,0)))
    parts.append(box((10,30,100),(-45,0,54)))
    parts.append(box((10,30,100),(45,0,54)))
    # bearing rings for two rollers, axis along X, two vertical levels
    for z in [35,75]:
        parts.append(annulus(4,12,12,(-50,0,z),axis='x'))
        parts.append(annulus(4,12,12,(50,0,z),axis='x'))
    # top cross support
    parts.append(box((100,12,8),(0,0,105)))
    return combine(parts)
file='PS-HU-H0-RLR-001-R00_dual_roller_side_frame.stl'
save(make_roller_holder(), file)
register('PS-HU-H0-RLR-001-R00', file, 'Dual roller side frame with bearing ring guides', 'Harvest Assist H0', 'PETG / PA12 if repeated', '40-60%', 'Use 8mm shafts or adapt holes by drilling. This is a bench-test holder, not a field unit.')

# ---------- Harvest cutter cover ----------
def make_cutter_cover():
    parts=[]
    # U-shaped guard with front opening, top transparent would be acrylic; this is printed side/top frame
    parts.append(box((120,8,55),(0,-40,30))) # rear wall
    parts.append(box((8,90,55),(-60,5,30))) # left wall
    parts.append(box((8,90,55),(60,5,30))) # right wall
    parts.append(box((120,90,6),(0,5,60))) # top frame (could be printed; transparent plate better)
    # front lip / chute connection
    parts.append(box((120,8,16),(0,50,10)))
    return combine(parts)
file='PS-HU-H0-CVR-001-R00_cutter_safety_cover_frame.stl'
save(make_cutter_cover(), file)
register('PS-HU-H0-CVR-001-R00', file, 'Cutter safety cover frame for bench test', 'Harvest Assist H0', 'PETG', '35-50%', 'Use a clear acrylic/polycarbonate inspection plate if needed. Do not operate blades without a cover.')

# ---------- Harvest straw chute ----------
def make_chute():
    parts=[]
    # ramp plate angled down
    ramp=box((100,5,100),(0,0,0))
    rotate(ramp, -35, [1,0,0])
    ramp.apply_translation((0,0,0))
    parts.append(ramp)
    # side rails angled similarly
    rail_l=box((6,8,100),(-54,0,8)); rotate(rail_l, -35, [1,0,0]); parts.append(rail_l)
    rail_r=box((6,8,100),(54,0,8)); rotate(rail_r, -35, [1,0,0]); parts.append(rail_r)
    # mounting tabs
    parts.append(box((120,12,8),(0,-45,25)))
    return combine(parts)
file='PS-HU-H0-CHU-001-R00_straw_discharge_chute.stl'
save(make_chute(), file)
register('PS-HU-H0-CHU-001-R00', file, 'Downward straw discharge chute', 'Harvest Assist H0', 'PLA/PETG', '20-35%', 'For desk tests only. Smooth surfaces reduce stem snagging.')

# ---------- Planter tray rails ----------
def make_planter_tray_rails():
    parts=[]
    # pair of long rails, 300mm apart, with stops. This STL is a scale/section, not full tray width.
    rail_len=260
    parts.append(box((rail_len,12,18),(0,-70,0)))
    parts.append(box((rail_len,12,18),(0,70,0)))
    parts.append(box((12,150,20),(-125,0,1))) # bottom stop
    parts.append(box((12,150,35),(125,0,8)))  # rear raised stop
    # small ladder cross braces
    for x in [-70,0,70]:
        parts.append(box((8,140,8),(x,0,-10)))
    return combine(parts)
file='PS-PP-P0-TRAY-001-R00_seedling_tray_rail_section.stl'
save(make_planter_tray_rails(), file)
register('PS-PP-P0-TRAY-001-R00', file, 'Seedling tray rail section / concept holder', 'Paddy Planter P-0', 'PETG / ASA', '30-45%', 'Scale/section concept. Real seedling tray dimensions must be measured before final design.')

# ---------- Planter depth gauge skid ----------
def make_depth_gauge():
    parts=[]
    # ski-like skid, three boxes approximating upturned nose
    parts.append(box((40,180,10),(0,0,0)))
    nose=box((40,45,10),(0,100,12)); rotate(nose, 20, [1,0,0]); parts.append(nose)
    tail=box((40,35,10),(0,-100,8)); rotate(tail, -12, [1,0,0]); parts.append(tail)
    # vertical mount boss and adjustment slots (as solid ears to drill)
    parts.append(box((35,16,70),(0,-20,40)))
    parts.append(box((60,8,18),(0,-20,78)))
    return combine(parts)
file='PS-PP-P0-DEPTH-001-R00_planting_depth_skid_gauge.stl'
save(make_depth_gauge(), file)
register('PS-PP-P0-DEPTH-001-R00', file, 'Planting depth skid gauge concept', 'Paddy Planter P-0', 'PETG / PA12', '40-60%', 'Concept geometry. Test in a mud box before any field use.')

# ---------- Station dock guide (bonus) ----------
def make_dock_guide():
    parts=[]
    parts.append(box((180,120,8),(0,0,0)))
    l=box((140,8,45),(-45,35,28)); rotate(l, -18,[0,0,1]); parts.append(l)
    r=box((140,8,45),(45,35,28)); rotate(r, 18,[0,0,1]); parts.append(r)
    parts.append(box((70,20,30),(0,-50,20)))
    return combine(parts)
file='PS-ST-S0-DOCK-001-R00_aze_dock_alignment_funnel.stl'
save(make_dock_guide(), file)
register('PS-ST-S0-DOCK-001-R00', file, 'Aze dock alignment funnel concept', 'Station S0', 'PETG / ASA', '35-50%', 'Bonus part. For dry dock alignment tests only, not an electrical charging connector.')

# ---------- docs ----------
readme = f"""
# Paddy Swarm 3D Print Pack v0.1 / R00 Concept Parts

This ZIP contains early **concept-level STL files** for Paddy Swarm Project prototypes.
All dimensions are in **millimeters**.

## Included prototype groups

- `Paddy Rover α-0` dry-ground basic rover parts
- `Harvest Assist H0` bench-test harvest mechanism parts
- `Paddy Planter P-0` one-row planter concept parts
- Bonus: `Station S0` dock alignment funnel concept

## Important safety status

These are **R00 concept parts**, not final load-rated engineering parts.
Do not use them directly in a real paddy field, near powered blades, or as sealed waterproof/electrical safety components without review and testing.

3D print parts are intended for:

- fit checks
- bench tests
- mockups
- low-risk dry tests
- replaceable outer parts
- guides, covers, brackets, trays, and fixtures

Use off-the-shelf or metal parts for motors, shafts, bearings, batteries, wiring, waterproof connectors, blades, and high-load structures.

## Suggested workflow

1. Print in PLA for dimension check.
2. Revise CAD dimensions after measuring real components.
3. Reprint in PETG/ASA for outdoor or repeated testing.
4. Use PA12/SLS or metal only after failure points are known.
5. Assign each printed part a visible part number before field testing.

## Part numbering rule

`PS-[MACHINE]-[STAGE]-[CATEGORY]-[NUMBER]-[REV]`

Example:

`PS-PR-A0-SBC-001-R00`

- `PS` = Paddy Swarm
- `PR` = Paddy Rover
- `A0` = Alpha-0
- `SBC` = single-board computer mount
- `001` = part number
- `R00` = revision 00
""".strip()
(ROOT/'README.md').write_text(readme, encoding='utf-8')

part_numbering = """
# Part Numbering

## Machine codes

- PR = Paddy Rover
- PP = Paddy Planter
- HU = Harvest Unit
- WU = Weeding Unit
- ST = Station
- PB = Power Box
- SC = Solar Carapace

## Stage codes

- A0 = Alpha-0
- A1 = Alpha-1
- R0 = Row-0
- P0 = Planter-0
- H0 = Harvest bench test
- W0 = Weeding bench test
- S0 = Station prototype

## Category codes

- BDY = Body / exterior
- FRM = Frame
- MNT = Mount
- CBL = Cable guide
- FND = Fender
- FLT = Float
- SKD = Skid
- WHL = Wheel
- PAD = Foot pad
- ARM = Arm
- GDE = Guide
- CVR = Cover
- BOX = Box holder
- TRAY = Tray
- DOCK = Dock part
- SEN = Sensor mount
- CAM = Camera mount
- BAT = Battery tray
- SBC = Single board computer mount
- CHU = Chute
- DEPTH = Depth gauge
""".strip()
(DOCS/'part_numbering.md').write_text(part_numbering, encoding='utf-8')

with open(ROOT/'print_manifest.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=['part_no','file','name','machine','recommended_material','infill','notes'])
    writer.writeheader(); writer.writerows(parts_meta)

# simple BOM grouped as first kit draft
with open(ROOT/'kit_index.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f)
    writer.writerow(['kit_no','kit_name','included_part_no'])
    kits = {
        'PS-PR-A0-KIT-001-R00':['PS-PR-A0-BMP-001-R00','PS-PR-A0-SBC-001-R00','PS-PR-A0-CAM-001-R00','PS-PR-A0-CBL-001-R00'],
        'PS-HU-H0-KIT-001-R00':['PS-HU-H0-GDE-001-R00','PS-HU-H0-RLR-001-R00','PS-HU-H0-CVR-001-R00','PS-HU-H0-CHU-001-R00'],
        'PS-PP-P0-KIT-001-R00':['PS-PP-P0-TRAY-001-R00','PS-PP-P0-DEPTH-001-R00'],
        'PS-ST-S0-KIT-001-R00':['PS-ST-S0-DOCK-001-R00'],
    }
    for kit, parts in kits.items():
        for pn in parts:
            writer.writerow([kit, kit.replace('-',' '), pn])

for meta in parts_meta:
    note = f"""
# {meta['part_no']}

## Name
{meta['name']}

## Machine
{meta['machine']}

## File
`stl/{meta['file']}`

## Recommended material
{meta['recommended_material']}

## Suggested infill
{meta['infill']}

## Notes
{meta['notes']}

## Safety status
R00 concept part. Validate dimensions, loads, screw clearances, material durability, and failure behavior before real machine use.
""".strip()
    (NOTES/(meta['part_no']+'.md')).write_text(note, encoding='utf-8')

# also include a lightweight OpenSCAD-style README placeholder with dimensions in human readable form
scad = """
// Paddy Swarm 3D Print Pack v0.1
// R00 concept STLs generated from parametric Python/trimesh primitives.
// Use the STL files for preview/printing and edit dimensions in the source script if needed.
// All dimensions are millimeters.
""".strip()
(ROOT/'SOURCE_NOTE.txt').write_text(scad, encoding='utf-8')

# copy generator script into pack
import shutil
shutil.copy('/mnt/data/create_paddy_3d_pack.py', ROOT/'source_create_paddy_3d_pack.py')

# make zip
zip_path = Path('/mnt/data/paddy_swarm_3d_print_pack_v0_1.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for path in ROOT.rglob('*'):
        z.write(path, path.relative_to(ROOT.parent))
print(zip_path)
print(len(parts_meta),'STL parts created')
for m in parts_meta:
    print(m['part_no'], m['file'])
