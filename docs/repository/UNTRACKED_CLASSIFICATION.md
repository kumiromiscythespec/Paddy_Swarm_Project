# Initial untracked-file classification

This audit describes the pre-publication working tree captured at START_HEAD
`7c149a65053f2292bc4cc0ed06d8941c96852f2b`. It is not an authority-promotion
mechanism.

## Complete inventory

[`UNTRACKED_FILE_AUDIT.json`](UNTRACKED_FILE_AUDIT.json) contains one record for
each of the 4,616 initially visible untracked files with:

- path;
- byte size;
- extension;
- project/lane;
- likely generated/source/evidence kind;
- A–J classification;
- authority relevance;
- 95 MiB HOLD flag.

The audit is reproducible with
[`../../tools/generate_repository_untracked_audit.ps1`](../../tools/generate_repository_untracked_audit.ps1).

## Conservative classification summary

| Class | Files | Bytes | Publication handling |
|---|---:|---:|---|
| A. CURRENT_DESIGN_AUTHORITY | 12 | 21,383 | Track |
| B. CURRENT_PHYSICAL_AUTHORITY | 53 | 172,409 | Track |
| C. VALIDATION_EVIDENCE | 895 | 70,730,106 | Track |
| D. CURRENT_SOURCE | 221 | 5,626,026 | Track |
| E. HISTORICAL / SUPERSEDED | 40 | 27,298 | Track for provenance |
| F. EXPERIMENTAL / HOLD | 774 | 277,809,836 | Track with HOLD semantics |
| G. GENERATED_REPRODUCIBLE | 1,171 | 811,274,891 | Track when part of a lane/reference/manifest |
| H. DIAGNOSTIC_TEMPORARY | 46 | 71,790,714 | Leave local and ignore narrowly |
| I. INDEPENDENT_PROJECT | 729 | 205,594,087 | Track separately from Common Rover authority |
| J. UNKNOWN_NEEDS_REVIEW | 675 | 762,012 | Preserve and track as provenance; never promote by filename |
| **Total** | **4,616** | **1,443,808,762** | |

`J` is intentionally conservative: many plain Markdown/text files cannot be
promoted from their names alone. Tracking preserves them; authority remains
subject to the precedence maps.

## Top-level project/lane summary

| Lane | Files | Approx. MiB | Classification note |
|---|---:|---:|---|
| `cad/common_rover/**` | 3,688 | 1,094.90 | Mixed authority, physical evidence, source, history, candidates and generated artifacts |
| `cad/ps_mht_v001/**` | 282 | 179.47 | Independent staged tower development; 46 diagnostics ignored |
| `cad/common/**` | 150 | 16.50 | Shared CAD source/reference material |
| `cad/accessories/**` | 77 | 20.96 | Independent accessory projects |
| Siphon-primer lanes | 160 | 31.40 | Independent project/package copies preserved |
| `cad/ps_mht_v001_phase3ig_lower_return_buffer/**` | 65 | 3.23 | Independent later PS-MHT lane |
| USB raincover lanes | 120 | 21.36 | Independent projects |
| Webcam rainhood lanes | 71 | 8.13 | Independent projects |
| `cad/crawler_h1/**` | 2 | 0.97 | Crawler STL evidence/candidates |
| root `tests/**` | 1 | 0.01 | Common Rover contract test |

## Large-file audit

No initially visible untracked file was at or above the 95 MiB HOLD threshold.
The largest was 67,039,221 bytes (about 63.93 MiB). Git LFS was not introduced.

The repository contains about 1.35 GiB of initial untracked content, so files
are committed by logical lane even though no single file crosses the hold gate.

## Ignored diagnostics

Only the 46 PS-MHT Phase 3IB STL intermediates matching `_diag*`,
`_finaldiag*`, `_glue_*`, or `_progress*` under
`cad/ps_mht_v001/exports/preview/` are ignored. They are reproducible debugging
snapshots and no authority document or manifest was found to require them.
They remain on disk. See [`GENERATED_ARTIFACT_POLICY.md`](GENERATED_ARTIFACT_POLICY.md).

The inaccessible `.pytest_cache/` is also ignored as a standard generated test
cache; its contents were not counted, inspected, modified or deleted.
