# Paddy Swarm Agent Contract

このファイルは、モデルや実行環境に依存しない project-wide canonical agent contract です。
Agent の作業方法を定めます。現在の設計寸法、最新版番号、engineering authority の宣言は保存しません。

## Mission

Paddy Swarm は、小規模・家族経営稲作の負担軽減を目的とした physical robotics project です。
実際の圃場、機械、電装、人間の安全、農業収入に影響するため、software-only project と同じ判断をしてはいけません。

## First Read

作業開始時に [CHATGPT_PROJECT_INDEX.md](CHATGPT_PROJECT_INDEX.md) を project authority entry point として確認してください。
Common Rover を扱う場合は [CURRENT_COMMON_ROVER_AUTHORITY.md](CURRENT_COMMON_ROVER_AUTHORITY.md) と、index が示す作業対象の current scoped authority を読んでください。
新しいフォルダ名、大きな version number、CAD 生成の成功だけで authority を昇格してはいけません。

変更前に対象ファイルの存在を確認し、既存ファイルは内容を読んでから編集してください。
適用される local instruction も確認し、無関係なファイルを読み込むことを作業開始の必須条件にしないでください。

## Instruction Architecture

| 文書 | Canonical な役割 |
|---|---|
| この AGENTS.md | How agents work: 共通の作業契約 |
| [CHATGPT_PROJECT_INDEX.md](CHATGPT_PROJECT_INDEX.md) | Where current engineering truth lives: authority navigation と precedence |
| Index から参照する authority documents | What is currently authoritative: 各 scope の設計・実測・validation status |
| [LONEWOLF_FANG_SAFETY_BOUNDARY.md](LONEWOLF_FANG_SAFETY_BOUNDARY.md) | Agent が自律的に越えてはいけない hard safety / irreversible-action boundary。作業開始時に読む |
| [Model operating profile](docs/agent/ASTRA_OPERATING_PROFILE.md) | 対象モデルを使用する場合の behavior tuning。Engineering authority ではない |
| [CODEX_RULES.md](CODEX_RULES.md) / [CLAUDE.md](CLAUDE.md) | Compatibility pointers。独立したルール・authority の保存先にしない |

AI instruction と engineering authority は別の体系です。Compatibility shim、model profile、skill、local override が project safety / authority boundary を黙って変更してはいけません。
実際の system instruction、tool permissions、sandbox、approval policy は実行環境が管理し、この契約から権限を付与・回避することはできません。
Task-specific user instruction は、runtime / system constraints の範囲内で作業範囲を限定できます。ユーザーの明示意図はその範囲内で一般的な skill の作業手順より優先し、既に与えられた承認を同一 scope で重ねて求めないでください。
ただし承認があっても、未取得の試験結果を事実として作ってはいけません。

`AGENTS.override.md` が存在する場合は読み、一時的・local な用途として扱ってください。
恒久的な project rule の保存先にはせず、存在しない override を既定動作として作成しないでください。
Override は共通契約と safety boundary への参照を維持し、例外の scope を明示する必要があります。

## Authority Boundary

以下は区別するための用語です。既存文書の scoped status 名や値を書き換える指示ではありません。

| 表記 | Agent が保持する意味・制限 |
|---|---|
| `PROPOSAL` | 提案。採用・承認・実証を意味しない |
| `DERIVED_ASSUMPTION` | 計算・推論による仮定。出典と導出を示し、実測として扱わない |
| `CAD_PASS` | 明示された CAD 検証 scope の合格のみ |
| `CONTRACT_PASS` | 明示された contract 検証 scope の合格のみ |
| `PHYSICAL_PASS` | 実際に試験した specimen / geometry / test scope の physical PASS のみ |
| `PHYSICAL_AUTHORITY` | 明示された scope で authoritative とされた physical evidence。全体承認ではない |
| `FIELD_PASS` | 明示された圃場・条件・試験 scope の field validation。別条件や deployment の自動承認ではない |
| `FAIL` | 実施した検証・試験の不合格。実施方法と scope を保持する |
| `HOLD` | 条件未解決・判断保留。PASS へ読み替えない |
| `NOT_TESTED` | 未試験。FAIL や PASS を意味しない |
| `NOT_APPROVED` | 未承認。検証結果の有無とは別に保持する |

- `CAD_PASS != PHYSICAL_PASS`、`CAD_PASS != PHYSICAL_AUTHORITY`。
- `PHYSICAL_PASS != FIELD_PASS`。新しい CAD は新しい authority を意味しません。
- 推測は measurement ではなく、blank result sheet は PASS ではありません。
- Physical result は実際の specimen、geometry、datum、test scope、条件、source trace と結び付けて扱ってください。
  別部品、変更した geometry、別の torque path、full assembly へ silent promotion してはいけません。
- 実測の範囲値と左右差を保持してください。導出した midpoint を未測定の absolute axis にしてはいけません。
- 部分試験を全体の fit / load / powered / waterproof / field validation に拡大してはいけません。
  `HOLD_NEAR_PASS` などの限定 status も元の意味を保持してください。

## Evidence Precedence

Canonical な順序は index の [Authority precedence rules](CHATGPT_PROJECT_INDEX.md#authority-precedence-rules) です。
次の要約はその適用のためのもので、新しい authority hierarchy を作りません。

1. Explicit, scoped physical PASS または direct physical measurement。
2. 同じ scope 内の current authority document。
3. Dated physical-authority lane とその source trace。
4. SHA-256 manifest / immutable validation evidence。
5. CAD / contract validation。
6. Older design candidate / trade study / historical design。

異なる scope の authority を勝手に merge しないでください。
Immutable evidence は記録の保全を意味し、CAD manifest が scoped physical truth に優先するわけではありません。
既に明示された supersession はその scope にだけ適用し、過去の証拠は保持してください。
ルール文書の更新自体は authority promotion ではありません。

## Autonomous Work

ユーザーの意図と task scope が明確で、安全かつ可逆な作業は不要な確認で停止せず完了まで進めてください。
Routine gap は repository evidence と既存 instruction から合理的に解決し、結果に影響する仮定を明示してください。
未取得の physical evidence があっても、それを必要としない読取り・分析・文書整理は進められます。

以下は owner review boundary です。実行条件と扱いは [safety boundary](LONEWOLF_FANG_SAFETY_BOUNDARY.md) に従い、推測で越えてはいけません。

- Authority promotion、証拠未提示の `PHYSICAL_PASS` declaration、`FIELD_PASS` declaration。
- Manufacturing release、purchasing release、deployment approval。
- Irreversible physical modification、powered hardware test、water / mud / field escalation。
- Safety-critical electrical change、crop / person / property risk。
- Destructive Git operation、physical outcome を実質的に変える未解決の conflict。

Boundary に達した場合は該当 action を止め、独立した安全な残作業は進めてください。
必要な owner decision を、証拠・未確定事項・提案が確認できる状態にして提示してください。
明示された承認は action / specimen / scope / 条件の範囲内でのみ有効で、別段階への包括承認にはなりません。

実質的な指示矛盾を発見した場合は `CONFLICT_FOUND` として file、heading、conflicting rule、proposed resolution を記録してください。
文体差や明示済みの historical supersession は矛盾に数えません。
Instruction が停止・確認・未完了の原因なら、その path、heading、該当 instruction と適用理由を示してください。
明示要件と自分の解釈を区別し、「ルールにより停止」だけで済ませないでください。

## Failure Handling

失敗を隠したり成功へ書き換えたりしないでください。
実際に製作・試験して失敗したもの、CAD / contract 検証で失敗したもの、製作前に棄却した案、未試験のものを区別してください。
`FAIL` は project evidence であり削除対象ではありません。失敗・棄却の理由と source trace を保持してください。
Correction / supersession は対象 scope と理由を明示し、元の結果を黙って置換しないでください。

## Git Discipline

作業開始時、変更前に以下の read-only command の出力を `START_BRANCH`、`START_HEAD`、`START_STATUS` として記録してください。

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Task scope 外のファイル・既存の変更・untracked file を保全してください。
Scope 内でも既存のユーザー変更を無関係に上書きしないでください。
明示的な作業対象となった既存 untracked file は、内容確認の上で scope 内の編集だけを行えます。
Untracked file を削除・移動してはいけません。Branch preservation を優先してください。
Owner の明示指示なしに `checkout`、`switch`、`reset`、`clean`、`stash`、`commit`、`push`、`merge`、`rebase`、branch 作成・変更、tag 作成、または `restore` 等による作業内容の破棄を行ってはいけません。
Task に禁止がある操作は実行せず、便利さを理由に branch や worktree を作らないでください。

Generated artifact の扱いは [GENERATED_ARTIFACT_POLICY.md](docs/repository/GENERATED_ARTIFACT_POLICY.md) に従ってください。
Generated / untracked は disposable を意味しません。Status をきれいにする目的で ignore を広げてはいけません。
CAD / STL / STEP / BOM / manifest / authority data / physical result の変更は、当該 task の明示 scope に含まれる場合だけ検討し、safety / authority boundary は別途維持してください。

## Verification

変更規模に応じた必要十分な verification を行ってください。
小さな documentation-only change のために、高負荷な full project test や CAD 再生成を無条件に実行しないでください。
Rule file の変更では、以下を確認してください。

- `git diff --check`。新規 untracked Markdown は通常の diff に出ないため、別途 whitespace と内容も確認する。
- 変更・作成した Markdown の broken links、invalid file references、存在する対象 heading。
- Contradictory instructions、duplicated canonical rules、compatibility shim が独立した authority を作っていないこと。
- AGENTS と safety boundary の整合、index の authority semantics を維持していること。
- 最終 `git status --short`、`git branch --show-current`、`git rev-parse HEAD` と開始状態との差分。

必要な checks が pass した後、新しい failure・変更・未解決の risk がなければ同じ test を繰り返さないでください。
実行していない check は実行済みと報告しないでください。

## Reporting

完了時には、変更内容・検証結果と、最低限次の項目を報告してください。

```text
START_BRANCH:
START_HEAD:
START_STATUS:
FINAL_BRANCH:
FINAL_HEAD:
FILES_CHANGED:
FILES_CREATED:
FILES_DELETED:
AUTHORITY_CHANGED:
PHYSICAL_STATUS_CHANGED:
GIT_OPERATION_STATUS:
UNRESOLVED_CONFLICTS:
```

Authority を変更していない場合は `AUTHORITY_CHANGED: NO` と明示してください。
Branch / HEAD の一致、既存の unrelated changes / untracked の保全、owner review が残る場合の具体的な action と理由を示してください。
Task 固有の報告形式が指定されている場合は、その形式と追加の status 項目も満たしてください。
