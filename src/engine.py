import time
import threading
import shutil
import uuid
import subprocess
import os
from typing import Optional, Callable, Dict, Any
from python_mpv_jsonipc import MPV
from .config import get_mpv_path

class AudioEngine:
    def __init__(self):
        self.mpv_path = get_mpv_path()
        if not self.mpv_path:
            raise RuntimeError("mpv is not installed or not in PATH.")
            
        # Find yt-dlp to ensure MPV can play YouTube URLs
        ytdl_path = shutil.which("yt-dlp")
        
        # Cleanup any orphaned yt-beats MPV processes from previous crashes
        self._cleanup_orphaned_processes()
        
        # Minimal args to prevent startup crashes on some Windows envs
        # We start MPV manually because python-mpv-jsonipc adds '=yes' to boolean flags
        # which causes MPV v0.41.0 to crash on startup (Exit code 1).
        
        pipe_id = f"ytbeats-{uuid.uuid4().hex[:6]}"
        if os.name == 'nt':
            self.ipc_path = r"\\.\pipe\\" + pipe_id
            ipc_socket_arg = pipe_id
        else:
            self.ipc_path = os.path.join("/tmp", f"{pipe_id}.sock")
            ipc_socket_arg = self.ipc_path
            
        mpv_args = [
            self.mpv_path,
            "--idle",
            "--no-video",
            "--no-config",
            "--volume=100",
            "--force-window=no",      # Strictly no window
            "--player-operation-mode=cplayer", # Force console mode (no OSC/GUI)
            "--osd-level=0",          # Disable on-screen display
            "--input-default-bindings=no", # Disable built-in keys
            "--input-builtin-bindings=no",
            f"--input-ipc-server={self.ipc_path}"
        ]
        
        # Use high-performance audio output on Windows if available
        if os.name == 'nt':
            mpv_args.append("--ao=wasapi")
        
        if ytdl_path:
            mpv_args.append(f"--script-opts=ytdl_hook-ytdl_path={ytdl_path}")
            
        # Launch MPV process
        self.process = subprocess.Popen(
            mpv_args,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Connection retry loop replaces the magic sleep
        connected = False
        start_time = time.time()
        while time.time() - start_time < 3.0: # Try for 3 seconds
            try:
                # Connection library to the existing process
                self.mpv = MPV(start_mpv=False, ipc_socket=ipc_socket_arg)
                connected = True
                break
            except Exception:
                time.sleep(0.1)
        
        if not connected:
            self.quit()
            raise RuntimeError(f"Could not connect to MPV IPC on: {self.ipc_path}")
                       
        # Configure MPV properties via IPC
        self.mpv.command("set_property", "keep-open", "yes") # Don't exit on partial errors
        
        # Event handling strategies from shellbeats
        self.ignore_events_until = 0.0
        self.on_track_end: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # Bind events
        self.mpv.bind_event("end-file", self._on_end_file)
        
    def play(self, url: str):
        """Plays a URL (stream or local file)."""
        # Grace period logic: Ignore events for 3 seconds to avoid
        # spurious 'end-file' during buffering/loading
        self.ignore_events_until = time.time() + 3.0
        
        try:
            # Check if it's already playing this URL to avoid restart?
            # For now, just play
            self.mpv.play(url)
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))

    def pause(self):
        """Toggles pause."""
        try:
            self.mpv.command("cycle", "pause")
        except Exception as e:
            pass # Silent fail is expected if MPV is not ready

    def stop(self):
        """Stops playback."""
        try:
            self.mpv.command("stop")
        except Exception as e:
            pass
            
    def set_volume(self, volume: int):
        """Sets volume (0-100)."""
        try:
            self.mpv.command("set_property", "volume", volume)
        except Exception:
            pass

    def change_volume(self, delta: int):
        """Changes volume by delta (e.g., 5 or -5)."""
        try:
            self.mpv.command("add", "volume", delta)
        except Exception:
            pass

    def quit(self):
        """Terminates the MPV process."""
        try:
            self.mpv.terminate()
        except:
            pass
        try:
            if self.process:
                self.process.terminate()
        except:
            pass
            
        # Cleanup Unix socket file
        if os.name != 'nt' and hasattr(self, 'ipc_path') and os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except:
                pass
            
    def get_status(self) -> Dict[str, Any]:
        """Returns playback status."""
        try:
            # Fetch properties; use default values if None is returned
            p = self.mpv.get_properties(["pause", "time-pos", "duration", "media-title", "volume"])
            return {
                "paused": p.get("pause", False) or False,
                "position": float(p.get("time-pos", 0) or 0),
                "duration": float(p.get("duration", 0) or 0),
                "title": p.get("media-title", "Stopped") or "Stopped",
                "volume": int(p.get("volume", 100) or 100),
            }
        except Exception:
            return {
                "paused": True,
                "position": 0,
                "duration": 0,
                "title": "Stopped",
                "volume": 100
            }

    def _on_end_file(self, event_data):
        """Handles track end events."""
        if time.time() < self.ignore_events_until:
            return

        reason = event_data.get("reason", "unknown")
        
        # 'eof' means natural end, 'error' means stream failed
        if reason == "eof":
            if self.on_track_end:
                self.on_track_end("eof")
        elif reason == "error":
            if self.on_error:
                self.on_error("MPV Stream Error")
            # Also treat error as track end to advance playlist?
            # shellbeats treats error as a reason to skip to next
            if self.on_track_end: 
                self.on_track_end("error")

    def _cleanup_orphaned_processes(self):
        """No-op by default to avoid killing other MPV instances. 
        Unique pipe names are used to prevent conflicts."""
        # Cleanup logic is now handled by process tracking and quit()
        pass
