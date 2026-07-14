# Station Control Development Plan

## Development Principles

| Contract item | Definition |
| --- | --- |
| Objective | Advance one bounded capability while preserving safety authority separation. |
| Implementation scope | Only the capability named by the active phase. |
| Excluded scope | All later-phase behavior and unapproved hardware actuation. |
| Test environment | Start offline and simulated; progress only through explicit gates. |
| Acceptance criteria | Deterministic checks and phase-specific evidence pass. |
| Evidence required | Inputs, outputs, environment, checks, and failures are recorded. |
| Failure impact | Stop phase progression without weakening rover or charging safety. |
| Rollback point | Return to the last accepted phase artifact and safe configuration. |

## Phase ST-001 Foundation Contracts

| Item | Definition |
| --- | --- |
| Objective | Fix requirements, architecture, safety, data, platform, plan, and example configuration contracts. |
| Implementation scope | Seven English documents and one simulation-safe TOML example. |
| Excluded scope | Application code, database, services, networking, packages, and hardware access. |
| Test environment | Static repository checks and isolated patch restoration. |
| Acceptance criteria | Exact structure, safe defaults, format, privacy, and patch checks pass. |
| Evidence required | Diff, hashes, contract reports, and one external evidence archive. |
| Failure impact | No implementation phase may rely on the failed contract set. |
| Rollback point | Remove only the eight untracked ST-001 files. |

## Phase ST-002 Platform Preflight

| Item | Definition |
| --- | --- |
| Objective | Establish a deterministic, read-only platform capability report. |
| Implementation scope | Python environment preflight; OS, CPU, RAM, and disk information; temperature adapter stub; monotonic clock; writable data-directory test; SQLite availability check; deterministic JSON report. |
| Excluded scope | GPIO access, network requirement, database creation, system service, and hardware output. |
| Test environment | Offline Orange Pi prototype and a development Linux host. |
| Acceptance criteria | Repeatable JSON schema and graceful unavailable states with no GPIO access. |
| Evidence required | Sanitized reports, resource observations, and failure-path checks. |
| Failure impact | Platform-dependent implementation remains blocked. |
| Rollback point | ST-001 contracts with no installed preflight service. |

## Phase ST-003 Station Simulator

| Item | Definition |
| --- | --- |
| Objective | Exercise station state transitions without real equipment. |
| Implementation scope | Two dummy fields, two or three dummy rovers, battery-change simulation, last-seen timeout, communication-loss simulation, and STOP/RETURN request simulation. |
| Excluded scope | Real rover communication, motion output, charging output, and sensor hardware. |
| Test environment | Offline simulation on a development host and prototype Linux. |
| Acceptance criteria | Deterministic transitions, timeouts, and request/result logs pass. |
| Evidence required | Scenario inputs, event traces, expected states, and replay results. |
| Failure impact | Storage and device-integration phases cannot use simulator claims. |
| Rollback point | ST-002 preflight with simulator data removed. |

## Phase ST-004 Local Storage

| Item | Definition |
| --- | --- |
| Objective | Persist accepted state and recover after interrupted writes. |
| Implementation scope | SQLite schema, event log, upload outbox, power-loss recovery test, and migration contract. |
| Excluded scope | Cloud upload, real rover input, hardware access, and unbounded retention. |
| Test environment | Temporary databases with simulated interruption and offline operation. |
| Acceptance criteria | Atomic transitions, idempotent outbox records, migration checks, and bounded retention pass. |
| Evidence required | Schema, migration record, recovery trace, and integrity checks. |
| Failure impact | Later stateful features remain blocked to prevent record loss. |
| Rollback point | Last accepted schema and a verified pre-migration backup. |

## Phase ST-005 Field Profiles

| Item | Definition |
| --- | --- |
| Objective | Validate and select private field-profile references safely. |
| Implementation scope | Profile validation, versioning, no-go and danger references, and manual switch gates. |
| Excluded scope | Exact public coordinates, automatic switching, navigation, and Google API use. |
| Test environment | Synthetic profiles with all rovers simulated as stopped or unsafe. |
| Acceptance criteria | Every switch gate is enforced and invalid profiles cannot become active. |
| Evidence required | Validation cases, switch decisions, and operator audit events. |
| Failure impact | Field selection remains fixed at the prior valid profile. |
| Rollback point | Previously active validated profile and profile schema. |

## Phase ST-006 Rover Monitoring

| Item | Definition |
| --- | --- |
| Objective | Record and present qualified rover state without motion authority. |
| Implementation scope | Registry updates, Protocol v0 status interpretation, last-seen logic, battery summary, faults, and communication quality. |
| Excluded scope | ARM, motor or PTO commands, automatic recovery, and cloud passthrough. |
| Test environment | Simulator first, then communication-only ESP32 with motor driver disconnected. |
| Acceptance criteria | Duplicate, replayed, stale, lost, and rebooted sessions are handled safely. |
| Evidence required | Protocol traces, state histories, and communication-loss results. |
| Failure impact | Rover state is marked degraded or unavailable; no output is requested. |
| Rollback point | Simulator-only registry input. |

## Phase ST-007 Water-Level Monitoring

| Item | Definition |
| --- | --- |
| Objective | Record, qualify, present, and alert on water-level observations. |
| Implementation scope | Adapter input, calibration reference, quality, alarms, staleness, and sensor-fault handling. |
| Excluded scope | Water-gate control, pump control, and single-sensor safety authority. |
| Test environment | Simulation followed by a controlled bucket test after approval. |
| Acceptance criteria | Invalid and stale data cannot satisfy mission gates; alarms are auditable. |
| Evidence required | Calibration references, sample traces, alarm cases, and fault cases. |
| Failure impact | Water-level state becomes invalid and dependent planning is blocked. |
| Rollback point | Simulation adapter with control outputs absent. |

## Phase ST-008 Distance Measurement

| Item | Definition |
| --- | --- |
| Objective | Store qualified ranges without misrepresenting them as positions. |
| Implementation scope | Range sources, time, age, quality, estimated accuracy, validity, and position-reference contract. |
| Excluded scope | Automatic navigation, row-level steering, and treating one range as 2D position. |
| Test environment | Simulated geometry and low-risk bench measurement. |
| Acceptance criteria | Single-range ambiguity and invalid-quality rejection are demonstrated. |
| Evidence required | Geometry cases, uncertainty results, and invalid-input decisions. |
| Failure impact | Position remains unavailable and navigation use remains prohibited. |
| Rollback point | Rover monitoring without range-derived position. |

## Phase ST-009 Charging Planning

| Item | Definition |
| --- | --- |
| Objective | Schedule charging needs without energizing charging hardware. |
| Implementation scope | Capacity planning, eligibility gates, evidence states, and simulated enable/disable requests. |
| Excluded scope | Direct contactor control, real battery charging, and Linux final authority. |
| Test environment | Simulation and later a low-current dummy load only after separate approval. |
| Acceptance criteria | Every independent safety condition is required and safe-off dominates. |
| Evidence required | Gate matrices, scheduling cases, request logs, and rejection cases. |
| Failure impact | Charging remains unavailable while rover and station remain safe. |
| Rollback point | Battery monitoring with charging disabled. |

## Phase ST-010 Mission Planning and Offline Sync

| Item | Definition |
| --- | --- |
| Objective | Plan approved missions and synchronize accepted records idempotently. |
| Implementation scope | Mission states and gates, conflicts, operator approval, outbox retry, acknowledgement, and idempotency. |
| Excluded scope | Automatic resume, direct rover motion authority, cloud dependency, and remote field switching. |
| Test environment | Offline-first simulation with disconnect, replay, and duplicate scenarios. |
| Acceptance criteria | Local work survives disconnection and replay causes no double aggregation. |
| Evidence required | Mission traces, gate decisions, outbox state, and receiver acknowledgements. |
| Failure impact | Missions remain paused or blocked and records stay queued locally. |
| Rollback point | Local planning without synchronization enabled. |

## Phase ST-011 Controlled Hardware Validation

| Item | Definition |
| --- | --- |
| Objective | Validate previously accepted contracts through sequential hardware gates. |
| Implementation scope | Communication-only ESP32, disconnected drivers, dummy loads, wheel-lifted motors, dry-ground low-speed work, charging dummy load, controlled real battery, bucket test, and finally field-edge test. |
| Excluded scope | Unattended operation, unrestricted field work, production claims, and skipping any gate. |
| Test environment | Controlled area with physical ESTOP, independent cutoff, observers, and phase-specific approval. |
| Acceptance criteria | Each gate has passing evidence before the next gate; field test is last. |
| Evidence required | Approved test plan, observed results, faults, safe-off proof, and rollback record. |
| Failure impact | Stop immediately, safe-off, record the failure, and do not advance. |
| Rollback point | The preceding passed gate with hardware returned to its safe configuration. |
