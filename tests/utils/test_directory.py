"""
Essential tests for directory utility functions.
"""

from sniffer.utils.directory import (
    ensure_directory,
    ensure_directories,
    is_directory_empty,
    list_files_in_directory,
)


class TestDirectoryUtils:
    """Test core directory utility functions."""

    def test_ensure_directory(self, temp_dir):
        """Test directory creation."""
        new_dir = temp_dir / "new_directory"
        ensure_directory(new_dir)
        assert new_dir.exists() and new_dir.is_dir()

    def test_ensure_directories(self, temp_dir):
        """Test multiple directory creation."""
        dirs = [temp_dir / "dir1", temp_dir / "dir2"]
        ensure_directories(dirs)
        assert all(d.exists() and d.is_dir() for d in dirs)

    def test_is_directory_empty(self, temp_dir):
        """Test directory emptiness check."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        assert is_directory_empty(empty_dir) is True

        # Add file and test again
        (empty_dir / "file.txt").write_text("content")
        assert is_directory_empty(empty_dir) is False

    def test_list_files_in_directory(self, temp_dir):
        """Test file listing."""
        (temp_dir / "file1.txt").write_text("content")
        (temp_dir / "file2.py").write_text("code")

        files = list_files_in_directory(temp_dir)
        file_names = [f.name for f in files]

        assert "file1.txt" in file_names
        assert "file2.py" in file_names
