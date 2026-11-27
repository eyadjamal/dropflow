# DropFlow Windows 11 modern context menu

Windows 11 does not show arbitrary `HKCU\Software\Classes\*\shell` verbs in the
primary menu. A top-level file/folder command requires:

1. A package identity (MSIX or sparse package).
2. A native COM DLL implementing `IExplorerCommand`.
3. A `desktop4:FileExplorerContextMenus` extension in the package manifest.
4. A trusted signing certificate for the package.

This folder contains that implementation.

## Layout

- `DropFlowShell.cpp` - native COM `IExplorerCommand` implementation.
- `DropFlowShell.def` - DLL exports.
- `DropFlowShell.dll` - compiled x64 DLL.
- `package/AppxManifest.xml` - sparse package manifest.
- `package/Assets/` - package logos and menu icon.
- `DropFlow.Shell.msix` - signed sparse package.
- `DropFlowDev.cer` - public development signing certificate.
- `Register-ModernMenu.ps1` - admin registration script.
- `installer/DropFlow-Setup.iss` - Inno Setup installer source.

## Manifest shape

```xml
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:uap10="http://schemas.microsoft.com/appx/manifest/uap/windows10/10"
  xmlns:com="http://schemas.microsoft.com/appx/manifest/com/windows10"
  xmlns:desktop4="http://schemas.microsoft.com/appx/manifest/desktop/windows10/4"
  xmlns:desktop5="http://schemas.microsoft.com/appx/manifest/desktop/windows10/5"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="DropFlow.Shell" Publisher="CN=DropFlowDev" Version="1.0.0.0" />
  <Properties>
    <uap10:AllowExternalContent>true</uap10:AllowExternalContent>
  </Properties>
  <Applications>
    <Application Id="DropFlow" Executable="DropFlow.exe"
                 uap10:TrustLevel="mediumIL" uap10:RuntimeBehavior="win32App">
      <Extensions>
        <com:Extension Category="windows.comServer">
          <com:ComServer>
            <com:SurrogateServer DisplayName="DropFlow Shell">
              <com:Class Id="7E3C9B6A-9F4C-4E2A-A8D3-3B7A6C1D9E21"
                         Path="DropFlowShell.dll" ThreadingModel="STA" />
            </com:SurrogateServer>
          </com:ComServer>
        </com:Extension>
        <desktop4:Extension Category="windows.fileExplorerContextMenus">
          <desktop4:FileExplorerContextMenus>
            <desktop5:ItemType Type="*">
              <desktop5:Verb Id="SendToDropFlow"
                             Clsid="7E3C9B6A-9F4C-4E2A-A8D3-3B7A6C1D9E21" />
            </desktop5:ItemType>
            <desktop5:ItemType Type="Directory">
              <desktop5:Verb Id="SendToDropFlow"
                             Clsid="7E3C9B6A-9F4C-4E2A-A8D3-3B7A6C1D9E21" />
            </desktop5:ItemType>
          </desktop4:FileExplorerContextMenus>
        </desktop4:Extension>
      </Extensions>
    </Application>
  </Applications>
</Package>
```

`AllowExternalContent` lets the package use the installed portable `DropFlow.exe`
without embedding the whole application in the MSIX.

## Rebuild

```powershell
# Native DLL (x64, static CRT)
cmd /c '"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && cl /nologo /LD /EHsc /MT /DUNICODE /D_UNICODE DropFlowShell.cpp /link /DEF:DropFlowShell.def /OUT:package\DropFlowShell.dll shell32.lib ole32.lib shlwapi.lib advapi32.lib'

# Package
makeappx pack /o /nv /d package /p DropFlow.Shell.msix

# Sign with your real code-signing certificate. The currently shipped
# certificate is a development certificate:
signtool sign /fd SHA256 /f my-cert.pfx /p PASSWORD /a DropFlow.Shell.msix
```

## Register

Run an elevated PowerShell:

```powershell
cd <this folder>
.\Register-ModernMenu.ps1 -AppDir "$env:LOCALAPPDATA\DropFlow"
```

The app directory must contain `DropFlow.exe` and `_internal`, and
`HKCU\Software\DropFlow\InstallDir` will be set for the handler.

On a fresh machine the package certificate must be trusted by the machine. The
included `.cer` is a **self-signed development certificate**; installing it into
the machine root store is only appropriate for testing. For public
distribution, replace it with a CA-issued code-signing certificate whose
subject exactly matches `<Identity Publisher="...">`, then rebuild and re-sign
the MSIX.

## Current limitation

`Add-AppxPackage` returned `0x800B0109` in the test environment because adding
the development certificate to the machine root store requires administrator
rights. The package manifest and signing itself are valid; registration must be
done from an elevated installer with a trusted certificate.

The primary Windows 11 menu cannot be enabled by a plain registry key; this
package/COM approach is required.
