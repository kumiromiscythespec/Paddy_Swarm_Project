# Common Rover v0.8.3 Measurement Integration and Dimensional Audit

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Document `PS-CR-MEASUREMENT-INTEGRATION-V0083` integrates user measurements without releasing holes,
shaft cut lengths, support-plate machining, or field use.

## 1. Parent protection and architecture

v0.8, v0.8.1 and v0.8.2 are protected by 56 embedded hashes and verified
against repository files when available. Two motors, two independent PTO
shafts, inward motor axes, DRIVE/NEUTRAL/PTO clutches, high CBOX/BBOX,
non-structural boxes, inverted-trapezoid crawlers, v0.8.1
`S2-REF-T5-BP2.00-OP5.50` and v0.8.2 `P3-A5052-T5` are unchanged.

## 2. Accepted provisional measurements

KP000 envelope becomes 67 x 17 x 35 mm, shaft center is 18.5 +/-0.5 mm
from the base, one insert protrusion is 6 mm, two round mounting holes are
reported at diameter 8 mm, there are two insert set screws and no grease
nipple. The CAD bore remains nominal 10 mm pending caliper verification.
Mount-hole centers and total axial envelope remain absent from geometry.

MODEL_A retains the 120 mm rotation safety OD and 20 mm axial width.
MODEL_B records flange OD 100 mm, toothed-body OD 96 mm provisional, axial
total 20 mm, face width 17 mm provisional and flange thickness 2 mm.
Hub OD/width and bore remain HOLD.

## 3. Rejected and reinterpreted inputs

The KP000 ruler reading of 11 mm is rejected because a 10 mm shaft passes
with almost no play. The reported pulley bore 11 mm is not accepted as a
load fit. A 17 mm value is axial tooth-face width, not toothed diameter; 96
mm is the provisional radial body OD, not hub OD. Three millimetres is an
unidentified tooth-width report. Fourteen millimetres is likely bolt length,
not M5 diameter. A 196 mm hex-key total length is not local tool clearance.
The 4 mm washer thickness is conflicted. The 1400 mm shaft value is inventory
total, never one installed shaft.

There are 12 registered discrepancies.

## 4. Shaft/bore fit

Configuration A, nominal 10 mm shaft and nominal 10 mm KP000 bore, is a
nominal match but remains tolerance HOLD. Configuration B, 10 mm shaft and
reported 11 mm pulley bore, has 1.0 mm diametral clearance and up to 0.5 mm
radial eccentricity before clamping. It can increase runout, belt wander,
tension variation, local set-screw stress, mass eccentricity, printed-hub
cracking and removal-to-removal variation.

If 11 mm is confirmed, the current single-set-screw pulley is
`FAIL_PROVISIONAL_FOR_LOAD`. Hand-turn prototype, precision bush, removable
metal hub and replacement with a true 10 mm bore are separately classified.

## 5. KP000 and plate non-regression

The old 45 x 15 x 35 envelope changes by +22 mm in X, +2 mm in Y and 0 mm
in Z. The axis/base relation changes from 17.5 to 18.5 mm. The 95 x 140 x
5 mm P3 plate remains a candidate and leaves 14 mm outline margin on each
side of the 67 mm KP000. No plate holes are emitted.

The one-side insert can reduce PTO belt/KP000 candidate distance to 3.0 mm.
Housing-only pulley/KP000 distance is 14.5 mm, but worst provisional
insert-facing-pulley distance is 8.5 mm, below the prior 10 mm safety target.
Insert direction and total axial envelope are therefore critical.

## 6. Pulley models and axial conflict

Safety decisions use MODEL_A OD120. MODEL_B is measurement visualization
only. The component expression 2 + 17 + 2 equals 21 mm and conflicts with
the reported 20 mm total by 1 mm. The 20 mm outer total controls the
provisional envelope; component widths are non-additive until remeasured.

## 7. Axial stack and shaft stock

Each side has an explicit stack table. Known housing, insert and pulley values
are separated from collars, spacer, coupling and output reserve HOLD values.
The preliminary geometric shaft coverage is
139.5 to
145.5 mm, but
there is no released installed-length range. Both 300 and 400 mm stock can
cover that preliminary range; 300 mm minimizes offcut provisionally. Cutting
remains HOLD.

## 8. Fixation

One set screw is prototype hand-turn only. Two screws and a D-flat remain
unreleased mitigations. A removable metal clamping hub or a printed toothed
ring bolted to a metal hub are preferred concepts, subject to bore, hub,
torque, bolt and material measurements. A keyed hub requires a different or
machined shaft.

## 9. Interference and width

All four belt intersection counts remain zero in the candidate model.
Candidate overall width remains 290 mm and PTO endpoints remain +/-145 mm.
Physical width is HOLD because collars, coupling, output reserve and complete
KP000 axial envelopes are missing. The report registers
2 provisional clearance
failure category and 4 HOLD checks.

## 10. Release state

- measurement integration: CONDITIONAL_PASS
- envelope geometry: CONDITIONAL_PASS_WITH_HOLDS
- physical fit: HOLD
- pulley bore fit: FAIL_PROVISIONAL
- support-plate hole pattern: PART_MEASUREMENT_REQUIRED
- shaft cutting, machining and drilling: HOLD
- field deployment: NOT_APPROVED
