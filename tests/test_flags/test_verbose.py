"""Tests for -v/--verbose diff display functionality."""

import tempfile
from unittest.mock import patch

import git_commitai


class TestVerboseFlag:
    """Test the -v/--verbose diff display functionality."""

    def test_create_commit_message_file_with_verbose(self):
        """Test that verbose flag adds diff to commit message file."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "M\tfile1.txt\nA\tfile2.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/file1.txt b/file1.txt
index 123..456 100644
--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,3 @@
-old line
+new line
 unchanged line"""
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Test commit message",
                        amend=False,
                        auto_staged=False,
                        no_verify=False,
                        verbose=True,
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check for commit message
                    assert "Test commit message" in content

                    # Check for verbose separator
                    assert "# ------------------------ >8 ------------------------" in content
                    assert "# Do not modify or remove the line above." in content
                    assert "# Everything below it will be ignored." in content

                    # Check for diff header
                    assert "# Diff of changes to be committed:" in content

                    # Check for actual diff content (as comments)
                    assert "# diff --git a/file1.txt b/file1.txt" in content
                    assert "# -old line" in content
                    assert "# +new line" in content

    def test_verbose_without_diff(self):
        """Test verbose mode when there's no diff to show."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = ""  # No diff

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Empty commit", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Verbose section should still be present
                    assert "# ------------------------ >8 ------------------------" in content
                    assert "# Diff of changes to be committed:" in content

    def test_verbose_with_amend(self):
        """Test verbose flag with --amend shows correct diff."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git rev-parse HEAD^" in cmd:
                        return "abc123"
                    elif "git diff abc123..HEAD" in cmd:
                        return """diff --git a/original.txt b/original.txt
index 111..222 100644
--- a/original.txt
+++ b/original.txt
@@ -1 +1 @@
-original content
+amended content"""
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/new.txt b/new.txt
new file mode 100644
index 000..333
--- /dev/null
+++ b/new.txt
@@ -0,0 +1 @@
+new file content"""
                    elif "git diff-tree" in cmd:
                        return "M\toriginal.txt"
                    elif "git diff --cached --name-status" in cmd:
                        return "A\tnew.txt"
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Amended commit", amend=True, verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Should show both original commit diff and new staged changes
                    assert "# diff --git a/original.txt b/original.txt" in content
                    assert "# -original content" in content
                    assert "# +amended content" in content

                    # Should also show additional staged changes
                    assert "# Additional staged changes:" in content
                    assert "# diff --git a/new.txt b/new.txt" in content
                    assert "# +new file content" in content

    def test_verbose_with_binary_files(self):
        """Test verbose mode properly handles binary files in diff."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "A\tlogo.png\nM\tcode.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/logo.png b/logo.png
new file mode 100644
index 000..111
Binary files /dev/null and b/logo.png differ
diff --git a/code.py b/code.py
index 222..333 100644
--- a/code.py
+++ b/code.py
@@ -1 +1 @@
-print("old")
+print("new")"""
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Added logo and updated code", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check for binary file indication
                    assert "# Binary files /dev/null and b/logo.png differ" in content

                    # Check for text file diff
                    assert '# -print("old")' in content
                    assert '# +print("new")' in content

    def test_main_flow_with_verbose(self):
        """Test the main flow with -v flag."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch("git_commitai.make_api_request", return_value="Verbose commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("sys.argv", ["git-commitai", "-v"]):
                                                git_commitai.main()

                                                # Verify create_commit_message_file was called with verbose=True
                                                mock_create.assert_called_once()
                                                call_args = mock_create.call_args[1]
                                                assert call_args["verbose"]

    def test_verbose_with_multiple_flags(self):
        """Test verbose combined with other flags."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch("git_commitai.make_api_request", return_value="Complex commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            # Combine -a, -n, -v flags
                                            with patch("sys.argv", ["git-commitai", "-a", "-n", "-v"]):
                                                git_commitai.main()

                                                # Verify all flags are passed correctly
                                                call_args = mock_create.call_args[1]
                                                assert call_args["auto_staged"]
                                                assert call_args["no_verify"]
                                                assert call_args["verbose"]

    def test_verbose_diff_formatting(self):
        """Test that diff lines are properly formatted as comments."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                # Multi-line diff with various git diff elements
                complex_diff = """diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,7 @@ def main():
     # Initialize application
     app = Application()

-    # Old configuration
+    # New configuration
     config = load_config()

@@ -20,3 +20,5 @@ def main():
     app.run()
+
+    return 0"""

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "M\tsrc/main.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return complex_diff
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Update configuration", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Every diff line should be commented
                    for line in complex_diff.split("\n"):
                        assert f"# {line}" in content

                    # Check specific formatting
                    assert "# @@ -10,7 +10,7 @@ def main():" in content
                    assert "# -    # Old configuration" in content
                    assert "# +    # New configuration" in content
                    assert "# +    return 0" in content

    def test_verbose_separator_not_in_normal_mode(self):
        """Test that verbose separator is not added without -v flag."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = "M\tfile.txt"

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Normal commit", verbose=False  # Not verbose
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Verbose separator should NOT be present
                    assert "# ------------------------ >8 ------------------------" not in content
                    assert "# Diff of changes to be committed:" not in content
