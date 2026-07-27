# RC-NM-001 strict logical message normalizer

This package is a deterministic, software-only boundary for untrusted Python
built-in fixture objects. Fixture property names are internal test contracts;
they are not declared to be Protocol v0 wire keys.

The boundary validates transport-provided size and parse metadata, accepts only
exact built-in fixture types, applies closed-object property rules, and produces
either an existing `NormalizedLogicalMessage` or `SessionCandidate`. A validated
exact `list` or `tuple` of protocol version candidates is copied to an internal
tuple solely because `SessionCandidate` requires an immutable fixture value.
No other implicit conversion, alias, case conversion, default, clamp, rounding,
or null substitution is performed.

Normalization is classification and typed-model construction only. It does not
formally accept a command, update accepted sequence state, establish ownership,
dispatch a runtime event, change a latch, or zero an output. STOP and
EMERGENCY_STOP identification records only whether the Protocol v0
identification gate was passed. `defensive_zero_candidate` is classification
metadata; the defensive-zero executor is HOLD for a separate safety-reviewed
engineering phase.

`VirtualInputBoundary` connects normalized fixtures to the existing session
manager and runtime adapter. SESSION_HELLO uses session negotiation, and
Controller-to-Rover SESSION_END uses the manager's safety-checked session-end
path. Only an adapter `RUNTIME_INPUT_READY` result can reach the runtime.
Normalization, negotiation, adapter, and runtime results remain separate in the
deterministic report. Reports omit decoded fixture payloads and exception
details.

Out of scope and HOLD: JSON or byte parsing, UTF-8 handling, duplicate JSON-key
detection, formal wire schemas/property names, framing, networking,
authentication, persistent storage/NVM, hardware access, motor/PTO output,
and all actual defensive-zero execution.
