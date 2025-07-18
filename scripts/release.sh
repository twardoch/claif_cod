#!/bin/bash
# this_file: scripts/release.sh
# Release script for claif_cod package

set -e

echo "🚀 Starting release process..."

# Check if we're on a clean working tree
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Working tree is not clean. Please commit or stash changes first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Run tests first
echo "🧪 Running tests..."
./scripts/test.sh

# Get current version
CURRENT_VERSION=$(python -c "from claif_cod import __version__; print(__version__)")
echo "📋 Current version: $CURRENT_VERSION"

# Check if we need to create a new tag
if [[ "$1" == "tag" ]]; then
    if [[ -z "$2" ]]; then
        echo "❌ Please provide a version number: ./scripts/release.sh tag v1.0.27"
        exit 1
    fi
    
    NEW_VERSION="$2"
    echo "🏷️  Creating new tag: $NEW_VERSION"
    
    # Create and push tag
    git tag "$NEW_VERSION"
    git push origin "$NEW_VERSION"
    
    echo "✅ Tag $NEW_VERSION created and pushed!"
fi

# Build the package
echo "🏗️  Building package..."
./scripts/build.sh

# Check if we should publish
if [[ "$1" == "publish" ]]; then
    echo "📤 Publishing to PyPI..."
    python -m twine upload dist/*
    echo "✅ Package published successfully!"
elif [[ "$1" == "publish-test" ]]; then
    echo "📤 Publishing to Test PyPI..."
    python -m twine upload --repository testpypi dist/*
    echo "✅ Package published to Test PyPI!"
else
    echo "📦 Package built but not published."
    echo "To publish, run: ./scripts/release.sh publish"
    echo "To publish to test PyPI: ./scripts/release.sh publish-test"
fi

echo "🎉 Release process completed!"