# Authentication & Connection

The Arxos CLI uses a secure authentication system that supports organization-based access control and building-specific permissions.

## Authentication

### Initial Setup

```bash
# Login to your organization
arxos auth login --org="salesforce-tower"

# Interactive login (opens browser)
arxos auth login --interactive

# Login with API key
arxos auth login --api-key="arxs_1234567890abcdef"
```

### Token Management

```bash
# Check current authentication status
arxos auth status

# Get current token info
arxos auth token info

# Refresh expired token
arxos auth token refresh

# Logout
arxos auth logout
```

### Organization Management

```bash
# List available organizations
arxos auth orgs list

# Switch organization
arxos auth org switch --org="different-org"

# View current organization permissions
arxos auth permissions
```

## Building Connection

### Connection Syntax

The Arxos CLI uses a URI-based connection system:

```
building://[organization]/[building-name]/[optional-scope]
```

Examples:
```bash
# Connect to entire building
arxos connect building://salesforce-tower/sf-main

# Connect to specific floor
arxos connect building://salesforce-tower/sf-main/floor-45

# Connect to specific system
arxos connect building://salesforce-tower/sf-main/electrical
```

### Connection Management

```bash
# List available buildings
arxos buildings list

# Show current connection
arxos connection status

# Connect to building
arxos connect building://org/building-name

# Disconnect
arxos disconnect

# Connection with specific permissions
arxos connect building://org/building --mode=read-only
```

### Connection Options

```bash
# Read-only connection
arxos connect building://org/building --read-only

# Specify coordinate system
arxos connect building://org/building --coordinates=imperial

# Set cache preferences
arxos connect building://org/building --cache=aggressive

# Development mode (bypass some validations)
arxos connect building://org/building --dev-mode
```

## Authentication Configuration

### Config File Location

The Arxos CLI stores configuration in:
- Linux/macOS: `~/.arxos/config.json`
- Windows: `%USERPROFILE%\.arxos\config.json`

### Sample Configuration

```json
{
  "auth": {
    "current_org": "salesforce-tower",
    "tokens": {
      "salesforce-tower": {
        "access_token": "arxs_...",
        "refresh_token": "arxs_refresh_...",
        "expires_at": "2024-12-31T23:59:59Z"
      }
    }
  },
  "connection": {
    "current": "building://salesforce-tower/sf-main",
    "preferences": {
      "coordinate_system": "imperial",
      "cache_level": "building",
      "default_format": "json"
    }
  }
}
```

## Permissions System

### Permission Levels

1. **Read-Only**: Query and view building data
2. **Contributor**: Modify object properties, create new objects
3. **Structural**: Make structural modifications, move load-bearing elements
4. **Admin**: Full building management, user permissions, system configuration

### Permission Scopes

```bash
# View your permissions
arxos auth permissions

# Example output:
# Building: salesforce-tower/sf-main
# - structural: read-only
# - electrical: contributor  
# - mechanical: contributor
# - architectural: contributor
# - admin: false
```

### Permission Validation

The CLI validates permissions before executing commands:

```bash
# This will fail if you don't have structural permissions
arxos modify beam:B-101 load-capacity=5000lbs
# Error: Insufficient permissions. Requires: structural.contributor

# Check permission before running
arxos auth can-execute "modify beam:B-101 load-capacity=5000lbs"
```

## Multi-Building Workflows

### Working with Multiple Buildings

```bash
# List all accessible buildings
arxos buildings list --org=all

# Quick building switch
arxos use building://different-org/other-building

# Run command against specific building without switching
arxos query "outlets WHERE voltage=120" --building=other-building

# Cross-building queries (if permissions allow)
arxos compare buildings --building1=sf-main --building2=sf-north
```

## Security Features

### API Key Management

```bash
# Generate new API key
arxos auth api-key create --name="automation-scripts"

# List API keys
arxos auth api-key list

# Revoke API key
arxos auth api-key revoke --key-id="key_123"
```

### Audit Trail

All authentication events are logged:

```bash
# View authentication history
arxos auth audit

# View building access history
arxos connection audit
```

### Session Management

```bash
# View active sessions
arxos auth sessions

# Terminate all other sessions
arxos auth sessions terminate-others

# Set session timeout
arxos config set session-timeout=8h
```

## Troubleshooting Authentication

### Common Issues

**Token Expired:**
```bash
# Refresh token automatically
arxos auth token refresh

# Or re-login
arxos auth login
```

**Permission Denied:**
```bash
# Check your permissions
arxos auth permissions

# Request access from building admin
arxos request-access --building=sf-main --level=contributor
```

**Connection Failed:**
```bash
# Check building availability
arxos buildings list

# Test connection
arxos connection test
```

### Environment Variables

Override config with environment variables:

```bash
export ARXOS_ORG="my-org"
export ARXOS_BUILDING="building-name" 
export ARXOS_API_KEY="arxs_..."
export ARXOS_ENDPOINT="https://api.arxos.io"
```