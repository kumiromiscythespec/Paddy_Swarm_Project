# One-Pump 4/6/8-Tower Test Plan

Pump reference: Tencen submersible, DC12 V, 20 W, marked 700 L/h maximum and
6 m head, nominal 13 mm discharge nipple. Dimensions, true nipple diameter,
intake location and minimum submergence are pending physical measurement.

## Sequence

Test 4 towers first, then 6, then 8. Do not proceed when dry-running,
uncontrolled bypass behavior, overflow activation, electrical leakage,
excessive branch CV or insufficient pump-well submergence occurs.

For every stage record:

- actual vertical head from pump-well level to each top outlet,
- pump voltage, current, instantaneous W and accumulated Wh,
- time for each branch to collect 1 L and calculated branch flow,
- minimum, maximum, mean and coefficient of variation across active branches,
- bypass flow, stop-return volume and pump-well drawdown rate,
- LOW/NORMAL/HIGH response and dry-run margin,
- flow before and after intake-strainer cleaning.

Targets are 0.5-1.0 L/min per tower: 2-4 L/min at four, 3-6 at six and 4-8
at eight towers. Eight-tower capability remains `NOT_QUALIFIED` until measured
at the actual head.

The discharge bypass returns to the common pump well and remains available
when every upper branch closes. Top outlets are open; no closed cross-connection
to the fresh-water system is permitted.

## Energy boundary

The DC meter connection is `12V supply -> main fuse -> DC accumulated-energy
meter -> timer/switch -> circulation pump`. Record as
`CIRCULATION_PUMP_ONLY_Wh`, including Wh per run/day/tower/litre. Fresh-water
equipment, sensors and timer standby are separate measurements.
