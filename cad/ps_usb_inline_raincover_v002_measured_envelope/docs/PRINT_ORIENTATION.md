# PRINT ORIENTATION — PETG / Bambu Lab A1

Baseline: 0.4 mm nozzle, 0.20 mm layer, at least 4 walls, at least 5 top/bottom layers, 25–35% infill. Dry PETG and tune extrusion before judging the 0.30 mm assembly clearance.

## Parts

- lower: print the flat lower datum directly on the build plate. Keep drain and cable ports open; no internal support should remain in weeps or nut captures.
- upper: print roof exterior on the build plate so the broad roof supplies bed contact and the open skirt faces upward. Confirm first-layer compensation does not close the parting groove. If roof finish/drain slope is functionally important, use a smooth plate and avoid warped adhesion zones.
- connector chamber fit coupon: STL contains the two gauge halves separated on the bed. Print as supplied; do not scale.
- labyrinth/drain coupon: print flat datum down, witness bay accessible upward.

## Long-part controls

The full shell is approximately 135 mm long. Inspect bed contact, corner lift, long-wall bowing, flange flatness, and parting-line straightness. Use slicer brim or mouse ears if needed; no oversized brim geometry is embedded in CAD. Avoid a long unsupported bridge and do not auto-orient the lower onto a side wall.

Before water testing, deburr cable-contact edges without enlarging the Ø4.4 mm Authority channel. Confirm drains measure Ø2.5 mm nominal and are open. Record `PRINT_PASS` separately from `CAD_PASS`.
