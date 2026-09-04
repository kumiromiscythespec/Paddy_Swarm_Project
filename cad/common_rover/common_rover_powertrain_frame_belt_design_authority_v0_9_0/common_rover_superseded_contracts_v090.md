# v0.9.0 superseded contracts

## Superseded

`Z_PTO_AXIS >= Z_MOTOR_AXIS`

Status: `SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO`.

The historical v0.8 through v0.8.5 files remain byte-protected and are not
rewritten.

## Current conditional contract

`PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS`

if and only if:

- `PTO_ROTATION_ENVELOPE_BOTTOM_Z >= 200`
- all four belt safety envelopes avoid frame, fasteners, supports, wiring,
  sensors, actuators, box supports and track dynamics;
- clutch full stroke avoids frame and belts;
- the PTO remains forward of the motor and outside the work-unit removal path.

Z=260 is boundary-only and not a standard candidate. Z>=280 is the standard
candidate range; Z>=280 also gives an OD120 envelope bottom of at least Z=220.
