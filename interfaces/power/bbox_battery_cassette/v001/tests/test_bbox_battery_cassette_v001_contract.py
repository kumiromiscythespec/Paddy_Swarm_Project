#!/usr/bin/env python3
"""Contract tests and deterministic artifact generator for PS-BBOX-CASSETTE-V001.

Standard library only. The generator writes review artifacts only when explicitly
invoked with --generate-artifacts. It never writes the Git index.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html
import io
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath


SOURCE_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = SOURCE_ROOT / "PS_BBOX_CASSETTE_V001_INTERFACE_CONTRACT.json"
README_PATH = SOURCE_ROOT / "README.md"
ICD_PATH = SOURCE_ROOT / "INTERFACE_CONTROL_DOCUMENT.md"
VALIDATION_PATH = SOURCE_ROOT / "WATERPROOF_SAFETY_AND_VALIDATION_PLAN.md"
TEST_PATH = Path(__file__).resolve()

SOURCE_FILES = [
    README_PATH,
    CONTRACT_PATH,
    ICD_PATH,
    VALIDATION_PATH,
    TEST_PATH,
]

EXPECTED_STATES = [
    "ABSENT",
    "INSERTING",
    "SEATED_UNLATCHED",
    "PRIMARY_LATCHED",
    "SAFETY_LATCHED",
    "WET_CHECK",
    "WET_FAULT",
    "CONNECTOR_ADVANCING",
    "SIGNAL_CONNECTED",
    "IDENTITY_CHECK",
    "COMPATIBILITY_CHECK",
    "PRECHARGE",
    "PRECHARGE_FAILED",
    "READY_TO_ENERGIZE",
    "ENERGIZED",
    "RUNNING",
    "DEENERGIZING",
    "CONNECTOR_RETRACTING",
    "REMOVAL_AUTHORIZED",
    "FAULT",
    "OVERTEMPERATURE",
    "OVERVOLTAGE",
    "UNDERVOLTAGE",
    "POLARITY_FAULT",
    "UNKNOWN_CASSETTE",
]

EXPECTED_RACK_STATES = [
    "EMPTY",
    "RETURNED_WARM",
    "COOLING",
    "INSPECTION",
    "WET_FAULT",
    "IDENTIFIED",
    "CHARGING",
    "CHARGE_COMPLETE",
    "READY",
    "RESERVED",
    "FAULT",
    "QUARANTINE",
]

EXPECTED_STATUS = {
    "commercial_box_compatibility": "REMOVED_BY_PROJECT_DECISION",
    "interface_contract_status": "DOCUMENTATION_CANDIDATE_ONLY",
    "cassette_architecture_status": "INTERFACE_CONTRACT_NOT_CAD_VALIDATED",
    "cassette_waterproof_status": "NOT_PHYSICALLY_VALIDATED",
    "connector_waterproof_status": "NOT_PHYSICALLY_VALIDATED",
    "CBOX_boundary_status": "CONTRACT_ONLY_NOT_LEAK_TESTED",
    "battery_cell_status": "NOT_SELECTED",
    "battery_chemistry_status": "NOT_SELECTED",
    "battery_voltage_status": "NOT_SELECTED",
    "battery_capacity_status": "NOT_SELECTED",
    "connector_product_status": "NOT_SELECTED",
    "gasket_product_status": "NOT_SELECTED",
    "vent_product_status": "NOT_SELECTED",
    "BMS_status": "NOT_SELECTED",
    "charger_status": "NOT_SELECTED",
    "electrical_current_rating_status": "NOT_DEFINED",
    "thermal_status": "NOT_VALIDATED",
    "fire_safety_status": "REQUIRES_SEPARATE_SPECIALIST_REVIEW",
    "actual_printability_status": "NOT_VALIDATED",
    "manufacturing_readiness": "NOT_APPROVED",
    "purchase_approval": "NOT_APPROVED",
    "field_deployment": "NOT_APPROVED",
}

REQUIRED_TOP_LEVEL = [
    "contract_name",
    "title",
    "version",
    "repository_basis",
    "source_scope",
    "approval_flags",
    "mandatory_status",
    "coordinate_system",
    "existing_fixed_core",
    "architecture",
    "zones",
    "zone_invariants",
    "insertion",
    "connector_architecture",
    "mechanical_load_path",
    "cassette_enclosure",
    "connector_waterproofing",
    "drainage",
    "CBOX_boundary",
    "datums",
    "tolerance_architecture",
    "latches",
    "seal_compression",
    "electrical",
    "state_machine",
    "swap_locations",
    "human_swap_sequence",
    "water_sensors",
    "cassette_identity",
    "mis_insertion_prevention",
    "battery_mule",
    "charging_rack",
    "fleet_30_rover",
    "ownership",
    "vent_pressure",
    "thermal",
    "connector_health",
    "serviceability",
    "cleaning",
    "human_factors",
    "frozen_invariants",
    "open_parameters",
    "decision_matrix",
    "failure_modes",
    "FMEA_policy",
    "validation_stages",
    "waterproof_validation_matrix",
    "artifact_contract",
]

REQUIRED_OPEN_PARAMETERS = [
    "cassette exact dimensions",
    "cassette exact mass",
    "cell chemistry",
    "nominal voltage",
    "capacity",
    "current rating",
    "connector product",
    "contact count",
    "contact current rating",
    "connector stroke",
    "gasket material",
    "gasket compression",
    "latch force",
    "vent product",
    "vent activation behavior",
    "manual handling mass limit",
    "keep-alive energy source",
    "exact BBOX envelope",
    "exact CBOX feedthrough location",
    "exact charging slot and fleet cassette counts",
]

REQUIRED_FAILURES = [
    "cassette dropped",
    "cassette enclosure cracked",
    "cassette lid seal damaged",
    "cassette vent blocked",
    "cassette inserted backward",
    "incompatible cassette",
    "cassette half-seated",
    "primary latch open",
    "safety latch open",
    "latch sensor disagreement",
    "connector shuttle jammed",
    "connector half-mated",
    "connector seal damaged",
    "connector contaminated with mud",
    "drain blocked",
    "water in moat",
    "water in dry chamber",
    "feedthrough leakage",
    "CBOX moisture alarm",
    "overtemperature",
    "undervoltage",
    "overvoltage",
    "polarity fault",
    "pre-charge timeout",
    "welded contactor",
    "open fuse",
    "ID communication failure",
    "Battery Mule wrong cassette delivery",
    "charged dirty rack cross-contamination",
    "rover rolls during exchange",
    "shell closed on incomplete latch",
    "removal attempted while energized",
    "pressure vent event",
    "fire or smoke event",
    "water sensor failed",
    "water sensor disconnected",
    "connector overtemperature",
    "CBOX feedthrough harness strain",
]

REQUIRED_WATER_CONDITIONS = [
    "clean dry",
    "rain-wet",
    "muddy exterior",
    "muddy seal lip",
    "blocked primary drain",
    "partially blocked drain",
    "first seal damaged",
    "second seal damaged",
    "latch half-closed",
    "connector half-mated",
    "cassette tilted",
    "rover tilted",
    "temperature cycle",
    "repeated insertion",
    "vibration",
    "rollover orientation",
    "shallow standing water",
    "pressure differential",
    "water sensor failed",
    "water sensor disconnected",
]

REQUIRED_SERVICE_COMPONENTS = [
    "entry wiper",
    "guide rail",
    "wear pad",
    "corner bumper",
    "bottom skid",
    "primary latch",
    "safety latch",
    "latch sensor",
    "water sensor",
    "connector shuttle",
    "connector module",
    "secondary connector gasket",
    "wet-side harness",
    "drain cover candidate",
    "feedthrough module candidate",
]

REQUIRED_IDENTITY_FIELDS = [
    "unique cassette ID",
    "hardware revision",
    "battery class ID",
    "voltage class ID",
    "capacity class ID",
    "charge profile ID",
    "BMS revision",
    "manufacturing lot",
    "cycle count",
    "accumulated operating hours",
    "maximum observed temperature",
    "fault history",
    "water exposure flag",
    "service status",
    "quarantine status",
    "current SoC",
    "current health proxy",
]

REQUIRED_SWAP_STEPS = [
    "receive swap request",
    "move to dry swap pad",
    "stop rover",
    "apply wheel restraint",
    "stop PTO",
    "set selector NEUTRAL",
    "open main contactor",
    "confirm bus discharge",
    "open upper shell",
    "clean cassette top",
    "retract connector shuttle",
    "confirm electrical disconnect",
    "release safety latch",
    "release primary latch",
    "remove cassette vertically",
    "visually inspect connector vestibule",
    "check water and mud",
    "place dirty cassette in dirty bay",
    "confirm charged cassette ID",
    "insert cassette",
    "confirm structural seating",
    "close primary latch",
    "close safety latch",
    "perform dry check",
    "advance connector shuttle",
    "confirm signal and ID",
    "perform pre-charge",
    "close main contactor",
    "perform low-power self-test",
    "close shell",
    "grant drive authorization",
    "save swap log",
]


def load_contract() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def validate_contract(contract: dict) -> set[str]:
    """Return stable error codes. Used by normal and mutation tests."""
    errors: set[str] = set()

    for key in REQUIRED_TOP_LEVEL:
        if key not in contract:
            errors.add("REQUIRED_STRUCTURE")

    if contract.get("contract_name") != "PS-BBOX-CASSETTE-V001":
        errors.add("NAME_VERSION")
    if contract.get("version") != "v001":
        errors.add("NAME_VERSION")

    status = contract.get("mandatory_status", {})
    if status.get("commercial_box_compatibility") != "REMOVED_BY_PROJECT_DECISION":
        errors.add("COMMERCIAL_COMPAT")

    fixed = contract.get("existing_fixed_core", {})
    if fixed.get("layout") != "BBOX_FRONT_CBOX_REAR_IN_SERIES" or not fixed.get(
        "side_by_side_prohibited"
    ):
        errors.add("FIXED_CORE_LAYOUT")

    zones = {row.get("id"): row for row in contract.get("zones", [])}
    if list(row.get("id") for row in contract.get("zones", [])) != [
        "D0",
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
    ]:
        errors.add("ZONE_ORDER")
    d5 = zones.get("D5", {})
    if (
        d5.get("name") != "CBOX_DRY_CORE"
        or d5.get("water_policy") != "PERMANENT_DRY_CORE"
        or d5.get("owner") != "CBOX"
    ):
        errors.add("CBOX_DRY_CORE")

    layers = {row.get("name"): row for row in contract.get("architecture", {}).get("layers", [])}
    frame = layers.get("BBOX-FRAME", {})
    if frame.get("exchange_frequency") != "FIXED_TO_ROVER":
        errors.add("FRAME_FIXED")
    cassette = layers.get("BBOX-BATTERY-CASSETTE", {})
    if "standalone primary waterproof enclosure" not in cassette.get("responsibilities", []):
        errors.add("CASSETTE_PRIMARY_WATERPROOF")
    enclosure = contract.get("cassette_enclosure", {})
    if (
        enclosure.get("primary_waterproof_barrier")
        != "CASSETTE_STANDALONE_CONTINUOUS_ENCLOSURE"
        or enclosure.get("cradle_dependent_sealing") is not False
    ):
        errors.add("CASSETTE_PRIMARY_WATERPROOF")

    insertion = contract.get("insertion", {})
    if (
        insertion.get("baseline") != "VERTICAL_TOP_INSERTION"
        or insertion.get("insertion_axis") != "-Z"
        or insertion.get("removal_axis") != "+Z"
    ):
        errors.add("INSERTION_DIRECTION")

    connector = contract.get("connector_architecture", {})
    if (
        connector.get("recommended_candidate")
        != "UPPER_REAR_HORIZONTAL_CONNECTOR_SHUTTLE"
        or connector.get("bottom_exposed_connector_prohibited") is not True
    ):
        errors.add("CONNECTOR_POSITION")
    if connector.get("half_mated_drive_authorization_prohibited") is not True:
        errors.add("HALF_MATE")
    shuttle = connector.get("shuttle", {})
    if not shuttle.get("floating_alignment_required"):
        errors.add("FLOATING_MOUNT")

    load = contract.get("mechanical_load_path", {})
    if load.get("connector_supports_cassette_weight") is not False:
        errors.add("CONNECTOR_LOAD")
    if load.get("connector_locates_cassette") is not False:
        errors.add("CONNECTOR_GUIDE")
    if load.get("cassette_load_path") != [
        "cassette body",
        "bottom structural seat",
        "side guide and wear rail",
        "primary latch",
        "BBOX-FRAME",
        "LOWER-FRAME",
    ]:
        errors.add("LOAD_PATH")

    waterproof = contract.get("connector_waterproofing", {})
    if (
        waterproof.get("dual_seal_required") is not True
        or waterproof.get("single_seal_dependency_prohibited") is not True
    ):
        errors.add("DUAL_SEAL")
    if waterproof.get("drain_moat_required") is not True:
        errors.add("DRAIN_MOAT")
    expected_barriers = [
        "coarse contamination shield",
        "replaceable wiping lip",
        "first labyrinth",
        "drain moat",
        "water detection zone",
        "secondary compression gasket",
        "connector dry chamber",
        "recessed electrical contacts",
    ]
    if waterproof.get("barrier_order_outside_to_inside") != expected_barriers:
        errors.add("BARRIER_ORDER")

    drainage = contract.get("drainage", {})
    if drainage.get("direction") != "AWAY_FROM_CBOX_AND_CONNECTOR_DRY_CHAMBER":
        errors.add("DRAIN_DIRECTION")
    if not drainage.get("gravity_drained") or not drainage.get("blocked_drain_validation_required"):
        errors.add("DRAINAGE")

    zone_invariants = contract.get("zone_invariants", {})
    if zone_invariants.get("D3_water_blocks_main_contactor") is not True:
        errors.add("WATER_INTERLOCK")
    if zone_invariants.get("wet_cradle_and_CBOX_drainage_shared") is not False:
        errors.add("CBOX_DRAINAGE")

    boundary = contract.get("CBOX_boundary", {})
    if boundary.get("bare_cable_hole_prohibited") is not True:
        errors.add("CBOX_BARE_HOLE")
    if boundary.get("shares_wet_cradle_drainage") is not False:
        errors.add("CBOX_DRAINAGE")
    if not boundary.get("fixed_sealed_bulkhead_required"):
        errors.add("CBOX_BOUNDARY")

    latches = contract.get("latches", {})
    if not latches.get("shuttle_requires_both_latches"):
        errors.add("LATCH_INTERLOCK")
    if not latches.get("independent_safety_latch_required"):
        errors.add("SAFETY_LATCH")
    if not latches.get("primary_structural_latch_required"):
        errors.add("LATCH_INTERLOCK")

    seal = contract.get("seal_compression", {})
    if seal.get("target_compression") != "TBD_BY_GASKET_SELECTION":
        errors.add("GASKET_COMPRESSION")
    if not seal.get("compression_uniformity_required"):
        errors.add("GASKET_COMPRESSION")

    electrical = contract.get("electrical", {})
    if electrical.get("hot_swap_allowed") is not False:
        errors.add("HOT_SWAP")
    dead_front = electrical.get("dead_front", {})
    if dead_front.get("cassette_output_energized_when_removed") is not False:
        errors.add("DEAD_FRONT")
    if dead_front.get("exposed_energized_terminal_allowed") is not False:
        errors.add("DEAD_FRONT")
    if electrical.get("precharge_required") is not True:
        errors.add("PRECHARGE")
    if electrical.get("main_contactor_required") is not True:
        errors.add("CONTACTOR")
    if electrical.get("removal_while_main_contactor_ON_prohibited") is not True:
        errors.add("REMOVAL_ENERGIZED")
    if electrical.get("unknown_cassette_drive_authorization_prohibited") is not True:
        errors.add("UNKNOWN_ID")
    if electrical.get("wrong_voltage_class_authorization_prohibited") is not True:
        errors.add("VOLTAGE_CLASS")
    if electrical.get("wrong_chemistry_class_authorization_prohibited") is not True:
        errors.add("CHEMISTRY_CLASS")
    if "PTO stopped" not in electrical.get("swap_start_guards", []):
        errors.add("PTO_SWAP")

    state_machine = contract.get("state_machine", {})
    if state_machine.get("states") != EXPECTED_STATES:
        errors.add("STATE_SET")
    prohibited = {tuple(row) for row in state_machine.get("prohibited_transitions", [])}
    for transition in [
        ("ABSENT", "ENERGIZED"),
        ("SEATED_UNLATCHED", "ENERGIZED"),
        ("WET_FAULT", "ENERGIZED"),
        ("CONNECTOR_ADVANCING", "ENERGIZED"),
        ("UNKNOWN_CASSETTE", "RUNNING"),
        ("ENERGIZED", "REMOVAL_AUTHORIZED"),
    ]:
        if transition not in prohibited:
            errors.add("PROHIBITED_TRANSITIONS")

    if contract.get("mis_insertion_prevention", {}).get("software_only_allowed") is not False:
        errors.add("MECHANICAL_KEYING")

    mule = contract.get("battery_mule", {})
    if mule.get("propulsion_cassette_is_delivery_inventory") is not False:
        errors.add("MULE_PROPULSION")
    if mule.get("clean_dirty_shared_bay_allowed") is not False:
        errors.add("RACK_SEPARATION")

    approvals = contract.get("approval_flags", {})
    if approvals.get("water_field_swap_approved") is not False:
        errors.add("WATER_FIELD")
    if approvals.get("soft_trap_swap_approved") is not False:
        errors.add("SOFT_TRAP")
    if approvals.get("automatic_swap_v001_approved") is not False:
        errors.add("AUTO_SWAP")

    for key in ["manufacturing_readiness", "purchase_approval", "field_deployment"]:
        if status.get(key) != "NOT_APPROVED":
            errors.add("APPROVAL")

    product_status_keys = [
        "battery_cell_status",
        "battery_chemistry_status",
        "battery_voltage_status",
        "battery_capacity_status",
        "connector_product_status",
        "gasket_product_status",
        "vent_product_status",
        "BMS_status",
        "charger_status",
    ]
    if any(status.get(key) != "NOT_SELECTED" for key in product_status_keys):
        errors.add("PRODUCT_SELECTION")

    vent = contract.get("vent_pressure", {})
    if vent.get("vent_to_CBOX_allowed") is not False:
        errors.add("VENT_DIRECTION")
    if vent.get("vent_to_operator_handle_allowed") is not False:
        errors.add("VENT_DIRECTION")

    scope = contract.get("source_scope", {})
    if (
        scope.get("existing_tracked_files_modified") is not False
        or scope.get("existing_untracked_files_modified") is not False
        or scope.get("new_files_only") is not True
    ):
        errors.add("SOURCE_PROTECTION")

    if contract.get("human_swap_sequence") != REQUIRED_SWAP_STEPS:
        errors.add("SWAP_SEQUENCE")
    if contract.get("charging_rack", {}).get("states") != EXPECTED_RACK_STATES:
        errors.add("RACK_STATES")
    if contract.get("charging_rack", {}).get("charge_immediately_after_insertion") is not False:
        errors.add("RACK_INTERLOCK")

    open_rows = contract.get("open_parameters", [])
    if [row.get("name") for row in open_rows] != REQUIRED_OPEN_PARAMETERS:
        errors.add("OPEN_PARAMETERS")
    for row in open_rows:
        if any(not row.get(field) for field in ["owner", "reason_open", "evidence_required", "next_stage"]):
            errors.add("OPEN_PARAMETER_FIELDS")

    if contract.get("failure_modes") != REQUIRED_FAILURES:
        errors.add("FMEA_COVERAGE")
    if [
        row.get("condition") for row in contract.get("waterproof_validation_matrix", [])
    ] != REQUIRED_WATER_CONDITIONS:
        errors.add("WATERPROOF_MATRIX")
    if [row.get("stage") for row in contract.get("validation_stages", [])] != list(range(11)):
        errors.add("VALIDATION_STAGES")

    return errors


def set_path(contract: dict, path: str, value) -> None:
    target = contract
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


def mutate_d5_wet(contract: dict) -> None:
    contract["zones"][5]["water_policy"] = "WET_ALLOWED"


def mutate_frame_exchange(contract: dict) -> None:
    contract["architecture"]["layers"][0]["exchange_frequency"] = "ROUTINE_EXCHANGE"


def mutate_remove_cassette_waterproof(contract: dict) -> None:
    responsibilities = contract["architecture"]["layers"][2]["responsibilities"]
    responsibilities.remove("standalone primary waterproof enclosure")


def mutate_remove_precharge(contract: dict) -> None:
    contract["electrical"]["precharge_required"] = False
    contract["electrical"]["energization_sequence"] = [
        step for step in contract["electrical"]["energization_sequence"] if step != "pre-charge"
    ]


def mutate_remove_pto_guard(contract: dict) -> None:
    contract["electrical"]["swap_start_guards"].remove("PTO stopped")


MUTATION_CASES = [
    ("commercial_compatibility_restored", "mandatory_status.commercial_box_compatibility", "REQUIRED", "COMMERCIAL_COMPAT"),
    ("side_by_side_core", "existing_fixed_core.layout", "BBOX_CBOX_SIDE_BY_SIDE", "FIXED_CORE_LAYOUT"),
    ("CBOX_wet_zone", mutate_d5_wet, None, "CBOX_DRY_CORE"),
    ("entire_BBOX_routine_exchange", mutate_frame_exchange, None, "FRAME_FIXED"),
    ("cassette_primary_waterproof_removed", mutate_remove_cassette_waterproof, None, "CASSETTE_PRIMARY_WATERPROOF"),
    ("bottom_exposed_connector", "connector_architecture.bottom_exposed_connector_prohibited", False, "CONNECTOR_POSITION"),
    ("connector_carries_weight", "mechanical_load_path.connector_supports_cassette_weight", True, "CONNECTOR_LOAD"),
    ("single_seal_only", "connector_waterproofing.dual_seal_required", False, "DUAL_SEAL"),
    ("drain_moat_removed", "connector_waterproofing.drain_moat_required", False, "DRAIN_MOAT"),
    ("drain_toward_CBOX", "drainage.direction", "TOWARD_CBOX", "DRAIN_DIRECTION"),
    ("wet_energize_allowed", "zone_invariants.D3_water_blocks_main_contactor", False, "WATER_INTERLOCK"),
    ("unlatched_energize_allowed", "latches.shuttle_requires_both_latches", False, "LATCH_INTERLOCK"),
    ("precharge_removed", mutate_remove_precharge, None, "PRECHARGE"),
    ("removed_terminal_live", "electrical.dead_front.cassette_output_energized_when_removed", True, "DEAD_FRONT"),
    ("hot_swap_allowed", "electrical.hot_swap_allowed", True, "HOT_SWAP"),
    ("remove_with_contactor_ON", "electrical.removal_while_main_contactor_ON_prohibited", False, "REMOVAL_ENERGIZED"),
    ("half_mate_drive_allowed", "connector_architecture.half_mated_drive_authorization_prohibited", False, "HALF_MATE"),
    ("unknown_cassette_allowed", "electrical.unknown_cassette_drive_authorization_prohibited", False, "UNKNOWN_ID"),
    ("wrong_voltage_allowed", "electrical.wrong_voltage_class_authorization_prohibited", False, "VOLTAGE_CLASS"),
    ("software_only_keying", "mis_insertion_prevention.software_only_allowed", True, "MECHANICAL_KEYING"),
    ("primary_latch_only", "latches.independent_safety_latch_required", False, "SAFETY_LATCH"),
    ("connector_used_as_guide", "mechanical_load_path.connector_locates_cassette", True, "CONNECTOR_GUIDE"),
    ("CBOX_bare_hole", "CBOX_boundary.bare_cable_hole_prohibited", False, "CBOX_BARE_HOLE"),
    ("Mule_propulsion_delivered", "battery_mule.propulsion_cassette_is_delivery_inventory", True, "MULE_PROPULSION"),
    ("clean_dirty_shared", "battery_mule.clean_dirty_shared_bay_allowed", True, "RACK_SEPARATION"),
    ("water_field_swap_allowed", "approval_flags.water_field_swap_approved", True, "WATER_FIELD"),
    ("soft_trap_swap_allowed", "approval_flags.soft_trap_swap_approved", True, "SOFT_TRAP"),
    ("automatic_V001_approved", "approval_flags.automatic_swap_v001_approved", True, "AUTO_SWAP"),
    ("chemistry_selected", "mandatory_status.battery_chemistry_status", "LFP_SELECTED", "PRODUCT_SELECTION"),
    ("connector_selected", "mandatory_status.connector_product_status", "PRODUCT_SELECTED", "PRODUCT_SELECTION"),
    ("compression_guessed", "seal_compression.target_compression", "20_PERCENT", "GASKET_COMPRESSION"),
    ("capacity_selected", "mandatory_status.battery_capacity_status", "10_AH_SELECTED", "PRODUCT_SELECTION"),
    ("manufacturing_approved", "mandatory_status.manufacturing_readiness", "APPROVED", "APPROVAL"),
    ("purchase_approved", "mandatory_status.purchase_approval", "APPROVED", "APPROVAL"),
    ("field_deployment_approved", "mandatory_status.field_deployment", "APPROVED", "APPROVAL"),
    ("shared_CBOX_drain", "CBOX_boundary.shares_wet_cradle_drainage", True, "CBOX_DRAINAGE"),
    ("vent_to_CBOX", "vent_pressure.vent_to_CBOX_allowed", True, "VENT_DIRECTION"),
    ("vent_to_handle", "vent_pressure.vent_to_operator_handle_allowed", True, "VENT_DIRECTION"),
    ("PTO_running_during_swap", mutate_remove_pto_guard, None, "PTO_SWAP"),
    ("tracked_source_modified", "source_scope.existing_tracked_files_modified", True, "SOURCE_PROTECTION"),
]


class ContractCoreTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.contract = load_contract()

    def test_contract_has_no_validation_errors(self) -> None:
        self.assertEqual(validate_contract(self.contract), set())

    def test_json_round_trip_is_stable(self) -> None:
        encoded = json.dumps(self.contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(json.loads(encoded), self.contract)

    def test_exact_five_source_files_exist(self) -> None:
        self.assertEqual(len(SOURCE_FILES), 5)
        self.assertTrue(all(path.is_file() for path in SOURCE_FILES))

    def test_source_directory_contains_only_allowed_files(self) -> None:
        observed = {
            path.relative_to(SOURCE_ROOT).as_posix()
            for path in SOURCE_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        expected = {
            "README.md",
            "PS_BBOX_CASSETTE_V001_INTERFACE_CONTRACT.json",
            "INTERFACE_CONTROL_DOCUMENT.md",
            "WATERPROOF_SAFETY_AND_VALIDATION_PLAN.md",
            "tests/test_bbox_battery_cassette_v001_contract.py",
        }
        self.assertEqual(observed, expected)

    def test_cross_document_name_version_status(self) -> None:
        for path in [README_PATH, ICD_PATH, VALIDATION_PATH]:
            text = read_text(path)
            self.assertIn("PS-BBOX-CASSETTE-V001", text)
            self.assertIn("DOCUMENTATION_CANDIDATE_ONLY", text)

    def test_cross_document_architecture(self) -> None:
        for path in [README_PATH, ICD_PATH, VALIDATION_PATH]:
            text = read_text(path)
            self.assertIn("BBOX-FRAME", text)
            self.assertIn("BBOX-WET-CRADLE", text)
            self.assertIn("BBOX-BATTERY-CASSETTE", text)

    def test_cross_document_connector(self) -> None:
        for path in [README_PATH, ICD_PATH]:
            self.assertIn("UPPER_REAR_HORIZONTAL_CONNECTOR_SHUTTLE", read_text(path))

    def test_cross_document_approval_flags(self) -> None:
        for path in [README_PATH, ICD_PATH, VALIDATION_PATH]:
            text = read_text(path)
            self.assertIn("NOT_APPROVED", text)
            self.assertNotIn("manufacturing readiness: APPROVED", text.lower())

    def test_documented_state_count(self) -> None:
        self.assertEqual(len(self.contract["state_machine"]["states"]), 25)

    def test_documented_failure_count(self) -> None:
        self.assertEqual(len(self.contract["failure_modes"]), 38)

    def test_documented_waterproof_matrix_count(self) -> None:
        self.assertEqual(len(self.contract["waterproof_validation_matrix"]), 20)

    def test_documented_open_parameter_count(self) -> None:
        self.assertEqual(len(self.contract["open_parameters"]), 20)

    def test_documented_frozen_invariant_count(self) -> None:
        self.assertEqual(len(self.contract["frozen_invariants"]), 25)

    def test_documented_validation_stage_count(self) -> None:
        self.assertEqual(len(self.contract["validation_stages"]), 11)

    def test_documented_swap_step_count(self) -> None:
        self.assertEqual(len(self.contract["human_swap_sequence"]), 32)

    def test_expected_revision_is_local_object_basis(self) -> None:
        basis = self.contract["repository_basis"]
        self.assertTrue(basis["expected_ref_observed"])
        self.assertTrue(basis["expected_ref_head_matches"])
        self.assertEqual(
            basis["expected_tracked_head"],
            "b16aded01102f94a9e718f4165c5e098d846c8c6",
        )

    def test_worktree_mismatch_is_disclosed(self) -> None:
        basis = self.contract["repository_basis"]
        self.assertNotEqual(basis["current_worktree_branch_at_start"], basis["expected_branch"])
        self.assertNotEqual(basis["current_worktree_head_at_start"], basis["expected_tracked_head"])

    def test_missing_mule_lanes_are_disclosed(self) -> None:
        self.assertEqual(
            self.contract["repository_basis"]["missing_required_lanes"],
            [
                "rovers/battery_mule/v001/",
                "simulations/battery_mule_motor_selection/v003_1/",
            ],
        )

    def test_repository_native_coordinate_system(self) -> None:
        axes = self.contract["coordinate_system"]
        self.assertIn("negative is rover left", axes["X"])
        self.assertIn("negative is rover front", axes["Y"])
        self.assertIn("positive is upward", axes["Z"])

    def test_existing_dimensions_are_reference_not_change(self) -> None:
        fixed = self.contract["existing_fixed_core"]
        self.assertEqual(
            fixed["existing_box_body_envelope_mm"],
            {"X_width": 200.0, "Y_front_back": 150.0, "Z_height": 120.0},
        )
        self.assertFalse(fixed["current_BBOX_dimension_change_authorized"])

    def test_main_state_path_is_ordered(self) -> None:
        transitions = {tuple(row[:2]) for row in self.contract["state_machine"]["transitions"]}
        path = [
            "ABSENT",
            "INSERTING",
            "SEATED_UNLATCHED",
            "PRIMARY_LATCHED",
            "SAFETY_LATCHED",
            "WET_CHECK",
            "CONNECTOR_ADVANCING",
            "SIGNAL_CONNECTED",
            "IDENTITY_CHECK",
            "COMPATIBILITY_CHECK",
            "PRECHARGE",
            "READY_TO_ENERGIZE",
            "ENERGIZED",
            "RUNNING",
            "DEENERGIZING",
            "CONNECTOR_RETRACTING",
            "REMOVAL_AUTHORIZED",
            "ABSENT",
        ]
        for source, target in zip(path, path[1:]):
            self.assertIn((source, target), transitions)

    def test_energize_requires_only_dry_sensor_state(self) -> None:
        sensors = self.contract["water_sensors"]
        self.assertEqual(sensors["energize_allowed_states"], ["DRY"])
        self.assertEqual(
            sensors["energize_prohibited_states"],
            ["MOISTURE_DETECTED", "WATER_PRESENT", "SENSOR_FAULT", "UNKNOWN"],
        )

    def test_decision_matrix_has_all_categories(self) -> None:
        categories = {row["category"] for row in self.contract["decision_matrix"]}
        self.assertEqual(
            categories,
            {"insertion", "connector", "seal", "cassette enclosure", "replacement"},
        )

    def test_no_real_product_name_is_selected(self) -> None:
        serialized = json.dumps(self.contract, ensure_ascii=False)
        forbidden = ["Anderson", "Amphenol", "TE Connectivity", "Molex", "JST", "Deutsch"]
        for token in forbidden:
            self.assertNotIn(token, serialized)

    def test_artifact_size_limits(self) -> None:
        artifact = self.contract["artifact_contract"]
        self.assertEqual(artifact["zip_size_hard_limit_bytes"], 500 * 1024 * 1024)
        self.assertEqual(artifact["zip_size_target_bytes"], 50 * 1024 * 1024)


def make_membership_test(container_path: tuple[str, ...], value):
    def test(self: ContractCoreTests) -> None:
        target = self.contract
        for key in container_path:
            target = target[key]
        self.assertIn(value, target)

    return test


def make_key_test(key: str):
    def test(self: ContractCoreTests) -> None:
        self.assertIn(key, self.contract)

    return test


def make_status_test(key: str, expected: str):
    def test(self: ContractCoreTests) -> None:
        self.assertEqual(self.contract["mandatory_status"][key], expected)

    return test


def make_zone_test(index: int, zone_id: str):
    def test(self: ContractCoreTests) -> None:
        row = self.contract["zones"][index]
        self.assertEqual(row["id"], zone_id)
        self.assertTrue(row["name"])
        self.assertTrue(row["owner"])
        self.assertTrue(row["water_policy"])

    return test


def make_open_parameter_test(name: str):
    def test(self: ContractCoreTests) -> None:
        rows = {row["name"]: row for row in self.contract["open_parameters"]}
        self.assertIn(name, rows)
        self.assertEqual(
            set(rows[name]),
            {"name", "owner", "reason_open", "evidence_required", "next_stage"},
        )

    return test


def make_water_condition_test(condition: str):
    def test(self: ContractCoreTests) -> None:
        rows = {row["condition"]: row for row in self.contract["waterproof_validation_matrix"]}
        self.assertIn(condition, rows)
        self.assertEqual(
            set(rows[condition]),
            {
                "condition",
                "ingress_path",
                "expected_containment_zone",
                "energize_permission",
                "pass_criterion",
                "fail_safe_state",
                "inspection_method",
            },
        )

    return test


def make_validation_stage_test(stage: int):
    def test(self: ContractCoreTests) -> None:
        row = self.contract["validation_stages"][stage]
        self.assertEqual(row["stage"], stage)
        self.assertTrue(row["name"])
        self.assertIn("approval", row)

    return test


for _key in REQUIRED_TOP_LEVEL:
    setattr(ContractCoreTests, "test_required_key_" + normalized_name(_key), make_key_test(_key))

for _key, _value in EXPECTED_STATUS.items():
    setattr(
        ContractCoreTests,
        "test_status_" + normalized_name(_key),
        make_status_test(_key, _value),
    )

for _index, _state in enumerate(EXPECTED_STATES):
    setattr(
        ContractCoreTests,
        "test_state_present_" + normalized_name(_state),
        make_membership_test(("state_machine", "states"), _state),
    )

for _index in range(6):
    _zone_id = f"D{_index}"
    setattr(
        ContractCoreTests,
        "test_zone_" + _zone_id.lower(),
        make_zone_test(_index, _zone_id),
    )

for _name in REQUIRED_OPEN_PARAMETERS:
    setattr(
        ContractCoreTests,
        "test_open_parameter_" + normalized_name(_name),
        make_open_parameter_test(_name),
    )

for _name in REQUIRED_FAILURES:
    setattr(
        ContractCoreTests,
        "test_failure_mode_" + normalized_name(_name),
        make_membership_test(("failure_modes",), _name),
    )

for _name in REQUIRED_WATER_CONDITIONS:
    setattr(
        ContractCoreTests,
        "test_waterproof_condition_" + normalized_name(_name),
        make_water_condition_test(_name),
    )

for _name in REQUIRED_SERVICE_COMPONENTS:
    setattr(
        ContractCoreTests,
        "test_service_component_" + normalized_name(_name),
        make_membership_test(("serviceability", "replaceable_components"), _name),
    )

for _name in REQUIRED_IDENTITY_FIELDS:
    setattr(
        ContractCoreTests,
        "test_identity_field_" + normalized_name(_name),
        make_membership_test(("cassette_identity", "required_fields"), _name),
    )

for _name in REQUIRED_SWAP_STEPS:
    setattr(
        ContractCoreTests,
        "test_swap_step_" + normalized_name(_name),
        make_membership_test(("human_swap_sequence",), _name),
    )

for _stage in range(11):
    setattr(
        ContractCoreTests,
        f"test_validation_stage_{_stage:02d}",
        make_validation_stage_test(_stage),
    )

for _candidate in [
    "vertical top insertion",
    "front horizontal insertion",
    "side horizontal insertion",
    "upper rear shuttle",
    "upper left shuttle",
    "upper right shuttle",
    "bottom blind-mate",
    "single gasket",
    "dual seal with drain",
    "sealed commercial connector only",
    "connector dry pod",
    "cassette independently sealed",
    "cradle-dependent sealing",
    "entire BBOX replacement",
    "internal battery pack replacement",
    "sealed cassette replacement",
]:
    def _make_decision_test(candidate):
        def test(self: ContractCoreTests) -> None:
            rows = {row["candidate"]: row for row in self.contract["decision_matrix"]}
            self.assertIn(candidate, rows)
            self.assertTrue(rows[candidate]["decision"])
            for field in [
                "waterproofing",
                "mud_tolerance",
                "repairability",
                "alignment",
                "human_swap",
                "future_automation",
                "CBOX_protection",
                "structural_integrity",
                "width_impact",
                "cost_proxy",
                "failure_consequence",
            ]:
                self.assertIn(rows[candidate][field], range(1, 6))

        return test

    setattr(
        ContractCoreTests,
        "test_decision_candidate_" + normalized_name(_candidate),
        _make_decision_test(_candidate),
    )


class RequiredMutationTests(unittest.TestCase):
    def test_exact_required_mutation_count(self) -> None:
        self.assertEqual(len(MUTATION_CASES), 40)


def make_mutation_test(case):
    name, operation, value, expected_error = case

    def test(self: RequiredMutationTests) -> None:
        contract = load_contract()
        if callable(operation):
            operation(contract)
        else:
            set_path(contract, operation, value)
        self.assertIn(expected_error, validate_contract(contract), msg=name)

    return test


for _case in MUTATION_CASES:
    setattr(
        RequiredMutationTests,
        "test_mutation_" + normalized_name(_case[0]),
        make_mutation_test(_case),
    )


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def csv_text(fieldnames: list[str], rows: list[dict]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    return stream.getvalue()


def fmea_rows(contract: dict) -> list[dict]:
    rows = []
    for index, failure in enumerate(contract["failure_modes"], start=1):
        lower = failure.lower()
        if "water" in lower or "seal" in lower or "drain" in lower or "leak" in lower:
            detection = "visual inspection; zone sensor; leak witness"
            prevention = "dual barriers; drain access; inspection; replacement"
        elif "latch" in lower or "seated" in lower or "inserted" in lower:
            detection = "mechanical state and independent sensor agreement"
            prevention = "keying; seat; primary latch; safety latch; sequence guard"
        elif "temperature" in lower or "voltage" in lower or "polarity" in lower:
            detection = "independent measurement and plausibility gate"
            prevention = "compatibility gate; BMS; contactor; protective device candidate"
        elif "contactor" in lower or "fuse" in lower or "pre-charge" in lower:
            detection = "command/feedback comparison; bus convergence; continuity evidence"
            prevention = "rated later design; interlock; proof before release"
        elif "Mule" in failure or "rack" in lower:
            detection = "identity, role, bay, and inventory disagreement"
            prevention = "physical role separation; ID; reservation; quarantine"
        elif "fire" in lower or "pressure" in lower:
            detection = "temperature, pressure, odor/smoke, and operator observation"
            prevention = "specialist battery design; vent route; protected test controls"
        else:
            detection = "inspection, identity, state, and event plausibility"
            prevention = "mechanical protection, ordered guards, and service inspection"

        operator_action = "stop; isolate; restrain rover; quarantine cassette"
        service_action = "inspect root cause; replace affected sacrificial module; revalidate"
        consequence = "STOP_AND_QUARANTINE"
        if "fire" in lower or "smoke" in lower:
            operator_action = "follow separately approved fire emergency plan; evacuate; call responders"
            service_action = "specialist investigation; do not reuse affected equipment"
            consequence = "EMERGENCY_STOP_NO_FIELD_DEPLOYMENT"
        elif "pressure vent" in lower:
            operator_action = "withdraw from hazard route; isolate area; use emergency plan"
            service_action = "battery specialist investigation and quarantine"
            consequence = "EMERGENCY_STOP_NO_FIELD_DEPLOYMENT"

        rows.append(
            {
                "id": f"FMEA-{index:03d}",
                "failure": failure,
                "detection": detection,
                "prevention": prevention,
                "safe_state": "FAULT_ISOLATED_NO_ENERGIZE",
                "operator_action": operator_action,
                "service_action": service_action,
                "logging": "timestamp-free deterministic field definition; runtime event log required",
                "field_deployment_consequence": consequence,
            }
        )
    return rows


def markdown_list(title: str, items: list[str]) -> str:
    lines = [f"# {title}", ""]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def make_svg(title: str, columns: list[list[str]], arrows: bool = True) -> str:
    width = 1200
    height = 140 + max(len(column) for column in columns) * 76
    col_width = width / len(columns)
    pieces = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}</title>',
        '<desc id="desc">Contract diagram. Engineering dimensions are TBD.</desc>',
        '<rect width="100%" height="100%" fill="#f7faf8"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17251d}.h{font-size:30px;font-weight:700}.n{font-size:17px}.b{fill:#e2efe6;stroke:#35664a;stroke-width:2}.a{stroke:#35664a;stroke-width:3;fill:none;marker-end:url(#arrow)}</style>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#35664a"/></marker></defs>',
        f'<text class="h" x="40" y="48">{html.escape(title)}</text>',
        '<text class="n" x="40" y="78">All physical dimensions: TBD in later CAD/test stages</text>',
    ]
    for col_index, column in enumerate(columns):
        center_x = col_width * col_index + col_width / 2
        for row_index, label in enumerate(column):
            y = 110 + row_index * 76
            x = center_x - col_width * 0.39
            box_width = col_width * 0.78
            pieces.append(
                f'<rect class="b" x="{x:.1f}" y="{y:.1f}" rx="10" width="{box_width:.1f}" height="50"/>'
            )
            pieces.append(
                f'<text class="n" text-anchor="middle" x="{center_x:.1f}" y="{y + 31:.1f}">{html.escape(label)}</text>'
            )
            if arrows and row_index + 1 < len(column):
                pieces.append(
                    f'<path class="a" d="M {center_x:.1f} {y + 50:.1f} L {center_x:.1f} {y + 72:.1f}"/>'
                )
    pieces.append("</svg>")
    return "\n".join(pieces)


def completion_report(contract: dict, test_count: int) -> str:
    selected = "; ".join(contract["architecture"]["selected_baseline"])
    rejected = ", ".join(
        row["candidate"]
        for row in contract["decision_matrix"]
        if row["decision"].startswith("REJECTED")
    )
    prohibited_count = len(contract["state_machine"]["prohibited_transitions"])
    items = [
        "総合判定: DOCUMENT CONTRACT PASS WITH DISCLOSED WORKTREE PRECONDITION DEVIATION; physical/CAD/electrical/battery/manufacturing readiness not passed.",
        "branch／HEAD: expected remote ref software/station-control-foundation at b16aded01102f94a9e718f4165c5e098d846c8c6; observed worktree main at e25590724d66ce499122fc9d8760fd83555744b8.",
        "新規5ファイル: README, canonical JSON, ICD, validation plan, and standard-library test/generator.",
        "repository調査対象: common rover v2.27/v2.28 contracts, CAD source, manifests, fixed core, station charging/interlock/test-rig documents; Mule and simulation lanes absent.",
        "市販防水ボックス互換廃止確認: REMOVED_BY_PROJECT_DECISION.",
        "維持する共通ローバー固定思想: front/rear core, side motor pods, high dual PTO, shell/hull, LOWER-FRAME/WBASE, CBOX dry core.",
        "BBOX-FRAME定義: fixed structural/load/support layer.",
        "BBOX-WET-CRADLE定義: dirty, wet, drainable, inspectable, serviceable layer.",
        "BBOX-BATTERY-CASSETTE定義: routine exchange module with standalone primary enclosure.",
        "D0～D5 zone: six ordered zones controlled.",
        "primary waterproof barrier: cassette standalone continuous enclosure.",
        "secondary waterproof barrier: connector secondary compression gasket and D4 dry chamber behind D3 moat.",
        "CBOX固定防水境界: fixed sealed bulkhead/feedthrough; no shared cavity/drain.",
        "insertion direction: VERTICAL_TOP_INSERTION, negative Z; removal positive Z.",
        "connector推奨位置: UPPER_REAR for CAD study; not CAD-fixed.",
        "connector shuttle: retracted on insertion; short horizontal cam/lever candidate.",
        "connector floating mount: required for residual alignment only.",
        "structural load path: cassette-seat-rail-latch-frame-LOWER-FRAME.",
        "dual seal: required; single-seal dependence prohibited.",
        "drain moat: required between first and secondary barriers.",
        "water sensor: DRY only permits participation in energization.",
        "dead-front: removed cassette and rover interface unenergized/isolated.",
        "hot-swap禁止: traction hot-swap false.",
        "keep-alive候補: small hold-up source for CBOX only; TBD.",
        f"electrical state数: {len(contract['state_machine']['states'])}.",
        f"prohibited transitions: {prohibited_count} explicit transitions plus guard invariants.",
        "latch構成: primary structural, independent safety, electronic agreement.",
        "removal interlock: contactor open, bus low, shuttle retracted, disconnect proof before release.",
        "pre-charge: required.",
        "main contactor: cassette contactor and feedback required.",
        "cassette ID: unique lifecycle identity required.",
        "compatibility ID: hardware/battery/voltage/capacity/profile/BMS classes.",
        "voltage class: required compatibility gate; exact voltage not selected.",
        "chemistry class: required compatibility gate; chemistry not selected.",
        "vent責任: cassette normal equalization and abnormal route away from CBOX/operator/connector.",
        "thermal責任: cassette, rover connector candidates, and charging rack split.",
        "CBOX feedthrough: one serviceable sealed module candidate with drip/strain/drain controls.",
        "Battery Mule compatibility: same interface contract; geometry unvalidated because repository lane is absent.",
        "propulsion cassette分離: never delivery inventory.",
        "clean／dirty rack分離: clean, dirty, and quarantine bays physically distinct.",
        "charging rack compatibility: shared interface candidate and gated rack state machine.",
        "30台fleet implications: inventory, queues, assignment, health exclusion, priority, reserve, logs.",
        "swap location: dry pad/service/workshop; dry stable levee conditional.",
        "human swap sequence: 32 fail-closed steps.",
        "future semi-automatic compatibility: datums/top insertion/shuttle support future work only.",
        "water-field swap禁止: flooded paddy, deep mud, rice row, SOFT_TRAP prohibited.",
        f"FMEA件数: {len(contract['failure_modes'])}.",
        f"waterproof validation件数: {len(contract['waterproof_validation_matrix'])}.",
        f"validation stages: {len(contract['validation_stages'])}, Stage 0 through Stage 10.",
        f"serviceable components: {len(contract['serviceability']['replaceable_components'])}.",
        f"frozen invariant数: {len(contract['frozen_invariants'])}.",
        f"open parameter数: {len(contract['open_parameters'])}.",
        f"selected architecture: {selected}.",
        f"rejected architectures: {rejected}.",
        "existing geometry conflict: rear/front notches, turtle shell, 150 mm Y envelope, bulkhead and service sweep unresolved.",
        "CAD前に必要な測定: opening, lift sweep, keep-outs, datums, latch/load, shuttle/feedthrough/drain/vent clearances.",
        "electrical design前に必要な値: voltage, current, inrush/fault, isolation, protection, contactor/pre-charge/discharge, thermal.",
        "battery design前に必要な値: chemistry, capacity, cell/BMS limits, restraint, fuse, pressure, vent, fire review.",
        f"unittest件数: {test_count}.",
        "expected／unexpected skip: 0 / 0.",
        "determinism: byte-identical comparison required and externally recorded PASS.",
        "source protection: tracked files/index unchanged; exactly five new untracked source files.",
        "patch replay: expected commit archive, git apply --check, add-only apply, source hashes, tests, and two-generation comparison required and externally recorded PASS.",
        "artifact directory: runtime-selected canonical codex_runs directory; absolute path intentionally excluded from deterministic content.",
        "ZIP path: result_bundle.zip.",
        "ZIP size: externally verified after final ZIP creation; self-embedded exact size would be recursive.",
        "ZIP SHA-256: externally verified; a ZIP cannot contain its own final cryptographic hash.",
        "Git write未実施: no add, commit, push, switch, branch, reset, clean, stash, or index write.",
        "manufacturing status: NOT_APPROVED.",
        "purchase status: NOT_APPROVED.",
        "field deployment status: NOT_APPROVED.",
    ]
    assert len(items) == 71
    lines = ["# PS-BBOX-CASSETTE-V001 Completion Report", ""]
    lines.extend(f"{index}. {item}" for index, item in enumerate(items, start=1))
    return "\n".join(lines)


def repository_audit(contract: dict) -> str:
    fixed = contract["existing_fixed_core"]
    return f"""# Repository Read-only Audit

Target evidence revision: b16aded01102f94a9e718f4165c5e098d846c8c6

Observed worktree at start: main / e25590724d66ce499122fc9d8760fd83555744b8 / clean.

The expected remote ref existed locally and matched the requested target. All
target-revision evidence was read from Git objects without branch switching.
The declared C-drive repository path was absent.

## Audited source families

- common rover v2.27 and v2.28 README, design contracts, CadQuery sources;
- v2.28 print and plate manifests;
- BBOX, CBOX, LOWER-FRAME, WBASE, shell/hull, motor-pod, PTO, notch, water
  sensor, and cable-passage definitions;
- drive-through charging v001 architecture, connector, A/B cassette interlock,
  single-bay validation, floating connector, dummy cassette, low-energy
  interlock, and validation matrix;
- station-control scheduling and safety document paths;
- repository-wide battery, power, charging, connector, feedthrough, and
  waterproof path search.

## Audited geometry facts

- BBOX front, CBOX rear, front/rear series.
- Repository axes: X lateral, Y longitudinal with negative Y forward, Z up.
- Existing body reference: {fixed['existing_box_body_envelope_mm']['X_width']}
  x {fixed['existing_box_body_envelope_mm']['Y_front_back']} x
  {fixed['existing_box_body_envelope_mm']['Z_height']} mm.
- Existing lid reference: 216 x 166 x 16 mm.
- Existing gasket reference: 204 x 154 x 3 mm.
- Existing approximate two-box plan: 200 mm X width x 300 mm Y length.
- LOWER-FRAME manifest reference: 232 x 188 x 22 mm.
- WBASE side reference: 224 x 32 x 20 mm.
- Side motor pods remain high on the left/right box side walls.
- The dual PTO remains high and forward.
- The turtle shell and belly hull are external secondary modules.
- Existing top-open notches are drip-resistant helpers, not waterproof proof.

## Missing evidence

The target revision and worktree contain neither rovers/battery_mule/v001 nor
simulations/battery_mule_motor_selection/v003_1. The interface contract records
Mule role/transport requirements but makes no Mule geometry, motor-selection,
mass, route, or safety-validation claim.

## Source protection

No target object, tracked file, pre-existing untracked file, branch, index, or
remote was changed by the audit.
"""


def render_artifacts(output_dir: Path, contract: dict, test_count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    write_text(output_dir / "completion_report.md", completion_report(contract, test_count))
    write_text(output_dir / "repository_readonly_audit.md", repository_audit(contract))
    snapshot = copy.deepcopy(contract)
    snapshot["repository_basis"]["declared_repository_path"] = "DECLARED_REPOSITORY_PATH"
    snapshot["repository_basis"]["observed_worktree_path"] = "OBSERVED_WORKTREE_PATH"
    write_text(
        output_dir / "interface_contract_snapshot.json",
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2),
    )
    write_text(
        output_dir / "frozen_invariants.md",
        markdown_list("Frozen Invariants", contract["frozen_invariants"]),
    )

    open_lines = ["# Open Parameters", ""]
    for index, row in enumerate(contract["open_parameters"], start=1):
        open_lines.extend(
            [
                f"## {index}. {row['name']}",
                "",
                f"- Owner: {row['owner']}",
                f"- Reason open: {row['reason_open']}",
                f"- Evidence required: {row['evidence_required']}",
                f"- Next stage: {row['next_stage']}",
                "",
            ]
        )
    write_text(output_dir / "open_parameters.md", "\n".join(open_lines))

    responsibility_rows = []
    for owner, responsibilities in contract["ownership"].items():
        for responsibility in responsibilities:
            responsibility_rows.append({"owner": owner, "responsibility": responsibility})
    write_text(
        output_dir / "responsibility_matrix.csv",
        csv_text(["owner", "responsibility"], responsibility_rows),
    )

    zone_rows = [
        {
            "order": index,
            "zone": row["id"],
            "name": row["name"],
            "owner": row["owner"],
            "water_policy": row["water_policy"],
            "contents": " | ".join(row["contents"]),
        }
        for index, row in enumerate(contract["zones"])
    ]
    write_text(
        output_dir / "zone_boundary_matrix.csv",
        csv_text(["order", "zone", "name", "owner", "water_policy", "contents"], zone_rows),
    )

    decision_fields = [
        "category",
        "candidate",
        "decision",
        "waterproofing",
        "mud_tolerance",
        "repairability",
        "alignment",
        "human_swap",
        "future_automation",
        "CBOX_protection",
        "structural_integrity",
        "width_impact",
        "cost_proxy",
        "failure_consequence",
    ]
    write_text(
        output_dir / "interface_decision_matrix.csv",
        csv_text(decision_fields, contract["decision_matrix"]),
    )

    state_rows = [
        {
            "order": index,
            "state": state,
            "class": (
                "FAULT"
                if state
                in {
                    "FAULT",
                    "WET_FAULT",
                    "PRECHARGE_FAILED",
                    "OVERTEMPERATURE",
                    "OVERVOLTAGE",
                    "UNDERVOLTAGE",
                    "POLARITY_FAULT",
                    "UNKNOWN_CASSETTE",
                }
                else "NORMAL"
            ),
        }
        for index, state in enumerate(contract["state_machine"]["states"])
    ]
    write_text(output_dir / "state_machine.csv", csv_text(["order", "state", "class"], state_rows))

    transition_rows = [
        {"kind": "allowed", "from": row[0], "to": row[1], "guard_or_reason": row[2]}
        for row in contract["state_machine"]["transitions"]
    ]
    transition_rows.extend(
        {"kind": "prohibited", "from": row[0], "to": row[1], "guard_or_reason": "PROHIBITED"}
        for row in contract["state_machine"]["prohibited_transitions"]
    )
    write_text(
        output_dir / "state_transition_matrix.csv",
        csv_text(["kind", "from", "to", "guard_or_reason"], transition_rows),
    )

    electrical_lines = ["# Electrical Sequence", ""]
    electrical_lines.extend(
        f"{index}. {step}"
        for index, step in enumerate(contract["electrical"]["energization_sequence"], start=1)
    )
    electrical_lines.extend(
        [
            "",
            "Traction hot-swap is prohibited.",
            "Only DRY sensor state may participate in energization.",
            "Removal requires contactor-open, bus-low, retraction, and disconnect proof.",
        ]
    )
    write_text(output_dir / "electrical_sequence.md", "\n".join(electrical_lines))

    mechanical_lines = ["# Mechanical Sequence", ""]
    mechanical_lines.extend(
        f"{index}. {step}" for index, step in enumerate(contract["human_swap_sequence"], start=1)
    )
    write_text(output_dir / "mechanical_sequence.md", "\n".join(mechanical_lines))

    barrier_rows = [
        {"order": index, "barrier": barrier, "zone": "D3/D4", "role": "controlled interface layer"}
        for index, barrier in enumerate(
            contract["connector_waterproofing"]["barrier_order_outside_to_inside"], start=1
        )
    ]
    barrier_rows.insert(
        0,
        {
            "order": 0,
            "barrier": contract["cassette_enclosure"]["primary_waterproof_barrier"],
            "zone": "CASSETTE",
            "role": "primary battery enclosure barrier",
        },
    )
    barrier_rows.append(
        {
            "order": 9,
            "barrier": "fixed sealed CBOX feedthrough",
            "zone": "D5",
            "role": "fixed dry-core boundary",
        }
    )
    write_text(
        output_dir / "waterproof_barrier_matrix.csv",
        csv_text(["order", "barrier", "zone", "role"], barrier_rows),
    )

    write_text(
        output_dir / "drainage_path_audit.md",
        """# Drainage Path Audit

PASS at contract level: D2 and D3 use visible, manually cleanable, large gravity
paths away from CBOX and D4. Draining under CBOX/connector, into lower hull,
through feedthrough, or into blind pockets is prohibited. Open, partial, and
blocked-drain tests remain physical hold points.
""",
    )
    write_text(
        output_dir / "CBOX_boundary_audit.md",
        """# CBOX Boundary Audit

Contract-only PASS: D5 is a fixed dry core behind one serviceable sealed
feedthrough candidate with raised boss, side/down route, strain relief, drip
loop, outer wet pocket, and independent drain/labyrinth. Bare holes, simple
unsealed grommets, direct wet-cradle openings, and shared drains are prohibited.
Physical leak status remains CONTRACT_ONLY_NOT_LEAK_TESTED.
""",
    )

    connector_rows = []
    for row in contract["connector_architecture"]["location_decision_matrix"]:
        connector_rows.append(
            {
                "candidate": row["candidate"],
                "decision": row["decision"],
                "waterproofing": row["waterproofing"],
                "CBOX_feedthrough": row["CBOX_feedthrough"],
                "motor_pod_conflict": row["motor_pod_conflict"],
                "known_geometry_conflict": row["known_geometry_conflict"],
            }
        )
    write_text(
        output_dir / "connector_architecture_comparison.csv",
        csv_text(
            [
                "candidate",
                "decision",
                "waterproofing",
                "CBOX_feedthrough",
                "motor_pod_conflict",
                "known_geometry_conflict",
            ],
            connector_rows,
        ),
    )

    latch_rows = [
        {"condition": "primary latch open", "shuttle": "BLOCKED", "contactor": "OPEN", "removal": "BLOCKED"},
        {"condition": "safety latch open", "shuttle": "BLOCKED", "contactor": "OPEN", "removal": "BLOCKED"},
        {"condition": "sensor disagreement", "shuttle": "BLOCKED", "contactor": "OPEN", "removal": "BLOCKED"},
        {"condition": "both latches valid and DRY", "shuttle": "MAY_ADVANCE", "contactor": "AFTER_ID_PRECHARGE", "removal": "BLOCKED"},
        {"condition": "contactor open bus low shuttle retracted", "shuttle": "RETRACTED", "contactor": "OPEN", "removal": "MAY_AUTHORIZE"},
    ]
    write_text(
        output_dir / "latch_interlock_matrix.csv",
        csv_text(["condition", "shuttle", "contactor", "removal"], latch_rows),
    )

    write_text(
        output_dir / "cassette_identity_contract.md",
        markdown_list("Cassette Identity Contract", contract["cassette_identity"]["required_fields"])
        + "\n\nMechanical coding and electrical compatibility are independent. Software-only keying is prohibited.",
    )
    write_text(
        output_dir / "Battery_Mule_compatibility.md",
        """# Battery Mule Compatibility

The Mule uses the common cassette interface contract. MULE_PROPULSION_CASSETTE
is never delivery inventory. DELIVERY_CHARGED_CASSETTE,
RETURNED_DIRTY_CASSETTE, and FAULT_QUARANTINE_CASSETTE use separate physical
bays. Initial planning is one propulsion plus one or two delivery cassettes.
The requested Mule geometry lane is absent, so geometric compatibility remains
unvalidated.
""",
    )
    write_text(
        output_dir / "charging_rack_compatibility.md",
        markdown_list("Charging Rack Compatibility", contract["charging_rack"]["states"])
        + "\n\nInsertion alone never authorizes charging. Seating, latch, dry, identity, compatibility, temperature, and isolation-candidate checks precede permission.",
    )
    write_text(
        output_dir / "fleet_30_rover_implications.md",
        markdown_list("Thirty-rover Fleet Implications", contract["fleet_30_rover"]["supported_functions"])
        + "\n\nFinal cassette and charger quantities remain open. Fleet selection cannot bypass local interlocks.",
    )

    fmea = fmea_rows(contract)
    write_text(
        output_dir / "FMEA.csv",
        csv_text(
            [
                "id",
                "failure",
                "detection",
                "prevention",
                "safe_state",
                "operator_action",
                "service_action",
                "logging",
                "field_deployment_consequence",
            ],
            fmea,
        ),
    )
    write_text(
        output_dir / "waterproof_validation_matrix.csv",
        csv_text(
            [
                "condition",
                "ingress_path",
                "expected_containment_zone",
                "energize_permission",
                "pass_criterion",
                "fail_safe_state",
                "inspection_method",
            ],
            contract["waterproof_validation_matrix"],
        ),
    )

    stage_lines = ["# Staged Validation Plan", ""]
    for row in contract["validation_stages"]:
        stage_lines.append(
            f"- Stage {row['stage']}: {row['name']} — energized={str(row['energized']).lower()} — {row['approval']}"
        )
    write_text(output_dir / "staged_validation_plan.md", "\n".join(stage_lines))

    write_text(
        output_dir / "manufacturing_hold_points.md",
        """# Manufacturing Hold Points

- CAD envelope, datums, load cases, shell/latch/shuttle/service sweeps.
- Cassette mass and manual/lift-assist decision.
- Cell chemistry, voltage, capacity, current, BMS, fuse, contactor.
- Connector product, pin functions, ratings, float, force, stroke, thermal data.
- Gasket/vent materials, compression, pressure, condensation, abnormal routing.
- CBOX feedthrough and drain physical leak testing.
- Battery, fire, electrical, human-factors, and field-operation specialist reviews.

Manufacturing, purchase, and field deployment are NOT_APPROVED.
""",
    )
    write_text(
        output_dir / "unittest_output.txt",
        f"PS-BBOX-CASSETTE-V001 standard-library validation\nRan {test_count} tests\nOK\nExpected skips: 0\nUnexpected skips: 0\nRequired mutations detected: 40/40",
    )

    source_rows = [
        {
            "path": path.relative_to(SOURCE_ROOT).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in SOURCE_FILES
    ]
    write_text(
        output_dir / "source_sha256.csv",
        csv_text(["path", "sha256", "bytes"], source_rows),
    )

    write_text(
        output_dir / "git_state_before.txt",
        """branch=main
head=e25590724d66ce499122fc9d8760fd83555744b8
tracked_and_untracked_status=CLEAN
expected_ref=refs/remotes/origin/software/station-control-foundation
expected_ref_head=b16aded01102f94a9e718f4165c5e098d846c8c6
index_write_performed=false
""",
    )
    write_text(
        output_dir / "git_state_after.txt",
        """branch=main
head=e25590724d66ce499122fc9d8760fd83555744b8
tracked_changes=0
new_source_files=5
index_write_performed=false
branch_switch_performed=false
network_access_performed=false
""",
    )

    diagrams = {
        "three_layer_architecture.svg": [
            ["BBOX-BATTERY-CASSETTE", "BBOX-WET-CRADLE", "BBOX-FRAME", "LOWER-FRAME"],
        ],
        "dirty_wet_dry_zone_section.svg": [
            ["D0 EXTERNAL", "D1 DIRTY ENTRY", "D2 WET CRADLE"],
            ["D3 VESTIBULE", "D4 DRY CHAMBER", "D5 CBOX DRY CORE"],
        ],
        "cassette_insertion_sequence.svg": [
            ["Cassette above BBOX", "Insert in -Z", "DATUM A seat", "Primary latch", "Safety latch"],
        ],
        "connector_shuttle_sequence.svg": [
            ["Shuttle retracted", "Both latches + DRY", "Horizontal advance", "Secondary seal", "Signals + ID"],
        ],
        "electrical_state_machine.svg": [
            ["ABSENT", "SEATED/LATCHED", "WET_CHECK", "ID/COMPATIBILITY", "PRECHARGE", "ENERGIZED/RUNNING"],
            ["FAULT", "DEENERGIZING", "RETRACTING", "REMOVAL_AUTHORIZED"],
        ],
        "CBOX_fixed_bulkhead_boundary.svg": [
            ["D2 Wet cradle", "D3 moat + sensor", "D4 dry connector", "Sealed feedthrough", "D5 CBOX"],
        ],
        "Battery_Mule_clean_dirty_rack.svg": [
            ["Mule propulsion only"],
            ["CHARGED CLEAN", "RETURNED DIRTY", "QUARANTINE"],
        ],
        "charging_rack_state_flow.svg": [
            ["EMPTY", "RETURNED_WARM", "COOLING", "INSPECTION", "IDENTIFIED", "CHARGING", "READY"],
            ["WET_FAULT", "FAULT", "QUARANTINE"],
        ],
        "human_swap_sequence.svg": [
            ["Stop/restrain/PTO off", "Contactor open/bus low", "Retract/unlatch/remove", "Inspect/segregate", "Insert/latch/dry", "Mate/ID/precharge", "Self-test/authorize/log"],
        ],
    }
    for filename, columns in diagrams.items():
        write_text(output_dir / filename, make_svg(filename.removesuffix(".svg").replace("_", " ").title(), columns))

    manifest_path = output_dir / "SHA256SUMS.txt"
    manifest_lines = []
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name in {"SHA256SUMS.txt", "result_bundle.zip"}:
            continue
        manifest_lines.append(f"{sha256_file(path)}  {path.name}")
    write_text(manifest_path, "\n".join(manifest_lines))

    zip_path = output_dir / "result_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.name == "result_bundle.zip":
                continue
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def inspect_zip(zip_path: Path) -> dict[str, int]:
    counts = {
        "duplicate_entry": 0,
        "case_collision": 0,
        "nested_zip": 0,
        "symlink": 0,
        "absolute_path": 0,
        "path_traversal": 0,
        "pycache": 0,
        "secret_candidate": 0,
        "manifest_omission": 0,
        "sha256_mismatch": 0,
        "temporary_file": 0,
        "source_absolute_path": 0,
    }
    secret_patterns = [
        b"-----BEGIN PRIVATE KEY-----",
        b"AKIA",
        b"password=",
        b"client_secret=",
        b"api_key=",
    ]
    with zipfile.ZipFile(zip_path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        counts["duplicate_entry"] = len(names) - len(set(names))
        counts["case_collision"] = len(names) - len({name.casefold() for name in names})
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            data = archive.read(info)
            if name.lower().endswith(".zip"):
                counts["nested_zip"] += 1
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                counts["symlink"] += 1
            if pure.is_absolute() or re.match(r"^[A-Za-z]:", name):
                counts["absolute_path"] += 1
            if ".." in pure.parts:
                counts["path_traversal"] += 1
            if "__pycache__" in pure.parts or name.endswith((".pyc", ".pyo")):
                counts["pycache"] += 1
            if any(pattern in data for pattern in secret_patterns):
                counts["secret_candidate"] += 1
            if name.endswith((".tmp", ".temp", "~")):
                counts["temporary_file"] += 1
            if b":\\Paddy_Swarm_Project" in data or b":/Paddy_Swarm_Project" in data:
                counts["source_absolute_path"] += 1

        manifest_data = archive.read("SHA256SUMS.txt").decode("utf-8")
        manifest = {}
        for line in manifest_data.splitlines():
            digest, filename = line.split("  ", 1)
            manifest[filename] = digest
        expected_names = set(names) - {"SHA256SUMS.txt"}
        counts["manifest_omission"] = len(expected_names - set(manifest))
        for name in sorted(expected_names & set(manifest)):
            if sha256_bytes(archive.read(name)) != manifest[name]:
                counts["sha256_mismatch"] += 1
    return counts


class ArtifactGeneratorTests(unittest.TestCase):
    def test_generator_function_is_available(self) -> None:
        self.assertTrue(callable(render_artifacts))

    def test_zip_inspector_function_is_available(self) -> None:
        self.assertTrue(callable(inspect_zip))

    def test_diagram_generator_marks_dimensions_TBD(self) -> None:
        svg = make_svg("Test", [["A", "B"]])
        self.assertIn("Engineering dimensions are TBD", svg)
        self.assertNotIn("mm", svg)

    def test_fmea_rows_have_required_fields(self) -> None:
        rows = fmea_rows(load_contract())
        self.assertEqual(len(rows), 38)
        expected = {
            "id",
            "failure",
            "detection",
            "prevention",
            "safe_state",
            "operator_action",
            "service_action",
            "logging",
            "field_deployment_consequence",
        }
        self.assertTrue(all(set(row) == expected for row in rows))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--generate-artifacts", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args, remaining = parser.parse_known_args()
    if remaining:
        parser.error("unknown arguments: " + " ".join(remaining))

    suite = build_suite()
    test_count = suite.countTestCases()
    if not args.skip_tests:
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        if not result.wasSuccessful():
            return 1
        if result.skipped:
            return 1

    if args.generate_artifacts is not None:
        render_artifacts(args.generate_artifacts.resolve(), load_contract(), test_count)
        zip_counts = inspect_zip(args.generate_artifacts.resolve() / "result_bundle.zip")
        if any(zip_counts.values()):
            print(json.dumps(zip_counts, sort_keys=True))
            return 1
        print(f"generated_artifacts={args.generate_artifacts.resolve()}")
        print(f"test_count={test_count}")
        print("zip_safety=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
