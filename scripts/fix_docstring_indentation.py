#!/usr/bin/env python3
"""
Fix Docstring Indentation Issues

This script fixes the docstring indentation issues that are causing syntax errors.
The main issue is that docstrings are not properly indented after function/class definitions.

Target Issues:
- Docstrings not properly indented after function definitions
- Docstrings not properly indented after class definitions
- Missing function bodies after docstrings

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional


class DocstringIndentationFixer:
    """Fixes docstring indentation issues"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

        # Files with docstring indentation issues
        self.files_with_indentation_issues = [
            "plugins/example_behavior_plugin.py",
            "cli/gus.py",
            "cli/svgx-cli.py",
            "svgx_engine/deploy_production.py",
            "svgx_engine/app.py",
            "api/middleware.py",
            "application/logging_config.py",
            "application/transaction.py",
            "application/exceptions.py",
            "domain/services.py",
            "domain/events.py",
            "domain/value_objects.py",
            "domain/exceptions.py",
            "services/iot/telemetry_api.py",
            "services/iot/device_registry.py",
            "services/ai/main.py",
            "services/gus/main.py",
            "services/gus/core/pdf_analysis.py",
            "services/planarx/planarx-community/user_agreement_flags.py",
            "services/planarx/planarx-community/main.py",
            "services/planarx/planarx-funding/grant_eligibility.py",
            "services/planarx/planarx-funding/hooks/milestone_hook.py",
            "services/planarx/planarx-community/frontend/onboarding_flow.py",
            "services/planarx/planarx-community/reputation/badges.py",
            "services/planarx/planarx-community/reputation/scoring_engine.py",
            "services/planarx/planarx-community/workflows/task_trigger_map.py",
            "services/planarx/planarx-community/integrations/build_hooks.py",
            "services/planarx/planarx-community/collab/realtime_editor.py",
            "services/planarx/planarx-community/collab/annotations.py",
            "services/planarx/planarx-community/examples/funding_escrow_demo.py",
            "services/planarx/planarx-community/notifications/collab_events.py",
            "services/planarx/planarx-community/mod/flagging.py",
            "services/planarx/planarx-community/mod/mod_queue.py",
            "services/planarx/planarx-community/funding/escrow_engine.py",
            "services/planarx/planarx-community/governance/models/board_roles.py",
            "services/ai/config/settings.py",
            "services/ai/arx-mcp/validate/rule_engine.py",
            "services/iot/tools/validate_schema.py",
            "services/iot/protocol/arxlink_sync.py",
            "domain/value_objects/pdf_analysis_value_objects.py",
            "infrastructure/database/session.py",
            "infrastructure/repositories/postgresql_pdf_analysis_repository.py",
            "infrastructure/services/file_storage_service.py",
            "infrastructure/services/gus_service.py",
            "infrastructure/deploy/monitoring/alerting_workflows.py",
            "infrastructure/database/tools/schema_validator.py",
            "infrastructure/database/tools/validate_documentation.py",
            "infrastructure/database/tools/audit_constraints.py",
            "infrastructure/database/alembic/versions/001_create_initial_schema.py",
            "application/use_cases/pdf_analysis_use_cases.py",
            "application/use_cases/building_hierarchy_use_cases.py",
            "application/use_cases/room_use_cases.py",
            "application/use_cases/user_use_cases.py",
            "application/use_cases/building_use_cases.py",
            "application/use_cases/device_use_cases.py",
            "application/use_cases/floor_use_cases.py",
            "application/use_cases/project_use_cases.py",
            "application/services/pdf_analysis_orchestrator.py",
            "svgx_engine/tools/svgx_linter.py",
            "svgx_engine/core/precision_system.py",
            "svgx_engine/core/cad_system_integration.py",
            "svgx_engine/core/precision_config.py",
            "svgx_engine/core/precision_input.py",
            "svgx_engine/core/constraint_system.py",
            "svgx_engine/core/dimensioning_system.py",
            "svgx_engine/core/precision_input_integration.py",
            "svgx_engine/core/assembly_system.py",
            "svgx_engine/core/drawing_views_system.py",
            "svgx_engine/core/grid_snap_system.py",
            "svgx_engine/core/precision_hooks.py",
            "svgx_engine/config/enterprise_config.py",
            "svgx_engine/runtime/custom_behavior_plugin_system.py",
            "svgx_engine/runtime/time_based_trigger_system.py",
            "svgx_engine/runtime/performance_optimization_engine.py",
            "svgx_engine/runtime/animation_behavior_system.py",
            "svgx_engine/runtime/ui_annotation_handler.py",
            "svgx_engine/runtime/physics_engine.py",
            "svgx_engine/runtime/event_driven_behavior_engine.py",
            "svgx_engine/runtime/ui_navigation_handler.py",
            "svgx_engine/runtime/__init__.py",
            "svgx_engine/runtime/ui_editing_handler.py",
            "svgx_engine/runtime/ui_selection_handler.py",
            "svgx_engine/runtime/advanced_behavior_engine.py",
            "svgx_engine/runtime/advanced_state_machine.py",
            "svgx_engine/runtime/advanced_rule_engine.py",
            "svgx_engine/utils/unified_error_handler.py",
            "svgx_engine/utils/logging_config.py",
            "svgx_engine/utils/precision_manager.py",
            "svgx_engine/utils/database.py",
            "svgx_engine/utils/telemetry.py",
            "svgx_engine/utils/errors.py",
            "svgx_engine/utils/permission_utils.py",
            "svgx_engine/utils/performance.py",
            "svgx_engine/models/bim_relationships.py",
            "svgx_engine/models/bim_metadata.py",
            "svgx_engine/models/database.py",
            "svgx_engine/models/bim.py",
            "svgx_engine/models/svgx.py",
            "svgx_engine/models/error_response.py",
            "svgx_engine/parser/parser.py",
            "svgx_engine/parser/geometry.py",
            "svgx_engine/schema/svgx_schema.py",
            "svgx_engine/deployment/enterprise_deployment.py",
            "svgx_engine/infrastructure/container.py",
            "svgx_engine/compiler/svgx_to_ifc.py",
            "svgx_engine/compiler/__init__.py",
            "svgx_engine/compiler/svgx_to_gltf.py",
            "svgx_engine/compiler/svgx_to_svg.py",
            "svgx_engine/compiler/svgx_to_json.py",
            "svgx_engine/services/ai_integration_service.py",
            "svgx_engine/services/enhanced_physics_engine.py",
            "svgx_engine/services/elite_parser.py",
            "svgx_engine/services/cache/redis_client.py",
            "svgx_engine/services/cmms/asset_tracking.py",
            "svgx_engine/services/cmms/cmms_integration.py",
            "svgx_engine/services/cmms/maintenance_scheduling.py",
            "svgx_engine/services/cad/constraint_system.py",
            "svgx_engine/services/cad/dimensioning_system.py",
            "svgx_engine/services/cad/precision_drawing.py",
            "svgx_engine/services/ai/ai_integration_service.py",
            "svgx_engine/services/ai/ai_frontend_integration.py",
            "svgx_engine/services/ai/user_pattern_learning.py",
            "svgx_engine/services/ai/advanced_ai_service.py",
            "svgx_engine/services/symbols/symbol_recognition.py",
            "svgx_engine/services/physics/advanced_thermal_analysis.py",
            "svgx_engine/services/performance/cdn_service.py",
            "svgx_engine/services/logging/structured_logger.py",
            "svgx_engine/services/notifications/monitoring.py",
            "svgx_engine/services/notifications/go_client_optimized.py",
            "svgx_engine/domain/events/building_events.py",
            "svgx_engine/domain/services/building_service.py",
            "svgx_engine/infrastructure/repositories/in_memory_building_repository.py",
            "svgx_engine/application/use_cases/building_use_cases.py",
            "svgx_engine/runtime/behavior/ui_event_dispatcher.py",
            "sdk/generator/docs_generator.py",
            "sdk/generator/generator.py",
            "core/security/auth_middleware.py",
            "core/shared/models/error.py"
        ]

    def fix_docstring_indentation_issues(self):
        """Fix docstring indentation issues"""
        print("🔧 Fixing Docstring Indentation Issues")
        print("=" * 60)

        success_count = 0
        error_count = 0

        for file_path in self.files_with_indentation_issues:
            full_path = self.project_root / file_path

            if not full_path.exists():
                print(f"⚠️  File not found: {file_path}")
                continue

            try:
                if self._fix_file_docstring_indentation(full_path):
                    print(f"✅ Fixed docstring indentation in: {file_path}")
                    success_count += 1
                else:
                    print(f"ℹ️  No docstring indentation issues found in: {file_path}")

            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"   ✅ Successfully fixed: {success_count} files")
        print(f"   ❌ Errors: {error_count} files")
        print(f"   📁 Total processed: {len(self.files_with_indentation_issues)} files")

    def _fix_file_docstring_indentation(self, file_path: Path) -> bool:
        """Fix docstring indentation issues in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix docstring indentation issues
            content = self._fix_docstring_indentation_patterns(content)

            # Validate syntax
            if not self._validate_syntax(content):
                print(f"⚠️  Syntax validation failed for {file_path}")
                return False

            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def _fix_docstring_indentation_patterns(self, content: str) -> str:
        """Fix docstring indentation patterns"""

        # Pattern 1: Function definition followed by unindented docstring
        # def func():
        # """
        # docstring
        # """
        content = re.sub(
            r'(def [^:]+:)\n\s*("""[^"]*""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # Pattern 2: Class definition followed by unindented docstring
        # class Class:
        # """
        # docstring
        # """
        content = re.sub(
            r'(class [^:]+:)\n\s*("""[^"]*""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # Pattern 3: Function definition followed by unindented docstring with multiple lines
        # def func():
        # """
        # docstring
        # content
        # """
        content = re.sub(
            r'(def [^:]+:)\n\s*("""[^"]*?""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # Pattern 4: Class definition followed by unindented docstring with multiple lines
        # class Class:
        # """
        # docstring
        # content
        # """
        content = re.sub(
            r'(class [^:]+:)\n\s*("""[^"]*?""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # Pattern 5: Async function definition followed by unindented docstring
        # async def func():
        # """
        # docstring
        # """
        content = re.sub(
            r'(async def [^:]+:)\n\s*("""[^"]*""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        # Pattern 6: Async function definition followed by unindented docstring with multiple lines
        # async def func():
        # """
        # docstring
        # content
        # """
        content = re.sub(
            r'(async def [^:]+:)\n\s*("""[^"]*?""")',"
            r'\1\n        \2',
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        return content

    def _validate_syntax(self, content: str) -> bool:
        """Validate that the content has valid Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def create_indentation_fix_example(self):
        """Create an example of proper docstring indentation"""
        example = '''
# Example of Proper Docstring Indentation

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ExampleClass:
    """
    Example class with proper docstring indentation.

    Attributes:
        config: Configuration dictionary

    Methods:
        process_data: Process input data
        validate_input: Validate input parameters
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the class.

        Args:
            config: Configuration dictionary

        Returns:
            None
        """
        self.config = config or {}
        self.logger = logger

    async def process_data(self, data: str) -> Dict[str, Any]:
        """
        Process input data asynchronously.

        Args:
            data: Input data to process

        Returns:
            Processed data dictionary

        Raises:
            ValueError: If data is invalid
        """
        try:
            result = {
                "status": "success",
                "data": data,
                "config": self.config
            }
            return result
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            raise ValueError(f"Invalid data: {e}")

    def validate_input(self, input_data: str) -> bool:
        """
        Validate input parameters.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(input_data and input_data.strip()
# Usage example
if __name__ == "__main__":
    example = ExampleClass({"test": "value"})
    result = await example.process_data("test_data")
    print(result)
'''

        example_path = self.project_root / "docs" / "proper_docstring_indentation_example.py"
        example_path.parent.mkdir(exist_ok=True)

        with open(example_path, 'w') as f:
            f.write(example)

        print(f"📝 Created proper docstring indentation example: {example_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_docstring_indentation.py [--dry-run] [--example]")
        sys.exit(1)

    project_root = "."
    dry_run = "--dry-run" in sys.argv
    create_example = "--example" in sys.argv

    fixer = DocstringIndentationFixer(project_root)

    if create_example:
        fixer.create_indentation_fix_example()

    if not dry_run:
        fixer.fix_docstring_indentation_issues()
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("Files that would be fixed:")
        for file_path in fixer.files_with_indentation_issues:
            full_path = Path(project_root) / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (not found)")


if __name__ == "__main__":
    main()
