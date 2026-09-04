# P25 Slide-In V002 design authority

P25_PHYSICAL_LAYOUT_SELECTION = CURRENT_SELECTED_CANDIDATE.
P25_WORKING_DIMENSION = 25.000000 mm.
PRIMARY_FUNCTION = POSITIONING / ASSEMBLY GAUGE.
STRUCTURAL_LOAD_AUTHORITY = PENDING.

Logical +X is the slide and P25 measurement direction.  The body is25 x18 x8
mm.  Its central external datum patches are X=0 and X=25, Y=-5..+5, Z=2..6.
The generated/reloaded BRep faces are planar, parallel and measured directly.
The B tongue extends25 mm; changing it cannot move either datum.

The T-section has a2 mm head and a stem of depth-minus2.  Its 2.1 mm/side head
overhang captures behind the measured6.4 mm entrance while the head remains
inside the10.8 mm internal maximum.  Positive bottom clearance prevents tongue
bottom-loading.  The first0.4 mm narrows0.3 mm per side as an insertion lead-in;
the remaining engagement has no taper.

No root fillet projects into the partially measured lip corridor.  This is a
deliberate fail-closed choice: adding an unmeasured fillet could bind at the lip.
The full-width stem-to-body union is continuous and not a thin tab.  Future
physical lip measurements may justify a non-fit-side root radius in a new lane.

The provisional body has no load-rated clamp.  Positioning, repeatability and
anti-side-shift assistance are the only claimed functions.  It cannot carry
drive torque or belt/bearing/shock load.
