# B15 selection rationale

## Physical authority

```text
A:
FAIL_OPTICAL
REJECTED

B:
NOMINAL_OPTICAL_PASS
SHIFT_OPTICAL_FAIL
SELECTED_CONDITIONAL

C:
OPTICAL_ROBUST_PASS
KNOWN_FALLBACK
```

## Why B is selected conditionally

- B retains 5 mm more forward rain overhang than C.
- The nominal physical camera view was clear.
- The remaining failure appears when lateral/mount displacement is deliberately introduced.
- v004 separates vertical fastening from lateral/yaw location and tests whether simple guides/stops can keep the camera in the nominal zone.
- A large displacement may make the hood visible and prompt inspection.

That last point is not a safety claim:

```text
NORMAL:
hood intrusion = NONE

EXCESSIVE MOUNT SHIFT:
hood intrusion may become visible

INTERPRETATION:
possible visual indication of camera/mount displacement

SAFETY_FEATURE = FALSE
STATUS_INDICATOR_ONLY = TRUE
```

## Fallback trigger

Propose `FALLBACK_TO_C_SETBACK20` if reasonable non-press-fit guide geometry cannot control shift, B nominal FOV is not repeatable, three reinstall cycles fail, or PETG guide stiffness/durability is inadequate. C has already achieved `OPTICAL_ROBUST_PASS`; a full A/B/C comparison need not be restarted.

