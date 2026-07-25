"""Render a compact visual-QA sheet from the generated STL files."""

from __future__ import annotations

import vtk

from parameters import EXPECTED_EXPORT_STEMS, EXPORT_DIR, REPORT_DIR


def render_preview() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORT_DIR / "artifact_preview.png"
    stems = EXPECTED_EXPORT_STEMS
    columns = 4
    rows = 2

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1800, 900)
    window.SetMultiSamples(8)

    for index, stem in enumerate(stems):
        row = index // columns
        column = index % columns
        x0 = column / columns
        x1 = (column + 1) / columns
        y1 = 1.0 - row / rows
        y0 = 1.0 - (row + 1) / rows

        renderer = vtk.vtkRenderer()
        renderer.SetViewport(x0, y0, x1, y1)
        renderer.SetBackground(0.96, 0.97, 0.98)
        window.AddRenderer(renderer)

        reader = vtk.vtkSTLReader()
        reader.SetFileName(str(EXPORT_DIR / f"{stem}.stl"))
        reader.Update()
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(reader.GetOutputPort())
        normals.SetFeatureAngle(45.0)
        normals.ConsistencyOn()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.20, 0.52, 0.78)
        actor.GetProperty().SetSpecular(0.20)
        actor.GetProperty().SetSpecularPower(18.0)
        renderer.AddActor(actor)

        label = vtk.vtkTextActor()
        label.SetInput(stem)
        label.GetTextProperty().SetFontFamilyToArial()
        label.GetTextProperty().SetFontSize(21)
        label.GetTextProperty().SetColor(0.08, 0.10, 0.14)
        label.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        label.GetPositionCoordinate().SetValue(0.04, 0.04)
        label.UseBoundsOff()
        renderer.AddViewProp(label)

        renderer.ResetCamera()
        camera = renderer.GetActiveCamera()
        camera.Azimuth(-25.0)
        camera.Elevation(28.0)
        camera.SetParallelProjection(1)
        camera.Zoom(0.86)
        renderer.ResetCameraClippingRange()

    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff()
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    print(output_path)


if __name__ == "__main__":
    render_preview()
