"""Scope gates, manifest ordering, seam independence and non-finalization."""

from pathlib import Path

from ps_mht_v001.parameters import (
    netpot_body_passage_selected,
    phase3sa_seam_clearance_selected,
)
from ps_mht_v001.print_manifest_phase3pa import build_print_manifest_phase3pa


def test_phase3pa_manifest_prints_c805_first() -> None:
    items = build_print_manifest_phase3pa()["print_items"]
    assert items[0] == {
        "file_name": "plate_01_netpot_fit_c805_phase3pa.stl",
        "quantity": 1,
        "print_status": "READY_FIRST",
        "prerequisite": None,
    }


def test_phase3pa_manifest_c800_and_c810_are_conditional() -> None:
    items = build_print_manifest_phase3pa()["print_items"]
    assert items[1]["prerequisite"] == "c805_too_loose"
    assert items[2]["prerequisite"] == "c805_too_tight"
    assert all(item["quantity"] == 1 for item in items)


def test_phase3pa_manifest_contains_no_final_function_ring() -> None:
    manifest = build_print_manifest_phase3pa()
    assert manifest["final_function_ring_included"] is False
    assert all("function_ring" not in item["file_name"] for item in manifest["print_items"])


def test_phase3pa_seam_selection_is_unchanged_and_independent() -> None:
    assert phase3sa_seam_clearance_selected is None
    assert build_print_manifest_phase3pa()["phase3sa_seam_clearance_selected"] is None


def test_phase3pa_body_passage_selection_does_not_finalize_port_assembly() -> None:
    assert netpot_body_passage_selected == 80.5
    assert build_print_manifest_phase3pa()["selected_passage_mm"] == 80.5
    assert build_print_manifest_phase3pa()["final_function_ring_included"] is False


def test_phase3pa_build_does_not_generate_phase3sa1_selected_plates() -> None:
    source = (Path(__file__).parents[1] / "build_phase3pa.py").read_text(encoding="utf-8")
    assert "build_plate_02_panel_capture_coupon_phase3sa1" not in source
    assert "build_plate_03_sector_panel_single_phase3sa1" not in source
    assert "build_plate_04_three_sector_short_parts_phase3sa1" not in source


def test_phase3pa_no_final_design_builder_is_present() -> None:
    package = Path(__file__).parents[1]
    forbidden = (
        "final_port_function_ring_phase3pa",
        "final_netpot_liner_phase3pa",
        "final_panel_integration_phase3pa",
    )
    assert not any((package / f"{name}.py").exists() for name in forbidden)
