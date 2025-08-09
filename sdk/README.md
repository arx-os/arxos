# Arxos SDK Generation

This directory contains the automated SDK generation system for all Arxos platform services. The system generates client SDKs in multiple programming languages from OpenAPI specifications.

## 🚀 Quick Start

### Prerequisites

1. **Node.js** (v18+) - For TypeScript SDK generation
2. **Python** (v3.8+) - For Python SDK generation and main generator
3. **Go** (v1.21+) - For Go SDK generation
4. **Java** (v11+) - For Java SDK generation
5. **.NET** (v6+) - For C# SDK generation
6. **PHP** (v8+) - For PHP SDK generation
7. **OpenAPI Generator CLI** - For code generation

### Installation

```bash
# Install OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli

# Install Python dependencies
pip install pyyaml jinja2

# Install language-specific tools
npm install -g prettier
pip install black
go install golang.org/x/tools/cmd/goimports@latest
```

### Generate All SDKs

```bash
# Generate all SDKs for all services and languages
python scripts/generate_sdks.py

# Generate SDKs for a specific service
python scripts/generate_sdks.py --service arx-backend

# Generate SDKs for a specific language
python scripts/generate_sdks.py --language typescript

# Generate SDK for specific service and language
python scripts/generate_sdks.py --service arx-backend --language typescript
```

### Test Generated SDKs

```bash
# Test all generated SDKs
python scripts/test_sdks.py

# Test specific language SDKs
python scripts/test_sdks.py --language typescript

# Test specific service SDKs
python scripts/test_sdks.py --service arx-backend

# Test specific test type
python scripts/test_sdks.py --type unit
```

## 📁 Project Structure

```
sdk/
├── generator/                 # SDK generation engine
│   ├── generator.py          # Main generator class
│   ├── config/               # Configuration files
│   │   ├── generator.yaml    # Generator configuration
│   │   └── services.yaml     # Service definitions
│   ├── templates/            # Custom templates
│   │   ├── typescript/       # TypeScript templates
│   │   ├── python/          # Python templates
│   │   ├── go/              # Go templates
│   │   ├── java/            # Java templates
│   │   ├── csharp/          # C# templates
│   │   └── php/             # PHP templates
│   └── utils/               # Utility functions
├── generated/                # Generated SDKs
│   ├── typescript/          # TypeScript SDKs
│   ├── python/             # Python SDKs
│   ├── go/                 # Go SDKs
│   ├── java/               # Java SDKs
│   ├── csharp/             # C# SDKs
│   └── php/                # PHP SDKs
├── scripts/                 # Generation and testing scripts
│   ├── generate_sdks.py    # Main generation script
│   └── test_sdks.py        # Testing script
├── tests/                   # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── examples/           # Example applications
└── docs/                   # Documentation
    ├── api/                # API documentation
    ├── sdk/                # SDK documentation
    └── examples/           # Usage examples
```

## 🏗️ Supported Services

### 1. Arx Backend API
- **Description**: Core backend services for Arxos platform
- **Base URL**: `http://localhost:8080/api`
- **Features**: Authentication, BIM Objects, Assets, CMMS, Maintenance, Export, Compliance, Security
- **Endpoints**: 150+ endpoints across 20+ categories

### 2. SVG Parser API
- **Description**: SVG to BIM conversion and management
- **Base URL**: `http://localhost:8082`
- **Features**: SVG Processing, Symbol Recognition, BIM Assembly, Export Interoperability
- **Endpoints**: 20+ endpoints for SVG operations

### 3. CMMS Service API
- **Description**: Computerized Maintenance Management System
- **Base URL**: `http://localhost:8081`
- **Features**: CMMS Integration, Field Mapping, Synchronization, Maintenance Workflows
- **Endpoints**: 30+ endpoints for maintenance operations

### 4. Database Infrastructure API
- **Description**: Database schema management and monitoring
- **Base URL**: `http://localhost:8083`
- **Features**: Schema Management, Migration Tools, Performance Monitoring, Health Checks
- **Endpoints**: 15+ endpoints for database operations

## 🌐 Supported Languages

### TypeScript/JavaScript
- **Generator**: `typescript-fetch`
- **Package Manager**: npm
- **Features**: Type safety, async/await, ES6 modules
- **Package Name**: `@arxos/api-client`

### Python
- **Generator**: `python`
- **Package Manager**: pip
- **Features**: Type hints, async support, pip packaging
- **Package Name**: `arxos-api-client`

### Go
- **Generator**: `go`
- **Package Manager**: go modules
- **Features**: Context support, Go modules, strong typing
- **Package Name**: `github.com/arxos/api-client`

### Java
- **Generator**: `java`
- **Package Manager**: Maven
- **Features**: Bean validation, Optional types, Maven packaging
- **Package Name**: `com.arxos:api-client`

### C#
- **Generator**: `csharp`
- **Package Manager**: NuGet
- **Features**: DateTimeOffset, Collections, .NET 6+
- **Package Name**: `Arxos.ApiClient`

### PHP
- **Generator**: `php`
- **Package Manager**: Composer
- **Features**: DateTime types, Composer packaging
- **Package Name**: `arxos/api-client`

## 🔧 Configuration

### Generator Configuration (`generator/config/generator.yaml`)

```yaml
generator:
  version: "1.0.0"
  output_dir: "../generated"
  template_dir: "./templates"
  validate_specs: true
  format_code: true
  add_examples: true

languages:
  - typescript
  - python
  - go
  - java
  - csharp
  - php

language_configs:
  typescript:
    generator: "typescript-fetch"
    additional_properties:
      supportsES6: true
      npmName: "@arxos/api-client"
      # ... more properties
```

### Service Configuration (`generator/config/services.yaml`)

```yaml
services:
  arx-backend:
    name: "Arx Backend API"
    description: "Core backend services for Arxos platform"
    openapi_spec: "../../arx-docs/api/arx_backend_api_spec.yaml"
    base_url: "http://localhost:8080/api"
    version: "1.0.0"
    languages:
      - typescript
      - python
      - go
      - java
      - csharp
      - php
    features:
      - authentication
      - rate_limiting
      - audit_logging
      # ... more features
```

## 🧪 Testing

### Test Types

1. **Unit Tests**: Test individual SDK functions
2. **Integration Tests**: Test against live APIs
3. **Build Tests**: Test compilation and packaging

### Running Tests

```bash
# Test all SDKs
python scripts/test_sdks.py

# Test specific language
python scripts/test_sdks.py --language typescript

# Test specific service
python scripts/test_sdks.py --service arx-backend

# Test specific test type
python scripts/test_sdks.py --type unit
```

### Test Coverage

- **Unit Tests**: >90% coverage target
- **Integration Tests**: All API endpoints
- **Build Tests**: All supported languages

## 📚 Generated SDKs

### TypeScript Example

```typescript
import { ArxBackendClient } from '@arxos/arx-backend';

const client = new ArxBackendClient('http://localhost:8080');

// Authenticate
const token = await client.authenticate('username', 'password');
client.setAuthToken(token);

// Make API calls
const health = await client.health.getHealth();
const projects = await client.projects.listProjects();
```

### Python Example

```python
from arxos_arx_backend import ArxBackendClient

client = ArxBackendClient('http://localhost:8080')

# Authenticate
token = client.authenticate('username', 'password')
client.set_auth_token(token)

# Make API calls
health = client.health.get_health()
projects = client.projects.list_projects()
```

### Go Example

```go
package main

import (
    "fmt"
    "github.com/arxos/arx-backend"
)

func main() {
    client := arxos.NewArxBackendClient("http://localhost:8080")

    // Authenticate
    token, err := client.Authenticate("username", "password")
    if err != nil {
        panic(err)
    }
    client.SetAuthToken(token)

    // Make API calls
    health, err := client.Health.GetHealth()
    if err != nil {
        panic(err)
    }
    fmt.Println("Health:", health)
}
```

## 🚀 CI/CD Integration

### GitHub Actions

The SDK generation is integrated with GitHub Actions for automated generation, testing, and publishing.

```yaml
name: SDK Generation and Publishing

on:
  push:
    branches: [main, develop]
    paths:
      - 'arx-docs/api/**'
      - 'sdk/**'
  release:
    types: [published]

jobs:
  generate-sdks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate SDKs
        run: |
          cd sdk
          python scripts/generate_sdks.py
```

### Package Publishing

SDKs are automatically published to their respective package registries:

- **npm**: `@arxos/api-client`
- **PyPI**: `arxos-api-client`
- **Maven Central**: `com.arxos:api-client`
- **NuGet**: `Arxos.ApiClient`
- **Packagist**: `arxos/api-client`

## 📊 Quality Metrics

### Technical Metrics
- **SDK Generation Time**: < 5 minutes
- **Test Coverage**: > 90%
- **Documentation Coverage**: > 95%
- **Zero Breaking Changes**: In patch releases

### Developer Experience Metrics
- **SDK Installation Time**: < 30 seconds
- **First Successful API Call**: < 5 minutes
- **Documentation Clarity Score**: > 4.5/5
- **Developer Satisfaction**: > 4.5/5

## 🔧 Customization

### Custom Templates

You can customize the generated code by modifying templates in `generator/templates/`:

```mustache
{{#operations}}
{{#operation}}
/**
 * {{summary}}
 * {{notes}}
 */
export const {{operationId}} = async (
    {{#parameters}}
    {{paramName}}{{^required}}?{{/required}}: {{dataType}},
    {{/parameters}}
    config?: RequestConfig
): Promise<{{#returnType}}{{{returnType}}}{{/returnType}}{{^returnType}}void{{/returnType}}> => {
    // Custom implementation
};
{{/operation}}
{{/operations}}
```

### Adding New Languages

1. Add language configuration to `generator.yaml`
2. Create templates in `templates/<language>/`
3. Update the generator to support the new language
4. Add test cases for the new language

### Adding New Services

1. Add service definition to `services.yaml`
2. Ensure OpenAPI spec is available
3. Update service configuration
4. Test generation for all supported languages

## 🐛 Troubleshooting

### Common Issues

1. **OpenAPI Generator Not Found**
   ```bash
   npm install -g @openapitools/openapi-generator-cli
   ```

2. **Template Not Found**
   - Check template directory structure
   - Ensure templates are in correct language subdirectory

3. **Generation Fails**
   - Validate OpenAPI specs: `swagger-cli validate spec.yaml`
   - Check OpenAPI Generator version compatibility
   - Review error logs for specific issues

4. **Tests Fail**
   - Ensure all language-specific tools are installed
   - Check package manager configurations
   - Verify test environment setup

### Debug Mode

Enable verbose logging for debugging:

```bash
python scripts/generate_sdks.py --verbose
python scripts/test_sdks.py --verbose
```

## 📈 Performance

### Generation Performance
- **Single Service/Language**: ~30 seconds
- **All Services/Languages**: ~5 minutes
- **Parallel Generation**: ~2 minutes (with optimizations)

### Test Performance
- **Unit Tests**: ~1 minute per language
- **Integration Tests**: ~5 minutes per service
- **Full Test Suite**: ~30 minutes

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
3. **Make changes**
4. **Add tests**
5. **Update documentation**
6. **Submit pull request**

### Code Standards

- **Python**: Black formatting, type hints
- **TypeScript**: Prettier formatting, ESLint
- **Go**: gofmt, goimports
- **Java**: Google Java Style
- **C#**: .NET formatting
- **PHP**: PSR-12

## 📞 Support

- **Documentation**: https://docs.arxos.com/sdk
- **Issues**: https://github.com/arxos/sdk/issues
- **Discussions**: https://github.com/arxos/sdk/discussions
- **Email**: support@arxos.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Generated with ❤️ by the Arxos SDK Generator**
