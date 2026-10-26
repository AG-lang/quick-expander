"""
Windows Autostart Integration
Manages automatic startup on Windows login via HKCU Run registry key.
"""

import sys
import winreg
from pathlib import Path

APP_NAME = "QuickExpander"


def get_default_command() -> str:
    """Returns the recommended launch command line for background startup."""
    base_dir = Path(__file__).resolve().parent.parent
    vbs_path = base_dir / "start_silent.vbs"
    if vbs_path.exists():
        return f'wscript.exe "{vbs_path}"'
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    main_py = base_dir / "main.py"
    return f'"{pythonw}" "{main_py}" --minimized'


def is_autostart_enabled() -> bool:
    """Checks if the application is registered in Windows Startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart(enable: bool, command: str = None) -> bool:
    """Enables or disables autostart in Windows registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        if enable:
            cmd = command or get_default_command()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error setting autostart: {e}")
        return False
