import yt_dlp
import threading
import queue
import time
import os
import shutil
from typing import List, Dict, Any, Callable, Optional

class DownloadTask:
    def __init__(self, url: str, title: str, playlist_name: str = None):
        self.url = url
        self.title = title
        self.playlist_name = playlist_name
        self.status = "pending" # pending, downloading, completed, error
        self.progress = 0.0
        self.error_msg = None
        self.filename = None

class DownloadQueue:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.queue = queue.Queue()
        self.tasks: List[DownloadTask] = [] # Keep track of all tasks
        self.active_task: Optional[DownloadTask] = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        
        # Callbacks for UI updates
        self.on_progress: Optional[Callable[[DownloadTask], None]] = None
        self.on_complete: Optional[Callable[[DownloadTask], None]] = None
        
    def add(self, url: str, title: str, playlist_name: str = None):
        """Adds a song to the download queue. Returns None if already downloaded."""
        # Extract video ID from URL for duplicate detection
        video_id = self._extract_video_id(url)
        
        if video_id and self.is_already_downloaded(video_id):
            return None  # Already exists
        
        task = DownloadTask(url, title, playlist_name)
        self.tasks.append(task)
        self.queue.put(task)
        return task
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        import re
        patterns = [
            r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'(?:embed/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def is_already_downloaded(self, video_id: str) -> bool:
        """Check if a video with this ID already exists in downloads."""
        try:
            for f in os.listdir(self.download_dir):
                # Files are saved as "title_[videoId].mp3"
                if f"[{video_id}]" in f:
                    return True
        except:
            pass
        return False
        
    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                task = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            try:
                self.active_task = task
                task.status = "downloading"
                
                # Check for FFmpeg before starting
                if not self.check_ffmpeg():
                    task.status = "error"
                    task.error_msg = "FFmpeg not found. Audio conversion will fail."
                    if self.on_complete: self.on_complete(task)
                    self.queue.task_done()
                    self.active_task = None
                    continue
                    
                self._process_download(task)
                self.queue.task_done()
                self.active_task = None
            except Exception as e:
                # Log any unexpected errors to file for debugging
                task.status = "error"
                task.error_msg = str(e)
                with open("download_worker_error.txt", "a") as f:
                    f.write(f"Worker error: {e}\n")
                if self.on_complete: self.on_complete(task)
                try:
                    self.queue.task_done()
                except:
                    pass
                self.active_task = None
    
    def check_ffmpeg(self) -> bool:
        """Checks if ffmpeg is available in the system path."""
        return shutil.which("ffmpeg") is not None
            
    def _process_download(self, task: DownloadTask):
        """Downloads the video using yt-dlp."""
        
        # Determine output path
        output_dir = self.download_dir
        if task.playlist_name:
            output_dir = os.path.join(output_dir, task.playlist_name)
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s_[%(id)s].%(ext)s'),
            'quiet': True,
            'progress_hooks': [lambda d: self._progress_hook(d, task)],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info and download
                info = ydl.extract_info(task.url, download=True)
                
                # Predict the final filename after MP3 conversion
                # yt-dlp prepare_filename gives the original, we swap extension to .mp3
                base_path = ydl.prepare_filename(info)
                final_filename = os.path.splitext(base_path)[0] + ".mp3"
                
                task.filename = final_filename
                task.status = "completed"
                task.progress = 100.0
                
                if self.on_complete:
                    self.on_complete(task)
        except Exception as e:
            task.status = "error"
            task.error_msg = str(e)
            if self.on_complete:
                self.on_complete(task)

    def _progress_hook(self, d, task):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                task.progress = float(p)
                if self.on_progress:
                    self.on_progress(task)
            except:
                pass
        elif d['status'] == 'finished':
            task.progress = 100.0

class MusicDownloader:
    # Kept for search functionality
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': 'in_playlist',
            'noplaylist': True,
        }
        
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches YouTube and returns results."""
        search_opts = {
            **self.ydl_opts,
            'default_search': 'ytsearch',
            'extract_flat': True,
        }
        
        # If it's a URL, don't use ytsearch prefix
        if query.startswith("http"):
            search_query = query
        else:
            search_query = f"ytsearch{limit}:{query}"
            
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            try:
                result = ydl.extract_info(search_query, download=False)
                if 'entries' in result:
                    return result['entries']
                elif 'title' in result: # Single video URL result
                    return [result]
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
            except Exception as e:
                return None

    def check_ffmpeg(self) -> bool:
        """Checks if ffmpeg is available in the system path."""
        return shutil.which("ffmpeg") is not None
