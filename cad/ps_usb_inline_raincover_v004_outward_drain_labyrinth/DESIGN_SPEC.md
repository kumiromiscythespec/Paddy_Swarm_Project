# DESIGN SPECIFICATION

## Authority and scope

v003 (`cad/ps_usb_inline_raincover_v003_side_load_labyrinth/`) is read-only design and Physical Authority. v004 changes only the labyrinth water-routing features needed to make chamber-side elevation HIGH and outside/drain-side elevation LOW.

Authority priority is: physical measurements and tests, v003 validated geometry, v004 CAD nominal geometry, then unvalidated assumptions.

## Preserved geometry

| Parameter | Authority |
|---|---:|
| Connector envelope | 95.1 × 18.7 × 10.8 mm |
| Chamber interior | 102.0 × 24.0 × 16.0 mm |
| Camera / extension cable OD | 3.8 / 4.0 mm |
| Nominal split cable channel | 4.4 mm |
| Local split relief | 0.25 mm |
| Drains | Ø2.5 mm ×2 |
| Roof slope | 3° |
| Umbrella skirt | 6.0 mm |
| Parting step / overlap / clearance | 2.0 / 3.0 / 0.30 mm |
| Closure | v003 M3 layout |

PETG upper/lower clamshell, upward-open lower cable path, complementary upper cover, no closed cable loop, no end threading, no cable cutting, roof without penetration, umbrella skirt, and parting labyrinth are preserved.

## v004 controlled changes

| Feature | v004 value | Design intent |
|---|---:|---|
| Lower outward slope | 7.0° over 10.0 mm | 1.2278 mm drop toward each outer port |
| Upper outward ceiling slope | 4.0° over 10.0 mm | 0.6993 mm drop toward each outer port |
| Chamber-side water sill | 1.2 mm | Interrupt chamber-directed surface water without lifting the cable |
| Capillary break | 1.2 mm wide × 0.8 mm deep | Interrupt continuous water film; open to drain |
| Drain placement | true low-point capture region | No lower closed pocket |

Both ends are mirrored so water descends away from the connector chamber. The capillary-break trench intersects the drain (`2.9246 mm³` CAD overlap) and is not a closed reservoir.

## Cable and connector safeguards

- The sill flanks the cable route; it does not cross or raise the 4.4 mm cable path.
- Nominal diametral clearance remains 0.6 mm for the Ø3.8 mm camera cable and 0.4 mm for the Ø4.0 mm extension cable.
- Connector/cable reference interference against upper and lower shells is 0 mm³ in CAD.
- Lower cable route stays open from above. Upper and lower single-part closed loops remain NONE.

## Water-design boundary

Required behavior covers top spray, side spray, cable-tracking water, weak direct pipette water, and normal gravity runoff. Strong direct jets, high-pressure hoses, pressure washers, forced continuous port jets, and immersion are outside design scope.

`PRESSURE_JET_RATED = FALSE`

`IMMERSION_RATED = FALSE`

## Print baseline

PETG, Bambu Lab A1, 0.4 mm nozzle, 0.20 mm layer, at least four walls, at least five top/bottom layers, and 25–35% infill. Verify all water-path features are free of stringing and debris before testing.

