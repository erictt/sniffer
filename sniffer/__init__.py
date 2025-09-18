"""
SunDogs - Video Processing and Transcription Library

A comprehensive library for processing video files to extract audio, frames,
and generate transcriptions with precise word-level timestamps.
"""

from .video_processor import VideoProcessor
from .transcription import AudioTranscriber
from .utils import (
    extract_filename_from_path,
    is_video_file,
    is_audio_file,
    ensure_directory,
    ensure_directories,
)

__version__ = "1.0.0"
__author__ = "SunDogs Team"

__all__ = [
    "VideoProcessor",
    "AudioTranscriber",
    "extract_filename_from_path",
    "is_video_file",
    "is_audio_file",
    "ensure_directory",
    "ensure_directories",
]
