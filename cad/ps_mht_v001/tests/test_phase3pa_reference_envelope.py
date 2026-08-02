"""Conservative measured reference-envelope checks."""

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.reference.siawadeky_netpot_reference_envelope_phase3pa import (
    PRINT_STATUS,
    STATUS,
    build_siawadeky_netpot_reference_envelope_phase3pa,
    reference_envelope_metadata_phase3pa,
)


def test_phase3pa_reference_envelope_is_one_valid_solid() -> None:
    metrics = measure_shape(
        build_siawadeky_netpot_reference_envelope_phase3pa()
    )
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid


def test_phase3pa_reference_envelope_has_measured_bounds() -> None:
    metrics = measure_shape(
        build_siawadeky_netpot_reference_envelope_phase3pa()
    )
    assert (metrics.size_x, metrics.size_y, metrics.size_z) == (
        108.0,
        108.0,
        68.0,
    )


def test_phase3pa_reference_is_not_a_printable_pot_model() -> None:
    assert STATUS == "REFERENCE_ENVELOPE_NOT_A_PRINTABLE_NETPOT_MODEL"
    assert PRINT_STATUS == "REFERENCE_STEP_ONLY_NO_STL"


def test_phase3pa_internal_diameters_are_metadata_only() -> None:
    metadata = reference_envelope_metadata_phase3pa()
    assert metadata["internal_diameters_geometry"] == (
        "NOT_MODELED_REFERENCE_ONLY"
    )
