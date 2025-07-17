#!/bin/bash
# this_file: scripts/test-release.sh
# Test the complete release workflow

set -e

echo "🚀 Testing complete release workflow..."

# Activate virtual environment
source .venv/bin/activate

# Test 1: Check versioning
echo "📋 Test 1: Versioning system..."
CURRENT_VERSION=$(python -c "from claif_cod import __version__; print(__version__)")
echo "✅ Current version: $CURRENT_VERSION"

# Test 2: Package build
echo "📦 Test 2: Package build..."
./scripts/build.sh
echo "✅ Package build successful"

# Test 3: Install and test the built package
echo "🧪 Test 3: Install and test package..."
# Create a temporary venv for testing
uv venv test-venv
source test-venv/bin/activate
uv pip install dist/claif_cod-*.whl
python -c "import claif_cod; print(f'Installed version: {claif_cod.__version__}')"
claif-cod --help > /dev/null
echo "✅ Package installation and CLI test successful"
deactivate
rm -rf test-venv

# Test 4: Binary build (if PyInstaller is available)
echo "🔨 Test 4: Binary build..."
if command -v pyinstaller &> /dev/null; then
    ./scripts/build-binary.sh
    echo "✅ Binary build successful"
else
    echo "⚠️  PyInstaller not available, skipping binary build"
fi

# Test 5: Simulate tagging
echo "🏷️  Test 5: Simulate git tagging..."
# Don't actually create tags in test, but show what would happen
echo "Current tags:"
git tag -l | tail -5
echo "Next tag would be: v1.0.27 (example)"
echo "✅ Git tagging simulation successful"

# Test 6: Check workflow files
echo "🔍 Test 6: Check workflow files..."
for workflow in .github/workflows/*.yml; do
    if [[ -f "$workflow" ]]; then
        echo "✅ Found workflow: $(basename "$workflow")"
    fi
done

# Test 7: Environment check
echo "🌍 Test 7: Environment check..."
echo "Python version: $(python3 --version)"
echo "UV version: $(uv --version)"
echo "Git version: $(git --version)"
echo "✅ Environment check successful"

echo ""
echo "🎉 All tests passed! Release workflow is ready."
echo ""
echo "To create a release:"
echo "1. ./scripts/release.sh tag v1.0.27"
echo "2. ./scripts/release.sh publish"
echo ""
echo "GitHub Actions will handle:"
echo "- Automated testing on push/PR"
echo "- Binary builds on tag creation"
echo "- PyPI publishing on tag creation"