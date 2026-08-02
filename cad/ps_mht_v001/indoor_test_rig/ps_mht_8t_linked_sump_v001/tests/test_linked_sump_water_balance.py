"""Water inventory, isolation and staged-flow tests (7)."""

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.parameters import (
    pump_eight_tower_capacity_status,
    zone_target_flow_l_h,
    zone_target_flow_l_min,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.water_balance import (
    build_water_balance_report,
    emergency_supply_misopen_sensitivity,
    isolation_sensitivity,
    water_balance_for_tower_count,
)


def test_flow_tables_cover_four_six_and_eight_towers() -> None:
    assert zone_target_flow_l_min == {4: (2.0, 4.0), 6: (3.0, 6.0), 8: (4.0, 8.0)}
    assert zone_target_flow_l_h == {4: (120.0, 240.0), 6: (180.0, 360.0), 8: (240.0, 480.0)}


def test_eight_tower_pump_capacity_is_not_prequalified() -> None:
    assert pump_eight_tower_capacity_status == "NOT_QUALIFIED"
    assert water_balance_for_tower_count(8)["pump_capacity_qualified"] is False


def test_known_normal_inventory_for_four_six_eight() -> None:
    assert water_balance_for_tower_count(4)["known_normal_inventory_excluding_pipe_and_pump_well_l"] == [28.0, 36.0]
    assert water_balance_for_tower_count(6)["known_normal_inventory_excluding_pipe_and_pump_well_l"] == [42.0, 54.0]
    assert water_balance_for_tower_count(8)["known_normal_inventory_excluding_pipe_and_pump_well_l"] == [56.0, 72.0]


def test_tower_buffer_totals_are_eight_twelve_sixteen_litres() -> None:
    assert [water_balance_for_tower_count(n)["tower_buffer_total_l"] for n in (4, 6, 8)] == [8.0, 12.0, 16.0]


def test_conservative_freeboard_absorbs_known_tower_return() -> None:
    for count in (4, 6, 8):
        case = water_balance_for_tower_count(count)
        assert case["worst_case_geometric_empty_capacity_l"] == 5.0 * count
        assert case["worst_case_headroom_after_known_tower_return_l"] == 3.0 * count


def test_one_and_two_sump_isolation_keep_other_branches_connected() -> None:
    for count in (4, 6, 8):
        for isolated in (1, 2):
            case = isolation_sensitivity(count, isolated)
            assert case["downstream_active_sumps_disconnected"] is False
            assert case["active_tower_count"] == count - isolated


def test_balance_preserves_unknowns_and_misopen_sensitivity() -> None:
    report = build_water_balance_report()
    assert "V_pipe" in report["unresolved_variables"]
    assert report["four_unused_branches_at_four_towers"]["closed_branch_count"] == 4
    assert emergency_supply_misopen_sensitivity()[-1]["receiver_required_before_margin_l"] == [7.5, 15.0]
