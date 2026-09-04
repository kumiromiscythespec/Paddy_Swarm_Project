# Common Rover secondary authority pointer

Document role: compatibility pointer retained under the historical
`rovers/common_rover/` namespace. It summarizes, but does not duplicate, the
repository-root primary pointer.

Current authority is composite and scoped.

Base design lineage:
**common_rover_inward_pto_coupling_cad_verified_v0_9_2_1**

PTO direction physical override:
**PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05_V001**

Current physical PTO direction is left `-X` outward and right `+X` outward.
The inward direction in the base lineage is superseded only for current
as-built direction scope. PTO shafts, supports and torque paths remain
independent; a common PTO shaft remains prohibited.

Canonical entry point: repository-root `CURRENT_COMMON_ROVER_AUTHORITY.md`.

This authority keeps the two-motor, two-independent-PTO, two-slide-clutch and
four-belt functional contract. Named CadQuery Shapes, actual Boolean
intersection volume, OCP distance and nearest-point evidence verify the
central coupling and its 0–10 mm sweep. The no-load dry-fit jig uses two
independent shaft references, independent 12.5 mm stubs and an empty 36 mm
center gap. Upstream powertrain geometry remains inherited conditional, not
full-system actual-CAD verified. Physical fit, machining, shaft cutting, load
and powered rotation remain HOLD.

Status: `FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED`;
`INWARD_PTO_GEOMETRY_CONDITIONAL_PASS` (historical CAD evidence only);
`PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY`;
`CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED`;
`COUPLING_FULL_SWEEP_ACTUAL_CAD_VERIFIED`;
`INDEPENDENT_DRY_FIT_JIG_READY`;
`UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL`;
`LOAD_CAPACITY_HOLD`; `PHYSICAL_FIT_HOLD`; `POWERED_TEST_NOT_APPROVED`;
`NOT_FOR_MANUFACTURING`; `FIELD_DEPLOYMENT_NOT_APPROVED`.

GITHUB_EXECUTABLE_CAD_RELEASE = HOLD
GITHUB_MANUFACTURING_RELEASE = HOLD
PURCHASE_STATUS = NOT_APPROVED
FIELD_DEPLOYMENT_STATUS = NOT_APPROVED

Physical and component-level authority is indexed at
`../../CHATGPT_PROJECT_INDEX.md`; later lanes are not implicitly promoted by
this secondary pointer.
