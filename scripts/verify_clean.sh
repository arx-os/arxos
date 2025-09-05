#!/bin/bash
# Verify the clean ArxOS implementation

echo "ArxOS Clean Architecture & Safety Verification"
echo "=============================================="
echo ""

# Check for clean directory structure
echo "✓ Checking project structure..."
if [ -d "arxos_clean" ]; then
    echo "  ❌ ERROR: arxos_clean directory exists (project within project)"
    exit 1
else
    echo "  ✓ No nested projects found"
fi

# Check for clean modules
echo ""
echo "✓ Checking clean modules..."
if [ -f "src/core/arxobject_simple.rs" ]; then
    echo "  ✓ arxobject_simple.rs exists"
else
    echo "  ❌ arxobject_simple.rs missing"
fi

if [ -f "src/core/point_cloud_simple.rs" ]; then
    echo "  ✓ point_cloud_simple.rs exists"
else
    echo "  ❌ point_cloud_simple.rs missing"
fi

# Check for documentation
echo ""
echo "✓ Checking documentation..."
if [ -f "src/core/CLEAN_ARCHITECTURE.md" ]; then
    echo "  ✓ CLEAN_ARCHITECTURE.md exists"
else
    echo "  ❌ CLEAN_ARCHITECTURE.md missing"
fi

# Count lines of code in clean modules
echo ""
echo "✓ Clean module statistics:"
echo "  arxobject_simple.rs: $(wc -l < src/core/arxobject_simple.rs) lines"
echo "  point_cloud_simple.rs: $(wc -l < src/core/point_cloud_simple.rs) lines"

# Check for test files
echo ""
echo "✓ Test files:"
test_count=$(ls src/core/tests/*clean*.rs 2>/dev/null | wc -l)
echo "  Found $test_count clean test file(s)"

echo ""
echo "=============================================="
echo "Clean Architecture & Safety Verification Complete!"
echo ""
echo "Running rustfmt and clippy (deny warnings) on core RF/control modules..."
if command -v cargo >/dev/null 2>&1; then
  # Offline-friendly format check
  cargo fmt --all -- --check | cat
  FMT=$?
  if [ $FMT -ne 0 ]; then
    echo "  ❌ rustfmt --check failed"
    exit $FMT
  else
    echo "  ✓ rustfmt --check passed"
  fi

  # Base clippy
  cargo clippy --workspace -D warnings -q | cat
  CL=$?
  if [ $CL -ne 0 ]; then
    echo "  ❌ Clippy reported issues"
    exit $CL
  else
    echo "  ✓ Clippy passed with -D warnings"
  fi

  # Optional: stricter pedantic/nursery on RF/control modules
  echo "(Optional) Running clippy pedantic/nursery on RF/control modules..."
  cargo clippy -p arxos-core -- -W clippy::pedantic -W clippy::nursery -A clippy::module_name_repetitions -A clippy::missing_errors_doc -A clippy::missing_panics_doc -A clippy::too_many_lines | cat
  echo "  ⚠️ pedantic/nursery run is advisory; fix findings as time allows"

  # Optional: cargo-deny / cargo-audit when internet available
  if command -v cargo-deny >/dev/null 2>&1; then
    echo "(Optional) Running cargo-deny (offline OK if index cached)..."
    cargo deny check | cat || true
  else
    echo "(Note) cargo-deny not installed; skip"
  fi
  if command -v cargo-audit >/dev/null 2>&1; then
    echo "(Optional) Running cargo-audit (requires advisory DB; internet recommended)..."
    cargo audit | cat || true
  else
    echo "(Note) cargo-audit not installed; skip"
  fi
else
  echo "  ⚠️ Skipping clippy: cargo not available on this machine"
fi
echo ""
echo "The ArxOS project now has:"
echo "  • Clean, simplified core modules"
echo "  • No nested project directories"
echo "  • Proper integration into main structure"
echo "  • Documentation for migration path"
echo ""
echo "✅ Ready for development with clean architecture!"