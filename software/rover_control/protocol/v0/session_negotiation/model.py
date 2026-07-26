from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SessionRole(str, Enum):
    CONTROLLER = "controller"
    OBSERVER = "observer"


class NegotiationDisposition(str, Enum):
    SESSION_ACCEPTED = "SESSION_ACCEPTED"
    SESSION_REJECTED = "SESSION_REJECTED"
    SESSION_ENDED = "SESSION_ENDED"
    NO_CHANGE = "NO_CHANGE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class RuntimeSynchronizationState(str, Enum):
    UNBOUND = "UNBOUND"
    SYNCHRONIZED = "SYNCHRONIZED"
    SESSION_ENDED = "SESSION_ENDED"
    BOOT_ID_CHANGED = "BOOT_ID_CHANGED"
    RUNTIME_BOOT_REJECTED = "RUNTIME_BOOT_REJECTED"
    RUNTIME_SESSION_END_REJECTED = "RUNTIME_SESSION_END_REJECTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True, slots=True)
class SessionCandidate:
    """Normalized SESSION_HELLO fixture; not a wire-format contract."""

    protocol_versions: object
    requested_role: object
    candidate_session_id: object
    rover_boot_id: object
    sender_id: object
    sender_instance_id: object
    human_switch_confirmation: object
    request_index: object


@dataclass(frozen=True, slots=True)
class SessionEndRequest:
    """Normalized Controller-to-Rover SESSION_END fixture."""

    rover_boot_id: object
    session_id: object
    sender_id: object
    sender_instance_id: object
    message_id: object
    sequence: object
    freshness_reference_ms: object
    ttl_ms: object
    request_index: object


@dataclass(frozen=True, slots=True)
class ReceiverPolicy:
    runtime_profile: str
    capability_profile_reference: str
    max_ttl_ms: int
    max_safe_sequence: int
    max_speed: int
    drive_available: bool
    turn_left_available: bool
    turn_right_available: bool
    pto_available: bool
    right_output_available: bool

    def __post_init__(self) -> None:
        if (
            not isinstance(self.runtime_profile, str)
            or not self.runtime_profile
            or not isinstance(self.capability_profile_reference, str)
            or not self.capability_profile_reference
        ):
            raise ValueError("profile references must be non-empty strings")
        numeric_values = (
            self.max_ttl_ms,
            self.max_safe_sequence,
            self.max_speed,
        )
        if any(type(value) is not int for value in numeric_values):
            raise TypeError("receiver policy numeric values must be exact integers")
        if (
            self.max_ttl_ms <= 0
            or self.max_safe_sequence < 0
            or self.max_speed <= 0
        ):
            raise ValueError("receiver policy numeric limits are invalid")
        capabilities = (
            self.drive_available,
            self.turn_left_available,
            self.turn_right_available,
            self.pto_available,
            self.right_output_available,
        )
        if any(type(value) is not bool for value in capabilities):
            raise TypeError("receiver policy capabilities must be exact booleans")


@dataclass(frozen=True, slots=True)
class SessionManagerState:
    current_rover_boot_id: str
    active_session_id: str | None = None
    active_controller_owner_id: str | None = None
    active_sender_instance_id: str | None = None
    selected_protocol_version: str | None = None
    controller_owned: bool = False
    used_session_ids: tuple[str, ...] = ()
    negotiation_step_index: int = 0
    last_negotiation_disposition: str | None = None
    session_generation_counter: int = 0
    session_termination_pending: bool = False
    runtime_synchronization_state: str = RuntimeSynchronizationState.UNBOUND.value
    last_ended_controller_owner_id: str | None = None
    last_ended_sender_instance_id: str | None = None

    def report_dict(self) -> dict[str, Any]:
        return {
            "current_rover_boot_id": self.current_rover_boot_id,
            "active_session_id": self.active_session_id,
            "active_controller_owner_id": self.active_controller_owner_id,
            "active_sender_instance_id": self.active_sender_instance_id,
            "selected_protocol_version": self.selected_protocol_version,
            "controller_owned": self.controller_owned,
            "used_session_ids": list(self.used_session_ids),
            "negotiation_step_index": self.negotiation_step_index,
            "last_negotiation_disposition": self.last_negotiation_disposition,
            "session_generation_counter": self.session_generation_counter,
            "session_termination_pending": self.session_termination_pending,
            "runtime_synchronization_state": self.runtime_synchronization_state,
            "last_ended_controller_owner_id": (
                self.last_ended_controller_owner_id
            ),
            "last_ended_sender_instance_id": self.last_ended_sender_instance_id,
        }


@dataclass(frozen=True, slots=True)
class NegotiationResult:
    disposition: NegotiationDisposition
    rejection_reason: str | None
    diagnostic_code: str | None
    selected_protocol_version: str | None
    accepted_session_id: str | None
    requested_role: str | None
    accepted_role: str | None
    rover_boot_id: str
    controller_ownership: bool
    capability_profile_reference: str
    deterministic_result_index: int
    runtime_event_dispatched: bool
    manager_state: SessionManagerState

    def report_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition.value,
            "rejection_reason": self.rejection_reason,
            "diagnostic_code": self.diagnostic_code,
            "selected_protocol_version": self.selected_protocol_version,
            "accepted_session_id": self.accepted_session_id,
            "requested_role": self.requested_role,
            "accepted_role": self.accepted_role,
            "rover_boot_id": self.rover_boot_id,
            "controller_ownership": self.controller_ownership,
            "capability_profile_reference": self.capability_profile_reference,
            "deterministic_result_index": self.deterministic_result_index,
            "runtime_event_dispatched": self.runtime_event_dispatched,
            "manager_state": self.manager_state.report_dict(),
        }


@dataclass(frozen=True, slots=True)
class ManagerAction:
    result: NegotiationResult
    adapter_result: Any | None = None
    runtime_result: Any | None = None


@dataclass(frozen=True, slots=True)
class RuntimeDispatch:
    adapter_result: Any | None
    runtime_result: Any | None
    rejection_reason: str | None
    diagnostic_code: str | None


@dataclass(frozen=True, slots=True)
class LocalRuntimeAction:
    runtime_result: Any | None
    rejection_reason: str | None
    diagnostic_code: str | None
