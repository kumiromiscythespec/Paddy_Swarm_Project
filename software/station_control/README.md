# Paddy Swarm Station Control

## Project Status

This directory is an **Experimental** and **Software foundation only** contract
for Phase ST-001. The phase creates documentation and an example configuration
only. It does not provide field deployment approval or unattended operation
approval.

## Purpose

Station control is planned to preserve, present, and coordinate field, rover,
unit, mission, battery, water-level, event, and alert information. Its initial
purpose is reliable operator support, not autonomous vehicle intelligence.

## Prototype Platform

The prototype target is an Orange Pi Zero 512MB running headless,
Debian-family Linux. The design assumes constrained memory, microSD write
endurance, local-network availability that may be intermittent, and no desktop
GUI.

## Future Production Platform

Future Raspberry Pi portability is required. Raspberry Pi OS Lite and
Raspberry Pi Compute Module platforms are candidates. Platform-specific access
must remain behind hardware adapter boundaries.

## Responsibilities

The Linux station is responsible for planning, recording, aggregation, and
operator presentation. Planned responsibilities include field profiles, rover
and unit registries, mission planning, local event history, alerts, and an
offline upload outbox.

## Safety Boundary

Linux is not the final authority for motor output or high-current charging.
Rover-side Protocol v0 remains the authoritative rover safety contract,
including deadman, STOP, EMERGENCY_STOP, explicit ARM, output freshness, and
communication-loss behavior. A future independent safety MCU and physical
circuitry must control charging safety. The Physical ESTOP remains independent
of Linux.

Hardware actuation is not implemented. Charging output is not implemented.
Water-level sensor access is not implemented. Rover motion command transmission
is not implemented.

## Offline-First Operation

Offline-first is the normal operating model. Field selection, local planning,
state recording, and outbox accumulation must remain available without cloud
access. When connectivity returns, only unaccepted records are retried, using
stable record identifiers and idempotency keys to prevent duplicate counting.

## Initial MVP

The initial MVP is planned as a device that does not lose state and supports
safe recording, presentation, and planning. It is not a device that
automatically drives rovers, switches fields, energizes chargers, or controls
water infrastructure.

## Repository Layout

The Phase ST-001 layout is:

```text
software/station_control/
|-- README.md
|-- config_examples/
|   `-- station.example.toml
`-- docs/
    |-- ARCHITECTURE.md
    |-- DATA_MODEL.md
    |-- DEVELOPMENT_PLAN.md
    |-- PLATFORM_SUPPORT.md
    |-- REQUIREMENTS.md
    `-- SAFETY_BOUNDARIES.md
```

## Development Phases

ST-001 fixes foundation contracts. Later phases are planned for platform
preflight, simulation, local storage, profiles, monitoring, measurement,
charging planning, mission planning, offline synchronization, and controlled
hardware validation. Each later phase requires its own evidence and gate.

## Current Non-Goals

- Real rover communication, motor control, and PTO control
- Charging contactor control or other high-current output
- Water-level sensor access, water-gate control, or pump control
- Cloud-dependent operation, Google API use, or exact field coordinates
- A desktop GUI, resident browser, camera AI, image recognition, or local LLM
- A map tile server, PostgreSQL, or a multi-container Docker stack
- Field deployment or unattended operation

## Hardware Test Status

Hardware test pending. No station hardware actuation, real charging output,
water or mud operation, PTO operation, or field operation has been approved or
validated by Phase ST-001.
