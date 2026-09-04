# Paddy Swarm Project — ChatGPT Repository Index

This file is the single first entry point for repository inspection. Follow the
links below before treating a dimension, CAD result, or physical observation as
authority. `CAD_PASS` never means `PHYSICAL_AUTHORITY`.

## Repository state

- Project: `kumiromiscythespec/Paddy_Swarm_Project`
- Branch at publication: `agent/organize-untracked-cad-assets-20260725`
- Base HEAD inspected before normalization: `7c149a65053f2292bc4cc0ed06d8941c96852f2b`
- Publication date: `2026-09-05` (Asia/Tokyo)
- Repository status: authority-indexed normalization snapshot; use the branch tip as the publication commit
- Detailed pre-flight record: [`docs/repository/REPOSITORY_STATE.md`](docs/repository/REPOSITORY_STATE.md)
- Machine-readable authority records: [`docs/repository/REPOSITORY_TREE_MANIFEST.json`](docs/repository/REPOSITORY_TREE_MANIFEST.json)

## Current Common Rover

| Scope | Current entry | Status boundary |
|---|---|---|
| Common Rover design | [`CURRENT_COMMON_ROVER_AUTHORITY.md`](CURRENT_COMMON_ROVER_AUTHORITY.md) | Explicit pointer remains inward-PTO v0.9.2.1; physical fit/load/powered/field are HOLD |
| Physical dimensions | [`COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md`](cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md) | Direct and derived as-built measurements only; no powered/dynamic promotion |
| Frame | [physical dimensional authority](cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md) and [Front Interface V002](cad/common_rover/frame/front_interface_dual_pto_20t_v002/DESIGN_AUTHORITY.md) | Physical rail/Z record is current; V002 is CAD/contract PASS with physical validation pending |
| Drivetrain | [Candidate C keeperless V003](cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003/README.md) | Print-ready CAD; spacer stack and powered validation pending |
| PTO | [`docs/repository/PTO_AUTHORITY_MAP.md`](docs/repository/PTO_AUTHORITY_MAP.md) | Measured 20T envelope exists; direction has an authority conflict; output-shaft final length/projection, load and powered test are unresolved |
| BBOX | [Compact Field BBOX V004 G065](cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/COMPACT_FIELD_BBOX_V004_G065_DESIGN_AUTHORITY.md) | G065 closed-dummy seal water PASS only; full-box/chimney/gland/global integration pending |
| CBOX | [v0.9.6.32 design authority](cad/common_rover/common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32/docs/DESIGN_AUTHORITY.md) | CAD shell/carrier authority; lid, water, thermal, powered and installed Z remain HOLD |
| CBOX mount | [Top-T-slot saddle V002](cad/common_rover/bbox_cbox/cbox_transverse_top_tslot_saddle_v002/README.md) | Coupon print first; full saddle, fit and load remain HOLD |
| Crawler drive | [Candidate C physical result](cad/common_rover/drivetrain/crawler_candidate_c_full_12t_sprocket_v001/CANDIDATE_C_PHYSICAL_RESULT.md) and [keeperless V003](cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003/README.md) | Candidate C is `HOLD_NEAR_PASS`, not full crawler physical PASS |
| Crawler idler | [Candidate C idler V001](cad/common_rover/drivetrain/crawler_idler_candidate_c_v001/README.md) | CAD/contract PASS; slicer and physical validation pending |

The detailed component and historical map is
[`docs/repository/COMMON_ROVER_AUTHORITY_MAP.md`](docs/repository/COMMON_ROVER_AUTHORITY_MAP.md).

## Physical validation

### PASS

- Two physically modified MISUMI shafts were each shortened by 12.0 mm and fit fully in KP000; approximately 1 mm spare was reported and no frame/other interference was observed. This record belongs to the Candidate-C crawler torque path and is **not** silently relabelled as PTO output-shaft length authority.
- The shortened physical key record is 19.7 mm minus 3.0 mm = 16.7 mm; length match PASS for the recorded Candidate-C drivetrain use.
- BBOX G065 closed-dummy seal: 60-minute upright plus four >10-degree tilt directions PASS, witness dry, no leak. This is seal-section/perimeter evidence only.
- GoldenMate battery insertion/presence in the temporary BBOX specimen is a physical fit PASS. It does not establish waterproofing, restraint, vibration, or V003/V004 lid fit.
- CAD/contract tests reported by individual lanes remain valid as CAD/contract evidence only.

### FAIL

- Candidate B crawler tooth fit is `FAIL_LOOSE`.
- CBOX cross-saddle V001 side-wall/side-M5 rail interface is `PHYSICAL_FIT_FAIL`; V002 is the replacement candidate.
- BBOX V003 G050 full-body groove is superseded unvalidated seal geometry; it was not the successful water-test specimen.

### HOLD

- PTO direction precedence between the declared inward v0.9.2.1 authority and later outward v0.9.6.38 interface candidate.
- PTO output-shaft exact final length, projection, retention, bearing/product selection, torque capacity and powered operation.
- PTO P20/P22/P25 placement-gauge physical result sheets and P25 slide-fit coupon selection are blank/pending.
- Full Common Rover integrated physical fit, powered test, load capacity, water/mud operation and field deployment.
- Full BBOX waterproofing including chimney/gland; CBOX water/thermal/powered tests; BBOX/CBOX installed transform.
- Crawler full-loop, powered dry run, dynamic clearance and field durability.

## Current blockers

- `AUTHORITY_CONFLICT`: inward versus outward independent PTO direction. No chronology-based promotion is permitted.
- No repository evidence uniquely ties the physically shortened MISUMI crawler shafts to the PTO output shafts.
- Exact previous MISUMI shaft order length/SKU is unproven, so an exact reorder length is not published.
- BBOX physical X/Y registration and exact interpretation of Z148/Z254 remain incomplete.
- CBOX physical component/service envelopes and final installed transform are incomplete.

## FIELD validation pending

Powered motion, load, dynamic crawler clearance, waterproof integrated rover,
mud operation, durability, field safety, manufacturing release, purchasing
release, and deployment approval all remain pending or not approved.

## Superseded designs

- Front-drive dual-PTO v0.8 through v0.8.5 are retained as design history.
- v0.9.0 through v0.9.2 are retained as the ancestry of the declared v0.9.2.1 design authority.
- Candidate/trade-study, temporary pulley, failed fit, and earlier BBOX/CBOX lanes remain in place and must not be mistaken for current physical authority.
- BBOX V003 G050 full-body seal geometry is superseded by the V004 G065 design; only the tested G065 dummy result is physical water authority.
- GoldenMate `99.4 mm` as a plan width is superseded; it is the measured terminal-inclusive vertical height. Current body mapping is 150.9 × 65.5 × 92.5 mm.

## Independent subprojects

The following are preserved as independent lanes and do not define Common Rover
authority: `cad/accessories`, `cad/ps_mht_v001`,
`cad/ps_mht_v001_phase3ig_lower_return_buffer`, siphon-primer packages,
`cad/ps_usb_inline_raincover_*`, and `cad/ps_webcam_rainhood_*`.

## Authority precedence rules

1. Explicit, scoped physical PASS or direct physical measurement.
2. Current authority document within the same scope.
3. Dated physical-authority lane and its source trace.
4. SHA-256 manifest / immutable validation evidence.
5. CAD and contract validation.
6. Older design candidate or trade study.

Conflicting scopes do not merge automatically. A newer folder name does not by
itself promote authority. Direct physical facts stay coupled to the tested
specimen, datum, and test scope. Blank result templates are never PASS.

## Key files for ChatGPT

- [`CURRENT_COMMON_ROVER_AUTHORITY.md`](CURRENT_COMMON_ROVER_AUTHORITY.md)
- [`docs/repository/COMMON_ROVER_AUTHORITY_MAP.md`](docs/repository/COMMON_ROVER_AUTHORITY_MAP.md)
- [`docs/repository/PTO_AUTHORITY_MAP.md`](docs/repository/PTO_AUTHORITY_MAP.md)
- [`docs/repository/REPOSITORY_STATE.md`](docs/repository/REPOSITORY_STATE.md)
- [`docs/repository/UNTRACKED_CLASSIFICATION.md`](docs/repository/UNTRACKED_CLASSIFICATION.md)
- [`docs/repository/UNTRACKED_FILE_AUDIT.json`](docs/repository/UNTRACKED_FILE_AUDIT.json)
- [`docs/repository/REPOSITORY_TREE_MANIFEST.json`](docs/repository/REPOSITORY_TREE_MANIFEST.json)
- [`docs/repository/GENERATED_ARTIFACT_POLICY.md`](docs/repository/GENERATED_ARTIFACT_POLICY.md)
- [`docs/repository/REMAINING_LOCAL_ONLY.md`](docs/repository/REMAINING_LOCAL_ONLY.md)
