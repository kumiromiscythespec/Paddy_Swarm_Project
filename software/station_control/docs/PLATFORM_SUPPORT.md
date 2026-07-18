# Station Control Platform Support

## Platform Strategy

The station application is planned as a small, headless, platform-neutral Linux
service set. Domain and safety contracts remain independent of board-specific
GPIO. Phase ST-001 defines targets and does not guarantee performance.

## Prototype Platform

The prototype target is Orange Pi Zero 512MB with headless Debian-family Linux,
CLI or SSH operation, microSD storage, limited RAM, and limited write endurance.
There is no desktop GUI and no heavy container stack requirement.

## Production Direction

Future candidates are Raspberry Pi OS Lite and Raspberry Pi Compute Module,
with eMMC preferred for production storage. The planned Python application is
platform-neutral; any board-specific GPIO layer belongs in an adapter.

## Operating-System Contract

The proposed OS contract is Linux, a Python 3.11-compatible runtime, UTF-8,
monotonic clock support, and local-network operation without cloud dependency.
Systemd and SQLite are available to later phases but are not integrated or
created in ST-001.

## Resource Constraints

The initial design targets are:

- Station application idle RAM below 128MB
- No individual process expected above 96MB under normal MVP load
- One to three lightweight processes
- No image processing and no resident browser process
- A bounded in-memory telemetry queue
- A bounded upload-outbox batch size

These are initial design targets, not performance guarantees in Phase ST-001.

## Storage Constraints

MicroSD has limited endurance. The planned design uses bounded log retention,
bounded telemetry history, batched durable writes, recoverable transactions,
and explicit storage-pressure alerts. Database schema and power-loss recovery
testing belong to later phases.

## Hardware Abstraction

Platform hardware access is isolated behind an adapter boundary. Domain logic
consumes qualified station health, water-level, power, and safety-MCU states
without importing board GPIO details. Orange Pi and Raspberry Pi adapters must
conform to the same domain contract.

## Supported Interfaces

Initial contract-level interfaces are local files, monotonic time, UTF-8 data,
CLI or SSH administration, and future local networking. Proposed rover protocol,
safety-MCU, and hardware adapter interfaces are documented but not implemented.

## Unsupported Initial Features

- Desktop GUI or browser process on the station
- Camera AI, image recognition, map tile server, or local LLM
- PostgreSQL or a multi-container Docker deployment
- Cloud-required operation or Google API dependency
- Real rover communication, GPIO, motor, charging, or water-gate control
- Automatic mission resume, ARM, or field switching

There is no Docker requirement for the initial station.

## Portability Acceptance Criteria

A future Raspberry Pi migration passes only when domain records, offline-first
behavior, Protocol v0 boundaries, independent charging authority, configuration
semantics, and failure behavior remain unchanged. Board-specific code must be
confined to adapters, and resource use must be measured against the target
platform before any deployment claim.
