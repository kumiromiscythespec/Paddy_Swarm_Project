# Source traceability

## Search performed

Before creating this lane, the repository was searched read-only for GoldenMate/battery dimensions and terminals; Freenove/ESP32/WROOM; MD10C/Cytron; 2PNCT/Taiyo Cabletec/1.25 sq; 9.6 mm cable and 14.9 mm gland; 900 mm service cable; CBOX 150 x 246 x 80; electrical/electronics records; physical measurements; datasheet references; BOMs; battery-tray lanes; BBOX/CBOX lanes; and wiring-chimney lanes.

No existing consolidated electrical-hardware physical-authority lane was found. The evidence was distributed across the sources below, so a new isolated integration record was warranted.

## Primary evidence map

| Repository source | Evidence used | Classification decision |
|---|---|---|
| `common_rover_physical_measurement_closure_v0_9_5_2/MEASUREMENT_LEDGER.md` | Battery 150.9/99.4/92.5; tab 6.3/0.7; receptacle 10.6; terminal top 99.4; 108 and 90.7 passage datums | PHYSICAL_DIRECT or PHYSICAL_FIT_RESULT, preserving datum distinctions |
| `common_rover_bbox_cbox_printable_prototype_v0_9_5_0/BATTERY_REFERENCE.md` | GoldenMate identity, 12.8 V/10 Ah/128 Wh, 1.2 kg | Label as PURCHASE_RECORD; mass as PHYSICAL_DIRECT |
| `common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/ESP32_PHYSICAL_INTEGRATION.md` | 56.8 x 28.2 x 12.9 mm; no holes observed | PHYSICAL_DIRECT |
| `common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/PHYSICAL_SOURCE_TRACE.md` | MD10C drawing references; cable purchase identity/length | DATASHEET_AUTHORITY and PURCHASE_RECORD, not physical |
| `common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2/CABLE_ARCHITECTURE.md` | Taiyo 2PNCT 1.25 sq x 2C, 3 m; OD unmeasured | PURCHASE_RECORD plus MEASUREMENT_PENDING |
| `bbox_lid_wiring_chimney_v001_above_water_gland/PHYSICAL_MEASUREMENTS.md` | Cable OD 9.6; gland male thread OD 14.9 | PHYSICAL_DIRECT for those specimens; no standard/product inference |
| `common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36/SERVICE_CABLE_REQUIREMENTS.md` | 900 mm service architecture | DESIGN_SERVICE_REQUIREMENT until completed-harness measurement is documented |
| `common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36/CBOX_MANUAL_SERVICE_REQUIREMENTS.md` | CBOX 150 x 246 x 80 | PHYSICAL_DIRECT |
| `common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/docs/ELECTRICAL_ARCHITECTURE.md` | Dual MD10C, ESP32, DC-DC, safety relay, fuse-holder packaging intent | Inventory/design context; unknown hardware remains pending |
| `front_drive_dual_pto_design_authority_v0_8_1` and later historical lanes | cassette 125 x 180 x 120; CBOX 130 x 140 x 105; BBOX 150 x 220 x 150 | Historical design envelopes only |

## Important non-equivalences

1. `CABLE-UNKNOWN-9P6-001` and `CABLE-2PNCT-001` are separate records.
2. Battery body and battery cassette are separate objects.
3. Historical CBOX/BBOX CAD envelopes and current physical boxes are separate histories.
4. MD10C datasheet dimensions are not physical measurements.
5. The 900 mm service value is not a measured finished-harness length under this authority.
6. The 108 mm passage result and historical 90.7 mm measurement use different datums.

## Confidence

`HIGH` means the repository record and current task classification agree. `MEDIUM` is used for the MD10C 69 x 35 mm historical drawing-reference pattern because the primary manufacturer drawing was not present in the searched authority material. Unknown values remain explicit rather than inferred.

