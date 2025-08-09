"""
CLI Translator for Arxos NLP System

This module provides CLI command generation functionality to convert
NLP intents and slots into structured ArxCLI commands.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from services.models.nlp_models import services.models.nlp_models
@dataclass
class CommandTemplate:
    """Template for CLI command generation"""
    intent_type: IntentType
    command: str
    subcommand: Optional[str] = None
    required_slots: List[SlotType] = None
    optional_slots: List[SlotType] = None
    argument_mapping: Dict[str, str] = None
    option_mapping: Dict[str, str] = None

    def __post_init__(self):
        if self.required_slots is None:
            self.required_slots = []
        if self.optional_slots is None:
            self.optional_slots = []
        if self.argument_mapping is None:
            self.argument_mapping = {}
        if self.option_mapping is None:
            self.option_mapping = {}


class CLITranslator:
    """
    CLI Translator for converting NLP intents to ArxCLI commands

    This class provides:
    - Command template matching
    - Argument and option mapping
    - Command validation
    - Command execution simulation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CLI Translator

        Args:
            config: Configuration dictionary for CLI translation
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Load command templates
        self._load_command_templates()

    def _load_command_templates(self):
        """Load CLI command templates"""
        self.command_templates = [
            # Create commands
            CommandTemplate(
                intent_type=IntentType.CREATE,
                command="arx",
                subcommand="create",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"color": "--color", "size": "--size", "type": "--type"}
            ),

            # Modify commands
            CommandTemplate(
                intent_type=IntentType.MODIFY,
                command="arx",
                subcommand="modify",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"property": "--property", "value": "--value"}
            ),

            # Delete commands
            CommandTemplate(
                intent_type=IntentType.DELETE,
                command="arx",
                subcommand="delete",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"force": "--force", "recursive": "--recursive"}
            ),

            # Move commands
            CommandTemplate(
                intent_type=IntentType.MOVE,
                command="arx",
                subcommand="move",
                required_slots=[SlotType.OBJECT_TYPE, SlotType.TARGET],
                argument_mapping={"object_type": "OBJECT_TYPE", "target": "TARGET"},
                option_mapping={"force": "--force"}
            ),

            # Query commands
            CommandTemplate(
                intent_type=IntentType.QUERY,
                command="arx",
                subcommand="query",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"filter": "--filter", "format": "--format"}
            ),

            # Export commands
            CommandTemplate(
                intent_type=IntentType.EXPORT,
                command="arx",
                subcommand="export",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"format": "--format", "output": "--output"}
            ),

            # Import commands
            CommandTemplate(
                intent_type=IntentType.IMPORT,
                command="arx",
                subcommand="import",
                required_slots=[SlotType.OBJECT_TYPE, SlotType.SOURCE],
                argument_mapping={"object_type": "OBJECT_TYPE", "source": "SOURCE"},
                option_mapping={"format": "--format", "force": "--force"}
            ),

            # Validate commands
            CommandTemplate(
                intent_type=IntentType.VALIDATE,
                command="arx",
                subcommand="validate",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"rules": "--rules", "strict": "--strict"}
            ),

            # Sync commands
            CommandTemplate(
                intent_type=IntentType.SYNC,
                command="arx",
                subcommand="sync",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"target": "--target", "force": "--force"}
            ),

            # Annotate commands
            CommandTemplate(
                intent_type=IntentType.ANNOTATE,
                command="arx",
                subcommand="annotate",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"note": "--note", "type": "--type"}
            ),

            # Inspect commands
            CommandTemplate(
                intent_type=IntentType.INSPECT,
                command="arx",
                subcommand="inspect",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"details": "--details", "format": "--format"}
            ),

            # Report commands
            CommandTemplate(
                intent_type=IntentType.REPORT,
                command="arx",
                subcommand="report",
                required_slots=[SlotType.OBJECT_TYPE],
                argument_mapping={"object_type": "OBJECT_TYPE"},
                option_mapping={"type": "--type", "format": "--format", "output": "--output"}
            )
        ]

    def generate_command(self, intent: Intent, slot_result: SlotResult, context: Any = None) -> CLICommand:
        """
        Generate CLI command from intent and slots

        Args:
            intent: Detected intent
            slot_result: Extracted slots
            context: Optional context information

        Returns:
            CLICommand with generated command structure
        """
        try:
            # Find matching command template
            template = self._find_command_template(intent.intent_type)
            if not template:
                return self._create_error_command(intent, "No command template found")

            # Validate required slots
            missing_slots = self._validate_required_slots(template, slot_result.slots)
            if missing_slots:
                return self._create_error_command(intent, f"Missing required slots: {missing_slots}")

            # Generate command arguments
            arguments = self._generate_arguments(template, slot_result.slots)

            # Generate command options
            options = self._generate_options(template, slot_result.slots)

            # Create CLI command
            cli_command = CLICommand(
                command=template.command,
                subcommand=template.subcommand,
                arguments=arguments,
                options=options,
                metadata={
                    "intent_type": intent.intent_type.value,
                    "confidence": intent.confidence,
                    "template_used": template.intent_type.value
                }
            )

            self.logger.info(f"Generated CLI command: {cli_command.to_string()}")
            return cli_command

        except Exception as e:
            self.logger.error(f"Error generating CLI command: {e}")
            return self._create_error_command(intent, str(e)

    def _find_command_template(self, intent_type: IntentType) -> Optional[CommandTemplate]:
        """Find command template for intent type"""
        for template in self.command_templates:
            if template.intent_type == intent_type:
                return template
        return None

    def _validate_required_slots(self, template: CommandTemplate, slots: List[Slot]) -> List[str]:
        """Validate that all required slots are present"""
        missing_slots = []
        slot_types = [slot.slot_type for slot in slots]

        for required_slot in template.required_slots:
            if required_slot not in slot_types:
                missing_slots.append(required_slot.value)

        return missing_slots

    def _generate_arguments(self, template: CommandTemplate, slots: List[Slot]) -> List[str]:
        """Generate command arguments from slots"""
        arguments = []

        for slot in slots:
            if slot.slot_type in template.argument_mapping:
                # Map slot to argument position
                arg_name = template.argument_mapping[slot.slot_type]
                if arg_name == "OBJECT_TYPE":
                    arguments.append(slot.value)
                elif arg_name == "TARGET":
                    arguments.append(slot.value)
                elif arg_name == "SOURCE":
                    arguments.append(slot.value)
                else:
                    arguments.append(slot.value)

        return arguments

    def _generate_options(self, template: CommandTemplate, slots: List[Slot]) -> Dict[str, Any]:
        """Generate command options from slots"""
        options = {}

        for slot in slots:
            if slot.slot_type in template.option_mapping:
                option_name = template.option_mapping[slot.slot_type]
                options[option_name] = slot.value
            else:
                # Handle common option mappings
                if slot.slot_type == SlotType.FORMAT:
                    options["--format"] = slot.value
                elif slot.slot_type == SlotType.LOCATION:
                    options["--location"] = slot.value
                elif slot.slot_type == SlotType.PROPERTY:
                    options["--property"] = slot.value
                elif slot.slot_type == SlotType.VALUE:
                    options["--value"] = slot.value
                elif slot.slot_type == SlotType.CONDITION:
                    options["--filter"] = slot.value

        return options

    def _create_error_command(self, intent: Intent, error: str) -> CLICommand:
        """Create error command for failed translation"""
        return CLICommand(
            command="arx",
            subcommand="help",
            arguments=["--error", error],
            options={},
            metadata={
                "intent_type": intent.intent_type.value,
                "confidence": intent.confidence,
                "error": error
            }
        )

    def validate_command(self, cli_command: CLICommand) -> bool:
        """
        Validate generated CLI command

        Args:
            cli_command: CLI command to validate

        Returns:
            True if command is valid, False otherwise
        """
        # Check if command exists
        if not cli_command.command:
            return False

        # Check if subcommand is valid
        valid_subcommands = [
            "create", "modify", "delete", "move", "query", "export",
            "import", "validate", "sync", "annotate", "inspect", "report"
        ]

        if cli_command.subcommand and cli_command.subcommand not in valid_subcommands:
            return False

        # Check if required arguments are present
        if cli_command.subcommand in ["create", "modify", "delete", "query", "export", "validate", "sync", "annotate", "inspect", "report"]:
            if not cli_command.arguments:
                return False

        return True

    def get_command_help(self, command: str, subcommand: Optional[str] = None) -> str:
        """
        Get help information for CLI command

        Args:
            command: Main command
            subcommand: Optional subcommand

        Returns:
            Help text for the command
        """
        help_texts = {
            "create": "Create new building objects: arx create <object_type> [options]",
            "modify": "Modify existing objects: arx modify <object> [options]",
            "delete": "Delete objects: arx delete <object> [options]",
            "move": "Move objects: arx move <object> <target> [options]",
            "query": "Query object information: arx query <object> [options]",
            "export": "Export object data: arx export <object> [options]",
            "import": "Import object data: arx import <object> <source> [options]",
            "validate": "Validate object compliance: arx validate <object> [options]",
            "sync": "Synchronize object data: arx sync <object> [options]",
            "annotate": "Add annotations: arx annotate <object> [options]",
            "inspect": "Inspect object details: arx inspect <object> [options]",
            "report": "Generate reports: arx report <object> [options]"
        }

        if subcommand:
            return help_texts.get(subcommand, f"No help available for subcommand: {subcommand}")
        else:
            return "ArxCLI commands: create, modify, delete, move, query, export, import, validate, sync, annotate, inspect, report"

    def simulate_execution(self, cli_command: CLICommand) -> Dict[str, Any]:
        """
        Simulate CLI command execution

        Args:
            cli_command: CLI command to simulate

        Returns:
            Simulation result
        """
        # This is a simulation - in a real implementation, this would
        # actually execute the command and return results

        simulation_result = {
            "command": cli_command.to_string(),
            "status": "simulated",
            "output": f"Simulated execution of: {cli_command.to_string()}",
            "success": True,
            "metadata": cli_command.metadata
        }

        # Add intent-specific simulation results
        if cli_command.subcommand == "create":
            simulation_result["output"] = f"Created {cli_command.arguments[0] if cli_command.arguments else 'object'}"
        elif cli_command.subcommand == "modify":
            simulation_result["output"] = f"Modified {cli_command.arguments[0] if cli_command.arguments else 'object'}"
        elif cli_command.subcommand == "delete":
            simulation_result["output"] = f"Deleted {cli_command.arguments[0] if cli_command.arguments else 'object'}"
        elif cli_command.subcommand == "query":
            simulation_result["output"] = f"Query results for {cli_command.arguments[0] if cli_command.arguments else 'object'}"
        elif cli_command.subcommand == "export":
            simulation_result["output"] = f"Exported {cli_command.arguments[0] if cli_command.arguments else 'object'}"

        return simulation_result

    def get_suggestions(self, partial_command: str) -> List[str]:
        """
        Get command suggestions based on partial input

        Args:
            partial_command: Partial CLI command

        Returns:
            List of suggested completions
        """
        suggestions = []
        partial_lower = partial_command.lower().strip()

        # Get subcommand suggestions
        valid_subcommands = [
            "create", "modify", "delete", "move", "query", "export",
            "import", "validate", "sync", "annotate", "inspect", "report"
        ]

        for subcmd in valid_subcommands:
            if partial_lower in subcmd or subcmd.startswith(partial_lower):
                suggestions.append(f"arx {subcmd}")

        # Get object type suggestions
        common_objects = [
            "room", "wall", "door", "window", "fixture", "equipment", "system"
        ]

        for obj in common_objects:
            if partial_lower in obj or obj.startswith(partial_lower):
                suggestions.append(f"arx create {obj}")
                suggestions.append(f"arx modify {obj}")
                suggestions.append(f"arx query {obj}")

        return list(set(suggestions)[:10]  # Limit to 10 unique suggestions


# Convenience function for quick CLI translation
def translate_to_cli(intent: Intent, slot_result: SlotResult, config: Optional[Dict[str, Any]] = None) -> CLICommand:
    """
    Convenience function for quick CLI translation

    Args:
        intent: Detected intent
        slot_result: Extracted slots
        config: Optional configuration

    Returns:
        CLICommand with generated command structure
    """
    translator = CLITranslator(config)
    return translator.generate_command(intent, slot_result) ))
