from __future__ import annotations
import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = "PS_IMAGE_REVIEW_RECEIPT_V2"
REVIEWER_TYPES = {
    "HUMAN", "CHATGPT_VISION", "OTHER_APPROVED_VISION_REVIEWER",
}
DECISIONS = {"PASS", "CONDITIONAL_PASS", "FAIL"}
ITEM_RESULTS = {"PASS", "FAIL", "NOT_VISIBLE", "NOT_APPLICABLE"}
REQUIRED_REVIEW_ITEMS = (
    "orientation_correct", "hole_face", "mounting_face",
    "rail_crossmember_joint", "visible_thin_wall", "disconnected_body",
    "tool_access", "structural_overlap", "boolean_residue",
)
CRITICAL_ITEMS = set(REQUIRED_REVIEW_ITEMS)

def canonical_payload(receipt):
    return {
        key: value for key, value in receipt.items()
        if key != "receipt_sha256"
    }

def receipt_sha256(receipt):
    return hashlib.sha256(json.dumps(
        canonical_payload(receipt), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()

def map_receipt_decision(decision):
    return {
        "PASS": "PASS_EXTERNAL_RECEIPT",
        "CONDITIONAL_PASS": "CONDITIONAL_EXTERNAL_RECEIPT",
        "FAIL": "FAIL_EXTERNAL_RECEIPT",
    }.get(decision, "FAIL_EXTERNAL_RECEIPT")

def create_receipt_template(expected, image_rows):
    return {
        **expected,
        "receipt_schema_version": SCHEMA_VERSION,
        "reviewer_type": "", "reviewer_name_or_id": "",
        "pipeline_generated": False, "overall_decision": "",
        "reviewed_image_files": [
            {"filename": row["filename"], "sha256": row["file_sha256"]}
            for row in image_rows
        ],
        "per_view_reviews": [
            {
                "view": row["view"], "note": "",
                "items": {
                    item: "NOT_VISIBLE" for item in REQUIRED_REVIEW_ITEMS
                },
            }
            for row in image_rows
        ],
        "blocking_issues": [], "required_reinspection": [],
        "receipt_sha256": "",
        "template_status": "UNSIGNED_PENDING_EXTERNAL_REVIEW",
    }

def validate_review_receipt(receipt, expected, image_rows):
    errors = []
    for field in (
        "loop_id", "part_id", "revision", "image_manifest_sha256",
        "source_geometry_fingerprint",
    ):
        if receipt.get(field) != expected.get(field):
            errors.append(f"{field} mismatch")
    if receipt.get("reviewer_type") not in REVIEWER_TYPES:
        errors.append("reviewer type unapproved")
    if not str(receipt.get("reviewer_name_or_id", "")).strip():
        errors.append("reviewer identity missing")
    if receipt.get("pipeline_generated"):
        errors.append("pipeline-generated receipt forbidden")
    decision = receipt.get("overall_decision")
    if decision not in DECISIONS:
        errors.append("invalid decision")
    expected_files = {
        Path(row["filename"]).name: row["file_sha256"] for row in image_rows
    }
    reviewed_files = {
        Path(row.get("filename", "")).name: row.get("sha256")
        for row in receipt.get("reviewed_image_files", [])
    }
    if reviewed_files != expected_files:
        errors.append("reviewed file/hash set mismatch")
    expected_views = {row["view"] for row in image_rows}
    reviews = {
        row.get("view"): row for row in receipt.get("per_view_reviews", [])
    }
    if set(reviews) != expected_views:
        errors.append("per-view review set mismatch")
    critical_not_visible = []
    for view, review in reviews.items():
        if not str(review.get("note", "")).strip():
            errors.append(f"{view}: empty note")
        items = review.get("items", {})
        if set(items) != set(REQUIRED_REVIEW_ITEMS):
            errors.append(f"{view}: review item set mismatch")
        for item, result in items.items():
            if result not in ITEM_RESULTS:
                errors.append(f"{view}:{item}: invalid result")
            if item in CRITICAL_ITEMS and result == "NOT_VISIBLE":
                critical_not_visible.append(f"{view}:{item}")
    blocking = len(receipt.get("blocking_issues", []))
    reinspection = len(receipt.get("required_reinspection", []))
    if critical_not_visible and not reinspection:
        errors.append("critical NOT_VISIBLE requires reinspection")
    if decision == "PASS" and (blocking or reinspection or critical_not_visible):
        errors.append("PASS cannot contain blocking/reinspection/critical NOT_VISIBLE")
    supplied_hash = receipt.get("receipt_sha256", "")
    if supplied_hash != receipt_sha256(receipt):
        errors.append("receipt hash invalid")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors, "overall_decision": decision,
        "mapped_review_status": (
            map_receipt_decision(decision) if not errors
            else "FAIL_EXTERNAL_RECEIPT"
        ),
        "blocking_issue_count": blocking,
        "required_reinspection_count": reinspection,
        "critical_not_visible_count": len(critical_not_visible),
        "reviewed_image_set_complete": reviewed_files == expected_files,
        "active_revision_match": receipt.get("revision") == expected.get("revision"),
        "image_hashes_match": reviewed_files == expected_files,
        "source_fingerprint_match": (
            receipt.get("source_geometry_fingerprint")
            == expected.get("source_geometry_fingerprint")
        ),
    }
