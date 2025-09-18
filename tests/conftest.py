"""
Pytest configuration and shared fixtures.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import cv2
import numpy as np


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_video_file(temp_dir):
    """Create a mock MP4 video file for testing."""
    video_path = temp_dir / "test_video.mp4"

    # Create a simple test video using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(
        str(video_path),
        fourcc,
        30.0,  # 30 FPS
        (640, 480),  # Resolution
    )

    # Create 150 frames (5 seconds at 30 FPS)
    for i in range(150):
        # Create a simple colored frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = (i * 5) % 255  # Blue channel changes over time
        frame[:, :, 1] = 100  # Green constant
        frame[:, :, 2] = 200  # Red constant

        video_writer.write(frame)

    video_writer.release()
    return video_path


@pytest.fixture
def mock_video_directory(temp_dir):
    """Create a directory with multiple mock video files."""
    video_files = []
    for i in range(3):
        video_path = temp_dir / f"test_video_{i}.mp4"

        # Create simple test videos
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(
            str(video_path),
            fourcc,
            24.0,  # 24 FPS
            (320, 240),  # Smaller resolution
        )

        # Create 48 frames (2 seconds at 24 FPS)
        for frame_num in range(48):
            frame = np.full((240, 320, 3), (i * 80, frame_num * 5, 150), dtype=np.uint8)
            video_writer.write(frame)

        video_writer.release()
        video_files.append(video_path)

    return temp_dir, video_files


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing."""
    audio_path = temp_dir / "test_audio.mp3"
    # Create a simple empty audio file for testing
    audio_path.touch()
    return audio_path


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for transcription testing."""
    mock_client = Mock()

    # Mock transcription response
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "text": "This is a test transcription",
        "words": [
            {"word": "This", "start": 0.0, "end": 0.5},
            {"word": "is", "start": 0.5, "end": 0.7},
            {"word": "a", "start": 0.7, "end": 0.8},
            {"word": "test", "start": 0.8, "end": 1.2},
            {"word": "transcription", "start": 1.2, "end": 2.0},
        ],
        "segments": [
            {
                "text": "This is a test transcription",
                "start": 0.0,
                "end": 2.0,
                "words": [
                    {"word": "This", "start": 0.0, "end": 0.5},
                    {"word": "is", "start": 0.5, "end": 0.7},
                    {"word": "a", "start": 0.7, "end": 0.8},
                    {"word": "test", "start": 0.8, "end": 1.2},
                    {"word": "transcription", "start": 1.2, "end": 2.0},
                ],
            }
        ],
    }

    mock_client.audio.transcriptions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "Hello world this is a test",
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
            {"word": "this", "start": 1.0, "end": 1.3},
            {"word": "is", "start": 1.3, "end": 1.5},
            {"word": "a", "start": 1.5, "end": 1.6},
            {"word": "test", "start": 1.6, "end": 2.0},
        ],
        "segments": [
            {
                "text": "Hello world this is a test",
                "start": 0.0,
                "end": 2.0,
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5},
                    {"word": "world", "start": 0.5, "end": 1.0},
                    {"word": "this", "start": 1.0, "end": 1.3},
                    {"word": "is", "start": 1.3, "end": 1.5},
                    {"word": "a", "start": 1.5, "end": 1.6},
                    {"word": "test", "start": 1.6, "end": 2.0},
                ],
            }
        ],
    }


@pytest.fixture
def mock_config(temp_dir, monkeypatch):
    """Mock configuration paths to use temporary directory."""
    monkeypatch.setattr("sniffer.config.VIDEO_PATH", str(temp_dir / "video"))
    monkeypatch.setattr("sniffer.config.AUDIO_PATH", str(temp_dir / "audio"))
    monkeypatch.setattr("sniffer.config.VIDEO_FRAMES_PATH", str(temp_dir / "frames"))
    monkeypatch.setattr(
        "sniffer.config.TRANSCRIPTS_PATH", str(temp_dir / "transcripts")
    )

    # Create the directories
    (temp_dir / "video").mkdir()
    (temp_dir / "audio").mkdir()
    (temp_dir / "frames").mkdir()
    (temp_dir / "transcripts").mkdir()


@pytest.fixture
def set_openai_api_key(monkeypatch):
    """Set a mock OpenAI API key for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-12345")
