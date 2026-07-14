# Paddy Swarm Rover Control Protocol v0 Test Vector Format

Status: Draft / Format definition only / Simulator-first / No vector files yet / Real motor output not approved

## 1. 文書の目的と状態

本文書は、`VALIDATION_ORDER.md`のdocument scenarioを決定論的caseへ変換するためのtest vector論理形式を定義する。実際のvectorファイルはまだ作成せず、encodingも決定しない。simulator-firstであり、実モーター出力は未承認である。本文書はprotocol実装開始または実機試験を承認する文書ではない。

本文書の項目名はtest vector文書上の論理ラベルであり、protocolのwire field名ではない。

## 2. 適用範囲と対象外

適用範囲は、初期状態、session・boot・controller fixture、入力message、validation failure位置、validation outcome、formal acceptance、defensive action、出力、active operation ID、最終状態、liveness、accepted sequence、command result、state snapshot、時間進行、watchdog後の状態、およびsource scenarioとの対応である。

wire encoding、protocol fieldの実型、transport、実機モーター試験、認証・暗号実装、performance benchmark、fuzzing実装、hardware-in-the-loop試験は対象外とする。

## 3. 上位文書とトレーサビリティ

参照文書は、`software/rover_control/README.md`、`SAFETY_REQUIREMENTS.md`、`STATE_MACHINE.md`、`protocol/README.md`、`protocol/v0/README.md`、`VALIDATION_ORDER.md`、`docs/safety.md`である。優先順位は、物理安全設計、SAFETY_REQUIREMENTS、STATE_MACHINE、protocol境界README、protocol v0 README、VALIDATION_ORDER、本文書の順とし、本文書は上位文書の意味を変更しない。

各vectorは、source document、source document SHA256、source chapter、source scenario number、protocol version、vector format version候補、vector ID、case titleを参照する。scenario番号だけから意味を推測せず、source SHA256が異なる場合は再レビューする。vector変更で上位仕様の矛盾を隠さず、上位文書変更時に影響vectorを追跡可能にする。

## 4. scenarioとtest vectorの違い

Document scenarioは人間向けの仕様例で、条件分岐や複数commandを1行に含み得る。Concrete test vectorはprofile、command type、初期状態、入力message、即時期待結果を各1つに固定し、必要な場合だけ時間進行後の期待結果を1つ持つ。条件分岐を含めず、「候補」や「維持」だけで結果を曖昧にしない。1つのdocument scenarioを複数vectorへ展開できる。

## 5. 将来のディレクトリ契約

将来候補の論理構成は次のとおりである。

```text
test_vectors/
  README.md
  CASE_CATALOG.md
  vectors/
    <vector-id>.<encoding-to-be-decided>
  manifest.<encoding-to-be-decided>
```

今回はREADME以外を作成しない。encodingと拡張子、1ファイル1vectorか複数vectorか、vector本体とmanifestの重複情報方針は未確定である。case IDはencodingから独立させる。

## 6. vector ID規則

prefixは`PV0-VAL-`、基本形式は`PV0-VAL-<source-scenario-number>`とし、scenario番号を3桁ゼロ埋めする（例: `PV0-VAL-002`、`PV0-VAL-023`）。分割caseはsuffixを付ける（例: `PV0-VAL-001A`、`PV0-VAL-001B`、`PV0-VAL-014L`、`PV0-VAL-014R`）。

IDは一意とし、承認済みIDまたは削除caseのIDを別の意味へ再利用しない。suffixの意味をcatalogへ記録する。vector IDはsequence、message ID、operation IDとは別で、wire dataへ送信する必要はない。

## 7. test vector論理レコード

各vectorは最低限、次の11 logical groupで構成する。

```text
identity
source
profile_and_capability
initial_fixture
stimulus
validation_expectation
immediate_expectation
time_advance
post_time_expectation
observability
notes
```

これらは論理groupであり、JSON object名として確定したものではない。各groupの省略可否は将来schemaで固定する。

`trigger kind`は`stimulus`へ含める。formal disposition、defensive action、message handling、result sourceは`validation_expectation`へ含める。output apply resultは`stimulus`、output apply safety actionは`immediate_expectation`に属する互いに別の論理項目候補とする。説明上は`stimulus.output_apply_result`と`immediate_expectation.output_apply_safety_action`を用いるが、実際のfield名としては確定しない。

## 8. source metadata

最低限の論理項目は、vector ID、title、source document path、source document SHA256、source chapter、source scenario number、protocol version、vector format version候補、simulator fixture version候補、profile、capability setである。個人情報、正確な農地座標、Wi-Fiパスワード、token、secret、実田んぼを特定する情報を含めない。

## 9. initial fixture

initial fixtureは、official state、armed、drive output、PTO output、安全ラッチ状態、rover boot ID fixture、session ID fixture、controller owner、sender role、last seen sequence候補、last accepted sequence、active operation IDまたはnone、selected mode、profile、capability、monotonic test time、freshness reference、watchdog remaining time、cached command result候補を表現可能にする。

official stateは、`BOOT_SAFE`、`DISARMED`、`ARMED_NEUTRAL`、`DRIVE_READY`、`DRIVE_ACTIVE`、`PTO_READY`、`PTO_ACTIVE`、`COMM_LOSS_LATCHED`、`FAULT_LATCHED`、`EMERGENCY_STOP_LATCHED`の10件だけとする。fixtureによる直接状態設定はsimulator test setupであり、実機の安全guardを迂回してよいことを意味しない。

## 10. stimulus message

stimulusは、trigger kind、logical message type、command typeまたはnone、direction、parseable、size valid、protocol version、rover boot ID、session ID、sender role、controller ownership、message ID、sequence、freshness reference、TTL、required fields present、payload validity、capability compatibility、state compatibility、guard result、output apply result候補を表現可能にする。

trigger kindの候補値は`MESSAGE`、`TIME_ADVANCE`、`INTERNAL_EVENT`である。`MESSAGE`はControllerまたはClientから論理messageを入力する。`TIME_ADVANCE`は新しいmessageなしにmonotonic test timeを進める。`INTERNAL_EVENT`はRover内部のwatchdog、fault、boot処理等をsimulator fixtureで発生させる。これらはwire message typeではなくtest harnessのcase開始方法を表す論理ラベルであり、`TIME_ADVANCE`と`INTERNAL_EVENT`ではstimulus messageがnoneであり得る。

message typeは承認済み12件、command typeは承認済み16件またはnoneから選択する。raw byte列や完成したJSONは今回定義しない。

## 11. validation expectation

最低限、trigger kind、first failing validation stepまたはnone、validation step numberまたはnot applicable、validation step nameまたはnot applicable、formal disposition、defensive action、message handling、result source、rejection reasonまたはnone、internal eventまたはnone、state machine event生成有無、last accepted sequence更新有無、result cache更新有無、control liveness更新有無を表現する。

各次元の論理値候補は次のとおりである。

- formal disposition: `FORMAL_ACCEPT`、`FORMAL_REJECT`、`NONE`
- defensive action: `DEFENSIVE_ZERO`、`NONE`
- message handling: `PROCESS`、`NO_MESSAGE_ACTION`、`CACHE_REPLAY`、`NOT_APPLICABLE`
- result source: `NEW_RESULT`、`CACHED_RESULT`、`NONE`

これらはtest vector上の論理ラベルであり、wire field名や最終schema enumではない。`VALIDATION_ORDER.md`の`FORMAL_ACCEPT`と`FORMAL_REJECT`はformal disposition、`DEFENSIVE_ZERO`はdefensive action、`NO_MESSAGE_ACTION`はmessage handlingであり、4概念を1つの相互排他的enumとして扱わない。`FORMAL_REJECT`と`DEFENSIVE_ZERO`は同時に表現できる。5番目の複合outcomeを作らず、defensive actionをformal acceptanceとせず、`NO_MESSAGE_ACTION`をformal rejectionとして偽装しない。

output apply safety actionはvalidation outcomeでもdefensive actionでもなく、値候補を`ZERO_ALL_OUTPUTS`と`NONE`の2件だけとする。`ZERO_ALL_OUTPUTS`をformal dispositionまたはdefensive actionへ入れない。`DEFENSIVE_ZERO`は正式受理できないSTOP/EMERGENCY_STOPの認識可能な停止意図に対するdefensive action、`ZERO_ALL_OUTPUTS`は正式受理後のoutput apply failureに対する安全処理であり、同義語として扱わず同じ項目へ入れない。

通常の有効commandは`MESSAGE / FORMAL_ACCEPT / NONE / PROCESS / NEW_RESULT`、通常の拒否commandは`MESSAGE / FORMAL_REJECT / NONE / PROCESS / NEW_RESULT`、defensive停止は`MESSAGE / FORMAL_REJECT / DEFENSIVE_ZERO / PROCESS / NEW_RESULT`とする。defensive停止はaccepted sequenceを更新せず、acceptedまたはappliedとして報告せず、requested formal transitionを適用しない。

## 12. immediate expected result

message処理直後について、formal disposition、defensive action、message handling、result source、output apply result、output apply safety action、command result sourceがnewかcachedか、current occurrenceが新規acceptedか、drive output、PTO output、armed、active operation ID、official final state、安全ラッチ、last accepted sequence、command result生成候補、command result status、rejection reason、state snapshot更新候補、last stop reason候補、fault reason候補、immediate liveness更新を表現する。cached resultの元command状態と現在のofficial stateを分離する。

official final stateは正式10状態から選ぶ。operation IDのnew、same、invalid、none等は意味を明確化する。acceptedと物理動作成功を同一視せず、output apply failureを成功扱いせず、defensive actionをformal acceptanceとして記録しない。

exact duplicateではcached command resultの再通知を候補とするが、現在のstate transitionとoutputを再適用しない。current official stateはinitial fixtureから必要な安全処理を除き変化せず、current occurrenceを新規acceptedとしない。

scenario 32は、trigger kind=`MESSAGE`、formal disposition=`FORMAL_ACCEPT`、defensive action=`NONE`、message handling=`PROCESS`、result source=`NEW_RESULT`、output apply result=`FAILED`、output apply safety action=`ZERO_ALL_OUTPUTS`を同時に表現する。`ZERO_ALL_OUTPUTS`はStep 20の出力適用失敗後にdrive/PTO outputをzero、active operation IDをinvalidとし、fault reasonを保持して`FAULT_LATCHED`へ遷移させるが、物理適用成功を意味しない。結果はcontrol liveness update=false、applied success=false、state_confirmed success=falseとする。scenario 32で`DEFENSIVE_ZERO`を使用せず、formal acceptance済みであるため`FORMAL_REJECT`へ書き換えず、apply failureを成功または安全PASSとしない。

## 13. time advanceとpost-timeout result

test harnessが制御するmonotonic test timeを用い、advance amount候補、freshness age、TTL expiry、watchdog expiry、result cache expiry候補、before-timeout assertion、at-timeout assertion、after-timeout assertionを表現する。

実時間sleepを必須とせず、harnessが決定論的に時計を進める。invalid messageでwatchdogを延長せず、wall clock変更で結果を変えない。watchdogの最終実時間値は未確定で、vectorは相対時間または設定値参照を使用可能にする。

`TIME_ADVANCE`または`INTERNAL_EVENT`をtrigger kindとし、stimulus message=noneのcaseを扱える。scenario 4は`TIME_ADVANCE`でwatchdog expiryを決定論的に発生させ、stimulus message=none、formal disposition=`NONE`、defensive action=`NONE`、message handling=`NOT_APPLICABLE`、result source=`NONE`、internal event=`communication_lost`、state machine event generated=trueとする。watchdog timeoutはtrigger原因の説明であり、状態機械へ渡す正式eventは`communication_lost`だけである。期待結果はdrive/PTO output=zero、operation ID=invalid、armed=false、`COMM_LOSS_LATCHED`、liveness更新なしである。scenario 4を`NO_MESSAGE_ACTION`やmessage rejectionにせず、`COMMAND_RESULT`を必須としないが、`STATE_SNAPSHOT`またはtelemetry更新候補を要求する。

## 14. NO_MESSAGE_ACTIONの二段階検証

`NO_MESSAGE_ACTION`はmessageが存在するが、そのmessageを理由としたactionを行わないcaseであり、messageなしのwatchdog timeoutおよび`CACHE_REPLAY`とは別である。Immediate phaseでは、message由来の状態変更、出力変更、active operation ID変更、formal acceptance、defensive action、liveness更新をすべて行わない。

Post-timeout phaseでは、初期状態が`DRIVE_ACTIVE`で独立watchdogが期限切れになった場合、全出力をzero、active operation IDをinvalid、armed=false、状態を`COMM_LOSS_LATCHED`とする。ただしmessageが正式受理されたことにはしない。

scenario 23、24、30、31はこの二段階形式を必須とし、即時結果とwatchdog後結果を1つの状態へ混同しない。

## 15. duplicateとresult cache

exact duplicate、sequence collision、stale sequence、result cache hit、result cache miss候補を扱う。exact duplicateの現在受信分は、trigger kind=`MESSAGE`、formal disposition=`NONE`、defensive action=`NONE`、message handling=`CACHE_REPLAY`、result source=`CACHED_RESULT`、new formal acceptance=false、last accepted sequence update=false、state transition reapply=false、output reapply=false、new operation ID=falseとする。

cached resultが元commandのaccepted結果を含んでも、duplicate受信分を新しく`FORMAL_ACCEPT`したことにはしない。cache replayと`NO_MESSAGE_ACTION`を同一視しない。exact duplicate判定はsequenceだけでなくmessage IDと内容一致を必要とする候補とし、cache miss時の最終方針は未確定である。original command result、cached result replay、current state snapshotを分離し、result cacheから返す内容と現在の`STATE_SNAPSHOT`を混同しない。scenario 9、19、26をresult cache関連caseとして追跡する。cache保持期間と実装方式は未確定である。

## 16. STOP・EMERGENCY_STOPのdefensive action

defensive caseは、formal outcome=`FORMAL_REJECT`、defensive action=`DEFENSIVE_ZERO`、accepted sequence更新なし、output=zero、active operation ID=invalid、requested formal transition適用なしを独立項目で表現する。`DRIVE_ACTIVE`は`DRIVE_READY`へ、`PTO_ACTIVE`は`PTO_READY`へ移し、latched状態は維持する。defensive EMERGENCY_STOPで正式ESTOP latchを作らず、安全ラッチを解除しない。正式STOP、正式EMERGENCY_STOP、defensive STOP、defensive EMERGENCY_STOPを同じ期待値へまとめない。

## 17. profile・capability・case展開

1 vectorにつきprofileとcommandを1つに固定する。Source scenario 1は次の2件へ展開する。

- `PV0-VAL-001A`: profile=`one_side_test`、expected final state=`DRIVE_READY`
- `PV0-VAL-001B`: profile=将来のDRIVE/PTO分離profile用fixture、expected final state=`ARMED_NEUTRAL`

後者のprofile名はtest fixture上の識別名であり、正式protocol profile名ではない。Source scenario 14は次の2件へ展開する。

- `PV0-VAL-014L`: command=`TURN_LEFT`、expected final state=`DRIVE_READY`
- `PV0-VAL-014R`: command=`TURN_RIGHT`、expected final state=`DRIVE_READY`

その他は原則1 source scenarioにつき1 vectorとする。source scenario countは36、minimum concrete vector countは38である。

## 18. 必須vector catalog

この表は将来必要なcaseの識別だけを行い、vectorデータやexpected field値を定義しない。

| Vector ID | Source scenario | Expansion reason |
| --- | ---: | --- |
| PV0-VAL-001A | 1 | one_side_test profile |
| PV0-VAL-001B | 1 | future split profile fixture |
| PV0-VAL-002 | 2 | none |
| PV0-VAL-003 | 3 | none |
| PV0-VAL-004 | 4 | none |
| PV0-VAL-005 | 5 | none |
| PV0-VAL-006 | 6 | none |
| PV0-VAL-007 | 7 | none |
| PV0-VAL-008 | 8 | none |
| PV0-VAL-009 | 9 | none |
| PV0-VAL-010 | 10 | none |
| PV0-VAL-011 | 11 | none |
| PV0-VAL-012 | 12 | none |
| PV0-VAL-013 | 13 | none |
| PV0-VAL-014L | 14 | TURN_LEFT |
| PV0-VAL-014R | 14 | TURN_RIGHT |
| PV0-VAL-015 | 15 | none |
| PV0-VAL-016 | 16 | none |
| PV0-VAL-017 | 17 | none |
| PV0-VAL-018 | 18 | none |
| PV0-VAL-019 | 19 | none |
| PV0-VAL-020 | 20 | none |
| PV0-VAL-021 | 21 | none |
| PV0-VAL-022 | 22 | none |
| PV0-VAL-023 | 23 | none |
| PV0-VAL-024 | 24 | none |
| PV0-VAL-025 | 25 | none |
| PV0-VAL-026 | 26 | none |
| PV0-VAL-027 | 27 | none |
| PV0-VAL-028 | 28 | none |
| PV0-VAL-029 | 29 | none |
| PV0-VAL-030 | 30 | none |
| PV0-VAL-031 | 31 | none |
| PV0-VAL-032 | 32 | none |
| PV0-VAL-033 | 33 | none |
| PV0-VAL-034 | 34 | none |
| PV0-VAL-035 | 35 | none |
| PV0-VAL-036 | 36 | none |

## 19. PASS・FAIL判定と安全制約

1 vectorは、trigger kind、expected validation step、formal disposition、defensive action、message handling、result source、output apply safety action、immediate output、operation ID結果、immediate official state、liveness更新、accepted sequence更新、command result候補、snapshot候補、および時間進行がある場合のpost-timeout結果がすべて一致し、unexpected state transition、output開始、安全ラッチ解除がない場合にだけPASS候補となる。cache replayを新規acceptanceとせず、internal eventをmessage rejectionとせず、output apply safety actionをvalidation outcomeとせず、output apply failureをapplied成功としないこともPASS条件とする。特にscenario 32はdefensive action=`NONE`かつoutput apply safety action=`ZERO_ALL_OUTPUTS`、scenario 4はinternal event=`communication_lost`でなければFAILとする。

安全上の期待値が1項目でも異なればFAILとする。未指定値を推測してPASSにせず、simulator内部例外を安全PASSとして扱わない。ログ失敗と安全動作結果を分離する。real motor outputを常に無効にしたfixtureで実行し、vector PASSだけで実機試験を承認しない。

## 20. 未確定事項と次の承認対象

encoding、file extension、schema language、1ファイル当たりのvector数、manifest形式、exact field名、ID値の実型、time value単位、output表現、operation ID表現、cached result表現、rejection detail表現、simulator fixture読込方式、test runner、result report形式は未確定である。

次の承認対象は`software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`である。38 concrete vectorの初期状態、stimulus、即時期待結果、時間進行後結果を人間可読表で固定することを目的とする。今回は`CASE_CATALOG.md`、JSON、schema、自動テストを作成しない。
