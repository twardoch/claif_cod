# Release Setup Documentation

## Overview

This document describes the complete release setup for the `claif_cod` project, including git-tag-based semversioning, comprehensive testing, build scripts, and GitHub Actions CI/CD.

## Version Management

### Git-Tag-Based Semversioning

The project uses **hatch-vcs** for automatic version management based on git tags:

- **Version Source**: Git tags (configured in `pyproject.toml`)
- **Version File**: `src/claif_cod/_version.py` (auto-generated)
- **Format**: Standard semver with development versions (e.g., `v1.0.27.dev6+g53dfe14.d20250717`)

### Current Setup

```toml
[tool.hatch.version]
source = 'vcs'  # Get version from git tags

[tool.hatch.build.hooks.vcs]
version-file = "src/claif_cod/_version.py"
```

## Local Scripts

### Build and Test Scripts

Located in `scripts/` directory:

1. **`test.sh`** - Run complete test suite with linting and coverage
2. **`build.sh`** - Build Python packages (wheel and sdist)
3. **`build-binary.sh`** - Build standalone binary with PyInstaller
4. **`release.sh`** - Complete release workflow with tagging and publishing
5. **`test-release.sh`** - Test the complete release workflow

### Usage Examples

```bash
# Run tests
./scripts/test.sh

# Build packages
./scripts/build.sh

# Build binary
./scripts/build-binary.sh

# Create and push tag
./scripts/release.sh tag v1.0.27

# Publish to PyPI
./scripts/release.sh publish

# Test complete workflow
./scripts/test-release.sh
```

## GitHub Actions Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

**Triggers**: Push/PR to main/develop branches
**Matrix**: Python 3.11, 3.12 on Ubuntu/Windows/macOS

**Jobs**:
- **Quality**: Linting, formatting, type checking
- **Test**: Run test suite with coverage
- **Build**: Build packages and upload artifacts

### 2. Push Workflow (`.github/workflows/push.yml`)

**Triggers**: Push to main (non-tag)
**Purpose**: Continuous integration on every push

**Jobs**:
- **Quality**: Code quality checks
- **Test**: Multi-platform testing
- **Build**: Package building

### 3. Release Workflow (`.github/workflows/release.yml`)

**Triggers**: Push of version tags (`v*`)
**Purpose**: Automated release to PyPI

**Jobs**:
- **Test Release**: Publish to TestPyPI first
- **Release**: Publish to PyPI and create GitHub release

### 4. Binary Builds Workflow (`.github/workflows/binary-builds.yml`)

**Triggers**: Push of version tags (`v*`)
**Purpose**: Build standalone binaries

**Jobs**:
- **Build Binaries**: Create executables for Linux/Windows/macOS
- **Release Binaries**: Attach to GitHub release

## Release Process

### 1. Standard Release

```bash
# 1. Ensure clean working tree
git status

# 2. Run complete test suite
./scripts/test-release.sh

# 3. Create and push tag
./scripts/release.sh tag v1.0.27

# 4. GitHub Actions will automatically:
#    - Run tests
#    - Build packages
#    - Build binaries
#    - Publish to PyPI
#    - Create GitHub release
```

### 2. Manual Release

```bash
# Build and publish manually
./scripts/build.sh
./scripts/release.sh publish
```

## Package Configuration

### Dependencies

**Core Dependencies**:
- `claif>=1.0.0` - Main framework
- `anyio>=4.0.0` - Async compatibility
- `fire>=0.7.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `loguru>=0.7.0` - Logging
- `tenacity>=9.0.0` - Retry logic

**Build Dependencies**:
- `hatchling>=1.27.0` - Build backend
- `hatch-vcs>=0.5.0` - Version control integration
- `build>=1.2.2.post1` - Package building

**Development Dependencies**:
- `pytest>=8.4.1` - Testing framework
- `pytest-cov>=6.2.1` - Coverage reporting
- `ruff>=0.12.4` - Linting and formatting
- `mypy>=1.17.0` - Type checking
- `twine>=6.1.0` - PyPI publishing

### Build Configuration

```toml
[build-system]
requires = ["hatchling>=1.27.0", "hatch-vcs>=0.5.0"]
build-backend = "hatchling.build"

[project]
name = "claif_cod"
requires-python = ">=3.11"
dynamic = ["version"]

[project.scripts]
claif-cod = "claif_cod.cli:main"
```

## Binary Builds

### PyInstaller Configuration

The project can be built as standalone binaries using PyInstaller:

```bash
pyinstaller \
  --onefile \
  --name claif-cod \
  --paths src \
  --hidden-import claif_cod \
  --hidden-import claif_cod.cli \
  --hidden-import claif_cod.client \
  --hidden-import claif_cod.transport \
  --hidden-import claif_cod.types \
  --hidden-import claif_cod.install \
  -c src/claif_cod/cli.py
```

### Platforms

Binaries are automatically built for:
- **Linux** (x86_64) - `.tar.gz`
- **Windows** (x86_64) - `.zip`
- **macOS** (x86_64) - `.tar.gz`

## Environment Setup

### Required Tools

- **Python 3.11+**
- **uv** (package manager)
- **git** (version control)

### Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/twardoch/claif_cod.git
cd claif_cod

# Install dependencies
uv sync

# Test setup
./scripts/test-release.sh
```

## Version History

The project maintains semantic versioning:
- **Major**: Breaking changes
- **Minor**: New features
- **Patch**: Bug fixes

Current version can be checked with:
```bash
python -c "from claif_cod import __version__; print(__version__)"
```

## Security Considerations

- **Secrets**: PyPI tokens stored in GitHub Secrets
- **Permissions**: Minimal permissions for GitHub Actions
- **Dependencies**: Regular security updates via Dependabot

## Troubleshooting

### Common Issues

1. **Build Failures**: Check Python version compatibility (3.11+)
2. **Test Failures**: Run `./scripts/test.sh` for detailed output
3. **Version Issues**: Ensure git tags are properly formatted (`v*`)
4. **PyPI Publishing**: Verify API tokens and permissions

### Debug Commands

```bash
# Check version
python -c "from claif_cod import __version__; print(__version__)"

# Check build
./scripts/build.sh

# Check tests
./scripts/test.sh

# Check complete workflow
./scripts/test-release.sh
```

## Contributing

When contributing to the project:

1. Follow the existing code style (enforced by ruff)
2. Add tests for new features
3. Update documentation
4. Ensure all checks pass locally
5. Create pull requests against the main branch

The CI/CD pipeline will automatically run all checks and tests.