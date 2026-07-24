# Common Rover v2.29.3.9.1 executable CadQuery seed

This lane is a deterministic, verification-only minimum assembly built from the
sealed `rovers/common_rover/v2.29.3.9.1/` authority. It creates exactly six
axis-aligned CadQuery solids:

1. left FPB rail
2. right FPB rail
3. front crossmember
4. CBOX
5. BBOX
6. battery cassette

The rail and crossmember solids are deliberately classified as
`SIMPLIFIED_TSLOT_AUTHORITY_ENVELOPE`. They are 20 × 20 mm rectangular
verification envelopes, not manufacturing profiles, extrusion selections, or
purchase specifications. No registered maximum-interface-width geometry is
synthesized.

## Run

Use the pinned repository environment:

```powershell
conda run -n paddy-cadquery-280-py312 python -B cad/common_rover/v2_29_3_9_1_executable_cad_seed/validate_seed.py
conda run -n paddy-cadquery-280-py312 python -B cad/common_rover/v2_29_3_9_1_executable_cad_seed/run_unit_tests.py
```

The validator checks single-solid validity, positive finite volume, exact
authority bounding boxes, the two intended rail/crossmember face contacts, zero
unintended volumetric intersections, rail mirror symmetry, the CBOX/BBOX
longitudinal relation, and the three distinct width classes (178 / 286 / 300
mm). Its default STEP roundtrip uses only an operating-system temporary
directory and deletes the file immediately; it never retains a repository STEP
artifact. Pass `--no-step-roundtrip` when only the in-memory gates are needed.

Two dimensionally distinct absolute tolerances are used:

- `linear_tolerance_mm = 1.0e-6` for declared coordinates and bounding boxes.
- `intersection_volume_tolerance_mm3 = 1.0e-9` for Boolean intersection noise
  and verification-only STEP volume replay.

These are exact configuration-contract values. The validator rejects any other
float, including 1.9× or 2× values, NaN, Infinity, zero, and negative values.
The contract values are not compared using themselves as tolerances.

The volume threshold is deliberately much smaller than any modeled feature but
remains a value expressed in mm³; the linear mm tolerance is never reused as a
volume threshold. An intersection volume exactly at the volume tolerance
passes, while any larger volume fails when no volumetric overlap is expected.

Validation is fail-closed. Boolean exceptions, negative/non-finite Boolean
volumes, missing or non-CadQuery objects, and missing/duplicate required
authority records produce structured blockers and `FAIL`. Exception messages,
temporary paths, and memory addresses are not included in deterministic JSON.
Battery placement is confirmed only after all six required hardware-envelope
records have each been found exactly once.

The build result is also closed over the exact six required component IDs.
Missing or extra keys, `None`, another object type, or a non-null solid count
other than six fails validation.

All 15 possible unordered pairs are listed in the report policy matrix. Four
pairs are Boolean checked (the two rail/crossmember contacts, rail separation,
and CBOX/BBOX contact), Battery/BBOX is envelope-checked as
`INTENDED_CONTAINMENT`, and the remaining ten pairs are explicitly
`NOT_AUTHORIZED_FOR_RELATION_ASSERTION`. The reported unintended-intersection
count applies only to the four Boolean-checked pairs; it is not a claim about
unauthorized pairs, and the intentional Battery/BBOX containment overlap is not
counted as unintended.

The successful state is `PASS_WITH_HOLD`. Manufacturing, purchase, field
deployment, waterproofing, structural-strength, executable-CAD release, and
manufacturing-release statuses remain held or unapproved. This seed does not
resolve those authority holds.
