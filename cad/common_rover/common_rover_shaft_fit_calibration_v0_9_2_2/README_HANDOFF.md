# Common Rover v0.9.2.2 shaft-fit calibration handoff

This exact 45-path package contains no-load physical fit coupons, not final
parts. The audited source reference is 10.10 mm CAD. P0–P5 test radial
positioning using hard-stop split clamps; S0–S6 test straight hand sliding.

Start with `PS-CR-V0922-MINIMUM-FIRST-PASS-PLATE` (P1/P2/P3 and
S1/S2/S3/S4). Import the STL without rotation. Record the unmodified, pre-deburr
result first. Do not scale the plate globally.

Run:

    python -B build_shaft_fit_calibration_v0922.py --verify
    python -B tests/test_shaft_fit_calibration_v0922.py

The current authority remains v0.9.2.1. Selection, machining, load capacity,
manufacturing and physical fit are HOLD. Powered test and field deployment are
NOT_APPROVED.
