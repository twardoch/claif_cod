#`claif_cod` - Development Guide for AI Agents

This document provides guidance for AI agents working on the`claif_cod` codebase. It explains the project structure, development principles, and implementation details.

## Project Overview

**Claif_COD** is a provider package for the Claif framework that wraps OpenAI's Codex CLI tool. It enables AI-powered code generation and manipulation through async subprocess management.

### Key Components

1. **Transport Layer** (`transport.py`)
   - Async subprocess management using anyio
   - JSON streaming communication with Codex CLI
   - Platform-aware CLI path discovery
   - Timeout and error handling

2. **Client Layer** (`client.py`)
   - Orchestrates transport lifecycle
   - Converts between Codex andClaif message formats
   - Manages connection state

3. **CLI Interface** (`cli.py`)
   - Fire-based command structure
   - Rich terminal output with progress indicators
   - Multiple output formats (text, json, code)

4. **Type System** (`types.py`)
   - Dataclasses for all message types
   - Options configuration
   - Content block hierarchy

### Current Implementation Status

- ✅ Basic async subprocess communication
- ✅ JSON message parsing and streaming
- ✅ CLI with Fire framework
- ✅ Rich terminal output
- ✅ Message format conversion
- ✅ Error handling and timeouts
- ✅ Platform-specific CLI discovery
- ⚠️ Limited test coverage
- ⚠️ No actual Codex CLI binary (hypothetical)
- ⚠️ Configuration system partially implemented

## Code Architecture Details

### Transport Layer Implementation

The `CodexTransport` class in `transport.py` handles all subprocess communication:

```python
# Key methods:
- _find_cli_path(): Searches for Codex CLI binary
  1. Check CODEX_CLI_PATH environment variable
  2. Search in PATH
  3. Check common installation locations
  
- _build_command(): Constructs CLI arguments
  - Handles all CodexOptions fields
  - Escapes arguments properly
  - Adds JSON output flag
  
- send_query(): Main execution method
  - Uses anyio.open_process() for async subprocess
  - Streams stdout line-by-line
  - Collects stderr for error reporting
  - Implements timeout with graceful shutdown
```

### Message Flow Architecture

```
1. User Input
   ↓
2. CLI/API Entry (cli.py / __init__.py)
   ↓
3. CodexClient.query() (client.py)
   ↓
4. CodexTransport.send_query() (transport.py)
   ↓
5. Subprocess execution (anyio)
   ↓
6. JSON line parsing
   ↓
7. CodexMessage creation (types.py)
   ↓
8. to_claif_message() conversion
   ↓
9. Yield Message to caller
```

### Error Handling Strategy

1. **Transport Errors**: Wrapped in TransportError
2. **Timeout Errors**: Process terminated, TimeoutError raised
3. **Parse Errors**: Logged and skipped (resilient parsing)
4. **CLI Not Found**: Clear error message with installation hint
5. **Result Errors**: Propagated from Codex CLI response

## Development Principles for`claif_cod`

### Code Style Guidelines

1. **Async-First Design**
   - All I/O operations use async/await
   - anyio for cross-platform async compatibility
   - Async generators for streaming responses

2. **Type Safety**
   - Comprehensive type hints on all functions
   - Dataclasses for structured data
   - Union types for flexibility (e.g., `str | None`)

3. **Error Handling**
   - Graceful degradation over hard failures
   - Detailed error messages for debugging
   - Timeout protection on all subprocess operations

4. **Logging Strategy**
   - loguru for structured logging
   - Debug logs for transport operations
   - Error logs for failures only
   - No info/warning spam

### Testing Approach

```python
# Current test coverage is minimal
# Focus areas for expansion:
1. Transport layer subprocess mocking
2. Message parsing edge cases
3. CLI command generation
4. Error handling scenarios
5. Platform-specific path discovery
```

### Configuration Management

```python
# Environment variables:
CODEX_CLI_PATH      # Path to Codex CLI binary
CODEX_DEFAULT_MODEL # Default model name
CODEX_ACTION_MODE   # Default action mode
CODEX_TIMEOUT       # Default timeout seconds

# Config file (~/.claif/config.toml):
[providers.codex]
enabled = true
cli_path = "/path/to/codex-cli"
default_model = "o4-mini"
timeout = 180
```

### Common Development Tasks

#### Adding a New CLI Command

1. Add method to `CodexCLI` class in `cli.py`
2. Use Fire conventions (underscores become hyphens)
3. Add rich formatting for output
4. Update README.md with example

```python
def new_command(self, arg1: str, arg2: int = 10) -> None:
    """Description for --help output."""
    # Implementation
```

#### Adding a New Option

1. Add field to `CodexOptions` dataclass in `types.py`
2. Update `_build_command()` in `transport.py`
3. Add CLI parameter in `cli.py`
4. Update option conversion in `__init__.py`

#### Handling New Message Types

1. Add new block type in `types.py` (inherit from `ContentBlock`)
2. Update `_parse_output_line()` in `transport.py`
3. Add conversion logic in `to_claif_message()`
4. Test with mock JSON responses

### Debugging Tips

1. **Enable verbose mode**: `--verbose` flag shows all transport operations
2. **Check CLI path**: `claif-cod health` verifies CLI discovery
3. **Test subprocess**: Run Codex CLI directly to verify behavior
4. **Mock responses**: Use test fixtures for JSON message testing
5. **Async debugging**: Use `asyncio.run(main(), debug=True)`

### Performance Considerations

- Subprocess spawn time is the main bottleneck
- JSON parsing is negligible compared to I/O
- Streaming prevents memory issues with large responses
- anyio provides optimal platform-specific async implementation

## Implementation Checklist

### Completed Features ✅












### Pending Features ⚠️

- [ ] Comprehensive test suite
- [ ] Configuration file support
- [ ] Retry logic for transient failures
- [ ] Response caching mechanism
- [ ] Session state management
- [ ] Progress callbacks for long operations
- [ ] Structured diff output for code changes
- [ ] Integration tests with mock CLI
- [ ] Performance benchmarks
- [ ] API documentation generation

## Testing Strategy for`claif_cod`

### Unit Test Structure

```python
# tests/test_transport.py
- Test CLI path discovery logic
- Test command building with various options
- Test JSON parsing with edge cases
- Test timeout handling

# tests/test_client.py
- Test message conversion
- Test error propagation
- Test connection lifecycle

# tests/test_cli.py
- Test command parsing
- Test output formatting
- Test error display
```

### Integration Test Approach

```python
# Mock Codex CLI subprocess
class MockCodexCLI:
    def __init__(self, responses):
        self.responses = responses
    
    async def run(self):
        for response in self.responses:
            print(json.dumps(response))
            await asyncio.sleep(0.1)
```

### Test Data Examples

```json
// Success response
{
  "message_type": "content",
  "content": [{"type": "text", "text": "Generated code"}]
}

// Error response
{
  "message_type": "result",
  "error": true,
  "message": "Model not available"
}
```

## Future Enhancements

### Short Term (v1.x)

1. **Complete test coverage** (target: >80%)
2. **Configuration file support** viaClaif config system
3. **Better error messages** with actionable hints
4. **Mock CLI for testing** without real Codex binary
5. **Documentation site** with API reference

### Medium Term (v2.x)

1. **Session management** for multi-turn conversations
2. **Response caching** to avoid duplicate queries
3. **Diff visualization** for code changes
4. **Plugin system** for custom processors
5. **Metrics collection** for usage analytics

### Long Term (v3.x)

1. **Native API integration** (skip CLI wrapper)
2. **Streaming optimizations** for faster response
3. **Multi-model routing** based on task type
4. **Collaborative features** for team usage
5. **IDE integrations** via language servers

## Maintenance Notes

- Keep dependency on `claif.common` minimal
- Maintain backward compatibility with CLI changes
- Document all breaking changes in CHANGELOG.md
- Run full test suite before releases
- Update README examples with each feature

## Contact

For questions about this codebase:
- GitHub Issues: https://github.com/twardoch/claif_cod/issues
-Claif Framework: https://github.com/twardoch/claif