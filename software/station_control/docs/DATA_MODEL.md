# Station Control Data Model

## Data-Model Principles

The proposed model is offline-first, append-aware, idempotent, and explicit
about measurement and clock quality. It separates public logical identifiers
from device identity and private field geometry. SQLite tables are future-phase
candidates and are not created in ST-001.

The proposed table set is `fields`, `stations`, `rovers`, `units`, `missions`,
`mission_steps`, `telemetry`, `range_measurements`, `position_estimates`,
`battery_samples`, `charging_sessions`, `water_level_samples`, `events`,
`alerts`, `calibrations`, `upload_outbox`, and `software_versions`.

Privacy classifications used below are `PUBLIC_EXAMPLE`, `INTERNAL`,
`DEVICE_REFERENCE`, and `PRIVATE_LOCATION`. Retention classes are `CONFIG`,
`HISTORY`, `TELEMETRY`, `AUDIT`, and `OUTBOX`.

## Identifiers

Common logical identifiers are `station_id`, `field_id`, `rover_id`, `unit_id`,
`mission_id`, `operation_id`, `event_id`, `sample_id`, `upload_record_id`,
`boot_id`, and `session_id`. They are opaque and stable within their domain.
They must not publish an actual device serial, credential, or private key.

Common event time fields are `occurred_at_utc`, `monotonic_ms`,
`clock_quality`, and `boot_id`. Proposed clock quality values are
`UNSYNCHRONIZED`, `RTC_ONLY`, `NTP_SYNCED`, and `OPERATOR_CONFIRMED`.

## Field

**Proposed table: `fields`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `field_id` | identifier | yes | Stable logical field identity | INTERNAL | CONFIG |
| `display_name` | text | yes | Operator-readable name | INTERNAL | CONFIG |
| `boundary_reference` | reference | yes | Pointer to private boundary data | PRIVATE_LOCATION | CONFIG |
| `station_position_reference` | reference | no | Pointer to private station position | PRIVATE_LOCATION | CONFIG |
| `entrance_reference` | reference | no | Pointer to private entrance data | PRIVATE_LOCATION | CONFIG |
| `water_inlet_reference` | reference | no | Pointer to private inlet data | PRIVATE_LOCATION | CONFIG |
| `water_outlet_reference` | reference | no | Pointer to private outlet data | PRIVATE_LOCATION | CONFIG |
| `work_direction` | text | no | Planned work orientation | INTERNAL | CONFIG |
| `row_spacing` | measurement | no | Spacing with units and validation | INTERNAL | CONFIG |
| `no_go_zones` | reference list | yes | Private prohibited-area references | PRIVATE_LOCATION | CONFIG |
| `danger_zones` | reference list | yes | Private hazard-area references | PRIVATE_LOCATION | CONFIG |
| `profile_version` | text | yes | Immutable profile revision | INTERNAL | HISTORY |
| `active_flag` | boolean | yes | Operator-selected planning profile | INTERNAL | HISTORY |

## Station

**Proposed table: `stations`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `station_id` | identifier | yes | Logical station identity | INTERNAL | CONFIG |
| `display_name` | text | yes | Operator-readable station name | INTERNAL | CONFIG |
| `active_field_id` | identifier | no | Selected validated field | PRIVATE_LOCATION | HISTORY |
| `boot_id` | identifier | yes | Current boot identity | INTERNAL | AUDIT |
| `health_state` | enum | yes | Current station health summary | INTERNAL | HISTORY |
| `software_version_id` | identifier | yes | Installed software reference | INTERNAL | HISTORY |

## Rover

**Proposed table: `rovers`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `rover_id` | identifier | yes | Logical rover identity | INTERNAL | CONFIG |
| `machine_identity_reference` | reference | yes | Non-secret identity lookup | DEVICE_REFERENCE | CONFIG |
| `software_version_id` | identifier | yes | Reported software version | INTERNAL | HISTORY |
| `current_field_id` | identifier | no | Current logical field | PRIVATE_LOCATION | HISTORY |
| `current_unit_id` | identifier | no | Attached unit | INTERNAL | HISTORY |
| `official_state` | enum | yes | Accepted rover state | INTERNAL | HISTORY |
| `last_seen_at_utc` | timestamp | yes | Most recent accepted report | INTERNAL | TELEMETRY |
| `battery_state` | structured value | no | Latest qualified battery summary | INTERNAL | TELEMETRY |
| `active_mission_id` | identifier | no | Current mission reference | INTERNAL | HISTORY |
| `fault_state` | structured value | yes | Current accepted faults | INTERNAL | HISTORY |
| `estimated_position_id` | identifier | no | Qualified estimate reference | PRIVATE_LOCATION | TELEMETRY |
| `measurement_quality` | enum | yes | Quality of current observation | INTERNAL | TELEMETRY |

## Unit

**Proposed table: `units`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `unit_id` | identifier | yes | Logical implement identity | INTERNAL | CONFIG |
| `display_name` | text | yes | Operator-readable name | INTERNAL | CONFIG |
| `unit_type` | enum | yes | Functional unit category | INTERNAL | CONFIG |
| `compatible_rover_types` | list | yes | Permitted rover categories | INTERNAL | CONFIG |
| `assigned_rover_id` | identifier | no | Current rover assignment | INTERNAL | HISTORY |
| `configuration_version` | text | yes | Validated configuration revision | INTERNAL | HISTORY |
| `availability_state` | enum | yes | Planning availability | INTERNAL | HISTORY |
| `fault_state` | structured value | yes | Current unit faults | INTERNAL | HISTORY |

## Mission

**Proposed table: `missions`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `mission_id` | identifier | yes | Stable mission identity | INTERNAL | HISTORY |
| `operation_id` | identifier | yes | Idempotent operator operation | INTERNAL | AUDIT |
| `field_id` | identifier | yes | Validated mission field | PRIVATE_LOCATION | HISTORY |
| `rover_id` | identifier | no | Assigned rover | INTERNAL | HISTORY |
| `unit_id` | identifier | no | Required unit | INTERNAL | HISTORY |
| `state` | enum | yes | Current mission state | INTERNAL | HISTORY |
| `operator_approved` | boolean | yes | Explicit approval result | INTERNAL | AUDIT |
| `battery_reserve_valid` | boolean | yes | Qualified reserve gate | INTERNAL | AUDIT |
| `water_level_gate` | enum | yes | Valid, overridden, or blocked | INTERNAL | AUDIT |
| `updated_at_utc` | timestamp | yes | Last accepted transition time | INTERNAL | HISTORY |

## Mission Step

**Proposed table: `mission_steps`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `mission_id` | identifier | yes | Parent mission | INTERNAL | HISTORY |
| `step_index` | integer | yes | Stable order within mission | INTERNAL | HISTORY |
| `step_type` | enum | yes | Proposed planning action | INTERNAL | HISTORY |
| `area_reference` | reference | no | Pointer to private work area | PRIVATE_LOCATION | HISTORY |
| `parameters` | structured value | yes | Non-secret planning values | INTERNAL | HISTORY |
| `approval_state` | enum | yes | Step approval condition | INTERNAL | AUDIT |

## Telemetry Sample

**Proposed table: `telemetry`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `sample_id` | identifier | yes | Unique sample identity | INTERNAL | TELEMETRY |
| `rover_id` | identifier | yes | Reporting rover | INTERNAL | TELEMETRY |
| `source` | text | yes | Measurement origin | DEVICE_REFERENCE | TELEMETRY |
| `measured_at` | timestamp | yes | Source measurement time | INTERNAL | TELEMETRY |
| `age_ms` | integer | yes | Age at evaluation | INTERNAL | TELEMETRY |
| `quality` | enum | yes | Qualified measurement state | INTERNAL | TELEMETRY |
| `estimated_accuracy` | measurement | no | Accuracy estimate with units | INTERNAL | TELEMETRY |
| `is_valid` | boolean | yes | Policy validation result | INTERNAL | TELEMETRY |
| `payload` | structured value | yes | Bounded telemetry fields | INTERNAL | TELEMETRY |

Measurement quality values are `VALID`, `DEGRADED`, `STALE`, `INVALID`, and
`UNAVAILABLE`.

## Range and Position Measurement

**Proposed table: `range_measurements`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `sample_id` | identifier | yes | Unique range sample | INTERNAL | TELEMETRY |
| `source` | text | yes | Range technology or endpoint | DEVICE_REFERENCE | TELEMETRY |
| `measured_at` | timestamp | yes | Source measurement time | INTERNAL | TELEMETRY |
| `age_ms` | integer | yes | Age at evaluation | INTERNAL | TELEMETRY |
| `range_value` | measurement | yes | Distance with units | INTERNAL | TELEMETRY |
| `quality` | enum | yes | Qualified measurement state | INTERNAL | TELEMETRY |
| `estimated_accuracy` | measurement | yes | Estimated range accuracy | INTERNAL | TELEMETRY |
| `is_valid` | boolean | yes | Policy validation result | INTERNAL | TELEMETRY |

**Proposed table: `position_estimates`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `sample_id` | identifier | yes | Unique position estimate | INTERNAL | TELEMETRY |
| `rover_id` | identifier | yes | Estimated rover | INTERNAL | TELEMETRY |
| `source` | text | yes | Sensor-fusion source | DEVICE_REFERENCE | TELEMETRY |
| `measured_at` | timestamp | yes | Estimate time | INTERNAL | TELEMETRY |
| `age_ms` | integer | yes | Age at evaluation | INTERNAL | TELEMETRY |
| `position_reference` | reference | yes | Private coordinate-store reference | PRIVATE_LOCATION | TELEMETRY |
| `quality` | enum | yes | Qualified estimate state | INTERNAL | TELEMETRY |
| `estimated_accuracy` | measurement | yes | Estimated positional accuracy | INTERNAL | TELEMETRY |
| `is_valid` | boolean | yes | Navigation eligibility result | INTERNAL | TELEMETRY |

A single range is not a 2D position and cannot populate a valid position
estimate without additional independent constraints.

## Battery Sample

**Proposed table: `battery_samples`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `sample_id` | identifier | yes | Unique battery sample | INTERNAL | TELEMETRY |
| `rover_id` | identifier | yes | Observed rover | INTERNAL | TELEMETRY |
| `source` | text | yes | Battery-report origin | DEVICE_REFERENCE | TELEMETRY |
| `measured_at` | timestamp | yes | Source measurement time | INTERNAL | TELEMETRY |
| `age_ms` | integer | yes | Age at evaluation | INTERNAL | TELEMETRY |
| `charge_estimate` | measurement | no | Qualified state-of-charge estimate | INTERNAL | TELEMETRY |
| `quality` | enum | yes | Qualified measurement state | INTERNAL | TELEMETRY |
| `estimated_accuracy` | measurement | no | Estimate uncertainty | INTERNAL | TELEMETRY |
| `is_valid` | boolean | yes | Reserve-policy eligibility | INTERNAL | TELEMETRY |

## Charging Session

**Proposed table: `charging_sessions`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `operation_id` | identifier | yes | Idempotent charge-plan operation | INTERNAL | AUDIT |
| `rover_id` | identifier | yes | Planned rover | INTERNAL | HISTORY |
| `state` | enum | yes | Planning or observed state | INTERNAL | HISTORY |
| `contact_confirmed` | boolean | yes | Independent contact evidence | INTERNAL | AUDIT |
| `polarity_valid` | boolean | yes | Independent polarity evidence | INTERNAL | AUDIT |
| `voltage_valid` | boolean | yes | Independent voltage evidence | INTERNAL | AUDIT |
| `temperature_valid` | boolean | yes | Independent temperature evidence | INTERNAL | AUDIT |
| `power_available` | boolean | yes | Qualified power state | INTERNAL | AUDIT |
| `safety_mcu_ready` | boolean | yes | Independent MCU readiness | INTERNAL | AUDIT |
| `physical_interlock_ready` | boolean | yes | Physical interlock evidence | INTERNAL | AUDIT |

This entity records planning and evidence only. Linux is not direct contactor
authority.

## Water-Level Sample

**Proposed table: `water_level_samples`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `sample_id` | identifier | yes | Unique water-level sample | INTERNAL | TELEMETRY |
| `field_id` | identifier | yes | Associated logical field | PRIVATE_LOCATION | TELEMETRY |
| `source` | text | yes | Sensor origin | DEVICE_REFERENCE | TELEMETRY |
| `measured_at` | timestamp | yes | Source measurement time | INTERNAL | TELEMETRY |
| `age_ms` | integer | yes | Age at evaluation | INTERNAL | TELEMETRY |
| `measurement` | measurement | no | Water-level value with units | INTERNAL | TELEMETRY |
| `quality` | enum | yes | Qualified measurement state | INTERNAL | TELEMETRY |
| `estimated_accuracy` | measurement | no | Estimated sensor accuracy | INTERNAL | TELEMETRY |
| `is_valid` | boolean | yes | Display and warning eligibility | INTERNAL | TELEMETRY |
| `calibration_id` | identifier | yes | Calibration version reference | INTERNAL | HISTORY |
| `alarm_state` | enum | yes | High, low, fault, or normal | INTERNAL | HISTORY |

## Event, Alert, and Upload Outbox

**Proposed table: `events`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `event_id` | identifier | yes | Unique event identity | INTERNAL | AUDIT |
| `operation_id` | identifier | no | Causative operation | INTERNAL | AUDIT |
| `occurred_at_utc` | timestamp | no | UTC time when available | INTERNAL | AUDIT |
| `monotonic_ms` | integer | yes | Ordering within boot | INTERNAL | AUDIT |
| `clock_quality` | enum | yes | Time-source quality | INTERNAL | AUDIT |
| `boot_id` | identifier | yes | Source boot identity | INTERNAL | AUDIT |
| `event_type` | text | yes | Stable event category | INTERNAL | AUDIT |

**Proposed table: `alerts`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `event_id` | identifier | yes | Alert event identity | INTERNAL | AUDIT |
| `severity` | enum | yes | Operator urgency | INTERNAL | AUDIT |
| `state` | enum | yes | Open, acknowledged, or cleared | INTERNAL | AUDIT |
| `source_reference` | reference | yes | Originating state or sample | INTERNAL | AUDIT |
| `operator_action` | text | no | Recorded response | INTERNAL | AUDIT |

**Proposed table: `upload_outbox`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `upload_record_id` | identifier | yes | Unique outbox record | INTERNAL | OUTBOX |
| `payload_hash` | digest | yes | Stable payload integrity value | INTERNAL | OUTBOX |
| `attempt_count` | integer | yes | Number of send attempts | INTERNAL | OUTBOX |
| `next_attempt_at` | timestamp | no | Earliest retry time | INTERNAL | OUTBOX |
| `accepted_acknowledgement` | text | no | Receiver acceptance reference | INTERNAL | OUTBOX |
| `idempotency_key` | identifier | yes | Duplicate aggregation guard | INTERNAL | OUTBOX |
| `payload_reference` | reference | yes | Local record to upload | INTERNAL | OUTBOX |

## Retention and Privacy

**Proposed table: `calibrations`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `calibration_id` | identifier | yes | Immutable calibration version | INTERNAL | HISTORY |
| `source` | text | yes | Sensor or adapter category | DEVICE_REFERENCE | HISTORY |
| `valid_from` | timestamp | yes | Start of applicability | INTERNAL | HISTORY |
| `parameters` | structured value | yes | Non-secret calibration values | INTERNAL | HISTORY |
| `evidence_reference` | reference | yes | Validation evidence pointer | INTERNAL | HISTORY |

**Proposed table: `software_versions`**

| Field name | Logical type | Required | Description | Privacy classification | Retention class |
| --- | --- | --- | --- | --- | --- |
| `software_version_id` | identifier | yes | Version record identity | INTERNAL | HISTORY |
| `component` | text | yes | Station or rover component | INTERNAL | HISTORY |
| `version` | text | yes | Reported release identifier | INTERNAL | HISTORY |
| `observed_at_utc` | timestamp | yes | First accepted observation | INTERNAL | HISTORY |
| `compatibility_state` | enum | yes | Protocol compatibility result | INTERNAL | HISTORY |

Configuration and audit history are retained longer than bounded telemetry.
Acknowledged outbox records may be compacted only after acceptance is durable.
Exact field coordinates, exact field addresses, and actual device secrets must
not be stored in the public repository; only private-store references belong in
the model.
