from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from corrected_progressive_print_plan import (
    PRINT_STEPS,
    validate_corrected_dependencies,
)
from final_gate_contract import (
    BASE_CORE_OUTPUTS,
    BASE_GENERATOR_IDENTITY,
    BASE_MANIFEST_SCHEMA,
    CONNECTIVITY_CORE_OUTPUTS,
    CONNECTIVITY_GENERATOR_IDENTITY,
    CONNECTIVITY_MANIFEST_SCHEMA,
    audit_repository_bytecode,
    compare_connectivity_core_outputs,
    compare_existing_stls,
    validate_base_fixture,
    validate_connectivity_fixture,
    validate_execution_order,
    validate_final_test_consistency,
)
from part_number_registry import ALL_PARTS, validate_registry
from physical_connection_model import (
    build_physical_connection_graph,
    validate_physical_connection_graph,
)
from validate_connectivity_correction import (
    validate_completeness_status,
)


def _edge_graph(predicate, **changes):
    graph = build_physical_connection_graph()
    edge = next(item for item in graph["edges"] if predicate(item))
    edge.update(changes)
    return graph


class ConnectivityNegativeCaseTests(unittest.TestCase):
    def assertGraphRejects(self, graph, token):
        result = validate_physical_connection_graph(graph)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(
            any(token in blocker for blocker in result["blockers"]),
            result["blockers"],
        )

    def test_t_nut_on_slotless_profile3_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: edge["interface_id"] == "AI-01",
                retention_method="METAL T-NUT IN PROFILE SLOT",
            ),
            "T_NUT",
        )

    def test_corner_connection_without_contact_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: (
                    "front_frame_corner_connector_left" in edge["nodes"]
                ),
                geometric_contact_exists=False,
                retention_exists=False,
            ),
            "LOOSE_PLACEMENT",
        )

    def test_rail_crossmember_loose_placement_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: set(edge["nodes"])
                == {
                    "front_frame_corner_connector_left",
                    "fpb_front_crossmember_dummy",
                },
                retention_exists=False,
            ),
            "LOOSE_PLACEMENT",
        )

    def test_cbox_saddle_loose_placement_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: "cbox_saddle_left" in edge["nodes"],
                retention_exists=False,
            ),
            "LOOSE_PLACEMENT",
        )

    def test_bbox_support_loose_placement_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: "bbox_support_front" in edge["nodes"],
                retention_exists=False,
            ),
            "LOOSE_PLACEMENT",
        )

    def test_float_adapter_loose_placement_rejected(self):
        self.assertGraphRejects(
            _edge_graph(
                lambda edge: "lower_float_adapter_left" in edge["nodes"],
                retention_exists=False,
            ),
            "LOOSE_PLACEMENT",
        )

    def test_p3_before_future_mate_rejected(self):
        changed = list(PRINT_STEPS)
        changed[0] = replace(
            changed[0],
            gates_available_at_step=("P0", "P1", "P2", "P3"),
        )
        result = validate_corrected_dependencies(tuple(changed))
        self.assertIn(
            "P3_REQUIRED_BEFORE_MATING_PART_EXISTS", result["blockers"]
        )

    def test_p4_before_future_growth_dependency_rejected(self):
        changed = list(PRINT_STEPS)
        changed[0] = replace(
            changed[0],
            gates_available_at_step=("P0", "P1", "P2", "P4"),
        )
        result = validate_corrected_dependencies(tuple(changed))
        self.assertIn(
            "P4_REQUIRED_BEFORE_ASSEMBLY_DEPENDENCY_EXISTS",
            result["blockers"],
        )

    def test_dependency_cycle_or_future_requirement_rejected(self):
        changed = list(PRINT_STEPS)
        changed[0] = replace(
            changed[0],
            print_prerequisites=(changed[1].part_key,),
        )
        result = validate_corrected_dependencies(tuple(changed))
        self.assertTrue(
            "DEPENDENCY_CYCLE" in result["blockers"]
            or "STEP_REQUIRES_FUTURE_PART" in result["blockers"]
        )

    def test_mirror_unlocked_by_p0_p2_only_rejected(self):
        changed = list(PRINT_STEPS)
        changed[3] = replace(
            changed[3],
            mirror_unlock_condition=(
                "front_frame_corner_connector_left P0/P1/P2 ONLY"
            ),
        )
        result = validate_corrected_dependencies(tuple(changed))
        self.assertTrue(
            any(
                blocker.startswith("MIRROR_UNLOCK_")
                for blocker in result["blockers"]
            ),
            result["blockers"],
        )

    def test_disconnected_graph_and_orphan_rejected(self):
        graph = build_physical_connection_graph()
        key = "pin_retainer_cover"
        graph["edges"] = [
            edge for edge in graph["edges"] if key not in edge["nodes"]
        ]
        result = validate_physical_connection_graph(graph)
        self.assertIn(
            "DISCONNECTED_FINAL_ASSEMBLY_GRAPH", result["blockers"]
        )
        self.assertIn("ORPHAN_PRINTED_PART", result["blockers"])

    def test_glue_only_and_tape_only_rejected(self):
        self.assertGraphRejects(
            _edge_graph(lambda edge: True, retention_method="GLUE ONLY"),
            "GLUE_ONLY",
        )
        self.assertGraphRejects(
            _edge_graph(lambda edge: True, retention_method="TAPE ONLY"),
            "TAPE_ONLY",
        )

    def test_missing_part_number_and_dummy_only_rejected(self):
        with self.assertRaises(ValueError):
            validate_registry(
                (
                    *ALL_PARTS[:19],
                    replace(ALL_PARTS[19], part_number=""),
                    *ALL_PARTS[20:],
                )
            )
        with self.assertRaises(ValueError):
            validate_registry(
                (
                    *ALL_PARTS[:19],
                    replace(
                        ALL_PARTS[19],
                        classification_marking="NO LOAD",
                    ),
                    *ALL_PARTS[20:],
                )
            )

    def test_ai10_silent_approval_rejected(self):
        graph = build_physical_connection_graph()
        graph["ai10_reservation"]["AI10_CLEARANCE_STATUS"] = "PASS"
        self.assertGraphRejects(graph, "AI10_CLEARANCE_SILENTLY_APPROVED")

    def test_unknown_float_body_generation_rejected(self):
        graph = build_physical_connection_graph()
        graph["float_body_boundary"]["float_body_generated"] = True
        self.assertGraphRejects(
            graph, "UNKNOWN_FLOAT_HARDPOINT_BODY_GENERATED"
        )

    def test_full_dummy_pass_while_float_body_hold_rejected(self):
        blockers = validate_completeness_status(
            {
                "CENTRAL_DRY_DUMMY_PART_SET_COMPLETE": "PASS",
                "FLOAT_INTERFACE_DRY_DUMMY_COMPLETE": "PASS",
                "FLOAT_BODY_SET_COMPLETE": "HOLD",
                "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE": "HOLD",
                "FULL_DUMMY_PRINT": "HOLD",
                "FULL_DUMMY_PART_SET_COMPLETE": "PASS",
            }
        )
        self.assertIn(
            "FULL_DUMMY_PASS_WHILE_FLOAT_BODY_HOLD", blockers
        )

        def write_fixture(
            root: Path,
            schema: str,
            generator: str,
            files: tuple[str, ...],
        ) -> None:
            root.mkdir(parents=True, exist_ok=True)
            for name in files:
                (root / name).write_bytes(b"fixture\n")
            (root / "dummy_kit_manifest.json").write_text(
                json.dumps(
                    {
                        "schema": schema,
                        "generator_identity": generator,
                        "core_output_contract": {
                            "count": len(files),
                            "files": files,
                            "packaging_files_excluded": True,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory(
            prefix="pfd_final_gate_negative_"
        ) as temporary:
            root = Path(temporary)
            base = root / "base"
            connectivity_a = root / "connectivity_a"
            connectivity_b = root / "connectivity_b"
            write_fixture(
                base,
                BASE_MANIFEST_SCHEMA,
                BASE_GENERATOR_IDENTITY,
                BASE_CORE_OUTPUTS,
            )
            write_fixture(
                connectivity_a,
                CONNECTIVITY_MANIFEST_SCHEMA,
                CONNECTIVITY_GENERATOR_IDENTITY,
                CONNECTIVITY_CORE_OUTPUTS,
            )
            write_fixture(
                connectivity_b,
                CONNECTIVITY_MANIFEST_SCHEMA,
                CONNECTIVITY_GENERATOR_IDENTITY,
                CONNECTIVITY_CORE_OUTPUTS,
            )

            with self.subTest("connectivity passed to base fixture"):
                audit = validate_base_fixture(connectivity_a)
                self.assertIn(
                    "CONNECTIVITY_FIXTURE_USED_FOR_BASE",
                    audit["blockers"],
                )
            with self.subTest("base passed to connectivity fixture"):
                audit = validate_connectivity_fixture(base)
                self.assertIn(
                    "BASE_FIXTURE_USED_FOR_CONNECTIVITY",
                    audit["blockers"],
                )
            with self.subTest("first-only SHA256SUMS"):
                (connectivity_a / "SHA256SUMS.txt").write_text(
                    "bad\n", encoding="utf-8"
                )
                audit = compare_connectivity_core_outputs(
                    connectivity_a, connectivity_b
                )
                self.assertIn(
                    "PACKAGING_FILE_IN_CORE_REPLAY",
                    audit["blockers"],
                )
                self.assertIn(
                    "DETERMINISM_FILE_SET_MISMATCH",
                    audit["blockers"],
                )
                (connectivity_a / "SHA256SUMS.txt").unlink()
            with self.subTest("first-only unit test output"):
                (connectivity_a / "unit_test_results.json").write_text(
                    "{}\n", encoding="utf-8"
                )
                audit = compare_connectivity_core_outputs(
                    connectivity_a, connectivity_b
                )
                self.assertIn(
                    "PACKAGING_FILE_IN_CORE_REPLAY",
                    audit["blockers"],
                )
                (connectivity_a / "unit_test_results.json").unlink()
            with self.subTest("packaging file included"):
                (connectivity_a / "source.patch").write_text(
                    "bad\n", encoding="utf-8"
                )
                audit = compare_connectivity_core_outputs(
                    connectivity_a, connectivity_b
                )
                self.assertIn(
                    "PACKAGING_FILE_IN_CORE_REPLAY",
                    audit["blockers"],
                )
                (connectivity_a / "source.patch").unlink()
            with self.subTest("different generators"):
                audit = compare_connectivity_core_outputs(
                    base, connectivity_b
                )
                self.assertIn(
                    "DETERMINISM_GENERATOR_MISMATCH",
                    audit["blockers"],
                )
            with self.subTest("untracked bytecode and pycache"):
                cache = root / "repository" / "__pycache__"
                cache.mkdir(parents=True)
                (cache / "untracked.cpython-312.pyc").write_bytes(b"x")
                audit = audit_repository_bytecode(root / "repository")
                self.assertIn("REPOSITORY_PYC_PRESENT", audit["blockers"])
                self.assertIn(
                    "REPOSITORY_PYCACHE_PRESENT", audit["blockers"]
                )
            with self.subTest("post-cleanliness import"):
                audit = validate_execution_order(
                    [
                        "REPOSITORY_PYTHON_EXECUTION",
                        "FINAL_REPOSITORY_CLEANLINESS_SCAN",
                        "REPOSITORY_PYTHON_EXECUTION",
                    ]
                )
                self.assertIn(
                    "POST_CLEANLINESS_PYTHON_EXECUTION",
                    audit["blockers"],
                )
            with self.subTest("artifact pass external fail"):
                artifact_json = root / "artifact.json"
                external_json = root / "external.json"
                artifact_text = root / "artifact.txt"
                external_text = root / "external.txt"
                good = {
                    "tests_run": 75,
                    "failures": 0,
                    "errors": 0,
                    "successful": True,
                    "run_id": "same",
                }
                bad = {**good, "failures": 1, "successful": False}
                artifact_json.write_text(
                    json.dumps(good), encoding="utf-8"
                )
                external_json.write_text(
                    json.dumps(bad), encoding="utf-8"
                )
                artifact_text.write_text("PASS", encoding="utf-8")
                external_text.write_text("FAIL", encoding="utf-8")
                audit = validate_final_test_consistency(
                    artifact_json,
                    artifact_text,
                    external_json,
                    external_text,
                )
                self.assertIn(
                    "FINAL_TEST_RESULT_INCONSISTENT",
                    audit["blockers"],
                )
            with self.subTest("one of 33 STL bytes changes"):
                reference = root / "reference"
                candidate = root / "candidate"
                reference.mkdir()
                candidate.mkdir()
                filenames = tuple(part.filename for part in ALL_PARTS)
                for name in filenames:
                    (reference / name).write_bytes(b"stable")
                    (candidate / name).write_bytes(b"stable")
                (candidate / filenames[0]).write_bytes(b"changed")
                audit = compare_existing_stls(
                    reference, candidate, filenames
                )
                self.assertEqual(
                    audit["MODIFIED_EXISTING_STL_COUNT"], 1
                )
                self.assertIn(
                    "EXISTING_STL_BYTE_CHANGE", audit["blockers"]
                )


if __name__ == "__main__":
    unittest.main()
