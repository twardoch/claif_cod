# CLAIF_COD - Codex Provider for CLAIF

**CLAIF_COD** is a Python package that provides integration with OpenAI's Codex CLI as part of the CLAIF (Command-Line Artificial Intelligence Framework) ecosystem. It enables AI-powered code generation, refactoring, and manipulation through both command-line and programmatic interfaces.

## What is CLAIF_COD?

CLAIF_COD is a specialized provider that wraps the Codex CLI binary, offering:

- **AI-powered code generation and manipulation** through OpenAI's Codex models
- **Multiple action modes** for different levels of automation (review, interactive, full-auto)
- **Project-aware operations** with working directory support
- **Subprocess management** with timeout protection and error handling
- **Rich terminal output** with progress indicators and formatted tables
- **Async/await support** for modern Python applications

The package acts as a bridge between the CLAIF framework and the Codex CLI, normalizing messages and providing a consistent interface across different AI providers.

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

### With CLAIF Framework
```bash
# Install CLAIF with Codex support
pip install claif[cod]
# or
pip install claif claif_cod
```

### Development Installation
```bash
# Install with all development dependencies
pip install -e ".[dev,test,docs,all]"
```

## Command Line Usage

CLAIF_COD provides a Fire-based CLI with rich terminal output:

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

## Why CLAIF_COD is Useful

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
- Works seamlessly with the CLAIF framework
- Plugin architecture for easy extension
- Configuration inheritance from CLAIF
- Compatible with existing codebases

## How It Works

### Architecture Overview

```
┌─────────────────────┐
│    User Code        │
├─────────────────────┤
│    CLAIF Core       │  ← Unified interface
├─────────────────────┤
│    CLAIF_COD        │  ← This package
├─────────────────────┤
│ CodexTransport      │  ← Subprocess management
├─────────────────────┤
│  Codex CLI Binary   │  ← External process
└─────────────────────┘
```

### Codebase Structure

```
src/claif_cod/
├── __init__.py       # Main entry point, exports query() function
├── __version__.py    # Version information (auto-generated)
├── cli.py           # Fire-based CLI with rich output
├── client.py        # Client logic for query lifecycle
├── transport.py     # Subprocess communication layer
└── types.py         # Type definitions and data structures
```

### Component Details

#### `__init__.py` - Main Entry Point
- Exports the primary `query()` async function
- Handles conversion between CLAIF and Codex options
- Provides version information
- Implements the CLAIF provider interface

#### `cli.py` - Command Line Interface
- Fire-based CLI framework
- Rich terminal output with tables and progress
- Commands: query, stream, models, health, config, modes
- Handles user input and formatting

#### `client.py` - Client Logic
- Manages the query lifecycle
- Validates options and parameters
- Coordinates with transport layer
- Normalizes messages to CLAIF format

#### `transport.py` - Transport Layer
- `CodexTransport` class for subprocess management
- CLI path discovery (env var → PATH → common locations)
- Command building with proper escaping
- JSON streaming parser for output
- Platform-specific handling (Windows, macOS, Linux)
- Timeout and error management

#### `types.py` - Type Definitions
- `CodexOptions`: Configuration dataclass
- `CodexMessage`: Message structure from Codex
- `TextBlock`, `CodeBlock`, `ErrorBlock`: Content types
- `ResultMessage`: Metadata and results
- Type hints for better IDE support

### Message Flow

1. **User Input** → CLI or Python API
2. **Option Conversion** → CLAIF options to CodexOptions
3. **Transport Layer** → Spawn Codex CLI subprocess
4. **Command Building** → Construct CLI arguments
5. **Execution** → Run subprocess with timeout
6. **Output Parsing** → Stream JSON lines
7. **Message Normalization** → Convert to CLAIF format
8. **User Output** → Yield messages to caller

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

- **o4-mini**: Fast, efficient model for quick tasks
- **o4**: Balanced model for general use
- **o4-preview**: Latest features and capabilities
- **o3.5**: Previous generation model

### Action Modes

- **review** (default): Preview changes before applying
- **interactive**: Approve each change individually
- **full-auto**: Apply all changes automatically

## Best Practices

1. **Always start with review mode** to understand what changes will be made
2. **Use specific, clear prompts** for better results
3. **Set appropriate timeouts** for complex operations
4. **Test generated code** thoroughly before production use
5. **Use version control** before applying automated changes
6. **Configure working directory** to limit scope of operations

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claif_cod --cov-report=html

# Run specific test file
pytest tests/test_transport.py
```

### Linting and Formatting
```bash
# Run linting
ruff check src/claif_cod tests

# Format code
ruff format src/claif_cod tests

# Type checking
mypy src/claif_cod
```

### Building Documentation
```bash
# Build Sphinx docs
cd docs && make html
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
- [CLAIF Framework](https://github.com/twardoch/claif)
- [Documentation](https://claif-cod.readthedocs.io/)

## Related Projects

- [CLAIF](https://github.com/twardoch/claif) - The main framework
- [CLAIF_CLA](https://github.com/twardoch/claif_cla) - Claude provider
- [CLAIF_GEM](https://github.com/twardoch/claif_gem) - Gemini provider