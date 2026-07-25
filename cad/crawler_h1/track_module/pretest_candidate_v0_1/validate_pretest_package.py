from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    contract = json.loads((ROOT / "manifest/pretest_candidate_contract.json").read_text(encoding="utf-8"))
    failures = []
    for part in contract["candidate_parts"]:
        path = ROOT / part["dest_path"]
        if not path.is_file():
            failures.append(f"MISSING:{part['dest_path']}")
            continue
        actual = sha256(path)
        if actual != part["sha256"]:
            failures.append(f"HASH_MISMATCH:{part['dest_path']}:{actual}")
    forbidden = []
    for path in ROOT.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            forbidden.append(path.relative_to(ROOT).as_posix())
        if path.is_file() and path.suffix.lower() in {".pyc", ".pyo"}:
            forbidden.append(path.relative_to(ROOT).as_posix())
    if forbidden:
        failures.extend(f"FORBIDDEN:{p}" for p in forbidden)
    print(json.dumps({
        "status": "PASS" if not failures else "FAIL",
        "candidate_part_count": len(contract["candidate_parts"]),
        "failures": failures,
    }, indent=2))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
