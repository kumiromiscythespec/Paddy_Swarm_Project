# Station Control Requirements

## Purpose and Scope

These requirements define the planned station-control foundation for an Orange
Pi Zero 512MB prototype and future portable Linux targets. Phase ST-001 covers
contracts only; implementation, hardware access, and field deployment are
excluded. The normal operating model is offline-first.

## Actors

- The operator selects a validated field, approves missions, reviews alerts,
  and records overrides.
- The Linux station plans, records, aggregates, and presents information.
- A rover reports state and retains final Protocol v0 motion safety authority.
- A future independent safety MCU retains final charging safety authority.
- A future synchronization service accepts idempotent outbox records but is not
  required for local operation.

## Field Profiles

A field profile contains the following logical properties. References identify
private operational data held outside the public repository, not exact
coordinates committed here.

| Property | Requirement |
| --- | --- |
| `field_id` | Stable non-secret logical identifier |
| `display_name` | Operator-readable label |
| `boundary_reference` | Reference to the private boundary data |
| `station_position_reference` | Reference to the private station position |
| `entrance_reference` | Reference to the private entrance description |
| `water_inlet_reference` | Reference to private inlet information |
| `water_outlet_reference` | Reference to private outlet information |
| `work_direction` | Planned traversal orientation |
| `row_spacing` | Profile value with units and validation status |
| `no_go_zones` | References to prohibited operational areas |
| `danger_zones` | References to operator-defined hazard areas |
| `profile_version` | Immutable profile revision |
| `active_flag` | Whether the profile is selected for planning |

Field switching is allowed only when all rovers are stopped, no mission is
active, no charging transition is in progress, an operator has confirmed the
change, and the target field profile has passed validation. Automatic field
switching is prohibited.

## Rover Registry

Each rover record includes `rover_id`, machine identity reference, software
version, current field, current unit, official state, last seen time, battery
state, active mission, fault state, estimated position, and measurement
quality. Authentication by MAC address alone is prohibited. Machine identity
references must not expose device credentials.

## Unit Registry

Each unit record includes a `unit_id`, display name, unit type, compatible rover
types, current rover assignment, current field, configuration revision,
availability state, inspection state, and fault state. Mission assignment
requires the selected rover and unit to be compatible and consistently linked.

## Mission Planning

The twelve mission states are:

1. `DRAFT`
2. `WAITING_APPROVAL`
3. `QUEUED`
4. `ASSIGNED`
5. `RUNNING`
6. `PAUSED`
7. `RETURNING`
8. `CHARGING`
9. `COMPLETED`
10. `FAILED`
11. `CANCELLED`
12. `EXPIRED`

A mission may start only when its field matches the active field, an operator
has approved it, the assigned unit matches, battery reserve and communication
quality meet policy, no rover fault is active, water level is valid or a
recorded operator override exists, no mission area conflicts, and station
capacity is available. Automatic mission restart after station reboot or
communication recovery is prohibited. A recovered mission remains `PAUSED` or
becomes `FAILED` until an operator makes a new decision.

## Battery Monitoring

Battery records include source, measured time, age, quality, estimated
accuracy, validity, charge estimate, voltage when available, temperature when
available, and reserve-policy result. Stale, invalid, or unavailable values
must not authorize a mission or charging transition.

## Charging Planning

Charging is planning only in this phase. Direct energization by Linux is
prohibited. A future charge transition requires all of: contact confirmed,
polarity valid, voltage valid, temperature valid, power available, independent
safety MCU ready, and physical interlock ready. Linux may request a transition
in a future phase but cannot be the final high-current authority.

## Water-Level Monitoring

A water-level record includes measurement, source, measured time, age, quality,
estimated accuracy, validity, calibration version, high alarm, low alarm, and
sensor fault. A redundant threshold sensor is a future candidate. Initial use
is limited to display, recording, and warning. Automatic water-gate and pump
control are non-goals, and one sensor must never be the sole authority for such
control.

## Distance and Position Estimation

A single range is not a 2D position. Future candidates include odometry, IMU,
UWB, and RTK sources. Every range or position estimate includes source,
`measured_at`, age, quality, estimated accuracy, and `is_valid`. Invalid quality
must not be used for automatic navigation. Approximate imagery-derived profiles
must not justify row-level steering or safety stopping.

## Local Data Logging

The planned local log records boot, operation, event, alert, mission transition,
measurement, acknowledgement, override, and failure information. Records use
UTC where available, a monotonic value for ordering within a boot, and explicit
clock quality. Storage and retention must be bounded for microSD operation.

## Offline Synchronization

Local operation must not depend on a cloud connection. The planned upload
outbox retains only pending or unaccepted records for retry. Each upload has a
unique record ID, payload hash, attempt state, accepted acknowledgement, and
idempotency key so a replay cannot cause double aggregation.

## Operator Interface

The planned local interface presents active field, rover and unit state,
mission state, battery reserve, water-level quality, station health, pending
alerts, and synchronization backlog. Safety-affecting approval and override
actions require explicit confirmation and an auditable event record.

## Station Self-Monitoring

The station records process health, boot ID, clock quality, storage capacity,
memory pressure, temperature when an adapter is available, local data write
status, safety-MCU state when available, and last successful rover contact.
Missing or invalid health inputs produce a visible degraded state.

## Acceptance Criteria

- The documented field-switch gates and all twelve mission states are present.
- Offline-first planning and logging do not depend on cloud access.
- Rover Protocol v0 and the future charging safety MCU retain final authority.
- Charging is planning only and direct high-current control is absent.
- Water-level data is quality-qualified and does not control infrastructure.
- A single range is explicitly rejected as a 2D position.
- Exact field coordinates and device credentials are excluded from the public
  repository.
- Phase ST-001 creates no implementation or hardware interface code.
