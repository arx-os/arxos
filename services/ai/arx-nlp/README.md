# Arxos NLP Integration

Natural Language Processing integration for the Arxos Platform, enabling users to interact with building data and systems using natural language.

## Overview

The Arxos NLP Integration provides a comprehensive natural language processing system that converts user input into structured ArxCLI commands. It includes intent detection, slot filling, contextual object resolution, and CLI command generation.

## Features

### Core NLP Capabilities
- **Intent Detection**: Identify user intentions with confidence scoring
- **Slot Filling**: Extract parameters from natural language input
- **Context Resolution**: Handle contextual object references
- **CLI Translation**: Convert NLP results to ArxCLI commands
- **Command Validation**: Validate generated commands before execution

### Supported Operations
- **Create**: Add new building objects (rooms, walls, doors, etc.)
- **Modify**: Update existing object properties
- **Delete**: Remove objects from the building model
- **Move**: Relocate objects to different positions
- **Query**: Search and retrieve object information
- **Export**: Export building data in various formats
- **Import**: Import building data from external sources
- **Validate**: Check building compliance and rules
- **Sync**: Synchronize data across systems
- **Annotate**: Add notes and comments to objects
- **Inspect**: Examine object details and properties
- **Report**: Generate building reports and summaries

### Advanced Features
- **Context Management**: Maintain session context and object references
- **Confidence Scoring**: Rate the accuracy of intent detection
- **Command Suggestions**: Provide autocomplete and suggestions
- **Error Handling**: Graceful handling of unrecognized inputs
- **Batch Processing**: Process multiple inputs efficiently

## Installation

### Prerequisites
- Python 3.7 or higher
- Arxos Platform components (arx-cli, arx-backend)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd arx-nlp

# Install in development mode
pip install -e .

# Run tests
pytest tests/
```

## Quick Start

### Basic Usage
```python
from arx_nlp import NLPRouter

# Initialize the NLP router
router = NLPRouter()

# Process natural language input
text = "create a bedroom with a door"
result = router.parse_natural_language(text)

print(f"Intent: {result.intent.intent_type}")
print(f"Confidence: {result.confidence}")
print(f"CLI Command: {result.cli_command.to_string()}")
```

### Advanced Usage
```python
from arx_nlp import NLPRouter, NLPContext

# Create context with user and building information
context = NLPContext(
    user_id="user123",
    building_id="building456",
    floor_id="floor1"
)

# Initialize router with configuration
config = {
    "intent_detection": {"confidence_threshold": 0.7},
    "slot_filling": {"enable_validation": True},
    "cli_translation": {"validate_commands": True}
}

router = NLPRouter(config)

# Process with context
text = "modify the kitchen layout to be larger"
result = router.parse_natural_language(text, context)

print(f"Generated Command: {result.cli_command.to_string()}")
print(f"Context: {result.context.object_context}")
```

## API Reference

### NLPRouter

Main class for NLP processing.

#### Methods

##### `parse_natural_language(text, context=None)`
Parse natural language input and convert to structured command.

**Parameters:**
- `text` (str): Natural language input
- `context` (NLPContext, optional): Context information

**Returns:**
- `NLPResponse`: Parsed response with intent, slots, and CLI command

##### `batch_process(texts, context=None)`
Process multiple natural language inputs in batch.

**Parameters:**
- `texts` (List[str]): List of natural language inputs
- `context` (NLPContext, optional): Context information

**Returns:**
- `List[NLPResponse]`: List of parsed responses

##### `get_suggestions(partial_text, context=None)`
Get command suggestions based on partial input.

**Parameters:**
- `partial_text` (str): Partial natural language input
- `context` (NLPContext, optional): Context information

**Returns:**
- `List[str]`: List of suggested completions

### IntentMapper

Intent detection and mapping functionality.

#### Methods

##### `detect_intent(text)`
Detect intent from natural language text.

**Parameters:**
- `text` (str): Natural language input

**Returns:**
- `Intent`: Detected intent with confidence

### SlotFiller

Slot filling and parameter extraction.

#### Methods

##### `extract_slots(text, intent_type)`
Extract slots from natural language text.

**Parameters:**
- `text` (str): Natural language input
- `intent_type` (IntentType): Detected intent type

**Returns:**
- `SlotResult`: Extracted slots with confidence

### CLITranslator

CLI command generation and translation.

#### Methods

##### `generate_command(intent, slot_result, context=None)`
Generate CLI command from intent and slots.

**Parameters:**
- `intent` (Intent): Detected intent
- `slot_result` (SlotResult): Extracted slots
- `context` (Any, optional): Context information

**Returns:**
- `CLICommand`: Generated CLI command

## Data Models

### NLPRequest
Request object for NLP processing.

**Fields:**
- `text` (str): Natural language input
- `context` (NLPContext, optional): Context information
- `config` (Dict[str, Any]): Configuration options
- `metadata` (Dict[str, Any]): Additional metadata

### NLPResponse
Response object containing parsed results.

**Fields:**
- `original_text` (str): Original input text
- `intent` (Intent): Detected intent
- `slots` (List[Slot]): Extracted slots
- `cli_command` (CLICommand): Generated CLI command
- `confidence` (float): Overall confidence score
- `context` (NLPContext): Resolved context
- `timestamp` (datetime): Processing timestamp
- `error` (str, optional): Error message if processing failed

### Intent
Intent detection result.

**Fields:**
- `intent_type` (IntentType): Type of detected intent
- `confidence` (float): Confidence score (0.0 to 1.0)
- `raw_text` (str): Original input text
- `required_slots` (List[SlotType]): Required slot types
- `optional_slots` (List[SlotType]): Optional slot types
- `metadata` (Dict[str, Any]): Additional metadata

### Slot
Slot extraction result.

**Fields:**
- `slot_type` (SlotType): Type of extracted slot
- `value` (str): Extracted value
- `value_type` (str): Type of value (string, number, etc.)
- `confidence` (float): Confidence score
- `start_pos` (int): Start position in text
- `end_pos` (int): End position in text
- `original_value` (str, optional): Original value before processing
- `metadata` (Dict[str, Any]): Additional metadata

### CLICommand
Generated CLI command.

**Fields:**
- `command` (str): Main command
- `arguments` (List[str]): Command arguments
- `options` (Dict[str, Any]): Command options
- `subcommand` (str, optional): Subcommand
- `metadata` (Dict[str, Any]): Additional metadata

## Configuration

### Intent Detection Configuration
```python
intent_config = {
    "confidence_threshold": 0.7,
    "enable_fuzzy_matching": True,
    "max_suggestions": 10
}
```

### Slot Filling Configuration
```python
slot_config = {
    "enable_validation": True,
    "strict_mode": False,
    "custom_patterns": []
}
```

### CLI Translation Configuration
```python
cli_config = {
    "validate_commands": True,
    "enable_simulation": True,
    "command_templates": []
}
```

## Examples

### Basic Command Processing
```python
# Create a room
result = router.parse_natural_language("create a bedroom")
# Output: arx create room --type bedroom

# Modify an object
result = router.parse_natural_language("change the kitchen color to blue")
# Output: arx modify kitchen --property color --value blue

# Query information
result = router.parse_natural_language("find all doors on floor 2")
# Output: arx query door --filter "floor=2"
```

### Advanced Context Usage
```python
# Set up context with building information
context = NLPContext(
    user_id="architect_001",
    building_id="office_building_123",
    floor_id="floor_2",
    permissions=["create", "modify", "query"]
)

# Process with context
result = router.parse_natural_language(
    "add a conference room next to the elevator",
    context
)
```

### Batch Processing
```python
# Process multiple commands
commands = [
    "create a kitchen",
    "add a door to the kitchen",
    "modify the kitchen size to 20x15"
]

results = router.batch_process(commands, context)

for i, result in enumerate(results):
    print(f"Command {i+1}: {result.cli_command.to_string()}")
```

## Error Handling

The NLP system provides comprehensive error handling:

```python
try:
    result = router.parse_natural_language("invalid command")
    if result.error:
        print(f"Error: {result.error}")
        # Handle error appropriately
except Exception as e:
    print(f"Processing error: {e}")
```

## Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arx_nlp

# Run specific test file
pytest tests/test_nlp_router.py
```

### Test Examples
```python
import pytest
from arx_nlp import NLPRouter

def test_basic_intent_detection():
    router = NLPRouter()
    result = router.parse_natural_language("create a room")

    assert result.intent.intent_type.value == "create"
    assert result.confidence > 0.5
    assert "create" in result.cli_command.to_string()

def test_slot_extraction():
    router = NLPRouter()
    result = router.parse_natural_language("create a red bedroom")

    assert len(result.slots) > 0
    assert any(slot.slot_type.value == "object_type" for slot in result.slots)
```

## Development

### Project Structure
```
arx-nlp/
├── __init__.py                 # Main package initialization
├── nlp_router.py              # Main NLP router
├── intent_mapper.py           # Intent detection and mapping
├── models/                    # Data models
│   ├── __init__.py
│   └── nlp_models.py
├── intent_detection/          # Intent detection components
│   ├── __init__.py
│   └── intent_detector.py
├── slot_filling/             # Slot filling components
│   ├── __init__.py
│   └── slot_filler.py
├── cli_translation/          # CLI translation components
│   ├── __init__.py
│   └── cli_translator.py
├── utils/                    # Utility functions
│   ├── __init__.py
│   └── context_manager.py
├── tests/                    # Test files
├── examples/                 # Example scripts
├── requirements.txt          # Dependencies
└── README.md                # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style

The project follows PEP 8 style guidelines. Use the provided tools:

```bash
# Format code
black arx-nlp/

# Check style
flake8 arx-nlp/

# Type checking
mypy arx-nlp/
```

## Monitoring and Troubleshooting

### Logging
The system uses structured logging for monitoring:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Router will log processing steps
router = NLPRouter()
result = router.parse_natural_language("create a room")
```

### Performance Monitoring
```python
# Get processing statistics
stats = router.get_processing_stats()
print(f"Average confidence: {stats.average_confidence}")
print(f"Total requests: {stats.total_requests}")
```

### Common Issues

1. **Low Confidence Scores**: Check input text quality and context
2. **Missing Slots**: Verify slot patterns and validation rules
3. **Invalid Commands**: Review command templates and mappings
4. **Context Issues**: Ensure proper context initialization

## Future Enhancements

### Planned Features
- Machine learning-based intent detection
- Advanced slot filling with entity recognition
- Voice command processing
- Multi-language support
- Real-time learning from user feedback

### Integration Points
- ArxCLI command execution
- Building data validation
- Real-time collaboration
- Mobile app integration

## License

This project is part of the Arxos Platform and follows the same licensing terms.

## Support

For support and questions:
- Check the documentation
- Review the examples
- Open an issue on the repository
- Contact the Arxos Platform team
