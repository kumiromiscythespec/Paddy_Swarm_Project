# Station Control Architecture

## Architecture Goals

The architecture favors offline-first operation, bounded resource use,
auditable state transitions, replaceable hardware adapters, and fail-safe
authority separation. Phase ST-001 defines a proposed structure only.

## System Context

```text
                         optional later synchronization
                                      |
                                      v
+---------------- Linux station control ----------------+
| Local Web UI <-> Station API                           |
|                    |                                   |
| Field Manager --- Rover Registry --- Unit Registry     |
|        |             |                 |               |
| Mission Planner --- Charging Scheduler                 |
|        |             |                                 |
| Water-Level Manager  Alert Manager --- Sync Manager    |
|        |             |                 |               |
| SQLite repository   Event log       Upload outbox      |
|        |                                               |
| Rover protocol gateway                                |
| Station safety-MCU adapter                            |
| Platform hardware adapter                             |
+--------|----------------|----------------|-------------+
         |                |                |
         v                v                v
  Rover Protocol v0   independent      platform health /
  safety authority    safety MCU       low-risk sensors
         |                |
         v                v
  rover outputs       physical charging safety circuit
```

The SQLite repository, API, and web UI are future-phase components and are not
implemented in ST-001.

## Trust Boundaries

The Linux station is trusted to plan and retain records, but not to guarantee
motor or high-current safety. Each rover retains output authority through
Protocol v0. A future safety MCU and physical circuitry retain charging
authority. External synchronization is untrusted as a direct command source,
and private field geometry remains outside the public repository.

## Linux Station Responsibilities

Linux manages proposed field and unit records, rover observations, mission
planning, charge scheduling, water-level presentation, alerts, the event log,
and the upload outbox. It issues only requests across safety boundaries and
records acknowledgements and results. It is not the final motor or charging
authority.

## Rover Responsibilities

The rover enforces deadman, STOP, EMERGENCY_STOP, communication-loss stop,
zero output at boot, explicit ARM, no automatic restart, session and sequence
freshness, and DRIVE/PTO mutual exclusion. Protocol v0 remains authoritative
even when a station request is accepted for consideration.

## Independent Safety MCU Responsibilities

A future station safety MCU is responsible for safe-off behavior when the Linux
heartbeat is lost and for qualifying contact, polarity, voltage, current,
temperature, and interlock conditions. Physical fuse and cutoff paths remain
independent. The MCU does not exist as an ST-001 implementation.

## Hardware Adapter Boundary

Candidate platform-neutral interfaces are `read_station_health`,
`read_water_level`, `read_power_status`, `request_charge_enable`,
`request_charge_disable`, and `read_safety_mcu_state`. They are proposed names,
not implemented functions. Future Orange Pi and Raspberry Pi adapters must hide
GPIO and board-specific details behind this boundary.

## Application Components

The proposed components are Local Web UI, Station API, Field Manager, Rover
Registry, Unit Registry, Mission Planner, Charging Scheduler, Water-Level
Manager, Alert Manager, Sync Manager, SQLite repository, Event log, Upload
outbox, Rover protocol gateway, Station safety-MCU adapter, and Platform
hardware adapter.

The initial process model permits one to three lightweight processes. There is
no container requirement, no desktop GUI, and no browser process on the Orange
Pi. Systemd integration is a future phase.

## Communication Model

Local networking is preferred. MQTT is a future candidate, not a current
dependency. Protocol v0 remains the rover safety contract. A station command is
a request, not unconditional motor authority. Command acknowledgement and
result logging are required, with explicit replay, duplicate, and stale-message
handling. Offline operation must not depend on cloud access.

## Storage Model

A future SQLite repository stores structured state, while an event log records
auditable transitions and an upload outbox tracks unaccepted synchronization
records. Writes, queues, batches, and retention are bounded. Each record carries
stable identifiers and clock-quality information suitable for recovery.

## Offline Synchronization

The station commits local state before scheduling an upload. Retry selects only
unaccepted records. Payload hashes and idempotency keys let the receiver accept
replays without double aggregation. Remote state cannot automatically ARM a
rover, resume a mission, switch a field, or energize charging equipment.

## Failure Modes

Linux process exit, freeze, reboot, storage exhaustion, damaged microSD, clock
loss, network loss, stale rover state, invalid measurements, and unavailable
safety-MCU state are assumed. Safety outputs remain or move safe. Recovered
missions remain paused or failed, invalid data is visibly degraded, and no
automatic resume occurs.

## Migration to Raspberry Pi

Application contracts use Linux, UTF-8, monotonic time, local files, and
platform-neutral adapters. A future Raspberry Pi port replaces only platform
adapters and packaging appropriate to Raspberry Pi OS Lite or Compute Module
hardware. Portability acceptance requires unchanged domain and safety contracts
with board-specific GPIO confined to an adapter implementation.
