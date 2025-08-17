"""Tests for staged files handling."""

from unittest.mock import patch
import git_commitai


class TestStagedFiles:
    """Test getting staged file contents."""

    def test_get_staged_files(self):
        """Test retrieving staged file contents."""
        with patch("git_commitai.run_git") as mock_run:
            # Mock the sequence of commands that will be called
            def side_effect(args, check=True):
                if "diff" in args and "--cached" in args and "--name-only" in args:
                    return "file1.py\nfile2.md"
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file1.py" in args:
                    return "10\t5\tfile1.py"  # Not binary (shows numbers)
                elif "show" in args and ":file1.py" in args:
                    return 'print("hello")'
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file2.md" in args:
                    return "3\t1\tfile2.md"  # Not binary
                elif "show" in args and ":file2.md" in args:
                    return "# Header\nContent"
                return ""

            mock_run.side_effect = side_effect

            result = git_commitai.get_staged_files()

            assert "file1.py" in result
            assert 'print("hello")' in result
            assert "file2.md" in result
            assert "# Header" in result

    def test_get_staged_files_empty(self):
        """Test when no files are staged."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = ""

            result = git_commitai.get_staged_files()
            assert result == ""

    def test_get_staged_files_with_binary(self):
        """Test retrieving staged files including binary files."""
        with patch("git_commitai.run_git") as mock_run:

            def side_effect(args, check=True):
                if "diff" in args and "--cached" in args and "--name-only" in args:
                    return "file1.py\nlogo.webp"
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file1.py" in args:
                    return "10\t5\tfile1.py"  # Text file
                elif "show" in args and ":file1.py" in args:
                    return 'print("hello")'
                elif "diff" in args and "--cached" in args and "--numstat" in args and "logo.webp" in args:
                    return "-\t-\tlogo.webp"  # Binary file (shows dashes)
                elif "cat-file" in args and "-s" in args and ":logo.webp" in args:
                    return "45678"  # File size in bytes
                return ""

            mock_run.side_effect = side_effect

            # Need to patch os.path.splitext for the binary file extension
            with patch("os.path.splitext", return_value=("logo", ".webp")):
                result = git_commitai.get_staged_files()

                assert "file1.py" in result
                assert 'print("hello")' in result
                assert "logo.webp (binary file)" in result
                assert "WebP image" in result or "File type: .webp" in result
                assert "KB" in result  # File size should be shown

    def test_get_staged_files_amend(self):
        """Test retrieving files for --amend."""
        with patch("git_commitai.run_git") as mock_run:

            def side_effect(args, check=True):
                if "diff-tree" in args and "--no-commit-id" in args and "--name-only" in args:
                    return "file1.py\nfile2.md"
                elif "diff" in args and "--cached" in args and "--name-only" in args:
                    return "file3.js"
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file1.py" in args:
                    return "10\t5\tfile1.py"
                elif "show" in args and ":file1.py" in args:
                    return 'print("hello")'
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file2.md" in args:
                    return "3\t1\tfile2.md"
                elif "show" in args and ":file2.md" in args:
                    return "# Header"
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file3.js" in args:
                    return "1\t1\tfile3.js"
                elif "show" in args and ":file3.js" in args:
                    return 'console.log("test")'
                return ""

            mock_run.side_effect = side_effect

            result = git_commitai.get_staged_files(amend=True)

            assert "file1.py" in result
            assert "file2.md" in result
            assert "file3.js" in result

    def test_get_staged_files_binary_types(self):
        """Test different binary file types are properly identified."""
        test_cases = [
            ("image.png", "-\t-\timage.png", "PNG image"),
            ("video.mp4", "-\t-\tvideo.mp4", "MP4 video"),
            ("archive.zip", "-\t-\tarchive.zip", "ZIP archive"),
            ("font.ttf", "-\t-\tfont.ttf", "TrueType font"),
        ]

        for filename, numstat_output, expected_description in test_cases:
            with patch("git_commitai.run_git") as mock_run:

                def side_effect(args, check=True):
                    if "diff" in args and "--cached" in args and "--name-only" in args:
                        return filename
                    elif "diff" in args and "--cached" in args and "--numstat" in args and filename in args:
                        return numstat_output
                    elif "cat-file" in args and "-s" in args and f":{filename}" in args:
                        return "1024"  # 1KB
                    return ""

                mock_run.side_effect = side_effect

                # Extract extension for os.path.splitext mock
                name, ext = filename.rsplit(".", 1)
                with patch("os.path.splitext", return_value=(name, f".{ext}")):
                    result = git_commitai.get_staged_files()

                    assert f"{filename} (binary file)" in result
                    assert expected_description in result or f"File type: .{ext}" in result
