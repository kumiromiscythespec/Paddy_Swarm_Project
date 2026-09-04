# Common Rover v0.8.1 handoff

This package contains only the v0.8.1 belt-clearance study. It does not contain
the repository's unrelated untracked files.

Status: physical fit HOLD; cutting/drilling/manufacturing/load/water/mud HOLD;
field deployment NOT_APPROVED.

## Rebuild

Required environment:

- Python 3.12.13
- CadQuery 2.8.0

From the extracted package root:

```text
python -B build_common_rover_front_drive_dual_pto_v0081.py --refresh-artifacts
python -B build_common_rover_front_drive_dual_pto_v0081.py --verify
python -B tests/test_common_rover_front_drive_dual_pto_v0081_contract.py
```

The builder is self-contained apart from Python/CadQuery. It does not import
files outside this package. `common_rover_front_drive_dual_pto_baseline_v0081.json` embeds the v0.8 baseline metrics
and preservation hashes.

`SHA256SUMS.txt` hashes every package file except itself. `MANIFEST.txt` lists
the exact 19 package paths.
