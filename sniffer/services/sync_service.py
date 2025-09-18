"""
Synchronization service for mapping frames to transcription data.
"""

from pathlib import Path

from ..utils.logging import get_logger


class SyncService:
    """Service for synchronizing frames with transcription data."""

    def __init__(self):
        self.logger = get_logger("sniffer.sync")

    def create_frame_transcript_table(
        self,
        position_frames: dict[int, str],
        transcript_data: dict | None = None,
    ) -> list[dict]:
        """
        Create a table mapping each second to its frame file path and spoken words.

        Args:
            position_frames: Dict mapping second -> frame_path from frame extraction
            transcript_data: Transcription data from AudioTranscriber

        Returns:
            List of dictionaries with second, frame_path, and words
        """
        self.logger.info("Creating frame-transcript synchronization table")

        table_data = []

        # Get all seconds that have frames
        frame_seconds = sorted(position_frames.keys())

        for second in frame_seconds:
            frame_path = position_frames[second]
            frame_filename = Path(frame_path).name

            # Find words spoken during this second
            words_in_second = []
            if transcript_data and "words" in transcript_data:
                words_in_second = self._get_words_for_second(
                    transcript_data["words"], second
                )

            # Format words for display
            words_text = self._format_words_for_second(words_in_second)

            table_data.append(
                {
                    "second": second,
                    "frame_path": frame_path,
                    "frame_filename": frame_filename,
                    "words": words_text,
                    "word_count": len(words_in_second),
                    "has_speech": len(words_in_second) > 0,
                }
            )

        self.logger.info(
            f"Created sync table with {len(table_data)} entries, "
            f"{sum(1 for item in table_data if item['has_speech'])} with speech"
        )

        return table_data

    def _get_words_for_second(
        self, words: list[dict], target_second: int
    ) -> list[dict]:
        """
        Get all words that are assigned to a specific second.

        Args:
            words: List of word dictionaries with timing information
            target_second: The second to find words for

        Returns:
            List of words spoken during that second
        """
        words_in_second = []

        for word_info in words:
            # Only use the assigned second to avoid duplication
            word_second = word_info.get("second")
            if word_second == target_second:
                words_in_second.append(word_info)

        return words_in_second

    def _format_words_for_second(self, words: list[dict]) -> str:
        """
        Format words for display in the sync table.

        Args:
            words: List of word dictionaries

        Returns:
            Formatted string of words for display
        """
        if not words:
            return "[silence]"

        # Extract just the word text and join them
        word_texts = []
        for word_info in words:
            word_text = word_info.get("word", "").strip()
            if word_text:
                word_texts.append(word_text)

        if not word_texts:
            return "[silence]"

        return " ".join(word_texts)

    def get_sync_statistics(self, sync_table: list[dict]) -> dict:
        """
        Generate statistics about the frame-transcript synchronization.

        Args:
            sync_table: Output from create_frame_transcript_table

        Returns:
            Dictionary with synchronization statistics
        """
        total_seconds = len(sync_table)
        seconds_with_speech = sum(1 for item in sync_table if item["has_speech"])
        seconds_with_silence = total_seconds - seconds_with_speech

        total_words = sum(item["word_count"] for item in sync_table)

        return {
            "total_seconds": total_seconds,
            "seconds_with_speech": seconds_with_speech,
            "seconds_with_silence": seconds_with_silence,
            "speech_coverage": f"{(seconds_with_speech / total_seconds * 100):.1f}%"
            if total_seconds > 0
            else "0.0%",
            "total_words": total_words,
            "average_words_per_second": f"{(total_words / total_seconds):.1f}"
            if total_seconds > 0
            else "0.0",
        }

