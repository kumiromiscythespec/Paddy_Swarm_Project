# Protocol v0 Virtual Rover

Status: software-only deterministic harness / real motor output not approved

This package implements RC-SM-001, a pure-Python execution model for the
normative safety states in `safety/STATE_MACHINE.md`. It does not implement a
wire protocol, transport, GPIO, PWM, motor driver, physical emergency stop, or
hardware interface.

## Safety boundary

- The model starts in `BOOT_SAFE` with `armed=false`, drive output zero, and
  PTO output zero.
- Only `DRIVE_ACTIVE` can have a non-zero logical drive output.
- Only `PTO_ACTIVE` can have an effective logical PTO output.
- Drive and PTO are never effective together.
- `DISARMED` and all latched states prohibit output.
- Reconnect does not arm, clear `COMM_LOSS_LATCHED`, or restore an operation.
- Emergency-stop reset enters `DISARMED`; it never restores motion.
- Runtime exceptions and invariant failures produce zero outputs and a
  distinct internal-failure diagnostic.
- `right_output=null` means the right output is unavailable. It is not a
  fabricated physical zero measurement.
- `real_motor_output_enabled` is always `false`.

All output values are simulator values. `left_output` is a signed logical
speed, not PWM, GPIO, voltage, current, or a motor command.

## Official states

The model uses the ten canonical states without adding a protocol state:

`BOOT_SAFE`, `DISARMED`, `ARMED_NEUTRAL`, `DRIVE_READY`, `DRIVE_ACTIVE`,
`PTO_READY`, `PTO_ACTIVE`, `COMM_LOSS_LATCHED`, `FAULT_LATCHED`, and
`EMERGENCY_STOP_LATCHED`.

## Inputs and canonical names

Protocol command names and receiver-local event names follow the existing
documents. RC-SM-001 also needs deterministic runner controls that are not
Protocol v0 commands:

| Runner input | Meaning |
| --- | --- |
| `BOOT` | Non-latched simulator lifecycle reset to `BOOT_SAFE`; requires a new, non-reused `session_id` |
| `DEADMAN_ASSERT` | Simulator-local deadman assertion |
| `WATCHDOG_TIMEOUT` | Inject communication-loss safety processing |
| `TICK` | Advance injected monotonic time without sleeping |

The requested convenience names map to existing canonical events:

| Convenience input | Canonical event |
| --- | --- |
| `CLEAR_EMERGENCY_STOP` | `emergency_stop_reset` |
| `DEADMAN_RELEASE` | `deadman_released` |
| `COMMUNICATION_CONNECTED` | `communication_restored` |
| `COMMUNICATION_LOST` | `communication_lost` |

`CONTROL_UPDATE` and `SESSION_END` are message inputs. They generate or
maintain state-machine behavior but are not added to the official 23-event
state-machine set.

## Deterministic input contract

`RuntimeInput` receives integer `now_ms` from the caller. The model never reads
a wall clock and never sleeps. Protocol message inputs carry a session,
sequence, issued time, and TTL. Operation-starting inputs carry the requested
logical speed. Active-operation updates carry the deterministic operation ID
and deadman value.

The runner-local `BOOT` input must carry a non-empty `session_id` different
from every session ID previously used by that runtime instance. A successful
`BOOT` invalidates the old session, clears its sequence tracking, and accepts
subsequent commands only in the new session. A reused-session or
missing-session `BOOT` is rejected and cannot reset sequence tracking or the
injected monotonic-time epoch. This is a harness input contract, not a new
Protocol v0 command.

Runner-local `BOOT` is not a safety-latch reset event. It is rejected in
`COMM_LOSS_LATCHED`, `FAULT_LATCHED`, and `EMERGENCY_STOP_LATCHED` without
changing the session, used-session history, sequence history, boot-session
readiness, or monotonic-time epoch. Session rollover and safety-latch release
are separate operations. `FAULT_LATCHED` requires `fault_reset`, and
`EMERGENCY_STOP_LATCHED` requires `emergency_stop_reset` with all guards.

Safety latches are independent. `fault_reset` does not release a
communication-loss latch. When `FAULT_LATCHED` and
`communication_loss_latched=true` coexist, `fault_reset` is rejected and both
latches remain fail closed until a separate communication-loss release
contract is defined. This is a harness-local safety policy; it does not add a
new release event to Protocol v0.

On every input, simulated physical emergency stop and fault flags are evaluated
before the software event. Physical emergency stop has highest priority. A
simultaneous fault reason is retained without lowering the displayed emergency
stop state.

The documents leave sequence-gap acceptance unresolved. This harness applies a
local fail-closed policy: after the first sequence, only the next contiguous
sequence is accepted. A forward gap is rejected with the existing
`invalid_payload` reason and diagnostic
`SEQUENCE_GAP_POLICY_FAIL_CLOSED`. This does not modify the formal Protocol v0
contract.

The documents also leave the `COMM_LOSS_LATCHED` release event name unresolved.
The harness therefore does not invent one. `communication_restored` keeps the
latch and all outputs at zero, and runner-local `BOOT` cannot clear it. The
latch remains until a separate release contract is defined.

Persistence across an actual ESP32 power cycle is outside RC-SM-001. NVM
storage, startup recovery, physical-input revalidation, and the hardware/runtime
contract needed to preserve or reconstruct safety latches remain on HOLD. This
software harness does not claim that creating a fresh process models an
approved hardware restart.

PTO deadman details are unresolved in the Protocol documents. The
`drive_pto_split_fixture` harness conservatively requires deadman assertion for
`PTO_START`.

## Step report

Every step exposes the current official state, previous state, canonical or
runner event, acceptance and rejection reason, armed/latch/deadman/communication
flags, selected mode, requested and effective speed, left and right logical
outputs, requested/effective PTO state, safety action, accepted sequence,
last accepted sequence, operation ID, stop reason, diagnostic, and
deterministic step index. The final snapshot also includes the stop reason.

Reports contain no absolute paths, wall-clock timestamps, usernames, hostnames,
or machine names.

## Relationship to the 38 Protocol v0 vectors

The vectors remain immutable validator contracts. This harness does not claim
that executing a runtime transition replaces Phase 1 or Phase 2 validation.

| Classification | Count | Vector IDs |
| --- | ---: | --- |
| Runtime core mapping (not full vector execution) | 26 | `001A`, `001B`, `003`, `004`, `005`, `007`, `011`, `012`, `014L`, `014R`, `015`, `016`, `017`, `018`, `020`, `021`, `022`, `025`, `027`, `028`, `029`, `032`, `033`, `034`, `035`, `036` |
| Validator-only | 11 | `006`, `008`, `009`, `010`, `013`, `019`, `023`, `024`, `026`, `030`, `031` |
| Runtime contract addition required | 1 | `002` |
| Unmapped | 0 | none |

`runtime_core_mapping` means that the harness models one or more runtime
concepts exercised by the vector. It does not mean that every vector field,
Layer 0 gate, validator disposition, output-apply field, or observability field
has been executed and compared, and it is not a vector PASS result. Only the
offline validator owns full Protocol v0 vector acceptance.

The validator-only group depends on Layer 0/validation-pipeline concerns such
as malformed input, boot-ID/controller ownership checks, exact duplicate
result caching, sequence collision identity, or generic payload validation.
`PV0-VAL-002` starts output but its validator fixture has no numeric requested
speed or explicit initial deadman input. Those fields must be supplied by a
future wire/runtime adapter rather than inferred from expected output.

## Running the tests

Use the fixed Protocol v0 environment without installing or updating packages:

```text
python -I software/rover_control/tests/safety/test_runtime_state_machine.py
python -I software/rover_control/tests/integration/test_protocol_state_machine.py
```

Passing these tests does not approve real motors, ESP32 GPIO/PWM, Cytron
MD10C, PTO hardware, physical emergency-stop wiring, wheels-on-ground tests,
water/mud/field tests, unattended operation, or production use.
