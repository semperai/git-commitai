from unittest.mock import patch
import git_commitai

class TestOpenEditorEdgeCases:
    """Test edge cases in open_editor."""

    def test_open_editor_windows(self):
        """Test open_editor on Windows."""
        with patch("os.name", "nt"):
            with patch("git_commitai.shlex.split", return_value=["notepad"]):
                with patch("subprocess.run") as mock_run:
                    git_commitai.open_editor("file.txt", "notepad")
                    mock_run.assert_called_once()

