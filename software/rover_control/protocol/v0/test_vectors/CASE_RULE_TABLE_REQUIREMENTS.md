# Protocol v0 Case Rule Table Requirements

## 1. 目的と適用範囲

本書は、Paddy Swarm Rover Control Protocol v0のLayer 2 semantic validatorが使用する、version-controlledなcase rule tableの要件を定める。rule tableは、38件のconcrete vectorごとの期待意味を固定するLayer 2のsemantic expectation contractである。

対象は文書化されたProtocol v0 test vectorだけであり、今回の成果物は要件文書と機械可読JSON rule tableに限定する。Layer 2 loader、validator、checkerその他の実装コードは作成しない。

## 2. trust modelと正本

安全要件、状態機械、Protocol v0文書、validation order、CASE_CATALOG、FIELD_MODELの順に上位の正本として扱う。ID-specific ruleはこれらの正本から作成し、vector本体からruleを自己生成してはならない。

manifestはvectorのidentityとintegrityを固定し、rule tableはID-specificなsemantic expectationを固定する。JSON Schemaはvectorの構造と型を検証し、rule tableは個々のIDに対する意味を検証する。concrete vectorはrule table作成後のconformance検査対象であり、rule tableの正本ではない。

Markdown sourceをruntimeで曖昧にparseしてruleを推測してはならない。承認されたrule tableを、後続承認で実装されるLayer 2が読み込む。

## 3. rule table pathとidentity

rule tableのrepository-relative pathは次のとおりとする。

```text
software/rover_control/protocol/v0/test_vectors/case_rules/protocol-v0-case-rules.json
```

identityは`rule_table_version=1`および`protocol_version=v0`で固定する。generated timestamp、absolute path、username、machine nameを含めてはならない。rule table自身のSHA256をrule table内部へ記録してはならない。

## 4. root object model

root objectは次の8 propertyだけをexact順序で持つ。

```text
rule_table_version
protocol_version
source_documents
vector_count
source_scenario_count
vector_id_order
aggregate_expectations
rules
```

固定値は`rule_table_version=1`、`protocol_version=v0`、`vector_count=38`、`source_scenario_count=36`とする。unknown root property、`null`、重複keyを禁止する。

## 5. source_documents model

`source_documents`は次の9 propertyをexact順序で持つ。

```text
safety_requirements
state_machine
protocol_readme
protocol_v0_readme
validation_order
case_catalog
field_model
vector_schema
manifest
```

各source objectは`path`、`sha256`だけをこの順序で持つ。pathはrepository-relativeな`/`区切りとし、SHA256は承認済みsource fileのlowercase 64桁hex digestと一致しなければならない。source hash不一致時はfail closedとする。

## 6. aggregate_expectations model

`aggregate_expectations`は次の7 propertyだけをexact順序で持つ。

```text
split_profile_ids
temporal_ids
cache_replay_ids
no_message_action_ids
defensive_zero_ids
accepted_sequence_update_true_ids
real_motor_output_true_count
```

各ID arrayは`vector_id_order`の相対順序に従い、重複を禁止する。固定集合は次のとおりとする。

- `split_profile_ids`: `PV0-VAL-001B`, `PV0-VAL-018`
- `temporal_ids`: `PV0-VAL-004`, `PV0-VAL-023`, `PV0-VAL-024`, `PV0-VAL-030`, `PV0-VAL-031`
- `cache_replay_ids`: `PV0-VAL-009`, `PV0-VAL-019`, `PV0-VAL-026`
- `no_message_action_ids`: `PV0-VAL-023`, `PV0-VAL-024`, `PV0-VAL-030`, `PV0-VAL-031`
- `defensive_zero_ids`: `PV0-VAL-020`, `PV0-VAL-021`, `PV0-VAL-022`, `PV0-VAL-027`, `PV0-VAL-028`, `PV0-VAL-029`
- `accepted_sequence_update_true_ids`: `PV0-VAL-001A`, `PV0-VAL-001B`, `PV0-VAL-002`, `PV0-VAL-017`, `PV0-VAL-018`, `PV0-VAL-025`, `PV0-VAL-032`, `PV0-VAL-034`
- `real_motor_output_true_count`: `0`

## 7. rule entry model

`rules`は38 objectのarrayとし、各entryは次の30 propertyだけをexact順序で持つ。

```text
vector_id
source_scenario
profile
initial_state
trigger_kind
logical_message_type
command_type
candidate_intent
parseable
terminal_step_number
terminal_step_name
formal_disposition
defensive_action
message_handling
result_source
rejection_reason
state_event
accepted_command_sequence_updated
control_liveness_updated
immediate_drive_output
immediate_pto_output
immediate_armed
immediate_operation_id
final_state
communication_loss_latch
fault_latch
emergency_stop_latch
temporal_required
post_time_state
relations
```

値が存在しない文字列fieldは空文字列とし、`null`を禁止する。PASSED_ALLまたは非message処理の`terminal_step_number`は0、validation停止時はVALIDATION_ORDERの最初の失敗step番号とする。`terminal_step_name`は停止step名と一致し、step 0では空文字列とする。

initial、validation、immediate expectationはCASE_CATALOGとSTATE_MACHINEに一致しなければならない。CONTROL_UPDATEはaccepted COMMAND sequenceを更新しない。accepted sequence flagは固定された8 IDだけをtrueとする。

## 8. relation model

各ruleの`relations`は次の9 propertyだけをexact順序で持つ。

```text
sequence
freshness
boot_id
session_id
controller_ownership
active_operation
cached_identity
watchdog
first_failure
```

許可値は次のとおりとする。

- `sequence`: `NEW`, `EXACT_DUPLICATE`, `COLLISION`, `STALE`, `NOT_APPLICABLE`
- `freshness`: `WITHIN_TTL`, `EXPIRED`, `NOT_APPLICABLE`
- `boot_id`: `MATCH`, `MISMATCH`, `UNAVAILABLE`, `NOT_APPLICABLE`
- `session_id`: `MATCH`, `MISMATCH`, `UNAVAILABLE`, `NOT_APPLICABLE`
- `controller_ownership`: `OWNER`, `NON_OWNER`, `UNAVAILABLE`, `NOT_APPLICABLE`
- `active_operation`: `MATCH_CURRENT`, `OLD_OR_INVALID`, `PRESENT`, `ABSENT`, `NOT_APPLICABLE`
- `cached_identity`: `MATCH`, `SEQUENCE_MATCH_MESSAGE_ID_DIFFERS`, `ABSENT`, `NOT_APPLICABLE`
- `watchdog`: `ADVANCE_COVERS_REMAINING`, `NOT_APPLICABLE`
- `first_failure`: `NONE`, `CAPABILITY_BEFORE_STATE`, `SESSION_BEFORE_OPERATION_AND_STATE`

relationはCASE_CATALOGおよびVALIDATION_ORDERから決定する。formal acceptanceとdefensive zeroを混同してはならず、malformedまたはwrong-bootのSTOP・EMERGENCY_STOPは`NO_MESSAGE_ACTION`とする。

## 9. orderingと一意性

`vector_id_order`、`rules`、aggregate内のID arrayは承認済み38 IDのexact順序に従う。各ruleの`vector_id`は一意であり、`rules`のID列は`vector_id_order`と完全一致しなければならない。missing ID、unexpected ID、重複ID、rule order mismatchはすべてfailureとする。

object propertyのpresentation orderも本書で指定した順序と完全一致させる。unknown propertyおよびproperty欠落を禁止する。

## 10. source scenario coverage

source scenarioは1から36までを完全にcoverする。scenario 1は`PV0-VAL-001A`と`PV0-VAL-001B`の2件、scenario 14は`PV0-VAL-014L`と`PV0-VAL-014R`の2件とし、その他のscenarioは各1件とする。

profile splitはfixture差だけを表し、`one_side_test`でTURNとPTO capabilityを利用可能にしてはならない。全ruleで実motor出力を禁止し、`real_motor_output_true_count`は0とする。

## 11. vector conformance validation

rule table作成後、独立した一時checkerでraw format、Strict JSON、root model、source hash、ID order、rule/relation model、一意性、aggregate、manifest identity、vector core expectation、relation、state invariant、terminal stepを順に検査する。

current manifestとはID、scenario、profile、accepted flagを照合する。current vectorとはinitial、validation、immediate、temporal expectationを照合する。CASE_CATALOGとはscenario別期待を、STATE_MACHINEとはstate、armed、output、latchを、VALIDATION_ORDERとはfirst-failure terminal stepを照合する。

一時checkerはrule table自身から期待値を生成してはならない。少なくとも30件のdeep-copy negative mutationをすべて検出し、negative JSON、checkerコード、fixtureをrepositoryへ保存してはならない。

## 12. failure handling

Strict JSON違反、duplicate key、source hash不一致、unknown property、property順序違反、missing/unexpected/duplicate rule、coverage不一致、aggregate不一致、manifest不一致、vector conformance不一致、state invariant不一致、terminal step不一致、negative mutationのunexpected passが1件でもあればFAILとして扱う。

FAIL時は推測による補正、曖昧なfallback、部分的acceptを行わない。正本間に解決不能な矛盾がある場合はrule tableを承認対象として扱わない。

## 13. security・safety境界

rule tableはoffline test vectorの期待意味を検証する補助contractであり、runtime state machine、通信経路、motor出力、実機安全を保証しない。物理ESTOPはソフトウェアから独立した安全手段でなければならない。

valid EMERGENCY_STOPだけが`EMERGENCY_STOP_LATCHED`へ遷移し、invalid ESTOPはlatchを成立させてはならない。reset成功後も`armed=false`とし、reconnectまたはSESSION_END後にoperationやARMを自動復元しない。DRIVEとPTO outputを同時activeにしてはならず、temporal caseでは即時結果とpost-time結果を混同しない。

rule tableにsecret、token、個人情報、農地位置、absolute path、backslash path、username、machine name、AppData、temp path、timestampを含めてはならない。network、package、hardware accessを前提としない。

## 14. 非目標と次の承認対象

今回はLayer 2 validator、case rule loader、runtime checker、case rule JSON Schema、manifest schema、test runner、package設定、fixtureを作成しない。Phase 1、manifest、vector、vector schema、既存文書を変更しない。

次の承認対象は、本rule tableを入力としてfail closedに動作するLayer 2 loaderおよびsemantic validatorの設計・実装・testである。実装は本rule tableの承認後に、別の明示的な作業として行う。
