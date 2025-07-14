#!/usr/bin/env python3
"""
Arxos SDK Generator
Generates client SDKs from OpenAPI specifications for all Arxos services.

This module provides automated SDK generation with support for multiple languages
and comprehensive customization options.
"""

import yaml
import json
import subprocess
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import shutil
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for SDK generation"""
    version: str
    output_dir: Path
    template_dir: Path
    validate_specs: bool
    format_code: bool
    add_examples: bool
    languages: List[str]
    language_configs: Dict[str, Dict[str, Any]]


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    description: str
    openapi_spec: Path
    base_url: str
    version: str
    languages: List[str]
    features: List[str]
    endpoints: List[str]


class OpenAPIValidator:
    """Validates OpenAPI specifications"""
    
    def __init__(self):
        self.swagger_cli_available = self._check_swagger_cli()
    
    def _check_swagger_cli(self) -> bool:
        """Check if swagger-cli is available"""
        try:
            subprocess.run(['swagger-cli', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("swagger-cli not found. Install with: npm install -g @apidevtools/swagger-cli")
            return False
    
    def validate_spec(self, spec_path: Path) -> bool:
        """Validate OpenAPI specification"""
        if not self.swagger_cli_available:
            logger.warning(f"Skipping validation for {spec_path} - swagger-cli not available")
            return True
        
        try:
            result = subprocess.run(
                ['swagger-cli', 'validate', str(spec_path)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"✅ Validated {spec_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Validation failed for {spec_path}: {e.stderr}")
            return False


class TemplateEngine:
    """Handles template processing and customization"""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self._load_templates()
    
    def _load_templates(self):
        """Load custom templates"""
        self.templates = {}
        if self.template_dir.exists():
            for template_file in self.template_dir.rglob("*.mustache"):
                self.templates[template_file.name] = template_file.read_text()
    
    def get_template_path(self, language: str) -> Optional[Path]:
        """Get template path for language"""
        template_path = self.template_dir / language
        if template_path.exists():
            return template_path
        return None


class CodeFormatter:
    """Handles code formatting for generated SDKs"""
    
    def __init__(self):
        self.formatters = {
            'typescript': self._format_typescript,
            'python': self._format_python,
            'go': self._format_go,
            'java': self._format_java,
            'csharp': self._format_csharp,
            'php': self._format_php
        }
    
    def format_code(self, language: str, output_path: Path):
        """Format generated code for language"""
        if language in self.formatters:
            try:
                self.formatters[language](output_path)
                logger.info(f"✅ Formatted {language} code in {output_path}")
            except Exception as e:
                logger.warning(f"⚠️ Code formatting failed for {language}: {e}")
    
    def _format_typescript(self, output_path: Path):
        """Format TypeScript code"""
        try:
            subprocess.run(['npx', 'prettier', '--write', str(output_path)], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("Prettier not available for TypeScript formatting")
    
    def _format_python(self, output_path: Path):
        """Format Python code"""
        try:
            subprocess.run(['black', str(output_path)], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("Black not available for Python formatting")
    
    def _format_go(self, output_path: Path):
        """Format Go code"""
        try:
            subprocess.run(['go', 'fmt', './...'], 
                         cwd=output_path, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("Go fmt not available")
    
    def _format_java(self, output_path: Path):
        """Format Java code"""
        # Java formatting typically handled by IDE
        pass
    
    def _format_csharp(self, output_path: Path):
        """Format C# code"""
        try:
            subprocess.run(['dotnet', 'format', str(output_path)], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("dotnet format not available")
    
    def _format_php(self, output_path: Path):
        """Format PHP code"""
        try:
            subprocess.run(['php-cs-fixer', 'fix', str(output_path)], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("PHP CS Fixer not available")


class SDKGenerator:
    """Main SDK generator class"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.services = self._load_services()
        self.validator = OpenAPIValidator()
        self.template_engine = TemplateEngine(self.config.template_dir)
        self.code_formatter = CodeFormatter()
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: str) -> GenerationConfig:
        """Load generator configuration"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return GenerationConfig(
            version=config_data['generator']['version'],
            output_dir=Path(config_data['generator']['output_dir']),
            template_dir=Path(config_data['generator']['template_dir']),
            validate_specs=config_data['generator']['validate_specs'],
            format_code=config_data['generator']['format_code'],
            add_examples=config_data['generator']['add_examples'],
            languages=config_data['languages'],
            language_configs=config_data['language_configs']
        )
    
    def _load_services(self) -> Dict[str, ServiceConfig]:
        """Load service definitions"""
        services_path = Path(__file__).parent / "config" / "services.yaml"
        if not services_path.exists():
            raise FileNotFoundError(f"Services configuration not found: {services_path}")
        
        with open(services_path, 'r') as f:
            services_data = yaml.safe_load(f)
        
        services = {}
        for service_name, service_data in services_data['services'].items():
            services[service_name] = ServiceConfig(
                name=service_data['name'],
                description=service_data['description'],
                openapi_spec=Path(service_data['openapi_spec']),
                base_url=service_data['base_url'],
                version=service_data['version'],
                languages=service_data['languages'],
                features=service_data['features'],
                endpoints=service_data['endpoints']
            )
        
        return services
    
    def generate_all_sdks(self):
        """Generate SDKs for all services and languages"""
        logger.info("🚀 Starting SDK generation for all services...")
        
        total_generations = len(self.services) * len(self.config.languages)
        completed = 0
        
        for service_name, service_config in self.services.items():
            logger.info(f"📦 Generating SDKs for {service_name}...")
            
            for language in self.config.languages:
                if language in service_config.languages:
                    try:
                        self.generate_sdk(service_name, language, service_config)
                        completed += 1
                        logger.info(f"✅ Generated {language} SDK for {service_name} ({completed}/{total_generations})")
                    except Exception as e:
                        logger.error(f"❌ Failed to generate {language} SDK for {service_name}: {e}")
                else:
                    logger.info(f"⏭️ Skipping {language} for {service_name} (not supported)")
        
        logger.info(f"🎉 SDK generation completed! Generated {completed} SDKs.")
    
    def generate_sdk(self, service_name: str, language: str, service_config: ServiceConfig):
        """Generate SDK for specific service and language"""
        # Validate OpenAPI spec
        if self.config.validate_specs:
            if not self.validator.validate_spec(service_config.openapi_spec):
                raise ValueError(f"OpenAPI spec validation failed for {service_name}")
        
        # Prepare output path
        output_path = self._get_output_path(service_name, language)
        
        # Clean output directory
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate SDK using OpenAPI Generator
        self._run_openapi_generator(service_config, language, output_path)
        
        # Post-process generated code
        self._post_process_sdk(service_name, language, output_path, service_config)
        
        # Format code if enabled
        if self.config.format_code:
            self.code_formatter.format_code(language, output_path)
        
        # Add examples if enabled
        if self.config.add_examples:
            self._add_examples(service_name, language, output_path, service_config)
    
    def _run_openapi_generator(self, service_config: ServiceConfig, language: str, output_path: Path):
        """Run OpenAPI Generator CLI"""
        generator_name = self._get_generator_name(language)
        additional_props = self._get_additional_properties(language, service_config)
        template_path = self.template_engine.get_template_path(language)
        
        cmd = [
            'openapi-generator-cli', 'generate',
            '-i', str(service_config.openapi_spec),
            '-g', generator_name,
            '-o', str(output_path),
            '--additional-properties', additional_props
        ]
        
        if template_path:
            cmd.extend(['--template-dir', str(template_path)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"OpenAPI Generator output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"OpenAPI Generator failed: {e.stderr}")
            raise RuntimeError(f"SDK generation failed: {e.stderr}")
    
    def _get_generator_name(self, language: str) -> str:
        """Get OpenAPI generator name for language"""
        generators = {
            'typescript': 'typescript-fetch',
            'python': 'python',
            'go': 'go',
            'java': 'java',
            'csharp': 'csharp',
            'php': 'php'
        }
        return generators.get(language, language)
    
    def _get_additional_properties(self, language: str, service_config: ServiceConfig) -> str:
        """Get additional properties for language"""
        base_props = self.config.language_configs[language]['additional_properties']
        
        # Add service-specific properties
        service_props = {
            'packageName': f"arxos-{service_config.name.lower().replace(' ', '-')}",
            'packageVersion': service_config.version,
            'packageUrl': f"https://github.com/arxos/sdk-{service_config.name.lower().replace(' ', '-')}",
            'infoTitle': service_config.name,
            'infoDescription': service_config.description,
            'infoVersion': service_config.version
        }
        
        # Combine properties
        all_props = {**base_props, **service_props}
        return ','.join([f"{k}={v}" for k, v in all_props.items()])
    
    def _get_output_path(self, service_name: str, language: str) -> Path:
        """Get output path for generated SDK"""
        service_dir = service_name.lower().replace(' ', '-')
        return self.config.output_dir / language / service_dir
    
    def _post_process_sdk(self, service_name: str, language: str, output_path: Path, service_config: ServiceConfig):
        """Post-process generated SDK"""
        logger.info(f"🔧 Post-processing {language} SDK for {service_name}...")
        
        # Add custom headers
        self._add_custom_headers(output_path, language)
        
        # Add authentication helpers
        self._add_auth_helpers(output_path, language, service_config)
        
        # Add error handling
        self._add_error_handling(output_path, language)
        
        # Add README
        self._add_readme(output_path, service_name, language, service_config)
        
        # Add package configuration
        self._add_package_config(output_path, language, service_config)
    
    def _add_custom_headers(self, output_path: Path, language: str):
        """Add custom headers to SDK"""
        # Implementation varies by language
        if language == 'typescript':
            self._add_typescript_headers(output_path)
        elif language == 'python':
            self._add_python_headers(output_path)
        elif language == 'go':
            self._add_go_headers(output_path)
    
    def _add_typescript_headers(self, output_path: Path):
        """Add custom headers for TypeScript"""
        headers_file = output_path / "src" / "headers.ts"
        headers_content = '''
// Custom headers for Arxos SDK
export const DEFAULT_HEADERS = {
    'User-Agent': 'Arxos-SDK-TypeScript/1.0.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
};

export const createHeaders = (customHeaders?: Record<string, string>) => {
    return { ...DEFAULT_HEADERS, ...customHeaders };
};
'''
        headers_file.parent.mkdir(parents=True, exist_ok=True)
        headers_file.write_text(headers_content)
    
    def _add_python_headers(self, output_path: Path):
        """Add custom headers for Python"""
        headers_file = output_path / "arxos_api_client" / "headers.py"
        headers_content = '''
"""Custom headers for Arxos SDK"""

DEFAULT_HEADERS = {
    'User-Agent': 'Arxos-SDK-Python/1.0.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def create_headers(custom_headers=None):
    """Create headers with defaults and custom headers"""
    if custom_headers is None:
        custom_headers = {}
    return {**DEFAULT_HEADERS, **custom_headers}
'''
        headers_file.parent.mkdir(parents=True, exist_ok=True)
        headers_file.write_text(headers_content)
    
    def _add_go_headers(self, output_path: Path):
        """Add custom headers for Go"""
        headers_file = output_path / "headers.go"
        headers_content = '''
package arxos

import "net/http"

// DefaultHeaders returns default headers for Arxos SDK
func DefaultHeaders() map[string]string {
	return map[string]string{
		"User-Agent":   "Arxos-SDK-Go/1.0.0",
		"Accept":       "application/json",
		"Content-Type": "application/json",
	}
}

// CreateHeaders creates headers with defaults and custom headers
func CreateHeaders(customHeaders map[string]string) map[string]string {
	headers := DefaultHeaders()
	for k, v := range customHeaders {
		headers[k] = v
	}
	return headers
}
'''
        headers_file.write_text(headers_content)
    
    def _add_auth_helpers(self, output_path: Path, language: str, service_config: ServiceConfig):
        """Add authentication helpers to SDK"""
        if language == 'typescript':
            self._add_typescript_auth(output_path, service_config)
        elif language == 'python':
            self._add_python_auth(output_path, service_config)
        elif language == 'go':
            self._add_go_auth(output_path, service_config)
    
    def _add_typescript_auth(self, output_path: Path, service_config: ServiceConfig):
        """Add authentication helpers for TypeScript"""
        auth_file = output_path / "src" / "auth.ts"
        auth_content = f'''
// Authentication helpers for {service_config.name}
export interface AuthConfig {{
    apiKey?: string;
    accessToken?: string;
    username?: string;
    password?: string;
}}

export class AuthManager {{
    private config: AuthConfig;

    constructor(config: AuthConfig) {{
        this.config = config;
    }}

    getHeaders(): Record<string, string> {{
        const headers: Record<string, string> = {{}};
        
        if (this.config.apiKey) {{
            headers['X-API-Key'] = this.config.apiKey;
        }}
        
        if (this.config.accessToken) {{
            headers['Authorization'] = `Bearer ${{this.config.accessToken}}`;
        }}
        
        return headers;
    }}

    async authenticate(username: string, password: string): Promise<string> {{
        // Implementation for authentication
        const response = await fetch('{service_config.base_url}/auth/login', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json'
            }},
            body: JSON.stringify({{ username, password }})
        }});
        
        if (!response.ok) {{
            throw new Error('Authentication failed');
        }}
        
        const data = await response.json();
        return data.access_token;
    }}
}}
'''
        auth_file.parent.mkdir(parents=True, exist_ok=True)
        auth_file.write_text(auth_content)
    
    def _add_python_auth(self, output_path: Path, service_config: ServiceConfig):
        """Add authentication helpers for Python"""
        auth_file = output_path / "arxos_api_client" / "auth.py"
        auth_content = f'''
"""Authentication helpers for {service_config.name}"""

import requests
from typing import Optional, Dict, Any

class AuthConfig:
    def __init__(self, api_key: Optional[str] = None, 
                 access_token: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        self.api_key = api_key
        self.access_token = access_token
        self.username = username
        self.password = password

class AuthManager:
    def __init__(self, config: AuthConfig):
        self.config = config

    def get_headers(self) -> Dict[str, str]:
        headers = {{}}
        
        if self.config.api_key:
            headers['X-API-Key'] = self.config.api_key
        
        if self.config.access_token:
            headers['Authorization'] = f'Bearer {{self.config.access_token}}'
        
        return headers

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate and return access token"""
        response = requests.post(
            '{service_config.base_url}/auth/login',
            json={{'username': username, 'password': password}},
            headers={{'Content-Type': 'application/json'}}
        )
        
        if not response.ok:
            raise Exception('Authentication failed')
        
        data = response.json()
        return data['access_token']
'''
        auth_file.parent.mkdir(parents=True, exist_ok=True)
        auth_file.write_text(auth_content)
    
    def _add_go_auth(self, output_path: Path, service_config: ServiceConfig):
        """Add authentication helpers for Go"""
        auth_file = output_path / "auth.go"
        auth_content = f'''
package arxos

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

// AuthConfig holds authentication configuration
type AuthConfig struct {{
	APIKey      string
	AccessToken string
	Username    string
	Password    string
}}

// AuthManager handles authentication
type AuthManager struct {{
	config AuthConfig
}}

// NewAuthManager creates a new auth manager
func NewAuthManager(config AuthConfig) *AuthManager {{
	return &AuthManager{{config: config}}
}}

// GetHeaders returns authentication headers
func (a *AuthManager) GetHeaders() map[string]string {{
	headers := make(map[string]string)
	
	if a.config.APIKey != "" {{
		headers["X-API-Key"] = a.config.APIKey
	}}
	
	if a.config.AccessToken != "" {{
		headers["Authorization"] = fmt.Sprintf("Bearer %s", a.config.AccessToken)
	}}
	
	return headers
}}

// Authenticate performs authentication
func (a *AuthManager) Authenticate(username, password string) (string, error) {{
	data := map[string]string{{
		"username": username,
		"password": password,
	}}
	
	jsonData, _ := json.Marshal(data)
	
	resp, err := http.Post(
		"{service_config.base_url}/auth/login",
		"application/json",
		bytes.NewBuffer(jsonData),
	)
	
	if err != nil {{
		return "", err
	}}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {{
		return "", fmt.Errorf("authentication failed: %d", resp.StatusCode)
	}}
	
	var result map[string]interface{{}}
	json.NewDecoder(resp.Body).Decode(&result)
	
	if token, ok := result["access_token"].(string); ok {{
		return token, nil
	}}
	
	return "", fmt.Errorf("invalid response format")
}}
'''
        auth_file.write_text(auth_content)
    
    def _add_error_handling(self, output_path: Path, language: str):
        """Add error handling to SDK"""
        if language == 'typescript':
            self._add_typescript_errors(output_path)
        elif language == 'python':
            self._add_python_errors(output_path)
        elif language == 'go':
            self._add_go_errors(output_path)
    
    def _add_typescript_errors(self, output_path: Path):
        """Add error handling for TypeScript"""
        errors_file = output_path / "src" / "errors.ts"
        errors_content = '''
// Error handling for Arxos SDK
export class ArxosError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
        public code?: string
    ) {
        super(message);
        this.name = 'ArxosError';
    }
}

export class AuthenticationError extends ArxosError {
    constructor(message: string = 'Authentication failed') {
        super(message, 401, 'AUTHENTICATION_ERROR');
        this.name = 'AuthenticationError';
    }
}

export class ValidationError extends ArxosError {
    constructor(message: string = 'Validation failed') {
        super(message, 400, 'VALIDATION_ERROR');
        this.name = 'ValidationError';
    }
}

export class RateLimitError extends ArxosError {
    constructor(message: string = 'Rate limit exceeded') {
        super(message, 429, 'RATE_LIMIT_ERROR');
        this.name = 'RateLimitError';
    }
}
'''
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        errors_file.write_text(errors_content)
    
    def _add_python_errors(self, output_path: Path):
        """Add error handling for Python"""
        errors_file = output_path / "arxos_api_client" / "errors.py"
        errors_content = '''
"""Error handling for Arxos SDK"""

class ArxosError(Exception):
    def __init__(self, message: str, status_code: int = None, code: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code

class AuthenticationError(ArxosError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, "AUTHENTICATION_ERROR")

class ValidationError(ArxosError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 400, "VALIDATION_ERROR")

class RateLimitError(ArxosError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429, "RATE_LIMIT_ERROR")
'''
        errors_file.parent.mkdir(parents=True, exist_ok=True)
        errors_file.write_text(errors_content)
    
    def _add_go_errors(self, output_path: Path):
        """Add error handling for Go"""
        errors_file = output_path / "errors.go"
        errors_content = '''
package arxos

import "fmt"

// ArxosError represents an SDK error
type ArxosError struct {
	Message    string
	StatusCode int
	Code       string
}

func (e *ArxosError) Error() string {
	return e.Message
}

// AuthenticationError represents authentication errors
type AuthenticationError struct {
	*ArxosError
}

func NewAuthenticationError(message string) *AuthenticationError {
	if message == "" {
		message = "Authentication failed"
	}
	return &AuthenticationError{
		ArxosError: &ArxosError{
			Message:    message,
			StatusCode: 401,
			Code:       "AUTHENTICATION_ERROR",
		},
	}
}

// ValidationError represents validation errors
type ValidationError struct {
	*ArxosError
}

func NewValidationError(message string) *ValidationError {
	if message == "" {
		message = "Validation failed"
	}
	return &ValidationError{
		ArxosError: &ArxosError{
			Message:    message,
			StatusCode: 400,
			Code:       "VALIDATION_ERROR",
		},
	}
}

// RateLimitError represents rate limit errors
type RateLimitError struct {
	*ArxosError
}

func NewRateLimitError(message string) *RateLimitError {
	if message == "" {
		message = "Rate limit exceeded"
	}
	return &RateLimitError{
		ArxosError: &ArxosError{
			Message:    message,
			StatusCode: 429,
			Code:       "RATE_LIMIT_ERROR",
		},
	}
}
'''
        errors_file.write_text(errors_content)
    
    def _add_readme(self, output_path: Path, service_name: str, language: str, service_config: ServiceConfig):
        """Add README file to SDK"""
        readme_file = output_path / "README.md"
        
        readme_content = f'''# {service_config.name} SDK ({language.title()})

This is the {language.title()} SDK for the {service_config.name}.

## Installation

'''
        
        if language == 'typescript':
            readme_content += f'''```bash
npm install @arxos/{service_name.lower().replace(' ', '-')}
```

## Usage

```typescript
import {{ {service_name.replace(' ', '')}Client }} from '@arxos/{service_name.lower().replace(' ', '-')}';

const client = new {service_name.replace(' ', '')}Client('{service_config.base_url}');

// Authenticate
const token = await client.authenticate('username', 'password');
client.setAuthToken(token);

// Make API calls
const health = await client.health.getHealth();
console.log('Service status:', health.status);
```'''
        
        elif language == 'python':
            readme_content += f'''```bash
pip install arxos-{service_name.lower().replace(' ', '-')}
```

## Usage

```python
from arxos_{service_name.lower().replace(' ', '_')} import {service_name.replace(' ', '')}Client

client = {service_name.replace(' ', '')}Client('{service_config.base_url}')

# Authenticate
token = client.authenticate('username', 'password')
client.set_auth_token(token)

# Make API calls
health = client.health.get_health()
print('Service status:', health.status)
```'''
        
        elif language == 'go':
            readme_content += f'''```bash
go get github.com/arxos/{service_name.lower().replace(' ', '-')}
```

## Usage

```go
package main

import (
    "fmt"
    "github.com/arxos/{service_name.lower().replace(' ', '-')}"
)

func main() {{
    client := arxos.New{service_name.replace(' ', '')}Client("{service_config.base_url}")
    
    // Authenticate
    token, err := client.Authenticate("username", "your-password")
    if err != nil {{
        panic(err)
    }}
    client.SetAuthToken(token)
    
    // Make API calls
    health, err := client.Health.GetHealth()
    if err != nil {{
        panic(err)
    }}
    fmt.Println("Service status:", health.Status)
}}
```'''
        
        readme_content += f'''

## Features

- Authentication support
- Error handling
- Type safety
- Comprehensive documentation

## Documentation

For detailed documentation, visit: https://docs.arxos.com/sdk/{language}/{service_name.lower().replace(' ', '-')}

## Support

For support, please contact: support@arxos.com
'''
        
        readme_file.write_text(readme_content)
    
    def _add_package_config(self, output_path: Path, language: str, service_config: ServiceConfig):
        """Add package configuration files"""
        if language == 'typescript':
            self._add_typescript_package_config(output_path, service_config)
        elif language == 'python':
            self._add_python_package_config(output_path, service_config)
        elif language == 'go':
            self._add_go_package_config(output_path, service_config)
    
    def _add_typescript_package_config(self, output_path: Path, service_config: ServiceConfig):
        """Add package.json for TypeScript"""
        package_file = output_path / "package.json"
        package_content = {
            "name": f"@arxos/{service_config.name.lower().replace(' ', '-')}",
            "version": service_config.version,
            "description": service_config.description,
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "lint": "eslint src/",
                "format": "prettier --write src/"
            },
            "keywords": ["arxos", "api", "client", "sdk"],
            "author": "Arxos Team",
            "license": "MIT",
            "repository": {
                "type": "git",
                "url": f"https://github.com/arxos/sdk-{service_config.name.lower().replace(' ', '-')}"
            },
            "dependencies": {
                "node-fetch": "^3.3.0"
            },
            "devDependencies": {
                "@types/node": "^18.0.0",
                "typescript": "^4.9.0",
                "jest": "^29.0.0",
                "@types/jest": "^29.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.8.0"
            }
        }
        package_file.write_text(json.dumps(package_content, indent=2))
    
    def _add_python_package_config(self, output_path: Path, service_config: ServiceConfig):
        """Add setup.py for Python"""
        setup_file = output_path / "setup.py"
        setup_content = f'''from setuptools import setup, find_packages

setup(
    name="arxos-{service_config.name.lower().replace(' ', '-')}",
    version="{service_config.version}",
    description="{service_config.description}",
    author="Arxos Team",
    author_email="support@arxos.com",
    url="https://github.com/arxos/sdk-{service_config.name.lower().replace(' ', '-')}",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
'''
        setup_file.write_text(setup_content)
    
    def _add_go_package_config(self, output_path: Path, service_config: ServiceConfig):
        """Add go.mod for Go"""
        go_mod_file = output_path / "go.mod"
        go_mod_content = f'''module github.com/arxos/{service_config.name.lower().replace(' ', '-')}

go 1.21

require (
    github.com/stretchr/testify v1.8.4
)

require (
    github.com/davecgh/go-spew v1.1.1 // indirect
    github.com/pmezard/go-difflib v1.0.0 // indirect
    gopkg.in/yaml.v3 v3.0.1 // indirect
)
'''
        go_mod_file.write_text(go_mod_content)
    
    def _add_examples(self, service_name: str, language: str, output_path: Path, service_config: ServiceConfig):
        """Add examples to SDK"""
        examples_dir = output_path / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        if language == 'typescript':
            self._add_typescript_examples(examples_dir, service_name, service_config)
        elif language == 'python':
            self._add_python_examples(examples_dir, service_name, service_config)
        elif language == 'go':
            self._add_go_examples(examples_dir, service_name, service_config)
    
    def _add_typescript_examples(self, examples_dir: Path, service_name: str, service_config: ServiceConfig):
        """Add TypeScript examples"""
        example_file = examples_dir / "basic-usage.ts"
        example_content = f'''import {{ {service_name.replace(' ', '')}Client }} from '../src';

async function main() {{
    const client = new {service_name.replace(' ', '')}Client('{service_config.base_url}');
    
    try {{
        // Authenticate
        const token = await client.authenticate('your-username', 'your-password');
        client.setAuthToken(token);
        
        // Check health
        const health = await client.health.getHealth();
        console.log('Service health:', health);
        
        // Example API calls based on available endpoints
        {self._generate_endpoint_examples(service_config.endpoints, 'typescript')}
        
    }} catch (error) {{
        console.error('Error:', error);
    }}
}}

main();
'''
        example_file.write_text(example_content)
    
    def _add_python_examples(self, examples_dir: Path, service_name: str, service_config: ServiceConfig):
        """Add Python examples"""
        example_file = examples_dir / "basic_usage.py"
        example_content = f'''from arxos_{service_name.lower().replace(' ', '_')} import {service_name.replace(' ', '')}Client

def main():
    client = {service_name.replace(' ', '')}Client('{service_config.base_url}')
    
    try:
        # Authenticate
        token = client.authenticate('your-username', 'your-password')
        client.set_auth_token(token)
        
        # Check health
        health = client.health.get_health()
        print('Service health:', health)
        
        # Example API calls based on available endpoints
        {self._generate_endpoint_examples(service_config.endpoints, 'python')}
        
    except Exception as error:
        print('Error:', error)

if __name__ == '__main__':
    main()
'''
        example_file.write_text(example_content)
    
    def _add_go_examples(self, examples_dir: Path, service_name: str, service_config: ServiceConfig):
        """Add Go examples"""
        example_file = examples_dir / "basic_usage.go"
        example_content = f'''package main

import (
    "fmt"
    "log"
    "github.com/arxos/{service_name.lower().replace(' ', '-')}"
)

func main() {{
    client := arxos.New{service_name.replace(' ', '')}Client("{service_config.base_url}")
    
    // Authenticate
    token, err := client.Authenticate("your-username", "your-password")
    if err != nil {{
        log.Fatal("Authentication failed:", err)
    }}
    client.SetAuthToken(token)
    
    // Check health
    health, err := client.Health.GetHealth()
    if err != nil {{
        log.Fatal("Health check failed:", err)
    }}
    fmt.Println("Service health:", health)
    
    // Example API calls based on available endpoints
    {self._generate_endpoint_examples(service_config.endpoints, 'go')}
}}
'''
        example_file.write_text(example_content)
    
    def _generate_endpoint_examples(self, endpoints: List[str], language: str) -> str:
        """Generate example code for endpoints"""
        examples = []
        
        for endpoint in endpoints:
            if endpoint == 'authentication':
                continue  # Already handled in main example
            
            if language == 'typescript':
                examples.append(f'''        // {endpoint.title()} example
        // const {endpoint} = await client.{endpoint}.list{endpoint.title()}();
        // console.log('{endpoint.title()}:', {endpoint});''')
            
            elif language == 'python':
                examples.append(f'''        # {endpoint.title()} example
        # {endpoint} = client.{endpoint}.list_{endpoint}()
        # print('{endpoint.title()}:', {endpoint})''')
            
            elif language == 'go':
                examples.append(f'''    // {endpoint.title()} example
    // {endpoint}, err := client.{endpoint.title()}.List{endpoint.title()}()
    // if err != nil {{
    //     log.Fatal("Failed to get {endpoint}:", err)
    // }}
    // fmt.Println("{endpoint.title()}:", {endpoint})''')
        
        return '\n'.join(examples)


def main():
    """Main entry point"""
    try:
        config_path = "sdk/generator/config/generator.yaml"
        generator = SDKGenerator(config_path)
        generator.generate_all_sdks()
        logger.info("🎉 SDK generation completed successfully!")
    except Exception as e:
        logger.error(f"❌ SDK generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 