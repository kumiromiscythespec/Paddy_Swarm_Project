# Common Rover v0.8.1 Belt-Clearance Differential Authority

Document ID: `PS-CR-FRONT-DRIVE-DUAL-PTO-BELT-CLEARANCE-V0081`  
Parent authority: `PS-CR-FRONT-DRIVE-DUAL-PTO-DESIGN-AUTHORITY-V008`  
Physical fit: `HOLD`  
Manufacturing release: `HOLD`  
Field deployment: `NOT_APPROVED`

## Scope

v0.8 remains intact. This document changes only belt-plane/support envelope
candidates needed to improve the v0.8 PTO clearance. It does not release a
physical part, aluminum cut, hole, load test, water/mud test, or field use.
Motor height means **motor shaft-center height**, not motor-body underside.

## Reproduced v0.8 baseline

The ten v0.8 path hashes match: `True`.

| Check | v0.8 |
|---|---:|
| DRIVE belt–frame | 15.5 mm |
| PTO belt–frame/fixed hardware | 5.5 mm |
| DRIVE belt–root 2040 | 25.5 mm |
| DRIVE belt–front track diagonal | 15.5 mm |
| PTO belt–2020 diagonal | 70.0 mm |
| PTO belt–front crossbar | 71.53 mm |
| PTO 60T–KP000 | 11.0 mm |
| Track dynamic–upper structure | 10.0 mm |
| STEP width | 290.0 mm |
| PTO ends | Y=+/-145 mm |

The 5.5 mm PTO corridor loses all recommended margin after the provisional
1 mm assembly, 2 mm frame-deflection and 2 mm belt-wander allowances.

## Ordered exploration

- Stage 1 Y-only candidates: 507 coarse plus refined candidates.
- Stage 1 maximum nominal/residual PTO clearance:
  9.50 /
  4.50 mm.
- Stage 1 result: `FAIL_CANNOT_REACH_13_AND_8`.
- Stage 2 compares reversed hardware and 5/6/8 mm metal support plates,
  then performs coarse and 0.25 mm refinement.
- Stage 2 result: `CONDITIONAL_PASS`.
- Stages 3–6: `NOT_EXECUTED_STAGE_2_SATISFIED_TARGET`.

Stage 1 cannot reach 13/8 mm without collision or fixed-hardware shortfall.
No X/Z frame move, root-crossmember change, stack-order change, tensioner
relocation, added 2020, or added 2040 is adopted.

## Recommended candidate — S2-REF-T5-BP2.00-OP5.50

- PTO belt planes move 2.0 mm outward to Y=+/-47.0.
- Inner KP000 axes stay at Y=+/-14.0.
- Each inner 2020 support is replaced by a **5 mm metal plate envelope
  candidate** at the same bearing center.
- Outer KP000/supports move 5.5 mm outward to Y=+/-87.5.
- Inner and outer fastener heads/nuts/washers face away from the belt.
- DRIVE belt planes remain Y=+/-119.0.
- Nominal PTO clearance: 15.00 mm.
- Residual PTO clearance: 10.00 mm.
- Nominal/residual DRIVE clearance:
  15.50 /
  10.50 mm.
- 60T-to-fixed candidate clearance:
  13.00 mm.
- Wiring-reserve clearance: 21.50 mm.
- Total width: 290.00 mm.
- PTO ends: +145 / -145 mm.

`RESIDUAL = NOMINAL - 1 - 2 - 2`. The 2 mm belt wander is provisional.
Measured belt lateral wander is still required, so this is
`CONDITIONAL_PASS`, not physical PASS.

## Alternatives

1. `S2-REF-T5-BP0.00-OP1.50` is the minimum-change threshold option:
   13.00 nominal /
   8.00 residual, with only
   1.50 mm summed Y change.
2. `S2-REF-T6-BP2.50-OP6.00` uses a 6 mm plate candidate:
   15.00 nominal /
   10.00 residual. It needs more
   Y movement and its strength is also uncalculated.

## Fasteners, tools, clutch, and tensioners

Candidate fixed-hardware intersections are zero. Left/right inner fastener
envelopes do not intersect. Parameterized left/right tool boxes do not
intersect the opposite support, but actual tool size and approach are HOLD.

Both clutches retain DRIVE, NEUTRAL, PTO and full-stroke registrations.
Both DRIVE and PTO tensioners retain minimum, nominal and maximum state
registrations. Actual stroke/travel envelopes are `PART_MEASUREMENT_REQUIRED`.

## Crawler and box non-regression

The inverted trapezoid, four-roller STEP candidate, 400 mm upper 2040,
260 mm lower 2040, Z200 box bottom, and 10 mm track/upper-structure clearance
remain unchanged. Z210 would give a 20 mm reference gap but is not selected
and is not used to solve belt clearance.

## Aluminum and added parts

The recommended envelope uses 2020 stock bars 7/8 and 2040 bars 7/8.
No member exceeds 400 mm. One 2020 and one 2040 400 mm bar remain reserve.
Two inner metal support plates require additional purchase. Their material,
outline, holes, mass, stiffness, fatigue, corrosion protection, and exact cost
are unresolved; therefore plate fabrication remains HOLD.

## Inspection result

- Geometric checks: 21 conditional,
  0 fail.
- Four belt/frame intersections: zero.
- Four belt/fastener intersections: zero.
- PTO nominal/residual: 15.00 /
  10.00 mm.
- DRIVE nominal/residual: 15.50 /
  10.50 mm.

## Mandatory holds

- Actual belt lateral wander and belt length
- Actual motor, clutch stroke, 20T/60T widths/flanges/runout
- KP000 dimensions, rating, sealing and life
- 5 mm plate material/strength/hole pattern
- Actual bolts, nuts, washers, collars, rings and couplings
- Actual tool access and tensioner travel
- Crawler cover, track runout, idler adjustment, mud allowance
- BBOX effective interior and cassette path
- Structural/torsional analysis and completed mass/CG

Physical fit remains `HOLD`; aluminum cutting, drilling, manufacturing and
load testing remain `HOLD`; field deployment remains `NOT_APPROVED`.
