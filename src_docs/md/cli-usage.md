# CLI Usage

Complete guide to using the `claif-cod` command-line interface.

## Installation and Setup

After installing `claif_cod`, the CLI is available as `claif-cod`:

```bash
# Verify installation
claif-cod --help

# Check system health
claif-cod health
```

## Basic Commands

### query

Execute a single query and return results.

```bash
# Basic usage
claif-cod query "Write a Python function to calculate factorial"

# With specific model
claif-cod query "Optimize this database query" --model o4

# With output format
claif-cod query "Create a REST API" --format json

# With working directory
claif-cod query "Add tests" --working-dir ./my-project
```

**Parameters:**
- `prompt` (required): The query to send to Codex
- `--model`: Model to use (default: o4-mini)
- `--format`: Output format (text, json, code)
- `--working-dir`: Working directory for operations
- `--sandbox`: Sandbox mode (read-only, workspace-write, danger-full-access)
- `--approval`: Approval policy (untrusted, on-failure, never)
- `--timeout`: Request timeout in seconds
- `--temperature`: Creativity level (0.0-2.0)
- `--max-tokens`: Maximum response length

### stream

Stream responses in real-time for long-running queries.

```bash
# Stream response
claif-cod stream "Explain machine learning concepts in detail"

# Stream with specific model
claif-cod stream "Write comprehensive documentation" --model o4-preview

# Stream with custom settings
claif-cod stream "Generate test suite" --max-tokens 3000 --temperature 0.1
```

### chat

Interactive chat mode for multi-turn conversations.

```bash
# Start interactive chat
claif-cod chat

# Chat with specific model
claif-cod chat --model o4

# Chat with system prompt
claif-cod chat --system "You are an expert Python developer"
```

**Interactive Commands:**
- `!exit` or `!quit`: Exit chat mode
- `!clear`: Clear conversation history
- `!save <filename>`: Save conversation to file
- `!load <filename>`: Load conversation from file
- `!model <model_name>`: Switch model
- `!help`: Show help

### exec

Execute code operations with file system access.

```bash
# Execute with review mode (default)
claif-cod exec "Fix all linting errors in this project"

# Execute with auto-approval
claif-cod exec "Format all Python files" --approval never

# Execute with restricted access
claif-cod exec "Analyze code quality" --sandbox read-only

# Execute in specific directory
claif-cod exec "Add type hints" --working-dir ./src --sandbox workspace-write
```

## Information Commands

### health

Check system health and configuration.

```bash
# Basic health check
claif-cod health

# Detailed health check
claif-cod health --verbose

# Check specific components
claif-cod health --check-cli --check-api --check-config
```

### models

List available models and their details.

```bash
# List all models
claif-cod models

# Show detailed model information
claif-cod models --detailed

# Show model capabilities
claif-cod model-info o4-mini
```

### version

Display version information.

```bash
# Show version
claif-cod version

# Show detailed version info
claif-cod version --detailed
```

## Configuration Commands

### config

Manage configuration settings.

```bash
# Show current configuration
claif-cod config show

# Show configuration in different formats
claif-cod config show --format json
claif-cod config show --format yaml

# Set configuration values
claif-cod config set --model o4-mini
claif-cod config set --sandbox workspace-write
claif-cod config set --approval on-failure
claif-cod config set --timeout 300
claif-cod config set --codex-path /usr/local/bin/codex

# Save configuration to file
claif-cod config save

# Load configuration from file
claif-cod config load --file ~/.codex/config.toml

# Reset to defaults
claif-cod config reset
```

## Global Options

These options work with all commands:

```bash
--verbose           # Enable verbose output
--debug             # Enable debug mode
--quiet             # Suppress non-essential output
--no-color          # Disable colored output
--config-file       # Use specific config file
--log-file          # Write logs to file
--help              # Show help for command
```

## Output Formats

### Text Format (Default)

```bash
claif-cod query "Hello world" --format text
```

Clean, human-readable output with syntax highlighting.

### JSON Format

```bash
claif-cod query "Hello world" --format json
```

```json
{
  "model": "o4-mini",
  "content": "print('Hello, world!')",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  },
  "finish_reason": "stop"
}
```

### Code Format

```bash
claif-cod query "Write a Python function" --format code
```

Outputs only the generated code without metadata.

### Raw Format

```bash
claif-cod query "Hello world" --format raw
```

Unprocessed output from the Codex CLI.

## Advanced Usage

### Working with Projects

```bash
# Analyze entire project
claif-cod query "Review this codebase for security issues" \
    --working-dir ./my-project \
    --sandbox read-only \
    --timeout 600

# Refactor specific modules
claif-cod exec "Modernize legacy code in the auth module" \
    --working-dir ./my-project/auth \
    --sandbox workspace-write \
    --approval on-failure

# Generate documentation
claif-cod query "Create comprehensive documentation" \
    --working-dir ./my-project \
    --model o4-preview \
    --max-tokens 4000
```

### Batch Operations

```bash
# Process multiple files
for file in src/*.py; do
    claif-cod query "Add type hints to this file: $file" \
        --working-dir "$(dirname "$file")" \
        --format code > "${file}.typed"
done

# Generate tests for all modules
find src -name "*.py" -exec claif-cod query \
    "Generate unit tests for this module: {}" \
    --working-dir src \
    --format code \
    --output tests/test_{}.py \;
```

### Pipeline Integration

```bash
# Git hook integration
#!/bin/bash
# .git/hooks/pre-commit

# Check for code quality issues
claif-cod query "Review staged changes for issues" \
    --working-dir . \
    --sandbox read-only \
    --format json > code_review.json

# Exit with error if issues found
if jq -e '.issues | length > 0' code_review.json > /dev/null; then
    echo "Code quality issues found. Check code_review.json"
    exit 1
fi
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: AI Code Review
on: [pull_request]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install claif_cod
        run: pip install claif_cod
        
      - name: AI Code Review
        run: |
          claif-cod query "Review this pull request for issues" \
            --working-dir . \
            --sandbox read-only \
            --format json > review.json
            
      - name: Post Review
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = JSON.parse(fs.readFileSync('review.json'));
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## AI Code Review\n\n${review.content}`
            });
```

## Troubleshooting

### Common Issues

#### Command Not Found

```bash
# Error: claif-cod: command not found
# Solution: Check installation and PATH

# Verify installation
pip show claif_cod

# Check if CLI is in PATH
which claif-cod

# Reinstall if needed
pip uninstall claif_cod
pip install claif_cod
```

#### Codex CLI Not Found

```bash
# Error: Codex CLI not found
# Solution: Install Codex CLI and set path

# Install Codex CLI
cargo install codex

# Check if in PATH
which codex

# Set explicit path
export CODEX_CLI_PATH=/usr/local/bin/codex
```

#### Permission Denied

```bash
# Error: Permission denied when accessing files
# Solution: Check file permissions and sandbox mode

# Check current permissions
ls -la

# Use appropriate sandbox mode
claif-cod query "Read this file" --sandbox read-only

# Fix permissions if needed
chmod +r filename
```

#### Timeout Errors

```bash
# Error: Request timed out
# Solution: Increase timeout or break into smaller tasks

# Increase timeout
claif-cod query "Complex task" --timeout 600

# Break into smaller tasks
claif-cod query "First part of task" --timeout 180
claif-cod query "Second part of task" --timeout 180
```

### Debug Mode

```bash
# Enable verbose debugging
claif-cod query "test" --verbose --debug

# Save debug output to file
claif-cod query "test" --verbose --debug --log-file debug.log

# Check specific components
claif-cod health --verbose --debug
```

### Environment Issues

```bash
# Check environment variables
env | grep CODEX
env | grep OPENAI

# Test CLI directly
codex --version

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

## Performance Optimization

### Response Caching

```bash
# Enable response caching (if available)
claif-cod config set --cache-enabled true
claif-cod config set --cache-ttl 3600  # 1 hour

# Clear cache
claif-cod cache clear

# Show cache stats
claif-cod cache stats
```

### Parallel Processing

```bash
# Process multiple queries in parallel
claif-cod query "Task 1" &
claif-cod query "Task 2" &
claif-cod query "Task 3" &
wait

# Use GNU parallel for complex workflows
parallel claif-cod query "Process file {}" --working-dir {} ::: project1 project2 project3
```

### Resource Management

```bash
# Limit token usage
claif-cod query "Large task" --max-tokens 1000

# Use faster model for simple tasks
claif-cod query "Simple task" --model o4-mini

# Set appropriate timeouts
claif-cod query "Quick task" --timeout 30
claif-cod query "Complex task" --timeout 600
```

## Best Practices

### Security

1. **Use read-only mode** for analysis tasks
2. **Review changes** before applying them
3. **Limit working directory** scope
4. **Use approval policies** in production
5. **Protect API keys** with environment variables

### Performance

1. **Choose appropriate models** for task complexity
2. **Set reasonable timeouts** for different operations
3. **Use streaming** for long responses
4. **Cache results** when possible
5. **Parallelize** independent operations

### Maintainability

1. **Document command usage** in scripts
2. **Use configuration files** for consistent settings
3. **Version control** configuration changes
4. **Test commands** before production use
5. **Monitor usage** and costs

---

*Next: Learn about [OpenAI Compatibility](openai-compatibility.md) or explore the [Architecture](architecture.md).*