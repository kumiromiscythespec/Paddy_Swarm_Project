from __future__ import annotations

from collections import Counter, defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
from typing import Iterable, Sequence

from drive_pto_contract import (
    A1_BUILD_PLATE_MM,
    BELT_WIDTH_MM,
    EXPECTED_BRANCH,
    EXPECTED_HEAD,
    PITCH_MM,
    belt_tooth_count,
    pitch_diameter_mm,
)
from geometry_common import BuiltPart
from part_number_registry import ALL_PARTS, validate_registry


SOURCE_LANE = (
    "cad/common_rover/"
    "v2_29_3_9_1_printed_drive_pto_kit_v0_1/"
)
VERTEX_QUANTIZATION_MM = 1.0e-5
DEGENERATE_AREA2_THRESHOLD = 1.0e-18


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _binary_triangles(data: bytes) -> list[tuple[tuple[float, float, float], ...]]:
    count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + count * 50
    if expected_size != len(data):
        raise ValueError("NOT_BINARY_STL")
    triangles = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        triangles.append(
            (
                (values[3], values[4], values[5]),
                (values[6], values[7], values[8]),
                (values[9], values[10], values[11]),
            )
        )
        offset += 50
    return triangles


def _ascii_triangles(data: bytes) -> list[tuple[tuple[float, float, float], ...]]:
    vertices = []
    for raw in data.decode("utf-8", errors="strict").splitlines():
        fields = raw.strip().split()
        if len(fields) == 4 and fields[0].lower() == "vertex":
            vertices.append(tuple(float(value) for value in fields[1:]))
    if not vertices or len(vertices) % 3:
        raise ValueError("INVALID_ASCII_STL")
    return [
        tuple(vertices[index : index + 3])
        for index in range(0, len(vertices), 3)
    ]


def load_stl_triangles(
    path: Path,
) -> list[tuple[tuple[float, float, float], ...]]:
    data = path.read_bytes()
    if len(data) >= 84:
        try:
            return _binary_triangles(data)
        except ValueError:
            pass
    return _ascii_triangles(data)


def _quantized(vertex: Sequence[float]) -> tuple[int, int, int]:
    return tuple(
        int(round(float(value) / VERTEX_QUANTIZATION_MM)) for value in vertex
    )


def _area2(
    triangle: tuple[tuple[float, float, float], ...],
) -> float:
    first, second, third = triangle
    a = tuple(second[index] - first[index] for index in range(3))
    b = tuple(third[index] - first[index] for index in range(3))
    cross = (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
    return sum(value * value for value in cross)


def inspect_stl_mesh(path: Path) -> dict[str, object]:
    triangles = load_stl_triangles(path)
    edge_to_triangles: dict[
        tuple[tuple[int, int, int], tuple[int, int, int]], list[int]
    ] = defaultdict(list)
    degenerate = 0
    for triangle_index, triangle in enumerate(triangles):
        if _area2(triangle) <= DEGENERATE_AREA2_THRESHOLD:
            degenerate += 1
        vertices = [_quantized(vertex) for vertex in triangle]
        for index in range(3):
            edge = tuple(
                sorted((vertices[index], vertices[(index + 1) % 3]))
            )
            edge_to_triangles[edge].append(triangle_index)
    bad_edges = {
        edge: indexes
        for edge, indexes in edge_to_triangles.items()
        if len(indexes) != 2
    }
    adjacency: dict[int, set[int]] = defaultdict(set)
    for indexes in edge_to_triangles.values():
        if len(indexes) == 2:
            first, second = indexes
            adjacency[first].add(second)
            adjacency[second].add(first)
    unseen = set(range(len(triangles)))
    component_count = 0
    while unseen:
        component_count += 1
        queue = deque((unseen.pop(),))
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
    watertight = not bad_edges
    passed = (
        bool(triangles)
        and watertight
        and degenerate == 0
        and component_count == 1
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "triangle_count": len(triangles),
        "watertight": watertight,
        "nonmanifold_or_boundary_edge_count": len(bad_edges),
        "degenerate_face_count": degenerate,
        "connected_component_count": component_count,
    }


def reject_duplicate_stls(paths: Iterable[Path]) -> dict[str, str]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        by_hash[sha256_file(path)].append(path.name)
    duplicates = {
        digest: names for digest, names in by_hash.items() if len(names) > 1
    }
    if duplicates:
        raise ValueError(f"DUPLICATE_STL_REJECTED:{duplicates}")
    return {names[0]: digest for digest, names in by_hash.items()}


def reject_bytecode_paths(paths: Iterable[str]) -> None:
    invalid = [
        path
        for path in paths
        if path.endswith((".pyc", ".pyo"))
        or "__pycache__" in Path(path).parts
    ]
    if invalid:
        raise ValueError(f"BYTECODE_REJECTED:{invalid}")


def reject_untracked_cad_outside_lane(paths: Iterable[str]) -> None:
    invalid = [
        path.replace("\\", "/")
        for path in paths
        if not path.replace("\\", "/").startswith(SOURCE_LANE)
    ]
    if invalid:
        raise ValueError(f"UNTRACKED_CAD_OUTSIDE_NEW_LANE_REJECTED:{invalid}")


def _git(repo_root: Path, *arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_repository_scope(repo_root: Path) -> dict[str, object]:
    branch = _git(repo_root, "branch", "--show-current")[0]
    head = _git(repo_root, "rev-parse", "HEAD")[0]
    tracked = _git(repo_root, "diff", "--name-only")
    staged = _git(repo_root, "diff", "--cached", "--name-only")
    untracked = _git(
        repo_root, "ls-files", "--others", "--exclude-standard"
    )
    reject_untracked_cad_outside_lane(untracked)
    pyc = [str(path) for path in repo_root.rglob("*.pyc")]
    pyo = [str(path) for path in repo_root.rglob("*.pyo")]
    pycache = [
        str(path)
        for path in repo_root.rglob("__pycache__")
        if path.is_dir()
    ]
    reject_bytecode_paths([*pyc, *pyo, *pycache])
    status = (
        branch == EXPECTED_BRANCH
        and head == EXPECTED_HEAD
        and not tracked
        and not staged
        and not pyc
        and not pyo
        and not pycache
    )
    return {
        "status": "PASS" if status else "FAIL",
        "scan_scope": "TARGET_WORKTREE_ONLY",
        "branch": branch,
        "branch_matches": branch == EXPECTED_BRANCH,
        "head": head,
        "head_matches": head == EXPECTED_HEAD,
        "tracked_baseline_changes": tracked,
        "staged_changes": staged,
        "allowed_untracked_source_lane_files": untracked,
        "pyc_count": len(pyc),
        "pyo_count": len(pyo),
        "pycache_count": len(pycache),
    }


def _part_validation(
    built: BuiltPart,
    stl_path: Path,
) -> dict[str, object]:
    record = built.record()
    box = record["bounding_box_mm"]
    marking = record["marking"]
    metadata = record["metadata"]
    shape_checks = {
        "cadquery_valid": record["valid"],
        "solid_count_one": record["solid_count"] == 1,
        "positive_volume": record["volume_mm3"] > 0.0,
        "part_number_matches": (
            marking["part_number"] == built.spec.part_number
            and marking["geometry_part_number"] == built.spec.part_number
        ),
        "marking_connected": (
            marking["marking_verified"]
            and marking["floating_part_number_solid_count"] == 0
            and marking["glyph_solid_count"]
            == marking["intersecting_glyph_solid_count"]
        ),
        "minimum_text_size": marking["minimum_text_size_mm"] >= 2.0,
        "minimum_wall": float(metadata["minimum_wall_mm"]) >= 1.2,
        "printable_orientation": bool(metadata["print_orientation"]),
        "build_plate_fit": all(
            float(box[axis]) <= A1_BUILD_PLATE_MM[index]
            for index, axis in enumerate(("x", "y", "z"))
        ),
        "support_off": metadata["support"] == "OFF",
        "no_trapped_support": not metadata["trapped_support"],
    }
    mesh = inspect_stl_mesh(stl_path)
    passed = all(shape_checks.values()) and mesh["status"] == "PASS"
    return {
        **record,
        "stl_sha256": sha256_file(stl_path),
        "stl_size_bytes": stl_path.stat().st_size,
        "shape_checks": shape_checks,
        "mesh": mesh,
        "status": "PASS" if passed else "FAIL",
    }


def validate_all(
    built_parts: Sequence[BuiltPart],
    artifact_directory: Path,
    repo_root: Path,
) -> dict[str, object]:
    stl_directory = artifact_directory / "stl"
    stl_paths = [stl_directory / part.spec.filename for part in built_parts]
    hashes = reject_duplicate_stls(stl_paths)
    records = [
        _part_validation(part, path)
        for part, path in zip(built_parts, stl_paths)
    ]
    continuous_belts = [
        record
        for record in records
        if record["metadata"].get("form") == "CONTINUOUS_CLOSED_LOOP"
    ]
    pulleys = [
        record
        for record in records
        if record["family"] == "pulley"
    ]
    guards = [
        record
        for record in records
        if record["family"] == "guard"
    ]
    analytical = {
        "20t_pitch_diameter_exact": math.isclose(
            pitch_diameter_mm(20),
            31.830988618379067,
            abs_tol=1.0e-12,
            rel_tol=0.0,
        ),
        "60t_pitch_diameter_exact": math.isclose(
            pitch_diameter_mm(60),
            95.4929658551372,
            abs_tol=1.0e-12,
            rel_tol=0.0,
        ),
        "ratio_3_to_1": math.isclose(60 / 20, 3.0),
        "450mm_is_90_teeth": belt_tooth_count(450.0) == 90,
        "pulley_count_8": len(pulleys) == 8,
        "20t_count_4": sum(
            record["metadata"]["teeth"] == 20 for record in pulleys
        )
        == 4,
        "60t_count_4": sum(
            record["metadata"]["teeth"] == 60 for record in pulleys
        )
        == 4,
        "pulley_pitch_5mm": all(
            record["metadata"]["pitch_mm"] == PITCH_MM for record in pulleys
        ),
        "pulley_belt_width_15mm": all(
            record["metadata"]["belt_width_mm"] == BELT_WIDTH_MM
            for record in pulleys
        ),
        "continuous_belt_count_3": len(continuous_belts) == 3,
        "continuous_belts_closed": all(
            record["metadata"]["closed_loop"] for record in continuous_belts
        ),
        "continuous_belts_90_teeth": all(
            record["metadata"]["tooth_count"] == 90
            for record in continuous_belts
        ),
        "continuous_belt_width_15mm": all(
            record["metadata"]["belt_width_mm"] == BELT_WIDTH_MM
            for record in continuous_belts
        ),
        "inner_tooth_orientation": all(
            record["metadata"]["inner_tooth_orientation"]
            for record in continuous_belts
        ),
        "hub_pcd24_when_selected": all(
            (
                not record["metadata"]["pcd24_4xm4"]
                or record["metadata"]["hub_pcd_mm"] == 24.0
            )
            for record in pulleys
        ),
        "guard_clearance_minimum_8mm": all(
            record["metadata"].get("minimum_guard_clearance_mm", 8.0) >= 8.0
            for record in guards
        ),
        "part_number_registry_unique": (
            validate_registry()["unique_part_number_count"] == len(ALL_PARTS)
        ),
        "generated_part_numbers_unique": (
            len({part.spec.part_number for part in built_parts})
            == len(built_parts)
        ),
        "stl_hashes_unique": len(hashes) == len(built_parts),
    }
    repository = validate_repository_scope(repo_root)
    passed = (
        all(record["status"] == "PASS" for record in records)
        and all(analytical.values())
        and repository["status"] == "PASS"
    )
    return {
        "schema": "PS_DRIVE_PTO_GEOMETRY_VALIDATION_V0_1",
        "status": "PASS" if passed else "FAIL",
        "build_plate": {
            "printer": "Bambu Lab A1",
            "dimensions_mm": A1_BUILD_PLATE_MM,
            "status": (
                "PASS"
                if all(
                    record["shape_checks"]["build_plate_fit"]
                    for record in records
                )
                else "FAIL"
            ),
        },
        "physical_part_number_status": (
            "PASS"
            if all(
                record["shape_checks"]["marking_connected"]
                and record["shape_checks"]["part_number_matches"]
                for record in records
            )
            else "FAIL"
        ),
        "analytical": analytical,
        "repository": repository,
        "part_count": len(records),
        "parts": records,
    }


def write_validation(
    report: dict[str, object],
    path: Path,
) -> None:
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
