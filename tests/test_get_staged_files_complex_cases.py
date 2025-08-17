from unittest.mock import patch
import git_commitai

class TestGetStagedFilesComplexCases:
    """Test complex cases in get_staged_files."""

    def test_get_staged_files_with_errors(self):
        """Test get_staged_files with file processing errors."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "diff" in args and "--cached" in args and "--name-only" in args:
                    return "file1.py\nfile2.py"
                elif "--numstat" in args:
                    # Simulate error for one file
                    if "file1.py" in args:
                        raise Exception("File error")
                    return "5\t3\tfile2.py"
                elif "show" in args and ":file2.py" in args:
                    return "print('hello')"
                return ""

            mock_run.side_effect = side_effect
            result = git_commitai.get_staged_files()
            # Should still process file2.py despite file1.py error
            assert "file2.py" in result
            assert "print('hello')" in result
            assert "file1.py" not in result

    def test_get_staged_files_amend_with_fatal_error(self):
        """Test get_staged_files in amend mode with fatal errors."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "--name-only" in args and "--cached" in args:
                    return ""  # No newly staged files
                elif "diff-tree" in args:
                    return "file.txt"
                elif "--numstat" in args:
                    return "fatal: error"  # Git error
                elif "show" in args:
                    return "fatal: error"
                return ""

            mock_run.side_effect = side_effect
            result = git_commitai.get_staged_files(amend=True)
            # Should handle the error gracefully
            assert result in ("", "# No files changed (empty commit)") or "file.txt" in result
            # Verify we attempted both staged and HEAD fallbacks for content
            mock_run.assert_any_call(["show", ":file.txt"], check=False)
            mock_run.assert_any_call(["show", "HEAD:file.txt"], check=False)
            # Verify we attempted both numstat checks (index and HEAD range)
            mock_run.assert_any_call(["diff", "--cached", "--numstat", "--", "file.txt"], check=False)
            mock_run.assert_any_call(["diff", "HEAD^", "HEAD", "--numstat", "--", "file.txt"], check=False)

