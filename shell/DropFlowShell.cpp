// DropFlowShell.cpp - native IExplorerCommand for the Windows 11 modern menu.
// Build (x64, static CRT):
//   cl /nologo /LD /EHsc /MT /DUNICODE /D_UNICODE DropFlowShell.cpp
//      /link /OUT:DropFlowShell.dll shell32.lib ole32.lib shlwapi.lib advapi32.lib
#include <windows.h>
#include <shobjidl.h>
#include <shlwapi.h>
#include <string>
#include <vector>
#include <new>

static HMODULE g_module = nullptr;

// Must match AppxManifest.xml and the installer.
static const CLSID CLSID_DropFlowCommand =
    {0x7e3c9b6a, 0x9f4c, 0x4e2a, {0xa8, 0xd3, 0x3b, 0x7a, 0x6c, 0x1d, 0x9e, 0x21}};

static std::wstring ModuleDir() {
    wchar_t path[MAX_PATH * 4] = {};
    DWORD n = GetModuleFileNameW(g_module, path, _countof(path));
    if (!n) return L"";
    PathRemoveFileSpecW(path);
    return path;
}

static std::wstring InstallDir() {
    wchar_t value[MAX_PATH * 4] = {};
    DWORD size = sizeof(value);
    if (RegGetValueW(HKEY_CURRENT_USER, L"Software\\DropFlow", L"InstallDir",
                     RRF_RT_REG_SZ, nullptr, value, &size) == ERROR_SUCCESS) {
        return value;
    }
    wchar_t local[MAX_PATH * 4] = {};
    DWORD n = GetEnvironmentVariableW(L"LOCALAPPDATA", local, _countof(local));
    if (n) return std::wstring(local) + L"\\DropFlow";
    return ModuleDir();
}

static bool GetPaths(IShellItemArray* items, std::vector<std::wstring>& paths) {
    if (!items) return false;
    DWORD count = 0;
    if (FAILED(items->GetCount(&count))) return false;
    for (DWORD i = 0; i < count && i < 64; ++i) {
        IShellItem* item = nullptr;
        if (FAILED(items->GetItemAt(i, &item)) || !item) continue;
        PWSTR path = nullptr;
        if (SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH, &path)) && path) {
            paths.emplace_back(path);
            CoTaskMemFree(path);
        }
        item->Release();
    }
    return !paths.empty();
}

static std::wstring Quote(const std::wstring& value) {
    return L"\"" + value + L"\"";
}

class DropFlowCommand final : public IExplorerCommand {
public:
    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (!ppv) return E_POINTER;
        *ppv = nullptr;
        if (riid == IID_IUnknown || riid == IID_IExplorerCommand) {
            *ppv = static_cast<IExplorerCommand*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override {
        return InterlockedIncrement(&refs_);
    }
    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = InterlockedDecrement(&refs_);
        if (!value) delete this;
        return value;
    }

    // IExplorerCommand
    IFACEMETHODIMP GetTitle(IShellItemArray*, PWSTR* title) override {
        if (!title) return E_POINTER;
        return SHStrDupW(L"Send to DropFlow", title);
    }
    IFACEMETHODIMP GetIcon(IShellItemArray*, PWSTR* icon) override {
        if (!icon) return E_POINTER;
        std::wstring path = ModuleDir() + L"\\Assets\\DropFlow.ico";
        return SHStrDupW(path.c_str(), icon);
    }
    IFACEMETHODIMP GetToolTip(IShellItemArray*, PWSTR* tooltip) override {
        if (tooltip) *tooltip = nullptr;
        return E_NOTIMPL;
    }
    IFACEMETHODIMP GetCanonicalName(GUID* name) override {
        if (!name) return E_POINTER;
        *name = GUID_NULL;
        return S_OK;
    }
    IFACEMETHODIMP GetState(IShellItemArray*, BOOL, EXPCMDSTATE* state) override {
        if (!state) return E_POINTER;
        *state = ECS_ENABLED;
        return S_OK;
    }
    IFACEMETHODIMP GetFlags(EXPCMDFLAGS* flags) override {
        if (!flags) return E_POINTER;
        *flags = ECF_DEFAULT;
        return S_OK;
    }
    IFACEMETHODIMP EnumSubCommands(IEnumExplorerCommand** commands) override {
        if (commands) *commands = nullptr;
        return E_NOTIMPL;
    }
    IFACEMETHODIMP Invoke(IShellItemArray* items, IBindCtx*) override {
        std::vector<std::wstring> paths;
        if (!GetPaths(items, paths)) return S_OK;

        std::wstring command = Quote(InstallDir() + L"\\DropFlow.exe") + L" --send";
        for (const auto& path : paths) {
            command += L" " + Quote(path);
            if (command.size() > 30000) break;
        }
        std::vector<wchar_t> buffer(command.begin(), command.end());
        buffer.push_back(L'\0');

        STARTUPINFOW si = {sizeof(si)};
        PROCESS_INFORMATION pi = {};
        si.dwFlags = STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_SHOWNORMAL;
        if (CreateProcessW(nullptr, buffer.data(), nullptr, nullptr, FALSE,
                           CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi)) {
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);
        }
        return S_OK;
    }

private:
    LONG refs_ = 1;
};

class ClassFactory final : public IClassFactory {
public:
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (!ppv) return E_POINTER;
        *ppv = nullptr;
        if (riid == IID_IUnknown || riid == IID_IClassFactory) {
            *ppv = static_cast<IClassFactory*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override {
        return InterlockedIncrement(&refs_);
    }
    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = InterlockedDecrement(&refs_);
        if (!value) delete this;
        return value;
    }
    IFACEMETHODIMP CreateInstance(IUnknown* outer, REFIID riid, void** ppv) override {
        if (outer) return CLASS_E_NOAGGREGATION;
        auto* command = new (std::nothrow) DropFlowCommand();
        if (!command) return E_OUTOFMEMORY;
        HRESULT hr = command->QueryInterface(riid, ppv);
        command->Release();
        return hr;
    }
    IFACEMETHODIMP LockServer(BOOL) override { return S_OK; }

private:
    LONG refs_ = 1;
};

static bool SetKeyValue(HKEY root, const wchar_t* subkey, const wchar_t* name,
                        const wchar_t* value) {
    HKEY key = nullptr;
    if (RegCreateKeyExW(root, subkey, 0, nullptr, 0, KEY_SET_VALUE,
                        nullptr, &key, nullptr) != ERROR_SUCCESS) return false;
    LONG ok = RegSetValueExW(key, name, 0, REG_SZ,
                             reinterpret_cast<const BYTE*>(value),
                             static_cast<DWORD>((wcslen(value) + 1) * sizeof(wchar_t)));
    RegCloseKey(key);
    return ok == ERROR_SUCCESS;
}

extern "C" BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        g_module = instance;
        DisableThreadLibraryCalls(instance);
    }
    return TRUE;
}

STDAPI
DllGetClassObject(REFCLSID clsid, REFIID riid, void** ppv) {
    if (clsid != CLSID_DropFlowCommand) return CLASS_E_CLASSNOTAVAILABLE;
    auto* factory = new (std::nothrow) ClassFactory();
    if (!factory) return E_OUTOFMEMORY;
    HRESULT hr = factory->QueryInterface(riid, ppv);
    factory->Release();
    return hr;
}

STDAPI DllCanUnloadNow() {
    return S_FALSE;
}

STDAPI DllRegisterServer() {
    wchar_t dll[MAX_PATH * 4] = {};
    if (!GetModuleFileNameW(g_module, dll, _countof(dll))) return E_FAIL;
    const wchar_t* base = L"Software\\Classes\\CLSID\\{7E3C9B6A-9F4C-4E2A-A8D3-3B7A6C1D9E21}";
    if (!SetKeyValue(HKEY_CURRENT_USER, base, nullptr, L"DropFlow Shell Extension"))
        return E_FAIL;
    std::wstring inproc = std::wstring(base) + L"\\InprocServer32";
    if (!SetKeyValue(HKEY_CURRENT_USER, inproc.c_str(), nullptr, dll))
        return E_FAIL;
    if (!SetKeyValue(HKEY_CURRENT_USER, inproc.c_str(), L"ThreadingModel", L"Both"))
        return E_FAIL;
    return S_OK;
}

STDAPI DllUnregisterServer() {
    RegDeleteTreeW(HKEY_CURRENT_USER,
                   L"Software\\Classes\\CLSID\\{7E3C9B6A-9F4C-4E2A-A8D3-3B7A6C1D9E21}");
    return S_OK;
}



