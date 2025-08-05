# claif_cod Documentation

**A Claif provider for OpenAI's Rust-based Codex CLI with full OpenAI client API compatibility.**

## TL;DR

`claif_cod` provides a Python wrapper around OpenAI's new Rust-based Codex CLI, offering full OpenAI client API compatibility. It integrates seamlessly with the Claif framework while providing standalone functionality for AI-powered code generation with multiple safety modes.

**Key Features:**
- 🔄 **OpenAI API Compatible** - Drop-in replacement for OpenAI Python client
- 🦀 **Rust-based Codex** - Uses the latest high-performance Codex CLI  
- 🛡️ **Safety First** - Multiple sandbox and approval modes
- ⚡ **Async Streaming** - Real-time response streaming with proper chunk handling
- 🎨 **Rich CLI** - Beautiful terminal interface with Fire and Rich
- 🔧 **Type Safe** - Full type hints and IDE support

**Quick Start:**
```python
from claif_cod import CodexClient

client = CodexClient()
response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Write a fibonacci function'}],
    model='gpt-4o'
)
print(response.choices[0].message.content)
```

---

## Documentation Chapters

### 1. [Installation](installation.md)
Complete installation guide including prerequisites, package installation, and development setup. Covers the transition from the old Node.js Codex to the new Rust-based version.

### 2. [Quick Start](quickstart.md)
Get up and running with `claif_cod` in minutes. Basic usage examples, first queries, and essential concepts to understand the package workflow.

### 3. [Configuration](configuration.md)
Comprehensive configuration guide covering environment variables, config files, CLI path setup, model selection, and integration with the Claif framework.

### 4. [Python API](python-api.md)
Complete Python API reference with examples. Covers the CodexClient class, async operations, streaming responses, error handling, and advanced usage patterns.

### 5. [CLI Usage](cli-usage.md)
Detailed command-line interface documentation. All CLI commands, options, output formats, interactive modes, and workflow examples for developers.

### 6. [OpenAI Compatibility](openai-compatibility.md)
Comprehensive guide to OpenAI API compatibility. How to use `claif_cod` as a drop-in replacement, differences from standard OpenAI client, and migration strategies.

### 7. [Architecture](architecture.md)
Deep dive into the technical architecture. Component overview, design decisions, subprocess management, message flow, and how everything works under the hood.

### 8. [Message Flow](message-flow.md)
Detailed explanation of how messages flow through the system. From user input to final output, including transformations, error handling, and streaming mechanics.

### 9. [API Reference](api-reference.md)
Complete API documentation with all classes, methods, parameters, return types, and code examples. Auto-generated from source code with additional context.

---

## What is claif_cod?

`claif_cod` is a sophisticated Python wrapper that bridges OpenAI's new Rust-based Codex CLI with the Claif framework ecosystem. It provides full compatibility with the OpenAI Python client API while adding powerful safety features and integration capabilities.

### Core Benefits

- **Unified Interface**: Consistent API across all Claif providers
- **OpenAI Compatible**: Use familiar `client.chat.completions.create()` patterns
- **Safety First**: Multiple sandbox and approval modes for secure code execution
- **Production Ready**: Robust subprocess handling and error recovery
- **Developer Experience**: Rich CLI with beautiful output and comprehensive type hints

### Use Cases

- **Code Generation**: Generate functions, classes, and complete applications
- **Code Review**: Analyze and improve existing codebases
- **Refactoring**: Systematic code improvements and modernization
- **Documentation**: Generate comments, docstrings, and documentation
- **Testing**: Create comprehensive test suites and benchmarks
- **Debugging**: Identify and fix bugs in complex codebases

---

## Quick Navigation

| Section | Description |
|---------|-------------|
| **Getting Started** | Installation, configuration, and first steps |
| **Usage** | Python API, CLI, and OpenAI compatibility |
| **Architecture** | Technical deep-dive and system design |
| **Reference** | Complete API documentation |

---

*Ready to get started? Begin with the [Installation Guide](installation.md) or jump straight to [Quick Start](quickstart.md) if you're familiar with Python packaging.*