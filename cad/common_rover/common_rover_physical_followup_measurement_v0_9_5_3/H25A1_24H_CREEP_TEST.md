# H2.5-A1 24 h Creep Test

Architecture: `H2.5-A1 / 2S collar-based shaft retention`

| Item | Value | Classification |
|---|---:|---|
| Load mass | 1.0 kg | USER_REPORTED / MEASURED_REFERENCE |
| Lever distance | 70 mm | USER_REPORTED / MEASURED_REFERENCE |
| Duration | 24 h | USER_REPORTED |
| Shaft shift | NONE | PHYSICAL_PASS_USER_REPORTED |
| Collar rotation | NONE_REPORTED | USER_REPORTED |
| Visible PETG creep | NONE_REPORTED | USER_REPORTED |
| Visible crack | NONE_REPORTED | USER_REPORTED |

Nominal static torque reference:

`T = 1.0 kg × 9.80665 m/s² × 0.070 m = 0.6864655 N·m ≈ 0.687 N·m`

Classification: `DERIVED_NOMINAL_REFERENCE`. The lever-to-gravity angle was not physically measured, so this value is not `PHYSICAL_MEASURED_TORQUE`.

Result: `H25A1_24H_CREEP_TEST = PHYSICAL_PASS_USER_REPORTED`.

The earlier 1.2 kg @ 70 mm result is retained separately as a short-duration source reference (nominal ≈0.824 N·m); it is not promoted to a 24 h PASS. Full sprocket remains `HOLD`, powered rotation and field deployment remain `NOT_APPROVED`.
