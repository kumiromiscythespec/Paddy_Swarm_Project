# MISUMI shaft/key procurement update — 2026-09-01

## Physical result

- Two shafts were each shortened by 12.0 mm.
- Both shortened shafts fit fully in KP000.
- Approximately 1 mm axial spare remained.
- No frame or other interference was observed.
- Key physical record remains 19.7 mm original, 3.0 mm removed, 16.7 mm effective; length match PASS.

## Procurement decision

Status is PROCUREMENT_UPDATE_PARTIAL. Repository search found
AHFGKR10-145-KA4-A20 only as PURCHASE_CANDIDATE with physical=NOT_YET.
That is not an order receipt or purchase authority, so this task does not silently
publish a 133 mm reorder. The allowed rule is:

future shaft order length = confirmed prior purchased length - 12.0 mm per shaft.

Confirm the prior MISUMI order record or directly measure the finished shaft before
issuing an exact SKU/length. Likewise, 19.7 mm physical key length does not prove
a nominal 20 mm purchased key.

Torque path is unchanged:

SHAFT → KEY → MISUMI METAL PULLEY → EXACT GROOVE-1/C1 →
PRINTED CARRIER → CANDIDATE C 12T.
