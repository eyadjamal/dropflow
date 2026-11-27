param(
    [string]$AppDir = (Join-Path $env:LOCALAPPDATA "DropFlow"),
    [string]$Package = (Join-Path $PSScriptRoot "DropFlow.Shell.msix"),
    [string]$Certificate = (Join-Path $PSScriptRoot "DropFlowDev.cer")
)

$ErrorActionPreference = "Stop"
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this script from an elevated PowerShell window."
}
if (-not (Test-Path (Join-Path $AppDir "DropFlow.exe"))) {
    throw "DropFlow.exe was not found in $AppDir"
}

# Register the COM server and the Windows 11 FileExplorerContextMenus extension.
& certutil.exe -addstore -f Root $Certificate | Out-Null
& certutil.exe -addstore -f TrustedPeople $Certificate | Out-Null

$old = Get-AppxPackage -Name "DropFlow.Shell" -ErrorAction SilentlyContinue
if ($old) { $old | Remove-AppxPackage -ErrorAction SilentlyContinue | Out-Null }

Add-AppxPackage -Path $Package -ExternalLocation $AppDir -ForceApplicationShutdown

New-Item -Path "HKCU:\Software\DropFlow" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\DropFlow" -Name InstallDir -Value $AppDir

Write-Host "DropFlow modern context menu registered."
Write-Host "If it does not appear, restart Windows Explorer."
