"""
Tests for NLP Router

This module contains tests for the main NLP router functionality.
"""

import pytest
from unittest.mock import Mock, patch

from arx_nlp import NLPRouter, NLPContext, IntentType, SlotType
from arx_nlp.models.nlp_models import Intent, Slot, SlotResult, CLICommand


class TestNLPRouter:
    """Test cases for NLPRouter"""

    def setup_method(self):
        """Set up test fixtures"""
        self.router = NLPRouter()
        self.context = NLPContext(
            user_id="test_user",
            building_id="test_building",
            floor_id="floor_1"
        )

    def test_basic_intent_detection(self):
        """Test basic intent detection"""
        result = self.router.parse_natural_language("create a bedroom")

        assert result.intent.intent_type == IntentType.CREATE
        assert result.confidence > 0.5
        assert "create" in result.cli_command.command

    def test_modify_intent_detection(self):
        """Test modify intent detection"""
        result = self.router.parse_natural_language("modify the kitchen")

        assert result.intent.intent_type == IntentType.MODIFY
        assert result.confidence > 0.5
        assert "modify" in result.cli_command.subcommand

    def test_query_intent_detection(self):
        """Test query intent detection"""
        result = self.router.parse_natural_language("find all doors")

        assert result.intent.intent_type == IntentType.QUERY
        assert result.confidence > 0.5
        assert "query" in result.cli_command.subcommand

    def test_slot_extraction(self):
        """Test slot extraction"""
        result = self.router.parse_natural_language("create a red bedroom")

        # Check that object type slot is extracted
        object_slots = [slot for slot in result.slots if slot.slot_type == SlotType.OBJECT_TYPE]
        assert len(object_slots) > 0

        # Check that property slot is extracted
        property_slots = [slot for slot in result.slots if slot.slot_type == SlotType.PROPERTY]
        assert len(property_slots) > 0

    def test_cli_command_generation(self):
        """Test CLI command generation"""
        result = self.router.parse_natural_language("create a bedroom")

        assert result.cli_command.command == "arx"
        assert result.cli_command.subcommand == "create"
        assert len(result.cli_command.arguments) > 0

    def test_context_resolution(self):
        """Test context resolution"""
        result = self.router.parse_natural_language("create a bedroom", self.context)

        assert result.context.user_id == "test_user"
        assert result.context.building_id == "test_building"
        assert result.context.session_id is not None

    def test_batch_processing(self):
        """Test batch processing"""
        texts = [
            "create a bedroom",
            "modify the kitchen",
            "find all doors"
        ]

        results = self.router.batch_process(texts, self.context)

        assert len(results) == 3
        assert results[0].intent.intent_type == IntentType.CREATE
        assert results[1].intent.intent_type == IntentType.MODIFY
        assert results[2].intent.intent_type == IntentType.QUERY

    def test_suggestions(self):
        """Test command suggestions"""
        suggestions = self.router.get_suggestions("create")

        assert len(suggestions) > 0
        assert any("create" in suggestion for suggestion in suggestions)

    def test_error_handling(self):
        """Test error handling for invalid input"""
        result = self.router.parse_natural_language("invalid command that makes no sense")

        # Should return a response with low confidence
        assert result.confidence < 0.5
        assert result.cli_command.command == "arx"
        assert result.cli_command.subcommand == "help"

    def test_validation(self):
        """Test command validation"""
        result = self.router.parse_natural_language("create a bedroom")

        is_valid = self.router.validate_command(result.cli_command)
        assert is_valid

    def test_help_functionality(self):
        """Test help functionality"""
        help_text = self.router.get_help()
        assert "Supported Commands" in help_text

        create_help = self.router.get_help("create")
        assert "create" in create_help.lower()

    def test_configuration(self):
        """Test router configuration"""
        config = {
            "intent_detection": {"confidence_threshold": 0.8},
            "slot_filling": {"enable_validation": True},
            "cli_translation": {"validate_commands": True}
        }

        configured_router = NLPRouter(config)
        result = configured_router.parse_natural_language("create a bedroom")

        assert result.intent.intent_type == IntentType.CREATE
        assert result.cli_command.command == "arx"

    def test_object_mappings(self):
        """Test object type mappings"""
        result = self.router.parse_natural_language("create a kitchen")

        # Check that kitchen is mapped to room type
        object_slots = [slot for slot in result.slots if slot.slot_type == SlotType.OBJECT_TYPE]
        assert len(object_slots) > 0

        # The mapped value should be "room" for kitchen
        kitchen_slot = next((slot for slot in object_slots if "kitchen" in slot.original_value), None)
        if kitchen_slot:
            assert kitchen_slot.value == "room"

    def test_complex_commands(self):
        """Test complex command processing"""
        result = self.router.parse_natural_language("create a red bedroom with size 20x15 on floor 2")

        assert result.intent.intent_type == IntentType.CREATE
        assert result.confidence > 0.5

        # Check for multiple slots
        assert len(result.slots) >= 3  # object_type, color, dimensions, location

        # Check CLI command
        assert result.cli_command.command == "arx"
        assert result.cli_command.subcommand == "create"


class TestIntentMapper:
    """Test cases for IntentMapper"""

    def setup_method(self):
        """Set up test fixtures"""
        from arx_nlp.intent_mapper import IntentMapper
        self.mapper = IntentMapper()

    def test_intent_detection(self):
        """Test intent detection"""
        intent = self.mapper.detect_intent("create a room")

        assert intent.intent_type == IntentType.CREATE
        assert intent.confidence > 0.5

    def test_suggestions(self):
        """Test intent suggestions"""
        suggestions = self.mapper.get_suggestions("create")

        assert len(suggestions) > 0
        assert any("create" in suggestion for suggestion in suggestions)

    def test_validation(self):
        """Test intent validation"""
        intent = Intent(
            intent_type=IntentType.CREATE,
            confidence=0.8,
            raw_text="create a room"
        )

        is_valid = self.mapper.validate_intent(intent)
        assert is_valid

    def test_help(self):
        """Test help functionality"""
        help_text = self.mapper.get_intent_help(IntentType.CREATE)
        assert "create" in help_text.lower()


class TestSlotFiller:
    """Test cases for SlotFiller"""

    def setup_method(self):
        """Set up test fixtures"""
        from arx_nlp.slot_filling.slot_filler import SlotFiller
        self.filler = SlotFiller()

    def test_slot_extraction(self):
        """Test slot extraction"""
        slot_result = self.filler.extract_slots("create a red bedroom", IntentType.CREATE)

        assert len(slot_result.slots) > 0
        assert slot_result.confidence > 0.0

    def test_suggestions(self):
        """Test slot suggestions"""
        suggestions = self.filler.get_suggestions("color")

        assert len(suggestions) > 0
        assert any("color" in suggestion for suggestion in suggestions)

    def test_validation(self):
        """Test slot validation"""
        slot = Slot(
            slot_type=SlotType.OBJECT_TYPE,
            value="room",
            confidence=0.8
        )

        is_valid = self.filler.validate_slot(slot)
        assert is_valid

    def test_help(self):
        """Test help functionality"""
        help_text = self.filler.get_slot_help(SlotType.OBJECT_TYPE)
        assert "object" in help_text.lower()


class TestCLITranslator:
    """Test cases for CLITranslator"""

    def setup_method(self):
        """Set up test fixtures"""
        from arx_nlp.cli_translation.cli_translator import CLITranslator
        self.translator = CLITranslator()

    def test_command_generation(self):
        """Test CLI command generation"""
        intent = Intent(
            intent_type=IntentType.CREATE,
            confidence=0.8,
            raw_text="create a room"
        )

        slot_result = SlotResult(
            slots=[
                Slot(slot_type=SlotType.OBJECT_TYPE, value="room", confidence=0.9)
            ],
            confidence=0.9
        )

        cli_command = self.translator.generate_command(intent, slot_result)

        assert cli_command.command == "arx"
        assert cli_command.subcommand == "create"
        assert len(cli_command.arguments) > 0

    def test_validation(self):
        """Test command validation"""
        cli_command = CLICommand(
            command="arx",
            subcommand="create",
            arguments=["room"]
        )

        is_valid = self.translator.validate_command(cli_command)
        assert is_valid

    def test_simulation(self):
        """Test command simulation"""
        cli_command = CLICommand(
            command="arx",
            subcommand="create",
            arguments=["room"]
        )

        simulation = self.translator.simulate_execution(cli_command)

        assert simulation["status"] == "simulated"
        assert simulation["success"] is True

    def test_suggestions(self):
        """Test command suggestions"""
        suggestions = self.translator.get_suggestions("create")

        assert len(suggestions) > 0
        assert any("create" in suggestion for suggestion in suggestions)

    def test_help(self):
        """Test help functionality"""
        help_text = self.translator.get_command_help("arx", "create")
        assert "create" in help_text.lower()


if __name__ == "__main__":
    pytest.main([__file__])
