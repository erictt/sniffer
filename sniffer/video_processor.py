"""
Video processing module for extracting audio and frames from video files.
Supports both single file and batch processing of MP4 files.
"""

from typing import Optional, TypedDict
from pathlib import Path
import moviepy as mp
import cv2
import random
import math

from .config.constants import AUDIO_PATH, VIDEO_FRAMES_PATH
from .utils.directory import ensure_directory
from .utils.file import extract_filename_from_path
from .utils.logging import get_logger, ProgressLogger


class ProcessResults(TypedDict, total=False):
    """Type definition for VideoProcessor.process_all() results."""
    processed_files: list[str]
    audio_paths: list[str]
    all_frames: dict[str, list[str]]
    position_frames: dict[str, dict[int, str]]
    transcripts: dict[str, dict]


class VideoProcessor:
    """
    A class for processing video files to extract audio and frames.
    Supports both single file and batch processing.
    """

    def __init__(self, video_input: str | Path):
        """
        Initialize VideoProcessor with a video file or directory path.

        Args:
            video_input: Path to a video file or directory containing MP4 files
        """
        self.video_input = Path(video_input)
        self.video_files = self._get_video_files()
        self.logger = get_logger("sniffer.video")
        self.progress = ProgressLogger("sniffer.video.progress")

        # Ensure output directories exist
        ensure_directory(AUDIO_PATH)
        ensure_directory(VIDEO_FRAMES_PATH)

    def _get_video_files(self) -> list[Path]:
        """Get list of video files to process."""
        if self.video_input.is_file():
            if self.video_input.suffix.lower() == ".mp4":
                return [self.video_input]
            else:
                raise ValueError(f"File must be MP4 format: {self.video_input}")
        elif self.video_input.is_dir():
            mp4_files = list(self.video_input.glob("*.mp4"))
            if not mp4_files:
                raise ValueError(f"No MP4 files found in directory: {self.video_input}")
            return sorted(mp4_files)
        else:
            raise ValueError(f"Path does not exist: {self.video_input}")

    def extract_audio(self, video_path: Optional[Path] = None) -> list[str]:
        """
        Extract audio from video file(s).

        Args:
            video_path: Specific video file to process (optional for single file mode)

        Returns:
            Path to extracted audio file(s)
        """
        if video_path:
            return [self._extract_single_audio(video_path)]

        # Always return a list, even for single files
        audio_paths = []
        for video_file in self.video_files:
            audio_path = self._extract_single_audio(video_file)
            audio_paths.append(audio_path)
        return audio_paths

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

    def extract_all_frames(
        self, video_path: Optional[Path] = None
    ) -> dict[str, list[str]]:
        """
        Extract all frames from video file(s).

        Args:
            video_path: Specific video file to process (optional for single file mode)

        Returns:
            List of frame file paths for single video, or dict mapping video names to frame paths
        """
        if video_path:
            frames = self._extract_all_frames_single(video_path)
            return {video_path.name: frames}

        # Always return a dict, even for single files
        all_frames = {}
        for video_file in self.video_files:
            frames = self._extract_all_frames_single(video_file)
            all_frames[video_file.name] = frames
        return all_frames

    def _extract_all_frames_single(self, video_path: Path) -> list[str]:
        """Extract all frames from a single video file."""
        self.logger.info(f"Extracting all frames from: {video_path.name}")

        video_file_name = extract_filename_from_path(str(video_path))
        video_frame_path = Path(VIDEO_FRAMES_PATH) / video_file_name
        ensure_directory(str(video_frame_path))

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        # Get video metadata
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = frame_count_total / fps if fps > 0 else 0

        self.logger.info(
            f"Video Metadata - Resolution: {width}x{height}, FPS: {fps:.2f}, "
            f"Frames: {frame_count_total}, Duration: {duration_seconds:.2f}s"
        )

        frame_paths = []
        extracted_count = 0

        while True:
            success, frame = cap.read()
            if not success:
                break

            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            timestamp_str = str(int(timestamp_ms)).zfill(8)

            frame_filename = video_frame_path / f"frame_ts_{timestamp_str}.png"
            cv2.imwrite(str(frame_filename), frame)
            frame_paths.append(str(frame_filename))
            extracted_count += 1

            if extracted_count % 100 == 0:
                self.progress.progress_update(
                    "Frame extraction", extracted_count, frame_count_total
                )

        cap.release()
        self.logger.info(f"Successfully extracted {extracted_count} frames")
        return frame_paths

    def extract_frames_by_position(
        self, position: str = "middle", video_path: Optional[Path] = None
    ) -> dict[str, dict[int, str]]:
        """
        Extract one frame per second based on position within that second.

        Args:
            position: Position within each second ('start', 'middle', 'end', 'random')
            video_path: Specific video file to process (optional for single file mode)

        Returns:
            Dict mapping second -> frame_path for single video, or nested dict for batch
        """
        valid_positions = ["start", "middle", "end", "random"]
        if position not in valid_positions:
            raise ValueError(
                f"Invalid position '{position}'. Must be one of {valid_positions}"
            )

        if video_path:
            frames = self._extract_frames_by_position_single(video_path, position)
            return {video_path.name: frames}

        # Always return a dict, even for single files
        all_frames = {}
        for video_file in self.video_files:
            frames = self._extract_frames_by_position_single(video_file, position)
            all_frames[video_file.name] = frames
        return all_frames

    def _extract_frames_by_position_single(
        self, video_path: Path, position: str
    ) -> dict[int, str]:
        """Extract frames by position from a single video file."""
        self.logger.info(
            f"Extracting {position} frames per second from: {video_path.name}"
        )

        video_file_name = extract_filename_from_path(str(video_path))
        video_frame_path = Path(VIDEO_FRAMES_PATH) / video_file_name
        ensure_directory(str(video_frame_path))

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        # Get video metadata
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps == 0:
            cap.release()
            raise ValueError("Video FPS is 0. Cannot process.")

        duration_seconds = total_frames / fps
        cap.release()

        # Calculate timestamps for each second
        timestamps = self._calculate_timestamps_per_second(
            duration_seconds, fps, position
        )

        # Extract frames at calculated timestamps
        return self._fetch_frames_by_timestamp(video_path, str(video_frame_path), timestamps)

    def _calculate_timestamps_per_second(
        self, duration_seconds: float, fps: float, position: str
    ) -> list[tuple]:
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
        self, video_path: Path, output_dir: str, timestamps: list[tuple]
    ) -> dict[int, str]:
        """Fetch and save frames at specific timestamps."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        extracted_frames = {}

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

        cap.release()
        self.logger.info(f"Successfully extracted {len(extracted_frames)} frames")
        return extracted_frames

    def get_video_files(self) -> list[Path]:
        """Get list of video files that will be processed."""
        return self.video_files

    def process_all(
        self,
        extract_audio: bool = True,
        extract_all_frames: bool = False,
        frame_position: Optional[str] = "middle",
    ) -> ProcessResults:
        """
        Process all videos with specified operations.

        Args:
            extract_audio: Whether to extract audio
            extract_all_frames: Whether to extract all frames
            frame_position: Position for per-second frame extraction (None to skip)

        Returns:
            Dictionary with results for each operation
        """
        results: ProcessResults = {
            "processed_files": [str(f) for f in self.video_files],
            "audio_paths": [],
            "all_frames": {},
            "position_frames": {},
        }

        if extract_audio:
            results["audio_paths"] = self.extract_audio()

        if extract_all_frames:
            results["all_frames"] = self.extract_all_frames()

        if frame_position:
            results["position_frames"] = self.extract_frames_by_position(frame_position)

        return results
