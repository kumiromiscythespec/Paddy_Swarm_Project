# VALIDATION REPORT

Status: `CAD_COMPLETE_USB_RAINCOVER_PHYSICAL_VALIDATION_PENDING`

CAD geometry/mesh/STEP checks pass. Print, fit, drainage, spray, field, and long-duration results remain physical PENDING.

## STL and BRep

| Artifact | Expected solids | BRep solids | STL triangles | Boundary/non-manifold edges |
|---|---:|---:|---:|---:|
| `connector_chamber_fit_coupon_v001` | 2 | 2 | 220 | 0 |
| `cable_channel_coupon_small_v001` | 1 | 1 | 704 | 0 |
| `cable_channel_coupon_large_v001` | 1 | 1 | 672 | 0 |
| `labyrinth_drain_coupon_v001` | 1 | 1 | 2370 | 0 |
| `usb_raincover_upper_v001` | 1 | 1 | 4236 | 0 |
| `usb_raincover_lower_v001` | 1 | 1 | 6426 | 0 |

## STEP re-import

- `connector_chamber_fit_coupon_v001`: valid=True, solids=2
- `labyrinth_drain_coupon_v001`: valid=True, solids=1
- `usb_raincover_upper_v001`: valid=True, solids=1
- `usb_raincover_lower_v001`: valid=True, solids=1
- `usb_raincover_assembly_v001`: valid=True, solids=2

## Dimensional and water-path checks

- `chamber_known_width_fits`: PASS
- `known_width_side_clearance_positive`: PASS
- `small_cable_channel_fits`: PASS
- `large_cable_channel_fits`: PASS
- `small_cable_not_hard_clamped`: PASS
- `large_cable_not_hard_clamped`: PASS
- `drain_diameter_minimum`: PASS
- `drain_count_two`: PASS
- `roof_wall_minimum`: PASS
- `parting_clearance_fdm_range`: PASS
- `parting_step_minimum`: PASS
- `parting_overlap_geometry_exact`: PASS
- `top_overlap_skirt_in_range`: PASS
- `floor_slope_in_range`: PASS
- `roof_slope_positive`: PASS
- `downward_ports_outside_chamber`: PASS
- `drains_outside_chamber_and_offset`: PASS
- `baffle_between_port_and_chamber`: PASS
- `labyrinth_horizontal_run_exact`: PASS
- `labyrinth_vertical_offset_exact`: PASS
- `minimum_bend_space_available`: PASS
- `no_straight_outside_connector_line`: PASS
- `gravity_path_exists`: PASS
- `no_intended_closed_low_pocket`: PASS
- `roof_has_no_screw_penetration`: PASS
- `m3_four_point_closure`: PASS
- `upper_lower_no_solid_interference`: PASS
- `unknown_length_not_declared_physical`: PASS
- `unknown_height_not_declared_physical`: PASS
- `waterproof_not_claimed`: PASS

## Known versus unknown

- Connector known width total clearance: 5.300 mm
- Connector known width side clearance: 2.650 mm/side
- Small cable diametral clearance: 1.000 mm
- Large cable diametral clearance: 1.100 mm
- Connector length, height, shape detail, rigid/flexible boundary, and strain-relief length remain UNKNOWN_PHYSICAL.
- Chamber 50 x 24 x 16 mm is PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED.

## Pass separation

- `CAD_PASS`: PASS
- `PRINT_PASS`: NOT PASSED / PENDING
- `FIT_PASS`: NOT PASSED / PENDING
- `DRAIN_PASS`: NOT PASSED / PENDING
- `TOP_RAIN_PASS`: NOT PASSED / PENDING
- `45_DEG_RAIN_PASS`: NOT PASSED / PENDING
- `CABLE_WATER_PASS`: NOT PASSED / PENDING
- `HEAVY_RAIN_FIELD_PASS`: NOT PASSED / PENDING
- `LONG_DURATION_PASS`: NOT PASSED / PENDING

`WATERTIGHT_STL != WATERPROOF_PRINT`. No IP or immersion rating is declared.
