# v0.8.5 tolerance-model correction

`NOT_FOR_MANUFACTURING`

## Superseded behavior

v0.8.4 applied one shared axial assembly error. That correlated component
motion and allowed zero central residual to pass. It also limited relative
KP000-to-pulley error to 1 mm.

## Corrected behavior

Left/right inner KP000, pulley and outer KP000 placement errors are independent
and each range from -1 to +1 mm.

`CENTER_RESIDUAL = CENTER_NOMINAL - LEFT_CENTERWARD_ERROR - RIGHT_CENTERWARD_ERROR`

The center worst case therefore subtracts 2 mm. A residual of zero is FAIL.

`RELATIVE_AXIAL_ERROR = ABS(KP000_ERROR - PULLEY_ERROR)`

The relative worst case is 2 mm.

`BELT_RESIDUAL = BELT_NOMINAL - RELATIVE_ERROR - FRAME_DEFLECTION - BELT_WANDER`

The belt worst allowance is 2 + 2 + 2 = 6 mm.

`PULLEY_RESIDUAL = PULLEY_NOMINAL - RELATIVE_ERROR - RUNOUT`

The pulley worst allowance is 2 + 1.5 = 3.5 mm.

PASS authority comes from mathematical interval analysis and decomposed
boundary enumeration. Monte Carlo is recorded only as a non-authoritative
cross-check.
