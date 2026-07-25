from __future__ import annotations

import unittest

from corrected_progressive_print_plan import (
    PRINT_STEPS,
    validate_corrected_dependencies,
)
from final_gate_contract import (
    CONNECTIVITY_CORE_OUTPUTS,
    validate_connectivity_fixture,
)
from part_number_registry import ALL_PARTS, CONNECTIVITY_PARTS, PARTS
from physical_connection_model import (
    build_physical_connection_graph,
    validate_physical_connection_graph,
)
from profile3_connection_geometry import CONNECTIVITY_BUILDERS
from tests._connectivity_artifact import (
    generated_connectivity_artifact,
)


class ConnectivityCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometries = [builder() for builder in CONNECTIVITY_BUILDERS]
        cls.connectivity_artifact = generated_connectivity_artifact()

    def test_additive_part_count_and_existing_registry_frozen(self):
        self.assertEqual(len(PARTS), 19)
        self.assertEqual(len(CONNECTIVITY_PARTS), 14)
        self.assertEqual(len(ALL_PARTS), 33)
        self.assertEqual(len({part.part_number for part in ALL_PARTS}), 33)
        audit = validate_connectivity_fixture(
            self.connectivity_artifact
        )
        self.assertEqual(audit["status"], "PASS", audit["blockers"])
        self.assertEqual(len(CONNECTIVITY_CORE_OUTPUTS), 71)

    def test_every_added_geometry_is_valid_marked_and_support_free(self):
        for part, geometry in zip(CONNECTIVITY_PARTS, self.geometries):
            self.assertTrue(geometry.shape.isValid(), part.key)
            self.assertTrue(geometry.marking.marking_verified, part.key)
            self.assertEqual(geometry.marking.part_number, part.part_number)
            self.assertEqual(
                geometry.marking.floating_text_solid_count, 0, part.key
            )
            self.assertFalse(
                geometry.design_metadata["structural_claim"], part.key
            )
            self.assertFalse(
                geometry.design_metadata["supplier_slot_geometry_used"],
                part.key,
            )
            self.assertFalse(
                geometry.design_metadata["t_nut_used"], part.key
            )
            self.assertFalse(
                geometry.design_metadata["direct_rail_holes"], part.key
            )
            self.assertFalse(
                geometry.design_metadata["support_required"], part.key
            )
            self.assertLessEqual(geometry.shape.BoundingBox().xlen, 256)
            self.assertLessEqual(geometry.shape.BoundingBox().ylen, 256)
            self.assertLessEqual(geometry.shape.BoundingBox().zlen, 256)

    def test_ai05_physical_marking_and_authority_zone(self):
        for part, geometry in zip(CONNECTIVITY_PARTS, self.geometries):
            if part.interface_id != "AI-05":
                continue
            legend = " ".join(geometry.marking.required_lines)
            self.assertIn("PROFILE-3 ONLY", legend)
            self.assertIn("REMOVE FOR REAL ALUMINUM", legend)
            self.assertEqual(
                geometry.design_metadata["authority_zone_y_mm"],
                [-125, -95],
            )
            self.assertEqual(
                geometry.design_metadata["assembly_anchor_y_mm"], -110
            )

    def test_physical_graph_is_connected_without_orphans(self):
        result = validate_physical_connection_graph(
            build_physical_connection_graph()
        )
        self.assertEqual(result["status"], "PASS_WITH_HOLD")
        self.assertEqual(result["connected_component_count"], 1)
        self.assertEqual(result["DISCONNECTED_PRINTED_PART_COUNT"], 0)
        self.assertEqual(result["orphan_parts"], [])

    def test_corrected_dependency_graph(self):
        result = validate_corrected_dependencies()
        self.assertEqual(len(PRINT_STEPS), 33)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["dependency_graph_acyclic"])
        self.assertEqual(result["IMPOSSIBLE_DEPENDENCY_COUNT"], 0)


if __name__ == "__main__":
    unittest.main()
