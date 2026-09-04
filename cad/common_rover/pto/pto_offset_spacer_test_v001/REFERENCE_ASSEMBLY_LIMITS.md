# Reference assemblies — not installed geometry

P20/P22/P25 reference STEP files are exploded component boards. Only the gauge
touching an80 mm display excerpt of the member-end reference demonstrates a
possible measurement use. The end-face data is X0 locally; frame reference
STEP retains the original500 x20 x40 source-member geometry after translation.

Display locations are NOT physical measurements, proposed PTO centers, or
global vehicle coordinates. Do not measure clearances between catalogue parts.

Included separate parts:

- existing frame reference excerpt and candidate gauge;
- KP000 relevant66.1 span with other source dimensions marked CAD_REFERENCE;
- exact earlier20T physical-envelope source, unchanged;
- nominal10 shaft, display length40 ONLY, no new cut length or keyway;
- measured100.1 radial envelope with26 axial CAD display extent;
- unchanged provisional v09626 60T CAD at102 for discrepancy inspection;
- unchanged Candidate C / MISUMI Groove-1 drivetrain reference.

No fake slide-clutch solid is included. No dimensioned unknown keep-out STEP
is justified. The clutch unknown boundary is explained in SVG/JSON/docs instead.
No new supports, actual fasteners or L-bracket are present. No catalogue-part
collision result is promoted to an installed assembly result.

Required real checks against KP000, shaft,20T, frame and nearby drivetrain are
all present in collision_report.json with null volume/distance and explicit
HOLD_MISSING_INSTALLED_TRANSFORMS. This is NOT a zero-intersection declaration.
Source dimensions alone cannot establish a conservative installed3D clearance.
