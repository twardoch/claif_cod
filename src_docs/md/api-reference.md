# API Reference

Complete API documentation for all classes, methods, and functions in `claif_cod`.

## Core Classes

### CodexClient

Main client class implementing the OpenAI Chat Completions API.

```python
class CodexClient:
    """OpenAI-compatible client for Codex CLI."""
```

#### Constructor

```python
def __init__(
    self,
    api_key: str | None = None,
    codex_path: str | None = None,
    working_dir: str | Path | None = None,
    model: str | None = None,
    sandbox_mode: str | None = None,
    approval_policy: str | None = None,
    timeout: int | None = None,
    **kwargs
)
```

**Parameters:**

- `api_key` (str, optional): OpenAI API key. Defaults to `OPENAI_API_KEY` environment variable.
- `codex_path` (str, optional): Path to Codex CLI binary. Auto-discovered if not provided.
- `working_dir` (str | Path, optional): Working directory for Codex operations.
- `model` (str, optional): Default model to use. Defaults to "o4-mini".
- `sandbox_mode` (str, optional): Sandbox policy. One of "read-only", "workspace-write", "danger-full-access".
- `approval_policy` (str, optional): Approval policy. One of "untrusted", "on-failure", "never".
- `timeout` (int, optional): Request timeout in seconds. Defaults to 180.

**Example:**

```python
from claif_cod import CodexClient

# Basic initialization
client = CodexClient()

# Full configuration
client = CodexClient(
    api_key="your-api-key",
    codex_path="/usr/local/bin/codex",
    working_dir="./my-project",
    model="o4",
    sandbox_mode="workspace-write",
    approval_policy="on-failure",
    timeout=300
)
```

#### Methods

##### chat.completions.create()

```python
def create(
    self,
    messages: list[dict[str, str]],
    model: str = "o4-mini",
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    stop: str | list[str] | None = None,
    stream: bool = False,
    n: int = 1,
    timeout: int | None = None,
    **kwargs
) -> ChatCompletion | Iterator[ChatCompletionChunk]
```

Create a chat completion using the OpenAI-compatible API.

**Parameters:**

- `messages` (list[dict]): List of message dictionaries with "role" and "content" keys.
- `model` (str): Model to use. Defaults to "o4-mini".
- `temperature` (float, optional): Creativity level (0.0-2.0). 
- `max_tokens` (int, optional): Maximum response length.
- `top_p` (float, optional): Nucleus sampling parameter.
- `frequency_penalty` (float, optional): Frequency penalty (-2.0 to 2.0).
- `presence_penalty` (float, optional): Presence penalty (-2.0 to 2.0).
- `stop` (str | list[str], optional): Stop sequences.
- `stream` (bool): Enable streaming responses. Defaults to False.
- `n` (int): Number of responses to generate. Defaults to 1.
- `timeout` (int, optional): Request timeout in seconds.

**Returns:**

- `ChatCompletion` if `stream=False`
- `Iterator[ChatCompletionChunk]` if `stream=True`

**Raises:**

- `APIError`: Invalid request parameters or API error
- `APIConnectionError`: Cannot connect to Codex CLI
- `APITimeoutError`: Request timeout
- `RateLimitError`: Rate limit exceeded

**Example:**

```python
# Basic completion
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Write a Python function"}
    ],
    model="o4-mini"
)

print(response.choices[0].message.content)

# Streaming completion
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Tell me a story"}],
    model="o4",
    stream=True,
    max_tokens=1500
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

##### models.list()

```python
def list(self) -> list[Model]
```

List available models.

**Returns:**

- `list[Model]`: List of available model objects.

**Example:**

```python
models = client.models.list()
for model in models:
    print(f"Model: {model.id}")
```

### AsyncCodexClient

Async version of CodexClient for async/await usage.

```python
class AsyncCodexClient:
    """Async OpenAI-compatible client for Codex CLI."""
```

All methods are identical to `CodexClient` but return coroutines:

```python
async def create(self, ...) -> ChatCompletion | AsyncIterator[ChatCompletionChunk]
async def list(self) -> list[Model]
```

**Example:**

```python
import asyncio
from claif_cod import AsyncCodexClient

async def main():
    client = AsyncCodexClient()
    
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
    
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Data Classes

### CodexOptions

Configuration options for Codex requests.

```python
@dataclass
class CodexOptions:
    """Configuration for Codex CLI requests."""
    
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: str | list[str] | None = None
    system_prompt: str | None = None
    working_dir: Path | None = None
    sandbox_mode: str | None = None
    approval_policy: str | None = None
    timeout: int | None = None
    auto_approve_everything: bool = False
```

**Example:**

```python
from claif_cod.types import CodexOptions
from pathlib import Path

options = CodexOptions(
    model="o4",
    temperature=0.2,
    max_tokens=2000,
    working_dir=Path("./project"),
    sandbox_mode="workspace-write",
    approval_policy="on-failure"
)
```

### CodexMessage

Internal message format used by the transport layer.

```python
@dataclass
class CodexMessage:
    """Internal message format from Codex CLI."""
    
    message_type: str
    content: list[ContentBlock]
    metadata: dict[str, Any] | None = None
    
    def to_openai_format(self) -> ChatCompletion:
        """Convert to OpenAI ChatCompletion format."""
```

### Content Blocks

Base class and implementations for different content types.

#### ContentBlock

```python
@dataclass
class ContentBlock:
    """Base class for content blocks."""
    
    type: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
```

#### TextBlock

```python
@dataclass
class TextBlock(ContentBlock):
    """Text content block."""
    
    text: str
    language: str | None = None
    
    def __post_init__(self):
        self.type = "text"
```

#### CodeBlock

```python
@dataclass  
class CodeBlock(ContentBlock):
    """Code content block."""
    
    code: str
    language: str
    file_path: str | None = None
    
    def __post_init__(self):
        self.type = "code"
```

#### ErrorBlock

```python
@dataclass
class ErrorBlock(ContentBlock):
    """Error content block."""
    
    error: str
    error_type: str = "unknown"
    
    def __post_init__(self):
        self.type = "error"
```

## Transport Layer

### CodexTransport

Low-level transport for communicating with Codex CLI.

```python
class CodexTransport:
    """Manages subprocess communication with Codex CLI."""
```

#### Constructor

```python
def __init__(
    self,
    cli_path: str | None = None,
    timeout: int | None = None,
    **kwargs
)
```

**Parameters:**

- `cli_path` (str, optional): Path to Codex CLI binary.
- `timeout` (int, optional): Default timeout in seconds.

#### Methods

##### send_query()

```python
async def send_query(
    self,
    prompt: str,
    options: CodexOptions
) -> AsyncIterator[CodexMessage]
```

Send query to Codex CLI and stream responses.

**Parameters:**

- `prompt` (str): Query prompt.
- `options` (CodexOptions): Request configuration.

**Yields:**

- `CodexMessage`: Streaming messages from Codex CLI.

**Raises:**

- `TransportError`: CLI communication error
- `TimeoutError`: Request timeout
- `ProcessError`: CLI process error

**Example:**

```python
from claif_cod.transport import CodexTransport
from claif_cod.types import CodexOptions

async def transport_example():
    transport = CodexTransport(timeout=300)
    options = CodexOptions(model="o4-mini")
    
    async for message in transport.send_query("Hello", options):
        print(f"Message type: {message.message_type}")
        for block in message.content:
            print(f"Content: {block}")
```

##### find_cli_path()

```python
def find_cli_path(self) -> str
```

Discover Codex CLI binary path.

**Returns:**

- `str`: Path to Codex CLI binary.

**Raises:**

- `FileNotFoundError`: CLI not found.

## CLI Module

### CLI

Fire-based command-line interface.

```python
class CLI:
    """Command-line interface for claif_cod."""
```

#### Constructor

```python
def __init__(
    self,
    codex_path: str | None = None,
    working_dir: str | None = None,
    model: str | None = None,
    sandbox: str | None = None,
    approval: str | None = None,
)
```

#### Methods

##### query()

```python
def query(
    self,
    prompt: str,
    model: str = "o4-mini",
    stream: bool = False,
    format: str = "text",
    working_dir: str | None = None,
    sandbox: str | None = None,
    approval: str | None = None,
    timeout: int | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    verbose: bool = False,
    **kwargs
) -> None
```

Execute a single query.

**Parameters:**

- `prompt` (str): Query prompt.
- `model` (str): Model to use.
- `stream` (bool): Enable streaming output.
- `format` (str): Output format ("text", "json", "code", "raw").
- `working_dir` (str, optional): Working directory.
- `sandbox` (str, optional): Sandbox mode.
- `approval` (str, optional): Approval policy.
- `timeout` (int, optional): Request timeout.
- `temperature` (float, optional): Temperature setting.
- `max_tokens` (int, optional): Max tokens.
- `verbose` (bool): Enable verbose output.

##### stream()

```python
def stream(
    self,
    prompt: str,
    model: str = "o4-mini",
    **kwargs
) -> None
```

Stream response in real-time.

##### chat()

```python
def chat(
    self,
    model: str = "o4-mini",
    system: str | None = None,
    **kwargs
) -> None
```

Start interactive chat mode.

##### health()

```python
def health(
    self,
    verbose: bool = False,
    check_cli: bool = True,
    check_api: bool = True,
    check_config: bool = True,
) -> None
```

Check system health.

##### models()

```python
def models(
    self,
    detailed: bool = False,
) -> None
```

List available models.

##### config()

```python
def config(
    self,
    action: str = "show",
    format: str = "text",
    file: str | None = None,
    **kwargs
) -> None
```

Manage configuration.

**Parameters:**

- `action` (str): Action ("show", "set", "save", "load", "reset").
- `format` (str): Output format for "show" action.
- `file` (str, optional): Config file path for "save"/"load".

## Utility Functions

### query()

High-level function for simple queries.

```python
async def query(
    prompt: str,
    options: CodexOptions | None = None
) -> AsyncIterator[Message]
```

**Parameters:**

- `prompt` (str): Query prompt.
- `options` (CodexOptions, optional): Request options.

**Yields:**

- `Message`: Claif-format messages.

**Example:**

```python
import asyncio
from claif_cod import query, CodexOptions

async def simple_query():
    options = CodexOptions(model="o4-mini", temperature=0.2)
    
    async for message in query("Write a function", options):
        print(message.content)

asyncio.run(simple_query())
```

## Exception Classes

### Base Exceptions

All exceptions inherit from OpenAI exception classes for compatibility.

#### OpenAIError

```python
class OpenAIError(Exception):
    """Base exception for all OpenAI-related errors."""
```

#### APIError

```python
class APIError(OpenAIError):
    """API-related errors."""
    
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
```

#### APIConnectionError

```python
class APIConnectionError(OpenAIError):
    """Connection-related errors."""
```

#### APITimeoutError

```python
class APITimeoutError(OpenAIError):
    """Timeout-related errors."""
```

#### RateLimitError

```python
class RateLimitError(APIError):
    """Rate limit errors."""
```

### Transport Exceptions

#### TransportError

```python
class TransportError(OpenAIError):
    """Transport layer errors."""
```

#### ProcessError

```python
class ProcessError(TransportError):
    """Subprocess execution errors."""
```

## Response Objects

The package uses OpenAI's response objects directly for compatibility:

### ChatCompletion

```python
from openai.types.chat import ChatCompletion

# Response structure:
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "o4-mini",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "Generated response"
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}
```

### ChatCompletionChunk

```python
from openai.types.chat import ChatCompletionChunk

# Streaming chunk structure:
{
    "id": "chatcmpl-123", 
    "object": "chat.completion.chunk",
    "created": 1677652288,
    "model": "o4-mini",
    "choices": [{
        "index": 0,
        "delta": {
            "role": "assistant",  # Only in first chunk
            "content": "partial content"
        },
        "finish_reason": null
    }]
}
```

## Constants

### Model Names

```python
AVAILABLE_MODELS = {
    "o4-mini": "Fast, efficient model",
    "o4": "Balanced performance", 
    "o4-preview": "Latest features",
    "o3.5": "Previous generation"
}

# OpenAI model mapping
OPENAI_MODEL_MAPPING = {
    "gpt-4o": "o4",
    "gpt-4o-mini": "o4-mini",
    "gpt-4o-preview": "o4-preview", 
    "o1-preview": "o4-preview",
    "gpt-3.5-turbo": "o3.5"
}
```

### Sandbox Modes

```python
SANDBOX_MODES = {
    "read-only": "Can only read files",
    "workspace-write": "Can write within working directory", 
    "danger-full-access": "Full system access"
}
```

### Approval Policies

```python
APPROVAL_POLICIES = {
    "untrusted": "Require approval for all actions",
    "on-failure": "Only ask when operations fail",
    "never": "Auto-approve everything"
}
```

---

*This completes the comprehensive API reference. For usage examples and tutorials, see the other documentation sections.*