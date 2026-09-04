# V002 body / V003 lid local-coordinate audit

## Exact sources

- Body: `cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8/artifacts/bbox_water_dummy_v002_body.step`
  - SHA-256: `9101bce93c2da8c1b9f87bfd38ae184451a7d1bfead4fb3a26ab9f8b36a176b9`
- Lid: `cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority/cad/bbox_lid_wiring_chimney_v003_local_wall_2p4.step`
  - SHA-256: `11582cab5641591f385b521252fe2feeb3f43bba7ed0e72c3591c56bf5ab5c9c`

Both imported as one valid solid. Values below are from actual STEP geometry and builder datum definitions, not file names.

## V002 body

| Datum | Exact local value |
|---|---:|
| BODY_LOCAL_X_MIN/MAX | -120 / +120 mm |
| BODY_LOCAL_Y_MIN/MAX | -95 / +95 mm |
| BODY_LOCAL_Z_MIN/MAX | 0 / 70.895 mm |
| TOP_RIM_LOCAL_Z | 70.000 mm |
| gasket groove floor / body-side contact | 69.500 mm |
| compressed gasket upper / lid-side contact | 70.895 mm |
| LID_MATING_LOCAL_Z | 70.895 mm |
| FLOOR_OUTER_LOCAL_Z | 0.000 mm |
| FLOOR_INNER_LOCAL_Z | 5.000 mm |
| BODY_EXTERNAL_HEIGHT | 70.895 mm including hard stops; 70.000 mm core shell |
| BODY_INTERNAL_USABLE_HEIGHT | 65.000 mm |

The `240 × 190 mm` total XY bounds include external M4 lugs. The sealed shell core is `200 × 150 × 70 mm`; its cavity is `192 × 142 × 65 mm`. The selected G18-B groove depth is `0.5 mm`; the hard-stop gap is `0.895 mm`. The builder’s compressed-gasket reference therefore spans `Z69.5..70.895 mm`.

## V003 lid

| Datum | Exact local value |
|---|---:|
| LID_LOCAL_X_MIN/MAX | -120 / +120 mm |
| LID_LOCAL_Y_MIN/MAX | -95 / +95 mm |
| LID_LOCAL_Z_MIN/MAX | 0 / 58 mm |
| BODY_MATING_LOCAL_Z | 0.000 mm |
| GASKET_CONTACT_LOCAL_Z | 0.000 mm |
| FLAT_LID_TOP_LOCAL_Z | 8.000 mm |
| LID_HIGHEST_LOCAL_Z (whole part) | 58.000 mm |
| CHIMNEY_HIGHEST_LOCAL_Z | 58.000 mm |

The flat lid is 8 mm thick. The 50 mm chimney begins at the flat lid top and reaches local `Z58 mm`. The phrase “lid highest” must therefore not be silently equated with flat lid top.

## Mathematically correct join

The lid mating/contact plane at local `Z0` is placed on the V002 compressed-gasket/hard-stop plane at body-local `Z70.895`:

```text
V003_LID_RELATIVE_TO_V002_BODY
Tx = 0.000 mm   Ty = 0.000 mm   Tz = 70.895 mm
Rx = 0.000 deg  Ry = 0.000 deg  Rz = 0.000 deg
```

Result:

```text
assembly Z min =   0.000 mm
assembly flat lid top = 78.895 mm
assembly chimney top = 128.895 mm
assembly Z max = 128.895 mm
assembly total height = 128.895 mm
```

This join is independent of rover placement and uses mating datums, not bounding-box alignment.
