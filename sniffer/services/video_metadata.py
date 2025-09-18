"""
Video metadata extraction service.
"""

from typing import TypedDict
from pathlib import Path
import moviepy as mp
import cv2

from .video_capture import VideoCapture
from ..utils.logging import get_logger


class VideoMetadata(TypedDict):
    """Type definition for video metadata."""

    resolution: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float
    duration_clip: float
    codec: str
    file_size: int


class VideoMetadataService:
    """Service for extracting video metadata."""

    def __init__(self):
        self.logger = get_logger("sniffer.services.metadata")

    def extract_metadata(self, video_path: Path) -> VideoMetadata | dict:
        """
        Extract comprehensive metadata from video file.

        Args:
            video_path: Path to the video file

        Returns:
            VideoMetadata dictionary or error dictionary
        """
        try:
            # Extract basic metadata using OpenCV
            opencv_metadata = self._extract_opencv_metadata(video_path)

            # Extract additional metadata using moviepy
            moviepy_metadata = self._extract_moviepy_metadata(video_path)

            # Combine metadata
            return VideoMetadata(
                resolution=f"{opencv_metadata['width']}x{opencv_metadata['height']}",
                width=opencv_metadata["width"],
                height=opencv_metadata["height"],
                fps=round(opencv_metadata["fps"], 2),
                frame_count=opencv_metadata["frame_count"],
                duration=round(opencv_metadata["duration"], 2),
                duration_clip=round(moviepy_metadata["duration"], 2)
                if moviepy_metadata["duration"]
                else opencv_metadata["duration"],
                codec="MP4",  # Basic codec info since we only support MP4
                file_size=video_path.stat().st_size,
            )

        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {video_path.name}: {e}")
            return {
                "error": str(e),
                "file_size": video_path.stat().st_size if video_path.exists() else 0,
            }

    def _extract_opencv_metadata(self, video_path: Path) -> dict:
        """Extract metadata using OpenCV."""
        with VideoCapture(video_path) as cap:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            return {
                "fps": fps,
                "width": width,
                "height": height,
                "frame_count": frame_count,
                "duration": duration,
            }

    def _extract_moviepy_metadata(self, video_path: Path) -> dict:
        """Extract additional metadata using moviepy."""
        try:
            video_clip = mp.VideoFileClip(str(video_path))
            duration = video_clip.duration
            video_clip.close()

            return {"duration": duration}

        except Exception as e:
            self.logger.warning(f"Could not extract moviepy metadata: {e}")
            return {"duration": None}

    def get_basic_info(self, video_path: Path) -> tuple[float, int, float]:
        """
        Get essential video information for processing.

        Returns:
            Tuple of (fps, total_frames, duration_seconds)
        """
        with VideoCapture(video_path) as cap:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            return fps, total_frames, duration
