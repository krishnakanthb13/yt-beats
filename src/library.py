import json
from pathlib import Path
from typing import List, Dict
from .config import get_app_data_dir

class MusicLibrary:
    def __init__(self):
        self.data_dir = get_app_data_dir()
        self.library_file = self.data_dir / "library.json"
        self.songs: List[Dict] = self._load_library()

    def _load_library(self) -> List[Dict]:
        if not self.library_file.exists():
            return []
        try:
            with open(self.library_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_library(self):
        with open(self.library_file, 'w') as f:
            json.dump(self.songs, f, indent=2)

    def add_song(self, song_data: Dict):
        """Adds a song to the library if not exists."""
        # check duplicates by id
        if not any(s['id'] == song_data['id'] for s in self.songs):
            self.songs.append(song_data)
            self.save_library()

    def get_songs(self) -> List[Dict]:
        return self.songs
