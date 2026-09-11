# Paddy Swarm FAILURE_LEDGER

GitHub上の [FAILURE_LEDGER.jsonl](FAILURE_LEDGER.jsonl) を失敗台帳の正本とします。
1行は1 failure recordです。[FAILURE_LEDGER.md](FAILURE_LEDGER.md) は自動生成ビューで、
COUNTや進捗を手入力しません。今回の成果物はローカルの新規ファイルであり、commit/pushは
実施していません。GitHubに記録済みとは扱わず、公開操作は別途明示された作業で行います。

全体台帳が既存構成に見当たらなかったため、部品別CAD・authority laneから独立した
ルート直下の新規laneを選びました。既存ファイルへの統合は行いません。
[project index](../CHATGPT_PROJECT_INDEX.md)、[agent contract](../AGENTS.md)、
[safety boundary](../LONEWOLF_FANG_SAFETY_BOUNDARY.md) のauthorityと安全境界を維持します。
この台帳は既存authorityやphysical validation statusを昇格するものではありません。

## 正本と補助記録

- [JSONL](FAILURE_LEDGER.jsonl): 正式IDの個別レコード。全COUNTの唯一の算出元。
- [schema](FAILURE_LEDGER_SCHEMA.md): フィールド、型、検証条件。
- [initial owner statement](INITIAL_OWNER_STATEMENT.md): 既存50件の初期化根拠。
- [unmapped JSON](KNOWN_UNMAPPED_FAILURES.json): 未対応候補群と既知の除外例の補助正本。
  正式failure recordではなく、COUNTEDを禁止します。
- [unmapped view](KNOWN_UNMAPPED_FAILURES.md): 補助JSONから生成。OBS番号は受付参照IDです。

## COUNTとID

COUNTは `classification == PHYSICAL_FAIL` かつ `count_status == COUNTED` の行の合計です。
ID最大値、行数、Markdown、補助候補数、official_count_memberの単純合計からは計算しません。
official_count_memberはこの条件との整合を検証するbooleanであり、独立した加算指示ではありません。
HOLD、ID_MAPPING_PENDING、DUPLICATE、CAD_FAIL、PREFLIGHT_FAIL、REJECTED_BEFORE_BUILD、
SUPERSEDED_UNVALIDATED、TEST_NOT_PERFORMEDは加算しません。

発行済みF-IDは変更・再利用・番号詰め・削除しません。将来F-0032が重複と分かった場合も
そのIDを保持し、count_status=NOT_COUNTED、official_count_member=false、
duplicate_of=F-0018として理由と証拠をnotes/evidenceに記録します。後続IDは維持します。
最新IDとCOUNTは一致しなくて構いません。既存50件を訂正する判断も今回のscope外です。

初期50行は新規発見ではなく既存公式COUNTの移行です。F-0001〜F-0046は個別placeholder、
F-0047は提供された事実のみ、F-0048〜F-0050はRECONSTRUCTION_PENDINGです。
未知のdate/specimen等はnullで、旧記録に新規FAILの資格確認を捏造しません。
legacyの資格例外はF-0001〜F-0050に固定し、後日の新規IDに流用できません。
詳細復元では同じ行を補完し、出典と訂正理由を残します。行の追加で再加算しません。

## 新規FAILの受付と判断

まず補助JSONにHOLDまたはID_MAPPING_PENDINGで記録します。正式IDを仮発行しません。
新規COUNTED前に以下を証拠・記録で確認し、qualificationの各項目を記録します。

1. 実物が存在するか。
2. 実際に物理試験・組立・使用が行われたか。
3. 期待結果が定義されていたか。
4. 実際結果が期待を満たさなかったか。
5. 過去failureとの重複ではないか。
6. 同一試験を恣意的に複数failureへ分割していないか。
7. 証拠または記録が存在するか。

1 testは自動的に1 failureでも複数failureでもありません。1回の物理試験で複数現象が
起きても、独立したfailure unitの証拠がなければ複数COUNTへ分割しません。
別個のspecimenや独立したfailure mechanismが明確な場合は個別record化できます。
判断不能ならHOLD。既存50件との重複確認ができなければID_MAPPING_PENDINGです。
新規IDは過去の発行履歴を確認して次の未使用番号を使います。COUNTから採番しません。
補助群が正式記録へ対応したら、補助側をNOT_COUNTEDとして対応IDと判断根拠をnotesに残し、
同じ観測を二重登録しません。補助記録自体は履歴として保全します。

validatorは記述の整合性を検証するだけで、証拠の真偽・実際の独立性・承認を自動判断しません。
qualificationをtrueにするために事実を推測してはいけません。
証拠のscope、specimen、geometry、試験条件を保持し、commit日や受付日をphysical test日にしません。
写真等はパス/URL参照で十分です。存在未確認の参照を作らず、証拠のコピーも強制しません。

## 失敗と改善案を分ける

台帳は「何が失敗したか」を記録します。改善設計・対策提案の保存先にはしません。
root causeに根拠がない場合はnull、root_cause_status=NOT_ESTABLISHEDとします。
F-0047のshaft shortenedは失敗後に報告された事実のみで、加工指示やPASS宣言ではありません。

## ローカル実行

Python 3.10以上、標準ライブラリのみ。repository rootから実行します。

```text
python -B failure_ledger/scripts/validate_failure_ledger.py --initial
python -B failure_ledger/scripts/generate_failure_ledger_md.py
python -B failure_ledger/scripts/validate_failure_ledger.py --initial
python -B failure_ledger/scripts/test_failure_ledger.py
```

正本を変更した後はgenerator → validatorの順です。初期作成時は生成ビューを用意した上で
上記順序も検証しました。generatorは不正データを拒否し、2つのMarkdownビューだけを書きます。
validatorはビュー全体のbyte一致も検証し、失敗時は非zero exitです。
--initialは今回の初期50件と初期分類を守る追加検証です。将来の正当な追加・訂正の通常検証では
このオプションを外します。COUNTの計算方法は変えず、手動COUNT値を追加しません。
GitHub Actionsは今回未導入。既存workflowの変更はHOLDで、接続するなら上記CLIを利用できます。

## 表示件数の意味

初期HOLDは1候補群・最大2件で、固有failure数は未確定です。
ID_MAPPING_PENDINGは3補助記録で、Candidate BはHOLD群と重複し得ます。両者を合計しません。
RECONSTRUCTION_PENDINGは厳密なstatusとして3件。別にLEGACY_DETAIL_NOT_RECONSTRUCTEDが46件あり、
どちらも既存COUNTEDの内数です。その他FAILを検索で発見しても自動登録・加算しません。
