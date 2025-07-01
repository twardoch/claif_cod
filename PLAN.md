# CLAIF_COD Development Plan - Minimal Viable Product

## Current Status

CLAIF_COD is a complete async subprocess wrapper for a hypothetical "Codex CLI" tool. The architecture is solid and correctly implements the CLAIF provider interface.

**Note**: This serves as a reference implementation and template for wrapping CLI-based AI tools into the CLAIF framework.

## MVP Strategy - Ship What Works

### Core Value Proposition

CLAIF_COD demonstrates how to:
1. Wrap any CLI tool with async subprocess management
2. Convert between tool-specific and CLAIF message formats
3. Provide both CLI and Python API interfaces
4. Handle errors, timeouts, and platform differences

### What We Have (Keep As-Is)

- ✅ Complete async transport layer with anyio
- ✅ Fire-based CLI with rich output
- ✅ Message format conversion
- ✅ Comprehensive type system
- ✅ Error handling and logging
- ✅ Platform-aware CLI discovery

### What We Need (Minimal Additions)

1. **Basic Mock CLI** (for testing/demo)
   - Simple Python script that echoes JSON
   - Just enough to show the wrapper works
   - Document as example, not production

2. **Essential Tests**
   - Transport layer subprocess handling
   - Message parsing edge cases
   - CLI command verification

3. **Clear Documentation**
   - State this is a reference implementation
   - Show how to adapt for real CLIs
   - Include architecture diagrams

## Scope for v1.x

### Already Complete
- ✅ CLAIF provider interface
- ✅ Async subprocess wrapper
- ✅ Fire CLI with rich output
- ✅ Message conversion logic
- ✅ Type-safe dataclasses
- ✅ Error handling framework
- ✅ Platform compatibility

### Minimal Additions for v1.0
- 🔲 Mock CLI script (50 lines)
- 🔲 Basic transport tests
- 🔲 README clarifications

### Intentionally Deferred
- ❌ Configuration file support (works via env vars)
- ❌ Session management (stateless is fine)
- ❌ Response caching (not needed for v1)
- ❌ Advanced features (keep it simple)

## Architecture Decisions

1. **No Changes Needed**
   - Current architecture is production-ready
   - All patterns are correctly implemented
   - Code is clean and well-structured

2. **Minimal Testing**
   - Focus on transport layer reliability
   - Test message parsing edge cases
   - Skip complex integration tests for v1.0

3. **Simple Configuration**
   - Environment variables work fine
   - No need for config files yet
   - Document the env vars clearly

## Release Criteria for v1.0

1. Mock CLI script works
2. Basic tests pass
3. README accurately describes the project
4. Package installs cleanly
5. All existing features work

## Post v1.0 Considerations

- If real CLI tools emerge, adapt the transport layer
- Add features only when there's clear demand
- Keep the codebase simple and maintainable
- Focus on being a good template/reference

## Philosophy

"Ship a working reference implementation that others can learn from and adapt."

The code is already good. Don't over-engineer. Make it clear what this is (a template) and what it isn't (a production Codex integration). Let users adapt it for their needs.