# API Implementation

This directory contains the internal implementation of the ArxOS REST API.

## Structure

- `server.go` - HTTP server setup and configuration
- `*_handlers.go` - HTTP request handlers for different resources
- `*_service.go` - Business logic services
- `middleware.go` - HTTP middleware (auth, CORS, logging, etc.)
- `interfaces.go` - Internal interfaces and contracts

## Purpose

This is the private implementation that:
- Implements the API specification defined in `/api/openapi/`
- Cannot be imported by external packages (Go's `/internal/` convention)
- Contains business logic, database interactions, and request handling

## Running the Server

The API server is started via the CLI command:
```bash
arx serve --port 8080
```

## Note

The public API specification is in `/api/openapi/openapi.yaml`.
This separation ensures implementation details remain private while
the contract remains public.