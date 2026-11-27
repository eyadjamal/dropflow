"""Windows 11 compositor-backed blur surface underneath a Tk window."""
import ctypes
from ctypes import wintypes as wt
import sys


def system_effects():
    if sys.platform != "win32":
        return False, True
    import winreg
    animations = wt.BOOL(True)
    ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(animations), 0)
    class HighContrast(ctypes.Structure):
        _fields_ = [("size", wt.UINT), ("flags", wt.DWORD), ("scheme", wt.LPWSTR)]
    contrast = HighContrast()
    contrast.size = ctypes.sizeof(contrast)
    ctypes.windll.user32.SystemParametersInfoW(0x42, contrast.size, ctypes.byref(contrast), 0)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            transparent = bool(winreg.QueryValueEx(key, "EnableTransparency")[0])
    except OSError:
        transparent = False
    return transparent and not (contrast.flags & 1), bool(animations.value)


def attach(win, enabled=True):
    if sys.platform != "win32" or sys.getwindowsversion().build < 22621:
        return False
    win._dropflow_glass_enabled = enabled and system_effects()[0]
    if not win._dropflow_glass_enabled:
        if getattr(win, "_dropflow_surface", None):
            ctypes.windll.user32.ShowWindow(win._dropflow_surface, 0)
        return False
    if getattr(win, "_dropflow_surface", None):
        win._dropflow_sync()
        return True
    user = ctypes.windll.user32
    create = user.CreateWindowExW
    create.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int,
                       ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND,
                       wt.HMENU, wt.HINSTANCE, wt.LPVOID]
    create.restype = wt.HWND
    # No redirection bitmap: DWM supplies the entire surface.
    surface = create(0x00200000 | 0x08000000 | 0x80 | 0x20, "STATIC", "",
                     0x80000000, 0, 0, 0, 0, None, None, None, None)
    if not surface:
        return False
    surface = wt.HWND(surface)
    class Accent(ctypes.Structure):
        _fields_ = [("state", ctypes.c_int), ("flags", ctypes.c_int),
                    ("tint", wt.DWORD), ("animation", ctypes.c_int)]
    class Attribute(ctypes.Structure):
        _fields_ = [("attribute", ctypes.c_int), ("data", ctypes.c_void_p),
                    ("size", ctypes.c_size_t)]
    # ACCENT_ENABLE_BLURBEHIND samples the scene below this HWND.
    accent = Accent(3, 0, 0, 0)
    attribute = Attribute(19, ctypes.cast(ctypes.byref(accent), ctypes.c_void_p),
                          ctypes.sizeof(accent))
    if not user.SetWindowCompositionAttribute(surface, ctypes.byref(attribute)):
        user.DestroyWindow(surface)
        return False
    win._dropflow_surface = surface
    def sync(event=None):
        if event and event.widget is not win:
            return
        if win.winfo_ismapped() and win._dropflow_glass_enabled:
            hwnd = user.GetAncestor(win.winfo_id(), 2)
            user.SetWindowPos(surface, wt.HWND(hwnd), win.winfo_rootx(), win.winfo_rooty(),
                              win.winfo_width(), win.winfo_height(), 0x10 | 0x40)
        else:
            user.ShowWindow(surface, 0)
    def destroy(event):
        if event.widget is win:
            user.DestroyWindow(surface)
            win._dropflow_surface = None
    for sequence in ("<Configure>", "<Map>", "<Unmap>", "<FocusIn>"):
        win.bind(sequence, sync, add="+")
    win.bind("<Destroy>", destroy, add="+")
    win._dropflow_sync = sync
    sync()
    return True
