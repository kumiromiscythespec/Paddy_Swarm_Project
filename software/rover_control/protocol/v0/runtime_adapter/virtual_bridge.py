from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Any

from ....simulator.virtual_rover import (
    Event,
    Profile,
    RuntimeConfig,
    RuntimeInput,
    RuntimeStateMachine,
    StepResult,
    snapshot_dict,
)

from .adapter import RuntimeInputAdapter
from .model import (
    AdapterDisposition,
    AdapterResult,
    NormalizedLogicalMessage,
    ReceiverContext,
)


@dataclass(frozen=True, slots=True)
class BridgeStep:
    bridge_step_index: int
    input_source: str
    adapter_result: AdapterResult | None
    runtime_result: StepResult | None

    def report_dict(self) -> dict[str, Any]:
        return {
            "bridge_step_index": self.bridge_step_index,
            "input_source": self.input_source,
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
        }


class VirtualReceiverBridge:
    """In-process bridge for normalized messages and receiver-local inputs."""

    def __init__(
        self,
        context: ReceiverContext,
        *,
        runtime_config: RuntimeConfig | None = None,
    ) -> None:
        if not isinstance(context, ReceiverContext):
            raise TypeError("context must be a ReceiverContext")
        config = runtime_config or RuntimeConfig(
            profile=Profile(context.runtime_profile),
            max_command_ttl_ms=context.max_ttl_ms,
            max_speed=context.max_speed,
            session_id=context.active_session_id,
            real_motor_output_enabled=False,
        )
        self._validate_config_alignment(context, config)
        self._context = context
        self._adapter = RuntimeInputAdapter()
        self._machine = RuntimeStateMachine(config)
        self._steps: list[BridgeStep] = []

    @property
    def context(self) -> ReceiverContext:
        return self._context

    @property
    def state(self):
        return self._machine.state

    @property
    def adapter_step_index(self) -> int:
        return self._adapter.step_index

    @property
    def runtime_step_index(self) -> int:
        return self._machine.state.step_index

    @property
    def steps(self) -> tuple[BridgeStep, ...]:
        return tuple(self._steps)

    def receive(
        self,
        message: NormalizedLogicalMessage,
        *,
        now_ms: int | None = None,
    ) -> BridgeStep:
        context = self._context_at(now_ms)
        previous_adapter_step = self._adapter.step_index
        try:
            adapter_result = self._adapter.adapt(message, context)
        except Exception:
            adapter_result = self._adapter.internal_error_result(
                message,
                previous_step_index=previous_adapter_step,
            )
        runtime_result = None
        if adapter_result.disposition is AdapterDisposition.RUNTIME_INPUT_READY:
            runtime_result = self._machine.step(adapter_result.runtime_input)
        self._context = context
        return self._record(
            "normalized_logical_message",
            adapter_result,
            runtime_result,
        )

    def complete_boot(self, *, now_ms: int) -> BridgeStep:
        return self._local(Event.BOOT_COMPLETE, now_ms=now_ms)

    def communication_restored(self, *, now_ms: int) -> BridgeStep:
        return self._local(Event.COMMUNICATION_RESTORED, now_ms=now_ms)

    def assert_deadman(self, *, now_ms: int) -> BridgeStep:
        return self._local(Event.DEADMAN_ASSERT, now_ms=now_ms)

    def release_deadman(self, *, now_ms: int) -> BridgeStep:
        return self._local(Event.DEADMAN_RELEASED, now_ms=now_ms)

    def tick(self, *, now_ms: int) -> BridgeStep:
        return self._local(Event.TICK, now_ms=now_ms)

    def report_dict(self) -> dict[str, Any]:
        return {
            "report_version": 1,
            "protocol_version": self._context.expected_protocol_version,
            "bridge": "deterministic_virtual_receiver",
            "runtime_profile": self._context.runtime_profile,
            "rover_boot_id": self._context.current_rover_boot_id,
            "active_session_id": self._context.active_session_id,
            "real_motor_output_enabled": False,
            "steps": [step.report_dict() for step in self._steps],
            "final_state": snapshot_dict(self._machine.state),
        }

    def render_report(self) -> str:
        return render_bridge_report(self.report_dict())

    def _local(
        self,
        event: Event,
        *,
        now_ms: int,
    ) -> BridgeStep:
        context = self._context_at(now_ms)
        runtime_result = self._machine.step(
            RuntimeInput.local(event, now_ms=now_ms)
        )
        self._context = context
        return self._record("receiver_local", None, runtime_result)

    def _record(
        self,
        input_source: str,
        adapter_result: AdapterResult | None,
        runtime_result: StepResult | None,
    ) -> BridgeStep:
        step = BridgeStep(
            bridge_step_index=len(self._steps) + 1,
            input_source=input_source,
            adapter_result=adapter_result,
            runtime_result=runtime_result,
        )
        self._steps.append(step)
        return step

    def _context_at(self, now_ms: int | None) -> ReceiverContext:
        if now_ms is None:
            return self._context
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative exact integer")
        if now_ms < self._context.current_monotonic_time_ms:
            raise ValueError("receiver monotonic time cannot move backwards")
        return replace(self._context, current_monotonic_time_ms=now_ms)

    @staticmethod
    def _validate_config_alignment(
        context: ReceiverContext,
        config: RuntimeConfig,
    ) -> None:
        if config.session_id != context.active_session_id:
            raise ValueError("runtime and receiver session IDs must match")
        if config.profile.value != context.runtime_profile:
            raise ValueError("runtime and receiver profiles must match")
        if config.max_command_ttl_ms != context.max_ttl_ms:
            raise ValueError("runtime and receiver TTL limits must match")
        if config.max_speed != context.max_speed:
            raise ValueError("runtime and receiver speed limits must match")
        if config.real_motor_output_enabled:
            raise ValueError("real motor output must remain disabled")
        expected_capabilities = (
            True,
            False,
            False,
            config.pto_available,
            config.right_output_available,
        )
        actual_capabilities = (
            context.drive_available,
            context.turn_left_available,
            context.turn_right_available,
            context.pto_available,
            context.right_output_available,
        )
        if actual_capabilities != expected_capabilities:
            raise ValueError("runtime and receiver capabilities must match")


def render_bridge_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
