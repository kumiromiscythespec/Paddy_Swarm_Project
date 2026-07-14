# Paddy Swarm Rover Control Protocol v0 Test Vector Encoding Decision

Status: Draft decision / Strict JSON selected / No JSON files yet / No schema file yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書はmachine-readable test vectorの保存encodingを比較し、protocol v0ではStrict JSONを採用すると決定する。wire protocolのencodingは決定しない。実JSON、schema、vector、manifest、parser、runnerはまだ作成しない。

## 2. 参照文書と優先順位

- schema requirements: `software/rover_control/protocol/v0/test_vectors/SCHEMA_REQUIREMENTS.md`
- schema requirements SHA256: `32d4b47623bcf5fe730ff100469b6e8c87fa3d71f4044b572598c0bef34a6f55`
- case catalog: `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`
- case catalog SHA256: `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d`
- format document: `software/rover_control/protocol/v0/test_vectors/README.md`
- format document SHA256: `94200d499d8841845f1348bed222f58f9a0aa3d3900deb95afcd0246fd13fe02`
- protocol version: `v0`
- concrete vector count: 38

物理安全設計と既存安全・protocol文書を上位とし、本文書はCASE_CATALOGやSCHEMA_REQUIREMENTSの意味を変更しない。

## 3. encoding選定条件

型曖昧性、parser一貫性、duplicate key検出、unknown field拒否、Python・TypeScript取扱性、将来のC/C++ simulator連携、schema環境、Git差分・手動review、deterministic生成、hash再現性、comment依存、implicit conversion、anchors・tags・merge等の複雑性、非有限数・巨大数、parser攻撃面、offline利用を評価する。

## 4. 比較対象

比較対象はStrict JSON、YAML、TOML、JSON Lines、CBOR、Protocol Buffersの6件だけとする。JSON5をStrict JSONと混同しない。

## 5. 比較結果

| Candidate | Human review | Type ambiguity | Duplicate key risk | Schema ecosystem | Python/TS portability | Git diff | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Strict JSON | Good | Low with strict subset | Requires explicit detection | Strong | Strong | Good | SELECTED |
| YAML | Good superficially | High: implicit typing | Parser-dependent | Moderate | Parser differences | Good | REJECTED |
| TOML | Good for config | Moderate | Tool-dependent | More limited | Good | Good | REJECTED |
| JSON Lines | Moderate | Low | Requires explicit detection | JSON-compatible | Strong | Moderate | REJECTED |
| CBOR | Poor without tools | Low | Decoder-dependent | Available | Available | Poor | REJECTED |
| Protocol Buffers | Poor without tools | Low | Schema-driven | Strong | Generated toolchain | Poor | REJECTED |

Strict JSONはparser普及、Python/TypeScript互換、nested fixture、JSON Schema親和性、人間可読性、制限subsetの定義可能性から選択する。ただしduplicate keyは追加検査を必須とする。YAMLはimplicit typing、anchors/aliases/tags/merge、parser差、duplicate処理差により機能過多である。TOMLは深い条件付き構造とschema toolingで劣る。JSON Linesは1vector 1fileと相性が薄くnested review性が下がる。CBORは直接reviewとdiffに不向きである。Protocol Buffersは生成工程とtoolchainが初期fixtureには過剰である。

## 6. 最終決定

```text
selected_encoding=Strict JSON
file_extension=.json
storage_model=one vector per file
root_value=object
text_encoding=UTF-8
BOM=false
line_ending=LF
trailing_newline=true
```

候補ファイル名は`<vector-id>.json`（例: `PV0-VAL-001A.json`、`PV0-VAL-032.json`）とし、ファイル名と内部vector IDの完全一致を必須とする。今回は`.json`ファイルを作成しない。

## 7. 採用するstrict JSON profile

comments、trailing comma、single-quoted string、unquoted key、JSON5 extension、NaN、Infinity、-Infinity、hex/octal/binary number、duplicate key、multiple root values、root array/scalar、BOM、JSON Linesを禁止する。

rootは単一object、keyはdouble-quoted string、stringは正規JSON escapeだけ、booleanはnative `true`/`false`とする。array順序は意味を持ち、object key順序は意味を持たない。

## 8. ファイル単位と命名規則

1ファイルにつき1 concrete vectorとし、38 vectorsは将来38 JSON filesへ展開する。1 JSONへ38件をまとめず、one-line JSONを必須にせずpretty-printed multi-lineを用いる。file名はvector IDと一致させ、directory traversalを禁止し、case-insensitive filesystemでも衝突しないIDを使う。削除済みIDを別意味へ再利用しない。future manifestもJSON候補だが、構造は未確定で今回は作成しない。

## 9. 文字encoding・改行・末尾改行

UTF-8、BOMなし、repository保存時LF、末尾改行1件を必須とする。CRLF入力受理はloader方針で後日決定し、書き戻しはLFへ正規化する。Unicode normalizationや全角・半角を暗黙変換しない。hashは保存raw bytesを対象とする。

## 10. object・array・key規則

root objectとし、11 logical groupをroot直下候補とする。exact field名は次工程まで未確定である。object key順序はsemanticではないが、repositoryのcanonical presentation orderは11 logical group順とする。array順序はsemanticであり、set相当arrayはschemaで重複拒否を明記する。空object/arrayをabsence代用にせず、unknown keyを無条件に無視しない。

## 11. duplicate key・unknown field・parser規則

duplicate object keyは常にvalidation failureとし、last-key-winsとfirst-key-winsを禁止する。parserがduplicateを失う場合はobject生成前またはparse hookで検出する。Python default挙動やTypeScript `JSON.parse`結果だけでduplicate不存在を証明しない。duplicate検査後にschema validationする。parser errorを安全PASSにせず、error時はvectorを実行しない。unknown fieldは将来schemaで原則rejectとし、未承認JSONをsimulatorへ入力しない。parser libraryは未選定である。

## 12. absent・none・not applicable・null

JSON `null`はv0 vectorで禁止する。`ABSENT`はmember省略、`NONE`と`NOT_APPLICABLE`は各fieldの値集合で許可された明示値、`VALUE`は具体値とする。absentをNONEへ自動変換せず、NONEとNOT_APPLICABLEを同一視しない。空文字・空object・空arrayを代用しない。operation ID expectationの小文字`none`とpresence semanticsの大文字`NONE`を区別する。field別のpresenceと許可値は将来schemaで固定する。

## 13. boolean・enum・number・time・ID表現

- Boolean: native JSON booleanだけを許可し、文字列`"true"`/`"false"`を禁止する。
- Enum: case-sensitive JSON stringとし、暗黙case変換を禁止してCASE_CATALOG表記を維持する。
- ID: vector/message/boot/session/operation/profile/simulator fixture versionはJSON stringとし、numeric IDを禁止する。
- SHA256: lowercase hex JSON string、64文字、`0x`なしとする。
- Number: floating point、fraction、exponent、negativeを原則禁止し、JSON integer、最大`9007199254740991`、Python/TypeScriptで同一に扱える範囲とする。範囲外をstringへ暗黙変換しない。
- Time: TTL、monotonic time、advance、watchdog remaining、freshness ageは非負integer millisecondsとする。具体値は未決定である。
- Output expectation: `zero`、`forward`、`same`を維持し、PWM/電圧値へ変換しない。

## 14. canonical review・diff・hash規則

object key順序はsemanticではないが、表示はlogical group順を規範presentation orderとする。group内field順は次工程で決定する。pretty-printは2 spaces、tabとtrailing whitespaceを禁止し、末尾改行を1件とする。generatorは同じ入力から同じbytesを生成可能にする。SHA256は保存UTF-8 bytesから計算し、semantic比較とbyte hashを区別する。formatterの意味変更を禁止し、hash不一致を自動修正して試験継続しない。JSON canonicalization standardは今回は選択しない。

## 15. security・resource limit・simulator gate

real motor output enabledを常にfalseとする。duplicate key検査とschema validation前にvectorを実行せず、unknown fieldを無視して実行しない。file size、nesting depth、string length、array lengthの上限を必須とするが具体値は未確定である。再帰・memory exhaustionを考慮し、external URL、remote schema fetch、executable tag、custom object、code evaluationを禁止する。source pathはrepository外へ出さず、秘密情報、個人情報、正確な農地座標を禁止する。encoding決定だけでsecurity成立や実機試験承認としない。

## 16. 未確定事項と次の承認対象

exact field名、JSON Schema draft/version、schema ID、unknown field詳細、file/depth/string/array limit、integer field別最大値、manifest、loader library、duplicate検出実装、error report、canonicalization、CRLF入力方針は未確定である。安全上の固定条件を未確定へ戻さない。

次工程候補は`software/rover_control/protocol/v0/test_vectors/JSON_SCHEMA_DECISION.md`である。JSON Schema採否、draft/version、`$id`とrepository-relative参照、remote fetch禁止、unknown property、cross-field表現、Python/TypeScript validator互換性を決定する。今回は作成しない。
