from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, Input, Label, Button, ProgressBar, ListItem, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import work

from .ui.widgets import SearchBar, PlayerControls, SearchResultItem, QueueItem, DownloadStatus, LibraryItem
from .downloader import MusicDownloader, DownloadQueue
from .engine import AudioEngine
from .config import get_downloads_dir

import threading
import time
import os

class YTBeatsApp(App):
    CSS_PATH = "ui/styles.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "download_selected", "Download"),
        ("/", "focus_search", "Search"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("r", "refresh_library", "Refresh Library"),
        ("n", "next_track", "Next"),
        ("p", "previous_track", "Previous"),
        ("c", "clear_queue", "Clear Queue"),
        ("]", "volume_up", "Vol +"),
        ("[", "volume_down", "Vol -"),
    ]

    def __init__(self):
        super().__init__()
        self.downloader = MusicDownloader()
        self.download_queue = DownloadQueue(str(get_downloads_dir()))
        self.engine = None 
        self.engine_error = None
        # Engine init is delayed or guarded to handle startup issues
        try:
            self.engine = AudioEngine()
        except Exception as e:
            self.engine_error = str(e)
            # We don't print here anymore, we'll notify in on_mount

        self.current_playlist = [] # List of dicts
        self.current_index = -1

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # Left Pane: Search & Library
            with Vertical(id="left-pane"):
                with TabbedContent(initial="search-tab"):
                    with TabPane("YouTube", id="search-tab"):
                        yield SearchBar(id="search-bar")
                        yield ListView(id="results-list")
                    with TabPane("Library", id="library-tab"):
                        yield ListView(id="library-list")
                
            # Right Pane: Queue & Downloads
            with Vertical(id="right-pane"):
                yield Label("Up Next", classes="section-header")
                yield ListView(id="queue-list")
                yield DownloadStatus()
                
        yield PlayerControls(id="player-controls")
        yield Footer()

    async def on_mount(self):
        """Startup tasks."""
        self.query_one("#search-input", Input).focus()
        self.action_refresh_library()
        
        if self.engine:
            # Set the callback for when a track ends
            self.engine.on_track_end = lambda reason: self.call_from_thread(self.action_next_track)
        
        if not self.engine:
            self.notify(f"Playback Engine Error: {self.engine_error}", severity="error")
        else:
            self.notify("YouTube Beats ready!")
        
        # Start the update timer
        self.set_interval(0.5, self.update_status)
        
        # Bind queue callbacks
        # Note: These run in thread, so we'll need call_from_thread to update UI safely if we were doing it directly.
        # But we perform polling update in update_status for simplicity in Textual.

    def update_status(self):
        """Periodic UI update."""
        # 1. Update Playback Status
        if self.engine:
            status = self.engine.get_status()
            
            # Update labels
            title = status.get("title", "Stopped")
            paused = status.get("paused", False)
            
            status_text = "Paused" if paused else "Playing" 
            if title == "Stopped": status_text = "Stopped"
            
            self.query_one("#status-label", Label).update(f"{status_text}: {title}")
            
            # Update Progress
            pos = status.get("position", 0)
            dur = status.get("duration", 0)
            pb = self.query_one("#track-progress", ProgressBar)
            if dur > 0:
                pb.update(total=dur, progress=pos)
            else:
                pb.update(total=100, progress=0)

            # Update Volume Label
            vol = status.get("volume", 100)
            self.query_one("#vol-label", Label).update(f"Vol: {vol}%")
            
        # 2. Update Downloads
        self.update_downloads_ui()

    def update_downloads_ui(self):
        """Updates the download status section."""
        container = self.query_one("#active-downloads", Vertical)
        
        # We'll just show the active task and pending count for simplicity
        active = self.download_queue.active_task
        container.query("Label").remove()
        container.query("ProgressBar").remove()
        
        if active:
            container.mount(Label(f"Downloading: {active.title}"))
            pb = ProgressBar(total=100, show_eta=True)
            pb.progress = active.progress
            container.mount(pb)
        else:
            pending = self.download_queue.queue.qsize()
            if pending > 0:
                container.mount(Label(f"Pending downloads: {pending}"))
            else:
                container.mount(Label("No active downloads."))

    async def on_input_submitted(self, message: Input.Submitted):
        if message.input.id == "search-input":
            query = message.value
            if not query: return
            self.notify(f"Searching for '{query}'...")
            self.perform_search(query)

    @work(exclusive=True, thread=True)
    def perform_search(self, query: str):
        results = self.downloader.search(query)
        
        # Clear must be done on main thread usually.
        # We schedule UI update on the main thread via call_from_thread.
        self.call_from_thread(self._update_results_list, results)

    def _update_results_list(self, results):
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()
        if not results:
            self.notify("No results found.", severity="warning")
            return
            
        for res in results:
            duration = res.get('duration_string', 'N/A')
            item = SearchResultItem(
                title=res.get('title', 'Unknown'),
                uploader=res.get('uploader', 'Unknown'),
                video_id=res.get('id', ''),
                duration=duration
            )
            list_view.append(item)
        
        self.notify(f"Found {len(results)} results.")
        self.query_one("#results-list", ListView).focus()

    async def on_list_view_selected(self, message: ListView.Selected):
        """Handle selection."""
        item = message.item
        if isinstance(item, SearchResultItem):
            self.enqueue(item.title, f"https://www.youtube.com/watch?v={item.video_id}", "streaming")
        elif isinstance(item, LibraryItem):
            self.enqueue(item.title, item.path, "local")

    def enqueue(self, title: str, url: str, source_type: str):
        """Add a song to the queue."""
        self.current_playlist.append({
            "title": title,
            "url": url,
            "type": source_type
        })
        
        # Update Queue UI
        queue_list = self.query_one("#queue-list", ListView)
        queue_list.append(QueueItem(title, "Pending"))
        
        # If nothing is playing, start playing immediately
        if self.current_index == -1:
            self.action_next_track()
        else:
            self.notify(f"Queued: {title}")

    def action_next_track(self):
        """Skip to the next track."""
        if not self.engine: return
        
        if self.current_index + 1 < len(self.current_playlist):
            self.current_index += 1
            self._start_playback()
        else:
            self.notify("End of queue reached.")

    def action_previous_track(self):
        """Go back to the previous track."""
        if not self.engine: return
        
        if self.current_index > 0:
            self.current_index -= 1
            self._start_playback()
        else:
            self.notify("Already at the start of the queue.")

    def _start_playback(self):
        """Common logic to start playing the current_index track."""
        if 0 <= self.current_index < len(self.current_playlist):
            track = self.current_playlist[self.current_index]
            self.query_one("#status-label", Label).update(f"Playing: {track['title']}")
            self._update_queue_status()
            
            # Use a worker to keep UI responsive and prevent overlap
            self.run_playback_worker(track['url'])
        else:
            self.query_one("#status-label", Label).update("Stopped")
            self._update_queue_status()

    @work(exclusive=True, thread=True)
    def run_playback_worker(self, url: str):
        """Exclusive worker to handle MPV play calls."""
        if self.engine:
            self.engine.play(url)

    def _update_queue_status(self):
        """Updates the status labels in the queue list."""
        queue_list = self.query_one("#queue-list", ListView)
        for i, item in enumerate(queue_list.children):
            if isinstance(item, QueueItem):
                if i < self.current_index:
                    item.query_one(".queue-status", Label).update("[Finished]")
                elif i == self.current_index:
                    item.query_one(".queue-status", Label).update("[Playing]")
                else:
                    item.query_one(".queue-status", Label).update("[Pending]")

    def action_clear_queue(self):
        """Clear the entire playlist."""
        self.current_playlist = []
        self.current_index = -1
        self.query_one("#queue-list", ListView).clear()
        if self.engine:
            self.engine.stop()
        self.query_one("#status-label", Label).update("Stopped")
        self.notify("Queue cleared.")

    def action_refresh_library(self):
        """Scan download directory for songs."""
        import os
        lib_list = self.query_one("#library-list", ListView)
        lib_list.clear()
        
        down_dir = get_downloads_dir()
        files = []
        for f in os.listdir(down_dir):
            if f.endswith((".mp3", ".m4a", ".webm", ".opus")):
                full_path = str(down_dir / f)
                files.append(LibraryItem(f, full_path))
        
        for item in files:
            lib_list.append(item)
        
        if files:
            self.notify(f"Library updated: {len(files)} files found.")

    def action_download_selected(self):
        """Download the selected item in the list."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.has_focus and list_view.highlighted_child:
            item = list_view.highlighted_child
            if isinstance(item, SearchResultItem):
                url = f"https://www.youtube.com/watch?v={item.video_id}"
                self.download_queue.add(url, item.title)
                self.notify(f"Added to download queue: {item.title}")
                self.update_downloads_ui()

    def action_focus_search(self):
        self.query_one("#search-input", Input).focus()

    def action_toggle_pause(self):
        if self.engine:
            self.engine.pause()
            
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-play":
            self.action_toggle_pause()
        elif event.button.id == "btn-stop":
            self.action_clear_queue()

    async def on_unmount(self):
        if self.engine:
            self.engine.quit()

    def action_volume_up(self):
        if self.engine:
            status = self.engine.get_status()
            vol = min(status.get("volume", 100) + 10, 100)
            self.engine.set_volume(vol)

    def action_volume_down(self):
        if self.engine:
            status = self.engine.get_status()
            vol = max(status.get("volume", 100) - 10, 0)
            self.engine.set_volume(vol)

if __name__ == "__main__":
    app = YTBeatsApp()
    app.run()
