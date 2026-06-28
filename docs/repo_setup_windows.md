# docs/repo_setup_windows.md

# WindowsでPaddy Swarm Projectのpublic repoを作る手順

この手順は、`C:\Paddy_Swarm_Project` をGitHubのpublic repositoryとして公開するためのメモです。

## 0. 前提

インストール済みであること：

- Git
- GitHub CLI `gh`

確認コマンド：

```powershell
git --version
gh --version
```

GitHub CLIにログインしていない場合：

```powershell
gh auth login
```

---

## 1. このZIPを展開する

`paddy_swarm_public_repo_files_v0_1.zip` を `C:\Paddy_Swarm_Project` に置いて、PowerShellで以下を実行します。

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_public_repo_files_v0_1.zip -DestinationPath . -Force
```

この時点で、以下のような構成になります。

```text
C:\Paddy_Swarm_Project
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── docs/
├── stl/
├── cad/
├── bom/
├── experiments/
├── software/
├── images/
├── tools/
├── print_manifest.csv
└── kit_index.csv
```

元の `paddy_swarm_3d_print_pack_v0_1.zip` は `.gitignore` によりGit管理対象から外れます。

---

## 2. Gitリポジトリ化する

```powershell
cd C:\Paddy_Swarm_Project
git init
git branch -M main
git status
```

---

## 3. 初回コミット

```powershell
git add .
git commit -m "Initial public Grade 0 release"
```

---

## 4. GitHub CLIでpublic repoを作ってpushする

リポジトリ名を `Paddy_Swarm_Project` にする場合：

```powershell
gh repo create Paddy_Swarm_Project --public --source=. --remote=origin --push
```

これでGitHub上にpublic repoが作成され、現在のフォルダ内容がpushされます。

---

## 5. 既にGitHub側でrepoを作った場合

GitHubのWeb画面で空のrepositoryを作成済みの場合は、以下を使います。  
`YOUR_GITHUB_ID` は自分のGitHubアカウント名に置き換えてください。

```powershell
git remote add origin https://github.com/YOUR_GITHUB_ID/Paddy_Swarm_Project.git
git push -u origin main
```

---

## 6. 公開前チェック

```powershell
git status
git log --oneline -5
```

確認すること：

- 個人情報が入っていない
- 正確な田んぼ位置情報が入っていない
- 家族・近隣・ナンバープレートが写った画像がない
- 危険な試験を推奨する文章になっていない
- 元のZIPや巨大ファイルを重複コミットしていない

---

## 7. 次回以降の更新

```powershell
git status
git add .
git commit -m "Update docs and test notes"
git push
```
