# Common Rover Robust Axial Tolerance Design Authority v0.8.5

Document ID: `PS-CR-ROBUST-AXIAL-TOLERANCE-V0085`

`NOT_FOR_MANUFACTURING`  
`PART_MEASUREMENT_REQUIRED`

## Protected parents and baseline

This is a difference authority over protected v0.8 through v0.8.4. Repository
runtime verification covers 100 parent paths. The v0.8.4 recommendation
`S2-INCC-OUTOO-SHIFT01.00` is preserved as a comparison but not inherited.

Its old center nominal was 1 mm. Independent bilateral error makes the new
center residual -1 mm, so it fails v0.8.5. The former Alternative A also has
only 1 mm nominal center clearance and is not robust under the corrected model.

## Corrected independent tolerance model

Each side has independent inner-KP000, pulley and outer-KP000 axial errors of
-1/0/+1 mm. Center error is bilateral, relative component error can reach
2 mm, belt worst allowance is 6 mm and pulley worst allowance is 3.5 mm.
Zero center residual is FAIL.

Selection priority is boundary pass, center residual, minimum belt residual,
minimum pulley residual, output reserve, plate fit, added parts, shaft length,
change and finally Stage. The v0.8.4 early-Stage preference is superseded.

## Search

The search contains 2108 candidates: two protected
v0.8.4 comparisons plus coarse 0.5 mm and refined 0.25 mm grids. All use inner
C/C and outer O/O. R1, R2 and R3 were explicitly evaluated:

- R1: center 4.0/2.0 mm, belt residual min 8.0 mm, status ROBUST_CONDITIONAL_PASS_CANDIDATE
- R2: center 5.0/3.0 mm, belt residual min 8.0 mm, status ROBUST_CONDITIONAL_PASS_CANDIDATE
- R3: center 5.0/3.0 mm, belt residual min 8.5 mm, status ROBUST_CONDITIONAL_PASS_CANDIDATE

## Recommended

`G-IN5.00-P11.25-OUT10.00`

- Inner centers: Y=+/-19.0 mm, shift 5.0 mm
- Pulley centers: Y=+/-58.25 mm, shift 11.25 mm
- Outer centers: Y=+/-97.5 mm, shift 10.0 mm
- Center nominal/residual: 9.0/7.0 mm
- Inner belt worst nominal/residual: 14.25/8.25 mm
- Outer belt worst nominal/residual: 14.25/8.25 mm
- Inner pulley worst nominal/residual: 14.75/11.25 mm
- Outer pulley worst nominal/residual: 14.75/11.25 mm
- Output reserve: 33.0 mm
- Width and ends: 290 mm, +/-145 mm

The interval authority is `ROBUST_CONDITIONAL_PASS` and includes the full
0..6 mm opposite protrusion interval.

## Alternatives

- Alternative A `G-IN5.00-P11.00-OUT09.50`: inner/pulley/outer shifts
  5.0/11.0/9.5 mm.
- Alternative B `G-IN5.00-P11.00-OUT09.75`: inner/pulley/outer shifts
  5.0/11.0/9.75 mm.

Both satisfy every corrected boundary gate. They are ordered below the
recommendation by residual/output/change priorities, not Stage.

## Support, tool and shaft

P3-A5052-T5 remains a mirrored independent 95 x 140 x 5 mm reference candidate.
No hole is released. Simplified tool clearance is 12 mm with zero envelope
intersection, but actual-tool access remains HOLD.

The coordinate-derived shaft range is 134.5 to
140.5 mm. A 300 or 400 mm bar can provisionally yield
two shafts. Kerf and cutting remain HOLD.

## Release

- Geometry envelope: `CONDITIONAL_PASS_CANDIDATE`
- Tolerance robustness: `ROBUST_CONDITIONAL_PASS_CANDIDATE`
- Opposite protrusion: `PART_MEASUREMENT_REQUIRED`
- Pulley bore fit: `FAIL_PROVISIONAL`
- Physical fit, support machining, drilling, shaft cutting: `HOLD`
- Load, water and mud tests: `HOLD`
- Field deployment: `NOT_APPROVED`
