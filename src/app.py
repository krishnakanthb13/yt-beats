from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, Input, Label
from textual.containers import Container

from .ui.widgets import SearchBar, PlayerControls, SearchResultItem
from .downloader import MusicDownloader
from .engine import AudioEngine

class YTBeatsApp(App):
    CSS_PATH = "ui/styles.css"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.downloader = MusicDownloader()
        # self.engine = AudioEngine() # Initialize later to avoid immediate mpv check issues during UI build
        self.engine = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield SearchBar(id="search-bar")
        yield ListView(id="results-list")
        yield PlayerControls(id="player-controls")
        yield Footer()

    async def on_mount(self):
        """Focus the search bar automatically on startup."""
        self.query_one("#search-input", Input).focus()

    async def on_unmount(self):
        """Cleanup resources on exit."""
        if self.engine:
            self.engine.quit()

    async def on_input_submitted(self, message: Input.Submitted):
        if message.input.id == "search-input":
            query = message.value
            if not query:
                return
            
            self.notify(f"Searching for '{query}'...")
            # Run search in a worker thread to keep UI responsive
            self.run_worker(self.perform_search(query), exclusive=True)

    async def perform_search(self, query: str):
        """Executes the search and updates the UI."""
        results = self.downloader.search(query)
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()
        
        if not results:
            self.notify("No results found.", severity="warning")
            return

        for res in results:
            # extract duration string if available or generic
            duration = res.get('duration_string', 'N/A')
            list_view.append(
                SearchResultItem(
                    title=res.get('title', 'Unknown'),
                    uploader=res.get('uploader', 'Unknown'),
                    video_id=res.get('id', ''),
                    duration=duration
                )
            )
        self.notify(f"Found {len(results)} results.")

    async def on_list_view_selected(self, message: ListView.Selected):
        """Handle item selection for playback."""
        item = message.item
        if isinstance(item, SearchResultItem):
            if not self.engine:
                # Try to initialize again just in case, or warn
                try:
                    from .engine import AudioEngine
                    self.engine = AudioEngine()
                except Exception as e:
                    self.notify(f"MPV Error: {e}", severity="error")
                    return
            
            self.notify(f"Loading '{item.title}'...")
            # Get stream URL in background
            self.run_worker(self.play_video(item.video_id, item.title))

    async def play_video(self, video_id: str, title: str):
        # STRATEGY: Pass raw YouTube URL to MPV, but FORCE it to use our pip-installed yt-dlp
        # This fixes 403 errors by ensuring the latest downloader is used.
        import shutil
        ytdl_path = shutil.which("yt-dlp")
        
        self.notify(f"Streaming via MPV + yt-dlp: {title}...")
        
        # We pass the raw link so MPV handles the handshake
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        if self.engine:
            # Inject the yt-dlp path into MPV options
            # This is critical for Windows/Chocolatey envs
            self.engine.set_ytdl_path(ytdl_path)
            
            try:
                self.engine.play(url)
                self.query_one("#status-label", Label).update(f"Playing: {title}")
                
                # Check for immediate crash
                self.set_timer(3.0, self.check_playback_status)
                
            except Exception as e:
                 self.notify(f"Playback failed: {e}", severity="error")
        else:
            self.notify("Engine not ready.", severity="error")

    def check_playback_status(self):
        """Checks if the engine is still running."""
        if self.engine and self.engine.process:
            ret = self.engine.process.poll()
            if ret is not None:
                self.notify(f"MPV exited early with code {ret}! Check logs.", severity="error")
                self.query_one("#status-label", Label).update("Status: Exited Error")
        else:
            self.notify("Could not resolve stream URL.", severity="error")

if __name__ == "__main__":
    app = YTBeatsApp()
    app.run()
