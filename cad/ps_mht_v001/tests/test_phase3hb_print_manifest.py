"""Phase 3H-B physical-gate print-manifest tests (7)."""

from ps_mht_v001.print_manifest_phase3hb import build_print_manifest_phase3hb


def _manifest() -> dict[str, object]:
    return build_print_manifest_phase3hb()


def test_phase3hb_plate_01_is_ready_first() -> None:
    item = _manifest()["items"][0]
    assert item["print_status"] == "READY_FIRST"
    assert item["part"] == "FULL_RING_LOWER_C050"


def test_phase3hb_plate_02_waits_for_plate_01_inspection() -> None:
    item = _manifest()["items"][1]
    assert item["print_status"] == "READY_AFTER_PLATE_01_INSPECTION"
    assert item["part"] == "FULL_RING_UPPER_C050"


def test_phase3hb_plate_03_is_held() -> None:
    item = _manifest()["items"][2]
    assert item["print_status"] == "HOLD_UNTIL_FULL_RING_PAIR_PASS"


def test_phase3hb_c030_is_not_required() -> None:
    assert _manifest()["candidate_disposition"]["c030"] == "NOT_REQUIRED"


def test_phase3hb_c070_is_not_required() -> None:
    assert _manifest()["candidate_disposition"]["c070"] == "NOT_REQUIRED"


def test_phase3hb_membrane_is_reference_only_and_water_is_pending() -> None:
    manifest = _manifest()
    assert manifest["temporary_test_membrane_status"] == "REFERENCE_ONLY"
    assert manifest["water_test_status"] == "PENDING"


def test_phase3hb_prints_are_alone_and_compression_release_is_not_automatic() -> None:
    manifest = _manifest()
    assert all(item["print_alone"] for item in manifest["items"])
    assert manifest["compression_ring_release_is_automatic"] is False
