# Paddy Swarm Rover Control Protocol v0 Test Vector Field Model

Status: Draft field contract / Strict JSON property model / No schema file yet / No vector files yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書はtest vector用のStrict JSON field contractである。wire protocol field、JSON Schema本体、JSON sampleではなく、CASE_CATALOGの意味を変更せず、実機モーター試験を承認しない。完成JSON object例は掲載しない。

## 2. 参照文書と優先順位

- JSON schema decision: `software/rover_control/protocol/v0/test_vectors/JSON_SCHEMA_DECISION.md`; SHA256 `f387ab5db14d7718c95a19d448af087683199b8244e4cb4f83e561e1040e70a4`
- encoding decision: `software/rover_control/protocol/v0/test_vectors/ENCODING_DECISION.md`; SHA256 `0fa8d42b406f8751ca46a51246a58448e9d02f6c610f576a2d14b8ac5650a6bf`
- schema requirements: `software/rover_control/protocol/v0/test_vectors/SCHEMA_REQUIREMENTS.md`; SHA256 `32d4b47623bcf5fe730ff100469b6e8c87fa3d71f4044b572598c0bef34a6f55`
- case catalog: `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`; SHA256 `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d`
- protocol version: `v0`; schema version: `1`; concrete vectors: `38`

上位文書を優先し、そのSHA256変更時は本文書を再レビューする。

## 3. 命名・型・presenceの共通規則

property名はcase-sensitive lowercase `snake_case`とし、aliasとunknown propertyを認めない。JSON `null`、安全項目のdefault補完、暗黙type/case変換、boolean文字列、空文字によるNONE代用を禁止する。REQUIREDをnull/空objectで満たさず、FORBIDDENはmember自体を省略する。object key順序は意味を持たず、array順序は意味を持つ。presenceは`REQUIRED`、`CONDITIONAL`、`OPTIONAL`、`FORBIDDEN`の4件だけとする。

## 4. root objectと11 logical group

| Group | Presence | Constraint |
| --- | --- | --- |
| identity | REQUIRED | closed object |
| source | REQUIRED | closed object |
| profile_and_capability | REQUIRED | closed object |
| initial_fixture | REQUIRED | closed object |
| stimulus | REQUIRED | closed object |
| validation_expectation | REQUIRED | closed object |
| immediate_expectation | REQUIRED | closed object |
| time_advance | CONDITIONAL | temporal 5 IDだけREQUIRED |
| post_time_expectation | CONDITIONAL | temporal 5 IDだけREQUIRED |
| observability | REQUIRED | closed object |
| notes | OPTIONAL | closed object |

temporal 5 IDは`PV0-VAL-004`、`023`、`024`、`030`、`031`で、time/postを両方REQUIREDとする。他33 IDでは両方FORBIDDENとし、片方だけを禁止する。12番目のroot propertyを追加しない。

## 5. identity

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| vector_id | string | REQUIRED | approved 38 ID exact set | filename stemと一致 |
| title | string | REQUIRED | 1–120 characters | case title |
| schema_version | integer | REQUIRED | const 1 | schema version |
| protocol_version | string | REQUIRED | const `v0` | protocol version |

vector_idは`PV0-VAL-`prefixを持ち、message/session/operation IDへ流用しない。

## 6. source

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| validation_document_path | string | REQUIRED | `software/rover_control/protocol/v0/VALIDATION_ORDER.md` | validation source |
| validation_document_sha256 | string | REQUIRED | `ed600175566a55ad7eea921d2471107ad5d7ee9d86168054ecb7f647e0608e4a` | source hash |
| validation_chapter | integer | REQUIRED | const 17 | source chapter |
| source_scenario | integer | REQUIRED | 1–36 | source scenario |
| case_catalog_path | string | REQUIRED | `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md` | catalog path |
| case_catalog_sha256 | string | REQUIRED | `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d` | catalog hash |

pathはrepository-relative `/`区切りとし、absolute、backslash、parent traversalを禁止する。

## 7. profile_and_capability

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| profile | string | REQUIRED | `one_side_test`, `drive_pto_split_fixture` | fixture profile |
| drive_available | boolean | REQUIRED | true | drive capability |
| turn_left_available | boolean | REQUIRED | false | left turn capability |
| turn_right_available | boolean | REQUIRED | false | right turn capability |
| pto_available | boolean | REQUIRED | profile mapping | PTO capability |
| right_output_available | boolean | REQUIRED | false | right output capability |
| real_motor_output_enabled | boolean | REQUIRED | const false | motor safety gate |

one_side_testはdrive=true、turn=false、PTO=false、right=false、motor=false。drive_pto_split_fixtureはdrive=true、turn=false、PTO=true、right=false、motor=falseで、scenario 1B/18用simulator fixture名であり実機profileではない。

## 8. initial_fixture

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| official_state | string | REQUIRED | official 10 states | initial state |
| armed | boolean | REQUIRED | boolean | armed flag |
| drive_output | string | REQUIRED | `zero`, `forward` | drive output |
| pto_output | string | REQUIRED | `zero`, `active` | PTO output |
| safety_latches | object | REQUIRED | latch fields below | latch fixture |
| rover_boot_id | string | REQUIRED | ID pattern | boot fixture |
| session_id | string | REQUIRED | ID pattern | session fixture |
| controller_owner_present | boolean | REQUIRED | boolean | owner presence |
| controller_owner_id | string | CONDITIONAL | present iff flag=true | owner ID |
| last_seen_sequence_present | boolean | REQUIRED | boolean | sequence presence |
| last_seen_sequence | integer | CONDITIONAL | 0–9007199254740991 | last seen |
| last_accepted_command_sequence_present | boolean | REQUIRED | boolean | accepted sequence presence |
| last_accepted_command_sequence | integer | CONDITIONAL | 0–9007199254740991 | last accepted |
| active_operation_present | boolean | REQUIRED | boolean | operation presence |
| active_operation_id | string | CONDITIONAL | present iff flag=true | active operation |
| selected_mode | string | REQUIRED | `NONE`, `DRIVE`, `PTO`, `NEUTRAL` | selected mode |
| monotonic_time_ms | integer | REQUIRED | non-negative safe integer | test time |
| freshness_reference_ms | integer | REQUIRED | non-negative safe integer | freshness reference |
| watchdog_remaining_ms | integer | REQUIRED | non-negative safe integer | remaining time |
| cached_command_result_present | boolean | REQUIRED | boolean | cache presence |
| cached_command_result | object | CONDITIONAL | present iff flag=true | cached result |

| safety_latches Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| communication_loss | boolean | REQUIRED | boolean | communication latch |
| fault | boolean | REQUIRED | boolean | fault latch |
| emergency_stop | boolean | REQUIRED | boolean | ESTOP latch |

| cached_command_result Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| message_id | string | REQUIRED | ID pattern | original message |
| sequence | integer | REQUIRED | safe integer | original sequence |
| formal_disposition | string | REQUIRED | approved formal enum | original disposition |
| rejection_reason | string | CONDITIONAL | required only if rejected | original rejection |
| applied_success | boolean | REQUIRED | boolean | original apply result |
| state_confirmed_success | boolean | REQUIRED | boolean | original confirmation |

各present=falseなら対応value fieldはFORBIDDEN。DRIVE_ACTIVE/PTO_ACTIVEはactive operationを要求する。cacheとcurrent snapshotを混同しない。

初期fixtureのstate不変条件は次を規範とする。

| official_state | armed | drive_output | pto_output | safety_latches |
| --- | ---: | --- | --- | --- |
| BOOT_SAFE | false | `zero` | `zero` | all false |
| DISARMED | false | `zero` | `zero` | all false |
| ARMED_NEUTRAL | true | `zero` | `zero` | all false |
| DRIVE_READY | true | `zero` | `zero` | all false |
| DRIVE_ACTIVE | true | `forward` | `zero` | all false |
| PTO_READY | true | `zero` | `zero` | all false |
| PTO_ACTIVE | true | `zero` | `active` | all false |
| COMM_LOSS_LATCHED | false | `zero` | `zero` | communication_loss=true |
| FAULT_LATCHED | false | `zero` | `zero` | fault=true |
| EMERGENCY_STOP_LATCHED | false | `zero` | `zero` | emergency_stop=true |

したがってDRIVE_READYでarmed=false、drive_output=forward、pto_output=activeは禁止し、DRIVE_ACTIVEでarmed=falseも禁止する。DRIVE_ACTIVE/PTO_ACTIVEのactive_operation_present=true要件は維持する。non-latched 7状態では3 latchをすべてfalseとし、latched状態では対応latch=trueを必須にする。上位状態機械が複数異常理由の保持を要求するため、latched状態の対応外latchはfalseへ固定しない。

## 9. stimulus

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| trigger_kind | string | REQUIRED | `MESSAGE`, `TIME_ADVANCE`, `INTERNAL_EVENT` | trigger |
| message | object | CONDITIONAL | MESSAGEだけREQUIRED | input message |
| internal_event | string | CONDITIONAL | INTERNAL_EVENTだけREQUIRED | direct internal event |
| output_apply_result | string | REQUIRED | `SUCCESS`, `FAILED`, `NOT_APPLICABLE` | Step 20 outcome |

| message Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| logical_message_type | string | CONDITIONAL | official 12 types | parsed type |
| command_type | string | CONDITIONAL | official 16 commands | COMMAND subtype |
| candidate_intent | string | CONDITIONAL | `STOP`, `EMERGENCY_STOP` | malformed fixture intent |
| direction | string | REQUIRED | transport fixture direction | direction |
| size_valid | boolean | REQUIRED | boolean | Step 2 |
| parseable | boolean | REQUIRED | boolean | Step 3 |
| protocol_version | string | CONDITIONAL | `v0` or invalid fixture value | parsed version |
| rover_boot_id | string | CONDITIONAL | string | boot ID |
| session_id | string | CONDITIONAL | string | session ID |
| sender_role | string | CONDITIONAL | string | sender role |
| controller_ownership | boolean | CONDITIONAL | boolean | ownership |
| message_id | string | CONDITIONAL | ID pattern | message ID |
| sequence | integer | CONDITIONAL | safe integer | sequence |
| freshness_age_ms | integer | CONDITIONAL | non-negative safe integer | age |
| ttl_ms | integer | CONDITIONAL | non-negative safe integer | TTL |
| required_fields_present | boolean | CONDITIONAL | boolean | required fields |
| payload_valid | boolean | CONDITIONAL | boolean | payload validity |
| capability_compatible | boolean | CONDITIONAL | boolean | capability |
| state_compatible | boolean | CONDITIONAL | boolean | state |
| guard_passed | boolean | CONDITIONAL | boolean | safety guard |
| control_update_deadman | boolean | CONDITIONAL | CONTROL_UPDATE only | deadman |
| operation_id | string | CONDITIONAL | CONTROL_UPDATE only | operation reference |

MESSAGEはmessage REQUIRED/internal_event FORBIDDEN、TIME_ADVANCEは両方FORBIDDEN、INTERNAL_EVENTはmessage FORBIDDEN/internal_event REQUIRED。parseable=falseはlogical_message_typeとparse後fieldをFORBIDDEN、malformed STOP/ESTOPはcandidate_intent REQUIRED。parseable=trueはcandidate_intent FORBIDDEN。parsed COMMANDはcommand_type REQUIRED、非COMMANDはFORBIDDEN。CONTROL_UPDATEはdeadman/operation REQUIRED、それ以外はFORBIDDEN。directionはMESSAGEでREQUIRED。scenario 32はFAILED、Step 20正常完了はSUCCESS、reject/cache/NO_MESSAGE_ACTION/TIME_ADVANCE/未到達はNOT_APPLICABLE。

## 10. validation_expectation

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| processing_path | string | REQUIRED | 4 processing paths | harness path |
| terminal_step_number | integer | CONDITIONAL | 1–23 | terminal step |
| terminal_step_name | string | CONDITIONAL | official step name | terminal step |
| handling_code | string | CONDITIONAL | approved diagnostic metadata | special handling |
| formal_disposition | string | REQUIRED | 3 formal values | formal result |
| defensive_action | string | REQUIRED | 2 defensive values | defensive result |
| message_handling | string | REQUIRED | 4 handling values | message action |
| result_source | string | REQUIRED | 3 source values | result origin |
| rejection_reason | string | CONDITIONAL | official 18 reasons | rejection |
| diagnostic_code | string | CONDITIONAL | e.g. sequence_collision | diagnostic only |
| state_machine_event_generated | boolean | REQUIRED | boolean | event generated |
| state_machine_event | string | CONDITIONAL | official 23 events | state event |
| accepted_command_sequence_updated | boolean | REQUIRED | boolean | accepted sequence change |
| result_cache_updated | boolean | REQUIRED | boolean | cache update |
| control_liveness_updated | boolean | REQUIRED | boolean | liveness update |

processing pathsは`PASSED_ALL`、`STOPPED_AT_VALIDATION_STEP`、`OUTPUT_APPLY_FAILED`、`NOT_APPLICABLE`で、validation outcomeではない。PASSED_ALL/NOT_APPLICABLEはterminal fields FORBIDDEN、STOPPEDは両方REQUIRED、OUTPUT_APPLY_FAILEDはstep 20/name REQUIRED。rejection_reasonはFORMAL_REJECTだけREQUIRED、それ以外は原則FORBIDDEN。collisionでは正式reasonとdiagnosticを分離する。

## 11. immediate_expectation

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| drive_output | string | REQUIRED | `zero`, `forward`, `same` | immediate drive |
| pto_output | string | REQUIRED | `zero`, `same` | immediate PTO |
| armed | boolean | REQUIRED | boolean | armed result |
| operation_id | string | REQUIRED | `new`, `same`, `invalid`, `none` | operation expectation |
| official_state | string | REQUIRED | official 10 states | final state |
| safety_latches | object | REQUIRED | same 3 booleans as fixture | final latches |
| last_accepted_command_sequence | string | REQUIRED | `same`, `stimulus_sequence` | sequence result |
| output_apply_safety_action | string | REQUIRED | `ZERO_ALL_OUTPUTS`, `NONE` | apply safety action |
| applied_success | boolean | REQUIRED | boolean | physical apply success |
| state_confirmed_success | boolean | REQUIRED | boolean | confirmation success |
| stop_reason | string | CONDITIONAL | approved command/event name | stop cause |
| fault_reason | string | CONDITIONAL | approved fault code | fault cause |

fault_reasonは新規FAULT_LATCHEDでREQUIRED、scenario 32は`output_apply_failed`、不要時FORBIDDEN。stop_reasonはCONDITIONALで曖昧な自然文を禁止する。

即時expectationのstate不変条件は次を規範とする。

| official_state | armed | drive_output | pto_output | safety_latches |
| --- | ---: | --- | --- | --- |
| BOOT_SAFE | false | `zero` | `zero` | all false |
| DISARMED | false | `zero` | `zero` | all false |
| ARMED_NEUTRAL | true | `zero` | `zero` | all false |
| DRIVE_READY | true | `zero` | `zero` | all false |
| DRIVE_ACTIVE | true | `forward` or `same` | `zero` | all false |
| PTO_READY | true | `zero` | `zero` | all false |
| PTO_ACTIVE | true | `zero` | `same` | all false |
| COMM_LOSS_LATCHED | false | `zero` | `zero` | communication_loss=true |
| FAULT_LATCHED | false | `zero` | `zero` | fault=true |
| EMERGENCY_STOP_LATCHED | false | `zero` | `zero` | emergency_stop=true |

non-latched 7状態では3 latchをすべてfalseとし、latched状態では対応latch=trueを必須にする。latched状態の対応外latchはfalseへ固定しない。scenario 32はformal=FORMAL_ACCEPT、defensive=NONE、apply=FAILED、safety=ZERO_ALL_OUTPUTS、drive_output=zero、pto_output=zero、armed=false、operation_id=invalid、official_state=FAULT_LATCHED、fault=true、fault_reason=output_apply_failed、applied_success=false、state_confirmed_success=falseとする。

## 12. time_advance

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| advance_ms | integer | REQUIRED | non-negative safe integer | monotonic advance |
| watchdog_expiry_expected | boolean | REQUIRED | true for temporal 5 | watchdog expectation |
| internal_event | string | REQUIRED | `communication_lost` for temporal 5 | timeout event |

semantic validatorはadvance_msがinitial watchdog remainingを満たすことを確認し、real sleepを使わない。

## 13. post_time_expectation

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| drive_output | string | REQUIRED | `zero` | post-timeout drive |
| pto_output | string | REQUIRED | `zero` | post-timeout PTO |
| operation_id | string | REQUIRED | `invalid` | operation result |
| armed | boolean | REQUIRED | false | armed result |
| official_state | string | REQUIRED | `COMM_LOSS_LATCHED` | timeout state |
| formal_disposition | string | REQUIRED | `NONE` | no command acceptance |
| command_result_required | boolean | REQUIRED | false | no new result |
| accepted_command_sequence_updated | boolean | REQUIRED | false | no sequence update |
| control_liveness_updated | boolean | REQUIRED | false | no liveness extension |

無効messageをwatchdog後に正式受理しない。

## 14. observability

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| command_result_required | boolean | REQUIRED | boolean | result expected |
| command_result_source | string | CONDITIONAL | NEW_RESULT/CACHED_RESULT | result source |
| command_result_formal_disposition | string | CONDITIONAL | formal enum | result disposition |
| command_result_rejection_reason | string | CONDITIONAL | official reason | result rejection |
| state_snapshot_required | boolean | REQUIRED | boolean | snapshot expectation |
| telemetry_update_required | boolean | REQUIRED | boolean | telemetry expectation |
| safety_log_required | boolean | REQUIRED | boolean | log expectation |
| cached_result_replay_expected | boolean | REQUIRED | boolean | cache replay expectation |

command_result_required=falseは詳細3 fieldsをFORBIDDEN、trueはsource/disposition REQUIRED。reject resultだけreason REQUIRED。CACHE_REPLAYはsource=CACHED_RESULTかつreplay=true。TIME_ADVANCE scenario 4はresult required=false。snapshot/telemetry/logはmessage resultと独立する。

## 15. notes

| Property | JSON type | Presence | Allowed values / constraint | Meaning |
| --- | --- | --- | --- | --- |
| summary | string | REQUIRED if notes exists | 1–500 characters | human summary |
| tags | array of string | OPTIONAL | max 16; each 1–32; unique | review tags |

secret、個人情報、農地座標を禁止し、notesで規範field不足を補わない。

## 16. 共通enum・pattern・ID規則

| Set | Count | Exact values/source |
| --- | ---: | --- |
| official states | 10 | BOOT_SAFE, DISARMED, ARMED_NEUTRAL, DRIVE_READY, DRIVE_ACTIVE, PTO_READY, PTO_ACTIVE, COMM_LOSS_LATCHED, FAULT_LATCHED, EMERGENCY_STOP_LATCHED |
| message types | 12 | SESSION_HELLO, SESSION_ACCEPTED, SESSION_REJECTED, SESSION_END, CAPABILITY_SNAPSHOT, COMMAND, CONTROL_UPDATE, COMMAND_RESULT, STATE_SNAPSHOT, TELEMETRY, ROVER_HEARTBEAT, DIAGNOSTIC |
| command types | 16 | ARM, DISARM, SET_SPEED_LIMIT, SELECT_DRIVE, SELECT_NEUTRAL, SELECT_PTO, MOVE_FORWARD, MOVE_REVERSE, TURN_LEFT, TURN_RIGHT, STOP, EMERGENCY_STOP, PTO_START, PTO_STOP, fault_reset, emergency_stop_reset |
| validation steps | 23 | transportから受信, message size上限候補, parse可能性, protocol version, message type, direction, rover boot ID, session ID, sender role, controller ownership, sequence / duplicate / stale, freshness reference, TTL / expiry, 必須項目, payload範囲, capability, current state, safety guard, state transition決定, 出力適用, COMMAND_RESULT生成, STATE_SNAPSHOTまたはtelemetry更新, ログ候補 |
| rejection reasons | 18 | unsupported_version, invalid_message_type, wrong_direction, invalid_boot_id, invalid_session, not_control_owner, duplicate_sequence, stale_sequence, expired, malformed, missing_required_field, invalid_payload, invalid_state, guard_failed, not_armed, mode_conflict, capability_unavailable, safety_latched |
| state machine events | 23 | boot_complete, boot_failed, SET_SPEED_LIMIT, ARM, SELECT_DRIVE, SELECT_PTO, SELECT_NEUTRAL, MOVE_FORWARD, MOVE_REVERSE, TURN_LEFT, TURN_RIGHT, STOP, deadman_released, command_expired, PTO_START, PTO_STOP, DISARM, communication_restored, fault_reset, emergency_stop_reset, EMERGENCY_STOP, communication_lost, fault_detected |
| profiles | 2 | one_side_test, drive_pto_split_fixture |
| trigger kinds | 3 | MESSAGE, TIME_ADVANCE, INTERNAL_EVENT |
| formal dispositions | 3 | FORMAL_ACCEPT, FORMAL_REJECT, NONE |
| defensive actions | 2 | DEFENSIVE_ZERO, NONE |
| message handling | 4 | PROCESS, NO_MESSAGE_ACTION, CACHE_REPLAY, NOT_APPLICABLE |
| result sources | 3 | NEW_RESULT, CACHED_RESULT, NONE |
| output apply results | 3 | SUCCESS, FAILED, NOT_APPLICABLE |
| output apply safety actions | 2 | ZERO_ALL_OUTPUTS, NONE |
| operation ID expectations | 4 | new, same, invalid, none |
| processing paths | 4 | PASSED_ALL, STOPPED_AT_VALIDATION_STEP, OUTPUT_APPLY_FAILED, NOT_APPLICABLE |

generic ID pattern候補は`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`、SHA256は`^[0-9a-f]{64}$`とする。vector IDはpatternに加え承認済み38 ID exact setで検証する。

## 17. group・field presence matrix

| Condition | Required | Forbidden |
| --- | --- | --- |
| temporal 5 IDs | time_advance, post_time_expectation | none |
| other 33 IDs | standard 8 required root groups | time_advance, post_time_expectation |
| trigger MESSAGE | stimulus.message | stimulus.internal_event |
| trigger TIME_ADVANCE | time_advance | stimulus.message, stimulus.internal_event |
| trigger INTERNAL_EVENT | stimulus.internal_event | stimulus.message |
| parseable=false | candidate_intent for malformed STOP/ESTOP | logical_message_type and parsed fields |
| parseable=true | parsed fields by type | candidate_intent |
| parsed COMMAND | command_type | CONTROL_UPDATE-only fields |
| CONTROL_UPDATE | control_update_deadman, operation_id | command_type |
| present flag=true | paired value field | none |
| present flag=false | none | paired value field |
| initial_fixture official 10 states | state別armed/output、active stateのactive operation、state別latch | state不変条件に反する値 |
| immediate_expectation official 10 states | state別armed/output/latch、FAULT_LATCHEDのfault_reason | state不変条件に反する値 |
| NO_MESSAGE_ACTION 4 IDs | time_advance, post_time_expectation、catalog固定のimmediate fields | state/output/latch不変条件に反する値 |

accepted COMMAND sequence update=trueは`PV0-VAL-001A`, `001B`, `002`, `017`, `018`, `025`, `032`, `034`の8 IDだけである。CONTROL_UPDATE、SESSION_END、duplicate、reject、defensive、NO_MESSAGE_ACTION、TIME_ADVANCEはfalseとする。

## 18. cross-field validation

- Root temporal: 指定5 IDはtime/post両方REQUIRED、他は両方FORBIDDEN、片方だけ禁止。
- CACHE_REPLAY: formal=NONE、defensive=NONE、source=CACHED_RESULT、accepted update=false、reapplyなし、新operation禁止、cached fixture REQUIRED。
- NO_MESSAGE_ACTION 4 ID（`PV0-VAL-023`、`024`、`030`、`031`）: formal=NONE、defensive=NONE、drive_output=same、pto_output=zero、armed=true、operation_id=same、official_state=DRIVE_ACTIVE、3 latch=false、last accepted sequence=same、liveness=false、post-timeout REQUIRED。pto_output=zeroはinitial PTO outputがzeroである具体的期待値であり、出力の再適用を意味しない。
- DEFENSIVE_ZERO: formal=FORMAL_REJECT、operation invalid、outputs zero、accepted update=false、latch解除禁止。
- OUTPUT_APPLY_FAILED: apply FAILED、formal ACCEPT、defensive NONE、safety ZERO_ALL_OUTPUTS、applied/confirmed false、operation invalid、FAULT_LATCHED、fault reason REQUIRED。
- TIME_ADVANCE: stimulus message禁止、processing NOT_APPLICABLE、handling NOT_APPLICABLE、formal NONE、command result false、communication loss後COMM_LOSS_LATCHED。

processing_pathをvalidation outcomeとして扱わず、malformed candidateをparsed commandとしない。scenario 4と32は上記組合せ以外を拒否する。

## 19. CASE_CATALOG列との対応

| CASE_CATALOG column | FIELD_MODEL path |
| --- | --- |
| ID | identity.vector_id |
| source | source.source_scenario |
| profile | profile_and_capability.profile |
| initial state | initial_fixture.official_state |
| trigger | stimulus.trigger_kind |
| stimulus | stimulus.message / stimulus.internal_event / time_advance |
| validation/event | validation_expectation.processing_path / terminal step / state event |
| formal disposition | validation_expectation.formal_disposition |
| defensive action | validation_expectation.defensive_action |
| message handling | validation_expectation.message_handling |
| result source | validation_expectation.result_source |
| rejection reason | validation_expectation.rejection_reason |
| immediate output | immediate_expectation.drive_output / pto_output |
| operation ID | immediate_expectation.operation_id |
| final state | immediate_expectation.official_state |
| liveness | validation_expectation.control_liveness_updated |
| accepted COMMAND sequence update | validation_expectation.accepted_command_sequence_updated |
| temporal result | time_advance / post_time_expectation |

CASE_CATALOGの全列情報を失わない。

## 20. 未確定事項と次の承認対象

schema title、`$defs`内部名、file/depth limits、validator library/version、error report、semantic validator、manifest、fixture ID、time/sequence具体値は未確定である。11 root名、presence、field名/type/enum、null禁止、motor=false、temporal 5 ID、accepted update 8 IDに加え、本書の正式10状態に対するarmed/output/latch不変条件、NO_MESSAGE_ACTION 4 IDのcatalog表現、scenario 32のarmed=falseを含む組合せは確定済みであり、未確定へ戻さない。

次工程候補は`software/rover_control/protocol/v0/test_vectors/VALIDATION_LIMITS.md`である。file size、nesting、string/array length、integer field別上限、parser resource、Layer 0拒否条件を決定する。今回は作成しない。
