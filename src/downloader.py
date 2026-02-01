import yt_dlp
from typing import List, Dict, Any

class MusicDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': 'in_playlist', # Just get metadata for playlists initially
            'noplaylist': True, # Default to single video unless specified
        }
        
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches YouTube and returns results."""
        search_opts = {
            **self.ydl_opts,
            'default_search': 'ytsearch',
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            try:
                # Search for 'limit' results
                result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                if 'entries' in result:
                    return result['entries']
            except Exception as e:
                print(f"Error searching: {e}")
                return []
        return []

    def get_stream_url(self, video_url: str) -> str:
        """Gets the direct stream URL for a video."""
        opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                return info['url']
            except:
                return None
