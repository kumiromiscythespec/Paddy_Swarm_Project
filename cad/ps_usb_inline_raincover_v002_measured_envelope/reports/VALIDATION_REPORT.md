# VALIDATION REPORT

Status: `CAD_COMPLETE_MEASURED_ENVELOPE_PHYSICAL_VALIDATION_PENDING`

Measured dimensions and inherited v001 architecture pass CAD validation. Connector-chamber, drain, full-shell spray, and powered tests remain Physical PENDING.

## STL/BRep

| Artifact | Expected solids | BRep solids | STL triangles | Boundary/non-manifold edges |
|---|---:|---:|---:|---:|
| `connector_chamber_fit_coupon_v002` | 2 | 2 | 1884 | 0 |
| `labyrinth_drain_coupon_v002` | 1 | 1 | 2796 | 0 |
| `usb_raincover_upper_v002` | 1 | 1 | 5180 | 0 |
| `usb_raincover_lower_v002` | 1 | 1 | 8368 | 0 |

## STEP re-import

- `connector_reference_v002`: valid=True, solids=1
- `connector_chamber_fit_coupon_v002`: valid=True, solids=2
- `labyrinth_drain_coupon_v002`: valid=True, solids=1
- `usb_raincover_upper_v002`: valid=True, solids=1
- `usb_raincover_lower_v002`: valid=True, solids=1
- `usb_raincover_assembly_v002`: valid=True, solids=5

## Interference

- `connector_vs_upper_mm3`: 0.00000000 mm3
- `connector_vs_lower_mm3`: 0.00000000 mm3
- `camera_cable_vs_upper_mm3`: 0.00000000 mm3
- `camera_cable_vs_lower_mm3`: 0.00000000 mm3
- `extension_cable_vs_upper_mm3`: 0.00000000 mm3
- `extension_cable_vs_lower_mm3`: 0.00000000 mm3
- `upper_vs_lower_mm3`: 0.00000000 mm3
- `connector_vs_fit_coupon_lower_mm3`: 0.00000000 mm3
- `connector_vs_fit_coupon_upper_mm3`: 0.00000000 mm3

## Checks

- `v001_authority_hashes_match`: PASS
- `v001_roof_slope_preserved`: PASS
- `v001_floor_slope_preserved`: PASS
- `v001_skirt_preserved`: PASS
- `v001_parting_step_preserved`: PASS
- `v001_parting_overlap_preserved`: PASS
- `v001_parting_clearance_preserved`: PASS
- `v001_labyrinth_run_preserved`: PASS
- `v001_labyrinth_offset_preserved`: PASS
- `v001_drain_preserved`: PASS
- `chamber_length_requirement`: PASS
- `chamber_width_requirement`: PASS
- `chamber_height_requirement`: PASS
- `axial_clearance_exact`: PASS
- `width_clearance_exact`: PASS
- `height_clearance_exact`: PASS
- `camera_channel_authority_4p4`: PASS
- `extension_channel_authority_4p4`: PASS
- `camera_cable_fits`: PASS
- `extension_cable_fits`: PASS
- `drain_d_exact`: PASS
- `parting_step_exact`: PASS
- `parting_overlap_exact`: PASS
- `skirt_exact`: PASS
- `floor_crown_recomputed`: PASS
- `connector_all_shell_interferences_zero`: PASS
- `connector_fit_coupon_interference_zero`: PASS
- `cable_reference_interferences_zero`: PASS
- `upper_lower_interference_zero`: PASS
- `fit_coupon_material_reduced`: PASS
- `m3_six_closure_selected`: PASS
- `max_axial_fastener_station_span_50`: PASS
- `roof_transverse_span_unchanged`: PASS
- `saddle_has_positive_gap_to_measured_envelope`: PASS
- `saddle_remains_inside_chamber`: PASS
- `saddle_is_loose_not_hard_clamp`: PASS
- `waterproof_not_claimed`: PASS

## Pass separation

- `CAD_PASS`: PASS
- `PRINT_PASS`: NOT PASSED / PENDING
- `CABLE_FIT_PASS`: PASS
- `CONNECTOR_FIT_PASS`: NOT PASSED / PENDING
- `DRAIN_PASS`: NOT PASSED / PENDING
- `SPRAY_PASS`: NOT PASSED / PENDING
- `POWERED_USB_PASS`: NOT PASSED / PENDING
- `HEAVY_RAIN_FIELD_PASS`: NOT PASSED / PENDING
- `LONG_DURATION_PASS`: NOT PASSED / PENDING

No waterproof/IP/heavy-rain/long-duration claim is made.
