# Common Rover v2.29.3.9.1 real profile input registration v0.1

This source-only lane registers two user-confirmed MISUMI purchase records:

- `PROFILE-01`: `NFS5-2020-400`, nominal 20 × 20 mm, 400 mm, quantity 4.
- `PROFILE-02`: `NFSB5-2040-400`, nominal 20 × 40 mm, 400 mm, quantity 4,
  listing colour/finish text `ブラック`.

The order history and supplied Amazon listing references are purchase evidence,
not production cross-section geometry authority. No web lookup is performed.
No customer name, personal order number, shipping address, or payment
information is stored.

Arrival is `PENDING`; measurements, official supplier drawings/tolerances,
accessory compatibility, role assignment, orientation, fit validation, and
structural approval remain `INCOMPLETE` or `HOLD`. Generic MISUMI 5-series
values must not fill missing geometry.

At least two members of each ordered model are assigned separate sample IDs.
The incoming-inspection template records directly accessible external
dimensions at END_A, CENTER, and END_B. Internal cavities and complex slot
geometry require supplier drawings or a separately authorized section cut.

This lane never generates STL, STEP, STP, SVG, or production geometry. All
generated JSON, CSV, Markdown reports, and test results go outside the
repository.

Run with bytecode disabled:

```text
python -B run_unit_tests.py --json <external>/unit_test_results.json --text <external>/unit_test_results.txt
python -B update_production_input_audit.py --repository-root <worktree> --output-dir <external> --baseline-inventory <prior-canonical-artifact>/baseline_tracked_cad_inventory.json
python -B validate_profile_registration.py --repository-root <worktree> --baseline-inventory <prior-canonical-artifact>/baseline_tracked_cad_inventory.json --artifact-dir <external>
```
