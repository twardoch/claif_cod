# Python API

Complete guide to using `claif_cod` in your Python applications.

## CodexClient Class

The main interface for interacting with Codex through Python.

### Basic Usage

```python
from claif_cod import CodexClient

# Initialize with defaults
client = CodexClient()

# Initialize with custom settings
client = CodexClient(
    api_key="your-api-key",           # OpenAI API key
    codex_path="/path/to/codex",      # Path to Codex CLI
    working_dir="./project",          # Working directory
    model="o4-mini",                  # Default model
    sandbox_mode="workspace-write",    # Sandbox policy
    approval_policy="on-failure",     # Approval policy
    timeout=300                       # Timeout in seconds
)
```

### Chat Completions API

`claif_cod` implements the OpenAI Chat Completions API for seamless compatibility.

#### Synchronous Requests

```python
from claif_cod import CodexClient

client = CodexClient()

# Basic completion
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to sort a list"}
    ],
    model="o4-mini"
)

# Access the response
print(response.choices[0].message.content)
print(f"Model used: {response.model}")
print(f"Usage: {response.usage}")
```

#### Advanced Parameters

```python
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Optimize this algorithm"}
    ],
    model="o4",
    temperature=0.2,        # Creativity level (0.0-2.0)
    max_tokens=2000,        # Maximum response length
    top_p=0.9,             # Nucleus sampling
    frequency_penalty=0.0,  # Reduce repetition
    presence_penalty=0.0,   # Encourage new topics
    stop=["END", "STOP"],  # Stop sequences
    timeout=600            # Request timeout
)
```

#### Streaming Responses

```python
# Enable streaming for real-time responses
stream = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Explain neural networks step by step"}
    ],
    model="o4-mini",
    stream=True,
    max_tokens=1500
)

# Process chunks as they arrive
full_response = ""
for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        full_response += content
        print(content, end="", flush=True)

print(f"\n\nFull response received: {len(full_response)} characters")
```

#### Multiple Choices

```python
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Write a function to calculate fibonacci"}
    ],
    model="o4-mini",
    n=3,  # Generate 3 different responses
    temperature=0.8
)

# Access all choices
for i, choice in enumerate(response.choices):
    print(f"\nOption {i+1}:")
    print(choice.message.content)
    print(f"Finish reason: {choice.finish_reason}")
```

## Working with Messages

### Message Format

```python
# System message (sets behavior)
system_message = {
    "role": "system",
    "content": "You are an expert Python developer focused on clean, efficient code."
}

# User message (your request)
user_message = {
    "role": "user", 
    "content": "Create a class for managing user sessions"
}

# Assistant message (previous AI response)
assistant_message = {
    "role": "assistant",
    "content": "Here's a session management class..."
}

# Complete conversation
messages = [system_message, user_message, assistant_message, {
    "role": "user",
    "content": "Add authentication to this class"
}]
```

### Multi-turn Conversations

```python
from claif_cod import CodexClient

client = CodexClient()
conversation = []

def add_message(role, content):
    conversation.append({"role": role, "content": content})

def chat(user_input):
    add_message("user", user_input)
    
    response = client.chat.completions.create(
        messages=conversation,
        model="o4-mini"
    )
    
    assistant_response = response.choices[0].message.content
    add_message("assistant", assistant_response)
    
    return assistant_response

# Start conversation
add_message("system", "You are a helpful coding assistant.")

# Multi-turn interaction
response1 = chat("Write a class for a todo list")
print("AI:", response1)

response2 = chat("Add a method to mark items as completed")
print("AI:", response2)

response3 = chat("Add unit tests for this class")
print("AI:", response3)
```

## Async Operations

### Async Client

```python
import asyncio
from claif_cod import AsyncCodexClient

async def async_example():
    client = AsyncCodexClient()
    
    # Async completion
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
    
    print(response.choices[0].message.content)

# Run async function
asyncio.run(async_example())
```

### Async Streaming

```python
import asyncio
from claif_cod import AsyncCodexClient

async def async_streaming():
    client = AsyncCodexClient()
    
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Explain async programming"}],
        model="o4-mini",
        stream=True
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

asyncio.run(async_streaming())
```

### Concurrent Requests

```python
import asyncio
from claif_cod import AsyncCodexClient

async def concurrent_requests():
    client = AsyncCodexClient()
    
    # Define multiple tasks
    tasks = [
        client.chat.completions.create(
            messages=[{"role": "user", "content": f"Write a {lang} hello world"}],
            model="o4-mini"
        )
        for lang in ["Python", "JavaScript", "Go", "Rust"]
    ]
    
    # Execute concurrently
    responses = await asyncio.gather(*tasks)
    
    # Process results
    for i, response in enumerate(responses):
        lang = ["Python", "JavaScript", "Go", "Rust"][i]
        print(f"\n{lang}:")
        print(response.choices[0].message.content)

asyncio.run(concurrent_requests())
```

## Error Handling

### Exception Types

```python
from claif_cod import CodexClient
from openai import (
    OpenAIError,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError
)

client = CodexClient()

try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
    
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement backoff strategy
    
except APITimeoutError as e:
    print(f"Request timed out: {e}")
    # Retry with longer timeout
    
except APIConnectionError as e:
    print(f"Connection error: {e}")
    # Check network connectivity
    
except APIError as e:
    print(f"API error: {e}")
    # Handle API-specific errors
    
except OpenAIError as e:
    print(f"OpenAI error: {e}")
    # Handle any OpenAI-related error
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected errors
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from claif_cod import CodexClient
from openai import RateLimitError, APITimeoutError

client = CodexClient()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=lambda retry_state: isinstance(retry_state.outcome.exception(), (RateLimitError, APITimeoutError))
)
def robust_request(messages, **kwargs):
    return client.chat.completions.create(
        messages=messages,
        **kwargs
    )

# Use with retry logic
try:
    response = robust_request(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Failed after retries: {e}")
```

### Graceful Degradation

```python
from claif_cod import CodexClient
from openai import OpenAIError

def safe_code_generation(prompt, fallback_response="# Code generation unavailable"):
    client = CodexClient()
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="o4-mini",
            timeout=30  # Short timeout for quick fallback
        )
        return response.choices[0].message.content
        
    except OpenAIError as e:
        print(f"AI service unavailable: {e}")
        return fallback_response
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return fallback_response

# Usage
code = safe_code_generation("Write a fibonacci function")
print(code)
```

## Advanced Usage Patterns

### Context Management

```python
from claif_cod import CodexClient
from contextlib import contextmanager

@contextmanager
def codex_session(working_dir=None, **kwargs):
    """Context manager for Codex sessions."""
    client = CodexClient(working_dir=working_dir, **kwargs)
    try:
        yield client
    finally:
        # Cleanup if needed
        pass

# Usage
with codex_session(working_dir="./my-project", sandbox_mode="workspace-write") as client:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Refactor this module"}],
        model="o4"
    )
    print(response.choices[0].message.content)
```

### Response Processing

```python
from claif_cod import CodexClient
import re

client = CodexClient()

def extract_code_blocks(response):
    """Extract code blocks from response."""
    content = response.choices[0].message.content
    
    # Find all code blocks
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
    
    return [
        {
            'language': lang or 'text',
            'code': code.strip()
        }
        for lang, code in code_blocks
    ]

# Usage
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Write Python and JavaScript functions"}],
    model="o4-mini"
)

code_blocks = extract_code_blocks(response)
for block in code_blocks:
    print(f"Language: {block['language']}")
    print(f"Code:\n{block['code']}\n")
```

### Custom Response Processing

```python
from claif_cod import CodexClient
from typing import List, Dict, Any

class CodexProcessor:
    def __init__(self, **client_kwargs):
        self.client = CodexClient(**client_kwargs)
    
    def generate_with_metadata(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response with additional metadata."""
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        choice = response.choices[0]
        return {
            'content': choice.message.content,
            'model': response.model,
            'usage': response.usage.dict() if response.usage else {},
            'finish_reason': choice.finish_reason,
            'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
            'completion_tokens': response.usage.completion_tokens if response.usage else 0,
            'total_tokens': response.usage.total_tokens if response.usage else 0
        }
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Generate responses for multiple prompts."""
        return [
            self.generate_with_metadata(prompt, **kwargs)
            for prompt in prompts
        ]

# Usage
processor = CodexProcessor(model="o4-mini")

prompts = [
    "Write a Python function to sort a list",
    "Create a React component for a button", 
    "Write SQL to find duplicate records"
]

results = processor.batch_generate(prompts)
for i, result in enumerate(results):
    print(f"Prompt {i+1}:")
    print(f"Tokens used: {result['total_tokens']}")
    print(f"Content: {result['content'][:100]}...")
    print()
```

## Integration Patterns

### Flask Integration

```python
from flask import Flask, request, jsonify
from claif_cod import CodexClient

app = Flask(__name__)
client = CodexClient()

@app.route('/generate', methods=['POST'])
def generate_code():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model', 'o4-mini')
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        
        return jsonify({
            'success': True,
            'content': response.choices[0].message.content,
            'usage': response.usage.dict() if response.usage else {}
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claif_cod import CodexClient
from typing import Optional

app = FastAPI(title="Codex API")
client = CodexClient()

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = "o4-mini"
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1000

class GenerateResponse(BaseModel):
    content: str
    model: str
    usage: dict

@app.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": request.prompt}],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return GenerateResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=response.usage.dict() if response.usage else {}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    models = client.models.list()
    return {"models": [model.id for model in models]}
```

## Testing

### Unit Testing

```python
import unittest
from unittest.mock import patch, MagicMock
from claif_cod import CodexClient

class TestCodexClient(unittest.TestCase):
    
    @patch('claif_cod.client.subprocess.run')
    def test_basic_completion(self, mock_run):
        # Mock subprocess response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"content": "Generated code"}',
            stderr=""
        )
        
        client = CodexClient()
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Test"}],
            model="o4-mini"
        )
        
        self.assertIsNotNone(response)
        self.assertEqual(len(response.choices), 1)
    
    def test_error_handling(self):
        with patch('claif_cod.client.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("CLI error")
            
            client = CodexClient()
            
            with self.assertRaises(Exception):
                client.chat.completions.create(
                    messages=[{"role": "user", "content": "Test"}],
                    model="o4-mini"
                )

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```python
import pytest
from claif_cod import CodexClient

@pytest.fixture
def client():
    return CodexClient()

def test_health_check(client):
    """Test that the client can connect to Codex."""
    # This test requires actual Codex CLI
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="o4-mini",
            max_tokens=10
        )
        assert response is not None
        assert len(response.choices) > 0
    except Exception as e:
        pytest.skip(f"Codex CLI not available: {e}")

def test_streaming(client):
    """Test streaming responses."""
    try:
        stream = client.chat.completions.create(
            messages=[{"role": "user", "content": "Count to 3"}],
            model="o4-mini",
            stream=True,
            max_tokens=50
        )
        
        chunks = list(stream)
        assert len(chunks) > 0
        
        # Verify chunk structure
        for chunk in chunks:
            assert hasattr(chunk, 'choices')
            if chunk.choices:
                assert hasattr(chunk.choices[0], 'delta')
                
    except Exception as e:
        pytest.skip(f"Codex CLI not available: {e}")
```

---

*Next: Learn about [CLI Usage](cli-usage.md) or explore [OpenAI Compatibility](openai-compatibility.md).*