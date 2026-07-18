#!/usr/bin/env python3
"""ST-009 deterministic seasonal capacity sweep contract tests."""

from __future__ import annotations

import ast
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "software/station_control/station/seasonal_capacity_sweep.py"
BASE = ROOT / "software/station_control/config_examples/seasonal-field-plan.example.json"
SWEEP = ROOT / "software/station_control/config_examples/seasonal-capacity-sweep-plan.example.json"
SPEC = importlib.util.spec_from_file_location("st009_capacity_sweep_tests", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("ST-009 module load failed.")
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class SeasonalCapacitySweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.st008 = MOD.load_st008(ROOT)
        cls.base, cls.base_report = MOD.validate_base_model(cls.st008, MOD.load_strict_json(BASE))
        cls.sweep = MOD.validate_sweep_plan(MOD.load_strict_json(SWEEP))
        cls.weed_survivors, cls.weed_shortfalls = MOD.weed_upper_bound_survivors(
            cls.st008, cls.base, cls.sweep["ranges"]["weed_rover_counts"],
        )
        cls.harvest_survivors, cls.cut_pruned, cls.recovery_pruned = MOD.harvest_upper_bound_survivors(
            cls.st008, cls.base, cls.sweep["ranges"],
        )
        cls.candidate = MOD.Candidate(4, 3, 5, 2, 16, 4, 4000, 4, 50, 20)
        cls.sample_report = MOD.build_report(
            ROOT, copy.deepcopy(cls.base), copy.deepcopy(cls.sweep), search_engine=cls.fake_search,
        )
        cls.broadcast_insufficient = MOD.broadcast_insufficient_targets(cls.base_report)
        cls.regression_a = cls.formal_records(
            MOD.Candidate(4, 3, 5, 3, 28, 12, 4000, 6, 50, 0),
        )
        cls.regression_b = cls.formal_records(
            MOD.Candidate(4, 6, 5, 3, 28, 12, 4000, 6, 50, 0),
        )
        reduced_ranges = {
            "broadcast_rover_counts": [4], "weed_rover_counts": [2, 3, 4],
            "high_cut_rover_counts": [4, 5], "carrier_rover_counts": [2, 3],
            "battery_pool_counts": [16, 20], "charger_counts": [4, 6],
            "cassette_capacity_g_values": [1000, 2000],
            "carrier_cassettes_per_trip_values": [1, 2],
            "temporary_drop_slot_counts": [50], "manual_recovery_per_day_values": [0, 10],
        }
        reduced_sweep = copy.deepcopy(cls.sweep)
        reduced_sweep["ranges"] = reduced_ranges
        reduced_weed, _ = MOD.weed_upper_bound_survivors(
            cls.st008, cls.base, reduced_ranges["weed_rover_counts"],
        )
        reduced_harvest, _, _ = MOD.harvest_upper_bound_survivors(
            cls.st008, cls.base, reduced_ranges,
        )
        cls.reduced_optimized, _ = MOD.exact_search(
            cls.st008, cls.base, reduced_sweep, reduced_weed, reduced_harvest,
        )
        cls.reduced_oracle = [
            MOD.TargetAccumulator(0, 0, 0, None, None, {}, []) for _ in MOD.TARGET_IDS
        ]
        for candidate in MOD.candidate_generator(reduced_ranges):
            scenarios = cls.formal_records(candidate)
            for target_index in range(3):
                MOD.update_accumulator(
                    cls.reduced_oracle[target_index],
                    MOD.StoredCandidate(candidate, MOD.target_metrics(scenarios, target_index)),
                )

    @staticmethod
    def fake_search(st008, base, sweep, weed, harvest):
        accumulators = [MOD.TargetAccumulator(0, 0, 0, None, None, {}, []) for _ in MOD.TARGET_IDS]
        candidate = MOD.Candidate(4, 3, 5, 2, 16, 4, 4000, 4, 50, 20)
        good = MOD.ScenarioMetrics(True, 10000, 10000, 10000, 10000, 0, 0, 0, 0, 0, ("NONE",))
        bad = MOD.ScenarioMetrics(False, 9000, 8000, 7000, 6000, 5, 2, 1, 100, 200, ("DISTANCE_CAPACITY",))
        scenarios = (good, bad, bad, bad, bad, bad)
        for index in range(3):
            MOD.update_accumulator(accumulators[index], MOD.StoredCandidate(candidate, MOD.target_metrics(scenarios, index)))
        return accumulators, {"evaluated": 1, "unique_satisfying": 1, "joined": 1, "power_pruned": 0, "battery_cache_hits": 0, "battery_cache_entries": 1, "phase_cache_hits": 0, "diagnostic_candidate_count": 1, "harvest_operation_cache_entries": 1, "harvest_battery_cache_entries": 1}

    @classmethod
    def formal_records(cls, candidate):
        geometry = cls.st008.derive_geometry(cls.base["field"])
        assumptions = dict(cls.base["assumptions"])
        assumptions["cassette_capacity_g"] = candidate.cassette_g
        assumptions["temporary_drop_slot_count"] = candidate.slots
        records = []
        for index, base_scenario in enumerate(cls.base["scenarios"]):
            scenario = MOD.scenario_for_candidate(base_scenario, candidate, index)
            records.append(MOD._scenario_metrics(
                cls.st008,
                cls.st008.simulate_broadcast(
                    scenario, geometry, cls.base["battery_model"], assumptions,
                ),
                cls.st008.simulate_weed(
                    scenario, geometry, cls.base["battery_model"], assumptions,
                ),
                cls.st008.simulate_harvest(
                    scenario, geometry, cls.base["battery_model"], assumptions,
                ),
            ))
        return tuple(records)

    @staticmethod
    def accumulator_snapshot(accumulator):
        return {
            "status": "FOUND" if accumulator.satisfying_count else "NOT_FOUND_WITHIN_BOUNDS",
            "count": accumulator.satisfying_count,
            "equipment": accumulator.equipment_best.candidate.candidate_id if accumulator.equipment_best else "",
            "human": accumulator.human_best.candidate.candidate_id if accumulator.human_best else "",
            "pareto": [item.candidate.candidate_id for item in MOD._frontier_records(accumulator)],
            "nearest": [item.candidate.candidate_id for _, item in accumulator.nearest],
        }

    def invalid_sweep(self, change) -> None:
        value = copy.deepcopy(self.sweep); change(value)
        with self.assertRaises(MOD.SweepFailure): MOD.validate_sweep_plan(value)

    # ST-008 integration
    def test_st008_module_load(self): self.assertEqual(self.st008.PHASE, "ST-008")
    def test_st008_base_validation(self): self.assertEqual(self.base["plan_version"], 1)
    def test_st008_six_scenarios(self): self.assertEqual(tuple(x["scenario_id"] for x in self.base["scenarios"]), MOD.SCENARIO_IDS)
    def test_st008_formal_result_reuse(self): self.assertEqual(self.base_report["result"], "PASS")
    def test_st008_source_not_duplicated(self): self.assertNotIn("def simulate_harvest(", SOURCE.read_text(encoding="utf-8"))
    def test_st008_source_tracked(self): self.assertTrue((ROOT / "software/station_control/station/seasonal_field_simulator.py").is_file())
    def test_st008_invalid_load(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(MOD.SweepFailure): MOD.load_st008(Path(td))
    def test_st008_candidate_adapter(self): self.assertTrue(MOD.validate_injected_candidate(self.st008, self.base, self.candidate))
    def test_st008_candidate_plan_six(self): self.assertEqual(len(MOD.injected_candidate_plan(self.base, self.candidate)["scenarios"]), 6)
    def test_st008_batch_six_adapter(self): self.assertTrue(MOD.validate_injected_candidate(self.st008, self.base, MOD.Candidate(4, 6, 12, 8, 48, 12, 4000, 6, 200, 20)))

    # Search space and candidate formulas
    def test_raw_count(self): self.assertEqual(MOD.raw_candidate_count(self.sweep["ranges"]), 2041200)
    def test_generator_is_iterator(self): self.assertFalse(isinstance(MOD.candidate_generator(self.sweep["ranges"]), list))
    def test_generator_deterministic(self): self.assertEqual(next(MOD.candidate_generator(self.sweep["ranges"])), next(MOD.candidate_generator(self.sweep["ranges"])))
    def test_generator_first_id(self): self.assertEqual(next(MOD.candidate_generator(self.sweep["ranges"])).candidate_id, "CFG-B04-W02-H04-C02-P16-R04-K1000-T01-S050-M00")
    def test_generator_unique_sample(self):
        ids=[x.candidate_id for x in itertools.islice(MOD.candidate_generator(self.sweep["ranges"]), 500)]; self.assertEqual(len(ids), len(set(ids)))
    def test_common_rover_formula(self): self.assertEqual(self.candidate.common_rovers, 7)
    def test_attachment_formula(self): self.assertEqual(self.candidate.attachments, 14)
    def test_payload_formula(self): self.assertEqual(self.candidate.payload_g, 16000)
    def test_cassette_proxy_formula(self): self.assertEqual(self.candidate.cassette_proxy, 68)
    def test_candidate_property_order(self): self.assertEqual(tuple(MOD.candidate_document(self.candidate))[0], "candidate_id")

    # Target and upper bounds
    def test_target_order(self): self.assertEqual(MOD.TARGET_IDS, ("TARGET_BASELINE", "TARGET_WET_RESILIENT", "TARGET_ALL_SCENARIOS"))
    def test_baseline_semantics(self): self.assertEqual(MOD.TARGET_INDICES[0], (0,))
    def test_wet_semantics(self): self.assertEqual(MOD.TARGET_INDICES[1], (0, 2))
    def test_all_semantics(self): self.assertEqual(MOD.TARGET_INDICES[2], (0, 1, 2, 3, 4, 5))
    def test_weed_baseline_survivors(self): self.assertEqual(self.weed_survivors["TARGET_BASELINE"], (3, 4, 5, 6))
    def test_weed_wet_safe_prune(self): self.assertEqual(self.weed_survivors["TARGET_WET_RESILIENT"], ())
    def test_weed_all_safe_prune(self): self.assertEqual(self.weed_survivors["TARGET_ALL_SCENARIOS"], ())
    def test_weed_nearest_retained(self): self.assertGreater(self.weed_shortfalls["TARGET_WET_RESILIENT"], 0)
    def test_harvest_evaluated_count_basis(self): self.assertEqual(9*7*3*4*4*3, 9072)
    def test_harvest_survivors(self): self.assertEqual(len(self.harvest_survivors), 2560)
    def test_slot_not_automatic_prune(self): self.assertTrue(any(x[4] == 50 for x in self.harvest_survivors))
    def test_upper_bound_not_success(self): self.assertNotIn("target_satisfied", MOD.harvest_upper_bound_survivors.__name__)
    def test_broadcast_fixed_insufficient_wet(self): self.assertTrue(self.broadcast_insufficient["TARGET_WET_RESILIENT"])
    def test_broadcast_fixed_insufficient_all(self): self.assertTrue(self.broadcast_insufficient["TARGET_ALL_SCENARIOS"])
    def test_wet_broadcast_exact_processed(self): self.assertEqual(self.base_report["scenario_results"][2]["broadcast"]["processed_distance_mm"],2697000)
    def test_wet_broadcast_exact_target(self): self.assertEqual(self.base_report["scenario_results"][2]["broadcast"]["target_distance_mm"],2990000)
    def test_wet_broadcast_exact_shortfall(self): self.assertEqual(self.base_report["scenario_results"][2]["broadcast"]["shortfall_distance_mm"],293000)
    def test_wet_recommendation_includes_broadcast(self): self.assertIn("BROADCAST_FIXED_CAPACITY_INSUFFICIENT",self.sample_report.document["target_results"][1]["recommendations"])
    def test_all_recommendation_includes_broadcast(self): self.assertIn("BROADCAST_FIXED_CAPACITY_INSUFFICIENT",self.sample_report.document["target_results"][2]["recommendations"])
    def test_wet_broadcast_diagnostic(self): self.assertIn(("TARGET_WET_RESILIENT","SWEEP_BROADCAST_FIXED_INSUFFICIENT"),[(x["target_id"],x["code"]) for x in self.sample_report.document["diagnostics"]])
    def test_all_broadcast_diagnostic(self): self.assertIn(("TARGET_ALL_SCENARIOS","SWEEP_BROADCAST_FIXED_INSUFFICIENT"),[(x["target_id"],x["code"]) for x in self.sample_report.document["diagnostics"]])
    def test_w03_versus_w06_nearest_ordering(self):
        a=MOD.StoredCandidate(MOD.Candidate(4,3,5,3,28,12,4000,6,50,0),MOD.target_metrics(self.regression_a,1));b=MOD.StoredCandidate(MOD.Candidate(4,6,5,3,28,12,4000,6,50,0),MOD.target_metrics(self.regression_b,1));self.assertLess(MOD.nearest_key(b),MOD.nearest_key(a))
    def test_w03_exact_untreated(self): self.assertEqual(self.regression_a[2].unfinished_weed_mm,2729500)
    def test_w06_exact_untreated(self): self.assertEqual(self.regression_b[2].unfinished_weed_mm,1721500)

    # Power and cache
    def test_power_count(self): self.assertEqual(len(tuple(itertools.product(MOD.EXPECTED_RANGES["battery_pool_counts"], MOD.EXPECTED_RANGES["charger_counts"]))), 45)
    def test_battery_range(self): self.assertEqual(MOD.EXPECTED_RANGES["battery_pool_counts"][0::8], [16,48])
    def test_charger_range(self): self.assertEqual(MOD.EXPECTED_RANGES["charger_counts"], [4,6,8,10,12])
    def test_battery_cache_deterministic(self):
        cache=MOD.BatteryScheduleCache(self.st008.schedule_batteries); a=cache((20,), (30,), 2, 1, 10, 1); b=cache((20,), (30,), 2, 1, 10, 1); self.assertEqual(a,b); self.assertEqual(cache.hits,1)
    def test_cache_memory_only(self): self.assertFalse(hasattr(MOD.BatteryScheduleCache(self.st008.schedule_batteries), "path"))
    def test_power_prune_relation(self): self.assertLess(16, MOD.Candidate(4,6,12,8,16,4,1000,1,50,0).common_rovers)

    # Mechanical flags
    def test_2kg_flag(self): self.assertIn("CASSETTE_LOAD_TEST_REQUIRED", MOD.mechanical_flags(2000,1))
    def test_4kg_flags(self): self.assertIn("MUD_SINKING_TEST_REQUIRED", MOD.mechanical_flags(4000,1))
    def test_batch6_flag(self): self.assertIn("CARRIER_BATCH_RACK_REQUIRED", MOD.mechanical_flags(1000,6))
    def test_payload_4kg_boundary(self): self.assertNotIn("CARRIER_PAYLOAD_ENGINEERING_REVIEW_REQUIRED", MOD.mechanical_flags(1000,4))
    def test_payload_over_4kg(self): self.assertIn("CARRIER_PAYLOAD_ENGINEERING_REVIEW_REQUIRED", MOD.mechanical_flags(1000,6))
    def test_flag_order(self): self.assertEqual(self.candidate.flags, tuple(x for x in MOD.MECHANICAL_FLAG_ORDER if x in self.candidate.flags))
    def test_flags_not_completion_gate(self): self.assertFalse(self.sweep["objective_policy"]["mechanical_review_is_feasibility_gate"])

    # Pareto and selection
    def test_strict_dominance(self): self.assertTrue(MOD.dominates((1,)*9,(2,)*9))
    def test_equality_not_dominance(self): self.assertFalse(MOD.dominates((1,)*9,(1,)*9))
    def test_one_dimension_dominance(self): self.assertTrue(MOD.dominates((1,2,2,2,2,2,2,2,2),(2,2,2,2,2,2,2,2,2)))
    def test_incomparable(self): self.assertFalse(MOD.dominates((1,2,1,1,1,1,1,1,1),(2,1,1,1,1,1,1,1,1)))
    def test_duplicate_candidate_removed(self):
        a=MOD.TargetAccumulator(0,0,0,None,None,{},[]); m=MOD.target_metrics((MOD.ScenarioMetrics(True,10000,10000,10000,10000,0,0,0,0,0,("NONE",)),)*6,0); r=MOD.StoredCandidate(self.candidate,m); MOD.update_frontier(a,r); MOD.update_frontier(a,r); self.assertEqual(sum(len(v) for v in a.frontier.values()),1)
    def test_equipment_key_deterministic(self):
        m=MOD.target_metrics((MOD.ScenarioMetrics(True,10000,10000,10000,10000,0,0,0,0,0,("NONE",)),)*6,0); r=MOD.StoredCandidate(self.candidate,m); self.assertEqual(MOD.equipment_key(r),MOD.equipment_key(r))
    def test_human_key_starts_manual(self):
        m=MOD.target_metrics((MOD.ScenarioMetrics(True,10000,10000,10000,10000,0,0,0,0,0,("NONE",)),)*6,0); self.assertEqual(MOD.human_key(MOD.StoredCandidate(self.candidate,m))[0],20)
    def test_nearest_key_length(self):
        m=MOD.target_metrics((MOD.ScenarioMetrics(False,0,0,0,0,1,1,1,1,1,("NONE",)),)*6,2); self.assertEqual(len(MOD.nearest_key(MOD.StoredCandidate(self.candidate,m))),11)
    def test_nearest_top_10_deterministic(self):
        for accumulator in self.reduced_optimized: self.assertEqual(accumulator.nearest,sorted(accumulator.nearest,key=lambda x:x[0]))
    def test_nearest_top_10_globally_exact(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["nearest"],self.accumulator_snapshot(oracle)["nearest"])
    def test_reduced_oracle_status(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["status"],self.accumulator_snapshot(oracle)["status"])
    def test_reduced_oracle_count(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(optimized.satisfying_count,oracle.satisfying_count)
    def test_reduced_oracle_equipment_min(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["equipment"],self.accumulator_snapshot(oracle)["equipment"])
    def test_reduced_oracle_human_min(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["human"],self.accumulator_snapshot(oracle)["human"])
    def test_reduced_oracle_pareto(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["pareto"],self.accumulator_snapshot(oracle)["pareto"])
    def test_reduced_oracle_nearest(self):
        for optimized,oracle in zip(self.reduced_optimized,self.reduced_oracle): self.assertEqual(self.accumulator_snapshot(optimized)["nearest"],self.accumulator_snapshot(oracle)["nearest"])
    def test_reduced_baseline_nearest_summary_mask(self): self.assertEqual(len(MOD.summary_document(self.reduced_optimized[0].nearest[0][1],0)["scenario_completion_mask"]),6)

    # Report and safety
    def test_report_root_order(self): self.assertEqual(tuple(self.sample_report.document)[0:4], ("report_version","phase","sweep_id","result"))
    def test_report_target_order(self): self.assertEqual([x["target_id"] for x in self.sample_report.document["target_results"]], list(MOD.TARGET_IDS))
    def test_report_candidate_order(self): self.assertEqual(next(iter(self.sample_report.document["target_results"][0]["equipment_quantity_min_candidate"]["candidate"])), "candidate")
    def test_report_diagnostic_order(self):
        d=self.sample_report.document["diagnostics"]; self.assertEqual(d,sorted(d,key=lambda x:(x["component"],x["code"],x["target_id"],x["candidate_id"],x["message"])))
    def test_report_recommendation_order(self):
        for t in self.sample_report.document["target_results"]: self.assertEqual(t["recommendations"],[x for x in MOD.RECOMMENDATION_ORDER if x in t["recommendations"]])
    def test_report_json_deterministic(self): self.assertEqual(MOD.render_json_report(self.sample_report),MOD.render_json_report(self.sample_report))
    def test_report_text_deterministic(self): self.assertEqual(MOD.render_text_report(self.sample_report),MOD.render_text_report(self.sample_report))
    def test_base_hash_stable(self): self.assertEqual(self.sample_report.document["canonical_base_plan_sha256"],MOD.sha256_canonical(self.base))
    def test_sweep_hash_stable(self): self.assertEqual(self.sample_report.document["canonical_sweep_plan_sha256"],MOD.sha256_canonical(self.sweep))
    def test_search_hash_stable(self): self.assertEqual(len(self.sample_report.document["canonical_search_state_sha256"]),64)
    def test_no_timestamp(self): self.assertNotIn("timestamp",MOD.render_json_report(self.sample_report).lower())
    def test_no_hostname(self): self.assertNotIn("hostname",MOD.render_json_report(self.sample_report).lower())
    def test_no_username(self): self.assertNotIn("username",MOD.render_json_report(self.sample_report).lower())
    def test_no_absolute_path(self): self.assertNotIn(str(ROOT),MOD.render_json_report(self.sample_report))
    def test_no_float_core(self): self.assertFalse(any(isinstance(x,ast.Constant) and isinstance(x.value,float) for x in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))))
    def test_artifact_equipment_id_not_blank(self): self.assertTrue(MOD._selected_id(self.sample_report.document["target_results"][0],"equipment_quantity_min_candidate"))
    def test_artifact_human_id_not_blank(self): self.assertTrue(MOD._selected_id(self.sample_report.document["target_results"][0],"human_min_candidate"))
    def test_report_and_evidence_selected_id_match(self): self.assertEqual(MOD._selected_id(self.sample_report.document["target_results"][0],"equipment_quantity_min_candidate"),self.sample_report.document["target_results"][0]["equipment_quantity_min_candidate"]["candidate"]["candidate"]["candidate_id"])

    # Strict negatives
    def test_invalid_version(self): self.invalid_sweep(lambda x:x.__setitem__("sweep_version",2))
    def test_duplicate_json_key(self): self.assertRaises(MOD.SweepFailure,MOD._reject_duplicate_keys,[("a",1),("a",2)])
    def test_null(self): self.assertRaises(MOD.SweepFailure,MOD._reject_null,None)
    def test_nan(self): self.assertRaises(MOD.SweepFailure,MOD._reject_constant,"NaN")
    def test_infinity(self): self.assertRaises(MOD.SweepFailure,MOD._reject_constant,"Infinity")
    def test_wrong_target_order(self): self.invalid_sweep(lambda x:x["targets"].reverse())
    def test_wrong_range(self): self.invalid_sweep(lambda x:x["ranges"]["weed_rover_counts"].append(7))
    def test_missing_range(self): self.invalid_sweep(lambda x:x["ranges"].pop("charger_counts"))
    def test_duplicate_range(self): self.invalid_sweep(lambda x:x["ranges"]["charger_counts"].append(12))
    def test_raw_count_mismatch(self): self.invalid_sweep(lambda x:x["search_policy"].__setitem__("raw_candidate_count",1))
    def test_invalid_base_plan(self):
        value=copy.deepcopy(self.base);value["plan_version"]=2
        with self.assertRaises(MOD.SweepFailure): MOD.validate_base_model(self.st008,value)
    def test_report_inside_repository(self):
        a=MOD.SweepArguments(ROOT,BASE,SWEEP,ROOT/"x.json",Path(tempfile.gettempdir())/"x.txt")
        with self.assertRaises(MOD.SweepFailure): MOD.validate_arguments(a)
    def test_missing_parent(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=MOD.SweepArguments(ROOT,BASE,SWEEP,p/"missing/x.json",p/"x.txt")
            with self.assertRaises(MOD.SweepFailure): MOD.validate_arguments(a)
    def test_parent_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);f=p/"file";f.write_text("x") ;a=MOD.SweepArguments(ROOT,BASE,SWEEP,f/"x.json",p/"x.txt")
            with self.assertRaises(MOD.SweepFailure): MOD.validate_arguments(a)
    def test_st008_exception(self):
        with self.assertRaises(RuntimeError): MOD.build_report(ROOT,self.base,self.sweep,st008_loader=lambda _:(_ for _ in ()).throw(RuntimeError()))
    def test_candidate_evaluation_exception(self):
        with self.assertRaises(RuntimeError): MOD.build_report(ROOT,self.base,self.sweep,search_engine=lambda *args:(_ for _ in ()).throw(RuntimeError()))
    def test_report_write_failure(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=MOD.SweepArguments(ROOT,BASE,SWEEP,p/"x.json",p/"x.txt")
            with mock.patch.object(MOD,"write_report",side_effect=OSError): self.assertEqual(MOD.run_sweep(a,builder=lambda *args:self.sample_report,write_reports=True).exit_code,7)
    def test_unexpected_internal(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);a=MOD.SweepArguments(ROOT,BASE,SWEEP,p/"x.json",p/"x.txt");r=MOD.run_sweep(a,builder=lambda *args:(_ for _ in ()).throw(RuntimeError("detail")));self.assertEqual(r.exit_code,7);self.assertNotIn("detail",MOD.render_json_report(r))


def _make_range_probe(key, index, expected):
    def test(self): self.assertEqual(self.sweep["ranges"][key][index], expected)
    return test


for _key, _values in MOD.EXPECTED_RANGES.items():
    for _index, _value in enumerate(_values):
        setattr(SeasonalCapacitySweepTests, f"test_range_{_key}_{_index:02d}", _make_range_probe(_key,_index,_value))


def _make_safety_probe(key, expected):
    def test(self): self.assertIs(self.sample_report.document["safety"][key], expected)
    return test


for _key, _value in MOD.safety_document().items():
    setattr(SeasonalCapacitySweepTests, f"test_safety_{_key}", _make_safety_probe(_key,_value))


def _make_candidate_formula_probe(index):
    def test(self):
        c=MOD.Candidate(4,2+(index%5),4+(index%9),2+(index%7),16+4*(index%9),4+2*(index%5),(1000,2000,4000)[index%3],(1,2,4,6)[index%4],(50,100,150,200)[index%4],(0,10,20)[index%3])
        self.assertEqual(c.payload_g,c.cassette_g*c.batch);self.assertEqual(c.attachments,c.broadcast+c.weed+c.high_cut+c.carrier);self.assertEqual(c.common_rovers,max(c.broadcast,c.weed,c.high_cut+c.carrier))
    return test


for _index in range(120):
    setattr(SeasonalCapacitySweepTests, f"test_candidate_formula_probe_{_index:03d}", _make_candidate_formula_probe(_index))


if __name__ == "__main__":
    unittest.main(verbosity=2)
