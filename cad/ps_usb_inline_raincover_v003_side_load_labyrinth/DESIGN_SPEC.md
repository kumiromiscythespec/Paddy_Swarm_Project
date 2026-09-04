# DESIGN SPEC — v003 SIDE-LOAD LABYRINTH

## Scope

- Authority: `cad/ps_usb_inline_raincover_v002_measured_envelope/`（read-only）
- v003 change scope: cable labyrinth assembly path only
- status: `CAD_COMPLETE_SIDE_LOAD_LABYRINTH_PHYSICAL_VALIDATION_PENDING`
- process: PETG / Bambu Lab A1 / 0.4 mm nozzle / 0.20 mm layer
- rating: `SPLASH_RESISTANT_NOT_WATERPROOF`

## Preserved Authority

| Item | Value / status |
|---|---|
| connector envelope | 95.1 × 18.7 × 10.8 mm |
| chamber | 102 × 24 × 16 mm; Physical PASS |
| camera / extension cable | Ø3.8 / Ø4.0 mm |
| channel | Ø4.4 mm nominal; Physical PASS |
| roof / skirt | 3° / 6 mm |
| floor | bilateral 2°, center crown 1.781 mm |
| drain | Ø2.5 mm ×2 |
| parting | 2 mm step / 3 mm overlap / 0.30 mm clearance |
| closure | M3×6, x = -50/0/+50 mm on both sides |
| saddle | v002 measured-envelope-safe position and loose 5.2 mm groove |

## Split channel

The lower contains an upward-open U-channel over the full chamber-to-exit route. It has no circular through-hole, tunnel, bridge, or captive ring. The upper contains a downward-open complementary tongue/ceiling and likewise cannot capture a cable by itself. A nominal 4.4 mm passage exists only after assembly.

The lower opening is 4.65 mm at the split and the upper tongue is 4.15 mm, providing 0.25 mm local FDM seam relief without changing the 4.4 mm channel Authority. The assembled vertical opening is 4.525 mm; Ø4.0 retains clearance and is not press-fit. Cable compression target remains NONE.

The cable path is top-loadable in CAD by a continuous swept placement envelope for both Ø3.8 and Ø4.0 references. The upper has an equivalent downward release envelope. All four sweep-to-part interferences are 0 mm³. Connector vertical placement and post-placement upper closure are also 0 mm³.

## Water controls

The path leaves the chamber, crosses the split terminal baffle, turns through an 8 mm plan-view dogleg, passes over the lower drip vestibule, and exits beneath the retained skirt before the cable turns downward. The dogleg sightline deviation is 2.555 mm versus a 2.325 mm relieved half-width, so a straight relieved passage sightline is not present.

The split seam is protected by three controls: downward-facing exit beneath the skirt, lateral offset dogleg, and a narrow upper cap tongue behind a wider bridge. The lower pocket, offset weep, and both drains remain visible with the upper removed. CAD water-path results do not replace colored-water testing.

## Pass separation

`CAD_PASS`, `PRINT_PASS`, `CABLE_FIT_PASS`, `CONNECTOR_FIT_PASS`, `ASSEMBLY_PATH_PASS`, `DRAIN_PASS`, `SPRAY_PASS`, `POWERED_USB_PASS`, `HEAVY_RAIN_FIELD_PASS`, and `LONG_DURATION_PASS` remain independent. Current `ASSEMBLY_PATH_PASS` is PENDING despite CAD assembly-path checks passing.

Current blockers are side-load cable assembly Physical validation, labyrinth drain effectiveness, and full-shell water intrusion. Heavy rain, wind-driven rain, long-duration exposure, split-seam capillary ingress, mud splash, drain contamination/blockage, and UV/weather aging remain `FIELD_UNCONFIRMED`.
