import json
import os
from pathlib import Path
from typing import List, Dict, Optional

from .config import get_app_data_dir

class PlaylistManager:
    def __init__(self, filename: str = "playlists.json"):
        # Check current directory first
        local_path = Path(filename).resolve()
        if local_path.exists():
            self.filepath = local_path
        else:
            # Fallback to AppData
            self.filepath = get_app_data_dir() / filename
            self._ensure_file()

    def _ensure_file(self):
        # Only create if it doesn't exist (and we decided to use the AppData path)
        if not self.filepath.exists():
            try:
                with open(self.filepath, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                print(f"Error creating playlist file: {e}")

    def load_playlists(self) -> List[Dict[str, str]]:
        """Load all saved playlists. Returns list of {name, url}."""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            return []

    def save_playlist(self, name: str, url: str) -> bool:
        """Save a new playlist. Returns True if saved, False if updated existing."""
        try:
            playlists = self.load_playlists()
            
            # Check if exists, update if so
            found = False
            for p in playlists:
                if p['name'] == name:
                    p['url'] = url
                    found = True
                    break
            
            if not found:
                playlists.append({"name": name, "url": url})
                
            with open(self.filepath, 'w') as f:
                json.dump(playlists, f, indent=4)
                
            return found
        except Exception as e:
            # Re-raise to let the app handle it or log it, but at least don't silent fail
            raise e

    def delete_playlist(self, name: str):
        try:
            playlists = self.load_playlists()
            playlists = [p for p in playlists if p['name'] != name]
            with open(self.filepath, 'w') as f:
                json.dump(playlists, f, indent=4)
        except Exception:
            pass
