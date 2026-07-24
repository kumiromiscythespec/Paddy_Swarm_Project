from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
from closed_loop_runner import run_cad_stage, run_static_preflight
from registry_loader import load_registries

STAGES = (
    "preflight", "solid", "holes", "minimum-assembly",
    "render", "package-review", "finalize", "all",
)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=STAGES, default="preflight")
    parser.add_argument("--output", required=True)
    parser.add_argument("--review-receipt")
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parent
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        raise SystemExit("clean output required")
    output.mkdir(parents=True, exist_ok=True)
    registries = load_registries(source)
    preflight = run_static_preflight(registries, source, output)
    if preflight["status"] != "PASS":
        return 30
    if args.stage == "preflight":
        result = {
            "design_analysis_process": "PASS_WITH_HOLD",
            "opening_routing_status": "PASS",
            "cadquery_import_status": (
                "AVAILABLE" if importlib.util.find_spec("cadquery")
                else "UNAVAILABLE"
            ),
            "loop_001_status": (
                "SOURCE_REPAIRED_AWAITING_CADQUERY_EXECUTION"
                if importlib.util.find_spec("cadquery") is None
                else "SOURCE_REPAIRED_READY_FOR_CADQUERY_EXECUTION"
            ),
            "next_loop_eligibility": "BLOCKED",
            "executable_upper_cad_seed": "NONE_NOT_EXECUTED",
        }
        (output / "preflight_status.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 0
    result = run_cad_stage(
        registries, source, output,
        "finalize" if args.stage == "all" else args.stage,
    )
    (output / "cad_stage_status.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result["exit_code"]

if __name__ == "__main__":
    raise SystemExit(main())
