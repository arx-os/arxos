# API Specifications

This directory contains the API specifications and contracts for ArxOS.

## Structure

- `openapi/` - OpenAPI 3.0 specification for the REST API

## Purpose

These specifications serve as:
- The contract between client and server
- Source for API documentation generation
- Input for client SDK generation
- Validation schemas for requests/responses

## Note

The actual implementation of these APIs is in `/internal/api/`.
This separation follows Go best practices by keeping the contract (specification)
separate from the implementation.