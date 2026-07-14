# Paddy Swarm Rover Control Protocol v0

```text
Status: Draft / Simulator-first / Real motor output not approved
```

本書はprotocol v0の論理メッセージとvalidation契約を定義します。wire encoding、データ型、バイト配置、具体的なJSONキーは未定義です。上位文書は[`README.md`](../../README.md)、[`SAFETY_REQUIREMENTS.md`](../../safety/SAFETY_REQUIREMENTS.md)、[`STATE_MACHINE.md`](../../safety/STATE_MACHINE.md)、[`protocol/README.md`](../README.md)、[`docs/safety.md`](../../../../docs/safety.md)です。矛盾時は物理安全設計、安全要件、状態機械、protocol境界、本書の順で優先します。

## 1. 文書の目的と状態

- v0の論理message集合、方向、envelope、validation順序を定義する。
- schemaとencodingは定義しない。
- simulator-firstとし、実モーター出力は未承認とする。
- v0では破壊的変更があり得る。

## 2. 固定する安全原則

- ESP32の状態を正本とする。
- UI送信成功やtransport ACKを動作成功と扱わない。
- reconnectでARMや動作を復元しない。
- sessionをまたいでsequenceを引き継がない。
- MOVEは単発送信で無期限継続しない。
- heartbeatやtelemetryだけでcontrol livenessを延長しない。
- DRIVEとPTOを同時許可しない。
- STOPとEMERGENCY_STOPを区別する。
- 物理非常停止はprotocolから独立する。
- 未知、不正、矛盾時はfail-closedとする。

## 3. endpointとrole

EndpointはController、Rover、Read-only observer候補です。1 roverにつきcommand権限を持つControllerは最大1つとします。Roverが権限状態の正本です。Observerはcommandを送信できません。controller切替は`DISARMED`かつ全出力ゼロで、人間の明示確認後だけ許可候補とします。controller喪失時は通信断安全処理を行います。cloud accountはsession成立条件にしません。

## 4. v0論理メッセージ集合

| Message type | Direction | Purpose | Changes rover state | Extends control liveness |
| --- | --- | --- | --- | --- |
| `SESSION_HELLO` | Client → Rover | session候補の開始 | No | No |
| `SESSION_ACCEPTED` | Rover → Client | session成立通知 | No | No |
| `SESSION_REJECTED` | Rover → Client | session拒否通知 | No | No |
| `SESSION_END` | Bidirectional | session終了要求・通知 | Safety processing only | No |
| `CAPABILITY_SNAPSHOT` | Rover → Client | capability通知 | No | No |
| `COMMAND` | Controller → Rover | 状態変更・操作要求 | After validation | No |
| `CONTROL_UPDATE` | Controller → Rover | 既存active operationの継続 | No new operation | Yes |
| `COMMAND_RESULT` | Rover → Controller | command受付・結果 | No | No |
| `STATE_SNAPSHOT` | Rover → Client | 正式状態snapshot | No | No |
| `TELEMETRY` | Rover → Client | 継続測定・診断値 | No | No |
| `ROVER_HEARTBEAT` | Rover → Client | Rover生存通知 | No | No |
| `DIAGNOSTIC` | Rover → Client | 診断情報 | No | No |

この12件以外を正式なv0 message typeとして追加しません。`CONTROL_UPDATE`だけが既存の有効な動作を継続でき、`COMMAND`単独でMOVEを無期限継続しません。

## 5. 共通envelopeの概念項目

候補は`protocol_version`、`message_type`、`message_id`、`rover_id`候補、`rover_boot_id`、`session_id`、`sender_id`、`sender_role`、`sequence`、`freshness_reference`、`ttl`、`payload`です。全項目が全messageで必須とは限らず、必須性は将来schemaで固定します。具体名、型、桁数、encodingは未確定です。個人情報や農地座標をenvelopeへ入れません。

## 6. session negotiation

`SESSION_HELLO`は対応version、要求role、client識別候補、instance nonce候補を通知します。`SESSION_ACCEPTED`は選択version、session ID、role、rover boot ID、controller ownership、capability version候補を返します。`SESSION_REJECTED`はunsupported version、controller active、role unavailable、security failure、malformed等を通知します。`SESSION_END`時、Roverは必要に応じて出力ゼロと通信断処理を行い、ARM状態を次sessionへ引き継ぎません。

## 7. rover_boot_idとsession_id

- ESP32再起動ごとに新しい`rover_boot_id`を生成する候補とする。
- 再起動前のsession、sequence、ARM、MOVE、PTOを復元しない。
- session IDは再利用しない。
- boot IDまたはsession ID不一致のcommandを拒否する。
- reconnectでは新session候補を作る。
- ID生成方式は未確定で、認証tokenとして使用しない。

## 8. sequence namespace

`controller_to_rover_command_sequence`と`rover_to_client_message_sequence`を論理的に分離します。command sequenceはsession内で単調増加し、duplicate、stale、危険側out-of-orderを適用しません。gapを命令繰返しと解釈しません。resetは新sessionだけです。最大値、wraparound、永続化は未確定で、規則決定まで実機出力を有効化しません。

## 9. freshness_referenceと期限

wall clock同期を前提にしません。Roverが現在boot/sessionに属するfreshness reference候補を発行し、Controllerがcommandへ関連付け、Roverが単調時間でageとTTLを検証できる方式を候補とします。古いboot/session、期限切れreference、最大値超過TTLを拒否します。具体生成方式とwire表現は未確定で、security tokenや認証tokenと同一視しません。

## 10. COMMAND

| Command type | Starts output | Latched effect | Requires control owner | one_side_test |
| --- | --- | --- | --- | --- |
| `ARM` | No | No | Yes | Allowed with guards |
| `DISARM` | No | No | Yes | Allowed |
| `SET_SPEED_LIMIT` | No | No | Yes | Allowed |
| `SELECT_DRIVE` | No | No | Yes | Profile-dependent |
| `SELECT_NEUTRAL` | No | No | Yes | Profile-dependent |
| `SELECT_PTO` | No | No | Yes | Rejected |
| `MOVE_FORWARD` | After guards | No | Yes | Allowed |
| `MOVE_REVERSE` | After guards | No | Yes | Allowed |
| `TURN_LEFT` | After guards | No | Yes | Rejected |
| `TURN_RIGHT` | After guards | No | Yes | Rejected |
| `STOP` | No | No | Yes | Allowed |
| `EMERGENCY_STOP` | No | Yes | Yes | Allowed |
| `PTO_START` | After guards | No | Yes | Rejected |
| `PTO_STOP` | No | No | Yes | Rejected/unavailable |
| `fault_reset` | No | Reset request | Yes | Guarded |
| `emergency_stop_reset` | No | Reset request | Yes | Guarded |

ARMとSET_SPEED_LIMITは出力開始ではありません。MOVEは継続`CONTROL_UPDATE`を必要とします。mode選択だけで出力しません。状態遷移の正本は`STATE_MACHINE.md`です。

## 11. CONTROL_UPDATE

`CONTROL_UPDATE`は既存のactive operationをデッドマン継続する専用message候補です。session、boot ID、controller ownership、control sequence、active operation ID、direction/command reference、deadman asserted、freshness reference、TTLを概念項目候補とします。

- generic heartbeatとして使わない。
- operation ID不一致を拒否する。
- direction、modeをこのmessageだけで変更しない。
- ARM、DISARM、STOP、EMERGENCY_STOPの代替にしない。
- 有効期間内の更新だけが継続候補になる。
- 更新停止時はESP32 watchdogで出力ゼロにする。
- 受信だけで新しい動作を開始しない。
- STOP等でactive operation IDを無効化する。

## 12. active operation ID

`active operation ID`は、`MOVE_FORWARD`、`MOVE_REVERSE`、将来のPTO動作と、それを継続する`CONTROL_UPDATE`を安全に関連付ける概念です。

- 出力を伴うcommandが全validationを通過した後、RoverがIDを割り当てる方式を候補とする。
- Controllerが任意IDを指定して新規動作を開始しない。
- `COMMAND_RESULT`または`STATE_SNAPSHOT`でControllerへ通知する。
- `CONTROL_UPDATE`は現在のactive operation IDとの一致を必要とする。
- 不一致、古い、別sessionのoperation IDを拒否する。
- reconnect後にoperation IDを引き継がず、認証tokenとして使用しない。
- 型、長さ、生成方式は未確定とする。

次のすべてでactive operation IDを無効化します。

- `STOP`
- 正常に受理された`PTO_STOP`
- `DISARM`
- `deadman_released`
- `command_expired`
- `communication_lost`またはwatchdog停止
- `fault_detected`
- `EMERGENCY_STOP`
- session終了
- ESP32再起動
- mode変更前のNEUTRAL遷移

無効化後に古い`CONTROL_UPDATE`を受信しても出力を再開しません。

## 13. STOP処理

正規STOPは、current valid sessionのcontrol ownerから届き、parse、対応version、通常validationを通過したcommandです。冪等に処理し、該当出力をゼロにしてactive operation IDを無効化します。`DRIVE_ACTIVE`では`DRIVE_READY`、`PTO_ACTIVE`では`PTO_READY`へ遷移し、READY/DISARMEDでも出力ゼロを再確認します。fault、communication loss、EMERGENCY_STOPのラッチを解除せず、重複受信で動作を再開しません。受付と結果状態を`COMMAND_RESULT`候補で通知します。

defensive local stopは正規acceptanceと明確に分離します。不正commandをacceptedとして記録せず、認識可能な停止意図に対して出力ゼロを選べる可能性を残します。これだけで正式状態解除は行わず、最終規則は`VALIDATION_ORDER.md`とtest vectorで固定します。

## 14. EMERGENCY_STOP処理

正規EMERGENCY_STOPは通常state guardやARM状態より高優先度ですが、current session、対応version、parse可能性等の最低限の構造validationを行います。冪等に全走行/PTO出力をゼロ、active operation IDを無効、armed=falseとし、`EMERGENCY_STOP_LATCHED`へ遷移します。reconnect、UI再読込み、重複受信で解除せず、解除は別command`emergency_stop_reset`と全guardを必要とし、その後も再ARMが必要です。物理非常停止はprotocolから独立します。

defensive local stopは正規acceptanceと分離します。正規受理できないmessageを成功扱いせず、認識可能な緊急停止意図に対して出力ゼロを選べる可能性を残します。無関係な端末が認証を迂回してラッチ解除できる設計にはしません。最終規則は実装前test vectorで固定します。

## 15. COMMAND_RESULT

Conceptual resultは`received`、`accepted`、`rejected`、`applied`または`state-confirmed`候補です。transport ACKとは別です。`rover_boot_id`、session ID、command ID、command sequence、result、rejection reason、resulting/current state、last accepted sequence、active operation IDまたはnoneを含む候補です。MOVEがacceptedでも新しいoperation IDを受け取る前に古い`CONTROL_UPDATE`を使いません。rejected commandでは新IDを発行しません。STOP、DISARM、fault、communication loss、EMERGENCY_STOP後はoperation IDをnoneまたは無効として通知します。正常に受理された`PTO_STOP`の結果では、resulting/current stateを`PTO_READY`、active operation IDをnoneまたは無効として通知します。拒否された`PTO_STOP`では新しいoperation IDを発行せず、`one_side_test`での拒否をPTO停止成功として偽装しません。receivedは動作開始を、acceptedは物理動作完了を意味しません。UIは`COMMAND_RESULT`と最新の`STATE_SNAPSHOT`で結果を確認します。

## 16. STATE_SNAPSHOT

ESP32の正式状態の正本です。候補はprotocol/session/boot ID、state、armed、mode、各latch、speed limit、output availability、last accepted sequence、last stop reason、watchdog、configuration version、capability/profile、uptime、active operation IDまたはnoneです。ACTIVE状態で必要なoperation IDが欠落・矛盾する場合は正常値として扱いません。READY、DISARMED、latched状態では古いoperation IDを有効として通知しません。reconnect後に古いoperationを復元せず、snapshot受信だけで出力を開始しません。取得前のUIはUNKNOWN・操作不能です。

## 17. TELEMETRY

変化・測定値の継続通知で、`STATE_SNAPSHOT`の代替ではありません。欠落だけでUIが以前の状態を無期限保持せず、受信でcontrol livenessを延長しません。sensor未搭載値を偽装しません。送信周期は未確定で、送信失敗が停止処理を遅らせてはなりません。

## 18. ROVER_HEARTBEAT

Rover生存通知候補です。boot IDとmessage sequence、freshness reference候補を持ち得ます。state snapshotの代替ではなく、Controllerのcontrol livenessを延長しません。受信だけでARMや動作を復元しません。周期は未確定です。

## 19. CAPABILITY_SNAPSHOT

候補はprofile、drive/left/right/turn/PTO/encoder/physical-estop-reporting availability、simulator/hardware mode、real motor output enabledです。受信前にUI機能を有効化せず、capabilityがないcommandを拒否します。`one_side_test`ではTURN、PTO、right outputを利用不可とし、未搭載値を0として偽装しません。実機出力有効化には別hardware gateが必要です。

## 20. validation順序

1. transportから受信
2. message size上限候補
3. parse可能性
4. protocol version
5. message type
6. direction
7. rover boot ID
8. session ID
9. sender role
10. controller ownership
11. sequence / duplicate / stale
12. freshness reference
13. TTL / expiry
14. 必須項目
15. payload範囲
16. capability
17. current state
18. safety guard
19. state transition決定
20. 出力適用
21. COMMAND_RESULT生成
22. STATE_SNAPSHOTまたはtelemetry更新
23. ログ候補

上位validation失敗時に下位の危険処理へ進みません。出力適用は全validation後です。STOP/EMERGENCY_STOPのdefensive actionは第13・14章の例外候補として分離します。

## 21. rejection reason集合

```text
unsupported_version
invalid_message_type
wrong_direction
invalid_boot_id
invalid_session
not_control_owner
duplicate_sequence
stale_sequence
expired
malformed
missing_required_field
invalid_payload
invalid_state
guard_failed
not_armed
mode_conflict
capability_unavailable
safety_latched
```

この18件以外を正式なv0 rejection reasonとして追加しません。wire文字列や数値codeは未確定です。拒否通知失敗で安全停止を遅らせません。

## 22. reconnectフロー

transport reconnect後、UIはUNKNOWN・操作不能とし、SESSION_HELLO、新session、CAPABILITY_SNAPSHOT、STATE_SNAPSHOT、latched状態確認、安全確認、DISARMED、必要なら人間の明示ARMの順を候補とします。古いsession、operation ID、MOVEを再利用・再送せず、reconnectだけでCOMM_LOSS_LATCHEDを解除、ARM、出力しません。

## 23. simulator-first gate

session、single controller、duplicate/stale/invalid boot/session/expired拒否、MOVE開始、CONTROL_UPDATE継続と停止、STOP、EMERGENCY_STOP、reconnect自動復帰禁止、one_side capability、TURN/PTO拒否、STATE_SNAPSHOT、COMMAND_RESULTを最初に仮想ローバーで検証します。実モーター接続前にtest vector化が必要ですが、本作業では作りません。

## 24. security未解決事項

session ID、boot ID、freshness referenceは認証ではありません。ローカルネットワークだけを信頼せず、pairing、controller認証、暗号化を将来決定します。security未解決中は実モーター出力を解放しません。秘密情報をmessage、ログ、repositoryへ保存しません。

## 25. compatibility方針

- versionは`v0`。
- 未対応versionを推測解釈しない。
- v0内でも破壊的変更があり得る。
- message type/必須項目追加は明示レビューする。
- 未知message typeを無視して動作継続しない。
- hardware v2.28.2、PWA、firmware、simulatorのversionと分離する。

## 26. 未確定事項

wire encoding、正確なfield名と型、各ID生成方式、freshness reference生成、TTL上限、message size、sequence wraparound、CONTROL_UPDATE/heartbeat/telemetry周期、retry、rate limit、security、PTOデッドマン、defensive action最終規則、clock sync補助要否は未確定です。本書だけで実装開始可能とはしません。

## 27. 次の承認対象

次の1作業候補は`software/rover_control/protocol/v0/VALIDATION_ORDER.md`です。validation順序、STOP/EMERGENCY_STOP defensive action、duplicate/stale/expiredの具体例、fail-closed test casesを定義します。本作業では作成しません。
