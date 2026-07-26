# Protocol v0 Runtime Adapter (RC-WA-001)

Status: software-only / simulator-first / real motor output prohibited

## Scope

This package converts an already normalized Protocol v0 logical message into the
existing RC-SM-001 `RuntimeInput`, then optionally dispatches that input through
an in-process deterministic virtual receiver bridge.

The Python property names in this package are internal test/runtime boundary
names. They are not approved wire keys. RC-WA-001 does not define or implement
wire encoding, byte layout, framing, a production JSON parser or schema,
WebSocket, HTTP, TCP/UDP, ESP-NOW, Bluetooth, authentication, ID generation,
PWA communication, or ESP32 communication.

## Responsibility boundary

The adapter validates:

- logical message type and direction;
- protocol version and sender role;
- for runtime-producing messages only, current rover boot ID, active session,
  controller ownership, and active owner ID;
- non-empty sender and message identity;
- exact-integer, non-boolean sequence structure and configured safe range;
- non-negative exact-integer freshness reference;
- positive exact-integer TTL and the configured TTL ceiling;
- message/payload model agreement and command-specific field presence;
- exact numeric speed boundaries without conversion, inference, defaulting,
  rounding, absolute-value conversion, or clamping;
- capabilities that are structurally unavailable in the selected runtime
  profile.

The existing runtime state machine remains authoritative for duplicate, stale,
sequence gap, expiry, operation ID match, current-state checks, safety guards,
accepted-sequence updates, and output-apply results. The adapter has no
sequence namespace or acceptance cache. `freshness_reference_ms` maps to
`issued_at_ms`, receiver monotonic time maps to `now_ms`, and `ttl_ms` passes
through unchanged. No wall clock is read.

Adapter `RUNTIME_INPUT_READY` means only that a structurally valid
`RuntimeInput` was produced. It does not mean runtime acceptance, output
application, state confirmation, or transport acknowledgement.

## Normalized logical model

`NormalizedLogicalMessage` carries the internal envelope:

- `protocol_version`, `logical_message_type`, and `direction`;
- `rover_boot_id`, `session_id`, `sender_id`, and `sender_role`;
- `controller_ownership`, `message_id`, and `sequence`;
- `freshness_reference_ms`, `ttl_ms`, and a typed payload.

`COMMAND` uses `CommandPayload`, `CONTROL_UPDATE` uses
`ControlUpdatePayload`, and Controller-to-Rover `SESSION_END` permits either no
payload or the explicitly empty `SessionEndPayload`. `OpaquePayload` recursively
freezes mapping and collection fixtures for all `NO_RUNTIME_ACTION` message
types. Its content is neither interpreted nor copied into adapter/runtime
reports, and it defines no Protocol or wire payload schema.

## Command payload contract

| Command | Required semantic field | Forbidden semantic fields |
| --- | --- | --- |
| `MOVE_FORWARD`, `MOVE_REVERSE` | `requested_speed` | `speed_limit`, `safety_confirmation` |
| `SET_SPEED_LIMIT` | `speed_limit` | `requested_speed`, `safety_confirmation` |
| `fault_reset`, `emergency_stop_reset` | exact boolean `safety_confirmation` | `requested_speed`, `speed_limit` |
| Other 11 commands | none | all three optional semantic fields |

All 16 command names map one-to-one to their existing RC-SM-001 `Event`.
MOVE speed and speed limit must be exact integers in `1..max_speed`; `bool`,
string, float, zero, negative, and over-limit values are rejected.
TURN and PTO commands are rejected at the adapter boundary when the receiver
profile explicitly lacks those capabilities. Runtime state and safety guards
are still evaluated only by RC-SM-001.

`CONTROL_UPDATE` requires a non-empty operation ID and an explicit exact
boolean deadman value. A true value is only a control-liveness candidate. A
false value is passed to RC-SM-001, which performs the canonical
`deadman_released` safety transition.

## Message disposition

- `COMMAND`, Controller-to-Rover `CONTROL_UPDATE`, and Controller-to-Rover
  `SESSION_END` can produce `RUNTIME_INPUT_READY`.
- `SESSION_HELLO` and correctly directed Rover-to-Client message types produce
  `NO_RUNTIME_ACTION`.
- A Rover-to-Client-only type presented with Controller-to-Rover direction is
  rejected and never dispatched.
- Envelope, payload, and capability failures produce `REJECTED`.

Every adapter result reports its own deterministic step index and keeps the
adapter disposition separate from the optional runtime `StepResult`.
`NO_RUNTIME_ACTION` is routing classification only. It is not Protocol formal
acceptance, session establishment, transport acknowledgement, or state
confirmation. `SESSION_HELLO`, `SESSION_ACCEPTED`, and `SESSION_REJECTED` are
not bound to the current active session; a candidate or notified session ID is
not installed by this adapter or bridge. COMMAND, CONTROL_UPDATE, and
Controller-to-Rover SESSION_END remain bound to the active boot, session, and
owner.
An unexpected adapter exception at the bridge boundary is not disguised as a
normal validation failure: it produces `internal_error=true` with
`ADAPTER_INTERNAL_ERROR`, and the runtime is not called.

## Virtual receiver bridge

`VirtualReceiverBridge.receive()` runs the adapter and calls
`RuntimeStateMachine.step()` only for `RUNTIME_INPUT_READY`. Adapter rejection
and `NO_RUNTIME_ACTION` leave the runtime step index and state unchanged.
Receiver-local `assert_deadman()` and `release_deadman()` map only to existing
local RC-SM-001 events; no deadman field is synthesized on an initial MOVE.
Boot completion, communication restoration, and deterministic tick helpers are
also receiver-local and never claim to be Protocol commands.

Reports contain separate adapter and runtime results, injected logical
identity, and a final runtime snapshot. They contain no wall-clock timestamp,
absolute path, user or host identity, random value, network activity, file
write, or hardware output. Real motor output remains `false`.

## PV0-VAL-002 completion fixture

The integration test supplies an explicit safe numeric requested speed, sets a
numeric speed limit through an earlier independent operation, and asserts the
receiver-local deadman before adapting sequence 42. It compares only the
runtime-expressible result. It does not infer speed from the vector's
`"forward"` expectation, does not modify the vector, does not claim full vector
execution or PASS, and does not change its
`RUNTIME_CONTRACT_REQUIRED` classification.

## HOLD

Wire protocol, production transport, authentication, persistent session or
sequence storage, message ID generation, exact duplicate result cache,
sequence collision identity comparison, final gap policy, final TTL/watchdog
values, real ESP32 integration, GPIO/PWM/motor output, hardware safety
approval, water/mud/paddy testing, and field operation remain outside
RC-WA-001 and on HOLD.
