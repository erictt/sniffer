"""
Process handler for video processing operations.
"""

from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from ..types import ProcessResults
from ..video_processor import VideoProcessor
from ..transcription import AudioTranscriber
from ..services import SyncService, ResultsService


class ProcessHandler:
    """Handles the main video processing workflow."""

    def __init__(self) -> None:
        self.sync_service = SyncService()
        self.results_service = ResultsService()

    def process_videos(
        self,
        video_files: list[Path],
        audio: bool,
        all_frames: bool,
        frames: str | None,
        transcribe: bool,
    ) -> tuple[list[ProcessResults], dict, list[dict]]:
        """
        Process multiple video files with progress tracking.

        Args:
            video_files: List of video file paths
            audio: Whether to extract audio
            all_frames: Whether to extract all frames
            frames: Frame position for extraction
            transcribe: Whether to transcribe audio

        Returns:
            Tuple of (processing results, transcript results, enhanced results)
        """
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Process each video file
            results = self._process_video_files(
                progress, video_files, audio, all_frames, frames
            )

            # Transcribe if requested
            transcript_results = self._process_transcriptions(
                progress, results, transcribe, audio
            )

            # Generate enhanced results only if transcribing
            enhanced_results = []
            if transcribe and frames:
                enhanced_results = self._generate_enhanced_results(
                    progress, video_files, results, transcript_results, frames
                )

            return results, transcript_results, enhanced_results

    def _process_video_files(
        self,
        progress: Progress,
        video_files: list[Path],
        audio: bool,
        all_frames: bool,
        frames: str | None,
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
                        # Note: Display methods should be called through DisplayManager in main.py
                        transcript_results[Path(audio_path).name] = {"error": str(e)}

                    progress.remove_task(transcribe_task)

        return transcript_results

    def _generate_enhanced_results(
        self,
        progress: Progress,
        video_files: list[Path],
        results: list[ProcessResults],
        transcript_results: dict,
        frames: str | None,
    ) -> list[dict]:
        """Generate enhanced results with summaries and sync tables."""
        enhanced_results: list[dict] = []

        if not frames:  # No frame extraction, skip sync tables
            return enhanced_results

        enhance_task = progress.add_task(
            "📊 Generating summaries and sync tables...", total=None
        )

        for i, (video_file, result) in enumerate(zip(video_files, results)):
            # Get transcript data for this video
            audio_filename = Path(result.get("audio_path", "")).name
            transcript_data = transcript_results.get(audio_filename)

            # Get video metadata
            processor = VideoProcessor(video_file)
            video_metadata = processor.get_video_metadata()

            # Generate and save sync table if we have position frames
            sync_table = []
            sync_stats = {}
            json_path = None
            if "position_frames" in result and result["position_frames"]:
                sync_table = self.sync_service.create_frame_transcript_table(
                    result["position_frames"], transcript_data
                )
                sync_stats = self.sync_service.get_sync_statistics(sync_table)

                # Save to JSON file automatically
                json_path = self.results_service.save_results_to_json(
                    video_file, video_metadata, sync_stats, sync_table, transcript_data
                )

            enhanced_results.append(
                {
                    "video_file": video_file,
                    "sync_table": sync_table,
                    "sync_stats": sync_stats,
                    "json_path": json_path,
                }
            )

        progress.update(enhance_task, description="✅ Enhanced results ready")
        progress.remove_task(enhance_task)

        return enhanced_results
