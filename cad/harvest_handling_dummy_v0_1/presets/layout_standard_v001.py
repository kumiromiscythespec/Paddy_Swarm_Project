"""Fixed pseudo-irregular 24-socket layout; no runtime random values."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass

from ..interfaces import validate_direction
from ..parameters import ALLOWED_TILT_ANGLES, ROOT_BASE
from .stem_height_standard_v001 import validate_height_classes


@dataclass(frozen=True)
class LayoutEntry:
    """One authoritative socket position and experimental-state row."""

    socket_id: str
    base_module: str
    x_mm: float
    y_mm: float
    tilt_angle_deg: float
    tilt_direction_deg: float
    height_class: str
    stem_class: str = "UNASSIGNED"
    pre_bend_code: str = "NONE"
    panicle_class: str = "NONE"
    leaf_state: str = "NONE"
    release_group: str = "FIXED"


_COORDINATES: tuple[tuple[float, float], ...] = (
    (-15.0, 15.0),
    (-36.0, 15.0),
    (-15.0, 37.0),
    (-57.0, 15.0),
    (-39.0, 39.0),
    (-60.0, 40.0),
    (15.0, 15.0),
    (36.0, 15.0),
    (57.0, 15.0),
    (15.0, 44.0),
    (39.0, 39.0),
    (60.0, 40.0),
    (-15.0, -15.0),
    (-37.0, -15.0),
    (-15.0, -38.0),
    (-58.0, -15.0),
    (-40.0, -40.0),
    (-61.0, -39.0),
    (15.0, -15.0),
    (37.0, -15.0),
    (15.0, -44.0),
    (40.0, -40.0),
    (61.0, -39.0),
    (15.0, -65.0),
)

_MODULES: tuple[str, ...] = (
    *("A" for _ in range(6)),
    *("B" for _ in range(6)),
    *("C" for _ in range(6)),
    *("D" for _ in range(6)),
)

_TILT_ANGLES: tuple[float, ...] = (
    20.0,
    0.0,
    10.0,
    30.0,
    10.0,
    0.0,
    10.0,
    20.0,
    0.0,
    10.0,
    20.0,
    0.0,
    20.0,
    10.0,
    0.0,
    30.0,
    10.0,
    20.0,
    0.0,
    10.0,
    20.0,
    0.0,
    10.0,
    0.0,
)

_DIRECTIONS: tuple[float, ...] = (
    0.0,
    135.0,
    270.0,
    45.0,
    180.0,
    315.0,
    90.0,
    225.0,
    0.0,
    315.0,
    135.0,
    270.0,
    0.0,
    45.0,
    225.0,
    90.0,
    315.0,
    180.0,
    180.0,
    270.0,
    90.0,
    135.0,
    45.0,
    225.0,
)

_HEIGHT_CLASSES: tuple[str, ...] = (
    "HIGH",
    "LOW",
    "STANDARD",
    "LOW",
    "HIGH",
    "STANDARD",
    "STANDARD",
    "HIGH",
    "LOW",
    "STANDARD",
    "LOW",
    "HIGH",
    "STANDARD",
    "LOW",
    "STANDARD",
    "HIGH",
    "LOW",
    "STANDARD",
    "HIGH",
    "STANDARD",
    "LOW",
    "STANDARD",
    "LOW",
    "STANDARD",
)

LAYOUT_STANDARD_V001: tuple[LayoutEntry, ...] = tuple(
    LayoutEntry(
        socket_id=f"S{index:02d}",
        base_module=_MODULES[index - 1],
        x_mm=_COORDINATES[index - 1][0],
        y_mm=_COORDINATES[index - 1][1],
        tilt_angle_deg=_TILT_ANGLES[index - 1],
        tilt_direction_deg=_DIRECTIONS[index - 1],
        height_class=_HEIGHT_CLASSES[index - 1],
    )
    for index in range(1, 25)
)


def entries_for_module(module: str) -> tuple[LayoutEntry, ...]:
    """Return the six fixed rows for module A, B, C, or D."""

    if module not in {"A", "B", "C", "D"}:
        raise ValueError(f"unknown base module: {module!r}")
    return tuple(
        entry
        for entry in LAYOUT_STANDARD_V001
        if entry.base_module == module
    )


def minimum_center_spacing() -> float:
    """Return the smallest pairwise socket-centre distance."""

    return min(
        math.hypot(left.x_mm - right.x_mm, left.y_mm - right.y_mm)
        for index, left in enumerate(LAYOUT_STANDARD_V001)
        for right in LAYOUT_STANDARD_V001[index + 1 :]
    )


def maximum_radial_diameter() -> float:
    """Return twice the maximum centre radius."""

    return 2.0 * max(
        math.hypot(entry.x_mm, entry.y_mm)
        for entry in LAYOUT_STANDARD_V001
    )


def radial_band_counts() -> dict[str, int]:
    """Count centre radii in the <=45, 45-60, and 60-75 mm bands."""

    counts = {"CENTER_LE_45": 0, "MID_45_TO_60": 0, "OUTER_60_TO_75": 0}
    for entry in LAYOUT_STANDARD_V001:
        radius = math.hypot(entry.x_mm, entry.y_mm)
        if radius <= 45.0:
            counts["CENTER_LE_45"] += 1
        elif radius <= 60.0:
            counts["MID_45_TO_60"] += 1
        elif radius <= 75.0:
            counts["OUTER_60_TO_75"] += 1
        else:
            raise ValueError(f"{entry.socket_id} lies beyond 75 mm radius")
    return counts


def coordinate_set() -> set[tuple[float, float]]:
    """Return the authoritative coordinate set."""

    return {(entry.x_mm, entry.y_mm) for entry in LAYOUT_STANDARD_V001}


def symmetry_matches() -> dict[str, bool]:
    """Report forbidden whole-layout mirror/rotation symmetries."""

    coordinates = coordinate_set()
    return {
        "x_axis": {(x, -y) for x, y in coordinates} == coordinates,
        "y_axis": {(-x, y) for x, y in coordinates} == coordinates,
        "rotation_180": {(-x, -y) for x, y in coordinates} == coordinates,
    }


def rows_as_dicts() -> list[dict[str, object]]:
    """Return serialization-ready rows from the authoritative tuple."""

    return [asdict(entry) for entry in LAYOUT_STANDARD_V001]


def validate_layout() -> None:
    """Validate all fixed-layout quantities, clearances, and asymmetry."""

    entries = LAYOUT_STANDARD_V001
    expected_ids = [f"S{index:02d}" for index in range(1, 25)]
    ids = [entry.socket_id for entry in entries]
    if ids != expected_ids:
        raise ValueError("layout must contain ordered S01-S24 without gaps")
    if len(coordinate_set()) != 24:
        raise ValueError("layout coordinates must be unique")
    if Counter(entry.base_module for entry in entries) != Counter(
        {"A": 6, "B": 6, "C": 6, "D": 6}
    ):
        raise ValueError("each base module must contain exactly six sockets")
    if minimum_center_spacing() + 1.0e-9 < ROOT_BASE.min_socket_spacing:
        raise ValueError("layout centre spacing is below 21 mm")
    if maximum_radial_diameter() > ROOT_BASE.max_layout_diameter:
        raise ValueError("layout exceeds 150 mm maximum diameter")
    if radial_band_counts() != {
        "CENTER_LE_45": 10,
        "MID_45_TO_60": 9,
        "OUTER_60_TO_75": 5,
    }:
        raise ValueError(f"incorrect radial density: {radial_band_counts()}")
    if any(symmetry_matches().values()):
        raise ValueError(f"layout has forbidden symmetry: {symmetry_matches()}")
    if Counter(entry.tilt_angle_deg for entry in entries) != Counter(
        {0.0: 8, 10.0: 8, 20.0: 6, 30.0: 2}
    ):
        raise ValueError("tilt counts must be 8/8/6/2")
    if any(entry.tilt_angle_deg not in ALLOWED_TILT_ANGLES for entry in entries):
        raise ValueError("layout contains unsupported tilt")
    for entry in entries:
        validate_direction(entry.tilt_direction_deg)
    if Counter(entry.tilt_direction_deg for entry in entries) != Counter(
        {direction: 3 for direction in range(0, 360, 45)}
    ):
        raise ValueError("each of eight directions must appear three times")
    validate_height_classes(tuple(entry.height_class for entry in entries))
    for entry in entries:
        if (
            entry.stem_class,
            entry.pre_bend_code,
            entry.panicle_class,
            entry.leaf_state,
            entry.release_group,
        ) != ("UNASSIGNED", "NONE", "NONE", "NONE", "FIXED"):
            raise ValueError(f"{entry.socket_id}: invalid fixed v0.1.0 state")


validate_layout()
