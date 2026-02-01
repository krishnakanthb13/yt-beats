# DESIGN_PHILOSOPHY.md

## 1. Problem Definition
Music listeners often find themselves toggling between browser tabs for YouTube and separate desktop apps for local music. Modern web interfaces are heavy, full of ads, and consume significant system resources. Existing terminal players often lack the seamless integration of YouTube search with local library management.

## 2. Why YT-Beats?
YT-Beats aims to provide a "Zen-like" music experience directly in the terminal. It combines the vastness of the YouTube catalog with the performance of local playback in a single, keyboard-driven interface.

## 3. Design Principles

- **Keyboard First**: Every action should be accessible via shortcuts. The mouse is optional, never required.
- **Async by Default**: The UI must never freeze. Search, playback initialization, and downloads occur in background threads to ensure a snappy TUI.
- **Minimalism**: Focus on the music. No album art (yet), no complicated playlists—just search, play, and queue.
- **Process Decoupling**: By running MPV as a separate process, we ensure that if the TUI crashes, the music keeps playing, and vice-versa. It also allows us to leverage MPV's hardware-accelerated audio processing.

## 4. Target Audience & Use Cases
- **Developers & Power Users**: Those who spend their day in the terminal and want low-overhead music controls.
- **Resource-Constrained Systems**: Users who want to listen to YouTube without the CPU/RAM penalty of a modern web browser.
- **Offline Enthusiasts**: Users who want to quickly "keep" a song they just discovered by downloading it as a high-quality MP3.

## 5. Real-World Workflow Fit
YT-Beats is designed to be "launched and forgotten." You search for a lo-fi beat or a full album, start it, and switch back to your coding IDE. The status bar in the terminal provides just enough information (track title and progress) without being distracting.

## 6. Trade-offs & Constraints
- **Dependency Heavy**: Relying on `mpv`, `yt-dlp`, and `ffmpeg` means the user has more initial setup, but the result is a much more robust and feature-rich experience than a pure-Python player.
- **TUI Limitations**: Being a terminal app, we trade visual flashiness (gradients, images) for speed, efficiency, and focus.
- **IPC over Native Bindings**: We use IPC to control MPV instead of native C-bindings (`python-mpv`). This was a conscious choice to avoid the common "segmentation fault" errors found in native Python-MPV wrappers on Windows and macOS.
