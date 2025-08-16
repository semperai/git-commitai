#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import tempfile
import argparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def get_env_config():
    """Get configuration from environment variables."""
    config = {
        'api_key': os.environ.get('GIT_COMMIT_AI_KEY'),
        'api_url': os.environ.get('GIT_COMMIT_AI_URL', 'https://api.openai.com/v1/chat/completions'),
        'model': os.environ.get('GIT_COMMIT_AI_MODEL', 'gpt-4o')
    }

    if not config['api_key']:
        print("Error: GIT_COMMIT_AI_KEY environment variable is not set")
        print()
        print("Please set up your API credentials:")
        print("  export GIT_COMMIT_AI_KEY='your-api-key'")
        print("  export GIT_COMMIT_AI_URL='https://api.openai.com/v1/chat/completions' # or your provider's URL")
        print("  export GIT_COMMIT_AI_MODEL='gpt-4o' # or your preferred model")
        sys.exit(1)

    return config

def run_command(cmd, check=True):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        # Don't strip here - let callers decide if they want to strip
        return result.stdout
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.stdout if e.stdout else ""

def check_staged_changes(amend=False):
    """Check if there are staged changes and provide git-like output if not."""
    if amend:
        # For --amend, we're modifying the last commit, so we don't need staged changes
        # But we should check if there's a previous commit to amend
        try:
            run_command('git rev-parse HEAD', check=True)
            return True
        except:
            print("fatal: You have nothing to amend.")
            return False

    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            capture_output=True
        )
        if result.returncode == 0:
            # No staged changes - mimic git commit output
            show_git_status()
            return False
        return True
    except subprocess.CalledProcessError:
        return False

def show_git_status():
    """Show git status output similar to what 'git commit' shows."""
    # Get branch name
    try:
        branch = run_command('git branch --show-current').strip()
        if not branch:  # detached HEAD state
            branch = run_command('git rev-parse --short HEAD').strip()
            print(f"HEAD detached at {branch}")
        else:
            print(f"On branch {branch}")
    except:
        print("On branch master")

    # Check if this is initial commit
    try:
        run_command('git rev-parse HEAD', check=True)
    except:
        print("\nInitial commit\n")

    # Get untracked and modified files - don't strip to preserve all lines
    try:
        status_output = run_command('git status --porcelain')

        untracked = []
        modified = []
        deleted = []

        if status_output:
            # Split on newlines but preserve empty strings to handle all lines
            lines = status_output.rstrip('\n').split('\n') if status_output.rstrip('\n') else []

            for line in lines:
                if not line:
                    continue
                # Git status --porcelain format: XY filename
                # X = staged status, Y = working tree status
                if len(line) >= 3:
                    staged_status = line[0] if len(line) > 0 else ' '
                    working_status = line[1] if len(line) > 1 else ' '
                    filename = line[3:] if len(line) > 3 else ''

                    if not filename:
                        continue

                    if staged_status == '?' and working_status == '?':
                        untracked.append(filename)
                    elif working_status == 'M':  # Modified in working tree
                        modified.append(filename)
                    elif working_status == 'D':  # Deleted in working tree
                        deleted.append(filename)

        # Show unstaged changes
        changes_shown = False
        if modified or deleted:
            print("Changes not staged for commit:")
            print('  (use "git add <file>..." to update what will be committed)')
            print('  (use "git restore <file>..." to discard changes in working directory)')
            for f in sorted(modified):
                print(f"\tmodified:   {f}")
            for f in sorted(deleted):
                print(f"\tdeleted:    {f}")
            changes_shown = True

        # Show untracked files
        if untracked:
            if changes_shown:
                print()
            print("Untracked files:")
            print('  (use "git add <file>..." to include in what will be committed)')
            for f in sorted(untracked):
                print(f"\t{f}")
            changes_shown = True

        # Final message
        if not changes_shown:
            print("nothing to commit, working tree clean")
        else:
            print()
            if untracked and not modified and not deleted:
                print("nothing added to commit but untracked files present (use \"git add\" to track)")
            elif modified or deleted:
                print("no changes added to commit (use \"git add\" and/or \"git commit -a\")")
    except Exception as e:
        # Fallback to simple message if something goes wrong
        print("No changes staged for commit")

def get_staged_files(amend=False):
    """Get list of staged files with their staged contents."""
    if amend:
        # For --amend, get files from the last commit plus any newly staged files
        # First, get files from the last commit
        last_commit_files = run_command('git diff-tree --no-commit-id --name-only -r HEAD').strip()
        # Then, get any newly staged files
        staged_files = run_command('git diff --cached --name-only').strip()

        # Combine and deduplicate
        all_filenames = set()
        if last_commit_files:
            all_filenames.update(last_commit_files.split('\n'))
        if staged_files:
            all_filenames.update(staged_files.split('\n'))

        files_output = '\n'.join(sorted(all_filenames))
    else:
        files_output = run_command('git diff --cached --name-only').strip()

    if not files_output:
        return ""

    all_files = []
    for filename in files_output.split('\n'):
        if filename:
            try:
                # For amend, try to get staged version first, then fall back to HEAD version
                if amend:
                    # Try staged version first
                    staged_content = run_command(f'git show :{filename}', check=False)
                    if not staged_content and 'fatal:' in staged_content:
                        # Fall back to HEAD version
                        staged_content = run_command(f'git show HEAD:{filename}', check=False)
                    staged_content = staged_content.strip()
                else:
                    # Get the staged content of the file (what's in the index)
                    staged_content = run_command(f'git show :{filename}', check=False).strip()

                if staged_content or staged_content == "":  # Include empty files too
                    all_files.append(f"{filename}\n```\n{staged_content}\n```\n")
            except Exception:
                # File might be newly added or binary, skip it
                continue

    return '\n'.join(all_files)

def get_git_diff(amend=False):
    """Get the git diff of staged changes."""
    if amend:
        # For --amend, show the diff of the last commit plus any new staged changes
        # Get the parent of HEAD (or use empty tree if it's the first commit)
        try:
            parent = run_command('git rev-parse HEAD^').strip()
            # Diff from parent to current index (staged changes + last commit)
            diff = run_command(f'git diff {parent}..HEAD').strip()
            # Also include any newly staged changes
            staged_diff = run_command('git diff --cached').strip()
            if staged_diff:
                diff = f"{diff}\n\n# Additional staged changes:\n{staged_diff}" if diff else staged_diff
        except:
            # First commit, use empty tree
            diff = run_command('git diff --cached').strip()
    else:
        diff = run_command('git diff --cached').strip()

    return f"```\n{diff}\n```"

def get_git_editor():
    """Get the configured git editor."""
    # Check environment variables first
    editor = os.environ.get('GIT_EDITOR')
    if editor:
        return editor

    editor = os.environ.get('EDITOR')
    if editor:
        return editor

    # Try git config
    try:
        editor = run_command('git config --get core.editor', check=False).strip()
        if editor:
            return editor
    except:
        pass

    # Default fallback
    return 'vi'

def get_current_branch():
    """Get current git branch name."""
    try:
        branch = run_command('git branch --show-current').strip()
        if not branch:  # detached HEAD state
            return run_command('git rev-parse --short HEAD').strip()
        return branch
    except:
        return 'unknown'

def get_git_dir():
    """Get the .git directory path."""
    # This should never fail since we check in main(), but just in case
    return run_command('git rev-parse --git-dir').strip()

def make_api_request(config, message):
    """Make API request to generate commit message."""
    payload = {
        'model': config['model'],
        'messages': [
            {
                'role': 'user',
                'content': message
            }
        ]
    }

    req = Request(
        config['api_url'],
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config['api_key']}"
        }
    )

    try:
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['choices'][0]['message']['content']
    except (URLError, HTTPError) as e:
        print(f"Error: Failed to make API request: {e}")
        sys.exit(1)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error: Failed to parse API response: {e}")
        sys.exit(1)

def create_commit_message_file(git_dir, commit_message, amend=False):
    """Create the commit message file with git template."""
    commit_file = os.path.join(git_dir, 'COMMIT_EDITMSG')

    with open(commit_file, 'w') as f:
        f.write(commit_message)
        f.write('\n\n')
        f.write('# Please enter the commit message for your changes. Lines starting\n')
        f.write("# with '#' will be ignored, and an empty message aborts the commit.\n")
        f.write('#\n')
        if amend:
            f.write('# You are amending the previous commit.\n')
            f.write('#\n')
        f.write(f'# On branch {get_current_branch()}\n')
        f.write('#\n')

        if amend:
            # Show what will be in the amended commit
            f.write('# Changes to be committed (including previous commit):\n')
            # Get files from last commit and staged
            try:
                last_commit_files = run_command('git diff-tree --no-commit-id --name-status -r HEAD')
                if last_commit_files:
                    for line in last_commit_files.split('\n'):
                        if line:
                            f.write(f'# {line}\n')
            except:
                pass

            # Also show newly staged files if any
            staged_status = run_command('git diff --cached --name-status')
            if staged_status.strip():
                f.write('# \n')
                f.write('# Additional staged changes:\n')
                for line in staged_status.split('\n'):
                    if line:
                        f.write(f'# {line}\n')
        else:
            f.write('# Changes to be committed:\n')
            # Get staged files status
            status = run_command('git diff --cached --name-status')
            for line in status.split('\n'):
                if line:
                    f.write(f'# {line}\n')
        f.write('#\n')

    return commit_file

def open_editor(filepath, editor):
    """Open file in editor and wait for it to close."""
    try:
        subprocess.run([editor, filepath])
    except Exception:
        print(f"Error: Failed to open editor: {editor}")
        sys.exit(1)

def is_commit_message_empty(filepath):
    """Check if commit message is empty (ignoring comments)."""
    try:
        with open(filepath, 'r') as f:
            for line in f:
                # Strip only trailing whitespace to preserve intentional indentation
                line = line.rstrip('\n\r')
                # Skip empty lines
                if not line or not line.strip():
                    continue
                # Check if this line is a comment (accounting for leading whitespace)
                if not line.lstrip().startswith('#'):
                    # Found actual content (non-comment, non-empty line)
                    return False
        return True
    except (IOError, OSError) as e:
        # More specific exception handling to avoid bare except
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate AI-powered git commit messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  git-commitai                    # Generate commit message for staged changes
  git-commitai -m "context"       # Add context about the changes
  git-commitai --amend            # Amend the previous commit with new message
  git-commitai --amend -m "fix"   # Amend with context

Environment variables:
  GIT_COMMIT_AI_KEY     Your API key (required)
  GIT_COMMIT_AI_URL     API endpoint URL (default: OpenAI)
  GIT_COMMIT_AI_MODEL   Model to use (default: gpt-4o)

For more information, visit: https://github.com/semperai/git-commitai
        """
    )
    parser.add_argument('-m', '--message', help='Additional context about the commit')
    parser.add_argument('--amend', action='store_true', help='Amend the previous commit')
    parser.add_argument('--version', action='version', version='git-commitai 1.0.1')
    args = parser.parse_args()

    # Check if in a git repository first
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'],
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("fatal: not a git repository (or any of the parent directories): .git")
        sys.exit(128)  # Git's standard exit code for this error

    # Check for staged changes or if we're amending
    if not check_staged_changes(amend=args.amend):
        sys.exit(1)

    # Get configuration
    config = get_env_config()

    # Build the prompt
    prompt = """You are a git commit message generator. Generate ONLY the commit message without any additional text, explanations, or prefixes like 'Here's the commit message' or 'Sure'.

The first line should be a concise summary (50 characters or less if possible).
If needed, add a blank line and then a more detailed explanation.
Focus on WHAT changed and WHY it changed.
Do not include any conversational text, only the commit message itself."""

    if args.message:
        prompt += f"\n\nUser context about this commit: {args.message}"

    # Get git information
    git_diff = get_git_diff(amend=args.amend)
    all_files = get_staged_files(amend=args.amend)

    prompt += f"""

Here is the git diff:

{git_diff}

Here are all of the files for context:

{all_files}"""

    # Make API request
    commit_message = make_api_request(config, prompt)

    # Get git directory
    git_dir = get_git_dir()

    # Create commit message file
    commit_file = create_commit_message_file(git_dir, commit_message, amend=args.amend)

    # Get modification time before editing
    mtime_before = os.path.getmtime(commit_file)

    # Open editor
    editor = get_git_editor()
    open_editor(commit_file, editor)

    # Check if file was modified (saved)
    mtime_after = os.path.getmtime(commit_file)

    if mtime_before == mtime_after:
        # File wasn't saved (user did :q! or equivalent)
        print("Aborting commit due to empty commit message.")
        sys.exit(1)

    # Check if message is empty
    if is_commit_message_empty(commit_file):
        print("Aborting commit due to empty commit message.")
        sys.exit(1)

    # Perform the commit
    try:
        if args.amend:
            subprocess.run(['git', 'commit', '--amend', '-F', commit_file], check=True)
        else:
            subprocess.run(['git', 'commit', '-F', commit_file], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == '__main__':
    main()
