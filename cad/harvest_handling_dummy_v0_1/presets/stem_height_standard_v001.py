"""Three fixed virtual-stem height classes for HHD-V001."""

from __future__ import annotations

from collections import Counter

from ..parameters import HEIGHTS_MM

EXPECTED_HEIGHT_COUNTS: dict[str, int] = {
    "LOW": 8,
    "STANDARD": 10,
    "HIGH": 6,
}


def validate_height_classes(classes: tuple[str, ...]) -> None:
    """Validate class names and the required 8/10/6 distribution."""

    unknown = set(classes) - set(HEIGHTS_MM)
    if unknown:
        raise ValueError(f"unknown height classes: {sorted(unknown)}")
    if Counter(classes) != Counter(EXPECTED_HEIGHT_COUNTS):
        raise ValueError(
            f"height counts must be {EXPECTED_HEIGHT_COUNTS}, got {Counter(classes)}"
        )
