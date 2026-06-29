# docs/repo_push_amphibious_hull_pack.md

# How to add this CAD pack to the public repo

Put `paddy_swarm_amphibious_hull_cad_v0_1.zip` in your repo root, for example:

```text
C:\Paddy_Swarm_Project
```

Then run PowerShell:

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_amphibious_hull_cad_v0_1.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add amphibious hull Grade 0 CAD pack v0.1"
git push
```

If the ZIP file itself appears in `git status`, do not commit the ZIP. Commit the extracted files only.
