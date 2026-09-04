# BBOX Installed Transform + Front Interface Registration Audit V001

Status: `TRANSFORM_PARTIAL_PHYSICAL_MEASUREMENT_REQUIRED`

This is a documentation/reference-registration lane only. It creates no manufacturing CAD, STEP, STL, DXF, print-ready body, cradle, or release geometry.

The exact V002 body and V003 lid join is resolved locally: the lid is translated by `(0, 0, 70.895) mm` without rotation. The resulting CAD assembly spans local `Z=0..128.895 mm`. The direct current-rover record spans global `Z=148..254 mm`, or `106 mm`; however, the record does not identify whether `254 mm` is the flat lid top, the chimney top, or another lid feature. The physical source also says only “lowest BBOX body point,” not specifically the shell-floor plane.

No direct physical BBOX X or Y locator was found. Front Interface V002 is a CAD authority with selected physical inputs, but manufacture, current installation, and its installed X/Y/Z transform remain unproven. Therefore the earlier H108/H110/H112/H116 intersections remain `CAD_REGISTERED_CONFLICT`, not a physical-solid finding, and collision promotion was not rerun.

H108 remains `HEIGHT_CANDIDATE`. It may return to design study only after the measurement plan closes the BBOX feature identity, BBOX X/Y/Z registration, and Front Interface installed-state/transform gates.

Key files:

- `BBOX_INSTALLED_TRANSFORM_AUDIT.md`: decision and transform candidates.
- `V002_V003_LOCAL_COORDINATE_AUDIT.md`: exact STEP geometry and join.
- `PHYSICAL_Z_SOURCE_TRACE.md`: origin and ambiguity of Z148/Z254.
- `BBOX_XY_SOURCE_AUDIT.md`: physical-vs-CAD placement evidence.
- `FRONT_INTERFACE_PHYSICAL_STATUS_AUDIT.md`: CAD and physical status separation.
- `COLLISION_CLASSIFICATION_AUDIT.md`: prior collision classification.
- `BBOX_PHYSICAL_REGISTRATION_MEASUREMENT_PLAN.md`: exact current-rover measurements required.
- `transform_candidates.json`, `validation_report.json`: machine-readable audit.

No protected source was modified. Git staging, commit, branch/HEAD change, push, pull, checkout, reset, restore, clean, or stash was not performed.
