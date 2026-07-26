from __future__ import annotations

from dataclasses import replace

from ....simulator.virtual_rover import (
    Event,
    RoverState,
    RuntimeInput,
    RuntimeStateMachine,
)
from ..runtime_adapter import (
    AdapterDisposition,
    LogicalMessageType,
    MessageDirection,
    NormalizedLogicalMessage,
    ReceiverContext,
    RuntimeInputAdapter,
    SenderRole,
    SessionEndPayload,
)

from .model import (
    LocalRuntimeAction,
    ManagerAction,
    NegotiationDisposition,
    NegotiationResult,
    ReceiverPolicy,
    RuntimeDispatch,
    RuntimeSynchronizationState,
    SessionCandidate,
    SessionEndRequest,
    SessionManagerState,
    SessionRole,
)


LATCHED_STATES = frozenset(
    {
        RoverState.COMM_LOSS_LATCHED,
        RoverState.FAULT_LATCHED,
        RoverState.EMERGENCY_STOP_LATCHED,
    }
)
NEGOTIATION_SAFE_STATES = frozenset(
    {
        RoverState.BOOT_SAFE,
        RoverState.DISARMED,
    }
)


class SessionNegotiationManager:
    """Deterministic in-process session and controller ownership manager."""

    def __init__(
        self,
        *,
        current_rover_boot_id: str,
        supported_protocol_versions: tuple[str, ...],
        runtime: RuntimeStateMachine,
        receiver_policy: ReceiverPolicy,
        initial_used_session_ids: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(current_rover_boot_id, str) or not current_rover_boot_id:
            raise ValueError("current_rover_boot_id must be non-empty")
        if (
            type(supported_protocol_versions) is not tuple
            or not supported_protocol_versions
            or any(
                not isinstance(value, str) or not value
                for value in supported_protocol_versions
            )
            or len(supported_protocol_versions)
            != len(set(supported_protocol_versions))
        ):
            raise ValueError("supported protocol versions must be unique strings")
        if not isinstance(runtime, RuntimeStateMachine):
            raise TypeError("runtime must be a RuntimeStateMachine")
        if not isinstance(receiver_policy, ReceiverPolicy):
            raise TypeError("receiver_policy must be a ReceiverPolicy")
        if (
            type(initial_used_session_ids) is not tuple
            or any(
                not isinstance(value, str) or not value
                for value in initial_used_session_ids
            )
            or len(initial_used_session_ids) != len(set(initial_used_session_ids))
        ):
            raise ValueError("initial used session IDs must be unique strings")
        self._validate_policy_alignment(runtime, receiver_policy)
        self._runtime = runtime
        self._policy = receiver_policy
        self._supported_protocol_versions = supported_protocol_versions
        self._adapter = RuntimeInputAdapter()
        self._receiver_context: ReceiverContext | None = None
        self._state = SessionManagerState(
            current_rover_boot_id=current_rover_boot_id,
            used_session_ids=initial_used_session_ids,
        )

    @property
    def state(self) -> SessionManagerState:
        return self._state

    @property
    def runtime(self) -> RuntimeStateMachine:
        return self._runtime

    @property
    def receiver_context(self) -> ReceiverContext | None:
        return self._receiver_context

    @property
    def receiver_policy(self) -> ReceiverPolicy:
        return self._policy

    def process_hello(
        self,
        candidate: SessionCandidate,
        *,
        now_ms: int,
    ) -> ManagerAction:
        if not isinstance(candidate, SessionCandidate):
            raise TypeError("candidate must be a SessionCandidate")
        self._validate_now(now_ms)
        result_index = self._state.negotiation_step_index + 1
        requested_role = self._role_label(candidate.requested_role)

        malformed_diagnostic = self._candidate_structure_diagnostic(
            candidate,
            result_index,
        )
        if malformed_diagnostic is not None:
            return self._reject(
                result_index,
                "malformed_candidate",
                malformed_diagnostic,
                requested_role=requested_role,
            )

        versions = candidate.protocol_versions
        selected_version = next(
            (
                supported
                for supported in self._supported_protocol_versions
                if supported in versions
            ),
            None,
        )
        if selected_version is None:
            return self._reject(
                result_index,
                "unsupported_version",
                "NO_SUPPORTED_PROTOCOL_VERSION",
                requested_role=requested_role,
            )

        role = self._role_or_none(candidate.requested_role)
        if role is not SessionRole.CONTROLLER:
            return self._reject(
                result_index,
                "role_unavailable",
                "OBSERVER_ROLE_HOLD"
                if role is SessionRole.OBSERVER
                else "REQUESTED_ROLE_UNAVAILABLE",
                requested_role=requested_role,
            )
        if candidate.rover_boot_id != self._state.current_rover_boot_id:
            return self._reject(
                result_index,
                "boot_id_mismatch",
                "ROVER_BOOT_ID_MISMATCH",
                requested_role=role.value,
            )

        session_id = candidate.candidate_session_id
        runtime_used_ids = self._runtime.state.used_session_ids
        if (
            session_id == self._state.active_session_id
            or session_id in self._state.used_session_ids
            or session_id in runtime_used_ids
        ):
            return self._reject(
                result_index,
                "session_id_reused",
                "SESSION_ID_REUSE_FORBIDDEN",
                requested_role=role.value,
            )

        sync_diagnostic = self._runtime_context_diagnostic()
        if sync_diagnostic is not None:
            return self._reject(
                result_index,
                "runtime_not_safe",
                sync_diagnostic,
                requested_role=role.value,
            )
        if self._state.controller_owned:
            return self._reject(
                result_index,
                "controller_active",
                "CONTROLLER_ALREADY_ACTIVE",
                requested_role=role.value,
            )

        safety_reason, safety_diagnostic = self._runtime_safety_rejection()
        if safety_reason is not None:
            return self._reject(
                result_index,
                safety_reason,
                safety_diagnostic,
                requested_role=role.value,
            )

        changing_controller = (
            self._state.last_ended_controller_owner_id is not None
            and candidate.sender_id
            != self._state.last_ended_controller_owner_id
        )
        if changing_controller:
            if (
                self._runtime.state.official_state
                is not RoverState.DISARMED
            ):
                return self._reject(
                    result_index,
                    "runtime_not_safe",
                    "CONTROLLER_SWITCH_REQUIRES_DISARMED",
                    requested_role=role.value,
                )
            if (
                self._state.runtime_synchronization_state
                != RuntimeSynchronizationState.SESSION_ENDED.value
            ):
                return self._reject(
                    result_index,
                    "runtime_not_safe",
                    "PREVIOUS_CONTROLLER_NOT_SAFELY_ENDED",
                    requested_role=role.value,
                )
            if not candidate.human_switch_confirmation:
                return self._reject(
                    result_index,
                    "human_confirmation_required",
                    "CONTROLLER_SWITCH_CONFIRMATION_REQUIRED",
                    requested_role=role.value,
                )

        runtime_result = self._runtime.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=now_ms,
                session_id=session_id,
            )
        )
        if runtime_result.internal_failure:
            return self._reject(
                result_index,
                "internal_error",
                "RUNTIME_BOOT_INTERNAL_ERROR",
                requested_role=role.value,
                disposition=NegotiationDisposition.INTERNAL_ERROR,
                runtime_dispatched=True,
                runtime_result=runtime_result,
                synchronization=RuntimeSynchronizationState.INTERNAL_ERROR,
            )
        if not runtime_result.accepted:
            reason = (
                "safety_latched"
                if runtime_result.rejection_reason == "safety_latched"
                else "session_id_reused"
                if runtime_result.rejection_reason == "invalid_session"
                else "runtime_not_safe"
            )
            return self._reject(
                result_index,
                reason,
                runtime_result.diagnostic_code or "RUNTIME_BOOT_REJECTED",
                requested_role=role.value,
                runtime_dispatched=True,
                runtime_result=runtime_result,
                synchronization=(
                    RuntimeSynchronizationState.RUNTIME_BOOT_REJECTED
                ),
            )

        next_state = replace(
            self._state,
            active_session_id=session_id,
            active_controller_owner_id=candidate.sender_id,
            active_sender_instance_id=candidate.sender_instance_id,
            selected_protocol_version=selected_version,
            controller_owned=True,
            used_session_ids=(*self._state.used_session_ids, session_id),
            negotiation_step_index=result_index,
            last_negotiation_disposition=(
                NegotiationDisposition.SESSION_ACCEPTED.value
            ),
            session_generation_counter=(
                self._state.session_generation_counter + 1
            ),
            session_termination_pending=False,
            runtime_synchronization_state=(
                RuntimeSynchronizationState.SYNCHRONIZED.value
            ),
        )
        self._state = next_state
        self._receiver_context = self._build_receiver_context(now_ms)
        result = NegotiationResult(
            disposition=NegotiationDisposition.SESSION_ACCEPTED,
            rejection_reason=None,
            diagnostic_code=None,
            selected_protocol_version=selected_version,
            accepted_session_id=session_id,
            requested_role=role.value,
            accepted_role=role.value,
            rover_boot_id=self._state.current_rover_boot_id,
            controller_ownership=True,
            capability_profile_reference=(
                self._policy.capability_profile_reference
            ),
            deterministic_result_index=result_index,
            runtime_event_dispatched=True,
            manager_state=self._state,
        )
        return ManagerAction(result, runtime_result=runtime_result)

    def end_session(
        self,
        request: SessionEndRequest,
        *,
        now_ms: int,
    ) -> ManagerAction:
        if not isinstance(request, SessionEndRequest):
            raise TypeError("request must be a SessionEndRequest")
        self._validate_now(now_ms)
        result_index = self._state.negotiation_step_index + 1
        diagnostic = self._session_end_structure_diagnostic(
            request,
            result_index,
        )
        if diagnostic is not None:
            return self._reject(
                result_index,
                "malformed_candidate",
                diagnostic,
                requested_role=SessionRole.CONTROLLER.value,
            )
        if not self._state.controller_owned or self._receiver_context is None:
            return self._reject(
                result_index,
                "runtime_not_safe",
                "NO_ACTIVE_CONTROLLER_SESSION",
                requested_role=SessionRole.CONTROLLER.value,
            )
        if request.rover_boot_id != self._state.current_rover_boot_id:
            return self._reject(
                result_index,
                "boot_id_mismatch",
                "ROVER_BOOT_ID_MISMATCH",
                requested_role=SessionRole.CONTROLLER.value,
            )
        if request.session_id != self._state.active_session_id:
            return self._reject(
                result_index,
                "session_id_reused",
                "SESSION_END_SESSION_MISMATCH",
                requested_role=SessionRole.CONTROLLER.value,
            )
        if (
            request.sender_id != self._state.active_controller_owner_id
            or request.sender_instance_id
            != self._state.active_sender_instance_id
        ):
            return self._reject(
                result_index,
                "controller_active",
                "ACTIVE_CONTROLLER_IDENTITY_MISMATCH",
                requested_role=SessionRole.CONTROLLER.value,
            )
        sync_diagnostic = self._runtime_context_diagnostic()
        if sync_diagnostic is not None:
            return self._reject(
                result_index,
                "runtime_not_safe",
                sync_diagnostic,
                requested_role=SessionRole.CONTROLLER.value,
            )

        context = replace(
            self._receiver_context,
            current_monotonic_time_ms=now_ms,
        )
        message = NormalizedLogicalMessage(
            protocol_version=self._state.selected_protocol_version,
            logical_message_type=LogicalMessageType.SESSION_END,
            direction=MessageDirection.CONTROLLER_TO_ROVER,
            rover_boot_id=self._state.current_rover_boot_id,
            session_id=self._state.active_session_id,
            sender_id=self._state.active_controller_owner_id,
            sender_role=SenderRole.CONTROLLER,
            controller_ownership=True,
            message_id=request.message_id,
            sequence=request.sequence,
            freshness_reference_ms=request.freshness_reference_ms,
            ttl_ms=request.ttl_ms,
            payload=SessionEndPayload(),
        )
        adapter_result = self._adapter.adapt(message, context)
        if adapter_result.disposition is not AdapterDisposition.RUNTIME_INPUT_READY:
            return self._reject(
                result_index,
                "malformed_candidate",
                adapter_result.diagnostic_code
                or "SESSION_END_ADAPTER_REJECTED",
                requested_role=SessionRole.CONTROLLER.value,
                adapter_result=adapter_result,
            )

        self._state = replace(
            self._state,
            session_termination_pending=True,
        )
        runtime_result = self._runtime.step(adapter_result.runtime_input)
        if runtime_result.internal_failure:
            return self._reject(
                result_index,
                "internal_error",
                "RUNTIME_SESSION_END_INTERNAL_ERROR",
                requested_role=SessionRole.CONTROLLER.value,
                disposition=NegotiationDisposition.INTERNAL_ERROR,
                runtime_dispatched=True,
                adapter_result=adapter_result,
                runtime_result=runtime_result,
                synchronization=RuntimeSynchronizationState.INTERNAL_ERROR,
            )
        if not runtime_result.accepted:
            return self._reject(
                result_index,
                "runtime_not_safe",
                runtime_result.diagnostic_code
                or "RUNTIME_SESSION_END_REJECTED",
                requested_role=SessionRole.CONTROLLER.value,
                runtime_dispatched=True,
                adapter_result=adapter_result,
                runtime_result=runtime_result,
                synchronization=(
                    RuntimeSynchronizationState.RUNTIME_SESSION_END_REJECTED
                ),
            )
        if not self._runtime_has_session_end_postcondition():
            return self._reject(
                result_index,
                "internal_error",
                "SESSION_END_SAFETY_POSTCONDITION_FAILED",
                requested_role=SessionRole.CONTROLLER.value,
                disposition=NegotiationDisposition.INTERNAL_ERROR,
                runtime_dispatched=True,
                adapter_result=adapter_result,
                runtime_result=runtime_result,
                synchronization=RuntimeSynchronizationState.INTERNAL_ERROR,
            )

        ended_session_id = self._state.active_session_id
        ended_owner_id = self._state.active_controller_owner_id
        ended_instance_id = self._state.active_sender_instance_id
        next_state = replace(
            self._state,
            active_session_id=None,
            active_controller_owner_id=None,
            active_sender_instance_id=None,
            selected_protocol_version=None,
            controller_owned=False,
            negotiation_step_index=result_index,
            last_negotiation_disposition=(
                NegotiationDisposition.SESSION_ENDED.value
            ),
            session_termination_pending=False,
            runtime_synchronization_state=(
                RuntimeSynchronizationState.SESSION_ENDED.value
            ),
            last_ended_controller_owner_id=ended_owner_id,
            last_ended_sender_instance_id=ended_instance_id,
        )
        self._state = next_state
        self._receiver_context = None
        result = NegotiationResult(
            disposition=NegotiationDisposition.SESSION_ENDED,
            rejection_reason=None,
            diagnostic_code=None,
            selected_protocol_version=None,
            accepted_session_id=ended_session_id,
            requested_role=SessionRole.CONTROLLER.value,
            accepted_role=None,
            rover_boot_id=self._state.current_rover_boot_id,
            controller_ownership=False,
            capability_profile_reference=(
                self._policy.capability_profile_reference
            ),
            deterministic_result_index=result_index,
            runtime_event_dispatched=True,
            manager_state=self._state,
        )
        return ManagerAction(
            result,
            adapter_result=adapter_result,
            runtime_result=runtime_result,
        )

    def update_rover_boot_id(
        self,
        new_rover_boot_id: object,
        *,
        now_ms: int,
        request_index: object,
    ) -> ManagerAction:
        self._validate_now(now_ms)
        result_index = self._state.negotiation_step_index + 1
        if (
            not isinstance(new_rover_boot_id, str)
            or not new_rover_boot_id
            or type(request_index) is not int
            or request_index != result_index
        ):
            return self._reject(
                result_index,
                "malformed_candidate",
                "BOOT_ID_UPDATE_INVALID",
            )
        if new_rover_boot_id == self._state.current_rover_boot_id:
            next_state = replace(
                self._state,
                negotiation_step_index=result_index,
                last_negotiation_disposition=(
                    NegotiationDisposition.NO_CHANGE.value
                ),
            )
            self._state = next_state
            return ManagerAction(
                self._make_result(
                    NegotiationDisposition.NO_CHANGE,
                    result_index,
                    diagnostic_code="ROVER_BOOT_ID_UNCHANGED",
                )
            )

        runtime_result = None
        runtime_dispatched = False
        if self._runtime_requires_safety_stop():
            runtime_dispatched = True
            runtime_result = self._runtime.step(
                RuntimeInput.local(
                    Event.COMMUNICATION_LOST,
                    now_ms=now_ms,
                )
            )

        had_active_session = self._state.active_session_id is not None
        ended_owner = self._state.active_controller_owner_id
        ended_instance = self._state.active_sender_instance_id
        disposition = (
            NegotiationDisposition.SESSION_ENDED
            if had_active_session
            else NegotiationDisposition.NO_CHANGE
        )
        synchronization = RuntimeSynchronizationState.BOOT_ID_CHANGED
        if runtime_result is not None and runtime_result.internal_failure:
            disposition = NegotiationDisposition.INTERNAL_ERROR
            synchronization = RuntimeSynchronizationState.INTERNAL_ERROR
        self._state = replace(
            self._state,
            current_rover_boot_id=new_rover_boot_id,
            active_session_id=None,
            active_controller_owner_id=None,
            active_sender_instance_id=None,
            selected_protocol_version=None,
            controller_owned=False,
            negotiation_step_index=result_index,
            last_negotiation_disposition=disposition.value,
            session_termination_pending=False,
            runtime_synchronization_state=synchronization.value,
            last_ended_controller_owner_id=(
                ended_owner
                if ended_owner is not None
                else self._state.last_ended_controller_owner_id
            ),
            last_ended_sender_instance_id=(
                ended_instance
                if ended_instance is not None
                else self._state.last_ended_sender_instance_id
            ),
        )
        self._receiver_context = None
        result = self._make_result(
            disposition,
            result_index,
            diagnostic_code=(
                "RUNTIME_BOOT_CHANGE_SAFETY_FAILURE"
                if disposition is NegotiationDisposition.INTERNAL_ERROR
                else "BOOT_ID_CHANGED_SESSION_INVALIDATED"
                if had_active_session
                else "ROVER_BOOT_ID_CHANGED"
            ),
            runtime_dispatched=runtime_dispatched,
        )
        return ManagerAction(result, runtime_result=runtime_result)

    def dispatch_runtime_message(
        self,
        message: NormalizedLogicalMessage,
        *,
        now_ms: int,
    ) -> RuntimeDispatch:
        if not isinstance(message, NormalizedLogicalMessage):
            raise TypeError("message must be a NormalizedLogicalMessage")
        self._validate_now(now_ms)
        if self._receiver_context is None:
            return RuntimeDispatch(
                None,
                None,
                "invalid_session",
                "SESSION_NOT_ESTABLISHED",
            )
        if message.logical_message_type == LogicalMessageType.SESSION_END:
            return RuntimeDispatch(
                None,
                None,
                "invalid_message_type",
                "SESSION_END_REQUIRES_MANAGER_PATH",
            )
        sync_diagnostic = self._runtime_context_diagnostic()
        if sync_diagnostic is not None:
            return RuntimeDispatch(
                None,
                None,
                "runtime_not_safe",
                sync_diagnostic,
            )
        context = replace(
            self._receiver_context,
            current_monotonic_time_ms=now_ms,
        )
        adapter_result = self._adapter.adapt(message, context)
        runtime_result = None
        if adapter_result.disposition is AdapterDisposition.RUNTIME_INPUT_READY:
            runtime_result = self._runtime.step(adapter_result.runtime_input)
        self._receiver_context = context
        return RuntimeDispatch(
            adapter_result,
            runtime_result,
            None,
            None,
        )

    def dispatch_receiver_local(
        self,
        event: Event,
        *,
        now_ms: int,
    ) -> LocalRuntimeAction:
        if not isinstance(event, Event):
            raise TypeError("event must be an Event")
        self._validate_now(now_ms)
        if self._receiver_context is None:
            return LocalRuntimeAction(
                None,
                "invalid_session",
                "SESSION_NOT_ESTABLISHED",
            )
        sync_diagnostic = self._runtime_context_diagnostic()
        if sync_diagnostic is not None:
            return LocalRuntimeAction(
                None,
                "runtime_not_safe",
                sync_diagnostic,
            )
        runtime_result = self._runtime.step(
            RuntimeInput.local(event, now_ms=now_ms)
        )
        self._receiver_context = replace(
            self._receiver_context,
            current_monotonic_time_ms=now_ms,
        )
        return LocalRuntimeAction(runtime_result, None, None)

    def _reject(
        self,
        result_index: int,
        reason: str,
        diagnostic_code: str,
        *,
        requested_role: str | None = None,
        disposition: NegotiationDisposition = (
            NegotiationDisposition.SESSION_REJECTED
        ),
        runtime_dispatched: bool = False,
        adapter_result=None,
        runtime_result=None,
        synchronization: RuntimeSynchronizationState | None = None,
    ) -> ManagerAction:
        self._state = replace(
            self._state,
            negotiation_step_index=result_index,
            last_negotiation_disposition=disposition.value,
            session_termination_pending=False,
            runtime_synchronization_state=(
                self._state.runtime_synchronization_state
                if synchronization is None
                else synchronization.value
            ),
        )
        result = NegotiationResult(
            disposition=disposition,
            rejection_reason=reason,
            diagnostic_code=diagnostic_code,
            selected_protocol_version=None,
            accepted_session_id=None,
            requested_role=requested_role,
            accepted_role=None,
            rover_boot_id=self._state.current_rover_boot_id,
            controller_ownership=False,
            capability_profile_reference=(
                self._policy.capability_profile_reference
            ),
            deterministic_result_index=result_index,
            runtime_event_dispatched=runtime_dispatched,
            manager_state=self._state,
        )
        return ManagerAction(
            result,
            adapter_result=adapter_result,
            runtime_result=runtime_result,
        )

    def _make_result(
        self,
        disposition: NegotiationDisposition,
        result_index: int,
        *,
        diagnostic_code: str | None,
        runtime_dispatched: bool = False,
    ) -> NegotiationResult:
        return NegotiationResult(
            disposition=disposition,
            rejection_reason=None,
            diagnostic_code=diagnostic_code,
            selected_protocol_version=self._state.selected_protocol_version,
            accepted_session_id=self._state.active_session_id,
            requested_role=None,
            accepted_role=None,
            rover_boot_id=self._state.current_rover_boot_id,
            controller_ownership=self._state.controller_owned,
            capability_profile_reference=(
                self._policy.capability_profile_reference
            ),
            deterministic_result_index=result_index,
            runtime_event_dispatched=runtime_dispatched,
            manager_state=self._state,
        )

    def _candidate_structure_diagnostic(
        self,
        candidate: SessionCandidate,
        expected_request_index: int,
    ) -> str | None:
        versions = candidate.protocol_versions
        if (
            type(versions) is not tuple
            or not versions
            or any(type(value) is not str or not value for value in versions)
        ):
            return "PROTOCOL_VERSION_CANDIDATES_INVALID"
        if len(versions) != len(set(versions)):
            return "PROTOCOL_VERSION_CANDIDATES_DUPLICATED"
        if self._role_or_none(candidate.requested_role) is None:
            return "REQUESTED_ROLE_INVALID"
        string_values = (
            candidate.candidate_session_id,
            candidate.rover_boot_id,
            candidate.sender_id,
            candidate.sender_instance_id,
        )
        if any(type(value) is not str or not value for value in string_values):
            return "SESSION_CANDIDATE_IDENTITY_INVALID"
        if type(candidate.human_switch_confirmation) is not bool:
            return "HUMAN_CONFIRMATION_BOOLEAN_REQUIRED"
        if (
            type(candidate.request_index) is not int
            or candidate.request_index != expected_request_index
        ):
            return "NEGOTIATION_REQUEST_INDEX_INVALID"
        return None

    @staticmethod
    def _session_end_structure_diagnostic(
        request: SessionEndRequest,
        expected_request_index: int,
    ) -> str | None:
        string_values = (
            request.rover_boot_id,
            request.session_id,
            request.sender_id,
            request.sender_instance_id,
            request.message_id,
        )
        if any(type(value) is not str or not value for value in string_values):
            return "SESSION_END_IDENTITY_INVALID"
        if (
            type(request.sequence) is not int
            or type(request.freshness_reference_ms) is not int
            or type(request.ttl_ms) is not int
        ):
            return "SESSION_END_NUMERIC_FIELD_INVALID"
        if (
            type(request.request_index) is not int
            or request.request_index != expected_request_index
        ):
            return "NEGOTIATION_REQUEST_INDEX_INVALID"
        return None

    def _runtime_context_diagnostic(self) -> str | None:
        if self._state.active_session_id is None:
            if (
                self._state.controller_owned
                or self._state.active_controller_owner_id is not None
                or self._state.active_sender_instance_id is not None
                or self._receiver_context is not None
            ):
                return "MANAGER_UNBOUND_CONTEXT_INCONSISTENT"
            return None
        if (
            not self._state.controller_owned
            or self._receiver_context is None
            or self._state.active_controller_owner_id is None
            or self._state.active_sender_instance_id is None
            or self._runtime.state.session_id != self._state.active_session_id
            or self._receiver_context.active_session_id
            != self._state.active_session_id
            or self._receiver_context.active_controller_owner_id
            != self._state.active_controller_owner_id
            or self._receiver_context.current_rover_boot_id
            != self._state.current_rover_boot_id
        ):
            return "MANAGER_RUNTIME_CONTEXT_MISMATCH"
        return None

    def _runtime_safety_rejection(self) -> tuple[str | None, str | None]:
        state = self._runtime.state
        if (
            state.official_state in LATCHED_STATES
            or state.communication_loss_latched
            or state.fault_latched
            or state.emergency_stop_latched
        ):
            return "safety_latched", "RUNTIME_SAFETY_LATCH_ACTIVE"
        if (
            state.official_state not in NEGOTIATION_SAFE_STATES
            or state.armed
            or state.deadman_active
            or state.left_output != 0
            or state.right_output is not None
            or state.pto_effective
            or state.pto_requested
            or state.operation_id is not None
        ):
            return "runtime_not_safe", "RUNTIME_NOT_SAFE_FOR_SESSION"
        return None, None

    def _runtime_has_session_end_postcondition(self) -> bool:
        state = self._runtime.state
        return (
            not state.armed
            and not state.deadman_active
            and state.left_output == 0
            and state.right_output is None
            and not state.pto_effective
            and not state.pto_requested
            and state.operation_id is None
        )

    def _runtime_requires_safety_stop(self) -> bool:
        state = self._runtime.state
        return (
            state.armed
            or state.deadman_active
            or state.left_output != 0
            or state.pto_effective
            or state.pto_requested
            or state.operation_id is not None
        )

    def _build_receiver_context(self, now_ms: int) -> ReceiverContext:
        if (
            self._state.active_session_id is None
            or self._state.active_controller_owner_id is None
        ):
            raise RuntimeError("cannot build receiver context without a session")
        return ReceiverContext(
            expected_protocol_version=self._state.selected_protocol_version,
            current_rover_boot_id=self._state.current_rover_boot_id,
            active_session_id=self._state.active_session_id,
            active_controller_owner_id=(
                self._state.active_controller_owner_id
            ),
            current_monotonic_time_ms=now_ms,
            max_ttl_ms=self._policy.max_ttl_ms,
            max_safe_sequence=self._policy.max_safe_sequence,
            runtime_profile=self._policy.runtime_profile,
            max_speed=self._policy.max_speed,
            drive_available=self._policy.drive_available,
            turn_left_available=self._policy.turn_left_available,
            turn_right_available=self._policy.turn_right_available,
            pto_available=self._policy.pto_available,
            right_output_available=self._policy.right_output_available,
        )

    @staticmethod
    def _role_or_none(value: object) -> SessionRole | None:
        if isinstance(value, SessionRole):
            return value
        try:
            return SessionRole(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _role_label(cls, value: object) -> str | None:
        role = cls._role_or_none(value)
        return None if role is None else role.value

    @staticmethod
    def _validate_now(now_ms: int) -> None:
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative exact integer")

    @staticmethod
    def _validate_policy_alignment(
        runtime: RuntimeStateMachine,
        policy: ReceiverPolicy,
    ) -> None:
        config = runtime.config
        expected_capabilities = (
            True,
            False,
            False,
            config.pto_available,
            config.right_output_available,
        )
        actual_capabilities = (
            policy.drive_available,
            policy.turn_left_available,
            policy.turn_right_available,
            policy.pto_available,
            policy.right_output_available,
        )
        if (
            config.profile.value != policy.runtime_profile
            or config.max_command_ttl_ms != policy.max_ttl_ms
            or config.max_speed != policy.max_speed
            or actual_capabilities != expected_capabilities
            or config.real_motor_output_enabled
        ):
            raise ValueError("receiver policy and runtime config do not align")
