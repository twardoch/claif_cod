#!/bin/bash
# this_file: scripts/build-binary.sh
# Build binary executable for claif_cod

set -e

echo "🔨 Building claif-cod binary..."

# Activate virtual environment
source .venv/bin/activate

# Install PyInstaller if not present
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    uv add pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist-binary/ build-binary/ claif-cod.spec

# Determine OS-specific settings
OS=$(uname -s)
case $OS in
    Linux*)   BINARY_NAME="claif-cod" ;;
    Darwin*)  BINARY_NAME="claif-cod" ;;
    CYGWIN*)  BINARY_NAME="claif-cod.exe" ;;
    MINGW*)   BINARY_NAME="claif-cod.exe" ;;
    *)        BINARY_NAME="claif-cod" ;;
esac

# Build binary
echo "📦 Building binary for $OS..."
pyinstaller \
    --onefile \
    --name "$BINARY_NAME" \
    --paths src \
    --hidden-import claif_cod \
    --hidden-import claif_cod.cli \
    --hidden-import claif_cod.client \
    --hidden-import claif_cod.transport \
    --hidden-import claif_cod.types \
    --hidden-import claif_cod.install \
    --distpath dist-binary \
    --workpath build-binary \
    --specpath . \
    -c src/claif_cod/cli.py

# Test binary
echo "🧪 Testing binary..."
./dist-binary/$BINARY_NAME --help
./dist-binary/$BINARY_NAME version

# Create archive
echo "📦 Creating archive..."
cd dist-binary
ARCHIVE_NAME="claif-cod-$OS-$(uname -m)"
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    tar -czf "$ARCHIVE_NAME.tar.gz" "$BINARY_NAME"
    echo "✅ Archive created: $ARCHIVE_NAME.tar.gz"
else
    zip "$ARCHIVE_NAME.zip" "$BINARY_NAME"
    echo "✅ Archive created: $ARCHIVE_NAME.zip"
fi

cd ..
echo "🎉 Binary build completed!"
echo "📍 Binary location: dist-binary/$BINARY_NAME"
echo "📍 Archive location: dist-binary/$ARCHIVE_NAME.*"