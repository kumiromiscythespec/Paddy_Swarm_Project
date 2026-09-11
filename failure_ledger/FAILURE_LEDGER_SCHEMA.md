# FAILURE_LEDGER schema v1

UTF-8 JSONL、空行なし、1行1object。JSON key重複は禁止。
[validator](scripts/validate_failure_ledger.py) と [共通実装](scripts/ledger.py) が実行検証します。

| Field | Type / meaning |
|---|---|
| failure_id | 正規化されたF-0001形式。4桁以上、正の整数、追加の先頭0は禁止。永続ID |
| official_count_member | boolean。PHYSICAL_FAIL + COUNTEDと必ず一致。COUNTの入力値ではない |
| date | 実物の試験/失敗日 YYYY-MM-DD またはnull。有効な暦日 |
| date_status | CONFIRMED / UNKNOWN。nullならUNKNOWN |
| component | string / null |
| version | string / null。repository版から実物版を推測しない |
| specimen | string / null |
| test | string / null。実際に行われた試験・組立・使用 |
| expected_result | string / null。事前期待が不明ならnull |
| actual_result | string / null |
| classification | PHYSICAL_FAIL / DUPLICATE / CAD_FAIL / PREFLIGHT_FAIL / REJECTED_BEFORE_BUILD / SUPERSEDED_UNVALIDATED / TEST_NOT_PERFORMED |
| failure_mode | string / null |
| count_status | COUNTED / NOT_COUNTED / HOLD / ID_MAPPING_PENDING |
| root_cause | string / null。NOT_ESTABLISHEDならnull |
| root_cause_status | NOT_ESTABLISHED / OWNER_REPORTED / EVIDENCE_SUPPORTED |
| evidence | object array。下記参照 |
| duplicate_of | 既存F-ID / null。自己参照・循環・COUNTEDとの併用禁止 |
| legacy_record | boolean。trueは初期F-0001〜F-0050のみ |
| detail_status | LEGACY_DETAIL_NOT_RECONSTRUCTED / RECONSTRUCTION_PENDING / PARTIAL / DOCUMENTED |
| notes | string / null。scope、訂正理由、事後事実。推測は禁止 |
| qualification | 下記7 keyのobject。各値true / false / null |

qualification keys:

```text
physical_specimen_exists
physical_activity_performed
expected_result_defined
expectation_not_met
uniqueness_checked
independent_failure_unit
evidence_exists
```

初期ID以外のCOUNTEDには7項目全てtrue、legacy_record=false、DOCUMENTED、
非空evidence、未知でないcomponent/specimen/test/expected_result/actual_resultが必須です。
未知の実施日はdate=nullで保持可能です。初期IDの例外は既存COUNTの移行限定であり、
別の新規failureをそのIDに入れ替える許可ではありません。永続性はGit履歴のreviewでも確認します。
初期validatorは50という期待値と照合しますが、表示COUNTは常に行の条件から計算します。

## Evidence object

各objectはtype、reference、scopeを必須とします。reference/scopeは非空string。
typeはrepository_path / test_report / cad_path / photo / video / youtube_url /
git_commit / note_url / external_url / owner_statementです。
repository_path、cad_path、owner_statementはrepository root相対の既存ファイルを検証。
git_commitは40桁SHA形式のみ検証し、試験日の証拠とはしません。
URL型はHTTP(S)形式のみ検証。test_report/photo/videoはファイル名・パスまたはURL参照が可能です。
外部到達性や内容の真偽は自動検証しません。scopeに何を裏付けるかを限定して記録します。
初期owner_statementは [提供情報の保存](INITIAL_OWNER_STATEMENT.md) を指し、
個別の物理試験報告が復元されたとの主張ではありません。

## Unmapped observation schema

[補助JSON](KNOWN_UNMAPPED_FAILURES.json) はobjectのarrayで、正式レコードとは別です。
必須keyは observation_id (OBS-001形式・一意)、component、classification、count_status、
maximum_candidates (判明した正の整数上限 / 不明・非該当ならnull)、notes、source_paths (repository相対ファイルパス配列)。
classificationは上記分類にPHYSICAL_FAILURE_CONFIRMED_OR_REPORTEDを追加可能。
count_statusはCOUNTED禁止。failure_idを持たず、正式IDを消費しません。
maximum_candidatesは独立性を確定した数でもCOUNTへの重みでもありません。
除外例がoptions群の場合も受付群としてのみ扱い、個々の棄却案の数を推測しません。
