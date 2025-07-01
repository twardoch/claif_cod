# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Configuration system integration with CLAIF
- Type definitions and data structures
- Error handling and timeout protection