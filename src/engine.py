import subprocess
import os
from .config import check_mpv_installed, get_mpv_path

class AudioEngine:
    def __init__(self):
        self.mpv_path = get_mpv_path()
        if not self.mpv_path:
            raise RuntimeError("mpv is not installed or not in PATH.")
        self.process = None
        self.ytdl_path = None # Default to system path logic if not set
        
    def set_ytdl_path(self, path: str):
        """Sets an explicit path for yt-dlp to be used by MPV."""
        self.ytdl_path = path

    def play(self, url: str):
        """Plays a URL or file path using a subprocess."""
        self.stop() # Stop any existing playback using force kill if needed
        
        # Basic arguments: no video, volume 100
        # We also log stderr to a file for debugging
        from .config import get_app_data_dir
        log_file = get_app_data_dir() / "mpv.log"
        self._log_fh = open(log_file, "w", buffering=1) # Line buffering
        
        args = [self.mpv_path, "--no-video", "--volume=100"]
        
        # If we have an explicit yt-dlp path, force MPV to use it
        if self.ytdl_path:
            args.append(f"--script-opts=ytdl_hook-ytdl_path={self.ytdl_path}")
            
        args.append(url)
        
        self._log_fh.write(f"Running command: {args}\n")
        self._log_fh.flush()
        
        # Start mpv as a standalone process
        self.process = subprocess.Popen(
            args, 
            stdout=self._log_fh, 
            stderr=self._log_fh,
            text=True 
        )
        
    def pause(self):
        """Not supported in subprocess mode easily without IPC."""
        pass
        
    def stop(self):
        """Stops playback by killing the process."""
        if self.process:
            try:
                self.process.terminate()
                self.process = None
            except:
                pass
        
    def set_volume(self, volume: int):
        """Not supported in subprocess mode without IPC."""
        pass
        
    def get_status(self):
        """Returns simplified status."""
        is_playing = self.process and self.process.poll() is None
        return {
            "title": "Playing..." if is_playing else "Stopped",
            "duration": 0,
            "position": 0,
            "paused": not is_playing,
            "volume": 0
        }
    
    def quit(self):
        """Ensures cleanup."""
        self.stop()
