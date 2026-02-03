# DESIGN_PHILOSOPHY.md

## 1. Problem Definition
Music listeners often find themselves toggling between browser tabs for YouTube and separate desktop apps for local music. Modern web interfaces are heavy, full of ads, and consume significant system resources. Existing terminal players often lack the seamless integration of YouTube search with local library management.

## 2. Why YT-Beats?
YT-Beats aims to provide a "Zen-like" music experience directly in the terminal. It combines the vastness of the YouTube catalog with the performance of local playback in a single, keyboard-driven interface.

## 3. Design Principles

- **Keyboard First**: Every action should be accessible via shortcuts. The mouse is optional, never required. The latest navigation system (Arrow keys for context, single-letter commands for action) maximizes speed for power users.
- **Async by Default**: The UI must never freeze. Search, playback initialization, and downloads occur in background threads to ensure a snappy TUI.
- **Minimalism & Focus**: Focus on the music. By moving to a tabbed interface, we categorize the experience (Discover, Organize, Keep, Manage) without cluttering the screen with unnecessary widgets.
- **Bandwidth Efficiency**: Only request what is needed. By strictly requesting audio streams and ignoring video data, YT-Beats reduces network usage by up to 90% compared to a standard web browser.
- **TUI Aesthetics**: Efficiency shouldn't mean ugliness. We use a curated high-contrast slate-and-cyan theme to provide a premium, modern feel that competes with graphical desktop apps.
- **Curated Persistence**: We enable users to save and manage their own playlists locally (`playlists.json`). This keeps the app portable and user-centric, avoiding reliance on cloud accounts for simple song lists.

## 4. Target Audience & Use Cases
- **Developers & Power Users**: Those who spend their day in the terminal and want low-overhead music controls.
- **Resource-Constrained Systems**: Users who want to listen to YouTube without the CPU/RAM penalty of a modern web browser.
- **Curators**: Users who want to build and manage custom playlists of YouTube streams mixed with local files, free from algorithm interference.
- **Library Builders**: Users who want to quickly "keep" a song they just discovered by downloading it as a high-quality MP3 with smart duplicate prevention.

## 5. Real-World Workflow Fit
YT-Beats is designed to be "launched and forgotten." The status bar provides just enough information (track title and progress) without being distracting. The focus is on getting to the music in under 3 seconds—search, hit enter, and get back to work.

## 6. Trade-offs & Constraints
- **Dependency Heavy**: Relying on `mpv`, `yt-dlp`, and `ffmpeg` means the user has more initial setup, but the result is a much more robust experience than a pure-Python player.
- **Process Decoupling**: We use IPC to control MPV instead of native bindings. This ensures that the music keeps playing even if the UI refreshes or the terminal is resized, providing the stability of a background service with the controls of a TUI.

