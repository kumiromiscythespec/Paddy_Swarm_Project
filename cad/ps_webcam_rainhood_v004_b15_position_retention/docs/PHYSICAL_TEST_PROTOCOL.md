# PHYSICAL TEST PROTOCOL

Current status: `CAD_COMPLETE_B15_POSITION_RETENTION_PHYSICAL_VALIDATION_PENDING`

## Stage 1 — print the coupon first

Print only `b15_position_retention_coupon_v004.stl` initially. Confirm the permanent ID is four exterior ribs.

Recommended baseline: Bambu Lab A1, PETG, 0.4 mm nozzle, 0.20 mm layers, at least three walls. Place the flat left exterior side/spine on the build plate with identifier ribs upward. Review every layer around the bevel, side guides, front/rear stops, tripod access, USB opening, and carrier underside. Auto-support approval is not sufficient.

## Coupon inspection before camera installation

1. Check BRep-derived dimensions were not rescaled in the slicer.
2. Remove support/stringing without sanding guide inner faces selectively.
3. Inspect guide roots, rounded ends, front stops, tripod hole, and seating plane for cracks or elephant-foot intrusion.
4. Reject the print if the carrier seating plane rocks or the guide faces are visibly damaged.

## B15 POSITION RETENTION TEST

1. Seat the camera without forcing it.
2. Record guide contact: `NONE / LIGHT / HARD`.
3. Confirm full seating and tripod screw access.
4. Install the same verified hardware practice used for v002; thread physical status remains pending unless measured separately.
5. Display the camera preview with fixed resolution, crop, zoom, rotation, and stabilization settings.
6. Establish the normal near-horizontal pose used in v003.
7. Record nominal upper-left, upper-center, and upper-right intrusion.
8. Apply normal hand disturbance in left/right translation and CW/CCW yaw.
9. Apply a light maintained hand load and inspect all three top regions.
10. Release the load and confirm return to the seated position.
11. Remove and reinstall three times; repeat nominal FOV inspection each time.
12. Inspect the camera case and PETG guides for marks, cracks, whitening, or permanent set.
13. Complete `reports/POSITION_RETENTION_TEST_SHEET.md`.

## Coupon PASS criteria

All are required:

1. nominal FOV intrusion is none;
2. guide contact is none or light;
3. no large lateral/yaw shift under normal hand disturbance;
4. after light load release, the camera returns to the normal seat;
5. three remove/reinstall cycles do not reproduce FOV intrusion;
6. no camera damage;
7. tripod screw remains removable.

`HARD` contact, forced seating, damage, unrecoverable shift, or repeatability failure is not a pass.

## Stage 2 — one full prototype only after coupon PASS

After `PASS_POSITION_RETENTION`, print one `tripod_carrier_b15_v004.stl` and one `rainhood_b15_v004.stl`. Do not mass-produce.

Verify:

- nominal left/center/right top FOV;
- mount play and return to seat;
- USB route and drip loop;
- rain coverage visual inspection;
- top spray;
- 45-degree spray;
- cable-side and rear splash.

Do not declare field pass before actual outdoor rain/wind exposure.

## Fallback

If B requires hard press fit, remains shift-sensitive, fails reinstall repeatability, damages the housing, or lacks PETG strength, stop and propose `FALLBACK_TO_C_SETBACK20`.

