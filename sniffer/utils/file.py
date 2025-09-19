"""
File utility functions for path and filename operations.
"""

from pathlib import Path


def extract_filename_from_path(path: str | Path) -> str:
    """
    Extract filename without extension from a file path.

    Args:
        path: File path as string or Path object

    Returns:
        Filename without extension
    """
    path = Path(path)
    return path.stem


def get_file_extension(path: str | Path) -> str:
    """
    Get file extension from a file path.

    Args:
        path: File path as string or Path object

    Returns:
        File extension (including the dot)
    """
    path = Path(path)
    return path.suffix


def is_video_file(path: str | Path) -> bool:
    """
    Check if file is a supported video format.

    Args:
        path: File path as string or Path object

    Returns:
        True if file is a supported video format
    """
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}
    return get_file_extension(path).lower() in video_extensions


def is_audio_file(path: str | Path) -> bool:
    """
    Check if file is a supported audio format.

    Args:
        path: File path as string or Path object

    Returns:
        True if file is a supported audio format
    """
    audio_extensions = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}
    return get_file_extension(path).lower() in audio_extensions


def ensure_file_exists(path: str | Path) -> bool:
    """
    Check if file exists and is accessible.

    Args:
        path: File path as string or Path object

    Returns:
        True if file exists and is accessible

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return True


def get_file_size(path: str | Path) -> int:
    """
    Get file size in bytes.

    Args:
        path: File path as string or Path object

    Returns:
        File size in bytes
    """
    path = Path(path)
    ensure_file_exists(path)
    return path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string
    """
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_value: float = float(size_bytes)
    while size_value >= 1024 and i < len(size_names) - 1:
        size_value /= 1024.0
        i += 1

    return f"{size_value:.1f}{size_names[i]}"


def get_video_files(input_path: str | Path) -> list[Path]:
    """
    Get list of video files from a path.

    Args:
        input_path: Path to a video file or directory containing MP4 files

    Returns:
        List of video file paths

    Raises:
        ValueError: If path doesn't exist or no video files found
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise ValueError(f"Path not found: {input_path}")

    if input_path.is_file():
        if input_path.suffix.lower() == ".mp4":
            return [input_path]
        else:
            raise ValueError(f"File must be MP4 format: {input_path}")
    elif input_path.is_dir():
        mp4_files = list(input_path.glob("*.mp4"))
        if not mp4_files:
            raise ValueError(f"No MP4 files found in directory: {input_path}")
        return sorted(mp4_files)
    else:
        raise ValueError(f"Invalid path: {input_path}")
