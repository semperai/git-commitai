from unittest.mock import patch
import git_commitai

class TestGetBinaryFileInfoDetailed:
    """Detailed tests for binary file info."""

    def test_binary_file_info_cat_file_exception(self):
        """Test binary file info when cat-file throws exception."""
        with patch("os.path.splitext", return_value=("file", ".bin")):
            with patch("git_commitai.run_git", side_effect=Exception("Cat-file error")):
                info = git_commitai.get_binary_file_info("file.bin")
                # When all git operations fail, it still returns file type and status
                assert "File type: .bin" in info or "Binary file" in info
                assert "Status: New file" in info or "no additional information" in info

    def test_binary_file_info_new_file_check_exception(self):
        """Test binary file info when checking if file is new throws exception."""
        with patch("os.path.splitext", return_value=("file", ".dat")):
            with patch("git_commitai.run_git") as mock_run:
                def side_effect(args, check=True):
                    if "-s" in args:  # Size check
                        return "2048"
                    elif "-e" in args:  # Existence check
                        raise Exception("Check failed")
                    return ""

                mock_run.side_effect = side_effect
                info = git_commitai.get_binary_file_info("file.dat")
                assert "2.0 KB" in info
                assert "New file" in info  # Should default to new file

