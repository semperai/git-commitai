from unittest.mock import MagicMock
import git_commitai

class TestBuildAIPromptEdgeCases:
    """Test edge cases in build_ai_prompt."""

    def test_build_prompt_with_amend_note(self):
        """Test build_ai_prompt with amend flag."""
        repo_config = {
            "prompt_template": "Template {AMEND_NOTE}"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = True

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args)
        assert "amending the previous commit" in prompt.lower()

    def test_build_prompt_excessive_blank_lines(self):
        """Test that excessive blank lines are normalized."""
        repo_config = {
            "prompt_template": "Line1\n\n\n\n\nLine2"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args)
        # Should normalize to max 2 newlines
        assert "\n\n\n" not in prompt
        assert prompt == "Line1\n\nLine2"

