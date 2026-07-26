from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any


class LogicalMessageType(str, Enum):
    SESSION_HELLO = "SESSION_HELLO"
    SESSION_ACCEPTED = "SESSION_ACCEPTED"
    SESSION_REJECTED = "SESSION_REJECTED"
    SESSION_END = "SESSION_END"
    CAPABILITY_SNAPSHOT = "CAPABILITY_SNAPSHOT"
    COMMAND = "COMMAND"
    CONTROL_UPDATE = "CONTROL_UPDATE"
    COMMAND_RESULT = "COMMAND_RESULT"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    TELEMETRY = "TELEMETRY"
    ROVER_HEARTBEAT = "ROVER_HEARTBEAT"
    DIAGNOSTIC = "DIAGNOSTIC"


class MessageDirection(str, Enum):
    CLIENT_TO_ROVER = "client_to_rover"
    CONTROLLER_TO_ROVER = "controller_to_rover"
    ROVER_TO_CLIENT = "rover_to_client"


class SenderRole(str, Enum):
    CONTROLLER = "controller"
    OBSERVER = "observer"
    ROVER = "rover"


class CommandType(str, Enum):
    ARM = "ARM"
    DISARM = "DISARM"
    SET_SPEED_LIMIT = "SET_SPEED_LIMIT"
    SELECT_DRIVE = "SELECT_DRIVE"
    SELECT_NEUTRAL = "SELECT_NEUTRAL"
    SELECT_PTO = "SELECT_PTO"
    MOVE_FORWARD = "MOVE_FORWARD"
    MOVE_REVERSE = "MOVE_REVERSE"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STOP = "STOP"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    PTO_START = "PTO_START"
    PTO_STOP = "PTO_STOP"
    FAULT_RESET = "fault_reset"
    EMERGENCY_STOP_RESET = "emergency_stop_reset"


class AdapterDisposition(str, Enum):
    RUNTIME_INPUT_READY = "RUNTIME_INPUT_READY"
    NO_RUNTIME_ACTION = "NO_RUNTIME_ACTION"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class CommandPayload:
    command_type: CommandType | str
    requested_speed: object | None = None
    speed_limit: object | None = None
    safety_confirmation: object | None = None


@dataclass(frozen=True, slots=True)
class ControlUpdatePayload:
    operation_id: object | None
    deadman_asserted: object | None


@dataclass(frozen=True, slots=True)
class SessionEndPayload:
    """Explicitly empty normalized payload for SESSION_END."""


@dataclass(frozen=True, slots=True)
class OpaquePayload:
    """Deep read-only fixture content with no Protocol payload schema."""

    content: object

    def __post_init__(self) -> None:
        object.__setattr__(self, "content", _freeze_opaque(self.content))


@dataclass(frozen=True, slots=True)
class NormalizedLogicalMessage:
    """Internal logical model; field names are not a wire-format contract."""

    protocol_version: object
    logical_message_type: LogicalMessageType | str
    direction: MessageDirection | str
    rover_boot_id: object
    session_id: object
    sender_id: object
    sender_role: SenderRole | str
    controller_ownership: object
    message_id: object
    sequence: object
    freshness_reference_ms: object
    ttl_ms: object
    payload: object | None = None


def _freeze_opaque(value: object) -> object:
    if value is None or type(value) in {bool, int, float, str, bytes}:
        return value
    if isinstance(value, Mapping):
        frozen = {
            _freeze_opaque(key): _freeze_opaque(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_opaque(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_opaque(item) for item in value)
    raise TypeError("opaque payload content must be recursively read-only compatible")


@dataclass(frozen=True, slots=True)
class ReceiverContext:
    expected_protocol_version: str
    current_rover_boot_id: str
    active_session_id: str
    active_controller_owner_id: str
    current_monotonic_time_ms: int
    max_ttl_ms: int
    max_safe_sequence: int
    runtime_profile: str
    max_speed: int
    drive_available: bool
    turn_left_available: bool
    turn_right_available: bool
    pto_available: bool
    right_output_available: bool

    def __post_init__(self) -> None:
        string_values = (
            self.expected_protocol_version,
            self.current_rover_boot_id,
            self.active_session_id,
            self.active_controller_owner_id,
            self.runtime_profile,
        )
        if any(not isinstance(value, str) or not value for value in string_values):
            raise ValueError("receiver identity and profile values must be non-empty")
        integer_values = (
            self.current_monotonic_time_ms,
            self.max_ttl_ms,
            self.max_safe_sequence,
            self.max_speed,
        )
        if any(type(value) is not int for value in integer_values):
            raise TypeError("receiver numeric limits must be exact integers")
        if self.current_monotonic_time_ms < 0:
            raise ValueError("current_monotonic_time_ms must be non-negative")
        if self.max_ttl_ms <= 0 or self.max_safe_sequence < 0 or self.max_speed <= 0:
            raise ValueError("receiver limits must be positive")
        capability_values = (
            self.drive_available,
            self.turn_left_available,
            self.turn_right_available,
            self.pto_available,
            self.right_output_available,
        )
        if any(type(value) is not bool for value in capability_values):
            raise TypeError("receiver capabilities must be exact booleans")


@dataclass(frozen=True, slots=True)
class AdapterResult:
    disposition: AdapterDisposition
    rejection_reason: str | None
    diagnostic_code: str | None
    message_id: str | None
    sequence: int | None
    logical_message_type: str | None
    mapped_event: str | None
    runtime_input: Any | None
    control_liveness_candidate: bool
    adapter_step_index: int
    internal_error: bool = False

    def report_dict(self) -> dict[str, Any]:
        return {
            "adapter_step_index": self.adapter_step_index,
            "disposition": self.disposition.value,
            "rejection_reason": self.rejection_reason,
            "diagnostic_code": self.diagnostic_code,
            "message_id": self.message_id,
            "sequence": self.sequence,
            "logical_message_type": self.logical_message_type,
            "mapped_event": self.mapped_event,
            "runtime_input": runtime_input_dict(self.runtime_input),
            "control_liveness_candidate": self.control_liveness_candidate,
            "internal_error": self.internal_error,
        }


def runtime_input_dict(runtime_input: Any | None) -> dict[str, Any] | None:
    if runtime_input is None:
        return None
    event = runtime_input.event
    event_value = event.value if isinstance(event, Enum) else str(event)
    return {
        "event": event_value,
        "now_ms": runtime_input.now_ms,
        "sequence": runtime_input.sequence,
        "issued_at_ms": runtime_input.issued_at_ms,
        "ttl_ms": runtime_input.ttl_ms,
        "session_id": runtime_input.session_id,
        "requested_speed": runtime_input.requested_speed,
        "speed_limit": runtime_input.speed_limit,
        "operation_id": runtime_input.operation_id,
        "deadman_asserted": runtime_input.deadman_asserted,
        "safety_confirmation": runtime_input.safety_confirmation,
        "physical_estop_asserted": runtime_input.physical_estop_asserted,
        "fault_present": runtime_input.fault_present,
        "output_apply_success": runtime_input.output_apply_success,
    }
