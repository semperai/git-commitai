import subprocess
import tempfile
from unittest.mock import patch
import git_commitai

class TestCreateCommitMessageFileVerboseMode:
    """Test verbose mode in create_commit_message_file."""

    def test_verbose_amend_first_commit(self):
        """Test verbose mode when amending the first commit."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                def side_effect(args, check=True):
                    if "rev-parse" in args and "HEAD^" in args:
                        raise subprocess.CalledProcessError(1, args)  # No parent
                    elif "--cached" in args and "--name-status" not in args:
                        return "diff --git a/first.txt"
                    elif "diff-tree" in args:
                        return ""
                    elif "--name-status" in args:
                        return "A\tfirst.txt"
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Initial commit", amend=True, verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "# diff --git a/first.txt" in content