# Paddy Swarm Rover Control Safety Requirements

## 1. 文書の目的

本書は、スマートフォン PWA、仮想ローバー、ESP32 実機に共通する安全要求を、実装言語や通信技術に依存せず定義する。UI の利便性より安全停止を優先するが、実田んぼでの安全稼働を保証する文書ではない。ルートの [`docs/safety.md`](../../../docs/safety.md) と [`software/rover_control/README.md`](../README.md) を上位参照文書とする。

## 2. 適用範囲

対象は、スマートフォン操作 UI、共通通信プロトコル、仮想ローバー、ESP32 ファームウェア、モータードライバー出力、コマンド受付・拒否、通信監視、安全状態、テレメトリー、ログである。

初期ハードウェア候補は ESP32、Cytron MD10C、JGB37-520 DC 12 V エンコーダー付きモーター、物理非常停止、12 V リレー、5 A ヒューズ、12 V→5 V 降圧器、12.8 V LiFePO4 とする。最初はモーター1基と MD10C 1枚の片側駆動試験、将来は左右2基と MD10C 2枚を想定する。これらの数値・機器は候補であり、実測・試験済みの保証値ではない。

## 3. 対象外と安全境界

- **PSRC-SAFE-BOUNDARY-001:** アプリは物理非常停止の代替であってはならない（MUST NOT）。
- **PSRC-SAFE-BOUNDARY-002:** ESP32 の停止処理は物理電源遮断の代替であってはならない（MUST NOT）。
- **PSRC-SAFE-BOUNDARY-003:** ソフトウェアだけで安全を保証してはならない（MUST NOT）。
- **PSRC-SAFE-BOUNDARY-004:** クラウドまたはインターネット接続を安全成立条件にしてはならない（MUST NOT）。
- **PSRC-SAFE-BOUNDARY-005:** スマートフォンが故障・停止しても、ESP32 側は安全停止できなければならない（MUST）。
- **PSRC-SAFE-BOUNDARY-006:** 仮想試験を通過するまで実モーターを接続してはならない（MUST NOT）。
- **PSRC-SAFE-BOUNDARY-007:** 実機駆動試験と浮力・水・泥・実田んぼ試験を分離しなければならない（MUST）。

## 4. 規定用語

- **MUST / 必須:** 適合のため必ず満たす。
- **MUST NOT / 禁止:** 適合のため実施してはならない。
- **SHOULD / 推奨:** 原則として満たし、外す場合は理由を記録する。
- **MAY / 任意:** 安全境界を弱めない範囲で選択できる。

固定する安全原則には MUST または MUST NOT を使用する。

## 5. 安全責任の優先順位

1. 物理非常停止・物理電源遮断
2. ESP32 側の安全状態と出力停止
3. 通信プロトコルの検証と拒否
4. スマートフォン UI の停止操作
5. 操作者への表示・警告

- **PSRC-SAFE-AUTH-001:** 下位機構は上位機構を解除または上書きしてはならない（MUST NOT）。
- **PSRC-SAFE-AUTH-002:** UI 表示より ESP32 が報告する実状態を正本としなければならない（MUST）。

## 6. 起動時安全要件

- **PSRC-SAFE-BOOT-001:** 電源投入直後は `DISARM` でなければならない（MUST）。
- **PSRC-SAFE-BOOT-002:** 起動時の PWM 出力はゼロでなければならない（MUST）。
- **PSRC-SAFE-BOOT-003:** DIR 状態だけでモーターが動かない構造にしなければならない（MUST）。
- **PSRC-SAFE-BOOT-004:** PTO 出力は停止していなければならない（MUST）。
- **PSRC-SAFE-BOOT-005:** 過去セッションの ARM 状態と走行命令を復元してはならない（MUST NOT）。
- **PSRC-SAFE-BOOT-006:** 通信確立だけで ARM してはならず、再起動後に自動始動してはならない（MUST NOT）。
- **PSRC-SAFE-BOOT-007:** 設定の読込み失敗、未知値、不正値では実機出力を有効化してはならない（MUST NOT）。

## 7. ARM / DISARM 要件

- **PSRC-SAFE-ARM-001:** ARM は人間の明示操作を必要としなければならない（MUST）。
- **PSRC-SAFE-ARM-002:** 接続確立だけで ARM してはならない（MUST NOT）。
- **PSRC-SAFE-ARM-003:** ARM 前に出力ゼロの STOP 状態と、有効な速度上限を確認しなければならない（MUST）。
- **PSRC-SAFE-ARM-004:** 非常停止中または通信異常中の ARM を拒否しなければならない（MUST）。
- **PSRC-SAFE-ARM-005:** DISARM 時は直ちにモーター出力をゼロにし、以後の走行命令を拒否しなければならない（MUST）。
- **PSRC-SAFE-ARM-006:** 再接続後および非常停止解除後は、明示的な再 ARM を必要としなければならない（MUST）。

## 8. デッドマン操作要件

- **PSRC-SAFE-DEADMAN-001:** 前進・後進・旋回は操作者が押している間だけ有効でなければならない（MUST）。
- **PSRC-SAFE-DEADMAN-002:** 指を離した場合、UI は停止要求を送らなければならない（MUST）。
- **PSRC-SAFE-DEADMAN-003:** ESP32 は UI イベント欠落を前提に、継続命令の有効期限を監視しなければならない（MUST）。
- **PSRC-SAFE-DEADMAN-004:** 単発 MOVE 命令だけで無期限に走行してはならない（MUST NOT）。
- **PSRC-SAFE-DEADMAN-005:** 継続操作には heartbeat または期限付き更新を必要としなければならない（MUST）。
- **PSRC-SAFE-DEADMAN-006:** 画面非表示、バックグラウンド移行、ページ終了時に UI は停止要求を試みなければならない（MUST）。
- **PSRC-SAFE-DEADMAN-007:** UI の停止要求の送信成功を安全成立の前提にしてはならない（MUST NOT）。

## 9. 通信断・watchdog 要件

- **PSRC-SAFE-COMM-001:** 有効な制御更新が候補値 0.5〜1.0 秒程度途切れた場合、ESP32 は停止しなければならない（MUST）。
- **PSRC-SAFE-COMM-002:** 正確な閾値は設定可能とし、安全試験で決定しなければならない（MUST）。
- **PSRC-SAFE-COMM-003:** 閾値をソースコード各所へ分散させてはならない（MUST NOT）。
- **PSRC-SAFE-COMM-004:** watchdog 停止時は PWM をゼロにしなければならない（MUST）。
- **PSRC-SAFE-COMM-005:** 通信復旧だけで走行を再開してはならない（MUST NOT）。
- **PSRC-SAFE-COMM-006:** 復旧後は DISARM または再 ARM 待ちへ移行しなければならない（MUST）。
- **PSRC-SAFE-COMM-007:** 古い heartbeat で watchdog を延長してはならない（MUST NOT）。
- **PSRC-SAFE-COMM-008:** テレメトリー送信失敗より制御入力監視を優先し、通信ライブラリの例外・切断でも安全停止しなければならない（MUST）。

## 10. コマンド完全性要件

各コマンドは、protocol version、session ID、command sequence number、command type、issued timestamp、expiry または有効期間、payload を持つ方針とする。通信データ形式自体は未確定である。

- **PSRC-SAFE-CMD-001:** 期限切れ、過去の連番、重複、別セッションの命令を拒否しなければならない（MUST）。
- **PSRC-SAFE-CMD-002:** 未知の command type、未対応 protocol version、必須項目欠落、範囲外 payload を拒否しなければならない（MUST）。
- **PSRC-SAFE-CMD-003:** 拒否した命令によって出力状態を危険側へ変更してはならない（MUST NOT）。
- **PSRC-SAFE-CMD-004:** 拒否理由をログまたはテレメトリーへ記録しなければならない（MUST）。

## 11. 速度・方向制御要件

- **PSRC-SAFE-DRIVE-001:** 有効な速度上限が未設定または不正な場合、走行を許可してはならない（MUST NOT）。
- **PSRC-SAFE-DRIVE-002:** 初期片側試験は低い速度上限から開始しなければならない（MUST）。
- **PSRC-SAFE-DRIVE-003:** PWM はハードコードせず設定値として検証しなければならない（MUST）。
- **PSRC-SAFE-DRIVE-004:** 方向反転時は一旦出力ゼロを経由しなければならない（MUST）。
- **PSRC-SAFE-DRIVE-005:** 最大出力のまま前進・後進を瞬時に切り替えてはならない（MUST NOT）。
- **PSRC-SAFE-DRIVE-006:** モーター方向の機体依存反転を設定化し、将来の左右出力を独立して制限できなければならない（MUST）。
- **PSRC-SAFE-DRIVE-007:** エンコーダー異常だけを根拠に危険な補正を行ってはならず、異常検出時は停止または出力制限へ移行しなければならない（MUST）。

加速度制限、反転待機時間、最大 PWM の具体値は試験前に固定せず、検証により決定する。

## 12. STOP 要件

- **PSRC-SAFE-STOP-001:** STOP は通常の安全停止要求であり、走行命令より優先しなければならない（MUST）。
- **PSRC-SAFE-STOP-002:** STOP 受理時は走行出力をゼロにし、処理中に古い MOVE 命令を再実行してはならない（MUST）。
- **PSRC-SAFE-STOP-003:** 初期 MVP では STOP 後に新しいデッドマン操作なしで再走行してはならない（MUST NOT）。
- **PSRC-SAFE-STOP-004:** STOP の受理と完了を記録しなければならない（MUST）。

STOP 後の正確な状態遷移は、次工程の `STATE_MACHINE.md` で定義する。

## 13. EMERGENCY_STOP 要件

- **PSRC-SAFE-ESTOP-001:** EMERGENCY_STOP は通常 STOP より高い優先度を持たなければならない（MUST）。
- **PSRC-SAFE-ESTOP-002:** 受理時は直ちに出力をゼロにし、非常停止状態をラッチしなければならない（MUST）。
- **PSRC-SAFE-ESTOP-003:** 非常停止中は MOVE、PTO_START、ARM を拒否しなければならない（MUST）。
- **PSRC-SAFE-ESTOP-004:** 通信再接続、アプリ再起動、ESP32 再起動だけで解除してはならない（MUST NOT）。
- **PSRC-SAFE-ESTOP-005:** 解除操作だけで再始動せず、解除後も明示的な再 ARM を必要としなければならない（MUST）。
- **PSRC-SAFE-ESTOP-006:** 物理非常停止はアプリと ESP32 から独立し、ソフトウェア失敗時も使用できなければならない（MUST）。
- **PSRC-SAFE-ESTOP-007:** 発生、解除要求、解除結果を記録しなければならない（MUST）。

物理非常停止の電気回路仕様は、本書だけでは保証しない。

## 14. DRIVE / NEUTRAL / PTO 排他要件

- **PSRC-SAFE-MODE-001:** DRIVE 中は PTO_START を、PTO 動作中は走行命令を拒否しなければならない（MUST）。
- **PSRC-SAFE-MODE-002:** DRIVE と PTO を直接切り替えてはならない（MUST NOT）。
- **PSRC-SAFE-MODE-003:** 切替前に NEUTRAL と出力ゼロを確認し、切替中は両出力を停止しなければならない（MUST）。
- **PSRC-SAFE-MODE-004:** PTO 停止確認前に DRIVE を許可してはならない（MUST NOT）。
- **PSRC-SAFE-MODE-005:** モード不整合時は NEUTRAL または DISARM 等の安全側へ移行しなければならない（MUST）。
- **PSRC-SAFE-MODE-006:** 初期片側モーター試験では PTO 出力を無効とし、未実装 PTO 命令を明示的に拒否しなければならない（MUST）。

## 15. アプリライフサイクル要件

- **PSRC-SAFE-APP-001:** バックグラウンド移行、画面非表示、ページ離脱時に停止要求を試みなければならない（MUST）。
- **PSRC-SAFE-APP-002:** 画面回転や UI 再描画で操作状態を継続してはならない（MUST NOT）。
- **PSRC-SAFE-APP-003:** タッチイベント消失を想定し、複数指入力や誤タップで相反命令を同時送信してはならない（MUST NOT）。
- **PSRC-SAFE-APP-004:** アプリ再読込み後は、状態不明かつ操作不能として開始しなければならない（MUST）。ESP32 から現在の接続またはセッションに対する有効かつ最新のテレメトリーを受信するまで、操作を許可してはならず（MUST NOT）、ARM、DISARM、STOP、EMERGENCY_STOP のいずれかを実機の確定状態として推測表示してはならない（MUST NOT）。UI 内部の以前の状態を復元して実機状態として使用してはならず（MUST NOT）、ESP32 側の最新テレメトリーを状態の正本としなければならない（MUST）。
- **PSRC-SAFE-APP-005:** UI 表示だけで実機状態を推測せず、ESP32 テレメトリーを正本としなければならない（MUST）。
- **PSRC-SAFE-APP-006:** 接続状態不明または UI と ESP32 の ARM 状態不一致時は操作不能として危険側操作を許可してはならない（MUST NOT）。

## 16. テレメトリー要件

- **PSRC-SAFE-TEL-001:** ESP32 は ARM/DISARM、STOP/EMERGENCY_STOP、DRIVE/NEUTRAL/PTO の実状態を送らなければならない（MUST）。
- **PSRC-SAFE-TEL-002:** 接続・heartbeat 状態、速度指令、速度上限、左右出力候補値、encoder 状態候補値、watchdog 停止理由、最終受理 command sequence、エラーまたは拒否理由を扱える設計でなければならない（MUST）。
- **PSRC-SAFE-TEL-003:** 初期片側試験で未使用の右側値を、存在するように偽装してはならない（MUST NOT）。
- **PSRC-SAFE-TEL-004:** テレメトリー欠落や古さを正常状態として表示してはならない（MUST NOT）。

## 17. ログ要件

記録候補は `command_received`、`command_accepted`、`command_rejected`、`state_changed`、`arm`、`disarm`、`stop`、`emergency_stop`、`watchdog_stop`、`connection_lost`、`connection_restored`、`telemetry_sample`、`configuration_loaded`、`configuration_rejected`、`firmware_boot` とする。

- **PSRC-SAFE-LOG-001:** ログ形式をバージョン管理しなければならない（MUST）。
- **PSRC-SAFE-LOG-002:** 正確な農地座標、Wi-Fi パスワード、秘密情報を標準ログへ保存してはならない（MUST NOT）。
- **PSRC-SAFE-LOG-003:** ログ失敗によって安全停止処理を遅らせてはならない（MUST NOT）。
- **PSRC-SAFE-LOG-004:** 時刻が不正確でも sequence による順序確認を可能にすべきである（SHOULD）。
- **PSRC-SAFE-LOG-005:** ログ欠落を安全動作成功の証明として扱ってはならない（MUST NOT）。

## 18. 設定要件

設定候補は watchdog timeout、maximum PWM、speed limit、motor direction inversion、encoder counts、internal/external reduction ratio、pin assignment、one-side/dual-side test profile、PTO enabled/disabled とする。

- **PSRC-SAFE-CONFIG-001:** 機種依存値をコードへ分散させず、設定に version を持たせ、範囲検証しなければならない（MUST）。
- **PSRC-SAFE-CONFIG-002:** 不明な設定 version、読込み失敗、不正値では実機出力を有効にしてはならない（MUST NOT）。
- **PSRC-SAFE-CONFIG-003:** Wi-Fi パスワード等の秘密設定を Git へ保存してはならない（MUST NOT）。
- **PSRC-SAFE-CONFIG-004:** サンプル設定に秘密情報や農地座標を含めてはならない（MUST NOT）。

## 19. 仮想ローバー先行要件

- **PSRC-SAFE-SIM-001:** 仮想ローバーと ESP32 は同じ通信契約を使用しなければならない（MUST）。
- **PSRC-SAFE-SIM-002:** ARM、DISARM、STOP、EMERGENCY_STOP、通信断停止、期限切れ・重複命令拒否、DRIVE/PTO 排他、片側駆動状態を再現しなければならない（MUST）。
- **PSRC-SAFE-SIM-003:** 将来の左右2モーター状態へ拡張可能であるべきである（SHOULD）。
- **PSRC-SAFE-SIM-004:** 仮想試験成功だけで実機安全を保証してはならず、通過するまで実モーターを接続してはならない（MUST NOT）。

## 20. 実機出力解放条件

- **PSRC-SAFE-HWGATE-001:** 仮想ローバー基本操作、通信断停止、期限切れ・重複拒否、起動時 DISARM、再接続後の自動非始動、ソフトウェア非常停止の各試験が PASS しなければならない（MUST）。
- **PSRC-SAFE-HWGATE-002:** 物理非常停止回路の単独確認を完了しなければならない（MUST）。
- **PSRC-SAFE-HWGATE-003:** 車体を浮かせるか駆動部が地面に接触しない、低速度上限、モーター1基・MD10C 1枚の片側駆動条件で開始しなければならない（MUST）。
- **PSRC-SAFE-HWGATE-004:** 操作者は物理非常停止へ即時アクセスできなければならない（MUST）。
- **PSRC-SAFE-HWGATE-005:** 水、泥、実田んぼから離れた乾いた試験環境で行わなければならない（MUST）。
- **PSRC-SAFE-HWGATE-006:** 条件未達時は実機出力を無効のまま維持しなければならない（MUST）。

## 21. 異常時の基本方針

- **PSRC-SAFE-FAULT-001:** 未知、矛盾、欠落、期限切れ、通信断、例外、設定失敗では安全側へ移行しなければならない（MUST）。
- **PSRC-SAFE-FAULT-002:** 不明状態で出力をゼロ以外に保持してはならない（MUST NOT）。
- **PSRC-SAFE-FAULT-003:** タスク停止や通信処理停止時にも watchdog が成立しなければならない（MUST）。
- **PSRC-SAFE-FAULT-004:** エラー表示より出力停止を優先しなければならない（MUST）。
- **PSRC-SAFE-FAULT-005:** 復旧時に自動始動してはならない（MUST NOT）。

「安全側」の具体的状態遷移は、次工程の `STATE_MACHINE.md` で定義する。

## 22. 検証方針

1. 文書レビュー
2. 状態機械レビュー
3. protocol test vectors
4. 仮想ローバー試験
5. 通信断試験
6. 出力無効の ESP32 試験
7. オシロスコープまたはテスター等による出力候補値確認
8. モーター未接続の MD10C 制御確認
9. 駆動部を浮かせた片側モーター試験
10. 乾いた地面での低速試験

水、泥、実田んぼ試験は、この制御 MVP の初期検証と分離する。

## 23. 未確定事項

現時点で、通信方式、メッセージデータ形式、PWA フレームワーク、ESP32 開発環境、watchdog 最終値、最大 PWM、方向反転待機時間、加速度制限、エンコーダー異常判定、STOP 後の最終状態、非常停止解除手順の詳細、物理非常停止回路の最終配線は未確定である。

- **PSRC-SAFE-OPEN-001:** 未確定の技術選定を安全原則として固定してはならない（MUST NOT）。
- **PSRC-SAFE-OPEN-002:** 技術選定後も、本書の固定安全原則を弱めてはならない（MUST NOT）。

## 24. 次の承認対象

次の1作業は、次の文書を作成して安全状態と遷移を定義することである。

```text
software/rover_control/safety/STATE_MACHINE.md
```

本作業では `STATE_MACHINE.md` を作成しない。
