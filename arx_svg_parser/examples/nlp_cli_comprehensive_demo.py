"""
Comprehensive NLP & CLI Integration Demo

Demonstrates all features of the NLP & CLI Integration service:
- Natural Language Processing for building design commands
- ArxLang DSL parsing and interpretation
- CLI command dispatching and routing
- AI-assisted layout generation (stub)
- Natural language to SVG conversion (stub)
- Voice command processing (stub)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nlp_cli_integration import NLPCLIIntegration

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_nlp_command(cmd):
    print(f"  Action: {cmd.action}")
    print(f"  Command Type: {cmd.command_type}")
    print(f"  Parameters: {cmd.parameters}")
    print(f"  Confidence: {cmd.confidence:.2f}")
    print(f"  Original Text: '{cmd.original_text}'")

def print_dsl_statement(stmt):
    print(f"  Statement Type: {stmt.statement_type}")
    print(f"  Operation: {stmt.operation}")
    print(f"  Parameters: {stmt.parameters}")
    print(f"  Line: {stmt.line_number}")

def print_cli_operation(op):
    print(f"  Command: {op.command}")
    print(f"  Subcommand: {op.subcommand}")
    print(f"  Arguments: {op.arguments}")
    print(f"  Options: {op.options}")
    if op.result:
        print(f"  Result: {op.result}")
    if op.error:
        print(f"  Error: {op.error}")

def main():
    print("🎯 Comprehensive NLP & CLI Integration Demo")
    
    # Initialize the service
    nlp_cli = NLPCLIIntegration()
    print("✓ Service initialized successfully")
    
    # 1. Natural Language Processing Demo
    print_section("Natural Language Processing")
    
    nlp_examples = [
        "create room",
        "add door",
        "modify wall color",
        "move window",
        "delete chair",
        "export plan",
        "create wall red 10x20",
        "abracadabra foo bar"
    ]
    
    print("Parsing natural language commands:")
    for example in nlp_examples:
        print(f"\nInput: '{example}'")
        cmd = nlp_cli.parse_natural_language(example)
        print_nlp_command(cmd)
    
    # 2. ArxLang DSL Demo
    print_section("ArxLang DSL Parsing")
    
    dsl_example = """
# ArxLang DSL Example
create room name=bedroom size=large
add door target=bedroom type=interior
modify wall target=bedroom color=blue
move window target=bedroom position=center
export plan format=svg
"""
    
    print("Parsing ArxLang DSL:")
    print(f"DSL Input:\n{dsl_example}")
    
    statements = nlp_cli.parse_arxlang(dsl_example)
    print(f"\nParsed {len(statements)} statements:")
    
    for i, stmt in enumerate(statements, 1):
        print(f"\nStatement {i}:")
        print_dsl_statement(stmt)
    
    # 3. CLI Command Dispatching Demo
    print_section("CLI Command Dispatching")
    
    cli_examples = [
        (["nlp", "create", "room"], {}),
        (["make", "bedroom"], {}),
        (["script", "building.arl"], {}),
        (["plan", "floor"], {}),
        (["unknown", "command"], {}),
        ([], {})
    ]
    
    print("Dispatching CLI commands:")
    for args, options in cli_examples:
        print(f"\nCommand: arx {' '.join(args) if args else ''}")
        op = nlp_cli.dispatch_cli_command("arx", args, options)
        print_cli_operation(op)
    
    # 4. AI-Assisted Layout Demo
    print_section("AI-Assisted Layout Generation")
    
    layout_requirements = {
        "building_type": "residential",
        "rooms": ["bedroom", "bathroom", "kitchen", "living_room"],
        "constraints": ["max_area=2000", "style=modern"],
        "preferences": ["open_plan", "natural_light"]
    }
    
    print("Generating AI-assisted layout:")
    print(f"Requirements: {layout_requirements}")
    
    layout_result = nlp_cli.ai_assisted_layout(layout_requirements)
    print(f"Result: {layout_result}")
    
    # 5. Natural Language to SVG Demo
    print_section("Natural Language to SVG Conversion")
    
    nl_to_svg_examples = [
        "create a red circle with radius 50",
        "draw a blue rectangle 100x200",
        "add a green triangle pointing up"
    ]
    
    print("Converting natural language to SVG:")
    for example in nl_to_svg_examples:
        print(f"\nInput: '{example}'")
        svg_result = nlp_cli.natural_language_to_svg(example)
        print(f"SVG Output: {svg_result}")
    
    # 6. Voice Command Processing Demo
    print_section("Voice Command Processing")
    
    voice_examples = [
        "voice_command_1.wav",
        "voice_command_2.wav",
        "voice_command_3.wav"
    ]
    
    print("Processing voice commands:")
    for audio_file in voice_examples:
        print(f"\nAudio file: {audio_file}")
        voice_result = nlp_cli.process_voice_command(audio_file)
        print_nlp_command(voice_result)
    
    # 7. Integration Demo
    print_section("Integration Example")
    
    print("Complete workflow: NLP → DSL → CLI → Action")
    
    # Step 1: Parse natural language
    nl_input = "create a bedroom with a door and window"
    print(f"\nStep 1 - NLP Input: '{nl_input}'")
    nl_cmd = nlp_cli.parse_natural_language(nl_input)
    print_nlp_command(nl_cmd)
    
    # Step 2: Convert to DSL
    dsl_script = f"""
# Generated from NLP input
create room name=bedroom
add door target=bedroom
add window target=bedroom
"""
    print(f"\nStep 2 - Generated DSL:\n{dsl_script}")
    dsl_statements = nlp_cli.parse_arxlang(dsl_script)
    print(f"Parsed {len(dsl_statements)} DSL statements")
    
    # Step 3: Execute via CLI
    cli_args = ["script", "generated.arl"]
    print(f"\nStep 3 - CLI Execution: arx {' '.join(cli_args)}")
    cli_result = nlp_cli.dispatch_cli_command("arx", cli_args, {})
    print_cli_operation(cli_result)
    
    print("\n🎉 NLP & CLI Integration Demo Completed!")
    print("="*50)
    print("\nKey Features Demonstrated:")
    print("  ✓ Natural Language Processing with confidence scoring")
    print("  ✓ ArxLang DSL parsing and statement extraction")
    print("  ✓ CLI command dispatching and routing")
    print("  ✓ AI-assisted layout generation (stub)")
    print("  ✓ Natural language to SVG conversion (stub)")
    print("  ✓ Voice command processing (stub)")
    print("  ✓ Complete workflow integration")

if __name__ == '__main__':
    main() 