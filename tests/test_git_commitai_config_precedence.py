import os
from unittest.mock import patch, MagicMock
import git_commitai

class TestGitCommitAIConfigPrecedence:
    """Test configuration precedence in detail."""

    def test_cli_overrides_everything(self):
        """Test that CLI args override all other configs."""
        mock_args = MagicMock()
        mock_args.api_key = "cli-key"
        mock_args.api_url = "cli-url"
        mock_args.model = "cli-model"

        with patch.dict(os.environ, {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_URL": "env-url",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            with patch("git_commitai.load_gitcommitai_config", return_value={
                "model": "repo-model"
            }):
                config = git_commitai.get_env_config(mock_args)

                assert config["api_key"] == "cli-key"
                assert config["api_url"] == "cli-url"
                assert config["model"] == "cli-model"

