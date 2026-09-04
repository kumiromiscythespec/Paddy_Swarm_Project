# Measurement Ledger

Every value preserves its source classification. Approximate values are not promoted to exact measurements.

| ID | Subsystem | Item | Value | Unit | Classification |
|---|---|---|---:|---|---|
| H25-ARCH | H2.5-A1 | architecture | 2S collar-based shaft retention | text | CAD_REFERENCE |
| H25-COLLAR-OD | H2.5-A1 | collar OD | 15.9 | mm | CAD_REFERENCE |
| H25-COLLAR-ID | H2.5-A1 | collar ID | 10.1 | mm | CAD_REFERENCE |
| H25-COLLAR-W | H2.5-A1 | collar axial width | 3.0 | mm | CAD_REFERENCE |
| H25-M4-COUNT | H2.5-A1 | M4 set screw count | 2 | count | CAD_REFERENCE |
| H25-M4-ANGLE | H2.5-A1 | set screw angle | 90.0 | degree | CAD_REFERENCE |
| H25-RADIAL | H2.5-A1 | full hardware radial envelope | 20.0 | mm radius | CAD_REFERENCE |
| H25-AXIAL | H2.5-A1 | full axial envelope | 8.8 | mm | CAD_REFERENCE |
| H25-LOAD | H2.5-A1 | 24 h load mass | 1.0 | kg | USER_REPORTED / MEASURED_REFERENCE |
| H25-LEVER | H2.5-A1 | lever distance | 70.0 | mm | USER_REPORTED / MEASURED_REFERENCE |
| H25-DURATION | H2.5-A1 | duration | 24.0 | h | USER_REPORTED |
| H25-TORQUE | H2.5-A1 | nominal static torque reference | 0.6864655000000001 | N*m | DERIVED_NOMINAL_REFERENCE |
| H25-SHIFT | H2.5-A1 | shaft shift | NONE | observation | PHYSICAL_PASS_USER_REPORTED |
| H25-ROTATION | H2.5-A1 | collar rotation | NONE_REPORTED | observation | USER_REPORTED |
| H25-CREEP | H2.5-A1 | visible PETG creep | NONE_REPORTED | observation | USER_REPORTED |
| H25-CRACK | H2.5-A1 | visible crack | NONE_REPORTED | observation | USER_REPORTED |
| H25-RESULT | H2.5-A1 | 24 h creep test | PHYSICAL_PASS_USER_REPORTED | status | PHYSICAL_PASS_USER_REPORTED |
| H25-PREV-LOAD | H2.5-A1 | previous short-duration load | 1.2 | kg | SOURCE_REFERENCE |
| H25-PREV-TORQUE | H2.5-A1 | previous nominal torque | 0.8237586 | N*m | DERIVED_NOMINAL_REFERENCE |
| DRV-PITCH | DRIVE | HTD pitch | 5.0 | mm | CAD_REFERENCE |
| DRV-CENTER | DRIVE | 20T to 60T center distance | 180.0 | mm | MEASURED |
| DRV-THEORY | DRIVE | theoretical pitch length | 565.643763 | mm | DERIVED_NOMINAL_REFERENCE |
| DRV-112 | DRIVE | 112T / 560 TPU result | CONDITIONAL_FAIL_TOOTH_LIFT | status | PHYSICAL_CONDITIONAL |
| DRV-112-F | DRIVE | 112T hand rotation forward | 20 | revolutions | USER_REPORTED |
| DRV-112-R | DRIVE | 112T hand rotation reverse | 20 | revolutions | USER_REPORTED |
| DRV-112-DERAIL | DRIVE | derailment | NONE_REPORTED | observation | USER_REPORTED |
| DRV-112-TRACK | DRIVE | lateral tracking abnormality | NONE_REPORTED | observation | USER_REPORTED |
| DRV-112-60LIFT | DRIVE | 60T tooth lift | NONE_REPORTED | observation | USER_REPORTED |
| DRV-112-DAMAGE | DRIVE | visible belt damage | NONE_REPORTED | observation | USER_REPORTED |
| DRV-112-20LIFT | DRIVE | 20T tooth lift | PRESENT_LOCALIZED | observation | PHYSICAL_FAIL |
| DRV-112-RECOVERY | DRIVE | recovery | PULLEY_ONLY_ROTATION_RESTORES_ENGAGEMENT | behavior | USER_REPORTED |
| DRV-113 | DRIVE | 113T / 565 status | NOT_TESTED_IN_THIS_LANE | status | PHYSICAL_TEST_PENDING |
| DRV-114 | DRIVE | 114T / 570 status | PHYSICAL_TEST_PENDING | status | PHYSICAL_TEST_PENDING |
| DRV-STRING | DRIVE | vinyl string loop | 583.0 | mm | MEASURED_USER_REPORTED |
| TEN-X | DRIVE_TENSIONER | position along shaft-center line | 71.0 | mm | MEASURED / USER_REPORTED |
| TEN-OFFSET | DRIVE_TENSIONER | perpendicular offset magnitude | 45.0 | mm approx | APPROX_MEASURED / USER_REPORTED_APPROX |
| TEN-OD | DRIVE_TENSIONER | roller OD | 25.9 | mm | MEASURED / USER_REPORTED |
| TEN-RADIUS | DRIVE_TENSIONER | derived roller radius | 12.95 | mm | DERIVED |
| TEN-D20 | DRIVE_TENSIONER | 20T center to tensioner center | 84.05950273467003 | mm approx | DERIVED_REFERENCE |
| TEN-D60 | DRIVE_TENSIONER | 60T center to tensioner center | 117.92370414806346 | mm approx | DERIVED_REFERENCE |
| TEN-CONTACT | DRIVE_TENSIONER | contact side | BACKSIDE | text | IMAGE_OBSERVED / USER_REPORTED_CONTEXT |
| TEN-STATUS | DRIVE_TENSIONER | 71 / approx45 / OD25.9 | PHYSICAL_REFERENCE | status | PHYSICAL_REFERENCE |
| TEN-FINAL | DRIVE_TENSIONER | final tensioner position | HOLD | status | HOLD |

The 583 mm vinyl-string observation remains recorded even though it conflicts with the derived pitch-length reference.
