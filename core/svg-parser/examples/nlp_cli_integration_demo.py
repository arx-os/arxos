"""
NLP & CLI Integration Demo

Demonstrates parsing of natural language building design commands into structured NLPCommand objects.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nlp_cli_integration import NLPCLIIntegration

EXAMPLES = [
    "create room",
    "add door",
    "modify wall color",
    "move window",
    "delete chair",
    "export plan",
    "create wall red 10x20",
    "abracadabra foo bar"
]

def print_command(cmd):
    print(f"\nParsed Command:")
    print(f"  Action: {cmd.action}")
    print(f"  Command Type: {cmd.command_type}")
    print(f"  Parameters: {cmd.parameters}")
    print(f"  Confidence: {cmd.confidence:.2f}")
    print(f"  Original Text: '{cmd.original_text}'")

if __name__ == "__main__":
    nlp = NLPCLIIntegration()
    if sys.stdin.isatty():
        print("NLP & CLI Integration Demo. Type a building design command (or 'exit' to quit):")
        while True:
            text = input("Command> ").strip()
            if text.lower() in ("exit", "quit"): break
            cmd = nlp.parse_natural_language(text)
            print_command(cmd)
    else:
        print("Demo examples:")
        for example in EXAMPLES:
            print(f"\nInput: {example}")
            cmd = nlp.parse_natural_language(example)
            print_command(cmd) 