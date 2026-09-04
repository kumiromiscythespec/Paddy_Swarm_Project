# VALIDATION REPORT

Status: `CAD_COMPLETE_SIDE_LOAD_LABYRINTH_PHYSICAL_VALIDATION_PENDING`

CAD validates the v003 split assembly path. Physical side-load, drain, and water tests remain pending.

## STL / BRep

| Artifact | Solids | BRep valid | STL triangles | Boundary/non-manifold edges |
|---|---:|---|---:|---:|
| `split_labyrinth_side_load_coupon_lower_v003` | 1 | True | 2932 | 0 |
| `split_labyrinth_side_load_coupon_upper_v003` | 1 | True | 1738 | 0 |
| `usb_raincover_lower_v003` | 1 | True | 8630 | 0 |
| `usb_raincover_upper_v003` | 1 | True | 6040 | 0 |

## STEP re-import

- `split_labyrinth_side_load_coupon_v003`: valid=True, solids=2
- `usb_raincover_lower_v003`: valid=True, solids=1
- `usb_raincover_upper_v003`: valid=True, solids=1
- `usb_raincover_assembly_v003`: valid=True, solids=5

## Interference

- `connector_vs_lower_mm3`: 0.00000000 mm³
- `connector_vs_upper_mm3`: 0.00000000 mm³
- `camera_cable_vs_lower_mm3`: 0.00000000 mm³
- `camera_cable_vs_upper_mm3`: 0.00000000 mm³
- `extension_cable_vs_lower_mm3`: 0.00000000 mm³
- `extension_cable_vs_upper_mm3`: 0.00000000 mm³
- `upper_vs_lower_mm3`: 0.00000000 mm³
- `camera_lower_top_load_sweep_vs_lower_mm3`: 0.00000000 mm³
- `extension_lower_top_load_sweep_vs_lower_mm3`: 0.00000000 mm³
- `camera_upper_release_sweep_vs_upper_mm3`: 0.00000000 mm³
- `extension_upper_release_sweep_vs_upper_mm3`: 0.00000000 mm³
- `connector_vertical_placement_vs_lower_mm3`: 0.00000000 mm³

## Checks

- `v002_authority_hashes_match`: PASS
- `connector_dimensions_preserved`: PASS
- `chamber_102x24x16_preserved`: PASS
- `channel_nominal_4p4_preserved`: PASS
- `local_split_relief_within_authority`: PASS
- `camera_cable_no_compression`: PASS
- `extension_cable_no_compression`: PASS
- `drains_preserved`: PASS
- `roof_skirt_parting_preserved`: PASS
- `m3x6_closure_preserved`: PASS
- `floor_crown_preserved`: PASS
- `lower_path_open_from_above`: PASS
- `no_closed_loop_in_lower`: PASS
- `no_closed_loop_in_upper`: PASS
- `continuous_cable_side_load_path`: PASS
- `connector_body_placement_path`: PASS
- `upper_closure_after_cable_placement`: PASS
- `connector_shell_interference_zero`: PASS
- `cable_reference_interference_zero`: PASS
- `upper_lower_interference_zero`: PASS
- `dogleg_blocks_relieved_straight_sightline`: PASS
- `coupon_material_substantially_reduced`: PASS
- `no_roof_penetration`: PASS
- `waterproof_not_claimed`: PASS

`CAD_PASS` does not imply PRINT, ASSEMBLY_PATH, DRAIN, SPRAY, or POWERED_USB PASS.
