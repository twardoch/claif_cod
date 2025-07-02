# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2025-07-01

### Changed
- Switched from anyio to asyncio for subprocess handling for improved reliability
- Import statements changed from relative to absolute imports (e.g., `from .client` to `from claif_cod.client`)
- Reorganized imports to follow standard Python import ordering conventions
- Changed disconnect error logging from WARNING to DEBUG level for cleaner output during cleanup

### Added
- Added reference documentation file (codex-cli-usage.txt)

### Fixed
- Fixed potential subprocess handling issues by using native asyncio instead of anyio
- Improved error handling during process cleanup operations

## [1.0.4] - 2025-07-01

[Previous version - no changelog entry]

## [1.0.3] - 2025-07-01

[Previous version - no changelog entry]

## [1.0.2] - 2025-07-01

### Fixed
- Reduced log noise by changing disconnect errors from WARNING to DEBUG level
- Changed "Unknown block type: input_text" warnings to DEBUG level since they're handled gracefully
- Filtered out user prompt echoes (input_text blocks) from command output
- Improved error message clarity with context about cleanup operations

### Changed
- Better handling of process termination errors with more appropriate logging levels
- Enhanced JSON message parsing to skip input_text content blocks
- Cleaner command output with no prompt echoing and reduced warning noise
- Messages containing only input_text blocks are now filtered out entirely

### Improved
- Much cleaner console output showing only the AI response
- Better user experience with minimal noise in standard operation

## [1.0.1] - 2025-07-01

### Added
- Comprehensive README documentation
- Complete pyproject.toml configuration
- CLI entry point `claif-cod`
- Full development dependencies setup
- Proper build configuration for wheel and sdist
- PLAN.md and TODO.md for project roadmap
- .specstory for conversation history

### Changed
- Updated package description and keywords
- Fixed import paths from relative to absolute
- Improved code formatting and linting compliance
- Enhanced project metadata
- Significant refactoring of all core modules
- Updated logging to use loguru instead of standard logging

### Fixed
- Import errors in all modules
- Missing newlines at end of files
- Ruff configuration issues

## [1.0.0] - 2025-07-01

### Added
- Initial release
- Basic Codex CLI integration
- Fire-based command-line interface
- Async subprocess transport layer
- Support for multiple action modes (review, interactive, full-auto)
- Rich terminal output with progress indicators
- Model management commands
- Configuration system integration withClaif
- Type definitions and data structures
- Error handling and timeout protection