#!/bin/bash
# Technical Debt Metrics Checker
# Run this script to check current status of technical debt metrics

set -e

echo "================================================"
echo "ArxOS Technical Debt Metrics Report"
echo "Generated: $(date)"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print metric
print_metric() {
    local name=$1
    local current=$2
    local target=$3
    local status=$4

    if [ "$status" = "good" ]; then
        echo -e "${GREEN}✓${NC} $name: $current (target: $target)"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠${NC} $name: $current (target: $target)"
    else
        echo -e "${RED}✗${NC} $name: $current (target: $target)"
    fi
}

# Navigate to repo root
cd "$(git rev-parse --show-toplevel)"

echo "📊 CRITICAL METRICS"
echo "-------------------"

# Count unwrap/expect usage
UNWRAP_COUNT=$(grep -r "\.unwrap()" src/ --include="*.rs" | wc -l | xargs)
EXPECT_COUNT=$(grep -r "\.expect(" src/ --include="*.rs" | wc -l | xargs)
TOTAL_UNSAFE=$(($UNWRAP_COUNT + $EXPECT_COUNT))

if [ $TOTAL_UNSAFE -lt 50 ]; then
    print_metric "Unwrap/Expect Count" "$TOTAL_UNSAFE" "<50" "good"
elif [ $TOTAL_UNSAFE -lt 200 ]; then
    print_metric "Unwrap/Expect Count" "$TOTAL_UNSAFE" "<50" "warn"
else
    print_metric "Unwrap/Expect Count" "$TOTAL_UNSAFE" "<50" "bad"
fi

# Check for duplicate modules
DUPLICATE_MODULES=0
if [ -d "src/domain" ] && [ -d "src/core/domain" ]; then
    DUPLICATE_MODULES=$((DUPLICATE_MODULES + 1))
fi
if [ -d "src/spatial" ] && [ -d "src/core/spatial" ]; then
    DUPLICATE_MODULES=$((DUPLICATE_MODULES + 1))
fi

if [ $DUPLICATE_MODULES -eq 0 ]; then
    print_metric "Duplicate Modules" "$DUPLICATE_MODULES" "0" "good"
else
    print_metric "Duplicate Modules" "$DUPLICATE_MODULES" "0" "bad"
fi

# Count TODO comments
TODO_COUNT=$(grep -r "TODO:" src/ --include="*.rs" | wc -l | xargs)
if [ $TODO_COUNT -lt 10 ]; then
    print_metric "TODO Comments" "$TODO_COUNT" "<10" "good"
elif [ $TODO_COUNT -lt 50 ]; then
    print_metric "TODO Comments" "$TODO_COUNT" "<10" "warn"
else
    print_metric "TODO Comments" "$TODO_COUNT" "<10" "bad"
fi

# Count 'as any' in TypeScript
if [ -d "pwa/src" ]; then
    AS_ANY_COUNT=$(grep -r "as any" pwa/src --include="*.ts" --include="*.tsx" | wc -l | xargs)
    if [ $AS_ANY_COUNT -eq 0 ]; then
        print_metric "TypeScript 'as any'" "$AS_ANY_COUNT" "0" "good"
    elif [ $AS_ANY_COUNT -lt 10 ]; then
        print_metric "TypeScript 'as any'" "$AS_ANY_COUNT" "0" "warn"
    else
        print_metric "TypeScript 'as any'" "$AS_ANY_COUNT" "0" "bad"
    fi
fi

echo ""
echo "📈 CODE QUALITY METRICS"
echo "----------------------"

# Count clone usage
CLONE_COUNT=$(grep -r "\.clone()" src/ --include="*.rs" | wc -l | xargs)
if [ $CLONE_COUNT -lt 30 ]; then
    print_metric "Clone Usage" "$CLONE_COUNT" "<30" "good"
elif [ $CLONE_COUNT -lt 60 ]; then
    print_metric "Clone Usage" "$CLONE_COUNT" "<30" "warn"
else
    print_metric "Clone Usage" "$CLONE_COUNT" "<30" "bad"
fi

# Count large files (>500 lines)
LARGE_FILES=$(find src -name "*.rs" -type f -exec wc -l {} \; | awk '$1 > 500' | wc -l | xargs)
if [ $LARGE_FILES -lt 3 ]; then
    print_metric "Large Files (>500 lines)" "$LARGE_FILES" "<3" "good"
elif [ $LARGE_FILES -lt 5 ]; then
    print_metric "Large Files (>500 lines)" "$LARGE_FILES" "<3" "warn"
else
    print_metric "Large Files (>500 lines)" "$LARGE_FILES" "<3" "bad"
fi

# List the large files
if [ $LARGE_FILES -gt 0 ]; then
    echo ""
    echo "  Large files detected:"
    find src -name "*.rs" -type f -exec wc -l {} \; | awk '$1 > 500 {print "  - " $2 " (" $1 " lines)"}' | sort -rn -t'(' -k2
fi

echo ""
echo "🧪 TESTING METRICS"
echo "-----------------"

# Count test files
TEST_FILES=$(find tests -name "*.rs" -type f 2>/dev/null | wc -l | xargs)
echo "  Integration test files: $TEST_FILES"

# Count test functions
TEST_FUNCTIONS=$(grep -r "#\[test\]" src/ tests/ --include="*.rs" 2>/dev/null | wc -l | xargs)
echo "  Test functions: $TEST_FUNCTIONS"

echo ""
echo "📁 BUILD STATUS"
echo "--------------"

# Check if build passes
if cargo check --quiet 2>/dev/null; then
    print_metric "Build Status" "PASS" "PASS" "good"
else
    print_metric "Build Status" "FAIL" "PASS" "bad"
fi

# Check for clippy warnings
CLIPPY_OUTPUT=$(cargo clippy --quiet 2>&1 || true)
CLIPPY_WARNINGS=$(echo "$CLIPPY_OUTPUT" | grep "warning:" | wc -l | xargs)

if [ $CLIPPY_WARNINGS -eq 0 ]; then
    print_metric "Clippy Warnings" "$CLIPPY_WARNINGS" "0" "good"
elif [ $CLIPPY_WARNINGS -lt 10 ]; then
    print_metric "Clippy Warnings" "$CLIPPY_WARNINGS" "0" "warn"
else
    print_metric "Clippy Warnings" "$CLIPPY_WARNINGS" "0" "bad"
fi

echo ""
echo "================================================"
echo "📋 SUMMARY"
echo "================================================"

# Calculate overall progress
METRICS_GOOD=0
METRICS_TOTAL=6

if [ $TOTAL_UNSAFE -lt 50 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi
if [ $DUPLICATE_MODULES -eq 0 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi
if [ $TODO_COUNT -lt 10 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi
if [ $AS_ANY_COUNT -eq 0 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi
if [ $CLONE_COUNT -lt 30 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi
if [ $LARGE_FILES -lt 3 ]; then METRICS_GOOD=$((METRICS_GOOD + 1)); fi

PROGRESS_PCT=$((METRICS_GOOD * 100 / METRICS_TOTAL))

echo "Overall Progress: $METRICS_GOOD/$METRICS_TOTAL metrics meeting targets ($PROGRESS_PCT%)"
echo ""

if [ $PROGRESS_PCT -eq 100 ]; then
    echo -e "${GREEN}🎉 All technical debt targets met!${NC}"
elif [ $PROGRESS_PCT -ge 75 ]; then
    echo -e "${GREEN}✓ Good progress on technical debt remediation${NC}"
elif [ $PROGRESS_PCT -ge 50 ]; then
    echo -e "${YELLOW}⚠ Moderate progress - keep going!${NC}"
else
    echo -e "${RED}✗ Significant technical debt remains${NC}"
fi

echo ""
echo "For detailed remediation plan, see: TECHNICAL_DEBT_REMEDIATION.md"
echo ""
