# BBOX XY source audit

The repository contains many BBOX placements, but no current direct physical BBOX X or Y locator relative to a repeatable rover frame face.

| Source/value | Classification | Current physical authority? | Reason |
|---|---|---|---|
| Cross Saddle `bbox_placed()` leaves X/Y at `(0,0)` | DERIVED_MOUNT_ASSUMPTION | No | Function applies only `Tz=254-8`; no physical XY measurement source. |
| Cross Saddle local rail centres `Y=±94.5` | DERIVED_MOUNT_ASSUMPTION | No | Based on the 189 mm reporting midpoint; its own JSON says local datum, not absolute vehicle Y authority. |
| v0.8 `bbox_center_x_mm=-75`, `Y=0` | HISTORICAL / CAD_ONLY | No | Design-candidate placement. |
| v0.9.0 BBOX centre `[-225,0,275]` | HISTORICAL / CAD_ONLY | No | Powertrain design model, not a current measurement. |
| v0.9.4.1 BBOX `center_x=-100`, `Y=0` | PROVISIONAL / CAD_ONLY | No | Integration CAD candidate. |
| v0.9.5.0 installed model translation `(-100,0,0)` | CAD_ONLY | No | Prototype assembly transform. |
| v0.9.5.2 lateral offset `2.5 mm` | DERIVED_REFERENCE_ONLY | No | Ledger explicitly says left/right datum not established. |
| v0.9.6.7 rapid-dry BBOX translation `(-140,0,0)` | CAD_ONLY | No | Temporary dry-fixture model. |
| Physical rail inside/outside spans 168–170 / 208–210 | PHYSICAL_DIRECT_RANGE | Partial context only | Locates rail separation, not BBOX faces or absolute vehicle centreline. |

Search result:

- `BBOX_X_PHYSICAL_DIRECT_COUNT = 0`
- `BBOX_Y_PHYSICAL_DIRECT_COUNT = 0`
- `INDEPENDENT_BBOX_XY_PHYSICAL_DATUM_COUNT = 0`
- required count for registration: at least `2`

Consequently:

- `BBOX_INSTALLED_X = HOLD_PHYSICAL_MEASUREMENT_REQUIRED`
- `BBOX_INSTALLED_Y = HOLD_PHYSICAL_MEASUREMENT_REQUIRED`
- `BBOX_INSTALLED_RX/RY/RZ = HOLD` unless current mounting faces demonstrate the assumed alignment.

Old CAD placements remain useful history but are not promoted.
