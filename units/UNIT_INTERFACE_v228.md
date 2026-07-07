# Paddy Swarm Unit Interface v228

This document defines the unit interface rules for attachments designed for:

```text
Paddy Swarm Common Rover v2.28.2 Dual PTO Restart
```

All v228-compatible units must follow this interface unless a later interface document explicitly replaces it.

## Core rule

The rover fixed core must not be redesigned for individual units.

The fixed core is:

```text
BBOX + CBOX in front/rear series
+ upper side-wall motor boxes
+ side-exit wheels
+ front high dual PTO output
```

Do not convert the rover into a different body shape for a unit.

## Fixed core dimensions

BBOX / CBOX body:

```text
200 x 150 x 120 mm
```

Lid:

```text
216 x 166 x 16 mm
```

Gasket:

```text
204 x 154 x 3 mm
```

The BBOX/CBOX boxes are arranged front-to-rear.

```text
Front
  ↓

[BBOX]
  |
[CBOX]

  ↓
Rear
```

They are not side-by-side.

## Box notch rule

The v228-compatible box notch rule is:

```text
- each box has one upper notch on each 20 cm wide wall face
- notches are on the front/rear 200 mm faces
- do not place notches on the 150 mm side faces
- do not place low side holes near the waterline
```

The notch is for dropping wiring from above.

The notch is not waterproof by itself.  
It requires additional sealing such as:

- silicone
- cable boot
- cable gland
- potting
- heat shrink
- drip cover

## Waterline rule

All units must assume the rover may float.

The target condition is:

```text
- BBOX/CBOX may be submerged up to roughly half height
- PTO output must remain above water
- motor boxes must remain above water
- wiring notches must remain above water
```

Do not design a unit that requires the rover body to sink in order to work.

For water and mud tests:

```text
first water test = dummy weights only
no electronics in first water test
```

## Coordinate convention

Use this coordinate convention for unit design documents and CAD comments:

```text
X = left / right
Y = front / rear
Z = up / down
```

Forward direction:

```text
+Y = front
-Y = rear
```

Left / right:

```text
-X = left
+X = right
```

Up:

```text
+Z = up
```

## Front PTO interface

v228.2 uses a front high dual PTO output.

The front PTO has two output positions:

```text
LEFT PTO output
RIGHT PTO output
```

These are intended for future left/right power takeoff experiments.

For early units, PTO should be used cautiously.

### PTO use levels

#### Allowed for early units

```text
- unlock a latch
- drop a unit
- raise or release a lightweight mechanism
- short-duration deployment action
```

#### Not allowed for early V001 units

```text
- continuous rotary weeding
- high-torque mud cutting
- pulling the rover downward
- mechanisms that can flip or drag the floating body
```

For `PS-WEED-V001-PASSIVE-RAKE`, PTO is used only for `PTO_DROP`, not continuous weeding.

## Unit mounting rule

Units should mount to the front unit interface or front PTO region.

Do not require new holes in BBOX/CBOX unless explicitly approved.

Preferred mounting:

```text
- front mount bracket
- shared PTO adapter
- removable pins
- clamp-on structures
- weak sacrificial pins where appropriate
```

Avoid:

```text
- permanent bonding to BBOX/CBOX
- drilling into waterproof box walls
- low-mounted waterline brackets
- hidden fasteners that cannot be cleaned
```

## Motor box rule

Motor boxes are mounted on the upper side wall of the waterproof box core.

They are not mounted on top of the boxes.

Units must not block:

- motor box access
- motor wiring access
- motor cooling / inspection space
- side wheel clearance

## Wheel and hull clearance

The rover wheels exit from the hull sides.

Units must not interfere with:

- wheel rotation
- TPU tread
- inner wheel float candidates
- axle service access
- mud clearance around wheel pockets

Any front unit must leave enough clearance for water, mud, straw, and roots to escape.

## Unit flotation and trim

Because the rover floats, front units must consider trim.

Heavy front units may push the PTO side downward.

If a unit extends forward or downward, consider:

```text
- mini floats on the unit
- adjustable ballast on the rover
- depth skids
- breakaway pins
- lift cord or manual recovery point
```

Do not depend on the rover sinking to make a tool reach the mud.

## Weeding unit rule

Early weeding units should follow this progression:

```text
V001: passive rake / comb
V002: oscillating rake
V003: dual counter-rotating rotor
```

Do not start with a complex rotary weeding unit.

Reason:

- the rover floats
- PTO reaction may move the body
- water propulsion must be verified first
- mud resistance is unknown
- tool depth control is not yet proven

## Passive rake rule

For passive rake units:

```text
- rover propulsion performs the weeding motion
- rake tines disturb shallow mud surface
- PTO is not used for continuous weeding
- depth is limited by skids
- tines must be replaceable
- unit must escape upward if it catches
```

Recommended initial working width:

```text
140 to 180 mm
```

Maximum early width:

```text
220 mm
```

Reason:

```text
30 cm rice row spacing must be respected.
The unit must not hit rice plants.
```

## Depth control rule

Early mud-contact units must include depth control.

Recommended depth levels:

```text
10 mm
20 mm
30 mm
```

Depth should be controlled by:

- skids
- height adjustment plates
- hinge angle stops
- manual pins
- drop limit stops

Do not use a fixed deep claw that can anchor the floating rover in mud.

## Breakaway rule

A unit must fail before damaging the rover body.

Recommended breakaway methods:

```text
- weak printed shear pin
- removable R-pin
- flexible tine
- upward escape hinge
- manual lift cord
```

The breakaway component should be cheap and easy to replace.

## Mini float rule

Front units may include mini floats.

Mini floats are for:

- reducing nose-down trim
- keeping PTO above water
- stabilizing a lowered tool
- improving recovery

Mini floats are not primary waterproof enclosures.

Printed mini floats require:

- sealing
- coating
- foam filling
- water tank testing

## Material rule

Default material groups:

```text
HARD:
- brackets
- arms
- skids
- latches
- mounts
- comb bars
- wheel hubs
- axle supports

TPU:
- tread
- bumpers
- soft stops
- optional flexible tines
- gasket-like parts
```

Do not let the word `tire`, `tread`, `rake`, or `tine` accidentally classify a HARD part as TPU.  
Manifest files must explicitly set material group.

## Print rule

All unit parts should target:

```text
Bambu Lab A1
256 x 256 x 256 mm
```

Preferred dense safety:

```text
safe 240
support-orient-fit-safe 244
gap 4
blank_a1_plates_4.3mf
```

Avoid:

```text
- parts larger than 240 mm
- floating islands
- hidden support traps
- 45 degree exactly as a safety assumption
- unsupported side protrusions
- sealed cavities that trap water
```

Use 46 degrees or more, preferably 60 degree style self-supporting geometry.

## Dense command template

From inside a unit version folder:

```powershell
python .\paddy_swarm_a1_dense_project_tools_v5_7_3_model_sets_paddy_fix.py --manifest .\<unit_out>\print_manifest_generic_marked.csv --out .\<unit_model_dense_sets> --group-mode all --ignore-manifest-plates --split-tpu --make-model-dense-sets --safe 240 --support-orient-fit-safe 244 --gap 4 --bambu-template-plate-inner-margin 12 --bambu-plate-inner-margin 12 --make-3mf --make-bambu-template-project-3mf --bambu-template-3mf .\blank_a1_plates_4.3mf --make-zip
```

## Documentation rule

Every unit version should include:

```text
README_<unit>.md
print_manifest.csv
print_manifest_generic_marked.csv
plate_manifest.csv
design_contract.json
SHA256SUMS
generation commands
```

README must state:

- compatible rover version
- purpose
- print status
- test status
- safety notes
- what not to do
- whether the unit is field-ready or not

## Test order

All v228-compatible units must follow this order:

```text
1. CAD generation
2. metadata-only check
3. slicer preview
4. small part print
5. dry fit
6. manual movement test
7. dummy weight water test
8. shallow mud resistance test
9. low-speed powered test
10. field-edge test only after repeated success
```

Do not skip directly to a real rice field.

## Field safety

The rice field is an income-producing field.

Do not test unproven units in a real paddy.

Early testing must be done in:

```text
- desk assembly
- dry floor
- water tank
- shallow mud tray
- controlled outdoor area
```

## Current v228-compatible unit

Current first unit:

```text
units/weed/passive_rake/v001/
```

Unit name:

```text
PS-WEED-V001-PASSIVE-RAKE
```

Purpose:

```text
- passive rake weeding experiment
- manual drop test
- PTO drop latch release test
- shallow mud depth control test
- front unit trim test
```

Status:

```text
prototype / pre-field / not field-ready
```