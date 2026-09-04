# VALIDATION REPORT

Status: `CAD_COMPLETE_OUTWARD_DRAIN_LABYRINTH_PHYSICAL_VALIDATION_PENDING`

v004 geometry passes CAD validation. Outward-drain coupon water validation remains Physical PENDING.

## STL / BRep

| Artifact | BRep valid | Solids | STL triangles | Boundary/non-manifold edges |
|---|---|---:|---:|---:|
| `outward_drain_labyrinth_coupon_lower_v004` | True | 1 | 3022 | 0 |
| `outward_drain_labyrinth_coupon_upper_v004` | True | 1 | 1634 | 0 |
| `usb_raincover_lower_v004` | True | 1 | 8818 | 0 |
| `usb_raincover_upper_v004` | True | 1 | 5832 | 0 |

## STEP re-import

- `outward_drain_labyrinth_coupon_v004`: valid=True, solids=2
- `usb_raincover_lower_v004`: valid=True, solids=1
- `usb_raincover_upper_v004`: valid=True, solids=1
- `usb_raincover_assembly_v004`: valid=True, solids=5

## Interference

- `connector_vs_lower_mm3`: 0.00000000 mm³
- `connector_vs_upper_mm3`: 0.00000000 mm³
- `camera_vs_lower_mm3`: 0.00000000 mm³
- `camera_vs_upper_mm3`: 0.00000000 mm³
- `extension_vs_lower_mm3`: 0.00000000 mm³
- `extension_vs_upper_mm3`: 0.00000000 mm³
- `upper_vs_lower_mm3`: 0.00000000 mm³
- `camera_top_load_sweep_vs_lower_mm3`: 0.00000000 mm³
- `extension_top_load_sweep_vs_lower_mm3`: 0.00000000 mm³
- `camera_release_sweep_vs_upper_mm3`: 0.00000000 mm³
- `extension_release_sweep_vs_upper_mm3`: 0.00000000 mm³
- `connector_placement_vs_lower_mm3`: 0.00000000 mm³

## Checks

- `v003_authority_hashes_match`: PASS
- `connector_and_chamber_authority_preserved`: PASS
- `4p4_channel_and_relief_preserved`: PASS
- `lower_floor_gravity_vector_outward`: PASS
- `lower_floor_drop_exact`: PASS
- `upper_ceiling_gravity_vector_outward`: PASS
- `upper_ceiling_drop_exact`: PASS
- `chamber_side_sill_present`: PASS
- `capillary_break_present_and_printable`: PASS
- `capillary_break_intersects_drain`: PASS
- `drain_at_lowest_capture_region`: PASS
- `closed_water_pocket_none`: PASS
- `drain_diameter_count_preserved`: PASS
- `camera_clearance_positive`: PASS
- `extension_clearance_positive`: PASS
- `lower_path_open_from_above`: PASS
- `lower_closed_loop_none`: PASS
- `upper_closed_loop_none`: PASS
- `cable_interference_zero`: PASS
- `connector_interference_zero`: PASS
- `connector_placement_path_clear`: PASS
- `upper_lower_unintended_interference_zero`: PASS
- `direct_line_of_sight_none`: PASS
- `roof_skirt_parting_m3_preserved`: PASS
- `coupon_material_reduced`: PASS
- `pressure_jet_not_rated`: PASS

Physical coupon water PASS is not inferred from CAD_PASS.
