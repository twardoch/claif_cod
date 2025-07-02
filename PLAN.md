# claif_cod Development Plan - v1.x Stable MVP

## Overview

`claif_cod` is the Codex/OpenAI provider for Claif, integrating with OpenAI's Codex CLI tool. The goal for v1.x is to create a stable, reliable MVP with comprehensive testing and cross-platform compatibility.

## Current Status (v1.0.7)

**Core Functionality**: Working Codex CLI integration ✅
**Auto-Install**: Automatic CLI installation when missing ✅
**Subprocess Management**: Async with anyio ✅
**CLI Interface**: Fire-based with clean output ✅

## MVP v1.x Improvement Plan

### 1. Testing & Reliability (Critical)

#### Unit Testing
- [ ] Add pytest test suite for all modules
  - [ ] Test transport.py subprocess handling
  - [ ] Test client.py message conversion
  - [ ] Test CLI command construction
  - [ ] Test JSON parsing logic
  - [ ] Test install.py functionality
- [ ] Mock subprocess operations
- [ ] Test timeout and cancellation
- [ ] Achieve 80%+ code coverage

#### Integration Testing
- [ ] Test with real Codex CLI
- [ ] Test auto-install flow
- [ ] Test different response formats
- [ ] Test error conditions
- [ ] Cross-platform compatibility

#### Subprocess Reliability
- [ ] Handle process termination cleanly
- [ ] Test with slow/hanging processes
- [ ] Verify memory cleanup
- [ ] Test concurrent operations
- [ ] Handle zombie processes

### 2. Error Handling & Messages

#### Better Error Context
- [ ] Add context to subprocess errors
- [ ] Clear API key error messages
- [ ] Installation failure guidance
- [ ] Network timeout explanations
- [ ] Model availability errors

#### Subprocess Error Handling
- [ ] Capture stderr properly
- [ ] Parse CLI error formats
- [ ] Handle non-zero exit codes
- [ ] Timeout error clarity
- [ ] Process spawn failures

### 3. CLI Discovery & Installation

#### Cross-Platform Discovery
- [ ] Test all discovery paths
- [ ] Handle symlinks correctly
- [ ] Support custom install paths
- [ ] Verify executable permissions
- [ ] Handle path spaces/quotes

#### Installation Robustness
- [ ] Verify npm/bun availability
- [ ] Handle partial installs
- [ ] Support proxy environments
- [ ] Offline install options
- [ ] Version compatibility checks

### 4. Transport Layer Improvements

#### Async Operations
- [ ] Proper cleanup on cancellation
- [ ] Handle process groups
- [ ] Stream buffering optimization
- [ ] Backpressure handling
- [ ] Resource leak prevention

#### Performance
- [ ] Profile subprocess overhead
- [ ] Optimize JSON parsing
- [ ] Reduce memory usage
- [ ] Connection pooling
- [ ] Response streaming

### 5. Documentation & Examples

#### User Documentation
- [ ] Installation guide
- [ ] API key setup guide
- [ ] Model selection guide
- [ ] Troubleshooting section
- [ ] Common errors FAQ

#### Developer Documentation
- [ ] Architecture overview
- [ ] Transport layer design
- [ ] Testing approach
- [ ] Contributing guide
- [ ] API reference

### 6. Code Organization

#### Module Structure
```
claif_cod/
├── __init__.py        # Clean public API
├── transport.py       # Robust subprocess layer
├── client.py         # Tested client wrapper
├── cli.py            # User-friendly CLI
├── types.py          # Well-defined types
├── install.py        # Cross-platform installer
└── utils.py          # Shared utilities
```

#### Key Improvements Needed

#### transport.py
- Better process lifecycle management
- Improved error context
- Resource cleanup
- Performance monitoring

#### client.py
- Message validation
- Error wrapping
- Retry logic
- Connection pooling

#### cli.py
- Standardized help text
- Progress indicators
- Better error display
- Command validation

## Quality Standards

### Code Quality
- 100% type hint coverage
- Comprehensive docstrings
- Maximum cyclomatic complexity: 10
- Clear error messages
- Consistent naming

### Testing Standards
- Unit tests for all functions
- Integration tests for workflows
- Mock all subprocess calls
- Test all error paths
- Cross-platform verification

### Documentation Standards
- Complete README
- API documentation
- Architecture diagrams
- Troubleshooting guide
- Performance tips

## Success Criteria for v1.x

1. **Reliability**: 99.9% success rate for subprocess operations
2. **Performance**: < 100ms overhead per operation
3. **Testing**: 80%+ test coverage with mocks
4. **Error Handling**: Clear, actionable error messages
5. **Cross-Platform**: Verified on Windows, macOS, Linux
6. **Documentation**: Complete user and API docs
7. **Installation**: Auto-install works on clean systems

## Development Priorities

### Immediate (v1.0.8)
1. Add comprehensive test suite
2. Fix subprocess cleanup issues
3. Improve error messages

### Short-term (v1.1.0)
1. Cross-platform testing
2. Complete documentation
3. Performance optimization

### Medium-term (v1.2.0)
1. Advanced CLI features
2. Response caching
3. Extended error recovery

## Non-Goals for v1.x

- Complex UI features
- Custom protocol extensions
- Database persistence
- Multi-user support
- Response transformation

## Testing Strategy

### Unit Test Focus
- Mock all subprocess.Popen calls
- Test JSON parsing edge cases
- Verify timeout behavior
- Test CLI discovery logic
- Validate error handling

### Integration Test Focus
- Real CLI execution (when available)
- Cross-platform path handling
- Installation verification
- Network failure scenarios
- API key validation

### Performance Testing
- Subprocess spawn overhead
- JSON parsing speed
- Memory usage profiling
- Concurrent operation limits
- Response streaming efficiency

Keep the codebase lean and focused on being a reliable subprocess-based provider for Claif.