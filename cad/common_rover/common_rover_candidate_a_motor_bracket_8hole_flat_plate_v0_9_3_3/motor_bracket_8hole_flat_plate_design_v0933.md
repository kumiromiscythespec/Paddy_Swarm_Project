# Common Rover Candidate A Motor Bracket 8-Hole Flat Adapter Plate v0.9.3.3

Status: `CONDITIONAL_PASS_CANDIDATE` / `NOT_FOR_POWERED_OPERATION`

## Design authority scope

This differential lane records a simple, repairable flat plate only. Current Common Rover authority pointers and the v0.9.3.1/v0.9.3.2 parent lanes remain unchanged. v0.9.3.2 is preserved as evidence; its M4 direct-thread variants are superseded only by this lane's M3/M5 through-hole concept.

## Functional geometry

- PETG plate: 42.0 × 80.0 × 6.0 mm, R3.0, flat base Z=0.
- Metal drilling reference: same XY geometry, 3.0 mm thick.
- Inner interface: four straight Ø3.4 mm M3 clearance through-holes at X=±12, Y=±15 mm.
- Outer interface: four straight Ø5.7 mm M5 clearance through-holes at X=±10, Y=±30 mm.
- One solid; no blind holes, threads, counterbores, countersinks, pockets, ribs, bosses, cradle, steps, or functional-surface text.
- Left and right use the identical part and identical STL; quantity required is two, but print one first.

## Automated geometry evidence

- Minimum edge ligament: **7.15 mm** (requirement ≥5.0 mm).
- Minimum hole-center distance: **15.132746 mm**.
- Minimum hole-edge gap: **10.582746 mm**.
- Maximum pairwise hole intersection volume: **0.000000000 mm³**.
- Maximum plate residual inside all eight cutting cylinders: **0.000000000 mm³**.
- Blank-minus-eight-holes analytic/CAD volume delta: **0.000000000 mm³**.

## Physical evidence and HOLDs

Ø3.4 M3 is `PASS / JUST_FIT`. Ø4.2 M4 is retained as `PASS / JUST_FIT_REFERENCE_ONLY`; the v0.9.3.3 plate contains zero M4 holes. Exact M3/M5 nut, washer, screw-tip, T-slot, and torque envelopes remain `MEASUREMENT_HOLD`. H6/H8/H10 are comparative height witnesses, not released spacer dimensions.

No belt tension, powered rotation, torque load, production drilling, field deployment, or authority update is approved.
