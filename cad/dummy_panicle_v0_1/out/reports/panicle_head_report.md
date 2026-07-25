# Panicle Head v0.1 Report (v0.1.3-panicle-head)

Status: `CALIBRATION_PENDING`.  CAD geometry and export validation are
complete; printed fit, retention, durability, centre of gravity, and mass are
not measured.

## DR-H01 TPU panel

- 79.127 x 195.000 x 2.000; V=1277.362 mm3; solids=1; estimate=1.546 g
- Length 195.0; measured maximum one-sided width
  40.631; panel/neck minimum thickness
  1.0/0.8.
- 10 deterministic lateral branches and 14 connected capsule grains.
- Standard assembly uses 4 panels (56 grains); recommended print quantity is
  6.  Print one panel first and calibrate the tab/slot fit.

## DR-H02 PETG hub

- Upright: 30.000 x 30.000 x 28.000; V=17641.649 mm3; solids=1; estimate=22.405 g
- Droop20: 30.000 x 30.000 x 28.000; V=17838.428 mm3; solids=1; estimate=22.655 g
- 30.0 OD x 28.0 high; four provisional 8.4 x 2.4 x 12 slots; provisional
  4.3 stem hole x 20; 1.2 split; 3.2 M3 through-hole and M3 nut trap.
- The requested 24 mm OD cannot preserve the required outer wall around the
  chamfered slot corners.  The calculated minimum is approximately 29.6 mm
  for both presets; the permitted rounded value 30.0 mm was adopted.
- Weight pocket: 8.0 diameter x 6.0 deep,
  301.593 mm3 nominal capacity.

| Conservative clearance | upright | droop20 |
|---|---:|---:|
| slot_outer_wall | 2.215 | 2.215 |
| adjacent_slot_gap | 5.728 | 5.728 |
| slot_to_pocket | 4.850 | 4.850 |
| stem_to_slot | 7.300 | 2.092 |
| stem_to_pocket | 2.000 | 2.099 |
| nut_trap_to_stem | 2.050 | 2.050 |
| nut_trap_outer_wall | 4.400 | 4.400 |

All reported cavity/wall clearances are at least 2.0 mm.  The 20-degree model
tilts the single stem interface, so the whole four-panel head droops together.

## DR-H03 PETG cap

- 12.117 x 12.200 x 6.000; V=390.124 mm3; solids=1; estimate=0.495 g
- 12.2 flange OD x 6.0 high; 7.8 plug; 8.2 shallow bead; diametral candidate
  interference 0.20.
- The cap is tool-removable through a shallow flange-edge notch.  Retention is
  not guaranteed before printed fit and shake tests.

## Panicle-only previews

- upright: 81.262 x 81.262 x 219.000 mm; 7 solids; `preview/panicle_assembly_upright.step`
- droop20: 85.584 x 84.904 x 208.736 mm; 7 solids; `preview/panicle_assembly_droop20.step`

Each preview contains DR-H01 x4, DR-H02 x1, DR-H03 x1, and one simple 4 mm
stem.  Panel orientations are 0/90/180/270 degrees, insertion is 12 mm, and
pairwise panel intersection is zero.  Preview STEP files are not printable
parts and no preview STL is generated.  PNG rendering was not executed because
the existing workflow does not provide a required renderer and no dependency
was added.

## Provisional CAD mass estimate

- Density settings: TPU 95A 1.210 g/cm3; PETG
  1.270 g/cm3; status `ESTIMATE_ONLY_MEASURE_PRINTED_PARTS`.
- Head without simple preview stem or metal weights: upright
  29.083 g; droop20 29.333 g.
- Both estimates exceed the 4-6 g target.  The largest contribution is the
  DR-H02 hub, followed by four DR-H01 panels.  The pocket can only add measured
  metal mass; it cannot reduce the base mass.
- This is not a measured failure determination.  Slicer perimeter/infill
  behaviour, extrusion, and printed material density remain unknown.  No
  fit or mass acceptance may be claimed until real parts are printed and
  weighed; later lightweighting would require a separately reviewed geometry
  revision.

## Safety

Powered cutting is not authorized.  TPU panicle branches must never contact a
rotating blade.  Secure any metal pocket contents and verify cap retention
before hand-motion testing.  Avoid over-tightening the M3 clamp.
