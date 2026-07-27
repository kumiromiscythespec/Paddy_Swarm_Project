from __future__ import annotations

import copy
import sys
import unittest
from collections import UserDict
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT))

from software.rover_control.protocol.v0.message_normalizer import (  # noqa: E402
    CandidateIntent,
    NormalizationDisposition,
    NormalizerPolicy,
    ReceivedLogicalObject,
    StrictLogicalMessageNormalizer,
)
from software.rover_control.protocol.v0.runtime_adapter import (  # noqa: E402
    CommandPayload,
    CommandType,
    ControlUpdatePayload,
    LogicalMessageType,
    MessageDirection,
    SessionEndPayload,
)
from software.rover_control.protocol.v0.session_negotiation import (  # noqa: E402
    SessionCandidate,
    SessionRole,
)


MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


def policy() -> NormalizerPolicy:
    return NormalizerPolicy(
        max_message_size_bytes=1_000,
        expected_protocol_version="v0",
        current_rover_boot_id="boot-1",
        max_safe_sequence=MAX_SAFE_SEQUENCE,
        max_ttl_ms=5_000,
    )


def command_payload(command: CommandType) -> dict[str, object]:
    result: dict[str, object] = {"command_type": command.value}
    if command in {CommandType.MOVE_FORWARD, CommandType.MOVE_REVERSE}:
        result["requested_speed"] = 20
    elif command is CommandType.SET_SPEED_LIMIT:
        result["speed_limit"] = 40
    elif command in {
        CommandType.FAULT_RESET,
        CommandType.EMERGENCY_STOP_RESET,
    }:
        result["safety_confirmation"] = True
    return result


def runtime_fixture(
    command: CommandType = CommandType.STOP,
    **overrides,
) -> dict[str, object]:
    values: dict[str, object] = {
        "protocol_version": "v0",
        "logical_message_type": "COMMAND",
        "rover_boot_id": "boot-1",
        "session_id": "session-1",
        "sender_id": "controller-1",
        "sender_role": "controller",
        "controller_ownership": True,
        "message_id": "message-1",
        "sequence": 1,
        "freshness_reference_ms": 10,
        "ttl_ms": 1_000,
        "payload": command_payload(command),
    }
    values.update(overrides)
    return values


def control_fixture(**overrides) -> dict[str, object]:
    values = runtime_fixture()
    values.update(
        logical_message_type="CONTROL_UPDATE",
        payload={"operation_id": "operation-1", "deadman_asserted": True},
    )
    values.update(overrides)
    return values


def session_end_fixture(*, include_payload: bool = True, **overrides):
    values = runtime_fixture()
    values["logical_message_type"] = "SESSION_END"
    if include_payload:
        values["payload"] = {}
    else:
        del values["payload"]
    values.update(overrides)
    return values


def hello_fixture(**overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "logical_message_type": "SESSION_HELLO",
        "rover_boot_id": "boot-1",
        "sender_id": "controller-1",
        "sender_role": "controller",
        "message_id": "hello-1",
        "payload": {
            "protocol_versions": ["v0"],
            "requested_role": "controller",
            "candidate_session_id": "session-1",
            "sender_instance_id": "controller-instance-1",
            "human_switch_confirmation": False,
            "request_index": 1,
        },
    }
    values.update(overrides)
    return values


def received(
    decoded_object: object,
    *,
    direction: object = "controller_to_rover",
    size_bytes: object = 100,
    parse_succeeded: object = True,
) -> ReceivedLogicalObject:
    return ReceivedLogicalObject(
        direction=direction,
        size_bytes=size_bytes,
        parse_succeeded=parse_succeeded,
        decoded_object=decoded_object,
    )


class StrictLogicalMessageNormalizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = StrictLogicalMessageNormalizer(policy())

    def normalize(self, decoded, **metadata):
        return self.normalizer.normalize(received(decoded, **metadata))

    def assert_no_action(self, result) -> None:
        self.assertEqual(
            NormalizationDisposition.NO_MESSAGE_ACTION,
            result.disposition,
        )
        self.assertIsNone(result.normalized_message)
        self.assertIsNone(result.session_candidate)
        self.assertFalse(result.runtime_dispatch_permitted)

    def assert_rejected(self, result) -> None:
        self.assertEqual(NormalizationDisposition.REJECTED, result.disposition)
        self.assertIsNone(result.normalized_message)
        self.assertIsNone(result.session_candidate)
        self.assertFalse(result.runtime_dispatch_permitted)

    def test_size_gate_accepts_zero_and_exact_max(self):
        for size in (0, policy().max_message_size_bytes):
            with self.subTest(size=size):
                result = self.normalize(runtime_fixture(), size_bytes=size)
                self.assertEqual(
                    NormalizationDisposition.MESSAGE_NORMALIZED,
                    result.disposition,
                )

    def test_size_gate_rejects_invalid_metadata_without_action(self):
        for value in (-1, True, "100", 1.0):
            with self.subTest(value=value):
                self.assert_no_action(
                    self.normalize(runtime_fixture(), size_bytes=value)
                )

    def test_size_gate_rejects_oversize_without_intent(self):
        result = self.normalize(runtime_fixture(), size_bytes=1_001)
        self.assert_no_action(result)
        self.assertIsNone(result.candidate_intent)
        self.assertFalse(result.identification_gate_passed)

    def test_parse_false_does_not_inspect_decoded_object(self):
        class Bomb:
            def __getattribute__(self, name):
                raise AssertionError("decoded object was inspected")

        result = self.normalizer.normalize(
            received(Bomb(), parse_succeeded=False)
        )
        self.assert_no_action(result)
        self.assertFalse(result.internal_error)

    def test_parse_metadata_requires_exact_bool(self):
        for value in (0, 1, "true", None):
            with self.subTest(value=value):
                self.assert_no_action(
                    self.normalize(
                        runtime_fixture(),
                        parse_succeeded=value,
                    )
                )

    def test_decoded_root_requires_exact_dict(self):
        for value in (None, [], UserDict(runtime_fixture())):
            with self.subTest(type=type(value).__name__):
                self.assert_no_action(self.normalize(value))

    def test_root_unknown_alias_case_and_direction_spoof_are_rejected(self):
        cases = []
        for key, value in (
            ("unexpected", 1),
            ("sessionId", "session-1"),
            ("Session_ID", "session-1"),
            ("direction", "controller_to_rover"),
        ):
            fixture = runtime_fixture()
            fixture[key] = value
            cases.append(fixture)
        for fixture in cases:
            with self.subTest(key=next(reversed(fixture))):
                result = self.normalize(fixture)
                self.assert_rejected(result)
                self.assertEqual(
                    "UNKNOWN_TOP_LEVEL_PROPERTY",
                    result.diagnostic_code,
                )

    def test_root_missing_required_property_is_rejected(self):
        for key in runtime_fixture():
            with self.subTest(key=key):
                fixture = runtime_fixture()
                del fixture[key]
                result = self.normalize(fixture)
                if key == "logical_message_type":
                    self.assert_no_action(result)
                else:
                    self.assert_rejected(result)

    def test_root_null_does_not_supply_a_default(self):
        for key in ("session_id", "message_id", "sequence", "ttl_ms"):
            with self.subTest(key=key):
                result = self.normalize(runtime_fixture(**{key: None}))
                self.assert_rejected(result)

    def test_unknown_message_type_is_no_action(self):
        result = self.normalize(
            runtime_fixture(logical_message_type="command")
        )
        self.assert_no_action(result)
        self.assertEqual(
            "MESSAGE_TYPE_NOT_IDENTIFIABLE",
            result.diagnostic_code,
        )

    def test_direction_requires_exact_trusted_metadata(self):
        class DirectionString(str):
            pass

        for value in (
            DirectionString("controller_to_rover"),
            MessageDirection.CONTROLLER_TO_ROVER,
            "CONTROLLER_TO_ROVER",
            None,
        ):
            with self.subTest(value=repr(value)):
                self.assert_no_action(
                    self.normalize(runtime_fixture(), direction=value)
                )

    def test_rover_only_type_in_controller_direction_is_rejected(self):
        for message_type in (
            "SESSION_ACCEPTED",
            "SESSION_REJECTED",
            "CAPABILITY_SNAPSHOT",
            "COMMAND_RESULT",
            "STATE_SNAPSHOT",
            "TELEMETRY",
            "ROVER_HEARTBEAT",
            "DIAGNOSTIC",
        ):
            with self.subTest(message_type=message_type):
                result = self.normalize(
                    {"logical_message_type": message_type}
                )
                self.assert_rejected(result)
                self.assertEqual("wrong_direction", result.rejection_reason)

    def test_rover_only_type_in_rover_direction_is_no_action(self):
        result = self.normalize(
            {"logical_message_type": "TELEMETRY"},
            direction="rover_to_client",
        )
        self.assert_no_action(result)

    def test_scalar_exact_types_reject_bool_float_and_numeric_string(self):
        for key, value in (
            ("sequence", True),
            ("sequence", 1.0),
            ("sequence", "1"),
            ("ttl_ms", True),
            ("freshness_reference_ms", 1.0),
        ):
            with self.subTest(key=key, value=value):
                self.assert_rejected(
                    self.normalize(runtime_fixture(**{key: value}))
                )

    def test_string_subclass_is_not_implicitly_accepted(self):
        class FixtureString(str):
            pass

        result = self.normalize(
            runtime_fixture(session_id=FixtureString("session-1"))
        )
        self.assert_rejected(result)

    def test_all_16_commands_normalize_to_existing_command_type(self):
        self.assertEqual(16, len(CommandType))
        for command in CommandType:
            with self.subTest(command=command.value):
                result = self.normalize(
                    runtime_fixture(
                        command,
                        message_id=f"message-{command.value}",
                    )
                )
                self.assertEqual(
                    NormalizationDisposition.MESSAGE_NORMALIZED,
                    result.disposition,
                )
                self.assertIsInstance(
                    result.normalized_message.payload,
                    CommandPayload,
                )
                self.assertIs(
                    command,
                    result.normalized_message.payload.command_type,
                )

    def test_unknown_command_type_is_rejected(self):
        result = self.normalize(
            runtime_fixture(payload={"command_type": "stop"})
        )
        self.assert_rejected(result)
        self.assertEqual("UNKNOWN_COMMAND_TYPE", result.diagnostic_code)

    def test_command_required_property_is_not_defaulted(self):
        for command, required in (
            (CommandType.MOVE_FORWARD, "requested_speed"),
            (CommandType.MOVE_REVERSE, "requested_speed"),
            (CommandType.SET_SPEED_LIMIT, "speed_limit"),
            (CommandType.FAULT_RESET, "safety_confirmation"),
            (CommandType.EMERGENCY_STOP_RESET, "safety_confirmation"),
        ):
            with self.subTest(command=command.value):
                payload = command_payload(command)
                del payload[required]
                result = self.normalize(runtime_fixture(payload=payload))
                self.assert_rejected(result)
                self.assertEqual(
                    "MISSING_REQUIRED_PROPERTY",
                    result.diagnostic_code,
                )

    def test_command_forbidden_property_is_rejected(self):
        cases = (
            (CommandType.STOP, "requested_speed", 10),
            (CommandType.MOVE_FORWARD, "speed_limit", 10),
            (CommandType.SET_SPEED_LIMIT, "safety_confirmation", True),
            (CommandType.FAULT_RESET, "requested_speed", 10),
        )
        for command, key, value in cases:
            with self.subTest(command=command.value, key=key):
                payload = command_payload(command)
                payload[key] = value
                result = self.normalize(runtime_fixture(payload=payload))
                self.assert_rejected(result)
                self.assertEqual(
                    "FORBIDDEN_PROPERTY_PRESENT",
                    result.diagnostic_code,
                )

    def test_unknown_command_payload_property_is_rejected(self):
        result = self.normalize(
            runtime_fixture(
                payload={"command_type": "ARM", "request_speed": 10}
            )
        )
        self.assert_rejected(result)
        self.assertEqual(
            "UNKNOWN_COMMAND_PAYLOAD_PROPERTY",
            result.diagnostic_code,
        )

    def test_move_and_speed_limit_require_exact_int_without_range_clamp(self):
        cases = (
            (CommandType.MOVE_FORWARD, "requested_speed"),
            (CommandType.SET_SPEED_LIMIT, "speed_limit"),
        )
        for command, key in cases:
            for invalid in (True, "20", 20.0, None):
                with self.subTest(
                    command=command.value,
                    invalid=invalid,
                ):
                    payload = command_payload(command)
                    payload[key] = invalid
                    self.assert_rejected(
                        self.normalize(runtime_fixture(payload=payload))
                    )
            payload = command_payload(command)
            payload[key] = 10_000
            result = self.normalize(runtime_fixture(payload=payload))
            self.assertEqual(
                NormalizationDisposition.MESSAGE_NORMALIZED,
                result.disposition,
            )
            self.assertEqual(10_000, getattr(result.normalized_message.payload, key))

    def test_reset_confirmation_requires_exact_bool(self):
        for command in (
            CommandType.FAULT_RESET,
            CommandType.EMERGENCY_STOP_RESET,
        ):
            for invalid in (1, "true", None):
                with self.subTest(command=command.value, invalid=invalid):
                    payload = command_payload(command)
                    payload["safety_confirmation"] = invalid
                    self.assert_rejected(
                        self.normalize(runtime_fixture(payload=payload))
                    )

    def test_valid_control_update_normalizes(self):
        result = self.normalize(control_fixture())
        self.assertEqual(
            NormalizationDisposition.MESSAGE_NORMALIZED,
            result.disposition,
        )
        self.assertEqual(
            ControlUpdatePayload("operation-1", True),
            result.normalized_message.payload,
        )

    def test_control_update_closed_required_and_exact_type_rules(self):
        cases = (
            {"deadman_asserted": True},
            {"operation_id": "operation-1"},
            {"operation_id": "", "deadman_asserted": True},
            {"operation_id": "operation-1", "deadman_asserted": 1},
            {
                "operation_id": "operation-1",
                "deadman_asserted": True,
                "unknown": 1,
            },
        )
        for payload in cases:
            with self.subTest(payload=payload):
                self.assert_rejected(
                    self.normalize(control_fixture(payload=payload))
                )

    def test_session_end_absent_or_empty_payload_normalizes(self):
        for fixture in (
            session_end_fixture(include_payload=False),
            session_end_fixture(),
        ):
            with self.subTest(has_payload="payload" in fixture):
                result = self.normalize(fixture)
                self.assertEqual(
                    NormalizationDisposition.MESSAGE_NORMALIZED,
                    result.disposition,
                )
                self.assertIsInstance(
                    result.normalized_message.payload,
                    SessionEndPayload,
                )

    def test_session_end_nonempty_or_wrong_payload_is_rejected(self):
        for payload in ({"reason": "done"}, None, [], UserDict()):
            with self.subTest(payload=repr(payload)):
                self.assert_rejected(
                    self.normalize(session_end_fixture(payload=payload))
                )

    def test_valid_session_hello_normalizes_candidate(self):
        result = self.normalize(
            hello_fixture(),
            direction="client_to_rover",
        )
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            result.disposition,
        )
        self.assertIsInstance(result.session_candidate, SessionCandidate)
        self.assertEqual(("v0",), result.session_candidate.protocol_versions)
        self.assertIs(
            SessionRole.CONTROLLER,
            result.session_candidate.requested_role,
        )
        self.assertFalse(result.runtime_dispatch_permitted)

    def test_hello_versions_are_exact_nonempty_unique_list_or_tuple(self):
        class CustomIterable:
            def __iter__(self):
                raise AssertionError("must not iterate")

        cases = ([], (), ["v0", "v0"], [""], [1], CustomIterable())
        for versions in cases:
            with self.subTest(versions=repr(versions)):
                fixture = hello_fixture()
                fixture["payload"]["protocol_versions"] = versions
                self.assert_rejected(
                    self.normalize(
                        fixture,
                        direction="client_to_rover",
                    )
                )
        fixture = hello_fixture()
        fixture["payload"]["protocol_versions"] = ("v0",)
        result = self.normalize(fixture, direction="client_to_rover")
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            result.disposition,
        )

    def test_hello_role_and_identity_exact_rules(self):
        cases = (
            ("sender_id", ""),
            ("sender_role", "Controller"),
            ("message_id", None),
        )
        for key, value in cases:
            with self.subTest(key=key):
                self.assert_rejected(
                    self.normalize(
                        hello_fixture(**{key: value}),
                        direction="client_to_rover",
                    )
                )
        for key in ("candidate_session_id", "sender_instance_id"):
            fixture = hello_fixture()
            fixture["payload"][key] = ""
            self.assert_rejected(
                self.normalize(fixture, direction="client_to_rover")
            )

    def test_observer_hello_normalizes_for_manager_decision(self):
        fixture = hello_fixture(sender_role="observer")
        fixture["payload"]["requested_role"] = "observer"
        result = self.normalize(fixture, direction="client_to_rover")
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            result.disposition,
        )
        self.assertIs(
            SessionRole.OBSERVER,
            result.session_candidate.requested_role,
        )

    def test_hello_boot_and_version_support_are_delegated_to_manager(self):
        fixture = hello_fixture(rover_boot_id="boot-other")
        fixture["payload"]["protocol_versions"] = ["v-other"]
        result = self.normalize(fixture, direction="client_to_rover")
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            result.disposition,
        )
        self.assertEqual(
            "boot-other",
            result.session_candidate.rover_boot_id,
        )
        self.assertEqual(
            ("v-other",),
            result.session_candidate.protocol_versions,
        )

    def test_hello_request_index_and_confirmation_exact_rules(self):
        cases = (
            ("request_index", True),
            ("request_index", -1),
            ("request_index", "1"),
            ("human_switch_confirmation", 0),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value):
                fixture = hello_fixture()
                fixture["payload"][key] = value
                self.assert_rejected(
                    self.normalize(
                        fixture,
                        direction="client_to_rover",
                    )
                )

    def test_stop_and_estop_identification_gate_passes(self):
        for command, intent in (
            (CommandType.STOP, CandidateIntent.STOP),
            (CommandType.EMERGENCY_STOP, CandidateIntent.EMERGENCY_STOP),
        ):
            with self.subTest(command=command.value):
                result = self.normalize(runtime_fixture(command))
                self.assertIs(intent, result.candidate_intent)
                self.assertTrue(result.identification_gate_passed)
                self.assertFalse(result.defensive_zero_candidate)

    def test_identification_failures_do_not_infer_safety_intent(self):
        cases = (
            received(runtime_fixture(), size_bytes=1_001),
            received(runtime_fixture(), parse_succeeded=False),
            received(
                runtime_fixture(protocol_version="v1"),
            ),
            received(
                runtime_fixture(logical_message_type="CONTROL_UPDATE"),
            ),
            received(runtime_fixture(), direction="client_to_rover"),
            received(runtime_fixture(rover_boot_id="boot-old")),
            received(
                runtime_fixture(payload={"command_type": ["STOP"]}),
            ),
        )
        for case in cases:
            with self.subTest(case=case):
                result = self.normalizer.normalize(case)
                self.assertIsNone(result.candidate_intent)
                self.assertFalse(result.identification_gate_passed)
                self.assertFalse(result.defensive_zero_candidate)

    def test_post_gate_failures_preserve_candidate_classification(self):
        cases = (
            ("session_id", None),
            ("sequence", True),
            ("ttl_ms", 0),
            ("payload", {"command_type": "STOP", "unknown": 1}),
        )
        for key, value in cases:
            with self.subTest(key=key):
                result = self.normalize(runtime_fixture(**{key: value}))
                self.assert_rejected(result)
                self.assertIs(CandidateIntent.STOP, result.candidate_intent)
                self.assertTrue(result.identification_gate_passed)
                self.assertTrue(result.defensive_zero_candidate)

    def test_normalizer_result_report_does_not_expand_payload(self):
        fixture = runtime_fixture(
            payload={"command_type": "ARM", "secret": "do-not-report"}
        )
        report = repr(self.normalize(fixture).report_dict())
        self.assertNotIn("do-not-report", report)
        self.assertNotIn("secret", report)

    def test_step_index_is_deterministic_and_monotonic(self):
        first = self.normalize(runtime_fixture())
        second = self.normalize(runtime_fixture())
        self.assertEqual(1, first.normalizer_step_index)
        self.assertEqual(2, second.normalizer_step_index)

    def test_unexpected_programming_error_is_explicit_internal_error(self):
        result = self.normalizer.normalize(object())
        self.assertEqual(
            NormalizationDisposition.INTERNAL_ERROR,
            result.disposition,
        )
        self.assertTrue(result.internal_error)
        self.assertEqual("NORMALIZER_INTERNAL_ERROR", result.diagnostic_code)
        self.assertIsNone(result.normalized_message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
