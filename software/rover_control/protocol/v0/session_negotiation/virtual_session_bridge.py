from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ....simulator.virtual_rover import (
    Event,
    RuntimeConfig,
    RuntimeStateMachine,
    snapshot_dict,
)
from ..runtime_adapter import NormalizedLogicalMessage

from .manager import SessionNegotiationManager
from .model import (
    ManagerAction,
    ReceiverPolicy,
    SessionCandidate,
    SessionEndRequest,
)


@dataclass(frozen=True, slots=True)
class SessionBridgeStep:
    bridge_step_index: int
    input_source: str
    negotiation_result: Any | None
    adapter_result: Any | None
    runtime_result: Any | None
    rejection_reason: str | None
    diagnostic_code: str | None

    def report_dict(self) -> dict[str, Any]:
        return {
            "bridge_step_index": self.bridge_step_index,
            "input_source": self.input_source,
            "negotiation_result": (
                None
                if self.negotiation_result is None
                else self.negotiation_result.report_dict()
            ),
            "adapter_result": (
                None
                if self.adapter_result is None
                else self.adapter_result.report_dict()
            ),
            "runtime_result": (
                None
                if self.runtime_result is None
                else self.runtime_result.report_dict()
            ),
            "rejection_reason": self.rejection_reason,
            "diagnostic_code": self.diagnostic_code,
        }


class VirtualSessionBridge:
    """Software-only deterministic bridge for session and runtime integration."""

    def __init__(
        self,
        *,
        current_rover_boot_id: str,
        supported_protocol_versions: tuple[str, ...],
        runtime_config: RuntimeConfig,
        receiver_policy: ReceiverPolicy,
        initial_used_session_ids: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(runtime_config, RuntimeConfig):
            raise TypeError("runtime_config must be a RuntimeConfig")
        runtime = RuntimeStateMachine(runtime_config)
        self._manager = SessionNegotiationManager(
            current_rover_boot_id=current_rover_boot_id,
            supported_protocol_versions=supported_protocol_versions,
            runtime=runtime,
            receiver_policy=receiver_policy,
            initial_used_session_ids=initial_used_session_ids,
        )
        self._steps: list[SessionBridgeStep] = []

    @property
    def manager(self) -> SessionNegotiationManager:
        return self._manager

    @property
    def runtime(self) -> RuntimeStateMachine:
        return self._manager.runtime

    @property
    def state(self):
        return self._manager.state

    @property
    def receiver_context(self):
        return self._manager.receiver_context

    @property
    def steps(self) -> tuple[SessionBridgeStep, ...]:
        return tuple(self._steps)

    def process_hello(
        self,
        candidate: SessionCandidate,
        *,
        now_ms: int,
    ) -> SessionBridgeStep:
        action = self._manager.process_hello(candidate, now_ms=now_ms)
        return self._record_manager_action("SESSION_HELLO", action)

    def end_session(
        self,
        request: SessionEndRequest,
        *,
        now_ms: int,
    ) -> SessionBridgeStep:
        action = self._manager.end_session(request, now_ms=now_ms)
        return self._record_manager_action("SESSION_END", action)

    def update_rover_boot_id(
        self,
        new_rover_boot_id: object,
        *,
        now_ms: int,
        request_index: object,
    ) -> SessionBridgeStep:
        action = self._manager.update_rover_boot_id(
            new_rover_boot_id,
            now_ms=now_ms,
            request_index=request_index,
        )
        return self._record_manager_action("ROVER_BOOT_ID_UPDATE", action)

    def receive(
        self,
        message: NormalizedLogicalMessage,
        *,
        now_ms: int,
    ) -> SessionBridgeStep:
        dispatch = self._manager.dispatch_runtime_message(
            message,
            now_ms=now_ms,
        )
        return self._record(
            "NORMALIZED_LOGICAL_MESSAGE",
            negotiation_result=None,
            adapter_result=dispatch.adapter_result,
            runtime_result=dispatch.runtime_result,
            rejection_reason=dispatch.rejection_reason,
            diagnostic_code=dispatch.diagnostic_code,
        )

    def complete_boot(self, *, now_ms: int) -> SessionBridgeStep:
        return self._receiver_local(Event.BOOT_COMPLETE, now_ms=now_ms)

    def communication_restored(self, *, now_ms: int) -> SessionBridgeStep:
        return self._receiver_local(
            Event.COMMUNICATION_RESTORED,
            now_ms=now_ms,
        )

    def assert_deadman(self, *, now_ms: int) -> SessionBridgeStep:
        return self._receiver_local(Event.DEADMAN_ASSERT, now_ms=now_ms)

    def release_deadman(self, *, now_ms: int) -> SessionBridgeStep:
        return self._receiver_local(Event.DEADMAN_RELEASED, now_ms=now_ms)

    def report_dict(self) -> dict[str, Any]:
        context = self._manager.receiver_context
        return {
            "report_version": 1,
            "protocol_version": "v0",
            "bridge": "deterministic_virtual_session_receiver",
            "real_motor_output_enabled": False,
            "manager_state": self._manager.state.report_dict(),
            "receiver_context": (
                None
                if context is None
                else {
                    "expected_protocol_version": (
                        context.expected_protocol_version
                    ),
                    "current_rover_boot_id": context.current_rover_boot_id,
                    "active_session_id": context.active_session_id,
                    "active_controller_owner_id": (
                        context.active_controller_owner_id
                    ),
                    "current_monotonic_time_ms": (
                        context.current_monotonic_time_ms
                    ),
                    "max_ttl_ms": context.max_ttl_ms,
                    "max_safe_sequence": context.max_safe_sequence,
                    "runtime_profile": context.runtime_profile,
                    "max_speed": context.max_speed,
                    "drive_available": context.drive_available,
                    "turn_left_available": context.turn_left_available,
                    "turn_right_available": context.turn_right_available,
                    "pto_available": context.pto_available,
                    "right_output_available": (
                        context.right_output_available
                    ),
                }
            ),
            "steps": [step.report_dict() for step in self._steps],
            "final_runtime_state": snapshot_dict(self._manager.runtime.state),
        }

    def render_report(self) -> str:
        return render_session_report(self.report_dict())

    def _receiver_local(
        self,
        event: Event,
        *,
        now_ms: int,
    ) -> SessionBridgeStep:
        action = self._manager.dispatch_receiver_local(event, now_ms=now_ms)
        return self._record(
            "RECEIVER_LOCAL",
            negotiation_result=None,
            adapter_result=None,
            runtime_result=action.runtime_result,
            rejection_reason=action.rejection_reason,
            diagnostic_code=action.diagnostic_code,
        )

    def _record_manager_action(
        self,
        source: str,
        action: ManagerAction,
    ) -> SessionBridgeStep:
        return self._record(
            source,
            negotiation_result=action.result,
            adapter_result=action.adapter_result,
            runtime_result=action.runtime_result,
            rejection_reason=action.result.rejection_reason,
            diagnostic_code=action.result.diagnostic_code,
        )

    def _record(
        self,
        input_source: str,
        *,
        negotiation_result,
        adapter_result,
        runtime_result,
        rejection_reason,
        diagnostic_code,
    ) -> SessionBridgeStep:
        step = SessionBridgeStep(
            bridge_step_index=len(self._steps) + 1,
            input_source=input_source,
            negotiation_result=negotiation_result,
            adapter_result=adapter_result,
            runtime_result=runtime_result,
            rejection_reason=rejection_reason,
            diagnostic_code=diagnostic_code,
        )
        self._steps.append(step)
        return step


def render_session_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
