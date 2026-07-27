from __future__ import annotations

from ....simulator.virtual_rover import (
    RoverState,
    RuntimeStateMachine,
)
from ..message_normalizer import (
    BoundaryStep,
    CandidateIntent,
    NormalizationDisposition,
)
from ..runtime_adapter import AdapterDisposition

from .model import (
    DefensiveZeroDisposition,
    DefensiveZeroResult,
    DefensiveZeroSourceStage,
)


_ACTIVE_STATE_LABELS = frozenset(
    {RoverState.DRIVE_ACTIVE.value, RoverState.PTO_ACTIVE.value}
)


class DefensiveZeroExecutor:
    """Evaluate one normalizer boundary step without formal command reuse."""

    def __init__(self, runtime: RuntimeStateMachine) -> None:
        if type(runtime) is not RuntimeStateMachine:
            raise TypeError("runtime must be a RuntimeStateMachine")
        self._runtime = runtime
        self._step_index = 0
        self._processed: dict[int, DefensiveZeroResult] = {}

    @property
    def step_index(self) -> int:
        return self._step_index

    def evaluate(
        self,
        boundary_step: BoundaryStep,
        *,
        now_ms: int,
    ) -> DefensiveZeroResult:
        boundary_index = (
            boundary_step.boundary_step_index
            if type(boundary_step) is BoundaryStep
            else None
        )
        if boundary_index in self._processed:
            return self._processed[boundary_index]

        self._step_index += 1
        executor_index = self._step_index
        try:
            if type(boundary_step) is not BoundaryStep:
                raise TypeError("boundary_step must be a BoundaryStep")
            if type(boundary_index) is not int or boundary_index <= 0:
                raise ValueError("boundary step index must be positive")
            if boundary_step.internal_error:
                result = self._internal_error_result(
                    boundary_step,
                    now_ms=now_ms,
                    executor_index=executor_index,
                )
            else:
                result = self._evaluate(
                    boundary_step,
                    now_ms=now_ms,
                    executor_index=executor_index,
                )
            self._processed[boundary_index] = result
            return result
        except Exception:
            result = self._internal_error_result(
                None,
                now_ms=now_ms,
                executor_index=executor_index,
            )
            if boundary_index is not None:
                self._processed[boundary_index] = result
            return result

    def _evaluate(
        self,
        step: BoundaryStep,
        *,
        now_ms: int,
        executor_index: int,
    ) -> DefensiveZeroResult:
        normalization = step.normalization_result
        intent = normalization.candidate_intent
        before_state = self._runtime.state
        runtime_before = before_state.step_index
        latches_before = self._latches(before_state)
        runtime_result = step.runtime_result

        if (
            intent is None
            or not normalization.identification_gate_passed
        ):
            return self._result(
                DefensiveZeroDisposition.NOT_APPLICABLE,
                intent,
                DefensiveZeroSourceStage.NONE,
                normalization.rejection_reason,
                normalization.diagnostic_code,
                None,
                runtime_before,
                False,
                latches_before,
                executor_index,
            )

        if runtime_result is not None and runtime_result.accepted:
            return self._result(
                DefensiveZeroDisposition.FORMAL_COMMAND_APPLIED,
                intent,
                DefensiveZeroSourceStage.FORMAL_RUNTIME,
                runtime_result.rejection_reason,
                runtime_result.diagnostic_code,
                runtime_result,
                runtime_before,
                self._runtime_invalidated_operation(runtime_result),
                latches_before,
                executor_index,
                formal_acceptance=True,
                sequence_updated=runtime_result.sequence_accepted,
            )

        if (
            runtime_result is not None
            and runtime_result.safety_action == "ZERO_ALL_OUTPUTS"
        ):
            return self._result(
                DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
                intent,
                DefensiveZeroSourceStage.RUNTIME,
                runtime_result.rejection_reason,
                runtime_result.diagnostic_code,
                runtime_result,
                runtime_before,
                self._runtime_invalidated_operation(runtime_result),
                latches_before,
                executor_index,
            )

        if not step.defensive_zero_candidate:
            return self._result(
                DefensiveZeroDisposition.NOT_APPLICABLE,
                intent,
                DefensiveZeroSourceStage.NONE,
                None,
                None,
                runtime_result,
                runtime_before,
                False,
                latches_before,
                executor_index,
            )

        source_stage, reason, diagnostic = self._source_metadata(step)
        operation_was_present = before_state.operation_id is not None
        local_result = self._runtime.apply_defensive_zero(
            now_ms=now_ms,
            candidate_intent=intent.value,
            rejection_reason=reason,
            diagnostic_code=diagnostic,
        )
        if local_result.internal_failure:
            disposition = DefensiveZeroDisposition.INTERNAL_ERROR
        else:
            disposition = DefensiveZeroDisposition.EXECUTED
        return self._result(
            disposition,
            intent,
            source_stage,
            reason,
            diagnostic,
            local_result,
            runtime_before,
            operation_was_present
            and self._runtime.state.operation_id is None,
            latches_before,
            executor_index,
            internal_error=local_result.internal_failure,
        )

    def _internal_error_result(
        self,
        step: BoundaryStep | None,
        *,
        now_ms: int,
        executor_index: int,
    ) -> DefensiveZeroResult:
        before_state = self._runtime.state
        runtime_before = before_state.step_index
        latches_before = self._latches(before_state)
        intent = (
            step.normalization_result.candidate_intent
            if step is not None
            else None
        )
        intent_label = intent.value if intent is not None else ""
        operation_was_present = before_state.operation_id is not None
        local_result = self._runtime.apply_defensive_zero(
            now_ms=now_ms,
            candidate_intent=intent_label,
            rejection_reason="internal_error",
            diagnostic_code="DEFENSIVE_ZERO_EXECUTOR_INTERNAL_ERROR",
        )
        return self._result(
            DefensiveZeroDisposition.INTERNAL_ERROR,
            intent,
            DefensiveZeroSourceStage.NONE,
            "internal_error",
            "DEFENSIVE_ZERO_EXECUTOR_INTERNAL_ERROR",
            local_result,
            runtime_before,
            operation_was_present
            and self._runtime.state.operation_id is None,
            latches_before,
            executor_index,
            internal_error=True,
        )

    def _result(
        self,
        disposition: DefensiveZeroDisposition,
        intent: CandidateIntent | None,
        source_stage: DefensiveZeroSourceStage,
        reason: str | None,
        diagnostic: str | None,
        runtime_result,
        runtime_before: int,
        operation_invalidated: bool,
        latches_before: tuple[bool, bool, bool],
        executor_index: int,
        *,
        formal_acceptance: bool = False,
        sequence_updated: bool = False,
        internal_error: bool = False,
    ) -> DefensiveZeroResult:
        state = self._runtime.state
        return DefensiveZeroResult(
            disposition=disposition,
            candidate_intent=intent,
            source_stage=source_stage,
            source_rejection_reason=reason,
            source_diagnostic_code=diagnostic,
            runtime_result=runtime_result,
            runtime_step_before=runtime_before,
            runtime_step_after=state.step_index,
            output_zero_confirmed=self._outputs_zero(),
            operation_invalidated=operation_invalidated,
            latch_preserved=latches_before == self._latches(state),
            formal_acceptance=formal_acceptance,
            sequence_updated=sequence_updated,
            executor_step_index=executor_index,
            internal_error=internal_error,
        )

    @staticmethod
    def _source_metadata(
        step: BoundaryStep,
    ) -> tuple[DefensiveZeroSourceStage, str, str]:
        normalization = step.normalization_result
        if normalization.disposition is NormalizationDisposition.REJECTED:
            return (
                DefensiveZeroSourceStage.NORMALIZER,
                normalization.rejection_reason or "invalid_payload",
                normalization.diagnostic_code
                or "NORMALIZER_DEFENSIVE_ZERO_CANDIDATE",
            )
        adapter = step.adapter_result
        if (
            adapter is not None
            and adapter.disposition is AdapterDisposition.REJECTED
        ):
            return (
                DefensiveZeroSourceStage.ADAPTER,
                adapter.rejection_reason or "invalid_payload",
                adapter.diagnostic_code
                or "ADAPTER_DEFENSIVE_ZERO_CANDIDATE",
            )
        return (
            DefensiveZeroSourceStage.ADAPTER,
            step.downstream_rejection_reason or "invalid_session",
            step.downstream_diagnostic_code
            or "DOWNSTREAM_DEFENSIVE_ZERO_CANDIDATE",
        )

    def _outputs_zero(self) -> bool:
        state = self._runtime.state
        return (
            state.requested_speed == 0
            and state.effective_speed == 0
            and state.left_output == 0
            and state.right_output is None
            and not state.pto_requested
            and not state.pto_effective
        )

    @staticmethod
    def _latches(state) -> tuple[bool, bool, bool]:
        return (
            state.communication_loss_latched,
            state.fault_latched,
            state.emergency_stop_latched,
        )

    @staticmethod
    def _runtime_invalidated_operation(runtime_result) -> bool:
        return (
            runtime_result.previous_state in _ACTIVE_STATE_LABELS
            and runtime_result.operation_id is None
        )
