<#
.SYNOPSIS
  Resets the modkit to a pristine state before launch:
    - restores Game\Content\OriginalAsset\* entries back to Game\Content\
    - deletes all Game\Content\Mods\<X>\ subfolders
  Files about to be replaced or deleted are first moved into a timestamped
  backup folder under Game\Saved\ModkitCleanupBackups\.

.EXAMPLE
  .\Clean-ModkitLeftovers.ps1            # dry-run
  .\Clean-ModkitLeftovers.ps1 -Apply     # commit
#>

[CmdletBinding()]
param(
    [string]$ModkitRoot  = (Resolve-Path "$PSScriptRoot\..").Path,
    [int]   $KeepBackups = 10,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

$ContentDir       = Join-Path $ModkitRoot 'Game\Content'
$ModsContentDir   = Join-Path $ContentDir 'Mods'
$OriginalAssetDir = Join-Path $ContentDir 'OriginalAsset'
$BackupRoot       = Join-Path $ModkitRoot 'Game\Saved\ModkitCleanupBackups'
$BackupDir        = Join-Path $BackupRoot (Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')

if ($Apply) { Write-Host "Mode: APPLY (changes will be made)"   -ForegroundColor Red }
else        { Write-Host "Mode: DRY-RUN (pass -Apply to commit)" -ForegroundColor Green }
if ($Apply) { Write-Host "Backups -> $BackupDir" -ForegroundColor Cyan }
Write-Host ""

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

# --- 1. Restore originals (backing up modded current versions) ---------------
$restoreCount = 0
if (Test-Path $OriginalAssetDir) {
    Get-ChildItem -Path $OriginalAssetDir -Recurse -File | ForEach-Object {
        $rel  = $_.FullName.Substring($OriginalAssetDir.Length).TrimStart('\','/')
        $dest = Join-Path $ContentDir $rel
        $bak  = Join-Path $BackupDir  $rel

        Write-Host "  RESTORE : $rel" -ForegroundColor Yellow
        if ($Apply) {
            if (Test-Path -LiteralPath $dest) {
                Ensure-Dir (Split-Path -Parent $bak)
                Move-Item -LiteralPath $dest -Destination $bak -Force
            }
            Ensure-Dir (Split-Path -Parent $dest)
            Move-Item -LiteralPath $_.FullName -Destination $dest -Force
        }
        $restoreCount++
    }
}

# --- 2. Delete Content\Mods subfolders (by moving them into backup) ----------
$deletedCount = 0
if (Test-Path $ModsContentDir) {
    Get-ChildItem -Path $ModsContentDir -Directory | ForEach-Object {
        $bak = Join-Path $BackupDir ("Mods\" + $_.Name)
        Write-Host "  DELETE  : Game\Content\Mods\$($_.Name)" -ForegroundColor Yellow
        if ($Apply) {
            Ensure-Dir (Split-Path -Parent $bak)
            Move-Item -LiteralPath $_.FullName -Destination $bak -Force
        }
        $deletedCount++
    }
}

# --- 3. Prune old backups ----------------------------------------------------
if ($Apply -and (Test-Path $BackupRoot)) {
    $allBackups = @(Get-ChildItem -Path $BackupRoot -Directory | Sort-Object Name -Descending)
    if ($allBackups.Count -gt $KeepBackups) {
        $allBackups | Select-Object -Skip $KeepBackups | ForEach-Object {
            Write-Host "  PRUNE   : $($_.Name)"
            Remove-Item -LiteralPath $_.FullName -Recurse -Force
        }
    }
}

# --- Summary -----------------------------------------------------------------
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Originals restored  : $restoreCount"
Write-Host "  Mod folders cleared : $deletedCount"
if (-not $Apply) {
    Write-Host "`nDry-run only. Re-run with -Apply to commit." -ForegroundColor Green
}
