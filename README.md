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
- 🔒 **Binary file aware** - Intelligently handles binary files without breaking

## Installation

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

## Configuration

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

## Usage

### Basic Usage
```bash
# Stage your changes
git add .

# Generate commit message
git commitai

# The AI will analyze your changes and open your editor with a suggested message
# Save and exit to commit, or quit without saving to abort
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

The `--amend` feature works just like `git commit --amend` but generates a new AI message based on:
- The changes from the previous commit
- Any newly staged changes
- The previous commit message (for context)
- Any additional context you provide with `-m`

### Workflow Examples

#### Standard Workflow
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
#
# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
#
# On branch main
#
# Changes to be committed:
#   M app.js
#

# Edit if needed, then save to commit or quit to abort
```

#### Amend Workflow
```bash
# You just made a commit but realized you forgot something
git commitai  # Creates commit: "Add user authentication"

# Oops, forgot to handle edge cases
vim auth.js  # Make additional changes
git add auth.js

# Amend with the new changes
git commitai --amend -m "Added edge case handling for expired tokens"

# Your editor opens with a new comprehensive message like:
# Add user authentication with comprehensive error handling
#
# - Implemented JWT-based authentication system
# - Added login and logout endpoints
# - Included token validation middleware
# - Added edge case handling for expired and malformed tokens
# - Implemented proper error responses for auth failures
#
# You are amending the previous commit.
#
# On branch main
#
# Changes to be committed (including previous commit):
#   M auth.js
#   A middleware/auth.js
#   M routes/user.js
#
```

## How It Works

1. **Analyzes staged changes**: Reads `git diff --cached` to understand what changed
2. **Gathers context**: Includes full file contents for better understanding
3. **Calls AI API**: Sends the context to your configured AI model
4. **Opens editor**: Places the generated message in your git editor
5. **Commits or aborts**: Just like regular `git commit` - save to commit, quit to abort

For `--amend`:
1. **Analyzes previous commit**: Includes changes from the last commit
2. **Includes new staged changes**: Combines with any newly staged files
3. **Provides previous message**: Uses the old commit message as context
4. **Generates comprehensive message**: Creates a new message covering all changes

## Tips

- **Better results with context**: Use `-m` flag to explain WHY you made changes
- **Model selection**: GPT-4 or Claude models generally produce better commit messages than GPT-3.5
- **Cost optimization**: For simple changes, smaller models like `gpt-3.5-turbo` work well
- **Amending commits**: Use `--amend` when you need to update the last commit rather than creating a new one
- **Editor shortcuts**: 
  - vim: `:wq` to save and commit, `:q!` to abort
  - nano: `Ctrl+O, Enter, Ctrl+X` to save, `Ctrl+X` to abort
  - VS Code: `Ctrl+S, Ctrl+W` to save, close without saving to abort

## Troubleshooting

### "API key not set" error
Make sure you've exported your API key:
```bash
export GIT_COMMIT_AI_KEY="your-key-here"
```

### "No staged changes" error
Stage your changes first:
```bash
git add .
```

### "Nothing to amend" error
This occurs when trying to use `--amend` on an initial commit (no HEAD exists yet). Make a normal commit first:
```bash
git commitai  # without --amend
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

## Advanced Configuration

### Using with different branches
You can set different models for different projects:
```bash
# In your project directory
git config core.commitai.model "gpt-4o"  # Premium model for important project
# In another project
git config core.commitai.model "gpt-3.5-turbo"  # Cheaper model for personal project
```

Then update the script to check git config:
```bash
MODEL="${GIT_COMMIT_AI_MODEL:-$(git config core.commitai.model || echo 'gpt-4o')}"
```

### Custom System Prompts
You can modify the prompt in the script to match your team's commit message conventions:
```bash
MESSAGE="Generate a conventional commit message (feat/fix/docs/style/refactor/test/chore)..."
```

## Contributing

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
pytest test_git_commitai.py -v --cov=. --cov-report=term-missing

# Run specific test
pytest test_git_commitai.py::TestGitStatus::test_parse_porcelain_modified_files -v

# Generate HTML coverage report
pytest test_git_commitai.py --cov=. --cov-report=html
# Open htmlcov/index.html in your browser
```

#### Code Quality

```bash
# Format code with black
black git-commitai test_git_commitai.py

# Check formatting without changing files
black --check git-commitai test_git_commitai.py

# Run linting
flake8 git-commitai test_git_commitai.py --max-line-length=100

# Type checking (optional)
mypy git-commitai
```

#### Writing Tests

When adding new features or fixing bugs, please include tests:

1. Add test cases to `test_git_commitai.py`
2. Follow the existing test structure
3. Ensure all tests pass before submitting PR
4. Aim for high code coverage (>90%)

Example test structure:
```python
def test_new_feature():
    """Test description of what you're testing."""
    with patch('git_commitai.some_function') as mock_func:
        mock_func.return_value = 'expected'
        result = git_commitai.new_feature()
        assert result == 'expected'
```

#### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Format your code (`black git-commitai test_git_commitai.py`)
7. Commit your changes (you can use `git-commitai` itself!)
8. Push to your fork (`git push origin feature/amazing-feature`)
9. Open a Pull Request

#### CI/CD

All pull requests automatically run:
- Tests on Python 3.8, 3.9, 3.10, 3.11, and 3.12
- Cross-platform tests (Ubuntu, macOS, Windows)
- Code coverage reporting
- Linting and formatting checks

## License

MIT License - feel free to use and modify as needed.

## Credits

Created by [your-name]. Inspired by the need for better commit messages and the power of AI to understand code changes.

---

**Note**: This tool sends your code changes to external AI APIs. Ensure you have permission to share your code with third-party services and that you're not violating any confidentiality agreements.

## 🔒 License
* This project is released under the MIT license as found in the [LICENSE](LICENSE) file.

## ✨ Star History
[![Star History](https://api.star-history.com/svg?repos=semperai/git-commitai&type=Date)](https://star-history.com/#semperai/git-commitai&Date)

## 🤗 Contributors
<a href="https://github.com/semperai/git-commitai/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=semperai/git-commitai" />
</a>
