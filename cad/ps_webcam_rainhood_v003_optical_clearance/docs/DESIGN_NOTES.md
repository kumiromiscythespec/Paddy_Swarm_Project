# Design notes

## Problem statement

The v002 tripod position reached physical fit, but the hood front edge or underside appears across the upper image, including both upper corners. v003 treats this as an optical-clearance problem, not a tripod-fit problem. Camera tilt and the carrier/tripod datums are deliberately unchanged.

## Coordinate authority

The source uses the v002 coordinate frame:

- X: camera width direction; tripod axis X = 0.15 mm.
- Y: lens/front is negative; tripod axis Y = 0 mm.
- Z: carrier top = 0 mm; camera and guides rise in positive Z.
- v002 hood front edge Y = -60.4 mm.

Candidate front positions are therefore -50.4, -45.4, and -40.4 mm. `front_setback` is not a new arbitrary length; it is always a delta from the v002 edge.

## Parametric optical geometry

The single source parameterizes at least:

- `front_setback`
- `underside_bevel_angle`
- `hood_top_height`
- `hood_front_length`
- `camera_reference_position`

The upper surface keeps the v002 1.5-degree roof slope and the 4 mm safe-envelope clearance datum. The full-width leading drip wall from v002 is intentionally absent because it is a likely optical occluder. Instead, the 3 mm roof transitions to a 1.2 mm leading edge through a calculated upward underside bevel. The requested 35/40/45-degree angles are the actual side-section bevel angles; roof slope is included in the run calculation.

The front edge is also set back. This combination tests the two requested variables and is not merely a uniform shortening of the v002 hood.

## Coupon fidelity decision

A small front cap attached with a new clip was rejected because the new clip tolerance could invalidate the camera-to-hood optical relationship. Each v003 coupon instead includes the exact v002 shell interface geometry:

- lower rails: same X, Y, Z, thickness;
- upper rails: same X, Y, Z, thickness;
- same rear stops;
- same rear crossbar and two bosses;
- same M4 clearance holes and nut traps;
- same rear USB slot.

The optical roof continues through Y=22 mm, behind the nominal camera-body rear Y=14.8 mm. Sidewall geometry continues into low rear spines that connect to the full interface. Rear roof and rear baffle are omitted only because they are behind the camera and not needed to compare upper-image intrusion. A later full rainhood must restore them without moving the chosen front geometry.

This is a low-material optical fixture, not proof of final structural stiffness, connector coverage, rain protection, or wind-driven-rain performance.

## Permanent identification

Small ribs protrude from the exterior of the right low rear spine:

- A: one rib
- B: two ribs
- C: three ribs

They are behind the nominal camera body, outside the carrier envelope, below the rain roof, and outside the optical front region. They do not cut a leakage path and do not modify the slide fit.

## Mechanical preservation

Tripod interface changes: `NONE`.

Carrier interface changes: `NONE`.

Candidate-specific changes are limited to:

1. front Y;
2. front underside bevel;
3. the forward sidewall taper needed to terminate at that front Y;
4. permanent exterior identifier count.

## Known limitations and holds

- Exact lens principal point and optical FOV boundary are unknown.
- The CAD camera box is a mechanical reference, not an optical frustum.
- No numerical final safety margin is asserted.
- The leading edge and front setback may reduce rain coverage; this is intentionally measured after optical comparison.
- Coupon rear coverage does not represent the final rear roof/baffle.
- Screw-head style remains outside this lane's design authority.
- No candidate is selected in CAD.

