# ps_webcam_rainhood_v003_optical_clearance

Status: `CAD_COMPLETE_OPTICAL_COUPON_PHYSICAL_VALIDATION_PENDING`

This lane explores the top-of-image intrusion seen after the v002 tripod position was physically achieved. It does not change the camera pose to hide the problem. The v002 tripod axis, camera reference, carrier envelope, slide rails, rear stops, M4 shell retention, and USB relief are fixed.

## What to print

Print and compare all three files; no winner is selected in CAD:

| Candidate | File | Setback from v002 front | Underside bevel | Permanent ID | Status |
|---|---|---:|---:|---:|---|
| A | `stl/optical_coupon_A_setback10.stl` | 10 mm | 35 deg | 1 exterior rib | `PHYSICAL_OPTICAL_VALIDATION_PENDING` |
| B | `stl/optical_coupon_B_setback15.stl` | 15 mm | 40 deg | 2 exterior ribs | `PHYSICAL_OPTICAL_VALIDATION_PENDING` |
| C | `stl/optical_coupon_C_setback20.stl` | 20 mm | 45 deg | 3 exterior ribs | `PHYSICAL_OPTICAL_VALIDATION_PENDING` |

The angle values were not adjusted away from the requested 35/40/45 degrees. The generator solves bevel run while accounting for the unchanged 1.5-degree v002 roof slope. The exact derived runs and measured CAD angles are in `reports/candidate_dimensions.csv`.

## Why these are coupons, not three deployable rainhoods

A front-only clip would introduce a new attachment datum and could move relative to the camera. These coupons therefore retain the complete v002 carrier interface: both rail pairs, rear stops, rear crossbar, M4 bosses/holes/nut traps, and USB opening. The full-width optical roof extends to Y=22 mm, 7.2 mm behind the nominal camera-body rear, and the optical sidewalls are held by low rear spines. Only the test-irrelevant rear roof and rear rain baffle are omitted to reduce print time and material.

The front roof and sidewall geometry is at the same coordinate relationship that a later full hood must use. The coupon itself is **not** a deployable rainhood and cannot establish rear connector rain protection.

## Fixed v002 datums

- v002 front edge: Y = -60.4 mm
- tripod axis: X = 0.15 mm, Y = 0 mm
- camera body reference: X = 0 mm, Y = -2.2 mm, body bottom Z = 17.2 mm
- folded safe envelope: front/rear Y = -30.4 / 26.0 mm; total H = 52.7 mm
- carrier: 110.8 x 74 x 6 mm
- hood inner/outer width: 112 / 118 mm
- top clearance datum: 4 mm at the folded-safe-front reference
- shell M4 centers: X = +/-44 mm, Y = 33 mm
- slide lateral/vertical clearance: 0.6 / 0.8 mm

Values are transcribed from the exact v002 source named in `docs/SOURCE_PROVENANCE.md`, not inferred from the brief.

## Generate

Known generation environment:

```powershell
& 'C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe' `
  'D:\Paddy_Swarm_Project\cad\ps_webcam_rainhood_v003_optical_clearance\source\ps_webcam_rainhood_v003.py'
```

One source generates all STL, STEP, reports, and side-view comparison images. Generation aborts on authority drift, invalid BRep, multi-solid output, empty or non-manifold STL, camera/carrier interference, bevel mismatch, or candidate/identifier duplication.

## Print guidance

- Material: PETG, matching the v002 development intent.
- Start with 0.20 mm layers, at least 3 walls, and 20-30% infill.
- Inspect the thin beveled leading edge in the slicer before printing.
- Preserve the model scale at 100%.
- A/B/C may be put on one plate only if the slicer confirms build-volume clearance, stable orientation, and acceptable supports; the 1/2/3 exterior ribs remain the authoritative physical IDs.
- Do not interpret a successful print as optical or rain approval.

Follow `docs/PHYSICAL_TEST_PROTOCOL.md` using the same v002 carrier and tripod screw. Record left, center, right, and mount-play intrusion separately.

## Pass levels

- `CAD_PASS`: established only by the generated validation report.
- `PRINT_PENDING`
- `FIT_PENDING`
- `OPTICAL_PENDING`
- `RAIN_PENDING`
- `FIELD_PENDING`

`OPTICAL_PASS`, `RAIN_PASS`, and `FIELD_PASS` are not declared.

