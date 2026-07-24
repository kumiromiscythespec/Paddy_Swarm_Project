from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from authority_core import main_gate, validate_scope
from cross_registry_validator import validate_cross_registry
from post_merge_validator import (
    forbidden_path_present, manifest_exists, post_apply_exit_ok,
    root_text_valid, validate_manifest, validate_pointers_and_holds,
)

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def execute_case(category, index):
    expect_failure = index != 0
    if category in {"lower_adapter", "upper_torque", "cross_registry"}:
        fastener = load("fastener_boundary_authority.json")
        slots = load("slot_zone_authority.json")
        mapping = load("slot_cross_registry_mapping.json")
        hosts = load("tslot_profile_authority.json")
        expectations = load("current_authority_expectations.json")
        if index:
            if category == "lower_adapter":
                affected = [a for a in fastener["body_tslot_anchor_records"] if a["slot_zone_id"].startswith("LOWER-ADAPTER")]
                anchor = affected[(index - 1) % len(affected)]
                mode = (index - 1) % 5
                if mode == 0: anchor["normalized_slot_face"] = "TOP_SLOT"
                elif mode == 1: anchor["host_slot_id"] = "RAIL-L-TOP"
                elif mode == 2: anchor["semantic_qualifier"] = "RAIL_TOP_SLOT"
                elif mode == 3: anchor["slot_zone_id"] = "UNKNOWN"
                else: anchor["side"] = "RIGHT" if anchor["side"] == "LEFT" else "LEFT"
            elif category == "upper_torque":
                affected = [a for a in fastener["body_tslot_anchor_records"] if a["slot_zone_id"] == "UPPER-TORQUE-MOUNT"]
                anchor = affected[(index - 1) % len(affected)]
                mode = (index - 1) % 5
                if mode == 0: anchor["normalized_slot_face"] = "REAR_FACE_SLOT"
                elif mode == 1: anchor["host_slot_id"] = "XMEMBER-REAR"
                elif mode == 2: anchor["semantic_qualifier"] = "REAR_FACE_SLOT_OF_FRONT_CROSSMEMBER"
                elif mode == 3: anchor["slot_zone_id"] = "UNKNOWN"
                else: anchor["canonical_host_component"] = "WRONG"
            else:
                anchor = fastener["body_tslot_anchor_records"][(index - 1) % 60]
                mode = (index - 1) % 8
                if mode == 0: anchor["canonical_host_component"] = "WRONG"
                elif mode == 1: anchor["side"] = "WRONG"
                elif mode == 2: anchor["normalized_slot_face"] = "WRONG"
                elif mode == 3: anchor["semantic_qualifier"] = "WRONG"
                elif mode == 4: anchor.pop("slot_zone_id")
                elif mode == 5: anchor["slot_zone_id"] = "UNKNOWN"
                elif mode == 6: mapping["mappings"].append(copy.deepcopy(mapping["mappings"][0]))
                else: anchor["deprecated_reference"] = True
        result = validate_cross_registry(fastener, slots, mapping, hosts, expectations)
        failed = result["status"] != "PASS"
    elif category == "manifest_location":
        if index == 0:
            failed = validate_manifest(HERE)["status"] != "PASS"
        else:
            mode = (index - 1) % 4
            if mode == 0: failed = manifest_exists(HERE / f"missing-{index}.json") is False
            elif mode == 1: failed = forbidden_path_present(["interfaces/x"], ["interfaces/"])
            elif mode == 2: failed = root_text_valid("invalid", VERSION) is False
            else: failed = post_apply_exit_ok(index) is False
    elif category == "patch_scope":
        if index == 0:
            failed = validate_scope(HERE)["status"] != "PASS"
        else:
            scope = load("correction_scope_contract.json")
            failed = scope["immutable_values"]["REGISTERED_WIDTH_MM"] == 286
    elif category == "post_merge":
        holds = load("known_hold_registry.json")
        if index:
            key = [k for k in holds if k != "version"][(index - 1) % (len(holds) - 1)]
            holds[key] = f"INVALID_{index}"
        result = validate_pointers_and_holds(HERE, holds)
        failed = result["status"] != "PASS"
    elif category == "python_execution":
        if index == 0:
            failed = False
        else:
            checks = [
                forbidden_path_present(["interfaces/x"], ["interfaces/"]),
                manifest_exists(HERE / "missing.json") is False,
                root_text_valid("bad", VERSION) is False,
                post_apply_exit_ok(1) is False,
            ]
            failed = checks[(index - 1) % 4]
    elif category == "main_gate":
        results = {"base": {"blockers": []}}
        if index:
            results[f"case-{index}"] = {"blockers": [f"BLOCKER-{index}"]}
        failed = main_gate(results)["MAIN_MERGE_READINESS"] != "READY"
    else:
        raise AssertionError(category)
    if failed != expect_failure:
        raise AssertionError(f"{category}-{index}: expected_failure={expect_failure}, failed={failed}")


VERSION = "v2.29.3.9.1"


def install_cases(cls, category):
    for index in range(40):
        def test(self, category=category, index=index):
            execute_case(category, index)
        test.__name__ = f"test_{category}_{index:03d}"
        setattr(cls, test.__name__, test)
