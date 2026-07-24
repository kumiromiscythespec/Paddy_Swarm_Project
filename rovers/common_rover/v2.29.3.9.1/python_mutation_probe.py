from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
import branch_probe

HERE = Path(__file__).resolve().parent
from authority_core import main_gate, validate_scope
from cross_registry_validator import compare_anchor, validate_cross_registry
from post_merge_validator import (
    forbidden_path_present, manifest_exists, post_apply_exit_ok, root_text_valid,
)


def module_proof():
    paths = {}
    for name in ["authority_core", "cross_registry_validator", "post_merge_validator"]:
        module = sys.modules[name]
        path = Path(module.__file__).resolve()
        paths[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return paths


def baseline():
    return {
        "canonical_host_component": "HOST-L", "side": "LEFT",
        "normalized_slot_face": "BOTTOM_SLOT", "semantic_qualifier": "RAIL_BOTTOM_SLOT",
        "host_slot_id": "SLOT-L", "position_mode": "PARAMETERIZED_INTERFACE_ZONE",
        "deprecated_reference": False, "mirror_zone_id": "PAIR",
    }, {
        "host_component": "HOST-L", "side": "LEFT",
        "normalized_slot_face": "BOTTOM_SLOT", "semantic_qualifier": "RAIL_BOTTOM_SLOT",
        "position_mode": "PARAMETERIZED_INTERFACE_ZONE", "mirror_pair": "PAIR",
    }, {
        "host_component": "HOST-L", "slot_id": "SLOT-L", "t_nut_permitted": True,
    }


def run_probe(name):
    anchor, zone, slot = baseline()
    ok = False
    if name == "host":
        anchor["canonical_host_component"] = "WRONG"
        ok = "CROSS_REGISTRY_HOST_MISMATCH" in compare_anchor(anchor, zone, slot)
    elif name == "side":
        anchor["side"] = "RIGHT"
        ok = "CROSS_REGISTRY_SIDE_MISMATCH" in compare_anchor(anchor, zone, slot)
    elif name == "face":
        anchor["normalized_slot_face"] = "TOP_SLOT"
        ok = "CROSS_REGISTRY_SLOT_FACE_MISMATCH" in compare_anchor(anchor, zone, slot)
    elif name == "count":
        result = validate_cross_registry(
            {"body_tslot_anchor_records": []}, {"zones": []}, {"mappings": []},
            {"slots": []}, {"BODY_TSLOT_ANCHOR_COUNT": 60},
        )
        ok = "BODY_TSLOT_ANCHOR_COUNT_MISMATCH" in result["blockers"]
    elif name == "manifest":
        ok = manifest_exists(HERE / "definitely_missing_manifest.json") is False
    elif name == "root":
        ok = root_text_valid("invalid", "v2.29.3.9.1") is False
    elif name == "exit":
        ok = post_apply_exit_ok(1) is False
    elif name == "gate":
        ok = main_gate({"x": {"blockers": ["X"]}})["MAIN_MERGE_READINESS"] == "HOLD"
    elif name == "scope":
        with (HERE / "fixed_body_dimension_authority.json").open(encoding="utf-8") as fh:
            value = json.load(fh)
        value["current_dimensions"]["CBOX"]["X"] = 131
        temp = HERE / "_probe_fixed_body.json"
        original = HERE / "fixed_body_dimension_authority.json"
        backup = original.read_bytes()
        try:
            original.write_text(json.dumps(value), encoding="utf-8")
            ok = validate_scope(HERE)["CORRECTION_SCOPE_VIOLATION_COUNT"] > 0
        finally:
            original.write_bytes(backup)
    elif name == "forbidden":
        ok = forbidden_path_present(["cad/dummy_panicle_v0_1/x"], ["cad/dummy_panicle_v0_1/"])
    payload = {
        "probe": name, "passed": bool(ok), "modules": module_proof(),
        "coverage": branch_probe.snapshot(),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run_probe(sys.argv[1]))
