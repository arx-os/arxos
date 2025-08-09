#!/usr/bin/env python3
"""
Documentation Generator for SDKs
Generates comprehensive documentation, examples, and tutorials for all SDKs
"""

import yaml
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import jinja2
import markdown
import shutil
import os

class DocumentationGenerator:
    """Documentation generator for SDKs"""

    def __init__(self, config_path: str = None):
    """
    Perform __init__ operation

Args:
        config_path: Description of config_path

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.config_path = config_path or "sdk/generator/config/documentation.yaml"
        self.config = self.load_config()
        self.template_env = self.setup_templates()
        self.output_dir = Path("sdk/docs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load documentation configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default documentation configuration"""
        return {
            "documentation": {
                "enabled": True,
                "formats": ["html", "markdown", "pdf"],
                "include_examples": True,
                "include_tutorials": True,
                "interactive_docs": True
            },
            "languages": ["typescript", "python", "go", "java", "csharp", "php"],
            "services": ["arx-backend", "arx-cmms", "arx-database"]
        }

    def setup_templates(self) -> jinja2.Environment:
        """Setup Jinja2 template environment"""
        template_dir = Path("sdk/generator/templates/docs")
        template_dir.mkdir(parents=True, exist_ok=True)

        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_all_documentation(self):
        """Generate documentation for all SDKs"""
        print("📚 Generating comprehensive documentation...")

        # Generate API documentation
        self.generate_api_documentation()

        # Generate SDK documentation
        self.generate_sdk_documentation()

        # Generate examples
        self.generate_examples()

        # Generate tutorials
        self.generate_tutorials()

        # Generate interactive documentation
        self.generate_interactive_docs()

        # Generate search index
        self.generate_search_index()

        print("✅ Documentation generation complete!")

    def generate_api_documentation(self):
        """Generate API documentation from OpenAPI specs"""
        print("  📖 Generating API documentation...")

        api_docs_dir = self.output_dir / "api"
        api_docs_dir.mkdir(exist_ok=True)

        # Generate documentation for each service
        services = [
            ("arx-backend", "Arx Backend API"),
            ("arx-cmms", "CMMS Service API"),
            ("arx-database", "Database Infrastructure API")
        ]

        for service_name, service_title in services:
            self.generate_service_api_docs(service_name, service_title, api_docs_dir)

    def generate_service_api_docs(self, service_name: str, service_title: str, output_dir: Path):
        """Generate API documentation for a specific service"""
        service_dir = output_dir / service_name
        service_dir.mkdir(exist_ok=True)

        # Generate HTML documentation
        self.generate_html_api_docs(service_name, service_title, service_dir)

        # Generate Markdown documentation
        self.generate_markdown_api_docs(service_name, service_title, service_dir)

        # Generate OpenAPI spec documentation
        self.generate_openapi_docs(service_name, service_dir)

    def generate_html_api_docs(self, service_name: str, service_title: str, output_dir: Path):
        """Generate HTML API documentation"""
        try:
            # Use Swagger UI to generate HTML docs
            spec_path = f"arx-docs/api/{service_name}_api_spec.yaml"
            if Path(spec_path).exists():
                html_file = output_dir / "index.html"

                # Create HTML documentation using Swagger UI
                html_content = self.template_env.get_template("swagger_ui.html").render(
                    title=f"{service_title} Documentation",
                    spec_url=f"../{service_name}_api_spec.yaml"
                )

                with open(html_file, 'w') as f:
                    f.write(html_content)

                # Copy OpenAPI spec
                shutil.copy(spec_path, output_dir / f"{service_name}_api_spec.yaml")

        except Exception as e:
            print(f"    ⚠️  Error generating HTML docs for {service_name}: {e}")

    def generate_markdown_api_docs(self, service_name: str, service_title: str, output_dir: Path):
        """Generate Markdown API documentation"""
        try:
            # Generate markdown documentation
            md_file = output_dir / "README.md"

            md_content = self.template_env.get_template("api_documentation.md").render(
                service_name=service_name,
                service_title=service_title,
                endpoints=self.get_api_endpoints(service_name)
            with open(md_file, 'w') as f:
                f.write(md_content)

        except Exception as e:
            print(f"    ⚠️  Error generating Markdown docs for {service_name}: {e}")

    def generate_openapi_docs(self, service_name: str, output_dir: Path):
        """Generate OpenAPI specification documentation"""
        try:
            spec_path = f"arx-docs/api/{service_name}_api_spec.yaml"
            if Path(spec_path).exists():
                # Generate OpenAPI documentation
                openapi_file = output_dir / "openapi.yaml"
                shutil.copy(spec_path, openapi_file)

        except Exception as e:
            print(f"    ⚠️  Error generating OpenAPI docs for {service_name}: {e}")

    def generate_sdk_documentation(self):
        """Generate SDK-specific documentation"""
        print("  📚 Generating SDK documentation...")

        sdk_docs_dir = self.output_dir / "sdk"
        sdk_docs_dir.mkdir(exist_ok=True)

        for language in self.config["languages"]:
            self.generate_language_sdk_docs(language, sdk_docs_dir)

    def generate_language_sdk_docs(self, language: str, output_dir: Path):
        """Generate SDK documentation for a specific language"""
        language_dir = output_dir / language
        language_dir.mkdir(exist_ok=True)

        # Generate main SDK documentation
        self.generate_sdk_readme(language, language_dir)

        # Generate API reference
        self.generate_api_reference(language, language_dir)

        # Generate installation guide
        self.generate_installation_guide(language, language_dir)

        # Generate configuration guide
        self.generate_configuration_guide(language, language_dir)

    def generate_sdk_readme(self, language: str, output_dir: Path):
        """Generate main README for SDK"""
        readme_file = output_dir / "README.md"

        readme_content = self.template_env.get_template("sdk_readme.md").render(
            language=language,
            language_title=language.title(),
            services=self.config["services"]
        )

        with open(readme_file, 'w') as f:
            f.write(readme_content)

    def generate_api_reference(self, language: str, output_dir: Path):
        """Generate API reference documentation"""
        api_ref_file = output_dir / "API_REFERENCE.md"

        api_ref_content = self.template_env.get_template("api_reference.md").render(
            language=language,
            services=self.config["services"]
        )

        with open(api_ref_file, 'w') as f:
            f.write(api_ref_content)

    def generate_installation_guide(self, language: str, output_dir: Path):
        """Generate installation guide"""
        install_file = output_dir / "INSTALLATION.md"

        install_content = self.template_env.get_template("installation_guide.md").render(
            language=language
        )

        with open(install_file, 'w') as f:
            f.write(install_content)

    def generate_configuration_guide(self, language: str, output_dir: Path):
        """Generate configuration guide"""
        config_file = output_dir / "CONFIGURATION.md"

        config_content = self.template_env.get_template("configuration_guide.md").render(
            language=language
        )

        with open(config_file, 'w') as f:
            f.write(config_content)

    def generate_examples(self):
        """Generate code examples for all SDKs"""
        print("  💡 Generating code examples...")

        examples_dir = self.output_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        for language in self.config["languages"]:
            self.generate_language_examples(language, examples_dir)

    def generate_language_examples(self, language: str, output_dir: Path):
        """Generate examples for a specific language"""
        language_dir = output_dir / language
        language_dir.mkdir(exist_ok=True)

        # Generate basic usage examples
        self.generate_basic_examples(language, language_dir)

        # Generate authentication examples
        self.generate_auth_examples(language, language_dir)

        # Generate API usage examples
        self.generate_api_examples(language, language_dir)

        # Generate error handling examples
        self.generate_error_examples(language, language_dir)

        # Generate advanced examples
        self.generate_advanced_examples(language, language_dir)

    def generate_basic_examples(self, language: str, output_dir: Path):
        """Generate basic usage examples"""
        basic_file = output_dir / "basic_usage.md"

        basic_content = self.template_env.get_template("basic_examples.md").render(
            language=language
        )

        with open(basic_file, 'w') as f:
            f.write(basic_content)

    def generate_auth_examples(self, language: str, output_dir: Path):
        """Generate authentication examples"""
        auth_file = output_dir / "authentication.md"

        auth_content = self.template_env.get_template("auth_examples.md").render(
            language=language
        )

        with open(auth_file, 'w') as f:
            f.write(auth_content)

    def generate_api_examples(self, language: str, output_dir: Path):
        """Generate API usage examples"""
        api_file = output_dir / "api_usage.md"

        api_content = self.template_env.get_template("api_examples.md").render(
            language=language,
            services=self.config["services"]
        )

        with open(api_file, 'w') as f:
            f.write(api_content)

    def generate_error_examples(self, language: str, output_dir: Path):
        """Generate error handling examples"""
        error_file = output_dir / "error_handling.md"

        error_content = self.template_env.get_template("error_examples.md").render(
            language=language
        )

        with open(error_file, 'w') as f:
            f.write(error_content)

    def generate_advanced_examples(self, language: str, output_dir: Path):
        """Generate advanced usage examples"""
        advanced_file = output_dir / "advanced_usage.md"

        advanced_content = self.template_env.get_template("advanced_examples.md").render(
            language=language
        )

        with open(advanced_file, 'w') as f:
            f.write(advanced_content)

    def generate_tutorials(self):
        """Generate tutorial guides"""
        print("  📖 Generating tutorial guides...")

        tutorials_dir = self.output_dir / "tutorials"
        tutorials_dir.mkdir(exist_ok=True)

        # Generate getting started tutorial
        self.generate_getting_started_tutorial(tutorials_dir)

        # Generate authentication tutorial
        self.generate_auth_tutorial(tutorials_dir)

        # Generate API integration tutorial
        self.generate_integration_tutorial(tutorials_dir)

        # Generate best practices tutorial
        self.generate_best_practices_tutorial(tutorials_dir)

    def generate_getting_started_tutorial(self, output_dir: Path):
        """Generate getting started tutorial"""
        tutorial_file = output_dir / "getting_started.md"

        tutorial_content = self.template_env.get_template("getting_started_tutorial.md").render(
            languages=self.config["languages"]
        )

        with open(tutorial_file, 'w') as f:
            f.write(tutorial_content)

    def generate_auth_tutorial(self, output_dir: Path):
        """Generate authentication tutorial"""
        tutorial_file = output_dir / "authentication_tutorial.md"

        tutorial_content = self.template_env.get_template("auth_tutorial.md").render()

        with open(tutorial_file, 'w') as f:
            f.write(tutorial_content)

    def generate_integration_tutorial(self, output_dir: Path):
        """Generate API integration tutorial"""
        tutorial_file = output_dir / "api_integration_tutorial.md"

        tutorial_content = self.template_env.get_template("integration_tutorial.md").render(
            services=self.config["services"]
        )

        with open(tutorial_file, 'w') as f:
            f.write(tutorial_content)

    def generate_best_practices_tutorial(self, output_dir: Path):
        """Generate best practices tutorial"""
        tutorial_file = output_dir / "best_practices_tutorial.md"

        tutorial_content = self.template_env.get_template("best_practices_tutorial.md").render()

        with open(tutorial_file, 'w') as f:
            f.write(tutorial_content)

    def generate_interactive_docs(self):
        """Generate interactive documentation"""
        print("  🎮 Generating interactive documentation...")

        interactive_dir = self.output_dir / "interactive"
        interactive_dir.mkdir(exist_ok=True)

        # Generate API explorer
        self.generate_api_explorer(interactive_dir)

        # Generate playground
        self.generate_playground(interactive_dir)

        # Generate documentation testing
        self.generate_doc_testing(interactive_dir)

    def generate_api_explorer(self, output_dir: Path):
        """Generate interactive API explorer"""
        explorer_file = output_dir / "api_explorer.html"

        explorer_content = self.template_env.get_template("api_explorer.html").render(
            services=self.config["services"]
        )

        with open(explorer_file, 'w') as f:
            f.write(explorer_content)

    def generate_playground(self, output_dir: Path):
        """Generate code playground"""
        playground_file = output_dir / "playground.html"

        playground_content = self.template_env.get_template("playground.html").render(
            languages=self.config["languages"]
        )

        with open(playground_file, 'w') as f:
            f.write(playground_content)

    def generate_doc_testing(self, output_dir: Path):
        """Generate documentation testing"""
        testing_file = output_dir / "doc_testing.html"

        testing_content = self.template_env.get_template("doc_testing.html").render()

        with open(testing_file, 'w') as f:
            f.write(testing_content)

    def generate_search_index(self):
        """Generate search index for documentation"""
        print("  🔍 Generating search index...")

        search_file = self.output_dir / "search_index.json"

        # Create search index
        search_index = {
            "pages": [],
            "examples": [],
            "tutorials": []
        }

        # Index all documentation files
        for file_path in self.output_dir.rglob("*.md"):
            relative_path = file_path.relative_to(self.output_dir)

            with open(file_path, 'r') as f:
                content = f.read()

            search_index["pages"].append({
                "path": str(relative_path),
                "title": self.extract_title(content),
                "content": content[:500]  # First 500 chars for search
            })

        with open(search_file, 'w') as f:
            json.dump(search_index, f, indent=2)

    def extract_title(self, content: str) -> str:
        """Extract title from markdown content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled"

    def get_api_endpoints(self, service_name: str) -> List[Dict[str, Any]]:
        """Get API endpoints for a service"""
        # This would typically parse the OpenAPI spec
        # For now, return sample endpoints
        return [
            {"method": "GET", "path": "/health", "description": "Health check endpoint"},
            {"method": "POST", "path": "/auth/login", "description": "Authentication endpoint"},
            {"method": "GET", "path": "/projects", "description": "List projects"},
            {"method": "POST", "path": "/projects", "description": "Create project"}
        ]

def main():
    """Main entry point"""
    generator = DocumentationGenerator()
    generator.generate_all_documentation()

if __name__ == "__main__":
    main()
