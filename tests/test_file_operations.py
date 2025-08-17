from unittest.mock import patch, mock_open
from io import StringIO
import git_commitai

class TestFileOperations:
    """Test file-related operations."""

    def test_strip_comments_and_save_success(self):
        """Test successful comment stripping."""
        content = "Commit message\n# This is a comment\nMore content\n# Another comment"
        expected = "Commit message\nMore content\n"

        with patch("builtins.open", mock_open(read_data=content)) as mock_file:
            result = git_commitai.strip_comments_and_save("test.txt")
            assert result is True

            # Check that the file was written correctly
            handle = mock_file()
            written_content = ""
            for call in handle.write.call_args_list:
                written_content += call[0][0]
            assert written_content == expected

    def test_strip_comments_and_save_io_error(self):
        """Test comment stripping with IO error."""
        with patch("builtins.open", side_effect=IOError("File error")):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                result = git_commitai.strip_comments_and_save("test.txt")
                assert result is False
                assert "Failed to process commit message" in fake_out.getvalue()
