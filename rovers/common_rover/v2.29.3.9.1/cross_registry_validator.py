from __future__ import annotations

from collections import Counter, defaultdict
from branch_probe import declare, hit

declare(
    "anchor_count_ok", "anchor_count_bad", "zone_id_present", "zone_id_missing",
    "zone_unique", "zone_unknown", "zone_multiple", "host_match", "host_mismatch",
    "side_match", "side_mismatch", "face_match", "face_mismatch",
    "semantic_match", "semantic_mismatch", "slot_host_match", "slot_host_mismatch",
    "position_match", "position_mismatch", "deprecated_clear", "deprecated_reference",
    "mapping_unique", "mapping_missing", "mapping_duplicate", "mirror_match", "mirror_mismatch",
    "lower_bottom", "lower_conflict", "upper_top", "upper_conflict",
)


def compare_anchor(anchor, zone, host_slot):
    blockers = []
    if anchor.get("canonical_host_component") != zone.get("host_component"):
        hit("host_mismatch")
        blockers.append("CROSS_REGISTRY_HOST_MISMATCH")
    else:
        hit("host_match")
    if anchor.get("side") != zone.get("side"):
        hit("side_mismatch")
        blockers.append("CROSS_REGISTRY_SIDE_MISMATCH")
    else:
        hit("side_match")
    if anchor.get("normalized_slot_face") != zone.get("normalized_slot_face"):
        hit("face_mismatch")
        blockers.append("CROSS_REGISTRY_SLOT_FACE_MISMATCH")
    else:
        hit("face_match")
    if anchor.get("semantic_qualifier") != zone.get("semantic_qualifier"):
        hit("semantic_mismatch")
        blockers.append("CROSS_REGISTRY_SEMANTIC_MISMATCH")
    else:
        hit("semantic_match")
    if (
        host_slot is None
        or host_slot.get("host_component") != anchor.get("canonical_host_component")
        or host_slot.get("slot_id") != anchor.get("host_slot_id")
        or not host_slot.get("t_nut_permitted")
    ):
        hit("slot_host_mismatch")
        blockers.append("CROSS_REGISTRY_SLOT_HOST_MISMATCH")
    else:
        hit("slot_host_match")
    if anchor.get("position_mode") != zone.get("position_mode"):
        hit("position_mismatch")
        blockers.append("CROSS_REGISTRY_POSITION_MODE_MISMATCH")
    else:
        hit("position_match")
    if anchor.get("deprecated_reference"):
        hit("deprecated_reference")
        blockers.append("CROSS_REGISTRY_DEPRECATED_REFERENCE")
    else:
        hit("deprecated_clear")
    if anchor.get("mirror_zone_id") != zone.get("mirror_pair"):
        hit("mirror_mismatch")
        blockers.append("CROSS_REGISTRY_MIRROR_MISMATCH")
    else:
        hit("mirror_match")
    return blockers


def validate_cross_registry(fastener, slot_authority, mapping, host_authority, expectations):
    anchors = fastener.get("body_tslot_anchor_records", [])
    expected_count = expectations.get("BODY_TSLOT_ANCHOR_COUNT", 60)
    blockers = []
    if len(anchors) != expected_count:
        hit("anchor_count_bad")
        blockers.append("BODY_TSLOT_ANCHOR_COUNT_MISMATCH")
    else:
        hit("anchor_count_ok")
    zones_by_id = defaultdict(list)
    for zone in slot_authority.get("zones", []):
        zones_by_id[zone.get("zone_id")].append(zone)
    slots_by_id = {slot["slot_id"]: slot for slot in host_authority.get("slots", [])}
    mapping_by_anchor = defaultdict(list)
    for row in mapping.get("mappings", []):
        mapping_by_anchor[row.get("anchor_instance_id")].append(row)
    rows = []
    counts = Counter()
    checked_ids = []
    for anchor in anchors:
        aid = anchor.get("current_anchor_instance_id")
        zone_id = anchor.get("slot_zone_id")
        if not zone_id:
            hit("zone_id_missing")
            counts["without_zone_id"] += 1
            blockers.append("BODY_TSLOT_ANCHOR_WITHOUT_ZONE_ID")
            continue
        hit("zone_id_present")
        matches = zones_by_id.get(zone_id, [])
        if not matches:
            hit("zone_unknown")
            counts["unknown_zone"] += 1
            blockers.append("UNKNOWN_SLOT_ZONE_ID")
            continue
        if len(matches) != 1:
            hit("zone_multiple")
            counts["multiple_zone"] += 1
            blockers.append("MULTIPLE_ZONE_MATCH")
            continue
        hit("zone_unique")
        map_matches = mapping_by_anchor.get(aid, [])
        if not map_matches:
            hit("mapping_missing")
            counts["unchecked"] += 1
            blockers.append("UNCHECKED_BODY_TSLOT_ANCHOR")
            continue
        if len(map_matches) != 1:
            hit("mapping_duplicate")
            counts["duplicate_checked"] += 1
            blockers.append("DUPLICATE_CHECKED_ANCHOR")
            continue
        hit("mapping_unique")
        map_row = map_matches[0]
        zone = matches[0]
        row_blockers = []
        if map_row.get("slot_zone_id") != zone_id:
            row_blockers.append("CROSS_REGISTRY_ZONE_MISMATCH")
        row_blockers += compare_anchor(anchor, zone, slots_by_id.get(anchor.get("host_slot_id")))
        for code in row_blockers:
            counts[code] += 1
            blockers.append(code)
        checked_ids.append(aid)
        rows.append({
            "anchor_instance_id": aid,
            "slot_zone_id": zone_id,
            "host_component": anchor.get("canonical_host_component"),
            "side": anchor.get("side"),
            "normalized_slot_face": anchor.get("normalized_slot_face"),
            "semantic_qualifier": anchor.get("semantic_qualifier"),
            "host_slot_id": anchor.get("host_slot_id"),
            "status": "PASS" if not row_blockers else "FAIL",
            "blockers": row_blockers,
        })
    lower = [a for a in anchors if a.get("slot_zone_id") in {"LOWER-ADAPTER-L", "LOWER-ADAPTER-R"}]
    lower_conflicts = sum(
        a.get("normalized_slot_face") != "BOTTOM_SLOT"
        or a.get("host_slot_id") not in {"RAIL-L-BOTTOM", "RAIL-R-BOTTOM"}
        for a in lower
    )
    if len(lower) == 8 and lower_conflicts == 0:
        hit("lower_bottom")
    else:
        hit("lower_conflict")
        blockers.append("LOWER_ADAPTER_SLOT_CONFLICT")
    torque = [a for a in anchors if a.get("slot_zone_id") == "UPPER-TORQUE-MOUNT"]
    torque_conflicts = sum(
        a.get("normalized_slot_face") != "TOP_SLOT"
        or a.get("semantic_qualifier") != "TOP_SLOT_OF_FRONT_CROSSMEMBER"
        or a.get("host_slot_id") != "XMEMBER-TOP"
        for a in torque
    )
    if len(torque) == 4 and torque_conflicts == 0:
        hit("upper_top")
    else:
        hit("upper_conflict")
        blockers.append("UPPER_TORQUE_SLOT_CONFLICT")
    checked_unique = len(set(checked_ids))
    unchecked = expected_count - checked_unique
    return {
        "status": "PASS" if not blockers else "FAIL",
        "BODY_TSLOT_ANCHOR_COUNT": len(anchors),
        "CROSS_REGISTRY_CHECKED_ANCHOR_COUNT": len(checked_ids),
        "UNCHECKED_BODY_TSLOT_ANCHOR_COUNT": max(0, unchecked),
        "DUPLICATE_CHECKED_ANCHOR_COUNT": counts["duplicate_checked"],
        "BODY_TSLOT_ANCHOR_WITHOUT_ZONE_ID_COUNT": counts["without_zone_id"],
        "UNKNOWN_SLOT_ZONE_ID_COUNT": counts["unknown_zone"],
        "MULTIPLE_ZONE_MATCH_COUNT": counts["multiple_zone"],
        "CROSS_REGISTRY_HOST_MISMATCH_COUNT": counts["CROSS_REGISTRY_HOST_MISMATCH"],
        "CROSS_REGISTRY_SIDE_MISMATCH_COUNT": counts["CROSS_REGISTRY_SIDE_MISMATCH"],
        "CROSS_REGISTRY_SLOT_FACE_MISMATCH_COUNT": counts["CROSS_REGISTRY_SLOT_FACE_MISMATCH"],
        "CROSS_REGISTRY_SEMANTIC_MISMATCH_COUNT": counts["CROSS_REGISTRY_SEMANTIC_MISMATCH"],
        "CROSS_REGISTRY_ZONE_MISMATCH_COUNT": counts["CROSS_REGISTRY_ZONE_MISMATCH"],
        "CROSS_REGISTRY_SLOT_HOST_MISMATCH_COUNT": counts["CROSS_REGISTRY_SLOT_HOST_MISMATCH"],
        "CROSS_REGISTRY_POSITION_MODE_MISMATCH_COUNT": counts["CROSS_REGISTRY_POSITION_MODE_MISMATCH"],
        "CROSS_REGISTRY_DEPRECATED_REFERENCE_COUNT": counts["CROSS_REGISTRY_DEPRECATED_REFERENCE"],
        "LOWER_ADAPTER_ANCHOR_COUNT": len(lower),
        "LOWER_ADAPTER_SLOT_CONFLICT_COUNT": lower_conflicts,
        "LOWER_ADAPTER_NON_BOTTOM_ANCHOR_COUNT": lower_conflicts,
        "UPPER_TORQUE_ANCHOR_COUNT": len(torque),
        "UPPER_TORQUE_SLOT_CONFLICT_COUNT": torque_conflicts,
        "UPPER_TORQUE_REAR_FACE_ANCHOR_COUNT": sum(
            a.get("normalized_slot_face") == "REAR_FACE_SLOT" for a in torque
        ),
        "rows": rows,
        "blockers": sorted(set(blockers)),
    }
