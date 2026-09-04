# SOURCE_TRACE

## Selected current source

- `cad/crawler_h1/track_module/pretest_candidate_v0_1/source_snapshots/crawler_h1_integrated_sprocket_reinforcement_v0_13_1.py` — tracked v0.13.1 integrated sprocket generator.
- `cad/crawler_h1/track_module/pretest_candidate_v0_1/upstream/contracts/crawler_h1_v0_13_1_design_contract.json` — external tooth profile and integrated-root contract.
- `cad/crawler_h1/track_module/pretest_candidate_v0_1/stl/petg/DRIVE_SPROCKET_V0131_INTEGRATED_B10_3_PCD24_M4.stl` — tracked drive mesh.

The tracked current source defines 12 teeth, phase 15 degrees, 30-degree spacing, tip/root radii 33.07/29.47 mm, tip/root tangential widths 7.5/9.5 mm, 44 mm axial width, 10.3 mm drive bore, and four 4.4 mm holes on PCD24 at phase 45 degrees. It already uses a 4.0 mm buried root extension and reports independent teeth 0.

## Separate-tooth lineage

`USER_REPORTED`: the failed physical article used separate inserted teeth with adhesive reinforcement. Repository search found v0.13.0 references to `crawler_h1_sprocket_fit_test_v0_4_0.py`, but that dependency body is not present in the tracked pretest snapshot. The old separate-tooth CAD is therefore `HOLD_HISTORICAL_GENERATOR_NOT_PRESENT`; it is not reconstructed by inference.

## Shaft and clamp references

- `cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5`: 10.0/10.1/10.2 fit coupon and corrected 10.1 mm no-load reference.
- `cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2`: split-clamp positioning coupons; these are explicitly no-load M3 fit references, not torque hubs.
- No verified metal split-clamp flange-hub product dimensions were found. H1 remains parameter HOLD.
