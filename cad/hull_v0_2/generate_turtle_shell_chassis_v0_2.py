from pathlib import Path
import math, csv, zipfile, shutil
import numpy as np
import trimesh

ROOT = Path('/mnt/data/paddy_swarm_turtle_shell_chassis_cad_v0_2')
STL = ROOT / 'stl' / 'hull_v0_2'
CAD = ROOT / 'cad' / 'hull_v0_2'
DOCS = ROOT / 'docs'
PN = DOCS / 'print_notes'
for d in [STL, CAD, DOCS, PN, ROOT/'experiments'/'shell_tilt_test']:
    d.mkdir(parents=True, exist_ok=True)

REV = 'R00'

def box(name, size, loc=(0,0,0)):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(loc)
    if name:
        m.metadata['name'] = name
    return m

def cyl(radius=5, height=5, loc=(0,0,0), sections=32):
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    m.apply_translation(loc)
    return m

def combine(meshes, name=None):
    meshes = [m for m in meshes if m is not None]
    c = trimesh.util.concatenate(meshes)
    if name: c.metadata['name'] = name
    return c

def export(mesh, filename):
    path = STL / filename
    mesh.export(path)
    return path

# Units: millimeters. Coordinate: X length, Y width, Z height.
# Full rover reference footprint ~500 L x 230 W. Printable segments stay <= 250 mm.
FULL_L = 500.0
SHELL_L = 480.0
SHELL_W = 170.0
SHELL_H = 54.0
SHELL_T = 3.0

def dome_segment(x_min, x_max, length=SHELL_L, width=SHELL_W, height=SHELL_H, thickness=SHELL_T, z0=78.0, nx=34, ny=26):
    """Create a thin turtle-shell-like arched cover segment.
    Segment is derived from a full ellipsoidal roof, split along X.
    Open bottom, closed side/end walls, plus printable flanges.
    """
    xs = np.linspace(x_min, x_max, nx)
    ys = np.linspace(-width/2, width/2, ny)
    verts=[]
    # outer
    for x in xs:
        gx = x/(length/2)
        lx = max(0.0, 1.0-gx*gx)
        for y in ys:
            gy = y/(width/2)
            ly = max(0.0, 1.0-gy*gy)
            z = z0 + height * (lx**0.42) * (ly**0.50)
            verts.append([x,y,z])
    # inner shifted downward, slightly narrowed in Y for simple thickness. Keep same x grid.
    for x in xs:
        gx = x/(length/2)
        lx = max(0.0, 1.0-gx*gx)
        for y in ys:
            yy = y * ((width-2*thickness)/width)
            gy = yy/((width-2*thickness)/2)
            ly = max(0.0, 1.0-gy*gy)
            z = z0 + max(0.0, height * (lx**0.42) * (ly**0.50) - thickness)
            verts.append([x,yy,z])
    faces=[]
    def idx(i,j,inner=False):
        return (nx*ny if inner else 0) + i*ny+j
    for i in range(nx-1):
        for j in range(ny-1):
            faces.append([idx(i,j), idx(i+1,j), idx(i+1,j+1)])
            faces.append([idx(i,j), idx(i+1,j+1), idx(i,j+1)])
            # inner reverse
            faces.append([idx(i,j,True), idx(i+1,j+1,True), idx(i+1,j,True)])
            faces.append([idx(i,j,True), idx(i,j+1,True), idx(i+1,j+1,True)])
    # connect boundary surfaces
    # y min/max sides
    for i in range(nx-1):
        for j in [0, ny-1]:
            faces.append([idx(i,j), idx(i+1,j), idx(i+1,j,True)])
            faces.append([idx(i,j), idx(i+1,j,True), idx(i,j,True)])
    # x min/x max ends
    for i in [0, nx-1]:
        for j in range(ny-1):
            faces.append([idx(i,j), idx(i,j+1), idx(i,j+1,True)])
            faces.append([idx(i,j), idx(i,j+1,True), idx(i,j,True)])
    shell = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    # Water-shedding side lips and shell-mount flanges under side edges
    seg_len = x_max-x_min
    cx=(x_min+x_max)/2
    flanges = [
        box('', (seg_len, 8, 8), (cx, width/2+3, z0+4)),
        box('', (seg_len, 8, 8), (cx, -width/2-3, z0+4)),
        # low gutter lips outside the side flanges
        box('', (seg_len, 4, 5), (cx, width/2+10, z0+2)),
        box('', (seg_len, 4, 5), (cx, -width/2-10, z0+2)),
    ]
    return combine([shell]+flanges)

# Chassis v0.2: central low tray + shell rail mount points + module bays.
def chassis_center_segment():
    meshes=[]
    # Low central spine plates, split into printable 250 mm reference segment.
    meshes.append(box('', (250, 112, 10), (0,0,18)))
    # side float connector rails
    meshes.append(box('', (250, 9, 18), (0,64,24)))
    meshes.append(box('', (250, 9, 18), (0,-64,24)))
    # shell rail supports - raised to keep shell above dry cassette
    meshes.append(box('', (235, 7, 12), (0,76,54)))
    meshes.append(box('', (235, 7, 12), (0,-76,54)))
    # cross ribs / slots represented by raised ribs
    for x in [-100,-50,0,50,100]:
        meshes.append(box('', (8, 108, 12), (x,0,30)))
    # cassette bay rails
    meshes.append(box('', (170, 6, 12), (0,32,38)))
    meshes.append(box('', (170, 6, 12), (0,-32,38)))
    # Battery low tray side stops
    meshes.append(box('', (130, 6, 8), (0,42,24)))
    meshes.append(box('', (130, 6, 8), (0,-42,24)))
    # four latch pads for shell, asymmetric notch key on left/front
    for x in [-95,95]:
        for y in [-70,70]:
            meshes.append(box('', (22,18,10),(x,y,62)))
    meshes.append(box('', (16,12,12),(-115,70,62)))  # orientation key block
    return combine(meshes, 'PSR-HU-020 chassis center segment v0.2')

# Shell mount base rail/gauge - printable reference part for ensuring shell/chassis slot alignment.
def shell_mount_base():
    meshes=[]
    meshes.append(box('', (230, 12, 8), (0,0,4)))
    for x in [-100,-50,0,50,100]:
        meshes.append(box('', (8,36,6), (x,0,11)))
    # orientation key notch block
    meshes.append(box('', (18,14,10),(-115,20,10)))
    return combine(meshes, 'PSR-SHL-000 shell mount base')

def inner_dry_cassette_dummy():
    meshes=[]
    meshes.append(box('', (150,60,38), (0,0,40)))
    # raised lid lip
    meshes.append(box('', (160,70,4), (0,0,62)))
    # handle rib
    meshes.append(box('', (80,8,8), (0,0,68)))
    # desiccant/inspection window dummy frame
    meshes.append(box('', (44,4,3), (0,36,57)))
    meshes.append(box('', (44,4,3), (0,44,57)))
    meshes.append(box('', (4,12,3), (-24,40,57)))
    meshes.append(box('', (4,12,3), (24,40,57)))
    return combine(meshes, 'PSR-PWR-010 inner dry cassette dummy')

def low_center_battery_tray():
    meshes=[]
    meshes.append(box('', (150,70,8),(0,0,8)))
    meshes.append(box('', (150,6,26),(0,38,20)))
    meshes.append(box('', (150,6,26),(0,-38,20)))
    meshes.append(box('', (6,70,26),(-78,0,20)))
    meshes.append(box('', (6,70,26),(78,0,20)))
    # strap slots represented as shallow raised bridges/guides
    meshes.append(box('', (10,84,6),(-35,0,34)))
    meshes.append(box('', (10,84,6),(35,0,34)))
    return combine(meshes, 'PSR-PWR-011 low center battery tray')

def charge_scute_insert():
    meshes=[]
    # Non-metallic window insert for wireless charging. Slight crown + raised rim.
    meshes.append(box('', (94,72,3),(0,0,1.5)))
    meshes.append(box('', (104,6,5),(0,39,4)))
    meshes.append(box('', (104,6,5),(0,-39,4)))
    meshes.append(box('', (6,72,5),(-52,0,4)))
    meshes.append(box('', (6,72,5),(52,0,4)))
    # centered coil alignment cross (thin raised bars)
    meshes.append(box('', (70,2,2),(0,0,7)))
    meshes.append(box('', (2,50,2),(0,0,7)))
    return combine(meshes, 'PSR-SHL-003 charge scute window insert')

def wireless_charge_window_dummy():
    meshes=[]
    meshes.append(box('', (110,86,5),(0,0,2.5)))
    meshes.append(box('', (90,66,3),(0,0,6.5)))
    # relief gutters
    meshes.append(box('', (120,4,4),(0,48,6)))
    meshes.append(box('', (120,4,4),(0,-48,6)))
    return combine(meshes, 'PSR-CHG-003 top wireless charge window dummy')

def solar_ready_pad():
    # Flat pad showing future solar/perovskite coating area, no electronics.
    meshes=[]
    meshes.append(box('', (150,82,3),(0,0,1.5)))
    # light rib grid for flexible panel adhesion / coating mask
    for y in [-24,0,24]:
        meshes.append(box('', (138,2,2),(0,y,5)))
    for x in [-48,0,48]:
        meshes.append(box('', (2,72,2),(x,0,5)))
    return combine(meshes, 'PSR-SHL-002 solar ready pad dummy')

# Simplified full assembly reference, not intended for printing as one part.
def assembly_reference():
    meshes=[]
    # central hull simplified full length
    meshes.append(box('', (500,112,12),(0,0,18)))
    # side floats simplified as elongated blocks with rounded-ish end caps cylinders for visual volume
    meshes.append(box('', (480,42,52),(0,100,28)))
    meshes.append(box('', (480,42,52),(0,-100,28)))
    # bow and stern raised ramps (concept blocks)
    meshes.append(box('', (32,190,20),(-250,0,36)))
    meshes[-1].apply_translation((0,0,0))
    # chassis rails and dry cassette
    meshes.append(chassis_center_segment().copy().apply_translation((0,0,0)) or chassis_center_segment())
    # full shell, two segments
    front = dome_segment(-SHELL_L/2, 0)
    rear = dome_segment(0, SHELL_L/2)
    meshes.extend([front,rear])
    # inner cassette visible lower (can be covered by shell)
    meshes.append(inner_dry_cassette_dummy())
    # charge scute position on rear top: place flat insert near x=70 and high on dome approx z=136
    sc = charge_scute_insert(); sc.apply_translation((70,0,136)); meshes.append(sc)
    return combine(meshes, 'PSR-ASM-001 full rover turtle shell reference assembly')

# Generate STL outputs
parts=[]
def add(id, filename, mesh, desc, material='PLA/PETG', print_note='Draft reference geometry. Validate dimensions before field use.'):
    path=export(mesh, filename)
    parts.append({
        'part_id':id,
        'filename':filename,
        'category':id.split('-')[1] if '-' in id else 'ASM',
        'material':material,
        'description':desc,
        'print_note':print_note,
        'path':str(path.relative_to(ROOT))
    })

add('PSR-HU-020', f'PSR-HU-020-{REV}_center_chassis_segment_v0_2.stl', chassis_center_segment(), 'Updated center chassis segment with shell mount rails, dry cassette bay, low battery tray interface, and side float connector rails.', 'PETG', 'Print flat. This is a chassis test segment, not a complete waterproof hull.')
add('PSR-SHL-000', f'PSR-SHL-000-{REV}_shell_mount_base_gauge.stl', shell_mount_base(), 'Shell mount base/gauge for testing rail spacing, orientation key, and replaceable shell interface.', 'PLA/PETG', 'PLA is acceptable for fit test; PETG for water-adjacent tests.')
add('PSR-SHL-001F', f'PSR-SHL-001F-{REV}_standard_turtle_shell_front.stl', dome_segment(-SHELL_L/2, 0), 'Front half of standard turtle shell cover. First defense layer against rain, splash, mud, and shallow waterline contact.', 'PETG', 'Print with supports as needed. Keep shell light; do not over-infill.')
add('PSR-SHL-001R', f'PSR-SHL-001R-{REV}_standard_turtle_shell_rear.stl', dome_segment(0, SHELL_L/2), 'Rear half of standard turtle shell cover. Provides removable roof cover and water-shedding side lips.', 'PETG', 'Print with supports as needed. Rear segment can carry Charge Scute insert in later revisions.')
add('PSR-SHL-002', f'PSR-SHL-002-{REV}_solar_ready_pad_dummy.stl', solar_ready_pad(), 'Solar/perovskite-ready pad dummy. Used to test future solar-shell mounting surface without adding panels yet.', 'PLA/PETG', 'This is a dummy pad; do not mount real panels until heat and water tests are complete.')
add('PSR-SHL-003', f'PSR-SHL-003-{REV}_charge_scute_window_insert.stl', charge_scute_insert(), 'Charge Scute / wireless charge window insert. Non-metallic target area for top wireless charging through the turtle shell.', 'PETG/ASA later', 'Keep non-metallic. Do not place screws or metal washers near this part.')
add('PSR-CHG-003', f'PSR-CHG-003-{REV}_top_wireless_charge_window_dummy.stl', wireless_charge_window_dummy(), 'Top wireless charge window dummy for the charge-module slot. Used to compare cassette, wired, and wireless charging upgrades.', 'PLA/PETG', 'Dummy only. Do not connect batteries directly to wireless coil modules.')
add('PSR-PWR-010', f'PSR-PWR-010-{REV}_inner_dry_cassette_dummy.stl', inner_dry_cassette_dummy(), 'Inner dry cassette dummy for controller, BMS, charger electronics, and radio module. Second defense layer under shell.', 'PLA/PETG', 'Use for fit tests only; final cassette needs gasket/seal validation.')
add('PSR-PWR-011', f'PSR-PWR-011-{REV}_low_center_battery_tray.stl', low_center_battery_tray(), 'Low-center battery tray mockup. Keeps battery mass low while the turtle shell remains lightweight.', 'PETG', 'Do not rely on printed tray alone to restrain a real lithium battery. Add straps and mechanical locks.')
add('PSR-ASM-001', f'PSR-ASM-001-{REV}_full_rover_turtle_shell_reference_assembly.stl', assembly_reference(), 'Full visual reference assembly showing revised chassis, side floats, shell, dry cassette, and charge scute concept.', 'Not for printing as one part', 'Reference only. This part exceeds normal print size and is for CAD review.')

# Manifests
with open(ROOT/'print_manifest_turtle_shell_v0_2.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=['part_id','filename','category','material','description','print_note','path'])
    w.writeheader(); w.writerows(parts)

with open(ROOT/'kit_index_turtle_shell_v0_2.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['kit','part_id','qty','required','purpose'])
    rows=[
        ['Turtle Shell Chassis v0.2','PSR-HU-020',1,'yes','Updated chassis test segment'],
        ['Turtle Shell Chassis v0.2','PSR-SHL-000',1,'yes','Shell mount gauge'],
        ['Turtle Shell Chassis v0.2','PSR-SHL-001F',1,'yes','Front standard shell'],
        ['Turtle Shell Chassis v0.2','PSR-SHL-001R',1,'yes','Rear standard shell'],
        ['Turtle Shell Chassis v0.2','PSR-PWR-010',1,'yes','Inner dry cassette fit check'],
        ['Turtle Shell Chassis v0.2','PSR-PWR-011',1,'yes','Low battery tray fit check'],
        ['Charge Module option','PSR-CHG-003',1,'optional','Top wireless charge window dummy'],
        ['Solar-ready option','PSR-SHL-002',1,'optional','Future panel/coating pad dummy'],
        ['Charge Scute option','PSR-SHL-003',1,'optional','Non-metallic wireless charge target'],
        ['CAD reference','PSR-ASM-001',1,'no','Full reference assembly only'],
    ]
    w.writerows(rows)

# SVG overview
svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
<style>text{font-family:Arial,'Noto Sans JP',sans-serif;font-size:20px}.small{font-size:15px}.label{font-size:18px;font-weight:bold}.outline{fill:none;stroke:#111;stroke-width:3}.part{fill:#e6eef5;stroke:#111;stroke-width:2}.shell{fill:#d9ead3;stroke:#111;stroke-width:3}.float{fill:#d9e2f3;stroke:#111;stroke-width:2}.charge{fill:#fff2cc;stroke:#111;stroke-width:2}.danger{fill:#f4cccc;stroke:#111;stroke-width:2}</style>
<text x="40" y="50" style="font-size:32px;font-weight:bold">Paddy Swarm Turtle Shell Chassis v0.2 - Overview</text>
<text x="40" y="80" class="small">Standard turtle shell is the first defense layer. Inner dry cassette remains the second defense layer.</text>
<!-- top view -->
<text x="80" y="130" class="label">Top View / 上面</text>
<rect x="130" y="180" width="650" height="80" rx="35" class="float"/>
<rect x="130" y="420" width="650" height="80" rx="35" class="float"/>
<rect x="190" y="285" width="530" height="110" rx="15" class="part"/>
<ellipse cx="455" cy="340" rx="285" ry="150" class="shell"/>
<line x1="455" y1="190" x2="455" y2="490" stroke="#111" stroke-width="2" stroke-dasharray="10,8"/>
<rect x="525" y="300" width="110" height="80" rx="8" class="charge"/>
<text x="535" y="345" class="small">Charge Scute</text>
<text x="535" y="365" class="small">充電甲板</text>
<rect x="285" y="300" width="145" height="80" rx="8" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="6,6"/>
<text x="300" y="345" class="small">Solar-ready</text>
<text x="300" y="365" class="small">後付け面</text>
<text x="805" y="225" class="small">Side floats / 左右フロート</text>
<text x="805" y="340" class="small">Central chassis + Power Bay</text>
<text x="805" y="365" class="small">中央シャーシ + 電源ベイ</text>
<!-- side view -->
<text x="80" y="570" class="label">Side View / 側面</text>
<rect x="160" y="675" width="600" height="22" class="part"/>
<rect x="300" y="630" width="240" height="40" rx="8" class="part"/>
<path d="M170 625 C260 505, 650 505, 750 625 L720 642 C620 555, 300 555, 200 642 Z" class="shell"/>
<rect x="395" y="584" width="110" height="42" rx="6" class="charge"/>
<text x="415" y="610" class="small">CHG</text>
<text x="790" y="610" class="small">甲羅は水切り・泥はね防止・10度傾斜時の水面ガード</text>
<text x="790" y="635" class="small">内部ドライカセットは残す。甲羅だけを最終防水にしない。</text>
<text x="790" y="660" class="small">No battery in shell. Keep mass low.</text>
</svg>'''
(DOCS/'turtle_shell_chassis_overview_v0_2.svg').write_text(svg, encoding='utf-8')

# Docs
README = f'''# Paddy Swarm Turtle Shell Chassis CAD Pack v0.2

This pack updates the Paddy Swarm amphibious rover test body with a **standard turtle shell cover** and a revised center chassis interface.

## Concept

The turtle shell is now treated as a standard first-defense layer:

- rain guard
- mud splash guard
- shallow waterline / tilt guard
- rollover scuff guard
- future solar/perovskite mounting surface
- mascot/trademark shape

It is **not** treated as the only waterproof enclosure in v0.2. The correct early structure is:

```text
outer standard turtle shell
↓
inner dry cassette / battery cassette
↓
low center battery tray and chassis
```

## Important safety rule

Do not remove the inner waterproof/dry cassette yet. FDM printed shells can leak through layer lines, seams, cracks, screw holes, and cable openings. Use this CAD pack for fit, float, tilt, splash, and handling tests before adding electronics.

## Main files

- `stl/hull_v0_2/PSR-HU-020-R00_center_chassis_segment_v0_2.stl`
- `stl/hull_v0_2/PSR-SHL-001F-R00_standard_turtle_shell_front.stl`
- `stl/hull_v0_2/PSR-SHL-001R-R00_standard_turtle_shell_rear.stl`
- `stl/hull_v0_2/PSR-PWR-010-R00_inner_dry_cassette_dummy.stl`
- `stl/hull_v0_2/PSR-PWR-011-R00_low_center_battery_tray.stl`
- `stl/hull_v0_2/PSR-SHL-003-R00_charge_scute_window_insert.stl`
- `stl/hull_v0_2/PSR-ASM-001-R00_full_rover_turtle_shell_reference_assembly.stl`

## Print priority

1. `PSR-SHL-000-R00_shell_mount_base_gauge.stl` in PLA
2. `PSR-HU-020-R00_center_chassis_segment_v0_2.stl` in PLA
3. `PSR-PWR-010-R00_inner_dry_cassette_dummy.stl` in PLA
4. `PSR-SHL-001F/R` shell halves in PLA for fit check
5. Repeat shell halves in PETG for water-adjacent tests
6. Print `PSR-SHL-003` Charge Scute insert only after confirming top-charge placement

## Bambu Lab A1 note

The shell is split into front/rear halves so printable parts stay near or below the A1 print area. The full assembly STL is a visual reference and is not meant to be printed as one piece.

## Field-use warning

This is Grade 0 / early Grade 1 CAD. Do not mount a live battery or controller until dry tests, splash tests, tilt tests, and paper-towel leak checks are complete.
'''
(ROOT/'README_turtle_shell_chassis_pack_v0_2.md').write_text(README, encoding='utf-8')

DOC_MAIN = '''# Paddy Swarm Standard Turtle Shell + Chassis v0.2

## Purpose

This revision changes the turtle shell from a future solar luxury part into a standard protective body cover.

The shell is intended to protect expensive electronics and motors from direct rain, mud splash, shallow waterline contact during tilt, and light rollover scuffing.

## Design decision

The shell is a first defense layer, not the final waterproof container.

```text
Standard Turtle Shell = first defense
Inner Dry Cassette = second defense
Battery Cassette = protected power module
Chassis = low-center structure and float/motor interface
```

## Why the chassis needed an update

A standard shell requires new hardpoints:

- shell mount rails
- orientation key so the shell cannot be installed backwards
- inner dry cassette bay
- low-center battery tray interface
- charge module / charge scute reserved area
- future solar-ready surface planning

## Charge Scute

The Charge Scute is a non-metallic window zone for future top wireless charging.

Rules:

- do not put metal screws near the coil window
- do not charge directly into a lithium battery
- use a receiver module, voltage regulation, CC/CV charger, BMS, fuse, and temperature monitoring
- keep cassette charging and wired charging compatible through the common Power Bay concept

## Solar-ready shell

The v0.2 shell does not include solar panels. It only reserves upper surface area for:

- future removable solar panel mount
- perovskite coating experiments
- adhesive panel tests

The rover must remain fully useful without solar.

## Tilt and waterline test

Recommended first tests:

1. Mount shell to chassis with no electronics.
2. Put paper towels inside the dry cassette dummy.
3. Add ballast equivalent to expected electronics/battery weight.
4. Float in water tray/tank.
5. Tilt to 5°, 10°, and 15°.
6. Confirm water runs off the shell and does not pool.
7. Confirm no water drips into the dry cassette zone.
8. Log whether shell lips touch water and whether the rover self-righting tendency worsens.

## Remaining risks

- Shell raises center of gravity if printed too thick.
- Shell can catch wind.
- Shell can hold heat if ventilation is poor.
- Shell can trap condensation if sealed incorrectly.
- FDM print layer lines are not waterproof by default.
- Motor shaft exits still need separate mud and water guards.
'''
(DOCS/'turtle_shell_chassis_v0_2.md').write_text(DOC_MAIN, encoding='utf-8')

PRINT_NOTES = '''# Print Notes: PSR-SHL / Turtle Shell v0.2

## Suggested print settings

For PLA fit checks:

- 0.4 mm nozzle
- 0.20 mm layer height
- 3 walls
- 15-20% infill
- supports as needed

For PETG water-adjacent shell tests:

- 0.4 or 0.6 mm nozzle
- 0.20-0.28 mm layer height
- 4 walls
- 15-25% infill
- avoid making the shell heavy

## Key principle

The turtle shell should be light. It protects by deflecting water and mud, not by becoming a heavy pressure vessel.

## Do not

- Do not install electronics under a shell-only waterproof assumption.
- Do not place lithium batteries in the shell roof.
- Do not place metal fasteners near the Charge Scute coil zone.
- Do not make flat top surfaces that hold water.

## First print order

1. Shell mount base gauge
2. Center chassis segment
3. Inner dry cassette dummy
4. Front shell half
5. Rear shell half
6. Charge Scute insert
'''
(PN/'PSR-SHL-R00.md').write_text(PRINT_NOTES, encoding='utf-8')

PUSH = '''# Repo push guide: Turtle Shell Chassis v0.2

From your local repository root:

```powershell
cd C:\\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_turtle_shell_chassis_cad_v0_2.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add standard turtle shell chassis CAD v0.2"
git push
```

Recommended commit note:

- Adds standard turtle shell cover concept
- Updates chassis with shell mount rails and inner dry cassette bay
- Adds Charge Scute wireless charge window dummy
- Keeps inner dry cassette as second defense layer
'''
(DOCS/'repo_push_turtle_shell_chassis_pack.md').write_text(PUSH, encoding='utf-8')

# copy generator script into CAD dir by writing this source from __file__? Since running from /tmp, copy itself.
import inspect
source = Path(__file__).read_text(encoding='utf-8') if '__file__' in globals() else ''
(CAD/'generate_turtle_shell_chassis_v0_2.py').write_text(source, encoding='utf-8')
(ROOT/'experiments'/'shell_tilt_test'/'.gitkeep').write_text('', encoding='utf-8')

# Zip
zip_path = Path('/mnt/data/paddy_swarm_turtle_shell_chassis_cad_v0_2.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(ROOT))
print(zip_path)
print('files', len([p for p in ROOT.rglob('*') if p.is_file()]))
