import os
import shutil
import sys
from pathlib import Path

APP_NAME = "yt-beats"

def get_app_data_dir() -> Path:
    """Returns the platform-specific app data directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
    else:
        base = Path(os.path.expanduser("~/.config"))
    
    app_dir = base / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_downloads_dir() -> Path:
    """Returns the directory where music will be saved."""
    app_dir = get_app_data_dir()
    downloads_dir = app_dir / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    return downloads_dir

def get_mpv_path() -> str:
    """Returns the absolute path to mpv executable, preferring .exe over .com."""
    mpv = shutil.which("mpv")
    if not mpv:
        return None
        
    # If we found mpv.com, try to see if mpv.exe is in the same folder
    # This avoids shim issues on Chocolatey/Windows
    if mpv.lower().endswith(".com"):
        exe_path = Path(mpv).parent / "mpv.exe"
        if exe_path.exists():
            return str(exe_path)
            
    return mpv

def check_mpv_installed() -> bool:
    """Checks if mpv is available in the system PATH."""
    return get_mpv_path() is not None
