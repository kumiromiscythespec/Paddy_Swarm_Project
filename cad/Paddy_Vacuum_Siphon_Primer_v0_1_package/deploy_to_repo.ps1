param(
    [string]$RepoRoot = "D:\Paddy_Swarm_Project"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Join-Path $PSScriptRoot "Paddy_Swarm_Project"
$CadSource = Join-Path $PackageRoot "cad\paddy_vacuum_siphon_primer_v0_1"
$CadDest = Join-Path $RepoRoot "cad\paddy_vacuum_siphon_primer_v0_1"
$StlSource = Join-Path $PackageRoot "stl\paddy_vacuum_siphon_primer_v0_1"
$StlDest = Join-Path $RepoRoot "stl\paddy_vacuum_siphon_primer_v0_1"

if (-not (Test-Path $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}
if (Test-Path $CadDest) {
    throw "Destination already exists. Refusing to overwrite: $CadDest"
}

New-Item -ItemType Directory -Path (Split-Path $CadDest) -Force | Out-Null
Copy-Item -Path $CadSource -Destination $CadDest -Recurse

New-Item -ItemType Directory -Path $StlDest -Force | Out-Null
Copy-Item -Path (Join-Path $StlSource "*") -Destination $StlDest -Recurse -Force

Write-Host "Installed CAD source to: $CadDest"
Write-Host "Installed preview STL to: $StlDest"
Write-Host "No git commit, push, checkout, or existing-file overwrite was performed."
