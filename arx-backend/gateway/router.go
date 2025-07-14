package gateway

import (
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/go-chi/chi/v5"
	"go.uber.org/zap"
)

// Router handles request routing to appropriate services
type Router struct {
	config       *Config
	discovery    *ServiceDiscovery
	loadBalancer *LoadBalancer
	logger       *zap.Logger
	mu           sync.RWMutex
	routes       map[string]*Route
}

// NewRouter creates a new router instance
func NewRouter(config *Config) (*Router, error) {
	if config == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}

	logger, err := zap.NewProduction()
	if err != nil {
		return nil, fmt.Errorf("failed to create logger: %w", err)
	}

	discovery, err := NewServiceDiscovery(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create service discovery: %w", err)
	}

	loadBalancer, err := NewLoadBalancer(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create load balancer: %w", err)
	}

	router := &Router{
		config:       config,
		discovery:    discovery,
		loadBalancer: loadBalancer,
		logger:       logger,
		routes:       make(map[string]*Route),
	}

	// Build route map
	if err := router.buildRouteMap(); err != nil {
		return nil, fmt.Errorf("failed to build route map: %w", err)
	}

	return router, nil
}

// RegisterRoutes registers all routes with the chi router
func (r *Router) RegisterRoutes(router chi.Router) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Register health check endpoint
	router.Get("/health", r.healthHandler)
	router.Get("/gateway/health", r.gatewayHealthHandler)

	// Register metrics endpoint
	router.Get("/metrics", r.metricsHandler)

	// Register service routes
	for path, route := range r.routes {
		r.registerRoute(router, path, route)
	}

	// Register catch-all handler for unmatched routes
	router.NotFound(r.notFoundHandler)
}

// registerRoute registers a single route with the chi router
func (r *Router) registerRoute(router chi.Router, path string, route *Route) {
	// Create proxy handler for this route
	handler := r.createProxyHandler(route)

	// Register with all specified methods
	for _, method := range route.Methods {
		switch strings.ToUpper(method) {
		case "GET":
			router.Get(path, handler)
		case "POST":
			router.Post(path, handler)
		case "PUT":
			router.Put(path, handler)
		case "DELETE":
			router.Delete(path, handler)
		case "PATCH":
			router.Patch(path, handler)
		case "OPTIONS":
			router.Options(path, handler)
		case "HEAD":
			router.Head(path, handler)
		default:
			r.logger.Warn("Unknown HTTP method", zap.String("method", method), zap.String("path", path))
		}
	}
}

// createProxyHandler creates a reverse proxy handler for a route
func (r *Router) createProxyHandler(route *Route) http.HandlerFunc {
	return func(w http.ResponseWriter, req *http.Request) {
		start := time.Now()

		// Get service instance from load balancer
		serviceInstance, err := r.loadBalancer.GetNext(route.Service)
		if err != nil {
			r.logger.Error("Failed to get service instance",
				zap.String("service", route.Service),
				zap.Error(err),
			)
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}

		// Create target URL
		targetURL, err := url.Parse(serviceInstance.URL)
		if err != nil {
			r.logger.Error("Failed to parse target URL",
				zap.String("url", serviceInstance.URL),
				zap.Error(err),
			)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}

		// Create reverse proxy
		proxy := httputil.NewSingleHostReverseProxy(targetURL)

		// Customize the proxy director
		originalDirector := proxy.Director
		proxy.Director = func(req *http.Request) {
			originalDirector(req)

			// Add custom headers
			req.Header.Set("X-Forwarded-For", req.RemoteAddr)
			req.Header.Set("X-Forwarded-Proto", req.URL.Scheme)
			req.Header.Set("X-Gateway-Service", route.Service)
			req.Header.Set("X-Gateway-Path", req.URL.Path)

			// Transform request if needed
			if route.Transform != nil {
				r.transformRequest(req, route.Transform)
			}
		}

		// Customize the proxy error handler
		proxy.ErrorHandler = func(w http.ResponseWriter, req *http.Request, err error) {
			r.logger.Error("Proxy error",
				zap.String("service", route.Service),
				zap.String("path", req.URL.Path),
				zap.Error(err),
			)
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
		}

		// Add response modification
		proxy.ModifyResponse = func(resp *http.Response) error {
			// Add response headers
			resp.Header.Set("X-Gateway-Service", route.Service)
			resp.Header.Set("X-Gateway-Response-Time", time.Since(start).String())

			// Transform response if needed
			if route.Transform != nil {
				return r.transformResponse(resp, route.Transform)
			}
			return nil
		}

		// Serve the request
		proxy.ServeHTTP(w, req)

		// Log request
		r.logger.Info("Request served",
			zap.String("service", route.Service),
			zap.String("path", req.URL.Path),
			zap.String("method", req.Method),
			zap.Duration("duration", time.Since(start)),
		)
	}
}

// transformRequest applies request transformations
func (r *Router) transformRequest(req *http.Request, transform *TransformConfig) {
	// Transform headers
	if transform.Headers != nil {
		for key, value := range transform.Headers {
			req.Header.Set(key, value)
		}
	}

	// Transform query parameters
	if transform.Query != nil {
		q := req.URL.Query()
		for key, value := range transform.Query {
			q.Set(key, value)
		}
		req.URL.RawQuery = q.Encode()
	}

	// Note: Body transformation would require reading and modifying the body
	// This is more complex and would need to be implemented based on specific requirements
}

// transformResponse applies response transformations
func (r *Router) transformResponse(resp *http.Response, transform *TransformConfig) error {
	// Transform headers
	if transform.Headers != nil {
		for key, value := range transform.Headers {
			resp.Header.Set(key, value)
		}
	}

	// Note: Body transformation would require reading and modifying the response body
	// This is more complex and would need to be implemented based on specific requirements

	return nil
}

// buildRouteMap builds the internal route map from configuration
func (r *Router) buildRouteMap() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	for serviceName, serviceConfig := range r.config.Services {
		for _, route := range serviceConfig.Routes {
			// Validate route
			if err := r.validateRoute(route, serviceName); err != nil {
				return fmt.Errorf("invalid route for service %s: %w", serviceName, err)
			}

			// Store route
			r.routes[route.Path] = &route
		}
	}

	r.logger.Info("Route map built successfully",
		zap.Int("route_count", len(r.routes)),
	)
	return nil
}

// validateRoute validates a route configuration
func (r *Router) validateRoute(route Route, serviceName string) error {
	if route.Path == "" {
		return fmt.Errorf("path cannot be empty")
	}

	if route.Service == "" {
		return fmt.Errorf("service cannot be empty")
	}

	if len(route.Methods) == 0 {
		return fmt.Errorf("at least one HTTP method must be specified")
	}

	// Validate HTTP methods
	for _, method := range route.Methods {
		switch strings.ToUpper(method) {
		case "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD":
			// Valid method
		default:
			return fmt.Errorf("invalid HTTP method: %s", method)
		}
	}

	return nil
}

// healthHandler handles health check requests
func (r *Router) healthHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"healthy","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `"}`))
}

// gatewayHealthHandler handles gateway-specific health checks
func (r *Router) gatewayHealthHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	// Note: In a real implementation, you'd use a JSON encoder
	w.Write([]byte(`{"status":"healthy","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `"}`))
}

// metricsHandler handles metrics requests
func (r *Router) metricsHandler(w http.ResponseWriter, req *http.Request) {
	// This would return Prometheus metrics
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("# Gateway metrics would be here\n"))
}

// notFoundHandler handles unmatched routes
func (r *Router) notFoundHandler(w http.ResponseWriter, req *http.Request) {
	r.logger.Warn("Route not found",
		zap.String("path", req.URL.Path),
		zap.String("method", req.Method),
		zap.String("remote_addr", req.RemoteAddr),
	)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	w.Write([]byte(`{"error":"route not found","path":"` + req.URL.Path + `"}`))
}

// UpdateConfig updates the router configuration
func (r *Router) UpdateConfig(config *Config) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Update discovery
	if err := r.discovery.UpdateConfig(config); err != nil {
		return fmt.Errorf("failed to update discovery config: %w", err)
	}

	// Update load balancer
	if err := r.loadBalancer.UpdateConfig(config); err != nil {
		return fmt.Errorf("failed to update load balancer config: %w", err)
	}

	// Rebuild route map
	r.config = config
	if err := r.buildRouteMap(); err != nil {
		return fmt.Errorf("failed to rebuild route map: %w", err)
	}

	return nil
}

// GetRoutes returns the current route map
func (r *Router) GetRoutes() map[string]*Route {
	r.mu.RLock()
	defer r.mu.RUnlock()

	routes := make(map[string]*Route)
	for path, route := range r.routes {
		routes[path] = route
	}

	return routes
}

// GetRoute returns a specific route by path
func (r *Router) GetRoute(path string) (*Route, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	route, exists := r.routes[path]
	return route, exists
}
