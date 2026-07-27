from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ....simulator.virtual_rover import RuntimeConfig, snapshot_dict
from ..runtime_adapter import (
    AdapterDisposition,
    LogicalMessageType,
)
from ..session_negotiation import (
    ReceiverPolicy,
    SessionEndRequest,
    VirtualSessionBridge,
)

from .model import (
    NormalizationDisposition,
    NormalizationResult,
    NormalizerPolicy,
    ReceivedLogicalObject,
)
from .normalizer import StrictLogicalMessageNormalizer


@dataclass(frozen=True, slots=True)
class BoundaryStep:
    boundary_step_index: int
    normalization_result: NormalizationResult
    negotiation_result: Any | None
    adapter_result: Any | None
    runtime_result: Any | None
    downstream_rejection_reason: str | None
    downstream_diagnostic_code: str | None
    defensive_zero_candidate: bool
    runtime_event_dispatched: bool
    internal_error: bool

    def report_dict(self) -> dict[str, Any]:
        return {
            "boundary_step_index": self.boundary_step_index,
            "normalization_result": self.normalization_result.report_dict(),
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
            "downstream_rejection_reason": self.downstream_rejection_reason,
            "downstream_diagnostic_code": self.downstream_diagnostic_code,
            "defensive_zero_candidate": self.defensive_zero_candidate,
            "runtime_event_dispatched": self.runtime_event_dispatched,
            "internal_error": self.internal_error,
        }


class VirtualInputBoundary:
    """Deterministic, software-only untrusted fixture integration boundary."""

    def __init__(
        self,
        *,
        normalizer_policy: NormalizerPolicy,
        supported_protocol_versions: tuple[str, ...],
        runtime_config: RuntimeConfig,
        receiver_policy: ReceiverPolicy,
        initial_used_session_ids: tuple[str, ...] = (),
    ) -> None:
        if type(normalizer_policy) is not NormalizerPolicy:
            raise TypeError("normalizer_policy must be a NormalizerPolicy")
        if supported_protocol_versions != (
            normalizer_policy.expected_protocol_version,
        ):
            raise ValueError(
                "supported protocol versions must match the v0 normalizer"
            )
        if normalizer_policy.max_safe_sequence != (
            receiver_policy.max_safe_sequence
        ):
            raise ValueError("normalizer and receiver sequence limits differ")
        if normalizer_policy.max_ttl_ms != receiver_policy.max_ttl_ms:
            raise ValueError("normalizer and receiver TTL limits differ")
        self._normalizer = StrictLogicalMessageNormalizer(normalizer_policy)
        self._bridge = VirtualSessionBridge(
            current_rover_boot_id=normalizer_policy.current_rover_boot_id,
            supported_protocol_versions=supported_protocol_versions,
            runtime_config=runtime_config,
            receiver_policy=receiver_policy,
            initial_used_session_ids=initial_used_session_ids,
        )
        self._steps: list[BoundaryStep] = []

    @property
    def normalizer(self) -> StrictLogicalMessageNormalizer:
        return self._normalizer

    @property
    def bridge(self) -> VirtualSessionBridge:
        return self._bridge

    @property
    def steps(self) -> tuple[BoundaryStep, ...]:
        return tuple(self._steps)

    def receive(
        self,
        received: ReceivedLogicalObject,
        *,
        now_ms: int,
    ) -> BoundaryStep:
        normalization = self._normalizer.normalize(received)
        negotiation_result = None
        adapter_result = None
        runtime_result = None
        downstream_reason = None
        downstream_diagnostic = None
        downstream_internal_error = False

        try:
            if (
                normalization.disposition
                is NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED
            ):
                bridge_step = self._bridge.process_hello(
                    normalization.session_candidate,
                    now_ms=now_ms,
                )
                negotiation_result = bridge_step.negotiation_result
                adapter_result = bridge_step.adapter_result
                runtime_result = bridge_step.runtime_result
                downstream_reason = bridge_step.rejection_reason
                downstream_diagnostic = bridge_step.diagnostic_code
            elif (
                normalization.disposition
                is NormalizationDisposition.MESSAGE_NORMALIZED
            ):
                message = normalization.normalized_message
                if (
                    message.logical_message_type
                    is LogicalMessageType.SESSION_END
                ):
                    bridge_step = self._end_session(message, now_ms=now_ms)
                    negotiation_result = bridge_step.negotiation_result
                else:
                    bridge_step = self._bridge.receive(message, now_ms=now_ms)
                adapter_result = bridge_step.adapter_result
                runtime_result = bridge_step.runtime_result
                downstream_reason = bridge_step.rejection_reason
                downstream_diagnostic = bridge_step.diagnostic_code
        except Exception:
            negotiation_result = None
            adapter_result = None
            runtime_result = None
            downstream_reason = "internal_error"
            downstream_diagnostic = "INPUT_BOUNDARY_INTERNAL_ERROR"
            downstream_internal_error = True

        runtime_dispatched = runtime_result is not None
        defensive = self._is_defensive_candidate(
            normalization,
            adapter_result,
            runtime_result,
        )
        step = BoundaryStep(
            boundary_step_index=len(self._steps) + 1,
            normalization_result=normalization,
            negotiation_result=negotiation_result,
            adapter_result=adapter_result,
            runtime_result=runtime_result,
            downstream_rejection_reason=downstream_reason,
            downstream_diagnostic_code=downstream_diagnostic,
            defensive_zero_candidate=defensive,
            runtime_event_dispatched=runtime_dispatched,
            internal_error=(
                normalization.internal_error or downstream_internal_error
            ),
        )
        self._steps.append(step)
        return step

    def complete_boot(self, *, now_ms: int):
        return self._bridge.complete_boot(now_ms=now_ms)

    def communication_restored(self, *, now_ms: int):
        return self._bridge.communication_restored(now_ms=now_ms)

    def assert_deadman(self, *, now_ms: int):
        return self._bridge.assert_deadman(now_ms=now_ms)

    def release_deadman(self, *, now_ms: int):
        return self._bridge.release_deadman(now_ms=now_ms)

    def update_rover_boot_id(
        self,
        rover_boot_id: object,
        *,
        now_ms: int,
        request_index: object,
    ):
        step = self._bridge.update_rover_boot_id(
            rover_boot_id,
            now_ms=now_ms,
            request_index=request_index,
        )
        current = self._bridge.state.current_rover_boot_id
        if current != self._normalizer.policy.current_rover_boot_id:
            self._normalizer.update_current_rover_boot_id(current)
        return step

    def report_dict(self) -> dict[str, Any]:
        context = self._bridge.receiver_context
        return {
            "report_version": 1,
            "protocol_version": "v0",
            "boundary": "strict_logical_message_virtual_input",
            "real_motor_output_enabled": False,
            "defensive_zero_executor_enabled": False,
            "manager_state": self._bridge.state.report_dict(),
            "receiver_context_present": context is not None,
            "steps": [step.report_dict() for step in self._steps],
            "final_runtime_state": snapshot_dict(self._bridge.runtime.state),
        }

    def render_report(self) -> str:
        return render_boundary_report(self.report_dict())

    def _end_session(self, message, *, now_ms: int):
        state = self._bridge.state
        request = SessionEndRequest(
            rover_boot_id=message.rover_boot_id,
            session_id=message.session_id,
            sender_id=message.sender_id,
            sender_instance_id=state.active_sender_instance_id or "",
            message_id=message.message_id,
            sequence=message.sequence,
            freshness_reference_ms=message.freshness_reference_ms,
            ttl_ms=message.ttl_ms,
            request_index=state.negotiation_step_index + 1,
        )
        return self._bridge.end_session(request, now_ms=now_ms)

    @staticmethod
    def _is_defensive_candidate(
        normalization: NormalizationResult,
        adapter_result,
        runtime_result,
    ) -> bool:
        if normalization.defensive_zero_candidate:
            return True
        if (
            not normalization.identification_gate_passed
            or normalization.candidate_intent is None
        ):
            return False
        if adapter_result is None:
            return True
        if adapter_result.disposition is not AdapterDisposition.RUNTIME_INPUT_READY:
            return True
        return runtime_result is None or not runtime_result.accepted


def render_boundary_report(report: dict[str, Any]) -> str:
    return json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
