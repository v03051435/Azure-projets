#!/usr/bin/env pwsh
<#
.SYNOPSIS
Prune old ACR image tags, keeping only the N most recent ones per repository.

.PARAMETER AcrName
Name of the Azure Container Registry (default: yhaodevopsacr)

.PARAMETER Keep
Number of most recent tags to keep per repository (default: 10)

.PARAMETER Repos
Comma-separated list of repositories to process (default: repos-api,repos-api2,repos-web)

.PARAMETER DryRun
If set, only show what would be deleted without actually deleting

.EXAMPLE
.\prune_acr_tags.ps1 -Keep 5
.\prune_acr_tags.ps1 -Keep 3 -Repos "repos-api,repos-web"
.\prune_acr_tags.ps1 -DryRun
#>

param(
    [string]$AcrName = "yhaodevopsacr",
    [int]$Keep = 10,
    [string]$Repos = "repos-api,repos-api2,repos-web",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoList = @($Repos -split ',' | ForEach-Object { $_.Trim() })
$totalDeleted = 0
$totalProcessed = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ACR Tag Pruning Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ACR: $AcrName"
Write-Host "Keep: $Keep tags per repo"
Write-Host "DryRun: $DryRun"
Write-Host ""

foreach ($repo in $repoList) {
    Write-Host "=== Processing repo: $repo ===" -ForegroundColor Yellow
    
    try {
        $tags = az acr repository show-tags --name $AcrName --repository $repo --detail --orderby time_desc -o json | ConvertFrom-Json
        
        if (-not $tags) {
            Write-Host "  No tags found" -ForegroundColor Gray
            continue
        }
        
        $tagCount = $tags | Measure-Object | Select-Object -ExpandProperty Count
        Write-Host "  Total tags: $tagCount"
        
        $toKeep = $tags | Select-Object -First $Keep
        $toDelete = $tags | Select-Object -Skip $Keep
        
        Write-Host "  Keep: $($toKeep.Count) tags"
        $toKeep | ForEach-Object { 
            Write-Host "    - $($_.name) (updated: $($_.lastUpdateTime))" -ForegroundColor Green 
        }
        
        if ($toDelete) {
            Write-Host "  Delete: $($toDelete.Count) tags" -ForegroundColor Red
            
            foreach ($tag in $toDelete) {
                $imageName = "$repo`:$($tag.name)"
                Write-Host "    - Deleting $imageName" -ForegroundColor Red
                
                if (-not $DryRun) {
                    try {
                        az acr repository delete --name $AcrName --image $imageName --yes 2>&1 | Out-Null
                        $totalDeleted++
                    } catch {
                        Write-Host "      ERROR: Failed to delete $imageName" -ForegroundColor Red
                    }
                } else {
                    $totalDeleted++
                }
            }
        } else {
            Write-Host "  Nothing to delete" -ForegroundColor Green
        }
        
        $totalProcessed++
    } catch {
        Write-Host "  ERROR: Failed to process repo $repo`: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Repos processed: $totalProcessed"
Write-Host "Tags deleted: $totalDeleted"
if ($DryRun) {
    Write-Host "(DRY RUN - no actual deletions)" -ForegroundColor Yellow
}
Write-Host ""
