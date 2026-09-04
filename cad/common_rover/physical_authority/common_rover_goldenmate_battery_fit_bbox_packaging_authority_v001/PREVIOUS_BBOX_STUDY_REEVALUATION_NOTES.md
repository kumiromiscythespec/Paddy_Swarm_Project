# Previous BBOX study reevaluation notes

## Field Box V001

The previous report used `150.9 × 99.4 mm` as the battery plan envelope. Therefore these conclusions require reevaluation:

- Orientation A Y clearance `(142-99.4)/2 = 21.30 mm/side`;
- Orientation B X clearance `(192-99.4)/2 = 46.30 mm/side`;
- all cradle pocket XY values derived from plan width `99.4 mm`;
- battery-body Boolean volumes built with a `99.4 mm` plan side;
- any orientation ranking based on those plan dimensions.

They are classified `REQUIRES_REEVALUATION_AFTER_BATTERY_AXIS_CORRECTION`.

The V002 cavity-height failure remains independently supported: body height `92.5 mm` and terminal-inclusive height `99.4 mm` both exceed the protected `65 mm` internal usable height. The exact old Boolean volumes must still be regenerated because their plan envelope was wrong, but the sign of the vertical shortage does not change.

## Tall BBOX H108/H110/H112/H116

The terminal clearances `H - support - 99.4` and body clearances `H - support - 92.5` use the corrected vertical roles and remain arithmetically meaningful. Nevertheless:

- any plan-fit or local packaging claim that inherited `99.4 mm` as width requires reevaluation;
- any battery Boolean envelope based on the old XYZ tuple requires reevaluation;
- candidate selection must consider the new physically successful `152 × 65.5 × 104 mm` internal specimen and field allowances;
- H108/H110/H112/H116 remain unselected.

The separate frame-registration issue is unchanged: prior Front Interface intersections remain `CAD_REGISTERED_CONFLICT`, with physical BBOX XY and Front Interface installed transforms unresolved. Battery-axis correction does not resolve or invalidate that transform HOLD.

Overall label:

`H108_H110_H112_H116 = REQUIRES_REEVALUATION_AFTER_BATTERY_AXIS_CORRECTION_AND_REGISTRATION_CLOSURE`
