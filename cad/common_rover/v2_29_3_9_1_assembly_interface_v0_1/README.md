# Common Rover v2.29.3.9.1 — Assembly Interface v0.1

## 目的

Assembly Interface v0.1 は、Common Rover の部品を見ただけで、向き、接続順、固定具、荷重経路、解除方法が判断できる状態を定義する concept / fit-test lane です。製造部品の完成、購入承認、強度承認を行う lane ではありません。

旧 Grade 0 STL は、authority envelope や個別の形状確認用であり、次の要素が揃った完成組立キットではありませんでした。

- アルミ T スロットと BOX の一次固定
- フロートの slide + metal pin + R-pin 固定
- スライド後の positive stop と抜け止め
- BOX と独立した後部構造支持
- 視認可能なロック状態
- FRONT / REAR / LEFT / RIGHT を含む誤組立防止
- 一貫した組立・分解手順

そのため旧 STL を組み合わせても、完成車体としての製造、強度、耐水、現場配備は承認されません。

## Authority boundary

前方構造骨格は aluminum 20×20-class T-slot の FPB です。左右 rail と front crossmember の AI-01 は既存 authority の butt-face + metal corner bracket 接続を再確認するだけで、再設計しません。

この lane は authority と executable seed から値を読み込みます。CBOX、BBOX、battery cassette、FPB 寸法、座標軸、幅区分、slot zones を独自定数として再定義しません。

BOX は単純に FPB の上へ置くだけではありません。printed saddle で位置決めし、metal clamp と metal structural member で一次荷重を閉じる必要があります。電気コネクタは構造荷重を受けません。BBOX を CBOX だけから片持ち支持してはいけません。

## Three-layer responsibility

### A. Primary structural

- aluminum FPB / metal lower-frame concept
- metal corner brackets
- T-nuts and metal bolts
- removable metal pins
- metal R-pins or cotter-pin candidates

### B. Printed positioning and sacrificial

- CBOX / BBOX saddles
- asymmetric keys and positive-stop shoulders
- float slide guide / receiver
- drain and mud-relief paths
- replaceable wear surfaces

Printed parts may position, guide, protect, or act as a replaceable bearing interface. A printed snap or thumb latch is not the sole primary fixing for a heavy component.

### C. Secondary latch

The thumb latch is **SECONDARY ONLY**. AI-08 applies it to a lightweight service cover and coupon evaluation. It may be considered for an inspection lid, dummy, secondary anti-separation, or pin-loss cover. It may not be the primary fixing for floats, BOXes, aluminum frame, motor, PTO, or another heavy component.

## Architecture comparison

| Option | Concept | Authority / conflict result | Load path and service result |
|---|---|---|---|
| A | FPB rail-mounted CBOX saddles + independent BBOX bridge | FPB is authoritative, but CBOX rail-top attachment competes with motor/input zones; rear bridge remains HOLD | Clear front service, but rail-top competition is high |
| B | Metal front-to-rear LOWER-FRAME cradle + drop-in saddles | Best concept fit with the registered BOTTOM_SLOT lower-adapter relation; rear tie and dimensions remain HOLD | Clearest continuous metal path, open drainage, replaceable saddles |
| C | Printed undertray + metal longitudinal supports | Support attachment is unregistered and broad tray geometry is not authoritative | Higher print volume, mud retention, hidden-fastener risk |

**Recommended concept: Option B.** It is the clearest way to separate structural metal from printed positioning and preserve independent float service. This recommendation does not authorize a rear bridge or cradle manufacturing shape. The BBOX hardpoints, cradle section, attachments, stiffness, and implement clearances remain HOLD.

## Interface map

- AI-01 — FPB rails to front crossmember; existing metal corner-bracket authority only.
- AI-02 — CBOX to printed saddle and metal structural cradle.
- AI-03 — BBOX to independent rear support; manufacturing geometry HOLD.
- AI-04 — CBOX/BBOX alignment and anti-separation; not BBOX vertical support.
- AI-05 — FPB `BOTTOM_SLOT` to lower float adapter.
- AI-06 — lower adapter to keyed float slide receiver.
- AI-07 — removable metal pin plus visible metal R-pin.
- AI-08 — lightweight service-cover thumb-latch test; secondary only.
- AI-09 — battery cassette seating and latch-sequence reservation; no connector implementation.

## Human-readable markings

Every applicable concept part uses visible orientation marks:

`FRONT`, `REAR`, `LEFT`, `RIGHT`, `TOP`, `BOTTOM`

Connection marks:

`A1 / A2`, `B1 / B2`, `F1 / F2`, `L1 / L2`

Float operation:

`1 INSERT` → `2 SLIDE` → `3 LOCK` → `4 VERIFY`

LEFT and RIGHT keys are asymmetric. FRONT and REAR stops are asymmetric. Reversed insertion must not reach the final stop. Pin bores align only at the positive stop. Pin head, R-pin, clamp heads, and lock windows remain visible after assembly.

## Assembly sequence

The recommended sequence is limited to twelve steps:

1. Assemble the FPB aluminum frame.
2. Verify both metal corner brackets.
3. Install CBOX positioning saddles on the metal cradle concept.
4. Install the independent rear support concept.
5. Drop in CBOX and verify A1/A2 stops.
6. Drop in BBOX and verify B1/B2 independent seating.
7. Install the visible metal anti-separation lock.
8. Install lower float adapters on `BOTTOM_SLOT`.
9. `1 INSERT` each correctly keyed float.
10. `2 SLIDE` rearward to the positive stop.
11. `3 LOCK` with metal pin and visible R-pin.
12. `4 VERIFY` all witness marks, pin heads, R-pins, brackets, and clamps.

Disassembly is the exact reverse order. Open-ended channels, downward drains, two-sided drift access, and visible extraction faces support muddy, gloved service. Physical muddy-glove verification remains HOLD.

## Battery cassette reservation

The required order is preserved as an interface contract:

1. cassette insert
2. guide to seat
3. primary latch close
4. safety latch close
5. sensor verification
6. connector shuttle movement
7. secondary seal compression
8. low-energy signal confirmation
9. ID / voltage / polarity / temperature verification
10. pre-charge
11. voltage-difference confirmation
12. main contactor
13. drive authorization

The connector shuttle candidates are compared/reserved only. No electrical connector, seal, sensor, latch, or shuttle manufacturing geometry is created. The connector carries no structural load.

## Fit-test coupons

The generator exports exactly five small STL coupons into an external artifact directory:

1. 20×20 T-slot envelope saddle-fit coupon, 0.20/0.30/0.40/0.50 mm candidates.
2. Slide tongue/receiver coupon, 0.20/0.30/0.40/0.50 mm candidates.
3. Positive-stop pin-alignment and 6 mm-class bore coupon.
4. Secondary thumb-latch coupon with multiple thickness/gap candidates.
5. Embossed orientation, connection, and operation-marking readability coupon.

They target Bambu Lab A1 at 100% scale with support-free orientation preferred and reduced material. Every coupon is marked `FIT TEST ONLY`; COUPON-04 is also marked `SECONDARY ONLY`. They are not load-test parts and are not full rover parts. STL files must never remain in the repository.

Each coupon also carries its source-defined unique part number (`COUPON-01` through `COUPON-05`) as an engraved physical marking. Filename-only and metadata-only identification are prohibited. The engraving is placed on a non-functional +Z exterior identification band, away from fit, sliding, contact, sealing, and measurement surfaces; the XY base face is placed on the build plate so the marked face remains visible and is not consumed by support removal. No revision is appended because the source coupon-ID authority defines no coupon revision/category mapping; no repository-wide production-part category is guessed.

Generation emits `printed_part_number_audit.json`, `printed_part_number_geometry_report.txt`, and `coupon_marking_map.csv`. Validation requires five nonblank unique numbers, common-handler geometry evidence, zero floating part-number solids, matching coupon/geometry/CSV/manifest/filename records, and byte-identical coupon replay.

## Generation

Run in the `paddy-cadquery-280-py312` environment:

```text
python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/generate_interface_package.py --output-dir <external-artifact-directory>
python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/run_unit_tests.py --json <external-json> --text <external-text>
python cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1/validate_interfaces.py --artifact-dir <external-artifact-directory> --output <external-json>
```

All SVG, JSON, CSV, Markdown reports, and STL coupons are external generated artifacts. The source lane contains Python, tests, and this README only.

## Release status

- FULL DUMMY PRINT: **HOLD**
- GITHUB EXECUTABLE CAD RELEASE: **HOLD**
- GITHUB MANUFACTURING RELEASE: **HOLD**
- MANUFACTURING: **NOT APPROVED**
- PURCHASE: **NOT APPROVED**
- WATERPROOF: **HOLD / NOT VALIDATED**
- STRUCTURAL: **HOLD / NOT VALIDATED**
- ELECTRICAL SAFETY: **HOLD / NOT VALIDATED**
- THERMAL: **HOLD / NOT VALIDATED**
- FIELD DEPLOYMENT: **HOLD / NOT APPROVED**
