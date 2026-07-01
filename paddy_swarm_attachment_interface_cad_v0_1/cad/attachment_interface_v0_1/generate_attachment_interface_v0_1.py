import os, csv, zipfile, shutil, math
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path('/mnt/data/paddy_swarm_attachment_interface_cad_v0_1')
if ROOT.exists():
    shutil.rmtree(ROOT)
(STL := ROOT/'stl'/'attachment_interface_v0_1').mkdir(parents=True)
(CAD := ROOT/'cad'/'attachment_interface_v0_1').mkdir(parents=True)
(DOCS := ROOT/'docs').mkdir(parents=True)
(DOCS/'print_notes').mkdir(parents=True)

# Coordinate convention: x=left/right, y=front/rear, z=up (mm)
# Nominal chassis for 20 cm class rover. Attachments fixed at four ports.
PORT_X = 70
FRONT_Y = 230
REAR_Y = -230
PORT_Z = 65
BODY_W = 200
BODY_L = 420
BODY_H = 34


def box(size, center, name=None):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    if name:
        m.metadata['name'] = name
    return m

def cyl(radius, depth, center, axis='z', sections=32, name=None):
    m = trimesh.creation.cylinder(radius=radius, height=depth, sections=sections)
    # cylinder height along z by default, rotate if needed
    if axis == 'x':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0,1,0]))
    elif axis == 'y':
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1,0,0]))
    m.apply_translation(center)
    if name:
        m.metadata['name'] = name
    return m

def combine(meshes):
    return trimesh.util.concatenate([m for m in meshes if m is not None])

def export(mesh, filename):
    mesh.export(str(STL/filename))

# Bracket/port: printable visual U-bracket with locating bosses, no boolean holes.
def port_block(x, y, z=PORT_Z, front=True):
    # mounting port block faces outwards along y. It is not a final load-rated bracket.
    sign = 1 if front else -1
    meshes = []
    # back plate
    meshes.append(box((44, 10, 50), (x, y, z), 'port_back_plate'))
    # top and bottom lips
    meshes.append(box((54, 18, 8), (x, y + sign*6, z+24), 'port_top_lip'))
    meshes.append(box((54, 18, 8), (x, y + sign*6, z-24), 'port_bottom_lip'))
    # side keys
    meshes.append(box((8, 18, 46), (x-27, y+sign*6, z), 'port_side_key_l'))
    meshes.append(box((8, 18, 46), (x+27, y+sign*6, z), 'port_side_key_r'))
    # fake locating pins / washers as cylinders on outside face
    meshes.append(cyl(4.5, 6, (x-14, y+sign*14, z+12), axis='y', sections=24))
    meshes.append(cyl(4.5, 6, (x+14, y+sign*14, z+12), axis='y', sections=24))
    meshes.append(cyl(4.5, 6, (x-14, y+sign*14, z-12), axis='y', sections=24))
    meshes.append(cyl(4.5, 6, (x+14, y+sign*14, z-12), axis='y', sections=24))
    return combine(meshes)

# wheel visual cylinder oriented along x
def wheel(x, y):
    meshes=[]
    meshes.append(cyl(36, 30, (x, y, 32), axis='x', sections=48))
    # hub faces
    meshes.append(cyl(17, 34, (x, y, 32), axis='x', sections=32))
    return combine(meshes)

# float visual: long side float blocks/rounded impression via boxes + cylinders
def side_float(x):
    meshes=[]
    meshes.append(box((35, 350, 34), (x, 0, 28)))
    meshes.append(cyl(17, 350, (x, 0, 45), axis='y', sections=24))
    return combine(meshes)

# Chassis with four fixed ports, belly rail and floats.
def chassis_v05():
    meshes=[]
    # central low platform
    meshes.append(box((BODY_W, BODY_L, BODY_H), (0,0,30)))
    meshes.append(box((180, 310, 22), (0,0,62)))  # low protective cover
    meshes.append(box((90, 130, 32), (0,0,88)))   # dry cassette dummy visible under cover line
    # central belly rail & weeding rail placeholder
    meshes.append(box((80, 310, 10), (0,0,8)))
    meshes.append(box((25, 310, 10), (-55,0,9)))
    meshes.append(box((25, 310, 10), (55,0,9)))
    # side floats and wheels
    meshes.append(side_float(-130)); meshes.append(side_float(130))
    for x in (-105,105):
        for y in (-145,145):
            meshes.append(wheel(x,y))
    # four interface ports
    for x in (-PORT_X, PORT_X):
        meshes.append(port_block(x, FRONT_Y, front=True))
        meshes.append(port_block(x, REAR_Y, front=False))
    # PTO guide shafts (visual/printed mock)
    meshes.append(cyl(4, BODY_W+20, (0, FRONT_Y-25, PORT_Z), axis='x', sections=16))
    meshes.append(cyl(4, BODY_W+20, (0, REAR_Y+25, PORT_Z), axis='x', sections=16))
    # charge scute plate
    meshes.append(box((70, 80, 4), (0, 35, 76)))
    return combine(meshes)

# Interface gauge separate: lighter reference plate to verify port geometry.
def interface_gauge():
    meshes=[]
    meshes.append(box((BODY_W+80, BODY_L+110, 5), (0,0,2.5)))
    meshes.append(box((4, BODY_L+110, 10), (0,0,8))) # centerline rib
    meshes.append(box((BODY_W+80, 4, 10), (0,0,8))) # lateral reference line
    for x in (-PORT_X, PORT_X):
        meshes.append(port_block(x, FRONT_Y, front=True))
        meshes.append(port_block(x, REAR_Y, front=False))
    # x/y reference markers at port centers
    for x in (-PORT_X, PORT_X):
        meshes.append(cyl(3, 16, (x, FRONT_Y, 35), axis='z'))
        meshes.append(cyl(3, 16, (x, REAR_Y, 35), axis='z'))
    return combine(meshes)

# Simple adapter plug to fill an unused port
def port_plug():
    meshes=[]
    meshes.append(box((42, 20, 42), (0,0,0)))
    meshes.append(box((58, 8, 58), (0,14,0)))
    meshes.append(cyl(3.6, 12, (-14,20,12), axis='y', sections=16))
    meshes.append(cyl(3.6, 12, (14,20,12), axis='y', sections=16))
    meshes.append(cyl(3.6, 12, (-14,20,-12), axis='y', sections=16))
    meshes.append(cyl(3.6, 12, (14,20,-12), axis='y', sections=16))
    return combine(meshes)

# Rear bridge using rear two ports.
def rear_bridge():
    meshes=[]
    # adapter plates align with rear port positions
    for x in (-PORT_X, PORT_X):
        meshes.append(port_block(x, 0, z=0, front=False))
    # long 3D printed bridge frame. Reference width about 300 mm; print split for real use.
    meshes.append(box((300, 22, 22), (0, -40, 0)))
    meshes.append(box((300, 18, 16), (0, -78, -14)))
    for x in (-100,0,100):
        meshes.append(box((55, 60, 12), (x, -92, -22))) # unit seat
        meshes.append(cyl(4, 18, (x-18, -92, -12), axis='z'))
        meshes.append(cyl(4, 18, (x+18, -92, -12), axis='z'))
    return combine(meshes)

# Front high cut bridge dummy/gauge. Not actual cutter.
def front_bridge_gauge():
    meshes=[]
    for x in (-PORT_X, PORT_X):
        meshes.append(port_block(x, 0, z=0, front=True))
    meshes.append(box((260, 22, 22), (0, 40, 0)))
    meshes.append(box((160, 16, 14), (0, 78, -10)))
    meshes.append(box((120, 8, 4), (0, 105, -24))) # height gauge lip
    return combine(meshes)

# Single direct seeding unit. Printed mock, no real metal required.
def single_ds_unit(x=0, y=0, z=0):
    meshes=[]
    # hopper open top bucket as solid-looking walls: bottom + four walls
    meshes.append(box((46, 36, 6), (x, y, z+55)))
    meshes.append(box((4, 40, 55), (x-25, y, z+82)))
    meshes.append(box((4, 40, 55), (x+25, y, z+82)))
    meshes.append(box((54, 4, 55), (x, y-22, z+82)))
    meshes.append(box((54, 4, 55), (x, y+22, z+82)))
    # metering box and roller
    meshes.append(box((50, 28, 22), (x, y-4, z+38)))
    meshes.append(cyl(9, 58, (x, y-4, z+38), axis='x', sections=24))
    # drop tube and opener
    meshes.append(box((12, 14, 52), (x, y-8, z+5)))
    meshes.append(box((20, 38, 8), (x, y-14, z-22)))  # micro skid
    # shallow opener wedge represented by tilted-ish two boxes
    opener = box((9, 36, 32), (x, y-28, z-12))
    opener.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-12), [1,0,0], point=[x,y-28,z-12]))
    meshes.append(opener)
    # soil gentle flap
    flap = box((30, 5, 22), (x, y+18, z-14))
    flap.apply_transform(trimesh.transformations.rotation_matrix(math.radians(15), [1,0,0], point=[x,y+18,z-14]))
    meshes.append(flap)
    return combine(meshes)

# Hopper extension wall: stackable open wall, no lid.
def hopper_extension(height=60):
    meshes=[]
    z=height/2
    meshes.append(box((4, 42, height), (-25,0,z)))
    meshes.append(box((4, 42, height), (25,0,z)))
    meshes.append(box((54, 4, height), (0,-23,z)))
    meshes.append(box((54, 4, height), (0,23,z)))
    # lower lip / joint ridge
    meshes.append(box((62, 48, 5), (0,0,2.5)))
    # upper locator nubs
    meshes.append(cyl(3, 6, (-17,-15,height+3), axis='z', sections=12))
    meshes.append(cyl(3, 6, (17,-15,height+3), axis='z', sections=12))
    meshes.append(cyl(3, 6, (-17,15,height+3), axis='z', sections=12))
    meshes.append(cyl(3, 6, (17,15,height+3), axis='z', sections=12))
    return combine(meshes)

# Three DS unit complete, uses rear bridge and PTO drive.
def three_ds_rear_module():
    meshes=[]
    meshes.append(rear_bridge())
    # move single units down relative to bridge
    for x in (-100,0,100):
        meshes.append(single_ds_unit(x, -110, 0))
    # printed PTO drivetrain: shaft + pulleys/gears to each unit
    meshes.append(cyl(4, 280, (0, -55, 12), axis='x', sections=16))
    for x in (-100,0,100):
        meshes.append(cyl(16, 10, (x, -55, 12), axis='x', sections=24))
        meshes.append(cyl(12, 10, (x, -98, 32), axis='x', sections=24))
        meshes.append(box((6, 45, 4), (x, -76, 22))) # belt/chain visual
    return combine(meshes)

# printed hardware mock set
def hardware_dummy():
    meshes=[]
    # M3/M4 bolt dummies
    for i,x in enumerate(np.linspace(-60,60,7)):
        meshes.append(cyl(3, 22, (x,0,12), axis='z', sections=16))
        meshes.append(cyl(5.2, 3, (x,0,24.5), axis='z', sections=6))
    # shafts
    for y in (30,50):
        meshes.append(cyl(3, 120, (0,y,6), axis='x', sections=16))
    # clip pins
    for x in (-40,0,40):
        meshes.append(cyl(2.2, 25, (x,80,8), axis='x', sections=12))
        meshes.append(cyl(7, 2, (x-14,80,8), axis='x', sections=16))
    # spring as stack of small torus? Use cylinder rings visual with coils boxes
    for i in range(6):
        meshes.append(cyl(5, 2, (-70, 80, i*5), axis='z', sections=16))
    return combine(meshes)

# Rear assembly on chassis: translate module to rear port locations on chassis.
def assembly_chassis_rear_ds():
    meshes=[]
    meshes.append(chassis_v05())
    ds = three_ds_rear_module()
    # align bridge port blocks at rear port y REAR_Y. local bridge port y=0 -> rear_y, z=PORT_Z, and faces rear
    ds.apply_translation((0, REAR_Y, PORT_Z))
    meshes.append(ds)
    # Add front bridge gauge to show front ports reserved for high-cut/camera work
    fg = front_bridge_gauge(); fg.apply_translation((0, FRONT_Y, PORT_Z)); meshes.append(fg)
    return combine(meshes)

# Export parts
parts = {
    'PSR-AIF-001-R00_attachment_interface_gauge_four_fixed_ports.stl': interface_gauge(),
    'PSR-AIF-010-R00_unused_port_plug_printable_dummy.stl': port_plug(),
    'PSR-WP-201-R00_base_chassis_four_port_interface_v0_5.stl': chassis_v05(),
    'PSR-WP-202-R00_front_high_cut_interface_bridge_gauge.stl': front_bridge_gauge(),
    'PSR-WP-203-R00_rear_direct_seeding_interface_bridge.stl': rear_bridge(),
    'PSR-DS-401-R00_single_direct_seeding_unit_printable_mock.stl': single_ds_unit(),
    'PSR-DS-402-R00_three_unit_direct_seeding_rear_module_reference.stl': three_ds_rear_module(),
    'PSR-DS-403-R00_hopper_extension_wall_plus60_no_lid.stl': hopper_extension(60),
    'PSR-DS-404-R00_hopper_extension_wall_plus100_no_lid.stl': hopper_extension(100),
    'PSR-DS-405-R00_printed_pto_drive_train_rear_3unit_dummy.stl': combine([cyl(4,280,(0,0,0),axis='x'), *[cyl(16,10,(x,0,0),axis='x') for x in (-100,0,100)], *[box((6,45,4),(x,-25,10)) for x in (-100,0,100)]]),
    'PSR-DS-406-R00_printable_hardware_dummy_set.stl': hardware_dummy(),
    'PSR-ASM-401-R00_chassis_v0_5_with_rear_ds_and_front_interface_reference.stl': assembly_chassis_rear_ds(),
}
for fn, mesh in parts.items():
    export(mesh, fn)

# Write generator script into CAD folder (copy self with simplified text)
script_text = Path('/mnt/data/create_attachment_interface_v0_1.py').read_text()
(CAD/'generate_attachment_interface_v0_1.py').write_text(script_text, encoding='utf-8')

# Docs
readme = """# Paddy Swarm Attachment Interface CAD v0.1

This package introduces the **Paddy Swarm Attachment Interface Standard v0.1**.

Purpose:
- Keep the rover body upgradable while keeping attachment locations fixed.
- Move direct seeding / planting-style modules to the **rear** so the rover wheels do not run over freshly placed germinated seed.
- Reserve the **front** attachment ports for high-cut harvest, camera-linked work, and operations that need visual confirmation.
- Keep belly weeding as a central underbody module.

Important: this is a **Grade 0 / mock-up CAD pack**. Shafts, pins, bushings and springs are included as 3D-printable dummy parts so a physical model can be assembled cheaply. Field-use versions may need metal shafts, bearings, bushings, springs, seals, and stronger hardware.

## Fixed interface concept

Coordinate convention:
- X: left/right
- Y: front/rear
- Z: up/down
- Body center is the origin.

Nominal fixed positions:
- Front-left port: X=-70 mm, Y=+230 mm
- Front-right port: X=+70 mm, Y=+230 mm
- Rear-left port: X=-70 mm, Y=-230 mm
- Rear-right port: X=+70 mm, Y=-230 mm
- Nominal port height: Z=65 mm

These values are the v0.1 interface reference. Future rover chassis updates should preserve these port positions or provide adapter plates.

## Attachment allocation rule

- Front two ports: high-cut harvest, camera-linked tools, inspection tools.
- Rear two ports: direct seeding, planting, replanting modules.
- Belly rail: underbody weeding modules.
- Side mounts: floats, guards, recovery aids.

## Included update

- Base chassis v0.5 with four fixed ports.
- Rear-mounted 3-unit direct seeding mock-up using the rear-left and rear-right ports.
- Front high-cut interface bridge gauge, not an actual cutter.
- 3D-printed dummy shafts, pins, springs and fasteners for low-cost model assembly.
- Stackable hopper extension walls with no lid, assuming wet germinated seed and non-rain-avoidance operation.

## Notes

The direct seeding module here is intentionally placed at the rear. It is meant to place germinated seed after the wheels pass, closer to the logic of a transplanter. The module includes a light skid/opener concept for shallow placement and wheel-track correction, but actual seed depth must be validated in tray and mud tests.
"""
(ROOT/'README_attachment_interface_v0_1.md').write_text(readme, encoding='utf-8')

std_doc = """# Paddy Swarm Attachment Interface Standard v0.1

## Core decision

The rover body should have four fixed attachment positions:

1. Front Left
2. Front Right
3. Rear Left
4. Rear Right

These positions should remain fixed across body revisions. If a future body changes shape, it should provide adapter plates rather than moving the attachment interface.

## Why this standard is needed

Without a fixed interface, each chassis version and attachment version can become incompatible. A fixed interface allows:

- Old attachments to fit newer bodies.
- New attachments to fit older bodies through adapters.
- Community-made modules to share the same mounting assumptions.
- CAD updates without destroying kit compatibility.
- Field repair by swapping only the module that failed.

## Work allocation

### Front ports

Recommended for:
- High-cut harvest arm
- Camera-guided operations
- Head / panicle guide tools
- Inspection and scout tools

Reason: the front camera can see the tool and the crop before the rover body touches it.

### Rear ports

Recommended for:
- Direct seeding with germinated seed
- Planting / replanting modules
- Light post-wheel soil settling tools

Reason: wheels pass first, then seed or seedlings are placed. This avoids running over freshly placed seed.

### Belly rail

Recommended for:
- Weeding stirrer
- Shallow mud agitation
- Underbody low-force work modules

Reason: forces are near the rover center of mass and easier to manage.

## Nominal v0.1 port coordinates

- Front-left:  X=-70 mm, Y=+230 mm, Z=65 mm
- Front-right: X=+70 mm, Y=+230 mm, Z=65 mm
- Rear-left:   X=-70 mm, Y=-230 mm, Z=65 mm
- Rear-right:  X=+70 mm, Y=-230 mm, Z=65 mm

These are reference dimensions for CAD alignment. They are not yet field-qualified mechanical load specifications.

## PTO policy

The v0.1 standard fixes the physical port positions first. PTO drive routing remains a mock-up in this release.

Planned direction:
- Left/right motor systems may feed left/right PTO paths.
- Rear direct seeding can be driven by a rear transverse shaft.
- Front high-cut harvest can use a front bridge shaft or dedicated actuator.
- If the PTO geometry changes later, adapter gearboxes should be used rather than moving the attachment ports.

## Safety

Do not test direct seeding in a production field before tray tests, mud tests and recovery planning. Real field versions may need metal shafts, bushings, bearings, seals, emergency stops and guarded pinch points.
"""
(DOCS/'attachment_interface_standard_v0_1.md').write_text(std_doc, encoding='utf-8')

update_doc = """# CAD Update Notes: v0.4 / DS v0.1 Reorganization

This update reorganizes the prior weeding-platform body and direct-seeding module around the new attachment standard.

## Changes

- Direct seeding moves from a front concept to a rear-mounted concept.
- Front ports are reserved for high-cut harvest and camera-visible tools.
- Base chassis is updated to a four-fixed-port reference body: `PSR-WP-201`.
- A rear direct-seeding bridge is added: `PSR-WP-203`.
- A rear 3-unit direct seeding module is added: `PSR-DS-402`.
- A front high-cut interface gauge is included only as a position reference: `PSR-WP-202`.

## Why direct seeding moved rearward

If germinated seed is placed in front of the rover, the wheels can press or drag the seed immediately after placement. Rear placement follows the same logic as rice transplanters: the traveling body passes first, then the seed/planting module places material behind it.

## Why high-cut moved forward

High-cut work needs visual confirmation of panicle position, height, lodging and obstruction. The front is better for camera-guided work and hand-like operations.

## Printing note

Reference assemblies are not recommended as one-piece prints. Print interface gauges and individual modules first.
"""
(DOCS/'cad_update_notes_v0_1.md').write_text(update_doc, encoding='utf-8')

repo_push = """# Repo push commands

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_attachment_interface_cad_v0_1.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add attachment interface standard and rear direct seeding CAD v0.1"
git push
```
"""
(DOCS/'repo_push_attachment_interface_v0_1.md').write_text(repo_push, encoding='utf-8')

print_notes = """# Print Notes: PSR-AIF / PSR-DS R00

Recommended first prints:

1. `PSR-AIF-001-R00_attachment_interface_gauge_four_fixed_ports.stl`
2. `PSR-AIF-010-R00_unused_port_plug_printable_dummy.stl`
3. `PSR-WP-203-R00_rear_direct_seeding_interface_bridge.stl`
4. `PSR-DS-401-R00_single_direct_seeding_unit_printable_mock.stl`
5. `PSR-DS-403-R00_hopper_extension_wall_plus60_no_lid.stl`
6. `PSR-DS-405-R00_printed_pto_drive_train_rear_3unit_dummy.stl`

Use PLA for fit checks. Use PETG only after fit is confirmed. TPU may be useful for later soft seed guides and mud-contact skids.

All shafts, pins, springs and fasteners in this pack are dummy printable geometry. They are for model assembly and motion layout review only.
"""
(DOCS/'print_notes'/'PSR-AIF-DS-R00.md').write_text(print_notes, encoding='utf-8')

# CSV manifests
manifest_rows = [
    ['part_id','filename','category','material_hint','print_role','notes'],
]
for fn in parts.keys():
    part_id = fn.split('_R00')[0].replace('-R00','')
    cat = 'reference_assembly' if 'ASM' in fn or 'reference' in fn else ('interface' if 'AIF' in fn else ('chassis' if 'WP' in fn else 'direct_seeding'))
    mat = 'PLA first; PETG after fit; dummy shafts may later become metal'
    role = 'reference_only_do_not_print_one_piece' if cat=='reference_assembly' else 'printable_mock'
    notes = 'rear direct seeding / four fixed port standard' if 'DS' in fn or 'AIF' in fn else 'body/interface reference'
    manifest_rows.append([part_id, f'stl/attachment_interface_v0_1/{fn}', cat, mat, role, notes])
with open(ROOT/'print_manifest_attachment_interface_v0_1.csv','w',newline='',encoding='utf-8') as f:
    csv.writer(f).writerows(manifest_rows)

kit_rows = [
    ['kit_id','kit_name','included_parts','purpose'],
    ['PSR-AIF-KIT-001','Four Fixed Port Interface Gauge','PSR-AIF-001, PSR-AIF-010','Validate the four attachment locations before updating body or attachments.'],
    ['PSR-WP-KIT-201','Base Chassis Four-Port v0.5','PSR-WP-201, PSR-AIF-010','Body reference with front/rear left/right attachment ports.'],
    ['PSR-DS-KIT-401','Rear 3-Unit Direct Seeding Mock-up','PSR-WP-203, PSR-DS-401, PSR-DS-402, PSR-DS-403, PSR-DS-404, PSR-DS-405','Rear-mounted direct seeding module for germinated seed, 3 units at 100 mm pitch.'],
    ['PSR-HC-KIT-202','Front High-Cut Interface Gauge','PSR-WP-202','Front-port position gauge for future high-cut camera-linked arm.'],
]
with open(ROOT/'kit_index_attachment_interface_v0_1.csv','w',newline='',encoding='utf-8') as f:
    csv.writer(f).writerows(kit_rows)

# Render preview via matplotlib
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    mesh = parts['PSR-ASM-401-R00_chassis_v0_5_with_rear_ds_and_front_interface_reference.stl']
    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(111, projection='3d')
    faces = mesh.vertices[mesh.faces]
    poly = Poly3DCollection(faces, linewidths=0.02, alpha=0.88)
    poly.set_facecolor((0.32,0.34,0.29,0.92))
    poly.set_edgecolor((0.05,0.05,0.05,0.15))
    ax.add_collection3d(poly)
    mins, maxs = mesh.bounds
    center = (mins+maxs)/2
    rng = (maxs-mins).max()/2
    ax.set_xlim(center[0]-rng, center[0]+rng)
    ax.set_ylim(center[1]-rng, center[1]+rng)
    ax.set_zlim(0, center[2]+rng*0.9)
    ax.view_init(elev=24, azim=-55)
    ax.set_xlabel('X left/right mm')
    ax.set_ylabel('Y front/rear mm')
    ax.set_zlabel('Z up mm')
    ax.set_title('Paddy Swarm AIF v0.1 / Chassis v0.5 / Rear Direct Seeding v0.2')
    plt.tight_layout()
    fig.savefig(ROOT/'paddy_swarm_attachment_interface_v0_1_render.png', dpi=180)
    plt.close(fig)
except Exception as e:
    (ROOT/'render_error.txt').write_text(str(e), encoding='utf-8')

# Zip it
zip_path = Path('/mnt/data/paddy_swarm_attachment_interface_cad_v0_1.zip')
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        z.write(p, p.relative_to(ROOT.parent))

print(zip_path)
print('files', len(list(ROOT.rglob('*'))))
