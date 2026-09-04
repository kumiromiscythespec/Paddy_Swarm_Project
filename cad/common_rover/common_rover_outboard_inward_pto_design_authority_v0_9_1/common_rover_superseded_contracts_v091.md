# v0.9.1 Superseded Contracts

Protected parent v0.9.0:

- `LEFT_PTO_OUTPUT_DIRECTION = +Y`
- `RIGHT_PTO_OUTPUT_DIRECTION = -Y`
- meaning: outward PTO outputs

Conditional v0.9.1 replacement:

- `LEFT_PTO_OUTPUT_DIRECTION = -Y`
- `RIGHT_PTO_OUTPUT_DIRECTION = +Y`
- meaning: inward PTO outputs
- left/right shafts remain independent
- left/right couplings remain independent
- left/right torque paths remain independent
- a direct left/right output edge is prohibited

The v0.9.0 clearance values 4.75/5.0/3.5 mm are preserved as baseline
records but do not satisfy the new v0.9.1 clearance authority.  They are
superseded by the 5/8/10 mm contracts in
`common_rover_clearance_contract_v091.md`.

No protected parent byte is changed.  This replacement becomes the current
repository pointer only after all v0.9.1 gate checks pass.

`PHYSICAL_FIT_HOLD` · `NOT_FOR_MANUFACTURING`
