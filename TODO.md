# claif_cod TODO List - MVP Focus

## Essential Tasks

### Real Codex CLI Implementation - ✅ COMPLETED
- [x] Use real @openai/codex package instead of mock
- [x] Remove mock CLI implementation
- [x] Update bundling to use actual OpenAI Codex CLI

### Auto-Install Support (Issue #201) - ✅ COMPLETED
- [x] Implement CLI detection logic
- [x] Add auto-install prompts when CLI missing
- [x] Integrate with bun bundling for offline installation
- [x] Clear error messages with installation guidance
- [x] Wire existing install commands as exception handlers

### Rich Dependencies - ✅ COMPLETED
- [x] Remove all rich dependencies from CLI
- [x] Replace rich.console with loguru logging
- [x] Simplify CLI output formatting
- [x] Remove rich.progress, rich.table, rich.syntax

### Core Testing
- [ ] Test transport._find_cli_path()
- [ ] Test transport._build_command()
- [ ] Test transport._parse_output_line()
- [ ] Test client message conversion
- [ ] Test CLI output formatting

### Documentation
- [ ] Update README to reflect real OpenAI Codex integration
- [ ] Document OPENAI_API_KEY environment variable requirement
- [ ] Add real Codex CLI usage examples
- [ ] Remove references to "reference implementation"

### Release Preparation
- [ ] Verify package installs: `pip install -e .`
- [ ] Run basic tests
- [ ] Tag and publish to PyPI

## Implementation Notes

**Principles:**
- Keep it simple and maintainable
- Use real OpenAI Codex CLI for production readiness
- Don't add features without user demand
- Ship what works, iterate based on feedback

**Total estimated work: 1-2 hours remaining**