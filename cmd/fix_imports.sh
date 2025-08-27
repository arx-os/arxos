#!/bin/bash

# Fix imports in cache/cache.go
sed -i '' 's|"github.com/arxos/arxos/core|// "github.com/arxos/arxos/core|g' commands/cache/cache.go

# Fix imports in support/jobs.go  
sed -i '' 's|"github.com/arxos/arxos/cmd|// "github.com/arxos/arxos/cmd|g' commands/support/jobs.go

# Fix imports in gitops/*.go
for file in commands/gitops/*.go; do
    sed -i '' 's|"github.com/arxos/arxos/core|// "github.com/arxos/arxos/core|g' "$file"
done

# Fix imports in deploy/*.go
for file in commands/deploy/*.go; do
    sed -i '' 's|"github.com/arxos/core|// "github.com/arxos/core|g' "$file"
done

# Fix imports in state/*.go
for file in commands/state/*.go; do
    sed -i '' 's|"github.com/arxos/core|// "github.com/arxos/core|g' "$file"
done

echo "Imports fixed. Now commenting out commands that depend on these imports..."

# Also need to comment out the commands that use these packages in root.go