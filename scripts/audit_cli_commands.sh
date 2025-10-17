#!/bin/bash
# ArxOS CLI Command Audit Script
# Tests all CLI commands to determine what works vs what shows fake/placeholder data
#
# Usage: ./scripts/audit_cli_commands.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARX_BIN="$PROJECT_ROOT/bin/arx"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results tracking
TOTAL_COMMANDS=0
WORKING_COMMANDS=0
PLACEHOLDER_COMMANDS=0
FAILING_COMMANDS=0
RESULTS_FILE="$PROJECT_ROOT/cli_audit_results.md"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ArxOS CLI Command Audit"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing binary: $ARX_BIN"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Initialize results file
cat > "$RESULTS_FILE" << 'EOF'
# ArxOS CLI Command Audit Results

**Generated:** $(date)

## Summary

- **Total Commands Tested:** TBD
- **✅ Working:** TBD
- **⚠️ Placeholder/Fake Data:** TBD
- **❌ Failing/Not Implemented:** TBD

## Detailed Results

EOF

# Function to test a command
test_command() {
    local category="$1"
    local command="$2"
    local description="$3"
    local expected_behavior="$4"

    TOTAL_COMMANDS=$((TOTAL_COMMANDS + 1))

    echo -e "${BLUE}Testing:${NC} $command"
    echo "  Description: $description"

    # Run command and capture output
    if output=$($ARX_BIN $command 2>&1); then
        # Command succeeded, check for placeholder indicators
        if echo "$output" | grep -qE "(placeholder|fake|mock|TODO|FIXME|not implemented)"; then
            echo -e "  ${YELLOW}Status: PLACEHOLDER${NC}"
            echo "  Output shows placeholder/fake data"
            PLACEHOLDER_COMMANDS=$((PLACEHOLDER_COMMANDS + 1))
            status="⚠️ PLACEHOLDER"
        else
            echo -e "  ${GREEN}Status: WORKING${NC}"
            WORKING_COMMANDS=$((WORKING_COMMANDS + 1))
            status="✅ WORKING"
        fi
    else
        # Command failed
        if echo "$output" | grep -qE "(not available|not initialized|not found|database connection failed)"; then
            echo -e "  ${YELLOW}Status: NEEDS SETUP${NC}"
            echo "  Requires database or configuration"
            FAILING_COMMANDS=$((FAILING_COMMANDS + 1))
            status="🔧 NEEDS SETUP"
        else
            echo -e "  ${RED}Status: FAILING${NC}"
            FAILING_COMMANDS=$((FAILING_COMMANDS + 1))
            status="❌ FAILING"
        fi
    fi

    # Append to results file
    cat >> "$RESULTS_FILE" << EOF

### $category: \`$command\`

**Status:** $status

**Description:** $description

**Expected Behavior:** $expected_behavior

<details>
<summary>Command Output</summary>

\`\`\`
$output
\`\`\`

</details>

EOF

    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing System Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_command "System" "version" \
    "Show version information" \
    "Displays version number, build time, commit hash"

test_command "System" "health" \
    "Check system health" \
    "Shows database, cache, and service status"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Building Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_command "Building" "building list" \
    "List all buildings" \
    "Shows table of buildings with IDs, names, addresses"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing BAS Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_command "BAS" "bas --help" \
    "Show BAS command help" \
    "Displays BAS subcommands and usage"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Repository/Version Control"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_command "Repository" "repo --help" \
    "Show repository command help" \
    "Displays repo subcommands and usage"

test_command "Branch" "branch --help" \
    "Show branch command help" \
    "Displays branch subcommands and usage"

test_command "Pull Request" "pr --help" \
    "Show PR command help" \
    "Displays PR subcommands and usage"

test_command "Issue" "issue --help" \
    "Show issue command help" \
    "Displays issue subcommands and usage"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Path-Based Queries"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_command "Path Query" "get --help" \
    "Show get command help" \
    "Displays path query usage and examples"

test_command "Path Query" "query --help" \
    "Show query command help" \
    "Displays advanced query options"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Audit Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Working Commands:${NC} $WORKING_COMMANDS"
echo -e "${YELLOW}⚠️  Placeholder Commands:${NC} $PLACEHOLDER_COMMANDS"
echo -e "${RED}❌ Failing Commands:${NC} $FAILING_COMMANDS"
echo -e "Total Commands Tested: $TOTAL_COMMANDS"
echo ""
echo "Detailed results saved to: $RESULTS_FILE"
echo ""

# Update summary in results file
sed -i.bak "s/TBD/$TOTAL_COMMANDS/; s/TBD/$WORKING_COMMANDS/; s/TBD/$PLACEHOLDER_COMMANDS/" "$RESULTS_FILE" 2>/dev/null || \
    perl -pi -e "s/TBD/$TOTAL_COMMANDS/g; s/TBD/$WORKING_COMMANDS/g; s/TBD/$PLACEHOLDER_COMMANDS/g" "$RESULTS_FILE"

# Generate recommendations
cat >> "$RESULTS_FILE" << 'EOF'

## Recommendations

### High Priority Wiring Tasks

1. **Commands with Placeholder Data** - Replace hardcoded responses with real database queries
2. **Commands Requiring Setup** - Document setup requirements and create test data
3. **Path-Based Queries** - Verify end-to-end functionality with test database

### Next Steps

1. Set up test database with sample data
2. Test path-based equipment queries with real data
3. Wire placeholder commands to use cases
4. Add integration tests for working workflows

EOF

echo "Run: cat $RESULTS_FILE"
echo ""

