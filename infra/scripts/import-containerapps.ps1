param(
    [ValidateSet("testbed", "prod")]
    [string]$Env = "testbed"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$infraRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$varFile = Join-Path $infraRoot "environments\$Env.tfvars"
$localVarFile = Join-Path $infraRoot "environments\\local.auto.tfvars"
$localVarArgs = @()
if (Test-Path $localVarFile) {
    $localVarArgs = @("-var-file=$localVarFile")
}

if (-not (Test-Path $varFile)) {
    throw "Missing tfvars: $varFile"
}

function Get-TfVarValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )
    $pattern = "^\s*$Name\s*=\s*`"?([^`"]+)`"?\s*$"
    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        if ($trimmed -match $pattern) { return $Matches[1] }
    }
    return ""
}

$subscriptionId = Get-TfVarValue -Name "subscription_id" -Path $varFile
$resourceGroup = Get-TfVarValue -Name "resource_group_name" -Path $varFile

if (-not $subscriptionId) { throw "subscription_id not found in $varFile" }
if (-not $resourceGroup) { throw "resource_group_name not found in $varFile" }

try {
    & terraform @("-chdir=$infraRoot", "workspace", "select", $Env) | Out-Null
} catch {
    & terraform @("-chdir=$infraRoot", "workspace", "new", $Env) | Out-Null
    & terraform @("-chdir=$infraRoot", "workspace", "select", $Env) | Out-Null
}

$apps = @("api", "api2", "web")
$stateList = @()
try {
    $stateList = & terraform @("-chdir=$infraRoot", "state", "list") 2>$null
} catch {
    $stateList = @()
}
foreach ($app in $apps) {
    $appName = if ($app -eq "api2") { "demo-api2-$Env" } else { "demo-$app-$Env" }
    $id = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.App/containerApps/$appName"
    $addrForCmd = 'azurerm_container_app.app[\"' + $app + '\"]'
    $addrForState = 'azurerm_container_app.app["' + $app + '"]'
    if ($stateList -and ($stateList -contains $addrForState)) {
        Write-Host "Skip (already in state): $addrForState"
        continue
    }
    $cmd = 'terraform -chdir="' + $infraRoot + '" import -var-file="' + $varFile + '"'
    if ($localVarArgs.Count -gt 0) {
        $cmd += ' -var-file="' + $localVarFile + '"'
    }
    $cmd += ' ' + $addrForCmd + ' "' + $id + '"'
    & cmd /c $cmd
}

& terraform @("-chdir=$infraRoot", "plan", "-var-file=$varFile") @localVarArgs
