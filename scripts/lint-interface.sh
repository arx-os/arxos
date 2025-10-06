#!/bin/bash
# Custom linter to detect interface{} usage instead of any
# This script is used by golangci-lint as a custom linter

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

# Function to check for interface{} usage
check_interface_usage() {
    local file="$1"
    local errors=0

    # Check for interface{} in function signatures
    if grep -n "interface{}" "$file" >/dev/null 2>&1; then
        while IFS=: read -r line_num line_content; do
            # Skip comments and strings
            if [[ "$line_content" =~ ^[[:space:]]*// ]] || [[ "$line_content" =~ \".*interface\{\}.*\" ]]; then
                continue
            fi

            # Check for interface{} usage
            if [[ "$line_content" =~ interface\{\} ]]; then
                print_error "$file:$line_num: Use 'any' instead of 'interface{}'"
                echo "  $line_content"
                errors=$((errors + 1))
            fi
        done < <(grep -n "interface{}" "$file")
    fi

    return $errors
}

# Function to check for map[string]interface{} usage
check_map_interface_usage() {
    local file="$1"
    local errors=0

    # Check for map[string]interface{} usage
    if grep -n "map\[string\]interface{}" "$file" >/dev/null 2>&1; then
        while IFS=: read -r line_num line_content; do
            # Skip comments and strings
            if [[ "$line_content" =~ ^[[:space:]]*// ]] || [[ "$line_content" =~ \".*map\[string\]interface\{\}.*\" ]]; then
                continue
            fi

            # Check for map[string]interface{} usage
            if [[ "$line_content" =~ map\[string\]interface\{\} ]]; then
                print_error "$file:$line_num: Use 'map[string]any' instead of 'map[string]interface{}'"
                echo "  $line_content"
                errors=$((errors + 1))
            fi
        done < <(grep -n "map\[string\]interface{}" "$file")
    fi

    return $errors
}

# Function to check for []interface{} usage
check_slice_interface_usage() {
    local file="$1"
    local errors=0

    # Check for []interface{} usage
    if grep -n "\[\]interface{}" "$file" >/dev/null 2>&1; then
        while IFS=: read -r line_num line_content; do
            # Skip comments and strings
            if [[ "$line_content" =~ ^[[:space:]]*// ]] || [[ "$line_content" =~ \".*\[\]interface\{\}.*\" ]]; then
                continue
            fi

            # Check for []interface{} usage
            if [[ "$line_content" =~ \[\]interface\{\} ]]; then
                print_error "$file:$line_num: Use '[]any' instead of '[]interface{}'"
                echo "  $line_content"
                errors=$((errors + 1))
            fi
        done < <(grep -n "\[\]interface{}" "$file")
    fi

    return $errors
}

# Function to check for chan interface{} usage
check_chan_interface_usage() {
    local file="$1"
    local errors=0

    # Check for chan interface{} usage
    if grep -n "chan interface{}" "$file" >/dev/null 2>&1; then
        while IFS=: read -r line_num line_content; do
            # Skip comments and strings
            if [[ "$line_content" =~ ^[[:space:]]*// ]] || [[ "$line_content" =~ \".*chan[[:space:]]+interface\{\}.*\" ]]; then
                continue
            fi

            # Check for chan interface{} usage
            if [[ "$line_content" =~ chan[[:space:]]+interface\{\} ]]; then
                print_error "$file:$line_num: Use 'chan any' instead of 'chan interface{}'"
                echo "  $line_content"
                errors=$((errors + 1))
            fi
        done < <(grep -n "chan interface{}" "$file")
    fi

    return $errors
}

# Main function
main() {
    local total_errors=0
    local files_checked=0

    # Check if we're being called by golangci-lint
    if [[ "${1:-}" == "--golangci-lint" ]]; then
        # Called by golangci-lint, expect file paths as arguments
        shift
        for file in "$@"; do
            if [[ -f "$file" && "$file" =~ \.go$ ]]; then
                files_checked=$((files_checked + 1))
                local file_errors=0

                check_interface_usage "$file" || file_errors=$?
                check_map_interface_usage "$file" || file_errors=$?
                check_slice_interface_usage "$file" || file_errors=$?
                check_chan_interface_usage "$file" || file_errors=$?

                total_errors=$((total_errors + file_errors))
            fi
        done

        # Exit with error code if issues found
        if [[ $total_errors -gt 0 ]]; then
            exit 1
        fi
        exit 0
    fi

    # Standalone usage - check all Go files in the project
    print_success "Checking for interface{} usage in Go files..."

    # Find all Go files
    while IFS= read -r -d '' file; do
        files_checked=$((files_checked + 1))
        local file_errors=0

        check_interface_usage "$file" || file_errors=$?
        check_map_interface_usage "$file" || file_errors=$?
        check_slice_interface_usage "$file" || file_errors=$?
        check_chan_interface_usage "$file" || file_errors=$?

        total_errors=$((total_errors + file_errors))
    done < <(find . -name "*.go" -not -path "./vendor/*" -not -path "./.git/*" -print0)

    # Print summary
    echo
    if [[ $total_errors -eq 0 ]]; then
        print_success "No interface{} usage found in $files_checked files!"
    else
        print_error "Found $total_errors interface{} usage issues in $files_checked files"
        echo
        echo "To fix these issues, replace:"
        echo "  interface{} → any"
        echo "  map[string]interface{} → map[string]any"
        echo "  []interface{} → []any"
        echo "  chan interface{} → chan any"
        echo
        echo "You can use this command to find and replace:"
        echo "  find . -name '*.go' -exec sed -i 's/interface{}/any/g' {} +"
        echo "  find . -name '*.go' -exec sed -i 's/map\[string\]interface{}/map[string]any/g' {} +"
        echo "  find . -name '*.go' -exec sed -i 's/\[\]interface{}/[]any/g' {} +"
        echo "  find . -name '*.go' -exec sed -i 's/chan interface{}/chan any/g' {} +"
    fi

    exit $total_errors
}

# Run main function
main "$@"
