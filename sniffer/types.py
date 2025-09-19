"""
Type definitions for the sniffer package.
"""

from typing import TypedDict


class WordTimestamp(TypedDict):
    """Type definition for word-level timestamp data."""

    word: str
    start: float
    end: float
    second: int


class SegmentData(TypedDict):
    """Type definition for segment data."""

    text: str
    start: float
    end: float
    words: list[dict]


class FrameSyncData(TypedDict):
    """Type definition for frame synchronization data."""

    frame_timestamp: float
    spoken_word: str | None
    has_speech: bool


class ProcessResults(TypedDict, total=False):
    """Type definition for VideoProcessor.process_all() results."""

    processed_file: str
    audio_path: str
    all_frames: list[str]
    position_frames: dict[int, str]


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
