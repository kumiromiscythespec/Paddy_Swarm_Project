# Validation report

Status: `CAD_COMPLETE_OPTICAL_COUPON_PHYSICAL_VALIDATION_PENDING`

This report proves CAD generation and mechanical-datum consistency only. It does not prove optical, rain, or field performance.

| Candidate | BRep | Solids | STEP reimport | STL triangles | Watertight edge check | Camera interference | Carrier interference | Physical optical |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| A | PASS | 1 | PASS | 1976 | PASS | 0.00000000 mm^3 | 0.00000000 mm^3 | PENDING |
| B | PASS | 1 | PASS | 1992 | PASS | 0.00000000 mm^3 | 0.00000000 mm^3 | PENDING |
| C | PASS | 1 | PASS | 2008 | PASS | 0.00000000 mm^3 | 0.00000000 mm^3 | PENDING |

Set checks:

- `three_candidates_generated`: PASS
- `candidate_stl_hashes_are_distinct`: PASS
- `candidate_brep_volumes_are_distinct`: PASS
- `candidate_front_bounds_are_distinct`: PASS
- `identifier_counts_are_1_2_3`: PASS
- `front_setbacks_are_10_15_20`: PASS
- `v002_interface_authority_exact_match`: PASS
- `same_interface_builder_used_for_all_candidates`: PASS

Pass separation:

- CAD_PASS: PASS
- PRINT_PENDING: YES
- FIT_PENDING: YES
- OPTICAL_PENDING: YES
- RAIN_PENDING: YES
- FIELD_PENDING: YES
- OPTICAL_PASS / RAIN_PASS / FIELD_PASS: NOT DECLARED
