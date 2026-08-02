"""Core Phase 4T-LS-A architecture specification tests (7)."""

import json
from pathlib import Path

import yaml

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001 import parameters as p


ROOT = Path(__file__).parents[1]


def test_maximum_tower_count_is_eight() -> None:
    assert p.maximum_tower_count == 8


def test_single_circulation_pump_authority() -> None:
    assert p.circulation_pump_count == 1


def test_parallel_equalization_and_serial_prohibition() -> None:
    assert p.hydraulic_connection == "PARALLEL_BRANCH_EQUALIZATION"
    assert p.serial_daisy_chain_allowed is False


def test_local_sumps_are_vented_and_never_airtight() -> None:
    assert p.local_sump_vented is True
    assert p.local_sump_airtight_allowed is False


def test_local_sump_height_reference_is_110_to_130_mm() -> None:
    assert p.local_sump_outer_height_mm == (110.0, 130.0)


def test_local_sump_volume_and_freeboard_ranges() -> None:
    assert p.local_sump_normal_volume_l == (5.0, 7.0)
    assert p.local_sump_gross_capacity_l == (12.0, 16.0)
    assert p.local_sump_emergency_freeboard_l[0] >= 4.0


def test_yaml_json_authorities_parse_and_prohibit_printed_tank() -> None:
    spec = yaml.safe_load(
        (ROOT / "specs" / "ps_mht_8t_linked_sump_v001.yaml").read_text(
            encoding="utf-8"
        )
    )
    interfaces = json.loads(
        (ROOT / "specs" / "ps_mht_8t_linked_sump_interfaces.json").read_text(
            encoding="utf-8"
        )
    )
    assert spec["local_sump"]["watertight_authority"] == "PURCHASED_PP_OR_PE_CONTAINER"
    assert "printed_petg_watertight_15L_tank" in spec["prohibited"]
    assert interfaces["cad"]["stl_output_count"] == 0
