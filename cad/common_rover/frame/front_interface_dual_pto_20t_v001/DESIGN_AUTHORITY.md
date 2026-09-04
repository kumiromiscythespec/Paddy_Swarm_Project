# Common Rover Front Interface Authority V001

Status: `CAD_PASS/CONTRACT_TEST_PASS/FRONT_INTERFACE_AUTHORITY_CANDIDATE_READY/PHYSICAL_VALIDATION_PENDING`  
Classification: `NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING`

## Datum authority

`CRAWLER_BOTTOM/FLOOR = Z0`. User physical measurements: left drive center 122.0 mm, right 123.0 mm; nominal authority 122.5 mm; observed range 122–123 mm; ±0.5 mm about nominal; approximate fore/aft tilt 1.0 mm. Historical 178 mm is provisional/obsolete and 175 mm is CAD-only.

## Reused authorities

- KP000: 67×17×35 mm, axis height 18.5±0.5 mm, bore 10 mm, collar protrusion 6 mm; measured mounting-hole centers 53 mm.
- PTO architecture: two independent 10 mm outputs, double supported, HTD5M 20T/20T, 5 mm pitch.
- 20T outside reference: exact protected source hash, bounding reference Ø35×20 mm. Current 10 mm centre interface remains pending.
- 400 mm 2040: declared physical inventory from v0.8; no cutting is released.
- Crawler: Candidate C driven V003, Candidate C idler V001 and reinforced 54 mm link authority are protected source references.

## Formal separation

The PTO shafts are independent segments with a 60 mm centre gap. They are collinear by candidate symmetry but not physically connected. PTO shafts carry torque only. Four unit mount points on the independent rectangular portal carry unit weight, working reaction, impact and attitude restraint. BBOX/CBOX is not a structural brace.

Support plates and all holes are reference-only. No manufacturing hole, shaft cut, spacer, fastener or frame migration is released.
