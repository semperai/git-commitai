import json
from unittest.mock import patch, mock_open
import git_commitai

class TestLoadGitCommitAIConfigEdgeCases:
    """Test edge cases in loading .gitcommitai config."""

    def test_config_file_exception_during_read(self):
        """Test handling exceptions during config file read."""
        with patch("git_commitai.get_git_root", return_value="/repo"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=Exception("Read error")):
                    config = git_commitai.load_gitcommitai_config()
                    assert config == {}

    def test_config_json_missing_fields(self):
        """Test JSON config with missing expected fields."""
        json_config = {"other_field": "value"}  # No 'model' or 'prompt'

        with patch("git_commitai.get_git_root", return_value="/repo"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(json_config))):
                    config = git_commitai.load_gitcommitai_config()
                    assert "model" not in config
                    assert "prompt_template" not in config


