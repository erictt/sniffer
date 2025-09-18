"""
Configuration constants for Sniffer video processing.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Directory paths for storing processed data
VIDEO_PATH: str = "data/video/"
AUDIO_PATH: str = "data/audio/"
VIDEO_FRAMES_PATH: str = "data/video_frames/"
TRANSCRIPTS_PATH: str = "data/transcripts/"
RESULTS_PATH: str = "data/results/"

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = os.getenv(
    "LOG_FORMAT",
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
LOG_FILE: str = os.getenv("LOG_FILE", "logs/sniffer.log")
LOG_ROTATION: str = os.getenv("LOG_ROTATION", "10 MB")
LOG_RETENTION: str = os.getenv("LOG_RETENTION", "10 days")
LOG_COLORIZE: bool = os.getenv("LOG_COLORIZE", "true").lower() == "true"

# OpenAI Configuration
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
