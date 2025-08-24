# Arxos Configuration

Centralized configuration for all Arxos platform components.

## Directory Structure

```
config/
├── frontend/           # Web UI configuration
│   ├── config.js      # Main frontend config with runtime updates
│   └── .env.example   # Environment variables template
├── backend/           # Backend server configuration  
│   ├── server.yaml    # Main server configuration
│   ├── server.development.yaml  # Development overrides
│   ├── server.production.yaml   # Production overrides
│   └── .env.example   # Environment variables template
└── cli/               # CLI tool configuration
    └── config.template.yaml  # User config template
```

## Configuration Hierarchy

Configuration is loaded in the following order (later overrides earlier):

1. **Default values** (hardcoded in application)
2. **Base configuration file** (e.g., `server.yaml`)
3. **Environment-specific file** (e.g., `server.production.yaml`)
4. **Environment variables** (highest priority)

## Component Configurations

### Frontend (`/frontend`)

The web UI configuration managed through:
- **config.js**: Runtime configuration with environment detection
- **Environment variables**: Override via `.env.local` (create from `.env.example`)

```javascript
// Access configuration in frontend code
const apiUrl = ARXOS_CONFIG.get('api.baseUrl');
const isAIEnabled = ARXOS_CONFIG.isFeatureEnabled('enableAI');
```

### Backend (`/backend`)

Server configuration using YAML with environment overrides:
- **server.yaml**: Complete configuration with all options
- **server.{env}.yaml**: Environment-specific overrides
- **.env**: Environment variables (create from `.env.example`)

```bash
# Start server with specific environment
ENV=production ./arxos-server

# Or use environment variable
ARXOS_SERVER_PORT=8080 ./arxos-server
```

### CLI (`/cli`)

User configuration for the CLI tool:
- Copy `config.template.yaml` to `~/.arxos/config.yaml`
- Customize for your environment
- Use profiles for multiple environments

```bash
# Use specific profile
arxos --profile production query select "*"

# Override with environment variable
ARXOS_CLI_BACKEND_URL=https://api.arxos.io arxos query select "*"
```

## Environment Variables

### Naming Convention

- Backend: `ARXOS_<SECTION>_<KEY>`
  - Example: `ARXOS_SERVER_PORT=8080`
- Frontend: `REACT_APP_<KEY>`
  - Example: `REACT_APP_API_URL=https://api.arxos.io`
- CLI: `ARXOS_CLI_<SECTION>_<KEY>`
  - Example: `ARXOS_CLI_BACKEND_URL=https://api.arxos.io`

### Common Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=arxos
DB_PASSWORD=secure-password

# Authentication
JWT_SECRET=long-random-string
ADMIN_PASSWORD=secure-admin-password

# Storage
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=arxos-storage

# AI Service
OPENAI_API_KEY=your-openai-key
```

## Configuration by Environment

### Development

- Mock AI enabled
- Debug logging
- CORS open for localhost
- No TLS required
- Auth bypass available
- Sample data seeding

### Staging

- Real services
- Info-level logging  
- CORS for staging domains
- TLS optional
- Full auth required
- No sample data

### Production

- All services enabled
- Minimal logging
- Strict CORS
- TLS required
- Full auth required
- Monitoring enabled
- Backups enabled

## Security Best Practices

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use environment variables
   - Use secret management services

2. **Rotate secrets regularly**
   - JWT secrets
   - API keys
   - Database passwords

3. **Use strong defaults**
   - Require auth by default
   - Use TLS in production
   - Enable rate limiting

4. **Separate environments**
   - Different databases
   - Different API keys
   - Different storage buckets

## Adding New Configuration

### 1. Backend Configuration

Add to `server.yaml`:
```yaml
my_feature:
  enabled: true
  option: "value"
```

Access in Go code:
```go
viper.GetBool("my_feature.enabled")
viper.GetString("my_feature.option")
```

### 2. Frontend Configuration

Add to `config.js`:
```javascript
const defaultConfig = {
  myFeature: {
    enabled: true,
    option: 'value'
  }
};
```

Access in JavaScript:
```javascript
const enabled = ARXOS_CONFIG.get('myFeature.enabled');
```

### 3. CLI Configuration

Add to `config.template.yaml`:
```yaml
my_feature:
  enabled: true
  option: "value"
```

Access in Go code:
```go
cfg := config.Get()
enabled := cfg.MyFeature.Enabled
```

## Validation

Configuration is validated on startup:
- Required fields must be present
- Types must match expected
- Ranges must be valid
- Connections must work

## Monitoring Configuration

View current configuration (sanitized):
```bash
# CLI
arxos config show

# API endpoint
GET /api/v1/admin/config

# Health check includes config status
GET /health
```

## Troubleshooting

### Configuration not loading

1. Check file exists and is readable
2. Validate YAML/JSON syntax
3. Check environment variable naming
4. Review logs for errors

### Wrong values being used

1. Check configuration hierarchy
2. Verify environment detection
3. Check for typos in keys
4. Use debug logging to see loaded values

### Performance issues

1. Adjust worker counts
2. Tune connection pools
3. Configure caching
4. Set appropriate timeouts

## Migration Guide

When updating configuration:

1. Add new fields with defaults
2. Mark deprecated fields
3. Provide migration script if needed
4. Update documentation
5. Test all environments

## Support

For configuration help:
- Check logs: `~/.arxos/logs/`
- Run diagnostics: `arxos diagnose config`
- Contact support with config hash: `arxos config hash`