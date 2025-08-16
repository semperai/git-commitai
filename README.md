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
export GIT_COMMIT_AI_MODEL="anthropic/claude-3.5-sonnet"
```

Add these to your `~/.bashrc` or `~/.zshrc` to make them permanent.

## 📖 Usage

```bash
# Basic usage - just like git commit!
git add .
git commitai

# With context for better messages
git commitai -m "Refactored auth system for JWT"

# Auto-stage tracked files
git commitai -a

# See all options
git commitai --help  # Opens the man page
```

## 📚 Documentation

### Get Help
```bash
# View the full manual
man git-commitai

# Quick help
git commitai --help
```

### Common Commands

| Command | Description |
|---------|-------------|
| `git commitai` | Generate commit message for staged changes |
| `git commitai -a` | Auto-stage tracked files and commit |
| `git commitai -m "context"` | Add context for better AI messages |
| `git commitai -v` | Show diff in editor while writing message |
| `git commitai --amend` | Amend the previous commit |
| `git commitai -n` | Skip git hooks |
| `git commitai --allow-empty` | Create empty commit (for CI triggers) |

### Supported Providers

- **OpenRouter** (Recommended) - Access to Claude, GPT-4, and many models
- **OpenAI** - GPT-4, GPT-3.5
- **Anthropic** - Claude models
- **Local LLMs** - Ollama, LM Studio
- **Any OpenAI-compatible API**

## ✨ Features

- 🤖 **AI-powered commit messages** - Analyzes your code changes and generates descriptive messages
- 📝 **Drop-in replacement** - Use `git commitai` just like `git commit` with the same flags
- 🔧 **Provider agnostic** - Works with OpenAI, Anthropic, local LLMs, or any compatible API
- 📖 **Full documentation** - Comprehensive man page with `git commitai --help`
- ⚡ **Smart context** - Understands both diffs and full file contents
- 🎯 **Git native** - Respects your git editor, hooks, and workflow

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
```

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Clone the repository
git clone https://github.com/semperai/git-commitai.git
cd git-commitai

# Run tests
make test

# Install locally for development
./install.sh --user
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🌟 Star History

[![Star History](https://api.star-history.com/svg?repos=semperai/git-commitai&type=Date)](https://star-history.com/#semperai/git-commitai&Date)
