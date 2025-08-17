import pytest
from unittest.mock import patch, MagicMock
import git_commitai

class TestDryRunEdgeCases:
    """Test edge cases in dry run functionality."""

    def test_dry_run_with_git_failure(self):
        """Test dry run when git commit --dry-run fails."""
        args = MagicMock()
        args.dry_run = True
        args.amend = False
        args.allow_empty = False
        args.no_verify = False
        args.verbose = False
        args.author = None
        args.date = None
        args.message = None

        with patch("git_commitai.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Git error")

            with pytest.raises(SystemExit) as exc_info:
                git_commitai.show_dry_run_summary(args)
            assert exc_info.value.code == 1


