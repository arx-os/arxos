"""
Basic NLP Integration Example

This example demonstrates the basic usage of the Arxos NLP Integration
system for processing natural language commands and converting them to
ArxCLI commands.
"""

import sys
import os
import logging

# Add the parent directory to the path to import arx_nlp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arx_nlp import NLPRouter, NLPContext, IntentType, SlotType
from arx_nlp.models.nlp_models import Intent, Slot, SlotResult, CLICommand


def setup_logging():
    """Set up logging for the example"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_nlp_result(result):
    """Print NLP processing result"""
    print(f"Original Text: '{result.original_text}'")
    print(f"Intent: {result.intent.intent_type.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"CLI Command: {result.cli_command.to_string()}")

    if result.slots:
        print("Extracted Slots:")
        for slot in result.slots:
            print(
                f"  - {slot.slot_type.value}: '{slot.value}' (confidence: {slot.confidence:.2f})"
            )

    if result.error:
        print(f"Error: {result.error}")

    print("-" * 40)


def basic_example():
    """Basic NLP processing example"""
    print_section("Basic NLP Processing Example")

    # Initialize the NLP router
    router = NLPRouter()

    # Test cases
    test_cases = [
        "create a bedroom",
        "modify the kitchen layout",
        "find all doors on floor 2",
        "export the building plan",
        "validate electrical systems",
        "sync the building data",
        "annotate the wall with a note",
        "inspect the HVAC system",
        "generate a report for the building",
    ]

    print("Processing natural language commands:")
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{text}'")
        result = router.parse_natural_language(text)
        print_nlp_result(result)


def advanced_example():
    """Advanced NLP processing with context"""
    print_section("Advanced NLP Processing with Context")

    # Create context with user and building information
    context = NLPContext(
        user_id="architect_001",
        building_id="office_building_123",
        floor_id="floor_2",
        permissions=["create", "modify", "query", "export"],
        object_context={"current_location": "floor_2", "building_type": "office"},
    )

    # Initialize router with configuration
    config = {
        "intent_detection": {"confidence_threshold": 0.6},
        "slot_filling": {"enable_validation": True},
        "cli_translation": {"validate_commands": True},
    }

    router = NLPRouter(config)

    # Test complex commands with context
    complex_commands = [
        "create a conference room with a door and window",
        "modify the kitchen color to blue and size to 20x15",
        "find all electrical outlets on this floor",
        "export the floor plan as SVG format",
        "add a note to the main entrance about access control",
    ]

    print("Processing complex commands with context:")
    for i, text in enumerate(complex_commands, 1):
        print(f"\n{i}. Input: '{text}'")
        result = router.parse_natural_language(text, context)
        print_nlp_result(result)

        # Show context information
        print(f"Context - User: {result.context.user_id}")
        print(f"Context - Building: {result.context.building_id}")
        print(f"Context - Floor: {result.context.floor_id}")
        print(f"Context - Session: {result.context.session_id}")


def batch_processing_example():
    """Batch processing example"""
    print_section("Batch Processing Example")

    router = NLPRouter()
    context = NLPContext(user_id="batch_user", building_id="test_building")

    # Batch of commands
    commands = [
        "create a bedroom",
        "add a bathroom next to the bedroom",
        "modify the bedroom size to 15x12",
        "add a window to the bedroom",
        "create a kitchen with appliances",
        "add a door between kitchen and living room",
        "modify the kitchen color to white",
        "find all rooms on floor 1",
        "export the building layout",
        "validate the electrical system",
    ]

    print("Processing batch of commands:")
    results = router.batch_process(commands, context)

    # Summary statistics
    intent_counts = {}
    total_confidence = 0
    successful_commands = 0

    for i, result in enumerate(results, 1):
        intent_type = result.intent.intent_type.value
        intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
        total_confidence += result.confidence

        if result.confidence > 0.5:
            successful_commands += 1

        print(
            f"{i:2d}. {result.intent.intent_type.value:8s} - {result.cli_command.to_string()}"
        )

    print(f"\nBatch Processing Summary:")
    print(f"Total commands: {len(results)}")
    print(f"Successful commands: {successful_commands}")
    print(f"Average confidence: {total_confidence / len(results):.2f}")
    print(f"Intent distribution: {intent_counts}")


def suggestions_example():
    """Command suggestions example"""
    print_section("Command Suggestions Example")

    router = NLPRouter()

    # Test partial inputs
    partial_inputs = [
        "create",
        "modify",
        "find",
        "export",
        "room",
        "kitchen",
        "door",
        "window",
    ]

    print("Getting suggestions for partial inputs:")
    for partial in partial_inputs:
        suggestions = router.get_suggestions(partial)
        print(f"\n'{partial}' -> {suggestions[:5]}")  # Show first 5 suggestions


def error_handling_example():
    """Error handling example"""
    print_section("Error Handling Example")

    router = NLPRouter()

    # Test invalid or ambiguous inputs
    invalid_inputs = [
        "abracadabra foo bar",
        "xyz 123 456",
        "random text that makes no sense",
        "",
        "   ",
        "create something that doesn't exist",
        "modify the impossible object",
    ]

    print("Testing error handling with invalid inputs:")
    for i, text in enumerate(invalid_inputs, 1):
        print(f"\n{i}. Input: '{text}'")
        result = router.parse_natural_language(text)
        print_nlp_result(result)


def validation_example():
    """Command validation example"""
    print_section("Command Validation Example")

    router = NLPRouter()

    # Test various commands and validate them
    test_commands = [
        "create a bedroom",
        "modify the kitchen",
        "delete the wall",
        "move the door",
        "find all windows",
        "export the building",
        "import data",
        "validate systems",
        "sync data",
        "annotate wall",
        "inspect room",
        "report building",
    ]

    print("Validating generated commands:")
    for i, text in enumerate(test_commands, 1):
        result = router.parse_natural_language(text)
        is_valid = router.validate_command(result.cli_command)

        print(
            f"{i:2d}. '{text}' -> {result.cli_command.to_string()} -> Valid: {is_valid}"
        )


def help_example():
    """Help functionality example"""
    print_section("Help Functionality Example")

    router = NLPRouter()

    # Get general help
    print("General Help:")
    print(router.get_help())

    # Get specific help topics
    help_topics = ["create", "modify", "query", "export", "sync"]

    print("\nSpecific Help Topics:")
    for topic in help_topics:
        help_text = router.get_help(topic)
        print(f"\n{topic.upper()} help:")
        print(help_text)


def main():
    """Main function to run all examples"""
    print("🎯 Arxos NLP Integration Examples")
    print("=" * 60)

    # Set up logging
    setup_logging()

    try:
        # Run all examples
        basic_example()
        advanced_example()
        batch_processing_example()
        suggestions_example()
        error_handling_example()
        validation_example()
        help_example()

        print_section("Example Execution Complete")
        print("✅ All examples executed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Intent detection with confidence scoring")
        print("  ✓ Slot filling for command parameters")
        print("  ✓ Contextual object resolution")
        print("  ✓ CLI command generation")
        print("  ✓ Batch processing capabilities")
        print("  ✓ Command suggestions and autocomplete")
        print("  ✓ Error handling and validation")
        print("  ✓ Help system and documentation")

    except Exception as e:
        print(f"❌ Error during example execution: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
