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