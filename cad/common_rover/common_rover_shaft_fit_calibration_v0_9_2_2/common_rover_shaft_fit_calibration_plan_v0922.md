# Common Rover shaft-fit calibration plan v0.9.2.2

Status: `NOT_FOR_MANUFACTURING`, `NO_LOAD_ONLY`, `PHYSICAL_FIT_SELECTION=PENDING_TEST`.

This lane separates two different fit contracts. P0–P5 are split clamps for
radial positioning; S0–S6 are short sleeves for straight hand sliding. Results
from one family must not be transferred to the other.

## Evidence and dimensional policy

The audited 60T source resolves `D_REF_CAD=10.10 mm`; the independent physical
reference is `D_REF_ACTUAL=10.1 mm`. Equal numbers do not make the physical
measurement the CAD authority. Printed comparison gauges were generally
0.1–0.4 mm undersize in X/Y while 5 mm thickness measured 5.0 mm. There was no
clear X/Y directional split and the result was not Z-only. Therefore
`GLOBAL_SCALE_CORRECTION=PROHIBITED`.

The v0.9.2.1 U block has local entry tightness followed by about 1.4 mm
diametral play. It fails radial positioning and remains only a rough, no-load
support.

## Geometry

Each clamp half is a separate watertight candidate. Its split face contains a
semicircular groove and lies at print Z=0. When assembled, planar hard-stop
lands touch at the shaft-axis plane; M3 candidate holes do not define the bore.
Sleeves print with the functional bore vertical, with only 0.4 mm entry/exit
chamfers. IDs use 1–7 geometric holes; there is no embossed or floating text.

Print `PLATE-C` first: P1/P2/P3 plus S1/S2/S3/S4. Print the full A/B plates only
if that subset does not yield one compliant candidate per family.

Selections, load capacity, machining, manufacturing and physical fit remain
HOLD. Powered testing and field deployment are NOT_APPROVED. The v0.9.2.1
authority pointer is intentionally unchanged.
