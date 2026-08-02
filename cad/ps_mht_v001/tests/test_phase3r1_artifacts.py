"""Phase 3R.1 envelope, plate, artifact, and non-regression gates."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.assembly.full_module_reference_phase3r1 import (
    build_full_module_reference_phase3r1,
)
from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    measure_shape,
    validate_printable_set,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.print_plate_layout_phase3r1 import (
    ORIENTATION_REFERENCE_SOLID_COUNT,
    STATUS,
    build_multi_plate_orientation_reference_phase3r1,
    phase3r1_individual_plates,
)
from ps_mht_v001.print_plate_layout_phase3r import (
    STATUS as PHASE3R_ORIENTATION_REFERENCE_STATUS,
    build_print_plate_layout_phase3r,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    TARGET_MAXIMUM_DIAMETER_MM,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3r1_module_reaches_238mm_diameter_target() -> None:
    maximum_diameter = 2.0 * maximum_radial_radius(
        build_full_module_reference_phase3r1()
    )
    assert maximum_diameter <= TARGET_MAXIMUM_DIAMETER_MM


def test_phase3r1_each_named_plate_fits_a1() -> None:
    expected_names = (
        "plate_01_large_index_ring_phase3r1",
        "plate_02_annular_nut_ring_phase3r1",
        "plate_03_self_supporting_shell_phase3r1",
        "plate_04_port_function_ring_phase3r1",
    )
    plates = phase3r1_individual_plates()
    assert tuple(name for name, _, _ in plates) == expected_names
    for name, model, solid_count in plates:
        metrics = validate_printable_set(model, name, solid_count)
        assert metrics.size_x <= 245.0
        assert metrics.size_y <= 245.0
        assert metrics.size_z <= 240.0
        assert (EXPORT_ROOT / "stl" / f"{name}.stl").is_file()


def test_phase3r1_orientation_reference_is_explicitly_not_sliceable() -> None:
    reference = build_multi_plate_orientation_reference_phase3r1()
    metrics = measure_shape(reference)
    assert STATUS == "DO_NOT_SLICE_AS_SINGLE_PLATE"
    assert metrics.solid_count == ORIENTATION_REFERENCE_SOLID_COUNT
    assert metrics.size_x > 245.0
    assert (
        EXPORT_ROOT
        / "step"
        / "multi_plate_orientation_reference_phase3r1.step"
    ).is_file()
    assert not (
        EXPORT_ROOT
        / "stl"
        / "multi_plate_orientation_reference_phase3r1.stl"
    ).exists()


def test_phase3r_1506mm_reference_remains_non_printable() -> None:
    metrics = measure_shape(build_print_plate_layout_phase3r())
    assert metrics.size_x > 1500.0
    assert (
        PHASE3R_ORIENTATION_REFERENCE_STATUS
        == "REFERENCE_MULTI_PLATE_LAYOUT_NOT_ONE_A1_PRINT_JOB"
    )


def test_phase1_through_phase3r_artifact_hashes_are_unchanged() -> None:
    audit = audit_baseline_hashes(EXPORT_ROOT)
    assert sum(
        len(item["expected"]) for item in audit.values()
        if item is not audit["phase3r"]
    ) == 90
    assert len(audit["phase3r"]["expected"]) == 40
    assert all(item["unchanged"] for item in audit.values())


def test_phase3r1_all_exported_steps_reload_valid() -> None:
    expected = {
        "ps_mht_v001_self_supporting_port_shell_coupon_phase3r1.step": 1,
        "ps_mht_v001_module_nut_ring_candidate_c025_phase3r1.step": 1,
        "ps_mht_v001_annular_nut_ring_calibration_coupon_phase3r1.step": 1,
        "multi_plate_orientation_reference_phase3r1.step":
            ORIENTATION_REFERENCE_SOLID_COUNT,
    }
    for name, count in expected.items():
        metrics = validate_step_round_trip(
            EXPORT_ROOT / "step" / name,
            count,
        )
        assert metrics.all_solids_valid


def test_phase3r1_all_exported_stls_are_closed_manifolds() -> None:
    paths = sorted((EXPORT_ROOT / "stl").glob("*phase3r1.stl"))
    assert len(paths) == 7
    for path in paths:
        assert validate_stl_mesh(path).closed_manifold


def test_phase3r1_shell_plate_stl_has_one_component() -> None:
    metrics = validate_stl_mesh(
        EXPORT_ROOT
        / "stl"
        / "plate_03_self_supporting_shell_phase3r1.stl"
    )
    assert metrics.connected_component_count == 1
