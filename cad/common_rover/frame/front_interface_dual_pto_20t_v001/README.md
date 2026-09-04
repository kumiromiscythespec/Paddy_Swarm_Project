# Common Rover Front Interface Authority V001

Status: `CAD_PASS/CONTRACT_TEST_PASS/FRONT_INTERFACE_AUTHORITY_CANDIDATE_READY/PHYSICAL_VALIDATION_PENDING`  
Classification: `NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING`

## Result

This isolated lane defines a reusable front interface with two mechanically independent PTO half-shafts, four KP000 references, a 400 mm 2040 transverse beam, explicit pulley/belt keep-outs, and a separate four-point unit-load portal. The user-supplied physical datum is `Z=122.5 mm` from crawler-bottom/floor `Z0`; PTO and drive axes differ by exactly `0.0 mm` in CAD.

Torque path and structural load path remain separate:

- `PTO_LOAD_ROLE = ROTATIONAL_TORQUE_ONLY`
- `UNIT_MOUNT_LOAD_ROLE = WEIGHT + WORK_REACTION + IMPACT + ATTITUDE_CONTROL`

The available exact 20T STEP is retained only as a hashed external source because its 6.1 mm legacy bore conflicts with the current 10 mm PTO shaft. This lane therefore uses a conservative Ø35×20 mm reference envelope and retains `PTO_20T_GEOMETRY_AUTHORITY_PENDING`. No 60T PTO geometry is present.

The combined STL is a coloured-agnostic assembly/reference mesh only. It is **not** a printable monolithic bracket. Standard extrusion, A5052 candidate plates, KP000, shafts and pulleys remain separate physical parts.

## Candidate layout

| item | value |
|---|---:|
| PTO / DRIVE axis Z | 122.5 mm |
| KP000 centers per side | 50 / 100 mm from center |
| KP000 pair spacing | 50.0 mm |
| pulley center plane | ±130.0 mm |
| bearing-plane to pulley-plane overhang | 30.0 mm |
| housing-to-pulley actual gap | 11.5 mm |
| independent shaft center gap | 60.0 mm |
| unit mount rectangle | 150×130 mm |

Local input-pulley adjustment is 10–20 mm candidate; the work unit itself stays fixed. No diagonal member is used. Straight orthogonal members and future shear-panel attachment provisions carry the architecture.
