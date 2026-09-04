# Common Rover v0.9.1 — Outboard Powertrain Pods and Inward Independent PTO

Document ID: `PS-CR-OUTBOARD-INWARD-V091`

Status: `CONDITIONAL_PASS_CANDIDATE`  
Physical fit: `HOLD`  
Manufacturing: `HOLD`  
Field deployment: `NOT_APPROVED`

## Scope and protected parent

This is a delta authority over protected v0.9.0.  It does not overwrite
v0.8–v0.9.0.  The parent lane contains 38 files and has tree-ledger SHA-256
`e6480973c32b76cbaf8c4cdb404f7a8ec1d2f9e4c48780bda8a416416c6421f6`.  The parent handoff ZIP SHA-256 is
`d6f4fe041617fa3153894365c2d71f86af964a1c1da78de9964fe63b2e9c9756`.  The chained v0.8–v0.8.5 protection contract covers
124 paths.

The v0.9.0 baseline is reproduced before this search:

- `S4-B-PTOX040.0-Z320.0-FX40.0-FY20.0-FZ20.0`
- motor axis Z=370 mm; PTO axis X=100, Z=320 mm
- PTO rotation bottom Z=260 mm; water/mud margin 60 mm
- DRIVE planes Y=±119 mm; PTO planes Y=±58.25 mm
- total width 290 mm
- outward PTO: left +Y, right -Y
- parent clearances 4.75/5.0/3.5 mm are reproduced but not accepted as v0.9.1 PASS
- E2 remains X=180, Z=455, bottom Z=440 mm

## Contract delta

v0.9.1 changes only PTO direction and the surrounding packaging contract:

- left motor shaft -Y and left PTO output -Y (both inward);
- right motor shaft +Y and right PTO output +Y (both inward);
- left and right PTO shafts, couplings, and torque paths remain independent;
- no edge connects the left and right inward output nodes;
- no common PTO shaft and no third PTO motor;
- two DRIVE belts plus two PTO belts remain four separate HTD 5M belts;
- Architecture B short-stroke selector and independent jackshafts are retained.

The old outward direction remains valid only inside the protected parent lane.
It is superseded conditionally by this lane after the pointer gate.

## Search order and counts

The required stage order was preserved.  Stage 10 was not needed because
FRAME-E meets the envelope targets without a new subframe proposal.

- Stage 0: 1 candidates
- Stage 1: 1 candidates
- Stage 2: 15 candidates
- Stage 3: 54 candidates
- Stage 4: 10 candidates
- Stage 5: 204 candidates
- Stage 6: 8 candidates
- Stage 7: 55 candidates
- Stage 8: 30 candidates
- Stage 9: 326 candidates
- Stage 10: 0 candidates

Stage 1 (direction-only flip) is rejected: it retains the parent's sub-target
clearances, has no defined central coupling bay, and does not model an
outboard pod.  F2040-B is rejected because its 40 mm Y thickness leaves only
1.5 mm to the selected PTO belt safety corridor.  Above/below L-bracket
placements are rejected when their physical bolt/tool envelopes consume the
belt corridor.  B2/B3 add service overlap; B4/B5 remain alternatives.

## Recommended candidate

`S9-B1-F2040A-FRAMEE-PTOX210-Z320-PY85.0-DY40.0-LX70-GAP60-C1`

- left/right outboard motor centers: X=-60, Y=±100, Z=370 mm;
- selected motor sensitivity: MOTOR_MEDIUM 100×65×85 mm;
- MOTOR_SMALL, MOTOR_MEDIUM, and MOTOR_LARGE all remain inside the 290 mm
  crawler-controlled width envelope; this is not a motor product selection;
- PTO 20T centers: X=0, Y=±85, Z=370 mm;
- PTO 60T centers: X=150, Y=±85, Z=320 mm;
- PTO 20T and 60T share the same Y plane per side without belt twist;
- DRIVE planes are Y=±125 mm; PTO/DRIVE safety corridors have a 9 mm gap;
- F2040-A rails are Y=±48 mm, 20 mm in Y and 40 mm in Z;
- FRAME-E transfers each PTO through two KP000 envelopes and independent
  A5052-P plate candidates into the split F2040-A structure;
- L_LARGE is checked as a full 40×40×5 mm sensitivity envelope with bolt,
  washer, T-nut, nut, insertion, and tool-rotation reserves.  Its near face is
  moved to X=220 mm, beyond the rotating and belt envelopes;
- PTO height Z=320 gives rotation bottom Z=260 and 60 mm above the Z=200
  water/mud reference;
- total width with guards, bolt reserves, large-motor sensitivity, wiring
  gland, track projection, and central guides is 290 mm (<300).

## 60T and bearing Y stack

The PTO 60T candidate is 20 mm wide and uses an OD120 rotation envelope.
The pulley plane is |Y|=85 mm.  KP000 full-envelope centers are |Y|=45 and
125 mm.  The actual-width side clearances are 15.5 mm each.  The conservative
31 mm axial safety envelope has 10 mm to each full KP000 envelope.  The 60T is
therefore between two bearings, never cantilevered, and never positioned by
contact with a bearing.

KP000 remains 67×17×35 mm with a 6 mm insert protrusion sensitivity and
14.5 mm full axial half-envelope.  Both mounting ears are required.  Direct
KP000-to-2040 mounting is prohibited.  Hole-center distance is still HOLD, so
the 95×140×5 mm plate is an envelope only and has no released manufacturing
holes.

## Central work-unit PTO bay

The left independent shaft ends at Y=+30 mm while pointing -Y.  The right
independent shaft ends at Y=-30 mm while pointing +Y.  Their end gap is 60 mm,
above the 30 mm minimum and 50 mm target.  They are not joined.

C1, work-unit-side left/right sliding sleeves, is recommended conditionally.
The unit enters from +X, is aligned, and each sleeve moves outward toward its
own rover PTO end.  C2–C5 remain documented alternatives.  Coupling outside
diameter, length, stroke, alignment allowance, torque, sealing, and retention
are unmeasured, so physical coupling fit remains
`PART_MEASUREMENT_REQUIRED`.

The central bay is mechanical only.  UNIT_PRESENT, UNIT_ID, power, data, and
fault interfaces remain at high E2.  Wiring follows WORK_UNIT → protected
vertical riser → E2 → CBOX and does not cross shafts, belts, or tracks.

## Minimum-clearance result

The v0.9.1 envelope contract is stricter than the parent:

| Contract | Absolute | Target | Recommended |
|---|---:|---:|---:|
| Belt safety to fixed structure | 5 | 8 | 11.5 |
| Belt safety to L-bracket/fastener | 5 | 8 | 10.0 |
| PTO OD120 to fixed structure | 8 | 10 | 10.0 |
| PTO OD120 to L-bracket/fastener | 8 | 10 | 10.0 |
| Clutch full stroke to fixed structure | 5 | 8 | 12.0 |
| Clutch full stroke to belt | 8 | 10 | 10.0 |

All reported distances are conservative parametric-envelope candidates, not
physical measurements.  The interference matrix records zero intersections
for four belts, PTO rotation, clutch states, central shafts, and coupling
sweeps under the stated envelopes.

## Alternatives

Alternative A uses B5 / FRAME-C at PTO Z=330, a 50 mm central gap, and C3
manual clamps.  It adds vertical structure and needs tool and mud-seal tests.

Alternative B uses B4 / FRAME-D at PTO Z=300, a 70 mm gap, and C5.  It reaches
295 mm overall width, adds a subframe, and reduces water/mud margin to 40 mm.

## Power-flow and safety

DRIVE routes each motor through its slide clutch, DRIVE dog, independent
jackshaft, DRIVE 20T/belt/60T, track shaft, and its own track.  PTO routes each
motor through its slide clutch, PTO dog, independent jackshaft, same-plane
PTO 20T/belt/60T, independent shaft, and inward output.  NEUTRAL has no output
edge.  DRIVE and PTO cannot be simultaneously engaged.  Shifting while the
motor rotates and PTO operation while travelling remain prohibited.

PTO start still requires UNIT_PRESENT and the safe-state interlocks.  E2
remains centered at X=180/Z=455 with bottom Z=440.

## Measurement and release gates

Required before physical fit or manufacture:

- actual motor body, shaft, mount holes, wiring gland, and cooling clearance;
- actual L-bracket legs, width, thickness, bolt/washer/T-nut stack, alloy,
  strength, and tool envelope;
- KP000 hole-center distance, opposite protrusion, housing tolerances, and
  fastener stack;
- 60T runout, flange form, bore, fixing, and guard;
- belt dynamics, tensioner travel, guard thickness, and mud loading;
- coupling OD, length, engagement/disengagement stroke, torque, misalignment,
  retention, and sealing;
- support-plate analysis, released holes, shaft length, and shaft retention;
- dry fit, guarded spin, load, water, and mud tests.

`PHYSICAL_FIT = HOLD`  
`SUPPORT_PLATE_MACHINING = HOLD`  
`SHAFT_CUTTING = HOLD`  
`MANUFACTURING = HOLD`  
`FIELD_DEPLOYMENT = NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
