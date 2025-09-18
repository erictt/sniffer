"""
Configuration package for SunDogs video processing.

This package contains application constants and settings.
"""

from .constants import (
    VIDEO_PATH,
    AUDIO_PATH,
    VIDEO_FRAMES_PATH,
    TRANSCRIPTS_PATH,
    RESULTS_PATH,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
    LOG_ROTATION,
    LOG_RETENTION,
    LOG_COLORIZE,
    OPENAI_API_KEY,
)

__all__ = [
    "VIDEO_PATH",
    "AUDIO_PATH",
    "VIDEO_FRAMES_PATH",
    "TRANSCRIPTS_PATH",
    "RESULTS_PATH",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "LOG_FILE",
    "LOG_ROTATION",
    "LOG_RETENTION",
    "LOG_COLORIZE",
    "OPENAI_API_KEY",
]
