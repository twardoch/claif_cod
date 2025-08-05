# Quick Start

Get up and running with `claif_cod` in just a few minutes. This guide assumes you've already [installed the package](installation.md).

## First Steps

### 1. Verify Installation

```bash
# Test that everything is working
claif-cod health

# Should output something like:
# ✅ Codex CLI found at: /usr/local/bin/codex
# ✅ OpenAI API key configured
# ✅ All systems ready
```

### 2. Your First Query

=== "Python API"

    ```python
    from claif_cod import CodexClient

    # Initialize client
    client = CodexClient()

    # Create a completion (exactly like OpenAI)
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
        ],
        model="o4-mini"
    )

    # Print the result
    print(response.choices[0].message.content)
    ```

=== "CLI"

    ```bash
    # Simple query
    claif-cod query "Write a Python function to calculate fibonacci numbers"

    # With specific model
    claif-cod query "Create a REST API with FastAPI" --model o4
    ```

### 3. Streaming Responses

=== "Python API"

    ```python
    from claif_cod import CodexClient

    client = CodexClient()

    # Enable streaming for real-time responses
    stream = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Explain how neural networks work"}
        ],
        model="o4-mini",
        stream=True
    )

    # Process chunks as they arrive
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    ```

=== "CLI"

    ```bash
    # Stream responses in real-time
    claif-cod stream "Explain machine learning concepts"
    ```

## Basic Concepts

### Models

`claif_cod` supports all models available in the Codex CLI:

- **o4-mini** - Fast and efficient (default)
- **o4** - Balanced performance and capability  
- **o4-preview** - Latest features
- **o3.5** - Previous generation

```python
# Specify model in Python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    model="o4"  # or "o4-mini", "o4-preview", etc.
)
```

```bash
# Specify model in CLI
claif-cod query "Hello" --model o4
```

### Safety Modes

Control how Codex interacts with your system:

=== "Sandbox Modes"

    - **read-only** - Can only read files (safest)
    - **workspace-write** - Can write within working directory
    - **danger-full-access** - Full system access (use with caution)

=== "Approval Policies"

    - **untrusted** - Require approval for all actions
    - **on-failure** - Only ask when operations fail
    - **never** - Auto-approve everything (risky)

```python
# Python: Configure safety
client = CodexClient(
    sandbox_mode="workspace-write",
    approval_policy="on-failure"
)
```

```bash
# CLI: Configure safety
claif-cod query "Fix bug" --sandbox workspace-write --approval on-failure
```

## Common Usage Patterns

### Code Generation

```python
from claif_cod import CodexClient

client = CodexClient()

# Generate a complete function
response = client.chat.completions.create(
    messages=[{
        "role": "system", 
        "content": "You are an expert Python developer. Write clean, well-documented code."
    }, {
        "role": "user", 
        "content": "Create a class for managing a simple todo list with add, remove, and list methods"
    }],
    model="o4",
    temperature=0.2
)

print(response.choices[0].message.content)
```

### Code Review and Improvement

```bash
# Review specific files
claif-cod query "Review this code for performance issues" --working-dir ./src

# Suggest improvements
claif-cod query "Add type hints and improve error handling" --sandbox workspace-write
```

### Interactive Development

```bash
# Start interactive mode
claif-cod chat --model o4

# Now you can have a conversation:
# > How do I implement a binary search?
# > Can you optimize this algorithm?
# > Add unit tests for the function
```

## Working with Projects

### Set Working Directory

```python
# Python: Specify project directory
client = CodexClient(working_dir="/path/to/your/project")

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Add logging to all functions"}],
    model="o4"
)
```

```bash
# CLI: Use current directory
cd /path/to/your/project
claif-cod query "Refactor user authentication module"

# Or specify directory
claif-cod query "Add tests" --working-dir ./my-project
```

### Multi-file Operations

```python
# Work across multiple files
response = client.chat.completions.create(
    messages=[{
        "role": "user", 
        "content": "Update both models.py and views.py to use async/await patterns"
    }],
    model="o4"
)
```

## Error Handling

### Basic Error Handling

```python
from claif_cod import CodexClient
from openai import OpenAIError

client = CodexClient()

try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
    print(response.choices[0].message.content)
    
except OpenAIError as e:
    print(f"OpenAI API error: {e}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Timeout Handling

```python
# Set custom timeout
client = CodexClient(timeout=300)  # 5 minutes

# Or per-request
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Complex refactoring task"}],
    model="o4",
    timeout=600  # 10 minutes for complex tasks
)
```

## Configuration Examples

### Basic Configuration

```python
from claif_cod import CodexClient

# Simple setup
client = CodexClient(
    model="o4-mini",
    sandbox_mode="workspace-write",
    approval_policy="on-failure"
)
```

### Advanced Configuration

```python
from pathlib import Path
from claif_cod import CodexClient

# Full configuration
client = CodexClient(
    api_key="your-api-key",           # OpenAI API key
    codex_path="/usr/local/bin/codex", # Explicit CLI path
    working_dir=Path("./my-project"),  # Project directory
    model="o4",                       # Default model
    sandbox_mode="workspace-write",    # Sandbox policy
    approval_policy="on-failure",     # Approval policy
    timeout=300                       # Request timeout
)
```

### Environment Variables

```bash
# Set up your environment
export OPENAI_API_KEY="your-api-key"
export CODEX_CLI_PATH="/usr/local/bin/codex"
export CODEX_DEFAULT_MODEL="o4-mini"
export CODEX_ACTION_MODE="review"
export CODEX_TIMEOUT="180"
```

## Output Formats

### CLI Output Formatting

```bash
# Default output (formatted)
claif-cod query "Hello"

# JSON output
claif-cod query "Hello" --format json

# Code-only output
claif-cod query "Write a function" --format code

# Verbose output with debugging
claif-cod query "Hello" --verbose
```

## Next Steps

Now that you're familiar with the basics:

1. **[Configuration](configuration.md)** - Learn about advanced configuration options
2. **[Python API](python-api.md)** - Deep dive into the Python interface
3. **[CLI Usage](cli-usage.md)** - Master all CLI commands and options
4. **[OpenAI Compatibility](openai-compatibility.md)** - Use as OpenAI drop-in replacement

## Quick Reference

### Essential Commands

```bash
# Basic query
claif-cod query "your prompt here"

# Stream response
claif-cod stream "your prompt here"

# Interactive chat
claif-cod chat

# Health check
claif-cod health

# List available models
claif-cod models

# Show configuration
claif-cod config show
```

### Essential Python Patterns

```python
from claif_cod import CodexClient

# Basic usage
client = CodexClient()
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "prompt"}],
    model="o4-mini"
)

# Streaming
for chunk in client.chat.completions.create(
    messages=[{"role": "user", "content": "prompt"}],
    model="o4-mini",
    stream=True
):
    print(chunk.choices[0].delta.content or "", end="")
```

---

*Ready for more advanced usage? Continue with the [Configuration Guide](configuration.md) or dive into the [Python API documentation](python-api.md).*