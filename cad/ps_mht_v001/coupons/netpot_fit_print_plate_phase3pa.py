"""One-coupon A1 plates in the required material-saving order."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.coupons.netpot_seat_fit_coupon_phase3pa import (
    build_netpot_seat_fit_coupon_phase3pa,
)


STATUS = "PHASE3PA_ONE_CANDIDATE_PER_A1_PLATE"
OPTIONAL_THREE_UP_MINIMUM_WIDTH_MM = 247.0
OPTIONAL_THREE_UP_STATUS = "NOT_GENERATED_EXCEEDS_A1_WITH_15MM_SPACING"


def build_plate_01_netpot_fit_c805_phase3pa() -> cq.Workplane:
    return build_netpot_seat_fit_coupon_phase3pa(80.5)


def build_plate_02_netpot_fit_c800_phase3pa() -> cq.Workplane:
    return build_netpot_seat_fit_coupon_phase3pa(80.0)


def build_plate_03_netpot_fit_c810_phase3pa() -> cq.Workplane:
    return build_netpot_seat_fit_coupon_phase3pa(81.0)


def phase3pa_individual_plates(
) -> tuple[tuple[str, cq.Workplane], ...]:
    return (
        (
            "plate_01_netpot_fit_c805_phase3pa",
            build_plate_01_netpot_fit_c805_phase3pa(),
        ),
        (
            "plate_02_netpot_fit_c800_phase3pa",
            build_plate_02_netpot_fit_c800_phase3pa(),
        ),
        (
            "plate_03_netpot_fit_c810_phase3pa",
            build_plate_03_netpot_fit_c810_phase3pa(),
        ),
    )
