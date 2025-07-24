#!/bin/bash

# Gin to Chi Migration Script
# This script migrates all Gin handlers to Chi framework

set -e

echo "🚀 Starting Gin to Chi Migration..."

# Create utils directory if it doesn't exist
mkdir -p utils

# List of files to migrate
FILES=(
    "handlers/advanced_ai.go"
    "handlers/ai.go"
    "handlers/ai_handlers.go"
    "handlers/cad.go"
    "handlers/cmms_handlers.go"
    "handlers/collaboration.go"
    "handlers/enterprise.go"
    "handlers/export.go"
    "handlers/notifications.go"
    "handlers/notification_handlers.go"
    "handlers/performance.go"
    "handlers/physics.go"
    "handlers/pipeline.go"
    "services/physics/signal_service.go"
    "tests/notifications_test.go"
    "tests/test_signal_service.go"
)

# Function to migrate a single file
migrate_file() {
    local file=$1
    echo "📝 Migrating $file..."
    
    # Create backup
    cp "$file" "${file}.backup"
    
    # Replace imports
    sed -i 's|"github.com/gin-gonic/gin"|"arx/utils"|g' "$file"
    
    # Replace gin.Context with utils.ChiContext
    sed -i 's/\*gin\.Context/\*utils.ChiContext/g' "$file"
    
    # Replace c.ShouldBindJSON with c.Reader.ShouldBindJSON
    sed -i 's/c\.ShouldBindJSON/c.Reader.ShouldBindJSON/g' "$file"
    
    # Replace c.JSON with c.Writer.JSON
    sed -i 's/c\.JSON(/c.Writer.JSON(/g' "$file"
    
    # Replace c.Param with c.Reader.Param
    sed -i 's/c\.Param(/c.Reader.Param(/g' "$file"
    
    # Replace c.Query with c.Reader.Query
    sed -i 's/c\.Query(/c.Reader.Query(/g' "$file"
    
    # Replace c.GetHeader with c.Reader.GetHeader
    sed -i 's/c\.GetHeader(/c.Reader.GetHeader(/g' "$file"
    
    # Replace gin.H with map[string]interface{}
    sed -i 's/gin\.H{/map[string]interface{}{/g' "$file"
    
    # Replace error responses
    sed -i 's/c\.JSON(http\.StatusBadRequest, map\[string\]interface{}{"error": "\([^"]*\)", "details": err\.Error()})/c.Writer.Error(http.StatusBadRequest, "\1", err.Error())/g' "$file"
    sed -i 's/c\.JSON(http\.StatusInternalServerError, map\[string\]interface{}{"error": "\([^"]*\)", "details": err\.Error()})/c.Writer.Error(http.StatusInternalServerError, "\1", err.Error())/g' "$file"
    
    # Replace router group registration
    sed -i 's/SetupRoutes(router \*gin\.Engine)/RegisterRoutes(router \*utils.ChiRouterGroup)/g' "$file"
    sed -i 's/RegisterRoutes(router \*gin\.RouterGroup)/RegisterRoutes(router \*utils.ChiRouterGroup)/g' "$file"
    
    # Replace router group creation
    sed -i 's/router\.Group(/utils.NewChiRouterGroup(router, /g' "$file"
    
    echo "✅ Migrated $file"
}

# Function to create migration utilities
create_migration_utils() {
    echo "🔧 Creating migration utilities..."
    
    cat > utils/chi_migration.go << 'EOF'
package utils

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
)

// ChiResponseWriter wraps http.ResponseWriter to provide Gin-like JSON response methods
type ChiResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

// NewChiResponseWriter creates a new ChiResponseWriter
func NewChiResponseWriter(w http.ResponseWriter) *ChiResponseWriter {
	return &ChiResponseWriter{
		ResponseWriter: w,
		statusCode:     http.StatusOK,
	}
}

// JSON sends a JSON response with the given status code and data
func (w *ChiResponseWriter) JSON(statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	w.statusCode = statusCode
	
	if data != nil {
		json.NewEncoder(w).Encode(data)
	}
}

// Error sends a JSON error response
func (w *ChiResponseWriter) Error(statusCode int, message string, details ...string) {
	response := map[string]interface{}{
		"error": message,
	}
	
	if len(details) > 0 {
		response["details"] = details[0]
	}
	
	w.JSON(statusCode, response)
}

// GetStatusCode returns the current status code
func (w *ChiResponseWriter) GetStatusCode() int {
	return w.statusCode
}

// ChiRequestReader provides Gin-like request reading methods
type ChiRequestReader struct {
	*http.Request
}

// NewChiRequestReader creates a new ChiRequestReader
func NewChiRequestReader(r *http.Request) *ChiRequestReader {
	return &ChiRequestReader{Request: r}
}

// ShouldBindJSON binds JSON request body to a struct
func (r *ChiRequestReader) ShouldBindJSON(obj interface{}) error {
	return json.NewDecoder(r.Body).Decode(obj)
}

// Param gets a URL parameter by name
func (r *ChiRequestReader) Param(name string) string {
	return chi.URLParam(r.Request, name)
}

// Query gets a query parameter by name
func (r *ChiRequestReader) Query(name string) string {
	return r.URL.Query().Get(name)
}

// QueryInt gets a query parameter as int
func (r *ChiRequestReader) QueryInt(name string) (int, error) {
	val := r.Query(name)
	if val == "" {
		return 0, nil
	}
	return strconv.Atoi(val)
}

// GetHeader gets a request header by name
func (r *ChiRequestReader) GetHeader(name string) string {
	return r.Header.Get(name)
}

// ChiContext provides a Gin-like context for Chi handlers
type ChiContext struct {
	Writer  *ChiResponseWriter
	Reader  *ChiRequestReader
	Request *http.Request
}

// NewChiContext creates a new ChiContext
func NewChiContext(w http.ResponseWriter, r *http.Request) *ChiContext {
	return &ChiContext{
		Writer:  NewChiResponseWriter(w),
		Reader:  NewChiRequestReader(r),
		Request: r,
	}
}

// ChiHandlerFunc is a function type that matches Gin handler signature
type ChiHandlerFunc func(*ChiContext)

// ToChiHandler converts a ChiHandlerFunc to http.HandlerFunc
func ToChiHandler(handler ChiHandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := NewChiContext(w, r)
		handler(ctx)
	}
}

// ChiRouterGroup provides Gin-like router group functionality
type ChiRouterGroup struct {
	router chi.Router
	prefix string
}

// NewChiRouterGroup creates a new ChiRouterGroup
func NewChiRouterGroup(router chi.Router, prefix string) *ChiRouterGroup {
	return &ChiRouterGroup{
		router: router,
		prefix: prefix,
	}
}

// Group creates a new router group
func (g *ChiRouterGroup) Group(prefix string, fn func(*ChiRouterGroup)) {
	subGroup := &ChiRouterGroup{
		router: g.router,
		prefix: g.prefix + prefix,
	}
	fn(subGroup)
}

// POST registers a POST route
func (g *ChiRouterGroup) POST(pattern string, handler ChiHandlerFunc) {
	g.router.Post(g.prefix+pattern, ToChiHandler(handler))
}

// GET registers a GET route
func (g *ChiRouterGroup) GET(pattern string, handler ChiHandlerFunc) {
	g.router.Get(g.prefix+pattern, ToChiHandler(handler))
}

// PUT registers a PUT route
func (g *ChiRouterGroup) PUT(pattern string, handler ChiHandlerFunc) {
	g.router.Put(g.prefix+pattern, ToChiHandler(handler))
}

// DELETE registers a DELETE route
func (g *ChiRouterGroup) DELETE(pattern string, handler ChiHandlerFunc) {
	g.router.Delete(g.prefix+pattern, ToChiHandler(handler))
}

// PATCH registers a PATCH route
func (g *ChiRouterGroup) PATCH(pattern string, handler ChiHandlerFunc) {
	g.router.Patch(g.prefix+pattern, ToChiHandler(handler))
}

// OPTIONS registers an OPTIONS route
func (g *ChiRouterGroup) OPTIONS(pattern string, handler ChiHandlerFunc) {
	g.router.Options(g.prefix+pattern, ToChiHandler(handler))
}

// HEAD registers a HEAD route
func (g *ChiRouterGroup) HEAD(pattern string, handler ChiHandlerFunc) {
	g.router.Head(g.prefix+pattern, ToChiHandler(handler))
}

// ChiEngine provides Gin-like engine functionality
type ChiEngine struct {
	router chi.Router
}

// NewChiEngine creates a new ChiEngine
func NewChiEngine() *ChiEngine {
	return &ChiEngine{
		router: chi.NewRouter(),
	}
}

// Group creates a new router group
func (e *ChiEngine) Group(prefix string, fn func(*ChiRouterGroup)) {
	group := NewChiRouterGroup(e.router, prefix)
	fn(group)
}

// POST registers a POST route
func (e *ChiEngine) POST(pattern string, handler ChiHandlerFunc) {
	e.router.Post(pattern, ToChiHandler(handler))
}

// GET registers a GET route
func (e *ChiEngine) GET(pattern string, handler ChiHandlerFunc) {
	e.router.Get(pattern, ToChiHandler(handler))
}

// PUT registers a PUT route
func (e *ChiEngine) PUT(pattern string, handler ChiHandlerFunc) {
	e.router.Put(pattern, ToChiHandler(handler))
}

// DELETE registers a DELETE route
func (e *ChiEngine) DELETE(pattern string, handler ChiHandlerFunc) {
	e.router.Delete(pattern, ToChiHandler(handler))
}

// PATCH registers a PATCH route
func (e *ChiEngine) PATCH(pattern string, handler ChiHandlerFunc) {
	e.router.Patch(pattern, ToChiHandler(handler))
}

// OPTIONS registers an OPTIONS route
func (e *ChiEngine) OPTIONS(pattern string, handler ChiHandlerFunc) {
	e.router.Options(pattern, ToChiHandler(handler))
}

// HEAD registers a HEAD route
func (e *ChiEngine) HEAD(pattern string, handler ChiHandlerFunc) {
	e.router.Head(pattern, ToChiHandler(handler))
}

// Router returns the underlying chi.Router
func (e *ChiEngine) Router() chi.Router {
	return e.router
}
EOF

    echo "✅ Created migration utilities"
}

# Function to update go.mod
update_go_mod() {
    echo "📦 Updating go.mod..."
    
    # Remove Gin dependency if it exists
    if grep -q "github.com/gin-gonic/gin" go.mod; then
        echo "Removing Gin dependency from go.mod..."
        sed -i '/github.com\/gin-gonic\/gin/d' go.mod
    fi
    
    echo "✅ Updated go.mod"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    go test ./... -v
    echo "✅ Tests completed"
}

# Main migration process
main() {
    echo "🎯 Starting comprehensive Gin to Chi migration..."
    
    # Create migration utilities
    create_migration_utils
    
    # Migrate each file
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            migrate_file "$file"
        else
            echo "⚠️  File $file not found, skipping..."
        fi
    done
    
    # Update go.mod
    update_go_mod
    
    # Run tests
    run_tests
    
    echo "🎉 Migration completed successfully!"
    echo "📋 Summary:"
    echo "   - Migrated ${#FILES[@]} files"
    echo "   - Created migration utilities"
    echo "   - Updated go.mod"
    echo "   - Ran tests"
    echo ""
    echo "🔍 Next steps:"
    echo "   1. Review the migrated code"
    echo "   2. Update any remaining Gin references"
    echo "   3. Test the application thoroughly"
    echo "   4. Remove backup files when satisfied"
}

# Run the migration
main "$@" 