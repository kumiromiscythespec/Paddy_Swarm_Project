# Common Rover motor-bracket to 2040 adapter v0.9.3.2

This handoff contains two no-load adapter pilot variants, an eight-hole M4 calibration coupon, seven STEP references, eight 1:1 SVG drawings, measurement records, and contract tests.

Recommended sequence: print coupon → calibrate actual M4 screw → print one C360 adapter → check M5×16/T-nut and bracket alignment → print the second identical adapter only after fit confirmation.

Run `python -B build_motor_bracket_adapter_v0932.py --verify` and `python -B tests/test_motor_bracket_adapter_v0932.py` with CadQuery 2.8. Do not energize, rotate, tension a belt, transmit torque, cut/drill metal, or treat this PETG mockup as manufacturing authority.
