# TODO - CLAIF_COD v1.0

## Priority 1: Core Functionality (MVP)

### Mock CLI Implementation
- [ ] Create `mock_codex_cli.py` script in `tests/fixtures/`
- [ ] Implement basic command parsing
- [ ] Add JSON output for queries
- [ ] Support model listing
- [ ] Handle health checks
- [ ] Document mock CLI behavior

### Configuration
- [ ] Implement `config save` command
- [ ] Implement `config load` command
- [ ] Add configuration file validation
- [ ] Create default config template
- [ ] Add config migration support

### Testing
- [ ] Add unit tests for transport layer
- [ ] Add unit tests for client module
- [ ] Add unit tests for CLI commands
- [ ] Create integration tests with mock CLI
- [ ] Add type checking tests
- [ ] Achieve >80% code coverage

### Documentation
- [ ] Update README with mock CLI instructions
- [ ] Add "Limitations" section to README
- [ ] Create CONTRIBUTING.md
- [ ] Add API documentation
- [ ] Create migration guide for other CLIs
- [ ] Add troubleshooting section

### Package & Release
- [ ] Verify all dependencies are correct
- [ ] Test package installation
- [ ] Create GitHub Actions for CI/CD
- [ ] Prepare PyPI release
- [ ] Tag v1.0.0 release

## Priority 2: Polish & Improvements

### Error Handling
- [ ] Add specific error for missing CLI
- [ ] Improve timeout error messages
- [ ] Add retry logic for transient failures
- [ ] Better JSON parsing errors

### CLI Enhancements
- [ ] Add `--version` flag
- [ ] Add `--debug` mode
- [ ] Improve help text
- [ ] Add command aliases
- [ ] Add shell completion

### Code Quality
- [ ] Add more type hints
- [ ] Improve docstrings
- [ ] Remove any dead code
- [ ] Optimize imports
- [ ] Add performance logging

## Priority 3: Future Features (Post v1.0)

### Advanced Features
- [ ] Session management
- [ ] Response caching
- [ ] Plugin system for CLIs
- [ ] Dynamic model discovery
- [ ] Approval strategy plugins

### Integration
- [ ] Support for Continue.dev CLI
- [ ] Support for GitHub Copilot CLI
- [ ] Generic CLI adapter framework
- [ ] Direct API integration option

### Developer Experience
- [ ] Development container setup
- [ ] VSCode extension
- [ ] Jupyter notebook support
- [ ] Interactive mode improvements

## Not Doing (Out of Scope for v1.0)

- ❌ Real Codex CLI integration (doesn't exist)
- ❌ Complex approval workflows
- ❌ Multi-user support
- ❌ Web UI
- ❌ Cloud deployment
- ❌ Commercial features
- ❌ Advanced telemetry
- ❌ Database integration

## Notes

Focus on delivering a solid reference implementation that:
1. Works out of the box with mock CLI
2. Demonstrates CLAIF provider patterns
3. Is well-tested and documented
4. Can be easily adapted to real CLIs

Remember: "Done is better than perfect" - ship a working v1.0 that people can use and learn from.