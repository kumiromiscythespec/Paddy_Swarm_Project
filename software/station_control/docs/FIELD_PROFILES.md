# Field Profiles

## 1. Status

Experimental, offline-only, simulation and configuration only. This phase has no production certification.

## 2. Purpose

ST-005 stores validated demo field profiles and operator-approved active-field selections.

## 3. Safety Boundary

There is no rover output, GPIO, network, serial, hardware output, water control, or automatic field selection. The physical ESTOP remains independent.

## 4. Separate Database Decision

Profiles use a separate external `field_profiles.db`. ST-004 `station.db` and its schema remain unchanged. Cross-database atomicity is not provided.

## 5. Abstract Field References

Only `local-ref:` and `local-zone-ref:` demo references are accepted. Exact coordinates, GNSS navigation, addresses, and real field locations are prohibited.

## 6. Field Profiles

A bounded catalog stores field ID, display name, enabled state, revision, local frame, references, and no-go zones.

## 7. Required References

Every enabled profile requires enabled ENTRY, WATER_INLET, WATER_OUTLET, and RECOVERY_POINT references.

## 8. No-Go Zones

No-go boundaries contain at least three unique abstract local-zone references and a controlled reason code.

## 9. Profile Revision

Revisions are sequential, operator approved, and atomically replace the validated profile content. Active-field revision additionally requires all rovers stopped, no active mission, and no charging transition.

## 10. Active Field Selection

Selection requires an enabled validated target, operator approval, all rovers stopped, no active mission, and no charging transition. Restart does not select or switch a field automatically.

## 11. Atomic Transactions

One complete session runs in one immediate transaction. Any failure causes full rollback with no partial profile, reference, zone, or active-state change.

## 12. Idempotency

Canonical request SHA-256 binds each operation ID. Identical replay is a no-op; changed content fails closed.

## 13. Integrity Verification

The database is reopened and checked after commit. Logical rows produce a deterministic canonical state SHA-256; the database file hash is not used.

## 14. CLI Usage

Run Python 3.11 with `-I -B`, an external database path, a strict JSON session, and external JSON and text report paths.

## 15. Current Non-Goals

No exact coordinates, GNSS navigation, rover output, GPIO, water control, automatic field selection, cloud integration, field-operation approval, unattended operation, or production certification is included.
