# TODO - CLAIF_COD Minimal Viable Product

## Essential for v1.0 (Do These Only)

### Mock CLI Script
- [ ] Create `tests/mock_codex_cli.py` (minimal implementation)
  ```python
  # Accept arguments, print JSON responses
  # Support: query, models, health commands
  # ~50 lines total
  ```

### Basic Tests
- [ ] Test transport._find_cli_path()
- [ ] Test transport._build_command() 
- [ ] Test transport._parse_output_line()
- [ ] Test client message conversion
- [ ] Test CLI output formatting

### Documentation Updates
- [ ] Add "Reference Implementation" note to README
- [ ] Document environment variables clearly
- [ ] Add mock CLI usage example
- [ ] State that Codex CLI doesn't exist

### Release
- [ ] Verify package installs: `pip install -e .`
- [ ] Run basic tests
- [ ] Tag release
- [ ] Publish to PyPI

## Nice to Have (If Time Permits)

- [ ] GitHub Actions workflow
- [ ] More test coverage
- [ ] Config file support
- [ ] Better error messages

## Future Ideas (Post v1.0)

**Only consider these if there's real demand:**

- Session management (if users need state)
- Config file support (if env vars aren't enough)
- Response caching (if performance matters)
- Retry logic (if reliability issues arise)
- Real CLI integration (if suitable CLIs appear)

**Principles:**
- Don't add features without user demand
- Keep it simple and maintainable
- Focus on being a good reference/template

## Explicitly Not Doing

- ❌ Configuration files (env vars are sufficient)
- ❌ Session management (stateless is simpler)
- ❌ Response caching (not needed)
- ❌ Advanced approval workflows (basic modes work)
- ❌ Comprehensive test suite (basic tests are enough)
- ❌ Performance optimization (it's fast enough)
- ❌ Multiple CLI support (one example is enough)
- ❌ Complex error recovery (fail fast is fine)

## Summary

**Ship what we have.** The code is good. Add a minimal mock CLI for testing, write a few tests, update the docs to be honest about what this is, and release it.

Total work: ~2-4 hours
- Mock CLI: 30 minutes
- Basic tests: 1 hour
- Doc updates: 30 minutes
- Release: 1 hour

**Remember**: This is a reference implementation that shows how to wrap CLI tools in CLAIF. It doesn't need to be perfect or feature-complete. It needs to be clear, correct, and useful as a template.