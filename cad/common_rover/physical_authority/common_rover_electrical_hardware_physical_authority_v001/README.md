# Common Rover Electrical Hardware Physical Authority V001

Status: `DOCUMENTATION_COMPLETE / ELECTRICAL_HARDWARE_AUTHORITY_RECORDED / PHYSICAL_GAPS_REMAIN`

This documentation-only lane consolidates physical measurements, physical fit results, datasheet values, purchase records, service requirements, and unresolved measurements used by Common Rover BBOX/CBOX electrical packaging. It does not create or modify CAD, approve wiring, select final protection ratings, or supersede existing authority files in place.

The canonical machine-readable record is `electrical_hardware_authority.json`. Values are authorized only with the `source_class` attached to each record. In particular:

- Cytron MD10C 75 x 43 mm is `DATASHEET_AUTHORITY`, not a physical measurement.
- Cable OD 9.6 mm belongs to an unidentified measured BBOX/CBOX cable specimen and is not automatically Taiyo Cabletec 2PNCT.
- Taiyo Cabletec 2PNCT 1.25 sq x 2C, 3 m is a `PURCHASE_RECORD`; its actual OD remains `MEASUREMENT_PENDING`.
- CBOX service length 900 mm is a `DESIGN_SERVICE_REQUIREMENT`, not a proven end-to-end finished-harness measurement.
- Historical cassette/box envelopes remain distinct from current physical component dimensions.

No STEP, STL, DXF, or other CAD artifact is present in this lane.

## Primary repository sources

- `common_rover_physical_measurement_closure_v0_9_5_2`: battery, terminals, and 108 mm passage result.
- `common_rover_bbox_cbox_printable_prototype_v0_9_5_0`: GoldenMate product/body/mass record.
- `common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2`: ESP32 measurement, MD10C drawing reference, and 2PNCT purchase record.
- `bbox_lid_wiring_chimney_v001_above_water_gland`: measured 9.6 mm cable and 14.9 mm gland thread.
- `common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36`: 900 mm service architecture and current 150 x 246 x 80 mm CBOX.
- `common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32`: current electrical inventory/zone intent and remaining service measurements.

See `SOURCE_TRACEABILITY.md`, `MEASUREMENT_GAPS.md`, and `electronics_inventory.csv` before using any value in packaging CAD.

