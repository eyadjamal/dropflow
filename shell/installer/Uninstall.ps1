$ErrorActionPreference = "SilentlyContinue"
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"") -Wait
    exit
}
$ErrorActionPreference = "SilentlyContinue"
$target = Join-Path $env:LOCALAPPDATA "DropFlow"
Get-Process DropFlow | Stop-Process -Force

$pkg = Get-AppxPackage -Name "DropFlow.Shell"
if ($pkg) { $pkg | Remove-AppxPackage }

Get-ChildItem "Cert:\LocalMachine\Root" |
    Where-Object { $_.Subject -eq "CN=DropFlowDev" } |
    Remove-Item -Force
Get-ChildItem "Cert:\LocalMachine\TrustedPeople" |
    Where-Object { $_.Subject -eq "CN=DropFlowDev" } |
    Remove-Item -Force

$desktop = [Environment]::GetFolderPath("Desktop")
Remove-Item (Join-Path $desktop "DropFlow.lnk") -Force
Remove-Item (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\DropFlow.lnk") -Force
Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow" -Recurse -Force
Remove-Item "HKCU:\Software\DropFlow" -Recurse -Force

