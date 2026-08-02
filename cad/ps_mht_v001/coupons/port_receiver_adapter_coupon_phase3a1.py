"""Corrected through-bore receiver/common-adapter clearance coupon."""

from __future__ import annotations

from ps_mht_v001.coupons.port_receiver_adapter_coupon import (
    ADAPTER_CLEARANCES,
    COUPON_SOLID_COUNT,
    build_port_receiver_adapter_coupon,
)


STATUS = "PHASE3A1_CORRECTED_CONTINUOUS_CENTER_PASSAGE"


def build_port_receiver_adapter_coupon_phase3a1():
    return build_port_receiver_adapter_coupon()

