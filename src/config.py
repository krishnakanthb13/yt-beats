import os
import shutil
import sys
from pathlib import Path

APP_NAME = "yt-beats"

def get_app_data_dir() -> Path:
    """Returns the platform-specific app data directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
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
    # Windows-specific path resolution for MPV
    if os.name == 'nt':
        if mpv and mpv.lower().endswith(".com"):
            exe_path = Path(mpv).parent / "mpv.exe"
            if exe_path.exists():
                return str(exe_path)
        
        if not mpv:
            # Fallback for common Chocolatey/Windows paths if which() fails
            fallbacks = [
                r"C:\ProgramData\chocolatey\lib\mpvio.install\tools\mpv.exe",
                r"C:\ProgramData\chocolatey\bin\mpv.exe",
                r"C:\mpv\mpv.exe",
                Path.home() / "mpv.exe"
            ]
            
            for path in fallbacks:
                if os.path.exists(path):
                    return str(path)
            
    return mpv

def check_mpv_installed() -> bool:
    """Checks if mpv is available in the system PATH."""
    return get_mpv_path() is not None
