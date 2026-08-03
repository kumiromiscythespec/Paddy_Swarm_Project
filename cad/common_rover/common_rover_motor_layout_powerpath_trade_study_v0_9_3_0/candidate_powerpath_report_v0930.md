# Candidate powerpath report v0.9.3.0

| ID | sequence | physics | result |
|---|---|---|---|
| P1 | motor X → selector X → INWARD_X_INDEPENDENT | common pattern, never a common physical left-right shaft | CONDITIONAL |
| P2 | motor X → selector X → INWARD_X_INDEPENDENT | separate DRIVE/PTO jackshaft candidates | CONDITIONAL |
| P3 | motor Y → selector X → INWARD_X_INDEPENDENT | one explicit bevel pair per side | CONDITIONAL |
| P4 | motor Y → selector Y → FORWARD_NEGATIVE_Y_INDEPENDENT | PTO remains Y; DRIVE branch alone uses bevel | CONDITIONAL |
| P5 | motor Z → selector X → INWARD_X_INDEPENDENT | vertical motor requires explicit bevel | CONDITIONAL |
| P6 | motor FUTURE_PRODUCT → selector X_OR_Y → PRODUCT_SELECTION_HOLD | envelope-only future comparison; PURCHASE_HOLD | PURCHASE_HOLD |

No belt or chain changes axis by 90 degrees. P3/P4/P5 use an explicit bevel or miter pair; P6 is only a future right-angle-gearmotor envelope. Left and right remain independent and no common cross-shaft is introduced. Metal pulley, bearing, bevel, shaft, brake, and dog geometry require product selection and physical measurement.
