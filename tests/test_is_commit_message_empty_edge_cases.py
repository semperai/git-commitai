from unittest.mock import patch, mock_open
import git_commitai


class TestIsCommitMessageEmptyEdgeCases:
    """Test edge cases in is_commit_message_empty."""

    def test_commit_message_only_whitespace(self):
        """Test with only whitespace and empty lines."""
        content = "   \n\t\n  \n"
        m = mock_open(read_data=content)
        # Ensure iteration over file yields the provided lines
        m.return_value.__iter__.return_value = iter(content.splitlines(True))
        with patch("builtins.open", m):
            assert git_commitai.is_commit_message_empty("fake_path")

    def test_commit_message_io_error(self):
        """Test with IO error during read."""
        with patch("builtins.open", side_effect=IOError("Read error")):
            assert git_commitai.is_commit_message_empty("fake_path")
