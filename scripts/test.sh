#!/bin/bash
# this_file: scripts/test.sh
# Test script for claif_cod package

set -e

echo "🧪 Running claif_cod test suite..."

# Activate virtual environment
source .venv/bin/activate

# Run linting
echo "🔍 Running linting..."
ruff check src/claif_cod tests --fix
ruff format src/claif_cod tests

# Run type checking
echo "🔍 Running type checking..."
mypy src/claif_cod

# Run tests with coverage
echo "🧪 Running tests with coverage..."
pytest --cov=claif_cod --cov-report=term-missing --cov-report=html --cov-report=xml -v

echo "✅ Test suite completed!"