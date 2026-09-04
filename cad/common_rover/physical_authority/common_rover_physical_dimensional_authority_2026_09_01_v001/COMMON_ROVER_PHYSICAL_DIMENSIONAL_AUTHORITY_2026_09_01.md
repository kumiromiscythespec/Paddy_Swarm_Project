# Common Rover physical dimensional authority — 2026-09-01

Status: COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01_CAPTURED / MISUMI_SHAFT_KEY_PHYSICAL_UPDATE_CAPTURED / PROCUREMENT_UPDATE_PARTIAL / NO_CAD_MUTATION / NO_GIT_MUTATION

## Authority rule

Direct user physical measurements dated 2026-09-01 take precedence for the current
as-built rover. Raw left/right and range values remain authoritative. Midpoints are
explicitly derived and do not become unmeasured absolute axes.

## Current as-built dimensions

| Group | Physical values | Derived result | Authority note |
|---|---:|---:|---|
| Upper rails Y span | outside 208–210; inside 168–170 mm | each rail 20.0 mm; centers 188–190 mm | absolute rail-axis Y remains PHYSICAL_PENDING |
| Upper rails Z | left top/bottom 255/235; right 254/234 mm | 20 mm height each; 1 mm side offset | 254.5 mm is midpoint only |
| BBOX | lid 254; body bottom 148 mm | 106 mm envelope | approximately flush with rail tops within 1 mm |
| Crawler | left 181; right 180 mm | 54 mm static clearance on both sides | not powered/dynamic clearance |
| DRIVE axis record | left 122; right 123 mm | nominal 122.5 mm | reused from existing physical record |

The old BBOX/frame Z257 assumption, rail Y ±100.5/±80.5 models and drive-axis
Z175/Z178 values are preserved in their source lanes but superseded for this
current as-built record.

## CBOX implication

The 150×246×80 CBOX remains an architectural envelope only. A provisional
floor lower bound of Z191 mm equals crawler-high Z181 + 10 mm and is
DESIGN_TARGET_ONLY. CBOX floor, Cross Base/saddle and a one-piece BBOX/CBOX
base remain HOLD and no geometry is created.

## Release boundary

No CAD, STEP, STL, SVG or DXF is generated or changed. Static dimensions do not
authorize powered motion, dynamic crawler clearance, water/mud testing or field use.
