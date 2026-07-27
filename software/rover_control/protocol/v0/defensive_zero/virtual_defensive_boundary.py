from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ....simulator.virtual_rover import RuntimeConfig, snapshot_dict
from ..message_normalizer import (
    BoundaryStep,
    NormalizerPolicy,
    ReceivedLogicalObject,
    VirtualInputBoundary,
)
from ..session_negotiation import ReceiverPolicy

from .executor import DefensiveZeroExecutor
from .model import DefensiveZeroDisposition, DefensiveZeroResult


@dataclass(frozen=True, slots=True)
class DefensiveBoundaryStep:
    defensive_boundary_step_index: int
    boundary_step: BoundaryStep
    defensive_zero_result: DefensiveZeroResult
    formal_command_accepted: bool
    defensive_zero_executed: bool
    runtime_native_zero_used: bool
    emergency_stop_latched_formally: bool
    outputs_zero: bool
    operation_id_present: bool
    last_accepted_sequence: int | None
    last_seen_sequence: int | None

    def report_dict(self) -> dict[str, Any]:
        normalization = self.boundary_step.normalization_result
        negotiation = self.boundary_step.negotiation_result
        adapter = self.boundary_step.adapter_result
        formal_runtime = self.boundary_step.runtime_result
        defensive_runtime = (
            self.defensive_zero_result.runtime_result
            if self.defensive_zero_result.disposition
            in {
                DefensiveZeroDisposition.EXECUTED,
                DefensiveZeroDisposition.INTERNAL_ERROR,
            }
            else None
        )
        return {
            "defensive_boundary_step_index": (
                self.defensive_boundary_step_index
            ),
            "normalization_result": normalization.report_dict(),
            "negotiation_result": (
                None if negotiation is None else negotiation.report_dict()
            ),
            "adapter_result": (
                None if adapter is None else adapter.report_dict()
            ),
            "formal_runtime_result": (
                None
                if formal_runtime is None
                else formal_runtime.report_dict()
            ),
            "defensive_runtime_result": (
                None
                if defensive_runtime is None
                else defensive_runtime.report_dict()
            ),
            "defensive_zero_result": (
                self.defensive_zero_result.report_dict()
            ),
            "formal_command_accepted": self.formal_command_accepted,
            "defensive_zero_executed": self.defensive_zero_executed,
            "runtime_native_zero_used": self.runtime_native_zero_used,
            "emergency_stop_latched_formally": (
                self.emergency_stop_latched_formally
            ),
            "outputs_zero": self.outputs_zero,
            "operation_id_present": self.operation_id_present,
            "last_accepted_sequence": self.last_accepted_sequence,
            "last_seen_sequence": self.last_seen_sequence,
        }


class VirtualDefensiveBoundary:
    """Software-only wrapper that executes classified defensive zeroes."""

    def __init__(
        self,
        *,
        normalizer_policy: NormalizerPolicy,
        supported_protocol_versions: tuple[str, ...],
        runtime_config: RuntimeConfig,
        receiver_policy: ReceiverPolicy,
        initial_used_session_ids: tuple[str, ...] = (),
    ) -> None:
        self._input_boundary = VirtualInputBoundary(
            normalizer_policy=normalizer_policy,
            supported_protocol_versions=supported_protocol_versions,
            runtime_config=runtime_config,
            receiver_policy=receiver_policy,
            initial_used_session_ids=initial_used_session_ids,
        )
        self._executor = DefensiveZeroExecutor(
            self._input_boundary.bridge.runtime
        )
        self._steps: list[DefensiveBoundaryStep] = []

    @property
    def input_boundary(self) -> VirtualInputBoundary:
        return self._input_boundary

    @property
    def bridge(self):
        return self._input_boundary.bridge

    @property
    def executor(self) -> DefensiveZeroExecutor:
        return self._executor

    @property
    def steps(self) -> tuple[DefensiveBoundaryStep, ...]:
        return tuple(self._steps)

    def receive(
        self,
        received: ReceivedLogicalObject,
        *,
        now_ms: int,
    ) -> DefensiveBoundaryStep:
        boundary_step = self._input_boundary.receive(
            received,
            now_ms=now_ms,
        )
        result = self._executor.evaluate(
            boundary_step,
            now_ms=now_ms,
        )
        runtime = self.bridge.runtime
        state = runtime.state
        formal_runtime = boundary_step.runtime_result
        formal_accepted = (
            formal_runtime is not None and formal_runtime.accepted
        )
        formally_latched_estop = (
            formal_accepted
            and formal_runtime is not None
            and formal_runtime.event == "EMERGENCY_STOP"
            and state.emergency_stop_latched
        )
        step = DefensiveBoundaryStep(
            defensive_boundary_step_index=len(self._steps) + 1,
            boundary_step=boundary_step,
            defensive_zero_result=result,
            formal_command_accepted=formal_accepted,
            defensive_zero_executed=(
                result.disposition is DefensiveZeroDisposition.EXECUTED
            ),
            runtime_native_zero_used=(
                result.disposition
                is DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME
            ),
            emergency_stop_latched_formally=formally_latched_estop,
            outputs_zero=self._outputs_zero(),
            operation_id_present=state.operation_id is not None,
            last_accepted_sequence=state.last_accepted_sequence,
            last_seen_sequence=state.last_seen_sequence,
        )
        self._steps.append(step)
        return step

    def reevaluate(
        self,
        defensive_boundary_step_index: int,
    ) -> DefensiveZeroResult:
        if (
            type(defensive_boundary_step_index) is not int
            or not 1
            <= defensive_boundary_step_index
            <= len(self._steps)
        ):
            raise ValueError("defensive boundary step index is invalid")
        step = self._steps[defensive_boundary_step_index - 1]
        return self._executor.evaluate(
            step.boundary_step,
            now_ms=self.bridge.runtime.state.monotonic_time_ms,
        )

    def complete_boot(self, *, now_ms: int):
        return self._input_boundary.complete_boot(now_ms=now_ms)

    def communication_restored(self, *, now_ms: int):
        return self._input_boundary.communication_restored(now_ms=now_ms)

    def assert_deadman(self, *, now_ms: int):
        return self._input_boundary.assert_deadman(now_ms=now_ms)

    def release_deadman(self, *, now_ms: int):
        return self._input_boundary.release_deadman(now_ms=now_ms)

    def update_rover_boot_id(
        self,
        rover_boot_id: object,
        *,
        now_ms: int,
        request_index: object,
    ):
        return self._input_boundary.update_rover_boot_id(
            rover_boot_id,
            now_ms=now_ms,
            request_index=request_index,
        )

    def report_dict(self) -> dict[str, Any]:
        state = self.bridge.runtime.state
        final_state = snapshot_dict(state)
        final_state["last_seen_sequence"] = state.last_seen_sequence
        final_state["watchdog_deadline_ms"] = state.watchdog_deadline_ms
        return {
            "report_version": 1,
            "protocol_version": "v0",
            "boundary": "virtual_defensive_zero_boundary",
            "real_motor_output_enabled": False,
            "defensive_zero_executor_enabled": True,
            "formal_and_defensive_paths_separated": True,
            "steps": [step.report_dict() for step in self._steps],
            "final_runtime_state": final_state,
        }

    def render_report(self) -> str:
        return render_defensive_report(self.report_dict())

    def _outputs_zero(self) -> bool:
        state = self.bridge.runtime.state
        return (
            state.requested_speed == 0
            and state.effective_speed == 0
            and state.left_output == 0
            and state.right_output is None
            and not state.pto_requested
            and not state.pto_effective
        )


def render_defensive_report(report: dict[str, Any]) -> str:
    return json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
