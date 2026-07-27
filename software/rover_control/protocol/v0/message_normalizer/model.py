from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..runtime_adapter import NormalizedLogicalMessage
from ..session_negotiation import SessionCandidate


class NormalizationDisposition(str, Enum):
    MESSAGE_NORMALIZED = "MESSAGE_NORMALIZED"
    SESSION_CANDIDATE_NORMALIZED = "SESSION_CANDIDATE_NORMALIZED"
    NO_MESSAGE_ACTION = "NO_MESSAGE_ACTION"
    REJECTED = "REJECTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CandidateIntent(str, Enum):
    STOP = "STOP"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass(frozen=True, slots=True)
class ReceivedLogicalObject:
    """Parser/transport fixture input; decoded_object remains untrusted."""

    direction: object
    size_bytes: object
    parse_succeeded: object
    decoded_object: object


@dataclass(frozen=True, slots=True)
class NormalizerPolicy:
    max_message_size_bytes: int
    expected_protocol_version: str
    current_rover_boot_id: str
    max_safe_sequence: int
    max_ttl_ms: int

    def __post_init__(self) -> None:
        numeric_values = (
            self.max_message_size_bytes,
            self.max_safe_sequence,
            self.max_ttl_ms,
        )
        if any(type(value) is not int for value in numeric_values):
            raise TypeError("normalizer policy numeric values must be exact integers")
        if self.max_message_size_bytes < 0:
            raise ValueError("max_message_size_bytes must be non-negative")
        if self.max_safe_sequence < 0:
            raise ValueError("max_safe_sequence must be non-negative")
        if self.max_ttl_ms <= 0:
            raise ValueError("max_ttl_ms must be positive")
        strings = (
            self.expected_protocol_version,
            self.current_rover_boot_id,
        )
        if any(type(value) is not str or not value for value in strings):
            raise ValueError("normalizer identity values must be non-empty strings")


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    disposition: NormalizationDisposition
    rejection_reason: str | None
    diagnostic_code: str | None
    normalized_message: NormalizedLogicalMessage | None
    session_candidate: SessionCandidate | None
    candidate_intent: CandidateIntent | None
    identification_gate_passed: bool
    defensive_zero_candidate: bool
    normalizer_step_index: int
    message_type_label: str | None
    runtime_dispatch_permitted: bool
    internal_error: bool = False

    def report_dict(self) -> dict[str, Any]:
        """Return metadata only; never serialize the untrusted fixture payload."""
        return {
            "normalizer_step_index": self.normalizer_step_index,
            "disposition": self.disposition.value,
            "rejection_reason": self.rejection_reason,
            "diagnostic_code": self.diagnostic_code,
            "message_type_label": self.message_type_label,
            "candidate_intent": (
                None
                if self.candidate_intent is None
                else self.candidate_intent.value
            ),
            "identification_gate_passed": self.identification_gate_passed,
            "defensive_zero_candidate": self.defensive_zero_candidate,
            "runtime_dispatch_permitted": self.runtime_dispatch_permitted,
            "normalized_message_present": self.normalized_message is not None,
            "session_candidate_present": self.session_candidate is not None,
            "internal_error": self.internal_error,
        }
