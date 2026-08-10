from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


KIT_VERSION = "v0.1"
ROVER_VERSION = "v2.29.3.9.1"
PROFILE = "HTD-5M"
PITCH_MM = 5.0
BELT_WIDTH_MM = 15.0
A1_BUILD_PLATE_MM = (256.0, 256.0, 256.0)
EXPECTED_BRANCH = (
    "cad/common-rover-v2.29.3.9.1-printed-drive-pto-kit-v0.1"
)
EXPECTED_HEAD = "e6ba477e7f0e14674d4266b0bc91cd86cd6ec8b8"
DRIVE_BELT_PITCH_LENGTH_MM = 450.0
DRIVE_BELT_TEETH = 90
DRIVE_CENTER_DISTANCE_NOMINAL_MM = 121.0
DRIVE_CENTER_DISTANCE_RANGE_MM = (112.0, 130.0)
MINIMUM_ADJUSTMENT_STROKE_MM = 12.0
PTO_INPUT_STATUS = "CALIBRATION_PENDING"
MEASUREMENT_STATUS = "CALIBRATION_PENDING"
SOURCE_REUSE_RESULT = "NOT_FOUND_IN_BASE"
SOURCE_REUSE_PROVENANCE = {
    "htd_geometry": "NOT_FOUND_IN_BASE",
    "physical_marking_pattern": (
        "Behavioral provenance: "
        "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/"
        "coupon_geometry.py::COMMON_ENGRAVED_PART_NUMBER_V1"
    ),
    "baseline_modification": "NONE",
}


def pitch_diameter_mm(teeth: int, pitch_mm: float = PITCH_MM) -> float:
    if teeth <= 0 or pitch_mm <= 0.0:
        raise ValueError("POSITIVE_TEETH_AND_PITCH_REQUIRED")
    return teeth * pitch_mm / math.pi


def belt_tooth_count(pitch_length_mm: float, pitch_mm: float = PITCH_MM) -> int:
    raw = pitch_length_mm / pitch_mm
    rounded = round(raw)
    if not math.isclose(raw, rounded, abs_tol=1.0e-9, rel_tol=0.0):
        raise ValueError("BELT_LENGTH_NOT_INTEGER_PITCH")
    return int(rounded)


@dataclass(frozen=True)
class PulleyPath:
    path_id: str
    small_bore_type: str
    small_bore_nominal_mm: float
    large_bore_type: str
    large_bore_nominal_mm: float
    final_belt_pitch_length_mm: float | None
    final_belt_status: str
    notes: str


PATHS: tuple[PulleyPath, ...] = (
    PulleyPath(
        "DRIVE-L",
        "D_SHAFT",
        6.0,
        "ROUND_PCD24_4XM4",
        10.0,
        DRIVE_BELT_PITCH_LENGTH_MM,
        "CANDIDATE",
        "JGB37-520 output to metal-supported phi10 output shaft",
    ),
    PulleyPath(
        "DRIVE-R",
        "D_SHAFT",
        6.0,
        "ROUND_PCD24_4XM4",
        10.0,
        DRIVE_BELT_PITCH_LENGTH_MM,
        "CANDIDATE",
        "Mirrored quantity; physically unique part numbers",
    ),
    PulleyPath(
        "PTO-A",
        "ROUND_SPLIT_CLAMP",
        10.0,
        "ROUND_SPLIT_CLAMP",
        10.0,
        None,
        "HOLD",
        "Shaft diameter, usable shaft length, and center distance unconfirmed",
    ),
    PulleyPath(
        "PTO-B",
        "ROUND_SPLIT_CLAMP",
        10.0,
        "ROUND_SPLIT_CLAMP",
        10.0,
        None,
        "HOLD",
        "Shaft diameter, usable shaft length, and center distance unconfirmed",
    ),
)

D6_BORE_COMPENSATION_MM = (-0.10, 0.00, 0.10)
B10_BORE_COMPENSATION_MM = (-0.12, 0.00, 0.12)
TOOTH_COMPENSATION_MM = (-0.12, 0.00, 0.12)
TPU_THICKNESS_CANDIDATES_MM = (1.8, 2.0, 2.2)


def require_confirmed_pto_belt(
    path_id: str,
    center_distance_mm: float | None,
    usable_shaft_length_mm: float | None,
    shaft_diameter_mm: float | None,
) -> None:
    if path_id not in {"PTO-A", "PTO-B"}:
        raise ValueError("GENERIC_UNKNOWN_PTO_PATH_REJECTED")
    values = (
        center_distance_mm,
        usable_shaft_length_mm,
        shaft_diameter_mm,
    )
    if any(value is None or value <= 0.0 for value in values):
        raise ValueError("UNKNOWN_PTO_BELT_LENGTH_INFERENCE_REJECTED")


def require_powered_approval(
    *,
    belt_kind: str,
    coupon_result: str | None,
    requested_stage: str,
) -> None:
    if belt_kind == "JOINER-FIT" and requested_stage.startswith("POWERED"):
        raise ValueError("JOINER_BELT_POWERED_APPROVAL_REJECTED")
    if requested_stage.startswith("POWERED") and coupon_result != "PASS":
        raise ValueError("POWERED_APPROVAL_WITHOUT_COUPON_PASS_REJECTED")
    if requested_stage in {"POWERED_LOADED", "FIELD_USE"}:
        raise ValueError(f"{requested_stage}_HOLD")


def contract_dict() -> dict[str, Any]:
    return {
        "schema": "PS_COMMON_ROVER_PRINTED_DRIVE_PTO_CONTRACT_V0_1",
        "kit_version": KIT_VERSION,
        "rover_version": ROVER_VERSION,
        "profile": PROFILE,
        "pitch_mm": PITCH_MM,
        "belt_width_mm": BELT_WIDTH_MM,
        "pulley_pitch_diameter_mm": {
            "20T": pitch_diameter_mm(20),
            "60T": pitch_diameter_mm(60),
        },
        "reduction_ratio": 3.0,
        "drive_motor": {
            "model": "JGB37-520",
            "voltage_v": 12,
            "rated_output_rpm": 60,
            "output_shaft": "phi6 D-shaft",
            "belt_reaction_rule": (
                "Motor output shaft must not be the sole belt-reaction support"
            ),
        },
        "drive_belt": {
            "designation": "450-5M-15",
            "pitch_length_mm": DRIVE_BELT_PITCH_LENGTH_MM,
            "teeth": DRIVE_BELT_TEETH,
            "nominal_center_distance_mm": DRIVE_CENTER_DISTANCE_NOMINAL_MM,
            "adjustment_range_mm": DRIVE_CENTER_DISTANCE_RANGE_MM,
            "minimum_adjustment_stroke_mm": MINIMUM_ADJUSTMENT_STROKE_MM,
        },
        "paths": [asdict(path) for path in PATHS],
        "pto_measurement_status": PTO_INPUT_STATUS,
        "calibration_measurement_status": MEASUREMENT_STATUS,
        "source_reuse": {
            "result": SOURCE_REUSE_RESULT,
            **SOURCE_REUSE_PROVENANCE,
        },
        "approvals": {
            "hand_fit": "COUPON_PASS_REQUIRED",
            "powered_no_load": "HOLD_STAGED_APPROVAL_REQUIRED",
            "powered_loaded": "HOLD",
            "field_use": "HOLD",
            "mud_test": "HOLD",
            "waterproof": "HOLD",
            "unmanned_operation": "HOLD",
            "production": "HOLD",
        },
    }
