# Paddy Swarm Rover Control Protocol v0 Validation Order

Status: Draft / Simulator-first / Real motor output not approved

## 1. 文書の目的と適用範囲

本文書は、ControllerからRoverへ届くmessageを、どの順番で検証し、失敗時に何をしてはならないかを定義する規範文書である。主対象は`COMMAND`と`CONTROL_UPDATE`であり、`SESSION_HELLO`と`SESSION_END`のvalidation境界も扱う。RoverからClientへ送るmessageの生成処理は主対象外とする。

本文書はencodingおよびプログラミング言語に依存しない。開発方針はsimulator-firstであり、実モーター出力は未承認である。物理非常停止は本文書およびprotocol validationから独立して機能しなければならない。

## 2. 上位安全原則

優先順位は、(1) 物理安全設計、(2) `SAFETY_REQUIREMENTS.md`、(3) `STATE_MACHINE.md`、(4) `protocol/README.md`、(5) `protocol/v0/README.md`、(6) 本文書の順とする。矛盾時は上位文書を優先する。

- 出力は、すべての必要なvalidationが成立した後にだけ適用する。
- 未知、不正または矛盾がある場合はfail-closedとする。
- 無効messageによって動作を開始または継続せず、ARMせず、安全ラッチを解除しない。
- 無効な`CONTROL_UPDATE`によってcontrol livenessを延長しない。
- transport ACKをcommand acceptanceとして扱わない。
- ログ処理より出力停止を優先する。
- reconnectによって状態、ARMまたはoperationを復元しない。
- 物理非常停止をprotocol validationへ依存させない。

## 3. validation結果の概念

以下はwire上の正式status名ではなく、validation方針を説明する概念名である。

- `FORMAL_ACCEPT`: messageが必要なvalidationをすべて通過し、state machineへ正式eventを渡せる。acceptedまたはappliedの`COMMAND_RESULT`候補を生成でき、必要な場合だけlast accepted sequenceを更新する。
- `FORMAL_REJECT`: messageを正式commandとして受理せず、requested state transitionを適用しない。rejection reasonを記録し、acceptedまたはappliedとして報告しない。
- `DEFENSIVE_ZERO`: messageは正式には拒否するが、認識可能な停止意図に対して走行/PTO出力を安全側のゼロへし、active operation IDを無効化する。requested commandを正式受理せず、そのcommandが要求した正式遷移を適用しない。ただし、ACTIVE状態をoperation IDなしで維持せず、`DRIVE_ACTIVE`では非ラッチ安全停止として`DRIVE_READY`へ、`PTO_ACTIVE`では非ラッチ安全停止として`PTO_READY`へ移行する。`DRIVE_READY`、`PTO_READY`、`ARMED_NEUTRAL`、`DISARMED`では現在状態を維持し、既存のlatched状態ではそのlatched状態を維持する。defensive actionだけで`EMERGENCY_STOP_LATCHED`へ正式遷移せず、安全ラッチを解除せず、last accepted sequenceを更新せず、acceptedまたはappliedとして報告しない。これらはrequested commandの正式遷移ではなく、出力ゼロ後に状態不変条件を守るためのローカル安全遷移である。
- `NO_MESSAGE_ACTION`: messageの意味または対象を安全に特定できないため、そのmessageを理由とした状態変更を行わず、control livenessも延長しない。既存watchdog、物理非常停止および内部fault処理は独立して継続する。

## 4. 23段階validation一覧

| Step | Validation |
| ---: | --- |
| 1 | transportから受信 |
| 2 | message size上限候補 |
| 3 | parse可能性 |
| 4 | protocol version |
| 5 | message type |
| 6 | direction |
| 7 | rover boot ID |
| 8 | session ID |
| 9 | sender role |
| 10 | controller ownership |
| 11 | sequence / duplicate / stale |
| 12 | freshness reference |
| 13 | TTL / expiry |
| 14 | 必須項目 |
| 15 | payload範囲 |
| 16 | capability |
| 17 | current state |
| 18 | safety guard |
| 19 | state transition決定 |
| 20 | 出力適用 |
| 21 | COMMAND_RESULT生成 |
| 22 | STATE_SNAPSHOTまたはtelemetry更新 |
| 23 | ログ候補 |

この順序を変更せず、stepを追加または削除しない。通常の出力開始はStep 20より前に行わない。Step 19で遷移が成立しなければStep 20へ進まない。Step 21～23の失敗によって安全出力停止を遅らせない。`DEFENSIVE_ZERO`は通常フローから分岐する安全側の例外であり、通常の出力適用ではない。

## 5. validation段階のグループ

- A. 受信・構文識別: Step 1～3
- B. protocol・対象識別: Step 4～7
- C. session・権限・replay・freshness: Step 8～13
- D. 内容・capability・状態・guard: Step 14～18
- E. 遷移・出力・結果・記録: Step 19～23

各グループで失敗したmessageは、そのグループ以後の危険な処理へ進めない。安全側の例外は第7～9章の条件を満たす`DEFENSIVE_ZERO`だけとする。

## 6. 共通の失敗処理

Step 1～7で失敗した場合は、信頼できる範囲に応じて`FORMAL_REJECT`または`NO_MESSAGE_ACTION`とする。message typeや対象Roverを信頼できない場合はmessage由来の状態変更をせず、livenessを延長しない。watchdogは独立して動作する。unsupported versionを推測解釈せず、wrong boot IDを現在bootのcommandとして扱わず、parse不能messageから停止意図を推測しない。

Step 8～18で通常commandが失敗した場合は`FORMAL_REJECT`とし、遷移を適用せず、出力を開始または継続せず、livenessを延長せず、rejection reasonを記録する。認識可能なSTOPまたはEMERGENCY_STOPだけは、第8章または第9章の条件を満たす場合に限り`DEFENSIVE_ZERO`候補となる。

Step 19で失敗した場合は`FORMAL_REJECT`とし、Step 20へ進まず、出力を開始せず、active operation IDを新規発行しない。Step 20で出力適用に失敗した場合は、全出力ゼロを優先し、active operation IDを無効化して`FAULT_LATCHED`候補とする。正式受理済みでも動作成功とは報告せず、fault情報を結果、snapshotおよびログ候補へ反映する。

## 7. 正式受理とdefensive actionの分離

| Item | Formal acceptance | Defensive action |
| --- | --- | --- |
| Command result | accepted/applied候補 | rejected |
| Last accepted sequence | 更新候補 | 更新しない |
| Requested state transition | 適用可能 | 適用しない |
| Output | command意味に従う | ゼロ方向だけ |
| Active operation ID | 開始時は新規候補 | 無効化だけ |
| Safety latch clear | guard成立時のみ | 禁止 |
| Logging | accepted | rejected＋defensive action |
| Post-zero state | 正式commandと状態機械に従う | DRIVE_ACTIVE→DRIVE_READY、PTO_ACTIVE→PTO_READY、latched状態は維持 |

`DEFENSIVE_ZERO`は、認証、session、ownershipその他の検証を迂回した正式command受理ではない。停止意図に基づく局所的な安全側処理と、requested state transitionの正式適用を明確に分離する。

## 8. STOPのvalidation方針

正式STOPはすべての必要なvalidationを通過した`FORMAL_ACCEPT`であり、冪等である。走行/PTO出力をゼロにし、active operation IDを無効化し、`DRIVE_ACTIVE`から`DRIVE_READY`へ、`PTO_ACTIVE`から`PTO_READY`へ遷移する。READYまたはDISARMEDでは出力ゼロを再確認する。latched状態を解除せず、accepted/applied result候補を生成する。

STOPのidentification gateは、次のすべてを要求する。

- Step 2のsize上限内である。
- Step 3で最低限parse可能である。
- Step 4で対応protocol versionである。
- Step 5で`COMMAND`と識別できる。
- Step 6でController → Rover方向である。
- Step 7で現在のrover boot IDと一致する。
- payloadからcommand typeを`STOP`と一意に識別できる。

gateを満たさないStep 2～7の失敗は`NO_MESSAGE_ACTION`とする。ただしwatchdogと物理非常停止は独立して動作する。gate通過後にStep 8～18で失敗した場合は`FORMAL_REJECT + DEFENSIVE_ZERO`候補とし、全出力をゼロ、active operation IDを無効にする。`DRIVE_ACTIVE`は`DRIVE_READY`へ、`PTO_ACTIVE`は`PTO_READY`へ非ラッチ安全遷移し、latched状態ではラッチを維持する。last accepted sequenceを更新せず、STOP acceptedとして記録せず、rejection reasonを保持する。

## 9. EMERGENCY_STOPのvalidation方針

正式EMERGENCY_STOPはすべての必要なvalidationを通過した`FORMAL_ACCEPT`であり、冪等である。全走行/PTO出力をゼロ、active operation IDを無効、armed=falseとし、`EMERGENCY_STOP_LATCHED`へ遷移する。reconnectや重複受信で解除せず、解除には別commandと全guardを要求し、解除後も再ARMを要求する。

EMERGENCY_STOPのidentification gateは、Step 2のsize上限内、Step 3で最低限parse可能、Step 4で対応protocol version、Step 5で`COMMAND`、Step 6でController → Rover方向、Step 7で現在のrover boot IDと一致し、payloadから`EMERGENCY_STOP`を一意に識別できることをすべて要求する。

gateを満たさないStep 2～7の失敗は`NO_MESSAGE_ACTION`とする。gate通過後にStep 8～18で失敗した場合は`FORMAL_REJECT + DEFENSIVE_ZERO`候補とし、出力をゼロ、active operation IDを無効化する。停止後は`DRIVE_ACTIVE`を`DRIVE_READY`へ、`PTO_ACTIVE`を`PTO_READY`へ非ラッチ安全遷移させる。`DRIVE_READY`、`PTO_READY`、`ARMED_NEUTRAL`、`DISARMED`では現在状態を維持し、`COMM_LOSS_LATCHED`、`FAULT_LATCHED`、`EMERGENCY_STOP_LATCHED`では現在のラッチ状態を維持する。defensive actionだけでは、`EMERGENCY_STOP_LATCHED`への正式遷移、accepted sequence更新、command acceptance記録、安全ラッチ解除、controller権限取得、session復旧またはARM状態変更による再始動を行わない。正式ラッチは正式受理command、物理非常停止または内部安全処理だけが成立させる。

## 10. sequenceとduplicate処理

- exact duplicate: 同一session、同一sequence、同一message IDかつ同一内容の処理済みmessageは、遷移や出力を再適用しない。以前の結果を再通知する方式は候補とし、accepted commandでも再始動しない。STOP/EMERGENCY_STOPはゼロまたはラッチ状態を維持する。
- sequence collision: 同一sequenceでmessage IDまたは内容が異なる場合は`FORMAL_REJECT`とし、replayまたは矛盾として記録する。通常commandは適用せず、STOP/EMERGENCY_STOPはidentification gate成立時だけ`DEFENSIVE_ZERO`候補とする。
- stale sequence: 処理済み範囲より古い場合は`FORMAL_REJECT`、遷移なし、liveness更新なしとする。STOP/EMERGENCY_STOPだけdefensive規則を適用できる。
- sequence gap: 欠落commandを推測せず、command繰返しとして扱わず、過去commandを再実行しない。より新しいsequenceの受理方針はsession内の安全規則と将来のtest vectorで固定する。

logical trackingでは、last seen command sequence候補、last accepted command sequence、command ID/result cache候補を区別する。具体的な保存方式は未確定である。

## 11. freshnessとexpiry処理

freshnessをwall clockだけで判定せず、boot/sessionに属するfreshness reference候補とRover側の単調時間によるageを用いる。TTL上限はRover側で制限する。expired commandを正式受理せず、expired `CONTROL_UPDATE`でlivenessを延長しない。delayed MOVEで始動せず、delayed ARMでARMせず、delayed resetでラッチを解除しない。

expired STOP/EMERGENCY_STOPはidentification gate成立時に`FORMAL_REJECT + DEFENSIVE_ZERO`候補となるが、acceptedとして記録しない。expired EMERGENCY_STOPだけでは正式な非常停止ラッチを作らない。

## 12. CONTROL_UPDATEとデッドマン

有効な`CONTROL_UPDATE`は、current rover boot ID、current session、current control owner、新しい有効sequence、有効freshness、TTL内、current active operation IDとの一致、current directionまたはoperation referenceとの無矛盾、current stateが`DRIVE_ACTIVE`または将来許可された`PTO_ACTIVE`であること、および有効なdeadman情報をすべて要求する。

`deadman asserted=true`は既存operationのliveness更新候補に限り、新規operationを開始せず、directionやmodeを変更しない。validation成立済みの`deadman asserted=false`は内部event `deadman_released`の生成候補となり、出力をゼロ、active operation IDを無効にし、`DRIVE_ACTIVE`から`DRIVE_READY`へ遷移する。PTO方式は未確定である。

invalidまたはexpired `CONTROL_UPDATE`は、livenessを延長せず、新規動作を開始せず、古いoperationを復元せず、そのmessageだけを根拠にdirectionやmodeを変更しない。watchdogは独立して停止を成立させる。

## 13. session・boot・controller ownership

wrong boot IDを現在bootのcommandとして扱わず、old sessionを再利用しない。observerおよびcontrol owner以外からの通常commandを拒否する。controller切替でARMやoperationを引き継がず、controller喪失時は通信断安全処理を行う。reconnect後は新session候補とする。session IDとboot IDは認証ではなく、security方式未確定中は実モーター出力を解放しない。

非owner STOP/EMERGENCY_STOPのdefensive actionは、第8章または第9章のidentification gateを満たす場合だけ候補となる。

## 14. payload・capability・state guard

必須項目欠落、数値範囲外、NaN、無限大、型不一致候補を拒否する。capabilityがないcommandを拒否し、`one_side_test`ではTURNとPTOを拒否する。`PTO_STOP`拒否をPTO停止成功として偽装しない。stateに不適合なcommandを拒否し、latched状態ではARMやMOVEを拒否する。resetは全解除guard成立時だけ受理する。validation失敗でactive operation IDを新規発行しない。STOP/EMERGENCY_STOPのdefensive actionでもlatched状態を解除しない。

## 15. COMMAND_RESULT・snapshot・ログ

transport ACKと`COMMAND_RESULT`を分離し、rejected commandをacceptedと表示しない。defensive actionはrejected＋defensive actionとして記録する候補とし、last accepted sequenceを更新しない。operation ID無効化をsnapshotへ反映する。output apply失敗を成功扱いしない。`COMMAND_RESULT`送信失敗でcommandを再適用せず、snapshot送信失敗やログ失敗で安全停止を遅らせない。payload全体または秘密情報を無条件保存しない。

## 16. validation failure matrix

STOP/EMERGENCY_STOP欄の`DEFENSIVE_ZERO`はidentification gate通過済みの場合だけを意味する。

| Failure | Normal command | STOP | EMERGENCY_STOP | Extends liveness | Updates accepted sequence |
| --- | --- | --- | --- | --- | --- |
| oversize | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| malformed | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| unsupported_version | FORMAL_REJECT | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| invalid_message_type | FORMAL_REJECT | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| wrong_direction | FORMAL_REJECT | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| invalid_boot_id | FORMAL_REJECT | NO_MESSAGE_ACTION | NO_MESSAGE_ACTION | No | No |
| invalid_session | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| wrong_sender_role | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| not_control_owner | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| exact_duplicate | cached result / no reapply | no reapply; zero維持 | no reapply; latch/zero維持 | No | No |
| sequence_collision | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| stale_sequence | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| invalid_freshness | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| expired | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| missing_required_field | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| invalid_payload | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| capability_unavailable | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| invalid_state | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| guard_failed | FORMAL_REJECT | FORMAL_REJECT + DEFENSIVE_ZERO | FORMAL_REJECT + DEFENSIVE_ZERO | No | No |
| output_apply_failed | all outputs zero + FAULT候補 | all outputs zero + FAULT候補 | all outputs zero + FAULT候補 | No | command受理済みなら維持、未受理ならNo |

STOPまたはEMERGENCY_STOP欄で`DEFENSIVE_ZERO`となった場合、非ラッチACTIVE状態は対応するREADYへ移行する。既存のlatched状態は維持する。これは`FORMAL_ACCEPT`または正式な非常停止ラッチを意味しない。

## 17. 文書ベース検証シナリオ

各行はGiven / When / Thenを構成する。`DZ`は`DEFENSIVE_ZERO`、`op ID`はactive operation IDを表す。

| No. | Scenario (Given / When) | Validation結果・formal acceptance・defensive action | Then: 出力 / op ID / 最終状態 / liveness |
| ---: | --- | --- | --- |
| 1 | DISARMED、全guard成立 / 有効ARM | FORMAL_ACCEPT / Yes / No | zero / none / one_side_testの場合はDRIVE_READY、将来のDRIVE/PTO分離profileの場合はARMED_NEUTRAL / No |
| 2 | DRIVE_READY / 有効MOVE_FORWARD | FORMAL_ACCEPT / Yes / No | forward / new / DRIVE_ACTIVE / Yes |
| 3 | DRIVE_ACTIVE / 有効CONTROL_UPDATE | FORMAL_ACCEPT / Yes / No | 維持 / 維持 / DRIVE_ACTIVE / Yes |
| 4 | DRIVE_ACTIVE / CONTROL_UPDATE停止、通信・制御更新watchdog timeout | internal safety event / commandなし / No | zero、armed=false / invalid / COMM_LOSS_LATCHED / No |
| 5 | DRIVE_ACTIVE / 有効deadman=false | FORMAL_ACCEPT / Yes / No | zero / invalid / DRIVE_READY / No |
| 6 | DRIVE_READY / wrong boot ID MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 7 | DRIVE_READY / invalid session MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 8 | DRIVE_READY / non-owner MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 9 | DRIVE_ACTIVE / exact duplicate MOVE | cached result、再適用なし / No(new) / No | 維持 / 維持 / DRIVE_ACTIVE / No |
| 10 | DRIVE_READY / sequence collision MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 11 | DRIVE_READY / stale MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 12 | DRIVE_READY / expired MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 13 | DRIVE_READY / invalid payload MOVE | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 14 | one_side_test、DRIVE_READY / TURN_LEFTまたはTURN_RIGHT | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 15 | one_side_test、DRIVE_READY / PTO_START | FORMAL_REJECT / No / No | zero / none / DRIVE_READY / No |
| 16 | DISARMED / MOVE | FORMAL_REJECT / No / No | zero / none / DISARMED / No |
| 17 | DRIVE_ACTIVE / 有効STOP | FORMAL_ACCEPT / Yes / No | zero / invalid / DRIVE_READY / No |
| 18 | PTO_ACTIVE / 有効STOP | FORMAL_ACCEPT / Yes / No | zero / invalid / PTO_READY / No |
| 19 | DRIVE_READY、直前のSTOP処理済み / 同一session、同一sequence、同一message ID、同一内容のexact duplicate STOP | cached result、再適用なし / No(new) / No | zero / invalid / DRIVE_READY / No |
| 20 | DRIVE_ACTIVE / stale STOP、gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY / No |
| 21 | DRIVE_ACTIVE / expired STOP、gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY / No |
| 22 | DRIVE_ACTIVE / invalid session STOP、gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY / No |
| 23 | DRIVE_ACTIVE、有効なactive operation ID、独立watchdogは未期限切れ / malformed STOP | NO_MESSAGE_ACTION / No / No | 現在の有効走行出力を維持 / 現在値を維持 / DRIVE_ACTIVE / No。独立watchdogは更新されず継続し、期限到達時に別途安全停止する |
| 24 | DRIVE_ACTIVE、有効なactive operation ID、独立watchdogは未期限切れ / wrong boot ID STOP | NO_MESSAGE_ACTION / No / No | 現在の有効走行出力を維持 / 現在値を維持 / DRIVE_ACTIVE / No。wrong boot IDを現在bootのSTOPとして扱わず、独立watchdogは更新されず継続し、期限到達時に別途安全停止する |
| 25 | DRIVE_ACTIVE / 有効EMERGENCY_STOP | FORMAL_ACCEPT / Yes / No | zero / invalid / EMERGENCY_STOP_LATCHED / No |
| 26 | EMERGENCY_STOP_LATCHED / exact duplicate EMERGENCY_STOP | cached result、再適用なし / No(new) / No | zero / invalid / EMERGENCY_STOP_LATCHED / No |
| 27 | DRIVE_ACTIVE / stale EMERGENCY_STOP、identification gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY、正式ESTOP latchなし / No |
| 28 | DRIVE_ACTIVE / expired EMERGENCY_STOP、identification gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY、正式ESTOP latchなし / No |
| 29 | DRIVE_ACTIVE / invalid session EMERGENCY_STOP、identification gate成立 | FORMAL_REJECT / No / DZ | zero / invalid / DRIVE_READY、正式ESTOP latchなし / No |
| 30 | DRIVE_ACTIVE、有効なactive operation ID、独立watchdogは未期限切れ / malformed EMERGENCY_STOP | NO_MESSAGE_ACTION / No / No | 現在の有効走行出力を維持 / 現在値を維持 / DRIVE_ACTIVE / No。message由来の非常停止ラッチなし。独立watchdogは更新されず継続し、期限到達時に別途安全停止する |
| 31 | DRIVE_ACTIVE、有効なactive operation ID、独立watchdogは未期限切れ / wrong boot ID EMERGENCY_STOP | NO_MESSAGE_ACTION / No / No | 現在の有効走行出力を維持 / 現在値を維持 / DRIVE_ACTIVE / No。message由来の非常停止ラッチなし。独立watchdogは更新されず継続し、期限到達時に別途安全停止する |
| 32 | DRIVE_READY、同時により高優先の非常停止なし / accepted MOVEのoutput apply失敗 | apply failure / formal受理済み・成功報告No / safety zero | zero / invalid / FAULT_LATCHED / No |
| 33 | EMERGENCY_STOP_LATCHED、解除guard不成立 / emergency_stop_reset | FORMAL_REJECT / No / No | zero / none / EMERGENCY_STOP_LATCHED / No |
| 34 | EMERGENCY_STOP_LATCHED、全guard成立 / valid emergency_stop_reset | FORMAL_ACCEPT / Yes / No | zero / none / DISARMED、再ARM必須 / No |
| 35 | COMM_LOSS_LATCHED、reconnect後の新session / old CONTROL_UPDATE | FORMAL_REJECT / No / No | zero / invalid / COMM_LOSS_LATCHED / No |
| 36 | DRIVE_ACTIVE、有効なcontroller session終了時にactive operationあり / 有効SESSION_END | FORMAL_ACCEPT / Yes / No | zero、armed=false / invalid / COMM_LOSS_LATCHED / No |

## 18. 未確定事項と次の承認対象

未確定事項は、message size上限、sequence gap受理方針、sequence wraparound、result cache保持期間、exact duplicate判定方法、security認証方式、非owner defensive stopの最終securityレビュー、TTL最終値、watchdog最終値、PTOデッドマン方式、output applyのatomicityおよびdiagnostic詳細である。

次の承認対象候補は`software/rover_control/protocol/v0/test_vectors/README.md`とする。目的は本文書のvalidation failure matrixを機械可読test vectorへ落とす前の形式定義である。今回はJSON、自動テストおよび同文書を作成しない。
