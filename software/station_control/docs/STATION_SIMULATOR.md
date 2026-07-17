# Deterministic Offline Station Simulator

Phase ST-003 implements a small Python 3.11 standard-library simulator for the
ST-001 station-control contract and the ST-002 Linux foundation. It is a
simulation-only process. It opens local scenario and report files but does not
use a network, socket, MQTT, GPIO, UART, serial, RS-485, CAN, database,
subprocess, web server, motor output, rover output, or charging output.

## Run

Create an external report directory, then run from the repository root:

```text
python3 -I -B software/station_control/station/simulator.py \
  --repository-root <repository> \
  --scenario software/station_control/config_examples/simulator-scenario.example.json \
  --json-report <external>/station-simulator-report.json \
  --text-report <external>/station-simulator-report.txt
```

Both report paths must be outside the repository. Reports use integer ticks and
contain no timestamp, current time, host name, user name, absolute path,
address, credential, exact field coordinate, or random value. Repeating the
same scenario produces byte-identical JSON and text.

## Scenario contract

Scenario version 1 contains exactly the abstract fields `FIELD-DEMO-001` and
`FIELD-DEMO-002`, and exactly the logical rovers `ROVER-DEMO-001`,
`ROVER-DEMO-002`, and `ROVER-DEMO-003`. Boundaries are abstract
`local-reference:` values rather than coordinates. Rovers expose only logical
field and unit identifiers, official state, integer battery percentage,
last-seen tick, fault text, active mission reference, and communication state.

Events are evaluated in nondecreasing tick order and then input order. The
event set is `BATTERY_SET`, `BATTERY_DECREASE`, `ROVER_SEEN`,
`COMMUNICATION_LOST`, `COMMUNICATION_RESTORED`, `FAULT_SET`, `FAULT_CLEAR`,
`STOP_REQUEST`, `RETURN_REQUEST`, `MISSION_CREATE`, `MISSION_APPROVE`,
`MISSION_ASSIGN`, `MISSION_START`, `MISSION_PAUSE`, `MISSION_CANCEL`,
`CHARGE_START`, `CHARGE_COMPLETE`, `FIELD_SWITCH_REQUEST`, and
`STATION_RESTART`.

## Mission and safety behavior

The exact mission-state set is `DRAFT`, `WAITING_APPROVAL`, `QUEUED`,
`ASSIGNED`, `RUNNING`, `PAUSED`, `RETURNING`, `CHARGING`, `COMPLETED`,
`FAILED`, `CANCELLED`, and `EXPIRED`.

A mission start requires explicit operator approval, an assigned rover, a
matching unit, the active field on both mission and rover, available
communication, no fault, and battery at or above the 20 percent reserve.
Communication loss or a last-seen difference greater than five ticks pauses a
running mission. Communication restoration and station restart never resume or
ARM a mission automatically. Zero battery retains a safe stopped rover and
pauses an active mission.

Field switching requires explicit operator confirmation, every rover stopped,
no active mission, and no charging transition. STOP and RETURN are recorded as
state requests with `direct_output_authority=false`; they are not motor
commands. Charge events alter simulation state only and never control charging
hardware. Linux remains without rover output authority, while physical ESTOP
authority remains independent.

## Validation

The scenario and report schemas use JSON Schema Draft 2020-12, local `$defs`,
explicit required properties, and `additionalProperties=false`. The simulator
does not import the optional `jsonschema` validator. Its own parser rejects
unknown properties, invalid types, invalid identifiers, unknown targets,
duplicate fixed identities, out-of-range integer values, and descending event
ticks before processing begins.
