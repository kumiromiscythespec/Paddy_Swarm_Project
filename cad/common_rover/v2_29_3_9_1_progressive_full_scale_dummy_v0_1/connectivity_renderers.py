from __future__ import annotations

from html import escape

from part_number_registry import ALL_PART_BY_KEY, CONNECTIVITY_PARTS
from physical_connection_model import AI10_RESERVATION


def _svg(title: str, width: int, height: int, body: list[str]) -> str:
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            "<style>",
            "text{font-family:Arial,sans-serif;fill:#17212b}"
            ".title{font-size:27px;font-weight:700}"
            ".label{font-size:15px;font-weight:700}"
            ".small{font-size:12px}"
            ".existing{fill:#b7c3cf;stroke:#35424e;stroke-width:2}"
            ".new{fill:#f2df54;stroke:#716400;stroke-width:2}"
            ".body{fill:#82c6bd;stroke:#215b57;stroke-width:2}"
            ".hold{fill:#fff3cd;stroke:#9a7200;stroke-width:2;stroke-dasharray:8 5}"
            ".pin{fill:#e87979;stroke:#7a2222;stroke-width:2}"
            ".arrow{stroke:#303b44;stroke-width:2;fill:none;marker-end:url(#arrow)}",
            "</style>",
            '<defs><marker id="arrow" markerWidth="10" markerHeight="7" '
            'refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" '
            'fill="#303b44"/></marker></defs>',
            f'<text x="28" y="42" class="title">{escape(title)}</text>',
            *body,
            "</svg>",
            "",
        )
    )

def profile3_connection_exploded_svg() -> str:
    body = [
        '<rect x="180" y="480" width="36" height="260" class="existing"/>',
        '<rect x="684" y="480" width="36" height="260" class="existing"/>',
        '<rect x="216" y="684" width="468" height="36" class="existing"/>',
        '<text x="360" y="708" class="label">EXISTING PROFILE-3 FPB</text>',
        '<path d="M142 660 L196 700 L236 660" class="new"/>',
        '<path d="M758 660 L704 700 L664 660" class="new"/>',
        '<text x="44" y="644" class="small">FRM-306 LEFT external sleeve</text>',
        '<text x="720" y="644" class="small">FRM-307 RIGHT external sleeve</text>',
        '<rect x="180" y="420" width="540" height="28" class="new"/>',
        '<text x="265" y="440" class="small">FRM-311 removable rear locator cross-tie</text>',
        '<rect x="265" y="335" width="370" height="52" class="existing"/>',
        '<text x="338" y="365" class="small">EXISTING REAR CRADLE HALVES</text>',
        '<rect x="420" y="320" width="60" height="82" class="new"/>',
        '<text x="386" y="308" class="small">FRM-308 center joiner</text>',
        '<rect x="214" y="342" width="52" height="45" class="new"/>',
        '<rect x="634" y="342" width="52" height="45" class="new"/>',
        '<text x="105" y="335" class="small">FRM-309 LEFT attachment</text>',
        '<text x="690" y="335" class="small">FRM-310 RIGHT attachment</text>',
        '<rect x="235" y="230" width="110" height="48" class="new"/>',
        '<rect x="555" y="230" width="110" height="48" class="new"/>',
        '<text x="205" y="216" class="small">BOX-307 saddle clip L</text>',
        '<text x="555" y="216" class="small">BOX-308 saddle clip R</text>',
        '<rect x="330" y="102" width="240" height="90" class="body"/>',
        '<text x="362" y="135" class="label">REMOVABLE BODY DUMMIES</text>',
        '<text x="350" y="160" class="small">connected seats; no structural claim</text>',
        '<path d="M450 478 L450 451" class="arrow"/>',
        '<path d="M450 416 L450 395" class="arrow"/>',
        '<path d="M450 315 L450 284" class="arrow"/>',
        '<path d="M450 225 L450 196" class="arrow"/>',
        '<rect x="45" y="70" width="810" height="22" class="hold"/>',
        '<text x="55" y="86" class="small">AI-10 axial clearance NOT YET AUDITED — no pulley/belt geometry generated</text>',
        '<text x="40" y="790" class="label">All yellow parts: DUMMY ONLY / NO LOAD / NOT STRUCTURAL / PROFILE-3 ONLY</text>',
    ]
    return _svg("PROFILE-3 connected dry assembly — exploded", 900, 820, body)


def rear_cradle_connection_svg() -> str:
    body = [
        '<rect x="70" y="330" width="170" height="46" class="existing"/>',
        '<rect x="660" y="330" width="170" height="46" class="existing"/>',
        '<text x="100" y="360" class="small">CRADLE LEFT</text>',
        '<text x="690" y="360" class="small">CRADLE RIGHT</text>',
        '<rect x="238" y="318" width="130" height="70" class="new"/>',
        '<rect x="532" y="318" width="130" height="70" class="new"/>',
        '<text x="250" y="310" class="small">LEFT attachment</text>',
        '<text x="540" y="310" class="small">RIGHT attachment</text>',
        '<rect x="380" y="290" width="140" height="126" class="new"/>',
        '<text x="393" y="280" class="small">CENTER JOINER</text>',
        '<rect x="85" y="475" width="730" height="40" class="new"/>',
        '<text x="280" y="500" class="label">FPB-TO-REAR VISUAL LOCATOR</text>',
        '<path d="M240 352 L374 352" class="arrow"/>',
        '<path d="M660 352 L526 352" class="arrow"/>',
        '<circle cx="340" cy="352" r="9" class="pin"/>',
        '<circle cx="560" cy="352" r="9" class="pin"/>',
        '<text x="285" y="548" class="small">Visible removable pins; no glue/tape/T-nut/direct rail holes</text>',
        '<rect x="90" y="145" width="720" height="80" class="hold"/>',
        '<text x="110" y="175" class="label">Rear hardpoint / section / stiffness = HOLD</text>',
        '<text x="110" y="200" class="small">This drawing validates dry positioning connectivity only.</text>',
    ]
    return _svg("Rear cradle physical connection", 900, 600, body)


def cbox_saddle_attachment_svg() -> str:
    body = [
        '<rect x="100" y="440" width="700" height="42" class="existing"/>',
        '<text x="345" y="467" class="label">PROFILE-3 RAIL ENVELOPES</text>',
        '<rect x="135" y="330" width="220" height="76" class="new"/>',
        '<rect x="545" y="330" width="220" height="76" class="new"/>',
        '<text x="150" y="322" class="small">BOX-307 LEFT BASE CLIP</text>',
        '<text x="558" y="322" class="small">BOX-308 RIGHT BASE CLIP</text>',
        '<rect x="175" y="230" width="150" height="65" class="existing"/>',
        '<rect x="575" y="230" width="150" height="65" class="existing"/>',
        '<text x="185" y="220" class="small">EXISTING SADDLE L</text>',
        '<text x="585" y="220" class="small">EXISTING SADDLE R</text>',
        '<rect x="260" y="90" width="380" height="100" class="body"/>',
        '<text x="355" y="135" class="label">CBOX DUMMY</text>',
        '<path d="M250 326 L250 300" class="arrow"/>',
        '<path d="M650 326 L650 300" class="arrow"/>',
        '<path d="M450 225 L450 194" class="arrow"/>',
        '<text x="155" y="520" class="small">Clip channel captures saddle base and rail outer envelope; visible dummy pin retains.</text>',
        '<text x="155" y="545" class="small">Existing saddles and part numbers are unchanged.</text>',
    ]
    return _svg("CBOX saddle attachment — no loose placement", 900, 590, body)


def bbox_support_attachment_svg() -> str:
    body = [
        '<rect x="100" y="480" width="700" height="50" class="existing"/>',
        '<text x="325" y="512" class="label">CONNECTED REAR CRADLE</text>',
        '<rect x="170" y="380" width="180" height="70" class="new"/>',
        '<rect x="550" y="380" width="180" height="70" class="new"/>',
        '<text x="175" y="370" class="small">BOX-309 FRONT ANCHOR</text>',
        '<text x="555" y="370" class="small">BOX-310 REAR ANCHOR</text>',
        '<rect x="130" y="270" width="260" height="70" class="existing"/>',
        '<rect x="510" y="270" width="260" height="70" class="existing"/>',
        '<text x="170" y="260" class="small">EXISTING FRONT SUPPORT</text>',
        '<text x="550" y="260" class="small">EXISTING REAR SUPPORT</text>',
        '<rect x="245" y="90" width="410" height="130" class="body"/>',
        '<text x="382" y="135" class="label">BBOX DUMMY</text>',
        '<text x="290" y="165" class="small">removable; support anchors remain on frame</text>',
        '<path d="M260 375 L260 345" class="arrow"/>',
        '<path d="M640 375 L640 345" class="arrow"/>',
        '<path d="M450 265 L450 225" class="arrow"/>',
        '<text x="125" y="570" class="small">FRONT/REAR keys make spacing unique and reject lateral slide.</text>',
        '<text x="125" y="592" class="small">BBOX has no vertical support path through CBOX.</text>',
    ]
    return _svg("BBOX support attachment — frame-retained supports", 900, 630, body)


def float_adapter_profile3_attachment_svg() -> str:
    body = [
        '<rect x="150" y="110" width="600" height="70" class="existing"/>',
        '<text x="300" y="150" class="label">SLOTLESS 20x20 PROFILE-3 RAIL</text>',
        '<rect x="195" y="225" width="220" height="85" class="new"/>',
        '<rect x="485" y="225" width="220" height="85" class="new"/>',
        '<text x="210" y="215" class="small">FLT-305 OUTER CLAMP L</text>',
        '<text x="500" y="215" class="small">FLT-306 OUTER CLAMP R</text>',
        '<rect x="195" y="350" width="220" height="75" class="new"/>',
        '<rect x="485" y="350" width="220" height="75" class="new"/>',
        '<text x="205" y="342" class="small">FLT-307 LOCATOR L</text>',
        '<text x="495" y="342" class="small">FLT-308 LOCATOR R</text>',
        '<rect x="205" y="470" width="200" height="70" class="existing"/>',
        '<rect x="495" y="470" width="200" height="70" class="existing"/>',
        '<text x="220" y="462" class="small">EXISTING LOWER ADAPTER L</text>',
        '<text x="510" y="462" class="small">EXISTING LOWER ADAPTER R</text>',
        '<path d="M305 185 L305 220" class="arrow"/>',
        '<path d="M595 185 L595 220" class="arrow"/>',
        '<path d="M305 315 L305 345" class="arrow"/>',
        '<path d="M595 315 L595 345" class="arrow"/>',
        '<path d="M305 430 L305 465" class="arrow"/>',
        '<path d="M595 430 L595 465" class="arrow"/>',
        '<rect x="150" y="580" width="600" height="55" class="hold"/>',
        '<text x="175" y="604" class="label">Y=-125..-95 mm; representative anchor -110 mm</text>',
        '<text x="210" y="625" class="small">No slot tooth / T-nut / direct rail hole / structural claim</text>',
    ]
    return _svg("PROFILE-3 float adapter attachment", 900, 680, body)


def ai10_clearance_reservation_svg() -> str:
    rows = [
        AI10_RESERVATION["drive_candidate"],
        AI10_RESERVATION["pto_candidate"],
        AI10_RESERVATION["sync_candidate"],
        AI10_RESERVATION["downstream_candidate"],
        "Axial shaft length / bearing overhang / row spacing = HOLD",
        "Guard envelope / 300 mm width interference = HOLD",
        "Independent PTO neutral interlock = REQUIRED",
        "LOW-LOAD SPREADER ONLY",
    ]
    body = [
        '<rect x="60" y="80" width="780" height="450" class="hold"/>',
        '<text x="90" y="120" class="label">RESERVATION ONLY — NO PULLEY OR BELT GEOMETRY</text>',
    ]
    for index, row in enumerate(rows):
        body.append(
            f'<text x="100" y="{165 + index * 42}" class="label">'
            f'{escape(row)}</text>'
        )
    body.extend(
        (
            '<text x="90" y="565" class="label">AI10_CLEARANCE_STATUS = NOT_YET_AUDITED</text>',
            '<text x="90" y="595" class="small">Current dummy geometry does not guarantee axial space.</text>',
        )
    )
    return _svg("AI-10 PTO-DRIVE SYNC LINK v0.1", 900, 640, body)


def profile3_connection_manual() -> str:
    lines = [
        "# PROFILE-3 physical connection manual",
        "",
        "All parts in this correction are visual dry-assembly connectors only. "
        "They are not structural clamps and must be removed when a real "
        "aluminum profile is selected.",
        "",
        "## Mandatory prohibitions",
        "",
        "- Do not use a T-nut on the slotless PROFILE-3 rails.",
        "- Do not drill the rails or crossmember.",
        "- Do not use glue-only or tape-only retention.",
        "- Keep every connector number, key, pin, and seated witness visible.",
        "- Carry no operating, field, battery, drive, or structural load.",
        "",
        "## Added printed parts",
        "",
        "| Part number | Filename | Interface | Physical role |",
        "|---|---|---|---|",
    ]
    roles = {
        "front_frame_corner_connector_left": "LEFT external AI-01 corner sleeve",
        "front_frame_corner_connector_right": "RIGHT external AI-01 corner sleeve",
        "rear_cradle_center_joiner": "Keyed two-half cradle joiner",
        "rear_cradle_left_attachment": "LEFT rail-to-cradle external channel",
        "rear_cradle_right_attachment": "RIGHT rail-to-cradle external channel",
        "front_fpb_to_rear_cradle_visual_locator": "Removable frame/cradle cross tie",
        "cbox_saddle_base_clip_left": "LEFT saddle-base/profile clip",
        "cbox_saddle_base_clip_right": "RIGHT saddle-base/profile clip",
        "bbox_support_anchor_front": "Unique FRONT support anchor",
        "bbox_support_anchor_rear": "Unique REAR support anchor",
        "profile3_rail_outer_clamp_left": "LEFT slotless rail outer clamp",
        "profile3_rail_outer_clamp_right": "RIGHT slotless rail outer clamp",
        "lower_adapter_visual_locator_left": "LEFT clamp-to-adapter locator",
        "lower_adapter_visual_locator_right": "RIGHT clamp-to-adapter locator",
    }
    for part in CONNECTIVITY_PARTS:
        lines.append(
            f"| {part.part_number} | `{part.filename}` | "
            f"{part.interface_id} | {roles[part.key]} |"
        )
    lines.extend(
        (
            "",
            "## Dry connection sequence",
            "",
            "1. Slide PS-PR-A1-FRM-306-R00 onto the LEFT rail and front crossmember; install visible connector-only dummy bolts.",
            "2. After LEFT P3/P4 passes, repeat with PS-PR-A1-FRM-307-R00 and the RIGHT rail.",
            "3. Install PS-PR-A1-FRM-309-R00/310-R00 from the open rear rail ends.",
            "4. Connect cradle halves with PS-PR-A1-FRM-308-R00 and visible dummy pin.",
            "5. Lower PS-PR-A1-FRM-311-R00 onto both rear rail datums and the center key.",
            "6. Slide PS-PR-A1-BOX-307-R00/308-R00 over the existing saddle bases and PROFILE-3 envelopes.",
            "7. Slide PS-PR-A1-BOX-309-R00/310-R00 over the unique FRONT/REAR support and cradle edges.",
            "8. Slide PS-PR-A1-FLT-305-R00/306-R00 from open rail ends to Y=-110 mm; retain through connector-only ears.",
            "9. Add PS-PR-A1-FLT-307-R00/308-R00 and then the unchanged lower adapters.",
            "10. Verify all pins/bolts, keys, part numbers, and NO LOAD markings remain visible.",
            "",
            "## Release",
            "",
            "Only the directed print-order gate associated with each connection "
            "may release the next mirror part. Dimensional-table agreement alone "
            "does not satisfy P3 or P4.",
            "",
        )
    )
    return "\n".join(lines)


def ai10_clearance_reservation_markdown() -> str:
    return "\n".join(
        (
            "# AI-10 PTO-DRIVE SYNC LINK v0.1 clearance reservation",
            "",
            "No dual-row pulley, belt, guard, shaft extension, or PTO geometry "
            "is manufactured or implied by this dummy.",
            "",
            f"- {AI10_RESERVATION['drive_candidate']}",
            f"- {AI10_RESERVATION['pto_candidate']}",
            f"- {AI10_RESERVATION['sync_candidate']}",
            f"- {AI10_RESERVATION['downstream_candidate']}",
            "- axial shaft length = HOLD",
            "- bearing overhang = HOLD",
            "- belt-row spacing = HOLD",
            "- guard envelope = HOLD",
            "- 300 mm width interference = HOLD",
            "- independent PTO neutral interlock = REQUIRED",
            "- application boundary = LOW-LOAD SPREADER ONLY",
            "- current dummy guarantees axial space = FALSE",
            "",
            "AI10_CLEARANCE_STATUS = NOT_YET_AUDITED",
            "",
        )
    )
