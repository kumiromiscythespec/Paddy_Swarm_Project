# RC-DZ-001 defensive zero executor

Status: software-only / simulator-first / real motor output prohibited

This package connects RC-NM-001 STOP and EMERGENCY_STOP identification
candidates to a receiver-local safety zero. It does not add a Protocol message,
wire command, or `Event` member. A defensive zero is never hidden STOP or
EMERGENCY_STOP acceptance.

`RuntimeStateMachine.apply_defensive_zero()` advances the deterministic runtime
once, validates receiver monotonic time, and reuses the existing
`_zero_motion()` safety transition. It returns `accepted=false`,
`sequence_accepted=false`, and `safety_action=ZERO_ALL_OUTPUTS`. It does not
change last-seen or last-accepted sequence state, establish a session, acquire
controller ownership, ARM, extend liveness/watchdog, issue an operation ID, or
clear a safety latch. Invalid ESTOP candidates do not create a formal emergency
stop latch.

The post-zero state is local invariant repair, not the requested command's
formal transition: DRIVE_ACTIVE becomes DRIVE_READY, PTO_ACTIVE becomes
PTO_READY, other non-active states remain unchanged, and existing latched
states remain latched. Armed READY/NEUTRAL states remain armed while motion,
PTO, operation ID, deadman, and watchdog are cleared.

`DefensiveZeroExecutor` distinguishes an executed local zero, a zero already
applied by runtime validation, a formally accepted STOP/EMERGENCY_STOP, and a
non-applicable input. Each normalizer boundary step is cached in-memory by its
deterministic index, so reevaluation cannot increment runtime twice or reapply
outputs. There is no global or persistent cache.

`VirtualDefensiveBoundary` wraps the existing `VirtualInputBoundary` without
modifying RC-NM-001. Its report keeps normalization, negotiation, adapter,
formal runtime, and defensive runtime results separate and omits decoded
payloads, exception text, paths, user/host identity, wall-clock timestamps, and
hardware actions.

HOLD: wire/JSON parsing, authentication and non-owner security policy, result
cache persistence, a hardware defensive-zero implementation, GPIO/PWM/motor or
PTO output, ESP32 integration, physical safety approval, and water/mud/paddy
field testing.
