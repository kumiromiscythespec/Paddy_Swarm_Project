# Common Rover B01
## BBOX / Upper Rail Registration Measurement

MEASUREMENT_RECORD / NOT_AUTHORITY_PROMOTION。本runは部分測定結果として終了。PHASE 1–5の識別回答に加え、PHASE 6の前側upper rail内幅130 mm・外幅210 mm、PHASE 7の後側内幅129 mm・外幅209 mmをOwner測定値として記録。BBOX接触なしのrail測定であり、BBOXの安定性UNKNOWNやBBOX関連接触測定の保留を解除しない。B01全体の解消やBBOX数値登録の完了ではない。

## Environment

```text
REPOSITORY: D:\Paddy_Swarm_Project
START_BRANCH: agent/organize-untracked-cad-assets-20260725
START_HEAD: 4fdd9d4f802547c90bacd315115a7d3d1cff3095
PRECONDITION_MISMATCH: NO
RECOMMENDED_REASONING: MEDIUM
REASONING_SETTING_CONTROL: USER / RUNTIME CONTROLLED
AGENT_MODE: SINGLE
SUBAGENT_USED: NO
```

START_STATUS:

```text
?? cad/common_rover/bbox/bbox_functional_diagonal_corner_locator_test_v001/
?? cad/common_rover/bbox/bbox_functional_diagonal_corner_locator_test_v002_fastener_relief/
?? cad/common_rover/bbox_cbox/bbox_cbox_stacked_service_cradle_v001/
?? cad/high_cut_harvest/
```

## Authority Scope

本runでOwnerによる外側目視・写真・静的計測・measurement-local datum設定は承認されていた。今回の終了指示により追加のB01測定は要求しない。Agentは提供値・写真・観察の整理を担当し、自ら実物を測定したとは表現しない。通電、motor/shaft操作、battery接続変更/着脱、lid開閉、BBOX/rail移動、部品取り外し、強制fit、水/泥/field、加工/接着は禁止。

適用文書は [AGENTS](../../AGENTS.md)、[index](../../CHATGPT_PROJECT_INDEX.md)、[current authority](../../CURRENT_COMMON_ROVER_AUTHORITY.md)、[safety boundary](../../LONEWOLF_FANG_SAFETY_BOUNDARY.md)。[Production audit](../agent/ASTRA_FIRST_PRODUCTION_TASK_V001_COMMON_ROVER_AUDIT_USAGE_OPTIMIZED_2026_09_08.md) のB01を対象とする。過去auditの実施未承認は、その時点の記録として維持し、今回の限定承認と区別する。

B01 source: [authority map](../repository/COMMON_ROVER_AUTHORITY_MAP.md)、[dated dimensions](../../cad/common_rover/physical_authority/common_rover_physical_dimensional_authority_2026_09_01_v001/COMMON_ROVER_PHYSICAL_DIMENSIONAL_AUTHORITY_2026_09_01.md)、[temporary packaging](../../cad/common_rover/physical_authority/common_rover_goldenmate_battery_fit_bbox_packaging_authority_v001/BATTERY_FIT_BBOX_PHYSICAL_PACKAGING_AUTHORITY.md)、[global integration holds](../../cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065/GLOBAL_INTEGRATION_HOLDS.md)。これらは今回の測定値ではなく比較用source。現状観察をcurrent engineering authorityに昇格しない。

## Specimen Identification

Ownerの「PHASE 1 — OWNER RESPONSE / CLARIFICATION」を一次sourceとする。

```text
SPECIMEN_ID: AS_FOUND_BBOX_SPECIMEN_001
SPECIMEN_STATE: TEMPORARY_PARTIALLY_FIXED
BBOX_CONFIGURATION: TEMPORARY_BATTERY_STORAGE_PLACEMENT
BBOX_ORIENTATION: INCLINED_AS_FOUND
FIXATION_STATE: PARTIAL_FIXATION / ONE_SIDE_ONLY
CONFIDENCE: HIGH (current physical state identification; owner reported)
CURRENT_DESIGN_MATCH: NOT_CONFIRMED
FINAL_INSTALLED_TRANSFORM: NOT_ESTABLISHED
BATTERY_INTERNAL_STATE: UNKNOWN (external observation)
POWER_STATE: UNPOWERED_CONFIRMED_BY_OWNER
FRONT_REFERENCE: front_side.jpg (owner confirmed vehicle front view)
AUTHORITY_PROMOTION: NO
```

傾斜は撮影のための偶発的poseではなく、片側fixtureだけを設置した現在の進捗状態とのOwner明示説明。角度の数値は未測定。HIGHはこの一時状態の同定に対する確度であり、V004との一致、安定支持、最終取付姿勢への確度ではない。固定側はPHASE 3でvehicle RIGHTと確認済み。安定性はUNKNOWNのまま。

提供写真は会話内表示を確認した。原本を編集・移動・repositoryへコピーしていない。写真中の文字は観察対象であり作業指示ではない。撮影時刻・全写真の同時性はファイル名から断定しない。

Photo source directory: `D:/Downloads/drive-download-20260907T220146Z-1-001/`（local external references、repository同梱ではない）。

| Photo ID | Filename | 記録用途 |
|---|---|---|
| P01 | PXL_20260907_215734143.jpg | BBOXがframeに対して傾斜している外観 |
| P02 | up_side.jpg | 上方からのBBOX、左右長手rail、白色fixtureの位置関係 |
| P03 | front_side.jpg | Owner確定の車体前面。前側上部の銀色横材と両端frame接続が見える |
| P04 | right_side.jpg | Owner提供の右側面写真。BBOX外側とrail/fixtureの観察 |
| P05 | isometric.jpg | 全体の位置関係と上部外形 |
| P06 | left_side.jpg | Owner提供の左側面写真。chimney様突出部の側面形状 |

PHASE 1時点の写真からの定性的観察（Owner提供写真に対するAgent読取り。実測ではない。後続のOwner同定はPHASE 4欄に記録）:

- 白色BBOX bodyの上にlid様の板状部とchimney様の箱状突出部が見える。板周囲に穴/ねじ様featureがある。閉鎖・締結・seal状態は未判定。
- 上部長手railと白色取付fixture・金属ねじ頭が見える。反対側の完全固定や支持能力を写真から証明しない。
- P06の突出部側面に円形featureが見えるが、actual cable gland装着とは同定できない。Gland/cable有無はUNKNOWN。
- 左右railの端・上面・側面の一部は見える。下面やBBOXのtrue lowest pointの全範囲が見えるとはしない。写真上の重なりをphysical contact/clearance値に変換しない。

### PHASE 8 — Historical specimen identity clarification

Source: Owner「PHASE 8 — OWNER RESPONSE」。Owner知識だけによる回答であり、新しい物理測定・接触・移動・開閉は要求していない。

```text
SPECIMEN_IDENTITY_ANSWER: OWNER_UNCERTAIN
CURRENT_BBOX_SPECIMEN: AS_FOUND_BBOX_SPECIMEN_001
HISTORICAL_TEMPORARY_BBOX_SPECIMEN_LINK: UNRESOLVED
EVIDENCE_CLASSIFICATION: OWNER_MEMORY / NOT_CONFIRMED
LIKELY_RELATIONSHIP: POSSIBLY_DIFFERENT_SPECIMEN_WITH_DESIGN_LINEAGE
CURRENT_DESIGN_MATCH: NOT_CONFIRMED
AUTHORITY_PROMOTION: NO
```

OWNER_RECOLLECTION: 過去のtemporary battery-fit / packaging測定に使った現物と、現在の撮影specimenが同じかは確実には思い出せない。過去は左右からclampする初期の仮fixture / prototypeで、現在と厳密に同じ完成箱形態ではなかった可能性があり、現在のBBOXはその測定値をもとに設計されたかもしれない、との記憶を保持する。これは未確認の記憶であり、DIFFERENT_PHYSICAL_SPECIMEN_CONFIRMEDにも、設計系譜の確定にも昇格しない。

過去のBATTERY_FIT_BBOX_PHYSICAL_PACKAGING_AUTHORITY.mdの測定は削除せず、現物同一性が未解決のpredecessor / design-input evidenceとして保持する。現在のBBOXへsame-specimen evidenceとして統合せず、過去の位置値を現在の傾斜したas-found poseへ転用しない。外観・寸法の類似やこの記憶からV004/current authorityとの一致を推定しない。現状状態の同定に対するPHASE 1のHIGH confidenceと、過去specimenとの関係UNRESOLVEDは別scopeである。

## Measurement Datum

```text
DATUM_TYPE: MEASUREMENT_LOCAL
DATUM_ID: B01_FRONT_TRANSVERSE_2020_AS_FOUND
DATUM_STATUS: TEMPORARY_GEOMETRY_REFERENCE
DATUM_DESCRIPTION: Flat upper surface of the front silver transverse 2020 extrusion
DATUM_PHOTO_REFERENCE: P03
FRONT_TRANSVERSE_2020_DATUM_ACCESS: YES (owner reported)
STABILITY_STATE: UNKNOWN (owner reported)
FUTURE_LENGTH_CHANGE_REQUIRED: YES (owner reported; not machining authorization)
FINAL_WIDTH_AUTHORITY: NOT_ESTABLISHED
GLOBAL_DATUM_MAPPING: UNKNOWN
AUTHORITY_PROMOTION: NO
```

Source: Owner「PHASE 2 — OWNER RESPONSE」。前側銀色横材の平らな上面は外側からアクセスでき、BBOXや他部品を動かさずmeasurement-local referenceにできるとの回答を記録。これは基準featureの指定であり、測定の実施や安定支持の確認ではない。Ownerは揺すり等の確認を行っておらず、静止していることから安定性を昇格していない。

この2020横材は車幅変更前の余材であり、最終車幅確定後に長さ変更が必要とのOwner説明。現在の左端・右端・全長・全長から導いた中点を最終幅の基準に使用しない。現在の端を新しいglobal X_REFやvehicle中心として採用しない。切断は本runの許可範囲外。将来の加工・移動があれば、同じdatum IDのまま前後の状態を混ぜず再同定が必要。

上面の水平/平面性や左右railとの共面性も未測定。Local datumはglobal vehicle Z0ではない。左右定義は車体前進方向を向いた左右。PHASE 3でOwnerがP03正面写真の画像右＝vehicle LEFT、画像左＝vehicle RIGHTを確認した。

## Upper Rail Measurements

PHASE 3時点では非接触識別のみを記録し、数値測定を保留していた。PHASE 6でOwnerが前側upper rail限定のspan測定を提供したため、以下に独立したscopeで追記する。左右別の高さ・datumからの各面位置は依然NOT_MEASUREDであり0ではない。

```text
VEHICLE_SIDE_MAPPING: CONFIRMED
OWNER_CONFIRMATION: YES
FRONT_PHOTO_IMAGE_RIGHT: VEHICLE_LEFT
FRONT_PHOTO_IMAGE_LEFT: VEHICLE_RIGHT
INSTALLED_FIXTURE_SIDE: VEHICLE_RIGHT
FIXATION_STATE: PARTIAL_FIXATION
VEHICLE_RIGHT_FIXTURE: INSTALLED
VEHICLE_LEFT_FIXTURE: NOT_INSTALLED
AUTHORITY_PROMOTION: NO
```

| Observation ID | Feature / side | Owner-reported state | Source | Boundary |
|---|---|---|---|---|
| OBS-P3-01 | Vehicle side mapping | CONFIRMED | PHASE 3回答 + P03 | 前方を向いた左右。Global座標へのmappingではない |
| OBS-P3-02 | Side fixture / RIGHT | INSTALLED | PHASE 3回答 | 片側のみ。座標・保持性能・最終位置は未測定 |
| OBS-P3-03 | Side fixture / LEFT | NOT_INSTALLED | PHASE 3回答 | RIGHTの位置をmirrorしてLEFTの測定値にしない |

この表は観察記録であり寸法measurement entryではない。LEFT fixture未設置をLEFT rail不在と混同しない。単一fixtureから最終installed transform、対称性、最終BBOX位置を推定しない。

### PHASE 6 — Owner-reported front upper rail spans

Source: Owner「PHASE 6 — OWNER MEASUREMENT RESULT」。MEASUREMENT_SCOPE: FRONT UPPER RAIL ONLY。BBOX_CONTACT: NO。POWER_STATE: UNPOWERED。数値はOwner提供値であり、Agentによる実測・写真縮尺からの推定ではない。

| Field | Measurement 01 | Measurement 02 |
|---|---|---|
| MEASUREMENT_ID | B01-P6-FRONT-UPPER-RAIL-INNER-SPAN | B01-P6-FRONT-UPPER-RAIL-OUTER-SPAN |
| SPECIMEN_ID | CURRENT_AS_FOUND_FRAME | CURRENT_AS_FOUND_FRAME |
| FEATURE | Front upper longitudinal rail inner-face to inner-face span | Front upper longitudinal rail outer-face to outer-face span |
| SIDE | LEFT_TO_RIGHT (Owner原文; spanであり単一側の位置ではない) | LEFT_TO_RIGHT (Owner原文; spanであり単一側の位置ではない) |
| DATUM | Direct face-to-face measurement; not BBOX datum | Direct face-to-face measurement; not BBOX datum |
| VALUE | 130 | 210 |
| UNIT | mm | mm |
| TOOL | Steel ruler | Steel ruler |
| TOOL_RESOLUTION | KNOWN / 1 mm (Owner follow-up) | KNOWN / 1 mm (Owner follow-up) |
| METHOD | 前側領域の左右黒色長手upper rail対向内面間を鋼尺で直接測定 | 同じ左右黒色長手upper railの前側領域の外面間を鋼尺で直接測定 |
| OWNER_REPORTED | YES | YES |
| PHOTO_REFERENCE | PXL_20260908_013138371.jpg | PXL_20260908_013147029.MP.jpg |
| CONDITION | FRONT UPPER RAIL ONLY; UNPOWERED; BBOX_CONTACT: NO | FRONT UPPER RAIL ONLY; UNPOWERED; BBOX_CONTACT: NO |
| CONFIDENCE | MEDIUM (Owner指定) | MEDIUM (Owner指定) |
| STATUS | MEASURED | MEASURED |
| NOTES | 前側のspanのみ。中心線・最終車幅へ変換しない | 同じrail pairのspan。後側spanや平行度を示さない |

Source追記: Owner「PHASE 6 — OWNER FOLLOW-UP」により鋼尺の最小目盛1 mm、内幅130 mm・外幅210 mmを再確認した。同じmeasurement IDへのmetadata補完であり、追加の独立測定や再測定として数えない。1 mmは工具分解能であり、測定精度・不確かさ・許容差を±1 mmと宣言するものではない。

PHOTO_STATUS: OWNER_PROVIDED (Owner申告)。PHOTO_REVIEW_STATUS: NOT_REVIEWED_BY_AGENT。2枚のfilenameとOwnerによる写真説明は受領済みだが、このfollow-upにもAgentが閲覧できる画像添付/絶対pathは確認できない。写真は測定面の同定と内幅/外幅の区別を支えるという説明をOWNER_REPORTEDとして保持し、画像内容をAgentが確認済みとはしない。NUMERICAL_SOURCE: OWNER_REPORTED_DIRECT_MEASUREMENT。Photo scaleによる数値置換なし。厳密な長手測点・読取り位置の画像確認は未完了だが、取得済み値の保存や独立した次項目の必須条件にはしない。

PHASE 2の横材上面datumにもhistorical X_REFにも数値mappingしていない。左右の面座標、個々のrail幅、中心線、対称性、最終車幅はspanから自動導出しない。前側rail測定の実施から、片側固定BBOXやrover全体の支持が安定しているとも推定しない。

### PHASE 7 — Owner-reported rear upper rail inner span

Source: Owner「PHASE 7 — OWNER MEASUREMENT RESULT」。NUMERICAL_SOURCE: OWNER_REPORTED_DIRECT_MEASUREMENT。

| Field | Measurement 03 |
|---|---|
| MEASUREMENT_ID | B01-P7-REAR-UPPER-RAIL-INNER-SPAN |
| SPECIMEN_ID | CURRENT_AS_FOUND_FRAME |
| FEATURE | Rear upper longitudinal rail inner-face to inner-face span |
| MEASUREMENT_LOCATION | Approximately 30 mm from vehicle rear end (Owner報告; 厳密なglobal座標ではない) |
| SIDE | LEFT_TO_RIGHT (対向rail内面間spanの意味; 個別面座標ではない) |
| DATUM | 対向内面間の直接測定。BBOX datumではない |
| VALUE | 129 |
| UNIT | mm |
| TOOL | Steel ruler |
| TOOL_RESOLUTION | KNOWN / 1 mm |
| METHOD | 後端から約30 mmの位置で左右upper rail内面間を鋼尺で測定 (Owner報告) |
| OWNER_REPORTED | YES |
| PHOTO_REFERENCE | PXL_20260908_014128183.jpg |
| CONDITION | BBOX_CONTACT: NO。無通電は先行Owner回答で確認済み; PHASE 7では新たな電源状態申告なし |
| CONFIDENCE | MEDIUM (Owner指定) |
| STATUS | MEASURED |
| NOTES | 後側の当該測点のspanのみ。平行度・角度・許容差・FAILを導出しない |

PHOTO_REVIEW_STATUS: NOT_REVIEWED_BY_AGENT。写真filenameは受領したが、この回答に閲覧可能な画像添付/絶対pathはない。写真縮尺から数値を置き換えていない。AUTHORITY_PROMOTION: NO。

Ownerのdesign clarificationと今回のas-found比較を以下に分離して記録する。

```text
NOMINAL_DESIGN_BASIS: 170 mm - 20 mm × 2 = 130 mm (Owner説明)
NOMINAL_INNER_SPAN: 130 mm (Owner説明の公称値)
FRONT_INNER_SPAN: 130 mm (PHASE 6)
REAR_INNER_SPAN: 129 mm (PHASE 7; 後端から約30 mm)
OBSERVED_FRONT_REAR_DIFFERENCE: 1 mm
FRONT_VS_NOMINAL: CONSISTENT (Owner比較)
REAR_VS_NOMINAL: 1 mm SMALLER AS-FOUND OBSERVATION
ASSEMBLY_VARIATION_OBSERVED: YES (Owner報告; 上記読取り値の差に限定)
PARALLELISM_STATUS: NOT_EVALUATED
ACCEPTANCE_THRESHOLD: NOT_DEFINED_IN_CURRENT_AUTHORITY
```

公称式はOwnerが説明した組立設計の背景であり、新規CAD実測値、現在の各rail幅の実測値、製造公差ではない。前後差1 mmは分解能1 mmの鋼尺による報告値の差として保持する。測定不確かさや差の許容値は定義されておらず、精密な平行度・角度誤差、許容差内外、PASS/FAILへ変換しない。

### PHASE 7 follow-up — Owner-reported rear outer span and design intent

Source: Owner「PHASE 7 — OWNER FOLLOW-UP」。追加の独立measurement entryとして記録する。

| Field | Measurement 04 |
|---|---|
| MEASUREMENT_ID | B01-P7-REAR-UPPER-RAIL-OUTER-SPAN |
| SPECIMEN_ID | CURRENT_AS_FOUND_FRAME |
| FEATURE | Rear upper longitudinal rail outer-face to outer-face span |
| MEASUREMENT_LOCATION | Approximately 30 mm from vehicle rear end (Owner location clarification; 後側内幅と同じ測点) |
| SIDE | LEFT_TO_RIGHT (rail pairのspan; 個別面座標ではない) |
| DATUM | 対向外面間の直接測定。BBOX datumではない |
| VALUE | 209 |
| UNIT | mm |
| TOOL | Steel ruler |
| TOOL_RESOLUTION | KNOWN / 1 mm |
| METHOD | 後側左右upper rail外面間を鋼尺で測定 (Owner報告) |
| OWNER_REPORTED | YES |
| PHOTO_REFERENCE | PXL_20260908_014901635.jpg |
| CONDITION | BBOX_CONTACT: NO。無通電は先行Owner回答で確認済み; 今回新たな電源状態申告なし |
| CONFIDENCE | MEDIUM (Owner指定) |
| STATUS | MEASURED |
| NOTES | 写真filenameのみ受領。PHOTO_REVIEW_STATUS: NOT_REVIEWED_BY_AGENT。数値はOwner直接測定値を使用 |

Source追記: Owner「PHASE 7 — OWNER LOCATION CLARIFICATION」。後側内幅129 mm・外幅209 mmはいずれも後端から約30 mmの同じ長手位置で測定したと確認された。SAME_LOCATION_AS_REAR_INNER_SPAN: YES。OWNER_CONFIRMATION: YES。工具は鋼尺、TOOL_RESOLUTION: KNOWN / 1 mm、BBOX_CONTACT: NO。同じ2件への位置metadata補完であり、再測定や追加measurementとして数えない。測点一致は後側内外spanの比較可能性を改善するが、平行度・角度の直接測定、製造公差、PASS/FAILを成立させない。PARALLELISM_STATUS: NOT_DIRECTLY_MEASURED。AUTHORITY_PROMOTION: NO。

| Span | Front (mm) | Rear (mm) | 報告値の前後差 |
|---|---|---|---|
| Inner | 130 | 129 | 後側が1 mm狭い |
| Outer | 210 | 209 | 後側が1 mm狭い |

OWNER_INTERPRETATION: 両spanの変化は、組立状態のrail pairの小さな収束傾向 / 非平行状態と整合する。これは報告された測定値についてのOwner解釈であり、平行度の直接測定ではない。どちらのrailが傾いているか、正確な角度誤差、各railの位置や幅は導出しない。鋼尺分解能1 mmと未定義の測定不確かさを踏まえ、差から精密な形状やPASS/FAILを確定しない。

```text
OBSERVED_FRONT_REAR_SPAN_CHANGE: 1 mm narrower at rear in both inner and outer span measurements
PARALLELISM_STATUS: NOT_DIRECTLY_MEASURED
AUTHORITY_PROMOTION: NO
ACCEPTANCE_THRESHOLD: NOT_DEFINED_IN_CURRENT_AUTHORITY
```

OWNER_DESIGN_INTENT: 農家・一般ユーザーによる組立と保守を想定し、工作機械水準のframe精度を前提にせず、現実的な手組みのばらつきを許容できる設計を目指す。今回の約1 mmの前後差はrobustness planningへの設計入力として保持し、自動的な組立FAILにはしない。この観察だけで数値的な製造公差を制定したり、現在の設計がそのばらつきを既に吸収できると検証済みにしたりしない。既存engineering authorityは変更しない。

```text
OBSERVED_ASSEMBLY_VARIATION: approximately 1 mm in this specimen / measurement scope
DESIGN_TOLERANCE: NOT_YET_DEFINED
ROBUSTNESS_REQUIREMENT: DESIGN_INTENT_RECORDED / NOT_YET_VALIDATED
```

## BBOX External Measurements

Source: Owner「PHASE 4 — OWNER RESPONSE」。外観featureの同定だけを記録。Body bottom / true lowest / rim / lid / chimney / cableを別featureとして扱う。写真から寸法・傾斜角を推定して埋めない。寸法測定は保留のまま。

| Observation ID | Feature | Owner-reported state | Photo reference | Scope / interpretation |
|---|---|---|---|---|
| OBS-P4-01 | Upper plate-like component | LID: CONFIRMED | P02/P05 | Feature identityのみ。閉鎖・締結・seal性能は未確認 |
| OBS-P4-02 | Rectangular box-like protrusion | CHIMNEY: CONFIRMED | P02/P05/P06 | Feature identityのみ。寸法・version一致は未確認 |
| OBS-P4-03 | Cable gland body | EXTERNALLY_UNKNOWN | P06 | 外面の円形featureだけでは装着glandと断定できない |
| OBS-P4-04 | Cable through gland | NOT_INSTALLED / NOT_VISIBLE (Owner原文) | 提供写真P01–P06 | 説明は「外側featureを通るcableが写真で見えない」。確実な不在・内部配線状態へ拡張しない |

観察記録のみ。OWNER_REPORTED: YES。AUTHORITY_PROMOTION: NO。Gland装着や配線完了を円形featureから推定しない。Cableについて正規化した観察はVISIBILITY: NOT_VISIBLE、確定したinstallation statusはUNKNOWNとし、NOT_PRESENTの測定entryにはしない。Lid/chimneyの識別によってrimや各topの位置が測定済みになるわけではない。

## BBOX / Rail Registration

Source: Owner「PHASE 5 — OWNER RESPONSE」。過去のtemporary BBOX測定で使ったreference-featureをOwner確認として記録。今回のas-found poseは最終installed transformではない。後で値が得られても一時状態と測定時点に限定する。

```text
X_REF_IDENTIFIED: YES
X_REF_SOURCE: OWNER_CONFIRMED_HISTORICAL_REFERENCE
X_REF_MEMBER: LONGITUDINAL_2040_500MM_MEMBER
X_REF_FEATURE: End plane of the vehicle-longitudinal 2040 extrusion
X_REF_MEASUREMENT_DIRECTION: From member end into vehicle interior, along vehicle longitudinal direction
REFERENCE_SCOPE: Historical temporary BBOX internal frame-space distance from this member end
PHASE_2_DATUM_AND_HISTORICAL_X_REF: DISTINCT_FEATURES
CONFIDENCE: HIGH (reference-feature identity; owner confirmation)
CURRENT_NUMERICAL_MEASUREMENT: NOT_TAKEN_IN_THIS_PHASE
AUTHORITY_PROMOTION: NO
```

OBS-P5-01: Ownerは公称部材長500 mmの長手2040材の端面をhistorical X_REFと同定した。500 mmは部材の公称識別情報であり、今回測定した長さではない。特定の左右member/端面の写真上の位置と、current global座標への数値mappingはこの回答から追加推定しない。基準featureのOwner確認は保持し、数値登録に必要な対応の精度とは区別する。

PHASE 2のB01_FRONT_TRANSVERSE_2020_AS_FOUNDは前側横2020材の上面であり、historical X_REFとは別feature。横材上面・余長のある横材端で代用しない。Historical X_REFから新しい車体中心線・最終幅datumを導かず、過去距離から現状BBOX位置も導かない。

PHOTO_SUPPORT: Ownerは「新たな上面写真が長手材端から内部方向への測定と整合する」と説明した。このPHASE 5メッセージには新規画像ファイル/添付を確認できないため、その記述はOWNER_REPORTEDの写真説明として保持し、Agentが新規写真を確認したとは記録しない。P02と同じ写真とも仮定しない。Photo scaleから数値の導出・上書きはしていない。

各measurementはMEASUREMENT_ID、SPECIMEN_ID、FEATURE、SIDE、DATUM、VALUE、UNIT、TOOL、TOOL_RESOLUTION（KNOWN/UNKNOWNと既知なら分解能）、METHOD、OWNER_REPORTED、PHOTO_REFERENCE、CONDITION、CONFIDENCE、STATUS、NOTESを保持する。現在の数値entryはPHASE 6–7のrail span 4件。BBOXとrailを同一datumで登録した数値は未取得。未提供値を0やOWNER_REPORTED: YESの架空entryで埋めない。

## Existing Record Comparison

HISTORICAL_NUMERICAL_COMPARISON: NOT_COMPLETED / SPECIMEN_AND_FEATURE_CORRESPONDENCE_UNRESOLVED。本runは部分結果で終了し、未解決の対応関係を無理に数値照合しない。Historical X_REF identityはCONFIRMED_BY_OWNER、historical measurementsはPRESERVED。X_REFの同定だけでは同一specimenや現在poseとの対応を成立させない。PHASE 7の同run内の前後比較とOwner公称設計説明は上記に記録し、過去authorityとの照合とは区別する。PHASE 8で過去BBOX specimenとの同一性は未解決と回答されたため、同一現物を前提とした値の統合は行わない。過去値に合わせて130/210/129/209を修正せず、既存authorityも上書きしない。BBOX高さは依然未取得であり、過去Z148/Z254やtemporary Z144/Z254を今回の値へコピーしない。

## Unknown / Not Measured

- 安定支持。固定側の左右対応はPHASE 3で解決済みだが、fixture位置・保持性能・対称性は未測定。
- V004/current designと実物の一致。過去temporary specimenとの関係はPHASE 8のOWNER_UNCERTAINによりUNRESOLVED。別specimenとも確定しない。
- Battery内部状態、gland本体の装着有無、cableの確定した装着/内部配線状態、lidの締結状態。Lid/chimneyのfeature identityはPHASE 4で確認済み、外側cableは写真上NOT_VISIBLE。
- Datumのglobal mapping、上面の水平/平面性、報告済みspan 4件以外の実測寸法・角度、最終installed transform・最終幅。
- PHASE 6–7の写真内容のAgent確認、詳細な測点。後側内幅・外幅の測点はともに後端から約30 mmで一致するとOwner確認済み。鋼尺分解能はKNOWN / 1 mm。左右の個別面位置/高さはNOT_MEASURED。平行度はNOT_DIRECTLY_MEASURED。
- Historical X_REFはOwner同定済み。今回の数値登録用の具体的なmember/端面と写真上の対応、新規上面写真のreference、現状specimenとの数値関係は未記録。
- 写真で見えないものはUNKNOWN。NOT_PRESENTは不在が確認できたfeatureにだけ使用する。

片側固定だけを理由に全作業を中止しない。BBOXに触れる、またはその支持に影響する計測は安定性UNKNOWNのため保留。BBOX非接触で実施されたPHASE 6–7のrail測定はその限定scopeで記録する。動かす・持上げる・lidを開く等が必要なら該当項目のみ停止し、独立した安全な記録整理は継続する。

## Result Classification

```text
B01_RUN_STATUS: PARTIAL_MEASUREMENT_COMPLETE
PHASE_1: OWNER_STATE_IDENTIFICATION_RECORDED
PHASE_2: TEMPORARY_LOCAL_DATUM_RECORDED
PHASE_3: SIDE_MAPPING_AND_FIXTURE_STATE_RECORDED / DIMENSIONS_NOT_MEASURED
PHASE_4: EXTERNAL_FEATURE_IDENTIFICATION_RECORDED / DIMENSIONS_NOT_MEASURED
PHASE_5: HISTORICAL_X_REF_IDENTITY_RECORDED / CURRENT_NUMERICAL_MEASUREMENT_NOT_TAKEN
PHASE_6: TWO_FRONT_UPPER_RAIL_SPANS_OWNER_REPORTED / TOOL_RESOLUTION_RECORDED
PHASE_7: TWO_REAR_UPPER_RAIL_SPANS_OWNER_REPORTED / NOMINAL_DESIGN_AND_ROBUSTNESS_INTENT_RECORDED
PHASE_8: OWNER_MEMORY_RECORDED / HISTORICAL_SPECIMEN_LINK_UNRESOLVED
PARALLELISM_STATUS: NOT_DIRECTLY_MEASURED
CONTACT_MEASUREMENTS: RAIL_ONLY_MEASUREMENTS_REPORTED / BBOX_CONTACT_ON_HOLD
B01_STATUS: HOLD_PENDING_STABLE_OR_FINAL_BBOX_PLACEMENT
RAIL_REGISTRATION: PARTIAL_PHYSICAL_EVIDENCE_RECORDED
BBOX_NUMERICAL_REGISTRATION: NOT_COMPLETED
FINAL_INSTALLED_TRANSFORM: NOT_ESTABLISHED
AUTHORITY_PROMOTION: NO
ACCEPTANCE_THRESHOLD: NOT_DEFINED_IN_CURRENT_AUTHORITY
PHYSICAL_AUTHORITY_PROMOTION_CANDIDATE: NO
```

## What This Evidence Supports

Ownerが確認した現状specimen ID、一時保管配置・RIGHT側のみ固定・LEFT側fixture未設置・傾斜、無通電という状態の記録。提供写真で見える外形と位置関係の定性的な観察。Ownerが指定した前側2020横材上面の一時measurement-local referenceと、そのアクセス可能性・使用範囲の記録。P03写真と車体左右の対応。

PHASE 5のOwner確認によるhistorical X_REFの部材端面と測定方向、およびPHASE 2 datumとの区別。既存authorityファイルを変更せず、後続review用のreference clarificationとして保持する。

PHASE 6のCURRENT_AS_FOUND_FRAME前側黒色upper rail pairの直接内幅130 mm・外幅210 mm、およびPHASE 7の後端から約30 mmでの内幅129 mm（Owner-reported、confidence MEDIUM）。さらにPHASE 7 follow-upの後側外幅209 mm（Owner-reported、confidence MEDIUM）。その測定scopeに限る。公称内幅130 mmの設計背景はOwner説明として保持し、現在の実測値と区別する。

## What This Evidence Does Not Support

Final installed transform、V004一致、報告されたspan以外の実測寸法/角度、平行度・公差適合判定、中心線・最終幅、fixture保持能力、安定支持の証明、CBOX/BBOX統合authority、PHYSICAL_PASS、waterproof、powered/field PASS、製造/購入/deployment release。

## Integrity

```text
AUTHORITY_CHANGED: NO
PHYSICAL_AUTHORITY_CHANGED: NO
CAD_STATUS_CHANGED: NO
PHYSICAL_STATUS_CHANGED: NO (existing validation status)
FIELD_STATUS_CHANGED: NO
SUBAGENT_USED: NO
FULL_REPOSITORY_SCAN: NO
UNRELATED_FULL_HASH: NO
POWERED_TEST_EXECUTED: NO
WATER_TEST_EXECUTED: NO
MUD_TEST_EXECUTED: NO
FIELD_TEST_EXECUTED: NO
IRREVERSIBLE_MODIFICATION: NO
COMMIT_CREATED: NO
PUSH_PERFORMED: NO
BRANCH_CHANGED: NO
FABRICATED_EVIDENCE: NO
```

## Next Owner Decision

本runはPARTIAL_MEASUREMENT_COMPLETEとして終了する。追加BBOX測定、BBOX移動、lid開閉、安定性確認の揺すり、fixture設置、最終配置、rail span再測定、新規写真は要求しない。BBOXはTEMPORARY_PARTIALLY_FIXED / INCLINED_AS_FOUNDであり、接触測定は安定性UNKNOWNのためHOLD。仮置きposeの追加測定でfinal installed transformを証明しようとしない。

B01は安定した配置または最終配置が成立した時、あるいはOwnerがこのscopeの継続を明示的に選んだ時に再開対象とする。その時点で対象状態と安全条件を確認する。現時点で配置変更や追加作業を求めるものではない。

## NEXT_RECOMMENDED_TASK

B02 — Current crawler assembly inputs / retention gap。PLANNING_ONLY。B02_EXECUTION_STARTED: NO。新しいB02 reportやengineering authorityは作成しない。

Source: [Production audit B02](../agent/ASTRA_FIRST_PRODUCTION_TASK_V001_COMMON_ROVER_AUDIT_USAGE_OPTIMIZED_2026_09_08.md) のB02 / S16–S21。以下のversionはauditが示す設計参照であり、写真の実装現物との一致確認ではない。

| Preflight項目 | 現状と不足情報 | 計画する無通電確認 |
|---|---|---|
| Drive specimen / version | 設計参照: crawler_candidate_c_12t_misumi_groove1_keeperless_v003。現物IDとV003対応はNOT_CONFIRMED | Ownerの製作記録・既存識別表示と現物の対応を整理。外観類似だけでversion確定しない |
| Idler specimen / version | 設計参照: crawler_idler_candidate_c_v001。現物IDとV001対応はNOT_CONFIRMED | 同様に現物と製作元を対応づけ、未確認はUNKNOWNのまま保持 |
| Shaft / bearing / spacer / retention | 使用可能軸長、bearing inner-ring面、左右spacer厚・材質・接触、保持方式・装着状態、service space、idler保持・mount位置が未確認。旧8 mm spacerはaudit上referenceのみ | まず外側から見える部品構成と保持要素を静的に識別。隠れた接触面・締結力・保持性能を外観だけで確定しない。数値測定や分解は別途scope設定 |
| Current parts physically exist | 提供済みP04/P06写真にはcrawler構成部品が見えるが、current設計参照一式の現存・完成・保持済みを証明しない | Drive / idler各現物の存在をOwner記録と照合。CAD/print-readyを製作済み扱いしない |

NEXT_SINGLE_INSPECTION_CANDIDATE: 現在のdrive / idler現物と製作元versionの対応を登録する、無通電・非接触のspecimen identity inventory 1件。Owner知識・製作記録を起点に、実施が別途承認された場合のみ外側の既存識別表示を確認する。各現物の存在、ID、versionまたはUNKNOWNを取得し、誤ったgeometryのstack評価を避けることを目的とする。今回この検査を開始したり、写真・測定をOwnerへ要求したりしない。

このidentity確認だけでretentionやloop assemblyの準備完了にはしない。後続で不足するshaft/bearing/spacer/retention情報を対象現物に結びつけて計画し、その後にmanual validationの実施条件を検討する。今回は回転・手回し・組立変更・powered testを一切開始しない。BBOXには触れず、B01を再開させない。
