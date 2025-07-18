#!/bin/bash
# this_file: scripts/build.sh
# Build script for claif_cod package

set -e

echo "🏗️  Building claif_cod package..."

# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/claif_cod.egg-info/

# Build the package
echo "📦 Building package..."
python -m build --no-isolation

# Check package
echo "🔍 Checking package..."
python -m twine check dist/*

echo "✅ Package built successfully!"
echo "📦 Files created:"
ls -la dist/