"""
Services module for Sniffer video processing.

This module contains service classes that handle specific business logic
and can be composed by higher-level components.
"""

from .video_metadata import VideoMetadataService
from .frame_extraction import FrameExtractionService
from .video_capture import VideoCapture

__all__ = ["VideoMetadataService", "FrameExtractionService", "VideoCapture"]
