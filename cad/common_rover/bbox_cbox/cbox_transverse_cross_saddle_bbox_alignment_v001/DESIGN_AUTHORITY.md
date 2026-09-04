# Design authority

## Physical basis

Rail outside span 208–210 mm, inside span 168–170 mm, width20 mm and center
distance188–190 mm are used exactly. Local Y0 is the midpoint of the current
rail centers at the mounting station; model centers ±94.5 are local nominal
coordinates only, not physical vehicle-axis authority. Left/right rail
top/bottom Z are255/235 and254/234 mm.

## Selected architecture

Two independent, equal-nominal PETG saddles attach to the outboard rail side
T-slot using accessible M5/T-nut candidate hardware. The outboard-only contact
starts1.2 mm from each local rail center, avoiding the centered BBOX lid envelope
over the full188–190 mm rail-spacing range. No cross-rail member exists, so frame
preload is not required.

The selected4 mm lift produces left/right support Z259/258. The CBOX follows the
1 mm as-built frame plane (0.303149 degree reference tilt). Its lowest
conservative bottom is Z257.849, providing
3.849 mm above the physical
BBOX lid plane outside the protected chimney.

## Protected BBOX

The exact BBOX v003 STEP is copied byte-for-byte as a reference. Sealing geometry,
gasket/land, M4 pattern, chimney, PG9 Ø15.2 interface,2.4 mm gland wall and wet
volume have zero delta. No new BBOX hole or BBOX↔CBOX passage exists.

## CBOX

Body authority is150 X ×246 Y ×80 Z. The exact v0.9.6.32 shell is reused and
rotated to long-axis Y; existing mounting tabs make its total X envelope152 mm.
The saddles remain inside that source-shell X envelope.

## Release boundary

CAD and contract PASS authorize saddle printing only. Retention, rail fit, load,
dynamic crawler, final clutch,500 mm frame and field validation remain pending.
