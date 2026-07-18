CREATE TABLE IF NOT EXISTS unit_schema_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS unit_processed_operations (
    operation_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    result_code TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS unit_registry (
    unit_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    unit_type TEXT NOT NULL,
    registration_state TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    profile_revision INTEGER NOT NULL CHECK(profile_revision >= 1),
    pto_contract TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    profile_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS unit_allowed_hardware_classes (
    unit_id TEXT NOT NULL,
    hardware_class TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    PRIMARY KEY(unit_id, hardware_class),
    FOREIGN KEY(unit_id) REFERENCES unit_registry(unit_id)
) STRICT;

CREATE TABLE IF NOT EXISTS unit_allowed_fields (
    unit_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    PRIMARY KEY(unit_id, field_id),
    FOREIGN KEY(unit_id) REFERENCES unit_registry(unit_id)
) STRICT;

CREATE TABLE IF NOT EXISTS unit_mount_state (
    unit_id TEXT PRIMARY KEY,
    mount_state TEXT NOT NULL,
    mounted_rover_id TEXT NOT NULL,
    mount_revision INTEGER NOT NULL CHECK(mount_revision >= 0),
    last_operation_id TEXT NOT NULL,
    FOREIGN KEY(unit_id) REFERENCES unit_registry(unit_id)
) STRICT;

CREATE TABLE IF NOT EXISTS unit_compatibility_decisions (
    compatibility_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    rover_id TEXT NOT NULL,
    requested_field_id TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    decision TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    context_json TEXT NOT NULL,
    context_sha256 TEXT NOT NULL,
    direct_output_authority INTEGER NOT NULL CHECK(direct_output_authority = 0),
    FOREIGN KEY(operation_id) REFERENCES unit_processed_operations(operation_id),
    FOREIGN KEY(unit_id) REFERENCES unit_registry(unit_id)
) STRICT;
