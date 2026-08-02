"""Read-only Phase 1 through Phase 3P-A/3CB-0 SHA-256 audit."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase3pa_nonregression import (
    audit_phase1_through_phase3sa2,
)
from ps_mht_v001.common.phase_baseline import file_sha256


PHASE3PA_SHA256 = {
    "preview/phase3pa_existing_port_function_ring_audit.json": "0aa6c01eac9da107e01b177103aff71623c791a4dfb5445d2bcdddb58f406563",
    "preview/phase3pa_m4_fastener_envelope_audit.json": "e7197ee5b7bc21d8049a6722b32a46309cea839aa47c5e93a13cc7374f91ce9f",
    "preview/phase3pa_maximum_diameter_audit.json": "47af53767c7a58a2c4f098a98f1597243cded8a769110f7d56ad1b62aeea7cad",
    "preview/phase3pa_ring_outer_diameter_comparison.json": "70125c8e5c87980711dfd707189fa47b778da7a93a752f15a1f5b5e7234861ff",
    "preview/phase3pa_validation_report.json": "0b7575c18ad5887100ff4272809e7749f5430e2065f97c6f56df2aaf84ccaf12",
    "preview/print_manifest_phase3pa.json": "50439033a8c7a20fc7491db737a39530d6e4034fcbd4d7edfcbe3d96b888af13",
    "preview/ps_mht_v001_netpot_fit_isometric_phase3pa.svg": "8028a1da9ae58d24926286a2f8466469a8a17a5c60b4fd92454aaf458d7b7105",
    "preview/ps_mht_v001_netpot_fit_section_phase3pa.svg": "c4afc0ac2104262fbe13b4c25e857989290090008ed8832a9e607d07c674433f",
    "ps_mht_v001_phase3pa_delivery.zip": "eae7182dd8611d4562e9e9aa53fb1a1202759545399a089f9eb75b2c36f949a7",
    "step/ps_mht_v001_netpot_seat_fit_coupon_c800_phase3pa.step": "757976b4eb843d67fe603817dfd71ad48ff4b51fed4692040cb76590bc1cdf27",
    "step/ps_mht_v001_netpot_seat_fit_coupon_c805_phase3pa.step": "85a4b9119c8e6f5c0cbc2e74da021fdf95f05feb5433811686cc9ecd726d0b6f",
    "step/ps_mht_v001_netpot_seat_fit_coupon_c810_phase3pa.step": "b399177bde6166c46ab7d21b40e408d7c199de116b0f4b04ec5de97046931300",
    "step/ps_mht_v001_siawadeky_netpot_reference_envelope_phase3pa.step": "11f5fb1ce6d9b2f999de6126415bdf2b155187661a7439ef30c4651805200023",
    "stl/plate_01_netpot_fit_c805_phase3pa.stl": "5643ed03be19ee5aa9236836a06182df546219b93bf1229ff3320c7ea130b728",
    "stl/plate_02_netpot_fit_c800_phase3pa.stl": "0577b94d5b3c430ea4d5a7d4e684776db700feeb667ca2d5793cd42c655e2c57",
    "stl/plate_03_netpot_fit_c810_phase3pa.stl": "52ec18bc1c0bcacad1664badbb2c14ef8b434e3eb885a85d255faa4b04955241",
    "stl/ps_mht_v001_netpot_seat_fit_coupon_c800_phase3pa.stl": "0577b94d5b3c430ea4d5a7d4e684776db700feeb667ca2d5793cd42c655e2c57",
    "stl/ps_mht_v001_netpot_seat_fit_coupon_c805_phase3pa.stl": "5643ed03be19ee5aa9236836a06182df546219b93bf1229ff3320c7ea130b728",
    "stl/ps_mht_v001_netpot_seat_fit_coupon_c810_phase3pa.stl": "52ec18bc1c0bcacad1664badbb2c14ef8b434e3eb885a85d255faa4b04955241",
}


PHASE3CB0_SOURCE_SHA256 = {
    "docs/PS_MHT_CAPILLARY_BUFFER_ARCHITECTURE.md": "3366f44d56dff15f6d2ad4bbd8fce2616526abe2bf4843105eef4db9ee7c0d7a",
    "docs/PS_MHT_EXISTING_SPEC_COMPATIBILITY.md": "ff09ab89da54e537e068e0af09515efbf80acb96d11b58fc2a3f1f4cdf3d0ae2",
    "docs/PS_MHT_WATER_BALANCE_4_TOWERS.md": "0c63769016f0c6def23d45b9f65ae06e60f937850cbbd71c0127d261ab7630a1",
    "docs/PS_MHT_HORIZONTAL_STACK_OPTIONS.md": "c7bb7183c5a6ffe0233be087752a3be8a426726d22ae44bb358f21d34c91c67a",
    "docs/PS_MHT_WICK_AND_MEDIA_TEST_PLAN.md": "0033dc060c80d223b21f417d65a86094b775c9ce22098020a68a2c4c7c134370",
    "docs/PS_MHT_4_TOWER_EXPERIMENT_PLAN.md": "31cf7302e6d10eed90a18f10635e5ca655122fc69d77cc0992581ea207f87ba2",
    "docs/PS_MHT_POWER_BUDGET.md": "a9c668c83f7cab4e6bdd86c5735c1a9c8cfebd6c6429dad5e36a6ab654730e4b",
    "specs/ps_mht_capillary_buffer_v001.yaml": "497e0f9a123f4abb4079153d7abddd89e9a64d4f5d82fdf6a9c76b3384b6010d",
}


def audit_existing_before_phase3ha(
    export_root: Path,
    package_root: Path,
) -> dict[str, dict[str, object]]:
    report = audit_phase1_through_phase3sa2(export_root)
    phase3pa_actual = {
        relative: file_sha256(export_root / relative)
        for relative in PHASE3PA_SHA256
    }
    report["phase3pa"] = {
        "expected": PHASE3PA_SHA256,
        "actual": phase3pa_actual,
        "unchanged": phase3pa_actual == PHASE3PA_SHA256,
    }
    phase3cb0_actual = {
        relative: file_sha256(package_root / relative)
        for relative in PHASE3CB0_SOURCE_SHA256
    }
    report["phase3cb0_sources"] = {
        "expected": PHASE3CB0_SOURCE_SHA256,
        "actual": phase3cb0_actual,
        "unchanged": phase3cb0_actual == PHASE3CB0_SOURCE_SHA256,
    }
    return report
