"""
Frame extraction service for video processing.
"""

from pathlib import Path
import cv2
import random
import math

from .video_capture import VideoCapture
from ..utils.logging import get_logger, ProgressLogger
from ..utils.directory import ensure_directory
from ..utils.file import extract_filename_from_path
from ..config.constants import VIDEO_FRAMES_PATH


class FrameExtractionConfig:
    """Configuration for frame extraction."""

    def __init__(
        self,
        video_path: str | Path,
        position: str | None = None,
        extract_all: bool = False,
        output_dir: str | None = None,
    ) -> None:
        self.video_path = Path(video_path)
        self.position = position
        self.extract_all = extract_all
        self.output_dir = output_dir or self._default_output_dir()

    def _default_output_dir(self) -> str:
        """Generate default output directory based on video filename."""
        video_file_name = extract_filename_from_path(str(self.video_path))
        return str(Path(VIDEO_FRAMES_PATH) / video_file_name)


class FrameExtractionService:
    """Service for extracting frames from video files."""

    def __init__(self) -> None:
        self.logger = get_logger("sniffer.services.frames")
        self.progress = ProgressLogger("sniffer.services.frames.progress")

    def extract_all_frames(self, config: FrameExtractionConfig) -> list[str]:
        """
        Extract all frames from video file.

        Args:
            config: Frame extraction configuration

        Returns:
            List of frame file paths
        """
        self.logger.info(f"Extracting all frames from: {config.video_path.name}")

        ensure_directory(config.output_dir)

        frame_paths = []
        extracted_count = 0

        with VideoCapture(config.video_path) as cap:
            # Log video metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_seconds = frame_count_total / fps if fps > 0 else 0

            self.logger.info(
                f"Video Metadata - Resolution: {width}x{height}, FPS: {fps:.2f}, "
                f"Frames: {frame_count_total}, Duration: {duration_seconds:.2f}s"
            )

            while True:
                success, frame = cap.read()
                if not success:
                    break

                timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                timestamp_str = str(int(timestamp_ms)).zfill(8)

                frame_filename = (
                    Path(config.output_dir) / f"frame_ts_{timestamp_str}.png"
                )
                cv2.imwrite(str(frame_filename), frame)
                frame_paths.append(str(frame_filename))
                extracted_count += 1

                if extracted_count % 100 == 0:
                    self.progress.progress_update(
                        "Frame extraction", extracted_count, frame_count_total
                    )

        self.logger.info(f"Successfully extracted {extracted_count} frames")
        return frame_paths

    def extract_frames_by_position(
        self, config: FrameExtractionConfig
    ) -> dict[int, str]:
        """
        Extract one frame per second based on position within that second.

        Args:
            config: Frame extraction configuration with position specified

        Returns:
            Dict mapping second -> frame_path
        """
        if not config.position:
            raise ValueError("Position must be specified for position-based extraction")

        valid_positions = ["start", "middle", "end", "random"]
        if config.position not in valid_positions:
            raise ValueError(
                f"Invalid position '{config.position}'. Must be one of {valid_positions}"
            )

        self.logger.info(
            f"Extracting {config.position} frames per second from: {config.video_path.name}"
        )

        ensure_directory(config.output_dir)

        # Get video information
        fps, total_frames, duration_seconds = self._get_video_info(config.video_path)

        if fps == 0:
            raise ValueError("Video FPS is 0. Cannot process.")

        # Calculate timestamps for each second
        timestamps = self._calculate_timestamps_per_second(
            duration_seconds, fps, config.position
        )

        # Extract frames at calculated timestamps
        return self._fetch_frames_by_timestamp(
            config.video_path, config.output_dir, timestamps
        )

    def _get_video_info(self, video_path: Path) -> tuple[float, int, float]:
        """Get basic video information."""
        with VideoCapture(video_path) as cap:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_seconds = total_frames / fps

            return fps, total_frames, duration_seconds

    def _calculate_timestamps_per_second(
        self, duration_seconds: float, fps: float, position: str
    ) -> list[tuple[int, int]]:
        """Calculate millisecond timestamps for frame extraction."""
        timestamps = []

        for second in range(math.ceil(duration_seconds)):
            start_ms = second * 1000
            end_ms = min((second + 1) * 1000, duration_seconds * 1000)

            target_ms: float
            match position:
                case "start":
                    target_ms = float(start_ms)
                case "middle":
                    target_ms = start_ms + (end_ms - start_ms) / 2
                case "end":
                    target_ms = max(float(start_ms), end_ms - (1000 / fps))
                case "random":
                    target_ms = random.uniform(start_ms, end_ms)
                case _:
                    raise ValueError(
                        f"Invalid position '{position}'. Must be one of: start, middle, end, random"
                    )

            timestamps.append((second, int(target_ms)))

        return timestamps

    def _fetch_frames_by_timestamp(
        self, video_path: Path, output_dir: str, timestamps: list[tuple[int, int]]
    ) -> dict[int, str]:
        """Fetch and save frames at specific timestamps."""
        extracted_frames = {}

        with VideoCapture(video_path) as cap:
            for second, ms in timestamps:
                cap.set(cv2.CAP_PROP_POS_MSEC, ms)
                success, frame = cap.read()

                if success:
                    frame_filename = Path(output_dir) / f"frame_s{second}_{ms}ms.png"
                    cv2.imwrite(str(frame_filename), frame)
                    extracted_frames[second] = str(frame_filename)
                else:
                    self.logger.warning(
                        f"Failed to fetch frame for second {second} at {ms}ms"
                    )

        self.logger.info(f"Successfully extracted {len(extracted_frames)} frames")
        return extracted_frames
