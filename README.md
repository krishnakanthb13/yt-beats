# YT-Beats

**"The minimal, cross-platform terminal music player for YouTube and local audio."**

A keyboard-driven music experience inspired by [Shellbeats](https://github.com/lalo-space/shellbeats), now available for Windows, Mac, and Linux.

## Features
- **Textual TUI**: Modern, keyboard-driven interface.
- **YouTube Integration**: Search and stream high-quality audio.
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
- **Quit**: Press **Ctrl+C** or type `q`.

**Note**: You must have `mpv` installed for audio playback.

## Running

```bash
python -m src.app
```
