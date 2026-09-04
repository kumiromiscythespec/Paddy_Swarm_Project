# Common Rover v0.9.2 — Inward PTO Coupling Design Authority

Document ID: `PS-CR-INWARD-PTO-COUPLING-V092`

Status: `CONDITIONAL_PASS_CANDIDATE`  
Physical fit: `HOLD`  
Manufacturing: `NOT_FOR_MANUFACTURING`  
Field deployment: `NOT_APPROVED`

## Scope and protected parents

This exact 45-path lane is a delta over protected v0.9.1. It does not
overwrite v0.8–v0.9.1. The v0.9.1 lane contains 37 protected files with tree
ledger `1670e3a2553ff4495022e8c3b45afcc1e534c886229d899fd6405d81c190c95d`. Its protected handoff ZIP has SHA-256
`54b2ca2894f6c78fce59752eb39b319cc8dbeb00befdf88525617f66bc17ab9c`. The chained audit also protects 124 v0.8–v0.8.5 paths
and 38 v0.9.0 paths.

## v0.9.1 contradiction reproduced

v0.9.1 gives inboard support faces at Y=+30.5/-30.5 and shaft ends at
Y=+30/-30. The geometric end gap is 60 mm, but the exposed shaft stub is only
0.5 mm per side. A coupling requiring 8 mm engagement plus axial reserve
cannot engage. Consequently:

- geometric bay, exposed shaft stub, engagement length, coupling body,
  movement sweep, and sensor envelopes are separate contracts;
- `CENTER_GAP_60MM` is not accepted as usable coupling engagement;
- a left-right common shaft or direct coupling remains prohibited.

## Fixed architecture

Two motors, two independent PTO ports, two independent inward PTO shafts,
two slide clutches, two DRIVE belts, and two PTO belts are retained.
DRIVE/NEUTRAL/PTO remains mechanically exclusive. PTO while travelling and
switching while motors rotate are prohibited. The 60T pulley remains between
two bearings. The central bay is mechanical only; UNIT_PRESENT, UNIT_ID,
left/right engaged feedback, electrical power, data, and fault signals remain
separate.

## Search stages

- Stage 0 Parent Baseline: 1
- Stage 1 Stub Lengths: 9
- Stage 2 Center Gaps: 7
- Stage 3 Stub Shift Pairs: 63
- Stage 4 Coupling Envelopes: 252
- Stage 5 Architectures: 252
- Stage 6 Fixed Movable Side: 252
- Stage 7 Shaft End Geometry: 252
- Stage 8 Engagement Depth: 252
- Stage 9 Sliding Stroke: 252
- Stage 10 Sensors: 4
- Stage 11 Shaft End Candidates: 7
- Stage 12 Full Factorial With Reserve: 7560
- Stage 13 Ranked Finalists: 3

Total recorded evaluations: `9166`. The core center-bay
table contains `1512` architecture/envelope/stub/shift
combinations. Stage order was retained. Larger coupling classes were not
forced into the design by widening the rover.

## Recommended candidate

`S12-C1-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1`

- C1 work-unit-side dual sliding sleeves;
- COUPLING_SMALL envelope: OD20, body length25, required engagement8,
  stroke10 mm;
- stub length 12.5 mm per side; no bearing-stack shift;
- shaft ends Y=+18/-18; central end gap 36 mm;
- engagement margin 2.5 mm after a 2 mm axial geometry reserve;
- body-to-body clearance 11 mm and full-sweep mutual clearance 12 mm;
- fixed-structure clearance 10 mm, wiring clearance 25 mm, installation
  path clearance 5 mm;
- total width remains 290 mm;
- left/right torque paths and engagement sensing remain independent.

Only the SMALL sensitivity envelope fits the searched center bay and
<300 mm width contract. MEDIUM reaches only 1 mm body gap at 10 mm shift and
299 mm width; at 12.5 mm shift it reaches 6 mm gap but 304 mm width and fails.
Therefore `COUPLING_PART_SELECTION_CRITICAL = TRUE`.

## Alternatives

- Alternative A: C4 axial face dog, SMALL, 12.5 mm stub, no shift, 1 mm
  reserve, S6. Tooth geometry, spring force, sealing, and machining are HOLD.
- Alternative B: C3 manual split clamp, SMALL, 12.5 mm stub, no shift, 2 mm
  reserve, S1. Tool, bolt retention, and service access are HOLD.

No commercial part is selected and no torque rating is inferred.

## Engagement and state safety

The sequence U0–U6 separates absence, physical presence, identity,
mechanical lock, left engagement, right engagement, and both-engaged ready.
PTO enable additionally requires the requested input mask
NONE/LEFT_ONLY/RIGHT_ONLY/BOTH, protection of unused inputs, DRIVE
disengagement, zero vehicle speed, zero motor speed before switching, and no
fault. Any fault removes PTO enable and enters manual-inspection lockout.

## Clearance and non-regression

The recommended simplified envelopes have zero recorded intersections.
Body mutual clearance is 11 mm; full sweep mutual clearance is 12 mm;
central fixed structure is 10 mm; wiring is 25 mm. v0.9.1 values are retained:
belt/fixed 11.5 mm, PTO OD120/fixed 10 mm, clutch/fixed 12 mm,
clutch/belt 10 mm, PTO bottom Z260, E2 bottom Z440, and total width 290 mm.

These are parametric envelope results, not physical measurements.

## Shaft length

The v0.9.1 provisional shaft range 139.5–145.5 mm is increased by 12 mm
inward extension to a v0.9.2 candidate range of 151.5–157.5 mm per side.
A 300 mm stock piece cannot safely yield two upper-range shafts. A 400 mm
piece may yield two candidates only after actual diameter, straightness,
saw allowance, facing allowance, retention, and final dimensions are known.
`SHAFT_CUTTING = HOLD`.

## Measurement and release gates

Required: actual shaft diameter/straightness, inboard face datums, available
stub, selected coupling OD/body/engagement/stroke/misalignment/torque/
retention/sealing, unit input coordinates, guards, caps, tool access,
wiring motion, mud intrusion, support analysis, and hand-fit evidence.

The dummy STEP/STL is hand-fit/no-load geometry only. It is not a torque
coupler and must not be powered.

`PHYSICAL_FIT = HOLD`  
`COUPLING_PART_SELECTION = CRITICAL_HOLD`  
`SUPPORT_MACHINING = HOLD`  
`SHAFT_CUTTING = HOLD`  
`LOAD_TEST = HOLD`  
`POWERED_ROTATION = HOLD`  
`WATER_MUD_TEST = HOLD`  
`FIELD_DEPLOYMENT = NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
