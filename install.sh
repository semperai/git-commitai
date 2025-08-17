#!/usr/bin/env bash

# Git Commit AI Installation Script
# https://github.com/semperai/git-commitai

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# System installation directories
INSTALL_DIR="/usr/local/bin"
MAN_DIR="/usr/local/share/man/man1"
REPO_URL="https://raw.githubusercontent.com/semperai/git-commitai/master"

# Function to print colored output
print_color() {
    local color="$1"
    shift
    printf "%b\n" "${color}$*${NC}"
}

# Function to detect OS and adjust paths
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        # macOS paths - prefer Homebrew if available
        if command -v brew &> /dev/null; then
            MAN_DIR="$(brew --prefix)/share/man/man1"
        else
            MAN_DIR="/usr/local/share/man/man1"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        print_color $YELLOW "⚠️  Windows detected. Consider using WSL (Windows Subsystem for Linux) for best compatibility."
        print_color $YELLOW "   Or install Git Bash: https://git-scm.com/download/win"
        echo ""
    else
        OS="unknown"
    fi

    # Debug output if needed
    if [[ "${DEBUG:-}" == "1" ]]; then
        echo "Detected OS: $OS"
        echo "OSTYPE: $OSTYPE"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    local missing=()

    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    # Check for git
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi

    # Check for curl or wget
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        missing+=("curl or wget")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        print_color $RED "Error: Missing required dependencies:"
        for dep in "${missing[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
}

# Function to download file
download_file() {
    local url=$1
    local output=$2

    if command -v curl &> /dev/null; then
        curl -fsSL "$url" -o "$output"
    elif command -v wget &> /dev/null; then
        wget -q "$url" -O "$output"
    else
        print_color $RED "Error: Neither curl nor wget found"
        exit 1
    fi
}

# Function to check if directory is writable
is_writable() {
    local dir=$1
    # Check if directory exists and is writable
    if [[ -d "$dir" ]] && [[ -w "$dir" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to create directory with or without sudo
create_directory() {
    local dir=$1

    if [[ -d "$dir" ]]; then
        return 0
    fi

    # Try to create parent directory first to check if we need sudo
    local parent_dir
    parent_dir=$(dirname "$dir")

    if is_writable "$parent_dir"; then
        print_color $YELLOW "Creating $dir..."
        mkdir -p "$dir"
    else
        print_color $YELLOW "Creating $dir (requires sudo)..."
        sudo mkdir -p "$dir"
    fi
}

# Function to copy file with or without sudo
copy_file() {
    local source=$1
    local dest_dir=$2
    local dest_file=$3

    if is_writable "$dest_dir"; then
        cp "$source" "$dest_dir/$dest_file"
        if [[ -x "$source" ]]; then
            chmod +x "$dest_dir/$dest_file"
        fi
    else
        print_color $YELLOW "Installing to $dest_dir (requires sudo)..."
        sudo cp "$source" "$dest_dir/$dest_file"
        if [[ -x "$source" ]]; then
            sudo chmod +x "$dest_dir/$dest_file"
        fi
    fi
}

# Function to remove file with or without sudo
remove_file() {
    local file=$1

    if [[ ! -f "$file" ]]; then
        return 0
    fi

    local dir
    dir=$(dirname "$file")

    if is_writable "$dir"; then
        rm -f "$file"
    else
        print_color $YELLOW "Removing $file (requires sudo)..."
        sudo rm -f "$file"
    fi
}

# Function to install system-wide
install_system() {
    print_color $BLUE "Installing git-commitai..."

    # Create temp directory for downloads
    local temp_dir=$(mktemp -d)
    trap "rm -rf $temp_dir" EXIT

    # Download script to temp directory first
    print_color $YELLOW "Downloading git-commitai..."
    download_file "$REPO_URL/git_commitai.py" "$temp_dir/git-commitai"
    chmod +x "$temp_dir/git-commitai"

    # Download man page to temp directory
    print_color $YELLOW "Downloading man page..."
    download_file "$REPO_URL/git-commitai.1" "$temp_dir/git-commitai.1"

    # Create directories if they don't exist
    create_directory "$INSTALL_DIR"
    create_directory "$MAN_DIR"

    # Copy files to system directories
    print_color $YELLOW "Installing git-commitai to $INSTALL_DIR..."
    copy_file "$temp_dir/git-commitai" "$INSTALL_DIR" "git-commitai"

    print_color $YELLOW "Installing man page to $MAN_DIR..."
    copy_file "$temp_dir/git-commitai.1" "$MAN_DIR" "git-commitai.1"

    # Update man database (OS-specific)
    if [[ "$OS" == "linux" ]]; then
        if command -v mandb &> /dev/null; then
            print_color $YELLOW "Updating man database..."
            if is_writable "/var/cache/man" || is_writable "/usr/share/man"; then
                mandb -q 2>/dev/null || true
            else
                sudo mandb -q 2>/dev/null || true
            fi
        fi
    elif [[ "$OS" == "macos" ]]; then
        # macOS typically doesn't need manual man database updates for /usr/local/share/man
        # But if makewhatis exists, we can run it
        if command -v makewhatis &> /dev/null; then
            print_color $YELLOW "Updating man database..."
            if is_writable "$MAN_DIR"; then
                makewhatis "$MAN_DIR" 2>/dev/null || true
            else
                sudo makewhatis "$MAN_DIR" 2>/dev/null || true
            fi
        fi
    fi

    print_color $GREEN "✓ Installation complete!"
}

# Function to configure git alias for the current user
configure_git_alias() {
    print_color $BLUE "\nConfiguring git alias..."

    # Set up git alias for current user
    git config --global alias.commitai "!$INSTALL_DIR/git-commitai"
    print_color $GREEN "✓ Git alias configured for user: $USER"
}

# Function to configure environment
configure_environment() {
    print_color $BLUE "\nConfiguring environment variables..."

    # Check if variables are already set
    if [[ -n "$GIT_COMMIT_AI_KEY" ]]; then
        print_color $GREEN "✓ GIT_COMMIT_AI_KEY is already set"
    else
        print_color $YELLOW "You need to set up your API credentials:"
        print_color $NC "Add these to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
        echo ""
        echo "# Git Commit AI Configuration"
        echo "export GIT_COMMIT_AI_KEY='your-api-key-here'"
        echo "export GIT_COMMIT_AI_URL='https://openrouter.ai/api/v1/chat/completions'"
        echo "export GIT_COMMIT_AI_MODEL='qwen/qwen3-coder'"
        echo ""

        read -p "Would you like to set up API credentials now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            setup_api_credentials
        fi
    fi
}

# Function to set up API credentials
setup_api_credentials() {
    print_color $BLUE "\nSelect your AI provider:"
    echo "1) OpenRouter (Recommended - Access to many models)"
    echo "2) OpenAI"
    echo "3) Anthropic Claude"
    echo "4) Local LLM (Ollama)"
    echo "5) Custom/Other"

    read -p "Enter choice [1-5]: " provider_choice

    case $provider_choice in
        1)
            API_URL="https://openrouter.ai/api/v1/chat/completions"
            DEFAULT_MODEL="qwen/qwen3-coder"
            print_color $YELLOW "Get your API key from: https://openrouter.ai/keys"
            ;;
        2)
            API_URL="https://api.openai.com/v1/chat/completions"
            DEFAULT_MODEL="gpt-4o"
            print_color $YELLOW "Get your API key from: https://platform.openai.com/api-keys"
            ;;
        3)
            API_URL="https://api.anthropic.com/v1/messages"
            DEFAULT_MODEL="claude-3-opus-20240229"
            print_color $YELLOW "Get your API key from: https://console.anthropic.com/settings/keys"
            ;;
        4)
            API_URL="http://localhost:11434/v1/chat/completions"
            DEFAULT_MODEL="qwen2.5-coder:7b"
            API_KEY="not-needed"
            print_color $YELLOW "Make sure Ollama is running locally"
            ;;
        5)
            read -p "Enter API URL: " API_URL
            read -p "Enter model name: " DEFAULT_MODEL
            ;;
        *)
            print_color $RED "Invalid choice"
            return
            ;;
    esac

    if [[ -z "$API_KEY" ]]; then
        read -p "Enter your API key: " API_KEY
    fi

    # Detect shell config file
    local shell_rc
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_rc="$HOME/.bashrc"
    else
        shell_rc="$HOME/.profile"
    fi

    # Write configuration
    {
        echo ""
        echo "# Git Commit AI Configuration"
        echo "export GIT_COMMIT_AI_KEY='$API_KEY'"
        echo "export GIT_COMMIT_AI_URL='$API_URL'"
        echo "export GIT_COMMIT_AI_MODEL='$DEFAULT_MODEL'"
    } >> "$shell_rc"

    print_color $GREEN "✓ Configuration saved to $shell_rc"
    print_color $YELLOW "Run: source $shell_rc"
}

# Function to test installation
test_installation() {
    print_color $BLUE "\nTesting installation..."

    # Test if git-commitai is accessible
    if command -v git-commitai &> /dev/null; then
        print_color $GREEN "✓ git-commitai command found in PATH"
    else
        print_color $RED "✗ git-commitai not found in PATH"
    fi

    # Test git alias
    if git config --get alias.commitai &> /dev/null; then
        print_color $GREEN "✓ git commitai alias configured"
    else
        print_color $YELLOW "⚠ git commitai alias not set"
    fi

    # Test man page
    if man git-commitai &> /dev/null 2>&1; then
        print_color $GREEN "✓ Man page accessible"
    else
        print_color $YELLOW "⚠ Man page not accessible (may need to restart terminal)"
    fi

    # Test API configuration
    if [[ -n "$GIT_COMMIT_AI_KEY" ]]; then
        print_color $GREEN "✓ API key configured in current session"
    else
        print_color $YELLOW "⚠ API key not configured in current session (check your shell config)"
    fi

    # Show permission status
    echo ""
    print_color $BLUE "Installation permissions:"
    if is_writable "$INSTALL_DIR"; then
        print_color $GREEN "  • $INSTALL_DIR is writable by user (no sudo needed)"
    else
        print_color $YELLOW "  • $INSTALL_DIR requires sudo for modifications"
    fi

    if is_writable "$MAN_DIR"; then
        print_color $GREEN "  • $MAN_DIR is writable by user (no sudo needed)"
    else
        print_color $YELLOW "  • $MAN_DIR requires sudo for modifications"
    fi
}

# Function to uninstall
uninstall() {
    print_color $BLUE "Uninstalling git-commitai..."

    # Confirm uninstall
    print_color $YELLOW "This will remove:"
    echo "  • $INSTALL_DIR/git-commitai (if it exists)"
    echo "  • $MAN_DIR/git-commitai.1 (if it exists)"
    echo "  • git alias 'commitai'"
    echo ""
    read -p "Continue with uninstall? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_color $YELLOW "Uninstall cancelled"
        exit 0
    fi

    # Remove system files with verification
    remove_file "$INSTALL_DIR/git-commitai"
    remove_file "$MAN_DIR/git-commitai.1"

    # Remove git alias (doesn't require sudo)
    git config --global --unset alias.commitai 2>/dev/null && \
        print_color $GREEN "✓ Git alias removed" || \
        print_color $YELLOW "No git alias 'commitai' found"

    # Update man database
    if [[ "$OS" == "linux" ]] && command -v mandb &> /dev/null; then
        if is_writable "/var/cache/man" || is_writable "/usr/share/man"; then
            mandb -q 2>/dev/null || true
        else
            sudo mandb -q 2>/dev/null || true
        fi
    fi

    print_color $GREEN "✓ Uninstallation complete!"
    print_color $YELLOW "Note: Environment variables in shell config files were not removed"
}

# Main installation flow
main() {
    print_color $BLUE "╔════════════════════════════════════╗"
    print_color $BLUE "║     Git Commit AI Installer       ║"
    print_color $BLUE "╚════════════════════════════════════╝"
    echo

    # Parse arguments
    case "${1:-}" in
        --uninstall)
            detect_os  # Need to detect OS first to set paths
            uninstall
            exit 0
            ;;
        --help|-h)
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --uninstall Remove git-commitai"
            echo "  --help      Show this help message"
            echo ""
            echo "The installer will automatically detect if sudo is needed for system directories."
            echo "On systems with Homebrew or similar, /usr/local may be user-writable."
            exit 0
            ;;
    esac

    # Check prerequisites
    detect_os
    check_prerequisites

    # Run installation
    install_system

    # Configure git alias for the current user
    configure_git_alias

    # Configure environment
    configure_environment

    # Test installation
    test_installation

    print_color $GREEN "\n╔════════════════════════════════════╗"
    print_color $GREEN "║    Installation Complete! 🎉       ║"
    print_color $GREEN "╚════════════════════════════════════╝"
    echo
    print_color $NC "Quick start:"
    print_color $NC "  1. Restart your terminal or run: source ~/.bashrc"
    print_color $NC "  2. Stage some changes: git add ."
    print_color $NC "  3. Generate commit: git commitai"
    print_color $NC "  4. View help: git commitai --help"
    print_color $NC "  5. View man page: man git-commitai"
    echo
    print_color $BLUE "For more information: https://github.com/semperai/git-commitai"
}

# Run main function
main "$@"
