from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT))

from software.rover_control.protocol.v0.runtime_adapter import (  # noqa: E402
    AdapterDisposition,
    CommandPayload,
    CommandType,
    ControlUpdatePayload,
    LogicalMessageType,
    MessageDirection,
    NormalizedLogicalMessage,
    OpaquePayload,
    ReceiverContext,
    RuntimeInputAdapter,
    SenderRole,
    SessionEndPayload,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    Event,
    RuntimeConfig,
    RuntimeStateMachine,
)


MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


def receiver_context(**overrides) -> ReceiverContext:
    values = {
        "expected_protocol_version": "v0",
        "current_rover_boot_id": "boot-1",
        "active_session_id": "session-1",
        "active_controller_owner_id": "controller-1",
        "current_monotonic_time_ms": 10,
        "max_ttl_ms": 5_000,
        "max_safe_sequence": MAX_SAFE_SEQUENCE,
        "runtime_profile": "one_side_test",
        "max_speed": 100,
        "drive_available": True,
        "turn_left_available": False,
        "turn_right_available": False,
        "pto_available": False,
        "right_output_available": False,
    }
    values.update(overrides)
    return ReceiverContext(**values)


def logical_message(**overrides) -> NormalizedLogicalMessage:
    values = {
        "protocol_version": "v0",
        "logical_message_type": LogicalMessageType.COMMAND,
        "direction": MessageDirection.CONTROLLER_TO_ROVER,
        "rover_boot_id": "boot-1",
        "session_id": "session-1",
        "sender_id": "controller-1",
        "sender_role": SenderRole.CONTROLLER,
        "controller_ownership": True,
        "message_id": "message-1",
        "sequence": 1,
        "freshness_reference_ms": 0,
        "ttl_ms": 1_000,
        "payload": CommandPayload(CommandType.STOP),
    }
    values.update(overrides)
    return NormalizedLogicalMessage(**values)


def valid_payload(command_type: CommandType) -> CommandPayload:
    if command_type in {CommandType.MOVE_FORWARD, CommandType.MOVE_REVERSE}:
        return CommandPayload(command_type, requested_speed=20)
    if command_type is CommandType.SET_SPEED_LIMIT:
        return CommandPayload(command_type, speed_limit=40)
    if command_type in {
        CommandType.FAULT_RESET,
        CommandType.EMERGENCY_STOP_RESET,
    }:
        return CommandPayload(command_type, safety_confirmation=True)
    return CommandPayload(command_type)


class RuntimeInputAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = RuntimeInputAdapter()
        self.context = receiver_context()

    def test_all_16_commands_map_to_existing_runtime_events(self):
        all_capabilities = receiver_context(
            runtime_profile="drive_pto_split_fixture",
            turn_left_available=True,
            turn_right_available=True,
            pto_available=True,
        )
        expected = {
            command.value: command.value
            for command in CommandType
        }
        self.assertEqual(16, len(expected))
        for command in CommandType:
            with self.subTest(command=command.value):
                result = self.adapter.adapt(
                    logical_message(
                        message_id=f"message-{command.value}",
                        payload=valid_payload(command),
                    ),
                    all_capabilities,
                )
                self.assertEqual(
                    AdapterDisposition.RUNTIME_INPUT_READY,
                    result.disposition,
                )
                self.assertEqual(expected[command.value], result.mapped_event)
                self.assertEqual(expected[command.value], result.runtime_input.event.value)

    def test_command_specific_required_payload_fields_are_enforced(self):
        cases = (
            (
                CommandPayload(CommandType.MOVE_FORWARD),
                "MOVE_SPEED_INVALID",
            ),
            (
                CommandPayload(CommandType.MOVE_REVERSE),
                "MOVE_SPEED_INVALID",
            ),
            (
                CommandPayload(CommandType.SET_SPEED_LIMIT),
                "SPEED_LIMIT_INVALID",
            ),
            (
                CommandPayload(CommandType.FAULT_RESET),
                "SAFETY_CONFIRMATION_BOOLEAN_REQUIRED",
            ),
            (
                CommandPayload(CommandType.EMERGENCY_STOP_RESET),
                "SAFETY_CONFIRMATION_BOOLEAN_REQUIRED",
            ),
        )
        for payload, diagnostic in cases:
            with self.subTest(command=payload.command_type):
                result = self.adapter.adapt(
                    logical_message(payload=payload),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_command_specific_forbidden_fields_are_rejected(self):
        cases = (
            CommandPayload(
                CommandType.MOVE_FORWARD,
                requested_speed=20,
                speed_limit=40,
            ),
            CommandPayload(
                CommandType.SET_SPEED_LIMIT,
                requested_speed=20,
                speed_limit=40,
            ),
            CommandPayload(CommandType.STOP, requested_speed=20),
            CommandPayload(CommandType.ARM, speed_limit=40),
            CommandPayload(CommandType.DISARM, safety_confirmation=True),
            CommandPayload(
                CommandType.FAULT_RESET,
                requested_speed=20,
                safety_confirmation=True,
            ),
        )
        for payload in cases:
            with self.subTest(command=payload.command_type):
                result = self.adapter.adapt(
                    logical_message(payload=payload),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(
                    "COMMAND_FORBIDDEN_FIELD_PRESENT",
                    result.diagnostic_code,
                )

    def test_unknown_command_and_missing_command_payload_are_rejected(self):
        cases = (
            (None, "COMMAND_PAYLOAD_REQUIRED"),
            (CommandPayload("NOT_A_COMMAND"), "UNKNOWN_COMMAND_TYPE"),
        )
        for payload, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(payload=payload),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(diagnostic, result.diagnostic_code)
                self.assertIsNone(result.runtime_input)

    def test_envelope_version_and_direction_are_exact(self):
        cases = (
            (
                {"protocol_version": "v1"},
                "unsupported_version",
                "UNSUPPORTED_PROTOCOL_VERSION",
            ),
            (
                {"direction": MessageDirection.ROVER_TO_CLIENT},
                "wrong_direction",
                "MESSAGE_DIRECTION_MISMATCH",
            ),
            (
                {"logical_message_type": "UNKNOWN"},
                "invalid_message_type",
                "UNKNOWN_LOGICAL_MESSAGE_TYPE",
            ),
        )
        for overrides, reason, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(**overrides),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(reason, result.rejection_reason)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_boot_and_session_must_match_receiver_context(self):
        cases = (
            (
                {"rover_boot_id": "old-boot"},
                "invalid_boot_id",
                "ROVER_BOOT_ID_MISMATCH",
            ),
            (
                {"session_id": "old-session"},
                "invalid_session",
                "SESSION_ID_MISMATCH",
            ),
        )
        for overrides, reason, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(**overrides),
                    self.context,
                )
                self.assertEqual(reason, result.rejection_reason)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_sender_role_ownership_owner_and_message_id_are_required(self):
        cases = (
            (
                {"sender_role": SenderRole.OBSERVER},
                "wrong_sender_role",
                "CONTROLLER_SENDER_ROLE_REQUIRED",
            ),
            (
                {"controller_ownership": False},
                "not_control_owner",
                "CONTROLLER_OWNERSHIP_REQUIRED",
            ),
            (
                {"sender_id": "controller-2"},
                "not_control_owner",
                "CONTROLLER_OWNER_ID_MISMATCH",
            ),
            (
                {"sender_id": ""},
                "missing_required_field",
                "SENDER_ID_REQUIRED",
            ),
            (
                {"message_id": ""},
                "missing_required_field",
                "MESSAGE_ID_REQUIRED",
            ),
        )
        for overrides, reason, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(**overrides),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(reason, result.rejection_reason)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_sequence_accepts_exact_integers_at_safe_boundaries(self):
        for sequence in (0, 1, MAX_SAFE_SEQUENCE):
            with self.subTest(sequence=sequence):
                result = self.adapter.adapt(
                    logical_message(sequence=sequence),
                    self.context,
                )
                self.assertEqual(
                    AdapterDisposition.RUNTIME_INPUT_READY,
                    result.disposition,
                )
                self.assertEqual(sequence, result.runtime_input.sequence)

    def test_sequence_rejects_negative_overflow_and_non_integer_values(self):
        values = (
            -1,
            MAX_SAFE_SEQUENCE + 1,
            1.0,
            "1",
            True,
            None,
        )
        for sequence in values:
            with self.subTest(sequence=sequence):
                result = self.adapter.adapt(
                    logical_message(sequence=sequence),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual("SEQUENCE_OUT_OF_RANGE", result.diagnostic_code)

    def test_ttl_and_freshness_valid_values_pass_through_unchanged(self):
        result = self.adapter.adapt(
            logical_message(
                freshness_reference_ms=7,
                ttl_ms=5_000,
            ),
            self.context,
        )
        self.assertEqual(AdapterDisposition.RUNTIME_INPUT_READY, result.disposition)
        self.assertEqual(7, result.runtime_input.issued_at_ms)
        self.assertEqual(10, result.runtime_input.now_ms)
        self.assertEqual(5_000, result.runtime_input.ttl_ms)

    def test_ttl_and_freshness_invalid_values_are_rejected(self):
        cases = (
            ({"freshness_reference_ms": -1}, "FRESHNESS_REFERENCE_INVALID"),
            ({"freshness_reference_ms": 1.0}, "FRESHNESS_REFERENCE_INVALID"),
            ({"freshness_reference_ms": True}, "FRESHNESS_REFERENCE_INVALID"),
            ({"ttl_ms": 0}, "TTL_INVALID"),
            ({"ttl_ms": -1}, "TTL_INVALID"),
            ({"ttl_ms": 5_001}, "TTL_LIMIT_EXCEEDED"),
            ({"ttl_ms": 1.0}, "TTL_INVALID"),
            ({"ttl_ms": "1000"}, "TTL_INVALID"),
            ({"ttl_ms": True}, "TTL_INVALID"),
        )
        for overrides, diagnostic in cases:
            with self.subTest(overrides=overrides):
                result = self.adapter.adapt(
                    logical_message(**overrides),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_expiry_is_delegated_to_runtime(self):
        context = receiver_context(current_monotonic_time_ms=1_000)
        adapted = self.adapter.adapt(
            logical_message(
                freshness_reference_ms=0,
                ttl_ms=100,
            ),
            context,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            adapted.disposition,
        )
        runtime = RuntimeStateMachine(RuntimeConfig(session_id="session-1"))
        runtime_result = runtime.step(adapted.runtime_input)
        self.assertFalse(runtime_result.accepted)
        self.assertEqual("expired", runtime_result.rejection_reason)

    def test_move_speed_is_exact_integer_with_no_coercion_or_clamp(self):
        values = (None, 0, -1, 101, True, "20", 20.0)
        for speed in values:
            with self.subTest(speed=speed):
                result = self.adapter.adapt(
                    logical_message(
                        payload=CommandPayload(
                            CommandType.MOVE_FORWARD,
                            requested_speed=speed,
                        )
                    ),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual("MOVE_SPEED_INVALID", result.diagnostic_code)
        valid = self.adapter.adapt(
            logical_message(
                payload=CommandPayload(
                    CommandType.MOVE_REVERSE,
                    requested_speed=100,
                )
            ),
            self.context,
        )
        self.assertEqual(AdapterDisposition.RUNTIME_INPUT_READY, valid.disposition)
        self.assertEqual(100, valid.runtime_input.requested_speed)

    def test_speed_limit_is_exact_integer_and_cannot_mix_with_move_speed(self):
        invalid_values = (None, 0, -1, 101, True, "40", 40.0)
        for limit in invalid_values:
            with self.subTest(limit=limit):
                result = self.adapter.adapt(
                    logical_message(
                        payload=CommandPayload(
                            CommandType.SET_SPEED_LIMIT,
                            speed_limit=limit,
                        )
                    ),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
        valid = self.adapter.adapt(
            logical_message(
                payload=CommandPayload(
                    CommandType.SET_SPEED_LIMIT,
                    speed_limit=100,
                )
            ),
            self.context,
        )
        self.assertEqual(100, valid.runtime_input.speed_limit)

    def test_control_update_maps_operation_and_explicit_deadman_boolean(self):
        for deadman in (True, False):
            with self.subTest(deadman=deadman):
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=LogicalMessageType.CONTROL_UPDATE,
                        payload=ControlUpdatePayload("operation-1", deadman),
                    ),
                    self.context,
                )
                self.assertEqual(
                    AdapterDisposition.RUNTIME_INPUT_READY,
                    result.disposition,
                )
                self.assertEqual(Event.CONTROL_UPDATE.value, result.mapped_event)
                self.assertEqual("operation-1", result.runtime_input.operation_id)
                self.assertIs(deadman, result.runtime_input.deadman_asserted)
                self.assertEqual(deadman, result.control_liveness_candidate)

    def test_control_update_rejects_missing_or_invalid_payload_members(self):
        cases = (
            (None, "CONTROL_UPDATE_PAYLOAD_REQUIRED"),
            (ControlUpdatePayload(None, True), "OPERATION_ID_REQUIRED"),
            (ControlUpdatePayload("", True), "OPERATION_ID_REQUIRED"),
            (ControlUpdatePayload("operation-1", None), "DEADMAN_BOOLEAN_REQUIRED"),
            (ControlUpdatePayload("operation-1", 1), "DEADMAN_BOOLEAN_REQUIRED"),
            (ControlUpdatePayload("operation-1", "true"), "DEADMAN_BOOLEAN_REQUIRED"),
        )
        for payload, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=LogicalMessageType.CONTROL_UPDATE,
                        payload=payload,
                    ),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_session_end_accepts_none_or_explicit_empty_payload(self):
        for payload in (None, SessionEndPayload()):
            with self.subTest(payload=payload):
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=LogicalMessageType.SESSION_END,
                        payload=payload,
                    ),
                    self.context,
                )
                self.assertEqual(
                    AdapterDisposition.RUNTIME_INPUT_READY,
                    result.disposition,
                )
                self.assertEqual(Event.SESSION_END.value, result.mapped_event)

    def test_payload_type_mismatch_is_rejected(self):
        cases = (
            (
                LogicalMessageType.COMMAND,
                ControlUpdatePayload("operation-1", True),
            ),
            (
                LogicalMessageType.CONTROL_UPDATE,
                CommandPayload(CommandType.STOP),
            ),
            (
                LogicalMessageType.SESSION_END,
                CommandPayload(CommandType.STOP),
            ),
        )
        for message_type, payload in cases:
            with self.subTest(message_type=message_type.value):
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=message_type,
                        payload=payload,
                    ),
                    self.context,
                )
                self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
                self.assertIsNone(result.runtime_input)

    def test_unavailable_turn_pto_and_drive_capabilities_reject_before_runtime(self):
        cases = (
            (
                receiver_context(drive_available=False),
                CommandPayload(CommandType.MOVE_FORWARD, requested_speed=20),
                "DRIVE_UNAVAILABLE",
            ),
            (
                receiver_context(drive_available=False),
                CommandPayload(CommandType.SELECT_DRIVE),
                "DRIVE_UNAVAILABLE",
            ),
            (
                self.context,
                CommandPayload(CommandType.TURN_LEFT),
                "TURN_LEFT_UNAVAILABLE",
            ),
            (
                self.context,
                CommandPayload(CommandType.TURN_RIGHT),
                "TURN_RIGHT_UNAVAILABLE",
            ),
            (
                self.context,
                CommandPayload(CommandType.SELECT_PTO),
                "PTO_UNAVAILABLE",
            ),
            (
                self.context,
                CommandPayload(CommandType.PTO_START),
                "PTO_UNAVAILABLE",
            ),
            (
                self.context,
                CommandPayload(CommandType.PTO_STOP),
                "PTO_UNAVAILABLE",
            ),
        )
        for context, payload, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                result = self.adapter.adapt(
                    logical_message(payload=payload),
                    context,
                )
                self.assertEqual(
                    "capability_unavailable",
                    result.rejection_reason,
                )
                self.assertEqual(diagnostic, result.diagnostic_code)

    def test_session_hello_new_candidate_is_not_bound_to_active_session(self):
        result = self.adapter.adapt(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_HELLO,
                direction=MessageDirection.CLIENT_TO_ROVER,
                session_id="candidate-session-2",
                controller_ownership=False,
                payload=OpaquePayload({"requested_role": "controller"}),
            ),
            self.context,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            result.disposition,
        )
        self.assertIsNone(result.runtime_input)
        self.assertEqual("session-1", self.context.active_session_id)

    def test_session_accepted_new_notification_does_not_install_session(self):
        result = self.adapter.adapt(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_ACCEPTED,
                direction=MessageDirection.ROVER_TO_CLIENT,
                session_id="notified-session-2",
                sender_id="rover-1",
                sender_role=SenderRole.ROVER,
                controller_ownership=False,
                payload=OpaquePayload({"selected_version": "v0"}),
            ),
            self.context,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            result.disposition,
        )
        self.assertIsNone(result.runtime_input)
        self.assertEqual("session-1", self.context.active_session_id)

    def test_session_rejected_without_established_session_is_no_runtime_action(self):
        result = self.adapter.adapt(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_REJECTED,
                direction=MessageDirection.ROVER_TO_CLIENT,
                session_id=None,
                sender_id="rover-1",
                sender_role=SenderRole.ROVER,
                controller_ownership=False,
                payload=OpaquePayload({"reason": "controller_active"}),
            ),
            self.context,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            result.disposition,
        )
        self.assertIsNone(result.runtime_input)

    def test_runtime_inert_message_types_accept_opaque_unexpanded_payload(self):
        message_types = (
            LogicalMessageType.TELEMETRY,
            LogicalMessageType.STATE_SNAPSHOT,
            LogicalMessageType.COMMAND_RESULT,
            LogicalMessageType.DIAGNOSTIC,
        )
        for message_type in message_types:
            with self.subTest(message_type=message_type.value):
                payload = OpaquePayload(
                    {
                        "private_fixture_value": ["must", "remain", "opaque"],
                    }
                )
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=message_type,
                        direction=MessageDirection.ROVER_TO_CLIENT,
                        session_id="unbound-notification-session",
                        sender_id="rover-1",
                        sender_role=SenderRole.ROVER,
                        controller_ownership=False,
                        payload=payload,
                    ),
                    self.context,
                )
                self.assertEqual(
                    AdapterDisposition.NO_RUNTIME_ACTION,
                    result.disposition,
                )
                self.assertIsNone(result.runtime_input)
                self.assertNotIn(
                    "private_fixture_value",
                    json.dumps(result.report_dict()),
                )

    def test_opaque_payload_fixture_is_deep_read_only(self):
        payload = OpaquePayload(
            {
                "nested": ["value", {"count": 1}],
            }
        )
        self.assertEqual("value", payload.content["nested"][0])
        self.assertEqual(1, payload.content["nested"][1]["count"])
        with self.assertRaises(TypeError):
            payload.content["nested"] = ()
        with self.assertRaises(TypeError):
            payload.content["nested"][1]["count"] = 2

    def test_all_nine_non_runtime_message_types_are_explicitly_classified(self):
        rover_types = (
            LogicalMessageType.SESSION_ACCEPTED,
            LogicalMessageType.SESSION_REJECTED,
            LogicalMessageType.CAPABILITY_SNAPSHOT,
            LogicalMessageType.COMMAND_RESULT,
            LogicalMessageType.STATE_SNAPSHOT,
            LogicalMessageType.TELEMETRY,
            LogicalMessageType.ROVER_HEARTBEAT,
            LogicalMessageType.DIAGNOSTIC,
        )
        cases = (
            (
                LogicalMessageType.SESSION_HELLO,
                MessageDirection.CLIENT_TO_ROVER,
                "controller-1",
                SenderRole.CONTROLLER,
                False,
            ),
            *(
                (
                    message_type,
                    MessageDirection.ROVER_TO_CLIENT,
                    "rover-1",
                    SenderRole.ROVER,
                    False,
                )
                for message_type in rover_types
            ),
        )
        self.assertEqual(9, len(cases))
        for message_type, direction, sender_id, role, ownership in cases:
            with self.subTest(message_type=message_type.value):
                result = self.adapter.adapt(
                    logical_message(
                        logical_message_type=message_type,
                        direction=direction,
                        sender_id=sender_id,
                        sender_role=role,
                        controller_ownership=ownership,
                        payload=None,
                    ),
                    self.context,
                )
                self.assertEqual(
                    AdapterDisposition.NO_RUNTIME_ACTION,
                    result.disposition,
                )
                self.assertIsNone(result.runtime_input)

    def test_rover_to_client_only_type_cannot_be_presented_controller_to_rover(self):
        result = self.adapter.adapt(
            logical_message(
                logical_message_type=LogicalMessageType.COMMAND_RESULT,
                direction=MessageDirection.CONTROLLER_TO_ROVER,
                payload=None,
            ),
            self.context,
        )
        self.assertEqual(AdapterDisposition.REJECTED, result.disposition)
        self.assertEqual("wrong_direction", result.rejection_reason)
        self.assertIsNone(result.runtime_input)

    def test_adapter_step_index_is_deterministic_and_not_a_sequence_namespace(self):
        first = self.adapter.adapt(logical_message(sequence=50), self.context)
        second = self.adapter.adapt(logical_message(sequence=1), self.context)
        self.assertEqual(1, first.adapter_step_index)
        self.assertEqual(2, second.adapter_step_index)
        self.assertEqual(AdapterDisposition.RUNTIME_INPUT_READY, first.disposition)
        self.assertEqual(AdapterDisposition.RUNTIME_INPUT_READY, second.disposition)


if __name__ == "__main__":
    unittest.main(verbosity=2)
