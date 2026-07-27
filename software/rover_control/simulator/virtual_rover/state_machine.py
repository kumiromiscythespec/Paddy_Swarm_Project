from __future__ import annotations

from dataclasses import dataclass, replace

from .model import (
    MAX_SAFE_SEQUENCE,
    DriveMode,
    Event,
    Profile,
    RoverState,
    RuntimeConfig,
    RuntimeInput,
    RuntimeState,
    StepResult,
    normalize_event,
)


COMMAND_EVENTS = frozenset(
    {
        Event.ARM,
        Event.DISARM,
        Event.SET_SPEED_LIMIT,
        Event.SELECT_DRIVE,
        Event.SELECT_NEUTRAL,
        Event.SELECT_PTO,
        Event.MOVE_FORWARD,
        Event.MOVE_REVERSE,
        Event.TURN_LEFT,
        Event.TURN_RIGHT,
        Event.STOP,
        Event.EMERGENCY_STOP,
        Event.PTO_START,
        Event.PTO_STOP,
        Event.FAULT_RESET,
        Event.EMERGENCY_STOP_RESET,
    }
)
SEQUENCED_MESSAGE_EVENTS = COMMAND_EVENTS | {Event.CONTROL_UPDATE, Event.SESSION_END}
ACTIVE_STATES = {RoverState.DRIVE_ACTIVE, RoverState.PTO_ACTIVE}
ARMED_STATES = {
    RoverState.ARMED_NEUTRAL,
    RoverState.DRIVE_READY,
    RoverState.DRIVE_ACTIVE,
    RoverState.PTO_READY,
    RoverState.PTO_ACTIVE,
}
LATCHED_STATES = {
    RoverState.COMM_LOSS_LATCHED,
    RoverState.FAULT_LATCHED,
    RoverState.EMERGENCY_STOP_LATCHED,
}


class InternalInvariantError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _Outcome:
    state: RuntimeState
    accepted: bool = True
    rejection_reason: str | None = None
    safety_action: str = "NONE"
    sequence_accepted: bool = False
    diagnostic_code: str | None = None


class RuntimeStateMachine:
    """Pure deterministic Protocol v0 safety state-machine simulator."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        self._state = RuntimeState(
            session_id=self.config.session_id,
            used_session_ids=(self.config.session_id,),
        )
        self._assert_invariants(self._state)

    @property
    def state(self) -> RuntimeState:
        return self._state

    def apply_defensive_zero(
        self,
        *,
        now_ms: int,
        candidate_intent: str,
        rejection_reason: str,
        diagnostic_code: str,
    ) -> StepResult:
        """Apply a receiver-local zero without accepting a Protocol event."""
        previous = self._state
        event_label = "receiver_local_defensive_zero"
        try:
            if (
                type(candidate_intent) is not str
                or candidate_intent
                not in {Event.STOP.value, Event.EMERGENCY_STOP.value}
            ):
                raise InternalInvariantError(
                    "candidate_intent must identify STOP or EMERGENCY_STOP"
                )
            if type(rejection_reason) is not str or not rejection_reason:
                raise InternalInvariantError(
                    "rejection_reason must be a non-empty exact string"
                )
            if type(diagnostic_code) is not str or not diagnostic_code:
                raise InternalInvariantError(
                    "diagnostic_code must be a non-empty exact string"
                )
            if type(now_ms) is not int or now_ms < 0:
                raise InternalInvariantError(
                    "now_ms must be a non-negative exact integer"
                )
            if now_ms < previous.monotonic_time_ms:
                raise InternalInvariantError(
                    "monotonic time moved backwards"
                )
            prepared = replace(
                previous,
                monotonic_time_ms=now_ms,
                step_index=previous.step_index + 1,
            )
            safe = self._zero_motion(prepared)
            self._assert_invariants(safe)
            self._state = safe
            return self._result(
                previous,
                safe,
                f"{event_label}/{candidate_intent}",
                accepted=False,
                rejection_reason=rejection_reason,
                safety_action="ZERO_ALL_OUTPUTS",
                sequence_accepted=False,
                diagnostic_code=diagnostic_code,
            )
        except Exception:
            failure_input = RuntimeInput.local(
                event_label,
                now_ms=now_ms,
            )
            failed = self._internal_failure_state(
                previous,
                failure_input,
            )
            self._state = failed
            return self._result(
                previous,
                failed,
                event_label,
                accepted=False,
                rejection_reason="internal_error",
                safety_action="ZERO_ALL_OUTPUTS",
                sequence_accepted=False,
                diagnostic_code="DEFENSIVE_ZERO_LOCAL_INTERNAL_ERROR",
                internal_failure=True,
            )

    def step(self, runtime_input: RuntimeInput) -> StepResult:
        previous = self._state
        event_label = (
            runtime_input.event.value
            if isinstance(runtime_input.event, Event)
            else str(runtime_input.event)
        )
        priority_requested = (
            runtime_input.physical_estop_asserted
            or runtime_input.fault_present
        )
        try:
            try:
                event = normalize_event(runtime_input.event)
                event_label = event.value
            except (TypeError, ValueError):
                prepared = (
                    self._prepare_priority_state(previous, runtime_input)
                    if priority_requested
                    else self._prepare_state(
                        previous,
                        runtime_input,
                        allow_epoch_reset=False,
                    )
                )
                priority_outcome = self._priority_safety_outcome(
                    prepared,
                    runtime_input,
                )
                if priority_outcome is None:
                    priority_outcome = _Outcome(
                        self._zero_motion(prepared),
                        accepted=False,
                        rejection_reason="invalid_message_type",
                        safety_action="ZERO_ALL_OUTPUTS",
                        diagnostic_code="UNKNOWN_EVENT_FAIL_CLOSED",
                    )
                safe = priority_outcome.state
                self._state = safe
                self._assert_invariants(safe)
                return self._result(
                    previous,
                    safe,
                    event_label,
                    accepted=priority_outcome.accepted,
                    rejection_reason=priority_outcome.rejection_reason,
                    safety_action=priority_outcome.safety_action,
                    diagnostic_code=priority_outcome.diagnostic_code,
                )

            valid_boot_session = (
                event is Event.BOOT
                and self._is_unused_boot_session(previous, runtime_input.session_id)
            )
            boot_is_latched = (
                event is Event.BOOT
                and previous.official_state in LATCHED_STATES
            )
            if priority_requested:
                prepared = self._prepare_priority_state(
                    previous,
                    runtime_input,
                )
            elif event is Event.BOOT and (
                not valid_boot_session or boot_is_latched
            ):
                prepared = self._prepare_rejected_boot_attempt(
                    previous,
                    runtime_input,
                )
            else:
                prepared = self._prepare_state(
                    previous,
                    runtime_input,
                    allow_epoch_reset=valid_boot_session,
                )
            priority_outcome = self._priority_safety_outcome(
                prepared,
                runtime_input,
            )
            if priority_outcome is not None:
                outcome = priority_outcome
            elif event in SEQUENCED_MESSAGE_EVENTS:
                message_state = prepared
                compound_fault_reset_blocked = (
                    event is Event.FAULT_RESET
                    and message_state.official_state is RoverState.FAULT_LATCHED
                    and message_state.communication_loss_latched
                )
                prepared, rejection_reason, diagnostic_code = self._validate_message(
                    prepared,
                    runtime_input,
                )
                if rejection_reason is not None:
                    defensive = event in {Event.STOP, Event.EMERGENCY_STOP}
                    rejected_state = (
                        self._zero_motion(
                            prepared,
                            stop_reason=event.value,
                        )
                        if defensive
                        else prepared
                    )
                    outcome = _Outcome(
                        rejected_state,
                        accepted=False,
                        rejection_reason=rejection_reason,
                        safety_action="ZERO_ALL_OUTPUTS" if defensive else "NONE",
                        diagnostic_code=diagnostic_code,
                    )
                else:
                    dispatch_state = (
                        message_state
                        if compound_fault_reset_blocked
                        else prepared
                    )
                    outcome = self._dispatch(
                        dispatch_state,
                        event,
                        runtime_input,
                    )
                    if outcome.accepted and event in COMMAND_EVENTS:
                        outcome = replace(
                            outcome,
                            state=replace(
                                outcome.state,
                                last_accepted_sequence=runtime_input.sequence,
                            ),
                            sequence_accepted=True,
                        )
            else:
                outcome = self._dispatch(prepared, event, runtime_input)

            self._assert_invariants(outcome.state)
            self._state = outcome.state
            return self._result(
                previous,
                outcome.state,
                event_label,
                accepted=outcome.accepted,
                rejection_reason=outcome.rejection_reason,
                safety_action=outcome.safety_action,
                sequence_accepted=outcome.sequence_accepted,
                diagnostic_code=outcome.diagnostic_code,
            )
        except Exception as error:
            failed = self._internal_failure_state(previous, runtime_input)
            self._state = failed
            return self._result(
                previous,
                failed,
                event_label,
                accepted=False,
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code=f"INTERNAL_{type(error).__name__.upper()}",
                internal_failure=True,
            )

    def _prepare_state(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
        *,
        allow_epoch_reset: bool,
    ) -> RuntimeState:
        if type(runtime_input.now_ms) is not int or runtime_input.now_ms < 0:
            raise InternalInvariantError("now_ms must be a non-negative integer")
        if not allow_epoch_reset and runtime_input.now_ms < state.monotonic_time_ms:
            raise InternalInvariantError("monotonic time moved backwards")
        return replace(
            state,
            monotonic_time_ms=runtime_input.now_ms,
            step_index=state.step_index + 1,
        )

    @staticmethod
    def _prepare_priority_state(
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> RuntimeState:
        now_ms = (
            runtime_input.now_ms
            if type(runtime_input.now_ms) is int and runtime_input.now_ms >= 0
            else state.monotonic_time_ms
        )
        return replace(
            state,
            monotonic_time_ms=max(state.monotonic_time_ms, now_ms),
            step_index=state.step_index + 1,
        )

    @staticmethod
    def _prepare_rejected_boot_attempt(
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> RuntimeState:
        if type(runtime_input.now_ms) is not int or runtime_input.now_ms < 0:
            raise InternalInvariantError("now_ms must be a non-negative integer")
        return replace(
            state,
            monotonic_time_ms=max(
                state.monotonic_time_ms,
                runtime_input.now_ms,
            ),
            step_index=state.step_index + 1,
        )

    @staticmethod
    def _is_unused_boot_session(
        state: RuntimeState,
        session_id: object,
    ) -> bool:
        return (
            isinstance(session_id, str)
            and bool(session_id.strip())
            and session_id not in state.used_session_ids
        )

    def _validate_message(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> tuple[RuntimeState, str | None, str | None]:
        if runtime_input.session_id != state.session_id:
            return state, "invalid_session", "SESSION_MISMATCH"
        sequence = runtime_input.sequence
        if type(sequence) is not int or sequence < 0 or sequence > MAX_SAFE_SEQUENCE:
            return state, "missing_required_field", "SEQUENCE_REQUIRED"
        if state.last_seen_sequence is not None:
            if sequence == state.last_seen_sequence:
                return state, "duplicate_sequence", "DUPLICATE_SEQUENCE"
            if sequence < state.last_seen_sequence:
                return state, "stale_sequence", "STALE_SEQUENCE"
            if sequence > state.last_seen_sequence + 1:
                return state, "invalid_payload", "SEQUENCE_GAP_POLICY_FAIL_CLOSED"

        state = replace(state, last_seen_sequence=sequence)
        issued_at = runtime_input.issued_at_ms
        ttl_ms = runtime_input.ttl_ms
        if (
            type(issued_at) is not int
            or type(ttl_ms) is not int
            or issued_at < 0
            or ttl_ms <= 0
        ):
            return state, "missing_required_field", "FRESHNESS_FIELDS_REQUIRED"
        if ttl_ms > self.config.max_command_ttl_ms:
            return state, "invalid_payload", "TTL_LIMIT_EXCEEDED"
        if runtime_input.now_ms >= issued_at + ttl_ms:
            return state, "expired", "COMMAND_EXPIRED"
        return state, None, None

    def _priority_safety_outcome(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome | None:
        if runtime_input.physical_estop_asserted:
            safe = self._emergency_stop_state(state)
            diagnostic_code = "PHYSICAL_ESTOP_ASSERTED"
            if runtime_input.fault_present:
                safe = self._fault_state(safe, "fault_present")
                diagnostic_code = "PHYSICAL_ESTOP_ASSERTED_WITH_FAULT"
            return _Outcome(
                safe,
                accepted=False,
                rejection_reason="safety_latched",
                safety_action="LATCH_EMERGENCY_STOP",
                diagnostic_code=diagnostic_code,
            )
        if runtime_input.fault_present:
            return _Outcome(
                self._fault_state(state, "fault_present"),
                accepted=False,
                rejection_reason="safety_latched",
                safety_action="LATCH_FAULT",
                diagnostic_code="FAULT_PRESENT",
            )
        return None

    def _dispatch(
        self,
        state: RuntimeState,
        event: Event,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if event is Event.BOOT:
            if state.official_state in LATCHED_STATES:
                return _Outcome(
                    self._zero_motion(state),
                    accepted=False,
                    rejection_reason="safety_latched",
                    safety_action="ZERO_ALL_OUTPUTS",
                    diagnostic_code="BOOT_DOES_NOT_CLEAR_SAFETY_LATCH",
                )
            session_id = runtime_input.session_id
            if not isinstance(session_id, str) or not session_id.strip():
                return self._reject(
                    state,
                    "missing_required_field",
                    "BOOT_NEW_SESSION_REQUIRED",
                    fail_closed=True,
                )
            if session_id in state.used_session_ids:
                return self._reject(
                    state,
                    "invalid_session",
                    "BOOT_SESSION_REUSE_FORBIDDEN",
                    fail_closed=True,
                )
            return _Outcome(
                self._boot_state(
                    runtime_input.now_ms,
                    state.step_index,
                    session_id,
                    (*state.used_session_ids, session_id),
                )
            )
        if event is Event.BOOT_COMPLETE:
            if state.official_state is not RoverState.BOOT_SAFE:
                return self._reject(state, "invalid_state", "BOOT_COMPLETE_INVALID_STATE")
            if not state.boot_session_ready:
                return self._reject(
                    state,
                    "guard_failed",
                    "BOOT_NEW_SESSION_REQUIRED",
                )
            return _Outcome(replace(state, official_state=RoverState.DISARMED))
        if event is Event.BOOT_FAILED:
            return _Outcome(
                self._fault_state(state, "boot_failed"),
                safety_action="LATCH_FAULT",
                diagnostic_code="BOOT_FAILED",
            )
        if event is Event.COMMUNICATION_RESTORED:
            if state.communication_alive:
                return _Outcome(state)
            if state.official_state in ACTIVE_STATES:
                return self._reject(
                    state,
                    "guard_failed",
                    "ACTIVE_COMMUNICATION_STATE_INCONSISTENT",
                    fail_closed=True,
                )
            return _Outcome(replace(state, communication_alive=True))
        if event in {
            Event.COMMUNICATION_LOST,
            Event.WATCHDOG_TIMEOUT,
            Event.SESSION_END,
        }:
            return _Outcome(
                self._communication_loss_state(state, "communication_lost"),
                safety_action="LATCH_COMMUNICATION_LOSS",
            )
        if event is Event.TICK:
            if (
                state.official_state in ACTIVE_STATES
                and state.watchdog_deadline_ms is not None
                and runtime_input.now_ms >= state.watchdog_deadline_ms
            ):
                return _Outcome(
                    self._communication_loss_state(state, "communication_lost"),
                    safety_action="LATCH_COMMUNICATION_LOSS",
                    diagnostic_code="WATCHDOG_EXPIRED",
                )
            return _Outcome(state)
        if event is Event.DEADMAN_ASSERT:
            if state.official_state not in {
                RoverState.DRIVE_READY,
                RoverState.DRIVE_ACTIVE,
                RoverState.PTO_READY,
                RoverState.PTO_ACTIVE,
            }:
                return self._reject(state, "invalid_state", "DEADMAN_INVALID_STATE")
            if not state.armed or not state.communication_alive:
                return self._reject(state, "guard_failed", "DEADMAN_GUARD_FAILED")
            deadline = (
                runtime_input.now_ms + self.config.watchdog_timeout_ms
                if state.official_state in ACTIVE_STATES
                else state.watchdog_deadline_ms
            )
            return _Outcome(
                replace(
                    state,
                    deadman_active=True,
                    watchdog_deadline_ms=deadline,
                )
            )
        if event in {Event.DEADMAN_RELEASED, Event.COMMAND_EXPIRED}:
            stopped = self._zero_motion(
                state,
                stop_reason=event.value,
            )
            return _Outcome(
                stopped,
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code=event.value,
            )
        if event is Event.CONTROL_UPDATE:
            return self._control_update(state, runtime_input)
        if event is Event.SET_SPEED_LIMIT:
            return self._set_speed_limit(state, runtime_input)
        if event is Event.ARM:
            return self._arm(state)
        if event is Event.DISARM:
            return self._disarm(state)
        if event is Event.SELECT_DRIVE:
            return self._select_drive(state)
        if event is Event.SELECT_NEUTRAL:
            return self._select_neutral(state)
        if event is Event.SELECT_PTO:
            return self._select_pto(state)
        if event in {Event.MOVE_FORWARD, Event.MOVE_REVERSE}:
            return self._move(state, event, runtime_input)
        if event in {Event.TURN_LEFT, Event.TURN_RIGHT}:
            return self._reject(
                state,
                "capability_unavailable",
                "TURN_UNAVAILABLE",
                fail_closed=state.official_state in ACTIVE_STATES,
            )
        if event is Event.STOP:
            return _Outcome(
                self._zero_motion(state, stop_reason=Event.STOP.value),
                safety_action="ZERO_ALL_OUTPUTS",
            )
        if event is Event.EMERGENCY_STOP:
            return _Outcome(
                self._emergency_stop_state(state),
                safety_action="LATCH_EMERGENCY_STOP",
            )
        if event is Event.PTO_START:
            return self._pto_start(state, runtime_input)
        if event is Event.PTO_STOP:
            return self._pto_stop(state)
        if event is Event.FAULT_DETECTED:
            return _Outcome(
                self._fault_state(state, "fault_detected"),
                safety_action="LATCH_FAULT",
            )
        if event is Event.FAULT_RESET:
            return self._fault_reset(state, runtime_input)
        if event is Event.EMERGENCY_STOP_RESET:
            return self._emergency_stop_reset(state, runtime_input)
        raise InternalInvariantError(f"unhandled event {event.value}")

    def _set_speed_limit(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if state.official_state is not RoverState.DISARMED:
            return self._reject(state, "invalid_state", "SPEED_LIMIT_INVALID_STATE")
        value = runtime_input.speed_limit
        if type(value) is not int or not 1 <= value <= self.config.max_speed:
            return self._reject(state, "invalid_payload", "INVALID_SPEED_LIMIT")
        return _Outcome(replace(state, speed_limit=value))

    def _arm(self, state: RuntimeState) -> _Outcome:
        if state.official_state in LATCHED_STATES:
            return self._reject(state, "safety_latched", "ARM_SAFETY_LATCHED")
        if state.official_state is not RoverState.DISARMED:
            return self._reject(state, "invalid_state", "ARM_INVALID_STATE")
        if not state.communication_alive or not 1 <= state.speed_limit <= self.config.max_speed:
            return self._reject(state, "guard_failed", "ARM_GUARD_FAILED")
        next_state = (
            RoverState.DRIVE_READY
            if self.config.profile is Profile.ONE_SIDE_TEST
            else RoverState.ARMED_NEUTRAL
        )
        next_mode = (
            DriveMode.DRIVE
            if self.config.profile is Profile.ONE_SIDE_TEST
            else DriveMode.NEUTRAL
        )
        return _Outcome(
            replace(
                state,
                official_state=next_state,
                selected_mode=next_mode,
                armed=True,
                deadman_active=False,
            )
        )

    def _disarm(self, state: RuntimeState) -> _Outcome:
        if state.official_state in LATCHED_STATES:
            return self._reject(state, "safety_latched", "DISARM_DOES_NOT_CLEAR_LATCH")
        if state.official_state is RoverState.BOOT_SAFE:
            return self._reject(state, "invalid_state", "DISARM_INVALID_STATE")
        stopped = self._zero_motion(state)
        return _Outcome(
            replace(
                stopped,
                official_state=RoverState.DISARMED,
                selected_mode=DriveMode.NONE,
                armed=False,
                deadman_active=False,
            ),
            safety_action="ZERO_ALL_OUTPUTS",
        )

    def _select_drive(self, state: RuntimeState) -> _Outcome:
        if state.official_state is not RoverState.ARMED_NEUTRAL:
            return self._reject(
                state,
                "invalid_state",
                "SELECT_DRIVE_INVALID_STATE",
                fail_closed=state.official_state in ACTIVE_STATES,
            )
        return _Outcome(
            replace(
                state,
                official_state=RoverState.DRIVE_READY,
                selected_mode=DriveMode.DRIVE,
                deadman_active=False,
            )
        )

    def _select_neutral(self, state: RuntimeState) -> _Outcome:
        if state.official_state not in {RoverState.DRIVE_READY, RoverState.PTO_READY}:
            return self._reject(
                state,
                "invalid_state",
                "SELECT_NEUTRAL_INVALID_STATE",
                fail_closed=state.official_state in ACTIVE_STATES,
            )
        return _Outcome(
            replace(
                self._zero_motion(state),
                official_state=RoverState.ARMED_NEUTRAL,
                selected_mode=DriveMode.NEUTRAL,
            )
        )

    def _select_pto(self, state: RuntimeState) -> _Outcome:
        if not self.config.pto_available:
            return self._reject(state, "capability_unavailable", "PTO_UNAVAILABLE")
        if state.official_state is not RoverState.ARMED_NEUTRAL:
            return self._reject(
                state,
                "invalid_state",
                "SELECT_PTO_INVALID_STATE",
                fail_closed=state.official_state in ACTIVE_STATES,
            )
        return _Outcome(
            replace(
                state,
                official_state=RoverState.PTO_READY,
                selected_mode=DriveMode.PTO,
                deadman_active=False,
            )
        )

    def _move(
        self,
        state: RuntimeState,
        event: Event,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if state.official_state is RoverState.PTO_ACTIVE:
            return self._reject(
                state,
                "mode_conflict",
                "MOVE_DURING_PTO",
                fail_closed=True,
            )
        if state.official_state is RoverState.DRIVE_ACTIVE:
            requested_direction = 1 if event is Event.MOVE_FORWARD else -1
            current_direction = 1 if state.effective_speed > 0 else -1
            if requested_direction != current_direction:
                return self._reject(
                    state,
                    "guard_failed",
                    "DIRECTION_REVERSAL_REQUIRES_ZERO",
                    fail_closed=True,
                )
            return self._reject(
                state,
                "invalid_state",
                "ACTIVE_MOVE_REQUIRES_CONTROL_UPDATE",
            )
        if state.official_state in LATCHED_STATES:
            return self._reject(state, "safety_latched", "MOVE_SAFETY_LATCHED")
        if state.official_state is not RoverState.DRIVE_READY:
            return self._reject(state, "invalid_state", "MOVE_INVALID_STATE")
        if not state.armed:
            return self._reject(state, "not_armed", "MOVE_NOT_ARMED")
        if not state.communication_alive or not state.deadman_active:
            return self._reject(state, "guard_failed", "MOVE_DEADMAN_OR_COMM_GUARD")
        speed = runtime_input.requested_speed
        if type(speed) is not int or not 1 <= speed <= state.speed_limit:
            return self._reject(state, "invalid_payload", "MOVE_SPEED_INVALID")
        effective = speed if event is Event.MOVE_FORWARD else -speed
        candidate = replace(
            state,
            official_state=RoverState.DRIVE_ACTIVE,
            selected_mode=DriveMode.DRIVE,
            requested_speed=speed,
            effective_speed=effective,
            left_output=effective,
            right_output=None,
            pto_requested=False,
            pto_effective=False,
            operation_id=self._operation_id(runtime_input.sequence),
            watchdog_deadline_ms=runtime_input.now_ms + self.config.watchdog_timeout_ms,
            stop_reason=None,
        )
        if not runtime_input.output_apply_success:
            return _Outcome(
                self._fault_state(candidate, "output_apply_failed"),
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code="OUTPUT_APPLY_FAILED",
            )
        return _Outcome(candidate)

    def _control_update(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if state.official_state not in ACTIVE_STATES:
            return self._reject(state, "invalid_state", "CONTROL_UPDATE_INVALID_STATE")
        if runtime_input.operation_id != state.operation_id:
            return self._reject(state, "invalid_payload", "OPERATION_ID_MISMATCH")
        if type(runtime_input.deadman_asserted) is not bool:
            return self._reject(state, "missing_required_field", "DEADMAN_VALUE_REQUIRED")
        if not runtime_input.deadman_asserted:
            return _Outcome(
                self._zero_motion(
                    state,
                    stop_reason=Event.DEADMAN_RELEASED.value,
                ),
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code="deadman_released",
            )
        return _Outcome(
            replace(
                state,
                deadman_active=True,
                watchdog_deadline_ms=runtime_input.now_ms + self.config.watchdog_timeout_ms,
            )
        )

    def _pto_start(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if not self.config.pto_available:
            return self._reject(state, "capability_unavailable", "PTO_UNAVAILABLE")
        if state.official_state is RoverState.DRIVE_ACTIVE:
            return self._reject(
                state,
                "mode_conflict",
                "PTO_START_DURING_DRIVE",
                fail_closed=True,
            )
        if state.official_state is not RoverState.PTO_READY:
            return self._reject(state, "invalid_state", "PTO_START_INVALID_STATE")
        if not state.armed or not state.communication_alive or not state.deadman_active:
            return self._reject(state, "guard_failed", "PTO_START_GUARD_FAILED")
        candidate = replace(
            state,
            official_state=RoverState.PTO_ACTIVE,
            selected_mode=DriveMode.PTO,
            requested_speed=0,
            effective_speed=0,
            left_output=0,
            right_output=None,
            pto_requested=True,
            pto_effective=True,
            operation_id=self._operation_id(runtime_input.sequence),
            watchdog_deadline_ms=runtime_input.now_ms + self.config.watchdog_timeout_ms,
            stop_reason=None,
        )
        if not runtime_input.output_apply_success:
            return _Outcome(
                self._fault_state(candidate, "output_apply_failed"),
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code="OUTPUT_APPLY_FAILED",
            )
        return _Outcome(candidate)

    def _pto_stop(self, state: RuntimeState) -> _Outcome:
        if not self.config.pto_available:
            return self._reject(state, "capability_unavailable", "PTO_UNAVAILABLE")
        if state.official_state not in {RoverState.PTO_ACTIVE, RoverState.PTO_READY}:
            return self._reject(state, "invalid_state", "PTO_STOP_INVALID_STATE")
        return _Outcome(
            replace(
                self._zero_motion(state),
                official_state=RoverState.PTO_READY,
                selected_mode=DriveMode.PTO,
            ),
            safety_action="ZERO_ALL_OUTPUTS",
        )

    def _fault_reset(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if state.official_state is not RoverState.FAULT_LATCHED:
            return self._reject(state, "invalid_state", "FAULT_RESET_INVALID_STATE")
        if state.communication_loss_latched:
            return _Outcome(
                self._zero_motion(state),
                accepted=False,
                rejection_reason="safety_latched",
                safety_action="ZERO_ALL_OUTPUTS",
                diagnostic_code="FAULT_RESET_BLOCKED_BY_COMM_LOSS_LATCH",
            )
        if (
            not runtime_input.safety_confirmation
            or runtime_input.fault_present
            or runtime_input.physical_estop_asserted
        ):
            return self._reject(state, "guard_failed", "FAULT_RESET_GUARD_FAILED")
        return _Outcome(
            RuntimeState(
                last_seen_sequence=state.last_seen_sequence,
                last_accepted_sequence=state.last_accepted_sequence,
                monotonic_time_ms=runtime_input.now_ms,
                session_id=state.session_id,
                used_session_ids=state.used_session_ids,
                boot_session_ready=False,
                step_index=state.step_index,
            )
        )

    def _emergency_stop_reset(
        self,
        state: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> _Outcome:
        if state.official_state is not RoverState.EMERGENCY_STOP_LATCHED:
            return self._reject(state, "invalid_state", "ESTOP_RESET_INVALID_STATE")
        if (
            not runtime_input.safety_confirmation
            or runtime_input.physical_estop_asserted
            or runtime_input.fault_present
            or state.fault_latched
            or state.communication_loss_latched
            or not state.communication_alive
        ):
            return self._reject(state, "guard_failed", "ESTOP_RESET_GUARD_FAILED")
        return _Outcome(
            replace(
                self._zero_motion(state),
                official_state=RoverState.DISARMED,
                selected_mode=DriveMode.NONE,
                armed=False,
                emergency_stop_latched=False,
                deadman_active=False,
            )
        )

    def _reject(
        self,
        state: RuntimeState,
        reason: str,
        diagnostic_code: str,
        *,
        fail_closed: bool = False,
    ) -> _Outcome:
        rejected_state = self._zero_motion(state) if fail_closed else state
        was_active = state.official_state in ACTIVE_STATES
        return _Outcome(
            rejected_state,
            accepted=False,
            rejection_reason=reason,
            safety_action="ZERO_ALL_OUTPUTS" if fail_closed and was_active else "NONE",
            diagnostic_code=diagnostic_code,
        )

    def _zero_motion(
        self,
        state: RuntimeState,
        *,
        stop_reason: str | None = None,
    ) -> RuntimeState:
        next_state = state.official_state
        if state.official_state is RoverState.DRIVE_ACTIVE:
            next_state = RoverState.DRIVE_READY
        elif state.official_state is RoverState.PTO_ACTIVE:
            next_state = RoverState.PTO_READY
        return replace(
            state,
            official_state=next_state,
            requested_speed=0,
            effective_speed=0,
            left_output=0,
            right_output=None,
            pto_requested=False,
            pto_effective=False,
            operation_id=None,
            watchdog_deadline_ms=None,
            deadman_active=False,
            stop_reason=(
                state.stop_reason
                if stop_reason is None
                else stop_reason
            ),
        )

    def _communication_loss_state(
        self,
        state: RuntimeState,
        reason: str,
    ) -> RuntimeState:
        safe = self._zero_motion(state)
        if state.official_state is RoverState.EMERGENCY_STOP_LATCHED:
            next_state = RoverState.EMERGENCY_STOP_LATCHED
        elif state.official_state is RoverState.FAULT_LATCHED:
            next_state = RoverState.FAULT_LATCHED
        elif state.official_state in ARMED_STATES:
            next_state = RoverState.COMM_LOSS_LATCHED
        else:
            next_state = state.official_state
        return replace(
            safe,
            official_state=next_state,
            selected_mode=DriveMode.NONE if next_state in LATCHED_STATES else safe.selected_mode,
            armed=False if next_state in LATCHED_STATES else safe.armed,
            communication_alive=False,
            communication_loss_latched=(
                state.communication_loss_latched
                or state.official_state in ARMED_STATES
                or state.official_state in LATCHED_STATES
            ),
            stop_reason=reason,
        )

    def _emergency_stop_state(self, state: RuntimeState) -> RuntimeState:
        return replace(
            self._zero_motion(state),
            official_state=RoverState.EMERGENCY_STOP_LATCHED,
            selected_mode=DriveMode.NONE,
            armed=False,
            emergency_stop_latched=True,
            stop_reason="EMERGENCY_STOP",
        )

    def _fault_state(self, state: RuntimeState, reason: str) -> RuntimeState:
        reasons = state.fault_reasons
        if reason not in reasons:
            reasons = (*reasons, reason)
        next_state = (
            RoverState.EMERGENCY_STOP_LATCHED
            if state.official_state is RoverState.EMERGENCY_STOP_LATCHED
            else RoverState.FAULT_LATCHED
        )
        if next_state is RoverState.EMERGENCY_STOP_LATCHED:
            stop_reason = state.stop_reason or Event.EMERGENCY_STOP.value
        else:
            stop_reason = reason
        return replace(
            self._zero_motion(state),
            official_state=next_state,
            selected_mode=DriveMode.NONE,
            armed=False,
            fault_latched=True,
            fault_reasons=reasons,
            stop_reason=stop_reason,
        )

    @staticmethod
    def _boot_state(
        now_ms: int,
        step_index: int,
        session_id: str,
        used_session_ids: tuple[str, ...],
    ) -> RuntimeState:
        return RuntimeState(
            session_id=session_id,
            used_session_ids=used_session_ids,
            monotonic_time_ms=now_ms,
            step_index=step_index,
        )

    def _internal_failure_state(
        self,
        previous: RuntimeState,
        runtime_input: RuntimeInput,
    ) -> RuntimeState:
        now_ms = (
            runtime_input.now_ms
            if type(runtime_input.now_ms) is int and runtime_input.now_ms >= 0
            else previous.monotonic_time_ms
        )
        prepared = replace(
            previous,
            monotonic_time_ms=max(previous.monotonic_time_ms, now_ms),
            step_index=previous.step_index + 1,
        )
        return self._fault_state(prepared, "internal_invariant_failure")

    @staticmethod
    def _operation_id(sequence: int | None) -> str:
        if sequence is None:
            raise InternalInvariantError("operation-starting command requires a sequence")
        return f"operation-{sequence:016d}"

    def _assert_invariants(self, state: RuntimeState) -> None:
        if self.config.real_motor_output_enabled:
            raise InternalInvariantError("real motor output must remain disabled")
        if state.right_output is not None:
            raise InternalInvariantError("unavailable right output must remain None")
        if (
            not state.used_session_ids
            or state.session_id not in state.used_session_ids
            or len(state.used_session_ids) != len(set(state.used_session_ids))
        ):
            raise InternalInvariantError("session identity history invariant failed")
        if state.pto_effective and state.left_output != 0:
            raise InternalInvariantError("drive and PTO cannot be active together")
        if state.official_state is not RoverState.DRIVE_ACTIVE and (
            state.left_output != 0 or state.effective_speed != 0
        ):
            raise InternalInvariantError("drive output outside DRIVE_ACTIVE")
        if state.official_state is not RoverState.PTO_ACTIVE and state.pto_effective:
            raise InternalInvariantError("PTO output outside PTO_ACTIVE")
        if state.official_state in ARMED_STATES and not state.armed:
            raise InternalInvariantError("armed state has armed=false")
        if state.official_state not in ARMED_STATES and state.armed:
            raise InternalInvariantError("safe or latched state has armed=true")
        if state.official_state is RoverState.DRIVE_ACTIVE:
            if (
                state.left_output == 0
                or state.operation_id is None
                or not state.deadman_active
                or not state.communication_alive
                or state.pto_effective
            ):
                raise InternalInvariantError("DRIVE_ACTIVE guard invariant failed")
        elif state.official_state is RoverState.PTO_ACTIVE:
            if (
                not state.pto_effective
                or state.operation_id is None
                or not state.deadman_active
                or not state.communication_alive
                or state.left_output != 0
            ):
                raise InternalInvariantError("PTO_ACTIVE guard invariant failed")
        elif state.operation_id is not None:
            raise InternalInvariantError("operation ID outside active state")
        if (
            state.official_state is RoverState.COMM_LOSS_LATCHED
            and not state.communication_loss_latched
        ):
            raise InternalInvariantError("communication latch missing")
        if state.official_state is RoverState.FAULT_LATCHED and not state.fault_latched:
            raise InternalInvariantError("fault latch missing")
        if (
            state.official_state is RoverState.EMERGENCY_STOP_LATCHED
            and not state.emergency_stop_latched
        ):
            raise InternalInvariantError("emergency stop latch missing")

    @staticmethod
    def _result(
        previous: RuntimeState,
        current: RuntimeState,
        event: str,
        *,
        accepted: bool,
        rejection_reason: str | None = None,
        safety_action: str = "NONE",
        sequence_accepted: bool = False,
        diagnostic_code: str | None = None,
        internal_failure: bool = False,
    ) -> StepResult:
        return StepResult(
            step_index=current.step_index,
            previous_state=previous.official_state.value,
            official_state=current.official_state.value,
            event=event,
            accepted=accepted,
            rejection_reason=rejection_reason,
            armed=current.armed,
            emergency_stop_latched=current.emergency_stop_latched,
            deadman_active=current.deadman_active,
            communication_alive=current.communication_alive,
            selected_mode=current.selected_mode.value,
            requested_speed=current.requested_speed,
            effective_speed=current.effective_speed,
            left_output=current.left_output,
            right_output=current.right_output,
            pto_requested=current.pto_requested,
            pto_effective=current.pto_effective,
            safety_action=safety_action,
            sequence_accepted=sequence_accepted,
            last_accepted_sequence=current.last_accepted_sequence,
            operation_id=current.operation_id,
            stop_reason=current.stop_reason,
            diagnostic_code=diagnostic_code,
            internal_failure=internal_failure,
        )


def snapshot_dict(state: RuntimeState) -> dict[str, object]:
    return {
        "official_state": state.official_state.value,
        "armed": state.armed,
        "emergency_stop_latched": state.emergency_stop_latched,
        "communication_loss_latched": state.communication_loss_latched,
        "fault_latched": state.fault_latched,
        "deadman_active": state.deadman_active,
        "communication_alive": state.communication_alive,
        "selected_mode": state.selected_mode.value,
        "speed_limit": state.speed_limit,
        "requested_speed": state.requested_speed,
        "effective_speed": state.effective_speed,
        "left_output": state.left_output,
        "right_output": state.right_output,
        "pto_requested": state.pto_requested,
        "pto_effective": state.pto_effective,
        "last_accepted_sequence": state.last_accepted_sequence,
        "operation_id": state.operation_id,
        "stop_reason": state.stop_reason,
        "step_index": state.step_index,
    }
