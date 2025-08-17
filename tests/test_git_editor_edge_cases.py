import os
from unittest.mock import patch
import git_commitai

class TestGitEditorEdgeCases:
    """Test edge cases in git editor detection."""

    def test_get_git_editor_config_exception(self):
        """Test git editor when git config throws exception."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("git_commitai.run_git", side_effect=Exception("Config error")):
                editor = git_commitai.get_git_editor()
                assert editor == "vi"  # Should fall back to vi

