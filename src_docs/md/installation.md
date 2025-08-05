# Installation

This guide covers everything you need to install and set up `claif_cod` on your system.

## Prerequisites

### Rust-based Codex CLI

`claif_cod` requires the new Rust-based Codex CLI. The old Node.js version is no longer supported.

#### Installing Codex CLI

=== "Cargo (Recommended)"

    ```bash
    # Install via Cargo (Rust package manager)
    cargo install codex
    ```

=== "GitHub Releases"

    ```bash
    # Download from GitHub releases
    # Visit: https://github.com/openai/codex/releases
    # Download the appropriate binary for your platform
    
    # On Linux/macOS, make it executable:
    chmod +x codex
    sudo mv codex /usr/local/bin/
    ```

=== "Package Managers"

    ```bash
    # Homebrew (macOS/Linux)
    brew install openai/tap/codex
    
    # Chocolatey (Windows)
    choco install codex
    
    # Scoop (Windows)
    scoop install codex
    ```

#### Verify Installation

```bash
# Check if codex is available
codex --version

# Test basic functionality
codex --help
```

!!! warning "Node.js Version No Longer Supported"
    If you have the old Node.js-based codex installed, you'll receive a warning to upgrade:
    
    ```bash
    # ❌ Old version (don't use)
    npm install -g @openai/codex
    
    # ✅ New version (required)
    cargo install codex
    ```

### Python Requirements

- **Python 3.11+** (Python 3.12 recommended)
- **pip** or **uv** for package installation

## Installation Methods

### Basic Installation

=== "pip"

    ```bash
    # Install from PyPI
    pip install claif_cod
    ```

=== "uv (Recommended)"

    ```bash
    # Install with uv (faster)
    uv pip install claif_cod
    ```

### With Claif Framework

If you want to use `claif_cod` with the full Claif framework:

=== "pip"

    ```bash
    # Install with Claif framework
    pip install claif claif_cod
    ```

=== "uv"

    ```bash
    # Install with Claif framework
    uv pip install claif claif_cod
    ```

### Development Installation

For contributing or modifying the package:

```bash
# Clone the repository
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod

# Install in development mode with all extras
pip install -e ".[dev,test,docs]"

# Or with uv
uv pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install
```

## Configuration

### Environment Variables

Set up environment variables for optimal experience:

```bash
# Optional: Specify codex CLI path if not in PATH
export CODEX_CLI_PATH="/usr/local/bin/codex"

# Optional: Set default model
export CODEX_DEFAULT_MODEL="o4-mini"

# Optional: Set default action mode
export CODEX_ACTION_MODE="review"

# Optional: Set default timeout (seconds)
export CODEX_TIMEOUT="180"

# Required: OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### CLI Path Discovery

`claif_cod` automatically discovers the Codex CLI using this priority order:

1. **CODEX_CLI_PATH** environment variable
2. **PATH** system environment
3. **Common installation locations**:
   - `/usr/local/bin/codex`
   - `/opt/homebrew/bin/codex`
   - `~/.cargo/bin/codex`
   - Windows: `%USERPROFILE%\.cargo\bin\codex.exe`

### Verify Installation

Test your installation:

```bash
# Check if claif-cod CLI is available
claif-cod --help

# Test health check
claif-cod health

# Test basic query
claif-cod query "Hello, world!" --model o4-mini
```

## Platform-Specific Notes

### macOS

```bash
# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Codex CLI
cargo install codex

# Install claif_cod
uv pip install claif_cod

# Set up environment
echo 'export CODEX_CLI_PATH="$HOME/.cargo/bin/codex"' >> ~/.zshrc
source ~/.zshrc
```

### Linux

```bash
# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Codex CLI
cargo install codex

# Install claif_cod
uv pip install claif_cod

# Add to PATH if needed
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Windows

```powershell
# Install Rust if needed
# Visit: https://rustup.rs/

# Install Codex CLI
cargo install codex

# Install claif_cod
uv pip install claif_cod

# Set environment variable
[Environment]::SetEnvironmentVariable("CODEX_CLI_PATH", "$env:USERPROFILE\.cargo\bin\codex.exe", "User")
```

## Docker Installation

For containerized environments:

```dockerfile
FROM python:3.12-slim

# Install Rust and Cargo
RUN apt-get update && apt-get install -y curl build-essential
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Codex CLI
RUN cargo install codex

# Install claif_cod
RUN pip install claif_cod

# Set environment variables
ENV CODEX_CLI_PATH="/root/.cargo/bin/codex"
ENV OPENAI_API_KEY="your-api-key"

# Verify installation
RUN claif-cod health
```

## Troubleshooting

### Common Issues

#### Codex CLI Not Found

```bash
# Error: Codex CLI not found
# Solution: Verify installation and PATH

# Check if codex is installed
which codex
# or
whereis codex

# If not found, reinstall
cargo install codex

# If still not found, set explicit path
export CODEX_CLI_PATH="/path/to/codex"
```

#### Permission Denied

```bash
# Error: Permission denied
# Solution: Fix permissions

# Make codex executable
chmod +x /path/to/codex

# Or reinstall in user directory
cargo install codex --force
```

#### Import Errors

```python
# Error: ModuleNotFoundError: No module named 'claif_cod'
# Solution: Ensure proper installation

# Reinstall package
pip uninstall claif_cod
pip install claif_cod

# Check installation
python -c "import claif_cod; print(claif_cod.__version__)"
```

#### OpenAI API Key Issues

```bash
# Error: OpenAI API key not found
# Solution: Set environment variable

export OPENAI_API_KEY="your-actual-api-key"

# Or pass directly to client
python -c "
from claif_cod import CodexClient
client = CodexClient(api_key='your-api-key')
"
```

### Getting Help

If you encounter issues:

1. **Check the logs**: Enable verbose mode with `--verbose`
2. **Verify prerequisites**: Run `claif-cod health`
3. **Check GitHub Issues**: [Report bugs](https://github.com/twardoch/claif_cod/issues)
4. **Community support**: Join the discussion in the repository

## Next Steps

Once installation is complete:

1. **[Quick Start](quickstart.md)** - Get up and running quickly
2. **[Configuration](configuration.md)** - Detailed configuration options
3. **[Python API](python-api.md)** - Learn the Python interface
4. **[CLI Usage](cli-usage.md)** - Master the command-line interface

---

*Having trouble? Check the [troubleshooting section](#troubleshooting) or [open an issue](https://github.com/twardoch/claif_cod/issues) on GitHub.*