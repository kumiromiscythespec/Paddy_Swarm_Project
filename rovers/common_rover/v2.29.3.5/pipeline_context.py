from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class PipelineContext:
    source_root: Path
    output_root: Path
    requested_stage: str
    active_loop_id: str = "LOOP-001"
    active_part_id: str = "V2292-FPB-RAIL-L"
    active_revision: str = "revA"
    registries: dict = field(default_factory=dict)
    routed_openings: list = field(default_factory=list)
    fastener_instance_set: list = field(default_factory=list)
    reachability_rows: list = field(default_factory=list)
    coordinate_rows: list = field(default_factory=list)
    structural_joints: list = field(default_factory=list)
    required_component_manifest: dict = field(default_factory=dict)
    hard_failure_counts: dict = field(default_factory=dict)
    hold_counts: dict = field(default_factory=dict)
    stage_statuses: dict = field(default_factory=dict)
    actual_part_solid: object | None = None
    last_successful_stage: str = "NONE"

    def record_stage(self, stage, status, details=None):
        self.stage_statuses[stage] = {
            "status": status, "details": details or {},
        }
        if status in {"PASS", "PASS_WITH_HOLD"}:
            self.last_successful_stage = stage

    def ensure_clean_output(self):
        if self.output_root.exists() and any(self.output_root.iterdir()):
            raise RuntimeError(f"clean output required: {self.output_root}")
        self.output_root.mkdir(parents=True, exist_ok=True)
