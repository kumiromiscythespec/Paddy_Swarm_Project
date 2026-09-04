# Bearing retention trade study v0.9.3.5

Measured bearing OD is approximately 25.9 mm and the printed seat is approximately 26.1–26.2 mm; outer-race movement is confirmed.

## Option A — seat coupon

Four nominal CAD coupon commands are emitted: 25.7, 25.8, 25.9 and 26.0 mm. These are not predictions of printed diameter. Each as-printed bore must be measured and recorded against the target series before any main seat update.

## Option B — removable retainer

- Three symmetric M3-class holes.
- Outer-race contact annulus begins at diameter 25.0 mm.
- Inner-race proxy intersection: 0.000000 mm³.
- Provisional shield-keepout intersection: 0.000000 mm³.
- Shaft intersection: 0.000000 mm³.
- Actual shield OD remains `MEASUREMENT_HOLD`; the ring remains `PHYSICAL_COUPON_REQUIRED`.
- No adhesive is the primary retention method; removal and drain notches are retained.
