from __future__ import annotations

import ast
import hashlib
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
    LogicalMessageType,
    MessageDirection,
    NormalizedLogicalMessage,
    SenderRole,
)
from software.rover_control.protocol.v0.session_negotiation import (  # noqa: E402
    NegotiationDisposition,
    ReceiverPolicy,
    SessionCandidate,
    SessionEndRequest,
    SessionRole,
    VirtualSessionBridge,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    Event,
    Profile,
    RoverState,
    RuntimeConfig,
    RuntimeInput,
)


MAX_SAFE_SEQUENCE = 9_007_199_254_740_991
SESSION_DIRECTORY = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/session_negotiation"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_bridge() -> VirtualSessionBridge:
    config = RuntimeConfig(
        profile=Profile.ONE_SIDE_TEST,
        max_command_ttl_ms=5_000,
        max_speed=100,
        session_id="runtime-bootstrap",
        real_motor_output_enabled=False,
    )
    policy = ReceiverPolicy(
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
    return VirtualSessionBridge(
        current_rover_boot_id="boot-1",
        supported_protocol_versions=("v0",),
        runtime_config=config,
        receiver_policy=policy,
    )


def candidate(**overrides) -> SessionCandidate:
    values = {
        "protocol_versions": ("v0",),
        "requested_role": SessionRole.CONTROLLER,
        "candidate_session_id": "session-1",
        "rover_boot_id": "boot-1",
        "sender_id": "controller-1",
        "sender_instance_id": "controller-instance-1",
        "human_switch_confirmation": False,
        "request_index": 1,
    }
    values.update(overrides)
    return SessionCandidate(**values)


def session_end(**overrides) -> SessionEndRequest:
    values = {
        "rover_boot_id": "boot-1",
        "session_id": "session-1",
        "sender_id": "controller-1",
        "sender_instance_id": "controller-instance-1",
        "message_id": "session-end-1",
        "sequence": 1,
        "freshness_reference_ms": 1,
        "ttl_ms": 1_000,
        "request_index": 2,
    }
    values.update(overrides)
    return SessionEndRequest(**values)


def command_message(
    command: CommandType,
    sequence: int,
    now_ms: int,
    *,
    session_id: str = "session-1",
    sender_id: str = "controller-1",
    requested_speed=None,
    speed_limit=None,
) -> NormalizedLogicalMessage:
    return NormalizedLogicalMessage(
        protocol_version="v0",
        logical_message_type=LogicalMessageType.COMMAND,
        direction=MessageDirection.CONTROLLER_TO_ROVER,
        rover_boot_id="boot-1",
        session_id=session_id,
        sender_id=sender_id,
        sender_role=SenderRole.CONTROLLER,
        controller_ownership=True,
        message_id=f"message-{sequence}-{command.value}",
        sequence=sequence,
        freshness_reference_ms=now_ms,
        ttl_ms=1_000,
        payload=CommandPayload(
            command,
            requested_speed=requested_speed,
            speed_limit=speed_limit,
        ),
    )


def establish_session(bridge: VirtualSessionBridge) -> None:
    step = bridge.process_hello(candidate(), now_ms=0)
    if (
        step.negotiation_result.disposition
        is not NegotiationDisposition.SESSION_ACCEPTED
    ):
        raise AssertionError("fixture session negotiation failed")


def prepare_disarmed() -> VirtualSessionBridge:
    bridge = make_bridge()
    establish_session(bridge)
    bridge.complete_boot(now_ms=1)
    return bridge


def prepare_drive_ready() -> VirtualSessionBridge:
    bridge = prepare_disarmed()
    bridge.communication_restored(now_ms=2)
    bridge.receive(
        command_message(
            CommandType.SET_SPEED_LIMIT,
            1,
            3,
            speed_limit=40,
        ),
        now_ms=3,
    )
    bridge.receive(command_message(CommandType.ARM, 2, 4), now_ms=4)
    return bridge


def prepare_drive_active() -> VirtualSessionBridge:
    bridge = prepare_drive_ready()
    bridge.assert_deadman(now_ms=5)
    bridge.receive(
        command_message(
            CommandType.MOVE_FORWARD,
            3,
            6,
            requested_speed=20,
        ),
        now_ms=6,
    )
    return bridge


def deterministic_report() -> bytes:
    bridge = prepare_drive_active()
    bridge.receive(command_message(CommandType.STOP, 4, 7), now_ms=7)
    bridge.receive(command_message(CommandType.DISARM, 5, 8), now_ms=8)
    bridge.end_session(
        session_end(
            message_id="session-end-deterministic",
            sequence=6,
            freshness_reference_ms=9,
        ),
        now_ms=9,
    )
    bridge.process_hello(
        candidate(
            candidate_session_id="session-2",
            request_index=3,
        ),
        now_ms=10,
    )
    return bridge.render_report().encode("utf-8")


class SessionRuntimeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        protected_roots = (
            REPOSITORY_ROOT / "software/rover_control/safety",
            (
                REPOSITORY_ROOT
                / "software/rover_control/protocol/v0/test_vectors"
            ),
            (
                REPOSITORY_ROOT
                / "software/rover_control/protocol/v0/runtime_adapter"
            ),
            (
                REPOSITORY_ROOT
                / "software/rover_control/simulator/virtual_rover"
            ),
        )
        protected = []
        for root in protected_roots:
            protected.extend(path for path in root.rglob("*") if path.is_file())
        cls.protected_hashes = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): sha256(path)
            for path in sorted(protected)
        }

    def test_initial_controller_session_is_accepted(self):
        bridge = make_bridge()
        step = bridge.process_hello(candidate(), now_ms=0)
        result = step.negotiation_result
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            result.disposition,
        )
        self.assertTrue(result.controller_ownership)
        self.assertEqual("controller-1", bridge.state.active_controller_owner_id)

    def test_new_session_is_applied_through_runtime_boot(self):
        bridge = make_bridge()
        step = bridge.process_hello(candidate(), now_ms=0)
        self.assertTrue(step.negotiation_result.runtime_event_dispatched)
        self.assertTrue(step.runtime_result.accepted)
        self.assertEqual(Event.BOOT.value, step.runtime_result.event)
        self.assertEqual("session-1", bridge.runtime.state.session_id)
        self.assertIn("session-1", bridge.runtime.state.used_session_ids)

    def test_boot_complete_is_separate_and_reaches_disarmed(self):
        bridge = make_bridge()
        establish_session(bridge)
        self.assertEqual(RoverState.BOOT_SAFE, bridge.runtime.state.official_state)
        step = bridge.complete_boot(now_ms=1)
        self.assertTrue(step.runtime_result.accepted)
        self.assertEqual(RoverState.DISARMED, bridge.runtime.state.official_state)

    def test_adapter_prepares_arm_only_after_explicit_receiver_steps(self):
        bridge = prepare_drive_ready()
        self.assertEqual(RoverState.DRIVE_READY, bridge.runtime.state.official_state)
        self.assertTrue(bridge.runtime.state.armed)
        self.assertTrue(bridge.runtime.state.communication_alive)
        self.assertEqual(40, bridge.runtime.state.speed_limit)

    def test_matching_session_and_owner_command_reaches_runtime(self):
        bridge = prepare_disarmed()
        bridge.communication_restored(now_ms=2)
        step = bridge.receive(
            command_message(
                CommandType.SET_SPEED_LIMIT,
                1,
                3,
                speed_limit=40,
            ),
            now_ms=3,
        )
        self.assertEqual(
            AdapterDisposition.RUNTIME_INPUT_READY,
            step.adapter_result.disposition,
        )
        self.assertTrue(step.runtime_result.accepted)
        self.assertEqual(40, bridge.runtime.state.speed_limit)

    def test_wrong_session_is_rejected_before_runtime_dispatch(self):
        bridge = prepare_drive_ready()
        runtime_step = bridge.runtime.state.step_index
        state_before = bridge.runtime.state
        step = bridge.receive(
            command_message(
                CommandType.STOP,
                3,
                5,
                session_id="old-session",
            ),
            now_ms=5,
        )
        self.assertEqual(AdapterDisposition.REJECTED, step.adapter_result.disposition)
        self.assertEqual("invalid_session", step.adapter_result.rejection_reason)
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)
        self.assertEqual(state_before, bridge.runtime.state)

    def test_wrong_owner_is_rejected_before_runtime_dispatch(self):
        bridge = prepare_drive_ready()
        runtime_step = bridge.runtime.state.step_index
        step = bridge.receive(
            command_message(
                CommandType.STOP,
                3,
                5,
                sender_id="controller-2",
            ),
            now_ms=5,
        )
        self.assertEqual(AdapterDisposition.REJECTED, step.adapter_result.disposition)
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)

    def test_session_end_from_drive_active_performs_safety_stop(self):
        bridge = prepare_drive_active()
        step = bridge.end_session(
            session_end(
                sequence=4,
                freshness_reference_ms=7,
            ),
            now_ms=7,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ENDED,
            step.negotiation_result.disposition,
        )
        self.assertTrue(step.runtime_result.accepted)
        self.assertEqual(
            RoverState.COMM_LOSS_LATCHED,
            bridge.runtime.state.official_state,
        )
        self.assertTrue(bridge.runtime.state.communication_loss_latched)
        self.assertFalse(bridge.runtime.state.armed)
        self.assertFalse(bridge.runtime.state.deadman_active)
        self.assertEqual(0, bridge.runtime.state.left_output)
        self.assertIsNone(bridge.runtime.state.operation_id)
        self.assertIsNone(bridge.state.active_session_id)
        self.assertIsNone(bridge.receiver_context)

    def test_ended_session_reuse_is_rejected(self):
        bridge = prepare_drive_active()
        bridge.end_session(
            session_end(sequence=4, freshness_reference_ms=7),
            now_ms=7,
        )
        runtime_step = bridge.runtime.state.step_index
        step = bridge.process_hello(
            candidate(request_index=3),
            now_ms=8,
        )
        self.assertEqual(
            "session_id_reused",
            step.negotiation_result.rejection_reason,
        )
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)

    def test_safe_reconnect_requires_and_accepts_a_new_session(self):
        bridge = make_bridge()
        establish_session(bridge)
        bridge.end_session(session_end(), now_ms=1)
        step = bridge.process_hello(
            candidate(
                candidate_session_id="session-2",
                request_index=3,
            ),
            now_ms=2,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            step.negotiation_result.disposition,
        )
        self.assertEqual("session-2", bridge.runtime.state.session_id)
        self.assertEqual(
            ("session-1", "session-2"),
            bridge.state.used_session_ids,
        )

    def test_reconnect_does_not_restore_arm_deadman_or_operation(self):
        bridge = prepare_drive_active()
        bridge.receive(command_message(CommandType.STOP, 4, 7), now_ms=7)
        bridge.receive(command_message(CommandType.DISARM, 5, 8), now_ms=8)
        bridge.end_session(
            session_end(sequence=6, freshness_reference_ms=9),
            now_ms=9,
        )
        step = bridge.process_hello(
            candidate(
                candidate_session_id="session-2",
                request_index=3,
            ),
            now_ms=10,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            step.negotiation_result.disposition,
        )
        state = bridge.runtime.state
        self.assertEqual(RoverState.BOOT_SAFE, state.official_state)
        self.assertFalse(state.armed)
        self.assertFalse(state.deadman_active)
        self.assertEqual(0, state.left_output)
        self.assertIsNone(state.operation_id)
        self.assertIsNone(state.last_accepted_sequence)

    def test_drive_active_rejects_new_controller_without_runtime_dispatch(self):
        bridge = prepare_drive_active()
        runtime_step = bridge.runtime.state.step_index
        step = bridge.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                human_switch_confirmation=True,
                request_index=2,
            ),
            now_ms=7,
        )
        self.assertEqual(
            "controller_active",
            step.negotiation_result.rejection_reason,
        )
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)
        self.assertEqual(RoverState.DRIVE_ACTIVE, bridge.runtime.state.official_state)

    def test_safety_latch_rejects_session_establishment(self):
        bridge = make_bridge()
        bridge.runtime.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=0))
        runtime_step = bridge.runtime.state.step_index
        step = bridge.process_hello(candidate(), now_ms=1)
        self.assertEqual(
            "safety_latched",
            step.negotiation_result.rejection_reason,
        )
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)
        self.assertEqual(RoverState.FAULT_LATCHED, bridge.runtime.state.official_state)

    def test_boot_id_change_invalidates_old_session_and_context(self):
        bridge = prepare_drive_active()
        update = bridge.update_rover_boot_id(
            "boot-2",
            now_ms=7,
            request_index=2,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ENDED,
            update.negotiation_result.disposition,
        )
        self.assertIsNone(bridge.state.active_session_id)
        self.assertIsNone(bridge.receiver_context)
        self.assertEqual(
            RoverState.COMM_LOSS_LATCHED,
            bridge.runtime.state.official_state,
        )
        runtime_step = bridge.runtime.state.step_index
        old_command = bridge.receive(
            command_message(CommandType.STOP, 4, 8),
            now_ms=8,
        )
        self.assertEqual("invalid_session", old_command.rejection_reason)
        self.assertIsNone(old_command.adapter_result)
        self.assertIsNone(old_command.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)

    def test_session_acceptance_does_not_auto_boot_complete_or_arm(self):
        bridge = make_bridge()
        step = bridge.process_hello(candidate(), now_ms=0)
        state = bridge.runtime.state
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            step.negotiation_result.disposition,
        )
        self.assertEqual(RoverState.BOOT_SAFE, state.official_state)
        self.assertFalse(state.armed)
        self.assertFalse(state.deadman_active)
        self.assertFalse(state.communication_alive)
        self.assertEqual(0, state.left_output)
        self.assertIsNone(state.operation_id)

    def test_adapter_context_matches_manager_and_runtime_session(self):
        bridge = make_bridge()
        establish_session(bridge)
        context = bridge.receiver_context
        self.assertIsNotNone(context)
        self.assertEqual(bridge.state.active_session_id, context.active_session_id)
        self.assertEqual(bridge.runtime.state.session_id, context.active_session_id)
        self.assertEqual(
            bridge.state.active_controller_owner_id,
            context.active_controller_owner_id,
        )
        self.assertEqual(
            bridge.state.current_rover_boot_id,
            context.current_rover_boot_id,
        )

    def test_manager_rejection_keeps_runtime_step_and_state_unchanged(self):
        bridge = make_bridge()
        runtime_step = bridge.runtime.state.step_index
        state_before = bridge.runtime.state
        step = bridge.process_hello(
            candidate(rover_boot_id="wrong-boot"),
            now_ms=0,
        )
        self.assertEqual(
            "boot_id_mismatch",
            step.negotiation_result.rejection_reason,
        )
        self.assertFalse(step.negotiation_result.runtime_event_dispatched)
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)
        self.assertEqual(state_before, bridge.runtime.state)
        self.assertIsNone(bridge.receiver_context)

    def test_controller_switch_requires_safe_end_and_confirmation(self):
        bridge = prepare_disarmed()
        bridge.end_session(session_end(), now_ms=2)
        denied = bridge.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                request_index=3,
            ),
            now_ms=3,
        )
        self.assertEqual(
            "human_confirmation_required",
            denied.negotiation_result.rejection_reason,
        )
        accepted = bridge.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                human_switch_confirmation=True,
                request_index=4,
            ),
            now_ms=4,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            accepted.negotiation_result.disposition,
        )
        self.assertEqual("controller-2", bridge.state.active_controller_owner_id)

    def test_observer_candidate_never_dispatches_runtime(self):
        bridge = make_bridge()
        runtime_step = bridge.runtime.state.step_index
        step = bridge.process_hello(
            candidate(requested_role=SessionRole.OBSERVER),
            now_ms=0,
        )
        self.assertEqual(
            "role_unavailable",
            step.negotiation_result.rejection_reason,
        )
        self.assertFalse(step.negotiation_result.runtime_event_dispatched)
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)

    def test_session_end_requires_manager_path_not_generic_adapter_path(self):
        bridge = prepare_disarmed()
        context = bridge.receiver_context
        message = NormalizedLogicalMessage(
            protocol_version="v0",
            logical_message_type=LogicalMessageType.SESSION_END,
            direction=MessageDirection.CONTROLLER_TO_ROVER,
            rover_boot_id=context.current_rover_boot_id,
            session_id=context.active_session_id,
            sender_id=context.active_controller_owner_id,
            sender_role=SenderRole.CONTROLLER,
            controller_ownership=True,
            message_id="generic-session-end",
            sequence=1,
            freshness_reference_ms=2,
            ttl_ms=1_000,
            payload=None,
        )
        runtime_step = bridge.runtime.state.step_index
        step = bridge.receive(message, now_ms=2)
        self.assertEqual("invalid_message_type", step.rejection_reason)
        self.assertEqual(
            "SESSION_END_REQUIRES_MANAGER_PATH",
            step.diagnostic_code,
        )
        self.assertIsNone(step.adapter_result)
        self.assertIsNone(step.runtime_result)
        self.assertEqual(runtime_step, bridge.runtime.state.step_index)

    def test_no_active_session_never_fabricates_receiver_context(self):
        bridge = make_bridge()
        step = bridge.receive(
            command_message(CommandType.STOP, 1, 0),
            now_ms=0,
        )
        self.assertIsNone(bridge.receiver_context)
        self.assertIsNone(step.adapter_result)
        self.assertIsNone(step.runtime_result)
        self.assertEqual("invalid_session", step.rejection_reason)
        self.assertEqual("SESSION_NOT_ESTABLISHED", step.diagnostic_code)

    def test_same_inputs_produce_byte_identical_report(self):
        first = deterministic_report()
        second = deterministic_report()
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first).hexdigest(),
            hashlib.sha256(second).hexdigest(),
        )

    def test_report_has_no_absolute_or_nondeterministic_metadata(self):
        report = deterministic_report().decode("utf-8")
        for forbidden in (
            str(REPOSITORY_ROOT),
            "timestamp",
            "username",
            "hostname",
            "machine_name",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.lower(), report.lower())

    def test_session_module_uses_no_network_random_or_wall_clock(self):
        forbidden_imports = {
            "asyncio",
            "datetime",
            "http",
            "random",
            "requests",
            "secrets",
            "socket",
            "threading",
            "time",
            "uuid",
        }
        found = []
        for path in SESSION_DIRECTORY.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".", 1)[0] in forbidden_imports:
                            found.append((path.name, node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.split(".", 1)[0] in forbidden_imports:
                        found.append((path.name, node.lineno, node.module))
        self.assertEqual([], found)

    def test_z_protected_artifacts_and_bytecode_are_unchanged(self):
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
