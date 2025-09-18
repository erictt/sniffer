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


def show_results_summary(
    results: list[ProcessResults], transcripts: Optional[dict] = None
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
        table.add_row("Audio Extraction", "✅ Complete", f"{audio_count} audio file(s)")

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
            # Get video files
            init_task = progress.add_task("🚀 Finding video files...", total=None)
            video_files = get_video_files(input_path_obj)
            progress.update(
                init_task, description=f"✅ Found {len(video_files)} video file(s)"
            )
            progress.remove_task(init_task)

            # Process each video file
            results = []
            for i, video_file in enumerate(video_files):
                process_task = progress.add_task(
                    f"🎬 Processing video {i + 1}/{len(video_files)}: {video_file.name}...",
                    total=None,
                )

                processor = VideoProcessor(video_file)
                result = processor.process_all(
                    extract_audio=audio,
                    extract_all_frames=all_frames,
                    frame_position=frames,
                )
                results.append(result)

                progress.update(
                    process_task, description=f"✅ Processed {video_file.name}"
                )
                progress.remove_task(process_task)

            # Transcribe if requested
            transcript_results = {}
            if transcribe and audio:
                audio_paths = [
                    result["audio_path"]
                    for result in results
                    if result.get("audio_path")
                ]

                if audio_paths:
                    for i, audio_path in enumerate(audio_paths):
                        transcribe_task = progress.add_task(
                            f"🎙️  Transcribing audio {i + 1}/{len(audio_paths)}: {Path(audio_path).name}...",
                            total=None,
                        )

                        try:
                            transcriber = AudioTranscriber(audio_path)
                            transcript = transcriber.transcribe()
                            transcript_results[Path(audio_path).name] = transcript

                            progress.update(
                                transcribe_task,
                                description=f"✅ Transcribed {Path(audio_path).name}",
                            )

                        except Exception as e:
                            progress.update(
                                transcribe_task,
                                description=f"❌ Transcription failed: {Path(audio_path).name}",
                            )
                            console.print(
                                f"⚠️  [yellow]Warning:[/yellow] Transcription failed for {Path(audio_path).name}: {e}"
                            )
                            console.print(
                                "💡 [dim]Make sure OPENAI_API_KEY environment variable is set[/dim]"
                            )
                            transcript_results[Path(audio_path).name] = {
                                "error": str(e)
                            }

                        progress.remove_task(transcribe_task)

        # Show results summary
        show_results_summary(results, transcript_results)
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

        # Create info table with metadata columns
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
            size_str = format_size(size_bytes)

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

        console.print(table)

        # Show summary
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
