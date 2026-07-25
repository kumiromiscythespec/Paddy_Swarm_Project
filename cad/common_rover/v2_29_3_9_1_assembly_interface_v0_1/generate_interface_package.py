from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
import tempfile


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_adapter import canonical_json, find_repository_root, load_context
from coupon_geometry import export_coupons, replay_coupon_exports
from svg_renderer import render_all
from validate_interfaces import (
    build_complete_manifest,
    deterministic_replay_report,
    validate_full,
)


def _external_output(requested: Path | None) -> Path:
    root = find_repository_root().resolve()
    output = (
        requested.resolve()
        if requested is not None
        else Path(
            tempfile.mkdtemp(
                prefix="common_rover_v229391_assembly_interface_v0_1_"
            )
        ).resolve()
    )
    if output == root or root in output.parents:
        raise ValueError("OUTPUT_DIRECTORY_MUST_BE_OUTSIDE_REPOSITORY")
    output.mkdir(parents=True, exist_ok=True)
    return output


def _connection_matrix(path: Path, manifest: dict) -> None:
    fields = [
        "interface_id",
        "connected_components",
        "primary_secondary",
        "function_classification",
        "assembly_direction",
        "removal_direction",
        "fastener_candidate",
        "visible_confirmation_point",
        "positive_stop",
        "anti_rotation_feature",
        "dirt_water_escape",
        "failure_mode",
        "human_intervention_method",
        "authority_source",
        "unresolved_values",
        "manufacturing_geometry_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in manifest["interfaces"]:
            row = dict(record)
            for field in (
                "connected_components",
                "authority_source",
                "unresolved_values",
            ):
                row[field] = " | ".join(row[field])
            writer.writerow({field: row[field] for field in fields})


def _assembly_markdown(manifest: dict) -> str:
    lines = [
        "# Assembly Interface v0.1 — assembly steps",
        "",
        "> NOT MANUFACTURING APPROVED. Use only for concept review and fit-test planning.",
        "",
        "## Assembly",
        "",
    ]
    for step in manifest["assembly_sequence"]:
        lines.extend(
            [
                f"{step['step']}. **{step['action']}**",
                (
                    f"   - Interface: {', '.join(step['interfaces'])}; "
                    f"tool: {step['tool']}."
                ),
                f"   - VERIFY: {step['verify']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Disassembly",
            "",
            "Disassemble in exact reverse order. Confirm the released state before moving the next load-bearing module.",
            "",
        ]
    )
    for step in manifest["disassembly_sequence"]:
        lines.extend(
            [
                f"{step['step']}. {step['action']}",
                f"   - {step['verify']}.",
                "",
            ]
        )
    field = manifest["field_service_evaluation"]
    lines.extend(
        [
            "## Mud-packed field service evaluation",
            "",
            f"- Status: **{field['status']}**.",
            f"- Glove access: {field['glove_access']}.",
            f"- Hidden fasteners: {field['hidden_fasteners']}.",
            f"- Pin head visible: {field['pin_head_visible']}.",
            f"- R-pin visible: {field['r_pin_visible']}.",
            f"- Tools: {', '.join(field['tools'])}.",
            f"- HOLD: {field['hold']}",
            "",
            "## Battery cassette reserved sequence",
            "",
        ]
    )
    for index, step in enumerate(
        manifest["battery_cassette_reservation"]["sequence"], start=1
    ):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "The connector carries no structural load. Shuttle selection and all electrical implementation remain HOLD.",
            "",
        ]
    )
    return "\n".join(lines)


def _unresolved_markdown(manifest: dict) -> str:
    lines = [
        "# Unresolved dimensions and decisions",
        "",
        "> Every item below remains HOLD. No value is silently converted into manufacturing geometry.",
        "",
    ]
    for record in manifest["interfaces"]:
        lines.append(f"## {record['interface_id']}")
        lines.append("")
        for value in record["unresolved_values"]:
            lines.append(f"- {value}")
        lines.extend(
            [
                (
                    "- Manufacturing geometry status: "
                    f"`{record['manufacturing_geometry_status']}`."
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Architecture-level HOLDs",
            "",
            "- Rear BBOX support hardpoints, member section, stiffness, frame tie, and implement clearance.",
            "- Lower-frame cradle section and its registered structural connection.",
            "- CBOX/BBOX metal clamp geometry, fastener grade, corrosion protection, and torque.",
            "- Float tongue bearing length, printed material strength, metal pin grade, edge distances, and R-pin specification.",
            "- Battery seat, primary latch, safety latch, sensor set, connector shuttle location, sealing, and electrical sequencing hardware.",
            "- Waterproof, structural, electrical, thermal, manufacturing, purchase, and field-deployment approvals.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the external Assembly Interface v0.1 package."
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--skip-coupons",
        action="store_true",
        help="Development-only: do not export fit-test STLs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = _external_output(args.output_dir)
    context = load_context()
    manifest = build_complete_manifest(context)
    first_render = render_all(
        manifest,
        manifest["load_paths"],
        manifest["assembly_sequence"],
        context,
    )
    replay_render = render_all(
        manifest,
        manifest["load_paths"],
        manifest["assembly_sequence"],
        context,
    )
    for filename, payload in first_render.items():
        (output / filename).write_bytes(payload)
    (output / "interface_manifest.json").write_text(
        canonical_json(manifest), encoding="utf-8", newline="\n"
    )
    _connection_matrix(output / "connection_matrix.csv", manifest)
    (output / "assembly_steps.md").write_text(
        _assembly_markdown(manifest), encoding="utf-8", newline="\n"
    )
    (output / "unresolved_dimensions.md").write_text(
        _unresolved_markdown(manifest), encoding="utf-8", newline="\n"
    )
    coupon_replay = None
    if not args.skip_coupons:
        export_coupons(output)
        coupon_replay = replay_coupon_exports(output)
    replay = deterministic_replay_report(
        manifest, first_render, replay_render, coupon_replay
    )
    (output / "deterministic_replay_report.json").write_text(
        canonical_json(replay), encoding="utf-8", newline="\n"
    )
    report = validate_full(
        context,
        manifest,
        first_render,
        replay_render,
        output_directory=None if args.skip_coupons else output,
    )
    (output / "interface_validation.json").write_text(
        canonical_json(report), encoding="utf-8", newline="\n"
    )
    sys.stdout.write(canonical_json(report))
    sys.stdout.write(f"OUTPUT_DIRECTORY={output}\n")
    return (
        0
        if report["ASSEMBLY_INTERFACE_V0_1_STATUS"] == "PASS_WITH_HOLD"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
