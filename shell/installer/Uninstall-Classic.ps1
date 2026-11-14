$ErrorActionPreference = "SilentlyContinue"
$target = Join-Path $env:LOCALAPPDATA "DropFlow"
Get-Process DropFlow | Stop-Process -Force

Remove-Item "HKCU:\Software\Classes\*\shell\DropFlow" -Recurse -Force
Remove-Item "HKCU:\Software\Classes\Directory\shell\DropFlow" -Recurse -Force
Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow" -Recurse -Force
Remove-Item "HKCU:\Software\DropFlow" -Recurse -Force
Remove-Item (Join-Path ([Environment]::GetFolderPath("Desktop")) "DropFlow.lnk") -Force
Remove-Item (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\DropFlow.lnk") -Force

