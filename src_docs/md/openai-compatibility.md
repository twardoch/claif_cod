# OpenAI Compatibility

`claif_cod` provides full compatibility with the OpenAI Python client API, making it a seamless drop-in replacement.

## Drop-in Replacement

### Basic Replacement

```python
# Instead of this:
# from openai import OpenAI
# client = OpenAI()

# Use this:
from claif_cod import CodexClient as OpenAI
client = OpenAI()

# Everything else works exactly the same
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Import Aliasing

```python
# Option 1: Direct replacement
from claif_cod import CodexClient as OpenAI

# Option 2: Explicit import
from claif_cod import CodexClient
client = CodexClient()

# Option 3: Conditional import
try:
    from claif_cod import CodexClient as OpenAI
except ImportError:
    from openai import OpenAI

client = OpenAI()
```

## API Compatibility

### Chat Completions

`claif_cod` implements the complete OpenAI Chat Completions API:

```python
from claif_cod import CodexClient

client = CodexClient()

# All OpenAI parameters are supported
response = client.chat.completions.create(
    model="gpt-4o",                    # Model selection
    messages=[                         # Message format
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,                   # Creativity control
    max_tokens=1000,                   # Response length
    top_p=1.0,                        # Nucleus sampling
    frequency_penalty=0.0,             # Repetition penalty
    presence_penalty=0.0,              # Topic diversity
    stop=None,                        # Stop sequences
    stream=False,                     # Streaming mode
    n=1,                              # Number of responses
    logit_bias={},                    # Token bias
    user="user123"                    # User identifier
)

# Response format matches OpenAI exactly
print(response.choices[0].message.content)
print(response.model)
print(response.usage.total_tokens)
```

### Streaming Support

```python
# Streaming works identically to OpenAI
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
    max_tokens=1500
)

# Process chunks exactly like OpenAI
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### Response Objects

Response objects match OpenAI's structure exactly:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# ChatCompletion object
print(type(response))  # <class 'openai.types.chat.chat_completion.ChatCompletion'>

# All fields available
print(response.id)                    # Completion ID
print(response.object)                # "chat.completion"
print(response.created)               # Unix timestamp
print(response.model)                 # Model used
print(response.choices[0].index)      # Choice index
print(response.choices[0].message.role)     # "assistant"
print(response.choices[0].message.content)  # Response content
print(response.choices[0].finish_reason)    # "stop", "length", etc.
print(response.usage.prompt_tokens)   # Input tokens
print(response.usage.completion_tokens)     # Output tokens  
print(response.usage.total_tokens)    # Total tokens
```

### Multiple Choices

```python
# Generate multiple responses (n > 1)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a haiku"}],
    n=3,
    temperature=0.9
)

# Access all choices
for i, choice in enumerate(response.choices):
    print(f"\nChoice {i+1}:")
    print(choice.message.content)
    print(f"Finish reason: {choice.finish_reason}")
```

## Model Mapping

### Model Name Translation

`claif_cod` automatically maps OpenAI model names to Codex equivalents:

```python
# OpenAI model names work directly
response = client.chat.completions.create(
    model="gpt-4o",           # Maps to o4
    messages=[{"role": "user", "content": "Hello"}]
)

response = client.chat.completions.create(
    model="gpt-4o-mini",      # Maps to o4-mini
    messages=[{"role": "user", "content": "Hello"}]
)

response = client.chat.completions.create(
    model="o1-preview",       # Maps to o4-preview
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Model Compatibility Table

| OpenAI Model | Codex Equivalent | Description |
|--------------|------------------|-------------|
| `gpt-4o` | `o4` | Main GPT-4 model |
| `gpt-4o-mini` | `o4-mini` | Smaller, faster model |
| `gpt-4o-preview` | `o4-preview` | Latest preview model |
| `o1-preview` | `o4-preview` | Reasoning model |
| `gpt-3.5-turbo` | `o3.5` | Previous generation |

### Custom Model Names

```python
# Use Codex-specific model names directly
response = client.chat.completions.create(
    model="o4-mini",          # Native Codex model name
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Migration Guide

### From OpenAI Client

#### Basic Migration

```python
# Before (OpenAI)
from openai import OpenAI

client = OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# After (claif_cod)
from claif_cod import CodexClient

client = CodexClient(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4o",  # Updated model name
    messages=[{"role": "user", "content": "Hello"}]
)
```

#### Configuration Migration

```python
# Before (OpenAI)
client = OpenAI(
    api_key="your-key",
    base_url="https://api.openai.com/v1",
    timeout=60.0,
    max_retries=2
)

# After (claif_cod)
client = CodexClient(
    api_key="your-key",
    # base_url not needed (uses Codex CLI)
    timeout=60,
    # max_retries handled by Codex CLI
    
    # Additional claif_cod options
    codex_path="/usr/local/bin/codex",
    sandbox_mode="workspace-write",
    approval_policy="on-failure"
)
```

### Handling Differences

#### Unsupported Features

Some OpenAI-specific features are not available:

```python
# These parameters are ignored or raise warnings:
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    
    # Unsupported (ignored with warning)
    logit_bias={"token_id": 0.5},      # Token bias not supported
    tools=[{"type": "function"}],       # Function calling different
    tool_choice="auto",                # Tool choice different
    response_format={"type": "json"},   # Response format different
)
```

#### Enhanced Features

`claif_cod` adds features not available in OpenAI:

```python
# claif_cod-specific enhancements
client = CodexClient(
    sandbox_mode="workspace-write",     # File system control
    approval_policy="on-failure",      # Interactive approval
    working_dir="./project",           # Project context
    codex_path="/custom/path/codex"    # CLI path control
)

# Additional metadata in responses
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# Access claif_cod-specific metadata
if hasattr(response, 'codex_metadata'):
    print(f"CLI version: {response.codex_metadata.cli_version}")
    print(f"Execution time: {response.codex_metadata.execution_time}")
```

## Error Compatibility

### Exception Mapping

`claif_cod` maps its errors to OpenAI exception types:

```python
from openai import (
    OpenAIError,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError
)

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
except RateLimitError as e:
    print("Rate limit exceeded")
    
except APITimeoutError as e:
    print("Request timed out")
    
except APIConnectionError as e:
    print("Connection failed")
    
except APIError as e:
    print(f"API error: {e.status_code}")
    
except OpenAIError as e:
    print(f"General OpenAI error: {e}")
```

### Error Code Mapping

| Codex CLI Error | OpenAI Exception | Description |
|-----------------|------------------|-------------|
| CLI not found | `APIConnectionError` | Cannot connect to service |
| Invalid model | `APIError` (400) | Invalid request parameter |
| Rate limited | `RateLimitError` (429) | Too many requests |
| Timeout | `APITimeoutError` | Request timeout |
| Auth failed | `APIError` (401) | Authentication failure |

## Testing Compatibility

### Unit Test Migration

```python
# Before (OpenAI mocking)
import unittest
from unittest.mock import patch, MagicMock
from openai import OpenAI

class TestOpenAI(unittest.TestCase):
    @patch('openai.OpenAI.chat.completions.create')
    def test_completion(self, mock_create):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello"
        mock_create.return_value = mock_response
        
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        self.assertEqual(response.choices[0].message.content, "Hello")

# After (claif_cod mocking)
import unittest
from unittest.mock import patch, MagicMock
from claif_cod import CodexClient

class TestCodexClient(unittest.TestCase):
    @patch('claif_cod.client.subprocess.run')
    def test_completion(self, mock_run):
        # Mock Codex CLI subprocess
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"choices": [{"message": {"content": "Hello"}}]}',
            stderr=""
        )
        
        client = CodexClient()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        self.assertEqual(response.choices[0].message.content, "Hello")
```

### Integration Testing

```python
import pytest
from claif_cod import CodexClient
from openai import OpenAI

@pytest.fixture(params=[CodexClient, OpenAI])
def client(request):
    """Test both OpenAI and claif_cod clients."""
    return request.param()

def test_completion_compatibility(client):
    """Test that both clients return compatible responses."""
    response = client.chat.completions.create(
        model="gpt-4o" if isinstance(client, CodexClient) else "gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    
    # Both should have same response structure
    assert hasattr(response, 'choices')
    assert len(response.choices) > 0
    assert hasattr(response.choices[0], 'message')
    assert hasattr(response.choices[0].message, 'content')
    assert hasattr(response, 'usage')
```

## Deployment Considerations

### Environment Variables

```bash
# OpenAI environment variables work unchanged
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Ignored by claif_cod

# Additional claif_cod variables
export CODEX_CLI_PATH="/usr/local/bin/codex"
export CODEX_DEFAULT_MODEL="o4-mini"
export CODEX_SANDBOX_MODE="workspace-write"
```

### Docker Migration

```dockerfile
# Before (OpenAI only)
FROM python:3.11
RUN pip install openai
ENV OPENAI_API_KEY="your-key"

# After (claif_cod)
FROM python:3.11

# Install Rust and Codex CLI
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cargo install codex

# Install claif_cod
RUN pip install claif_cod

# Environment variables
ENV OPENAI_API_KEY="your-key"
ENV CODEX_CLI_PATH="/root/.cargo/bin/codex"
```

### Configuration Migration

```python
# Utility function for seamless migration
def get_ai_client():
    """Get AI client with fallback support."""
    try:
        from claif_cod import CodexClient
        return CodexClient()
    except ImportError:
        from openai import OpenAI
        return OpenAI()

# Usage
client = get_ai_client()
response = client.chat.completions.create(
    model="gpt-4o",  # Works with both
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Performance Comparison

### Speed Differences

```python
import time
from claif_cod import CodexClient
from openai import OpenAI

def benchmark_clients():
    codex_client = CodexClient()
    openai_client = OpenAI()
    
    prompt = "Write a simple Python function"
    
    # Benchmark claif_cod
    start = time.time()
    codex_response = codex_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    codex_time = time.time() - start
    
    # Benchmark OpenAI
    start = time.time()
    openai_response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    openai_time = time.time() - start
    
    print(f"claif_cod time: {codex_time:.2f}s")
    print(f"OpenAI time: {openai_time:.2f}s")
    
    return codex_time, openai_time
```

### Resource Usage

- **claif_cod**: Uses subprocess overhead but local CLI caching
- **OpenAI**: Direct HTTP requests but network latency
- **Memory**: claif_cod uses slightly more memory for subprocess management
- **Latency**: claif_cod may have lower latency with local CLI optimizations

---

*Next: Explore the [Architecture](architecture.md) to understand how everything works under the hood.*