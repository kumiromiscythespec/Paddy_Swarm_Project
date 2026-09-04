# Spacer / gauge variant comparison

|Candidate|Working length mm|Nominal residual mm|Role|Installed clearance / winner|
|---|---:|---:|---|---|
|P20|20.0|3.0|MINIMUM_SPACE_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|
|P22|22.0|5.0|BALANCED_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|
|P25|25.0|8.0|HIGHER_CLEARANCE_CANDIDATE|HOLD / PHYSICAL_TEST_PENDING|

All three reuse the same 18 x8 mm end section and independent PETG gauge
construction. Printed working lengths require caliper measurements; CAD does
not compensate by changing requested20/22/25 dimensions.

Actual installed interference, bolt/T-nut/set-screw access, 20T screw access,
shaft withdrawal, wrench/hex-key paths, both belt paths, tensioning and pulley
removal are HOLD for every candidate. Null values in collision_report.json
mean NOT EVALUATED from an installed transform, never zero interference.

No automatic P20 selection. Start static checks at P25 if helpful, then compare
P22 and P20 after safe independent support is established. Select the shortest
candidate that physically passes ALL interference and service checks.
