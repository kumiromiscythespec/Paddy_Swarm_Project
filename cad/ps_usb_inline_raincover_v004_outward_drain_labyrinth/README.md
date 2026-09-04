# USB Inline Raincover v004 — OUTWARD-DRAIN LABYRINTH

Status: `CAD_COMPLETE_OUTWARD_DRAIN_LABYRINTH_PHYSICAL_VALIDATION_PENDING`

Physical rating inherited from v003: `SPLASH_RESISTANT_PHYSICAL_PASS_WITH_PRESSURE_JET_LIMIT`

This enclosure is designed as a gravity-drained,
splash-resistant rain cover.

It is not a pressure-jet-rated enclosure
and is not designed for immersion.

本品は、重力排水を使う防滴レインカバーです。圧力噴流に対する防水筐体でも、浸水使用を想定した筐体でもありません。

## Purpose

v004 preserves the physically successful v003 side-load cable architecture, 4.4 mm cable path, and 102 × 24 × 16 mm connector chamber. The controlled change is the water path: a 7° outward lower floor, 4° outward upper ceiling, 1.2 mm chamber-side sill, and a 1.2 × 0.8 mm open capillary break connected to each Ø2.5 mm drain.

The cable drip loop below the cover is mandatory. It reduces the volume of water tracking along the cable; it does not block a pressure jet aimed into a port. A strong direct pipette jet is record-only and outside the pass requirement.

## Physical Authority inherited from v003

- Connector fit: PASS
- 4.4 mm cable fit for Ø3.8 / Ø4.0 mm cables: PASS
- Side-load assembly without end threading or cable cutting: PASS
- Top spray: DRY
- Side spray: DRY
- Weak direct pipette jet: DRY
- Strong direct pipette jet: WET (`PRESSURE_JET_LIMIT_OBSERVED`)

These inherited results do not establish v004 water performance. The new outward-drain and capillary-break geometry remains `PENDING` until its coupon is printed and tested.

## Installation Authority

Mount the cover near the upper portion of a protected cable run on a vertical support pipe. Keep the long axis approximately horizontal, drains downward, ports not upward-facing, and the cover suspended above soil and grass. Form a drip loop below the cover and inspect the drains periodically.

## Print and test gate

Print only the two coupon parts first:

1. `outward_drain_labyrinth_coupon_lower_v004.stl`
2. `outward_drain_labyrinth_coupon_upper_v004.stl`

Full-shell printing and testing remain on HOLD until side-load, closure, repeated assembly, top/side/cable-tracking/weak-direct water tests, drain function, and no-pooling checks all pass. See `docs/PHYSICAL_TEST_PROTOCOL.md`.

## Manufacturing baseline

- Printer: Bambu Lab A1
- Material: PETG
- Nozzle: 0.4 mm
- Layer height: 0.20 mm
- Suggested walls: at least 4
- Suggested top/bottom: at least 5
- Suggested infill: 25–35%

