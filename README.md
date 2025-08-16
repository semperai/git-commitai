# Git Commit AI

An intelligent git commit message generator that uses AI to analyze your staged changes and generate meaningful commit messages, following conventional commit standards.

## Features

- 🤖 **AI-powered commit message generation** - Analyzes your code changes and generates descriptive commit messages
- 📝 **Works like native `git commit`** - Same workflow: save to commit, quit to abort
- 🔧 **Provider agnostic** - Works with OpenAI, OpenRouter, Anthropic, local LLMs, or any OpenAI-compatible API
- ✏️ **Full editor integration** - Uses your configured git editor for message editing
- 📊 **Context aware** - Includes both the diff and full file contents for better understanding
- 💬 **Additional context support** - Optional `-m` flag for providing extra context about your changes

## Installation

### Quick Install

1. Download the script:
```bash
curl -O https://raw.githubusercontent.com/kasumi-1/git-commit-ai/master/git-commitai
chmod +x git-commitai
```

2. Install as a git command (choose one method):

#### Method 1: Git Alias (Simplest)
```bash
git config --global alias.commitai '!'"$(pwd)/git-commitai"
```
Now you can use: `git commitai`

#### Method 2: Add to PATH
```bash
# Move to a directory in your PATH
sudo mv git-commitai /usr/local/bin/
# Or add to your personal bin
mkdir -p ~/bin
mv git-commitai ~/bin/
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc
```
Now you can use: `git commitai` or just `git-commitai`

#### Method 3: Custom Git Command
```bash
# Git automatically recognizes git-* commands in PATH
sudo mv git-commitai /usr/local/bin/git-commitai
```
Now you can use: `git commitai`

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

### Workflow Example
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
# On branch master
#
# Changes to be committed:
#   M app.js
#

# Edit if needed, then save to commit or quit to abort
```

## How It Works

1. **Analyzes staged changes**: Reads `git diff --cached` to understand what changed
2. **Gathers context**: Includes full file contents for better understanding
3. **Calls AI API**: Sends the context to your configured AI model
4. **Opens editor**: Places the generated message in your git editor
5. **Commits or aborts**: Just like regular `git commit` - save to commit, quit to abort

## Tips

- **Better results with context**: Use `-m` flag to explain WHY you made changes
- **Model selection**: GPT-4 or Claude models generally produce better commit messages than GPT-3.5
- **Cost optimization**: For simple changes, smaller models like `gpt-3.5-turbo` work well
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

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use and modify as needed.

## Credits

Created by kasumi-1
