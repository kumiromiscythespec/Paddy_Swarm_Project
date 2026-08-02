"""Deprecation and Phase 3R assembly exclusion gates."""

from __future__ import annotations

from ps_mht_v001.assembly.module_interface_phase3r import (
    interface_components_phase3r,
)
from ps_mht_v001.assembly.planting_port_phase3r import port_components_phase3r
from ps_mht_v001.common.fasteners import (
    M4_CARTRIDGE_STATUS,
    M4_RETAINER_STATUS,
)
from ps_mht_v001.coupons.angled_port_print_coupon import (
    STATUS as OLD_ANGLED_STATUS,
)
from ps_mht_v001.coupons.index_key_fit_coupon import (
    STATUS as OLD_INDEX_STATUS,
)
from ps_mht_v001.coupons.m3_port_cartridge_fit_coupon import (
    STATUS as OLD_M3_COUPON_STATUS,
)
from ps_mht_v001.coupons.m4_cartridge_fit_coupon import (
    STATUS as OLD_M4_COUPON_STATUS,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    CARTRIDGE_STATUS as M3_CARTRIDGE_STATUS,
    RETAINER_STATUS as M3_RETAINER_STATUS,
)
from ps_mht_v001.tower_module.module_interface import THIN_SIX_KEY_STATUS


def test_all_print_failed_small_parts_are_deprecated() -> None:
    statuses = (
        M4_CARTRIDGE_STATUS,
        M4_RETAINER_STATUS,
        M3_CARTRIDGE_STATUS,
        M3_RETAINER_STATUS,
        THIN_SIX_KEY_STATUS,
    )
    assert set(statuses) == {"DEPRECATED_AFTER_PRINT_FAILURE"}


def test_old_failed_coupons_are_do_not_reprint() -> None:
    statuses = (
        OLD_INDEX_STATUS,
        OLD_M4_COUPON_STATUS,
        OLD_M3_COUPON_STATUS,
        OLD_ANGLED_STATUS,
    )
    assert set(statuses) == {
        "DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE"
    }


def test_phase3r_module_interface_contains_no_cartridge_or_gate() -> None:
    names = {component.name.lower() for component in interface_components_phase3r()}
    assert not any("cartridge" in name or "gate" in name for name in names)


def test_phase3r_port_contains_no_cartridge_or_gate() -> None:
    names = {component.name.lower() for component in port_components_phase3r()}
    assert not any("cartridge" in name or "gate" in name for name in names)
