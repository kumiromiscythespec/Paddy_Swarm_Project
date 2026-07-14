# Paddy Swarm Rover Control Protocol v0 JSON Schema Decision

Status: Draft decision / JSON Schema Draft 2020-12 selected / No schema file yet / No vector files yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書はStrict JSON test vectorのschema方式とvalidation責任境界を決定する。wire protocol schemaの決定文書ではない。JSON Schema本体、JSON vector、field model、manifest、parser、validator、simulatorはまだ作成しない。

## 2. 参照文書と優先順位

- encoding decision: `software/rover_control/protocol/v0/test_vectors/ENCODING_DECISION.md`
- encoding decision SHA256: `0fa8d42b406f8751ca46a51246a58448e9d02f6c610f576a2d14b8ac5650a6bf`
- schema requirements: `software/rover_control/protocol/v0/test_vectors/SCHEMA_REQUIREMENTS.md`
- schema requirements SHA256: `32d4b47623bcf5fe730ff100469b6e8c87fa3d71f4044b572598c0bef34a6f55`
- case catalog: `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`
- case catalog SHA256: `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d`
- protocol version: `v0`
- concrete vector count: 38

優先順位は物理安全設計、SAFETY_REQUIREMENTS、STATE_MACHINE、protocol README、protocol v0 README、VALIDATION_ORDER、test vector format README、CASE_CATALOG、SCHEMA_REQUIREMENTS、ENCODING_DECISION、本文書とする。本文書は上位文書の意味を変更しない。

## 3. schema方式の選定条件

Strict JSON適合、Python/TypeScript validator対応、cross-field・conditional表現、unknown property・null拒否、enum/pattern/range、local reference、remote禁止、offline validation、error location、tool成熟度、determinism、version管理、攻撃面、C/C++ simulator連携、human reviewを評価する。

## 4. 比較対象

比較対象はJSON Schema Draft 2020-12、JSON Schema Draft 7、OpenAPI 3.1 Schema、TypeScript type only、Python model only、Handwritten validator onlyの6件だけとする。

## 5. 比較結果

| Candidate | Strict JSON fit | Conditional rules | Python/TS support | Offline use | Cross-language source of truth | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| JSON Schema Draft 2020-12 | Strong | Strong | Both have candidates | Yes | Yes | SELECTED |
| JSON Schema Draft 7 | Strong | Moderate | Broad | Yes | Yes | REJECTED |
| OpenAPI 3.1 Schema | Strong | Moderate | Available | Yes | API-oriented | REJECTED |
| TypeScript type only | Partial | Language code | TypeScript only | Yes | No | REJECTED |
| Python model only | Partial | Language code | Python only | Yes | No | REJECTED |
| Handwritten validator only | Flexible | Flexible | Separate implementations | Yes | Weak | REJECTED |

Draft 2020-12はStrict JSON、`if`/`then`/`else`、`allOf`、`oneOf`、`not`、`const`、`enum`、`dependentRequired`、`dependentSchemas`、`$defs`、`unevaluatedProperties`を扱い、Python/TypeScript双方のvalidator候補と単一のcross-language sourceを持てるため選択する。Draft 7は新規基準としてcomposition・unevaluated処理が弱い。OpenAPIは不要なAPI要素を伴う。言語固有type/modelはruntimeまたはcross-language sourceにならず、handwritten-onlyは仕様乖離リスクが高い。

## 6. 最終決定

```text
selected_schema_language=JSON Schema
selected_dialect=Draft 2020-12
selected_schema_count=1
schema_and_semantic_validator_both_required=true
schema_file_created=false
```

JSON Schemaだけで全安全意味を保証したことにしない。

## 7. draft・dialect・schema identity

```text
schema_keyword_uri=https://json-schema.org/draft/2020-12/schema
schema_id=urn:paddy-swarm:protocol:v0:test-vector-schema:1
schema_version=1
protocol_version=v0
```

schema versionとprotocol versionを分離する。将来の`$schema`は上記URI、`$id`は上記URNを用いる。URNを取得URLとして扱わずnetwork accessしない。Draft 2020-12 meta-schemaはvalidatorへ内蔵または事前bundleし、validation中のremote fetchを禁止する。schema IDをvector/message/operation IDへ流用しない。JSON schema例は掲載しない。

## 8. 将来のschemaファイル配置

将来のschema pathは`software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json`とする。schemaは1件で、1 test vectorのroot objectを検証し、38件をまとめたarray schemaにはしない。manifest schemaは別承認とする。今回は`schema/`もschema fileも作成しない。filenameはlowercase kebab-case、pathはrepository-relativeとする。

## 9. self-contained schemaと参照方針

```text
schema_document_model=single_self_contained_file
external_ref_allowed=false
remote_ref_allowed=false
local_fragment_ref_allowed=true
local_definition_container=$defs
```

許可する参照は`#/$defs/<definition-name>`だけである。HTTP/HTTPS `$ref`、file URI、repository外、別schema file、recursive remote fetch、dynamic network resolutionを禁止する。`$dynamicRef`や外部vocabularyに依存しない。meta-schemaは事前bundleしnetwork取得しない。

## 10. object closureとunknown property

unknown propertyは常にvalidation failureとし、無視して実行しない。各独立object definitionは原則`additionalProperties: false`、composition境界では`unevaluatedProperties: false`を使用できる。`allOf`やconditional branchを壊す位置へ機械的にclosureを置かず、actual schemaでcomposition testを行う。rootも閉じ、11 group外を無条件許可しない。exact root fieldはFIELD_MODEL承認後に固定し、extension/vendor fieldや`x-`特例をv0では設けない。

## 11. type・enum・pattern・range方針

safety-critical fieldへ暗黙defaultを設定せず、`default`を補完命令として使わない。JSON `null`をtypeに含めない。booleanは`boolean`、ID/enumは`string`、数値は`integer`、timeは非負integer、最大安全整数は`9007199254740991`とする。SHA256はanchored lowercase 64 hex pattern、vector IDはanchored `PV0-VAL-` pattern、source scenarioは1～36、enumは承認済み集合だけとする。`format` annotationだけへ安全性を依存せず、必要ならpattern/semantic検査を併用する。type coercionを禁止する。

## 12. cross-field validation方針

`required`、`properties`、`const`、`enum`、`allOf`、`oneOf`、`not`、`if`、`then`、`else`、`dependentRequired`、`dependentSchemas`、`additionalProperties`、`unevaluatedProperties`を候補とする。

- Trigger: MESSAGEはmessage必須、TIME_ADVANCEはmessage禁止、INTERNAL_EVENTはevent必須。TIME_ADVANCE/INTERNAL_EVENTでPROCESS禁止。
- CACHE_REPLAY: formal=`NONE`、defensive=`NONE`、source=`CACHED_RESULT`、sequence更新false、新operation禁止。
- NO_MESSAGE_ACTION: formal=`NONE`、defensive=`NONE`、liveness false、即時state/output/op変更禁止、ACTIVEならpost-timeout group必須。
- DEFENSIVE_ZERO: formal=`FORMAL_REJECT`、sequence更新false、operation=`invalid`、output=`zero`、latch解除禁止。
- Output apply failure: result=`FAILED`、formal=`FORMAL_ACCEPT`、defensive=`NONE`、safety action=`ZERO_ALL_OUTPUTS`、applied/state confirmed=false、operation=`invalid`、state=`FAULT_LATCHED`、fault reason必須。
- TIME_ADVANCE communication loss: event=`communication_lost`、formal=`NONE`、handling=`NOT_APPLICABLE`、command result required=false、state=`COMM_LOSS_LATCHED`。

5番目のvalidation outcomeを追加して解決しない。

## 13. schema外validationとの責任分離

validationを4層に分離する。

- Layer 0 — byte and loader validation: UTF-8、BOM、file size、LF/末尾改行、single root、duplicate key、parse error、depth/string/array limit。duplicate keyをJSON Schemaへ任せない。
- Layer 1 — JSON Schema validation: structure、required/forbidden、type、enum、pattern、range、unknown property、conditional、group presence。
- Layer 2 — semantic and cross-file validation: filename/内部ID一致、全file ID一意、38 IDとscenario coverage、source SHA実照合、CASE_CATALOG意味一致、sequence/temporal集合、cross-file hash、schema/catalog version対応。
- Layer 3 — simulator execution validation: transition、output、operation ID、liveness、watchdog、cache replay、immediate/post-timeout、fault/communication latch。

全LayerがPASSするまで安全試験PASSとしない。schemaだけではduplicate key、raw bytes、LF、filename、cross-file uniqueness/coverage、source実照合、simulator挙動、物理motor安全、interlock、physical ESTOP、network security、authentication/authorizationを保証しない。

## 14. Python・TypeScript validator互換性

双方でDraft 2020-12を検証し、同じpositive fixturesをaccept、negative fixturesをrejectしなければならない。libraryは未選定とし、custom keyword、implementation extension、`format` default差に依存しない。strict mode相当を要求し、remote resolutionを無効化する。schema compile errorやvalidator disagreementはFAILとし、多数決で解決せずschema/toolingを再レビューする。

## 15. security・resource・simulator gate

duplicate検査前にparse結果を信頼せず、Layer 0～2完了前やschema validation前にsimulator実行しない。unknown propertyを無視しない。external URL、remote fetch、code evaluation、custom executable formatを禁止する。file size、nesting depth、string/array length上限を必須とし、違反はvalidation failureとする。具体値は未確定である。real motor output enabled=falseを必須とし、schemaやsimulatorだけで実機・実田んぼ投入を承認しない。

## 16. 未確定事項と次の承認対象

exact root/group field名、schema title、`$defs`名、field別presence、integer range、string/array/file/depth limit、Python/TypeScript libraryとversion固定、schema/semantic error report、manifest schema、positive/negative conformance fixturesは未確定である。一方、JSON Schema採用、Draft 2020-12、`$schema` URI、`$id` URN、self-contained single schema、remote ref禁止、unknown property拒否、null禁止、4層validation、実motor未承認は未確定へ戻さない。

次工程候補は`software/rover_control/protocol/v0/test_vectors/FIELD_MODEL.md`である。11 groupの正式JSON property名、field名、type、enum、presence、none/not applicable、依存関係、CASE_CATALOG列対応をschema作成前に固定する。今回は作成しない。
