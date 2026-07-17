# Rover Registry

## 1. Status

Experimental and offline only. This phase is simulation and policy evaluation only and has no production certification.

## 2. Purpose

ST-006 registers demo rovers, stores bounded field and unit permissions, manages registration state, and records deterministic assignment authorization decisions.

## 3. Safety Boundary

There is no rover communication, actual assignment, ARM, motor output, charging output, field navigation, GPIO, serial access, or direct output authority. The physical ESTOP remains independent.

## 4. Separate Database Decision

The registry uses a separate external `rover_registry.db`. It does not modify ST-004 or ST-005 databases and provides no cross-database transaction.

## 5. Rover Identity Scope

Only bounded demo IDs are accepted. There is no password storage, secret key storage, MAC or IP storage, actual rover serial, certificate material, or cryptographic authentication.

## 6. Registration States

PENDING, REGISTERED, SUSPENDED, and terminal REVOKED states use explicit operator-approved transitions. Automatic registration and automatic state transition are prohibited.

## 7. Field Permissions

Each rover has a bounded set of demo field permissions. Permission strings do not connect to another database.

## 8. Unit Permissions

Each rover has a bounded set of demo unit permissions. Permission records grant policy eligibility only.

## 9. Profile Revisions

Sequential revisions require operator approval, a confirmed stopped rover, no active mission, and no charging transition. A full session rollback prevents partial permission updates.

## 10. Assignment Authorization

Authorization evaluates a supplied demo safety context. It requires a registered enabled rover, allowed field and unit, matching active field, operator approval, QUEUED mission, stopped rover, communication availability, no fault, battery reserve minimum 20, and an unasserted physical ESTOP.

## 11. Authorization Denial Reasons

All applicable denial reasons are recorded in fixed contract order. AUTHORIZED still performs no assignment, ARM, output, communication, or navigation.

## 12. Atomic Transactions

One session uses one immediate SQLite transaction. Any operation failure causes full session rollback.

## 13. Idempotency

Canonical request SHA256 binds each operation ID. Identical replay is a no-op; changed content fails closed.

## 14. Integrity Verification

The database is reopened and checked after processing. Logical rows produce a deterministic canonical state SHA256 instead of a database file hash.

## 15. Orange Pi Validation

Windows and Orange Pi cross-platform validation compares source hashes, unittest results, deterministic reports, canonical state, and SQLite integrity without sudo or hardware access.

## 16. CLI Usage

Run Python 3.11 with `-I -B`, an external database, a strict JSON session, and external JSON and text reports.

## 17. Current Non-Goals

No production certification, field-operation approval, unattended-operation approval, secret storage, cryptographic authentication, actual assignment, actual ARM, rover output, or hardware control is included.
