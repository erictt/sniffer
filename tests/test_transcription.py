"""
Tests for audio transcription functionality.
"""

import pytest
from unittest.mock import patch

from sniffer.transcription import AudioTranscriber


@pytest.fixture(autouse=True)
def mock_openai_api_key():
    """Mock OPENAI_API_KEY for all transcription tests."""
    with patch("sniffer.transcription.OPENAI_API_KEY", "test-api-key"):
        yield


class TestAudioTranscriberInitialization:
    """Test AudioTranscriber initialization."""

    def test_init_with_api_key(self, mock_audio_file):
        """Test initializing with API key."""
        transcriber = AudioTranscriber(mock_audio_file, api_key="test-key")
        assert transcriber.api_key == "test-key"
        assert transcriber.audio_file == mock_audio_file

    def test_init_with_env_api_key(self, mock_audio_file):
        """Test initializing with environment API key."""
        # The fixture sets 'test-api-key' as the default
        transcriber = AudioTranscriber(mock_audio_file)
        assert transcriber.api_key == "test-api-key"
        assert transcriber.audio_file == mock_audio_file

    def test_init_without_api_key(self, mock_audio_file):
        """Test initializing without API key raises error."""
        with patch("sniffer.transcription.OPENAI_API_KEY", None):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                AudioTranscriber(mock_audio_file)

    def test_init_explicit_key_overrides_env(self, mock_audio_file):
        """Test explicit API key overrides environment."""
        transcriber = AudioTranscriber(mock_audio_file, api_key="explicit-key")
        assert transcriber.api_key == "explicit-key"

    def test_init_with_missing_file(self, temp_dir):
        """Test initializing with missing audio file raises error."""
        missing_file = temp_dir / "missing.mp3"
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            AudioTranscriber(missing_file)


class TestTranscription:
    """Test transcription functionality."""

    def test_transcribe_success(
        self, mock_audio_file, mock_openai_client, set_openai_api_key
    ):
        """Test successful transcription with timestamps."""
        with patch("sniffer.transcription.OpenAI") as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            transcriber = AudioTranscriber(mock_audio_file)
            result = transcriber.transcribe()

            # Verify OpenAI client was called correctly
            mock_openai_client.audio.transcriptions.create.assert_called_once()
            call_args = mock_openai_client.audio.transcriptions.create.call_args

            assert call_args.kwargs["model"] == "whisper-1"
            assert call_args.kwargs["response_format"] == "verbose_json"
            assert call_args.kwargs["timestamp_granularities"] == ["word", "segment"]

            # Verify result
            assert "text" in result
            assert "words" in result
            assert "segments" in result

    def test_transcribe_custom_params(
        self, mock_audio_file, mock_openai_client, set_openai_api_key
    ):
        """Test transcription with custom parameters."""
        with patch("sniffer.transcription.OpenAI") as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            transcriber = AudioTranscriber(mock_audio_file)
            transcriber.transcribe(
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

            call_args = mock_openai_client.audio.transcriptions.create.call_args
            assert call_args.kwargs["response_format"] == "verbose_json"
            assert call_args.kwargs["timestamp_granularities"] == ["segment"]

    def test_transcribe_api_error(
        self, mock_audio_file, mock_openai_client, set_openai_api_key
    ):
        """Test handling API errors during transcription."""
        with patch("sniffer.transcription.OpenAI") as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client
            mock_openai_client.audio.transcriptions.create.side_effect = Exception(
                "API Error"
            )

            transcriber = AudioTranscriber(mock_audio_file)

            with pytest.raises(Exception, match="API Error"):
                transcriber.transcribe()


class TestWordTimestampExtraction:
    """Test word timestamp extraction."""

    def test_extract_word_timestamps(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test extracting word timestamps from transcript."""
        transcriber = AudioTranscriber(mock_audio_file)
        words = transcriber.extract_word_timestamps(sample_transcript)

        assert len(words) == 6
        assert words[0]["word"] == "Hello"
        assert words[0]["start"] == 0.0
        assert words[0]["end"] == 0.5

    def test_extract_word_timestamps_empty(self, mock_audio_file, set_openai_api_key):
        """Test extracting from transcript without words."""
        transcript = {"text": "test", "segments": []}
        transcriber = AudioTranscriber(mock_audio_file)
        words = transcriber.extract_word_timestamps(transcript)

        assert len(words) == 0


class TestSegmentExtraction:
    """Test segment extraction."""

    def test_extract_segments(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test extracting segments from transcript."""
        transcriber = AudioTranscriber(mock_audio_file)
        segments = transcriber.extract_segments(sample_transcript)

        assert len(segments) == 1
        assert segments[0]["text"] == "Hello world this is a test"
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 2.0

    def test_extract_segments_empty(self, mock_audio_file, set_openai_api_key):
        """Test extracting from transcript without segments."""
        transcript = {"text": "test", "words": []}
        transcriber = AudioTranscriber(mock_audio_file)
        segments = transcriber.extract_segments(transcript)

        assert len(segments) == 0


class TestTextAtTimestamp:
    """Test getting text at specific timestamp."""

    def test_get_text_at_timestamp_exact(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test getting text at exact timestamp."""
        transcriber = AudioTranscriber(mock_audio_file)
        word = transcriber.get_text_at_timestamp(sample_transcript, 0.75)

        assert word == "world"

    def test_get_text_at_timestamp_tolerance(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test getting text with tolerance."""
        transcriber = AudioTranscriber(mock_audio_file)
        word = transcriber.get_text_at_timestamp(sample_transcript, 0.4, tolerance=0.2)

        assert word == "Hello"

    def test_get_text_at_timestamp_no_match(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test getting text when no word matches."""
        transcriber = AudioTranscriber(mock_audio_file)
        word = transcriber.get_text_at_timestamp(sample_transcript, 10.0)

        assert word is None


class TestFrameSynchronization:
    """Test frame-audio synchronization."""

    def test_synchronize_with_frames(
        self, sample_transcript, mock_audio_file, set_openai_api_key
    ):
        """Test synchronizing transcript with frame timestamps."""
        transcriber = AudioTranscriber(mock_audio_file)
        frame_times = [0.25, 0.75, 1.25, 2.5]

        result = transcriber.synchronize_with_frames(sample_transcript, frame_times)

        assert len(result) == 4
        assert result[0]["frame_timestamp"] == 0.25
        assert result[0]["spoken_word"] == "Hello"
        assert result[0]["has_speech"] is True

        assert result[1]["frame_timestamp"] == 0.75
        assert result[1]["spoken_word"] == "world"

        assert result[3]["frame_timestamp"] == 2.5
        assert result[3]["spoken_word"] is None
        assert result[3]["has_speech"] is False
