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

from software.rover_control.protocol.v0.defensive_zero import (  # noqa: E402
    DefensiveZeroDisposition,
    DefensiveZeroSourceStage,
    VirtualDefensiveBoundary,
)
from software.rover_control.protocol.v0.message_normalizer import (  # noqa: E402
    CandidateIntent,
    NormalizationDisposition,
    NormalizerPolicy,
    ReceivedLogicalObject,
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


def make_boundary() -> VirtualDefensiveBoundary:
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
    return VirtualDefensiveBoundary(
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


def hello() -> dict[str, object]:
    return {
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


def command_payload(command: CommandType, *, speed: int = 20):
    payload: dict[str, object] = {"command_type": command.value}
    if command in {CommandType.MOVE_FORWARD, CommandType.MOVE_REVERSE}:
        payload["requested_speed"] = speed
    elif command is CommandType.SET_SPEED_LIMIT:
        payload["speed_limit"] = speed
    return payload


def runtime_message(
    command: CommandType,
    sequence: int,
    freshness_reference_ms: int,
    *,
    session_id: str = "session-1",
    boot_id: str = "boot-1",
    sender_id: str = "controller-1",
    controller_ownership: bool = True,
    ttl_ms: object = 1_000,
    speed: int = 20,
) -> dict[str, object]:
    return {
        "protocol_version": "v0",
        "logical_message_type": "COMMAND",
        "rover_boot_id": boot_id,
        "session_id": session_id,
        "sender_id": sender_id,
        "sender_role": "controller",
        "controller_ownership": controller_ownership,
        "message_id": f"message-{sequence}-{command.value}",
        "sequence": sequence,
        "freshness_reference_ms": freshness_reference_ms,
        "ttl_ms": ttl_ms,
        "payload": command_payload(command, speed=speed),
    }


def session_end(sequence: int, now_ms: int) -> dict[str, object]:
    fixture = runtime_message(CommandType.STOP, sequence, now_ms)
    fixture["logical_message_type"] = "SESSION_END"
    fixture["payload"] = {}
    return fixture


def receive(
    boundary: VirtualDefensiveBoundary,
    fixture: object,
    *,
    now_ms: int,
    **metadata,
):
    return boundary.receive(
        envelope(fixture, **metadata),
        now_ms=now_ms,
    )


def establish(boundary: VirtualDefensiveBoundary) -> None:
    step = receive(
        boundary,
        hello(),
        now_ms=0,
        direction="client_to_rover",
    )
    result = step.boundary_step.negotiation_result
    if (
        result is None
        or result.disposition
        is not NegotiationDisposition.SESSION_ACCEPTED
    ):
        raise AssertionError("test fixture session negotiation failed")


def prepare_drive_active() -> VirtualDefensiveBoundary:
    boundary = make_boundary()
    establish(boundary)
    boundary.complete_boot(now_ms=1)
    boundary.communication_restored(now_ms=2)
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
    boundary.assert_deadman(now_ms=5)
    receive(
        boundary,
        runtime_message(CommandType.MOVE_FORWARD, 3, 6),
        now_ms=6,
    )
    if (
        boundary.bridge.runtime.state.official_state
        is not RoverState.DRIVE_ACTIVE
    ):
        raise AssertionError("test fixture did not reach DRIVE_ACTIVE")
    return boundary


def deterministic_report() -> bytes:
    boundary = prepare_drive_active()
    receive(
        boundary,
        runtime_message(
            CommandType.STOP,
            4,
            7,
            session_id="wrong-session",
        ),
        now_ms=7,
    )
    return boundary.render_report().encode("utf-8")


class DefensiveZeroPipelineIntegrationTests(unittest.TestCase):
    def assert_zero(self, boundary: VirtualDefensiveBoundary) -> None:
        state = boundary.bridge.runtime.state
        self.assertEqual(0, state.requested_speed)
        self.assertEqual(0, state.effective_speed)
        self.assertEqual(0, state.left_output)
        self.assertIsNone(state.right_output)
        self.assertFalse(state.pto_requested)
        self.assertFalse(state.pto_effective)
        self.assertIsNone(state.operation_id)
        self.assertFalse(state.deadman_active)
        self.assertIsNone(state.watchdog_deadline_ms)

    def test_wrong_session_stop_executes_local_zero(self):
        boundary = prepare_drive_active()
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
        self.assertEqual(
            AdapterDisposition.REJECTED,
            step.boundary_step.adapter_result.disposition,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            DefensiveZeroSourceStage.ADAPTER,
            step.defensive_zero_result.source_stage,
        )
        self.assertFalse(step.formal_command_accepted)
        self.assertEqual(
            RoverState.DRIVE_READY,
            boundary.bridge.runtime.state.official_state,
        )
        self.assert_zero(boundary)

    def test_wrong_owner_stop_zeroes_without_sequence_update(self):
        boundary = prepare_drive_active()
        before_seen = boundary.bridge.runtime.state.last_seen_sequence
        before_accepted = (
            boundary.bridge.runtime.state.last_accepted_sequence
        )
        step = receive(
            boundary,
            runtime_message(
                CommandType.STOP,
                4,
                7,
                sender_id="intruder",
            ),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertTrue(step.defensive_zero_result.operation_invalidated)
        self.assertFalse(step.defensive_zero_result.sequence_updated)
        self.assertEqual(
            before_seen,
            boundary.bridge.runtime.state.last_seen_sequence,
        )
        self.assertEqual(
            before_accepted,
            boundary.bridge.runtime.state.last_accepted_sequence,
        )
        self.assert_zero(boundary)

    def test_invalid_ttl_estop_executes_without_formal_latch(self):
        boundary = prepare_drive_active()
        fixture = runtime_message(
            CommandType.EMERGENCY_STOP,
            4,
            7,
            ttl_ms=0,
        )
        step = receive(boundary, fixture, now_ms=7)
        self.assertEqual(
            NormalizationDisposition.REJECTED,
            step.boundary_step.normalization_result.disposition,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertFalse(step.emergency_stop_latched_formally)
        self.assertFalse(
            boundary.bridge.runtime.state.emergency_stop_latched
        )
        self.assert_zero(boundary)

    def test_unknown_stop_payload_property_executes_local_zero(self):
        boundary = prepare_drive_active()
        fixture = runtime_message(CommandType.STOP, 4, 7)
        fixture["payload"]["unknown"] = "opaque-secret"
        step = receive(boundary, fixture, now_ms=7)
        normalization = step.boundary_step.normalization_result
        self.assertTrue(normalization.identification_gate_passed)
        self.assertIs(CandidateIntent.STOP, normalization.candidate_intent)
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            DefensiveZeroSourceStage.NORMALIZER,
            step.defensive_zero_result.source_stage,
        )
        self.assert_zero(boundary)

    def test_unsupported_version_stop_does_not_zero(self):
        boundary = prepare_drive_active()
        before = boundary.bridge.runtime.state
        fixture = runtime_message(CommandType.STOP, 4, 7)
        fixture["protocol_version"] = "v1"
        step = receive(boundary, fixture, now_ms=7)
        self.assertEqual(
            DefensiveZeroDisposition.NOT_APPLICABLE,
            step.defensive_zero_result.disposition,
        )
        self.assertIsNone(
            step.boundary_step.normalization_result.candidate_intent
        )
        self.assertEqual(before, boundary.bridge.runtime.state)

    def test_wrong_boot_stop_does_not_zero(self):
        boundary = prepare_drive_active()
        before = boundary.bridge.runtime.state
        step = receive(
            boundary,
            runtime_message(
                CommandType.STOP,
                4,
                7,
                boot_id="wrong-boot",
            ),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.NOT_APPLICABLE,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(before, boundary.bridge.runtime.state)

    def test_parse_failure_has_no_intent_or_zero(self):
        boundary = prepare_drive_active()
        before = boundary.bridge.runtime.state
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 7),
            now_ms=7,
            parse_succeeded=False,
        )
        self.assertEqual(
            DefensiveZeroDisposition.NOT_APPLICABLE,
            step.defensive_zero_result.disposition,
        )
        self.assertIsNone(
            step.boundary_step.normalization_result.candidate_intent
        )
        self.assertEqual(before, boundary.bridge.runtime.state)

    def test_expired_stop_uses_runtime_native_zero_once(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 0, ttl_ms=1),
            now_ms=10,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            DefensiveZeroSourceStage.RUNTIME,
            step.defensive_zero_result.source_stage,
        )
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertIs(
            step.boundary_step.runtime_result,
            step.defensive_zero_result.runtime_result,
        )
        self.assert_zero(boundary)

    def test_stale_stop_uses_runtime_native_zero_once(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 2, 7),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assert_zero(boundary)

    def test_duplicate_stop_uses_runtime_native_zero_once(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 3, 7),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertEqual(
            "duplicate_sequence",
            step.boundary_step.runtime_result.rejection_reason,
        )
        self.assert_zero(boundary)

    def test_valid_stop_remains_formal_command(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 7),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.FORMAL_COMMAND_APPLIED,
            step.defensive_zero_result.disposition,
        )
        self.assertTrue(step.formal_command_accepted)
        self.assertTrue(step.boundary_step.runtime_result.accepted)
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertEqual(
            "STOP",
            boundary.bridge.runtime.state.stop_reason,
        )

    def test_invalid_session_estop_does_not_create_formal_latch(self):
        boundary = prepare_drive_active()
        step = receive(
            boundary,
            runtime_message(
                CommandType.EMERGENCY_STOP,
                4,
                7,
                session_id="wrong-session",
            ),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertFalse(step.formal_command_accepted)
        self.assertFalse(step.emergency_stop_latched_formally)
        self.assertFalse(
            boundary.bridge.runtime.state.emergency_stop_latched
        )
        self.assert_zero(boundary)

    def test_expired_estop_uses_runtime_native_zero_without_latch(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(
                CommandType.EMERGENCY_STOP,
                4,
                0,
                ttl_ms=1,
            ),
            now_ms=10,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertFalse(
            boundary.bridge.runtime.state.emergency_stop_latched
        )
        self.assert_zero(boundary)

    def test_stale_estop_uses_runtime_native_zero_without_latch(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.EMERGENCY_STOP, 2, 7),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertFalse(
            boundary.bridge.runtime.state.emergency_stop_latched
        )
        self.assert_zero(boundary)

    def test_valid_estop_remains_formal_and_latched(self):
        boundary = prepare_drive_active()
        before_step = boundary.bridge.runtime.state.step_index
        step = receive(
            boundary,
            runtime_message(CommandType.EMERGENCY_STOP, 4, 7),
            now_ms=7,
        )
        self.assertEqual(
            DefensiveZeroDisposition.FORMAL_COMMAND_APPLIED,
            step.defensive_zero_result.disposition,
        )
        self.assertTrue(step.formal_command_accepted)
        self.assertTrue(step.emergency_stop_latched_formally)
        self.assertEqual(
            before_step + 1,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            boundary.bridge.runtime.state.official_state,
        )

    def test_defensive_candidate_preserves_existing_estop_latch(self):
        boundary = prepare_drive_active()
        receive(
            boundary,
            runtime_message(CommandType.EMERGENCY_STOP, 4, 7),
            now_ms=7,
        )
        step = receive(
            boundary,
            runtime_message(
                CommandType.STOP,
                5,
                8,
                session_id="wrong-session",
            ),
            now_ms=8,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertTrue(step.defensive_zero_result.latch_preserved)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            boundary.bridge.runtime.state.official_state,
        )
        self.assertTrue(
            boundary.bridge.runtime.state.emergency_stop_latched
        )

    def test_old_session_stop_after_session_end_does_not_restore_session(self):
        boundary = prepare_drive_active()
        receive(boundary, session_end(4, 7), now_ms=7)
        before_seen = boundary.bridge.runtime.state.last_seen_sequence
        before_accepted = (
            boundary.bridge.runtime.state.last_accepted_sequence
        )
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 5, 8),
            now_ms=8,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            step.defensive_zero_result.disposition,
        )
        self.assertIsNone(boundary.bridge.state.active_session_id)
        self.assertFalse(boundary.bridge.state.controller_owned)
        self.assertTrue(
            boundary.bridge.runtime.state.communication_loss_latched
        )
        self.assertEqual(
            before_seen,
            boundary.bridge.runtime.state.last_seen_sequence,
        )
        self.assertEqual(
            before_accepted,
            boundary.bridge.runtime.state.last_accepted_sequence,
        )

    def test_old_boot_stop_after_boot_change_is_not_applicable(self):
        boundary = prepare_drive_active()
        boundary.update_rover_boot_id(
            "boot-2",
            now_ms=7,
            request_index=2,
        )
        before = boundary.bridge.runtime.state
        step = receive(
            boundary,
            runtime_message(CommandType.STOP, 4, 8, boot_id="boot-1"),
            now_ms=8,
        )
        self.assertEqual(
            DefensiveZeroDisposition.NOT_APPLICABLE,
            step.defensive_zero_result.disposition,
        )
        self.assertEqual(before, boundary.bridge.runtime.state)

    def test_same_step_reevaluation_is_idempotent(self):
        boundary = prepare_drive_active()
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
        runtime_after_first = boundary.bridge.runtime.state.step_index
        executor_after_first = boundary.executor.step_index
        result = boundary.reevaluate(
            step.defensive_boundary_step_index
        )
        self.assertIs(step.defensive_zero_result, result)
        self.assertEqual(
            runtime_after_first,
            boundary.bridge.runtime.state.step_index,
        )
        self.assertEqual(executor_after_first, boundary.executor.step_index)

    def test_identical_input_sequence_produces_byte_identical_report(self):
        first = deterministic_report()
        second = deterministic_report()
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )

    def test_report_separates_formal_and_defensive_runtime_results(self):
        boundary = prepare_drive_active()
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
        report = step.report_dict()
        self.assertIsNone(report["formal_runtime_result"])
        self.assertIsNotNone(report["defensive_runtime_result"])
        self.assertTrue(report["defensive_zero_executed"])
        self.assertFalse(report["formal_command_accepted"])
        self.assertTrue(
            boundary.report_dict()["defensive_zero_executor_enabled"]
        )

    def test_report_excludes_payload_environment_and_hardware_action(self):
        boundary = prepare_drive_active()
        secret = "opaque-payload-must-not-appear"
        fixture = runtime_message(CommandType.STOP, 4, 7)
        fixture["payload"]["unknown"] = secret
        receive(boundary, fixture, now_ms=7)
        report = boundary.render_report()
        self.assertNotIn(secret, report)
        self.assertNotIn("traceback", report.lower())
        self.assertNotIn("timestamp", report.lower())
        self.assertNotIn("real_motor_output_enabled\": true", report)
        for value in (
            str(REPOSITORY_ROOT),
            os.environ.get("USERNAME", ""),
            socket.gethostname(),
        ):
            if value:
                self.assertNotIn(value, report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
