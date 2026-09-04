# Design Authority v0.9.6.17

## Scope

Crawler-link anti-derail guard only. The single geometry parent is the exact source STL identified by `eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a`. No drive sprocket, hub, cap, collar, yoke, key, or drive-wheel internal architecture is a geometry dependency.

## Authority order

1. Exact source STL bytes and measured mesh bounds.
2. User physical guard measurements.
3. This additive thick-root guard contract.

## Final geometry contract

- Two source guide regions identified at X=-4..+4, Y=+/-23..+/-27 and Z=0..9 in source coordinates.
- Functional height: 9.0 mm relative to the old 6.0 mm physical datum.
- Upper wall: 5.0 mm, with added thickness toward the link interior.
- Root land: 6.0 mm minimum; R3-class curved apron into the body.
- Top: R1-class chamfer; predominantly vertical blocking face.
- Frame-facing surface delta: 0.0 mm.
- Source Y extent: 54.0 mm; final Y extent: 54.0 mm.
- Unexpected removed source material: 0.

The final STL is the physical authority. No STEP is released because the parent is a mesh. This lane does not authorize powered operation.
