"""Theoretical body clearance and measured-flange support checks."""

import pytest

from ps_mht_v001.coupons.netpot_seat_fit_coupon_phase3pa import (
    fit_theory_phase3pa,
)


@pytest.mark.parametrize(
    ("diameter", "diametral", "radial"),
    [(80.0, 1.4, 0.7), (80.5, 1.9, 0.95), (81.0, 2.4, 1.2)],
)
def test_phase3pa_theoretical_clearances(
    diameter: float,
    diametral: float,
    radial: float,
) -> None:
    theory = fit_theory_phase3pa(diameter)
    assert theory["diametral_clearance_mm"] == pytest.approx(diametral)
    assert theory["radial_clearance_mm"] == pytest.approx(radial)


@pytest.mark.parametrize(
    ("diameter", "support"),
    [(80.0, 14.0), (80.5, 13.75), (81.0, 13.5)],
)
def test_phase3pa_flange_support_width(
    diameter: float,
    support: float,
) -> None:
    theory = fit_theory_phase3pa(diameter)
    assert theory["flange_support_width_mm"] == support
    assert theory["ring_outside_flange_width_mm"] == 4.0
