"""
Tests for video processing functionality.
"""

import pytest
from unittest.mock import patch, Mock

from sniffer.video_processor import VideoProcessor


class TestVideoProcessorInitialization:
    """Test VideoProcessor initialization."""

    def test_init_with_single_video(self, mock_video_file, mock_config):
        """Test initializing with single video file."""
        processor = VideoProcessor(mock_video_file)

        assert processor.video_file == mock_video_file

    def test_init_with_directory_raises_error(self, mock_video_directory, mock_config):
        """Test initializing with directory raises error."""
        video_dir, _ = mock_video_directory

        with pytest.raises(ValueError, match="Path must be a file"):
            VideoProcessor(video_dir)

    def test_init_with_non_mp4_file(self, temp_dir, mock_config):
        """Test initializing with non-MP4 file raises error."""
        non_video_file = temp_dir / "test.txt"
        non_video_file.write_text("not a video")

        with pytest.raises(ValueError, match="File must be MP4 format"):
            VideoProcessor(non_video_file)

    def test_init_with_missing_path(self, temp_dir, mock_config):
        """Test initializing with missing path raises error."""
        missing_path = temp_dir / "missing.mp4"

        with pytest.raises(ValueError, match="Path must be a file"):
            VideoProcessor(missing_path)


class TestAudioExtraction:
    """Test audio extraction functionality."""

    @patch("sniffer.video_processor.mp.VideoFileClip")
    def test_extract_audio_single_video(
        self, mock_video_clip, mock_video_file, mock_config
    ):
        """Test extracting audio from single video."""
        # Setup mocks
        mock_clip_instance = Mock()
        mock_audio_clip = Mock()
        mock_clip_instance.audio = mock_audio_clip
        mock_video_clip.return_value = mock_clip_instance

        processor = VideoProcessor(mock_video_file)
        result = processor.extract_audio()

        # Verify calls
        mock_video_clip.assert_called_once_with(str(mock_video_file))
        mock_audio_clip.write_audiofile.assert_called_once()
        mock_audio_clip.close.assert_called_once()
        mock_clip_instance.close.assert_called_once()

        # Verify result
        assert isinstance(result, str)
        assert result.endswith(".mp3")

    @patch("sniffer.video_processor.mp.VideoFileClip")
    def test_extract_audio_failure(self, mock_video_clip, mock_video_file, mock_config):
        """Test audio extraction failure handling."""
        # Setup mock to raise exception
        mock_video_clip.side_effect = Exception("Video processing error")

        processor = VideoProcessor(mock_video_file)

        with pytest.raises(Exception, match="Video processing error"):
            processor.extract_audio()


class TestFrameExtraction:
    """Test frame extraction functionality."""

    @patch("sniffer.video_processor.cv2.VideoCapture")
    @patch("sniffer.video_processor.cv2.imwrite")
    def test_extract_all_frames(
        self, mock_imwrite, mock_video_capture, mock_video_file, mock_config
    ):
        """Test extracting all frames from video."""
        # Setup mock video capture
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            # cv2.CAP_PROP_FPS
            5: 30.0,
            # cv2.CAP_PROP_FRAME_WIDTH
            3: 640,
            # cv2.CAP_PROP_FRAME_HEIGHT
            4: 480,
            # cv2.CAP_PROP_FRAME_COUNT
            7: 90,
            # cv2.CAP_PROP_POS_MSEC
            0: 0,  # Will be incremented in real implementation
        }.get(prop, 0)

        # Mock frame reading - return 3 frames then False
        call_count = 0

        def mock_read():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return True, "mock_frame"
            return False, None

        mock_cap.read = mock_read
        mock_imwrite.return_value = True

        processor = VideoProcessor(mock_video_file)
        result = processor.extract_all_frames()

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 3
        assert mock_imwrite.call_count == 3

    @patch("sniffer.video_processor.cv2.VideoCapture")
    def test_extract_all_frames_invalid_video(
        self, mock_video_capture, mock_video_file, mock_config
    ):
        """Test extracting frames from invalid video."""
        # Setup mock to fail opening
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False

        processor = VideoProcessor(mock_video_file)

        with pytest.raises(ValueError, match="Could not open video file"):
            processor.extract_all_frames()


class TestFramesByPosition:
    """Test frame extraction by position."""

    @patch("sniffer.video_processor.cv2.VideoCapture")
    @patch("sniffer.video_processor.cv2.imwrite")
    def test_extract_frames_by_position_middle(
        self, mock_imwrite, mock_video_capture, mock_video_file, mock_config
    ):
        """Test extracting frames at middle position per second."""
        # Setup mock video capture
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            5: 30.0,  # FPS
            7: 90,  # Total frames (3 seconds)
        }.get(prop, 0)

        # Mock successful frame reading
        mock_cap.read.return_value = (True, "mock_frame")
        mock_cap.set.return_value = True
        mock_imwrite.return_value = True

        processor = VideoProcessor(mock_video_file)
        result = processor.extract_frames_by_position("middle")

        # Verify result - should have frames for 3 seconds
        assert isinstance(result, dict)
        assert len(result) == 3
        assert 0 in result
        assert 1 in result
        assert 2 in result

    def test_extract_frames_invalid_position(self, mock_video_file, mock_config):
        """Test extracting frames with invalid position."""
        processor = VideoProcessor(mock_video_file)

        with pytest.raises(ValueError, match="Invalid position"):
            processor.extract_frames_by_position("invalid")

    @pytest.mark.parametrize("position", ["start", "middle", "end", "random"])
    def test_extract_frames_all_positions(self, position, mock_video_file, mock_config):
        """Test all valid position options."""
        with (
            patch("sniffer.video_processor.cv2.VideoCapture") as mock_capture,
            patch("sniffer.video_processor.cv2.imwrite") as mock_imwrite,
        ):
            # Setup mocks
            mock_cap = Mock()
            mock_capture.return_value = mock_cap
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {5: 30.0, 7: 60}.get(prop, 0)
            mock_cap.read.return_value = (True, "mock_frame")
            mock_imwrite.return_value = True

            processor = VideoProcessor(mock_video_file)
            result = processor.extract_frames_by_position(position)

            assert isinstance(result, dict)
            assert len(result) == 2  # 2 seconds of video


class TestProcessAll:
    """Test complete processing functionality."""

    def test_process_all_audio_only(self, mock_video_file, mock_config):
        """Test processing with audio extraction only."""
        with patch("sniffer.video_processor.mp.VideoFileClip"):
            processor = VideoProcessor(mock_video_file)
            result = processor.process_all(
                extract_audio=True, extract_all_frames=False, frame_position=None
            )

            assert "processed_file" in result
            assert "audio_path" in result

    def test_process_all_complete(self, mock_video_file, mock_config):
        """Test complete processing with all options."""
        with (
            patch("sniffer.video_processor.mp.VideoFileClip"),
            patch("sniffer.video_processor.cv2.VideoCapture") as mock_capture,
            patch("sniffer.video_processor.cv2.imwrite"),
        ):
            # Setup video capture mock
            mock_cap = Mock()
            mock_capture.return_value = mock_cap
            mock_cap.isOpened.return_value = True
            mock_cap.get.side_effect = lambda prop: {5: 30.0, 7: 60}.get(prop, 0)
            mock_cap.read.return_value = (True, "mock_frame")
            mock_cap.set.return_value = True  # Mock the cap.set() method

            processor = VideoProcessor(mock_video_file)
            result = processor.process_all(
                extract_audio=True,
                extract_all_frames=False,  # Disable to avoid hang
                frame_position="middle",
            )

            assert "processed_file" in result
            assert "audio_path" in result
            assert "position_frames" in result
