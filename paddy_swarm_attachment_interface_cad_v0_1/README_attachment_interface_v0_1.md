# Paddy Swarm Attachment Interface CAD v0.1

This package introduces the **Paddy Swarm Attachment Interface Standard v0.1**.

Purpose:
- Keep the rover body upgradable while keeping attachment locations fixed.
- Move direct seeding / planting-style modules to the **rear** so the rover wheels do not run over freshly placed germinated seed.
- Reserve the **front** attachment ports for high-cut harvest, camera-linked work, and operations that need visual confirmation.
- Keep belly weeding as a central underbody module.

Important: this is a **Grade 0 / mock-up CAD pack**. Shafts, pins, bushings and springs are included as 3D-printable dummy parts so a physical model can be assembled cheaply. Field-use versions may need metal shafts, bearings, bushings, springs, seals, and stronger hardware.

## Fixed interface concept

Coordinate convention:
- X: left/right
- Y: front/rear
- Z: up/down
- Body center is the origin.

Nominal fixed positions:
- Front-left port: X=-70 mm, Y=+230 mm
- Front-right port: X=+70 mm, Y=+230 mm
- Rear-left port: X=-70 mm, Y=-230 mm
- Rear-right port: X=+70 mm, Y=-230 mm
- Nominal port height: Z=65 mm

These values are the v0.1 interface reference. Future rover chassis updates should preserve these port positions or provide adapter plates.

## Attachment allocation rule

- Front two ports: high-cut harvest, camera-linked tools, inspection tools.
- Rear two ports: direct seeding, planting, replanting modules.
- Belly rail: underbody weeding modules.
- Side mounts: floats, guards, recovery aids.

## Included update

- Base chassis v0.5 with four fixed ports.
- Rear-mounted 3-unit direct seeding mock-up using the rear-left and rear-right ports.
- Front high-cut interface bridge gauge, not an actual cutter.
- 3D-printed dummy shafts, pins, springs and fasteners for low-cost model assembly.
- Stackable hopper extension walls with no lid, assuming wet germinated seed and non-rain-avoidance operation.

## Notes

The direct seeding module here is intentionally placed at the rear. It is meant to place germinated seed after the wheels pass, closer to the logic of a transplanter. The module includes a light skid/opener concept for shallow placement and wheel-track correction, but actual seed depth must be validated in tray and mud tests.
