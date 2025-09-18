"""
Process handler for video processing operations.
"""

from typing import Optional
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from ..video_processor import VideoProcessor, ProcessResults
from ..transcription import AudioTranscriber
from .display import DisplayManager


class ProcessHandler:
    """Handles the main video processing workflow."""

    def __init__(self):
        self.display = DisplayManager()

    def process_videos(
        self,
        video_files: list[Path],
        audio: bool,
        all_frames: bool,
        frames: Optional[str],
        transcribe: bool,
    ) -> tuple[list[ProcessResults], dict]:
        """
        Process multiple video files with progress tracking.

        Args:
            video_files: List of video file paths
            audio: Whether to extract audio
            all_frames: Whether to extract all frames
            frames: Frame position for extraction
            transcribe: Whether to transcribe audio

        Returns:
            Tuple of (processing results, transcript results)
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.display.console,
        ) as progress:
            # Process each video file
            results = self._process_video_files(
                progress, video_files, audio, all_frames, frames
            )

            # Transcribe if requested
            transcript_results = self._process_transcriptions(
                progress, results, transcribe, audio
            )

            return results, transcript_results

    def _process_video_files(
        self,
        progress: Progress,
        video_files: list[Path],
        audio: bool,
        all_frames: bool,
        frames: Optional[str],
    ) -> list[ProcessResults]:
        """Process video files for audio and frame extraction."""
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

            progress.update(process_task, description=f"✅ Processed {video_file.name}")
            progress.remove_task(process_task)

        return results

    def _process_transcriptions(
        self,
        progress: Progress,
        results: list[ProcessResults],
        transcribe: bool,
        audio: bool,
    ) -> dict:
        """Process audio transcriptions if requested."""
        transcript_results = {}

        if transcribe and audio:
            audio_paths = [
                result["audio_path"] for result in results if result.get("audio_path")
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
                        self.display.print(
                            f"⚠️  [yellow]Warning:[/yellow] Transcription failed for {Path(audio_path).name}: {e}"
                        )
                        self.display.print(
                            "💡 [dim]Make sure OPENAI_API_KEY environment variable is set[/dim]"
                        )
                        transcript_results[Path(audio_path).name] = {"error": str(e)}

                    progress.remove_task(transcribe_task)

        return transcript_results
