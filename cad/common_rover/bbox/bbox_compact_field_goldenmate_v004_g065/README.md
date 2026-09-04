# Compact Field BBOX V004 — G065 full-body/lid print candidate

COMPACT_SEAL_G065_WATER_PHYSICAL_PASS/LOCAL_BBOX_V004_CAD_PASS/CONTRACT_TEST_PASS/FULL_BODY_PRINT_READY/FULL_LID_PRINT_READY/FULL_BBOX_WATERPROOF_PHYSICAL_PENDING/GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING

Source package: `D:\Paddy_Swarm_Project\cad\common_rover\bbox\bbox_compact_field_goldenmate_v003`. Water-tested seal: `D:\Paddy_Swarm_Project\cad\common_rover\bbox\bbox_compact_seal_b_water_dummy_v001`. Both read-only.
Torque/drivetrain and unrelated lanes are out of scope. No Git stage/commit/branch changes.

Actual G050 -> G065 depth +0.150000 mm. **Not only a depth edit:** the V003 lid opening broke 42 mm of seal land, and four mid-boss roofs contacted the nominal cord. V004 restores the local lid-thickness sealing bridge and removes only groove roofs. Lower chimney opening changes to 42 x27.5; chimney above Z8, PG9/recess/2.4 wall are unchanged. See SEAL_GEOMETRY_TRACEABILITY.md before printing.

Body 180 x96 x114.395; lid 180 x104 x58; cavity155 x69 x110; all fit A1. First print body and lid, then empty-box water test, then fully dry battery fit/TPU/strap test.
Full-box water and chimney/gland performance are PHYSICAL_PENDING. The user's successful water test was the G065 closed dummy only.

Run from this lane with Python3.12/CadQuery2.8 and -B:

```
python -B build_bbox_v004_g065.py --build
python -B tests/test_bbox_v004_g065.py
python -B build_bbox_v004_g065.py --verify
python -B build_bbox_v004_g065.py --zip
```

The builder depends on protected parent source in the repository; ZIP is an audited new-lane handoff, not a bundled copy of all historical authorities. Do not stage from COMMIT_PATHS without separate user authorization.
STL material/quality checks and depth precision do not establish slicer success. HOLD_SLICER_NOT_RUN.
Strap reference is reservation-only; actual anchoring must be proven before restraining the 1.2kg battery.
