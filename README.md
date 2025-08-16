# Git Commit AI

<div align="center">
  <br />
  <p>
    <a href="https://github.com/semperai/git-commitai">
      <img src="logo.webp" alt="Git Commit AI Logo" width="200" />
    </a>
  </p>
  <h3 align="center">Git Commit AI</h3>
  <p align="center">
    <strong>Intelligent commit messages powered by AI</strong>
    <br />
    <br />
    <a href="https://github.com/semperai/git-commitai#features">Features</a>
    ·
    <a href="https://github.com/semperai/git-commitai#installation">Installation</a>
    ·
    <a href="https://github.com/semperai/git-commitai#usage">Usage</a>
    ·
    <a href="https://github.com/semperai/git-commitai/issues">Report Bug</a>
  </p>
  <br />

  <!-- Badges -->
  <p>
    <a href="https://github.com/semperai/git-commitai/stargazers">
      <img src="https://img.shields.io/github/stars/semperai/git-commitai?style=for-the-badge" alt="Stars" />
    </a>
    <a href="https://github.com/semperai/git-commitai/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/semperai/git-commitai/tests.yml?style=for-the-badge&label=Tests" alt="Tests" />
    </a>
    <a href="https://codecov.io/gh/semperai/git-commitai">
      <img src="https://img.shields.io/codecov/c/github/semperai/git-commitai?style=for-the-badge" alt="Coverage" />
    </a>
    <a href="https://github.com/semperai/git-commitai/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/semperai/git-commitai?style=for-the-badge" alt="License" />
    </a>
  </p>

  <!-- Language and compatibility badges -->
  <p>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    </a>
    <a href="https://github.com/psf/black">
      <img src="https://img.shields.io/badge/Code%20Style-Black-000000?style=for-the-badge&logo=python&logoColor=white" alt="Code style" />
    </a>
    <a href="https://git-scm.com/">
      <img src="https://img.shields.io/badge/Git-2.0+-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git" />
    </a>
  </p>
</div>

<br />

---

<div align="center">
  <p align="center">
    An intelligent git commit message generator that uses AI to analyze your staged changes and generate meaningful, conventional commit messages. Works seamlessly with your existing git workflow.
  </p>
</div>

---

## ✨ Features

- 🤖 **AI-powered commit message generation** - Analyzes your code changes and generates descriptive commit messages
- 📝 **Works like native `git commit`** - Same workflow: save to commit, quit to abort
- 🔧 **Provider agnostic** - Works with OpenAI, OpenRouter, Anthropic, local LLMs, or any OpenAI-compatible API
- ✏️ **Full editor integration** - Uses your configured git editor for message editing
- 📊 **Context aware** - Includes both the diff and full file contents for better understanding
- 💬 **Additional context support** - Optional `-m` flag for providing extra context about your changes
- 🔄 **Amend support** - Use `--amend` to update the previous commit with AI-generated messages
- 🚀 **Auto-staging** - Use `-a` to automatically stage all tracked, modified files
- 🔒 **Binary file aware** - Intelligently handles binary files without breaking
- ⚡ **Hook skipping** - Use `-n` to bypass pre-commit hooks when needed
- 👀 **Verbose mode** - Use `-v` to see the full diff in your editor

## 📦 Installation

### Quick Install

1. Download the script:
```bash
curl -O https://raw.githubusercontent.com/semperai/git-commitai/main/git_commitai.py
chmod +x git_commitai.py
```

2. Install as a git command (choose one method):

#### Method 1: Git Alias (Simplest)
```bash
git config --global alias.commitai '!python3 '"$(pwd)/git_commitai.py"
```
Now you can use: `git commitai`

#### Method 2: Add to PATH with wrapper script
```bash
# Create a wrapper script
echo '#!/bin/bash\npython3 /path/to/git_commitai.py "$@"' > git-commitai
chmod +x git-commitai
sudo mv git-commitai /usr/local/bin/
```
Now you can use: `git commitai`

#### Method 3: Direct execution
```bash
# Just run directly
python3 git_commitai.py
# Or make it executable
chmod +x git_commitai.py
./git_commitai.py
```

## ⚙️ Configuration

Set up your environment variables based on your AI provider:

### OpenRouter (Recommended - Access to many models)
```bash
export GIT_COMMIT_AI_KEY="sk-or-v1-..."
export GIT_COMMIT_AI_URL="https://openrouter.ai/api/v1/chat/completions"
export GIT_COMMIT_AI_MODEL="openai/gpt-4o"  # or "anthropic/claude-3.5-sonnet" etc.
```

Add to your `~/.bashrc` or `~/.zshrc` to make permanent:
```bash
echo 'export GIT_COMMIT_AI_KEY="sk-or-v1-..."' >> ~/.bashrc
echo 'export GIT_COMMIT_AI_URL="https://openrouter.ai/api/v1/chat/completions"' >> ~/.bashrc
echo 'export GIT_COMMIT_AI_MODEL="openai/gpt-4o"' >> ~/.bashrc
```

### Other Providers

<details>
<summary>OpenAI</summary>

```bash
export GIT_COMMIT_AI_KEY="sk-..."
export GIT_COMMIT_AI_URL="https://api.openai.com/v1/chat/completions"
export GIT_COMMIT_AI_MODEL="gpt-4o"
```
</details>

<details>
<summary>Anthropic Claude</summary>

```bash
export GIT_COMMIT_AI_KEY="sk-ant-..."
export GIT_COMMIT_AI_URL="https://api.anthropic.com/v1/messages"
export GIT_COMMIT_AI_MODEL="claude-3-opus-20240229"
```
</details>

<details>
<summary>Local LLMs (Ollama)</summary>

```bash
export GIT_COMMIT_AI_KEY="not-needed"
export GIT_COMMIT_AI_URL="http://localhost:11434/v1/chat/completions"
export GIT_COMMIT_AI_MODEL="llama2"
```
</details>

<details>
<summary>Azure OpenAI</summary>

```bash
export GIT_COMMIT_AI_KEY="your-azure-key"
export GIT_COMMIT_AI_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15"
export GIT_COMMIT_AI_MODEL="gpt-4"
```
</details>

## 🚀 Usage

### Command Line Options

```bash
git-commitai [options]

Options:
  -m, --message TEXT    Additional context about the commit
  -a, --all            Automatically stage all tracked, modified files
  -n, --no-verify      Skip pre-commit and commit-msg hooks
  -v, --verbose        Show diff of changes in the editor
  --amend              Amend the previous commit
  --version            Show version information
  -h, --help           Show help message
```

### Basic Usage
```bash
# Stage your changes
git add .

# Generate commit message
git commitai

# The AI will analyze your changes and open your editor with a suggested message
# Save and exit to commit, or quit without saving to abort
```

### Auto-stage and Commit (`-a` flag)
```bash
# Make changes to tracked files
vim existing-file.py

# Auto-stage all tracked changes and commit
git commitai -a

# With context
git commitai -a -m "Refactored error handling"

# Note: -a only stages tracked files, not new untracked files
# For new files, you still need: git add new-file.py
```

### Skip Hooks (`-n` flag)
```bash
# Skip pre-commit hooks (useful for WIP commits)
git commitai -n

# Skip hooks with auto-staging
git commitai -a -n

# Emergency fix - bypass all checks
git commitai -a -n -m "Emergency production fix"
```

### Verbose Mode (`-v` flag)
```bash
# See the full diff in your editor while writing the message
git commitai -v

# Review everything: auto-stage and show diff
git commitai -a -v

# Maximum visibility
git commitai -a -v -m "Major refactor"
```

### With Additional Context
```bash
git commitai -m "This refactors the auth system to use JWT tokens instead of sessions"
```

### Amending Previous Commits
```bash
# Amend the last commit with a new AI-generated message
git commitai --amend

# Amend with additional context for the AI
git commitai --amend -m "Fixed the race condition and improved error handling"

# Stage new changes and amend them into the previous commit
git add fixed-file.js
git commitai --amend
```

### Combining Flags
```bash
# Auto-stage, skip hooks, show diff
git commitai -a -n -v

# Auto-stage with context
git commitai -a -m "Performance improvements"

# Verbose amend
git commitai --amend -v

# Skip hooks for amend
git commitai --amend -n
```

## 📚 Workflow Examples

### Standard Workflow
```bash
# Make some changes
echo "console.log('Hello World')" >> app.js
git add app.js

# Generate AI commit message
git commitai

# Your editor opens with something like:
# Add console log statement to app.js
#
# Added a Hello World console output for debugging purposes.
# This is a temporary addition for testing the application startup.
```

### Quick Fix Workflow
```bash
# Fix a bug quickly
vim buggy-file.js

# Auto-stage and commit with context, skip hooks
git commitai -a -n -m "Hotfix for null pointer exception"
```

### Review Before Commit Workflow
```bash
# Make multiple changes
vim file1.py file2.py file3.py

# Auto-stage and review all changes
git commitai -a -v

# Editor shows the AI message plus the full diff below
# Review everything, adjust message if needed, then commit
```

### WIP (Work in Progress) Workflow
```bash
# Save work in progress, bypassing checks
git commitai -a -n -m "WIP: Implementing new feature"

# Later, amend with proper commit
git commitai --amend -m "Implement user profile feature"
```

## 🎯 Flag Details

### `-a, --all` - Auto-stage Tracked Files
- Automatically runs `git add -u` before committing
- Only stages **tracked** files that have been modified or deleted
- Does **NOT** stage untracked (new) files
- Equivalent to `git commit -a`
- Cannot be used with `--amend`

### `-n, --no-verify` - Skip Git Hooks
- Bypasses pre-commit and commit-msg hooks
- Useful for:
  - WIP (Work in Progress) commits
  - Emergency hotfixes
  - Temporarily broken code
  - Skipping time-consuming checks
- Use with caution - hooks exist for a reason!

### `-v, --verbose` - Show Diff in Editor
- Displays the full diff below the commit message
- Diff appears after a scissors line (`>8`)
- Everything below the scissors is ignored by git
- Helps you review changes while writing the message
- Especially useful for large or complex commits

### `--amend` - Modify Previous Commit
- Replaces the last commit with a new one
- Generates new AI message based on all changes
- Includes both previous commit changes and any new staged changes
- Cannot be used with `-a` flag

## 🛠️ How It Works

1. **Analyzes staged changes**: Reads `git diff --cached` to understand what changed
2. **Detects file types**: Identifies and handles binary files appropriately
3. **Gathers context**: Includes full file contents for better understanding
4. **Calls AI API**: Sends the context to your configured AI model
5. **Opens editor**: Places the generated message in your git editor
6. **Applies flags**: Handles auto-staging, hook skipping, and verbose mode
7. **Commits or aborts**: Just like regular `git commit` - save to commit, quit to abort

## 💡 Tips & Best Practices

### Commit Message Quality
- **Better results with context**: Use `-m` flag to explain WHY you made changes
- **Model selection**: GPT-4 or Claude models generally produce better commit messages
- **Cost optimization**: For simple changes, smaller models like `gpt-3.5-turbo` work well

### Workflow Tips
- **Review large changes**: Use `-v` flag for complex commits to review while writing
- **Quick fixes**: Combine `-a -n` for rapid iterations during development
- **Amending commits**: Use `--amend` to fix the last commit instead of creating new ones
- **WIP commits**: Use `-n -m "WIP: ..."` for work-in-progress saves

### Editor Shortcuts
- **vim**: `:wq` to save and commit, `:q!` to abort
- **nano**: `Ctrl+O, Enter, Ctrl+X` to save, `Ctrl+X` to abort
- **VS Code**: `Ctrl+S, Ctrl+W` to save, close without saving to abort
- **emacs**: `Ctrl+X Ctrl+S, Ctrl+X Ctrl+C` to save and exit

## 🔧 Troubleshooting

### "API key not set" error
Make sure you've exported your API key:
```bash
export GIT_COMMIT_AI_KEY="your-key-here"
```

### "No staged changes" error
Stage your changes first or use the `-a` flag:
```bash
git add .
# OR
git commitai -a
```

### "Nothing to amend" error
This occurs when trying to use `--amend` with no previous commit. Make a normal commit first:
```bash
git commitai  # without --amend
```

### "Cannot use -a/--all with --amend" error
The `-a` flag doesn't work with `--amend`. Stage changes manually:
```bash
git add .
git commitai --amend
```

### Empty response from API
- Check your API key is valid
- Verify the API URL is correct for your provider
- Ensure the model name is supported by your provider

### Script not found when using `git commitai`
Make sure the script is in your PATH or properly aliased:
```bash
which git-commitai  # Should show the path
git config --get alias.commitai  # Should show the alias if using that method
```

## 🔬 Advanced Configuration

### Using with different branches
You can set different models for different projects:
```bash
# In your project directory
git config core.commitai.model "gpt-4o"  # Premium model for important project
# In another project
git config core.commitai.model "gpt-3.5-turbo"  # Cheaper model for personal project
```

Then update the script to check git config:
```python
MODEL="${GIT_COMMIT_AI_MODEL:-$(git config core.commitai.model || echo 'gpt-4o')}"
```

### Custom System Prompts
You can modify the prompt in the script to match your team's commit message conventions:
```python
prompt = "Generate a conventional commit message (feat/fix/docs/style/refactor/test/chore)..."
```

### Hook Integration
Create a prepare-commit-msg hook to always use git-commitai:
```bash
#!/bin/sh
# .git/hooks/prepare-commit-msg
if [ -z "$2" ]; then
  git-commitai
fi
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](#development) below.

### Development

#### Setting Up Development Environment

1. **Clone the repository:**
```bash
git clone https://github.com/semperai/git-commitai.git
cd git-commitai
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies:**
```bash
pip install -r requirements.txt
```

#### Running Tests

```bash
# Run all tests
pytest test_git_commitai.py -v

# Run with coverage report
pytest test_git_commitai.py -v --cov=git_commitai --cov-report=term-missing

# Run specific test class
pytest test_git_commitai.py::TestAutoStageFlag -v

# Run specific test
pytest test_git_commitai.py::TestGitStatus::test_parse_porcelain_modified_files -v

# Generate HTML coverage report
pytest test_git_commitai.py --cov=git_commitai --cov-report=html
# Open htmlcov/index.html in your browser
```

#### Code Quality

```bash
# Format code with black
black git_commitai.py test_git_commitai.py

# Check formatting without changing files
black --check git_commitai.py test_git_commitai.py

# Run linting
flake8 git_commitai.py test_git_commitai.py --max-line-length=100

# Type checking (optional)
mypy git_commitai.py
```

#### Writing Tests

When adding new features or fixing bugs, please include tests:

1. Add test cases to `test_git_commitai.py`
2. Follow the existing test structure
3. Ensure all tests pass before submitting PR
4. Aim for high code coverage (>90%)

Example test structure:
```python
class TestNewFeature:
    """Test the new feature functionality."""
    
    def test_new_feature_basic(self):
        """Test basic functionality of new feature."""
        with patch('git_commitai.some_function') as mock_func:
            mock_func.return_value = 'expected'
            result = git_commitai.new_feature()
            assert result == 'expected'
    
    def test_new_feature_edge_case(self):
        """Test edge cases."""
        # Test implementation
```

#### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Format your code (`black git_commitai.py test_git_commitai.py`)
7. Commit your changes (you can use `git-commitai` itself!)
8. Push to your fork (`git push origin feature/amazing-feature`)
9. Open a Pull Request

#### CI/CD

All pull requests automatically run:
- Tests on Python 3.8, 3.9, 3.10, 3.11, and 3.12
- Cross-platform tests (Ubuntu, macOS, Windows)
- Code coverage reporting
- Linting and formatting checks

## 📄 License

MIT License - feel free to use and modify as needed.

---

**⚠️ Privacy Note**: This tool sends your code changes to external AI APIs. Ensure you have permission to share your code with third-party services and that you're not violating any confidentiality agreements.

## 🔒 License
This project is released under the MIT license as found in the [LICENSE](LICENSE) file.

## ✨ Star History
[![Star History](https://api.star-history.com/svg?repos=semperai/git-commitai&type=Date)](https://star-history.com/#semperai/git-commitai&Date)

## 🤗 Contributors
<a href="https://github.com/semperai/git-commitai/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=semperai/git-commitai" />
</a>
