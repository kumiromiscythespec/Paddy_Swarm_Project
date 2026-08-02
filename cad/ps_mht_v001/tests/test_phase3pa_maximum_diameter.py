"""Reference-only 116/120/124 mm function-ring envelope comparison."""

import pytest

from ps_mht_v001.audit.port_maximum_diameter_audit_phase3pa import (
    maximum_diameter_audit_phase3pa,
    ring_candidate_comparison_phase3pa,
)


def test_phase3pa_baseline_maximum_diameter_is_preserved() -> None:
    audit = ring_candidate_comparison_phase3pa()
    assert audit["baseline_phase3sa_maximum_diameter_mm"] == pytest.approx(
        237.48183810800376
    )


def test_phase3pa_116_120_124_candidates_are_compared() -> None:
    audit = ring_candidate_comparison_phase3pa()
    assert set(audit["candidates"]) == {"od_116", "od_120", "od_124"}


def test_phase3pa_candidate_maximum_diameters_are_measured() -> None:
    candidates = ring_candidate_comparison_phase3pa()["candidates"]
    assert candidates["od_116"]["reference_ring_only_maximum_module_diameter_mm"] == pytest.approx(237.88991835096283)
    assert candidates["od_120"]["reference_ring_only_maximum_module_diameter_mm"] == pytest.approx(239.86738656305934)
    assert candidates["od_124"]["reference_ring_only_maximum_module_diameter_mm"] == pytest.approx(241.878092686304)
    assert candidates["od_116"]["reference_maximum_module_diameter_mm"] == pytest.approx(241.21513055239188)


def test_phase3pa_124_is_rejected_for_240mm_limit() -> None:
    audit = maximum_diameter_audit_phase3pa()
    assert audit["od_124_rejected"] is True
    assert audit["ring_only_rejected_candidates"] == ["od_124"]
    assert audit["rejected_candidates"] == ["od_116", "od_120", "od_124"]
    assert audit["installed_netpot_exceeds_limit"] is True


def test_phase3pa_116_and_120_do_not_claim_fastener_solution() -> None:
    candidates = ring_candidate_comparison_phase3pa()["candidates"]
    assert candidates["od_116"]["status"] == (
        "REDESIGN_REQUIRED_INSTALLED_POT_MAXIMUM_DIAMETER"
    )
    assert candidates["od_120"]["status"] == (
        "REDESIGN_REQUIRED_INSTALLED_POT_MAXIMUM_DIAMETER"
    )
    assert not candidates["od_116"]["outside_flange_m4_possible_with_3mm_walls"]


def test_phase3pa_local_ear_and_inboard_options_are_reference_only() -> None:
    audit = ring_candidate_comparison_phase3pa()
    assert audit["local_ear_reference"]["status"] == (
        "REFERENCE_ONLY_NOT_GENERATED"
    )
    assert audit["inboard_fastener_reference"]["status"] == (
        "POT_REMOVED_ONLY_REFERENCE"
    )
