# Contributing to Git Commit AI

Thanks for considering contributing to Git Commit AI! We welcome contributions from everyone, regardless of their level of experience.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Philosophy](#project-philosophy)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Type Checking](#type-checking)
- [Style Guidelines](#style-guidelines)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Style Guide](#python-style-guide)
  - [Documentation Style Guide](#documentation-style-guide)
- [Community](#community)

## Getting Started

- Make sure you have a [GitHub account](https://github.com/signup/free)
- Fork the repository on GitHub
- Read the [README.md](README.md) for an overview of the project
- Check the [Issues](https://github.com/semperai/git-commitai/issues) page for something to work on

## Project Philosophy

**IMPORTANT: Git Commit AI should be a perfect drop-in replacement for `git commit`**

Our core principle is that `git commitai` should behave EXACTLY like `git commit` in all cases, with the only difference being that we generate the commit message using AI. This means:

- **Every flag that `git commit` supports should work identically in `git commitai`**
- **The behavior, output, and side effects should match `git commit` precisely**
- **Any deviation from standard `git commit` behavior is considered a bug** (except for intentional modifications like the `-m` flag which provides AI context instead of the full message)
- **When in doubt, test what `git commit` does and match that behavior exactly**

If you find ANY behavior that doesn't match standard `git commit`, please report it as a bug. We want users to be able to alias `git commit` to `git commitai` without noticing any difference except better commit messages.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When you create a bug report on GitHub, there's an issue template that will guide you through providing all necessary information. The key information we need:

- How standard `git commit` behaves in your situation
- How `git commitai` behaves differently
- Clear reproduction steps
- Your environment details (OS, Python version, Git version, AI provider)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **If it's a git commit feature**: Reference the git documentation and explain how `git commit` implements it
- **If it's an AI/generation improvement**: Explain how it improves commit message quality
- **Provide specific examples** to demonstrate the improvement
- **Explain why this enhancement would be useful**

### Your First Code Contribution

Unsure where to begin? You can start by looking through these issues:

- Issues labeled `good first issue` - issues which should only require a few lines of code
- Issues labeled `help wanted` - issues which need extra attention
- Issues labeled `git-compatibility` - ensuring we match git commit behavior
- Issues labeled `documentation` - improvements to docs

Many of the best contributions involve implementing missing `git commit` flags. Check the README for the full list of unsupported flags.

### Pull Requests

Please follow these steps:

1. **Fork the repo** and create your branch from `master`
2. **Add tests** if you've added code that should be tested
3. **Test against real git** - Ensure your implementation matches `git commit` behavior
4. **Add type hints** to any new functions or modified code
5. **Run type checking** with `mypy` to ensure type safety
6. **Update documentation** if you've changed APIs or added features
7. **Ensure the test suite passes** with `pytest`
8. **Format your code** with `black` and check with `flake8`
9. **Issue the pull request**

## Development Setup

1. **Clone your fork:**
```bash
git clone https://github.com/YOUR_USERNAME/git-commitai.git
cd git-commitai
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install in development mode:**
```bash
pip install -e .
```

5. **Run the application:**
```bash
./git_commitai.py
```

## Testing

We use pytest for testing. Please write tests for any new functionality.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=git_commitai --cov-report=html

# Run specific test file
pytest tests/test_commit_message.py

# Run with verbose output
pytest -v
```

### Writing Tests

When testing git compatibility, always test against actual git behavior:

```python
def test_feature_matches_git():
    """Test that our implementation matches git commit behavior."""
    # Run the same operation with git commit
    git_result = subprocess.run(['git', 'commit', '--flag'], ...)

    # Run with git commitai
    our_result = subprocess.run(['git', 'commitai', '--flag'], ...)

    # Results should match (excluding commit message differences)
    assert git_result.returncode == our_result.returncode
    assert git_result.stderr == our_result.stderr  # Errors should be identical
```

## Type Checking

We use **type hints** and **mypy** for static type checking to catch bugs early and improve code maintainability.

### Running Type Checks

```bash
# Basic type checking
mypy git_commitai.py
```

### Adding Type Hints

All new code should include type hints:

```python
from typing import List, Optional, Dict, Any

def process_files(filenames: List[str], verbose: bool = False) -> Dict[str, Any]:
    """Process git files and return their status.

    Args:
        filenames: List of file paths to process
        verbose: Whether to output detailed information

    Returns:
        Dictionary containing file statuses and metadata
    """
    result: Dict[str, Any] = {}
    for filename in filenames:
        # Your code here
        pass
    return result
```

### Common Type Hints Patterns

```python
# Optional parameters (can be None)
def func(param: Optional[str] = None) -> None:
    pass

# Union types (multiple possible types)
from typing import Union
def get_value() -> Union[str, int]:
    pass

# Function that never returns normally
from typing import NoReturn
def exit_with_error(msg: str) -> NoReturn:
    print(msg)
    sys.exit(1)

# Subprocess results
import subprocess
result: subprocess.CompletedProcess[str] = subprocess.run(..., text=True)

# Type aliases for complex types
from typing import TypeAlias
ConfigDict: TypeAlias = Dict[str, Union[str, int, bool]]
```

### Fixing Type Errors

If mypy reports errors:

1. **Read the error carefully** - mypy errors are usually very descriptive
2. **Check the mypy documentation** for the specific error code
3. **Add appropriate type hints** or fix the type mismatch
4. **Use `cast()` sparingly** when you know better than mypy:
   ```python
   from typing import cast
   value = cast(str, ambiguous_value)  # Tell mypy this is definitely a str
   ```
5. **Use `# type: ignore` as a last resort** with a comment explaining why:
   ```python
   result = some_dynamic_operation()  # type: ignore # Third-party library returns Any
   ```

## Style Guidelines

### Git Commit Messages

We eat our own dog food! Use `git commitai` for your commits, or follow these conventions:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Style Guide

We follow PEP 8 with these tools:

- **Black** for code formatting (line length: 100)
- **Flake8** for linting
- **isort** for import sorting
- **mypy** for type checking

Run all checks before committing:

```bash
# Format code
black . --line-length 100

# Check linting
flake8 .

# Sort imports
isort .

# Type checking
mypy git_commitai.py

# Or run all checks at once
make lint  # If Makefile is available
```

### Documentation Style Guide

- Keep language clear and concise
- Update the man page (`git-commitai.1`) for user-facing changes
- Add docstrings with type hints to all functions:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function purpose.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input is provided

    Example:
        >>> example_function("test", 42)
        True
    """
    pass
```

## Adding Support for New Git Flags

If you're adding support for a new git commit flag:

1. **Study the git documentation and source code** - Understand EXACTLY how git implements this flag
2. **Test git's behavior extensively** - Try edge cases, combinations with other flags, error conditions
3. **Implement to match git precisely** - The behavior should be indistinguishable from git commit
4. **Add type hints** to all new functions and parameters
5. **Update the argument parser** in `git-commitai`
6. **Add comprehensive tests** that verify matching behavior with git
7. **Run mypy** to ensure type safety
8. **Update the man page** to document the flag
9. **Update the README.md** commands table to mark it as supported
10. **Add examples** showing the flag in use

Remember: If there's ANY difference from how `git commit` handles the flag, it's a bug that needs to be fixed.

## Testing Git Compatibility

Before submitting a PR for a new git flag:

```bash
# Test with git commit
git commit --your-flag --other-flags

# Test with git commitai
git commitai --your-flag --other-flags

# Run type checking
mypy git_commitai.py

# Run tests
pytest tests/
```

## Continuous Integration

Our CI pipeline automatically runs:
- **mypy** type checking
- **pytest** test suite
- **Coverage** reporting

Your PR must pass all CI checks before it can be merged.

## Community

- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For contributing code

## Recognition

Contributors will be recognized in our README.md. We appreciate all contributions, no matter how small!

## Questions?

Feel free to open an issue with the `question` label if you need help or clarification.

---

Thank you for contributing to Git Commit AI! 🎉
