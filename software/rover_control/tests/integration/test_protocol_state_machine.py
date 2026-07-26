from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "software/rover_control/simulator/virtual_rover"
VECTOR_DIRECTORY = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/test_vectors/vectors"
)
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "software/rover_control/protocol/v0/test_vectors/manifest/test-vector-manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "paddy_virtual_rover_integration_test",
    PACKAGE_DIRECTORY / "__init__.py",
    submodule_search_locations=[str(PACKAGE_DIRECTORY)],
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load virtual rover package")
VIRTUAL_ROVER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VIRTUAL_ROVER
SPEC.loader.exec_module(VIRTUAL_ROVER)


DeterministicRunner = VIRTUAL_ROVER.DeterministicRunner
Event = VIRTUAL_ROVER.Event
Profile = VIRTUAL_ROVER.Profile
RoverState = VIRTUAL_ROVER.RoverState
RuntimeConfig = VIRTUAL_ROVER.RuntimeConfig
RuntimeInput = VIRTUAL_ROVER.RuntimeInput
RuntimeStateMachine = VIRTUAL_ROVER.RuntimeStateMachine
VectorClassification = VIRTUAL_ROVER.VectorClassification
classify_vector_id = VIRTUAL_ROVER.classify_vector_id


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_vector(vector_id: str) -> dict:
    return json.loads(
        (VECTOR_DIRECTORY / f"{vector_id}.json").read_text(encoding="utf-8")
    )


def prepare_drive_ready(profile=Profile.ONE_SIDE_TEST):
    machine = RuntimeStateMachine(RuntimeConfig(profile=profile))
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
    return machine


def prepare_drive_active():
    machine = prepare_drive_ready()
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


def prepare_pto_active():
    machine = prepare_drive_ready(Profile.DRIVE_PTO_SPLIT_FIXTURE)
    machine.step(
        RuntimeInput.command(Event.SELECT_PTO, sequence=3, now_ms=4)
    )
    machine.step(RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=5))
    machine.step(
        RuntimeInput.command(Event.PTO_START, sequence=4, now_ms=6)
    )
    return machine


def execute_stop_reason_vector_case(vector_id):
    if vector_id == "PV0-VAL-018":
        machine = prepare_pto_active()
        runtime_input = RuntimeInput.command(
            Event.STOP,
            sequence=5,
            now_ms=7,
        )
    else:
        machine = prepare_drive_active()
        operation_id = machine.state.operation_id
        if vector_id == "PV0-VAL-005":
            runtime_input = RuntimeInput.command(
                Event.CONTROL_UPDATE,
                sequence=4,
                now_ms=6,
                operation_id=operation_id,
                deadman_asserted=False,
            )
        elif vector_id == "PV0-VAL-017":
            runtime_input = RuntimeInput.command(
                Event.STOP,
                sequence=4,
                now_ms=6,
            )
        elif vector_id == "PV0-VAL-020":
            runtime_input = RuntimeInput.command(
                Event.STOP,
                sequence=2,
                now_ms=6,
            )
        elif vector_id == "PV0-VAL-021":
            runtime_input = RuntimeInput.command(
                Event.STOP,
                sequence=4,
                now_ms=2_000,
                issued_at_ms=0,
                ttl_ms=1_000,
            )
        elif vector_id == "PV0-VAL-022":
            runtime_input = RuntimeInput.command(
                Event.STOP,
                sequence=4,
                now_ms=6,
                session_id="wrong-session",
            )
        elif vector_id == "PV0-VAL-027":
            runtime_input = RuntimeInput.command(
                Event.EMERGENCY_STOP,
                sequence=2,
                now_ms=6,
            )
        elif vector_id == "PV0-VAL-028":
            runtime_input = RuntimeInput.command(
                Event.EMERGENCY_STOP,
                sequence=4,
                now_ms=2_000,
                issued_at_ms=0,
                ttl_ms=1_000,
            )
        elif vector_id == "PV0-VAL-029":
            runtime_input = RuntimeInput.command(
                Event.EMERGENCY_STOP,
                sequence=4,
                now_ms=6,
                session_id="wrong-session",
            )
        else:
            raise AssertionError(f"unhandled stop-reason vector {vector_id}")
    last_accepted_before = machine.state.last_accepted_sequence
    result = machine.step(runtime_input)
    return machine, result, runtime_input.sequence, last_accepted_before


class ProtocolStateMachineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        input_paths = [
            REPOSITORY_ROOT / "software/rover_control/safety/SAFETY_REQUIREMENTS.md",
            REPOSITORY_ROOT / "software/rover_control/safety/STATE_MACHINE.md",
            REPOSITORY_ROOT / "software/rover_control/protocol/README.md",
            REPOSITORY_ROOT / "software/rover_control/protocol/v0/README.md",
            REPOSITORY_ROOT / "software/rover_control/protocol/v0/VALIDATION_ORDER.md",
        ]
        input_paths.extend(
            path
            for path in (
                REPOSITORY_ROOT
                / "software/rover_control/protocol/v0/test_vectors"
            ).rglob("*")
            if path.is_file()
        )
        cls.input_hashes_before = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): digest(path)
            for path in sorted(input_paths)
        }

    def scenario_inputs(self):
        return [
            RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=0),
            RuntimeInput.local("COMMUNICATION_CONNECTED", now_ms=1),
            RuntimeInput.command(
                Event.SET_SPEED_LIMIT,
                sequence=1,
                now_ms=2,
                speed_limit=40,
            ),
            RuntimeInput.command(Event.ARM, sequence=2, now_ms=3),
            RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=4),
            RuntimeInput.command(
                Event.MOVE_FORWARD,
                sequence=3,
                now_ms=5,
                requested_speed=20,
            ),
            RuntimeInput.command(
                Event.CONTROL_UPDATE,
                sequence=4,
                now_ms=100,
                operation_id="operation-0000000000000003",
                deadman_asserted=True,
            ),
            RuntimeInput.local(Event.TICK, now_ms=200),
            RuntimeInput.command(Event.STOP, sequence=5, now_ms=201),
        ]

    def test_official_state_set_matches_state_machine_document(self):
        self.assertEqual(
            {
                "BOOT_SAFE",
                "DISARMED",
                "ARMED_NEUTRAL",
                "DRIVE_READY",
                "DRIVE_ACTIVE",
                "PTO_READY",
                "PTO_ACTIVE",
                "COMM_LOSS_LATCHED",
                "FAULT_LATCHED",
                "EMERGENCY_STOP_LATCHED",
            },
            {state.value for state in RoverState},
        )

    def test_required_simulator_aliases_map_to_canonical_events(self):
        aliases = {
            "CLEAR_EMERGENCY_STOP": "emergency_stop_reset",
            "DEADMAN_RELEASE": "deadman_released",
            "COMMUNICATION_CONNECTED": "communication_restored",
            "COMMUNICATION_LOST": "communication_lost",
        }
        for alias, canonical in aliases.items():
            with self.subTest(alias=alias):
                self.assertEqual(canonical, VIRTUAL_ROVER.normalize_event(alias).value)

    def test_runner_report_is_byte_identical_for_same_inputs(self):
        runner = DeterministicRunner()
        first = runner.render(self.scenario_inputs()).encode("utf-8")
        second = runner.render(self.scenario_inputs()).encode("utf-8")
        self.assertEqual(first, second)

    def test_runner_reuse_has_no_cross_run_mutable_state(self):
        runner = DeterministicRunner()
        first = runner.run(self.scenario_inputs())
        second = runner.run(self.scenario_inputs())
        self.assertEqual(first, second)
        self.assertEqual("DRIVE_READY", first["final_state"]["official_state"])

    def test_runner_boot_cannot_clear_emergency_stop_latch(self):
        inputs = self.scenario_inputs()[:-1]
        inputs.extend(
            [
                RuntimeInput.command(
                    Event.EMERGENCY_STOP,
                    sequence=5,
                    now_ms=201,
                ),
                RuntimeInput.local(
                    Event.BOOT,
                    now_ms=0,
                    session_id="session-2",
                ),
                RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=202),
            ]
        )
        report = DeterministicRunner().run(inputs)
        boot_step = report["steps"][-2]
        self.assertFalse(boot_step["accepted"])
        self.assertEqual("safety_latched", boot_step["rejection_reason"])
        self.assertEqual(
            "BOOT_DOES_NOT_CLEAR_SAFETY_LATCH",
            boot_step["diagnostic_code"],
        )
        self.assertEqual(
            "EMERGENCY_STOP_LATCHED",
            report["final_state"]["official_state"],
        )
        self.assertTrue(report["final_state"]["emergency_stop_latched"])
        self.assertFalse(report["final_state"]["armed"])
        self.assertEqual(0, report["final_state"]["left_output"])

    def test_runner_compound_latch_reset_and_boot_bypass_is_blocked(self):
        inputs = self.scenario_inputs()[:-1]
        inputs.extend(
            [
                RuntimeInput.local(Event.COMMUNICATION_LOST, now_ms=201),
                RuntimeInput.local(Event.FAULT_DETECTED, now_ms=202),
                RuntimeInput.command(
                    Event.FAULT_RESET,
                    sequence=5,
                    now_ms=203,
                    safety_confirmation=True,
                ),
                RuntimeInput.local(
                    Event.BOOT,
                    now_ms=0,
                    session_id="session-2",
                ),
                RuntimeInput.local(Event.BOOT_COMPLETE, now_ms=204),
                RuntimeInput.local(
                    Event.COMMUNICATION_RESTORED,
                    now_ms=205,
                ),
                RuntimeInput.command(
                    Event.SET_SPEED_LIMIT,
                    sequence=5,
                    now_ms=206,
                    speed_limit=40,
                ),
                RuntimeInput.command(Event.ARM, sequence=6, now_ms=207),
                RuntimeInput.local(Event.DEADMAN_ASSERT, now_ms=208),
                RuntimeInput.command(
                    Event.MOVE_FORWARD,
                    sequence=7,
                    now_ms=209,
                    requested_speed=20,
                ),
            ]
        )
        report = DeterministicRunner().run(inputs)
        fault_reset_step = next(
            step
            for step in report["steps"]
            if step["event"] == Event.FAULT_RESET.value
        )
        self.assertFalse(fault_reset_step["accepted"])
        self.assertEqual(
            "FAULT_RESET_BLOCKED_BY_COMM_LOSS_LATCH",
            fault_reset_step["diagnostic_code"],
        )
        self.assertEqual(
            "FAULT_LATCHED",
            report["final_state"]["official_state"],
        )
        self.assertTrue(report["final_state"]["fault_latched"])
        self.assertTrue(report["final_state"]["communication_loss_latched"])
        self.assertFalse(report["final_state"]["armed"])
        self.assertEqual(0, report["final_state"]["left_output"])

    def test_report_has_no_absolute_or_nondeterministic_metadata(self):
        report = DeterministicRunner().render(self.scenario_inputs())
        lowered = report.lower()
        self.assertNotIn(str(REPOSITORY_ROOT).lower(), lowered)
        self.assertNotIn("timestamp", lowered)
        self.assertNotIn("username", lowered)
        self.assertNotIn("machine_name", lowered)
        self.assertNotIn("hostname", lowered)

    def test_each_step_exposes_required_runtime_fields(self):
        report = DeterministicRunner().run(self.scenario_inputs())
        expected = {
            "step_index",
            "previous_state",
            "official_state",
            "event",
            "accepted",
            "rejection_reason",
            "armed",
            "emergency_stop_latched",
            "deadman_active",
            "communication_alive",
            "selected_mode",
            "requested_speed",
            "effective_speed",
            "left_output",
            "right_output",
            "pto_requested",
            "pto_effective",
            "safety_action",
            "sequence_accepted",
            "last_accepted_sequence",
            "operation_id",
            "stop_reason",
            "diagnostic_code",
            "internal_failure",
        }
        self.assertEqual(expected, set(report["steps"][0]))
        self.assertEqual(
            list(range(1, len(report["steps"]) + 1)),
            [step["step_index"] for step in report["steps"]],
        )
        self.assertEqual("STOP", report["final_state"]["stop_reason"])

    def test_report_declares_real_motor_output_disabled(self):
        report = DeterministicRunner().run(self.scenario_inputs())
        self.assertFalse(report["real_motor_output_enabled"])
        self.assertTrue(all(step["right_output"] is None for step in report["steps"]))

    def test_all_38_vectors_have_explicit_runtime_classification(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        vector_ids = [row["vector_id"] for row in manifest["vectors"]]
        classifications = Counter(classify_vector_id(item) for item in vector_ids)
        self.assertEqual(38, len(vector_ids))
        self.assertEqual(
            26,
            classifications[VectorClassification.RUNTIME_CORE_MAPPING],
        )
        self.assertEqual(
            11,
            classifications[VectorClassification.VALIDATOR_ONLY],
        )
        self.assertEqual(
            1,
            classifications[VectorClassification.RUNTIME_CONTRACT_REQUIRED],
        )
        self.assertEqual(0, classifications[VectorClassification.UNMAPPED])

    def test_runtime_core_mapping_is_not_declared_as_full_vector_execution(self):
        readme = (PACKAGE_DIRECTORY / "README.md").read_text(encoding="utf-8")
        self.assertEqual(
            "runtime_core_mapping",
            VectorClassification.RUNTIME_CORE_MAPPING.value,
        )
        self.assertFalse(hasattr(VectorClassification, "SUPPORTED"))
        self.assertIn("not full vector execution", readme)
        self.assertIn("it is not a vector PASS result", readme)

    def test_validator_only_vectors_are_not_claimed_as_runtime_passes(self):
        for vector_id in {
            "PV0-VAL-006",
            "PV0-VAL-008",
            "PV0-VAL-009",
            "PV0-VAL-010",
            "PV0-VAL-013",
            "PV0-VAL-019",
            "PV0-VAL-023",
            "PV0-VAL-024",
            "PV0-VAL-026",
            "PV0-VAL-030",
            "PV0-VAL-031",
        }:
            with self.subTest(vector_id=vector_id):
                self.assertEqual(
                    VectorClassification.VALIDATOR_ONLY,
                    classify_vector_id(vector_id),
                )

    def test_move_vector_requires_runtime_speed_and_deadman_contract(self):
        vector = load_vector("PV0-VAL-002")
        message = vector["stimulus"]["message"]
        self.assertNotIn("requested_speed", message)
        self.assertNotIn("control_update_deadman", message)
        self.assertEqual(
            VectorClassification.RUNTIME_CONTRACT_REQUIRED,
            classify_vector_id("PV0-VAL-002"),
        )

    def test_arm_vector_final_states_match_runtime_profiles(self):
        one_side = prepare_drive_ready(Profile.ONE_SIDE_TEST)
        split = prepare_drive_ready(Profile.DRIVE_PTO_SPLIT_FIXTURE)
        self.assertEqual(
            load_vector("PV0-VAL-001A")["immediate_expectation"]["official_state"],
            one_side.state.official_state.value,
        )
        self.assertEqual(
            load_vector("PV0-VAL-001B")["immediate_expectation"]["official_state"],
            split.state.official_state.value,
        )

    def test_watchdog_vector_matches_runtime_transition(self):
        machine = prepare_drive_active()
        machine.step(RuntimeInput.local(Event.TICK, now_ms=755))
        vector = load_vector("PV0-VAL-004")
        self.assertEqual(
            vector["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertEqual(0, machine.state.left_output)
        self.assertFalse(machine.state.armed)

    def test_deadman_release_vector_matches_runtime_transition(self):
        machine = prepare_drive_active()
        machine.step(RuntimeInput.local("DEADMAN_RELEASE", now_ms=6))
        vector = load_vector("PV0-VAL-005")
        self.assertEqual(
            vector["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertEqual(0, machine.state.left_output)

    def test_stop_vector_matches_runtime_transition(self):
        machine = prepare_drive_active()
        machine.step(RuntimeInput.command(Event.STOP, sequence=4, now_ms=6))
        vector = load_vector("PV0-VAL-017")
        self.assertEqual(
            vector["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertIsNone(machine.state.operation_id)
        self.assertEqual(
            vector["immediate_expectation"]["stop_reason"],
            machine.state.stop_reason,
        )

    def test_nine_stop_reason_vectors_match_runtime_expressible_expectations(self):
        vector_ids = (
            "PV0-VAL-005",
            "PV0-VAL-017",
            "PV0-VAL-018",
            "PV0-VAL-020",
            "PV0-VAL-021",
            "PV0-VAL-022",
            "PV0-VAL-027",
            "PV0-VAL-028",
            "PV0-VAL-029",
        )
        for vector_id in vector_ids:
            with self.subTest(vector_id=vector_id):
                vector = load_vector(vector_id)
                expected = vector["immediate_expectation"]
                machine, result, stimulus_sequence, accepted_before = (
                    execute_stop_reason_vector_case(vector_id)
                )
                self.assertEqual(
                    expected["official_state"],
                    machine.state.official_state.value,
                )
                self.assertEqual(0, machine.state.left_output)
                self.assertFalse(machine.state.pto_effective)
                self.assertEqual(expected["armed"], machine.state.armed)
                self.assertIsNone(machine.state.operation_id)
                self.assertEqual(expected["stop_reason"], machine.state.stop_reason)
                self.assertEqual(expected["stop_reason"], result.stop_reason)
                if expected["last_accepted_command_sequence"] == "same":
                    self.assertEqual(
                        accepted_before,
                        machine.state.last_accepted_sequence,
                    )
                else:
                    self.assertEqual(
                        stimulus_sequence,
                        machine.state.last_accepted_sequence,
                    )
                self.assertEqual(
                    expected["applied_success"],
                    result.accepted,
                )

    def test_emergency_stop_and_reset_vectors_match_runtime(self):
        machine = prepare_drive_active()
        machine.step(
            RuntimeInput.command(Event.EMERGENCY_STOP, sequence=4, now_ms=6)
        )
        self.assertEqual(
            load_vector("PV0-VAL-025")["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        machine.step(
            RuntimeInput.command(
                Event.EMERGENCY_STOP_RESET,
                sequence=5,
                now_ms=7,
                safety_confirmation=True,
            )
        )
        self.assertEqual(
            load_vector("PV0-VAL-034")["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertFalse(machine.state.armed)

    def test_output_apply_failure_vector_matches_runtime_fault(self):
        machine = prepare_drive_ready()
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
        vector = load_vector("PV0-VAL-032")
        self.assertTrue(result.accepted)
        self.assertEqual(
            vector["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertEqual(
            vector["immediate_expectation"]["fault_reason"],
            machine.state.fault_reasons[-1],
        )
        self.assertEqual(
            vector["immediate_expectation"]["fault_reason"],
            result.stop_reason,
        )

    def test_session_end_vector_matches_communication_loss_transition(self):
        machine = prepare_drive_active()
        result = machine.step(
            RuntimeInput.command(Event.SESSION_END, sequence=4, now_ms=6)
        )
        vector = load_vector("PV0-VAL-036")
        self.assertEqual(
            vector["immediate_expectation"]["official_state"],
            machine.state.official_state.value,
        )
        self.assertFalse(machine.state.armed)
        self.assertEqual("communication_lost", result.stop_reason)

    def test_runtime_uses_only_standard_library_and_local_modules(self):
        allowed_imports = {
            "__future__",
            "collections.abc",
            "dataclasses",
            "enum",
            "json",
            "typing",
            "deterministic_runner",
            "model",
            "state_machine",
        }
        for path in PACKAGE_DIRECTORY.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    imports.add(node.module)
            with self.subTest(path=path.name):
                self.assertEqual(set(), imports - allowed_imports)

    def test_runtime_source_has_no_filesystem_or_hardware_write_calls(self):
        forbidden_calls = {
            "open",
            "write",
            "write_bytes",
            "write_text",
            "socket",
            "connect",
            "send",
        }
        found = []
        for path in PACKAGE_DIRECTORY.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        name = node.func.attr
                    else:
                        continue
                    if name in forbidden_calls:
                        found.append((path.name, node.lineno, name))
        self.assertEqual([], found)

    def test_z_repository_inputs_unchanged_and_no_bytecode_exists(self):
        input_paths = [
            REPOSITORY_ROOT / path
            for path in self.input_hashes_before
        ]
        hashes_after = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): digest(path)
            for path in input_paths
        }
        self.assertEqual(self.input_hashes_before, hashes_after)
        rover_root = REPOSITORY_ROOT / "software/rover_control"
        self.assertFalse(any(rover_root.rglob("*.pyc")))
        self.assertFalse(any(rover_root.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
