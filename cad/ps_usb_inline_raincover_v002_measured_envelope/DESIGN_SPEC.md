# DESIGN SPEC — v002 MEASURED CONNECTOR ENVELOPE

## Scope and status

- lane: `cad/ps_usb_inline_raincover_v002_measured_envelope/`
- v001 Authority: `cad/ps_usb_inline_raincover_v001/`（read-only）
- status: `CAD_COMPLETE_MEASURED_ENVELOPE_PHYSICAL_VALIDATION_PENDING`
- rating: `SPLASH_RESISTANT_NOT_WATERPROOF`
- material/process: PETG, Bambu Lab A1, 0.4 mm nozzle, 0.20 mm layer

## Dimensional Authority

| Item | Value | Authority |
|---|---:|---|
| connector envelope L × W × H | 95.1 × 18.7 × 10.8 mm | physical measurement |
| chamber inner L × W × H | 102 × 24 × 16 mm | v002 initial Authority |
| camera cable OD | 3.8 mm | physical measurement |
| extension cable OD | 4.0 mm | physical measurement |
| both cable channels | 4.4 mm | v001 coupon physical PASS |
| wall | 3.0 mm | v001 preserved |
| roof slope / skirt | 3° / 6 mm | v001 preserved |
| floor slope | center-high 2° to both ends | v001 concept, crown recalculated |
| labyrinth run / offset | 10 / 5 mm | v001 preserved |
| drain | Ø2.5 mm ×2 | v001 preserved |
| parting step / overlap / clearance | 2 / 3 / 0.30 mm | v001 preserved |

Clearance is 6.9 mm axial total (3.45 mm/end), 5.3 mm width total, and 5.2 mm height total. `CONNECTOR_COMPRESSION = NONE`; CAD intersections with upper, lower, baffles, and labyrinth are 0 mm³.

## Architecture

The water path remains: downward cable port → drip vestibule → terminal baffle/interception → offset weep → gravity drain. There is no straight line-of-sight path from either cable entrance or drain to the connector envelope. The lower floor has a 1.781 mm center crown, recalculated as `tan(2°) × 51 mm`; it does not apply a one-way 2° fall over 102 mm. The roof keeps a 3° single fall and has no penetration.

Both ends use a 4.4 mm channel. Cable bend space is at least R4 and cable-contact edges target R1 or more. Two 3 mm-long loose saddles are located outside the measured protected envelope; their groove is channel diameter + 0.8 mm, so they locate cable without hard clamping. This is a `MEASURED_ENVELOPE_REQUIRED_CHANGE` from the v001 saddle locations.

## Long-shell stiffness and closure decision

The chamber grew 50 → 102 mm. Roof transverse span, chamber width, wall thickness, and parting geometry remain unchanged, so no external roof rib was added. Ribs would add print and runoff discontinuities without reducing the governing transverse roof span. To control central parting-line bow and distribute closure over the 100 mm fastener span, closure is changed from M3×4 to M3×6 at x = -50, 0, +50 mm on both side flanges, with captured hex nuts. This is `MEASURED_ENVELOPE_REQUIRED_CHANGE`; all fasteners remain outside the water umbrella and connector chamber.

The 128 mm lower has a flat print datum. The 134.6 mm upper and lower fit the A1 bed. Physical print validation must check corner lift, long-wall bow, seam straightness, flange stiffness, and warpage. No CAD brim is included.

## Parts and references

- production: `usb_raincover_upper_v002`, `usb_raincover_lower_v002`
- low-material fit gauge: `connector_chamber_fit_coupon_v002` (14.55% of full-shell solid volume)
- water-path gauge: `labyrinth_drain_coupon_v002` with `WITNESS_BAY`
- non-manufacturing reference: `connector_reference_v002` and Ø3.8/Ø4.0 cable references in assembly STEP

## Gates

`CAD_PASS`, `PRINT_PASS`, `CABLE_FIT_PASS`, `CONNECTOR_FIT_PASS`, `DRAIN_PASS`, `SPRAY_PASS`, `POWERED_USB_PASS`, `HEAVY_RAIN_FIELD_PASS`, and `LONG_DURATION_PASS` are independent. A lower-level PASS never implies a higher one.

Current blockers are connector chamber physical fit, labyrinth drain effectiveness, and full-shell water intrusion. Heavy rain, wind-driven rain, long-duration exposure, capillary ingress, mud splash, drain blockage/contamination, and UV/weather aging remain `FIELD_UNCONFIRMED`.
