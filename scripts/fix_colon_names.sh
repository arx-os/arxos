#!/bin/bash

# Script to rename all files and directories containing colons
# Windows doesn't allow colons in filenames, so we replace them with underscores

echo "Starting to rename files and directories with colons..."

# First, rename all files (do files before directories to avoid path issues)
echo "Renaming files..."
find /Users/joelpate/repos/arxos -type f -name "*:*" 2>/dev/null | while read -r file; do
    dir=$(dirname "$file")
    old_name=$(basename "$file")
    new_name=$(echo "$old_name" | tr ':' '_')
    
    if [ "$old_name" != "$new_name" ]; then
        echo "Renaming file: $old_name -> $new_name"
        mv "$file" "$dir/$new_name"
    fi
done

# Then rename directories (from deepest to shallowest to avoid path issues)
echo "Renaming directories..."
find /Users/joelpate/repos/arxos -type d -name "*:*" 2>/dev/null | sort -r | while read -r dir; do
    parent=$(dirname "$dir")
    old_name=$(basename "$dir")
    new_name=$(echo "$old_name" | tr ':' '_')
    
    if [ "$old_name" != "$new_name" ]; then
        echo "Renaming directory: $old_name -> $new_name"
        mv "$dir" "$parent/$new_name"
    fi
done

echo "Completed renaming files and directories with colons."

# Update any references in configuration files
echo "Updating references in configuration files..."

# Update arxos.yml files
find /Users/joelpate/repos/arxos -name "arxos.yml" -o -name "*.yaml" -o -name "*.yml" 2>/dev/null | while read -r file; do
    if grep -q "building:" "$file" 2>/dev/null; then
        echo "Updating references in: $file"
        sed -i.bak 's/building:/building_/g' "$file"
        rm "${file}.bak"
    fi
done

# Update Go source files that might reference building:demo or building:hq
find /Users/joelpate/repos/arxos -name "*.go" 2>/dev/null | while read -r file; do
    if grep -q "building:" "$file" 2>/dev/null; then
        echo "Updating references in: $file"
        sed -i.bak 's/building:demo/building_demo/g' "$file"
        sed -i.bak 's/building:hq/building_hq/g' "$file"
        rm "${file}.bak"
    fi
done

echo "Completed updating references."
echo "All colons in filenames have been replaced with underscores."