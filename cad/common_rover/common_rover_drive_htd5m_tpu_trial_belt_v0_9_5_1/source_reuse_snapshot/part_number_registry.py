from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


PART_NUMBER_PATTERN = re.compile(
    r"^PS-(?:DRV|PTO|BLT|CPN|HUB|SPC|TEN|GRD|FLG|GGE|JIG|TPL|FUS|STO)"
    r"-[A-Z0-9-]+-R00$"
)
REVISION = "R00"


@dataclass(frozen=True)
class PartSpec:
    key: str
    part_number: str
    title: str
    family: str
    filename: str
    material: str
    classification: str
    print_target: str
    generated: bool = True

    @property
    def marking_lines(self) -> tuple[str, str]:
        body, revision = self.part_number.rsplit("-", 1)
        tokens = body.split("-")
        split = max(2, len(tokens) - 1)
        first = "-".join(tokens[:split])
        second = "-".join((*tokens[split:], revision))
        if len(first) > 13 and len(tokens) >= 4:
            split -= 1
            first = "-".join(tokens[:split])
            second = "-".join((*tokens[split:], revision))
        return first, second


def _spec(
    key: str,
    number: str,
    title: str,
    family: str,
    *,
    material: str = "PETG",
    classification: str = "LOW-LOAD TEST ONLY",
    print_target: str = "TARGET-P1-FIRST-ARTICLE",
    generated: bool = True,
) -> PartSpec:
    filename = f"{number}_{key}.stl"
    return PartSpec(
        key,
        number,
        title,
        family,
        filename,
        material,
        classification,
        print_target,
        generated,
    )


PULLEY_PARTS = (
    _spec("drive_l_20t_pulley", "PS-DRV-L-20T-R00", "Drive L 20T D-bore pulley", "pulley"),
    _spec("drive_l_60t_pulley", "PS-DRV-L-60T-R00", "Drive L 60T PCD24 pulley", "pulley"),
    _spec("drive_r_20t_pulley", "PS-DRV-R-20T-R00", "Drive R 20T D-bore pulley", "pulley", print_target="TARGET-P3-DUAL-DRIVE"),
    _spec("drive_r_60t_pulley", "PS-DRV-R-60T-R00", "Drive R 60T PCD24 pulley", "pulley", print_target="TARGET-P3-DUAL-DRIVE"),
    _spec("pto_a_20t_pulley", "PS-PTO-A-20T-R00", "PTO A 20T clamp pulley", "pulley", print_target="TARGET-P4-PTO-A"),
    _spec("pto_a_60t_pulley", "PS-PTO-A-60T-R00", "PTO A 60T clamp pulley", "pulley", print_target="TARGET-P4-PTO-A"),
    _spec("pto_b_20t_pulley", "PS-PTO-B-20T-R00", "PTO B 20T clamp pulley", "pulley", print_target="TARGET-P5-PTO-B"),
    _spec("pto_b_60t_pulley", "PS-PTO-B-60T-R00", "PTO B 60T clamp pulley", "pulley", print_target="TARGET-P5-PTO-B"),
)

BELT_PARTS = (
    _spec("drive_l_450_belt", "PS-BLT-DL-450-R00", "Drive L continuous 450-5M-15 belt", "belt", material="TPU 95A", classification="POWERED LOAD HOLD", print_target="TARGET-P2-ONE-DRIVE-PATH"),
    _spec("drive_r_450_belt", "PS-BLT-DR-450-R00", "Drive R continuous 450-5M-15 belt", "belt", material="TPU 95A", classification="POWERED LOAD HOLD", print_target="TARGET-P3-DUAL-DRIVE"),
    _spec("spare_450_belt", "PS-BLT-SP-450-R00", "Spare continuous 450-5M-15 belt", "belt", material="TPU 95A", classification="POWERED LOAD HOLD", print_target="TARGET-P3-DUAL-DRIVE"),
    _spec("tooth_fit_a", "PS-BLT-TF-A-R00", "HTD-5M tooth-fit short A", "belt_coupon", material="TPU 95A", classification="HAND FIT ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("tooth_fit_b", "PS-BLT-TF-B-R00", "HTD-5M tooth-fit short B", "belt_coupon", material="TPU 95A", classification="HAND FIT ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("tooth_fit_c", "PS-BLT-TF-C-R00", "HTD-5M tooth-fit short C", "belt_coupon", material="TPU 95A", classification="HAND FIT ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("bend_fit_short", "PS-BLT-BEND-R00", "20T bend-fit short", "belt_coupon", material="TPU 95A", classification="HAND FIT ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("joiner_fit", "PS-BLT-JOIN-R00", "TPU belt joiner-fit coupon", "belt_coupon", material="TPU 95A", classification="HAND ONLY NEVER POWERED", print_target="TARGET-P0-CALIBRATION"),
    _spec("pto_a_final_belt_hold", "PS-BLT-PA-XXX-R00", "PTO A final belt", "belt", material="TPU 95A", classification="HOLD LENGTH UNKNOWN", print_target="TARGET-P4-PTO-A", generated=False),
    _spec("pto_b_final_belt_hold", "PS-BLT-PB-XXX-R00", "PTO B final belt", "belt", material="TPU 95A", classification="HOLD LENGTH UNKNOWN", print_target="TARGET-P5-PTO-B", generated=False),
)

COUPON_PARTS = tuple(
    _spec(
        f"{kind.lower()}_{variant.lower()}",
        f"PS-CPN-{code}-{variant}-R00",
        f"{title} {variant}",
        "coupon",
        material=material,
        classification="CALIBRATION ONLY",
        print_target="TARGET-P0-CALIBRATION",
    )
    for kind, code, title, material in (
        ("D6", "D6", "phi6 D-shaft bore coupon", "PETG"),
        ("B10", "B10", "phi10 round bore coupon", "PETG"),
        ("T20", "T20", "20T tooth engagement coupon", "PETG"),
        ("T60", "T60", "60T tooth engagement coupon", "PETG"),
    )
    for variant in ("A", "B", "C")
) + (
    _spec("commercial_belt_fit", "PS-CPN-C450-R00", "Commercial 450-5M-15 belt fit coupon", "coupon", classification="CALIBRATION ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("printed_belt_fit", "PS-CPN-PBLT-R00", "Printed TPU belt fit coupon", "coupon", material="PETG", classification="CALIBRATION ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("pcd24_hub_coupon", "PS-CPN-PCD24-R00", "PCD24 4xM4 hub coupon", "coupon", classification="CALIBRATION ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("clamp_insert_coupon", "PS-CPN-INS-R00", "Clamp bolt and insert coupon", "coupon", classification="CALIBRATION ONLY", print_target="TARGET-P0-CALIBRATION"),
    _spec("tpu_thickness_coupon", "PS-CPN-TPUT-R00", "TPU belt thickness coupon", "coupon", material="TPU 95A", classification="CALIBRATION ONLY", print_target="TARGET-P0-CALIBRATION"),
)

HUB_AND_SPACER_PARTS = tuple(
    _spec(
        f"{path.lower()}_hub_adapter",
        f"PS-HUB-{code}-R00",
        f"{path} sacrificial hub adapter",
        "hub_adapter",
        classification="LOW-LOAD TEST ONLY METAL FASTENERS REQUIRED",
        print_target=target,
    )
    for path, code, target in (
        ("DRIVE-L", "DL", "TARGET-P2-ONE-DRIVE-PATH"),
        ("DRIVE-R", "DR", "TARGET-P3-DUAL-DRIVE"),
        ("PTO-A", "PA", "TARGET-P4-PTO-A"),
        ("PTO-B", "PB", "TARGET-P5-PTO-B"),
    )
) + tuple(
    _spec(
        f"{path.lower()}_shaft_spacer",
        f"PS-SPC-{code}-R00",
        f"{path} shaft spacer",
        "spacer",
        classification="FIT TEST ONLY",
        print_target=target,
    )
    for path, code, target in (
        ("DRIVE-L", "DL", "TARGET-P2-ONE-DRIVE-PATH"),
        ("DRIVE-R", "DR", "TARGET-P3-DUAL-DRIVE"),
        ("PTO-A", "PA", "TARGET-P4-PTO-A"),
        ("PTO-B", "PB", "TARGET-P5-PTO-B"),
    )
) + tuple(
    _spec(
        f"{path.lower()}_removable_flange",
        f"PS-FLG-{code}-60-R00",
        f"{path} removable 60T flange",
        "flange",
        classification="LOW-LOAD TEST ONLY",
        print_target=target,
    )
    for path, code, target in (
        ("DRIVE-L", "DL", "TARGET-P2-ONE-DRIVE-PATH"),
        ("DRIVE-R", "DR", "TARGET-P3-DUAL-DRIVE"),
        ("PTO-A", "PA", "TARGET-P4-PTO-A"),
        ("PTO-B", "PB", "TARGET-P5-PTO-B"),
    )
)

TENSIONER_PARTS = tuple(
    _spec(
        f"{path.lower()}_tensioner_slider",
        f"PS-TEN-{code}-R00",
        f"{path} parameterized tensioner guide",
        "tensioner",
        classification="GUIDE ONLY METAL BRACKET CARRIES BELT REACTION",
        print_target=target,
    )
    for path, code, target in (
        ("DRIVE-L", "DL", "TARGET-P1-FIRST-ARTICLE"),
        ("DRIVE-R", "DR", "TARGET-P3-DUAL-DRIVE"),
        ("PTO-A", "PA", "TARGET-P4-PTO-A"),
        ("PTO-B", "PB", "TARGET-P5-PTO-B"),
    )
) + (
    _spec("tension_adjustment_knob", "PS-TEN-KNOB-R00", "Tension adjustment hand knob", "tensioner", classification="HAND ADJUSTMENT ONLY METAL NUT REQUIRED"),
)

GUARD_PARTS = tuple(
    _spec(
        f"{path.lower()}_belt_guard",
        f"PS-GRD-{code}-R00",
        f"{path} temporary belt guard",
        "guard",
        classification="TEMPORARY LOW-SPEED GUARD FINAL MOUNTS HOLD",
        print_target=target,
    )
    for path, code, target in (
        ("DRIVE-L", "DL", "TARGET-P2-ONE-DRIVE-PATH"),
        ("DRIVE-R", "DR", "TARGET-P3-DUAL-DRIVE"),
        ("PTO-A", "PA", "TARGET-P4-PTO-A"),
        ("PTO-B", "PB", "TARGET-P5-PTO-B"),
    )
) + (
    _spec("shaft_end_guard", "PS-GRD-SHAFT-R00", "Shaft end temporary guard", "guard", classification="TEMPORARY LOW-SPEED GUARD"),
)

TOOLING_PARTS = (
    _spec("center_distance_gauge", "PS-GGE-CTR-R00", "112-130 mm center-distance gauge", "tooling", classification="MEASUREMENT ONLY"),
    _spec("pulley_alignment_gauge", "PS-GGE-ALIGN-R00", "Pulley face alignment gauge", "tooling", classification="MEASUREMENT ONLY"),
    _spec("parallelism_gauge", "PS-GGE-PAR-R00", "Shaft parallelism gauge", "tooling", classification="MEASUREMENT ONLY"),
    _spec("motor_slide_template", "PS-TPL-MSLIDE-R00", "Parameterized motor-slide drilling template", "tooling", classification="TRANSFER TEMPLATE VERIFY FRAME BEFORE DRILLING"),
    _spec("bearing_block_template", "PS-TPL-BBLK-R00", "Bearing-block location template", "tooling", classification="TRANSFER TEMPLATE VERIFY AUTHORITY BEFORE DRILLING"),
    _spec("tpu_joining_jig", "PS-JIG-TPUJ-R00", "TPU belt joining jig", "tooling", classification="HAND FIT ONLY NEVER POWERED"),
    _spec("sacrificial_torque_fuse", "PS-FUS-TORQ-R00", "Sacrificial torque fuse candidate", "tooling", classification="PRINTED TEST ONLY POWERED LOAD HOLD"),
    _spec("belt_storage_fixture", "PS-STO-BELT-R00", "Labeled belt storage fixture", "tooling", classification="STORAGE ONLY"),
)

ALL_PARTS: tuple[PartSpec, ...] = (
    PULLEY_PARTS
    + BELT_PARTS
    + COUPON_PARTS
    + HUB_AND_SPACER_PARTS
    + TENSIONER_PARTS
    + GUARD_PARTS
    + TOOLING_PARTS
)
PART_BY_KEY = {part.key: part for part in ALL_PARTS}
PART_BY_NUMBER = {part.part_number: part for part in ALL_PARTS}


def validate_registry(parts: Iterable[PartSpec] = ALL_PARTS) -> dict[str, object]:
    records = tuple(parts)
    numbers = [part.part_number for part in records]
    filenames = [part.filename for part in records]
    malformed = [
        number for number in numbers if not PART_NUMBER_PATTERN.fullmatch(number)
    ]
    duplicate_numbers = sorted(
        {number for number in numbers if numbers.count(number) > 1}
    )
    duplicate_filenames = sorted(
        {name for name in filenames if filenames.count(name) > 1}
    )
    if malformed or duplicate_numbers or duplicate_filenames:
        raise ValueError(
            "INVALID_PART_REGISTRY:"
            f"malformed={malformed};duplicate_numbers={duplicate_numbers};"
            f"duplicate_filenames={duplicate_filenames}"
        )
    return {
        "status": "PASS",
        "part_count": len(records),
        "generated_part_count": sum(part.generated for part in records),
        "unique_part_number_count": len(set(numbers)),
        "revision": REVISION,
    }


validate_registry()
