# Station Control Safety Boundaries

## Safety Objective

No Linux failure, network failure, stale record, invalid measurement, or
operator-interface failure may cause rover motion or high-current charging to
move toward a hazardous state. Phase ST-001 is experimental documentation;
hardware test pending.

## Authority Separation

Linux plans, records, aggregates, and presents. Rover Protocol v0 is final rover
output authority. A future independent safety MCU and physical circuit are final
charging authority. The physical ESTOP is independent of Linux and software
services.

## Linux Failure Assumptions

Linux processes are assumed to stop, freeze, restart, lose their clock, exhaust
storage, or fail with the microSD device. Loss of a Linux heartbeat must cause
the future charging safety MCU to safe-off. No Linux recovery path may imply
automatic output enablement.

## Rover Safety Authority

The rover enforces deadman, STOP, EMERGENCY_STOP, communication-loss stop,
zero output on boot, explicit ARM, no automatic restart, session and sequence
freshness, and DRIVE/PTO mutual exclusion. Linux must not directly drive motor
GPIO. A station request cannot override Protocol v0 rejection.

## Charging Safety Authority

Linux must not directly drive a high-current contactor. A future independent
safety MCU and physical path qualify fuse, contact, polarity, current, voltage,
temperature, power, and cutoff conditions. Loss, stale state, or disagreement
causes or retains safe-off.

## Physical Emergency Stop

The physical ESTOP remains independent of Linux, the local interface, network,
and cloud services. Its circuit must be able to remove or inhibit hazardous
energy without waiting for software acknowledgement.

## Mission Approval Boundary

Missions require recorded operator approval and all defined planning gates.
An operator override is always recorded with scope, reason, and resulting
decision. Unattended operation, field operation, water or mud operation, and
PTO operation are not approved by this phase.

## Field Switching Boundary

Field switching requires all rovers stopped, no active mission, no charging
transition, operator confirmation, and a validated target profile. Automatic
field switching is prohibited. Private field geometry is referenced, not stored
as exact coordinates in the public repository.

## Sensor Trust Boundary

Safety-related measurements include source, measured time, age, quality,
estimated accuracy, and validity. Invalid, stale, or unavailable values cannot
authorize action. One water-level sensor must not control a water gate or pump;
initial water-level use is display, recording, and warning only.

## Communication-Loss Behavior

Rovers apply their communication-loss stop independently. The charging safety
MCU safe-offs after heartbeat loss. Cloud commands are never passed directly
through to a rover. A disconnected station continues local records and queues
uploads without weakening safety gates.

## Restart and Recovery

After station reboot, an interrupted mission is `PAUSED` or `FAILED`. Automatic
resume and automatic ARM are prohibited. An operator must review current field,
rover, unit, sensor, battery, fault, communication, and safety-MCU state before
a new request.

## Prohibited Operations

- Direct motor GPIO drive from Linux
- Direct high-current contactor drive from Linux
- Automatic ARM, mission resume, or field switching
- Using invalid sensor values as evidence of safety
- Water-gate or pump control from one water-level sensor
- Direct cloud-to-rover command passthrough
- Unapproved unattended, field, water, mud, PTO, or real charging operation
- Treating one station-to-rover range as a 2D position

## Hardware-Test Gate

The gates are sequential. Failure at a gate stops progression and returns work
to the preceding safe configuration.

1. Simulation
2. Dummy rover
3. ESP32 communication only
4. Motor driver disconnected
5. LED or low-current dummy load
6. Wheel-lifted single motor
7. Wheel-lifted dual motor
8. Dry-ground low-speed test
9. Charging dummy load
10. Controlled real-battery test
11. Water-level bucket test
12. Field-edge test
