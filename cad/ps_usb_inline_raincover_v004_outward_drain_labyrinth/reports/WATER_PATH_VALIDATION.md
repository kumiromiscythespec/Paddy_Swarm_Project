# WATER PATH VALIDATION

Physical rating: `SPLASH_RESISTANT_PHYSICAL_PASS_WITH_PRESSURE_JET_LIMIT`

| Required CAD statement | Result |
|---|---|
| `LOWER FLOOR GRAVITY VECTOR` | OUTWARD |
| `UPPER CEILING GRAVITY VECTOR` | OUTWARD |
| `CHAMBER-SIDE SILL` | PRESENT |
| `CAPILLARY BREAK` | PRESENT_AND_DRAIN_CONNECTED |
| `DRAIN` | AT_LOWEST_POINT_CAPTURE_REGION |
| `CLOSED WATER POCKET` | NONE_CAD |
| `DIRECT LINE OF SIGHT` | NONE_CAD |
| `physical_v004_coupon` | PENDING |

The lower relief slopes outward 7° and the upper ceiling slopes outward 4° without reducing minimum cable clearance.
The 1.2 × 0.8 mm capillary break directly intersects the relocated 2.5 mm drain capture region.
Strong direct pipette WET is recorded as `PRESSURE_JET_LIMIT_OBSERVED`; it is not a required PASS condition.
Physical coupon tests at level, +5°, and -5° remain mandatory.
