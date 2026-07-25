# Dummy Panicle v0.1.3-panicle-head Interface Report

All dimensions are millimetres.  No repository evidence of a successful
printed fit or measured mass was found, so all listed fit values remain
`CALIBRATION_PENDING`.  Powered cutting is not authorized by this revision.

## Shared interfaces

- `STEM-NOMINAL-4`: 4.0 shaft, 4.3 provisional receiver, 20 insertion.
- `PANICLE-TAB-V001`: TPU tab 8.0 x 2.0 x 14; provisional PETG slot
  8.4 x 2.4 x 12 deep.
- A1 conservative envelope: 240 x 240 x
  220; nozzle 0.4; standard layer
  0.20.
- PETG wall target 2.0; TPU minimum
  0.8.  DR-H03 uses its explicitly permitted 1.5 mm
  minimum flange thickness.

## Existing calibration coupon maps

| Stem label | Hole diameter |
|---:|---:|
| 1 | 4.10 |
| 2 | 4.20 |
| 3 | 4.30 |
| 4 | 4.40 |
| 5 | 4.50 |

| Slot label | Width | Thickness |
|---:|---:|---:|
| 1 | 8.2 | 2.4 |
| 2 | 8.4 | 2.4 |
| 3 | 8.6 | 2.4 |
| 4 | 8.4 | 2.2 |
| 5 | 8.4 | 2.6 |

## Existing interfaces retained

- DR-B01 remains the fixed 0-degree MEDIUM root socket.
- DR-S03 exports preset `tube_id_3p6_calibration`.  Its mating ID is unmeasured
  and it is not guaranteed to be the same material or stock as the DR-C01
  nominal 4.0 OD / 2.5 ID cartridge tube.
- DR-C01 uses two identical holders.  Its 4.10 cartridge bore and 4.30 stem
  bore are calibration candidates and do not guarantee retention.
- Cartridge equation: 170 =
  2 x 15 +
  2 x 30 +
  80.
- The 30 mm datum begins at the cartridge-side PETG face nearest the nominal
  blade zone, not the outside/stem-side holder face.
- The removable PETG gauge is only for drawing lines directly on the paper
  tube or non-cutting bench visualization.  Remove it afterward.  It is
  prohibited near a blade and for powered cutting.

## Panicle head interfaces

- DR-H01: four 8.0 x 2.0 x 14 TPU tabs in service; print one first for fit,
  then print six including spares.
- DR-H02: four 8.4 x 2.4 x 12 top-entry slots at 90-degree intervals.
- DR-H02 nominal 24 mm OD did not satisfy the simultaneous 2 mm wall
  constraints.  Both fixed presets therefore use the permitted 30.0 mm OD.
- DR-H02 stem interface is fixed 0 degrees (`upright`) or fixed 20 degrees
  (`droop20`); there is no moving hinge.
- DR-H03 uses a 7.8 mm plug and 8.2 mm shallow bead in the uncalibrated
  8.0 mm pocket.  Its 0.20 mm diametral interference candidate does not
  guarantee retention.
- TPU branches must never contact a rotating blade.

## Export validation

- STL linear/angular tolerances: 0.05 /
  0.10.
- Every printable STEP is re-imported as one valid positive-volume solid.
- Preview STEP compounds are re-imported with seven component solids and are
  explicitly non-printable.
- Compact DR-C01 outer-stem socket depth:
  9.2.
