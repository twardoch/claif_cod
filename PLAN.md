# claif_cod Development Plan - Production OpenAI Codex Integration

## Project Vision

`claif_cod` provides production-ready integration with OpenAI's Codex CLI tool within theClaif framework. It uses the official @openai/codex npm package to deliver real AI-powered coding assistance with auto-install capabilities and streamlined dependencies.

## MVP Strategy

### Core Value Proposition
- **Production Integration**: Real OpenAI Codex CLI functionality
- **Auto-Install Support**: Handles missing dependencies gracefully (Issue #201)
- **Real AI Coding**: Genuine code generation and assistance capabilities
- **Minimal Dependencies**: Uses loguru instead of rich for simplicity

### Architecture Overview

```
claif_cod/
├── transport.py   # Async subprocess management
├── client.py      #Claif provider interface
├── cli.py         # Fire-based CLI (loguru only)
├── types.py       # Type definitions
└── install.py     # Auto-install functionality
```

## Implementation Plan

### Phase 1: Dependency Cleanup
- [ ] Remove all rich imports and usage
- [ ] Replace rich.console with loguru logging  
- [ ] Simplify progress indicators and tables
- [ ] Use plain text output with clear formatting

### Phase 2: Auto-Install Integration
- [ ] Implement CLI detection logic in transport.py
- [ ] Add auto-install prompts when CLI missing
- [ ] Integrate with bun bundling system
- [ ] Provide clear installation guidance

### Phase 3: Real CLI Testing
- [ ] Test real @openai/codex CLI integration
- [ ] Add basic transport layer tests
- [ ] Test message parsing and error handling
- [ ] Verify cross-platform compatibility

### Phase 4: Documentation & Release
- [ ] Update README to document real Codex usage
- [ ] Document OPENAI_API_KEY configuration
- [ ] Create real usage examples
- [ ] Publish to PyPI

## Technical Decisions

### Simplified Output
- **Before**: Rich tables, progress bars, syntax highlighting
- **After**: Clean loguru-based logging with structured output
- **Benefit**: Fewer dependencies, easier maintenance

### Auto-Install Strategy
- Detect missing CLI tools gracefully
- Provide actionable error messages
- Support both npm and bun installation paths
- Fall back to manual installation instructions

### Real Codex CLI Integration
- Uses official @openai/codex npm package
- JSON response format from real OpenAI API
- Supports actual Codex commands and capabilities
- Requires OPENAI_API_KEY for authentication

## Success Criteria

1. **Usability**: Works with `uvx claif_cod` out of box
2. **Functionality**: Real OpenAI Codex integration works
3. **Configuration**: Clear OPENAI_API_KEY setup process
4. **Reliability**: Handles missing dependencies gracefully
5. **Simplicity**: Minimal codebase, easy to understand

## Non-Goals

- Complex features (caching, sessions, etc.)
- Extensive configuration options
- Performance optimization beyond basic needs

## Configuration Guide

For developers using claif_cod with OpenAI Codex:

1. **API Key Setup**: Set OPENAI_API_KEY environment variable
2. **Installation**: Run `claif_cod install` for auto-setup
3. **Usage**: Use standard CLAIF patterns for querying
4. **Error Handling**: Auto-install handles missing CLI dependencies
5. **Authentication**: Codex CLI handles OpenAI API authentication

## Release Strategy

- **v1.0**: Production Codex integration with auto-install
- **v1.1**: Enhanced CLI options and error handling
- **v2.0**: Advanced features based on user feedback

This approach delivers immediate value with real OpenAI Codex functionality through a clean, unified interface.