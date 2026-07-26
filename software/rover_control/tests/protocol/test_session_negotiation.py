from __future__ import annotations

import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT))

from software.rover_control.protocol.v0.session_negotiation import (  # noqa: E402
    NegotiationDisposition,
    ReceiverPolicy,
    RuntimeSynchronizationState,
    SessionCandidate,
    SessionEndRequest,
    SessionNegotiationManager,
    SessionRole,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    Event,
    Profile,
    RoverState,
    RuntimeConfig,
    RuntimeInput,
    RuntimeStateMachine,
)


MAX_SAFE_SEQUENCE = 9_007_199_254_740_991


def runtime_config(
    profile: Profile = Profile.ONE_SIDE_TEST,
) -> RuntimeConfig:
    return RuntimeConfig(
        profile=profile,
        max_command_ttl_ms=5_000,
        max_speed=100,
        session_id="runtime-bootstrap",
        real_motor_output_enabled=False,
    )


def receiver_policy(config: RuntimeConfig) -> ReceiverPolicy:
    return ReceiverPolicy(
        runtime_profile=config.profile.value,
        capability_profile_reference=f"{config.profile.value}-capabilities-v0",
        max_ttl_ms=config.max_command_ttl_ms,
        max_safe_sequence=MAX_SAFE_SEQUENCE,
        max_speed=config.max_speed,
        drive_available=True,
        turn_left_available=False,
        turn_right_available=False,
        pto_available=config.pto_available,
        right_output_available=config.right_output_available,
    )


def make_manager(
    runtime: RuntimeStateMachine | None = None,
    *,
    used: tuple[str, ...] = (),
) -> SessionNegotiationManager:
    runtime = runtime or RuntimeStateMachine(runtime_config())
    return SessionNegotiationManager(
        current_rover_boot_id="boot-1",
        supported_protocol_versions=("v0",),
        runtime=runtime,
        receiver_policy=receiver_policy(runtime.config),
        initial_used_session_ids=used,
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


def end_request(**overrides) -> SessionEndRequest:
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


def prepare_runtime_state(state: RoverState) -> RuntimeStateMachine:
    profile = (
        Profile.DRIVE_PTO_SPLIT_FIXTURE
        if state in {RoverState.ARMED_NEUTRAL, RoverState.PTO_ACTIVE}
        else Profile.ONE_SIDE_TEST
    )
    runtime = RuntimeStateMachine(runtime_config(profile))
    if state is RoverState.BOOT_SAFE:
        return runtime
    if state is RoverState.FAULT_LATCHED:
        runtime.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=0))
        return runtime
    if state is RoverState.EMERGENCY_STOP_LATCHED:
        runtime.step(
            RuntimeInput.local(
                Event.TICK,
                now_ms=0,
                physical_estop_asserted=True,
            )
        )
        return runtime

    runtime.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
    if state is RoverState.DISARMED:
        return runtime
    runtime.step(
        RuntimeInput.local(Event.COMMUNICATION_RESTORED, now_ms=1)
    )
    runtime.step(
        RuntimeInput.command(
            Event.SET_SPEED_LIMIT,
            sequence=1,
            now_ms=2,
            session_id="runtime-bootstrap",
            speed_limit=40,
        )
    )
    runtime.step(
        RuntimeInput.command(
            Event.ARM,
            sequence=2,
            now_ms=3,
            session_id="runtime-bootstrap",
        )
    )
    if state is RoverState.ARMED_NEUTRAL:
        return runtime
    if profile is Profile.DRIVE_PTO_SPLIT_FIXTURE:
        runtime.step(
            RuntimeInput.command(
                Event.SELECT_PTO,
                sequence=3,
                now_ms=4,
                session_id="runtime-bootstrap",
            )
        )
        runtime.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
        runtime.step(
            RuntimeInput.command(
                Event.PTO_START,
                sequence=4,
                now_ms=6,
                session_id="runtime-bootstrap",
            )
        )
    else:
        runtime.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=4))
        runtime.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=5,
                session_id="runtime-bootstrap",
                requested_speed=20,
            )
        )
    if state is RoverState.COMM_LOSS_LATCHED:
        runtime.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=7)
        )
    return runtime


class SessionNegotiationUnitTests(unittest.TestCase):
    def test_version_selection_accepts_supported_candidate(self):
        manager = make_manager()
        action = manager.process_hello(
            candidate(protocol_versions=("v9", "v0")),
            now_ms=0,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            action.result.disposition,
        )
        self.assertEqual("v0", action.result.selected_protocol_version)
        self.assertTrue(action.result.controller_ownership)

    def test_version_selection_rejects_unsupported_without_runtime_dispatch(self):
        manager = make_manager()
        runtime_step = manager.runtime.state.step_index
        action = manager.process_hello(
            candidate(protocol_versions=("v9",)),
            now_ms=0,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_REJECTED,
            action.result.disposition,
        )
        self.assertEqual("unsupported_version", action.result.rejection_reason)
        self.assertFalse(action.result.runtime_event_dispatched)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_version_candidate_structure_is_table_driven(self):
        cases = (
            ((), "PROTOCOL_VERSION_CANDIDATES_INVALID"),
            (["v0"], "PROTOCOL_VERSION_CANDIDATES_INVALID"),
            (("v0", "v0"), "PROTOCOL_VERSION_CANDIDATES_DUPLICATED"),
            ((True,), "PROTOCOL_VERSION_CANDIDATES_INVALID"),
        )
        for versions, diagnostic in cases:
            with self.subTest(versions=versions):
                manager = make_manager()
                action = manager.process_hello(
                    candidate(protocol_versions=versions),
                    now_ms=0,
                )
                self.assertEqual("malformed_candidate", action.result.rejection_reason)
                self.assertEqual(diagnostic, action.result.diagnostic_code)
                self.assertIsNone(action.runtime_result)

    def test_boot_id_match_is_accepted(self):
        action = make_manager().process_hello(candidate(), now_ms=0)
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            action.result.disposition,
        )
        self.assertEqual("boot-1", action.result.rover_boot_id)

    def test_boot_id_mismatch_is_rejected_without_runtime_dispatch(self):
        manager = make_manager()
        runtime_step = manager.runtime.state.step_index
        action = manager.process_hello(
            candidate(rover_boot_id="boot-old"),
            now_ms=0,
        )
        self.assertEqual("boot_id_mismatch", action.result.rejection_reason)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_empty_boot_id_is_malformed(self):
        action = make_manager().process_hello(
            candidate(rover_boot_id=""),
            now_ms=0,
        )
        self.assertEqual("malformed_candidate", action.result.rejection_reason)
        self.assertEqual(
            "SESSION_CANDIDATE_IDENTITY_INVALID",
            action.result.diagnostic_code,
        )

    def test_first_session_id_is_recorded_only_after_runtime_boot_acceptance(self):
        manager = make_manager()
        action = manager.process_hello(candidate(), now_ms=0)
        self.assertTrue(action.runtime_result.accepted)
        self.assertEqual("session-1", manager.state.active_session_id)
        self.assertEqual(("session-1",), manager.state.used_session_ids)
        self.assertEqual("session-1", manager.runtime.state.session_id)
        self.assertIsNotNone(manager.receiver_context)

    def test_active_session_reuse_is_rejected(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        runtime_step = manager.runtime.state.step_index
        replay = manager.process_hello(
            candidate(request_index=2),
            now_ms=1,
        )
        self.assertEqual("session_id_reused", replay.result.rejection_reason)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_ended_session_reuse_is_rejected_and_history_is_retained(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        ended = manager.end_session(end_request(), now_ms=1)
        self.assertEqual(
            NegotiationDisposition.SESSION_ENDED,
            ended.result.disposition,
        )
        replay = manager.process_hello(
            candidate(request_index=3),
            now_ms=2,
        )
        self.assertEqual("session_id_reused", replay.result.rejection_reason)
        self.assertIn("session-1", manager.state.used_session_ids)
        self.assertIsNone(manager.receiver_context)

    def test_session_id_empty_wrong_type_and_runtime_history_are_rejected(self):
        cases = (
            ("", "malformed_candidate"),
            (True, "malformed_candidate"),
            ("runtime-bootstrap", "session_id_reused"),
        )
        for session_id, reason in cases:
            with self.subTest(session_id=session_id):
                action = make_manager().process_hello(
                    candidate(candidate_session_id=session_id),
                    now_ms=0,
                )
                self.assertEqual(reason, action.result.rejection_reason)
                self.assertFalse(action.result.runtime_event_dispatched)

    def test_first_controller_is_accepted_and_second_is_not_auto_switched(self):
        manager = make_manager()
        first = manager.process_hello(candidate(), now_ms=0)
        runtime_step = manager.runtime.state.step_index
        second = manager.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                human_switch_confirmation=True,
                request_index=2,
            ),
            now_ms=1,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            first.result.disposition,
        )
        self.assertEqual("controller_active", second.result.rejection_reason)
        self.assertEqual("controller-1", manager.state.active_controller_owner_id)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_same_sender_reconnect_requires_new_session_but_not_switch(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        manager.end_session(end_request(), now_ms=1)
        old = manager.process_hello(
            candidate(request_index=3),
            now_ms=2,
        )
        new = manager.process_hello(
            candidate(
                candidate_session_id="session-2",
                request_index=4,
            ),
            now_ms=3,
        )
        self.assertEqual("session_id_reused", old.result.rejection_reason)
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            new.result.disposition,
        )
        self.assertEqual("session-2", manager.state.active_session_id)

    def test_session_end_sender_mismatch_is_rejected_before_runtime(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        runtime_step = manager.runtime.state.step_index
        action = manager.end_session(
            end_request(sender_id="controller-2"),
            now_ms=1,
        )
        self.assertEqual("controller_active", action.result.rejection_reason)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)
        self.assertEqual("session-1", manager.state.active_session_id)

    def test_controller_switch_requires_human_confirmation_after_safe_end(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        manager.runtime.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=1)
        )
        manager.end_session(
            end_request(freshness_reference_ms=2),
            now_ms=2,
        )
        denied = manager.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                request_index=3,
            ),
            now_ms=3,
        )
        accepted = manager.process_hello(
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
            "human_confirmation_required",
            denied.result.rejection_reason,
        )
        self.assertEqual(
            NegotiationDisposition.SESSION_ACCEPTED,
            accepted.result.disposition,
        )
        self.assertEqual("controller-2", manager.state.active_controller_owner_id)

    def test_controller_switch_is_rejected_from_boot_safe_even_if_confirmed(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        manager.end_session(end_request(), now_ms=1)
        runtime_step = manager.runtime.state.step_index
        action = manager.process_hello(
            candidate(
                candidate_session_id="session-2",
                sender_id="controller-2",
                sender_instance_id="controller-instance-2",
                human_switch_confirmation=True,
                request_index=3,
            ),
            now_ms=2,
        )
        self.assertEqual("runtime_not_safe", action.result.rejection_reason)
        self.assertEqual(
            "CONTROLLER_SWITCH_REQUIRES_DISARMED",
            action.result.diagnostic_code,
        )
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_runtime_safety_state_matrix_is_fail_closed(self):
        cases = (
            (RoverState.BOOT_SAFE, NegotiationDisposition.SESSION_ACCEPTED, None),
            (RoverState.DISARMED, NegotiationDisposition.SESSION_ACCEPTED, None),
            (
                RoverState.ARMED_NEUTRAL,
                NegotiationDisposition.SESSION_REJECTED,
                "runtime_not_safe",
            ),
            (
                RoverState.DRIVE_ACTIVE,
                NegotiationDisposition.SESSION_REJECTED,
                "runtime_not_safe",
            ),
            (
                RoverState.PTO_ACTIVE,
                NegotiationDisposition.SESSION_REJECTED,
                "runtime_not_safe",
            ),
            (
                RoverState.COMM_LOSS_LATCHED,
                NegotiationDisposition.SESSION_REJECTED,
                "safety_latched",
            ),
            (
                RoverState.FAULT_LATCHED,
                NegotiationDisposition.SESSION_REJECTED,
                "safety_latched",
            ),
            (
                RoverState.EMERGENCY_STOP_LATCHED,
                NegotiationDisposition.SESSION_REJECTED,
                "safety_latched",
            ),
        )
        for state, disposition, reason in cases:
            with self.subTest(state=state.value):
                runtime = prepare_runtime_state(state)
                manager = make_manager(runtime)
                runtime_step = runtime.state.step_index
                action = manager.process_hello(
                    candidate(),
                    now_ms=runtime.state.monotonic_time_ms + 1,
                )
                self.assertEqual(disposition, action.result.disposition)
                self.assertEqual(reason, action.result.rejection_reason)
                if disposition is NegotiationDisposition.SESSION_REJECTED:
                    self.assertEqual(runtime_step, runtime.state.step_index)

    def test_observer_is_role_unavailable_and_never_dispatches_runtime(self):
        manager = make_manager()
        runtime_step = manager.runtime.state.step_index
        action = manager.process_hello(
            candidate(requested_role=SessionRole.OBSERVER),
            now_ms=0,
        )
        self.assertEqual("role_unavailable", action.result.rejection_reason)
        self.assertEqual("OBSERVER_ROLE_HOLD", action.result.diagnostic_code)
        self.assertIsNone(action.runtime_result)
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_manager_runtime_context_mismatch_is_fail_closed(self):
        manager = make_manager()
        manager.process_hello(candidate(), now_ms=0)
        manager.runtime._state = replace(
            manager.runtime.state,
            session_id="unexpected-session",
        )
        runtime_step = manager.runtime.state.step_index
        action = manager.process_hello(
            candidate(
                candidate_session_id="session-2",
                request_index=2,
            ),
            now_ms=1,
        )
        self.assertEqual("runtime_not_safe", action.result.rejection_reason)
        self.assertEqual(
            "MANAGER_RUNTIME_CONTEXT_MISMATCH",
            action.result.diagnostic_code,
        )
        self.assertEqual(runtime_step, manager.runtime.state.step_index)

    def test_result_indices_generation_and_state_are_deterministic(self):
        def execute() -> bytes:
            manager = make_manager()
            accepted = manager.process_hello(candidate(), now_ms=0)
            payload = {
                "result": accepted.result.report_dict(),
                "runtime": accepted.runtime_result.report_dict(),
            }
            return (
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")

        first = execute()
        second = execute()
        self.assertEqual(first, second)
        self.assertEqual(1, make_manager().state.negotiation_step_index + 1)
        self.assertEqual(64, len(hashlib.sha256(first).hexdigest()))
        lowered = first.decode("utf-8").lower()
        for forbidden in (
            str(REPOSITORY_ROOT).lower(),
            "timestamp",
            "username",
            "hostname",
            "random",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_boot_id_change_invalidates_session_without_clearing_latches(self):
        runtime = prepare_runtime_state(RoverState.FAULT_LATCHED)
        manager = make_manager(runtime)
        before = runtime.state
        action = manager.update_rover_boot_id(
            "boot-2",
            now_ms=1,
            request_index=1,
        )
        self.assertEqual(
            NegotiationDisposition.NO_CHANGE,
            action.result.disposition,
        )
        self.assertEqual("boot-2", manager.state.current_rover_boot_id)
        self.assertTrue(runtime.state.fault_latched)
        self.assertEqual(before.official_state, runtime.state.official_state)
        self.assertIsNone(manager.receiver_context)

    def test_runtime_boot_acceptance_does_not_boot_complete_or_arm(self):
        manager = make_manager()
        action = manager.process_hello(candidate(), now_ms=0)
        self.assertTrue(action.runtime_result.accepted)
        self.assertEqual(RoverState.BOOT_SAFE, manager.runtime.state.official_state)
        self.assertFalse(manager.runtime.state.armed)
        self.assertEqual(0, manager.runtime.state.left_output)
        self.assertIsNone(manager.runtime.state.operation_id)
        self.assertEqual(
            RuntimeSynchronizationState.SYNCHRONIZED.value,
            manager.state.runtime_synchronization_state,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
