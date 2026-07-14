# Protocol v0 Test Vector Manifest Requirements

## 1. 目的と適用範囲

本書は、Protocol v0の38 concrete test vectorについて、file identity、integrityおよびcoverageを固定するmanifest contractを定める。manifestは正規vector fileのexact set、repository-relative path、raw byte SHA256、raw byte size、vector ID、source scenario、profileおよびaccepted COMMAND sequence更新flagを列挙し、offline validation前のpreflightを可能にする。

manifestはvector semanticのsource of truthではない。vectorの意味、状態遷移および期待結果は、承認済みの安全要件、状態機械、validation order、CASE_CATALOG、FIELD_MODELおよびvector schemaに従う。manifestはruntime state machine、simulator、security認証またはmotor outputを実行しない。

## 2. 規範source

manifestが固定する規範sourceは、Protocol v0 validation order、CASE_CATALOG、FIELD_MODEL、VALIDATION_LIMITSおよびDraft 2020-12 vector schemaである。各sourceはrepository-relative pathとraw byte SHA256の組で識別する。source hash mismatch時はmanifestまたはvector内容から値を推測せず、fail closedとする。

vector semanticの優先順位は既存文書が定める。manifest entryやvector自身からID-specific semantic ruleを生成し、それを根拠にvectorを自己承認してはならない。

## 3. manifest pathとidentity

manifestの正規pathは次のとおりとする。

```text
software/rover_control/protocol/v0/test_vectors/manifest/test-vector-manifest.json
```

`manifest_version`は整数`1`、`protocol_version`は文字列`v0`とする。manifest自身のSHA256をmanifest内部へ格納してはならない。generated timestamp、absolute path、machine nameまたはusernameをidentityとして追加してはならない。

## 4. root object model

rootはobjectであり、propertyは次の8件だけをこの順序で持つ。

```text
manifest_version
protocol_version
vector_schema
source_documents
vector_directory
vector_count
source_scenario_count
vectors
```

固定値は`manifest_version=1`、`protocol_version=v0`、`vector_directory=software/rover_control/protocol/v0/test_vectors/vectors`、`vector_count=38`、`source_scenario_count=36`とする。unknown root property、duplicate key、`null`および型変換による補完を禁止する。

## 5. vector_schemaとsource_documents

`vector_schema`は`path`、`sha256`だけをこの順序で持つclosed objectである。pathは`software/rover_control/protocol/v0/test_vectors/schema/test-vector.schema.json`、SHA256は`ea021f20390962246aad09a2334dfb898588442333c679cc2911fb9895dbc013`とする。

`source_documents`は次の4 propertyだけをこの順序で持つ。

```text
validation_order
case_catalog
field_model
validation_limits
```

各値は`path`、`sha256`だけをこの順序で持つclosed objectとする。pathおよびSHA256は実repository fileのraw bytesと一致しなければならない。unknown propertyを禁止する。

## 6. vector entry model

`vectors`は38 objectのarrayである。各entryは次の7 propertyだけをこの順序で持つ。

```text
vector_id
path
sha256
size_bytes
source_scenario
profile
accepted_command_sequence_updated
```

`vector_id`と`path`はstring、`sha256`は64文字のlowercase hexadecimal string、`size_bytes`はpositive integer、`source_scenario`は1～36のinteger、`accepted_command_sequence_updated`はbooleanとする。`profile`は`one_side_test`または`drive_pto_split_fixture`だけを許可する。entryはclosed objectであり、unknown propertyを禁止する。

## 7. orderingとcanonicalization

array orderはfilesystem、localeまたはZIP entry orderに依存せず、次のexact ID順とする。

```text
PV0-VAL-001A
PV0-VAL-001B
PV0-VAL-002
PV0-VAL-003
PV0-VAL-004
PV0-VAL-005
PV0-VAL-006
PV0-VAL-007
PV0-VAL-008
PV0-VAL-009
PV0-VAL-010
PV0-VAL-011
PV0-VAL-012
PV0-VAL-013
PV0-VAL-014L
PV0-VAL-014R
PV0-VAL-015
PV0-VAL-016
PV0-VAL-017
PV0-VAL-018
PV0-VAL-019
PV0-VAL-020
PV0-VAL-021
PV0-VAL-022
PV0-VAL-023
PV0-VAL-024
PV0-VAL-025
PV0-VAL-026
PV0-VAL-027
PV0-VAL-028
PV0-VAL-029
PV0-VAL-030
PV0-VAL-031
PV0-VAL-032
PV0-VAL-033
PV0-VAL-034
PV0-VAL-035
PV0-VAL-036
```

manifestの正規表現はUTF-8、BOMなし、LF、2-space indentation、末尾LFちょうど1件のStrict JSONである。key並びは本書のpresentation orderに従う。canonicalizationのためにvector bytes、Unicodeまたは改行を変換してはならない。

## 8. path・SHA256・size規則

validationはpath containmentを最初に確認する。vector pathは`software/rover_control/protocol/v0/test_vectors/vectors/<vector-id>.json`形式のrepository-relative pathとし、canonical解決後もvector directory直下に存在しなければならない。absolute path、URL、backslash、`.`または`..` segment、duplicate path、directory外pathを禁止する。

regular fileだけを許可し、symlinkは追跡せず拒否する。SHA256はrepository fileのraw bytesから計算し、sizeは同じraw bytesのbyte数とする。manifest entryやparsed JSONからhashまたはsizeを再構成してはならない。vector IDとfilename stemは一致しなければならない。

## 9. coverage invariants

次のcoverageをすべて満たさなければならない。

```text
vector_count=38
unique_vector_id_count=38
unique_path_count=38
source_scenario_count=36
scenario_1_entry_count=2
scenario_14_entry_count=2
all_other_scenario_entry_count=1
profile_one_side_test_count=36
profile_drive_pto_split_fixture_count=2
accepted_sequence_updated_true_count=8
accepted_sequence_updated_false_count=30
```

split profileのexact setは`PV0-VAL-001B`と`PV0-VAL-018`である。accepted sequence更新trueのexact setは`PV0-VAL-001A`、`PV0-VAL-001B`、`PV0-VAL-002`、`PV0-VAL-017`、`PV0-VAL-018`、`PV0-VAL-025`、`PV0-VAL-032`、`PV0-VAL-034`である。scenario 1と14だけが各2 entryであり、その他scenarioは各1 entryとする。

## 10. manifest validation sequence

validation sequenceは次の順序とする。

1. isolated offline runtimeとtoolchainを確認する。
2. manifest path containment、regular fileおよびsymlink禁止を確認する。
3. raw size、BOM、CR、LF、line limitsおよびUTF-8を確認する。
4. Strict JSON、duplicate key、root objectおよびclosed property setを確認する。
5. manifest identity、property orderおよび固定source path/hashを確認する。
6. vector entryの型、order、ID/path一意性およびpath containmentを確認する。
7. 各vectorの存在、regular file、symlink禁止、raw SHA256およびraw sizeを確認する。
8. scenario、profileおよびaccepted sequence coverageを確認する。
9. manifest preflight成功後だけvector Layer 0へ進む。

manifestを先に検証せずvector arrayを部分的に実行してはならない。

## 11. failure handling

manifest欠落、parse error、unknown property、duplicate key、source hash mismatch、schema hash mismatch、vector欠落、vector hash/size mismatch、duplicate ID/path、order mismatchまたはcoverage mismatchはfail closedとする。corrupt manifest、schema mismatchおよびsource document mismatchはglobal fatalであり、vector validationへ進まない。

validatorは不正entryをskip、補完、truncateまたは自動修復してPASSにしてはならない。runtime exceptionをvalidation failureへ安全に分類できない場合はinternal errorとし、PASSまたはwarningへ変換しない。failure時もrepository fileを変更しない。

## 12. 非目標と次の承認対象

manifestはJSON Schema、CASE_CATALOG、semantic rule table、runtime state machine、simulator、security layerまたは実機安全承認の代替ではない。今回はmanifest JSON Schema、loader実装、validator実装、CLI、package configuration、test runner、fixture、CIおよびhardware interfaceを作成しない。

次の承認対象は、manifest format、offline loader/validator design、manifest schema要否、Python実装pathとmodule構成、version-controlled case rule table形式、diagnostic/exit code contract、および実装・test fixture作成である。
