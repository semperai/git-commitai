from unittest.mock import patch
import subprocess
import git_commitai

class TestGitDiffComplexCases:
    """Test complex cases in get_git_diff."""

    def test_get_git_diff_amend_first_commit(self):
        """Test get_git_diff for amend on first commit."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "HEAD^" in args:
                    raise subprocess.CalledProcessError(1, args)
                elif "--cached" in args:
                    return "diff --git a/file.txt b/file.txt\n+new file"
                return ""

            mock_run.side_effect = side_effect
            result = git_commitai.get_git_diff(amend=True)
            assert "diff --git" in result
            assert "+new file" in result

