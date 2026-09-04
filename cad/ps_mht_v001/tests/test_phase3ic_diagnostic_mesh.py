"""Phase 3I-C diagnostic STL comparison and mesh tests (7)."""

import json
from pathlib import Path

from ps_mht_v001.common.validation import validate_stl_mesh
from ps_mht_v001.print_manifest_phase3ic import build_print_manifest_phase3ic


PACKAGE_ROOT = Path(__file__).parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"
DIAG_ROOT = EXPORT_ROOT / "stl" / "diagnostic_phase3ic"


def _paths() -> list[Path]:
    return sorted(DIAG_ROOT.glob("phase3ic_diag_*.stl"))


def test_phase3ic_exactly_five_diagnostic_stls_exist() -> None:
    assert len(_paths()) == 5


def test_phase3ic_each_diagnostic_stl_is_one_component() -> None:
    assert all(validate_stl_mesh(path).connected_component_count == 1 for path in _paths())


def test_phase3ic_each_diagnostic_stl_is_closed_manifold() -> None:
    assert all(validate_stl_mesh(path).closed_manifold for path in _paths())


def test_phase3ic_diagnostic_meshes_have_zero_bad_edges() -> None:
    assert all(validate_stl_mesh(path).boundary_or_nonmanifold_edge_count == 0 for path in _paths())


def test_phase3ic_diagnostic_meshes_have_zero_degenerate_triangles() -> None:
    report = json.loads((EXPORT_ROOT / "preview" / "phase3ic_validation_report.json").read_text(encoding="utf-8"))
    assert all(item["degenerate_triangle_count"] == 0 for item in report["diagnostic_stl_mesh_validation"].values())


def test_phase3ic_diagnostics_are_do_not_print() -> None:
    items = build_print_manifest_phase3ic()["diagnostics"]
    assert all(item["status"] == "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT" for item in items)
    assert all(item["print"] is False for item in items)


def test_phase3ic_each_diagnostic_uses_one_new_project_object() -> None:
    items = build_print_manifest_phase3ic()["diagnostics"]
    assert all(item["object_count_per_new_project"] == 1 for item in items)

