param([string]$Python = 'python', [string]$ISCC = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe")
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE) { throw 'Tests failed' }
& $Python -m PyInstaller --noconfirm --distpath dist330 DropFlow.spec
if ($LASTEXITCODE) { throw 'Executable build failed' }
Copy-Item THIRD_PARTY_NOTICES.txt dist330\DropFlow\
Copy-Item LICENSE dist330\DropFlow\
Copy-Item README.md dist330\DropFlow\README.txt
& $ISCC shell\installer\DropFlow-Setup-Classic.iss
if ($LASTEXITCODE) { throw 'Installer build failed' }
