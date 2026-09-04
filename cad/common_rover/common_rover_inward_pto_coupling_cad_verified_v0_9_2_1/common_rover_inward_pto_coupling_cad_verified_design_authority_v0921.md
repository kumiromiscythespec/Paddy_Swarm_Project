# Common Rover inward PTO coupling actual-CAD authority v0.9.2.1

Document ID: `PS-CR-INWARD-PTO-CAD-VERIFIED-V0921`

Status:

- FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED
- INWARD_PTO_GEOMETRY_CONDITIONAL_PASS
- CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED
- COUPLING_FULL_SWEEP_ACTUAL_CAD_VERIFIED
- INDEPENDENT_DRY_FIT_JIG_READY
- UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL
- PHYSICAL_FIT_HOLD
- LOAD_CAPACITY_HOLD
- POWERED_TEST_NOT_APPROVED
- NOT_FOR_MANUFACTURING
- FIELD_DEPLOYMENT_NOT_APPROVED

## Parent and superseded behavior

This differential authority protects v0.8 through v0.9.2 and reproduces the
v0.9.2 baseline. The v0.9.2 report used parametric/fixed expected clearances
and a fixed zero intersection count; it did not implement actual Shape-pair
interference. Its no-load dummy also used one Y-continuous shaft and was
invalid for independent-PTO fit confirmation. The parent files remain intact.

## Actual-CAD calculation authority

Every row in the v0.9.2.1 clearance matrix is calculated from named CadQuery
Shapes. Boolean common geometry uses `CadQuery.Shape.intersect()`,
intersection volume uses `Shape.Volume()`, solid count uses `Shape.Solids()`,
and minimum distance plus nearest points use
`OCP.BRepExtrema_DistShapeShape`. Exceptions are classified `ERROR` and never
fall back to `PASS`.

- numerical distance tolerance: 0.050 mm
- intersection volume tolerance: 0.010 mm³
- pair calculations in the matrix: 138
- intersect/contact/clear: 0/14/124
- pass/fail/error: 138/0/0
- minimum actual distance: 0.000 mm
- minimum pair/state: `CAD-0009` / `RETRACTED`
- nearest point A: (160.000, 18.000, 320.000) mm
- nearest point B: (160.000, 18.000, 320.000) mm
- maximum actual intersection volume: 0.000000 mm³

Known-geometry canaries pass 6/6:
overlap, face contact, 5 mm gap, 10 mm gap, coaxial 1 mm radial gap, and a
0.5 mm-sampled sweep collision.

## State results

| State | Pairs | Intersect | Contact | Clear | PASS | FAIL | ERROR |
|---|---:|---:|---:|---:|---:|---:|---:|
| RETRACTED | 28 | 0 | 4 | 24 | 28 | 0 | 0 |
| PARTIAL | 28 | 0 | 4 | 24 | 28 | 0 | 0 |
| ENGAGED | 28 | 0 | 4 | 24 | 28 | 0 | 0 |
| FULL_SWEEP | 24 | 0 | 2 | 22 | 24 | 0 | 0 |

The full stroke is represented by a conservative continuous sweep Shape and
by 21 actual positions per side at
0.5 mm intervals. The sampled sweep contains
420 actual pair calculations. Its minimum
clearance is 5.000 mm at
travel 0.000 mm; collision position is
`None`.

## Independent dry-fit authority

The jig uses two distinct uncut 300 mm stock references. The left shaft ends
at Y=+18 mm and extends outward to +318 mm; the right ends at Y=-18 mm and
extends outward to -318 mm. No solid crosses the central 36 mm interval.
Bearing-face to shaft-end stub reference is 12.5 mm on each side. Left and
right sleeves and work-unit inputs are separate. Sleeve travel states are
0/5/10 mm; the 10 mm state provides 10 mm geometric overlap against the
8 mm engagement reference. These are no-load geometry references, not product
fit or torque parts.

DF0 through DF8 cover parts, independent shaft positioning, retracted sleeves,
front insertion, mechanical lock, partial engagement, full engagement,
disengagement, and removal. The 35/36/37 mm comparison gauges are assembly
references, not tolerance gauges. The 12.5 mm stub gauge is nominal only.

## Upstream scope limitation

Central coupling Shapes are actual-CAD verified by this lane. Frame, bracket,
fastener, belt, clutch, pulley, track, and other upstream powertrain items are
reconstructed from v0.9.2 parametric envelopes and retain
`UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL`. This document explicitly
does not claim `ACTUAL_CAD_FULL_SYSTEM_VERIFIED`.

## Release holds

Physical fit, load capacity, shaft cutting, shaft-end machining, support-plate
machining, manufacturing, powered rotation, and field deployment remain HOLD
or NOT_APPROVED. No physical test has been performed. Do not infer a product
coupling bore, material, key, D-flat, torque capacity, wear life, or fit from
the printed dummy.
