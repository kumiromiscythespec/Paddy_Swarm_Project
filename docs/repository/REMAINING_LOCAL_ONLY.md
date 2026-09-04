# Remaining local-only files

This is the exhaustive list of files that were visible as untracked at the
normalization pre-flight and were intentionally left local. All 46 are
reproducible PS-MHT Phase 3IB exploratory mesh snapshots, are not authority or
manifest inputs, and are covered by the four narrow `.gitignore` patterns
documented in `GENERATED_ARTIFACT_POLICY.md`. No file was deleted.

- `cad/ps_mht_v001/exports/preview/_diag2_chute_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag2_full_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag2_guides_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag2_wick_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag3_full_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_chute_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_cradle_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_dam_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_full_t0.01_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_full_t0.02_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_full_t0.05_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_guides_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_keeper_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_lugs_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_outerroot_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_diag_phase3ib_0.1.stl`
- `cad/ps_mht_v001/exports/preview/_diag_wick_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_finaldiag_cradle_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_finaldiag_full_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_finaldiag_keeper_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_finaldiag_sump_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_glue_False_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_glue_True_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_beforeholes_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_hole0.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_hole120.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_hole240.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_raw0.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_raw120.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress2_raw240.0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_base_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_chute_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_cradle0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_cradle120_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_cradle240_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_guides_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_lug0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_lug120_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_lug240_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_opening_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_port0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_port120_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_port240_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_wick0_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_wick120_phase3ib.stl`
- `cad/ps_mht_v001/exports/preview/_progress_wick240_phase3ib.stl`

The pre-existing `.pytest_cache/` directory is also ignored as generated test
cache. Windows denied directory access during the audit, so its contents could
not be enumerated; the directory was not opened, modified, or deleted.

Other paths matched by ignore rules predate this normalization and were outside
the 4,616-file visible-untracked pre-flight population. They were neither
reclassified nor deleted.
