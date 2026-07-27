from __future__ import annotations

from dataclasses import replace

from ..runtime_adapter import (
    CommandPayload,
    CommandType,
    ControlUpdatePayload,
    LogicalMessageType,
    MessageDirection,
    NormalizedLogicalMessage,
    SenderRole,
    SessionEndPayload,
)
from ..session_negotiation import SessionCandidate, SessionRole

from .model import (
    CandidateIntent,
    NormalizationDisposition,
    NormalizationResult,
    NormalizerPolicy,
    ReceivedLogicalObject,
)


_RUNTIME_TOP_KEYS = frozenset(
    {
        "protocol_version",
        "logical_message_type",
        "rover_boot_id",
        "session_id",
        "sender_id",
        "sender_role",
        "controller_ownership",
        "message_id",
        "sequence",
        "freshness_reference_ms",
        "ttl_ms",
        "payload",
    }
)
_SESSION_END_REQUIRED_TOP_KEYS = _RUNTIME_TOP_KEYS - {"payload"}
_HELLO_TOP_KEYS = frozenset(
    {
        "logical_message_type",
        "rover_boot_id",
        "sender_id",
        "sender_role",
        "message_id",
        "payload",
    }
)
_HELLO_PAYLOAD_KEYS = frozenset(
    {
        "protocol_versions",
        "requested_role",
        "candidate_session_id",
        "sender_instance_id",
        "human_switch_confirmation",
        "request_index",
    }
)
_CONTROL_UPDATE_KEYS = frozenset({"operation_id", "deadman_asserted"})
_COMMAND_BASE_KEYS = frozenset({"command_type"})
_MOVE_COMMANDS = frozenset(
    {CommandType.MOVE_FORWARD, CommandType.MOVE_REVERSE}
)
_RESET_COMMANDS = frozenset(
    {CommandType.FAULT_RESET, CommandType.EMERGENCY_STOP_RESET}
)
_ROVER_TO_CLIENT_TYPES = frozenset(
    {
        LogicalMessageType.SESSION_ACCEPTED,
        LogicalMessageType.SESSION_REJECTED,
        LogicalMessageType.CAPABILITY_SNAPSHOT,
        LogicalMessageType.COMMAND_RESULT,
        LogicalMessageType.STATE_SNAPSHOT,
        LogicalMessageType.TELEMETRY,
        LogicalMessageType.ROVER_HEARTBEAT,
        LogicalMessageType.DIAGNOSTIC,
    }
)
_KNOWN_DIRECTIONS = frozenset(
    {
        MessageDirection.CLIENT_TO_ROVER.value,
        MessageDirection.CONTROLLER_TO_ROVER.value,
        MessageDirection.ROVER_TO_CLIENT.value,
    }
)


class StrictLogicalMessageNormalizer:
    """Strict Python-fixture boundary with no formal runtime side effects."""

    def __init__(self, policy: NormalizerPolicy) -> None:
        if type(policy) is not NormalizerPolicy:
            raise TypeError("policy must be a NormalizerPolicy")
        self._policy = policy
        self._step_index = 0

    @property
    def policy(self) -> NormalizerPolicy:
        return self._policy

    @property
    def step_index(self) -> int:
        return self._step_index

    def update_current_rover_boot_id(self, rover_boot_id: str) -> None:
        """Synchronize trusted receiver metadata after a manager boot update."""
        if type(rover_boot_id) is not str or not rover_boot_id:
            raise ValueError("rover_boot_id must be an exact non-empty string")
        self._policy = replace(
            self._policy,
            current_rover_boot_id=rover_boot_id,
        )

    def normalize(self, received: ReceivedLogicalObject) -> NormalizationResult:
        self._step_index += 1
        step_index = self._step_index
        try:
            return self._normalize(received, step_index)
        except Exception:
            return NormalizationResult(
                NormalizationDisposition.INTERNAL_ERROR,
                "internal_error",
                "NORMALIZER_INTERNAL_ERROR",
                None,
                None,
                None,
                False,
                False,
                step_index,
                None,
                False,
                True,
            )

    def _normalize(
        self,
        received: ReceivedLogicalObject,
        step_index: int,
    ) -> NormalizationResult:
        if type(received) is not ReceivedLogicalObject:
            raise TypeError("received must be a ReceivedLogicalObject")

        # Gate 1: size metadata. bool is deliberately not an integer here.
        if type(received.size_bytes) is not int or received.size_bytes < 0:
            return self._no_action(step_index, "invalid_size_metadata")
        # Gate 2: trusted transport/decoder size limit.
        if received.size_bytes > self._policy.max_message_size_bytes:
            return self._no_action(step_index, "message_too_large")
        # Gate 3: parse result. Do not access decoded_object on failure.
        if type(received.parse_succeeded) is not bool:
            return self._no_action(step_index, "invalid_parse_metadata")
        if not received.parse_succeeded:
            return self._no_action(step_index, "parse_failed")
        # Gate 4: exact decoded object type.
        decoded = received.decoded_object
        if type(decoded) is not dict or not self._exact_string_keys(decoded):
            return self._no_action(step_index, "decoded_object_not_exact_dict")
        # Gate 5: safe message type identification.
        raw_type = decoded.get("logical_message_type")
        if type(raw_type) is not str:
            return self._no_action(step_index, "message_type_not_identifiable")
        message_type = self._enum_or_none(LogicalMessageType, raw_type)
        if message_type is None:
            return self._no_action(
                step_index,
                "message_type_not_identifiable",
            )
        # Gate 6: exact trusted direction metadata.
        direction = received.direction
        if type(direction) is not str or direction not in _KNOWN_DIRECTIONS:
            return self._no_action(
                step_index,
                "direction_not_identifiable",
                message_type.value,
            )
        mismatch = self._direction_mismatch(message_type, direction)
        if mismatch:
            return self._reject(
                step_index,
                "wrong_direction",
                "MESSAGE_DIRECTION_MISMATCH",
                message_type.value,
            )
        if message_type in _ROVER_TO_CLIENT_TYPES:
            return self._no_action(
                step_index,
                "rover_to_client_message",
                message_type.value,
            )
        if (
            message_type is LogicalMessageType.SESSION_END
            and direction == MessageDirection.ROVER_TO_CLIENT.value
        ):
            return self._no_action(
                step_index,
                "rover_to_client_message",
                message_type.value,
            )

        # Gates 7-9: identification, closed-object validation, typed model.
        if message_type is LogicalMessageType.SESSION_HELLO:
            return self._normalize_hello(decoded, step_index)
        return self._normalize_runtime(
            decoded,
            message_type,
            direction,
            step_index,
        )

    def _normalize_hello(
        self,
        decoded: dict[str, object],
        step_index: int,
    ) -> NormalizationResult:
        message_type_label = LogicalMessageType.SESSION_HELLO.value
        diagnostic = self._closed_object_diagnostic(
            decoded,
            _HELLO_TOP_KEYS,
            _HELLO_TOP_KEYS,
            "UNKNOWN_TOP_LEVEL_PROPERTY",
        )
        if diagnostic is not None:
            return self._reject_structure(
                step_index,
                diagnostic,
                message_type_label,
            )
        if type(decoded["payload"]) is not dict:
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        payload = decoded["payload"]
        if not self._exact_string_keys(payload):
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        diagnostic = self._closed_object_diagnostic(
            payload,
            _HELLO_PAYLOAD_KEYS,
            _HELLO_PAYLOAD_KEYS,
            "UNKNOWN_SESSION_HELLO_PROPERTY",
        )
        if diagnostic is not None:
            return self._reject_structure(
                step_index,
                diagnostic,
                message_type_label,
            )
        top_strings = (
            decoded["rover_boot_id"],
            decoded["sender_id"],
            decoded["sender_role"],
            decoded["message_id"],
        )
        if any(type(value) is not str or not value for value in top_strings):
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        requested_role = self._enum_or_none(
            SessionRole,
            payload["requested_role"],
        )
        if (
            requested_role is None
            or decoded["sender_role"] != requested_role.value
        ):
            return self._reject_structure(
                step_index,
                "REQUESTED_ROLE_INVALID",
                message_type_label,
            )
        versions = payload["protocol_versions"]
        if type(versions) not in {list, tuple} or not versions:
            return self._reject_structure(
                step_index,
                "PROTOCOL_VERSION_CANDIDATES_INVALID",
                message_type_label,
            )
        if any(type(value) is not str or not value for value in versions):
            return self._reject_structure(
                step_index,
                "PROTOCOL_VERSION_CANDIDATES_INVALID",
                message_type_label,
            )
        if len(versions) != len(set(versions)):
            return self._reject_structure(
                step_index,
                "PROTOCOL_VERSION_CANDIDATES_DUPLICATED",
                message_type_label,
            )
        identifiers = (
            payload["candidate_session_id"],
            payload["sender_instance_id"],
        )
        if any(type(value) is not str or not value for value in identifiers):
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        if type(payload["human_switch_confirmation"]) is not bool:
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        request_index = payload["request_index"]
        if type(request_index) is not int or request_index < 0:
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                message_type_label,
            )
        candidate = SessionCandidate(
            protocol_versions=tuple(versions),
            requested_role=requested_role,
            candidate_session_id=payload["candidate_session_id"],
            rover_boot_id=decoded["rover_boot_id"],
            sender_id=decoded["sender_id"],
            sender_instance_id=payload["sender_instance_id"],
            human_switch_confirmation=payload[
                "human_switch_confirmation"
            ],
            request_index=request_index,
        )
        return NormalizationResult(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            None,
            None,
            None,
            candidate,
            None,
            False,
            False,
            step_index,
            message_type_label,
            False,
        )

    def _normalize_runtime(
        self,
        decoded: dict[str, object],
        message_type: LogicalMessageType,
        direction: str,
        step_index: int,
    ) -> NormalizationResult:
        label = message_type.value
        protocol_version = decoded.get("protocol_version")
        if (
            type(protocol_version) is not str
            or protocol_version != self._policy.expected_protocol_version
        ):
            return self._reject(
                step_index,
                "unsupported_version",
                "UNSUPPORTED_PROTOCOL_VERSION",
                label,
            )
        rover_boot_id = decoded.get("rover_boot_id")
        if (
            type(rover_boot_id) is not str
            or rover_boot_id != self._policy.current_rover_boot_id
        ):
            return self._reject(
                step_index,
                "invalid_boot_id",
                "ROVER_BOOT_ID_MISMATCH",
                label,
            )

        intent = self._candidate_intent(decoded, message_type, direction)
        gate_passed = intent is not None
        required_keys = (
            _SESSION_END_REQUIRED_TOP_KEYS
            if message_type is LogicalMessageType.SESSION_END
            else _RUNTIME_TOP_KEYS
        )
        diagnostic = self._closed_object_diagnostic(
            decoded,
            _RUNTIME_TOP_KEYS,
            required_keys,
            "UNKNOWN_TOP_LEVEL_PROPERTY",
        )
        if diagnostic is not None:
            return self._reject_structure(
                step_index,
                diagnostic,
                label,
                intent,
                gate_passed,
            )

        string_fields = (
            "protocol_version",
            "logical_message_type",
            "rover_boot_id",
            "session_id",
            "sender_id",
            "sender_role",
            "message_id",
        )
        if any(
            type(decoded[name]) is not str or not decoded[name]
            for name in string_fields
        ):
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                label,
                intent,
                gate_passed,
            )
        if decoded["sender_role"] != SenderRole.CONTROLLER.value:
            return self._reject_structure(
                step_index,
                "CONTROLLER_SENDER_ROLE_REQUIRED",
                label,
                intent,
                gate_passed,
            )
        if type(decoded["controller_ownership"]) is not bool:
            return self._reject_structure(
                step_index,
                "TYPE_MISMATCH",
                label,
                intent,
                gate_passed,
            )
        sequence = decoded["sequence"]
        freshness = decoded["freshness_reference_ms"]
        ttl_ms = decoded["ttl_ms"]
        if (
            type(sequence) is not int
            or sequence < 0
            or sequence > self._policy.max_safe_sequence
        ):
            return self._reject_structure(
                step_index,
                "SEQUENCE_OUT_OF_RANGE",
                label,
                intent,
                gate_passed,
            )
        if type(freshness) is not int or freshness < 0:
            return self._reject_structure(
                step_index,
                "FRESHNESS_REFERENCE_INVALID",
                label,
                intent,
                gate_passed,
            )
        if (
            type(ttl_ms) is not int
            or ttl_ms <= 0
            or ttl_ms > self._policy.max_ttl_ms
        ):
            return self._reject_structure(
                step_index,
                "TTL_INVALID",
                label,
                intent,
                gate_passed,
            )

        payload_result = self._normalize_payload(message_type, decoded)
        if type(payload_result) is str:
            return self._reject_structure(
                step_index,
                payload_result,
                label,
                intent,
                gate_passed,
            )
        message = NormalizedLogicalMessage(
            protocol_version=decoded["protocol_version"],
            logical_message_type=message_type,
            direction=MessageDirection(direction),
            rover_boot_id=decoded["rover_boot_id"],
            session_id=decoded["session_id"],
            sender_id=decoded["sender_id"],
            sender_role=SenderRole.CONTROLLER,
            controller_ownership=decoded["controller_ownership"],
            message_id=decoded["message_id"],
            sequence=sequence,
            freshness_reference_ms=freshness,
            ttl_ms=ttl_ms,
            payload=payload_result,
        )
        return NormalizationResult(
            NormalizationDisposition.MESSAGE_NORMALIZED,
            None,
            None,
            message,
            None,
            intent,
            gate_passed,
            False,
            step_index,
            label,
            True,
        )

    def _normalize_payload(
        self,
        message_type: LogicalMessageType,
        decoded: dict[str, object],
    ) -> CommandPayload | ControlUpdatePayload | SessionEndPayload | str:
        if message_type is LogicalMessageType.SESSION_END:
            if "payload" not in decoded:
                return SessionEndPayload()
            payload = decoded["payload"]
            if type(payload) is not dict:
                return "TYPE_MISMATCH"
            if not self._exact_string_keys(payload):
                return "TYPE_MISMATCH"
            if payload:
                return "UNKNOWN_SESSION_END_PROPERTY"
            return SessionEndPayload()

        payload = decoded["payload"]
        if type(payload) is not dict or not self._exact_string_keys(payload):
            return "TYPE_MISMATCH"
        if message_type is LogicalMessageType.CONTROL_UPDATE:
            diagnostic = self._closed_object_diagnostic(
                payload,
                _CONTROL_UPDATE_KEYS,
                _CONTROL_UPDATE_KEYS,
                "UNKNOWN_CONTROL_UPDATE_PROPERTY",
            )
            if diagnostic is not None:
                return diagnostic
            operation_id = payload["operation_id"]
            deadman = payload["deadman_asserted"]
            if type(operation_id) is not str or not operation_id:
                return "TYPE_MISMATCH"
            if type(deadman) is not bool:
                return "TYPE_MISMATCH"
            return ControlUpdatePayload(operation_id, deadman)

        if message_type is not LogicalMessageType.COMMAND:
            return "UNSUPPORTED_INPUT_MESSAGE_TYPE"
        raw_command = payload.get("command_type")
        if type(raw_command) is not str:
            return "TYPE_MISMATCH"
        command = self._enum_or_none(CommandType, raw_command)
        if command is None:
            return "UNKNOWN_COMMAND_TYPE"
        expected_keys = set(_COMMAND_BASE_KEYS)
        if command in _MOVE_COMMANDS:
            expected_keys.add("requested_speed")
        elif command is CommandType.SET_SPEED_LIMIT:
            expected_keys.add("speed_limit")
        elif command in _RESET_COMMANDS:
            expected_keys.add("safety_confirmation")
        expected = frozenset(expected_keys)
        all_command_keys = frozenset(
            {
                "command_type",
                "requested_speed",
                "speed_limit",
                "safety_confirmation",
            }
        )
        if not frozenset(payload) <= all_command_keys:
            return "UNKNOWN_COMMAND_PAYLOAD_PROPERTY"
        if not frozenset(payload) <= expected:
            return "FORBIDDEN_PROPERTY_PRESENT"
        diagnostic = self._closed_object_diagnostic(
            payload,
            expected,
            expected,
            "FORBIDDEN_PROPERTY_PRESENT",
        )
        if diagnostic is not None:
            return diagnostic
        if command in _MOVE_COMMANDS:
            speed = payload["requested_speed"]
            if type(speed) is not int:
                return "TYPE_MISMATCH"
            return CommandPayload(command, requested_speed=speed)
        if command is CommandType.SET_SPEED_LIMIT:
            speed_limit = payload["speed_limit"]
            if type(speed_limit) is not int:
                return "TYPE_MISMATCH"
            return CommandPayload(command, speed_limit=speed_limit)
        if command in _RESET_COMMANDS:
            confirmation = payload["safety_confirmation"]
            if type(confirmation) is not bool:
                return "TYPE_MISMATCH"
            return CommandPayload(command, safety_confirmation=confirmation)
        return CommandPayload(command)

    def _candidate_intent(
        self,
        decoded: dict[str, object],
        message_type: LogicalMessageType,
        direction: str,
    ) -> CandidateIntent | None:
        if (
            message_type is not LogicalMessageType.COMMAND
            or direction != MessageDirection.CONTROLLER_TO_ROVER.value
        ):
            return None
        payload = decoded.get("payload")
        if type(payload) is not dict or not self._exact_string_keys(payload):
            return None
        raw_command = payload.get("command_type")
        if type(raw_command) is not str:
            return None
        if raw_command == CommandType.STOP.value:
            return CandidateIntent.STOP
        if raw_command == CommandType.EMERGENCY_STOP.value:
            return CandidateIntent.EMERGENCY_STOP
        return None

    @staticmethod
    def _direction_mismatch(
        message_type: LogicalMessageType,
        direction: str,
    ) -> bool:
        if message_type is LogicalMessageType.SESSION_HELLO:
            return direction != MessageDirection.CLIENT_TO_ROVER.value
        if message_type is LogicalMessageType.SESSION_END:
            return direction not in {
                MessageDirection.CONTROLLER_TO_ROVER.value,
                MessageDirection.ROVER_TO_CLIENT.value,
            }
        if message_type in _ROVER_TO_CLIENT_TYPES:
            return direction != MessageDirection.ROVER_TO_CLIENT.value
        return direction != MessageDirection.CONTROLLER_TO_ROVER.value

    @staticmethod
    def _closed_object_diagnostic(
        value: dict[str, object],
        allowed: frozenset[str],
        required: frozenset[str],
        unknown_diagnostic: str,
    ) -> str | None:
        keys = frozenset(value)
        if not keys <= allowed:
            return unknown_diagnostic
        if not required <= keys:
            return "MISSING_REQUIRED_PROPERTY"
        return None

    @staticmethod
    def _exact_string_keys(value: dict[object, object]) -> bool:
        return all(type(key) is str for key in value)

    @staticmethod
    def _enum_or_none(enum_type, value):
        if type(value) is not str:
            return None
        try:
            return enum_type(value)
        except ValueError:
            return None

    def _no_action(
        self,
        step_index: int,
        reason: str,
        label: str | None = None,
    ) -> NormalizationResult:
        return NormalizationResult(
            NormalizationDisposition.NO_MESSAGE_ACTION,
            reason,
            self._diagnostic(reason),
            None,
            None,
            None,
            False,
            False,
            step_index,
            label,
            False,
        )

    @staticmethod
    def _reject(
        step_index: int,
        reason: str,
        diagnostic: str,
        label: str | None,
    ) -> NormalizationResult:
        return NormalizationResult(
            NormalizationDisposition.REJECTED,
            reason,
            diagnostic,
            None,
            None,
            None,
            False,
            False,
            step_index,
            label,
            False,
        )

    @staticmethod
    def _reject_structure(
        step_index: int,
        diagnostic: str,
        label: str,
        intent: CandidateIntent | None = None,
        gate_passed: bool = False,
    ) -> NormalizationResult:
        return NormalizationResult(
            NormalizationDisposition.REJECTED,
            "invalid_fixture",
            diagnostic,
            None,
            None,
            intent,
            gate_passed,
            gate_passed,
            step_index,
            label,
            False,
        )

    @staticmethod
    def _diagnostic(reason: str) -> str:
        return {
            "invalid_size_metadata": "SIZE_METADATA_INVALID",
            "message_too_large": "MESSAGE_SIZE_LIMIT_EXCEEDED",
            "invalid_parse_metadata": "PARSE_METADATA_INVALID",
            "parse_failed": "PARSE_FAILED",
            "decoded_object_not_exact_dict": "DECODED_OBJECT_TYPE_INVALID",
            "message_type_not_identifiable": "MESSAGE_TYPE_NOT_IDENTIFIABLE",
            "direction_not_identifiable": "DIRECTION_NOT_IDENTIFIABLE",
            "rover_to_client_message": "ROVER_TO_CLIENT_NO_ACTION",
        }[reason]
