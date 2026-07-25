# Common Rover v2.29.3.9.1 production-intent input audit v0.1

This source-only lane audits whether real manufacturing inputs exist before any
production-intent geometry is generated. It does not create STL, STEP, STP, or
SVG files. All generated reports must be written outside the repository.

The existing 33 progressive full-scale dummy STL files remain `DUMMY ONLY / NO
LOAD / NOT STRUCTURAL / PROFILE-3 ONLY`. They are not manufacturing parts,
real-rover parts, structural parts, or evidence of compatibility with an
actual aluminum extrusion. Their geometry and part numbers are not
automatically reusable, and removing the dummy marking does not promote them
to production.

The corrected repository-output contract permits the 181 tracked STL and 109
tracked STEP/STP files sealed at base
`242737507c1f94811ff309b36905525057761c45`, provided every baseline file is
unchanged. Added, modified, deleted, or untracked CAD output fails the audit.
The filesystem scan is independent of `.gitignore`.

Run with bytecode disabled:

```text
python -B run_unit_tests.py --json <external>/unit_test_results.json --text <external>/unit_test_results.txt
python -B generate_production_input_audit.py --repository-root <worktree> --output-dir <external> --baseline-inventory <external>/baseline_tracked_cad_inventory.json
python -B validate_production_input_audit.py --repository-root <worktree> --artifact-dir <external>
```

Expected outcome is `PASS_WITH_HOLD`: the audit is valid, but production STL
generation, manufacturing, purchase, and field deployment remain unapproved
until all actual inputs are closed.
