"""Automated geometric and export validation for the calibration-only artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, pi
from pathlib import Path

import cadquery as cq
import vtk

from bore_gauges import build_all_bore_gauges
from htd5m_profile import (
    coupon_span_angle_deg,
    describe_profile,
    groove_profile_points,
    outside_diameter_mm,
    pitch_angle_deg,
    pitch_diameter_mm,
    station_angles_deg,
)
from parameters import (
    BORE_GAUGES,
    CALIBRATION_STATUS,
    COUPON_TOOTH_COUNT,
    COUPONS,
    EXPECTED_PITCH_DIAMETERS_MM,
    EXPECTED_EXPORT_STEMS,
    EXPORT_DIR,
    HTD_PITCH_MM,
    OPTIONAL_COMBINED_STEP_STEMS,
    REFERENCE_OUTSIDE_DIAMETERS_MM,
    REPORT_DIR,
    TOOTH_FACE_WIDTH_MM,
)
from tooth_fit_coupons import build_all_tooth_fit_coupons


ABS_TOL = 1.0e-6


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def _check(checks: list[Check], condition: bool, name: str, detail: str) -> None:
    checks.append(Check(name, bool(condition), detail))


def _shape_is_one_valid_solid(model: cq.Workplane) -> tuple[bool, str]:
    solids = model.solids().vals()
    valid = len(solids) == 1 and solids[0].isValid()
    return valid, f"solids={len(solids)}, valid={solids[0].isValid() if solids else False}"


def _validate_step_roundtrip(path: Path) -> tuple[bool, str]:
    imported = cq.importers.importStep(str(path))
    solids = imported.solids().vals()
    ok = len(solids) == 1 and solids[0].isValid()
    return ok, f"roundtrip solids={len(solids)}, valid={solids[0].isValid() if solids else False}"


def _validate_stl(path: Path) -> tuple[bool, str]:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    output = reader.GetOutput()
    points = output.GetNumberOfPoints()
    cells = output.GetNumberOfCells()
    return points > 0 and cells > 0, f"points={points}, triangles={cells}"


def _validate_gauges(
    checks: list[Check], models: dict[str, cq.Workplane]
) -> None:
    for spec in BORE_GAUGES:
        model = models[spec.key]
        shape = model.val()
        box = shape.BoundingBox()
        ok, detail = _shape_is_one_valid_solid(model)
        _check(checks, ok, f"{spec.key}: one valid solid", detail)
        _check(
            checks,
            isclose(box.zlen, spec.thickness_mm, abs_tol=ABS_TOL),
            f"{spec.key}: thickness",
            f"actual={box.zlen:.6f} mm, expected={spec.thickness_mm:.6f} mm",
        )
        _check(
            checks,
            spec.center_spacing_mm
            >= (14.0 if spec.nominal_mm == 6.0 else 18.0),
            f"{spec.key}: center spacing",
            f"{spec.center_spacing_mm:.3f} mm",
        )
        end_wall = 0.5 * (spec.length_mm - spec.center_span_mm) - 0.5 * max(
            spec.candidates_mm
        )
        side_wall = 0.5 * spec.width_mm - 0.5 * max(spec.candidates_mm)
        _check(
            checks,
            end_wall >= spec.minimum_edge_wall_mm - ABS_TOL
            and side_wall >= spec.minimum_edge_wall_mm - ABS_TOL,
            f"{spec.key}: minimum edge wall",
            f"end={end_wall:.3f} mm, side={side_wall:.3f} mm, "
            f"minimum={spec.minimum_edge_wall_mm:.3f} mm",
        )
        _check(
            checks,
            len(spec.hole_centers_x_mm) == len(spec.candidates_mm),
            f"{spec.key}: bore count",
            f"{len(spec.candidates_mm)} true-circle candidates",
        )
        _check(
            checks,
            all(
                isclose(
                    spec.hole_centers_x_mm[index + 1]
                    - spec.hole_centers_x_mm[index],
                    spec.center_spacing_mm,
                    abs_tol=ABS_TOL,
                )
                for index in range(len(spec.hole_centers_x_mm) - 1)
            ),
            f"{spec.key}: center locations",
            ", ".join(f"{value:.3f}" for value in spec.hole_centers_x_mm),
        )
        _check(
            checks,
            tuple(round(value, 2) for value in spec.candidates_mm)
            == (
                (6.00, 6.10, 6.20, 6.30, 6.40)
                if spec.nominal_mm == 6.0
                else (10.00, 10.10, 10.20, 10.30, 10.40, 10.50)
            ),
            f"{spec.key}: candidate diameters",
            ", ".join(f"{value:.2f} mm" for value in spec.candidates_mm),
        )
        cylindrical_faces = model.faces("%Cylinder").vals()
        modeled_bores: list[tuple[float, float, float]] = []
        for face in cylindrical_faces:
            cylinder = face._geomAdaptor().Cylinder()
            axis_location = cylinder.Axis().Location()
            modeled_bores.append(
                (2.0 * cylinder.Radius(), axis_location.X(), axis_location.Y())
            )
        actual_bores_match = len(modeled_bores) == len(spec.candidates_mm) and all(
            any(
                isclose(actual_diameter, expected_diameter, abs_tol=ABS_TOL)
                and isclose(actual_x, expected_x, abs_tol=ABS_TOL)
                and isclose(actual_y, 0.0, abs_tol=ABS_TOL)
                for actual_diameter, actual_x, actual_y in modeled_bores
            )
            for expected_diameter, expected_x in zip(
                spec.candidates_mm, spec.hole_centers_x_mm
            )
        )
        _check(
            checks,
            actual_bores_match,
            f"{spec.key}: modeled cylindrical bores",
            ", ".join(
                f"D{diameter:.2f}@({x:.2f},{y:.2f})"
                for diameter, x, y in sorted(modeled_bores)
            ),
        )
        _check(
            checks,
            model.faces("%Cone").size() == 2 * len(spec.candidates_mm),
            f"{spec.key}: both bore entries chamfered",
            f"conical faces={model.faces('%Cone').size()}",
        )
        _check(
            checks,
            0.0 < box.xlen <= 240.0 and 0.0 < box.ylen <= 240.0,
            f"{spec.key}: sensible A1 XY bounding box",
            f"{box.xlen:.3f} x {box.ylen:.3f} mm",
        )


def _validate_coupons(
    checks: list[Check], models: dict[str, cq.Workplane]
) -> None:
    profile_descriptions = {count: describe_profile(count) for count in (20, 60)}
    for count, description in profile_descriptions.items():
        expected_pd = count * HTD_PITCH_MM / pi
        _check(
            checks,
            isclose(description["pitch_diameter_mm"], expected_pd, abs_tol=ABS_TOL),
            f"{count}T: pitch diameter formula",
            f"{description['pitch_diameter_mm']:.9f} mm",
        )
        _check(
            checks,
            abs(
                float(description["pitch_diameter_mm"])
                - EXPECTED_PITCH_DIAMETERS_MM[count]
            )
            <= 0.01,
            f"{count}T: requested pitch-diameter tolerance",
            f"calculated={description['pitch_diameter_mm']:.9f} mm, "
            f"reference={EXPECTED_PITCH_DIAMETERS_MM[count]:.6f} mm, "
            f"difference={float(description['pitch_diameter_mm']) - EXPECTED_PITCH_DIAMETERS_MM[count]:+.9f} mm",
        )
        _check(
            checks,
            isclose(description["arc_pitch_check_mm"], HTD_PITCH_MM, abs_tol=ABS_TOL),
            f"{count}T: pitch preserved",
            f"pitch-circle arc={description['arc_pitch_check_mm']:.9f} mm",
        )
        angles = station_angles_deg(count, COUPON_TOOTH_COUNT)
        _check(
            checks,
            len(angles) == 6
            and all(
                isclose(
                    angles[index + 1] - angles[index],
                    pitch_angle_deg(count),
                    abs_tol=ABS_TOL,
                )
                for index in range(5)
            ),
            f"{count}T: six pitch stations",
            ", ".join(f"{angle:.3f} deg" for angle in angles),
        )
        _check(
            checks,
            isclose(
                coupon_span_angle_deg(count, COUPON_TOOTH_COUNT),
                6.0 * 360.0 / count,
                abs_tol=ABS_TOL,
            ),
            f"{count}T: curved coupon span",
            f"{coupon_span_angle_deg(count, COUPON_TOOTH_COUNT):.3f} deg",
        )

    _check(
        checks,
        not isclose(
            outside_diameter_mm(20), outside_diameter_mm(60), abs_tol=ABS_TOL
        )
        and not isclose(
            pitch_angle_deg(20), pitch_angle_deg(60), abs_tol=ABS_TOL
        ),
        "20T/60T: curvature differs",
        f"OD={outside_diameter_mm(20):.6f}/{outside_diameter_mm(60):.6f} mm, "
        f"pitch angle={pitch_angle_deg(20):.3f}/{pitch_angle_deg(60):.3f} deg",
    )

    for spec in COUPONS:
        model = models[spec.key]
        box = model.val().BoundingBox()
        ok, detail = _shape_is_one_valid_solid(model)
        _check(checks, ok, f"{spec.key}: one valid solid", detail)
        _check(
            checks,
            isclose(box.zlen, TOOTH_FACE_WIDTH_MM, abs_tol=ABS_TOL),
            f"{spec.key}: face width",
            f"actual={box.zlen:.6f} mm, expected={TOOTH_FACE_WIDTH_MM:.6f} mm",
        )
        geometry = groove_profile_points(spec.pulley_teeth, spec.clearance_mm)
        cylindrical_radii = [
            face._geomAdaptor().Cylinder().Radius()
            for face in model.faces("%Cylinder").vals()
        ]
        main_arc_face_count = sum(
            isclose(
                radius,
                float(geometry["main_radius_mm"]),
                abs_tol=ABS_TOL,
            )
            for radius in cylindrical_radii
        )
        tip_arc_face_count = sum(
            isclose(
                radius,
                float(geometry["tip_radius_mm"]),
                abs_tol=ABS_TOL,
            )
            for radius in cylindrical_radii
        )
        _check(
            checks,
            geometry["main_radius_mm"] > 0.0
            and geometry["tip_radius_mm"] > 0.0
            and geometry["bottom_depth_mm"] > 0.0,
            f"{spec.key}: curved paired-arc groove",
            f"R1'={geometry['main_radius_mm']:.3f}, "
            f"R2'={geometry['tip_radius_mm']:.3f}, "
            f"depth={geometry['bottom_depth_mm']:.3f} mm",
        )
        _check(
            checks,
            main_arc_face_count == 2 * COUPON_TOOTH_COUNT
            and tip_arc_face_count == 2 * COUPON_TOOTH_COUNT,
            f"{spec.key}: six actual paired-arc groove stations",
            f"main-arc faces={main_arc_face_count}, "
            f"transition-arc faces={tip_arc_face_count}",
        )
        _check(
            checks,
            0.0 < box.xlen <= 240.0
            and 0.0 < box.ylen <= 240.0
            and 0.0 < box.zlen <= 220.0,
            f"{spec.key}: sensible A1 bounding box",
            f"{box.xlen:.3f} x {box.ylen:.3f} x {box.zlen:.3f} mm",
        )

    for count in (20, 60):
        variants = [
            spec for spec in COUPONS if spec.pulley_teeth == count
        ]
        variant_volumes = {
            spec.fit_key: models[spec.key].val().Volume() for spec in variants
        }
        _check(
            checks,
            variant_volumes["tight"]
            > variant_volumes["standard"]
            > variant_volumes["loose"],
            f"{count}T: clearance changes contact geometry",
            ", ".join(
                f"{key}={value:.6f} mm^3"
                for key, value in variant_volumes.items()
            ),
        )
        station_sets = {
            station_angles_deg(spec.pulley_teeth, COUPON_TOOTH_COUNT)
            for spec in variants
        }
        _check(
            checks,
            len(station_sets) == 1,
            f"{count}T: clearance does not change pitch stations",
            f"clearances={', '.join(f'{spec.clearance_mm:.2f}' for spec in variants)} mm",
        )


def _validate_exports(checks: list[Check]) -> None:
    for stem in EXPECTED_EXPORT_STEMS:
        for suffix in (".step", ".stl"):
            path = EXPORT_DIR / f"{stem}{suffix}"
            exists_and_nonempty = path.is_file() and path.stat().st_size > 0
            _check(
                checks,
                exists_and_nonempty,
                f"{path.name}: present and nonempty",
                f"bytes={path.stat().st_size if path.is_file() else 0}",
            )
            if not exists_and_nonempty:
                continue
            if suffix == ".step":
                ok, detail = _validate_step_roundtrip(path)
            else:
                ok, detail = _validate_stl(path)
            _check(checks, ok, f"{path.name}: readable geometry", detail)

    for stem in OPTIONAL_COMBINED_STEP_STEMS:
        path = EXPORT_DIR / f"{stem}.step"
        imported = (
            cq.importers.importStep(str(path))
            if path.is_file() and path.stat().st_size > 0
            else None
        )
        imported_solids = imported.solids().size() if imported is not None else 0
        expected_solids = {
            "htd5m_bore_gauges_plate_v0_1": 2,
            "htd5m_tooth_coupons_plate_v0_1": 6,
            "htd5m_calibration_all_plate_v0_1": 8,
        }[stem]
        box = imported.val().BoundingBox() if imported is not None else None
        _check(
            checks,
            path.is_file()
            and path.stat().st_size > 0
            and imported_solids == expected_solids
            and box is not None
            and box.xlen <= 240.0
            and box.ylen <= 240.0
            and box.zlen <= 220.0,
            f"{path.name}: optional disconnected plate",
            f"bytes={path.stat().st_size if path.is_file() else 0}, "
            f"disconnected solids={imported_solids}, "
            f"bbox={box.xlen:.3f} x {box.ylen:.3f} x {box.zlen:.3f} mm"
            if box is not None
            else f"bytes=0, disconnected solids={imported_solids}, bbox=none",
        )

    forbidden = [
        path.name
        for path in EXPORT_DIR.glob("*")
        if "pulley" in path.name.lower()
        and path.suffix.lower() in {".step", ".stl"}
    ]
    _check(
        checks,
        not forbidden,
        "No complete pulley export",
        "none" if not forbidden else ", ".join(forbidden),
    )


def _write_report(checks: list[Check]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "validation_report.md"
    passed = sum(check.passed for check in checks)
    lines = [
        "# Validation report",
        "",
        f"- Automated checks: **{passed}/{len(checks)} passed**",
        f"- Physical fit status: **{CALIBRATION_STATUS}**",
        "- Scope: bore gauges and six-tooth curved coupons only; no full pulley.",
        "",
        "## Pitch and outside-diameter references",
        "",
        "| Curve | Requested pitch ref. | Calculated/adopted pitch dia. | Pitch diff. | Requested OD ref. | Adopted OD | OD diff. |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| 20T | {EXPECTED_PITCH_DIAMETERS_MM[20]:.6f} | "
            f"{pitch_diameter_mm(20):.9f} | "
            f"{pitch_diameter_mm(20) - EXPECTED_PITCH_DIAMETERS_MM[20]:+.9f} | "
            f"{REFERENCE_OUTSIDE_DIAMETERS_MM[20]:.2f} | "
            f"{outside_diameter_mm(20):.9f} | "
            f"{outside_diameter_mm(20) - REFERENCE_OUTSIDE_DIAMETERS_MM[20]:+.9f} |"
        ),
        (
            f"| 60T | {EXPECTED_PITCH_DIAMETERS_MM[60]:.6f} | "
            f"{pitch_diameter_mm(60):.9f} | "
            f"{pitch_diameter_mm(60) - EXPECTED_PITCH_DIAMETERS_MM[60]:+.9f} | "
            f"{REFERENCE_OUTSIDE_DIAMETERS_MM[60]:.2f} | "
            f"{outside_diameter_mm(60):.9f} | "
            f"{outside_diameter_mm(60) - REFERENCE_OUTSIDE_DIAMETERS_MM[60]:+.9f} |"
        ),
        "",
        "## Checks",
        "",
        "| Result | Check | Detail |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {'PASS' if check.passed else 'FAIL'} | {check.name} | {check.detail} |"
        for check in checks
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def validate_all() -> list[Check]:
    checks: list[Check] = []
    models: dict[str, cq.Workplane] = {}
    models.update(build_all_bore_gauges())
    models.update(build_all_tooth_fit_coupons())
    _validate_gauges(checks, models)
    _validate_coupons(checks, models)
    _validate_exports(checks)
    report_path = _write_report(checks)
    failed = [check for check in checks if not check.passed]
    print(f"Validation report: {report_path}")
    print(f"Checks: {len(checks) - len(failed)}/{len(checks)} passed")
    if failed:
        for check in failed:
            print(f"FAIL: {check.name}: {check.detail}")
        raise SystemExit(1)
    return checks


if __name__ == "__main__":
    validate_all()
