"""
Video capture context manager for proper resource management.
"""

import cv2
from pathlib import Path
from typing import Optional
from ..utils.logging import get_logger


class VideoCapture:
    """Context manager for cv2.VideoCapture with proper resource cleanup."""

    def __init__(self, video_path: str | Path):
        self.video_path = str(video_path)
        self.cap: Optional[cv2.VideoCapture] = None
        self.logger = get_logger("sniffer.services.video_capture")

    def __enter__(self) -> cv2.VideoCapture:
        """Open video capture."""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        return self.cap

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if exc_type is not None:
            self.logger.error(f"Error during video capture: {exc_val}")

    @property
    def is_opened(self) -> bool:
        """Check if video capture is currently opened."""
        return self.cap is not None and self.cap.isOpened()
