# CONTRIBUTING.md

Thank you for your interest in improving YT-Beats! This project is open-source and welcomes contributions from everyone.

## 1. Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/krishnakanthb13/yt-beats.git
   cd yt-beats
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure system dependencies are installed**:
   - [mpv](https://mpv.io/)
   - [ffmpeg](https://ffmpeg.org/)
   - [yt-dlp](https://github.com/yt-dlp/yt-dlp)

4. **Run the app in development mode**:
   ```bash
   python -m src.app
   ```

## 2. Workflow

1. **Fork** the repository on GitHub.
2. **Create a branch** for your feature or bug fix: `git checkout -b feat/my-new-feature`.
3. **Write code** and ensure it follows the project's async/worker patterns.
4. **Test** your changes across different YouTube queries and local files.
5. **Submit a Pull Request** with a clear description of your changes.

## 3. Bug Reporting

When reporting a bug, please include:
- Your Operating System.
- Python version.
- Any error messages from the terminal or the Textual notification system.
- Steps to reproduce the issue.

## 4. Feature Suggestions

Feel free to open an issue to discuss new features. We are particularly interested in:
- Improved queue management (move/remove items).
- Playlist support.
- Custom keybindings configuration.
- UI themes.

## 5. Pre-submission Checklist

- [ ] Code follows PEP 8 style guidelines.
- [ ] No blocking I/O on the main thread (use Textual `@work` decorators).
- [ ] MPV IPC connection logic remains robust.
- [ ] Documentation updated if adding new features.
- [ ] `requirements.txt` updated if adding new libraries.

---
**Happy coding!**
