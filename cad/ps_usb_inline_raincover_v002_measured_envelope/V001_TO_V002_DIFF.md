# V001 TO V002 DIFF

## Changed

| Item | v001 | v002 | Disposition / reason |
|---|---:|---:|---|
| chamber length | 50.0 mm | 102.0 mm | measured 95.1 mm protected span; `MEASURED_ENVELOPE_REQUIRED_CHANGE` |
| camera cable OD | 3.6 mm | 3.8 mm | physical measurement |
| extension cable OD | 7.9 mm | 4.0 mm | physical measurement supersedes provisional value |
| camera channel | 4.6 mm nominal | 4.4 mm | v001 coupon physical PASS |
| extension channel | 9.0 mm | 4.4 mm | 9.0 no longer required; v001 coupon physical PASS |
| connector envelope Authority | none | 95.1 × 18.7 × 10.8 mm | rigid-to-flexible protected bounding envelope |
| floor center crown | 0.873 mm | 1.781 mm | recalculated for 102 mm two-way 2° floor |
| loose cable saddles | x = ±21 mm, 5 mm long | x = ±49.275 mm, 3 mm long | keep outside 95.1 mm envelope |
| closure | M3×4 | M3×6 | central seam-span control; `MEASURED_ENVELOPE_REQUIRED_CHANGE` |

## Preserved

- chamber width 24 mm and height 16 mm
- PETG upper/lower clamshell and lower flat print base
- 3° roof, no roof penetration, 6 mm umbrella skirt
- center-high bilateral 2° floor drainage concept
- downward cable ports, 10 mm drip vestibule/run, 5 mm vertical offset
- terminal baffle and no straight line-of-sight water path
- Ø2.5 mm drains ×2 and offset weep path
- 2 mm parting step, 3 mm radial overlap, 0.30 mm clearance
- external side-flange M3 closure with captured hex nuts

## Superseded provisional records

`V001 CHAMBER nominal length = 50.0 mm` versus `physical required envelope length = 95.1 mm`: `REJECTED_UNDERSIZED`. This is not a CAD failure; it is `PROVISIONAL_DIMENSION_SUPERSEDED_BY_PHYSICAL_MEASUREMENT`.

The 7.9 mm cable value is `SUPERSEDED_BY_PHYSICAL_MEASUREMENT`; the 9.0 mm large channel is `NO_LONGER_REQUIRED` in v002 full geometry.
