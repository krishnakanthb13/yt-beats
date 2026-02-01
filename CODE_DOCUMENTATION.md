# CODE_DOCUMENTATION.md

## 1. File & Folder Structure

```text
yt-beats/
├── src/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── styles.css         # Vanilla CSS for the Textual TUI
│   │   └── widgets.py        # Custom Textual widgets (SearchBar, PlayerControls, etc.)
│   ├── __init__.py
│   ├── app.py                # Main application entry point and TUI logic
│   ├── config.py             # Configuration and path management
│   ├── downloader.py          # yt-dlp wrapper for searching and downloading
│   ├── engine.py              # MPV-based audio playback engine
│   └── library.py             # Local library management (scanning)
├── .gitignore                # Git exclusion rules
├── LICENSE                   # GNU GPL v3 License
├── README.md                 # Project overview and quick start
├── requirements.txt          # Python dependencies
├── YT-Beats.bat              # Windows launcher
└── YT-Beats.sh               # Unix/macOS launcher
```

## 2. High-Level Architecture

YT-Beats follows a decoupled architecture where the UI, Downloader, and Playback Engine operate independently:

- **UI Layer (Textual)**: Manages the Terminal User Interface, user input, and state visualization. It uses Workers to perform non-blocking operations.
- **Downloader Layer (yt-dlp)**: Handles YouTube metadata extraction, search queries, and background download/conversion tasks. Requests are strictly limited to audio-only streams to save ~90% bandwidth.
- **Playback Layer (MPV + IPC)**: Controls a background MPV process via JSON-IPC. This allows for stable, high-performance audio playback without blocking the TUI.

## 3. Core Modules & Functions

| Module | Class/Function | Description |
| :--- | :--- | :--- |
| `app.py` | `YTBeatsApp` | The main Textual application class. Coordinates UI events and background tasks. |
| `engine.py` | `AudioEngine` | Manages the lifecycle of the MPV process and handles playback commands via IPC. |
| `downloader.py`| `MusicDownloader`| Provides search functionality and direct stream URL extraction. |
| `downloader.py`| `DownloadQueue` | Manages a background thread for sequential file downloads and MP3 conversion. |
| `config.py` | `get_downloads_dir`| Ensures the cross-platform download directory exists and returns its path. |

## 4. Data Flow

1. **User Search**: Input -> `YTBeatsApp.perform_search` -> `MusicDownloader.search` -> Results returned to ListView.
2. **Streaming**: Selection -> `YTBeatsApp.enqueue` -> `AudioEngine.play(url)` -> MPV process starts playback.
3. **Downloading**: Selection -> `DownloadQueue.add` -> `yt-dlp` download -> `ffmpeg` conversion -> Saved to local library.
4. **Library Refresh**: `action_refresh_library` -> `os.listdir` -> `LibraryItem` creation -> ListView update.

## 5. Dependencies

### Runtime
- `textual`: TUI framework.
- `yt-dlp`: YouTube extraction and downloading.
- `python-mpv-jsonipc`: MPV IPC bridge.
- `mpv`: (System) Media player process.
- `ffmpeg`: (System) Audio conversion utility.

## 6. Execution Flow

1. `app.py` is executed.
2. `YTBeatsApp.__init__` initializes the `AudioEngine` (spawning MPV) and `DownloadQueue`.
3. `on_mount` focuses the search bar and scans the local library.
4. `update_status` starts a 0.5s interval to poll MPV for playback position/title and update UI labels.
5. User interactively triggers searches, playback, or downloads.
6. `on_unmount` ensures the MPV process is gracefully terminated.
