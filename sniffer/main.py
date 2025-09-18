#!/usr/bin/env python3
"""
Sniffer - Video Content Extraction Tool

A comprehensive tool for sniffing out audio, frames, and transcriptions
from video files with precise word-level timestamps.
"""

from pathlib import Path
from typing import Optional

import typer
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .video_processor import VideoProcessor, ProcessResults
from .transcription import AudioTranscriber
from .config import VIDEO_PATH, AUDIO_PATH, VIDEO_FRAMES_PATH, TRANSCRIPTS_PATH
from .utils import setup_default_logging
from .utils.directory import ensure_directories

app = typer.Typer(
    name="sniffer",
    help="🔍 Video Content Extraction Tool",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()


def setup_directories() -> None:
    """Ensure all required directories exist."""
    ensure_directories([VIDEO_PATH, AUDIO_PATH, VIDEO_FRAMES_PATH, TRANSCRIPTS_PATH])


def initialize_logging(verbose: bool = False) -> None:
    """Initialize logging system."""
    setup_default_logging()


def show_results_summary(results: ProcessResults) -> None:
    """Display a summary of processing results."""
    table = Table(title="🎯 Processing Results Summary")
    table.add_column("Operation", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    # Files processed
    files_count = len(results.get("processed_files", []))
    table.add_row("Files Processed", "✅ Complete", f"{files_count} video(s)")

    # Audio extraction
    if results.get("audio_paths"):
        audio_count = (
            len(results["audio_paths"])
            if isinstance(results["audio_paths"], list)
            else 1
        )
        table.add_row("Audio Extraction", "✅ Complete", f"{audio_count} audio file(s)")

    # Frame extraction
    if results.get("all_frames"):
        frame_count = (
            sum(len(frames) for frames in results["all_frames"].values())
            if isinstance(results["all_frames"], dict)
            else len(results["all_frames"])
        )
        table.add_row("All Frames", "✅ Complete", f"{frame_count} frames")

    if results.get("position_frames"):
        pos_frame_count = (
            sum(len(frames) for frames in results["position_frames"].values())
            if isinstance(results["position_frames"], dict)
            else len(results["position_frames"])
        )
        table.add_row("Position Frames", "✅ Complete", f"{pos_frame_count} frames")

    # Transcription
    if results.get("transcripts"):
        transcript_count = len(results["transcripts"])
        table.add_row(
            "Transcription", "✅ Complete", f"{transcript_count} transcript(s)"
        )

    console.print(table)


@app.command()
def process(
    input_path: str = typer.Argument(
        ..., help="📁 Path to video file or directory containing MP4 files"
    ),
    # Audio options
    audio: bool = typer.Option(
        True, "--audio/--no-audio", help="🎵 Extract audio from videos"
    ),
    # Frame options
    frames: Optional[str] = typer.Option(
        None,
        "--frames",
        help="🖼️  Extract frames by position per second [start|middle|end|random]",
        click_type=click.Choice(["start", "middle", "end", "random"]),
    ),
    all_frames: bool = typer.Option(
        False, "--all-frames", help="🎞️  Extract ALL frames (large output!)"
    ),
    # Transcription options
    transcribe: bool = typer.Option(
        False, "--transcribe", help="🎙️  Transcribe audio with word-level timestamps"
    ),
    # Output options
    verbose: bool = typer.Option(False, "--verbose", "-v", help="📝 Verbose output"),
) -> None:
    """
    🎬 Process video files to extract audio, frames, and generate transcriptions.

    [bold cyan]Examples:[/bold cyan]

    • Process single video with middle frames and transcription:
      [dim]python main.py process video.mp4 --frames middle --transcribe[/dim]

    • Batch process folder with audio only:
      [dim]python main.py process ./videos --no-frames[/dim]

    • Extract all frames (warning: large output!):
      [dim]python main.py process video.mp4 --all-frames --no-audio[/dim]
    """

    # Initialize logging
    initialize_logging(verbose)

    setup_directories()

    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        console.print(f"❌ [red]Error:[/red] Path not found: {input_path}")
        raise typer.Exit(1)

    # Show processing configuration
    if verbose:
        config_table = Table(title="🔧 Processing Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Input Path", str(input_path_obj))
        config_table.add_row("Extract Audio", "✅ Yes" if audio else "❌ No")
        config_table.add_row("Extract All Frames", "✅ Yes" if all_frames else "❌ No")
        config_table.add_row("Frame Position", frames or "❌ None")
        config_table.add_row("Transcribe Audio", "✅ Yes" if transcribe else "❌ No")

        console.print(config_table)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize processor
            init_task = progress.add_task(
                "🚀 Initializing video processor...", total=None
            )
            processor = VideoProcessor(input_path_obj)
            video_files = processor.get_video_files()
            progress.update(
                init_task, description=f"✅ Found {len(video_files)} video file(s)"
            )
            progress.remove_task(init_task)

            # Process videos
            process_task = progress.add_task("🎬 Processing videos...", total=None)
            results = processor.process_all(
                extract_audio=audio,
                extract_all_frames=all_frames,
                frame_position=frames,
            )
            progress.update(process_task, description="✅ Video processing complete")
            progress.remove_task(process_task)

            # Transcribe if requested
            if transcribe and audio:
                transcribe_task = progress.add_task(
                    "🎙️  Transcribing audio...", total=None
                )
                try:
                    transcriber = AudioTranscriber()
                    audio_paths = results["audio_paths"]

                    if audio_paths:
                        transcript_results = transcriber.transcribe_batch(audio_paths)
                    else:
                        transcript_results = {}
                    results["transcripts"] = transcript_results
                    progress.update(
                        transcribe_task,
                        description=f"✅ Transcribed {len(transcript_results)} audio file(s)",
                    )

                except Exception as e:
                    progress.update(
                        transcribe_task, description="❌ Transcription failed"
                    )
                    console.print(
                        f"⚠️  [yellow]Warning:[/yellow] Transcription failed: {e}"
                    )
                    console.print(
                        "💡 [dim]Make sure OPENAI_API_KEY environment variable is set[/dim]"
                    )

                progress.remove_task(transcribe_task)

        # Show results summary
        show_results_summary(results)
        console.print("🎉 [green]All processing completed successfully![/green]")

    except Exception as e:
        console.print(f"❌ [red]Error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def info(
    input_path: str = typer.Argument(..., help="📁 Path to video file or directory"),
) -> None:
    """
    📊 Show information about video files without processing them.
    """

    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        console.print(f"❌ [red]Error:[/red] Path not found: {input_path}")
        raise typer.Exit(1)

    try:
        processor = VideoProcessor(input_path_obj)
        video_files = processor.get_video_files()

        # Create info table
        table = Table(title="📹 Video Files Information")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="yellow")
        table.add_column("Path", style="dim")

        total_size = 0
        for video_file in video_files:
            size_bytes = video_file.stat().st_size
            total_size += size_bytes

            # Format file size
            size_str = format_size(size_bytes)

            table.add_row(video_file.name, size_str, str(video_file.parent))

        console.print(table)
        console.print(
            f"\n📈 [bold]Total:[/bold] {len(video_files)} files, {format_size(total_size)}"
        )

    except Exception as e:
        console.print(f"❌ [red]Error:[/red] {e}")
        raise typer.Exit(1)


def format_size(size_bytes: int) -> str:
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


@app.command()
def setup() -> None:
    """
    🔧 Setup required directories and check dependencies.
    """

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Setup directories
        setup_task = progress.add_task("📁 Setting up directories...", total=None)
        setup_directories()
        progress.update(setup_task, description="✅ Directories created")
        progress.remove_task(setup_task)

        # Check dependencies
        deps_task = progress.add_task("🔍 Checking dependencies...", total=None)

        # Check OpenAI API key
        import os

        api_key = os.getenv("OPENAI_API_KEY")

        progress.remove_task(deps_task)

    # Show setup results
    table = Table(title="🛠️  Setup Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    table.add_row("Data Directories", "✅ Ready", "Created in ./data/")
    table.add_row(
        "OpenAI API Key",
        "✅ Found" if api_key else "⚠️  Missing",
        "Set OPENAI_API_KEY env var for transcription"
        if not api_key
        else "Ready for transcription",
    )

    console.print(table)

    if not api_key:
        console.print("\n💡 [yellow]To enable transcription:[/yellow]")
        console.print("   [dim]export OPENAI_API_KEY='your-api-key-here'[/dim]")


if __name__ == "__main__":
    app()
