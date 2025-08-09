#!/usr/bin/env python3
"""
Arxos SDK Documentation Generator
Generates comprehensive documentation for all SDKs including API docs, SDK docs, examples, and tutorials.
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Main documentation generator class"""

    def __init__(self, sdk_path: Path):
        self.sdk_path = sdk_path
        self.docs_path = sdk_path / "docs"
        self.docs_path.mkdir(exist_ok=True)

        # Create documentation directories
        (self.docs_path / "api").mkdir(exist_ok=True)
        (self.docs_path / "sdk").mkdir(exist_ok=True)
        (self.docs_path / "examples").mkdir(exist_ok=True)
        (self.docs_path / "tutorials").mkdir(exist_ok=True)

    def generate_all_documentation(self):
        """Generate all documentation"""
        logger.info("📚 Starting documentation generation...")

        # Generate API documentation
        self.generate_api_documentation()

        # Generate SDK documentation
        self.generate_sdk_documentation()

        # Generate examples
        self.generate_examples()

        # Generate tutorials
        self.generate_tutorials()

        # Generate index pages
        self.generate_index_pages()

        logger.info("✅ Documentation generation completed!")

    def generate_api_documentation(self):
        """Generate API documentation from OpenAPI specs"""
        logger.info("📖 Generating API documentation...")

        api_docs_path = self.docs_path / "api"

        # Find all OpenAPI specs
        specs_path = Path("arx-docs/api")
        if not specs_path.exists():
            logger.warning("OpenAPI specs directory not found")
            return

        for spec_file in specs_path.glob("*_api_spec.yaml"):
            service_name = spec_file.stem.replace("_api_spec", "")
            logger.info(f"Generating API docs for {service_name}...")

            # Generate HTML documentation
            self.generate_html_api_docs(spec_file, api_docs_path / service_name)

            # Generate Markdown documentation
            self.generate_markdown_api_docs(spec_file, api_docs_path / service_name)

    def generate_html_api_docs(self, spec_file: Path, output_path: Path):
        """Generate HTML API documentation"""
        output_path.mkdir(exist_ok=True)

        try:
            # Use redoc-cli to generate HTML docs
            subprocess.run([
                "npx", "redoc-cli", "bundle", str(spec_file),
                "-o", str(output_path / "index.html"),
                "--title", f"{spec_file.stem.replace('_', ' ').title()} API Documentation"
            ], check=True, capture_output=True)

            logger.info(f"✅ Generated HTML docs for {spec_file.name}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to generate HTML docs for {spec_file.name}: {e}")
        except FileNotFoundError:
            logger.warning("⚠️ redoc-cli not found, skipping HTML generation")

    def generate_markdown_api_docs(self, spec_file: Path, output_path: Path):
        """Generate Markdown API documentation"""
        output_path.mkdir(exist_ok=True)

        try:
            # Load OpenAPI spec
            with open(spec_file, 'r') as f:
                spec = yaml.safe_load(f)

            # Generate Markdown
            markdown_content = self.generate_markdown_from_spec(spec)

            with open(output_path / "README.md", 'w') as f:
                f.write(markdown_content)

            logger.info(f"✅ Generated Markdown docs for {spec_file.name}")
        except Exception as e:
            logger.error(f"❌ Failed to generate Markdown docs for {spec_file.name}: {e}")

    def generate_markdown_from_spec(self, spec: Dict[str, Any]) -> str:
        """Generate Markdown from OpenAPI specification"""
        content = []

        # Title
        content.append(f"# {spec.get('info', {}).get('title', 'API Documentation')}")
        content.append("")

        # Description
        if 'info' in spec and 'description' in spec['info']:
            content.append(spec['info']['description'])
            content.append("")

        # Version
        if 'info' in spec and 'version' in spec['info']:
            content.append(f"**Version:** {spec['info']['version']}")
            content.append("")

        # Base URL
        if 'servers' in spec and spec['servers']:
            content.append(f"**Base URL:** {spec['servers'][0]['url']}")
            content.append("")

        # Authentication
        if 'components' in spec and 'securitySchemes' in spec['components']:
            content.append("## Authentication")
            content.append("")
            for scheme_name, scheme in spec['components']['securitySchemes'].items():
                content.append(f"### {scheme_name}")
                content.append(f"**Type:** {scheme.get('type', 'unknown')}")
                if 'description' in scheme:
                    content.append(f"**Description:** {scheme['description']}")
                content.append("")

        # Endpoints
        if 'paths' in spec:
            content.append("## Endpoints")
            content.append("")

            for path, methods in spec['paths'].items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        content.append(f"### {method.upper()} {path}")
                        content.append("")

                        if 'summary' in details:
                            content.append(f"**Summary:** {details['summary']}")
                            content.append("")

                        if 'description' in details:
                            content.append(f"**Description:** {details['description']}")
                            content.append("")

                        # Parameters
                        if 'parameters' in details:
                            content.append("**Parameters:**")
                            content.append("")
                            for param in details['parameters']:
                                content.append(f"- `{param['name']}` ({param.get('in', 'unknown')}) - {param.get('description', 'No description')}")
                            content.append("")

                        # Request body
                        if 'requestBody' in details:
                            content.append("**Request Body:**")
                            content.append("")
                            content.append("```json")
                            # Add example request body if available
                            content.append("{}")
                            content.append("```")
                            content.append("")

                        # Responses
                        if 'responses' in details:
                            content.append("**Responses:**")
                            content.append("")
                            for status_code, response in details['responses'].items():
                                content.append(f"- `{status_code}` - {response.get('description', 'No description')}")
                            content.append("")

                        content.append("---")
                        content.append("")

        return "\n".join(content)

    def generate_sdk_documentation(self):
        """Generate SDK-specific documentation"""
        logger.info("📖 Generating SDK documentation...")

        sdk_docs_path = self.docs_path / "sdk"

        # Generate docs for each language
        for language_dir in (self.sdk_path / "generated").iterdir():
            if language_dir.is_dir():
                language = language_dir.name
                logger.info(f"Generating SDK docs for {language}...")

                language_docs_path = sdk_docs_path / language
                language_docs_path.mkdir(exist_ok=True)

                # Generate language-specific documentation
                self.generate_language_sdk_docs(language, language_dir, language_docs_path)

    def generate_language_sdk_docs(self, language: str, sdk_dir: Path, docs_path: Path):
        """Generate SDK documentation for a specific language"""
        # Generate main README
        readme_content = self.generate_sdk_readme(language, sdk_dir)
        with open(docs_path / "README.md", 'w') as f:
            f.write(readme_content)

        # Generate service-specific docs
        for service_dir in sdk_dir.iterdir():
            if service_dir.is_dir():
                service_name = service_dir.name
                service_docs_path = docs_path / service_name
                service_docs_path.mkdir(exist_ok=True)

                # Generate service documentation
                service_readme = self.generate_service_docs(language, service_name, service_dir)
                with open(service_docs_path / "README.md", 'w') as f:
                    f.write(service_readme)

    def generate_sdk_readme(self, language: str, sdk_dir: Path) -> str:
        """Generate main SDK README for a language"""
        content = []

        content.append(f"# Arxos SDK - {language.title()}")
        content.append("")
        content.append(f"This directory contains the {language.title()} SDKs for all Arxos services.")
        content.append("")

        # List available services
        content.append("## Available Services")
        content.append("")
        for service_dir in sdk_dir.iterdir():
            if service_dir.is_dir():
                service_name = service_dir.name.replace('-', ' ').title()
                content.append(f"- [{service_name}](./{service_dir.name}/README.md)")
        content.append("")

        # Installation instructions
        content.append("## Installation")
        content.append("")
        if language == "typescript":
            content.append("```bash")
            content.append("npm install @arxos/api-client")
            content.append("```")
        elif language == "python":
            content.append("```bash")
            content.append("pip install arxos-api-client")
            content.append("```")
        elif language == "go":
            content.append("```bash")
            content.append("go get github.com/arxos/api-client")
            content.append("```")
        elif language == "java":
            content.append("```xml")
            content.append("<dependency>")
            content.append("    <groupId>com.arxos</groupId>")
            content.append("    <artifactId>api-client</artifactId>")
            content.append("    <version>1.0.0</version>")
            content.append("</dependency>")
            content.append("```")
        elif language == "csharp":
            content.append("```bash")
            content.append("dotnet add package Arxos.ApiClient")
            content.append("```")
        elif language == "php":
            content.append("```bash")
            content.append("composer require arxos/api-client")
            content.append("```")
        content.append("")

        # Quick start
        content.append("## Quick Start")
        content.append("")
        content.append("```" + language)
        if language == "typescript":
            content.append("import { ArxBackendClient } from '@arxos/arx-backend';")
            content.append("")
            content.append("const client = new ArxBackendClient('http://localhost:8080');")
            content.append("const health = await client.health.getHealth();")
        elif language == "python":
            content.append("from arxos_arx_backend import ArxBackendClient")
            content.append("")
            content.append("client = ArxBackendClient('http://localhost:8080')")
            content.append("health = client.health.get_health()")
        elif language == "go":
            content.append("import \"github.com/arxos/arx-backend\"")
            content.append("")
            content.append("client := arxos.NewArxBackendClient(\"http://localhost:8080\")")
            content.append("health, err := client.Health.GetHealth()")
        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_service_docs(self, language: str, service_name: str, service_dir: Path) -> str:
        """Generate service-specific documentation"""
        content = []

        service_title = service_name.replace('-', ' ').title()
        content.append(f"# {service_title} SDK - {language.title()}")
        content.append("")

        # Service description
        content.append("## Overview")
        content.append("")
        content.append(f"This SDK provides type-safe access to the {service_title} API.")
        content.append("")

        # Installation
        content.append("## Installation")
        content.append("")
        if language == "typescript":
            content.append(f"```bash")
            content.append(f"npm install @arxos/{service_name}")
            content.append(f"```")
        elif language == "python":
            content.append(f"```bash")
            content.append(f"pip install arxos-{service_name.replace('-', '_')}")
            content.append(f"```")
        elif language == "go":
            content.append(f"```bash")
            content.append(f"go get github.com/arxos/{service_name}")
            content.append(f"```")
        content.append("")

        # Usage examples
        content.append("## Usage")
        content.append("")
        content.append("### Basic Usage")
        content.append("")
        content.append("```" + language)
        if language == "typescript":
            content.append(f"import {{ {service_title.replace(' ', '')}Client }} from '@arxos/{service_name}';")
            content.append("")
            content.append(f"const client = new {service_title.replace(' ', '')}Client('http://localhost:8080');")
            content.append("const health = await client.health.getHealth();")
        elif language == "python":
            content.append(f"from arxos_{service_name.replace('-', '_')} import {service_title.replace(' ', '')}Client")
            content.append("")
            content.append(f"client = {service_title.replace(' ', '')}Client('http://localhost:8080')")
            content.append("health = client.health.get_health()")
        elif language == "go":
            content.append(f"import \"github.com/arxos/{service_name}\"")
            content.append("")
            content.append(f"client := arxos.New{service_title.replace(' ', '')}Client(\"http://localhost:8080\")")
            content.append("health, err := client.Health.GetHealth()")
        content.append("```")
        content.append("")

        # Authentication
        content.append("### Authentication")
        content.append("")
        content.append("```" + language)
        if language == "typescript":
            content.append("const token = await client.authenticate('username', 'password');")
            content.append("client.setAuthToken(token);")
        elif language == "python":
            content.append("token = client.authenticate('username', 'password')")
            content.append("client.set_auth_token(token)")
        elif language == "go":
            content.append("token, err := client.Authenticate(\"username\", \"password\")")
            content.append("client.SetAuthToken(token)")
        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_examples(self):
        """Generate example applications"""
        logger.info("📖 Generating examples...")

        examples_path = self.docs_path / "examples"

        # Generate examples for each language
        for language_dir in (self.sdk_path / "generated").iterdir():
            if language_dir.is_dir():
                language = language_dir.name
                logger.info(f"Generating examples for {language}...")

                language_examples_path = examples_path / language
                language_examples_path.mkdir(exist_ok=True)

                self.generate_language_examples(language, language_dir, language_examples_path)

    def generate_language_examples(self, language: str, sdk_dir: Path, examples_path: Path):
        """Generate examples for a specific language"""
        # Generate basic example
        basic_example = self.generate_basic_example(language)
        with open(examples_path / "basic_usage.md", 'w') as f:
            f.write(basic_example)

        # Generate authentication example
        auth_example = self.generate_auth_example(language)
        with open(examples_path / "authentication.md", 'w') as f:
            f.write(auth_example)

        # Generate error handling example
        error_example = self.generate_error_handling_example(language)
        with open(examples_path / "error_handling.md", 'w') as f:
            f.write(error_example)

    def generate_basic_example(self, language: str) -> str:
        """Generate basic usage example"""
        content = []

        content.append(f"# Basic Usage Example - {language.title()}")
        content.append("")
        content.append("This example demonstrates basic SDK usage.")
        content.append("")

        content.append("## Code")
        content.append("")
        content.append("```" + language)

        if language == "typescript":
            content.append("import { ArxBackendClient } from '@arxos/arx-backend';")
            content.append("")
            content.append("async function main() {")
            content.append("    const client = new ArxBackendClient('http://localhost:8080');")
            content.append("")
            content.append("    try {")
            content.append("        // Check health")
            content.append("        const health = await client.health.getHealth();")
            content.append("        console.log('Health:', health);")
            content.append("")
            content.append("        // List projects")
            content.append("        const projects = await client.projects.listProjects();")
            content.append("        console.log('Projects:', projects);")
            content.append("    } catch (error) {")
            content.append("        console.error('Error:', error);")
            content.append("    }")
            content.append("}")
            content.append("")
            content.append("main();")

        elif language == "python":
            content.append("from arxos_arx_backend import ArxBackendClient")
            content.append("")
            content.append("def main():")
            content.append("    client = ArxBackendClient('http://localhost:8080')")
            content.append("")
            content.append("    try:")
            content.append("        # Check health")
            content.append("        health = client.health.get_health()")
            content.append("        print('Health:', health)")
            content.append("")
            content.append("        # List projects")
            content.append("        projects = client.projects.list_projects()")
            content.append("        print('Projects:', projects)")
            content.append("    except Exception as error:")
            content.append("        print('Error:', error)")
            content.append("")
            content.append("if __name__ == '__main__':")
            content.append("    main()")

        elif language == "go":
            content.append("package main")
            content.append("")
            content.append("import (")
            content.append("    \"fmt\"")
            content.append("    \"github.com/arxos/arx-backend\"")
            content.append(")")
            content.append("")
            content.append("func main() {")
            content.append("    client := arxos.NewArxBackendClient(\"http://localhost:8080\")")
            content.append("")
            content.append("    // Check health")
            content.append("    health, err := client.Health.GetHealth()")
            content.append("    if err != nil {")
            content.append("        fmt.Printf(\"Error: %v\\n\", err)")
            content.append("        return")
            content.append("    }")
            content.append("    fmt.Printf(\"Health: %+v\\n\", health)")
            content.append("")
            content.append("    // List projects")
            content.append("    projects, err := client.Projects.ListProjects()")
            content.append("    if err != nil {")
            content.append("        fmt.Printf(\"Error: %v\\n\", err)")
            content.append("        return")
            content.append("    }")
            content.append("    fmt.Printf(\"Projects: %+v\\n\", projects)")
            content.append("}")

        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_auth_example(self, language: str) -> str:
        """Generate authentication example"""
        content = []

        content.append(f"# Authentication Example - {language.title()}")
        content.append("")
        content.append("This example demonstrates authentication with the SDK.")
        content.append("")

        content.append("## Code")
        content.append("")
        content.append("```" + language)

        if language == "typescript":
            content.append("import { ArxBackendClient } from '@arxos/arx-backend';")
            content.append("")
            content.append("async function authenticate() {")
            content.append("    const client = new ArxBackendClient('http://localhost:8080');")
            content.append("")
            content.append("    try {")
            content.append("        // Authenticate")
            content.append("        const token = await client.authenticate('username', 'password');")
            content.append("        client.setAuthToken(token);")
            content.append("")
            content.append("        // Make authenticated request")
            content.append("        const projects = await client.projects.listProjects();")
            content.append("        console.log('Projects:', projects);")
            content.append("    } catch (error) {")
            content.append("        console.error('Authentication failed:', error);")
            content.append("    }")
            content.append("}")
            content.append("")
            content.append("authenticate();")

        elif language == "python":
            content.append("from arxos_arx_backend import ArxBackendClient")
            content.append("")
            content.append("def authenticate():")
            content.append("    client = ArxBackendClient('http://localhost:8080')")
            content.append("")
            content.append("    try:")
            content.append("        # Authenticate")
            content.append("        token = client.authenticate('username', 'password')")
            content.append("        client.set_auth_token(token)")
            content.append("")
            content.append("        # Make authenticated request")
            content.append("        projects = client.projects.list_projects()")
            content.append("        print('Projects:', projects)")
            content.append("    except Exception as error:")
            content.append("        print('Authentication failed:', error)")
            content.append("")
            content.append("if __name__ == '__main__':")
            content.append("    authenticate()")

        elif language == "go":
            content.append("package main")
            content.append("")
            content.append("import (")
            content.append("    \"fmt\"")
            content.append("    \"github.com/arxos/arx-backend\"")
            content.append(")")
            content.append("")
            content.append("func authenticate() {")
            content.append("    client := arxos.NewArxBackendClient(\"http://localhost:8080\")")
            content.append("")
            content.append("    // Authenticate")
            content.append("    token, err := client.Authenticate(\"username\", \"password\")")
            content.append("    if err != nil {")
            content.append("        fmt.Printf(\"Authentication failed: %v\\n\", err)")
            content.append("        return")
            content.append("    }")
            content.append("    client.SetAuthToken(token)")
            content.append("")
            content.append("    // Make authenticated request")
            content.append("    projects, err := client.Projects.ListProjects()")
            content.append("    if err != nil {")
            content.append("        fmt.Printf(\"Error: %v\\n\", err)")
            content.append("        return")
            content.append("    }")
            content.append("    fmt.Printf(\"Projects: %+v\\n\", projects)")
            content.append("}")
            content.append("")
            content.append("func main() {")
            content.append("    authenticate()")
            content.append("}")

        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_error_handling_example(self, language: str) -> str:
        """Generate error handling example"""
        content = []

        content.append(f"# Error Handling Example - {language.title()}")
        content.append("")
        content.append("This example demonstrates proper error handling with the SDK.")
        content.append("")

        content.append("## Code")
        content.append("")
        content.append("```" + language)

        if language == "typescript":
            content.append("import { ArxBackendClient, ArxosError, AuthenticationError } from '@arxos/arx-backend';")
            content.append("")
            content.append("async function handleErrors() {")
            content.append("    const client = new ArxBackendClient('http://localhost:8080');")
            content.append("")
            content.append("    try {")
            content.append("        const projects = await client.projects.listProjects();")
            content.append("        console.log('Projects:', projects);")
            content.append("    } catch (error) {")
            content.append("        if (error instanceof AuthenticationError) {")
            content.append("            console.error('Authentication failed:', error.message);")
            content.append("            // Handle authentication error")
            content.append("        } else if (error instanceof ArxosError) {")
            content.append("            console.error('API error:', error.message);")
            content.append("            console.error('Status code:', error.statusCode);")
            content.append("        } else {")
            content.append("            console.error('Unexpected error:', error);")
            content.append("        }")
            content.append("    }")
            content.append("}")
            content.append("")
            content.append("handleErrors();")

        elif language == "python":
            content.append("from arxos_arx_backend import ArxBackendClient, ArxosError, AuthenticationError")
            content.append("")
            content.append("def handle_errors():")
            content.append("    client = ArxBackendClient('http://localhost:8080')")
            content.append("")
            content.append("    try:")
            content.append("        projects = client.projects.list_projects()")
            content.append("        print('Projects:', projects)")
            content.append("    except AuthenticationError as error:")
            content.append("        print('Authentication failed:', error.message)")
            content.append("        # Handle authentication error")
            content.append("    except ArxosError as error:")
            content.append("        print('API error:', error.message)")
            content.append("        print('Status code:', error.status_code)")
            content.append("    except Exception as error:")
            content.append("        print('Unexpected error:', error)")
            content.append("")
            content.append("if __name__ == '__main__':")
            content.append("    handle_errors()")

        elif language == "go":
            content.append("package main")
            content.append("")
            content.append("import (")
            content.append("    \"fmt\"")
            content.append("    \"github.com/arxos/arx-backend\"")
            content.append(")")
            content.append("")
            content.append("func handleErrors() {")
            content.append("    client := arxos.NewArxBackendClient(\"http://localhost:8080\")")
            content.append("")
            content.append("    projects, err := client.Projects.ListProjects()")
            content.append("    if err != nil {")
            content.append("        switch e := err.(type) {")
            content.append("        case *arxos.AuthenticationError:")
            content.append("            fmt.Printf(\"Authentication failed: %v\\n\", e.Message)")
            content.append("            // Handle authentication error")
            content.append("        case *arxos.ArxosError:")
            content.append("            fmt.Printf(\"API error: %v\\n\", e.Message)")
            content.append("            fmt.Printf(\"Status code: %d\\n\", e.StatusCode)")
            content.append("        default:")
            content.append("            fmt.Printf(\"Unexpected error: %v\\n\", err)")
            content.append("        }")
            content.append("        return")
            content.append("    }")
            content.append("    fmt.Printf(\"Projects: %+v\\n\", projects)")
            content.append("}")
            content.append("")
            content.append("func main() {")
            content.append("    handleErrors()")
            content.append("}")

        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_tutorials(self):
        """Generate tutorials"""
        logger.info("📖 Generating tutorials...")

        tutorials_path = self.docs_path / "tutorials"

        # Generate getting started tutorial
        getting_started = self.generate_getting_started_tutorial()
        with open(tutorials_path / "getting_started.md", 'w') as f:
            f.write(getting_started)

        # Generate advanced usage tutorial
        advanced_usage = self.generate_advanced_usage_tutorial()
        with open(tutorials_path / "advanced_usage.md", 'w') as f:
            f.write(advanced_usage)

    def generate_getting_started_tutorial(self) -> str:
        """Generate getting started tutorial"""
        content = []

        content.append("# Getting Started with Arxos SDKs")
        content.append("")
        content.append("This tutorial will guide you through setting up and using Arxos SDKs.")
        content.append("")

        content.append("## Prerequisites")
        content.append("")
        content.append("- Node.js 18+ (for TypeScript/JavaScript)")
        content.append("- Python 3.8+ (for Python)")
        content.append("- Go 1.21+ (for Go)")
        content.append("- Java 11+ (for Java)")
        content.append("- .NET 6+ (for C#)")
        content.append("- PHP 8.1+ (for PHP)")
        content.append("")

        content.append("## Installation")
        content.append("")
        content.append("### TypeScript/JavaScript")
        content.append("```bash")
        content.append("npm install @arxos/arx-backend")
        content.append("```")
        content.append("")

        content.append("### Python")
        content.append("```bash")
        content.append("pip install arxos-arx-backend")
        content.append("```")
        content.append("")

        content.append("### Go")
        content.append("```bash")
        content.append("go get github.com/arxos/arx-backend")
        content.append("```")
        content.append("")

        content.append("## Basic Usage")
        content.append("")
        content.append("### 1. Create a client")
        content.append("")
        content.append("```typescript")
        content.append("import { ArxBackendClient } from '@arxos/arx-backend';")
        content.append("")
        content.append("const client = new ArxBackendClient('http://localhost:8080');")
        content.append("```")
        content.append("")

        content.append("### 2. Check service health")
        content.append("")
        content.append("```typescript")
        content.append("const health = await client.health.getHealth();")
        content.append("console.log('Service health:', health);")
        content.append("```")
        content.append("")

        content.append("### 3. Authenticate")
        content.append("")
        content.append("```typescript")
        content.append("const token = await client.authenticate('username', 'password');")
        content.append("client.setAuthToken(token);")
        content.append("```")
        content.append("")

        content.append("### 4. Make API calls")
        content.append("")
        content.append("```typescript")
        content.append("const projects = await client.projects.listProjects();")
        content.append("console.log('Projects:', projects);")
        content.append("```")
        content.append("")

        content.append("## Next Steps")
        content.append("")
        content.append("- Read the [API Documentation](../api/)")
        content.append("- Check out [Examples](../examples/)")
        content.append("- Learn about [Error Handling](advanced_usage.md#error-handling)")
        content.append("")

        return "\n".join(content)

    def generate_advanced_usage_tutorial(self) -> str:
        """Generate advanced usage tutorial"""
        content = []

        content.append("# Advanced Usage Tutorial")
        content.append("")
        content.append("This tutorial covers advanced features and best practices.")
        content.append("")

        content.append("## Error Handling")
        content.append("")
        content.append("Always handle errors properly:")
        content.append("")
        content.append("```typescript")
        content.append("try {")
        content.append("    const result = await client.projects.createProject(projectData);")
        content.append("} catch (error) {")
        content.append("    if (error instanceof AuthenticationError) {")
        content.append("        // Handle authentication errors")
        content.append("    } else if (error instanceof ValidationError) {")
        content.append("        // Handle validation errors")
        content.append("    } else {")
        content.append("        // Handle other errors")
        content.append("    }")
        content.append("}")
        content.append("```")
        content.append("")

        content.append("## Rate Limiting")
        content.append("")
        content.append("The SDK handles rate limiting automatically, but you can configure it:")
        content.append("")
        content.append("```typescript")
        content.append("const client = new ArxBackendClient('http://localhost:8080', {")
        content.append("    rateLimit: {")
        content.append("        maxRequests: 100,")
        content.append("        windowMs: 60000")
        content.append("    }")
        content.append("});")
        content.append("```")
        content.append("")

        content.append("## Caching")
        content.append("")
        content.append("Use caching for better performance:")
        content.append("")
        content.append("```typescript")
        content.append("const cachedResult = await client.makeCachedRequest(")
        content.append("    'projects-list',")
        content.append("    () => client.projects.listProjects()")
        content.append(");")
        content.append("```")
        content.append("")

        content.append("## Retry Logic")
        content.append("")
        content.append("Configure retry behavior:")
        content.append("")
        content.append("```typescript")
        content.append("const client = new ArxBackendClient('http://localhost:8080', {")
        content.append("    retry: {")
        content.append("        maxRetries: 3,")
        content.append("        retryDelay: 1000,")
        content.append("        backoffMultiplier: 2")
        content.append("    }")
        content.append("});")
        content.append("```")
        content.append("")

        return "\n".join(content)

    def generate_index_pages(self):
        """Generate index pages"""
        logger.info("📖 Generating index pages...")

        # Generate main documentation index
        index_content = self.generate_main_index()
        with open(self.docs_path / "index.md", 'w') as f:
            f.write(index_content)

        # Generate API documentation index
        api_index_content = self.generate_api_index()
        with open(self.docs_path / "api" / "index.md", 'w') as f:
            f.write(api_index_content)

        # Generate SDK documentation index
        sdk_index_content = self.generate_sdk_index()
        with open(self.docs_path / "sdk" / "index.md", 'w') as f:
            f.write(sdk_index_content)

    def generate_main_index(self) -> str:
        """Generate main documentation index"""
        content = []

        content.append("# Arxos SDK Documentation")
        content.append("")
        content.append("Welcome to the Arxos SDK documentation. This documentation covers all SDKs generated for the Arxos platform.")
        content.append("")

        content.append("## Quick Navigation")
        content.append("")
        content.append("- **[API Documentation](./api/)** - OpenAPI specifications and API references")
        content.append("- **[SDK Documentation](./sdk/)** - Language-specific SDK documentation")
        content.append("- **[Examples](./examples/)** - Code examples and usage patterns")
        content.append("- **[Tutorials](./tutorials/)** - Step-by-step guides")
        content.append("")

        content.append("## Supported Languages")
        content.append("")
        content.append("- **TypeScript/JavaScript** - Full type safety and modern ES6+ features")
        content.append("- **Python** - Type hints, async support, and pip packaging")
        content.append("- **Go** - Strong typing, context support, and Go modules")
        content.append("- **Java** - Bean validation, Optional types, and Maven packaging")
        content.append("- **C#** - DateTimeOffset, Collections, and .NET 6+ support")
        content.append("- **PHP** - DateTime types and Composer packaging")
        content.append("")

        content.append("## Services")
        content.append("")
        content.append("- **Arx Backend API** - Core backend services (150+ endpoints)")
        content.append("- **SVG Parser API** - SVG to BIM conversion (20+ endpoints)")
        content.append("- **CMMS Service API** - Maintenance management (30+ endpoints)")
        content.append("- **Database Infrastructure API** - Schema management (15+ endpoints)")
        content.append("")

        content.append("## Getting Started")
        content.append("")
        content.append("1. Choose your preferred language from the [SDK Documentation](./sdk/)")
        content.append("2. Follow the installation instructions")
        content.append("3. Check out the [Examples](./examples/) for usage patterns")
        content.append("4. Read the [Tutorials](./tutorials/) for step-by-step guides")
        content.append("")

        content.append("## Support")
        content.append("")
        content.append("- **Documentation**: This site")
        content.append("- **Issues**: [GitHub Issues](https://github.com/arxos/sdk/issues)")
        content.append("- **Discussions**: [GitHub Discussions](https://github.com/arxos/sdk/discussions)")
        content.append("- **Email**: support@arxos.com")
        content.append("")

        return "\n".join(content)

    def generate_api_index(self) -> str:
        """Generate API documentation index"""
        content = []

        content.append("# API Documentation")
        content.append("")
        content.append("This section contains the API documentation for all Arxos services.")
        content.append("")

        content.append("## Available APIs")
        content.append("")
        content.append("- **[Arx Backend API](./arx-backend/)** - Core backend services")

        content.append("- **[CMMS Service API](./arx-cmms/)** - Maintenance management")
        content.append("- **[Database Infrastructure API](./arx-database/)** - Schema management")
        content.append("")

        content.append("## API Features")
        content.append("")
        content.append("- **Authentication** - JWT, API key, and OAuth2 support")
        content.append("- **Rate Limiting** - Configurable rate limiting")
        content.append("- **Error Handling** - Comprehensive error responses")
        content.append("- **Validation** - Request and response validation")
        content.append("- **Documentation** - Auto-generated from OpenAPI specs")
        content.append("")

        return "\n".join(content)

    def generate_sdk_index(self) -> str:
        """Generate SDK documentation index"""
        content = []

        content.append("# SDK Documentation")
        content.append("")
        content.append("This section contains language-specific SDK documentation.")
        content.append("")

        content.append("## Available SDKs")
        content.append("")
        content.append("- **[TypeScript/JavaScript](./typescript/)** - Full type safety and modern features")
        content.append("- **[Python](./python/)** - Type hints and async support")
        content.append("- **[Go](./go/)** - Strong typing and context support")
        content.append("- **[Java](./java/)** - Bean validation and Optional types")
        content.append("- **[C#](./csharp/)** - DateTimeOffset and Collections")
        content.append("- **[PHP](./php/)** - DateTime types and Composer")
        content.append("")

        content.append("## SDK Features")
        content.append("")
        content.append("- **Type Safety** - Full type definitions and validation")
        content.append("- **Error Handling** - Comprehensive error types and handling")
        content.append("- **Authentication** - Built-in authentication helpers")
        content.append("- **Rate Limiting** - Automatic rate limiting")
        content.append("- **Caching** - Response caching for performance")
        content.append("- **Retry Logic** - Configurable retry mechanisms")
        content.append("")

        return "\n".join(content)


def main():
    """Main entry point for documentation generation"""
    parser = argparse.ArgumentParser(description="Generate SDK documentation")
    parser.add_argument(
        "--sdk-path",
        help="Path to SDK directory",
        default="sdk"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sdk_path = Path(args.sdk_path)
    if not sdk_path.exists():
        logger.error(f"SDK path not found: {sdk_path}")
        sys.exit(1)

    try:
        generator = DocumentationGenerator(sdk_path)
        generator.generate_all_documentation()
        logger.info("🎉 Documentation generation completed successfully!")
    except Exception as e:
        logger.error(f"❌ Documentation generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
