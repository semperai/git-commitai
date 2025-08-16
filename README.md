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
git commitai --help
```

## 📚 Documentation

### Get Help
```bash
man git-commitai
```

### Git Commit Commands Support

The following table shows all `git commit` flags and their current support status in `git commitai`:

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
| `-m, --message=<msg>` | Provide context message for AI | ✅ **Supported** (modified behavior) |
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

#### Note on `-m` flag
In standard `git commit`, the `-m` flag provides the entire commit message. In `git commitai`, this flag provides context to the AI to help generate a better commit message based on your changes.

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
