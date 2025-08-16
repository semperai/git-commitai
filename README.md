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
    <a href="#quick-install">Quick Install</a>
    ·
    <a href="#usage">Usage</a>
    ·
    <a href="#documentation">Documentation</a>
    ·
    <a href="https://github.com/semperai/git-commitai/issues">Report Bug</a>
  </p>
  <br />

  <!-- Badges -->
  <p>
    <a href="https://github.com/semperai/git-commitai/stargazers">
      <img src="https://img.shields.io/github/stars/semperai/git-commitai?style=flat" alt="Stars" />
    </a>
    <a href="https://github.com/semperai/git-commitai/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/semperai/git-commitai/test.yml?style=flat&label=Tests" alt="Tests" />
    </a>
    <a href="https://github.com/semperai/git-commitai/releases">
      <img src="https://img.shields.io/github/v/release/semperai/git-commitai?style=flat" alt="Release" />
    </a>
    <a href="https://github.com/semperai/git-commitai/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/semperai/git-commitai?style=flat" alt="License" />
    </a>
    <a href="https://github.com/semperai/git-commitai">
      <img src="https://img.shields.io/badge/python-3.8+-blue?style=flat" alt="Python" />
    </a>
  </p>
</div>

---

**Git Commit AI** analyzes your staged changes and generates meaningful, conventional commit messages using AI. Works seamlessly with your existing git workflow - just use `git commitai` instead of `git commit`.

## 🚀 Quick Install

### Linux/macOS/WSL

Run this single command to install and set up everything:

```bash
curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | bash
```

### Windows

Run in PowerShell:

```powershell
# Download and run the installer
irm https://raw.githubusercontent.com/semperai/git-commitai/master/install.ps1 | iex

# Or download first, then run
Invoke-WebRequest -Uri https://raw.githubusercontent.com/semperai/git-commitai/master/install.ps1 -OutFile install.ps1
.\install.ps1
```

The installer will:
- ✅ Download and install git-commitai
- ✅ Set up the `git commitai` command
- ✅ Install the man page for `git commitai --help` (Unix/Linux)
- ✅ Guide you through API configuration
- ✅ Add to your PATH automatically

### Manual Installation Options

<details>
<summary>Install for current user only</summary>

```bash
curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | bash -s -- --user
```
</details>

<details>
<summary>System-wide installation (requires sudo)</summary>

```bash
curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | sudo bash -s -- --system
```
</details>

<details>
<summary>Uninstall</summary>

```bash
curl -sSL https://raw.githubusercontent.com/semperai/git-commitai/master/install.sh | bash -s -- --uninstall
```
</details>

## ⚙️ Configuration

After installation, the script will guide you through setting up your API credentials. You can also configure manually:

```bash
# Example with OpenRouter (recommended)
export GIT_COMMIT_AI_KEY="sk-or-v1-..."
export GIT_COMMIT_AI_URL="https://openrouter.ai/api/v1/chat/completions"
export GIT_COMMIT_AI_MODEL="qwen/qwen3-coder"
```

Add these to your `~/.bashrc` or `~/.zshrc` to make them permanent.

You can also override these settings per-command using CLI flags:

```bash
# Use a different model for a specific commit
git commitai --model "gpt-4o" --api-key "sk-..."

# Test with a local LLM
git commitai --api-url "http://localhost:11434/v1/chat/completions" --model "llama2"
```

### Commit Message Templates (.gitmessage)

Git Commit AI automatically reads and uses your `.gitmessage` template files to understand your project's commit conventions. This helps generate messages that match your team's style guide.

The tool looks for templates in this order (first found wins):
1. **Git config template**: Set via `git config commit.template`
2. **Repository template**: `.gitmessage` in your repository root
3. **Global template**: `~/.gitmessage` in your home directory

#### Setting Up a Template

Create a `.gitmessage` file with your project's commit guidelines:

```bash
# Create a repository-specific template
cat > .gitmessage << 'EOF'
# Format: <type>(<scope>): <subject>
#
# <type> must be one of:
#   feat: A new feature
#   fix: A bug fix
#   docs: Documentation changes
#   style: Code style changes (formatting, semicolons, etc)
#   refactor: Code refactoring without adding features or fixing bugs
#   test: Adding or updating tests
#   chore: Maintenance tasks, dependency updates, etc
#
# <scope> is optional and indicates the module affected
#
# Example: feat(auth): Add OAuth2 login support
#
# The body should explain the motivation for the change
EOF

# Or set a global template
git config --global commit.template ~/.gitmessage

# Or set a repository-specific template
git config commit.template .github/commit-template
```

When a template is found, Git Commit AI uses it as additional context to generate messages that follow your conventions while still adhering to Git best practices.

## 📖 Usage

```bash
# Basic usage - just like git commit!
git add .
git commitai

# With context for better messages
git commitai -m "Refactored auth system for JWT"

# Auto-stage tracked files
git commitai -a

# Override API settings for this commit
git commitai --model "claude-3.5-sonnet" --api-key "sk-ant-..."

# Debug mode for troubleshooting
git commitai --debug

# See all options
git commitai --help
```

## 📚 Documentation

### Get Help
```bash
man git-commitai
```

### Git Commit AI Specific Commands

These commands are unique to `git commitai` and not found in standard `git commit`:

| Flag | Description | Purpose |
|------|-------------|---------|
| `-m, --message <context>` | Provide context for AI | **Modified behavior**: Unlike `git commit` where this sets the entire message, in `git commitai` this provides context to help the AI understand your intent |
| `--debug` | Enable debug logging | Outputs debug information to stderr for troubleshooting. Shows git commands, API requests, and decision points |
| `--api-key <key>` | Override API key | Temporarily use a different API key for this commit only. Overrides `GIT_COMMIT_AI_KEY` environment variable |
| `--api-url <url>` | Override API endpoint | Use a different API endpoint for this commit. Useful for testing different providers or local models |
| `--model <name>` | Override model name | Use a different AI model for this commit. Overrides `GIT_COMMIT_AI_MODEL` environment variable |

### Standard Git Commit Commands Support

The following table shows all standard `git commit` flags and their support status in `git commitai`:

| Flag | Description | Status |
|------|-------------|--------|
| `-a, --all` | Auto-stage all tracked modified files | ✅ **Supported** |
| `--interactive` | Interactively add files | ❌ Not supported |
| `--patch` | Interactively add hunks of patch | ❌ Not supported |
| `-s, --signoff` | Add Signed-off-by trailer | ❌ Not supported |
| `-v, --verbose` | Show diff in commit message editor | ✅ **Supported** |
| `-u<mode>, --untracked-files[=<mode>]` | Show untracked files | ❌ Not supported |
| `--amend` | Amend the previous commit | ✅ **Supported** |
| `--dry-run` | Don't actually commit, just show what would be committed | ❌ Not supported |
| `-c, --reedit-message=<commit>` | Reuse and edit message from specified commit | ❌ Not supported |
| `-C, --reuse-message=<commit>` | Reuse message from specified commit | ❌ Not supported |
| `--squash=<commit>` | Construct commit for squashing | ❌ Not supported |
| `--fixup=<commit>` | Construct commit for autosquash rebase | ❌ Not supported |
| `-F, --file=<file>` | Read commit message from file | ❌ Not supported |
| `--reset-author` | Reset author information | ❌ Not supported |
| `--allow-empty` | Allow empty commits | ✅ **Supported** |
| `--allow-empty-message` | Allow commits with empty message | ❌ Not supported |
| `--no-verify, -n` | Skip pre-commit and commit-msg hooks | ✅ **Supported** |
| `-e, --edit` | Force edit of commit message | ❌ Not supported |
| `--author=<author>` | Override author information | ❌ Not supported |
| `--date=<date>` | Override author date | ❌ Not supported |
| `--cleanup=<mode>` | Set commit message cleanup mode | ❌ Not supported |
| `--status` | Include git status in commit editor | ❌ Not supported |
| `--no-status` | Don't include git status in commit editor | ❌ Not supported |
| `-i, --include` | Stage specified files in addition to staged | ❌ Not supported |
| `-o, --only` | Commit only specified files | ❌ Not supported |
| `--pathspec-from-file=<file>` | Read pathspec from file | ❌ Not supported |
| `--pathspec-file-nul` | NUL-separated pathspec file | ❌ Not supported |
| `--trailer <token>[(=\|:)<value>]` | Add trailers to commit message | ❌ Not supported |
| `-S[<keyid>], --gpg-sign[=<keyid>]` | GPG-sign commit | ❌ Not supported |
| `--no-gpg-sign` | Don't GPG-sign commit | ❌ Not supported |
| `--` | Separate paths from options | ❌ Not supported |
| `<pathspec>...` | Commit only specified paths | ❌ Not supported |

#### Legend
- ✅ **Supported** - Fully functional in git-commitai
- ❌ Not supported - Not yet implemented

### Supported Providers

- **OpenRouter** (Recommended) - Access to Claude, GPT-4, and many models
- **Local LLMs** (Recommended) - Ollama, LM Studio
- **OpenAI** - GPT-4, GPT-3.5
- **Anthropic** - Claude models
- **Any OpenAI-compatible API**

## ✨ Features

- 🤖 **AI-powered commit messages** - Analyzes your code changes and generates descriptive messages
- 📝 **Drop-in replacement** - Use `git commitai` just like `git commit` with the same flags
- 🔧 **Provider agnostic** - Works with OpenAI, Anthropic, local LLMs, or any compatible API
- 📖 **Full documentation** - Comprehensive man page with `git commitai --help`
- ⚡ **Smart context** - Understands both diffs and full file contents
- 🎯 **Git native** - Respects your git editor, hooks, and workflow
- 🐛 **Debug mode** - Built-in debugging for troubleshooting issues
- 🔄 **CLI overrides** - Override API settings per-command for testing and flexibility
- 📋 **Template support** - Automatically uses your `.gitmessage` templates for project-specific conventions

## 🧪 Examples

```bash
# Stage changes and generate commit message
git add src/
git commitai

# Quick fix with auto-staging
vim buggy-file.js
git commitai -a -m "Fixed null pointer exception"

# Work in progress (skip hooks)
git commitai -a -n -m "WIP: implementing feature"

# Amend last commit with better message
git commitai --amend

# Trigger CI/CD with empty commit
git commitai --allow-empty -m "Trigger deployment"

# Review changes while committing
git commitai -v

# Test with a different model
git commitai --model "gpt-4o" --api-key "sk-..."

# Use local LLM for sensitive code
git commitai --api-url "http://localhost:11434/v1/chat/completions" --model "codellama"

# Debug mode for troubleshooting (outputs to stderr)
git commitai --debug 2> debug.log
git commitai --debug -a -m "Testing auto-stage" 2>&1 | tee debug.log

# Combine CLI overrides with debug
git commitai --debug --model "claude-3.5-sonnet" --api-key "sk-ant-..."
```

### Using with .gitmessage Templates

```bash
# Create a project-specific template
cat > .gitmessage << 'EOF'
# Type: feat|fix|docs|style|refactor|test|chore
# Scope: (optional) affected module
#
# Remember: Use imperative mood in the subject line
EOF

# Git Commit AI will automatically detect and use this template
git add .
git commitai

# The AI will generate messages following your template format
# Example output: "feat(auth): Add JWT token validation"
```

## 🐛 Debugging

If you encounter issues, use the `--debug` flag to enable detailed logging to stderr:

```bash
# Enable debug mode (outputs to stderr)
git commitai --debug

# Capture debug output to a file
git commitai --debug 2> debug.log

# View debug output on screen and save to file
git commitai --debug 2>&1 | tee debug.log

# Debug with other flags
git commitai --debug -a -v 2> debug.log

# Debug with API overrides
git commitai --debug --model "gpt-4" --api-url "https://api.openai.com/v1/chat/completions" 2> debug.log
```

The debug output includes:
- All git commands executed
- API request/response details
- File processing information
- Configuration and environment details (including CLI overrides)
- Template file detection and loading
- Error messages and stack traces

When reporting bugs, please include relevant portions of the debug output.

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/semperai/git-commitai.git
cd git-commitai
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
pytest
./install.sh --user
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🌟 Star History

[![Star History](https://api.star-history.com/svg?repos=semperai/git-commitai&type=Date)](https://star-history.com/#semperai/git-commitai&Date)
