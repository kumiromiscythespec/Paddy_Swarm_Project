"""Phase 3H, Phase 3P-A, source, and linked-sump SHA-256 audit."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase3hb_nonregression import (
    audit_linked_sump_phase4tlsa,
    file_sha256,
)


PHASE3H_EXPORT_SHA256 = {
    "ps_mht_v001_phase3ha_delivery.zip": "0f6fd9098a901eca8c6a3f0e945ebe6034c40ad6660c8803c50edfd551f197d6",
    "preview/horizontal_joint_isometric_phase3ha.svg": "3a174c273e42aa05f8bf746852311b71fc9ad51b258dc1f33fccb5ddc0fe3cbc",
    "preview/horizontal_joint_section_phase3ha.svg": "abf3cd23434d744cd323633a74da9eb2d91f8af0e43f49303b091a13078ab5a5",
    "preview/phase3ha_validation_report.json": "432cd293039f57348a44f26e15c1408f5679b968c66922337ac42251e471141d",
    "preview/phase3hb_nonregression_audit.json": "53f2b7bfce309768ee53181617227e9b6a36a721c4e154f3adfc407c4ae1482c",
    "preview/phase3hb_validation_report.json": "71c74a9425b9162f4fd77e8fddac7e3f4b42590ed50610c607733e467c5045c7",
    "preview/print_manifest_phase3ha.json": "6fd98de5f62e6a8adda5bcac079e2436423d01bfa8cdb27129fa1994025715db",
    "preview/print_manifest_phase3hb.json": "02b93d7711998a0c97c435654e831a01aafebd07df72b5e4fb83f5a437fea4df",
    "step/full_ring_joint_pair_c050_reference_phase3ha.step": "2e61af0d9a6b6c4f628653be26735c808fcda580de15d998d8f4b9e2ebb4f7db",
    "step/horizontal_joint_arc_coupon_c030_phase3ha.step": "6485e03769b3befe418ec35bd6d9a88f066f416d846ac1f9de2cabca2c8db6f0",
    "step/horizontal_joint_arc_coupon_c050_phase3ha.step": "9c4926f9d3268dfce3927f598eef575b442a4a44d657cf6e560eaf276a72e53e",
    "step/horizontal_joint_arc_coupon_c070_phase3ha.step": "d8bb9c77f4279ed6648f5e74d8f6f602632b6c1a563ddc5e666fc435a74af59a",
    "step/horizontal_joint_compression_assembly_reference_phase3ha.step": "95362dd8b26274e3beff46bed045c0602db0a521636569ce6d2fa2255aa0f5ad",
    "step/horizontal_joint_compression_ring_phase3ha.step": "5a5fd51c9f30dfed1429a9dce97e63dab479247156e388eca8bec1d7fd0d85d3",
    "step/ps_mht_v001_compression_ring_reference_phase3hb.step": "3c54496007721e642a84623bc3536c051d590d3a3f0c7d5fe197d9878e831097",
    "step/ps_mht_v001_full_ring_lower_c050_phase3hb.step": "f03d2eb4e80ee9974f8fca49d2e1f0333f4a435f0b66f170922d83ae20ff7324",
    "step/ps_mht_v001_full_ring_pair_c050_reference_phase3hb.step": "b4d7f71fda2a798752efc2d89731e73cd73a29dd6927cc2377d824b340233814",
    "step/ps_mht_v001_full_ring_upper_c050_phase3hb.step": "f0c9ac261f98c58a4adfa61dc24a6016f3a69e41d692649b235dfa017213b7e9",
    "step/temporary_test_membrane_reference_phase3ha.step": "ad39df77f9a8972495547ff3442d804fd886b251f3fcf0e62237504e650dbfab",
    "stl/horizontal_joint_arc_coupon_c030_phase3ha.stl": "f3d15ee13fb51c1d28d7967f396267ff60d6487ab8b925f5da4492669e6e5b89",
    "stl/horizontal_joint_arc_coupon_c050_phase3ha.stl": "6787d6a52d742c2d17f48564675789a37c52bfffb85f348a4c602773ac321144",
    "stl/horizontal_joint_arc_coupon_c070_phase3ha.stl": "8ec7de5b0b2afe905cd5d295e3a3754bc9df3f94fd35ea1aebf6427e250f2b38",
    "stl/horizontal_joint_compression_ring_phase3ha.stl": "124a9c08c623c9a689c44151493d48e21ac311d8f8d0daf5986a89505e2fd2b7",
    "stl/plate_01_full_ring_lower_c050_phase3hb.stl": "c175b7aec2065f7d19db73e1e398d040094f04f2a950d34338c1e65acc62ad06",
    "stl/plate_02_full_ring_upper_c050_phase3hb.stl": "56ef478a3e76e6f162166acbf515434c9cabee6dac76c53e039f823365c3510f",
    "stl/plate_03_compression_ring_HOLD_phase3hb.stl": "124a9c08c623c9a689c44151493d48e21ac311d8f8d0daf5986a89505e2fd2b7",
}

PHASE3PA_EXPORT_SHA256 = {
    "ps_mht_v001_phase3pa_delivery.zip": "eae7182dd8611d4562e9e9aa53fb1a1202759545399a089f9eb75b2c36f949a7",
    "preview/phase3pa_existing_port_function_ring_audit.json": "0aa6c01eac9da107e01b177103aff71623c791a4dfb5445d2bcdddb58f406563",
    "preview/phase3pa_m4_fastener_envelope_audit.json": "e7197ee5b7bc21d8049a6722b32a46309cea839aa47c5e93a13cc7374f91ce9f",
    "preview/phase3pa_maximum_diameter_audit.json": "47af53767c7a58a2c4f098a98f1597243cded8a769110f7d56ad1b62aeea7cad",
    "preview/phase3pa_ring_outer_diameter_comparison.json": "70125c8e5c87980711dfd707189fa47b778da7a93a752f15a1f5b5e7234861ff",
    "preview/phase3pa_validation_report.json": "0b7575c18ad5887100ff4272809e7749f5430e2065f97c6f56df2aaf84ccaf12",
    "preview/print_manifest_phase3pa.json": "50439033a8c7a20fc7491db737a39530d6e4034fcbd4d7edfcbe3d96b888af13",
    "preview/ps_mht_v001_netpot_fit_isometric_phase3pa.svg": "8028a1da9ae58d24926286a2f8466469a8a17a5c60b4fd92454aaf458d7b7105",
    "preview/ps_mht_v001_netpot_fit_section_phase3pa.svg": "c4afc0ac2104262fbe13b4c25e857989290090008ed8832a9e607d07c674433f",
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

SOURCE_SHA256 = {
    "cad/ps_mht_v001/tower_module/horizontal_ring_joint_phase3ha.py": "b1632e070cd76c9db2fba02ec6a9fd2d8323f8fc9db2f1f488486056166e9cc0",
    "cad/ps_mht_v001/test_fixtures/horizontal_joint_compression_fixture_phase3ha.py": "2a803a530eb7f17234a74c33e14635d6c9095212f9af77d1f3922e2cf3aea2d7",
    "cad/ps_mht_v001/reference/temporary_test_membrane_phase3ha.py": "64f8d1c3639100a14db93a79be3a1c9384f0a51521f7d36f147f5cc399ee8ae8",
    "cad/ps_mht_v001/reference/full_ring_pair_phase3hb.py": "e11f9e5a82b7e3cf37b0ab1fb92103bcf5ea371270d47b7b01317c20bbb770b4",
    "cad/ps_mht_v001/build_phase3ha.py": "893d55ce2b8c98690daa8cf089748c498238ab531debde784b4c832e96b981a5",
    "cad/ps_mht_v001/build_phase3hb.py": "6fe1f8a7c46170d3787840d075947a9786e9bba3466d4d5beca5f3179644e09c",
    "cad/ps_mht_v001/parameters.py": "e223f80b924ed7a1ac71816494f2ebfe9be7ac5f97a28618b9878bc992ab6ef3",
    "cad/ps_mht_v001/reference/siawadeky_netpot_measurements_phase3pa.py": "7e733171f84b00755c1eb13579ed1440a147cab7ea6ec7ecf5075b57e9de3b73",
    "cad/ps_mht_v001/reference/siawadeky_netpot_reference_envelope_phase3pa.py": "b84e136023e6bac1d828bce45ecd4863114f07b6fdc2e05fb2d232aab066b0a6",
}


def _audit_paths(root: Path, expected: dict[str, str]) -> dict[str, object]:
    actual = {relative: file_sha256(root / relative) for relative in expected}
    return {
        "expected": expected,
        "actual": actual,
        "artifact_count": len(expected),
        "unchanged": actual == expected,
    }


def audit_phase3ia_nonregression(
    repository_root: Path,
    export_root: Path,
) -> dict[str, object]:
    phase3h = _audit_paths(export_root, PHASE3H_EXPORT_SHA256)
    phase3pa = _audit_paths(export_root, PHASE3PA_EXPORT_SHA256)
    sources = _audit_paths(repository_root, SOURCE_SHA256)
    linked = audit_linked_sump_phase4tlsa(repository_root)
    return {
        "phase3h_exports": phase3h,
        "phase3pa_netpot_calibration_exports": phase3pa,
        "authoritative_sources": sources,
        "linked_sump": linked,
        "all_unchanged": all(
            item["unchanged"] for item in (phase3h, phase3pa, sources, linked)
        ),
    }
