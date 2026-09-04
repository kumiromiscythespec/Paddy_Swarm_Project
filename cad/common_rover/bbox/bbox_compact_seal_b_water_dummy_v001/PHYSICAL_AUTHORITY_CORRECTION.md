# Corrected physical test authority

Source: user correction following the fail-closed STEP/STL audit. This document is a delta authority in a new lane; it does not patch the source V003 documents or artifacts.

## Mapping

- Coupon A: documented/nominal groove 0.45 mm; actual source rim Z8.00, floor Z7.45; actual groove 0.55 mm; physical dry PASS.
- Coupon B: documented/nominal groove 0.55 mm; actual source rim Z8.00, floor Z7.35; actual groove 0.65 mm; physical dry PASS.
- Selected full body: rim Z113.50, floor Z113.00; actual groove 0.50 mm; physical seal NOT TESTED.

For both tested coupons the user observed normal hard-stop closure, no major gasket extrusion, no PETG whitening, ten open/close cycles and no gasket cut/damage. The actual G065 Coupon B was preferred for practical cord positioning. These are dry observations, not water performance.

## New candidates

- WATER_DUMMY_G065: exact 0.65 mm actual depth; PRIMARY water-test candidate. Calculated compression is 1.8 − 0.65 − 0.895 = 0.255 mm, 14.1667%.
- WATER_DUMMY_G055: exact 0.55 mm actual depth; comparison. Calculated compression is 1.8 − 0.55 − 0.895 = 0.355 mm, 19.7222%.

Ratios are CALCULATED_REFERENCE only. Actual rubber deformation, retention and water performance must be observed.

## Promotion logic

- G065 passing all water criteria permits the user to record `COMPACT_SEAL_G065_WATER_PHYSICAL_PASS`.
- If G055 also passes, record G055 separately; compare retention, compression and repeated closure behavior.
- If only G065 passes, select 0.65 mm for the NEXT full-body seal correction.
- If only G055 passes, select 0.55 mm and document that the deeper G065 lost water performance.
- If both fail, do not release full BBOX print.
- After a physical winner exists, create a NEW corrected Compact Field BBOX lane. Its actual groove must match the winning dummy and pass the same STEP measurement regression. Do not silently patch V003 or replace its existing 0.50 mm groove.

No water result, full-box release, chimney/PG9 qualification or field approval is claimed by this lane.
