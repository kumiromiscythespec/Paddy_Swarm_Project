param(
    [string]$OutputPath = "docs/repository/UNTRACKED_FILE_AUDIT.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Not inside a Git repository."
}

$startBranch = (git branch --show-current).Trim()
$startHead = (git rev-parse HEAD).Trim()
$scriptRelativePath = "tools/generate_repository_untracked_audit.ps1"
$normalizedOutputPath = $OutputPath.Replace("\", "/")

function Get-ProjectLane([string]$Path) {
    $parts = $Path -split "/"
    if ($parts.Length -ge 4 -and $parts[0] -eq "cad" -and $parts[1] -eq "common_rover" -and
        $parts[2] -in @("bbox", "bbox_cbox", "drivetrain", "frame", "physical_authority", "pto")) {
        return ($parts[0..3] -join "/")
    }
    if ($parts.Length -ge 3 -and $parts[0] -eq "cad" -and $parts[1] -eq "common_rover") {
        return ($parts[0..2] -join "/")
    }
    if ($parts.Length -ge 2 -and $parts[0] -eq "cad") {
        return ($parts[0..1] -join "/")
    }
    if ($parts.Length -ge 2) {
        return ($parts[0..1] -join "/")
    }
    return $parts[0]
}

function Get-Classification([string]$Path, [string]$Extension) {
    $leaf = [System.IO.Path]::GetFileName($Path)

    if ($Path -match "^cad/ps_mht_v001/exports/preview/(?:_diag|_finaldiag|_glue_|_progress).*[.]stl$") {
        return "H. DIAGNOSTIC_TEMPORARY"
    }
    if ($Path -match "^cad/(?:accessories|Paddy_Vacuum_Siphon_Primer_v0_1_package|paddy_vacuum_siphon_primer_v0_1|ps_mht_v001(?:_phase3ig_lower_return_buffer)?|ps_usb_inline_raincover_|ps_webcam_rainhood_)") {
        return "I. INDEPENDENT_PROJECT"
    }
    if ($Path -match "^cad/common_rover/physical_authority/") {
        return "B. CURRENT_PHYSICAL_AUTHORITY"
    }
    if ($Path -match "^cad/common_rover/pto/pto_20t_od10_physical_envelope_v001/(?:README[.]md|authority_report[.]md|physical_measurements[.]json)$") {
        return "B. CURRENT_PHYSICAL_AUTHORITY"
    }
    if ($Path -match "^cad/common_rover/(?:common_rover_inward_pto_coupling_cad_verified_v0_9_2_1|frame/front_interface_dual_pto_20t_v002|bbox/bbox_compact_field_goldenmate_v004_g065|common_rover_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32|drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003)/" -and
        $leaf -match "(?i)authority|README") {
        return "A. CURRENT_DESIGN_AUTHORITY"
    }
    if ($Path -match "(?i)(?:^|/)(?:test(?:s)?|validation|evidence|audit|report|manifest|SHA256SUMS|TEST_LOG|BUILD_LOG|physical_result|PHYSICAL_RESULT|MEASUREMENT_LEDGER|source_traceability)(?:/|_|[.]|$)" -or
        $leaf -match "(?i)(test|validation|audit|report|manifest|sha256|result|evidence)") {
        return "C. VALIDATION_EVIDENCE"
    }
    if ($Path -match "(?i)(supersed|historical|obsolete|failure|rejection)") {
        return "E. HISTORICAL / SUPERSEDED"
    }
    if ($Path -match "(?i)(candidate|trade_study|prototype|coupon|trial|temp_|_hold|/hold|physical_validation_pending)") {
        return "F. EXPERIMENTAL / HOLD"
    }
    if ($Extension -in @(".step", ".stp", ".stl", ".svg", ".png", ".dxf", ".3mf")) {
        return "G. GENERATED_REPRODUCIBLE"
    }
    if ($Extension -in @(".py", ".ps1", ".cmd", ".json", ".yaml", ".yml", ".csv")) {
        return "D. CURRENT_SOURCE"
    }
    if ($Extension -in @(".md", ".txt")) {
        return "J. UNKNOWN_NEEDS_REVIEW"
    }
    return "J. UNKNOWN_NEEDS_REVIEW"
}

function Get-OriginKind([string]$Path, [string]$Extension, [string]$Classification) {
    if ($Classification -eq "H. DIAGNOSTIC_TEMPORARY") {
        return "GENERATED_REPRODUCIBLE_DIAGNOSTIC"
    }
    if ($Classification -eq "C. VALIDATION_EVIDENCE") {
        return "VALIDATION_OR_PROVENANCE_EVIDENCE"
    }
    if ($Extension -in @(".step", ".stp", ".stl", ".svg", ".png", ".dxf", ".3mf")) {
        return "LIKELY_GENERATED_ARTIFACT_OR_REFERENCE"
    }
    if ($Extension -in @(".py", ".ps1", ".cmd")) {
        return "SOURCE"
    }
    if ($Extension -in @(".json", ".yaml", ".yml", ".csv")) {
        return "STRUCTURED_SOURCE_OR_EVIDENCE"
    }
    if ($Extension -in @(".md", ".txt")) {
        return "DOCUMENTATION_OR_TEXT_EVIDENCE"
    }
    return "UNKNOWN"
}

function Get-AuthorityRelevance([string]$Classification) {
    switch ($Classification) {
        "A. CURRENT_DESIGN_AUTHORITY" { return "PRIMARY_OR_COMPONENT_DESIGN_AUTHORITY" }
        "B. CURRENT_PHYSICAL_AUTHORITY" { return "DIRECT_OR_DERIVED_PHYSICAL_AUTHORITY" }
        "C. VALIDATION_EVIDENCE" { return "VALIDATION_AND_PROVENANCE" }
        "D. CURRENT_SOURCE" { return "REPRODUCTION_SOURCE_OR_STRUCTURED_INPUT" }
        "E. HISTORICAL / SUPERSEDED" { return "HISTORY_PRESERVATION_DO_NOT_PROMOTE" }
        "F. EXPERIMENTAL / HOLD" { return "CANDIDATE_OR_HOLD_DO_NOT_PROMOTE" }
        "G. GENERATED_REPRODUCIBLE" { return "DERIVED_ARTIFACT_RETAIN_WHEN_REFERENCED" }
        "H. DIAGNOSTIC_TEMPORARY" { return "NO_AUTHORITY_REFERENCE_FOUND_IGNORE_CANDIDATE" }
        "I. INDEPENDENT_PROJECT" { return "OUTSIDE_COMMON_ROVER_AUTHORITY" }
        default { return "REVIEW_BEFORE_AUTHORITY_USE" }
    }
}

$untracked = @(
    git ls-files --others --exclude-standard |
        ForEach-Object { $_.Replace("\", "/") } |
        Where-Object { $_ -ne $scriptRelativePath -and $_ -ne $normalizedOutputPath } |
        Sort-Object
)

$records = foreach ($path in $untracked) {
    $absolutePath = Join-Path $repoRoot $path
    $item = Get-Item -LiteralPath $absolutePath
    $extension = $item.Extension.ToLowerInvariant()
    $classification = Get-Classification -Path $path -Extension $extension
    [ordered]@{
        path = $path
        size_bytes = [long]$item.Length
        extension = if ($extension) { $extension } else { "[none]" }
        project_lane = Get-ProjectLane -Path $path
        likely_generated_or_source = Get-OriginKind -Path $path -Extension $extension -Classification $classification
        classification = $classification
        authority_relevance = Get-AuthorityRelevance -Classification $classification
        large_file_hold = ($item.Length -ge 95MB)
    }
}

$classificationSummary = @(
    $records |
        Group-Object { $_["classification"] } |
        Sort-Object Name |
        ForEach-Object {
            [ordered]@{
                classification = $_.Name
                file_count = $_.Count
                size_bytes = [long](($_.Group | ForEach-Object { $_["size_bytes"] } | Measure-Object -Sum).Sum)
            }
        }
)

$laneSummary = @(
    $records |
        Group-Object { $_["project_lane"] } |
        Sort-Object Name |
        ForEach-Object {
            [ordered]@{
                project_lane = $_.Name
                file_count = $_.Count
                size_bytes = [long](($_.Group | ForEach-Object { $_["size_bytes"] } | Measure-Object -Sum).Sum)
            }
        }
)

$document = [ordered]@{
    schema = "PADDY_SWARM_UNTRACKED_FILE_AUDIT_V1"
    repository = $repoRoot.Replace("\", "/")
    start_branch = $startBranch
    start_head = $startHead
    captured_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    scope_note = "Snapshot of the 4616 pre-flight untracked files. The generator script and generated audit documents are excluded. Classification is conservative and does not itself promote authority."
    thresholds = [ordered]@{
        github_hard_limit_bytes = 100000000
        project_hold_threshold_bytes = 99614720
    }
    totals = [ordered]@{
        file_count = $records.Count
        size_bytes = [long](($records | ForEach-Object { $_["size_bytes"] } | Measure-Object -Sum).Sum)
        large_file_hold_count = @($records | Where-Object { $_["large_file_hold"] }).Count
    }
    classification_summary = $classificationSummary
    lane_summary = $laneSummary
    files = @($records)
}

$outputAbsolute = Join-Path $repoRoot $OutputPath
$outputDirectory = Split-Path -Parent $outputAbsolute
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$document | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputAbsolute -Encoding utf8
Write-Output "Wrote $($records.Count) records to $OutputPath"
