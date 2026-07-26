from __future__ import annotations

from ....simulator.virtual_rover import Event, RuntimeInput

from .model import (
    AdapterDisposition,
    AdapterResult,
    CommandPayload,
    CommandType,
    ControlUpdatePayload,
    LogicalMessageType,
    MessageDirection,
    NormalizedLogicalMessage,
    ReceiverContext,
    SenderRole,
    SessionEndPayload,
)


COMMAND_EVENT_MAP = {
    CommandType.ARM: Event.ARM,
    CommandType.DISARM: Event.DISARM,
    CommandType.SET_SPEED_LIMIT: Event.SET_SPEED_LIMIT,
    CommandType.SELECT_DRIVE: Event.SELECT_DRIVE,
    CommandType.SELECT_NEUTRAL: Event.SELECT_NEUTRAL,
    CommandType.SELECT_PTO: Event.SELECT_PTO,
    CommandType.MOVE_FORWARD: Event.MOVE_FORWARD,
    CommandType.MOVE_REVERSE: Event.MOVE_REVERSE,
    CommandType.TURN_LEFT: Event.TURN_LEFT,
    CommandType.TURN_RIGHT: Event.TURN_RIGHT,
    CommandType.STOP: Event.STOP,
    CommandType.EMERGENCY_STOP: Event.EMERGENCY_STOP,
    CommandType.PTO_START: Event.PTO_START,
    CommandType.PTO_STOP: Event.PTO_STOP,
    CommandType.FAULT_RESET: Event.FAULT_RESET,
    CommandType.EMERGENCY_STOP_RESET: Event.EMERGENCY_STOP_RESET,
}

ROVER_TO_CLIENT_TYPES = frozenset(
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
NO_RUNTIME_ACTION_TYPES = ROVER_TO_CLIENT_TYPES | {
    LogicalMessageType.SESSION_HELLO,
}
RESET_COMMANDS = frozenset(
    {
        CommandType.FAULT_RESET,
        CommandType.EMERGENCY_STOP_RESET,
    }
)
MOVE_COMMANDS = frozenset(
    {
        CommandType.MOVE_FORWARD,
        CommandType.MOVE_REVERSE,
    }
)
PTO_COMMANDS = frozenset(
    {
        CommandType.SELECT_PTO,
        CommandType.PTO_START,
        CommandType.PTO_STOP,
    }
)


class RuntimeInputAdapter:
    """Deterministic structural adapter with no sequence acceptance state."""

    def __init__(self) -> None:
        self._step_index = 0

    @property
    def step_index(self) -> int:
        return self._step_index

    def adapt(
        self,
        message: NormalizedLogicalMessage,
        context: ReceiverContext,
    ) -> AdapterResult:
        if not isinstance(message, NormalizedLogicalMessage):
            raise TypeError("message must be a NormalizedLogicalMessage")
        if not isinstance(context, ReceiverContext):
            raise TypeError("context must be a ReceiverContext")
        self._step_index += 1
        step_index = self._step_index

        message_type = self._enum_or_none(
            LogicalMessageType,
            message.logical_message_type,
        )
        message_type_label = self._label(message.logical_message_type)
        result_identity = {
            "message_id": (
                message.message_id
                if isinstance(message.message_id, str) and message.message_id
                else None
            ),
            "sequence": (
                message.sequence if type(message.sequence) is int else None
            ),
            "logical_message_type": message_type_label,
            "adapter_step_index": step_index,
        }

        if message.protocol_version != context.expected_protocol_version:
            return self._reject(
                **result_identity,
                reason="unsupported_version",
                diagnostic="UNSUPPORTED_PROTOCOL_VERSION",
            )
        if message_type is None:
            return self._reject(
                **result_identity,
                reason="invalid_message_type",
                diagnostic="UNKNOWN_LOGICAL_MESSAGE_TYPE",
            )

        direction = self._enum_or_none(MessageDirection, message.direction)
        if direction not in self._allowed_directions(message_type):
            return self._reject(
                **result_identity,
                reason="wrong_direction",
                diagnostic="MESSAGE_DIRECTION_MISMATCH",
            )

        sender_role = self._enum_or_none(SenderRole, message.sender_role)
        role_diagnostic = self._role_diagnostic(
            message_type,
            direction,
            sender_role,
        )
        if role_diagnostic is not None:
            return self._reject(
                **result_identity,
                reason="wrong_sender_role",
                diagnostic=role_diagnostic,
            )

        if message_type in NO_RUNTIME_ACTION_TYPES or (
            message_type is LogicalMessageType.SESSION_END
            and direction is MessageDirection.ROVER_TO_CLIENT
        ):
            return AdapterResult(
                AdapterDisposition.NO_RUNTIME_ACTION,
                None,
                None,
                result_identity["message_id"],
                result_identity["sequence"],
                message_type.value,
                None,
                None,
                False,
                step_index,
            )

        if message.rover_boot_id != context.current_rover_boot_id:
            return self._reject(
                **result_identity,
                reason="invalid_boot_id",
                diagnostic="ROVER_BOOT_ID_MISMATCH",
            )
        if message.session_id != context.active_session_id:
            return self._reject(
                **result_identity,
                reason="invalid_session",
                diagnostic="SESSION_ID_MISMATCH",
            )
        if not isinstance(message.sender_id, str) or not message.sender_id:
            return self._reject(
                **result_identity,
                reason="missing_required_field",
                diagnostic="SENDER_ID_REQUIRED",
            )
        if type(message.controller_ownership) is not bool:
            return self._reject(
                **result_identity,
                reason="missing_required_field",
                diagnostic="CONTROLLER_OWNERSHIP_BOOLEAN_REQUIRED",
            )

        if not message.controller_ownership:
            return self._reject(
                **result_identity,
                reason="not_control_owner",
                diagnostic="CONTROLLER_OWNERSHIP_REQUIRED",
            )
        if message.sender_id != context.active_controller_owner_id:
            return self._reject(
                **result_identity,
                reason="not_control_owner",
                diagnostic="CONTROLLER_OWNER_ID_MISMATCH",
            )

        if not isinstance(message.message_id, str) or not message.message_id:
            return self._reject(
                **result_identity,
                reason="missing_required_field",
                diagnostic="MESSAGE_ID_REQUIRED",
            )
        if (
            type(message.sequence) is not int
            or message.sequence < 0
            or message.sequence > context.max_safe_sequence
        ):
            return self._reject(
                **result_identity,
                reason="invalid_payload",
                diagnostic="SEQUENCE_OUT_OF_RANGE",
            )
        if (
            type(message.freshness_reference_ms) is not int
            or message.freshness_reference_ms < 0
        ):
            return self._reject(
                **result_identity,
                reason="invalid_payload",
                diagnostic="FRESHNESS_REFERENCE_INVALID",
            )
        if type(message.ttl_ms) is not int or message.ttl_ms <= 0:
            return self._reject(
                **result_identity,
                reason="invalid_payload",
                diagnostic="TTL_INVALID",
            )
        if message.ttl_ms > context.max_ttl_ms:
            return self._reject(
                **result_identity,
                reason="invalid_payload",
                diagnostic="TTL_LIMIT_EXCEEDED",
            )

        if message_type is LogicalMessageType.COMMAND:
            return self._adapt_command(
                message,
                context,
                step_index,
            )
        if message_type is LogicalMessageType.CONTROL_UPDATE:
            return self._adapt_control_update(
                message,
                context,
                step_index,
            )
        if message_type is LogicalMessageType.SESSION_END:
            return self._adapt_session_end(message, context, step_index)
        raise AssertionError(f"unhandled logical message type {message_type.value}")

    def internal_error_result(
        self,
        message: object,
        *,
        previous_step_index: int,
    ) -> AdapterResult:
        """Create an explicit fail-closed result for an unexpected bridge error."""
        self._step_index = max(self._step_index, previous_step_index + 1)
        message_id = getattr(message, "message_id", None)
        sequence = getattr(message, "sequence", None)
        message_type = getattr(message, "logical_message_type", None)
        return AdapterResult(
            AdapterDisposition.REJECTED,
            "internal_error",
            "ADAPTER_INTERNAL_ERROR",
            message_id if isinstance(message_id, str) and message_id else None,
            sequence if type(sequence) is int else None,
            self._label(message_type),
            None,
            None,
            False,
            self._step_index,
            True,
        )

    def _adapt_command(
        self,
        message: NormalizedLogicalMessage,
        context: ReceiverContext,
        step_index: int,
    ) -> AdapterResult:
        if not isinstance(message.payload, CommandPayload):
            return self._message_reject(
                message,
                step_index,
                "missing_required_field",
                "COMMAND_PAYLOAD_REQUIRED",
            )
        payload = message.payload
        command_type = self._enum_or_none(CommandType, payload.command_type)
        if command_type is None:
            return self._message_reject(
                message,
                step_index,
                "invalid_payload",
                "UNKNOWN_COMMAND_TYPE",
            )

        payload_diagnostic = self._command_payload_diagnostic(
            command_type,
            payload,
            context,
        )
        if payload_diagnostic is not None:
            reason = (
                "capability_unavailable"
                if payload_diagnostic.endswith("_UNAVAILABLE")
                else "invalid_payload"
            )
            return self._message_reject(
                message,
                step_index,
                reason,
                payload_diagnostic,
            )

        event = COMMAND_EVENT_MAP[command_type]
        values: dict[str, object] = {}
        if command_type in MOVE_COMMANDS:
            values["requested_speed"] = payload.requested_speed
        elif command_type is CommandType.SET_SPEED_LIMIT:
            values["speed_limit"] = payload.speed_limit
        elif command_type in RESET_COMMANDS:
            values["safety_confirmation"] = payload.safety_confirmation
        runtime_input = RuntimeInput.command(
            event,
            sequence=message.sequence,
            now_ms=context.current_monotonic_time_ms,
            issued_at_ms=message.freshness_reference_ms,
            ttl_ms=message.ttl_ms,
            session_id=message.session_id,
            **values,
        )
        return AdapterResult(
            AdapterDisposition.RUNTIME_INPUT_READY,
            None,
            None,
            message.message_id,
            message.sequence,
            LogicalMessageType.COMMAND.value,
            event.value,
            runtime_input,
            False,
            step_index,
        )

    def _adapt_control_update(
        self,
        message: NormalizedLogicalMessage,
        context: ReceiverContext,
        step_index: int,
    ) -> AdapterResult:
        if not isinstance(message.payload, ControlUpdatePayload):
            return self._message_reject(
                message,
                step_index,
                "missing_required_field",
                "CONTROL_UPDATE_PAYLOAD_REQUIRED",
            )
        payload = message.payload
        if not isinstance(payload.operation_id, str) or not payload.operation_id:
            return self._message_reject(
                message,
                step_index,
                "missing_required_field",
                "OPERATION_ID_REQUIRED",
            )
        if type(payload.deadman_asserted) is not bool:
            return self._message_reject(
                message,
                step_index,
                "missing_required_field",
                "DEADMAN_BOOLEAN_REQUIRED",
            )
        runtime_input = RuntimeInput.command(
            Event.CONTROL_UPDATE,
            sequence=message.sequence,
            now_ms=context.current_monotonic_time_ms,
            issued_at_ms=message.freshness_reference_ms,
            ttl_ms=message.ttl_ms,
            session_id=message.session_id,
            operation_id=payload.operation_id,
            deadman_asserted=payload.deadman_asserted,
        )
        return AdapterResult(
            AdapterDisposition.RUNTIME_INPUT_READY,
            None,
            None,
            message.message_id,
            message.sequence,
            LogicalMessageType.CONTROL_UPDATE.value,
            Event.CONTROL_UPDATE.value,
            runtime_input,
            payload.deadman_asserted,
            step_index,
        )

    def _adapt_session_end(
        self,
        message: NormalizedLogicalMessage,
        context: ReceiverContext,
        step_index: int,
    ) -> AdapterResult:
        if message.payload is not None and not isinstance(
            message.payload,
            SessionEndPayload,
        ):
            return self._message_reject(
                message,
                step_index,
                "invalid_payload",
                "SESSION_END_PAYLOAD_TYPE_MISMATCH",
            )
        runtime_input = RuntimeInput.command(
            Event.SESSION_END,
            sequence=message.sequence,
            now_ms=context.current_monotonic_time_ms,
            issued_at_ms=message.freshness_reference_ms,
            ttl_ms=message.ttl_ms,
            session_id=message.session_id,
        )
        return AdapterResult(
            AdapterDisposition.RUNTIME_INPUT_READY,
            None,
            None,
            message.message_id,
            message.sequence,
            LogicalMessageType.SESSION_END.value,
            Event.SESSION_END.value,
            runtime_input,
            False,
            step_index,
        )

    @staticmethod
    def _command_payload_diagnostic(
        command_type: CommandType,
        payload: CommandPayload,
        context: ReceiverContext,
    ) -> str | None:
        if command_type in MOVE_COMMANDS:
            if payload.speed_limit is not None or payload.safety_confirmation is not None:
                return "COMMAND_FORBIDDEN_FIELD_PRESENT"
            speed = payload.requested_speed
            if type(speed) is not int or not 1 <= speed <= context.max_speed:
                return "MOVE_SPEED_INVALID"
            if not context.drive_available:
                return "DRIVE_UNAVAILABLE"
            return None
        if command_type is CommandType.SET_SPEED_LIMIT:
            if (
                payload.requested_speed is not None
                or payload.safety_confirmation is not None
            ):
                return "COMMAND_FORBIDDEN_FIELD_PRESENT"
            limit = payload.speed_limit
            if type(limit) is not int or not 1 <= limit <= context.max_speed:
                return "SPEED_LIMIT_INVALID"
            return None
        if command_type in RESET_COMMANDS:
            if payload.requested_speed is not None or payload.speed_limit is not None:
                return "COMMAND_FORBIDDEN_FIELD_PRESENT"
            if type(payload.safety_confirmation) is not bool:
                return "SAFETY_CONFIRMATION_BOOLEAN_REQUIRED"
            return None
        if (
            payload.requested_speed is not None
            or payload.speed_limit is not None
            or payload.safety_confirmation is not None
        ):
            return "COMMAND_FORBIDDEN_FIELD_PRESENT"
        if command_type is CommandType.SELECT_DRIVE and not context.drive_available:
            return "DRIVE_UNAVAILABLE"
        if command_type is CommandType.TURN_LEFT and not context.turn_left_available:
            return "TURN_LEFT_UNAVAILABLE"
        if command_type is CommandType.TURN_RIGHT and not context.turn_right_available:
            return "TURN_RIGHT_UNAVAILABLE"
        if command_type in PTO_COMMANDS and not context.pto_available:
            return "PTO_UNAVAILABLE"
        return None

    @staticmethod
    def _allowed_directions(
        message_type: LogicalMessageType,
    ) -> frozenset[MessageDirection]:
        if message_type is LogicalMessageType.SESSION_HELLO:
            return frozenset({MessageDirection.CLIENT_TO_ROVER})
        if message_type is LogicalMessageType.SESSION_END:
            return frozenset(
                {
                    MessageDirection.CONTROLLER_TO_ROVER,
                    MessageDirection.ROVER_TO_CLIENT,
                }
            )
        if message_type in ROVER_TO_CLIENT_TYPES:
            return frozenset({MessageDirection.ROVER_TO_CLIENT})
        return frozenset({MessageDirection.CONTROLLER_TO_ROVER})

    @staticmethod
    def _role_diagnostic(
        message_type: LogicalMessageType,
        direction: MessageDirection,
        role: SenderRole | None,
    ) -> str | None:
        if direction is MessageDirection.ROVER_TO_CLIENT:
            return None if role is SenderRole.ROVER else "ROVER_SENDER_ROLE_REQUIRED"
        if message_type is LogicalMessageType.SESSION_HELLO:
            return (
                None
                if role in {SenderRole.CONTROLLER, SenderRole.OBSERVER}
                else "CLIENT_SENDER_ROLE_REQUIRED"
            )
        return (
            None
            if role is SenderRole.CONTROLLER
            else "CONTROLLER_SENDER_ROLE_REQUIRED"
        )

    @staticmethod
    def _enum_or_none(enum_type, value):
        if isinstance(value, enum_type):
            return value
        try:
            return enum_type(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _label(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None

    def _message_reject(
        self,
        message: NormalizedLogicalMessage,
        step_index: int,
        reason: str,
        diagnostic: str,
    ) -> AdapterResult:
        return self._reject(
            message_id=(
                message.message_id
                if isinstance(message.message_id, str) and message.message_id
                else None
            ),
            sequence=message.sequence if type(message.sequence) is int else None,
            logical_message_type=self._label(message.logical_message_type),
            adapter_step_index=step_index,
            reason=reason,
            diagnostic=diagnostic,
        )

    @staticmethod
    def _reject(
        *,
        message_id: str | None,
        sequence: int | None,
        logical_message_type: str | None,
        adapter_step_index: int,
        reason: str,
        diagnostic: str,
    ) -> AdapterResult:
        return AdapterResult(
            AdapterDisposition.REJECTED,
            reason,
            diagnostic,
            message_id,
            sequence,
            logical_message_type,
            None,
            None,
            False,
            adapter_step_index,
        )
