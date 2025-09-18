"""
Results output service for saving processing results to JSON files.
"""

from pathlib import Path
import json
from typing import Any

from ..utils.logging import get_logger
from ..utils.directory import ensure_directory
from ..config.constants import RESULTS_PATH


class ResultsService:
    """Service for saving video processing results to structured files."""

    def __init__(self):
        self.logger = get_logger("sniffer.results")

    def save_results_to_json(
        self,
        video_file: Path,
        video_metadata: dict[str, Any],
        frame_transcript_stats: dict[str, Any],
        frame_transcript_mapping: list[dict],
        transcript_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Save video processing results to JSON file in data/results/.

        Args:
            video_file: Source video file
            video_metadata: Video metadata from VideoMetadataService
            frame_transcript_stats: Statistics about frame-transcript sync
            frame_transcript_mapping: Frame-transcript mapping table
            transcript_data: Transcription data from AudioTranscriber

        Returns:
            Path to the saved JSON file
        """
        self.logger.info(f"Saving results to JSON for: {video_file.name}")

        # Use video file name with .json extension in results directory
        video_name = video_file.stem
        json_file_path = Path(RESULTS_PATH) / f"{video_name}.json"

        # Ensure directory exists
        ensure_directory(json_file_path.parent)

        # Enhanced video info with file size
        enhanced_video_info = {
            "video_file": video_file.name,
            "video_path": str(video_file),
            "file_size": self._format_file_size(video_file.stat().st_size),
        }

        # Add video metadata if available
        if "error" not in video_metadata:
            enhanced_video_info.update({
                "duration": f"{video_metadata['duration']:.2f}s",
                "resolution": video_metadata["resolution"],
                "fps": video_metadata["fps"],
                "total_frames": video_metadata["frame_count"],
            })

        # Create clean, non-redundant output structure
        output_data = {
            "video_info": enhanced_video_info,
            "frame_transcript_statistics": frame_transcript_stats,
            "frame_transcript_mapping": frame_transcript_mapping,
        }

        # Add transcript overview if available
        if transcript_data and "error" not in transcript_data:
            text = transcript_data.get("text", "")
            words = transcript_data.get("words", [])

            if text and words:
                # Calculate speech analysis
                speech_analysis = self._analyze_speech_patterns(words)

                output_data["transcript_overview"] = {
                    "total_words": len(words),
                    "total_characters": len(text),
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "speech_analysis": speech_analysis,
                }

        # Add metadata
        output_data["metadata"] = {
            "generated_by": "sniffer",
            "version": "1.0",
            "timestamp": self._get_current_timestamp(),
        }

        # Write to JSON file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Results saved to: {json_file_path}")
        return str(json_file_path)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

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

    def _analyze_speech_patterns(self, words: list[dict]) -> dict[str, Any]:
        """Analyze speaking patterns and gaps in speech."""
        if not words:
            return {}

        # Calculate gaps between words
        gaps = []
        for i in range(1, len(words)):
            prev_end = words[i - 1].get("end", 0)
            curr_start = words[i].get("start", 0)
            gap = curr_start - prev_end
            if gap > 0.5:  # Significant gap
                gaps.append(gap)

        # Calculate speaking statistics
        first_word_start = words[0].get("start", 0)
        last_word_end = words[-1].get("end", 0)
        total_speech_time = last_word_end - first_word_start

        return {
            "first_word_at": f"{first_word_start:.2f}s",
            "last_word_at": f"{last_word_end:.2f}s",
            "total_speech_duration": f"{total_speech_time:.2f}s",
            "significant_gaps": len(gaps),
            "longest_gap": f"{max(gaps):.2f}s" if gaps else "0.00s",
        }