# Current motor-layout authority audit v0.9.3.0

This is a read-only comparison. `DESIGN_AUTHORITY_UPDATE=PROHIBITED`.

## Current authority

- Pointer: `rovers/common_rover/v2.29.3.9.1`
- Coordinates: +X lateral left, +Y rear, +Z up.
- CBOX: X -65..65, Y -140..0, Z 0..105 mm.
- BBOX: X -75..75, Y 0..220, Z 0..150 mm.
- Battery cassette: 125 × 180 × 120 mm; extraction proxy remains separately protected.
- Frame rail centers: X ±79 mm; rail sections X 69..89 / -89..-69, Y -232..0, Z 0..20 mm.
- Transformed track comparison proxy: X ±135..145 mm; overall 290 mm; `COMPARISON_PROXY_NOT_CURRENT_EXACT_TRACK_SOLID`.
- Unit mating keep-out: X -72..72, Y -380..-246, Z 0..160 mm.

The v0.9.2.1 lane uses a legacy coordinate convention (+X forward, +Y left) and a much higher motor-Z candidate. Values are compared, not silently selected. The study uses the current v2 coordinate authority because the user explicitly defines total width along X.

## Existing placeholder versus physical motor

The inherited left placeholder is only 18 × 54 × 52 mm (X/Y/Z). It is not treated as JGB37-520 physical geometry. Replacing it at the current motor line leaves a perpendicular offset of **19.235384 mm** to the registered input axis (19 mm lateral, 3 mm vertical), so Candidate G fails coaxial transmission continuity.

The pinned v2.29.3.5 component-registry reference is retained. A working-copy byte difference that can arise from text line endings is recorded and is not auto-reconciled.

## Protected ledgers

| path | files | ledger | result |
|---|---|---|---|
| rovers/common_rover/v2.29.3.9.1 | 45 | 0cb5a1acaa87fde7d36f8cea5f42df2b582f09e8a06ac16eca514377105b0768 | PASS |
| cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1 | 37 | c6c73292a24b37647f65dc16bf5deacf5754af2ef6b17f7a6e0c49402f47bf3e | PASS |
| cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2 | 45 | 880d8b5ac46397c05f419a8344da19f6e710b135b32591c67d53ae1375d7d7bc | PASS |
| cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1 | 55 | d7cb3a99f02b87b9fea4623a60c5b758f1a8796a9514708edc84050321be58c1 | PASS |
| cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2 | 45 | 4e7bed750f1b090276ce40077067aac08ded50a5da3ec8b87f1c79f994e92f92 | PASS |
