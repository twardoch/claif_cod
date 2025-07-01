# CLAIF_COD - Codex Provider for CLAIF

CLAIF_COD is the Codex provider implementation for the CLAIF (Command Line Artificial Intelligence Framework). It provides a wrapper around the Codex CLI to integrate advanced code generation and manipulation capabilities into the unified CLAIF ecosystem.

## What is CLAIF_COD?

CLAIF_COD is a specialized provider package that:
- Wraps the Codex CLI for use with CLAIF
- Provides code-focused AI capabilities
- Supports multiple action modes (review, interactive, full-auto)
- Handles subprocess communication with the Codex binary
- Offers a Fire-based CLI with rich terminal output
- Includes timeout and error handling for subprocess operations

## Installation

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

### With CLAIF
```bash
# Install CLAIF with Codex support
pip install claif claif_cod
```

### Prerequisites
You need to have the Codex CLI binary installed and accessible. Set the path:
```bash
export CODEX_CLI_PATH=/path/to/codex-cli
```

## Command Line Usage

CLAIF_COD provides its own Fire-based CLI with specialized features for code generation:

### Basic Queries
```bash
# Ask Codex to write code
claif-cod query "Write a Python function to calculate fibonacci numbers"

# Query with specific model
claif-cod query "Refactor this code" --model o4

# Query with custom parameters
claif-cod query "Add type hints" --temperature 0.2 --max-tokens 1000
```

### Action Modes
```bash
# Review mode (default) - shows changes before applying
claif-cod query "Fix the bug in main.py" --action-mode review

# Interactive mode - prompts for each action
claif-cod query "Optimize this function" --action-mode interactive

# Full-auto mode - applies all changes automatically
claif-cod query "Add error handling" --action-mode full-auto

# Auto-approve all actions
claif-cod query "Update dependencies" --auto-approve
```

### Working Directory
```bash
# Specify working directory for code execution
claif-cod query "Run tests and fix failures" --working-dir /path/to/project

# Use current directory
claif-cod query "Format all Python files" --working-dir .
```

### Streaming
```bash
# Stream responses in real-time
claif-cod stream "Implement a REST API"

# Stream with specific model
claif-cod stream "Write unit tests" --model o4
```

### Code-Specific Output
```bash
# Output format optimized for code
claif-cod query "Generate a class" --output-format code

# Show metrics for performance analysis
claif-cod query "Optimize algorithm" --show-metrics
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

# Set Codex CLI path
claif-cod config set --codex_cli_path /usr/local/bin/codex-cli

# Save configuration
claif-cod config save
```

## Python API Usage

### Basic Usage
```python
import asyncio
from claif_cod import query, CodexOptions

async def main():
    # Simple code generation
    async for message in query("Write a sorting algorithm"):
        print(message.content)
    
    # Query with options
    options = CodexOptions(
        model="o4",
        temperature=0.2,
        action_mode="review",
        working_dir=Path("./src")
    )
    async for message in query("Refactor database module", options):
        print(message.content)

asyncio.run(main())
```

### Action Modes
```python
from claif_cod.types import CodexOptions, ActionMode

# Review mode - see changes before applying
options = CodexOptions(
    action_mode="review",
    auto_approve_everything=False
)

# Interactive mode - approve each change
options = CodexOptions(
    action_mode="interactive"
)

# Full automation
options = CodexOptions(
    action_mode="full-auto",
    full_auto=True
)
```

### Working with Projects
```python
from pathlib import Path

# Set project directory
options = CodexOptions(
    working_dir=Path("/path/to/project"),
    action_mode="review"
)

# Generate code in specific directory
async for message in query("Create a new module", options):
    print(message.content)
```

### Subprocess Management
```python
from claif_cod.transport import CodexTransport

# Create transport with custom timeout
transport = CodexTransport(
    cli_path="/usr/local/bin/codex-cli",
    timeout=300  # 5 minutes
)

# Execute query
async for message in transport.query("Complex refactoring", options):
    print(message.content)
```

## Why Use CLAIF_COD?

### 1. **Code-Focused AI**
- Specialized for code generation and manipulation
- Understanding of project context and structure
- Intelligent refactoring and optimization

### 2. **Flexible Action Modes**
- **Review Mode**: See all changes before applying
- **Interactive Mode**: Approve changes one by one
- **Full-Auto Mode**: Fully automated code changes

### 3. **Project Integration**
- Works with existing codebases
- Respects project structure
- Handles multiple file operations

### 4. **Safety Features**
- Review changes before applying
- Timeout protection for long operations
- Error handling and recovery

## How It Works

### Architecture

```
┌─────────────────────┐
│    CLAIF Core       │
├─────────────────────┤
│   Codex Provider    │
├─────────────────────┤
│    CLAIF_COD        │
├─────────────────────┤
│  Subprocess Layer   │
├─────────────────────┤
│   Codex CLI Binary  │
└─────────────────────┘
```

### Core Components

#### 1. **Main Module** (`__init__.py`)
Provides the main `query` function that:
- Converts CLAIF options to CodexOptions
- Delegates to the client module
- Yields normalized messages

#### 2. **Client Module** (`client.py`)
- Manages the query lifecycle
- Handles option validation
- Coordinates with transport layer

#### 3. **Transport Module** (`transport.py`)
- `CodexTransport`: Manages subprocess communication
- Handles CLI path resolution
- Implements timeout and error handling
- Parses CLI output into messages

#### 4. **Types Module** (`types.py`)
- `CodexOptions`: Configuration for queries
- `ActionMode`: Enum for action modes
- Type definitions for strong typing

#### 5. **CLI Module** (`cli.py`)
Fire-based CLI providing:
- Query commands with all options
- Streaming support
- Model management
- Configuration handling

### Message Flow

1. Query enters through CLAIF interface
2. CLAIF_COD converts options to CodexOptions
3. Client validates and prepares the query
4. Transport spawns Codex CLI subprocess
5. CLI arguments constructed from options
6. Subprocess output parsed into messages
7. Messages normalized to CLAIF format
8. Messages yielded to user

### Configuration

CLAIF_COD inherits configuration from CLAIF and adds:

```toml
[providers.codex]
enabled = true
cli_path = "/usr/local/bin/codex-cli"
default_model = "o4-mini"
default_action_mode = "review"
timeout = 180

[codex.models]
available = ["o4", "o4-mini", "o4-turbo"]
default = "o4-mini"

[codex.safety]
auto_approve = false
full_auto = false
```

### Environment Variables

- `CODEX_CLI_PATH`: Path to Codex CLI binary
- `CODEX_DEFAULT_MODEL`: Default model to use
- `CODEX_ACTION_MODE`: Default action mode
- `CODEX_TIMEOUT`: Default timeout in seconds

### Action Modes Explained

#### Review Mode (Default)
- Shows all proposed changes
- Requires manual confirmation
- Safe for production code

#### Interactive Mode
- Prompts for each individual change
- Fine-grained control
- Good for selective updates

#### Full-Auto Mode
- Applies all changes automatically
- No confirmation required
- Use with caution

## Error Handling

CLAIF_COD provides robust error handling:

```python
from claif_cod.transport import CodexTransport
from claif.common import ProviderError, TimeoutError

try:
    async for message in query("Generate code"):
        print(message.content)
except TimeoutError:
    print("Query timed out")
except ProviderError as e:
    print(f"Codex error: {e}")
```

## Best Practices

1. **Start with Review Mode**: Always review AI-generated code changes
2. **Use Specific Prompts**: Clear, specific prompts yield better results
3. **Set Appropriate Timeouts**: Complex operations may need longer timeouts
4. **Test Generated Code**: Always test AI-generated code thoroughly
5. **Version Control**: Commit before using full-auto mode

## Contributing

To contribute to CLAIF_COD:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Links

- [GitHub Repository](https://github.com/twardoch/claif_cod)
- [PyPI Package](https://pypi.org/project/claif_cod/)
- [CLAIF Framework](https://github.com/twardoch/claif)
- [Codex Documentation](https://codex.ai/docs)