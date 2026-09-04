# Design authority

The repository does not provide one mechanically consistent BBOX/CBOX dimension set. The conflict is recorded and no synthetic value is created.

| lineage | BBOX | lid / gasket | CBOX | use here |
|---|---|---|---|---|
| v2.28 fixed core | 200×150×120 | lid 216×166×16 nominal; gasket 204×154×3 | fixed-core relationship | BBOX display reference only |
| v0.9.6.0 submerged | lower shell 200×130×97 | lid 200×130×4.2; gasket outer 186×116×2 | 180×92×45 | separate submerged authority |
| v0.9.6.32 modular CBOX | n/a | n/a | body 246×150×80; print bbox 246×152×80 | exact local CBOX geometry; vehicle transform HOLD |

`AUTHORITY_CONFLICT_RECORDED_NO_SYNTHETIC_UNIFIED_DIMENSION`.

The concept STEP uses v2.28's 200×150×120 BBOX only as a labelled display reference, the measured 150.9×99.4×92.5 mm 12.8 V LiFePO4 prototype battery as a physical envelope reference, and the exact v0.9.6.32 CBOX shell in local coordinates. The displayed CBOX Z and symmetric ± lateral examples are not position, direction, or stroke authority.

Protected principles: HIGH_MOUNTED_DUAL_MOTOR_4WD_ARCHITECTURE, BBOX_CBOX_SEPARATION, REMOVABLE_BATTERY_CASSETTE_CONCEPT, LIFEPO4_12_8V_CURRENT_PROTOTYPE_BATTERY_AUTHORITY, INDEPENDENT_LEFT_RIGHT_DRIVE, CURRENT_CRAWLER_AND_PTO_ARCHITECTURE, CURRENT_SEALING_TEST_HISTORY, EXISTING_REAR_SLIDE_RESEARCH_ARTIFACTS.
