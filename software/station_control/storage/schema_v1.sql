CREATE TABLE IF NOT EXISTS schema_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS processed_operations (
    operation_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    result_code TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS event_log (
    event_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    FOREIGN KEY(operation_id) REFERENCES processed_operations(operation_id)
) STRICT;

CREATE TABLE IF NOT EXISTS upload_outbox (
    upload_record_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'ACKNOWLEDGED', 'DEAD_LETTER')),
    attempt_count INTEGER NOT NULL CHECK(attempt_count >= 0),
    last_error_code TEXT NOT NULL,
    acknowledgement_id TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES event_log(event_id)
) STRICT;
