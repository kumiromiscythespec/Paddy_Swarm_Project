import os, json, csv, math, shutil, zipfile
from pathlib import Path
import numpy as np
import trimesh
from trimesh.transformations import translation_matrix

ROOT = Path('/mnt/data/paddy_swarm_amphibious_hull_cad_v0_1')
if ROOT.exists():
    shutil.rmtree(ROOT)
for d in ['cad/hull_v0_1','stl/hull_v0_1','docs/print_notes','docs','images/concept','experiments/float_test']:
    (ROOT/d).mkdir(parents=True, exist_ok=True)

STL_DIR = ROOT/'stl/hull_v0_1'
CAD_DIR = ROOT/'cad/hull_v0_1'

parts = []

def box(name, extents, center):
    m = trimesh.creation.box(extents=extents)
    m.apply_transform(translation_matrix(center))
    return m

def export_mesh(meshes, filename, part_no, title, material='PLA/PETG', print_note='', quantity=1):
    if not isinstance(meshes, (list, tuple)):
        meshes=[meshes]
    mesh = trimesh.util.concatenate(meshes)
    # STL units are mm; no unit metadata in STL.
    path = STL_DIR/filename
    mesh.export(path)
    bounds = mesh.bounds
    dims = bounds[1]-bounds[0]
    parts.append({
        'part_no': part_no,
        'filename': filename,
        'title': title,
        'quantity': quantity,
        'material': material,
        'size_x_mm': round(float(dims[0]),2),
        'size_y_mm': round(float(dims[1]),2),
        'size_z_mm': round(float(dims[2]),2),
        'print_note': print_note
    })
    return path

# Common functions

def waterline_strips(L, W, H, side='outer_left', x_offset=0):
    # raised bands on one long wall, at three heights.
    meshes=[]
    y = -W/2 - 0.8 if side == 'outer_left' else W/2 + 0.8
    # length, thickness, height. Use very shallow raised bars.
    for z, label in [(H*0.40,'safe'),(H*0.58,'warning'),(H*0.75,'danger')]:
        meshes.append(box(f'waterline_{label}', [L-12, 1.2, 1.8], [x_offset, y, z]))
    return meshes

def make_float_tray(L=165, W=50, H=80, wall=3, bottom=4, side='left', segment='mid'):
    meshes=[]
    # bottom and walls
    meshes.append(box('bottom', [L, W, bottom], [0,0,bottom/2]))
    meshes.append(box('wall_left', [L, wall, H], [0, -W/2+wall/2, H/2]))
    meshes.append(box('wall_right', [L, wall, H], [0, W/2-wall/2, H/2]))
    meshes.append(box('wall_front', [wall, W, H], [-L/2+wall/2, 0, H/2]))
    meshes.append(box('wall_back', [wall, W, H], [L/2-wall/2, 0, H/2]))
    # internal baffles, lower than top so lid sits over them
    for bx in [-L/6, L/6]:
        meshes.append(box('baffle', [wall, W-2*wall, H-10], [bx, 0, (H-10)/2 + bottom]))
    # foam retaining ledges at inner top (tiny rails)
    meshes.append(box('top_lip_left', [L-6, 2, 4], [0, -W/2+wall+1, H-4]))
    meshes.append(box('top_lip_right', [L-6, 2, 4], [0, W/2-wall-1, H-4]))
    # seam alignment pads outside ends
    meshes.append(box('seam_pad_front', [8, W+6, 5], [-L/2+4,0,H+2.5]))
    meshes.append(box('seam_pad_back', [8, W+6, 5], [L/2-4,0,H+2.5]))
    # waterline strips on outer side; for left float, outer is y=-, right float outer is y=+
    meshes += waterline_strips(L, W, H, side='outer_left' if side=='left' else 'outer_right')
    # a small segment code block (no readable text, just different bar counts)
    nbar = {'front':1, 'mid':2, 'rear':3}.get(segment,2)
    for i in range(nbar):
        meshes.append(box('segment_marker', [18, 1.2, 2], [-L/2+15+i*12, (-W/2-1.4 if side=='left' else W/2+1.4), H-8]))
    return meshes

def make_float_lid(L=165, W=50, plate=3, lip=6, wall=2, tol=0.8):
    meshes=[]
    # top plate overhangs a little; inner lips fit into tray.
    meshes.append(box('top_plate', [L, W, plate], [0,0,plate/2]))
    innerL=L-2*3-tol
    innerW=W-2*3-tol
    z = -lip/2
    meshes.append(box('inner_lip_left', [innerL, wall, lip], [0, -innerW/2+wall/2, z]))
    meshes.append(box('inner_lip_right', [innerL, wall, lip], [0, innerW/2-wall/2, z]))
    meshes.append(box('inner_lip_front', [wall, innerW, lip], [-innerL/2+wall/2, 0, z]))
    meshes.append(box('inner_lip_back', [wall, innerW, lip], [innerL/2-wall/2, 0, z]))
    # shallow raised center ribs for stiffness
    meshes.append(box('rib_long', [L-20, 2, 2], [0,0,plate+1]))
    meshes.append(box('rib_cross', [2, W-12, 2], [0,0,plate+1]))
    return meshes

def make_seam_joiner_clip(L=60, outerW=58, gapW=52, top=4, sideH=14, sideT=3):
    meshes=[]
    # U clip straddles two neighboring segment top pads / sides.
    meshes.append(box('clip_top', [L, outerW, top], [0,0,sideH + top/2]))
    meshes.append(box('clip_side_l', [L, sideT, sideH], [0,-outerW/2+sideT/2,sideH/2]))
    meshes.append(box('clip_side_r', [L, sideT, sideH], [0,outerW/2-sideT/2,sideH/2]))
    # center ridge to show seam line
    meshes.append(box('seam_ridge', [2, outerW, 2], [0,0,sideH+top+1]))
    return meshes

def make_central_hull_frame(L=240, W=116, base=8):
    meshes=[]
    # base deck
    meshes.append(box('base', [L,W,base], [0,0,base/2]))
    # side rails to align with floats
    railH=16; railW=6
    meshes.append(box('left_side_rail', [L,railW,railH], [0,-W/2+railW/2,base+railH/2]))
    meshes.append(box('right_side_rail', [L,railW,railH], [0,W/2-railW/2,base+railH/2]))
    # waterproof box cradle rails
    cradleL=170; cradleW=78; cradleH=18; rW=6
    meshes.append(box('cradle_left_rail', [cradleL,rW,cradleH], [0,-cradleW/2,base+cradleH/2]))
    meshes.append(box('cradle_right_rail', [cradleL,rW,cradleH], [0,cradleW/2,base+cradleH/2]))
    meshes.append(box('cradle_front_stop', [8,cradleW+10,cradleH], [-cradleL/2,0,base+cradleH/2]))
    meshes.append(box('cradle_back_stop', [8,cradleW+10,cradleH], [cradleL/2,0,base+cradleH/2]))
    # belly module rails on underside (represented as bottom ribs)
    meshes.append(box('belly_rail_l', [L-40,5,8], [0,-22,-4]))
    meshes.append(box('belly_rail_r', [L-40,5,8], [0,22,-4]))
    # CG cross mark raised on top
    meshes.append(box('cg_x', [62,2,1.5], [0,0,base+cradleH+1]))
    meshes.append(box('cg_y', [2,62,1.5], [0,0,base+cradleH+1]))
    # battery low tray ledges
    meshes.append(box('battery_lip_l', [90,4,8], [0,-18,base+5]))
    meshes.append(box('battery_lip_r', [90,4,8], [0,18,base+5]))
    return meshes

def make_waterproof_box_dummy(L=140,W=80,H=55, wall=3):
    # not waterproof, a visual dummy; open bottom shell with lid seam.
    meshes=[]
    meshes.append(box('box_body', [L,W,H], [0,0,H/2]))
    # draw top lid seam as raised rim
    meshes.append(box('lid_rim_front',[L,2,2],[0,-W/2-1,H+1]))
    meshes.append(box('lid_rim_back',[L,2,2],[0,W/2+1,H+1]))
    meshes.append(box('lid_rim_left',[2,W,2],[-L/2-1,0,H+1]))
    meshes.append(box('lid_rim_right',[2,W,2],[L/2+1,0,H+1]))
    # cable ports on top as dummy raised glands (not real holes)
    meshes.append(box('cable_gland_1',[16,12,5],[-30,0,H+4]))
    meshes.append(box('cable_gland_2',[16,12,5],[30,0,H+4]))
    return meshes

def make_ballast_tray(L=150,W=70,H=18, wall=3, bottom=3):
    meshes=[]
    meshes.append(box('bottom',[L,W,bottom],[0,0,bottom/2]))
    meshes.append(box('wall_l',[L,wall,H],[0,-W/2+wall/2,H/2]))
    meshes.append(box('wall_r',[L,wall,H],[0,W/2-wall/2,H/2]))
    meshes.append(box('wall_f',[wall,W,H],[-L/2+wall/2,0,H/2]))
    meshes.append(box('wall_b',[wall,W,H],[L/2-wall/2,0,H/2]))
    # divider slots for weights
    for x in [-40,0,40]:
        meshes.append(box('divider',[2,W-2*wall,H-4],[x,0,H/2]))
    # small center mark
    meshes.append(box('center_mark_x',[50,1.5,1.5],[0,0,H+1]))
    meshes.append(box('center_mark_y',[1.5,40,1.5],[0,0,H+1]))
    return meshes

def make_belly_module_rail_sample(L=140,W=80,H=20):
    meshes=[]
    meshes.append(box('module_plate',[L,W,4],[0,0,2]))
    meshes.append(box('left_tongue',[L-20,8,8],[0,-W/2+10,8]))
    meshes.append(box('right_tongue',[L-20,8,8],[0,W/2-10,8]))
    meshes.append(box('wedge_lock_tab',[18,16,10],[L/2-20,0,11]))
    return meshes

def make_bow_mud_deflector(L=120,W=115,H=35):
    # Simple sloped deflector triangular prism-like, implemented as a rectangular base plus ramp plates approximated by boxes.
    meshes=[]
    meshes.append(box('base',[L,W,4],[0,0,2]))
    # stepped ramp: easy to print, no support; represents mud deflector concept
    for i in range(5):
        stepL=L - i*18
        stepH=4
        x=-L/2 + stepL/2 + i*9
        z=4 + i*6
        meshes.append(box(f'ramp_step_{i}', [stepL,W,stepH], [x,0,z]))
    # side cheeks
    meshes.append(box('side_l',[L,3,H],[0,-W/2+1.5,H/2]))
    meshes.append(box('side_r',[L,3,H],[0,W/2-1.5,H/2]))
    return meshes

# Export parts. Use distinct left/right segment files for repo clarity; geometry mirrored only by waterline side and marker.
segments = [('front','002'),('mid','003'),('rear','004')]
for segment, num in segments:
    export_mesh(make_float_tray(side='left', segment=segment), f'PSR-HU-{num}-R00_left_float_{segment}_tray.stl', f'PSR-HU-{num}-R00', f'Left float {segment} open tray', material='PETG recommended', print_note='Open-top float tray; add foam and seal for water testing; print upright; brim recommended.')
segments_r = [('front','005'),('mid','006'),('rear','007')]
for segment, num in segments_r:
    export_mesh(make_float_tray(side='right', segment=segment), f'PSR-HU-{num}-R00_right_float_{segment}_tray.stl', f'PSR-HU-{num}-R00', f'Right float {segment} open tray', material='PETG recommended', print_note='Open-top float tray; add foam and seal for water testing; print upright; brim recommended.')

export_mesh(make_central_hull_frame(), 'PSR-HU-001-R00_central_hull_short_frame.stl', 'PSR-HU-001-R00', 'Central hull short frame with cradle and belly rails', 'PLA first, PETG later', 'Print flat on bed; no support expected.')
export_mesh(make_bow_mud_deflector(), 'PSR-HU-008-R00_bow_mud_deflector_step_ramp.stl', 'PSR-HU-008-R00', 'Stepped bow mud deflector concept', 'PLA/PETG', 'Concept part; print flat; not a structural part.')
export_mesh(make_waterproof_box_dummy(), 'PSR-HU-010-R00_waterproof_box_dummy.stl', 'PSR-HU-010-R00', 'Waterproof box placement dummy', 'PLA', 'Visual/dummy only; not waterproof.')
export_mesh(make_ballast_tray(), 'PSR-HU-013-R00_ballast_test_tray.stl', 'PSR-HU-013-R00', 'Ballast test tray for weight placement', 'PLA/PETG', 'Use tape/zip ties to secure weights during water tests.')
export_mesh(make_float_lid(), 'PSR-HU-015-R00_float_segment_lid_generic.stl', 'PSR-HU-015-R00', 'Generic float segment lid', 'PETG recommended', 'One lid per float tray; seal with tape/silicone only for controlled water tests.', quantity=6)
export_mesh(make_seam_joiner_clip(), 'PSR-HU-016-R00_float_seam_joiner_clip.stl', 'PSR-HU-016-R00', 'Float seam joiner clip', 'PLA/PETG', 'Clip over seam between float segments; use with tape for water tests.', quantity=4)
export_mesh(make_belly_module_rail_sample(), 'PSR-HU-012-R00_belly_module_rail_sample.stl', 'PSR-HU-012-R00', 'Belly module rail sample', 'PLA/PETG', 'Sample rail/tongue for future module swap tests.')

# Save generator source in package
shutil.copy('/mnt/data/generate_hull_pack.py', CAD_DIR/'generate_amphibious_hull_v0_1.py')

# CSV manifests
with open(ROOT/'print_manifest.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f, fieldnames=['part_no','filename','title','quantity','material','size_x_mm','size_y_mm','size_z_mm','print_note'])
    writer.writeheader(); writer.writerows(parts)
with open(ROOT/'kit_index.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f)
    writer.writerow(['category','part_no','filename','description'])
    for p in parts:
        writer.writerow(['hull_v0_1', p['part_no'], 'stl/hull_v0_1/'+p['filename'], p['title']])

# Documentation files
readme = """# Paddy Swarm Amphibious Hull CAD Pack v0.1 / 水陸両用型ローバー船体CADパック

This pack adds the first printable CAD/STL set for the Paddy Swarm Amphibious Hull concept.

このパックは、Paddy Swarm Project の「水陸両用型ローバー船体 v0.1」をGrade 0試験用に3Dプリントできる形へ落としたものです。

## Important / 重要

These parts are **experimental Grade 0 parts**. They are not waterproof, not field-proven, and not a finished rover.

- Do not put electronics or batteries in water.
- Do not use these parts in a real paddy field first.
- Start with PLA fit checks, then PETG water-tank tests.
- Use foam inside float trays during water tests.
- Seal seams only for controlled tests using tape/silicone.
- If a paper towel placed in the waterproof-box position gets wet, the design fails the water-ingress test.

## Contents

- `stl/hull_v0_1/` — printable STL files
- `cad/hull_v0_1/generate_amphibious_hull_v0_1.py` — source generator used to create the STL files
- `docs/amphibious_hull_v0_1.md` — design notes and assembly concept
- `docs/print_notes/PSR-HU-R00.md` — print notes
- `print_manifest.csv` — part sizes and print notes
- `kit_index.csv` — repo index entries

## First print recommendation

Print in this order:

1. `PSR-HU-001-R00_central_hull_short_frame.stl` in PLA
2. `PSR-HU-013-R00_ballast_test_tray.stl` in PLA
3. One float tray, e.g. `PSR-HU-003-R00_left_float_mid_tray.stl`, in PLA
4. Same float tray in PETG
5. Float lid and seam joiner clips
6. Water-tank test with no electronics

## Repository merge

From the repo root:

```powershell
Expand-Archive -Path .\paddy_swarm_amphibious_hull_cad_v0_1.zip -DestinationPath . -Force
git add .
git commit -m "Add amphibious hull Grade 0 CAD pack v0.1"
git push
```
"""
(ROOT/'README_amphibious_hull_pack_v0_1.md').write_text(readme, encoding='utf-8')

design = """# docs/amphibious_hull_v0_1.md

# Paddy Swarm Amphibious Hull v0.1

## Purpose

This is the first Grade 0 CAD pack for the Paddy Swarm amphibious hull concept.

Design principle:

```text
Instead of attaching floats to a vehicle,
design a floating small hull and attach drive/working modules to it.
```

日本語で言えば、これは「車体にフロートを足す」のではなく、**浮く船体に足回りと作業アームを付ける**設計です。

## Target

- 30cm rice-row spacing awareness
- Narrow hull, around 220–240mm max concept width
- Left/right side floats as primary buoyancy
- Low center of gravity
- Open-top float trays for foam insertion and inspection
- No electronics during Grade 0 water tests

## Parts

| Part No. | Name |
|---|---|
| PSR-HU-001-R00 | Central hull short frame |
| PSR-HU-002-R00 | Left float front tray |
| PSR-HU-003-R00 | Left float mid tray |
| PSR-HU-004-R00 | Left float rear tray |
| PSR-HU-005-R00 | Right float front tray |
| PSR-HU-006-R00 | Right float mid tray |
| PSR-HU-007-R00 | Right float rear tray |
| PSR-HU-008-R00 | Bow mud deflector concept |
| PSR-HU-010-R00 | Waterproof box dummy |
| PSR-HU-012-R00 | Belly module rail sample |
| PSR-HU-013-R00 | Ballast test tray |
| PSR-HU-015-R00 | Generic float segment lid |
| PSR-HU-016-R00 | Float seam joiner clip |

## Float structure

Each float segment is an open tray with:

- bottom plate
- side walls
- internal baffles
- foam insertion space
- waterline raised bands
- lid part
- seam clips for multi-segment tests

This is not a sealed boat hull. It is a Grade 0 test structure.

## Buoyancy test concept

Use no electronics. Put foam inside trays, mount lids, temporarily seal seams with tape or silicone, then test in a water tank.

Minimum checks:

```text
normal posture
front-up 10 degrees
front-down 10 degrees
left tilt 10 degrees
right tilt 10 degrees
light rocking
paper towel at waterproof-box position
```

Pass condition:

```text
paper towel stays dry
waterline stays below danger area
no sudden sinking if one segment leaks
```

## Print notes

- PLA: fit test and visual test
- PETG: water-tank test parts
- TPU: not used in this pack
- Use brim for tall float trays
- Print float trays upright/open-side up
- Do not assume FDM parts are watertight

## Next iteration ideas

- Add readable embossed labels
- Improve seam connector geometry
- Add true dovetail keys
- Create scaled full assembly jig
- Add optional wide-test float
- Add side-charge cutout version
- Add watertight lid gasket channel
"""
(ROOT/'docs/amphibious_hull_v0_1.md').write_text(design, encoding='utf-8')

print_notes = """# docs/print_notes/PSR-HU-R00.md

# Print Notes: PSR-HU-R00 Amphibious Hull Parts

## Recommended first settings

```text
Material first test: PLA
Material water test: PETG
Nozzle: 0.4mm
Layer height: 0.20mm
Walls: 3–4
Infill: 15–25% for frame parts
Supports: none expected for most parts
Brim: recommended for tall float trays
Scale: 100%
Unit: mm
```

## Float trays

Print open side up. These are tall narrow parts, so brim is recommended.

Before water testing:

```text
1. Print one tray in PLA to check fit.
2. Print the same tray in PETG.
3. Insert foam.
4. Fit lid.
5. Use tape or silicone only for controlled tests.
6. Do not add electronics.
```

## Central hull short frame

Print flat on the bed. This is a fit/placement frame, not a final load-bearing chassis.

## Ballast test tray

Use for washers, fishing weights, bolts, or small steel plates. Secure weights with tape or zip ties during water tests.

## Waterproof box dummy

This is a dummy shape only. It is not waterproof and must not be used to hold electronics.

## Safety

If the paper towel at the waterproof-box position becomes wet during test, mark the test as failed and revise the hull.
"""
(ROOT/'docs/print_notes/PSR-HU-R00.md').write_text(print_notes, encoding='utf-8')

push_commands = """# docs/repo_push_amphibious_hull_pack.md

# How to add this CAD pack to the public repo

Put `paddy_swarm_amphibious_hull_cad_v0_1.zip` in your repo root, for example:

```text
C:\\Paddy_Swarm_Project
```

Then run PowerShell:

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_amphibious_hull_cad_v0_1.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add amphibious hull Grade 0 CAD pack v0.1"
git push
```

If the ZIP file itself appears in `git status`, do not commit the ZIP. Commit the extracted files only.
"""
(ROOT/'docs/repo_push_amphibious_hull_pack.md').write_text(push_commands, encoding='utf-8')

# Add a .gitkeep in empty-ish test folder
(ROOT/'experiments/float_test/.gitkeep').write_text('', encoding='utf-8')

# Make zip
zip_path = Path('/mnt/data/paddy_swarm_amphibious_hull_cad_v0_1.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(ROOT))

print(f'Created {zip_path}')
print('Files:')
for p in sorted(ROOT.rglob('*')):
    if p.is_file(): print(p.relative_to(ROOT))
