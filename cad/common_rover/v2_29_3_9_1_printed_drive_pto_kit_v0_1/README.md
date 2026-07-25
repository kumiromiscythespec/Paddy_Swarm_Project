# Printed HTD-5M Drive and PTO Transmission Kit v0.1

This source lane produces calibration and low-load test candidates for Common Rover v2.29.3.9.1. It does not approve field use, mud exposure, waterproofing, powered load, unmanned operation, or production.

## Fixed geometry contract

- Profile: HTD-5M printed test candidate
- Pitch: 5.0 mm
- Belt width: 15.0 mm
- 20T pitch diameter: `20 * 5 / pi`
- 60T pitch diameter: `60 * 5 / pi`
- Drive reduction: 3:1
- Drive belt: 450-5M-15, 90 teeth
- Drive center-distance candidate: 121 mm nominal, 112-130 mm adjustment range

The eight pulley bodies have unique engraved part numbers. DRIVE-L/R 20T variants use a parameterized phi6 D-bore and split clamp. All 60T variants include a phi10 candidate bore and PCD24 4xM4 interface. PTO bores remain measurement candidates. Final PTO continuous belts are deliberately not generated.

## Source-reuse audit

The target-worktree search found no HTD-5M pulley or belt implementation in the base. The lane therefore records `SOURCE_REUSE_RESULT = NOT_FOUND_IN_BASE`. Its generalized engraving verifier has explicit behavioral provenance to the base lane’s `COMMON_ENGRAVED_PART_NUMBER_V1`; no dependency folder or source from another branch is copied.

## Generation

Run only in the dedicated CadQuery 2.8 / Python 3.12 environment, with bytecode disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe -B generate_drive_pto_kit.py `
  --repo-root D:\Paddy_Swarm_Project_worktrees\common_rover_v229391_printed_drive_pto_kit_v0_1 `
  --output-dir D:\Paddy_Swarm_Project_work\codex_runs\<timestamp>_common_rover_v229391_printed_drive_pto_kit_v0_1
```

Then run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
C:\Users\yu_ki\Miniforge\envs\paddy-cadquery-280-py312\python.exe -B run_unit_tests.py `
  --artifact-dir D:\Paddy_Swarm_Project_work\codex_runs\<timestamp>_common_rover_v229391_printed_drive_pto_kit_v0_1
```

STL, STEP, manifests, validation reports, checksums, the source patch, and the ZIP bundle are written only to the external artifact directory.

## Print gate

Only `TARGET-P0-CALIBRATION` is initially approved for printing. Measurements must replace `CALIBRATION_PENDING` entries before first-article selection. Joiner-fit belts are hand-fit-only and never powered. All powered and field gates remain HOLD.
