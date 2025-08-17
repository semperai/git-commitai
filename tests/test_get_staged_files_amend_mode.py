from unittest.mock import patch
import git_commitai

class TestGetStagedFilesAmendMode:
    """Test get_staged_files in amend mode with various scenarios."""

    def test_get_staged_files_amend_show_index_fatal(self):
        """Test amend mode when show index fails with fatal error."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "diff-tree" in args:
                    return "file.txt"
                elif "diff" in args and "--cached" in args and "--name-only" in args:
                    return ""  # No additional staged files
                elif "--numstat" in args:
                    return "10\t5\tfile.txt"
                elif "show" in args and ":file.txt" in args:
                    # Simulate fatal error for index version
                    return "fatal: Path 'file.txt' does not exist in the index"
                elif "show" in args and "HEAD:file.txt" in args:
                    # Fall back to HEAD version
                    return "file content from HEAD"
                return ""

            mock_run.side_effect = side_effect
            result = git_commitai.get_staged_files(amend=True)
            assert "file content from HEAD" in result

            mock_run.side_effect = side_effect
            result = git_commitai.get_staged_files(amend=True)
            assert "file content from HEAD" in result
            # Ensure the fallback path was taken and output is correctly formatted
            mock_run.assert_any_call(["show", ":file.txt"], check=False)
            mock_run.assert_any_call(["show", "HEAD:file.txt"], check=False)
            assert "file.txt\n```\n" in result
            assert "fatal:" not in result
