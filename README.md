#`claif_cod` - Codex Provider forClaif

## Quickstart

Claif_COD is an async Python wrapper that integrates CLI-based AI code generation tools into the Claif framework. It provides a subprocess-based transport layer that communicates with AI CLIs through JSON streaming, offering both command-line and Python API interfaces for code generation tasks. Version 1.0.5 improves subprocess reliability by switching to native asyncio.

```bash
pip install claif_cod && claif-cod query "Write a Python function to calculate fibonacci numbers"
```

**Claif_COD** is a Python package that provides integration with OpenAI's Codex CLI as part of the Claif (Command-Line Artificial Intelligence Framework) ecosystem. It enables AI-powered code generation, refactoring, and manipulation through both command-line and programmatic interfaces.

## What`claif_cod` Does

Claif_COD acts as a specialized provider that creates an async subprocess wrapper around the Codex CLI binary. The package:

- **Manages subprocess communication** with the Codex CLI binary through async streaming
- **Converts betweenClaif and Codex message formats** for unified API compatibility
- **Provides multiple action modes** (review, interactive, full-auto) for code safety
- **Handles platform-specific CLI discovery** across Windows, macOS, and Linux
- **Implements timeout protection** and graceful error handling for long operations
- **Offers both CLI and Python API** interfaces with rich terminal output
- **Logs operations with loguru** for debugging and monitoring

The transport layer spawns the Codex CLI as a subprocess, streams JSON-formatted messages, and normalizes them into the Claif message format for consistent cross-provider usage.

## Installation

### Prerequisites

You need to have the Codex CLI binary installed. Set the path via environment variable:
```bash
export CODEX_CLI_PATH=/path/to/codex-cli
```

### From PyPI
```bash
pip install claif_cod
```

### From Source
```bash
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod
pip install -e .
```

### WithClaif Framework
```bash
# InstallClaif with Codex support
pip install claif[cod]
# or
pip install claif claif_cod
```

### Development Installation
```bash
# Clone and install with development dependencies
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod
pip install -e ".[dev,test]"

# Or using uv for faster installation
uv pip install -e ".[dev,test]"
```

## Command Line Usage

Claif_COD provides a Fire-based CLI with rich terminal output:

### Basic Commands

```bash
# Simple code generation
claif-cod query "Write a Python function to calculate fibonacci numbers"

# Use specific model
claif-cod query "Refactor this code for better performance" --model o4

# Set custom parameters
claif-cod query "Add comprehensive error handling" --temperature 0.2 --max-tokens 2000
```

### Action Modes

Control how code changes are applied:

```bash
# Review mode (default) - preview all changes before applying
claif-cod query "Fix the bug in main.py" --action-mode review

# Interactive mode - approve each change individually
claif-cod query "Update all docstrings" --action-mode interactive

# Full-auto mode - apply all changes automatically
claif-cod query "Format all files" --action-mode full-auto --auto-approve
```

### Working with Projects

```bash
# Specify project directory
claif-cod query "Run tests and fix failures" --working-dir /path/to/project

# Use current directory
claif-cod query "Add type hints to all functions" --working-dir .
```

### Streaming Responses

```bash
# Stream responses in real-time
claif-cod stream "Implement a REST API with FastAPI"

# Stream with specific model
claif-cod stream "Create comprehensive unit tests" --model o4-preview
```

### Model Management

```bash
# List available models
claif-cod models

# Show model details
claif-cod model-info o4-mini

# List action modes
claif-cod modes
```

### Configuration

```bash
# Show current configuration
claif-cod config show

# Set configuration values
claif-cod config set --codex_cli_path /usr/local/bin/codex-cli
claif-cod config set --default_model o4-mini
claif-cod config set --timeout 300

# Save configuration
claif-cod config save
```

### Additional Commands

```bash
# Check service health
claif-cod health

# Show version
claif-cod version
```

## Python API Usage

### Basic Usage

```python
import asyncio
from claif_cod import query, CodexOptions

async def main():
    # Simple query
    async for message in query("Write a sorting algorithm"):
        print(message.content)
    
    # With options
    options = CodexOptions(
        model="o4",
        temperature=0.2,
        max_tokens=1500,
        action_mode="review"
    )
    async for message in query("Optimize this function", options):
        print(message.content)

asyncio.run(main())
```

### Advanced Configuration

```python
from pathlib import Path
from claif_cod import query, CodexOptions

async def generate_code():
    options = CodexOptions(
        model="o4-preview",
        temperature=0.3,
        max_tokens=2000,
        action_mode="interactive",
        working_dir=Path("./src"),
        system_prompt="You are an expert Python developer",
        auto_approve_everything=False,
        timeout=300
    )
    
    async for message in query("Create a web scraper", options):
        if message.content_type == "code":
            print(f"Generated code:\n{message.content}")
        elif message.content_type == "error":
            print(f"Error: {message.content}")
        else:
            print(message.content)
```

### Working with Transport Layer

```python
from claif_cod.transport import CodexTransport
from claif_cod.types import CodexOptions

# Create custom transport
transport = CodexTransport(
    cli_path="/usr/local/bin/codex-cli",
    timeout=600  # 10 minutes for complex operations
)

# Execute query
options = CodexOptions(model="o4", action_mode="review")
async for message in transport.query("Refactor entire module", options):
    print(f"{message.message_type}: {message.content}")
```

### Error Handling

```python
from claif.common import ProviderError, TimeoutError
from claif_cod import query, CodexOptions

async def safe_query():
    try:
        options = CodexOptions(timeout=120)
        async for message in query("Complex refactoring", options):
            print(message.content)
    except TimeoutError:
        print("Operation timed out")
    except ProviderError as e:
        print(f"Codex error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Why`claif_cod` is Useful

### 1. **Unified Interface**
- Consistent API across different AI providers
- Easy switching between Codex, Claude, Gemini, and others
- Standardized message format and error handling

### 2. **Safety Features**
- Default review mode prevents unwanted changes
- Timeout protection for long-running operations
- Clear error messages and logging
- Working directory isolation

### 3. **Developer Experience**
- Rich CLI with colored output and progress indicators
- Both sync and async APIs
- Type hints and IDE support
- Comprehensive documentation

### 4. **Integration**
- Works seamlessly with the Claif framework
- Plugin architecture for easy extension
- Configuration inheritance fromClaif
- Compatible with existing codebases

## How`claif_cod` Works

### Architecture Overview

```
┌─────────────────────┐
│    User Code        │
├─────────────────────┤
│   Claif Core       │  ← Unified interface (Message types)
├─────────────────────┤
│   `claif_cod`        │  ← This package (provider adapter)
├─────────────────────┤
│   CodexClient       │  ← Client orchestration layer
├─────────────────────┤
│  CodexTransport     │  ← Async subprocess management
├─────────────────────┤
│  Codex CLI Binary   │  ← External process (JSON I/O)
└─────────────────────┘
```

### Codebase Structure

The package is organized into five main modules:

```
src/claif_cod/
├── __init__.py       # Main entry point, exports query() function
├── cli.py           # Fire-based CLI with rich terminal output
├── client.py        # Client orchestration and message conversion
├── transport.py     # Async subprocess communication layer
└── types.py         # Type definitions and data structures
```

### Component Details

#### `__init__.py` - Main Entry Point (22 lines)
- Exports the primary `query()` async generator function
- ConvertsClaif's `ClaifOptions` to `CodexOptions`
- Imports from `claif.common` for unified Message types
- Uses loguru for debug logging
- Version string: "0.1.0"

#### `cli.py` - Command Line Interface (334 lines)
- `CodexCLI` class with Fire-based commands
- Rich console output with progress spinners and tables
- Commands implemented:
  - `query`: Execute a prompt with options
  - `stream`: Real-time streaming responses
  - `models`: List available models
  - `model_info`: Show model details
  - `modes`: List action modes
  - `health`: Check service status
  - `config`: Manage configuration
  - `version`: Show version info
- Async execution with `asyncio.run()`
- Response formatting (text, json, code modes)

#### `client.py` - Client Orchestration (55 lines)
- `CodexClient` class manages transport lifecycle
- Module-level `_client` instance for reuse
- Converts `CodexMessage` toClaif `Message` format
- Handles connection/disconnection
- Error propagation from transport layer

#### `transport.py` - Async Subprocess Layer (171 lines)
- `CodexTransport` class with anyio for async subprocess
- Key methods:
  - `_find_cli_path()`: Platform-aware CLI discovery
  - `_build_command()`: Construct CLI arguments
  - `send_query()`: Execute subprocess and stream output
  - `_parse_output_line()`: JSON line parsing
- Uses `anyio.open_process()` for subprocess management
- Graceful timeout handling with process termination
- Stderr collection for error reporting

#### `types.py` - Type Definitions (142 lines)
- Data classes with `@dataclass` decorator:
  - `CodexOptions`: All configuration options
  - `ContentBlock` (base class)
  - `TextBlock`, `CodeBlock`, `ErrorBlock`: Content types
  - `CodexMessage`: Main message structure
  - `ResultMessage`: Completion metadata
- Method `to_claif_message()` for format conversion
- Comprehensive type hints for IDE support

### Message Flow

1. **User Input** → CLI (`fire.Fire`) or Python API
2. **Option Conversion** → `ClaifOptions` → `CodexOptions` in `__init__.py`
3. **Client Layer** → `CodexClient.query()` manages lifecycle
4. **Transport Layer** → `CodexTransport.send_query()` spawns subprocess
5. **CLI Discovery** → Check env var → PATH → common locations
6. **Command Building** → Construct args: `[cli_path, "query", "--model", model, ...]`
7. **Subprocess Execution** → `anyio.open_process()` with JSON streaming
8. **Output Parsing** → Line-by-line JSON parsing in `_parse_output_line()`
9. **Message Conversion** → `CodexMessage.to_claif_message()` normalizes format
10. **Async Yielding** → Messages yielded back through async generators

### Configuration

Environment variables:
- `CODEX_CLI_PATH`: Path to Codex CLI binary
- `CODEX_DEFAULT_MODEL`: Default model (o4-mini)
- `CODEX_ACTION_MODE`: Default action mode (review)
- `CODEX_TIMEOUT`: Default timeout in seconds

Configuration file (`~/.claif/config.toml`):
```toml
[providers.codex]
enabled = true
cli_path = "/usr/local/bin/codex-cli"
default_model = "o4-mini"
default_action_mode = "review"
timeout = 180

[providers.codex.models]
available = ["o3.5", "o4-mini", "o4", "o4-preview"]
default = "o4-mini"
```

### Models Available

The package supports any model that the Codex CLI accepts. Common models include:

- **o4-mini**: Fast, efficient model for quick tasks (default)
- **o4**: Balanced model for general use
- **o4-preview**: Latest features and capabilities
- **o3.5**: Previous generation model

The actual available models depend on your Codex CLI version and API access.

### Action Modes

- **review** (default): Preview changes before applying
- **interactive**: Approve each change individually
- **full-auto**: Apply all changes automatically

## Best Practices

1. **Always start with review mode** to understand what changes will be made
2. **Use specific, clear prompts** for better results
3. **Set appropriate timeouts** for complex operations (default: 180s)
4. **Test generated code** thoroughly before production use
5. **Use version control** before applying automated changes
6. **Configure working directory** to limit scope of operations
7. **Check CLI path** with `health` command if encountering issues
8. **Use verbose mode** (`--verbose`) for debugging transport issues

## Development

### Setting Up Development Environment
```bash
# Clone the repository
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod

# Install with dev dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all tests with pytest
pytest

# Run with coverage
pytest --cov=claif_cod --cov-report=html

# Run specific test file
pytest tests/test_package.py -v
```

### Code Quality Tools
```bash
# Format code with ruff
ruff format src/claif_cod tests

# Check linting
ruff check src/claif_cod tests --fix

# Type checking with mypy
mypy src/claif_cod

# Run all formatters (as per CLAUDE.md)
fd -e py -x autoflake {}
fd -e py -x pyupgrade --py312-plus {}
fd -e py -x ruff check --output-format=github --fix --unsafe-fixes {}
fd -e py -x ruff format --respect-gitignore --target-version py312 {}
```

### Building and Publishing
```bash
# Build distribution
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with descriptive message
6. Push to your fork
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/twardoch/claif_cod)
- [PyPI Package](https://pypi.org/project/claif_cod/)
- [Claif Framework](https://github.com/twardoch/claif)
- [Documentation](https://claif-cod.readthedocs.io/)

## Related Projects

- [Claif](https://github.com/twardoch/claif) - The main framework
- [Claif_CLA](https://github.com/twardoch/claif_cla) - Claude provider
- [Claif_GEM](https://github.com/twardoch/claif_gem) - Gemini provider