from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "software/rover_control/simulator/virtual_rover"
SPEC = importlib.util.spec_from_file_location(
    "paddy_virtual_rover_safety_test",
    PACKAGE_DIRECTORY / "__init__.py",
    submodule_search_locations=[str(PACKAGE_DIRECTORY)],
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load virtual rover package")
VIRTUAL_ROVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VIRTUAL_ROVER
SPEC.loader.exec_module(VIRTUAL_ROVER)


Event = VIRTUAL_ROVER.Event
Profile = VIRTUAL_ROVER.Profile
RoverState = VIRTUAL_ROVER.RoverState
RuntimeConfig = VIRTUAL_ROVER.RuntimeConfig
RuntimeInput = VIRTUAL_ROVER.RuntimeInput
RuntimeStateMachine = VIRTUAL_ROVER.RuntimeStateMachine


class RuntimeStateMachineSafetyTests(unittest.TestCase):
    def prepare_drive_ready(self, machine=None):
        machine = machine or RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1))
        machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=2,
                speed_limit=40,
            )
        )
        result = machine.step(
            RuntimeInput.command(Event.ARM, sequence=2, now_ms=3)
        )
        self.assertTrue(result.accepted)
        return machine

    def prepare_split_neutral(self):
        machine = RuntimeStateMachine(
            RuntimeConfig(profile=Profile.DRIVE_PTO_SPLIT_FIXTURE)
        )
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1))
        machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=2,
                speed_limit=40,
            )
        )
        machine.step(RuntimeInput.command(Event.ARM, sequence=2, now_ms=3))
        self.assertEqual(RoverState.ARMED_NEUTRAL, machine.state.official_state)
        return machine

    def prepare_drive_active(self, machine=None):
        machine = self.prepare_drive_ready(machine)
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=4))
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=5,
                requested_speed=20,
            )
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DRIVE_ACTIVE, machine.state.official_state)
        return machine

    def prepare_pto_active(self):
        machine = self.prepare_split_neutral()
        machine.step(
            RuntimeInput.command(Event.SELECT_PTO, sequence=3, now_ms=4)
        )
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
        result = machine.step(
            RuntimeInput.command(Event.PTO_START, sequence=4, now_ms=6)
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.PTO_ACTIVE, machine.state.official_state)
        return machine

    def assert_latched_boot_rejected(self, machine, expected_state, latch_name):
        session_id = machine.state.session_id
        used_session_ids = machine.state.used_session_ids
        last_seen_sequence = machine.state.last_seen_sequence
        last_accepted_sequence = machine.state.last_accepted_sequence
        boot_session_ready = machine.state.boot_session_ready
        monotonic_time_ms = machine.state.monotonic_time_ms
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("safety_latched", result.rejection_reason)
        self.assertEqual(
            "BOOT_DOES_NOT_CLEAR_SAFETY_LATCH",
            result.diagnostic_code,
        )
        self.assertEqual("ZERO_ALL_OUTPUTS", result.safety_action)
        self.assertEqual(expected_state, machine.state.official_state)
        self.assertTrue(getattr(machine.state, latch_name))
        self.assertEqual(0, machine.state.left_output)
        self.assertFalse(machine.state.pto_effective)
        self.assertEqual(session_id, machine.state.session_id)
        self.assertEqual(used_session_ids, machine.state.used_session_ids)
        self.assertEqual(last_seen_sequence, machine.state.last_seen_sequence)
        self.assertEqual(
            last_accepted_sequence,
            machine.state.last_accepted_sequence,
        )
        self.assertEqual(boot_session_ready, machine.state.boot_session_ready)
        self.assertEqual(monotonic_time_ms, machine.state.monotonic_time_ms)
        return result

    def assert_compound_fault_reset_rejected(self, machine, sequence, now_ms):
        session_id = machine.state.session_id
        used_session_ids = machine.state.used_session_ids
        last_seen_sequence = machine.state.last_seen_sequence
        last_accepted_sequence = machine.state.last_accepted_sequence
        fault_reasons = machine.state.fault_reasons
        stop_reason = machine.state.stop_reason
        boot_session_ready = machine.state.boot_session_ready
        communication_alive = machine.state.communication_alive
        result = machine.step(
            RuntimeInput.command(
                Event.FAULT_RESET,
                sequence=sequence,
                now_ms=now_ms,
                safety_confirmation=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("safety_latched", result.rejection_reason)
        self.assertEqual(
            "FAULT_RESET_BLOCKED_BY_COMM_LOSS_LATCH",
            result.diagnostic_code,
        )
        self.assertEqual("ZERO_ALL_OUTPUTS", result.safety_action)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.fault_latched)
        self.assertTrue(machine.state.communication_loss_latched)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)
        self.assertFalse(machine.state.pto_effective)
        self.assertEqual(session_id, machine.state.session_id)
        self.assertEqual(used_session_ids, machine.state.used_session_ids)
        self.assertEqual(last_seen_sequence, machine.state.last_seen_sequence)
        self.assertEqual(
            last_accepted_sequence,
            machine.state.last_accepted_sequence,
        )
        self.assertEqual(fault_reasons, machine.state.fault_reasons)
        self.assertEqual(stop_reason, machine.state.stop_reason)
        self.assertEqual(boot_session_ready, machine.state.boot_session_ready)
        self.assertEqual(
            communication_alive,
            machine.state.communication_alive,
        )
        return result

    def test_boot_initial_state_is_safe(self):
        state = RuntimeStateMachine().state
        self.assertEqual(RoverState.BOOT_SAFE, state.official_state)
        self.assertFalse(state.armed)
        self.assertEqual(0, state.left_output)
        self.assertIsNone(state.right_output)
        self.assertFalse(state.pto_effective)

    def test_non_latched_boot_resets_runtime_without_restoring_motion(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.BOOT_SAFE, machine.state.official_state)
        self.assertEqual("session-2", machine.state.session_id)
        self.assertIsNone(machine.state.last_seen_sequence)
        self.assertIsNone(machine.state.last_accepted_sequence)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)
        self.assertFalse(machine.state.pto_effective)
        self.assertIsNone(machine.state.operation_id)

    def test_boot_requires_a_new_nonempty_session(self):
        machine = self.prepare_drive_active()
        missing = machine.step(RuntimeInput.local(Event.BOOT, now_ms=0))
        self.assertFalse(missing.accepted)
        self.assertEqual("missing_required_field", missing.rejection_reason)
        self.assertEqual("session-1", machine.state.session_id)
        self.assertEqual(3, machine.state.last_seen_sequence)

    def test_boot_rejects_current_session_without_resetting_sequence(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-1",
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("invalid_session", result.rejection_reason)
        self.assertEqual("BOOT_SESSION_REUSE_FORBIDDEN", result.diagnostic_code)
        self.assertEqual("session-1", machine.state.session_id)
        self.assertEqual(3, machine.state.last_seen_sequence)
        self.assertEqual(3, machine.state.last_accepted_sequence)
        self.assertEqual(5, machine.state.monotonic_time_ms)
        self.assertEqual(0, machine.state.left_output)

    def test_boot_rejects_any_previously_used_session_id(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-1",
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("invalid_session", result.rejection_reason)
        self.assertEqual("session-2", machine.state.session_id)
        self.assertEqual(("session-1", "session-2"), machine.state.used_session_ids)

    def test_boot_invalidates_old_session_and_starts_new_sequence_namespace(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=1))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=2))
        replay = machine.step(
            RuntimeInput.command(
                Event.STOP,
                sequence=3,
                now_ms=3,
                session_id="session-1",
            )
        )
        self.assertFalse(replay.accepted)
        self.assertEqual("invalid_session", replay.rejection_reason)
        self.assertIsNone(machine.state.last_seen_sequence)
        accepted = machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=4,
                session_id="session-2",
                speed_limit=30,
            )
        )
        self.assertTrue(accepted.accepted)
        self.assertEqual(1, machine.state.last_seen_sequence)
        self.assertEqual(1, machine.state.last_accepted_sequence)

    def test_boot_cannot_clear_emergency_stop_latch(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        self.assert_latched_boot_rejected(
            machine,
            RoverState.EMERGENCY_STOP_LATCHED,
            "emergency_stop_latched",
        )
        arm = machine.step(
            RuntimeInput.command(Event.ARM, sequence=5, now_ms=7)
        )
        move = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=6,
                now_ms=8,
                requested_speed=20,
            )
        )
        self.assertFalse(arm.accepted)
        self.assertFalse(move.accepted)
        self.assertEqual("safety_latched", arm.rejection_reason)
        self.assertEqual("safety_latched", move.rejection_reason)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )

    def test_boot_cannot_clear_fault_latch_before_fault_reset(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=6))
        self.assert_latched_boot_rejected(
            machine,
            RoverState.FAULT_LATCHED,
            "fault_latched",
        )
        second_boot = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=7,
                session_id="session-2",
            )
        )
        self.assertFalse(second_boot.accepted)
        self.assertEqual("safety_latched", second_boot.rejection_reason)
        reset = machine.step(
            RuntimeInput.command(
                Event.FAULT_RESET,
                sequence=4,
                now_ms=8,
                safety_confirmation=True,
            )
        )
        self.assertTrue(reset.accepted)
        self.assertEqual(RoverState.BOOT_SAFE, machine.state.official_state)
        boot = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        self.assertTrue(boot.accepted)
        self.assertEqual("session-2", machine.state.session_id)

    def test_boot_cannot_clear_communication_loss_latch(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
        )
        self.assert_latched_boot_rejected(
            machine,
            RoverState.COMM_LOSS_LATCHED,
            "communication_loss_latched",
        )
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_RESTORED, now_ms=7)
        )
        arm = machine.step(
            RuntimeInput.command(Event.ARM, sequence=4, now_ms=8)
        )
        move = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=5,
                now_ms=9,
                requested_speed=20,
            )
        )
        self.assertFalse(arm.accepted)
        self.assertFalse(move.accepted)
        self.assertEqual("safety_latched", arm.rejection_reason)
        self.assertEqual("safety_latched", move.rejection_reason)
        self.assertEqual(
            RoverState.COMM_LOSS_LATCHED,
            machine.state.official_state,
        )

    def test_boot_complete_sequence_cannot_bypass_any_safety_latch(self):
        cases = (
            (
                RoverState.EMERGENCY_STOP_LATCHED,
                lambda machine: machine.step(
                    RuntimeInput.command(
                        Event.EMERGENCY_STOP,
                        sequence=4,
                        now_ms=6,
                    )
                ),
            ),
            (
                RoverState.FAULT_LATCHED,
                lambda machine: machine.step(
                    RuntimeInput.local(Event.FAULT_DETECTED, now_ms=6)
                ),
            ),
            (
                RoverState.COMM_LOSS_LATCHED,
                lambda machine: machine.step(
                    RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
                ),
            ),
        )
        for expected_state, latch_action in cases:
            with self.subTest(expected_state=expected_state.value):
                machine = self.prepare_drive_active()
                latch_action(machine)
                next_sequence = (
                    machine.state.last_seen_sequence or 0
                ) + 1
                boot = machine.step(
                    RuntimeInput.local(
                        Event.BOOT,
                        now_ms=0,
                        session_id="session-2",
                    )
                )
                boot_complete = machine.step(
                    RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=7)
                )
                machine.step(
                    RuntimeInput.local(
                        Event.COMMUNICATION_RESTORED,
                        now_ms=8,
                    )
                )
                arm = machine.step(
                    RuntimeInput.command(
                        Event.ARM,
                        sequence=next_sequence,
                        now_ms=9,
                    )
                )
                machine.step(
                    RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=10)
                )
                move = machine.step(
                    RuntimeInput.command(
                        Event.MOVE_FORWARD,
                        sequence=next_sequence + 1,
                        now_ms=11,
                        requested_speed=20,
                    )
                )
                self.assertFalse(boot.accepted)
                self.assertFalse(boot_complete.accepted)
                self.assertFalse(arm.accepted)
                self.assertFalse(move.accepted)
                self.assertEqual(expected_state, machine.state.official_state)
                self.assertNotEqual(
                    RoverState.DRIVE_ACTIVE,
                    machine.state.official_state,
                )
                self.assertFalse(machine.state.armed)
                self.assertEqual(0, machine.state.left_output)

    def test_boot_complete_enters_disarmed(self):
        machine = RuntimeStateMachine()
        result = machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)

    def test_boot_failure_latches_fault_and_zeroes_outputs(self):
        machine = RuntimeStateMachine()
        result = machine.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=0))
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.fault_latched)
        self.assertEqual("LATCH_FAULT", result.safety_action)

    def test_arm_requires_live_communication(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=1,
                speed_limit=30,
            )
        )
        result = machine.step(
            RuntimeInput.command(Event.ARM, sequence=2, now_ms=2)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)

    def test_arm_requires_valid_speed_limit(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1))
        result = machine.step(
            RuntimeInput.command(Event.ARM, sequence=1, now_ms=2)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)

    def test_explicit_arm_enters_drive_ready_for_one_side_profile(self):
        machine = self.prepare_drive_ready()
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertTrue(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_reconnect_does_not_arm(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        result = machine.step(
            RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1)
        )
        self.assertTrue(result.accepted)
        self.assertFalse(machine.state.armed)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)

    def test_split_profile_arm_enters_armed_neutral(self):
        machine = self.prepare_split_neutral()
        self.assertTrue(machine.state.armed)
        self.assertEqual("NEUTRAL", machine.state.selected_mode.value)

    def test_move_without_deadman_is_rejected(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=4,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_move_is_accepted_only_with_deadman(self):
        machine = self.prepare_drive_active()
        self.assertTrue(machine.state.deadman_active)
        self.assertEqual(20, machine.state.requested_speed)
        self.assertEqual(20, machine.state.effective_speed)
        self.assertEqual(20, machine.state.left_output)
        self.assertIsNotNone(machine.state.operation_id)

    def test_deadman_release_stops_immediately(self):
        machine = self.prepare_drive_active()
        result = machine.step(RuntimeInput.local("DEADMAN_RELEASE", now_ms=6))
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)
        self.assertFalse(machine.state.deadman_active)
        self.assertIsNone(machine.state.operation_id)
        self.assertEqual("deadman_released", result.stop_reason)

    def test_valid_control_update_extends_liveness_without_new_operation(self):
        machine = self.prepare_drive_active()
        operation_id = machine.state.operation_id
        accepted_sequence = machine.state.last_accepted_sequence
        result = machine.step(
            RuntimeInput.command(
                Event.CONTROL_UPDATE,
                sequence=4,
                now_ms=100,
                operation_id=operation_id,
                deadman_asserted=True,
            )
        )
        self.assertTrue(result.accepted)
        self.assertFalse(result.sequence_accepted)
        self.assertEqual(accepted_sequence, machine.state.last_accepted_sequence)
        self.assertEqual(operation_id, machine.state.operation_id)
        self.assertEqual(850, machine.state.watchdog_deadline_ms)

    def test_tick_before_watchdog_deadline_preserves_motion(self):
        machine = self.prepare_drive_active()
        result = machine.step(RuntimeInput.local(Event.TICK, now_ms=754))
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DRIVE_ACTIVE, machine.state.official_state)

    def test_tick_at_watchdog_deadline_latches_communication_loss(self):
        machine = self.prepare_drive_active()
        result = machine.step(RuntimeInput.local(Event.TICK, now_ms=755))
        self.assertEqual("WATCHDOG_EXPIRED", result.diagnostic_code)
        self.assertEqual(RoverState.COMM_LOSS_LATCHED, machine.state.official_state)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)
        self.assertEqual("communication_lost", result.stop_reason)

    def test_explicit_watchdog_timeout_stops_motion(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(Event.WATCHDOG_TIMEOUT, now_ms=6)
        )
        self.assertEqual("LATCH_COMMUNICATION_LOSS", result.safety_action)
        self.assertEqual(RoverState.COMM_LOSS_LATCHED, machine.state.official_state)

    def test_communication_loss_stops_and_disarms(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local("COMMUNICATION_LOST", now_ms=6))
        self.assertEqual(RoverState.COMM_LOSS_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.communication_loss_latched)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_reconnect_does_not_clear_communication_latch(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local("COMMUNICATION_LOST", now_ms=6))
        result = machine.step(
            RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=7)
        )
        self.assertTrue(result.accepted)
        self.assertTrue(machine.state.communication_alive)
        self.assertEqual(RoverState.COMM_LOSS_LATCHED, machine.state.official_state)
        self.assertFalse(machine.state.armed)

    def test_duplicate_reconnect_in_drive_active_is_idempotent(self):
        machine = self.prepare_drive_active()
        operation_id = machine.state.operation_id
        result = machine.step(
            RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=6)
        )
        self.assertTrue(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual(RoverState.DRIVE_ACTIVE, machine.state.official_state)
        self.assertTrue(machine.state.communication_alive)
        self.assertTrue(machine.state.deadman_active)
        self.assertEqual(operation_id, machine.state.operation_id)
        self.assertEqual(20, machine.state.left_output)

    def test_arm_is_rejected_while_communication_latched(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local("COMMUNICATION_LOST", now_ms=6))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=7))
        result = machine.step(
            RuntimeInput.command(Event.ARM, sequence=4, now_ms=8)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("safety_latched", result.rejection_reason)

    def test_duplicate_sequence_is_rejected(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(Event.STOP, sequence=2, now_ms=4)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("duplicate_sequence", result.rejection_reason)

    def test_stale_sequence_is_rejected(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(Event.MOVE_FORWARD, sequence=1, now_ms=4)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("stale_sequence", result.rejection_reason)

    def test_expired_command_is_rejected_and_never_replayed(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=100,
                issued_at_ms=0,
                ttl_ms=50,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("expired", result.rejection_reason)
        replay = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=101,
                requested_speed=20,
            )
        )
        self.assertEqual("duplicate_sequence", replay.rejection_reason)

    def test_sequence_gap_is_rejected_fail_closed(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(Event.STOP, sequence=5, now_ms=4)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_payload", result.rejection_reason)
        self.assertEqual(
            "SEQUENCE_GAP_POLICY_FAIL_CLOSED",
            result.diagnostic_code,
        )

    def test_wrong_session_is_rejected(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=4,
                session_id="old-session",
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_session", result.rejection_reason)
        self.assertEqual(2, machine.state.last_accepted_sequence)

    def test_defensive_stop_records_stop_reason_without_acceptance(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(
                Event.STOP,
                sequence=4,
                now_ms=6,
                session_id="old-session",
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_session", result.rejection_reason)
        self.assertEqual("STOP", result.stop_reason)
        self.assertEqual("STOP", machine.state.stop_reason)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_emergency_stop_zeroes_and_latches(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        self.assertTrue(result.accepted)
        self.assertEqual("LATCH_EMERGENCY_STOP", result.safety_action)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_emergency_stop_clear_requires_all_guards(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        result = machine.step(
            RuntimeInput.command(
                "CLEAR_EMERGENCY_STOP",
                sequence=5,
                now_ms=7,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )

    def test_emergency_stop_clear_enters_disarmed_only(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        result = machine.step(
            RuntimeInput.command(
                "CLEAR_EMERGENCY_STOP",
                sequence=5,
                now_ms=7,
                safety_confirmation=True,
            )
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_clear_does_not_resume_or_allow_move_without_rearm(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        machine.step(
            RuntimeInput.command(
                Event.EMERGENCY_STOP_RESET,
                sequence=5,
                now_ms=7,
                safety_confirmation=True,
            )
        )
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=6,
                now_ms=8,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)

    def test_fault_during_estop_keeps_estop_priority_and_fault_reason(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=7))
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertTrue(machine.state.fault_latched)
        self.assertIn("fault_detected", machine.state.fault_reasons)
        self.assertEqual("EMERGENCY_STOP", machine.state.stop_reason)

    def test_boot_complete_with_physical_estop_cannot_enter_disarmed(self):
        machine = RuntimeStateMachine()
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT_COMPLETE,
                now_ms=0,
                physical_estop_asserted=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertTrue(machine.state.emergency_stop_latched)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_boot_complete_with_fault_cannot_enter_disarmed(self):
        machine = RuntimeStateMachine()
        result = machine.step(
            RuntimeInput.local(
                Event.BOOT_COMPLETE,
                now_ms=0,
                fault_present=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.fault_latched)
        self.assertIn("fault_present", machine.state.fault_reasons)

    def test_physical_estop_preempts_active_command_and_zeroes_immediately(self):
        machine = self.prepare_drive_active()
        operation_id = machine.state.operation_id
        result = machine.step(
            RuntimeInput.command(
                Event.CONTROL_UPDATE,
                sequence=4,
                now_ms=6,
                operation_id=operation_id,
                deadman_asserted=True,
                physical_estop_asserted=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.sequence_accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual(3, machine.state.last_seen_sequence)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertTrue(machine.state.emergency_stop_latched)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)
        self.assertIsNone(machine.state.operation_id)

    def test_physical_estop_priority_retains_simultaneous_fault_reason(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(
                Event.TICK,
                now_ms=6,
                physical_estop_asserted=True,
                fault_present=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertTrue(machine.state.emergency_stop_latched)
        self.assertTrue(machine.state.fault_latched)
        self.assertIn("fault_present", machine.state.fault_reasons)
        self.assertEqual("EMERGENCY_STOP", machine.state.stop_reason)

    def test_physical_estop_preempts_unknown_software_event(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(
                "UNKNOWN_COMMAND",
                now_ms=6,
                physical_estop_asserted=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("PHYSICAL_ESTOP_ASSERTED", result.diagnostic_code)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertEqual(0, machine.state.left_output)

    def test_physical_estop_preempts_invalid_monotonic_time(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.local(
                Event.TICK,
                now_ms=4,
                physical_estop_asserted=True,
            )
        )
        self.assertFalse(result.accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual(
            RoverState.EMERGENCY_STOP_LATCHED,
            machine.state.official_state,
        )
        self.assertEqual(5, machine.state.monotonic_time_ms)
        self.assertEqual(0, machine.state.left_output)


    def test_one_side_profile_rejects_pto(self):
        machine = self.prepare_drive_ready()
        result = machine.step(
            RuntimeInput.command(Event.PTO_START, sequence=3, now_ms=4)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("capability_unavailable", result.rejection_reason)

    def test_split_profile_can_start_pto_only_from_pto_ready(self):
        machine = self.prepare_pto_active()
        self.assertTrue(machine.state.pto_requested)
        self.assertTrue(machine.state.pto_effective)
        self.assertEqual(0, machine.state.left_output)

    def test_pto_active_rejects_move_and_fails_closed(self):
        machine = self.prepare_pto_active()
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=5,
                now_ms=7,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("mode_conflict", result.rejection_reason)
        self.assertEqual(RoverState.PTO_READY, machine.state.official_state)
        self.assertFalse(machine.state.pto_effective)

    def test_drive_active_rejects_pto_start_and_fails_closed(self):
        machine = self.prepare_split_neutral()
        machine.step(
            RuntimeInput.command(Event.SELECT_DRIVE, sequence=3, now_ms=4)
        )
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
        machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=4,
                now_ms=6,
                requested_speed=20,
            )
        )
        result = machine.step(
            RuntimeInput.command(Event.PTO_START, sequence=5, now_ms=7)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("mode_conflict", result.rejection_reason)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_drive_to_pto_switch_requires_stop_and_neutral(self):
        machine = self.prepare_split_neutral()
        machine.step(
            RuntimeInput.command(Event.SELECT_DRIVE, sequence=3, now_ms=4)
        )
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
        machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=4,
                now_ms=6,
                requested_speed=20,
            )
        )
        machine.step(RuntimeInput.command(Event.STOP, sequence=5, now_ms=7))
        machine.step(
            RuntimeInput.command(Event.SELECT_NEUTRAL, sequence=6, now_ms=8)
        )
        result = machine.step(
            RuntimeInput.command(Event.SELECT_PTO, sequence=7, now_ms=9)
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.PTO_READY, machine.state.official_state)

    def test_disarm_zeroes_drive_output(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(Event.DISARM, sequence=4, now_ms=6)
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_disarmed_move_is_rejected(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1))
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=1,
                now_ms=2,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_state", result.rejection_reason)
        self.assertEqual(0, machine.state.left_output)

    def test_unknown_event_rejects_and_zeroes_active_output(self):
        machine = self.prepare_drive_active()
        result = machine.step(RuntimeInput.local("UNKNOWN_COMMAND", now_ms=6))
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_message_type", result.rejection_reason)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_internal_exception_is_diagnostic_and_fault_latched(self):
        machine = self.prepare_drive_active()
        with mock.patch.object(machine, "_dispatch", side_effect=RuntimeError("injected")):
            result = machine.step(RuntimeInput.local(Event.TICK, now_ms=6))
        self.assertTrue(result.internal_failure)
        self.assertEqual("INTERNAL_RUNTIMEERROR", result.diagnostic_code)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_output_apply_failure_is_formally_accepted_but_fault_latched(self):
        machine = self.prepare_drive_ready()
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=4))
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=5,
                requested_speed=20,
                output_apply_success=False,
            )
        )
        self.assertTrue(result.accepted)
        self.assertTrue(result.sequence_accepted)
        self.assertFalse(result.internal_failure)
        self.assertEqual("OUTPUT_APPLY_FAILED", result.diagnostic_code)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)
        self.assertEqual("output_apply_failed", result.stop_reason)

    def test_direction_reversal_requires_zero_transition(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(
                Event.MOVE_REVERSE,
                sequence=4,
                now_ms=6,
                requested_speed=20,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)
        self.assertEqual(
            "DIRECTION_REVERSAL_REQUIRES_ZERO",
            result.diagnostic_code,
        )
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_backwards_monotonic_time_is_internal_failure_and_zero(self):
        machine = self.prepare_drive_active()
        result = machine.step(RuntimeInput.local(Event.TICK, now_ms=4))
        self.assertTrue(result.internal_failure)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_invalid_speed_limit_is_rejected_without_arming(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        result = machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=1,
                speed_limit=0,
            )
        )
        self.assertFalse(result.accepted)
        self.assertEqual("invalid_payload", result.rejection_reason)
        self.assertEqual(0, machine.state.speed_limit)

    def test_pto_start_requires_deadman_in_split_fixture(self):
        machine = self.prepare_split_neutral()
        machine.step(
            RuntimeInput.command(Event.SELECT_PTO, sequence=3, now_ms=4)
        )
        result = machine.step(
            RuntimeInput.command(Event.PTO_START, sequence=4, now_ms=5)
        )
        self.assertFalse(result.accepted)
        self.assertEqual("guard_failed", result.rejection_reason)
        self.assertEqual(RoverState.PTO_READY, machine.state.official_state)

    def test_session_end_is_communication_loss_safety_transition(self):
        machine = self.prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(Event.SESSION_END, sequence=4, now_ms=6)
        )
        self.assertTrue(result.accepted)
        self.assertFalse(result.sequence_accepted)
        self.assertEqual(RoverState.COMM_LOSS_LATCHED, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)

    def test_stop_is_idempotent_in_drive_ready(self):
        machine = self.prepare_drive_ready()
        first = machine.step(
            RuntimeInput.command(Event.STOP, sequence=3, now_ms=4)
        )
        second = machine.step(
            RuntimeInput.command(Event.STOP, sequence=4, now_ms=5)
        )
        self.assertTrue(first.accepted)
        self.assertTrue(second.accepted)
        self.assertEqual(RoverState.DRIVE_READY, machine.state.official_state)
        self.assertEqual(0, machine.state.left_output)
        self.assertEqual("STOP", first.stop_reason)
        self.assertEqual("STOP", second.stop_reason)

    def test_communication_loss_while_disarmed_does_not_arm_or_latch(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
        machine.step(RuntimeInput.local("COMMUNICATION_LOST", now_ms=1))
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)
        self.assertFalse(machine.state.armed)
        self.assertFalse(machine.state.communication_loss_latched)

    def test_fault_reset_returns_to_boot_safe_not_ready(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=0))
        result = machine.step(
            RuntimeInput.command(
                Event.FAULT_RESET,
                sequence=1,
                now_ms=1,
                safety_confirmation=True,
            )
        )
        self.assertTrue(result.accepted)
        self.assertEqual(RoverState.BOOT_SAFE, machine.state.official_state)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_fault_reset_requires_new_boot_session_before_boot_complete(self):
        machine = RuntimeStateMachine()
        machine.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=0))
        machine.step(
            RuntimeInput.command(
                Event.FAULT_RESET,
                sequence=1,
                now_ms=1,
                safety_confirmation=True,
            )
        )
        blocked = machine.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=2)
        )
        self.assertFalse(blocked.accepted)
        self.assertEqual("guard_failed", blocked.rejection_reason)
        self.assertEqual(RoverState.BOOT_SAFE, machine.state.official_state)
        booted = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        self.assertTrue(booted.accepted)
        completed = machine.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=1)
        )
        self.assertTrue(completed.accepted)
        self.assertEqual(RoverState.DISARMED, machine.state.official_state)

    def test_fault_reset_is_blocked_after_communication_loss_then_fault(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
        )
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=7))
        self.assertIn("fault_detected", machine.state.fault_reasons)
        self.assert_compound_fault_reset_rejected(
            machine,
            sequence=4,
            now_ms=8,
        )

    def test_fault_reset_is_blocked_after_fault_then_communication_loss(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=6))
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=7)
        )
        self.assertIn("fault_detected", machine.state.fault_reasons)
        self.assertEqual("communication_lost", machine.state.stop_reason)
        self.assert_compound_fault_reset_rejected(
            machine,
            sequence=4,
            now_ms=8,
        )

    def test_boot_failed_compound_latch_cannot_reset_or_boot_around_comm_loss(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
        )
        machine.step(RuntimeInput.local(Event.BOOT_FAILED, now_ms=7))
        self.assertIn("boot_failed", machine.state.fault_reasons)
        self.assert_compound_fault_reset_rejected(
            machine,
            sequence=4,
            now_ms=8,
        )
        boot = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        boot_complete = machine.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=9)
        )
        self.assertFalse(boot.accepted)
        self.assertFalse(boot_complete.accepted)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.communication_loss_latched)
        self.assertEqual(0, machine.state.left_output)

    def test_compound_fault_and_comm_loss_cannot_reach_drive_active(self):
        machine = self.prepare_drive_active()
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
        )
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=7))
        reset = self.assert_compound_fault_reset_rejected(
            machine,
            sequence=4,
            now_ms=8,
        )
        boot = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        boot_complete = machine.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=9)
        )
        machine.step(
            RuntimeInput.local(Event.COMMUNICATION_RESTORED, now_ms=10)
        )
        speed_limit = machine.step(
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=4,
                now_ms=11,
                speed_limit=40,
            )
        )
        arm = machine.step(
            RuntimeInput.command(Event.ARM, sequence=5, now_ms=12)
        )
        machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=13))
        move = machine.step(
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=6,
                now_ms=14,
                requested_speed=20,
            )
        )
        self.assertFalse(reset.accepted)
        self.assertFalse(boot.accepted)
        self.assertFalse(boot_complete.accepted)
        self.assertFalse(speed_limit.accepted)
        self.assertFalse(arm.accepted)
        self.assertFalse(move.accepted)
        self.assertEqual(RoverState.FAULT_LATCHED, machine.state.official_state)
        self.assertTrue(machine.state.fault_latched)
        self.assertTrue(machine.state.communication_loss_latched)
        self.assertFalse(machine.state.armed)
        self.assertEqual(0, machine.state.left_output)

    def test_standalone_fault_reset_still_enters_boot_safe(self):
        machine = self.prepare_drive_active()
        machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=6))
        self.assertFalse(machine.state.communication_loss_latched)
        reset = machine.step(
            RuntimeInput.command(
                Event.FAULT_RESET,
                sequence=4,
                now_ms=7,
                safety_confirmation=True,
            )
        )
        self.assertTrue(reset.accepted)
        self.assertEqual(RoverState.BOOT_SAFE, machine.state.official_state)
        self.assertFalse(machine.state.fault_latched)
        self.assertFalse(machine.state.communication_loss_latched)
        blocked = machine.step(
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=8)
        )
        self.assertFalse(blocked.accepted)
        boot = machine.step(
            RuntimeInput.local(
                Event.BOOT,
                now_ms=0,
                session_id="session-2",
            )
        )
        self.assertTrue(boot.accepted)
        self.assertEqual("session-2", machine.state.session_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
