# Local Storage

## 1. Status

Phase ST-004 is experimental. It provides simulation and local storage only,
not production certification or approval for unattended operation.

## 2. Purpose

The component provides lightweight offline-first SQLite state for deterministic
event logging, an upload outbox, operation idempotency, and integrity evidence
on Python 3.11 systems such as the Orange Pi Zero 512MB.

## 3. Safety Boundary

This component performs no actual upload, network access, GPIO access, serial
access, rover communication, motor output, charging output, or other hardware
output. Physical ESTOP remains independent. Successful storage does not mean a
rover, field, charging system, cloud service, or unattended operation is ready.

## 4. Database Location

The database must remain outside the repository. Reports must also be outside
the repository. Database, WAL, and SHM files are runtime state and are not
source artifacts or result-ZIP content.

## 5. SQLite Runtime Configuration

Every connection enables foreign keys, selects WAL journal mode, selects
`synchronous FULL`, and sets a 5000 ms busy timeout. Runtime values are checked
before storage work proceeds.

## 6. Schema Version

The only supported schema version is 1 for application phase ST-004. The four
STRICT tables are `schema_metadata`, `processed_operations`, `event_log`, and
`upload_outbox`. Unknown or damaged metadata fails closed; there is no migration,
automatic downgrade, database deletion, or database corruption repair.

## 7. Event Log

Events are stored with their operation identity, logical tick, source, canonical
payload JSON, and payload SHA256. Canonical payload JSON is UTF-8, key-sorted,
compact, duplicate-key-free, and contains no NaN or Infinity.

## 8. Upload Outbox

Outbox records persist only `PENDING`, `ACKNOWLEDGED`, or `DEAD_LETTER` state.
ST-004 never persists `IN_FLIGHT`. Attempts and acknowledgements are offline
session simulations; they make no network call and convey no actual remote
acknowledgement.

## 9. Atomic Session Transactions

All operations in one session execute in input order inside one `BEGIN
IMMEDIATE` transaction. Every operation succeeds before commit. Any state,
identity, idempotency, injected-interruption, or SQLite failure causes full
session rollback with no partial event or outbox commit.

## 10. Idempotency

The operation object canonical JSON SHA256 is stored with its operation ID.
Same-ID same-content replay is a successful no-op. Same-ID different-content
replay is a conflict and rolls back the whole session.

## 11. Power-Interruption Model

A Python test-only injection point can interrupt processing after a selected
operation and before commit. It is not exposed by the CLI. Tests close and
reopen the database, verify complete rollback, and preserve the previously
committed canonical state. This is a simulation, not power-loss certification.

## 12. Integrity Verification

The component runs `PRAGMA integrity_check` after session processing and after
reopen. It expects exactly `ok`. It does not attempt automatic database repair.
The deterministic comparison uses canonical database state SHA256; database
file SHA256 is not used because WAL and platform details can change file bytes.

## 13. CLI Usage

```text
python -I -B software/station_control/station/local_storage.py \
  --repository-root <repository-root> \
  --database <external-data-directory>/station.db \
  --session software/station_control/config_examples/local-storage-session.example.json \
  --json-report <external-report-directory>/local-storage-report.json \
  --text-report <external-report-directory>/local-storage-report.txt
```

The standard output and text report use the same fixed property order. Reports
contain no current time, host name, user name, absolute path, private coordinate,
credential, or environment dump.

## 14. Current Non-Goals

Current non-goals include cloud upload, HTTP, MQTT, sockets, Web UI, systemd,
GPIO, UART, RS-485, CAN, rover commands, PTO control, motor control, charging
control, water-level sensor access, database corruption recovery, field
operation approval, production certification, and unattended operation.
