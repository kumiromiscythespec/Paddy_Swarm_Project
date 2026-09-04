# VALIDATION REPORT

Status: `CAD_COMPLETE_TPU_STORM_SKIN_PHYSICAL_VALIDATION_PENDING`

CAD and interface checks pass. Acoustic, anchor, peel, uplift, rain, field wind, and aging are physical validation items.

## STL/BRep

| Artifact | Expected solids | BRep solids | STL triangles | Boundary/non-manifold edges |
|---|---:|---:|---:|---:|
| `storm_skin_anchor_coupon_v005_petg` | 1 | 1 | 1468 | 0 |
| `storm_skin_anchor_coupon_v005_tpu` | 1 | 1 | 1340 | 0 |
| `tpu_acoustic_coupon_1p0` | 1 | 1 | 452 | 0 |
| `tpu_acoustic_coupon_1p5` | 1 | 1 | 876 | 0 |
| `tpu_acoustic_coupon_2p0` | 1 | 1 | 1300 | 0 |
| `tpu_preload_strap_coupon_v005` | 3 | 3 | 3972 | 0 |
| `rainhood_tpu_storm_skin_v005` | 1 | 1 | 3644 | 0 |
| `rainhood_b15_storm_anchor_v005` | 1 | 1 | 7752 | 0 |

## STEP re-import

- `storm_skin_anchor_coupon_v005`: valid=True, solids=2
- `rainhood_tpu_storm_skin_v005`: valid=True, solids=1
- `rainhood_b15_storm_anchor_v005`: valid=True, solids=1
- `storm_skin_assembly_v005`: valid=True, solids=5

## Interface and interference

- `camera_vs_installed_TPU_mm3`: 0.00000000 mm^3
- `optical_exclusion_vs_installed_TPU_mm3`: 0.00000000 mm^3
- `USB_route_vs_installed_TPU_mm3`: 0.00000000 mm^3
- `carrier_vs_installed_TPU_mm3`: 0.00000000 mm^3
- `v005_anchor_hood_vs_installed_TPU_mm3`: 0.00000000 mm^3
- `anchor_coupon_PETG_vs_TPU_mm3`: 0.00000000 mm^3
- v004 hood removed volume: 0.00000000 mm^3
- external anchor geometry added: 1553.721 mm^3
- TPU nose margin above B optical interior: 2.000 mm

## Checks

- `v004_optical_front_y_unchanged`: PASS
- `v004_bevel_unchanged`: PASS
- `v004_hood_geometry_not_removed`: PASS
- `only_external_anchor_geometry_added_to_hood`: PASS
- `tripod_and_carrier_authority_unchanged`: PASS
- `USB_route_unchanged`: PASS
- `camera_TPU_interference_zero`: PASS
- `optical_TPU_interference_zero`: PASS
- `USB_TPU_interference_zero`: PASS
- `carrier_TPU_interference_zero`: PASS
- `hood_TPU_no_solid_overlap`: PASS
- `anchor_coupon_clearance_no_overlap`: PASS
- `nose_stays_above_B_optical_interior`: PASS
- `four_mechanical_anchors`: PASS
- `no_roof_penetration`: PASS
- `adhesive_not_primary`: PASS
- `roof_membrane_min_1p5`: PASS
- `anchor_tab_min_2p5`: PASS
- `anchor_head_width_10_to_12`: PASS
- `anchor_root_width_min_10`: PASS
- `anchor_root_min_R2`: PASS
- `cavity_clearance_positive`: PASS
- `preload_X_parameterized`: PASS
- `preload_Y_parameterized`: PASS
- `flat_pattern_reduced_X`: PASS
- `flat_pattern_reduced_Y`: PASS
- `rear_corner_drainage_reliefs_present`: PASS
- `installed_numeric_contact_clearance_is_small`: PASS
- `wind_result_not_certified`: PASS

## Pass separation

- `CAD_PASS`: PASS
- `TPU_ANCHOR_PHYSICAL_PASS`: NOT PASSED / PENDING
- `TPU_RAIN_NOISE_REDUCTION_PHYSICAL_PASS`: NOT PASSED / PENDING
- `TPU_STORM_SKIN_BENCH_RETENTION_PASS`: NOT PASSED / PENDING
- `FIELD_WIND_VALIDATION_PASS`: NOT PASSED / PENDING
- `WIND_DRIVEN_RAIN_PASS`: NOT PASSED / PENDING
- `UV_WEATHER_AGING_PASS`: NOT PASSED / PENDING

No certified wind rating is declared.
