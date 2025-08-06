"""
CLI Translation Package

This package provides CLI command generation functionality to convert
NLP intents and slots into structured ArxCLI commands.
"""

from .cli_translator import CLITranslator, translate_to_cli

__all__ = ["CLITranslator", "translate_to_cli"]
