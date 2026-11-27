; DropFlow-Setup.iss - build with Inno Setup 6 (ISCC.exe DropFlow-Setup.iss)
; This produces DropFlow-Setup.exe. The modern-menu package is signed with the
; development certificate in this folder; for public distribution replace it
; with a CA-issued certificate and rebuild DropFlow.Shell.msix.

#define AppName "DropFlow"
#define AppVersion "3.4.0"
#define AppPublisher "Eyad Jamal"
#define AppExe "DropFlow.exe"
#define AppSource "..\..\..\DropFlow-Windows"

[Setup]
AppId={{8B5B3A74-57C1-45F4-9E2E-D5F6D3A1C9E2}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\DropFlow
DefaultGroupName=DropFlow
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=DropFlow-Setup
OutputDir=output
SetupIconFile=..\package\Assets\DropFlow.ico
Compression=lzma2/ultra64
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
Source: "..\DropFlow.Shell.msix"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\DropFlowDev.cer"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Register-ModernMenu.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "Uninstall.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DropFlow"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Parameters: "--workspace"
Name: "{autodesktop}\DropFlow"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Parameters: "--workspace"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\Register-ModernMenu.ps1"" -AppDir ""{app}"" -Package ""{app}\DropFlow.Shell.msix"" -Certificate ""{app}\DropFlowDev.cer"""; Flags: runhidden waituntilterminated
Filename: "{app}\{#AppExe}"; Parameters: "--workspace"; Description: "Launch DropFlow"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\DropFlow"; ValueType: string; ValueName: "InstallDir"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayName"; ValueData: "DropFlow"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#AppVersion}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "Publisher"; ValueData: "{#AppPublisher}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#AppExe}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\DropFlow"; ValueType: string; ValueName: "UninstallString"; ValueData: """{uninstallexe}"""

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\Uninstall.ps1"""; Flags: runhidden waituntilterminated; RunOnceId: "DropFlowUninstall"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"




