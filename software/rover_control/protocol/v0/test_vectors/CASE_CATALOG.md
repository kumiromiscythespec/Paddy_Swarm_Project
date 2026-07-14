# Paddy Swarm Rover Control Protocol v0 Test Vector Case Catalog

Status: Draft / Human-readable catalog only / No vector files yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書は、承認済み36シナリオから展開した38件の期待値を人間がレビューするためのcatalogである。実際のtest vectorファイルでもwire protocol schemaでもなく、JSONやYAMLのfield名を確定しない。実機モーター試験を承認せず、上位文書と矛盾する場合は上位文書を優先する。

## 2. 参照文書とトレーサビリティ

- source document: `software/rover_control/protocol/v0/VALIDATION_ORDER.md`
- source document SHA256: `ed600175566a55ad7eea921d2471107ad5d7ee9d86168054ecb7f647e0608e4a`
- format document: `software/rover_control/protocol/v0/test_vectors/README.md`
- format document SHA256: `94200d499d8841845f1348bed222f58f9a0aa3d3900deb95afcd0246fd13fe02`
- protocol version: `v0`
- source scenario count: 36
- concrete vector count: 38

上位文書のSHA256が変化した場合、本文書を再レビューしなければならない。

## 3. catalog表記規則

- output: `zero`、`forward`、`same`。`same`はinitial fixtureの現在値を即時維持するが、liveness延長を意味しない。
- active operation ID: `new`、`same`、`invalid`、`none`
- formal disposition: `FORMAL_ACCEPT`、`FORMAL_REJECT`、`NONE`
- defensive action: `DEFENSIVE_ZERO`、`NONE`
- message handling: `PROCESS`、`NO_MESSAGE_ACTION`、`CACHE_REPLAY`、`NOT_APPLICABLE`
- result source: `NEW_RESULT`、`CACHED_RESULT`、`NONE`
- trigger kind: `MESSAGE`、`TIME_ADVANCE`、`INTERNAL_EVENT`

これらはcatalog上の論理表記であり、最終schemaのenumではない。

## 4. profileとfixture規則

使用するprofileまたはfixtureは`one_side_test`と`drive_pto_split_fixture`だけである。後者はscenario 1Bおよび18用のtest fixture識別名で、正式protocol profile名ではない。`one_side_test`ではTURNとPTOを利用できない。`drive_pto_split_fixture`では文書試験用に`ARMED_NEUTRAL`、`PTO_ACTIVE`、`PTO_READY`を表現できる。fixture指定だけで実モーター出力を有効化しない。

## 5. 入力・validation catalog

| Vector ID | Source | Profile | Initial state | Trigger | Stimulus | Validation / internal event | Rejection reason |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| PV0-VAL-001A | 1 | one_side_test | DISARMED | MESSAGE | COMMAND:ARM | PASS | none |
| PV0-VAL-001B | 1 | drive_pto_split_fixture | DISARMED | MESSAGE | COMMAND:ARM | PASS | none |
| PV0-VAL-002 | 2 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | PASS | none |
| PV0-VAL-003 | 3 | one_side_test | DRIVE_ACTIVE | MESSAGE | CONTROL_UPDATE:deadman=true | PASS | none |
| PV0-VAL-004 | 4 | one_side_test | DRIVE_ACTIVE | TIME_ADVANCE | none | INTERNAL:communication_lost | none |
| PV0-VAL-005 | 5 | one_side_test | DRIVE_ACTIVE | MESSAGE | CONTROL_UPDATE:deadman=false | PASS;event=deadman_released | none |
| PV0-VAL-006 | 6 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP7:invalid_boot_id | invalid_boot_id |
| PV0-VAL-007 | 7 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP8:invalid_session | invalid_session |
| PV0-VAL-008 | 8 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP10:not_control_owner | not_control_owner |
| PV0-VAL-009 | 9 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:MOVE_FORWARD | STEP11:exact_duplicate | none |
| PV0-VAL-010 | 10 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP11:sequence_collision | duplicate_sequence |
| PV0-VAL-011 | 11 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP11:stale_sequence | stale_sequence |
| PV0-VAL-012 | 12 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP13:expired | expired |
| PV0-VAL-013 | 13 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP15:invalid_payload | invalid_payload |
| PV0-VAL-014L | 14 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:TURN_LEFT | STEP16:capability_unavailable | capability_unavailable |
| PV0-VAL-014R | 14 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:TURN_RIGHT | STEP16:capability_unavailable | capability_unavailable |
| PV0-VAL-015 | 15 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:PTO_START | STEP16:capability_unavailable | capability_unavailable |
| PV0-VAL-016 | 16 | one_side_test | DISARMED | MESSAGE | COMMAND:MOVE_FORWARD | STEP17:invalid_state | invalid_state |
| PV0-VAL-017 | 17 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:STOP | PASS | none |
| PV0-VAL-018 | 18 | drive_pto_split_fixture | PTO_ACTIVE | MESSAGE | COMMAND:STOP | PASS | none |
| PV0-VAL-019 | 19 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:STOP | STEP11:exact_duplicate | none |
| PV0-VAL-020 | 20 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:STOP | STEP11:stale_sequence | stale_sequence |
| PV0-VAL-021 | 21 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:STOP | STEP13:expired | expired |
| PV0-VAL-022 | 22 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:STOP | STEP8:invalid_session | invalid_session |
| PV0-VAL-023 | 23 | one_side_test | DRIVE_ACTIVE | MESSAGE | malformed candidate STOP | STEP3:malformed | none |
| PV0-VAL-024 | 24 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:STOP | STEP7:invalid_boot_id | none |
| PV0-VAL-025 | 25 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:EMERGENCY_STOP | PASS | none |
| PV0-VAL-026 | 26 | one_side_test | EMERGENCY_STOP_LATCHED | MESSAGE | COMMAND:EMERGENCY_STOP | STEP11:exact_duplicate | none |
| PV0-VAL-027 | 27 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:EMERGENCY_STOP | STEP11:stale_sequence | stale_sequence |
| PV0-VAL-028 | 28 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:EMERGENCY_STOP | STEP13:expired | expired |
| PV0-VAL-029 | 29 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:EMERGENCY_STOP | STEP8:invalid_session | invalid_session |
| PV0-VAL-030 | 30 | one_side_test | DRIVE_ACTIVE | MESSAGE | malformed candidate EMERGENCY_STOP | STEP3:malformed | none |
| PV0-VAL-031 | 31 | one_side_test | DRIVE_ACTIVE | MESSAGE | COMMAND:EMERGENCY_STOP | STEP7:invalid_boot_id | none |
| PV0-VAL-032 | 32 | one_side_test | DRIVE_READY | MESSAGE | COMMAND:MOVE_FORWARD | STEP20:output_apply_failed | none |
| PV0-VAL-033 | 33 | one_side_test | EMERGENCY_STOP_LATCHED | MESSAGE | COMMAND:emergency_stop_reset | STEP18:guard_failed | guard_failed |
| PV0-VAL-034 | 34 | one_side_test | EMERGENCY_STOP_LATCHED | MESSAGE | COMMAND:emergency_stop_reset | PASS | none |
| PV0-VAL-035 | 35 | one_side_test | COMM_LOSS_LATCHED | MESSAGE | CONTROL_UPDATE:old-session/old-operation | STEP8:invalid_session | invalid_session |
| PV0-VAL-036 | 36 | one_side_test | DRIVE_ACTIVE | MESSAGE | SESSION_END | PASS;event=communication_lost | none |

## 6. 即時期待結果 catalog

| Vector ID | Formal disposition | Defensive action | Message handling | Result source | Immediate drive/PTO output | Operation ID | Official final state | Liveness update | Accepted COMMAND sequence update | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PV0-VAL-001A | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | Yes | - |
| PV0-VAL-001B | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | ARMED_NEUTRAL | No | Yes | fixture-only profile |
| PV0-VAL-002 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=forward;P=zero | new | DRIVE_ACTIVE | Yes | Yes | - |
| PV0-VAL-003 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=same;P=zero | same | DRIVE_ACTIVE | Yes | No | COMMAND sequence unchanged |
| PV0-VAL-004 | NONE | NONE | NOT_APPLICABLE | NONE | D=zero;P=zero | invalid | COMM_LOSS_LATCHED | No | No | command result required=false |
| PV0-VAL-005 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | COMMAND sequence unchanged |
| PV0-VAL-006 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-007 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-008 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-009 | NONE | NONE | CACHE_REPLAY | CACHED_RESULT | D=same;P=zero | same | DRIVE_ACTIVE | No | No | new acceptance=false;transition/output reapply=false |
| PV0-VAL-010 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | diagnostic=sequence_collision |
| PV0-VAL-011 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-012 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-013 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-014L | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-014R | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-015 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DRIVE_READY | No | No | - |
| PV0-VAL-016 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DISARMED | No | No | - |
| PV0-VAL-017 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | Yes | - |
| PV0-VAL-018 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | PTO_READY | No | Yes | fixture-only profile |
| PV0-VAL-019 | NONE | NONE | CACHE_REPLAY | CACHED_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | new acceptance=false;transition/output reapply=false |
| PV0-VAL-020 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | - |
| PV0-VAL-021 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | - |
| PV0-VAL-022 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | - |
| PV0-VAL-023 | NONE | NONE | NO_MESSAGE_ACTION | NONE | D=same;P=zero | same | DRIVE_ACTIVE | No | No | post-watchdog required |
| PV0-VAL-024 | NONE | NONE | NO_MESSAGE_ACTION | NONE | D=same;P=zero | same | DRIVE_ACTIVE | No | No | post-watchdog required |
| PV0-VAL-025 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | EMERGENCY_STOP_LATCHED | No | Yes | - |
| PV0-VAL-026 | NONE | NONE | CACHE_REPLAY | CACHED_RESULT | D=zero;P=zero | invalid | EMERGENCY_STOP_LATCHED | No | No | new acceptance=false;transition/output reapply=false |
| PV0-VAL-027 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | formal ESTOP latch=false |
| PV0-VAL-028 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | formal ESTOP latch=false |
| PV0-VAL-029 | FORMAL_REJECT | DEFENSIVE_ZERO | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | DRIVE_READY | No | No | formal ESTOP latch=false |
| PV0-VAL-030 | NONE | NONE | NO_MESSAGE_ACTION | NONE | D=same;P=zero | same | DRIVE_ACTIVE | No | No | post-watchdog required |
| PV0-VAL-031 | NONE | NONE | NO_MESSAGE_ACTION | NONE | D=same;P=zero | same | DRIVE_ACTIVE | No | No | post-watchdog required |
| PV0-VAL-032 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | FAULT_LATCHED | No | Yes | apply=FAILED;safety=ZERO_ALL_OUTPUTS;applied=false;state_confirmed=false;fault=output_apply_failed |
| PV0-VAL-033 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | EMERGENCY_STOP_LATCHED | No | No | - |
| PV0-VAL-034 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | none | DISARMED | No | Yes | re-ARM required |
| PV0-VAL-035 | FORMAL_REJECT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | COMM_LOSS_LATCHED | No | No | - |
| PV0-VAL-036 | FORMAL_ACCEPT | NONE | PROCESS | NEW_RESULT | D=zero;P=zero | invalid | COMM_LOSS_LATCHED | No | No | COMMAND sequence not applicable |

## 7. 時間進行・post-timeout catalog

| Vector ID | Before/time trigger | Immediate state/output/op | Time advance | Post-timeout output | Post-timeout op ID | Post-timeout armed | Post-timeout state | Formal acceptance after timeout |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PV0-VAL-004 | TIME_ADVANCE; watchdog expiry; internal event=communication_lost | COMM_LOSS_LATCHED / zero / invalid | none | zero | invalid | false | COMM_LOSS_LATCHED | NONE; command result required=false |
| PV0-VAL-023 | MESSAGE; malformed STOP; NO_MESSAGE_ACTION | DRIVE_ACTIVE / same / same | independent watchdog expiry; communication_lost | zero | invalid | false | COMM_LOSS_LATCHED | NONE; no new command result |
| PV0-VAL-024 | MESSAGE; wrong boot STOP; NO_MESSAGE_ACTION | DRIVE_ACTIVE / same / same | independent watchdog expiry; communication_lost | zero | invalid | false | COMM_LOSS_LATCHED | NONE; no new command result |
| PV0-VAL-030 | MESSAGE; malformed ESTOP; NO_MESSAGE_ACTION | DRIVE_ACTIVE / same / same | independent watchdog expiry; communication_lost | zero | invalid | false | COMM_LOSS_LATCHED | NONE; no new command result |
| PV0-VAL-031 | MESSAGE; wrong boot ESTOP; NO_MESSAGE_ACTION | DRIVE_ACTIVE / same / same | independent watchdog expiry; communication_lost | zero | invalid | false | COMM_LOSS_LATCHED | NONE; no new command result |

## 8. 特殊caseの規範

Exact duplicateは`PV0-VAL-009`、`019`、`026`で、formal disposition=`NONE`、handling=`CACHE_REPLAY`、source=`CACHED_RESULT`とする。current occurrenceの新規acceptance、accepted sequence再更新、遷移・output再適用、新規operation ID発行を行わず、cached resultと現在の`STATE_SNAPSHOT`を区別する。

Defensive STOPは`020`、`021`、`022`、defensive EMERGENCY_STOPは`027`、`028`、`029`で、`FORMAL_REJECT`＋`DEFENSIVE_ZERO`、output zero、operation invalid、`DRIVE_READY`、accepted sequence更新なしとする。defensive ESTOPは正式な`EMERGENCY_STOP_LATCHED`を作らない。

Output apply failure `PV0-VAL-032`はformal disposition=`FORMAL_ACCEPT`、defensive action=`NONE`、apply=`FAILED`、safety action=`ZERO_ALL_OUTPUTS`、output zero、operation invalid、fault reason=`output_apply_failed`、`FAULT_LATCHED`、applied=false、state_confirmed=false、accepted COMMAND sequence update=trueとする。

Internal eventは`PV0-VAL-004`=`communication_lost`、`PV0-VAL-005`=`deadman_released`、`PV0-VAL-036`=`communication_lost`とする。

## 9. coverage・PASS条件

source scenarioは36、concrete vectorは38、scenario 1と14は各2、その他は34である。第5章と第6章のID集合と順序は完全一致し、重複・欠落・unexpected IDはない。official state、formal disposition、defensive action、message handling、result sourceは第3章の許可値だけを使う。NO_MESSAGE_ACTION 4件は第7章のpost-timeoutを持ち、duplicate 3件は`CACHE_REPLAY`、scenario 32は`FORMAL_ACCEPT`＋`FAILED`＋`ZERO_ALL_OUTPUTS`である。

各列が規範mapおよび上位文書と一致し、unexpected transition、output、liveness更新、sequence更新、安全ラッチ変更がない場合だけPASS候補とする。実vector、schema、コードは作成していない。

## 10. 未確定事項と次の承認対象

次の承認対象候補は`software/rover_control/protocol/v0/test_vectors/SCHEMA_REQUIREMENTS.md`である。CASE_CATALOGの列をmachine-readable vectorへ変換する際の必須性、enum候補、null / none / not applicable、cross-field validationをencoding選定前に定義する。今回は作成しない。
