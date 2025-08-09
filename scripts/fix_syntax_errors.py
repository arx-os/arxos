(((#!/usr/bin/env python3
"""
Syntax Error Fix Script

This script fixes critical syntax errors identified in the development standards analysis.
Focuses on the most critical issues that prevent the codebase from running.

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

def fix_nlp_router_imports(file_path: str) -> bool:
    """Fix missing imports in nlp_router.py"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix missing imports
        content = re.sub(
            r'from services\.intent_detection\.intent_detector\nfrom services\.slot_filling\.slot_filler\nfrom services\.cli_translation\.cli_translator\nfrom services\.models\.nlp_models\nfrom services\.utils\.context_manager',
            'from services.intent_detection.intent_detector import IntentDetector\nfrom services.slot_filling.slot_filler import SlotFiller\nfrom services.cli_translation.cli_translator import CLITranslator\nfrom services.models.nlp_models import NLPModels\nfrom services.utils.context_manager import ContextManager',
            content
        )

        with open(file_path, 'w') as f:
            f.write(content)

        print(f"✅ Fixed imports in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def fix_rule_engine_syntax(file_path: str) -> bool:
    """Fix syntax errors in rule_engine.py"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Fix extra parentheses in lambda functions
        content = re.sub(
            r"'starts_with': lambda x, y: str\(x\)\.startswith\(str\(y\)\)\),",
            "'starts_with': lambda x, y: str(x).startswith(str(y)),",
            content
        )

        content = re.sub(
            r"'ends_with': lambda x, y: str\(x\)\.endswith\(str\(y\)\)\),",
            "'ends_with': lambda x, y: str(x).endswith(str(y)),",
            content
        )

        # Fix missing import
        content = re.sub(
            r'from services\.models\.mcp_models\n\s+MCPFile, MCPRule, RuleCondition, RuleAction, BuildingModel, BuildingObject,\n\s+ValidationResult, ValidationViolation, MCPValidationReport, ComplianceReport,\n\s+RuleSeverity, RuleCategory, ConditionType, ActionType,\n\s+serialize_mcp_file, deserialize_mcp_file\n\s+\)',
            'from services.models.mcp_models import (\n    MCPFile, MCPRule, RuleCondition, RuleAction, BuildingModel, BuildingObject,\n    ValidationResult, ValidationViolation, MCPValidationReport, ComplianceReport,\n    RuleSeverity, RuleCategory, ConditionType, ActionType,\n    serialize_mcp_file, deserialize_mcp_file\n)',
            content
        )

        with open(file_path, 'w') as f:
            f.write(content)

        print(f"✅ Fixed syntax in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def fix_planarx_syntax_errors() -> bool:
    """Fix syntax errors in planarx community files"""
    planarx_files = [
        "services/planarx/planarx-community/reputation/routes.py",
        "services/planarx/planarx-community/collab/routes.py",
        "services/planarx/planarx-community/governance/voting_engine.py",
        "services/planarx/planarx-community/mod/user_roles.py",
        "services/planarx/planarx-community/funding/__init__.py",
        "services/planarx/planarx-community/funding/routes/init_escrow.py"
    ]

    success = True
    for file_path in planarx_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Fix common syntax errors
                # Remove unmatched parentheses
                content = re.sub(r'\)\s*\)', ')', content)
                content = re.sub(r'\(\s*\(', '(', content)

                # Fix invalid syntax patterns
                content = re.sub(r'from\s+(\w+)\s*$', r'from \1 import *', content, flags=re.MULTILINE)

                with open(file_path, 'w') as f:
                    f.write(content)

                print(f"✅ Fixed syntax in {file_path}")
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                success = False

    return success

def fix_ai_service_syntax_errors() -> bool:
    """Fix syntax errors in AI service files"""
    ai_files = [
        "services/ai/arx-nlp/__init__.py",
        "services/ai/arx-nlp/intent_mapper.py",
        "services/ai/arx-mcp/__init__.py",
        "services/ai/arx-mcp/validate/__init__.py",
        "services/ai/arx-mcp/models/__init__.py",
        "services/ai/arx-mcp/report/__init__.py",
        "services/ai/arx-nlp/intent_detection/__init__.py",
        "services/ai/arx-nlp/intent_detection/intent_detector.py",
        "services/ai/arx-nlp/utils/context_manager.py",
        "services/ai/arx-nlp/utils/__init__.py",
        "services/ai/arx-nlp/models/__init__.py",
        "services/ai/arx-nlp/slot_filling/slot_filler.py",
        "services/ai/arx-nlp/slot_filling/__init__.py",
        "services/ai/arx-nlp/cli_translation/__init__.py",
        "services/ai/arx-nlp/cli_translation/cli_translator.py"
    ]

    success = True
    for file_path in ai_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Fix common syntax errors
                # Remove unmatched parentheses
                content = re.sub(r'\)\s*\)', ')', content)
                content = re.sub(r'\(\s*\(', '(', content)

                # Fix invalid syntax patterns
                content = re.sub(r'from\s+(\w+)\s*$', r'from \1 import *', content, flags=re.MULTILINE)

                with open(file_path, 'w') as f:
                    f.write(content)

                print(f"✅ Fixed syntax in {file_path}")
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
                success = False

    return success

def main():
    """Main function to fix all syntax errors"""
    print("🔧 Fixing Critical Syntax Errors")
    print("=" * 50)

    # Fix specific critical files
    critical_fixes = [
        ("services/ai/arx-nlp/nlp_router.py", fix_nlp_router_imports),
        ("services/ai/arx-mcp/validate/rule_engine.py", fix_rule_engine_syntax),
    ]

    success_count = 0
    total_count = 0

    for file_path, fix_func in critical_fixes:
        if os.path.exists(file_path):
            total_count += 1
            if fix_func(file_path):
                success_count += 1

    # Fix planarx syntax errors
    if fix_planarx_syntax_errors():
        success_count += 1
    total_count += 1

    # Fix AI service syntax errors
    if fix_ai_service_syntax_errors():
        success_count += 1
    total_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_count} fixes successful")

    if success_count == total_count:
        print("✅ All critical syntax errors fixed!")
        return 0
    else:
        print("⚠️  Some syntax errors could not be fixed automatically")
        return 1

if __name__ == "__main__":
    sys.exit(main()
