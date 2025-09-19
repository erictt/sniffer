"""
Tests for main CLI functionality.
"""

from typer.testing import CliRunner
from unittest.mock import patch, Mock

from sniffer.main import app


runner = CliRunner()


class TestCLICommands:
    """Test CLI command functionality."""

    def test_help_command(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Video Content Extraction Tool" in result.stdout

    def test_setup_command(self):
        """Test setup command."""
        with patch("sniffer.main.ensure_directories") as mock_ensure:
            result = runner.invoke(app, ["setup"])
            assert result.exit_code == 0
            mock_ensure.assert_called_once()

    def test_setup_command_with_api_key(self):
        """Test setup command with API key present."""
        with (
            patch("sniffer.main.ensure_directories"),
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
        ):
            result = runner.invoke(app, ["setup"])
            assert result.exit_code == 0
            assert "Found" in result.stdout

    def test_setup_command_without_api_key(self):
        """Test setup command without API key."""
        with (
            patch("sniffer.main.ensure_directories"),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = runner.invoke(app, ["setup"])
            assert result.exit_code == 0
            assert "Missing" in result.stdout


class TestProcessCommand:
    """Test process command functionality."""

    def test_process_command_help(self):
        """Test process command help."""
        result = runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process video files" in result.stdout

    @patch("sniffer.main.get_video_files")
    def test_process_missing_input(self, mock_get_video_files):
        """Test process command with missing input."""
        mock_get_video_files.side_effect = ValueError(
            "Path not found: /nonexistent/path"
        )

        result = runner.invoke(app, ["process", "/nonexistent/path"])
        assert result.exit_code == 1
        assert "Path not found" in result.stdout

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.cli.process_handler.VideoProcessor")
    def test_process_single_video_audio_only(
        self, mock_processor, mock_get_video_files, temp_dir
    ):
        """Test processing single video with audio only."""
        # Create test video file
        test_video = temp_dir / "test.mp4"
        test_video.touch()

        # Setup mocks
        mock_get_video_files.return_value = [test_video]

        mock_instance = Mock()
        mock_instance.process_all.return_value = {
            "processed_file": str(test_video),
            "audio_path": str(temp_dir / "audio.mp3"),
        }
        mock_processor.return_value = mock_instance

        result = runner.invoke(app, ["process", str(test_video)])
        assert result.exit_code == 0

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.cli.process_handler.VideoProcessor")
    @patch("sniffer.cli.process_handler.SyncService")
    def test_process_with_frames(
        self, mock_sync_service, mock_processor, mock_get_video_files, temp_dir
    ):
        """Test processing with frame extraction."""
        test_video = temp_dir / "test.mp4"
        test_video.touch()

        mock_get_video_files.return_value = [test_video]

        # Mock VideoProcessor
        mock_instance = Mock()
        mock_instance.process_all.return_value = {
            "processed_file": str(test_video),
            "audio_path": str(temp_dir / "audio.mp3"),
            "position_frames": {0: str(temp_dir / "frame_0.png")},
        }
        mock_instance.get_video_metadata.return_value = {
            "duration": 10.0,
            "resolution": "1920x1080",
            "fps": 30.0,
            "frame_count": 300,
        }
        mock_processor.return_value = mock_instance

        # Mock sync service
        mock_sync_service.return_value.create_frame_transcript_table.return_value = []
        mock_sync_service.return_value.get_sync_statistics.return_value = {}

        result = runner.invoke(app, ["process", str(test_video), "--frames", "middle"])
        assert result.exit_code == 0

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.cli.process_handler.VideoProcessor")
    @patch("sniffer.cli.process_handler.AudioTranscriber")
    def test_process_with_transcription(
        self, mock_transcriber, mock_processor, mock_get_video_files, temp_dir
    ):
        """Test processing with transcription."""
        test_video = temp_dir / "test.mp4"
        test_video.touch()

        # Setup mocks
        mock_get_video_files.return_value = [test_video]

        mock_video_instance = Mock()
        mock_video_instance.process_all.return_value = {
            "processed_file": str(test_video),
            "audio_path": str(temp_dir / "audio.mp3"),
        }
        mock_processor.return_value = mock_video_instance

        # Setup transcriber mock
        mock_transcriber_instance = Mock()
        mock_transcriber_instance.transcribe.return_value = {
            "text": "test transcription",
            "words": [],
        }
        mock_transcriber.return_value = mock_transcriber_instance

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            result = runner.invoke(app, ["process", str(test_video), "--transcribe"])
            assert result.exit_code == 0

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.cli.process_handler.VideoProcessor")
    def test_process_verbose_mode(self, mock_processor, mock_get_video_files, temp_dir):
        """Test processing in verbose mode."""
        test_video = temp_dir / "test.mp4"
        test_video.touch()

        mock_get_video_files.return_value = [test_video]

        mock_instance = Mock()
        mock_instance.process_all.return_value = {
            "processed_file": str(test_video),
            "audio_path": str(temp_dir / "audio.mp3"),
        }
        mock_processor.return_value = mock_instance

        result = runner.invoke(app, ["process", str(test_video), "--verbose"])
        assert result.exit_code == 0

    def test_process_error_handling(self, temp_dir):
        """Test process command error handling."""
        # Test with non-existent path
        non_existent_path = temp_dir / "non_existent.mp4"

        result = runner.invoke(app, ["process", str(non_existent_path)])
        assert result.exit_code == 1
        assert "Path not found" in result.stdout


class TestInfoCommand:
    """Test info command functionality."""

    def test_info_command_help(self):
        """Test info command help."""
        result = runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0
        assert "Show information about video files" in result.stdout

    @patch("sniffer.main.get_video_files")
    def test_info_missing_path(self, mock_get_video_files):
        """Test info command with missing path."""
        mock_get_video_files.side_effect = ValueError(
            "Path not found: /nonexistent/path"
        )

        result = runner.invoke(app, ["info", "/nonexistent/path"])
        assert result.exit_code == 1
        assert "Path not found" in result.stdout

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.video_processor.VideoProcessor")
    def test_info_single_video(self, mock_processor, mock_get_video_files, temp_dir):
        """Test info command with single video."""
        test_video = temp_dir / "test.mp4"
        test_video.write_text("fake video content")  # Add some content for size

        mock_get_video_files.return_value = [test_video]

        mock_instance = Mock()
        mock_instance.get_video_metadata.return_value = {
            "resolution": "1920x1080",
            "fps": 30.0,
            "duration": 10.5,
            "frame_count": 315,
            "file_size": 1000000,
        }
        mock_processor.return_value = mock_instance

        result = runner.invoke(app, ["info", str(test_video)])
        assert result.exit_code == 0
        assert "test.mp4" in result.stdout

    @patch("sniffer.main.get_video_files")
    @patch("sniffer.video_processor.VideoProcessor")
    def test_info_multiple_videos(self, mock_processor, mock_get_video_files, temp_dir):
        """Test info command with multiple videos."""
        video_files = []
        for i in range(3):
            video_file = temp_dir / f"test_{i}.mp4"
            video_file.write_text(f"fake video content {i}")
            video_files.append(video_file)

        mock_get_video_files.return_value = video_files

        mock_instance = Mock()
        mock_instance.get_video_metadata.return_value = {
            "resolution": "1920x1080",
            "fps": 30.0,
            "duration": 10.5,
            "frame_count": 315,
            "file_size": 1000000,
        }
        mock_processor.return_value = mock_instance

        result = runner.invoke(app, ["info", str(temp_dir)])
        assert result.exit_code == 0
        assert "3 files" in result.stdout

    @patch("sniffer.main.get_video_files")
    def test_info_error_handling(self, mock_get_video_files, temp_dir):
        """Test info command error handling."""
        test_video = temp_dir / "test.mp4"
        test_video.touch()

        mock_get_video_files.side_effect = Exception("Info error")

        result = runner.invoke(app, ["info", str(test_video)])
        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestUtilityFunctions:
    """Test utility functions in main module."""

    def test_format_size_function(self):
        """Test file size formatting function."""
        from sniffer.utils.file import format_file_size

        assert format_file_size(0) == "0B"
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1048576) == "1.0MB"
        assert format_file_size(1073741824) == "1.0GB"
