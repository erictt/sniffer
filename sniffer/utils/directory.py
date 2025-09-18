"""
Directory utility functions for managing directories and paths.
"""

from pathlib import Path


def ensure_directory(path: str | Path) -> None:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path as string or Path object
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")


def ensure_directories(paths: list[str | Path]) -> None:
    """
    Create multiple directories if they don't exist.

    Args:
        paths: List of directory paths
    """
    for path in paths:
        ensure_directory(path)


def is_directory_empty(path: str | Path) -> bool:
    """
    Check if directory is empty.

    Args:
        path: Directory path as string or Path object

    Returns:
        True if directory is empty
    """
    path = Path(path)
    if not path.exists():
        return True
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    return len(list(path.iterdir())) == 0


def get_directory_size(path: str | Path) -> int:
    """
    Calculate total size of all files in directory (recursive).

    Args:
        path: Directory path as string or Path object

    Returns:
        Total size in bytes
    """
    path = Path(path)
    if not path.exists():
        return 0
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    total_size = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size

    return total_size


def list_files_in_directory(
    directory: str | Path, pattern: str = "*", recursive: bool = False
) -> list[Path]:
    """
    List all files in directory matching pattern.

    Args:
        directory: Directory path to search
        pattern: File pattern to match (e.g., "*.mp4")
        recursive: Whether to search subdirectories

    Returns:
        List of file paths
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    if recursive:
        return [p for p in directory.rglob(pattern) if p.is_file()]
    else:
        return [p for p in directory.glob(pattern) if p.is_file()]


def create_subdirectory(parent: str | Path, name: str) -> Path:
    """
    Create a subdirectory within parent directory.

    Args:
        parent: Parent directory path
        name: Name of subdirectory to create

    Returns:
        Path to created subdirectory
    """
    parent = Path(parent)
    subdirectory = parent / name
    ensure_directory(subdirectory)
    return subdirectory


def clean_directory(path: str | Path, pattern: str = "*") -> int:
    """
    Remove all files matching pattern from directory.

    Args:
        path: Directory path to clean
        pattern: File pattern to match for deletion

    Returns:
        Number of files deleted
    """
    path = Path(path)
    if not path.exists() or not path.is_dir():
        return 0

    files_to_delete = list(path.glob(pattern))
    deleted_count = 0

    for file_path in files_to_delete:
        if file_path.is_file():
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")

    return deleted_count
