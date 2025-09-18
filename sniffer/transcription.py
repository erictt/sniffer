"""
Audio transcription module using OpenAI's Whisper API for precise word-level timestamps.
"""

from typing import Optional
from pathlib import Path
import json

from openai import OpenAI
from .utils.logging import get_logger, ProgressLogger
from .config.constants import OPENAI_API_KEY


class AudioTranscriber:
    """
    A class for transcribing a single audio file using OpenAI's Whisper API.
    Provides word-level timestamps for precise audio-text alignment.
    """

    def __init__(self, audio_file: str | Path, api_key: Optional[str] = None):
        """
        Initialize AudioTranscriber with a single audio file and OpenAI API key.

        Args:
            audio_file: Path to the audio file to transcribe
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY from config)
        """
        self.audio_file = Path(audio_file)
        if not self.audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")

        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in .env file or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.logger = get_logger("sniffer.transcription")
        self.progress = ProgressLogger("sniffer.transcription.progress")

    def transcribe(
        self,
        response_format: str = "verbose_json",
        timestamp_granularities: list[str] | None = None,
        save_transcript: bool = True,
        output_dir: Optional[str] = None,
    ) -> dict:
        """
        Transcribe the audio file with word-level timestamps.

        Args:
            response_format: Format for transcription response ("verbose_json" for timestamps)
            timestamp_granularities: List of granularities ("word", "segment")
            save_transcript: Whether to save transcript as JSON file
            output_dir: Directory to save transcript file (default: data/transcripts/)

        Returns:
            Dictionary containing transcription with word-level timestamps
        """
        if timestamp_granularities is None:
            timestamp_granularities = ["word", "segment"]

        self.logger.info(f"Transcribing audio: {self.audio_file.name}")

        try:
            with open(self.audio_file, "rb") as audio_file:
                # Use verbose_json format when timestamp_granularities are provided
                if timestamp_granularities and response_format == "verbose_json":
                    from typing import Literal

                    # Ensure timestamp_granularities contains only valid values
                    valid_granularities: list[Literal["word", "segment"]] = []
                    for g in timestamp_granularities:
                        if g == "word":
                            valid_granularities.append("word")
                        elif g == "segment":
                            valid_granularities.append("segment")

                    transcript_verbose = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=valid_granularities,
                    )
                    result = transcript_verbose.model_dump()
                else:
                    # Default to JSON format without timestamp granularities
                    transcript_json = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="json",
                    )
                    result = transcript_json.model_dump()

            self.logger.info(
                f"Successfully transcribed audio: {len(result.get('words', []))} words detected"
            )

            # Add second assignments to words if word-level timestamps are available
            if "words" in result and result["words"]:
                result["words"] = self.extract_word_timestamps(result)

            # Save transcript if requested
            if save_transcript:
                from .config.constants import TRANSCRIPTS_PATH
                from .utils.directory import ensure_directory

                if output_dir is None:
                    output_dir = TRANSCRIPTS_PATH

                ensure_directory(output_dir)

                transcript_filename = f"{self.audio_file.stem}_transcript.json"
                transcript_path = Path(output_dir) / transcript_filename

                with open(transcript_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                self.logger.info(f"Saved transcript to: {transcript_filename}")

            return result

        except Exception as e:
            self.logger.error(f"Transcription failed for {self.audio_file.name}: {e}")
            raise

    def extract_word_timestamps(
        self, transcript: dict
    ) -> list[dict[str, str | float | int]]:
        """
        Extract and enhance word-level timestamps with second bucket assignment.

        This method processes the raw OpenAI API response to add 'second' fields
        for easier frame-to-word synchronization.

        Args:
            transcript: Raw transcript dictionary from OpenAI API

        Returns:
            List of dictionaries with word, start, end times, and assigned second
        """
        words_with_timestamps = []

        if "words" in transcript:
            for word_info in transcript["words"]:
                start_time = float(word_info.get("start", 0.0))
                end_time = float(word_info.get("end", 0.0))

                # Simple: assign word to the second where it starts
                assigned_second = int(start_time)

                words_with_timestamps.append(
                    {
                        "word": word_info.get("word", ""),
                        "start": start_time,
                        "end": end_time,
                        "second": assigned_second,
                    }
                )

        return words_with_timestamps

    def extract_segments(self, transcript: dict) -> list[dict[str, str | float]]:
        """
        Extract segment-level information from transcript.

        Args:
            transcript: Transcript dictionary from OpenAI API

        Returns:
            List of dictionaries with segment text, start, and end times
        """
        segments = []

        if "segments" in transcript:
            for segment in transcript["segments"]:
                segments.append(
                    {
                        "text": segment.get("text", ""),
                        "start": segment.get("start", 0.0),
                        "end": segment.get("end", 0.0),
                        "words": segment.get("words", []),
                    }
                )

        return segments

    def get_text_at_timestamp(
        self, transcript: dict, timestamp: float, tolerance: float = 0.1
    ) -> Optional[str]:
        """
        Get the word/text that was spoken at a specific timestamp.

        Args:
            transcript: Transcript dictionary with enhanced words (including 'second' field)
            timestamp: Time in seconds to query
            tolerance: Tolerance in seconds for matching

        Returns:
            Word spoken at the timestamp, or None if not found
        """
        words = transcript.get("words", [])

        for word_info in words:
            start = float(word_info["start"])
            end = float(word_info["end"])

            if start - tolerance <= timestamp <= end + tolerance:
                word = word_info["word"]
                return word.strip() if isinstance(word, str) else str(word).strip()

        return None

    def synchronize_with_frames(
        self, transcript: dict, frame_timestamps: list[float]
    ) -> list[dict]:
        """
        Synchronize transcript words with frame timestamps.

        Args:
            transcript: Transcript dictionary with enhanced words (including 'second' field)
            frame_timestamps: List of frame timestamps in seconds

        Returns:
            List of dictionaries mapping frame timestamps to spoken words
        """
        synchronized_data = []

        for frame_time in frame_timestamps:
            spoken_word = self.get_text_at_timestamp(transcript, frame_time)

            synchronized_data.append(
                {
                    "frame_timestamp": frame_time,
                    "spoken_word": spoken_word,
                    "has_speech": spoken_word is not None,
                }
            )

        return synchronized_data
