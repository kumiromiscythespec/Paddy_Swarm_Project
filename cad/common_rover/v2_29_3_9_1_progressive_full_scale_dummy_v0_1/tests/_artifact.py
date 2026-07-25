from __future__ import annotations

import tempfile
import os
from pathlib import Path

from final_gate_contract import validate_base_fixture
from generate_dummy_kit import generate


_TEMPORARY: tempfile.TemporaryDirectory[str] | None = None
_ARTIFACT: Path | None = None


def generated_artifact() -> Path:
    global _TEMPORARY, _ARTIFACT
    if _ARTIFACT is None:
        configured = os.environ.get("PFD_TEST_ARTIFACT")
        if configured:
            candidate = Path(configured).resolve()
            audit = validate_base_fixture(candidate)
            if audit["status"] != "PASS":
                raise RuntimeError(
                    "PFD_BASE_FIXTURE_INVALID:"
                    + ",".join(audit["blockers"])
                )
            _ARTIFACT = candidate
            return _ARTIFACT
        _TEMPORARY = tempfile.TemporaryDirectory(
            prefix="pfd_v01_test_artifact_"
        )
        _ARTIFACT = Path(_TEMPORARY.name) / "artifact"
        generate(_ARTIFACT)
        audit = validate_base_fixture(_ARTIFACT)
        if audit["status"] != "PASS":
            raise RuntimeError(
                "GENERATED_BASE_FIXTURE_INVALID:"
                + ",".join(audit["blockers"])
            )
    return _ARTIFACT
