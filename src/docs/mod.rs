//! API documentation

use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

/// Simple OpenAPI-style documentation endpoint
pub async fn api_docs() -> Json<Value> {
    Json(json!({
        "openapi": "3.0.0",
        "info": {
            "title": "ArxOS API",
            "version": "1.0.0",
            "description": "Buildings as Queryable Databases - REST API for building infrastructure management"
        },
        "servers": [
            {
                "url": "/api",
                "description": "ArxOS API v1"
            }
        ],
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "System health status"
                        }
                    }
                }
            },
            "/api/objects": {
                "get": {
                    "summary": "List building objects",
                    "security": [{"api_key": []}],
                    "responses": {
                        "200": {
                            "description": "List of building objects"
                        }
                    }
                },
                "post": {
                    "summary": "Create building object",
                    "security": [{"api_key": []}],
                    "responses": {
                        "201": {
                            "description": "Object created successfully"
                        }
                    }
                }
            },
            "/api/events": {
                "get": {
                    "summary": "Server-sent events stream",
                    "security": [{"api_key": []}],
                    "responses": {
                        "200": {
                            "description": "Event stream"
                        }
                    }
                }
            },
            "/api/webhooks": {
                "get": {
                    "summary": "List webhooks",
                    "security": [{"api_key": []}]
                },
                "post": {
                    "summary": "Create webhook",
                    "security": [{"api_key": []}]
                }
            },
            "/api/bulk/update": {
                "post": {
                    "summary": "Bulk update operation",
                    "security": [{"api_key": []}]
                }
            },
            "/api/bulk/delete": {
                "post": {
                    "summary": "Bulk delete operation", 
                    "security": [{"api_key": []}]
                }
            }
        },
        "components": {
            "securitySchemes": {
                "api_key": {
                    "type": "apiKey",
                    "name": "X-API-Key",
                    "in": "header"
                }
            }
        }
    }))
}

/// Simple documentation UI
pub async fn docs_ui() -> axum::response::Html<&'static str> {
    axum::response::Html(r#"
<!DOCTYPE html>
<html>
<head>
    <title>ArxOS API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .endpoint { margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; background: #f8f9fa; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: bold; color: white; }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        .patch { background: #fca130; }
        .delete { background: #f93e3e; }
        code { background: #f1f1f1; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>ArxOS API Documentation</h1>
    <p>Buildings as Queryable Databases - REST API v1.0.0</p>
    
    <h2>Authentication</h2>
    <p>All API requests require an API key in the <code>X-API-Key</code> header.</p>
    
    <h2>Endpoints</h2>
    
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/health</code>
        <p>System health check and status information</p>
    </div>
    
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/objects</code>
        <p>List building objects with optional filtering</p>
    </div>
    
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/objects</code>
        <p>Create a new building object</p>
    </div>
    
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/events</code>
        <p>Server-sent events stream for real-time updates</p>
    </div>
    
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/webhooks</code>
        <p>List registered webhooks</p>
    </div>
    
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/bulk/update</code>
        <p>Perform bulk update operations on multiple objects</p>
    </div>
    
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/bulk/delete</code>
        <p>Perform bulk delete operations on multiple objects</p>
    </div>
    
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/objects/:id/history</code>
        <p>Get change history for a specific object</p>
    </div>
    
    <h2>Example Usage</h2>
    <pre><code>curl -H "X-API-Key: your-api-key" http://localhost:3000/api/health</code></pre>
    
    <p><a href="/api-docs/openapi.json">Download OpenAPI JSON specification</a></p>
</body>
</html>
    "#)
}

/// Create documentation routes
pub fn docs_routes() -> Router {
    Router::new()
        .route("/docs", get(docs_ui))
        .route("/api-docs/openapi.json", get(api_docs))
}