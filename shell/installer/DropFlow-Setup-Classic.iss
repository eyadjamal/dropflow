; DropFlow-Setup-Classic.iss
; Public, non-admin installer: portable app + classic "Show more options" menu.
; Build with Inno Setup 6: ISCC.exe DropFlow-Setup-Classic.iss

#define AppName "DropFlow"
#define AppVersion "3.4.0"
#define AppPublisher "Eyad Jamal"
#define AppExe "DropFlow.exe"
#define AppSource "..\..\dist340\DropFlow"

[Setup]
AppId={{A8F3D61B-4D2A-4E7E-9A87-2E4F8C1B6D33}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\DropFlow
DefaultGroupName=DropFlow
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=DropFlow-Setup-3.4.0
OutputDir=output-classic
SetupIconFile=..\package\Assets\DropFlow.ico
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#AppSource}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Uninstall-Classic.ps1"; DestDir: "{app}"; DestName: "Uninstall.ps1"; Flags: ignoreversion

[Icons]
Name: "{group}\DropFlow"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Parameters: "--workspace"
Name: "{autodesktop}\DropFlow"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Parameters: "--workspace"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "--workspace"; Description: "Launch DropFlow"; Flags: nowait postinstall skipifsilent

[Registry]
; Windows 11 legacy/classic context menu. Modern primary-menu registration
; requires a signed package and is not included in this public installer.
Root: HKCU; Subkey: "Software\Classes\*\shell\DropFlow"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Send to DropFlow"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\*\shell\DropFlow"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#AppExe},0"
Root: HKCU; Subkey: "Software\Classes\*\shell\DropFlow"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"
Root: HKCU; Subkey: "Software\Classes\*\shell\DropFlow\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" --send ""%1"""
Root: HKCU; Subkey: "Software\Classes\Directory\shell\DropFlow"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Send to DropFlow"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\shell\DropFlow"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#AppExe},0"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\DropFlow\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" --send ""%1"""
Root: HKCU; Subkey: "Software\DropFlow"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayName"; ValueData: "DropFlow"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#AppVersion}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "Publisher"; ValueData: "{#AppPublisher}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#AppExe}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "UninstallString"; ValueData: """{uninstallexe}"""

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\Uninstall.ps1"""; Flags: runhidden waituntilterminated; RunOnceId: "DropFlowClassicUninstall"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"




