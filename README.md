# claif_cod - Codex Provider for Claif

## Quickstart

```bash
# Install and start using Codex
pip install claif_cod
claif-cod query "Write a Python fibonacci function"

# Or use it with the Claif framework
pip install claif[all]
claif query "Refactor this code for better performance" --provider codex

# Stream responses with live display
claif-cod stream "Create a REST API with FastAPI"

# Choose action mode for code safety
claif-cod query "Fix all bugs" --action-mode review  # Preview changes first
```

## What is claif_cod?

`claif_cod` is an async Python wrapper that integrates OpenAI's Codex CLI into the Claif framework. It provides a subprocess-based transport layer that communicates with the Codex CLI through JSON streaming, enabling AI-powered code generation, refactoring, and manipulation with multiple safety modes.

**Key Features:**
- **Async subprocess management** - Efficient streaming with native asyncio
- **Multiple action modes** - Review, interactive, or full-auto code changes
- **Platform-aware CLI discovery** - Works on Windows, macOS, and Linux
- **Timeout protection** - Graceful handling of long operations
- **Rich CLI interface** - Beautiful output with Fire and Rich
- **Type-safe API** - Full type hints and IDE support
- **Clean JSON streaming** - Reliable message parsing and error handling

## Installation

### Prerequisites

You need the Codex CLI binary installed. Set the path via environment variable:

```bash
export CODEX_CLI_PATH=/path/to/codex-cli
```

Or install it via npm:

```bash
npm install -g @openai/codex
```

### Basic Installation

```bash
# Core package only
pip install claif_cod

# With Claif framework
pip install claif claif_cod
```

### Development Installation

```bash
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod
pip install -e ".[dev,test]"

# Or using uv for faster installation
uv pip install -e ".[dev,test]"
```

## CLI Usage

`claif_cod` provides a Fire-based CLI with rich terminal output for all your code generation needs.

### Basic Commands

```bash
# Simple code generation
claif-cod query "Write a sorting algorithm in Python"

# Use specific model
claif-cod query "Optimize this database query" --model o4

# Set parameters
claif-cod query "Add error handling" --temperature 0.2 --max-tokens 2000

# With system prompt
claif-cod query "Convert to TypeScript" --system "You are a TypeScript expert"
```

### Action Modes

Control how code changes are applied to ensure safety:

```bash
# Review mode (default) - Preview all changes before applying
claif-cod query "Fix the bug in main.py" --action-mode review

# Interactive mode - Approve each change individually
claif-cod query "Update all docstrings" --action-mode interactive

# Full-auto mode - Apply all changes automatically (use with caution!)
claif-cod query "Format all files" --action-mode full-auto --auto-approve
```

### Working with Projects

```bash
# Specify project directory
claif-cod query "Run tests and fix failures" --working-dir /path/to/project

# Use current directory
claif-cod query "Add type hints to all functions" --working-dir .

# Work on specific files
claif-cod query "Refactor user.py and auth.py" --working-dir ./src
```

### Streaming Responses

```bash
# Stream responses in real-time
claif-cod stream "Implement a websocket server"

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
claif-cod config set --codex-cli-path /usr/local/bin/codex-cli
claif-cod config set --default-model o4-mini
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
        action_mode="review",
        system_prompt="You are an expert Python developer"
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
        system_prompt="You are an expert in clean code and design patterns",
        auto_approve_everything=False,
        timeout=300
    )
    
    async for message in query("Refactor user authentication module", options):
        if hasattr(message, 'content'):
            print(f"Content: {message.content}")
        
        # Handle different content types
        if hasattr(message.content, '__iter__'):
            for block in message.content:
                if block.type == "code":
                    print(f"Generated code:\n{block.text}")
                elif block.type == "error":
                    print(f"Error: {block.text}")

asyncio.run(generate_code())
```

### Working with Transport Layer

```python
from claif_cod.transport import CodexTransport
from claif_cod.types import CodexOptions

async def custom_transport():
    # Create transport with custom settings
    transport = CodexTransport(
        cli_path="/usr/local/bin/codex-cli",
        timeout=600  # 10 minutes for complex operations
    )
    
    # Execute query
    options = CodexOptions(
        model="o4",
        action_mode="review",
        working_dir=Path("./project")
    )
    
    async for message in transport.send_query("Refactor entire module", options):
        print(f"{message.message_type}: {message.content}")

asyncio.run(custom_transport())
```

### Error Handling

```python
from claif.common import ProviderError, TimeoutError
from claif_cod import query, CodexOptions

async def safe_query():
    try:
        options = CodexOptions(timeout=120)
        async for message in query("Complex refactoring task", options):
            print(message.content)
            
    except TimeoutError:
        print("Operation timed out - try breaking into smaller tasks")
        
    except ProviderError as e:
        print(f"Codex error: {e}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(safe_query())
```

### Using with Claif Framework

```python
from claif import query as claif_query, Provider, ClaifOptions

async def use_with_claif():
    # Query through Claif framework
    options = ClaifOptions(
        provider=Provider.CODEX,
        model="o4-mini",
        temperature=0.2,
        system_prompt="Focus on performance and readability"
    )
    
    async for message in claif_query("Optimize database queries", options):
        print(message.content)

asyncio.run(use_with_claif())
```

## How It Works

### Architecture Overview

```
┌─────────────────────┐
│    User Code        │
├─────────────────────┤
│   Claif Core       │  ← Unified interface (Message types)
├─────────────────────┤
│   claif_cod        │  ← This package (provider adapter)
├─────────────────────┤
│   CodexClient      │  ← Client orchestration layer
├─────────────────────┤
│  CodexTransport    │  ← Async subprocess management
├─────────────────────┤
│  Codex CLI Binary  │  ← External process (JSON I/O)
└─────────────────────┘
```

### Core Components

#### Main Module (`__init__.py`)

Entry point providing the `query()` function:

```python
async def query(
    prompt: str,
    options: ClaifOptions | None = None
) -> AsyncIterator[Message]:
    """Query Codex with unified Claif interface."""
    # Convert options
    codex_options = _convert_options(options) if options else CodexOptions()
    
    # Use module-level client
    async for message in _client.query(prompt, codex_options):
        yield message
```

Features:
- Minimal overhead (22 lines)
- Option conversion from Claif to Codex formats
- Loguru debug logging
- Clean async generator interface

#### CLI Module (`cli.py`)

Fire-based CLI with rich terminal output (334 lines):

```python
class CodexCLI:
    def query(self, prompt: str, **kwargs):
        """Execute a code generation query."""
        
    def stream(self, prompt: str, **kwargs):
        """Stream responses in real-time."""
        
    def models(self):
        """List available models."""
        
    def config(self, action: str = "show", **kwargs):
        """Manage configuration."""
```

Key features:
- Rich progress spinners and tables
- Response formatting (text, json, code)
- Async execution with proper error handling
- Configuration management

#### Client Module (`client.py`)

Orchestrates transport lifecycle (55 lines):

```python
class CodexClient:
    def __init__(self):
        self.transport = None
        
    async def query(self, prompt: str, options: CodexOptions):
        # Lazy transport creation
        if not self.transport:
            self.transport = CodexTransport(options.timeout)
            
        # Convert messages
        async for codex_msg in self.transport.send_query(prompt, options):
            yield self._convert_message(codex_msg)
```

Features:
- Lazy transport initialization
- Message format conversion
- Clean separation of concerns
- Module-level instance for reuse

#### Transport Module (`transport.py`)

Async subprocess management (171 lines):

```python
class CodexTransport:
    async def send_query(self, prompt: str, options: CodexOptions):
        # Find CLI
        cli_path = self._find_cli_path()
        
        # Build command
        cmd = self._build_command(cli_path, prompt, options)
        
        # Execute with streaming
        async with await anyio.open_process(cmd) as proc:
            async for line in proc.stdout:
                if message := self._parse_output_line(line):
                    yield message
```

Key methods:
- `_find_cli_path()` - Platform-aware CLI discovery
- `_build_command()` - Safe argument construction
- `_parse_output_line()` - Resilient JSON parsing
- Timeout handling with process termination

#### Types Module (`types.py`)

Comprehensive type definitions (142 lines):

```python
@dataclass
class CodexOptions:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    action_mode: str | None = None
    working_dir: Path | None = None
    system_prompt: str | None = None
    auto_approve_everything: bool = False
    timeout: int | None = None
    
@dataclass
class CodexMessage:
    message_type: str
    content: list[ContentBlock]
    metadata: dict[str, Any] | None = None
    
    def to_claif_message(self) -> Message:
        """Convert to Claif format."""
```

Content block hierarchy:
- `ContentBlock` (base)
- `TextBlock` - Regular text
- `CodeBlock` - Code snippets
- `ErrorBlock` - Error messages

### Message Flow

1. **User Input** → CLI or Python API call
2. **Option Conversion** → `ClaifOptions` → `CodexOptions`
3. **Client Layer** → `CodexClient.query()` manages lifecycle
4. **Transport Layer** → `CodexTransport.send_query()` spawns subprocess
5. **CLI Discovery** → Check env var → PATH → common locations
6. **Command Building** → `[cli_path, "query", "--model", model, ...]`
7. **Subprocess Execution** → `anyio.open_process()` with JSON streaming
8. **Output Parsing** → Line-by-line JSON parsing
9. **Message Conversion** → `CodexMessage.to_claif_message()`
10. **Async Yielding** → Messages yielded back through generators

### Code Structure

```
claif_cod/
├── src/claif_cod/
│   ├── __init__.py       # Main entry point (22 lines)
│   ├── cli.py           # Fire CLI interface (334 lines)
│   ├── client.py        # Client orchestration (55 lines)
│   ├── transport.py     # Subprocess management (171 lines)
│   └── types.py         # Type definitions (142 lines)
├── tests/
│   └── test_package.py  # Basic tests
├── pyproject.toml       # Package configuration
├── README.md            # This file
└── CLAUDE.md            # Development guide
```

### Configuration

Environment variables:
- `CODEX_CLI_PATH` - Path to Codex CLI binary
- `CODEX_DEFAULT_MODEL` - Default model (o4-mini)
- `CODEX_ACTION_MODE` - Default action mode (review)
- `CODEX_TIMEOUT` - Default timeout in seconds

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

The package supports any model that the Codex CLI accepts:

- **o4-mini** - Fast, efficient for quick tasks (default)
- **o4** - Balanced performance and capability
- **o4-preview** - Latest features and improvements
- **o3.5** - Previous generation model

### Action Modes

- **review** (default) - Preview changes before applying
- **interactive** - Approve each change individually
- **full-auto** - Apply all changes automatically

## Installation with Bun

While the Codex CLI is typically installed via npm, you can use Bun for faster installation:

```bash
# Install bun if needed
curl -fsSL https://bun.sh/install | bash

# Install Codex CLI with bun
bun add -g @openai/codex

# The CLI will be available at
~/.bun/bin/codex
```

## Why Use claif_cod?

### 1. **Unified Interface**
- Consistent API across all Claif providers
- Easy switching between Codex, Claude, and Gemini
- Standardized message format

### 2. **Safety First**
- Default review mode prevents unwanted changes
- Multiple action modes for different risk levels
- Working directory isolation
- Timeout protection

### 3. **Developer Experience**
- Rich CLI with beautiful output
- Full async support
- Comprehensive type hints
- Clear error messages

### 4. **Production Ready**
- Robust subprocess handling
- Graceful error recovery
- Platform-specific optimizations
- Extensive logging

### 5. **Integration**
- Seamless Claif framework integration
- Plugin architecture
- Configuration inheritance
- Compatible with existing codebases

## Best Practices

1. **Always start with review mode** to understand changes
2. **Use specific prompts** for better results
3. **Set appropriate timeouts** for complex operations
4. **Test generated code** thoroughly
5. **Use version control** before applying changes
6. **Configure working directory** to limit scope
7. **Check CLI path** with `health` command
8. **Use verbose mode** for debugging

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod

# Install with dev dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claif_cod --cov-report=html

# Run specific test
pytest tests/test_transport.py -v
```

### Code Quality

```bash
# Format code
ruff format src/claif_cod tests

# Lint code
ruff check src/claif_cod tests --fix

# Type checking
mypy src/claif_cod

# Run all checks (as per CLAUDE.md)
fd -e py -x ruff format {}
fd -e py -x ruff check --fix --unsafe-fixes {}
python -m pytest
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Adam Twardoch

## Links

### claif_cod Resources

- [GitHub Repository](https://github.com/twardoch/claif_cod) - Source code
- [PyPI Package](https://pypi.org/project/claif_cod/) - Latest release
- [Issue Tracker](https://github.com/twardoch/claif_cod/issues) - Bug reports
- [Documentation](https://claif-cod.readthedocs.io/) - Full docs

### Related Projects

**Claif Ecosystem:**
- [Claif](https://github.com/twardoch/claif) - Main framework
- [claif_cla](https://github.com/twardoch/claif_cla) - Claude provider
- [claif_gem](https://github.com/twardoch/claif_gem) - Gemini provider

**Upstream Projects:**
- [OpenAI Codex](https://openai.com/blog/openai-codex/) - Codex documentation
- [OpenAI API](https://platform.openai.com/) - API reference

**Tools & Libraries:**
- [Fire](https://github.com/google/python-fire) - CLI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [anyio](https://github.com/agronholm/anyio) - Async compatibility
- [Loguru](https://github.com/Delgan/loguru) - Logging library