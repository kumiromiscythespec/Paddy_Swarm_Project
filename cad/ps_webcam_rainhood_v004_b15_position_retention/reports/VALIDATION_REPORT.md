# VALIDATION REPORT

Status: `CAD_COMPLETE_B15_POSITION_RETENTION_PHYSICAL_VALIDATION_PENDING`

CAD generation and authority preservation pass. Position retention, full-hood optical behavior, rain, field exposure, static load, and durability remain physical tests.

## Artifacts

| Artifact | BRep solids | STL triangles | Boundary/non-manifold edges | STEP reimport |
|---|---:|---:|---:|---|
| `b15_position_retention_coupon_v004` | 1 | 7192 | 0 | PASS |
| `tripod_carrier_b15_v004` | 1 | 7152 | 0 | PASS |
| `rainhood_b15_v004` | 1 | 1960 | 0 | PASS |

## Controlled delta

- v002 carrier geometry removed: 0.00000000 mm^3
- v004 retention geometry added: 573.772 mm^3
- v002 guide length: 44.0 mm
- v004 guide length: 52.4 mm
- guide/front-stop/rear-stop nominal clearance: 0.7 mm
- guide height: 2.8 mm
- tripod axis/hole, carrier seating plane, shell rails/stops/M4/nut traps, and USB relief: unchanged

## Interference

- `camera_vs_v004_carrier_mm3`: 0.00000000 mm^3
- `camera_vs_b15_hood_mm3`: 0.00000000 mm^3
- `carrier_vs_b15_hood_mm3`: 0.00000000 mm^3
- `camera_vs_integrated_coupon_mm3`: 0.00000000 mm^3

## Checks

- `v002_interface_authority_exact_match`: PASS
- `tripod_axis_unchanged`: PASS
- `tripod_hole_unchanged`: PASS
- `carrier_seating_plane_unchanged`: PASS
- `shell_interface_builder_is_v002_exact`: PASS
- `B_front_y_exact`: PASS
- `B_setback_exact`: PASS
- `B_bevel_exact`: PASS
- `B_bevel_run_matches_authority`: PASS
- `B_front_length_exact`: PASS
- `B_front_roof_matches_v003_exactly`: PASS
- `B_front_sidewalls_match_v003_exactly`: PASS
- `top_clearance_preserved`: PASS
- `guide_clearance_preserved_0p7`: PASS
- `front_stop_clearance_0p7`: PASS
- `rear_stop_clearance_0p7`: PASS
- `guide_height_preserved_2p8`: PASS
- `guide_extended_vs_v002`: PASS
- `v002_carrier_geometry_not_removed`: PASS
- `position_retention_geometry_added`: PASS
- `camera_carrier_interference_zero`: PASS
- `camera_hood_interference_zero`: PASS
- `carrier_hood_interference_zero`: PASS
- `camera_coupon_interference_zero`: PASS
- `coupon_identifier_is_4_ribs`: PASS
- `hard_press_fit_not_designed`: PASS
- `status_indicator_not_safety_feature`: PASS

## Pass separation

- `CAD_PASS`: PASS
- `PRINT_PASS`: NOT PASSED / PENDING
- `FIT_PASS`: NOT PASSED / PENDING
- `STATIC_PASS`: NOT PASSED / PENDING
- `POSITION_RETENTION_PHYSICAL_PASS`: NOT PASSED / PENDING
- `B15_FULL_HOOD_OPTICAL_PHYSICAL_PASS`: NOT PASSED / PENDING
- `RAIN_VISUAL_PASS`: NOT PASSED / PENDING
- `WATER_TEST_PASS`: NOT PASSED / PENDING
- `FIELD_PASS`: NOT PASSED / PENDING
- `DURABILITY_PASS`: NOT PASSED / PENDING

`B_setback15` remains `SELECTED_CONDITIONAL`. CAD does not close the mount lateral/yaw retention blocker.
