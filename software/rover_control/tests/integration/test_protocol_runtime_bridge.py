from __future__ import annotations

import ast
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


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
    SenderRole,
    VirtualReceiverBridge,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    RoverState,
    VectorClassification,
    classify_vector_id,
)


ADAPTER_DIRECTORY = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/runtime_adapter"
)
VECTOR_002_PATH = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/test_vectors/vectors/PV0-VAL-002.json"
)
ACCEPTANCE_BASELINE_PATH = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/test_vectors/offline_validator"
    / "acceptance-baseline.json"
)
MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receiver_context(**overrides) -> ReceiverContext:
    values = {
        "expected_protocol_version": "v0",
        "current_rover_boot_id": "boot-1",
        "active_session_id": "session-1",
        "active_controller_owner_id": "controller-1",
        "current_monotonic_time_ms": 0,
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


def command_message(
    command: CommandType,
    sequence: int,
    now_ms: int,
    *,
    requested_speed=None,
    speed_limit=None,
    safety_confirmation=None,
    **overrides,
) -> NormalizedLogicalMessage:
    return logical_message(
        message_id=f"message-{sequence}-{command.value}",
        sequence=sequence,
        freshness_reference_ms=now_ms,
        payload=CommandPayload(
            command,
            requested_speed=requested_speed,
            speed_limit=speed_limit,
            safety_confirmation=safety_confirmation,
        ),
        **overrides,
    )


def prepare_drive_ready() -> VirtualReceiverBridge:
    bridge = VirtualReceiverBridge(receiver_context())
    bridge.complete_boot(now_ms=0)
    bridge.communication_restored(now_ms=1)
    bridge.receive(
        command_message(
            CommandType.SET_SPEED_LIMIT,
            1,
            2,
            speed_limit=40,
        ),
        now_ms=2,
    )
    bridge.receive(
        command_message(CommandType.ARM, 2, 3),
        now_ms=3,
    )
    return bridge


def prepare_drive_active() -> VirtualReceiverBridge:
    bridge = prepare_drive_ready()
    bridge.assert_deadman(now_ms=4)
    bridge.receive(
        command_message(
            CommandType.MOVE_FORWARD,
            3,
            5,
            requested_speed=20,
        ),
        now_ms=5,
    )
    return bridge


def deterministic_scenario_report() -> bytes:
    bridge = prepare_drive_active()
    operation_id = bridge.state.operation_id
    bridge.receive(
        logical_message(
            logical_message_type=LogicalMessageType.CONTROL_UPDATE,
            message_id="message-4-control",
            sequence=4,
            freshness_reference_ms=100,
            payload=ControlUpdatePayload(operation_id, True),
        ),
        now_ms=100,
    )
    bridge.receive(
        command_message(CommandType.STOP, 5, 101),
        now_ms=101,
    )
    return bridge.render_report().encode("utf-8")


class ProtocolRuntimeBridgeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        protected_roots = (
            REPOSITORY_ROOT / "software/rover_control/safety",
            REPOSITORY_ROOT / "software/rover_control/protocol/v0/test_vectors",
            REPOSITORY_ROOT / "software/rover_control/simulator/virtual_rover",
        )
        protected = []
        for root in protected_roots:
            protected.extend(path for path in root.rglob("*") if path.is_file())
        cls.protected_hashes = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): sha256(path)
            for path in sorted(protected)
        }

    def test_normal_boot_session_speed_limit_and_arm_preparation(self):
        bridge = prepare_drive_ready()
        self.assertEqual(RoverState.DRIVE_READY, bridge.state.official_state)
        self.assertTrue(bridge.state.armed)
        self.assertTrue(bridge.state.communication_alive)
        self.assertEqual(40, bridge.state.speed_limit)
        self.assertEqual("session-1", bridge.state.session_id)
        self.assertEqual(4, bridge.runtime_step_index)

    def test_receiver_local_deadman_assert_is_not_a_protocol_message(self):
        bridge = prepare_drive_ready()
        adapter_steps = bridge.adapter_step_index
        receipt = bridge.assert_deadman(now_ms=4)
        self.assertIsNone(receipt.adapter_result)
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertTrue(bridge.state.deadman_active)
        self.assertEqual(adapter_steps, bridge.adapter_step_index)

    def test_adapter_move_forward_reaches_drive_active(self):
        bridge = prepare_drive_ready()
        bridge.assert_deadman(now_ms=4)
        receipt = bridge.receive(
            command_message(
                CommandType.MOVE_FORWARD,
                3,
                5,
                requested_speed=20,
            ),
            now_ms=5,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual(RoverState.DRIVE_ACTIVE, bridge.state.official_state)
        self.assertEqual(20, bridge.state.left_output)
        self.assertEqual("operation-0000000000000003", bridge.state.operation_id)

    def test_control_update_extends_liveness_without_new_operation(self):
        bridge = prepare_drive_active()
        operation_id = bridge.state.operation_id
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.CONTROL_UPDATE,
                message_id="message-4-control",
                sequence=4,
                freshness_reference_ms=100,
                payload=ControlUpdatePayload(operation_id, True),
            ),
            now_ms=100,
        )
        self.assertTrue(receipt.adapter_result.control_liveness_candidate)
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual(operation_id, bridge.state.operation_id)
        self.assertEqual(850, bridge.state.watchdog_deadline_ms)

    def test_receiver_local_deadman_release_stops_motion(self):
        bridge = prepare_drive_active()
        receipt = bridge.release_deadman(now_ms=6)
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual("deadman_released", receipt.runtime_result.stop_reason)
        self.assertEqual(RoverState.DRIVE_READY, bridge.state.official_state)
        self.assertEqual(0, bridge.state.left_output)
        self.assertIsNone(bridge.state.operation_id)

    def test_control_update_false_performs_runtime_deadman_release(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.CONTROL_UPDATE,
                message_id="message-4-control-release",
                sequence=4,
                freshness_reference_ms=6,
                payload=ControlUpdatePayload(bridge.state.operation_id, False),
            ),
            now_ms=6,
        )
        self.assertFalse(receipt.adapter_result.control_liveness_candidate)
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual("deadman_released", receipt.runtime_result.stop_reason)
        self.assertEqual(0, bridge.state.left_output)

    def test_valid_stop_keeps_adapter_and_runtime_results_separate(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            command_message(CommandType.STOP, 4, 6),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual("STOP", receipt.runtime_result.stop_reason)
        self.assertEqual(RoverState.DRIVE_READY, bridge.state.official_state)
        self.assertEqual(0, bridge.state.left_output)

    def test_valid_emergency_stop_latches_and_zeroes(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            command_message(CommandType.EMERGENCY_STOP, 4, 6),
            now_ms=6,
        )
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            bridge.state.official_state,
        )
        self.assertTrue(bridge.state.emergency_stop_latched)
        self.assertFalse(bridge.state.armed)
        self.assertEqual(0, bridge.state.left_output)

    def test_wrong_session_is_adapter_rejection_without_runtime_dispatch(self):
        bridge = prepare_drive_ready()
        runtime_step = bridge.runtime_step_index
        receipt = bridge.receive(
            command_message(
                CommandType.MOVE_FORWARD,
                3,
                4,
                requested_speed=20,
                session_id="old-session",
            ),
            now_ms=4,
        )
        self.assertEqual(AdapterDisposition.REJECTED, receipt.adapter_result.disposition)
        self.assertEqual("invalid_session", receipt.adapter_result.rejection_reason)
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(RoverState.DRIVE_READY, bridge.state.official_state)

    def test_wrong_boot_id_is_adapter_rejection_without_runtime_dispatch(self):
        bridge = prepare_drive_ready()
        runtime_step = bridge.runtime_step_index
        receipt = bridge.receive(
            command_message(
                CommandType.STOP,
                3,
                4,
                rover_boot_id="old-boot",
            ),
            now_ms=4,
        )
        self.assertEqual("invalid_boot_id", receipt.adapter_result.rejection_reason)
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)

    def test_expired_message_is_adapter_ready_but_runtime_rejected(self):
        bridge = prepare_drive_ready()
        bridge.assert_deadman(now_ms=4)
        message = command_message(
            CommandType.MOVE_FORWARD,
            3,
            0,
            requested_speed=20,
            ttl_ms=1_000,
        )
        receipt = bridge.receive(message, now_ms=2_000)
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertFalse(receipt.runtime_result.accepted)
        self.assertEqual("expired", receipt.runtime_result.rejection_reason)
        self.assertEqual(RoverState.DRIVE_READY, bridge.state.official_state)

    def test_duplicate_sequence_is_delegated_to_runtime(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            command_message(CommandType.STOP, 3, 6),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertFalse(receipt.runtime_result.accepted)
        self.assertEqual(
            "duplicate_sequence",
            receipt.runtime_result.rejection_reason,
        )
        self.assertEqual("STOP", receipt.runtime_result.stop_reason)
        self.assertEqual(0, bridge.state.left_output)

    def test_stale_sequence_is_delegated_to_runtime(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            command_message(
                CommandType.MOVE_FORWARD,
                2,
                6,
                requested_speed=20,
            ),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertFalse(receipt.runtime_result.accepted)
        self.assertEqual("stale_sequence", receipt.runtime_result.rejection_reason)
        self.assertEqual(RoverState.DRIVE_ACTIVE, bridge.state.official_state)
        self.assertEqual(20, bridge.state.left_output)

    def test_adapter_rejection_leaves_runtime_step_and_state_unchanged(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        receipt = bridge.receive(
            command_message(
                CommandType.MOVE_FORWARD,
                4,
                6,
                requested_speed="20",
            ),
            now_ms=6,
        )
        self.assertEqual(AdapterDisposition.REJECTED, receipt.adapter_result.disposition)
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)

    def test_adapter_internal_error_is_distinct_and_never_calls_runtime(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        with mock.patch.object(
            bridge._adapter,
            "adapt",
            side_effect=RuntimeError("injected"),
        ):
            receipt = bridge.receive(
                command_message(CommandType.STOP, 4, 6),
                now_ms=6,
            )
        self.assertEqual(AdapterDisposition.REJECTED, receipt.adapter_result.disposition)
        self.assertTrue(receipt.adapter_result.internal_error)
        self.assertEqual(
            "ADAPTER_INTERNAL_ERROR",
            receipt.adapter_result.diagnostic_code,
        )
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)

    def test_runtime_state_guard_rejection_is_not_adapter_rejection(self):
        bridge = prepare_drive_ready()
        receipt = bridge.receive(
            command_message(
                CommandType.MOVE_FORWARD,
                3,
                4,
                requested_speed=20,
            ),
            now_ms=4,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            receipt.adapter_result.disposition,
        )
        self.assertFalse(receipt.runtime_result.accepted)
        self.assertEqual("guard_failed", receipt.runtime_result.rejection_reason)
        self.assertEqual(5, bridge.runtime_step_index)

    def test_session_end_dispatches_communication_loss_safety_transition(self):
        bridge = prepare_drive_active()
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_END,
                message_id="message-4-session-end",
                sequence=4,
                freshness_reference_ms=6,
                payload=None,
            ),
            now_ms=6,
        )
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual(
            RoverState.COMM_LOSS_LATCHED,
            bridge.state.official_state,
        )
        self.assertFalse(bridge.state.armed)
        self.assertEqual(0, bridge.state.left_output)

    def test_rover_to_client_message_is_no_runtime_action(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        opaque_value = "opaque-telemetry-must-not-enter-report"
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.TELEMETRY,
                direction=MessageDirection.ROVER_TO_CLIENT,
                session_id="unbound-telemetry-session",
                sender_id="rover-1",
                sender_role=SenderRole.ROVER,
                controller_ownership=False,
                message_id="telemetry-1",
                sequence=100,
                freshness_reference_ms=6,
                payload=OpaquePayload(
                    {
                        "sample": [opaque_value],
                    }
                ),
            ),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            receipt.adapter_result.disposition,
        )
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)
        self.assertNotIn(opaque_value, bridge.render_report())

    def test_session_hello_new_candidate_does_not_change_current_session(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_HELLO,
                direction=MessageDirection.CLIENT_TO_ROVER,
                session_id="candidate-session-2",
                controller_ownership=False,
                message_id="session-hello-2",
                sequence=100,
                freshness_reference_ms=6,
                payload=OpaquePayload({"requested_role": "controller"}),
            ),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            receipt.adapter_result.disposition,
        )
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)
        self.assertEqual("session-1", bridge.context.active_session_id)
        self.assertEqual("session-1", bridge.state.session_id)

    def test_session_accepted_notification_does_not_install_new_session(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_ACCEPTED,
                direction=MessageDirection.ROVER_TO_CLIENT,
                session_id="notified-session-2",
                sender_id="rover-1",
                sender_role=SenderRole.ROVER,
                controller_ownership=False,
                message_id="session-accepted-2",
                sequence=100,
                freshness_reference_ms=6,
                payload=OpaquePayload({"selected_version": "v0"}),
            ),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            receipt.adapter_result.disposition,
        )
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)
        self.assertEqual("session-1", bridge.context.active_session_id)
        self.assertEqual("session-1", bridge.state.session_id)

    def test_session_rejected_without_session_never_dispatches_runtime(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime_step_index
        state_before = bridge.state
        receipt = bridge.receive(
            logical_message(
                logical_message_type=LogicalMessageType.SESSION_REJECTED,
                direction=MessageDirection.ROVER_TO_CLIENT,
                session_id=None,
                sender_id="rover-1",
                sender_role=SenderRole.ROVER,
                controller_ownership=False,
                message_id="session-rejected-2",
                sequence=100,
                freshness_reference_ms=6,
                payload=OpaquePayload({"reason": "controller_active"}),
            ),
            now_ms=6,
        )
        self.assertEqual(
            AdapterDisposition.NO_RUNTIME_ACTION,
            receipt.adapter_result.disposition,
        )
        self.assertIsNone(receipt.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime_step_index)
        self.assertEqual(state_before, bridge.state)
        self.assertEqual("session-1", bridge.context.active_session_id)
        self.assertEqual("session-1", bridge.state.session_id)

    def test_pv0_val_002_completion_fixture_uses_explicit_speed_and_deadman(self):
        vector = json.loads(VECTOR_002_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("requested_speed", vector["stimulus"]["message"])
        self.assertEqual(
            VectorClassification.RUNTIME_CONTRACT_REQUIRED,
            classify_vector_id("PV0-VAL-002"),
        )
        bridge = VirtualReceiverBridge(
            receiver_context(
                current_rover_boot_id="boot-pv0-002",
                active_session_id="session-pv0-002",
                active_controller_owner_id="controller-pv0-002",
                current_monotonic_time_ms=9_997,
            )
        )
        bridge.complete_boot(now_ms=9_997)
        bridge.communication_restored(now_ms=9_998)
        bridge.receive(
            logical_message(
                rover_boot_id="boot-pv0-002",
                session_id="session-pv0-002",
                sender_id="controller-pv0-002",
                message_id="fixture-speed-limit",
                sequence=40,
                freshness_reference_ms=9_998,
                payload=CommandPayload(
                    CommandType.SET_SPEED_LIMIT,
                    speed_limit=40,
                ),
            ),
            now_ms=9_998,
        )
        bridge.receive(
            logical_message(
                rover_boot_id="boot-pv0-002",
                session_id="session-pv0-002",
                sender_id="controller-pv0-002",
                message_id="fixture-arm",
                sequence=41,
                freshness_reference_ms=9_999,
                payload=CommandPayload(CommandType.ARM),
            ),
            now_ms=9_999,
        )
        bridge.assert_deadman(now_ms=10_000)
        receipt = bridge.receive(
            logical_message(
                rover_boot_id="boot-pv0-002",
                session_id="session-pv0-002",
                sender_id="controller-pv0-002",
                message_id="message-pv0-002-completion",
                sequence=42,
                freshness_reference_ms=10_000,
                ttl_ms=1_000,
                payload=CommandPayload(
                    CommandType.MOVE_FORWARD,
                    requested_speed=20,
                ),
            ),
            now_ms=10_010,
        )
        self.assertTrue(receipt.runtime_result.accepted)
        self.assertEqual(RoverState.DRIVE_ACTIVE, bridge.state.official_state)
        self.assertTrue(bridge.state.armed)
        self.assertEqual(20, bridge.state.left_output)
        self.assertFalse(bridge.state.pto_effective)
        self.assertIsNotNone(bridge.state.operation_id)
        self.assertEqual(42, bridge.state.last_accepted_sequence)
        self.assertFalse(bridge.state.communication_loss_latched)
        self.assertFalse(bridge.state.fault_latched)
        self.assertFalse(bridge.state.emergency_stop_latched)
        self.assertFalse(bridge.report_dict()["real_motor_output_enabled"])

    def test_same_inputs_produce_byte_identical_bridge_report(self):
        first = deterministic_scenario_report()
        second = deterministic_scenario_report()
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )

    def test_report_has_no_absolute_or_nondeterministic_metadata(self):
        report = deterministic_scenario_report().decode("utf-8")
        lowered = report.lower()
        forbidden = (
            str(REPOSITORY_ROOT).lower(),
            "timestamp",
            "username",
            "hostname",
            "machine_name",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, lowered)

    def test_report_keeps_adapter_and_runtime_results_in_separate_fields(self):
        report = json.loads(deterministic_scenario_report())
        message_steps = [
            step
            for step in report["steps"]
            if step["adapter_result"] is not None
        ]
        self.assertTrue(message_steps)
        for step in message_steps:
            self.assertIn("adapter_result", step)
            self.assertIn("runtime_result", step)
            self.assertNotIn("accepted", step["adapter_result"])

    def test_real_motor_output_is_always_reported_disabled(self):
        bridge = prepare_drive_active()
        report = bridge.report_dict()
        self.assertFalse(report["real_motor_output_enabled"])
        self.assertIsNone(report["final_state"]["right_output"])
        self.assertFalse(bridge.state.pto_effective)

    def test_adapter_and_bridge_source_use_no_forbidden_runtime_mechanisms(self):
        forbidden_imports = {
            "asyncio",
            "http",
            "random",
            "requests",
            "socket",
            "threading",
            "time",
        }
        forbidden_calls = {
            "open",
            "sleep",
            "socket",
            "start",
            "write",
            "write_bytes",
            "write_text",
        }
        found = []
        for path in ADAPTER_DIRECTORY.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".", 1)[0] in forbidden_imports:
                            found.append((path.name, node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.split(".", 1)[0] in forbidden_imports:
                        found.append((path.name, node.lineno, node.module))
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        call_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        call_name = node.func.attr
                    else:
                        continue
                    if call_name in forbidden_calls:
                        found.append((path.name, node.lineno, call_name))
        self.assertEqual([], found)

    def test_z_protected_artifacts_baseline_and_vector_are_unchanged(self):
        hashes_after = {
            REPOSITORY_ROOT.joinpath(path).relative_to(REPOSITORY_ROOT).as_posix():
            sha256(REPOSITORY_ROOT / path)
            for path in self.protected_hashes
        }
        self.assertEqual(self.protected_hashes, hashes_after)
        self.assertEqual(
            "bc482767c4a352080e4f0a06feeca700d9005a0fc74a44e77ef739d93ebafb6b",
            sha256(VECTOR_002_PATH),
        )
        self.assertEqual(
            "87737ffaf53eaa35316f5a98a95c273a0b3413a0643d97363a068e29b8fcb956",
            sha256(ACCEPTANCE_BASELINE_PATH),
        )
        rover_root = REPOSITORY_ROOT / "software/rover_control"
        self.assertFalse(any(rover_root.rglob("*.pyc")))
        self.assertFalse(any(rover_root.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
