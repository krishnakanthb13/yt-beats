from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label, ListItem, ListView, ProgressBar
from textual.containers import Container, Horizontal, Vertical

class SearchBar(Container):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search YouTube... (Press / to focus)", id="search-input")

class SearchResultItem(ListItem):
    def __init__(self, title: str, uploader: str, video_id: str, duration: str):
        super().__init__()
        self.title = title
        self.uploader = uploader
        self.video_id = video_id
        self.duration = duration

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="result-title")
        yield Label(f"{self.uploader} - {self.duration}", classes="result-meta")

class LibraryItem(ListItem):
    def __init__(self, title: str, path: str):
        super().__init__()
        self.title = title
        self.path = path

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="library-title")
        yield Label(self.path, classes="library-path")

class QueueItem(ListItem):
    def __init__(self, title: str, status: str):
        super().__init__()
        self.title = title
        self.status = status

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="queue-title")
        yield Label(self.status, classes="queue-status")

class PlayerControls(Container):
    def compose(self) -> ComposeResult:
        yield Button("Pause", id="btn-play", variant="primary")
        yield Button("Stop", id="btn-stop", variant="error")
        with Vertical(id="player-info"):
            yield Label("Stopped", id="status-label")
            yield ProgressBar(id="track-progress", show_eta=False, show_percentage=False)
        yield Label("Vol: 100%", id="vol-label")

