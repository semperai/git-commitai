#!/usr/bin/env python3

import pytest
import os
import sys
import tempfile
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open, call
from io import StringIO

# Simple import now that it has .py extension
import git_commitai

class TestGitStatus:
    """Test the git status parsing and display functions."""

    def test_parse_porcelain_modified_files(self):
        """Test parsing modified files from git status --porcelain."""
        with patch('git_commitai.run_command') as mock_run:
            # Setup mock returns
            mock_run.side_effect = [
                'main',  # git branch --show-current
                '',      # git rev-parse HEAD (success, not initial commit)
                ' M README.md\n M git-commitai\n?? LICENSE'  # git status --porcelain
            ]

            with patch('sys.stdout', new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                # Check that both modified files are shown
                assert 'modified:   README.md' in output
                assert 'modified:   git-commitai' in output
                assert 'LICENSE' in output
                assert 'Untracked files:' in output
                assert 'Changes not staged for commit:' in output

    def test_parse_porcelain_staged_and_modified(self):
        """Test parsing files that are staged with additional modifications."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'main',
                '',
                'MM file1.txt\nM  file2.txt\n M file3.txt'
            ]

            with patch('sys.stdout', new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                # MM means staged with additional unstaged changes
                assert 'modified:   file1.txt' in output
                # M  means staged only (not shown in unstaged)
                assert 'modified:   file2.txt' not in output
                # _M means modified but not staged
                assert 'modified:   file3.txt' in output

    def test_parse_porcelain_deleted_files(self):
        """Test parsing deleted files."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'main',
                '',
                ' D deleted.txt\nD  staged_delete.txt'
            ]

            with patch('sys.stdout', new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                assert 'deleted:    deleted.txt' in output
                assert 'deleted:    staged_delete.txt' not in output

    def test_clean_working_tree(self):
        """Test output when working tree is clean."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'main',
                '',
                ''  # No output from git status --porcelain
            ]

            with patch('sys.stdout', new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                assert 'nothing to commit, working tree clean' in output

    def test_initial_commit(self):
        """Test output for initial commit."""
        with patch('git_commitai.run_command') as mock_run:
            def side_effect(cmd, check=True):
                if 'branch --show-current' in cmd:
                    return 'main'
                elif 'rev-parse HEAD' in cmd:
                    if check:
                        raise subprocess.CalledProcessError(1, cmd)
                    return ''
                elif 'status --porcelain' in cmd:
                    return '?? README.md'
                return ''

            mock_run.side_effect = side_effect

            with patch('sys.stdout', new=StringIO()) as fake_out:
                # Mock CalledProcessError since it's used in the function
                with patch.object(subprocess, 'CalledProcessError', Exception):
                    git_commitai.show_git_status()
                    output = fake_out.getvalue()

                    assert 'Initial commit' in output
                    assert 'Untracked files:' in output

class TestStagedFiles:
    """Test getting staged file contents."""

    def test_get_staged_files(self):
        """Test retrieving staged file contents."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'file1.py\nfile2.md',  # git diff --cached --name-only
                'print("hello")',       # git show :file1.py
                '# Header\nContent'     # git show :file2.md
            ]

            result = git_commitai.get_staged_files()

            assert 'file1.py' in result
            assert 'print("hello")' in result
            assert 'file2.md' in result
            assert '# Header' in result

    def test_get_staged_files_empty(self):
        """Test when no files are staged."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.return_value = ''

            result = git_commitai.get_staged_files()
            assert result == ''

    def test_get_staged_files_amend(self):
        """Test retrieving files for --amend."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'file1.py\nfile2.md',  # git diff-tree from HEAD
                'file3.js',             # git diff --cached --name-only
                'print("hello")',       # git show :file1.py
                '# Header',             # git show :file2.md
                'console.log("test")'   # git show :file3.js
            ]

            result = git_commitai.get_staged_files(amend=True)

            assert 'file1.py' in result
            assert 'file2.md' in result
            assert 'file3.js' in result

class TestCheckStagedChanges:
    """Test checking for staged changes."""

    def test_has_staged_changes(self):
        """Test when there are staged changes."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1  # git diff returns 1 when there are changes

            assert git_commitai.check_staged_changes() == True

    def test_no_staged_changes(self):
        """Test when there are no staged changes."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0  # git diff returns 0 when no changes

            with patch('git_commitai.show_git_status'):
                assert git_commitai.check_staged_changes() == False

    def test_amend_with_previous_commit(self):
        """Test --amend with a previous commit."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.return_value = 'abc123'  # Successful HEAD lookup

            assert git_commitai.check_staged_changes(amend=True) == True

    def test_amend_without_previous_commit(self):
        """Test --amend on initial commit."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git rev-parse HEAD')

            with patch('sys.stdout', new=StringIO()) as fake_out:
                result = git_commitai.check_staged_changes(amend=True)
                output = fake_out.getvalue()

                assert result == False
                assert 'nothing to amend' in output

class TestGitEditor:
    """Test git editor detection."""

    def test_git_editor_env(self):
        """Test GIT_EDITOR environment variable."""
        with patch.dict(os.environ, {'GIT_EDITOR': 'nano'}):
            assert git_commitai.get_git_editor() == 'nano'

    def test_editor_env(self):
        """Test EDITOR environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {'EDITOR': 'vim'}):
                assert git_commitai.get_git_editor() == 'vim'

    def test_git_config_editor(self):
        """Test git config core.editor."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('git_commitai.run_command') as mock_run:
                mock_run.return_value = 'emacs'
                assert git_commitai.get_git_editor() == 'emacs'

    def test_default_editor(self):
        """Test default editor fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('git_commitai.run_command') as mock_run:
                mock_run.return_value = ''
                assert git_commitai.get_git_editor() == 'vi'

class TestAPIRequest:
    """Test API request handling."""

    def test_successful_api_request(self):
        """Test successful API request."""
        config = {
            'api_key': 'test-key',
            'api_url': 'https://api.example.com',
            'model': 'test-model'
        }

        mock_response = {
            'choices': [
                {'message': {'content': 'Fix bug in authentication'}}
            ]
        }

        with patch('git_commitai.urlopen') as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(mock_response).encode()

            result = git_commitai.make_api_request(config, 'test message')
            assert result == 'Fix bug in authentication'

    def test_api_request_error(self):
        """Test API request error handling."""
        config = {
            'api_key': 'test-key',
            'api_url': 'https://api.example.com',
            'model': 'test-model'
        }

        with patch('git_commitai.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError('url', 500, 'Server Error', {}, None)

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, 'test message')

class TestCommitMessageEmpty:
    """Test commit message empty checking."""

    def test_empty_message(self):
        """Test detecting empty commit message."""
        content = """
# Please enter the commit message for your changes.
# Lines starting with '#' will be ignored.
#
# On branch main
        """
        with patch('builtins.open', mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty('fake_path') == True

    def test_non_empty_message(self):
        """Test detecting non-empty commit message."""
        content = """Fix authentication bug

This fixes the issue where users couldn't log in.

# Please enter the commit message for your changes.
        """
        with patch('builtins.open', mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty('fake_path') == False

class TestAmendFeatures:
    """Test --amend specific features."""

    def test_get_git_diff_amend(self):
        """Test getting diff for --amend."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'abc123',  # git rev-parse HEAD^
                'diff --git a/file.txt...',  # git diff parent..HEAD
                ''  # git diff --cached (no additional staged changes)
            ]

            result = git_commitai.get_git_diff(amend=True)
            assert 'diff --git a/file.txt' in result

    def test_get_git_diff_amend_with_staged(self):
        """Test getting diff for --amend with additional staged changes."""
        with patch('git_commitai.run_command') as mock_run:
            mock_run.side_effect = [
                'abc123',  # git rev-parse HEAD^
                'diff --git a/file1.txt...',  # git diff parent..HEAD
                'diff --git a/file2.txt...'   # git diff --cached (additional staged)
            ]

            result = git_commitai.get_git_diff(amend=True)
            assert 'file1.txt' in result
            assert 'file2.txt' in result
            assert 'Additional staged changes' in result

    def test_create_commit_message_file_amend(self):
        """Test creating commit message file for --amend."""
        with patch('git_commitai.get_current_branch', return_value='main'):
            with patch('git_commitai.run_command') as mock_run:
                mock_run.side_effect = [
                    'M\tfile1.txt\nA\tfile2.txt',  # git diff-tree
                    'M\tfile3.txt'  # git diff --cached
                ]

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        'Test commit message',
                        amend=True
                    )

                    with open(commit_file, 'r') as f:
                        content = f.read()

                    assert 'Test commit message' in content
                    assert 'You are amending the previous commit' in content
                    assert 'including previous commit' in content
                    assert 'Additional staged changes' in content

class TestMainFlow:
    """Test the main flow of the application."""

    def test_not_in_git_repo(self):
        """Test behavior when not in a git repository."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, 'git')

            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    with patch('sys.argv', ['git-commitai']):
                        git_commitai.main()

                assert exc_info.value.code == 128
                assert 'fatal: not a git repository' in fake_out.getvalue()

    def test_no_api_key(self):
        """Test behavior when API key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                git_commitai.get_env_config()

    def test_successful_commit(self):
        """Test successful commit flow."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            with patch('git_commitai.check_staged_changes', return_value=True):
                with patch('git_commitai.get_env_config') as mock_config:
                    mock_config.return_value = {
                        'api_key': 'test',
                        'api_url': 'http://test',
                        'model': 'test'
                    }

                    with patch('git_commitai.make_api_request', return_value='Test commit'):
                        with patch('git_commitai.get_git_dir', return_value='/tmp/.git'):
                            with patch('git_commitai.create_commit_message_file', return_value='/tmp/COMMIT'):
                                with patch('os.path.getmtime', side_effect=[1000, 2000]):
                                    with patch('git_commitai.open_editor'):
                                        with patch('git_commitai.is_commit_message_empty', return_value=False):
                                            with patch('sys.argv', ['git-commitai']):
                                                git_commitai.main()

    def test_successful_amend(self):
        """Test successful --amend flow."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            with patch('git_commitai.check_staged_changes', return_value=True):
                with patch('git_commitai.get_env_config') as mock_config:
                    mock_config.return_value = {
                        'api_key': 'test',
                        'api_url': 'http://test',
                        'model': 'test'
                    }

                    with patch('git_commitai.make_api_request', return_value='Amended commit'):
                        with patch('git_commitai.get_git_dir', return_value='/tmp/.git'):
                            with patch('git_commitai.create_commit_message_file', return_value='/tmp/COMMIT'):
                                with patch('os.path.getmtime', side_effect=[1000, 2000]):
                                    with patch('git_commitai.open_editor'):
                                        with patch('git_commitai.is_commit_message_empty', return_value=False):
                                            with patch('sys.argv', ['git-commitai', '--amend']):
                                                git_commitai.main()

                                                # Verify git commit --amend was called
                                                calls = mock_run.call_args_list
                                                assert any(['--amend' in str(call) for call in calls])

# Add this if running as a script
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=git_commitai', '--cov-report=term-missing'])
