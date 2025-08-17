import pytest
from unittest.mock import patch
import git_commitai

class TestMainWithDryRunDebug:
    """Test main with dry-run and debug combination."""

    def test_main_dry_run_with_debug_logging(self):
        """Test that dry-run mode logs correctly with debug enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                        "repo_config": {}
                    }

                    with patch("git_commitai.make_api_request", return_value="Test"):
                        with patch("git_commitai.show_dry_run_summary") as mock_dry_run:
                            mock_dry_run.side_effect = SystemExit(0)

                            with patch("git_commitai.debug_log") as mock_debug:
                                with pytest.raises(SystemExit):
                                    with patch("sys.argv", ["git-commitai", "--debug", "--dry-run"]):
                                        git_commitai.main()

                                # Check that debug logging mentioned dry-run
                                debug_calls = [str(call) for call in mock_debug.call_args_list]
                                assert any("DRY RUN MODE" in str(call) or "dry-run" in str(call).lower()
                                          for call in debug_calls)

        # Reset debug flag
        git_commitai.DEBUG = False
