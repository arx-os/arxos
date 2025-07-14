#!/usr/bin/env python3
"""
Example Generator for SDKs
Generates comprehensive code examples for all SDKs and languages
"""

import yaml
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import jinja2
import shutil
import os

class ExampleGenerator:
    """Example generator for SDKs"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "sdk/generator/config/examples.yaml"
        self.config = self.load_config()
        self.template_env = self.setup_templates()
        self.output_dir = Path("sdk/examples")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load example configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default example configuration"""
        return {
            "examples": {
                "enabled": True,
                "languages": ["typescript", "python", "go", "java", "csharp", "php"],
                "categories": [
                    "basic_usage",
                    "authentication", 
                    "project_management",
                    "bim_objects",
                    "asset_management",
                    "cmms_integration",
                    "export_operations",
                    "error_handling",
                    "performance",
                    "advanced_features"
                ]
            }
        }
    
    def setup_templates(self) -> jinja2.Environment:
        """Setup Jinja2 template environment"""
        template_dir = Path("sdk/generator/templates/examples")
        template_dir.mkdir(parents=True, exist_ok=True)
        
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_all_examples(self):
        """Generate examples for all SDKs"""
        print("💡 Generating comprehensive examples...")
        
        # Generate basic usage examples
        self.generate_basic_examples()
        
        # Generate authentication examples
        self.generate_auth_examples()
        
        # Generate project management examples
        self.generate_project_examples()
        
        # Generate BIM object examples
        self.generate_bim_examples()
        
        # Generate asset management examples
        self.generate_asset_examples()
        
        # Generate CMMS integration examples
        self.generate_cmms_examples()
        
        # Generate export operation examples
        self.generate_export_examples()
        
        # Generate error handling examples
        self.generate_error_examples()
        
        # Generate performance examples
        self.generate_performance_examples()
        
        # Generate advanced feature examples
        self.generate_advanced_examples()
        
        # Generate complete application examples
        self.generate_complete_apps()
        
        print("✅ Example generation complete!")
    
    def generate_basic_examples(self):
        """Generate basic usage examples"""
        print("  📚 Generating basic usage examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_basic_examples(language)
    
    def generate_language_basic_examples(self, language: str):
        """Generate basic examples for a specific language"""
        examples_dir = self.output_dir / language / "basic_usage"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate installation example
        self.generate_installation_example(language, examples_dir)
        
        # Generate client setup example
        self.generate_client_setup_example(language, examples_dir)
        
        # Generate first API call example
        self.generate_first_api_call_example(language, examples_dir)
        
        # Generate configuration example
        self.generate_configuration_example(language, examples_dir)
    
    def generate_installation_example(self, language: str, output_dir: Path):
        """Generate installation example"""
        example_file = output_dir / "01_installation.md"
        
        content = self.template_env.get_template("installation_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_client_setup_example(self, language: str, output_dir: Path):
        """Generate client setup example"""
        example_file = output_dir / "02_client_setup.md"
        
        content = self.template_env.get_template("client_setup_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_first_api_call_example(self, language: str, output_dir: Path):
        """Generate first API call example"""
        example_file = output_dir / "03_first_api_call.md"
        
        content = self.template_env.get_template("first_api_call_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_configuration_example(self, language: str, output_dir: Path):
        """Generate configuration example"""
        example_file = output_dir / "04_configuration.md"
        
        content = self.template_env.get_template("configuration_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_auth_examples(self):
        """Generate authentication examples"""
        print("  🔐 Generating authentication examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_auth_examples(language)
    
    def generate_language_auth_examples(self, language: str):
        """Generate authentication examples for a specific language"""
        examples_dir = self.output_dir / language / "authentication"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate API key authentication
        self.generate_api_key_auth_example(language, examples_dir)
        
        # Generate username/password authentication
        self.generate_password_auth_example(language, examples_dir)
        
        # Generate OAuth authentication
        self.generate_oauth_auth_example(language, examples_dir)
        
        # Generate session management
        self.generate_session_management_example(language, examples_dir)
    
    def generate_api_key_auth_example(self, language: str, output_dir: Path):
        """Generate API key authentication example"""
        example_file = output_dir / "01_api_key_auth.md"
        
        content = self.template_env.get_template("api_key_auth_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_password_auth_example(self, language: str, output_dir: Path):
        """Generate password authentication example"""
        example_file = output_dir / "02_password_auth.md"
        
        content = self.template_env.get_template("password_auth_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_oauth_auth_example(self, language: str, output_dir: Path):
        """Generate OAuth authentication example"""
        example_file = output_dir / "03_oauth_auth.md"
        
        content = self.template_env.get_template("oauth_auth_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_session_management_example(self, language: str, output_dir: Path):
        """Generate session management example"""
        example_file = output_dir / "04_session_management.md"
        
        content = self.template_env.get_template("session_management_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_project_examples(self):
        """Generate project management examples"""
        print("  📁 Generating project management examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_project_examples(language)
    
    def generate_language_project_examples(self, language: str):
        """Generate project examples for a specific language"""
        examples_dir = self.output_dir / language / "project_management"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CRUD operations
        self.generate_project_crud_example(language, examples_dir)
        
        # Generate project workflows
        self.generate_project_workflow_example(language, examples_dir)
        
        # Generate project collaboration
        self.generate_project_collaboration_example(language, examples_dir)
    
    def generate_project_crud_example(self, language: str, output_dir: Path):
        """Generate project CRUD example"""
        example_file = output_dir / "01_project_crud.md"
        
        content = self.template_env.get_template("project_crud_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_project_workflow_example(self, language: str, output_dir: Path):
        """Generate project workflow example"""
        example_file = output_dir / "02_project_workflow.md"
        
        content = self.template_env.get_template("project_workflow_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_project_collaboration_example(self, language: str, output_dir: Path):
        """Generate project collaboration example"""
        example_file = output_dir / "03_project_collaboration.md"
        
        content = self.template_env.get_template("project_collaboration_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_bim_examples(self):
        """Generate BIM object examples"""
        print("  🏗️ Generating BIM object examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_bim_examples(language)
    
    def generate_language_bim_examples(self, language: str):
        """Generate BIM examples for a specific language"""
        examples_dir = self.output_dir / language / "bim_objects"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate wall creation
        self.generate_wall_creation_example(language, examples_dir)
        
        # Generate room creation
        self.generate_room_creation_example(language, examples_dir)
        
        # Generate device creation
        self.generate_device_creation_example(language, examples_dir)
        
        # Generate BIM assembly
        self.generate_bim_assembly_example(language, examples_dir)
    
    def generate_wall_creation_example(self, language: str, output_dir: Path):
        """Generate wall creation example"""
        example_file = output_dir / "01_wall_creation.md"
        
        content = self.template_env.get_template("wall_creation_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_room_creation_example(self, language: str, output_dir: Path):
        """Generate room creation example"""
        example_file = output_dir / "02_room_creation.md"
        
        content = self.template_env.get_template("room_creation_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_device_creation_example(self, language: str, output_dir: Path):
        """Generate device creation example"""
        example_file = output_dir / "03_device_creation.md"
        
        content = self.template_env.get_template("device_creation_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_bim_assembly_example(self, language: str, output_dir: Path):
        """Generate BIM assembly example"""
        example_file = output_dir / "04_bim_assembly.md"
        
        content = self.template_env.get_template("bim_assembly_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_asset_examples(self):
        """Generate asset management examples"""
        print("  📦 Generating asset management examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_asset_examples(language)
    
    def generate_language_asset_examples(self, language: str):
        """Generate asset examples for a specific language"""
        examples_dir = self.output_dir / language / "asset_management"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate asset CRUD
        self.generate_asset_crud_example(language, examples_dir)
        
        # Generate asset tracking
        self.generate_asset_tracking_example(language, examples_dir)
        
        # Generate asset maintenance
        self.generate_asset_maintenance_example(language, examples_dir)
    
    def generate_asset_crud_example(self, language: str, output_dir: Path):
        """Generate asset CRUD example"""
        example_file = output_dir / "01_asset_crud.md"
        
        content = self.template_env.get_template("asset_crud_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_asset_tracking_example(self, language: str, output_dir: Path):
        """Generate asset tracking example"""
        example_file = output_dir / "02_asset_tracking.md"
        
        content = self.template_env.get_template("asset_tracking_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_asset_maintenance_example(self, language: str, output_dir: Path):
        """Generate asset maintenance example"""
        example_file = output_dir / "03_asset_maintenance.md"
        
        content = self.template_env.get_template("asset_maintenance_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_cmms_examples(self):
        """Generate CMMS integration examples"""
        print("  🔧 Generating CMMS integration examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_cmms_examples(language)
    
    def generate_language_cmms_examples(self, language: str):
        """Generate CMMS examples for a specific language"""
        examples_dir = self.output_dir / language / "cmms_integration"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CMMS connection
        self.generate_cmms_connection_example(language, examples_dir)
        
        # Generate field mapping
        self.generate_field_mapping_example(language, examples_dir)
        
        # Generate data synchronization
        self.generate_data_sync_example(language, examples_dir)
    
    def generate_cmms_connection_example(self, language: str, output_dir: Path):
        """Generate CMMS connection example"""
        example_file = output_dir / "01_cmms_connection.md"
        
        content = self.template_env.get_template("cmms_connection_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_field_mapping_example(self, language: str, output_dir: Path):
        """Generate field mapping example"""
        example_file = output_dir / "02_field_mapping.md"
        
        content = self.template_env.get_template("field_mapping_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_data_sync_example(self, language: str, output_dir: Path):
        """Generate data synchronization example"""
        example_file = output_dir / "03_data_sync.md"
        
        content = self.template_env.get_template("data_sync_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_export_examples(self):
        """Generate export operation examples"""
        print("  📤 Generating export operation examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_export_examples(language)
    
    def generate_language_export_examples(self, language: str):
        """Generate export examples for a specific language"""
        examples_dir = self.output_dir / language / "export_operations"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate BIM export
        self.generate_bim_export_example(language, examples_dir)
        
        # Generate CAD export
        self.generate_cad_export_example(language, examples_dir)
        
        # Generate report export
        self.generate_report_export_example(language, examples_dir)
    
    def generate_bim_export_example(self, language: str, output_dir: Path):
        """Generate BIM export example"""
        example_file = output_dir / "01_bim_export.md"
        
        content = self.template_env.get_template("bim_export_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_cad_export_example(self, language: str, output_dir: Path):
        """Generate CAD export example"""
        example_file = output_dir / "02_cad_export.md"
        
        content = self.template_env.get_template("cad_export_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_report_export_example(self, language: str, output_dir: Path):
        """Generate report export example"""
        example_file = output_dir / "03_report_export.md"
        
        content = self.template_env.get_template("report_export_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_error_examples(self):
        """Generate error handling examples"""
        print("  🚨 Generating error handling examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_error_examples(language)
    
    def generate_language_error_examples(self, language: str):
        """Generate error examples for a specific language"""
        examples_dir = self.output_dir / language / "error_handling"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate basic error handling
        self.generate_basic_error_example(language, examples_dir)
        
        # Generate retry logic
        self.generate_retry_logic_example(language, examples_dir)
        
        # Generate custom error handling
        self.generate_custom_error_example(language, examples_dir)
    
    def generate_basic_error_example(self, language: str, output_dir: Path):
        """Generate basic error handling example"""
        example_file = output_dir / "01_basic_error_handling.md"
        
        content = self.template_env.get_template("basic_error_handling_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_retry_logic_example(self, language: str, output_dir: Path):
        """Generate retry logic example"""
        example_file = output_dir / "02_retry_logic.md"
        
        content = self.template_env.get_template("retry_logic_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_custom_error_example(self, language: str, output_dir: Path):
        """Generate custom error handling example"""
        example_file = output_dir / "03_custom_error_handling.md"
        
        content = self.template_env.get_template("custom_error_handling_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_performance_examples(self):
        """Generate performance examples"""
        print("  📈 Generating performance examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_performance_examples(language)
    
    def generate_language_performance_examples(self, language: str):
        """Generate performance examples for a specific language"""
        examples_dir = self.output_dir / language / "performance"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate connection pooling
        self.generate_connection_pooling_example(language, examples_dir)
        
        # Generate request batching
        self.generate_request_batching_example(language, examples_dir)
        
        # Generate caching
        self.generate_caching_example(language, examples_dir)
    
    def generate_connection_pooling_example(self, language: str, output_dir: Path):
        """Generate connection pooling example"""
        example_file = output_dir / "01_connection_pooling.md"
        
        content = self.template_env.get_template("connection_pooling_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_request_batching_example(self, language: str, output_dir: Path):
        """Generate request batching example"""
        example_file = output_dir / "02_request_batching.md"
        
        content = self.template_env.get_template("request_batching_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_caching_example(self, language: str, output_dir: Path):
        """Generate caching example"""
        example_file = output_dir / "03_caching.md"
        
        content = self.template_env.get_template("caching_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_advanced_examples(self):
        """Generate advanced feature examples"""
        print("  🚀 Generating advanced feature examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_advanced_examples(language)
    
    def generate_language_advanced_examples(self, language: str):
        """Generate advanced examples for a specific language"""
        examples_dir = self.output_dir / language / "advanced_features"
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate webhooks
        self.generate_webhooks_example(language, examples_dir)
        
        # Generate real-time updates
        self.generate_realtime_example(language, examples_dir)
        
        # Generate custom middleware
        self.generate_middleware_example(language, examples_dir)
    
    def generate_webhooks_example(self, language: str, output_dir: Path):
        """Generate webhooks example"""
        example_file = output_dir / "01_webhooks.md"
        
        content = self.template_env.get_template("webhooks_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_realtime_example(self, language: str, output_dir: Path):
        """Generate real-time updates example"""
        example_file = output_dir / "02_realtime_updates.md"
        
        content = self.template_env.get_template("realtime_updates_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_middleware_example(self, language: str, output_dir: Path):
        """Generate custom middleware example"""
        example_file = output_dir / "03_custom_middleware.md"
        
        content = self.template_env.get_template("custom_middleware_example.md").render(
            language=language
        )
        
        with open(example_file, 'w') as f:
            f.write(content)
    
    def generate_complete_apps(self):
        """Generate complete application examples"""
        print("  🏗️ Generating complete application examples...")
        
        for language in self.config["examples"]["languages"]:
            self.generate_language_complete_apps(language)
    
    def generate_language_complete_apps(self, language: str):
        """Generate complete apps for a specific language"""
        apps_dir = self.output_dir / language / "complete_apps"
        apps_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate project management app
        self.generate_project_management_app(language, apps_dir)
        
        # Generate asset tracking app
        self.generate_asset_tracking_app(language, apps_dir)
        
        # Generate BIM viewer app
        self.generate_bim_viewer_app(language, apps_dir)
    
    def generate_project_management_app(self, language: str, output_dir: Path):
        """Generate project management app example"""
        app_dir = output_dir / "project_management_app"
        app_dir.mkdir(exist_ok=True)
        
        # Generate main application file
        main_file = app_dir / f"main.{self.get_file_extension(language)}"
        content = self.template_env.get_template(f"project_management_app_{language}.md").render()
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        # Generate README
        readme_file = app_dir / "README.md"
        readme_content = self.template_env.get_template("project_management_app_readme.md").render(
            language=language
        )
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def generate_asset_tracking_app(self, language: str, output_dir: Path):
        """Generate asset tracking app example"""
        app_dir = output_dir / "asset_tracking_app"
        app_dir.mkdir(exist_ok=True)
        
        # Generate main application file
        main_file = app_dir / f"main.{self.get_file_extension(language)}"
        content = self.template_env.get_template(f"asset_tracking_app_{language}.md").render()
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        # Generate README
        readme_file = app_dir / "README.md"
        readme_content = self.template_env.get_template("asset_tracking_app_readme.md").render(
            language=language
        )
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def generate_bim_viewer_app(self, language: str, output_dir: Path):
        """Generate BIM viewer app example"""
        app_dir = output_dir / "bim_viewer_app"
        app_dir.mkdir(exist_ok=True)
        
        # Generate main application file
        main_file = app_dir / f"main.{self.get_file_extension(language)}"
        content = self.template_env.get_template(f"bim_viewer_app_{language}.md").render()
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        # Generate README
        readme_file = app_dir / "README.md"
        readme_content = self.template_env.get_template("bim_viewer_app_readme.md").render(
            language=language
        )
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "typescript": "ts",
            "python": "py",
            "go": "go",
            "java": "java",
            "csharp": "cs",
            "php": "php"
        }
        return extensions.get(language, "txt")

def main():
    """Main entry point"""
    generator = ExampleGenerator()
    generator.generate_all_examples()

if __name__ == "__main__":
    main() 