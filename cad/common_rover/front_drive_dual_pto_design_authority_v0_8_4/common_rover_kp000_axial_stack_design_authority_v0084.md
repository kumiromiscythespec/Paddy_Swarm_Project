# Common Rover KP000 Axial Stack Design Authority v0.8.4

Document ID: `PS-CR-KP000-AXIAL-STACK-V0084`

`NOT_FOR_MANUFACTURING`  
`PART_MEASUREMENT_REQUIRED`

## Authority and protected parents

This is a difference authority layered on protected v0.8, v0.8.1, v0.8.2 and
v0.8.3. It does not release support-plate machining, drilling, shaft cutting,
load testing, water/mud testing or field deployment. Parent SHA verification
checked 76 paths when the
repository was available.

The fixed architecture remains two motors, two independent lateral PTO shafts,
no common PTO shaft, inward motor axes, left output +Y, right output -Y,
front-concentrated DRIVE/NEUTRAL/PTO transmission, high non-structural serial
CBOX/BBOX and inverse-trapezoid crawlers.

## v0.8.3 deficiency and baseline

The baseline was reproduced: pulley-to-housing 14.5 mm,
pulley-to-collar-worst 8.5 mm, PTO-belt residual-to-collar 3.0 mm,
PTO-belt-to-frame 15.0 mm, DRIVE-belt-to-frame 15.5 mm, width 290 mm and
PTO ends +/-145 mm.

The physical HTD belt is 15 mm wide. The v0.8.3 path foundation adds a
3 mm per-side swept-path offset, so the nominal axial sweep is 21 mm.
Assembly, wander and deflection add 5 mm per side for a 31 mm safety sweep.

KP000 is 67 x 17 x 35 mm. Its known collar extends 6 mm beyond one housing
face. The opposite protrusion is not measured and remains a 0..6 mm
sensitivity variable.

## Orientation authority

`ORIENTATION_C` means the set-screw collar faces vehicle center.
`ORIENTATION_O` means it faces vehicle outside. These names are used instead
of ambiguous left/right-facing labels.

At unchanged Y=+/-14 mm, dual inner `ORIENTATION_C` gives:

`28 - 17 - 6 - 6 = -1 mm`

The STEP envelope confirms this collision candidate. Flip-only is rejected.

## Ordered exploration

| Stage | Candidates | Nominal pass | Outcome |
|---:|---:|---:|---|
| 0 | 1 | 0 | BASELINE |
| 1 | 16 | 0 | ORDERED_SEARCH |
| 2 | 76 | 4 | ORDERED_SEARCH |
| 3 | 169 | 28 | ORDERED_SEARCH |
| 4 | 33 | 22 | ORDERED_SEARCH |
| 5 | 0 | 0 | NOT_REQUIRED_AFTER_STAGE_4_ROBUST_ALTERNATIVE |
| 6 | 0 | 0 | NOT_REQUIRED_AFTER_STAGE_4_ROBUST_ALTERNATIVE |

Stage 5 spacer/collar optimization and Stage 6 alternate bearing selection were
not required after Stage 4 produced a fully robust alternative. They are not
automatically adopted.

## Recommended candidate

`S2-INCC-OUTOO-SHIFT01.00` is the first ordered stage meeting nominal gates.

- Inner KP000: C/C, Y=+/-15.0 mm
- Outer KP000: O/O, Y=+/-87.5 mm
- Pulley plane: Y=+/-47.0 mm
- Center clearance: 1.0 mm
- Inner belt nominal/residual: 13.0/8.0 mm
- Outer belt nominal/residual: 21.5/16.5 mm
- Inner/outer pulley nominal clearance: 13.5/22.0 mm
- Inner/outer pulley residual after 1.5 mm runout and 1 mm axial error: 11.0/19.5 mm
- Simplified tool clearance: 12.0 mm, but actual tool remains HOLD
- Total width 290 mm; PTO output ends +/-145 mm

This requires 1.0 mm outward movement per inner KP000, or 2.0 mm additional
central bearing-center width. Pulley movement, outer-KP000 movement, PTO-end
extension and support-plate enlargement are zero. Required shaft range becomes
138.5..144.5 mm, 1.0 mm
shorter than the v0.8.3 provisional range.

The recommendation follows the Stage hierarchy and is
`CONDITIONAL_PASS_AT_NOMINAL_ONLY` because only opposite protrusion values
[0] pass every specified
allowance combination. Physical fit is not released.

## Alternatives

Alternative A `S4-IN01.00-P06.00-OUT+03.5` moves the pulley 6.0 mm outward and the
outer KP000 3.5 mm outward. It passes all
756 combinations and is
`ROBUST_CONDITIONAL_PASS`, but is not preferred because Stage 2
already meets nominal gates with fewer changes.

Alternative B `S3-IN01-P+03` moves the pulley 3.0 mm outward and is
fully robust only through opposite protrusion
3 mm.

## Support plates and tool access

P3-A5052-T5 remains an independent mirrored 95 x 140 x 5 mm A5052-P candidate.
The reference envelopes fit without outline enlargement. No manufacturing hole
is created because KP000 hole-center distance is missing. The reference STEP
shows mounting, belt, pulley and tool keep-outs only.

The recommended collar directions permit simplified +X/front hex-key insertion
with a 12 mm candidate clearance. Tool intersection is zero in the simplified
envelope, but `HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED` remains. Pulley or belt
removal requirements must be verified at dry assembly.

## Axial stack and stock

The stack contains 17 classified entries per side. Coordinate-derived shaft
length is 138.5..144.5 mm.
A 300 mm or 400 mm stock bar can provisionally yield two shafts, subject to
kerf, end preparation and final measurements. No cut length is released.

## Robust sensitivity

The recommendation was checked across 7 opposite protrusions, 4 pulley
runouts, 3 assembly errors, 3 frame deflections and 3 belt-wander values:
756 combinations. 276 pass and
480 fail. This is a measurement gate, not a manufactured
fit claim.

## Release states

- Geometry envelope: `CONDITIONAL_PASS_CANDIDATE`
- Robustness: `CONDITIONAL_PASS_AT_NOMINAL_ONLY`
- Opposite protrusion: `PART_MEASUREMENT_REQUIRED`
- Physical fit: `HOLD`
- Pulley bore fit: `FAIL_PROVISIONAL`
- Shaft cutting / support machining / drilling: `HOLD`
- Load, water and mud tests: `HOLD`
- Field deployment: `NOT_APPROVED`
