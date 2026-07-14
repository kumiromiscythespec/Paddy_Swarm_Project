# Paddy Swarm Rover Control Protocol v0 Test Vector Validation Limits

Status: Draft limits contract / Layer 0 resource limits / No loader implementation yet / No schema file yet / No vector files yet / Simulator-first / Real motor output not approved

## 1. 文書の目的と状態

本文書はStrict JSON test vector用Layer 0制限である。wire protocol message size、JSON Schema、loader実装、runtime watchdog値の決定文書ではない。CASE_CATALOG/FIELD_MODELの意味を変更せず、実機モーター試験を承認しない。

## 2. 参照文書と優先順位

- field model: `software/rover_control/protocol/v0/test_vectors/FIELD_MODEL.md`; SHA256 `0e9a694b5654c129a953b2405f628a2a12f79b6ed9bfacfa570d6ee5dd3cc724`
- JSON schema decision: `software/rover_control/protocol/v0/test_vectors/JSON_SCHEMA_DECISION.md`; SHA256 `f387ab5db14d7718c95a19d448af087683199b8244e4cb4f83e561e1040e70a4`
- encoding decision: `software/rover_control/protocol/v0/test_vectors/ENCODING_DECISION.md`; SHA256 `0fa8d42b406f8751ca46a51246a58448e9d02f6c610f576a2d14b8ac5650a6bf`
- case catalog: `software/rover_control/protocol/v0/test_vectors/CASE_CATALOG.md`; SHA256 `4021e082b9085f0785b5e3967389e1b0ee7535e682d832f6f4696997e369f22d`
- protocol version `v0`; schema version `1`; vector count `38`

上位文書SHA256変更時は再レビューする。

## 3. Layer 0の責任範囲

Layer 0はschema前に、file existence/type/name/extension、path containment、symlink、raw size、UTF-8/BOM/line endings/trailing newline、Strict JSON syntax、duplicate key、number token、depth、object/array/node count、key/string length、resource limitを検査する。enum意味、state transition、catalog意味/source hash実照合、38 coverage、simulator、protocol acceptance、実機安全は扱わない。FAIL fileをLayer 1以降へ渡さない。

## 4. limit設計原則

fail-closedとし、超過時のtruncate、自動修復、型変換、Unicode正規化、改行変換、default補完、partial executionを禁止する。parser/resource errorをPASSにしない。同じbytesはPython/TypeScriptで同じ判定とし、count単位を明示する。raw byte limitとsemantic field limit、operational timeoutとparser limitを分離する。

## 5. counting semantics

- File bytes: filesystemから読んだraw bytes。
- UTF-8 bytes: stringを正規化せずUTF-8 encodeしたbytes。
- Unicode scalar count: Unicode scalar valueは`U+0000`～`U+D7FF`および`U+E000`～`U+10FFFF`のcode pointである。`U+D800`～`U+DFFF`はscalar valueではない。Python `len(str)`とJavaScript UTF-16 code unitsを同一視せず、TypeScriptもcode point iteration相当を使う。
- Surrogate pair: JSON escape展開後の正しいhigh-surrogate + low-surrogate pair（例: `\uD83D\uDE00`）は対応するsupplementary Unicode scalar value 1件として数える。単独high/low surrogate、highの後がlow以外、low先行を拒否し、無視・0文字化・2 scalar扱いを禁止する。
- Nesting depth: root object=1、nested object/arrayごとに+1、scalarは増やさない。
- JSON node: object、array、string、integer、booleanを各1。keyはnodeに含めず別管理。nullは禁止。
- Object members: 1 object内member数。duplicateは計数前または同時に拒否。
- Array elements: 1 array内element数。
- Line count: LF区切りlogical lines。末尾必須LFの後の空行を数えない。
- Line byte length: LFを除く1 logical lineのraw UTF-8 bytes。

## 6. file・path・extension limits

```text
maximum_file_size_bytes=65536
maximum_line_count=2048
maximum_line_bytes=4096
required_extension=.json
regular_file_required=true
symlink_allowed=false
```

承認済み`vectors/`配下かつcanonical解決後も同配下だけを許可する。repository外、absolute、drive-qualified、UNC、backslash、`.`/`..` segment、NULを禁止する。filenameは`<vector-id>.json`、case-insensitive衝突を禁止する。stem/内部ID一致はLayer 2。sizeはparse前に検査し、64 KiB超を部分実行しない。

## 7. byte encoding・BOM・改行

```text
text_encoding=UTF-8
BOM_allowed=false
repository_line_ending=LF
CR_allowed=false
trailing_newline_required=true
trailing_newline_count=1
empty_file_allowed=false
whitespace_only_file_allowed=false
```

UTF-16/32、Shift_JIS、invalid/overlong UTF-8、不正surrogate encoding、CRLF/bare CR、末尾LFなし/複数、trailing whitespaceを拒否する。JSON string escapeの`\r`/`\n`とfile改行を混同しない。

UTF-8 decode直後のraw decoded source text検査は、raw NUL、実際の禁止control、file-level禁止文字、raw bidi control、raw zero-width文字を対象とする。一方、escapeされた禁止文字はraw source検査だけでは判定できないため、Strict JSON tokenizationとescape展開後に全object key/string valueを別途検査する。

## 8. JSON構文・number token limits

Strict JSONだけを許可し、comments、trailing comma、single quote、unquoted key、duplicate/multiple roots、root array/scalar、NaN、Infinity、-Infinity、hex/octal/binary、fraction/decimal point、exponent、leading plus、複数桁leading zero、negative zero、negative integerを禁止する。

```text
minimum_integer_value=0
maximum_integer_value=9007199254740991
maximum_integer_decimal_digits=16
```

JSON整数tokenとして検査し、floatからintegerへ変換しない。

## 9. nesting・node・object・array limits

```text
maximum_nesting_depth=16
maximum_total_json_nodes=512
maximum_object_members=32
maximum_array_elements=32
maximum_root_members=11
notes.tags maximum_array_elements=16
```

rootは承認済み11 group候補だけで実memberは11以下。message 22 fieldsを許容するためobject上限32とする。超過containerを部分実行せず、duplicateを上限内でも許可せず、depth error/recursion exceptionをPASSにしない。

## 10. key・stringの共通limits

```text
maximum_key_unicode_scalars=64
maximum_key_utf8_bytes=128
maximum_generic_string_unicode_scalars=1024
maximum_generic_string_utf8_bytes=4096
```

field-specific limitが小さければそちらを適用する。全decoded key/string valueについて、NUL、単独high/low surrogate、Unicode control、identifier/path/enum内のbidi control・zero-width、IDのleading/trailing whitespace、empty IDを拒否し、Unicode normalizationで同一化しない。escape形式で記載されていても許可しない。

Unicode scalar countとUTF-8 byte countはescape展開とsurrogate検証後のscalar sequenceから計算する。正しいpairは1 scalarとしてUTF-8 encodeする。単独surrogateはU+FFFDへ置換または無視してbyte計算せず、その前または同時に`FORBIDDEN_STRING_CHARACTER`で拒否する。禁止文字は同code、key長超過は`KEY_LENGTH_EXCEEDED`、string長超過は`STRING_LENGTH_EXCEEDED`とする。

## 11. identity・source field limits

| Field | Scalar max | UTF-8 byte max | Additional rule |
| --- | ---: | ---: | --- |
| identity.vector_id | 64 | 64 | ASCII; approved 38 IDs |
| identity.title | 120 | 512 | whitespace-only forbidden |
| source path fields | 256 | 256 | ASCII repository-relative |
| SHA256 fields | 64 | 64 | lowercase ASCII hex |
| profile | 32 | 32 | approved 2 values |
| protocol_version | 8 | 8 | const `v0` |
| schema_version | integer | — | const 1 |

固定値照合はLayer 1/2、長さ・byte・禁止文字・traversalはLayer 0で行う。

## 12. fixture・message field limits

rover_boot_id、session_id、controller_owner_id、active_operation_id、message_id、operation_id、cached result message_idは最大64 Unicode scalars/64 UTF-8 bytesとし、pattern候補`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`を用いる。enum fieldは最大64 scalars/64 bytes。candidate intent、message/command type、state、event、reasonの集合照合はLayer 1。direction/sender role等もgeneric string limit以下とする。

## 13. time・sequence・integer field limits

| Field category | Minimum | Maximum |
| --- | ---: | ---: |
| schema_version | 1 | 1 |
| validation_chapter | 17 | 17 |
| source_scenario | 1 | 36 |
| terminal_step_number | 1 | 23 |
| sequence fields | 0 | 4294967295 |
| monotonic_time_ms | 0 | 9007199254740991 |
| freshness_reference_ms | 0 | 9007199254740991 |
| freshness_age_ms | 0 | 86400000 |
| ttl_ms | 0 | 86400000 |
| watchdog_remaining_ms | 0 | 86400000 |
| advance_ms | 0 | 86400000 |

24h上限はfixture input limitでruntime TTL/watchdog値ではない。advance/watchdog関係はsemantic validatorが検査する。wraparoundは未決定。超過をstringへ変換せずnegativeを拒否する。

## 14. notes・diagnostic field limits

| Field | Scalar max | UTF-8 byte max | Additional rule |
| --- | ---: | ---: | --- |
| notes.summary | 500 | 2048 | whitespace-only forbidden |
| notes.tags item | 32 | 128 | unique; max 16 elements |
| diagnostic_code | 64 | 64 | ASCII identifier candidate |
| handling_code | 64 | 64 | ASCII identifier candidate |
| stop_reason | 64 | 64 | approved command/event |
| fault_reason | 64 | 64 | approved fault code |
| rejection_reason | 64 | 64 | official 18 reasons |

secret、個人情報、農地座標を禁止する。

## 15. duplicate key・parse failure・拒否動作

stage 8ではStrict JSON tokenizationとstring escapeの決定論的decodeを行う。不正escape syntaxは`JSON_PARSE_ERROR`とする。正しいsurrogate pairは1 scalarへdecodeする。単独surrogateをreplacement characterへ変換・削除せず、stage 11で拒否できる状態を保持する。parserが自動置換して不正状態を失う場合、その結果だけに依存しない。

duplicate keyはescape展開と正しいsurrogate pairのdecode後のkey値で比較し、表記だけ異なる同一keyを重複として拒否する。Unicode normalizationは行わない。単独surrogateを含むkeyはduplicate結果にかかわらず拒否する。duplicate diagnosticは`DUPLICATE_KEY`とし、禁止文字との競合時はloader stage順に従う。last/first-key-winsを禁止し、schemaに任せずparse hook/token parser相当で検出する。

partial object/fixtureを返して実行せず、resource exception、stack overflow、OOM、uncaught exceptionをPASSにしない。error時はsimulatorを起動せずreal motor gateを変更しない。最初のfatal errorでpipelineを停止し、追加診断を集めても再開しない。不正escape syntaxは`JSON_PARSE_ERROR`、syntactically読める単独surrogateは`FORBIDDEN_STRING_CHARACTER`、decoded key重複は`DUPLICATE_KEY`を用い、新diagnostic codeを追加しない。

## 16. loader diagnostic code

以下31件はLayer 0 diagnosticで、protocol rejection reason、state event、formal dispositionではない。

```text
FILE_NOT_FOUND
FILE_NOT_REGULAR
SYMLINK_FORBIDDEN
PATH_OUTSIDE_VECTOR_DIRECTORY
INVALID_FILE_EXTENSION
INVALID_VECTOR_FILENAME
FILE_TOO_LARGE
TOO_MANY_LINES
LINE_TOO_LONG
EMPTY_FILE
WHITESPACE_ONLY_FILE
INVALID_UTF8
BOM_FORBIDDEN
CR_FORBIDDEN
TRAILING_NEWLINE_REQUIRED
MULTIPLE_TRAILING_NEWLINES
TRAILING_WHITESPACE_FORBIDDEN
JSON_PARSE_ERROR
ROOT_OBJECT_REQUIRED
MULTIPLE_ROOT_VALUES
DUPLICATE_KEY
NESTING_DEPTH_EXCEEDED
TOTAL_NODE_COUNT_EXCEEDED
OBJECT_MEMBER_COUNT_EXCEEDED
ARRAY_ELEMENT_COUNT_EXCEEDED
KEY_LENGTH_EXCEEDED
STRING_LENGTH_EXCEEDED
FORBIDDEN_STRING_CHARACTER
FORBIDDEN_NUMBER_FORMAT
INTEGER_RANGE_EXCEEDED
RESOURCE_LIMIT_EXCEEDED
```

exact setを増減せず、COMMAND_RESULTへ送らない。複数errorの順序は次章のloader orderに従う。

## 17. cross-language conformance

Layer 0順序を次に固定する: (1) path containment、(2) file type/symlink、(3) extension/filename、(4) raw size、(5) raw byteのBOM/CR/trailing newline/line limits、(6) UTF-8 decode、(7) raw decoded source character checks、(8) Strict JSON tokenization and escape decoding、(9) duplicate key、(10) depth/node/container limits、(11) decoded key/string character and length checks、(12) number/integer range、(13) root object、(14) Layer 1 handoff。stage 7はraw source、stage 11はescape展開後valueを検査し、前段FAIL時は後段へ進まない。

Python/TypeScriptはraw bytes、LF lines、line bytes、UTF-8、Unicode scalars、valid surrogate pair count、literal/escaped supplementary character count、lone high/low surrogate rejection、escaped NUL/bidi/zero-width rejection、decoded UTF-8 bytes、duplicate、depth、nodes、members/elements、integer token/range、diagnostic code、first fatal errorを一致させる。JS UTF-16 `.length`、replacement character recovery、default duplicate処理、JSON.parse結果だけ、NaN/Infinity差へ依存しない。Python encoder errorをgeneric exceptionのまま扱わない。disagreementは`validation_result=FAIL`、`simulator_execution=false`、`review_required=true`とし多数決しない。

## 18. 未確定事項と次の承認対象

Python/TypeScript loader library、streaming parser、error report JSON、diagnostic message、runtime TTL/watchdog、sequence wraparound、manifest file count/directory bytes、conformance fixturesは未確定である。64 KiB、LF only、BOM/CR禁止、末尾LF1、depth16、nodes512、members32、elements32、root11、duplicate/null/float/negative拒否、safe integer、field limits、Unicode scalar範囲、単独surrogate拒否、raw/decoded検査分離、14-stage order、31 codesは未確定へ戻さない。

次工程候補は`software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json`である。FIELD_MODELをDraft 2020-12へ実装し、Layer 1対象、closed objects、conditionals、remote refなしを満たすschema本体だけを作成する。今回はschema directory/fileを作成しない。
