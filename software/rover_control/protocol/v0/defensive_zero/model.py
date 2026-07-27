from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ....simulator.virtual_rover import StepResult
from ..message_normalizer import CandidateIntent


class DefensiveZeroDisposition(str, Enum):
    EXECUTED = "EXECUTED"
    ALREADY_APPLIED_BY_RUNTIME = "ALREADY_APPLIED_BY_RUNTIME"
    FORMAL_COMMAND_APPLIED = "FORMAL_COMMAND_APPLIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DefensiveZeroSourceStage(str, Enum):
    NORMALIZER = "NORMALIZER"
    ADAPTER = "ADAPTER"
    RUNTIME = "RUNTIME"
    FORMAL_RUNTIME = "FORMAL_RUNTIME"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class DefensiveZeroResult:
    disposition: DefensiveZeroDisposition
    candidate_intent: CandidateIntent | None
    source_stage: DefensiveZeroSourceStage
    source_rejection_reason: str | None
    source_diagnostic_code: str | None
    runtime_result: StepResult | None
    runtime_step_before: int
    runtime_step_after: int
    output_zero_confirmed: bool
    operation_invalidated: bool
    latch_preserved: bool
    formal_acceptance: bool
    sequence_updated: bool
    executor_step_index: int
    internal_error: bool = False

    def report_dict(self) -> dict[str, Any]:
        return {
            "executor_step_index": self.executor_step_index,
            "disposition": self.disposition.value,
            "candidate_intent": (
                None
                if self.candidate_intent is None
                else self.candidate_intent.value
            ),
            "source_stage": self.source_stage.value,
            "source_rejection_reason": self.source_rejection_reason,
            "source_diagnostic_code": self.source_diagnostic_code,
            "runtime_result": (
                None
                if self.runtime_result is None
                else self.runtime_result.report_dict()
            ),
            "runtime_step_before": self.runtime_step_before,
            "runtime_step_after": self.runtime_step_after,
            "output_zero_confirmed": self.output_zero_confirmed,
            "operation_invalidated": self.operation_invalidated,
            "latch_preserved": self.latch_preserved,
            "formal_acceptance": self.formal_acceptance,
            "sequence_updated": self.sequence_updated,
            "internal_error": self.internal_error,
        }
