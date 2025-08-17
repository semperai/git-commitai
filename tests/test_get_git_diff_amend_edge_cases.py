from unittest.mock import patch
import git_commitai

class TestGetGitDiffAmendEdgeCases:
    """Test get_git_diff in amend mode edge cases."""

    def test_get_git_diff_amend_with_exception_in_parent(self):
        """Test amend when getting parent commit raises general exception."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "HEAD^" in args:
                    raise Exception("General error")
                elif "--cached" in args:
                    return "diff --git a/file.txt"
                return ""

            mock_run.side_effect = side_effect
            result = git_commitai.get_git_diff(amend=True)
            assert "diff --git" in result

            # Verify result is wrapped in code fences (expected formatting)
            assert result.startswith("```") and result.strip().endswith("```")

            # Ensure we fell back to cached diff after exception on HEAD^
            calls = [c.args[0] for c in mock_run.call_args_list]
            assert any(cmd[:2] == ["rev-parse", "HEAD^"] for cmd in calls)
            assert any(cmd == ["diff", "--cached"] for cmd in calls)

