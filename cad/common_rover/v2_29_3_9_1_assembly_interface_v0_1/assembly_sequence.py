from __future__ import annotations

from typing import Any


BATTERY_SEQUENCE = (
    "cassette insert",
    "guide to seat",
    "primary latch close",
    "safety latch close",
    "sensor verification",
    "connector shuttle movement",
    "secondary seal compression",
    "low-energy signal confirmation",
    "ID / voltage / polarity / temperature verification",
    "pre-charge",
    "voltage-difference confirmation",
    "main contactor",
    "drive authorization",
)

CONNECTOR_SHUTTLE_CANDIDATES = (
    "UPPER_REAR_HORIZONTAL_CONNECTOR_SHUTTLE",
    "UPPER_SIDE_HORIZONTAL_CONNECTOR_SHUTTLE",
    "UPPER_LEFT",
    "UPPER_RIGHT",
)


def build_assembly_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "action": "Assemble FPB aluminum frame",
            "interfaces": ["AI-01"],
            "tool": "one hex-key size candidate",
            "verify": "FRONT, LEFT, RIGHT marks and butt-face contact",
        },
        {
            "step": 2,
            "action": "Verify both metal corner brackets",
            "interfaces": ["AI-01"],
            "tool": "visual + hex key",
            "verify": "all bracket bolt heads and seams visible",
        },
        {
            "step": 3,
            "action": "Install CBOX positioning saddles on metal cradle",
            "interfaces": ["AI-02"],
            "tool": "one hex-key size candidate",
            "verify": "A1/A2 and FRONT keys agree",
        },
        {
            "step": 4,
            "action": "Install independent rear BBOX support",
            "interfaces": ["AI-03"],
            "tool": "one hex-key size candidate",
            "verify": "B1/B2 visible; authority dimensions remain HOLD",
        },
        {
            "step": 5,
            "action": "Drop CBOX into saddle",
            "interfaces": ["AI-02"],
            "tool": "hands / gloves",
            "verify": "CBOX reaches positive stop at A1/A2",
        },
        {
            "step": 6,
            "action": "Drop BBOX onto independent rear support",
            "interfaces": ["AI-03"],
            "tool": "hands / gloves",
            "verify": "BBOX reaches B1/B2; no vertical support from CBOX",
        },
        {
            "step": 7,
            "action": "Install visible anti-separation lock",
            "interfaces": ["AI-04"],
            "tool": "metal pin / clamp candidate",
            "verify": "A2/B1 window and retained pin visible",
        },
        {
            "step": 8,
            "action": "Install lower float adapters on BOTTOM_SLOT",
            "interfaces": ["AI-05"],
            "tool": "one hex-key size candidate",
            "verify": "L1/L2 and lower bolt heads visible",
        },
        {
            "step": 9,
            "action": "1 INSERT each float receiver",
            "interfaces": ["AI-06"],
            "tool": "hands / gloves",
            "verify": "LEFT/RIGHT asymmetric keys enter",
        },
        {
            "step": 10,
            "action": "2 SLIDE rearward to positive stop",
            "interfaces": ["AI-06"],
            "tool": "hands / gloves",
            "verify": "F1/F2 witness lines and pin windows align",
        },
        {
            "step": 11,
            "action": "3 LOCK with metal pin and R-pin",
            "interfaces": ["AI-07"],
            "tool": "hands / optional drift",
            "verify": "pin head and R-pin both visible",
        },
        {
            "step": 12,
            "action": "4 VERIFY every visible indicator",
            "interfaces": [f"AI-{index:02d}" for index in range(1, 10)],
            "tool": "visual / gloved touch check",
            "verify": "no hidden lock; all witness marks show seated/locked",
        },
    ]


def build_disassembly_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": index,
            "action": f"Reverse assembly step {row['step']}: {row['action']}",
            "interfaces": list(row["interfaces"]),
            "tool": row["tool"],
            "verify": (
                "Confirm released state before the next load-bearing part is moved"
            ),
        }
        for index, row in enumerate(
            reversed(build_assembly_steps()), start=1
        )
    ]


def field_service_evaluation() -> dict[str, Any]:
    return {
        "status": "PASS_WITH_HOLD",
        "glove_access": True,
        "hidden_fasteners": False,
        "pin_head_visible": True,
        "r_pin_visible": True,
        "mud_release_features": [
            "open-ended slide channels",
            "downward drain slots",
            "two-sided pin drift access",
            "thumb-latch pry notch for secondary cover only",
        ],
        "tool_count_target": 2,
        "tools": [
            "one hex-key size",
            "optional pin drift / cleaning brush",
        ],
        "hold": (
            "Mud-packed release must be verified on physical coupons and a "
            "non-operational mock-up."
        ),
    }


def battery_reservation() -> dict[str, Any]:
    return {
        "sequence": list(BATTERY_SEQUENCE),
        "connector_structural_load": False,
        "candidate_shuttles": list(CONNECTOR_SHUTTLE_CANDIDATES),
        "selected_shuttle": None,
        "comparison_only": True,
        "manufacturing_geometry": False,
        "status": "HOLD",
    }
