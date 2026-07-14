# Protocol v0 Offline Loader and Validator Design

## 1. 目的と適用範囲

本書は、Protocol v0 test vector manifestと38 concrete vectorを完全offlineで読み込み、Layer 0、Draft 2020-12 JSON SchemaおよびLayer 2 semantic validationを決定論的に実行する将来validatorの設計contractを定める。今回は設計だけを対象とし、loader、parser、validator、CLI、test runnerまたはhardware interfaceを実装しない。

## 2. trust modelとfail-closed原則

manifest、vector、schemaおよびsource documentは入力であり、無条件には信用しない。path containment、regular file、symlink禁止、raw byte hashおよびsizeを独立に検証する。manifestやvector自身からsemantic ruleを生成して自己承認してはならない。

M0～M2のfailure時はvector validationへ進まない。Layer 0 failureのvectorはparse/schemaへ、Layer 1 failureのvectorはLayer 2へ渡さない。1 vectorのfailureがあっても、global fatalでない限り他vectorの安全検査を省略せず、検出済みdiagnosticを収集する。corrupt manifest、schema hash mismatchおよびsource document hash mismatchはglobal fatalとする。runtime exceptionをPASSへ変換せず、warningだけで安全failureを隠さない。

## 3. input artifacts

入力は、machine-readable manifest、manifestが固定する38 vector、Draft 2020-12 vector schema、VALIDATION_ORDER、CASE_CATALOG、FIELD_MODELおよびVALIDATION_LIMITSである。全pathはrepository-relativeとし、manifest directoryまたはvector directoryの境界をcanonical pathで検証する。

Layer 2は、承認済みsourceから別途作成・レビューされたversion-controlled case rule tableを入力とする。Markdownをruntimeに自然言語parserで解釈しない。

## 4. runtimeとoffline toolchain

validatorはisolated offline Python environmentで実行する設計とする。runtime version、JSON Schema implementation、dependency integrityおよびtoolchain markerをStage M0で確認する。network access、remote dependency取得、user site、global package fallbackおよび実行中のpackage変更を禁止する。

toolchain mismatchはglobal fatalであり、manifestやvectorを開く前にexit code 2で停止する。toolchain検査はrepository fileを変更しない。

## 5. validation pipeline概要

pipeline orderは次のexact順序とする。

```text
Stage M0: runtime/toolchain preflight
Stage M1: manifest raw/Strict JSON validation
Stage M2: manifest identity/path/hash/size/coverage validation
Layer 0: vector raw loader
Layer 1: Draft 2020-12 JSON Schema validation
Layer 2: semantic validation
Stage A0: aggregate coverage validation
Stage R0: deterministic report generation
```

各stageは明示的なPASS/FAILとdiagnosticを返し、後段は前段のhandoff条件を満たした入力だけを受け取る。Stage R0はvalidation結果を変えず、既に確定した結果を決定論的に表現する。

## 6. manifest preflight

Stage M1はmanifestのpath containment、regular file、symlink禁止、raw size、UTF-8、BOM、CR、LF、末尾改行、line limits、Strict JSON、duplicate keyおよびroot objectを検査する。Stage M2はroot property exact set/order、manifest identity、schema/source pathとhash、38 entry order、entry closed model、vector ID/path一意性、file existence、raw hash、raw sizeおよびcoverageを検査する。

manifest pathを無条件で信用せず、absolute path、URL、backslash、`.`/`..` segmentおよびvector directory外pathを拒否する。manifest preflightのいずれかがFAILした場合はLayer 0へ進まない。

## 7. Layer 0 raw loader

Layer 0は`VALIDATION_LIMITS.md`の次の14 stageをexact順序で実行する。

1. path containment
2. file type／symlink
3. extension／filename
4. raw size
5. raw BOM／CR／trailing newline／line limits
6. UTF-8 decode
7. raw decoded source character checks
8. strict JSON tokenization and escape decoding
9. duplicate key
10. container limits
11. decoded key／string forbidden-character and length
12. number／integer
13. root object
14. Layer 1 handoff

既存Layer 0 diagnostic codeは次の31件だけとし、名称を増減または再定義しない。

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

Layer 0成功時だけdecoded objectをLayer 1へ渡す。失敗時にpartial object、補完済みobjectまたは自動修復済みbytesを渡さない。

## 8. Layer 1 JSON Schema validation

Layer 1はmanifestが指定するrepository-relative schema pathを使用し、schema raw SHA256をmanifest値と比較する。schemaをStrict JSONとしてparseし、`Draft202012Validator.check_schema`相当のmeta-validationを行う。local `#/$defs/...` referenceだけを許可し、external/remote `$ref`およびnetwork fetchを禁止する。

固定schemaは`software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json`、SHA256は`ea021f20390962246aad09a2334dfb898588442333c679cc2911fb9895dbc013`である。各Layer 0 PASS vectorを個別にDraft 2020-12 validationし、errorはdeterministic JSON pointer順で出力する。schema failure vectorをLayer 2へ渡さない。

## 9. Layer 2 semantic validation

Layer 2はmanifestまたはvector内容だけをsource of truthとしてはならない。承認済みCASE_CATALOG、FIELD_MODEL、VALIDATION_ORDERから作成し、独立レビューされたversion-controlled case rule tableを使う。ID-specific rule tableをvector内容から自動生成してはならない。

最低限、filename stemとidentity、manifest ID/path/hash/size、source path/hash、scenario、profile、`real_motor_output_enabled=false`、initial state、stimulus、terminal step、formal disposition、defensive action、message handling、result source、rejection reason/event presence、accepted sequence policy、output、armed、operation、final state、safety latch、temporal group、sequence/freshness/TTL、boot/session/ownership、active operation、cached result、present flagおよびscenario-specific invariantを検査する。

Layer 2 failureはvector semantic failureとして記録し、runtime state machineやsimulatorを実行しない。

## 10. aggregate coverage validation

Stage A0はLayer 2後に次を検査する。

```text
vector file count=38
vector ID count=38
source scenario count=36
scenario 1 count=2
scenario 14 count=2
other scenario count=1
split profile IDs=PV0-VAL-001B,PV0-VAL-018
temporal IDs=PV0-VAL-004,PV0-VAL-023,PV0-VAL-024,PV0-VAL-030,PV0-VAL-031
CACHE_REPLAY IDs=PV0-VAL-009,PV0-VAL-019,PV0-VAL-026
NO_MESSAGE_ACTION IDs=PV0-VAL-023,PV0-VAL-024,PV0-VAL-030,PV0-VAL-031
accepted sequence true exact IDs=PV0-VAL-001A,PV0-VAL-001B,PV0-VAL-002,PV0-VAL-017,PV0-VAL-018,PV0-VAL-025,PV0-VAL-032,PV0-VAL-034
real motor output true count=0
duplicate ID count=0
missing ID count=0
unexpected ID count=0
filename mismatch count=0
```

aggregate failureは個別vector PASSを取り消すものではないが、overall resultをFAIL、exit codeを6とする。

## 11. diagnostic model

diagnostic familyは次の7件を分離する。

```text
TOOLCHAIN_*
MANIFEST_*
LAYER0_*
SCHEMA_*
SEMANTIC_*
COVERAGE_*
INTERNAL_*
```

manifest diagnosticの規範候補は`MANIFEST_NOT_FOUND`、`MANIFEST_NOT_REGULAR`、`MANIFEST_SYMLINK_FORBIDDEN`、`MANIFEST_PARSE_ERROR`、`MANIFEST_UNKNOWN_PROPERTY`、`MANIFEST_DUPLICATE_KEY`、`MANIFEST_SCHEMA_HASH_MISMATCH`、`MANIFEST_SOURCE_HASH_MISMATCH`、`MANIFEST_VECTOR_NOT_FOUND`、`MANIFEST_VECTOR_HASH_MISMATCH`、`MANIFEST_VECTOR_SIZE_MISMATCH`、`MANIFEST_VECTOR_ID_MISMATCH`、`MANIFEST_VECTOR_PATH_MISMATCH`、`MANIFEST_DUPLICATE_VECTOR_ID`、`MANIFEST_DUPLICATE_VECTOR_PATH`、`MANIFEST_ORDER_MISMATCH`、`MANIFEST_COVERAGE_MISMATCH`とする。

schema diagnosticの規範候補は`SCHEMA_NOT_FOUND`、`SCHEMA_HASH_MISMATCH`、`SCHEMA_PARSE_ERROR`、`SCHEMA_META_VALIDATION_FAILED`、`SCHEMA_EXTERNAL_REF_FORBIDDEN`、`SCHEMA_VALIDATION_FAILED`とする。

semantic diagnosticの規範候補は`SEMANTIC_FILENAME_ID_MISMATCH`、`SEMANTIC_SOURCE_MISMATCH`、`SEMANTIC_PROFILE_MISMATCH`、`SEMANTIC_SCENARIO_MISMATCH`、`SEMANTIC_SEQUENCE_POLICY_MISMATCH`、`SEMANTIC_STATE_MISMATCH`、`SEMANTIC_OUTPUT_MISMATCH`、`SEMANTIC_OPERATION_MISMATCH`、`SEMANTIC_LATCH_MISMATCH`、`SEMANTIC_RELATION_MISMATCH`、`SEMANTIC_CASE_RULE_MISMATCH`とする。今回はこれらを実装しない。

## 12. exit code設計

future contractは次の7 codeとする。

```text
0 = all validation PASS
2 = toolchain／manifest global preflight failure
3 = one or more Layer 0 failures
4 = schema meta-validationまたはvector schema failure
5 = Layer 2 semantic failure
6 = aggregate coverage failure
7 = internal validator error
```

global fatalは即時に対応codeを返す。vector validationで複数layerのfailureがある場合は、最も早いpipeline layerのnon-zero codeを返し、reportには検出済み全diagnosticを残す。internal errorをsemantic failureへ偽装しない。

## 13. deterministic report設計

text summaryは`overall_result`、`manifest_result`、`schema_result`、`vector_count`、`layer0_pass/fail`、`schema_pass/fail`、`semantic_pass/fail`、`coverage_result`、`diagnostic_count`および`exit_code`を含む。

machine-readable reportはStrict JSON、deterministic property order、exact vector ID順とする。diagnosticはlayer、vector ID、JSON pointer、diagnostic codeの順にsortする。timestampを任意metadataとして出力してもvalidation result hashには含めない。absolute path、username、machine name、secret、tokenまたは農地位置を出力せず、repository-relative pathを使用する。

## 14. security・safety境界

validatorは完全offlineであり、remote `$ref`を取得しない。symlinkを追跡せず、vector directory外を読まず、manifest pathを無条件で信用しない。hash mismatch時はfail closedとし、validation中にmanifest、schema、source documentまたはvectorを書き換えない。repositoryへ一時fileを置かない。

validatorはmotor outputを生成せず、simulatorを自動起動せず、serial、GPIO、CAN、BluetoothまたはWi-Fiへ接続しない。本validatorのPASSは実機安全承認を意味しない。Layer 3 runtime behaviorは範囲外であり、物理ESTOPはsoftware validatorから独立する。

## 15. 非目標と実装前承認事項

今回はmanifest JSON Schema、loader code、validator code、CLI、package configuration、unit/integration test、negative fixture、runtime simulator、hardware interface、CI workflowまたはGitHub Actionsを作成しない。

実装前に、manifest format、loader/validator design、manifest schema要否、Python module path、case rule table表現、diagnostic/exit code contractおよびtest fixture作成を個別に承認する。承認なしにruntime接続、hardware accessまたは実機出力へ範囲を広げない。
