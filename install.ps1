# Git Commit AI Installation Script for Windows
# Run in PowerShell as Administrator for system-wide installation
# Or run as regular user for user installation

param(
    [switch]$System,
    [switch]$Uninstall,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Color {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

# Show help
if ($Help) {
    Write-Color "Git Commit AI Installer for Windows" "Cyan"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -System     Install system-wide (requires Administrator)"
    Write-Host "  -Uninstall  Remove git-commitai"
    Write-Host "  -Help       Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.ps1                # Install for current user"
    Write-Host "  .\install.ps1 -System        # Install system-wide"
    Write-Host "  .\install.ps1 -Uninstall     # Remove installation"
    exit 0
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check prerequisites
function Test-Prerequisites {
    $missing = @()

    # Check for Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -notmatch "Python 3\.[8-9]|Python 3\.1[0-2]") {
            $missing += "Python 3.8 or higher"
        }
    } catch {
        $missing += "Python 3.8 or higher"
    }

    # Check for Git
    try {
        git --version | Out-Null
    } catch {
        $missing += "Git"
    }

    if ($missing.Count -gt 0) {
        Write-Color "Error: Missing required dependencies:" "Red"
        foreach ($dep in $missing) {
            Write-Host "  - $dep"
        }
        Write-Host ""
        Write-Color "Please install:" "Yellow"
        Write-Host "  Python: https://www.python.org/downloads/"
        Write-Host "  Git: https://git-scm.com/download/win"
        exit 1
    }
}

# Download file
function Download-File {
    param(
        [string]$Url,
        [string]$Output
    )

    try {
        Invoke-WebRequest -Uri $Url -OutFile $Output -UseBasicParsing
    } catch {
        Write-Color "Error: Failed to download from $Url" "Red"
        Write-Host $_.Exception.Message
        exit 1
    }
}

# Install for user
function Install-User {
    Write-Color "Installing git-commitai for current user..." "Blue"

    # Create directories
    $userBin = "$env:LOCALAPPDATA\Programs\git-commitai"
    $scriptsDir = "$env:APPDATA\Python\Scripts"

    if (-not (Test-Path $userBin)) {
        New-Item -ItemType Directory -Path $userBin -Force | Out-Null
    }
    if (-not (Test-Path $scriptsDir)) {
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }

    # Download Python script
    Write-Color "Downloading git-commitai..." "Yellow"
    $scriptUrl = "https://raw.githubusercontent.com/semperai/git-commitai/master/git_commitai.py"
    $scriptPath = "$userBin\git_commitai.py"
    Download-File -Url $scriptUrl -Output $scriptPath

    # Create batch wrapper for command line
    $batchContent = @"
@echo off
python "$scriptPath" %*
"@
    $batchPath = "$scriptsDir\git-commitai.cmd"
    Set-Content -Path $batchPath -Value $batchContent

    # Create PowerShell wrapper
    $ps1Content = @"
#!/usr/bin/env pwsh
python "$scriptPath" `$args
"@
    $ps1Path = "$scriptsDir\git-commitai.ps1"
    Set-Content -Path $ps1Path -Value $ps1Content

    # Set up git alias
    Write-Color "Setting up git alias..." "Yellow"
    git config --global alias.commitai "!python `"$scriptPath`""

    # Add to PATH if needed
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$scriptsDir*") {
        Write-Color "Adding to user PATH..." "Yellow"
        $newPath = "$currentPath;$scriptsDir"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$scriptsDir"
        Write-Color "Added $scriptsDir to PATH" "Green"
        Write-Color "Please restart your terminal for PATH changes to take effect" "Yellow"
    }

    Write-Color "✓ User installation complete!" "Green"
}

# Install system-wide
function Install-System {
    if (-not (Test-Administrator)) {
        Write-Color "Error: System-wide installation requires Administrator privileges" "Red"
        Write-Color "Please run PowerShell as Administrator and try again" "Yellow"
        exit 1
    }

    Write-Color "Installing git-commitai system-wide..." "Blue"

    # Create directories
    $systemBin = "$env:ProgramFiles\git-commitai"

    if (-not (Test-Path $systemBin)) {
        New-Item -ItemType Directory -Path $systemBin -Force | Out-Null
    }

    # Download Python script
    Write-Color "Downloading git-commitai..." "Yellow"
    $scriptUrl = "https://raw.githubusercontent.com/semperai/git-commitai/master/git_commitai.py"
    $scriptPath = "$systemBin\git_commitai.py"
    Download-File -Url $scriptUrl -Output $scriptPath

    # Create batch wrapper
    $batchContent = @"
@echo off
python "$scriptPath" %*
"@
    $batchPath = "$systemBin\git-commitai.cmd"
    Set-Content -Path $batchPath -Value $batchContent

    # Set up git alias (global)
    Write-Color "Setting up git alias..." "Yellow"
    git config --system alias.commitai "!python `"$scriptPath`"" 2>$null

    # Add to system PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$systemBin*") {
        Write-Color "Adding to system PATH..." "Yellow"
        $newPath = "$currentPath;$systemBin"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        $env:Path = "$env:Path;$systemBin"
        Write-Color "Added $systemBin to PATH" "Green"
    }

    Write-Color "✓ System installation complete!" "Green"
}

# Configure environment
function Set-Environment {
    Write-Color "`nConfiguring environment variables..." "Blue"

    # Check if already configured
    if ($env:GIT_COMMIT_AI_KEY) {
        Write-Color "✓ GIT_COMMIT_AI_KEY is already set" "Green"
        return
    }

    Write-Color "You need to set up your API credentials:" "Yellow"
    Write-Host ""
    Write-Host "Select your AI provider:"
    Write-Host "1) OpenRouter (Recommended - Access to many models)"
    Write-Host "2) OpenAI"
    Write-Host "3) Anthropic Claude"
    Write-Host "4) Local LLM (Ollama)"
    Write-Host "5) Skip configuration"

    $choice = Read-Host "Enter choice [1-5]"

    switch ($choice) {
        "1" {
            $apiUrl = "https://openrouter.ai/api/v1/chat/completions"
            $model = "anthropic/claude-3.5-sonnet"
            Write-Color "Get your API key from: https://openrouter.ai/keys" "Yellow"
            $apiKey = Read-Host "Enter your API key"
        }
        "2" {
            $apiUrl = "https://api.openai.com/v1/chat/completions"
            $model = "gpt-4o"
            Write-Color "Get your API key from: https://platform.openai.com/api-keys" "Yellow"
            $apiKey = Read-Host "Enter your API key"
        }
        "3" {
            $apiUrl = "https://api.anthropic.com/v1/messages"
            $model = "claude-3-opus-20240229"
            Write-Color "Get your API key from: https://console.anthropic.com/settings/keys" "Yellow"
            $apiKey = Read-Host "Enter your API key"
        }
        "4" {
            $apiUrl = "http://localhost:11434/v1/chat/completions"
            $model = "llama2"
            $apiKey = "not-needed"
            Write-Color "Make sure Ollama is running locally" "Yellow"
        }
        "5" {
            Write-Color "Skipping configuration. You'll need to set environment variables manually." "Yellow"
            return
        }
        default {
            Write-Color "Invalid choice" "Red"
            return
        }
    }

    # Set environment variables
    Write-Color "Setting environment variables..." "Yellow"

    $scope = if ($System) { "Machine" } else { "User" }

    [Environment]::SetEnvironmentVariable("GIT_COMMIT_AI_KEY", $apiKey, $scope)
    [Environment]::SetEnvironmentVariable("GIT_COMMIT_AI_URL", $apiUrl, $scope)
    [Environment]::SetEnvironmentVariable("GIT_COMMIT_AI_MODEL", $model, $scope)

    # Also set for current session
    $env:GIT_COMMIT_AI_KEY = $apiKey
    $env:GIT_COMMIT_AI_URL = $apiUrl
    $env:GIT_COMMIT_AI_MODEL = $model

    Write-Color "✓ Configuration saved!" "Green"
}

# Test installation
function Test-Installation {
    Write-Color "`nTesting installation..." "Blue"

    # Test git-commitai command
    try {
        $cmd = Get-Command git-commitai -ErrorAction Stop
        & $cmd.Path --version 2>&1 | Out-Null
        Write-Color "✓ git-commitai command found" "Green"
    } catch {
        Write-Color "⚠ git-commitai not accessible yet (restart terminal)" "Yellow"
    }

    # Test git alias
    $gitAlias = git config --get alias.commitai
    if ($gitAlias) {
        Write-Color "✓ git commitai alias configured" "Green"
    } else {
        Write-Color "⚠ git commitai alias not set" "Yellow"
    }

    # Test API configuration
    if ($env:GIT_COMMIT_AI_KEY) {
        Write-Color "✓ API key configured" "Green"
    } else {
        Write-Color "⚠ API key not configured" "Yellow"
    }
}

# Uninstall
function Uninstall-GitCommitAI {
    Write-Color "Uninstalling git-commitai..." "Blue"

    # Remove user installation
    $userBin = "$env:LOCALAPPDATA\Programs\git-commitai"
    $scriptsDir = "$env:APPDATA\Python\Scripts"

    if (Test-Path $userBin) {
        Remove-Item -Path $userBin -Recurse -Force
        Write-Color "✓ Removed user installation" "Green"
    }

    if (Test-Path "$scriptsDir\git-commitai.cmd") {
        Remove-Item -Path "$scriptsDir\git-commitai.cmd" -Force
        Remove-Item -Path "$scriptsDir\git-commitai.ps1" -Force -ErrorAction SilentlyContinue
        Write-Color "✓ Removed command wrappers" "Green"
    }

    # Remove system installation (if admin)
    if (Test-Administrator) {
        $systemBin = "$env:ProgramFiles\git-commitai"
        if (Test-Path $systemBin) {
            Remove-Item -Path $systemBin -Recurse -Force
            Write-Color "✓ Removed system installation" "Green"
        }
    }

    # Remove git alias
    git config --global --unset alias.commitai 2>$null
    Write-Color "✓ Removed git alias" "Green"

    Write-Color "Note: Environment variables were not removed" "Yellow"
    Write-Color "Uninstallation complete!" "Green"
}

# Main execution
Write-Color "╔════════════════════════════════════╗" "Blue"
Write-Color "║     Git Commit AI Installer        ║" "Blue"
Write-Color "║         for Windows                 ║" "Blue"
Write-Color "╚════════════════════════════════════╝" "Blue"
Write-Host ""

# Check prerequisites
Test-Prerequisites

# Handle uninstall
if ($Uninstall) {
    Uninstall-GitCommitAI
    exit 0
}

# Run installation
if ($System) {
    Install-System
} else {
    Install-User
}

# Configure environment
Set-Environment

# Test installation
Test-Installation

Write-Color "`n╔════════════════════════════════════╗" "Green"
Write-Color "║    Installation Complete! 🎉       ║" "Green"
Write-Color "╚════════════════════════════════════╝" "Green"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  1. Restart your terminal or command prompt"
Write-Host "  2. Stage some changes: git add ."
Write-Host "  3. Generate commit: git commitai"
Write-Host "  4. View help: git commitai --help"
Write-Host ""
Write-Color "For more information: https://github.com/semperai/git-commitai" "Blue"
