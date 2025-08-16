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

# Default installation directory
INSTALL_DIR="/usr/local/bin"
MAN_DIR="/usr/local/share/man/man1"
REPO_URL="https://raw.githubusercontent.com/semperai/git-commitai/master"


# Function to print colored output
print_color() {
    local color="$1"
    shift
    # Join remaining args; preserve spaces; add newline
    printf "%b\n" "${color}$*${NC}"
}

# Function to check if running with sudo/root
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ "$1" == "system" ]]; then
        print_color $RED "Error: System-wide installation requires sudo privileges"
        print_color $YELLOW "Run: sudo ./install.sh"
        print_color $YELLOW "Or use: ./install.sh --user for user installation"
        exit 1
    fi
}

# Function to detect OS and adjust paths
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        # macOS might need different man path
        if [[ -d "/usr/local/share/man" ]]; then
            MAN_DIR="/usr/local/share/man/man1"
        elif [[ -d "/opt/local/share/man" ]]; then
            # MacPorts
            MAN_DIR="/opt/local/share/man/man1"
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

# Function to install for current user
install_user() {
    print_color $BLUE "Installing git-commitai for current user..."

    # Create user directories if they don't exist
    USER_BIN="$HOME/.local/bin"
    USER_MAN="$HOME/.local/share/man/man1"

    mkdir -p "$USER_BIN"
    mkdir -p "$USER_MAN"

    # Download and install script
    print_color $YELLOW "Downloading git-commitai..."
    download_file "$REPO_URL/git_commitai.py" "$USER_BIN/git-commitai"
    chmod +x "$USER_BIN/git-commitai"

    # Download and install man page
    print_color $YELLOW "Installing man page..."
    download_file "$REPO_URL/git-commitai.1" "$USER_MAN/git-commitai.1"

    # Set up git alias
    print_color $YELLOW "Setting up git alias..."
    git config --global alias.commitai "!$USER_BIN/git-commitai"

    # Add to PATH if needed
    if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
        print_color $YELLOW "Adding $USER_BIN to PATH..."

        # Detect shell and update appropriate config file
        if [[ -n "$ZSH_VERSION" ]] || [[ -f "$HOME/.zshrc" ]]; then
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.zshrc"
            SHELL_RC="$HOME/.zshrc"
        elif [[ -n "$BASH_VERSION" ]] || [[ -f "$HOME/.bashrc" ]]; then
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
            SHELL_RC="$HOME/.bashrc"
        else
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.profile"
            SHELL_RC="$HOME/.profile"
        fi

        print_color $YELLOW "Added PATH to $SHELL_RC"
    fi

    # Add MANPATH if needed
    if [[ -z "$MANPATH" ]] || [[ ":$MANPATH:" != *":$USER_MAN:"* ]]; then
        if [[ -n "$ZSH_VERSION" ]] || [[ -f "$HOME/.zshrc" ]]; then
            echo "export MANPATH=\"\$HOME/.local/share/man:\$MANPATH\"" >> "$HOME/.zshrc"
        elif [[ -n "$BASH_VERSION" ]] || [[ -f "$HOME/.bashrc" ]]; then
            echo "export MANPATH=\"\$HOME/.local/share/man:\$MANPATH\"" >> "$HOME/.bashrc"
        else
            echo "export MANPATH=\"\$HOME/.local/share/man:\$MANPATH\"" >> "$HOME/.profile"
        fi
    fi

    print_color $GREEN "✓ User installation complete!"
    if [[ -n "${SHELL_RC:-}" ]]; then
        print_color $YELLOW "\nPlease run: source $SHELL_RC"
        print_color $YELLOW "Or restart your terminal for PATH changes to take effect."
    else
        print_color $YELLOW "\nIf you just added PATH/MANPATH in a prior step, run: source ~/.bashrc or ~/.zshrc"
        print_color $YELLOW "Otherwise, restart your terminal."
    fi

}

# Function to install system-wide
install_system() {
    check_permissions "system"

    print_color $BLUE "Installing git-commitai system-wide..."

    # Create directories if they don't exist
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$MAN_DIR"

    # Download and install script
    print_color $YELLOW "Downloading git-commitai..."
    download_file "$REPO_URL/git_commitai.py" "$INSTALL_DIR/git-commitai"
    chmod +x "$INSTALL_DIR/git-commitai"

    # Download and install man page
    print_color $YELLOW "Installing man page..."
    download_file "$REPO_URL/git-commitai.1" "$MAN_DIR/git-commitai.1"

    # Update man database (OS-specific)
    if [[ "$OS" == "linux" ]]; then
        if command -v mandb &> /dev/null; then
            print_color $YELLOW "Updating man database..."
            mandb -q 2>/dev/null || true
        fi
    elif [[ "$OS" == "macos" ]]; then
        if command -v makewhatis &> /dev/null; then
            print_color $YELLOW "Updating man database..."
            makewhatis "$MAN_DIR" 2>/dev/null || true
        fi
    fi

    print_color $GREEN "✓ System installation complete!"
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
        echo "export GIT_COMMIT_AI_MODEL='anthropic/claude-3.5-sonnet'"
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
            DEFAULT_MODEL="anthropic/claude-3.5-sonnet"
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
            DEFAULT_MODEL="llama2"
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
    if [[ -n "$ZSH_VERSION" ]] || [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ -n "$BASH_VERSION" ]] || [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi

    # Write configuration
    {
        echo ""
        echo "# Git Commit AI Configuration"
        echo "export GIT_COMMIT_AI_KEY='$API_KEY'"
        echo "export GIT_COMMIT_AI_URL='$API_URL'"
        echo "export GIT_COMMIT_AI_MODEL='$DEFAULT_MODEL'"
    } >> "$SHELL_RC"

    print_color $GREEN "✓ Configuration saved to $SHELL_RC"
    print_color $YELLOW "Run: source $SHELL_RC"
}

# Function to test installation
test_installation() {
    print_color $BLUE "\nTesting installation..."

    # Test if git-commitai is accessible
    if command -v git-commitai &> /dev/null; then
        print_color $GREEN "✓ git-commitai command found"
    else
        print_color $YELLOW "⚠ git-commitai not in PATH yet (restart terminal)"
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
        print_color $YELLOW "⚠ Man page not accessible yet"
    fi

    # Test API configuration
    if [[ -n "$GIT_COMMIT_AI_KEY" ]]; then
        print_color $GREEN "✓ API key configured"
    else
        print_color $YELLOW "⚠ API key not configured"
    fi
}

# Function to uninstall
uninstall() {
    print_color $BLUE "Uninstalling git-commitai..."

    # Remove system files
    if [[ -f "$INSTALL_DIR/git-commitai" ]]; then
        if [[ $EUID -eq 0 ]]; then
            rm -f "$INSTALL_DIR/git-commitai"
            rm -f "$MAN_DIR/git-commitai.1"
            print_color $GREEN "✓ System files removed"
        else
            print_color $YELLOW "System files require sudo to remove"
        fi
    fi

    # Remove user files
    if [[ -f "$HOME/.local/bin/git-commitai" ]]; then
        rm -f "$HOME/.local/bin/git-commitai"
        rm -f "$HOME/.local/share/man/man1/git-commitai.1"
        print_color $GREEN "✓ User files removed"
    fi

    # Remove git alias
    git config --global --unset alias.commitai 2>/dev/null || true
    print_color $GREEN "✓ Git alias removed"

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
        --user)
            INSTALL_TYPE="user"
            ;;
        --system)
            INSTALL_TYPE="system"
            ;;
        --uninstall)
            uninstall
            exit 0
            ;;
        --help|-h)
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --user      Install for current user only (default)"
            echo "  --system    Install system-wide (requires sudo)"
            echo "  --uninstall Remove git-commitai"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            INSTALL_TYPE="user"
            ;;
    esac

    # Check prerequisites
    detect_os
    check_prerequisites

    # Run installation
    if [[ "$INSTALL_TYPE" == "system" ]]; then
        install_system
    else
        install_user
    fi

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
    echo
    print_color $BLUE "For more information: https://github.com/semperai/git-commitai"
}

# Run main function
main "$@"
