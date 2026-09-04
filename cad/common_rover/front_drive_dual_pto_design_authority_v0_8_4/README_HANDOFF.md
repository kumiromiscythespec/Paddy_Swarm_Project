# v0.8.4 handoff

`PS-CR-KP000-AXIAL-STACK-V0084` is a 24-file, self-contained design-audit package.

It preserves the two independent PTO architecture and explores KP000
orientation and axial placement in strict Stage order. The recommended
candidate is minimum-change and conditional. Alternative A is the full
specified-sensitivity candidate.

Run:

`python -B build_common_rover_kp000_axial_stack_v0084.py --verify`

`python -B tests/test_common_rover_kp000_axial_stack_v0084_contract.py`

No manufacturing holes, shaft cuts, support-plate machining, load tests or
field use are approved. `NOT_FOR_MANUFACTURING`.
