from pathlib import Path
import pytest
import vtk

from ps_mht_v001_phase3ig_lower_return_buffer.src.export_models import HOLD_MODELS, PLATE_MODELS
from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import PACKAGE_ROOT


@pytest.mark.parametrize("name", list(PLATE_MODELS) + list(HOLD_MODELS))
def test_required_stl_is_closed_manifold(name):
    root = "exports/diagnostics" if name in PLATE_MODELS else "exports/stl"
    path = PACKAGE_ROOT / root / name
    assert path.is_file() and path.stat().st_size > 0
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    mesh = reader.GetOutput()
    assert mesh.GetNumberOfPoints() > 0 and mesh.GetNumberOfCells() > 0
    edge = vtk.vtkFeatureEdges(); edge.SetInputData(mesh)
    edge.BoundaryEdgesOn(); edge.NonManifoldEdgesOn(); edge.FeatureEdgesOff(); edge.ManifoldEdgesOff(); edge.Update()
    assert edge.GetOutput().GetNumberOfCells() == 0


@pytest.mark.parametrize("name", PLATE_MODELS)
def test_diagnostic_stl_is_inside_a1(name):
    path = PACKAGE_ROOT / "exports/diagnostics" / name
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    bounds = reader.GetOutput().GetBounds()
    assert bounds[1] - bounds[0] <= 245.0
    assert bounds[3] - bounds[2] <= 245.0
    assert bounds[5] - bounds[4] <= 240.0

