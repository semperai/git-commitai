#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import json
import subprocess
import shlex
import argparse
import time
import re
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Dict, List, Optional, Tuple, Any, Union


# Global debug flag
DEBUG: bool = False

# Retry configuration constants
MAX_RETRIES: int = 3
RETRY_DELAY: int = 2  # seconds between retries
RETRY_BACKOFF: float = 1.5  # backoff multiplier for each retry

REQ_TIMEOUT: int = 300  # 5 minutes timeout for requests


def redact_secrets(message: Union[str, Any]) -> str:
    """Redact sensitive information from debug messages.

    Args:
        message: Message to redact (will be converted to string if not already)

    Returns:
        String with sensitive information redacted
    """
    if not isinstance(message, str):
        message = str(message)

    # Patterns for common sensitive data
    patterns: List[Tuple[str, Any]] = [
        # API keys (various formats)
        (r'\b[A-Za-z0-9]{32,}\b', lambda m: m.group()[:4] + '...' + m.group()[-4:] if len(m.group()) > 8 else 'REDACTED'),

        # Bearer tokens in Authorization headers
        (r'Bearer\s+[\w\-\.]+', 'Bearer [REDACTED]'),

        # Basic auth credentials
        (r'Basic\s+[\w\+/=]+', 'Basic [REDACTED]'),

        # API keys in various formats (key=value, apikey:value, etc.)
        (r'(api[_\-]?key|token|secret|password|auth|credential)["\']?\s*[:=]\s*["\']?[\w\-\.]+["\']?',
         lambda m: m.group().split(':')[0].split('=')[0] + '=[REDACTED]'),

        # Environment variable values for sensitive vars
        (r'GIT_COMMIT_AI_KEY["\']?\s*[:=]\s*["\']?[\w\-\.]+["\']?', 'GIT_COMMIT_AI_KEY=[REDACTED]'),

        # URLs with embedded credentials
        (r'(https?://)([^:]+):([^@]+)@', r'\1[USER]:[PASS]@'),

        # JSON values for sensitive keys
        (r'"(api_key|apiKey|token|secret|password|auth|credential)"\s*:\s*"[^"]*"',
         lambda m: f'"{m.group().split(":")[0].strip()[1:-1]}": "[REDACTED]"'),

        # OAuth tokens
        (r'oauth[_\-]?token["\']?\s*[:=]\s*["\']?[\w\-\.]+["\']?', 'oauth_token=[REDACTED]'),

        # SSH keys (partial redaction)
        (r'ssh-rsa\s+[\w\+/=]+', lambda m: 'ssh-rsa ' + m.group().split()[1][:10] + '...[REDACTED]'),

        # Private keys
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----',
         '-----BEGIN PRIVATE KEY-----\n[REDACTED]\n-----END PRIVATE KEY-----'),
    ]

    redacted: str = message
    for pattern, replacement in patterns:
        if callable(replacement):
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        else:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)

    return redacted


def debug_log(message: str) -> None:
    """Log debug messages if debug mode is enabled, with secret redaction.

    Args:
        message: Debug message to log
    """
    if DEBUG:
        # Redact sensitive information before logging
        safe_message: str = redact_secrets(message)
        print(f"DEBUG: {safe_message}", file=sys.stderr)


def show_man_page() -> bool:
    """Try to show the man page, fall back to help text if not available.

    Returns:
        True if man page was shown, False otherwise
    """
    try:
        # Try to use man command to show the man page
        result = subprocess.run(
            ["man", "git-commitai"],
            check=False
        )
        if result.returncode == 0:
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # If man page is not available, return False to show argparse help
    return False


def get_git_root() -> str:
    """Get the root directory of the git repository.

    Returns:
        Path to git repository root
    """
    try:
        return run_git(["rev-parse", "--show-toplevel"]).strip()
    except (subprocess.CalledProcessError, Exception):
        return os.getcwd()


def load_gitcommitai_config() -> Dict[str, Any]:
    """Load configuration from .gitcommitai file in the repository root.

    The .gitcommitai file should contain a prompt template with placeholders:
    - {CONTEXT} - User-provided context via -m flag
    - {DIFF} - The git diff of changes
    - {FILES} - The modified files with their content
    - {GITMESSAGE} - Content from .gitmessage template if exists
    - {AMEND_NOTE} - Note about amending if --amend is used

    Also supports optional model configuration.

    Returns:
        Dictionary containing configuration (may be empty)
    """
    debug_log("Looking for .gitcommitai configuration file")

    config: Dict[str, Any] = {}

    try:
        git_root: str = get_git_root()
        config_path: str = os.path.join(git_root, ".gitcommitai")

        if not os.path.exists(config_path):
            debug_log("No .gitcommitai file found")
            return config

        debug_log(f"Found .gitcommitai at: {config_path}")

        with open(config_path, 'r') as f:
            content: str = f.read()

        # Check if it's JSON format (for backward compatibility)
        content_stripped: str = content.strip()
        if content_stripped.startswith('{'):
            try:
                json_config: Dict[str, Any] = json.loads(content)
                # Extract only model and prompt from JSON
                if 'model' in json_config:
                    config['model'] = json_config['model']
                if 'prompt' in json_config:
                    config['prompt_template'] = json_config['prompt']
                debug_log("Loaded .gitcommitai as JSON format")
                return config
            except json.JSONDecodeError:
                debug_log("Failed to parse as JSON, treating as template")

        # Check for model specification at the top of the file
        lines: List[str] = content.split('\n')
        template_lines: List[str] = []

        for line in lines:
            # Check for model specification (e.g., "model: gpt-4" or "model=gpt-4")
            if line.strip().startswith('model:') or line.strip().startswith('model='):
                model_value: str = line.split(':', 1)[1] if ':' in line else line.split('=', 1)[1]
                config['model'] = model_value.strip()
                debug_log(f"Found model specification: {config['model']}")
            else:
                template_lines.append(line)

        # The rest is the prompt template
        prompt_template: str = '\n'.join(template_lines).strip()
        if prompt_template:
            config['prompt_template'] = prompt_template
            debug_log(f"Loaded prompt template ({len(prompt_template)} characters)")

    except Exception as e:  # Catch all exceptions
        debug_log(f"Error loading .gitcommitai: {e}")

    return config


def get_env_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Get configuration from environment variables, .gitcommitai file, and command line args.

    Args:
        args: Parsed command line arguments

    Returns:
        Configuration dictionary with API settings and repo config
    """
    debug_log("Loading environment configuration")

    # Load from .gitcommitai file first
    repo_config: Dict[str, Any] = load_gitcommitai_config()

    # Build final config with precedence: CLI args > env vars > .gitcommitai > defaults
    config: Dict[str, Any] = {
        "api_key": (
            args.api_key or
            os.environ.get("GIT_COMMIT_AI_KEY")
        ),
        "api_url": (
            args.api_url or
            os.environ.get("GIT_COMMIT_AI_URL", "https://openrouter.ai/api/v1/chat/completions")
        ),
        "model": (
            args.model or
            os.environ.get("GIT_COMMIT_AI_MODEL") or
            repo_config.get("model") or
            "qwen/qwen3-coder"
        ),
    }

    # Add repository-specific configuration
    config["repo_config"] = repo_config

    # Log config with redacted sensitive values
    debug_log(f"Config loaded - URL: {config['api_url']}, Model: {config['model']}, Key present: {bool(config['api_key'])}")
    debug_log(f"Repository config keys: {list(repo_config.keys())}")

    if not config["api_key"]:
        print("Error: GIT_COMMIT_AI_KEY environment variable is not set")
        print()
        print("Please set up your API credentials:")
        print("  export GIT_COMMIT_AI_KEY='your-api-key'")
        print(
            "  export GIT_COMMIT_AI_URL='https://openrouter.ai/api/v1/chat/completions' # or your provider's URL"
        )
        print("  export GIT_COMMIT_AI_MODEL='qwen/qwen3-coder' # or your preferred model")
        print()
        print("For quick setup, run: curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | bash")
        sys.exit(1)

    return config


def run_git(args: List[str], check: bool = True) -> str:
    """Run git with a list of args safely (no shell). Returns stdout text.

    Args:
        args: List of git command arguments
        check: Whether to raise exception on non-zero exit code

    Returns:
        Standard output from git command

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    debug_log(f"Running git command: git {' '.join(args)}")

    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=check
        )
        debug_log(f"Git command successful, output length: {len(result.stdout)} chars")
        return result.stdout
    except subprocess.CalledProcessError as e:
        debug_log(f"Git command failed with code {e.returncode}: {e.stderr}")
        if check:
            raise
        return e.stdout if e.stdout else ""


def build_ai_prompt(repo_config: Dict[str, Any], args: argparse.Namespace) -> str:
    """Build the AI prompt, incorporating repository-specific customization.

    Args:
        repo_config: Repository-specific configuration
        args: Parsed command line arguments

    Returns:
        Complete prompt string for AI
    """

    # Check if repository has a custom prompt template
    if repo_config.get('prompt_template'):
        debug_log("Using custom prompt template from .gitcommitai")

        # Read .gitmessage if it exists
        gitmessage_content: str = read_gitmessage_template() or ""

        # Prepare replacement values
        replacements: Dict[str, str] = {
            'CONTEXT': f"Additional context from user: {args.message}" if args.message else "",
            'GITMESSAGE': gitmessage_content,
            'AMEND_NOTE': "Note: You are amending the previous commit." if args.amend else "",
        }

        # Start with the template
        base_prompt: str = repo_config['prompt_template']

        # Replace placeholders - but don't add them yet for DIFF and FILES
        # We'll add those at the end of the function
        for key, value in replacements.items():
            if key not in ['DIFF', 'FILES']:
                placeholder: str = '{' + key + '}'
                if placeholder in base_prompt:
                    base_prompt = base_prompt.replace(placeholder, value)

        # Normalize excessive blank lines introduced by empty replacements
        base_prompt = re.sub(r"\n{3,}", "\n\n", base_prompt).strip("\n")

    else:
        # Use default prompt
        debug_log("Using default prompt")
        base_prompt = """You are a git commit message generator that follows Git best practices strictly.

CRITICAL RULES YOU MUST FOLLOW:

1. STRUCTURE:
   - If the change is simple and clear, use ONLY a subject line (single line commit)
   - For complex changes that need explanation, use subject + blank line + body
   - Never add a body unless it provides valuable context about WHY the change was made

2. SUBJECT LINE (FIRST LINE):
   - Maximum 50 characters (aim for less when possible)
   - Start with a capital letter
   - NO period at the end
   - Use imperative mood (e.g., "Add", "Fix", "Update", not "Added", "Fixes", "Updated")
   - Be concise but descriptive
   - Think: "If applied, this commit will [your subject line]"

3. BODY (ONLY if needed):
   - Leave one blank line after the subject
   - Wrap lines at 72 characters maximum
   - Explain WHAT changed and WHY, not HOW (the code shows how)
   - Focus on the motivation and context for the change
   - Use bullet points with "-" for multiple items if needed

4. GOOD SUBJECT LINE EXAMPLES:
   - "Add user authentication module"
   - "Fix memory leak in data processor"
   - "Update dependencies to latest versions"
   - "Refactor database connection logic"
   - "Remove deprecated API endpoints"

5. CODE ISSUE DETECTION:
   After generating the message, check the code changes for potential issues.
   If you detect any obvious problems, add warnings as Git-style comments after the commit message.
   These warnings help the developer catch bugs before committing.

   Look for these types of severe or critical issues:
   - Hardcoded secrets
   - Syntax errors or typos in variable names
   - null/undefined reference errors
   - Missing imports that will cause runtime errors

   Format warnings like this:
   # ⚠️  WARNING: [Brief description of issue]
   # Found in: [filename]
   # Details: [Specific concern]

6. OUTPUT FORMAT:
   - Generate the commit message following ALL formatting rules correctly
   - Add a blank line after the message
   - If code issues detected, add warning comments
   - NO explanations outside of warning comments
   - NO markdown formatting
   - NEVER warn about commit message formatting (you should generate it correctly)

Remember:
- Most commits only need a clear subject line
- You are responsible for generating a properly formatted message - don't warn about your own formatting
- Only warn about actual code issues that could cause problems"""

    # Add .gitmessage template context if available and not already included via template
    if not repo_config.get('prompt_template'):
        gitmessage_template: Optional[str] = read_gitmessage_template()
        if gitmessage_template:
            base_prompt += f"""

PROJECT-SPECIFIC COMMIT TEMPLATE/GUIDELINES:
The following template or guidelines are configured for this project. Use this as additional context
to understand the project's commit message conventions, but still follow the Git best practices above:

{gitmessage_template}
"""
            debug_log("Added .gitmessage template to prompt context")

        # Add user context
        if args.message:
            base_prompt += f"\n\nAdditional context from user: {args.message}"

    return base_prompt


def stage_all_tracked_files() -> bool:
    """Stage all tracked, modified files (equivalent to git add -u).

    Returns:
        True if successful, False otherwise
    """
    debug_log("Staging all tracked files with 'git add -u'")

    try:
        # git add -u stages all tracked files that have been modified or deleted
        # but does NOT add untracked files
        subprocess.run(["git", "add", "-u"], check=True, capture_output=True)
        debug_log("Successfully staged tracked files")
        return True
    except subprocess.CalledProcessError as e:
        debug_log(f"Failed to stage tracked files: {e}")
        print(f"Error: Failed to stage tracked files: {e}")
        return False


def check_staged_changes(amend: bool = False, auto_stage: bool = False, allow_empty: bool = False) -> bool:
    """Check if there are staged changes and provide git-like output if not.

    Args:
        amend: Whether we're amending a commit
        auto_stage: Whether to auto-stage tracked files
        allow_empty: Whether to allow empty commits

    Returns:
        True if we can proceed with commit, False otherwise
    """
    debug_log(f"Checking staged changes - amend: {amend}, auto_stage: {auto_stage}, allow_empty: {allow_empty}")

    if auto_stage and not amend:
        # First, check if there are any changes to stage
        try:
            # Check for modified tracked files
            result = subprocess.run(["git", "diff", "--quiet"], capture_output=True)
            if result.returncode != 0:
                debug_log("Found unstaged changes, auto-staging them")
                # There are unstaged changes in tracked files, stage them
                if not stage_all_tracked_files():
                    return False
            else:
                debug_log("No unstaged changes to auto-stage")
            # Continue to check if we now have staged changes
        except subprocess.CalledProcessError:
            pass

    if amend:
        # For --amend, we're modifying the last commit, so we don't need staged changes
        # But we should check if there's a previous commit to amend
        try:
            run_git(["rev-parse", "HEAD"], check=True)
            debug_log("Found previous commit to amend")
            return True
        except subprocess.CalledProcessError:
            debug_log("No previous commit to amend")
            print("fatal: You have nothing to amend.")
            return False

    # If --allow-empty is set, we can proceed even without staged changes
    if allow_empty:
        debug_log("Allow empty flag set, proceeding without staged changes")
        return True

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], capture_output=True
        )
        if result.returncode == 0:
            debug_log("No staged changes found")
            # No staged changes - mimic git commit output
            show_git_status()
            return False
        debug_log("Found staged changes")
        return True
    except subprocess.CalledProcessError:
        return False


def show_git_status() -> None:
    """Show git status output similar to what 'git commit' shows."""
    debug_log("Showing git status")

    # Get branch name
    try:
        branch: str = run_git(["branch", "--show-current"]).strip()
        if not branch:  # detached HEAD state
            branch = run_git(["rev-parse", "--short", "HEAD"]).strip()
            print(f"HEAD detached at {branch}")
        else:
            print(f"On branch {branch}")
    except:
        print("On branch master")

    # Check if this is initial commit
    try:
        run_git(["rev-parse", "HEAD"], check=True)
    except:
        print("\nInitial commit\n")

    # Get untracked and modified files - don't strip to preserve all lines
    try:
        status_output: str = run_git(["status", "--porcelain"])

        untracked: List[str] = []
        modified: List[str] = []
        deleted: List[str] = []

        if status_output:
            # Split on newlines but preserve empty strings to handle all lines
            lines: List[str] = (
                status_output.rstrip("\n").split("\n")
                if status_output.rstrip("\n")
                else []
            )

            for line in lines:
                if not line:
                    continue
                # Git status --porcelain format: XY filename
                # X = staged status, Y = working tree status
                if len(line) >= 3:
                    staged_status: str = line[0] if len(line) > 0 else " "
                    working_status: str = line[1] if len(line) > 1 else " "
                    filename: str = line[3:] if len(line) > 3 else ""

                    if not filename:
                        continue

                    if staged_status == "?" and working_status == "?":
                        untracked.append(filename)
                    elif working_status == "M":  # Modified in working tree
                        modified.append(filename)
                    elif working_status == "D":  # Deleted in working tree
                        deleted.append(filename)

        # Show unstaged changes
        changes_shown: bool = False
        if modified or deleted:
            print("Changes not staged for commit:")
            print('  (use "git add <file>..." to update what will be committed)')
            print(
                '  (use "git restore <file>..." to discard changes in working directory)'
            )
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
                print(
                    'nothing added to commit but untracked files present (use "git add" to track)'
                )
            elif modified or deleted:
                print(
                    'no changes added to commit (use "git add" and/or "git commit -a")'
                )
    except Exception as e:
        debug_log(f"Error showing git status: {e}")
        # Fallback to simple message if something goes wrong
        print("No changes staged for commit")


def get_binary_file_info(filename: str, amend: bool = False) -> str:
    """Get information about a binary file.

    Args:
        filename: Path to the binary file
        amend: Whether we're amending a commit

    Returns:
        Formatted information about the binary file
    """
    debug_log(f"Getting binary file info for: {filename}")

    info_parts: List[str] = []

    # Get file extension
    _, ext = os.path.splitext(filename)
    if ext:
        info_parts.append(f"File type: {ext}")

    # Try to get file size from git
    try:
        size_output: str
        if amend:
            # Try to get size from index first, then HEAD
            size_output = run_git(["cat-file", "-s", f":{filename}"], check=False)
            if not size_output or "fatal:" in size_output:
                size_output = run_git(["cat-file", "-s", f"HEAD:{filename}"], check=False)
        else:
            size_output = run_git(["cat-file", "-s", f":{filename}"], check=False)

        if size_output and "fatal:" not in size_output:
            size_bytes: int = int(size_output.strip())
            size_str: str
            # Format size nicely
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            info_parts.append(f"Size: {size_str}")
    except:
        pass

    # Common binary file type descriptions
    binary_descriptions: Dict[str, str] = {
        ".jpg": "JPEG image",
        ".jpeg": "JPEG image",
        ".png": "PNG image",
        ".gif": "GIF image",
        ".webp": "WebP image",
        ".svg": "SVG vector image",
        ".ico": "Icon file",
        ".pdf": "PDF document",
        ".zip": "ZIP archive",
        ".tar": "TAR archive",
        ".gz": "Gzip compressed file",
        ".exe": "Windows executable",
        ".dll": "Dynamic link library",
        ".so": "Shared object library",
        ".dylib": "Dynamic library (macOS)",
        ".mp3": "MP3 audio",
        ".mp4": "MP4 video",
        ".avi": "AVI video",
        ".mov": "QuickTime video",
        ".ttf": "TrueType font",
        ".woff": "Web font",
        ".woff2": "Web font 2.0",
        ".db": "Database file",
        ".sqlite": "SQLite database",
    }

    if ext.lower() in binary_descriptions:
        info_parts.append(f"Description: {binary_descriptions[ext.lower()]}")

    # Check if it's a new file or modified
    try:
        if amend:
            # Check if file exists in parent commit
            run_git(["cat-file", "-e", f"HEAD^:{filename}"], check=True)
            info_parts.append("Status: Modified")
        else:
            # Check if file exists in HEAD
            run_git(["cat-file", "-e", f"HEAD:{filename}"], check=True)
            info_parts.append("Status: Modified")
    except:
        info_parts.append("Status: New file")

    return (
        "\n".join(info_parts)
        if info_parts
        else "Binary file (no additional information available)"
    )


def get_staged_files(amend: bool = False, allow_empty: bool = False) -> str:
    """Get list of staged files with their staged contents.

    Args:
        amend: Whether we're amending a commit
        allow_empty: Whether this is an empty commit

    Returns:
        Formatted string with file contents
    """
    debug_log(f"Getting staged files - amend: {amend}, allow_empty: {allow_empty}")

    files_output: str
    if amend:
        # For --amend, get files from the last commit plus any newly staged files
        # First, get files from the last commit
        last_commit_files: str = run_git(
            ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
        ).strip()
        # Then, get any newly staged files
        staged_files: str = run_git(["diff", "--cached", "--name-only"]).strip()

        # Combine and deduplicate
        all_filenames: set[str] = set()
        if last_commit_files:
            all_filenames.update(last_commit_files.split("\n"))
        if staged_files:
            all_filenames.update(staged_files.split("\n"))

        files_output = "\n".join(sorted(all_filenames))
    else:
        files_output = run_git(["diff", "--cached", "--name-only"]).strip()

    debug_log(f"Found {len(files_output.split()) if files_output else 0} staged files")

    if not files_output:
        if allow_empty:
            return "# No files changed (empty commit)"
        return ""

    all_files: List[str] = []
    for filename in files_output.split("\n"):
        if filename:
            try:
                # Check if file is binary
                is_binary_check: str
                if amend:
                    # For amend, check if file exists in index first, then HEAD
                    is_binary_check = run_git(
                        ["diff", "--cached", "--numstat", "--", filename], check=False
                    )
                    if not is_binary_check or "fatal:" in is_binary_check:
                        is_binary_check = run_git(
                            ["diff", "HEAD^", "HEAD", "--numstat", "--", filename], check=False
                        )
                else:
                    is_binary_check = run_git(
                        ["diff", "--cached", "--numstat", "--", filename], check=False
                    )

                # Git shows '-' for binary files in numstat
                if is_binary_check and is_binary_check.strip().startswith("-"):
                    # It's a binary file
                    file_info: str = get_binary_file_info(filename, amend)
                    all_files.append(
                        f"{filename} (binary file)\n```\n{file_info}\n```\n"
                    )
                else:
                    # It's a text file, get its content
                    staged_content: str
                    if amend:
                        # Try staged version first, then fall back to HEAD version
                        staged_content = run_git(
                            ["show", f":{filename}"], check=False
                        )
                        if not staged_content or "fatal:" in staged_content:
                            # Fall back to HEAD version
                            staged_content = run_git(
                                ["show", f"HEAD:{filename}"], check=False
                            )
                        staged_content = staged_content.strip()
                    else:
                        # Get the staged content of the file (what's in the index)
                        staged_content = run_git(
                            ["show", f":{filename}"], check=False
                        ).strip()

                    # Redact any secrets in file content before including in debug logs
                    debug_log(f"Processing file {filename} with content length: {len(staged_content)}")

                    if (
                        staged_content or staged_content == ""
                    ):  # Include empty files too
                        all_files.append(f"{filename}\n```\n{staged_content}\n```\n")
            except Exception as e:
                debug_log(f"Error processing file {filename}: {e}")
                # File might be newly added or have other issues, skip it
                continue

    return "\n".join(all_files) if all_files else "# No files changed (empty commit)"


def get_git_diff(amend: bool = False, allow_empty: bool = False) -> str:
    """Get the git diff of staged changes, with binary file handling.

    Args:
        amend: Whether we're amending a commit
        allow_empty: Whether this is an empty commit

    Returns:
        Formatted diff string
    """
    debug_log(f"Getting git diff - amend: {amend}, allow_empty: {allow_empty}")

    diff: str
    if amend:
        # For --amend, show the diff of the last commit plus any new staged changes
        # Get the parent of HEAD (or use empty tree if it's the first commit)
        try:
            parent: str = run_git(["rev-parse", "HEAD^"]).strip()
            # Diff from parent to current index (staged changes + last commit)
            diff = run_git(["diff", f"{parent}..HEAD"]).strip()
            # Also include any newly staged changes
            staged_diff: str = run_git(["diff", "--cached"]).strip()
            if staged_diff:
                diff = (
                    f"{diff}\n\n# Additional staged changes:\n{staged_diff}"
                    if diff
                    else staged_diff
                )
        except:
            # First commit, use empty tree
            diff = run_git(["diff", "--cached"]).strip()
    else:
        diff = run_git(["diff", "--cached"]).strip()

    debug_log(f"Diff size: {len(diff)} characters")

    if not diff and allow_empty:
        return "```\n# No changes (empty commit)\n```"

    # Process the diff to add information about binary files
    diff_lines: List[str] = diff.split("\n") if diff else []
    processed_lines: List[str] = []
    i: int = 0

    while i < len(diff_lines):
        line: str = diff_lines[i]

        # Check for binary file indicators
        if line.startswith("Binary files"):
            # Extract filename from the binary files line
            # Format: "Binary files a/path/file and b/path/file differ"
            parts: List[str] = line.split(" ")
            if len(parts) >= 4:
                file_a: str = parts[2].lstrip("a/")
                file_b: str = parts[4].lstrip("b/")
                # Use the 'b/' version as it's the new version
                filename: str = file_b if file_b != "/dev/null" else file_a

                # Add enhanced binary file information
                processed_lines.append(line)
                processed_lines.append(f"# Binary file: {filename}")

                # Try to get more info about the binary file
                binary_info: str = get_binary_file_info(filename, amend)
                for info_line in binary_info.split("\n"):
                    processed_lines.append(f"# {info_line}")
        else:
            processed_lines.append(line)

        i += 1

    processed_diff: str = "\n".join(processed_lines) if processed_lines else diff
    return f"```\n{processed_diff}\n```"


def get_git_editor() -> str:
    """Get the configured git editor.

    Returns:
        Editor command string
    """
    # Check environment variables first
    editor: Optional[str] = os.environ.get("GIT_EDITOR")
    if editor:
        return editor

    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Try git config
    try:
        editor = run_git(["config", "--get", "core.editor"], check=False).strip()
        if editor:
            return editor
    except:
        pass

    # Default fallback
    return "vi"


def get_current_branch() -> str:
    """Get current git branch name.

    Returns:
        Branch name or commit hash if detached
    """
    try:
        branch: str = run_git(["branch", "--show-current"]).strip()
        if not branch:  # detached HEAD state
            return run_git(["rev-parse", "--short", "HEAD"]).strip()
        return branch
    except:
        return "unknown"


def get_git_dir() -> str:
    """Get the .git directory path.

    Returns:
        Path to .git directory
    """
    # This should never fail since we check in main(), but just in case
    return run_git(["rev-parse", "--git-dir"]).strip()


def read_gitmessage_template() -> Optional[str]:
    """Read .gitmessage template file if it exists.

    Returns:
        Template content or None if not found
    """
    debug_log("Checking for .gitmessage template file")

    # 1. Check for .gitmessage in repository root (HIGHEST PRIORITY)
    try:
        git_root: str = get_git_root()
        repo_gitmessage: str = os.path.join(git_root, ".gitmessage")
        if os.path.isfile(repo_gitmessage):
            debug_log(f"Found repository .gitmessage: {repo_gitmessage}")
            try:
                with open(repo_gitmessage, 'r') as f:
                    content: str = f.read()
                debug_log("Successfully read repository .gitmessage template")
                debug_log(f"Template content length: {len(content)} characters")
                return content
            except (IOError, OSError) as e:
                debug_log(f"Failed to read repository template from {repo_gitmessage}: {e}")
    except Exception as e:
        debug_log(f"Error checking for repository .gitmessage: {e}")

    # 2. Check git config for commit.template (SECOND PRIORITY)
    try:
        configured_template: str = run_git(["config", "--get", "commit.template"], check=False).strip()
        if configured_template:
            # Expand ~ to home directory if present
            if configured_template.startswith("~"):
                configured_template = os.path.expanduser(configured_template)
            # If not absolute path, make it relative to git root
            elif not os.path.isabs(configured_template):
                try:
                    git_root = get_git_root()
                    configured_template = os.path.join(git_root, configured_template)
                except Exception:
                    pass

            if os.path.isfile(configured_template):
                debug_log(f"Found configured template: {configured_template}")
                try:
                    with open(configured_template, 'r') as f:
                        content = f.read()
                    debug_log(f"Successfully read configured template")
                    debug_log(f"Template content length: {len(content)} characters")
                    return content
                except (IOError, OSError) as e:
                    debug_log(f"Failed to read configured template from {configured_template}: {e}")
    except Exception as e:
        debug_log(f"Error checking for configured template: {e}")

    # 3. Check for global .gitmessage in home directory (LOWEST PRIORITY)
    try:
        home_gitmessage: str = os.path.expanduser("~/.gitmessage")
        if os.path.isfile(home_gitmessage):
            debug_log(f"Found home directory .gitmessage: {home_gitmessage}")
            try:
                with open(home_gitmessage, 'r') as f:
                    content = f.read()
                debug_log("Successfully read home directory .gitmessage template")
                debug_log(f"Template content length: {len(content)} characters")
                return content
            except (IOError, OSError) as e:
                debug_log(f"Failed to read home template from {home_gitmessage}: {e}")
    except Exception as e:
        debug_log(f"Error checking for home .gitmessage: {e}")

    debug_log("No .gitmessage template file found")
    return None


def show_dry_run_summary(args: argparse.Namespace) -> None:
    """Show what would be committed in dry-run mode by delegating to git.

    Args:
        args: Parsed command line arguments
    """
    debug_log("Dry-run mode: delegating to git commit --dry-run")

    # Build the git commit command with --dry-run
    commit_cmd: List[str] = ["git", "commit", "--dry-run"]

    # Add any other flags that were passed
    if args.amend:
        commit_cmd.append("--amend")

    if args.allow_empty:
        commit_cmd.append("--allow-empty")

    if args.no_verify:
        commit_cmd.append("--no-verify")

    if args.verbose:
        commit_cmd.append("--verbose")

    if args.author:
        commit_cmd.extend(["--author", args.author])

    if args.date:
        commit_cmd.extend(["--date", args.date])

    # If user provided a message context, we can add it as a placeholder message
    # (though it won't be shown in dry-run output)
    if args.message:
        commit_cmd.extend(["-m", "placeholder"])

    debug_log(f"Executing: {' '.join(commit_cmd)}")

    try:
        # Run git commit --dry-run and let it handle all the output
        result = subprocess.run(commit_cmd, check=False)
        # Exit with the same code that git returned
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        debug_log(f"Git commit --dry-run failed with code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        debug_log(f"Error running git commit --dry-run: {e}")
        print(f"Error: Failed to run git commit --dry-run: {e}")
        sys.exit(1)

def make_api_request(config: Dict[str, Any], message: str) -> str:
    """Make API request with retry logic.

    Args:
        config: Configuration dictionary with API settings
        message: Prompt message to send to API

    Returns:
        Generated commit message from AI

    Raises:
        SystemExit: On API failure after retries
    """
    debug_log(f"Making API request to {config['api_url']} with model {config['model']}")
    debug_log(f"Prompt length: {len(message)} characters")

    delay: float = RETRY_DELAY
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        debug_log(f"API request attempt {attempt}/{MAX_RETRIES}")

        try:
            payload: Dict[str, Any] = {
                "model": config["model"],
                "messages": [{"role": "user", "content": message}],
            }

            # Create request with headers (will be redacted in debug output)
            headers: Dict[str, str] = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['api_key']}",
            }

            # Log headers with explicitly redacted auth
            safe_headers = dict(headers)
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "Bearer [REDACTED]"
            debug_log(f"Request headers: {safe_headers}")

            req: Request = Request(
                config["api_url"],
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )

            with urlopen(req, timeout=REQ_TIMEOUT) as response:
                data: Dict[str, Any] = json.loads(response.read().decode("utf-8"))
                result: str = data["choices"][0]["message"]["content"]
                debug_log(f"API request successful on attempt {attempt}, response length: {len(result)} characters")
                return result

        except (URLError, HTTPError) as e:
            last_error = e
            error_msg: str = str(e)

            # Check if it's an HTTP error with a status code
            if isinstance(e, HTTPError):
                error_msg = f"HTTP {e.code}: {e.reason}"
                # Don't retry on client errors (4xx)
                if 400 <= e.code < 500:
                    debug_log(f"API request failed with client error, not retrying: {error_msg}")
                    print(f"Error: API request failed: {error_msg}")
                    sys.exit(1)

            debug_log(f"API request attempt {attempt} failed: {error_msg}")

            if attempt < MAX_RETRIES:
                debug_log(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= RETRY_BACKOFF

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            last_error = e
            debug_log(f"Failed to parse API response on attempt {attempt}: {e}")

            if attempt < MAX_RETRIES:
                debug_log(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= RETRY_BACKOFF

    # All retries exhausted
    debug_log(f"All {MAX_RETRIES} API request attempts failed")
    print(f"Error: Failed to make API request after {MAX_RETRIES} attempts: {last_error}")
    sys.exit(1)


def create_commit_message_file(
    git_dir: str,
    commit_message: str,
    amend: bool = False,
    auto_staged: bool = False,
    no_verify: bool = False,
    verbose: bool = False,
    allow_empty: bool = False,
    author: Optional[str] = None,
    date: Optional[str] = None,
) -> str:
    """Create the commit message file with git template.

    Args:
        git_dir: Path to .git directory
        commit_message: Generated commit message
        amend: Whether we're amending
        auto_staged: Whether files were auto-staged
        no_verify: Whether hooks will be skipped
        verbose: Whether to include diff
        allow_empty: Whether this is an empty commit
        author: Custom author if specified
        date: Custom date if specified

    Returns:
        Path to created commit message file
    """
    debug_log(f"Creating commit message file in {git_dir}")

    commit_file: str = os.path.join(git_dir, "COMMIT_EDITMSG")

    # Split the commit message to separate actual message from any AI-generated warnings
    # Warnings will start with "# ⚠️  WARNING:" and should appear first in comments
    message_lines: List[str] = commit_message.split('\n')
    actual_message: List[str] = []
    warning_comments: List[str] = []

    in_warnings: bool = False
    for line in message_lines:
        # Check if this line is part of a warning
        if (line.startswith('# ⚠️  WARNING:') or
            line.startswith('# Found in:') or
            line.startswith('# Details:') or
            (in_warnings and line.startswith('#'))):
            warning_comments.append(line)
            in_warnings = True
        elif line.strip() == '' and in_warnings:
            # Empty line in warnings section
            warning_comments.append(line)
        elif line.strip() == '':
            # Empty line not in warnings section
            actual_message.append(line)
            in_warnings = False
        else:
            in_warnings = False
            actual_message.append(line)

    # Reconstruct the actual commit message without warnings
    clean_message: str = '\n'.join(actual_message).rstrip()

    with open(commit_file, "w") as f:
        # Write the actual commit message
        f.write(clean_message)

        # Ensure proper spacing before comments section
        if not clean_message.endswith('\n'):
            f.write('\n')
        f.write('\n')

        # If there are AI-generated warnings, add them FIRST in the comment section
        if warning_comments:
            for idx, line in enumerate(warning_comments):
                if line.strip():  # Only write non-empty lines
                    f.write(f"{line}\n")
                elif idx < len(warning_comments) - 1:
                    # Write empty lines between warnings, but not at the end
                    f.write("#\n")
            f.write("#\n")  # Add separator after all warnings

        # Add Git's standard template comments
        f.write("# Please enter the commit message for your changes. Lines starting\n")
        f.write("# with '#' will be ignored, and an empty message aborts the commit.\n")
        f.write("#\n")
        if amend:
            f.write("# You are amending the previous commit.\n")
            f.write("#\n")
        if auto_staged:
            f.write("# Files were automatically staged using -a flag.\n")
            f.write("#\n")
        if no_verify:
            f.write("# Git hooks will be skipped (--no-verify).\n")
            f.write("#\n")
        if allow_empty:
            f.write("# This will be an empty commit (--allow-empty).\n")
            f.write("#\n")
        if author:
            f.write(f"# Using custom author: {author}\n")
            f.write("#\n")
        if date:
            f.write(f"# Using custom date: {date}\n")
            f.write("#\n")
        f.write(f"# On branch {get_current_branch()}\n")
        f.write("#\n")

        if amend:
            # Show what will be in the amended commit
            f.write("# Changes to be committed (including previous commit):\n")
            # Get files from last commit and staged
            try:
                last_commit_files: str = run_git(
                    ["diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD"]
                )
                if last_commit_files:
                    for line in last_commit_files.split("\n"):
                        if line:
                            f.write(f"# {line}\n")
            except:
                pass

            # Also show newly staged files if any
            staged_status: str = run_git(["diff", "--cached", "--name-status"])
            if staged_status.strip():
                f.write("# \n")
                f.write("# Additional staged changes:\n")
                for line in staged_status.split("\n"):
                    if line:
                        f.write(f"# {line}\n")
        elif allow_empty:
            # For empty commits, note that there are no changes
            f.write("# No changes to be committed (empty commit)\n")
        else:
            f.write("# Changes to be committed:\n")
            # Get staged files status
            status: str = run_git(["diff", "--cached", "--name-status"])
            for line in status.split("\n"):
                if line:
                    f.write(f"# {line}\n")
        f.write("#\n")

        # Add verbose diff if requested
        if verbose:
            f.write("# ------------------------ >8 ------------------------\n")
            f.write("# Do not modify or remove the line above.\n")
            f.write("# Everything below it will be ignored.\n")
            f.write("#\n")
            f.write("# Diff of changes to be committed:\n")
            f.write("#\n")

            # Get the appropriate diff
            diff_output: str
            if amend:
                # For amend, show diff from parent to current state
                try:
                    parent: str = run_git(["rev-parse", "HEAD^"]).strip()
                    diff_output = run_git(["diff", f"{parent}..HEAD"])
                    # Also include any newly staged changes
                    staged_diff: str = run_git(["diff", "--cached"])
                    if staged_diff.strip():
                        diff_output += "\n# Additional staged changes:\n" + staged_diff
                except:
                    # First commit or other issue, just show staged
                    diff_output = run_git(["diff", "--cached"])
            else:
                # Normal commit, show staged changes
                diff_output = run_git(["diff", "--cached"])

            # Add diff as comments
            if diff_output:
                for line in diff_output.split("\n"):
                    f.write(f"# {line}\n")
            elif allow_empty:
                f.write("# No changes (empty commit)\n")

    debug_log(f"Commit message file created: {commit_file}")
    return commit_file


def open_editor(filepath: str, editor: str) -> None:
    """Open file in editor and wait for it to close.

    Args:
        filepath: Path to file to edit
        editor: Editor command

    Raises:
        SystemExit: If editor fails to open
    """
    debug_log(f"Opening editor: {editor} {filepath}")

    try:
        # Use POSIX splitting except on Windows for better compatibility
        cmd: List[str] = shlex.split(editor, posix=(os.name != "nt")) + [filepath]

        subprocess.run(cmd)
        debug_log("Editor closed")
    except Exception as e:
        debug_log(f"Failed to open editor: {e}")
        print(f"Error: Failed to open editor: {editor}")
        sys.exit(1)


def strip_comments_and_save(filepath: str) -> bool:
    """Strip comment lines from commit message file and save it back.

    Args:
        filepath: Path to commit message file

    Returns:
        True if successful, False otherwise
    """
    debug_log(f"Stripping comments from file: {filepath}")

    clean_lines: List[str] = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                # If line starts with # (ignoring whitespace), it's a comment
                if line.lstrip().startswith("#"):
                    # Skip all comment lines
                    continue
                else:
                    # Keep non-comment lines
                    clean_lines.append(line)

        # Write back the cleaned message
        with open(filepath, "w") as f:
            # Remove trailing whitespace/newlines but keep internal structure
            content: str = "".join(clean_lines).rstrip()
            if content:
                f.write(content)
                f.write("\n")  # Ensure file ends with newline

            debug_log(f"Cleaned message: {repr(content[:100])}..." if len(content) > 100 else f"Cleaned message: {repr(content)}")

        debug_log(f"Stripped {len(clean_lines)} lines of content from commit message")
        return True
    except (IOError, OSError) as e:
        debug_log(f"Error processing commit message file: {e}")
        print(f"Error: Failed to process commit message: {e}")
        return False


def is_commit_message_empty(filepath: str) -> bool:
    """Check if commit message is empty (ignoring comments).

    Args:
        filepath: Path to commit message file

    Returns:
        True if message is empty, False otherwise
    """
    debug_log(f"Checking if commit message is empty: {filepath}")

    try:
        with open(filepath, "r") as f:
            for line in f:
                # Strip only trailing whitespace to preserve intentional indentation
                line = line.rstrip("\n\r")
                # Skip empty lines
                if not line or not line.strip():
                    continue
                # Check if this line is a comment (accounting for leading whitespace)
                if not line.lstrip().startswith("#"):
                    # Found actual content (non-comment, non-empty line)
                    debug_log("Commit message has content")
                    return False
        debug_log("Commit message is empty")
        return True
    except (IOError, OSError) as e:
        debug_log(f"Error reading commit message file: {e}")
        # More specific exception handling to avoid bare except
        return True


def main() -> None:
    """Main entry point for git-commitai."""
    global DEBUG

    # Check for --help flag early and show man page if available
    if "--help" in sys.argv or "-h" in sys.argv:
        if show_man_page():
            sys.exit(0)
        # fall through to argparse help

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate AI-powered git commit messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  git-commitai                    # Generate commit message for staged changes
  git-commitai -m "context"       # Add context about the changes
  git-commitai -a                 # Auto-stage all tracked files and commit
  git-commitai --amend            # Amend the previous commit with new message
  git-commitai --allow-empty      # Create an empty commit
  git-commitai --dry-run          # Show what would be committed without committing
  git-commitai --author "Name <email@example.com>"  # Override author
  git-commitai --date "2024-01-01T12:00:00"  # Override date
  git-commitai --debug            # Enable debug logging

Configuration:
  Create a .gitcommitai file in your repository root to customize the AI prompt.

  The file can optionally start with a model specification:
    model: gpt-4

  Then include your prompt template with placeholders:
    {CONTEXT} - User-provided context via -m flag
    {DIFF} - The git diff of changes
    {FILES} - The modified files with their content
    {GITMESSAGE} - Content from .gitmessage template if exists

  Example .gitcommitai file:
    model: gpt-4

    You are an expert git commit message generator for our project.

    Follow these rules:
    - Use conventional commits format (feat, fix, docs, etc.)
    - Maximum 50 characters for subject line
    - Use imperative mood

    {GITMESSAGE}
    {CONTEXT}

    Review these changes:
    {DIFF}

    Full file contents:
    {FILES}

    Generate a commit message:

Quick Install:
  curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | bash

Environment variables:
  GIT_COMMIT_AI_KEY     Your API key (required)
  GIT_COMMIT_AI_URL     API endpoint URL (default: OpenRouter)
  GIT_COMMIT_AI_MODEL   Model to use (default: qwen/qwen3-coder)

For full documentation, run: man git-commitai
For more information, visit: https://github.com/semperai/git-commitai
        """,
    )
    parser.add_argument("-m", "--message", help="Additional context about the commit")
    parser.add_argument(
        "--amend", action="store_true", help="Amend the previous commit"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Automatically stage all tracked, modified files",
    )
    parser.add_argument(
        "-n",
        "--no-verify",
        action="store_true",
        help="Skip pre-commit and commit-msg hooks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show diff of changes in the editor",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow creating an empty commit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually commit, just show what would be committed",
    )
    parser.add_argument(
        "--author",
        help="Override author information (format: 'Name <email@example.com>')",
    )
    parser.add_argument(
        "--date",
        help="Override author date (format: 'YYYY-MM-DD HH:MM:SS' or ISO 8601)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to stderr",
    )

    # Debug section arguments
    debug_group = parser.add_argument_group('debug options', 'Override API configuration (requires --debug)')
    debug_group.add_argument("--api-key", help="Override API key")
    debug_group.add_argument("--api-url", help="Override API URL")
    debug_group.add_argument("--model", help="Override model name")

    args: argparse.Namespace = parser.parse_args()

    # Enable debug mode if flag is set
    if args.debug:
        DEBUG = True
        debug_log("=" * 60)
        debug_log("Git Commit AI started with --debug flag")
        debug_log(f"Python version: {sys.version}")
        debug_log(f"Arguments: {sys.argv[1:]}")
        if args.dry_run:
            debug_log("DRY RUN MODE - No commit will be created")

    # Check if in a git repository first
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, check=True
        )
        debug_log("Git repository detected")
    except subprocess.CalledProcessError:
        debug_log("Not in a git repository")
        print("fatal: not a git repository (or any of the parent directories): .git")
        sys.exit(128)  # Git's standard exit code for this error

    # Check for conflicting flags
    if args.all and args.amend:
        debug_log("Conflicting flags: -a and --amend")
        print("Error: Cannot use -a/--all with --amend")
        print(
            "The --amend flag modifies the previous commit and doesn't auto-stage new changes."
        )
        sys.exit(1)

    # Check for staged changes or if we're amending or auto-staging or allowing empty
    if not check_staged_changes(amend=args.amend, auto_stage=args.all, allow_empty=args.allow_empty):
        sys.exit(1)

    # Get configuration (including repo-specific config)
    config: Dict[str, Any] = get_env_config(args)

    # Build the AI prompt using repository-specific customization
    prompt: str = build_ai_prompt(config["repo_config"], args)

    # Get git information
    git_diff: str = get_git_diff(amend=args.amend, allow_empty=args.allow_empty)
    all_files: str = get_staged_files(amend=args.amend, allow_empty=args.allow_empty)

    # Handle template placeholders if using custom template
    if config["repo_config"].get('prompt_template'):
        # Check if template has placeholders for DIFF and FILES
        if '{DIFF}' in prompt:
            prompt = prompt.replace('{DIFF}', git_diff)
        else:
            # Append at the end if no placeholder
            prompt += f"\n\nHere is the git diff of changes:\n\n{git_diff}"

        if '{FILES}' in prompt:
            prompt = prompt.replace('{FILES}', all_files)
        else:
            # Append at the end if no placeholder
            prompt += f"\n\nHere are all the modified files with their content for context:\n\n{all_files}"

        # Add final instruction if not already in template
        if "Generate the commit message" not in prompt and "generate the commit message" not in prompt.lower():
            prompt += "\n\nGenerate the commit message following the rules above:"
    else:
        # Default behavior - append diff and files
        prompt += f"""

Here is the git diff of changes:

{git_diff}

Here are all the modified files with their content for context:

{all_files}

Generate the commit message following the rules above:"""

    # Make API request with retry logic
    commit_message: str = make_api_request(config, prompt)

    # If dry-run mode, show what would be committed and exit
    if args.dry_run:
        debug_log("Dry-run mode: showing summary and exiting")
        show_dry_run_summary(args)
        sys.exit(0)

    # Get git directory
    git_dir: str = get_git_dir()

    # Create commit message file
    commit_file: str = create_commit_message_file(
        git_dir,
        commit_message,
        amend=args.amend,
        auto_staged=args.all,
        no_verify=args.no_verify,
        verbose=args.verbose,
        allow_empty=args.allow_empty,
        author=args.author,
        date=args.date,
    )

    # Get modification time before editing
    mtime_before: float = os.path.getmtime(commit_file)

    # Open editor
    editor: str = get_git_editor()
    open_editor(commit_file, editor)

    # Check if file was modified (saved)
    mtime_after: float = os.path.getmtime(commit_file)

    if mtime_before == mtime_after:
        # File wasn't saved (user did :q! or equivalent)
        debug_log("Commit aborted - file not saved")
        print("Aborting commit due to empty commit message.")
        sys.exit(1)

    # Check if message is empty
    if is_commit_message_empty(commit_file):
        debug_log("Commit aborted - empty message")
        print("Aborting commit due to empty commit message.")
        sys.exit(1)

    # Strip comments from the commit message file before committing
    if not strip_comments_and_save(commit_file):
        sys.exit(1)

    # Perform the commit
    try:
        commit_cmd: List[str] = ["git", "commit"]

        if args.amend:
            commit_cmd.append("--amend")

        if args.no_verify:
            commit_cmd.append("--no-verify")

        if args.allow_empty:
            commit_cmd.append("--allow-empty")

        if args.author:
            commit_cmd.extend(["--author", args.author])

        if args.date:
            commit_cmd.extend(["--date", args.date])

        commit_cmd.extend(["-F", commit_file])

        debug_log(f"Executing commit command: {' '.join(commit_cmd)}")
        subprocess.run(commit_cmd, check=True)
        debug_log("Commit successful")
    except subprocess.CalledProcessError as e:
        debug_log(f"Commit failed with code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
