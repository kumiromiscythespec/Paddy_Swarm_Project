# Paddy Swarm Rover Control Protocol v0 Test Vector Schema Requirements

Status: Draft / Logical schema requirements only / Encoding not selected / No schema file yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書は、将来のmachine-readable test vector schemaが満たすべき論理要件を定義する。schema本体やwire protocol schemaではなく、JSON・YAMLのfield名やencodingを確定しない。`CASE_CATALOG.md`の意味を変更せず、実機モーター試験を承認しない。

## 2. 適用範囲と対象外

適用範囲は、test vectorのlogical group、値集合、型、presence、欠落表現、cross-field validation、安全制約、version・privacy要件である。JSON、YAML、JSON Schemaその他の実schema、sample・実vector、manifest、parser、validator、runner、PWA・ESP32・simulatorコード、encoding選定は対象外とする。

## 3. 参照文書と優先順位

- format document: `software/rover_control/protocol/v0/test_vectors/README.md`
- format document SHA256: `94200d499d8841845f1348bed222f58f9a0aa3d3900deb95afcd0246fd13fe02`
- case catalog: `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`
- case catalog SHA256: `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d`
- validation source: `software/rover_control/protocol/v0/VALIDATION_ORDER.md`
- validation source SHA256: `ed600175566a55ad7eea921d2471107ad5d7ee9d86168054ecb7f647e0608e4a`
- protocol version: `v0`
- source scenario count: 36
- concrete vector count: 38

優先順位は、物理安全設計、SAFETY_REQUIREMENTS、STATE_MACHINE、protocol README、protocol v0 README、VALIDATION_ORDER、test vector format README、CASE_CATALOG、本文書の順とする。上位文書のSHA256変更時は再レビューを必須とする。

## 4. schema設計原則

- fail-closedとし、未知値を推測受理しない。
- unknown field許可方針はschema versionごとに明示する。
- 安全上重要な項目を暗黙defaultで補完しない。
- 初期状態と期待状態、即時結果と時間経過後結果、formal dispositionとdefensive action、validationとoutput apply resultを分離する。
- `ABSENT`、`NONE`、`NOT_APPLICABLE`を同一視しない。
- booleanと文字列、数値と数値文字列、enumの大文字小文字を暗黙変換しない。
- schema validation成功だけで安全試験PASSとしない。

## 5. logical recordと11 group

| Group | Purpose | Base presence | May be conditional | Safety relevance |
| --- | --- | --- | --- | --- |
| identity | vector識別 | REQUIRED | No | High |
| source | 上位仕様trace | REQUIRED | No | High |
| profile_and_capability | profile・能力条件 | REQUIRED | Yes | High |
| initial_fixture | 初期状態 | REQUIRED | Yes | Critical |
| stimulus | trigger・入力 | REQUIRED | Yes | Critical |
| validation_expectation | validation結果 | REQUIRED | Yes | Critical |
| immediate_expectation | 即時結果 | REQUIRED | Yes | Critical |
| time_advance | 論理時間進行 | CONDITIONAL | Yes | High |
| post_time_expectation | 時間経過後結果 | CONDITIONAL | Yes | Critical |
| observability | result・snapshot観測 | CONDITIONAL | Yes | High |
| notes | 人間向け補足 | OPTIONAL | Yes | Low |

group名はこの11件だけをちょうど1回用い、12番目を追加しない。これらを実際のJSON object名としては確定しない。

## 6. presence・absence・noneの意味

presence分類は次の4件である。

- `REQUIRED`: 常に存在し、型と値が有効でなければならない。
- `CONDITIONAL`: 明示された他項目またはcase種別により必須または禁止となる。
- `OPTIONAL`: 省略可能だが、存在時は型と値を検証する。
- `FORBIDDEN`: 存在してはならず、存在時はvalidation失敗とする。

REQUIREDをnullで満たしたことにせず、FORBIDDENをnullで残す方式を原則認めない。CONDITIONAL条件を人間の推測に依存させない。

値の存在意味は`ABSENT`（項目不存在）、`NONE`（概念は適用されるが現在値なし）、`NOT_APPLICABLE`（概念自体が非適用）、`VALUE`（有効な具体値）の4件を区別する。missing fieldを自動的にNONEへ変換せず、安全上重要な欠落をNOT_APPLICABLEへ偽装しない。NONEのwire表現、空文字、null採否はencoding決定後まで未確定とする。

## 7. 共通値集合と型要件

- Official states (10): `BOOT_SAFE`, `DISARMED`, `ARMED_NEUTRAL`, `DRIVE_READY`, `DRIVE_ACTIVE`, `PTO_READY`, `PTO_ACTIVE`, `COMM_LOSS_LATCHED`, `FAULT_LATCHED`, `EMERGENCY_STOP_LATCHED`
- Trigger kind (3): `MESSAGE`, `TIME_ADVANCE`, `INTERNAL_EVENT`
- Formal disposition (3): `FORMAL_ACCEPT`, `FORMAL_REJECT`, `NONE`
- Defensive action (2): `DEFENSIVE_ZERO`, `NONE`
- Message handling (4): `PROCESS`, `NO_MESSAGE_ACTION`, `CACHE_REPLAY`, `NOT_APPLICABLE`
- Result source (3): `NEW_RESULT`, `CACHED_RESULT`, `NONE`
- Output apply result (3): `SUCCESS`, `FAILED`, `NOT_APPLICABLE`
- Output apply safety action (2): `ZERO_ALL_OUTPUTS`, `NONE`
- Operation ID expectation (4): `new`, `same`, `invalid`, `none`
- Catalog output expectation (3): `zero`, `forward`, `same`

これらはschema要件上の論理値集合で、encoding上の最終表現ではない。型を暗黙変換せず、集合外の値を拒否する。

## 8. identity・source要件

vector ID、title、protocol version、vector format version候補、source document path・SHA256・chapter・scenario number、profile、simulator fixture version候補を扱う。vector IDは必須かつ全vector集合内で一意、prefixは`PV0-VAL-`とし、message IDやoperation IDへ流用しない。source scenarioは1～36、SHA256は64桁hex候補、pathはrepository-relativeとし、絶対Windowsパスと`..`を禁止する。

## 9. profile・initial fixture要件

profile/fixtureは`one_side_test`と`drive_pto_split_fixture`だけを許可する。initial fixtureはofficial state、armed、drive/PTO output、安全ラッチ、boot/session fixture、controller owner、sender role、last seen sequence候補、last accepted COMMAND sequence、active operation ID、mode、capability、monotonic time、freshness reference、watchdog remaining、cached result候補、real motor output enabledを表現可能にする。

`real motor output enabled=false`を必須とする。one_side_testではTURN、PTO、right outputを利用不可とする。initial stateは正式10状態だけとし、ACTIVEなのに必要なoperation IDがないfixtureを正常扱いせず、latched状態で危険な出力を許可しない。fixtureは実機guard迂回を許可しない。

## 10. stimulus要件

trigger kind、stimulus message有無、logical message type候補、command type候補、candidate intent候補、direction、parseable、size valid、protocol version、boot/session ID、sender role、ownership、message ID、sequence、freshness reference、TTL、required fields present、payload validity、capability・state compatibility、guard result、output apply result、internal event候補を扱う。

candidate intentはmalformed STOP/EMERGENCY_STOP試験用fixture metadata候補であり、正式parse済みcommand typeとして扱わない。output apply resultはstimulus groupに属する。raw byte列は定義しない。

## 11. validation expectation要件

first failing validation step、step number・name、formal disposition、defensive action、message handling、result source、rejection reason、internal event、state machine event generated、last accepted sequence update、result cache update、control liveness updateを扱う。

`FORMAL_REJECT + DEFENSIVE_ZERO`を別項目で表現可能にする。NO_MESSAGE_ACTIONをFORMAL_REJECTへ、CACHE_REPLAYをFORMAL_ACCEPTへ変換せず、internal eventをmessage rejectionとして扱わない。failing stepなしはNONEまたはNOT_APPLICABLEを明示でき、reasonなしに架空reasonを生成しない。

## 12. immediate expectation要件

drive/PTO output、armed、active operation ID、official final state、安全ラッチ、last accepted sequence、command result required・status候補・source、rejection reason、state snapshot required候補、last stop reason、fault reason、immediate liveness update、output apply safety action、applied success、state confirmed successを扱う。

final stateは正式10状態だけとする。defensive actionをformal acceptanceとして記録せず、cached resultと現在状態を分離する。output apply failureをapplied成功にせず、`ZERO_ALL_OUTPUTS`をvalidation outcomeへ入れない。

## 13. time advance・post-timeout要件

time advance有無、monotonic advance amount候補、watchdog expiry、internal event、before/at-timeout assertion、post-timeout drive/PTO output、operation ID、armed、official state、formal acceptance、command result生成有無を扱う。

wall clockやreal sleepを必須とせず、harnessが決定論的に時間を進める。scenario 23、24、30、31は即時とpost-timeoutの両方を必須とする。scenario 4は`TIME_ADVANCE`を主triggerとし、watchdog後のeventは`communication_lost`、状態は`COMM_LOSS_LATCHED`とする。

## 14. observability・notes要件

observabilityはCOMMAND_RESULT、STATE_SNAPSHOT、telemetry、cache replay source、rejection・fault・stop reasonの観測期待を表現可能にする。安全処理の成否とログ・送信成否を分離する。notesは補足専用で、必須期待値やcross-field ruleをnotesだけに記載してはならない。秘密情報、個人情報、正確な農地座標を含めない。

## 15. cross-field validation

### Trigger

- `MESSAGE`はstimulus messageをREQUIREDとする。
- `TIME_ADVANCE`はstimulus messageをFORBIDDENとする。
- `INTERNAL_EVENT`はinternal eventをREQUIREDとする。
- `TIME_ADVANCE`または`INTERNAL_EVENT`でmessage handling=`PROCESS`を禁止する。

### Formal disposition

- FORMAL_ACCEPTとFORMAL_REJECTを同時にしない。
- `CACHE_REPLAY`、`NO_MESSAGE_ACTION`、`NOT_APPLICABLE`ではformal disposition=`NONE`とする。

### Defensive action

- `DEFENSIVE_ZERO`はformal disposition=`FORMAL_REJECT`、accepted sequence update=false、operation ID=`invalid`とし、安全ラッチを解除しない。

### Cache replay

- `CACHE_REPLAY`はresult source=`CACHED_RESULT`、accepted sequence update=false、新規operation IDなし、state transition/output再適用なしとする。

### NO_MESSAGE_ACTION

- defensive action=`NONE`、immediate liveness update=falseとし、message由来で即時state/output/operationを変更しない。ACTIVE caseでpost-timeoutが必要なら独立watchdogを明記する。

### Output apply failure

- output apply result=`FAILED`、formal disposition=`FORMAL_ACCEPT`、defensive action=`NONE`、safety action=`ZERO_ALL_OUTPUTS`、applied=false、state confirmed=false、operation ID=`invalid`、final state=`FAULT_LATCHED`、fault reason REQUIREDとする。

### TIME_ADVANCE communication loss

- trigger=`TIME_ADVANCE`、internal event=`communication_lost`、formal disposition=`NONE`、message handling=`NOT_APPLICABLE`、final state=`COMM_LOSS_LATCHED`、command result required=falseとする。

## 16. 特殊case要件

- Exact duplicate: `PV0-VAL-009`, `PV0-VAL-019`, `PV0-VAL-026`
- Defensive STOP: `PV0-VAL-020`, `PV0-VAL-021`, `PV0-VAL-022`
- NO_MESSAGE_ACTION + watchdog: `PV0-VAL-023`, `PV0-VAL-024`, `PV0-VAL-030`, `PV0-VAL-031`
- Defensive EMERGENCY_STOP: `PV0-VAL-027`, `PV0-VAL-028`, `PV0-VAL-029`
- Output apply failure: `PV0-VAL-032`
- Internal/time event: `PV0-VAL-004`, `PV0-VAL-005`, `PV0-VAL-036`

schemaは各群についてCASE_CATALOGの意味を欠落なく表現可能でなければならない。特にscenario 4と32を第15章の一意な組合せで表現する。

## 17. version・security・privacy

schema versionと上位文書SHA256のtraceを要求し、version変更時のunknown field policyを明示する。正確な農地座標、Wi-Fiパスワード、token、秘密鍵、認証秘密、実在人物の個人情報を禁止する。source pathはrepository-relativeとし、fixture IDを認証tokenとして扱わない。boot/session/operation IDを秘密情報または認証として扱わない。real motor outputを常に無効化し、schema validationでsecurity成立を保証したことにしない。

## 18. 未確定事項と次の承認対象

encoding、JSON/YAML選択、schema language、exact field名、null使用可否、unknown field policy、integer範囲、ID長、SHA256文字列の大小文字、time単位、output数値表現、sequence・operation ID型、1ファイル当たりvector数、manifest形式、schema version表現、validation error report形式は未確定である。未確定を理由に第15章の安全規則を弱めない。

次の承認対象候補は`software/rover_control/protocol/v0/test_vectors/ENCODING_DECISION.md`である。JSON・YAML等を、simulator fixture安全性、parser実装容易性、diff可読性、厳密型検証、コメント可否、duplicate key処理、number表現で比較し、最終encodingを1つ選ぶ。今回は作成しない。
