from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT))

from software.rover_control.protocol.v0.defensive_zero import (  # noqa: E402
    DefensiveZeroDisposition,
    DefensiveZeroExecutor,
    DefensiveZeroSourceStage,
)
from software.rover_control.protocol.v0.message_normalizer import (  # noqa: E402
    BoundaryStep,
    CandidateIntent,
    NormalizationDisposition,
    NormalizationResult,
)
from software.rover_control.simulator.virtual_rover import (  # noqa: E402
    Event,
    Profile,
    RoverState,
    RuntimeConfig,
    RuntimeInput,
    RuntimeStateMachine,
)


def prepare_disarmed(
    profile: Profile = Profile.ONE_SIDE_TEST,
) -> RuntimeStateMachine:
    machine = RuntimeStateMachine(RuntimeConfig(profile=profile))
    machine.step(RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0))
    machine.step(RuntimeInput.local(Event.COMMUNICATION_RESTORED, now_ms=1))
    return machine


def prepare_armed(
    profile: Profile = Profile.ONE_SIDE_TEST,
) -> RuntimeStateMachine:
    machine = prepare_disarmed(profile)
    machine.step(
        RuntimeInput.command(
            Event.SET_SPEED_LIMIT,
            sequence=1,
            now_ms=2,
            speed_limit=40,
        )
    )
    machine.step(RuntimeInput.command(Event.ARM, sequence=2, now_ms=3))
    return machine


def prepare_drive_active() -> RuntimeStateMachine:
    machine = prepare_armed()
    machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=4))
    machine.step(
        RuntimeInput.command(
            Event.MOVE_FORWARD,
            sequence=3,
            now_ms=5,
            requested_speed=20,
        )
    )
    return machine


def prepare_pto_ready() -> RuntimeStateMachine:
    machine = prepare_armed(Profile.DRIVE_PTO_SPLIT_FIXTURE)
    machine.step(
        RuntimeInput.command(Event.SELECT_PTO, sequence=3, now_ms=4)
    )
    return machine


def prepare_pto_active() -> RuntimeStateMachine:
    machine = prepare_pto_ready()
    machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
    machine.step(
        RuntimeInput.command(Event.PTO_START, sequence=4, now_ms=6)
    )
    return machine


def candidate_boundary_step(
    *,
    boundary_index: int = 1,
    intent: CandidateIntent | None = CandidateIntent.STOP,
    gate: bool = True,
    defensive: bool = True,
    disposition: NormalizationDisposition = (
        NormalizationDisposition.REJECTED
    ),
    runtime_result=None,
    internal_error: bool = False,
) -> BoundaryStep:
    normalization = NormalizationResult(
        disposition=disposition,
        rejection_reason=(
            "invalid_fixture"
            if disposition is NormalizationDisposition.REJECTED
            else None
        ),
        diagnostic_code=(
            "TEST_REJECTION"
            if disposition is NormalizationDisposition.REJECTED
            else None
        ),
        normalized_message=None,
        session_candidate=None,
        candidate_intent=intent,
        identification_gate_passed=gate,
        defensive_zero_candidate=defensive,
        normalizer_step_index=boundary_index,
        message_type_label="COMMAND" if intent is not None else None,
        runtime_dispatch_permitted=False,
        internal_error=internal_error,
    )
    return BoundaryStep(
        boundary_step_index=boundary_index,
        normalization_result=normalization,
        negotiation_result=None,
        adapter_result=None,
        runtime_result=runtime_result,
        downstream_rejection_reason=None,
        downstream_diagnostic_code=None,
        defensive_zero_candidate=defensive,
        runtime_event_dispatched=runtime_result is not None,
        internal_error=internal_error,
    )


class RuntimeDefensiveZeroLocalApiTests(unittest.TestCase):
    def assert_safe_zero(self, machine: RuntimeStateMachine) -> None:
        state = machine.state
        self.assertEqual(0, state.requested_speed)
        self.assertEqual(0, state.effective_speed)
        self.assertEqual(0, state.left_output)
        self.assertIsNone(state.right_output)
        self.assertFalse(state.pto_requested)
        self.assertFalse(state.pto_effective)
        self.assertIsNone(state.operation_id)
        self.assertFalse(state.deadman_active)
        self.assertIsNone(state.watchdog_deadline_ms)

    def test_receiver_local_api_state_matrix_preserves_safety_contract(self):
        def communication_latched():
            machine = prepare_drive_active()
            machine.step(
                RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=6)
            )
            return machine

        def fault_latched():
            machine = prepare_drive_active()
            machine.step(RuntimeInput.local(Event.FAULT_DETECTED, now_ms=6))
            return machine

        def estop_latched():
            machine = prepare_drive_active()
            machine.step(
                RuntimeInput.command(
                    Event.EMERGENCY_STOP,
                    sequence=4,
                    now_ms=6,
                )
            )
            return machine

        cases = (
            (prepare_drive_active, RoverState.DRIVE_READY),
            (prepare_pto_active, RoverState.PTO_READY),
            (prepare_armed, RoverState.DRIVE_READY),
            (prepare_pto_ready, RoverState.PTO_READY),
            (
                lambda: prepare_armed(Profile.DRIVE_PTO_SPLIT_FIXTURE),
                RoverState.ARMED_NEUTRAL,
            ),
            (prepare_disarmed, RoverState.DISARMED),
            (communication_latched, RoverState.COMM_LOSS_LATCHED),
            (fault_latched, RoverState.FAULT_LATCHED),
            (estop_latched, RoverState.EMERGENCY_STOP_LATCHED),
        )
        for factory, expected_state in cases:
            with self.subTest(expected_state=expected_state.value):
                machine = factory()
                before = machine.state
                latches = (
                    before.communication_loss_latched,
                    before.fault_latched,
                    before.emergency_stop_latched,
                )
                session_contract = (
                    before.session_id,
                    before.used_session_ids,
                    before.boot_session_ready,
                )
                result = machine.apply_defensive_zero(
                    now_ms=before.monotonic_time_ms,
                    candidate_intent="STOP",
                    rejection_reason="invalid_session",
                    diagnostic_code="SESSION_MISMATCH",
                )
                self.assertFalse(result.accepted)
                self.assertFalse(result.sequence_accepted)
                self.assertFalse(result.internal_failure)
                self.assertEqual("ZERO_ALL_OUTPUTS", result.safety_action)
                self.assertEqual(expected_state, machine.state.official_state)
                self.assertEqual(before.armed, machine.state.armed)
                self.assertEqual(
                    before.last_seen_sequence,
                    machine.state.last_seen_sequence,
                )
                self.assertEqual(
                    before.last_accepted_sequence,
                    machine.state.last_accepted_sequence,
                )
                self.assertEqual(
                    latches,
                    (
                        machine.state.communication_loss_latched,
                        machine.state.fault_latched,
                        machine.state.emergency_stop_latched,
                    ),
                )
                self.assertEqual(
                    session_contract,
                    (
                        machine.state.session_id,
                        machine.state.used_session_ids,
                        machine.state.boot_session_ready,
                    ),
                )
                self.assertEqual(
                    before.step_index + 1,
                    machine.state.step_index,
                )
                self.assert_safe_zero(machine)

    def test_stop_and_estop_intents_are_receiver_local_not_events(self):
        official_events = {event.value for event in Event}
        for intent in ("STOP", "EMERGENCY_STOP"):
            with self.subTest(intent=intent):
                machine = prepare_drive_active()
                result = machine.apply_defensive_zero(
                    now_ms=6,
                    candidate_intent=intent,
                    rejection_reason="invalid_session",
                    diagnostic_code="SESSION_MISMATCH",
                )
                self.assertFalse(result.accepted)
                self.assertNotIn(result.event, official_events)
                self.assertEqual(
                    f"receiver_local_defensive_zero/{intent}",
                    result.event,
                )
                if intent == "EMERGENCY_STOP":
                    self.assertFalse(
                        machine.state.emergency_stop_latched
                    )

    def test_invalid_intents_fail_closed_without_formal_event(self):
        for intent in ("", "UNKNOWN", None, 1, True):
            with self.subTest(intent=intent):
                machine = prepare_drive_active()
                before_seen = machine.state.last_seen_sequence
                before_accepted = machine.state.last_accepted_sequence
                result = machine.apply_defensive_zero(
                    now_ms=6,
                    candidate_intent=intent,
                    rejection_reason="invalid_session",
                    diagnostic_code="SESSION_MISMATCH",
                )
                self.assertTrue(result.internal_failure)
                self.assertFalse(result.accepted)
                self.assertFalse(result.sequence_accepted)
                self.assertEqual(
                    "receiver_local_defensive_zero",
                    result.event,
                )
                self.assertEqual(
                    RoverState.FAULT_LATCHED,
                    machine.state.official_state,
                )
                self.assertEqual(
                    before_seen,
                    machine.state.last_seen_sequence,
                )
                self.assertEqual(
                    before_accepted,
                    machine.state.last_accepted_sequence,
                )
                self.assert_safe_zero(machine)

    def test_equal_monotonic_time_is_valid(self):
        machine = prepare_drive_active()
        now_ms = machine.state.monotonic_time_ms
        result = machine.apply_defensive_zero(
            now_ms=now_ms,
            candidate_intent="STOP",
            rejection_reason="invalid_session",
            diagnostic_code="SESSION_MISMATCH",
        )
        self.assertFalse(result.internal_failure)
        self.assertEqual(now_ms, machine.state.monotonic_time_ms)

    def test_later_monotonic_time_is_valid(self):
        machine = prepare_drive_active()
        result = machine.apply_defensive_zero(
            now_ms=9,
            candidate_intent="STOP",
            rejection_reason="invalid_session",
            diagnostic_code="SESSION_MISMATCH",
        )
        self.assertFalse(result.internal_failure)
        self.assertEqual(9, machine.state.monotonic_time_ms)
        self.assertFalse(result.accepted)
        self.assertFalse(result.sequence_accepted)

    def test_invalid_time_fails_closed_and_preserves_sequences(self):
        for now_ms in (4, -1, True, "6"):
            with self.subTest(now_ms=now_ms):
                machine = prepare_drive_active()
                before_seen = machine.state.last_seen_sequence
                before_accepted = machine.state.last_accepted_sequence
                result = machine.apply_defensive_zero(
                    now_ms=now_ms,
                    candidate_intent="STOP",
                    rejection_reason="invalid_session",
                    diagnostic_code="SESSION_MISMATCH",
                )
                self.assertTrue(result.internal_failure)
                self.assertFalse(result.accepted)
                self.assertFalse(result.sequence_accepted)
                self.assertEqual(
                    before_seen,
                    machine.state.last_seen_sequence,
                )
                self.assertEqual(
                    before_accepted,
                    machine.state.last_accepted_sequence,
                )
                self.assert_safe_zero(machine)


class DefensiveZeroExecutorTests(unittest.TestCase):
    def test_executed_disposition_calls_local_api_once(self):
        machine = prepare_drive_active()
        executor = DefensiveZeroExecutor(machine)
        before = machine.state.step_index
        result = executor.evaluate(
            candidate_boundary_step(),
            now_ms=6,
        )
        self.assertEqual(
            DefensiveZeroDisposition.EXECUTED,
            result.disposition,
        )
        self.assertEqual(
            DefensiveZeroSourceStage.NORMALIZER,
            result.source_stage,
        )
        self.assertEqual(before + 1, machine.state.step_index)
        self.assertFalse(result.formal_acceptance)
        self.assertFalse(result.sequence_updated)
        self.assertTrue(result.operation_invalidated)

    def test_runtime_native_zero_is_not_applied_twice(self):
        machine = prepare_drive_active()
        native = machine.step(
            RuntimeInput.command(
                Event.STOP,
                sequence=2,
                now_ms=6,
            )
        )
        before = machine.state.step_index
        executor = DefensiveZeroExecutor(machine)
        result = executor.evaluate(
            candidate_boundary_step(runtime_result=native),
            now_ms=6,
        )
        self.assertEqual(
            DefensiveZeroDisposition.ALREADY_APPLIED_BY_RUNTIME,
            result.disposition,
        )
        self.assertEqual(before, machine.state.step_index)
        self.assertIs(native, result.runtime_result)

    def test_formal_command_is_not_reapplied(self):
        machine = prepare_drive_active()
        formal = machine.step(
            RuntimeInput.command(Event.STOP, sequence=4, now_ms=6)
        )
        before = machine.state.step_index
        executor = DefensiveZeroExecutor(machine)
        result = executor.evaluate(
            candidate_boundary_step(
                defensive=False,
                disposition=NormalizationDisposition.MESSAGE_NORMALIZED,
                runtime_result=formal,
            ),
            now_ms=6,
        )
        self.assertEqual(
            DefensiveZeroDisposition.FORMAL_COMMAND_APPLIED,
            result.disposition,
        )
        self.assertTrue(result.formal_acceptance)
        self.assertTrue(result.sequence_updated)
        self.assertEqual(before, machine.state.step_index)

    def test_gate_failure_is_not_applicable(self):
        machine = prepare_drive_active()
        before = machine.state
        executor = DefensiveZeroExecutor(machine)
        result = executor.evaluate(
            candidate_boundary_step(
                intent=None,
                gate=False,
                defensive=False,
                disposition=(
                    NormalizationDisposition.NO_MESSAGE_ACTION
                ),
            ),
            now_ms=6,
        )
        self.assertEqual(
            DefensiveZeroDisposition.NOT_APPLICABLE,
            result.disposition,
        )
        self.assertEqual(before, machine.state)
        self.assertFalse(result.output_zero_confirmed)

    def test_unexpected_executor_input_is_internal_error_and_safe(self):
        machine = prepare_drive_active()
        before = machine.state.step_index
        executor = DefensiveZeroExecutor(machine)
        result = executor.evaluate(object(), now_ms=6)
        self.assertEqual(
            DefensiveZeroDisposition.INTERNAL_ERROR,
            result.disposition,
        )
        self.assertTrue(result.internal_error)
        self.assertEqual(before + 1, machine.state.step_index)
        self.assertEqual(
            RoverState.FAULT_LATCHED,
            machine.state.official_state,
        )
        self.assertTrue(result.output_zero_confirmed)

    def test_same_boundary_step_is_idempotent(self):
        machine = prepare_drive_active()
        executor = DefensiveZeroExecutor(machine)
        step = candidate_boundary_step()
        first = executor.evaluate(step, now_ms=6)
        runtime_after_first = machine.state.step_index
        second = executor.evaluate(step, now_ms=99)
        self.assertIs(first, second)
        self.assertEqual(runtime_after_first, machine.state.step_index)
        self.assertEqual(1, executor.step_index)


if __name__ == "__main__":
    unittest.main(verbosity=2)
