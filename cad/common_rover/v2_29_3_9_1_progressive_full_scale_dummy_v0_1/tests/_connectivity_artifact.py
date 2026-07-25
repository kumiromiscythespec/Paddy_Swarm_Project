from __future__ import annotations

import os
from pathlib import Path
import tempfile

from final_gate_contract import validate_connectivity_fixture
from generate_connectivity_correction import generate
from tests._artifact import generated_artifact


_TEMPORARY: tempfile.TemporaryDirectory[str] | None = None
_ARTIFACT: Path | None = None


def generated_connectivity_artifact() -> Path:
    global _TEMPORARY, _ARTIFACT
    if _ARTIFACT is not None:
        return _ARTIFACT
    configured = os.environ.get("PFD_CONNECTIVITY_TEST_ARTIFACT")
    if configured:
        candidate = Path(configured).resolve()
        audit = validate_connectivity_fixture(candidate)
        if audit["status"] != "PASS":
            raise RuntimeError(
                "PFD_CONNECTIVITY_FIXTURE_INVALID:"
                + ",".join(audit["blockers"])
            )
        _ARTIFACT = candidate
        return _ARTIFACT

    baseline_configured = os.environ.get(
        "PFD_CONNECTIVITY_BASELINE_ARTIFACT"
    )
    baseline = (
        Path(baseline_configured).resolve()
        if baseline_configured
        else generated_artifact()
    )
    _TEMPORARY = tempfile.TemporaryDirectory(
        prefix="pfd_connectivity_test_artifact_"
    )
    _ARTIFACT = Path(_TEMPORARY.name) / "artifact"
    generate(_ARTIFACT, baseline)
    audit = validate_connectivity_fixture(_ARTIFACT)
    if audit["status"] != "PASS":
        raise RuntimeError(
            "GENERATED_CONNECTIVITY_FIXTURE_INVALID:"
            + ",".join(audit["blockers"])
        )
    return _ARTIFACT
