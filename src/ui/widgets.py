from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label, ListItem, ListView
from textual.containers import Container, Horizontal

class SearchBar(Container):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search YouTube...", id="search-input")

class SearchResultItem(ListItem):
    def __init__(self, title: str, uploader: str, video_id: str, duration: str):
        super().__init__()
        self.title = title
        self.uploader = uploader
        self.video_id = video_id
        self.duration = duration

    def compose(self) -> ComposeResult:
        yield Label(f"{self.title} ({self.duration}) - {self.uploader}")

class PlayerControls(Container):
    def compose(self) -> ComposeResult:
        yield Button("Play/Pause", id="btn-play")
        yield Label("Status: Stopped", id="status-label")
