"""
Essential tests for file utility functions.
"""

import pytest
from pathlib import Path

from sniffer.utils.file import (
    extract_filename_from_path,
    get_file_extension,
    is_video_file,
    is_audio_file,
    ensure_file_exists,
    format_file_size,
)


class TestFileUtils:
    """Test core file utility functions."""

    def test_extract_filename_from_path(self):
        """Test filename extraction."""
        assert extract_filename_from_path("/path/to/video.mp4") == "video"
        assert extract_filename_from_path(Path("/path/to/document.pdf")) == "document"

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert get_file_extension("/path/to/video.mp4") == ".mp4"
        assert get_file_extension(Path("/path/to/file")) == ""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("video.mp4", True),
            ("movie.avi", True),
            ("VIDEO.MP4", True),  # Case insensitive
            ("audio.mp3", False),
            ("document.pdf", False),
        ],
    )
    def test_is_video_file(self, filename, expected):
        """Test video file detection."""
        assert is_video_file(filename) == expected

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("audio.mp3", True),
            ("sound.wav", True),
            ("AUDIO.MP3", True),  # Case insensitive
            ("video.mp4", False),
            ("document.pdf", False),
        ],
    )
    def test_is_audio_file(self, filename, expected):
        """Test audio file detection."""
        assert is_audio_file(filename) == expected

    def test_ensure_file_exists(self, temp_dir):
        """Test file existence checking."""
        # Valid file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert ensure_file_exists(test_file) is True

        # Missing file
        missing_file = temp_dir / "missing.txt"
        with pytest.raises(FileNotFoundError):
            ensure_file_exists(missing_file)

    @pytest.mark.parametrize(
        "size_bytes,expected",
        [
            (0, "0B"),
            (1024, "1.0KB"),
            (1048576, "1.0MB"),
            (1073741824, "1.0GB"),
        ],
    )
    def test_format_file_size(self, size_bytes, expected):
        """Test file size formatting."""
        assert format_file_size(size_bytes) == expected
