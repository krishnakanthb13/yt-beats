from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, Input, Label, Button, ProgressBar, ListItem, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import work

from .ui.widgets import SearchBar, PlayerControls, SearchResultItem, QueueItem, LibraryItem
from .downloader import MusicDownloader, DownloadQueue
from .engine import AudioEngine
from .config import get_downloads_dir

import os


class YTBeatsApp(App):
    CSS_PATH = "ui/styles.css"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "download_selected", "Download"),
        Binding("/", "focus_search", "Search"),
        Binding("space", "toggle_pause", "Pause / Resume", priority=True),
        Binding("r", "refresh_library", "Refresh Library"),
        Binding("n", "next_track", "Next"),
        Binding("p", "previous_track", "Prev"),
        Binding("c", "clear_queue", "Clear"),
        Binding("[", "volume_down", "Vol -"),
        Binding("]", "volume_up", "Vol +"),
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
                with TabbedContent(initial="search-tab", id="main-tabs"):
                    with TabPane("YouTube", id="search-tab"):
                        yield SearchBar(id="search-bar")
                        yield ListView(id="results-list")
                    with TabPane("Library", id="library-tab"):
                        yield Label(str(get_downloads_dir()), id="library-folder-path", classes="folder-path")
                        yield ListView(id="library-list")
                    with TabPane("Downloads", id="downloads-tab"):
                        yield ListView(id="downloads-list")
                
            # Right Pane: Queue
            with Vertical(id="right-pane"):
                yield Label("Up Next", classes="section-header")
                yield ListView(id="queue-list")
                
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
        if not self.downloader.check_ffmpeg():
            self.notify("FFmpeg not found! Downloads will fail to convert to MP3.", severity="warning")
        
        # Bind queue callbacks
        self.download_queue.on_complete = lambda task: self.call_from_thread(self._on_download_complete, task)
        
        # Start the update timer
        self.set_interval(0.5, self.update_status)

    def update_status(self):
        """Periodic UI update."""
        try:
            # 1. Update Playback Status
            if self.engine:
                status = self.engine.get_status()
                title = status.get("title", "Stopped")
                paused = status.get("paused", False)
                status_text = "Paused" if paused else "Playing" 
                if title == "Stopped": status_text = "Stopped"
                
                self.query_one("#status-label", Label).update(f"{status_text}: {title}")
                
                pos = status.get("position", 0)
                dur = status.get("duration", 0)
                pb = self.query_one("#track-progress", ProgressBar)
                if dur > 0:
                    pb.update(total=dur, progress=pos)
                else:
                    pb.update(total=100, progress=0)

                vol = status.get("volume", 100)
                self.query_one("#vol-label", Label).update(f"Vol: {vol}%")
                
            # 2. Update Downloads
            self.update_downloads_ui()
        except:
            # Silent fail for the timer to prevent crash
            pass

    def update_downloads_ui(self):
        """Updates the download list with all active and pending tasks."""
        try:
            dl_list = self.query_one("#downloads-list", ListView)
        except:
            return

        tasks = self.download_queue.tasks
        
        try:
            # If the list count mismatch, fully rebuild (safest)
            if len(dl_list.children) != len(tasks):
                dl_list.clear() # Clear existing
                
                for i, task in enumerate(tasks):
                    # Unique IDs based on task id
                    t_id = id(task)
                    
                    # Create ProgressBar without initial progress (set after)
                    pb = ProgressBar(total=100, classes="dl-progress", id=f"pb-{t_id}")
                    
                    # Create generic ListItem with known children IDs
                    item = ListItem(
                        Horizontal(
                            Label(task.title, classes="dl-title"),
                            Label(task.status.capitalize(), classes="dl-status", id=f"lbl-status-{t_id}"),
                            pb,
                            classes="dl-item-container"
                        )
                    )
                    dl_list.append(item)
            else:
                # Update loop
                for task in tasks:
                    t_id = id(task)
                    try:
                        # Find the widgets by ID in the whole list view 
                        # (querying by ID is safer than index dependence)
                        status_lbl = dl_list.query_one(f"#lbl-status-{t_id}", Label)
                        pb = dl_list.query_one(f"#pb-{t_id}", ProgressBar)
                        
                        status_text = task.status.capitalize()
                        if task.status == "error":
                            status_text = "Failed"
                            
                        status_lbl.update(status_text)
                        pb.progress = task.progress
                    except:
                        # If a single item fails, ignore it
                        continue

        except Exception as e:
            # Log critical UI errors but don't crash
            with open("ui_critical_error.txt", "a") as f: # Append mode
                f.write(f"Error in update: {e}\n")

    def _on_download_complete(self, task):
        """Handle download completion (success or error)."""
        try:
            if task.status == "completed":
                self.notify(f"Download complete: {task.title}")
                # Auto-refresh library so the new song shows up
                self.action_refresh_library()
            else:
                self.notify(f"Download failed: {task.title}\n{task.error_msg}", severity="error")
        except Exception as e:
            with open("callback_error.txt", "w") as f:
                f.write(str(e))
            
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
            list_view.append(ListItem(Label("No results found. Try another search.", classes="result-meta")))
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
        
        # Determine if we should start playing immediately
        # We start if the engine isn't running or if it's currently stopped/idle
        should_start = True
        if self.engine:
            status = self.engine.get_status()
            if status.get("title") != "Stopped":
                should_start = False
        
        if should_start:
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
                status_label = item.query_one(".queue-status", Label)
                if i < self.current_index:
                    status_label.update("Finished")
                    item.remove_class("playing-now")
                elif i == self.current_index:
                    status_label.update("Playing")
                    item.add_class("playing-now")
                else:
                    status_label.update("Pending")
                    item.remove_class("playing-now")

    def action_clear_queue(self):
        """Clear the entire playlist."""
        self.current_playlist = []
        self.current_index = -1
        self.query_one("#queue-list", ListView).clear()
        if self.engine:
            self.engine.stop()
        self.query_one("#status-label", Label).update("Stopped")
        self.notify("Queue cleared.")

    @work(thread=True)
    def action_refresh_library(self):
        """Scan download directory for songs in the background."""
        down_dir = get_downloads_dir()
        files = []
        try:
            for f in os.listdir(down_dir):
                if f.endswith((".mp3", ".m4a", ".webm", ".opus")):
                    full_path = str(down_dir / f)
                    files.append(LibraryItem(f, full_path))
        except Exception as e:
            self.notify(f"Error scanning library: {e}", severity="error")
            return
        
        self.call_from_thread(self._update_library_list, files)

    def _update_library_list(self, files):
        """Updates the library list items on the main thread."""
        lib_list = self.query_one("#library-list", ListView)
        lib_list.clear()
        for item in files:
            lib_list.append(item)
        
        if files:
            # Switch to library tab automatically to show findings
            try:
                self.query_one(TabbedContent).active = "library-tab"
            except:
                pass
            self.notify(f"Library updated: {len(files)} files found.")

    def action_download_selected(self):
        """Download the selected item in the list."""
        try:
            # Try to find the highlighted item in either results or the active queue
            focused = self.focused
            if not focused: return

            # Case 1: Downloading from Search Results
            results_list = self.query_one("#results-list", ListView)
            if results_list.has_focus and results_list.highlighted_child:
                item = results_list.highlighted_child
                if isinstance(item, SearchResultItem):
                    url = f"https://www.youtube.com/watch?v={item.video_id}"
                    task = self.download_queue.add(url, item.title)
                    if task is None:
                        self.notify(f"Already in library: {item.title}", severity="warning")
                    else:
                        self.notify(f"Added to Downloads: {item.title}")
                        # Switch tab to show it
                        try:
                            self.query_one("#main-tabs", TabbedContent).active = "downloads-tab"
                        except:
                            pass
                    return

            # Case 2: Downloading from the active Queue (Up Next)
            queue_list = self.query_one("#queue-list", ListView)
            if queue_list.has_focus and queue_list.highlighted_child:
                idx = queue_list.index
                if idx is not None and 0 <= idx < len(self.current_playlist):
                    track = self.current_playlist[idx]
                    if track["type"] == "streaming":
                        task = self.download_queue.add(track["url"], track["title"])
                        if task is None:
                            self.notify(f"Already in library: {track['title']}", severity="warning")
                        else:
                            self.notify(f"Downloading from Queue: {track['title']}")
                            try:
                                self.query_one("#main-tabs", TabbedContent).active = "downloads-tab"
                            except:
                                pass
                    else:
                        self.notify("This song is already a local file.")
        except Exception as e:
            import traceback
            with open("action_error.txt", "w") as f:
                f.write(traceback.format_exc())
            self.notify(f"Error: {e}", severity="error")

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

    def on_unmount(self):
        if self.engine:
            self.engine.quit()

    def action_volume_up(self):
        if self.engine:
            self.engine.change_volume(10)

    def action_volume_down(self):
        if self.engine:
            self.engine.change_volume(-10)

if __name__ == "__main__":
    try:
        app = YTBeatsApp()
        app.run()
    except Exception as e:
        import traceback
        with open("crash.log", "w") as f:
            f.write(traceback.format_exc())
        print("Application crashed! Check crash.log for details.")
