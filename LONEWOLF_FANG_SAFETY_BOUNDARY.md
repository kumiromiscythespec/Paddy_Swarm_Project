# Paddy Swarm Hard Safety Boundary

この文書は [AGENTS.md](AGENTS.md) から参照する hard safety / irreversible-action boundary です。
新しい engineering authority、試験結果、release approval を宣言するものではありません。
現在の事実と未承認事項は [CHATGPT_PROJECT_INDEX.md](CHATGPT_PROJECT_INDEX.md) と各 scoped authority を確認してください。

## Principles

- 実田んぼは収入を生む production assets であり、使い捨ての実験環境ではありません。
- Human safety は日程・効率・完成を急ぐことより優先します。
- Physical evidence は CAD への確信より優先します。Evidence precedence と status の区別は [AGENTS.md / Authority Boundary](AGENTS.md#authority-boundary) と [Evidence Precedence](AGENTS.md#evidence-precedence) に従います。
- 失敗は evidence として保存し、隠蔽・削除・成功への書換えをしてはいけません。記録の扱いは [Failure Handling](AGENTS.md#failure-handling) に従います。

## Owner Review and Evidence

AGENTS の [Autonomous Work](AGENTS.md#autonomous-work) に挙げた owner review boundary を自律的に越えてはいけません。
実行には対象 action、specimen / geometry、test scope、条件に対応する owner の明示承認が必要です。
実行前提として必要な prerequisite evidence がある場合は、それも確認してください。
ただし、その action で取得する test result / measurement は実施後の evidence であり、事前承認の代替や自動的な開始前提ではありません。
その未取得を理由に循環的に開始不能としてはいけません。
同じ範囲について既に承認がある場合は再確認を繰り返さず、その範囲を維持してください。
承認のない次段階や、条件変更で承認範囲を超える action は止め、具体的な未確定事項を示してください。

Authority promotion は owner の判断です。Agent は evidence の整理と promotion proposal を作れますが、勝手に確定できません。
Owner authorization は measurement や test result の代わりにはなりません。
証拠未提示の `PHYSICAL_PASS` を作らず、`FIELD_PASS` の新規宣言には実際の scoped field evidence と owner review を必要とします。
提供済みの physical result を source trace と元の scope のまま記録・引用することと、別 scope への promotion を区別してください。
Blank result sheet、CAD / contract PASS、予想される fit は physical evidence を代替しません。

Manufacturing、purchasing、deployment の approval / release は自動化しません。
図面、部品リスト、候補品、試験計画、review 用文書の準備は、その task scope 内で進められますが、準備の完了を release と記載してはいけません。
Owner authorization なしに shaft cutting、穴あけ、切削、接着等の不可逆加工・実機変更へ進めてはいけません。
人、作物、農業収入、機械、財産に risk を加える action と、physical outcome を実質的に変える未解決の conflict は owner review に戻してください。
Destructive Git / repository action は [Git Discipline](AGENTS.md#git-discipline) に従い、実機側の承認を repository 破壊操作の承認と解釈してはいけません。

## Staged Validation

[CONTRIBUTING.md / 最重要方針](CONTRIBUTING.md#最重要方針) の進行順序を維持します。

机上 → dry（乾いた地面）→ water tank（水槽）→ soft soil（柔らかい土）→ shallow mud（浅泥）→ simulated wet environment（水あり模擬環境）→ small non-production area（小区画・非本番環境）→ field edge（実田んぼ端部）。

この順序は段階的な validation boundary であり、自動 PASS chain ではありません。
前段階の試験記録と未解決事項を確認し、次段階の環境、specimen、scope、危険源、停止条件を owner が review できる状態にしてください。
各段階の PASS は試験済みの範囲に限定し、次段階の実施や圃場への展開を自動承認しません。
試験手順の作成・レビューと、実際の試験開始を区別してください。

- CAD から powered hardware test へ自動的に進めてはいけません。
- Dry test から水・泥・圃場へ自動的に進めてはいけません。水槽から後続段階への移行も明示承認の対象です。
- Dry であっても powered operation は独立した境界です。無通電 fit の承認を動作試験の承認にしてはいけません。
- Field edge の validation は生産圃場全体への deployment approval ではありません。

## Electrical, Mechanical and Agricultural Safety

Battery、charging、motor、回転機械、blades、防水電装系を扱う際は、その作業に関わる安全条件を明示してください。
通電・蓄電エネルギー、短絡・発熱、停止・隔離方法、巻込み・切創、水の侵入、絶縁・保護の未確認事項を CAD の見た目だけで安全と判断してはいけません。
Safety-critical electrical change、充電・通電・回転試験、水中電装試験は、該当 action の owner review を経てください。
非通電の密閉試験片で得た seal PASS を、battery / electronics を組み込んだ full enclosure の waterproof / thermal / powered PASS にしてはいけません。

対象分野と人間向けの議論方針は [CONTRIBUTING.md / 安全に関わる変更](CONTRIBUTING.md#安全に関わる変更) に従います。
収穫・除草アーム、水管理、農薬・種子処理、飼料利用等の安全性も未検証のまま断定しないでください。
安全に関わる変更は実装前に議論できる提案へまとめてください。ただし一般的な Issue 投稿の案内は、agent に外部送信を許可する指示ではありません。
ユーザーから依頼されたルール整理や安全文書の修正自体を、実機変更や試験の開始と取り違えないでください。

## Privacy and Sharing

正確な私有地・圃場の位置、住所、個人情報を公開・露出させてはいけません。
写真・動画・図・添付資料・位置メタデータについて、家族、近隣住民、ナンバープレート、場所を特定する情報を確認してください。
具体的な共有上の注意は [CONTRIBUTING.md / 写真・動画の共有ルール](CONTRIBUTING.md#写真動画の共有ルール) を参照してください。
公開用に除去・匿名化が必要な場合も、元の failure evidence を破壊せずに扱ってください。
