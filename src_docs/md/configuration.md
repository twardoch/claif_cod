# Configuration

Comprehensive guide to configuring `claif_cod` for your environment and use cases.

## Configuration Methods

`claif_cod` supports multiple configuration methods with the following priority order:

1. **Runtime parameters** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Default values** (lowest priority)

## Environment Variables

### Core Variables

```bash
# Required: OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Optional: Explicit path to Codex CLI
export CODEX_CLI_PATH="/usr/local/bin/codex"

# Optional: Default model to use
export CODEX_DEFAULT_MODEL="o4-mini"

# Optional: Default action mode
export CODEX_ACTION_MODE="review"

# Optional: Default timeout in seconds
export CODEX_TIMEOUT="180"

# Optional: Default sandbox mode
export CODEX_SANDBOX_MODE="workspace-write"

# Optional: Default approval policy
export CODEX_APPROVAL_POLICY="on-failure"

# Optional: Working directory
export CODEX_WORKING_DIR="/path/to/project"
```

### Advanced Variables

```bash
# Debug and logging
export CODEX_DEBUG="true"
export CODEX_LOG_LEVEL="DEBUG"

# Performance tuning
export CODEX_MAX_TOKENS="2000"
export CODEX_TEMPERATURE="0.2"
export CODEX_TOP_P="1.0"

# Retry configuration
export CODEX_MAX_RETRIES="3"
export CODEX_RETRY_DELAY="1.0"
```

## Configuration Files

### Claif Framework Integration

When using with the Claif framework, add to `~/.claif/config.toml`:

```toml
[providers.codex]
enabled = true
cli_path = "/usr/local/bin/codex"
default_model = "o4-mini"
default_action_mode = "review"
timeout = 180
sandbox_mode = "workspace-write"
approval_policy = "on-failure"

[providers.codex.models]
available = ["o3.5", "o4-mini", "o4", "o4-preview"]
default = "o4-mini"

[providers.codex.safety]
default_sandbox = "workspace-write"
allowed_sandboxes = ["read-only", "workspace-write", "danger-full-access"]
default_approval = "on-failure"
allowed_approvals = ["untrusted", "on-failure", "never"]

[providers.codex.performance]
default_timeout = 180
max_timeout = 600
default_max_tokens = 2000
default_temperature = 0.2
```

### Standalone Configuration

For standalone usage, create `~/.codex/config.toml`:

```toml
[cli]
path = "/usr/local/bin/codex"
timeout = 180

[models]
default = "o4-mini"
available = ["o3.5", "o4-mini", "o4", "o4-preview"]

[safety]
sandbox_mode = "workspace-write"
approval_policy = "on-failure"

[api]
base_url = "https://api.openai.com/v1"
max_retries = 3
retry_delay = 1.0

[output]
format = "text"
verbose = false
```

## CLI Path Discovery

`claif_cod` automatically discovers the Codex CLI binary using this search order:

### 1. Environment Variable

```bash
export CODEX_CLI_PATH="/explicit/path/to/codex"
```

### 2. System PATH

The CLI searches your system PATH for `codex`:

```bash
# Check if codex is in PATH
which codex
# or
whereis codex
```

### 3. Common Installation Locations

If not found in PATH, searches these locations:

=== "Linux/macOS"

    ```
    /usr/local/bin/codex
    /opt/homebrew/bin/codex
    ~/.cargo/bin/codex
    ~/.local/bin/codex
    /usr/bin/codex
    ```

=== "Windows"

    ```
    %USERPROFILE%\.cargo\bin\codex.exe
    %LOCALAPPDATA%\Programs\codex\codex.exe
    C:\Program Files\codex\codex.exe
    C:\Program Files (x86)\codex\codex.exe
    ```

### Custom Discovery

```python
from claif_cod import CodexClient

# Explicit path
client = CodexClient(codex_path="/custom/path/to/codex")

# Search additional locations
client = CodexClient(
    search_paths=[
        "/opt/custom/bin/codex",
        "~/tools/codex",
        "/usr/local/custom/codex"
    ]
)
```

## Model Configuration

### Available Models

```python
from claif_cod import CodexClient

# List available models
client = CodexClient()
models = client.models.list()
for model in models:
    print(f"Model: {model.id}")
```

### Model Selection

=== "Runtime"

    ```python
    # Per-request model selection
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4"  # Override default
    )
    ```

=== "Client-level"

    ```python
    # Default model for client
    client = CodexClient(model="o4-preview")
    ```

=== "Environment"

    ```bash
    export CODEX_DEFAULT_MODEL="o4"
    ```

### Model-specific Settings

```toml
[providers.codex.models.o4-mini]
max_tokens = 1000
temperature = 0.1
top_p = 0.9

[providers.codex.models.o4]
max_tokens = 2000
temperature = 0.2
top_p = 1.0

[providers.codex.models.o4-preview]
max_tokens = 4000
temperature = 0.3
top_p = 1.0
```

## Safety Configuration

### Sandbox Modes

Control file system access:

=== "read-only"

    - Can only read files
    - No write operations allowed
    - Safest mode for code analysis

    ```python
    client = CodexClient(sandbox_mode="read-only")
    ```

=== "workspace-write"

    - Can read/write within working directory
    - Cannot access parent directories
    - Good balance of safety and functionality

    ```python
    client = CodexClient(
        sandbox_mode="workspace-write",
        working_dir="/path/to/project"
    )
    ```

=== "danger-full-access"

    - Full system access
    - Can read/write anywhere
    - Use with extreme caution

    ```python
    client = CodexClient(sandbox_mode="danger-full-access")
    ```

### Approval Policies

Control when user approval is required:

=== "untrusted"

    - Require approval for all actions
    - Highest security level
    - Good for sensitive environments

    ```python
    client = CodexClient(approval_policy="untrusted")
    ```

=== "on-failure"

    - Only ask approval when operations fail
    - Balanced approach
    - Default setting

    ```python
    client = CodexClient(approval_policy="on-failure")
    ```

=== "never"

    - Never ask for approval
    - Auto-approve all actions
    - Use only in trusted environments

    ```python
    client = CodexClient(approval_policy="never")
    ```

## Performance Configuration

### Timeout Settings

```python
from claif_cod import CodexClient

# Client-level timeout
client = CodexClient(timeout=300)  # 5 minutes

# Per-request timeout
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Complex task"}],
    model="o4",
    timeout=600  # 10 minutes for this request
)
```

### Token Limits

```python
# Configure token limits
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Generate code"}],
    model="o4-mini",
    max_tokens=1500,
    temperature=0.2,
    top_p=0.9
)
```

### Retry Configuration

```toml
[providers.codex.retry]
max_attempts = 3
initial_delay = 1.0
max_delay = 60.0
exponential_base = 2.0
jitter = true
```

```python
from claif_cod import CodexClient
from tenacity import retry, stop_after_attempt, wait_exponential

# Custom retry configuration
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def make_request():
    return client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model="o4-mini"
    )
```

## Working Directory Configuration

### Setting Working Directory

```python
from pathlib import Path
from claif_cod import CodexClient

# Absolute path
client = CodexClient(working_dir="/path/to/project")

# Relative path
client = CodexClient(working_dir="./my-project")

# Path object
client = CodexClient(working_dir=Path("~/projects/myapp").expanduser())
```

### Dynamic Working Directory

```python
import os
from claif_cod import CodexClient

# Change working directory per request
client = CodexClient()

# Request 1: Work on frontend
os.chdir("./frontend")
response1 = client.chat.completions.create(
    messages=[{"role": "user", "content": "Update React components"}],
    model="o4"
)

# Request 2: Work on backend
os.chdir("../backend")
response2 = client.chat.completions.create(
    messages=[{"role": "user", "content": "Optimize database queries"}],
    model="o4"
)
```

## CLI Configuration

### Global CLI Settings

```bash
# Set default CLI options
claif-cod config set --model o4-mini
claif-cod config set --sandbox workspace-write
claif-cod config set --approval on-failure
claif-cod config set --timeout 300

# Save configuration
claif-cod config save

# View current configuration
claif-cod config show
```

### Per-command Configuration

```bash
# Override defaults per command
claif-cod query "Complex task" \
    --model o4 \
    --timeout 600 \
    --sandbox danger-full-access \
    --approval never \
    --working-dir ./project
```

## Validation and Testing

### Configuration Validation

```python
from claif_cod import CodexClient

# Test configuration
client = CodexClient()

# Validate CLI path
if client.validate_cli_path():
    print("✅ Codex CLI found and working")
else:
    print("❌ Codex CLI not found or not working")

# Test API connectivity
try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "test"}],
        model="o4-mini",
        max_tokens=1
    )
    print("✅ API connection working")
except Exception as e:
    print(f"❌ API connection failed: {e}")
```

### Health Check

```bash
# Comprehensive health check
claif-cod health

# Detailed health check
claif-cod health --verbose

# Check specific components
claif-cod health --check-cli
claif-cod health --check-api
claif-cod health --check-config
```

## Troubleshooting Configuration

### Common Issues

#### CLI Not Found

```bash
# Check CLI path
echo $CODEX_CLI_PATH

# Test CLI directly
codex --version

# Manually set path
export CODEX_CLI_PATH="/usr/local/bin/codex"
```

#### Permission Issues

```bash
# Check file permissions
ls -la $(which codex)

# Fix permissions
chmod +x $(which codex)
```

#### API Key Issues

```bash
# Check API key
echo $OPENAI_API_KEY

# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### Debug Mode

```python
import logging
from claif_cod import CodexClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = CodexClient()
# Now all operations will show detailed debug information
```

```bash
# CLI debug mode
claif-cod query "test" --verbose --debug
```

## Best Practices

### Security

1. **Use environment variables** for sensitive data
2. **Restrict sandbox modes** in production
3. **Enable approval policies** for critical systems
4. **Regular key rotation** for API keys
5. **Audit configuration** periodically

### Performance

1. **Set appropriate timeouts** for your use cases
2. **Use caching** for repeated requests
3. **Optimize token limits** for efficiency
4. **Monitor API usage** and costs
5. **Use streaming** for long responses

### Maintainability

1. **Document configuration** choices
2. **Version control** configuration files
3. **Test configuration** changes
4. **Use consistent** naming conventions
5. **Regular updates** of dependencies

---

*Next: Learn about the [Python API](python-api.md) or explore [CLI Usage](cli-usage.md).*