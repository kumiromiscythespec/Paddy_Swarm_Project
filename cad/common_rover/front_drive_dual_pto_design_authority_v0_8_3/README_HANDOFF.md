# Common Rover v0.8.3 measurement integration handoff

This exact 20-file package is an audit and remeasurement
gate, not a manufacturing release.

Runtime: Python 3.12.13, CadQuery 2.8.0.

```powershell
python -B build_common_rover_measurement_integration_v0083.py --verify
python -B tests/test_common_rover_measurement_integration_v0083_contract.py
```

The ZIP is standalone. Repository-present mode verifies all v0.8/v0.8.1/v0.8.2
hashes. Hole centers, shaft cut lengths, pulley bore fit, machining, loading
and field deployment remain HOLD or NOT_APPROVED.
