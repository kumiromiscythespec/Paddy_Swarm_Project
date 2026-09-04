# Common Rover v0.8.4 remeasurement sheet

`NOT_FOR_MANUFACTURING`  
`PART_MEASUREMENT_REQUIRED`

| Priority | ID | Component | Dimension | Current | Instrument | Resolution | Method | Gate |
|---|---|---|---|---|---|---|---|---|
| CRITICAL | C01 | KP000 | opposite-side protrusion | UNKNOWN; scenarios 0..6 mm | CALIPER | 0.1 mm | Measure from housing face to opposite axial extreme on every unit. | ROBUSTNESS_AND_CLEARANCE |
| CRITICAL | C02 | KP000 | mounting-hole center distance | HOLD | CALIPER | 0.1 mm | outer-edge span minus hole diameter; or inner-edge span plus hole diameter. | SUPPORT_PLATE_HOLE_PATTERN |
| CRITICAL | C03 | KP000 | total axial envelope | 17 housing + asymmetric protrusions | CALIPER | 0.1 mm | Measure extreme axial face to extreme axial face and mark collar direction. | PHYSICAL_STACK |
| CRITICAL | C04 | KP000 | actual bore | nominal 10; ruler 11 rejected | CALIPER/BORE_GAUGE | 0.01 mm | Measure multiple clock positions. | SHAFT_FIT |
| CRITICAL | C05 | 60T | actual bore | reported 11; HOLD | CALIPER/BORE_GAUGE | 0.01 mm | Measure and check fit on 10 mm shaft. | PULLEY_BORE_FIT |
| CRITICAL | C06 | 60T | radial runout | scenarios 0..1.5 mm | DIAL_INDICATOR | 0.05 mm | Rotate on representative centered hub. | PULLEY_CLEARANCE |
| CRITICAL | C07 | 60T | hub OD and axial width | HOLD | CALIPER | 0.1 mm | Measure hub separately from toothed body. | AXIAL_STACK |
| CRITICAL | C08 | TOOL | hex-key and socket working envelope | HOLD | CALIPER | 0.1 mm | Measure short arm, bend radius, socket OD and ratchet head. | TOOL_ACCESS |
| HIGH | H01 | ASSEMBLY | axial assembly error | scenario +/-1 mm | ASSEMBLY_GAUGE | 0.1 mm | Measure bearing and pulley face locations after dry assembly. | ROBUSTNESS |
| HIGH | H02 | FRAME | deflection toward PTO belt | scenario 0..2 mm | DIAL_GAUGE | 0.1 mm | Apply representative static fixture load only after approval. | BELT_RESIDUAL |
| HIGH | H03 | BELT | lateral wander | scenario 0..2 mm | VIDEO/RULER | 0.1 mm | No powered test until load-test approval. | BELT_RESIDUAL |
| HIGH | H04 | SHAFT | collars, coupling and retaining widths | HOLD | CALIPER | 0.1 mm | Measure selected components face-to-face. | SHAFT_CUT_LENGTH |

KP000 hole center distance:

`CENTER_DISTANCE = OUTER_EDGE_TO_OUTER_EDGE - HOLE_DIAMETER`

or

`CENTER_DISTANCE = INNER_EDGE_TO_INNER_EDGE + HOLE_DIAMETER`
