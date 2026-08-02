"""Phase 2 spigot/socket, indexing, load-face, and pair tests."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.assembly.module_pair_phase2 import (
    module_pair_interference_volume,
)
from ps_mht_v001.common.validation import (
    measure_shape,
    validate_single_printable,
)
from ps_mht_v001.parameters import (
    index_station_count,
    index_station_step,
    interface_load_contact_width,
    interface_radial_clearance,
    module_height,
    print_bed_x,
    print_bed_y,
    print_bed_z,
)
from ps_mht_v001.tower_module.module_interface import (
    build_planting_module_with_interface,
    compression_stop_radial_width,
    index_angles,
    socket_spigot_diametral_clearance,
)


def test_phase2_module_is_one_valid_solid() -> None:
    metrics = validate_single_printable(
        build_planting_module_with_interface(),
        "phase2_module",
    )
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid


def test_phase2_module_fits_a1() -> None:
    metrics = measure_shape(build_planting_module_with_interface())
    assert metrics.size_x <= print_bed_x
    assert metrics.size_y <= print_bed_y
    assert metrics.size_z <= print_bed_z
    assert isclose(metrics.size_z, module_height + 8.0, abs_tol=1.0e-6)


def test_sixfold_index_is_60_degree_increment() -> None:
    assert index_station_count == 6
    assert index_station_step == 60.0
    assert index_angles() == (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)


def test_spigot_socket_clearance() -> None:
    assert isclose(
        socket_spigot_diametral_clearance(),
        2.0 * interface_radial_clearance,
        abs_tol=1.0e-6,
    )


def test_load_face_is_independent_of_m4() -> None:
    assert interface_load_contact_width >= 6.0
    assert isclose(
        compression_stop_radial_width(),
        interface_load_contact_width,
        abs_tol=1.0e-6,
    )


def test_zero_degree_pair_has_no_solid_overlap() -> None:
    assert module_pair_interference_volume(0.0) <= 1.0e-6


def test_sixty_degree_pair_has_no_solid_overlap() -> None:
    assert module_pair_interference_volume(60.0) <= 1.0e-6


def test_pair_axes_remain_concentric_by_construction() -> None:
    lower = build_planting_module_with_interface().val().Center()
    upper = (
        build_planting_module_with_interface()
        .rotate((0, 0, 0), (0, 0, 1), 60.0)
        .translate((0, 0, module_height))
        .val()
        .Center()
    )
    assert isclose(lower.x, upper.x, abs_tol=1.0e-6)
    assert isclose(lower.y, upper.y, abs_tol=1.0e-6)

