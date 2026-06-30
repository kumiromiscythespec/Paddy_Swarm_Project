# Repo push guide: Turtle Shell Chassis v0.2

From your local repository root:

```powershell
cd C:\Paddy_Swarm_Project
Expand-Archive -Path .\paddy_swarm_turtle_shell_chassis_cad_v0_2.zip -DestinationPath . -Force
git status
git add .
git commit -m "Add standard turtle shell chassis CAD v0.2"
git push
```

Recommended commit note:

- Adds standard turtle shell cover concept
- Updates chassis with shell mount rails and inner dry cassette bay
- Adds Charge Scute wireless charge window dummy
- Keeps inner dry cassette as second defense layer
