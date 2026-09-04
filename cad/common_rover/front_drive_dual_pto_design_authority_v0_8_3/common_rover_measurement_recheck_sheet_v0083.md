# Common Rover v0.8.3 corrected remeasurement sheet

**NOT_FOR_MANUFACTURING — PART_MEASUREMENT_REQUIRED**

Do not transfer a reported value into CAD until its classification and gate are closed.

## Hole-center equations

`CENTER_DISTANCE = OUTER_EDGE_TO_OUTER_EDGE - HOLE_DIAMETER`

or

`CENTER_DISTANCE = INNER_EDGE_TO_INNER_EDGE + HOLE_DIAMETER`

| Priority | ID | Part | Measurement | Current input | Accuracy | Method | Gate |
|---|---|---|---|---|---|---|---|
| CRITICAL | C01 | KP000 | mounting-hole center distance | UNKNOWN | 0.1 mm | Measure outer-edge distance and subtract diameter, or inner-edge distance and add diameter. | Required before support-plate holes |
| CRITICAL | C02 | KP000 | total axial envelope including insert | 17 housing + 6 one side; other side unknown | 0.1 mm | Measure extreme axial face to opposite extreme axial face. | Required for pulley and stack clearance |
| CRITICAL | C03 | KP000 | actual bore | 10 nominal; 11 ruler rejected | 0.05 mm | Measure at two angles and two axial depths; verify with 10 mm pin. | Resolve nominal fit |
| CRITICAL | C04 | 60T | actual bore | 11 reported | 0.05 mm | Measure at two angles/depths without set-screw distortion. | Required before any loaded use |
| CRITICAL | C05 | 60T | center hub OD | UNKNOWN | 0.1 mm | Measure maximum hub cylinder OD, excluding flange. | Required for metal hub/bush concept |
| CRITICAL | C06 | 60T | center hub axial width | UNKNOWN | 0.1 mm | Measure hub extreme face-to-face width. | Required for axial stack |
| CRITICAL | C07 | 60T | tooth-face axial width confirmation | 17 provisional; 3 semantic conflict | 0.1 mm | Measure usable toothed face between flange inner faces. | Resolve 20 vs 21 mm component sum |
| CRITICAL | C08 | T_SLOT | narrow entrance width | UNKNOWN | 0.1 mm | Measure narrowest slot mouth perpendicular to slot. | Required for T-nut insertion |
| CRITICAL | C09 | BOLT | thread major diameter | M5 candidate; 14 likely length | 0.05 mm | Measure thread crest diameter and verify pitch. | Confirm bolt designation |
| CRITICAL | C10 | SOCKET | actual outside diameter | 8 nominal size only | 0.1 mm | Measure largest socket barrel OD used at bolt. | Required for local tool envelope |
| HIGH | H01 | PTO_SHAFT | installed left length | UNKNOWN | 0.5 mm | Measure planned inner shaft end to output end after stack mock-up. | Cut length HOLD |
| HIGH | H02 | PTO_SHAFT | installed right length | UNKNOWN | 0.5 mm | Measure independently; do not mirror without confirming parts. | Cut length HOLD |
| HIGH | H03 | PTO_SHAFT | axial play | ALMOST_NONE qualitative | 0.05 mm | Push-pull assembled shaft and record total travel. | Collar/retention design |
| HIGH | H04 | KP000 | insert protrusion direction | 6 one side | 0.1 mm | Mark shaft-output direction and measure both sides separately. | Worst pulley/belt clearance |
| HIGH | H05 | FASTENER | washer thickness | 4 conflict | 0.05 mm | Measure one washer alone; confirm it is not a stacked pair. | Fastener stack |
| HIGH | H06 | TOOL | hex key short arm and bend radius | UNKNOWN | 0.5 mm | Measure actual short arm from bend tangent and outside bend radius. | Tool sweep |
| HIGH | H07 | TOOL | ratchet head envelope | UNKNOWN | 0.5 mm | Measure maximum head width/thickness with socket installed. | Tool sweep |
| HIGH | H08 | PTO_OUTPUT | collars, coupling and reserve widths | UNKNOWN | 0.1 mm | Measure each axial item face-to-face and define required exposed shaft. | Installed shaft length |

Record left and right separately, photograph the reference faces, and include the measuring tool in the photo. Manufacturing remains HOLD.
