CREATE TABLE IF NOT EXISTS rover_schema_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS rover_processed_operations (
    operation_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    result_code TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS rover_registry (
    rover_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    registration_state TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    profile_revision INTEGER NOT NULL CHECK(profile_revision >= 1),
    hardware_class TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    profile_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS rover_allowed_fields (
    rover_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    PRIMARY KEY(rover_id, field_id),
    FOREIGN KEY(rover_id) REFERENCES rover_registry(rover_id)
) STRICT;

CREATE TABLE IF NOT EXISTS rover_allowed_units (
    rover_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    PRIMARY KEY(rover_id, unit_id),
    FOREIGN KEY(rover_id) REFERENCES rover_registry(rover_id)
) STRICT;

CREATE TABLE IF NOT EXISTS rover_authorization_decisions (
    authorization_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    rover_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    requested_field_id TEXT NOT NULL,
    requested_unit_id TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    decision TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    context_json TEXT NOT NULL,
    context_sha256 TEXT NOT NULL,
    direct_output_authority INTEGER NOT NULL CHECK(direct_output_authority = 0),
    FOREIGN KEY(operation_id) REFERENCES rover_processed_operations(operation_id),
    FOREIGN KEY(rover_id) REFERENCES rover_registry(rover_id)
) STRICT;
