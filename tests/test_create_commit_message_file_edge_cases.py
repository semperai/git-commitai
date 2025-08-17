from unittest.mock import patch
import tempfile
import git_commitai

class TestCreateCommitMessageFileEdgeCases:
    """Test edge cases in create_commit_message_file."""

    def test_create_commit_message_with_warnings(self):
        """Test commit message file creation with AI warnings."""
        commit_msg = """Fix authentication bug

# ⚠️  WARNING: Potential null reference error
# Found in: auth.js
# Details: Variable 'user' may be undefined"""

        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git", return_value=""):
                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, commit_msg
                    )
                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check that warnings appear before standard comments
                    assert "Fix authentication bug" in content
                    assert "# ⚠️  WARNING:" in content
                    warning_pos = content.index("# ⚠️  WARNING:")
                    standard_pos = content.index("# Please enter the commit message")
                    assert warning_pos < standard_pos

