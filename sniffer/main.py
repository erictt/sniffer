#!/usr/bin/env python3
"""
Sniffer - Video Content Extraction Tool

A comprehensive tool for sniffing out audio, frames, and transcriptions
from video files with precise word-level timestamps.
"""

from pathlib import Path

import typer
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import (
    VIDEO_PATH,
    AUDIO_PATH,
    VIDEO_FRAMES_PATH,
    TRANSCRIPTS_PATH,
    RESULTS_PATH,
)
from .utils import setup_default_logging
from .utils.directory import ensure_directories
from .cli import ProcessHandler, DisplayManager

app = typer.Typer(
    name="sniffer",
    help="🔍 Video Content Extraction Tool",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()
display = DisplayManager()
process_handler = ProcessHandler()


def setup_directories() -> None:
    """Ensure all required directories exist."""
    ensure_directories(
        [VIDEO_PATH, AUDIO_PATH, VIDEO_FRAMES_PATH, TRANSCRIPTS_PATH, RESULTS_PATH]
    )


def initialize_logging(verbose: bool = False) -> None:
    """Initialize logging system."""
    setup_default_logging()


def get_video_files(input_path: Path) -> list[Path]:
    """
    Get list of video files from a path.

    Args:
        input_path: Path to a video file or directory containing MP4 files

    Returns:
        List of video file paths

    Raises:
        ValueError: If path doesn't exist or no video files found
    """
    if not input_path.exists():
        raise ValueError(f"Path not found: {input_path}")

    if input_path.is_file():
        if input_path.suffix.lower() == ".mp4":
            return [input_path]
        else:
            raise ValueError(f"File must be MP4 format: {input_path}")
    elif input_path.is_dir():
        mp4_files = list(input_path.glob("*.mp4"))
        if not mp4_files:
            raise ValueError(f"No MP4 files found in directory: {input_path}")
        return sorted(mp4_files)
    else:
        raise ValueError(f"Invalid path: {input_path}")


# Function moved to DisplayManager class


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
    frames: str | None = typer.Option(
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
      [dim]python main.py process ./videos[/dim]

    • Extract all frames (warning: large output!):
      [dim]python main.py process video.mp4 --all-frames --no-audio[/dim]
    """

    # Initialize logging
    initialize_logging(verbose)

    setup_directories()

    input_path_obj = Path(input_path)

    # Show processing configuration
    if verbose:
        display.show_processing_config(
            input_path_obj, audio, all_frames, frames, transcribe
        )

    try:
        # Get video files with progress indication
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            init_task = progress.add_task("🚀 Finding video files...", total=None)
            video_files = get_video_files(input_path_obj)
            progress.update(
                init_task, description=f"✅ Found {len(video_files)} video file(s)"
            )
            progress.remove_task(init_task)

        # Process videos using the new handler
        results, transcript_results, enhanced_results = process_handler.process_videos(
            video_files, audio, all_frames, frames, transcribe
        )

        # Show results summary (no sync table display)
        has_results_file = len(enhanced_results) > 0
        display.show_results_summary(
            results, transcript_results, transcribe, has_results_file
        )
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

    try:
        video_files = get_video_files(input_path_obj)

        # Display video information using DisplayManager
        display.show_video_info_table(video_files)

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

    # Show setup results using DisplayManager
    display.show_setup_status(api_key is not None)


if __name__ == "__main__":
    app()
