# CODE_DOCUMENTATION.md

## 1. File & Folder Structure

```text
yt-beats/
├── src/
│   ├── ui/
│   │   ├── styles.css         # Modern Slate Theme (Cyan/Slate)
│   │   └── widgets.py        # Custom Widgets (SearchBar, SearchResultItem, etc.)
│   ├── app.py                # App Logic: TUI, Event Loop, Library Scanning
│   ├── config.py             # Binary Discovery (mpv, ffmpeg) & Pathing
│   ├── downloader.py          # yt-dlp layer, DownloadQueue, & ID matching
│   ├── engine.py              # MPV JSON-IPC playback manager
│   └── __init__.py           # Package init
├── .gitignore                # Excludes virtualenvs, downloads, and .txt logs
├── LICENSE                   # GNU GPL v3
├── README.md                 # User guide & Features
├── requirements.txt          # Python dependencies
├── YT-Beats.bat              # Windows Launcher
└── YT-Beats.sh               # macOS/Linux Launcher
```

## 2. High-Level Architecture

YT-Beats uses a **Decoupled Worker Architecture**:

-   **Frontend (Textual)**: React-like TUI that uses CSS for styling. It handles navigation across three core tabs: **YouTube**, **Library**, and **Downloads**.
-   **Extraction (yt-dlp)**: High-speed metadata extraction. It filters for `bestaudio` to minimize data overhead.
-   **Audio Backend (MPV)**: Runs as an independent process. The Python app controls it via a JSON-over-TCP IPC bridge.
-   **Worker Threads**: Critical tasks (Searching, Local File Scanning, Downloading) run in background workers to keep the UI at a constant 60fps.

## 3. Core Modules & Functions

| Module | Purpose | Key Feature |
| :--- | :--- | :--- |
| `app.py` | Main Orchestrator | Manages tabbed content and playback queue. |
| `engine.py` | Audio Engine | Polling-based position and volume updates. |
| `downloader.py`| YouTube Layer | `DownloadQueue` prevents duplicates via Video ID extraction. |
| `config.py` | Configuration | Automatically locates `mpv.exe` and `ffmpeg.exe` on Windows/Unix. |
| `widgets.py` | UI Components | Lightweight ListItem wrappers with cyan-accented highlights. |

## 4. Execution Flow

1.  **Init**: `app.py` starts, initializes `AudioEngine` (spawning MPV) and `DownloadQueue`.
2.  **Startup Check**: `DownloadQueue` verifies `ffmpeg` presence for later MP3 conversions.
3.  **Library Scan**: A background worker scans the `downloads/` folder for existing media.
4.  **Playback Loop**: Every 0.5s, the app polls MPV for current title, position, and duration to update the progress bar.
5.  **Shutdown**: `on_unmount` sends a `quit` command to MPV and cleans up IPC sockets.

## 5. Platform-Specific Implementations (Windows)

To ensure stability on Windows, several specific optimizations are implemented:
- **Binary Discovery**: `config.py` includes a fallback mechanism for locating `mpv.exe` across common install paths (Chocolatey, custom folders) if the system PATH check fails.
- **IPC over Named Pipes**: Uses `\\.\pipe\ytbeats-XXXXXX` for high-reliability communication on Windows, avoiding the overhead of local network sockets.
- **Aggressive Cleanup**: `engine.py` performs a multi-layer process cleanup on startup (via PID file and Taskkill) to prevent zombie MPV processes from sticking around.
- **Low-Latency Audio**: Explicitly requests the `wasapi` audio output (`--ao=wasapi`) for high-performance audio on Windows.

## 6. Debugging & Logs

The app manages several runtime log files to capture errors without interrupting the user (all ignored by git):
- `crash.log`: Fatal application crashes or startup failures.
- `download_worker_error.txt`: Detailed error backtraces from the background download thread.
- `ui_critical_error.txt`: Errors specifically related to Textual CSS or UI widget updates.
- `callback_error.txt`: Issues within the download completion event handlers.
