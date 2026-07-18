# Unit Registry

## 1. Status

ST-007 is experimental, offline only, and limited to simulation and policy evaluation only. It has no production certification.

## 2. Purpose

The component records two demo units, their permissions, operator-declared mount state, and deterministic compatibility decisions.

## 3. Safety Boundary

There is no physical mount, physical unmount, attachment sensor, PTO output, motor output, rover communication, ARM, or actual assignment. The physical ESTOP remains independent.

## 4. Separate Database Decision

ST-007 uses a separate external `unit_registry.db`. It does not open or join station, field-profile, or rover-registry databases.

## 5. Unit Identity Scope

The only positive-session identities are `UNIT-DEMO-SCOUT` and `UNIT-DEMO-WEED`. `UNIT-DEMO-WEED` represents the PS-WEED-V001.2 PASSIVE RAKE. There is no actual device serial, MAC or IP storage, or password or secret storage.

## 6. Unit Types

The policy types are `SCOUT_SENSOR`, `PASSIVE_RAKE`, `CARRIER`, and `TEST_ONLY`.

## 7. Registration States

States are `PENDING`, `REGISTERED`, `SUSPENDED`, and terminal `RETIRED`. There is no automatic registration or automatic state transition.

## 8. PTO Contracts

Contracts are `NONE`, `DEPLOY_ASSIST_ONLY`, and `CONTINUOUS`. They are policy metadata and never grant output authority.

## 9. Hardware Compatibility

Enabled hardware-class permissions are evaluated from local records only. A compatible result does not control hardware.

## 10. Field Permissions

Requested and active demo field identifiers must satisfy the stored enabled field policy.

## 11. Mount State

`MOUNTED` and `UNMOUNTED` are operator-declared simulation states. They do not confirm physical conditions.

## 12. Mount Safety Conditions

Operator approval required, rover stopped required, motor output disabled required, PTO output disabled required, no active mission, and no charging transition. Main power isolation is operator-declared simulation input. Mechanical lock confirmation is operator-declared simulation input.

## 13. Compatibility Decisions

`COMPATIBLE` and `INCOMPATIBLE` are deterministic policy decisions with ordered reasons and direct output authority always false.

## 14. Profile Revisions

An approved revision increments by one while the unit is unmounted, PTO output is disabled, and main power is isolated. Permissions are replaced atomically.

## 15. Atomic Transactions

One input session is one immediate transaction. Any operation failure causes full session rollback without partial unit, permission, mount, or decision changes.

## 16. Idempotency

The canonical operation SHA-256 makes an identical operation a duplicate no-op and rejects changed content under the same operation ID.

## 17. Integrity Verification

The database is reopened, its schema is verified, and SQLite integrity is checked. Canonical state SHA256 compares logical state rather than database bytes.

## 18. Orange Pi Validation

Windows and Orange Pi cross-platform validation compares deterministic JSON, text, and canonical state output using Python 3.11 and SQLite.

## 19. CLI Usage

Run `python3 -I -B software/station_control/station/unit_registry.py --repository-root <repository> --database <external>/unit_registry.db --session <session.json> --json-report <external>/report.json --text-report <external>/report.txt`.

## 20. Current Non-Goals

Physical operation, attachment sensing, mission start, network access, automatic state changes, unattended operation, and field-operation approval remain out of scope.
