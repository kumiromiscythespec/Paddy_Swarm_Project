"""Phase 1 five-stage assembly and aluminium-frame tests."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.assembly.full_tower_assembly import (
    build_frame_model,
    build_full_tower_model,
    build_tower_only_model,
    frame_components,
    tower_components,
)
from ps_mht_v001.common.validation import measure_shape, validate_multi_solid
from ps_mht_v001.parameters import (
    frame_base_depth,
    frame_base_width,
    frame_height,
    module_count,
    rear_post_front_clearance,
    rear_post_max_envelope_clearance,
    tower_nominal_height,
)


def test_tower_has_five_separable_module_solids() -> None:
    components = tower_components()
    modules = [item for item in components if item.name.startswith("module_")]
    assert len(modules) == module_count
    assert all(item.printable for item in modules)
    metrics = validate_multi_solid(
        build_tower_only_model(),
        "tower_only",
        len(components),
    )
    assert metrics.solid_count == 7
    assert metrics.all_solids_valid


def test_nominal_tower_reference_height() -> None:
    metrics = measure_shape(build_tower_only_model())
    assert isclose(metrics.size_z, tower_nominal_height, abs_tol=1.0e-6)


def test_frame_envelope_and_rear_post_clearance() -> None:
    components = frame_components()
    metrics = validate_multi_solid(
        build_frame_model(),
        "aluminum_frame",
        len(components),
    )
    assert isclose(metrics.size_x, frame_base_width, abs_tol=1.0e-6)
    assert isclose(metrics.size_y, frame_base_depth, abs_tol=1.0e-6)
    assert metrics.size_z >= frame_height
    assert isclose(rear_post_front_clearance(), 40.0, abs_tol=1.0e-6)
    assert isclose(
        rear_post_max_envelope_clearance(),
        20.0,
        abs_tol=1.0e-6,
    )


def test_full_assembly_solids_are_valid() -> None:
    expected = len(frame_components()) + len(tower_components())
    metrics = validate_multi_solid(
        build_full_tower_model(),
        "full_tower",
        expected,
    )
    assert expected == 14
    assert metrics.all_solids_valid


def test_tower_contacts_broad_aluminum_support_plane() -> None:
    drain_envelope = tower_components()[0].model.val().BoundingBox()
    support_plate = next(
        component
        for component in frame_components()
        if component.name == "tower_load_spreader_plate"
    ).model.val().BoundingBox()
    assert isclose(drain_envelope.zmin, 0.0, abs_tol=1.0e-6)
    assert isclose(support_plate.zmax, 0.0, abs_tol=1.0e-6)
    assert support_plate.xlen >= 200.0
    assert support_plate.ylen >= 200.0
