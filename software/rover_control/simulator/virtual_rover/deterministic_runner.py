from __future__ import annotations

import json
from collections.abc import Iterable
from enum import Enum
from typing import Any

from .model import (
    PROTOCOL_VERSION,
    REPORT_VERSION,
    SIMULATOR_VERSION,
    RuntimeConfig,
    RuntimeInput,
)
from .state_machine import RuntimeStateMachine, snapshot_dict


class VectorClassification(str, Enum):
    RUNTIME_CORE_MAPPING = "runtime_core_mapping"
    UNMAPPED = "unmapped"
    VALIDATOR_ONLY = "validator_only"
    RUNTIME_CONTRACT_REQUIRED = "runtime_contract_required"


RUNTIME_CORE_MAPPING_VECTOR_IDS = frozenset(
    {
        "PV0-VAL-001A",
        "PV0-VAL-001B",
        "PV0-VAL-003",
        "PV0-VAL-004",
        "PV0-VAL-005",
        "PV0-VAL-007",
        "PV0-VAL-011",
        "PV0-VAL-012",
        "PV0-VAL-014L",
        "PV0-VAL-014R",
        "PV0-VAL-015",
        "PV0-VAL-016",
        "PV0-VAL-017",
        "PV0-VAL-018",
        "PV0-VAL-020",
        "PV0-VAL-021",
        "PV0-VAL-022",
        "PV0-VAL-025",
        "PV0-VAL-027",
        "PV0-VAL-028",
        "PV0-VAL-029",
        "PV0-VAL-032",
        "PV0-VAL-033",
        "PV0-VAL-034",
        "PV0-VAL-035",
        "PV0-VAL-036",
    }
)
VALIDATOR_ONLY_VECTOR_IDS = frozenset(
    {
        "PV0-VAL-006",
        "PV0-VAL-008",
        "PV0-VAL-009",
        "PV0-VAL-010",
        "PV0-VAL-013",
        "PV0-VAL-019",
        "PV0-VAL-023",
        "PV0-VAL-024",
        "PV0-VAL-026",
        "PV0-VAL-030",
        "PV0-VAL-031",
    }
)
RUNTIME_CONTRACT_REQUIRED_VECTOR_IDS = frozenset({"PV0-VAL-002"})


def classify_vector_id(vector_id: str) -> VectorClassification:
    if vector_id in RUNTIME_CORE_MAPPING_VECTOR_IDS:
        return VectorClassification.RUNTIME_CORE_MAPPING
    if vector_id in VALIDATOR_ONLY_VECTOR_IDS:
        return VectorClassification.VALIDATOR_ONLY
    if vector_id in RUNTIME_CONTRACT_REQUIRED_VECTOR_IDS:
        return VectorClassification.RUNTIME_CONTRACT_REQUIRED
    return VectorClassification.UNMAPPED


class DeterministicRunner:
    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()

    def run(self, inputs: Iterable[RuntimeInput]) -> dict[str, Any]:
        machine = RuntimeStateMachine(self.config)
        steps = [machine.step(runtime_input).report_dict() for runtime_input in inputs]
        return {
            "report_version": REPORT_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "simulator": "virtual_rover",
            "simulator_version": SIMULATOR_VERSION,
            "profile": self.config.profile.value,
            "real_motor_output_enabled": False,
            "initial_state": "BOOT_SAFE",
            "steps": steps,
            "final_state": snapshot_dict(machine.state),
        }

    def render(self, inputs: Iterable[RuntimeInput]) -> str:
        return render_report(self.run(inputs))


def render_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
