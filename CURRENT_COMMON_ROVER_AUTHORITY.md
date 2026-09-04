# Current Paddy Swarm Common Rover Authority

Document role: repository-root primary pointer for the explicitly declared
Common Rover **design authority**. It is not a claim that every later component
lane has been promoted to one physically validated rover.

For the dated physical authority, component authorities, resolved PTO
direction decision, and validation boundaries, start at
[`CHATGPT_PROJECT_INDEX.md`](CHATGPT_PROJECT_INDEX.md).

Current authority is composite and scoped.

Base design lineage:
**common_rover_inward_pto_coupling_cad_verified_v0_9_2_1**

Canonical document:
`cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1/common_rover_inward_pto_coupling_cad_verified_design_authority_v0921.md`

PTO direction physical override:
**PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05_V001**

Canonical override document:
`cad/common_rover/pto/physical_authority/pto_outward_direction_physical_authority_2026_09_05_v001/PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY_2026_09_05.md`

The inward PTO direction defined by v0.9.2.1 is superseded for the current
as-built rover. Current physical PTO direction is left `-X` outward and right
`+X` outward. The shafts, bearing/support arrangements and torque paths remain
independent, and a common PTO shaft remains prohibited.

Status:

- `FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED`
- `INWARD_PTO_GEOMETRY_CONDITIONAL_PASS` (historical CAD evidence only)
- `INWARD_PTO_DIRECTION_SUPERSEDED_BY_PHYSICAL_OUTWARD_DIRECTION`
- `PTO_OUTWARD_DIRECTION_PHYSICAL_AUTHORITY`
- `CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED`
- `COUPLING_FULL_SWEEP_ACTUAL_CAD_VERIFIED`
- `INDEPENDENT_DRY_FIT_JIG_READY`
- `UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL`
- `PHYSICAL_FIT_HOLD`
- `LOAD_CAPACITY_HOLD`
- `POWERED_TEST_NOT_APPROVED`
- `NOT_FOR_MANUFACTURING`
- `FIELD_DEPLOYMENT_NOT_APPROVED`

History:

- v0.8: full rover envelope
- v0.8.1: PTO belt clearance
- v0.8.2: KP000 support plate candidate
- v0.8.3: measurement integration
- v0.8.4: KP000 orientation search
- v0.8.5: robust PTO axial candidate
- v0.9.0: complete powertrain, frame, belt corridor and unit interface contract
- v0.9.1: outboard powertrain pods and inward independent PTO candidate
- v0.9.2: inward PTO shaft-stub, coupling envelope and central work-unit bay correction
- v0.9.2.1: central coupling actual-CAD evidence and independent no-load dry-fit jig correction

`Z_PTO_AXIS >= Z_MOTOR_AXIS` is
`SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO`.

The v0.9.0 conditional replacement is:

`PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS`

if `PTO_ROTATION_ENVELOPE_BOTTOM_Z >= 200` and the belt/frame contracts pass.

The v0.9.1 direction delta is:

- left PTO output `-Y` (inward)
- right PTO output `+Y` (inward)
- left/right shafts, couplings and torque paths remain independent
- a common PTO shaft remains prohibited

These direction values are retained as design history. They are not the
current as-built PTO direction after the 2026-09-05 scoped physical override.

The v0.9.2 coupling delta supersedes the inference that the v0.9.1 geometric
60 mm center gap is usable coupling engagement. Its exposed inward stub was
only 0.5 mm per side. The conditional candidate uses independent 12.5 mm
stubs, shaft ends at Y=+18/-18, a 36 mm end gap and SMALL coupling sensitivity
envelopes. Actual coupling selection, physical fit, shaft cutting, machining,
load and powered rotation remain HOLD.

The v0.9.2.1 evidence correction uses named CadQuery Shapes, actual Boolean
intersection volume, OCP minimum distance and nearest points for the central
coupling region. RETRACTED, PARTIAL, ENGAGED and full 0–10 mm sweep states are
verified. The dry-fit jig now uses two physically independent uncut shaft
references, 12.5 mm stubs and an empty 36 mm center gap. Upstream
frame/belt/clutch/pulley/track geometry remains inherited conditional; this is
not an `ACTUAL_CAD_FULL_SYSTEM_VERIFIED` release.

GITHUB_EXECUTABLE_CAD_RELEASE = HOLD
GITHUB_MANUFACTURING_RELEASE = HOLD
PURCHASE_STATUS = NOT_APPROVED
FIELD_DEPLOYMENT_STATUS = NOT_APPROVED

## Scoped authority boundary

The 2026-09-05 physical authority explicitly replaces v0.9.2.1 only in PTO
output-direction scope. v0.9.2.1 remains the preserved base design lineage and
historical CAD/coupling evidence. The matching outward statement in v0.9.6.38
is supporting interface evidence; v0.9.6.38 as a whole is not promoted.

Exact shaft length, projection, bearing/product, final bearing mount, shaft and
pulley retention, axial spacer, guard production geometry, alignment tolerance,
coupling/tool envelope, torque, powered operation, durability, mud/water test,
manufacturing and field deployment remain HOLD or NOT_APPROVED. See
[`docs/repository/PTO_AUTHORITY_MAP.md`](docs/repository/PTO_AUTHORITY_MAP.md)
for the direction authority and the remaining validation boundaries.
