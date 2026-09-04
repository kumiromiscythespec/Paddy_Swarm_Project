# Generated artifact policy

Generated does not mean disposable. This repository uses generated outputs as
review surfaces, printable deliverables, geometry references, validation
evidence, and reproducibility checks.

## Track

- final and named-reference STEP/STP;
- final and print-oriented STL/3MF;
- source Python and structured specification JSON/YAML/CSV;
- authority, physical result, failure and supersession records;
- validation reports, audit JSON, test logs, manifests and SHA256SUMS;
- diagrams and previews referenced by a lane or needed to interpret a result.

## Ignore narrowly

- Python bytecode and test caches;
- machine-local slicer output already covered by `*.gcode`;
- the 46 reproducible PS-MHT Phase 3IB exploratory STL snapshots whose names
  begin `_diag`, `_finaldiag`, `_glue_`, or `_progress` in the single preview
  directory.

Those diagnostic files are retained locally and were not deleted. The ignore
patterns do not cover final/reference STL or any JSON, Markdown, STEP, manifest,
physical result, or source file.

Their exhaustive path list is in
[`REMAINING_LOCAL_ONLY.md`](REMAINING_LOCAL_ONLY.md).

## Change rule

Do not broaden ignore patterns merely to make `git status` clean. Before a new
generated class is ignored, verify that it is reproducible, is not referenced
as authority/evidence, and is not the only record of a physical result.
