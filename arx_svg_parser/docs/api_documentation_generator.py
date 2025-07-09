#!/usr/bin/env python3
"""
API Documentation Generator

Automatically generates comprehensive OpenAPI/Swagger documentation for all Arxos API endpoints.
Includes request/response examples, error codes, authentication requirements, and performance expectations.
"""

import json
import yaml
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import inspect
import ast
import re

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APIDocumentationGenerator:
    """Automated API documentation generator for Arxos platform."""
    
    def __init__(self, output_dir: str = "docs/api"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # API specification
        self.openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Arxos SVG-BIM API",
                "description": "Comprehensive API for SVG to BIM conversion and building management",
                "version": "1.0.0",
                "contact": {
                    "name": "Arxos Platform",
                    "url": "https://arxos.com",
                    "email": "api@arxos.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.arxos.com",
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "tags": []
        }
        
        # Endpoint definitions
        self.endpoints = {
            "export": {
                "description": "Export and interoperability endpoints",
                "endpoints": [
                    {
                        "path": "/api/v1/export/create-job",
                        "method": "POST",
                        "summary": "Create export job",
                        "description": "Create a new export job for building data",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    },
                                    "example": {
                                        "building_id": "BUILDING_001",
                                        "format": "ifc_lite",
                                        "options": {
                                            "output_path": "exports/building.ifc",
                                            "include_metadata": True
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Export job created successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ExportJobResponse"
                                        }
                                    }
                                }
                            },
                            "400": {
                                "description": "Invalid request data",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Authentication required",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            },
                            "500": {
                                "description": "Internal server error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/jobs",
                        "method": "GET",
                        "summary": "List export jobs",
                        "description": "List all export jobs, optionally filtered by building ID",
                        "parameters": [
                            {
                                "name": "building_id",
                                "in": "query",
                                "description": "Filter jobs by building ID",
                                "required": False,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of export jobs",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/ExportJobResponse"
                                            }
                                        }
                                    }
                                }
                            },
                            "401": {
                                "description": "Authentication required",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/jobs/{job_id}",
                        "method": "GET",
                        "summary": "Get export job status",
                        "description": "Get the status of a specific export job",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "description": "Export job ID",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Export job details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ExportJobResponse"
                                        }
                                    }
                                }
                            },
                            "404": {
                                "description": "Export job not found",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/jobs/{job_id}",
                        "method": "DELETE",
                        "summary": "Cancel export job",
                        "description": "Cancel a specific export job",
                        "parameters": [
                            {
                                "name": "job_id",
                                "in": "path",
                                "description": "Export job ID",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Export job cancelled successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {
                                                    "type": "string",
                                                    "example": "Export job cancelled successfully"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "404": {
                                "description": "Export job not found",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/statistics",
                        "method": "GET",
                        "summary": "Get export statistics",
                        "description": "Get comprehensive export statistics and metrics",
                        "responses": {
                            "200": {
                                "description": "Export statistics",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ExportStatisticsResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/export-ifc-lite",
                        "method": "POST",
                        "summary": "Export to IFC-lite",
                        "description": "Export building data to IFC-lite format for BIM interoperability",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "IFC-lite file download",
                                "content": {
                                    "application/octet-stream": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            },
                            "400": {
                                "description": "Invalid request or export failed",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ErrorResponse"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/export-gltf",
                        "method": "POST",
                        "summary": "Export to glTF",
                        "description": "Export building data to glTF format for 3D visualization",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "glTF file download",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/export-ascii-bim",
                        "method": "POST",
                        "summary": "Export to ASCII-BIM",
                        "description": "Export building data to ASCII-BIM format for human-readable representation",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "ASCII-BIM file download",
                                "content": {
                                    "text/plain": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/export-geojson",
                        "method": "POST",
                        "summary": "Export to GeoJSON",
                        "description": "Export building data to GeoJSON format for spatial data and GIS integration",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "GeoJSON file download",
                                "content": {
                                    "application/geo+json": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/export-excel",
                        "method": "POST",
                        "summary": "Export to Excel",
                        "description": "Export building data to Excel format for data analysis and reporting",
                        "request_body": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ExportRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Excel file download",
                                "content": {
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                                        "schema": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        },
                        "security": [{"bearerAuth": []}]
                    },
                    {
                        "path": "/api/v1/export/formats",
                        "method": "GET",
                        "summary": "Get supported formats",
                        "description": "Get list of supported export formats",
                        "responses": {
                            "200": {
                                "description": "List of supported formats",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "formats": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "value": {"type": "string"},
                                                            "name": {"type": "string"},
                                                            "description": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    {
                        "path": "/api/v1/export/statuses",
                        "method": "GET",
                        "summary": "Get export statuses",
                        "description": "Get list of export job status values",
                        "responses": {
                            "200": {
                                "description": "List of export statuses",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "statuses": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "value": {"type": "string"},
                                                            "name": {"type": "string"},
                                                            "description": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        # Schema definitions
        self.schemas = {
            "ExportRequest": {
                "type": "object",
                "required": ["building_id", "format"],
                "properties": {
                    "building_id": {
                        "type": "string",
                        "description": "Building ID to export",
                        "example": "BUILDING_001"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["ifc_lite", "gltf", "ascii_bim", "excel", "parquet", "geojson", "json", "xml", "csv", "pdf"],
                        "description": "Export format",
                        "example": "ifc_lite"
                    },
                    "options": {
                        "type": "object",
                        "description": "Export options",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Output file path",
                                "example": "exports/building.ifc"
                            },
                            "include_metadata": {
                                "type": "boolean",
                                "description": "Include metadata in export",
                                "example": True
                            },
                            "compression": {
                                "type": "boolean",
                                "description": "Enable file compression",
                                "example": False
                            },
                            "validation_level": {
                                "type": "string",
                                "enum": ["basic", "standard", "comprehensive"],
                                "description": "Validation level for export",
                                "example": "standard"
                            }
                        }
                    }
                }
            },
            "ExportJobResponse": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Unique job identifier",
                        "example": "550e8400-e29b-41d4-a716-446655440000"
                    },
                    "building_id": {
                        "type": "string",
                        "description": "Building ID",
                        "example": "BUILDING_001"
                    },
                    "format": {
                        "type": "string",
                        "description": "Export format",
                        "example": "ifc_lite"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "processing", "completed", "failed", "cancelled"],
                        "description": "Export job status",
                        "example": "pending"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Job creation timestamp",
                        "example": "2024-12-19T10:30:00Z"
                    },
                    "completed_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Job completion timestamp",
                        "example": "2024-12-19T10:31:00Z"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to exported file",
                        "example": "exports/building_001.ifc"
                    },
                    "error_message": {
                        "type": "string",
                        "description": "Error message if job failed",
                        "example": "Invalid building data"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional job metadata",
                        "properties": {
                            "file_size": {"type": "integer"},
                            "element_count": {"type": "integer"},
                            "processing_time": {"type": "number"}
                        }
                    }
                }
            },
            "ExportStatisticsResponse": {
                "type": "object",
                "properties": {
                    "total_jobs": {
                        "type": "integer",
                        "description": "Total number of export jobs",
                        "example": 150
                    },
                    "by_format": {
                        "type": "object",
                        "description": "Job counts by export format",
                        "properties": {
                            "ifc_lite": {
                                "type": "object",
                                "properties": {
                                    "pending": {"type": "integer"},
                                    "completed": {"type": "integer"},
                                    "failed": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "by_status": {
                        "type": "object",
                        "description": "Job counts by status",
                        "properties": {
                            "pending": {"type": "integer"},
                            "processing": {"type": "integer"},
                            "completed": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "cancelled": {"type": "integer"}
                        }
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Error message",
                        "example": "Invalid request data"
                    },
                    "detail": {
                        "type": "string",
                        "description": "Detailed error information",
                        "example": "Building ID is required"
                    },
                    "code": {
                        "type": "string",
                        "description": "Error code",
                        "example": "VALIDATION_ERROR"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Error timestamp",
                        "example": "2024-12-19T10:30:00Z"
                    }
                }
            }
        }
    
    def generate_openapi_spec(self):
        """Generate complete OpenAPI specification."""
        # Add tags
        for category, info in self.endpoints.items():
            self.openapi_spec["tags"].append({
                "name": category,
                "description": info["description"]
            })
        
        # Add paths
        for category, info in self.endpoints.items():
            for endpoint in info["endpoints"]:
                path = endpoint["path"]
                method = endpoint["method"].lower()
                
                if path not in self.openapi_spec["paths"]:
                    self.openapi_spec["paths"][path] = {}
                
                self.openapi_spec["paths"][path][method] = {
                    "tags": [category],
                    "summary": endpoint["summary"],
                    "description": endpoint["description"],
                    "responses": endpoint["responses"]
                }
                
                # Add parameters
                if "parameters" in endpoint:
                    self.openapi_spec["paths"][path][method]["parameters"] = endpoint["parameters"]
                
                # Add request body
                if "request_body" in endpoint:
                    self.openapi_spec["paths"][path][method]["requestBody"] = endpoint["request_body"]
                
                # Add security
                if "security" in endpoint:
                    self.openapi_spec["paths"][path][method]["security"] = endpoint["security"]
        
        # Add schemas
        self.openapi_spec["components"]["schemas"] = self.schemas
    
    def generate_markdown_docs(self):
        """Generate comprehensive Markdown documentation."""
        docs = []
        
        # Header
        docs.append("# Arxos API Documentation")
        docs.append("")
        docs.append("## Overview")
        docs.append("")
        docs.append("The Arxos API provides comprehensive endpoints for SVG to BIM conversion and building management.")
        docs.append("")
        docs.append("### Base URL")
        docs.append("- Development: `http://localhost:8000`")
        docs.append("- Production: `https://api.arxos.com`")
        docs.append("")
        docs.append("### Authentication")
        docs.append("All API endpoints require JWT Bearer token authentication.")
        docs.append("")
        docs.append("```bash")
        docs.append("Authorization: Bearer <your-jwt-token>")
        docs.append("```")
        docs.append("")
        
        # Endpoints by category
        for category, info in self.endpoints.items():
            docs.append(f"## {category.title()} Endpoints")
            docs.append("")
            docs.append(info["description"])
            docs.append("")
            
            for endpoint in info["endpoints"]:
                docs.append(f"### {endpoint['summary']}")
                docs.append("")
                docs.append(endpoint["description"])
                docs.append("")
                docs.append(f"**Endpoint:** `{endpoint['method']} {endpoint['path']}`")
                docs.append("")
                
                # Parameters
                if "parameters" in endpoint:
                    docs.append("**Parameters:**")
                    docs.append("")
                    for param in endpoint["parameters"]:
                        required = "Required" if param.get("required", False) else "Optional"
                        docs.append(f"- `{param['name']}` ({param['in']}) - {param['description']} ({required})")
                    docs.append("")
                
                # Request body
                if "request_body" in endpoint:
                    docs.append("**Request Body:**")
                    docs.append("")
                    docs.append("```json")
                    if "example" in endpoint["request_body"]["content"]["application/json"]["schema"]:
                        docs.append(json.dumps(endpoint["request_body"]["content"]["application/json"]["schema"]["example"], indent=2))
                    docs.append("```")
                    docs.append("")
                
                # Responses
                docs.append("**Responses:**")
                docs.append("")
                for status_code, response in endpoint["responses"].items():
                    docs.append(f"- `{status_code}` - {response['description']}")
                docs.append("")
                
                # Example
                docs.append("**Example:**")
                docs.append("")
                docs.append("```bash")
                docs.append(f"curl -X {endpoint['method']} \\")
                docs.append(f"  '{endpoint['path']}' \\")
                docs.append("  -H 'Authorization: Bearer <token>' \\")
                docs.append("  -H 'Content-Type: application/json' \\")
                if "request_body" in endpoint:
                    docs.append("  -d '{")
                    if "example" in endpoint["request_body"]["content"]["application/json"]["schema"]:
                        docs.append(json.dumps(endpoint["request_body"]["content"]["application/json"]["schema"]["example"], indent=4).replace("\n", "\n  "))
                    docs.append("  }'")
                docs.append("```")
                docs.append("")
        
        # Error codes
        docs.append("## Error Codes")
        docs.append("")
        docs.append("| Code | Description |")
        docs.append("|------|-------------|")
        docs.append("| 400 | Bad Request - Invalid request data |")
        docs.append("| 401 | Unauthorized - Authentication required |")
        docs.append("| 403 | Forbidden - Insufficient permissions |")
        docs.append("| 404 | Not Found - Resource not found |")
        docs.append("| 429 | Too Many Requests - Rate limit exceeded |")
        docs.append("| 500 | Internal Server Error - Server error |")
        docs.append("")
        
        # Rate limiting
        docs.append("## Rate Limiting")
        docs.append("")
        docs.append("API requests are rate limited to ensure fair usage:")
        docs.append("- **Authenticated users**: 1000 requests per hour")
        docs.append("- **Unauthenticated users**: 100 requests per hour")
        docs.append("- **Export operations**: 100 exports per hour")
        docs.append("")
        
        # Performance
        docs.append("## Performance")
        docs.append("")
        docs.append("Typical response times:")
        docs.append("- **Status queries**: <100ms")
        docs.append("- **Export operations**: <1s for typical buildings")
        docs.append("- **File downloads**: Varies by file size")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_postman_collection(self):
        """Generate Postman collection for API testing."""
        collection = {
            "info": {
                "name": "Arxos API",
                "description": "Complete API collection for Arxos SVG-BIM platform",
                "version": "1.0.0",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "auth_token",
                    "value": "your-jwt-token-here",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Add requests by category
        for category, info in self.endpoints.items():
            category_item = {
                "name": category.title(),
                "item": []
            }
            
            for endpoint in info["endpoints"]:
                request_item = {
                    "name": endpoint["summary"],
                    "request": {
                        "method": endpoint["method"],
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{auth_token}}",
                                "type": "text"
                            },
                            {
                                "key": "Content-Type",
                                "value": "application/json",
                                "type": "text"
                            }
                        ],
                        "url": {
                            "raw": "{{base_url}}" + endpoint["path"],
                            "host": ["{{base_url}}"],
                            "path": endpoint["path"].split("/")[1:]
                        }
                    }
                }
                
                # Add request body
                if "request_body" in endpoint:
                    request_item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(endpoint["request_body"]["content"]["application/json"]["schema"]["example"], indent=2)
                    }
                
                category_item["item"].append(request_item)
            
            collection["item"].append(category_item)
        
        return collection
    
    def save_documentation(self):
        """Save all documentation files."""
        # Generate OpenAPI spec
        self.generate_openapi_spec()
        
        # Save OpenAPI spec
        openapi_file = self.output_dir / "openapi.yaml"
        with open(openapi_file, 'w') as f:
            yaml.dump(self.openapi_spec, f, default_flow_style=False, sort_keys=False)
        
        # Save JSON version
        openapi_json_file = self.output_dir / "openapi.json"
        with open(openapi_json_file, 'w') as f:
            json.dump(self.openapi_spec, f, indent=2)
        
        # Save Markdown docs
        markdown_file = self.output_dir / "api_documentation.md"
        markdown_content = self.generate_markdown_docs()
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)
        
        # Save Postman collection
        postman_file = self.output_dir / "arxos_api_collection.json"
        postman_collection = self.generate_postman_collection()
        with open(postman_file, 'w') as f:
            json.dump(postman_collection, f, indent=2)
        
        print(f"✅ API documentation generated successfully!")
        print(f"📁 Files saved to: {self.output_dir}")
        print(f"   - openapi.yaml: OpenAPI specification")
        print(f"   - openapi.json: OpenAPI specification (JSON)")
        print(f"   - api_documentation.md: Comprehensive API documentation")
        print(f"   - arxos_api_collection.json: Postman collection")

def main():
    """Main function to generate API documentation."""
    print("🚀 Generating Arxos API Documentation...")
    
    generator = APIDocumentationGenerator()
    generator.save_documentation()
    
    print("🎉 API documentation generation completed!")

if __name__ == "__main__":
    main() 