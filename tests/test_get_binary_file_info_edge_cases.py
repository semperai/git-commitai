from unittest.mock import patch
import git_commitai

class TestGetBinaryFileInfoEdgeCases:
    """Test edge cases in get_binary_file_info."""

    def test_binary_file_info_no_extension(self):
        """Test binary file info for file without extension."""
        with patch("os.path.splitext", return_value=("filename", "")):
            with patch("git_commitai.run_git", return_value=""):
                info = git_commitai.get_binary_file_info("filename")
                # Without extension, it won't add "File type:" but will add status
                assert "Status: Modified" in info or "Binary file" in info

    def test_binary_file_info_size_parsing_error(self):
        """Test binary file info when size can't be parsed."""
        with patch("os.path.splitext", return_value=("file", ".bin")):
            with patch("git_commitai.run_git", return_value="not-a-number"):
                info = git_commitai.get_binary_file_info("file.bin")
                # Should handle gracefully
                assert "File type: .bin" in info or "no additional information" in info

    def test_binary_file_info_amend_mode(self):
        """Test binary file info in amend mode."""
        with patch("os.path.splitext", return_value=("file", ".jpg")):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.side_effect = [
                    "fatal: Not a valid object",  # First try with index
                    "1024"  # Second try with HEAD
                ]
                info = git_commitai.get_binary_file_info("file.jpg", amend=True)
                assert "JPEG image" in info or "1.0 KB" in info

