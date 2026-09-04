# DRIVE 112T / 560 mm TPU Physical Test

Test configuration: 20T motor pulley, 60T driven pulley, HTD 5M, measured center distance 180.0 mm, tensioner installed.

| Observation | Result | Classification |
|---|---|---|
| Forward hand rotation | 20 revolutions complete | USER_REPORTED |
| Reverse hand rotation | 20 revolutions complete | USER_REPORTED |
| Derailment | NONE_REPORTED | USER_REPORTED |
| Lateral tracking abnormality | NONE_REPORTED | USER_REPORTED |
| 60T tooth lift | NONE_REPORTED | USER_REPORTED |
| Visible belt damage | NONE_REPORTED | USER_REPORTED |
| 20T tooth lift | PRESENT_LOCALIZED | PHYSICAL_FAIL |
| Recovery | Pulley-only rotation restores engagement | USER_REPORTED |

Final result: `DRIVE_HTD5M_112T_560_TPU = CONDITIONAL_FAIL_TOOTH_LIFT`.

This is a useful physical comparison, not a final selection. It does not establish powered readiness, driving capability, or approval to purchase a commercial 560 mm belt.
