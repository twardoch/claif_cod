# GitHub Workflows to Add

Due to GitHub App permissions, the workflow files could not be automatically committed. Please manually add these files to your repository.

## Files to Add

Copy these files to `.github/workflows/` in your repository:

1. **test.yml** - Test workflow for PR/push to main/develop
2. **push.yml** - Continuous integration workflow
3. **release.yml** - Release workflow for PyPI publishing
4. **binary-builds.yml** - Binary builds workflow for standalone executables

## Setup Instructions

1. Copy the files to `.github/workflows/`:
   ```bash
   cp workflows-to-add/*.yml .github/workflows/
   ```

2. Commit and push the workflow files:
   ```bash
   git add .github/workflows/
   git commit -m "feat: add GitHub Actions workflows for CI/CD and releases"
   git push
   ```

3. Set up GitHub Secrets (for PyPI publishing):
   - `PYPI_TOKEN` - PyPI API token for production releases
   - `TEST_PYPI_TOKEN` - TestPyPI API token for testing

## Workflow Overview

### test.yml
- Triggers on push/PR to main/develop
- Runs quality checks (linting, formatting, type checking)
- Tests on Python 3.11, 3.12 across Ubuntu/Windows/macOS
- Builds packages and uploads artifacts

### push.yml
- Triggers on push to main (excluding tags)
- Similar to test.yml but for continuous integration
- Builds and tests on every push

### release.yml
- Triggers on git tag push (v*)
- First publishes to TestPyPI for testing
- Then publishes to PyPI for production
- Creates GitHub releases

### binary-builds.yml
- Triggers on git tag push (v*)
- Builds standalone binaries with PyInstaller
- Creates archives for Linux, Windows, macOS
- Attaches binaries to GitHub releases

## Environment Setup

The workflows expect these PyPI environments in your repository settings:
- `testpypi` - For TestPyPI publishing
- `pypi` - For PyPI publishing

## Testing

After adding the workflows, test them by:
1. Creating a PR to trigger test.yml
2. Pushing to main to trigger push.yml
3. Creating a tag to trigger release.yml and binary-builds.yml