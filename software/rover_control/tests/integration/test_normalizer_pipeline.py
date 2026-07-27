from __future__ import annotations

import hashlib
import os
import socket
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT))

from software.rover_control.protocol.v0.message_normalizer import (  # noqa: E402
    CandidateIntent,
    NormalizationDisposition,
    NormalizerPolicy,
    ReceivedLogicalObject,
    VirtualInputBoundary,
)
from software.rover_control.protocol.v0.runtime_adapter import (  # noqa: E402
    AdapterDisposition,
    CommandType,
)
from software.rover_control.protocol.v0.session_negotiation import (  # noqa: E402
    NegotiationDisposition,
    ReceiverPolicy,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    Profile,
    RoverState,
    RuntimeConfig,
)


MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


def make_boundary() -> VirtualInputBoundary:
    config = RuntimeConfig(
        profile=Profile.ONE_SIDE_TEST,
        max_command_ttl_ms=5_000,
        max_speed=100,
        session_id="runtime-bootstrap",
        real_motor_output_enabled=False,
    )
    normalizer_policy = NormalizerPolicy(
        max_message_size_bytes=4_096,
        expected_protocol_version="v0",
        current_rover_boot_id="boot-1",
        max_safe_sequence=MAX_SAFE_SEQUENCE,
        max_ttl_ms=config.max_command_ttl_ms,
    )
    receiver_policy = ReceiverPolicy(
        runtime_profile=config.profile.value,
        capability_profile_reference="one-side-test-capabilities-v0",
        max_ttl_ms=config.max_command_ttl_ms,
        max_safe_sequence=MAX_SAFE_SEQUENCE,
        max_speed=config.max_speed,
        drive_available=True,
        turn_left_available=False,
        turn_right_available=False,
        pto_available=False,
        right_output_available=False,
    )
    return VirtualInputBoundary(
        normalizer_policy=normalizer_policy,
        supported_protocol_versions=("v0",),
        runtime_config=config,
        receiver_policy=receiver_policy,
    )


def envelope(
    decoded: object,
    *,
    direction: object = "controller_to_rover",
    size_bytes: object = 200,
    parse_succeeded: object = True,
) -> ReceivedLogicalObject:
    return ReceivedLogicalObject(
        direction=direction,
        size_bytes=size_bytes,
        parse_succeeded=parse_succeeded,
        decoded_object=decoded,
    )


def hello(
    *,
    session_id: str = "session-1",
    request_index: int = 1,
    role: str = "controller",
    boot_id: str = "boot-1",
) -> dict[str, object]:
    return {
        "logical_message_type": "SESSION_HELLO",
        "rover_boot_id": boot_id,
        "sender_id": "controller-1",
        "sender_role": role,
        "message_id": f"hello-{request_index}",
        "payload": {
            "protocol_versions": ["v0"],
            "requested_role": role,
            "candidate_session_id": session_id,
            "sender_instance_id": "controller-instance-1",
            "human_switch_confirmation": False,
            "request_index": request_index,
        },
    }


def command_payload(command: CommandType, *, speed: int = 20):
    payload: dict[str, object] = {"command_type": command.value}
    if command in {CommandType.MOVE_FORWARD, CommandType.MOVE_REVERSE}:
        payload["requested_speed"] = speed
    elif command is CommandType.SET_SPEED_LIMIT:
        payload["speed_limit"] = speed
    elif command in {
        CommandType.FAULT_RESET,
        CommandType.EMERGENCY_STOP_RESET,
    }:
        payload["safety_confirmation"] = True
    return payload


def runtime_message(
    command: CommandType,
    sequence: int,
    now_ms: int,
    *,
    session_id: str = "session-1",
    boot_id: str = "boot-1",
    ttl_ms: int = 1_000,
    speed: int = 20,
) -> dict[str, object]:
    return {
        "protocol_version": "v0",
        "logical_message_type": "COMMAND",
        "rover_boot_id": boot_id,
        "session_id": session_id,
        "sender_id": "controller-1",
        "sender_role": "controller",
        "controller_ownership": True,
        "message_id": f"message-{sequence}-{command.value}",
        "sequence": sequence,
        "freshness_reference_ms": now_ms,
        "ttl_ms": ttl_ms,
        "payload": command_payload(command, speed=speed),
    }


def control_update(
    sequence: int,
    now_ms: int,
    operation_id: str,
    *,
    deadman: bool = True,
) -> dict[str, object]:
    fixture = runtime_message(CommandType.STOP, sequence, now_ms)
    fixture["logical_message_type"] = "CONTROL_UPDATE"
    fixture["payload"] = {
        "operation_id": operation_id,
        "deadman_asserted": deadman,
    }
    return fixture


def session_end(sequence: int, now_ms: int) -> dict[str, object]:
    fixture = runtime_message(CommandType.STOP, sequence, now_ms)
    fixture["logical_message_type"] = "SESSION_END"
    fixture["payload"] = {}
    return fixture


def receive(
    boundary: VirtualInputBoundary,
    fixture: object,
    *,
    now_ms: int,
    **metadata,
):
    return boundary.receive(
        envelope(fixture, **metadata),
        now_ms=now_ms,
    )


def establish(boundary: VirtualInputBoundary) -> None:
    step = receive(
        boundary,
        hello(),
        now_ms=0,
        direction="client_to_rover",
    )
    if (
        step.negotiation_result is None
        or step.negotiation_result.disposition
        is not NegotiationDisposition.SESSION_ACCEPTED
    ):
        raise AssertionError("test fixture session negotiation failed")


def prepare_disarmed() -> VirtualInputBoundary:
    boundary = make_boundary()
    establish(boundary)
    boundary.complete_boot(now_ms=1)
    boundary.communication_restored(now_ms=2)
    return boundary


def prepare_drive_ready() -> VirtualInputBoundary:
    boundary = prepare_disarmed()
    receive(
        boundary,
        runtime_message(CommandType.SET_SPEED_LIMIT, 1, 3, speed=40),
        now_ms=3,
    )
    receive(
        boundary,
        runtime_message(CommandType.ARM, 2, 4),
        now_ms=4,
    )
    return boundary


def prepare_drive_active() -> VirtualInputBoundary:
    boundary = prepare_drive_ready()
    boundary.assert_deadman(now_ms=5)
    receive(
        boundary,
        runtime_message(CommandType.MOVE_FORWARD, 3, 6),
        now_ms=6,
    )
    return boundary


def deterministic_report() -> bytes:
    boundary = prepare_drive_active()
    receive(
        boundary,
        control_update(
            4,
            7,
            boundary.bridge.runtime.state.operation_id,
        ),
        now_ms=7,
    )
    receive(
        boundary,
        runtime_message(CommandType.STOP, 5, 8),
        now_ms=8,
    )
    return boundary.render_report().encode("utf-8")


class NormalizerPipelineIntegrationTests(unittest.TestCase):
    def test_raw_session_hello_reaches_session_manager_and_establishes(self):
        boundary = make_boundary()
        step = receive(
            boundary,
            hello(),
            now_ms=0,
            direction="client_to_rover",
        )
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            step.normalization_result.disposition,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            step.negotiation_result.disposition,
        )
        self.assertTrue(step.runtime_event_dispatched)
        self.assertEqual("session-1", boundary.bridge.state.active_session_id)

    def test_malformed_hello_does_not_dispatch_manager_or_runtime(self):
        boundary = make_boundary()
        before = boundary.bridge.runtime.state.step_index
        fixture = hello()
        fixture["payload"]["unexpected"] = "opaque-secret"
        step = receive(
            boundary,
            fixture,
            now_ms=0,
            direction="client_to_rover",
        )
        self.assertEqual(
            NormalizationDisposition.REJECTED,
            step.normalization_result.disposition,
        )
        self.assertIsNone(step.negotiation_result)
        self.assertIsNone(step.adapter_result)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_raw_arm_speed_limit_and_move_traverse_existing_layers(self):
        boundary = prepare_drive_active()
        self.assertEqual(
            RoverState.DRIVE_ACTIVE,
            boundary.bridge.runtime.state.official_state,
        )
        for step in boundary.steps[-3:]:
            self.assertEqual(
                NormalizationDisposition.MESSAGE_NORMALIZED,
                step.normalization_result.disposition,
            )
            self.assertEqual(
                AdapterDisposition.RUNTIME_INPUT_READY,
                step.adapter_result.disposition,
            )
            self.assertTrue(step.runtime_event_dispatched)
            self.assertTrue(step.runtime_result.accepted)

    def test_control_update_continues_existing_operation(self):
        boundary = prepare_drive_active()
        operation_id = boundary.bridge.runtime.state.operation_id
        step = receive(
            boundary,
            control_update(4, 7, operation_id),
            now_ms=7,
        )
        self.assertTrue(step.runtime_result.accepted)
        self.assertEqual(
            operation_id,
            boundary.bridge.runtime.state.operation_id,
        )
        self.assertTrue(boundary.bridge.runtime.state.deadman_active)

    def test_raw_session_end_uses_manager_safety_end_path(self):
        boundary = prepare_drive_active()
        step = receive(boundary, session_end(4, 7), now_ms=7)
        self.assertEqual(
            NegotiationDisposition.SESSION_ENDED,
            step.negotiation_result.disposition,
        )
        self.assertTrue(step.runtime_event_dispatched)
        self.assertTrue(step.runtime_result.accepted)
        self.assertIsNone(boundary.bridge.state.active_session_id)
        self.assertFalse(boundary.bridge.state.controller_owned)
        self.assertEqual(0, boundary.bridge.runtime.state.left_output)

    def test_wrong_session_move_normalizes_then_adapter_rejects(self):
        boundary = prepare_drive_ready()
        before = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(
                CommandType.MOVE_FORWARD,
                3,
                5,
                session_id="session-wrong",
            ),
            now_ms=5,
        )
        self.assertEqual(
            NormalizationDisposition.MESSAGE_NORMALIZED,
            step.normalization_result.disposition,
        )
        self.assertEqual(AdapterDisposition.REJECTED, step.adapter_result.disposition)
        self.assertEqual("invalid_session", step.adapter_result.rejection_reason)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_expired_move_is_adapter_ready_then_runtime_rejected(self):
        boundary = prepare_drive_ready()
        boundary.assert_deadman(now_ms=5)
        step = receive(
            boundary,
            runtime_message(CommandType.MOVE_FORWARD, 3, 0, ttl_ms=1),
            now_ms=10,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            step.adapter_result.disposition,
        )
        self.assertTrue(step.runtime_event_dispatched)
        self.assertFalse(step.runtime_result.accepted)
        self.assertEqual("expired", step.runtime_result.rejection_reason)

    def test_malformed_normal_command_stops_before_adapter(self):
        boundary = prepare_disarmed()
        before = boundary.bridge.runtime.state.step_index
        fixture = runtime_message(CommandType.ARM, 1, 3)
        fixture["payload"]["unexpected"] = 1
        step = receive(boundary, fixture, now_ms=3)
        self.assertEqual(
            NormalizationDisposition.REJECTED,
            step.normalization_result.disposition,
        )
        self.assertIsNone(step.adapter_result)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_malformed_stop_before_gate_has_no_intent_or_dispatch(self):
        boundary = prepare_drive_active()
        before = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 7),
            now_ms=7,
            parse_succeeded=False,
        )
        self.assertEqual(
            NormalizationDisposition.NO_MESSAGE_ACTION,
            step.normalization_result.disposition,
        )
        self.assertIsNone(step.normalization_result.candidate_intent)
        self.assertFalse(step.defensive_zero_candidate)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_post_gate_wrong_session_stop_is_classification_only(self):
        boundary = prepare_drive_active()
        before_sequence = boundary.bridge.runtime.state.last_accepted_sequence
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(
                CommandType.STOP,
                4,
                7,
                session_id="wrong-session",
            ),
            now_ms=7,
        )
        self.assertIs(
            CandidateIntent.STOP,
            step.normalization_result.candidate_intent,
        )
        self.assertTrue(step.normalization_result.identification_gate_passed)
        self.assertTrue(step.defensive_zero_candidate)
        self.assertEqual(AdapterDisposition.REJECTED, step.adapter_result.disposition)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before_step, boundary.bridge.runtime.state.step_index)
        self.assertEqual(
            before_sequence,
            boundary.bridge.runtime.state.last_accepted_sequence,
        )

    def test_post_gate_invalid_ttl_estop_does_not_create_formal_latch(self):
        boundary = prepare_drive_active()
        before = boundary.bridge.runtime.state.step_index
        fixture = runtime_message(CommandType.EMERGENCY_STOP, 4, 7)
        fixture["ttl_ms"] = 0
        step = receive(boundary, fixture, now_ms=7)
        self.assertIs(
            CandidateIntent.EMERGENCY_STOP,
            step.normalization_result.candidate_intent,
        )
        self.assertTrue(step.defensive_zero_candidate)
        self.assertIsNone(step.adapter_result)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertFalse(boundary.bridge.runtime.state.emergency_stop_latched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_valid_stop_uses_existing_formal_runtime_path(self):
        boundary = prepare_drive_active()
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 7),
            now_ms=7,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            step.adapter_result.disposition,
        )
        self.assertTrue(step.runtime_result.accepted)
        self.assertFalse(step.defensive_zero_candidate)
        self.assertEqual(0, boundary.bridge.runtime.state.left_output)
        self.assertEqual("STOP", boundary.bridge.runtime.state.stop_reason)

    def test_valid_estop_uses_existing_formal_latch_path(self):
        boundary = prepare_drive_active()
        step = receive(
            boundary,
            runtime_message(CommandType.EMERGENCY_STOP, 4, 7),
            now_ms=7,
        )
        self.assertTrue(step.runtime_result.accepted)
        self.assertFalse(step.defensive_zero_candidate)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            boundary.bridge.runtime.state.official_state,
        )
        self.assertTrue(boundary.bridge.runtime.state.emergency_stop_latched)

    def test_session_end_then_old_session_command_is_rejected(self):
        boundary = prepare_drive_active()
        receive(boundary, session_end(4, 7), now_ms=7)
        before = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.ARM, 5, 8),
            now_ms=8,
        )
        self.assertEqual(
            NormalizationDisposition.MESSAGE_NORMALIZED,
            step.normalization_result.disposition,
        )
        self.assertIsNone(step.adapter_result)
        self.assertEqual("invalid_session", step.downstream_rejection_reason)
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_boot_id_update_invalidates_old_boot_fixture(self):
        boundary = prepare_drive_active()
        boundary.update_rover_boot_id(
            "boot-2",
            now_ms=7,
            request_index=2,
        )
        before = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.ARM, 4, 8, boot_id="boot-1"),
            now_ms=8,
        )
        self.assertEqual(
            NormalizationDisposition.REJECTED,
            step.normalization_result.disposition,
        )
        self.assertEqual(
            "ROVER_BOOT_ID_MISMATCH",
            step.normalization_result.diagnostic_code,
        )
        self.assertFalse(step.runtime_event_dispatched)
        self.assertEqual(before, boundary.bridge.runtime.state.step_index)

    def test_observer_hello_is_normalized_then_manager_holds(self):
        boundary = make_boundary()
        step = receive(
            boundary,
            hello(role="observer"),
            now_ms=0,
            direction="client_to_rover",
        )
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            step.normalization_result.disposition,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_REJECTED,
            step.negotiation_result.disposition,
        )
        self.assertEqual("role_unavailable", step.negotiation_result.rejection_reason)
        self.assertFalse(step.runtime_event_dispatched)

    def test_hello_boot_mismatch_is_decided_by_session_manager(self):
        boundary = make_boundary()
        step = receive(
            boundary,
            hello(boot_id="boot-other"),
            now_ms=0,
            direction="client_to_rover",
        )
        self.assertEqual(
            NormalizationDisposition.SESSION_CANDIDATE_NORMALIZED,
            step.normalization_result.disposition,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_REJECTED,
            step.negotiation_result.disposition,
        )
        self.assertEqual(
            "boot_id_mismatch",
            step.negotiation_result.rejection_reason,
        )
        self.assertFalse(step.runtime_event_dispatched)

    def test_report_does_not_expand_rejected_untrusted_payload(self):
        boundary = make_boundary()
        secret = "opaque-payload-must-not-appear"
        fixture = runtime_message(CommandType.ARM, 1, 0)
        fixture["payload"]["unknown"] = secret
        receive(boundary, fixture, now_ms=0)
        report = boundary.render_report()
        self.assertNotIn(secret, report)
        self.assertNotIn("unknown", report)
        self.assertNotIn("traceback", report.lower())

    def test_report_excludes_environment_paths_user_host_and_wall_clock(self):
        report = deterministic_report().decode("utf-8")
        values = (
            str(REPOSITORY_ROOT),
            os.environ.get("USERNAME", ""),
            socket.gethostname(),
        )
        for value in values:
            if value:
                self.assertNotIn(value, report)
        self.assertNotIn("timestamp", report.lower())
        self.assertNotIn("real_motor_output_enabled\": true", report)
        self.assertNotIn("defensive_zero_executor_enabled\": true", report)

    def test_identical_input_sequence_produces_byte_identical_report(self):
        first = deterministic_report()
        second = deterministic_report()
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
