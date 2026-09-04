# Exact G065 seal traceability

Read-only measured authority: `D:\Paddy_Swarm_Project\cad\common_rover\bbox\bbox_compact_seal_b_water_dummy_v001`. Generated G065 STEP measures 0.650000000 mm, not an old parameter label.
V004 has width 2.1, actual depth 0.65, hard-stop 0.895, cord OD1.8, outer R6.0, inner R3.9 and centerline R4.95.
Nominal cord compression reference is 0.255 mm (14.166667%); this is not a prediction of rubber deformation.
Full centerline perimeter 451.101767 mm, versus dummy 219.101767 mm. Trim the physical cord/joint to fit; do not use a stretched cord as a dimensional workaround.

Actual translated straight section symmetric difference: 0 mm3.
Four actual corner seal-wall symmetric differences: [0, 0, 0, 0] mm3.
The broader left/front corner comparison includes 41.047500 mm3 of allowed chimney-mouth difference INSIDE the seal; this is separately reported and excluded only from the seal-wall comparison.
Allowed differences are perimeter length, body size, eight rather than four external M4 compression stations, and chimney presence.

M4 architecture remains external vertical through-bolts, flat lid and 0.895 hard-stop. Hole-to-cord minimum is 1.900000 mm, and intersection is zero. This is smaller than the corner-only dummy distance; full-box clamping uniformity must be physically checked.

Two necessary local top-interface corrections (task section 6) are NOT hidden:

1. Extend the groove cutter upward beyond hard-stop to remove four obsolete mid-boss roofs. The naive depth-only body intersects nominal cord by 18.406304 mm3. New intersection is zero. The groove bottom alone moves down 0.15 mm.
2. Restore a 42 x9.5 x8 mm lid-thickness bridge outside the 155 x69 battery opening. V003 was missing 42 x2.1 mm of lid seal land beneath its chimney opening. V004 has zero missing seal land. The lower chimney mouth changes from 42 x37 to 42 x27.5 mm; the chimney ABOVE the 8 mm lid, PG9 hole, 2.4 wall, recess and counterbore are exactly unchanged.

The new lid contains 3192.000000 mm3 additional material and no removed material. Body removed volume 165.576219 mm3; no added body material; zero body delta outside groove envelope. These are local seal corrections, not a battery/upper-chimney redesign.
