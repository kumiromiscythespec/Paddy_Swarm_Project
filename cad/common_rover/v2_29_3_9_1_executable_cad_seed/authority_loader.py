from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence


AUTHORITY_RELATIVE = Path("rovers/common_rover/v2.29.3.9.1")
LINEAR_TOLERANCE_MM = 1.0e-6
INTERSECTION_VOLUME_TOLERANCE_MM3 = 1.0e-9
COMPONENT_IDS = (
    "V22939-FPB-RAIL-L",
    "V22939-FPB-RAIL-R",
    "V22939-FPB-FRONT-XMEMBER",
    "V22939-CBOX",
    "V22939-BBOX",
    "V22939-BATTERY-CASSETTE",
)
SOURCE_FILES = (
    "coordinate_authority.json",
    "body_frame_authority.json",
    "front_crossmember_authority.json",
    "fixed_body_dimension_authority.json",
    "hardware_envelope_registry.json",
    "operational_width_contract.json",
    "known_hold_registry.json",
)


class AuthorityError(RuntimeError):
    def __init__(self, blockers: str | Iterable[str]):
        values = (blockers,) if isinstance(blockers, str) else tuple(blockers)
        self.blockers = tuple(sorted(set(values)))
        super().__init__(";".join(self.blockers))


def _tuple3(values: Iterable[float]) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3:
        raise AuthorityError(f"expected XYZ triple, received {result!r}")
    return result


@dataclass(frozen=True)
class Envelope:
    component_id: str
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    source_path: str
    source_revision: str
    dimension_status: str

    @property
    def dimensions(self) -> tuple[float, float, float]:
        return tuple(
            self.maximum[index] - self.minimum[index] for index in range(3)
        )

    @property
    def center(self) -> tuple[float, float, float]:
        return tuple(
            (self.maximum[index] + self.minimum[index]) / 2.0
            for index in range(3)
        )

    def with_bounds(
        self,
        minimum: Iterable[float] | None = None,
        maximum: Iterable[float] | None = None,
    ) -> "Envelope":
        return replace(
            self,
            minimum=_tuple3(minimum) if minimum is not None else self.minimum,
            maximum=_tuple3(maximum) if maximum is not None else self.maximum,
        )

    def translated(self, delta: Iterable[float]) -> "Envelope":
        vector = _tuple3(delta)
        return self.with_bounds(
            tuple(self.minimum[index] + vector[index] for index in range(3)),
            tuple(self.maximum[index] + vector[index] for index in range(3)),
        )


@dataclass(frozen=True)
class SourceRecord:
    relative_path: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class AuthorityParameters:
    version: str
    units: str
    axes: tuple[tuple[str, str, str], ...]
    components: tuple[Envelope, ...]
    front_datum_y_mm: float
    bare_frame_width_mm: float
    rail_center_separation_mm: float
    core_length_mm: float
    registered_interface_width_mm: float
    operational_hard_limit_mm: float
    linear_tolerance_mm: float
    intersection_volume_tolerance_mm3: float
    battery_placement_status: str
    source_records: tuple[SourceRecord, ...]
    release_holds: tuple[tuple[str, str], ...]

    def component(self, component_id: str) -> Envelope:
        for component in self.components:
            if component.component_id == component_id:
                return component
        raise KeyError(component_id)

    def with_component(self, replacement: Envelope) -> "AuthorityParameters":
        if replacement.component_id not in {
            component.component_id for component in self.components
        }:
            raise KeyError(replacement.component_id)
        return replace(
            self,
            components=tuple(
                replacement
                if component.component_id == replacement.component_id
                else component
                for component in self.components
            ),
        )


def find_repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / AUTHORITY_RELATIVE / "candidate_patch_manifest.json").is_file():
            return parent
    raise AuthorityError("repository root containing sealed v2.29.3.9.1 lane not found")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_close(actual: float, expected: float, label: str, tolerance: float) -> None:
    if not math.isclose(float(actual), float(expected), abs_tol=tolerance, rel_tol=0.0):
        raise AuthorityError(f"{label}: expected {expected}, got {actual}")


def _assert_vector(
    actual: Iterable[float],
    expected: Iterable[float],
    label: str,
    tolerance: float,
) -> None:
    actual_values = tuple(actual)
    expected_values = tuple(expected)
    if len(actual_values) != len(expected_values):
        raise AuthorityError(f"{label}: vector length mismatch")
    for index, (actual_value, expected_value) in enumerate(
        zip(actual_values, expected_values)
    ):
        _assert_close(actual_value, expected_value, f"{label}[{index}]", tolerance)


def index_unique_component_records(
    records: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    blockers: list[str] = []
    for component_id in COMPONENT_IDS:
        matches = tuple(
            record
            for record in records
            if record.get("canonical_component_id") == component_id
        )
        if len(matches) != 1:
            blockers.append(
                "AUTHORITY_COMPONENT_RECORD_COUNT_MISMATCH:"
                f"{component_id}:{len(matches)}"
            )
        else:
            indexed[component_id] = matches[0]
    if blockers:
        raise AuthorityError(blockers)
    return indexed


def load_authority(
    repository_root: Path | None = None,
    linear_tolerance_mm: float = LINEAR_TOLERANCE_MM,
    intersection_volume_tolerance_mm3: float = (
        INTERSECTION_VOLUME_TOLERANCE_MM3
    ),
    hardware_records: Sequence[Mapping[str, object]] | None = None,
) -> AuthorityParameters:
    root = (repository_root or find_repository_root()).resolve()
    lane = root / AUTHORITY_RELATIVE
    coordinate = _load(lane / "coordinate_authority.json")
    frame = _load(lane / "body_frame_authority.json")
    crossmember = _load(lane / "front_crossmember_authority.json")
    fixed = _load(lane / "fixed_body_dimension_authority.json")
    hardware = (
        list(hardware_records)
        if hardware_records is not None
        else _load(lane / "hardware_envelope_registry.json")
    )
    width = _load(lane / "operational_width_contract.json")
    holds = _load(lane / "known_hold_registry.json")

    by_id = index_unique_component_records(hardware)
    components = tuple(
        Envelope(
            component_id=component_id,
            minimum=_tuple3(by_id[component_id]["envelope_min_xyz_mm"]),
            maximum=_tuple3(by_id[component_id]["envelope_max_xyz_mm"]),
            source_path=str(by_id[component_id]["source_path"]),
            source_revision=str(by_id[component_id]["source_revision"]),
            dimension_status=str(by_id[component_id]["dimension_status"]),
        )
        for component_id in COMPONENT_IDS
    )
    parameters = AuthorityParameters(
        version="v2.29.3.9.1",
        units=str(coordinate["units"]),
        axes=tuple(
            (
                axis,
                str(values["meaning"]),
                str(values["positive"]),
            )
            for axis, values in sorted(coordinate["axes"].items())
        ),
        components=components,
        front_datum_y_mm=float(crossmember["front_datum_y_mm"]),
        bare_frame_width_mm=float(frame["bare_frame_union"]["width_mm"]),
        rail_center_separation_mm=abs(
            float(frame["rail_centerlines_x_mm"]["LEFT"])
            - float(frame["rail_centerlines_x_mm"]["RIGHT"])
        ),
        core_length_mm=float(fixed["core_length_mm"]),
        registered_interface_width_mm=float(width["candidate_target_max_mm"]),
        operational_hard_limit_mm=float(width["hard_limit_mm"]),
        linear_tolerance_mm=float(linear_tolerance_mm),
        intersection_volume_tolerance_mm3=float(
            intersection_volume_tolerance_mm3
        ),
        battery_placement_status="PLACED_FROM_HARDWARE_ENVELOPE_REGISTRY",
        source_records=tuple(
            SourceRecord(
                relative_path=(AUTHORITY_RELATIVE / name).as_posix(),
                sha256=_sha256(lane / name),
                bytes=(lane / name).stat().st_size,
            )
            for name in SOURCE_FILES
        ),
        release_holds=tuple(
            (key, str(value))
            for key, value in sorted(holds.items())
            if key != "version"
        ),
    )

    _assert_vector(
        parameters.component("V22939-FPB-RAIL-L").minimum,
        frame["rail_envelopes"]["LEFT"]["min"],
        "left rail minimum",
        linear_tolerance_mm,
    )
    _assert_vector(
        parameters.component("V22939-FPB-RAIL-L").maximum,
        frame["rail_envelopes"]["LEFT"]["max"],
        "left rail maximum",
        linear_tolerance_mm,
    )
    _assert_vector(
        parameters.component("V22939-FPB-RAIL-R").minimum,
        frame["rail_envelopes"]["RIGHT"]["min"],
        "right rail minimum",
        linear_tolerance_mm,
    )
    _assert_vector(
        parameters.component("V22939-FPB-RAIL-R").maximum,
        frame["rail_envelopes"]["RIGHT"]["max"],
        "right rail maximum",
        linear_tolerance_mm,
    )
    _assert_vector(
        parameters.component("V22939-FPB-FRONT-XMEMBER").minimum,
        crossmember["envelope"]["min"],
        "crossmember minimum",
        linear_tolerance_mm,
    )
    _assert_vector(
        parameters.component("V22939-FPB-FRONT-XMEMBER").maximum,
        crossmember["envelope"]["max"],
        "crossmember maximum",
        linear_tolerance_mm,
    )
    for component_id, dimension_id in (
        ("V22939-CBOX", "CBOX"),
        ("V22939-BBOX", "BBOX"),
        ("V22939-BATTERY-CASSETTE", "BATTERY_CASSETTE"),
    ):
        expected = fixed["current_dimensions"][dimension_id]
        _assert_vector(
            parameters.component(component_id).dimensions,
            (expected["X"], expected["Y"], expected["Z"]),
            f"{dimension_id} dimensions",
            linear_tolerance_mm,
        )
    width_records = [record for record in hardware if record.get("width_inclusion")]
    registered_min = min(
        float(record["maximum_interface_envelope"]["min_xyz_mm"][0])
        for record in width_records
    )
    registered_max = max(
        float(record["maximum_interface_envelope"]["max_xyz_mm"][0])
        for record in width_records
    )
    _assert_close(
        registered_max - registered_min,
        parameters.registered_interface_width_mm,
        "registered maximum-interface width",
        linear_tolerance_mm,
    )
    return parameters
