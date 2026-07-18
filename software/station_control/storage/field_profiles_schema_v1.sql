CREATE TABLE IF NOT EXISTS field_schema_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS field_processed_operations (
    operation_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    logical_tick INTEGER NOT NULL CHECK(logical_tick >= 0),
    result_code TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS field_profiles (
    field_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    profile_revision INTEGER NOT NULL CHECK(profile_revision >= 1),
    local_frame_id TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    profile_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS field_references (
    reference_id TEXT PRIMARY KEY,
    field_id TEXT NOT NULL,
    reference_type TEXT NOT NULL,
    label TEXT NOT NULL,
    location_reference TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    FOREIGN KEY(field_id) REFERENCES field_profiles(field_id)
) STRICT;

CREATE TABLE IF NOT EXISTS field_no_go_zones (
    zone_id TEXT PRIMARY KEY,
    field_id TEXT NOT NULL,
    label TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    boundary_json TEXT NOT NULL,
    boundary_sha256 TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    FOREIGN KEY(field_id) REFERENCES field_profiles(field_id)
) STRICT;

CREATE TABLE IF NOT EXISTS field_active_state (
    state_key TEXT PRIMARY KEY CHECK(state_key = 'ACTIVE_FIELD'),
    active_field_id TEXT NOT NULL,
    selection_revision INTEGER NOT NULL CHECK(selection_revision >= 1),
    last_operation_id TEXT NOT NULL
) STRICT;
