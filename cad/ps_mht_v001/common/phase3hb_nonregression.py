"""Phase 3H-A output and linked-sump SHA-256 non-regression audit."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


PHASE3HA_SHA256 = {
    "preview/horizontal_joint_isometric_phase3ha.svg": "3a174c273e42aa05f8bf746852311b71fc9ad51b258dc1f33fccb5ddc0fe3cbc",
    "preview/horizontal_joint_section_phase3ha.svg": "abf3cd23434d744cd323633a74da9eb2d91f8af0e43f49303b091a13078ab5a5",
    "preview/phase3ha_validation_report.json": "432cd293039f57348a44f26e15c1408f5679b968c66922337ac42251e471141d",
    "preview/print_manifest_phase3ha.json": "6fd98de5f62e6a8adda5bcac079e2436423d01bfa8cdb27129fa1994025715db",
    "ps_mht_v001_phase3ha_delivery.zip": "0f6fd9098a901eca8c6a3f0e945ebe6034c40ad6660c8803c50edfd551f197d6",
    "step/full_ring_joint_pair_c050_reference_phase3ha.step": "2e61af0d9a6b6c4f628653be26735c808fcda580de15d998d8f4b9e2ebb4f7db",
    "step/horizontal_joint_arc_coupon_c030_phase3ha.step": "6485e03769b3befe418ec35bd6d9a88f066f416d846ac1f9de2cabca2c8db6f0",
    "step/horizontal_joint_arc_coupon_c050_phase3ha.step": "9c4926f9d3268dfce3927f598eef575b442a4a44d657cf6e560eaf276a72e53e",
    "step/horizontal_joint_arc_coupon_c070_phase3ha.step": "d8bb9c77f4279ed6648f5e74d8f6f602632b6c1a563ddc5e666fc435a74af59a",
    "step/horizontal_joint_compression_assembly_reference_phase3ha.step": "95362dd8b26274e3beff46bed045c0602db0a521636569ce6d2fa2255aa0f5ad",
    "step/horizontal_joint_compression_ring_phase3ha.step": "5a5fd51c9f30dfed1429a9dce97e63dab479247156e388eca8bec1d7fd0d85d3",
    "step/temporary_test_membrane_reference_phase3ha.step": "ad39df77f9a8972495547ff3442d804fd886b251f3fcf0e62237504e650dbfab",
    "stl/horizontal_joint_arc_coupon_c030_phase3ha.stl": "f3d15ee13fb51c1d28d7967f396267ff60d6487ab8b925f5da4492669e6e5b89",
    "stl/horizontal_joint_arc_coupon_c050_phase3ha.stl": "6787d6a52d742c2d17f48564675789a37c52bfffb85f348a4c602773ac321144",
    "stl/horizontal_joint_arc_coupon_c070_phase3ha.stl": "8ec7de5b0b2afe905cd5d295e3a3754bc9df3f94fd35ea1aebf6427e250f2b38",
    "stl/horizontal_joint_compression_ring_phase3ha.stl": "124a9c08c623c9a689c44151493d48e21ac311d8f8d0daf5986a89505e2fd2b7",
}

LINKED_SUMP_SHA256SUMS_SHA256 = (
    "c300b1e77fe0c0721747e39e176982d37058358c63d143b46020948fad391bbe"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_phase3ha_exports(export_root: Path) -> dict[str, object]:
    actual = {
        relative: file_sha256(export_root / relative)
        for relative in PHASE3HA_SHA256
    }
    return {
        "expected": PHASE3HA_SHA256,
        "actual": actual,
        "artifact_count": len(PHASE3HA_SHA256),
        "unchanged": actual == PHASE3HA_SHA256,
    }


def audit_linked_sump_phase4tlsa(repository_root: Path) -> dict[str, object]:
    sump_root = (
        repository_root
        / "cad"
        / "ps_mht_v001"
        / "indoor_test_rig"
        / "ps_mht_8t_linked_sump_v001"
    )
    sums_path = sump_root / "SHA256SUMS.txt"
    sums_hash = file_sha256(sums_path)
    expected: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"invalid linked-sump SHA line: {line!r}")
        expected[match.group(2)] = match.group(1)
    actual = {
        relative: file_sha256(repository_root / relative)
        for relative in expected
    }
    return {
        "manifest_sha256_expected": LINKED_SUMP_SHA256SUMS_SHA256,
        "manifest_sha256_actual": sums_hash,
        "manifest_unchanged": sums_hash == LINKED_SUMP_SHA256SUMS_SHA256,
        "expected": expected,
        "actual": actual,
        "artifact_count_in_manifest": len(expected),
        "unchanged": (
            sums_hash == LINKED_SUMP_SHA256SUMS_SHA256
            and actual == expected
        ),
    }
