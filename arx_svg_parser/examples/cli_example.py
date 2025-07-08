#!/usr/bin/env python3
"""
Symbol Manager CLI Example

This script demonstrates how to use the Symbol Manager CLI
with various commands and options.

Author: Arxos Development Team
Date: 2024
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def create_sample_symbol_file():
    """Create a sample symbol JSON file for testing."""
    sample_symbol = {
        "id": "cli_test_symbol",
        "name": "CLI Test Symbol",
        "system": "electrical",
        "description": "Test symbol created via CLI",
        "category": "test",
        "tags": ["cli", "test", "electrical"],
        "svg": {
            "content": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='blue'/></svg>"
        },
        "properties": {
            "voltage": "220V",
            "current": "10A",
            "created_by": "cli_example"
        }
    }
    
    with open("sample_symbol.json", "w") as f:
        json.dump(sample_symbol, f, indent=2)
    
    print("✅ Created sample_symbol.json")

def create_sample_bulk_file():
    """Create a sample bulk symbols JSON file for testing."""
    sample_symbols = [
        {
            "id": "bulk_test_1",
            "name": "Bulk Test Symbol 1",
            "system": "electrical",
            "description": "First bulk test symbol",
            "category": "test",
            "tags": ["bulk", "test", "electrical"],
            "svg": {
                "content": "<svg width='50' height='50'><rect width='40' height='40' fill='red'/></svg>"
            }
        },
        {
            "id": "bulk_test_2",
            "name": "Bulk Test Symbol 2",
            "system": "mechanical",
            "description": "Second bulk test symbol",
            "category": "test",
            "tags": ["bulk", "test", "mechanical"],
            "svg": {
                "content": "<svg width='50' height='50'><polygon points='25,5 45,45 5,45' fill='green'/></svg>"
            }
        },
        {
            "id": "bulk_test_3",
            "name": "Bulk Test Symbol 3",
            "system": "plumbing",
            "description": "Third bulk test symbol",
            "category": "test",
            "tags": ["bulk", "test", "plumbing"],
            "svg": {
                "content": "<svg width='50' height='50'><ellipse cx='25' cy='25' rx='20' ry='15' fill='purple'/></svg>"
            }
        }
    ]
    
    with open("sample_bulk_symbols.json", "w") as f:
        json.dump(sample_symbols, f, indent=2)
    
    print("✅ Created sample_bulk_symbols.json")

def run_cli_command(command, description):
    """Run a CLI command and display the result."""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.stdout:
            print("Output:")
            print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Command executed successfully")
        else:
            print("❌ Command failed")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    """Main function to demonstrate CLI usage."""
    print("Arxos Symbol Manager CLI - Example Usage")
    print("=" * 50)
    
    # Create sample files
    create_sample_symbol_file()
    create_sample_bulk_file()
    
    # CLI commands to demonstrate
    commands = [
        # Help command
        ("python cmd/symbol_manager_cli.py --help", "Show CLI help"),
        
        # Create symbol from file
        ("python cmd/symbol_manager_cli.py create --file sample_symbol.json", "Create symbol from file"),
        
        # Create symbol from command line
        ("python cmd/symbol_manager_cli.py create --id cli_cmd_symbol --name 'CLI Command Symbol' --system electrical --description 'Created via command line' --tags 'cli,command,test'", "Create symbol from command line"),
        
        # List symbols
        ("python cmd/symbol_manager_cli.py list", "List all symbols"),
        
        # List symbols with system filter
        ("python cmd/symbol_manager_cli.py list --system electrical", "List electrical symbols"),
        
        # Search symbols
        ("python cmd/symbol_manager_cli.py list --query test", "Search for symbols with 'test'"),
        
        # Get specific symbol
        ("python cmd/symbol_manager_cli.py get --id cli_test_symbol", "Get specific symbol"),
        
        # Update symbol
        ("python cmd/symbol_manager_cli.py update --id cli_test_symbol --name 'Updated CLI Test Symbol' --description 'Updated via CLI'", "Update symbol"),
        
        # Bulk import
        ("python cmd/symbol_manager_cli.py bulk-import --file sample_bulk_symbols.json", "Bulk import symbols"),
        
        # Bulk export
        ("python cmd/symbol_manager_cli.py bulk-export --output exported_symbols.json", "Bulk export symbols"),
        
        # Get statistics
        ("python cmd/symbol_manager_cli.py stats", "Get symbol statistics"),
        
        # List symbols with limit
        ("python cmd/symbol_manager_cli.py list --limit 5", "List first 5 symbols"),
        
        # Delete symbol (with confirmation)
        ("python cmd/symbol_manager_cli.py delete --id cli_cmd_symbol", "Delete symbol (will prompt for confirmation)"),
        
        # Delete symbol (force)
        ("python cmd/symbol_manager_cli.py delete --id cli_test_symbol --force", "Delete symbol (force)"),
    ]
    
    successful_commands = 0
    total_commands = len(commands)
    
    for command, description in commands:
        success = run_cli_command(command, description)
        if success:
            successful_commands += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("CLI Example Summary")
    print("=" * 50)
    print(f"Total commands executed: {total_commands}")
    print(f"Successful commands: {successful_commands}")
    print(f"Failed commands: {total_commands - successful_commands}")
    
    if successful_commands == total_commands:
        print("🎉 All commands executed successfully!")
    else:
        print("⚠️  Some commands failed. Check the output above for details.")
    
    # Cleanup
    print("\n🧹 Cleaning up sample files...")
    cleanup_files = [
        "sample_symbol.json",
        "sample_bulk_symbols.json",
        "exported_symbols.json"
    ]
    
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"  ✅ Removed {file}")

def interactive_mode():
    """Run CLI in interactive mode for manual testing."""
    print("\n🎮 Interactive CLI Mode")
    print("=" * 50)
    print("Enter CLI commands manually. Type 'quit' to exit.")
    print("Example commands:")
    print("  python cmd/symbol_manager_cli.py list")
    print("  python cmd/symbol_manager_cli.py create --id test --name 'Test Symbol' --system electrical")
    print("  python cmd/symbol_manager_cli.py get --id test")
    print()
    
    while True:
        try:
            command = input("CLI> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not command:
                continue
            
            # Run the command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print(result.stderr)
            
            print(f"Exit code: {result.returncode}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main() 