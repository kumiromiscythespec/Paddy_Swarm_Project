# Paddy Swarm Rover Control Protocol

本書は具体的なwire schemaではなく、将来の`protocol/v0`で守る通信契約の境界文書です。上位参照文書は[`software/rover_control/README.md`](../README.md)、[`SAFETY_REQUIREMENTS.md`](../safety/SAFETY_REQUIREMENTS.md)、[`STATE_MACHINE.md`](../safety/STATE_MACHINE.md)、[`docs/safety.md`](../../../docs/safety.md)です。矛盾する場合は安全文書を優先します。

## 1. 文書の目的

- PWA、仮想ローバー、ESP32が共有する通信契約の境界を定義する。
- transportやデータ形式に依存しない。
- ESP32側の安全状態を正本とする。
- 物理非常停止を代替せず、実田んぼでの安全を保証しない。
- 実装済み通信仕様として扱わない。

## 2. 適用範囲

対象はsession確立、controller権限、command envelope、sequence、期限、command受付・拒否・結果、liveness、state snapshot、telemetry、capability、version、reconnect、ログとの関連です。クラウド管理、Google連携、正確な農地座標、完全自動運転、transport・wire encoding・認証方式の最終決定は対象外です。

## 3. 安全上の責任境界

- スマートフォンが送信成功と表示しても実機動作成功を意味しない。
- transport ACKだけでcommandの受理・適用を判断しない。
- ESP32がcommandを検証し、状態遷移と出力可否を決定する。
- UIはESP32の最新かつ有効なstate snapshotまたはtelemetryを正本とする。
- 通信不能でもESP32側watchdogが停止を成立させる。
- reconnectだけでARMや動作を復元しない。
- protocol異常時は拒否または安全停止とする。
- 物理非常停止はprotocolから独立する。

## 4. transportとencodingからの独立

- WebSocket、BLE、HTTP、MQTT等を現段階では選ばない。
- JSON、CBOR、Protocol Buffers等を現段階では選ばない。
- transportが順序を保証しても、protocol側で重複、遅延、再送、sessionを検証する。
- transport切断検出だけをwatchdogの唯一の根拠にしない。
- message size、周期、再送回数の最終値は未確定とする。
- transport変更後も安全状態機械の意味を変えない。

## 5. 論理メッセージ分類

| Logical class | Purpose |
| --- | --- |
| Session negotiation | version、session、controller候補の確立 |
| Capability | 機体構成と利用可能機能の通知 |
| Command | 操作者が要求する状態変更または操作 |
| Command result | commandの受信、受理、拒否、適用結果 |
| State snapshot | ESP32の現在の正式状態 |
| Telemetry | 状態、出力、watchdog、異常等の継続通知 |
| Liveness | heartbeatまたは制御更新監視 |
| Diagnostic | エラー、拒否理由、診断情報 |

これらは論理分類であり、具体的なmessage type名やschemaではありません。

## 6. sessionとcontroller権限

- commandは有効なsessionに属する。
- reconnect時に以前のsessionを無条件で再利用しない。
- sessionをまたいでsequenceやARM状態を引き継がない。
- 初期MVPでは1台のローバーにcommand権限を持つcontrollerは同時に最大1つとする。
- 追加接続はread-only候補または拒否とする。
- controller権限を無言で奪取しない。
- controller切替時は全出力ゼロとし、`DISARMED`および人間の明示確認を基本条件とする。
- controller喪失時は通信断安全処理を行う。
- controller leaseの方式は未確定とする。

クラウドアカウントをsession成立条件にはしません。

## 7. command envelopeの概念項目

operator commandが最低限持つ概念項目は、protocol version、message class、session ID、controllerまたはsender識別子、command ID、command sequence、command type、issued time、validityまたはexpiry情報、payloadです。

- 具体的なフィールド名とencodingは`protocol/v0`で決定する。
- 必須項目欠落、未対応version、別session、不明command、範囲外payloadを拒否する。
- 拒否により状態や出力を危険側へ変更しない。

## 8. sequenceと冪等性

- sequenceはsession内で単調増加させる。
- 過去、重複、out-of-orderのcommandを危険側へ適用しない。
- sequence resetは新しいsessionでのみ可能とする。
- command IDとsequenceの関係は将来schemaで固定する。
- sequence gapを命令繰返しとして扱わない。
- STOPやEMERGENCY_STOPの重複受信で危険な副作用を発生させない。
- 重複時は以前のcommand resultを再通知する方式を候補とする。

未対応version、破損message、無効session等の検証を、STOPやEMERGENCY_STOPでも無視しません。物理非常停止はprotocol検証と無関係に作動します。

## 9. 時刻・期限・watchdog

- 制御commandは受信側で検証可能な有効期間を持つ。
- issued timeだけを安全根拠にしない。
- スマートフォンとESP32のwall clock一致を前提にしない。
- session内の単調時間、TTL、受信時刻等を組み合わせる方式を将来決定する。
- 期限切れcommandを拒否し、遅延packetで動作を再開しない。
- command受信だけでwatchdogを無条件に延長しない。
- 有効な制御更新だけをliveness更新候補とする。
- heartbeat受信だけでARMや動作を復元しない。
- watchdog最終時間は安全試験で決定する。

## 10. operator commandと内部eventの分類

### Operator-originated command candidates

| Event | Classification |
| --- | --- |
| `ARM` | operator |
| `DISARM` | operator |
| `SET_SPEED_LIMIT` | operator |
| `SELECT_DRIVE` | operator |
| `SELECT_NEUTRAL` | operator |
| `SELECT_PTO` | operator |
| `MOVE_FORWARD` | operator |
| `MOVE_REVERSE` | operator |
| `TURN_LEFT` | operator |
| `TURN_RIGHT` | operator |
| `STOP` | operator |
| `EMERGENCY_STOP` | operator |
| `PTO_START` | operator |
| `PTO_STOP` | operator |
| `fault_reset` | operator |
| `emergency_stop_reset` | operator |

### Receiver-localまたは状態機械内部event

| Event | Classification |
| --- | --- |
| `boot_complete` | internal |
| `boot_failed` | internal |
| `deadman_released` | internal |
| `command_expired` | internal |
| `communication_lost` | internal |
| `communication_restored` | internal |
| `fault_detected` | internal |

23件を重複なく1回ずつ分類します。operatorが内部eventを自由に送信できる設計にはしません。`deadman_released`はUI通知を契機に生成される可能性がありますが、ESP32側の期限切れ停止が独立して成立しなければなりません。

## 11. command意味の基本規則

- `ARM`: guard成立後に安全状態を進める要求であり、出力開始ではない。
- `DISARM`: 全出力ゼロおよびDISARMED要求。
- `MOVE_FORWARD` / `MOVE_REVERSE`: 有効なデッドマン更新中だけ動作候補。
- `TURN_LEFT` / `TURN_RIGHT`: `one_side_test`では拒否。
- `STOP`: 通常停止。冪等、非ラッチ。
- `EMERGENCY_STOP`: 高優先度のラッチ停止。
- `SET_SPEED_LIMIT`: 始動commandではない。
- `SELECT_DRIVE` / `SELECT_NEUTRAL` / `SELECT_PTO`: モード選択であり直接出力しない。
- `PTO_START`: PTO_READYかつ全guard成立時だけ有効。
- `PTO_STOP`: PTO出力停止。
- `fault_reset`: 原因解消後にBOOT_SAFEへ戻す候補。
- `emergency_stop_reset`: 全解除guard成立後にDISARMEDへ戻す候補。

状態遷移の正本は`STATE_MACHINE.md`です。

## 12. Command result

transport上の通信成功とは別に、`received`、`accepted`、`rejected`、`applied`または`state-confirmed`の段階を区別します。具体的なstatus名は将来確定します。

Command resultは概念上、session ID、command ID、command sequence、result、rejection reason候補、resulting/current state、ESP32が最後に受理したsequenceを持ちます。

- `received`は動作開始を意味しない。
- `accepted`は物理動作完了を意味しない。
- UIはstate snapshotまたはtelemetryで結果状態を確認する。
- command result喪失時にcommandを無条件再実行しない。

## 13. 拒否理由カテゴリ

概念カテゴリは`unsupported_version`、`invalid_session`、`not_control_owner`、`duplicate_sequence`、`stale_sequence`、`expired`、`malformed`、`missing_required_field`、`invalid_payload`、`invalid_state`、`guard_failed`、`not_armed`、`mode_conflict`、`capability_unavailable`、`emergency_stop_latched`、`fault_latched`、`communication_latched`です。

具体的なwire codeは未確定です。拒否通知やログより安全な出力停止を優先します。

## 14. State snapshotとtelemetry

ESP32が送る状態情報候補は、protocol version、session ID、controller権限状態、正式な安全状態、armed、selected mode、各latch、速度指令、速度上限、drive/PTO出力可否、last accepted sequence、last stop reason、watchdog状態、configuration version、capability/profile、単調時刻またはuptimeです。

- UIは最新かつ有効な状態を正本とする。
- UI再読込み直後はUNKNOWN・操作不能とする。
- 最新snapshot受信前にDISARM等を推測しない。
- `one_side_test`で未搭載の右側出力を0として偽装しない。
- 未搭載値はunavailableまたはnot presentとして表現する。

## 15. capabilityとprofile

候補は`one_side_test`、`dual_side_drive`、PTO/TURN enabled、left/right output available、encoder available、physical estop status availableです。

- profile名は文書上の識別名である。
- capabilityがないcommandを拒否する。
- capability受信前にUI機能を有効表示しない。
- capability変化だけでARMや動作を開始しない。
- 初期片側試験ではPTOとTURNを無効化する。

## 16. reconnectと復旧

- UI再接続時はUNKNOWN・操作不能から開始する。
- 古いUI状態を実機状態として復元しない。
- 新しいsession候補を確立し、state snapshotを取得する。
- 通信復旧だけで`COMM_LOSS_LATCHED`を解除しない。
- reconnectだけでARM、MOVE、PTOを再送しない。
- latched状態をUI判断で解除しない。
- 再ARMには人間の明示操作を必要とする。

## 17. デッドマンとliveness

- MOVEは単発送信だけで無期限継続しない。
- 有効なデッドマン更新を継続して必要とする。
- UIは指を離したとき停止またはrelease意図を通知する。
- その通知が失われてもESP32側で期限切れ停止する。
- バックグラウンド移行、画面ロック、ページ終了、通信断を想定する。
- heartbeatとMOVE更新を同一messageにするかは未確定とする。
- 通常telemetryをcommand livenessとして誤用しない。
- STOP送信成功を安全成立の唯一条件にしない。

## 18. security境界

- ローカルネットワークであることだけを信頼根拠にしない。
- 無関係な端末からcommandを受け付けない仕組みを必要とする。
- 認証、pairing、暗号化方式は未確定とする。
- 仮想段階と実モーター段階で必要なsecurity gateを分けてレビューする。
- 実モーター出力解放前にcontroller識別と不正操作対策を別途確認する。
- security異常時に実機出力を有効化しない。
- 秘密情報をrepository、通常ログ、telemetryへ保存しない。
- cloud接続をsecurity成立条件にしない。

## 19. ログとプライバシー

記録候補はsession/controller lifecycle、command受信・受理・拒否、state snapshot/change、communication lifecycle、watchdog stopです。

- protocolとログ形式を独立してversion管理する。
- ログ失敗で安全停止を遅らせない。
- Wi-Fiパスワード、秘密鍵、token、正確な農地座標を標準messageやログへ入れない。
- payload全体の無条件ログ保存を避ける。

## 20. version方針

- 最初のprotocol系列は`v0`とする。
- 各messageはprotocol versionを識別可能にする。
- 未対応versionを推測解釈しない。
- v0では破壊的変更があり得る。
- hardware v2.28.2とprotocol v0を混同しない。
- PWA、firmware、simulatorのversionとも独立する。
- compatibility詳細は`protocol/v0`で定義する。

## 21. 概念上の正常フロー

初回接続はtransport接続、version/session候補確認、controller権限確認、capabilityとstate snapshot受信、速度上限設定、明示ARMの順を候補とします。

デッドマン走行は有効MOVE、command result、DRIVE_ACTIVE状態通知、継続更新、releaseまたはSTOP、DRIVE_READY確認の順です。

通信断は有効更新停止、ESP32 watchdog、全出力ゼロ、COMM_LOSS_LATCHED、reconnect、state snapshot、安全確認、DISARMED、必要なら再ARMの順で、自動解除しません。

非常停止はEMERGENCY_STOP、全出力ゼロ、EMERGENCY_STOP_LATCHED、全解除guard、DISARMED、再ARMの順です。

## 22. 未確定事項

transport、encoding、フィールド名、message type名、TTL表現、session確立方法、controller lease、authentication、encryption、command result status、rejection code、heartbeat/telemetry周期、最大message size、retry、rate limit、clock同期方式、v0 compatibility詳細は未確定です。

未確定事項を理由に安全上の固定条件を弱めません。

## 23. 次の承認対象

次の1作業候補は`software/rover_control/protocol/v0/README.md`です。v0で使用するmessage集合、envelopeの具体的な論理フィールド、validation順序、compatibility、test vector方針を定義します。本作業ではこのファイル、schema、コードを作成しません。
