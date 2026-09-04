# PTO offset gauge design

PRIMARY_USE = FIT / POSITION / CLEARANCE TEST.
STRUCTURAL_LOAD_AUTHORITY = NOT_APPROVED.

Three rectangular one-piece gauges have exact X-direction face separation
20.0, 22.0 and 25.0 mm. Width18 and height8 mm give 144 mm2 per end face.
Both complete end faces are planar, parallel, unchamfered and unlabelled.
The designated measurement patch is Y=-5..+5, Z=2..6 mm on each end.
Do not measure across the engraved top, a first-layer lip or an angled edge.

Top labels use broad 1 mm native CAD strokes, engraved 0.6 mm deep. The smallest
label-to-end distance is 4.55 mm. There is no font/runtime dependency, shaft
bore, keyway, bolt pattern, KP000 mounting seat, 2040 clamping feature or torque
transfer feature. No triangular joint or L-bracket is added. These blocks do
not claim a final two-surface attachment that the sources do not establish.

Gauge-local X0 is its datum face A. For a static setup it can register against
the physically identified member-end face. Face B is the opposite gauge face;
which KP000/support face should register there, and whether that represents the
intended offset, must be physically established before interpreting placement.
The gauge does not define the PTO axis by L+33.05 or any old global coordinate.

Reference physical KP span66.1 and 60T max100.1 are retained without rounding.
All other simplified KP dimensions and the 60T axial extent are explicitly
CAD references. Original source parts are not scaled, overwritten or promoted.

Structural spacers, final support plates, shaft cuts, belt tension, permanent
load paths, powered operation and final slide-clutch design are outside scope.
