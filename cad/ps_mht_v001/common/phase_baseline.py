"""Immutable Phase 1/2 artifact hashes captured before Phase 3A work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PHASE1_SHA256 = {
    "preview/phase1_validation_report.json":
        "ba75de5bf21577fa1a694ae98b9c4f43a07d32f9a0c764788588b8779e6b7192",
    "preview/ps_mht_v001_full_tower_assembly_phase1.svg":
        "be65fa2910b1e45c2fc6087c8e909c995c71fca41e60e2612370d881f521b03f",
    "step/ps_mht_v001_aluminum_frame_phase1.step":
        "73ed10e3ac6856015e65424673a31d1d57e52e635f13271c9439fdfe29a731a5",
    "step/ps_mht_v001_full_tower_assembly_phase1.step":
        "ea38ed2b87cfb5830cc50866c35fe33df07da91ef276f973d92bd988394cc805",
    "step/ps_mht_v001_planting_module_A.step":
        "a36d5216279f4a8c9ebaab93ec7e364d041c339a3f6670e615480cb0a7ce7da6",
    "step/ps_mht_v001_tower_5_module_phase1.step":
        "03d9b4e7f031e127619eeafd18c9a3d4d27a3447bfa26e447706c1ca785478ef",
    "stl/ps_mht_v001_planting_module_A.stl":
        "8f6074b8b984883d95413627832679636beda4cbf7986f06303abbabdc88298d",
}


PHASE2_SHA256 = {
    "preview/phase2_validation_report.json":
        "8099efa855b302f53cb72bafbe38cf272cd621b0856b255aacc5e45dae8ffe8e",
    "preview/ps_mht_v001_module_interface_section_phase2.svg":
        "67a9d852a075354cdae47d675348f6bd531cbcb3f8d2415689486a95a88c3ae1",
    "preview/ps_mht_v001_planting_module_interface_phase2.svg":
        "af05128462a5d0b11989ed7316d45f7de3b28152de4c1addeb2efa17825f7865",
    "step/ps_mht_v001_exploded_interface_phase2.step":
        "f61748800ee84f777f20820ebe1542793066c2d745d4c4bd945a8651a8419739",
    "step/ps_mht_v001_keepouts_reference_phase2.step":
        "98c51725ec4732a1414eed1d99f2c4d48300390ecac28c006e948926100dd225",
    "step/ps_mht_v001_m4_insert_coupon_phase2.step":
        "67138fa89bfafc629d07d4e58cc3a268e3a26018ef4676b6c8a73134e3b01e61",
    "step/ps_mht_v001_m4_nut_cartridge_phase2.step":
        "00acf54b9b44245d362f786e3a1461cb11597afac796e98e1d090622da7703e5",
    "step/ps_mht_v001_m4_nut_cartridge_retainer_phase2.step":
        "01401a139c38f0d7d08d751900da96035c9e4fc085aef780f12a4c614ea08c4e",
    "step/ps_mht_v001_module_gasket_cord_reference_phase2.step":
        "8da49649bcf10b3ac0f66ede6e40b59f445a269704fafde9987e46156f346f64",
    "step/ps_mht_v001_module_interface_coupon_phase2.step":
        "03830cb11dfd8da7d557c5eb2418e2da96777415af850f5fc7486125f8e39df1",
    "step/ps_mht_v001_module_pair_0deg_phase2.step":
        "eb51fda72ece5c9030a6e59c49433ccc43664e8eb964e012ae362e6a3ba565fb",
    "step/ps_mht_v001_module_pair_60deg_phase2.step":
        "e6d8c58f16d64fd13e7be9d087bfba10688399a0c0626f0ba63faa5cd3bb9aac",
    "step/ps_mht_v001_module_roundness_coupon_phase2.step":
        "eb03fa96c51ed512b97956070b9c5bd648fe7ef6713e4e90132e6f63f331b3e4",
    "step/ps_mht_v001_planting_module_interface_phase2.step":
        "eb31bf8cfaa9b07ae92fab7776df359fa6f43f8164062dfb09c69b2938a17768",
    "step/ps_mht_v001_tpu_gasket_coupon_phase2.step":
        "25f7d3c0144d9aff576f2b67e69f494c354e50bbf76407ab27ab5ccc43b0f095",
    "stl/ps_mht_v001_m4_insert_coupon_phase2.stl":
        "951b7e3b08b647855b0fe80a2e7dfc043961a798f92efd90be331d5c72e4501a",
    "stl/ps_mht_v001_m4_nut_cartridge_phase2.stl":
        "f0a6b290688c7fbd31fdf165adfe869fbf13f99ea64aded6682fb03e876be4b3",
    "stl/ps_mht_v001_m4_nut_cartridge_retainer_phase2.stl":
        "f73e1ae269fa1ad738b827693a78f8ea3648bb5d1109b183dd585ca37c64a97e",
    "stl/ps_mht_v001_module_interface_coupon_phase2.stl":
        "e5bbd98a8f9f2642a4cc728c21d32a64e35c468b93aa634386b5a77287ad070c",
    "stl/ps_mht_v001_module_roundness_coupon_phase2.stl":
        "60a5228bdac20f7d15a1fef45c8a1ff0192f9e218eaa88845f6e18cf1e2af401",
    "stl/ps_mht_v001_planting_module_interface_phase2.stl":
        "3f23d0e4b75a233ed730ddbee85a141c3517cd73ff29854dded4dfb71ebb463f",
    "stl/ps_mht_v001_tpu_gasket_coupon_phase2.stl":
        "65215face1f04b1a56fd6f6e9510ce30e2c527b414879a5b4f3af39790b61ff5",
}


PHASE3A_SHA256 = json.loads(
    Path(__file__).with_name("phase3a_baseline.json").read_text(
        encoding="utf-8"
    )
)

PHASE3A1_SHA256 = json.loads(
    Path(__file__).with_name("phase3a1_baseline.json").read_text(
        encoding="utf-8"
    )
)

PHASE3R_SHA256 = json.loads(
    Path(__file__).with_name("phase3r_baseline.json").read_text(
        encoding="utf-8"
    )
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_baseline_hashes(
    export_root: Path,
) -> dict[str, dict[str, object]]:
    report: dict[str, dict[str, object]] = {}
    for phase, expected in (
        ("phase1", PHASE1_SHA256),
        ("phase2", PHASE2_SHA256),
        ("phase3a", PHASE3A_SHA256),
        ("phase3a1", PHASE3A1_SHA256),
        ("phase3r", PHASE3R_SHA256),
    ):
        actual = {
            relative: file_sha256(export_root / relative)
            for relative in expected
        }
        report[phase] = {
            "expected": expected,
            "actual": actual,
            "unchanged": actual == expected,
        }
    return report
