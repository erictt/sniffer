"""
Display utilities for CLI output formatting.
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..video_processor import ProcessResults


class DisplayManager:
    """Manages rich console display output."""

    def __init__(self):
        self.console = Console()

    def show_processing_config(
        self,
        input_path: Path,
        audio: bool,
        all_frames: bool,
        frames: str | None,
        transcribe: bool,
    ) -> None:
        """Display processing configuration table."""
        config_table = Table(title="🔧 Processing Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Input Path", str(input_path))
        config_table.add_row("Extract Audio", "✅ Yes" if audio else "❌ No")
        config_table.add_row("Extract All Frames", "✅ Yes" if all_frames else "❌ No")
        config_table.add_row("Frame Position", frames or "❌ None")
        config_table.add_row("Transcribe Audio", "✅ Yes" if transcribe else "❌ No")

        self.console.print(config_table)

    def show_results_summary(
        self, results: list[ProcessResults], transcripts: dict | None = None, transcribe: bool = False, has_results_file: bool = False
    ) -> None:
        """Display a summary of processing results."""
        table = Table(title="🎯 Processing Results Summary")
        table.add_column("Operation", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        # Files processed
        files_count = len(results)
        table.add_row("Files Processed", "✅ Complete", f"{files_count} video(s)")

        # Audio extraction
        audio_count = sum(1 for result in results if result.get("audio_path"))
        if audio_count > 0:
            table.add_row(
                "Audio Extraction", "✅ Complete", f"{audio_count} audio file(s)"
            )

        # Frame extraction
        all_frames_count = sum(len(result.get("all_frames", [])) for result in results)
        if all_frames_count > 0:
            table.add_row("All Frames", "✅ Complete", f"{all_frames_count} frames")

        position_frames_count = sum(
            len(result.get("position_frames", {})) for result in results
        )
        if position_frames_count > 0:
            table.add_row(
                "Position Frames", "✅ Complete", f"{position_frames_count} frames"
            )

        # Transcription
        if transcripts:
            transcript_count = len(transcripts)
            table.add_row(
                "Transcription", "✅ Complete", f"{transcript_count} transcript(s)"
            )

        # Results file
        if has_results_file:
            table.add_row(
                "Results File", "✅ Saved", "data/results/{video_name}.json"
            )

        self.console.print(table)

    def _show_transcription_details(self, transcripts: dict) -> None:
        """Display detailed transcription content."""
        self.console.print("\n🎙️  [bold cyan]Transcription Results[/bold cyan]\n")

        for audio_filename, transcript_data in transcripts.items():
            if "error" in transcript_data:
                self.console.print(
                    f"❌ [red]{audio_filename}[/red]: {transcript_data['error']}"
                )
                continue

            self.console.print(f"📄 [bold]{audio_filename}[/bold]")

            # Show full text if available
            if "text" in transcript_data and transcript_data["text"]:
                self.console.print("[dim]Full text:[/dim]")
                self.console.print(f"[white]{transcript_data['text']}[/white]\n")

            # Show word-level details if available
            if "words" in transcript_data and transcript_data["words"]:
                word_count = len(transcript_data["words"])
                duration = transcript_data.get("duration", "unknown")
                self.console.print(
                    f"[dim]Word-level timestamps: {word_count} words, duration: {duration}s[/dim]"
                )

                # Show first few words as a sample
                sample_words = transcript_data["words"][:10]
                if sample_words:
                    self.console.print("[dim]Sample words with timestamps:[/dim]")
                    for word_info in sample_words:
                        word = word_info.get("word", "")
                        start = word_info.get("start", 0)
                        end = word_info.get("end", 0)
                        self.console.print(f"  [{start:.2f}-{end:.2f}s] {word}")

                    if len(transcript_data["words"]) > 10:
                        remaining = len(transcript_data["words"]) - 10
                        self.console.print(
                            f"  [dim]... and {remaining} more words[/dim]"
                        )

            self.console.print("")


    def show_video_info_table(self, video_files: list[Path]) -> None:
        """Display video files information table."""
        from ..video_processor import VideoProcessor

        table = Table(title="📹 Video Files Information")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="yellow")
        table.add_column("Resolution", style="green")
        table.add_column("FPS", style="blue")
        table.add_column("Duration", style="magenta")
        table.add_column("Frames", style="red")
        table.add_column("Path", style="dim")

        total_size = 0
        for video_file in video_files:
            size_bytes = video_file.stat().st_size
            total_size += size_bytes
            size_str = self._format_file_size(size_bytes)

            try:
                processor = VideoProcessor(video_file)
                video_metadata = processor.get_video_metadata()

                if "error" in video_metadata:
                    table.add_row(
                        video_file.name,
                        size_str,
                        "Error",
                        "Error",
                        "Error",
                        "Error",
                        str(video_file.parent),
                    )
                else:
                    table.add_row(
                        video_file.name,
                        size_str,
                        video_metadata["resolution"],
                        f"{video_metadata['fps']}",
                        f"{video_metadata['duration']}s",
                        str(video_metadata["frame_count"]),
                        str(video_file.parent),
                    )
            except Exception:
                table.add_row(
                    video_file.name,
                    size_str,
                    "Error",
                    "Error",
                    "Error",
                    "Error",
                    str(video_file.parent),
                )

        self.console.print(table)

        # Show summary
        self.console.print(
            f"\n📈 [bold]Total:[/bold] {len(video_files)} files, {self._format_file_size(total_size)}"
        )

    def show_setup_status(self, api_key_exists: bool) -> None:
        """Display setup status table."""
        table = Table(title="🛠️  Setup Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")

        table.add_row("Data Directories", "✅ Ready", "Created in ./data/")
        table.add_row(
            "OpenAI API Key",
            "✅ Found" if api_key_exists else "⚠️  Missing",
            "Set OPENAI_API_KEY env var for transcription"
            if not api_key_exists
            else "Ready for transcription",
        )

        self.console.print(table)

        if not api_key_exists:
            self.console.print("\n💡 [yellow]To enable transcription:[/yellow]")
            self.console.print(
                "   [dim]export OPENAI_API_KEY='your-api-key-here'[/dim]"
            )

    def print(self, *args, **kwargs):
        """Wrapper for console.print."""
        self.console.print(*args, **kwargs)

    def print_exception(self):
        """Wrapper for console.print_exception."""
        self.console.print_exception()

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size_value: float = float(size_bytes)
        while size_value >= 1024 and i < len(size_names) - 1:
            size_value /= 1024.0
            i += 1

        return f"{size_value:.1f}{size_names[i]}"
