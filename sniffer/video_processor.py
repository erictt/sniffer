"""
Video processing module for extracting audio and frames from video files.
Supports both single file and batch processing of MP4 files.
"""

from pathlib import Path
import moviepy as mp
import cv2  # noqa: F401 - Required for tests to patch correctly

from .types import ProcessResults
from .config.constants import AUDIO_PATH, VIDEO_FRAMES_PATH
from .utils.directory import ensure_directory
from .utils.file import extract_filename_from_path
from .utils.logging import get_logger, ProgressLogger
from .services import VideoMetadataService, FrameExtractionService
from .services.frame_extraction import FrameExtractionConfig


class VideoProcessor:
    """
    A class for processing a single video file to extract audio and frames.
    """

    def __init__(self, video_file: str | Path) -> None:
        """
        Initialize VideoProcessor with a single video file.

        Args:
            video_file: Path to a single MP4 video file
        """
        self.video_file = Path(video_file)
        if not self.video_file.is_file():
            raise ValueError(f"Path must be a file: {self.video_file}")
        if self.video_file.suffix.lower() != ".mp4":
            raise ValueError(f"File must be MP4 format: {self.video_file}")

        self.logger = get_logger("sniffer.video")
        self.progress = ProgressLogger("sniffer.video.progress")

        # Initialize services
        self.metadata_service = VideoMetadataService()
        self.frame_service = FrameExtractionService()

        # Ensure output directories exist
        ensure_directory(AUDIO_PATH)
        ensure_directory(VIDEO_FRAMES_PATH)

    def extract_audio(self) -> str:
        """
        Extract audio from the video file.

        Returns:
            Path to extracted audio file
        """
        return self._extract_single_audio(self.video_file)

    def _extract_single_audio(self, video_path: Path) -> str:
        """Extract audio from a single video file."""
        self.logger.info(f"Extracting audio from: {video_path.name}")

        video_file_name = extract_filename_from_path(str(video_path))
        audio_file_name = f"{video_file_name}.mp3"
        audio_output_path = Path(AUDIO_PATH) / audio_file_name

        try:
            video_clip = mp.VideoFileClip(str(video_path))
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(str(audio_output_path), logger=None)
            audio_clip.close()
            video_clip.close()
            self.logger.info(f"Successfully extracted audio to: {audio_file_name}")
            return str(audio_output_path)
        except Exception as e:
            self.logger.error(f"Audio extraction failed for {video_path.name}: {e}")
            raise

    def extract_all_frames(self) -> list[str]:
        """
        Extract all frames from the video file.

        Returns:
            List of frame file paths
        """
        config = FrameExtractionConfig(video_path=self.video_file, extract_all=True)
        return self.frame_service.extract_all_frames(config)

    # Method moved to FrameExtractionService

    def extract_frames_by_position(self, position: str = "middle") -> dict[int, str]:
        """
        Extract one frame per second based on position within that second.

        Args:
            position: Position within each second ('start', 'middle', 'end', 'random')

        Returns:
            Dict mapping second -> frame_path
        """
        config = FrameExtractionConfig(video_path=self.video_file, position=position)
        return self.frame_service.extract_frames_by_position(config)

    # Methods moved to FrameExtractionService

    def get_video_metadata(self) -> dict:
        """
        Extract metadata from the video file.

        Returns:
            Dictionary containing video metadata
        """
        return self.metadata_service.extract_metadata(self.video_file)  # type: ignore[return-value]

    def process_all(
        self,
        extract_audio: bool = True,
        extract_all_frames: bool = False,
        frame_position: str | None = "middle",
    ) -> ProcessResults:
        """
        Process the video with specified operations.

        Args:
            extract_audio: Whether to extract audio
            extract_all_frames: Whether to extract all frames
            frame_position: Position for per-second frame extraction (None to skip)

        Returns:
            Dictionary with results for each operation
        """
        results: ProcessResults = {
            "processed_file": str(self.video_file),
        }

        if extract_audio:
            results["audio_path"] = self.extract_audio()

        if extract_all_frames:
            results["all_frames"] = self.extract_all_frames()

        if frame_position:
            results["position_frames"] = self.extract_frames_by_position(frame_position)

        return results
