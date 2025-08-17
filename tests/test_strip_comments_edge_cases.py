import os
import tempfile
from unittest.mock import patch
import git_commitai

class TestStripCommentsEdgeCases:
    """Test edge cases in strip_comments_and_save."""

    def test_strip_comments_io_error(self):
        """Test strip_comments_and_save with IO error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = git_commitai.strip_comments_and_save("/fake/path")
            assert result is False

    def test_strip_comments_empty_result(self):
        """Test strip_comments_and_save resulting in empty file."""
        content = """# This is a comment
# Another comment
   # Indented comment"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = git_commitai.strip_comments_and_save(tmp_path)
            assert result is True

            with open(tmp_path, 'r') as f:
                stripped = f.read()
            # Should be empty or just newline
            assert stripped.strip() == ""
        finally:
            os.unlink(tmp_path)

