from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


PROTOCOL_VERSION = "v0"
REPORT_VERSION = 1
SIMULATOR_VERSION = "0.1.0"
MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


class RoverState(str, Enum):
    BOOT_SAFE = "BOOT_SAFE"
    DISARMED = "DISARMED"
    ARMED_NEUTRAL = "ARMED_NEUTRAL"
    DRIVE_READY = "DRIVE_READY"
    DRIVE_ACTIVE = "DRIVE_ACTIVE"
    PTO_READY = "PTO_READY"
    PTO_ACTIVE = "PTO_ACTIVE"
    COMM_LOSS_LATCHED = "COMM_LOSS_LATCHED"
    FAULT_LATCHED = "FAULT_LATCHED"
    EMERGENCY_STOP_LATCHED = "EMERGENCY_STOP_LATCHED"


class DriveMode(str, Enum):
    NONE = "NONE"
    DRIVE = "DRIVE"
    PTO = "PTO"
    NEUTRAL = "NEUTRAL"


class Profile(str, Enum):
    ONE_SIDE_TEST = "one_side_test"
    DRIVE_PTO_SPLIT_FIXTURE = "drive_pto_split_fixture"


class Event(str, Enum):
    # Simulator-local lifecycle/time inputs.
    BOOT = "BOOT"
    DEADMAN_ASSERT = "DEADMAN_ASSERT"
    WATCHDOG_TIMEOUT = "WATCHDOG_TIMEOUT"
    TICK = "TICK"

    # Protocol v0 operator commands.
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

    # Protocol message inputs that generate state-machine events.
    CONTROL_UPDATE = "CONTROL_UPDATE"
    SESSION_END = "SESSION_END"

    # Receiver-local/state-machine events.
    BOOT_COMPLETE = "boot_complete"
    BOOT_FAILED = "boot_failed"
    DEADMAN_RELEASED = "deadman_released"
    COMMAND_EXPIRED = "command_expired"
    COMMUNICATION_LOST = "communication_lost"
    COMMUNICATION_RESTORED = "communication_restored"
    FAULT_DETECTED = "fault_detected"


EVENT_ALIASES = (
    ("CLEAR_EMERGENCY_STOP", Event.EMERGENCY_STOP_RESET),
    ("DEADMAN_RELEASE", Event.DEADMAN_RELEASED),
    ("COMMUNICATION_CONNECTED", Event.COMMUNICATION_RESTORED),
    ("COMMUNICATION_LOST", Event.COMMUNICATION_LOST),
)


def normalize_event(value: Event | str) -> Event:
    if isinstance(value, Event):
        return value
    for alias, event in EVENT_ALIASES:
        if value == alias:
            return event
    return Event(value)


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    profile: Profile = Profile.ONE_SIDE_TEST
    watchdog_timeout_ms: int = 750
    max_command_ttl_ms: int = 5_000
    max_speed: int = 100
    session_id: str = "session-1"
    real_motor_output_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.profile, Profile):
            raise TypeError("profile must be a Profile")
        if not isinstance(self.watchdog_timeout_ms, int) or self.watchdog_timeout_ms <= 0:
            raise ValueError("watchdog_timeout_ms must be a positive integer")
        if not isinstance(self.max_command_ttl_ms, int) or self.max_command_ttl_ms <= 0:
            raise ValueError("max_command_ttl_ms must be a positive integer")
        if not isinstance(self.max_speed, int) or self.max_speed <= 0:
            raise ValueError("max_speed must be a positive integer")
        if not self.session_id:
            raise ValueError("session_id must be non-empty")
        if self.real_motor_output_enabled:
            raise ValueError("the virtual rover cannot enable real motor output")

    @property
    def pto_available(self) -> bool:
        return self.profile is Profile.DRIVE_PTO_SPLIT_FIXTURE

    @property
    def right_output_available(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RuntimeInput:
    event: Event | str
    now_ms: int
    sequence: int | None = None
    issued_at_ms: int | None = None
    ttl_ms: int | None = None
    session_id: str | None = None
    requested_speed: int | None = None
    speed_limit: int | None = None
    operation_id: str | None = None
    deadman_asserted: bool | None = None
    safety_confirmation: bool = False
    physical_estop_asserted: bool = False
    fault_present: bool = False
    output_apply_success: bool = True

    @classmethod
    def command(
        cls,
        event: Event | str,
        *,
        sequence: int,
        now_ms: int,
        session_id: str = "session-1",
        ttl_ms: int = 1_000,
        **values: Any,
    ) -> RuntimeInput:
        return cls(
            event=event,
            now_ms=now_ms,
            sequence=sequence,
            issued_at_ms=values.pop("issued_at_ms", now_ms),
            ttl_ms=ttl_ms,
            session_id=session_id,
            **values,
        )

    @classmethod
    def local(cls, event: Event | str, *, now_ms: int, **values: Any) -> RuntimeInput:
        return cls(event=event, now_ms=now_ms, **values)


@dataclass(frozen=True, slots=True)
class RuntimeState:
    official_state: RoverState = RoverState.BOOT_SAFE
    selected_mode: DriveMode = DriveMode.NONE
    armed: bool = False
    emergency_stop_latched: bool = False
    communication_loss_latched: bool = False
    fault_latched: bool = False
    deadman_active: bool = False
    communication_alive: bool = False
    speed_limit: int = 0
    requested_speed: int = 0
    effective_speed: int = 0
    left_output: int = 0
    right_output: int | None = None
    pto_requested: bool = False
    pto_effective: bool = False
    last_seen_sequence: int | None = None
    last_accepted_sequence: int | None = None
    operation_id: str | None = None
    monotonic_time_ms: int = 0
    watchdog_deadline_ms: int | None = None
    session_id: str = "session-1"
    used_session_ids: tuple[str, ...] = ("session-1",)
    boot_session_ready: bool = True
    stop_reason: str | None = None
    fault_reasons: tuple[str, ...] = ()
    step_index: int = 0


@dataclass(frozen=True, slots=True)
class StepResult:
    step_index: int
    previous_state: str
    official_state: str
    event: str
    accepted: bool
    rejection_reason: str | None
    armed: bool
    emergency_stop_latched: bool
    deadman_active: bool
    communication_alive: bool
    selected_mode: str
    requested_speed: int
    effective_speed: int
    left_output: int
    right_output: int | None
    pto_requested: bool
    pto_effective: bool
    safety_action: str
    sequence_accepted: bool
    last_accepted_sequence: int | None
    operation_id: str | None
    stop_reason: str | None
    diagnostic_code: str | None
    internal_failure: bool

    def report_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "previous_state": self.previous_state,
            "official_state": self.official_state,
            "event": self.event,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "armed": self.armed,
            "emergency_stop_latched": self.emergency_stop_latched,
            "deadman_active": self.deadman_active,
            "communication_alive": self.communication_alive,
            "selected_mode": self.selected_mode,
            "requested_speed": self.requested_speed,
            "effective_speed": self.effective_speed,
            "left_output": self.left_output,
            "right_output": self.right_output,
            "pto_requested": self.pto_requested,
            "pto_effective": self.pto_effective,
            "safety_action": self.safety_action,
            "sequence_accepted": self.sequence_accepted,
            "last_accepted_sequence": self.last_accepted_sequence,
            "operation_id": self.operation_id,
            "stop_reason": self.stop_reason,
            "diagnostic_code": self.diagnostic_code,
            "internal_failure": self.internal_failure,
        }
