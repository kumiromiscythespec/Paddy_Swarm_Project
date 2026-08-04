# Common Rover Powertrain Frame Right-Angle Joint Trade Study v0.9.3.4

Status: `TRADE_STUDY_ONLY` / `NO_MANUFACTURING_RELEASE`

## Scope and parent evidence

This differential lane compares two right-angle frame-joint concepts without changing authority or v0.9.3.0, v0.9.3.1, or v0.9.3.3. The latest user-reported stack uses two added plain washers and one lower height-adjustment nut per M5×16. Gap range 4.3…4.5 mm, full T-nut thread traversal, no aluminum indentation, four-point levelness, and M5×16 are physical no-load PASS results. Powered or belt load remains NOT_APPROVED.

The available exact CAD does not identify the current profile manufacturer, slot, wall, core-hole, or orientation. Consequently the frame is a conservative 40×20 mm rectangular side-rail envelope and 100×40×20 mm crossmember envelope. Exact profile compatibility remains `MEASUREMENT_HOLD`.

## Baseline rejection

The current inner-corner proxy intrudes 27.9 mm from each inner face. The nominal 100 mm powertrain corridor is reduced to **44.2 mm**. It is retained only as comparison evidence and is `REJECT_CANDIDATE_IN_POWERTRAIN_ZONE`.

## Candidate A — outboard end-tap bolt

The crossmembers butt between X=-50 and +50 mm inner faces. Bolt head, through corridor, end engagement, outboard tool, and tip-intrusion envelopes are separated. Central fixed intrusion is zero. M5 and M6 are envelope comparisons only. Exact thread size, core location, wall clearance, bolt length, engagement, and two-core feasibility remain HOLD. A one-bolt-per-side arrangement does not provide adequate anti-rotation evidence.

## Candidate B — underside full-width tie plate

Two 180×40×3 mm R3 reference plates join the frame from below without upper-zone intrusion. The plate-only drop is 3 mm; head/washer drop and total ground-clearance impact remain measurement HOLD. Proxy common volumes against CBOX, BBOX, and track are zero, but drainage, mud retention, T-slot coordinates, fastener protection, and four-point support require a physical mockup.

## Crossmember Y sweep

The 5 mm grid evaluates 255 front/rear pairs against a fixed guarded envelope Y=-250.0…-120.0 mm and a separate service envelope Y=-255.0…-115.0 mm.

- Minimum viable: front Y=-280.0, rear Y=-90.0, frame length 230.0 mm, fixed clearance 10.0 mm, service clearance 5.0 mm.
- Target: front Y=-285.0, rear Y=-85.0, frame length 240.0 mm, fixed clearance 15.0 mm, service clearance 10.0 mm.
- Limiter: conservative 60T fixed-guard proxy; service limiter is belt/guard removal access.

## Actual height case

`ACTUAL_H4P3_TO_H4P5_WASHER_NUT_STACK` is the primary case. The comparison motor/20T datum is Z=115.3…115.5 mm (derived nominal 115.4 mm), while the retained 60T/selector candidate is Z=166.0 mm. The vertical difference is 50.5…50.7 mm (derived nominal 50.6 mm). `PREVIOUS_H3P8_TO_H3P9_TWO_NUT_STACK` is retained as historical evidence; H6/H8/H10 remain references. These values are comparison geometry and do not update authority.

## M5 length evidence

M5×16 traversed the full T-nut thread according to the latest user report and is a physical no-load PASS in the two-washer/one-nut stack. Thread pitch is unmeasured, so engagement millimetres are deliberately not calculated. M5×20 comparison priority is lowered but not cancelled; M5×25 remains LENGTH_HOLD. A 24-hour no-load creep check is required before belt tension.

## Decision

`A_AND_B_PHYSICAL_MOCKUP_REQUIRED`. Candidate A depends on profile end-hole/tap evidence; Candidate B depends on underside/T-slot/ground-clearance/drainage evidence. Scores do not override these HOLDs. Fallback C/D are recorded but not modeled because neither A nor B has a current hard CAD fail.

No drilling, tapping, plate manufacture, powered rotation, belt tension, torque load, or field deployment is approved.
