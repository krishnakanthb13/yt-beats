# YT-Beats

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

![YT-Beats Preview](assets/release_v0.0.6.png)

**"The minimal, cross-platform terminal music player for YouTube and local audio."**

A keyboard-driven music experience designed for speed and focus. YT-Beats combines the power of `yt-dlp` and `mpv` with a modern TUI built on `Textual`.

## Features
- **Textual TUI**: Modern, keyboard-driven interface.
- **YouTube Integration**: Search and stream high-quality audio.
- **Bandwidth Optimized**: Streams and downloads pure audio data only, bypassing 90% of typical video bandwidth.
- **Smart Playback**: Prioritizes local files if already downloaded.
- **Lightweight**: Uses `mpv` for efficient playback.

## specific Requirements
- Python 3.9+
- [mpv](https://mpv.io/) connected to system PATH

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting the App
- **Windows**: Double-click `YT-Beats.bat` or run it from terminal.
- **Mac/Linux**: Run `./YT-Beats.sh` from terminal.
- **Manual**: `python -m src.app`

### Controls
- **Search**: The cursor starts in the search bar. Type your query and press **Enter**.
- **Navigate**: Use **Up/Down** arrows to browse results.
- **Play**: Press **Enter** on a result to start streaming.
- **Download**: Press **d** on a result to download the audio to your local library.
- **Quit**: Press **Ctrl+C** or type `q`.

### Features
- **Minimalism**: Focus on the music. No album art (yet), no complicated playlists—just search, play, and queue.
- **Bandwidth Efficiency**: Only request what is needed. By strictly requesting audio streams and ignoring video data, YT-Beats reduces network usage by up to 90% compared to a standard web browser by requesting pure audio containers (Opus/AAC/M4A).
- **Process Decoupling**: By running MPV as a separate process, we ensure that if the TUI crashes, the music keeps playing, and vice-versa. It also allows us to leverage MPV's hardware-accelerated audio processing.

**Note**: You must have `mpv` installed for audio playback.

## Documentation

- [Code Documentation](CODE_DOCUMENTATION.md) - Detailed technical overview.
- [Design Philosophy](DESIGN_PHILOSOPHY.md) - Why this project exists.
- [Contributing](CONTRIBUTING.md) - How to help the project.

## Running

```bash
python -m src.app
```
