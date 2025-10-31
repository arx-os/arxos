#!/bin/bash
# ArxOS Security Hooks Setup Script
# Installs pre-commit hooks and configures secret scanning

set -e

echo "🔒 ArxOS Security Hooks Setup"
echo "=============================="
echo ""

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip3 install pre-commit || echo "⚠️  Failed to install via pip3, trying pip..."
    pip install pre-commit
fi

# Verify installation
if ! command -v pre-commit &> /dev/null; then
    echo "❌ Error: Could not install pre-commit"
    echo "Please install manually: pip install pre-commit"
    exit 1
fi

echo "✅ pre-commit installed"

# Install pre-commit hooks
echo ""
echo "🔧 Installing pre-commit hooks..."
pre-commit install

echo ""
echo "🎯 Running pre-commit on all files (first run may take longer)..."
pre-commit run --all-files || echo "⚠️  Some hooks may have warnings - review output above"

# Setup detect-secrets baseline if not exists
if [ ! -f .secrets.baseline ]; then
    echo ""
    echo "📝 Creating secrets baseline..."
    if command -v detect-secrets &> /dev/null; then
        detect-secrets scan --baseline .secrets.baseline
    else
        echo "⚠️  detect-secrets not installed - skipping baseline creation"
        echo "Install with: pip install detect-secrets"
    fi
fi

echo ""
echo "✅ Security hooks setup complete!"
echo ""
echo "📚 What was installed:"
echo "  • Pre-commit hooks for:"
echo "    - Rust formatting (cargo fmt)"
echo "    - Rust linting (cargo clippy)"
echo "    - Rust tests (cargo test)"
echo "    - General file checks"
echo "    - Secret detection"
echo "    - Private key detection"
echo ""
echo "🚀 Next steps:"
echo "  • Hooks will run automatically on 'git commit'"
echo "  • Run manually with: pre-commit run --all-files"
echo "  • Install detect-secrets: pip install detect-secrets"
echo ""
echo "🔍 Security scanning:"
echo "  • GitHub Actions: See .github/workflows/security-scan.yml"
echo "  • Pre-commit: See .pre-commit-config.yaml"
echo ""

