"""Documentation contract for Common Rover electrical hardware authority V001."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
REPO = LANE.parents[3]
LANE_REL = "cad/common_rover/physical_authority/common_rover_electrical_hardware_physical_authority_v001/"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_DIRTY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}
EXPECTED_OUTSIDE_UNTRACKED_COUNT = 4133
EXPECTED_OUTSIDE_UNTRACKED_DIGEST = "22d0f97b11ab4df86e0f60b61d2c169709233fe08b0d0ce89ce6636a75b02a3f"
EXPECTED_AUTHORITY_SHA = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
ALLOWED_CLASSES = {
    "PHYSICAL_DIRECT",
    "PHYSICAL_FIT_RESULT",
    "DATASHEET_AUTHORITY",
    "PURCHASE_RECORD",
    "DESIGN_SERVICE_REQUIREMENT",
    "UNVERIFIED_HISTORICAL",
    "MEASUREMENT_PENDING",
    "UNKNOWN_REQUIRES_SOURCE_CONFIRMATION",
}


def run_git(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outside_untracked_digest(paths: list[str]) -> str:
    # The baseline was captured by Windows PowerShell Sort-Object.  Reuse that
    # collation contract rather than comparing it with Python's code-point sort.
    assert paths
    repo_ps = str(REPO).replace("'", "''")
    script = rf"""
$ErrorActionPreference='Stop'
$repo='{repo_ps}'
$laneRel='{LANE_REL}'
$items=@(git -C $repo ls-files --others --exclude-standard | Where-Object {{ $_ -notlike "$laneRel*" }})
$sha=[System.Security.Cryptography.SHA256]::Create()
$lines=New-Object System.Collections.Generic.List[string]
foreach($rel in ($items | Sort-Object)){{
  $abs=Join-Path $repo $rel
  if(Test-Path -LiteralPath $abs -PathType Leaf){{
    $h=(Get-FileHash -LiteralPath $abs -Algorithm SHA256).Hash.ToLower()
    $lines.Add(($rel.Replace('\','/') + [char]0 + $h))
  }}
}}
$bytes=[System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLower()
"""
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=REPO, check=True, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip().splitlines()[-1]


checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))
    print(f"{name}: {'PASS' if condition else 'FAIL'}")


data = json.loads((LANE / "electrical_hardware_authority.json").read_text(encoding="utf-8"))
records = {row["record_id"]: row for row in data["trace_records"]}
inventory = list(csv.DictReader((LANE / "electronics_inventory.csv").open(encoding="utf-8", newline="")))
inventory_ids = {row["item_id"] for row in inventory}

check("001_repository", Path(run_git("rev-parse", "--show-toplevel")[0]).resolve() == REPO.resolve())
check("002_branch", run_git("branch", "--show-current") == [EXPECTED_BRANCH])
check("003_head", run_git("rev-parse", "HEAD") == [EXPECTED_HEAD])
check("004_staged_zero", run_git("diff", "--cached", "--name-only") == [])
check("005_tracked_dirty_unchanged", set(run_git("diff", "--name-only")) == EXPECTED_DIRTY)
check("006_authority_sha", all(file_sha(REPO / p) == h for p, h in EXPECTED_AUTHORITY_SHA.items()))

untracked = run_git("ls-files", "--others", "--exclude-standard")
outside = [p for p in untracked if not p.startswith(LANE_REL)]
lane_untracked = [p for p in untracked if p.startswith(LANE_REL)]
check("007_outside_untracked_count", len(outside) == EXPECTED_OUTSIDE_UNTRACKED_COUNT)
check("008_outside_untracked_bytes", outside_untracked_digest(untracked) == EXPECTED_OUTSIDE_UNTRACKED_DIGEST)
check("009_lane_all_untracked", len(lane_untracked) == 11 and not run_git("ls-files", LANE_REL))

required_trace = {"value", "unit", "source_class", "source_location", "source_date_if_known", "confidence", "notes"}
check("010_trace_schema", all(required_trace <= set(row) for row in records.values()))
check("011_source_classes", all(row["source_class"] in ALLOWED_CLASSES for row in records.values()))
check("012_battery_body", records["BAT-BODY-001"]["value"] == [150.9, 99.4, 92.5] and records["BAT-BODY-001"]["source_class"] == "PHYSICAL_DIRECT")
check("013_battery_mass", records["BAT-MASS-001"]["value"] == 1.2 and records["BAT-MASS-001"]["source_class"] == "PHYSICAL_DIRECT")
check("014_battery_terminals", [records[k]["value"] for k in ("BAT-TAB-W-001", "BAT-TAB-T-001", "BAT-RECEPTACLE-W-001", "BAT-TERM-Z-001")] == [6.3, 0.7, 10.6, 99.4])
check("015_passage", records["BAT-PASSAGE-001"]["value"] == 108.0 and records["BAT-PASSAGE-001"]["source_class"] == "PHYSICAL_FIT_RESULT" and "90.7" in records["BAT-PASSAGE-001"]["notes"])
check("016_esp32", records["ESP32-BODY-001"]["value"] == [56.8, 28.2, 12.9] and records["ESP32-BODY-001"]["source_class"] == "PHYSICAL_DIRECT")
check("017_md10c_datasheet", records["MD10C-PLAN-001"]["value"] == [75.0, 43.0] and records["MD10C-PLAN-001"]["source_class"] == "DATASHEET_AUTHORITY")
check("018_md10c_physical_pending", records["MD10C-PHYSICAL-XY-001"]["value"] is None and records["MD10C-HEIGHT-001"]["value"] is None)
check("019_md10c_holes_not_released", records["MD10C-HOLES-001"]["source_class"] == "UNVERIFIED_HISTORICAL" and records["MD10C-HOLES-001"]["cad_use"] == "HOLD_SOURCE_CONFIRMATION")
check("020_cable_9p6_physical", records["CABLE-OD-001"]["value"] == 9.6 and records["CABLE-OD-001"]["source_class"] == "PHYSICAL_DIRECT")
check("021_gland_14p9", records["GLAND-THREAD-001"]["value"] == 14.9 and records["GLAND-THREAD-001"]["source_class"] == "PHYSICAL_DIRECT")
check("022_2pnct_purchase", records["2PNCT-PURCHASE-001"]["source_class"] == "PURCHASE_RECORD" and "3 m" in records["2PNCT-PURCHASE-001"]["value"])
check("023_2pnct_od_pending", records["2PNCT-OD-001"]["value"] is None and records["2PNCT-OD-001"]["source_class"] == "MEASUREMENT_PENDING")
check("024_no_cable_identity_merge", records["CABLE-OD-001"]["item_id"] != records["2PNCT-OD-001"]["item_id"] and "not copied" in records["2PNCT-OD-001"]["notes"])
check("025_service_900_design_only", records["SERVICE-CABLE-001"]["value"] == 900.0 and records["SERVICE-CABLE-001"]["source_class"] == "DESIGN_SERVICE_REQUIREMENT")
check("026_cbox_current", records["CBOX-BODY-001"]["value"] == [150.0, 246.0, 80.0] and records["CBOX-BODY-001"]["source_class"] == "PHYSICAL_DIRECT")
check("027_inventory_minimum", {"BAT-001", "DRIVER-001", "MCU-001", "DCDC-001", "ESTOP-001", "RELAY-001", "FUSE-HOLDER-001", "FUSE-5A-001", "CONN-XT60-001", "WIRE-001", "CRIMP-001", "CAP-001", "GLAND-001"} <= inventory_ids)
check("028_conflicts_recorded", {row["id"] for row in data["conflicts_and_separations"]} >= {"BATTERY_VS_CASSETTE", "OLD_VS_CURRENT_CBOX", "CABLE_IDENTITY", "SERVICE_LENGTH_CLASSIFICATION"})

manifest = [line.strip() for line in (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
actual = sorted(str(path.relative_to(LANE)).replace("\\", "/") for path in LANE.rglob("*") if path.is_file())
check("029_exact_manifest", sorted(manifest) == actual)
check("030_no_cad", not any(path.suffix.lower() in {".step", ".stp", ".stl", ".dxf", ".fcstd"} for path in LANE.rglob("*")))
check("031_status", data["status"] == ["DOCUMENTATION_COMPLETE", "ELECTRICAL_HARDWARE_AUTHORITY_RECORDED", "PHYSICAL_GAPS_REMAIN"])

failed = [name for name, passed in checks if not passed]
print(f"TOTAL: {len(checks) - len(failed)}/{len(checks)} PASS")
if failed:
    print("FAILED: " + ", ".join(failed))
    sys.exit(1)
