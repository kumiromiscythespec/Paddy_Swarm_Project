# Common Rover v0.8.2 handoff

This exact 27-file package details the independent inner
KP000 support-plate candidate while preserving v0.8 and v0.8.1.

## Runtime

- Python 3.12.13
- CadQuery 2.8.0

## Commands

```powershell
python -B build_common_rover_kp000_support_plate_v0082.py --verify
python -B tests/test_common_rover_kp000_support_plate_v0082_contract.py
```

The builder supports standalone ZIP extraction. When parent repository paths
are present it verifies all protected hashes; otherwise it verifies the
embedded canonical hash sets.

Every DXF/STEP/SVG hole is a parametric inspection placeholder.
`NOT_FOR_MANUFACTURING`, `PART_MEASUREMENT_REQUIRED`, physical fit HOLD,
machining HOLD and field deployment NOT_APPROVED apply.
