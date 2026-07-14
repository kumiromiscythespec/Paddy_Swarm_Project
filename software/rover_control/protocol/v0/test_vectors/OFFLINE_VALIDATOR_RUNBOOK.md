# Protocol v0 Offline Validator Runbook

## 1. 目的と適用範囲

このrunbookは、Protocol v0 test vectorに対するoffline validatorの再現可能な実行方法と、acceptance baselineによる確認方法を定める。対象はmanifest、Layer 0、JSON Schema、Layer 2 semantic rule、aggregate coverageであり、validatorは入力を変更しない。

## 2. 安全上の位置づけ

検証はoffline限定であり、networkまたはhardwareへ接続しない。物理ESTOPは独立した安全手段のままである。Phase 2がPASSしても実機投入許可または実機安全承認にはならない。

## 3. 前提artifact

実行前に、acceptance baselineの`critical_artifacts`に記録された10件について、repository-relative path、SHA256、sizeを実ファイルと照合する。vector schema、manifest、case rule table、要件文書、設計文書、Phase 1／2実装、Phase 1／2 testのいずれかが一致しない場合はFAILとして停止する。

## 4. offline toolchain

`<isolated-python>`はPython 3.11.0とjsonschema 4.26.0を備え、Draft 2020-12 validatorを利用できる固定toolchainを指す。`<toolchain-marker>`のSHA256は`f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16`でなければならない。isolated modeで実行し、network access、package変更、別環境への切替を行わない。

## 5. Phase 1の役割

Phase 1はmanifest global preflight、各vectorのLayer 0、JSON Schema validationまでを担当する。Layer 2 semantic ruleとaggregate coverageは判定しないため、Phase 1 reportの`full_validator_result=NOT_AVAILABLE`は正常なphase boundaryを示す。

## 6. Phase 2の役割

Phase 2はPhase 1の結果に加え、case rule table preflight、Layer 2 semantic validation、aggregate coverageを判定する。正式な最終判定にはPhase 2を使用する。

## 7. Phase 1実行手順

`<repository-root>`をcurrent directoryとして、次を実行する。

```text
<isolated-python> -I \
  software/rover_control/protocol/v0/test_vectors/offline_validator/phase1.py \
  --repository-root <repository-root> \
  --toolchain-marker <toolchain-marker> \
  --toolchain-marker-sha256 f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16 \
  --json-report <external-report-directory>/phase1-report.json \
  --text-report <external-report-directory>/phase1-report.txt
```

この例の`\`は論理的な行継続を示す。Windows cmdとPowerShellでは行継続記号が異なるため、使用するshellの構文に置き換える。

## 8. Phase 2実行手順

Phase 1の前提が成立している状態で、`<repository-root>`をcurrent directoryとして次を実行する。

```text
<isolated-python> -I \
  software/rover_control/protocol/v0/test_vectors/offline_validator/phase2.py \
  --repository-root <repository-root> \
  --toolchain-marker <toolchain-marker> \
  --toolchain-marker-sha256 f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16 \
  --json-report <external-report-directory>/phase2-report.json \
  --text-report <external-report-directory>/phase2-report.txt
```

Windows cmdとPowerShellでは行継続記号が異なる。各shellの構文へ置き換えても、引数、順序、値は維持する。

## 9. report出力規則

JSON reportとtext reportは必ず`<external-report-directory>`へ保存する。repository内のreport pathは拒否される。正式なpositive reportのSHA256はacceptance baselineの`positive_reports`と比較でき、同じ入力とtoolchainによる再実行で一致しなければならない。

## 10. 正常終了の確認

Phase 1はmanifest、Layer 0、schemaが全件PASSし、diagnosticが0であることを確認する。最終確認ではPhase 2のvector count、Layer 0 pass count、schema pass count、semantic pass countが各38、coverage resultがPASS、diagnostic countが0、exit codeが0であることを確認する。さらに4件のpositive report hashをacceptance baselineと照合する。

## 11. exit codeとdiagnostic

```text
0 = full offline validation PASS
2 = toolchain／manifest global preflight failure
3 = one or more Layer 0 failures
4 = schema artifact／vector schema failure
5 = rule table preflight／Layer 2 semantic failure
6 = aggregate coverage failure
7 = internal validator／report output failure
```

exit codeは小さい番号が常に優先という意味ではなく、pipelineで最も早く発生したfailure layerを表す。後続で検出したdiagnosticもreportへ保持し、削除または無視してPASS扱いしない。exit 0もhardware安全承認を意味しない。

## 12. failure時の対応

artifactまたはreportのhash不一致時に自動修正しない。validationを通す目的でvectorを変更してはならない。source documentとの矛盾を検出した場合はFAILとして停止し、入力、toolchain、diagnostic、reportを保全してowner reviewへ渡す。diagnosticを削除または無視して再判定してはならない。

## 13. repository保全規則

validator入力と既存repository fileは変更しない。report、調査用copy、検査出力はrepository外に置く。実行前後に対象artifactのSHA256を比較し、想定外の新規file、変更、削除がないことを確認する。network、hardware、package操作、Git write操作は行わない。

## 14. 非目標と次工程

このoffline validationは、実機試験、hardware統合、物理ESTOP、運用環境の安全承認を代替しない。runtime state machineの検証と実装判断は次の独立工程であり、このrunbookのPASSから自動的に承認されない。
