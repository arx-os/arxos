package graphql

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/graphql-go/graphql"
	"github.com/graphql-go/graphql/language/location"
)

// Handler handles GraphQL requests
type Handler struct {
	schema *Schema
	logger domain.Logger
}

// GraphQLRequest represents a GraphQL request
type GraphQLRequest struct {
	Query         string         `json:"query"`
	Variables     map[string]any `json:"variables"`
	OperationName string         `json:"operationName"`
}

// GraphQLResponse represents a GraphQL response
type GraphQLResponse struct {
	Data       any            `json:"data,omitempty"`
	Errors     []GraphQLError `json:"errors,omitempty"`
	Extensions map[string]any `json:"extensions,omitempty"`
}

// GraphQLError represents a GraphQL error
type GraphQLError struct {
	Message    string          `json:"message"`
	Locations  []ErrorLocation `json:"locations,omitempty"`
	Path       []any           `json:"path,omitempty"`
	Extensions map[string]any  `json:"extensions,omitempty"`
}

// ErrorLocation represents the location of an error
type ErrorLocation struct {
	Line   int `json:"line"`
	Column int `json:"column"`
}

// NewHandler creates a new GraphQL handler
func NewHandler(schema *Schema, logger domain.Logger) *Handler {
	return &Handler{
		schema: schema,
		logger: logger,
	}
}

// ServeHTTP handles HTTP requests for GraphQL
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		h.logger.Debug("GraphQL request completed",
			"method", r.Method,
			"path", r.URL.Path,
			"duration", time.Since(start),
		)
	}()

	// Set CORS headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

	// Handle preflight requests
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Only allow GET and POST methods
	if r.Method != "GET" && r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse request
	var req GraphQLRequest
	var err error

	if r.Method == "GET" {
		req, err = h.parseGetRequest(r)
	} else {
		req, err = h.parsePostRequest(r)
	}

	if err != nil {
		h.logger.Error("Failed to parse GraphQL request", "error", err)
		h.sendErrorResponse(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	// Execute GraphQL query
	result := h.executeQuery(r.Context(), req)

	// Send response
	h.sendResponse(w, result)
}

// parseGetRequest parses a GET request
func (h *Handler) parseGetRequest(r *http.Request) (GraphQLRequest, error) {
	query := r.URL.Query().Get("query")
	if query == "" {
		return GraphQLRequest{}, fmt.Errorf("query parameter is required")
	}

	var variables map[string]any
	if vars := r.URL.Query().Get("variables"); vars != "" {
		if err := json.Unmarshal([]byte(vars), &variables); err != nil {
			return GraphQLRequest{}, fmt.Errorf("invalid variables: %v", err)
		}
	}

	return GraphQLRequest{
		Query:         query,
		Variables:     variables,
		OperationName: r.URL.Query().Get("operationName"),
	}, nil
}

// parsePostRequest parses a POST request
func (h *Handler) parsePostRequest(r *http.Request) (GraphQLRequest, error) {
	// Check content type
	contentType := r.Header.Get("Content-Type")
	if contentType != "application/json" && contentType != "application/graphql" {
		return GraphQLRequest{}, fmt.Errorf("unsupported content type: %s", contentType)
	}

	var req GraphQLRequest

	if contentType == "application/graphql" {
		// Handle raw GraphQL query
		body := make([]byte, r.ContentLength)
		if _, err := r.Body.Read(body); err != nil {
			return GraphQLRequest{}, fmt.Errorf("failed to read body: %v", err)
		}
		req.Query = string(body)
	} else {
		// Handle JSON request
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			return GraphQLRequest{}, fmt.Errorf("invalid JSON: %v", err)
		}
	}

	if req.Query == "" {
		return GraphQLRequest{}, fmt.Errorf("query is required")
	}

	return req, nil
}

// executeQuery executes a GraphQL query
func (h *Handler) executeQuery(ctx context.Context, req GraphQLRequest) *graphql.Result {
	// Add request context
	params := graphql.Params{
		Schema:         *h.schema.schema,
		RequestString:  req.Query,
		VariableValues: req.Variables,
		OperationName:  req.OperationName,
		Context:        ctx,
	}

	result := graphql.Do(params)

	// Log query execution
	if len(result.Errors) > 0 {
		h.logger.Error("GraphQL query errors", "errors", result.Errors)
	} else {
		h.logger.Debug("GraphQL query executed successfully")
	}

	return result
}

// sendResponse sends a GraphQL response
func (h *Handler) sendResponse(w http.ResponseWriter, result *graphql.Result) {
	w.Header().Set("Content-Type", "application/json")

	response := GraphQLResponse{
		Data: result.Data,
	}

	// Convert GraphQL errors
	if len(result.Errors) > 0 {
		response.Errors = make([]GraphQLError, len(result.Errors))
		for i, err := range result.Errors {
			response.Errors[i] = GraphQLError{
				Message:   err.Message,
				Locations: convertErrorLocations(err.Locations),
				Path:      err.Path,
			}
		}
	}

	// Add extensions
	if result.Extensions != nil {
		response.Extensions = result.Extensions
	}

	// Send response
	if err := json.NewEncoder(w).Encode(response); err != nil {
		h.logger.Error("Failed to encode GraphQL response", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// sendErrorResponse sends an error response
func (h *Handler) sendErrorResponse(w http.ResponseWriter, message string, statusCode int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	response := GraphQLResponse{
		Errors: []GraphQLError{
			{
				Message: message,
			},
		},
	}

	json.NewEncoder(w).Encode(response)
}

// convertErrorLocations converts GraphQL error locations
func convertErrorLocations(locations []location.SourceLocation) []ErrorLocation {
	if len(locations) == 0 {
		return nil
	}

	result := make([]ErrorLocation, len(locations))
	for i, loc := range locations {
		result[i] = ErrorLocation{
			Line:   loc.Line,
			Column: loc.Column,
		}
	}
	return result
}

// IntrospectionHandler handles GraphQL introspection queries
func (h *Handler) IntrospectionHandler(w http.ResponseWriter, r *http.Request) {
	// GraphQL introspection query
	introspectionQuery := `
		query IntrospectionQuery {
			__schema {
				queryType { name }
				mutationType { name }
				subscriptionType { name }
				types {
					...FullType
				}
				directives {
					name
					description
					locations
					args {
						...InputValue
					}
				}
			}
		}

		fragment FullType on __Type {
			kind
			name
			description
			fields(includeDeprecated: true) {
				name
				description
				args {
					...InputValue
				}
				type {
					...TypeRef
				}
				isDeprecated
				deprecationReason
			}
			inputFields {
				...InputValue
			}
			interfaces {
				...TypeRef
			}
			enumValues(includeDeprecated: true) {
				name
				description
				isDeprecated
				deprecationReason
			}
			possibleTypes {
				...TypeRef
			}
		}

		fragment InputValue on __InputValue {
			name
			description
			type { ...TypeRef }
			defaultValue
		}

		fragment TypeRef on __Type {
			kind
			name
			ofType {
				kind
				name
				ofType {
					kind
					name
					ofType {
						kind
						name
						ofType {
							kind
							name
							ofType {
								kind
								name
								ofType {
									kind
									name
									ofType {
										kind
										name
									}
								}
							}
						}
					}
				}
			}
		}
	`

	req := GraphQLRequest{
		Query: introspectionQuery,
	}

	result := h.executeQuery(r.Context(), req)
	h.sendResponse(w, result)
}

// PlaygroundHandler serves GraphQL Playground
func (h *Handler) PlaygroundHandler(w http.ResponseWriter, r *http.Request) {
	playgroundHTML := `
<!DOCTYPE html>
<html>
<head>
	<title>ArxOS GraphQL Playground</title>
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/css/index.css" />
	<link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/favicon.png" />
	<script src="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/js/middleware.js"></script>
</head>
<body>
	<div id="root">
		<style>
			body {
				background-color: rgb(23, 42, 58);
				font-family: Open Sans, sans-serif;
				height: 90vh;
			}
			#root {
				height: 100vh;
				width: 100%;
				display: flex;
				align-items: center;
				justify-content: center;
			}
			.loading {
				display: inline-block;
				width: 50px;
				height: 50px;
				border: 3px solid rgba(255,255,255,.3);
				border-radius: 50%;
				border-top-color: #fff;
				animation: spin 1s ease-in-out infinite;
			}
			@keyframes spin {
				to { transform: rotate(360deg); }
			}
		</style>
		<div class="loading"></div>
	</div>
	<script>
		window.addEventListener('load', function (event) {
			const root = document.getElementById('root');
			root.innerHTML = '';
			
			GraphQLPlayground.init(root, {
				endpoint: window.location.origin + '/graphql',
				settings: {
					'editor.theme': 'dark',
					'editor.fontSize': 14,
					'editor.fontFamily': 'Monaco, Consolas, "Courier New", monospace',
					'request.credentials': 'include',
					'general.betaUpdates': false,
					'editor.reuseHeaders': true,
					'tabs.hideQueryPlan': false,
					'editor.formatOnSave': true,
					'editor.codeActionsOnSave': {
						'source.fixAll.eslint': true
					}
				}
			});
		});
	</script>
</body>
</html>
	`

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(playgroundHTML))
}

// GraphQLMiddleware provides GraphQL-specific middleware
func GraphQLMiddleware(logger domain.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Add GraphQL-specific headers
			w.Header().Set("X-GraphQL-Version", "1.0")

			logger.Debug("GraphQL middleware applied",
				"path", r.URL.Path,
				"method", r.Method,
			)

			next.ServeHTTP(w, r)
		})
	}
}
