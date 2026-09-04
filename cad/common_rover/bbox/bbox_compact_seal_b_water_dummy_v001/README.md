# Compact perimeter water dummies: G065 primary / G055 comparison

This NEW isolated lane corrects the test-authority mapping without changing any existing CAD. It contains two closed, hollow PETG water dummies and one common lid. Only the actual groove bottom differs. Neither variant includes a chimney, gland, cable, vent or pressure-boundary penetration.

First print:

- `artifacts/water_dummy_g065_body.stl`
- `artifacts/water_dummy_common_lid.stl`

Then, for comparison, print `artifacts/water_dummy_g055_body.stl`. Keep the unmarked, dimensionally similar bodies identified by their filenames and removable labels on the exterior. Do not scratch/notch a seal surface to identify them. The common lid is identical for both.

| Printed-source identity | Documented depth | Actual STEP/STL depth | User physical result |
|---|---:|---:|---|
| Previous Coupon A | 0.45 mm | 0.55 mm | DRY PASS |
| Previous Coupon B | 0.55 mm | 0.65 mm | DRY PASS; preferred retention |
| Existing full BBOX | 0.50 mm | 0.50 mm | NOT TESTED |

The previous B result is NOT a 0.55 mm result. The closed water dummies have no water-test result yet. The existing full BBOX remains G050 and PRINT HOLD.

Run using the project CadQuery 2.8 environment and Python `-B`:

1. `python -B build_water_dummy.py --build`
2. `python -B tests/test_water_dummy.py --report`
3. `python -B build_water_dummy.py --audit-full --index`
4. `python -B build_water_dummy.py --verify`
5. `python -B build_water_dummy.py --package`

No command performs Git mutations. A new package uses exclusive creation and never overwrites an existing ZIP.

Authority status:

`SEAL_GEOMETRY_AUDIT_COMPLETE / COUPON_A_ACTUAL_G055_DRY_PASS / COUPON_B_ACTUAL_G065_DRY_PASS / G065_SELECTED_FOR_PRIMARY_WATER_TEST / FULL_BBOX_GROOVE_G050_UNVALIDATED / FULL_BBOX_PRINT_HOLD`

CAD/print status is separately recorded in the validation report. WATER PHYSICAL TEST PENDING.
