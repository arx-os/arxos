"""
CLI Translation Package

This package provides CLI command generation functionality to convert
NLP intents and slots into structured ArxCLI commands.
"""

from services.cli_translator

__all__ = [
    "CLITranslator",
    "translate_to_cli"
] 