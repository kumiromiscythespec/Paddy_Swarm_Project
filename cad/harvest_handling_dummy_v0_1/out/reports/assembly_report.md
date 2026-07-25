# PS-HARVEST-HANDLING-DUMMY-V001 Standard Assembly Report

## Fixed layout

- 24 unique independent sockets; six per module.
- Minimum centre spacing: 21.000 mm.
- Radial layout diameter: 144.803 mm.
- Radial bands: {'CENTER_LE_45': 10, 'MID_45_TO_60': 9, 'OUTER_60_TO_75': 5}.
- Forbidden symmetry checks: {'x_axis': False, 'y_axis': False, 'rotation_180': False}.
- Socket outer-surface minimum clearance:
  2.595 mm.
- Projected upper-stem crossing pairs:
  25.

| Socket | Module | X | Y | Tilt | Direction | Height |
|---|---|---:|---:|---:|---:|---|
| S01 | A | -15.0 | 15.0 | 20 | 0 | HIGH |
| S02 | A | -36.0 | 15.0 | 0 | 135 | LOW |
| S03 | A | -15.0 | 37.0 | 10 | 270 | STANDARD |
| S04 | A | -57.0 | 15.0 | 30 | 45 | LOW |
| S05 | A | -39.0 | 39.0 | 10 | 180 | HIGH |
| S06 | A | -60.0 | 40.0 | 0 | 315 | STANDARD |
| S07 | B | 15.0 | 15.0 | 10 | 90 | STANDARD |
| S08 | B | 36.0 | 15.0 | 20 | 225 | HIGH |
| S09 | B | 57.0 | 15.0 | 0 | 0 | LOW |
| S10 | B | 15.0 | 44.0 | 10 | 315 | STANDARD |
| S11 | B | 39.0 | 39.0 | 20 | 135 | LOW |
| S12 | B | 60.0 | 40.0 | 0 | 270 | HIGH |
| S13 | C | -15.0 | -15.0 | 20 | 0 | STANDARD |
| S14 | C | -37.0 | -15.0 | 10 | 45 | LOW |
| S15 | C | -15.0 | -38.0 | 0 | 225 | STANDARD |
| S16 | C | -58.0 | -15.0 | 30 | 90 | HIGH |
| S17 | C | -40.0 | -40.0 | 10 | 315 | LOW |
| S18 | C | -61.0 | -39.0 | 20 | 180 | STANDARD |
| S19 | D | 15.0 | -15.0 | 0 | 180 | HIGH |
| S20 | D | 37.0 | -15.0 | 10 | 270 | STANDARD |
| S21 | D | 15.0 | -44.0 | 20 | 90 | LOW |
| S22 | D | 40.0 | -40.0 | 0 | 135 | STANDARD |
| S23 | D | 61.0 | -39.0 | 10 | 45 | LOW |
| S24 | D | 15.0 | -65.0 | 0 | 225 | STANDARD |

## Preview

- Mount nominal plates are 105 x 210 x 6 mm.  The left seam tongue produces
  a 110 x 210 x 9 mm functional feature envelope and the locating pins produce
  a 105 x 210 x 9 mm right envelope; the joined footprint remains
  210 x 210 mm and both halves remain A1-safe.
- Bounding box: 616.144 x 625.012 x
  902.000 mm.
- Component solids: 54 =
  mount 2 + base 4 + socket 24 + virtual commercial stem 24.
- Heights: {'HIGH': 6, 'LOW': 8, 'STANDARD': 10}.
- Tilts: {20.0: 6, 0.0: 8, 10.0: 8, 30.0: 2}.
- Directions: {0.0: 3, 135.0: 3, 270.0: 3, 45.0: 3, 180.0: 3, 315.0: 3, 90.0: 3, 225.0: 3}.
- File: `preview/HU-H0-HHD_standard_fixed_root.step`.
- `printable=false`; no preview STL is generated.
- PNG was not generated and no rendering dependency was added.

This is a fixed-root gathering/holding/transport handling dummy only.  It does
not authorize powered cutting.
