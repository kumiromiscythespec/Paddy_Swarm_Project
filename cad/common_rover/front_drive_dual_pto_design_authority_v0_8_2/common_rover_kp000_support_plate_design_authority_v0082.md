# Common Rover KP000 Support Plate Design Authority v0.8.2

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Document: `PS-CR-KP000-SUPPORT-PLATE-V0082`  
Parent: v0.8 and fixed v0.8.1 candidate `S2-REF-T5-BP2.00-OP5.50`.

## 1. Authority

This supplement details the two independent inner-KP000 support plates. It
does not repeat the v0.8.1 belt-placement search. Physical fit, material
selection, machining, drilling, cutting, load testing, water/mud testing and
field deployment remain HOLD or NOT_APPROVED.

## 2. Protected architecture and baseline

Two motors, two independent PTO ports, inward motor shafts, outward PTO
outputs, three-position DRIVE/NEUTRAL/PTO clutches, no common PTO shaft,
front-concentrated transmission, non-structural CBOX/BBOX, inverted-trapezoid
tracks, width 290 mm and PTO ends +/-145 mm are unchanged.

The fixed v0.8.1 clearances remain PTO belt/frame 15.0 mm, PTO
belt/fasteners 20.0 mm, DRIVE belt/frame 15.5 mm, DRIVE
belt/fasteners 19.5 mm, PTO 60T/fixed 13.0 mm, wiring 21.5 mm, PTO
residual 10.0 mm, DRIVE residual 10.5 mm and track/upper structure 10.0 mm.

## 3. Existing evidence and missing measurements

The repository contains the user-reported 60T maximum dimension 102 mm, whose
meaning remains `CALIBRATION_PENDING`, and a 120 mm safety rotation envelope.
The 45 x 15 x 35 mm KP000 and nominal 10 mm shaft are unverified CAD
envelopes, not measurements. No manufacturer KP000 drawing, purchase record
or dimensioned physical photo was found. 59 sheet entries remain
`PART_MEASUREMENT_REQUIRED`.

## 4. Plate role and selected outline

Each 5 mm metal plate supports one inner KP000, holds its shaft center at
Y=+/-14 mm, replaces the obstructing inner 2020 support, keeps bolt heads away
from the belt, remains removable with its bearing, and transfers candidate
belt reaction toward the front metal frame. The plates are not joined.

Recommended `P3-A5052-T5` is P3, an A5052-P 5 mm triangular load-path
flat-profile candidate. Width 95.0 mm, height
140.0 mm and every shown hole remain parametric.

Alternatives are `P2-A6061-T5` and
`P3-STEEL-T4.5`. P1 is lighter but misses the preferred
tool clearance; lower-safety candidates remain HOLD.

## 5. Material comparison

- A5052-P 5 mm: corrosion and forming/machining candidate; minimum analytical
  input yield 140 MPa; exact temper and certificate required.
- A6061-series 5 mm: higher candidate yield input; exact alloy/temper and
  availability required.
- General structural steel 3 mm: lower section stiffness and rust protection
  burden.
- General structural steel 4.5 mm: stronger/stiffer candidate but heavier;
  coating and galvanic isolation required.

Material properties are explicitly parametric comparison inputs, not certified
allowables.

## 6. Hole and fastening contract

KP000 holes, frame holes, slots, locating holes, cover holes and datum holes
are separately managed. Current CAD/DXF holes are inspection placeholders.
Edge distance 10 mm and spacing 20 mm are candidate rules only. A slot may
adjust alignment but may not be the sole permanent locator.

F2 captive insert is recommended only as the KP000-to-plate concept and F5
T-nut only as the plate-to-frame concept. Insert pull-out, thread engagement,
T-nut fit/slip, bolt preload, mud sealing, corrosion and reverse-load locking
remain HOLD.

## 7. Tool access

Tool insertion is redirected along X. The envelope study gives 14 mm nominal
candidate clearance with zero simplified intersections, improving the v0.8.1
1.5 mm central approach. Actual hex key, socket, spanner, ratchet and finger
envelopes must be measured before serviceability is accepted.

## 8. Load and analytical comparison

LC1 through LC5 use hypothetical 100–300 N belt loads, 1–5 N m torque,
shock factors 1.0–2.0, simultaneous 100 N coupling side load and load
reversal. The conservative flat-plate comparison uses simple cantilever
stress/deflection formulas. `P3-A5052-T5` has candidate safety factor
2.0218 and deflection
0.1932 mm under the comparison envelope.
Hole bearing, tear-out, bolt loads, T-nut slip, frame rotation, fatigue and
corrosion are not passed.

Status is `CONDITIONAL_PASS_ANALYTICAL_ONLY`, not physical PASS.

## 9. Deflection-clearance coupling

PTO residual clearance after the comparison plate deflection is
9.8068 mm. PTO 60T/fixed
clearance after the same conservative displacement is
12.8068 mm. Both exceed
8 mm and 10 mm candidate gates, respectively. Belt tracking tolerance and
actual frame connection stiffness remain HOLD.

## 10. Alignment and assembly

1. Loosely fasten left and right plates independently.
2. Loosely fasten each KP000 to its plate.
3. Pass each independent PTO shaft through its inner and outer KP000 pair.
4. Rotate each shaft by hand.
5. Adjust until binding is minimized; limits remain ALIGNMENT_LIMIT_HOLD.
6. Snug plate-to-frame fasteners.
7. Tighten KP000 fasteners incrementally and diagonally.
8. Tighten plate-to-frame fasteners.
9. Rotate each shaft again and record the change.
10. Install the 60T pulley and axial collars.
11. Install the belt.
12. Recheck shaft rotation and center movement under candidate belt tension.

Record shaft insertion resistance, unloaded rotation torque, left/right center
difference, bearing parallelism, tightening-induced rotation change and
belt-load-induced center movement. Limits are `ALIGNMENT_LIMIT_HOLD`.

Replacement follows the controlled reverse sequence after removing belt,
pulley and collars. Never use plate flexure for alignment.

## 11. Interference and non-regression

The 15 registered envelope checks have
zero candidate intersections. Width remains 290 mm; PTO ends remain
Y=+/-145 mm. No belt location, track geometry, box arrangement, aluminum
member length or parent architecture changed.

## 12. Mud, water and corrosion

Provide downward drainage, avoid water-trap pockets, isolate dissimilar
metals, verify coating/finish, retain grease-port and bearing replacement
access, and keep any mud guard outside belt and tool envelopes. Stainless
fasteners against aluminum require an isolation system candidate.

## 13. Release state

- envelope geometry: CONDITIONAL_PASS_CANDIDATE
- analytical strength: CONDITIONAL_PASS_ANALYTICAL_ONLY
- physical fit: HOLD
- material selection: HOLD
- hole pattern: PART_MEASUREMENT_REQUIRED
- aluminum cutting: HOLD
- plate machining and drilling: HOLD
- load and water/mud tests: HOLD
- field deployment: NOT_APPROVED
