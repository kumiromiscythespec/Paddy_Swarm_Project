"""Reference-only CadQuery envelopes for Phase 4T-LS-A.

These models communicate space, flow topology, service access and load-path
separation.  They are not tank, fitting, valve or printable-part definitions.
"""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.parameters import (
    branch_identifiers,
    local_sump_high_level_reference_mm,
    local_sump_reference_outer_size_mm,
    tower_bottom_drain_elevation_mm,
    tower_reference_load_kg,
    tower_support_deck_elevation_mm,
)


REFERENCE_STATUS = "REFERENCE_ONLY_NOT_A_WATERTIGHT_OR_PRINTABLE_PART"
PRINT_TARGET = False
STL_ALLOWED = False
TANK_LOAD_BEARING = False
FRAME_MEMBER_MM = 10.0
LEVEL_MARKER_THICKNESS_MM = 3.0


def _box(
    size: tuple[float, float, float],
    center: tuple[float, float, float],
) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)


def _compound(models: list[cq.Workplane]) -> cq.Workplane:
    solids = [solid for model in models for solid in model.solids().vals()]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _cylinder(
    radius: float,
    length: float,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(*start),
        cq.Vector(*direction),
    )
    return cq.Workplane("XY").newObject([solid])


def build_local_sump_reference_envelope() -> cq.Workplane:
    """Build a deliberately open skeletal 420 x 320 x 120 mm envelope."""

    size_x, size_y, size_z = local_sump_reference_outer_size_mm
    half_x = 0.5 * size_x
    half_y = 0.5 * size_y
    member = FRAME_MEMBER_MM
    model: cq.Workplane | None = None
    members: list[cq.Workplane] = []
    for z_value in (0.5 * member, size_z - 0.5 * member):
        members.extend(
            [
                _box((size_x, member, member), (0.0, -half_y + 0.5 * member, z_value)),
                _box((size_x, member, member), (0.0, half_y - 0.5 * member, z_value)),
                _box((member, size_y, member), (-half_x + 0.5 * member, 0.0, z_value)),
                _box((member, size_y, member), (half_x - 0.5 * member, 0.0, z_value)),
            ]
        )
    for x_value in (-half_x + 0.5 * member, half_x - 0.5 * member):
        for y_value in (-half_y + 0.5 * member, half_y - 0.5 * member):
            members.append(
                _box((member, member, size_z), (x_value, y_value, 0.5 * size_z))
            )
    for level in (50.0, 80.0, local_sump_high_level_reference_mm):
        members.append(
            _box(
                (size_x, LEVEL_MARKER_THICKNESS_MM, LEVEL_MARKER_THICKNESS_MM),
                (0.0, -half_y + 0.5 * LEVEL_MARKER_THICKNESS_MM, level),
            )
        )
    # Large attached pads identify candidate zones only; no hole is defined.
    members.extend(
        [
            _box((size_x, member, member), (0.0, half_y - 0.5 * member, 45.0)),
            _box((size_x, member, member), (0.0, half_y - 0.5 * member, 95.0)),
            _box((60.0, member, 34.0), (-70.0, half_y - 0.5 * member, 45.0)),
            _box((60.0, member, 34.0), (70.0, half_y - 0.5 * member, 95.0)),
        ]
    )
    for member_shape in members:
        model = member_shape if model is None else model.union(member_shape)
    if model is None:
        raise RuntimeError("local sump envelope did not create geometry")
    return model


def local_sump_reference_metadata() -> dict[str, object]:
    return {
        "status": REFERENCE_STATUS,
        "outer_envelope_mm": list(local_sump_reference_outer_size_mm),
        "normal_level_reference_mm": 50.0,
        "maximum_operating_level_reference_mm": 80.0,
        "high_level_reference_mm": local_sump_high_level_reference_mm,
        "branch_candidate_region_present": True,
        "emergency_overflow_candidate_region_present": True,
        "bulkhead_hole_diameter_mm": None,
        "open_skeletal_non_watertight_geometry": True,
        "tank_supports_tower_load": False,
        "commercial_container_measurement_pending": True,
    }


def build_tower_support_deck_reference() -> cq.Workplane:
    """Build dry floor-supported frame plus non-contact drain/load references."""

    deck_top = tower_support_deck_elevation_mm[1]
    outer_x = 520.0
    outer_y = 420.0
    leg = 30.0
    models: list[cq.Workplane] = []
    for x_value in (-245.0, 245.0):
        for y_value in (-195.0, 195.0):
            models.append(
                _box((leg, leg, deck_top), (x_value, y_value, 0.5 * deck_top))
            )
    models.extend(
        [
            _box((outer_x, 30.0, 20.0), (0.0, -195.0, deck_top - 10.0)),
            _box((outer_x, 30.0, 20.0), (0.0, 195.0, deck_top - 10.0)),
            _box((30.0, outer_y, 20.0), (-245.0, 0.0, deck_top - 10.0)),
            _box((30.0, outer_y, 20.0), (245.0, 0.0, deck_top - 10.0)),
            _box((outer_x - 30.0, 35.0, 20.0), (0.0, 0.0, deck_top - 10.0)),
            _box((35.0, outer_y - 30.0, 20.0), (0.0, 0.0, deck_top - 10.0)),
        ]
    )
    dry_frame = models[0]
    for member in models[1:]:
        dry_frame = dry_frame.union(member)
    load_plate = (
        cq.Workplane("XY")
        .workplane(offset=deck_top - 10.0)
        .circle(140.0)
        .circle(40.0)
        .extrude(10.0)
        .union(dry_frame)
    )
    drain_ref = (
        cq.Workplane("XY")
        .workplane(offset=tower_bottom_drain_elevation_mm[0])
        .circle(15.0)
        .circle(10.0)
        .extrude(
            tower_bottom_drain_elevation_mm[1]
            - tower_bottom_drain_elevation_mm[0]
        )
    )
    load_arrow = _cylinder(
        4.0,
        35.0,
        (0.0, 0.0, tower_bottom_drain_elevation_mm[1] + 10.0),
        (0.0, 0.0, -1.0),
    ).union(
        cq.Workplane("XY")
        .workplane(offset=tower_bottom_drain_elevation_mm[1])
        .circle(10.0)
        .workplane(offset=12.0)
        .circle(4.0)
        .loft(combine=True)
    )
    return _compound([load_plate, drain_ref, load_arrow])


def support_deck_reference_metadata() -> dict[str, object]:
    return {
        "status": REFERENCE_STATUS,
        "deck_elevation_mm": tower_support_deck_elevation_mm[1],
        "tower_bottom_drain_elevation_mm": tower_bottom_drain_elevation_mm[1],
        "reference_load_kg": tower_reference_load_kg,
        "load_path": "DRY_FRAME_TO_FLOOR",
        "sump_pullout_clearance_reference_mm": [460.0, 360.0],
        "tank_load_bearing": False,
        "pipe_load_bearing": False,
    }


def build_central_pump_well_reference() -> cq.Workplane:
    """Build an open 300 x 300 x 180 mm measurement envelope and internals."""

    size_x = 300.0
    size_y = 300.0
    size_z = 180.0
    member = 10.0
    models: list[cq.Workplane] = []
    for z_value in (5.0, 175.0):
        models.extend(
            [
                _box((size_x, member, member), (0.0, -145.0, z_value)),
                _box((size_x, member, member), (0.0, 145.0, z_value)),
                _box((member, size_y, member), (-145.0, 0.0, z_value)),
                _box((member, size_y, member), (145.0, 0.0, z_value)),
            ]
        )
    for x_value in (-145.0, 145.0):
        for y_value in (-145.0, 145.0):
            models.append(_box((member, member, size_z), (x_value, y_value, 90.0)))
    frame = models[0]
    for member_shape in models[1:]:
        frame = frame.union(member_shape)
    for level in (45.0, 90.0, 145.0):
        frame = frame.union(_box((size_x, 3.0, 3.0), (0.0, -148.5, level)))
    pump_envelope = _box((100.0, 80.0, 100.0), (-60.0, 0.0, 55.0))
    settling_partition = _box((8.0, 260.0, 100.0), (35.0, 0.0, 55.0))
    strainer_envelope = _cylinder(30.0, 80.0, (85.0, 0.0, 15.0), (0.0, 0.0, 1.0))
    drain_arrow = _cylinder(5.0, 55.0, (110.0, -150.0, 18.0), (0.0, -1.0, 0.0))
    return _compound(
        [frame, pump_envelope, settling_partition, strainer_envelope, drain_arrow]
    )


def pump_well_reference_metadata() -> dict[str, object]:
    return {
        "status": REFERENCE_STATUS,
        "outer_height_mm": 180.0,
        "commercial_pp_pe_authority": True,
        "location": "NEAR_TRUNK_MIDPOINT",
        "level_markers": ["LOW", "NORMAL", "HIGH"],
        "settling_bay_reference": True,
        "removable_strainer_reference": True,
        "complete_drain_direction_reference": True,
        "pump_dimensions": "PHYSICAL_MEASUREMENT_PENDING",
        "minimum_submergence": "PHYSICAL_MEASUREMENT_PENDING",
    }


def _build_parallel_zone(
    tower_positions_x: tuple[float, ...],
    active_branch_indices: tuple[int, ...],
) -> cq.Workplane:
    count = len(tower_positions_x)
    trunk_margin = 250.0
    trunk_start = min(tower_positions_x) - trunk_margin
    trunk_end = max(tower_positions_x) + trunk_margin
    models: list[cq.Workplane] = []
    for x_value in tower_positions_x:
        models.append(build_local_sump_reference_envelope().translate((x_value, 0.0, 0.0)))
    models.append(
        _cylinder(
            20.0,
            trunk_end - trunk_start,
            (trunk_start, 250.0, 40.0),
            (1.0, 0.0, 0.0),
        )
    )
    for index, x_value in enumerate(tower_positions_x):
        active = index in active_branch_indices
        branch_start_y = 160.0 if active else 225.0
        branch_length = 90.0 if active else 25.0
        models.append(
            _cylinder(
                0.5 * (32.0 if active else 25.0),
                branch_length,
                (x_value, branch_start_y, 40.0),
                (0.0, 1.0, 0.0),
            )
        )
        models.append(
            _box(
                (48.0, 48.0, 48.0),
                (x_value, 205.0 if active else 220.0, 40.0),
            )
        )
    pump = build_central_pump_well_reference().translate((0.0, 470.0, 0.0))
    pump_link = _cylinder(20.0, 220.0, (0.0, 250.0, 40.0), (0.0, 1.0, 0.0))
    models.extend([pump, pump_link])
    return _compound(models)


def build_parallel_equalization_zone_4tower_reference() -> cq.Workplane:
    positions = (-875.0, -375.0, 375.0, 875.0)
    # The physical rig uses four branches; the 8-way manifold's four spare
    # closures are documented in the interface spec and diagram.
    return _build_parallel_zone(positions, (0, 1, 2, 3))


def build_parallel_equalization_zone_8tower_reference() -> cq.Workplane:
    positions = (-1750.0, -1250.0, -750.0, -250.0, 250.0, 750.0, 1250.0, 1750.0)
    return _build_parallel_zone(positions, (0, 1, 2, 3))


def parallel_zone_metadata(tower_positions: int) -> dict[str, object]:
    if tower_positions not in (4, 8):
        raise ValueError("reference zone positions must be four or eight")
    return {
        "status": REFERENCE_STATUS,
        "tower_positions": tower_positions,
        "active_branches": 4,
        "closed_future_branches": 4 if tower_positions == 8 else 4,
        "hydraulic_connection": "PARALLEL_BRANCH_EQUALIZATION",
        "serial_daisy_chain": False,
        "common_pump_well_near_midpoint": True,
        "rear_service_route": True,
        "crosses_human_aisle": False,
        "room_floor_dimensions_fixed": False,
        "branch_identifiers": list(branch_identifiers),
    }


def build_isolation_flow_reference_assembly() -> cq.Workplane:
    """Build an abstract flow-path assembly for one isolatable branch."""

    tower = (
        cq.Workplane("XY")
        .workplane(offset=170.0)
        .circle(100.0)
        .circle(97.0)
        .extrude(300.0)
    )
    sump = build_local_sump_reference_envelope()
    upper_supply = _cylinder(8.0, 230.0, (-230.0, 0.0, 500.0), (1.0, 0.0, 0.0))
    supply_drop = _cylinder(8.0, 30.0, (0.0, 0.0, 500.0), (0.0, 0.0, -1.0))
    supply_valve = _box((45.0, 45.0, 45.0), (-130.0, 0.0, 500.0))
    equalization_branch = _cylinder(16.0, 170.0, (0.0, 160.0, 40.0), (0.0, 1.0, 0.0))
    equalization_valve = _box((60.0, 60.0, 60.0), (0.0, 220.0, 40.0))
    trunk = _cylinder(20.0, 500.0, (-250.0, 330.0, 40.0), (1.0, 0.0, 0.0))
    overflow = _cylinder(16.0, 220.0, (70.0, 160.0, 100.0), (0.0, -1.0, 0.0))
    safety_receiver = _box((180.0, 100.0, 50.0), (70.0, -110.0, 25.0))
    return _compound(
        [
            sump,
            tower,
            upper_supply,
            supply_drop,
            supply_valve,
            equalization_branch,
            equalization_valve,
            trunk,
            overflow,
            safety_receiver,
        ]
    )


def isolation_reference_metadata() -> dict[str, object]:
    return {
        "status": REFERENCE_STATUS,
        "upper_supply_valve_present": True,
        "equalization_valve_present": True,
        "common_trunk_present": True,
        "emergency_overflow_present": True,
        "emergency_destination": "NON_CIRCULATING_EMERGENCY_RECEIVER",
        "equalization_closure_does_not_disconnect_other_branches": True,
        "flow_direction_defined_in_svg": True,
    }
